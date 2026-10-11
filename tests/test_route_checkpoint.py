"""Resume checks reject stale native intent; not manufacturing qualification."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import sys
import unittest
import json
from unittest.mock import patch

from pcbir.physical import BoardSide, CopperLayer, PadKind, PadReference, PadShape, Point, TrackSegment

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import finish_routed_candidate as checkpoint
import seed_battery_usb_candidate as usb_migration
import shorten_cellular_feed as rf_migration


class RouteCheckpointTests(unittest.TestCase):
    def test_rf_migration_refuses_unpinned_input(self):
        with TemporaryDirectory() as directory:
            pcb = Path(directory) / 'other.kicad_pcb'
            pcb.write_text('unrelated input')
            output = Path(directory) / 'new/routed.kicad_pcb'
            with patch.object(sys, 'argv', ['rf', '--pcb', str(pcb), '--output', str(output)]), \
                 patch.object(checkpoint, 'current_candidate') as load:
                with self.assertRaisesRegex(ValueError, 'Not the pinned PCB'):
                    rf_migration.main()
                load.assert_not_called()
            self.assertFalse(output.parent.exists())

    def test_rf_migration_never_overwrites_a_candidate(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'retained.kicad_pcb'
            output.write_text('retained')
            with patch.object(sys, 'argv', ['rf', '--pcb', 'missing', '--output', str(output)]):
                with self.assertRaisesRegex(ValueError, 'Output exists'):
                    rf_migration.main()
            self.assertEqual(output.read_text(), 'retained')

    def test_rf_migration_rejects_changed_source_before_loading_candidate(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'board.copper').write_text('changed source')
            pcb = root / 'prior.kicad_pcb'
            pcb.write_text('pinned fixture')
            output = root / 'new/routed.kicad_pcb'
            digest = rf_migration.sha256(pcb.read_bytes()).hexdigest()
            with patch.object(sys, 'argv', ['rf', '--pcb', str(pcb), '--output', str(output)]), \
                 patch.object(rf_migration, 'ROOT', root), \
                 patch.object(rf_migration, 'PRIOR_PCB_SHA256', digest), \
                 patch.object(checkpoint, 'current_candidate') as load:
                with self.assertRaisesRegex(ValueError, 'Source changed'):
                    rf_migration.main()
                load.assert_not_called()
            self.assertFalse(output.parent.exists())

    def test_usb_migration_refuses_unpinned_input_before_loading_source(self):
        with TemporaryDirectory() as directory:
            pcb = Path(directory) / 'other.kicad_pcb'
            pcb.write_text('unrelated input')
            output = Path(directory) / 'seed.kicad_pcb'
            with patch.object(sys, 'argv', ['seed', '--pcb', str(pcb), '--output', str(output)]), \
                 patch.object(usb_migration, 'posed_source') as load:
                with self.assertRaisesRegex(ValueError, 'Only the pinned'):
                    usb_migration.main()
                load.assert_not_called()
            self.assertFalse(output.exists())

    def test_usb_migration_never_overwrites_an_existing_candidate(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'seed.kicad_pcb'
            output.write_text('retained')
            with patch.object(sys, 'argv', ['seed', '--pcb', 'missing', '--output', str(output)]), \
                 patch.object(usb_migration, 'posed_source') as load:
                with self.assertRaisesRegex(ValueError, 'Output exists'):
                    usb_migration.main()
                load.assert_not_called()
            self.assertEqual(output.read_text(), 'retained')

    def test_native_stub_selection_handles_only_exact_ordinary_duplicate_extent(self):
        a = TrackSegment('A', Point.mm(1, 1), Point.mm(2, 1), 200000, CopperLayer.FRONT)
        b = TrackSegment('A', a.end, a.start, a.width_nm, a.layer)
        other = TrackSegment('A', Point.mm(2, 1), Point.mm(3, 1), 200000, a.layer)
        board = NS(tracks=(a, b, other), vias=(), nets=(NS(name='A'),), net_routing_rules=())
        with TemporaryDirectory() as directory:
            pcb, report = Path(directory) / 'board.kicad_pcb', Path(directory) / 'drc.json'
            pcb.write_text('(kicad_pcb (segment (start 1 1) (end 2 1) (width 0.2) '
                           '(layer "F.Cu") (net "A") (uuid "u1")))')
            report.write_text(json.dumps({'unconnected_items': [], 'violations': [
                {'type': 'track_dangling', 'severity': 'warning', 'items': [{'uuid': 'u1'}]}]}))
            for owner_tracks in ((), (b,)):
                with self.subTest(owned=bool(owner_tracks)), \
                     patch.object(checkpoint, 'posed_source', return_value=NS(tracks=owner_tracks, vias=())), \
                     patch.object(checkpoint, 'distribution_zone_nets', return_value=set()), \
                     patch.object(checkpoint, 'explicit_copper_connectivity',
                                  return_value=NS(net_connected=lambda n: True)), \
                     patch.object(checkpoint, 'replace', side_effect=lambda obj, **kw: NS(**(vars(obj) | kw))), \
                     patch.object(checkpoint, 'prune_track_stubs', return_value=()) as prune:
                    if owner_tracks:
                        with self.assertRaisesRegex(ValueError, 'Not disposable'):
                            checkpoint.prune_native_stubs(board, pcb, report)
                        prune.assert_not_called()
                    else:
                        result = checkpoint.prune_native_stubs(board, pcb, report)
                        self.assertEqual(result.tracks, (other,))
                        self.assertEqual(prune.call_args.args[1], (a, b))

    def test_native_stub_cleanup_rejects_open_board_before_resolving_tracks(self):
        with TemporaryDirectory() as directory:
            report = Path(directory) / 'drc.json'
            report.write_text(json.dumps({'unconnected_items': [{}], 'violations': []}))
            with self.assertRaisesRegex(ValueError, 'incomplete board'):
                checkpoint.prune_native_stubs(None, Path('missing'), report)

    def test_native_stub_cleanup_does_not_waive_other_findings(self):
        with TemporaryDirectory() as directory:
            report = Path(directory) / 'drc.json'
            report.write_text(json.dumps({'unconnected_items': [], 'violations': [
                {'type': 'clearance', 'severity': 'error'}]}))
            with self.assertRaisesRegex(ValueError, 'other native findings'):
                checkpoint.prune_native_stubs(None, Path('missing'), report)

    def test_resume_refuses_to_overwrite_before_loading_input(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'retained.kicad_pcb'
            output.write_text('retained')
            with patch.object(sys, 'argv', ['finish', '--pcb', 'missing.kicad_pcb',
                                           '--output', str(output)]), \
                 patch.object(checkpoint, 'current_candidate') as load:
                with self.assertRaisesRegex(ValueError, 'Output exists'):
                    checkpoint.main()
                load.assert_not_called()
            self.assertEqual(output.read_text(), 'retained')

    def test_physical_pad_selector_preserves_hierarchy(self):
        self.assertEqual(checkpoint.pad_reference('PWR/U_CHARGE.6'),
                         PadReference('PWR/U_CHARGE', '6'))

    def test_physical_pad_selector_requires_both_parts(self):
        for value in ('U1', '.1', 'U1.'):
            with self.subTest(value=value), self.assertRaises(checkpoint.argparse.ArgumentTypeError):
                checkpoint.pad_reference(value)

    def fixture(self, text):
        pads = tuple(NS(number=str(i), position=Point.mm(i, 0),
            rotation_degrees=0, size=NS(width_nm=500000, height_nm=600000),
            kind=PadKind.SMD, shape=PadShape.RECTANGLE, connector_contact=False)
            for i in (1, 2))
        board = NS(placements=(NS(reference='U1', footprint='f',
            position=Point.mm(1, 2), rotation_degrees=0, side=BoardSide.FRONT),),
            footprints={'f': NS(pads=pads)},
            nets=(NS(name='V', pads=(PadReference('U1', '1'), PadReference('U1', '2'))),))
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'candidate.kicad_pcb'
            path.write_text(text)
            with patch.object(checkpoint, 'posed_source', return_value=board), \
                 patch.object(checkpoint, 'placement_rejection_reasons', return_value=()), \
                 patch.object(checkpoint, 'validate_hard_macros'):
                return checkpoint.current_candidate(path)

    text = '''(kicad_pcb (footprint "f" (layer "F.Cu")
        (property "Reference" "U1") (at 1 2)
        (pad "2" smd rect (at 2 0) (size 0.5 0.6) (layers "F.Cu") (net "V"))
        (pad "1" smd rect (at 1 0) (size 0.5 0.6) (layers "F.Cu") (net "V"))))'''

    def test_saved_pad_order_is_not_identity(self):
        self.assertEqual(self.fixture(self.text).placements[0].reference, 'U1')

    def test_stale_native_pose_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Stale native pose'):
            self.fixture(self.text.replace('(at 1 2)', '(at 1.1 2)'))

    def test_changed_land_position_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Changed land position'):
            self.fixture(self.text.replace('(at 2 0)', '(at 2.1 0)'))

    def test_changed_land_angle_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Changed land angle'):
            self.fixture(self.text.replace('(at 2 0)', '(at 2 0 90)'))

    def test_changed_net_rejected(self):
        with self.assertRaises((KeyError, ValueError)):
            self.fixture(self.text.replace('(net "V")', '(net "GND")', 1))

    def test_changed_land_kind_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Changed pad shape/kind'):
            self.fixture(self.text.replace('smd rect', 'thru_hole rect', 1))

    def test_guard_is_not_a_python_assertion(self):
        with self.assertRaisesRegex(ValueError, 'blocked'):
            checkpoint.require(False, 'blocked')
