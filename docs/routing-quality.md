# Routing-quality review

The generic checklist and implementation are in CopperScript
`docs/routing-quality-todo.md`. No compiler algorithms are copied into this project.

- [x] Replace the central hole in the top GND intent with a compatible host pour.
- [x] Verify `build/routing-quality-20261010/ground-merged.kicad_pcb` after native
  refill: zero DRC violations/opens and zero gap to both owned regulator GND zones.
- [x] Identify 14 bypass capacitor/protected-pin associations in `board.copper`.
- [x] Probe direct surface candidates against the existing real routing; eight
  are blocked (C_CC, C_ACCEL, C_LEVEL_A/B, C_STATUS_A/B, C_DEC4, C_NRF_VDD3).
- [x] Revisit those fixed poses and routing obstacles with pad-level placement.
- [x] Generate a fresh complete route with the new generic escape/bypass defaults;
  inspect actual cap paths, vias, adjacent common-net exits and fallback geometry.
- [x] Generate new fabrication/qualification evidence only after that validation.
- [ ] Review remaining ordinary same-net area/stitching X junctions and extend
  the generic area-route preference without rewriting owned macro copper.
- [ ] Complete independent CAM, RF/power/battery and assembly qualification.

The ground-only candidate does not rewrite existing via escapes or relocate
passives. Its ten proposed decoupling surface segments were not committed.
Prior manufacturing packages are retained unchanged; old qualification reports
are historical after the source changes. The assembly provenance digest was
refreshed, but all 83 exact selections remain unreviewed. Nothing was ordered.

## Follow-up local review

The level translator now sits 3 mm lower to leave room below the modem. Four
translator bypasses use generic pin-associated placement instead of fixed poses.
CopperScript's access-aware placement and straight-lead/local surface search
connect all 13 ordinary bypass associations in the separate local review, with
zero local-path vias and no pending associations; DEC3 remains specialized.
`build/decoupling-review-20261010/review.json` records source/algorithm/seed hashes
and actual path lengths (1.640–3.321 mm). Reproduce it with:

```powershell
uv run --locked python scripts/review_decoupling.py --pose-seed build/routing-quality-20261010/ground-merged.kicad_pcb --output build/new-local-review --movable C_LEVEL_A --movable C_LEVEL_B --movable C_STATUS_A --movable C_STATUS_B
```

This imports ONLY historical poses, never historical ordinary copper. Current
fixed source intent, locked footprints and immutable macro assets win. Output
directories are never overwritten. Native refill of the local review has no
clearance errors, one expected unfinished macro enable-port warning and 106
opens elsewhere: it is deliberately NOT a routed fabrication candidate.

The first fresh all-source routing attempt passed ordinary package exits and RF/clock
groups but initially fails the modem USB differential pair. Its ordinary area
route is correctly gated; full routing/fabrication evidence remains outstanding.
A second preflight at the legal local-review poses passes all 82 ordinary exits,
every critical group including both USB pairs, and all bypass reservations. The
pose-preserving full comparison uses `scripts/route_review_candidate.py`, invoking
only CopperScript algorithms. It never copies seed copper or overwrites a review.
Reading the saved local native PCB through the exact current-source guard also
confirms all thirteen surface chains (26 terminals, no proposed repair tracks).
The earlier ground-only PCB and qualification reports are historical, not
current-source release certificates after relocating the translator.

## New native-clean review files

The pose-preserving full attempt needed repairs for V5 and GNSS_TIMEPULSE, then
the debug-header V3V3 contact. CopperScript now retains verified exits on partial
ordinary nets: releasing V5's failed-net escapes allowed later stitching to block
charger pin 13. Rebuilding the five dense V5 exits at the pre-stitching current-
source area checkpoint connects that rail without weakening source rules.
The debug-header contact succeeds with an 8 mm computational search radius.

All intermediate inputs remain in separate `build/routing-quality-*-20261010`
directories. The native-identified ACCEL_INT dangling tail (including reversed
duplicate runs) and its orphan via were conservatively cleaned with CopperScript
algorithms; exact source/macro ownership and terminal connectivity were checked.
No macro or critical copper was pruned. The new final export passes KiCad 10.0.6
refill with **zero violations and zero unconnected items**.

- `build/routing-quality-clean-20261010/board.kicad_pcb` and `native-drc.json`:
  native-clean current-source input checkpoint.
- `build/fabrication-routing-quality-20261010/board.kicad_pcb` and `drc.json`:
  actual staged/exported board and clean native report.
- `build/fabrication-routing-quality-20261010/gerbers-drill.zip`: six copper
  layers, masks/paste/silkscreens, outline and PTH/NPTH drills.
- `build/fabrication-routing-quality-20261010/manufacturing-package.zip`:
  native board/project, manufacturing artwork/netlist, positions and checksums.
- `build/assembly-routing-quality-20261010/assembly-review.zip`: candidate
  BOM/CPL, 43 identities / 83 placements, **zero approved selections**.
- `build/cam-routing-quality-20261010.json`: 10 pass / 3 incomplete.
- `build/engineering-routing-quality-20261010.json`: 7 pass / 36 incomplete.
- `build/qualification-routing-quality-20261010.json`: 19 pass / 3 incomplete.

The exported PCB SHA-256 is
`33adc8ec883a47288d467386e9e0c4992337eac120aa0909223fc6819cf4a270`.
Its exact-source native readback confirms all thirteen ordinary F.Cu bypass
chains (26 terminals), no pending links and zero proposed replacement tracks.
Both regulator ground fills meet the host fill with zero gap and 58.638 mm of
shared boundary each. Existing surface paths, not new proposals, are the proof.

There are still **11 strict same-net X junctions** in the exported geometry: two
inside immutable regulator GND copper and nine ordinary area/stitching junctions
(V3V3 4, V1V8_MODEM 2, GNSS_TX 1, MCU_SWDCLK 1, NRF_RESET 1). These are electrically
legal, but the area-topology quality task remains open. The package escape fix
does not claim to eliminate every crossing in an ordinary area route.

Independent parser/vector CAM and fabrication geometry remain incomplete.
Reviewed stackup/operating inputs, matching/layout review, impedance/transient
simulation and RF/power/battery prototype evidence remain required. All new
archives are **review artifacts, not production-approved files**;
`qualified_release=false` and all selection review flags are preserved.
Previous fabrication/assembly archives remain unchanged and historical.

Subsequent user instruction selects JLC06161H-3313 and approves the exact BOM.
Current selections are now reviewed under that assumption; old archives retain
their historical flags. See `stackup-selection.md` for new bound reports and
actual RF/USB width/reference findings. The native copper remains unchanged;
CPL, CAM, RF/power/battery and prototype qualification are still pending.

Current follow-up tests: 274 focused CopperScript checks passed, 3 optional skips;
34 tracker tests plus 28 subtests passed. No broader full-suite claim is made.
