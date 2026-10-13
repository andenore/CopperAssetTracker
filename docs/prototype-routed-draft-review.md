# Routed draft review — 12 October 2026

This is inspection of the first v2 failed draft, not a final fabrication board
or RF/USB/power approval. Retain the failed evidence while stronger candidates
run. Item 6 mechanical fit/test-access work is excluded.

Native board:
`build/prototype-preorder-v2-20261012/native/verification-001/CopperAssetTracker.kicad_pcb`.
SHA256: `74369182a220e335fac00673c18259075bd99606614bfe66c392eeee6d4e318c`.
The source has 97 physical components / 95 fitted selections and zero ERC
findings. Ordinary routing leaves USER_LED_2 open. Native DRC has three opens
(USER_LED_2, V3V3, V3V8), two dangling-track findings, and zero isolated zones.
No manufacturing export is permitted from this draft.

## RF observations

The shared read-only engineering assessment inventories every cellular/GNSS net
in `engineering-draft-all-rf.json`. All four networks use 142 um F.Cu copper.
Their projected conductor envelopes have actual filled In1.Cu GND coverage;
the host CELL_RF and GNSS_RF contracts additionally pass the authored 300 um
projection margin. Projection is not electrical return inductance or impedance
qualification. The nominal isolated-microstrip screen gives about 51 ohm;
coplanar copper, mask, pad launches, component fields, tolerance and antenna
installation are not included, so every impedance screen stays incomplete.

| Actual pad-centre route section | Copper length | Signal vias |
| --- | --- | --- |
| Modem RF pad 60 to RF-link pad 1 | 3540 um | 0 |
| RF-link pad 2 to DC-block pad 1 | 2000 um | 0 |
| DC-block pad 2 to LTE connector pad 1 | 6567 um | 0 |
| GNSS RF pad 11 to GNSS connector pad 1 | 6999 um | 0 |

Lengths are rounded for display. Component internals are excluded. The TVS-to-
connector paths are 3575 um cellular and 1900 um GNSS; they overlap the main
feed, not additional series lengths. Both DNP shunt lands remain physical RF
branches and must be included in the launch/matching model. No RF signal vias
were introduced. Unique centreline paths are geometric screening, not copper-
connectivity or propagation-delay proof.

The additional generic RF layout inventories passed the read-only source/native
land, pose and immutable-copper checkpoint for all 97 physical components and
all three macros. Each connector has two physical ground lands; both join one
modeled top-ground component with spanning In1.Cu ground returns. The nearest
modeled return via is 1000 um from each land centre and 75 um from its copper
edge. These are conservative geometric inventories, not an RF return-inductance
or connector-launch approval. Cellular V3V8 copper has zero XY-projection gap
on In2.Cu behind the intervening In1.Cu reference, and 1154 um top-layer edge
gap; neither value alone establishes coupling or a short. The reports remain
`incomplete` and `qualified_release=false`.

## Assembly observations

The shared candidate writer has matched 95 normalized BOM/CPL references to
native placement data; both DNP shunts are excluded. Native rotations are
preserved, not converted using guessed supplier offsets. Catalogue confirmation
requires Standard PCBA and modem X-ray. Exact-order pin-1/rotation and special
footprint process confirmation remain required.

The plotted native F.Cu/F.Fab/Edge.Cuts PDF and PNG were visually inspected.
They show the relocated cellular connector beside the modem RF support and
the passive GNSS connector beside its receiver/protection circuit. The combined
fab-layer reference text is crowded; this is not evidence about final silkscreen
or mask/paste. The draft image is not generated Gerber inspection. Full layer,
drill, mask/paste and supplier artwork inspection follows a successful native
candidate and fresh manufacturing export.

![Failed native draft; not for fabrication](../build/prototype-preorder-v2-20261012/review-draft-top.png)

## Remaining gates

Finish ordinary routing and actual filled plane contacts; rerun native DRC and
source identity. Review actual RF cross-section/ESD returns and complete USB
channel modelling. Resolve the electrical and sourcing findings in the companion
reviews. Obtain the GNSS experiment choice, exact prototype risk acceptance,
supplier process/stock confirmation and final package approval. No bench result,
fabrication approval or simultaneous LTE/GNSS qualification is claimed.
