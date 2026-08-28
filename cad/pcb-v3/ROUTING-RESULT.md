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
