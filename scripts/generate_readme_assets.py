"""Board-specific showcase snapshots; never routing or production signoff.

Use the compiler's source/native checkpoint guard and authoritative electrical
serializer. Placement illustrations deliberately hide copper, keeping the exact
candidate poses; routing plots use the untouched filled native candidate.
"""
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import subprocess
import argparse

from pcbir.backends.kicad_pcb import KiCadPcbBackend
from pcbir.backends.kicad_project import write_kicad_project
from pcbir.loader import load_design
from pcbir.serializer import board_to_dict
from checkpoint_source import current_candidate

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pcb", type=Path, required=True)
    parser.add_argument("--kicad-cli", required=True)
    args = parser.parse_args()
    pcb = args.pcb.resolve()
    board = current_candidate(pcb)
    output = ROOT / "docs/showcase"
    design = load_design(ROOT / "board.copper", locked=True, offline=True)
    ir = board_to_dict(design)
    write_json(output / "electrical-ir.excerpt.json", {
        "schema": ir["schema"], "kind": ir["kind"], "name": ir["name"],
        "components": [c for c in ir["components"] if c["ref"] in {"U_MODEM", "C_MCU"}],
        "nets": [n for n in ir["nets"] if n["name"] == "V3V8"],
    })
    write_json(output / "physical-ir.excerpt.json", {
        "note": "Selected fields of native-source-checked physical IR; not a complete serialization.",
        "units": "nanometres; rotations in degrees",
        "placements": [{**asdict(p), "rotation_degrees": str(p.rotation_degrees)}
                       for p in board.placements if p.reference in {"U_MODEM", "C_MCU"}],
        "tracks": [asdict(t) for t in board.tracks if t.net == "V3V8"][:2],
    })
    manifest = json.loads((pcb.parent / "manifest.json").read_text())
    drc = json.loads((pcb.parent / "drc.json").read_text())
    if manifest["exported_pcb_sha256"] != hashlib.sha256(pcb.read_bytes()).hexdigest():
        raise ValueError("The export manifest does not describe this PCB")
    write_json(output / "snapshot.json", {
        "pcb": str(pcb.relative_to(ROOT)).replace("\\", "/"),
        "pcb_sha256": hashlib.sha256(pcb.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256((ROOT / "board.copper").read_bytes()).hexdigest(),
        "component_count": len(board.placements), "net_count": len(board.nets),
        "track_count": len(board.tracks), "via_count": len(board.vias),
        "copper_layers": manifest["copper_layers"],
        "native_drc_violation_count": len(drc["violations"]),
        "native_unconnected_item_count": len(drc["unconnected_items"]),
        "qualified_release": manifest["qualified_release"],
        "placement_view": "Same candidate poses and pads, with tracks/vias/zones hidden for illustration.",
        "routing_views": "Native KiCad exports of the unchanged filled review candidate; unmirrored top view.",
    })
    # The authoritative routed board is never modified. This display-only copy
    # is not a manufacturing artifact or a new independently planned placement.
    placement = replace(board, tracks=(), vias=(), zones=(), zone_fills=(),
                        polygons=(), hard_macros=(), materialized_macros=())
    display_pcb = ROOT / "build/readme-showcase/placement.kicad_pcb"
    write_kicad_project(KiCadPcbBackend().generate(placement), display_pcb)
    plots = (
        (display_pcb, "F.Cu,F.CrtYd,Edge.Cuts", "placement.svg"),
        (pcb, "F.Cu,F.SilkS,Edge.Cuts", "routing-top.svg"),
        (pcb, "In2.Cu,Edge.Cuts", "routing-inner.svg"),
        (pcb, "B.Cu,Edge.Cuts", "routing-bottom.svg"),
    )
    for source, layers, name in plots:
        subprocess.run([args.kicad_cli, "pcb", "export", "svg", "--layers", layers,
                        "--mode-single", "--fit-page-to-board", "--exclude-drawing-sheet",
                        "--output", str(output / name), str(source)], check=True)
        # KiCad emits trailing spaces; normalize text without changing geometry.
        plot = output / name
        plot.write_text("\n".join(line.rstrip() for line in
                                   plot.read_text(encoding="utf-8").splitlines()) + "\n",
                        encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
