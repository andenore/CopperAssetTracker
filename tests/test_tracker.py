"""Source contracts, not a hardware safety or RF qualification certificate."""
import csv
import hashlib
import json
from pathlib import Path
import unittest

from copper_cli import (assembly_check, assembly_snapshot, audit_footprints, check, compile_board,
                        components, constraints, fixed_placements, nanometres, net, net_names, part,
                        query, routing_rules)

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
        self.assertEqual({p.name for p in (ROOT / "src/tracker").glob("*.copper")}, {"power_tree.copper"})
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
        # JLCPCB places everything fitted; consigned parts are hand-fitted.
        # Every RF matching land is fitted for the printed antennas.
        fitted = [s for s in self.lock["selections"] if s["populate"] != "none"]
        self.assertTrue(all(s["mpn"] and s["supplier_part"] for s in fitted))
        self.assertEqual({s["reference"] for s in fitted if s["supplier"] != "jlcpcb"},
                         {s["reference"] for s in fitted if s["populate"] == "consigned"})
        self.assertEqual({s["reference"] for s in self.lock["selections"] if s["populate"] == "none"}, set())
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
        # Each selection is bound to its own component and every one is
        # reviewed but the printed antennas' new matching parts, which await
        # a human review; a source change that alters another fails again.
        pending = {"L_BT_SHUNT", "C_BT_SERIES", "C_GNSS_SERIES", "C_GNSS_SHUNT", "C_CELL_SHUNT1", "L_CELL_SERIES", "L_CELL_SHUNT"}
        self.assertEqual(r["reviewed_count"], len(self.lock["selections"]) - len(pending))
        self.assertEqual({s["reference"] for s in self.lock["selections"] if not s["reviewed"]}, pending)
        self.assertTrue(all(i["code"] == "REVIEW_REQUIRED" for i in r["issues"]), r["issues"])

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
        # The matching network splits the feed. The two module-side budgets and
        # the antenna-side span between two fixed pads stay inside the
        # SIM7672X V1.01 p60 20 mm module-to-antenna maximum; the antenna-side
        # net also carries the radiator, so it has no routed-length budget.
        rules = routing_rules()
        feed = [rules[n] for n in ("CELL_RF", "CELL_RF_MATCH", "CELL_RF_ANT")]
        self.assertEqual(sum(nanometres(r["max_length"]) for r in feed[:2]), 12000000)
        self.assertNotIn("max_length", rules["CELL_RF_ANT"])
        self.assertEqual(rules["CELL_RF_ANT"]["kind"], "rf_feed")
        for rule in feed:
            self.assertEqual(rule["max_vias"], 0)
            self.assertEqual(rule["allowed_layers"], "F.Cu")
        # The network runs along x = 4.4 mm from the LTE antenna feed, which
        # its antenna constraint fixes on the same column.
        fixed = fixed_placements()["C_CELL_SERIES"]
        self.assertEqual((nanometres(fixed["x"]), nanometres(fixed["y"])), (4400000, 18900000))
        self.assertEqual(net("CELL_RF_ANT"), {("C_CELL_SERIES", "2"), ("ANT_CELL", "FEED")})

    def test_rf_macro_identity(self):
        # The retained Johanson asset stays bound to its hash for history.
        scene = json.loads((ROOT / "nrf-antenna-macro.json").read_text())
        self.assertEqual(hashlib.sha256((ROOT / scene["asset"]).read_bytes()).hexdigest(), scene["asset_sha256"])
        macros = {m["name"]: m for m in self.design["physical_macros"]}
        self.assertEqual(len(macros), 3)
        nordic = macros["nordic-rf"]
        self.assertEqual(nordic["symbol"], "NRF52832_NORDIC_MATCH_SIX_LAYER")
        self.assertEqual({m["target"] for m in nordic["mappings"] if m["kind"] == "member"},
                         {"U_NRF", "C_BT_MATCH", "L_BT_MATCH"})

    def test_three_synthesized_trace_antennas_replace_chip_and_connectors(self):
        removed = {"J_CELL", "J_GNSS", "C_ANT_SERIES", "L_ANT_SHUNT", "L_ANT_SERIES"}
        self.assertTrue(removed.isdisjoint(self.components))
        self.assertNotIn("ANT_TEE", net_names())
        source = (ROOT / "board.copper").read_text()
        self.assertNotIn("johanson", source)
        self.assertNotIn("molex_sma", source)
        antennas = {c["parameters"]["name"]: c for c in constraints("antenna")}
        self.assertEqual(set(antennas), {"lte", "ble", "gnss"})
        feeds = {"lte": ("ANT_CELL", "CELL_RF_ANT"), "ble": ("ANT_BT", "ANT_FEED"),
                 "gnss": ("ANT_GNSS", "GNSS_RF_ANT")}
        for name, (feed, feed_net) in feeds.items():
            antenna = antennas[name]
            self.assertEqual(antenna["targets"], [feed + ".FEED"])
            self.assertEqual(self.components[feed], "rf.AntennaFeed")
            self.assertIn((feed, "FEED"), net(feed_net))
            self.assertEqual(antenna["parameters"]["ground"], "GND")
            # Tuned in the full-wave model: geometry and its site digest.
            self.assertTrue(antenna["parameters"]["geometry"].startswith(("monopole ", "meander ")))
            self.assertTrue(antenna["parameters"]["tuned_for"].startswith("sha256:"))
            report = json.loads((ROOT / "revisions/pcb-antennas-v1" / f"{name}-synthesis.json").read_text())
            self.assertEqual(report["site_digest"], antenna["parameters"]["tuned_for"])
            self.assertEqual(report["geometry"], antenna["parameters"]["geometry"])
        self.assertEqual(antennas["ble"]["parameters"]["bands"], "2400 MHz-2483.5 MHz")
        self.assertEqual(antennas["gnss"]["parameters"]["bands"], "1559 MHz-1606 MHz")
        self.assertEqual(antennas["lte"]["parameters"]["bands"], "791 MHz-862 MHz")
        # The feed pads are bare copper: no BOM or CPL line.
        feed_part = part(self.design, "rf.AntennaFeed")
        self.assertFalse(feed_part["assembled"])


if __name__ == "__main__":
    unittest.main()
