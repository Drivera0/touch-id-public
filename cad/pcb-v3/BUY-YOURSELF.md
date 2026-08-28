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

## 2. The cell — and the "catalogue part" was WRONG on both counts

> ### CORRECTION 2026-08-28 — read this before buying anything
>
> An earlier version of this file said **VARTA CP1254 A4X IP Wires**
> (`63125201334-VAR`) was the protected, wired assembly B6 asked for, and that
> its drawing was an unreadable scan. **Both claims were wrong.** The drawing
> parses fine, and it says the part is **not protected and does not fit.**

**The drawing is machine-readable.** `getfile.ashx?id=134488` = VARTA dwg
**805999 rev 0**, *"CP1254 A4 IP W SOC 30% **with kapton and crimping tags**"*.
Its text extracts cleanly. The earlier "16 image objects, no extractable text"
finding was about a different fetch path, and it stopped the check that would
have caught this.

### There is no PCM in it

Nothing in the drawing's parts list is a protection circuit — it is kapton
tape, insulation tapes, crimping tags, Sumitube F34 sleeving and two AWG 30
UL 1571 wires. And **note 4 is explicit**:

> "BATTERY VALIDATION INCLUDING SAFETY ELECTRONICS MUST BE DONE BY CUSTOMER
> ACCORDING TO UL 2054."

The dimensions settle it independently. Bare cell **5.4** mm; finished assembly
**5.6 mm including tags thickness** — a **0.2 mm** delta. That is kapton plus
crimped tags. **No PCM fits in 0.2 mm.** So "IP" is insulation, not integrated
protection.

### And it does not fit the pocket

The drawing gives the FINISHED envelope, which Texim's spec block does not:

| | drawing (finished) | housing has | verdict |
|---|---|---|---|
| diameter incl. kapton overlap | **Ø12.8 +0.10/−0.30** → **12.9 max** | Ø12.50 pocket | **FAILS by 0.40 mm** |
| height incl. tags | **5.6 ±0.3** → **5.9 max** | 5.6 + 1.61 above | fits, eats 0.30 of the 1.61 |
| leads | AWG 30 UL 1571, red +, black −, **42 ±3 mm**, twisted, lead-free tinned | ±X wire windows | fine |
| weight | 2.0 g | — | — |
| shipped state | **SOC 30 %** | — | arrives part-charged |

Ø12.1 was always the **bare cell**. The model's `cell_d_max = 12.1` never
accounted for the kapton wrap, so the pocket was sized against the wrong
number. **A wrapped assembly needs the pocket at Ø13.0+, not Ø12.50.**

### Both Texim CP1254 A4X parts are now NRND

`63125201334-VAR` *and* `63125501513-VAR` both carry **"This product is not
intended for new designs."** Still "In Stock", still **Price on Request**, and
both flagged **dangerous goods** for shipping.

| part | what it actually is | status |
|---|---|---|
| `63125201334-VAR` | A4X + kapton + tags + wires — **no PCM** | In stock, **NRND**, RFQ |
| `63125501513-VAR` | A4X bare cell | In stock, **NRND**, RFQ |
| `63125201331-VAR` | A4X PCBS | No stock |

[Avnet Abacus](https://www.avnet.com/wps/portal/abacus/manufacturers/m/varta-microbattery/products/varta-coinpower/)
is the other authorised VARTA distributor if Texim will not quote a single unit.

### What this leaves open

The PCM still has nowhere to live. It is not on the board (measured — 9.1 % of
the top layer is free and none of it can take a via), and it is **not on the
cell** either. That is now the open item, and it is a design decision, not a
purchase.

**Does A4X still cap at 4.00 V?** `preflight.py` check 15 hard-codes
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

### You are not allowed to attach the wires yourself

CoinPower Technical Handbook **§8.7, Cell Connection**:

> "Soldering or welding of wires or other types of connectors **directly to the
> cell is strictly prohibited.** A proper cell connection **can only be done by
> the cell manufacturer itself.** If soldering or welding … is performed by any
> entity other than the cell manufacturer, **all claims regarding warranty,
> performance and safety will be invalidated.**"

This closes the obvious workaround. "Buy the bare Ø12.1 cell — which *does* fit
the pocket — and add your own leads and PCM" is not an option. And §7.3 makes
the PCM non-optional: *"This is mandatory for all lithium cells."*

**So the bind is:** the bare cell fits but may not be connected; the wired
assembly may be connected but is Ø12.9 and carries no PCM. **The housing was
sized around a cell nobody is permitted to use.**

### Diameter is not the hard part — the axial gap is

The pocket has plenty of room to grow. Collar OD is 17.17, so:

| pocket | collar wall left |
|---|---|
| Ø12.5 (now) | 2.335 mm |
| Ø13.4 | 1.885 mm |
| **Ø14.0** | **1.585 mm** |

Bosses sit 10.255 mm from the axis and the filleted cavity corner 7.995 mm, so
neither is reached. **Any of these is fine.**

The tight dimension is the **1.61 mm axial gap** (cell top z 7.85 → barrel
bottom z 9.46), and it has to swallow both the PCM *and* VARTA's venting
allowance — the handbook says *"under abusive conditions the cell may vent; to
ensure safe venting, up to __ mm of additional space in axial direction is
necessary"*, and drawing note 3 repeats it as "cell deflection space". **The
digit is dropped by this PDF's text encoding — get that number before
committing to a stack-up.**

### Where an individual can actually buy one — checked 2026-08-28

Nobody sells a **protected + wired CP1254** over a counter. Every authorised
VARTA channel is RFQ, MOQ and dangerous-goods paperwork, and the assembly they
would quote has no PCM anyway. These are the real single-unit options:

| source | what you get | price | protected? | notes |
|---|---|---|---|---|
| [patareid.ee — A4X with wires](https://www.patareid.ee/en/products/varta-cp1254-a4x-77mah-li-ion-battery-37v-with-wires/) | genuine VARTA A4X, wires | **€15.00** | **No** | **Out of stock, 1 month**. Retail checkout, EE → CA |
| [patareid.ee — A4X with tabs](https://www.patareid.ee/en/products/varta-cp1254-a4x-coinpower-li-ion-77mah-battery-37v-with-tabs/) | genuine VARTA A4X, solder tabs | ~€15 | No | tabs, not wires |
| [AliExpress — LIR1254 *with protection circuit board*](https://www.aliexpress.com/item/1005006538533778.html) | clone cell + PCM + wires | **C$7.09** | **Claims yes** | 71 sold. **Verify Ø and PCM chip.** LIR1254 is Ø12.5 nominal — bigger than the VARTA's Ø12.1 before the PCB |
| [CentralSound — CP1254 A3 w/ wires](https://centralsound.co/products/varta-cp1254-a3-3-7v-li-ion-rechargeable-battery-new-w-wires) | A3, not A4X, wires | ~US$15/2 | No | US shipper, earbud-repair trade |
| [Amazon — STRENG-CELL 2-pack](https://www.amazon.com/STRENG-CELL-Replacement-Battery-Wf1000X-Bluetooth/dp/B0975WF9MD) | CP1254-compatible, wires | ~US$15 | No | ships to CA |
| eBay ([A3](https://www.ebay.com/itm/146278466951), [A4](https://www.ebay.com/itm/145283672753)) | 2 pcs + tools | ~US$12 | No | earbud repair stock |

**Why they are all unprotected:** these are earbud service parts. In a
Powerbeats or a Galaxy Bud the PCM sits on the earbud's mainboard, not on the
cell — so the aftermarket never puts one on the cell either. Same reason
VARTA's own "IP W" assembly has none.

**The AliExpress protected LIR1254 is the only candidate that ships with a
PCM**, and it is the one that needs measuring before it is trusted: confirm
the finished diameter, the PCM's protection IC, and its over-charge trip. Its
product page is behind a bot check, so open it yourself.

**Shipping:** every one of these is a lithium cell — dangerous goods. Expect
surface-only shipping and longer transit into Vancouver, and expect some
sellers to refuse the route outright.
