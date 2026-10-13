# Passive GNSS antenna recommendation

Recommend **Taoglas FXP611.07.0092C** as an external prototype antenna for
U_GNSS (**u-blox MAX-M10S-00B**) through J_GNSS. This is a passive, linearly
polarized flex antenna with 1559-1610 MHz coverage, nominal 50 ohm interface,
92 mm factory cable and U.FL-compatible plug. Its coverage contains the
receiver's GPS/Galileo/GLONASS/BeiDou L1 signals; L2/L5 support is unnecessary
for this receiver. It does not require antenna power or a bias tee.

Exact facts and mandatory RF obligations belong in CopperLib under
`packages/antennas/taoglas/fxp611-07-0092c/`. The board-specific recommendation,
source hashes and sourcing snapshot are in
[gnss-antenna-recommendation.json](gnss-antenna-recommendation.json).
This is a recommendation, not an approved BOM/release update. It deliberately
does not overwrite the previous checksum-bound antenna-selection.json,
cellular review, generated source or retained PCB. The earlier snapshot still
says no exact GNSS antenna had been selected at that time.

## Manufacturer and receiver review

Taoglas datasheet **SPE-13-8-010-G**, pp1-4 and p10, was read; specification
and mechanical drawing were rendered and inspected. Mount on plastic and reserve
**40 x 40 mm** with **200 um** mounting height allowance. Keep at least
**10 mm** between the radiating element and metal or the main device ground
plane. This includes battery metal, and prevents simply sticking it onto the
populated board. Keep the host RF trace's ground reference intact: radiator
clearance and feed return requirements are different.

The nominal body dimensions and p10 drawing differ; the specified 40 mm square
fits their published dimensions, but current tolerances need confirmation.
The connector BOM also uses MHFHT while the specification/title say MHF I;
confirm actual supplied mating/height details before enclosure release.
Reference measurements use a 300 x 300 mm ABS panel, not this tracker enclosure.
Do not guarantee installed VSWR, peak gain or sensitivity from reference values.

u-blox **UBX-20053088 R05**, pp6 and 77-81, establishes integrated 50 ohm
matching, DC blocking, LNA and filtering. A passive antenna is compatible with
this front end. Do not add a generic matching network or active-antenna supply
merely because the antenna is external. The receiver reference explicitly calls
for reviewing additional SAW rejection in co-located cellular designs. Integrated
filtering is not enough evidence to omit it here. Estimate transmitter coupling,
measure antenna isolation, and compare against receiver immunity; account for
filter insertion loss and antenna/cable loss in the sensitivity review.

## Sourcing and remaining work

DigiKey SKU **931-1236-ND** lists **2097** units on its retrieved US product page
(2026-10-12). The Norway page was unavailable to the retrieval tool, so Norway
shipping, current price and checkout stock are not claimed as confirmed.
This antenna is installed after PCBA, not a JLCPCB pick-and-place/CPL item.
No order was placed.

- [x] Find an exact passive cabled GNSS antenna with appropriate L1 coverage.
- [x] Retain manufacturer dimensions, clearance and source hash in CopperLib.
- [x] Review passive compatibility and integrated receiver matching/DC block.
- [ ] Verify enclosure and cable fit, supplied connector, battery/ground clearance.
- [ ] Close RF ESD and LTE isolation/SAW filtering decisions.
- [ ] Qualify the actual GNSS feed/support on the selected six-layer stackup.
- [ ] Adopt the candidate into a fresh source-bound review and manufacturing
  selection; do not retroactively relabel the old package.
- [ ] Measure installed match, acquisition/tracking performance and LTE/BLE
  desensitization on battery and during USB charging.

The recommendation does not complete GNSS RF approval or production release.
