# Website showcase

`make showcase` rebuilds the board pictures on the CopperScript website
without KiCad (`scripts/showcase.sh`):

1. `copper check`, then `copper route-board` with the Makefile's route settings
   and `--verify-plane-fill native`, into a fresh
   `build/board/runs/<UTC time>-showcase/`.
2. `copper fill` of the routed board, `copper plot` of the filled board and of
   the unfilled one, and `copper drc --cam` of the filled board, which also
   reads the plotted copper and drills back against the netlist. The printed
   antennas' radiator ends are excused with `--expected-open-ends` from the
   route report, which lists exactly the open ends its native verification
   attributed to the synthesized antennas.
3. `copper render` of five views from the plotted Gerbers into
   `docs/showcase/`: top copper with silkscreen, In2.Cu, bottom copper, all six
   copper layers without zone fills (from the unfilled plot), and placement
   (front silkscreen and solder-mask openings). Gold is exposed copper: copper
   inside the solder-mask openings. Every view is from above, unmirrored.
4. The IR excerpts (`C_MCU` with its `decouples` association and the `V3V8`
   net from `copper compile`; the `C_MCU` and `U_MODEM` placements from the
   board) and `snapshot.json`, which binds the tracker commit and input hashes,
   the compiler commit and executable hash, the route, DRC and CAM results and
   every published asset by SHA-256.

Then, from CopperScript, copy the assets to the website and check them:

```sh
scripts/update_site_showcase.sh --tracker-root ../CopperAssetTracker
node scripts/check_site.cjs
```

Review the website's captions, date and counts against `snapshot.json`.

## Scope

A showcase is a routing review illustration. Native DRC is narrower than
KiCad's and lists what it does not check in `snapshot.json`; the route still
has blocked electrical requirements (counted there); no independent CAM,
manufacturing export, supplier or assembly review is made, and
`qualified_release` is false. `docs/showcase/source-inputs/` belongs to the
earlier `promo-reroute-20261013` candidate ([its record](promo-reroute-20261013.md))
and is kept as that candidate's history.
