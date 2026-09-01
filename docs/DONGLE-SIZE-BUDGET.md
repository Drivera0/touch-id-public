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

## RECOMMENDATION

Do not let mechanical size block firmware. Bring up FIDO2 + ESB on the
two Nordic PCA10059 dongles first (they are ugly and huge and that is
irrelevant), then spin option 1 with option 2's measurement. A 20 mm nub
that works beats a 9 mm nub that does not exist.

## SOURCES

- Insight SiP ISP1807 Data Sheet R19 — https://www.insightsip.com/fichiers_insightsip/pdf/ble/ISP1807/isp_ble_DS1807.pdf
- GCT USB4155 drawing Rev C — https://gct.co/files/drawings/usb4155.pdf
- Minew MS88SF3 datasheet V1.1 — https://www.minew.com/uploads/MS88SF3_V1.1-nRF52840-Datasheet.pdf
- Raytac MDBT50Q-1MV2 spec Ver.L — https://www.mouser.com/datasheet/3/1361/1/
- Logi Bolt USB-C receiver dims — https://www.bhphotovideo.com/c/product/1922726-REG/
- YubiKey 5C Nano dims — https://www.yubico.com/product/yubikey-5c-nano/
