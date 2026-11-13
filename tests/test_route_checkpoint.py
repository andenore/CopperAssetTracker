"""The project composes intent; shared CopperScript owns native geometry guards."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RouteCheckpointTests(unittest.TestCase):
    def test_no_repair_entrypoints_remain(self):
        retired = ('finish_routed_candidate', 'route_review_candidate', 'probe_open_routes',
            'probe_clock_routes', 'review_decoupling', 'seed_battery_usb_candidate', 'shorten_cellular_feed')
        for name in retired:
            with self.subTest(script=name):
                self.assertFalse((ROOT / 'scripts' / (name + '.py')).exists())

    def test_standard_review_has_no_pose_seed_or_named_repair_switches(self):
        settings = (ROOT / 'Makefile').read_text()
        recipe = settings.split('\nroute:\n', 1)[1].split('\n', 1)[0]
        self.assertIn('$(COPPER) build board.copper', recipe)
        self.assertIn('-- $(ROUTE)', recipe)
        self.assertFalse((ROOT / 'make').exists())
        for option in ('--pose-seed', '--route-v5', '--reroute-net', '--plane-pad'):
            self.assertNotIn(option, settings)
