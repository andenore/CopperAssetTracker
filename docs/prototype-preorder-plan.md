# CopperAssetTracker prototype preorder plan

Complete pre-order items 1 through 5 for a source-matched engineering prototype.
The user excluded item 6 (mechanical fit and test-access work). This exclusion
does not approve electrical risks or waive manufacturer RF or battery limits.
Production qualification and post-delivery measurements remain separate.

Baseline: RF-support v8, 97 physical components, 95 fitted selections, ERC clean
and legal placement; routing and native routing DRC are not yet complete.
Fresh work is under `build/prototype-preorder-v1-20261012/` and subsequent
numbered candidates. The v1 route was stopped after finding the generic
point-to-point-only RF limitation; no v1 native routing pass is claimed.
Retain historical outputs. Reusable definitions belong in CopperLib, shared
algorithms in CopperScript, and configuration/evidence in this project.

## 1 GNSS filtering and protection

- [x] Review current manufacturer filter/protection sources and exact assembly
  identities; compare supported GNSS passbands, LTE rejection, insertion loss,
  ESD and power limits.
- [x] Select a source-backed front end or reviewed populate/bypass experiment
  options. Do not treat unknown antenna isolation as a pass.
  The user accepted preparation of a five-unit restricted passive-GNSS experiment
  on 2026-10-12. Initial GNSS tests keep the modem physically unpowered and
  LTE/BLE transmit disabled; controlled coexistence requires a separately
  reviewed setup. Simultaneous service and ordering are not approved. See
  `revisions/prototype-preorder-v1/restricted-experiment-acceptance.json`.
- [x] Put reusable parts/circuits/footprints and qualification contracts in
  CopperLib; add electrical/topology/footprint regression checks.
  Existing exact protection parts/circuit and new passive coexistence experiment
  options are library-owned; five focused library regression checks pass.
  The R08 GNSS datasheet/model correction and integer-unit operating/ramp limits
  are now library-owned as well; six RF-support regressions pass. V3 rebuilds
  source and library locks rather than changing v2's recorded inputs.
- [x] Record the selected receive configuration, remaining coexistence risks and
  required post-delivery measurements. No enclosure-fit work is included.
  See `revisions/rf-support-v1/gnss-prototype-decision.json`: retain the integrated
  front end for a restricted experiment; low-gain is the manufacturer's default,
  not a verified firmware state. B4327 requires a future protected redesign.
  This is not a board-level solder-population alternative or RF approval.
- [x] Freeze fresh source/assembly/library inputs and pass ERC/placement before
  full routing.
  V2 retains 97 physical / 95 fitted parts, zero ERC findings, a 31-footprint
  library lock, immutable macro files and legal source-constrained placement.
  Its routing preflight passed all critical nets, plane/package contacts and
  ordinary exits after one accepted USB-filter placement move. The first full
  v2 route finished with USER_LED_2 open; native fill also found V3V3/V3V8 opens
  and two dangling ends. Its draft is retained and is not an export candidate.
  V3 composition passed zero-error ERC and eight composition regressions. Its
  R08 library model and subsequent 31-footprint physical lock are bound in
  `build/prototype-preorder-v3-20261012/source-freeze.json`; the composition-step
  manifest is preserved rather than silently rewriting its earlier lock hash.

## 2 Routing and verification

- [x] Run the standard bounded CopperScript routing pipeline with the three
  immutable macros, six layers and native plane-fill verification.
- [x] Repair any algorithmic issues in CopperScript, not project routing code.
  Preserve RF widths/clearances/layers, bypass intent and macro copper.
  Implemented explicit via-free RF tree support for TVS/tuning-land branches;
  188 focused regressions pass, including strict candidate BOM/CPL identity and
  package-access rollback. Generic native-feedback cleanup now considers all
  completed ordinary area owners, while preserving immutable/source copper and
  requiring before/after connectivity and fresh native proof. Its regression
  run passed 82 tests with one skipped. A stronger generic routing candidate
  uses a bounded larger failed-net search budget and wider guide escape; no
  tracker-specific repair script was added.
  The LED trial identified one movable adjacent-net blocker but rolled back
  when that blocker could not reroute. The duplicate two-pass cleanup run was
  stopped with its files retained; v3 is configured for four standard failed-first passes
  with the cleanup fix and current GNSS model. No rollback or DRC gate is waived.
  The complete detailed-router module also passed all 42 tests, including the
  bounded refinement, failed-first and transactional repair cases.
  The initial four-pass v3 run retained USER_LED_2_A and two V3V3 gaps. The
  shared thorough profile closed all 61 ordinary nets. KiCad 10.0.6 native
  verification of `thorough-feedback/native/verification-003/` reports zero
  opens, zero violations and zero islands. Source, pad/pose and immutable-macro
  identity match. Accepted filled-board SHA256:
  `5576fd30317e805fe85d18b666d12dbfd0200f143a51176cd5ac6546b00fcff0`.
- [x] Verify zero unintended opens/native DRC violations and source-matched
  pad/net/pose/macro identity for the exact final candidate.
- [x] Review actual RF/ESD returns, decoupling and USB reference transitions;
  record unsupported solver checks separately from geometric passes.
  Final source-bound cellular and GNSS inventories each show two connector
  ground lands and via-free signal routes. The 21 bypass checks are surface
  connected. These are geometry screens; launch impedance, RF returns and
  coexistence remain externally incomplete.

## 3 Critical electrical margins

- [x] Review the complete battery-powered modem USB operating states and supply
  corners, not just the nominal shared-rail voltage.
- [x] Review charger regulation/current/timer/temperature bounds, battery
  protection and electrical harness polarity; mechanical-fit checks are excluded.
- [x] Review modem burst droop, effective capacitance, converter/current-path
  ratings and applicable RF/USB modelling. Use sourced bounds; unknown inputs
  remain explicit rather than becoming assumed guarantees.
  Findings are in `docs/prototype-electrical-review.md`: modem static margin
  60 mV; newly identified logic upper margin only 6 mV; timer completion and
  effective capacitance unresolved. These reviews are not qualification passes.
- [ ] Implement justified source changes and repeat affected checks; document
  controlled prototype operating limits and post-delivery measurements.
  The R08 open-selector model correction is implemented and source-bound. The
  proposed controls explicitly hold the modem rail off during initial GNSS
  bring-up; an after-boot firmware command is not assumed to prevent early TX.
  Shared GNSS/logic power means receiver standby is not physical RF protection.
  Feedback-divider hardware and charging behavior are not silently changed or
  approved; resolve the retained electrical risks and test configuration first.
  The post-delivery sequence, record fields and component-specific limits are
  written in `docs/prototype-bringup-checklist.md`. Its measurement boxes remain
  unchecked. Battery USB/modem tests need a separately reviewed RF setup because
  GNSS standby is not input protection.

## 4 Manufacturing package and independent review

- [x] Export fresh Gerbers, plated/nonplated drills, native/project/rules and
  fabrication instructions for JLC06161H-3313 / NP-155F and required via processes.
- [x] Run available independent CAM parsers and native/drill/netlist agreement
  checks against this exact package. Missing vector/solver evidence stays open.
  The exact `manufacturing-NOT-APPROVED` export was audited against the accepted
  native board. Package checksum/native binding, native DRC, six-layer inventory,
  drill reconciliation and IPC-356 contact reconciliation pass. The pinned
  parser corpus and parser/render agreement fail; CAM connectivity and full
  fabrication-geometry evidence remain incomplete. See
  `docs/prototype-cam-review.md` and the retained `cam-review-NOT-APPROVED.json`.
  The additive cell-detail recheck explicitly identifies libgerbv's two corpus
  failures and preserves the same fail/not-qualified outcome; its SHA256 is
  `9cb9134636f04984ebdb39d90584ce54e6c0d755e3a6bdbe4bade3af88f7cf4a`.
- [x] Inspect layer inventory, copper/outline/drill alignment, mask/paste and
  critical RF/power artwork; bind reports and files with checksums.
  A qualitative per-layer screen was rendered for all six copper layers,
  outline, top/bottom soldermask and paste, and both silkscreens; the accepted
  native 3D top render was also inspected. The 95 CPL entries are all Top, and
  the empty bottom paste/mask/legend layers are consistent with the one-sided
  placement and tented-via design. Drill/contact reconciliation has zero
  defects. Renders and source reports are retained under
  `build/prototype-preorder-v3-20261012/thorough-feedback/cam-render-NOT-APPROVED/`.
  This is only a visual screen: it does not resolve the independent parser
  disagreement or qualify RF/power geometry.
- [x] Prepare an explicitly unqualified prototype candidate package; never reuse
  the old 91-part exports or present file generation as release approval.
  The export is tied to the accepted native-board hash above and states
  `qualified_release=false`; independent CAM review remains open.

## 5 Assembly and sourcing review

- [ ] Review changed exact MPNs/packages/pin maps and BOM/CPL reference identity,
  polarity/rotations, DNP states and required modem assembly processes.
  The generated five-unit review candidate reconciles all 95 fitted BOM
  references to 95 CPL placements, but the assembly audit records zero manually
  reviewed references and 14 changed/new identities against the earlier
  approved root BOM. Exact source/rating/package review and human CPL polarity,
  rotation, and modem-process review remain open.
- [ ] Check timestamped supplier evidence for every fitted identity; distinguish
  public catalogue/distributor inventory from confirmed PCBA availability.
  The v3-lock-bound public catalogue record covers all 51 ordering codes:
  27 exact identities returned and 24 fetch/search or stale-stock gaps. No live
  account-specific availability or reservation is claimed. The user authorized
  a five-unit JLCPCB stock/DFM/assembly-preview upload, but it has not been
  performed; no supplier availability is assumed.
- [x] Generate matching BOM/CPL files and document new selection/review gaps.
  The shared `assembly candidate-bom` command produced a v1 human-review bundle:
  95 exact identities with all generated review flags conservative. Comparison
  with the user's earlier approved root lock preserves 81 unchanged approved
  identities and identifies 14 changed/new identities still needing review.
  It does not alter strict BOM export gates. The generic writer now normalizes source hierarchy exactly as
  the PCB backend and can generate hash-bound unapproved CPL from native CSV.
  The v2 native draft has a normalized 95-part BOM/CPL bundle, explicitly not
  approved and not suitable for ordering. Eight source-composition regressions
  pass with the new copied R08 review. The thorough v3 candidate carries fresh
  95-reference BOM/CPL files generated from its exact native positions; all
  flags remain conservatively unapproved.
- [ ] Complete JLCPCB live-stock, DFM and assembly-preview review for five units,
  then bind returned results to the checksummed candidate. The user authorized
  this upload scope for quantity five on 2026-10-12; payment and ordering were
  explicitly withheld. A local three-file preview bundle is prepared under
  `build/prototype-preorder-v3-20261012/supplier-preview-5-units-NOT-APPROVED/`.
  Upload has not occurred: Computer Use stopped because browser URL-policy
  enforcement is unsupported for the current Windows browser. No supplier
  stock, DFM or assembly-preview result is claimed.
- [ ] Obtain exact-package approval before ordering. No purchase, order,
  commit, push or review waiver is authorized.

## Completion criteria

Check off a task only against retained evidence for its actual inputs. The plan
is complete when items 1 through 5 have their required design/geometry/file/review
evidence; unavoidable supplier or human approvals must be identified explicitly.
Bench measurements validate the delivered prototype later. Unknown radio,
battery or charging behavior cannot be described as safe or production-approved.

## CAM bounds follow-up — 12 October 2026

The generic CopperScript `PyGerberAdapter` now derives Gerber region bounds
from the contour centerline (including arc extrema) rather than incorrectly
stroking region segments with the active aperture. Regression coverage includes
a rectangular region and a semicircle with a deliberately wide aperture. The
two focused CAM/manufacturing test modules pass 14 tests in the actual
CopperScript working tree. Source SHA256:
`de5b63bcb4c9d15bf3f3363ed0efd760ffb41e9b62b6a137dc4ada45d884ea31`; test
SHA256:
`fa0754bbfbd3e049776aa4aa51a7f336db1ebe815770f12ff48ce9a9d55cd941`.

A read-only recheck of the exact five-unit candidate Gerber ZIP
(`5b740247a05d8f441fae39b75b2be16c423d5d195e924c7d44075b2e31ab755b`)
found matching PyGerber/Gerbonara bounds for all 13 artwork files (10 with
geometry and 3 empty). This resolves only the identified metadata bounds
disagreement. The saved candidate CAM report has not been replaced or upgraded:
libgerbv still accepts `negative_missing_end`, rejects `positive_polarity`, and
the parser/render, copper-connectivity and fabrication-geometry gates remain
unresolved. The parser and test edits are uncommitted; no Tracker board or
manufacturing file changed, and nothing was ordered or uploaded.

The complete audit was rerun with the updated adapter and retained at
`build/prototype-preorder-v3-20261012/thorough-feedback/cam-review-bounds-followup-003-NOT-APPROVED.json`
(SHA256 `54bd254c70186686dad4daa943d51c38c0a56216593e36a911f089e37afb3207`).
It remains **FAIL**: package checksum, native-board binding and saved native
DRC pass; libgerbv still fails the same two corpus cells, parser agreement
still fails, and copper-connectivity/fabrication-geometry remain incomplete.
The new report no longer shows the earlier 100–400 um region aperture overcount;
remaining layer-bound deltas are mostly nanometre/submicron-scale, while exact
render digests still disagree. The negative missing-end test is intentional:
[Ucamco's current spec, section 4.13](https://www.ucamco.com/files/downloads/file_en/554/gerber-layer-format-specification-revision-2026-05_en.pdf)
requires M02 as the last command and encourages readers to error when it is
missing because it indicates truncation. None of these checks establishes
fabrication approval.
