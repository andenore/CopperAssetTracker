# LTE and passive GNSS RF support revision

Implementation plan; old routed boards and release locks remain historical.
Reusable parts/circuits and source facts belong in CopperLib. Shared analysis,
placement and routing belong in CopperScript. This project owns configuration,
source composition and verification evidence, not routing repair algorithms.

- [x] Verify exact protection ratings, package/pin maps and listed PCBA identities.
- [x] Add library-owned LTE protection/DC-block/tuning support and passive GNSS
  protection, preserving the receiver's integrated DC block/LNA.
- [ ] Close additional GNSS filtering and its own ESD/power/matching design.
- [x] Adopt both exact external antenna assemblies in a new revision selection.
- [x] Author RF pad-distance constraints and surface-only feed
  and grounded-coplanar intent on JLC06161H-3313 / NP-155F.
- [x] Build fresh source and check ERC: 97 physical parts, 95 fitted selections.
- [x] Verify legal placement with real footprints and accept immutable macro
  copper; retain routability warnings, not an RF/layout qualification pass.
- [ ] Route using the standard shared pipeline; retain source-bound native DRC
  and RF geometry evidence. Never reuse old passes for changed copper.
- [x] Quantify conditional point-frequency LTE-to-GNSS budgets with explicit
  bounds and unknowns using the shared CopperScript algorithm.
- [ ] Obtain measured coupling, correct receiver gain-mode/band-wide limits,
  full-path field modelling and supplier process acceptance.
- [x] Record assembly/DNP state, external installation/clearance instructions
  and prototype tests. No fictional tuning, enclosure fit or bench results.

RF design and production approval stay false until the exact changed package
has all required evidence. No purchase, fabrication order or push is implied.

## Implemented source revision

LTE selects Taoglas FXUB16.07.0150AQ, 150 mm factory cable. CopperLib's
`packages/circuits/simcom/lte-antenna-support` contains the conditional
SIM7672X V1.01 Figure30 adaptation: 0 ohm link, 100 pF initial DC block,
two DNP shunt tuning lands and Semtech RClamp1561PQTCT TVS. The direct-coax
topology differs from the reference's RF test connector arrangement.
J_CELL moves to make space for this support; no matching result is assumed.

GNSS selects passive Taoglas FXP611.07.0092C, 92 mm factory cable. The
MAX-M10S integrated matching, DC block and LNA remain intact. A TI
TPD1E01B04DPYR is placed near J_GNSS; DPY capacitance is 200 fF typical /
230 fF maximum at zero bias. No active bias tee is present.

RF segments use nominal 142 um width / 201 um ground clearance on the selected
JLCPCB six-layer outer coplanar cross-section. Each is constrained to F.Cu,
zero signal vias. LTE segment length budgets sum to 20 mm. These are routing
requirements, not measured characteristic impedance or complete launch EM.
Actual signal and TVS-ground paths still need independent review.

The new exact ESD parts, package drawings, reusable topology and reference
limits belong in CopperLib. CopperScript owns `rf_coexistence.isolation_budget`
and now propagates `assembled = false` into native BOM/CPL exclusions while
retaining physical copper. New sourcing candidates in procurement.json remain
unreviewed; existing BOM approval does not automatically cover them.

## GNSS coexistence is an explicit remaining design gate

The pre-order work records an **unapproved experimental baseline** in
[gnss-prototype-decision.json](gnss-prototype-decision.json). MAX-M10S already
contains matching/DC block/notch/LNA/SAW; keep passive GNSS without an additional
SAW for initial characterization with LTE/BLE transmit disabled. B4327 remains
a future protected redesign, not a board-level solder-population option.
This choice prepares a candidate; it does not approve simultaneous LTE/GNSS or
ordering. The manufacturer's default is low-gain, but actual firmware must be
checked. Table43 is typical room-temperature 64QAM/10 MHz data, not a guaranteed
immunity limit. Shared RF-tree routing now needs explicit topology intent for
the physically connected TVS and DNP shunt pads.

[coexistence-screen.json](coexistence-screen.json) binds nine receiver samples,
conditional transmitter limits and the shared algorithm. The transmitter
reference specifies 23 dBm plus up to 2700 mdB positive tolerance. Receiver
Table43 immunity applies to **low-gain mode**, which is not yet confirmed in
firmware. The extra 3 dB screening margin is an authored allowance.

For example, at 1710 MHz the conditional budget needs 53700 mdB total
attenuation (54 dB rounded up). Candidate B4327 rejection is at least 34 dB
there, leaving 19700 mdB required antenna isolation (20 dB rounded up).
Isolation has not been measured; this is not a pass. Point samples must not
be interpolated into immunity guarantees across all LTE bands.

B39162B4327P810 was reviewed but **not added**. Its multi-constellation passband
loss must be included in sensitivity, and some LTE ranges lack guaranteed
rejection. More importantly, its ESD notice requires an application-specific
series-C / shunt-L / series-C high-pass network in addition to a TVS/varistor,
with effectiveness tested. A bare TVS plus SAW would not close this requirement.
The reusable source facts and limitations are in CopperLib's MAX-M10S package.

To close this gate, measure antenna S21 in the intended enclosure across every
enabled LTE transmit band, establish the actual receiver mode/limits, then
select and simulate any required filtering/protection. Validate GNSS cold-start,
tracking C/N0 and sensitivity during maximum-power LTE, BLE, charging and
battery-powered modem USB operation. Also validate installed LTE match/loss,
RF peaks under mismatch and system ESD. Do not invent measurements.

Mount both antennas on the intended plastic enclosure, maximize isolation,
retain factory cable lengths and verify retention/mating. Reserve 40 x 40 mm
for GNSS and maintain the manufacturer's 10 mm radiator clearance from battery
metal and the main board ground. This does not mean removing feed return ground.

## Reproduction

Compose with the existing builder plus `--modem-power --rf-layout --rf-support`.
The candidate is `build/rf-support-v8-20261012/source/board.copper`.
Resolve footprints using `python -m copperscript lock <board.copper> --offline`,
then the standard `route-board --locked --offline` pipeline with six layers,
the three copied hard-macro scenes and native plane-fill verification.
No custom tracker routing repair is added. Historical boards/review packages
are preserved and remain independent of this revision.

## Verification history

The 97-part v6 attempt stopped before routing: the LTE TVS signal pad faced
away from J_CELL, giving 4425 um against the authored 3600 um maximum. V8
rotates the electrically symmetric TVS to 90 degrees, keeping its courtyard
unchanged and putting its signal pad toward J_CELL (3575 um nominal pad-center
distance). The limit is retained. The canonical fixed modem-status translator
poses were also removed from this variant so shared placement can relocate its
bank without losing electrical or decoupling intent.

CopperScript now diagnoses contradictory fixed pad constraints before soft
placement and names exact relative distances in physical DRC. No tracker-local
routing repair is involved. Placement, fresh routing/native DRC and system RF
qualification are separate checks; a source correction is not their pass.

V8 `plan-layout --locked --offline --candidates 1` completed successfully with
the three copied hard-macro scenes and real footprints. Its placement gate is
`warning` (legal placement with routability warnings), routing is `not_run`, and
release verification is `blocked`. The inspection PCB and full report are in
`build/rf-support-v8-20261012/`; [verification.json](verification.json) records
their exact hashes. Tracker source-build tests pass (8 tests); focused library
checks also pass, as do 62 focused CopperScript tests (not the full suite).
Read-only installed KiCad inspection independently confirms 97 footprints,
95 fitted BOM entries, both tuning-land CPL exclusions and the actual 3575 um
TVS-to-connector signal-pad distance. These do not replace RF simulation, native routing/DRC or
prototype evidence. V7 was an incomplete build using an unsupported unquoted
manifest path with spaces; V8 uses the pinned footprint-cache path.
