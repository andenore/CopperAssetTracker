"""Tracker source composition for read-only shared native checkpoint checks.

No routing, repair or selected-net algorithms live here. Use a current reviewed
CopperScript checkout for these tools; this does not upgrade the release locks.
"""
from pathlib import Path

from pcbir.footprints import FootprintResolver
from pcbir.hard_macros import apply_hard_macro_scene
from pcbir.loader import load_design
from pcbir.native_checkpoint import read_front_native_checkpoint
from pcbir.physicalize import PrototypePhysicalOptions, resolved_physicalize

ROOT = Path(__file__).resolve().parents[1]


def posed_source(pcb, *, with_copper=False, project_root=ROOT, locked=True):
    project_root = Path(project_root).resolve()
    design = load_design(project_root / "board.copper", locked=locked, offline=True)
    board = resolved_physicalize(design,
        FootprintResolver(base_directory=project_root, locked=locked, offline=True),
        PrototypePhysicalOptions(copper_layers=6, fabrication_profile="jlcpcb-six-layer"))
    # Retained historical candidates may still use external scene bindings.
    if not board.hard_macros:
        for scene in ("nrf-antenna-macro.json", "logic-power-macro.json", "modem-power-macro.json"):
            board = apply_hard_macro_scene(board, project_root / scene, locked=locked, offline=True)
    return read_front_native_checkpoint(board, pcb, include_copper=with_copper)


def current_candidate(path, **source_options):
    return posed_source(path, with_copper=True, **source_options)
