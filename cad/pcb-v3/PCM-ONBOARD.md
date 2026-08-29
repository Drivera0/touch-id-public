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

## Availability

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

**I have the body size (1.25 × 2.85 × 0.50) and the pinout, but not the pad
positions or sizes.** The package drawing is an image in the datasheet with no
extractable dimensions, and EasyEDA's public API returns 404 for `C6989585`.

**The standing rule is never to invent a land pattern**, so the placement stops
here until one of these produces it:

1. **Open EasyEDA (free), place `C6989585`, export the footprint.** Five
   minutes, and it is authoritative — it is what JLC will assemble to.
2. Render the Mitsumi package drawing (page 3 of the Digi-Key mirror) at high
   DPI and read the dimensions by eye.
3. Ask Mitsumi for the recommended land pattern.

Route 1 is the fastest and the most trustworthy.
