"""One pinned tracker checkpoint migration; not a generic native-board importer.

Move only J_CELL and replace only CELL_RF tracks using CopperScript's existing
legal surface-path candidates. Preserve the native board and all other copper;
the result requires the matching source change and fresh native refill/DRC.
"""
import argparse
from dataclasses import replace
from hashlib import sha256
import json
from math import hypot
from pathlib import Path
import subprocess
import shutil
import sys

PRIOR_PCB_SHA256 = "70caf673a789d4a6cfb4eaad1cb6247de70ccd1d47bfcc828c2dd438ac74aa31"
PRIOR_SOURCE_SHA256 = "177d718446a3dbadd669289578e6d2307b9ae9e19bd76bb4bbe93b573ac05d5c"
ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def migrate(board):
    from pcbir.local_critical import local_surface_candidates
    from pcbir.physical import Point
    from pcbir.placement import placement_rejection_reasons
    from pcbir.hard_macros import validate_hard_macros
    from pcbir.surface_path import surface_path_between
    from pcbir.routing_clearance import RoutingClearanceIndex
    from pcbir.placement import transformed_pad_position
    from pcbir.physical import CopperLayer
    pose = next(p for p in board.placements if p.reference == "J_CELL")
    require(pose.position == Point.mm(31, 6) and pose.rotation_degrees == 90,
            "Not the pinned earlier connector pose")
    position = Point.mm(6, 8)
    placements = tuple(replace(p, position=position, rotation_degrees=180)
                       if p.reference == "J_CELL" else p for p in board.placements)
    placement_rules = tuple(replace(r, fixed_position=position,
        fixed_rotation_degrees=180, allowed_orientations=(180,))
        if r.reference == "J_CELL" else r for r in board.placement_rules)
    rules = tuple(replace(r, max_length_nm=20000000) if r.net == "CELL_RF" else r
                  for r in board.net_routing_rules)
    proposal = replace(board, placements=placements, placement_rules=placement_rules,
                       net_routing_rules=rules,
                       tracks=tuple(t for t in board.tracks if t.net != "CELL_RF"))
    require(not any(v.net == "CELL_RF" for v in board.vias), "Unexpected RF vias")
    reasons = placement_rejection_reasons(proposal, {p.reference: p for p in placements})
    require(not reasons, f"Illegal connector placement: {reasons}")
    rule = next(r for r in rules if r.net == "CELL_RF")
    candidates = list(local_surface_candidates(proposal, rule))
    if not candidates:
        net = next(n for n in proposal.nets if n.name == "CELL_RF")
        poses = {p.reference: p for p in placements}
        require(len(net.pads) == 2, "Unexpected RF terminal count")
        terminals = [transformed_pad_position(proposal, poses[p.component], p.pad)
                     for p in net.pads]
        path = surface_path_between(proposal, RoutingClearanceIndex(proposal),
            rule.net, *terminals, rule.width_nm or proposal.rules.default_track_width_nm,
            CopperLayer.FRONT, step_nm=100000, maximum_detour_nm=3000000,
            state_budget=60000)
        if path:
            candidates.append(path)
    for tracks in candidates:
        length_nm = sum(hypot(t.end.x_nm-t.start.x_nm, t.end.y_nm-t.start.y_nm) for t in tracks)
        if length_nm <= rule.max_length_nm:
            result = replace(proposal, tracks=(*proposal.tracks, *tracks))
            validate_hard_macros(result)
            return result, tracks, length_nm
    raise ValueError("No legal short surface RF feed; no native output written")


def native_write(args):
    import pcbnew
    require(not args.output.exists(), "Output exists")
    require(sha256(args.pcb.read_bytes()).hexdigest() == PRIOR_PCB_SHA256, "Not the pinned PCB")
    delta = json.loads(args.delta.read_text())
    board = pcbnew.LoadBoard(str(args.pcb.resolve()))
    connector = next(fp for fp in board.GetFootprints() if fp.GetReference() == "J_CELL")
    require(delta["connector_position_nm"] == [6000000, 8000000] and
            delta["connector_rotation_degrees"] == 180, "Unexpected connector delta")
    connector.SetPosition(pcbnew.VECTOR2I(*delta["connector_position_nm"]))
    connector.SetOrientationDegrees(180)
    net = board.FindNet("CELL_RF")
    require(net is not None, "Missing native CELL_RF")
    for track in list(board.GetTracks()):
        if track.GetNetname() == "CELL_RF":
            require(not isinstance(track, pcbnew.PCB_VIA), "Unexpected RF via")
            board.Remove(track)
    for record in delta["tracks"]:
        require(record["layer"] == "F.Cu" and record["net"] == "CELL_RF", "Out-of-scope track")
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(pcbnew.VECTOR2I(*record["start"]))
        track.SetEnd(pcbnew.VECTOR2I(*record["end"]))
        track.SetWidth(record["width_nm"])
        track.SetLayer(pcbnew.F_Cu)
        track.SetNetCode(net.GetNetCode())
        board.Add(track)
    pcbnew.SaveBoard(str(args.output.resolve()), board)
    require(args.output.is_file() and args.output.stat().st_size > 0, "Native save failed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pcb", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--kicad-python")
    parser.add_argument("--native-write", action="store_true")
    parser.add_argument("--delta", type=Path)
    args = parser.parse_args()
    if args.native_write:
        native_write(args)
        return
    require(not args.output.exists(), "Output exists")
    require(sha256(args.pcb.read_bytes()).hexdigest() == PRIOR_PCB_SHA256, "Not the pinned PCB")
    require(sha256((ROOT / "board.copper").read_bytes()).hexdigest() == PRIOR_SOURCE_SHA256,
            "Source changed; this is only the pinned earlier checkpoint migration")
    require(args.kicad_python is not None, "Explicit KiCad Python required")
    delta = args.output.with_suffix(".rf-delta.json")
    targets = (delta, args.output.with_suffix(".kicad_pro"),
               args.output.parent / "fp-lib-table", args.output.parent / "CopperScript.pretty")
    require(not any(p.exists() for p in targets), "Output envelope exists")
    from finish_routed_candidate import current_candidate
    board = current_candidate(args.pcb)
    result, tracks, length_nm = migrate(board)
    require(tuple(t for t in result.tracks if t.net != "CELL_RF") ==
            tuple(t for t in board.tracks if t.net != "CELL_RF") and result.vias == board.vias,
            "Migration changed out-of-scope copper")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    document = {"schema": "copper-asset-tracker-cellular-feed-migration/v1",
        "qualified_release": False, "native_refill_drc_required": True,
        "source_contract_update_required": True,
        "input_pcb_sha256": PRIOR_PCB_SHA256, "input_source_sha256": PRIOR_SOURCE_SHA256,
        "connector_position_nm": [6000000, 8000000], "connector_rotation_degrees": 180,
        "maximum_feed_length_nm": 20000000, "proposed_track_length_nm": round(length_nm),
        "tracks": [{"net": t.net, "layer": t.layer.value,
                    "start": [t.start.x_nm,t.start.y_nm], "end": [t.end.x_nm,t.end.y_nm],
                    "width_nm": t.width_nm} for t in tracks]}
    delta.write_text(json.dumps(document, indent=2)+"\n", encoding="utf-8")
    # Native DRC must see the same project and embedded footprint libraries;
    # missing-library warnings must not be hidden by disabling checks.
    shutil.copy2(args.pcb.with_suffix(".kicad_pro"), args.output.with_suffix(".kicad_pro"))
    shutil.copy2(args.pcb.parent / "fp-lib-table", args.output.parent / "fp-lib-table")
    shutil.copytree(args.pcb.parent / "CopperScript.pretty", args.output.parent / "CopperScript.pretty")
    subprocess.run([args.kicad_python, str(Path(__file__).resolve()), "--native-write",
                    "--pcb", str(args.pcb.resolve()), "--output", str(args.output.resolve()),
                    "--delta", str(delta.resolve())], check=True)
    print(json.dumps(document), flush=True)


if __name__ == "__main__":
    main()
