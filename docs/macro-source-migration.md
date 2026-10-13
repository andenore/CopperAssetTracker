> Historical binding-syntax migration record. The current definition migration is
> recorded in [macro-definition-migration.md](macro-definition-migration.md).

# Source macro migration

2026-10-13. The active board imports the Nordic physical asset and the two
TPS63020 assets and declares `physical_macro` bindings in `board.copper`.
Power bindings use `on PWR`; the RF binding maps the board component set.
Make no longer passes duplicate macro scenes. The revision source builder
converts retained historical scene selections into source declarations before
compilation. Power probes consume prepared source selections. Native checkpoint
readers still support older source/scene candidates without double binding.

The three selected asset SHA-256 values and every resolved member/net mapping
match the former scene inputs. CopperLib and footprint dependency pins, macro
geometry, electrical circuitry and fixed poses are preserved. Compiler and board
source identities change, so old evidence must not be presented as current.

The retained assembly lock reports `STALE_LOCK`: all 83 exact selections remain
reviewed, but the new compiled source digest needs a fresh assembly review.
The lock was not rewritten to approve the migration. Previously routed boards,
native DRC reports and showcase renders retain their historical bindings; the
showcase snapshot explicitly records its historical canonical source status.
No new full-board route, manufacturing qualification or ordering approval is
claimed by this migration.

Validation uses the current CopperScript implementation: exact asset/map
equivalence, equality of legacy/source physical macros, rigid clusters and nets,
source-selected terminated power probes, current board ERC and consumer tests.
The compiler dependency is updated to the published source-macro commit;
`copper.mod`/`copper.lock` library inputs remain unchanged.

Published CopperScript pin: `db125738d3cdc0cde8293fc9476e8a0a12366317`. The locked environment
passes 63 tests and 34 subtests; seven optional working-copy integration cases
remain explicitly skipped. ERC passes. Source-only compilation and legal PCB
placement run without macro scene arguments; routing/native release gates remain
blocked or not run as expected for a placement draft. Outputs are under ignored
`build/macro-source-migration/`, not the historical manufacturing bundle.

The test target uses pytest with a declared development dependency, so both
unittest-style and pytest-style consumer suites run in the locked environment.
The former unittest-only target could not load the two pytest-based modules.
`make fetch` uses `copper lock --locked` to prepare selected assets without
rewriting the committed library inventory.
