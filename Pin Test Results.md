---
title: Pin Test Results
type: reference
tags:
  - touchid
  - hardware
  - reference
---

# Pin Test Results

Raw data: `cad/pin-test-results.csv` (session 1–2), `cad/pin-test-modes-2026-08-26.csv` (session 3, both modes). Logger: `pin-test-v2.html`. Procedure: [[touchid/Pin Test Procedure|Pin Test Procedure]].

> [!warning] There is no power rail in the slot
> Session 3 identifies **J11-1/2/3 as PWM RGB LED drive lines**, not a battery rail, and **J4 as the switch/encoder block**. The module connector carries signals and LED drive only. The keyboard cannot power an ESP32-C3 through these pins. The 2026-08-18 power architecture is **dead**, not merely reopened.

## Pin function map — current best understanding

| Pin | Function | Evidence |
|---|---|---|
| J4-1 | Encoder A (pull-up) | 3.293 V, ~55 kΩ source, both modes |
| J4-2 | Signal, idle low — **not ground** | 0.03–0.07 V, no current under load. Continuity to J4-5 tested 2026-08-27: **no beep** |
| J4-3 | Encoder B (pull-up) | 3.293 V, ~55 kΩ source, both modes |
| J4-4 | **Switch / encoder press** | Loading it **muted the PC and zoomed Chrome** — a real input event |
| J4-5 | **GND — confirmed** | Only pin that beeps to USB-C shell |
| J4-6 | Module detect? | Steady 0.001 V, unaffected by load, doesn't beep to ground |
| J11-1 | **RGB anode — channel 1** | PWM fluctuation, ~231–244 Ω, changes nearby RGB when loaded |
| J11-2 | **RGB anode — channel 2** | PWM fluctuation, ~440–450 Ω, changes nearby RGB when loaded |
| J11-3 | **RGB anode — channel 3** | PWM fluctuation, ~465–483 Ω, changes nearby RGB when loaded |
| J11-4 | **LED common return** | Stiff ~0.3 V at 3 mA (≈3–6 Ω), goes to 0.000 when lights sleep |

## The evidence for the LED reading

**1. The voltages oscillate.** J11-1/2/3 don't hold a value — they sweep and repeat ("bounces from 2.9 to 3.5 then bounces back down, repeating"). A battery rail does not do this. A PWM'd LED channel read by an averaging meter does exactly this.

**2. They all settle to 3.530 V when the backlight sleeps.** In knob mode `v_sleep1_lightoff` reads **3.530 on all three pins simultaneously** — steady, identical. That's three anodes idling at the supply through their driver, with no PWM running. It's the single most diagnostic number in the whole dataset.

**3. Loading them changes the RGB lights** — and specifically "the lights in the vicinity, not all". You're loading one LED channel and dimming it. Contact resistance cannot do this.

**4. The source resistances are LED-shaped.** Recomputed against the true 3.530 V source rather than the PWM average:

| Pin | Loaded (knob) | Current | Source R |
|---|---|---|---|
| J11-1 | 1.065 | 10.7 mA | ~231 Ω |
| J11-2 | 0.642 | 6.4 mA | ~450 Ω |
| J11-3 | 0.606 | 6.1 mA | ~483 Ω |

Three different values in the 200–500 Ω band is the classic signature of per-colour current-limiting resistors — each colour gets a different value because red, green and blue have different forward voltages.

**5. J11-4 behaves like the common return.** It holds ~0.3 V stiffly at 3 mA (3–6 Ω, the only genuinely low-impedance pin in the slot) while awake, and drops to **0.000 V** when the lights sleep.

**6. J4-4 generated real input events.** Loading it muted the PC and zoomed Chrome in *both* modes. That is a switch/encoder line being pulled low, registering as a press and a rotation.

## Switch mode vs knob mode

Very little changed electrically. Same pull-up values on J4-1/3/4, same LED behaviour on J11, same ground. J4-4 produced input events in both modes.

This argues the **module hardware is identical** in both cases — the same passive switches, encoder and RGB LEDs — and the web setting only changes how the keyboard *interprets* the encoder signals in firmware. There is no hardware reconfiguration to exploit.

## What this means for the design

**The slot cannot power the module.** Even if firmware were driven to hold all three LED channels full-on, the three current-limit resistors in parallel give ~116 Ω, or roughly **30 mA into a dead short and about 4.6 mA at 3.0 V**. An ESP32-C3 needs an order of magnitude more, with BLE transmit peaks into the hundreds of mA. It isn't close, and stealing it would visibly break the backlight.

Remaining options, in order of preference:

1. **On-board LiPo in the module**, charged over its own USB-C. Fully self-contained, no keyboard modification, no firmware dependency. Costs thickness — check against the 2.7 mm depth constraint beside U1.
2. **Tap the keyboard's battery connector** inside the case. Real VBAT, plenty of current, but requires opening the keyboard and routing a wire into the slot.
3. **Harvest the LED rail into a supercap** and duty-cycle hard. ~5 mA average could support an occasional fingerprint scan from deep sleep, but it fights the backlight and is fragile. Long shot.

The J4 signals remain useful for a different purpose: the module could *emulate* the switch and encoder so the keyboard still sees a valid module, while the fingerprint side runs independently over BLE.

## Confirmed by physical inspection — 2026-08-26

Examining the two stock modules settles it beyond the meter readings:

| Module | J4 contacts | J11 contacts | RGB LED on PCB |
|---|---|---|---|
| **Knob module** | yes | **none** | no |
| **Button module** | yes | **all four** | **yes** |

A module that doesn't light up simply doesn't touch J11. A module that does, touches all four. **J11 exists solely to drive a module's RGB LED** — that is now proven by inspection, not inferred from voltages.

It also means a fully functional module needs **only the J4 contacts**. The knob works on four pins: encoder A, encoder B, click, ground.

### Consequences for our module

- Model the TouchID module on the **button module**, not the knob. A fingerprint reader you press *is* a button, and the keyboard already knows how to handle one.
- **The RGB is free.** Wire an RGB LED to J11-1/2/3/4 exactly as the button module does. The keyboard drives it, so it matches keyboard lighting with no firmware and no draw from our own battery.
- The **button module PCB is a reference design** — photograph both sides and caliper the pad geometry. Given that U1/U2 footprints were invented placeholders, a known-correct pogo pad layout is worth copying rather than deriving.

## Remaining tests

- [ ] **Set the RGB to pure red**, then green, then blue, measuring all three pins each time. One channel should drop each time — this maps colour to pin, which is the wiring map needed if our module gets an RGB LED.
- [ ] **Continuity J11-4 → J4-5** with the keyboard off. Confirms whether the return is grounded or switched by the keyboard.
- [ ] `v_sleep2_deep` still never measured in either mode.
- [ ] Trace **J4-2 and J4-6** on the keyboard PCB — if either is genuinely unconnected, it's a candidate for injecting tapped battery power into the slot.
- [ ] Locate the keyboard's internal battery connector. Internal photos: https://fccid.io/2BE3OAIR75V3

Superseded (answered by the inspection above): AC-volts PWM check, brightness-zero check, knob underside photograph.

## Session 1 — 2026-08-18 (voltage survey, mode unrecorded)

| Pin | GND beep | V wired | V wireless | V off |
|---|---|---|---|---|
| J4-1 | | 3.293 | 3.293 | 0.00 |
| J4-2 | | 0.009 | 0.071 | 0.001 |
| J4-3 | | 3.293 | 3.293 | 0.000 |
| J4-4 | | 3.293 | 3.293 | 0.000 |
| J4-5 | **yes** | 0.000 | 0.000 | 0.000 |
| J4-6 | | 0.001 | 0.000 | 0.000 |
| J11-1 | | 3.680 | 3.466 | 0.200 |
| J11-2 | | 3.680 | 3.466 | 0.236 |
| J11-3 | | 3.685 | 3.466 | 0.280 |
| J11-4 | | 0.332 | 0.312 | 0.003 |

The steady-looking 3.466 V readings were almost certainly PWM averages that happened to sit still long enough to write down. The apparent "Li-ion charging vs discharging" story (3.680 wired, 3.466 wireless) was a coincidence of duty cycle, not battery chemistry.

## Session 2 — 2026-08-26 (first 100 Ω load test)

J11-1/2/3 collapsed to 1.031 / 0.596 / 0.526 V, implying 236 / 482 / 559 Ω. Read at the time as a possible bad ground contact; session 3 reproduced the same numbers in both modes, so the values are real and the hand-held ground was not the problem.

J4-1/3/4 collapsed to 0.006 V — ~55 kΩ, confirming weak MCU pull-ups.

## Power architecture — DEAD

The 2026-08-18 plan (J11-1+2+3 tied as VBAT in → 3.3 V LDO → ESP32-C3) rested on J11 being a battery rail. It is an LED connector. Do not build it.

## Related

- [[touchid/Harvest Test Procedure|Harvest Test Procedure]] — session 4, decides whether the LED rail can power the module
- [[touchid/Pin Test Procedure|Pin Test Procedure]]
- [[touchid/Hardware Teardown|Hardware Teardown]]
- [[touchid/TouchID Module Design|TouchID Module Design]]
- [[touchid/Firmware and PCB|Firmware and PCB]]
- [[touchid/Architecture and Design|Architecture and Design]]
