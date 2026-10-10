# Routing and fabrication attempt — 2026-10-09

This is an inspection draft, not a production release. No production Gerbers
have been generated. The pinned compiler, locked CopperLib replacement, actual
footprints, six-layer JLCPCB profile and Nordic/Johanson hard macro were used.
Each attempt below records its source changes. Clearances and fabrication
rules were not waived. Earlier boards are historical when the source changes.

## Fanout-based attempts

The normal route options produced a legal placement and successful global
routing. All eight critical RF/USB nets connected geometrically; the Nordic
owner copper remained immutable. Package-access negotiation did not close:

| Reference / pad | Function | Net |
| --- | --- | --- |
| `U_NRF.34` | XC1 crystal terminal | `NRF_XC1` |
| `PWR/U_LOGIC.4` | VOUT_4 | `V3V3` |
| `PWR/U_LOGIC.5` | VOUT_5 | `V3V3` |
| `U_CC.12` | USB-C controller VDD | `V3V3` |

The first attempt was interrupted after repeated pattern searches and the
beginning of a placement repair showed the same blockers. A second, completed
attempt enabled maze fanout, 3 mm same-net plane contact radius and 1.5 mm
surface detours, with no package placement/pattern retries. It still reported
these four pads pending and prevented ordinary area routing from starting.
The XC1 analysis found 11 legal local candidates, all blocked by selected
escapes; this is a joint escape-assignment problem, not proof that the pad
has no geometrically legal exit.

Artifacts: `build/routed.kicad_pcb`, `build/route.json`, `build/drc.json`.
The completed route report has `routing_complete=false`, 0 ordinary nets
routed and 67 ordinary nets unrouted. Native KiCad zone refill and DRC report
109 unconnected items and 114 violations: 113 dangling fanout vias plus one
inherited modem silkscreen-over-copper warning. This is not a routed board.

## Direct routing attempt

A separate bounded direct-area strategy completed without the optional fanout
reservation controller. This did not disable ERC, physical constraints, macro
ownership or final native DRC. It used one candidate, a 0.5 mm grid, one pass,
30,000 search states, a 2x repair budget, constrained-pins-first and progressive
guides. Same-net plane contact radius was 3 mm and surface detour was 1.5 mm;
zone escape and local-ripup trials were disabled. A neutral ordering fallback
was selected. The routing pipeline finished in about 609 seconds.

All eight critical nets and 47 of 67 ordinary nets connected geometrically.
Twenty ordinary nets remain unrouted, with GND and V3V3 additionally awaiting
verified plane connectivity. The explicit-copper check reports 22 open nets
and route incompleteness. Both the router's native check and a separate KiCad
10.0.6 refill/save/DRC run report **34 unconnected items and one violation**:
the inherited modem pin-one silkscreen-over-copper warning. No clearance or
short-circuit violations were reported for this partial draft. The report has
`status=fail`, `routing_complete=false` and `fabrication_ready=false`.

Artifacts, kept separate from the fanout attempt:

- `build/direct-routed.kicad_pcb`: best partial board, saved after native refill.
- `build/direct-route.json`: routing metrics and per-net diagnostics.
- `build/direct-drc.json`: separate native DRC, including exact open endpoints.

Unrouted ordinary nets are `DEBUG_TX`, `GNSS_RX`, `GNSS_TX`, `MCU_MODEM_RX`,
`MCU_NRF_RX`, `MCU_NRF_TX`, `MODEM_EN`, `MODEM_STATUS_1V8`, `MODEM_UART_TX`,
`NRF_DEC3`, `NRF_RESET`, `PWR/BAT`, `PWR/BAT_NTC`, `PWR/LOGIC_FB`,
`PWR/MODEM_FB`, `SIM_IO`, `USB_C_CC1`, `USB_C_CC2`, `USB_C_VBUS_DET` and
`V3V8`. Diagnostics distinguish unreachable local endpoints from exhausted
search budgets; neither proves the connections are physically impossible.

XC1 connected in this strategy, confirming the earlier escape assignment was
strategy-dependent. Its final route is about 36.9 mm with three vias; XC2 is
about 20.0 mm with no vias. These are geometry results, not approved oscillator
layouts. Critical-net connectivity also does not establish RF/USB qualification:
the two USB pairs have about 1.259 mm skew, no configured skew limit, and the
critical review reports no coupled length. Review reference layouts and impose
appropriate clock, RF, USB and switched-power constraints before rerouting.

## Production gates

Do not export or order artwork from an incomplete route. Require zero native
opens and violations after refill, inspect every layer, and complete independent
CAM review. RF matching/stackup and converter current-path widths/reference
layout remain unqualified. All 83 retained exact assembly selections still require review;
they must not be bulk-marked approved to bypass the assembly gate.

The native manufacturing-file exporter explicitly does not provide an
independently qualified release. Do not label skipped-CAM exports as production
qualification. See [validation](validation.md), [power design](power-design.md)
and [component evidence](component-evidence.md).

## Regulator macros and short-clock pass — 2026-10-09

This section records the initial width-rule blocker. The following scoped-width
reroute supersedes it; earlier drafts remain preserved for comparison.

The two TPS63020 layouts now come from CopperLib's reusable
`packages/circuits/ti/tps63020-buck-boost` package. The nine-member always-on
macro binds the logic converter; the eleven-member enabled/series-feedback
macro binds the modem converter. They own paired power-pin contacts, switch
polygons, input/output capacitor copper, feedback/sense, local ground and
explicit external ports. They remain **unqualified authored TI-reference
adaptations**, with `production_publishable=false`. Neither resistor values
nor the electrical topology were changed.

Both variants passed isolated CopperScript physical acceptance and native
KiCad 10.0.6 refill/save/DRC at 0/90/180/270 degrees: **zero violations and
zero opens in all eight fixtures**. Each fixture includes terminated external
VIN/VOUT/EN port connections and the host ground planes. These fixtures remove
host circuitry and host per-net routing profiles intentionally; they are not
full-board acceptance. `make power-probes` repeats them. Reports and boards are
under `build/power-probes/`. F.Cu/In2.Cu/B.Cu copper was rendered and visually
inspected. Current, thermal, EMI, transient, stackup and assembly qualification
remain open.

The logic anchor moved from (45,61) to (49,63) mm to clear the CAN connector
and separate the power macros. Crystal/load/DEC3 poses were adjusted against
the actual locked courtyards and preserved RF private copper. The crystal nets
now require F.Cu-only trees, no vias and at most 8 mm total conductor each;
DEC3 requires F.Cu, no vias and at most 2 mm. These numerical bounds are authored
short-route targets, not Nordic numerical maxima. The initial 1.5 mm DEC3
placement target conflicted with the exact courtyards; the final terminal-to-
terminal placement is about 1.85 mm, bounded at 2 mm with the routed-length
limit retained. None of these new clock routes has yet been generated/verified.

The bounded direct route was rerun with all three macro scenes and the earlier
direct strategy's budgets. Fixed courtyard conflicts were resolved. The final
attempt advanced past placement but **stopped during hard-macro acceptance**:
the pinned compiler applies the host's 0.8 mm `PWR/VSYS` and `V3V8` net-wide
width minimum to local 0.2 mm VINA, EN and output-sense branches, plus paired
0.24 mm package entries that exceed its 1 mm breakout region. Those branches
are not the main load-current conductors. It reports 23 `DRC-TRACK-WIDTH`
findings, so no new full-board PCB/report or Gerber release was produced.

The 0.8 mm distribution rule and 0.24 mm/1 mm breakout rule have **not** been
weakened or bypassed. A compiler enhancement needs explicit, validated local
conductor contracts for immutable macro-owned branches while preserving the
host-routing minimum and fabrication minimum. Approval to make that CopperScript
change has been requested. Until it is implemented and tested, the older
`build/direct-routed.kicad_pcb` remains a historical partial draft, not a route
of the current source. All 87 assembly selections remain unreviewed; no
production Gerbers were generated.

## Scoped-width compiler implementation and reroute

The approved CopperScript implementation adds v0.4 explicit width contracts
for indexed asset track rows, expanded into typed local segment contracts.
Only exact validated, immutable owner occurrences can use them. The fabrication
minimum remains mandatory; host copper and undeclared owner tracks keep their
net-wide rules. Purposes/evidence and applied widths are recorded as
`DRC-MACRO-WIDTH-CONTRACT` informational findings, bound into geometry/signoff
digests. This is not a clearance, layer, route-length, via or connectivity waiver.

Both CopperLib assets now declare the individual 0.24 mm DSJ entries and
0.2 mm VINA/EN/output-sense branches. The 0.8 mm power lead-ins and host rail
constraints are unchanged. The geometry itself did not change. Assets remain
unqualified and current/thermal capacity unresolved.

The tracker explicitly uses editable `../CopperScript` in `pyproject.toml` and
`uv.lock` for this unpublished implementation, based on compiler commit
`c777fda1c70fd1f31bd9683fdb22b773d5a88374`. It also retains the explicit CopperLib
replacement. No installed-package patching, compiler copying, commit or
publication was performed. A reviewed published revision and refreshed locks
are needed before standalone reproducible remote builds.

138 focused compiler tests passed across macros, physical IR/DRC, breakout,
critical routing, KiCad export and physical flow. They cover legacy rejection,
polyline/rotation binding, missing owner copper, malformed contracts, duplicate
host occurrences, undeclared owner tracks, fabrication minimums, fingerprint
changes and preservation of non-width limits. All 15 tracker tests pass, including
macro acceptance with its actual 0.8 mm host rules. Twelve targeted CopperLib
tests pass; its full suite reports 124 passed, 31 skipped and the same two
unrelated TPS62130A CRLF/LF reproduction failures. All eight independent native
regulator fixtures pass again with zero violations and zero opens.

The full-board reroute uses the same bounded direct budgets described above,
now with all three macro scenes. It passes placement and macro acceptance.
The completed attempt connects **51 of 64 ordinary nets and 6 of 11 critical
nets**. Its status remains failed/incomplete, not fabrication-ready. Current
artifacts are `build/power-clock-routed.kicad_pcb`,
`build/power-clock-route.json` and `build/power-clock-drc.json`; the earlier
direct-route artifacts are preserved as historical drafts.

Separate KiCad 10.0.6 refill/save/DRC reports **21 unconnected items across 18
nets and one inherited modem silkscreen-over-copper warning**, down from 34
unconnected items in the earlier draft. There are no native shorts, clearance
or track-width errors. VSYS, BAT, V3V8, GND, V3V3 and both converters' internal
nets have no native opens. The router's two deferred-plane flags do not mean
those filled planes are open; its overall completion flag remains false because
other nets are incomplete. CopperScript records 47 informational local-width
contract applications and no track-width errors, with host rail rules unchanged.

The rejected clock candidates measured 9.917615 mm for NRF_XC1 (8 mm limit),
8.231077 mm for NRF_XC2 (8 mm limit), and 2.168528 mm for NRF_DEC3 (2 mm limit).
None of that rejected copper was retained. These bounded-search failures do
not establish that compliant routes are impossible. The modem USB pair also
failed: its coarse guide had no segments to offset, and joint search found no
candidate. The MCU USB pair routed, but neither USB nor RF impedance is qualified
without the intended manufacturing stackup and reference-layout review.

The 13 unrouted ordinary nets are I2C_SDA, DEBUG_TX, PWR/ILIM, MCU_MODEM_RX,
PWR/BAT_NTC, ACCEL_INT, MODEM_UART_RX, MODEM_UART_TX, USB_C_CC1, SIM_IO,
GNSS_TX, GNSS_RX and GNSS_TIMEPULSE. Next routing work should address the
Nordic crystal/load/DEC3 placement and short routes jointly, then modem USB and
remaining interface breakouts. Clock bounds and power-width rules must remain
enforced. A six-layer native copper contact sheet was visually checked for gross
layout only; it is not CAM or hardware qualification. All 87 assembly selections
remain unreviewed, and power/RF/current/thermal qualification remains open.
No production Gerbers, commit, publication or order was made.

## CAN removal and comparison reroute

At the user's request, the project removes U_CAN (TCAN334GDR), J_CAN,
R_CAN_TERM (120 ohm) and C_CAN (100 nF), their CAN_TX/CAN_RX/CAN_H/CAN_L
nets, supply/ground bindings, fixed connector placement, library imports and
FDCAN1 configuration. MCU PC4/PC5 are now unused; no other signals were
reassigned. Reusable CopperLib CAN definitions remain available. The six-layer
outline, RF and converter macros, rail widths and clock bounds are unchanged.

Assembly/procurement records contain 83 exact unreviewed references in 43
identities, with all retained offers and review flags unchanged. The electrical
assembly digest was refreshed. Locked offline ERC/compilation and all 16 project
tests pass, including a new no-CAN check and readable candidate-BOM coverage.

A bounded comparison reroute uses the scoped-width attempt's exact settings
and all three macro scenes, with outputs `build/no-can-routed.kicad_pcb`,
`build/no-can-route.json` and a separate native report `build/no-can-drc.json`.
It completed in about 733 seconds. The preferred ordering was retained because
neutral fallback was worse: 15 versus 18 failed ordinary nets. **45 of 60
ordinary nets and 8 of 11 critical nets** connect. The two deferred-plane flags
remain, but separate native refill reports no GND or V3V3 opens. Main rails and
internal converter nets also have no native opens. Status remains failed,
`routing_complete=false` and `fabrication_ready=false`.

Native KiCad 10.0.6 refill/save/DRC reports **22 unconnected items across 18 nets
and two warnings**: the inherited modem pin-one silkscreen issue and a new
MODEM_EN dangling-via warning at (62.2,45.0) mm. That via is the immutable
enabled macro's EN port, not disposable fanout copper; its host connection or
a reviewed macro adaptation needs investigation. There are no native shorts,
clearance or track-width errors. CopperScript records 47 informational scoped
width applications and no width errors. Six native copper layers were rendered
and inspected for gross layout, not CAM or hardware qualification.

Compared with the 21-open CAN-equipped draft, DEBUG_TX, GNSS_RX, GNSS_TX,
I2C_SDA, MCU_MODEM_RX, PWR/BAT_NTC and both modem USB nets closed. New open
nets are MODEM_PWRKEY, MODEM_STATUS_1V8, NRF_RESET, NRF_SWDCLK, PWR/ISET,
SIM_CLK, SIM_RST and USB_C_CURRENT_1. Thus removing CAN frees parts and routing
space, but this automatic placement/reroute did **not** improve overall native
closure. Both historical boards are retained; the older board is not a valid
route of the current source.

The unchanged crystal and DEC3 candidates still exceed their 8/8/2 mm limits.
Both USB pairs now route geometrically: MCU skew is 0.629607 mm, modem skew
1.259213 mm; the modem pair uses four signal vias. No skew limit is configured,
and impedance, via transitions and return paths remain unqualified. Connectivity
must not be presented as USB signoff.

The 15 failed ordinary nets are NRF_RESET, USB_C_CURRENT_1, NRF_SWDCLK,
PWR/ISET, ACCEL_INT, PWR/ILIM, MODEM_UART_RX, MODEM_UART_TX,
MODEM_STATUS_1V8, USB_C_CC1, MODEM_PWRKEY, SIM_RST, SIM_CLK, SIM_IO and
GNSS_TIMEPULSE. Next work needs targeted clock placement and terminal-access
improvements, plus EN-port native closure, rather than weaker rules. No
production Gerbers, commit, publication or order was made.

## Targeted open-connection repairs — 2026-10-10

The CAN-free baseline above had 22 native open items on 18 nets. Investigation
distinguished over-length Nordic candidates, long support/control branches,
ordinary pins blocked by previously accepted copper, and the separate EN-port
dangling-via warning. A routing failure is not proof that a legal path is
impossible.

The enabled TPS63020 asset in CopperLib now ends its EN port at an owned F.Cu
lead-in rather than directly at the In2/F.Cu transition via. Both via layers
have owned connections, and the host enters F.Cu. Enabled asset digest is
`153e00613383203ac89fe978ad1cde20a69431cd05d12588ded861057a7f3734`.
The always-on asset and all switching/feedback/current paths are unchanged.
Both variants pass separate native refill/DRC with zero violations and opens
at 0/90/180/270 degrees. This is geometry evidence, not converter qualification.

Reset pull-up, charger ILIM/ISET resistors, USB-current pull-ups, and modem
translation/PWRKEY support now have compact, explicit legal source placements.
No parts or nets were removed. The horizontal DEC3 capacitor leaves more room
for HFXO escapes. Crystal/load/VDD2 placements changed jointly; source priority
is DEC3 (155), XC2 (151), XC1 (150). All original 5/2 mm placement distances,
8/8/2 mm routed-length limits, 0.18 mm surface-only/no-via clock rules, rail
widths, fabrication rules and RF macro protections remain enforced.

CopperScript now refines bounded repairs for over-length candidates as well
as no-path results. Length-bounded no-via critical repairs use the existing
0.1 mm resolution floor, geometric layer/direction costs and an independent
local search preference, without modifying the recorded global guide. Legal
owned candidate smoothing occurs before length rejection, against a private
snapshot of all committed copper. Snapshot construction avoids duplicating
the immutable macro prefix; tests cover preserved obstacles, unchanged limits,
missing-guide rejection and non-macro model errors.

The reproducible `scripts/probe_clock_routes.py` runs the three ordered jobs
with real global guides and every immutable macro. XC1 is 7.576589 mm, XC2
7.847249 mm, and DEC3 1.960366 mm, all connected without vias. It intentionally
does not route the other interfaces and is not whole-board closure evidence.
Earlier candidate probes that exceeded a bound or blocked the second crystal
net were rejected, not accepted by increasing limits.

A three-pass direct experiment (50,000 states, soft rip-up) was interrupted
after persistent ordinary-pin failures; it used superseded clock poses and
did not produce a completed/native-verified board. It is not a new signoff
result. The subsequent escape-first attempt uses current source, two passes,
30,000 states, 2x repair budget, maze fanout, zero package placement/pattern
retries, 3 mm plane contact radius and 1.5 mm stitching detour. Its initial
ordinary-package stage reserves all 86 exits with zero pending pads. Final
critical, routing and native checks still determine full-board closure.

That zero-pattern-retry attempt completes all 11 critical nets and passes
critical/contact geometry DRC, but three V3V3 contacts remain pending:
U_CC.12 (VDD), U_MODEM_LEVEL.10 (DIR1 tied high) and U_MODEM_STATUS.7
(VCCA). It therefore correctly blocks ordinary area routing. Its 73 native
open items and 88 warnings describe an escape-only draft, not a regression of
the 22-open routed baseline. Artifacts are `build/escape-first-route.json` and
`build/escape-first-routed.kicad_pcb`. A subsequent bounded attempt enables
both existing pattern-negotiation strategies, including plane-first obstacles;
it does not waive the three contacts or remove their supply connections.

Native refill/DRC of `build/clock-source-probe.kicad_pcb` independently finds
no open items on XC1, XC2 or DEC3. Its 117 other opens are intentional unrouted
interfaces; its warnings are an unconsumed EN lead-in and inherited modem silk.
The full-board and assembly gates remain closed. Current source passes locked
offline ERC/compilation and 18 project tests. CopperScript's 60 detailed/local
routing tests and 92 critical/macro tests pass; four CopperLib TPS63020 asset
tests pass. All 83 procurement selections remain exact and unreviewed; only the
assembly source digest changed. No production artwork or external publication
was made.

### Final closure and review export

The two negotiation strategies also failed preflight: plane-first lost
U_MODEM_LEVEL.4/.9 signal exits; critical-first retained three pending V3V3
contacts. A joint V3V3/signal allocation diagnostic found 105 exits and zero
pending contacts, but no source zone-reservation change was needed in the
accepted board. The alternative late-contact full run (`late-contact-route.json`)
connected all 11 critical and 59/60 ordinary nets. Native DRC improved from
22 to 8 open items: two V3V3 contacts and six items on V5. This result remained
failed and no artwork was exported from it.

Keeping accepted copper fixed, plane stitching at 0.1 mm candidate spacing
and a 0.025 mm/50,000-state local maze closed U_CC.12 and U_MODEM_LEVEL.10.
Native refill confirmed six remaining opens, all V5. A 0.25 mm/100,000-state
V5 diagnostic exhausted its budget; the accepted 0.5 mm/300,000-state geometric
search connected V5 with 130.111486 mm of new copper. These diagnostics used
empty connected search preferences, not proof of a new global-routing pass;
acceptance is based on preserved source geometry/contracts and the independent
whole-board native result. `v5-long-native.json` confirmed zero opens.

The reusable modem footprint's authored pin-one marker was moved clear of
its mask opening; all land geometry and courtyard remain unchanged. A native
report identified an ordinary 0.14631 mm VSYS stub. Cleanup removed only that
exact non-macro track and retained its source board. The finishing script
rejects stale source poses, changed pad/net/size/angle/kind and missing
components, checks macro ownership and physical constraints, and still
requires native refill/DRC. `finished-native.json` confirms **zero violations
and zero unconnected items**. The ignored native informational checks were not
changed; shorts, clearance, widths and connectivity were not waived.

The native-clean six-layer export is `build/fabrication-review-20261010`.
Its manifest explicitly has `qualified_release=false`; independent CAM and
live stock are not checked. Separate `assembly-review-20261010` contains
candidate BOM/CPL with 43 grouped identities and 83 placements; all 83 original
review flags remain false. No production approval or external publication was
made. See [manufacturing review](manufacturing-review.md) for artifacts and
reproduction, including the checkpoint requirement.
