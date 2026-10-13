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

    def test_rf_revision_rejects_historical_pose_replay(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'new'
            args = self.arguments(output) + ['--modem-power', '--rf-layout', '--pose-seed', 'unused.kicad_pcb']
            with patch.object(sys, 'argv', args), patch.object(builder, 'assess') as assess:
                with self.assertRaisesRegex(ValueError, 'fresh source-only'):
                    builder.main()
                assess.assert_not_called()
            self.assertFalse(output.exists())

    def test_cellular_rf_revision_requires_modem_support_before_writes(self):
        with TemporaryDirectory() as directory:
            output = Path(directory)/'new'
            with patch.object(sys, 'argv', self.arguments(output)+['--rf-layout']), \
                 patch.object(builder, 'assess') as assess:
                with self.assertRaisesRegex(ValueError, '--modem-power'):
                    builder.main()
                assess.assert_not_called()
            self.assertFalse(output.exists())

    def test_rf_support_requires_both_parent_revisions_before_writes(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'new'
            with patch.object(sys, 'argv', self.arguments(output) + ['--rf-support']), \
                 patch.object(builder, 'assess') as assess:
                with self.assertRaisesRegex(ValueError, '--rf-layout and --modem-power'):
                    builder.main()
                assess.assert_not_called()
            self.assertFalse(output.exists())

    @unittest.skipUnless(os.environ.get('COPPERLIB_REVIEW_ROOT'), 'explicit library review root required')
    def test_rf_support_revision_adds_physical_dnp_without_shorting_dc_block(self):
        footprints = ROOT / '.copper-cache/pkg/0c22bbbc033f71e79d6d'
        if not footprints.is_dir():
            self.skipTest('locked KiCad footprint cache required')
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'source'
            args = ['build', '--modem-power', '--rf-layout', '--rf-support',
                '--library-review-root', os.environ['COPPERLIB_REVIEW_ROOT'],
                '--kicad-footprint-root', str(footprints), '--output', str(output)]
            with patch.object(sys, 'argv', args), patch('builtins.print'):
                self.assertEqual(builder.main(), 0)
            record = json.loads((output / 'revision-build.json').read_text())
            self.assertEqual(record['components'], 97)
            self.assertEqual(record['erc_errors'], 0)
            self.assertTrue(record['rf_support_revision'])
            self.assertEqual(record['gnss_antenna'], 'FXP611.07.0092C')
            self.assertEqual(len(record['inputs']['rf_library_selection']), 8)
            decision = json.loads((output / 'gnss-prototype-decision.json').read_text())
            self.assertEqual(decision['selected_option'], 'integrated-front-end-baseline')
            self.assertFalse(decision['production_approved'])
            self.assertFalse(decision['prototype_risk_acceptance_received'])
            review = json.loads((output / 'rf-library-evidence/gnss-datasheet-review.json').read_text())
            self.assertEqual(review['open_vio_sel_operating_limits']['vio_min_mv'], 2700)
            self.assertFalse(record['qualified_release'])
            self.assertFalse(record['assembly_reviewed'])
            source = (output / 'board.copper').read_text()
            self.assertIn('net CELL_RF { U_MODEM.ANT_MAIN; CELL_MATCH.HOST; }', source)
            self.assertIn('net CELL_ANT { CELL_MATCH.ANTENNA; J_CELL.SIGNAL; }', source)
            self.assertIn('D_GNSS_ESD.IO;', source)
            self.assertIn('constraint routing(CELL_MATCH/TUNE)', source)
            self.assertEqual(source.count('topology = "tree";'), 3)
            self.assertEqual(source.count('constraint routing(GNSS_RF)'), 1)
            self.assertIn('fixed_placement(J_CELL) { x = 4.4mm; y = 31.9mm;', source)
            self.assertIn('fixed_placement(CELL_MATCH/D_ESD) { x = 5.45mm; y = 27.9mm; rotation = 90;', source)
            self.assertNotIn('fixed_placement(C_STATUS_A)', source)
            self.assertNotIn('fixed_placement(C_STATUS_B)', source)
            self.assertNotIn('fixed_placement(U_MODEM_STATUS)', source)
            self.assertIn('decouples = "U_MODEM_STATUS.VCCA"', source)
            selections = {s['reference']: s for s in json.loads((output / 'assembly.lock').read_text())['selections']}
            self.assertEqual(len(selections), 95)
            self.assertNotIn('CELL_MATCH/C_HOST', selections)
            self.assertNotIn('CELL_MATCH/C_ANT', selections)
            self.assertEqual(selections['CELL_MATCH/D_ESD']['supplier_part'], 'C20336388')
            self.assertEqual(selections['D_GNSS_ESD']['supplier_part'], 'C779389')
            self.assertTrue(all(not s['reviewed'] for s in selections.values()))

    @unittest.skipUnless(os.environ.get('COPPERLIB_REVIEW_ROOT'), 'explicit library review root required')
    def test_real_modem_revision_build_records_unplaced_source_not_approval(self):
        footprints = ROOT / '.copper-cache/pkg/0c22bbbc033f71e79d6d'
        if not footprints.is_dir():
            self.skipTest('locked KiCad footprint cache required')
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'source'
            args = ['build', '--modem-power', '--rf-layout', '--library-review-root', os.environ['COPPERLIB_REVIEW_ROOT'],
                '--kicad-footprint-root', str(footprints), '--output', str(output)]
            with patch.object(sys, 'argv', args), patch('builtins.print'):
                self.assertEqual(builder.main(), 0)
            record = json.loads((output / 'revision-build.json').read_text())
            self.assertEqual(record['components'], 91)
            self.assertEqual(record['erc_errors'], 0)
            self.assertEqual(record['copper_layers'], 6)
            self.assertTrue(record['rf_layout_revision'])
            self.assertEqual(record['gnss_antenna_type'], 'passive')
            choice = json.loads((output / 'antenna-selection.json').read_text())
            self.assertFalse(choice['gnss']['board_supplied_bias'])
            self.assertFalse(choice['gnss']['external_antenna_power_required'])
            self.assertFalse(choice['qualified_release'])
            self.assertEqual(choice['cellular']['mpn'], 'FXUB16.07.0150AQ')
            self.assertEqual(record['cellular_antenna'], choice['cellular']['mpn'])
            fabrication = json.loads((output / 'fabrication-selection.json').read_text())
            self.assertEqual(fabrication['selected_profile'], 'JLC06161H-3313')
            self.assertEqual(record['selected_stackup'], fabrication['selected_profile'])
            self.assertFalse(fabrication['qualified_release'])
            self.assertFalse(fabrication['cellular_feed']['supplier_acceptance_received'])
            self.assertEqual(len(record['inputs']['rf_library_selection']), 4)
            for selection in record['inputs']['rf_library_selection'].values():
                self.assertEqual(builder.hash_file(output / selection['copied_path']), selection['sha256'])
            scene = json.loads((output / 'nrf-antenna-macro.json').read_text())
            self.assertTrue(scene['asset'].startswith('github.com/andenore/CopperLib/'))
            self.assertEqual(record['inputs']['rf_asset'], scene['asset_sha256'])
            self.assertIn('fixed_placement(U_NRF) { x = 84mm; y = 12mm;', (output / 'board.copper').read_text())
            source = (output / 'board.copper').read_text()
            self.assertIn('fixed_placement(J_CELL) { x = 4.4mm; y = 25.3mm; rotation = 180;', source)
            self.assertIn('width = 142um; clearance = 201um;', source)
            self.assertEqual(source.count('constraint routing(CELL_RF)'), 1)
            self.assertIn('cellular-feed.copper', record['inputs']['rf_revision'])
            self.assertEqual(record['placement_status'], 'not_run_use_shared_route_board')
            self.assertIsNone(record['inputs']['prior_native'])
            self.assertFalse(record['ordinary_historical_copper_imported'])
            self.assertFalse(record['qualified_release'])
            self.assertFalse(record['assembly_reviewed'])
            self.assertNotIn('pcb', record['outputs'])
            self.assertFalse((output / 'placed-unrouted.kicad_pcb').exists())
            selections = json.loads((output / 'assembly.lock').read_text())['selections']
            self.assertTrue(all(not s['reviewed'] for s in selections))
