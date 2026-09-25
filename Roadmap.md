---
title: Roadmap
type: plan
tags:
  - touchid
  - plan
---

# Roadmap

> [!info] Principle
> Each phase is self-contained and teaches a distinct skill. Do them in order — every step de-risks the next. Fork tinyTouch first and keep everything in git on a **personal** account (see privacy note below).

## Phase 0 — Pin test ⟵ current
Run [[touchid/Pin Test Procedure|the pin test]]. Deliverable: `pin-test-results.csv` + `slot-labeled.jpg` + `knob-underside.jpg`. Decides the power strategy for everything after.

## Phase 1 — Wired prototype (works with today's code)
- [ ] Buy parts (~$25): XIAO ESP32-S3 dev board, ZW101 sensor, jumper wires, breadboard
- [ ] Wire per firmware pins (UART 57600 + INT), flash tinyTouch, set up the Mac helper + Keychain
- [ ] Confirm enroll → touch → password typed over USB
- *Skill: toolchain, HID, the sensor protocol*

## Phase 2 — Finger-to-secret mapping
- [ ] Map each of the 5 slots to a different secret (Mac pw / SSH passphrase / etc.)
- *Skill: reading & modifying the codebase — see idea in [[touchid/Architecture and Design|Architecture and Design]]*

## Phase 3 — Windows helper (if needed)
- [ ] Port the Python helper to Windows Credential vault (or dumb stored-password mode)

## Phase 4 — Bluetooth (v2)
- [ ] Add BLE-keyboard mode on the ESP32 + BLE listener in the helper
- [ ] Requires the state-machine refactor from [[touchid/Firmware and PCB|Firmware and PCB]]
- [ ] Combine with keyboard-pin power (if Phase 0 found a usable rail) → fully wireless
- *Skill: BLE, event-driven firmware*

## Phase 5 — Deep sleep + secure boot
- [ ] INT-wake deep sleep (battery life)
- [ ] Enable flash encryption + secure boot (protect the pairing key)
- *Skill: low-power design, hardware security*

## Phase 6 — Custom PCB (v1 board)
- [ ] Design in KiCad (or atopile → KiCad) around ESP32-S3-MINI-1
- [ ] Custom pogo-pad footprint for the slot; antenna keep-out toward plastic
- [ ] Housing that screws into the slot like the knob; fab 5 at JLCPCB
- *Skill: schematic + layout + mechanical fit*

## Phase 7 (stretch) — Real security key
- [ ] Hold actual SSH keys / act as a FIDO2 authenticator (passkeys, `ssh -sk`)
- [ ] Possibly migrate to nRF52840
- *Serious protocol work — long-term*

## If selling (any point after Phase 1)
- [ ] Keep the MIT notice + credit Zimeng Xiong
- [ ] FCC: stay on the pre-certified MINI-1 module
- [ ] Product name avoids "Touch ID" / "tinyTouch"
- Details in [[touchid/Firmware and PCB|Firmware and PCB]]

---

> [!note] Privacy note (school account)
> Keep this project on a **personal** device/accounts, not the school Microsoft/OneDrive account — school IT admins can access anything stored or synced through that account. Local git + personal GitHub keeps it invisible to them. The login is the leak, not the app.

## Related
- [[touchid/README|Project README]]
- [[touchid/Architecture and Design|Architecture and Design]]
- [[touchid/Firmware and PCB|Firmware and PCB]]
