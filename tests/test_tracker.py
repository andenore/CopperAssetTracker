"""Source contracts, not a hardware safety or RF qualification certificate."""
import csv
import hashlib
import json
from pathlib import Path
import unittest

from copper_cli import (assembly_check, assembly_snapshot, audit_footprints, check, compile_board,
                        components, fixed_placements, nanometres, net, net_names, part, query,
                        routing_rules)

ROOT = Path(__file__).resolve().parents[1]


class TrackerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = compile_board()
        cls.components = components()
        cls.lock = json.loads((ROOT / "assembly.lock").read_text())
        cls.selections = {s["reference"]: s for s in cls.lock["selections"]}

    def test_erc(self):
        report = check()
        self.assertTrue(report["passed"], report["diagnostics"])
        self.assertEqual(report["counts"]["error"], 0)

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
        for ref, name in expected.items():
            self.assertEqual(self.components[ref], name)
        for definition in self.design["parts"]:
            if definition["name"].startswith("tracker."):
                continue
            for footprint in definition["footprints"]:
                self.assertNotIn("Tracker.pretty", footprint)

    def test_can_removed(self):
        removed = {"U_CAN", "J_CAN", "R_CAN_TERM", "C_CAN"}
        self.assertTrue(removed.isdisjoint(self.components))
        self.assertFalse(any(n.startswith("CAN_") for n in net_names()))
        pins = {p["pin"]: p for p in query("pins", "U_MCU")["pins"]}
        self.assertEqual(pins["PC4"]["nets"], [])
        self.assertEqual(pins["PC5"]["nets"], [])
        source = (ROOT / "board.copper").read_text()
        self.assertNotIn("FDCAN1", source)
        self.assertNotIn("can_phy", source)
        self.assertNotIn("can_header", source)
        self.assertTrue(removed.isdisjoint(self.selections))

    def test_procurement_coverage(self):
        expected = {s["reference"] for s in assembly_snapshot()["selections"]}
        self.assertEqual(expected, set(self.selections))
        self.assertEqual(len(expected), len(self.lock["selections"]))
        self.assertTrue(all(s["supplier"] == "jlcpcb" and s["mpn"] and s["supplier_part"]
                            for s in self.lock["selections"]))
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
                s = self.selections[ref]
                self.assertEqual((s["mpn"], s["supplier_part"]), (g["mpn"], g["supplier_part"]))

    def test_manufacturing_review_gate(self):
        r = assembly_check()
        self.assertEqual(r["exact_selection_count"], len(self.lock["selections"]))
        # New source/compiler inputs invalidate the retained assembly snapshot.
        # Exact reviewed selections remain facts, but are not reapproved here.
        self.assertFalse(r["passed"])
        self.assertEqual({issue["code"] for issue in r["issues"]}, {"STALE_LOCK"})
        self.assertEqual(r["reviewed_count"], 83)

    def test_battery_and_power_path(self):
        self.assertIn(("PWR/J_BAT", "P1"), net("PWR/BAT"))
        self.assertIn(("PWR/J_BAT", "P2"), net("GND"))
        self.assertEqual(net("PWR/BAT_NTC"), {("PWR/J_BAT", "P3"), ("PWR/U_CHARGE", "TS")})
        self.assertIn(("PWR/U_CHARGE", "OUT_10"), net("PWR/VSYS"))
        self.assertNotIn(("U_MODEM", "VBAT_1"), net("PWR/BAT"))
        for pin in ("VBAT_1", "VBAT_2", "VBAT_3"):
            self.assertIn(("U_MODEM", pin), net("V3V8"))
        self.assertIn(("PWR/U_MODEM", "EN"), net("MODEM_EN"))
        self.assertIn(("PWR/R_MODEM_EN_PD", "2"), net("GND"))

    def test_modem_translation(self):
        self.assertEqual(net("MCU_MODEM_TX"), {("U_MCU", "PB6"), ("U_MODEM_LEVEL", "A_TX")})
        self.assertEqual(net("MODEM_UART_RX"), {("U_MODEM_LEVEL", "B_RX"), ("U_MODEM", "MAIN_RXD")})
        self.assertEqual(net("MODEM_STATUS_1V8"), {("U_MODEM", "STATUS"), ("U_MODEM_STATUS", "B_STATUS")})
        self.assertEqual(net("MODEM_STATUS"), {("U_MODEM_STATUS", "A_STATUS"), ("U_MCU", "PC1")})
        self.assertEqual(net("MODEM_PWRKEY"), {("U_MODEM_KEY", "OUT"), ("U_MODEM", "PWRKEY")})

    def test_usb_detection_is_battery_fed_without_external_backfeed(self):
        self.assertIn(("U_MODEM", "USB_VBUS"), net("V3V8"))
        self.assertNotIn(("U_MODEM", "USB_VBUS"), net("V5"))
        self.assertTrue({("J_POWER", "VBUS_A"), ("J_POWER", "VBUS_B")}.issubset(net("V5")))
        self.assertFalse({("J_POWER", "VBUS_A"), ("J_POWER", "VBUS_B")} & net("V3V8"))
        self.assertIn(("PWR/U_MODEM", "VOUT_4"), net("V3V8"))

    def test_nordic_support(self):
        for pin in ("DEC1", "DEC3", "DEC4"):
            self.assertEqual(net("NRF_" + pin), {("U_NRF", pin), ("C_" + pin, "1")})
        self.assertIn(("Y_NRF", "XTAL1"), net("NRF_XC1"))
        self.assertIn(("Y_NRF", "XTAL2"), net("NRF_XC2"))

    def test_modem_and_regulator_lands(self):
        # The audit requires each footprint's numbered pads to equal its part's pin numbers.
        audit = audit_footprints()
        self.assertTrue(audit["passed"], [e["errors"] for e in audit["entries"] if not e["passed"]])
        users = {ref: e for e in audit["entries"] for ref in e["components"]}
        self.assertTrue(users["U_MODEM"]["reference"].endswith("SIM7670G_LNGV.kicad_mod"))
        self.assertEqual(users["PWR/U_LOGIC"], users["PWR/U_MODEM"])
        modem = part(self.design, self.components["U_MODEM"])
        self.assertEqual({p["number"] for p in modem["pins"].values()}, {str(i) for i in range(1, 125)})
        for ref in ("PWR/U_LOGIC", "PWR/U_MODEM"):
            regulator = part(self.design, self.components[ref])
            self.assertEqual({p["number"] for p in regulator["pins"].values()}, {str(i) for i in range(1, 16)})

    def test_cellular_feed_has_source_backed_surface_length_limit(self):
        rule = routing_rules()["CELL_RF"]
        self.assertEqual(rule["kind"], "rf_feed")
        self.assertEqual(nanometres(rule["max_length"]), 20000000)
        self.assertEqual(rule["max_vias"], 0)
        self.assertEqual(rule["allowed_layers"], "F.Cu")
        fixed = fixed_placements()["J_CELL"]
        self.assertEqual((nanometres(fixed["x"]), nanometres(fixed["y"])), (6000000, 8000000))
        self.assertEqual(fixed["rotation"], 180)

    def test_rf_macro_identity(self):
        scene = json.loads((ROOT / "nrf-antenna-macro.json").read_text())
        self.assertEqual(hashlib.sha256((ROOT / scene["asset"]).read_bytes()).hexdigest(), scene["asset_sha256"])
        macros = {m["name"]: m for m in self.design["physical_macros"]}
        self.assertEqual(len(macros), 3)
        nordic = macros["nordic-antenna"]
        self.assertEqual(nordic["symbol"], "NRF52832_JOHANSON_MANAGED_SIX_LAYER")
        self.assertEqual(len([m for m in nordic["mappings"] if m["kind"] == "member"]), 7)


if __name__ == "__main__":
    unittest.main()
