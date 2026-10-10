# Native-clean fabrication review — 2026-10-10

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

The bounded late-contact run is recorded in `routing-attempts.md`; it saved
`build/late-contact-routed.kicad_pcb` with V5 and two supply contacts pending.
The application finishing helper can resume that current-source candidate:

```console
uv run --locked python scripts/finish_routed_candidate.py --pcb build/late-contact-routed.kicad_pcb --route-v5 --output build/resumed-routed.kicad_pcb
kicad-cli pcb drc --refill-zones --save-board --format json --severity-all --exit-code-violations -o build/resumed-native.json build/resumed-routed.kicad_pcb
```

The helper uses real global guides when resuming V5. This specific end-to-end
resume command has not been rerun; the accepted V5 diagnostic used unbiased
local search, and the final checkpoint's strict source/macro/geometry checks
and native DRC were verified separately. Do not assume a heuristic rerun will
reproduce the same copper. Any remaining opens/errors are a failed candidate.
If native DRC reports only the known short dangling VSYS stub, its exact
report-identified ordinary segment may be cleaned; macro/critical tracks or
other warnings may not be waived:

```console
uv run --locked python scripts/finish_routed_candidate.py --pcb build/resumed-routed.kicad_pcb --native-report build/resumed-native.json --output build/finished-routed.kicad_pcb
kicad-cli pcb drc --refill-zones --save-board --format json --severity-all --exit-code-violations -o build/finished-native.json build/finished-routed.kicad_pcb
uv run --locked copper export-manufacturing build/finished-routed.kicad_pcb --kicad-cli kicad-cli --skip-independent-cam -o build/fabrication-review-new
uv run --locked python scripts/export_assembly_review.py --fabrication build/fabrication-review-new --output build/assembly-review-new
```

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
