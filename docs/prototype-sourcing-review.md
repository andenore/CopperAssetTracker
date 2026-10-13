# Prototype sourcing review — 12 October 2026

The new source has 95 fitted references and 51 distinct JLCPCB ordering codes.
Its assembly lock retains `reviewed=false` for all entries; the user's earlier
BOM approval is not blanket approval of changed packages or ratings.
An exact comparison with the approved root lock finds 81 unchanged identities
and 14 changed/new identities. Earlier approval of those 81 unchanged BOM
identities remains acknowledged; the composition tool's conservative flags do
not revoke it. Fresh native placement/process review is still needed, and the
14 differences must be reviewed explicitly. No flags were silently cleared.
`build/prototype-preorder-v2-20261012/assembly-review-native-draft/` contains
the shared CopperScript unapproved candidate BOM, matching native CPL and offline
identity diagnostics. All 95 fitted references match the native placement data;
both DNP RF tuning capacitors are excluded. Native position CSV SHA256:
`61a22ced930a6b464a14ed0a7147c98fe78e37f4aea752516b4068fb525dff19`.
BOM SHA256: `51987f991722a050f320b321f7cd1bca46603c1a0e69319191951830710f3e82`.
CPL SHA256: `99e35d82842c97201cd1bdfe8f00a0ce216247b3b071e641c646ad374fe37f53`.
These files bind the first failed native draft, not a completed/final route.
They are useful for footprint/pin-1 review, not manufacturing pairing; regenerate
and rebind them after acceptance of a final native candidate.
This is for human review only, not supplier upload or purchasing.

Changed/new references versus the canonical root selection are:

| References | Exact MPN / JLC code | Review focus |
| --- | --- | --- |
| CELL_MATCH/C_DC | 0402CG101J500NT / C1546 | C0G 100 pF, RF model/loss/power |
| CELL_MATCH/D_ESD | RCLAMP1561PQTCT / C20336388 | Exact SLP1006P2 land pattern; loading/return/system ESD |
| CELL_MATCH/R_LINK | RC0402FR-070RL / C106231 | 0 ohm RF link, loss/current/pulse ratings |
| D_GNSS_ESD | TPD1E01B04DPYR / C779389 | DPY, not DPL; NSMD adaptation needs process acceptance |
| PWR/R_TMR | 0402WGF6802TCE / C36871 | 68 kohm, timer programming not recharge guarantee |
| PWR/TEMP/R_ISOLATION | 0402WGF1003TCE / C25741 | 100 kohm TS isolation |
| PWR/TEMP/R_SHUNT | 0402WGF3902TCE / C25783 | 39 kohm divider |
| PWR/TEMP/R_TOP | 0603WAF4302T5E / C23172 | 43 kohm, actual 0603 footprint and tolerance |
| PWR/U_CHARGE | BQ24072TRGTR / C129319 | T-variant only; exact RGT land map and temperature/voltage limits |
| U_MODEM/C_100N | CL05B104KO5NNNC / C1525 | 100 nF local bypass; exact pad association |
| U_MODEM/C_10P | GRM1555C1H100JA01D / C76946 | 10 pF local bypass, C0G/RF behavior |
| U_MODEM/C_1U | CL10A105KB8NNNC / C15849 | 1 uF local bypass, bias/temperature |
| U_MODEM/C_33N | CL05B333KB5VPNC / C472437 | 33 nF local bypass, actual voltage/dielectric |
| U_MODEM/U | SIM7670G-LNGV / C45935408 | Hierarchy change; exact variant/process and accepted SIM7672X assumption |

Two physical tuning lands CELL_MATCH/C_HOST and CELL_MATCH/C_ANT are DNP and must
be absent from both fitted BOM and CPL. They remain physical copper/clearance
objects. External Taoglas antennas, cell, holder and sensor/harness are not SMT
assembly components. No quantity or stock reservation is implied.

## Public supplier evidence and its limits

The per-code record is
`revisions/prototype-preorder-v1/public-catalogue-review.json`, bound to the v3
assembly lock. Read-only public checks were attempted for all 51 fitted ordering
codes on 12 October 2026: 27 exact identities were returned, while 24 have
fetch/search or stale-stock evidence gaps. All 51 live order-specific quantities
remain unknown; none is reserved. Failed selected URLs are recorded rather than
silently interpreted as discontinued or zero stock. The record does not approve
the generated unreviewed assembly lock or waive exact-order review.

Exact public JLCPCB catalogue identity/type pages were read on this review date:
[TI DPY TVS](https://jlcpcb.com/partdetail/TexasInstruments-TPD1E01B04DPYR/C779389),
[Semtech TVS](https://jlcpcb.com/partdetail/SEMTECH-RCLAMP1561PQTCT/C20336388),
[T-variant charger](https://jlcpcb.com/partdetail/TexasInstruments-BQ24072TRGTR/C129319).
The two TVS pages identify SMT, Economic and Standard PCBA. Their returned text
does not establish usable quantity or reserved inventory. Public summary
capacitance fields do not supersede exact manufacturer rating conditions.

The Octopart/Nexar connector failed with its 2000-part account quota exceeded.
No component stock result was returned. Later public search located the exact
[C45935408 modem catalogue](https://jlcpcb.com/partdetail/48042558-LTE_Cat_1bis/C45935408):
it confirms Standard PCBA only and mandatory X-ray inspection, but its returned
page does not establish reserved inventory. A later returned view displayed
45 in stock and 43 available to order, but the search service labels that view
as crawled five months ago: those quantities are not a current confirmation.
That same exact-code page requires an assembly support fixture, in addition to
Standard PCBA and X-ray. This is an assembly-process requirement, not the
excluded mechanical-fit/test-access assessment. A second assembly-service
code C9900162595 is not silently substituted for the selected code.

The exact [RF link listing](https://jlcpcb.com/partdetail/RC0402FR-070RL/C106231)
has a three-month-old indexed zero-stock entry; a fresh direct fetch failed.
Treat that as a sourcing risk, not current stock confirmation or proof that all
zero-ohm links are unavailable. The [43 kohm resistor catalogue](https://jlcpcb.com/partdetail/23899-0603WAF4302T5E/C23172)
confirms the selected 0603 identity and process type; quantity text differed
between indexed and directly returned views and is not an order reservation.
No other fitted identities have newly confirmed order-specific PCBA inventory.
Additional exact catalogue checks confirm the 0402 100 nF C1525, 0603 1 uF
C15849 and 0402 C0G 10 pF C76946 selections and their SMT service types;
returned pages do not expose current usable quantities. Sources:
[100 nF](https://jlcpcb.com/partdetail/C1525),
[1 uF](https://jlcpcb.com/partdetail/C15849),
[10 pF](https://jlcpcb.com/partdetail/MurataElectronics-GRM1555C1H100JA01D/C76946).
Public searches also locate the exact
[100 kohm](https://jlcpcb.com/partdetail/C25741),
[39 kohm](https://jlcpcb.com/partdetail/26526-0402WGF3902TCE/C25783) and
[68 kohm](https://jlcpcb.com/partdetail/37849-0402WGF6802TCE/C36871)
resistor identities. The indexed 100 kohm quantity is two weeks old and is not
a reservation; the other returned views do not establish current inventory.
The direct selected 100 pF C1546 page failed to fetch, and exact-code searches
did not locate a JLCPCB PCBA page for the selected 33 nF C472437. This is an
evidence gap, not proof of unavailability. Its LCSC warehouse page is not PCBA
stock confirmation. Retain both gaps for account-specific review.
The [MAX-M10S exact catalogue](https://jlcpcb.com/partdetail/U_BLOXAG-MAX_M10S00B/C4153167),
returned on this review date with a one-day crawl age, identifies the 18-land
package, Economic/Standard service and MSL 4 handling; it does not expose a
current available quantity. Moisture handling/reflow acceptance must be part of
the exact assembly-process review, not inferred from an old warehouse count.
Confirm its hardware/firmware revision as well: the public MPN is unsuffixed
MAX-M10S-00B, while the current R08/ROM SPG 5.10 source review names -00B-01.
Do not silently infer exact revision applicability from a family catalogue title.
Distributor warehouse counts and loosely matched search results are not
assembly-stock evidence. No substitutions or supplier uploads were made.

JLCPCB's [parts service](https://jlcpcb.com/parts/) provides account/order-specific
BOM stock review. Completing that review would require authorization to upload
the BOM, a connected/logged-in account and the prototype quantity. None is
assumed or performed by this task. No part substitutions, preorders or purchases
have been made. Standard PCBA/modem support fixture and X-ray, GNSS MSL 4
handling, all special footprints, CPL pin-1 and
supplier-specific rotations still need exact-order preview/process confirmation.

## Five-unit review-only follow-up — 12 October 2026

The user subsequently authorized uploading the Gerbers, BOM and CPL to JLCPCB
for stock, DFM and assembly-preview review only, for five prototype units.
Payment, ordering and manufacturing release remain unauthorized. No supplier
upload was completed: the Computer Use service stopped because browser
URL-policy enforcement is unsupported for the current Windows browser. No live
JLCPCB stock, DFM or assembly-preview result is claimed.

A local, checksummed upload candidate is prepared at
`build/prototype-preorder-v3-20261012/supplier-preview-5-units-NOT-APPROVED/`.
Its three upload files are the Gerber ZIP, candidate BOM and native-position CPL;
their SHA256 values are recorded in that folder's `manifest.json`. The bundle
is explicitly not approved for ordering. The native board is route-complete, but
the exact CAM audit is not qualified. The current candidate assembly report has
95 fitted references, zero reviewed references and 14 changed/new identities
versus the earlier approved root BOM. Supplier preview could inform stock and
process review, but cannot approve those identities or resolve the outstanding
electrical/RF requirements.

## Remaining approval

Review exact manufacturer source/package/rating applicability for changed
selections; review final native CPL against footprint origins and pad 1;
resolve live PCBA stock for all 51 codes and the chosen quantity; obtain explicit
prototype risk/package approval and supplier process acceptance. Only then can
a strict reviewed BOM and approved upload package be described as ready.
