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
| Zones | **12 — keep-outs only** (antenna ×4, screw-boss ×2×4). GND pours are OFF until routing is done — see below |

## Checker results

```
sexp_check    PARSE OK, 0 bare LF, 46 footprints, 177 pads, 12 zones
check_board   different-net pairs < 0.127 mm : 0
check_drc     NO DRC VIOLATIONS          (KiCadRoutingTools, graded at 0.20)
check_connect 27 nets split                <- EXPECTED, see below
```

Closest body to a screw boss: **C5, 0.770 mm clear** of the r1.40 keep-out.
Closest copper to a screw hole: **J11-2, 0.200 mm clear** of the 0.850 keep-out.

**It is not routed.** Placement is checked; tracks are not drawn. Scripting an
autorouter in one sitting and trusting its output is a worse idea than routing
it in KiCad, where you can see what it does. So `check_connect` reports every
net as split — that is the unrouted state, not a defect. Route, then re-run all
three.

## Route first, pour last — the GND pours are OFF on purpose

`EMIT_GND_POURS = False`. This is not a detail; it is what was hanging KiCad.

KiCadRoutingTools' parser states it plainly (`kicad_parser.py:5163`):
*"every zone consumer (obstacle map, plane connectivity) treats `pcb.zones` as
copper"*. The earlier board had GND pours spanning the **whole 19.30 mm square
on three of the four layers**. To any of the 26 non-GND nets that is one giant
foreign-copper obstacle covering the entire board — every pad escape blocked
immediately. The router thrashed 200,000 iterations per net, and because the
plugin routes **in-process**, KiCad's window could not repaint. It looked
frozen. It was working, hopelessly.

Rule areas are unaffected — the parser skips them via `GetIsRuleArea()` — so
the twelve keep-out zones are still enforced during routing.

**Order: route the signals, then lay the plane down** (the plugin's Planes tab,
or set `EMIT_GND_POURS = True` and rebuild). That is the normal PCB order
anyway. Settings sheet: `ROUTING-SETTINGS.md`.

## The mounting screws — a constraint I had missed

Daniel asked whether anything was sitting on the two corner screws. It was.

The housing does not just want a hole there: it grows a **solid plastic boss of
radius 1.20 mm** at each screw (`touchid_module_v5.py`, boss_r 1.20, 4 mm tall)
standing directly on the board face. Each screw therefore costs a **r1.20 disc
of board area**, not a Ø1.30 hole.

The first placement put **ROK3 dead under the +X boss** — 0.000 mm — with R2 at
0.25, ROK2 at 0.95 and R1 at 0.98 also inside it, and ROK3's copper 0.219 mm
from a hole needing 0.850. My checker had tested the keep-out, the cavity,
courtyard overlap and pad clearance, and never tested this.

Three things changed as a result:

1. **`BOSS_XY` / `BOSS_R` / `BOSS_KEEP` are now hard constraints applied at
   placement time,** not a check run afterwards.
2. **The keep-outs are drawn into the board** as real rule areas — a 24-sided
   polygon of radius 1.40 at each screw, on **all four copper layers**, with
   tracks, vias, pads, copper pour and footprints all disallowed. KiCad's own
   DRC and any autorouter now enforce them; previously only this script knew.
3. **The twenty 0402s are packed by search, not by a hand-written slot list.**
   The hand list found 23 slots, lost 4 to the bosses and came up one part
   short, which nearly cost C13. The packer masks every 0.05 mm position on the
   board in both rotations, lays shelves from the bottom edge up, then mops up
   the leftover pockets. **20/20 placed, 2 rotated, nothing dropped.**

### And a 0.08 mm problem worth remembering

With honest 0.20 mm clearance the bottom strip was **1.92 mm** tall and two rows
of 0402 need **2.00**. Eight hundredths of a millimetre, and it cost a whole row
of eight parts — which is what made the board look full.

U1 had 0.32 mm of unused travel toward the spacebar before it fouls the lip
wall, so **U1_CY went 0.90 → 1.00**. The strip became 2.02 mm, both rows fit,
and there is still 0.22 mm against the wall. That is the entire fix.

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
0.02 mm, which is not a fit on a printed part. **U1_CY = 1.00** — 0.22 mm of
real margin, at a cost of 0.22 mm of antenna-to-edge distance. See the 0.08 mm
note above for why it is 1.00 and not 0.90.

## Layout

| Region | x | Holds |
|---|---|---|
| Left strip | −8.97 … −6.25 (2.72) | U3, U4, C1, C2, BT1 pads. **Too narrow for an 0805** |
| Right strip | 4.65 … 8.97 (4.32) | U2 and every 0805 — the only strip wide enough |
| Bottom strip | full width, y < −6.75 | **two rows of ten 0402s** — this is what makes the twenty small parts land |

Antenna keep-out, **all four copper layers**: x −7.05 … 5.45, y 4.95 … 9.65.
Nearest pogo copper is at y −1.12, so it clears by **6.07 mm**.

Screw keep-outs, **all four copper layers**: r1.40 at (+8.10, −8.10) and
(−8.10, +8.10) — tracks, vias, pads, pour and footprints all disallowed.

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

## 2026-08-27 — the routing failure, its two root causes, and the fix

The first autoroute left **23 of 58 pad pairs open**. The cause was placement,
not router settings, and there were two of them.

### Root cause 1 — 43 dead pads sealed the module

`fp_mdbt50q()` emitted all 61 pads from Raytac's drawing. **Only 18 are
connected**; the other 43 are unused GPIO with no net. Measured on the built
board, the ring's neighbour gaps are **uniformly 0.40 mm** — every one of the
12 gaps along the bottom edge. A 0.20 mm track at 0.20 mm clearance needs
**0.60 mm** to pass. So the ring was a sealed wall:

- inner-ring signals could not escape outward
- **78.7 mm2 of empty board and 26.7 mm2 of legal via sites inside the ring
  were unreachable**

Fix: emit only the 18 connected pads. Omitting land under an unused module pin
is normal practice — the pin sits over solder mask. Cost: 18 solder joints
instead of 61, of which 6 are the large GND pads.

Measured effect: F.Cu routable area **135 -> 171 mm2 (+27%)**, legal via-site
area **56 -> 69 mm2 (+23%)**, largest single via region 20.4 -> 27.6 mm2.

### Root cause 2 — the packer optimised area, not routability

`_CLR = 0.20` was body-to-body and the courtyard only adds 0.14, so parts sat
**0.34 mm apart pad-to-pad** in two solid rows of eight. Nothing could enter or
leave that strip: 0.60 mm is needed for one track, 1.00 mm for a via.

Two changes:

1. **Directional spacing.** An 0402's pads face along its long axis. That is
   the gap that must be a channel (0.60); the perpendicular gap only needs
   clearance (0.20). The bottom row is now 14 parts rotated 90 deg with
   **0.67 mm channels above and below**, so every pad exits into open board.
2. **Slots and assignment are now separate problems.** Geometry generates the
   legal slots; a Hungarian assignment then decides which part goes in which,
   against the centroid of the pins it actually connects to. The old packer was
   netlist-blind and put ROK1/ROK2/ROK3 — one divider chain on U2's right-hand
   pins — on three different edges of the board.

Board capacity is **exactly 20 routable slots for 20 parts**. There is no spare.

### The result, and what is still wrong

Nets fully connected went **14/27 -> 23/27**. But the router bought that with
copper we did not ask for:

| | |
|---|---|
| segments below the 0.127 fab floor | **285 of 447**, at 0.0889 mm |
| vias | **all 55 at 0.25/0.15**, not the 0.6/0.3 netclass |
| tightest clearance | **0.1156 mm** (U2 pad 8 to a VBAT_OV_SET track) |
| still open | VRDIV, and parts of VSTOR / VIN_DC / SENSOR_MCU_3V3 |

This is KiCadRoutingTools' "terminal geometry escalation", which prefers
shipping thin copper to reporting an open. It is a reasonable default and the
wrong one for us. **The connectivity number is not trustworthy until escalation
is forbidden** — `--fab-overrides` pins the floor and disables it.

### A correction to ROUTING-SETTINGS.md

I said "Fix DRC settings after routing" was safe because it only clamps net
classes when the Min Clearance override is ticked. That is wrong. It **loosened
three Board Setup values to the routed floors** — it rewrites your design rules
to match whatever the router did. Leave it **unticked**.
