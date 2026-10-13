# Copper macro-definition migration

2026-10-13. The active board imports named CopperLib `.copper` macros:
`NRF52832_JOHANSON_MANAGED_SIX_LAYER`, `TPS63020_SIX_LAYER_ALWAYS_ON` and
`TPS63020_SIX_LAYER_ENABLED_SERIES_FEEDBACK`. The revision source builder also
selects the reviewed corner and enabled-power-output exports when requested.
Existing electrical member/net mappings, fixed poses, footprint geometry and
all immutable owner copper are preserved.

Compiler pin: `17ebc6f488dcc8f80a3e0052a18af35760a9b759`. CopperLib pin: `50655eff5613690a606c9dd1de456b2adae249df`.
The installed, locked compiler and managed dependency inventory were used for
acceptance, not an editable sibling compiler or executable layout generator.
Legacy scenes/JSON assets remain historical selection and equivalence fixtures.
Canonical generated asset hashes change with the source format and explicit
footprint identities; old JSON hashes are not relabeled as current evidence.

Validation: ERC passes; the final installed compiler passes 70 consumer tests and 34 subtests, with one
retained-review-artifact case skipped. With the reviewed library supplied, all eight
revision-builder tests also pass, including fresh RF-layout and RF-support source
using the migrated corner and enabled-power-output definitions. The exact legacy/source pad/net maps,
member poses, rigid clusters and physical copper compare equal after excluding
only the changed asset identity. Both terminated TPS63020 probes pass independent
KiCad 10.0.6 refill/DRC at 0, 90, 180 and 270 degrees: zero violations and zero
unconnected items in all eight reports. Outputs are under ignored
`build/macro-definition-final-power-probes/`; they are geometry fixtures, not converter
current/thermal/EMI or assembly qualification.

The engineering plan points to the current pinned library contracts and actual
macro source inputs. Contract requirements and stackup data are unchanged;
Nordic/GNSS source-reference lists have advanced with the pinned library.
The path/source transition is recorded in `build/macro-definition-evidence-paths.json`.
No old report is promoted to current evidence; operating-envelope review and the
evidence map remain incomplete/empty.

The showcase retains its original PCB, native reports, rendered assets and all
original hashes. It is explicitly historical. Twenty exact original composition
inputs (including original checkout line endings) are archived under
`docs/showcase/source-inputs/` and verified against the retained hashes. Git text
normalization is disabled for those archived bytes. This avoids claiming that
the current source or new dependency inventory generated the old figures.

The assembly lock is unchanged and remains stale for current inputs. No fresh
full-board route, manufacturing qualification, assembly approval or ordering is
claimed. Generic compiler/routing work remains in CopperScript; reusable macro
definitions remain in CopperLib; board composition/evidence remain here.
