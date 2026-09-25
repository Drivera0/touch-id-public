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

## 2026-08-27 — footprints re-sourced from JLCPCB, and where JLCPCB is wrong

Fetched from `easyeda.com/api/products/<LCSC>/components` (1 unit = 10 mil).

| part | mine | JLCPCB | taken |
|---|---|---|---|
| **L1** C2849435 | 3.24 x **0.96** (0805 stand-in) | 3.256 x **2.20** | **JLCPCB** |
| **0402** C1525 | 1.56 x 0.55 (Samsung) | 1.34 x 0.54 | **JLCPCB** |
| **0603** C19666 | 2.40 x 0.85 (IPC nominal) | 2.20 x 0.90 | **JLCPCB** |
| **U2** C882746 | 3.90, pad 0.60 x 0.24 (TI) | 3.981, pad 0.665 x 0.28 | **TI — kept mine** |
| **U1** C5118826 | 10 x 11.5, pitch 1.1 | same | already agreed |

**L1 was simply wrong, and JLCPCB is not needed to prove it.** The DMBJ
PNLS252012 body is **2.0 mm wide**; a land 0.96 mm tall cannot hold it — the
part would overhang its own pads by 0.52 mm each side. JLC's 2.2 mm sits 0.1 mm
proud of the body, which is what a land pattern is. The part's own datasheet
dimension was in `PCB-V3-NOTES.md` the whole time.

**U2 is the opposite case.** JLC's land is *larger* than TI's: 0.665 x 0.280
against 0.60 x 0.24. At 0.5 mm pitch that closes the pad-to-pad gap from 0.26
to **0.22 mm** — more solder, more bridging risk. TI is the authority on its own
package and JLC's house library is tuned for their process, not for margin.
**Kept TI's.**

The lesson: neither source is automatically right. A vendor land pattern and a
fab's house library answer different questions. The tie-breaker is the part's
own body dimensions, and whichever number is conservative for the failure mode
that matters — overhang for L1, solder bridging for U2.

### Cost of getting it right

Correct footprints made the board **harder**, which is the honest outcome:
L1 went from 1.10 mm of courtyard to 2.34, forcing C5 out of the right column
(it moved beside BT1 on the left, where CBAT belongs anyway). Open connections
went 7 -> 9. The 0402 shrink gave back some room: **25 slots for 22 parts**,
the first real spare capacity this board has had.

## 2026-08-27 — two real bugs found by asking why LX was thin

### U2's land was 0.25 mm off its own centreline

```python
off = [(-2 + i) * pitch + pitch / 2 for i in range(5)]   # -0.75 .. +1.25
```

That is the **even**-count formula. The BQ25505 has **5 pads per side**, so the
row must be symmetric: `(i - 2) * pitch` = -1.0, -0.5, 0, +0.5, +1.0. As
written, every edge of the land sat **0.25 mm off the package centreline** and
the perimeter pads did not line up with the thermal pad. The part would have
been placed crooked on its own footprint.

Fixed. U2's perimeter pad field is now centred on (0, 0) with the thermal pad,
verified from the emitted board.

### LX wrapped 11 mm around three sides of the chip

U2's **LX is pin 20, on the TOP edge**. L1 was stacked *below* U2, so the
switching node ran from the top of the package, around the right-hand side, and
down to the inductor — about **11 mm** for a node that should be as small as
possible. On a boost converter LX is the highest-dv/dt net on the board and its
loop area sets the radiated noise and part of the efficiency.

Two changes: **L1 moved above U2**, and **L1 rotated 180 deg** so its LX
terminal faces down. Pad-to-pad is now **1.91 mm, essentially straight**
(U2.20 at x 5.81, L1.1 at x 5.78).

LX stays 0.20 mm wide and that is correct — the whole run is inside the
neck-down zone of both pads, and 0.40 copper cannot land on a 0.24 mm QFN pad
without a taper. 0.20 mm carries 0.74 A; this converter moves microamps to
milliamps. **For LX the number that matters is loop area, not width**, and
preflight check 10 now exempts nets shorter than twice the neck-down length
instead of flagging them forever.

Open connections went 8 -> 7.

### C7 out of the right column — 7 opens -> 5

With only L1 + U2 left in the right column it has **0.70 mm of gap to spend
instead of 0.25**, which is enough for a via lane above and below the chip.
C7 (0603, 1.04 mm tall) fits the 2.22 mm bottom strip, and the 0402 packer had
**3 spare slots** to give up — the first time this board has had any slack.

`check_escape` went 3 boxed-in -> **1**, and the remaining opens are no longer
concentrated on U2: they are spread across ROK3, C7, U1, U2 and U2, which is
what a board at its limit looks like rather than one with a structural fault.

## Bottom-face copper, and why TP9/TP10 stay (2026-08-27)

**Every one of the 25 bottom-side pads is bare copper, and the bottom face is
the outside of the assembled module** — `touchid_module_v5.py` is explicit that
"the PCB forms the bottom 1.2 of the assembled 8.36 stack". Nothing covers it.

That is 10 test points + J3 (SWD: SWDIO, SWCLK, RESET, VSTOR, GND) + the J4/J11
pogo pads, spread from x -7.97 to +6.03 across the face that seats into the
keyboard slot. Live rails down there include **VSTOR, VBAT and VIN_DC**.

Daniel confirmed the module **drops straight down** onto the pogo pins rather
than sliding in. That removes the failure I was most worried about: on a sliding
insertion the sprung pins sweep across the whole bottom face on the way in, and
J4.5 is chassis ground — a ground pin dragging over the VSTOR pad would short
the storage cap on every insertion. Straight-down means each pin only ever meets
its own pad.

**TP9 and TP10 (spare GND) were removed and then put back.** Two reasons:

1. Removing two pads shifted the 0402 assignment enough to break the routing:
   **0 open connections became 4** (R6/BL_FLAG, C6/SENSOR_3V3, and both of U2's
   VBAT and VSTOR pins), and the best recovery over several re-route strategies
   was 3. The placement that routes cleanly is not robust to small perturbations.
2. The premise was wrong anyway. I proposed removing them as clutter, but
   they are **GND** — the safest possible net to expose on that face. Shorting
   GND to the chassis is a non-event; it is VSTOR and VBAT that matter. Trading
   a fully-passing board for tidiness on the two least risky pads is a bad deal.

**Still worth knowing:** the exposed rails are a real if low-probability hazard
(conductive debris, a dropped module, a metal slot floor). If that ever needs
closing, the fix is to tent everything except J4/J11 in solder mask and accept
losing probe access — not to delete pads and re-route.

## Full sweep, 2026-08-28 — three more found in the same blind spot

The missing ground plane was not a one-off. It got through because **zones were
a category the gate could not see at all**, and once I looked there properly,
two more were sitting in the same place.

**1. The zones are not filled.** A zone in this file is an outline plus fill
settings; the copper itself lives in `(filled_polygon ...)` blocks that KiCad
computes. `check_connected` models the fill and reports "all nets connected"
from the outline alone — but **a plot taken from an unfilled board has no plane
on it**. That is the original bug again, one step further along.
→ **check 18** blocks until the fill is materialised. This is the one manual
step left: open in KiCad, `Edit > Fill All Zones` (B), **save**, re-run.

**2. Board thickness was never declared.** No `(stackup)` block at all, and
thickness is not visible to any 2D check because it is not in the copper.
housing v5 is built around a **1.20 mm** board ("the PCB forms the bottom 1.2 of
the assembled 8.36 stack") — and **KiCad and JLCPCB both default 4-layer to
1.60 mm.** Ordering the default gives a board 0.40 mm too thick for its own
housing. A stackup summing to exactly 1.200 mm is now emitted, ENIG specified.
→ **check 19** cross-checks the stackup total against the housing's
`pcb_t_ref`, the same way check 12 guards `mcu_center`.
> Copper weights are the standard JLC build (1 oz outer, 0.5 oz inner). The
> dielectric split is nominal and only makes the total come out right — JLC's
> actual prepreg/core split governs. **The total is the requirement, and it must
> still be chosen by hand on the order form.**

**3. Check 7 could not see a pour either.** It tested tracks and vias, and a
plane is neither — so a fill spilling into the antenna keep-out would have been
invisible, on the one region of this board whose emptiness is the whole point.
The keep-outs do set `copperpour=not_allowed` on all four layers (verified), but
"the setting is right" and "the copper is not there" are different claims.
→ check 7 now tests fill polygons per layer as well.

**Also fixed:** the three GND pads a human actually solders a wire to (BT1-2,
J2-6, J3-5) were connected **solid** into three copper planes. A plane that size
sinks heat faster than an iron delivers it — cold joints and lifted pads. They
now get thermal relief (`zone_connect 1`). J4-5 stays solid deliberately: it is
a pogo *contact*, never soldered, and wants the lowest resistance available.
The test points stay solid too — probe pads, never soldered.

**And the recurring one:** checks 17/18 first counted **6** copper zones where
there are **3**, because `\(zone(.*?)\n\t\)` mis-splits a filled zone. That is
the fourth time regex has lied about this file format. Both now go through
`sexp.py`.

### State

18 checks. **One blocker, and it is a step you have to take, not a defect:**
fill the zones in KiCad and save. Everything else passes — DRC clean,
all nets connected, placement identical to the generator.

## VBAT's "no 0.40 mm trunk" — measured, and deliberately not fixed

The warning asked the wrong question. Width is a proxy; what matters is the
volt drop at the current the net actually carries. Measured on the routed board:

| net | worst path | R | I peak | IR drop |
|---|---|---|---|---|
| **VBAT** | BT1.1 → U2.18 | **67.8 mΩ** | 210 mA | **14.2 mV** |
| VSTOR | TP2.1 → C10.1 | 59.5 mΩ | 210 mA | 12.5 mV |
| LX | L1.1 → U2.20 | 11.6 mΩ | 210 mA | 2.4 mV |
| VIN_DC | L1.2 → R2.2 | 4.2 mΩ | 3.3 mA | 0.01 mV |

210 mA is the **CP1254's own maximum pulse rating**, so it bounds anything the
board can draw. At that current the cell's own ~0.5 Ω ESR drops **105 mV** —
**7.4× more than the entire trace**. Widening VBAT to 0.40 mm would halve
67.8 mΩ and buy about 7 mV against a 105 mV drop that is inherent to the cell.
Thermally there is nothing to discuss either: 0.2 mm of 1 oz copper carries well
over an amp, and the peak here is 0.21 A.

**No board change. The trace is not, and cannot become, the limiting element.**

Check 10 is now an IR-drop check rather than a width check, with peak currents
taken from the design docs (sensor 25 mA / 200 mA·4 µs, nRF ~15 mA, harvest
1.1 mA/pin, cell 210 mA) and a 25 mV budget — roughly 8 % of the sensor rail's
300 mV margin.

> **It grades only the nets it can trace, and says so.** Its graph is
> endpoint-and-overlap based, while real copper connectivity is geometric: a
> track may cross a pad without ending on it, and VSTOR's copper reads as six
> disconnected components to a naive endpoint graph while being perfectly
> whole. Rather than ship a model that might one day report a flattering
> number for a net it cannot actually follow, the check stays silent where it
> has no evidence. **Connectivity is check 6's job, and check_connected models
> the geometry properly.**

## There is no BOM or CPL for this board — and the files that exist are POISON

`cad/exports/fingerprint module-BOM.csv` and `-CPL.csv` (19 Aug) describe a
**completely different, dead board**:

* `U1 = ESP32-C3-MINI-1-N4` — the retired architecture. U1 is now a Raytac
  MDBT50Q.
* `U2 = TPS7A2033` — on this board U2 is the **BQ25505 charger**; the LDOs are
  U3/U4. Same designators, different parts.
* 4 BOM lines and 6 placements, against ~30 parts that need placing.
* Coordinates around 92–108 mm — a different board origin entirely.

**Uploading them would place the wrong parts at the wrong coordinates.**
They should be deleted or moved to `cad/archive/`, not left next to the good
exports where they can be picked up by mistake.

### What JLCPCB actually needs for assembly (and what it does not)

It does **not** use 3D models. Placement is 2D:

| file | contents |
|---|---|
| **BOM** | designator → LCSC part number |
| **CPL** (pick-and-place) | designator, X, Y, **rotation**, top/bottom |

The machine takes a part from the feeder its LCSC number identifies and puts it
at X/Y with that rotation. JLC knows the part's real body from **their own
library, keyed by the LCSC number** — nothing in our files describes it. The
3D models in `cad/pcb-v3/3dmodels/` exist purely for our housing collision
check; the fab never sees them.

### Two things that will bite

1. **Rotation convention.** JLC's expected orientation for a package frequently
   differs from KiCad's footprint rotation, which is the classic way to get a
   whole reel placed 90° or 180° out. Every rotation must be checked against
   JLC's own part preview, not assumed.
2. **LCSC numbers exist for only a handful of parts** — U1 (C5118826), the 0402
   (C1525), 0603 (C19666), L1 (C2849435), and U2's package reference. **Every
   BOM line needs one**, and several resistor values here are unusual
   (6.04M, 6.98M, 4.53M, 7.15M, 1.33M) — they are unlikely to be JLC "basic"
   parts, which means extended-part fees or a substitution that changes the
   thresholds those dividers set.

> Note the divider values are not free to substitute: ROV1/ROV2 set the charge
> ceiling and ROK1/2/3 set the VBAT_OK window. Swapping to a nearest-available
> value moves those voltages — recompute with preflight check 15 before agreeing
> to any substitution.
