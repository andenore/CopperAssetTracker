# Prototype fabrication instructions

Status: engineering review candidate, not an approved order or production release.
These instructions accompany only a source-matched, checksummed package with a
successful native fill/DRC report. Do not combine historical exports with a new
source revision. Mechanical fit and test-access work are excluded by the user.

## Construction and impedance

Request JLCPCB JLC06161H-3313, NanYa NP-155F, nominal 1600 um, six copper
layers, outer 1 oz and inner 1/2 oz. No `No requirement` material selection,
unreviewed suffix change, or laminate substitution. Layer order is F.Cu,
In1.Cu, In2.Cu, In3.Cu, In4.Cu, B.Cu. The exact published construction and
calculator-model differences are in [stackup selection](stackup-selection.md).

The cellular and GNSS source intent uses 142 um wide surface RF traces with
201 um minimum coplanar ground clearance over In1.Cu GND, without signal vias.
Request 50 ohm controlled impedance, an authored prototype tolerance of
10 percent, and coupon measurement. The minimum clearance is not a guarantee
that every routed gap is 201 um; inspect actual artwork and launches. Supplier
acceptance and full-channel modelling remain open. Do not let a fabrication
width adjustment silently alter pad launches or matching-network branches.

Published construction spacings, in order, are 99400, 550000, 108800, 550000
and 99400 nm. Construction copper is 35000 nm on the outer layers and 15200 nm
on each inner layer. Do not stretch the construction to force a nominal total
or substitute the impedance calculator's 40640 nm exterior copper for it.

## Files and processes

Use the generated manifest and checksum inventory to identify the exact native
board, six copper Gerbers, mask/paste/silkscreen/outline layers, plated and
nonplated drill files, and IPC-356 data. Drill origin and artwork origin must
agree. Do not infer drill plating from a filename when the manifest/process
evidence says otherwise. Retain the actual via-process sidecars and review
pad intersections, annular rings, finished holes and required tenting/filling
against supplier capability before ordering. Nominal dimensions are not proof
of guaranteed barrel plating or current capacity.

The modem and fine-pitch protection packages require assembly-process review.
The selected C45935408 modem catalogue calls for Standard PCBA, a support
fixture and X-ray inspection. The selected C4153167 GNSS module is MSL 4;
confirm moisture handling and reflow process with the assembler. These supplier
process requirements are separate from the excluded mechanical-fit/test-access
work and are not waived by that exclusion.
Use exact package identities and the generated native pad geometry, not a
generic module footprint or an unreviewed manufacturer variant. No filled or
capped via-in-pad requirement is presumed from an unrelated historical board.

## Assembly and approval boundary

Only a BOM and CPL generated from this exact source and native board may be
paired. Hierarchical source references are normalized by CopperScript to the
native PCB names. Exclude the two DNP RF tuning capacitors from fitted BOM/CPL;
retain their physical copper and RF branches in geometry review. Preserve
native rotations for review rather than guessing supplier rotation offsets.

Files named `NOT-APPROVED` are for human review, not assembly ordering. Current
stock/reservation, placement-preview polarity/rotations, package processes,
prototype RF/electrical risk acceptance, and explicit approval of the exact
checksummed package are separate gates. Supplier uploads, purchases and orders
are not authorized by file preparation.

Independent CAM parser checks must identify the tools, versions and exact files
checked. Parsing and image inspection do not establish independent copper
connectivity, impedance, ampacity or production qualification. Post-delivery
RF/USB/power and charging measurements are not claimed as completed.
