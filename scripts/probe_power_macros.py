"""Isolated geometry probes using the tracker's exact locked footprint set.

This intentionally cuts away host circuitry for geometry tests, not ERC signoff.
It never replaces the full board or produces a production release.
"""
import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from pcbir.backends.kicad_pcb import KiCadPcbBackend
from pcbir.backends.kicad_project import write_kicad_project
from pcbir.clusters import cluster_placements
from pcbir.drc import PhysicalDrcPolicy, run_physical_drc
from pcbir.footprints import FootprintResolver
from pcbir.hard_macros import bind_hard_macro, materialize_hard_macros
from pcbir.loader import load_design
from pcbir.macro_bindings import PreparedMacroBinding, prepare_macro_bindings
from pcbir.packages import resolve_module_asset
from pcbir.physical import CopperLayer, PadReference, PhysicalBoard, PhysicalNet, Point, TrackSegment, Via
from pcbir.placement import transformed_local_point
from pcbir.physicalize import PrototypePhysicalOptions, resolved_physicalize

ROOT = Path(__file__).resolve().parents[1]


def isolated_probe(physical, scene_path, rotation=0, *, port_consumers=True):
    if isinstance(scene_path, PreparedMacroBinding):
        prepared = scene_path
        binding = prepared.binding
        scene = {"name": binding.name,
                 "bindings": {m.key: m.target for m in binding.mappings if m.kind == "member"},
                 "net_bindings": {m.key: m.target for m in binding.mappings if m.kind == "net"}}
        asset, digest = prepared.path, prepared.digest
    else:
        # Retained historical tests/candidates may still select a legacy scene.
        scene = json.loads(scene_path.read_text())
        asset = resolve_module_asset(scene_path, scene["asset"], locked=True, offline=True)
        digest = scene["asset_sha256"]
    references = set(scene["bindings"].values())
    # Preserve every physical contact and net membership within the selected
    # circuit; shared rails are truncated only in this explicitly isolated probe.
    nets = tuple(PhysicalNet(n.name, tuple(p for p in n.pads if p.component in references))
                 for n in physical.nets if any(p.component in references for p in n.pads))
    board = PhysicalBoard(name=scene["name"], outline=physical.outline,
        footprints=physical.footprints, placements=tuple(p for p in physical.placements if p.reference in references),
        nets=nets, stackup=physical.stackup, rules=physical.rules,
        zones=tuple(z for z in physical.zones if z.id == "ground-return-plane"),
        metadata={"prototype_placement": "false", "fabrication_ready": "false"})
    board = bind_hard_macro(board, asset, expected_sha256=digest,
        name=scene["name"], bindings=scene["bindings"], net_bindings=scene["net_bindings"])
    cluster = board.rigid_clusters[0]
    poses = {p.reference: p for p in board.placements}
    anchor = replace(poses[cluster.anchor.reference], position=Point.mm(50, 40), rotation_degrees=rotation)
    poses.update(cluster_placements(board, cluster, anchor))
    from pcbir.placement import placement_rejection_reasons
    reasons = placement_rejection_reasons(board, poses)
    if reasons:
        print("Probe placement rejected:", reasons, flush=True)
    board = materialize_hard_macros(replace(board, placements=tuple(poses.values())))
    if not port_consumers:
        return board
    # Terminated host-side fixture loads exercise every declared F.Cu port.
    # They are geometry-only resistors, not additional production components.
    resistor = poses[scene["bindings"]["R_BOT"]]
    tracks, vias, loads = [], [], []
    extra_pads = {}
    for port in board.hard_macros[0].ports:
        direction = -1 if port.name == "VOUT" else 1
        x, y = port.position.x_nm / 1e6, port.position.y_nm / 1e6
        end_x = x + direction * 5
        signal = transformed_local_point(anchor, Point.mm(end_x, y))
        ground = transformed_local_point(anchor, Point.mm(end_x + direction * 1.02, y))
        ground_via = transformed_local_point(anchor, Point.mm(end_x + direction * 1.02, y + 1.25))
        ref = "PROBE_" + port.name
        loads.append(replace(resistor, reference=ref,
            position=transformed_local_point(anchor, Point.mm(end_x + direction * .51, y)),
            rotation_degrees=rotation + (180 if direction < 0 else 0)))
        extra_pads.setdefault(port.net, []).append(PadReference(ref, "1"))
        extra_pads.setdefault("GND", []).append(PadReference(ref, "2"))
        tracks.extend((TrackSegment(port.net, transformed_local_point(anchor, port.position), signal, 200000, CopperLayer.FRONT),
                       TrackSegment("GND", ground, ground_via, 200000, CopperLayer.FRONT)))
        vias.append(Via("GND", ground_via, 600000, 300000))
    return replace(board, placements=(*board.placements, *loads),
        nets=tuple(replace(n, pads=(*n.pads, *extra_pads.get(n.name, ()))) for n in board.nets),
        tracks=(*board.tracks, *tracks), vias=(*board.vias, *vias))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rotation", type=int, choices=(0, 90, 180, 270), default=0)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "build/power-probes")
    parser.add_argument("--kicad-cli", default="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe")
    args = parser.parse_args()
    design = load_design(ROOT / "board.copper", locked=True, offline=True)
    physical = resolved_physicalize(design, FootprintResolver(base_directory=ROOT, locked=True, offline=True),
        PrototypePhysicalOptions(copper_layers=6, fabrication_profile="jlcpcb-six-layer"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    selections = {p.binding.name: p for p in prepare_macro_bindings(design, locked=True, offline=True)}
    for name in ("logic-buck-boost", "modem-buck-boost"):
        board = isolated_probe(physical, selections[name], args.rotation)
        drc = run_physical_drc(board, policy=PhysicalDrcPolicy(False))
        stem = board.name + f"-{args.rotation}"
        (args.output_dir / f"{stem}-physical.json").write_text(drc.to_json())
        pcb = args.output_dir / f"{stem}.kicad_pcb"
        write_kicad_project(KiCadPcbBackend().generate(board), pcb)
        report = args.output_dir / f"{stem}-native.json"
        subprocess.run([args.kicad_cli, "pcb", "drc", "--refill-zones", "--save-board", "--format", "json",
                        "--severity-all", "--exit-code-violations", "-o", str(report), str(pcb)], check=True)
        result = json.loads(report.read_text())
        assert not result["violations"] and not result["unconnected_items"], result
        print(f"{stem}: native geometry clean; not power/thermal qualification; sha256:{sha256(pcb.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
