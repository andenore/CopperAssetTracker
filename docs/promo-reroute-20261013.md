# Fresh route and promo figures — 13 October 2026

Scope: `promo-reroute-20261013`, a source-matched routing review, not a
manufacturing export, production approval or approval to order. The earlier
manufacturing candidate and its evidence are retained unchanged.

## Inputs and result

- Tracker source: `a01ece38e29f12ee9bd98a020594b3b49ac533bd`.
- Reviewed compiler merge: `78138ba9a772a915471cbe3820d9501a25475582` (reviewed RF/CAM work plus upstream
  `b915dd353c1e3a4e9fd983f82d7c2cc0a1bbcdfa`).
- Library merge: `39e86f334de5a4279bbdbda9384ee39c5bbcb55c`.
- Six layers, 100 × 80 mm; 97 physical / 95 fitted components.
- All 61 ordinary nets connected; ground and supply planes verified by native
  refill. 968 tracks, 340 vias; 21/21 decoupling feeds surface-connected.
- KiCad 10.0.6: zero included violations, zero unconnected items, zero islands.
- Source/native checkpoint passed: pad nets, lands, poses and all three immutable
  physical macros match. Macro bindings come from `.copper` declarations, not
  duplicate CLI scene arguments. No historical ordinary copper or pose seed was
  imported, and no board-specific routing repair was used.

Accepted native board:
`build/promo-reroute-20261013/route-03/native/verification-003/CopperAssetTracker.kicad_pcb`.
Keep its native project directory, footprint library and `fp-lib-table` together.
PCB SHA256: `935320e5d9e65f1438de27f233fec3428af5fcd1e74ccaa69167fe74261f31a8`.
Native DRC SHA256: `d275d1fa20996c4a368ea385f042ac5e37da9d4cc95ba38e1ebaf9ea76e42522`.
Full route report SHA256: `bc2bcfd446fb6d9ea2099318bef7399ea154581268c0598556415ed0ceefa529`.

The source folder retains `revision-build.json`, `source-freeze.json` and
`code-inputs.json`; the latter records exact compiler/library source bytes.
`docs/showcase/snapshot.json` binds source, locks, native board, DRC, route reports
and all six rendered/excerpt assets. The promo page mirrors those assets exactly.
Placement uses native front fabrication/courtyard artwork at final routed poses;
copper views are exports of the untouched accepted filled board.

The compiler merge was tested in an isolated `validation/rf-cam-20261013`
worktree. Pulling directly into the original compiler checkout was blocked by
overlapping local edits; a subsequent CLI edit was detected during this run.
That original source checkout was preserved, not reset or silently replaced.
The tracker, library and LED-ring checkouts have incorporated their fetched
upstream state. Website/documentation updates are separate from publishing the
broader compiler/library work.

The compiler and library review merges above are local validation commits;
this documentation/site publication does not publish them or advance release
pins. A public checkout of `main` alone does not yet reproduce this exact
snapshot. Use the recorded reviewed inputs when available, and keep the
source-byte inventory with the local evidence.

## Reproduce in PowerShell

Select the reviewed CopperScript environment and CopperLib checkout explicitly.
For an uncommitted compiler review, set `PYTHONPATH` to that checkout, rather than
silently using a different installed compiler. Run from the tracker repository:

```powershell
$review = "build/review-new"
$library = "C:/Users/anden/Documents/dev/CopperLib"
$footprints = ".copper-cache/pkg/0c22bbbc033f71e79d6d"
$kicad = "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"

python scripts/build_battery_revision.py --modem-power --rf-layout --rf-support `
  --library-review-root $library --kicad-footprint-root $footprints `
  --output "$review/source"
if ($LASTEXITCODE -ne 0) { throw "Composition failed" }
Push-Location "$review/source"
try {
  python -m copperscript lock board.copper --offline
  if ($LASTEXITCODE -ne 0) { throw "Lock failed" }
  python -m copperscript route-board board.copper --locked --offline --layers 6 `
    --fab-profile jlcpcb-six-layer --routing-profile thorough --pitch-mm 0.5 `
    --fanout-maze --soft-ripup --constrained-pins-first --progressive-guides `
    --guide-escape-mm 1 --repair-budget-multiplier 4 --detailed-feedback-trials 0 `
    --plane-contact-radius-mm 3 --plane-stitch-detour-mm 1.5 `
    --verify-plane-fill $kicad --native-evidence-directory ../route/native `
    --report ../route/route.json -o ../route/routed.kicad_pcb --progress
  if ($LASTEXITCODE -ne 0) { throw "Routing failed; inspect retained reports" }
} finally { Pop-Location }
```

Use a fresh directory and a pinned local footprint installation/cache. This run
explicitly used its reviewed `.copper-cache/pkg/0c22bbbc033f71e79d6d` footprint
root in the builder. Wait for a successful lock before routing: two retained
preflight attempts started too soon and failed footprint-lock validation, not
routing. `route-03` is the completed attempt. Source hashes depend on explicit
review paths; compare manifests, not just an output filename.

For figures, read the accepted native directory from `plane_verification` in
the route report. Run `scripts/generate_readme_assets.py` with that filled PCB,
its source folder, `--route-report`, `--candidate` and `--unlocked-review`.
The generator checks source/native and DRC/report bindings before rendering.
Then run CopperScript's `scripts/update_site_showcase.py --tracker-root` and
`scripts/check_site.py`. Review captions and counts as well as asset hashes.

## Checks and remaining gates

CopperScript's full merged test suite: 2,856 passed, 17 explicit skips. The
assembly/macro merge regressions passed (81 tests). The broader pulled library
suite reports 187 passed, one platform footprint skip and two failures in
`test_adi_gmsl_parts.py` for MAX96792A: upstream part/evidence now use a
5.6 × 5.6 mm exposed pad, while test expectations still name 5.1 × 5.1 mm.
MAX96792A is not used by this tracker. This review records the discrepancy and
does not modify that unrelated component or claim the whole library suite passes.

Tracker suite: 70 passed, one explicit skip requiring separately retained RF
review artifacts. The static website check passes (URLs, metadata, native SVGs
and mirrored snapshot hashes). These are software/presentation checks, not RF
qualification. The 358 recorded compiler/library source inputs were rehashed
after routing with no mismatches.

Browser presentation QA used the computer-use workflow: all four views loaded
with the new captions and candidate identifier, with no horizontal overflow at
desktop width or 390 px mobile width. Browser cache keys were updated to avoid
mixing older artwork/scripts with the new snapshot.

### Figure refresh — 15 October 2026

The five illustrations now show native surface package pads highlighted in gold.
This makes lands connected to a same-colour plane visible. Placement includes
native pads as well as fabrication outlines/courtyards. A new combined view shows
all six copper layers, tracks, vias and package outlines, with zones and solid
copper fill graphics hidden. Reference/value labels are hidden in placement and
combined views to avoid overlaps. All views remain unmirrored.

The shared renderer lives in CopperScript's `scripts/render_board_showcase.py`.
It asks KiCad to plot exact native geometry, making temporary presentation copies
without saving or refilling the authoritative PCB. `rendering.json` records 97
footprints, 641 pads, 1,308 track/via items and their preserved geometry hashes;
the combined view omits 34 zones and nine solid copper graphics.

The retained PCB was relocated to the local validation archive. To refresh its
artwork, supply that exact file (SHA256 `935320e5d9e65f1438de27f233fec3428af5fcd1e74ccaa69167fe74261f31a8`):

```powershell
python scripts/generate_readme_assets.py --refresh-figures `
  --pcb <path-to-retained-CopperAssetTracker.kicad_pcb> `
  --kicad-cli "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" `
  --renderer ../CopperScript/scripts/render_board_showcase.py
```

This mode verifies the retained PCB, DRC and previous asset hashes before
rendering. It updates only artwork, rendering metadata and asset hashes, retaining
the historical source status, input bindings and review results. It does not
revalidate today's migrated source or change routing/qualification claims.

Refresh checks passed: 12 focused renderer/showcase tests, recorded asset hashes,
and all five browser view controls at 1,440 px and 390 px widths with no horizontal
overflow. The full-size link follows the selected view; direct SVG view links
also work with JavaScript disabled.

Five native check types are ignored: `missing_courtyard`,
`track_not_centered_on_via`, `tuning_profile_track_geometries`,
`footprint_filters_mismatch`, `footprint_type_mismatch`. Native fill reconciles
three deferred explicit-copper findings; it does not verify every electrical
requirement. 109 requirement checks pass and 13 remain blocked, including
RF/USB impedance, topology and return-via verification.

Independent CAM and new manufacturing/assembly exports were not performed for
this reroute. Supplier/DFM/assembly-preview review, applicable RF/USB/power
verification and prototype tests remain open. No measurements, concurrent
LTE/GNSS approval or battery-mode USB success are fabricated. The selected
JLCPCB JLC06161H-3313 / NP-155F stackup and approved BOM assumptions remain;
the passive-GNSS prototype stays restricted. `qualified_release=false`.
