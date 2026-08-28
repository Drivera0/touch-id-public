---
title: pcb-v3 routing — honest results, and the one thing still broken
type: project
tags: [touchid, pcb, routing]
updated: 2026-08-27
---

# Routing pcb-v3

The router now runs **locally in the sandbox** (`tools/com_github_.../` has a
`grid_router-linux-x86_64.so`), so this is CLI output, not GUI screenshots.

## The fab floor had to be pinned first

With only `--fab-tier standard` the router silently routed **285 of 447
segments at 0.0889 mm** and put **all 55 vias at 0.25/0.15** — the "advanced,
more costly" rung. It does this deliberately: *"terminal geometry escalation
(better than shipping opens)"*.

Correction to an earlier note: 0.0889 is **not** below JLC's floor. Per
`py_router/fab_tiers.py`, JLC standard for **4 layers** is 0.0889 track /
0.10 clearance; 0.127 is the **2-layer** number. So that board was orderable —
it just was not what `pcb-v3.kicad_pro` specifies, and nothing said so.

`fab_floor_touchid.txt` pins the floor and **disables escalation**.

## Results, same placement, three floors

| floor | unrouted nets | disconnected pads | segments under 0.20 |
|---|---|---|---|
| **0.20** (our design rule) | 1 (VRDIV) | 6 | 0 / 442 |
| 0.16 | 1 (VRDIV) | 6 | 2 / 442 |
| 0.127 | **0** | **5** | 102 / 542 |

`pcb-v3-routed2.kicad_pcb` is the 0.20 board: every track >= 0.20, every via
0.6/0.3, exactly the netclass. `pcb-v3-routed-0127.kicad_pcb` is the 0.127 one.

## Everything still open is U2

- VBAT_OK    - U2 (8.46, 0.31)
- VBAT_OV_SET- U2 (6.56, -1.59)
- VIN_DC     - U2 (5.16, 0.31)
- VSTOR      - U2 (6.06, 1.71) and U4 (-7.18, -0.33)
- VRDIV      - ROV2, the divider that hangs off U2 pin 8

**Why.** U2 is a 0.5 mm-pitch QFN: its pad-to-pad gap is **0.26 mm** and a
0.20 track needs 0.60 mm to pass, so nothing routes between its pads. Every
pin must escape radially — and U2's land is 3.90 mm in a 4.32 mm strip, giving
**0.21 mm of ring per side**. There are about two usable lanes for twenty pins.

U1 cannot move to widen that strip: at `U1_CX` -1.20 the packer loses a slot,
at -1.60 and -2.00 the left strip overflows. Verified by sweep.

## Next

Free the right strip for U2's divider chain by moving the three 0805s (C5, C7)
out of it — rotated, an 0805 is 1.10 mm wide and fits the 2.72 mm left strip.
Then ROV1/ROV2/ROK1/ROK2/ROK3 can sit beside the pins they program.

---

## Update — two hard limits found, and one tool bug

### The autorouter ignores `--layers` and routes on the ground plane

Every run prints:

```
Using 3 routing layers: ['F.Cu', 'In1.Cu', 'B.Cu']
  Full-stack: appended 1 unrequested copper layer(s) as FORBIDDEN obstacles
  (no routing, vias respect their copper): In2.Cu
```

…and then puts **signal segments on In2.Cu anyway**:

| run | In2.Cu signal segments |
|---|---|
| `--layer-costs … 3.0` on In2.Cu | 41 (VIN_DC 24, VSTOR 9, OK_HYST 4, …) |
| In2.Cu cost raised to **999** | still 25, and connectivity got *worse* |

So the continuous ground plane — the entire reason this board is 4 layers —
**cannot be protected by configuration.** Any routed output must be checked for
In2.Cu signal copper, and cleaned by hand.

### U2 cannot be fully escaped at this board size

BQ25505 is 0.5 mm pitch: **0.26 mm between pads**, and a 0.20 mm track needs
0.60 mm to pass. So every pin escapes radially only, and U2's 3.90 mm land sits
in a 4.32 mm strip — **0.21 mm of ring per side**, roughly one lane per edge for
2-3 signals per edge. Four pins are structurally stuck (one per side):

- pin 2  VIN_DC       (5.16, 0.31)
- pin 13 VBAT_OK      (8.46, 0.31)
- pin 19 VSTOR        (6.06, 1.71)
- pin 8  VRDIV        (7.06, -1.59)

Everything tried, and rejected:

| attempt | result |
|---|---|
| rip-up 8, 400k iterations | no change |
| finer floor 0.127 | closes VRDIV, still 3 stuck |
| open In2.Cu to the router | no change — they can't leave the pad at all |
| via-in-pad | **impossible** — pads are 0.24 mm wide, narrower than any via |
| move U1 left to widen the strip | pushes the antenna keep-out onto J2's sensor pads |
| bottom-anchor the 0805s, move J2 outboard | no net gain |

`U1_CX` was swept at -1.00/-1.30/-1.50/-1.70: the left strip overflows or the
packer loses a slot. **The current placement is a genuine local optimum.**

### Where that leaves it

`pcb-v3-routed-best.kicad_pcb` — 406-460 segments, all >= 0.20 mm, vias 0.6/0.3,
no DRC violations at the 0.127 grading. Open: the four U2 pins above, plus
41 signal segments sitting on In2.Cu that must be moved off.

This is the point the original brief anticipated: *"routing it in KiCad, where
you can see what it does."* Six connections and a plane cleanup is an hour of
interactive routing, and a human can nudge neighbours in ways the batch router
will not.

## The plane cannot be protected — measured, not assumed

A full-board **rule area on In2.Cu** (`tracks not_allowed`, vias and pour
allowed) was added to `build_pcb_v3.py`. The router honours rule areas for the
antenna and screw keep-outs, so this should have worked. It did not:
41 -> 25 segments, and connectivity got *worse*.

Strip-and-reroute was then iterated three times (delete In2.Cu copper, re-route
only the nets that broke):

| round | In2.Cu segments after | open pads |
|---|---|---|
| 1 | 42 | 8 |
| 2 | 44 | 7 |
| 3 | 30 | 7 |

**It does not converge.** The router's rescue phase bypasses the layer
restriction. Configuration cannot fix this.

## Two end states, and the trade between them

| file | plane | open connections |
|---|---|---|
| `pcb-v3-routed-best.kicad_pcb` | **carved** — 41 segs / 50 mm, incl. a 23.8 mm VIN_DC run across 16 of 19.3 mm | **4** |
| `pcb-v3-handoff.kicad_pcb` | **intact** — In2.Cu signal copper removed | **16** |

That copper was load-bearing, which is why removing it costs twelve more
connections.

**Recommendation: take `pcb-v3-handoff.kicad_pcb`.** The continuous return path
is why this board is 4 layers; a plane cut by a 23.8 mm slot under the boost
converter is a permanent defect that is hard to reason about later, whereas
sixteen short hand-routes are an evening's work and most sit in open board.

## Driving it further — and the third proof the board is over-subscribed

Routing one net at a time onto the plane-clean board, accepting a result only
if it (a) added **zero** In2.Cu copper and (b) reduced total open pads, drove it
from 16 open to **12 open with the plane fully intact**. It then converged —
no further single-net attempt improved it.

`pcb-v3-handoff.kicad_pcb`: 397 segments, 49 vias, **min track 0.200 mm, all
vias 0.6/0.3, NO DRC VIOLATIONS at 0.20, zero signal copper on In2.Cu.**

But the 12 are *not* all U2. Five VSTOR opens are on U3/U4/TP2/J3 and two
VIN_DC opens are on TP1/C1 — the **left strip**. Measured:

```
left column: 4 parts (U3,U4,C1,C2), 4.90 mm of bodies in 5.80 mm of space
   (BT1's 3.00 mm wire pads occupy -6.60..-3.60 of the same strip)
=> max gap per part = 0.225 mm     a 0.20 track needs 0.60 pad-to-pad
```

So the left column has the identical defect the 0402 rows had, and it cannot be
fixed by spacing: 0.60 mm gaps for those four parts need 7.30 mm and there is
5.80. Raising the gap just drives C2 into BT1 (verified: -0.225 mm overlap).

That is the **third independent place** the board runs out of room — bottom row,
U2's ring, left column. It is one finding, not three: **there is not enough
perimeter to give every part a routing channel.**

## The way out is the BOM, not the layout

| change | frees |
|---|---|
| C1, C2 4.7 uF **0603 -> 0402** | 0.50 mm of left-column height, 1.45 mm width each |
| C5 10 uF, C7 22 uF **0805 -> 0603** | the right strip stops being the only home for them |
| **BT1's wire pads out of the left column** | left column gap 0.225 -> **1.14 mm** |

That last one is the big one. Tested C1/C2 -> 0402 alone: still only 0.35 mm of
gap, because BT1 is what actually caps the column.

Caveat before adopting: a 22 uF 0603 has worse DC-bias derating and higher ESR
than the 0805. C7 exists to hold the ZW0905's 200 mA / 4 us scan transient to
36 mV, so that one needs its derated capacitance checked, not just its
footprint swapped.

## Implemented: the BOM change, and the result

Three changes, then re-routed:

1. **C1, C2 (4.7 uF) 0603 -> 0402** and moved out of the hand-written left
   column into the netlist-driven packer. They are CIN and CSTOR — they belong
   at U2, and a size-only stack had put them on the opposite edge of the board.
2. **C5 (10 uF), C7 (22 uF) 0805 -> 0603**, so the right strip is no longer the
   only place they can physically go.
3. **Left column is now just U3 + U4** at 1.00 mm gaps. BT1 stayed where it was
   — it was never the problem on its own; *four* parts in a 5.80 mm column was.

Slots went 20/20 (no spare) to **22 parts in 22 slots**, and the router stopped
needing the plane layer at all.

| | before | after |
|---|---|---|
| open connections | 12 | **7** |
| signal copper on In2.Cu | 0 (only after stripping) | **0, natural** |
| DRC violations @0.20 | 0 | 1 (53 um pad clip) |
| min track / vias | 0.200 / 0.6-0.3 | 0.200 / 0.6-0.3 |

The one DRC item is a VSTOR segment clipping the corner of U3's thermal pad by
**0.053 mm**. Four re-route variants all reproduce it; it is a ten-second drag
in KiCad and not worth more batch attempts.

### Still to verify before ordering

C7's 22 uF is now 0603. It exists to hold the ZW0905's 200 mA / 4 us scan
transient to 36 mV. **Check its DC-bias-derated capacitance, not just that the
footprint fits** — a 0603 22 uF derates harder than the 0805 did.
