---
title: MCU swap — MDBT50Q to Fanstel BC840M
type: project
updated: 2026-08-30
---

# Replacing U1 with a smaller module

**Why:** U1 is 15.5 x 10.5 mm on a 20 x 19 mm board. It is the single largest
consumer of area and the root cause of the space pressure — the two remaining
open pads, the pogo-block congestion around U5, and the "board is at capacity"
finding all trace back to it.

For scale: the entire 0201 campaign (14 parts) recovered **7.83 mm2**.

## Candidates, from DESIGN-SPEC's own shortlist, re-verified 2026-08-30

| Module | Size (mm) | Body area | Range @1 Mbps | VDDH | Status |
|---|---|---|---|---|---|
| Raytac MDBT50Q-1MV2 *(current)* | 15.5 x 10.5 x 2.05 | 162.75 mm2 | — | yes, pin 30 | consigned; not at LCSC |
| **Fanstel BC840M** | **7.1 x 12.2 x 1.5** | **86.62 mm2** | **135 m** | **yes, 1.7–5.5 V** | production, $8.86 |
| Fanstel BC840 | 7.1 x 9.2 x 1.5 | 65.32 mm2 | **4 m** | yes | **SOLD OUT + range risk** |
| Fanstel BC840E | 7.1 x 12.2 x 1.8 | — | 850 m | yes | **u.FL external antenna — ruled out** |
| Holyiot 17095 | 9.4 x 9.25 | 86.95 mm2 | ? | **NO** | ruled out, see below |

### BC840M saves 76.13 mm2 of body area — 9.7x the whole 0201 campaign

It is also **0.55 mm thinner** (1.5 vs 2.05), which matters because the module
already stands proud of the slot.

### Why NOT the smaller BC840

**Range is 4 m at 1 Mbps**, against BC840M's 135 m. Same silicon, smaller
antenna. DESIGN-SPEC already ruled out the u-blox ANNA-B112 because *"the
keyboard's top frame is metal"* — a 4 m free-space rating inside a metal
enclosure is the same mistake in a different package. It is also sold out at
Fanstel. The extra 21.3 mm2 BC840M costs is cheap insurance.

### Why NOT Holyiot 17095

**No 4.2 V direct** — it has no VDDH. VSTOR reaches 3.912 V (VBAT_OV), which is
above the nRF52840's 3.6 V VDD maximum, so VDDH is not optional here. This is
the same reason DESIGN-SPEC notes "no non-Nordic module accepts 4.2 V".

## What BC840M keeps

Same nRF52840 CKAA (Rev. D), 1 MB flash / 256 KB RAM, CryptoCell-310, SWD,
integrated antenna, -40 to +85 C, integrated EMI shield. All 13 signals U1
currently uses (SWD x2, sensor UART x2 + WAKEUP + SW_EN, BL_FLAG, RESET,
VBAT_OK, VBAT_SENSE, NRF_VDD, VSTOR, GND) are ordinary GPIO/power on a 48-GPIO
part — pin count is not a constraint.

## BLOCKING BEFORE ANY BOARD WORK

1. **Land pattern from the Fanstel datasheet.** Standing rule: never invent one.
   BC840M is LGA — the pad array must come from the datasheet, not be inferred.
2. **Antenna keep-out.** DESIGN-SPEC records "keep-out 2.5 mm **unverified**"
   for this family. The datasheet gives "antenna area width is 10.1mm" against a
   7.1 mm body, so the keep-out flares WIDER than the module. The current
   antenna keep-out (x [-6.66, 6.60], y [2.95, +9.30]) must be re-derived.
3. **Sourcing.** 0 stock at JLCPCB (C5155822 is the BC840, pre-order, $18.07).
   Buy direct from Fanstel and **consign**, which U1 already is.
4. **X-ray inspection** is flagged Required on the JLC part — LGA has no visible
   joints. Confirm cost at order time.

## What this does NOT fix by itself

The two open pads (U5.2, R6.1) are in the **pogo block**, not under U1. Freeing
76 mm2 gives the placer room to move the PCM cluster out of the pogo shadow,
which is the mechanism by which it should help — but that is a prediction, not
a result, and it must be proven by a rebuild + reroute + preflight.
