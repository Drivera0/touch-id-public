---
title: Harvest Test Procedure
type: guide
tags:
  - touchid
  - hardware
  - guide
  - power
updated: 2026-08-26
---

# Harvest Test Procedure — can the LED rail power the module?

> [!goal] What this decides
> Whether **J11-1/2/3 can supply usable current while the backlight is off**.
> This one result chooses between two completely different products:
>
> - **Pass** → a self-contained module. Pop it in, nothing modified, nothing to charge.
> - **Fail** → the only clean option left is tapping the keyboard's internal battery, which means opening the keyboard and soldering a wire.
>
> Companion logger: `harvest-test.html` in this vault. Prior work: [[touchid/docs/bench/Pin Test Procedure|Pin Test Procedure]], [[touchid/docs/bench/Pin Test Results|Pin Test Results]].

## Why this test exists

Session 3 established that `v_sleep1_lightoff` reads a steady **3.530 V on all three pins simultaneously** when the backlight sleeps. That is an **unloaded** reading — the meter draws essentially nothing, so it proves a voltage is present but says nothing about whether current is available behind it.

Those are very different things. A 10 MΩ leakage path and a stiff 3.3 V supply both read 3.530 V on a multimeter. Only one of them can run a fingerprint sensor.

The session-3 load tests **were run with the backlight awake**. So we have loaded numbers for the awake state and unloaded numbers for the asleep state, and no overlap. This test fills the gap.

### The thing that makes harvesting possible

The keyboard turns the module's LED off by **opening the return** (J11-4), not by dropping the anodes. Confirmed 2026-08-26: no continuity J11-4 → J4-5 with the keyboard off.

So when the backlight sleeps, J11-1/2/3 sit at 3.530 V through their per-colour limit resistors with **no path through the LED at all**. Current we draw from them returns through **J4-5**, the real chassis ground — it never enters the LED, so it lights nothing and dims nothing.

That is the entire trick. Everything below is just measuring whether the supply behind it is real.

## What we already know

| Pin | Source resistance (measured awake) | Implied colour |
|---|---|---|
| J11-1 | ~231 Ω | red (lowest V_f, so smallest resistor) |
| J11-2 | ~450 Ω | green or blue |
| J11-3 | ~483 Ω | green or blue |
| J11-4 | ~3–6 Ω dynamic, stiff 0.3 V offset | common cathode, switched low-side sink |

## Predicted results — write these down before you measure

If the source behaves the same asleep as awake, you will get these numbers. **Matching them is the pass condition.**

### Per-pin, backlight off

| Load | J11-1 | J11-2 | J11-3 |
|---|---|---|---|
| 1 kΩ | 2.868 V | 2.434 V | 2.380 V |
| 330 Ω | 2.076 V | 1.493 V | 1.433 V |
| 100 Ω | 1.066 V | 0.642 V | 0.605 V |

> [!note] The 100 Ω column is a control, not a discovery
> Those three values are what you already measured in session 3. If they reproduce with the backlight **off**, the source is identical in both states and the whole model holds. If they come out much lower, the asleep state is weaker than the awake state and the 330 Ω / 1 kΩ columns tell you by how much.

### Combined harvest node (three 100 Ω isolation resistors)

| Load | Predicted V | Current | Power |
|---|---|---|---|
| 1 kΩ | 3.063 V | 3.06 mA | 9.4 mW |
| **330 Ω** | **2.414 V** | **7.32 mA** | **17.7 mW** |
| 100 Ω | 1.398 V | 13.98 mA | 19.5 mW |

**The 330 Ω combined reading is the single most important number in this session.**

For scale: the module needs about **5.5 mWh/day**. At 17.7 mW, two hours of harvesting per day is already six times the budget, and one fingerprint scan is replaced in about ten seconds.

## Tools

- Digital multimeter with DC-volts, continuity and resistance modes
- **3 × 100 Ω** resistors, ¼ W (brown-black-brown-gold) — isolation
- **1 × 330 Ω** (orange-orange-brown-gold) — primary load
- **1 × 1 kΩ** (brown-black-red-gold) — light load
- **1 × 100 kΩ** (brown-black-yellow-gold) — for the J11-4 flag test
- Breadboard, 5 jumper wires
- Keyboard with module removed, USB-C cable
- Phone camera and a timer

Meter settings are unchanged from [[touchid/docs/bench/Pin Test Procedure|Pin Test Procedure]]: **DC volts**, lowest range above 3.5 V for 1 mV resolution, never `A`/`mA` across a rail.

> [!warning] Three specific risks in this session
> 1. **Never bridge J11-1/2/3 to J11-4.** That is a direct LED overdrive path. Everything here returns to **J4-5**.
> 2. **Never tie J11-1/2/3 directly to each other.** They are three separate driver outputs. The 100 Ω isolation resistors in Phase 2 exist precisely so that a backlight wake mid-test cannot make them fight each other.
> 3. **Minimum 100 Ω, always.** No direct shorts to ground, not even briefly.
>
> The voltages here are harmless to you. The risk is entirely to the keyboard.

## Phase 0 — reach and confirm the lights-off state

There are two different ways the backlight goes dark, and they may not be the same electrical state. Test both, and record which one each measurement belongs to.

- **State A — sleep timeout.** Leave the keyboard untouched until the backlight drops on its own.
- **State B — brightness zero.** Set brightness to 0 manually while the keyboard is otherwise awake.

For each state, with **no load connected**, measure J11-1, J11-2, J11-3 and J11-4 against J4-5.

**Expected:** 3.530 V on 1/2/3, and 0.000 V on J11-4.

If you cannot reproduce 3.530 V unloaded, stop — something has changed since session 3, and no loaded reading will mean anything until that is resolved.

## Phase 1 — per-pin load line, backlight OFF

Use **breadboard setup 1** (single-pin) in `harvest-test.html`.

- 330 Ω from the pin under test to the `−` rail
- `−` rail jumpered to **J4-5**
- Red probe on the load's node, black probe on the `−` rail

For each pin — J11-1, then J11-2, then J11-3:

1. **Load removed.** Record the unloaded voltage. No current flows, so contact quality cannot affect this number.
2. **1 kΩ in.** Read within ~10 s. Record.
3. **330 Ω in.** Record.
4. **100 Ω in.** Record.
5. Re-seat your grip and repeat each reading 4–5 times. **Keep the highest.** Contact resistance can only pull a reading down, never up.
6. Watch the keyboard the whole time. Any glow, flicker, or the backlight waking is data — write it in `notes`.

Three load points instead of one is the point of this phase. A genuine resistive source gives three readings that fall on a straight line; leakage does not. One point can be faked by a bad contact, three cannot.

### Ground-path control — run this once per session

With the 330 Ω load running on J11-1, move the meter's **black probe from the `−` rail to the USB-C shell**.

- Reading jumps toward 3.5 V → your **J4-5 contact was the resistance**. The run is invalid. Redo with ground clipped to the USB shell.
- Reading stays near the loaded value → the drop is **real and on the keyboard side**.

This is the check that separates a weak rail from a bad wire, and it is why the session-2 numbers were initially distrusted.

## Phase 2 — the combined harvest node

**This is the phase that answers the question.** Use **breadboard setup 2**.

Each pin gets its own 100 Ω isolation resistor; the three meet at a common node; one load resistor runs from that node to J4-5.

Backlight **off only**. Do not run this phase awake.

1. Build the node with **no load resistor** installed. Record the unloaded node voltage — should still be ~3.530 V.
2. **1 kΩ** from node to `−` rail. Record.
3. **330 Ω.** Record. ← the headline number
4. **100 Ω.** Record.
5. Repeat in the other lights-off state (A vs B).

The logger computes total current and effective source resistance for you.

## Phase 3 — J11-4 as a free "backlight awake" flag

If J11-4 is a switched sink, it can tell the module when to stop harvesting using **one pin and one resistor** instead of sampling PWM on three ADC channels. That is a meaningful power saving on a module living off a supercap.

No external supply needed — borrow the 3.53 V that is already sitting on J11-1.

1. **100 kΩ** from **J11-1** to **J11-4**. (100 kΩ limits this to ~35 µA — harmless.)
2. Measure **J11-4** against J4-5 with the backlight **asleep**. 
3. Wake the backlight. Measure J11-4 again.

| Observation | Meaning |
|---|---|
| Asleep: rises well above 0.3 V (toward 3.5) · Awake: stays ~0.3 V | **Confirmed.** The sink is open when asleep, closed when awake. Flag works. |
| Both states ~0.3 V | Sink is always on. J11-4 is not a usable flag; gate on J11-1/2/3 PWM instead. |
| Both states near 0 V | Something else is holding it down. Re-examine the topology. |

## Phase 4 — endurance and interference

Short tests can hide slow current limits and can miss the keyboard noticing.

1. Rebuild the Phase 2 node with the **330 Ω** load. Backlight asleep.
2. Leave it connected for **10 minutes**. Record the node voltage at 0, 1, 5 and 10 minutes.
   - Steady → real supply.
   - Slow decay → something is current-limiting or a capacitor is draining. Note the shape.
3. Does the backlight wake on its own during those 10 minutes? Does the keyboard behave oddly, drop its connection, or change lighting?
4. **With the load still connected**, wake the backlight by tapping a key. Watch the keyboard's own LEDs closely and describe what happens.

Step 4 tells us how aggressively the harvest gate has to back off, which sets the design of that part of the circuit. "Visible dimming" and "no visible change" lead to different components.

## Reading the result

Judge on the **combined 330 Ω** reading from Phase 2.

| Node voltage | Current | Verdict |
|---|---|---|
| **≥ 2.0 V** | ≥ 6 mA | **Confirmed.** Harvesting is the plan. Self-contained module is achievable. |
| 1.0 – 2.0 V | 3–6 mA | **Workable but tight.** Still ~5–10× the daily budget, but storage sizing needs care. |
| 0.3 – 1.0 V | 1–3 mA | **Marginal.** Possible in principle, fragile in practice. Keyboard tap becomes the safer plan. |
| **< 0.3 V** | < 1 mA | **Dead.** The 3.530 V is leakage. Fall back to tapping the keyboard battery. |

## Then what

**On a pass**, the remaining unknown moves to storage, and the next decision is a supercapacitor alone versus a supercap plus a small soldered-in cell. That depends on how long the module must survive with the keyboard fully off, and on what physically fits the 17.94 × 17.94 × ~5 mm cavity.

**On a fail**, the next test is tracing J4-2 and J4-6 on the keyboard PCB to see whether a tapped battery wire can ride an existing pogo pin rather than needing a new contact in the slot.

Either way, the sensor's **standby current on its detect rail** is still unmeasured and is the other thing that can sink the battery budget. Since the sensor is not bought yet, make it a purchase criterion — pick one with a specified low-power finger-detect mode rather than discovering it afterward.

## Related

- [[touchid/docs/bench/Pin Test Procedure|Pin Test Procedure]]
- [[touchid/docs/bench/Pin Test Results|Pin Test Results]]
- [[touchid/docs/design/Firmware and PCB|Firmware and PCB]]
- [[touchid/docs/design/DESIGN-SPEC|DESIGN-SPEC]]
