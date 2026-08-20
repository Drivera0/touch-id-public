---
title: Pin Test Results
type: reference
tags:
  - touchid
  - hardware
  - reference
---

# Pin Test Results — 2026-08-18

Raw data: `cad/pin-test-results.csv`. Procedure and pin numbering: [[touchid/Pin Test Procedure|Pin Test Procedure]] (looking into the slot, typing position: J4 = 6-pin left block, J11 = 4-pin right block, top row toward rear, numbered left→right then down).

## Readings

| Pin | GND beep | V wired | V wireless | V off | Verdict |
|---|---|---|---|---|---|
| J4-1 | | 3.293 | 3.293 | 0.00 | pulled-up signal (encoder?) — **not a power rail** |
| J4-2 | | 0.009 | 0.071 | 0.001 | idle-low signal / detect |
| J4-3 | | 3.293 | 3.293 | 0.000 | pulled-up signal (encoder?) |
| J4-4 | | 3.293 | 3.293 | 0.000 | pulled-up signal (encoder press?) |
| J4-5 | **yes** | 0.000 | 0.000 | 0.000 | **GND — confirmed** |
| J4-6 | | 0.001 | 0.000 | 0.000 | driven low / NC |
| J11-1 | | 3.680 | 3.466 | 0.200 | **VBAT (battery rail) — switched by power slider** |
| J11-2 | | 3.680 | 3.466 | 0.236 | **VBAT** |
| J11-3 | | 3.685 | 3.466 | 0.280 | **VBAT** |
| J11-4 | | 0.332 | 0.312 | 0.003 | floating / detect — leave open |

3.680 V wired vs 3.466 V wireless = classic Li-ion behavior (charger present vs battery at partial charge). The 3.293 V on J4-1/3/4 matches CH592 3.3 V logic pull-ups, not a supply.

## Power architecture — DECIDED

The module powers from the keyboard: **J11-1 + J11-2 + J11-3 tied together = VBAT in** (parallel pins share pogo contact current), **J4-5 = GND**. All other pins left unconnected. On the module PCB: VBAT → 3.3 V LDO (low-dropout, ≥250 mA, e.g. XC6220/TPS7A02 class) → ESP32-C3-MINI-1 + fingerprint sensor. Bulk cap (≥100 µF) near the LDO input to ride out pogo-contact bounce and BLE TX peaks.

No keyboard data lines are used → no keyboard firmware modification needed. The module is a self-contained BLE device, per [[touchid/Architecture and Design|Architecture and Design]].

## Still to measure (from the procedure)

- [ ] **Sleep sweeps** (v_sleep1_lightoff, v_sleep2_deep) on J11-1 — does VBAT survive keyboard sleep? Decides whether the module needs deep-sleep + fast-boot handling.
- [ ] **Load test** on J11-1 (100–330 Ω to J4-5): confirm the rail holds ≥3.3 V under load through the pogo pins.
- [ ] Continuity: confirm J11-1/2/3 beep to each other (same rail, not three separate nets).

## Related

- [[touchid/Hardware Teardown|Hardware Teardown]]
- [[touchid/TouchID Module Design|TouchID Module Design]]
- [[touchid/Firmware and PCB|Firmware and PCB]]
