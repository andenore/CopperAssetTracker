# Source-driven board configuration

Physical builds use CopperScript's source-driven layer selection. The compiler
revision is pinned in `.copper-version`; the shared layer-selection rules follow
CopperScript `7e70ead`.

| Target | Copper layers | Source requirement |
| --- | ---: | --- |
| main | 6 | Inner-layer zones and routing requirements |

The Makefile's `copper` calls pass no `--layers`. CopperScript uses the declared physical stackup or the smallest
supported stack accommodating layer requirements and the fabrication profile.
An explicit `--layers 4` on a call remains a selection/check; it cannot replace
a conflicting source stackup.

Physical layer requirements, zones and net rules belong in `.copper`.
`FAB_PROFILE` and routing/placement budgets remain build settings: source
fabrication selection and an optional `build` block are not implemented yet.
An inferred layer count does not invent dielectric properties or establish
fabrication, electrical, RF or assembly qualification.

The board sources, dependency manifests/locks and assembly selections are
unchanged by this build migration. Previous routed/manufacturing artifacts
retain their old compiler/input bindings; this migration does not renew them.

## Migration checks (2026-11-10)

Locked/offline ERC passes. One-candidate placement produces byte-identical KiCad boards with inferred layers and explicit --layers 6.

Dry runs of plan, edit, route and si-check omit layer flags by default and
retain explicit LAYERS overrides. The shared layer-selection rules match CopperScript. These are configuration/placement checks, not a fresh full-route,
native DRC or manufacturing qualification.
