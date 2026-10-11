"""Tracker-only bindings for the separate battery revision, never release approval.

Run with the explicit CopperScript working copy. Generic divider/current/timer
algorithms belong there, and source facts belong in the supplied CopperLib.
"""
import argparse
from pathlib import Path
import json
import tempfile

from pcbir import compile_source
from pcbir.elaborate import elaborate
from pcbir.erc import check as electrical_check, has_errors

from pcbir.engineering_qualification import evaluate_requirement
from pcbir.qualification import check, hash_file, load_json, report
import pcbir.power_integrity as power

ROOT = Path(__file__).resolve().parents[1]


def validate_circuit(root, library, design):
    """Bind numerical choices to actual compiled topology, not metadata alone."""
    with tempfile.TemporaryDirectory(prefix="tracker-battery-") as directory:
        work = Path(directory)
        (work / "power").mkdir()
        (work / "power/power_tree.copper").write_bytes((root / design["source"]).read_bytes())
        (work / "copper.mod").write_text("module tracker-battery-review\n"
            "require github.com/andenore/CopperLib v0.1.0\n"
            f"replace github.com/andenore/CopperLib => {library.as_posix()}\n", encoding="utf-8")
        board = compile_source('''board BatteryFixture {
            import power "./power";
            module PWR: power.AssetTrackerPowerTree;
            net INPUT { PWR.VIN5; }
            net GND { PWR.GND; }
            net EN { PWR.MODEM_EN; }
            net LOGIC { PWR.V3V3; }
            net MODEM { PWR.V3V8; }
        }''', str(work / "board.copper"), offline=True)
        if has_errors(electrical_check(board)):
            raise ValueError("battery revision electrical errors")
        flat = elaborate(board)
        components = {c.ref: c for c in flat.components}
        if not components["PWR/U_CHARGE"].part.endswith(".BQ24072TRGTR"):
            raise ValueError("revision does not use BQ24072T")
        for reference, key in (("PWR/TEMP/R_TOP", "upper_ohms"), ("PWR/TEMP/R_SHUNT", "shunt_ohms"),
                               ("PWR/TEMP/R_ISOLATION", "isolation_ohms"), ("PWR/R_ISET", "iset_ohms"),
                               ("PWR/R_TMR", "tmr_ohms")):
            if components[reference].value.in_unit("ohm") != design[key]:
                raise ValueError("revision resistor differs from reviewed choice: " + reference)
        nets = {n.name: {(e.component, e.pin) for e in n.endpoints} for n in flat.nets}
        if nets["PWR/TS_SENSE"] != {("PWR/U_CHARGE", "TS"), ("PWR/TEMP/R_ISOLATION", "P2")}:
            raise ValueError("TS bypasses its isolation resistor or has unexpected connections")
        if nets["PWR/BAT_NTC"] != {("PWR/J_BAT", "P3"), ("PWR/TEMP/R_TOP", "P2"),
                ("PWR/TEMP/R_SHUNT", "P1"), ("PWR/TEMP/R_ISOLATION", "P1")}:
            raise ValueError("NTC divider topology mismatch")
        if not {("PWR/U_CHARGE", "CE"), ("PWR/U_CHARGE", "TD"), ("PWR/R_TMR", "2"),
                ("PWR/U_CHARGE", "EN2"), ("PWR/U_CHARGE", "VSS"), ("PWR/U_CHARGE", "EP"),
                ("PWR/TEMP/R_SHUNT", "P2"), ("PWR/J_BAT", "P2")} <= nets["GND"]:
            raise ValueError("grounded enable/timer/sensor/protected-negative topology mismatch")
        if nets["PWR/TMR"] != {("PWR/U_CHARGE", "TMR"), ("PWR/R_TMR", "1")}:
            raise ValueError("timer is not programmed as reviewed")
        if not {("PWR/TEMP/R_TOP", "P1"), ("PWR/U_CHARGE", "IN"), ("PWR/U_CHARGE", "EN1")} <= nets["INPUT"]:
            raise ValueError("divider is not referenced to charger input")
        if nets["PWR/BAT"] != {("PWR/J_BAT", "P1"), ("PWR/U_CHARGE", "BAT_2"),
                ("PWR/U_CHARGE", "BAT_3"), ("PWR/C_BAT", "1")}:
            raise ValueError("protected positive battery topology mismatch")


def assess(root, library):
    selection = load_json(root / "docs/battery-selection.json")
    design = selection["temperature_cutoff_design"]
    paths = {
        "selection": root / "docs/battery-selection.json",
        "revision": root / design["source"],
        "cell": library / selection["library_specification"],
        "charger": library / design["library_charger_limits"],
        "sensor": library / selection["harness"]["sensor_library_specification"],
        "holder": library / selection["holder"]["library_specification"],
        "bias": library / "packages/circuits/ti/bq24072t-ts-43k-39k/circuit.copper",
        "part": library / "packages/parts/ti/bq24072t/part.copper",
        "power_algorithm": Path(power.__file__),
        "engineering_algorithm": Path(power.__file__).with_name("engineering_qualification.py"),
        "qualification_algorithm": Path(power.__file__).with_name("qualification.py"),
        "review_script": Path(__file__),
    }
    cell, charger, sensor, holder = (load_json(paths[n]) for n in ("cell", "charger", "sensor", "holder"))
    if (cell["id"] != "kjell.32058" or charger["id"] != "ti.bq24072t"
            or sensor["id"] != "semitec.103at-2" or holder["id"] != "mpd.bh-18650-w"):
        raise ValueError("unexpected battery revision identities")
    validate_circuit(root, library, design)
    checks = [check("battery.revision-source-binding", "pass", "Compiled revision matches charger, divider, isolated TS, enabled safety timer and ISET choices")]
    budget = design["assumed_rt_envelope_percent"] / 100
    basis = "Provisional assumed R/T envelope +/-5% and TS leakage +/-100 nA; not guaranteed manufacturer bounds"
    for label, temp, limit_name, bound in (
        ("cold", design["screen_cold_c"], "minimum_ratio", {"minimum": charger["cold_threshold_max_permille_vin"] / 1000}),
        ("hot", design["screen_hot_c"], "maximum_ratio", {"maximum": charger["hot_threshold_min_permille_vin"] / 1000}),
    ):
        resistance = sensor["nominal_resistance_by_temperature_c"][str(temp)]
        parameters = dict(upper_ohms=design["upper_ohms"], shunt_ohms=design["shunt_ohms"],
            isolation_ohms=design["isolation_ohms"], upper_tolerance=design["resistor_tolerance_percent"] / 100,
            shunt_tolerance=design["resistor_tolerance_percent"] / 100,
            isolation_tolerance=design["resistor_tolerance_percent"] / 100,
            ntc_min_ohms=resistance * (1 - budget), ntc_max_ohms=resistance * (1 + budget),
            input_min_v=charger["input_min_mv"] / 1000, input_max_v=charger["input_max_mv"] / 1000,
            maximum_input_leakage_a=design["assumed_ts_leakage_na"] / 1000000000)
        limits = {limit_name: bound}
        if label == "hot":
            limits.update(open_minimum_ratio={"minimum": charger["cold_threshold_max_permille_vin"] / 1000},
                          short_maximum_ratio={"maximum": charger["hot_threshold_min_permille_vin"] / 1000})
        checks.append(evaluate_requirement("battery.provisional-" + label,
            {"algorithm": "calculation", "stage": "design"},
            {"basis": basis, "calculation": "ratiometric_ntc_divider", "parameters": parameters, "limits": limits},
            None, {}, None))
    checks.append(evaluate_requirement("battery.conditional-voltage", {"algorithm": "range", "stage": "design"},
        {"basis": "TI T-variant EC versus linked Kjell pack; retail applicability and transients pending",
         "values": {"minimum_mv": charger["battery_regulation_min_mv"], "maximum_mv": charger["battery_regulation_max_mv"]},
         "limits": {"minimum_mv": {"minimum": cell["datasheet_pack"]["charge_voltage_min_mv"]},
                    "maximum_mv": {"maximum": cell["datasheet_pack"]["charge_voltage_max_mv"]}}}, None, {}, None))
    current = power.resistor_programming_window(factor_min=charger["iset_factor_min_a_ohm"],
        factor_max=charger["iset_factor_max_a_ohm"], resistor_ohms=design["iset_ohms"], tolerance=0.01, inverse=True)
    multiplier = charger["fast_charge_timer_multiplier"]
    timer = power.resistor_programming_window(factor_min=charger["tmr_factor_min_s_per_kohm"] * multiplier / 1000,
        factor_max=charger["tmr_factor_max_s_per_kohm"] * multiplier / 1000,
        resistor_ohms=design["tmr_ohms"], tolerance=0.01, inverse=False)
    checks.append(check("battery.programmed-current", "pass" if current["programmed_maximum"] * 1000 <= cell["datasheet_pack"]["standard_charge_current_ma"] else "fail",
        "Static ISET window versus pack standard current; actual charge current can be lower",
        minimum_ma=round(current["programmed_minimum"] * 1000), maximum_ma=round(current["programmed_maximum"] * 1000)))
    checks.append(check("battery.programmed-timer", "pass" if
        design["tmr_ohms"] * 0.99 > charger["tmr_resistor_min_ohms_exclusive"] and
        design["tmr_ohms"] * 1.01 < charger["tmr_resistor_max_ohms_exclusive"] else "fail",
        "Resistor lies inside TI programming range; NOT proof of full recharge",
        minimum_s=round(timer["programmed_minimum"]), maximum_s=round(timer["programmed_maximum"])))
    for identifier, detail in (
        ("source-applicability", "Current Kjell retail cell and linked pack specification equivalence pending"),
        ("guaranteed-temperature", "Provisional R/T and TS leakage assumptions are not source guarantees; do not approve from mathematical passes"),
        ("thermal-tracking", "Insulated cell-mounted sensor thermal coupling, lag, self-heating and cell/sensor mismatch unmeasured"),
        ("harness-current", "Protected-cell fit/retention, 24 AWG holder leads/contact losses, connector polarity and protection trip/recovery pending"),
        ("charge-completion", "Minimum timer remains shorter than full-capacity constant-current time at minimum programmed current; taper, input/system load and timer slowdown unresolved"),
        ("routing-assembly", "New circuit changes topology; previous native DRC, BOM/CPL and Gerbers do not qualify this revision"),
        ("prototype", "Battery-only modem USB, bursts, undervoltage, charging and sensor/harness fault tests pending"),
    ):
        checks.append(check("battery." + identifier, "incomplete", detail,
            stage="bench" if identifier in {"prototype", "thermal-tracking"} else "design"))
    result = report("tracker-battery-revision-screen", {"library_mode": "explicit_unlocked_working_copy_review",
        "files": {name: hash_file(path) for name, path in paths.items()}}, checks)
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
