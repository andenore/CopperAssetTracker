"""The README's committed examples must describe current source honestly."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest
from xml.etree import ElementTree

from pcbir.loader import load_design
from pcbir.serializer import board_to_dict

ROOT = Path(__file__).resolve().parents[1]
SHOWCASE = ROOT / "docs/showcase"


class ShowcaseTests(unittest.TestCase):
    def test_electrical_excerpt_matches_current_authoritative_ir(self):
        current = board_to_dict(load_design(ROOT / "board.copper", locked=True, offline=True))
        sample = json.loads((SHOWCASE / "electrical-ir.excerpt.json").read_text())
        for key in ("schema", "kind", "name"):
            self.assertEqual(sample[key], current[key])
        for key in ("components", "nets"):
            for item in sample[key]:
                self.assertIn(item, current[key])

    def test_snapshot_is_source_bound_and_not_a_release(self):
        sample = json.loads((SHOWCASE / "snapshot.json").read_text())
        self.assertRegex(sample["canonical_source_commit"], r"^[0-9a-f]{40}$")
        historical = sample["canonical_source_status"] in {
            "historical_input_before_macro_source_migration", "historical_input_before_macro_definition_migration"}
        if historical:
            self.assertNotEqual(sample["canonical_source_sha256"], hashlib.sha256((ROOT / "board.copper").read_bytes()).hexdigest())
            def input_bytes(name):
                if 'canonical_input_snapshots' in sample:
                    path = (SHOWCASE / sample['canonical_input_snapshots'][name]).resolve()
                    self.assertTrue(path.is_relative_to(SHOWCASE.resolve()))
                    return path.read_bytes()
                return subprocess.check_output(["git", "show", sample["canonical_source_commit"] + ":" + name], cwd=ROOT)
        else:
            self.assertEqual(sample["canonical_source_status"], "current_source")
            self.assertEqual(sample["macro_binding"], "in_language")
            def input_bytes(name):
                return (ROOT / name).read_bytes()
        self.assertEqual(sample["canonical_source_sha256"], hashlib.sha256(input_bytes("board.copper")).hexdigest())
        for name, digest in sample["composition_inputs"].items():
            self.assertEqual(digest, hashlib.sha256(input_bytes(name)).hexdigest())
        source = ROOT / sample["source"]
        if source.exists():
            self.assertEqual(sample["source_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertFalse(sample["qualified_release"])
        self.assertFalse(sample["locked_release_input"])
        self.assertEqual(sample["schema"], "copperassettracker-showcase/v2")
        self.assertEqual(sample["revision"], "rf-support-v1")
        self.assertEqual(sample["component_count"], 97)
        self.assertGreater(sample["track_count"], 0)
        self.assertGreater(sample["via_count"], 0)
        self.assertGreater(sample["blocked_requirement_count"], 0)
        expected_cam = ("skipped_by_request" if sample["canonical_source_status"] == "historical_input_before_macro_source_migration"
                        else "not_run_for_this_routing_review")
        self.assertEqual(sample["independent_cam"], expected_cam)
        for key in ("pcb_sha256", "source_lock_sha256", "assembly_lock_sha256",
                    "source_freeze_sha256", "native_drc_sha256", "route_summary_sha256"):
            self.assertRegex(sample[key], r"^[0-9a-f]{64}$")
        self.assertEqual(sample["native_unconnected_item_count"], 0)
        self.assertEqual(sample["native_drc_violation_count"], 0)
        self.assertEqual(len(sample["copper_layers"]), 6)
        pcb = ROOT / sample["pcb"]
        if pcb.exists():
            self.assertEqual(sample["pcb_sha256"], hashlib.sha256(pcb.read_bytes()).hexdigest())
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

    def test_rendering_preserves_recorded_board_and_includes_fill_free_stack(self):
        snapshot = json.loads((SHOWCASE / "snapshot.json").read_text())
        rendering = json.loads((SHOWCASE / "rendering.json").read_text())
        self.assertEqual(rendering["pcb_sha256"], snapshot["pcb_sha256"])
        self.assertEqual(rendering["all_layers"], snapshot["copper_layers"])
        self.assertEqual(rendering["native_geometry"]["footprints"], snapshot["component_count"])
        self.assertEqual(rendering["native_geometry"]["tracks_and_vias"], snapshot["track_count"] + snapshot["via_count"])
        self.assertGreater(rendering["native_geometry"]["pads"], 0)
        self.assertFalse(rendering["views"]["routing-all.svg"]["copper_fills"])
        for name in ("placement.svg", "routing-top.svg", "routing-all.svg"):
            self.assertIn(rendering["pad_color"], (SHOWCASE / name).read_text())

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
