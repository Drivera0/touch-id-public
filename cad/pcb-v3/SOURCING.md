---
title: TouchID v3 — sourcing
type: project
---

# Sourcing — all 21 BOM lines, checked 2026-08-28

Every part number below was read from **JLCPCB's own assembly library**, not
from LCSC's shop and not from a datasheet.

> **These are two different warehouses.** LCSC *sells* parts JLCPCB cannot
> *place*. A part with shop stock and no assembly stock comes back as "cannot
> be assembled" **after you have paid**. Anything sourced from an LCSC search
> alone is unverified for this purpose.

Machine-readable version: `cad/exports/touchid-v3-BOM.csv`.
Re-verify the lands with `python verify_sourcing.py`, the whole order with
`python preflight.py pcb-v3-handoff.kicad_pcb` (check 21).

## The blocker: U1 has no assembly stock anywhere

**Every MDBT50Q variant in JLCPCB's library reads stock 0 — all 19 of them**,
Raytac's own and JLC's internal entries alike. This is not a variant problem
and not a wrong part number.

It is **not delisted**: `isBuyComponent = 1`, no `noBuyReason`, estimate "11"
(days). It is backordered — `canPresaleNumber = -75`. LCSC's shop is also out
of stock, though third-party sellers on LCSC list **32 pieces at $25.54**,
5–7 business days, against Raytac's own $18.98.

At ~$19–26 this is also **by far the most expensive part on the board** —
more than everything else combined.

The bare nRF52840 die *is* in stock (C190794, 52 404 pcs) but that is a
different design: crystal, matching network, antenna, and RF certification.
Not a substitution.

**Three ways forward, none of which need the board to change:**

| option | cost | what it means |
|---|---|---|
| Wait for JLC stock | none | ~11 days quoted, 75-unit backlog ahead of you. Re-check at order time. |
| Buy the module yourself, have JLC fit the rest | ~$25 + hand work | You solder an LGA-61 module with pads **under** the body. Needs hot air or a reflow plate; not an iron job. |
| JLC consigned parts | shipping | You post the module to JLC and they place it. |

The rest of the board is fully assemblable today.

## What is sourced

**JLC Basic parts** (no per-type setup fee) — 6 of the 20 distinct codes:

| ref | value | LCSC | stock |
|---|---|---|---|
| C3, C10 | 100 nF 16 V X7R 0402 | `C1525` | 35.8 M |
| C12, C13 | 10 nF 50 V X7R 0402 | `C15195` | 8.4 M |
| C6, C8, C9 | 1 µF 25 V X5R 0402 | `C52923` | 11.9 M |
| R1, R2, R3, R7 | 1 kΩ 1 % 0402 | `C11702` | 13.9 M |
| R5 | 1 MΩ 1 % 0402 | `C26083` | 3.5 M |
| R6 | 100 kΩ 1 % 0402 | `C25741` | 14.8 M |

**Extended parts** — 14 distinct types, each carrying a one-off JLC setup fee:

| ref | part | LCSC | stock |
|---|---|---|---|
| U1 | Raytac MDBT50Q-1MV2 | `C5118826` | **0** |
| U2 | TI BQ25505RGRR | `C882746` | 829 |
| U3, U4 | TI TPS7A2033DQNR | `C46459900` | 4 371 |
| L1 | DMBJ PNLS252012-220M 22 µH | `C2849435` | 2 288 |
| C1, C2 | Murata GRM155R61E475ME15D 4.7 µF **25 V** | `C2858031` | 184 764 |
| C4 | Murata GRM1555C1H103JE01D 10 nF **C0G** | `C22400107` | 72 632 |
| C5 | 10 µF 16 V X5R 0603 | `C18164635` | 1.13 M |
| C7 | 22 µF **10 V** X5R 0603 | `C20416425` | 1.17 M |
| R4 | 4.7 MΩ 1 % | `C3013173` | 263 891 |
| ROK1 | 4.53 MΩ 1 % | `C137964` | 9 229 |
| ROK2 | 7.15 MΩ 1 % | `C477783` | 4 637 |
| ROK3 | 1.33 MΩ 1 % | `C5713265` | 103 945 |
| ROV1 | 6.04 MΩ 1 % | `C172106` | **2 040** |
| ROV2 | 6.98 MΩ 1 % | `C137942` | **2 674** |

## Three choices that are not arbitrary

**C1/C2 — Murata 25 V, and the reason is the curve, not the rating.**
These are CIN and CSTOR; the BQ25505 wants **≥ 4.7 µF**. A 4.7 µF 0402 at
4.3 V DC bias can lose half its value, which is the *same trap* already
documented for C7 — and unlike C7 it would show up as boost instability at
cold start, not as ripple. The Murata part is chosen because **Murata
publishes the DC-bias curve**, so the requirement can be *verified* instead of
assumed. **That verification has not been done** — it needs SimSurfing and a
human. If the curve gives under 4.7 µF effective at 4.3 V, step to a 10 µF
nominal in the same 0402 land (`C6119763`, 10 V, 185 596 in stock).

**C4 — C0G on purpose.** CREF sets the BQ25505's internal reference droop, so
this is a leakage-critical part, not a decoupling cap. The ±5 % tolerance sits
inside the datasheet's 9–11 nF window.

**ROV1/ROV2 — thin, single-sourced, and they set the charge voltage.**
2 040 and 2 674 pieces, one manufacturer each. These are the pair that gives
`VBAT_OV = 3.912 V` (3.955 V worst case) against the CP1254's 4.00 V limit.
**Do not let anyone substitute these blind** — a "close enough" value here
walks the charger back toward the 4.246 V that was the original overcharge
bug. If either goes out of stock, recompute from
`VBAT_OV = 1.5 × 1.21 × (1 + ROV2/ROV1)` and keep the worst case under 4.00 V.
ROK1 (9 229) and ROK2 (4 637) are also single-sourced but only set the
VBAT_OK thresholds, where being a little off is harmless.

## Land verification

`verify_sourcing.py` measures every land on the board against the package
actually bought: **25 of 25 two-terminal lands match, 0 mismatches.**

Its first version reported three mismatches that did not exist, by bounding
each pad with its circumscribed circle — which inflates every elongated pad.
L1's land read 4.256 mm when it is 3.256. Rewritten to rotate the four
corners. **The checker was wrong again, not the board**, which is now the
usual outcome here.

## Still open

* **U1 stock** — the one thing standing between this and an assembly order.
* **C1/C2 DC-bias curve** — needs a human and Murata SimSurfing.
* **No gerbers exist for this board.** Sourcing does not fix that; they still
  have to be exported from KiCad before anything can be uploaded.
* **BT1** is not on this list and never will be: the cell is a hand-wired,
  protected assembly (B6), not a placed part.
