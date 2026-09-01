"""
gen_flash_jig.py -- v2: compact pogo-pin flashing jig for pcb-v7, with a
push-button ejector. Three printed parts: jig + lever + plunger.
(The bulky all-in-one "flash station" is retired; wires now exit through
arches under the jig to the DAPLink and power source on the desk.)

Board facts (verified, pcb-v7-zero-opens):
  board          20.00 x 19.00 x 1.20 mm
  register holes NPTH O1.20 at (+-8.75, 0)
  J3 pads        (-8..0, +3.0), 2.0 mm pitch: SWDIO SWCLK RESET VSTOR GND

EJECT BUTTON -- a seesaw lever lies in the wiring cavity, its button poking
out the front (-Y) wall. Press DOWN ~2 mm: the long arm (2:1 advantage)
drives the O3 plunger up through the deck at (0, +6.5) -- the one spot on
the board's bottom SCANNED fully clear of pads/vias/tracks -- popping the
board ~4 mm off the posts. Five J3 spring pins plus one unwired helper pin
at (-5.25, +0.55) (scanned, 0.92 clear) keep the lift level. The lever's O3
axle stubs snap UP into downward-opening pivot slots (0.25 mm lip); the
plunger's O5 bottom flange rests on the lever's tip plate.

ORIENTATION -- engraved arrow on the +Y wall top points AWAY from the
button: THE BOARD'S SPACEBAR (ANTENNA / radio MODULE) EDGE POINTS AWAY FROM
THE EJECT BUTTON. Engraved dot on the west wall top marks the SWDIO end.
Wrong-way-round insertion puts 3.6 V on ground copper -- glance first.

WIRING (one-time, inside the cavity, never on a PCB): solder wires to the
five wired pin tails, route them out the bottom arches (west/east/rear) to
the DAPLink (SWDIO, SWCLK, GND) and the 3.6 V supply (VSTOR, GND). RESET
tail stays parked. The helper pin and plunger connect to nothing.

PINS: P75-E2 only (O1.02 barrel, O1.3 conical head, 16.5 mm). Drop each pin
in from the top; the head seats in its O1.45 recess. Solder wires to the
tails in the cavity below. Lee's P125-B does NOT fit (see bore comment).

Usage: python gen_flash_jig.py -> 3dmodels/flash_jig.stl + _lever + _plunger
"""
import os
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "3dmodels")
os.makedirs(OUT, exist_ok=True)

# ----- board facts (mm) -----
BW, BH, BT = 20.00, 19.00, 1.20
REG = [(-8.75, 0.0), (8.75, 0.0)]
J3 = [(-8.0, 3.0), (-6.0, 3.0), (-4.0, 3.0), (-2.0, 3.0), (0.0, 3.0)]
J3_NAMES = ["SWDIO", "SWCLK", "RESET", "VSTOR", "GND"]
LIFTER = (-5.25, 0.55)          # unwired helper spring pin (scanned clear)
PLUNGER_XY = (0.0, 6.5)         # ejector plunger (scanned fully clear)

# ----- jig parameters -----
CLR, POCKET_D = 0.15, 1.0
DECK_T, CAVITY_T = 13.0, 7.0   # roomier soldering cavity (user: size is free)
WALL = 6.0                     # thicker walls, longer lever guide slot
PIN_HOLE, POST_D, POST_UP = 1.15, 1.05, 2.6
PLUNGER_BORE = 3.5
PIVOT_Y = -8.5
LEVER_T = 3.0
LEVER_X0, LEVER_X1 = 1.5, 7.5   # lever lane, clear of the GND tail at (0,3)
AXLE_D = 3.0

L = BW + 2 * CLR + 2 * WALL     # 28.3
W = BH + 2 * CLR + 2 * WALL     # 27.3
H = DECK_T + CAVITY_T           # 19.0
FRONT = -W / 2                  # -13.65

base = cq.Workplane("XY").box(L, W, H, centered=(True, True, False))

# wiring cavity, open bottom (ABSOLUTE cut -- see station post-mortem: a
# faces("<Z") workplane is Y-mirrored and once hollowed the wrong region)
_cw, _ch = L - 8, W - 8   # 4 mm perimeter rim
base = base.cut(cq.Workplane("XY").workplane(offset=-1)
                .moveTo(-_cw / 2, -_ch / 2).lineTo(_cw / 2, -_ch / 2)
                .lineTo(_cw / 2, _ch / 2).lineTo(-_cw / 2, _ch / 2).close()
                .extrude(CAVITY_T + 1))

# board pocket + finger notch (front wall top, unchanged position)
base = (base.faces(">Z").workplane()
        .rect(BW + 2 * CLR, BH + 2 * CLR).cutBlind(-POCKET_D))
base = (base.faces(">Z").workplane()
        .pushPoints([(0, FRONT + WALL / 2)])
        .slot2D(12, 8, 0).cutBlind(-POCKET_D - 2))

# pin bores (5 wired + 1 helper), plunger bore, lever slot in the front wall
floor_z = H - POCKET_D
base = (base.faces(">Z").workplane(offset=-POCKET_D)
        .pushPoints(J3 + [LIFTER]).circle(PIN_HOLE / 2).cutThruAll())
# v2.1 SEATED PINS (user's idea): a O1.45 x 1.0 counterbore at each bore's
# top recesses and REGISTERS the P75-E2's O1.3 conical head, so every tip is
# centred on its pad instead of leaning in the loose barrel bore; the O1.15
# bore below is the small pass-through for barrel + wire tail. (Lee's P125-B
# was ruled out: O2.0 barrels on the 2.0 mm J3 pitch touch -> all signals
# short through the jig.)
base = (base.faces(">Z").workplane(offset=-POCKET_D)
        .pushPoints(J3 + [LIFTER]).circle(1.45 / 2).cutBlind(-1.0))
base = base.cut(cq.Workplane("XY", origin=(PLUNGER_XY[0], PLUNGER_XY[1], -1))
                .circle(PLUNGER_BORE / 2).extrude(H + 2))
base = base.cut(cq.Workplane("XY").workplane(offset=1.5)
                .moveTo(LEVER_X0 - 1.0, FRONT - 1).lineTo(LEVER_X1 + 1.0, FRONT - 1)
                .lineTo(LEVER_X1 + 1.0, FRONT + WALL + 1)
                .lineTo(LEVER_X0 - 1.0, FRONT + WALL + 1).close().extrude(6.5))

# WIRE ARCHES through the bottom rim: wires leave the cavity underneath and
# run along the desk. West + east arches sit at the J3 tail latitude; the
# rear arch is west of the plunger/lever gear.
for (ax0, ay0, ax1, ay1) in [
        (-L / 2 - 1, -1.0, -_cw / 2 + 1, 7.0),    # west wall, y 0..6
        (_cw / 2 - 1, -1.0, L / 2 + 1, 7.0),      # east wall
        (-9.0, _ch / 2 - 1, -1.0, W / 2 + 1)]:    # rear (+Y) wall, x -9..-1
    base = base.cut(cq.Workplane("XY").workplane(offset=-1)
                    .moveTo(ax0, ay0).lineTo(ax1, ay0)
                    .lineTo(ax1, ay1).lineTo(ax0, ay1).close()
                    .extrude(5.0))

# ---------------- fused additions ----------------
adds = []
# pivot bosses hanging from the cavity ceiling, snap slots opening downward
for bx in (LEVER_X0 - 2.5, LEVER_X1 + 2.5):
    boss = (cq.Workplane("XY", origin=(bx, PIVOT_Y, 1.6))
            .rect(3.0, 5.0).extrude(CAVITY_T - 1.6 + 1.0))
    slot = (cq.Workplane("YZ", origin=(bx - 1.6, PIVOT_Y, 3.5))
            .circle(AXLE_D / 2 + 0.2).extrude(3.2)
            .union(cq.Workplane("XY", origin=(bx, PIVOT_Y, 0))
                   .rect(3.4, AXLE_D - 0.5).extrude(3.5)))
    adds.append(boss.cut(slot).val())
for (px, py) in REG:
    adds.append(cq.Workplane("XY", origin=(px, py, floor_z - 1.0))
                .circle(POST_D / 2).extrude(POST_UP + 1.0)
                .faces(">Z").chamfer(0.3).val())
fused = base.val()
for a in adds:
    fused = fused.fuse(a)
base = cq.Workplane("XY").newObject([fused.clean()])

# engraved orientation marks (the embossed ridge/dot of v1 confused; engraved
# arrow on the +Y wall top points away from the eject button = spacebar edge)
base = base.cut(cq.Workplane("XY").workplane(offset=H - 0.5)
                .moveTo(-3.0, W / 2 - 3.4).lineTo(3.0, W / 2 - 3.4)
                .lineTo(0.0, W / 2 - 0.8).close().extrude(1.0))
base = base.cut(cq.Workplane("XY", origin=(-(L / 2 - WALL / 2), 3.0, H - 0.5))
                .circle(0.9).extrude(1.0))

# ---------------- lever + plunger (separate prints, lie flat) -------------
BTN_Y = -(W / 2) - 3.0   # button cap just outside the front face
lever = (cq.Workplane("XY").workplane(offset=1.5)
         .moveTo(LEVER_X0, BTN_Y - 1.5).lineTo(LEVER_X1, BTN_Y - 1.5)
         .lineTo(LEVER_X1, 5.0).lineTo(LEVER_X0, 5.0).close().extrude(LEVER_T))
lever = lever.union(cq.Workplane("XY").workplane(offset=1.5)      # tip plate
                    .moveTo(-2.0, 4.5).lineTo(LEVER_X1, 4.5)
                    .lineTo(LEVER_X1, 8.5).lineTo(-2.0, 8.5).close()
                    .extrude(LEVER_T))
lever = lever.union(cq.Workplane("XY").workplane(offset=1.5)      # button cap
                    .moveTo(LEVER_X0 - 1.5, BTN_Y - 1.5)
                    .lineTo(LEVER_X1 + 1.5, BTN_Y - 1.5)
                    .lineTo(LEVER_X1 + 1.5, BTN_Y + 3.0)
                    .lineTo(LEVER_X0 - 1.5, BTN_Y + 3.0).close()
                    .extrude(LEVER_T + 4.0))
for sx in (LEVER_X0 - 2.6, LEVER_X1):                              # axle stubs
    lever = lever.union(cq.Workplane("YZ", origin=(sx, PIVOT_Y, 3.0))
                        .circle(AXLE_D / 2).extrude(2.6))
lf = None
for s in lever.solids().vals():
    lf = s if lf is None else lf.fuse(s)
lever = cq.Workplane("XY").newObject([lf.clean()])

plunger = (cq.Workplane("XY").circle(5.0 / 2).extrude(1.5)
           .faces(">Z").workplane().circle(3.0 / 2).extrude(H - 7.3))   # idle top ~0.3 below pocket floor

cq.exporters.export(base, os.path.join(OUT, "flash_jig.stl"))
cq.exporters.export(base, os.path.join(OUT, "flash_jig.step"))
cq.exporters.export(lever, os.path.join(OUT, "flash_jig_lever.stl"))
cq.exporters.export(plunger, os.path.join(OUT, "flash_jig_plunger.stl"))
print("wrote flash_jig.stl/.step + _lever.stl + _plunger.stl")
print("jig %.1f x %.1f x %.1f mm; button at front; wires exit W/E/rear arches"
      % (L, W, H))
for (p, n) in zip(J3, J3_NAMES):
    print("   pin %-6s at (%5.1f, %4.1f)" % (n, p[0], p[1]))
