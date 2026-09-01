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

**Lee's Electronics walk-in (4131 Fraser St, Mon–Fri 9–5:30), ~CA$22 — all
links verified live 2026-09-01:**

| Item | Qty | Price | Link |
|---|---|---|---|
| [Wire-wrap wire 30 AWG BLACK, 50 ft](https://leeselectronic.com/en/product/1018800-wire-wrapping-wire-30awg-black-50ft-pkg.html) | 1 | CA$3.80 | product 1018800 |
| [RED](https://leeselectronic.com/en/product/1018802-wire-wrapping-wire-30awg-red-50ft-pkg.html) · [ORANGE](https://leeselectronic.com/en/product/1018803-wire-wrapping-wire-30awg-orange-50ft-pkg.html) · [YELLOW](https://leeselectronic.com/en/product/1018804-wire-wrapping-wire-30awg-yellow-50ft-pkg.html) · [GREEN](https://leeselectronic.com/en/product/1018805-wire-wrapping-wire-30awg-green-50ft-pkg.html) · [BLUE](https://leeselectronic.com/en/product/1018806-wire-wrapping-wire-30awg-blue-50ft-pkg.html) | 4 of these | CA$3.80 each | 5 colors total → one per J3 signal |
| [Heat shrink 2.0 mm 2:1 BLACK, per metre](https://leeselectronic.com/en/product/176020-heat-shrink-20mm-2-1-black.html) ([CLEAR](https://leeselectronic.com/en/product/177020-heat-shrink-20mm-2-1-clear.html) / [RED](https://leeselectronic.com/en/product/170020-heat-shrink-20mm-2-1-red.html)) | 1 m | CA$1.10 | one metre covers all six joints many times over |
| [Solder 60/40 rosin core, **0.8 mm**, 14 g](https://leeselectronic.com/en/product/10693-10693solderleadedrosincore08mm17.html) | 1 | CA$4.00 | 0.8 mm beats the 1.0 mm at the same price for these small joints |

Lee's total: 5 × $3.80 + $1.10 + $4.00 = **CA$24.10** (or $16.50 with 3 wire colors).

**Pogo pins — the one thing Lee's can't supply.** Their only pogo is the
P125-B (Ø2.0 mm): five of those barrels on the J3 row's 2.0 mm pitch touch
each other and short every signal — ruled out by geometry, not preference.
No-waste buy, verified live:
* **[AliExpress: "10pc P75 Series Pogo Pins 1.02mm Dia" — 10 pcs, C$1.40](https://www.aliexpress.com/item/1005008087364831.html)**
  — **pick the "P75-E2" variant** (conical head) in the option selector, it's
  there. Add it to the MuseLab DAPLink cart: same order, no extra shipping,
  only 4 spare pins. Slow (2–4 wk) but the probe order sets the timeline.
* [Amazon.ca 100-pack, CA$9.99](https://www.amazon.ca/dp/B0D48VHRY4) — only if speed matters.

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

## Desoldering the sensor's XH-1.00 6-pin connector (+ tools) — Lee's, verified 2026-09-01

The ZW0922's vertical connector is 4.5 mm tall and MUST come off (0.4 mm of
room above the cell). Buy at Lee's, ~CA$29–42:

| Item | Price | Why |
|---|---|---|
| [Desoldering wick, anti-hot, 1.5 mm / 2 m](https://leeselectronic.com/en/product/18659-desoldering-wick-anti-hot-15mm-2-meter.html) | CA$8.50 | 1.5 mm matches the 1.0 mm-pitch pads — wider braid bridges neighbors |
| [Soldering paste flux, 10 g](https://leeselectronic.com/en/product/42381-soldering-paste-flux-10g.html) | CA$4.80 | wick barely works dry; flux makes it drink solder |
| [Side cutter 5" RT-100](https://leeselectronic.com/en/product/10781-tool-5-side-cutter-rt-100.html) | CA$7.50 | to cut the connector's plastic shroud off first |
| [Tweezer, antistatic, fine tip TST-10](https://leeselectronic.com/en/product/10263-10263tooltweezerfinetipwl2010.html) (or [narrow TST-11](https://leeselectronic.com/en/product/16494-tool-tweezer-fine-narrow-tip-tst-11.html)) | CA$3.95 | to pull each freed pin |
| [Isopropyl 99.9%, 100 ml](https://leeselectronic.com/en/product/4285-isoproyl-alcohol-824-100ml.html) | CA$13.50 | flux-residue cleanup (a pharmacy 99% bottle also works, cheaper) |
| optional: [Xcelite flush cutter 170MVN](https://leeselectronic.com/en/product/16956-xcelite-diagonal-shear-cutter-5-flush-jaw-20-awg.html) | CA$25.55 | nicer cutter, not required |

**Beginner method — never lever all 6 pins at once:**
1. Snip the connector's plastic shroud away with the cutter until only six
   bare pins stand in the pads. Cut plastic, never pull on pads.
2. One pin at a time: grip with tweezers, touch the iron to its joint, lift
   it out the moment the solder melts.
3. Flux on the pads, lay the wick on, press the iron on top of the wick —
   lift wick and iron TOGETHER (a cooled wick stuck to the pad rips it off).
4. Swab with isopropyl. Pads should be flat and shiny; then solder the wires.

The sensor die is on the other side of that little board — keep each iron
touch under ~3 s, rest between. Buy a spare module; the first one is
practice (BUY-YOURSELF.md already says this).

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
