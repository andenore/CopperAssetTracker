"""Current-source modem bypass/native routing checkpoint, never power approval.

Board selectors only: CopperScript owns source/geometry/macro validation and
surface-path algorithms; KiCad owns independent native DRC. All outputs are new.
"""
import argparse
from pathlib import Path
import json
import math
import subprocess

from pcbir.physical import CopperLayer
from pcbir.placement import transformed_pad_position
from pcbir.pin_escape import _verified_land_path
from pcbir.routing_clearance import RoutingClearanceIndex
from pcbir.qualification import hash_file
from checkpoint_source import current_candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pcb', type=Path, required=True)
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--native-cli', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    native_report = args.output.with_suffix('.native-drc.json')
    if args.output.exists() or native_report.exists():
        raise ValueError('preserve prior reports; choose a new output')
    board = current_candidate(args.pcb, project_root=args.project_root, locked=False)
    pcb_hash = hash_file(args.pcb)
    poses = {p.reference: p for p in board.placements}
    index = RoutingClearanceIndex(board)
    feeds = []
    for link in board.decoupling_links:
        if not link.capacitor.component.startswith('U_MODEM/'):
            continue
        target, cap = poses[link.target.component], poses[link.capacitor.component]
        land = next(p for p in board.footprints[target.footprint].pads if p.number == link.target.pad)
        endpoint = transformed_pad_position(board, cap, link.capacitor.pad)
        path = _verified_land_path(board, land, target, link.net, endpoint, index,
            require_via=False, target_layer=CopperLayer.FRONT)
        feeds.append({'capacitor': link.capacitor.component, 'target_pad': link.target.pad,
            'status': 'pass' if path is not None else 'incomplete',
            'via_free_surface_track_chain': path is not None,
            'path_length_nm': round(sum(math.hypot(t.end.x_nm-t.start.x_nm,
                t.end.y_nm-t.start.y_nm) for t in path)) if path is not None else None})
    if len(feeds) != 4:
        raise ValueError('current source must contain the four explicit modem bypass links')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    run = subprocess.run([str(args.native_cli.resolve()), 'pcb', 'drc', '--format', 'json',
        '--severity-all', '-o', str(native_report.resolve()), str(args.pcb.resolve())],
        capture_output=True, text=True)
    if run.returncode or not native_report.exists():
        raise ValueError('native DRC invocation failed: ' + run.stderr + run.stdout)
    if hash_file(args.pcb) != pcb_hash:
        raise ValueError('read-only native checkpoint changed the input')
    native = json.loads(native_report.read_text())
    document = {'schema': 'copperassettracker-modem-power-routing-checkpoint/v0.1',
        'qualified_release': False, 'locked_release_input': False,
        'scope': 'explicit surface bypass chains and independent native connectivity/geometry only',
        'components': len(board.placements), 'copper_layers': len(board.stackup.copper_layers),
        'tracks': len(board.tracks), 'vias': len(board.vias),
        'bypass_feeds': feeds, 'native_unconnected_items': len(native['unconnected_items']),
        'native_violations': len(native['violations']),
        'native_error_count': sum(v['severity'] == 'error' for v in native['violations']),
        'inputs': {'pcb': pcb_hash, 'source': hash_file(args.project_root / 'board.copper'),
            'power_composition': hash_file(args.project_root / 'src/tracker/power_tree.copper'),
            'resolved_lock': hash_file(args.project_root / 'copper.lock'),
            'assembly_lock': hash_file(args.project_root / 'assembly.lock'),
            'modem_macro_scene': hash_file(args.project_root / 'modem-power-macro.json'),
            'native_cli': hash_file(args.native_cli), 'checker': hash_file(Path(__file__)),
            'surface_path_algorithm': hash_file(Path(__import__('pcbir.pin_escape', fromlist=['__file__']).__file__)),
            'local_surface_search_algorithm': hash_file(Path(__import__('pcbir.surface_path', fromlist=['__file__']).__file__)),
            'route_cleanup_algorithm': hash_file(Path(__import__('pcbir.route_cleanup', fromlist=['__file__']).__file__)),
            'source_composition': hash_file(Path(__file__).with_name('checkpoint_source.py')),
            'native_checkpoint_algorithm': hash_file(Path(__import__('pcbir.native_checkpoint', fromlist=['__file__']).__file__)),
            'revision_build': hash_file(args.project_root / 'revision-build.json'),
            'native_report': hash_file(native_report)},
        'unresolved': ['effective local reservoir capacitance and ESR',
            'actual filled load-current path widths/neckdowns, via plating and current sharing',
            'battery/charger envelope, temperature guarantees, harness/mechanics and charging completion',
            'low-battery burst droop, USB detection/startup and converter thermal/stability tests',
            'RF/USB simulation and prototype qualification; new BOM/CPL review and locked release inputs']}
    args.output.write_text(json.dumps(document, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: document[k] for k in ('components', 'bypass_feeds',
        'native_unconnected_items', 'native_violations', 'native_error_count')}), flush=True)
    return int(document['native_error_count'] or document['native_unconnected_items']
        or any(f['status'] != 'pass' for f in feeds))


if __name__ == '__main__':
    raise SystemExit(main())
