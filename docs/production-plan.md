# Production-readiness plan

The six-layer candidate is a review candidate, not an approved production release.
Only the canonical 83-part BOM is approved under the user assumption. The 91-part
revision needs changed-selection approval; neither scope approves CPL, RF, power or CAM.
The current 97-physical / 95-fitted pre-prototype scope is tracked separately in
[the preorder plan](prototype-preorder-plan.md); the user excludes mechanical
fit/test-access work for that pass, not assembly-process or electrical review.
Its v3 source/lock and current routing status are in [validation](validation.md).
The current GNSS model uses the corrected R08 open-selector supply limits.
Select JLCPCB **JLC06161H-3313 / NP-155F**, nominal 1600 um,
outer 1 oz / inner 1/2 oz. The RF revision hashes that exact selection.
See `stackup-selection.md` and `engineering-plan.json` for source-bound inputs.

## 1. Characterize actual RF and USB geometry — in progress

- [ ] Review adjacent reference planes, especially modem USB on In2 beside
  In3 V3V3, and the actual return paths at transitions.
- [ ] Model RF and USB using actual copper, mask, stackup and launches; record
  solver assumptions, convergence, limits and geometry hashes. Formula screens
  alone cannot close the impedance requirement.
- [ ] Qualify actual detect-pin voltage/transients and USB firmware sequencing;
  see `usb-battery-power.md`. Nominal/shared-rail operation is not bench approval.

Acceptance: reviewed, reproducible geometry-bound modelling for all three
radios and both USB paths; no uncovered or unexplained reference transitions.

## 2. Close manufacturer integration/layout requirements

- [x] Review Johanson corner guidance and correct the RF review revision's
  closed clearance island. Shared CopperScript v0.5 host-edge validation and
  isolated six-layer native refill preserve the matching returns and NC land.
  This does not close antenna tuning, enclosure or impedance qualification.
- [x] Review MAX-M10S R05 integrated matching/filtering and reproduce the long
  host-feed detour. Shared bounded RF surface search accepts a shorter via-free
  candidate; final whole-board routing and actual reference coverage remain open.
- [x] Review exact MAX-M10S integration guidance: antenna type, matching,
  filtering/ESD/bias, ground/layout and RF feed geometry.
  Source review is recorded in CopperLib; consumer antenna/coexistence choices
  and detailed layout qualification remain open.
  The user selected a passive GNSS antenna: no antenna-power bias circuit.
  Exact passive antenna/cable and connector ESD are selected in RF-support v1;
  coexistence, system ESD and sensitivity qualification remain open.
  See [RF support revision](../revisions/rf-support-v1/README.md).
- [x] Select applicable modem reference basis: the user explicitly accepted
  SIM7672X applicability. This is a scoped assumption, not manufacturer-confirmed
  exact-variant equivalence; do not repeatedly ask for the same assumption.
- [x] Select the external cellular antenna: Taoglas FXUB16.07.0150AQ, factory
  150 mm U.FL-compatible assembly. Reusable source/band facts belong in CopperLib.
- [x] Select passive GNSS Taoglas FXP611.07.0092C with its factory 92 mm cable;
  retain integrated receiver DC isolation and reserve enclosure/metal clearance.
- [x] Perform cellular schematic/reference/actual-copper review and record its
  findings in [the design review](../revisions/rf-layout-v1/cellular-design-review.md).
- [x] Implement an isolated source revision with library-owned LTE initial
  DC-block/tuning/ESD support and passive GNSS ESD; select both external antennas.
  See [RF support implementation and remaining gates](../revisions/rf-support-v1/README.md).
- [ ] Verify the new protection/tuning layout and close GNSS coexistence/filter
  design, then close the review findings: system RF ESD and installed matching,
  launch/return modelling, supplier process acceptance and enclosure placement.
  The review outcome is changes required, not passed design approval.
- [ ] Qualify modem supply burst requirements and exact-variant limitations.
- [ ] Review Nordic/Johanson macro adaptations and antenna/enclosure keepouts.
- [ ] Keep reusable manufacturer guidance and qualification contracts in
  CopperLib; record only the tracker implementation/review decisions here.

Acceptance: every required support component and source-backed placement rule
is implemented or explicitly justified, with exact document provenance.

## 3. Qualify power and battery — awaiting operating inputs

- [ ] Complete the selected Kjell 32058/103AT-2 pack and sensor guarantees,
  protection trip/recovery, battery range, USB source limit, peak/RMS loads and
  ambient envelope; see [battery integration](battery-selection.md).
- [ ] Review converters and charger, power paths/vias, effective capacitance,
  inductor saturation, transient droop and thermal limits against that envelope.
- [ ] Keep capacity/transient algorithms in CopperScript and reusable device
  constraints/macros in CopperLib. Do not invent currents or thermal limits.

Acceptance: reviewed operating envelope, source-backed design/simulation and
prototype measurements; no unqualified battery/NTC or power-path assumptions.

## 4. Apply justified layout changes and revalidate

- [ ] Change RF widths, USB routing, support circuitry or power geometry only
  after steps 1–3 establish the relevant requirements.
- [ ] Preserve approved identities unless an explicitly reviewed change is
  necessary. Preserve macro-critical copper and generic decoupling intent.
- [ ] Rebuild, route, fill and run native DRC/connectivity plus geometry checks.
- [ ] Generate a new versioned fabrication/assembly candidate and fresh audits.

Acceptance: zero native violations/opens, current source and library locks,
consistent exported geometry, and fresh evidence bound to that exact candidate.

## 5. Independent fabrication and assembly review

- [ ] Close independent Gerber/drill parser corpus and agreement checks,
  final-artwork copper connectivity, fabrication DFM and minimum barrel/loss data.
- [ ] Inspect CPL rotations, polarity, centroids and JLCPCB assembly preview;
  verify exact stackup selection and live sourcing before an order.

Acceptance: all mandatory release gates pass and a human approves the exact
manufacturing/assembly package. This plan does not authorize placing an order.

## 6. Prototype validation before volume release

- [ ] Measure supply startup/burst/thermal behaviour, charging/NTC behaviour,
  USB function and radio/antenna performance in the intended enclosure.
- [ ] Attach measured, candidate-bound evidence and fix/retest any failures.

Acceptance: reviewed bench evidence and release approval; neither a clean DRC
nor a nominal impedance calculation substitutes for these measurements.

Current implementation/status is in [validation](validation.md). The battery-powered
USB requirement and scoped SIM7672X assumption are in [USB power](usb-battery-power.md).
Native routing closure and the local bypass bank are implemented in the 91-part
revision; their electrical adequacy remains subject to the requirements above.
