# Prototype release checklist

Latest geometry/connectivity status is in [validation](validation.md). A prototype
build is a separate experimental decision: keep `qualified_release=false` until
the complete production criteria pass. This checklist authorizes no purchase,
supplier upload or bypass of the production ordering gate.

## Before fabrication

- [ ] Approve the exact revision/package/quantity and document outstanding risks,
  input hashes/pins, bring-up limits and required measurements.
- [ ] Review changed 91-part BOM selections, supplier stock, CPL polarity/centroids/
  rotations and assembly preview; confirm modem Standard PCBA/X-ray requirements.
- [ ] Review RF impedance/matching/antenna adaptations, cellular feed limit,
  GNSS antenna bias/ESD/coexistence and USB references/transitions on the selected stackup.
- [ ] Qualify modem bypass effective capacitance, distribution necks/vias/current
  sharing and reservoir ESR/bias; a local bank and connected pour do not prove PI.
- [ ] Complete battery retail/datasheet equivalence, protection, holder fit, harness/
  NTC thermal tracking, guaranteed cutoff bounds and safety-timer recharge review.
- [ ] Resolve shared modem/USB-detect rail startup/burst/down-state risks: the static
  screen leaves about 60 mV at relevant limits. Retain the source bounds.
- [ ] Review independent final artwork/connectivity/DFM and fresh native closure
  for the exact upload package. Publish/pin reviewed tool/library inputs.

## Bring-up and measurements

- [ ] Current-limited bench bring-up: verify harness polarity and rails before
  attaching the cell; check charger, NTC and thermal behavior.
- [ ] Measure modem supply/detect startup, transmit bursts, cable removal and
  disabled/undervoltage recovery at minimum pack voltage.
- [ ] Exercise battery-only full-speed enumeration and sustained USB transfers;
  validate host shutdown/data-pin behavior and firmware sequencing.
- [ ] Measure antenna/RF behavior in the intended enclosure; tune and retest.
- [ ] Attach candidate-bound results and close [production requirements](production-plan.md)
  before volume-release approval.
