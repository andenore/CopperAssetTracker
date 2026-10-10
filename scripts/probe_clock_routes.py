"""Reproduce the ordered Nordic clock probe, not whole-board signoff.

Current fixed source poses override the supplied draft. Other components keep
their historical poses, but no historical ordinary copper is imported. Real
global guides and all immutable macros remain; only the three clock jobs run.
"""
import argparse
from dataclasses import replace
from pathlib import Path

from pcbir.backends.kicad_pcb import KiCadPcbBackend
from pcbir.backends.kicad_project import write_kicad_project
from pcbir.critical import route_critical_nets
from pcbir.physical import RouteKind
from pcbir.routing import route_global

from probe_open_routes import ROOT, posed_source

CLOCKS = frozenset({"NRF_XC1", "NRF_XC2", "NRF_DEC3"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pcb", type=Path, default=ROOT / "build/no-can-routed.kicad_pcb")
    parser.add_argument("--output", type=Path, default=ROOT / "build/clock-probe")
    args = parser.parse_args()
    source = posed_source(args.pcb)
    board = replace(source, net_routing_rules=tuple(
        replace(r, kind=RouteKind.GENERAL) if r.net not in CLOCKS else r
        for r in source.net_routing_rules))
    guides = route_global(board)
    result = route_critical_nets(board, guides, on_progress=lambda *a: print(a, flush=True))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".json").write_text(result.to_json())
    routed = replace(result.board, net_routing_rules=source.net_routing_rules)
    write_kicad_project(KiCadPcbBackend().generate(routed), args.output.with_suffix(".kicad_pcb"))
    assert {n for r in result.nets for n in r.nets} == CLOCKS
    assert all(r.connected and not r.via_count for r in result.nets), result.nets
    print("Ordered clock geometry passes; other nets are intentionally unrouted; not fabrication signoff.")


if __name__ == "__main__":
    main()
