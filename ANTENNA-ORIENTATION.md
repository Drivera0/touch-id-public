---
title: Antenna orientation — the sign convention, resolved from the file
type: project
tags:
  - touchid
  - pcb
  - rf
updated: 2026-08-27
---

# Task C — which edge faces the spacebar

**Answer: board-local +Y is the spacebar edge. −Y is the rear, toward the screen.**

**`DESIGN-SPEC.md` §2's table is correct as printed.** The J4 pogo pads really are at
y −8.32 … −1.12. The extraction quoted in `NEXT-SESSION.md` that produced
+1.12 … +8.32 applied a sign flip that the file does not call for. §4 below says why
that mistake was easy to make, because one sentence in DESIGN-SPEC §1 invites it.

Reproduce any of this with `cad/pcb-v2/extract_pogo.py` (read-only).

---

## 1. What the file actually contains

`pcb-v2.kicad_pcb` has two footprints:

```
(footprint "touchid:touchid_board"        (at 148.5011 105.0036)      <- rotation 0
(footprint "Espressif:ESP32-C3-MINI-1"    (at 148.5011 105.0036 180)  <- rotation 180
```

All ten pogo pads live in `touchid_board`, which sits **at the origin with zero
rotation**. So a pad's footprint-local `(at x y)` *is* `global − origin` — no
rotation, no offset, no flip. Pad coordinates come straight out of the file:

| pad | net | x | y |
|---|---|---|---|
| J4-1 | | −7.200 | −7.220 |
| J4-2 | | −4.700 | −7.220 |
| J4-3 | | −7.200 | −4.720 |
| J4-4 | | −4.700 | −4.720 |
| **J4-5** | **GND** | **−7.200** | **−2.220** |
| J4-6 | | −4.700 | −2.220 |
| J11-1 | VBAT | 3.450 | −7.200 |
| J11-2 | VBAT | 5.950 | −7.200 |
| J11-3 | VBAT | 3.450 | −4.700 |
| J11-4 | | 5.950 | −4.700 |

Ø2.2 pads, so the copper bounding box is **x [−8.300, +7.050], y [−8.320, −1.120]** —
exactly DESIGN-SPEC §2's numbers.

The extractor paren-matches `(pad ...)` blocks rather than regex-scraping them, and
prints the count first: **95 pad blocks, 95 with coordinates, 10 round B.Cu pads of
Ø2.2**. That count is the guard against DESIGN-SPEC §7 trap 3 — a checker that has
gone blind still prints a confident summary, so the count has to be checked, not the
summary.

---

## 2. Why +Y is the spacebar — two independent routes

`Pin Test Procedure.md` fixes the physical convention. Looking straight **down** into
the slot with the module removed:

```
   REAR (toward screen)
   J4        J11
   1  2      1  2
   3  4      3  4
   5  6
   FRONT (toward spacebar)
```

Both the module's pads and the slot's pins are seen from the same side — from above —
so plan positions do not mirror between the two views. KiCad's top view is that same
view.

### Route 1 — block shape. Uses no pad names at all.

J4 has **three** rows, J11 has **two**, and the diagram shows both blocks flush at the
**rear**, with J4 alone carrying an extra row toward the **front**.

In the file:

| | rows (y) |
|---|---|
| J4 | −7.220, −4.720, **−2.220** |
| J11 | −7.200, −4.700 |

The two blocks share the −7.2 row and the −4.7 row. **J4's unshared row is the one at
−2.220**, the least negative. So the shared edge at −7.2 is the REAR and the direction
of J4's extra row is the FRONT.

→ **increasing y is toward the spacebar.**

### Route 2 — the ground pin. Uses a measured fact, not a drawing.

`Pin Test Procedure.md`: *"**J4-5** (confirmed ground) is the **bottom-left** pin of
the 6-pin block."* Bottom = front = spacebar; left = the J4 side.

**J4-5 is the only J4 pad in the file carrying a net, and that net is `GND`.** It sits
at (−7.200, −2.220): the most negative x in the block, and the least negative y.

→ −x is left, and **+y is toward the spacebar.** Same answer, arrived at from a
meter reading rather than from a sketch.

### Cross-check on handedness

J4 is the 6-pin block and the procedure puts it on the **LEFT**. In the file J4 is at
negative x and J11 at positive x. Consistent, so the x convention is ordinary: −x is
left when looking down at the installed module.

> Minor artifact, recorded and dismissed: J4's rows sit 0.020 mm further from the
> origin than J11's (−7.220 vs −7.200). Systematic, well under any tolerance that
> matters, almost certainly rounding in the original Altium import. It does not
> affect anything here.

---

## 3. The keep-out region this leaves

All pogo copper is confined to **y ≤ −1.120**. On a 19.30 mm square board
(y ∈ [−9.65, +9.65]) that leaves, free of pogo copper **on every layer**:

| | |
|---|---|
| Depth from the +Y board edge | **10.770 mm** (from +9.650 down to −1.120) |
| Width | the full **19.30 mm** |

For scale, pcb-v2's existing ESP32 keepout — read out of the file, not out of a note —
is a pair of zones on F.Cu **and** B.Cu at

```
local x [-6.655, +6.600]   y [+2.950, +9.300]
copperpour / tracks / vias / pads: not_allowed;  footprints: allowed
```

i.e. **13.255 wide × 6.350 deep**, sitting at the +Y edge with **4.070 mm** to spare
before the nearest pogo copper. That keepout has already been laid out successfully
once on this outline.

**The MDBT50Q is 10.5 mm wide against the ESP32's 13.2** — 2.7 mm narrower — so its
keep-out is very unlikely to be wider than the one that already fits, and the depth
budget is 10.77 mm against the 6.35 the ESP32 needed.

> [!warning] This is a bound, not the proof Task C asked for
> Task C wanted the MDBT50Q keep-out *shown* to fit. That needs its dimensions in mm,
> and those are **`PART-LIBRARY.md` §9 item 1 — still open**. Raytac's §2.3 is a
> drawing with no text layer. What is proved here is the *available envelope*
> (10.77 × 19.30) and the fact that a 6.35 × 13.26 keepout already fits in it. The
> final check has to wait for the real numbers.

### Also inside the free half — must be kept out of the keep-out

- **TP-DP / TP-DN / TP-IO9**, B.Cu, at (−2.00 / 0.00 / +2.00, **+1.30**), Ø1.8 →
  copper from y +0.40 to +2.20. These are v2 parts. Task D relocates the test points
  anyway; put the new ones at **negative y**, on the pogo side.
- **Mounting hole at (−8.10, +8.10)**, Ø1.30. It is in the +Y half. Keep it
  **non-plated with no annular copper**, or move the keep-out clear of it.

---

## 4. Where the confusion came from — fix this line in DESIGN-SPEC

DESIGN-SPEC §1 makes two claims that cannot both hold:

> "Board-local coordinates in this document are `global − origin`."
> "Board-local +Y is KiCad-up."

KiCad's file format has **Y increasing downward**. Under `global − origin`, a pad with
local y = −7.220 is at global y = 97.78, which is a *smaller* global y — **KiCad-up**.
So the pogo pads, at negative local y, are KiCad-**up**, and local **+Y is
KiCad-DOWN**. The second sentence is the wrong one.

Every table in DESIGN-SPEC follows the first sentence and is right. Anyone who trusts
the second sentence negates y and lands on +1.12 … +8.32 — which is precisely the
discrepancy NEXT-SESSION flagged.

**Corrective wording:** *"Board-local = `global − origin`, keeping KiCad's Y-down
convention. Board-local +Y is toward the spacebar; −Y is toward the screen."*

Verified against the keepout zones as a third witness: DESIGN-SPEC §2 lists the
antenna keepout at y [2.95, +9.30], and the file's zones read
`107.9536 .. 114.3036` global = **+2.950 .. +9.300** local under `global − origin`,
with no flip. Three independent objects — pogo pads, keepout zones, mounting-hole
diagonal — all agree on the unflipped frame.

---

## 5. What this means for the v3 layout

**pcb-v2's ESP32 antenna already points at the spacebar.** The keepout at
y +2.95…+9.30 is on the +Y edge, and +Y is the spacebar. Daniel's instruction and the
existing board agree, so Task E **preserves** the orientation rather than reversing it.
The module changes; the direction does not.

The MDBT50Q's 15.5 mm length must run along **y**, antenna end toward **+y**.

> [!danger] This collides with housing v5's cell ledges — Task E must resolve it
> Pushing the module to +y so the antenna reaches the spacebar edge puts the module
> body at roughly y −6.4 … +9.2. Housing v5's cell seat ledges are at
> **\|y\| 5.45 … 9.0, \|x\| ≤ 4.0, z 1.65 … 2.45**, and the module is 2.05 tall —
> so the ledge would land on the module.
>
> The fix is a rotation, not a redesign: **move the ledges to ±X**. The module is
> 10.5 wide (x ±5.25) and the cell rim reaches x ±6.05, so a ledge with its inner edge
> at \|x\| = 5.45 clears the module by the same 0.20 mm the ±Y version had. The
> collar arcs and the sensor-wire windows swap axes with it.
>
> Consequence to check when it is done: the wire windows would then be at ±Y, while
> **J2 sits at x = ±7.60** (y 2.90 / 4.40 / 5.90). The six sensor wires and the cell
> ledges would want the same corridor. Either J2 moves to ±Y in the v3 layout, or the
> ledges get notched. **Decide this before drawing pcb-v3**, and re-run
> `touchid_module_v5.py` with `mcu_center` set to whatever Task E chooses — the script
> re-runs every boolean check and will catch it if it does not clear.

## Related

- [[touchid/PART-LIBRARY|Part library]] — §9 item 1, the missing keep-out dimensions
- [[touchid/cad/scripts/HOUSING-V5-NOTES|Housing v5 notes]]
- [[touchid/Pin Test Procedure|Pin Test Procedure]] — the physical numbering convention
- [[touchid/DESIGN-SPEC|DESIGN-SPEC]] — §1 needs the wording fix in §4 above
