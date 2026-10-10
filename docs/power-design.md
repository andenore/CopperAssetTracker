# Power architecture and review limits

USB-C VBUS (5 V) -> BQ24072 IN. Protected 1S pack -> BAT.
Charger OUT -> VSYS -> two TPS63020 buck-boost channels.
Neither 5 V nor the variable pack/VSYS voltage directly feeds modem VBAT.

Internal USB detection now uses switched regulated V3V8 with modem VBAT, not
external USB-C VBUS. The user accepts SIM7672X V1.01 applicability; USB detection
must remain at least 3.6 V, stricter than VBAT's 3.4 V minimum. The limited static
corner screen leaves only about 60 mV further droop margin. Actual pin voltage,
startup/shutdown, power-cycle discharge and firmware/bench operation remain
unqualified; see `usb-battery-power.md`. This source change is included only in
the new `fabrication-usb-battery-20261010` review files, not earlier Gerbers.

Each converter uses a 1.5 uH Bourns SRP4020TA-1R5M, 10 uF input,
100 nF VINA decoupling and three 22 uF outputs.
With the nominal 0.5 V feedback reference:

- Logic: 100k bottom, 560k top -> 3.3 V.
- Modem: 100k bottom, 330k + 330k top -> 3.8 V.

A nominal 100 uF ceramic reservoir sits on modem VBAT. Nominal MLCC values
are not effective capacitance under DC bias; verify derating/transients.
No claim of 2 A delivery at every battery voltage/temperature is made.
Review switching loops, converter limits, pack protection and measured modem
bursts. JST rates XH at 3 A with AWG22: choose the actual crimp/harness accordingly.
Firmware must implement a safe low-battery policy above the pack cutoff.

BQ24072 CE, TD and EN2 are grounded. EN1 follows USB VBUS (USB500 mode).
R_ISET=2.2k gives about 405 mA nominal charging; R_ILIM=3.3k is present but
its programmable mode is not selected. TMR is open for the default safety timer.
TS connects to a compatible pack-mounted NTC and must not be bypassed.
Verify charging-current tolerance, pack rating, USB source compatibility and
charger thermals. This charger is not cell protection.

J_BAT: 1 BAT+, 2 GND, 3 NTC; both mounting tabs connect to PCB ground.
Verify actual harness polarity before connection. Logic EN follows VSYS;
modem EN is PC10-controlled with a 100k pulldown. Both supplies use power-save
mode. Standby/sleep current is not qualified; modem peaks need battery support.

The original 5 V-only TPS62130A buck/hard macro is not reused: a 1S pack
falls below a 3.8 V buck output. This project requires a new reviewed power
layout and does not depend on the earlier uncommitted copper-overlap feature.

References: [BQ24072](https://www.ti.com/lit/ds/symlink/bq24072.pdf),
[TPS63020](https://www.ti.com/lit/ds/symlink/tps63020.pdf),
[Bourns](https://www.bourns.com/docs/Product-Datasheets/SRP4020TA.pdf),
[JST](https://www.jst-mfg.com/product/pdf/eng/eXH.pdf).
