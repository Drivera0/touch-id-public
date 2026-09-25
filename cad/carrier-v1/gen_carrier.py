"""
gen_carrier.py -- TouchID flashing CARRIER v1.  ONE board (no guide plate).

Emits carrier-v1.kicad_pcb (47 x 58 mm, 2 layer, 1.6 mm) + a preview PNG.

WHY ONE BOARD: the P75-E2 is 16.5 mm long and would have needed a second
"guide" plate to stop 14 mm of pin wobbling above the board.  Instead the pin
is mounted UPSIDE DOWN -- tube soldered into a O1.05 plated hole with only
~2 mm standing proud, the other ~14 mm hanging DOWN into the printed frame's
opening.  Tip accuracy comes from the hole it emerges from (a 2 mm
cantilever).  See CARRIER-DESIGN.md Addendum A.

COORDINATES: board-local, origin = centre of the DUT, IDENTICAL to the DUT's
own KiCad frame.  The DUT sits components-up / bottom-down, which is its
natural KiCad orientation, so there is NO mirroring.  KiCad is Y-down and we
never negate Y (memory: touchid-spacebar-edge-is-plus-y).  The board OUTLINE is
deliberately NOT centred on the DUT -- everything lives up and to the right of
it, so centring the outline would only add empty laminate.

DUT FACTS -- parsed from cad/v7-release/pcb-v7-zero-opens.kicad_pcb:
  outline   20.00 x 19.00 x 1.20
  J3        five O1.20 SMD pads on B.Cu, 2.00 pitch, y = +3.00,
            x = -8, -6, -4, -2, 0  =  SWDIO SWCLK RESET VSTOR GND
  MH        two O1.20 NPTH at (+-8.75, 0)

U1 FOOTPRINT -- CONFIRMED from Seeed's own "XIAO Series Package and PCB
Design", page 3 (XIAO RP2040, SKU 102010428).  Local copy in ../../datasheets/.
The callouts are vector outlines, not text; they were read off a 7x render.
  row spacing 17.0 c-c   pad 3.0 x 2.0 SMD   pitch 2.54, 7/side   body 17.8 x 21
  right row, USB end first: 5V GND 3V3 D10 D9 D8 D7
  D8 = P2 = GP2 = SWCLK,  D10 = P3 = GP3 = SWDIO,  D7 = P1 = GP1 = nRESET

XIAO UNDERSIDE: the module also carries exposed pads on its BELLY -- four
O1.5 round (its own SWD) 5.85 mm above centre, and two 1.3 x 2.3 rectangles
8.6 mm BELOW centre labelled GND and VIN.  VIN is the 5 V rail.  This carrier
deliberately puts NO copper under the module footprint except the 14 lands, so
none of those can touch anything.  5 V must never get near VSTOR.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "carrier-v1.kicad_pcb")

# ---------------- board outline (not centred on the DUT) ----------------
BX0, BX1, BY0, BY1 = -16.0, 31.0, -20.0, 38.0
TH = 1.6

# ---------------- DUT-derived, never edit by hand ----------------
J3      = [(-8.0, 3.0), (-6.0, 3.0), (-4.0, 3.0), (-2.0, 3.0), (0.0, 3.0)]
J3_NAME = ["SWDIO", "SWCLK", "RESET", "VSTOR", "GND"]
MH_DUT  = [(-8.75, 0.0), (8.75, 0.0)]
# the DUT body, 20.00 x 19.00 centred on the origin -- the same rectangle
# check_carrier.py uses for the no-F.Cu-under-the-board rule
DX0_, DX1_, DY0_, DY1_ = -10.0, 10.0, -9.5, 9.5
DUT_W, DUT_H = 20.0, 19.0

# Pads are OBLONG, stretched perpendicular to the 2.00 mm row, because these
# are the only joints made by hand and a round pad cannot be made big enough:
# O1.60 round on 2.00 pitch leaves a 0.275 mm annular ring, which is a very
# thin target for an iron.  Elongating in Y costs nothing (the pitch is in X)
# and gives 0.775 mm of ring where the iron actually goes.
POGO_DRILL             = 1.05            # P75-E2 tube is O1.02
POGO_PAD_X, POGO_PAD_Y = 1.60, 2.60
DOWEL_DRILL, DOWEL_PAD = 1.05, 2.40      # O1.0 dowel, isolated so it can be round

# ---------------- XIAO RP2040 ----------------
XIAO_ROWS, XIAO_PITCH, XIAO_N = 17.00, 2.54, 7
XIAO_CY = 23.5
XIAO_PAD_W, XIAO_PAD_H   = 3.00, 2.00
XIAO_BODY_W, XIAO_BODY_H = 17.8, 21.0
XIAO_LEFT  = ["D6", "D5", "D4", "D3", "D2", "D1", "D0"]     # low-Y first
XIAO_RIGHT = ["D7", "D8", "D9", "D10", "3V3", "GND", "5V"]  # low-Y first

# ---------------- lanes (2.54 grid so J2 lands straight on them) ---------
LANE_X = {"SWDIO_R": 16.00, "SWCLK_R": 18.54, "nRST_R": 21.08}
VSTOR_X, GND_X = 23.62, 26.16
LANE_Y = {"SWDIO_R": 11.0, "SWCLK_R": 9.0, "nRST_R": 7.0}
J2_Y   = 13.0
RES_X  = 13.0
BOT_Y  = -13.0                                   # J1 / test-point row

NETS = ["", "SWDIO", "SWCLK", "nRESET", "VSTOR", "GND",
        "SWDIO_R", "SWCLK_R", "nRST_R"]
NID  = {n: i for i, n in enumerate(NETS)}

parts = []          # (ref, x, y, rot, pads, hide_ref)

def th(num, dx, dy, drill, pad, net="", pad_y=None, shape="circle"):
    return (num, dx, dy, shape, pad, pad_y or pad, drill,
            ['"*.Cu"', '"*.Mask"'], net)

# Every reference designator is hidden.  Each part already carries a plain-
# language silk label ('3.6 V IN', 'V+', 'GND', 'SWD ESCAPE', the five pogo
# names), R1-R3 are the same 100R part so their designators carry no assembly
# information, and the auto-placed ref fields were the sole cause of all seven
# silk_overlap warnings.  JLC place parts from the CPL, not from silkscreen.
def add(ref, x, y, rot, pads, hide_ref=True):
    parts.append((ref, x, y, rot, pads, hide_ref))

# --- PP1..PP5 pogo pins ---------------------------------------------------
for i, ((x, y), nm) in enumerate(zip(J3, J3_NAME), 1):
    net = {"SWDIO": "SWDIO_R", "SWCLK": "SWCLK_R", "RESET": "nRST_R"}.get(nm, nm)
    add(f"PP{i}", x, y, 0, [th("1", 0, 0, POGO_DRILL, POGO_PAD_X, net,
                               pad_y=POGO_PAD_Y, shape="oval")], True)

# --- DW1/DW2 registration dowels (no net) --------------------------------
for i, (x, y) in enumerate(MH_DUT, 1):
    add(f"DW{i}", x, y, 0, [th("1", 0, 0, DOWEL_DRILL, DOWEL_PAD, "")], True)

# --- U1 XIAO RP2040, SMD land pattern ------------------------------------
def xiao_pad(num, x, y, net):
    return (num, x, y, "rect", XIAO_PAD_W, XIAO_PAD_H, None,
            ['"F.Cu"', '"F.Paste"', '"F.Mask"'], net)

NET_OF = {"D8": "SWCLK", "D10": "SWDIO", "D7": "nRESET", "GND": "GND"}
xp, y0 = [], XIAO_CY - (XIAO_N - 1) * XIAO_PITCH / 2.0
for i in range(XIAO_N):
    xp.append(xiao_pad(str(i + 1), -XIAO_ROWS / 2, y0 + i * XIAO_PITCH,
                       NET_OF.get(XIAO_LEFT[i], "")))
for i in range(XIAO_N):
    xp.append(xiao_pad(str(XIAO_N + i + 1), XIAO_ROWS / 2, y0 + i * XIAO_PITCH,
                       NET_OF.get(XIAO_RIGHT[i], "")))
add("U1", 0, 0, 0, xp)

def xiao_y(name):
    return y0 + XIAO_RIGHT.index(name) * XIAO_PITCH

# --- R1..R3, 0805 100R, each level with the pin it serves ----------------
# 100R limits clamp current if the 3.6 V target drives back into the XIAO's
# 3.3 V pins -- the same mitigation Raspberry Pi use on the Debug Probe.
def r0805(net_a, net_b):
    lay = ['"F.Cu"', '"F.Paste"', '"F.Mask"']
    return [("1", -0.95, 0, "roundrect", 1.20, 1.40, None, lay, net_a),
            ("2",  0.95, 0, "roundrect", 1.20, 1.40, None, lay, net_b)]
add("R1", RES_X, xiao_y("D10"), 0, r0805("SWDIO",  "SWDIO_R"))
add("R2", RES_X, xiao_y("D8"),  0, r0805("SWCLK",  "SWCLK_R"))
add("R3", RES_X, xiao_y("D7"),  0, r0805("nRESET", "nRST_R"))

# --- J1 power in (keyed JST-XH) + test points, one row along the bottom --
add("TP1", -7.0, BOT_Y, 0, [th("1", 0, 0, 1.00, 2.20, "VSTOR")])
add("J1",   0.0, BOT_Y, 0, [th("1", -1.25, 0, 1.00, 1.70, "VSTOR"),
                            th("2",  1.25, 0, 1.00, 1.70, "GND")])
add("TP2",  7.0, BOT_Y, 0, [th("1", 0, 0, 1.00, 2.20, "GND")])

# --- J2 probe escape: five pins sitting directly on the five lanes, in the
#     SAME ORDER as J3 itself -- SWDIO SWCLK RESET VSTOR GND ---------------
add("J2", 0.0, J2_Y, 0, [
    th("1", LANE_X["SWDIO_R"], 0, 1.02, 1.70, "SWDIO_R"),
    th("2", LANE_X["SWCLK_R"], 0, 1.02, 1.70, "SWCLK_R"),
    th("3", LANE_X["nRST_R"],  0, 1.02, 1.70, "nRST_R"),
    th("4", VSTOR_X,           0, 1.02, 1.70, "VSTOR"),
    th("5", GND_X,             0, 1.02, 1.70, "GND")])

MH = [(-12.0, -16.0), (27.0, -16.0), (-12.0, 34.0), (27.0, 34.0)]

# ---------------- routing ----------------
W = 0.5
def pad_xy(ref, num):
    for r, px, py, rot, pads, _h in parts:
        if r != ref: continue
        for (n, dx, dy, *_rest) in pads:
            if str(n) != str(num): continue
            if rot == 90: dx, dy = -dy, dx
            return (px + dx, py + dy)
    raise KeyError(f"{ref}.{num}")

T, V = [], []
def run(pts, net, layer="F.Cu", w=W):
    for i in range(len(pts) - 1):
        T.append((pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], layer, net, w))
def via(x, y, net):
    V.append((x, y, net)); return (x, y)

# RULE 1: no F.Cu inside the DUT rectangle except the PP*/DW* pads.  The DUT's
#   BOTTOM face carries exposed gold (J4, J11, TP1-TP10) and hovers ~1.5 mm
#   over this surface.
# RULE 2: no copper at all under the XIAO body except its own 14 lands -- the
#   module's belly carries exposed GND / VIN / SWD pads.
# Each signal: straight out of the module, through its resistor, down to B.Cu
# on its own vertical lane, then left on its own horizontal lane to its pin.
for ref, sig, pin_name, tgt in (("R1", "SWDIO_R", "D10", "PP1"),
                                ("R2", "SWCLK_R", "D8",  "PP2"),
                                ("R3", "nRST_R",  "D7",  "PP3")):
    drive = {"SWDIO_R": "SWDIO", "SWCLK_R": "SWCLK", "nRST_R": "nRESET"}[sig]
    run([(XIAO_ROWS / 2, xiao_y(pin_name)), pad_xy(ref, 1)], drive)
    v = via(LANE_X[sig], xiao_y(pin_name), sig)
    run([pad_xy(ref, 2), v], sig)
    run([v, (LANE_X[sig], LANE_Y[sig]), (pad_xy(tgt, 1)[0], LANE_Y[sig]),
         pad_xy(tgt, 1)], sig, "B.Cu")

# GND: out of the module, down its lane, along the bottom row
gy = xiao_y("GND")
run([(XIAO_ROWS / 2, gy), (GND_X, gy)], "GND")
vg = via(GND_X, gy, "GND")
run([vg, (GND_X, BOT_Y), pad_xy("J1", 2)], "GND", "B.Cu", 0.8)
run([(4.0, BOT_Y), (4.0, 3.0), pad_xy("PP5", 1)], "GND", "B.Cu", 0.8)
run([pad_xy("J1", 2), pad_xy("TP2", 1)], "GND", "B.Cu", 0.8)

# VSTOR: J1 up to PP4 on B.Cu; out to J2 on F.Cu around the bottom
run([pad_xy("J1", 1), (-2.0, BOT_Y), pad_xy("PP4", 1)], "VSTOR", "B.Cu", 0.8)
run([pad_xy("J1", 1), pad_xy("TP1", 1)], "VSTOR", "F.Cu", 0.8)
run([pad_xy("J1", 1), (-1.25, -17.0), (VSTOR_X, -17.0), (VSTOR_X, J2_Y)],
    "VSTOR", "F.Cu", 0.8)

# ---------------- silkscreen: (x, y, text, size, rot) ----------------
SILK = [
    (7.5,  36.8, "TouchID CARRIER v1", 1.3, 0),
    (7.5,  34.9, "XIAO RP2040 -- USB-C AT TOP", 0.8, 0),
    # Orientation.  The previous wording was '^ +Y  SPACEBAR EDGE' and the
    # caret was a trap: the board plots and displays Y-DOWN, so on the real
    # part +Y runs toward the XIAO, i.e. DOWNWARD in the top view, while the
    # caret points up.  Read one way it names the DUT edge just above it
    # (right); read the other it claims +Y is up (wrong).  A marker that can
    # be read backwards on a board where backwards puts SWDIO on the GND pin
    # is not a marker.  No glyph, and the DUT outline below does the pointing.
    (0.0,  10.6, "SPACEBAR EDGE OF YOUR BOARD LINES UP HERE", 0.65, 0),
    (0.0, -11.0, "board drops over DW1/DW2 -- components UP", 0.7, 0),
    # bottom power row.  V+/GND sit 1.9 mm above the title line so the two
    # never share a scanline -- at the old y they were 0.1 mm apart and KiCad
    # flagged both pairs.
    (-7.0, -15.4, "V+", 0.8, 0),
    (7.0,  -15.4, "GND", 0.8, 0),
    # J1 polarity, beside the pins rather than above them -- the row above is
    # already V+/GND for the test points and a second pair there would read as
    # labelling the same two holes twice.
    (-3.1, -13.0, "+", 0.8, 0),
    (3.1,  -13.0, "-", 0.8, 0),
    (0.0,  -17.3, "3.6 V IN  (KEYED)", 1.0, 0),
    (0.0,  -18.9, "METER THE TEST POINTS BEFORE THE BOARD GOES IN", 0.7, 0),
    # J2 probe escape.  The old single-line legend ran under the nRST_R via at
    # (21.08, 15.88) and got clipped by its mask opening; one small label per
    # pin, below the row, is both legal and easier to read.
    (21.08, 10.0, "SWD ESCAPE", 0.8, 0),
]
for _x, _nm in ((LANE_X["SWDIO_R"], "DIO"), (LANE_X["SWCLK_R"], "CLK"),
                (LANE_X["nRST_R"],  "RST"), (VSTOR_X, "V+"), (GND_X, "GND")):
    SILK.append((_x, 11.5, _nm, 0.55, 0))
# labels sit BELOW the dowel row -- at y = -2.0 they fouled DW1's pad once the
# dowel pads grew to O2.40 for hand soldering
for (x, _y), nm in zip(J3, J3_NAME):
    SILK.append((x, -3.4, nm, 0.55, 90))
for (x, _y), nm in zip(MH_DUT, ["DW1", "DW2"]):
    SILK.append((x, 5.6, nm, 0.55, 0))

# ---------------- silkscreen lines: (x1, y1, x2, y2) ----------------
# A drawn box where the DUT lands.  It is 0.3 mm outside the 20.00 x 19.00
# body on every side, so it stays clear of DW1/DW2's O2.40 pads (nearest
# approach 0.275 mm) and is still visible once the board is sitting in it.
OUT_M = 0.3
OX0, OX1 = DX0_ - OUT_M, DX1_ + OUT_M
OY0, OY1 = DY0_ - OUT_M, DY1_ + OUT_M
SILK_LINES = [(OX0, OY0, OX1, OY0), (OX1, OY0, OX1, OY1),
              (OX1, OY1, OX0, OY1), (OX0, OY1, OX0, OY0)]
SILK_LINE_W = 0.15

# ---------------- emit ----------------
def emit():
    L = []; a = L.append
    a("(kicad_pcb")
    a("\t(version 20240108)")
    a('\t(generator "gen_carrier.py")')
    a('\t(generator_version "8.0")')
    a("\t(general"); a(f"\t\t(thickness {TH})")
    a("\t\t(legacy_teardrops no)"); a("\t)")
    a('\t(paper "A4")')
    a("\t(layers")
    for num, nm, ty in [(0, "F.Cu", "signal"), (31, "B.Cu", "signal"),
                        (34, "B.Paste", "user"), (35, "F.Paste", "user"),
                        (36, "B.SilkS", "user"), (37, "F.SilkS", "user"),
                        (38, "B.Mask", "user"), (39, "F.Mask", "user"),
                        (44, "Edge.Cuts", "user"), (46, "B.CrtYd", "user"),
                        (47, "F.CrtYd", "user"), (49, "F.Fab", "user")]:
        a(f'\t\t({num} "{nm}" {ty})')
    a("\t)")
    a("\t(setup"); a(f"\t\t(aux_axis_origin {BX0} {BY1})")
    a("\t\t(pad_to_mask_clearance 0)"); a("\t)")
    for i, n in enumerate(NETS):
        a(f'\t(net {i} "{n}")')
    for (x1, y1, x2, y2) in [(BX0, BY0, BX1, BY0), (BX1, BY0, BX1, BY1),
                             (BX1, BY1, BX0, BY1), (BX0, BY1, BX0, BY0)]:
        a("\t(gr_line"); a(f"\t\t(start {x1} {y1})"); a(f"\t\t(end {x2} {y2})")
        a("\t\t(stroke (width 0.1) (type default))")
        a('\t\t(layer "Edge.Cuts")'); a("\t)")
    for (x1, y1, x2, y2) in SILK_LINES:
        a("\t(gr_line"); a(f"\t\t(start {x1} {y1})"); a(f"\t\t(end {x2} {y2})")
        a(f"\t\t(stroke (width {SILK_LINE_W}) (type default))")
        a('\t\t(layer "F.SilkS")'); a("\t)")
    for (x, y, txt, sz, rot) in SILK:
        a(f'\t(gr_text "{txt}"')
        a(f"\t\t(at {x} {y}{'' if rot == 0 else ' ' + str(rot)})")
        a('\t\t(layer "F.SilkS")')
        a(f"\t\t(effects (font (size {sz} {sz}) (thickness {round(sz*0.15,3)})))")
        a("\t)")
    for (ref, px, py, rot, pads, hide) in parts:
        a(f'\t(footprint "carrier:{ref}"')
        a('\t\t(layer "F.Cu")')
        a(f"\t\t(at {px} {py}{'' if rot == 0 else ' ' + str(rot)})")
        a(f'\t\t(property "Reference" "{ref}"')
        a("\t\t\t(at 0 -2.6 0)")
        a('\t\t\t(layer "F.SilkS")')
        if hide: a("\t\t\t(hide yes)")
        a("\t\t\t(effects (font (size 0.7 0.7) (thickness 0.12)))")
        a("\t\t)")
        a("\t\t(attr through_hole)")
        for (num, dx, dy, shape, w, h, drill, layers, net) in pads:
            a(f'\t\t(pad "{num}" {"thru_hole" if drill else "smd"} {shape}')
            a(f"\t\t\t(at {dx} {dy}{'' if rot == 0 else ' ' + str(rot)})")
            a(f"\t\t\t(size {w} {h})")
            if drill: a(f"\t\t\t(drill {drill})")
            a("\t\t\t(layers " + " ".join(layers) + ")")
            if shape == "roundrect": a("\t\t\t(roundrect_rratio 0.25)")
            if net: a(f'\t\t\t(net {NID[net]} "{net}")')
            a("\t\t)")
        a("\t)")
    for i, (x, y) in enumerate(MH, 1):
        a(f'\t(footprint "carrier:MH{i}"')
        a('\t\t(layer "F.Cu")'); a(f"\t\t(at {x} {y})")
        a(f'\t\t(property "Reference" "MH{i}" (at 0 0 0) (layer "F.SilkS")'
          ' (hide yes) (effects (font (size 0.6 0.6) (thickness 0.1))))')
        a("\t\t(attr through_hole)")
        a('\t\t(pad "" np_thru_hole circle'); a("\t\t\t(at 0 0)")
        a("\t\t\t(size 3.2 3.2)"); a("\t\t\t(drill 3.2)")
        a('\t\t\t(layers "F&B.Cu" "*.Mask")'); a("\t\t)"); a("\t)")
    for (x, y, net) in V:
        a("\t(via"); a(f"\t\t(at {x} {y})"); a("\t\t(size 0.8)")
        a("\t\t(drill 0.4)"); a('\t\t(layers "F.Cu" "B.Cu")')
        a(f"\t\t(net {NID[net]})"); a("\t)")
    for (x1, y1, x2, y2, layer, net, w) in T:
        a("\t(segment")
        a(f"\t\t(start {round(x1,4)} {round(y1,4)})")
        a(f"\t\t(end {round(x2,4)} {round(y2,4)})")
        a(f"\t\t(width {w})"); a(f'\t\t(layer "{layer}")')
        a(f"\t\t(net {NID[net]})"); a("\t)")
    a(")")
    return "\n".join(L) + "\n"

if __name__ == "__main__":
    open(OUT, "w").write(emit())
    print("wrote", OUT)
    print(f"carrier {BX1-BX0:.0f} x {BY1-BY0:.0f} x {TH} mm "
          f"({(BX1-BX0)*(BY1-BY0):.0f} mm2), 2 layer, {len(parts)} footprints, "
          f"{len(T)} segments, {len(V)} vias, {len(MH)} mounting holes")
