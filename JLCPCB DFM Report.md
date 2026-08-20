---
title: JLCPCB DFM Report — land pattern audit
type: project
tags:
  - touchid
  - hardware
  - jlcpcb
updated: 2026-08-20
---

# Land pattern audit — every footprint traced to a vendor source

Scope: every component on `cad/pcb-v2/pcb-v2.kicad_pcb`, checked against the
vendor drawing behind the JLCPCB part number actually being purchased.

**Order [order #] / Y6 is scrap** — it was built with a wrong U2 land pattern.
This document is no longer a hold request. It is the pre-order record for the
next order: what was wrong, what the vendor source says, and what `pcb-v2`
now contains.

| Field | Value |
|---|---|
| Superseded order | [order #] / Y6, customer order ID 12208316 |
| Board | 19.60 × 17.60 mm, 2 layer, 1.2 mm, ENIG, 5 pcs + SMT assembly |
| Board coordinate frame (Gerber) | X 90.2 – 109.8 mm, Y 0.0 – 17.6 mm (centre 100.0, 8.8) |
| KiCad ↔ Gerber transform | `kicad_x = gerber_x + 48.5011`, `kicad_y = 113.8036 − gerber_y` (Y mirrored) |

---

## Summary

| Ref | Part | JLCPCB # | Vendor source | Y6 as built | pcb-v2 now |
|---|---|---|---|---|---|
| U1 | ESP32-C3-MINI-1-N4 | C2838502 | Espressif datasheet v2.2 Fig 11-1 / official `ESP32-C3-MINI-1.kicad_mod` | **correct** | correct |
| U2 | TPS7A2033DQNR | C46459900 | TI DQN0004A 4215302/E | **defective** | corrected |
| C1, C2 | 1 µF 25 V X5R 0402 | C52923 | Samsung MLCC catalog, 1005 ±0.10 | in spec | unchanged |
| C3, C4 | 47 µF 6.3 V X5R 0805 | C16780 | Samsung MLCC catalog, 2012 ±0.20 | out of spec | corrected |

Two things worth stating plainly, because both cost time on this project:

1. **JLCPCB AutoCAM passing means the board is manufacturable, not that the
   parts fit.** Y6 passed AutoCAM with result 1 and was still scrap.
2. **A generator script is not evidence of what shipped.** An earlier revision
   of this document accused U1's footprint of being defective, based on reading
   `build_board.py`. Parsing the artwork that was actually manufactured proved
   U1 was correct. Read the Gerber, not the code.

---

## 1. U2 — TPS7A2033DQNR, X2SON-4 (DQN), 1.0 × 1.0 mm

LCSC/JLCPCB **C46459900**, JLCPCB "Extended" tier. Component centre in the
Gerber frame: X 92.400, Y 11.800, rotation 0.

Source: Texas Instruments package drawing **DQN0004A, 4215302/E (12/2016)**,
"LAND PATTERN EXAMPLE" sheet. Independently confirmed against the KiCad
official library part `Package_SON.pretty/Texas_X2SON-4_1x1mm_P0.65mm.kicad_mod`,
whose geometry matches the TI drawing.

### The trap in TI's drawing

The land pattern sheet carries a **SOLDER MASK DEFINED** detail with "0.05 MIN
ALL AROUND". That means its dimensions — `4X (0.36)`, `4X (0.21)`, `(⌀0.48)` —
are **solder mask openings, not copper**. The copper underneath is 0.05 mm
larger on every side. Reading those numbers as copper silently shrinks every
pad by 0.10 mm.

### Required geometry

| Feature | Required |
|---|---|
| Pad centres | **(±0.43, ±0.325)** from component centre |
| Pitch | **0.86 mm** in X (centre-to-centre), **0.65 mm** in Y |
| Pad copper | **0.46 (X) × 0.31 (Y)**, inner corner chamfered ~0.21 mm at 45° |
| Solder mask opening | **0.36 × 0.21** — solder-mask defined, 0.05 mm min all around |
| Thermal pad (pin 5) copper | **0.58 × 0.58 square rotated 45°** (diamond) |
| Thermal mask opening | **0.48** diamond (mask margin −0.05) |
| Thermal paste aperture | **0.45** diamond (paste margin −0.065), ≈88 % coverage per TI's stencil sheet |
| Exposed-metal clearance | 0.22 mm typ between thermal and signal pads |

The chamfer is not cosmetic. Full 0.46 mm pads and a 0.58 mm diamond **overlap**
without it — the chamfer is what creates the 0.22 mm clearance.

### What Y6 shipped with

| Feature | As built |
|---|---|
| Signal pads | 4 × **0.30 × 0.30** roundrect |
| Pad centres | **(±0.52, ±0.52)** |
| Thermal pad | **0.55 × 0.55**, **not rotated** |

Roughly 15–25 % of each terminal over copper, contacting along a strip about
0.1 mm wide. On a 1 × 1 mm leadless package that is open joints or a part that
reflows off the land.

### What pcb-v2 contains now

Copper 0.46 × 0.31 at (±0.43, ±0.325), inner corners chamfered; mask 0.36 × 0.21;
thermal 0.58 diamond with a 0.48 mask opening and 0.45 paste aperture. Matches
the TI drawing.

> An intermediate fix (2026-08-19) used TI's mask-opening numbers as copper —
> 0.36 × 0.30 pads at ±0.421 and a 0.48 thermal, then shrank the mask a further
> 0.05, leaving only 0.26 × 0.20 of wetted copper per pad, **31 % less than TI
> specifies**. That is now replaced.

### Pin assignment — preserved through the fix

TI SBVS338H, DQN 4-pin, **top view**. Not the SOT-23-5 (DBV) order.

| Pin | Function | Net | Position from centre |
|---|---|---|---|
| 1 | OUT | +3V3 | (−0.43, −0.325) |
| 2 | GND | GND | (−0.43, +0.325) |
| 3 | EN | VBAT | (+0.43, +0.325) |
| 4 | IN | VBAT | (+0.43, −0.325) |
| 5 | Thermal | GND | (0, 0) |

---

## 2. U1 — ESP32-C3-MINI-1-N4

LCSC/JLCPCB **C2838502**. Gerber centre X 100.000, Y 8.800, rotation 180.
Module body 13.2 × 16.6 mm.

**U1's land pattern was never the problem.** Parsing the Y6 artwork's apertures
proves it: 26 × `R,0.4×0.8` + 22 × `R,0.8×0.4` = 48 perimeter pads on 0.8 mm
pitch, plus 9 thermal and 4 × 0.7 mm corner pads = 61 pads, already rotated 180°
with the antenna away from the pogo pads. That is Espressif's published pattern.

### The one real defect — introduced by the Altium → KiCad import

Espressif's footprint gives pin 49 (the module ground pad) as a **3 × 3 grid**:
eight 1.45 mm squares plus, at the corner slot, a 1.45 mm square with one corner
chamfered. In the Y6 Gerber that chamfered shape is the file's single `G36`
region, present in **GTL, GTS and GTP** at the correct slot — copper, mask and
paste all correct.

The KiCad import split that custom pad in two:

- a plain **0.8 × 0.8** rect at the correct slot, and
- the 1.45 mm chamfered polygon **offset by exactly (1.45, 1.45)**, on **F.Cu
  only** — no mask opening, no paste.

Net effect: **1.28 mm² of solderable area missing** from that corner of the
module ground pad (67 % of that pad), and a 1.92 mm² copper island buried under
solder mask doing nothing. Total mask-and-paste area at the thermal grid fell
from 18.7425 mm² to 17.4600 mm².

All nine pads are GND, so there was no short and no electrical fault — which is
exactly why it survived every clearance and connectivity check.

> Total-area comparisons hide this. Counting all copper gave 18.7069 mm² against
> the ordered 18.7425 mm² — a 0.2 % difference that looks like rounding. The
> copper was redistributed, not equivalent.

**Fixed 2026-08-20.** Pad 49 is rebuilt as a single custom pad at
(−1.97501, 0.725) with Espressif's chamfer polygon on F.Cu + F.Mask + F.Paste;
the detached island is deleted. Verified: the polygon's global bounding box is
now x [149.7511, 151.2011], y [103.5536, 105.0036] with the +x/+y corner cut —
byte-identical in position and orientation to the Y6 `G36` region.

### Placement origin — verified correct

U1's footprint origin sits at the **body centre**, not the pad-ring centre. The
F.Fab outline is 13.2 × 16.6 centred on (0, 0), while the pad ring centres on
y = +2.70 because the antenna end carries no pads. The CPL uses the body centre,
which is what JLCPCB wants. No change needed — but the two differ by 2.70 mm, so
do not "correct" this.

---

## 3. C1, C2 — 1 µF 25 V X5R 0402

LCSC/JLCPCB **C52923** = Samsung **CL05A105KA5NQNC**, ±10 %, JLCPCB Basic.
Body 1.00 ± 0.10 × 0.50 ± 0.10 × 0.50 ± 0.10 mm, terminal band 0.25 ± 0.10 mm.

| Dimension | Samsung 1005, ±0.10 tol row | pcb-v2 | |
|---|---|---|---|
| Gap between pads | 0.38 – 0.46 | **0.41** | ok |
| Pad length | 0.50 – 0.58 | **0.55** | ok |
| Pad width | 0.56 – 0.64 | **0.60** | ok |
| Total span | 1.38 – 1.62 | **1.51** | ok |

All four in range. No change made.

---

## 4. C3, C4 — 47 µF 6.3 V X5R 0805

LCSC/JLCPCB **C16780** = Samsung **CL21A476MQYNNNE**, ±20 %, JLCPCB Basic.
Body 2.00 ± 0.20 × 1.25 ± 0.20 × **1.25 ± 0.20** mm, terminal band 0.50 +0.20/−0.30 mm.

Note the height: this is a **1.25 mm tall** 0805, not the common 0.85 mm part.
That belongs in the housing clearance check.

| Dimension | Samsung 2012, ±0.20 tol row | Y6 as built | | pcb-v2 now |
|---|---|---|---|---|
| Gap between pads | 0.83 – 0.93 | 1.10 | **+0.17 over** | **0.88** |
| Pad length | 0.91 – 1.01 | 0.90 | **0.01 under** | **0.96** |
| Pad width | 1.35 – 1.45 | 1.25 | **0.10 under** | **1.40** |
| Total span | 2.65 – 2.95 | 2.90 | ok | **2.80** |

The pad width mattered most: at 1.25 mm the land was exactly as wide as the
capacitor body, so with the body's +0.20 mm tolerance the part could overhang
its own pad. Samsung wants the land wider than the body so a fillet forms on
each side and the part self-centres in reflow.

> An earlier note described this land as "0.51 mm short in the toe direction".
> That was wrong — the total span was inside Samsung's range the whole time. The
> real deviations were the gap and the pad width.

Fixing this moved the pad edges outward, which forced the GND return run between
C3 and C4 to shift 0.15 mm further from the board centre. Clearance to C3-1 went
from 0.056 mm to 0.206 mm.

---

## 5. Open, not fixed

- **One +3V3 / VBAT track pair at exactly 0.1270 mm**, JLCPCB's stated minimum.
  Zero margin. Passed on Y6 as well.
- **J2's six Ø1.2 mm pads carry F.Paste** and will get stencil apertures. They
  are hand-soldered wire pads for the fingerprint sensor pigtail, so nothing is
  placed on them — the paste just reflows into six domes on 1.5 mm pitch
  (0.3 mm gaps). Decide whether to strip F.Paste before plotting.
- **The fingerprint sensor is still not sourced.** J2's pinout (3V3, GND, TX,
  RX, INT, VT) is provisional and a different sensor could change the board.
- **The board file uses `(net "NAME")` in pads with no net declaration block.**
  That is not KiCad's schema, which expects an integer ordinal. Confirm KiCad
  and `kicad-cli` will actually open and plot this file before assuming a
  Gerber export will succeed.

---

## 6. Verified unchanged from Y6

From the CAM output in `[order #]_y6` — no change needed:

- Board profile 19.600 × 17.600 mm from the GKO layer, area 341.3 mm², 1 design
- Drill: 15 × Ø0.30 + 2 × Ø2.20, all plated; mounting holes at X 91.7 / 108.3, Y 8.8
- 2 layers, 1.2 mm, 1 oz outer copper, green mask, white silk, ENIG, vias tented
- No impedance control, no countersunk holes
- Top and bottom silkscreen content and orientation
- Auto-panelisation to 71.6 × 71.6 mm with rails and fiducials

---

## References

- TI package drawing DQN0004A 4215302/E — https://www.ti.com/lit/ml/qfnd355c/qfnd355c.pdf
- TPS7A20 datasheet (SBVS338H) — https://www.ti.com/lit/ds/symlink/tps7a20.pdf
- JLCPCB part page C46459900 — https://jlcpcb.com/partdetail/C46459900
- KiCad official footprint `Texas_X2SON-4_1x1mm_P0.65mm` — https://github.com/KiCad/kicad-footprints/blob/master/Package_SON.pretty/Texas_X2SON-4_1x1mm_P0.65mm.kicad_mod
- ESP32-C3-MINI-1 datasheet — https://documentation.espressif.com/esp32-c3-mini-1_datasheet_en.html
- Samsung MLCC catalog (land dimensions table) — https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/7133/MLCC.pdf
- JLCPCB part page C52923 — https://jlcpcb.com/partdetail/C52923
- JLCPCB part page C16780 — https://jlcpcb.com/partdetail/C16780
