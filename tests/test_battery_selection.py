import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("battery_review", ROOT / "scripts/review_battery_selection.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class BatterySelectionTests(unittest.TestCase):
    def assess_fixture(self, *, voltage_limit=4250, source_matches=True):
        # Synthetic data test the application binding; real source facts are
        # tested in CopperLib, not duplicated as a private component definition.
        selection = {"selected_external_cell": "fixture", "library_specification": "cell.json",
                     "library_charger_limits": "charger.json", "reviewed_power_source_sha256": "a" * 64}
        cell = {"id": "fixture", "datasheet_pack": {"charge_voltage_max_mv": voltage_limit,
                                                    "charge_temperature_max_c": 45}}
        charger = {"id": "ti.bq24072", "battery_regulation_max_mv": 4230,
                   "nominal_direct_10k_ntc_hot_c": 50}
        with patch.object(review, "load_json", side_effect=[selection, cell, charger]), \
             patch.object(review, "hash_file", return_value=("a" if source_matches else "b") * 64):
            return review.assess(ROOT, ROOT)

    def test_voltage_screen_does_not_approve_temperature_or_harness(self):
        result = self.assess_fixture()
        checks = {c["id"]: c["status"] for c in result["checks"]}
        self.assertEqual(checks["battery.charge-voltage"], "pass")
        self.assertEqual(checks["battery.nominal-hot-cutoff"], "fail")
        self.assertEqual(checks["battery.harness-current"], "incomplete")
        self.assertEqual(checks["battery.source-applicability"], "incomplete")
        self.assertFalse(result["qualified_release"])
        self.assertFalse(result["locked_release_input"])

    def test_strict_4200_mv_cell_fails_charger_voltage(self):
        result = self.assess_fixture(voltage_limit=4200)
        self.assertEqual(result["checks"][0]["status"], "fail")

    def test_source_change_invalidates_old_circuit_screens(self):
        result = self.assess_fixture(source_matches=False)
        self.assertTrue(all(c["status"] == "incomplete" for c in result["checks"]))

    def test_report_output_is_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            output.write_text("preserve me", encoding="utf-8")
            with patch("sys.argv", ["review", "--library-review-root", str(ROOT), "--output", str(output)]), \
                 patch.object(review, "assess", return_value=self.assess_fixture()):
                with self.assertRaises(FileExistsError):
                    review.main()
            self.assertEqual(output.read_text(), "preserve me")

    def test_selection_is_offboard_and_not_a_bom_approval(self):
        selection = json.loads((ROOT / "docs/battery-selection.json").read_text())
        self.assertEqual(selection["selected_external_cell"], "kjell.32058")
        self.assertEqual(selection["connector_pin_assignment"]["3"], "cell_mounted_ntc_to_protected_negative")
        self.assertEqual(selection["holder"]["id"], "mpd.bh-18650-w")
        self.assertEqual(selection["temperature_cutoff_design"]["nominal_target_max_c"], 35)
        self.assertFalse(selection["temperature_cutoff_design"]["assumptions_confirmed"])
        self.assertFalse(selection["qualified_release"])
