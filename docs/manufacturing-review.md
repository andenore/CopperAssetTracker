# Native-clean fabrication review — 2026-10-10

New solver work uses `make route-review` and CopperScript's shared `route-board`
pipeline. Project-local finishing commands are retired after equivalent shared
closure; historical files below remain unchanged. Release locks and the pinned
manufacturing workflow are not upgraded by that benchmark result.

Historical checkpoint: the later routing-quality changes relocated the level
translator and its bypasses. The retained files below are unchanged and do not
certify current source intent. See [routing-quality review](routing-quality.md)
for the separate new routing candidates and their native checks.

The 100 × 80 mm, six-layer routing candidate has zero open connections and
zero native DRC violations after KiCad 10.0.6 zone refill. It is **not an
approved production release**. Native closure does not qualify the schematic,
device models, RF performance, battery safety, power transients or assembly.

## Files

- `build/finished-routed.kicad_pcb`: finished board at this historical checkpoint.
- `build/finished-native.json`: independent filled-board connectivity/DRC.
- `build/finished-routed.geometry.json`: source-contract geometry check;
  source zones remain refill intent, not invented filled copper.
- `build/fabrication-review-20261010/gerbers-drill.zip`: all six copper
  layers, both masks/paste/silkscreens, outline, PTH and NPTH drills.
- `build/fabrication-review-20261010/manufacturing-package.zip`: native
  project, artwork, drills, IPC-D-356 netlist, positions, checksums and manifest.
- `build/assembly-review-20261010/assembly-review.zip`: **candidate**
  JLC-format BOM/CPL (43 identities, 83 placements), status and checksums.
  No selection was approved. Do not treat these CSVs as a reviewed PCBA order.
- `build/final-preview/top.png`: top-copper native preview, inspected for
  gross placement/fill errors, not independent CAM qualification.

Manufacturing export reruns strict native refill/DRC on its staged copy and
inventory-checks all 13 Gerber layers, drills and the manufacturing netlist.
X2 FileFunction records identify L1 through L6; through-drill metadata spans
layers 1–6. The archive retains source rules and footprints. Its manifest has
`qualified_release=false` and `assembly_bom_included=false`. The separate
candidate assembly data preserve native CCW rotations/common origin and exact
83-reference equality; supplier-specific rotation offsets are **not guessed**.

## Reproduce from a retained native checkpoint

Generated files are ignored build artifacts. Keep the native checkpoint and
reports if reproducing this exact route; a new automatic placement/reroute is
a new candidate and must pass its own checks. The locked source/library assets
and local editable CopperScript changes must also be retained. No generic
components or compiler algorithms are copied into this project.

The historical late-contact result is recorded in `history/routing-attempts.md`;
its project-specific finishing/cleanup commands have now been retired. Retained
native boards and reports are unchanged, and tracked scripts remain recoverable
from Git history. New candidates use the shared pipeline:

```console
make route-review REVIEW_COPPER="python -m copperscript" REVIEW_DIR=build/new-review
```

Activate current reviewed CopperScript first. Both standard balanced and thorough
Tracker runs achieved current-source native closure on 2026-10-11; see
[exact evidence and retirement scope](autonomous-routing-review.md). This does
not upgrade the pinned manufacturing workflow or approve the separate production
revision. Never copy an old checkpoint's approval flags onto a new reroute.

Native export refuses nonzero opens or violations. `--skip-independent-cam`
acknowledges an **unqualified file-generation export**, never a release waiver.
Use the installed absolute KiCad executable on Windows. The normal `make
manufacturing` assembly-review gate remains closed.

## Required before an order

Executable CAM/RF/power assessment and current-input checkpoint commands are now
documented in [engineering qualification](engineering-qualification.md), with
board-specific inputs in `engineering-plan.json`. They preserve all existing
unapproved flags and do not alter this retained routing/manufacturing candidate.

Review every exact component's package, pin mapping, ratings and selection;
verify all 83 placement rotations, polarity and centroids in the JLC preview.
Recheck live stock. Finish exact-modem/MCU/GNSS support and ESD review; qualify
the stackup, matching/feed impedance and USB return paths; verify power burst
delivery, MLCC derating, charger thermals and battery/NTC/polarity. Complete
independent CAM/DFM and mechanical/panel requirements. Preserve the unapproved
flags until actual review evidence exists. No order or publication was made.
