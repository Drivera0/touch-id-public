---
title: PCM selection — the inline cell protection
type: project
---

# Choosing the PCM

> ## 2026-08-28 — THE PCM IS NO LONGER A PART YOU BUY
>
> Two findings changed the architecture. **Read this before the rest of the
> file, which is now background.**
>
> **1. Nothing fits on the board.** Scanning the routed board against pads,
> component BODIES, all 288 F.Cu tracks, vias and the F.Cu keepouts: the
> largest free square anywhere on the top layer is **0.9 mm**. The smallest
> integrated-FET PCM in existence is 1.0 mm die / ~1.3 mm land. **B6 was right.**
> (Two earlier scans of mine said otherwise — one read the *unrouted* file, one
> silently parsed zero of 288 tracks, and neither excluded component bodies.
> U1 alone is 10.5 × 15.5 on a 19.3 mm square: **44 % of the board**.)
>
> **2. So it goes in the battery assembly, not on a carrier you solder.** Hand-
> building an inline module is per-unit labour and does not scale to a product.
> Buying a *protected pack* instead is what every earbud manufacturer does, it
> needs no board change, and the assembly step stays "solder two wires to BT1".
>
> **The MC3651 recommendation below is therefore now a SPEC LINE to hand a pack
> assembler, not a part to order.** Its 0.315 A trip is still the reason it is
> the right answer — see below.

## The cell that actually fits — and it is a compromise

Searched 2026-08-28 for a cell that is **already protected AND factory-wired**.

**Nothing at any maker or catalogue distributor fits.** Not Adafruit, SparkFun,
TinyCircuits, PowerStream, Digi-Key or Mouser. The reason is geometric: the
pocket is round, so a Ø14.0 limit caps a rectangular pouch at about **9.9 × 9.9
mm** footprint, and the smallest protected LiPo any of them sell is ~3× that.

The column available is **z 2.25 → 9.46 = 7.21 mm** (cell bottom sits on the
MCU lid through the insulator; the sensor barrel starts at 9.46).

**A fitted PCM adds about +3 mm of thickness and +0.5 mm of diameter** — that
adder, published by LiPol Battery across their micro coin line, is what kills
almost everything:

| part | cell | **assembled, incl. PCM + wires** | verdict |
|---|---|---|---|
| **LiPol LPM1040, 40 mAh** | Ø10.0 × 4.0 | **Ø10.5 × 7.0** | **FITS** — 0.21 mm spare |
| LiPol LPM1240, 60 mAh | Ø12.0 × 4.3 | Ø12.5 × 7.3 | misses by **0.1 mm** |
| LiPol LPM1254, 65–80 mAh | Ø12.0 × 5.4 | Ø12.5 × 8.4 | misses by 1.2 mm |
| LPM1140 48 mAh / LPM1045 46 mAh | — | Ø11.5 × 7.3 / Ø10.5 × 7.5 | miss by 0.1 / 0.3 mm |
| **VARTA CP1254 A4X** | Ø12.1 × 5.4 | **no PCM available at all** | — |

Supplier: **LiPol Battery Co. Ltd**, Shenzhen — `lipobattery.us` /
`lipolbattery.com`. MOQ 5, PayPal/card, worldwide DHL/FedEx/UPS. They publish
real trip data per model (their LP221620 datasheet gives **over-charge 4.275 V
±50 mV, over-discharge 2.75 V ±50 mV, over-current 2–2.5 A**) — but **not for
the LPM line**, so those numbers must be requested, not assumed.

### What 40 mAh costs

Against the 4.0 mWh/day load budget, charging only to 3.912 V and cutting at
3.12 V:

| cell | nameplate | usable (approx) | reserve with zero harvest |
|---|---|---|---|
| CP1254 A4X 77 mAh | 285 mWh | ~142 mWh | **~36 days** |
| LPM1240 60 mAh | 222 mWh | ~133 mWh | ~33 days |
| **LPM1040 40 mAh** | 148 mWh | ~89 mWh | **~22 days** |

Harvest still covers the daily load ~4.7× on four hours of backlight, so the
cell is only a dark-period buffer. **Three weeks of not touching the keyboard**
is the real question, and that is a product decision, not an engineering one.

### Two things to settle with LiPol before ordering

1. **Ask for the LPM1240 stack-up.** The "+3 mm" is a round-number blanket
   figure across the series. If the real number for that model lands at 7.2 mm
   it fits, and it carries **50 % more capacity** than the LPM1040. One email.
2. **LPM1040 has 0.21 mm of margin, and the cell's own +0.2 mm thickness
   tolerance eats all of it** — worst case is exactly 7.2 mm. Ask for the
   assembled max, not the typical, **and** ask what axial venting clearance
   they require. VARTA demand one for CoinPower; a Li-ion coin from anyone
   needs the lid free to lift.

Researched 2026-08-28. The PCM cannot go on the board (B6: 9.1 % of the top
layer free, none of it via-capable) and does not come on the cell (the VARTA
"IP W" assembly is kapton + tags + wires only). **So it goes inline on the
leads**, between the cell and BT1.

## VARTA's own recommended list is mostly unusable

VARTA name six acceptable parts. Two problems:

**Four of the six are IC-only** — they switch external MOSFETs, which there is
no room for. BQ29700/29707, S-8211C, R5613L, MM3077LY all need a dual N-ch FET
beside them, and no DFN dual FET under 0.80 mm tall was found in stock. SOT-23-6
(FS8205A and friends) is 1.1–1.45 mm, which eats most of the 1.61 mm on its own.

**Both integrated-FET parts they name are dead:**

| part | status |
|---|---|
| Diodes **AP9211** | **Obsolete** at Digi-Key, 0 stock across all 25 listings. LCSC has **2 pcs**, flagged Discontinued |
| **SGM41100** | **0 stock** at LCSC, JLCPCB and Digi-Key. Digi-Key does not carry the line |

So the answer is a part VARTA does not name.

## The candidates that survive

| | **Mitsumi MC3651DF1AAM** | **ALLPOWER AP6683** |
|---|---|---|
| package | PLP-4E, **1.25 × 2.85 × 0.50 max** | DFN1×1-4, **1.00 × 1.00 × 0.40–0.50** |
| integrated FETs | yes, 65 mΩ typ | yes, 55 mΩ typ |
| over-charge | **4.280 V ±20 mV** | 4.30 V (4.25–4.35) |
| over-discharge | 2.700 V ±100 mV | 2.80 V (2.7–2.9) |
| **discharge over-current** | **0.315 A** | 0.9 A |
| short-circuit | ≈2.9 A, 0.75 ms | 10 A, 300 µs |
| Iq operating | 3.0 µA typ / **4.5 µA max** | **0.7 µA typ** (no max given) |
| Iq power-down | 0.1 µA max | 0.1 µA typ |
| 0 V charging | **prohibited** | allowed |
| buy | **Digi-Key CA, 2 485 stock, C$2.11 @1, Active** | LCSC `C2849565`, 103 757 stock, US$0.063, MOQ 1 |

## Recommendation: MC3651DF1AAM

**Because of one number: the 0.315 A over-current trip.**

The cell is rated **140 mA continuous / 210 mA pulse**. Every other part in this
report trips between 0.9 A and 11 A — they protect the *wiring*, not the cell.
A 0.9 A trip means the PCM does not intervene until the cell is already at 6×
its continuous rating. 0.315 A is the only threshold found anywhere that is
actually sized to this cell.

It is also the only integrated-FET part with real stock that is **Active**
rather than obsolete, it is a name brand with guaranteed max limits rather than
typicals, and 1.25 × 2.85 × 0.50 mm fits.

**Cost of choosing it:** 3.0 µA typ / 4.5 µA max is **6.7 % / 10.0 %** of the
4.0 mWh/day budget (0.7 µA would have been 1.6 %). Harvest covers ~4.7×, so it
is affordable — but it is now the third-largest line in the budget, above
nRF sleep. Re-run the budget when the design is next touched.

**Backup: AP6683** if the Iq turns out to matter more than the trip point —
0.7 µA, 1 mm square, six cents. But it is typicals-only, several specs are
"guaranteed by design, not tested", and the vendor has no Digi-Key or Mouser
presence. For a part whose entire job is to work when everything else has
failed, that is a real reservation.

## Two things to confirm before ordering the MC3651

1. **Is the over-discharge latch enabled on the DF1AAM option?** The series
   datasheet ties standby current to it (0.1 µA latched vs 0.5 µA not) but the
   per-option table does not say which this variant is. **If it latches, release
   may require a charger** — and this device's "charger" is a harvester that
   only runs when the keyboard backlight is on. Ask Mitsumi or Digi-Key.
2. **0 V charge is prohibited.** A cell that self-discharges to 0 V cannot be
   revived — the device would be bricked. Probably tolerable: `VBAT_OK` opens
   the load at 3.12 V, the PCM cuts at 2.70 V and then draws 0.1 µA, and
   CoinPower holds >90 % for a year, so reaching 0 V would take years. It is
   also arguably the *correct* safety behaviour. But know that it is the
   failure mode.

## The ready-made PCM board route is dead — on thickness

Worth recording so nobody re-opens it:

* **LCSC sells no assembled PCM modules** — bare ICs only.
* **AliExpress**: every listing that states a thickness says **2.2 mm**.
* **Professional catalogue (EYBMS)**: all 16 models in the 1S line are **3.0 mm**,
  without exception, including the round coin-style boards.

**2.2–3.0 mm against 1.61 mm of space.** On top of that, the lowest over-current
trip on the market is 2.5 A (≈18× the cell's rating), the IC is always
`DW01 + 8205A` where it is named at all, and **not one listing publishes a
quiescent current** — which for a harvesting design is disqualifying by itself.

So the PCM has to be a bare IC on a small carrier: either a tiny satellite PCB,
or specified to whichever pack assembler builds the cell.

## Where it physically goes

Two candidate locations:

| | space | verdict |
|---|---|---|
| **above the cell** (z 7.85 → 9.46) | **1.61 mm** tall × Ø15.60 wide | **use this** — laterally enormous, height is the only constraint |
| ±X wire channels | 2.135 mm radial × 2.26 mm tall, 90° each side | already carries **six** hand-soldered sensor wires to J2 |

Stack-up above the cell, MC3651 on a 0.4 mm 2-layer carrier:

```
  0.50   MC3651DF1AAM (max)
  0.40   carrier PCB
  0.05   solder
  ----
  0.95   used        of 1.61 available
  0.66   LEFT for VARTA's venting / deflection allowance
```

A 0.2 mm flex carrier instead would leave 0.91 mm.

**This is where the unknown bites.** The CoinPower handbook requires "up to
__ mm of additional space in axial direction" for safe venting and the digit is
dropped by the PDF's text encoding — see `BUY-YOURSELF.md`. If that figure is
≤ 0.6 mm the stack works as drawn. **Do not bond the carrier down onto the cell
top**: the venting mechanism is the lid lifting, so the board must not clamp it.
