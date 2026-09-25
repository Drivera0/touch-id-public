# DONGLE SIZE BUDGET — WHY "LOGI BOLT SMALL" IS HARD

Written 2026-08-31 after the user hit a wall sourcing an nRF52840 module
small enough for a Logi-Bolt-class USB-C receiver. Every number below is
traced; anything unconfirmed is marked **UNCONFIRMED**.

## THE TARGET

| Reference part | Overall size (mm) | Has a 2.4 GHz radio? | Source |
|---|---|---|---|
| Logi Bolt USB-C receiver | 15.24 x 12.7 x 7.62 (0.6" x 0.5" x 0.3") | YES | B&H / Staples spec listing |
| YubiKey 5C Nano | 12 x 10.1 x 7 | no (wired only) | yubico.com product page |

USB-C insertion depth eats ~6.5 mm of that 15.24 mm, so the Bolt's
**visible nub is only ~8-9 mm long**. That is the number that is hard.

## THE REAL CONSTRAINT IS NOT THE CHIP

The nRF52840 die package (aQFN73) is **7 x 7 mm** (Minew MS88SF3
datasheet, s.3.1). Size is lost to three other things:

1. **The pre-certified module wrapper** (crystals, DC-DC, matching, antenna).
2. **The module's ANTENNA KEEP-OUT** — copper-free space that must exist
   next to the antenna or range collapses.
3. **The USB-C plug + shell walls.**

### Candidate modules (all nRF52840, all with USB D+/D- brought out)

| Module | Size (mm) | Antenna | Notes | Source |
|---|---|---|---|---|
| Raytac MDBT50Q-1MV2 (knob's module) | 15.5 x 10.5 x 2.05 | chip | **Alone it is the entire Bolt body.** Dead end for the dongle. | Raytac spec Ver.L |
| Minew MS88SF3 | 18.5 x 12.5 x 2.0 | PCB trace | JLCPCB-stocked (C20416747) but too long. USB pads confirmed (s.8.1). | Minew DS V1.1 |
| **Insight SiP ISP1807(-LR)** | **8.0 x 8.0 x 1.0** | integrated | LGA, 62 pads, 0.65 mm pitch. USB **D+ (pad 8), D- , VBUS (pad 12)** confirmed. FCC/IC/CE/TELEC/KCC/NCC/CCC/Anatel. | isp_ble_DS1807 R19, s.4.1/4.3 |

ISP1807 is the only pre-certified nRF52840 module found that is smaller
than the Bolt's internal volume.

### THE ISP1807 TRAP — THE KEEP-OUT, NOT THE MODULE

isp_ble_DS1807 R19 s.4.3 "Antenna Keep-Out Zone": *"no metal, no traces
and no components on any application PCB layer except mechanical LGA
pads."* The drawing annotates **4.0 mm** (depth from the antenna edge)
and **18.0 mm min** (width of the zone). **UNCONFIRMED:** read the
drawing yourself before laying out — 18 mm is wider than the whole
dongle, so Insight SiP must be asked what degradation a narrower zone
costs.

Keep-out is a *metal* exclusion, not a *plastic* one: the PCB can simply
END there and the 4 mm can be air inside the shell, with the module
overhanging the board edge. That is how the length is bought back.

## USB-C PLUG

| Part | Overall (mm) | Required PCB thickness | Notes | Source |
|---|---|---|---|---|
| GCT USB4155 (USB 3.2 Gen2 Type-C plug, horizontal SMT, 24 contacts) | 15.50 x 8.00 x 2.90 | **0.80 +/- 0.05** | Mid-mount: the board slots INTO the connector, so board and plug share the same height. 10,000 mating cycles. | GCT drawing USB4155 Rev C, 12/12/24 |

**0.8 mm board is mandatory** for that part — say so on the JLCPCB order;
the default is 1.6 mm. A 24-contact USB 3.x plug is overkill for FIDO2
(full-speed USB 2.0 is enough); a USB 2.0-only Type-C plug may be cheaper
and easier to assemble — **UNCONFIRMED**, not yet sourced.

**The metal USB-C shell is a grounded slab sitting inside the host port.**
Put the antenna at the FAR end of the dongle, never near the plug. This
is why every commercial receiver has the antenna at the tip.

## BUDGET (ISP1807 route, order along the insertion axis)

| Segment | mm |
|---|---|
| Plug portion inside the host port | ~6.5 (USB-C spec insertion depth) |
| Connector's on-board footprint | ~9 (**UNCONFIRMED** split of the 15.50 overall — measure off the GCT drawing) |
| ISP1807 body | 8.0 |
| Antenna keep-out (air, no copper) | 4.0 |
| End wall | ~0.8 |
| **Total length** | **~28**, of which **~22 visible** |

Width: 8.0 module + clearance + walls = **~11-12 mm** (Bolt is 12.7 — FINE).
Height: 0.8 board + 1.0 module + walls = **~4-6 mm**, and the plug itself
is 2.90 (Bolt is 7.62 — FINE).

**So width and height are already Bolt-class. Only LENGTH is over, and
the whole overage is the antenna keep-out.** Landing zone is a normal
YubiKey 5C (not Nano) sized nub, not a Bolt.

## OPTIONS

1. **ISP1807 + accept ~20 mm of nub.** Only pre-certified path to
   near-Bolt size. Costs: LGA 0.65 mm pitch (machine assembly only, no
   hand soldering, check JLCPCB stock/consigned parts), higher unit price.
2. **Shrink the keep-out on purpose.** The link is knob-to-dongle across
   one desk (~1 m). A few dB of antenna loss is affordable here in a way
   it would not be for a 10 m product. Prototype two versions of the
   board — full keep-out and squeezed — and measure RSSI. Cheap.
3. **Bare nRF52840 aQFN73 (7 x 7) + own antenna.** True Bolt size. Costs
   full FCC/CE *intentional radiator* certification (thousands) plus RF
   layout skill. **NOT a v1 move.** Revisit only if this sells.

## PRODUCTION TARGET DECIDED (2026-08-31): 9 mm VISIBLE NUB (Bolt-class)

The user committed to a Bolt-class 9 mm-protrusion production dongle.
That means **OPTION 3 is the production route** — a pre-certified module
cannot hit 9 mm (its fixed antenna keep-out is the whole overage). 9 mm
is how Logitech/Yubico do it: bare radio silicon + own antenna + self-
certification. Concretely:

- **Bare nRF52840 (aQFN73, 7x7) or WLCSP** on our own PCB.
- **Own antenna** (chip antenna or tuned PCB trace) + impedance matching
  — this is real RF-design work, the actual hard part (not the size).
- Target length: ~9 mm visible + ~6.5 mm insertion = ~15.5 mm total,
  matching the Bolt (15.24). Width/height already fit.
- **Certification is a SELLING cost, not a building cost.** A bare-chip
  9 mm dongle for the user's OWN use needs no certification. Selling it
  needs FCC/CE intentional-radiator cert: ~$3-10k + test lab.

### Sequencing (do NOT build the 9 mm board first)

This is how every hardware company does it, not a compromise:
1. Firmware bring-up on the ugly dev dongles (PCA10059) — size irrelevant.
2. Optional intermediate: ISP1807 module board (~20 mm) to prove the
   real link + enclosure cheaply, no RF-design or cert needed.
3. Production: the 9 mm bare-chip certified board — LAST, once the
   product is proven and there's reason to spend the RF + cert effort.

The firmware is identical across all three, so nothing is wasted.
A 20 mm nub that works today does not block the 9 mm nub later.

## SOURCES

- Insight SiP ISP1807 Data Sheet R19 — https://www.insightsip.com/fichiers_insightsip/pdf/ble/ISP1807/isp_ble_DS1807.pdf
- GCT USB4155 drawing Rev C — https://gct.co/files/drawings/usb4155.pdf
- Minew MS88SF3 datasheet V1.1 — https://www.minew.com/uploads/MS88SF3_V1.1-nRF52840-Datasheet.pdf
- Raytac MDBT50Q-1MV2 spec Ver.L — https://www.mouser.com/datasheet/3/1361/1/
- Logi Bolt USB-C receiver dims — https://www.bhphotovideo.com/c/product/1922726-REG/
- YubiKey 5C Nano dims — https://www.yubico.com/product/yubikey-5c-nano/

## APPENDIX — BUYABLE CONSUMER DONGLES, SMALLEST FIRST

Added 2026-08-31. Vendors almost never publish receiver dimensions;
these are the ones that ARE published. Anything not listed here was
searched for and found undocumented.

| Product | Port | Overall (mm) | Radio? | Source |
|---|---|---|---|---|
| YubiKey 5C Nano | USB-C | 12 x 10.1 x 7 | **NO** (wired) | yubico.com |
| **Logi Bolt USB-C receiver (956-000156)** | USB-C | **15.24 x 12.7 x 7.62** | 2.4 GHz | B&H / Staples listing |
| Logi Bolt USB-A receiver (956-000007) | USB-A | 18.65 x 14.4 x 6.11 | 2.4 GHz | Logitech spec via B&H |
| Matias DC20 "USB-C Nano Receiver" | USB-C | **NOT PUBLISHED** ($19.95) | 2.4 GHz | matias.store/products/dc20 |
| Avantree C81-PC | USB-C | 26 x 14 x 7 | BT 5.3 | Amazon listing |
| TP-Link UB5A nano | USB-A | 18.9 x 14.8 x 6.8 | BT 5.3 | eTeknix review |

**CONCLUSION: the Logi Bolt USB-C receiver is the smallest consumer
USB-C dongle with a 2.4 GHz radio that publishes its size.** Nothing
documented beats it. It is the benchmark to hold against a mock-up.

Note the USB-A Bolt is thinner (6.11 vs 7.62 mm) — a USB-A tongue is a
thin blade, a USB-C plug is a 2.56 mm-thick shell. **Choosing USB-C
costs ~1.5 mm of height before any of our parts exist.**

Also on hand for free: the **NuPhy Air75 V3's own 2.4 GHz dongle**.
Measure it with calipers — it is the most relevant real-world sample
since it talks to the same keyboard.

**DO NOT plan on gutting a commercial receiver for its shell**
(**UNCONFIRMED**, but these are welded and molded tightly around their
own PCB). Their value is as a caliper reference and a 3D-print target.
