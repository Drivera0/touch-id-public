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
| Dimensions | 19.3 × 19.3 mm | |

Quoted on the web form 2026-08-28: **C$32.68**, or **C$25.76** in the JLCONE
desktop app — the same order is about C$7 cheaper there, so it is worth using.

**Filled in and left ready in JLCONE, 2026-08-28** (not ordered): 5 boards,
**US$18.61** + US$25.92 shipping, 3–4 day build. Uploading the zip made JLC's
own parser read **4 layers and 19.3 × 19.3 mm** straight off the gerbers, which
is the best independent confirmation the export is right — those two fields set
themselves. Only thickness and finish had to be chosen by hand.

Everything else was already correct at JLC's 4-layer defaults: 1 oz outer /
0.5 oz inner, min via 0.3 mm/(0.4/0.45), plugged vias, flying-probe fully
tested, order mark removed, and every exotic option (gold fingers, castellated
holes, edge plating, backdrill…) off.

## Everything also lives in a JLCONE project

**Projects ▸ My Projects ▸ "TouchID v3 - fingerprint keyboard module"**, so a
future order does not depend on finding these files again:

| tab | holds | note |
|---|---|---|
| **PCB** | `touchid-v3-jlcpcb.zip` + BOM + CPL as one entry | has an **Order Now** button |
| **3D** | housing `.stl` and full assembly `.step` | each has its own Order Now |
| **Others** | `touchid-v3-docs.zip` | README, verification report, checksums, annotated BOM, no-U1 BOM, sourcing notes |

The PCB entry carries the **full 20-line BOM** — the real design. If U1 is
still out of stock when you order, swap in `touchid-v3-BOM-no-U1.csv` from the
docs zip instead.

> The Others tab rejects `.md` and `.txt`, which is why the documentation is
> zipped. The project description field also caps at ~200 characters, so the
> detail lives here rather than there.

## IN THE CART, NOT ORDERED — 2026-08-28

Both line items are **saved in the JLCPCB cart, unticked, subtotal $0.00**.
Nothing was purchased. Project name in JLCONE: **`touchid-v3-jlcpcb`**.

| line | what | qty | build | price |
|---|---|---|---|---|
| `touchid-v3-jlcpcb_Y7` | PCB — green, 1.2 mm, ENIG | 5 | 3–4 d | **$24.13** |
| `touchid-v3-jlcpcb_Y7` | Standard PCBA, assemble top side | 5 | 3–4 d | **$91.25** |
| | | | **total** | **$115.38** |

**The fixed costs dominate at this quantity.** Of the $91.25 assembly charge,
only **$26.18 is components** — the rest is Setup $25.56, Feeders Loading
$29.07 (charged per unique part, and there are 19), Stencil $8.21, with SMT
Assembly itself just $1.29. So a bigger run costs very little more: the next
25 boards would add roughly the component cost alone. **Decide the quantity
before ordering, not after.** Confirm Parts Placement is $0.45 — keep it.

### U1 is assembled by nobody, and is deliberately left off this quote

JLC's own parts search shows **all 19 MDBT50Q variants at 0 stock and 0 idle
parts, with no Select button on any** — there is no substitute to pick. So the
quote uses **`assembly/touchid-v3-BOM-no-U1.csv`**, a 19-line file that is
byte-identical to the main BOM minus the U1 row. JLC confirms the intent
explicitly on upload: *"U1 designator don't exist in the BOM file"* → Continue.

**When the module returns**, re-upload the full `touchid-v3-BOM.csv` instead
and U1 comes back. Nothing else changes.

### C5 — fixed by changing the part, after two wrong theories

`C18164635` (CCTC) came back "No Part Selected" on **every** upload despite
1.1 M in stock. Two plausible causes were tested and both were wrong: it was
not the four extra metadata columns (a clean 4-column file failed identically)
and not the under-specified comment (`10uF 16V X5R 0603` failed too).

Diffing it field-by-field against `C20416425` — C7's part, same CCTC 0603
family, always matches — everything material is equivalent. The one categorical
difference is **`idleFlag`: null on the failing part, true on the working one.**

C5 is now **`C70225`** (FH 0603X106K160NT), same 10 µF 16 V X5R ±10% 0603,
479 k in stock, `idleFlag` true. **JLC auto-matched it first try, 19/19
confirmed.** Costs $0.88 more, which buys the removal of a manual step from
every future upload.

That is an observation, not a proven mechanism — `idleFlag` tracked the
behaviour and the swap is verified to work. Do not treat it as a general rule.

Assembly settings already chosen: Standard process, **Top side only** (all 46
footprints are front-side), qty 5, edge rails added by JLCPCB, and **Confirm
Parts Placement = Yes** — that last one is worth keeping, because it is the only
control that catches a U1–U4 rotation error before five boards are built wrong.
The 72-hour auto-confirm default was left on; there is a "do not confirm
automatically" checkbox if you would rather production waited indefinitely.

> **Standard PCBA panelises the board to 71.3 × 71.3 mm** (JLC requires ≥70 mm
> per side) and adds edge rails. So the boards arrive attached to a rail, and
> **how they are separated matters here**: the housing lip is 19.54 mm against a
> 19.50 mm worst-case board, so a break-off nub of even 0.1 mm would stop it
> fitting. Either take JLC's Depaneling Service or plan to file the edges flat.

### Two BOM faults JLCPCB found that none of my checks did

**U3 and U4 arrived on two separate lines.** They are the same TPS7A2033DQNR,
but the netlist describes them differently ("sensor rail" vs "switched
sensor-MCU rail") and `make_bom_cpl.py` grouped by that description. JLC gave
the quantity to one line and **zero** to the other. Fixed at source — a BOM line
is one *purchasable item*, so it now groups by part number: 21 lines → 20, and
U3,U4 is one line at qty 10.

`verify_handoff.py` passed both before and after, because it only checks that
BOM and CPL cover the same **designators** — which was true either way. One part
spread across two lines was outside everything I had written.

**C5 came back "No Part Selected"** despite `C18164635` being in the file with
1.1 M in stock. Its search box had been pre-filled from the comment as
`10uF0603 0603`, which matches nothing — JLC fell back to a text search instead
of using the part number in the row. Searching `C18164635` found it first hit.
**No file change was needed; the row was always correct.**

### Board outline tolerance: ±0.2 mm is deliberate, do not "improve" it

JLC quotes ±0.2 mm (Regular) on the outline. That was designed for: the board
is **19.30** so the worst case is **19.50**, and the housing lip is **19.54** —
0.04 mm of margin at the extreme. Paying for ±0.1 mm (Precision) buys nothing
the housing needs, and it is worth knowing that `touchid_module_v5.py` has no
housing-∩-PCB boolean check, so this fit rests on that arithmetic rather than
on an intersection test like the other five clearances.

### Defaults that turned out to be right — confirm, don't change

Two 4-layer defaults happen to match what was verified, which is luck worth
checking rather than assuming next time:

* **Outer copper 1 oz, inner 0.5 oz.** The board's own stackup declares
  0.035 mm outer and 0.0152 mm inner, which *is* 1 oz / 0.5 oz. So preflight
  check 10's IR-drop numbers hold as quoted.
* **Min via hole size 0.3 mm / (0.4/0.45 mm).** Every via on this board is
  0.3 mm drill in a 0.6 mm pad, so this is the standard rung with no upcharge —
  the finer rungs would cost more and buy nothing.

**Deburring / edge rounding defaults to Yes** (C$0.14) and only appears once
you pick 4 layers. Harmless, arguably wanted on a board that slides into a
keyboard slot, but it is a real charge you did not choose — set it to No if you
would rather not have it.

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
* **The HLK-ZW0922 sensor** — solders to J2 by hand. Same file.
  *(The ZW0905 is discontinued; the ZW0922 is a drop-in — same flange, barrel,
  step and pin order. See `../pcb-v3/SENSOR-ZW0922.md`.)*
* **Gerbers** — next step.
