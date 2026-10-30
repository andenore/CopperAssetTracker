"""Board bindings stay local; reusable requirements/algorithms do not."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).parents[1]
CACHE = ROOT / ".copper-cache/pkg"
# Requirements every contract of a kind must name; each needs reviewed external evidence.
REQUIRED = {
    "rf": {"matching-review", "impedance", "prototype-rf"},
    "power": {"component-ratings", "current-capacity", "layout-review", "transient", "prototype-power"},
    "interface": {"operating-mode", "layout-review", "impedance", "signal-integrity", "prototype-interface"},
}


def load_contract(path):
    contract = json.loads(Path(path).read_text(encoding="utf-8"))
    assert contract["schema"] == "copperscript-engineering-contract/v0.1" and contract["kind"] in REQUIRED, path
    ids = [item["id"] for item in contract["requirements"]]
    assert len(ids) == len(set(ids)) and REQUIRED[contract["kind"]] <= set(ids), path
    for item in contract["requirements"]:
        assert item["stage"] in {"design", "simulation", "bench"} and item["description"].strip(), item
        if item["id"] in REQUIRED[contract["kind"]]:
            assert item["algorithm"] == "external", item
    return contract


def library_root(path):
    """The verified CopperLib cache entry (`make fetch`) that holds a plan input."""
    relative = path.resolve().relative_to(CACHE.resolve())
    root = CACHE / relative.parts[0]
    assert "module github.com/andenore/CopperLib" in (root / "copper.mod").read_text(), root
    return root.resolve()


class EngineeringPlanTests(unittest.TestCase):
    def test_every_reusable_contract_is_library_owned(self):
        plan_path = ROOT / "docs/engineering-plan.json"
        plan = json.loads(plan_path.read_text())
        self.assertEqual(len(plan["contracts"]), 7)
        roots = set()
        for entry in plan["contracts"]:
            path = (plan_path.parent / entry["path"]).resolve()
            roots.add(library_root(path))
            self.assertFalse(load_contract(path)["production_publishable"])
        self.assertEqual(len(roots), 1)
        selected = plan["context"]["stackup"]
        # Consumers select and review; supplier facts live only in the library profile.
        self.assertEqual(set(selected), {"profile_path", "reviewed"})
        self.assertTrue(selected["reviewed"])
        profile_path = plan_path.parent / selected["profile_path"]
        self.assertEqual(library_root(profile_path), roots.pop())
        stackup = json.loads(profile_path.read_text())
        self.assertEqual(stackup["schema"], "copperscript-fabrication-stackup/v0.1")
        self.assertEqual(stackup["selected_profile"], "JLC06161H-3313")
        self.assertEqual(sum(layer["thickness_nm"] for layer in stackup["physical_layers"]), 1538400)
        self.assertIsNone(stackup["finished_via_plating_nm"])
        self.assertTrue(all(layer["loss_tangent"] is None for layer in stackup["physical_layers"] if layer["kind"] == "dielectric"))
        self.assertFalse(plan["context"]["operating_envelope"]["reviewed"])
        self.assertEqual(plan["evidence"], {})

    def test_ordering_keeps_existing_review_and_new_qualification_gates(self):
        make = shutil.which("make")
        self.assertIsNotNone(make, "GNU Make is required for the workflow gate test")
        shell = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"
        for action in ("package", "manufacturing", "order"):
            args = [make, action]
            if os.name == "nt" and shell.is_file():
                args.append("SHELL=" + str(shell).replace("\\", "/"))
            result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=30)
            self.assertNotEqual(result.returncode, 0, action)
            self.assertIn("Unsupported migration operation:", result.stderr)
            self.assertIn("No files exported", result.stderr)
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
