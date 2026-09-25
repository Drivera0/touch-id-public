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

---

## Coin cell HOLDER — evaluated and rejected, 2026-08-30

The idea: fit a holder with wires, buy generic LIR1254 cells off the shelf, keep
the protection on the board. It solves the "wired cells are rare" problem
cleanly. **It fails on four counts, and the second is the serious one.**

### 1. It does not fit the pocket

    housing body OD                18.37 mm
    sensor window ID               15.60 mm
    cell pocket, SHORT             13.00 mm   <-- plan of record
    cell pocket, TALL              14.00 mm
    the cell                       12.50 mm dia

A holder must wrap a retaining wall, side clips and contacts **around** a
12.5 mm cell. The smallest practical 12 mm holders are ~15.5-16.0 mm across.

    SHORT pocket 13.00  ->  short by 2.50-3.00 mm
    TALL  pocket 14.00  ->  short by 1.50-2.00 mm

Widening the pocket to 16 mm leaves a **1.2 mm collar wall** against 18.37 OD,
and the sensor window is already 15.60.

### 2. It makes the biggest unmeasured risk in the project worse

The module is already **12.86 mm (short) / 14.86 mm (tall) against the 8.36 mm
knob module it replaces** — 1.5x to 1.8x. A holder adds 1.5-3.0 mm on top,
taking it to **~16.4-17.9 mm, or 2.0-2.1x**.

The housing file says it plainly: *"a slot depth NOBODY HAS MEASURED ... If the
slot turns out shallow this is the first thing to give."* Spending 3 mm of
height on a convenience, against an unmeasured limit, is the wrong bet — and
**measuring the slot is cheap.** Do that first, whatever else is decided.

### 3. Spring contacts under a device that gets PRESSED

The impedance budget survives it — contacts add ~20-50 mOhm against 3.3 Ohm.
Reliability is the issue: **a fingerprint reader is a button.** Repeated axial
force on a spring-held coin cell risks momentary contact break, and a momentary
break on a BLE device is a reset mid-transaction. The wired cell has no such
failure mode.

### 4. Reese's Law — this one matters for selling them

**16 CFR 1263**, from Reese's Law, issued March 2024 and **in effect September
2024**. For consumer products with button/coin cells it requires:

* battery compartments with **replaceable** cells to be secured so they need
  **a tool, or two independent and simultaneous hand movements** to open;
* the compartment to survive **use-and-abuse testing** without liberating the
  cell;
* warnings on the packaging, on the product where practicable, and in the
  instructions.

A sealed, wired cell inside a glued housing is a far smaller compliance surface
than a user-accessible coin-cell compartment. Adding a holder converts a sealed
product into one carrying the full compartment requirement — exactly the wrong
direction for selling these.

### And it does not actually solve the PCM question

Generic **LIR1254 cells are BARE** — a Li-ion coin in a can, no protection. So
"keep the PCM" means keeping **U5 on the board**, which is what the design
already does. The holder changes how the cell is *mounted*, not whether the
board carries protection. It costs height, fit, reliability and a regulatory
category, and buys nothing on that front.

**Verdict: stay with a pre-wired cell.** The wired-cell rarity that motivated
this is better solved by [the LPM1254 sourcing above](#) — LiPol sell wired
assemblies at MOQ 5 with card payment.

---

## LiPol quotation received 2026-08-30 — resolves two open questions

**Quoted:** LPM1254 3.6 V **80 mAh**, with protection circuit and wires.
MOQ 5 @ [pricing redacted].
Lead time 1-2 weeks, DHL/UPS/FedEx door-to-door 7 days, PayPal/card, duties excluded.

### 1. Max discharge current is 80 mA for this variant — a THIRD figure

| source | max continuous |
|---|---|
| VARTA CP1254 — **wrong cell**, corrected 2026-08-30 | 140 mA |
| LPM1254 60 mAh datasheet | 30 mA |
| LPM1254 65 mAh catalogue page | 65 mA |
| **LPM1254 80 mAh — vendor, for the part quoted** | **80 mA** |

The rating scales with capacity, which is why three numbers were all "right".
**For the 80 mAh part the load of 25 mA is 31% of rating** — comfortable, not
the 83% that the 60 mAh datasheet implied. U5's 0.315 A trip is **3.9x** the
cell rating (not 2.2x, not 10.5x).

### 2. The assembled size — the housing file asked for exactly this

`touchid_module_v6.py` says, verbatim:

> *"LIPOL CONTRADICT THEMSELVES ON DIAMETER, so this is built to the WORSE one
> ... Resolve it with LiPol before production."*
> *"The datasheet publishes NO assembled thickness, so 8.4 is still the
> website's '+3.0 mm' blanket adder on a 5.4 cell -- NOT a per-model figure."*

**Vendor answer, with PCM: 6.7 mm thick x 12 mm diameter.** Both guesses were
conservative:

| | modelled | actual | |
|---|---|---|---|
| diameter | 13.5 | **12.0** | 1.50 mm smaller |
| thickness | 8.4 | **6.7** | 1.70 mm smaller |

O12.0 clears even the SHORT pocket (O13.00) by 1.00 mm.

### 3. So the PROTECTED cell is now the SHORTER build, not the taller one

Module height = `riser_h + 8.36`.

| build | riser | cell | module | vs the 8.36 knob module |
|---|---|---|---|---|
| tall, as built | 6.50 | 8.4 budget | 14.86 | 1.78x |
| **re-cut for the real protected cell** | **4.80** | **6.7 actual** | **13.16** | **1.57x** |
| short (bare-cell plan of record) | 4.50 | 5.6 | 12.86 | 1.54x |

**The protected cell costs only 0.30 mm of height over the bare-cell plan** —
and it deletes U5, R8 and C14 from the board, which removes the U5.2 open pad
and one of the two zero-stock BOM lines (`C6989585`). That is a much better
trade than the 2.00 mm the "tall" variant was reserving.

### 4. The shipping is the problem, and it is probably a fixed DG fee

    [volume pricing redacted]
   [volume pricing redacted]
   [volume pricing redacted]
   [volume pricing redacted]

Lithium cells ship as dangerous goods (**UN3480**, cells shipped on their own),
which carries a per-SHIPMENT surcharge plus DG packaging and paperwork. If that
is what the [shipping] is, it barely moves with quantity or destination — so the
question to ask is whether it **scales**, not just whether it can be reduced.

**Still to ask:** price WITHOUT the PCM (for comparison, though the protected
part now looks better on both board and housing), shipping to a US address
(destination redacted), whether [shipping] is a DG surcharge and how it scales, and
production pricing versus the sample fee.
