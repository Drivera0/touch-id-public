# Firmware

The firmware for the knob (Zephyr RTOS on the nRF52840) is **closed source**
and isn't in this repository.

- **Design docs** are public: [sensor protocol](../docs/firmware/SENSOR-PROTOCOL.md),
  [auth crypto](../docs/firmware/AUTH-CRYPTO.md), [flashing](../docs/firmware/FLASHING.md) and
  [the fork audit](../docs/firmware/FIRMWARE-INVENTORY.md).
- **Prebuilt firmware** will be published as `.hex` files under this repo's
  [Releases](https://github.com/Drivera0/touch-id-public/releases) once it has run on real hardware. Each release
  includes `SHA256SUMS` so you can check the download.

Status: not yet built for or run on a real board. See
[Project status](../README.md#project-status).
