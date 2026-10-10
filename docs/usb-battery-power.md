# Battery-powered internal USB - requirement confirmed 2026-10-10

The user requires MCU-to-modem USB on battery. External USB-C is a charging/power
input, not the host of this internal link. UART fallback does not satisfy the
requirement. No 480 Mbit/s MCU host capability is assumed.

## Current architecture and accepted design basis

The user instructed "Assume sim7672x applies" on 2026-10-10. Use SIM7672X Hardware
Design V1.01 as this board's design basis, explicitly as a user-approved assumption,
not manufacturer-confirmed equivalence or a global catalogue approval.

`board.copper` now connects U_MODEM.USB_VBUS (pad 24) to the regulated, switched
V3V8 modem rail. J_POWER.VBUS_A/VBUS_B and PWR.VIN5 stay on external input-only V5.
No connection ties a battery-generated rail into the charging connector. VBAT
and USB detection share the same supply, so detection is not separately powered
when that modem rail is removed. Host data-pin shutdown tolerance remains open.

The exact supplier-linked SIM7670X specification, revision 2024.05, was downloaded
and both complete pages rendered/visually inspected. SHA-256:
`12d00aae02bc600ac678f8d478d86e099f3339f9a9a7e2837773e5d9489acb11`.
It is a two-page product brief, not a hardware guide; no USB detect operating
range, input current or sequencing limits are supplied. CopperLib retains the
URL and source review in the modem package. Public SIMCom and carrier-document
searches did not establish exact LNGV hardware-guide applicability; the LilyGO
SIM7670G hardware-guide link actually points to SIM7672X V1.02.

Under the accepted guide, Tables 17/51 specify USB detection at 3.6-5.2 V, whereas
VBAT permits 3.4-4.2 V. Direct regulated 3.8 V is a valid nominal design choice,
not proof that burst droop stays within USB limits. Never use 3.3 V or variable
VSYS as substitutes. No new regulator or BOM identity is introduced this round.

## Static margin screen - not transient qualification

CopperScript's reusable `divider_voltage_window` uses independent resistor and
reference corners and explicit additive regulation budgets. It cannot approve
mandatory simulation/bench evidence. The existing two 330k upper resistors and
100k lower resistor are UNI-ROYAL 0402WGF3303TCE/0402WGF1003TCE; the manufacturer
datasheet's F tolerance code is 1% (2019-02-12 V.3, p2, SHA-256
`11cd644d5d8a34a6d12775afb80bf58d8fc11f0c3b700dbd0f7a59942ceaa5ef`).
Source: https://datasheet.lcsc.com/datasheet/pdf/0a975aaa49b7c97f38a963127be4a823.pdf?productCode=C25778

TI TPS63020 SLVS916I p6 gives feedback 0.495-0.505 V, maximum line/load regulation
0.5% each, and power-save upward offset up to 5%. This board ties PS_SYNC low.
Conservatively allocate -1% / +6% regulation after the divider/reference corners;
do not rely on power-save's positive offset at minimum voltage or during transitions.
Source: https://www.ti.com/lit/ds/symlink/tps63020.pdf, SHA-256
`d117773bb7370fd79377bc70ce987eec3469ea5979547a09df52fca5f95b2e69`.

This limited arithmetic screen gives 3.660334-4.139653 V: only about 60 mV
additional downward margin to USB's 3.6 V limit and 60 mV upward margin to VBAT's
4.2 V limit. Feedback bias/leakage, resistor thermal drift, aging, ripple,
interconnect loss, startup and transmit transients are **not included**. Therefore
the shared-rail design is a prototype candidate, not a qualified battery USB fix.
Measure at pad 24 and all VBAT pins across the actual pack/load/temperature range.
If margins cannot be demonstrated, add a separate regulated detect supply or
review a revised modem supply/feedback design; do not waive the voltage bounds.

## Firmware and power-cycle obligations

Shut down with PWRKEY/AT+CPOF before removing MODEM_EN. Stop USB host traffic and
prevent DP/DM driving an unpowered modem. USB readiness is typically 470 ms in
Table 12, not a guaranteed maximum; firmware must verify enumeration/readiness.
Table 13 requires an off/on interval of at least 2 s, and VBAT must discharge below
1.3 V before another power-on. The converter disconnects its load from the input
in shutdown but does not guarantee an active output discharge; verify the real
capacitor/bleeder discharge. Reset correctness is not proved by MODEM_EN toggling.

The guide's USB sleep mode needs unplugged USB. This shared rail cannot deassert
detect independently of VBAT; low-power USB sleep is not implemented. Do not
advertise that mode without adding attach control and reviewing its sequencing.

## Required states and acceptance

- Battery only, modem enabled: enumerate at supported full speed and transfer
  data with no charging cable, across the approved battery/load/temperature range.
- External power plus battery: the same internal host/device link works while
  charging. The external connector remains input-only.
- Remove charging cable with a healthy battery: internal USB remains functional;
  verify there is no detect dropout or unintended re-enumeration during transfer.
- Modem disabled: no phantom power through detect or DP/DM; firmware stops the
  host link and sequences disconnect/power-down according to exact device limits.
- Battery undervoltage: orderly disconnect/shutdown or specified recovery without
  unsafe pin voltages. Continuous USB below the approved battery range is not
  required; the cutoff range remains unresolved.
- Attach external power: no external VBUS backfeed, rail contention or unsafe
  sequencing. Measure startup/attach waveforms, not merely steady-state voltage.

## Implementation todo

- [x] Bind the confirmed requirement and state names in `engineering-plan.json`.
- [x] Record user-authorized SIM7672X V1.01 applicability and source hash; this
  removes exact-model confirmation as a prerequisite to design work, not bench work.
- [x] Compare the existing regulated V3V8 static budget; keep dynamic margin open.
- [x] Retain reusable source guidance in CopperLib and the arithmetic algorithm
  in CopperScript. No new generic circuit/part is needed for this net change.
- [x] Move USB detection to switched V3V8; keep external input V5 separate.
- [ ] Validate load/startup/backfeed and modem-disabled host data pins; no guessed
  input current, device tolerance, clamp path or battery envelope.
- [x] Preserve all 83 exact BOM placements/43 identities and reviewed flags;
  refresh only source provenance for the changed net.
- [x] Refresh assembly provenance; rebuild/reroute and generate a new versioned
  candidate. Earlier Gerbers do not implement the changed hardware.
- [ ] Attach candidate-bound full-speed/firmware, power-transition and bench
  evidence. A requirement binding is not a passing electrical review.

The source net changed; prior fabrication Gerbers are now historical and do not
implement battery-fed USB detection. Rebuild to a new versioned candidate and
bind fresh reports before using the qualification checkpoint.

## Historical requirement-only checkpoint (before the net change)

All 36 tracker unit tests passed, including the updated battery requirement and
safe-state bindings. The native board hash remains
`33adc8ec883a47288d467386e9e0c4992337eac120aa0909223fc6819cf4a270`.
Library changes this round are Markdown guidance/source notes only; locked part,
footprint, macro and contract assets and approved BOM identities are unchanged.

Fresh `build/engineering-usb-battery-required-20261010.json` has 8 pass /
41 incomplete mandatory checks. Fresh
`build/qualification-usb-battery-required-20261010.json` has 22 pass / 3 incomplete,
revalidating the unchanged `build/cam-usb-paths-20261010.json` against current
artifact/algorithm bindings. Both have `qualified_release=false`; neither has
a failed mandatory check. The USB operating-mode evidence is missing, so these
counts do not indicate that battery USB works. Audit exit code 1 is expected for
incomplete qualification. No order, commit or push was performed.

## Current wired/routed checkpoint

New fabrication candidate:
`build/fabrication-usb-battery-20261010/routed.kicad_pcb`, SHA-256
`70caf673a789d4a6cfb4eaad1cb6247de70ccd1d47bfcc828c2dd438ac74aa31`.
The pre-export routed candidate and the exported PCB both pass the strict
current-source contact/pose/placement/macro guard for all 83 components. Native
KiCad 10.0.6 refill/DRC and the manufacturing export's DRC find zero violations
and zero opens. There are 367 vias/drill hits and 552 netlist contacts.

Native old/new comparison finds exactly one changed pad net, U_MODEM.24 from V5
to V3V8. Only V5/V3V8 track/via geometry changes; USB data and RF copper are
unchanged. All six native copper layers were exported, rasterized and visually
inspected; this is a layout review aid, not impedance/power qualification.

Verification: 39 tracker tests, 144 focused CopperScript qualification/native
reader tests (410 existing warnings), and 10 focused CopperLib contract/footprint
tests passed. Shared locked library asset bytes/checksum are unchanged; Markdown
source guidance and the reusable CopperScript calculation changed, not parts.

Fresh reports: `build/engineering-usb-battery-wired-20261010.json` has 8 pass /
41 incomplete; `build/cam-usb-battery-wired-20261010.json` has 10 pass /
3 incomplete; `build/qualification-usb-battery-wired-20261010.json` has 22 pass /
3 incomplete. No mandatory check fails; all have `qualified_release=false`.
No external simulation/bench result is invented to approve the new USB power path.

Review artifacts:

- `build/fabrication-usb-battery-20261010/gerbers-drill.zip`
- `build/fabrication-usb-battery-20261010/manufacturing-package.zip`
- `build/assembly-usb-battery-20261010/assembly-review.zip`

All three archives pass ZIP integrity checks. The fabrication manifest includes
the unchanged exact BOM; fresh assembly review reports 43 grouped rows,
83 placements and 83 approved selections, but CPL and live sourcing remain
unreviewed. Earlier candidates are retained. No order, commit or push occurred.

Next: qualify actual shared-rail margins over the pack/load/temperature envelope,
implement/verify USB host readiness and safe shutdown/recovery, and measure
battery-only enumeration/data transfer plus charging-cable removal. Independent
CAM/DFM, RF/USB signal models, CPL and the other production gates remain open.
