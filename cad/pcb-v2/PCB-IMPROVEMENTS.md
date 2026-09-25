---
title: PCB improvement plan — square outline, corner holes, one flex
type: project
tags:
  - touchid
  - hardware
  - pcb
updated: 2026-08-20
---

> [!done] APPLIED 2026-08-20 — the board is now ready for Altium
>
> **The file could not be opened by anything.** `pcb-v2.kicad_pcb` declared
> `generator "pcbnew" 10.0` but had **zero top-level `(net ...)` declarations**,
> and every pad, track and via carried `(net "NAME")` with no ordinal. That is
> not KiCad's schema, so pcbnew would refuse it — which is why DRC had never
> been run and the Gerbers never plotted. Fixed: 10 declarations inserted,
> 271 references rewritten (pads → `(net <n> "NAME")`, tracks/vias → `(net <n>)`).
>
> **The checkers went blind the moment the schema was corrected** —
> `check_board` reported `tracks 0` and every net as `None`, while still
> printing a confident summary. All three scripts now expand bare ordinals
> before matching. This is the same failure mode the handoff warns about.
>
> Applied since:
> - Outline → **19.30 × 19.30, R2.0** (verified extent, 8 Edge.Cuts primitives)
> - Mounting holes → **Ø1.30 at (+8.10, −8.10) and (−8.10, +8.10)** — diagonal
> - **C3 +1.05 mm, C4 +1.20 mm in Y** to clear the new corner hole
> - 16 board-edge keepouts deleted (Altium enforces edge clearance by rule);
>   the 2 antenna keepouts kept and extended to y = +9.30
> - `B.Paste` removed from 13 bottom-side pads
> - 12 segments ripped (11 on the moved pads, 1 orphan GND run)
> - Stale `pcb-v2.PcbDoc`, `.PrjPcb` and `.PcbDoc.LOG` **deleted** — git keeps them
>
> State: 95 pads, 175 tracks, 18 vias, 2 zones, parses clean, one sub-0.127 pair
> (the known 0.1270). **Exactly 4 pads are unrouted — C3-1, C3-2, C4-1, C4-2** —
> which is what the autorouter is for. No orphan copper.
>
> ### Importing into Altium
> Do **not** reopen the old `.PcbDoc`; it is gone and it was stale. Use
> **File → Import → KiCad** (AD 26.9.1 has it) on `pcb-v2.kicad_pcb`. Verify
> after import that nets and footprints came across, not just copper — check
> the net count is 9 and that U1 still has 61 pads. Then autoroute the 4
> unrouted pads and run DRC.
>
> Still not done: the +3V3/VBAT pair at exactly 0.1270 mm, and J2 is still six
> hand-solder pads split across both strips.

# PCB improvements for the v4 housing

Scope: `cad/pcb-v2/` only. Driven by the new enclosure
([[touchid/docs/design/Module Mechanical v3|Module Mechanical v4]]), which allows a bigger,
square board.

## What is already good — don't "fix" it

Checked before proposing anything:

- **18 keepout zones, zero violations.** Tracks, vias and pads all respect them,
  including the ESP32 antenna keepout at x [−6.66, 6.60], y [2.95, 8.42].
- All nets single-island; one sub-0.127 mm pair (the +3V3/VBAT one).
- Land patterns all now trace to vendor drawings — see
  [[touchid/docs/build/JLCPCB DFM Report|JLCPCB DFM Report]].

I expected to find J2 sitting in the antenna keepout. **It isn't** — J2's pads
are at |x| = 7.6 and the keepout only spans |x| < 6.66. They are immediately
alongside it, which is still worth moving away from, but it is not a violation.

---

## 1. Square the outline — 19.60 × 17.60 → 19.30 × 19.30, R2.0

| | Current | Proposed |
|---|---|---|
| Outline | 19.60 × 17.60 | **19.30 square** |
| Area | 341.51 mm² | **369.04 mm²** (+8.1%) |

Gives up 0.30 mm in X to gain 1.70 mm in Y — and Y is the starved axis, because
U1's body is 16.6 mm of the 17.6 mm board. The surplus lands at **+Y, the
antenna end**, which is exactly where an ESP32 module wants clearance.

## 2. Mounting holes — the biggest single gain

Ø2.20 at (±8.3, 0) → **Ø1.30 at the corners**, matching the v4 housing's M1.2
bosses at (±8.10, ±8.10).

The old holes sit at x [7.2, 9.4] and [−9.4, −7.2], y [−1.1, 1.1] — dead in the
middle of **both** side strips, cutting each one in half lengthwise. Moving them
to the corners unblocks the entire length of both strips. Nothing else on this
board recovers as much useful area for as little effort.

## 3. One flex instead of six wires — the Apple move

Replace J2's six Ø1.2 mm hand-solder pads with a single **0.5 mm FPC ZIF**
(`C5213748`, 5.00 × 2.90 × 1.00 mm, 3.30 mm land).

| | J2 today | FPC connector |
|---|---|---|
| Board width consumed | **16.40 mm**, across both strips | **3.30 mm**, one strip |
| Assembly | hand-soldered, six wires | reflowed, plug-in |
| Height | flat | 1.00 mm |

What "Apple thin cable" actually buys here is not thinness for its own sake —
it's that **one flex replaces six wires and one fold replaces six routes**. The
1.00 mm connector height matters more than it looks: a vertical top-entry ZIF
would be 4.40 mm closed and 5.65 with the latch open, which eats the sensor's
headroom. A 1.00 mm back-flip part leaves the tail free to fold once, flat,
beside the sensor.

Put it at **negative Y** in the strip so the flex runs away from the antenna
rather than past it.

## 4. Net effect

| | Current | Proposed |
|---|---|---|
| Top-side free area | 100.87 mm² | **128.33 mm²** |
| Widest usable side strip | **3.20 mm** | **5.20 mm** |

## 5. Smaller fixes worth doing in the same pass

- **Remove `B.Paste` from J4, J11 and the three test points.** The bottom face
  is the pogo contact plane; solder paste there reflows into domes and wrecks
  contact flatness. JLCPCB probably won't cut a bottom stencil today (no bottom
  parts in the CPL), so this is latent rather than live — but it is wrong in the
  file and bites the moment a bottom-side part is added.
- **Open the 0.1270 mm +3V3/VBAT pair.** It sits at exactly JLCPCB's stated
  minimum with zero margin. With U1 moving anyway there is no reason to keep it.
- **Extend the antenna keepout into the new +Y space**, and consider a board
  cutout under the antenna now that there is room for one.
- **Widen the 11 segments still at 0.15 mm** where the new U2 land allows.

---

## What this costs — read before starting

**U1 has to move −1.05 mm in X for any of this to work, and that invalidates
every trace to it.** With U1 centred the strip is 3.05 mm before clearances,
and the connector land needs 3.30 — it does not fit on a square board either
unless the module shifts.

So this is a **re-layout, not an edit**. 187 segments, 18 vias and 18 keepout
zones all move. I have deliberately not hand-patched `pcb-v2.kicad_pcb` for
this: partially editing it would leave a file that is neither the verified old
board nor the new one, which is exactly the ambiguity that has cost this project
time twice already.

Order of work when you do start:

1. New Edge.Cuts at 19.30 square, R2.0
2. Move the corner keepouts to match the new outline
3. Reposition U1 to x = −1.05 (body x [−7.65, 5.55])
4. Replace the two Ø2.2 holes with Ø1.3 at (±8.10, ±8.10)
5. Delete J2's six pads; place the FPC land in the +X strip at negative Y
6. Re-route, then `sexp_check` → `check_board` → `check_connect`
7. KiCad DRC, plot, and independently verify the plotted Gerbers

Steps 6 and 7 are the ones that were skipped before the scrapped order.

## Still blocking

The sensor is not sourced. If it turns out to have discrete flying wires rather
than a 0.5 mm flex tail, item 3 changes completely — see
[[touchid/docs/design/Sensor Connector Plan|Sensor Connector Plan]].
