---
title: Component reference — datasheets, models, and what is already verified
type: project
updated: 2026-08-29
---

# Component reference

**One index for every part on the board**, so nobody has to re-derive a part
number or go hunting for a datasheet again.

> [!important] **Most of this does NOT need downloading.**
> Every footprint on `pcb-v3-handoff.kicad_pcb` has **already been measured
> against its package** by `verify_sourcing.py` (it compares each land to the
> part actually bought, using rotated pad corners rather than circumscribed
> circles). `preflight.py` re-checks the whole board before any order.
>
> **So the only part that needs a new footprint is the PCM.** Pulling 3D models
> for the passives would be work without a purpose — they are 0402s and 0603s
> whose lands are verified and whose height (0.5 mm) is nowhere near the 2.25 mm
> cell seat.

## The board — 20 distinct parts

| refs | part | LCSC | lib | JLC stock | datasheet |
|---|---|---|---|---|---|
| U1 | Raytac MDBT50Q-1MV2, SMD-61P | `C5118826` | extended | 0 | [PDF](https://www.lcsc.com/datasheet/C5118826.pdf) |
| U2 | TI BQ25505RGRR, VQFN-20-EP 3.5x3.5 | `C882746` | extended | 829 | [PDF](https://www.lcsc.com/datasheet/C882746.pdf) |
| U3, U4 | TI TPS7A2033DQNR, X2SON-4 1x1 | `C46459900` | extended | 4371 | [PDF](https://www.lcsc.com/datasheet/C46459900.pdf) |
| L1 | DMBJ PNLS252012-220M 22uH, 1008, 1.02R, 500mA | `C2849435` | extended | 2288 | [PDF](https://www.lcsc.com/datasheet/C2849435.pdf) |
| C1, C2 | Murata GRM155R61A106ME44D 10uF 10V X5R 0402 | `C77000` | extended | 543698 | [PDF](https://www.lcsc.com/datasheet/C77000.pdf) |
| C5 | FH 0603X106K160NT 10uF 16V X5R 0603 | `C70225` | extended | 479335 | [PDF](https://www.lcsc.com/datasheet/C70225.pdf) |
| C7 | CCTC TCC0603X5R226M100CT 22uF 10V X5R 0603 | `C20416425` | extended | 1168621 | [PDF](https://www.lcsc.com/datasheet/C20416425.pdf) |
| C4 | Murata GRM1555C1H103JE01D 10nF 50V C0G 0402 | `C22400107` | extended | 72632 | [PDF](https://www.lcsc.com/datasheet/C22400107.pdf) |
| C10, C3 | Samsung CL05B104KO5NNNC 100nF 16V X7R 0402 | `C1525` | BASIC | 35834447 | [PDF](https://www.lcsc.com/datasheet/C1525.pdf) |
| C6, C8, C9 | Samsung CL05A105KA5NQNC 1uF 25V X5R 0402 | `C52923` | BASIC | 11865003 | [PDF](https://www.lcsc.com/datasheet/C52923.pdf) |
| C12, C13 | Samsung CL05B103KB5NNNC 10nF 50V X7R 0402 | `C15195` | BASIC | 8405016 | [PDF](https://www.lcsc.com/datasheet/C15195.pdf) |
| R1, R2, R3, R7 | UNI-ROYAL 0402WGF1001TCE 1k 1% 0402 | `C11702` | BASIC | 13920787 | [PDF](https://www.lcsc.com/datasheet/C11702.pdf) |
| R4 | FOJAN FRC0402F4704TS 4.7M 1% 0402 | `C3013173` | extended | 263891 | [PDF](https://www.lcsc.com/datasheet/C3013173.pdf) |
| R5 | UNI-ROYAL 0402WGF1004TCE 1M 1% 0402 | `C26083` | BASIC | 3470670 | [PDF](https://www.lcsc.com/datasheet/C26083.pdf) |
| R6 | UNI-ROYAL 0402WGF1003TCE 100k 1% 0402 | `C25741` | BASIC | 14849306 | [PDF](https://www.lcsc.com/datasheet/C25741.pdf) |
| ROK1 | YAGEO RC0402FR-074M53L 4.53M 1% 0402 | `C137964` | extended | 9229 | [PDF](https://www.lcsc.com/datasheet/C137964.pdf) |
| ROK2 | YAGEO RC0402FR-077M15L 7.15M 1% 0402 | `C477783` | extended | 4637 | [PDF](https://www.lcsc.com/datasheet/C477783.pdf) |
| ROK3 | FOJAN FRC0402F1334TS 1.33M 1% 0402 | `C5713265` | extended | 103945 | [PDF](https://www.lcsc.com/datasheet/C5713265.pdf) |
| ROV1 | Walsin WR04W6044FTL 6.04M 1% 0402 | `C172106` | extended | 2040 | [PDF](https://www.lcsc.com/datasheet/C172106.pdf) |
| ROV2 | YAGEO RC0402FR-076M98L 6.98M 1% 0402 | `C137942` | extended | 2674 | [PDF](https://www.lcsc.com/datasheet/C137942.pdf) |
LCSC datasheet links resolve for every code above. JLC assembly stock is a
**2026-08-28 snapshot** — re-check at order time (preflight WARN 21b).

## The three parts that are NOT on the BOM

These are hand-fitted, so they never appear in the assembly files.

| what | part | datasheet | status |
|---|---|---|---|
| Fingerprint sensor | **HLK-ZW0922** | `datasheets/HLK-ZW0922 Specification V1.0_2024-11-20.pdf` + rendered drawing | **archived here** |
| Cell | bare 1254-class + factory leads | see `CELL-DECIDED.md` | awaiting choice |
| **PCM (new)** | **Mitsumi MC3651DF1AAM** | `datasheets/MC3651_SeriesSpecifications.pdf` + rendered bottom view | **archived here** |

## Where to buy the two that JLC cannot supply today

| part | source | price | note |
|---|---|---|---|
| **U1** MDBT50Q-1MV2 | consign to JLC | — | JLC stock 0; customer ships to their warehouse |
| **PCM** MC3651DF1AAM | **Digi-Key CA `2508-MC3651DF1AAMCT-ND`** | **US$1.33 @ qty 1** | **Active, 2,485 in stock, Cut Tape** |

## CAD / 3D models — what actually exists

| part | model? | where |
|---|---|---|
| **MC3651DF1AAM** | **YES — Ultra Librarian, symbol + footprint** | `digikey.ca/en/models/13684190?tab=ultralibrarian` |
| AP6683 (rejected alt) | yes — EasyEDA symbol + footprint | JLC part page `C2849565` |
| everything else on the BOM | **not needed** | lands already verified on the board |

## Files archived in `datasheets/`

* `MC3651_SeriesSpecifications.pdf` — the PCM, 8 pages, full electricals
* `MC3651-PLP-4E-bottom-view.png` — 600 dpi render of the terminal geometry
* `HLK-ZW0922 Specification V1.0_2024-11-20.pdf` — the sensor
* `ZW0922-dimensions-drawing.png` — 260 dpi render of §2.3

> [!warning] **Downloads land where I cannot reach them.**
> Anything downloaded through the browser goes to the machine's Downloads
> folder. This session can only see the vault, the uploads folder and its own
> scratch space. **To get a file to me, drop it in the vault or attach it to a
> message** — that is how the ZW0922 spec and this PCM datasheet arrived, and
> both worked first time.
