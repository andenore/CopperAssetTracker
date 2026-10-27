# RF layout review revision

Source-only composition, not a routing repair or an RF-qualified release.
Use `scripts/build_battery_revision.py --modem-power --rf-layout` with explicit
local CopperLib and footprint roots, then the standard CopperScript pipeline.
Old review outputs and canonical release locks remain unchanged.

The Nordic anchor and its authored fixed support group move together by 4 mm
right and 6 mm up. The unchanged 6500 um square antenna ground/via exclusion
then occupies x = 93500..100000 um and y = 0..6500 um, opening onto both
outer board edges. The antenna origin is x = 98500 um, y = 3250 um.
CopperLib owns the managed-footprint macro; CopperScript v0.5 checks its
declared full-edge openings. Matching strokes, isolated NC land, prescribed
Nordic ground returns and all six-layer exclusions are unchanged.

Evidence: Johanson 36S0021A Rev. 4.0 (2024), pages 2-3, SHA-256
`c11a1866c9fd04bad6dcbbd40cfdfbec067c731e47ba83f4e58b56c0e4c9dfa0`.
This is an adaptation of its corner concept, not vendor CAD or tuned values.

GNSS review uses MAX-M10S Integration Manual UBX-20053088 R05, pages 77-81,
SHA-256 `5a7510ef84f7e2757c57e362a25e3c16bcf8c80af5a4f70790c2e51032dbcd13`.
RF_IN is internally matched to 50 ohm with DC blocking, notch/LNA/SAW filtering.
Do not add an arbitrary matching network to the receiver input. The external
GNSS antenna type is user-selected **passive** (`antenna-selection.json`). No
board-powered bias injection or externally powered active antenna is required.
The exact passive antenna/cable, LTE coexistence filtering and connector ESD
still require review; selecting the type does not qualify an antenna model.
The shared router should shorten the feed, retain F.Cu/no-via intent and check
actual ground coverage after refill. A 200 um width is not proof of 50 ohm.

Open gates: actual JLCPCB laminate/dielectric and RF impedance calculation,
return-plane/via-fence review, LTE/GNSS antenna selection and coexistence,
antenna tuning, enclosure/ground shape, RF bench and complete prototype tests.
These are not cleared by ERC, a corner geometry check or zero native DRC.

Preflight review output: `build/rf-preflight-20261012/`. The 91-part source
passes ERC and shared placement. The measured historical GNSS feed comparison
accepts 5154 um instead of 14888 um, on F.Cu with zero vias, using shared
critical routing acceptance and preserved macro copper. An isolated RF macro
refill has zero native violations/opens, positive ground-fill controls and
sampled exclusions on all six layers; its 22 immutable copper objects remain.
This is not a full-board routed/filled candidate or an impedance result.
The passive GNSS choice clears the antenna-type prerequisite for full routing.

Earlier full-run review: `build/rf-passive-full-20261012/`, with exact frozen inputs in
`build/rf-passive-inputs-20261012/`. The standard locked/offline router connects
all 61 ordinary nets and both USB pairs. Independent source/native readback
confirms 91 components, six layers, 907 tracks, 318 vias and 21 of 21 surface
decoupling connections. The GNSS feed is 5154 um long with no vias.

That earlier candidate is **incomplete**: independent KiCad DRC reports zero violations
but one remaining open between In3.Cu V3V3 fill fragments. Bounded shared feedback
closed the V3V8 open but did not close V3V3. The prior clean board, canonical
source and release locks remain unchanged. No production exports or refreshed
showcase figures are claimed from this incomplete run. See the run's
`independent-checkpoint.json` and `route-rf-passive.json`; generic fill-bridge
investigation remains on the CopperScript visual-review plan.

## Latest closed routing review

`build/rf-fill-components-full-v2-20261012/` is a fresh standard locked/offline
six-layer run, with exact compiler/library/source inputs frozen under
`build/rf-fill-components-inputs-v2-20261012/`. The fix belongs in CopperScript:
native-fill anchors are sampled across electrical components and accessible
layers, not merely different polygons. Already-connected fragments do not
receive redundant bridges, and unchanged native-rejected trials are cached
conservatively. No tracker-specific routing code or extra source constraint was
added; the configured trial/search bounds are unchanged.

The V3V3 bridge is accepted on In3.Cu in the first trial; shared dependency repair
reroutes SIM_IO/SIM_RST/SIM_VCC and preserves the immutable prefix. V3V8 closes
on In1.Cu in the third trial. Independent exact-source/native readback and KiCad
DRC confirm 91 components, six layers, 925 tracks, 326 vias, zero opens and zero
violations. All 61 ordinary nets, both USB pairs and all 21 surface bypasses
are connected. GNSS_RF remains 5154 um long on F.Cu with zero vias.

Evidence: `route-rf-passive.json`, `run-inputs.json`, `run-result.json`,
`independent-checkpoint.json` and `independent-native-drc.json` in the latest run.
The filled review board is `native-rf-passive/verification-003/CopperAssetTracker.kicad_pcb`,
SHA-256 `90ad07b17c793ae4413d84f6a828e6c29596da587810363bcb52c50fa341f7f6`.
Canonical source/locks and prior candidates are unchanged.

This is **routing closure, not production approval**. Electrical RF/USB/power
requirements remain blocked; native fill resolves the three deferred bare-copper
zone observations, not those electrical requirements. The five-region visual
review, refreshed showcase figures, antenna/cable/ESD/coexistence review,
independent CAM, changed assembly/CPL review, prototype measurements and final
release approval still remain. No new production exports are claimed.

## Cellular connector and nominal impedance revision — 2026-10-12

- [x] Inspect the actual SIM7670G ANT_MAIN land: pad 60, west edge at
  x = 8000 um, y = 24000 um with the current modem rotation.
- [x] Move J_CELL from y = 26100 um to y = 25300 um, retaining x = 4400 um
  and rotation = 180 degrees. Its signal land faces the modem. Move the four
  local bypasses upward by 800 um to make room; retain their pin-associated
  3 mm bounds, orientation and via-free routing intent. The reservoir is unchanged.
  A straight y = 24000 um connector placement conflicts with the bypass bank's
  real courtyards; no courtyard or distance rule was waived to force it.
- [x] Check JLCPCB's current calculator on standard JLC06161H-3313, L1
  coplanar single-ended over L2, 50 ohm, 1 oz exterior / 0.5 oz interior,
  nominal 1600 um order thickness and 201 um input ground gap.
  It returns width = 141986 nm and ground gap = 200660 nm. Source geometry
  rounds these to 142 um / 201 um in `cellular-feed.copper`.
- [x] Fix native clearance export generically in CopperScript. The same-stem
  `.kicad_dru` keeps the RF clearance during native refill; a default-control
  regression confirms native 90 um versus explicit 201 um gaps.
- [x] Complete the fresh full-board run and independent source/native check in
  `build/cellular-impedance-full-20261012/`.
- [x] Retain the corrected source-matched export/refill under
  `build/cellular-impedance-export-v2-20261012/`, with unchanged explicit routed
  copper, 91 parts, six layers, 908 tracks, 310 vias, all 21 surface bypasses,
  zero native opens and zero native violations.
- [x] Compare actual uniform-section ground gaps and adjacent L2 coverage.
  Ten uniform-section samples measure 201500..201501 nm gaps, within the
  declared 1000 nm geometry-screen tolerance around the 201 um source minimum.
  The whole conductor projection and an authored 300 um reference margin are
  covered by actual In1.Cu ground fill. This margin is not a vendor/solver bound.
- [ ] Review excluded pad launches/bends, connected ground-via returns,
  matching/ESD boundary and complete-path RF behaviour.
- [ ] Complete full RF/process/enclosure and prototype qualification.

Calculator evidence/settings are in `cellular-impedance-calculator.json` and
`jlc-cellular-coplanar-20261012.jpg`. The standard tab now labels its finished
thickness as 1540 um with 10 percent tolerance; that is not a new nominal order
choice. Keep the published 99400 nm L1-to-L2 prepreg separation; do not stretch
dielectrics to make the construction sum equal the nominal 1600 um order label.

The [JLCPCB guide](https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator)
uses NP-155F for six layers, with mask and trapezoidal etch parameters. Its
40640 nm exterior copper model differs from the 35000 nm construction-table
entry; the earlier isolated-microstrip approximation must not silently substitute
for this model. The guide's material must be selected/confirmed when ordering.
The calculator's numerical 0.5 percent setting is not a manufacturing guarantee.
142 um / 201 um is **nominal 50 ohm design intent**, not a measured or
full-board RF-qualified result. No production gate is cleared by this screen.

The corrected filled review PCB is
`build/cellular-impedance-export-v2-20261012/native/verification-001/CopperAssetTracker.kicad_pcb`,
SHA-256 `08635abdaed273d276d3a971ef3668ee0c35fd1ff7c4e5d4c7ffea658fe7e9b1`.
The cellular feed is 3089 um long instead of 3420 um, on F.Cu with zero vias.
The signal land is x = 5450 um, y = 25300 um. Both connector ground lands have
a nearest GND via 1000 um away by centre distance; this inventory does not
qualify an electrically connected RF via fence.

`reexport-result.json`, `plane-verification.json`, `independent-native-drc.json`
and `cellular-rf-review.json` bind the exact compiler, source, native PCB, rules,
stackup, calculation screenshot and measurement algorithms. The first isolated
compiler snapshot accidentally omitted the RF rule from its native rules file;
its routing-closed PCB is **superseded for impedance evaluation**. The corrected
snapshot was tested directly, then the shared backend re-exported this turn's
source-matched copper and refilled it. No tracks, vias or poses were hand-repaired.
Keep the corrected `.kicad_dru` and `.kicad_pro` with the retained PCB.

The first 22-sample screen is retained, including seven deviations around the
large launches. A separate ten-sample screen excludes source-derived land
bounding circles plus clearance/half minimum fill width and a declared bend
region. Those exclusions are explicitly unqualified, not erased failures:
uniform sections match the selected cross-section; the entire connector-to-modem
path has **not** been established as 50 ohm. No matching network is presumed
unnecessary or silently supplied by an external antenna assembly.

## LTE antenna / exact stackup design review - 2026-10-12

The [cellular design review](cellular-design-review.md) selects Taoglas
**FXUB16.07.0150AQ**, a passive cabled antenna covering the reviewed EU LTE bands,
and locks JLCPCB **JLC06161H-3313 / NP-155F** in
[`fabrication-selection.json`](fabrication-selection.json). External antenna
facts and the fabrication models remain library-owned; source composition
copies their exact hashed companion documents into `rf-library-evidence/`.

The new read-only build evidence is under `build/cellular-design-review-20261012/`.
The review outcome is **changes required**, not RF-approved: RF ESD and matching/
DC-isolation adaptation are unresolved, launches/returns need field modelling,
and antenna enclosure/bench qualification is absent. The original routed PCB is
unchanged; no new production Gerbers, orders or release approvals are claimed.

> `scripts/build_battery_revision.py` is retired (it read private CopperScript
> internals); recover it from Git history to rebuild this revision.
