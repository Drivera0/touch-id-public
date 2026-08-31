# HANDOFF — FIRMWARE AUDIT & FLASH READINESS (for Claude Code)

Written 2026-08-31. Hardware is FROZEN: `cad/pcb-v3/pcb-v7-zero-opens.kicad_pcb`
passed the full order gate (preflight 0 blockers) and the fab package in
`cad/v7-release/` verifies clean. Your job is the SOFTWARE side: audit this
repo for firmware, decide what is flashable to the real board, and get the
right code ready. The user is a beginner at electronics — explain, don't assume.

## THE HEADLINE FINDING YOU MUST NOT MISS

**There is no firmware for this board in the repo.** `Firmware and PCB.md`
references github.com/ZimengXiong/tinyTouch — an external ESP32 Arduino `.ino`
from the project's ABANDONED wired architecture. Its pins (FP_TX 43, FP_RX 44,
FP_INT 2) do not exist on this MCU; it has no BLE HID, no harvest power logic.
It is study material, NEVER flash material. If you find any code presented as
"the firmware", check it against the pin table below before believing it.
Anything that doesn't match netlist_v3.py is stale. The likely real task:
write the firmware from scratch (nRF Connect SDK / Zephyr recommended — the
SoftDevice/SDK choice has NOT been made; make it explicitly with the user).

## GROUND RULES (inherited from HANDOVER-OPEN-PADS.md — still binding)

1. NEVER invent a dimension, pin, or part number. Every hardware fact below
   traces to `cad/pcb-v3/netlist_v3.py` (the netlist authority) or
   `datasheets/`. If you need a fact that isn't written down, say so.
2. Do NOT order anything or spend money. The user places all orders.
3. Do NOT delete or overwrite originals. New work = new files. Commit at
   every milestone.
4. A claim only counts when it's verified: firmware claims require a clean
   build; board claims require `cad/pcb-v3/preflight.py`.

## HARDWARE TRUTH — MCU pin map (from netlist_v3.py, U1 = Raytac MDBT50Q-1MV2, nRF52840)

| Signal | nRF pin | Direction | Notes |
|---|---|---|---|
| SENSOR_TX → nRF **RX** | **P0.06** | in | sensor's TX. UART 57600 8N1, 3.3 V TTL |
| nRF **TX** → SENSOR_RX | **P0.08** | out | |
| SENSOR_WAKEUP | **P0.07** | in | finger-detect interrupt, ACTIVE HIGH, low when idle |
| SENSOR_SW_EN | **P0.26** | out | logic-level EN of U4 (TPS7A2033) = sensor **MCU** rail switch |
| VBAT_OK | **P0.27** | in | BQ25505 storage-good. High ≈ VSTOR>3.498 V, low ≈ <3.123 V |
| VBAT_SENSE | **P0.03 / AIN1** | analog | cell voltage divider tap |
| BL_FLAG | **P0.02 / AIN0** | analog | keyboard backlight state flag (J11-4) — ANALOG, not digital |
| SWDIO / SWCLK / nRESET | module pins 51/53/40 | — | J3 pads, see flashing |

Clock: **XL1/XL2 are NOT fitted — no 32.768 kHz crystal.** Firmware MUST
configure the LFCLK source as internal RC (LFRC) with calibration. A default
BLE config expecting LFXO will hang or drift. Sleep budget is ~6 µA total.

## POWER MODEL (get this wrong and the board browns out)

- **VSTOR** is the system rail (cell + BQ25505 boost). U1's VDDH sits on it.
- **U3** (always-on LDO) → SENSOR_3V3: the sensor's finger-detect rail.
  Stays powered ALWAYS (spec: sensor standby 8–12 µA).
- **U4** (switched LDO, EN = P0.26) → SENSOR_MCU_3V3: the sensor's algorithm
  MCU. Firmware turns this on only to enroll/match, off otherwise.
- Sensor spec (HLK-ZW0922 V1.0, `datasheets/` + `cad/pcb-v3/SENSOR-ZW0922.md`):
  - Power OFF interval ≥ **150 ms** before re-powering the sensor MCU.
  - Open the UART only AFTER MCU_3.3V is up (spec forbids the reverse order).
  - On host sleep, drive RX/TX low/pulled-down (leakage through sensor IO).
  - Match flow: WAKEUP rises → power U4 → wait ~100 ms power-on → UART
    commands (image 80–120 ms, features 60–100 ms, compare 200–1300 ms) →
    sleep sensor → U4 off. Storage: 50 prints.
  - FD mode draws 200 mA for 4 µs peaks on SENSOR_3V3 — already handled in
    hardware (LDO + caps); don't add firmware polling that defeats FD.
- **Radio discipline: treat VBAT_OK (P0.27) as permission.** The 80 mAh cell
  allows 80 mA max discharge; BLE TX bursts are fine, but when VBAT_OK is
  low, the harvester says storage is weak — stay in low-power, no radio.
- Harvest only runs when the keyboard backlight is on (see memory/vault:
  300 Ω awake vs 11 kΩ asleep). BL_FLAG (AIN0) tells firmware which world
  it's in. Don't schedule hungry work when backlight is off.

## WHAT THE PRODUCT DOES (target behavior)

Fingerprint-auth module replacing the NuPhy Air75 V3 knob. Finger touch →
sensor match → BLE (HID or GATT — design choice open) tells the paired
computer "identity confirmed" (unlock / type credential — see
`Firmware and PCB.md` for the tinyTouch ideas worth stealing: nonce flow,
Mac helper, Keychain). Bring-up order: (1) blink/advertise hello-world,
(2) power state machine (U4 + VBAT_OK + sleep µA), (3) sensor UART
enroll/match, (4) BLE integration, (5) power budget measurement.

## FLASHING (the part the user asked about — verify code BEFORE this)

- Probe: MuseLab Mini DAPLink-HS (CMSIS-DAP). Tool: **pyOCD**, not nrfjprog:
  `pyocd flash -t nrf52840 build/zephyr/zephyr.hex` (or the merged hex).
- Connection: J3 pads on board bottom, (-8..0, +3.0), 2.0 mm pitch:
  **SWDIO, SWCLK, RESET, VSTOR, GND** (RESET unused by DAPLink flow — park it).
  Printed jig: `cad/v7-release/flash-jig/` (drop board on posts, button ejects).
- **Power: the board must see 3.6 V on VSTOR while flashing** (bench supply
  or the cell; the probe's 3.3 V is NOT enough for full rails; 5 V direct to
  VSTOR is FORBIDDEN — cell is attached to that rail). Wiring picture:
  `cad/v7-release/flash-jig/J3-flashing-hookup.png`.
- After flashing with a bench supply, expect BLE only when VSTOR > ~3.5 V
  (VBAT_OK gating above) — a "dead" radio at 3.3 V is not a bug.

## YOUR DELIVERABLES

1. Inventory: every file in the repo that claims to be or reference firmware,
   marked KEEP (reference) / STALE (old architecture) / MISSING (to write).
2. A pin-map cross-check: any code's pin usage diffed against the table above
   (regenerate truth with `python3 cad/pcb-v3/netlist_v3.py` if in doubt).
3. The SDK decision made WITH the user (recommend nRF Connect SDK/Zephyr;
   board target: raytac_mdbt50q_db_40? No — that's the dev board; define a
   custom board DTS for this PCB, LFRC config included).
4. A firmware skeleton that compiles clean, with the power state machine
   stubbed and every pin from the table in one `board` header/DTS.
5. A step-by-step flash checklist the user can follow at the jig.

Everything hardware: `cad/v7-release/README.md`. Sensor spec:
`HLK-ZW0922 Specification V1.0` (user has the PDF; facts mirrored in
`cad/pcb-v3/SENSOR-ZW0922.md`). Cell: `cad/pcb-v3/CELL-QUOTE-2026-08-31.md`
(protected cell — the PCB has NO protection on it, by design).
