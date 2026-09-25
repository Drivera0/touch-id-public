# ORDER.md — what to upload to JLCPCB, and in what order

Current as of Addendum Q. Every figure here comes from a script that reads the
built files, not from this document being kept up to date by hand. Re-run the
three commands in "Proof" below and they will print these same numbers.

---

## Cleared to order

Every pin length is now measured (2026-09-18): barrel **13.00**, relaxed
**17.00**, compressed **14.50**. The stroke falls out of the last two at
**2.50 mm** — that figure had no source before and it is what proves the DUT
can never reach the carrier's copper.

```
seat bar top     9.30 mm
dowels cut to   19.5 mm    (CHANGED from 19.0 -- cut them 0.5 longer)
tip stands      4.50 mm proud, 2.50 mm of travel
                -> the board stops 2.00 mm above the carrier, always
frame           58.00 x 69.00 x 22.00, 36.9 cm3
verify_frame.py 0 blockers -- every published JLC3DP rule checked
```

### Both orders are clear

The barrel measured **Ø1.00** against the carrier's **Ø1.05** hole — 0.025 mm
per side. It fits, the hole stays as drawn, and the PCB needs no change.

Worst-case tip-to-pad error, computed by `verify_frame.py` rather than asserted:

```
0.050  carrier hole position (JLCPCB)
0.025  barrel slop in the hole
0.141  barrel cocked over 4.50 mm of overhang
0.088  DUT on the dowels
0.050  DUT pad position
-----
0.354  everything at its limit, same direction  ->  59% of the 0.600 mm
       a O1.20 pad allows.  0.246 mm spare.
```

The largest term is the pin cocking in its hole. Gravity hangs each pin plumb
on its own, so soldering them without nudging keeps it near zero — worth
knowing, not worth designing around.

**Also check U1 stock before ordering the PCB.** `C9900176459` (XIAO RP2040) is
an Extended part. The main board order has been paused since 2026-09-01 because
its U1 went to zero — do not repeat that.

---

## Order 1 — the carrier PCB (JLCPCB)

| what | value |
|---|---|
| upload | `carrier-v1-gerbers.zip` |
| size | 47 x 58 mm, 2 layer |
| **thickness** | **1.6 mm** — not 1.2. This is not pcb-v7 |
| surface finish | HASL is fine; the pogo pads are soldered, not contacted |
| quantity | 5 (the minimum) |

### Assembly (optional but recommended)

| what | value |
|---|---|
| BOM | `carrier-v1-BOM.csv` |
| CPL / pick-and-place | `carrier-v1-CPL.csv` |
| parts placed | 4 — U1 and R1/R2/R3 |
| U1 | `C9900176459` XIAO RP2040 (Extended) |
| R1-R3 | `C17408` 0805 100R 1% (Basic) |

J1, J2, the five pogo pins and the two dowels are deliberately **not** in the
CPL. Seven through-hole joints are not worth an assembly setup fee, and JLC
cannot place the pogo pins at all — the 2.00 mm pitch is below every
machine-placeable contact that exists.

---

## Order 2 — the printed frame (JLC3DP)

| what | value |
|---|---|
| upload | `flash_frame.stl` |
| size | 58.00 x 69.00 x 22.00 mm |
| volume | 36.9 cm3 |
| **material** | **MJF Nylon PA12** preferred — see below |
| quantity | 1 |

### Why PA12 rather than PLA this time

The older note in `README.md` said FDM PLA was enough. That was written before
the seat bar existed, and the bar changes the argument: it is now a
**height-setting surface that a hot pin tail rests on**. You solder each pin at
the carrier, 14.5 mm up a thin brass tube whose other end is sitting on the bar.
PLA softens around 60 C. PA12 does not go anywhere near that.

How much heat actually reaches the tail has **not been measured** — this is
reasoning, not a test result. If you would rather save the money, PETG or ABS
are the FDM compromise; PLA is the one to avoid.

### DFM, against JLC3DP's own published limits

Their guideline (read 2026-09-18) gives, for both MJF nylon and FDM plastic:

| their rule | this part |
|---|---|
| tolerance +-0.3 mm within 100 mm | budgeted — the recess has 0.50 mm of worst-case slack |
| min wall 1.5-2.0 mm at this size | **nothing on the part is under 2.0 mm** |
| hole depth <= 3 x diameter | O2.4 x 6.7 mm = **2.8:1** |
| escape holes >= 2.5 mm | not applicable — open bottom, no enclosed voids |

Those four are not the whole list. `verify_frame.py` now checks **every**
numbered rule on that page — build size, wall thickness, embossed/engraved
detail, hole depth, small columns, static-assembly clearance, escape holes,
tolerance — and it measures the minimum wall rather than asserting it, by
voxelising the STL and running a Euclidean distance transform. One command
answers the whole checklist:

```
python3 verify_frame.py     ->  FRAME: 0 blockers
                                every published JLC3DP rule checked -- clear to order
```

**It will not print that until you measure a pin.** `PIN_L` being a datasheet
figure is a BLOCKER in that script, not a warning, because the seat bar's whole
job is to set the contact height to a known number.

---

## Do NOT order

* `pin_setter.stl` — **superseded.** The seat bar inside the frame does its job.
* anything from `cad/v7-release/flash-jig/` — that is the jig that failed.

---

## What you supply yourself

| # | item | qty | note |
|---|---|---|---|
| 3 | P75-E2 pogo pin, 16.5 mm | 5 (+ spares) | measure one first |
| 6 | JST-XH 2-pin header + crimped lead | 1 | J1, power in. **Left pin is +** |
| 7 | 4.0 mm banana plugs | 2 | the DP100 end of that lead |
| 8 | 1x5 2.54 mm male header | 1 | J2, SWD escape — only if you want it |
| 10 | M3 x 8 self-tapping screw | 4 | into the printed bosses |
| 11 | 18 AWG solid copper wire, cut to **19.5 mm** | 2 | DW1/DW2 dowels |

The dowel length is printed by `gen_frame.py` and changes if `PIN_L` changes.
Cut them after you have re-run it.

---

## Assembly order

1. Screw the carrier into the frame's recess, 4 x M3. **The triangle engraved
   on the outer wall marks the +Y / spacebar edge** — the four screw holes are
   symmetric, so the carrier will bolt down backwards just as happily, and the
   opening underneath is not symmetric. Backwards puts every pin over solid
   deck instead of over the bar.
2. Drop the five pogo pins in from the top. The O1.02 barrel passes the O1.05
   hole and the tail lands on the bar. All five end up level, with the barrel
   standing **0.5 mm** proud of the board and the contact tip **4.54 mm**.
3. Drop the two dowels in. Same bar, same principle.
4. Solder all seven at the carrier's top face. **Solder the GOLD barrel only.**
   If you see grey/silver metal at the board's surface instead of gold, stop —
   the pin is sitting too low and solder there will kill the spring.
   Sanity check before you solder: all five tips level, ~4.5 mm proud.
5. Solder the XIAO RP2040 if you did not have JLC place it.
6. Meter TP1 (V+) and TP2 (GND) with the supply on, **before** any board goes in.

Once assembled: thread the DUT onto both dowels, let it drop 2.46 mm onto the
five tips, and press to about 60% of travel — roughly 300 g. The board sits
3.04 mm above the carrier. Press harder and the plungers bottom out at 2.04 mm
and stop; there is no way to press it onto the carrier's copper.

---

## Proof

```
python3 check_carrier.py                       ->  PREFLIGHT: 0 blockers
python3 verify_frame.py                        ->  FRAME: 0 blockers
python3 verify_fab.py                          ->  VERIFY: 0 failures
kicad-cli pcb drc carrier-v1.kicad_pcb         ->  0 errors, 0 unconnected
```

The 19 `lib_footprint_issues` KiCad reports are expected: footprints are
generated inline rather than pulled from a library, so there is no library
called `carrier` for it to find.

Sources for the JLC3DP figures:
<https://jlc3dp.com/help/article/3d-printing-design-guideline>
