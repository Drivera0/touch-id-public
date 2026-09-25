---
title: Module mechanical v4 — square PCB, M1.2 screws, two layout options
type: project
tags:
  - touchid
  - mechanical
  - housing
updated: 2026-08-20
---

# Module mechanical v4

Source: `cad/scripts/touchid_module_v4.py` — a patched copy of
`touchid_module.py`, so **all the caliper-measured geometry, the ear, the rear
shelf, the sensor seat and the smoothed trims are preserved exactly**. Verified:
the v4 outer envelope matches `touchid_module_housing_final.stl` to within
0.002 mm (mesh tolerance).

Baseline archived untouched at
`cad/archive/2026-08-20-housing-final-baseline/`.

Set `MODE` at the top of the script and re-run; both variants are exported.

---

## The two options are mutually exclusive

U1 is 13.2 mm wide. Even after thinning the wall, the cavity is 17.94, leaving
**4.74 mm of spare width** to divide between the two sides. A top-side FPC
connector needs 3.25 (2.90 body + clearances) and a screw boss needs 2.60 even
at M1.2. That's 5.85 against 4.74.

So you can have the connector **or** diagonal screws, not both. Dropping to
M1.0 doesn't rescue it, and neither does a 0.4 mm wall.

| | `MODE = "connector"` | `MODE = "diagonal"` |
|---|---|---|
| U1 | pushed to −X, x [−8.75, 4.45] | centred, x ±6.60 |
| PCB screws | **(8.10, +8.10) and (8.10, −8.10)** | **(8.10, −8.10) and (−8.10, +8.10)** |
| Free strip | **4.17 mm** — FPC connector fits with 1.27 spare | 2.37 mm — **no top-side connector** |
| Sensor wiring | plug-in FPC | hand-soldered, or move it to the underside |

### Bosses sit on the corner diagonal

Both modes put the bosses at (±8.10, ±8.10), tucked into the cavity corners so
they fuse into **both** walls and stay clear of the side strips.

`boss_c = 8.10` is a balance between two limits that pull in opposite
directions. Moving **out** along the diagonal buys clearance from U1 (0.00 mm at
c = 7.45, 0.31 at 8.10, 0.50 at 8.30) but eats the outer wall (1.98 mm at 7.45,
1.06 at 8.10, 0.21 at 8.70). 8.10 keeps both healthy.

Note the boss radius **cannot exceed 1.202 mm anywhere on the diagonal** — that
is the perpendicular distance from U1's corner (6.6, 8.3) to the line y = x. So
the corner buys position, not a bigger boss.

Moving into the corner also improved the tight pogo clearance from **0.31 mm to
0.58 mm**.

### The corner still doesn't unlock connector + diagonal together

Corner bosses let U1 shift 0.42 mm before the boss fouls it, which narrows the
gap but does not close it:

| Screw | Wall 0.8 | Wall 0.7 | Wall 0.6 |
|---|---|---|---|
| M1.2 | short 0.46 | short 0.36 | short 0.26 |
| M1.0 | short 0.20 | short 0.10 | **0.00** |

Only M1.0 screws on a 0.6 mm wall reach parity, at exactly zero margin. Not a
trade worth taking on this project.

Both keep the **M2 ear screw unchanged** (Ø2.0 hole, countersink, at the (−,−)
corner) — that one goes into the keyboard's threaded boss and was never a PCB
fastener.

---

## What changed from `touchid_module.py`

| | v3 final | v4 |
|---|---|---|
| PCB screws | 2 × M2, pilot Ø1.7, boss r2.3 | **2 × M1.2**, pilot Ø0.95, boss r1.20 |
| Screw positions | (±8.3, 0) | mode-dependent, see above |
| Lip wall | 1.40 | **0.80** |
| Lip cavity | 16.74 | **17.94** |
| Ear screw | M2 | M2, unchanged |
| PCB | 19.60 × 17.60 | **19.30 square**, R2.0 |

### Why the wall had to come down

**Your current cavity is 16.74 mm and the ESP32-C3-MINI-1 is 16.6 mm long — a
total clearance of 0.14 mm, i.e. 0.07 mm per side.** That is not a real fit; a
0.1 mm moulding or print variation and the module doesn't go in. Thinning the
lip wall to 0.80 gives 17.94, so 1.34 mm total (0.67 per side), and is what
makes either of the two options above possible at all.

0.80 mm is comfortable for injection moulding, thin for FDM. If you prototype in
PETG expect the lip tier to be fragile.

### Bug fixed

`touchid_module.py` unions the mounting ear **after** cutting the cavity, and
the ear bar reaches to radius 9.0 along the corner diagonal — inside the cavity
footprint. Measured on your script: the bar fills the cavity corner and
**collides with a centred ESP32 module by 5.567 mm³**, at
x [−6.60, −4.55], y [−8.30, −6.13], z [0, 2.40].

v4 re-cuts both cavity tiers after the ear is merged, so the cavity always wins.
Worth back-porting.

---

## Verification

Boolean-checked on the solids, both modes:

- housing ∩ ESP32 module = **0.000 mm³**
- outer envelope matches the original STL to 0.002 mm
- nothing on the housing goes below z = 0, so the PCB underside at −1.2 stays
  the lowest plane and the pogo pads are never held off

Screw clearance to the nearest pogo pad (PCB hole Ø1.3):

| Mode | Screw | Pogo clearance | PCB hole → edge |
|---|---|---|---|
| connector | (8.10, +8.10) | +11.23 mm | +0.71 mm |
| connector | (8.10, −8.10) | **+0.58 mm** | +0.71 mm |
| diagonal | (8.10, −8.10) | **+0.58 mm** | +0.71 mm |
| diagonal | (−8.10, +8.10) | +8.61 mm | +0.71 mm |

The 0.58 mm one is the tightest; re-check it when the pogo pad positions are
re-derived for the square outline. Boss detail at c = 8.10: spans 6.90…9.30 so
it merges into both cavity walls, 0.31 mm gap to U1, 1.06 mm of wall around the
pilot.

---

## Open items

- **M1.2 self-tapping into plastic** is fine for a handful of assembly cycles.
  If the module needs repeated servicing, use heat-set inserts — but check they
  fit the boss OD first.
- **Component positions are provisional.** Nothing goes to copper until the
  sensor is bought — see [[touchid/docs/design/Sensor Connector Plan|Sensor Connector Plan]].
- **PCB outline tolerance.** 19.30 nominal, ±0.2 → 19.50 worst case, inside the
  19.54 lip. Don't go bigger without tightening it.
- The rear retention shelf is carried over unchanged from v3 and has **not**
  been re-checked against the new wall thickness.

## Files

| File | What |
|---|---|
| `cad/scripts/touchid_module_v4.py` | parametric source, `MODE` at the top |
| `cad/exports/touchid_assembly_v4_*.step` | housing + board, coloured — open in Fusion |
| `cad/exports/touchid_housing_v4_*.step` / `.stl` | housing alone |
| `cad/exports/touchid_pcb_v4_*.step` / `.stl` | matching square board blank |
| `cad/archive/2026-08-20-housing-final-baseline/` | your untouched original |

## Related

- [[touchid/docs/design/Sensor Connector Plan|Sensor Connector Plan]]
- [[touchid/docs/design/Mechanical and Housing|Mechanical and Housing]]
- [[touchid/docs/build/JLCPCB DFM Report|JLCPCB DFM Report]]
