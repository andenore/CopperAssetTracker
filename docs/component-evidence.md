# Component evidence and credits

Exact canonical per-reference selections are in assembly.lock;
grouped selections are in procurement/parts.json. Library inclusion is not a
stock reservation or a complete design-suitability check.

Reusable component models, custom footprints and their converter now belong to
CopperLib. Package ownership and evidence are indexed in
[library package ownership](../../CopperLib/docs/package-layout.md).
This project owns application bindings and selected offers. The 91-part review
uses its own candidate selections; see [current status](validation.md).

## Cat-1 bis modem

[SIM7670G-LNGV C45935408](https://jlcpcb.com/partdetail/48042558-LTE_Cat_1bis/C45935408)
is the SIMCom listing (Standard PCBA, X-ray required).
Select C45935408, not the distinct consignment C9900162595.
Recheck current stock and assembly eligibility before ordering.

The [SIMCom supplier-linked specification](https://datasheet.lcsc.com/datasheet/pdf/ee03db1eecfc7b8f7e60fb0421704843.pdf?productCode=C45935408)
identifies SIM7670G as Cat-1 bis. SHA256:
12d00aae02bc600ac678f8d478d86e099f3339f9a9a7e2837773e5d9489acb11.
Used power/UART/STATUS/SIM/USB/RF pins were cross-checked against the exact
C45935408 symbol and SIMCom-authored
[SIM7672X Hardware Design V1.01](https://files.waveshare.com/wiki/SIM7670G-LTE-Cat-1-GNSS-HAT/SIM7672X_Series_Hardware_Design_V1.01.pdf),
Tables 4/5. This is not complete variant equivalence. Unused multifunction
pins are unconnected; exact-model current manufacturer-guide signoff remains open.

The full 124-land footprint comes from the exact
[EasyEDA product API](https://easyeda.com/api/products/C45935408/components?version=6.5.44),
package UUID 2be3f51bf5e54bc28cbf6586caa12048, title
LCC-124_L24.0-W24.0-P1.0-TL. Original JSON SHA256:
bde713d456f592968facd909ba03b4e3736ff7edb684c97ac55bf3d7429e3df6.
CopperLib's `packages/parts/simcom/sim7670g-lngv/import_footprint.py` validates
identity and preserves all lands.
No downloaded executable code is run.

## Footprints and circuits

TPS63020 DSJ0014 uses [TI's land drawings](https://www.ti.com/lit/ds/symlink/tps63020.pdf);
PDF SHA256 d117773bb7370fd79377bc70ce987eec3469ea5979547a09df52fca5f95b2e69.
Signal pins 1-14 remain separate; central and comb PGND lands are pad 15.
Paste windows are separate from common copper. Final stencil/thermal review required.

The [Bourns SRP4020TA sheet](https://www.bourns.com/docs/Product-Datasheets/SRP4020TA.pdf)
has SHA256 601b2bd60f01531d3dd98df00eab15635fa971ebc03cf7ae4ccb5679faf03485.
Inductor lands use its 5.2 mm outer span, 2.2 mm gap and 2.4 mm width.

[JST XH catalogue](https://www.jst-mfg.com/product/pdf/eng/eXH.pdf), page 6,
SHA256 9426b136902f11900825077535e5c65032b7fbc31ffb59c5e9e1f463bb20fb90:
SMT connector bodies checked visually. Lands are from exact EasyEDA
C161860/C161861 packages, UUIDs 339b3d311e1c4b379b2d8061c2d7ac48 and
2e6c2e3d58c5466fb09fd1d264c24934. Both mounting tabs connect to PCB ground.
The four-pin pattern has larger tab lands; confirm manufacturer land patterns
before release rather than substituting a through-hole XH footprint.

UART/STATUS models use [TI SN74AXC2T245 pin/truth tables](https://www.ti.com/lit/ds/symlink/sn74axc2t245.pdf).
Both represent the same C1882550 device, with explicitly different directions.
YXC 32 MHz crystal is C9009, not CopperLib's 25 MHz C9006.
CL=12pF and accuracy are catalogue options; confirm exact manufacturer
options and tune the initial 18pF load capacitors on the board.

## Assembly catalogue

The two without API CAD data were verified on JLCPCB part pages:
[USB4135-GF-A C5438410](https://jlcpcb.com/partdetail/6314253-USB4135_GFA/C5438410),
[0603USB-601MLC C3211396](https://jlcpcb.com/partdetail/Coilcraft-0603USB601MLC/C3211396).
Recheck live stock, assembly mode, minimum quantity, attrition and rotations
for every line at order time. All 83 retained selections are now approved under
the user's instruction to assume BOM approval; see `bom-approval.md`. This does
not approve CPL or confirm current availability. Changed 91-part selections
require separate review.

## Credits

Board source and RF macro derive from CopperScript full_vertical and CopperLib's
Nordic/Johanson reference. Build structure follows CopperLedRing.
Dependencies remain separately commit-pinned; KiCad footprints retain upstream
licence/provenance in the managed dependency cache.

Modem and JST land data: **JLCEDA / EasyEDA Official Library**,
https://lceda.cn/ and https://easyeda.com/. Conversion adds KiCad packaging,
body and courtyard metadata; it does not constitute manufacturer qualification.
Retain these credits when redistributing converted land data.
