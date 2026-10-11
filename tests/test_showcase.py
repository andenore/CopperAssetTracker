"""The README's committed examples must describe current source honestly."""
import hashlib
import json
from pathlib import Path
import re
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
        self.assertEqual(sample["canonical_source_sha256"], hashlib.sha256((ROOT / "board.copper").read_bytes()).hexdigest())
        for name, digest in sample["composition_inputs"].items():
            self.assertEqual(digest, hashlib.sha256((ROOT / name).read_bytes()).hexdigest())
        source = ROOT / sample["source"]
        if source.exists():
            self.assertEqual(sample["source_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertFalse(sample["qualified_release"])
        self.assertFalse(sample["locked_release_input"])
        self.assertEqual(sample["revision"], "modem-power-v1")
        self.assertEqual(sample["component_count"], 91)
        self.assertEqual(sample["net_count"], 75)
        self.assertEqual((sample["track_count"], sample["via_count"]), (921, 314))
        self.assertEqual(sample["native_unconnected_item_count"], 0)
        self.assertEqual(sample["native_drc_violation_count"], 0)
        self.assertEqual(len(sample["copper_layers"]), 6)
        for name, digest in sample["review_inputs"].items():
            path = source.parent / name
            if path.exists():
                self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())
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
        self.assertIn("91 placements, 75", readme)
        self.assertIn("The same 91 candidate component poses", readme)

    def test_images_are_native_svg_and_linked_in_readme(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for name in ("placement", "routing-top", "routing-inner", "routing-bottom"):
            with self.subTest(name=name):
                path = SHOWCASE / f"{name}.svg"
                self.assertEqual(ElementTree.parse(path).getroot().tag, "{http://www.w3.org/2000/svg}svg")
                self.assertIn(f"docs/showcase/{name}.svg", readme)

    def test_capacitor_examples_use_plain_numbers_and_engineering_units(self):
        electrical = json.loads((SHOWCASE / "electrical-ir.excerpt.json").read_text())
        capacitor = next(c for c in electrical["components"] if c["ref"] == "C_MCU")
        self.assertEqual(capacitor["value"], {"value": "100", "unit": "nF", "base_value": "0.0000001"})
        physical = json.loads((SHOWCASE / "physical-ir.excerpt.json").read_text())
        placement = next(p for p in physical["placements"] if p["reference"] == "C_MCU")
        self.assertEqual(placement["value"], "100 nF")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("1E+2", readme)
        self.assertNotIn("1E-7", readme)


if __name__ == "__main__":
    unittest.main()
