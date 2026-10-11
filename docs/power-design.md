# Power architecture and review limits

USB-C VBUS (5 V) feeds charger IN; protected 1S pack feeds BAT. Charger OUT
supplies VSYS and two TPS63020 buck-boost channels. Neither raw 5 V nor variable
pack/VSYS voltage directly feeds modem VBAT. A buck-only 3.8 V stage is unsuitable
across a 1S discharge range.

Internal USB detection shares switched regulated V3V8 with modem VBAT. The scoped
SIM7672X V1.01 assumption requires at least 3.6 V at detection, stricter than VBAT's
3.4 V minimum. The static screen leaves about 60 mV droop margin. Startup,
shutdown/discharge, burst and host-data-pin behavior require measurement; see
[USB power requirements](usb-battery-power.md).

## Converters and distribution

Each converter has a 1.5 uH Bourns SRP4020TA-1R5M, 10 uF input, 100 nF VINA bypass
and three 22 uF outputs. With nominal 0.5 V feedback:

- Logic: 100 kohm bottom / 560 kohm top targets 3.3 V.
- Modem: 100 kohm bottom / two 330 kohm top resistors targets 3.8 V.

The 91-part revision adds four pin-associated modem bypass feeds, a widened
converter tap/via bank and regional distribution intent. Native filled continuity
passes; filled necks, via current sharing and impedance remain unqualified.
The nominal 100 uF reservoir needs effective capacitance/ESR evidence under bias
and temperature. No 2 A guarantee across all pack voltages is established.

Logic EN follows VSYS; modem EN is PC10-controlled with a 100 kohm pull-down.
Both converters use power-save mode. Review startup, switching/sense paths,
pack protection, measured bursts and safe low-battery firmware policy.

## Charger and external pack

The latest modem-power/battery revision uses BQ24072T, the 43/39 kohm TS bias
network with 100 kohm isolation and cell-mounted 103AT-2 sensor, targeting
roughly 5–35 degrees C. Its 2.2 kohm ISET has static 359–448 mA bounds; 68 kohm
TMR does not yet establish full recharge including taper. Guaranteed sensor,
leakage, fault, thermal-tracking and charging limits remain open. See
[battery integration](battery-selection.md) for exact bounds and sources.

The separate canonical 83-part source uses non-T BQ24072 with a direct NTC and
open default timer. It is not the selected tighter-window battery implementation.
Do not use the root source's BOM or charging assumptions for the 91-part review.

J_BAT is 1 BAT+, 2 GND, 3 NTC; mounting tabs connect to PCB GND. Verify harness
polarity, protected-cell fit, contact losses and wire/connector ratings. Cell
protection does not replace charger-temperature control; die regulation does not
establish cell-temperature protection.

Latest validation is in [status](validation.md); electrical and release obligations
are in [production plan](production-plan.md). Neither routing nor documentation
establishes battery safety or hardware qualification.
