"""Reroute a legal pose seed using CopperScript; never import its ordinary copper.

This project workflow preserves a reviewed placement for a controlled routing
comparison. Algorithms and all electrical/physical checks remain in CopperScript.
The result is a review candidate, not manufacturing or assembly authorization.
Run independent native refill/DRC afterwards, then current qualification gates.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from pcbir.backends.kicad_pcb import KiCadPcbBackend
from pcbir.backends.kicad_project import write_kicad_project
from pcbir.detailed import DetailedRouterOptions
from pcbir.drc import run_physical_drc
from pcbir.fanout import FanoutOptions
from pcbir.flow import run_routing_pipeline
from pcbir.hard_macros import macro_source
from pcbir.package_access import PackageAccessOptions
from pcbir.pad_stitch import stitch_duplicate_pads
from pcbir.physical import nm_from_mm
from pcbir.placement import PlacementPlannerOptions, placement_rejection_reasons
from pcbir.plane import PlaneStitchOptions, stitch_zone_pads
from pcbir.progress import console_progress
from pcbir.routeflow import PlacementRoutingFeedbackOptions
from pcbir.zone_geometry import distribution_zone_nets

from probe_open_routes import ROOT, posed_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pose-seed", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="new directory, never overwritten")
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("review output already exists; choose a new directory")
    source = macro_source(posed_source(args.pose_seed))
    options = PlacementPlannerOptions(candidate_count=1, analytical_iterations=0,
        refinement_passes=0, escape_spacing_passes=0,
        fixed_references=frozenset(p.reference for p in source.placements))
    reasons = placement_rejection_reasons(source, {p.reference: p for p in source.placements}, options)
    if reasons:
        raise ValueError(f"illegal seed placement: {reasons}")
    args.output.mkdir(parents=True, exist_ok=False)
    result = run_routing_pipeline(source, placement_options=options,
        feedback_options=PlacementRoutingFeedbackOptions(maximum_iterations=1),
        detailed_options=DetailedRouterOptions(pitch_nm=nm_from_mm("0.5"),
            maximum_passes=2, maximum_search_states=30000, repair_budget_multiplier=2,
            enable_soft_ripup=True, constrained_pins_first=True,
            progressive_guides=True, defer_zone_nets=True),
        fanout_options=FanoutOptions(maze_escapes=True),
        package_access_options=PackageAccessOptions(maximum_trials=0,
            maximum_pattern_trials=2, reserve_plane_contacts=False),
        on_progress=console_progress())
    # Persist the area result before the separate prospective-plane search.
    (args.output / "area-route.json").write_text(result.detailed.to_json())
    (args.output / "critical-route.json").write_text(result.critical.to_json())
    write_kicad_project(KiCadPcbBackend().generate(result.board), args.output / "area-routed.kicad_pcb")
    print("PROSPECTIVE_PLANE_CONTACTS started", flush=True)
    plane = stitch_zone_pads(result.board, PlaneStitchOptions(step_nm=nm_from_mm("0.1"),
        maximum_contact_radius_nm=nm_from_mm(3), maximum_detour_nm=nm_from_mm("1.5"),
        maze_step_nm=nm_from_mm("0.05"), maze_state_budget=5000))
    board = stitch_duplicate_pads(plane.board).board
    drc = run_physical_drc(board)
    write_kicad_project(KiCadPcbBackend().generate(board), args.output / "routed.kicad_pcb")
    document = {"schema": "copper-asset-tracker-routing-review/v1", "production_ready": False,
        "native_verification_required": True,
        "source_sha256": sha256((ROOT / "board.copper").read_bytes()).hexdigest(),
        "pose_seed_sha256": sha256(args.pose_seed.read_bytes()).hexdigest(),
        "pipeline_status": result.status.value, "physical_drc": json.loads(drc.to_json()),
        "failed_critical_nets": sorted(result.package_access.failed_critical_nets),
        "ordinary_failed_nets": [n.net for n in result.detailed.nets if not n.connected
                                 and n.net not in distribution_zone_nets(result.board)],
        "deferred_zone_nets": [n.net for n in result.detailed.nets if not n.connected
                               and n.net in distribution_zone_nets(result.board)],
        "bypass_pending": [{"capacitor": p.component, "reason": reason}
                           for p, reason in result.fanout.decoupling_pending],
        "plane_pending": [f"{p.component}.{p.pad}" for p in plane.pending_pads]}
    (args.output / "route-review.json").write_text(json.dumps(document, indent=2, sort_keys=True)+"\n")
    print(json.dumps({k: document[k] for k in ("pipeline_status", "failed_critical_nets",
        "ordinary_failed_nets", "bypass_pending", "plane_pending")}), flush=True)
    return 0 if not document["ordinary_failed_nets"] and not document["failed_critical_nets"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
