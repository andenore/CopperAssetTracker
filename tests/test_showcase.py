"""The README's committed examples must describe current source honestly."""
import hashlib
import json
from pathlib import Path
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
        self.assertEqual(sample["source_sha256"], hashlib.sha256((ROOT / "board.copper").read_bytes()).hexdigest())
        self.assertFalse(sample["qualified_release"])
        self.assertEqual(sample["component_count"], 83)
        self.assertEqual(len(sample["copper_layers"]), 6)

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
