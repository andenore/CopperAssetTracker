# BOM approval boundary — 2026-10-10

User instruction: "Choose standard JLCPCB 6 layer stackup and continue. Assume
bom is approved". This records a user-directed approval assumption, not a newly
performed independent component audit.

All 83 exact selections (43 grouped identities) in `assembly.lock` are marked
`reviewed=true`. References, manufacturer/MPN, supplier codes, footprints and
electrical design are unchanged. The library inventory adds only the stackup
profile; its provenance digest is refreshed to
`59c7b218e3e86450609089de1c448d3a18c7e645f57cb61824ac8a3864918e35`.
The generic assembly check still enforces
coverage, exact identities and the current electrical digest; no gate is bypassed.

This approval does not cover CPL rotations/centroids/polarity, supplier preview,
live stock, RF/power/battery performance, CAM/DFM, or an order. Placement review
and production release remain pending. Earlier assembly archives retain their
historical unreviewed flags. New candidate exports report BOM approval separately.

## Battery USB connectivity change

On 2026-10-10, the user accepted SIM7672X hardware-guide applicability. The only
electrical endpoint change is U_MODEM.USB_VBUS moving from V5 to switched V3V8.
No component identity, value, footprint, supplier code, placement count or reviewed
flag changes. All 83 exact selections remain approved under the existing BOM
assumption. Assembly source provenance is refreshed to
`b23def3974355e8bddee3981dca2b742279a0f4e69b7dbb81cf51afe29034eb4`.
This is not approval of new copper, USB performance, CPL or fabrication release.

## Showcase publication preparation

Two pre-existing TPS62130A macro assets in CopperLib had Windows CRLF checkout
bytes instead of their deterministic generated LF bytes. Their line endings
were normalized and package asset attributes now enforce LF. This changes the
library content inventory, not the tracker circuit or any selected component.
The assembly provenance digest is rebound to
`89b688beeb44aeb245a6647b07f5daac32ca8be8aa85f828c5ab0263a24fc36f`;
all 83 exact selections and existing reviewed flags are retained.
README illustrations are descriptive snapshots, not new production approval.

The published build now pins CopperLib `f54a03b36e8a785eb512626b3f5110a7f321e37c`
and CopperScript `e5fefc5a292b41462cee14243f647131f4af0c61`. The development
replacement and editable compiler dependency are removed. Canonical remote Git
inventories rebind the assembly digest to
`9c966dc4dbaa117f3d212b34127aed090f34014ad7839d0b08bc47d03be3491d`,
again preserving every selected component and reviewed flag. Qualification
reports bound to the previous locks/plan are historical and must be regenerated;
the unchanged illustrated native geometry is independently source-guarded.

## Plain numeric notation

CopperScript `209e4998223283923c3f1f0fb52f6fb97791cf46` emits ordinary
fixed-point numbers with declared units instead of scientific notation. The
tracker's before/after electrical IR was compared after exact decimal parsing:
values, units, connectivity, library provenance and all 83 selection identities
are unchanged. Only serialized numeric spelling changes. The assembly digest
is rebound to `f923a4effa54ebb7829aa85a397e0f302de97b3530dea3c0db0367ebe65a1ecc`,
preserving every existing selection and reviewed flag. This display change is
not new production approval; historical qualification bindings stay historical.
