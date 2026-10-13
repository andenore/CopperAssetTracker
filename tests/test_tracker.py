"""Source contracts, not a hardware safety or RF qualification certificate."""
import csv
import hashlib
import json
from pathlib import Path
import unittest
from pcbir.assembly import check_assembly, load_lock, snapshot
from pcbir.elaborate import elaborate
from pcbir.erc import check, has_errors
from pcbir.footprints import FootprintResolver
from pcbir.loader import load_design
from pcbir.physicalize import PrototypePhysicalOptions, resolved_physicalize

ROOT = Path(__file__).resolve().parents[1]

class TrackerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = load_design(ROOT / "board.copper", locked=True, offline=True)
        cls.board = cls.design.electrical
        cls.flat = elaborate(cls.board)
        cls.nets = {n.name: {(e.component, e.pin) for e in n.endpoints} for n in cls.flat.nets}
        cls.lock = load_lock(ROOT / "assembly.lock")
        cls.physical = resolved_physicalize(cls.design,
            FootprintResolver(base_directory=ROOT, locked=True, offline=True),
            PrototypePhysicalOptions(copper_layers=6, fabrication_profile="jlcpcb-six-layer"))

    def test_erc(self):
        self.assertFalse(has_errors(check(self.board)))

    def test_reusable_parts_are_library_owned(self):
        self.assertEqual({p.name for p in (ROOT / "packages/tracker").glob("*.copper")}, {"power_tree.copper"})
        self.assertFalse(list((ROOT / "footprints").rglob("*.kicad_mod")))
        self.assertFalse((ROOT / "scripts/import_modem_footprint.py").exists())
        expected = {
            "U_MODEM": "simcom.SIM7670G_LNGV",
            "U_MODEM_LEVEL": "translator.MODEM_UART_TRANSLATOR",
            "U_MODEM_STATUS": "translator.MODEM_STATUS_TRANSLATOR",
            "Y_NRF": "yxc.YXC_X322532MOB4SI",
        }
        components = {c.ref: c.part for c in self.flat.components}
        for ref, part in expected.items():
            self.assertEqual(components[ref], part)
        for name, part in self.flat.library.items():
            if name.startswith("tracker."):
                continue
            for footprint in part.footprints:
                self.assertNotIn("Tracker.pretty", footprint)

    def test_can_removed(self):
        removed = {"U_CAN", "J_CAN", "R_CAN_TERM", "C_CAN"}
        self.assertTrue(removed.isdisjoint(c.ref for c in self.flat.components))
        self.assertFalse(any(n.startswith("CAN_") for n in self.nets))
        endpoints = {e for net in self.nets.values() for e in net}
        self.assertTrue({("U_MCU", "PC4"), ("U_MCU", "PC5")}.isdisjoint(endpoints))
        source = (ROOT / "board.copper").read_text()
        self.assertNotIn("FDCAN1", source)
        self.assertNotIn("can_phy", source)
        self.assertNotIn("can_header", source)
        self.assertTrue(removed.isdisjoint(s.reference for s in self.lock.selections))

    def test_procurement_coverage(self):
        expected = {s.reference for s in snapshot(self.board).selections}
        self.assertEqual(expected, {s.reference for s in self.lock.selections})
        self.assertEqual(len(expected), len(self.lock.selections))
        self.assertTrue(all(s.exact and s.supplier == "jlcpcb" for s in self.lock.selections))
        groups = json.loads((ROOT / "procurement/parts.json").read_text())["groups"]
        refs = [r for g in groups for r in g["references"]]
        self.assertEqual(expected, set(refs))
        self.assertEqual(len(refs), len(set(refs)))
        with (ROOT / "procurement/candidate-bom.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        csv_refs = [ref for row in rows for ref in row["Designator"].split(",")]
        self.assertEqual(expected, set(csv_refs))
        self.assertEqual(len(csv_refs), len(set(csv_refs)))
        for g in groups:
            for ref in g["references"]:
                s = next(s for s in self.lock.selections if s.reference == ref)
                self.assertEqual((s.mpn, s.supplier_part), (g["mpn"], g["supplier_part"]))

    def test_manufacturing_review_gate(self):
        r = check_assembly(self.board, self.lock)
        self.assertEqual(r["exact_selection_count"], len(self.lock.selections))
        # New source/compiler inputs invalidate the retained assembly snapshot.
        # Exact reviewed selections remain facts, but are not reapproved here.
        self.assertFalse(r["passed"])
        self.assertEqual({issue["code"] for issue in r["issues"]}, {"STALE_LOCK"})
        self.assertEqual(r["reviewed_count"], 83)

    def test_battery_and_power_path(self):
        self.assertIn(("PWR/J_BAT", "P1"), self.nets["PWR/BAT"])
        self.assertIn(("PWR/J_BAT", "P2"), self.nets["GND"])
        self.assertEqual(self.nets["PWR/BAT_NTC"], {("PWR/J_BAT", "P3"), ("PWR/U_CHARGE", "TS")})
        self.assertIn(("PWR/U_CHARGE", "OUT_10"), self.nets["PWR/VSYS"])
        self.assertNotIn(("U_MODEM", "VBAT_1"), self.nets["PWR/BAT"])
        for pin in ("VBAT_1", "VBAT_2", "VBAT_3"):
            self.assertIn(("U_MODEM", pin), self.nets["V3V8"])
        self.assertIn(("PWR/U_MODEM", "EN"), self.nets["MODEM_EN"])
        self.assertIn(("PWR/R_MODEM_EN_PD", "2"), self.nets["GND"])

    def test_modem_translation(self):
        self.assertEqual(self.nets["MCU_MODEM_TX"], {("U_MCU", "PB6"), ("U_MODEM_LEVEL", "A_TX")})
        self.assertEqual(self.nets["MODEM_UART_RX"], {("U_MODEM_LEVEL", "B_RX"), ("U_MODEM", "MAIN_RXD")})
        self.assertEqual(self.nets["MODEM_STATUS_1V8"], {("U_MODEM", "STATUS"), ("U_MODEM_STATUS", "B_STATUS")})
        self.assertEqual(self.nets["MODEM_STATUS"], {("U_MODEM_STATUS", "A_STATUS"), ("U_MCU", "PC1")})
        self.assertEqual(self.nets["MODEM_PWRKEY"], {("U_MODEM_KEY", "OUT"), ("U_MODEM", "PWRKEY")})

    def test_usb_detection_is_battery_fed_without_external_backfeed(self):
        self.assertIn(("U_MODEM", "USB_VBUS"), self.nets["V3V8"])
        self.assertNotIn(("U_MODEM", "USB_VBUS"), self.nets["V5"])
        self.assertTrue({("J_POWER", "VBUS_A"), ("J_POWER", "VBUS_B")}.issubset(self.nets["V5"]))
        self.assertFalse({("J_POWER", "VBUS_A"), ("J_POWER", "VBUS_B")} & self.nets["V3V8"])
        self.assertIn(("PWR/U_MODEM", "VOUT_4"), self.nets["V3V8"])

    def test_nordic_support(self):
        for pin in ("DEC1", "DEC3", "DEC4"):
            self.assertEqual(self.nets["NRF_" + pin], {("U_NRF", pin), ("C_" + pin, "1")})
        self.assertIn(("Y_NRF", "XTAL1"), self.nets["NRF_XC1"])
        self.assertIn(("Y_NRF", "XTAL2"), self.nets["NRF_XC2"])

    def test_modem_and_regulator_lands(self):
        poses = {p.reference: p for p in self.physical.placements}
        modem = self.physical.footprints[poses["U_MODEM"].footprint]
        self.assertEqual({p.number for p in modem.pads}, {str(i) for i in range(1, 125)})
        self.assertEqual(len(modem.pads), 124)
        for ref in ("PWR/U_LOGIC", "PWR/U_MODEM"):
            f = self.physical.footprints[poses[ref].footprint]
            self.assertEqual({p.number for p in f.pads if p.number}, {str(i) for i in range(1, 16)})
            apertures = [p for p in f.pads if not p.number]
            self.assertEqual(len(apertures), 6)
            self.assertTrue(all(p.kind.value == "aperture" and p.has_solder_paste for p in apertures))

    def test_cellular_feed_has_source_backed_surface_length_limit(self):
        from pcbir.physical import CopperLayer, Point, RouteKind
        from pcbir.placement import transformed_pad_position
        from dataclasses import replace
        rules = {r.net: r for r in self.physical.net_routing_rules}
        rule = rules["CELL_RF"]
        self.assertEqual(rule.kind, RouteKind.RF_FEED)
        self.assertEqual(rule.max_length_nm, 20000000)
        self.assertEqual(rule.max_vias, 0)
        self.assertEqual(rule.allowed_layers, (CopperLayer.FRONT,))
        fixed = {r.reference: r for r in self.physical.placement_rules}
        self.assertEqual(fixed["J_CELL"].fixed_position, Point.mm(6, 8))
        self.assertEqual(fixed["J_CELL"].fixed_rotation_degrees, 180)
        poses = {p.reference: p for p in self.physical.placements}
        modem = replace(poses["U_MODEM"], position=fixed["U_MODEM"].fixed_position,
                        rotation_degrees=fixed["U_MODEM"].fixed_rotation_degrees)
        self.assertEqual(transformed_pad_position(self.physical, modem, "60"),
                         Point(8000024, 24000000))

    def test_rf_macro_identity(self):
        scene = json.loads((ROOT / "nrf-antenna-macro.json").read_text())
        self.assertEqual(hashlib.sha256((ROOT / scene["asset"]).read_bytes()).hexdigest(), scene["asset_sha256"])
        macros = {m.cluster: m for m in self.physical.hard_macros}
        self.assertEqual(len(macros), 3)
        self.assertEqual(macros["nordic-antenna"].asset_sha256, scene["asset_sha256"])
        cluster = next(c for c in self.physical.rigid_clusters if c.name == "nordic-antenna")
        self.assertEqual(len(cluster.members), 7)

if __name__ == "__main__":
    unittest.main()
