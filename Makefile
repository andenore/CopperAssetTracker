# CopperAssetTracker board settings. The recipes are CopperScript's shared ones
# (make/board.mk, make/route-build.sh and make/release-build.sh, copied
# unchanged from CopperScript 7df887c); only settings and the project's own
# targets live here.
SOURCE := board.copper
LAYERS := 6
FAB_PROFILE := jlcpcb-six-layer
# Maze fanout and fine plane stitching tuned for this board (the shared
# defaults already set one candidate and fanout). Dense fine regions give the
# 0.4 mm-pitch packages a 0.05 mm grid: on the 0.25 mm base grid the nRF HFXO
# nets (XC1/XC2, F.Cu, no vias) have no legal path past C_DEC3.
EXTRA_ROUTE_ARGS ?= --unified-set fine_regions=dense --fanout-maze --package-initial-pair-states 0 --no-early-plane-stitch --plane-stitch-step-mm 0.1 --plane-maze-step-mm 0.025 --plane-maze-budget 50000 --plane-contact-radius-mm 3 --plane-stitch-detour-mm 1.5

# The CopperScript compiler is the Rust `copper` binary. By default it is built
# from the sibling CopperScript checkout (make copper); set COPPER=copper to use
# an installed binary on PATH, or COPPERSCRIPT to another checkout.
COPPERSCRIPT ?= ../CopperScript
COPPER ?= $(COPPERSCRIPT)/target/release/copper
CARGO ?= $(or $(shell command -v cargo),$(HOME)/.cargo/bin/cargo)

include make/board.mk

.NOTPARALLEL:
SHELL := /bin/bash
# make/board.mk already defines KICAD_CLI (empty: the shared route recipes then
# skip KiCad), so a `?=` default here never applies. Recipes that must run KiCad
# use KICAD_CLI_BIN, which falls back to kicad-cli on PATH.
KICAD_CLI_BIN = $(or $(strip $(KICAD_CLI)),kicad-cli)
# Every footprint is managed: copper.mod maps the KiCad libraries to the pinned
# github.com/KiCad/kicad-footprints commit and copper.lock binds their content,
# so no local KiCad footprint directory is used.

# Each route gets a fresh build/board/runs/<UTC time>-route/;
# build/board/runs/latest-route points at the newest one.
RUNS := $(OUT)/runs
RUN_ID := $(shell date -u +%Y%m%dT%H%M%SZ)-route
ROUTED := $(RUNS)/latest-route/board.kicad_pcb
route: RUN_DIR = $(RUNS)/$(RUN_ID)
route: | latest-route
.PHONY: latest-route
latest-route:
	@mkdir -p $(RUNS)/$(RUN_ID) && ln -sfn $(RUN_ID) $(RUNS)/latest-route
	@echo "Route run: $(RUNS)/$(RUN_ID) (follow: tail -f $(RUNS)/latest-route/routing.log)"

# One legal placement candidate with macro copper; no board-level routing.
layout: PHYSICAL_ARGS += --candidates 1
.PHONY: copper plan si-check render review order test
plan: layout

# Build the Rust compiler from the CopperScript checkout, with its pinned
# toolchain (rust-toolchain.toml applies in that directory); incremental, so a
# no-op when current. Skipped when COPPER names a binary outside that checkout.
check compile layout edit route si-check bom order test assembly-update: copper
copper:
	$(if $(filter $(COPPERSCRIPT)/target/release/copper,$(COPPER)),cd $(COPPERSCRIPT) && $(CARGO) build --release --locked -p copper,@true)

# Board tests: source facts checked through the copper CLI (needs pytest,
# see requirements-test.txt).
PYTHON ?= python3
test:
	COPPER="$(abspath $(COPPER))" $(PYTHON) -m pytest tests -q

# Pre-route signal-integrity screening: impedance from the declared stack-up,
# reference planes, layer groups and length-match groups.
si-check:
	$(COPPER) si-check $(SOURCE) $(RESOLVE_ARGS) --offline --layers $(LAYERS) --fab-profile $(FAB_PROFILE)

# Layer SVGs of the newest routed (and refilled) board.
render:
	"$(KICAD_CLI_BIN)" pcb export svg --layers F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu --common-layers Edge.Cuts --mode-multi --fit-page-to-board --exclude-drawing-sheet --check-zones -o $(RUNS)/latest-route/layers/ $(ROUTED)

# Browse and annotate a board in CopperReview (local web viewer; Ctrl+C stops it).
# Defaults to the newest routed board; its stage follows that route's run.json.
# Point REVIEW_BOARD elsewhere (e.g. $(OUT)/placed.kicad_pcb) and set
# REVIEW_STAGE=placed to review a placement. REVIEW_ARGS=--no-browser etc.
UV ?= uv
COPPERREVIEW ?= ../CopperReview
REVIEW_BOARD ?= $(ROUTED)
REVIEW_STAGE ?=
REVIEW_ARGS ?=
review_stage = $(or $(REVIEW_STAGE),$(if $(filter $(ROUTED),$(REVIEW_BOARD)),$$(jq -e '.status == "passed"' $(RUNS)/latest-route/run.json > /dev/null 2>&1 && echo fully_routed || echo partially_routed),unknown))
review:
	@test -f $(REVIEW_BOARD) || { echo "No board at $(REVIEW_BOARD): run 'make route' first."; exit 1; }
	$(UV) run --project $(COPPERREVIEW) copper-review $(REVIEW_BOARD) --source $(SOURCE) --stage $(review_stage) $(REVIEW_ARGS)

# Complete ordering list: every component on the board, grouped by part, with
# quantity per board, manufacturer and MPN, the assembly route and the recorded
# supplier code. No route needed.
LOCK := assembly.lock
ORDER := build/order
.PHONY: bom assembly-update
bom:
	@mkdir -p $(ORDER)
	$(COPPER) assembly check $(SOURCE) $(RESOLVE_ARGS) --offline --lock $(LOCK) --report $(ORDER)/assembly-report.json
	$(COPPER) assembly bom $(SOURCE) $(RESOLVE_ARGS) --offline --lock $(LOCK) -o $(ORDER)/bom.csv --hand-assembly $(ORDER)/hand-assembly.csv --ordering $(ORDER)/ordering.csv
	@echo "Complete BOM -> $(ORDER)/ordering.csv"

# Rebind assembly.lock to the current source after changes: unchanged
# components keep their selection and review, changed ones keep their
# selection but need review again, new ones are added unreviewed.
assembly-update:
	$(COPPER) assembly update $(SOURCE) $(RESOLVE_ARGS) --offline --lock $(LOCK)

# Prototype order package for JLCPCB PCB + PCBA, built from the newest passed
# route (build/board/runs/latest-route), so run `make route` first. JLCPCB places
# every assembly.lock selection with populate = supplier; hand-assembly.csv lists
# the rest to buy and fit by hand. The files are native-DRC-clean but NOT an
# independently CAM-qualified release (--skip-independent-cam), and the CPL
# keeps KiCad's rotations: check every part in JLCPCB's placement preview.
order:
	@jq -e '.status == "passed"' $(RUNS)/latest-route/run.json > /dev/null 2>&1 || { echo "No passed route at $(RUNS)/latest-route: run 'make route' first."; exit 1; }
	@stale=$$(for f in $(SOURCE) copper.mod copper.lock; do [ $$f -nt $(ROUTED) ] && echo $$f; done); \
	  if [ -n "$$stale" ]; then echo "Routed board predates: $$stale -- run 'make route' first."; exit 1; fi
	@$(MAKE) --no-print-directory bom
	$(COPPER) export-manufacturing $(ROUTED) --kicad-cli "$(KICAD_CLI_BIN)" --skip-independent-cam --bom $(ORDER)/bom.csv --replace -o $(ORDER)/jlcpcb
	@echo "Order package -> $(ORDER): upload jlcpcb/ to JLCPCB; buy and fit hand-assembly.csv by hand."
