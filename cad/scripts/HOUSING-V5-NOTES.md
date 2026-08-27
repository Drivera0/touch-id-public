---
title: Housing v5 — riser column and cell seat
type: project
tags:
  - touchid
  - housing
updated: 2026-08-27
---

# Housing v5

`touchid_module_v5.py`. **v4 was not edited** — it is untouched and still builds.
Run the script; it prints every clearance and runs eight boolean checks before it
exports anything.

## What changed from v4

| | v4 | v5 |
|---|---|---|
| Top face | z 7.16 | **z 11.66** |
| Sensor barrel bottom | z 4.96 | **z 9.46** |
| Riser | — | annulus OD 18.37 / ID 15.60, z 7.16 → 11.66, wall **1.385** |
| Cell seat | — | rests on the module lid through a **0.20 mm insulating pad** |
| Cell collar | — | two arcs ID 12.50 / OD 16.77, z 2.90 → 5.16, ±45° about ±Y |

Everything else carries forward untouched: 19.54 lip, 0.80 wall, 2.90 lip height,
diagonal M1.2 bosses at (±8.10, ∓8.10), M2 ear screw at `ear_diag` 13.84.

## Boolean checks — all pass

```
housing n MCU module = 0.0000    cell n MCU module = 0.0000
housing n sensor     = 0.0000    cell n bosses     = 0.0000
housing n cell       = 0.0000    MCU  n sensor     = 0.0000
cell    n sensor     = 0.0000    MCU  n bosses     = 0.0000
housing zmin = -0.0000   zmax = 11.6600   volume = 1101.56 mm^3
```

## The clearance discrepancy — the model disagrees with the brief

NEXT-SESSION expected **~2.26 mm** above the cell. The model gives **1.61 mm**.
The brief says to trust the model, so here is where the 0.65 mm went.

**−0.20 mm — the cell is taller than the brief assumed.**
VARTA gives the CP1254 A4 height as **5.4 +0.2/−0.1**, so the worst-case cell is
**5.6 mm**. v5 models 5.6. A pocket cut for 5.4 would not close on a max-tolerance
cell, and cells are not sorted.

**−0.45 mm — the cell cannot sit as low as the brief assumed.**
2.26 mm of clearance implies a cell underside at z 1.80. The MDBT50Q is 2.05 mm
tall and the cell (Ø12.1, under the centred sensor bore) sits *inside* the
module's footprint, so z 1.80 would put the cell through the module. v5 rests
the cell **on the module lid** at z 2.25, through a 0.20 mm insulating pad —
the lid is grounded and a lithium cell can is live, so the pad is not optional.

**1.61 mm is still a fit**, and it is air. Nothing has to occupy it.

## Design decisions taken, with reasons

**The cell rests on the module lid, not on ledges. This changed.**
v5's first pass grew two ledges in from the cavity wall at ±Y. That worked only
while the module was centred. Once `pcb-v3` pushed the module to
**x −0.80, y +0.90** — forced by the BQ25505's 3.98 mm land, see
`cad/pcb-v3/PCB-V3-NOTES.md` — the cell no longer overhangs the module anywhere
except a 1.6 mm sliver on +X, so no ledge can reach it from two sides.
Resting it on the lid is simpler, gains 0.20 mm of clearance, and needs one
cheap part: a **Ø12.5 × 0.20 PET or Kapton disc** between the lid and the can.

**The collar is two arcs, not a ring.** ±X is left open on purpose: that is where
the six hand-soldered sensor wires drop past the cell to J2, now at
**x −8.20 and +7.80, y 3.30 / 4.80 / 6.30**. A full ring would seal that route.
The windows are **45°** either side of the X axis, z 2.90 → 5.16 — widened from
35° because J2 moved outward and a wire to (8.20, 4.80) sits about 60° off +Y,
which the narrower window only just cleared.

**Cell radial slop is 0.20 mm per side** (pocket Ø12.50 on a Ø12.1 max cell).

**No ledges means no under-ledge height limit.** The tallest board parts are the
22 µF 0805 at 1.25 mm and L1 at 1.20 mm; both sit in the side strips, well clear.

## Carried forward unchanged and re-verified

- Sensor window Ø15.60 in the Ø18.37 riser → **1.385 mm of wall**
- ZW0905 flange Ø18.00 on the 18.37 top face → **0.185 mm margin per side**

That 0.185 mm is unchanged from v4 and is still the tightest number in the whole
housing. It has not got worse, but it has not got better either.

## Still open

- **The cell needs retaining from above.** Nothing stops it lifting off the lid;
  the sensor barrel is 1.61 mm above it. A foam pad or an adhesive dot is the
  obvious answer, but it is not modelled.
- **The insulating disc is a new part** and is not on the BOM.
- `mcu_center` now tracks `pcb-v3` at **(−0.80, 0.90)**. If the board placement
  moves again, re-run this script — it re-runs all eight boolean checks and will
  catch a collision.
