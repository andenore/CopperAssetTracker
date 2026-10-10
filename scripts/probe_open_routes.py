"""Application-only diagnostic probes; never a production routing/signoff path.

Rebuilds locked source geometry at a previous draft's poses, retaining exact
macro assets. Optional ordinary copper is read only as diagnostic obstacles.
Empty connected search guides deliberately remove coarse-guide bias; actual
clearance, terminal connectivity and source routing rules remain mandatory.
Historical ordinary copper can become stale when source poses change. The
--with-copper mode is obstacle analysis only, never current-board closure
evidence. Use a complete source reroute and independent native DRC for that.
"""
import argparse
from dataclasses import replace
from decimal import Decimal
import json
from math import hypot
from pathlib import Path

from pcbir.backends.kicad_pcb import KiCadPcbBackend, kicad_reference
from pcbir.backends.kicad_project import write_kicad_project
from pcbir.clusters import cluster_placements
from pcbir.detailed import DetailedRouterOptions, route_detailed
from pcbir.drc import PhysicalDrcPolicy, run_physical_drc
from pcbir.footprints import FootprintResolver
from pcbir.hard_macros import apply_hard_macro_scene, materialize_hard_macros
from pcbir.importers.kicad_mod import _parse_sexpr, _children, _first
from pcbir.loader import load_design
from pcbir.local_critical import local_surface_candidates
from pcbir.physical import CopperLayer, Point, TrackSegment, Via, RouteKind, nm_from_mm
from pcbir.physicalize import PrototypePhysicalOptions, resolved_physicalize
from pcbir.placement import placement_rejection_reasons, transformed_pad_position
from pcbir.routing import GlobalRoutingResult, GlobalRoutingStatus, GlobalRoutingMetrics, GlobalNetRoute

ROOT = Path(__file__).resolve().parents[1]


def posed_source(pcb=ROOT / "build/no-can-routed.kicad_pcb", *, with_copper=False):
    design = load_design(ROOT / "board.copper", locked=True, offline=True)
    board = resolved_physicalize(design,
        FootprintResolver(base_directory=ROOT, locked=True, offline=True),
        PrototypePhysicalOptions(copper_layers=6, fabrication_profile="jlcpcb-six-layer"))
    for scene in ("nrf-antenna-macro.json", "logic-power-macro.json", "modem-power-macro.json"):
        board = apply_hard_macro_scene(board, ROOT / scene, locked=True, offline=True)
    tree = _parse_sexpr(pcb.read_text(), str(pcb))
    manifest_path = pcb.with_suffix(".editor-intent.json")
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        reverse = {v: k for k, v in manifest["native_references"].items()}
    else:
        reverse = {kicad_reference(p.reference): p.reference for p in board.placements}
    poses = {p.reference: p for p in board.placements}
    for fp in _children(tree, "footprint"):
        ref = next(p[2] for p in _children(fp, "property") if p[1] == "Reference")
        ref = reverse[ref]
        at = _first(fp, "at")
        poses[ref] = replace(poses[ref], position=Point.mm(at[1], at[2]),
            rotation_degrees=(Decimal(at[3]) + 360) % 360 if len(at) > 3 else 0)
    # Current fixed source intent wins over historical pose data.
    for rule in board.placement_rules:
        if rule.fixed_position is not None:
            poses[rule.reference] = replace(poses[rule.reference], position=rule.fixed_position,
                rotation_degrees=rule.fixed_rotation_degrees or 0)
    for cluster in board.rigid_clusters:
        poses.update(cluster_placements(board, cluster, poses[cluster.anchor.reference]))
    board = replace(board, placements=tuple(poses.values()))
    reasons = placement_rejection_reasons(board, poses)
    if reasons:
        print("PLACEMENT", json.dumps(reasons), flush=True)
    board = materialize_hard_macros(board)
    if with_copper:
        native_nets = {item[1]: item[2] for item in _children(tree, "net")}
        # KiCad's saved format may use names directly rather than numeric IDs.
        native_nets.update({net.name: net.name for net in board.nets})
        tracks = list(board.tracks)
        vias = list(board.vias)
        for segment in _children(tree, "segment"):
            start, end = _first(segment, "start"), _first(segment, "end")
            track = TrackSegment(native_nets[_first(segment, "net")[1]], Point.mm(*start[1:3]),
                Point.mm(*end[1:3]), nm_from_mm(_first(segment, "width")[1]),
                CopperLayer(_first(segment, "layer")[1]))
            if track not in tracks:
                tracks.append(track)
        for item in _children(tree, "via"):
            at = _first(item, "at")
            layers = _first(item, "layers")
            via = Via(native_nets[_first(item, "net")[1]], Point.mm(*at[1:3]),
                nm_from_mm(_first(item, "size")[1]), nm_from_mm(_first(item, "drill")[1]),
                CopperLayer(layers[1]), CopperLayer(layers[2]))
            if via not in vias:
                vias.append(via)
        board = replace(board, tracks=tuple(tracks), vias=tuple(vias))
    return board


def probe(board, names, pitch=.25, budget=30000):
    rules = {r.net: r for r in board.net_routing_rules}
    for net in board.nets:
        if net.name not in names:
            continue
        terminals = {f"{p.component}.{p.pad}": [q.x_nm/1e6, q.y_nm/1e6]
            for p in net.pads for q in [transformed_pad_position(board,
                next(x for x in board.placements if x.reference == p.component), p.pad)]}
        print("TERMINALS", net.name, json.dumps(terminals), flush=True)
        if net.name in rules:
            for candidate in local_surface_candidates(board, rules[net.name]):
                print("LOCAL", net.name, sum(round(hypot(t.end.x_nm-t.start.x_nm,
                    t.end.y_nm-t.start.y_nm)) for t in candidate)/1e6, flush=True)
    # Diagnostic search owner, not evidence of successful global routing.
    guides = GlobalRoutingResult(GlobalRoutingStatus.SUCCESS,
        tuple(GlobalNetRoute(n, True, (), (), (), 0) for n in sorted(names)), (),
        GlobalRoutingMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0), "diagnostic", "diagnostic")
    search_board = replace(board, net_routing_rules=tuple(
        replace(r, kind=RouteKind.GENERAL) if r.net in names else r for r in board.net_routing_rules))
    result = route_detailed(search_board, guides, DetailedRouterOptions(
        pitch_nm=nm_from_mm(pitch), maximum_passes=1, maximum_search_states=budget,
        layer_preference_cost=0, direction_preference_cost=0, constrained_pins_first=True,
        route_smoothing=True), only_nets=frozenset(names))
    for n in result.nets:
        print("RESULT", n.net, n.connected, n.length_nm/1e6, n.diagnostics, flush=True)
    # Restore authoritative kinds before full physical checking/export.
    restored = replace(result.board, net_routing_rules=board.net_routing_rules)
    return result, restored


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--net", action="append", required=True)
    ap.add_argument("--with-copper", action="store_true")
    ap.add_argument("--pitch", type=float, default=.25)
    ap.add_argument("--budget", type=int, default=30000)
    ap.add_argument("--output", type=Path, default=ROOT / "build/open-probe")
    args = ap.parse_args()
    board = posed_source(with_copper=args.with_copper)
    result, routed = probe(board, set(args.net), args.pitch, args.budget)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".json").write_text(result.to_json())
    report = run_physical_drc(routed, policy=PhysicalDrcPolicy(False))
    args.output.with_suffix(".drc.json").write_text(report.to_json())
    write_kicad_project(KiCadPcbBackend().generate(routed), args.output.with_suffix(".kicad_pcb"))


if __name__ == "__main__":
    main()
