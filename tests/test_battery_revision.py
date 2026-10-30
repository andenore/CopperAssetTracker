"""Separate revision cannot inherit old routing or battery/BOM approval."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("battery_revision", ROOT / "scripts/review_battery_revision.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
LIBRARY = os.environ.get("COPPERLIB_REVIEW_ROOT")


class BatteryRevisionSourceTests(unittest.TestCase):
    def test_external_items_are_not_pcba_approvals(self):
        proposals = json.loads((ROOT / "revisions/battery-v1/procurement.json").read_text())
        self.assertTrue(all(not c["reviewed"] for c in proposals["components"].values()))
        self.assertIn("kjell.32058", proposals["external_not_pcba"])
        self.assertEqual(proposals["components"]["PWR/U_CHARGE"]["supplier_part"], "C129319")

    def test_new_circuit_is_separate_from_current_locked_source(self):
        draft = (ROOT / "revisions/battery-v1/power_tree.copper").read_text()
        canonical = (ROOT / "src/tracker/power_tree.copper").read_text()
        self.assertIn("charger.BQ24072TRGTR", draft)
        self.assertIn("charger.BQ24072RGTR", canonical)
        self.assertIn("role = decoupling", draft)
        self.assertNotIn("part BQ24072", draft)


@unittest.skipUnless(LIBRARY, "explicit CopperLib working-copy review root required")
class BatteryRevisionIntegrationTests(unittest.TestCase):
    def test_preliminary_screen_never_approves_missing_guarantees(self):
        result = review.assess(ROOT, Path(LIBRARY))
        checks = {c["id"]: c["status"] for c in result["checks"]}
        for identifier in ("provisional-cold", "provisional-hot", "revision-source-binding", "conditional-voltage"):
            self.assertEqual(checks["battery." + identifier], "pass")
        for identifier in ("guaranteed-temperature", "thermal-tracking", "charge-completion", "harness-current"):
            self.assertEqual(checks["battery." + identifier], "incomplete")
        self.assertFalse(result["qualified_release"])
        self.assertFalse(result["locked_release_input"])

    def test_metadata_cannot_override_actual_resistor(self):
        selection = json.loads((ROOT / "docs/battery-selection.json").read_text())
        design = dict(selection["temperature_cutoff_design"], tmr_ohms=10000)
        with self.assertRaisesRegex(ValueError, "resistor differs"):
            review.validate_circuit(ROOT, Path(LIBRARY), design)

    def test_isolation_cannot_be_bypassed(self):
        design = json.loads((ROOT / "docs/battery-selection.json").read_text())["temperature_cutoff_design"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / design["source"]
            target.parent.mkdir(parents=True)
            source = (ROOT / design["source"]).read_text()
            source = source.replace("net BAT_NTC { J_BAT.P3; TEMP.NTC; }", "net BAT_NTC { J_BAT.P3; TEMP.NTC; U_CHARGE.TS; }")
            source = source.replace("net TS_SENSE { TEMP.TS; U_CHARGE.TS; }", "net TS_SENSE { TEMP.TS; }")
            target.write_text(source)
            with self.assertRaisesRegex(ValueError, "TS bypasses"):
                review.validate_circuit(root, Path(LIBRARY), design)
