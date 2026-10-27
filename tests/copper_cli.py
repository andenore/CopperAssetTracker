"""Run the CopperScript CLI on this board and read its public JSON output.

Tests assert board facts on what `copper compile`, `copper check`, `copper
query` and `copper assembly` print, never on compiler internals. COPPER
overrides the command (for example `COPPER=copper` or a Rust build);
COPPERSCRIPT_SOURCE points the default `python -m copperscript` at a source
checkout. Every call is locked and offline: run `make fetch` first.
"""
import atexit
import functools
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "board.copper"
LOCKED = ("--locked", "--offline")
COMMAND = shlex.split(os.environ["COPPER"]) if os.environ.get("COPPER") else [sys.executable, "-m", "copperscript"]


class CopperError(Exception):
    """The CLI rejected the board; the message is its stderr."""


def _environment():
    environment = {**os.environ, "PYTHONUTF8": "1"}
    source = os.environ.get("COPPERSCRIPT_SOURCE")
    if source:
        environment["PYTHONPATH"] = os.pathsep.join(filter(None, (source, os.environ.get("PYTHONPATH"))))
    return environment


@functools.cache
def _scratch() -> Path:
    directory = Path(tempfile.mkdtemp(prefix="tracker-tests-"))
    atexit.register(shutil.rmtree, directory, True)
    return directory


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([*COMMAND, *args], cwd=ROOT, env=_environment(),
                          capture_output=True, text=True, encoding="utf-8", check=False)


def _json(result: subprocess.CompletedProcess):
    try:
        return json.loads(result.stdout)
    except ValueError:
        raise CopperError(result.stderr.strip() or result.stdout.strip()) from None


def _written(result: subprocess.CompletedProcess, output: Path) -> dict:
    if not output.exists():
        raise CopperError(result.stderr.strip() or result.stdout.strip())
    return json.loads(output.read_text(encoding="utf-8"))


@functools.cache
def _compile() -> str:
    output = _scratch() / "board.json"
    result = run("compile", str(BOARD), *LOCKED, "--no-check", "-o", str(output))
    if result.returncode:
        raise CopperError(result.stderr.strip())
    return output.read_text(encoding="utf-8")


def compile_board() -> dict:
    """`copper compile` JSON IR of the board."""
    return json.loads(_compile())


@functools.cache
def _check() -> str:
    return json.dumps(_json(run("check", str(BOARD), *LOCKED, "--json", "--pins", "off")))


def check() -> dict:
    """`copper check --json` document; unmarked pins are not reported."""
    return json.loads(_check())


@functools.cache
def _query(*args: str) -> str:
    return json.dumps(_json(run("query", str(BOARD), *args, *LOCKED, "--json")))


def query(*args: str) -> dict:
    return json.loads(_query(*args))


def endpoint(text: str) -> tuple[str, str]:
    component, _, pin = text.rpartition(".")
    return component, pin


def net(name: str) -> set[tuple[str, str]]:
    """Flattened (component, pin) endpoints of one net."""
    return {endpoint(member["endpoint"]) for member in query("net", name)["net"]["members"]}


def net_names() -> set[str]:
    return {item["net"] for item in query("nets")["nets"]}


def components() -> dict[str, str]:
    """Flattened component reference -> part."""
    return {item["ref"]: item["part"] for item in query("components")["components"]}


def part(design: dict, name: str) -> dict:
    """A compiled part with its pins keyed by name."""
    (item,) = [item for item in design["parts"] if item["name"] == name]
    return {**item, "pins": {pin["name"]: pin for pin in item["pins"]}}


@functools.cache
def _snapshot() -> str:
    output = _scratch() / "snapshot.lock"
    output.unlink(missing_ok=True)
    return json.dumps(_written(run("assembly", "snapshot", str(BOARD), *LOCKED, "-o", str(output)), output))


def assembly_snapshot() -> dict:
    """`copper assembly snapshot`: the selections a fresh lock would need."""
    return json.loads(_snapshot())


@functools.cache
def _assembly_check(lock: Path) -> str:
    output = _scratch() / "assembly.json"
    output.unlink(missing_ok=True)
    return json.dumps(_written(run("assembly", "check", str(BOARD), *LOCKED, "--lock", str(lock),
                                   "--report", str(output)), output))


def assembly_check(lock: Path = ROOT / "assembly.lock") -> dict:
    """`copper assembly check` report for a lock."""
    return json.loads(_assembly_check(lock))


@functools.cache
def _audit() -> str:
    return json.dumps(_json(run("audit-footprints", str(BOARD), *LOCKED, "--json")))


def audit_footprints() -> dict:
    """`copper audit-footprints --json`: each selected footprint resolves
    and its numbered pads equal its part's pin numbers."""
    return json.loads(_audit())


def constraints(kind: str) -> list[dict]:
    return [item for item in compile_board()["constraints"] if item["kind"] == kind]


def routing_rules() -> dict[str, dict]:
    """Routing constraint parameters by target net."""
    return {target: item["parameters"] for item in constraints("routing") for target in item["targets"]}


def fixed_placements() -> dict[str, dict]:
    """Fixed placement parameters by target reference."""
    return {target: item["parameters"] for item in constraints("fixed_placement") for target in item["targets"]}


def nanometres(quantity: dict) -> int:
    """A length quantity's base value (metres) in integer nanometres."""
    from decimal import Decimal
    value = Decimal(quantity["base_value"]) * 1_000_000_000
    assert value == value.to_integral_value(), quantity
    return int(value)
