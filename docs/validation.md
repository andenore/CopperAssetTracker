# Latest validation status

Fresh pending-change review: **2026-10-13**. The 97-footprint revision has a new
successful full route, independent source/macro checkpoint and native DRC
readback; the full reviewed test suites pass (with explicit environment skips). See
[the scoped validation record](change-validation-20261013.md). Its outputs are
in `build/change-validation-20261013/`, not the historical manufacturing bundle.
Production qualification and ordering remain unapproved.

The following checkpoints describe the earlier manufacturing-review work.

Recorded checkpoint: **2026-10-12**, KiCad 10.0.6. Evidence is scoped to the
exact candidates below, not a production-approved release.

## Active pre-prototype checks — items 1 through 5

The user excluded mechanical-fit/test-access item 6 for this pre-order pass.
The checkable scope and retained findings are in
[the preorder plan](prototype-preorder-plan.md). The fresh v3 source under
`build/prototype-preorder-v3-20261012/source/` incorporates the library-owned
MAX-M10S R08 open-selector supply correction. It has 97 physical / 95 fitted
parts, zero ERC errors, eight passing composition regressions and a new
31-footprint physical lock. `source-freeze.json` records the transition from
composition lock to routing lock without rewriting historical evidence.

The initial balanced four-pass run retained three opens. The shared thorough
profile then routed all 61 ordinary nets and completed native fill verification.
KiCad 10.0.6 reports zero native opens, zero violations and zero islands on
`thorough-feedback/native/verification-003/CopperAssetTracker.kicad_pcb`.
The accepted board SHA256 is
`5576fd30317e805fe85d18b666d12dbfd0200f143a51176cd5ac6546b00fcff0`.
The native DRC report has five explicitly ignored rule classes; see its exact
`ignored_checks` list before interpreting the zero included violations.
The source/land/pose and three immutable-macro checkpoint passes. A V3V8 plane
bridge was accepted after displaced USB-C current-sense routes were restored.
All 21 decoupling checks are surface-connected. These results do not complete
the separate impedance, return-path, power-envelope or RF qualification gates.

A manufacturing export is generated and explicitly `qualified_release=false`.
The 95-reference BOM/CPL bundle is bound to native positions and remains
unapproved. The user accepted the restricted five-unit passive-GNSS experiment
and authorized JLCPCB upload for stock, DFM and assembly-preview review only;
ordering and payment are not authorized. A three-file local preview candidate
is prepared, but was not uploaded: the browser URL-policy guard stopped
Computer Use. The exact-candidate CAM audit completed FAIL/NOT QUALIFIED; parser
corpus and parser/render agreement fail, while connectivity and fabrication
geometry remain incomplete. No supplier stock/DFM/assembly-preview result is
claimed. See the [CAM review](prototype-cam-review.md) and the five-unit
candidate manifest.
The diagnostic recheck now records the failing libgerbv corpus cells explicitly:
it accepts `negative_missing_end` and fails to re-export `positive_polarity`.
The additive report is
`build/prototype-preorder-v3-20261012/thorough-feedback/cam-review-cell-details-001-NOT-APPROVED.json`
(SHA256 `9cb9134636f04984ebdb39d90584ce54e6c0d755e3a6bdbe4bade3af88f7cf4a`);
it preserves the fail/not-qualified result and the native drill/contact
reconciliation evidence.

The first completed v2 run left USER_LED_2 open and native V3V3/V3V8 contacts open,
with two dangling-track findings. Its draft is retained for diagnostics, not
fabrication. A larger-search two-pass variant and its duplicate were stopped
in favor of the fresh v3 candidate; their files are retained.

Reusable fixes add explicit via-free RF trees and protected, connectivity-proven
cleanup of completed ordinary routing owners. Focused runs passed 188 shared
tests, 82 native/feedback tests with one skipped, all 42 detailed-router tests,
six library RF-support tests and the eight composition tests noted above.
These counts describe separate overlapping suites, not a summed unique total.
See [the electrical review](prototype-electrical-review.md),
[sourcing review](prototype-sourcing-review.md) and
[independent CAM findings](prototype-cam-review.md) for unresolved evidence.
The v3 source has an explicitly unapproved 95-part BOM identity bundle; a final
native CPL must follow the accepted route. Earlier user approval of 81 unchanged
identities is acknowledged; 14 changed/new selections remain reviewable.

No bench measurements, routine concurrent LTE/GNSS approval, supplier upload,
reservation, order, production release, commit or push has been performed in this work.

## New LTE / passive GNSS support source

[RF-support v1](../revisions/rf-support-v1/README.md) adds a reusable LTE initial
DC-block/tuning/ESD circuit and exact GNSS ESD protection from CopperLib,
selects both external passive Taoglas antenna assemblies, and authors surface
RF constraints on the same exact JLCPCB six-layer selection. Fresh source
composition is ERC-clean with 97 physical components / 95 fitted selections.
The two shunt tuning lands are DNP; shared CopperScript now carries native
BOM/CPL exclusions as well as assembly-lock omission.

GNSS interference budgets use the conditional SIM7672X positive TX tolerance
and u-blox's **low-gain-mode** point-frequency immunity, with missing measured
isolation left incomplete. Additional SAW filtering is not implemented or
approved: band coverage, sensitivity loss, power and its required protection
network still need evidence. Full launch/return EM, system ESD, enclosure fit,
supplier process acceptance and installed RF/USB/power tests stay open.

The earlier placement-only candidate is `build/rf-support-v8-20261012/`. Earlier placement attempts
were rejected and are not native routing closure evidence. V8 has a legal
real-footprint placement and accepted macro copper; its placement gate retains
routability warnings. Routing/native fill are not run for V8 and release remains
blocked. [The verification record](../revisions/rf-support-v1/verification.json)
binds the inspection artifacts. Older 91-part PCB,
design-review hashes, Gerbers and release locks remain historical; they do not
approve this changed source. See the RF-support checklist for current physical
verification results. No new production-approved exports or order is claimed.

## Latest cellular RF placement / nominal cross-section review

The subsequent [cellular design review](../revisions/rf-layout-v1/cellular-design-review.md)
selects Taoglas FXUB16.07.0150AQ and locks JLC06161H-3313 / NP-155F.
`build/cellular-design-review-20261012/` retains a fresh 91-part ERC-clean source
composition and read-only return/noise geometry. Both connector ground lands
have modeled copper-connected spanning return vias; this is not an RF-inductance
pass. Review outcome: **changes required** for RF ESD and matching/DC-isolation
adaptation, complete launch/return modelling and enclosure integration.
No board copper or production exports changed, and RF approval remains open.

J_CELL moves 800 um upward, with the local modem bypass bank moved to retain
legal courtyards and its original pin-distance limits. The fresh six-layer run
under `build/cellular-impedance-full-20261012/` connects all 61 ordinary nets,
both USB pairs and all 21 surface bypasses. The corrected source-matched native
export/refill is retained under `build/cellular-impedance-export-v2-20261012/`:
91 components, 908 tracks, 310 vias, zero native opens and zero violations.
The first snapshot's missing native RF rule is superseded, not presented as
valid impedance evidence. No explicit tracks/vias or poses changed during re-export.

CELL_RF is 3089 um long with zero vias. JLCPCB's standard JLC06161H-3313
calculator gives the nominal 50 ohm masked coplanar cross-section; source rounds
it to 142 um width and 201 um minimum ground gap. Ten uniform-section samples
match that geometry, and actual In1.Cu ground covers the conductor plus an
authored 300 um margin. The larger pad launches, bend and RF return/via fence
remain unqualified; this does not establish the complete path as 50 ohm.

The [RF revision record](../revisions/rf-layout-v1/README.md) identifies the
corrected PCB hash, source/algorithm bindings, supplier calculation and remaining
RF work. No new fabrication/assembly release or prototype measurement is claimed.

## Earlier modem-power/battery revision

The earlier reviewed 91-component, six-layer source-only run has 75 physical nets,
921 tracks and 314 vias. The standard balanced pipeline connects all 61 ordinary
nets and both USB pairs. Native refill reports zero opens, DRC violations and
isolated copper islands. The independent checkpoint guard confirms source/pad
identity, legal placement, immutable macros, required arrays and all four via-free
F.Cu modem bypass feeds. Surface-connected decoupling coverage is 21/21.

Evidence under `build/latest-power-review-20261011/`:

- `route-closure-v5.json`: completed routing and native plane verification.
- `native-closure-v5/verification-003/CopperAssetTracker.kicad_pcb`: retained filled PCB.
- `closure-v5-checkpoint.json`: independent source/geometry/bypass/native guard.
- `closure-v5-result.json` and `compiler-source-v5.json`: commands, frozen compiler
  and exact input/output hashes.

The [showcase snapshot](showcase/snapshot.json) binds the published illustrations
and IR excerpts. Reproduction and revision-specific physical intent are in the
[revision guide](../revisions/modem-power-v1/README.md).

This is an unlocked working-copy review. Changed/new BOM selections remain
unapproved; release pins and fabrication/assembly files need fresh review.
The routing report retains 11 blocked engineering requirements. Qualified release
remains false: RF/USB models, current/thermal/transient capacity, effective MLCC,
battery/charging guarantees, CAM, CPL and prototype evidence are still pending.

## Canonical locked board

Root `board.copper` is the separate 83-component design. Its latest shared balanced
and thorough benchmark runs connect 60 ordinary nets with zero native opens,
violations and islands. Its 83 exact BOM selections / 43 identities are approved
under the user assumption recorded in [BOM approval](bom-approval.md).
That scope does not approve the 91-component revision, CPL or fabrication.

The canonical benchmark's current retained evidence is under
`C:/Users/anden/Documents/Codex/2026-10-09/pull-from-all-copper-repose/autonomous-routing-20261011/`:
`tracker-budget-retry-route.json`, its `tracker-budget-retry-native/verification-001/`
filled PCB/DRC, and `tracker-thorough-retry-route.json`. Balanced source SHA-256:
`03883bab0bd8e5734127711bc1137698ea355e77c202afc825b2807430e2baff`;
lock SHA-256: `b49fd2c543ac7a9588e6c13f27a95f51d621c2b8163ca74bc44172653264f7a8`.
These bindings establish this checkpoint, not future-source approval.

Use the [README](../README.md) for current build pins and review commands, and
the [production plan](production-plan.md) for remaining acceptance criteria.
Every result applies only to its recorded artifacts and inputs; changes require
new evidence. No production or prototype order has been authorized.
