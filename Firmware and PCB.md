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

## Chip choice REVISITED — 2026-08-26

> [!warning] The ESP32-C3-MINI-1 decision is superseded
> Two findings force a rethink: the keyboard slot supplies **no power** (see [[touchid/Pin Test Results|Pin Test Results]] — J11 is an RGB LED connector), and the C3-MINI's **13.2 mm width** is what creates the connector-vs-screws deadlock in [[touchid/Module Mechanical v3|Module Mechanical v3]].

### Wi-Fi is not needed

The module's only wireless job is getting an auth result to the Mac. BLE does that device-to-device with no infrastructure. Wi-Fi would mean storing router credentials on the device holding the password, depending on a network being up, and burning far more power. **BLE only.**

That removes the reason to stay on Espressif. Every ESP32 MINI-1 module is 13.2 × 16.6 mm regardless of variant, so the C6 is a newer part at the same size — a drop-in, but no help dimensionally.

### The width arithmetic

`Module Mechanical v3` needs 5.85 mm spare width (FPC connector 3.25 + screw boss 2.60) against a 17.94 mm cavity.

| Module | Chip | Size (mm) | Antenna | Width | Spare | Clears 5.85? |
|---|---|---|---|---|---|---|
| ESP32-C3-MINI-1 | ESP32-C3 | 13.2 × 16.6 × 2.4 | PCB | 13.2 | 4.74 | ✗ short 1.11 |
| ESP32-C6-MINI-1 | ESP32-C6 | 13.2 × 16.6 × 2.4 | PCB | 13.2 | 4.74 | ✗ short 1.11 |
| **Raytac MDBT42Q** | nRF52832 | 16 × 10 × 2.2 | chip | 10.0 | 7.94 | ✅ |
| **Holyiot-17095** | nRF52832 | ~17 × 9.5 | integrated | 9.5 | 8.44 | ✅ |
| Insight SiP ISP1807 | nRF52840 | 8 × 8 × 1.0 | integrated | 8.0 | 9.94 | ✅ |
| u-blox ANNA-B112 | nRF52832 | 6.5 × 6.5 × 1.5 | integrated | 6.5 | 11.44 | ✅ |

**All four nRF52 options clear it.** Going below 10 mm buys nothing we need, so select on practicality rather than absolute size.

> [!caution] Integrated-antenna keep-out
> A 6.5 × 6.5 module is not 6.5 × 6.5 in the layout. Integrated-antenna parts need a ground-plane keep-out — antenna end at a board edge, no copper beneath or beside it, typically several mm. On a 19 × 19 board also holding a sensor and battery, that keep-out eats much of the apparent size win. **The datasheet's placement rules matter more than the outline.**

### Recommendation — revised 2026-08-26 after a sourcing sweep

> [!warning] The MDBT42Q recommendation below was superseded before it was acted on
> Two things changed it: storage now has to be a **cell**, not a supercap (see
> [[touchid/DESIGN-SPEC|DESIGN-SPEC]] §9), which makes module **height** as binding as
> width; and a verified pin-by-pin check showed VDDH is far rarer than assumed.

| Part | Size (mm) | LCSC / JLC | 4.2 V direct | Decisive factor |
|---|---|---|---|---|
| **Fanstel BC840** | 7.1 × 9.2 × **1.5** | C5155822, in stock | **yes — VDDH to 5.5 V** | narrowest *and* thinnest. VDDH deletes U2 and its caps outright. ~$17 is the whole penalty |
| **Holyiot 17095** | 9.4 × 9.25 × **?** | **C9900031218** | no | in JLCPCB's SMT catalog → a **verified land pattern**, exactly the safeguard that would have caught the invented U1/U2 footprints |
| Raytac MDBT50Q-1MV2 | 15.5 × 10.5 × 2.05 | not at LCSC | yes, VDDH pin 30 | highest-confidence datasheet of the three, but 10.5 mm buys only 2.7 mm over the ESP32 |

**MDBT42Q is out on availability** — LCSC C2828282 is out of stock, and nRF52832 has
no VDDH so the regulator would stay.

> [!danger] Two dimensions here are still unverified
> **Holyiot 17095's height appears nowhere in its datasheet** — against a 4.96 mm
> ceiling that is not acceptable, and a reseller listing is not a source (trap #2:
> vendor spec tables are the package, not the module). **BC840's 2.5 mm antenna
> keep-out is second-hand** — open `BC840-p Product Specifications.pdf` before layout.

**Ruled out, with reasons worth remembering:**

- **ESP32-H2-MINI-1** — 13.2 × 16.6 × 2.4, identical to the C3. Zero gain.
- **u-blox ANNA-B112** — 6.5 × 6.5 sounds ideal, but §3.2.1 says it **cannot be
  mounted in a metal enclosure** and it needs an antenna tuning strip drawn on the
  host PCB. The keyboard's top frame is metal. *A 6.5 mm package is not a 6.5 mm
  layout* — the general lesson for every integrated-antenna part.
- **Insight SiP ISP1807** — 8 × 8 × 1.0, thinnest of all, but its `VBUS` pin is a
  USB-regulator input, **not** VDDH. Abs max VCC 3.9 V. Cannot take a cell directly.
- **SiLabs BGM220S** — the 6 × 6 body needs an antenna polygon copied onto your top
  layer extending ~5 mm past the module. Real bounding box ≈ 10.8 × 9.0.
- **No non-Nordic module accepts 4.2 V.** STM32WB5MMG 3.6 V, BGM220S 3.8 V, RSL10 SIP
  3.63 V, PAN1760A 3.6 V. STM32WB5MMG (C2847339, 11.0 × 7.3 × 1.38) is otherwise the
  most interesting outsider — fully self-contained antenna, 2-layer compatible, and
  the only part in the sweep publishing a real *with-retention* sleep figure (2.1 µA).
- **TI CC2652RSIP** — no integrated antenna.

> [!note] Vendors publish sleep current *without* RAM retention
> Raytac, Insight SiP and u-blox all quote the no-retention number. Insight SiP is the
> honest exception, publishing **+30 nA per 4 KB retained** — so a fully-retained
> nRF52840 is ~3.4 µA, not the advertised 1.5 µA. Budget accordingly.

### Cost of the switch

Leaving ESP-IDF for Nordic. Smaller than it sounds, because **tinyTouch's USB HID path was never going to survive anyway** — a module buried in a keyboard slot has to be BLE, and that rewrite was already scoped (see the correction note above). What's reusable ports cleanly: the `0xEF01` sensor protocol is plain UART, and Adafruit's nRF52 Arduino core is mature. Also note the **power argument now points the same way** — the ESP32-C3 draws ~80 mA transmitting and Nordic parts are cited at 10–16× more efficient for BLE, which stops being academic once we're on a battery we can barely fit. The fingerprint sensor dominates *active* draw regardless of MCU; the Nordic win is in idle and advertising, where the module spends virtually its whole life.

### BLE limitation to design around

| Scenario | Works over BLE? |
|---|---|
| Lock screen (Mac already booted) | ✅ Bluetooth stack running |
| `sudo` in terminal | ✅ |
| App / password-manager prompts | ✅ |
| **FileVault unlock at cold boot** | ❌ likely not |

At the FileVault pre-boot screen macOS loads a minimal driver set that generally excludes third-party Bluetooth keyboards; Apple's own Touch ID keyboard gets special treatment, and USB keyboards work. This contradicts the "Mac login ✅ today" row in [[touchid/Architecture and Design|Architecture and Design]], which assumed USB HID. **The module cannot be the only way into the machine.**

Worth verifying on the actual Mac: pair any third-party Bluetooth keyboard, restart with FileVault on, see whether it types at the unlock prompt.

### FCC note

The modular-certification escape hatch still applies — MDBT42Q, Holyiot, ISP1807 and ANNA-B112 all carry modular approval, same as the ESP32-C3-MINI-1 did. Switching vendors doesn't lose that advantage.
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
