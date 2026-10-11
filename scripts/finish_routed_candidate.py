"""Finish a current-source native routing candidate; never hardware signoff.

Consumes an existing routed candidate, not arbitrary historical copper. Fixed
source poses and every native pad's connectivity/geometry must match current
locked intent. Immutable macro copper, widths and all critical limits remain
validated by CopperScript. Native refill/DRC is mandatory after export.
"""
import argparse
from collections import Counter
from dataclasses import replace
import json
from pathlib import Path

from pcbir.backends.kicad_pcb import KiCadPcbBackend, kicad_reference
from pcbir.backends.kicad_project import write_kicad_project
from pcbir.drc import PhysicalDrcPolicy, run_physical_drc, explicit_copper_connectivity
from pcbir.hard_macros import macro_source, validate_hard_macros
from pcbir.importers.kicad_mod import _children, _first, _parse_sexpr
from pcbir.physical import BoardSide, CopperLayer, PadKind, PadReference, Point, RouteKind, nm_from_mm
from pcbir.placement import placement_rejection_reasons
from pcbir.plane import PlaneStitchOptions, stitch_zone_pads
from pcbir.routing import route_global
from pcbir.detailed import DetailedRouterOptions, route_detailed
from pcbir.fanout import FanoutOptions, route_fanout
from pcbir.progress import console_progress
from pcbir.route_cleanup import EscapeChain, prune_track_stubs, release_unused_escapes
from pcbir.pad_via_arrays import require_via_in_pad_arrays
from pcbir.zone_geometry import distribution_zone_nets

from probe_open_routes import ROOT, posed_source


def require(condition, message):
    if not condition:
        raise ValueError(str(message))


def pad_reference(value):
    """Parse an explicit physical pad selector, including hierarchical refs."""
    parts = value.rsplit('.', 1)
    if len(parts) != 2 or not all(parts):
        raise argparse.ArgumentTypeError('expected physical COMPONENT.PAD')
    return PadReference(*parts)


def current_candidate(path, **source_options):
    """Reject changed native poses/lands rather than moving existing tracks."""
    board = posed_source(path, with_copper=True, **source_options)
    poses = {kicad_reference(p.reference): p for p in board.placements}
    tree = _parse_sexpr(path.read_text(), str(path))
    native_nets = {n[1]: n[2] for n in _children(tree, "net")}
    native_nets.update({n.name: n.name for n in board.nets})
    expected_nets = {p: n.name for n in board.nets for p in n.pads}
    seen = set()
    for fp in _children(tree, "footprint"):
        ref = next(p[2] for p in _children(fp, "property") if p[1] == "Reference")
        require(ref not in seen and ref in poses, f"Unexpected native reference {ref}")
        seen.add(ref)
        pose = poses[ref]
        require(pose.side is BoardSide.FRONT and _first(fp, 'layer')[1] == 'F.Cu',
                'This application checkpoint currently supports front-mounted parts only')
        at = _first(fp, "at")
        require(Point.mm(*at[1:3]) == pose.position, f"Stale native pose: {ref}")
        require((float(at[3]) if len(at) > 3 else 0) % 360 == float(pose.rotation_degrees), ref)
        footprint = board.footprints[pose.footprint]
        native_pads = _children(fp, "pad")
        require(len(native_pads) == len(footprint.pads), f"Changed lands: {ref}")
        # Saving in KiCad sorts pads; ordering is not land identity.
        native_pads.sort(key=lambda p: (p[1], Point.mm(*_first(p, 'at')[1:3]).x_nm,
                                       Point.mm(*_first(p, 'at')[1:3]).y_nm))
        source_pads = sorted(footprint.pads, key=lambda p: (p.number, p.position.x_nm, p.position.y_nm))
        for native, pad in zip(native_pads, source_pads):
            require(native[1] == pad.number, f"Changed pad mapping: {ref}")
            kind = ('connect' if pad.connector_contact else 'smd') if pad.kind is PadKind.SMD else {
                PadKind.APERTURE: 'smd', PadKind.THROUGH_HOLE: 'thru_hole',
                PadKind.NON_PLATED_THROUGH_HOLE: 'np_thru_hole'}[pad.kind]
            require(native[2] == kind and native[3] == ('rect' if pad.shape.value == 'rectangle'
                                                      else pad.shape.value), f'Changed pad shape/kind: {ref}')
            if pad.kind is PadKind.SMD:
                require(_first(native, 'drill') is None and 'F.Cu' in _first(native, 'layers')[1:],
                        f'Changed copper/drill: {ref}')
            at = _first(native, "at")
            require(Point.mm(*at[1:3]) == pad.position, f"Changed land position: {ref}.{pad.number}")
            require((float(at[3]) if len(at) > 3 else 0) % 360 == float(
                (pad.rotation_degrees + pose.rotation_degrees) % 360), f"Changed land angle: {ref}.{pad.number}")
            size = _first(native, "size")
            require((nm_from_mm(size[1]), nm_from_mm(size[2])) == (pad.size.width_nm, pad.size.height_nm), ref)
            net = _first(native, "net")
            require((native_nets[net[1]] if net else None) == expected_nets.get(PadReference(pose.reference, pad.number)), ref)
    require(seen == set(poses), "Missing native components")
    require(not placement_rejection_reasons(board, {p.reference: p for p in board.placements}), "Illegal placement")
    validate_hard_macros(board)
    return board


def prune_native_stubs(board, pcb, report_path, **source_options):
    """Resolve native warning UUIDs; CopperScript owns pruning/connectivity."""
    report = json.loads(report_path.read_text())
    require(not report['unconnected_items'], 'Do not prune an incomplete board')
    require(all(v['type'] in {'track_dangling', 'via_dangling'} and v['severity'] == 'warning'
                for v in report['violations']), 'Resolve other native findings first')
    uuids = {i['uuid'] for v in report['violations'] for i in v['items']}
    tree = _parse_sexpr(pcb.read_text(), str(pcb))
    native = [t for t in _children(tree, 'segment') if _first(t, 'uuid')[1] in uuids]
    native_vias = [v for v in _children(tree, 'via') if _first(v, 'uuid')[1] in uuids]
    require(uuids and len(native) + len(native_vias) == len(uuids),
            'Report does not identify current copper')
    native_nets = {n[1]: n[2] for n in _children(tree, 'net')}
    native_nets.update({n.name: n.name for n in board.nets})
    owner = posed_source(pcb, **source_options)
    rules = {r.net: r for r in board.net_routing_rules}
    targets = []
    for item in native:
        net = native_nets[_first(item, 'net')[1]]
        require(net not in distribution_zone_nets(board), 'Do not prune filled-plane contacts')
        require(net not in rules or rules[net].kind is RouteKind.GENERAL,
                'Do not prune critical copper')
        a, b = Point.mm(*_first(item, 'start')[1:3]), Point.mm(*_first(item, 'end')[1:3])
        found = [t for t in board.tracks if t.net == net and {t.start, t.end} == {a, b}
                 and t.layer.value == _first(item, 'layer')[1]
                 and t.width_nm == nm_from_mm(_first(item, 'width')[1])]
        # Native exporters may contain reversed duplicate runs. Treat only
        # the exact same swept extent/width/layer/net as one reported target;
        # every occurrence must be ordinary, never owner copper. The generic
        # pruner and terminal-connectivity check still decide what can go.
        require(found and all(t not in owner.tracks for t in found),
                'Not disposable ordinary copper')
        targets.extend(t for t in found if t not in targets)
    via_targets = []
    for item in native_vias:
        net = native_nets[_first(item, 'net')[1]]
        require(net not in distribution_zone_nets(board), 'Do not prune filled-plane contacts')
        require(net not in rules or rules[net].kind is RouteKind.GENERAL,
                'Do not prune critical copper')
        layers = _first(item, 'layers')[1:]
        found = [v for v in board.vias if v.net == net
                 and v.position == Point.mm(*_first(item, 'at')[1:3])
                 and v.size_nm == nm_from_mm(_first(item, 'size')[1])
                 and v.drill_nm == nm_from_mm(_first(item, 'drill')[1])
                 and [v.from_layer.value, v.to_layer.value] == layers]
        require(len(found) == 1 and found[0] not in owner.vias, 'Not disposable ordinary via')
        via_targets.extend(found)
    names = frozenset(t.net for t in (*targets, *via_targets))
    nets = [n for n in board.nets if n.name in names]
    require(all(explicit_copper_connectivity(board, only_nets=names).net_connected(n)
                for n in nets), 'Actual input net is not connected')
    context = replace(board, tracks=tuple(t for t in board.tracks if t not in targets))
    retained = prune_track_stubs(context, tuple(targets), trim_overhangs=True)
    candidate = replace(context, tracks=(*context.tracks, *retained))
    if via_targets:
        tracks, vias = release_unused_escapes(candidate, candidate.tracks, candidate.vias,
            tuple(EscapeChain(v.net, (), (), v) for v in via_targets), Counter(),
            mutable_tracks=Counter(), removable_vias=Counter(via_targets))
        candidate = replace(candidate, tracks=tracks, vias=vias)
        require_via_in_pad_arrays(candidate, 'native stub cleanup')
    require(all(explicit_copper_connectivity(candidate, only_nets=names).net_connected(n)
                for n in nets), 'Pruning changed terminal connectivity')
    # Native UUIDs identify these ordinary objects; the shared transaction
    # proves whether any conservative overlapping-stub remnants are redundant.
    remaining_tracks = tuple((Counter(targets) & Counter(candidate.tracks)).elements())
    remaining_vias = tuple((Counter(via_targets) & Counter(candidate.vias)).elements())
    if remaining_tracks or remaining_vias:
        # This review-only transaction requires the newer compiler; keep the
        # existing locked loader usable when no such repair is requested.
        from pcbir.route_cleanup import remove_redundant_ordinary_copper
        proven = remove_redundant_ordinary_copper(candidate, remaining_tracks, remaining_vias,
            mutable_tracks=Counter(candidate.tracks) - Counter(owner.tracks),
            mutable_vias=Counter(candidate.vias) - Counter(owner.vias))
        if proven is not None:
            candidate = proven
    return candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pcb", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--unlocked-review", action="store_true", help="explicit local revision, never locked release evidence")
    parser.add_argument("--output", type=Path, default=ROOT / "build/finished-routed.kicad_pcb")
    parser.add_argument("--route-v5", action="store_true")
    parser.add_argument("--net", action="append", default=[],
                        help="bounded ordinary-net repair; keep partial results for review")
    parser.add_argument("--ripup-net", action="append", default=[],
                        help="evict an explicitly selected ordinary repair net before stitching; input retained")
    parser.add_argument("--plane-pad", action="append", type=pad_reference, default=[],
                        help="explicit current-source pad needing a prospective plane contact")
    parser.add_argument("--stitch-planes", action="store_true",
                        help="check prospective plane contacts for all source pads")
    parser.add_argument("--plane-radius-mm", default='3')
    parser.add_argument("--plane-detour-mm", default='1.5')
    parser.add_argument("--plane-search-states", type=int, default=50000)
    parser.add_argument("--plane-step-mm", default='0.025')
    parser.add_argument("--refanout", action="store_true",
                        help="rebuild legal escapes for selected ordinary repair nets")
    parser.add_argument("--search-states", type=int, default=300000)
    parser.add_argument("--pitch-mm", default='0.5')
    parser.add_argument("--native-report", type=Path,
                        help="Current input's native DRC; remove only its exact non-macro dangling track")
    parser.add_argument("--prune-native-stubs", type=Path,
                        help="native-clean input's warning report; conservatively prune exact ordinary stubs")
    args = parser.parse_args()
    require(not args.output.exists(), 'Output exists; choose a new review candidate')
    require(not (args.stitch_planes and args.plane_pad),
            'Choose all plane pads or explicit selectors, not both')
    source_options = dict(project_root=args.project_root, locked=not args.unlocked_review)
    board = current_candidate(args.pcb, **source_options)
    if args.ripup_net:
        from pcbir.route_cleanup import ripup_mutable_nets
        require(set(args.ripup_net) <= set(args.net), 'Every evicted net must be rerouted')
        owner = posed_source(args.pcb, **source_options)
        board = ripup_mutable_nets(board, frozenset(args.ripup_net),
            mutable_tracks=Counter(board.tracks) - Counter(owner.tracks),
            mutable_vias=Counter(board.vias) - Counter(owner.vias))
    contacts = None
    if args.plane_pad or args.stitch_planes:
        known = {p for n in board.nets for p in n.pads}
        require(set(args.plane_pad) <= known, 'Unknown physical plane pad')
        contacts = stitch_zone_pads(board, PlaneStitchOptions(
            step_nm=nm_from_mm('.1'), maze_step_nm=nm_from_mm(args.plane_step_mm),
            maze_state_budget=args.plane_search_states,
            maximum_radius_nm=nm_from_mm(args.plane_radius_mm),
            maximum_contact_radius_nm=nm_from_mm(args.plane_radius_mm),
            maximum_detour_nm=nm_from_mm(args.plane_detour_mm),
            only_pads=None if args.stitch_planes else frozenset(args.plane_pad)))
        board = contacts.board
        print('PLANE_PENDING', contacts.pending_pads, flush=True)
    repair = None
    if args.net:
        fanout = (route_fanout(board, FanoutOptions(maze_escapes=True),
                              only_nets=frozenset(args.net)) if args.refanout else None)
        if fanout is not None:
            board = fanout.board
            print('FANOUT_PENDING', fanout.pending_pads, flush=True)
        guides = route_global(macro_source(posed_source(args.pcb, **source_options)))
        repair = route_detailed(board, guides, DetailedRouterOptions(
            pitch_nm=nm_from_mm(args.pitch_mm), maximum_passes=1,
            maximum_search_states=args.search_states,
            layer_preference_cost=0, direction_preference_cost=0,
            constrained_pins_first=True, route_smoothing=True),
            only_nets=frozenset(args.net), on_progress=console_progress(),
            fanout_accesses=fanout.routing_accesses if fanout else None,
            fanout_created_tracks=fanout.created_tracks if fanout else None,
            fanout_created_vias=frozenset((v.net, v.position) for v in fanout.created_vias)
                                if fanout else None)
        board = repair.board
    if args.route_v5:
        contacts = stitch_zone_pads(board, PlaneStitchOptions(
            step_nm=nm_from_mm('.1'), maze_step_nm=nm_from_mm('.025'),
            maze_state_budget=50000, maximum_contact_radius_nm=nm_from_mm(3),
            maximum_detour_nm=nm_from_mm('1.5'), only_pads=frozenset((
                PadReference('U_CC', '12'), PadReference('U_MODEM_LEVEL', '10')))))
        require(not contacts.pending_pads, contacts.pending_pads)
        guides = route_global(macro_source(posed_source(args.pcb, **source_options)))
        routed = route_detailed(contacts.board, guides, DetailedRouterOptions(
            pitch_nm=nm_from_mm('.5'), maximum_passes=1, maximum_search_states=300000,
            layer_preference_cost=0, direction_preference_cost=0,
            constrained_pins_first=True, route_smoothing=True), only_nets=frozenset({'V5'}))
        require(any(n.net == 'V5' and n.connected for n in routed.nets), routed.nets)
        board = routed.board
    if args.native_report:
        report = json.loads(args.native_report.read_text())
        require(not report['unconnected_items'], 'Do not prune an incomplete board')
        uuids = {i['uuid'] for f in report['violations'] if f['type'] == 'track_dangling' for i in f['items']}
        tree = _parse_sexpr(args.pcb.read_text(), str(args.pcb))
        targets = [t for t in _children(tree, 'segment') if _first(t, 'uuid')[1] in uuids]
        require(len(targets) == len(uuids), 'Native report does not match this board')
        owner = posed_source(args.pcb, **source_options)
        removed = []
        for target in targets:
            a, b = Point.mm(*_first(target, 'start')[1:3]), Point.mm(*_first(target, 'end')[1:3])
            tracks = [t for t in board.tracks if t.net == 'PWR/VSYS' and t.layer == CopperLayer.FRONT
                      and {t.start, t.end} == {a, b} and t.width_nm == nm_from_mm(_first(target, 'width')[1])]
            require(len(tracks) == 1 and tracks[0] not in owner.tracks, 'Not a disposable VSYS stub')
            require((a.x_nm-b.x_nm)**2 + (a.y_nm-b.y_nm)**2 <= nm_from_mm('.2')**2,
                    'Only the short native-reported overhang may be pruned')
            removed.extend(tracks)
        board = replace(board, tracks=tuple(t for t in board.tracks if t not in removed))
        print(f'Removed {len(removed)} native-reported ordinary stubs; input retained.')
    if args.prune_native_stubs:
        require(not (args.native_report or args.net or args.route_v5 or contacts is not None),
                'Native stub cleanup must be a separate current-input stage')
        board = prune_native_stubs(board, args.pcb, args.prune_native_stubs, **source_options)
        print('Native-identified ordinary stub pruning checked; input retained.', flush=True)
    validate_hard_macros(board)
    drc = run_physical_drc(board, policy=PhysicalDrcPolicy(False))
    errors = [f for f in drc.findings if f.severity.value == 'error'
              and f.code not in ('DRC-OPEN-NET', 'DRC-ROUTE-INCOMPLETE')]
    require(not errors, errors)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix('.geometry.json').write_text(drc.to_json())
    if contacts is not None:
        args.output.with_suffix('.contacts.json').write_text(json.dumps({
            'scope': 'prospective_plane_contacts_only', 'production_ready': False,
            'native_verification_required': True,
            'pending': [f'{p.component}.{p.pad}' for p in contacts.pending_pads],
            'created_tracks': contacts.added_track_count,
            'created_vias': contacts.added_via_count}, indent=2)+'\n')
    if repair is not None:
        args.output.with_suffix('.routing.json').write_text(repair.to_json())
    write_kicad_project(KiCadPcbBackend().generate(board), args.output)
    print('Candidate exported; native refill/DRC and assembly/qualification gates remain mandatory.')
    return int((repair is not None and any(not n.connected for n in repair.nets))
               or (contacts is not None and bool(contacts.pending_pads)))


if __name__ == '__main__':
    raise SystemExit(main())
