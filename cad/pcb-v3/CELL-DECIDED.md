---
title: The cell — DECIDED
type: project
---

# The cell: LiPol LPM1254 with PCM + wires

Decided 2026-08-28. **Protected at the factory, wired at the factory, full
published datasheet, MOQ 5, PayPal or credit card, DHL door-to-door.**
Nothing to solder, nothing to assemble, no RFQ black box.

Datasheet: `li-polymer-battery.com/wp-content/uploads/2021/09/LPM1254.pdf`
Product page: [lipobattery.us/lpm1254-3-6v-65mah-micro-lithium-ion-battery](https://www.lipobattery.us/lpm1254-3-6v-65mah-micro-lithium-ion-battery/)

## Why this one and not the others

The search kept failing because it was looking at the wrong two things.

**Protected LiPo pouches don't fit — the module is 19.30 mm SQUARE.** Every
protected pouch PowerStream sells (a real retailer, cart, qty-1 prices,
published dimensions) is a **21–52 mm strip**. The shortest, GM201021-PCB at
3 × 10 × 21, is still longer than the 16.77 mm cavity. All nine `-PCB` models
fail on length alone. Pouches are made as strips; this module has no strip in it.

**A coin cell is the only form factor that fits** — and VARTA don't sell a
protected one, which is what sent this in circles. **LiPol do.**

## The numbers, all from the datasheet

| | |
|---|---|
| **PCM** | **Yes** |
| **Wires** | **UL10064 32AWG, 30 ±3.0 mm** — bare leads, no connector |
| Configuration | 1S1P, ~1.5 g |
| **Assembled size** | **Ø13 ±0.5 × 6.5 ±0.3** → worst case **Ø13.5 × 6.8** |
| Rated capacity | 60 mAh min / 64 typ (this datasheet); 65–80 mAh by variant |
| Nominal voltage | 3.7 V (3.6 V on the catalogue page) |
| Max charge voltage | 4.2 V ±50 mV |
| Discharge cut-off | 3.0 V |
| Internal impedance | < 750 mΩ |
| Cycle life | 500 cycles ≥ 80 % |
| Certification | IEC62133-2-2017, RoHS |

**Protection — the numbers that were missing everywhere else:**

| | |
|---|---|
| Over-charge | **4.25 V ±50 mV**, 0.7–1.3 s delay, release 4.00 V ±50 mV |
| Over-discharge | **2.75 V ±50 mV**, 14–26 ms delay, resume 3.50 V ±100 mV |
| Over-current | **0.2 – 0.75 A**, 8–16 ms delay |

That over-current window is right-sized for a 60–80 mAh cell. The generic
market PCM trips at 2.5 A, which protects the wiring and not the cell.

## It fits the housing as already built

Housing v5.2 models the cell at Ø13.5 × 8.4 in a Ø14.00 pocket with a 9.21 mm
column. The real assembly is **Ø13.5 × 6.8 worst case** — so the model is
conservative by 1.6 mm in height and **no housing change is needed**.

## Electrically

`VBAT_OV` = 3.912 V (3.955 worst case) sits **295 mV below** the 4.25 V
over-charge trip — clear of the 150 mV guard preflight check 15 enforces, so
the charger never becomes the safety device's job. Max charge voltage 4.2 V is
well above our ceiling. `VBAT_OK` falling at 3.12 V acts before the PCM's
2.75 V cut-off, which is the right order.

> [!warning] **The one spec to check against the load: max continuous discharge.**
> This datasheet says **30 mA**; the catalogue page for the 65 mAh variant says
> **65 mA**. The CP1254 did **140 mA continuous / 210 mA pulse**.
> The ZW0905 draws 15 mA typ / **25 mA max** while scanning, and the nRF52840
> radio adds to that. A scan overlapping a BLE transmit could exceed 30 mA.
> At <750 mΩ the voltage droop is trivial (~30 mV at 40 mA), so this is a
> **cycle-life** question, not a brown-out. **Confirm the figure for the exact
> variant ordered**, and if it is 30 mA, check the firmware never scans and
> transmits at the same instant.

## Capacity, and the stretch option

| cell | assembled | capacity | reserve at zero harvest |
|---|---|---|---|
| CP1254 A4X (unobtainable protected) | — | 77 mAh | ~36 days |
| **LPM1254** | Ø13.5 × 6.8 | **65–80 mAh** | **~36–43 days** |
| **LPM1454** ← stretch | Ø14.5 × ~6.8 | **85–105 mAh** | **~47–57 days** |

**LPM1454 (Ø14.0 cell, 85–105 mAh) would BEAT the CP1254**, and it still passes
the Ø15.60 bore. It needs the pocket grown Ø14.00 → Ø15.00, which leaves a
1.085 mm collar wall — acceptable. Worth asking about in the same email; if the
assembled diameter comes back ≤ 14.5 it is strictly the better part.

## Two things to confirm before paying

1. **Assembled diameter and thickness, as a maximum.** LiPol contradict
   themselves: the catalogue page says a PCM adds **"+3 mm thickness, +0.5 mm
   diameter"** (→ Ø12.5 × 8.4), while the LPM1254 datasheet drawing says the
   finished pack is **Ø13 ±0.5 × 6.5 ±0.3** (→ Ø13.5 × 6.8). Same part, two
   answers. The housing is cut for the worse of the two, so either way it fits
   — but get the real number in writing.
2. **Max continuous discharge current** for the exact variant (30 vs 65 mA).

## How to buy it — published on their own page

> "our MOQ is **5 pcs**… When we have them in stock, it's available to order
> small quantity order." … "we will provide you with an invoice for payment…
> payment methods are **PayPal, credit card**, and bank transfer" … "we will
> ship them out via **DHL/UPS/FedEx Door to Door**" … "warranty is **one year**
> after the sale."

**If out of stock the MOQ jumps to 5 000 or 10 000** — so the first question is
whether the LPM1254 with PCM is in stock. Reply promised within 12 hours.

This is the same buy-by-invoice flow as the ZW0905 on Alibaba, not a corporate
procurement process.
