---
title: TouchID v3 netlist
type: project
tags:
  - touchid
  - pcb
  - netlist
updated: 2026-08-27
---

# TouchID v3 netlist

**Generated from `netlist_v3.py` by `export_netlist.py` — do not hand-edit.**
Edit the Python and re-run, or the two will disagree.

48 parts · 186 pins · 52 deliberate no-connects · 30 nets · no single-pin nets

> [!warning] Structurally complete is not the same as settled
> Every pin is accounted for and no net has fewer than two connections. The
> six flags at the bottom are open **design** questions, not wiring errors.

---

## Nets

| Net | # | Connections |
|---|---|---|
| `GND` | 41 | U1-1, U1-2, U1-15, U1-33, U1-55, U1-32, U2-1, U2-3, U2-5, U2-6, U2-15, U2-16, U2-17, U2-21, U3-2, U3-5, U4-2, U4-5, J4-5, J2-6, J3-5, TP8-1, TP9-1, TP10-1, ROV1-2, ROK1-2, C1-2, C2-2, C3-2, C4-2, C5-2, C6-2, C7-2, C8-2, C9-2, C10-2, R5-2, C12-2, C13-2, U5-4, R9-2 |
| `VSTOR` | 11 | U1-30, U2-19, U3-3, U3-4, U4-4, J3-4, TP2-1, C2-1, C3-1, C10-1, R4-1 |
| `VIN_DC` | 7 | U2-2, TP1-1, R1-2, R2-2, R3-2, L1-2, C1-1 |
| `SENSOR_3V3` | 5 | U3-1, J2-1, TP5-1, C6-1, C7-1 |
| `VBAT` | 5 | U2-18, BT1-1, TP3-1, C5-1, R8-1 |
| `SENSOR_MCU_3V3` | 4 | U4-1, J2-3, TP6-1, C8-1 |
| `VBAT_OK` | 4 | U1-16, U2-13, TP4-1, R7-1 |
| `VBAT_SENSE` | 4 | U1-9, R4-2, R5-1, C12-1 |
| `BL_FLAG` | 3 | U1-11, R6-2, C13-1 |
| `BL_RETURN` | 3 | J11-4, TP7-1, R6-1 |
| `CELL_NEG` | 3 | BT1-2, U5-1, C14-2 |
| `OK_HYST` | 3 | U2-11, ROK2-1, ROK3-2 |
| `OK_PROG` | 3 | U2-12, ROK1-1, ROK2-2 |
| `PCM_VDD` | 3 | U5-2, R8-2, C14-1 |
| `RESET` | 3 | U1-40, J3-3, R7-2 |
| `VBAT_OV_SET` | 3 | U2-7, ROV1-1, ROV2-2 |
| `VRDIV` | 3 | U2-8, ROV2-1, ROK3-1 |
| `HARV_1` | 2 | J11-1, R1-1 |
| `HARV_2` | 2 | J11-2, R2-1 |
| `HARV_3` | 2 | J11-3, R3-1 |
| `LX` | 2 | U2-20, L1-1 |
| `NRF_VDD` | 2 | U1-28, C9-1 |
| `PCM_VM` | 2 | U5-3, R9-1 |
| `SENSOR_RX` | 2 | U1-24, J2-5 |
| `SENSOR_SW_EN` | 2 | U1-19, U4-3 |
| `SENSOR_TX` | 2 | U1-22, J2-4 |
| `SENSOR_WAKEUP` | 2 | U1-23, J2-2 |
| `SWCLK` | 2 | U1-53, J3-2 |
| `SWDIO` | 2 | U1-51, J3-1 |
| `VREF_SAMP` | 2 | U2-4, C4-1 |

---

## Parts, pin by pin

### BT1 — Cell wire pads — bare 1254-class cell + factory leads

> 3.0 V discharge cut-off, 4.30 +-0.05 V charge, 210 mA pulse (CP1254 A4X figures). Two O1.4 wire-landing pads on 1.6 mm pitch — NOT a cell footprint. Solder the cell's LEADS here; never put an iron on the cell (CoinPower handbook 8.7). 4.30 V is the cell's charge voltage; the 4.00 V in some notes is the RAPID-charge footnote and does not apply here.

| Pin | Net |
|---|---|
| 1 | `VBAT` |
| 2 | `CELL_NEG` |

### C1 — 10uF 10V X5R 0402

> CIN. Was 4.7uF — Murata's DC-bias curve showed that part delivering only ~2.3-2.8 uF at this board's 3.9 V, against the BQ25505's 4.7 uF minimum. Specify by C_eff, never by marked value.

| Pin | Net |
|---|---|
| 1 | `VIN_DC` |
| 2 | `GND` |

### C2 — 10uF 10V X5R 0402

> CSTOR. Same change as C1. 0603 was not an option — it collides with 62 neighbouring pads/tracks here (12 at C1), so the land is fixed at 0402 and more nominal capacitance in the same land was the only lever.

| Pin | Net |
|---|---|
| 1 | `VSTOR` |
| 2 | `GND` |

### C3 — 0.1uF 0402

> CSTOR HF

| Pin | Net |
|---|---|
| 1 | `VSTOR` |
| 2 | `GND` |

### C4 — 10nF 0402 low-leak

> CREF, 9-11 nF window

| Pin | Net |
|---|---|
| 1 | `VREF_SAMP` |
| 2 | `GND` |

### C5 — 10uF 16V X5R 0603

> CBAT bulk beside the cell

| Pin | Net |
|---|---|
| 1 | `VBAT` |
| 2 | `GND` |

### C6 — 1uF 0402

> LDO input side of U3 is VSTOR; this is OUT

| Pin | Net |
|---|---|
| 1 | `SENSOR_3V3` |
| 2 | `GND` |

### C7 — 22uF 10V X5R 0603

> ZW0905 200 mA / 4 us scan transient. REQUIREMENT: ripple < 200 mV (Hi-Link), so C_eff at 3.3 V bias must be >= 4 uF, target >= 8 uF. Do NOT substitute a 6.3 V part -- it derates onto the floor.

| Pin | Net |
|---|---|
| 1 | `SENSOR_3V3` |
| 2 | `GND` |

### C8 — 1uF 0402

| Pin | Net |
|---|---|
| 1 | `SENSOR_MCU_3V3` |
| 2 | `GND` |

### C9 — 1uF 0402

> REG0 output decoupling

| Pin | Net |
|---|---|
| 1 | `NRF_VDD` |
| 2 | `GND` |

### C10 — 0.1uF 0402

> VDDH decoupling, at the module

| Pin | Net |
|---|---|
| 1 | `VSTOR` |
| 2 | `GND` |

### C12 — 10nF 0402

> SAADC sampling reservoir

| Pin | Net |
|---|---|
| 1 | `VBAT_SENSE` |
| 2 | `GND` |

### C13 — 10nF 0402

| Pin | Net |
|---|---|
| 1 | `BL_FLAG` |
| 2 | `GND` |

### C14 — 0.1uF 0402

> Datasheet C1. Across VDD and S1, for supply-voltage fluctuation.

| Pin | Net |
|---|---|
| 1 | `PCM_VDD` |
| 2 | `CELL_NEG` |

### J2 — Sensor pads, HLK-ZW0922 (was ZW0905 — discontinued)

> DESIGN-SPEC §5 as corrected 2026-08-27. The old table was the ZW0901's, reversed end-for-end. **2026-08-28: the ZW0905 is DISCONTINUED; the replacement HLK-ZW0922 has this SAME pin order** (spec V1.0 §4.3), so no board change. See cad/pcb-v3/SENSOR-ZW0922.md.

| Pin | Net |
|---|---|
| 1 | `SENSOR_3V3` |
| 2 | `SENSOR_WAKEUP` |
| 3 | `SENSOR_MCU_3V3` |
| 4 | `SENSOR_TX` |
| 5 | `SENSOR_RX` |
| 6 | `GND` |

### J3 — SWD pads

> Pads, not a connector. Pin 4 is the rail, so a programmer can see target voltage.

| Pin | Net |
|---|---|
| 1 | `SWDIO` |
| 2 | `SWCLK` |
| 3 | `RESET` |
| 4 | `VSTOR` |
| 5 | `GND` |

### J4 — Keyboard slot, 6-pin pogo block (LEFT)

> J4-1/3/4 must stay unconnected: loading them in knob mode generated volume/mute events (session 3).

| Pin | Net |
|---|---|
| 1 | *(no connect)* |
| 2 | *(no connect)* |
| 3 | *(no connect)* |
| 4 | *(no connect)* |
| 5 | `GND` |
| 6 | *(no connect)* |

### J11 — Keyboard slot, 4-pin pogo block (RIGHT)

> 1/2/3 are the RGB LED anodes. 4 is the LED common return.

| Pin | Net |
|---|---|
| 1 | `HARV_1` |
| 2 | `HARV_2` |
| 3 | `HARV_3` |
| 4 | `BL_RETURN` |

### L1 — 22uH

> LBOOST -> VIN_DC. Package NOT verified.

| Pin | Net |
|---|---|
| 1 | `LX` |
| 2 | `VIN_DC` |

### R1 — 1k 0402

> caps awake draw to ~1.1 mA/pin

| Pin | Net |
|---|---|
| 1 | `HARV_1` |
| 2 | `VIN_DC` |

### R2 — 1k 0402

| Pin | Net |
|---|---|
| 1 | `HARV_2` |
| 2 | `VIN_DC` |

### R3 — 1k 0402

| Pin | Net |
|---|---|
| 1 | `HARV_3` |
| 2 | `VIN_DC` |

### R4 — 4.7M 0402

| Pin | Net |
|---|---|
| 1 | `VSTOR` |
| 2 | `VBAT_SENSE` |

### R5 — 1M 0402

| Pin | Net |
|---|---|
| 1 | `VBAT_SENSE` |
| 2 | `GND` |

### R6 — 100k 0402

> series protection only

| Pin | Net |
|---|---|
| 1 | `BL_RETURN` |
| 2 | `BL_FLAG` |

### R7 — 1k 0402

> 1k so an SWD programmer can still override RESET

| Pin | Net |
|---|---|
| 1 | `VBAT_OK` |
| 2 | `RESET` |

### R8 — 330R 0402

> Datasheet R1. VDD series protection; 330R typ, 470R max.

| Pin | Net |
|---|---|
| 1 | `VBAT` |
| 2 | `PCM_VDD` |

### R9 — 2.7k 0402

> Datasheet R2. FUNCTIONAL, not optional -- every over-current figure in the datasheet is measured with R2 = 2.7k. Omit it and 0.315 A is not 0.315 A.

| Pin | Net |
|---|---|
| 1 | `PCM_VM` |
| 2 | `GND` |

### ROK1 — 4.53M 0402

> VBAT_OK falling = 3.12 V

| Pin | Net |
|---|---|
| 1 | `OK_PROG` |
| 2 | `GND` |

### ROK2 — 7.15M 0402

| Pin | Net |
|---|---|
| 1 | `OK_HYST` |
| 2 | `OK_PROG` |

### ROK3 — 1.33M 0402

> VBAT_OK rising = 3.47 V

| Pin | Net |
|---|---|
| 1 | `VRDIV` |
| 2 | `OK_HYST` |

### ROV1 — 6.04M 0402 1%

> VBAT_OV = 1.5*1.21*(1+6.98/6.04) = 3.912 V, 3.955 V worst case. The cell's charge voltage is 4.30 V, NOT the 4.00 V some notes claimed — 4.00 is the rapid-charge footnote. The binding ceiling is the PCM's over-charge trip minus 150 mV, so pick the cell's PCM before retuning this divider.

| Pin | Net |
|---|---|
| 1 | `VBAT_OV_SET` |
| 2 | `GND` |

### ROV2 — 6.98M 0402 1%

| Pin | Net |
|---|---|
| 1 | `VRDIV` |
| 2 | `VBAT_OV_SET` |

### TP1 — test point, B.Cu

> keep on the -Y half — the +Y half is the antenna keep-out

| Pin | Net |
|---|---|
| 1 | `VIN_DC` |

### TP2 — test point, B.Cu

> keep on the -Y half — the +Y half is the antenna keep-out

| Pin | Net |
|---|---|
| 1 | `VSTOR` |

### TP3 — test point, B.Cu

> keep on the -Y half — the +Y half is the antenna keep-out

| Pin | Net |
|---|---|
| 1 | `VBAT` |

### TP4 — test point, B.Cu

> keep on the -Y half — the +Y half is the antenna keep-out

| Pin | Net |
|---|---|
| 1 | `VBAT_OK` |

### TP5 — test point, B.Cu

> keep on the -Y half — the +Y half is the antenna keep-out

| Pin | Net |
|---|---|
| 1 | `SENSOR_3V3` |

### TP6 — test point, B.Cu

> keep on the -Y half — the +Y half is the antenna keep-out

| Pin | Net |
|---|---|
| 1 | `SENSOR_MCU_3V3` |

### TP7 — test point, B.Cu

> keep on the -Y half — the +Y half is the antenna keep-out

| Pin | Net |
|---|---|
| 1 | `BL_RETURN` |

### TP8 — test point, B.Cu

> keep on the -Y half — the +Y half is the antenna keep-out

| Pin | Net |
|---|---|
| 1 | `GND` |

### TP9 — test point, B.Cu

> keep on the -Y half — the +Y half is the antenna keep-out

| Pin | Net |
|---|---|
| 1 | `GND` |

### TP10 — test point, B.Cu

> keep on the -Y half — the +Y half is the antenna keep-out

| Pin | Net |
|---|---|
| 1 | `GND` |

### U1 — Raytac MDBT50Q-1MV2 (nRF52840)

> 17/18 = XL1/XL2 left NC: internal LFRC, no 32.768 kHz crystal. Saves a 3215 crystal + 2 caps; costs ~2 uA of the 6 uA sleep budget.

| Pin | Net |
|---|---|
| 1 | `GND` |
| 2 | `GND` |
| 3 | *(no connect)* |
| 4 | *(no connect)* |
| 5 | *(no connect)* |
| 6 | *(no connect)* |
| 7 | *(no connect)* |
| 8 | *(no connect)* |
| 9 | `VBAT_SENSE` |
| 10 | *(no connect)* |
| 11 | `BL_FLAG` |
| 12 | *(no connect)* |
| 13 | *(no connect)* |
| 14 | *(no connect)* |
| 15 | `GND` |
| 16 | `VBAT_OK` |
| 17 | *(no connect)* |
| 18 | *(no connect)* |
| 19 | `SENSOR_SW_EN` |
| 20 | *(no connect)* |
| 21 | *(no connect)* |
| 22 | `SENSOR_TX` |
| 23 | `SENSOR_WAKEUP` |
| 24 | `SENSOR_RX` |
| 25 | *(no connect)* |
| 26 | *(no connect)* |
| 27 | *(no connect)* |
| 28 | `NRF_VDD` |
| 29 | *(no connect)* |
| 30 | `VSTOR` |
| 31 | *(no connect)* |
| 32 | `GND` |
| 33 | `GND` |
| 34 | *(no connect)* |
| 35 | *(no connect)* |
| 36 | *(no connect)* |
| 37 | *(no connect)* |
| 38 | *(no connect)* |
| 39 | *(no connect)* |
| 40 | `RESET` |
| 41 | *(no connect)* |
| 42 | *(no connect)* |
| 43 | *(no connect)* |
| 44 | *(no connect)* |
| 45 | *(no connect)* |
| 46 | *(no connect)* |
| 47 | *(no connect)* |
| 48 | *(no connect)* |
| 49 | *(no connect)* |
| 50 | *(no connect)* |
| 51 | `SWDIO` |
| 52 | *(no connect)* |
| 53 | `SWCLK` |
| 54 | *(no connect)* |
| 55 | `GND` |
| 56 | *(no connect)* |
| 57 | *(no connect)* |
| 58 | *(no connect)* |
| 59 | *(no connect)* |
| 60 | *(no connect)* |
| 61 | *(no connect)* |

### U2 — TI BQ25505

> VSTOR (19) is the load rail; the cell sits on VBAT_SEC (18). The brief says 'BQ25505 VBAT <-> cell' but the part has no pin called VBAT — this is TI's own topology, Figure 16.

| Pin | Net |
|---|---|
| 1 | `GND` |
| 2 | `VIN_DC` |
| 3 | `GND` |
| 4 | `VREF_SAMP` |
| 5 | `GND` |
| 6 | `GND` |
| 7 | `VBAT_OV_SET` |
| 8 | `VRDIV` |
| 9 | *(no connect)* |
| 10 | *(no connect)* |
| 11 | `OK_HYST` |
| 12 | `OK_PROG` |
| 13 | `VBAT_OK` |
| 14 | *(no connect)* |
| 15 | `GND` |
| 16 | `GND` |
| 17 | `GND` |
| 18 | `VBAT` |
| 19 | `VSTOR` |
| 20 | `LX` |
| 21 | `GND` |

### U3 — TI TPS7A2033 3.3 V LDO (sensor rail)

> Always on. Feeds the ZW0905's 10 uA standby rail.

| Pin | Net |
|---|---|
| 1 | `SENSOR_3V3` |
| 2 | `GND` |
| 3 | `VSTOR` |
| 4 | `VSTOR` |
| 5 | `GND` |

### U4 — TI TPS7A2033 3.3 V LDO (switched sensor-MCU rail)

> Fed from VSTOR rather than cascaded off SENSOR_3V3: cascading would leave no headroom, and this also keeps the sensor's 25 mA scan current off the always-on standby rail.

| Pin | Net |
|---|---|
| 1 | `SENSOR_MCU_3V3` |
| 2 | `GND` |
| 3 | `SENSOR_SW_EN` |
| 4 | `VSTOR` |
| 5 | `GND` |

### U5 — Mitsumi MC3651DF1AAM cell protection, PLP-4E

> Over-charge 4.280 V, over-discharge 2.700 V, discharge over-current 0.315 A -- 2.2x the cell's 140 mA rating, and the reason this part beat the AP6683's 0.9 A. Iq 3.0 uA typ / 4.5 max = 6.7 % of the 4.0 mWh/day budget. Digi-Key 2508-MC3651DF1AAMCT-ND, US$1.33 at qty 1.

| Pin | Net |
|---|---|
| 1 | `CELL_NEG` |
| 2 | `PCM_VDD` |
| 3 | `PCM_VM` |
| 4 | `GND` |
| 5 | *(no connect)* |

---

## Flags — carried from `PART-LIBRARY.md` §9

These print on every run of `netlist_v3.py`. They are not cosmetic.

### BL_FLAG / R6

NEXT-SESSION specifies '1M/220k' on J11-4. The MEASUREMENTS say that cannot work: J11-4 reads 0.316 V awake and 0.000 V asleep (Pin Test Results, 3-6 ohm source). Both are below any digital V_IL, so a GPIO cannot tell them apart, and a 1M/220k divider would shrink 0.32 V to 0.06 V. This netlist uses a 100k series resistor into an SAADC pin and reads it as an ANALOG value, threshold ~0.15 V.

### B6  BT1 PCM — RESOLVED AS A PROCUREMENT ITEM. It cannot go on this board.

VARTA CoinPower handbook 6.3: a CoinPower cell MUST run with a PCM providing over-charge, over-discharge, over-current AND short-circuit protection. It names acceptable parts: SGM41100V, Ricoh R5613L, Seiko S8211CAY/S8200A, Mitsumi MM3077LY, TI BQ29700/29707, Diodes AP9211. MEASURED on pcb-v3: 9.1 % of the top layer is free, and there is NO free spot anywhere -- not even 1.3 x 1.3 mm -- where a VIA IS LEGAL. Every remaining gap sits over a J4/J11 pogo pad, and a through-hole via there exits through the mating contact. The AP9211 (2.0 x 3.0, the only single-chip option, FETs included) does not fit at all. So the PCM goes ON THE CELL: buy the CP1254 as a protected, tabbed assembly and solder its two leads to BT1's wire pads. That also retires the 'VARTA publishes no tab geometry' warning, because the assembly's leads are specified by whoever builds it. IF a future revision puts the PCM on the board instead, it needs ~2.0 x 3.0 mm WITH via access, which means freeing area -- most plausibly a narrower BLE module, since U1 is 10.5 x 15.5 on a 19.3 mm square.

### B6b VBAT_OV WAS OVERCHARGING THE CELL — FIXED

ROV1/ROV2 were 5.6M/7.5M, giving VBAT_OV = 4.246 V. The CP1254 A4's maximum charging voltage is 4.00 +-0.05 V, so the charger was set 246 mV ABOVE the cell limit -- and only 54 mV under the 4.30 V over-charge trip of the very PCM that B6 adds, which would have made the safety device the working regulator. Now 6.04M/6.98M = 3.912 V nominal, 3.955 V worst case with 1 % parts.

### Load budget grew — 3.3 -> 4.0 mWh/day

The always-on LDO's own quiescent current was never counted. TPS7A20 IGND is 6.5 uA typ / 10 uA over -40..85 C, against the sensor's 10 uA standby. Add the cell-sense divider (4.7M+1M across VSTOR = 0.75 uA). New total ~4.0 mWh/day: scans 1.93, sensor standby 0.89, U3 quiescent 0.58, nRF sleep 0.53, divider 0.07. Harvest still covers it about 4.7x on four hours of backlight, down from 6x. U4 disabled adds nothing (0.07 uA).

