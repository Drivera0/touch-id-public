# FLASH JIG — SHOPPING LIST (verified 2026-09-01)

What the printed jig (`flash_jig.stl` + lever + plunger) needs to become a
working flashing station. Quantities come from `cad/pcb-v3/gen_flash_jig.py`.

## The honest DigiKey answer first

**The pogo pins are NOT on DigiKey.** The jig's bores are sized for the
**P75-E2** probe (Ø1.02 barrel, 16.5 mm long — it must reach through the
13 mm deck). DigiKey carries precision Mill-Max spring pins instead, and the
closest match (0906-1-15-20-75-14-11-0) is only 5.9 mm long — checked
2026-09-01, unusable here. Do not substitute; buy P75-E2 where it's sold.

## The list

| # | Item | Qty | Where | Notes |
|---|---|---|---|---|
| 1 | **P75-E2 pogo pins**, Ø1.02 barrel, 16.5 mm | 6 used (buy a 100-pack, ~$10–15) | Amazon.ca (e.g. ASIN B0BYK8JNKB) or Walmart.ca | 5 wired J3 pins + 1 unwired helper; spares matter — tips bend |
| 2 | **Hookup wire, 28–30 AWG stranded, silicone**, ≥5 colors | 1 small kit | **DigiKey.ca** — Hookup Wire category (Adafruit/BKL silicone-wire kits) or any starter multi-color kit | one color per J3 signal; silicone survives soldering close to the insulation |
| 3 | **Heat-shrink assortment**, 1.5–3 mm | 1 kit | **DigiKey.ca** or any hardware store | over each pin-tail solder joint |
| 4 | **MuseLab Mini DAPLink-HS** (CMSIS-DAP probe) | 1 | AliExpress / Seeed — not on DigiKey | already chosen; pyOCD target `nrf52840` |
| 4b | *DigiKey-stocked alternative:* **Raspberry Pi Debug Probe** | (1) | **DigiKey.ca**, ~$18 CAD — search "Raspberry Pi Debug Probe" (SC0889) | also CMSIS-DAP, works with pyOCD; buy only if the MuseLab falls through — verify the listing before ordering |
| 5 | **3.6 V supply** for VSTOR while flashing | 1 | Chosen: MiniWare MDP-P906, official AliExpress store (see chat notes) — not DigiKey | bench-style CC/CV; NEVER 5 V onto VSTOR |
| 6 | Thin solder (0.5–0.8 mm) + flux | — | anywhere | — |

## Assembly reminders

- Wiring map: `J3-flashing-hookup.png` in this folder. SWDIO SWCLK RESET
  VSTOR GND, west→east; engraved dot = SWDIO end; engraved arrow = the
  board's spacebar/module edge points AWAY from the eject button.
- Solder wires to the pin **tails inside the cavity** — never to the PCB.
  RESET tail: solder a wire and park it, unconnected.
- Wires exit through the bottom arches (west/east/rear) to the DAPLink and
  supply on the desk.
- The helper pin at (−5.25, +0.55) and the ejector plunger connect to nothing.
- Flash power: 3.6 V on VSTOR (probe's 3.3 V alone is not enough; 5 V is
  forbidden — the cell hangs on that rail). Full flow: `../../..​/HANDOFF-FIRMWARE.md`.
