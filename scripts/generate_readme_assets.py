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
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pcb", type=Path, required=True)
    parser.add_argument("--kicad-cli", required=True)
    parser.add_argument("--project-root", type=Path, default=ROOT, help="source revision matching the PCB")
    parser.add_argument("--unlocked-review", action="store_true", help="explicit working-copy revision, not a locked release")
    parser.add_argument("--route-report", type=Path, help="shared route report instead of a manufacturing manifest")
    args = parser.parse_args()
    pcb = args.pcb.resolve()
    project = args.project_root.resolve()
    pcb_digest = hashlib.sha256(pcb.read_bytes()).hexdigest()
    board = current_candidate(pcb, project_root=project, locked=not args.unlocked_review)
    output = ROOT / "docs/showcase"
    design = load_design(project / "board.copper", locked=not args.unlocked_review, offline=True)
    ir = board_to_dict(design)
    electrical_excerpt = {
        "schema": ir["schema"], "kind": ir["kind"], "name": ir["name"],
        "components": [c for c in ir["components"] if c["ref"] == "C_MCU"],
        "nets": [n for n in ir["nets"] if n["name"] == "V3V8"],
    }
    physical_excerpt = {
        "note": "Selected fields of native-source-checked physical IR; not a complete serialization.",
        "units": "nanometres; rotations in degrees",
        "placements": [{**asdict(p), "rotation_degrees": str(p.rotation_degrees)}
                       for p in board.placements if p.reference in {"U_MODEM", "U_MODEM/U", "C_MCU"}],
        "tracks": [asdict(t) for t in board.tracks if t.net == "V3V8"][:2],
    }
    drc = json.loads((pcb.parent / "drc.json").read_text())
    if args.route_report:
        route = json.loads(args.route_report.read_text())
        evidence = route["plane_verification"]
        if (not route["routing_complete"] or not evidence["passed"]
                or evidence["filled_board_digest"] != pcb_digest
                or evidence["report_digest"] != hashlib.sha256((pcb.parent / "drc.json").read_bytes()).hexdigest()):
            raise ValueError("Route/native evidence does not describe this filled PCB")
        manifest = {"copper_layers": [layer.value for layer in board.stackup.copper_layers], "qualified_release": False}
    else:
        manifest = json.loads((pcb.parent / "manifest.json").read_text())
        if manifest["exported_pcb_sha256"] != pcb_digest:
            raise ValueError("The export manifest does not describe this PCB")
    if drc["violations"] or drc["unconnected_items"]:
        raise ValueError("Showcase routing requires clean native evidence")
    snapshot = {
        "pcb": str(pcb.relative_to(ROOT)).replace("\\", "/"),
        "pcb_sha256": hashlib.sha256(pcb.read_bytes()).hexdigest(),
        "source": str((project / "board.copper").relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": hashlib.sha256((project / "board.copper").read_bytes()).hexdigest(),
        "canonical_source_sha256": hashlib.sha256((ROOT / "board.copper").read_bytes()).hexdigest(),
        "revision": "modem-power-v1" if args.unlocked_review else "canonical",
        "locked_release_input": not args.unlocked_review,
        "composition_inputs": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
            "board.copper", "revisions/battery-v1/power_tree.copper", "revisions/battery-v1/placement.json",
            "revisions/modem-power-v1/distribution.copper", "revisions/modem-power-v1/placement.json",
            "revisions/modem-power-v1/modem-power-macro.json", "scripts/build_battery_revision.py")},
        "native_report_sha256": hashlib.sha256((pcb.parent / "drc.json").read_bytes()).hexdigest(),
        "route_report_sha256": hashlib.sha256(args.route_report.read_bytes()).hexdigest() if args.route_report else None,
        "review_inputs": {name: hashlib.sha256((project / name).read_bytes()).hexdigest() for name in (
            "board.copper", "copper.mod", "copper.lock", "assembly.lock",
            "packages/tracker/power_tree.copper", "nrf-antenna-macro.json",
            "logic-power-macro.json", "modem-power-macro.json")},
        "component_count": len(board.placements), "net_count": len(board.nets),
        "track_count": len(board.tracks), "via_count": len(board.vias),
        "copper_layers": manifest["copper_layers"],
        "native_drc_violation_count": len(drc["violations"]),
        "native_unconnected_item_count": len(drc["unconnected_items"]),
        "qualified_release": manifest["qualified_release"],
        "placement_view": "Same candidate poses and pads, with tracks/vias/zones hidden for illustration.",
        "routing_views": "Native KiCad exports of the unchanged filled review candidate; unmirrored top view.",
    }
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
    if hashlib.sha256(pcb.read_bytes()).hexdigest() != pcb_digest:
        raise ValueError("Rendering changed the authoritative PCB")
    write_json(output / "electrical-ir.excerpt.json", electrical_excerpt)
    write_json(output / "physical-ir.excerpt.json", physical_excerpt)
    snapshot["rendered_assets"] = {
        name: hashlib.sha256((output / name).read_bytes()).hexdigest()
        for name in ("electrical-ir.excerpt.json", "physical-ir.excerpt.json",
                     *(name for _, _, name in plots))
    }
    write_json(output / "snapshot.json", snapshot)


if __name__ == "__main__":
    main()
