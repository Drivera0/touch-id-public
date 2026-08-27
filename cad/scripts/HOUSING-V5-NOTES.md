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
| Cell seat | — | two ledges at ±Y, z 1.65 → 2.45, inner edge \|y\| = 5.45 |
| Cell collar | — | two arcs ID 12.50 / OD 16.77, z 2.90 → 5.16, ±55° about ±Y |

Everything else carries forward untouched: 19.54 lip, 0.80 wall, 2.90 lip height,
diagonal M1.2 bosses at (±8.10, ∓8.10), M2 ear screw at `ear_diag` 13.84.

## Boolean checks — all pass

```
housing n MCU module = 0.0000    cell n MCU module = 0.0000
housing n sensor     = 0.0000    cell n bosses     = 0.0000
housing n cell       = 0.0000    MCU  n sensor     = 0.0000
cell    n sensor     = 0.0000    MCU  n bosses     = 0.0000
housing zmin = -0.0000   zmax = 11.6600   volume = 1171.12 mm^3
```

## The clearance discrepancy — the model disagrees with the brief

NEXT-SESSION expected **~2.26 mm** above the cell. The model gives **1.41 mm**.
The brief says to trust the model, so here is where the 0.85 mm went.

**−0.20 mm — the cell is taller than the brief assumed.**
VARTA gives the CP1254 A4 height as **5.4 +0.2/−0.1**, so the worst-case cell is
**5.6 mm**. v5 models 5.6. A pocket cut for 5.4 would not close on a max-tolerance
cell, and cells are not sorted.

**−0.65 mm — the cell cannot sit as low as the brief assumed.**
2.26 mm of clearance implies a cell underside at z 1.80. The MDBT50Q is 2.05 mm
tall and the cell (Ø12.1) sits *entirely inside* the module's 15.5 × 10.5
footprint, so z 1.80 would put the cell through the module. The cell underside
has to be above 2.05. v5 puts it at **2.45**, allowing 0.40 mm because the
module's lid is a grounded metal shield and a lithium cell can is live — they
must not touch.

**1.41 mm is still a fit**, and it is air. Nothing has to occupy it.

## Design decisions taken, with reasons

**Cell rests on ledges, never on the module.** Two ledges grow in from the
lip-tier cavity wall at ±Y. Their inner edge is at \|y\| = 5.45, which clears the
module edge at 5.25 by 0.20 mm. The cell rim reaches \|y\| = 6.05, so it overhangs
and bears on the strip beyond. The ±Y direction is the only place a ledge can
reach the cell without crossing the module footprint.

**The collar is two arcs, not a ring.** ±X is left open on purpose: that is where
the six hand-soldered sensor wires drop past the cell to J2 at
(±7.60, 2.90 / 4.40 / 5.90). A full ring would seal that route. The windows are
35° either side of the X axis, z 2.90 → 5.16.

**Cell radial slop is 0.20 mm per side** (pocket Ø12.50 on a Ø12.1 max cell).

**Component headroom under the ledges is 1.65 mm.** The tallest planned part is
the 22 µF 0805 sensor-rail cap at 1.25 mm, so it fits — but Task E must keep tall
parts out of the two strips at \|y\| 5.45 → 9.0, \|x\| ≤ 4.0.

## Carried forward unchanged and re-verified

- Sensor window Ø15.60 in the Ø18.37 riser → **1.385 mm of wall**
- ZW0905 flange Ø18.00 on the 18.37 top face → **0.185 mm margin per side**

That 0.185 mm is unchanged from v4 and is still the tightest number in the whole
housing. It has not got worse, but it has not got better either.

## Still open

- `mcu_center` is provisional at (0, 0). Task C decides the real placement, and
  the ledge geometry depends on it — if the module moves in Y, the ledges move
  with it. Re-run the script after Task C is settled.
- The cell needs retaining from above. Nothing currently stops it lifting off the
  ledges; the sensor barrel is 1.41 mm above it. A foam pad or an adhesive dot is
  the obvious answer but it is not modelled.
