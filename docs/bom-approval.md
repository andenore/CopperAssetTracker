# BOM approval scope

The user instructed: "Choose standard JLCPCB 6 layer stackup and continue. Assume
bom is approved". This is a user-directed assumption, not an independent audit.
The canonical root `assembly.lock` contains 83 approved exact selections in
43 identities. The generic check enforces identities, coverage and current
electrical provenance. The lock is authoritative for its current digest.

The user also accepted SIM7672X Hardware Design V1.01 as this board's design basis
for battery-fed USB detection. This is a scoped applicability assumption;
manufacturer equivalence and electrical performance remain unqualified.

The combined 91-component modem-power/battery revision has changed/new selections
that are candidates and require separate approval. Do not inherit approval from
the root board. BOM approval does not cover CPL centroids/rotations/polarity,
supplier preview, live stock, RF/power/battery performance, CAM/DFM or an order.
See [latest status](validation.md) and [release requirements](production-plan.md).
