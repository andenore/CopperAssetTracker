"""Application bindings only; numerical/evidence algorithms stay in CopperScript.

Explicit working-library review, not locked-package resolution or release approval.
Never modifies a PCB, source, BOM, package lock or previously generated report.
"""
import argparse
from pathlib import Path
import json

import pcbir.engineering_qualification as engineering
from pcbir.qualification import check, hash_file, load_json, report

ROOT = Path(__file__).resolve().parents[1]


def assess(root: Path, library: Path):
    selection_path = root / "docs/battery-selection.json"
    selection = load_json(selection_path)
    cell_path = library / selection["library_specification"]
    charger_path = library / selection["library_charger_limits"]
    cell, charger = load_json(cell_path), load_json(charger_path)
    if cell["id"] != selection["selected_external_cell"] or charger["id"] != "ti.bq24072":
        raise ValueError("unexpected selected cell or charger identity")
    pack = cell["datasheet_pack"]
    actual_source = hash_file(root / "src/tracker/power_tree.copper")
    source_matches = actual_source == selection["reviewed_power_source_sha256"]
    checks = []
    for identifier, metric, value, maximum, basis in (
        ("battery.charge-voltage", "maximum_charge_mv", charger["battery_regulation_max_mv"],
         pack["charge_voltage_max_mv"], "TI EC p13 vs Kjell linked pack datasheet section 4.3; applicability still pending"),
        ("battery.nominal-hot-cutoff", "nominal_hot_cutoff_c", charger["nominal_direct_10k_ntc_hot_c"],
         pack["charge_temperature_max_c"], "TI nominal 10k NTC window vs pack section 4.7; not a guaranteed tolerance-corner model"),
    ):
        checks.append(engineering.evaluate_requirement(identifier, {"algorithm": "range", "stage": "design"},
            {"basis": basis, "values": {metric: value if source_matches else None},
             "limits": {metric: {"maximum": maximum}}}, None, {}, None))
    checks.append(check("battery.source-binding", "pass" if source_matches else "incomplete",
        "Source matches reviewed direct-TS/grounded-CE/open-TMR circuit" if source_matches
        else "Power source changed: previous circuit assumptions must be reviewed again"))
    for identifier, detail in (
        ("battery.source-applicability", "Current retail revision and exact pack source equivalence not reviewed"),
        ("battery.harness-current", "Holder, wiring, connector, pack protection trip/recovery and worst-case load not qualified"),
        ("battery.temperature-corners", "Cell-mounted sensor and guaranteed cutoff corners not implemented/reviewed"),
        ("battery.charge-timer", "Open-TMR timeout versus selected capacity, taper, input/thermal regulation and system load unresolved"),
        ("battery.prototype", "Actual battery-only USB, modem bursts, charging and safe undervoltage states not measured"),
    ):
        checks.append(check(identifier, "incomplete", detail, stage="bench" if identifier.endswith("prototype") else "design"))
    inputs = {"library_mode": "explicit_unlocked_working_copy_review", "files": {
        "selection": hash_file(selection_path), "cell": hash_file(cell_path),
        "charger": hash_file(charger_path), "power_source": actual_source,
        "board_source": hash_file(root / "board.copper"), "assembly_lock": hash_file(root / "assembly.lock"),
        "library_lock": hash_file(root / "copper.lock"), "review_script": hash_file(Path(__file__)),
        "range_algorithm": hash_file(Path(engineering.__file__)),
        "qualification_algorithm": hash_file(Path(engineering.__file__).with_name("qualification.py")),
        "numeric_validation": hash_file(Path(engineering.__file__).with_name("power_integrity.py")),
        "compiler_lock": hash_file(root / "uv.lock"),
    }}
    result = report("tracker-battery-integration-screen", inputs, checks)
    result["locked_release_input"] = False
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library-review-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = assess(ROOT, args.library_review_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    for item in result["checks"]:
        print(f"{item['status']}: {item['id']} - {item['detail']}")
    return 1 if result["status"] == "fail" else 2


if __name__ == "__main__":
    raise SystemExit(main())
