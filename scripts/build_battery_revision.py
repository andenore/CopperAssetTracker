"""Build an isolated full-board electrical/placement draft with local library inputs.

Board composition only; compiler, geometry, macros and placement use CopperScript.
Does not alter canonical source/locks or import historical routed copper.
"""
import argparse
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import shutil
import re

from pcbir.assembly import load_lock, lock_to_json, snapshot
from pcbir.backends.kicad_pcb import KiCadPcbBackend, kicad_reference
from pcbir.backends.kicad_project import write_kicad_project
from pcbir.compiler import compile_design_file
from pcbir.elaborate import elaborate
from pcbir.erc import check, has_errors
from pcbir.footprints import FootprintResolver
from pcbir.hard_macros import apply_hard_macro_scene, materialize_hard_macros
from pcbir.importers.kicad_mod import _children, _first, _parse_sexpr
from pcbir.physical import Point
from pcbir.physicalize import PrototypePhysicalOptions, resolved_physicalize
from pcbir.placement import placement_rejection_reasons
from pcbir.qualification import hash_file, load_json
from pcbir.serializer import write_json

from review_battery_revision import ROOT, assess


PRIOR_NATIVE_SHA256 = "8282270ea329f5f7ae82b36b672419bd1380057a8be7fd8a62b9e93d19e9d24d"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library-review-root", type=Path, required=True)
    parser.add_argument("--kicad-footprint-root", type=Path, required=True)
    parser.add_argument("--pose-seed", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--modem-power", action="store_true", help="combine the reusable local modem bypass bank and regional distribution revision")
    args = parser.parse_args()
    library, footprints, work = args.library_review_root.resolve(), args.kicad_footprint_root.resolve(), args.output.resolve()
    if work.exists():
        raise ValueError("output exists; preserve the old review")
    if hash_file(args.pose_seed) != PRIOR_NATIVE_SHA256:
        raise ValueError("pose seed must be the pinned RF checkpoint")
    screen = assess(ROOT, library)
    work.mkdir(parents=True, exist_ok=False)
    shutil.copytree(ROOT / "packages", work / "packages")
    shutil.copytree(ROOT / "assets", work / "assets")
    for name in ("board.copper", "nrf-antenna-macro.json", "logic-power-macro.json", "modem-power-macro.json"):
        shutil.copy2(ROOT / name, work / name)
    shutil.copy2(ROOT / "revisions/battery-v1/power_tree.copper", work / "packages/tracker/power_tree.copper")
    pose_changes = load_json(ROOT / "revisions/battery-v1/placement.json")["poses"]
    source = (work / "board.copper").read_text(encoding="utf-8")
    if args.modem_power:
        shutil.copy2(ROOT / 'revisions/modem-power-v1/modem-power-macro.json', work / 'modem-power-macro.json')
        source = source.replace('import simcom "github.com/andenore/CopperLib/packages/parts/simcom/sim7670g-lngv";',
            'import simcom "github.com/andenore/CopperLib/packages/circuits/simcom/sim7670g-vbat-bypass";')
        source = source.replace('component U_MODEM: simcom.SIM7670G_LNGV;', 'module U_MODEM: simcom.SIM7670G_VBAT_BYPASS;')
        source = source.replace('fixed_placement(U_MODEM)', 'fixed_placement(U_MODEM/U)')
        source = re.sub(r'(constraint max_distance\([^}]+)U_MODEM\.', r'\1U_MODEM/U.', source)
        # Authored reservoir-origin bound changes to make room for the four
        # genuinely local, pad-associated bypasses. Not a vendor maximum.
        source = source.replace('max_distance(C_MODEM_BULK, U_MODEM/U.VBAT_1) { distance = 5mm; }',
            'max_distance(C_MODEM_BULK, U_MODEM/U.VBAT_1) { distance = 7mm; }')
        source = source.rstrip()[:-1] + '\n' + (ROOT / 'revisions/modem-power-v1/distribution.copper').read_text() + '\n}\n'
        pose_changes.update(load_json(ROOT / 'revisions/modem-power-v1/placement.json')['poses'])
    for reference, pose in pose_changes.items():
        rule = f"constraint fixed_placement({reference}) {{ x = {pose['x_mm']}mm; y = {pose['y_mm']}mm; rotation = {pose['rotation']}; side = front; }}"
        pattern = r"constraint fixed_placement\(" + re.escape(reference) + r"\)\s*\{[^}]*\}"
        source, count = re.subn(pattern, lambda _: rule, source)
        if count > 1:
            raise ValueError("duplicate source pose")
        if count == 0:
            source = source.rstrip()[:-1] + "\n    " + rule + "\n}\n"
    (work / "board.copper").write_text(source, encoding="utf-8")
    manifest = (ROOT / "copper.mod").read_text(encoding="utf-8")
    manifest += f"\nreplace github.com/andenore/CopperLib => {library.as_posix()}\n"
    manifest += f"replace github.com/KiCad/kicad-footprints => {footprints.as_posix()}\n"
    (work / "copper.mod").write_text(manifest, encoding="utf-8")
    design = compile_design_file(work / "board.copper", offline=True)
    diagnostics = check(design.electrical)
    if has_errors(diagnostics):
        raise ValueError(f"electrical errors: {diagnostics}")
    write_json(design, work / "electrical.ir.json")
    (work / "battery-screen.json").write_text(json.dumps(screen, indent=2, allow_nan=False) + "\n")
    # Preserve candidate identities only; changed/new references remain unreviewed.
    prior = {s.reference: s for s in load_lock(ROOT / "assembly.lock").selections}
    proposals = load_json(ROOT / "revisions/battery-v1/procurement.json")
    if args.modem_power:
        extra = load_json(ROOT / 'revisions/modem-power-v1/procurement.json')
        proposals['components'].update(extra['components'])
        proposals['reuse_candidates'].update(extra['reuse_candidates'])
    lock = snapshot(design.electrical)
    selections = []
    for selection in lock.selections:
        candidate = proposals["components"].get(selection.reference)
        reused = proposals["reuse_candidates"].get(selection.reference)
        if candidate:
            selection = replace(selection, **{k: candidate[k] for k in
                ("manufacturer", "mpn", "supplier", "supplier_part", "source_url")}, reviewed=False)
        elif reused:
            old = prior[reused]
            selection = replace(selection, manufacturer=old.manufacturer, mpn=old.mpn, supplier=old.supplier,
                supplier_part=old.supplier_part, source_url=old.source_url, reviewed=False)
        elif selection.reference in prior:
            old = prior[selection.reference]
            if old.part == selection.part and old.footprint == selection.footprint:
                selection = replace(selection, manufacturer=old.manufacturer, mpn=old.mpn, supplier=old.supplier,
                    supplier_part=old.supplier_part, source_url=old.source_url, reviewed=False)
        selections.append(selection)
    (work / "assembly.lock").write_text(lock_to_json(replace(lock, selections=tuple(selections))), encoding="utf-8")
    board = resolved_physicalize(design, FootprintResolver(base_directory=work, offline=True),
        PrototypePhysicalOptions(copper_layers=6, fabrication_profile="jlcpcb-six-layer"))
    for scene in ("nrf-antenna-macro.json", "logic-power-macro.json", "modem-power-macro.json"):
        board = apply_hard_macro_scene(board, work / scene, offline=True)
    reverse = {kicad_reference(p.reference): p.reference for p in board.placements}
    if args.modem_power:
        reverse['U_MODEM'] = 'U_MODEM/U'
    poses = {p.reference: p for p in board.placements}
    fixed = set()
    tree = _parse_sexpr(args.pose_seed.read_text(), str(args.pose_seed))
    for fp in _children(tree, "footprint"):
        ref = next(p[2] for p in _children(fp, "property") if p[1] == "Reference")
        reference = reverse[ref]
        at = _first(fp, "at")
        poses[reference] = replace(poses[reference], position=Point.mm(at[1], at[2]),
            rotation_degrees=(Decimal(at[3]) + 360) % 360 if len(at) > 3 else 0)
        fixed.add(reference)
    # New source poses override historical placements; no historical ordinary copper.
    changed_existing = fixed & pose_changes.keys()
    for reference, pose in pose_changes.items():
        poses[reference] = replace(poses[reference], position=Point.mm(pose["x_mm"], pose["y_mm"]),
            rotation_degrees=pose["rotation"])
    board = replace(board, placements=tuple(poses.values()))
    print(f"ERC clean: {len(elaborate(design.electrical).components)} components; preserving {len(fixed - changed_existing)} old poses", flush=True)
    preflight = placement_rejection_reasons(board, poses)
    (work / "placement-preflight.json").write_text(json.dumps({"qualified_release": False, "rejections": preflight}, indent=2) + "\n")
    if preflight:
        raise ValueError("placement preflight: " + "; ".join(preflight))
    board = materialize_hard_macros(board)
    reasons = placement_rejection_reasons(board, {p.reference: p for p in board.placements})
    write_kicad_project(KiCadPcbBackend().generate(board), work / "placed-unrouted.kicad_pcb")
    document = {"schema": "copperassettracker-battery-revision-build/v0.1", "qualified_release": False,
        "modem_power_revision": args.modem_power,
        "library_mode": "explicit_unlocked_working_copy_review", "erc_errors": 0,
        "components": len(board.placements), "copper_layers": len(board.stackup.copper_layers),
        "preserved_pose_count": len(fixed - changed_existing), "changed_existing_poses": sorted(changed_existing), "ordinary_historical_copper_imported": False,
        "placement_rejections": reasons, "assembly_reviewed": False,
        "inputs": {"prior_native": hash_file(args.pose_seed), "revision": hash_file(ROOT / "revisions/battery-v1/power_tree.copper"),
                   "canonical_board": hash_file(ROOT / "board.copper"), "revision_procurement": hash_file(ROOT / "revisions/battery-v1/procurement.json"),
                   "placement_choices": hash_file(ROOT / "revisions/battery-v1/placement.json"), "generated_board": hash_file(work / "board.copper"),
                   "builder": hash_file(Path(__file__)), "resolved_lock": hash_file(work / "copper.lock")},
        "outputs": {"electrical_ir": hash_file(work / "electrical.ir.json"), "pcb": hash_file(work / "placed-unrouted.kicad_pcb"),
                    "assembly_lock": hash_file(work / "assembly.lock")}}
    (work / "revision-build.json").write_text(json.dumps(document, indent=2, allow_nan=False) + "\n")
    if args.modem_power:
        document['inputs']['modem_revision'] = {name: hash_file(ROOT / 'revisions/modem-power-v1' / name)
            for name in ('distribution.copper', 'placement.json', 'procurement.json', 'modem-power-macro.json')}
        (work / "revision-build.json").write_text(json.dumps(document, indent=2, allow_nan=False) + "\n")
    print(json.dumps(document, indent=2), flush=True)
    return 1 if reasons else 0


if __name__ == "__main__":
    raise SystemExit(main())
