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
