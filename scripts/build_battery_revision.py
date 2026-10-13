"""Compose an isolated full-board source revision with local library inputs.

Board composition only; compiler, geometry, macros and placement use CopperScript.
Does not alter canonical source/locks or import historical routed copper.
Default builds need no historical PCB; standard route-board owns placement and
routing. An explicit pinned pose seed is historical reproduction only.
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
from pcbir.hard_macros import materialize_hard_macros
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
    parser.add_argument("--pose-seed", type=Path, help="optional pinned historical placement reproduction; omitted for a fresh source-only build")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--modem-power", action="store_true", help="combine the reusable local modem bypass bank and regional distribution revision")
    parser.add_argument("--rf-layout", action="store_true", help="compose the two-edge-open antenna corner revision using its CopperLib asset")
    parser.add_argument("--rf-support", action="store_true", help="compose unqualified LTE DC-block/tuning/ESD and passive GNSS ESD support")
    args = parser.parse_args()
    library, footprints, work = args.library_review_root.resolve(), args.kicad_footprint_root.resolve(), args.output.resolve()
    if work.exists():
        raise ValueError("output exists; preserve the old review")
    if args.rf_support and not (args.rf_layout and args.modem_power):
        raise ValueError("RF support revision requires --rf-layout and --modem-power")
    if args.rf_layout and not args.modem_power:
        raise ValueError("cellular RF layout revision requires --modem-power support module")
    if args.rf_layout and args.pose_seed is not None:
        raise ValueError("RF layout revision requires a fresh source-only build, not a historical pose seed")
    if args.pose_seed is not None and hash_file(args.pose_seed) != PRIOR_NATIVE_SHA256:
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
    if args.rf_layout:
        shutil.copy2(ROOT / 'revisions/rf-layout-v1/nrf-antenna-macro.json', work / 'nrf-antenna-macro.json')
        pose_changes.update(load_json(ROOT / 'revisions/rf-layout-v1/placement.json')['poses'])
        antenna_revision = 'rf-support-v1' if args.rf_support else 'rf-layout-v1'
        antenna = load_json(ROOT / 'revisions' / antenna_revision / 'antenna-selection.json')
        if (antenna['gnss']['antenna_type'] != 'passive'
                or antenna['gnss']['board_supplied_bias'] is not False
                or antenna['gnss']['external_antenna_power_required'] is not False):
            raise ValueError("RF revision implements only the approved passive GNSS input")
        shutil.copy2(ROOT / 'revisions' / antenna_revision / 'antenna-selection.json', work / 'antenna-selection.json')
        fabrication = load_json(ROOT / 'revisions/rf-layout-v1/fabrication-selection.json')
        shutil.copy2(ROOT / 'revisions/rf-layout-v1/fabrication-selection.json', work / 'fabrication-selection.json')
        # External assembly/supplier facts are library-owned companion data,
        # not fictional PCB components or tracker-local routing algorithms.
        selection_files = {
            'cellular-antenna-specification': (antenna['cellular'], 'library_specification'),
            'cellular-antenna-contract': (antenna['cellular'], 'library_contract'),
            'selected-stackup': (fabrication, 'library_profile'),
            'selected-calculator-model': (fabrication, 'library_calculator_model'),
        }
        if args.rf_support:
            selection_files.update({
                'gnss-antenna-specification': (antenna['gnss'], 'library_specification'),
                'gnss-antenna-contract': (antenna['gnss'], 'library_contract'),
            })
            decision = load_json(ROOT / 'revisions/rf-support-v1/gnss-prototype-decision.json')
            if (decision['selected_option'] != 'integrated-front-end-baseline'
                    or decision['external_saw_fitted'] is not False
                    or decision['external_saw_footprint_reserved'] is not False):
                raise ValueError('RF support source implements only the unfiltered experimental GNSS baseline')
            shutil.copy2(ROOT / 'revisions/rf-support-v1/gnss-prototype-decision.json', work / 'gnss-prototype-decision.json')
            options_path = (library / decision['library_options']).resolve()
            options_path.relative_to(library)
            options = load_json(options_path)
            if (options['production_publishable'] is not False
                    or not any(o['id'] == decision['selected_option'] for o in options['options'])):
                raise ValueError('GNSS experimental library option is absent or incorrectly qualified')
            selection_files['gnss-prototype-options'] = ({
                'library_options': decision['library_options'],
                'library_options_sha256': hash_file(options_path)}, 'library_options')
            selection_files['gnss-datasheet-review'] = (decision, 'library_datasheet_review')
        selection_bindings = {}
        evidence_dir = work / 'rf-library-evidence'
        evidence_dir.mkdir()
        for name, (selection, key) in selection_files.items():
            selected = (library / selection[key]).resolve()
            selected.relative_to(library)
            expected = selection[key + '_sha256']
            if hash_file(selected) != expected:
                raise ValueError(f'RF library selection changed: {name}; review before rebuilding')
            copied = evidence_dir / (name + '.json')
            shutil.copy2(selected, copied)
            selection_bindings[name] = {'library_path': selection[key], 'sha256': expected,
                                        'copied_path': copied.relative_to(work).as_posix()}
        feed = (ROOT / 'revisions/rf-layout-v1/cellular-feed.copper').read_text(encoding='utf-8')
        source, count = re.subn(r'constraint routing\(CELL_RF\)\s*\{[^}]*\}',
            lambda _: feed.strip(), source)
        if count != 1:
            raise ValueError('RF revision requires exactly one cellular feed routing constraint')
        source = source.replace('constraint max_distance(J_GNSS, U_GNSS.RF_IN)',
            '// User-selected passive GNSS antenna: no board-powered bias injection.\n    constraint max_distance(J_GNSS, U_GNSS.RF_IN)')
    if args.rf_support:
        source, count = re.subn(r'constraint routing\(CELL_RF\)\s*\{[^}]*\}', '', source)
        if count != 1:
            raise ValueError('RF support revision requires exactly one original cellular feed rule')
        source = source.replace('board CopperAssetTracker {', '''board CopperAssetTracker {
    import cell_support "github.com/andenore/CopperLib/packages/circuits/simcom/lte-antenna-support";
    import gnss_esd "github.com/andenore/CopperLib/packages/parts/ti/tpd1e01b04";''')
        old_cell = 'net CELL_RF { U_MODEM.ANT_MAIN; J_CELL.SIGNAL; }'
        old_gnss = 'net GNSS_RF { U_GNSS.RF_IN; J_GNSS.SIGNAL; }'
        if source.count(old_cell) != 1 or source.count(old_gnss) != 1:
            raise ValueError('RF support revision requires exact original feed bindings')
        source = source.replace(old_cell, 'net CELL_RF { U_MODEM.ANT_MAIN; CELL_MATCH.HOST; }')
        source = source.replace(old_gnss, 'net GNSS_RF { U_GNSS.RF_IN; J_GNSS.SIGNAL; D_GNSS_ESD.IO; }')
        source = source.replace('net GND {', 'net GND { CELL_MATCH.GND; D_GNSS_ESD.RETURN;', 1)
        source = source.replace('max_distance(J_GNSS, U_GNSS.RF_IN) { distance = 5mm; }',
            'max_distance(J_GNSS, U_GNSS.RF_IN) { distance = 8mm; }')
        gnss_feed = '''constraint routing(GNSS_RF) {
        kind = rf_feed; priority = 120; target_impedance_ohms = 50;
        topology = "tree"; // Explicit connector/receiver/TVS support topology.
        width = 142um; clearance = 201um;
        allowed_layers = "F.Cu"; max_vias = 0; max_length = 12mm;
    }'''
        source, count = re.subn(r'constraint routing\(GNSS_RF\)\s*\{[^}]*\}', lambda _: gnss_feed, source)
        if count != 1:
            raise ValueError('RF support revision requires exactly one GNSS feed rule')
        source = source.rstrip()[:-1] + '\n' + (ROOT / 'revisions/rf-support-v1/support.copper').read_text() + '\n}\n'
        pose_changes.update(load_json(ROOT / 'revisions/rf-support-v1/placement.json')['poses'])
        # The coax now occupies the previous translator bank's fixed poses.
        # Keep its circuit and decoupling intent; let the shared placer choose
        # legal local poses instead of importing historical coordinates.
        for reference in ('U_MODEM_STATUS', 'C_STATUS_A', 'C_STATUS_B'):
            pose_changes.pop(reference)
            # A canonical source pose may predate the revision override.
            source, count = re.subn(r'constraint fixed_placement\(' + re.escape(reference)
                + r'\)\s*\{[^}]*\}', '', source)
            if count > 1:
                raise ValueError('duplicate source pose while releasing RF-space companion')
    for reference, pose in pose_changes.items():
        rule = f"constraint fixed_placement({reference}) {{ x = {pose['x_mm']}mm; y = {pose['y_mm']}mm; rotation = {pose['rotation']}; side = front; }}"
        pattern = r"constraint fixed_placement\(" + re.escape(reference) + r"\)\s*\{[^}]*\}"
        source, count = re.subn(pattern, lambda _: rule, source)
        if count > 1:
            raise ValueError("duplicate source pose")
        if count == 0:
            source = source.rstrip()[:-1] + "\n    " + rule + "\n}\n"
    # Revision JSON files are retained historical selection templates. Fresh
    # generated boards carry their selected bindings directly in the source.
    for filename, alias in (("nrf-antenna-macro.json", "nordic_layout"),
                            ("logic-power-macro.json", "logic_layout"),
                            ("modem-power-macro.json", "modem_layout")):
        scene = load_json(work / filename)
        asset = scene["asset"]
        if not asset.startswith(("github.com/", "gitlab.com/", "https://")):
            asset = "./" + asset
        source, count = re.subn(r'import ' + re.escape(alias) + r' "[^"]+";',
            lambda _: f'import {alias} "{asset}";', source)
        if count != 1:
            raise ValueError("missing or duplicate macro asset import")
        source, count = re.subn(r'physical_macro ' + re.escape(scene["name"])
            + r'\s*:\s*' + re.escape(alias) + r'(?:\s+on\s+[^{}]+)?\s*\{[^}]*\}', '', source)
        if count != 1:
            raise ValueError("missing or duplicate canonical macro binding")
        mappings = [f"        member {key} = {target};" for key, target in scene["bindings"].items()]
        mappings += [f"        net {key} = {target};" for key, target in scene["net_bindings"].items()]
        declaration = f'    physical_macro {scene["name"]}: {alias} {{\n' + "\n".join(mappings) + "\n    }"
        source = source.rstrip()[:-1].rstrip() + "\n" + declaration + "\n}\n"
    (work / "board.copper").write_text(source, encoding="utf-8")
    manifest = (ROOT / "copper.mod").read_text(encoding="utf-8")
    manifest += f"\nreplace github.com/andenore/CopperLib => {library.as_posix()}\n"
    manifest += f"replace github.com/KiCad/kicad-footprints => {footprints.as_posix()}\n"
    if args.rf_support:
        manifest += 'footprint-library TPD1E01B04 github.com/andenore/CopperLib/packages/parts/ti/tpd1e01b04/footprints\n'
        manifest += 'footprint-library RCLAMP1561PQ github.com/andenore/CopperLib/packages/parts/semtech/rclamp1561pq/footprints\n'
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
    if args.rf_support:
        extra = load_json(ROOT / 'revisions/rf-support-v1/procurement.json')
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
    if args.pose_seed is None:
        # Composition only. Do not add another project-local placement/router:
        # the standard compiler command runs and validates those stages next.
        document = {"schema": "copperassettracker-battery-revision-build/v0.1",
            "qualified_release": False, "modem_power_revision": args.modem_power,
            "rf_layout_revision": args.rf_layout,
            "rf_support_revision": args.rf_support,
            "library_mode": "explicit_unlocked_working_copy_review", "erc_errors": 0,
            "components": len(elaborate(design.electrical).components), "copper_layers": 6,
            "placement_status": "not_run_use_shared_route_board", "preserved_pose_count": 0,
            "ordinary_historical_copper_imported": False, "assembly_reviewed": False,
            "inputs": {"prior_native": None, "canonical_board": hash_file(ROOT / "board.copper"),
                "revision": hash_file(ROOT / "revisions/battery-v1/power_tree.copper"),
                "revision_procurement": hash_file(ROOT / "revisions/battery-v1/procurement.json"),
                "placement_choices": hash_file(ROOT / "revisions/battery-v1/placement.json"),
                "generated_board": hash_file(work / "board.copper"),
                "builder": hash_file(Path(__file__)), "resolved_lock": hash_file(work / "copper.lock")},
            "outputs": {"electrical_ir": hash_file(work / "electrical.ir.json"),
                "assembly_lock": hash_file(work / "assembly.lock")}}
        if args.modem_power:
            document['inputs']['modem_revision'] = {name: hash_file(ROOT / 'revisions/modem-power-v1' / name)
                for name in ('distribution.copper', 'placement.json', 'procurement.json', 'modem-power-macro.json')}
        if args.rf_layout:
            document['inputs']['rf_revision'] = {name: hash_file(ROOT / 'revisions/rf-layout-v1' / name)
                for name in ('placement.json', 'nrf-antenna-macro.json', 'README.md', 'antenna-selection.json', 'cellular-feed.copper', 'fabrication-selection.json')}
            document['inputs']['rf_library_selection'] = selection_bindings
            document['cellular_antenna'] = antenna['cellular']['mpn']
            document['selected_stackup'] = fabrication['selected_profile']
            document['gnss_antenna_type'] = antenna['gnss']['antenna_type']
            scene = load_json(work / 'nrf-antenna-macro.json')
            document['inputs']['rf_asset'] = hash_file(library / scene['asset'].split('CopperLib/', 1)[1])
            if document['inputs']['rf_asset'] != scene['asset_sha256']:
                raise ValueError("RF macro library asset identity changed")
        if args.rf_support:
            document['inputs']['rf_support_revision'] = {name: hash_file(ROOT / 'revisions/rf-support-v1' / name)
                for name in ('antenna-selection.json', 'support.copper', 'placement.json', 'procurement.json', 'gnss-prototype-decision.json')}
            document['gnss_antenna'] = antenna['gnss']['mpn']
            document['rf_coexistence_status'] = 'unqualified_filter_decision_requires_coupling_evidence'
        (work / "revision-build.json").write_text(json.dumps(document, indent=2, allow_nan=False) + "\n")
        print(json.dumps(document, indent=2), flush=True)
        return 0
    board = resolved_physicalize(design, FootprintResolver(base_directory=work, offline=True),
        PrototypePhysicalOptions(copper_layers=6, fabrication_profile="jlcpcb-six-layer"))
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
