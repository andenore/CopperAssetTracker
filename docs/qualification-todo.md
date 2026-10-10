# Tracker qualification checklist

Generic implementation lives in CopperScript `docs/qualification-todo.md` and
CopperLib `docs/engineering-contracts.md`. This file tracks only this board.

- [x] Bind the existing six-layer native manufacturing candidate without rerouting.
- [x] Add board-specific RF/power contract bindings in `engineering-plan.json`.
- [x] Leave unknown stackup, pack, USB, load, temperature, efficiency and effective
  capacitance inputs as null; do not substitute plausible illustrative values.
- [x] Run package hashes, layer inventory, drill/contact/via and net-partition
  reconciliation; all 295 drill hits, 552 contacts and 295 vias pass.
- [x] Screen actual filled In1 GND coverage under cellular/GNSS track envelopes;
  zero-extra-margin coverage passes, not impedance qualification.
- [x] Run fail-closed CAM/RF/power checkpoint; all three reports are incomplete,
  not falsely qualified. Add blocking ordering-target prerequisites.
- [x] Refresh library inventory and only the unreviewed assembly provenance
  digest; all 83 exact selections and zero reviewed flags are preserved.
- [x] Verify 27 tracker tests; record upstream focused and broader-suite results
  in CopperScript's checklist without claiming the full suite passed.
- [x] Select JLC06161H-3313 standard 1.6 mm construction, retaining sourced
  dielectric/copper data in CopperLib and generic screening in CopperScript.
- [ ] Obtain order-specific minimum barrel plating and dielectric loss data.
- [x] Inventory actual RF/USB layers and widths against that construction.
- [ ] Resolve RF feed width and USB inner-layer/launch modelling findings;
  see `stackup-selection.md`. No estimated width is production-qualified.
- [x] Extract actual USB pair gaps/overlaps, member copper lengths, vias and
  adjacent plane nets/separations using generic CopperScript algorithms;
  see `rf-usb-geometry-review.md`. Breakout/return/delay modelling stays open.
- [x] Add mandatory whole-link USB design/simulation/bench contract from CopperLib
  and generic CopperScript validation; do not approve USB through auxiliary screens.
- [x] Trace four explicit USB pad-centre paths with native pad layers/via types,
  distinguishing transitions, unused barrels and nearest GND vias. See
  `usb-channel-review.md`; electromagnetic delay/return modelling remains open.
- [x] Confirm battery-mode USB requirement: user requires MCU-to-modem USB on
  battery. Record functional/safe states in the source-bound engineering plan.
- [x] Adopt user-authorized SIM7672X V1.01 applicability and move USB detection
  to switched V3V8 without tying it to the external input connector.
- [ ] Qualify actual detect-pin voltage/transients, host firmware and required
  power states; see `usb-battery-power.md`. Static headroom is only about 60 mV.
- [ ] Review exact SIM7670G-LNGV hardware/matching/layout requirements.
- [ ] Review MAX-M10S integration/antenna/ESD requirements and pin exact sources.
  Integration manual R05 source/figures reviewed and pinned in CopperLib;
  datasheet hash, consumer antenna/filter/protection and layout remain open.
- [ ] Review BLE macro adaptations, prescribed matching returns and enclosure.
- [ ] Qualify cellular/GNSS/BLE impedance using actual stackup/geometry.
- [ ] Define minimum battery/VSYS, modem burst/logic loads, USB, pack and ambient
  envelopes; obtain biased MLCC, ESR, inductor/current and temperature data.
- [ ] Complete converter/charger layout, conductor capacity and thermal review.
- [ ] Supply reviewed, board-bound solver and prototype measurement evidence.
- [ ] Complete independent final-artwork CAM connectivity/DFM and parser corpus.
- [x] Record user-directed exact BOM approval for 83 selections / 43 identities;
  refresh provenance only for the added generic profile, with no part changes.
- [ ] Approve CPL rotations, polarity, centroids and supplier preview;
  recheck live stock before ordering. BOM approval does not approve placements.
- [x] New assembly package and selected-stackup reports preserve old artifacts.

Reports belong outside the immutable fabrication package. Nonzero audit exit
codes mean failed/incomplete checks, not a routing regression. Native DRC closure
does not approve RF, power, battery safety, assembly or a production order.
