"""Source migration preserves locked asset identities and physical realization."""
from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest

from pcbir.compiler import compile_design_file
from pcbir.footprints import FootprintResolver
from pcbir.hard_macros import apply_hard_macro_scene
from pcbir.macro_bindings import prepare_macro_bindings
from pcbir.physicalize import PrototypePhysicalOptions, resolved_physicalize

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from probe_power_macros import isolated_probe


class MacroSourceMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = compile_design_file(ROOT / 'board.copper', locked=True, offline=True)
        cls.prepared = prepare_macro_bindings(cls.design, locked=True, offline=True)
        cls.options = PrototypePhysicalOptions(copper_layers=6, fabrication_profile='jlcpcb-six-layer')
        cls.physical = resolved_physicalize(cls.design, FootprintResolver(ROOT, locked=True, offline=True), cls.options)

    def test_exact_legacy_asset_identity_and_mapping_are_preserved(self):
        selected = {p.binding.name: p for p in self.prepared}
        for filename in ('nrf-antenna-macro.json', 'logic-power-macro.json', 'modem-power-macro.json'):
            scene = json.loads((ROOT / filename).read_text())
            prepared = selected[scene['name']]
            self.assertEqual(prepared.digest, scene['asset_sha256'])
            self.assertEqual({m.key: m.target for m in prepared.binding.mappings if m.kind == 'member'}, scene['bindings'])
            self.assertEqual({m.key: m.target for m in prepared.binding.mappings if m.kind == 'net'}, scene['net_bindings'])

    def test_physical_realization_matches_legacy_scene_loading(self):
        plain = replace(self.design, electrical=replace(self.design.electrical, physical_macros=()))
        legacy = resolved_physicalize(plain, FootprintResolver(ROOT, locked=True, offline=True), self.options)
        for filename in ('nrf-antenna-macro.json', 'logic-power-macro.json', 'modem-power-macro.json'):
            legacy = apply_hard_macro_scene(legacy, ROOT / filename, locked=True, offline=True)
        self.assertEqual(legacy.hard_macros, self.physical.hard_macros)
        self.assertEqual(legacy.rigid_clusters, self.physical.rigid_clusters)
        self.assertEqual(legacy.nets, self.physical.nets)

    def test_power_probe_consumes_source_selection(self):
        selected = next(p for p in self.prepared if p.binding.name == 'logic-buck-boost')
        probe = isolated_probe(self.physical, selected, port_consumers=False)
        self.assertEqual(probe.materialized_macros, ('logic-buck-boost',))
        self.assertEqual(probe.hard_macros[0].asset_sha256, selected.digest)

    def test_build_recipe_does_not_repeat_source_macro_bindings(self):
        physical_line = next(l for l in (ROOT / 'Makefile').read_text().splitlines() if l.startswith('PHYSICAL :='))
        self.assertNotIn('--hard-macro', physical_line)
