# Transitional public-CLI adapter. Proposed copper project/build/package commands are not implemented.
SHELL := bash
.DEFAULT_GOAL := check
COPPER ?= copper
COPPER_RUST_REV := $(strip $(file <.copper-version))
TARGET ?= main
include make/targets/$(TARGET).mk
RESOLVE_ARGS ?= --locked --offline
OUT := build/$(TARGET)
KICAD_CLI ?= kicad-cli
RUN_DIR ?=
EXTRA_ROUTE_ARGS ?=
.PHONY: check compile power-check layout edit fetch install-compiler test-smoke test route route-draft assembly package manufacturing order
fetch:
	"$(COPPER)" lock "$(SOURCE)" --locked
	"$(COPPER)" audit-footprints "$(SOURCE)" --locked
check:
	"$(COPPER)" check "$(SOURCE)" $(RESOLVE_ARGS) $(CHECK_ARGS)
compile:
	"$(COPPER)" compile "$(SOURCE)" $(RESOLVE_ARGS) -o "$(OUT)/board.json"
power-check:
	"$(COPPER)" power-check "$(SOURCE)" $(RESOLVE_ARGS)
layout:
	"$(COPPER)" plan-layout "$(SOURCE)" $(RESOLVE_ARGS) --layers $(LAYERS) --fab-profile $(FAB_PROFILE) -o "$(OUT)/placed.kicad_pcb" --report "$(OUT)/placement.json"
edit:
	"$(COPPER)" edit-mechanical "$(SOURCE)" $(RESOLVE_ARGS) --layers $(LAYERS) --fab-profile $(FAB_PROFILE)
test-smoke:
	COPPER_TEST_BIN="$(COPPER)" node --test tests/rust-cli.test.cjs
test:
	@echo "Full acceptance is not migrated; see docs/project-migration.md. Run test-smoke for the public-CLI subset." >&2; exit 3
# Diagnostic route, not a freshness-checked package/release operation.
route-draft: check
	@test -n "$(RUN_DIR)" || { echo "Set RUN_DIR to a fresh directory under build/$(TARGET)/runs/" >&2; exit 2; }
	@case "$(abspath $(RUN_DIR))" in "$(CURDIR)/build/$(TARGET)/runs/"*) ;; *) echo "RUN_DIR must be under build/$(TARGET)/runs/" >&2; exit 2;; esac
	@mkdir -p "$(dir $(RUN_DIR))"; mkdir "$(RUN_DIR)"
	"$(COPPER)" route-board "$(SOURCE)" $(RESOLVE_ARGS) --layers $(LAYERS) --fab-profile $(FAB_PROFILE) $(ROUTE_ARGS) $(EXTRA_ROUTE_ARGS) --checkpoint-dir "$(RUN_DIR)" --verify-plane-fill "$(KICAD_CLI)" --report "$(RUN_DIR)/route-report.json" -o "$(RUN_DIR)/board.kicad_pcb" --progress
route: route-draft
	@if test -n "$(ACCEPTANCE_BLOCKER)"; then echo "$(ACCEPTANCE_BLOCKER)" >&2; exit 3; fi
assembly:
	@test -n "$(ASSEMBLY_LOCK)" || { echo "No assembly lock selected for this target" >&2; exit 3; }
	"$(COPPER)" assembly check "$(SOURCE)" $(RESOLVE_ARGS) --lock "$(ASSEMBLY_LOCK)" --report "$(OUT)/assembly.json"
package manufacturing order:
	@echo "Unsupported migration operation: shared Rust run freshness/packaging and mandatory client acceptance coverage are not complete. No files exported. See docs/project-migration.md." >&2; exit 3
install-compiler:
	rustup toolchain install 1.97.0 --profile minimal
	cargo +1.97.0 install --git https://github.com/andenore/CopperScript.git --rev $(COPPER_RUST_REV) --locked --force copper
