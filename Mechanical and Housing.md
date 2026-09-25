---
title: Mechanical and Housing
type: reference
tags:
  - touchid
  - mechanical
  - housing
  - reference
---

# Mechanical and Housing

## The fit constraint

The NuPhy module (the swappable knob/keyswitch that seats in the slot) is a **square of ~19 × 19 mm**. Everything must live **inside** that outline — nothing can overhang it. This is the governing constraint.

> [!important] Confirm by measurement
> "~19 mm" is from eyeballing; the real footprint + slot depth come from calipers (see [[touchid/Pin Test Procedure|Pin Test Procedure]] / measurement). A ±1–2 mm difference changes which parts fit (e.g. it decides whether an ESP32-S3-MINI-1 could ever squeeze in). **Measure before buying/finalizing.**

### Budget math
Usable interior = module width − 2 × wall. With ~1.5 mm walls → **~16 mm internal**. So:
- **Sensor body** ≤ ~16 mm (leaves a bezel) — see sensor shortlist below.
- **MCU module** must fit the PCB, which fits the ~16–17 mm interior → **ESP32-C3-MINI-1 (13.2 × 16.6 mm) fits; S3-MINI-1 (20.5 mm long) does not.** See [[touchid/Firmware and PCB|Firmware and PCB]].

## The stack (one-piece module, like NuPhy's own)

```
 finger
   ↓
[ fingerprint sensor ]   ← sensing face flush at housing top (where knob was)
[ custom PCB ]           ← ESP32-C3-MINI-1 on the underside; sensor FPC folds down to it
[ gold pads ]            ← on PCB bottom, land on the keyboard's pogo pins (J4/J11)
   housing screws into the slot's threaded boss (the round hole in the daughterboard)
```

- **Springs are keyboard-side** (J4/J11 pogo pins) → the module's side is just **flat gold pads on the PCB bottom**. No mating connector to buy. (Confirm from the knob-underside photo.)
- **Back the sensor against the housing** so finger-press force lands on plastic, not the PCB/FPC solder joints.
- Sensor→PCB link: short folded **FPC ribbon** (Apple-style) or a board-to-board mezzanine connector. FPC exit must stay within the 19 mm outline or fold inward.
- **Antenna** end of the MCU points to the plastic side of the slot (metal blocks BLE) — see [[touchid/Firmware and PCB|Firmware and PCB]].

## Sensor shortlist (fit + FPC + protocol)

Prefer the `0xEF01` family (keeps tinyTouch firmware ~unchanged) with an **FPC tail**, body ≤ ~16 mm. Verify exact dims against each datasheet.

| Sensor | Shape / size | FPC ribbon | Protocol → firmware | Notes |
|---|---|---|---|---|
| **Hi-Link ZW-series** (ZW101 / square **ZW0608**) | round or square, small | some variants — confirm | `0xEF01` → none | same family as tinyTouch; square option good |
| **GROW R502-B** | round, ~15 mm sensing | **yes (FPC 0.5 mm 6-pin)** | GROW `0xEF01` → ~none | verify outer Ø + thickness (one listing ~8.4 mm — maybe too thick) |
| DFRobot **SEN0542** | round Ø19 | yes (FPC conn) | ID809 → **port** | Ø19 = edge-to-edge, no bezel; great docs |

> [!note] Apple reference
> Apple's Touch ID die is only **8 × 8 mm** (170 µm thin), on a flex, under sapphire — you can't buy it (custom AuthenTec silicon bound to the Secure Enclave). Buyable small-die-on-flex sensors (Goodix/FPC) have proprietary drivers → not worth the fight. Hence the open-protocol ZW/GROW modules. Active sensing area on those is small (~5–8 mm); the rest of the body is bezel/electronics.

## Housing — printing + material

### Where to print at UBC
Details + access in [[touchid/UBC Facilities and Contacts|UBC Facilities and Contacts]]. Summary:
- **HATCH Makerspace (ICICS 061B)** — FormLabs **Form 2 (SLA resin)** = best detail for a small precise part; also FDM. Access gated (HATCH/sponsor; contact the technician).
- **ECE Makerspace** — FDM printer farm + soldering station. ECE-access (CS uncertain — verify).
- Broadly accessible / off-campus fallback: UBC Physics & Astronomy 3D printing service, VPL Inspiration Lab, MakerLabs (paid), or any cheap FDM.

### Material — it needs to hold screws
> [!tip] Recommended: FDM **PETG + brass heat-set inserts**
> - **PETG** is tougher and less brittle than PLA — it won't crack around screw bosses like PLA does, and it's easy to print. Good default for a functional part with screws.
> - For any screw that gets driven/removed repeatedly (module retention screw, housing screws), don't thread into bare plastic — press in **brass heat-set threaded inserts** with a soldering iron. This is the robust, reusable way to put machine screws into printed parts. Works great in PETG/ABS/PLA.

Alternatives:
- **SLA resin (Form 2)** — best surface finish + fine detail, ideal at 19 mm scale. Caveat: standard resin is **brittle**, and heat-set inserts don't work well (resin doesn't remelt) → use **glued-in inserts** or generously-sized self-tapping bosses, and pick a **Tough/Durable** resin, not standard.
- **ABS/ASA** — strong, good threads, but warps and fumes (needs enclosure).
- **Nylon (PA)** — excellent mechanical/threads, but hard to print (moisture-sensitive).
- **PLA** — fine for a throwaway fit-check prototype; too brittle for a screwed final part.

**Suggested plan:** fit-check prototypes in **PLA/PETG (FDM)** to dial in dimensions cheaply → final in **PETG + heat-set inserts** (durable) or **SLA tough resin** (prettiest) with glued inserts. Design screw bosses for inserts (straight-wall hole sized to the insert, ~e.g. M2/M2.5).

## Related
- [[touchid/Firmware and PCB|Firmware and PCB]]
- [[touchid/Architecture and Design|Architecture and Design]]
- [[touchid/UBC Facilities and Contacts|UBC Facilities and Contacts]]
