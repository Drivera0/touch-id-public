# FLASHING CHECKLIST — J3, DAPLink, pyOCD

For the jig. Facts trace to HANDOFF-FIRMWARE.md; wiring picture:
`cad/v7-release/flash-jig/J3-flashing-hookup.png` (in the vault).

## Before you touch the board

- [ ] Firmware verified: it was built for `touchid_module/nrf52840` from
      `firmware/app/` in THIS repo. Anything else (especially any ESP32
      `.bin` / `.ino`) is never flash material.
- [ ] Build is clean: `west build` finished with no errors, hex exists at
      `build/zephyr/zephyr.hex`.

## Power — read twice

- [ ] Board must see **3.6 V on VSTOR** while flashing. Bench supply or the
      cell. The probe's 3.3 V is NOT enough for full rails.
- [ ] **NEVER 5 V direct to VSTOR** — the cell hangs on that rail.

## Hookup (J3 pads, board bottom, 2.0 mm pitch)

- [ ] Drop the board on the jig posts (`cad/v7-release/flash-jig/`).
- [ ] SWDIO, SWCLK, GND to the MuseLab Mini DAPLink-HS. RESET is unused by
      the DAPLink flow — park it. VSTOR from the bench supply, not the probe.

## Flash

```sh
pip install pyocd          # once
pyocd flash -t nrf52840 build/zephyr/zephyr.hex
```

(pyOCD, not nrfjprog — the probe is CMSIS-DAP.)

## After

- [ ] RTT console for logs: `pyocd rtt -t nrf52840` (the sensor owns the
      only UART; there is no serial console).
- [ ] Expect BLE advertising ("knob-fp-dev") only when VSTOR > ~3.5 V —
      VBAT_OK gates the radio. **A dead radio at 3.3 V is not a bug**; the
      boot log will say `VBAT_OK low at boot: not advertising`.

## WSL note

USB probes need forwarding into WSL: on Windows, `usbipd list` then
`usbipd attach --wsl --busid <id>` (install usbipd-win once). Or run pyOCD
from Windows Python directly — the hex file is the same.
