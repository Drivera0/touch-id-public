# HANDOFF — DESIGN THE DONGLE PCB (for a hardware-focused Claude session)

You are being asked to help design a **USB-C wireless receiver dongle**,
the companion to an existing fingerprint knob. Think **Logitech Bolt
USB-C receiver**: compact, sealed, barely protrudes from the port. This
doc is the brief. The person is a **beginner at electronics — explain,
don't assume; never invent a part number or dimension.**

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
