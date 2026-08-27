"""
Raytac MDBT50Q-1MV2 land pattern — 61 pads, cross-validated from TWO sources.

  Source 1  Raytac approval sheet Ver. K, p.12, "Top View (mm) recommended
            solder pad layout". Read at 400 % from the vendor PDF.
  Source 2  JLCPCB / EasyEDA library part C5118826 ("MDBT50Q-1MV2",
            package COMM-SMD_MDBT50Q-1MV2-1), pulled as JSON, EasyEDA units
            converted at 1 unit = 10 mil = 0.254 mm.

Source 2 agreed with source 1 on ALL of: pad count (61), pad size
(0.6 x 0.4), every column x, every row y, and the 0.8 mm pitch. The two
frames differ by a constant (0.45, 0.60) offset only. That is the check
NEXT-SESSION rule 1 demands, and it is why these numbers are not invented.

DRAWING FRAME used below: origin at the module's bottom-left corner,
x right 0..10.5, y up 0..15.5, ANTENNA AT HIGH Y.

Run:  python mdbt50q_footprint.py
      validates, then writes MDBT50Q-1MV2.kicad_mod next to this file.
"""
import os
import sys

# ---------------------------------------------------------------- geometry --
BODY_W, BODY_H = 10.5, 15.5          # Ver. K §2.1: 15.5 x 10.5 x 2.05
PITCH = 0.8
PAD_LONG, PAD_SHORT = 0.6, 0.4       # Ver. K p.11 callout "61 pad_0.6x0.4"

# Column / row datums, drawing frame. Rings sit 0.6 and 1.5 from each edge.
X_LEFT_OUT, X_LEFT_IN = 0.6, 1.5
X_RIGHT_IN, X_RIGHT_OUT = 9.0, 9.9   # = 10.5 - 1.5, 10.5 - 0.6
Y_BOT_OUT, Y_BOT_IN = 0.6, 1.5
Y_MID = 7.2                          # the six centre pads

# side  = pad long axis runs in X (0.6 wide, 0.4 tall)
# stack = pad long axis runs in Y (0.4 wide, 0.6 tall)
SIDE, STACK = "side", "stack"

# pin: (x, y, orientation)   — drawing frame
PADS = {
    # ---- left edge, outer column x=0.6 ----
    1:  (X_LEFT_OUT, 11.5, SIDE),
    2:  (X_LEFT_OUT, 10.4, SIDE),
    3:  (X_LEFT_OUT,  9.6, SIDE),
    4:  (X_LEFT_OUT,  8.0, SIDE),
    6:  (X_LEFT_OUT,  7.2, SIDE),
    8:  (X_LEFT_OUT,  6.4, SIDE),
    10: (X_LEFT_OUT,  5.6, SIDE),
    12: (X_LEFT_OUT,  4.8, SIDE),
    14: (X_LEFT_OUT,  4.0, SIDE),
    # ---- left edge, inner column x=1.5 (staggered) ----
    5:  (X_LEFT_IN,   7.6, SIDE),
    7:  (X_LEFT_IN,   6.8, SIDE),
    9:  (X_LEFT_IN,   6.0, SIDE),
    11: (X_LEFT_IN,   5.2, SIDE),
    13: (X_LEFT_IN,   4.4, SIDE),
    # ---- bottom edge, outer row y=0.6 ----
    15: (0.45,  Y_BOT_OUT, STACK),
    16: (1.25,  Y_BOT_OUT, STACK),
    17: (2.05,  Y_BOT_OUT, STACK),
    18: (2.85,  Y_BOT_OUT, STACK),
    20: (3.65,  Y_BOT_OUT, STACK),
    22: (4.45,  Y_BOT_OUT, STACK),
    24: (5.25,  Y_BOT_OUT, STACK),
    26: (6.05,  Y_BOT_OUT, STACK),
    28: (6.85,  Y_BOT_OUT, STACK),
    30: (7.65,  Y_BOT_OUT, STACK),
    31: (8.45,  Y_BOT_OUT, STACK),
    32: (9.25,  Y_BOT_OUT, STACK),
    33: (10.05, Y_BOT_OUT, STACK),
    # ---- bottom edge, inner row y=1.5 (staggered) ----
    19: (3.25, Y_BOT_IN, STACK),
    21: (4.05, Y_BOT_IN, STACK),
    23: (4.85, Y_BOT_IN, STACK),
    25: (5.65, Y_BOT_IN, STACK),
    27: (6.45, Y_BOT_IN, STACK),
    29: (7.25, Y_BOT_IN, STACK),
    # ---- right edge, outer column x=9.9 ----
    34: (X_RIGHT_OUT,  1.6, SIDE),
    35: (X_RIGHT_OUT,  2.4, SIDE),
    37: (X_RIGHT_OUT,  3.2, SIDE),
    39: (X_RIGHT_OUT,  4.0, SIDE),
    41: (X_RIGHT_OUT,  4.8, SIDE),
    44: (X_RIGHT_OUT,  6.4, SIDE),
    46: (X_RIGHT_OUT,  7.2, SIDE),
    48: (X_RIGHT_OUT,  8.0, SIDE),
    51: (X_RIGHT_OUT,  9.6, SIDE),
    53: (X_RIGHT_OUT, 10.4, SIDE),
    55: (X_RIGHT_OUT, 11.5, SIDE),
    # ---- right edge, inner column x=9.0 (staggered) ----
    36: (X_RIGHT_IN,  2.8, SIDE),
    38: (X_RIGHT_IN,  3.6, SIDE),
    40: (X_RIGHT_IN,  4.4, SIDE),
    42: (X_RIGHT_IN,  5.2, SIDE),
    43: (X_RIGHT_IN,  6.0, SIDE),
    45: (X_RIGHT_IN,  6.8, SIDE),
    47: (X_RIGHT_IN,  7.6, SIDE),
    49: (X_RIGHT_IN,  8.4, SIDE),
    50: (X_RIGHT_IN,  9.2, SIDE),
    52: (X_RIGHT_IN, 10.0, SIDE),
    54: (X_RIGHT_IN, 10.8, SIDE),
    # ---- centre row y=7.2 ----
    56: (3.25, Y_MID, STACK),
    57: (4.05, Y_MID, STACK),
    58: (4.85, Y_MID, STACK),
    59: (5.65, Y_MID, STACK),
    60: (6.45, Y_MID, STACK),
    61: (7.25, Y_MID, STACK),
}

# ------------------------------------------------------------- keep-out -----
# Ver. K p.12, red dashed "No ground pad" — ALL LAYERS.
# Bottom edge sits exactly on the y=11.5 pad row; top edge on the module top.
# It overhangs the module by ~1.0 mm each side; Raytac does not dimension the
# overhang and §2.3 says "keep it as wide as you can", so 1.0 is a MINIMUM.
KEEPOUT_ALL = dict(x0=-1.0, x1=BODY_W + 1.0, y0=11.5, y1=BODY_H)

# Orange dashed "Toplayer no ground pad" — TOP LAYER ONLY. Dimensioned
# 2.95 from the module's left edge, 1.6 wide, 1.2 tall, hanging below y=11.5.
KEEPOUT_TOP = dict(x0=2.95, x1=2.95 + 1.6, y0=11.5 - 1.2, y1=11.5)

# ----------------------------------------------------------- validation -----
def validate():
    bad = []
    if len(PADS) != 61:
        bad.append(f"pad count is {len(PADS)}, Raytac says 61")
    if sorted(PADS) != list(range(1, 62)):
        missing = set(range(1, 62)) - set(PADS)
        bad.append(f"pin numbers not 1..61; missing {sorted(missing)}")

    ladder_x = {0.45, 0.6, 1.25, 1.5, 2.05, 2.85, 3.25, 3.65, 4.05, 4.45,
                4.85, 5.25, 5.65, 6.05, 6.45, 6.85, 7.25, 7.65, 8.45, 9.0,
                9.25, 9.9, 10.05}
    for n, (x, y, _) in PADS.items():
        if round(x, 2) not in ladder_x:
            bad.append(f"pin {n} x={x} is not on the drawing's x ladder")
        if not (0 <= x <= BODY_W and 0 <= y <= BODY_H):
            bad.append(f"pin {n} at ({x},{y}) is outside the {BODY_W}x{BODY_H} body")

    # the two rings must be symmetric about the body centreline
    if abs((BODY_W - X_LEFT_OUT) - X_RIGHT_OUT) > 1e-9:
        bad.append("outer columns are not symmetric")
    if abs((BODY_W - X_LEFT_IN) - X_RIGHT_IN) > 1e-9:
        bad.append("inner columns are not symmetric")

    # every row/column must be on a 0.8 grid within itself
    groups = {}
    for n, (x, y, o) in PADS.items():
        key = ("col", round(x, 2)) if o == SIDE else ("row", round(y, 2))
        groups.setdefault(key, []).append(round(y if o == SIDE else x, 2))
    for key, vals in groups.items():
        vals.sort()
        gaps = {round(b - a, 2) for a, b in zip(vals, vals[1:])}
        if not gaps <= {0.8, 1.6, 1.1, 2.4}:
            bad.append(f"{key} has off-grid spacing {sorted(gaps)}")
    return bad


# ------------------------------------------------------------- emitter ------
def to_local(x, y):
    """Drawing frame -> KiCad footprint local. Origin at body centre.
    Local +Y is the ANTENNA end, which the board frame maps to the spacebar
    edge (see ANTENNA-ORIENTATION.md). Place this footprint at rotation 0."""
    return round(x - BODY_W / 2.0, 4), round(y - BODY_H / 2.0, 4)


def emit():
    L = []
    a = L.append
    a('(footprint "MDBT50Q-1MV2"')
    a('\t(version 20240108)')
    a('\t(generator "mdbt50q_footprint.py")')
    a('\t(layer "F.Cu")')
    a('\t(descr "Raytac MDBT50Q-1MV2 nRF52840 BLE module, 15.5x10.5x2.05. '
      'Land pattern from Ver.K p.12, cross-checked against JLCPCB C5118826. '
      'Local +Y is the antenna end.")')
    a('\t(tags "raytac nrf52840 ble module")')
    a('\t(attr smd)')
    for n in sorted(PADS):
        x, y, o = PADS[n]
        lx, ly = to_local(x, y)
        sx, sy = (PAD_LONG, PAD_SHORT) if o == SIDE else (PAD_SHORT, PAD_LONG)
        a(f'\t(pad "{n}" smd rect')
        a(f'\t\t(at {lx} {ly})')
        a(f'\t\t(size {sx} {sy})')
        a('\t\t(layers "F.Cu" "F.Mask" "F.Paste")')
        a('\t)')
    # body outline on the courtyard + fab layers
    hw, hh = BODY_W / 2.0, BODY_H / 2.0
    for layer, w in (("F.CrtYd", 0.05), ("F.Fab", 0.1)):
        a(f'\t(fp_rect (start {-hw} {-hh}) (end {hw} {hh}) '
          f'(stroke (width {w}) (type solid)) (fill none) (layer "{layer}"))')
    a(')')
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    problems = validate()
    print("MDBT50Q-1MV2 land pattern")
    print(f"  pads defined      : {len(PADS)}")
    print(f"  body              : {BODY_W} x {BODY_H}")
    print(f"  pad sizes         : side {PAD_LONG}x{PAD_SHORT}, "
          f"stacked {PAD_SHORT}x{PAD_LONG}")
    print(f"  keep-out, ALL     : x {KEEPOUT_ALL['x0']}..{KEEPOUT_ALL['x1']}  "
          f"y {KEEPOUT_ALL['y0']}..{KEEPOUT_ALL['y1']}   "
          f"(depth {KEEPOUT_ALL['y1'] - KEEPOUT_ALL['y0']:.1f} from the antenna end)")
    print(f"  keep-out, TOP only: x {KEEPOUT_TOP['x0']}..{KEEPOUT_TOP['x1']}  "
          f"y {KEEPOUT_TOP['y0']}..{KEEPOUT_TOP['y1']}")
    if problems:
        print("\n  VALIDATION FAILED:")
        for p in problems:
            print("   -", p)
        sys.exit(1)
    print("  validation        : OK (61 pins 1..61, all on the drawing ladder,\n"
          "                      rings symmetric, rows/cols on the 0.8 grid)")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "MDBT50Q-1MV2.kicad_mod")
    with open(out, "wb") as f:
        f.write(emit().encode("utf-8"))
    print(f"  wrote {out}")
