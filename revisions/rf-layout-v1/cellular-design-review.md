# Cellular RF design review - 2026-10-12

**Review performed; outcome: changes required before RF design signoff.**
This is a source/geometry review, not full-path simulation, prototype approval,
regulatory approval or permission to order. No PCB copper, parts or release
locks were changed in this review. The original routed candidate is retained.

## Selected antenna and assembly boundary

Select **Taoglas FXUB16.07.0150AQ**, one external passive flex antenna per board,
with its factory **150 mm** cable and MHF I/U.FL-compatible connector to J_CELL.
Its manufacturer band table explicitly covers B1/B3/B7/B8/B20/B28 and
B38/B40/B41, including both directions for FDD. B20 includes the entire
791-821 MHz downlink; do not use a vague marketing frequency envelope as proof.
These bands are supported in the reviewed SIM7670G family specification.
Operator/SIM/firmware and exact-variant restrictions still need commissioning.

Reusable facts, source hash and qualification contract are in CopperLib's
`packages/antennas/taoglas/fxub16-07-0150aq/`. The
[manufacturer datasheet](https://www.taoglas.com/datasheets/FXUB16.07.0150AQ.pdf)
is SPE-24-8-235-A, dated 2024-09-24; pages 3-7 and 9-10 were inspected,
including band, mechanical, cable-direction and measured return-loss drawings.
It is not a JLCPCB placement item. Keep the antenna out of PCB BOM/CPL and
include it in the final external assembly manifest instead.

Mount on a non-metal wall and reserve at least **90400 by 15000 um**, with
**240 um** antenna thickness. The introduction says 90400 um while the drawing
says 90000 um. A **20000 um** metal/battery clearance allowance is an authored
prototype packaging provision, not an FXUB16 source minimum or a verified fit.
No enclosure CAD is selected. Confirm retention, bend radius, battery position
and separation from GNSS/BLE. Do not trim the cable; measured RF behavior varies
with cable direction. Published LTE peak gain reaches **4100 mdBi**; that is not
a blanket certification gain allowance. The higher **6320 mdBi** figure includes
other frequencies and must not be substituted as the LTE-only value.

[DigiKey Norway](https://www.digikey.no/en/products/detail/taoglas-limited/FXUB16-07-0150AQ/25622267)
lists the exact assembly, supplier identity `931-FXUB16.07.0150AQ-ND`.
The indexed stock snapshot was 476; a live Octopart lookup was quota-blocked.
Recheck availability before purchase. No antenna was purchased or ordered.

## Exact fabrication selection

Lock **JLC06161H-3313**, **NP-155F**, six layers, nominal **1600 um**, exterior
1 oz and interior 1/2 oz. The published L1-L2 prepreg is **99400 nm**.
[Stackup instructions](../../docs/stackup-selection.md) list every physical layer.
[`fabrication-selection.json`](fabrication-selection.json) binds the unchanged
library construction and the separate current calculator model by hash.
Require supplier confirmation of material/construction and controlled impedance.
The authored prototype request is **50 ohm with 10 percent tolerance**, plus a
coupon measurement. It is not an accepted JLCPCB order or calculator guarantee.
Loss data and order-specific process bounds remain unresolved.

The nominal masked grounded-coplanar feed uses **142 um** width and **201 um**
minimum top ground gap with In1.Cu GND beneath it. JLCPCB's calculator solves the
uniform nominal cross-section; rounded dimensions and large pad launches still
need a full-path field solution. Its 40640 nm copper model and 35000 nm published
construction copper are retained separately, not conflated.

## Source and actual copper review

Reviewed PCB:
`build/cellular-impedance-export-v2-20261012/native/verification-001/CopperAssetTracker.kicad_pcb`,
SHA-256 `08635abdaed273d276d3a971ef3668ee0c35fd1ff7c4e5d4c7ffea658fe7e9b1`.
Fresh selection composition and read-only geometry evidence are under
`build/cellular-design-review-20261012/`. Old manufacturing files are not
regenerated releases for this selection.
[`cellular-design-review.json`](cellular-design-review.json) binds exact input
and evidence hashes. `layout-inventory-v2.json` confirms the retained board's
91 placements, 908 tracks and 310 vias match the prepared source lands, poses
and immutable copper. The source text is unchanged from the routed revision;
the new library inventory is separately prepared and checked, not presumed
identical from matching source text. The older unbound inventory is retained
but is not the final source-bound review report.

Top copper and actual L2 ground were also rendered and visually inspected in
`build/cellular-design-review-20261012/layers/`. Both close-ups use the same
window, x = 1500..11500 um and y = 20000..29000 um. L2 remains continuous beneath
the cellular feed; the wider launches and bend remain explicit model regions.

- [x] Inspect modem ANT_MAIN pad 60 and connector pad 1; review actual rotation
  and physical lands, not component-origin distance.
- [x] Confirm **3089 um** total surface feed, **zero** signal vias, and both
  actual tracks at **142 um** width. SIM7672X's accepted related-family layout
  guidance limits ANT-to-connector PCB length to **20 mm**.
- [x] Review existing actual filled L2 GND coverage and ten uniform-section
  gap samples. The earlier seven launch-area deviations remain recorded.
- [x] Review both duplicated connector ground lands independently. The generic
  CopperScript checker finds a modeled connected top-copper path to an adjacent
  ground-layer return via for each, with nearest via center **1000 um** from pad
  center and annulus **75 um** from pad edge. These are not disconnected vias
  merely selected by net name. Polygonal joins do not qualify RF inductance,
  local ground webs or via-fence spacing.
- [x] Inventory actual power/clock/USB copper. Closest selected top-layer power
  copper is V3V8, approximately **2076 um** edge-to-edge from the signal copper
  including its lands. The nearest selected clock projection is SIM_CLK on
  In3.Cu, approximately **7946 um** away. V3V8/In2 and V3V3/In3 overlap the feed's
  XY projection behind L2 ground; zero projected distance is not a short or an
  interference failure. No universal RF spacing pass is inferred.
- [x] Review the one 45-degree direction change and both large pad launches.
  There is no signal-layer transition; neither bend nor launch is qualified by
  excluding it from uniform-section sampling.
- [x] Review Figure 30/32 and pp58-60 of the accepted SIM7672X V1.01 reference.
  The matching/DC-blocking block is on the antenna side of the illustrated test
  connector. J_CELL is an antenna disconnect, not that switched test connector.
  A direct cabled antenna is a deliberate topology adaptation requiring its own
  matching/protection/DC-isolation review, not a literal reproduction.
- [x] Review test access: disconnect the antenna and use a suitable U.FL adapter
  for conducted modem tests. Characterizing the PCB feed itself needs a separate
  fixture/unpopulated modem land and calibrated/de-embedded measurement. Never
  connect an unprotected VNA to a transmitting modem.

## Findings that block RF design signoff

1. **RF ESD protection missing.** CELL_RF directly joins the modem and J_CELL;
   the selected antenna does not establish integrated protection. The accepted
   modem reference recommends bidirectional, low-capacitance RF protection.
   Table 48 names Murata LXES03AAA1-154, INPAQ CES10201V05B0 and
   BilLSEMI BLE5V0CR05UB. These are source candidates, not approved/sourced board
   selections. Select an available exact device, check clamp/RF swing/loading,
   place it at the connector with a short return, then regenerate/route/review.
2. **Matching and DC isolation adaptation unresolved.** Figure 30 reserves
   two shunts and series elements, initially 0 ohm and 100 pF with shunts DNP.
   Do not invent final tuning values, assume the antenna contains these elements
   or infer module DC blocking from nominal 50 ohm. Establish the actual port/DC
   boundary, then implement justified support or record a defensible omission.
3. **Launch, bend and ground-return model missing.** No supported full-path
   field solver/model has been run. Solver executables checked were absent from
   PATH; this is not evidence that every possible tool is absent. Model actual
   pads, coplanar fill, vias, mask, material/process corners and any new support.
4. **Mechanical installation unverified.** Antenna selected, but no enclosure
   fit, battery/metal clearance or cable-retention evidence exists. Final antenna
   match, radiated performance and LTE/GNSS/BLE coexistence require hardware.

The review is complete as an inspection with actionable findings. The design
gate is **not passed**. Complete these adaptations, rerun the standard shared
source/placement/routing pipeline after electrical changes, obtain geometry-bound
simulation and supplier acceptance, then approve an exact engineering prototype
package. Prototype measurements remain a separate acceptance stage.

Reusable algorithms and metadata remain in CopperScript/CopperLib. No custom
tracker-local RF or routing repair algorithm was introduced.

[Cellular qualification plan](cellular-engineering-plan.json) binds the selected
external antenna and modem contracts to this inspection, stackup and source.
Its mandatory matching, reference-layout, simulation and bench evidence stays
open. This scoped cellular plan is not a whole-board production qualification.

The shared `assess-engineering` command was run against this exact PCB and plan.
[Retained assessment](../../build/cellular-design-review-20261012/engineering-assessment.json)
reports `incomplete`, with `qualified_release=false`. Projected L2 ground
coverage and both source provenance checks pass. Material loss/minimum via
plating, reviewed operating bounds and all required external RF evidence remain
incomplete. The nonzero command exit is the expected qualification gate, not a
route failure.

Verification: 76 focused CopperScript regressions, 15 focused CopperLib tests
and six real tracker composition tests passed, alongside four review-binding
tests including retained artifact checksum checks. The much larger full CopperLib
integration suite was stopped and is not reported as passed. The source-bound
native review completed without changing PCB bytes. This test evidence is
software/geometry verification, not a hardware RF approval.
