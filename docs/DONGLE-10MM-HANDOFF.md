# HANDOFF — BUILD THE 10 mm PRODUCTION DONGLE

Purpose: a self-contained brief for (a) a future Claude session and
(b) a human RF/PCB specialist the owner hires. It states what the dongle
is, the size target and why it's hard, the parts, the RF work, and the
certification path. Read the companion docs before starting:
`DONGLE-SIZE-BUDGET.md` (the traced size math), `DONGLE-PCB-HANDOFF.md`
(general dongle brief + first-draft BOM), `DONGLE-HOST-PROTOCOL.md`
(USB↔host wire format), `AUTH-CRYPTO.md` (knob↔dongle security).

The owner is a **beginner at electronics.** Explain choices; never invent
a dimension, pin, or part number — trace it or mark it UNCONFIRMED.

---

## 1. WHAT THIS DEVICE IS

A USB-C wireless receiver dongle, the companion to a fingerprint knob
that lives in a keyboard. Think **Logitech Bolt receiver** in size. The
knob (separate, already designed at pcb-v7: nRF52840 + HLK-ZW0922 sensor,
harvest-powered) reads and matches the fingerprint ON the knob. This
dongle:

- receives over **proprietary 2.4 GHz (Nordic ESB/Gazell)** from the knob,
- presents to the computer as a **USB FIDO2 security key** (+ a USB HID
  keyboard for lock-screen password typing),
- holds the per-site FIDO2 keys and does the signing (the authenticator);
  the knob only sends "verified: owner's finger — authorized."

It is, functionally, a YubiKey Bio whose fingerprint sensor lives in the
keyboard instead of on the key. Firmware base: **OpenSK** (FIDO2/CTAP2 on
nRF52840) + our ESB link + our HMAC challenge-proof.

## 2. THE SIZE TARGET AND WHY IT'S THE HARD PART

Target: **~10 mm of visible nub** (Bolt class; Bolt is 15.24 mm total,
~8-9 mm visible after the ~6.5 mm USB-C insertion depth).

Established in DONGLE-SIZE-BUDGET.md:
- **Width and height are already Bolt-class** with any nRF52840 approach.
- **Only length is hard, and the entire overage is the antenna.**
- A **pre-certified module cannot hit 10 mm** — its fixed antenna
  keep-out (ISP1807: 4 mm) forces ~20 mm. Modules are the EASY, BIGGER
  path (good for prototyping, not for 10 mm).
- **10 mm requires the bare-chip route**: bare nRF52840 (7×7 mm aQFN73,
  or the smaller WLCSP) + your own antenna + your own RF matching. This
  is exactly what Logitech/Yubico do; it is the actual engineering cost,
  not the money.

## 3. PARTS (bare-chip BOM)

Copy exact passive/crystal/inductor values from **Nordic's published
nRF52840 reference design** — do not invent them.

| # | part | qty | purpose |
|---|---|---|---|
| 1 | nRF52840 (aQFN73 7×7, or WLCSP for smaller) | 1 | MCU + 2.4 GHz + USB + crypto (CryptoCell CC310) |
| 2 | 32 MHz crystal (HFXO) + 2 load caps | 1 | REQUIRED for USB clock accuracy |
| 3 | 32.768 kHz crystal (LFXO) + 2 caps | 0-1 | optional; can use internal RC |
| 4 | antenna — chip antenna or tuned PCB trace | 1 | 2.4 GHz to the knob |
| 5 | RF pi-match network (≈2C + 1L, 0402) | ~3 | antenna tuning; values BY MEASUREMENT |
| 6 | USB-C connector (USB 2.0 FS is enough) | 1 | data + power |
| 7 | USB ESD protection (e.g. USBLC6-2SC6) | 1 | protect D+/D- |
| 8 | decoupling caps (100 nF ×several + bulk µF) | ~8 | power-pin stability |
| 9 | DC/DC inductors (per Nordic reference) | 2 | internal buck; optional (LDO mode OK on USB) |
| 10 | status LED + resistor | 0-2 | optional |
| 11 | secure element (NXP SE050 / Microchip ATECC608) | 0-1 | optional; certified-grade key storage |

## 4. THE RF WORK (what the specialist is actually for)

This is why a specialist is worth hiring. The hard, skill-gated tasks:

1. **Antenna choice + placement.** 2.4 GHz chip antenna or a tuned PCB
   trace (inverted-F / meander). MUST sit at the FAR end from the USB-C
   plug — the plug's metal shell is a grounded slab that kills an antenna
   near it. Every commercial receiver puts the antenna at the tip.
2. **Impedance matching** the antenna to the nRF52840's 50 Ω RF pin via
   the pi-network (item 5), tuned with a **NanoVNA** (or the specialist's
   lab VNA). This is the iterate-and-measure step.
3. **Ground plane + layer stack.** Likely 4-layer, controlled impedance,
   0.8 mm total (a USB-C mid-mount plug wants a thin board).
4. **Keep-out trade.** DONGLE-SIZE-BUDGET.md option 2: because the
   knob↔dongle link is ~1 m across a desk, a few dB of antenna loss is
   affordable. The specialist can deliberately shrink the keep-out and
   measure the RSSI cost — this is how the last millimetres are bought.

If hiring: ask for a 2.4 GHz **RF layout + antenna tuning** specialist
(the same skill set as BLE/Zigbee product design). Give them this doc,
DONGLE-SIZE-BUDGET.md, and the Nordic nRF52840 reference design.

## 5. FLASHING & BOOT

- Production sealed unit: **USB bootloader** (Nordic Open Bootloader or
  Adafruit UF2) so it reflashes over its own USB-C, no probe. Reserve a
  couple of SWD test pads anyway for factory bring-up / recovery.
- Set **APPROTECT** (debug-port lockout) on production firmware since the
  dongle holds FIDO2 keys and (for the HID lane) a login password.

## 6. CERTIFICATION — a SELLING cost, not a building cost

- **For the owner's personal use: NO certification needed.** A bare-chip
  10 mm dongle built for yourself is legal to build and use.
- **To SELL it:** a bare chip + own antenna is an "intentional radiator"
  and needs **FCC (US) / CE-RED (EU)** certification via an accredited
  test lab. Ballpark **$3k-10k** + lab time. (This is the cost a
  pre-certified module would have avoided — the module trades size for
  skipping this. At 10 mm you take the cert on yourself.)
- If cert cost is unacceptable, the fallback is the ~20 mm module dongle
  (ISP1807), which carries modular certification and skips most of this.

## 7. COST (personal proof-of-concept, before any commercial decision)

From DONGLE-SIZE-BUDGET.md / session estimate 2026-09-01:
- 5 assembled boards from a fab (JLCPCB-class), one spin: ~$120-200.
- NanoVNA for antenna tuning: ~$50. Debug probe: already owned (MuseLab
  DAPLink from the knob project).
- RF rarely works first try — budget 2-3 board spins.
- **Realistic personal PoC total: ~$300-500**, plus the RF design time.

## 8. RECOMMENDED SEQUENCE (do NOT build the 10 mm board first)

This is how every hardware company does it, not a compromise:
1. **Firmware PoC on dev boards** — receiver = Nordic nRF52840 Dongle
   (PCA10059, OpenSK-supported); knob stand-in = nRF52840 DK (PCA10056)
   with the ZW0922 wired to its headers. Prove the whole chain.
2. **Intermediate module board (~20 mm, ISP1807)** — proves the real
   link + enclosure with NO RF-design or cert. Optional but de-risking.
3. **10 mm bare-chip board** — LAST, once the product is proven and worth
   the RF + (if selling) certification effort. Same firmware throughout,
   so nothing is wasted.

## 9. WHAT TO HAND A SPECIALIST

- This doc + DONGLE-SIZE-BUDGET.md (size math, part numbers, sources).
- The BOM (section 3) and Nordic's nRF52840 reference design.
- The mechanical target: ~10 mm visible nub, USB-C, sealed.
- The one ask that needs their expertise: **antenna + RF matching + layer
  stack for a 2.4 GHz nRF52840 in a Bolt-sized USB-C body, and the
  keep-out-vs-range trade for a 1 m link.**
- Everything else (firmware, protocol, knob) is done or specified — they
  only need to deliver the RF-correct small board.
