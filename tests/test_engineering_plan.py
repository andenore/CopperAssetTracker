"""Board bindings stay local; reusable requirements/algorithms do not."""
import json
from pathlib import Path
import unittest

from pcbir.engineering_qualification import load_contract
from pcbir.packages import resolve_module_root
from pcbir.stackup_qualification import resolve_stackup_context

ROOT = Path(__file__).parents[1]


class EngineeringPlanTests(unittest.TestCase):
    def test_every_reusable_contract_is_library_owned(self):
        plan_path = ROOT / "docs/engineering-plan.json"
        plan = json.loads(plan_path.read_text())
        self.assertEqual(len(plan["contracts"]), 7)
        library = resolve_module_root(ROOT / "board.copper", "github.com/andenore/CopperLib",
                                      locked=True, offline=True)
        for entry in plan["contracts"]:
            path = (plan_path.parent / entry["path"]).resolve()
            self.assertTrue(path.is_relative_to(library))
            self.assertFalse(load_contract(path)["production_publishable"])
        context = resolve_stackup_context(plan_path, plan)
        self.assertTrue(context["stackup"]["reviewed"])
        self.assertEqual(context["stackup"]["selected_profile"], "JLC06161H-3313")
        self.assertEqual(sum(layer["thickness_nm"] for layer in context["stackup"]["physical_layers"]), 1538400)
        self.assertIsNone(context["stackup"]["finished_via_plating_nm"])
        self.assertTrue(all(layer["loss_tangent"] is None for layer in context["stackup"]["physical_layers"] if layer["kind"] == "dielectric"))
        self.assertFalse(plan["context"]["operating_envelope"]["reviewed"])
        self.assertEqual(plan["evidence"], {})

    def test_ordering_keeps_existing_review_and_new_qualification_gates(self):
        makefile = (ROOT / "Makefile").read_text()
        self.assertIn("order: manufacturing cam-audit engineering-audit qualification", makefile)
        self.assertIn("manufacturing: assembly route verify", makefile)
        for command in ("audit-cam", "assess-engineering", "qualification-gate"):
            self.assertEqual(makefile.count("$(COPPER) " + command + " "), 1)
        self.assertIn('"$(CARGO_HOME)/bin/copper', makefile)
        lock = json.loads((ROOT / "assembly.lock").read_text())
        self.assertEqual(len(lock["selections"]), 83)
        self.assertTrue(all(selection["reviewed"] for selection in lock["selections"]))

    def test_actual_usb_pair_bindings_are_board_specific_screens(self):
        plan = json.loads((ROOT / "docs/engineering-plan.json").read_text())
        screens = plan["differential_pair_screens"]
        self.assertEqual({(s["positive_net"], s["negative_net"]) for s in screens},
                         {("USB_DP_MCU", "USB_DM_MCU"), ("USB_DP_MODEM", "USB_DM_MODEM")})
        self.assertTrue(all(s["maximum_search_gap_nm"] == 400000 for s in screens))
        self.assertEqual(len({s["id"] for s in screens}), 2)
        self.assertFalse({s["id"] for s in screens} & {s["id"] for s in plan["microstrip_screens"]})
        self.assertTrue((ROOT / "docs/production-plan.md").is_file())

    def test_whole_usb_link_is_mandatory_not_just_auxiliary_geometry(self):
        plan = json.loads((ROOT / "docs/engineering-plan.json").read_text())
        usb = next(c for c in plan["contracts"] if c["scope"] == "usb-link")
        contract = load_contract(ROOT / "docs" / usb["path"])
        self.assertEqual(contract["kind"], "interface")
        self.assertEqual(len(contract["requirements"]), 5)
        self.assertTrue(all(r["algorithm"] == "external" for r in contract["requirements"]))
        self.assertEqual(usb["bindings"]["layout-review"]["inline_components"], ["FL_USB"])
        self.assertEqual(usb["bindings"]["operating-mode"]["maximum_host_rate_bps"], 12000000)
        mode = usb["bindings"]["operating-mode"]
        self.assertIs(mode["required_battery_usb_operation"], True)
        self.assertIn("battery-only", mode["required_functional_states"])
        self.assertIn("charging-cable-unplug-with-battery", mode["required_functional_states"])
        self.assertEqual(set(mode["required_safe_states"]),
                         {"modem-disabled", "battery-undervoltage", "external-power-attach"})
        self.assertIs(mode["external_connector_backfeed_allowed"], False)
        self.assertFalse(mode["reviewed"])
        self.assertTrue((ROOT / "docs/usb-battery-power.md").is_file())
        self.assertEqual({s["net"] for s in plan["route_path_screens"]},
                         {s[k] for s in plan["differential_pair_screens"] for k in ("positive_net", "negative_net")})
