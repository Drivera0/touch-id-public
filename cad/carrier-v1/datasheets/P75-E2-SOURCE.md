# P75-E2 — where every number comes from

> **Superseded by measurement, 2026-09-18.** Every length below is now measured
> with calipers (see "Measured" at the bottom). The drawing is kept as the
> cross-check it turned out to be — it agrees to within 0.04 mm — and as the
> only source for the three diameters.

**Source:** the dimensioned drawing in the listing the pins were actually bought
from — amazon.ca ASIN **B0D48VHRY4**, "100 Pcs Spring Test Probe Pogo Pin P75-E2
Dia 1.3mm Length 16.5mm", brand PURPLELILY, sold by Moorrish.
Drawing image: `https://m.media-amazon.com/images/I/311rMM-4C7L._AC_SL1500_.jpg`
Read 2026-09-18.

This is a **seller's drawing, not a manufacturer datasheet.** It is recorded
here because it is the best source that exists for these specific pins, and
because it is internally consistent — see the check below.

## Transcribed dimensions

| feature | value | used in |
|---|---|---|
| tip cone (Ø1.3 head) length | **1.5 mm** | `PIN_HEAD_L` |
| plunger shank, cone to barrel | **2.54 mm** | `PIN_SHANK_L` |
| barrel (gold tube) length | **12.5 mm** | `PIN_TUBE_L` — sets the seat bar |
| overall | **16.54 mm** | `PIN_L` |
| head diameter | **Ø1.3 mm** | too big for the Ø1.05 carrier hole, by design |
| plunger shank diameter | **Ø0.74 mm** | must never enter the hole |
| barrel diameter | **Ø1.02 mm** | 0.015 mm/side in the Ø1.05 hole |

**Consistency check:** 1.5 + 2.54 + 12.5 = **16.54**, exactly the stated overall.
A drawing whose chain closes to the millimetre is far more trustworthy than the
listing's own prose, which says 16.5 mm in the title and **16 mm** in the
description.

## What the listing does NOT give

* **stroke / travel** — `PIN_STROKE = 2.50` is still a generic P75-series figure
  with no source on this listing. It is what `verify_frame.py` uses to prove the
  DUT can never reach the carrier, so it matters.
* **spring force** — 100 g, same caveat. Only affects how hard you press.
* **tolerances** — none stated anywhere.

## The number that matters most

`PIN_TUBE_L`. The seat bar height is `CAR_TOP - PIN_TUBE_L + TUBE_PROUD`, so the
barrel length alone decides whether the barrel or the plunger ends up inside the
carrier's hole. Measure the gold section with calipers before printing.


---

## Measured — Dan, 2026-09-18, calipers

| what | measured | drawing said |
|---|---|---|
| gold barrel | **13.00 mm** | 12.5 |
| overall, relaxed | **17.00 mm** | 16.54 |
| overall, fully compressed | **14.50 mm** | — |

Everything else is arithmetic on those three:

| derived | value | drawing said |
|---|---|---|
| **stroke** = relaxed − compressed | **2.50 mm** | not on the listing at all |
| plunger exposed = relaxed − barrel | 4.00 mm | 4.04 |
| head cone = compressed − barrel | 1.50 mm | 1.5 |
| shank = plunger − head | 2.50 mm | 2.54 |

**The stroke was the important one.** It had no source anywhere — it was a
generic P75-series figure — and it is what proves the plunger runs out of travel
before the DUT can reach the carrier's copper. It is now measured.

The chain is also self-consistent in a way that validates it: the Ø0.74 shank
(2.50) is exactly the stroke (2.50), so at full compression the shank vanishes
into the barrel and only the 1.50 mm head cone is left outside. A plunger whose
shank were longer than its stroke would jam on the barrel's mouth instead of
bottoming internally. `gen_frame.py` and `verify_frame.py` both assert this.

## Barrel diameter — measured 2026-09-18

**Ø1.00 mm.** The drawing said Ø1.02.

Against the carrier's Ø1.05 hole that is **0.05 mm diametral, 0.025 mm per
side** — looser than the 0.015 the drawing implied, but it fits, which is what
the PCB order was waiting on. The hole stays at Ø1.05: tightening it toward the
pin would leave nothing for JLCPCB's own hole tolerance, and a hole that comes
back undersize is a board the pins will not go into at all.

The cost of the extra slop is in the tip-to-pad budget, where "barrel cocked in
the hole" is now the largest single term (0.141 mm of the 0.354 mm worst case).
`verify_frame.py` computes that budget rather than asserting it.

## Still not measured

* **Ø0.74 shank, Ø1.3 head.** Nothing depends on either.
* **spring force** (100 g). Only affects how hard the board has to be held.
* **the 18 AWG dowel wire**, assumed Ø1.024. Second largest term in the
  tip-to-pad budget. It is a consumable you cut yourself, so it blocks no
  order — but it is worth a caliper before you cut two 19.5 mm lengths.
