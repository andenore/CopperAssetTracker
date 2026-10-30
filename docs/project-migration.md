# Rust project migration

Branch: `codex/rust-client-layout`. Preparation, not completed board qualification.
Compiler: `21b2ca44aee63665feeb67e39da1713ac693e934` (Rust only); exact dependency and assembly pins are preserved.

## Active layout

| Target | Source | Layers | Assembly lock |
| --- | --- | --- | --- |
| main | `board.copper` | 6 | `assembly.lock` |

Board-owned composition belongs in `src/`, physical inputs in `assets/`,
and generated runs in `build/<target>/runs/<run-id>/`. CopperBench uses target-local
`boards/<target>/src` and `assets`. Optional empty directories are not required.
Dependency caches stay ignored. Historical evidence is retained at its original paths.

## Working interface today

The proposed `project` blocks and `copper build/package` commands do not exist
in this compiler. Do not put unsupported fields into `copper.mod`. The small
`make/targets/*.mk` files are temporary settings adapters; move them into the
versioned manifest when the shared project implementation lands.

- `make fetch`: locked preparation; no dependency version update.
- `make check`, `make compile`, `make power-check`: public Rust CLI.
- `make test-smoke`: public-JSON regression subset using Node's built-in runner.
- `make route RUN_DIR=build/main/runs/NAME`: fresh diagnostic routing with
  native verification. It is not a source-freshness-checked build/package operation.
- `make test`, `package`, `manufacturing`, `order`: explicit unsupported
  result until mandatory coverage/shared run validation is available. Nothing is exported.

GNU Make/Git Bash are only command shortcuts. The Rust commands work directly
on Windows and Linux. Normal check/compile operations do not need Python, uv or jq.

## Remaining coverage

The Python board/revision/probe suites and removed CAM/engineering commands require migration. Source-selected macros remain bound to the same libraries. Historical root JSON macro snapshots stay at their old paths for the retained probes; the active board uses managed source macros.

Legacy scripts/tests are retained so their checks can be ported, not deleted.
Archived workflow recipes are in `docs/migration/legacy-ci/`; the new workflow
checks sources and the explicitly named acceptance subset only. Re-enable native
route/package CI after equivalent gates exist; a green source job is not release
acceptance. Do not use legacy wrappers with the Rust-only pin as if they were supported.

## Completion checklist

- [x] Dedicated branch preserves prior uncommitted migration work.
- [x] Rust-only compiler pin and common source commands.
- [x] Active source/asset layout prepared, with historic evidence retained.
- [ ] Compiler-provided project validation and consumed-input provenance.
- [ ] All mandatory client tests ported to supported public contracts.
- [ ] Native route, assembly and package gates rerun on the moved inputs.
- [ ] Strict layout CI and shared Rust build/package workflow adopted.

Layout preparation, workflow adoption, physical acceptance and engineering
qualification are separate outcomes. Old successful runs retain their old hashes;
this branch does not authorize production, publication or orders.

## Local validation on 2026-10-30

Compiler: Rust-only `21b2ca44aee63665feeb67e39da1713ac693e934`.

- CopperAssetTracker: compile passed; ERC passed; before/after public IR matched
  after explicit path-identity changes.
- Public-CLI contract subset: 1 test passed. This does not replace the retained legacy suite.
- Dependency manifests/locks and existing assembly selections were not changed.
- Full routing, native KiCad DRC and manufacturing export were not rerun.
- Windows entry-point execution was checked on LedRing and Bench prototype;
  all five PowerShell wrappers parsed. Linux CI has not run on these local branches.
