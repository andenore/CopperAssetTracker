"""Board-specific showcase snapshots; never routing or production signoff.

Use the compiler's source/native checkpoint guard and authoritative electrical
serializer. Placement illustrations deliberately hide copper, keeping the exact
candidate poses; routing plots use the untouched filled native candidate.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import argparse

from pcbir.loader import load_design
from pcbir.serializer import board_to_dict
from pcbir.importers.kicad_mod import _children, _first, _parse_sexpr
from pcbir.quantities import decimal_text
from decimal import Decimal
from checkpoint_source import current_candidate

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_placement_excerpt(pcb):
    tree = _parse_sexpr(pcb.read_text(encoding="utf-8"), str(pcb))
    placements = []
    for footprint in _children(tree, "footprint"):
        reference = next(p[2] for p in _children(footprint, "property") if p[1] == "Reference")
        if reference not in {"U_MODEM", "U_MODEM_U", "C_MCU"}:
            continue
        at = _first(footprint, "at")
        placements.append({"reference": reference, "footprint": footprint[1],
            "position_mm": {"x": decimal_text(Decimal(at[1])), "y": decimal_text(Decimal(at[2]))},
            "rotation_degrees": decimal_text(Decimal(at[3]) if len(at) > 3 else Decimal(0))})
    return {"note": "Selected source-checked native PCB placements; not a full physical-IR serialization or production approval.",
            "units": "millimetres and degrees as represented in the KiCad PCB", "placements": placements}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pcb", type=Path, required=True)
    parser.add_argument("--kicad-cli", required=True)
    parser.add_argument("--project-root", type=Path, default=ROOT, help="source revision matching the PCB")
    parser.add_argument("--unlocked-review", action="store_true", help="explicit working-copy revision, not a locked release")
    parser.add_argument("--route-report", type=Path, help="shared route report instead of a manufacturing manifest")
    parser.add_argument("--candidate", help="display identifier for this exact fresh routing review")
    args = parser.parse_args()
    pcb = args.pcb.resolve()
    project = args.project_root.resolve()
    pcb_digest = hashlib.sha256(pcb.read_bytes()).hexdigest()
    board = current_candidate(pcb, project_root=project, locked=True)
    output = ROOT / "docs/showcase"
    design = load_design(project / "board.copper", locked=True, offline=True)
    ir = board_to_dict(design)
    electrical_excerpt = {
        "schema": ir["schema"], "kind": ir["kind"], "name": ir["name"],
        "components": [c for c in ir["components"] if c["ref"] == "C_MCU"],
        "nets": [n for n in ir["nets"] if n["name"] == "V3V8"],
    }
    physical_excerpt = native_placement_excerpt(pcb)
    drc = json.loads((pcb.parent / "drc.json").read_text())
    route = None
    if args.route_report:
        route = json.loads(args.route_report.read_text())
        evidence = route["plane_verification"]
        if (route["status"] != "pass" or not route["routing_complete"] or not evidence["passed"]
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
    revision_build = json.loads((project / "revision-build.json").read_text()) if (project / "revision-build.json").exists() else {}
    revision = ("rf-support-v1" if revision_build.get("rf_support_revision") else
                "rf-layout-v1" if revision_build.get("rf_layout_revision") else
                "modem-power-v1" if revision_build.get("modem_power_revision") else "canonical")
    composition_paths = ["board.copper", "scripts/build_battery_revision.py"]
    if revision_build:
        composition_paths += ["revisions/battery-v1/" + name for name in
                              ("power_tree.copper", "placement.json", "procurement.json")]
        for field, directory in (("modem_revision", "modem-power-v1"),
                                 ("rf_revision", "rf-layout-v1"), ("rf_support_revision", "rf-support-v1")):
            composition_paths += ["revisions/" + directory + "/" + name
                                  for name in revision_build.get("inputs", {}).get(field, {})]
    composition_inputs = {name: digest(ROOT / name) for name in composition_paths}
    if revision_build and (revision_build["inputs"]["generated_board"] != digest(project / "board.copper")
                           or revision_build["inputs"]["canonical_board"] != digest(ROOT / "board.copper")
                           or revision_build["inputs"]["builder"] != digest(ROOT / "scripts/build_battery_revision.py")):
        raise ValueError("Composition evidence no longer matches source or builder")
    snapshot = {
        "schema": "copperassettracker-showcase/v2",
        "candidate": args.candidate or project.parent.name,
        "pcb": str(pcb.relative_to(ROOT)).replace("\\", "/"),
        "pcb_sha256": hashlib.sha256(pcb.read_bytes()).hexdigest(),
        "source": str((project / "board.copper").relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": hashlib.sha256((project / "board.copper").read_bytes()).hexdigest(),
        "canonical_source_sha256": hashlib.sha256((ROOT / "board.copper").read_bytes()).hexdigest(),
        "canonical_source_status": "current_source",
        "canonical_source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "revision": revision,
        "locked_release_input": not args.unlocked_review,
        "composition_inputs": composition_inputs,
        "native_report_sha256": hashlib.sha256((pcb.parent / "drc.json").read_bytes()).hexdigest(),
        "route_report_sha256": hashlib.sha256(args.route_report.read_bytes()).hexdigest() if args.route_report else None,
        "native_drc_sha256": digest(pcb.parent / "drc.json"),
        "source_lock_sha256": digest(project / "copper.lock"),
        "assembly_lock_sha256": digest(project / "assembly.lock"),
        "electrical_ir_sha256": digest(project / "electrical.ir.json") if (project / "electrical.ir.json").exists() else None,
        "routing_code_inputs_sha256": digest(project / "code-inputs.json") if (project / "code-inputs.json").exists() else None,
        "source_freeze_sha256": digest(project / "source-freeze.json") if (project / "source-freeze.json").exists() else None,
        "route_summary_sha256": digest(args.route_report.with_name(args.route_report.stem + ".summary.json")) if args.route_report else None,
        "routing_status": route["status"] if route else "export_manifest",
        "blocked_requirement_count": route["requirements"]["counts"].get("blocked", 0) if route else None,
        "ignored_drc_check_types": [item["key"] for item in drc.get("ignored_checks", [])],
        "independent_cam": "not_run_for_this_routing_review",
        "manufacturing_export": "not_generated_for_this_routing_review",
        "supplier_availability": "not_checked_by_this_run",
        "assembly_preview_review": "not_approved",
        "macro_binding": "in_language" if design.electrical.physical_macros else "historical_scenes",
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
    # Select native artwork layers instead of rebuilding or editing copper.
    # This also preserves required via arrays and immutable macro ownership.
    snapshot["placement_view"] = "Native front fabrication/courtyard artwork from the same fresh route, with copper omitted."
    plots = (
        (pcb, "F.Fab,F.CrtYd,Edge.Cuts", "placement.svg"),
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
