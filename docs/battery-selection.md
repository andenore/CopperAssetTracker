# Accessible prototype battery

Selected for integration review: **Kjell & Company 32058**, protected 1S 18650,
2600 mAh. [Norwegian product page](https://www.kjell.com/no/produkter/elektro-og-verktoy/batterier/litiumbatterier/kjell-company-18650-li-ion-batteri-36-v-2600-mah-p32058).
Downloaded official HTML marks it in stock on 2026-10-10. Recheck stock before
buying; no local store, quantity, purchase or reservation is established.
Do not substitute article 32088: that USB-C model explicitly cannot be charged
through its terminals.

The prior Biltema 84-1378 candidate is not the selected battery: its official
catalogue explicitly says no internal protection and gives 4200 mV maximum,
below the BQ24072 guaranteed 4230 mV maximum. Do not silently grant a tolerance
that Biltema does not publish.

Reusable source facts live in CopperLib under `packages/batteries/kjell/32058`,
both charger variants, `packages/sensors/semitec/103at-2` and
`packages/battery-holders/mpd/bh-18650-w`. Project-specific choice and
connector bindings live in `battery-selection.json`. The new library companions
are working-copy data, **not yet pinned by this project's copper.lock**.

## Earlier locked circuit: why a revision is needed

The linked Kjell pack specification allows 4200 mV +/-50 mV: the current
charger's 4160-4230 mV regulation range fits that published window. This is a
conditional voltage screen, not approval of the complete battery integration.
Confirm the current retail revision matches the linked A1 datasheet; the nominal
voltage labels differ. Use pack limits rather than the higher bare-cell currents.

The pack charging range ends at 45 C. The present direct 10 kohm NTC circuit is
nominally about 0-50 C, and sensor/current/threshold tolerances are not reviewed.
It is not a suitable guaranteed cutoff design. CE is presently tied to ground:
firmware alone cannot disable charging. TI's published Rs/Rp adaptation extends
the temperature window; it cannot be assumed to tighten it. Die temperature
regulation is not cell temperature protection.

The present 2200 ohm +/-1% ISET resistor and TI's 797/890/975 A-ohm bounds imply
approximately 359-448 mA, nominal 405 mA. These are static programming bounds,
not actual charge current under input/thermal limiting or system load. The open
TMR fast-charge timer is 14,400-21,600 s (4-6 hours). Charging this capacity at
the nominal current takes over 6 hours even before taper, so full recharge from
empty cannot be presumed. Review the timer/current/source budget together;
do not disable the safety timer simply to suppress a timeout.

## Integration checklist

- [x] Choose a protected, replaceable cell sold through a Norwegian retailer.
- [x] Record exact primary references and separate retail/pack facts in CopperLib.
- [x] Add a content-bound compatibility screen using existing CopperScript algorithms.
- [ ] Confirm current retail/datasheet equivalence and protection trip/recovery data.
- [x] Select MPD BH-18650-W, explicitly intended for protected 18650 cells.
- [ ] Verify actual fit/retention for the pack up to 71,500 um long; the holder's
  body length is not a published maximum accepted cell length or current rating.
- [x] Select cell-mounted Semitec 103AT-2 and a voltage-based BQ24072T TS circuit.
- [ ] Establish guaranteed cutoff bounds inside the pack charging range,
  including sensor curve, leakage, resistor drift and cell-temperature tracking.
- [ ] Review a three-wire harness: J_BAT pin 1 protected positive, pin 2 protected
  negative, pin 3 thermistor returning to protected negative. Insulate/thermally
  attach the sensor to the cell; do not solder directly to the removable cell.
- [ ] Qualify holder/harness/contact resistance, connector current and full supply
  path for modem bursts at minimum battery voltage. The pack's 3000 mA continuous
  rating is not evidence of an adequate pulse trip threshold or board ampacity.
- [ ] Resolve charger timer/input/thermal budget and modem distribution/local
  bypass findings in `prototype-plan.md`; newly added parts require BOM review.
- [ ] Publish/pin reusable data and bind the final selection into the main
  engineering plan before generating any upload/release package.
- [ ] Re-route/refill/DRC and regenerate source-bound assembly/CAM/qualification
  files after electrical changes; measure actual battery-only USB and burst load.

## Lower-temperature hardware revision

Selected nominal design target: roughly **5–35 °C**. A separate board composition
in `revisions/battery-v1/power_tree.copper` changes U_CHARGE to **BQ24072TRGTR**
(BQ24072T, JLC C129319). This voltage-based TS variant permits a narrower
window. TI's pin mapping and RGT0016C package were checked against the reference
layout/drawing; do not substitute a BQ24075T/BQ24079T or the non-T charger.

The reusable CopperLib module uses 43 kohm upper, 39 kohm shunt and **100 kohm
TS isolation**, with 1% resistors. Isolation follows TI Figure18/p26 because
the upper resistor is below 100 kohm. J_BAT pin 3 now connects the cell-mounted
NTC to the divider; TS connects only through the isolation resistor. CE and TD
remain grounded; charging-temperature inhibition is independent of firmware.
There is a 2 mm pin-to-pin limit on the isolation-to-TS connection and a via-free
F.Cu rule. Charger capacitors now carry pin-specific decoupling roles as well as
their short-distance constraints. Small-signal returns must not carry modem load
current; the physical routing/thermal/harness review is still required.

Under the explicitly provisional **5% R/T envelope** and **100 nA TS leakage**
budgets, the generic CopperScript corner calculation blocks charging at sensor
0 °C and 40 °C, and for ideal NTC open/short faults. These are mathematical
screens, **not guaranteed trip temperatures**. Catalogue R25/B tolerances do
not establish a guaranteed full R/T curve, TI does not specify TS leakage in
its EC table, and the still-air sensor time constant is not a cell-tracking
guarantee. Isolation, arbitrary wiring faults, thermal lag and ground error need
independent review/testing. Never attach the sensor electrically to a bare cell.

Charge regulation is now **4160–4240 mV**, conditionally inside the linked pack's
4150–4250 mV range, leaving only **10 mV** upper static margin. Retail/datasheet
equivalence and actual charging transients are unresolved. ISET remains 2200 ohm:
static programming is **359–448 mA**. TMR is now **68 kohm**, giving nominal
**30,600 s** and independent corners **23,562–37,774 s**. Its minimum remains
shorter than the full-capacity constant-current time at minimum programmed
current even before taper; this is an improvement, not a complete recharge proof.
Do not disable the safety timer or silently increase the USB source budget.

The draft contains **87 components on six layers**, with no ERC errors or
represented placement rejection after moving five charger-support parts and
preserving the other 78 existing poses. Its placement-only native check reports
no non-connectivity errors; dangling macro copper and unrouted connections are
expected and remain open. It is **not a routed production PCB**. Earlier routed
files and canonical package/BOM locks remain untouched; new candidates and the
draft assembly snapshot are unreviewed, and the working library/compiler are
explicit local replacements rather than a published release pin.

Selected external holder: MPD **BH-18650-W**, with 24 AWG leads of 150 mm,
listed by [DigiKey Norway](https://www.digikey.no/en/products/detail/mpd-memory-protection-devices/BH-18650-W/3029217).
No exact current rating/contact resistance or accepted pack length is established.
Fit, retention, wire/connector losses and cell protection trip/recovery must be
validated before full-power charging/modem tests. The cell, holder, NTC and
insulated harness are not JLCPCB assembly components. Crimp/terminate holder and
sensor leads to the specified connector assignment; verify polarity by measurement
before connecting the board. A ready-made 18650 cable is not automatically safe.

Build and screen with the explicit current working copies; pick fresh output
names on repeat runs:

```powershell
uv run --project ../CopperScript python scripts/review_battery_revision.py --library-review-root ../CopperLib --output build/battery-revision-20261010-v3.json
uv run --project ../CopperScript python scripts/build_battery_revision.py --library-review-root ../CopperLib --kicad-footprint-root .copper-cache/pkg/0c22bbbc033f71e79d6d --pose-seed build/fabrication-prototype-rf-20261010/routed.kicad_pcb --output build/battery-v1-20261010-v7
```

The builder checks actual compiled resistor values and TS/timer/enable/pack
topology before screening, generates full-board IR and a draft assembly lock,
validates actual footprint/macro placement and writes a placed-unrouted PCB.
It never imports historical ordinary copper or overwrites previous builds.
Numerical checks have **6 pass, 7 incomplete**, and `qualified_release=false`.
The main engineering plan now hashes battery selection/revision inputs so old
reports cannot silently qualify the new release decision.

Verification: **40 focused CopperScript tests**, **141 CopperLib tests passed
(31 skipped)** and **57 tracker tests plus 32 subtests passed** using the explicit
working compiler/library. Skipped library tests are not qualification evidence.
Next: confirmed cutoff/thermal/harness evidence, timer completion, updated
routing/assembly/stock checks and the outstanding modem/RF/USB work in
`prototype-plan.md`. No supplier upload, purchase or production approval occurred.

## Reproduce the bounded review

From this project, with the new CopperLib working copy explicitly supplied:

```powershell
uv run --locked python scripts/review_battery_selection.py --library-review-root ../CopperLib --output build/battery-selection-20261010-v2.json
```

The output is exclusive: preserve old reports and choose a new name for a later
review. Exit 1 means a failed screen; exit 2 means unresolved checks. Neither
authorizes charging or ordering. A power-source hash mismatch invalidates both
voltage and nominal-temperature screens. No PCB, BOM or lock is modified.
The report hashes inputs and shared algorithms, has `qualified_release=false`,
and explicitly identifies its **unlocked** library review. It is separate from
the earlier native RF/CAM reports, which do not assess this battery selection.

Earlier checkpoint verification: 52 tracker unit tests and 12 focused CopperLib tests
pass. The final battery screen reports 2 pass, 1 fail and 5 incomplete; the
failure is the nominal hot cutoff, not a test execution error. No new battery
charging approval, supplier upload, purchase or production release was made.
