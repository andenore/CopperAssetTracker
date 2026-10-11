# Latest validation status

Recorded checkpoint: **2026-10-11**, KiCad 10.0.6. Documentation consolidation
does not constitute a new routing or hardware validation run.

## Modem-power/battery revision

The latest reviewed 91-component, six-layer source-only run has 75 physical nets,
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
