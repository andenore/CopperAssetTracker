# Prototype bring-up checklist

Status: planned measurements, not completed tests or permission to energize.
Applies only after an exact source-matched prototype package is approved and
assembled. Mechanical fit and test-access assessment are excluded by the user.
This checklist does not waive component limits, battery safety review or RF risk
acceptance. Use qualified electrical/RF review for the actual test setup.

Record the package manifest hash, board serial/revision, fitted component
identities, instrument identities/calibration, firmware hash, setup and ambient
temperature with every result. A measured value from another board or source
revision is not evidence for this one. Attach raw waveforms and failure notes,
not only a pass/fail statement.

## Sequence and evidence

| Stage | Prerequisites and configuration | Record / acceptance basis |
| --- | --- | --- |
| Unpowered inspection | Exact BOM/CPL and assembly preview approved; no battery attached | Native artwork comparison, fitted/DNP identity, polarity, shorts and solder/process inspection. Modem support fixture/X-ray and GNSS MSL 4 handling must be confirmed by the assembler. |
| Supply-only first power | Qualified current-limited setup; charging and RF transmit not assumed safe | Actual input current, every rail at its device pads, startup/overshoot and fault response. Stop on a limit violation or unexplained heating; do not increase the supply limit merely to mask a fault. |
| Logic/GNSS baseline | MODEM_EN inactive, modem rail verified off, MCU USB drivers stopped and BLE transmit disabled | VCC/V_IO/V_BCKP, V_IO ramp, receiver startup current, actual MAX-M10S hardware/ROM revision and low-gain configuration/readback. R08 open-selector V_IO is 2700 mV through VCC; rise time is 25–35000 us/V. Verify source applicability before using these limits. |
| Battery-powered modem USB | Actual cell/protection/harness review complete; reviewed RF setup prevents uncharacterized GNSS exposure | Full-speed enumeration, sustained bidirectional transfers, detect voltage at modem pad 24 and VBAT at device pads over battery/load states. USB must work without external USB-C power. Apply the user's SIM7672X applicability assumption explicitly; record actual fitted modem identity. |
| Modem supply burst | Current path, converter and RF test configuration reviewed first | Pad-level transient minimum/maximum, input/rail current, ringing, temperature and recovery under recorded load/network conditions. Static divider screens of 3660–4140 mV leave 60 mV margin; they are not transient guarantees. |
| Power sequencing | Host/data drivers stopped before modem shutdown | PWRKEY/AT+CPOF behavior, residual VBAT/discharge, receiver/level-shifter pins and restart. Verify VBAT below 1300 mV and at least 2 s off before the reviewed restart sequence; firmware intent alone is insufficient. |
| Charger characterization | Actual protected cell specification and temperature-sensor applicability accepted before cell charging | Charge voltage/current, taper/termination, timer behavior, NTC trips and fault inhibition, input/system sharing and thermal behavior. Prefer a reviewed battery simulator for initial characterization; do not short or overheat a real cell to test faults. |
| RF characterization | Exact antennas, cables, reference configuration and controlled test setup reviewed | Coupon/line impedance, actual RF launches/branches, return path and ESD loading; receiver baseline and isolation/coexistence measurements. Typical room-temperature immunity numbers are not guaranteed band-wide limits. |

The logic divider screen reaches 3594 mV against a 3600 mV upper limit: its
remaining 6 mV is particularly weak. Validate startup, ripple and temperature
behavior; do not describe this as a qualified power rail. Feedback-divider or
operating-mode changes require a new source revision and affected verification.

Charging completion is also unresolved. The programmed minimum fast-charge
timer is 23562 s, while 2600 mAh at the screened minimum 359 mA requires at
least 26073 s before taper. Record incomplete-charge behavior rather than
disabling a safety timer or raising the USB current budget without a redesign.
The intended charging/operation temperature target is 5–35 degC; mathematical
NTC screens do not establish actual trip temperatures or sensor fault safety.

## GNSS/LTE boundary

Initial GNSS baseline testing is proposed with the modem physically unpowered
and BLE transmit disabled. Its risk acceptance is still pending. GNSS shares
the logic supply and has no independent power switch: receiver standby is not
RF-input protection. A command sent after modem boot is not proof that no early
transmission occurred. Battery USB and later maximum-power modem tests therefore
need a separately reviewed RF configuration before modem power-up.

Routine simultaneous LTE/GNSS service is not approved. Do not infer antenna
isolation from connector spacing, use typical immunity as an absolute maximum,
or infer immunity from the RF_IN absolute maximum. A protected front-end
redesign remains an alternative to accepting the restricted experiment.

## Result disposition

- [ ] Exact package and prototype risk acceptance recorded.
- [ ] Supplier stock, assembly preview and package-process acceptance recorded.
- [ ] Unpowered inspection completed.
- [ ] Supply-only startup and logic/GNSS baseline completed.
- [ ] Battery USB and reviewed modem supply/sequencing tests completed.
- [ ] Charger/cell/NTC applicability and characterization completed.
- [ ] RF/coupon, isolation and controlled coexistence measurements completed.

Every box starts unchecked. Fabrication of a deliberately restricted engineering
prototype may precede these measurements after approval; an approved production
release cannot inherit invented or unperformed results. See
[electrical review](prototype-electrical-review.md) for source hashes/limits and
[preorder plan](prototype-preorder-plan.md) for work completed before ordering.
