# Validation status

Checked 2026-10-09 using the pinned compiler and dependencies, Python 3.13.14
and KiCad 10.0.6. This is a development board, not a manufacturing release.

- Locked, offline electrical checks and compilation passed.
- All nine project regression tests passed: library ownership, electrical rules, procurement
  coverage, assembly review gating, power topology, modem interface levels,
  Nordic clock/decoupling, physical pad mappings and RF macro identity.
- All 87 populated references have exact candidate selections, grouped into
  45 procurement identities. None has been approved for assembly. The assembly
  check intentionally fails with `REVIEW_REQUIRED`, not stale-lock errors.
- The six-layer physical build resolved the real footprints and produced a
  legal placed board while preserving the Nordic/Johanson RF hard macro.
  Placement has escape-channel/congestion warnings and is still provisional.
- Native KiCad loaded the board and exported an inspected SVG/PNG preview.
- Native DRC on the placed, unrouted board reports 307 unconnected items and
  one silkscreen-over-copper warning at the modem's pin-one marker. Other
  reported violation categories are absent; this does not imply route closure.

Generated files are under the ignored `build/` directory: `board.json`,
`placed.kicad_pcb`, `placement.json`, `assembly.json`, `placed-drc.json` and
`preview.svg`/`preview.png`. Normal builds recreate source and placement
artifacts; the native placed-board DRC and preview were additional checks.

Before ordering, finish routing and silkscreen cleanup, close native DRC and
unconnected items, qualify RF and battery/power behavior, review every BOM
selection and assembly rotation, and recheck live JLCPCB stock. See
[power design](power-design.md) and [component evidence](component-evidence.md).

## Component library migration

The 2026-10-09 migration moved 13 part/interface definitions, five custom
footprints and the modem converter into CopperLib. Only the application-specific
power-tree module remains local. Package aliases and footprint identities changed;
the before/after compiled pin contracts, connectivity, component values, power
states and placement/routing constraints were compared and are identical.
All five footprint files preserve their original geometry and metadata, with
line endings normalized. Assembly identities/digest and the dependency inventory
were refreshed without changing any JLCPCB offer or review flag.

The pinned project compiler passes ERC, compilation and all nine tests, including
physical footprint resolution and the preserved RF macro binding. The placed
PCB was rebuilt successfully with the migrated identities:
legal placement, HPWL 2614.3 mm, before the subsequent routing attempts below. Native KiCad DRC
again reports 307 unconnected items and the one inherited modem silkscreen
warning. CopperLib's eight new migration tests pass. Its full suite reports
133 passed, 18 skipped,
and two failures in unchanged TPS62130A assets: stored Windows CRLF bytes differ
from regenerated LF JSON bytes. Those unrelated assets were not changed here.

The project currently uses `replace github.com/andenore/CopperLib => ../CopperLib`.
Remote/CI builds need these library additions published and the exact supported
asset inventory to match the lock; prefer pinning that reviewed published commit
and removing the replacement. No commit, push or publication was performed.

## Routing attempts

The subsequent fanout strategy blocked on four package-access endpoints.
A bounded direct-area strategy connected all eight critical nets and 47 of
67 ordinary nets. Twenty ordinary nets and two deferred plane nets remain
incomplete. A separate KiCad 10.0.6 refill/save/DRC run on the best partial
board reports 34 unconnected items and one modem silkscreen warning. The
route is explicitly not fabrication-ready; no production Gerbers were generated.

The partial board and detailed/native reports are `build/direct-routed.kicad_pcb`,
`build/direct-route.json` and `build/direct-drc.json`. Clock routes, USB pair
geometry, RF stackup/matching and switched-power current paths still need
reference-layout qualification, in addition to closing all native opens and
reviewing assembly selections and CAM. See [routing attempts](routing-attempts.md)
for settings, failure diagnostics and the distinct fanout-attempt artifacts.

## Current power/clock implementation

The latest source passes locked offline ERC, compilation and all **15 project
tests**, including cardinal macro rotations, external-port fixtures, lost
immutable copper, changed pad bindings/footprints, clock/rail constraints and
the intentionally closed assembly review gate. Only the assembly source digest
was refreshed; offers, MPNs and all 87 `reviewed=false` flags were preserved.

The reusable CopperLib TPS63020 assets regenerate deterministically. Its 12
targeted macro/component tests pass. The current full CopperLib test invocation
reports 124 passed, 31 skipped and the same two pre-existing TPS62130A CRLF/LF
reproduction failures; those unrelated assets remain untouched.

Eight independent native regulator fixtures (both variants, all cardinal
rotations, terminated external ports) have zero violations and zero opens after
KiCad refill. This is isolated geometry evidence, not whole-board or converter
qualification. Native copper-layer previews were inspected.

The approved v0.4 compiler implementation distinguishes exact immutable local
width contracts from host rail rules, without changing fabrication minimums.
138 focused compiler tests pass. The tracker explicitly consumes the unpublished
editable sibling CopperScript checkout; reviewed publication/pinning remains
necessary for standalone remote reproducibility.

The full-board reroute now passes macro acceptance with the wide rail rules
retained. The current partial board is `build/power-clock-routed.kicad_pcb`.
Separate native refill/save/DRC reports **21 unconnected items and one inherited
modem silkscreen warning**, compared with 34 opens in the historical draft.
There are no native shorts, clearance or track-width errors, and no native
opens on VSYS, BAT, V3V8, GND, V3V3 or internal converter nets. The route connects
51 of 64 ordinary nets and 6 of 11 critical nets; clock/DEC3, modem USB and
remaining interface routes still fail the completion gate. No bounds were
weakened. Six-layer copper previews were inspected for gross layout, not CAM
qualification. See the
[scoped-width reroute](routing-attempts.md#scoped-width-compiler-implementation-and-reroute).
No production artwork, commit, publication or order was made.

## CAN-free source

CAN and its four dedicated components were removed at the user's request.
Locked offline ERC/compilation and all 16 project tests pass. Assembly and both
procurement representations cover exactly 83 references in 43 identities; every
selection remains unreviewed. PC4/PC5 are unused, and unchanged rail/clock/RF
contracts remain tested. The saved comparison board is
`build/no-can-routed.kicad_pcb`: 45/60 ordinary and 8/11 critical nets connect.
Separate native refill/save/DRC reports **22 unconnected items and two warnings**
(inherited modem silkscreen and new MODEM_EN dangling macro-port via), versus
21 opens and one warning before CAN removal. There are no native shorts,
clearance or track-width errors, and no main-rail or ground-plane opens.
USB pairs now connect, but other signals regressed; overall closure did not
improve. Clock/DEC3 routes remain rejected by unchanged length bounds.
Six-layer copper previews were inspected for gross layout only. The route and
assembly gates remain closed; no production Gerbers were generated. Previous
native results above describe historical CAN-equipped boards, not this source.
See [CAN removal](routing-attempts.md#can-removal-and-comparison-reroute).

## Finished routing candidate — 2026-10-10

The CAN-free source now has a finished native candidate,
`build/finished-routed.kicad_pcb`. Independent KiCad 10.0.6 refill/save/DRC in
`build/finished-native.json` reports **0 violations and 0 unconnected items**.
The earlier 21/22-open and escape-only boards above are historical, not current
closure evidence. CopperScript also checks the current source's physical
geometry, immutable macros, rail/clock bounds and placement. Source zones are
not considered filled by that check; actual zone connectivity is evidenced by
the native report, not a fabricated filled-zone model.

Clock lengths remain XC1 7.576589 mm, XC2 7.847249 mm and DEC3 1.960366 mm,
with zero clock vias. Late-contact full routing connected all 11 critical and
59/60 ordinary nets. Finer 0.025 mm local surface search closed the last two
3.3 V contacts at unchanged width/clearance. A separate bounded 300,000-state
USB 5 V repair connected the last ordinary net; native refill confirmed zero
opens. One exact disposable 0.14631 mm VSYS overhang was removed, retaining
its input. CopperLib's modem marker moved clear of pad 1 without changing any
of the 124 lands or courtyard. Final native checks include both repairs.

Current checks: 25 project tests, 60 detailed/local-critical compiler tests,
92 critical/macro compiler tests, 26 CLI tests, and 13 targeted CopperLib
component/TPS63020 tests pass. Locked offline ERC/compilation pass. The current
assembly source digest is
`b3418b67aba61362b2ec444ae8ba76053a12c68134ed22e075a4cc36be680b84`;
83/83 selections are exact, **0 reviewed**. No approvals were manufactured.

Six-layer Gerbers/drills, netlist, checksums, native board and placements were
exported only after native closure. Candidate BOM/CPL are separated from that
fabrication archive and explicitly unapproved. Export qualification remains
false: independent CAM, exact-variant/support/ESD review, RF/impedance, power
and charging thermals, live stock and supplier assembly preview are outstanding.
No commit, publication or order was made. See
[manufacturing review](manufacturing-review.md).
