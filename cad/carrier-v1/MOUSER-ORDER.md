# Mouser Canada order -- flash fixture BOM

All prices CAD, qty-1, **verified on mouser.ca 2026-09-18**.
Shipping is a flat C$20 regardless of basket size, so everything small
that Mouser stocks is worth adding in one go.

## Verified lines

| # | Part | Mfr / MPN | Mouser # | Qty | Unit | Ext |
|---|------|-----------|----------|-----|------|-----|
| 1 | XIAO RP2040 (the debug probe) | Seeed 102010428 | 713-102010428 | 2 | 7.06 | 14.12 |
| 2 | J1 board header, 2-pin JST-XH 2.50 mm TH | JST B2B-XH-A(LF)(SN) | 306-B2BXHALFSNP | 5 | 0.144 | 0.72 |
| 3 | J1 cable housing, 2-pin | JST XHP-2 | 306-XHP-2 | 5 | 0.144 | 0.72 |
| 4 | J1 crimp contacts (2 per cable + spares) | JST SXH-001T-P0.6 | 306-SXH-001T-P0.6 | 10 | 0.187 | 1.87 |
| 5 | 4 mm banana plug, black (bench supply -) | Soldered 555061 | 392-101675 | 1 | 0.778 | 0.78 |
| 6 | 4 mm banana plug, red (bench supply +) | Soldered 555062 | 392-101676 | 1 | 0.778 | 0.78 |
| 7 | J2 SWD escape header, 1x5 2.54 mm male TH, gold | Wurth 61300511121 | 710-61300511121 | 5 | 0.374 | 1.87 |

Subtotal ~C$20.86 + C$20 shipping = **~C$40.86**

Quantities are set to 5 for the per-board parts because JLC is building 5
carrier PCBs and these are all under 20 cents -- a second order costs another
C$20 in postage.

## Links

- XIAO RP2040: https://www.mouser.ca/ProductDetail/713-102010428
- B2B-XH-A(LF)(SN): https://www.mouser.ca/en/ProductDetail/JST-Commercial/B2B-XH-ALFSN?qs=cdbOS8ANM9DdcSn9qRmfCw%3D%3D
- XHP-2: https://www.mouser.ca/en/ProductDetail/JST-Commercial/XHP-2?qs=QpmGXVUTftGT4osVcj8ZRw%3D%3D
- SXH-001T-P0.6: https://www.mouser.ca/en/ProductDetail/JST-Commercial/SXH-001T-P0.6?qs=QpmGXVUTftHVe8yFBLIwfA%3D%3D
- Banana black 555061: https://www.mouser.ca/en/ProductDetail/Soldered/555061
- Banana red 555062: https://www.mouser.ca/en/ProductDetail/Soldered/555062
- Wurth 61300511121: https://www.mouser.ca/en/ProductDetail/Wurth-Elektronik/61300511121?qs=PhR8RmCirEZCsCRHq%252BvfRQ%3D%3D

## Caveats / unconfirmed

- **Line 8 screws.** Mouser lists them as "M3 Thread, 8 mm (L), Panhead
  Phillips, Steel, Self Tap".  The *thread form* (sheet-metal type B vs a
  plastic thread-forming Plastite/BT profile) is NOT stated on the product
  page and I have not read the drawing, so treat it as unconfirmed against
  a datasheet.  A standard M3 sheet-metal self-tapper will still form a
  thread in MJF PA12 with our 2.4 mm pilot and 6.7 mm engagement.
  Only 12 packs in stock; a hardware store sells 4 screws for under a
  dollar, so this line is convenience, not necessity.
- **J2 is optional.**  It is the SWD escape.  Skip line 7 if you are not
  going to use it.

## Deliberately NOT bought from Mouser

- **M3 x 8 self-tapping screws x4** (they hold the carrier PCB down on the
  frame's four bosses, O2.4 mm pilot, 6.7 mm engagement).  Mouser's part is
  Io Audio IO-M3X8STP-100 at **C$10.67 for a pack of 100** (verified
  2026-09-18: description ends "Pack=100", minimum 1, qty-1 = C$10.67; the
  50-pack IO-M3X8STP-50 is C$4.06 but non-stocked, 16-week lead).  You need
  4.  Buy them loose at a hardware store for ~C$1: M3 x 8 self-tapping,
  pan head Phillips.

- **18 AWG bare copper for the two alignment dowels (2 x 19.5 mm).**
  Mouser's only match is Alpha Wire 296 SV005, a 100 ft spool at
  **C$198.36**.  Absurd for 40 mm of need.  Use instead:
  - K&S Precision Metals 1 mm brass rod (hobby shop, ~C$3) -- straightest
    and most accurate option, ground to size; or
  - a scrap of 18 AWG solid copper house/bell wire (1.024 mm nominal),
    insulation stripped; or
  - 0.039 in music wire.
  Target is 1.00-1.02 mm to suit the DUT's 1.20 mm NPTH holes.
- **Hookup wire for the bench-supply lead** (~1 m each of red and black,
  20-22 AWG stranded).  Mouser's smallest spools are C$100+.  Use whatever
  stranded wire you already have, or buy locally.
