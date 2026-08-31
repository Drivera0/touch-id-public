# TouchID v7 — RELEASE PACKAGE (2026-08-31)

**This folder is the single source for ordering and building. Everything in it
was verified the day it was copied here: preflight 0 blockers, verify_gerbers
0 failures, verify_handoff 0 failures.** If a file here ever disagrees with
one in `pcb-v3/`, the one in `pcb-v3/` is the live working copy — regenerate
this folder rather than editing it.

## What each file is

| file | what it is | where it goes |
|---|---|---|
| `pcb-v7-zero-opens.kicad_pcb` | THE board. 20.00 × 19.00 mm, 4-layer, 46 parts | reference copy — edit only the one in `pcb-v3/` |
| `pcb-v7-zero-opens.kicad_pro` | its project file, carries the REAL fab rules | keep beside the board; do not delete |
| `touchid-v7-gerbers.zip` | 11 gerber layers + PTH/NPTH drill + job file, corner origin | **JLCPCB upload, PCB order** |
| `assembly/touchid-v7-BOM.csv` | 19 lines, 29 parts, all with LCSC codes | **JLCPCB upload, assembly** |
| `assembly/touchid-v7-CPL.csv` | 29 placements, corner-based, matches the gerbers | **JLCPCB upload, assembly** |
| `assembly/touchid-v7-BOM-annotated.csv` | same BOM with sourcing notes | your reference, don't upload |
| `housing/touchid_housing_v5_diagonal_quoted.stl` | THE housing, "quoted" variant: riser 5.10, pocket Ø13.00, sized to LiPol's quoted Ø12×6.7 cell (+datasheet bands), module 13.46 mm | 3D print |
| `housing/touchid_assembly_v5_diagonal_quoted.step` | full assembly model (housing+board+cell+sensor) | reference / fit checks |
| `housing/touchid_housing_v5_diagonal_tall.stl` | FALLBACK housing (riser 6.50) — only if a delivered cell measures >7.0 mm | 3D print (fallback) |
| `housing/PRINTING.md` | orientation, material and slicer settings — read before slicing | your printer |
| `flash-jig/flash_station.stl` | **the one to print**: self-contained USB-C flashing station (68×68×19) — pocket + spring self-eject + rear tray holding the DAPLink and a USB-C buck module (set to 3.6 V!), two cable slots in the rear wall. Board's spacebar/module edge points at the cables (engraved arrow; dot = SWDIO end). Wiring guide in `pcb-v3/gen_flash_station.py` header | any FDM printer |
| `flash-jig/flash_jig.stl` | minimal jig (28×27×19, no electronics bay) — superseded by the station but kept | any FDM printer |
| `flash-jig/flash_jig.step` | same jig, editable CAD | if the print needs tweaks |
| `flash-jig/J3-flashing-hookup.png` | which J3 pad is which, bottom view | your bench |

## Order-form picks (NOT in any file — set them at checkout)

* Thickness **1.2 mm** (JLC defaults 4-layer to 1.6)
* Via option matching **0.40/0.20 mm**
* **Confirm Parts Placement = Yes** (U1–U4 are the rotatable parts)
* Depaneling service (the housing lip has 0.04 mm to spare — no break-off nubs)
* Re-check stock: **U1 / C5118826** (MDBT50Q) was 0 at last check
* Cell: LiPol LPM1254 80 mAh **with PCM + wires** — quoted 2026-08-31,
  MOQ 5 @ $20 + shipping; you order it, see `pcb-v3/CELL-DECIDED.md`

## Where things came from / how to regenerate

* Working directory: `../pcb-v3/` (tools, checkers, the live board)
* Gerbers: `install_kicad_cli.sh` then the plot flags it documents
* BOM/CPL: `python3 make_bom_cpl.py pcb-v7-zero-opens.kicad_pcb`
* Jig: `python3 gen_flash_jig.py`
* Full session record: `../pcb-v3/OPENS-CLOSED-V7.md`
* Superseded boards (v3–v6): `../pcb-v3/_archive-superseded/`
* The old `../v6-handoff/` folder holds the same gerber/assembly outputs under
  their original names; this folder is the curated copy.
