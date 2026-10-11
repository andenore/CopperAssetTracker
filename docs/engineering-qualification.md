# Engineering assessment workflow

Current routing state and exact artifact references are in [validation](validation.md).
Select the board revision first: the root 83-part build and modem-power/battery
91-part review have different sources, selections and tool inputs. A plan or
report for one must not qualify the other.

Use shared CopperScript commands and library-owned contracts. The project owns
bindings, operating scenarios, sourcing and measurements. Generate a fresh
fabrication review package from the selected source, then assess that package's
exact exported native PCB with a matching engineering plan:

```console
copper audit-cam <package-directory> --kicad-python <interpreter> --report <new-cam.json>
copper assess-engineering <package-board.kicad_pcb> --plan <revision-plan.json> --kicad-python <interpreter> --report <new-engineering.json>
copper qualification-gate <package-directory> --plan <revision-plan.json> --cam-report <new-cam.json> --engineering-report <new-engineering.json> --report <new-gate.json>
```

Install `copperscript[qualification]`, or sync the pinned qualification extra.
Choose new report paths outside the package. Missing facts/tools/evidence produce
incomplete results; generated files do not imply passing qualification.

Make targets use `QUALIFICATION_DIR`, `QUALIFICATION_PCB`, `QUALIFICATION_RUN` and
`KICAD_PYTHON`. Run `cam-audit` and `engineering-audit` separately to collect both
reports, then `qualification`. Provision a pinned second parser/profile before
adding reviewed `CAM_AUDIT_ARGS`. Keep exported artifacts immutable.

Actual filled-copper/reference and USB path screens are geometric checks, not
impedance, delay or current-capacity proof. The BLE reference's deliberate copper
exclusions need source-specific treatment. Neither native DRC nor an auxiliary
screen substitutes for whole-channel USB, RF, power, CAM or bench evidence.

All reports bind artifact, algorithm, plan, source, library and external evidence
identities. Documentation/plan/input changes can invalidate earlier evidence.
Complete [production acceptance](production-plan.md) and [prototype review](prototype-plan.md)
before proposing a package decision; no command authorizes a supplier order.
