"""Board-specific showcase snapshots; never routing or production signoff.

Use the compiler's source/native checkpoint guard and authoritative electrical
serializer. Native pads remain visible; a combined view hides fills in a
temporary presentation copy. The authoritative native candidate is untouched.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import argparse
import shutil
import sys
import tempfile

import pcbir

from pcbir.loader import load_design
from pcbir.serializer import board_to_dict
from pcbir.importers.kicad_mod import _children, _first, _parse_sexpr
from pcbir.quantities import decimal_text
from decimal import Decimal
from checkpoint_source import current_candidate

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ("placement.svg", "routing-top.svg", "routing-inner.svg", "routing-bottom.svg", "routing-all.svg")


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_assets(pcb, cli, renderer, output):
    with tempfile.TemporaryDirectory(prefix="tracker-figures-") as folder:
        rendered = Path(folder)
        subprocess.run([sys.executable, str(renderer), "--pcb", str(pcb),
                        "--kicad-cli", str(cli), "--output", str(rendered)], check=True)
        metadata = json.loads((rendered / "rendering.json").read_text())
        if metadata["pcb_sha256"] != digest(pcb):
            raise ValueError("Rendering metadata does not describe the native PCB")
        output.mkdir(parents=True, exist_ok=True)
        for name in (*VIEWS, "rendering.json"):
            shutil.copyfile(rendered / name, output / name)
    return {"renderer_sha256": digest(renderer), "metadata": "rendering.json"}


def describe_rendering(snapshot, rendering):
    snapshot["rendering"] = rendering
    snapshot["placement_view"] = "Native front package pads (gold), fabrication outlines and courtyards at the recorded poses; tracks, vias and fills omitted; reference/value labels hidden."
    snapshot["routing_views"] = "Native KiCad exports of the recorded review candidate, with surface package pads highlighted gold; unmirrored top view. The combined six-copper-layer view hides zones and solid copper fill graphics in a temporary copy, preserving native pads, tracks and vias."


def refresh_figures(pcb, cli, renderer, output):
    """Refresh an exact retained candidate without claiming current-source validation."""
    snapshot_path = output / "snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if digest(pcb) != snapshot["pcb_sha256"]:
        raise ValueError("The retained snapshot does not describe this PCB")
    if digest(pcb.parent / "drc.json") != snapshot["native_drc_sha256"]:
        raise ValueError("Native DRC does not match the retained snapshot")
    for name, expected in snapshot["rendered_assets"].items():
        if digest(output / name) != expected:
            raise ValueError(f"Existing showcase asset does not match its snapshot: {name}")
    rendering = render_assets(pcb, cli, renderer, output)
    describe_rendering(snapshot, rendering)
    for name in (*VIEWS, "rendering.json"):
        snapshot["rendered_assets"][name] = digest(output / name)
    write_json(snapshot_path, snapshot)


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
    parser.add_argument("--renderer", type=Path, default=Path(pcbir.__file__).resolve().parents[1] / "scripts/render_board_showcase.py",
                        help="shared CopperScript native showcase renderer")
    parser.add_argument("--refresh-figures", action="store_true",
                        help="refresh only artwork of the checksum-bound retained snapshot; preserve historical source/review evidence")
    args = parser.parse_args()
    pcb = args.pcb.resolve()
    if args.refresh_figures:
        refresh_figures(pcb, args.kicad_cli, args.renderer.resolve(), ROOT / "docs/showcase")
        return
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
            "src/tracker/power_tree.copper", "nrf-antenna-macro.json",
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
    describe_rendering(snapshot, render_assets(pcb, args.kicad_cli, args.renderer.resolve(), output))
    if hashlib.sha256(pcb.read_bytes()).hexdigest() != pcb_digest:
        raise ValueError("Rendering changed the authoritative PCB")
    write_json(output / "electrical-ir.excerpt.json", electrical_excerpt)
    write_json(output / "physical-ir.excerpt.json", physical_excerpt)
    snapshot["rendered_assets"] = {
        name: hashlib.sha256((output / name).read_bytes()).hexdigest()
        for name in ("electrical-ir.excerpt.json", "physical-ir.excerpt.json",
                     *VIEWS, "rendering.json")
    }
    write_json(output / "snapshot.json", snapshot)


if __name__ == "__main__":
    main()
