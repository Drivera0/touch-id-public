---
title: Sensor connector plan — replacing the J2 solder pads
type: project
tags:
  - touchid
  - hardware
  - mechanical
  - jlcpcb
updated: 2026-08-20
---

# Replacing J2's hand-soldered pads with a plug-in connector

Goal: the fingerprint sensor's tail plugs in instead of being soldered to six
Ø1.2 mm pads. **Nothing has been changed on the board yet** — the pin order and
pin count depend on which sensor gets bought, and getting that wrong means
redoing the footprint. See "What this is waiting on" at the bottom.

---

## The part

**JLCPCB `C5213748`** — HCTL **HC-FPC-05-09-6RLTAG**, 0.5 mm pitch, 6-pin,
horizontal back-flip ZIF.

| | |
|---|---|
| Body | 5.00 (L) × 2.90 (D) × **1.00 (H)** mm |
| PCB land depth | **3.30 ±0.05** mm |
| Depth incl. actuator swing | **(3.5)** mm — reference dim, no tolerance given |
| Tier / stock / price | Extended · ~39 000 · $0.061 |
| Datasheet | https://datasheet.lcsc.com/datasheet/pdf/94239c3bf870fbd9168a2953a20da7e1.pdf |

Dimensionally identical twin if it ever goes out of stock: XFCN
**F0504-H-06-10G-R**, `C510962`. Same series in 4/5/8 pin: `C5213746`,
`C5213747`, `C5213749`.

### Why not a vertical / top-entry connector

The sensor sits directly above the board and its tail comes straight down, so a
top-entry ZIF looks like the obvious geometry. It is the wrong call — every
vertical FPC part at JLCPCB is **larger on all three axes**:

| | best vertical (`C262496`) | this horizontal part |
|---|---|---|
| Length | 8.60 | **5.00** |
| Depth | 3.00 | **2.90** |
| Height | 4.40 closed, **5.65 latch open** | **1.00** |

At 1.00 mm tall there is ample room to fold the tail down beside the sensor.

> Nothing finer than 0.5 mm pitch is available at 4–8 pins. Hirose FH33 (2.5 mm
> deep) and Kyocera 6844 (2.7 mm) would both fit outright, but LCSC only stocks
> them from 9 and 11 positions up. **2.90 mm body / 3.30 mm land is the floor of
> the whole category** — so this plan holds for any 0.5 mm ZIF, not just this part.

---

## Why it does not fit today

The two side strips beside U1 are the only free top-side area, and they are
narrower than earlier notes assumed (those describe a 1.6 mm strip on a
superseded board outline).

| | mm |
|---|---|
| Board half-width | 9.80 |
| U1 body edge | 6.60 |
| Raw strip | 3.20 |
| less 0.25 to the module body, 0.25 to the board edge | **2.70 usable** |
| connector keepout needed | **3.50** |
| **shortfall** | **0.80** |

Tightening to the absolute minimums — 0.15 mm to the module, 0.20 mm
copper-to-edge — gets to 2.85 and still leaves a 0.65 mm shortfall. Dropping to
a 4-pin part does not help: it shortens the connector, and **depth is the
constraint, not length**.

---

## The plan: shift U1, and give up the second screw

### 1. Move U1 0.80 mm in −X

New U1 extents (board-local, board is x ∈ [−9.80, 9.80], y ∈ [−8.80, 8.80]):

| | now | after |
|---|---|---|
| Body | x [−6.60, 6.60] | x [−7.40, 5.80] |
| Courtyard | x [−6.80, 6.80] | x [−7.60, 6.00] |
| Copper | x [−6.30, 6.30] | x [−7.10, 5.50] |

Y is unchanged — U1 is 16.6 mm on a 17.6 mm board, so there is only 1.0 mm of
total slack in that axis and none of it is useful.

Result: **right strip 3.50 mm** (x 6.05 → 9.55) ✓, **left strip 1.90 mm**
(x −9.55 → −7.65).

### 2. The left mounting hole cannot survive

`Un2` is a Ø2.20 mm plated hole with **no annular ring** (pad 2.2, drill 2.2).
With edge clearance it needs ≈ 2.8 mm of strip. The left strip is 1.90 mm. It
does not fit at any Y position — this is a width problem, not a placement one.

Everything else on that strip is fine at 1.90 mm: U2 is 1.01 wide, C1 and C2 are
0.60 wide. They just shift outboard to a strip centre of x ≈ −8.60.

**Recommended resolution: one screw plus a housing feature.** Keep the
right-hand screw, and on the left let the housing capture the board edge with a
moulded lip or pocket instead of a fastener. One screw and one anti-rotation
feature is normal retention for a 19 mm part, it costs nothing in a printed
housing, and the housing is being redrawn anyway.

Alternatives considered and why they are worse:

- **Both screws on the right strip, stacked in Y.** Fits geometrically, but puts
  both fasteners on one side while the keyboard's pogo springs push the opposite
  edge up. Poor retention.
- **Drop to M1.4 (Ø1.5 hole) on the left.** 1.5 + 0.2 each side = 1.90 exactly.
  Zero margin into a printed plastic boss. Not trustworthy.
- **Edge scallop / half-hole on the left.** Works in 1.90 mm and JLCPCB supports
  it, but the screw head then only overlaps board on three sides.

### 3. Strip allocation after the shift

**Right strip — x 6.05 … 9.55, centre 7.80**

| Feature | y range | note |
|---|---|---|
| C4 | −8.20 … −5.40 | unchanged |
| C3 | −5.00 … −2.20 | unchanged |
| Screw `Un1` | −1.40 … +0.80 | moves from x 8.30 → **7.80** to centre it in the strip; 0.65 mm clear each side |
| **FPC connector** | **+1.60 … +6.60** | 5.00 mm long, land x 6.15 … 9.45 |
| spare | +6.60 … +8.55 | 1.95 mm |

**Left strip — x −9.55 … −7.65, centre −8.60**

| Feature | y range | note |
|---|---|---|
| C2 | −7.46 … −5.95 | shifts outboard ~1.0 mm in X |
| C1 | −5.56 … −4.05 | ” |
| U2 | −3.40 … −2.60 | ” |
| free | −1.10 … +8.55 | the old `Un2` hole is gone |

Everything fits. The old J2 pads (currently split 3-and-3 across both strips at
y 2.30 … 6.50) are removed entirely.

### 4. Consequences to budget for

- **Full re-route.** U1 moving 0.80 mm invalidates every trace to it. This is not
  a nudge — it is a re-layout of both strips.
- **Housing bosses move**, and one becomes a lip.
- **BOM/CPL rebuild**, with U1's CPL origin still on the **body centre**, not the
  pad-ring centre (they differ by 2.70 mm — see `JLCPCB DFM Report.md`).

---

## Separate finding: the housing STL does not match this board

Measured from `cad/pcb-v2/touchid_module_housing_final.stl` by ray-casting the
mesh, not by eye:

| | STL | current board |
|---|---|---|
| Interior cavity below the rim | ≈ 15 × 15 mm | needs 19.6 × 17.6 |
| Outer envelope | **22.11 × 23.29 × 7.16 mm** | slot budget ≈ 19 × 19 |
| Symmetry | asymmetric — an ear runs out to x = −12.34 | — |

Internal structure: outer wall from z = 0, a rim from **z = 5.16 to 7.16**, and a
clear aperture through the middle roughly x ∈ [−6, 6], y ∈ [−6, 6].

This is built around the older square 19.5 × 19.5 geometry that
`TouchID Module Design.md` already marks superseded. It needs redrawing
regardless of the connector work — which is precisely why moving the bosses
costs nothing extra right now.

> **Unresolved and worth settling before the housing is redrawn:** the board is
> 19.6 mm wide but `Mechanical and Housing.md` puts the whole module inside a
> ~19 × 19 mm slot. Those cannot both be true with walls of any thickness. The
> ~19 figure is flagged in that note as eyeballed; the 19.6 is caliper-measured.
> Re-measure the slot before committing wall thickness.

---

## Also worth doing while J2 is being reworked

The six existing Ø1.2 mm J2 pads carry **F.Paste**, so the stencil prints solder
domes on them on 1.5 mm pitch. Moot once they are replaced by a connector, but
if the pads are kept in any form, decide this deliberately.

---

## What this is waiting on

**The sensor.** Nothing above should be committed to copper until it is bought,
because the tail decides the part:

- **0.5 mm 6-pin FPC tail** → `C5213748` as planned. `GROW R502-B` on the
  shortlist in `Mechanical and Housing.md` is listed with exactly this, so this
  is the likely outcome.
- **Discrete flying wires** → an FPC-ZIF is the wrong family. Every wire-to-board
  option is deeper than 2.90 mm, which would push this back toward mounting the
  connector on the **underside** (there is a completely clear 19.0 × 6.35 mm band
  at y 2.20 … 8.55 on B.Cu) and measuring the keyboard slot for clearance above
  the pogo blocks.
- **Different pin count or order** → the land pattern and the strip allocation
  above both change.

## Related

- [[touchid/docs/build/JLCPCB DFM Report|JLCPCB DFM Report]] — land pattern audit, all parts
- [[touchid/docs/design/Mechanical and Housing|Mechanical and Housing]] — slot budget, sensor shortlist
- [[touchid/docs/design/TouchID Module Design|TouchID Module Design]] — board outline history
