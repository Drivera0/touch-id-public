# Generates pcb-v2-corrected.kicad_pcb — complete board with placed hardware.
# Board frame = HOUSING frame (top view, components side); KiCad y = -housing y.
# F.Cu = component side (inside the cavity). B.Cu = pogo pad side (module bottom).
# Run: python build_board.py

import os
OUT = os.path.dirname(os.path.abspath(__file__))
OX, OY = 100, 100   # board origin on the sheet

NETS = {1: "VBAT", 2: "GND", 3: "+3V3", 4: "FP_TX", 5: "FP_RX", 6: "FP_INT",
        7: "USB_DP", 8: "USB_DN", 9: "BOOT_IO9"}

S = []  # collected s-expr fragments (inside the single footprint container)

def pad(name, x, y, w, h, layer, net=0, shape="roundrect", drill=None,
        ptype="smd", rot=0, mask=None):
    n = f' (net {net} "{NETS[net]}")' if net else ''
    d = f' (drill {drill})' if drill else ''
    layers = {'F': '"F.Cu" "F.Mask" "F.Paste"', 'B': '"B.Cu" "B.Mask"',
              '*': '"F.Cu" "B.Cu" "F.Mask" "B.Mask"'}[layer]
    extra = ' (roundrect_rratio 0.25)' if shape == "roundrect" else ''
    a = f'{x:.4f} {y:.4f}' + (f' {rot}' if rot else '')
    if mask is not None:
        extra += f' (solder_mask_margin {mask})'
    return (f' (pad "{name}" {ptype} {shape} (at {a}) '
            f'(size {w} {h}){d} (layers {layers}){extra}{n})')

def line(x1, y1, x2, y2, layer, wdt=0.12):
    return (f' (fp_line (start {x1:.2f} {y1:.2f}) (end {x2:.2f} {y2:.2f}) '
            f'(stroke (width {wdt}) (type solid)) (layer "{layer}"))')

def rect(cx, cy, w, h, layer, wdt=0.12):
    x1, y1, x2, y2 = cx-w/2, cy-h/2, cx+w/2, cy+h/2
    return [line(x1,y1,x2,y1,layer,wdt), line(x2,y1,x2,y2,layer,wdt),
            line(x2,y2,x1,y2,layer,wdt), line(x1,y2,x1,y1,layer,wdt)]

def text(s, x, y, layer, size=0.7):
    mir = " (justify mirror)" if layer.startswith("B.") else ""
    return (f' (fp_text user "{s}" (at {x:.2f} {y:.2f}) (layer "{layer}") '
            f'(effects (font (size {size} {size}) (thickness 0.12)){mir}))')

# ---------------- pogo pads (B.Cu, module bottom) ----------------
# pad-side (px,py) -> housing (-px,py) -> kicad (-px,-py)
# CALIPER-MEASURED 2026-08-19 on the knob module PCB:
#   pad dia 2.20, pitch 2.50 (spans F=4.70 G=7.22 K=4.70 all agree),
#   J4: pad edge 0.48 from top edge, 1.50 from side edge
#   J11: 0.50 from top edge; L/N disagreed by 0.3 -> J11 x split the
#   difference and pads are OVAL 2.5x2.2 to absorb the uncertainty.
#   Board 19.6 x 17.6 (centered frame: x +-9.8, y +-8.8).
# NOTE: J11 pads were briefly 2.5 mm oval to absorb the L/N measurement
# disagreement, but 2.5 wide on a 2.5 pitch leaves ZERO gap -> DRC short.
# Reverted to 2.2 circles (0.3 gap): a pogo pin tip is ~0.9 mm, so a 2.2 pad
# still tolerates the ~0.3 mm position uncertainty.
pogo = [("J4-2",4.70,7.22,0,2.2),("J4-1",7.20,7.22,0,2.2),
        ("J4-4",4.70,4.72,0,2.2),("J4-3",7.20,4.72,0,2.2),
        ("J4-6",4.70,2.22,0,2.2),("J4-5",7.20,2.22,2,2.2),
        ("J11-2",-5.95,7.20,1,2.2),("J11-1",-3.45,7.20,1,2.2),
        ("J11-4",-5.95,4.70,0,2.2),("J11-3",-3.45,4.70,1,2.2)]
for name, px, py, net, w in pogo:
    shp = "circle" if w == 2.2 else "oval"
    S.append(pad(name, -px, -py, w, 2.2, 'B', net, shape=shp))
    # silk labels OUTBOARD of outer columns, INBOARD of inner columns
    # (no room above the top rows: pads are only 0.48 from the board edge)
    dx = -(w/2 + 0.75) if abs(px) > 5 else (w/2 + 0.75)   # kicad x = -px
    if px < 0: dx = -dx
    S.append(text(name, -px + dx, -py, "B.SilkS", 0.5))

# ---------------- mounting holes ----------------
S.append(pad("", 8.3, 0, 2.2, 2.2, '*', 0, "circle", 2.2, "np_thru_hole"))
S.append(pad("", -8.3, 0, 2.2, 2.2, '*', 0, "circle", 2.2, "np_thru_hole"))
# NO alignment post holes (posts removed per drawing sign-off)

import footprints_lcsc as FP

# ---------------- U1: ESP32-C3-MINI-1-N4 (LCSC C2838502) ----------------
# Land pattern taken verbatim from JLCPCB/LCSC's own component library —
# package "WIFIM-SMD_ESP32-C3-MINI-1". See footprints_lcsc.py for the pull
# and for the cross-check against Espressif datasheet v2.2 Figure 11-1.
#
# 2026-08-19: this REPLACES a hand-invented "SIMPLIFIED" pattern of 14 pads on
# a 1.0 mm pitch. The real part has 48 pads on a 0.8 mm pitch, so essentially
# nothing landed. Never author a module footprint by hand again.
#
# Geometry: 48 perimeter pads 0.80 (radial) x 0.40 (along edge), 0.80 pitch;
# pin 49 = 3x3 grid of 1.45 squares (5.40 overall); pins 50-53 = 0.70 corner
# anchors. Overall land 12.60 x 10.60.
#
# Placement: module BODY centred on the board, so the pad ring sits +2.70 in
# kicad y and the antenna half stays at -y against the top wall, unchanged.
U1_PAD_CY = -FP.U1_BODY_DY          # +2.700

# pin -> net.  Pin functions from the same LCSC part record (symbol pins).
# 3=3V3  8=EN  6=IO3  23=IO9  26=IO18  27=IO19  30=RXD0  31=TXD0
# GND: 1, 2, 11, 14 and the whole 36..53 block (incl. thermal + corners).
U1_NET = {3: 3, 8: 3, 6: 6, 23: 9, 26: 8, 27: 7, 30: 4, 31: 5,
          5: 3, 22: 3}   # 5=IO2, 22=IO8: strapping, tied high
for _p in (1, 2, 11, 14):
    U1_NET[_p] = 2
for _p in range(36, 54):
    U1_NET[_p] = 2
U1_LABEL = {3: "3V3", 8: "EN", 6: "INT", 23: "IO9", 26: "USB_DN",
            27: "USB_DP", 30: "RXD", 31: "TXD", 5: "IO2*", 22: "IO8*"}
# * IO2 and IO8 are strapping pins held at +3V3. Espressif Table 4-1 lists
#   both as Floating by default (no internal pull); Table 4-3 requires
#   GPIO2=1 for both boot modes and GPIO8=1 for Joint Download Boot.
#   FIRMWARE CONSTRAINT: never configure GPIO2 or GPIO8 as outputs --
#   driving them low would short +3V3 through the pin driver.

for _pin, _x, _y, _w, _h in FP.u1_perimeter_pads():
    S.append(pad(f"U1-{_pin}", _x, U1_PAD_CY + _y, _w, _h, 'F',
                 U1_NET.get(_pin, 0), shape="rect"))
for _i, (_x, _y) in enumerate(FP.u1_thermal_pads(), 1):
    S.append(pad(f"U1-49_{_i}", _x, U1_PAD_CY + _y, FP.U1_TH_SIDE,
                 FP.U1_TH_SIDE, 'F', 2, shape="rect"))
for _pin, _x, _y in FP.u1_corner_pads():
    S.append(pad(f"U1-{_pin}", _x, U1_PAD_CY + _y, FP.U1_CORNER_SIDE,
                 FP.U1_CORNER_SIDE, 'F', 2, shape="rect"))

# body + antenna keep-out, both from the LCSC outline rather than guessed
S += rect(0, 0, FP.U1_BODY_W, FP.U1_BODY_H, "F.Fab")
_ant_y = U1_PAD_CY + FP.U1_ANT_EDGE                 # -3.000
_ant_top = -FP.U1_BODY_H / 2
S += rect(0, (_ant_y + _ant_top) / 2, FP.U1_BODY_W - 0.2, _ant_y - _ant_top,
          "F.Fab")
S.append(text("U1 ESP32-C3-MINI-1-N4", 0, U1_PAD_CY, "F.Fab", 0.8))
S.append(text("ANT", 0, (_ant_y + _ant_top) / 2, "F.SilkS", 0.8))

# =====================================================================
# ALL COMPONENTS ON TOP (same side as the ESP32) — user requirement.
# The only space beside the module is the two 1.6 mm side strips, so the
# LDO and caps use MICRO packages (X2SON-4, 0402, 0805). Too small to
# hand-solder -> order the board with JLCPCB SMT assembly.
# Strips: |x| = 6.9..8.3, avoiding the screw holes (|y| < 2.0 blocked).
# U1 is rotated 180 (antenna at +y), so its pads live at y -7.65..2.25.
# =====================================================================
# U2: TPS7A2033DQNR 3.3V LDO, X2SON-4 / DQN (1.0 x 1.0) — left strip
#     LCSC C46459900. Replaced TPS7A0233 (TPS7A02) on 2026-08-19 because that
#     part was marginal twice over for this rail:
#       VBAT is raw Li-ion (3.466 V on battery .. ~4.2 V charging, measured
#       3.680 V wired / 3.466 V wireless in the pin test).
#       - dropout: TPS7A02 = 270 mV @ 200 mA, but headroom at 3.466 V in /
#         3.3 V out is only 166 mV -> it would fall out of regulation.
#         TPS7A20 = 140 mV @ 300 mA, which fits inside 166 mV.
#       - current: ESP32-C3-MINI-1 peaks at 350 mA. 200 mA left a 150 mA
#         deficit for the bulk caps to cover; 300 mA leaves only 50 mA
#         (~0.21 V droop over a 400 us BLE TX burst on 94 uF, so the rail
#         stays above the C3's 3.0 V minimum).
#     Same DQN package and SAME PINOUT as TPS7A02, so the land pattern below
#     serves either part.
ux, uy = -7.6, -3.0
S += rect(ux, uy, 1.0, 1.0, "F.Fab")
S.append(text("U2 TPS7A20", ux+1.9, uy, "F.Fab", 0.45))
# PINOUT — TI SBVS338H (TPS7A20) Figure 4-3 / SBVS277C (TPS7A02) Figure 5-1,
# DQN 4-pin X2SON, TOP VIEW:  pin1 = OUT, pin2 = GND, pin3 = EN, pin4 = IN,
# pin5 = thermal pad (internally tied to GND, TI: "connect to ground plane").
# NOTE: this is NOT the DBV/SOT-23-5 order (where pin 1 = IN). The original
# code used the DBV order, which put VBAT on OUT and +3V3 on IN -- i.e. the
# regulator wired backwards. Fixed 2026-08-19.
# Land pattern: taken from JLCPCB/LCSC's own library for C46459900 (see
# footprints_lcsc.py) and cross-checked against TI package drawing 4215302/E.
# 2026-08-19: REPLACES a derived pattern (0.30 sq pads at +-0.52/+-0.52) that
# put only ~20-25% of each terminal over copper. The thermal land is a square
# rotated 45 deg so its flats face the signal pads -- that orientation is not
# optional, it is what creates the 0.22 mm exposed-metal clearance.
# TI 4215302/E marks this land SOLDER MASK DEFINED with a 0.05 mm web all
# around. Copper-to-copper is only 0.054 mm here (unavoidable on a 1x1 X2SON,
# and identical in TI's own drawing); pulling the mask in by 0.05 per side
# gives a 0.154 mm mask dam between the thermal pad and the signal pads, which
# is what actually prevents a solder bridge.
U2_MASK = -0.05

for _pin, (_dx, _dy) in sorted(FP.U2_PINS.items()):
    S.append(pad(f"U2-{_pin}", ux + _dx, uy + _dy, FP.U2_PAD_W, FP.U2_PAD_H,
                 'F', {1: 3, 2: 2, 3: 1, 4: 1}[_pin], shape="rect",
                 mask=U2_MASK))
S.append(pad("U2-5", ux, uy, FP.U2_TH_SIDE, FP.U2_TH_SIDE, 'F', 2,
             shape="rect", rot=FP.U2_TH_ROT, mask=U2_MASK))
# C1/C2: 100nF+1uF 0402, left strip below U2
def cap402(name, cx, cy, na, nb):
    # LCSC C52923 package "C0402": pads 0.500 (along) x 0.540 (across) at
    # +-0.420. Rotated 90 here, so the offset runs in y and the sizes swap.
    _a, _c, _o = FP.C0402_ALONG, FP.C0402_ACROSS, FP.C0402_OFF
    return [pad(f"{name}-1", cx, cy-_o, _c, _a, 'F', na, shape="rect"),
            pad(f"{name}-2", cx, cy+_o, _c, _a, 'F', nb, shape="rect"),
            text(name, cx+1.3, cy, "F.Fab", 0.4)]
# moved down 0.4/0.5 mm on 2026-08-19: the new DQN land pattern is wider than
# the old 4-pad guess, and C1 ended up 0.07 mm from U2-1 (min is 0.127).
# NOTE net swap too: C1 sits on the OUT side (pin 1) and C2 feeds IN.
S += cap402("C1", -7.6, -4.8, 3, 2)     # LDO OUT decoupling (+3V3)
S += cap402("C2", -7.6, -6.7, 1, 2)     # LDO IN  decoupling (VBAT)
# C3a/C3b: 2x 47uF 0805 bulk (VBAT), right strip
def cap805(name, cx, cy, na, nb):
    # LCSC C16780 package "C0805": pads 1.410 (along) x 1.350 (across) at
    # +-1.000 -> a 3.410 mm long land. The hand-written pads this replaces were
    # only 0.90 long, i.e. 0.51 mm short in the toe direction.
    _a, _c, _o = FP.C0805_ALONG, FP.C0805_ACROSS, FP.C0805_OFF
    return [pad(f"{name}-1", cx, cy-_o, _c, _a, 'F', na, shape="rect"),
            pad(f"{name}-2", cx, cy+_o, _c, _a, 'F', nb, shape="rect"),
            text(name, cx-1.6, cy, "F.Fab", 0.45)]
S += cap805("C3", 7.6, -3.10, 1, 2)   # top pad 0.295 clear of the screw hole
S += cap805("C4", 7.6, -6.71, 1, 2)   # 0.200 to C3, 0.385 to the board edge
# J2: sensor wire pads (TOP, normal size) in the strips above the screws,
# outside the antenna's width so the keep-out stays clean
j2L = [("1","3V3",3),("2","GND",2),("3","TX",4)]
j2R = [("4","RX",5),("5","INT",6),("6","VT",3)]
# 2026-08-19: the signal names are now also on F.SilkS so they are actually
# PRINTED on the board -- previously they lived only on F.Fab (a documentation
# layer), which left the six sensor pads completely unmarked on real hardware.
# They go OUTBOARD of the pads: pad edge is at |x| = 8.2, board edge at 9.8,
# so a 0.4 mm text centred at |x| = 8.9 clears the soldermask opening by
# ~0.2 mm and the board edge by ~0.4 mm. (They cannot sit inboard at |x| = 6.1
# -- that is on top of the ESP32's pads and the fab would clip them.)
SILK_X = 8.9
for (pn,label,net), y in zip(j2L, [2.9,4.4,5.9]):
    S.append(pad(f"J2-{pn}", -7.6, y, 1.2, 1.2, 'F', net, "circle"))   # 1.2 not 1.4: 1.5 pitch needs >=0.127 gap
    S.append(text(label, -6.1, y, "F.Fab", 0.4))
    S.append(text(label, -SILK_X, y, "F.SilkS", 0.4))
for (pn,label,net), y in zip(j2R, [2.9,4.4,5.9]):
    S.append(pad(f"J2-{pn}", 7.6, y, 1.2, 1.2, 'F', net, "circle"))   # 1.2 not 1.4: 1.5 pitch needs >=0.127 gap
    S.append(text(label, 6.1, y, "F.Fab", 0.4))
    S.append(text(label, SILK_X, y, "F.SilkS", 0.4))
S.append(text("J2 sensor wires", -7.4, 7.3, "F.Fab", 0.45))
# (no "J2" header on silk: at (0,7.6) it would sit under the ESP32 module body
#  (±6.6 x ±8.3) and be invisible. Each pad carries its own signal name instead.)
# programming pads: BOTTOM side, FLAT COPPER ONLY (no components under the
# board) — zero height, allowed
for name, x, net in [("TP-DP",-2.0,7),("TP-DN",0.0,8),("TP-IO9",2.0,9)]:
    S.append(pad(name, x, 1.3, 1.8, 1.8, 'B', net, "circle"))
    S.append(text(name.replace("TP-",""), x, 2.7, "B.SilkS", 0.5))
S.append(text("driver0", 0, 4.2, "B.SilkS", 0.9))
S.append(text("fingerprint module v1  2026", 0, 5.6, "B.SilkS", 0.6))

# ---------------- board outline (Edge.Cuts): 19.6 x 17.6, R2 corners ------
# CALIPER-MEASURED 2026-08-19: A=19.60 wide, B=17.60 tall (NOT square).
# Pad-side edge (kicad -y) is 8.8 from center; pads sit 0.48 from it.
bx, by, r = 19.6/2, 17.6/2, 2.0
oc = []
oc.append(line(-bx+r,-by, bx-r,-by, "Edge.Cuts"))
oc.append(line( bx, -by+r, bx, by-r, "Edge.Cuts"))
oc.append(line( bx-r, by, -bx+r, by, "Edge.Cuts"))
oc.append(line(-bx, by-r, -bx, -by+r, "Edge.Cuts"))
for (cx,cy,a1) in [(bx-r,-by+r,0),(bx-r,by-r,90),(-bx+r,by-r,180),(-bx+r,-by+r,270)]:
    # 90-deg arcs via kicad fp_arc: start/mid/end
    import math
    sa = math.radians(a1-90); ma = math.radians(a1-45); ea = math.radians(a1)
    def pt(ang): return (cx + r*math.cos(ang), cy + r*math.sin(ang))
    (x1,y1),(xm,ym),(x2,y2) = pt(sa), pt(ma), pt(ea)
    oc.append(f' (fp_arc (start {x1:.3f} {y1:.3f}) (mid {xm:.3f} {ym:.3f}) (end {x2:.3f} {y2:.3f}) (stroke (width 0.12) (type solid)) (layer "Edge.Cuts"))')
S += oc

# ---------------- 3D model references (resolved from the local KiCad install)
# NOTE: uses the KiCad 9 path variable; for KiCad 8 replace KICAD9_ with KICAD8_.
# The ESP32-S2-MINI-1 model is a visual stand-in for the C3-MINI-1 (same can,
# size and antenna zone) — swap when Espressif's C3 footprint is imported.
def model(path, x, y, rz, bottom=False):
    out = []
    rx = 180 if bottom else 0
    z = -1.2 if bottom else 0
    for VAR in ("${KICAD8_3DMODEL_DIR}", "${KICAD9_3DMODEL_DIR}", "${KICAD10_3DMODEL_DIR}"):
        out.append(f'  (model "{VAR}/{path}"\n'
                   f'    (offset (xyz {x} {-y} {z}))\n'
                   f'    (scale (xyz 1 1 1))\n'
                   f'    (rotate (xyz {rx} 0 {rz})))')
    return "\n".join(out)
S.append(model("Capacitor_SMD.3dshapes/C_0402_1005Metric.step", -7.6, -4.4, 90))
S.append(model("Capacitor_SMD.3dshapes/C_0402_1005Metric.step", -7.6, -6.2, 90))
S.append(model("Capacitor_SMD.3dshapes/C_0805_2012Metric.step", 7.6, -3.6, 90))
S.append(model("Capacitor_SMD.3dshapes/C_0805_2012Metric.step", 7.6, -7.1, 90))

# ---------------- assemble file ----------------
layers = '''  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )'''
nets = '\n'.join(f'  (net {i} "{n}")' for i, n in NETS.items())
fp = ('(footprint "touchid:touchid_board" (layer "F.Cu")\n  (at %d %d)\n'
      '  (descr "TouchID module board: F.Cu=components (cavity side), B.Cu=pogo pads (module bottom). Nets: VBAT from J11-1/2/3, GND J4-5, 3V3 via U2 LDO. Ratsnest shows required connections - routing TBD.")\n'
      '  (property "Reference" "PCB1" (at 0 -12) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))\n'
      '  (property "Value" "touchid_v1" (at 0 12) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))\n'
      % (OX, OY) + '\n'.join(S) + '\n)')
pcb = (f'(kicad_pcb (version 20221018) (generator pcbnew)\n'
       f'  (general (thickness 1.2))\n  (paper "A4")\n{layers}\n'
       f'  (setup (pad_to_mask_clearance 0))\n'
       f'  (net 0 "")\n{nets}\n{fp}\n)\n')
open(os.path.join(OUT, "pcb-v2-corrected.kicad_pcb"), "w").write(pcb)
print("wrote pcb-v2-corrected.kicad_pcb")
