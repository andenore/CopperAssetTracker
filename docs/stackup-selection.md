# Selected stackup and next layout review — 2026-10-10

Select **JLC06161H-3313**, nominal 1.6 mm FR4, 1 oz outer / 0.5 oz inner copper.
Its reusable profile is in CopperLib
`packages/profiles/jlcpcb/jlc06161h-3313/stackup.json`, selected and content-bound
by `engineering-plan.json`. Exact source HTML hashes/locators are retained there.
This selects supplier construction, not a new plane/net assignment. Current
board order remains F.Cu / In1.Cu / In2.Cu / In3.Cu / In4.Cu / B.Cu.

Published dielectric spacings, top to bottom: 0.0994 / 0.55 / 0.1088 / 0.55 /
0.0994 mm. Published Dk values: 3313 4.1, core 4.6, 2116 4.16. The construction
sums to 1.5384 mm, within the published 10% finished-thickness tolerance around
nominal 1.6 mm. Keep those spacings; do not stretch them to fill a nominal sum.
The native PCB's existing nominal thickness remains 1.6 mm. The native file does
not yet contain this detailed supplier construction; specify the exact profile
at order/impedance review, rather than relying on an unspecified default.

JLC publishes average hole plating of 18 um, not a guaranteed local minimum.
Minimum finished barrel plating and dielectric loss tangents remain unresolved.
The full stackup qualification gate therefore remains incomplete even though
the construction has been selected. No measurement or supplier confirmation is
invented. [Stackup](https://jlcpcb.com/impedance),
[capabilities](https://jlcpcb.com/capabilities/pcb-capabilities).

## Actual-route screening findings

CopperScript inventories the actual exported PCB, not hypothetical source rules.
Isolated microstrip estimates ignore solder mask, coplanar copper, local pads,
roughness and matching structures. They do not replace field-solver evidence.

| Route | Actual geometry | Finding / required action |
| --- | --- | --- |
| LTE CELL_RF | 0.20 mm F.Cu; 35.586 mm total segments | Filled In1 GND covers the conductor; isolated estimate 43.59 ohm. Review 50-ohm feed geometry, matching/support and length against the exact modem guide. |
| GNSS_RF | 0.20 mm F.Cu; 14.888 mm total segments | Same 43.59-ohm isolated estimate and geometric coverage. Review feed/ESD/antenna integration and exact guide. |
| MCU USB DP/DM | 0.18 mm F.Cu throughout | In1 coverage passes the minimum geometric screen. Single-line estimate 45.99 ohm is NOT 90-ohm differential qualification; actual gaps and discontinuities need coupled modelling. |
| Modem USB DP/DM | 0.18 mm; 4 F.Cu + 12 In2.Cu segments per member | Three of four F.Cu segment envelopes/member lack full projected In1 coverage. Inspect launch/antipad geometry; do not infer a faulty bus solely from this screen. Inner routing requires its own embedded/stripline and transition model. |
| BLE NRF_RF_ANT | 0.25 mm F.Cu, owned RF macro | Intentional reference keepouts prevent the isolated solid-reference premise. No routed impedance estimate is claimed; review the reference/matching adaptation as a whole. |

The isolated formula puts a 0.15 mm outer microstrip near 50.14 ohm on these
nominal inputs. This is a **solver candidate**, not a prescribed production width.
No RF matching values, macro copper or routed widths were changed from screening.
Fresh coupled/field-solver results may require layout changes before final CAM.

## Current evidence / approval boundary

User-directed BOM approval is recorded in `bom-approval.md`: 83/83 exact approved
selections, 43 identities. New BOM/CPL review data are in
`build/assembly-bom-approved-20261010/assembly-review.zip`; placement approval,
supplier rotations/centroids/polarity, live stock and the order remain pending.

Latest reports (retained separately, never modifying fabrication archives):

- `build/engineering-stackup-selected-r2-20261010.json`: 7 pass / 36 incomplete;
  seven separate screening results, not substitutes for qualification checks.
- `build/cam-stackup-selected-r2-20261010.json`: 10 pass / 3 incomplete.
- `build/qualification-stackup-selected-r2-20261010.json`: 20 pass / 3 incomplete.

The native PCB/Gerber package remains the exact review candidate at
`build/fabrication-routing-quality-20261010` (PCB SHA-256
`33adc8ec883a47288d467386e9e0c4992337eac120aa0909223fc6819cf4a270`).
Zero native opens/violations remains its existing verified condition, not RF,
power, CAM or hardware approval. Earlier qualification reports are historical
after the plan/library/BOM/algorithm changes. All release flags stay false.

Next: model RF feeds and both USB layers/launches, obtain the actual pack/NTC and
temperature envelope, then complete rail-current/MLCC/transient/thermal review.
Independent CAM/DFM and prototype measurements remain separate release gates.

Verification: 53 focused CopperScript stackup/engineering/CAM/checkpoint tests
passed; all 34 tracker tests (including 28 subtests) passed. The new assembly
archive and unchanged Gerber/drill archive pass ZIP integrity checks. Exact
before/after selection comparison confirms that only the reviewed flags and
library-provenance digest changed in `assembly.lock`. All fresh report bindings
pass; qualification remains incomplete, not failed or waived.
