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
> Find out what each of the **10 pogo pins** does — especially **whether any pin can power the module**. Written for a first-time multimeter user. ~30–45 min. Companion interactive logger: `pin-test.html` in the Personal Project working folder.

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

Label the physical pins to match, then **photograph the slot with the numbers on it** (`slot-labeled.jpg`). That photo is what makes the readings interpretable.

## Tools

- Digital multimeter (needs continuity-beep + DC-voltage modes)
- Keyboard with module removed, USB-C cable
- Optional but valuable: one 100–330 Ω resistor (for the load test)
- Phone camera

> [!warning] The one real risk
> Touching a probe across two pins at once can short them. Probe **one pin at a time**, tip vertical and gentle. The board has TVS protection so a slip probably won't kill anything, but don't make a habit of it.

## Phase 1 — Continuity map (keyboard OFF, unplugged)

**1a. Ground pins.** One probe on the USB-C **metal shell**, touch the other to each pin. Beep = that pin is **ground**. Record yes/no.

**1b. Twinned pins.** Find pins wired together (reliability doubling). Use the triangular sweep so each pair is tested once:

- Fix probe on **J4-1**, sweep the other probe across J4-2 → J11-4
- Fix on **J4-2**, sweep J4-3 → J11-4 (skip J4-1, already done)
- …continue down to the last pair **J11-3 ↔ J11-4**
- 45 checks total. **Only record a pair when it beeps** — most won't.

> [!tip] Reading the tie matrix in the HTML tool
> Left edge = one pin, top edge = the other; click the box where they cross. Only the **lower-left half** is clickable (each pair once). Because your fixed probe is always *earlier* in the list than the pins you sweep, the box you want is always in the clickable half — it sits **down the fixed pin's column**. If a box is greyed out, you have the pair backwards.

**1c. Knob module underside.** Photograph its contact pads (`knob-underside.jpg`); note which pins they land on and whether the encoder legs are visible.

## Phase 2 — Voltage survey (keyboard ON)

DC-volts mode. **Black probe stays on ground** (USB shell or a known ground pin); red probe touches each pin. `0.00` is a valid result — record it. Do a full 10-pin sweep in **four states**:

| Sweep | State | Why |
|---|---|---|
| 1 | **Wired, awake** (USB in, tap a key first) | baseline; may show 5 V passthrough |
| 2 | **Wireless, awake** (cable out, BLE/2.4G, tap a key) | normal running state |
| 3 | **Asleep** (idle 6+ min, don't touch, then measure) | **decides the power design** — does power survive sleep? |
| 4 | **Off** (power switch off) | anything live here is wired straight to the battery |

Interpreting values: `0.00` = ground/inactive · `~3.3` = signal-high **or** real 3.3 V supply · `~3.5–4.2` = battery rail (jackpot) · `~5` = USB passthrough · drifting 0.1–0.9 = floating/nothing.

## Phase 3 — Load test ("rubber-band test") — needs the resistor

Separates a **real power rail** from a **pull-up** (a signal line that shows 3.3 V but collapses under load). Only test pins that read a **steady ≥3.3 V in Sweep 2**:

1. Keyboard on, wireless, awake.
2. Bridge the resistor from the candidate pin to a ground pin.
3. Measure the candidate pin's voltage **while the resistor is on**.

- Barely drops (3.3 → 3.1) = **real power rail** ✅
- Collapses (3.3 → <0.5) = pull-up, can't power anything.

Keep each load under ~10 s; with 100–330 Ω the current is tiny and safe.

## Recording results

Fill `pin-test-results.csv` (columns: `pin, gnd_beep, tied_to, v_wired, v_wireless, v_asleep, v_off, v_loaded, notes`), or use `pin-test.html` and hit **Download CSV**. **Raw numbers only** — don't round to what "seems right," don't skip zeros. Include `slot-labeled.jpg` and `knob-underside.jpg`.

> [!note] Then what
> The results feed the power decision and the pinout map in [[touchid/Architecture and Design|Architecture and Design]]. Best case: a pin holds ~3.3 V under load even while asleep → module runs off keyboard power, fully wireless. Worst case: fall back to a battery-connector tap or an on-board LiPo.

## Related

- [[touchid/Hardware Teardown|Hardware Teardown]]
- [[touchid/Architecture and Design|Architecture and Design]]
