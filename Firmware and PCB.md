---
title: Firmware and PCB
type: reference
tags:
  - touchid
  - firmware
  - pcb
  - reference
---

# Firmware and PCB

## tinyTouch code review

Repo: https://github.com/ZimengXiong/tinyTouch — one `.ino` firmware + one Python helper. Good hobby code with unusually thoughtful security; great to learn from *because* it has clear places to improve.

### What's genuinely good
- **Security core** better than most hobby projects: every message authenticated (HMAC-SHA256), a **fresh AES-CTR session key per touch**, **replay protection** (nonce tracking), password **wiped from RAM** right after typing.
- Clean single-file firmware; readable separation of sensor / crypto / typing.
- Sensor protocol is the standard `0xEF01` family (GenImg, Img2Tz, Search, Match), LED command `0x3C`. Enrolls 5 fingers; LED ring gives status colours (purple idle / white scan / green match / red fail).

### Where it can improve (each = a lesson)
- [ ] **Deep sleep (highest value for battery use).** Current loop polls every 25 ms, never sleeps (~20–40 mA idle). On keyboard power that drains the battery. Fix: sleep until the sensor's INT "finger touched" wire wakes the chip → near-zero idle. *Lesson: interrupts + sleep modes.*
- [ ] **Memory habits.** Uses Arduino `String` everywhere (fragmentation risk on long-running devices). Rewrite hot paths with fixed buffers. *Lesson: embedded memory discipline.*
- [ ] **Hardcoded values.** Device serial, pins, timings baked in (helper only recognizes *his* ESP32 serial `B8F862FB478C`). Make configurable — easy first contribution.
- [ ] **Unprotected key.** Pairing key sits in plaintext flash; readable with a $5 cable. The S3 supports **flash encryption + secure boot** (README winks at it) — enabling them is a meaty, high-value security upgrade.
- [ ] **Blocking structure.** One long sequence; nothing else runs mid sensor-chat. Refactor to a **state machine** — becomes necessary anyway once BLE is added.

> [!important] Correction logged during review
> Despite the "wire(less)ly" tagline, **the current code is USB-wired only** — no Bluetooth anywhere. The ESP32 enumerates as USB HID keyboard + serial; the helper scans for a USB serial port. **BLE must be added** (both sides): BLE-keyboard mode on the chip + a BLE listener in the helper. Normal work, no locked chips.

### Sensor wiring (from the code)
4 signal wires: UART TX/RX at **57600 baud**, an **INT** finger-detect pin, plus power. Trivial to run on a short ribbon from the slot to the brain. (Firmware pins as written: FP_TX 43, FP_RX 44, FP_INT 2.)

## Licensing & selling

> [!success] MIT licensed — selling is allowed
> Confirmed `LICENSE` file: **MIT**, © 2026 Zimeng Xiong. You may use, modify, and **sell** the code/CAD/helper, even closed-source. Only obligation: include his copyright + the MIT text with the product. His README asks that CAD changes stay open — not binding under MIT, but worth honouring for goodwill.

Other selling caveats (not copyright):
- **FCC certification** required for any Bluetooth product. Escape hatch: build on a **pre-certified radio module** (the ESP32-C3-MINI-1 we're using carries modular cert) → cheaper verification instead of full cert. Wired-only units are lighter-touch.
- **Naming:** don't use "Touch ID" (Apple TM) or "tinyTouch" (his name) on a product. "Works with NuPhy Air75 V3" as compatibility is fine; don't imply endorsement.

## Chip choice for a custom PCB

> [!warning] Size correction (2026-08-18): S3-MINI-1 is TOO LONG for the 19 mm module
> The **ESP32-S3-MINI-1 is 15.4 × 20.5 × 2.4 mm** (datasheet). The **20.5 mm length exceeds the ~19 mm module envelope**, and rotation can't help a rectangle whose long side already exceeds the square. So the S3-MINI does **not** fit flat inside the final module. (Earlier notes that said "use the S3-MINI" were wrong on fit.)

> [!tip] Decision: split by version
> - **Wired breadboard prototype (v1):** **XIAO ESP32-S3** dev board — size doesn't matter on a breadboard, runs tinyTouch unmodified (USB HID). Prove the sensor + crypto here first.
> - **Final wireless in-module board (v2):** **ESP32-C3-MINI-1** (13.2 × 16.6 mm) — **fits** inside 19 mm. Since we chose wireless/BLE, we don't need the S3's USB-HID, so the C3 is fine; firmware change is minor (same Espressif/Arduino + BLE, drop the unused USB path). Verify 16.6 mm length against the measured module + wall budget.

Module size reference:

| Module | Size (mm) | Fits ~19 mm? | Firmware |
|---|---|---|---|
| ESP32-S3-MINI-1 | 15.4 × 20.5 | ❌ too long | — |
| **ESP32-C3-MINI-1** | 13.2 × 16.6 | ✅ (snug) | minor (BLE, no USB) |
| ESP32-C6-MINI-1 | 13.2 × 16.6 | ✅ | minor |
| nRF52840 module (Raytac MDBT50Q) | ~15.5 × 10.5 | ✅ easily | full rewrite; best low-power |
| bare ESP32-S3 QFN | ~7 × 7 | ✅ | advanced — own RF/antenna, loses module FCC cert |

- **nRF52840** stays the low-power endgame (v3+) if battery life demands it — smaller and sips µA, but different ecosystem.
- **Note:** C3 can't be a *USB* keyboard (no USB-OTG), which is why it's only viable *because* we went wireless. It can still be flashed over its USB-Serial/JTAG.

See mechanical fit + stack in [[touchid/Mechanical and Housing|Mechanical and Housing]].

### The custom board is mostly plumbing
MINI-1 + a 3.3 V regulator + sensor ribbon connector + **pogo pads on the underside** to meet the keyboard pins + optional USB-C + a handful of passives from the datasheet reference. ~20 components — a beginner-appropriate KiCad project. Fab 5 boards at JLCPCB ≈ $10–30. The pogo-pad footprint for the slot will be **custom** (exists nowhere yet).

### atopile — worth using
[atopile](https://github.com/atopile/atopile) (MIT, YC W24) lets you **describe the board in code** (`.ato` files) and compiles to a KiCad project with validation — a great fit for a compose-known-blocks board like this, and it matches the code/git workflow. There's a Claude skill for it, so it can be co-authored. Caveats: physical **layout still happens in KiCad** (incl. the antenna keep-out), and it's a young tool with a thinner library. Exports to KiCad, so no lock-in.

> [!warning] Antenna keep-out
> The keyboard's top frame is **metal** and blocks Bluetooth. **Where the antenna is:** on the module it's the **exposed zigzag copper trace at one short end** (the end not under the metal shield can). The datasheet marks it and specifies a **keep-out zone** (no copper/ground/metal/parts) that must sit at the **edge of your PCB**, ideally overhanging. Layout rules: (1) antenna end at the board edge, (2) keep-out clear of copper on all layers, (3) orient the module so that end points at the **plastic** part of the slot, away from the metal frame. Test signal with the case assembled before ordering final boards. The official Espressif KiCad footprint includes the keep-out courtyard automatically. (MINI-1U variant has no trace antenna — uses an external U.FL antenna you place on plastic.)

## Assembly (PCBA) — getting the chip installed

You don't hand-solder the module. Order **PCBA (PCB Assembly)** from **JLCPCB or PCBWay**: they fab the board *and* solder the parts. Upload three files (KiCad/atopile export these): **Gerbers** (board), **BOM** (parts list), **CPL/pick-and-place** (part positions). ~low tens of $ for 5 assembled boards + parts + setup.

> [!tip] Pick in-library parts to keep assembly cheap
> JLCPCB solders from its **LCSC** parts library — those are auto-loaded and cheap. Parts *not* in the library become consigned/hand-solder add-ons (pricier). The ESP32 modules, regulators, and common passives are stocked, so choose from the library where possible. The castellated ESP32 module and FFC connector are both fine for machine assembly. Option for board #1: **partial assembly** (fab installs the fine-pitch/module parts, you hand-solder easy bits at UBC's soldering station).

Print/soldering/measuring facilities: see [[touchid/UBC Facilities and Contacts|UBC Facilities and Contacts]].

## Related
- [[touchid/Architecture and Design|Architecture and Design]]
- [[touchid/Mechanical and Housing|Mechanical and Housing]]
- [[touchid/UBC Facilities and Contacts|UBC Facilities and Contacts]]
- [[touchid/Roadmap|Roadmap]]
