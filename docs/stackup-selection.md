# Selected stackup

Select JLCPCB **JLC06161H-3313**, nominal **1600 um**, **NP-155F** material,
outer 1 oz / inner 1/2 oz. The RF revision locks the exact choice in
[`fabrication-selection.json`](../revisions/rf-layout-v1/fabrication-selection.json).
Do not choose `No requirement`, a different suffix, or substitute laminate.
Library-owned `packages/profiles/jlcpcb/jlc06161h-3313/stackup.json` records exact
source hashes/locators. Bind the selected profile to each revision's engineering
plan; it does not by itself set plane nets. Layer order is
F.Cu / In1.Cu / In2.Cu / In3.Cu / In4.Cu / B.Cu.

Published dielectric spacings are 99400 / 550000 / 108800 / 550000 / 99400 nm;
Dk values are 3313: 4.1, core: 4.6, 2116: 4.16. Construction totals 1538400 nm,
within published 10% tolerance around nominal 1600 um. Do not stretch dielectric
spacings to force the nominal total. Specify the exact construction in fabrication
and impedance review; a nominal native-board thickness is insufficient.

| Layer / separator | Published construction thickness |
| --- | --- |
| L1 / F.Cu | 35000 nm |
| 3313 prepreg | 99400 nm |
| L2 / In1.Cu | 15200 nm |
| Core | 550000 nm |
| L3 / In2.Cu | 15200 nm |
| 2116 prepreg | 108800 nm |
| L4 / In3.Cu | 15200 nm |
| Core | 550000 nm |
| L5 / In4.Cu | 15200 nm |
| 3313 prepreg | 99400 nm |
| L6 / B.Cu | 35000 nm |

For CELL_RF use masked grounded coplanar on F.Cu over adjacent In1.Cu GND:
nominal 50 ohm, 142 um source width, 201 um source minimum ground clearance,
no signal vias. Request controlled impedance with an authored 10 percent
prototype fabrication tolerance and coupon measurement; supplier acceptance
has not been received. Actual gaps, not just minimum clearance, matter.
USB/GNSS/BLE channels need their own model and process requirements.

JLCPCB's calculator uses NP-155F, mask and trapezoidal etched-trace parameters.
Its exterior copper model is 40640 nm, not the construction table's 35000 nm.
The reusable `calculator-model.json` companion preserves that distinction;
do not overwrite the construction profile or stretch dielectrics. The current
calculator standard labels finished thickness as 1540 um with 10 percent
tolerance. Neither that label nor numerical iteration tolerance is an order
acceptance or a measured impedance result. See the
[calculator guide](https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator)
and the [cellular design review](../revisions/rf-layout-v1/cellular-design-review.md).

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
