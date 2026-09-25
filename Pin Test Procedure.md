---
title: Pin Test Procedure
type: guide
tags:
  - touchid
  - hardware
  - guide
---

# Pin Test Procedure — mapping the slot pins

> [!goal] Purpose
> Find out what each of the **10 pogo pins** does — especially **whether any pin can power the module**, and **how the pins change between the keyboard's switch-module and knob-module settings**. Written for a first-time multimeter user. Companion interactive logger: `pin-test-v2.html` in this vault.

> [!warning] The v1 result was a fail
> The first 100 Ω load test collapsed J11-1/2/3 from 3.466 V to 1.031 / 0.596 / 0.526 V — implying **236 / 482 / 559 Ω** of source resistance, far too high for a battery rail. The keyboard's lights also changed under load. That reopened the power decision. See [[touchid/Pin Test Results|Pin Test Results]].

## Pin naming convention

Look **straight down into the slot**, module removed, keyboard in normal typing position:

- **J4** = the **6-pin** block on the **LEFT** → pins `J4-1 … J4-6`
- **J11** = the **4-pin** block on the **RIGHT** → pins `J11-1 … J11-4`

Within each block, number the **top row (toward the rear/screen) left→right, then down**:

```
   REAR (toward screen)
   J4        J11
   1  2      1  2
   3  4      3  4
   5  6
   FRONT (toward spacebar)
```

So **J4-5** (confirmed ground) is the **bottom-left** pin of the 6-pin block, and **J11-1** is the **top-left** pin of the 4-pin block.

## Tools

- Digital multimeter with continuity-beep, DC-voltage and resistance modes
- **100 Ω** resistor, ¼ W (brown-black-brown-gold). A 10 kΩ (brown-black-**orange**-gold) is only good enough to characterise pull-ups, not rails.
- Breadboard, two jumper wires
- Keyboard with module removed, USB-C cable
- Phone camera

### Meter settings

| Mode | Dial | Used for |
|---|---|---|
| DC volts | `V⎓` / `DCV` — **not** `V∼` | every voltage reading |
| Continuity | beep symbol | ground and tied-pin checks, power off |
| Resistance | `Ω` | verifying the resistor before each session |

Use the **lowest DC range above 3.5 V** (usually 4 V or 6 V) so you get 1 mV resolution. On a coarse 20 V range you lose the resolution needed to see a small sag. Never use `A` / `mA` across a rail.

> [!warning] The one real risk
> Touching a probe across two pins at once can short them. Probe **one pin at a time**, tip vertical and gentle. Hold jumper wires by the insulation, never two bare tips at once. 3.4 V at 35 mA is harmless to you — the risk is to the keyboard.

## Breadboard setup for the load test

- **100 Ω resistor** — one leg in hole `10a`, other leg bent up into the `−` rail above column 10
- **Jumper 1** — hole `10e` → the pin under test
- **Jumper 2** — `−` rail (around column 8) → **J4-5**
- **Meter red probe** — hole `10c`
- **Meter black probe** — `−` rail (around column 2)

Holes `10a`–`10e` are one electrical node, which is how the resistor, jumper 1 and the red probe all connect without touching. The `−` rail is **only** ground because jumper 2 makes it so — a breadboard has no inherent ground. Rows f–j and the bottom rails stay empty.

Column 10 is arbitrary. Any column works as long as all three connections share the same column on the same side of the centre channel.

## Phase 1 — Continuity map (keyboard OFF, unplugged)

**1a. Ground pins.** One probe on the USB-C **metal shell**, touch the other to each pin. Beep = that pin is **ground**. Record `yes` or `no` on every pin — a blank means "not tested", not "no".

**1b. Twinned pins.** Find pins wired together. Use the triangular sweep so each pair is tested once:

- Fix probe on **J4-1**, sweep the other probe across J4-2 → J11-4
- Fix on **J4-2**, sweep J4-3 → J11-4 (skip J4-1, already done)
- …continue down to the last pair **J11-3 ↔ J11-4**
- 45 checks total. **Only record a pair when it beeps** — most won't.

**1c. Settle the J11 question.** Do **J11-1, J11-2 and J11-3 beep to each other**? This was assumed in v1 and never verified, and the three pins gave three different load results — which they shouldn't if they're one node.

**1d. Knob module underside.** Photograph its contact pads (`knob-underside.jpg`); note which pins they land on and whether the encoder legs are visible.

## Phase 2 — Voltage survey (keyboard ON)

DC-volts mode. **Black probe stays on ground** (USB shell or J4-5); red probe touches each pin. `0.00` is a valid result — record it. Full 10-pin sweep in **five states**:

| Column | State | Why |
|---|---|---|
| `v_wired` | **Wired, awake** (USB in, tap a key first) | baseline; may show 5 V passthrough |
| `v_wireless` | **Wireless, awake** (cable out, BLE/2.4G, tap a key) | normal running state |
| `v_sleep1_lightoff` | **Light sleep** (backlight dropped, untouched) | first stage of power management |
| `v_sleep2_deep` | **Deep sleep** (idle 6+ min, don't touch) | **decides the firmware design** — does power survive sleep? |
| `v_off` | **Off** (power switch off) | anything live here is wired straight to the battery |

Interpreting values: `0.00` = ground/inactive · `~3.3` = signal-high **or** real 3.3 V supply · `~3.5–4.2` = battery rail · `~5` = USB passthrough · drifting 0.1–0.9 = floating/nothing.

## Phase 3 — Load test with 100 Ω

Separates a **real power rail** from a **pull-up or current-limited pin**. Only test pins reading a steady **≥3.3 V** in the wireless sweep.

1. Meter to **Ω**, verify the resistor is ~100 off-board. Back to **DC volts**.
2. Keyboard on, wireless, awake.
3. **Jumper 2 to J4-5 first.** Ground before power, always.
4. Jumper 1 to the pin under test.
5. **Resistor out** of the board — read and record the unloaded value. No current flows, so contact quality cannot affect this number.
6. **Resistor in** — read within ~10 s, record as `v_loaded`.
7. Re-seat your grip and repeat 4–5 times. **Keep the highest reading.** Contact resistance can only pull it down, never up.
8. Run the ground-path control test below.
9. Lift **jumper 1 first**, then jumper 2.

**Watch the keyboard while the load is on.** Lights changing, mode switching, anything visible — that's data. Put it in `notes`.

### Ground-path control test — run this every session

With the load running on J11-1, move the meter's **black probe from the `−` rail to the USB-C shell**.

- Reading jumps toward 3.4 V → your **J4-5 ground contact was the resistance**. The run is invalid; redo with ground clipped to the USB shell.
- Reading stays near the loaded value → the drop is **real and on the keyboard side**.

This is the test that separates a genuinely weak rail from a bad hand-held wire, and it's the reason the v1 numbers can't yet be trusted.

### Reading the result

Source resistance = (V_unloaded − V_loaded) ÷ (V_loaded ÷ 100).

| Implied source resistance | Verdict |
|---|---|
| ≤ 2 Ω | solid rail — can power the module |
| 2–20 Ω | usable rail |
| 20 Ω – 1 kΩ | current-limited or switched — not a plain supply |
| > 1 kΩ | signal / pull-up |

## Phase 4 — Mode comparison

The keyboard's web settings can reassign the module pins between **switch module** (press = keypress) and **knob module** (turn = volume, click = mute). If firmware reconfigures these pins, their electrical behaviour should change with the setting.

1. Complete Phases 1–3 fully in **one** mode. Write down which one.
2. Change the mode in the keyboard's web settings. Power-cycle if the setting requires it.
3. Repeat Phases 1–3 **without moving the breadboard**.
4. Compare. A pin that behaves differently between modes is firmware-controlled.

**What we're looking for:** a mode in which one of the J11 pins presents a genuinely low source resistance, or a detect scheme we can imitate so the keyboard powers our module the way it powers the knob.

## Recording results

Use `pin-test-v2.html` — two tables, live source-resistance calculation, mode comparison, CSV export. Or fill `cad/pin-test-results.csv` directly (columns: `pin, gnd_beep, tied_to, v_wired, v_wireless, v_sleep1_lightoff, v_sleep2_deep, v_off, v_loaded, notes`).

**Raw numbers only** — don't round to what "seems right," don't skip zeros. Always record the resistor value in `notes`. Include `slot-labeled.jpg` and `knob-underside.jpg`.

> [!note] Then what
> The results feed the power decision and the pinout map in [[touchid/Architecture and Design|Architecture and Design]]. Best case: a pin holds ≥3.3 V under a 100 Ω load, in at least one mode, even while asleep → module runs off keyboard power. Worst case: fall back to a battery-connector tap or an on-board LiPo.

## Related

- [[touchid/Harvest Test Procedure|Harvest Test Procedure]] — session 4, the loaded-while-asleep test this session never ran
- [[touchid/Pin Test Results|Pin Test Results]]
- [[touchid/Hardware Teardown|Hardware Teardown]]
- [[touchid/Architecture and Design|Architecture and Design]]
