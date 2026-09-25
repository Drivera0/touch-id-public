---
title: Architecture and Design
type: reference
tags:
  - touchid
  - design
  - reference
---

# Architecture and Design

## The sidecar model

The module is a **self-contained device that shares the keyboard's chassis and (ideally) power, nothing more.** The computer sees two unrelated gadgets: "NuPhy Air75 V3" (the keyboard) and "Fingerprint Module." The keyboard's own firmware is never modified and never knows the module is there.

```
[ ZW101 sensor ] --UART(4 wires)--> [ ESP32-S3 brain ] --BLE/USB--> [ Mac/Windows helper ] --> types password
        ^                                   ^
   in the slot                     powered via slot pogo pins
                                    (or battery tap / own LiPo)
```

## Why not use the keyboard's own chip?

> [!warning] It's a software wall, not a hardware one
> The CH592M *could* physically do it (it has BLE and spare pins). But it runs **NuPhy's closed firmware** with no published source and no way to add features. It knows keys, lights, and the knob — not fingerprints. See below on why we can't replace that firmware either.

- **No QMK on the V3.** The Air75 **V2** supported QMK (open firmware you can modify) — on that keyboard this plan would be realistic. The **V3 dropped QMK** for NuPhy's proprietary NuPhy IO system. Community QMK status: https://github.com/zhogov/nuphy-state-of-qmk-firmware
- **Wiping it is brutal & risky.** Overwriting NuPhy's firmware means recreating *everything* (every key, BLE pairing, battery mgmt, backlight, 2.4G dongle) from scratch, on a chip QMK has never supported, likely with copy protection so no backup/undo. Brick risk on a $120 keyboard. No V3 community project to lean on.
- **Even V2's "open" was half-open** — QMK only drove *wired* mode; wireless ran on a separate closed chip.
- **Security is cleaner separate.** tinyTouch keeps the encrypted password keyed to a chip you fully control. Routing it through a multi-purpose keyboard radio muddies that.

**Conclusion:** the sidecar isn't the compromise — it's the good option. Own $8 chip, one job, keyboard untouched.

## Power strategy (decided by the pin test)

> [!success] Decision (2026-08-18): target = **wireless, powered from the keyboard**
> Chosen for the cleanest physical result — no cable, no USB port, no battery, so the module sits flush in the slot like the knob (a wired version would need a cable exit = a hole or a module that protrudes too much). **Contingent on the pin test** finding a power pin that holds under load and survives sleep. If it doesn't, fallbacks reintroduce a charge port or case-opening. Consequences: deep-sleep-on-INT and BLE antenna placement move onto the critical path (see [[touchid/docs/design/Firmware and PCB|Firmware and PCB]]).

Ranked best → fallback:

1. **Keyboard pin power** — a slot pin carries a usable rail (3.3 V or battery) that survives sleep and holds under load → module runs off the keyboard's 4000 mAh battery. Fully wireless, cleanest. *Confirm via [[touchid/docs/bench/Pin Test Procedure|Pin Test Procedure]] Phase 3 + Sweep 3.*
2. **Battery-connector tap** — thin wires into the case to the battery connector. Voids warranty, more invasive, but works.
3. **Own LiPo** — module carries a tiny cell (e.g. 401230). Fully independent, but adds bulk and charging.

> [!note] Sleep is the catch
> Keyboards cut power to peripherals when asleep. If the slot pin dies during sleep (Sweep 3 shows 0 V), either tap the battery instead, or accept "tap a key to wake, then touch sensor."

## Data path — same in wired OR wireless

The module **always talks over its own link**, independent of the keyboard's mode:

- **Keyboard wireless:** two independent radios. Fully wireless desk.
- **Keyboard wired:** module *still* uses its own link — it **cannot** use the keyboard's USB cable (that runs to NuPhy's chip; nothing can inject data through it).

So the keyboard's wired/wireless setting is irrelevant to the module. The module's own link is either:
- **USB cable** (tinyTouch as-written today) — appears as a USB keyboard + serial channel, OR
- **Bluetooth** (must be added — see [[touchid/docs/design/Firmware and PCB|Firmware and PCB]]) — the ESP32-S3's idle BLE radio.

## What it works for

| Scenario | Works? | Notes |
|---|---|---|
| Mac login / lock / `sudo` | ✅ today | exactly tinyTouch's use case |
| Windows login / UAC | ✅ needs Windows helper port | helper is Mac-only today |
| SSH key **passphrase** | ✅ | it's just a text prompt |
| "Touch ID or password" popups (Safari autofill, Settings) | ✅ via **fallback** | click "Use Password…", module types it — automating the fallback, not replacing biometrics |
| Apple Pay / passkeys / WebAuthn / some banking | ❌ never | require the real Secure Enclave; no password fallback. This is the "at the cost of some security" gap |

## Best feature idea: finger-to-secret mapping

The sensor stores **5 fingerprints** and the code already knows *which* finger matched (slots 1–5). Currently every finger types the same password. Small mod (~30 lines across firmware + helper): **map each finger to a different secret.**

- Right index → Mac password
- Left index → SSH passphrase
- Middle → Windows password

Turns a one-trick button into a **five-secret vault**, and it's a perfect first real modification for learning the codebase. Full hardware-security-key behaviour (holding actual SSH keys, passkeys like a YubiKey) is possible on the S3 but a serious project — filed as a late phase in [[touchid/notes/Roadmap|Roadmap]].

## Related

- [[touchid/docs/design/Firmware and PCB|Firmware and PCB]]
- [[touchid/docs/bench/Pin Test Procedure|Pin Test Procedure]]
- [[touchid/notes/Roadmap|Roadmap]]
