---
title: JLCPCB DFM Report — U1/U2 land pattern defect
type: project
tags:
  - touchid
  - hardware
  - jlcpcb
---

# DFM issue report — order [order #] / Y6

| Field | Value |
|---|---|
| Customer code | [order #] |
| Produce order code | Y6 |
| Customer order ID | 12208316 |
| Gerber file | `fingerprint module-jlcpcb_Y6.zip` |
| Board | 19.60 × 17.60 mm, 2 layer, 1.2 mm, ENIG, 5 pcs + SMT assembly |
| Board coordinate frame | X 90.2 – 109.8 mm, Y 0.0 – 17.6 mm (centre 100.0, 8.8) |

---

## 0. Read this first — placement adjustment cannot fix this

**The defect is in the copper artwork, not in the placement data.**

The CPL X/Y/rotation values for U1 and U2 are correct. The *land patterns
etched into the top copper layer* (`touchid_module.GTL`, with matching
`.GTS` solder mask and `.GTP` paste) do not match the packages of the parts
being assembled. Moving the components will not make them line up with
pads that are the wrong size, the wrong pitch, and in the wrong places.

**Requested action: place order Y6 on hold. Do not start production.**
Corrected Gerber files will be uploaded. Only the top copper, top solder
mask and top paste layers change; board outline, drill, bottom layers,
stackup, finish and quantity all stay as ordered.

---

## 1. U2 — TPS7A2033DQNR, DQN package (X2SON-4, 1.0 × 1.0 mm)

LCSC C46459900. Component centre in the Gerber: **X 92.400, Y 11.800, rotation 0**.

### What is in the file now (incorrect)

| Feature | As drawn |
|---|---|
| Signal pads | 4 × square **0.30 × 0.30 mm** |
| Pad centres | **(±0.52, ±0.52)** from component centre |
| Effective pitch | **1.04 mm** in X, **1.04 mm** in Y |
| Thermal pad | **0.55 × 0.55 mm** square, **not rotated** |
| Solder mask | non-solder-mask-defined |

### What it must be

Source: Texas Instruments package drawing **DQN0004A, 4215302/E (12/2016)**,
"LAND PATTERN EXAMPLE" sheet. Independently confirmed by the KiCad official
library part `Package_SON.pretty/Texas_X2SON-4_1x1mm_P0.65mm.kicad_mod`,
whose geometry matches the TI drawing exactly.

| Feature | Required |
|---|---|
| Pad centres | **(±0.43, ±0.325)** from component centre |
| Pitch | **0.86 mm** in X, **0.65 mm** in Y |
| Pad copper | **0.46 mm (X) × 0.31 mm (Y)**, inner corner chamfered 45° |
| Solder mask opening | **0.36 × 0.21 mm** — this land pattern is **solder-mask defined (SMD)**, mask opening smaller than the copper |
| Mask web | 0.05 mm min all around (per TI solder mask detail) |
| Thermal pad (pin 5) copper | **0.58 × 0.58 mm square rotated 45°** (diamond) |
| Thermal pad mask opening | **0.48 × 0.48 mm** rotated 45° (mask margin −0.05) |
| Thermal paste aperture | approx **0.45 mm** (paste margin −0.065), ~88% coverage per TI stencil sheet |
| Exposed-metal clearance | **0.22 mm typ** between thermal pad and signal pads |

TI's own callouts on the land pattern sheet, for cross-reference:
`4X (0.21)`, `4X (0.36)`, `(0.65)`, `(0.86)`, `(Ø0.48)`, `4X (0.18)`,
`(0.22) TYP EXPOSED METAL CLEARANCE`.

### Consequence if built as-is

Each pad is offset outward by **0.09 mm in X and 0.195 mm in Y**. Overlaying
the drawn pads on the true terminal positions gives roughly **20–25 % of each
terminal over copper**, contacting along a strip only about **0.1 mm wide**.
On a 1 × 1 mm leadless package this means open joints, a skewed part, or a
part that reflows off the land entirely. The thermal pad is also the wrong
shape and orientation, so its clearance to the signal pads is out of spec.

### Pin assignment — must be preserved

TI SBVS338H Figure 4-3, DQN 4-pin, **top view**. This is *not* the SOT-23-5
(DBV) order.

| Pin | Function | Net | Position (from centre) |
|---|---|---|---|
| 1 | OUT | +3V3 | (−0.43, −0.325) |
| 2 | GND | GND | (−0.43, +0.325) |
| 3 | EN | VBAT | (+0.43, +0.325) |
| 4 | IN | VBAT | (+0.43, −0.325) |
| 5 | Thermal pad | GND | (0, 0) |

Corner ordering is unchanged from the current file — only the coordinates and
pad geometry change, so the netlist is unaffected.

---

## 2. U1 — ESP32-C3-MINI-1-N4

LCSC C2838502. Component centre in the Gerber: **X 100.000, Y 8.800, rotation 180**.
Module body 13.2 × 16.6 mm.

### What is in the file now (incorrect)

| Feature | As drawn |
|---|---|
| Pad count | **14** |
| Pad size | **1.6 mm (X) × 0.8 mm (Y)** |
| Pitch | **1.0 mm** |
| Left column | x = −6.1, y = −2.5 … +4.5 (8 pads, 1.0 mm steps) |
| Right column | x = +6.1, y = −1.0, 0.0, +1.0, +2.2, +3.2, +4.2 (6 pads) |

This was a hand-simplified placeholder pattern — it is labelled
`SIMPLIFIED footprint` in the source that generated the board. It is not
derived from any Espressif drawing.

### What it must be

Source: **ESP32-C3-MINI-1 & ESP32-C3-MINI-1U Datasheet v2.2, Figure 11-1
"ESP32-C3-MINI-1 Recommended PCB Land Pattern"**.

| Feature | Required |
|---|---|
| Pad count | **48** |
| Pitch | **0.8 mm** |
| Pad width | **0.4 mm** |
| Layout | per Espressif Figure 11-1, including the thermal pad area and its vias |
| Antenna keep-out | must remain clear of copper (already respected in the current file) |

### Consequence if built as-is

The pitch error is **0.2 mm per pad and cumulative**. By the fourth pad the
offset already exceeds a full pad width, so beyond at most one pad nothing
lands on copper. The pad count is also wrong (14 vs 48). The module cannot be
assembled onto this artwork.

---

## 3. What is *not* wrong

Verified against the CAM output in `[order #]_y6` and correct — no change needed:

- Board profile 19.600 × 17.600 mm from the GKO layer, area 341.3 mm², 1 design
- Drill: 15 × Ø0.30 mm + 2 × Ø2.20 mm, all plated; mounting holes at
  X 91.7 / 108.3, Y 8.8
- 2 layers, 1.2 mm thickness, 1 oz outer copper
- Minimum trace spacing found 0.139 mm (above the 0.127 mm limit)
- Green solder mask, white silkscreen, ENIG, vias tented, no impedance control,
  no countersunk holes
- Top and bottom silkscreen content and orientation
- 99 test points, AutoCAM result 1 (pass)
- Auto-panelisation to 71.6 × 71.6 mm with rails and fiducials — fine as planned

The passing AutoCAM result is consistent with this report: AutoCAM confirms the
board is *manufacturable*, which it is. It does not verify that a land pattern
matches the package of the part being placed on it.

---

## 4. Short version for the DFM comment box

> Please place order [order #] / Y6 on hold — do not start production.
>
> The top-layer land patterns for U1 (ESP32-C3-MINI-1-N4, C2838502) and U2
> (TPS7A2033DQNR, C46459900) in the uploaded Gerber do not match the packages
> of the parts to be assembled. This is a copper artwork error, not a
> placement error, so it cannot be corrected by adjusting component positions.
>
> U2: pads are drawn 0.30 × 0.30 mm at ±0.52/±0.52 mm from centre. TI drawing
> DQN0004A 4215302/E requires 0.46 × 0.31 mm pads at ±0.43/±0.325 mm, a
> solder-mask-defined opening of 0.36 × 0.21 mm, and a 0.58 mm square thermal
> pad rotated 45°.
>
> U1: pads are drawn as 14 pads on 1.0 mm pitch. Espressif's recommended land
> pattern (datasheet v2.2, Figure 11-1) is 48 pads on 0.8 mm pitch, 0.4 mm
> pad width.
>
> I will upload corrected Gerber files. Only top copper, top solder mask and
> top solder paste change — board outline, drill, bottom layers, stackup,
> surface finish and quantity remain as ordered.

---

## References

- TI package drawing DQN0004A 4215302/E — https://www.ti.com/lit/ml/qfnd355c/qfnd355c.pdf
- TPS7A20 datasheet (SBVS338H) — https://www.ti.com/lit/ds/symlink/tps7a20.pdf
- KiCad official footprint `Texas_X2SON-4_1x1mm_P0.65mm` — https://github.com/KiCad/kicad-footprints/blob/master/Package_SON.pretty/Texas_X2SON-4_1x1mm_P0.65mm.kicad_mod
- ESP32-C3-MINI-1 datasheet — https://documentation.espressif.com/esp32-c3-mini-1_datasheet_en.html
