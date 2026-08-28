---
title: TouchID — the two parts JLCPCB does not supply
type: project
---

# The two parts you buy yourself

JLCPCB assembles the board. **These two are not on the BOM and never will be** —
the sensor mounts to pads (J2) and the cell is hand-wired to BT1. Checked
2026-08-28.

---

## 1. Fingerprint sensor — HLK-ZW0905

**It must be the ZW0905 exactly.** Hi-Link sell the ZW0901, ZW0906, ZW0623,
ZW0642, ZW0919 and ZW0608 alongside it. They look nearly identical and have
**different pinouts and different diameters**. The pinout in DESIGN-SPEC §5 was
*already wrong once* — it was the ZW0901's table, reversed end-for-end.

The housing gives you **0.185 mm of margin per side** on an Ø18.00 flange. A
ZW0919 at Ø18.10 does not fit.

| where | price | MOQ |
|---|---|---|
| [Alibaba — Hi-Link official listing](https://www.alibaba.com/product-detail/Hi-Link-HLK-ZW0905-Semiconductor-fingerprint_1601090935149.html) | ~$2.99 | 1 |
| [Alibaba — second ZW0905 listing](https://www.alibaba.com/product-detail/Semiconductor-fingerprint-identification-module-ZW0905-Hailingke_1601070742648.html) | $2.79–4.69 | 1 |
| [Hi-Link direct — ZW0905 test kit / dev board](https://hlktech.net/index.php?id=1226) | ~$5.28 | 1 |

It is **not on AliExpress** — the ZW0623, ZW0906 and ZW0919 are, the ZW0905 is
not. Alibaba is the route.

> **Buy the test kit, not just the module.** It is about $2 more and it comes
> with the USB-UART adapter. You have to bring the sensor protocol up *before*
> the board exists, and you cannot do that with a bare module. Get a spare
> bare module too — J2 is a hand-soldered flex tail and the first one is
> practice.

**Confirm on the listing before paying:** flange **Ø18.00 ±0.05**, barrel
**Ø15.50**, thickness **2.40 mm**, **UART 3.3 V**, and that the pinout matches
DESIGN-SPEC §5 as corrected on 2026-08-27.

---

## 2. The cell — and there is a catalogue part for it

B6 said "buy the CP1254 as a protected, tabbed assembly" and left it as an
open procurement item. **That assembly exists as a stocked part number:**

> ### VARTA CoinPower **CP1254 A4X IP Wires**, 74 mAh
> **Texim Europe `63125201334-VAR`** — [product page](https://www.texim-europe.com/product/battery-and-power-supplies/batteries/rechargeable-batteries/lithium/varta-coinpower/detail/63125201334-var)
> **"IP" = integrated protection. It ships with wires.** That is precisely the
> B6 item: the PCM on the cell, leads defined by the builder.
> **In stock. Price on request** — this is an RFQ, not a checkout button.

The other two CP1254 variants Texim list, for context:

| part | what it is | stock |
|---|---|---|
| `63125201334-VAR` | A4X **IP Wires** — protected + leads | **In stock** ← this one |
| `63125501513-VAR` | A4X bare cell, no protection | In stock |
| `63125201331-VAR` | A4X **PCBS** | No stock |

[Avnet Abacus](https://www.avnet.com/wps/portal/abacus/manufacturers/m/varta-microbattery/products/varta-coinpower/)
is the other authorised VARTA distributor if Texim will not quote a single unit.

### Two things to settle in the RFQ, and they are not formalities

**1. The finished envelope — Texim quotes the bare CELL.** Their spec block
says Ø12.1 × 5.4 mm, which is the cell, not the assembly. The housing gives:

| | available | note |
|---|---|---|
| pocket diameter | **Ø12.50** | 0.20 mm radial slop over a Ø12.1 cell |
| cell height allowance | 5.6 mm | worst-case A4, not the nominal 5.4 |
| **clear space above the cell** | **1.61 mm** | cell top z 7.85 → sensor barrel z 9.46 |
| lead exit | ±X wire windows | the collar is open on those sides |

So: **the PCM and its wrap must fit inside 1.61 mm above the cell, and the
whole thing must stay under Ø12.5.** Ask for the assembly drawing and check
those two numbers. VARTA's own drawing (`getfile.ashx?id=134488`) is a
**scanned image** — 16 image objects, no extractable text — so it has to be
read by eye, not parsed.

**2. Does A4X still cap at 4.00 V?** `preflight.py` check 15 hard-codes
`CELL_V_CHARGE_MAX = 4.00` from the **A4** datasheet (2020-02-18). The part in
stock is **A4X** (2023-06-26). If A4X moved that number, check 15 is grading
against a stale limit — get the A4X figure and update the constant.

### The A4X change matters more than VARTA make it sound

VARTA removed the **Current Interruption Device** from the A4 generation, and
say so plainly: modern PCMs handle overcharge better, and CIDs can break on
drop tests. They state no dimensional or electrical impact.

But the CID was a *second, independent* overcharge stop. Without it **the PCM
is the only one left** — which makes the 3.912 V charge ceiling (a full 345 mV
below the PCM's 4.30 V trip) worth more than it was when this was a belt-and-
braces argument. Do not let anyone "recover the lost capacity" by raising it.

### Do not substitute a bare LIR1254

The LIR1254 is the same 12.5 × 5.4 form factor, widely sold (EEMB, Grepow),
and cheap — and **every one of those listings is an unprotected cell**. The
eBay and Amazon 4-packs have no PCM and no leads. Under this design the PCM is
not optional: VARTA's CoinPower handbook §6.3 requires over-charge,
over-discharge, over-current *and* short-circuit protection, and the A4X has
no CID to fall back on.

If the VARTA route fails, the fallback is a **pack assembler** (EEMB and
Grepow both do custom terminations) building to the envelope above — not a
bare cell off a marketplace.
