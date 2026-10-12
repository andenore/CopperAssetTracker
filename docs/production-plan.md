# Production-readiness plan

The six-layer candidate is a review candidate, not an approved production release.
Only the canonical 83-part BOM is approved under the user assumption. The 91-part
revision needs changed-selection approval; neither scope approves CPL, RF, power or CAM.
Select JLCPCB **JLC06161H-3313**, nominal 1.6 mm, outer 1 oz / inner 0.5 oz.
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
- [ ] Review exact MAX-M10S integration guidance: antenna type, matching,
  filtering/ESD/bias, ground/layout and RF feed geometry.
  Source review is recorded in CopperLib; consumer antenna/coexistence choices
  and detailed layout qualification remain open.
  The user selected a passive GNSS antenna: no antenna-power bias circuit.
  Exact antenna/cable, connector ESD, coexistence and sensitivity qualification
  remain open. See [RF layout review revision](../revisions/rf-layout-v1/README.md).
- [ ] Obtain exact SIM7670G-LNGV hardware guidance or manufacturer confirmation
  of applicability of the related SIM7672X document. Resolve matching/ESD and
  supply burst requirements; do not treat family resemblance as approval.
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
