# Distributor sourcing (2026-11-02)

`assembly.lock` now records DigiKey, Mouser and Farnell offers as `alternates`
on each selection whose exact manufacturer part those distributors list.
Alternates never change what JLCPCB is given; they are for spares, quotes and
hand builds. [distributor-bom.csv](../procurement/distributor-bom.csv) is the
same data grouped by MPN (one row per part, quantity per board, all four
supplier codes), generated from the lock. Once J_CELL and J_GNSS are
reviewed, `make bom` writes the per-designator ordering sheet with one column
per distributor.

Coverage of the 43 distinct MPNs: JLCPCB 42, DigiKey 26, Farnell 20, Mouser 16;
nine are listed at all three. The two SMA jacks (Molex 73251-2200) are not
stocked by JLCPCB, so they are `consigned` with DigiKey as the primary offer.

## How the codes were checked

Codes were looked up for the exact MPN; none was derived from a distributor's
numbering pattern. DigiKey codes were read from DigiKey product or search
pages. Mouser and Farnell block automated page reads, so most of their codes
come from search-result text for that exact MPN and product URL, not from the
live page. Mouser's BQ24072RGTR and MAX-M10S-00B codes have no product URL.
An empty cell means no listing was confirmed, not that the distributor cannot
supply the part (several Mouser pages exist whose code could not be read).
Stock, price and packaging were not checked. Confirm each line in the
distributor's cart before ordering.

## Gaps and risks

- **No DigiKey, Mouser or Farnell listing (14 MPNs):** all FH 0402 C0G
  capacitors, all UNI-ROYAL 0402 resistors (Mouser lists a few as
  `303-…`, not confirmed here), the KENTO KT-0603R LED, the YXC X322532MOB4SI
  crystal and the SIM7670G-LNGV modem (LCSC/SIMCom only). A non-JLCPCB build
  needs equivalent substitutes (for example Yageo RC0402FR-07 resistors and
  Murata GRM15 C0G capacitors). Substitutes are new selections that need their
  own review, not alternates of these MPNs.
- **CL21A226MAQNNNE** (six TPS63020 output capacitors) is marked obsolete at
  DigiKey and Mouser; DigiKey suggests CL21A226MAYNNNE. JLCPCB C45783 is
  unaffected for now.
- **CL21A106KAYNNNE** is marked discontinued at DigiKey.
- **NRF52832-QFAA-R** is NRND at Nordic; Mouser lists only the -R7 reel.
- **FTSH-105-01-L-DV-007-K** (SWD headers) is sold in tubes, and STM32G0C1RET6
  in trays: no cut tape.
