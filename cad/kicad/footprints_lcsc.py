# Land patterns pulled from JLCPCB / LCSC's own component library — the exact
# footprints JLCPCB associates with the part numbers on our BOM.
#
# PROVENANCE (2026-08-19). Do not hand-edit these numbers. If a value here is
# ever wrong, re-pull it from the source below rather than adjusting by eye.
#   U1  C2838502   https://easyeda.com/api/products/C2838502/components
#                  package "WIFIM-SMD_ESP32-C3-MINI-1", owner LCSC,
#                  JLCPCB Part Class: Extended Part, SMT: true
#   U2  C46459900  https://easyeda.com/api/products/C46459900/components
#                  package X2SON-4(1x1)
#
# Cross-checked against the manufacturer drawings:
#   U1  Espressif ESP32-C3-MINI-1 datasheet v2.2, Figure 11-1
#       -> 48 pads, 0.4 mm wide, 0.8 mm pitch, thermal grid 5.4 x 5.4,
#          4 x dia 0.7 vias.  LCSC matches on all four.
#   U2  TI DQN0004A package drawing 4215302/E, LAND PATTERN EXAMPLE
#       -> pads at (+-0.43, +-0.325); LCSC gives (+-0.421, +-0.325).
#          0.009 mm apart, which is EasyEDA's unit-grid rounding, not a
#          disagreement.
#
# EasyEDA PCB unit = 10 mil = 0.254 mm exactly. Origin of each footprint is
# EasyEDA (4000, 3000). EasyEDA Y increases downward.

EDA = 0.254           # mm per EasyEDA unit
OX, OY = 4000.0, 3000.0

def _mm(u):
    return round(u * EDA, 4)

def _rel(x, y):
    """EasyEDA absolute -> mm relative to the footprint origin, Y still down."""
    return _mm(x - OX), _mm(y - OY)

# =====================================================================
# U1 — ESP32-C3-MINI-1-N4  (C2838502)  package WIFIM-SMD_ESP32-C3-MINI-1
# =====================================================================
# 48 perimeter pads, each 0.800 mm (radial) x 0.400 mm (along the edge),
# on a 0.800 mm pitch (EasyEDA spacing 3.1496 u x 0.254 = 0.8000 mm).
U1_PITCH      = _mm(3.1496)      # 0.8000
U1_PAD_LONG   = _mm(3.1496)      # 0.8000  radial
U1_PAD_SHORT  = _mm(1.5748)      # 0.4000  along the edge

# Column / row centre lines (EasyEDA absolute)
_U1_LEFT_X    = 3976.7717
_U1_RIGHT_X   = 4023.2283
_U1_TOP_Y     = 2980.7087        # antenna end has no pads; this is the row
_U1_BOTTOM_Y  = 3019.2913        #   nearest the antenna keep-out

# pins 1-11   left column, top -> bottom
_U1_LEFT_YS   = [2984.252, 2987.402, 2990.551, 2993.701, 2996.85, 3000.0,
                 3003.15, 3006.299, 3009.449, 3012.598, 3015.748]
# pins 12-24  bottom row, left -> right
_U1_BOT_XS    = [3981.102, 3984.252, 3987.402, 3990.551, 3993.701, 3996.85,
                 4000.0, 4003.15, 4006.299, 4009.449, 4012.598, 4015.748,
                 4018.898]
# pins 25-35  right column, bottom -> top
_U1_RIGHT_YS  = [3015.748, 3012.598, 3009.449, 3006.299, 3003.15, 3000.0,
                 2996.85, 2993.701, 2990.551, 2987.402, 2984.252]
# pins 36-48  top row, right -> left
_U1_TOP_XS    = [4018.898, 4015.748, 4012.598, 4009.449, 4006.299, 4003.15,
                 4000.0, 3996.85, 3993.701, 3990.551, 3987.402, 3984.252,
                 3981.102]

def u1_perimeter_pads():
    """[(pin, x_mm, y_mm, w_mm, h_mm)] with Y still EasyEDA-down."""
    out, pin = [], 1
    for y in _U1_LEFT_YS:                      # 1-11  vertical edge
        x, yy = _rel(_U1_LEFT_X, y)
        out.append((pin, x, yy, U1_PAD_LONG, U1_PAD_SHORT)); pin += 1
    for x_ in _U1_BOT_XS:                      # 12-24 horizontal edge
        x, yy = _rel(x_, _U1_BOTTOM_Y)
        out.append((pin, x, yy, U1_PAD_SHORT, U1_PAD_LONG)); pin += 1
    for y in _U1_RIGHT_YS:                     # 25-35
        x, yy = _rel(_U1_RIGHT_X, y)
        out.append((pin, x, yy, U1_PAD_LONG, U1_PAD_SHORT)); pin += 1
    for x_ in _U1_TOP_XS:                      # 36-48
        x, yy = _rel(x_, _U1_TOP_Y)
        out.append((pin, x, yy, U1_PAD_SHORT, U1_PAD_LONG)); pin += 1
    assert pin == 49, pin
    return out

# pin 49 — thermal: 3 x 3 grid of 1.45 mm squares, 1.975 mm pitch,
# overall 5.400 mm square (agrees with Espressif's "5.4").
U1_TH_SIDE = _mm(5.7087)          # 1.4500
_U1_TH_XS  = [3992.2238, 4000.0, 4007.7752]
_U1_TH_YS  = [2992.2245, 3000.0, 3007.7759]

def u1_thermal_pads():
    return [_rel(x, y) for y in _U1_TH_YS for x in _U1_TH_XS]

# pins 50-53 — 0.70 mm corner anchor pads (Espressif's "4 x 0.7")
U1_CORNER_SIDE = _mm(2.7559)      # 0.7000
_U1_CORNERS = {50: (4023.4252, 2980.5118), 51: (4023.4252, 3019.4882),
               52: (3976.5748, 3019.4882), 53: (3976.5748, 2980.5118)}

def u1_corner_pads():
    return [(p, *_rel(x, y)) for p, (x, y) in sorted(_U1_CORNERS.items())]

# Module body / keep-out, from the same footprint's outline
U1_BODY_W   = _mm(4026.378 - 3973.622)      # 13.4000 (13.2 body + margin)
U1_BODY_H   = _mm(3022.441 - 2956.2992)     # 16.8000 (16.6 body + margin)
U1_BODY_DY  = _mm(2989.3701 - OY)           # -2.7000 body centre vs pad centre
U1_ANT_EDGE = _mm(2977.9528 - OY)           # -5.7000 antenna keep-out boundary

# Overall pad-ring extent (used for the clearance check)
U1_LAND_W = _mm(4024.8031 - 3975.1969)      # 12.6000
U1_LAND_H = _mm(3020.8661 - 2979.1339)      # 10.6000

# =====================================================================
# U2 — TPS7A2033DQNR  (C46459900)  package X2SON-4(1x1)
# =====================================================================
# 4 signal pads 0.360 mm (X) x 0.300 mm (Y); thermal is a 0.48 mm square
# rotated 45 degrees (a diamond) so its flats face the signal pads.
U2_PAD_W  = _mm(1.4173)           # 0.3600
U2_PAD_H  = _mm(1.1812)           # 0.3000
U2_OFF_X  = _mm((4005.315 - 4002.0) / 2)    # 0.4210
U2_OFF_Y  = _mm((3001.559 - 2999.0) / 2)    # 0.3249
U2_TH_SIDE = _mm(1.8898)          # 0.4800  square, rotated 45
U2_TH_ROT  = 45

# Pin 1 is the -X/-Y corner in EasyEDA (Y down) and carries the chamfer.
# TI SBVS338H Fig 4-3 top view: 1=OUT 2=GND 3=EN 4=IN 5=thermal(GND).
U2_PINS = {1: (-U2_OFF_X, -U2_OFF_Y),
           2: (-U2_OFF_X, +U2_OFF_Y),
           3: (+U2_OFF_X, +U2_OFF_Y),
           4: (+U2_OFF_X, -U2_OFF_Y)}

if __name__ == "__main__":
    p = u1_perimeter_pads()
    xs = [x for _, x, _, w, _ in p for x in (x - w / 2, x + w / 2)]
    ys = [y for _, _, y, _, h in p for y in (y - h / 2, y + h / 2)]
    print(f"U1 perimeter pads : {len(p)}  pitch {U1_PITCH}  "
          f"pad {U1_PAD_LONG} x {U1_PAD_SHORT}")
    print(f"U1 land extent    : {max(xs)-min(xs):.3f} x {max(ys)-min(ys):.3f} mm"
          f"   (expect {U1_LAND_W} x {U1_LAND_H})")
    print(f"U1 thermal        : 9 x {U1_TH_SIDE} sq, overall "
          f"{max(x for x,_ in u1_thermal_pads())*2 + U1_TH_SIDE:.3f}")
    print(f"U1 corners        : {len(u1_corner_pads())} x {U1_CORNER_SIDE} sq")
    print(f"U2 pads           : {U2_PAD_W} x {U2_PAD_H} at "
          f"(+-{U2_OFF_X}, +-{U2_OFF_Y}); thermal {U2_TH_SIDE} @ {U2_TH_ROT}")

# =====================================================================
# Passives — also pulled from LCSC rather than hand-written
# =====================================================================
#   C1,C2  C52923   1uF 25V X5R  package "C0402"
#   C3,C4  C16780   47uF 6.3V X5R package "C0805"
# Both are given here as (pad_along, pad_across, centre_offset) in mm, where
# "along" is the axis the two pads are separated on.
#
# 2026-08-19: the hand-written values they replace were
#   0402 -> 0.50 x 0.60 at +-0.48   (LCSC: 0.50 x 0.54 at +-0.42)
#   0805 -> 1.25 x 0.90 at +-1.00   (LCSC: 1.41 x 1.35 at +-1.00)
# The 0805 land was 0.51 mm short in the toe direction, which is most of the
# solder fillet. Using LCSC's larger land forces C3/C4 to be re-spaced.
C0402_ALONG,  C0402_ACROSS,  C0402_OFF  = _mm(1.9685), _mm(2.126), _mm(1.654)
C0805_ALONG,  C0805_ACROSS,  C0805_OFF  = _mm(5.5512), _mm(5.315), _mm(3.937)

C0402_REACH = C0402_OFF + C0402_ALONG / 2     # 0.690 half-length of the land
C0805_REACH = C0805_OFF + C0805_ALONG / 2     # 1.705
