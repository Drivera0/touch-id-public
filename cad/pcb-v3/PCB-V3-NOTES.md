---
title: pcb-v3 — placement, and the constraint that set it
type: project
tags:
  - touchid
  - pcb
updated: 2026-08-27
---

# pcb-v3

Built by `build_pcb_v3.py`. **`pcb-v2.kicad_pcb` was not touched.**

| | |
|---|---|
| Outline | 19.30 × 19.30, R2.0 |
| Layers | **4** — F.Cu, In1.Cu, In2.Cu, B.Cu |
| Nets | 27, from `netlist_v3.py` (single source of truth) |
| Footprints | 46 · **177 pads** |
| Zones | 7 — antenna keep-out ×4 layers, GND pour on F.Cu / In2.Cu / B.Cu |

## Checker results

```
sexp_check   PARSE OK, 1901 CRLF, 0 bare LF          <- run first, always
check_board  different-net pairs < 0.127 mm : 0
check_connect  27 nets split                          <- EXPECTED, see below
```

**It is not routed.** Placement is checked; tracks are not drawn. Scripting an
autorouter in one sitting and trusting its output is a worse idea than routing
it in KiCad, where you can see what it does. So `check_connect` reports every
net as split — that is the unrouted state, not a defect. Route, then re-run all
three.

## The constraint that set the layout

**The BQ25505's land is ~3.98 mm across and there is no 3.98 mm strip beside a
centred module.**

Two independent sources agree on that width:

- TI drawing **RGR0020A 4219031/B** — perimeter pads at ±1.65 centre-to-centre
  with a 0.6 length → **3.90** overall.
- JLCPCB assembly library **C882746** — ±1.658 with 0.665 → **3.98** overall.

With U1 centred, each side strip is 8.97 − 5.25 = **3.72 mm**, and the charger
fits in neither. So **U1 is shifted to x = −0.80**, which opens a 4.32 mm strip
on +X. The antenna still points at **+Y, the spacebar** — only its X position
moves, and Raytac wants the module near a board edge anyway.

This was a forced move, not a preference.

### And the Y position is set by the housing, not the board edge

The module is 15.5 mm long in a **17.94 mm lip cavity**, so its centre cannot
exceed 8.97 − 7.75 = 1.22 or the lip wall lands on the module. 1.22 leaves
0.02 mm, which is not a fit on a printed part, so **U1_CY = 0.90** — 0.32 mm of
real margin, at a cost of 0.3 mm of antenna-to-edge distance.

## Layout

| Region | x | Holds |
|---|---|---|
| Left strip | −8.97 … −6.25 (2.72) | U3, U4, C1, C2, BT1 pads. **Too narrow for an 0805** |
| Right strip | 4.65 … 8.97 (4.32) | U2 and every 0805 — the only strip wide enough |
| Bottom strip | full width, y < −6.85 | **two rows of ten 0402s** — this is what makes the twenty small parts land |

Antenna keep-out, **all four copper layers**: x −7.05 … 5.45, y 4.85 … 9.65.
Nearest pogo copper is at y −1.12, so it clears by **5.97 mm**.

The ten pogo pads keep their **exact** pcb-v2 coordinates, extracted rather than
retyped.

## The three carried-over issues, all fixed

1. **`+3V3`/`VBAT` at 0.1270** — gone. Both nets are gone with the old power
   architecture, and the closest different-net pair on v3 is above 0.127.
2. **F.Paste on J2** — removed. J2, J3, BT1 and the test points are all
   `F.Mask`/`B.Mask` only. A stencil would have printed solder domes on pads
   that get hand-soldered.
3. **Pads left for "the autorouter"** — none. Every netlist pin has a pad and
   every pad has its net; the checker fails the build if one is missing.

## Two checker bugs this found — worth knowing about

- My clearance function used `min(dx, dy)` for overlapping boxes, so it
  reported **−1.8 mm for pads that overlapped by 0.2**. Wrong number, real
  violation. It is `max(dx, dy)` — the shallower axis.
- I had it skip every same-footprint pad pair, reasoning that vendor land
  patterns are the vendor's business. That also skipped **BT1's own two wire
  pads, sitting 0.100 mm apart** — which `check_board` then caught. The skip now
  applies only to U1/U2/U3/U4.

Both are the same lesson as DESIGN-SPEC §7 trap 3: a checker printing a
confident summary is not evidence.

## PROVISIONAL — verify before ordering

| Ref | Why |
|---|---|
| **L1** | `C2849435` is a DMBJ **PNLS252012-220M**, so 2.5 × 2.0 × **1.2** mm — but its **land pattern was never traced**. An 0805 land stands in and is very likely too small. Get the DMBJ drawing. |
| **BT1** | VARTA gives CP1254 dimensions "without Tags" and does not publish the tab geometry. Two generous wire pads are used instead. The cell is wired down from above anyway, so this is the safe choice either way. |
| **C1, C2 (0603)** | 0402 and 0805 lands come from Samsung's tables via DESIGN-SPEC §3. 0603 is IPC nominal, not traced to a specific part. |

## Still to do

- **Route it.** Then re-run all three checkers and expect `check_connect` to
  report 0 split nets.
- Vias must avoid the pogo pads: the ten of them own B.Cu below y = −1.12.
- In1.Cu is currently an empty signal layer. It is there for routing; In2.Cu
  carries the solid ground plane.
