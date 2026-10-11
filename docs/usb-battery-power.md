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
VSYS as substitutes. Sharing the detect rail does not require a separate regulator.

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



Latest routed status is in [validation](validation.md); complete the candidate-bound
firmware, power-transition and bench evidence in [production plan](production-plan.md).
