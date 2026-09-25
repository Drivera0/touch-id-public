---
title: Verified part library — v3 rebuild
type: project
tags:
  - touchid
  - hardware
  - parts
updated: 2026-08-27
---

# Verified part library (Task A)

**Rule for this file:** every number carries its source. Anything that could not be
traced to a vendor drawing is in **§9 Not verified** and must NOT be drawn as a
footprint until it is closed. Nothing here was estimated, scaled off a picture, or
inferred from a spec table.

Sources fetched 2026-08-27. Where a drawing revision is printed, it is quoted.

---

## 1. U1 — Raytac MDBT50Q-1MV2 (nRF52840 BLE module)

Source: **Raytac approval sheet Version K, issued 2022/07/01**, obtained from
SparkFun's mirror (`cdn.sparkfun.com/assets/4/7/4/3/8/`).

### Electrical — verified

| | Value | Where |
|---|---|---|
| Module size | **15.5 (−0.15) × 10.5 (+0.2) × 2.05** mm | §2.1 PCB Size table |
| Pin count | **61** | §2.5 Pin Assignment |
| **VDDH** | **pin 30**, "High voltage power supply" | §2.5 — **confirmed** |
| VDD | pin 28 | §2.5 |
| DCCH | pin 31 | §2.5 |
| VBUS | pin 32 | §2.5 |
| SWDIO / SWDCLK | **pin 51 / pin 53** | §2.5 |
| GND | pins 1, 2, 15, 33, 55 | §2.5 |
| VDD abs max | **−0.3 to +3.9 V** | §5.1 Absolute Maximum Ratings |
| VDDH abs max | **−0.3 to +5.8 V** | §5.1 |
| VDDH operating | **2.5 min / 3.7 nom / 5.5 max** | §5.2 Operating Conditions |
| VDD operating | 1.7 / 3.0 / 3.6 V | §5.2 |
| VDD_POR | 1.75 V | §5.2 |
| **t_R VDDH** | **100 ms max** rise time 0 → 3.7 V | §5.2 |
| Internal | 32 MHz crystal + Reg1 RF DC/DC inductor already inside | §3 |

> **This settles the VDDH-not-VDD instruction with a datasheet number.** A cell
> charged to 4.25 V exceeds VDD's 3.9 V absolute maximum by 350 mV. VDDH's 5.8 V
> abs max and 5.5 V operating max take it comfortably. The cell floor, 3.0 V at
> discharge cut-off, is well above VDDH's 2.5 V minimum.

> [!danger] New constraint found in §5.2 — see §9 item 2
> **t_R VDDH is 100 ms maximum** for the rise from 0 to 3.7 V. A harvest-charged
> cell rises over hours, not milliseconds. Connecting the cell straight to VDDH,
> as the brief's netlist does, violates this on every cold start from a flat cell.

### Land pattern and antenna keep-out — **NOT VERIFIED, see §9 item 1**

§2.2 (Recommended Layout of Solder Pad, pp. 9–12) and §2.3 (RF Layout Suggestion /
Keep-Out Area, pp. 13–15) are **vector drawings with no extractable text**. Text
extraction returns those pages blank.

One screenshot of pp. 10–12 was captured through the browser pane at 65 % zoom
before the pane stopped compositing. The following callouts were legible in it and
are recorded **as leads, not as verified dimensions**:

| Read from the drawing at 65 % | Page |
|---|---|
| `61 pad, 0.6 x 0.4` — with separate `0.4` and `0.6` leaders | p. 11 |
| `2.95`, `1.6`, `1.2` on the top-layer no-ground-pad region | p. 10 |
| `11.7` overall vertical dimension of the pad field | p. 10 |
| `10.5` overall width | p. 12 |

**Do not build a footprint from that table.** A 61-pad land pattern needs every row
position and pitch, and reading them off a low-magnification screenshot is the same
failure mode that produced the invented U1/U2 patterns. §9 item 1 says how to close it.

---

## 2. U2 — TI BQ25505 boost charger with MPPT, LCSC C882746

Source: **datasheet SLUSBJ3F**, Aug 2013 rev. March 2019; package drawing
**RGR0020A 4219031/B 04/2022**.

### Package outline — VQFN-20 RGR0020A

| Feature | Value |
|---|---|
| Body | 3.65 / 3.35 square (3.5 nominal) |
| Height | 1.0 max / 0.8 |
| Standoff | 0.05 / 0.00 |
| Pitch | **0.5** (16× 0.5 between the outer pins per side) |
| Lead length | 20× 0.5 / 0.3 |
| Lead width | 20× 0.30 / 0.18 |
| **Exposed thermal pad** | **2.05 ± 0.1** square |

### Land pattern — EXAMPLE BOARD LAYOUT, same drawing

| Feature | Value |
|---|---|
| Perimeter pads | **20× (0.6) long × (0.24) wide** |
| Pitch | 16× (0.5) |
| Overall pad-field span | (3.3) × (3.3) |
| **Thermal land** | **(2.05) × (2.05)** |
| Thermal vias | 4× Ø(0.2), at ±(0.775) in x and y |
| Corner radius | (R0.05) TYP |
| Stencil, thermal pad | 4× (0.92) squares at ±(0.56) — 81 % coverage, 0.125 mm stencil |

### The mask-vs-copper question — resolved, and it is NOT the DQN case

The brief warns that TI QFN thermal pads are "routinely solder-mask-defined", citing
the TPS7A2033 DQN incident. **On this drawing that warning does not apply the same way,
and the difference is worth writing down:**

- The **DQN0004A** drawing (TPS7A2033) carries a LAND PATTERN EXAMPLE explicitly
  annotated **SOLDER MASK DEFINED**. Its printed numbers are mask openings, and copper
  is 0.05 larger per side. That is what cost order Y6.
- The **RGR0020A** drawing carries the generic **SOLDER MASK DETAILS** box showing
  *both* options side by side — `NON SOLDER MASK DEFINED (PREFERRED)` and
  `SOLDER MASK DEFINED` — with no pad-specific SMD callout anywhere on the layout.
  The layout is titled `LAND PATTERN EXAMPLE / EXPOSED METAL SHOWN`, and the two mask
  leaders read `0.07 MIN ALL AROUND` (the NSMD case) and `0.07 MAX ALL AROUND` (the
  SMD case).

**Therefore, for RGR0020A the choice is the designer's, and TI's stated preference is
NSMD.** Design it NSMD:

| Layer | Perimeter pad | Thermal pad |
|---|---|---|
| **Copper** | **0.60 × 0.24** | **2.05 × 2.05** |
| **Mask opening** | 0.74 × 0.38 (+0.07 per side) | 2.19 × 2.19 (+0.07 per side) |
| Paste | 0.60 × 0.24 (1:1) | 4× 0.92 at ±0.56 |

> The mask dam between adjacent perimeter mask openings works out at
> 0.5 − 0.38 = **0.12 mm**. That is at JLCPCB's floor. Expect the fab to gang the
> mask across the pin row; that is normal for 0.5 mm QFN and is not a defect.
> If a solid dam is wanted instead, reduce mask expansion to 0.05 and re-check.

### Pinout — SLUSBJ3F §5

| # | Name | | # | Name |
|---|---|---|---|---|
| 1 | VSS | | 11 | OK_HYST |
| 2 | VIN_DC | | 12 | OK_PROG |
| 3 | VOC_SAMP | | 13 | VBAT_OK |
| 4 | VREF_SAMP | | 14 | VBAT_PRI |
| 5 | EN (active low) | | 15 | VSS |
| 6 | NC — tie to PowerPad | | 16 | NC — tie to GND |
| 7 | VBAT_OV | | 17 | NC — tie to GND |
| 8 | VRDIV | | 18 | VBAT_SEC |
| 9 | VB_SEC_ON | | 19 | VSTOR |
| 10 | VB_PRI_ON | | 20 | LBOOST |

### Ratings and required externals — all from §6.1 / §6.3

| | Value |
|---|---|
| VIN_DC recommended | **0.1 – 5.1 V** |
| VIN_DC / VSTOR / all programming pins, abs max | −0.3 – 5.5 V |
| VBAT_SEC / VBAT_PRI | 2 – 5.5 V |
| Peak input power | 510 mW |
| CIN | ≥ 4.7 µF, close to pins 2 and 1 |
| CSTOR | ≥ 4.7 µF ∥ 0.1 µF, close to pins 19 and 1 |
| CBAT | ≥ 100 µF equivalent |
| CREF | 9 / 10 / 11 nF **low leakage**, VREF_SAMP to GND |
| L1 | **22 µH**, LBOOST (20) to VIN_DC (2) |
| ROC1 + ROC2 | 18 – 22 MΩ (unused here — VOC_SAMP straps to GND) |
| ROV1 + ROV2 | **11 – 15 MΩ** |
| ROK1+ROK2+ROK3 | 11 – 15 MΩ |
| VBIAS | **1.205 / 1.21 / 1.217 V** (§6.5) |

> **This overturns DESIGN-SPEC §9's claim** that harvesting PMICs "are out of spec
> above 3.3 V input". That is true of the BQ25504; the BQ25505 is specified to
> **5.1 V** on VIN_DC. The brief's choice of the '505 is correct and this is why.

### VBAT_OV — the brief's 5.6 MΩ / 7.5 MΩ checks out

TI's worked example (§8.2.1) computes ROV1 for VBAT_OV = 4.2 V at RSUM = 13 MΩ:

```
ROV1 = 3 · RSUM · VBIAS / (2 · VBAT_OV) = 3 × 13 M × 1.21 / (2 × 4.2) = 5.618 M → 5.62 M
```

so the governing relation is `VBAT_OV = 1.5 · VBIAS · RSUM / ROV1`.

With the brief's parts, **ROV1 = 5.6 MΩ (VBAT_OV → VSS), ROV2 = 7.5 MΩ (VRDIV → VBAT_OV)**:

```
RSUM = 13.1 MΩ                      (inside the 11–15 MΩ window)
VBAT_OV = 1.5 × 1.21 × 13.1 / 5.6 = 4.246 V
```

**4.25 V confirmed.** Hysteresis is internal, 24–45 mV, so the charger restarts at
about 4.21 V.

> Constraint from §6.1 note 2: **VBAT_OV must be set higher than VIN_DC.** VIN_DC is
> regulated to VOC/2 ≈ 1.5–2.0 V here, and its open-circuit excursion tops out at
> 3.92 V measured. 4.25 V clears both.

---

## 3. U3 — TI TPS7A2033DQNR, X2SON-4 (DQN), LCSC C46459900

**Reuse the traced pattern in `DESIGN-SPEC.md` §3 verbatim.** It was traced from TI
package drawing **DQN0004A 4215302/E** and is the one place in this project where the
solder-mask-defined reading has already been done correctly.

| Feature | Value |
|---|---|
| Copper pads | 0.46 × 0.31 at (±0.43, ±0.325), inner corner chamfered 0.209289 |
| Mask opening | 0.36 × 0.21 (`solder_mask_margin −0.05`) |
| Thermal copper | 0.58 × 0.58 rotated 45° |
| Thermal mask | 0.48 (margin −0.05) |
| Thermal paste | 0.45 (`solder_paste_margin −0.065`) |
| Pinout (top view) | 1 OUT · 2 GND · 3 EN · 4 IN · 5 thermal/GND |

Pin 3 is a **logic-level enable**, which matters for §9 item 3.

---

## 4. U4 — TI LM66100, SC-70-6 (DCK), LCSC C2869734

Source: **datasheet SLVSEZ8A**, March 2019 rev. June 2019; package drawing
**DCK0006A 4214835/D 11/2024**.

### Package outline

| Feature | Value |
|---|---|
| Body | A = 2.15 / 1.85 long, B = 1.4 / 1.1 wide |
| Height | **1.1 max** |
| Lead span | 2.4 / 1.8 |
| Pitch | 4× **0.65** |
| Lead width | 6× 0.30 / 0.15 |
| Lead length | 0.46 / 0.26 TYP |
| Standoff | 0.1 / 0.0 |

### Land pattern — EXAMPLE BOARD LAYOUT

| Feature | Value |
|---|---|
| Pads | **6× (0.9) long × (0.4) wide** |
| Pitch | 4× (0.65) |
| Row spacing | **(2.2)** centre-to-centre |
| Corner radius | (R0.05) TYP |
| Mask | `0.07 MIN ARROUND` NSMD (preferred) / `0.07 MAX ARROUND` SMD |
| Paste | 1:1 with copper, 0.125 mm stencil |

Same generic SOLDER MASK DETAILS box as the BQ25505 — **not** marked solder-mask-defined.
Design NSMD: **copper 0.9 × 0.4, mask opening 1.04 × 0.54**.

### Pinout and the enable behaviour

| # | Name | Note |
|---|---|---|
| 1 | VIN | |
| 2 | GND | |
| 3 | **CE** | active low, **must not float** |
| 4 | N/C | tie to GND or leave floating |
| 5 | ST | active-low open drain; tie to GND if unused |
| 6 | VOUT | |

| | Value |
|---|---|
| VIN operating | 1.5 – 5.5 V |
| R_ON at 3.6 V | 91 mΩ typ / 110 max |
| I_Q at 3.6 V | 150 nA typ |
| I_SD at 3.6 V | 120 nA typ |
| **V_ON (turn on)** | **V_CE − V_IN = −250 … −80 mV** |
| **V_OFF (turn off)** | **V_CE − V_IN = 0 … +80 mV** |
| t_ON at 3.6 V | 40 µs |

> [!danger] CE is a comparator input referenced to VIN, not a logic input — see §9 item 3
> To hold the switch **off**, the datasheet requires **V_CE > V_IN + 80 mV**. With
> V_IN = SENSOR_3.3V = 3.3 V that means CE must reach **3.38 V**. An nRF52840 GPIO
> drives to VDD, which in VDDH mode is the REGOUT0 setting, 3.3 V at the very most.
> **The GPIO cannot turn this switch off.** The brief's line
> `SENSOR_3.3V --> LM66100 --> MCU_3.3V <-- gated by MCU GPIO` does not work as drawn.

---

## 5. BT1 — VARTA CoinPower CP 1254 A4  ⚠️ SUPERSEDED

> [!warning] This is NOT the cell being used. Do not read numbers off it.
> The cell is the **LiPol LPM1254**. This CP1254 section is kept for the
> comparison only. Its **140 mA continuous / 210 mA pulse** figures leaked into
> `PCM-ONBOARD.md` and the U5 netlist note as if they described the current
> cell — corrected 2026-08-30. The LPM1254 is **30 mA max continuous**
> (65 mA on the catalogue page for the 65 mAh variant). See `CELL-SOURCING.md`.
>
> VARTA is ruled out anyway: both A4X parts NRND, no North American CoinPower
> distributor, and no protected variant exists.


Source: **VARTA preliminary data sheet, issue 2020-02-18**, type number **63125**,
cell code INR1254 (`elektronik.ropla.eu/pdf/stock/vmb/cp1254a4.pdf`).

| | Value |
|---|---|
| Chemistry | Graphite / LiNiMnCoO₂ |
| Nominal voltage | 3.7 average, **3.62 min** |
| **Typical capacity** | **77 mAh** at 0.1 C, 4.3 → 3.0 V |
| Nominal capacity | 70 mAh at 0.2 C |
| **Diameter** | **12.1 +0.0 / −0.3** → **12.1 max** |
| **Height** | **5.4 +0.2 / −0.1** → **5.6 max** ← not 5.4 |
| Weight | 1.8 g |
| Charge method | CC + CV |
| **Charge voltage** | **4.30 ± 0.05 V** |
| Initial charge current | 35 standard / 70 fast / 140 rapid mA |
| Charge cut-off current | 1.4 mA |
| Discharge cut-off | **3.0 V** |
| Max pulse discharge | **210 mA @ 2 s** |
| Max continuous discharge | 140 mA |
| **Charge temperature** | **0 to 45 °C** |
| Discharge temperature | −20 to 60 °C |
| Impedance | **< 0.5 Ω @ 1 kHz** |
| Cycle life | > 500 to 80 % of initial |

Three things the brief did not have:

1. **Height max is 5.6 mm, not 5.4.** The housing pocket must be cut for 5.6 or the
   lid will not close on a worst-case cell. Housing v5 is modelled at 5.6 — see
   `HOUSING-V5-NOTES.md`.
2. **VBAT_OV = 4.25 V is safe and slightly conservative.** Charge voltage is
   4.30 ± 0.05, so 4.25 V sits below even the low end of the tolerance band. The
   "max 4.00 V" figure that appears in search results is footnote 3 and applies only
   to the **rapid charge** rate of 140 mA, which this design cannot approach —
   harvest current is on the order of 1 mA.

   > **This paragraph was right, and a later session overrode it anyway.**
   > `NETLIST-V3.md` §B6b (2026-08-28) asserted the cell's limit was 4.00 V —
   > the exact misreading this paragraph warns about — and put 4.00 into
   > `preflight.py` check 15, where it graded every later revision. Corrected
   > 2026-08-28: `CELL_V_CHARGE_MAX = 4.30`.
   >
   > The change B6b made was still *justified*, just not for the stated reason:
   > the old 4.246 V nominal had a **4.295 V worst case sitting on a PCM's
   > 4.30 V trip**. That is the real constraint. **The ceiling on `VBAT_OV` is
   > the PCM's trip minus 150 mV, not the cell** — so it cannot be finalised
   > until the PCM is chosen. See `cad/pcb-v3/NETLIST-V3.md` §B6 and §B6b.
3. **"Cell must not be used without external safety electronics (PCM)."** VARTA states
   this on the face of the datasheet. There is no PCM in the brief's architecture.
   See §9 item 4.

Charge temperature 0–45 °C confirms DESIGN-SPEC §9's instruction to gate charging on
temperature in firmware.

---

## 6. L1 — 22 µH inductor — **NOT VERIFIED, see §9 item 5**

LCSC `C2849435` could not be reached and no vendor drawing was obtained. Height is
unknown, which is the one dimension that matters most here.

For comparison only, **not as a substitution**: TI characterised the BQ25505 with a
**Coilcraft LPS4018-223, 4.0 × 4.0 × 1.8 mm** (SLUSBJ3F §6.6 and §8.1). A 1008
(2.5 × 2.0) part in the same inductance will have materially higher DCR, which costs
boost efficiency at the µA input currents this design runs at. Worth a second look
when the LCSC page is reachable.

---

## 7. Passives

| Ref | Value | Size | Source |
|---|---|---|---|
| R_series ×3 | 1 kΩ | 0402 | DESIGN-SPEC §9 harvest table |
| ROV1 | 5.6 MΩ | **0402** | §2 above; 0402 so it can be hand-swapped |
| ROV2 | 7.5 MΩ | **0402** | §2 above |
| ROK1/2/3 | TBD, sum 11–15 MΩ | 0402 | SLUSBJ3F §6.3 |
| C_IN | 4.7 µF ≥ 6.3 V | 0603 | SLUSBJ3F §6.3 |
| C_STOR | 4.7 µF + 0.1 µF | 0603 + 0402 | SLUSBJ3F §6.3 |
| C_REF | 10 nF **low leakage** | 0402 | SLUSBJ3F §6.3, 9–11 nF window |
| C_SENSOR | **22 µF** | 0805 | DESIGN-SPEC §5 — holds the 200 mA / 4 µs droop to 36 mV |

C1/C2 (1 µF 0402, `C52923`) and C3/C4 (47 µF 0805, `C16780`) land patterns carry
forward unchanged from DESIGN-SPEC §3 — both were checked against Samsung's land
tables and both passed. **C3/C4 body is 1.25 mm tall**, not the common 0.85.

---

## 8. Corrections to existing notes

| Note | Says | Actually |
|---|---|---|
| DESIGN-SPEC §9, NEXT-SESSION Task A | MDBT50Q "not at LCSC" | **JLCPCB lists it as `C5118826`.** Worth confirming — a JLC-catalogued part means an assembly-verified land pattern is available, which would close §9 item 1 outright |
| DESIGN-SPEC §9 | Harvesting PMICs "out of spec above 3.3 V input" | True of BQ25504. **BQ25505 VIN_DC is specified to 5.1 V** |
| DESIGN-SPEC §9 | CP1254 "fails geometrically twice" | Both failures are answered by the v5 riser: height by raising the ceiling to 9.46, diameter by stacking the cell **above** the MCU rather than beside it |
| DESIGN-SPEC §9 power path | 3 × LM66100 ideal diode ORed | Superseded — the 1 kΩ series resistors isolate the three channels, so no ORing parts at all |
| NEXT-SESSION §2 | CP1254 "Ø12.1 × 5.4" | **5.4 +0.2 → model 5.6** |

---

## 9. Not verified — do not draw these until closed

1. **MDBT50Q-1MV2 land pattern and antenna keep-out, in mm.**
   Blocking: the whole of Task E, and the antenna placement in Task C.
   Why it is open: pp. 9–15 of the Ver. K approval sheet are vector drawings with no
   text layer, and the browser pane stopped compositing frames mid-read, so the pages
   could not be re-read at working magnification.
   **Fastest close (about five minutes):** Raytac publishes a *Footprint & Design Guide*
   package — §2.4 of the approval sheet — containing Altium/Eagle/Protel footprints plus
   2D/3D drawings, from the Support page at `raytac.com/download/index.php?index_id=43`.
   Download it and read the footprint file directly; that gives exact pad coordinates
   with no drawing interpretation at all.
   **Alternative close:** open the Ver. K PDF at pp. 9–15 at 200 % or more and read the
   dimensions off the drawing.
   **Third option, possibly best:** if `C5118826` is confirmed at JLCPCB, take their
   assembly-verified land pattern.

2. **How VDDH is brought up within its 100 ms rise-time limit.**
   Raytac §5.2 specifies **t_R VDDH = 100 ms max** from 0 to 3.7 V. Charging a flat
   CP1254 from harvest takes hours, so a direct cell-to-VDDH connection ramps VDDH
   many orders of magnitude too slowly on first power-up.
   The parts to do this properly are already in the design: **BQ25505 VBAT_OK** (pin 13)
   is exactly a "storage is charged enough" digital output, and it can gate a switch
   feeding VDDH so the module sees a fast edge instead of a slow ramp.
   Needs a decision: which switch, and what VBAT_OK / VBAT_OK_HYST thresholds.
   ROK1+ROK2+ROK3 must total 11–15 MΩ.

3. **The LM66100 cannot be turned off by an nRF52 GPIO.** §4 above, with the datasheet
   numbers. Turning the switch off needs V_CE > V_IN + 80 mV = 3.38 V; the GPIO tops
   out at 3.3 V. Turning it *on* works; turning it off does not.
   **The cheapest fix uses a part already traced in this project:** a second
   **TPS7A2033** fed from the cell, output MCU_3.3V, with its **logic-level EN (pin 3)**
   on the GPIO. Same footprint as U3, already verified against DQN0004A, and it deletes
   the LM66100 from the BOM entirely.
   Recorded, not applied — substituting a part is Daniel's call, not an unattended
   session's. Task D's netlist is written to the brief and flags this line.

4. **The CP1254 A4 requires a protection circuit module and there isn't one.**
   VARTA: "Cell must not be used without external safety electronics (PCM)."
   BQ25505's VBAT_OV covers overcharge and firmware can cover undervoltage, but neither
   covers short circuit or the cell's own fault modes, and neither is what VARTA means.
   Decide: source the CP1254 as a tabbed assembly with a PCM fitted, or add a
   protection IC. Both cost board or stack height that is not currently budgeted.

5. **22 µH inductor `C2849435` — package, DCR and height all unknown.** §6 above.

6. **BQ25505 VBAT_OK divider values.** Not specified anywhere in the brief. Needs a
   target: the sensible one is VBAT_OK ≈ 3.1 V rising with hysteresis up to ≈ 3.5 V,
   sitting just above the CP1254's 3.0 V discharge cut-off. Depends on item 2.
