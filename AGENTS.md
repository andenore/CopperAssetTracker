# CopperScript entry point

Before design work, run `copper agent-guide`
in the active CopperScript environment. Retrieve individual guide topics and
library contracts as needed. Follow this project's README and build/review targets
for its board configuration and evidence.

Read only task-relevant evidence. Current board status is in `docs/validation.md`;
release criteria are in `docs/production-plan.md`. Do not use old build outputs
as current evidence without checking their input bindings.

If the pinned compiler lacks the guide, explicitly select a current compiler for
guidance/review as the README describes; retain the project's build pins. Generic
algorithms belong in CopperScript; reusable definitions belong in library
repositories. Keep board-specific composition and qualification evidence here.

## Rust layout migration

Read docs/project-migration.md before using historical scripts or build evidence.
Build with the Makefile (README "Build"): each target is a plain call of the
Rust `copper` compiler. Old compiler-internal Python helpers
are migration references; do not install them into the normal build or weaken
their checks. Footprints come from the managed modules pinned in copper.mod,
never from a local KiCad installation. Historical evidence is not refreshed by moving files.
