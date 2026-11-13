# CopperAssetTracker. Each target is a plain `copper` call, written out in full;
# `copper <command> --help` explains every option. Nothing here needs KiCad.
#
# COPPER is the compiler pinned in .copper-version: build it in the CopperScript
# checkout (cargo build --release --locked -p copper) or pass COPPER=copper.
COPPER ?= ../CopperScript/target/release/copper
PYTHON ?= python3
SHELL := bash
.NOTPARALLEL:
.PHONY: check test si-check layout route render review bom assembly-update order antennas showcase

# Router settings for this board: maze fanout and fine plane stitching. Dense
# fine regions give the 0.4 mm-pitch packages a 0.05 mm grid: on the 0.25 mm
# base grid the nRF HFXO nets (XC1/XC2, F.Cu, no vias) have no legal path past
# C_DEC3.
ROUTE := --fab-profile jlcpcb-six-layer --candidates 1 --feedback-iterations 1 --router-iterations 5 --progress \
  --fanout --fanout-maze --unified-set fine_regions=dense --package-initial-pair-states 0 \
  --no-early-plane-stitch --plane-stitch-step-mm 0.1 --plane-maze-step-mm 0.025 --plane-maze-budget 50000 \
  --plane-contact-radius-mm 3 --plane-stitch-detour-mm 1.5

# Every route is a new build/board/<UTC time>-<pid>/ with a run.json; RUN is the newest.
RUN ?= $(patsubst %/run.json,%,$(lastword $(sort $(wildcard build/board/*/run.json))))

# The synthesized antennas end in tracks that are open by design. The route
# report lists them and the export excuses exactly those. KiCad's DRC cannot,
# so the KiCad cross-check (make route order KICAD=1, kicad-cli on PATH) stops
# on them.
VERIFY := $(if $(KICAD),--verify kicad)
EXPORT = $(if $(KICAD),--drc kicad --plotter kicad,--expected-open-ends $(RUN)/route-report.json)

check:
	$(COPPER) check board.copper --locked

# Board tests through the copper CLI (pip install -r requirements-test.txt).
test:
	COPPER="$(abspath $(COPPER))" $(PYTHON) -m pytest tests -q

si-check:
	$(COPPER) si-check board.copper --locked --offline --fab-profile jlcpcb-six-layer

layout:
	$(COPPER) plan-layout board.copper --locked --fab-profile jlcpcb-six-layer --candidates 1 -o build/board/placed.kicad_pcb --report build/board/placement.json

route:
	$(COPPER) build board.copper --locked $(VERIFY) -- $(ROUTE)

render:
	rm -rf $(RUN)/plot && $(COPPER) plot $(RUN)/board.kicad_pcb -o $(RUN)/plot
	$(COPPER) render $(RUN)/plot --layer F.Cu --layer Edge.Cuts -o $(RUN)/F_Cu.svg
	$(COPPER) render $(RUN)/plot --layer In1.Cu --layer Edge.Cuts -o $(RUN)/In1_Cu.svg
	$(COPPER) render $(RUN)/plot --layer In2.Cu --layer Edge.Cuts -o $(RUN)/In2_Cu.svg
	$(COPPER) render $(RUN)/plot --layer In3.Cu --layer Edge.Cuts -o $(RUN)/In3_Cu.svg
	$(COPPER) render $(RUN)/plot --layer In4.Cu --layer Edge.Cuts -o $(RUN)/In4_Cu.svg
	$(COPPER) render $(RUN)/plot --layer B.Cu --layer Edge.Cuts -o $(RUN)/B_Cu.svg

# Browse and annotate the newest route in CopperReview (Ctrl+C stops it).
review:
	uv run --project ../CopperReview copper-review $(RUN)/board.kicad_pcb --project . --entry board.copper --source board.copper

bom:
	$(COPPER) assembly check board.copper --locked --offline --lock assembly.lock
	$(COPPER) assembly bom board.copper --locked --offline --lock assembly.lock -o build/order/bom.csv --hand-assembly build/order/hand-assembly.csv --ordering build/order/ordering.csv

# Rebind assembly.lock after source changes; changed selections need review again.
assembly-update:
	$(COPPER) assembly update board.copper --locked --offline --lock assembly.lock

# JLCPCB package from the newest route. The export refuses a route that did not
# pass or predates a source change, refills and checks the board itself, and is
# not independently CAM-qualified.
order: bom
	$(COPPER) export-manufacturing $(RUN)/board.kicad_pcb --run $(RUN)/run.json $(EXPORT) --skip-independent-cam --bom build/order/bom.csv --replace -o build/order/jlcpcb

# Full-wave synthesis of the three printed antennas (constraint antenna in
# board.copper); paste the printed geometry and tuned_for lines into the
# declaration. Tens of minutes each: make antenna-lte runs one, SYNTH=--verify
# re-evaluates the declared geometry only. Simulation evidence only.
antennas: antenna-ble antenna-gnss antenna-lte
antenna-%:
	$(COPPER) synthesize-antenna board.copper --locked --offline --fab-profile jlcpcb-six-layer --antenna $* --report revisions/pcb-antennas-v1/$*-synthesis.json $(SYNTH)

# The website pictures in docs/showcase from a fresh route (docs/showcase.md).
showcase:
	bash scripts/showcase.sh --copper "$(COPPER)" --route "$(ROUTE)"
