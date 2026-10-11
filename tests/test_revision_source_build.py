"""Fresh revision composition never requires historical native route artifacts."""
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_battery_revision as builder


class RevisionSourceBuildTests(unittest.TestCase):
    def arguments(self, output):
        return ['build', '--library-review-root', 'unused-lib',
            '--kicad-footprint-root', 'unused-footprints', '--output', str(output)]

    def test_default_reaches_composition_without_reading_historical_pcb(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'new'
            with patch.object(sys, 'argv', self.arguments(output)), \
                 patch.object(builder, 'hash_file', side_effect=AssertionError('unexpected seed read')) as hashes, \
                 patch.object(builder, 'assess', side_effect=RuntimeError('composition reached')):
                with self.assertRaisesRegex(RuntimeError, 'composition reached'):
                    builder.main()
                hashes.assert_not_called()
            self.assertFalse(output.exists())

    def test_explicit_unpinned_seed_still_rejected_before_writes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            seed, output = root / 'other.kicad_pcb', root / 'new'
            seed.write_text('not the historical checkpoint')
            with patch.object(sys, 'argv', self.arguments(output) + ['--pose-seed', str(seed)]), \
                 patch.object(builder, 'assess') as assess:
                with self.assertRaisesRegex(ValueError, 'pinned RF checkpoint'):
                    builder.main()
                assess.assert_not_called()
            self.assertFalse(output.exists())

    def test_source_only_build_never_overwrites_existing_output(self):
        with TemporaryDirectory() as directory:
            output = Path(directory)
            sentinel = output / 'retained'
            sentinel.write_text('preserve')
            with patch.object(sys, 'argv', self.arguments(output)), patch.object(builder, 'assess') as assess:
                with self.assertRaisesRegex(ValueError, 'output exists'):
                    builder.main()
                assess.assert_not_called()
            self.assertEqual(sentinel.read_text(), 'preserve')

    @unittest.skipUnless(os.environ.get('COPPERLIB_REVIEW_ROOT'), 'explicit library review root required')
    def test_real_modem_revision_build_records_unplaced_source_not_approval(self):
        footprints = ROOT / '.copper-cache/pkg/0c22bbbc033f71e79d6d'
        if not footprints.is_dir():
            self.skipTest('locked KiCad footprint cache required')
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'source'
            args = ['build', '--modem-power', '--library-review-root', os.environ['COPPERLIB_REVIEW_ROOT'],
                '--kicad-footprint-root', str(footprints), '--output', str(output)]
            with patch.object(sys, 'argv', args), patch('builtins.print'):
                self.assertEqual(builder.main(), 0)
            record = json.loads((output / 'revision-build.json').read_text())
            self.assertEqual(record['components'], 91)
            self.assertEqual(record['erc_errors'], 0)
            self.assertEqual(record['copper_layers'], 6)
            self.assertEqual(record['placement_status'], 'not_run_use_shared_route_board')
            self.assertIsNone(record['inputs']['prior_native'])
            self.assertFalse(record['ordinary_historical_copper_imported'])
            self.assertFalse(record['qualified_release'])
            self.assertFalse(record['assembly_reviewed'])
            self.assertNotIn('pcb', record['outputs'])
            self.assertFalse((output / 'placed-unrouted.kicad_pcb').exists())
            selections = json.loads((output / 'assembly.lock').read_text())['selections']
            self.assertTrue(all(not s['reviewed'] for s in selections))
