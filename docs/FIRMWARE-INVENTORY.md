# FIRMWARE INVENTORY — audit of the tinyTouch fork (2026-08-31)

Every file that claimed to be or reference firmware, per HANDOFF-FIRMWARE.md
deliverable 1. Verdict confirmed by pin-map diff against
`cad/pcb-v3/netlist_v3.py` (regenerated 2026-08-31 — matches the handoff
table exactly).

## The headline, confirmed

**Nothing in the fork was flashable to this board.** Both firmwares target
ESP32 (Xtensa/RISC-V, Espressif SDKs); the board is an nRF52840
(Raytac MDBT50Q-1MV2, ARM Cortex-M4). Wrong architecture before pins even
enter into it.

## Pin-map cross-check (deliverable 2)

| signal | board truth (netlist_v3.py) | tiny_touch_keyboard.ino | verdict |
|---|---|---|---|
| sensor TX → MCU RX | P0.06 | GPIO 43 (`FP_TX_PIN`) | ✗ pin doesn't exist on nRF |
| MCU TX → sensor RX | P0.08 | GPIO 44 (`FP_RX_PIN`) | ✗ |
| finger-detect INT | P0.07 | GPIO 2 (`FP_INT_PIN`) | ✗ |
| sensor MCU rail switch | P0.26 (SENSOR_SW_EN) | — none; sensor always powered | ✗ no harvest power logic |
| VBAT_OK | P0.27 | — | ✗ absent |
| VBAT_SENSE | P0.03/AIN1 | — | ✗ absent |
| BL_FLAG | P0.02/AIN0 | — | ✗ absent |
| link | BLE | USB wired HID + serial | ✗ no BLE anywhere |
| UART | 57600 8N1 | 57600 8N1 | ✓ only survivor |

## File verdicts

| was | verdict | now |
|---|---|---|
| `firmware/tiny_touch_keyboard/` (ESP32 .ino) | STALE — abandoned wired architecture. Study material: 0xEF01 sensor flow, HMAC/AES-CTR session crypto, nonce replay protection | `reference/tinytouch/keyboard-firmware/` |
| `firmware/tiny_touch_smartcard/` (ESP-IDF, USB CCID/PIV) | STALE — USB smartcard, no USB on this product | deleted |
| `software/macos-helper/` | STALE as code, KEEP as design source: nonce flow, Keychain, launchd helper | `reference/tinytouch/macos-helper/` |
| `web/flasher/`, `web/recovery/` (+ prebuilt ESP32 .bins) | STALE — esptool-js serial flashing; nRF52840 flashes over SWD, no serial bootloader | deleted |
| `tinytouch` CLI, `packaging/`, `software/api/`, `tests/` | STALE — upstream's release/distribution machinery | deleted |
| `.github/`, `VERSION`, `hardware/case/` | not ours (workflows, funding, upstream case) | deleted |
| **board firmware** | **MISSING → written** | `firmware/app/` + `firmware/boards/` |

## SDK decision (deliverable 3)

**Zephyr RTOS, upstream v4.2.0** (nRF Connect SDK is Zephyr + Nordic layers;
upstream alone fully supports nRF52840 BLE and is a lighter install).
No SoftDevice — Zephyr's open-source BLE stack. Revisit to NCS only if a
Nordic-only feature is needed. Board target: **`touchid_module/nrf52840`**,
a custom board (the Raytac dev-board target is NOT this PCB) with:

- LFCLK = internal RC + calibration (**no crystal fitted** — XL1/XL2 open)
- console on SEGGER RTT (the only UART belongs to the sensor)
- U4 modeled as a `regulator-fixed` with the spec's 150 ms off / 100 ms
  settle baked into the DTS so code can't violate the sequencing
- every pin from the handoff table in `touchid_module.dts` (deliverable 4)

## Still open

- **ZW0922 byte-level UART protocol** — in the spec PDF only; stubs in
  `sensor_zw0922.c` return -ENOSYS until filled in against it. Do NOT
  assume the 0xEF01 family from the .ino applies.
- **HID vs custom GATT** for the auth report (bring-up step 4).
- BL_FLAG voltage thresholds — measure on real hardware.
