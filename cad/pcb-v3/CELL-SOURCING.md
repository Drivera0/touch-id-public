---
title: Cell sourcing — LPM1254, and two datasheet contradictions
type: project
updated: 2026-08-30
---

# The cell — buyable, but the datasheet contradicts the design notes twice

Requirements the cell must meet: **20-35 mAh** (60+ is fine), **impedance under
3.3 Ohm**, factory-fitted wires (you may not solder to the cell yourself), fits
the **D14.00 housing pocket**, and buyable **singly and in small volume**.

## LiPol LPM1254 — checked against the real datasheet (MD_9241_10, 10.09.2021)

| | datasheet | design needs | verdict |
|---|---|---|---|
| assembled size | **D13 ±0.5 × 6.5 ±0.3** | D13.5 × 8.4 pocket | **fits** |
| wires | **UL10064 32AWG, 30 ±3 mm** | same | **exact match** |
| capacity | 60 mAh min, 64 typ | 20-35 mAh | **comfortable** |
| internal impedance | **<750 mOhm** | under 3300 mOhm | **4.4x margin** |
| max continuous discharge | **30 mA** | 25 mA peak | **83% loaded — thin** |
| compliance | IEC62133-2-2017, RoHS | needed to sell | **good** |

The size and the wire spec match CURRENT-STATE line-for-line, so **the housing
was built for this cell.** Impedance is the one that had to pass and it passes
easily.

> [!danger] CONTRADICTION 1 — the cell is rated 30 mA, not 140 mA
> `PCM-ONBOARD.md` line 24 states *"The cell is rated **140 mA** continuous."*
> The datasheet says **max continuous discharge current 30 mA** (standard
> discharge 12 mA). That is a **4.7x** error, and 140 mA appears nowhere in the
> document — it looks like an assumed 2C rate on a 70 mAh cell.
>
> **What it costs:** the real load is 25 mA (50 scans/day at 25 mA for 1.5 s),
> which is **83% of the cell's rating** — inside spec, but with 17% margin
> rather than the ~6x that 140 mA implied.
>
> **What it breaks:** PCM-ONBOARD ranked the MC3651DF1AAM first *because*
> "0.315 A = **2.2x** cell rating ... the only one that protects the cell."
> Against the real 30 mA rating, 0.315 A is **10.5x**. The comparison that
> selected U5 rests on a number the datasheet contradicts. (MC3651 may still be
> the right part — it has the tightest trip available — but no PCM IC trips near
> 66 mA, so **no protection IC meaningfully guards this cell's continuous
> rating.** They guard against shorts.)

> [!danger] CONTRADICTION 2 — the CATALOGUE part is the PROTECTED one
> PCM-ONBOARD's founding premise: *"a bare wired 1254 is an ordinary retail
> product, a protected one is not."* The datasheet is titled **"Lithium Polymer
> Battery Pack LPM1254 3.7V 60mAh with Protection Circuit Module (PCM)"** and
> its mechanical table reads **PCM: Yes**. The protected part is the standard
> product; the **bare** cell is the special request.
>
> This inverts the sourcing argument that moved the PCM onto the board.

## What this opens up — deleting U5, R8 and C14

The cell's own PCM is **functionally the same part** as U5:

| | cell's PCM | U5 (MC3651) on board |
|---|---|---|
| over-charge | 4.25 V ±50 mV | 4.280 V |
| over-discharge | 2.75 V | 2.700 V |
| over-current | 0.2-0.75 A | 0.315 A |

Buying the catalogue protected cell would let **U5, R8 and C14 come off the
board**, which:

* **removes the U5.2 open pad entirely** — the safety-critical one, the pad that
  currently leaves the protection IC unpowered;
* **frees area inside the pogo block**, the densest region on the board and the
  reason U5.2 has zero legal via sites within 2.5 mm;
* drops three parts from the BOM.

**Do not act on this yet.** It must be confirmed with LiPol that the protected
LPM1254 is orderable at low quantity with wires — CURRENT-STATE records **MOQ 5,
PayPal/card, DHL**, and an enquiry sent 2026-08-28 whose answer is not recorded.
Chase that enquiry before changing the board.

## Alternatives if LiPol does not work out

* **EEMB LIR1254** — 3.7 V 65 mAh, genuinely retail (Amazon / eBay / Walmart /
  eemb.store), UL IEC 62133 (file MH20555). **Bare coin cells, no wires**, sold
  in 4-packs, and eemb.store shows **Sold Out**. EEMB do make "batteries with
  various terminations, pins, wires & connectors" so a wired version likely
  exists to order — needs an MOQ answer. **Do not solder leads on yourself.**
* **VARTA CP1254** — 77 mAh, <0.5 Ohm, 210 mA pulse; electrically the best of
  the three by a wide margin. Already ruled out: both A4X parts NRND, no North
  American CoinPower distributor, and no protected variant.

> [!warning] Get the IR and max-discharge in writing before committing
> DESIGN-SPEC already warns that `TTWWLL` format codes are reliable for size but
> **internal resistance is not inferable** and spans "fine" to "fails the
> budget". This page's numbers come from LiPol's own datasheet; any substitute
> needs the same treatment. The 140 mA figure is exactly the failure that
> warning describes.
