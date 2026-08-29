---
title: PCM on the board — MC3651DF1AAM
type: project
updated: 2026-08-29
---

# The PCM moves onto the PCB

**Decided 2026-08-29.** The cell will be a plain bare cell with factory leads;
the protection lives on the board. This is what unblocks cell sourcing — a
bare wired 1254 is an ordinary retail product, a protected one is not.

**Chosen: Mitsumi MC3651DF1AAM** — JLCPCB **`C6989585`**, XDFN-4-EP.

## Why this one — ranked against the alternatives

| # | part | over-current trip | Iq | area (IC only) | verdict |
|---|---|---|---|---|---|
| **1** | **MC3651DF1AAM** | **0.315 A = 2.2×** cell rating | 3.0 typ / 4.5 max µA | 3.56 mm² | **only one that protects the cell** |
| 2 | ALLPOWER AP6683 | 0.9 A = 6.4× | **0.7 µA** | **1.00 mm²** | smallest, but typicals-only, obscure vendor |
| 3 | ABLIC S-82A1A + FET + R | settable ±3 mV | 2.0 / 4.0 µA | 8.02 mm² | exact trip, but 3 parts and 0 stock |
| 4 | Diodes AP9211 | 2.2 A = 15.7× | 3.0 / 4.5 µA | 6.00 mm² | **OBSOLETE — waiting won't help** |

The cell is rated **140 mA continuous**. A 0.9 A trip protects the wiring, not
the cell. At 0.315 A the protection engages while the cell is still
recoverable. Mitsumi (Minebea) also publish **guaranteed maxima**, where the
AP6683 gives typicals "guaranteed by design, not tested in production" — for a
part whose whole job is working after everything else has failed, that matters.

**Note VARTA's own recommendation, the AP9211, ranks last**: 15.7× trip, six
times the area, and Digi-Key list it obsolete.

## Confirmed specifications (Mitsumi datasheet, Digi-Key mirror)

| | |
|---|---|
| over-charge detect / release | **4.280 V** / 4.180 V |
| over-discharge detect / release | **2.700 V** / 2.700 V |
| discharge over-current | 0.020 V detect → **0.315 A limit**, 32 ms delay |
| charge over-current | −0.0250 V → 0.390 A, 8.5 ms |
| short detect | 0.190 V, 0.750 ms |
| current consumption | **3.0 µA typ / 4.5 µA max**; standby 0.025 µA (latch on) |
| FET Rss(on) | 65 mΩ typ @ 3.5 V |
| operating voltage | 1.5–5.5 V |
| 0 V battery charge | **Prohibition** |
| package | PLP-4E, **1.25 × 2.85 × 0.50 max** |

Against this design: `VBAT_OV` worst case **3.955 V** sits **325 mV** below the
4.280 V trip (preflight check 15 wants ≥150). `VBAT_OK` drops the load at
3.12 V, so the board acts first and the PCM at 2.700 V is a true backstop —
the correct order. Energy cost **0.266 mWh/day = 6.7 %** of the 4.0 mWh/day
budget.

## Availability — Digi-Key beats JLC for this part

**Digi-Key CA `2508-MC3651DF1AAMCT-ND` (Cut Tape) — Part Status ACTIVE,
In-Stock 2,485, US$1.33 at quantity ONE.** Cut tape means you can buy a single
piece. Manufacturer lead time 12 weeks for restock, MSL 1.

That is materially better than JLC: stock 0, minimum 5, C$12.72 pre-order
(unit C$2.54). **So consign it from Digi-Key**, exactly like the BLE module.

**A CAD model exists.** Digi-Key's EDA/CAD Models page for this part
(`digikey.ca/en/models/13684190?tab=ultralibrarian`) carries an **Ultra
Librarian** model with symbol and footprint. Downloading needs a Digi-Key
account and acceptance of their model download agreement, so that is the
user's action, not mine — but it removes the need to derive a land pattern at
all, and an Ultra Librarian footprint is a far safer starting point than
anything I would draw from the package outline.

## Old availability note (JLC)

**JLCPCB `C6989585` — stock 0, minimum 5, pre-order $9.19 for 5**
(unit $1.8376). Pre-orderable exactly like U1. Digi-Key CA also lists
MC3651DF1AAM as **Active** with 2,485 in stock at C$2.11, so consignment is the
fallback. All 16 MC3651 variants are in JLC's library; all read 0 today.

## CORRECTION — it is not a one-part solution

I described integrated-FET parts as "one component". **The MC3651's
application circuit needs three more:**

| part | value | why |
|---|---|---|
| **R2** | **2.7 kΩ** | V− to S2. **Functional, not optional** — it appears in the test conditions for every over-current spec |
| R1 | 330 Ω (470 max) | VDD series, voltage-fluctuation and ESD protection |
| C1 | 0.1 µF | voltage fluctuation |

So the real board cost is roughly **5.7 mm²** of parts (3.56 + three 0402s at
0.72 each), not the 2.56 mm² I first estimated. The board has 55.52 mm² free
but fragmented into gaps under 0.9 mm, so this is still a re-place job — just a
bigger one than stated.

> [!warning] **Pin "D" — the exposed pad — MUST BE ELECTRICALLY OPEN.**
> The datasheet is explicit: *"Drain terminal of discharge and charge MOS-FET.
> Drain terminal must be open electrically."* This is unusual — most exposed
> pads are grounded or thermally tied. Grounding this one shorts the FET drains.
> **Do not let a footprint or an autorouter connect it.**

## Pinout

| pin | symbol | connect to |
|---|---|---|
| 1 | **S1** | cell **negative** terminal |
| 2 | **VDD** | cell **positive**, through R1 |
| 3 | **V−** | to S2 through R2 |
| 4 | **S2** | system negative (charger/load negative) |
| — | **D** | **open — do not connect** |

The PCM sits in the **negative** path: cell− → S1 … S2 → board GND. Cell+ goes
straight through. So `BT1` pin 2 stops being GND and becomes a new net
(`CELL_NEG`), with the PCM's S2 becoming board GND.

## BLOCKED — the land pattern

> **RESOLVED 2026-08-29 — I was wrong that there is no bottom view.** I said
> page 3 "ends after the Side View". It does not; my browser screenshot was
> clipped. The user supplied the PDF, and rendered locally at 600 dpi the page
> carries a **full dimensioned Bottom View**. Lesson repeated: a screenshot of
> a PDF viewer is not the document.

## PLP-4E terminal geometry — read from the Mitsumi drawing

Rendered from `datasheets/MC3651_SeriesSpecifications.pdf` page 3; the image is
archived as `datasheets/MC3651-PLP-4E-bottom-view.png`.

**Controlled (toleranced):**

| | |
|---|---|
| terminal height | **0.20 ±0.05** |
| wide terminal width | **0.65 ±0.05** |
| small terminal width | **0.20 ±0.05** |
| terminal spacing | **0.725 BASIC** (boxed) |
| corner chamfer | **C0.05** — this is the **pin 1 indicator** |
| positional tolerance | ⌖ 0.05 (M) |

**Reference only — in parentheses on the drawing, so NOT controlled:**
D centre pad **(1.15) × (1.80)**; edge offsets (0.075), (0.25), (0.05).

Body **1.25 ±0.05 × 2.85 ±0.05 × 0.50 max**.

**Layout:** four terminals in two rows — one **wide (0.65)** and one **small
(0.20)** per row — plus the large centre **D** pad. The 0.725 reading is
self-consistent: wide-pad centre 0.375 from the left edge, small-pad centre at
1.100, whose far edge lands 0.050 from the right edge, matching the drawing's
(0.05) edge offset exactly.

> **Pin numbering is given in the TOP view** (1 top-left, 4 top-right,
> 2 bottom-left, 3 bottom-right). The drawing above is the **BOTTOM** view, so
> it is mirrored left-to-right. **Get this wrong and the part is reversed** —
> exactly the failure mode that hit the sensor pinout once already.

## What still has to happen

This is the **package** outline, not a vendor **land pattern** — Mitsumi
publish no recommended land. Deriving one per **IPC-7351** for a no-lead
package is standard, defensible practice (terminal size plus a small toe
extension, no side extension), but it is a derivation and should be labelled as
one. The alternative is to ask Mitsumi for their recommended land.

**Do not connect the D pad.** See the warning above.

### Also learned while checking

* **EasyEDA has no library for `C6989585`.** JLC's own page says so outright:
  *"Currently, there is no library. You can request free CAD model design at
  EasyEDA."* So the footprint would have to be drawn either way.
* **The AP6683 (`C2849565`) does have one** — symbol and footprint both render
  on its JLC page — and it is **103,743 in stock, minimum 1, C$0.0465**, versus
  the MC3651's stock 0 / minimum 5 / C$12.72 pre-order. That is a real
  practical advantage the earlier ranking did not weigh.
* **Unresolved conflict on the AP6683:** JLC's attribute table lists
  *"Charging Saturation Voltage 4.1 V"* and *"Supply Current (Iq) 100 nA"*,
  against the 4.30 V / 0.7 µA from earlier research. If the over-charge trip
  really is 4.1 V, the margin over `VBAT_OV` (3.955 V worst case) is **145 mV**
  — just under preflight's 150 mV guard. **Resolve before choosing it.**

What IS confirmed from the drawing:

* body **1.25 ±0.05 × 2.85 ±0.05 × 0.50 max**
* pin layout, TOP view: **1 top-left, 4 top-right, 2 bottom-left, 3
  bottom-right**, with **D as the large centre pad**
* the schematic pin sketch is *not* dimensioned, so pad sizes cannot be scaled
  off it

EasyEDA's public API also 404s for `C6989585`, and its `/svgs` endpoint returns
*"schematic not drawn"* — so JLC's "symbol and footprint available in EasyEDA"
line may be generic text rather than a promise about this part.

**The standing rule is never to invent a land pattern**, so the placement stops
here until one of these produces it:

1. **Open EasyEDA (free), place `C6989585`, export the footprint.** Five
   minutes, and it is authoritative — it is what JLC will assemble to.
2. Render the Mitsumi package drawing (page 3 of the Digi-Key mirror) at high
   DPI and read the dimensions by eye.
3. Ask Mitsumi for the recommended land pattern.

Route 1 is the fastest and the most trustworthy.

---

## Placement feasibility — measured 2026-08-29

**U5 does not fit anywhere on the current board.** Scanning every 0.1 mm
position against pads, component bodies, all F.Cu tracks and vias:

| | placements |
|---|---|
| U5 courtyard 3.41 × 1.81 | **0** |
| U5 rotated 1.81 × 3.41 | **0** |
| one 0402 (R8/R9/C14) | 57 |
| one 0402 rotated | 103 |

So the three passives have homes; **the IC does not**. Dropping the PCM in is
not possible — existing parts have to move and the board has to be re-routed.

That makes this a **re-layout**, not an insertion. The 55.52 mm² of free area
is real but fragmented into slivers under 0.9 mm, and the PCM needs one
contiguous 3.41 × 1.81 with via access.

**Options, in increasing disruption:**

1. **Re-place locally** — shift the 0402s around the least-congested edge to
   consolidate a 3.4 × 1.8 pocket, then re-route. Cheapest, and the free area
   exists in principle. May not converge.
2. **Move U2 or L1** — the next-largest movable bodies after U1. Frees a real
   pocket but disturbs the BQ25505's switching loop, which is the one place on
   this board where layout genuinely matters electrically.
3. **Narrower BLE module (v4)** — U1 is 44 % of the board. This is the answer
   B6 originally proposed, and it is the only one with room to spare. But every
   sub-162 mm² module either lacks a VDDH pad or needs antenna clearance a
   19.30 mm board cannot give (see the module survey).

**Recommended: try 1, fall back to 2.** Option 3 is a bigger project than the
PCM justifies on its own.
