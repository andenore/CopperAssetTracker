# USB channel qualification checkpoint - 2026-10-10

Historical geometry checkpoint: USB detection has since moved from external V5
to switched V3V8 under the user's SIM7672X V1.01 applicability assumption. See
`usb-battery-power.md` for current connectivity and newly bound reports. The
candidate/reports below predate that source change and are not current release proof.

Continues stage 1 of `production-plan.md`; no component, board copper or firmware
changes are made. BOM approval is retained. This is not production approval.

## Whole-channel gate

`usb-link` now binds CopperLib's reusable USB 2.0 contract in
`docs/engineering-plan.json`. It covers MCU-to-modem communication through FL_USB,
including both pairs of routed net sections and the inline common-mode filter.
Mandatory requirements are operating-mode and layout design review, impedance
and signal-integrity simulation, and prototype electrical/function measurements.
They cannot be replaced by geometry or assumed pass flags. CopperScript validates
stages, mandatory coverage, reviewed report bytes and current-input bindings.

The official USB-IF 2025-06-03 ZIP and base specification PDF are pinned in the
library contract. The full-speed load/timing figure was visually inspected using
the PDF workflow. Mode-applicable ECNs and exact transceiver/filter models still
require review. Native report kind `rf-power` is retained for compatibility and
now includes interface gates; the old statement that USB was only auxiliary is
superseded for this tracker.

## Bounded pad-centre paths

CopperScript `route_path_geometry` operates on exact native straight centrelines,
physical pad centres/layers and verified through-via types. It splits at exact
coincidences, rejects ambiguous/cyclic shortest-path guesses and separates
off-path copper. It does not infer component internals, pad-area/copper-edge
contacts, filled zones, electrical delay or full-artwork connectivity.

The four tracker paths are simple chains: no branches, off-path track segments
or disconnected track islands in this bounded graph. Terminals are MCU pads
44/43 to FL_USB pads 1/4, then FL_USB pads 2/3 to modem pads 27/28.
Track lengths remain 27.478/25.589 mm before FL_USB and 17.887/18.517 mm after it.
Summed DP/DM track lengths are about 45.365/44.106 mm; the 1.259 mm difference
excludes filter internals, pad fields and via delay and is not electrical skew.

Each modem member uses two F-to-In2 transitions through full-depth vias. The
published construction gives 0.6897 mm between used layer centres and 0.8137 mm
of unused barrel below In2 at each site. These are construction-based geometric
estimates, not measurements or an EM stub/resonance qualification. Do not assume
backdrilling is needed solely from these numbers.

| Site | Signal via position (mm) | Nearest spanning GND via distance |
| --- | --- | --- |
| Filter-side DP | 36.555, 32.405 | 3.181 mm |
| Filter-side DM | 37.445, 32.405 | 4.065 mm |
| Modem-side DP | 34.000, 22.945 | 5.676 mm |
| Modem-side DM | 34.000, 22.055 | 4.992 mm |

The source's 2 mm return-via condition uses `reference_change` with declared
shared In1 GND, not an unconditional via-distance rule. Thus these raw distances
alone do not prove a source-rule violation. But the shared-reference premise
needs real review: In2 is much nearer In3 V3V3 than In1 GND, and conservative
projected coverage fails locally on both adjacent planes. Model the actual
openings, launches and power-plane-to-GND return transfer before accepting the
exception or changing routing/stitching. A nearby via would not by itself close
that review either.

## Signalling mode and power-state issue

The [ST STM32G0C1 datasheet](https://www.st.com/resource/en/datasheet/stm32g0c1mc.pdf)
establishes full-speed USB host/device capability, and the board configures USB_FS.
The candidate host limit is 12 Mbit/s, not a 480 Mbit/s host. Firmware host roles,
clocking, modem full-speed enumeration/descriptors and drivers still require
confirmation. Do not judge this channel using high-speed-only limits by default.

Modem USB_VBUS (pad 24) is wired to external `V5`, while battery power supplies
the modem through the 3.8 V converter. No battery-powered V5 generator is present.
SIMCom's related SIM7672X V1.01 guide describes an active-high USB detect input,
separate from VBAT, and full/high-speed peripheral modes. Its source and Figure 17
review are retained in CopperLib `sim7670g-lngv/usb-review-pending.md`; exact-model
equivalence is still unconfirmed. Consequently battery-only USB cannot be assumed
functional, even though the modem and UART may have power.

The user confirmed on 2026-10-10 that USB must work on battery. UART is not an
acceptable substitute for this requirement. The plan now records battery-only
operation and charging-cable removal, with safe disabled/undervoltage/attach
states and no external connector backfeed. See `usb-battery-power.md` for the
implementation checklist and source blocker. Do not connect a guessed voltage
to USB_VBUS; exact operating/attach limits remain unconfirmed. The mode gate stays
incomplete and the hardware is not yet changed.

## Verification and next actions

Current geometry candidate remains
`build/fabrication-routing-quality-20261010/board.kicad_pcb`, SHA-256
`33adc8ec883a47288d467386e9e0c4992337eac120aa0909223fc6819cf4a270`.
Earlier reports remain historical because plan, library and
native-reader algorithm bindings have changed; do not reuse them as current proof.

Verified this round:

- 127 focused CopperScript path/interface/pair/stackup/engineering/checkpoint/CAM
  and editor-overlay tests passed; 10 focused CopperLib contract/footprint tests
  passed; all 36 tracker tests passed. These are not full upstream suite claims.
- Native current-source poses, pad geometry/net/layer intent, placement and macro
  checks passed for 83 components. Fresh KiCad DRC found zero violations and zero
  opens (`build/drc-usb-paths-20261010.json`); native PCB hash is unchanged.
- Fresh engineering report: 8 pass / 41 incomplete; CAM: 10 pass / 3 incomplete;
  checkpoint: 22 pass / 3 incomplete. No mandatory check failed. All reports
  remain `qualified_release=false`; missing USB external results now count.
- Report paths: `build/engineering-usb-paths-r2-20261010.json`,
  `build/cam-usb-paths-20261010.json`, `build/qualification-usb-paths-20261010.json`.
- Library inventory refresh contains exactly one new locked asset, the 2741-byte
  reusable USB qualification contract, and no other additions/changes/removals.
  Its checksum is
  `sha256:89d822a75d9bf0e6286aad408440f31c62425d33649607f64ee6b05babd71f08`.
  Assembly provenance was refreshed; all 83 exact identities/approved flags and
  all parts/footprints/macros remain unchanged. Inventory/checksum equality passed.
- New `build/assembly-usb-paths-20261010/assembly-review.zip` has 43 BOM rows,
  83 placements and 83 approved selections; CPL is not approved and live stock is
  not checked. It and the unchanged Gerber/drill ZIP pass archive-integrity checks.
- No order, commit or push was performed. Cached source PDFs/ZIP and rendered
  review images are ignored, not redistributed.

Next: implement the confirmed USB battery requirement after exact modem support
is established; model the full-speed
channel, common-mode filter and actual layer transitions/return transfer; then
implement justified hardware changes and regenerate a new candidate. RF antenna,
pack/temperature/load data, CAM/DFM, CPL and bench evidence remain open.
