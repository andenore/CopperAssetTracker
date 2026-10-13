# Pending-change validation — 13 October 2026

This is a fresh source-to-route validation of the 97-footprint RF-support
revision, not production approval or a replacement for the historical
manufacturing candidate. No supplier upload, order or bench result is claimed.

## Source and routing

The existing source builder composed `--modem-power --rf-layout --rf-support`
against the explicitly reviewed CopperLib checkout and the pinned KiCad
footprint cache. ERC passed; there are 97 physical components and 95 fitted
selections. The generated source is identical to the earlier v3 circuit source.
A new offline physical lock resolves 31 footprint identities. Compiler/library
release pins were not advanced by this working-copy review.

The standard CopperScript pipeline ran without a pose seed, imported historical
ordinary copper or a tracker-specific routing repair. Its options were:

```powershell
python -m copperscript route-board board.copper --locked --offline --layers 6 `
  --fab-profile jlcpcb-six-layer `
  --hard-macro nrf-antenna-macro.json --hard-macro logic-power-macro.json `
  --hard-macro modem-power-macro.json --routing-profile thorough --pitch-mm 0.5 `
  --fanout-maze --soft-ripup --constrained-pins-first --progressive-guides `
  --guide-escape-mm 1 --repair-budget-multiplier 4 --detailed-feedback-trials 0 `
  --plane-contact-radius-mm 3 --plane-stitch-detour-mm 1.5 `
  --verify-plane-fill "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" `
  --native-evidence-directory ../route-02/native `
  --report ../route-02/route.json -o ../route-02/routed.kicad_pcb --progress
```

The command exits successfully: 61 ordinary nets routed, zero ordinary nets
unrouted, three zone-net observations resolved by native fill, and all 21
decoupling feeds verified as surface-connected. The result has 968 track segments
and 340 vias on six copper layers. Native verification records zero opens,
zero included violations and zero islands. Its two USB pairs meet the authored
skew limits; this is not impedance or USB-on-battery qualification.

The shared source/native checkpoint independently accepts all 97 footprints,
their actual lands/nets/layers, legal poses, actual tracks/vias, all three
immutable macros and required via arrays. A separate KiCad 10.0.6 refill/DRC
readback also records zero opens and zero included violations.

Both native DRC reports list five ignored check types: `missing_courtyard`,
`track_not_centered_on_via`, `tuning_profile_track_geometries`,
`footprint_filters_mismatch` and `footprint_type_mismatch`. They are not silently
treated as completed checks. The first independent readback omitted the generated
footprint library and reported 97 library-resolution errors. That diagnostic is
retained; including `fp-lib-table` and `CopperScript.pretty` resolves it without
suppressing library checks.

## Test closure

- CopperAssetTracker: 66 passed, including actual revision composition and
  retained RF evidence.
- CopperLib: 188 passed, two unrelated ADI footprint tests skipped because their
  installed-library paths are Linux-specific. Its 19 native regulator macro
  tests additionally pass against the matching installed footprint set.
- CopperScript: clean final full suite passes: 2802 passed, 17 skipped. An earlier
  full run recorded 2793 passed, six failed and 20 skipped; those failures concerned
  missing pinned example caches, a routing fixture's overlapping default logo,
  and two examples' default artwork positions.
- Focused shared CAM/RF/DNP/native-clearance/placement/repair suite: 220 passed.
- Corrected routing fixture: three passed with native checks enabled.
- Final artwork/example checks: 68 passed, with no skips, including native
  artwork integration. Example marks are placed clear of components and meet
  native minimum text height; checks are not waived.

The review also corrects stale RF-source/showcase assertions, restores showcase
composition/lock bindings, pins checksum-bound SVG line endings and updates a
golden report only after reproducing its old hash by reversing the diagnostic
message change. The fixture board and KiCad export hashes were unchanged.

CopperScript's remaining skips cover a Linux-only default path, four host symlink
checks, eight unavailable ngspice integrations, three legacy optional macro-trial
checks whose sibling footprint path is absent, and one editor-overlay test whose
executable-name check does not recognize Windows' upper-case EXE suffix. The
independent native board checks above did run. Skipped tests are not qualification
passes. Test reports and exact source-byte inventories are retained with the build.

Concurrent physical-macro language implementation appeared in the original
CopperScript working tree after the validation snapshot. That work is excluded
from this result and must remain untouched. CopperScript integration uses the
isolated `validation/rf-cam-20261013` branch; CopperLib and CopperAssetTracker
can advance local `main` only after confirming their original source is unchanged.

## Retained outputs and identity

Outputs are under `build/change-validation-20261013/` in CopperAssetTracker.
The `source/` folder retains composition and locks; `route-02/` contains the
board, generated local footprint library, reports, progress log and native
verification. `route-02/readback-20261013/` retains the independent readback.
The source's replacement paths identify the isolated review checkouts; this is
explicit working-copy evidence, not a standalone pinned production package.

```text
60d44faa43321811788604fa76b4d94297bbb314df47886452e2dd306cf05826  source/board.copper
841f5380885b32e051bb035adb338428f71318b67296ecfa6bec947ad6e4fc22  source/copper.lock
b5e60eeb9b3f47b6119af104b9c668bdd7072e69f5ce7b5a2084cbbc9132198e  route-02/routed.kicad_pcb
06e1bbc75b7342625679cb1c56efcb83b219c54f62744b42962aaf17dee33fb2  route-02/route.json
2176da859b6f5adb1c51fdd4482c7a5f3ab6f4042bfc0232042ea2b2f7cf4409  route-02/native/verification-003/CopperAssetTracker.kicad_pcb
681bfa9be369d99769763beece5b5c61368c8721dc334dedb3c8e482fd86dd27  route-02/native/verification-003/drc.json
4a120e053cc20cbd7a28713cbacfc0f6cf0bc1c26ae4bb20add0587eae60fc1a  route-02/readback-20261013/drc-with-library.json
```

Thirteen electrical requirements remain blocked. Exact RF/USB impedance and
return-path modelling, power/battery-USB validation, coexistence/ESD and prototype
measurements, qualified independent CAM, supplier/assembly review and explicit
release/order approval remain separate gates. No new manufacturing release,
prototype approval, package email or purchase follows from this routing pass.
