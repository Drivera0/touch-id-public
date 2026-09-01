# Off-the-shelf dongles — buy instead of build

Date: 2026-08-31
Question: is there a finished, compact, USB-C, openly-programmable nRF52840
dongle we can buy, flash, and ship — skipping the PCB, the antenna and the
certification bill?

## Short answer

**Yes, one: Raytac MDBT50Q-CX-40.** It is the only USB-C option found.

## The candidates

| Product | Size (mm, cased) | Connector | Price | Programming | Verdict |
|---|---|---|---|---|---|
| **Raytac MDBT50Q-CX-40** | 26.2 × 15.1 × 6.8 (**excl. connector**) | **USB-C** | ~$8.45–9.50 @1 | Open DFU bootloader + mainline Zephyr board support | **Lead candidate** |
| Fanstel USB840M | 26.0 × 15.0 × 6.0 | USB-A | $14.40 @1 → $10.67 @1k | Nordic USB CDC ACM secure bootloader, button on case | Right size, wrong connector |
| Ezurio BL654 USB (451-00004) | not published | USB-A | $18.64 @1 (DigiKey, 506 in stock) | Built-in bootloader, Zephyr `bl654_usb` | Wrong connector, pricey |
| makerdiary nRF52840 MDK USB Dongle w/Case | 50.8 × 21.1 × 7.6 | USB-A | $19.90 @1 | UF2 bootloader, button DFU, SWD | **No FCC or CE found** — see below |
| Fanstel USB840F / USB840X | 52 × 21 × 21 | USB-A | $14.40 / $29.99 @1 | Bootloader + Tag-Connect SWD | Looks like a lab tool, not a product |
| Holyiot 17120-USB | 27.55 × 11.30 × **1.60** | not verified | not found | not verified | 1.6 mm = bare PCB, no enclosure |

**Rejected:** Nordic PCA10059 and April Brother (bare PCBs, exposed
castellations). Nordic's own DevZone states the PCA10059 is not CE certified
and that certification cannot be inherited — *"it's always the end product that
needs to be certified."*

**Don't chase these — they are not dongles:** nice!nano and Seeed XIAO nRF52840
are USB-C but carry a *receptacle*, not a male plug. They are boards you plug a
cable into, not things you plug into a laptop.

## Why the CX-40 wins

- Only USB-C finished dongle found anywhere
- Smallest enclosed unit in the list
- Cheapest
- Open bootloader, upstream Zephyr board support — firmware side is fully ours
- **Same MDBT50Q module family already in the knob design**, so the radio is a
  known quantity and the pairing work carries over
- Raytac markets itself as an ODM/OEM house and sells via DigiKey, Amazon, eBay,
  Tindie, Switch Science

DigiKey: MDBT50Q-CX-40, part 25271280.

## The catch, if we SELL rather than just use

**Every enclosed dongle on the market carries the FCC grant of the module
inside it, not a grant for the finished dongle.** Verified against the actual
filings: FCC ID SH6MDBT50Q is registered as a "Bluetooth Low Energy & IEEE
802.15.4 Combo Module" and its document list includes a Modular Approval Request
letter. Same for Fanstel's X8WBC840M. The plastic case is mechanical packaging,
not a regulatory boundary.

This is not fatal — it is the normal OEM path thousands of products follow — but
it means:

1. Our product exterior must be labeled **"Contains FCC ID: SH6MDBT50Q"**
   (FCC KDB 996369 D04, 47 CFR Part 2 labeling).
2. We must retain documentation showing the host complies.
3. The finished product still needs its own Part 15B authorization for its
   non-transmitter digital functions.
4. Under RED, a CE mark on a module does not transfer to a finished product
   either.

**The sharp edge: our own firmware.** Flashing a custom FIDO2 stack replaces the
entire firmware image, radio stack included. FCC §2.933 material notes a Change
in ID requires stating whether original test results remain representative, and
compliance consultancies list "firmware controlling transmission parameters"
among changes that may force a permissive change or fresh certification.
**Whether our firmware triggers a Class II permissive change is the question the
whole build-vs-buy decision turns on, and it needs a compliance consultant.**

If we want our own FCC ID on the label: Change in ID needs a signed Letter of
Authorization from Raytac naming the original FCC ID, the equipment and our
company. Type 1 leaves both grants valid (the normal OEM case). Consultancies
quote under two weeks. Subtlety: a Change in ID against SH6MDBT50Q gives us our
own ID for a *module*, not for the finished product.

**None of the above is legal advice. A compliance consultant must confirm items
3 and the firmware question before any commercial sale.**

## Unconfirmed — verify before ordering

1. **CX-40 price conflict:** $8.45 vs $9.50, both attributed to DigiKey; neither
   verified on-page. **No 100/1000 break published anywhere.** Get a direct
   quote from sales@raytac.com.
2. **USB840M pricing** — the $14.40→$10.67 ladder actually verified on-page
   belongs to USB840F, not USB840M.
3. **No vendor anywhere publishes OEM/white-label resale permission.** Raytac,
   Fanstel and Ezurio say nothing about rebranding or resale rights. Must be
   asked directly. makerdiary is the only one with a customization page:
   *"We are ready to customize our electronics and firmware"* — no mention of
   branding or resale.
4. **Is any enclosure openable / SWD reachable without destroying the case?**
   Not stated for CX-40, USB840M or makerdiary. Only USB840F/X document an SWD
   path.
5. **Protrusion from the port:** nobody publishes it. Raytac's 26.2 mm
   explicitly EXCLUDES the connector, so real protrusion is greater — this needs
   measuring on a sample before any housing work.
6. **makerdiary:** only Taiwan NCC CCAO19LP0660T0 found. No FCC, no CE, despite
   direct search. Treat as uncertified for US/EU.
7. **BL654 USB dimensions and FCC ID** — not found.
8. **CE/UKCA scope for all candidates** — every vendor claims "CE certified"
   with no notified-body number or DoC published.

## Recommended next step

Order **one** MDBT50Q-CX-40 from DigiKey. Confirm it enumerates, flash a Zephyr
hello-world over DFU, measure the actual protrusion with calipers, and confirm
the radio talks to the knob. That is a ~$10 experiment that de-risks the entire
dongle half of the project before a single PCB is designed.

## Canadian sourcing check — genuine Nordic PCA10059 (2026-09-01, live)

Wanted as a BENCH TOOL only (dev/test target); rejected above as the
shipping product.

| Seller | Price | Stock |
|---|---|---|
| [Mouser Canada](https://www.mouser.ca/ProductDetail/Nordic-Semiconductor/nRF52840-Dongle) | **CA$16.20** | 0 now — **1,200 arriving 2026-09-16**, backorder today and it ships in ~2–3 wk. **Best option.** |
| [DigiKey Canada](https://www.digikey.ca/en/products/detail/nordic-semiconductor-asa/NRF52840-DONGLE/9491124) | CA$17.22 | 0, backorder already past due, 16-week lead — skip |
| [RobotShop Canada — Seeed MDK dongle](https://ca.robotshop.com/products/seeedstudio-nrf52840-mdk-usb-dongle) | CA$19.53 | same chip, NOT the Nordic board (UF2 bootloader, different pinout) |
| Amazon.ca | CA$50+ | GeeekPi/Taidacent markups — skip |
