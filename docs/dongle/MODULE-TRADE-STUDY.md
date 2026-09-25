# Dongle module trade study — can it be Logi Bolt sized?

Date: 2026-08-31
Status: **BLOCKING DECISION — needs user input before any BOM work**

## Bottom line

**A Logi Bolt USB-C sized dongle is not achievable with a pre-certified nRF52840
module.** Not "tight" — geometrically impossible, by a margin that no layout
skill closes. The two hard requirements in the handoff brief are in direct
conflict:

- Req 1: "prefer a pre-certified module … the beginner should not pay for full
  radio certification"
- Req 4: "target a sealed nub roughly the size of a Logi Bolt / YubiKey Nano"

One of them has to give. See "The decision" at the bottom.

## The killing number

| Thing | Length |
|---|---|
| Logi Bolt USB-C receiver, **entire product** | **14.1 mm** |
| Raytac MDBT50Q-1MV2, **module alone** | **15.5 mm** |

The knob's module is **1.4 mm longer than the whole Logitech product**, before
adding a USB-C connector, ESD diodes, decoupling caps, an LED, or any plastic.

Logi Bolt USB-C full dimensions: **7.0 (H) × 12.85 (W) × 14.1 (L) mm**, 0.97 g
— from Logitech's own support page, confirmed against the retailer listings.

## Candidates measured against that envelope

Usable internal PCB width, assuming ~1 mm wall each side: **~10.85 mm**.

| Module | Body L×W×H (mm) | Keep-out demand | Fits 14.1 × 12.85? | Verdict |
|---|---|---|---|---|
| Raytac MDBT50Q-1MV2 | 15.5 × 10.5 × 2.05 | 3.8 mm deep band, **inside its own outline** — costs zero extra board | **No** — 15.5 > 14.1 | Out on length |
| Insight SiP ISP1807 | 8.0 × 8.0 × 1.0 | **18.0 mm min board width**, 4.0 deep, 5.0 mm overhang each side | **No** — 18.0 > 12.85 | Out on keep-out |
| Fanstel BC840M | 12.3 × 7.05 × 1.5 (antenna flares to 10.1 wide) | 5.5 mm beyond board/GND edge | **Marginally yes** | Only survivor — see caveats |
| Fanstel BC840 | 7.1 × 9.2 × 1.5 | 2.5 mm beyond board/GND edge | Yes | **Out — 4 m range** |
| u-blox NINA-B3 | 15.0 × 10.0 × 2.23 | not in datasheet (see gaps) | No — 15.0 > 14.1 | Out on length |
| Ebyte / Minew / Holyiot | 13–23 mm long | **no published number** | — | Can't design to them |

### ISP1807 is the clearest illustration of the trap

Smallest nRF52840 module in existence at 8 × 8 mm — one quarter the footprint of
the Raytac. Its datasheet then demands a minimum host board width of 18.0 mm,
and characterizes its antenna specifically on a "USB dongle ground plane of
18 × 30 mm²". The module that saves the most body area demands the most board.
This is the same finding as the knob (see `touchid-smaller-module-needs-more-board`),
and here it bites harder.

### BC840M — the only geometric survivor, with two open risks

- 12.3 mm long fits inside 14.1 mm. 10.1 mm antenna width fits inside ~10.85 mm.
- **Risk 1:** datasheet says *"keep all external metal at least 30 mm from the
  antenna area."* This dongle plugs into a metal USB-C port on a metal laptop.
  That rule cannot be honored, ever. Probably a range-optimization statement
  rather than a certification condition — **must be confirmed with Fanstel by
  email before committing.**
- **Risk 2:** 5.5 mm of its 12.3 mm length must be free of ground plane. That
  leaves ~6.8 × 7.05 mm of grounded board for the USB-C connector, ESD array,
  decoupling and LED. Extremely tight, not yet proven by a layout attempt.
- Vendor page says 12.2 mm; datasheet and mechanical drawing say **12.3 ± 0.1**.
  Use 12.3. Body width: drawing says 7.05 ± 0.05, spec text says 7.1.

## The reality check: what a certified module dongle actually measures

Fanstel's own shipping product, **USB840M**, is a certified nRF52840 USB dongle
built around the BC840M — i.e. the vendor's own best effort at exactly this
problem, by the people who designed the module.

**26.0 × 15.0 × 6.0 mm.** $14.40 at qty 1, $10.67 at 1k.
FCC X8WBC840, IC 4100A-BC840, CE, RCM, TELEC 201-190140.

That is **1.84× the length** of a Logi Bolt USB-C. It is the strongest available
evidence for where the floor really sits.

## Why Logitech can do it and this project can't (yet)

The Logi Bolt is not a module design. It is a chip-down radio with a custom
antenna tuned to that specific plastic shell, and Logitech paid for full
intentional-radiator certification. That is precisely the cost the handoff brief
says to avoid. The size and the "no certification bill" goal are the same
tradeoff viewed from two sides.

## The decision

**Option A — keep the pre-certified module, accept a larger dongle.**
Realistic target ~20–26 mm long. Protrudes maybe 10–13 mm from the port. Still
a small sealed nub, just not a Logi Bolt. No certification bill. Can be ordered
from JLCPCB on the same workflow as the knob.

**Option B — hold the Logi Bolt size, go chip-down.**
Bare nRF52840 QFN + discrete matching network + custom antenna. Requires full
FCC/CE intentional-radiator testing (real money, typically five figures) and RF
design experience this project doesn't have yet. Directly contradicts brief
req 1.

**Option C — module now, chip-down later.**
Build Option A as the prototype to prove the radio protocol, firmware, FIDO2
stack and the knob pairing. Revisit the size only if it becomes a real product.
Keeps the money and the risk at zero for now.

## Confirmed vs unconfirmed

**Confirmed from primary sources:**

- Logi Bolt USB-C 7.0 × 12.85 × 14.1 mm — Logitech support page
- MDBT50Q-1MV2 15.5 × 10.5 × 2.05 mm, tol −0.15/+0.20 — Raytac spec Ver.L §2.1 p.7
- MDBT50Q keep-out 3.8 mm deep, all layers, flush with the antenna-end edge —
  Raytac Ver.L §2.2 p.9, Ver.K §2.2 p.9, DG RF-layout PDF (4 independent places)
- ISP1807 18.0 mm minimum board width — datasheet R19 §4.3 p.14
- BC840M 12.3 × 7.05, antenna region 10.1 wide, keep-out 5.5 mm beyond edge
- BC840 range 4 m at 1 Mbps — stated 3× in Fanstel datasheet Ver 1.08
- USB840M 26.0 × 15.0 × 6.0 mm, pricing, cert IDs — Fanstel product page

**Unconfirmed — do not design against these yet:**

1. MDBT50Q keep-out **width** has no number in the current revision (Ver.L says
   only "as wide as possible"). The 12.4 mm figure is Ver.K-only and was
   deliberately removed.
2. No Raytac document states any enclosure, metal, or board-edge clearance.
3. NINA-B3 keep-out is not in its datasheet — lives in the u-blox System
   Integration Manual, not yet retrieved.
4. Ebyte, Minew and Holyiot publish **no numeric keep-out at all**.
5. Whether the BC840M 30 mm metal rule is advisory or a cert condition.
6. Internal PCB dimensions of the Logi Bolt are inferred from external
   dimensions minus assumed 1 mm walls — nobody has published a teardown
   measurement, and the USB-C plug insertion depth was not measured.
7. All Raytac numbers were read from rendered drawing images, not extracted
   text. Re-read Ver.L p.9 before typing anything into a footprint.
