# Build algorithms come from the pinned CopperScript dependency.
.DEFAULT_GOAL := all
.NOTPARALLEL:
UV ?= uv
ifeq ($(OS),Windows_NT)
KICAD_CLI ?= $(ProgramW6432)/KiCad/10.0/bin/kicad-cli.exe
else
KICAD_CLI ?= kicad-cli
endif
BOARD := board.copper
BUILD := build
PCB := $(BUILD)/placed.kicad_pcb
ROUTED := $(BUILD)/routed.kicad_pcb
PHYSICAL := --layers 6 --fab-profile jlcpcb-six-layer
LOCKED := --locked --offline
QUALIFICATION_DIR ?= $(BUILD)/manufacturing
QUALIFICATION_PCB ?= $(QUALIFICATION_DIR)/$(notdir $(ROUTED))
QUALIFICATION_RUN ?= candidate-1
QUALIFICATION_REPORTS := $(BUILD)/qualification-$(QUALIFICATION_RUN)
ifeq ($(OS),Windows_NT)
KICAD_PYTHON ?= $(ProgramW6432)/KiCad/10.0/bin/python.exe
else
KICAD_PYTHON ?= /usr/bin/python3
endif
CAM_AUDIT_ARGS ?=
# Explicit current CopperScript command for a review, not a lockfile upgrade.
REVIEW_COPPER ?=
REVIEW_DIR ?= $(BUILD)/autonomous-review
REVIEW_PROFILE ?= balanced
.PHONY: all fetch check test compile pcb edit route route-review render verify assembly manufacturing cam-audit engineering-audit qualification order
all: check test compile pcb

fetch:
	$(UV) sync --locked
	$(UV) run --locked copper lock $(BOARD) --locked
	$(UV) run --locked copper check $(BOARD) --locked
	$(UV) run --locked copper audit-footprints $(BOARD) --locked

check:
	$(UV) run --locked copper check $(BOARD) $(LOCKED)

test:
	$(UV) run --locked python -m pytest tests -q

compile: check
	$(UV) run --locked copper compile $(BOARD) $(LOCKED) -o $(BUILD)/board.json

pcb: check
	$(UV) run --locked copper plan-layout $(BOARD) $(LOCKED) $(PHYSICAL) --candidates 1 -o $(PCB) --report $(BUILD)/placement.json

edit:
	$(UV) run --locked copper edit-mechanical $(BOARD) $(LOCKED) $(PHYSICAL)

# Retained pinned-build checkpoint. New solver reviews use route-review below.
route: pcb
	$(UV) run --locked copper route-board $(BOARD) $(LOCKED) $(PHYSICAL) --candidates 1 --fanout --fanout-maze --package-initial-pair-states 0 --no-early-plane-stitch --plane-stitch-step-mm 0.1 --plane-maze-step-mm 0.025 --plane-maze-budget 50000 --plane-contact-radius-mm 3 --plane-stitch-detour-mm 1.5 --progress --verify-plane-fill "$(KICAD_CLI)" --report $(BUILD)/route.json -o $(ROUTED)

# A bounded route can still exit nonzero with a saved draft. See
# docs/autonomous-routing-review.md for shared rerouting and native checks;
# neither this target nor manufacturing bypasses a failed completion gate.

# Generic orchestration only: no pose seed, selected net/pad or repair script.
# A new directory is mandatory; a failed run retains its truthful draft/report.
route-review:
	$(if $(strip $(REVIEW_COPPER)),,$(error Set REVIEW_COPPER to a current CopperScript command; this target does not upgrade pinned dependencies))
	$(UV) run --locked python -c "from pathlib import Path; Path('$(REVIEW_DIR)').mkdir(parents=True, exist_ok=False)"
	$(REVIEW_COPPER) route-board $(BOARD) $(LOCKED) $(PHYSICAL) --routing-profile $(REVIEW_PROFILE) --fanout-maze --plane-contact-radius-mm 3 --plane-stitch-detour-mm 1.5 --verify-plane-fill "$(KICAD_CLI)" --native-evidence-directory "$(REVIEW_DIR)/native" --report "$(REVIEW_DIR)/route.json" -o "$(REVIEW_DIR)/candidate.kicad_pcb" --progress

render: pcb
	"$(KICAD_CLI)" pcb export svg --layers F.Cu,B.Cu --common-layers Edge.Cuts --mode-multi --fit-page-to-board --exclude-drawing-sheet -o $(BUILD)/layers/ $(PCB)

verify:
	"$(KICAD_CLI)" pcb drc --refill-zones --save-board --format json --severity-all --exit-code-violations -o $(BUILD)/drc.json $(ROUTED)
	$(UV) run --locked python -c "import json; r=json.load(open('$(BUILD)/drc.json')); assert not r['violations'] and not r['unconnected_items'], 'DRC or unrouted connections remain'"

# Exact BOM selections are user-approved; CPL/engineering gates remain separate.
assembly: check
	$(UV) run --locked copper assembly check $(BOARD) $(LOCKED) --lock assembly.lock --report $(BUILD)/assembly.json
	$(UV) run --locked copper assembly bom $(BOARD) $(LOCKED) --lock assembly.lock -o $(BUILD)/bom.csv

manufacturing: assembly route verify
	$(UV) run --locked copper export-manufacturing $(ROUTED) --kicad-cli "$(KICAD_CLI)" --skip-independent-cam --bom $(BUILD)/bom.csv --replace -o $(BUILD)/manufacturing

cam-audit: check
	$(UV) run --locked --extra qualification copper audit-cam $(QUALIFICATION_DIR) --kicad-python "$(KICAD_PYTHON)" $(CAM_AUDIT_ARGS) --report $(QUALIFICATION_REPORTS)/cam.json

engineering-audit: check
	$(UV) run --locked --extra qualification copper assess-engineering $(QUALIFICATION_PCB) --plan docs/engineering-plan.json --kicad-python "$(KICAD_PYTHON)" --report $(QUALIFICATION_REPORTS)/engineering.json

# Audits intentionally stop on incomplete evidence; run the two audit targets
# separately to collect both reports. Choose a new QUALIFICATION_RUN each time.
qualification:
	$(UV) run --locked --extra qualification copper qualification-gate $(QUALIFICATION_DIR) --plan docs/engineering-plan.json --cam-report $(QUALIFICATION_REPORTS)/cam.json --engineering-report $(QUALIFICATION_REPORTS)/engineering.json --report $(QUALIFICATION_REPORTS)/gate.json

order: manufacturing cam-audit engineering-audit qualification
	$(UV) run --locked python -c "print('Recheck live stock, RF/battery qualification and JLC Standard PCBA BOM/CPL preview before uploading build/manufacturing. This command does not order anything.')"
