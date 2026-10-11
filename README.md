# CopperAssetTracker

LLM agents: start with `copper agent-guide` in the selected CopperScript
environment; see [the project pointer](AGENTS.md) for older compiler pins.

**A cellular, GNSS and Bluetooth asset tracker — designed as code.**

CopperAssetTracker takes CopperScript's full-vertical example into a standalone,
rechargeable hardware project: an STM32 host, LTE Cat-1 bis connectivity, GNSS,
Bluetooth and motion sensing on a six-layer board. Readable circuit intent becomes
inspectable intermediate representations, placed components, routed copper and
manufacturing review files.

![Actual routed top copper and silkscreen](docs/showcase/routing-top.svg)

*Native KiCad export of the 100 × 80 mm review candidate: 91 placements, 75
physical nets and six copper layers. This is a routed prototype design,
**not a production-approved product**.*

Prototype battery choice: Kjell & Company **32058**, protected 18650, **2600 mAh**.
See [battery integration review](docs/battery-selection.md). It is an external
cell, not a JLCPCB assembly item. The separate battery revision uses a hardware
temperature window targeting roughly 5–35 °C. The combined
[91-component modem-power/battery revision](revisions/modem-power-v1/README.md) adds
CopperLib's pin-associated modem bypass bank, a wider converter output tap and
regional power distribution. ERC/placement and fresh routing checks pass;
native refill/DRC has zero violations and zero opens, with all four modem bypass
feeds verified via-free. The figures and excerpts below now show this revision's
2026-10-11 source-only routing checkpoint. Temperature guarantees, reservoir bias
derating, assembly and battery/burst-load tests remain pending. The canonical
83-component source, release locks and older manufacturing files are unchanged;
they are not fabrication data for the illustrated 91-component revision.

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
of shared parts. The canonical composition lives in [board.copper](board.copper)
and [power_tree.copper](packages/tracker/power_tree.copper). The illustrated
revision adds [battery/charger composition](revisions/battery-v1/power_tree.copper)
and [regional distribution intent](revisions/modem-power-v1/distribution.copper).
Its source builder composes these inputs; it does not repair routed copper.

### Shared autonomous-routing review

New routing improvements run through CopperScript's standard `route-board`,
not this project's historical selected-net repair helpers. `make route-review`
requires an explicit current compiler command, for example:

```console
make route-review REVIEW_COPPER="python -m copperscript" REVIEW_DIR=build/review-new
```

Activate the current CopperScript environment first. This review target keeps
the board's locked library inputs, six layers and macro assets, uses the bounded
`balanced` profile, and saves native evidence plus a failed or completed draft in
a **new** directory. It does not upgrade compiler pins or replace manufacturing
artifacts. The 2026-10-11 shared balanced and thorough runs each closed all
60 ordinary nets, with zero opens, violations and islands after native refill.
The seven project-local routing/repair entry points have been retired;
read-only checkpoint validation now delegates to CopperScript. See
[closure evidence and migration](docs/autonomous-routing-review.md).
That benchmark uses the canonical 83-part source. The illustrated 91-part revision
also closes through the standard `balanced` CLI: 61 ordinary nets, both USB pairs
and native-verified GND, 3.3 V and 3.8 V fills. It requires neither a historical
placement seed nor board-specific routing repairs. Neither result is production
approval; see [the revision's commands and evidence](revisions/modem-power-v1/README.md).

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

These excerpts come from the generated modem-power revision's tracker source,
not a second example circuit:

```copper
import simcom "github.com/andenore/CopperLib/packages/circuits/simcom/sim7670g-vbat-bypass";
module U_MODEM: simcom.SIM7670G_VBAT_BYPASS;

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
elaboration resolves actual component references and footprint pads. Similarly,
`U_MODEM` composes CopperLib's modem and four pin-associated bypass capacitors;
the modem's physical reference becomes `U_MODEM/U`, without duplicating the
reusable circuit in this project.

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
source-checked 91-part candidate. Coordinates are integer nanometres (54,045 um,
21,190 um, rounded), not diagram coordinates:

```json
{
  "footprint": "Capacitor_SMD:C_0402_1005Metric",
  "position": { "x_nm": 54044976, "y_nm": 21190002 },
  "reference": "C_MCU",
  "rotation_degrees": "0",
  "side": "front",
  "source_path": "C_MCU",
  "value": "100 nF"
}
```

Browse the [electrical IR excerpt](docs/showcase/electrical-ir.excerpt.json),
[physical IR excerpt](docs/showcase/physical-ir.excerpt.json), including real track
segments, and [snapshot provenance](docs/showcase/snapshot.json). These small
excerpts are not full IR files or qualification reports. `make compile` produces
the canonical full hierarchical `build/board.json`; the revision builder produces
its own `electrical.ir.json` in the selected review directory.

### Place components and preserve reference geometry

![Component placement, pads and courtyards](docs/showcase/placement.svg)

*The same 91 candidate component poses with copper hidden for readability. This
is a placement-only illustration of the routed checkpoint, not a fresh
unconstrained auto-placement or a photograph of assembled hardware.*

The flow combines board-specific fixed anchors, generic placement decisions,
pin-associated decoupling and rigid RF/power hard macros. Macro ownership keeps
critical relative placement and current-loop geometry intact during routing.

### Route, check and iterate

![In2.Cu regional modem supply and signal routing](docs/showcase/routing-inner.svg)

*In2.Cu regional 3.8 V distribution and signal routing, viewed from above without
mirroring. In1.Cu and In4.Cu carry ground planes; In3.Cu carries the 3.3 V zone
and a low-current modem USB-detection spur. Connectivity is checked; return-path
performance and current capacity are separate qualification gates.*

![Bottom copper routing](docs/showcase/routing-bottom.svg)

*B.Cu, also viewed from above. A single-layer image does not show every connection.*

The router is experimental. This checkpoint was reached from source through the
standard CLI's bounded placement, routing and native-feedback repair flow.
Shared CopperScript algorithms close the supply-plane contacts while preserving
protected package exits and immutable macro geometry; no project-specific
selected-net repair script is involved. The source/native guard rejects stale
pad nets, changed lands, illegal placement and altered macro geometry before a
checkpoint is reused. Success on this board is not a guarantee for every design.

Selected output from the illustrated KiCad 10.0.6 checkpoint:

```json
{
  "component_count": 91,
  "net_count": 75,
  "track_count": 921,
  "via_count": 314,
  "native_drc_violation_count": 0,
  "native_unconnected_item_count": 0,
  "qualified_release": false
}
```

The shared report records 21 of 21 surface-connected decoupling associations.
An independent checkpoint check also verifies all four modem bypass feeds as
via-free F.Cu chains, with rounded lengths from 2,011 um to 2,763 um. These are
connectivity checks, not proof of effective capacitance or high-frequency power
integrity. The same routing report explicitly retains **11 blocked engineering
requirements**, including RF/USB impedance and reference/return-path verification.

That last field is intentional: zero opens and DRC violations establish a useful
routing checkpoint, not RF performance, impedance, charging safety or battery USB
operation. The promise is **inspectable hardware automation**: describe intent,
reuse engineering building blocks, inspect each representation, and carry the
evidence to a real release decision.

## Engineering status and evidence

Next steps and acceptance criteria: [production plan](docs/production-plan.md).
Historical 83-part actual-geometry findings and verification:
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
- USB-C power input and **BQ24072TRGTR** 1S Li-ion power-path charger in the
  illustrated revision, with a reusable thermistor-bias circuit and timer.
- Three-pin SMT **JST XH battery connector**: 1 BAT+, 2 GND, 3 pack NTC.
- Two TPS63020DSJR buck-boost supplies: 3.3 V logic and switchable 3.8 V modem.
- Nano-SIM, two U.FL RF connectors, two SWD headers, debug UART, button/LEDs.
- Provisional 100 x 80 mm six-layer board; preserved Nordic/Johanson RF hard macro.

All 83 canonical populated references have exact candidate manufacturer part
numbers and
JLCPCB codes in [assembly.lock](assembly.lock) and
[procurement/parts.json](procurement/parts.json). The readable
[candidate BOM](procurement/candidate-bom.csv) is for sourcing, **not assembly signoff**.
41 of the 43 retained identities returned `jlcOnSale=1` in the earlier public EasyEDA catalogue check;
the USB connector and Coilcraft filter were checked on JLCPCB part pages.
The 91-part revision generates a separate candidate assembly lock; its changed
and added selections still need approval. The older lock/BOM is not its CPL or BOM.

The modem's exact C45935408 stock record reported **22** on 2026-10-09.
JLCPCB requires **Standard PCBA and X-ray inspection** for it. Recheck stock
before ordering; do not select the similarly named consignment C9900162595.
See [component evidence](docs/component-evidence.md).

## Build

Install [uv](https://docs.astral.sh/uv/), Git, GNU Make and KiCad 10.
The canonical 83-part build's compiler, CopperLib and KiCad footprints are pinned
to published Git commits; these are not the newer illustrated revision's tool inputs:

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
These default targets build the canonical 83-part design, not the pictured
91-part revision. `make manufacturing` creates review exports and skips
independent CAM; it is not a production-approval shortcut.
Use pinned managed footprints, not a different system footprint revision;
the RF and both regulator macros' geometry identities are checked before
materialization. The reusable regulator assets are owned by CopperLib, not
this project. Their native geometry checks do not qualify power performance.

### Build and route the illustrated revision on Windows

Use a current CopperScript environment containing the native-closure changes
(commit `e6f153d20eaae6e82b9e2ee52af307129187fc7d` or newer) and the reviewed
CopperLib working copy (`df54c3f73cb833a98942d7d4ad326efd189863cb` for the pictured
checkpoint). Activate that compiler environment before these commands, from the
Tracker directory. The managed footprint cache must already be populated by
`make fetch`. Choose a new output directory for each attempt:

```powershell
python scripts/build_battery_revision.py --modem-power `
  --library-review-root ../CopperLib `
  --kicad-footprint-root .copper-cache/pkg/0c22bbbc033f71e79d6d `
  --output build/new-power-review
Set-Location build/new-power-review
python -m copperscript route-board board.copper --offline --layers 6 `
  --fab-profile jlcpcb-six-layer `
  --hard-macro nrf-antenna-macro.json --hard-macro logic-power-macro.json `
  --hard-macro modem-power-macro.json --routing-profile balanced --pitch-mm 0.5 `
  --fanout-maze --soft-ripup --constrained-pins-first --progressive-guides `
  --plane-contact-radius-mm 3 --plane-stitch-detour-mm 1.5 `
  --verify-plane-fill "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe" `
  --native-evidence-directory native-new --report route-new.json `
  -o routed-new.kicad_pcb --progress
```

The first command only composes source, IR and candidate selections; the second
owns placement, routing and native verification. Use the retained **filled PCB**
identified by a successful route report's `plane_verification` evidence. A
failed/incomplete report is not a routed success. Newer tool/library inputs can
change the result; compare their recorded hashes before reusing evidence.

README illustrations and compact example data live under `docs/showcase`.
Bulky build attempts, manufacturing archives, dependency caches and downloaded
vendor PDFs remain excluded from Git. To regenerate these snapshots from a local
source-matched candidate with adjacent native `drc.json` and its matching route
report. From the Tracker directory, using the current compiler environment:

```powershell
python scripts/generate_readme_assets.py `
  --project-root build/latest-power-review-20261011 --unlocked-review `
  --pcb build/latest-power-review-20261011/native-closure-v5/verification-003/CopperAssetTracker.kicad_pcb `
  --route-report build/latest-power-review-20261011/route-closure-v5.json `
  --kicad-cli "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
```

These are native KiCad SVG exports; `snapshot.json` records source/candidate,
composition and evidence hashes. The renderer is documentation tooling, not a
routing repair or a manufacturing export.

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
The user-approved canonical BOM has 83 reviewed exact selections; this does not approve
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

The canonical BOM is approved by user instruction (83 exact selections / 43
identities), separately from pending CPL/board approval. The selected construction
is JLC06161H-3313, nominal 1.6 mm, outer 1 oz / inner 0.5 oz. Actual RF/USB
screening found unresolved impedance/reference-model issues; see
[stackup selection and follow-up](docs/stackup-selection.md). No production order
is authorized by this assumption.

The historical 83-part prototype-review candidate has zero native
violations/opens. It
preserves battery-fed USB detection and all non-cellular routing, while moving
J_CELL beside the actual west-facing modem antenna edge. The via-free cellular
feed is now about 18 mm instead of 36 mm, within the assumed SIM7672X guide's
20 mm limit. This does not qualify its impedance, matching or launch geometry.
Its review Gerbers/drills are in `build/fabrication-prototype-rf-20261010`, with
assembly review in `build/assembly-prototype-rf-20261010`. These superseded the
earlier 83-part candidates for review, not production approval, and do not
describe the illustrated 91-part revision. See the
[prototype checklist](docs/prototype-plan.md) for unresolved design decisions
and the exact candidate/check provenance; no order has been placed.
