# Prototype CAM review — 12 October 2026

Status: incomplete. No independent CAM or fabrication approval is granted.
Actual final-candidate manufacturing checks follow successful filled native DRC;
the parser corpus below is separate from this board's artwork.

## Independent parser experiment

Downloaded the official gerbv Windows v2.11.0 archive from its GitHub release
asset API after the direct release URL timed out. Verified the publisher's
SHA256 before unpacking. This is a task-local tool, not a global installation.

Archive SHA256:
`19a5bf4a681f7df89d9bc6ea6b3447d8efe0f08c5eb1c4ddea5d8c27b69584f7`.
The executable reports `gerbv version v2.11.0`; executable SHA256:
`e0887849731457ff651e173caef0ee8aca303336a22f0103ff2092c83b030936`.

CopperScript's PyGerber adapter reports version 2.4.3 and combined interpreter/
package-source identity:
`6da262af76d759b850af75964a66a6dc4aabdc1764622517201df801ced98581`.
The shared hash-pinned experimental profile and eight corpus files are retained
under `CopperScript/build/cam-preorder-profile-20261012/`.

Observed corpus results: PyGerber passed all eight cases. The libgerbv adapter
passed six and failed two: `negative_missing_end` was accepted, while
`positive_polarity` failed re-export with a nonzero process result. Direct
reproduction with the positive fixture also returned a nonzero result without
stderr. This is a failure of the current adapter/tool combination; it is not
evidence that the candidate board's copper is wrong, nor permission to remove
the failing tests. The profile is explicitly NOT-QUALIFIED.

The adapter uses independent libgerbv parsing/re-export and PyGerber to
normalize the resulting geometry. Those stages are not two independent copper
connectivity extractors. Full Gerber/XNC specification coverage, vector copper
connectivity/fabrication-geometry checks and external DFM review remain open.

Source: [official gerbv release](https://github.com/gerbv/gerbv/releases/tag/v2.11.0).

## Exact package checks still required

Retain an `audit-cam` report for the actual source-matched manufacturing
directory. Check all layer inventory and checksums, native binding/DRC, drill
multisets and IPC-356 contacts/net partition. Inspect actual mask/paste,
outline/drill alignment, RF/ESD return and power artwork. Parsing, inventory
agreement or a rendered image must not be described as an independent
connectivity or impedance pass. Any unsupported native features remain explicit.

## Exact v3 candidate audit — 12 October 2026

`build/prototype-preorder-v3-20261012/thorough-feedback/manufacturing-NOT-APPROVED/`
is bound to accepted native PCB SHA256
`5576fd30317e805fe85d18b666d12dbfd0200f143a51176cd5ac6546b00fcff0`.
The audit reports no checksum mismatch, confirms native-board binding and saved
native DRC, inventories six copper layers, parses 340 metric drill hits, and
reconciles all 340 drills and 580 IPC-D-356 contacts with no multiset defects.
These structural checks do not extract copper connectivity.

The audit is **FAIL / NOT QUALIFIED**. The pinned parser corpus and
parser/render-agreement checks fail: libgerbv reports parsing/re-export issues
for mask, paste and silkscreen files, and disagreements are reported on multiple
layers. Copper-connectivity and fabrication-geometry evidence are incomplete.
This does not establish that the generated board artwork is defective; it means
the current independent-parser profile cannot qualify it. Preserve both the
failure and the profile's known limitations. Retained report:
`build/prototype-preorder-v3-20261012/thorough-feedback/cam-review-NOT-APPROVED.json`
(SHA256 `97b5602d666fcda4a99b3d6170823107245ad92543f906f726f1a4f94634c889`).

The user authorized JLCPCB stock/DFM/assembly preview for five units, not an
order. The Gerber/BOM/CPL candidate is checksummed locally, but no upload or
supplier result is claimed; the current Windows browser is blocked by its URL
policy guard. See the local `supplier-preview-5-units-NOT-APPROVED` package.

For a qualitative visual screen, PyGerber 2.4.3 rendered each of the six copper
layers, outline, top/bottom mask and paste, and top/bottom legend; KiCad 10.0.6
rendered the accepted native board in 3D. The native 3D image is a placement
view, not a rendering of the exported fabrication files:

![Accepted native board top-side 3D review](../build/prototype-preorder-v3-20261012/thorough-feedback/cam-render-NOT-APPROVED/top-native-3d-review.png)

The individual layer images are retained beside it. The bottom paste, mask and
legend files contain no apertures/graphics, consistent with all 95 fitted CPL
parts being on Top and the board's tented-via settings. This visual inspection
found no gross outline/placement discrepancy, but it cannot reconcile the
independent-parser disagreement or establish copper connectivity, controlled
impedance, or fabrication acceptance.

## Diagnostic recheck with per-case corpus results

After the generic CopperScript audit was updated to retain individual corpus
cells, the unchanged manufacturing package was audited again. The additive
report is
`build/prototype-preorder-v3-20261012/thorough-feedback/cam-review-cell-details-001-NOT-APPROVED.json`
(SHA256 `9cb9134636f04984ebdb39d90584ce54e6c0d755e3a6bdbe4bade3af88f7cf4a`).
It remains **FAIL / NOT QUALIFIED**. The pinned libgerbv v2.11.0 corpus failures
are now explicit: it accepts the malformed `negative_missing_end` case and
rejects `positive_polarity` during re-export. PyGerber passes all eight corpus
cases. The independent layer comparison still reports parser/re-export errors
and disagreements on multiple exported layers; this does not by itself prove
that the original Gerbers are defective.

The recheck again passes package checksums/native-board binding and native
DRC; it reconciles 340 drills, 580 IPC-D-356 contacts and the 340-via set with
zero multiset defects, and the exporter net partition has no split or merged
source nets. Those structural checks are not copper extraction. Copper
connectivity and fabrication-geometry evidence remain incomplete, so the CAM
failure is preserved and no fabrication approval is granted.
