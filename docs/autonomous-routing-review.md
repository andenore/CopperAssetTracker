# Shared routing closure and project-script retirement — 2026-10-11

The unchanged locked **83-component**, six-layer Tracker benchmark now routes
through CopperScript's standard `route-board`, without pose seeds, selected-net
repair flags or board-local solver logic. Both balanced and thorough profiles
closed **60/60 ordinary nets**; the two distribution-zone nets are independently
verified by actual KiCad 10.0.6 refill. Each run has **0 unconnected items,
0 other violations and 0 isolated copper islands**. `fabrication_ready` remains
false. This is not approval of the separate 91-component battery/modem revision.

## Re-run

Activate the current reviewed CopperScript environment, then from this project:

```console
make route-review REVIEW_COPPER="python -m copperscript" REVIEW_DIR=build/new-review
```

Use a new output directory. The wrapper supplies source, locked library inputs,
six-layer profile and three macro scene assets. CopperScript owns placement,
package access, ordinary routing, bounded repair, plane contacts and refill
verification. A nonzero exit retains an incomplete draft/report, never approval.
The pinned `make route`/manufacturing workflow and release locks are not upgraded.

## Retained balanced evidence

Files remain in the chat's workspace at
`C:/Users/anden/Documents/Codex/2026-10-09/pull-from-all-copper-repose/autonomous-routing-20261011/`:

- `tracker-budget-retry-route.json`: source-matched shared routing report.
- `tracker-budget-retry.kicad_pcb`: exported native draft, read-only audited.
- `tracker-budget-retry-native/verification-001/CopperAssetTracker.kicad_pcb`:
  independently filled native board.
- `tracker-budget-retry-native/verification-001/drc.json`: independent DRC.
- `tracker-thorough-retry-route.json` and its native evidence: second bounded
  profile also achieves closure, without changing hardware source or rules.

SHA256 bindings for the balanced result:

| Input/evidence | SHA256 |
| --- | --- |
| `board.copper` | `03883bab0bd8e5734127711bc1137698ea355e77c202afc825b2807430e2baff` |
| `copper.lock` | `b49fd2c543ac7a9588e6c13f27a95f51d621c2b8163ca74bc44172653264f7a8` |
| Exported native PCB bytes | `32cb50fbb34f811eb63e87194fa78c1e55460181e4f4ba1906315d6a92cbb9f4` |
| Filled native PCB bytes | `337e29805a4dee2cee7a5b74dd564627a001ac36e294c55bf5f87e4c55299c80` |
| Native DRC bytes | `7cd8bb521edee81389bc8c9e554b0992778c6e69294002fa2bc6679655269571` |

The report also binds canonical physical geometry
`d1eea6fd9fe11eeb1be4f8dc6abd62084008bfa2b90fe72d8199473c1bbcf651`
and verifier input export
`d81ab1262bf74f86638097e4d43d0ff73d7feaaa07c52b04411c293fb17997ff`.
These semantic/export digests are not interchangeable with saved PCB byte hashes.

Readback observes 83 components, 877 tracks, 304 vias and 8 immutable polygons.
Shared source/land/macro/required-array validation passes without changing the
input. Every one of the 14 explicit decoupling associations is connected by
actual top-layer copper with all vias, zone fills and component-internal joins
excluded from the exact contact graph. This proves via-free connectivity, not
an impedance, maximum-distance or transient-performance qualification.
The endpoint-only chain finder misses C_STATUS_B's interior track junction;
its false negative is recorded as generic follow-up research, not repaired by
a project-specific algorithm.

## Retired entry points

Removed: `finish_routed_candidate.py`, `route_review_candidate.py`,
`probe_open_routes.py`, `probe_clock_routes.py`, `review_decoupling.py`,
`seed_battery_usb_candidate.py` and `shorten_cellular_feed.py`.
Tracked versions remain recoverable from Git history. Historical PCB/report/
manufacturing archives were not removed or replaced.

`scripts/checkpoint_source.py` now only composes this board's source/library and
macro assets, delegating front-native pose, land and explicit-copper validation
to CopperScript's `pcbir.native_checkpoint`. Rendering and modem-power checks
use that read-only wrapper. It never reinserts missing copper or repairs a route;
duplicate owner occurrences, vias and polygons must exist in the actual file.
Via finish is source intent, not fabrication evidence. Native outline/zone/mask/
material audits, fresh filled DRC and qualification remain separate requirements.
Use current reviewed CopperScript for these readers; older compiler pins do not
contain the new shared module. No lockfile was silently advanced.

The frozen solver snapshot passed 2,436 tests with 21 optional skips. The new
native-checkpoint module was added afterwards and is verified separately, not
included retroactively in that full-suite result.
The finalized reader has 40 passing real-geometry cases, including renamed
and rotated lands, rigid-owner moves, missing/duplicate copper, polygon rings,
drills and pose-only scope. Its earlier 36-case version also passed alongside
113 existing ownership/array/branch/cleanup cases (149 passed, one optional
skip). The post-retirement Tracker suite passes all 51 remaining cases, with
the explicit CopperLib review root and no skips. These counts overlap.
