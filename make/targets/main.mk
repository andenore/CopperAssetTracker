# Settings only; the board remains authoritative for geometry and electrical intent.
SOURCE := board.copper
LAYERS := 6
FAB_PROFILE := jlcpcb-six-layer
ASSEMBLY_LOCK := assembly.lock
CHECK_ARGS :=
ROUTE_ARGS := --candidates 1 --fanout --fanout-maze --package-initial-pair-states 0 --no-early-plane-stitch --plane-stitch-step-mm 0.1 --plane-maze-step-mm 0.025 --plane-maze-budget 50000 --plane-contact-radius-mm 3 --plane-stitch-detour-mm 1.5
ACCEPTANCE_BLOCKER :=
