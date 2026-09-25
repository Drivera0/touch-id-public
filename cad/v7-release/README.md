# TouchID v7 — RELEASE PACKAGE (2026-08-31)

**This folder is the single source for ordering and building. Everything in it
was verified the day it was copied here: preflight 0 blockers, verify_gerbers
0 failures, verify_handoff 0 failures.** If a file here ever disagrees with
one in `pcb-v3/`, the one in `pcb-v3/` is the live working copy — regenerate
this folder rather than editing it.


> **Flash jig: superseded.** The printed `flash-jig/` parts failed (the pogo-pin
> holes didn't print through, and the lever doesn't fit). Use `../carrier-v1/`
> instead: that carrier PCB and flash frame are built.

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
| `flash-jig/flash_jig.stl` + `_lever.stl` + `_plunger.stl` | **the flashing jig, v2** (32×31×20 + 2 small parts): drop board on posts, press to flash, push the front button to eject. Wires exit through arches underneath to the DAPLink + 3.6 V supply on the desk. Engraved arrow = board's spacebar/module edge points AWAY from the button; dot = SWDIO end. Wiring in `pcb-v3/gen_flash_jig.py` header | any FDM printer |
| `flash-jig/flash_jig.step` | jig, editable CAD | if the print needs tweaks |
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

## CART STAGED 2026-09-01 (JLCONE desktop app) — NOT PAID

Four items sit in the JLCPCB cart, fully configured, awaiting the USER's payment:
1. PCB ×5 — 1.2 mm, 4-layer, 0.2 mm via option, edge rounding, remove mark — C$61.29
2. Standard PCBA ×5, top side, Confirm Parts Placement=Yes (auto-confirm OFF),
   depaneling=Yes, 23/24 BOM lines placed — C$129.01
3+4. JLC3DP housings: quoted ×2 + tall ×1, MJF PA12-HP nylon, dyed black — C$4.33
Total ≈ C$194.63 + shipping (~C$36); coupons (C$27.75 + C$20.81) apply at checkout.

**U1 (MDBT50Q, C5118826) is still ZERO STOCK — marked "Do not place".**
Boards will arrive with every part EXCEPT the radio module. Before paying,
decide: (a) wait for restock and re-add U1 to the order, or (b) pay now and
hand-solder a module bought from DigiKey/Mouser (Raytac castellations are
hand-solderable). The 0201-vs-0402 BOM text mismatches JLC flagged were
verified against the board (pads ARE 0201) and confirmed as-matched.

## 3DP ORDER UPDATE 2026-09-01 (evening)

User PAID the 3D-print order (W2026090116450154, C$17.09): 3 housings + jig +
lever + plunger, all MJF PA12-HP black. JLC flagged thin walls on both
housings; the "0.13 mm" was the TIER-JUNCTION CONTACT (user diagnosed it) —
v6.4 thickened walls to 1.0 where possible, v6.5 added junction ledges
(0.135 -> 0.85 mm bearing). Both files replaced via JLCONE; status now
"Reviewing". Verifier: cad/scripts/wall_check.py (thin walls + junction
contact). PCB+PCBA remain in cart UNPAID awaiting U1 pre-order
(C5118826: 0 stock, pre-orderable, ~11-day lead, C$25.26/pc).
