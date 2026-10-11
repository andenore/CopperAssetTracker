# Prototype release checklist

This is a separate experimental-build decision, not production qualification.
Keep `qualified_release=false`; do not invent bench results to unblock a first
prototype. No purchase or supplier upload is authorized by this checklist.

## Before committing to fabrication

- [x] Confirm existing review files have zero native violations/open items and
  83 approved exact BOM selections. CPL and live stock are not approved.
- [x] Re-read and visually inspect SIM7672X V1.01 pp26, 58-60 and TPS63020
  SLVS916I pp6, 23. The SIMCom guide applies only under the user's design assumption.
- [x] Correct the cellular connector placement/orientation and reroute CELL_RF
  below the guide's 20 mm trace limit; preserve all other copper and selections.
- [x] Refill/check the new native candidate, verify source poses/pad nets/macros,
  compare the native copper delta and refresh versioned Gerber/BOM/CPL review files.
- [ ] Review the SIMCom recommended local VBAT capacitor bank, at least 2 mm
  supply distribution, optional supply filtering/surge protection and antenna
  matching/ESD strategy. A routed 100 uF MLCC alone is not this review.
- [ ] Review LTE/GNSS/BLE feed impedance, matching/antenna adaptations and USB
  reference transitions on JLC06161H-3313; do not relabel formula screens as solvers.
- [x] Select an accessible protected cell: Kjell article 32058, 2600 mAh.
  See `battery-selection.md`; selection is not charging approval.
- [ ] Complete retail/datasheet equivalence, holder/NTC/harness/current limits,
  USB source limit, temperature cutoff and prototype quantity. The new battery
  screen fails the earlier nominal hot cutoff; a separate BQ24072T revision now
  targets roughly 5–35 °C with preliminary screens passing. Guaranteed bounds,
  charging completion and hardware tests remain unresolved. Older RF reports
  do not cover this revision.
- [ ] Resolve or explicitly accept the shared modem/USB detect rail risk: the
  current static window leaves only about 60 mV beyond each relevant limit.
  Changing feedback alone cannot be presumed to fix burst droop or startup.
- [ ] Independently review final artwork/connectivity/DFM and assembly orientation,
  pin 1, polarity and centroids in the JLCPCB preview. Confirm Standard PCBA/X-ray.
- [ ] Recheck live stock for the intended quantity and obtain supplier review.
- [ ] Approve the exact prototype upload package and document outstanding risks,
  current hashes/pins, bring-up limits and required measurements. Do not bypass
  the existing production `make order` qualification gate.

## After receiving boards

- [ ] Current-limited bench bring-up; check harness polarity and rails before
  connecting a battery. Validate charger/NTC behaviour and thermal limits.
- [ ] Measure modem supply/detect startup, transmit bursts and cable removal at
  minimum pack voltage. Check disabled/undervoltage states and safe host firmware.
- [ ] Exercise battery-only full-speed USB enumeration and sustained transfers.
- [ ] Measure antenna/RF behaviour in the actual enclosure; tune matching if needed.
- [ ] Record candidate-bound evidence and fix/retest before production approval.

## Battery integration revision

- [x] Select Kjell 32058 and record protected-cell source facts in CopperLib.
- [x] Add reusable BQ24072T part, conservative TS bias module, external sensor
  and protected-cell holder specifications in CopperLib.
- [x] Add generic independent divider/leakage/fault and K/R/K*R screens in
  CopperScript; keep unknown source guarantees explicitly unresolved.
- [x] Compile the separate full-board revision: 87 components, no ERC errors.
- [x] Validate the six-layer placement with actual footprints and macro copper:
  five old charger-support poses changed, 78 preserved; no represented placement
  rejection. Do not waive the short TS/programming/decoupling constraints.
- [ ] Complete guaranteed thermistor/leakage/drift and cell thermal-tracking
  review; actual protected-cell holder fit/contact losses and harness assembly.
- [ ] Resolve safety-timer adequacy for full recharge without disabling the timer.
- [ ] Recheck new JLC candidates and review revised BOM/centroids; publish/pin
  reusable library/compiler changes before adopting the main source revision.
- [ ] Route/refill the revised board and repeat current native, assembly, CAM
  and engineering checks. Existing Gerbers belong to the earlier circuit.
- [ ] Finish modem supply distribution/bypass and RF/USB findings above, then
  obtain exact prototype-package and quantity approval.

See `battery-selection.md` for repeatable working-copy review commands. The main
engineering plan now hashes the battery selection/revision inputs, invalidating
earlier reports for a new release decision without rewriting those reports.

## First concrete finding

The current native modem pad 60 is at (8 mm, 24 mm), facing left at the source's
90-degree rotation. The old comment said north and fixed J_CELL at (31 mm, 6 mm).
Its existing CELL_RF track sum is about 36 mm, exceeding the assumed guide's
20 mm maximum. Even the straight pad-centre distance is about 29 mm, so routing
alone cannot fix this placement. Move the connector near the real pad; preserve
the earlier native files as historical checkpoints.

SIMCom source: [V1.01 p60, Figure 32](https://files.waveshare.com/wiki/SIM7670G-LTE-Cat-1-GNSS-HAT/SIM7672X_Series_Hardware_Design_V1.01.pdf),
SHA256 `bd198ceb5eecddbafd3d438782cf35c89208e40a8c4b3b1eb19097fdb363706d`.
Reusable reference facts belong in CopperLib; placement/routing/checking
algorithms stay in CopperScript. This file owns only the tracker release decisions.

## Corrected RF-length checkpoint

J_CELL is now fixed at (6 mm, 8 mm), rotated 180 degrees. Its signal land faces
right. CopperScript's existing exact-clearance surface-path search produces a
via-free F.Cu feed of 17,693 um (rounded to the nearest um), below 20 mm. The
source now carries `max_length = 20mm` as well as the existing zero-via rule.
This is a length correction, not complete RF layout approval: the current
200 um width, module-edge launch, coplanar ground clearance, impedance and
matching/ESD adaptations still require review. See `stackup-selection.md`.

Only J_CELL's native pose and CELL_RF tracks changed. Exact native multiset
comparison preserves all other tracks and all 367 vias. The source comparison
finds only the connector fixed-placement and feed-length constraint changed;
all other serialized electrical semantics and all 83 approved selections are
identical. The assembly lock's design digest was refreshed, not its identities
or approval flags. Strict current-source pad/net/pose/placement/macro checks
and fresh KiCad 10.0.6 refill/DRC both pass, with zero violations and zero opens.

Current exported PCB: `build/fabrication-prototype-rf-20261010/routed.kicad_pcb`,
SHA256 `8282270ea329f5f7ae82b36b672419bd1380057a8be7fd8a62b9e93d19e9d24d`.
Source SHA256 `03883bab0bd8e5734127711bc1137698ea355e77c202afc825b2807430e2baff`.
Compiler/library pins remain unchanged. The new native images and source-bound
snapshot in `docs/showcase/` supersede the earlier README illustrations.

New review files (all unqualified; older files retained):

- `build/fabrication-prototype-rf-20261010/gerbers-drill.zip`
- `build/fabrication-prototype-rf-20261010/manufacturing-package.zip`
- `build/assembly-prototype-rf-20261010/assembly-review.zip`

The fabrication package includes the unchanged approved native-reference BOM.
Fresh assembly data contain 43 rows and 83 placements; CPL and live stock remain
unreviewed. Fresh reports outside the immutable package:

- `build/cam-prototype-rf-20261010.json`: 10 pass / 3 incomplete.
- `build/engineering-prototype-rf-20261010.json`: 8 pass / 41 incomplete.
- `build/qualification-prototype-rf-20261010.json`: 22 pass / 3 incomplete.

No automated mandatory check fails, but missing evidence is not approval. All release
flags remain false. Independent copper/DFM, RF/power/USB modelling, operating
inputs, CPL review and prototype measurements remain open. No supplier upload
or order was made.

The application-only `scripts/shorten_cellular_feed.py` migrates the exact earlier
PCB/source hashes using shared CopperScript algorithms. Reproduce it from the
earlier `4d7c9d2` source checkpoint, then adopt the source delta and rerun native
refill/check/export. It deliberately refuses changed source, unknown PCB bytes
and existing outputs; it is not a general native-board importer.

Verification: all 47 tracker unit tests and 10 focused CopperLib contract/GNSS
footprint tests pass. ZIP integrity and every package SHA256SUMS entry were
checked; the fabrication and fresh assembly BOM CSVs are identical. Native
placement/top-copper illustrations were rasterized and visually inspected.

## Historical RF-checkpoint power findings (superseded only in the new draft)

The adopted SIMCom guide's local VBAT capacitor recommendation is not yet
implemented in full. The source has one local 100 uF ceramic reservoir and
three 22 uF converter-output capacitors, but no local 10 pF / 33 nF / 100 nF /
1 uF bank at the modem VBAT contacts. The converter-output lands are near
(46-50 mm, 49 mm), while modem VBAT contacts are at (8 mm, 19-21 mm); those
remote capacitors must not be counted as a reviewed local bypass network.
The approved reservoir CL32A107MQVNNNE needs DC-bias/effective-capacitance and
transient review; its nominal 100 uF alone does not establish a 100 uF reservoir.

The explicit V3V8 routing inventory has 800 um trunks and 200/240 um branches
on F.Cu, In2.Cu and B.Cu, with no V3V8 distribution zone. Thus it does not
implement the guide's at-least-2-mm regulator-to-module recommendation. This
is a manual design finding; the incomplete power-layout gate is not a passing
width approval. Review the main high-current path and required pad neckdowns
separately from the low-current detect/feedback branches; widening the entire
multi-load net blindly is not a current-distribution solution.

Next design revision: establish the actual supply/pack/load envelope, confirm
effective reservoir capacitance, add the source-backed local bypass/support
network with explicitly reviewed selections, and redesign the modem power
distribution. Reusable support topology/parts belong in CopperLib, any new
path/branch algorithms in CopperScript. Do not silently carry the existing BOM
approval onto added or replaced selections. Retest the RF corridor and all
source/native/assembly/export checks after that revision.

## Combined modem-power/battery revision checklist

- [x] Add the reusable SIMCom modem/local bypass topology in CopperLib; retain
  actual pin association and all three required VBAT contacts.
- [x] Add a reusable widened TPS63020 output variant with four off-pad vias;
  preserve the switching, quiet feedback and ground-return circuit.
- [x] Compose those with battery-v1 in an isolated, source-bound 91-part draft;
  preserve earlier canonical source, locks and fabrication archives.
- [x] Add the regional In2 modem-power corridor and actual-footprint placement.
  Placement/geometry guards pass; native placement DRC has no non-connectivity
  errors. New assembly identities are candidates, not inherited approval.
- [x] Complete fresh routing and independently refill/check the native candidate.
- [x] Verify direct surface bypass feeds, all VBAT contacts and native DC
  continuity of filled distribution/GND against the actual routed result.
  This does not qualify current capacity, return impedance or transient behavior.
- [ ] Resolve reservoir effective capacitance, source/load envelope, via/plating
  capacity, supply droop/startup/USB detection and converter thermal behavior.
- [ ] Refresh locked release inputs and changed BOM/CPL review before exporting
  replacement fabrication files. Earlier archives remain the old 83-part board.

Implementation inputs and reproducible commands: `revisions/modem-power-v1/`.

### Completed routing checkpoint (91-part working-copy revision)

Final native PCB: `build/power-v2-20261010-route-v15/routed.kicad_pcb`, SHA256
`d8c724d70b8ca4ff1d35801eb38d5035c8b8cfcbc9f5521b5e72a360aa6f0762`.
Current isolated source: `build/power-v2-20261010-v13/board.copper`, SHA256
`2d0a5dcda3e61cc0066c0c8938e2c3547479f275c182ed67704c61dc47412205`.
Six copper layers; physical readback has 1,146 tracks and 371 vias. Native KiCad
10.0.6 refill/DRC and a separate read-only DRC both report zero violations and
zero unconnected items. Strict current-source pad/net/pose/placement/macro checks
pass. All four local bypass feeds are via-free F.Cu chains to assigned VBAT pads.

Evidence: `build/power-v2-20261010-route-v15/final-routing-checkpoint.json` and its
fresh sibling `.native-drc.json`; layer views are `routing-top.svg` and
`routing-power.svg` in the same directory. The checkpoint binds PCB, source,
power composition, locks, macro scene, native executable, build record and
checking/routing algorithm files. Native layer views were visually inspected.

The full route first needed V5/GNSS_TIMEPULSE repair. Native refill then exposed
through-via clearance fields splitting the original load strip, an unattached
second-layer detect spur, and a lower spur tie isolating accelerometer supply
contacts. Source-only fill corrections preserve the reserved core and all
keepouts. The boxed-in accelerometer contact was placed before rerouting only
ordinary I2C_SCL. Exact native-identified ordinary stubs/vias were removed only
with shared mutability, macro/array and actual pad-connectivity checks.

Regression scope: CopperScript focused routing suite 106 passed; CopperLib
144 passed / 31 optional skips. Tracker full-suite results are recorded in the
revision README. Full CopperScript-suite success is not claimed.

This is not a locked release or replacement fabrication package. Canonical
source/locks and the earlier 83-part manufacturing archives remain unchanged.
Effective reservoir capacitance/ESR, actual load-path neckdowns/current sharing,
battery/charger guarantees and charging completion, low-battery burst/USB tests,
RF/USB modelling, changed selection/CPL review and updated release pins remain
open. No supplier upload or order was made.
