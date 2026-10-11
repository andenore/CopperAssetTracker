# Selected stackup

Select JLCPCB **JLC06161H-3313**, nominal 1.6 mm FR4, outer 1 oz / inner 0.5 oz.
Library-owned `packages/profiles/jlcpcb/jlc06161h-3313/stackup.json` records exact
source hashes/locators. Bind the selected profile to each revision's engineering
plan; it does not by itself set plane nets. Layer order is
F.Cu / In1.Cu / In2.Cu / In3.Cu / In4.Cu / B.Cu.

Published dielectric spacings are 0.0994 / 0.55 / 0.1088 / 0.55 / 0.0994 mm;
Dk values are 3313: 4.1, core: 4.6, 2116: 4.16. Construction totals 1.5384 mm,
within published 10% tolerance around nominal 1.6 mm. Do not stretch dielectric
spacings to force the nominal total. Specify the exact construction in fabrication
and impedance review; a nominal native-board thickness is insufficient.

Published 18 um average hole plating is not a guaranteed minimum. Order-specific
minimum barrel plating and dielectric loss remain unresolved. See [supplier stackup](https://jlcpcb.com/impedance)
and [capabilities](https://jlcpcb.com/capabilities/pcb-capabilities).

Model actual routed widths, coupled gaps, pads, launches, mask, adjacent planes,
local openings and return transitions. Isolated microstrip estimates do not
qualify differential USB or embedded routes; proximity to a power plane is not
proof of a ground reference. BLE macro exclusions require source-specific review.
Do not prescribe production widths from auxiliary formula screens.

Latest routing status is in [validation](validation.md); remaining modelling,
process and assembly requirements are in [production plan](production-plan.md).
