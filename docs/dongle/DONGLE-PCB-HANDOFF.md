# HANDOFF — DESIGN THE DONGLE PCB (for a hardware-focused Claude session)

You are being asked to help design a **USB-C wireless receiver dongle**,
the companion to an existing fingerprint knob. Think **Logitech Bolt
USB-C receiver**: compact, sealed, barely protrudes from the port. This
doc is the brief. The person is a **beginner at electronics — explain,
don't assume; never invent a part number or dimension.**

## SIZE — the honest budget is in docs/dongle/DONGLE-SIZE-BUDGET.md; read it first

Do NOT hand-wave "the chip is 7 mm so it's fine." A prior session traced
the real mechanical floor; the summary:

- Width and height ARE Logi-Bolt-class already. Only LENGTH is over.
- The whole length overage is the **antenna keep-out** on a pre-certified
  module, not the silicon. YubiKey Nano is NOT a valid size proof — it
  has no radio, so no antenna keep-out.
- Smallest pre-certified nRF52840 module with USB brought out is the
  **Insight SiP ISP1807 (8x8x1.0)**; its 4 mm keep-out pushes the nub to
  roughly **YubiKey-5C size (~20 mm visible), not Bolt (~9 mm)**.
- Realistic v1: accept the ~20 mm nub, and/or shrink the keep-out on
  purpose (the link is a 1 m desk hop, so a few dB loss is fine — build
  two boards and measure). True-Bolt-tiny needs a bare nRF52840 + own
  antenna + full intentional-radiator certification — NOT a v1 move.

Design target: a sealed YubiKey-5C-class nub. Full trace, part numbers,
and the length budget: **docs/dongle/DONGLE-SIZE-BUDGET.md**.

## WHAT THIS DONGLE IS

The fingerprint sensor and matching live in a separate **knob** module
(already designed, frozen at pcb-v7, nRF52840 + HLK-ZW0922). This dongle
is the knob's **USB face**: it receives over 2.4 GHz from the knob and
presents to the computer as a USB device (a FIDO2 security key + a USB
keyboard). It is a receiver, like a wireless-mouse dongle — but with a
little more brains (it does the FIDO2 signing; see below).

Firmware and product decisions are LOCKED (see docs/firmware/CODING-PLAN.md and
docs/firmware/ROADMAP.md). Your job is the **hardware**: schematic + PCB + a case,
Logi-Bolt-small, USB-C.

## HARD REQUIREMENTS (from the locked design)

1. **MCU/radio: Nordic nRF52840** — it does 2.4 GHz radio AND native USB
   in one chip (why the dongle can be tiny). Prefer a **pre-certified
   module** (e.g. the same Raytac MDBT50Q family the knob uses, or a
   smaller nRF52840 module) so the radio carries FCC/CE modular cert —
   the beginner should not pay for full radio certification.
2. **Connector: USB-C** (data, USB 2.0 full-speed is enough for FIDO2 HID).
3. **Radio to the knob: proprietary 2.4 GHz (Nordic ESB/Gazell)**, not
   BLE. Needs an antenna — the module's built-in chip/PCB antenna is
   fine; DO NOT bury it under a metal case or ground plane.
4. **Form factor: as small as reasonably possible** — target a sealed
   nub roughly the size of a Logi Bolt / YubiKey Nano, minimal protrusion.
5. **Flashing:** must be programmable. Two ways to support — either a
   USB bootloader (so the finished unit flashes over its own USB-C, no
   probe), or small SWD test pads for a probe. USB bootloader is
   preferred for a sealed consumer unit.
6. **Power:** bus-powered from USB (no battery). Simple.
7. Optional: one small status LED.

## FIRST-DRAFT BOM (bare-chip route, for the ~9-10 mm target)

Derived 2026-09-01 by diffing against the knob's netlist. The knob is
mostly harvest + sensor parts (U2 BQ25505, U3/U4 TPS7A2033, BT1, L1, the
ROV/ROK/divider resistors, J2) — the dongle DROPS all of that. It keeps
only the nRF52840 core and ADDS a USB front end.

| # | part | qty | purpose |
|---|---|---|---|
| 1 | nRF52840 (aQFN73 bare) — or MDBT50Q module for a dev board | 1 | MCU + 2.4 GHz radio + USB + FIDO2 crypto (CryptoCell CC310) |
| 2 | 32 MHz crystal (HFXO) + 2 load caps | 1 | required for USB (RC not accurate enough) |
| 3 | 32.768 kHz crystal (LFXO) + 2 caps | 0-1 | OPTIONAL — omit and use RC, like the knob does |
| 4 | antenna — chip antenna or PCB trace | 1 | 2.4 GHz link to the knob |
| 5 | RF matching network (pi: ~2C + 1L, 0402) | ~3 | antenna tuning; values by measurement |
| 6 | USB-C connector | 1 | data + power (knob has NO USB) |
| 7 | USB ESD protection (TVS, e.g. USBLC6-2SC6) | 1 | protect D+/D- |
| 8 | decoupling caps (100 nF x several + a few bulk uF) | ~8 | power-pin stability |
| 9 | DC/DC inductors (per Nordic reference) | 2 | internal buck; optional (LDO mode works on USB) |
| 10 | status LED + resistor | 0-2 | optional, YubiKey-style |
| 11 | secure element (SE050 / ATECC608) | 0-1 | OPTIONAL — certified-grade key storage, later |
| 12 | flashing: SWD pads or USB bootloader | 0 | no added parts either way |

Exact crystal/inductor/cap values: copy Nordic's published nRF52840
reference design — do NOT invent them. Module route (MDBT50Q) folds
items 1-5, 8-9 into the module.

**No knob parts are removed by adding the dongle** — the two devices have
disjoint jobs (knob = harvest + sensor + radio; dongle = USB + FIDO2),
and the knob is frozen at v7 regardless. FIDO2 and the 2.4 GHz protocol
are firmware on the knob's existing nRF52840, not separate parts.

## WHAT TO PRODUCE

1. A parts list (BOM) with real, orderable parts — nRF52840 module,
   USB-C connector, passives, LED, ESD protection on the USB lines.
   Trace every choice; flag anything not confirmed.
2. A schematic (module + USB-C + decoupling + ESD + antenna keep-out).
3. A small 2- or 4-layer PCB layout with the antenna keep-out respected.
4. A note on the enclosure (small injection-molded or 3D-printed shell)
   and how the antenna clearance survives it.
5. A fab/order checklist (JLCPCB-style), like the knob project used —
   but DO NOT order anything; the person places all orders.

## GROUND RULES (inherited from the project)

- Never invent a dimension, pin, or part number; trace every fact to a
  datasheet or say it's unconfirmed.
- Do not order anything or spend money — the person places all orders.
- Commit at milestones. New work = new files; don't overwrite originals.
- A hardware claim only counts when checked against a datasheet /
  design-rule check.

## CONTEXT YOU MAY WANT

- The knob PCB and its methods live in the user's Obsidian vault
  (`.../Foundation/touchid/cad/`), same style: netlist authority,
  preflight gate, JLCPCB DFM. The dongle can follow the same workflow.
- The knob uses the Raytac MDBT50Q-1MV2 (nRF52840) — a known-good,
  pre-certified module choice already validated for this project.
- Why USB-C and small matters: this is intended as a **sellable
  consumer product** eventually (a fingerprint security key whose sensor
  lives in the keyboard). The dongle is the part that plugs into every
  computer, so it must look and feel like a finished receiver.

## FIRST STEP

Confirm the module choice (reuse MDBT50Q vs a smaller nRF52840 module)
WITH the user, then draft the BOM. Ask before assuming the enclosure
process (3D-print for prototypes vs injection-mold for production).
