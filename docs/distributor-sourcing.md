# Distributor sourcing (2026-11-02)

`assembly.lock` now records DigiKey, Mouser and Farnell offers as `alternates`
on each selection whose exact manufacturer part those distributors list.
Alternates never change what JLCPCB is given; they are for spares, quotes and
hand builds. [distributor-bom.csv](../procurement/distributor-bom.csv) is the
same data grouped by MPN (one row per part, quantity per board, all four
supplier codes), generated from the lock. Once J_CELL and J_GNSS are
reviewed, `make bom` writes the per-designator ordering sheet with one column
per distributor.

Coverage of the 44 distinct MPNs: JLCPCB 43, Farnell 31, Mouser 30, DigiKey 21;
seven are listed at all three. The two SMA jacks (Molex 73251-2200) are not
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

- **No DigiKey, Mouser or Farnell listing (3 MPNs):** the KENTO KT-0603R LED,
  the YXC X322532MOB4SI crystal and the SIM7670G-LNGV modem (LCSC/SIMCom only).
  The FH 0402 C0G capacitors and UNI-ROYAL 0402 resistors that had none are
  replaced in the lock by reviewed YAGEO and Murata selections (YAGEO RC/AC0402
  resistors, YAGEO CC0402/CC0603 and Murata GRM15/GJM15/GRM21 capacitors),
  which JLCPCB and at least one distributor stock.
- The TPS63020 output capacitors are Samsung **CL21A226MPCLRNC** (C307529) and
  the 10 µF inputs Murata **GRM21BR61H106KE43L** (C440198), replacing the
  CL21A226MAQNNNE (obsolete at DigiKey and Mouser) and CL21A106KAYNNNE
  (discontinued at DigiKey) of the first selection.
- **NRF52832-QFAA-R** is NRND at Nordic; Mouser lists only the -R7 reel.
- **FTSH-105-01-L-DV-007-K** (SWD headers) is sold in tubes, and STM32G0C1RET6
  in trays: no cut tape.
