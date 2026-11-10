"""The README's committed examples must describe current source honestly."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest
from xml.etree import ElementTree

from copper_cli import compile_board

ROOT = Path(__file__).resolve().parents[1]
SHOWCASE = ROOT / "docs/showcase"


class ShowcaseTests(unittest.TestCase):
    def test_electrical_excerpt_matches_current_authoritative_ir(self):
        current = compile_board()
        sample = json.loads((SHOWCASE / "electrical-ir.excerpt.json").read_text())
        for key in ("schema", "kind", "name"):
            self.assertEqual(sample[key], current[key])
        for key in ("components", "nets"):
            for item in sample[key]:
                self.assertIn(item, current[key])

    def test_snapshot_is_source_bound_and_not_a_release(self):
        sample = json.loads((SHOWCASE / "snapshot.json").read_text())
        self.assertEqual(sample["schema"], "copperassettracker-showcase/v3")
        self.assertRegex(sample["source"]["git_commit"], r"^[0-9a-f]{40}$")
        self.assertRegex(sample["compiler"]["copperscript_commit"], r"^[0-9a-f]{40}$")
        # Bound to the current design: rerun `make showcase` after changing it.
        design = {name: digest for name, digest in sample["source"]["input_sha256"].items()
                  if name.endswith((".copper", ".mod", ".lock"))}
        self.assertIn("board.copper", design)
        for name, digest in design.items():
            with self.subTest(input=name):
                self.assertEqual(digest, hashlib.sha256((ROOT / name).read_bytes()).hexdigest())
        self.assertFalse(sample["qualified_release"])
        self.assertEqual(sample["independent_cam"], "not run")
        self.assertEqual(sample["route"]["status"], "pass")
        self.assertEqual(sample["route"]["unrouted_ordinary_nets"], [])
        self.assertGreater(sample["component_count"], 0)
        self.assertEqual(sample["track_count"], sample["route"]["tracks"])
        self.assertEqual(sample["via_count"], sample["route"]["vias"])
        self.assertGreater(sample["track_count"], 0)
        self.assertGreater(sample["via_count"], 0)
        self.assertEqual(sample["blocked_requirement_count"], sample["route"]["requirements"]["blocked"])
        self.assertGreater(sample["blocked_requirement_count"], 0)
        self.assertTrue(sample["native_drc"]["passed"])
        self.assertTrue(sample["native_drc"]["not_checked"])
        self.assertIn("CAM read-back PASSED", sample["native_drc"]["cam_readback"])
        self.assertEqual(sample["native_unconnected_item_count"], 0)
        self.assertEqual(sample["native_drc_violation_count"], 0)
        self.assertEqual(len(sample["copper_layers"]), 6)
        for key in ("pcb_sha256",):
            self.assertRegex(sample[key], r"^[0-9a-f]{64}$")
        for name, digest in sample["rendered_assets"].items():
            self.assertEqual(digest, hashlib.sha256((SHOWCASE / name).read_bytes()).hexdigest())

    def test_readme_json_examples_match_committed_excerpts(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        examples = [json.loads(block) for block in re.findall(r"```json\n(.*?)\n```", readme, re.S)]
        self.assertEqual(len(examples), 3)
        electrical = json.loads((SHOWCASE / "electrical-ir.excerpt.json").read_text())
        capacitor = next(c for c in electrical["components"] if c["ref"] == "C_MCU")
        # The README intentionally omits algorithm-only SI base_value.
        component = {**capacitor, "value": {k: v for k, v in capacitor["value"].items() if k != "base_value"}}
        self.assertEqual(examples[0], component)
        physical = json.loads((SHOWCASE / "physical-ir.excerpt.json").read_text())
        self.assertIn(examples[1], physical["placements"])
        snapshot = json.loads((SHOWCASE / "snapshot.json").read_text())
        self.assertEqual(examples[2], {key: snapshot[key] for key in examples[2]})
        self.assertIn("module U_MODEM: simcom.SIM7670G_VBAT_BYPASS;", readme)
        self.assertIn(f"{snapshot['component_count']} footprints", readme)
        self.assertIn(f"same {snapshot['component_count']}-footprint", readme)

    def test_images_are_native_svg_and_linked_in_readme(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for name in ("placement", "routing-top", "routing-inner", "routing-bottom", "routing-all"):
            with self.subTest(name=name):
                path = SHOWCASE / f"{name}.svg"
                self.assertEqual(ElementTree.parse(path).getroot().tag, "{http://www.w3.org/2000/svg}svg")
                self.assertIn(f"docs/showcase/{name}.svg", readme)

    def test_rendering_is_native_and_includes_fill_free_stack(self):
        snapshot = json.loads((SHOWCASE / "snapshot.json").read_text())
        rendering = json.loads((SHOWCASE / "rendering.json").read_text())
        self.assertEqual(rendering["renderer"], "copper render")
        self.assertEqual(set(rendering["views"]), {f"{name}.svg" for name in (
            "placement", "routing-top", "routing-inner", "routing-bottom", "routing-all")})
        combined = rendering["views"]["routing-all.svg"]
        self.assertFalse(combined["zone_fills"])
        drawn = {plate.split("&")[0].split(":")[0] for plate in combined["plates"]}
        self.assertTrue(set(snapshot["copper_layers"]) <= drawn)
        for name in ("placement.svg", "routing-top.svg", "routing-all.svg"):
            self.assertIn(rendering["exposed_copper_color"], (SHOWCASE / name).read_text())

    def test_capacitor_examples_use_plain_numbers_and_engineering_units(self):
        electrical = json.loads((SHOWCASE / "electrical-ir.excerpt.json").read_text())
        capacitor = next(c for c in electrical["components"] if c["ref"] == "C_MCU")
        self.assertEqual(capacitor["value"], {"value": "100", "unit": "nF", "base_value": "0.0000001"})
        physical = json.loads((SHOWCASE / "physical-ir.excerpt.json").read_text())
        placement = next(p for p in physical["placements"] if p["reference"] == "C_MCU")
        self.assertIn("millimetres", physical["units"])
        for value in placement["position_mm"].values():
            self.assertRegex(value, r"^-?\d+(?:\.\d+)?$")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("1E+2", readme)
        self.assertNotIn("1E-7", readme)


if __name__ == "__main__":
    unittest.main()
