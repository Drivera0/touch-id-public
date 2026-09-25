---
title: MCU swap — MDBT50Q to Fanstel BC840M — REJECTED
type: project
updated: 2026-08-30
---

# Replacing U1 with a smaller module — REJECTED 2026-08-30

> [!failure] Verdict: NO SWAP. Keep the Raytac MDBT50Q-1MV2.
> BC840M's datasheet (Ver 1.08) disqualifies it three ways, and the decisive
> one is not size. **A smaller module needs MORE board area here**, because
> the small modules use PCB TRACE antennas and MDBT50Q uses a CERAMIC CHIP
> antenna. See "Why the swap fails" at the bottom.

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
| Holyiot 17095 | 9.4 x 9.25 | 86.95 mm2 | ? | **NO** | ruled out — no VDDH |
| Insight SiP ISP1807 | 8.0 x 8.0 x 1.0 | 64.00 mm2 | 230 m | **NO** | ruled out — see below |
| Minew MS88SF3 | 18.5 x 12.5 | 231.25 mm2 | 300–350 m | ? | **BIGGER than what we have** |

### BC840M saves 76.13 mm2 of body area — 9.7x the whole 0201 campaign

It is also **0.55 mm thinner** (1.5 vs 2.05), which matters because the module
already stands proud of the slot.

### Why NOT the smaller BC840

**Range is 4 m at 1 Mbps**, against BC840M's 135 m. Same silicon, smaller
antenna. DESIGN-SPEC already ruled out the u-blox ANNA-B112 because *"the
keyboard's top frame is metal"* — a 4 m free-space rating inside a metal
enclosure is the same mistake in a different package. It is also sold out at
Fanstel. The extra 21.3 mm2 BC840M costs is cheap insurance.

### Why NOT the ISP1807 — the tempting one

8.0 x 8.0 x 1.0 mm, 64 mm2, nRF52840, integrated antenna and matching, an
on-module 32.768 kHz crystal, and 2.4 GHz proprietary (Gazell). On area alone it
beats everything. **Two hard blockers, both from datasheet R18:**

1. **No VDDH.** Pin 26 VCC_nRF is the only supply: **1.7–3.6 V, absolute max
   3.9 V**. The revision history is explicit — *"R6: Correction VCC / VCCH, **No
   High-Power Mode availability**."* VSTOR reaches 3.912 V, which is PAST its
   absolute maximum, not merely outside the operating range.
2. **Antenna keep-out is 18.0 mm min x 4.0 mm** — "no metal, no traces and no
   components on any application PCB layer". On a 20.00 mm wide board that is
   the entire antenna end, inside a metal keyboard frame.

### Why NOT Holyiot 17095

**No 4.2 V direct** — it has no VDDH. VSTOR reaches 3.912 V (VBAT_OV), which is
above the nRF52840's 3.6 V VDD maximum, so VDDH is not optional here. This is
the same reason DESIGN-SPEC notes "no non-Nordic module accepts 4.2 V".

## VDDH is ARCHITECTURAL — this is why the small modules keep failing

Two candidates died on VDDH, so it was worth proving the requirement is real
rather than incidental. It is:

    U1.30  VSTOR      -> VDDH, straight off the storage rail
    U1.28  NRF_VDD    -> "REG0 output decoupling" (C9)

**REG0 is the nRF52840's INTERNAL high-voltage regulator.** In high-voltage
mode VDDH is the input and VDD is REG0's *output*, which needs the decoupling
cap — that is exactly what C9 is. NRF_VDD is not fed by anything on the board.

Both TPS7A2033 LDOs power the SENSOR rails (U3 -> SENSOR_3V3, U4 ->
SENSOR_MCU_3V3), not the MCU. So there is no existing 3.3 V rail to retarget.

Dropping VDDH would mean **adding a third LDO purely for the MCU**: more parts
and area on a board already at capacity, and its quiescent current comes
straight out of the harvest budget. VDDH is a requirement, not a convenience.

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

---

## Can a different CELL unlock a smaller module? No — asked and answered 2026-08-30

Tempting idea: the 3.6 V wall that kills ISP1807 comes from VSTOR reaching
3.912 V, and 3.912 V is a Li-ion number. Pick a lower-voltage chemistry and
VDDH stops being required. **It does not work, for two independent reasons.**

### 1. The ceiling is set by the SOURCE, not the cell

DESIGN-SPEC, "three deliberate deletions": *"a source that cannot exceed
**3.68 V** cannot overcharge a 4.2 V cell. It self-limits at ~25-30% SOC."*
There is no charger IC — harvest reaches the cell through ideal diodes, so
VSTOR tracks the source and tops out at **3.68 V whatever cell is fitted**.

**3.68 V is still above the 3.6 V VDD maximum of every non-VDDH module**, and
there is no middle tier: modules are either standard-VDD (3.6 V max) or
high-voltage (5.5 V max). Nothing is rated 3.7-3.8 V. Changing chemistry moves
a number that was never the binding constraint.

Capping lower is not available either — see
[[touchid-lm66100-cannot-be-gpio-gated]]: the LM66100's CE is a comparator
referenced to VIN, so the harvest path cannot be opened under firmware control.

### 2. Small LiFePO4 cells are not a purchasable product

LFP tops out at 3.65 V and would have been the candidate chemistry. At the
**20-35 mAh** this design needs, it effectively does not exist at retail: LFP is
an industrial large-format chemistry and the small parts are 20 **Ah**, not
20 mAh. Same trap as the protected LPM1254 — correct on paper, unbuyable.

### What the cell decision DOES still control

Sourcing and sellability, which is the reason it was raised. Requirements are
unchanged and modest: **20-35 mAh**, storage impedance **under 3.3 Ohm**, bare
cell with factory leads (protection lives on-board at U5), and it must be
buyable singly AND in small production quantity. That is an ordinary small
LiPo — the VARTA CP1254 A4 (77 mAh, <0.5 Ohm, 210 mA pulse) is noted as
electrically ideal but fails mechanically.

**Conclusion: VDDH is non-negotiable, so the module choice stands on its own.
BC840M remains the recommendation.**


---

## Why the swap fails — datasheet Ver 1.08, checked 2026-08-30

### 1. "Don't use a module with internal antenna inside a metal case"

Verbatim, from *Notes on Antenna and PCB Layout*. It also asks to **"keep all
external metal at least 30 mm from the antenna area."** The NuPhy Air75 V3's top
frame is metal and the module sits in a slot in it — 30 mm is not available in
any direction.

This is the **exact** disqualifier DESIGN-SPEC already used to rule out the
u-blox ANNA-B112: *"cannot sit in a metal enclosure — the keyboard's top frame
is metal."* The same test was simply never applied to BC840M.

### 2. The required ground-free width does not fit the board

Datasheet mounting rules for a corner placement:
* *"the antenna area shall extend **5.5 mm** from the edge of ground plane"*
* *"Ground plane shall be at least **5 mm** from the edge of the antenna area"*

        antenna area width                10.10 mm
        + 5 mm ground clearance each side 20.10 mm   required ground-free width
        board width                       20.00 mm
        SHORTFALL                         -0.10 mm

It fails before any margin, on a rule with no give in it. The preferred
placement is worse still — it wants the antenna to **overhang the board edge by
5.5 mm**, which the slot cannot accommodate.

### 3. The keep-out GROWS, so the area saving is illusory

|  | MDBT50Q (chip ant.) | BC840M (trace ant.) |
|---|---|---|
| body | 162.75 mm2 | 87.33 mm2 |
| ground-free area required | 84.20 mm2 | **110.55 mm2** |
| ground surviving at the sides | 3.37 mm each | **none — full width** |

The body shrinks by 75.42 mm2 and the mandatory ground-free area grows by
26.35 mm2, on **both** F.Cu and B.Cu. Net saving is ~49 mm2, not 76 — and it is
unobtainable anyway because of the 0.10 mm width shortfall.

## The lesson worth keeping

**MDBT50Q is physically bigger because its antenna is a ceramic chip, and that
is precisely what lets it work here.** A chip antenna tolerates nearby ground
and nearby metal; a PCB trace antenna does not, and buys its small body by
demanding clear space around it. On a 20 x 19 mm board inside a metal keyboard,
the tolerant antenna is worth more than the small body.

Every smaller candidate examined (BC840, BC840M, ISP1807) uses a trace or
integrated-matching antenna with a keep-out at least as large as MDBT50Q's.
**Do not re-open this on module BODY size alone** — compare body + mandatory
keep-out, and check the metal-enclosure note first, because it is the cheapest
disqualifier to test.
