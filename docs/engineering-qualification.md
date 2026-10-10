# CAM / RF / power assessment of the retained candidate

Current follow-up: JLC06161H-3313 is selected and the exact BOM is user-approved.
See [stackup selection](stackup-selection.md) for the latest `*-stackup-selected-r2`
reports, RF/USB findings and separate CPL/board approval limits. All older reports
and commands below refer to retained historical checkpoints. The actual current
fabrication board is `build/fabrication-routing-quality-20261010/board.kicad_pcb`.

Routing-quality changes now modify source intent (top GND overlap and decoupling
roles). The `*-current.json` reports below describe the earlier retained candidate
and are now historical, not current-source qualification. The new ground-only
review candidate and remaining full reroute work are recorded in CopperScript's
`docs/routing-quality-todo.md`; existing production packages remain unchanged.

Use generic CopperScript commands and CopperLib contracts. This project contains
only board-specific bindings (`engineering-plan.json`), sourcing, operating
conditions and future measurements; no compiler algorithms or reusable parts.

The preserved fabrication package is still explicitly unqualified. Commands use
its exact exported native PCB and create new reports outside the package:

```console
copper audit-cam build/fabrication-review-20261010 --kicad-python "C:/Program Files/KiCad/10.0/bin/python.exe" --report build/cam-audit-next.json
copper assess-engineering build/fabrication-review-20261010/finished-routed.kicad_pcb --plan docs/engineering-plan.json --kicad-python "C:/Program Files/KiCad/10.0/bin/python.exe" --report build/engineering-audit-next.json
copper qualification-gate build/fabrication-review-20261010 --plan docs/engineering-plan.json --cam-report build/cam-audit-next.json --engineering-report build/engineering-audit-next.json --report build/qualification-gate-next.json
```

Use `uv run --locked --extra qualification` after syncing that extra, or an
installed `copper` environment with `copperscript[qualification]`. Choose new
report filenames per run; reports are never overwritten. Exit 1 is expected
while facts/tools/evidence are missing, not a routing regression.

The latest completed assessment is retained in `build/cam-audit-current.json`
(10 pass, 3 incomplete), `build/engineering-audit-current.json` (7 pass,
36 incomplete) and `build/qualification-gate-current.json` (19 pass,
3 incomplete). There are no failed current-input bindings. The `next` filenames
above are for a fresh run, not overwriting these reports. Earlier dated reports
are historical and became stale when the native reader/algorithms changed.

Initial actual-candidate checks pass package hashes, all 13 Gerber layer metadata,
295 drill hits, 552 physical contact records, 295 via records and the native/IPC
net partition. Filled In1 GND geometrically covers all cellular/GNSS feed track
envelopes with zero EXTRA margin. This is a minimum geometric screen, not
impedance or RF-return-path electrical qualification. It does not justify the
existing approximately 35.6 mm cellular or 14.9 mm GNSS total track lengths.
Both require exact-layout/stackup and RF review; limits are not invented.

The BLE reference deliberately excludes copper near chip matching/antenna
geometry. Do not blindly apply the solid-reference coverage screen there.
Matching returns, keepouts, antenna values and enclosure adaptation still need
source-backed review and prototype tuning.

Remain blocked on a pinned second independent CAM parser/corpus, qualified
Gerber-to-vector extraction and fabrication capabilities, exact stackup/plating,
modem/GNSS matching/support, operating loads and pack/USB/temperature limits,
effective MLCC/inductor/current data, external impedance/transient evidence and
bench RF/power/charging/thermal measurements. Generic vector CAM algorithms exist
but have NOT independently verified this candidate's Gerber copper.

The report-based checkpoint verifies unchanged artifacts, algorithms, sources,
library contracts, operating plan and external evidence. It cannot approve the
83 unreviewed BOM/CPL selections or authorize an order. `make order` now also
requires successful CAM, RF/power and checkpoint commands after its existing
assembly/native gates; missing evidence stops it.

For Make assessment targets, set `QUALIFICATION_DIR`, `QUALIFICATION_PCB`,
`QUALIFICATION_RUN` and `KICAD_PYTHON` for the retained candidate; run `cam-audit`
and `engineering-audit` separately to collect both reports despite incomplete
status, then `qualification`. Add reviewed `CAM_AUDIT_ARGS` only after provisioning
the pinned second parser/profile. Do not modify generated artifacts to fit a gate.

See CopperScript `docs/engineering-qualification.md`, its implementation checklist,
CopperLib `docs/engineering-contracts.md`, and this project's qualification TODO.
