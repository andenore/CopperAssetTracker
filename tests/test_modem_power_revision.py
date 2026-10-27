"""Power revision composition is explicit and cannot inherit prior approval."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]


class ModemPowerRevisionTests(unittest.TestCase):
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
