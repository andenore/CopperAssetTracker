"""Power revision composition is explicit and cannot inherit prior approval."""
import json
from pathlib import Path
from unittest.mock import patch
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_battery_revision as builder
import probe_open_routes as probe
import check_modem_power_revision as power_check


class ModemPowerRevisionTests(unittest.TestCase):
    def test_checkpoint_never_overwrites_report(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'retained.json'
            output.write_text('retained')
            with patch.object(sys, 'argv', ['check', '--pcb', str(root / 'pcb'),
                '--project-root', str(root), '--native-cli', 'unused', '--output', str(output)]), \
                patch.object(power_check, 'current_candidate') as load:
                with self.assertRaisesRegex(ValueError, 'preserve prior reports'):
                    power_check.main()
            load.assert_not_called()
            self.assertEqual(output.read_text(), 'retained')

    def test_checkpoint_requires_actual_four_links_before_native_invocation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            pcb, output = root / 'pcb', root / 'report.json'
            pcb.write_text('fixture')
            with patch.object(sys, 'argv', ['check', '--pcb', str(pcb), '--project-root', str(root),
                '--native-cli', 'unused', '--output', str(output)]), \
                patch.object(power_check, 'current_candidate', return_value=SimpleNamespace(placements=(), decoupling_links=())), \
                patch.object(power_check, 'RoutingClearanceIndex'), \
                patch.object(power_check.subprocess, 'run') as native:
                with self.assertRaisesRegex(ValueError, 'four explicit modem bypass links'):
                    power_check.main()
            native.assert_not_called()
            self.assertFalse(output.exists())

    def test_zone_is_regional_and_does_not_widen_detect_or_feedback(self):
        source = (ROOT / 'revisions/modem-power-v1/distribution.copper').read_text()
        self.assertIn('layers = "In2.Cu"', source)
        self.assertIn('minimum_width = 2mm', source)
        self.assertIn('reserve_routing = true', source)
        self.assertNotIn('constraint routing', source)
        self.assertIn('minimum_width = 2mm; priority = 2;', source)
        self.assertIn('minimum_width = 0.2mm; priority = 1;', source)

    def test_new_candidates_do_not_inherit_bom_approval(self):
        proposals = json.loads((ROOT / 'revisions/modem-power-v1/procurement.json').read_text())
        self.assertTrue(all(not p['reviewed'] for p in proposals['components'].values()))
        self.assertEqual(proposals['reuse_candidates']['U_MODEM/U'], 'U_MODEM')

    def test_power_macro_pins_new_reusable_asset(self):
        scene = json.loads((ROOT / 'revisions/modem-power-v1/modem-power-macro.json').read_text())
        self.assertTrue(scene['asset'].endswith('tps63020-six-layer-enabled-power-output.json'))
        self.assertEqual(len(scene['asset_sha256']), 64)
        self.assertEqual(scene['net_bindings']['VOUT'], 'V3V8')

    def test_default_diagnostic_loader_stays_locked(self):
        # No accidental default downgrade when the new local-review mode is added.
        with patch.object(probe, 'load_design', side_effect=RuntimeError('checkpoint')) as load:
            with self.assertRaisesRegex(RuntimeError, 'checkpoint'):
                probe.posed_source(Path('unused'))
        load.assert_called_once_with(probe.ROOT.resolve() / 'board.copper', locked=True, offline=True)

    def test_explicit_revision_loader_uses_selected_root(self):
        project = ROOT / 'build/explicit-fixture'
        with patch.object(probe, 'load_design', side_effect=RuntimeError('checkpoint')) as load:
            with self.assertRaisesRegex(RuntimeError, 'checkpoint'):
                probe.posed_source(Path('unused'), project_root=project, locked=False)
        load.assert_called_once_with(project.resolve() / 'board.copper', locked=False, offline=True)
