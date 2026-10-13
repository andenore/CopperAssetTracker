# Prototype electrical review — 12 October 2026

Scope: the 97-physical / 95-fitted RF-support candidate, composed in
`build/prototype-preorder-v3-20261012/source`. The v2 change explicitly permits
via-free trees on the three branched RF nets; it does not change supply or
charging component values from v1. V3 additionally incorporates the corrected
GNSS open-selector supply model and R08 provenance, without changing hardware
connections, divider values or charge settings. This is a design review, not
electrical qualification or permission to charge the selected cell. Item 6
mechanical fit/test-access work is excluded.

## Supply and battery-powered USB

The source connects modem VBAT and USB detect to regulated V3V8, never battery
VSYS or external input V5. External USB-C is input-only; the MCU is the internal
USB host. Full-speed enumeration on battery remains a required prototype test.
SIM7672X applicability is the user's assumption, not vendor-confirmed equivalence.

CopperScript `divider_voltage_window` uses 495–505 mV reference, 1 percent
resistors, and independent negative 1 percent / positive 6 percent regulation
budgets (including power-save offset). Results below are rounded to whole mV;
rounding is for display, not evidence of additional margin.

| Rail | Feedback upper / lower | Static window | Relevant remaining margin |
| --- | --- | --- | --- |
| Modem | 330 kohm + 330 kohm / 100 kohm | 3660–4140 mV | 60 mV to USB minimum / VBAT maximum |
| Logic | 560 kohm / 100 kohm | 3180–3594 mV | 6 mV to 3600 mV upper limit |

These are not transient or temperature guarantees. Feedback leakage/drift,
effective capacitors, startup, ripple, interconnect losses and load steps are
absent. The logic margin is particularly weak. Do not call either rail qualified
from this calculation. A revised feedback tolerance or converter operating mode
needs exact component/source review and updated source-bound evidence; silently
changing a macro's PS_SYNC connection is not acceptable.

Sources: TI TPS63020 SLVS916I p6, cached
`CopperLib/cache/tps63020-usb-review.pdf`, SHA256
`d117773bb7370fd79377bc70ce987eec3469ea5979547a09df52fca5f95b2e69`;
UNI-ROYAL resistor tolerance code F, datasheet V3 p2, SHA256
`11cd644d5d8a34a6d12775afb80bf58d8fc11f0c3b700dbd0f7a59942ceaa5ef`.
See [USB states and sequencing](usb-battery-power.md) for detect limits,
power-off discharge, USB host shutdown and unsupported USB sleep.

## Charging and protected cell

BQ24072TRGTR regulation 4160–4240 mV is conditionally inside the older linked
Kjell pack specification's 4150–4250 mV range. The 10 mV upper static margin is
not proof of charging safety or current retail/datasheet equivalence.

2200 ohm ISET programs 359–448 mA; system/input/thermal limits can reduce actual
current. 68000 ohm TMR is inside the exclusive 18000–72000 ohm range including
1 percent tolerance. Its fast-charge timer is 23562–37774 s. At 359 mA, charging
2600 mAh requires at least 26073 s at constant current, already longer than the
minimum timer, before taper. Do not promise full recharge, disable the timer or
raise the USB source budget to hide this finding.

The 43000 / 39000 ohm divider and 100000 ohm TS isolation have conditional
0 degC / 40 degC inhibition screens. Assumed 5 percent R/T and 100 nA leakage
are not guaranteed manufacturer bounds. Intended 5–35 degC operation needs
thermal coupling, actual trip and fault verification.

J_BAT: pin 1 protected positive, pin 2 protected negative, pin 3 insulated
cell-mounted NTC returning to protected negative. Measure actual harness
polarity before connection; no bare-cell contact or direct cell soldering.
Protection trip/recovery and full current-path resistance remain unknown.
No mechanical-fit assessment is included here.

Source: CopperLib BQ24072T `charging-limits.json`, sourced to TI SLUS937C;
Kjell `specification.json` retains the older source and applicability gap.
The fresh build's `source/battery-screen.json` binds source and algorithms and
retains all incomplete checks. See [battery selection](battery-selection.md).

## Burst current, capacitance and RF

The four library bypasses, regional V3V8 zone and four converter output-tap
vias express distribution intent. They do not prove minimum plated barrel
thickness, pad-entry current, load sharing or thermal limits.
The exact assembly reservoir is Samsung **CL32A107MQVNNNE**, nominal 100 uF;
previous family product-sheet review does not supply effective capacitance,
ESR and bias/temperature curves for this exact selected ordering identity.
The current [manufacturer product page](https://product.samsungsem.com/mlcc/CL32A107MQVNNN.do)
explicitly lists the E packaging suffix, 1210 size, 100 uF, 6.3 V and
20 percent tolerance. It labels its design data typical; its simulation service
was inaccessible during this review. This confirms ordering identity and
nominal ratings, not a guaranteed bias/temperature capacitance minimum.
Do not enter nominal 100 uF as guaranteed effective capacitance in a droop model.
Peak/RMS load, converter efficiency, cell protection and actual path resistance
must be supplied before a meaningful current/drop or thermal result exists.

GNSS low-gain is the manufacturer default but actual firmware remains unchecked.
u-blox Table43 is typical room-temperature 64QAM/10 MHz immunity data, not
guaranteed band-wide immunity. The baseline omits external SAW; B4327 remains a
future protected redesign. Initial GNSS bring-up disables LTE/BLE transmit;
simultaneous operation needs a controlled experiment and antenna coupling data.
The selected 142 um / 201 um RF cross-section is not a complete launch model.

The current MAX-M10S datasheet is UBX-20035208 R08, 30 January 2026, rather than
the R05 revision recorded in the earlier frozen v2 library model. The downloaded R08
bytes have SHA256
`e36d9c8585809c0dc486804d2634c66cd1888ad71af0f28ce0b830ffa8df6bec`.
Its pin drawing/table (p9) agrees with the selected 18-pad assignments; the
board leaves VIO_SEL open for its shared 3 V supply and does not use VCC_RF
to bias the passive antenna. Tables 12–14 (pp11–12) specify VCC 1760–3600 mV,
V_IO 2700 mV through VCC when VIO_SEL is open, and V_BCKP 1650–3600 mV.
The v2 generic V_IO model minimum of 1650 mV was therefore too permissive
for this mode, although the candidate's static rail minimum is 3180 mV.
CopperLib now pins R08 provenance and conservatively models 2700 mV minimum
for its explicitly open-selector subset, with reusable integer-unit limits in
`datasheet-review.json`. Six library RF-support regressions pass. A fresh v3
source/library lock incorporates this correction and its copied review evidence;
the older v2 source/route is not silently relabeled as using the new model.

R08 also bounds V_IO rise time per volt to 25–35000 us/V: verify the actual
converter ramp at the receiver, not merely the final voltage. Allow up to
100 mA startup current (p13). With VCC and V_IO absent, do not drive receiver
PIOs (p10). RF_IN's 0 dBm absolute maximum is specified for a 50 ohm continuous
wave source; it is not an LTE coexistence performance guarantee. These are
additional prototype checks, not measured results. Source:
[u-blox R08 datasheet](https://content.u-blox.com/sites/default/files/MAX-M10S_DataSheet_UBX-20035208.pdf).
The reviewed R08 source applies to MAX-M10S-00B-01 / ROM SPG 5.10. The selected
JLCPCB ordering description is the unsuffixed MAX-M10S-00B family name; confirm
the actual hardware/firmware revision before applying its source limits and
configuration assumptions. The conservative open-selector model is not a claim
that every warehouse revision has been independently qualified.

## Required prototype controls and unresolved decisions

For the proposed restricted GNSS experiment, keep MODEM_EN inactive and the
internal USB host/data drivers stopped during initial receiver bring-up. Verify
the modem rail is actually off; do not infer transmitter inhibition from a
command that firmware intends to send after boot. BLE transmission must also
remain disabled. Record the actual low-gain receiver configuration/readback,
rail ramp and receiver supply voltage before using the baseline measurements.

The GNSS receiver shares the logic rail: the current source does not provide
an independent receiver power switch. Receiver standby or a firmware flag must
not be represented as physical RF-input protection. Later modem power-up,
battery USB enumeration and transmit-load tests require a separately reviewed
test configuration that prevents uncharacterized receiver exposure. Controlled
antenna isolation/coexistence tests follow those checks; routine simultaneous
LTE/GNSS use is not approved by the restricted experiment proposal.

Before energizing: qualified electrical review, current-limited bring-up,
polarity and rails checked without assuming a battery/charger safety pass.
Before cell charging: resolve source applicability, temperature sensing/faults,
charge regulation and thermal behavior. Before maximum-power modem tests: prove
the supply/current path and detect margin. Before concurrent GNSS/LTE service:
characterize RF coupling and performance. Bench results follow delivery; no
measurement has been invented or treated as already complete.

Fabrication/assembly candidates may be prepared for review while these gates
remain open. Exact prototype risk acceptance and supplier confirmation are
required before any order; preparation is not approval.

The [bring-up checklist](prototype-bringup-checklist.md) defines the proposed
measurement sequence and evidence to retain. All measurement boxes are
unchecked; this is test planning, not a bench or safety pass.
