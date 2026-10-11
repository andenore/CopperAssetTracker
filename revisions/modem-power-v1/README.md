# Combined modem-power and battery routing revision

Uses the battery-v1 charger, hardware thermistor divider and timer revision,
plus CopperLib's reusable SIM7670G modem/bypass module. All four local ceramic
feeds have explicit pin-associated decoupling intent and 3 mm pad-relative
placement bounds. These are authored bounds, not manufacturer maxima. Ground
vias remain permitted; the supply feed should reach the consuming pad first.

The reserved In2.Cu power corridor is nominally 6 mm wide and has a 2 mm minimum
fill width. Native refill exposed disconnected fragments around through-via
clearance fields, so a wider unreserved same-rail region lets this load fill
pass around them without relaxing the reserved core or any keepout. Distinct
priorities avoid ambiguous overlapping native zone rules. In1.Cu supplies the
adjacent ground reference. The new reusable converter asset widens its output
lobe/tap and supplies four parallel off-pad 600/300 um through vias. It keeps
the switching, chip-entry, quiet sense and ground-return topology unchanged.
Pad entries, current sharing, plating, voltage drop and transients still need
qualification; a source zone's minimum-width setting is not a filled-current
path proof. Do not widen every low-current branch or count nominal MLCC values
as effective capacitance.

A low-current unreserved In2.Cu/In3.Cu spur feeds the opposite-edge USB-VBUS
detection pad. Its minimum fill width is 200 um, not the 2 mm VBAT load-path
rule. Its lower tie reaches the existing output-tap through vias below the
accelerometer's 3.3 V contacts. The second layer bypasses a signal-cut fragment;
the tie location avoids isolating those contacts from the logic plane. Native
refill must prove continuity of both supplies, not only the modem net. Adjacent
signal coupling and its effect on USB geometry still require simulation/review.

The cellular connector moves to the short lower-west launch so its F.Cu feed
does not cross the new bypass feeds. The status translator and its two local
capacitors move down together; three USB-C detection-divider resistors move
away from the enlarged converter tap. Actual courtyards remain binding.
The reservoir moves above the new bank; its authored component-origin bound
changes from 5 mm to 7 mm. Its unchanged Samsung 100 uF ceramic is **not** proven
to supply the reference's 100 uF effective reservoir: Samsung's retrieved
product sheet has no bias graph ([manufacturer product data](https://weblib.samsungsem.com/mlcc/mlcc-ec-data-sheet.do?partNumber=CL32A107MQVNNN)). ESR, actual bias/temperature capacitance,
low-battery burst and USB-detect margin remain unresolved.

Source basis: SIM7672X Hardware Design V1.01 p26 Figure 6, explicitly accepted
by the user as applicable. Reusable evidence and qualification boundaries are
in CopperLib. No vendor-confirmed equivalence or hardware approval is claimed.
Supplier candidates remain unapproved and stock needs checking at order time.

Build into a new directory (working-copy review, not locked release):

```powershell
uv run --project ../CopperScript python scripts/build_battery_revision.py --modem-power --library-review-root ../CopperLib --kicad-footprint-root .copper-cache/pkg/0c22bbbc033f71e79d6d --output build/new-power-review
Set-Location build/new-power-review
$nativeEvidence = Join-Path (Get-Location).Path 'native-new'
uv run --project ../../../CopperScript copper route-board board.copper --offline --layers 6 --fab-profile jlcpcb-six-layer --hard-macro nrf-antenna-macro.json --hard-macro logic-power-macro.json --hard-macro modem-power-macro.json --routing-profile balanced --pitch-mm 0.5 --fanout-maze --soft-ripup --constrained-pins-first --progressive-guides --plane-contact-radius-mm 3 --plane-stitch-detour-mm 1.5 --verify-plane-fill "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" --native-evidence-directory $nativeEvidence --report route-new.json -o routed-new.kicad_pcb --progress
```

The second command is the replacement shared workflow, not a reproduction of
the old pose-frozen helper's route. Use a new review directory and current
CopperScript environment; it deliberately remains an unlocked working-copy
review. It places/routes current source, never copies historical ordinary
copper, and requires independent native refill/DRC. Earlier 83-part
fabrication archives are preserved and do not describe this 91-part revision.
The default composition step no longer requires a historical placement file:
it writes source, electrical IR, candidate assembly selections and input hashes.
Its record explicitly says placement has not run. The shared command performs
placement/routing and native verification next. An optional `--pose-seed` is
retained only for exact pinned historical placement reproduction.

The current CopperScript adapter resolves native-evidence paths before changing
the subprocess working directory, so relative paths are now supported. The
absolute form above also works with older checkouts. Keep each attempt's
evidence directory distinct; existing evidence is never overwritten. A
successful routing pass still needs a successful native refill.

Local plane access also exposed two distinct issues. CopperScript now honors
declared neckdown widths in cheap surface paths and the local via-search maze,
with exact rechecks of emitted pieces. Separately, this board's default-width
accelerometer power escape was boxed in by neighboring I2C clock copper. The
historical repair workflow reserved that supply contact first, then rerouted
the ordinary I2C clock net using shared guarded algorithms. That project-local
entry point is retired; new repairs belong in CopperScript's shared workflow.
No pad, clearance, width or via-in-pad permission is waived. Every resulting
candidate still requires independent native refill/DRC.

## Initial source-only attempt, 2026-10-11

The 91-part revision was rebuilt without a historical placement seed
into `build/latest-power-review-20261011/`. Its generated source hash matches
the revision recorded below. The complete standard `balanced` flow exported
`routed-rerun.kicad_pcb` and `route-rerun.json`; all 61 ordinary nets and both
USB pairs routed, with 76 package exits retained. Native KiCad 10.0.6 refill
still reports **two opens, on V3V3 and V3V8**, zero other violations and zero
isolated copper islands. The report is correctly marked failed/incomplete.

Eight native repair candidates reduced the opens but introduced four dangling
via warnings and were rejected. This is a bounded-search result, not a proof
of infeasibility. The build folder contains every candidate's native evidence,
the retained filled board, a read-only source/macro/modem-bypass audit, SVG
views, input records and the remaining shared-tool investigation items.
All four modem supply bypass feeds still pass their via-free F.Cu chain checks.
The Tracker regression suite passed 55 tests without skips. Root source and
release locks are unchanged; no manufacturing approval is implied.

## Latest verified source-only checkpoint, 2026-10-11

The later fresh source-only v5 run is now natively closed without that historical
repair checkpoint: `build/latest-power-review-20261011/route-closure-v5.json`
reports CLI exit 0 and routing complete, all 61 ordinary nets and both USB pairs
connected, zero native opens, non-library violations and islands. Its retained
filled PCB is `native-closure-v5/verification-003/CopperAssetTracker.kicad_pcb`
inside that build folder. `closure-v5-checkpoint.json` independently confirms
source/macro/required-array ownership, legal placement, all four via-free F.Cu
modem bypass feeds, and zero native DRC violations/opens. Counts: 91 components,
six layers, 921 tracks and 314 vias. Exact commands/hashes and native layer
SVG/PNG views are retained alongside it. The unchanged locked 83-part benchmark
also passes with zero native opens, non-library violations and islands. The
full compiler inventory is verified with exact failed-case replay of two
initial offline-cache misses; original and replay test reports are retained.
`closure-v5-result.json` and `compiler-source-v5.json` bind the exact result,
commands, frozen compiler and output hashes. This remains an unlocked review,
not a production-approved release.

The main [project README](../../README.md) now illustrates this checkpoint with
native placement and routed-layer exports and source-bound IR excerpts.

## Historical verified routed checkpoint

The following records the earlier result. Its v15 PCB and v13 source
directories were not present in the local checkout when the fresh run above
was performed; use actual retained artifacts and current reports for review.

`build/power-v2-20261010-route-v15/routed.kicad_pcb` is the completed 91-part
six-layer routing review. Its isolated source is in
`build/power-v2-20261010-v13/`; root source/locks and earlier 83-part packages
are unchanged. Native refill and an independent read-only DRC each have
**zero violations and zero unconnected items**. The strict source/macro guard
and all four direct surface-chain checks pass. Physical readback: 1,146 tracks,
371 vias. This remains an unlocked, unqualified review, not production approval.

| Local capacitor | Consuming VBAT pad | F.Cu chain length, rounded |
| --- | --- | --- |
| 10 pF | 55 | 2,550 um |
| 33 nF | 55 | 2,011 um |
| 100 nF | 56 | 2,219 um |
| 1 uF | 57 | 2,763 um |

All four chains use zero vias; ground vias remain allowed. Actual native DC
connectivity includes all three VBAT contacts and both filled supply rails.
Width/current capacity, ground-return impedance and transient behavior are
separate unresolved engineering checks.

The sibling `final-routing-checkpoint.json` binds exact PCB/source/lock/macro/build
and algorithm hashes. Native top/power layer views are `routing-top.svg` and
`routing-power.svg` beside that report. Never substitute those review results
for the older manufacturing archives or reuse them after an input changes.

Regression scope: 106 focused CopperScript routing tests passed; CopperLib
144 passed with 31 optional skips; Tracker 64 passed with 32 passing subtests.
Effective reservoir capacitance/ESR, battery/charger evidence,
RF/USB analysis, prototype measurements and changed BOM/CPL/release inputs
still gate fabrication-package replacement.
