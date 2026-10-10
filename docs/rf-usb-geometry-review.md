# RF/USB geometry checkpoint — 2026-10-10

Stage 1 of `production-plan.md`; no layout or manufacturing copper changed.
Candidate: `build/fabrication-routing-quality-20261010/board.kicad_pcb`, SHA-256
`33adc8ec883a47288d467386e9e0c4992337eac120aa0909223fc6819cf4a270`.
Report: `build/engineering-pair-geometry-r2-20261010.json`.

## USB findings

CopperScript's generic pair inventory uses native straight segments, widths,
vias and filled adjacent copper, not source nominal gap. The 0.40 mm search gap
is an explicit candidate-search window, not an impedance/quality acceptance
limit. Only exactly parallel overlaps are counted, using interval unions.

| Path | Routed layers | Copper DP / DM length | Parallel overlap per member | Signal vias per member |
| --- | --- | --- | --- | --- |
| MCU USB | F.Cu | 27.478 / 25.589 mm | 25.069 mm | 0 |
| Modem USB | F.Cu + In2.Cu | 17.887 / 18.517 mm | 14.008 mm, on In2 | 2 |

Recognized parallel sections have **0.200000–0.200002 mm actual edge gap** and
0.18 mm widths. Thus nominal gap retention is not the primary issue. MCU
members differ by 1.889 mm of inventoried copper; modem members by 0.630 mm.
These are not qualified pin-to-pin path delay/skew values: pads, vias, electrical
length and topology need separate treatment. Nonparallel/breakout sections
must not be silently treated as the same uniform coupled line.

MCU F.Cu segments have full zero-margin projected coverage on In1 GND, separated
by 0.0994 mm dielectric. Modem surface segments fail that conservative coverage
screen on 3/4 segments per member. On modem In2, 4/12 segments per member lack
full projected coverage on **each** adjacent plane. This may include transition
antipads; identify the actual openings and return geometry before deciding on a
layout change. A coverage failure does not by itself quantify USB performance.

The In2 adjacent copper is In1 GND at 0.5500 mm and In3 V3V3 at 0.1088 mm.
Therefore an In1-only microstrip approximation is unsuitable. Model both
adjacent planes and unequal dielectrics, their local openings, vias/stubs and
GND-to-power-reference return paths. Do not automatically regard a nearby
power plane as a qualified ground return. Review whether to retain this routing
with proven returns or move it to a better-characterized layer.

Next: pin-to-pin topology/delay extraction, discontinuity modelling and reviewed
layer-specific solver evidence; then justified routing/width changes and fresh
DRC/export. No guessed impedance-driven width edits were made.

## GNSS manufacturer review

Reusable guidance and exact integration-manual provenance now live in CopperLib
`packages/parts/u-blox/max-m10s/integration-review.md` and `qualification.json`.
The cached manual is UBX-20053088 **R05, 28-Apr-2026**, not the older R04 search
index result. Its antenna-bias, grounding and typical supply figures were
rendered and visually inspected using the PDF review workflow.

The module's RF matching is integrated; this does not approve the host feed,
antenna, cellular coexistence or ESD. The tracker currently connects RF_IN
directly to J_GNSS and does not supply antenna bias. Antenna type/power and
cellular/BLE-to-GNSS coupling must be resolved before selecting bias/protection
or additional filtering. Preserve the approved BOM until such a change is
justified. The 3.3 V source wiring matches the typical shared VCC/V_IO and open
VIO_SEL arrangement; detailed layout and source datasheet hash remain pending.

## Provenance and release boundary

Library lock refresh was audited: only the MAX-M10S qualification JSON changed
in the locked asset inventory (1792 → 2226 bytes); no parts, footprints or macros
changed. Its new module checksum is
`sha256:d4502ec39225290030efa29c7a2106fad6b6107c291ab63f4aded14355b47690`.
Assembly provenance digest was refreshed without changing the 83 identities or
their approved flags. Cached documents/images are ignored, not redistributed.

New evidence/report bindings supersede earlier engineering checkpoints, not
the unchanged fabrication artwork. Qualification remains incomplete. The staged
plan still requires power inputs, exact modem guidance, solver/bench evidence,
independent CAM/DFM and human CPL review.

USB screening is currently auxiliary: the RF/power checkpoint does not itself
qualify USB performance. Add reusable interface design/simulation/bench contracts
and board bindings before treating a future all-pass checkpoint as approval of
the complete tracker. This remains an explicit step-1 release prerequisite.

## Verification

- 71 focused CopperScript pair/stackup/engineering/checkpoint/CAM tests passed.
- 8 focused CopperLib contract/MAX-M10S-footprint tests passed.
- 35 tracker tests passed, including approved BOM and pair-binding regressions.
- Current-source native pose/pad/net/placement/macro checks passed for 83 parts.
- Fresh native KiCad DRC: zero violations and zero unconnected items; board hash
  unchanged. Report: `build/drc-pair-geometry-20261010.json`.
- Refreshed assembly check: 83/83 exact, 83 reviewed, no issues; availability
  not checked. New `build/assembly-pair-geometry-20261010/assembly-review.zip`
  contains 43 BOM rows and 83 placements, with CPL still unapproved. It and the
  unchanged Gerber/drill ZIP pass archive-integrity checks.
- Fresh engineering report: 7 pass / 36 incomplete; CAM: 10 pass / 3 incomplete;
  checkpoint: 21 pass / 3 incomplete. All remain `qualified_release=false`.
  Reports are `build/engineering-pair-geometry-r2-20261010.json`,
  `build/cam-pair-geometry-20261010.json` and
  `build/qualification-pair-geometry-20261010.json`. No mandatory check failed;
  local coverage failures remain visible within auxiliary screening.

These are bounded regression runs, not a claim that the full upstream suites
or hardware qualification passed. No order, commit or push was performed.
