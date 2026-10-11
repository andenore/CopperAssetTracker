# CopperAssetTracker

**A cellular, GNSS and Bluetooth asset tracker — designed as code.**

CopperAssetTracker takes CopperScript's full-vertical example into a standalone,
rechargeable hardware project: an STM32 host, LTE Cat-1 bis connectivity, GNSS,
Bluetooth and motion sensing on a six-layer board. Readable circuit intent becomes
inspectable intermediate representations, placed components, routed copper and
manufacturing review files.

![Actual routed top copper and silkscreen](docs/showcase/routing-top.svg)

*Native KiCad export of the 100 × 80 mm review candidate: 83 placements, 73
physical nets and six copper layers. This is a routed prototype design,
**not a production-approved product**.*

Prototype battery choice: Kjell & Company **32058**, protected 18650, **2600 mAh**.
See [battery integration review](docs/battery-selection.md). It is an external
cell, not a JLCPCB assembly item. The separate battery revision uses a hardware
temperature window targeting roughly 5–35 °C. The combined
[91-component modem-power/battery draft](revisions/modem-power-v1/README.md) adds
CopperLib's pin-associated modem bypass bank, a wider converter output tap and
regional power distribution. ERC/placement and fresh routing checks pass;
native refill/DRC has zero violations and zero opens, with all four modem bypass
feeds verified via-free. Evidence is recorded separately. Temperature guarantees, reservoir bias
derating, assembly and battery/burst-load tests remain pending. The illustrated
83-component board and existing manufacturing files are the unchanged earlier
checkpoint, not fabrication data for the new revision.

## Why CopperScript?

A PCB contains more intent than wires: a capacitor protects a particular pin,
a switching converter has a critical current loop, and an RF feed needs a
reference layout and return path. CopperScript makes that intent explicit,
version-controlled and testable alongside the connections.

- **Readable hardware source:** components, peripheral selection, nets, supply
  domains and physical constraints in `.copper` files.
- **Reusable engineering:** CopperLib parts, footprints, regulator hard macros
  and qualification contracts instead of per-board copies.
- **Inspectable automation:** electrical IR, physical geometry, routing reports,
  native KiCad boards and assembly data at each stage.
- **Honest checkpoints:** missing connectivity and qualification evidence remain
  visible. Gerber generation is not the same as production approval.

## Three repositories, one workflow

| Repository | Owns |
| --- | --- |
| [CopperScript](https://github.com/andenore/CopperScript) | Language/compiler/ERC, physical IR, placement/routing algorithms, KiCad export and generic assessment tools |
| [CopperLib](https://github.com/andenore/CopperLib) | Shared components, footprints, reusable circuits/hard macros, stackup profiles and engineering contracts |
| CopperAssetTracker | This board's composition, power configuration, placement intent, exact BOM and board-specific evidence |

Generic improvements belong in CopperScript; reusable components belong in
CopperLib. This project does not fork the compiler or maintain private copies
of shared parts. Its composition lives in [board.copper](board.copper) and
[power_tree.copper](packages/tracker/power_tree.copper).

## From intent to copper

```text
board.copper + CopperLib imports + pinned dependencies
        ↓ parse, resolve, elaborate and electrical checks
Electrical IR — typed components, nets and supply intent
        ↓ resolve footprints, constraints and hard macros
Physical IR — pads, placements, layers and owned geometry
        ↓ place, escape, route, repair and stitch plane contacts
KiCad PCB — native zone refill and DRC checkpoint
        ↓ export and independently review
Gerbers + drills + BOM + CPL + manifests
        ↓ RF / USB / power / CAM / assembly / prototype evidence
Production approval — a separate engineering decision
```

### Describe the circuit

These excerpts come from the actual tracker source, not a second example circuit:

```copper
import simcom "github.com/andenore/CopperLib/packages/parts/simcom/sim7670g-lngv";
component U_MODEM: simcom.SIM7670G_LNGV;

configure U_MCU.USB_FS as MODEM_USB {
    DP = PA12;
    DM = PA11;
}

net V3V8 {
    PWR.V3V8;
    // Battery-fed USB detection. SIM7672X V1.01 applicability assumed by user.
    // Requires >=3.6 V at pad 24 under burst load; qualification stays open.
    U_MODEM.USB_VBUS;
    U_MODEM.VBAT_1;
    U_MODEM.VBAT_2;
    U_MODEM.VBAT_3;
    C_MODEM_BULK.1;
}
```

The hierarchical `PWR` module composes CopperLib's charger and converter parts
into this board's power tree. Compilation preserves that hierarchy; physical
elaboration resolves actual component references and footprint pads.

### Give placement and routing semantic intent

```copper
component C_MCU: CAPACITOR {
    value = 100nF;
    footprint = "Capacitor_SMD:C_0402_1005Metric";
    role = decoupling;
    decouples = "U_MCU.VDD";
}

constraint copper_zone(GND) {
    id = "top-ground-return"; layers = "F.Cu";
    polygon_mm = "0.5,0.5;99.5,0.5;99.5,79.5;0.5,79.5";
    priority = 1; pad_connection = solid; island_policy = "remove_all";
    allow_same_net_hard_macro_overlap = true;
}
```

The decoupling association feeds generic pin-aware placement and short direct
surface-feed decisions; it does not forbid necessary ground-return vias. The
ground-zone permission lets compatible board/macro fills overlap without allowing
ordinary routing to rewrite immutable converter copper. Native refill still has
to establish connected fill.

### Inspect what the compiler understood

These component fields come from the generated electrical IR. Human-facing
values use ordinary numbers and engineering units (`100 nF`), not scientific
notation. The full IR also carries an exact SI base value for algorithms;
the decoupling properties survive compilation:

```json
{
  "footprint": "Capacitor_SMD:C_0402_1005Metric",
  "modes": {},
  "part": "CAPACITOR",
  "properties": { "decouples": "U_MCU.VDD", "role": "decoupling" },
  "ref": "C_MCU",
  "value": { "unit": "nF", "value": "100" }
}
```

The physical IR then records real geometry. This placement object comes from the
current-source-checked candidate. Coordinates are integer nanometres (52.505 mm,
21.440002 mm), not diagram coordinates:

```json
{
  "footprint": "Capacitor_SMD:C_0402_1005Metric",
  "position": { "x_nm": 52505000, "y_nm": 21440002 },
  "reference": "C_MCU",
  "rotation_degrees": "90",
  "side": "front",
  "source_path": "C_MCU",
  "value": "100 nF"
}
```

Browse the [electrical IR excerpt](docs/showcase/electrical-ir.excerpt.json),
[physical IR excerpt](docs/showcase/physical-ir.excerpt.json), including real track
segments, and [snapshot provenance](docs/showcase/snapshot.json). These small
excerpts are not full IR files or qualification reports. `make compile` produces
the full hierarchical `build/board.json`.

### Place components and preserve reference geometry

![Component placement, pads and courtyards](docs/showcase/placement.svg)

*The same 83 candidate component poses with copper hidden for readability. This
is a placement-only illustration of the routed checkpoint, not a fresh
unconstrained auto-placement or a photograph of assembled hardware.*

The flow combines board-specific fixed anchors, generic placement decisions,
pin-associated decoupling and rigid RF/power hard macros. Macro ownership keeps
critical relative placement and current-loop geometry intact during routing.

### Route, check and iterate

![In2.Cu signal routing](docs/showcase/routing-inner.svg)

*In2.Cu signal routing, viewed from above without mirroring. In1.Cu and In4.Cu
provide ground planes; In3.Cu provides the 3.3 V distribution zone.*

![Bottom copper routing](docs/showcase/routing-bottom.svg)

*B.Cu, also viewed from above. A single-layer image does not show every connection.*

The router is experimental. This checkpoint was reached through bounded routing,
source-backed placement refinement, targeted repairs and native refill/DRC —
not one unattended command that guarantees a finished board. The source/native
guard rejects stale pad nets, changed lands, illegal placement and altered macro
geometry before a checkpoint is reused.

Selected output from the illustrated KiCad 10.0.6 checkpoint:

```json
{
  "component_count": 83,
  "net_count": 73,
  "track_count": 1118,
  "via_count": 367,
  "native_drc_violation_count": 0,
  "native_unconnected_item_count": 0,
  "qualified_release": false
}
```

That last field is intentional: zero opens and DRC violations establish a useful
routing checkpoint, not RF performance, impedance, charging safety or battery USB
operation. The promise is **inspectable hardware automation**: describe intent,
reuse engineering building blocks, inspect each representation, and carry the
evidence to a real release decision.

## Engineering status and evidence

Next steps and acceptance criteria: [production plan](docs/production-plan.md).
Latest actual-geometry findings and verification:
[RF/USB checkpoint](docs/rf-usb-geometry-review.md).
USB whole-channel gates and pad-centre path follow-up:
[USB channel review](docs/usb-channel-review.md).

CAM/RF/power assessment commands, tested scope and remaining qualification blockers
are documented in [engineering qualification](docs/engineering-qualification.md)
and [the tracker checklist](docs/qualification-todo.md). Generic algorithms remain
in CopperScript and reusable contracts in CopperLib.

Standalone CopperScript asset-tracker hardware project, extracted from
`examples/full_vertical` and structured like CopperLedRing. No production order
has been created.

## Hardware

- STM32G0C1RET6 host, nRF52832 BLE radio, LIS2DW12 motion sensor, MAX-M10S GNSS.
- SIMCom **SIM7670G-LNGV**, LTE **Cat-1 bis**, JLCPCB **C45935408**.
  Replaces EG800G-EU with its 24 x 24 mm / 124-land footprint and actual used-pin
  connections, 1.8 V UART/STATUS translation and open-drain PWRKEY.
- USB-C power input and **BQ24072RGTR** 1S Li-ion power-path charger.
- Three-pin SMT **JST XH battery connector**: 1 BAT+, 2 GND, 3 pack NTC.
- Two TPS63020DSJR buck-boost supplies: 3.3 V logic and switchable 3.8 V modem.
- Nano-SIM, two U.FL RF connectors, two SWD headers, debug UART, button/LEDs.
- Provisional 100 x 80 mm six-layer board; preserved Nordic/Johanson RF hard macro.

All 83 populated references have exact candidate manufacturer part numbers and
JLCPCB codes in [assembly.lock](assembly.lock) and
[procurement/parts.json](procurement/parts.json). The readable
[candidate BOM](procurement/candidate-bom.csv) is for sourcing, **not assembly signoff**.
41 of the 43 retained identities returned `jlcOnSale=1` in the earlier public EasyEDA catalogue check;
the USB connector and Coilcraft filter were checked on JLCPCB part pages.

The modem's exact C45935408 stock record reported **22** on 2026-10-09.
JLCPCB requires **Standard PCBA and X-ray inspection** for it. Recheck stock
before ordering; do not select the similarly named consignment C9900162595.
See [component evidence](docs/component-evidence.md).

## Build

Install [uv](https://docs.astral.sh/uv/), Git, GNU Make and KiCad 10.
The compiler, CopperLib and KiCad footprints are pinned to published Git commits:

| Dependency | Revision / lock |
| --- | --- |
| CopperScript | `209e4998223283923c3f1f0fb52f6fb97791cf46` in `pyproject.toml` and `uv.lock` |
| CopperLib | `f54a03b36e8a785eb512626b3f5110a7f321e37c` in `copper.mod` and `copper.lock` |
| KiCad footprints | `7ebfa6b23cc292a56f751b7b5f4a0e12eeef69dd` in `copper.mod` and `copper.lock` |

No sibling source checkout is needed and no compiler code is copied into the
project. `copper.lock` binds the complete supported-asset inventories; `uv.lock`
pins the compiler dependency. Run from this directory:

The engineering plan refers to contracts/profile files in that exact library
commit's verified `.copper-cache` directory, populated by `make fetch`.
They remain library-owned; no sibling checkout or copied contract is required.

```sh
make fetch             # online bootstrap; preserves pinned versions
make check test compile
make pcb               # placed, unrouted PCB + readiness report
make render            # front/back SVG
make edit              # shared mechanical editor
make route             # experimental full-board routing
make verify            # native KiCad refill/DRC of routed board
make power-probes      # isolated regulator macros, all cardinal rotations
make assembly          # check approved exact selections and export BOM
make manufacturing     # reviewed BOM + route + native DRC required
```

Windows: `.\build-windows.ps1 -Target fetch`, then
`.\build-windows.ps1 -Target all`; optional `-Uv` and `-KiCadCli` paths.
Default `make` checks/tests/compiles/places; it does not order anything.
The pictured repaired checkpoint is not guaranteed to be reproduced by a fresh
bounded `make route` run. `make manufacturing` creates review exports and skips
independent CAM; it is not a production-approval shortcut.
Use pinned managed footprints, not a different system footprint revision;
the RF and both regulator macros' geometry identities are checked before
materialization. The reusable regulator assets are owned by CopperLib, not
this project. Their native geometry checks do not qualify power performance.

README illustrations and compact example data live under `docs/showcase`.
Bulky build attempts, manufacturing archives, dependency caches and downloaded
vendor PDFs remain excluded from Git. To regenerate these snapshots from a local
source-matched candidate with adjacent `manifest.json` and `drc.json`:

```powershell
uv run --locked python scripts/generate_readme_assets.py `
  --pcb build/fabrication-prototype-rf-20261010/routed.kicad_pcb `
  --kicad-cli "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
```

These are native KiCad SVG exports; `snapshot.json` records source/candidate hashes.

## Battery and firmware

Use a **protected 1S, 4.2 V maximum Li-ion/LiPo pack**, a compatible pack-mounted
10 kohm NTC and wiring rated for measured modem peaks. Verify harness pin
numbering/polarity physically: this is not a generic two-wire battery pinout.
No battery, harness, SIM, external LTE/GNSS antennas or firmware is supplied.
Do not use LiFePO4, 2S or an unprotected cell.

The charger uses USB500 mode and about 405 mA nominal charge current. Modem
bursts require the battery; USB-only operation is not qualified. PC10 enables
the modem rail, PC0 controls PWRKEY and PC1 reads translated STATUS.
Keep Nordic DC/DC disabled (LDO circuit) and tune the 32 MHz crystal loads.
USB-C is **power-only**; the MCU/modem USB pair is internal. Modem USB detection
now shares the battery-fed switched 3.8 V rail, separate from external USB-C VBUS.
SIM7672X V1.01 applicability is assumed by user instruction; voltage/transient
margin and firmware/bench operation remain unqualified. See
[battery USB implementation](docs/usb-battery-power.md).

## Not ready to order

ERC and package resolution are source checks, not hardware qualification.
The user-approved BOM has 83 reviewed exact selections; this does not approve
CPL, RF/power/interface performance, CAM/DFM or an order.

Remaining work includes independent CAM/DFM review; RF/USB impedance,
matching, return-path and signal-integrity evidence; power/current/transient
and charging-thermal validation; CPL centroid/rotation/polarity approval and
fresh supplier checks; firmware and prototype measurements. Under the assumed
SIM7672X guidance, battery-fed USB detection has only about **60 mV static
downward margin**, before ripple and transient effects: operation must be
measured, not inferred from connectivity.

The regulator macros pass isolated native DRC in cardinal rotations and use
owner-scoped width contracts. That does not qualify converter performance.
CAN and four dedicated parts have been removed to free routing space. The
source-backed placement/route refinement history is in
[routing-quality review](docs/routing-quality.md); earlier checkpoints and
exports are historical, not approval of current source.

See [power design](docs/power-design.md),
[validation status](docs/validation.md), [routing attempts](docs/routing-attempts.md)
and [manufacturing review](docs/manufacturing-review.md) for the detailed evidence.

The current BOM is now approved by user instruction (83 exact selections / 43
identities), separately from pending CPL/board approval. The selected construction
is JLC06161H-3313, nominal 1.6 mm, outer 1 oz / inner 0.5 oz. Actual RF/USB
screening found unresolved impedance/reference-model issues; see
[stackup selection and follow-up](docs/stackup-selection.md). No production order
is authorized by this assumption.

The current prototype-review candidate has zero native violations/opens. It
preserves battery-fed USB detection and all non-cellular routing, while moving
J_CELL beside the actual west-facing modem antenna edge. The via-free cellular
feed is now about 18 mm instead of 36 mm, within the assumed SIM7672X guide's
20 mm limit. This does not qualify its impedance, matching or launch geometry.
Fresh review Gerbers/drills are in `build/fabrication-prototype-rf-20261010`, with
assembly review in `build/assembly-prototype-rf-20261010`. These supersede the
earlier candidates for current-source review, not production approval. See the
[prototype checklist](docs/prototype-plan.md) for unresolved design decisions
and the exact candidate/check provenance; no order has been placed.
