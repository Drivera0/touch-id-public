---
title: TouchID v3 — handoff
type: project
---

# TouchID v3 — handoff

Verified 2026-08-28. **`touchid-v3-jlcpcb.zip` is the file you upload.**

Everything here is a **copy**. The originals stay in `cad/pcb-v3/` and
`cad/exports/` where the build scripts expect them. `reports/SHA256SUMS.txt`
proves these copies are the files that were graded.

```
touchid-v3-jlcpcb.zip   <-- UPLOAD THIS. 11 gerbers + 2 drill files + job file
gerbers/    the same files loose, for inspection
board/      pcb-v3-handoff.kicad_pcb   the board
            pcb-v3-handoff.kicad_pro   THE RULES — must travel with the board
assembly/   touchid-v3-BOM.csv         21 lines, every one sourced
            touchid-v3-CPL.csv         29 placements
housing/    touchid_housing_v5_diagonal.step / .stl    the part you print
            touchid_assembly_v5_diagonal.step          housing + PCB + U1 + cell + sensor
            touchid_pcb_v5_diagonal.step               board solid, for fit checks
reports/    VERIFICATION.txt           full output of all five checkers
            plot-log.txt               KiCad's own plot log
            SHA256SUMS.txt
```

> **The `.kicad_pro` is not optional.** A board shipped without its sibling
> project file makes KiCad fall back on stale defaults — that alone once
> invented 39 phantom clearance violations on a board whose DRC was clean.

## What was checked, and what each check is worth

| checker | result |
|---|---|
| `sexp_check.py` | parses, 628 top-level children, 46 footprints / 134 pads / 458 segments / 65 vias |
| `preflight.py` | **21 checks, 0 blockers**, 2 warnings |
| `verify_handoff.py` | **13 checks, 0 failures** — BOM/CPL re-derived from the board by different code |
| `verify_sourcing.py` | **25/25 lands** match the package actually bought |
| `verify_gerbers.py` | **12 checks, 0 failures** — plotted output vs the board |
| `touchid_module_v5.py` | **8/8 boolean checks = 0.0000 mm³**, housing zmin ≥ 0 |

## What the gerber check actually proves

Not that the files exist — that they are *this* board:

* **67 drill hits, 67 board holes**, and the diameters agree exactly:
  `{0.30: 65, 1.30: 2}` in the drill files, `{0.30: 65, 1.30: 2}` on the board.
* **Outline 19.300 × 19.300 mm**, read back out of `Edge_Cuts.gbr`.
* **No layer silently empty.** This is the failure that produces a board with a
  missing plane and no error anywhere: F.Cu 3631 draws, In1.Cu 158, In2.Cu 2462,
  B.Cu 3298. In1.Cu is low because it is the only copper layer that is *not* a
  ground plane — signals only.
* All 11 layers metric, 4.6 format, positive image, unmirrored.

## Two things KiCad flagged, and what they were

**"Board stackup settings not up to date"** on the first plot. Our stackup was
written by script and listed only copper and dielectric; KiCad expects the mask,
paste and silk entries too. Accepting KiCad's completed stackup added them and
the second plot ran with **0 errors, 0 warnings**. The dielectrics were not
touched — copper + dielectric is still exactly **1.2000 mm**.

That is why the job file says **1.22 mm**: KiCad reports the *finished* part,
1.20 laminate + 0.02 of solder mask. **You still order 1.2 mm** — that is the
laminate, and 0.02 mm is far inside the fab's own ±0.13 mm tolerance. `preflight`
check 19 now separates the two instead of summing everything, which is what made
it briefly report a blocker that was pure bookkeeping.

**"Zone fills are out-of-date"** before the first plot. Expected: the pours were
built by `route_planes.py` and `gnd_taps.py`, so KiCad has no fill hash of its
own and will always say this. Refilled rather than plotting copper nothing had
graded — then re-ran everything. Still 458 segments, 65 vias, 3 filled zones,
0 unrouted.

`verify_handoff.py` exists because `make_bom_cpl.py` grading its own output
proves nothing. It re-derives the origin transform as a translation of the
board's measured lower-left **corner**, deliberately not as the `+9.65 / 9.65−`
form the generator uses, so one sign error cannot reproduce itself in both.
29 placements, 0 coordinate mismatches, corners map exactly to (0,0) and
(19.30, 19.30).

Both failures it reported on the first run were **its own bugs**, which is now
the normal outcome here: it filtered blank references out of the expected set
but not the observed one, and then it keyed a dict by reference — and since
*both* mounting holes carry a blank reference, the second silently overwrote
the first and it reported one hole where there are two. The board was right
both times.

## The two warnings, neither of which is a defect

**U1 has no JLC assembly stock.** Every MDBT50Q variant in JLCPCB's library
reads 0 — all 19. Not delisted, backordered (~11 days, backlog −75). You have
decided to wait. Re-check at order time; nothing in this folder changes.

**J4/J11 pogo geometry is unverified.** It is fixed by the keyboard, so it is a
*measurement* you take, not a datasheet anyone can send. `POGO-PAD-DATASHEET.html`
is the bench reference for it, and it flags a 0.02 mm Y-datum mismatch between
the J4 and J11 rows.

## Three things that must be set on the order form

These are invisible to every file here — they are dropdowns on JLCPCB's page,
and the defaults are wrong for this board.

| setting | value | why |
|---|---|---|
| **Board thickness** | **1.20 mm** | the housing is built around it; JLC defaults 4-layer to **1.60** |
| Surface finish | **ENIG** | matches the stackup the board was checked against |
| Layers | 4 | |

## Rotation risk is smaller than it looks

**Only U1, U2, U3 and U4 can be rotated wrong.** The other 25 placements are
two-pad parts where 180° is physically identical. All four are at 0° — check
them against JLC's own part preview at order time, which is the only thing that
can confirm a package's expected orientation.

## To re-verify from scratch

```
cd cad/pcb-v3
python sexp_check.py     pcb-v3-handoff.kicad_pcb    # always first
python preflight.py      pcb-v3-handoff.kicad_pcb    # the order gate
python verify_handoff.py                             # BOM/CPL, independent
python verify_sourcing.py                            # package vs land
cd ../scripts && python touchid_module_v5.py         # housing booleans
```

Never eyeball the individual checkers in place of `preflight.py` — it is the
single go/no-go, and the checks it wraps have each been wrong on their own.

## Not in this folder, on purpose

* **BT1's cell** — a hand-wired protected assembly, not a placed part. See
  `../pcb-v3/BUY-YOURSELF.md`.
* **The ZW0905 sensor** — solders to J2 by hand. Same file.
* **Gerbers** — next step.
