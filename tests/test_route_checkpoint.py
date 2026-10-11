"""The project composes intent; shared CopperScript owns native geometry guards."""
from pathlib import Path
from unittest.mock import patch
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import checkpoint_source as checkpoint
import check_modem_power_revision as power_check
import generate_readme_assets as showcase


class RouteCheckpointTests(unittest.TestCase):
    def test_readonly_consumers_use_shared_source_wrapper(self):
        self.assertIs(power_check.current_candidate, checkpoint.current_candidate)
        self.assertIs(showcase.current_candidate, checkpoint.current_candidate)

    def test_composition_delegates_all_geometry_to_shared_reader(self):
        project = ROOT / 'build/test-only-root'
        path, design, board, result = Path('candidate.kicad_pcb'), object(), object(), object()
        with patch.object(checkpoint, 'load_design', return_value=design) as load, \
             patch.object(checkpoint, 'FootprintResolver') as resolver, \
             patch.object(checkpoint, 'resolved_physicalize', return_value=board), \
             patch.object(checkpoint, 'apply_hard_macro_scene', return_value=board) as macro, \
             patch.object(checkpoint, 'read_front_native_checkpoint', return_value=result) as reader:
            self.assertIs(checkpoint.current_candidate(path, project_root=project), result)
        load.assert_called_once_with(project.resolve() / 'board.copper', locked=True, offline=True)
        resolver.assert_called_once_with(base_directory=project.resolve(), locked=True, offline=True)
        self.assertEqual(macro.call_count, 3)
        reader.assert_called_once_with(board, path, include_copper=True)

    def test_wrapper_does_not_hide_shared_validation_failure(self):
        with patch.object(checkpoint, 'posed_source', side_effect=ValueError('missing owner')):
            with self.assertRaisesRegex(ValueError, 'missing owner'):
                checkpoint.current_candidate(Path('candidate'))

    def test_no_repair_entrypoints_remain(self):
        retired = ('finish_routed_candidate', 'route_review_candidate', 'probe_open_routes',
            'probe_clock_routes', 'review_decoupling', 'seed_battery_usb_candidate', 'shorten_cellular_feed')
        for name in retired:
            with self.subTest(script=name):
                self.assertFalse((ROOT / 'scripts' / (name + '.py')).exists())

    def test_standard_review_has_no_pose_seed_or_named_repair_switches(self):
        makefile = (ROOT / 'Makefile').read_text()
        recipe = makefile.split('\nroute-review:\n', 1)[1].split('\nrender:', 1)[0]
        self.assertIn('route-board $(BOARD)', recipe)
        self.assertIn('--routing-profile $(REVIEW_PROFILE)', recipe)
        self.assertIn('--verify-plane-fill', recipe)
        for option in ('--pose-seed', '--route-v5', '--reroute-net', '--plane-pad'):
            self.assertNotIn(option, recipe)
