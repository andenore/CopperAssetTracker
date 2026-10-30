# Accessible prototype battery

Selected for integration review: **Kjell & Company 32058**, protected 1S 18650,
2600 mAh. [Norwegian product page](https://www.kjell.com/no/produkter/elektro-og-verktoy/batterier/litiumbatterier/kjell-company-18650-li-ion-batteri-36-v-2600-mah-p32058).
Recheck live stock before buying; no local store, quantity, purchase or reservation is established.
Do not substitute article 32088: that USB-C model explicitly cannot be charged
through its terminals.

Reusable source facts live in CopperLib under `packages/batteries/kjell/32058`,
both charger variants, `packages/sensors/semitec/103at-2` and
`packages/battery-holders/mpd/bh-18650-w`. Project-specific choice and
connector bindings live in `battery-selection.json`. The new library companions
are working-copy data, **not yet pinned by this project's copper.lock**.

## Integration checklist

- [ ] Confirm current retail/datasheet equivalence and protection trip/recovery data.

- [ ] Verify actual fit/retention for the pack up to 71,500 um long; the holder's
  body length is not a published maximum accepted cell length or current rating.

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
- [ ] Refresh native/assembly/CAM evidence for changed inputs and measure
  actual battery-only USB and burst load; current routing is in [validation](validation.md).

## Selected hardware and remaining bounds

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

Selected external holder: MPD **BH-18650-W**, with 24 AWG leads of 150 mm,
listed by [DigiKey Norway](https://www.digikey.no/en/products/detail/mpd-memory-protection-devices/BH-18650-W/3029217).
No exact current rating/contact resistance or accepted pack length is established.
Fit, retention, wire/connector losses and cell protection trip/recovery must be
validated before full-power charging/modem tests. The cell, holder, NTC and
insulated harness are not JLCPCB assembly components. Crimp/terminate holder and
sensor leads to the specified connector assignment; verify polarity by measurement
before connecting the board. A ready-made 18650 cable is not automatically safe.

## Bounded review record

The review script, `scripts/review_battery_selection.py`, drove CopperScript's
internal Python APIs and has been removed; it remains in the history at
`8ac4fea`. Its saved reports stay the record: each hashes its inputs and shared
algorithms, has `qualified_release=false`, and explicitly identifies its
**unlocked** library review. Neither a failed nor an unresolved screen
authorized charging or ordering. Native RF/CAM checks do not assess battery suitability; these are separate
requirements.

The combined modem-power/battery revision is the latest routed review. Follow its
[composition/build guide](../revisions/modem-power-v1/README.md); the canonical root
BOM approval does not approve its new selections.
