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
