# FLASH JIG — SHOPPING LIST (verified 2026-09-01)

What the printed jig (`flash_jig.stl` + lever + plunger) needs to become a
working flashing station. Quantities come from `cad/pcb-v3/gen_flash_jig.py`.

## The honest DigiKey answer first

**The pogo pins are NOT on DigiKey.** The jig's bores are sized for the
**P75-E2** probe (Ø1.02 barrel, 16.5 mm long — it must reach through the
13 mm deck). DigiKey carries precision Mill-Max spring pins instead, and the
closest match (0906-1-15-20-75-14-11-0) is only 5.9 mm long — checked
2026-09-01, unusable here. Do not substitute; buy P75-E2 where it's sold.

## NO-WASTE PLAN (user's preference: buy only what's needed) — 2026-09-01

**Lee's Electronics walk-in (4131 Fraser St, Mon–Fri 9–5:30), ~CA$18:**

| Item | Qty | Price |
|---|---|---|
| 30 AWG wire-wrap wire, 50 ft spools (pick 5 colors) | 5 | CA$3.80 each = $19.00 — or buy 2–3 colors ($7.60–11.40) and tag wires with tape labels |
| Heat shrink 2.0 mm 2:1, per length | 2 | CA$0.90–1.10 each |
| Solder, 60/40 rosin core, 17 g mini spool | 1 | CA$4.00 (their 1 lb spools are $22.50–58 — skip) |

**Pogo pins — the one thing Lee's can't supply.** Their only pogo is the
P125-B (Ø2.0 mm): five of those barrels on the J3 row's 2.0 mm pitch touch
each other and short every signal — ruled out by geometry, not preference.
Smallest sane P75-E2 buys:
* **AliExpress: 10–20 pc packs, ~CA$2–4** — add to the MuseLab DAPLink order,
  same cart, no extra shipping, no 94 spare pins. Slow (2–4 wk) but the
  probe order sets the timeline anyway.
* Amazon.ca 100-pack CA$9.99 (amazon.ca/dp/B0D48VHRY4) — only if speed matters.

The jig (v2.1) has counterbore head-seats sized for the P75-E2's Ø1.3 conical
head — the user's seat-and-small-hole idea, applied to the pin that fits.

## Best CAD prices (checked live 2026-09-01)

| Item | Price | Link |
|---|---|---|
| **P75-E2 pins, 100 pcs, 16.5 mm** (PURPLELILY, ships from Amazon) | **CA$9.99** (only 4 packs left; free ship on $35+) | amazon.ca/dp/B0D48VHRY4 |
| **BOJACK 30 AWG silicone wire kit, 5 colors × 32.8 ft + 20 heat-shrink tubes + mini stripper** — covers wire AND heat-shrink in one | **CA$19.99**, free delivery next day | amazon.ca — search "BOJACK 30 AWG silicone wire kit heat shrink" |
| alt: BNTECHGO 30 AWG kit, 10 colors × 10 ft (wire only) | CA$14.26 | amazon.ca — search "BNTECHGO 30 gauge silicone wire kit" |
| alt: **Lee's Electronics** (4131 Fraser St, walk-in, Mon–Fri 9–5:30) — 30 AWG wire-wrap wire, solid core, CA$3.80 per 50 ft spool per color | CA$19.00 for 5 colors | leeselectronic.com — search "wire wrap 30awg" |

Lee's pogo pins are P125-B (Ø2.0 mm, 33 mm) — too fat for the jig's Ø1.15
bores, don't substitute. Their heat-shrink kit (CA$20) was out of stock.
Best combo: pins CA$9.99 + BOJACK kit CA$19.99 ≈ **CA$30 total** — the
BOJACK's 5 colors map one-per-signal onto SWDIO/SWCLK/RESET/VSTOR/GND.
Note: 30 AWG solid wire-wrap from Lee's also works fine for this jig (joints
are strain-relieved through the arches); stranded silicone is just nicer.

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
