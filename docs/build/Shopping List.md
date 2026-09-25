---
title: Shopping List
type: project
tags:
  - touchid
  - hardware
---

# Shopping list — what JLCPCB does *not* supply

JLCPCB delivers the assembled carrier board only: PCB + U1 (ESP32-C3-MINI-1),
U2 (TPS7A2033 LDO), C1/C2 (1 µF), C3/C4 (47 µF). Everything below is yours to buy.

## ⚠ Blocked — do not buy yet

### Fingerprint sensor
**The part is still not chosen, and the housing can't accept an arbitrary one.**
The housing has a **Ø12.4 mm window** with a **Ø14.2 mm counterbore** — the sensor
body must fit that, or the housing has to be re-modelled.

| Candidate | Outer Ø | Verdict |
|---|---|---|
| GROW R502-B | ~22 mm | ✗ too big (also one listing says 8.4 mm thick) |
| Hi-Link ZW101 | ~21 mm | ✗ too big |
| **Hi-Link ZW111** | **unverified** | current pick — **measure/confirm OD before ordering** |
| Hi-Link ZW0608 | 19 × 19 mm square | fallback, needs a square-window housing variant |

Also confirm before buying: **wire count and pinout**. The board exposes
3V3 / GND / TX / RX / INT / VT. On `0xEF01`-family parts **VT** is sometimes a
touch-power *input* and sometimes a finger-detect *output* — the board currently
ties it to +3V3, which is only correct in the first case.

## Safe to buy now

### Housing
- **PETG filament** (recommended) — tougher than PLA, won't crack at the screw bosses
- or **SLA tough/durable resin** if using the Form 2 at UBC HATCH Makerspace (ICICS 061B, access is gated — contact the technician). Not standard resin: it's brittle.

### Fasteners
- **M2 brass heat-set inserts** — for the two PCB bosses. Do not thread screws into bare plastic.
  (SLA note: heat-set doesn't work in resin — use glued-in inserts instead.)
- **M2 screws** ×2 — PCB → housing bosses (board holes are Ø2.2 at ±8.3 mm)
- **M2 countersunk screw** ×1 — module ear → keyboard's threaded boss (you may be able to reuse the one from the knob module you removed)
- A **soldering iron insert tip** if you don't have one, for pressing the inserts

### Sensor wiring
- **28–30 AWG stranded wire**, 6 conductors, if the sensor's own pigtail is too short
- Flux + fine solder — the J2 pads are Ø1.2 mm on 1.5 mm pitch

## Programming access — there is no connector

The ESP32 is flashed over its native USB-Serial/JTAG, but the board has **no USB
port and no programming header**. The pads are flat copper on the **bottom** side:

| Signal | Pad |
|---|---|
| USB D+ | TP-DP |
| USB D− | TP-DN |
| BOOT (GPIO9) | TP-IO9 |
| GND | J4-5 (pogo pad) |
| Power (VBAT) | J11-1/2/3 (pogo pads) |

So you need a way to touch 5 pads at once. Either:

- **Pogo-pin probes** (P75-type) + a scrap of perfboard to make a small jig — reusable, best if you'll reflash often; or
- Solder thin wires temporarily to the pads — free, but fiddly on Ø1.8 mm pads

Plus a **USB-C or micro-USB breakout board** that exposes **D+, D−, GND, 5V**.

Handy detail: the TPS7A20's input is rated to **6 V**, so you can feed the VBAT
pads straight from **USB 5 V** on the bench — no separate battery or supply needed
for programming.

## Still to measure first (from [[touchid/docs/bench/Pin Test Results|Pin Test Results]])

- [ ] Sleep sweep on J11-1 — does VBAT survive keyboard sleep? Decides whether firmware needs deep-sleep handling
- [ ] Load test on J11-1 (100–330 Ω) — confirm the rail holds up through the pogo contacts under the ESP32's ~350 mA TX peaks
- [ ] Continuity J11-1/2/3 to each other (confirm one rail, not three nets)

That load test matters more now: the LDO needs ≥3.44 V at its input to hold 3.3 V
out (140 mV dropout), and the pogo contacts sit in that path.
