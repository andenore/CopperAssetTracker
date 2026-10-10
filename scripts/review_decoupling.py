"""Export a local bypass review, NOT a complete route or fabrication candidate.

Only historical component poses seed the review; no historical ordinary copper
is imported. Current locked footprints, fixed intent and macro assets win. All
placement/search algorithms remain in CopperScript. A separate full reroute and
native refill/DRC are required before producing new manufacturing evidence.
"""
import argparse
from dataclasses import replace
from hashlib import sha256
import json
from math import hypot
from pathlib import Path

from pcbir import decoupling
from pcbir.backends.kicad_pcb import KiCadPcbBackend
from pcbir.backends.kicad_project import write_kicad_project
from pcbir.drc import PhysicalDrcPolicy, run_physical_drc
from pcbir.hard_macros import macro_source, materialize_hard_macros
from pcbir.physical import CopperLayer, RouteKind
from pcbir.pin_escape import _verified_land_path
from pcbir.placement import PlacementPlannerOptions, placement_rejection_reasons, transformed_pad_position
from pcbir.routing_clearance import RoutingClearanceIndex

from probe_open_routes import ROOT, posed_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pose-seed", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="new review directory; never overwritten")
    parser.add_argument("--movable", action="append", default=[], help="bypass reference to relocate (repeatable)")
    args = parser.parse_args()
    source = macro_source(posed_source(args.pose_seed))
    role_refs = {l.capacitor.component for l in source.decoupling_links}
    movable = set(args.movable) if args.movable else role_refs
    if not movable <= role_refs:
        raise ValueError("--movable must name pin-associated bypass capacitors")
    options = PlacementPlannerOptions(fixed_references=frozenset(
        p.reference for p in source.placements if p.reference not in movable))
    poses, moved = decoupling.improve_decoupling_placement(
        source, {p.reference: p for p in source.placements}, options)
    rejection = placement_rejection_reasons(source, poses, options)
    if rejection:
        raise ValueError(f"illegal review placement: {rejection}")
    result = decoupling.route_decouplers(materialize_hard_macros(replace(source, placements=tuple(poses.values()))))
    index = RoutingClearanceIndex(result.board)
    rules = {r.net: r for r in source.net_routing_rules}
    associations = []
    for link in source.decoupling_links:
        target, cap = poses[link.target.component], poses[link.capacitor.component]
        rule = rules.get(link.net)
        specialized = rule is not None and rule.kind is not RouteKind.GENERAL
        path = None
        if not specialized:
            land = next(p for p in source.footprints[target.footprint].pads if p.number == link.target.pad)
            path = _verified_land_path(result.board, land, target, link.net,
                transformed_pad_position(result.board, cap, link.capacitor.pad), index,
                require_via=False, target_layer=CopperLayer.FRONT,
                required_width_nm=rule.width_nm if rule and rule.width_nm else source.rules.default_track_width_nm)
        associations.append({"capacitor": link.capacitor.component,
            "target": f"{link.target.component}.{link.target.pad}",
            "status": "specialized_router" if specialized else "surface_connected" if path is not None else "pending",
            "surface_path_length_mm": round(sum(hypot(t.end.x_nm-t.start.x_nm, t.end.y_nm-t.start.y_nm)
                for t in path)/1e6, 6) if path is not None else None,
            "local_path_vias": 0 if path is not None else None})
    # Non-contact checks remain useful, but this intentionally unrouted review
    # cannot certify all-board connectivity, filled return planes or RF/power.
    drc = run_physical_drc(result.board, policy=PhysicalDrcPolicy(False))
    args.output.mkdir(parents=True, exist_ok=False)
    write_kicad_project(KiCadPcbBackend().generate(result.board), args.output / "local-bypasses.kicad_pcb")
    document = {"schema": "copper-asset-tracker-local-bypass-review/v1",
        "scope": "local_surface_only", "production_ready": False,
        "source_sha256": sha256((ROOT / "board.copper").read_bytes()).hexdigest(),
        "pose_seed_sha256": sha256(args.pose_seed.read_bytes()).hexdigest(),
        "decoupling_algorithm_sha256": sha256(Path(decoupling.__file__).read_bytes()).hexdigest(),
        "moved_count": moved, "created_surface_tracks": len(result.created_tracks),
        "associations": associations,
        "pending": [{"capacitor": l.capacitor.component, "reason": reason} for l, reason in result.pending],
        "physical_drc": json.loads(drc.to_json())}
    (args.output / "review.json").write_text(json.dumps(document, indent=2, sort_keys=True)+"\n")
    print(json.dumps({k: document[k] for k in ("scope", "moved_count", "created_surface_tracks", "associations", "pending")}), flush=True)
    return 1 if result.pending else 0


if __name__ == "__main__":
    raise SystemExit(main())
