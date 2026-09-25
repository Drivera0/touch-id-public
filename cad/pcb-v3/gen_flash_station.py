"""
gen_flash_station.py -- self-contained USB-C flashing station for pcb-v7.

Supersedes the bare jig (gen_flash_jig.py, kept) by adding a rear equipment
tray so EVERYTHING lives in one printed block: the MuseLab Mini DAPLink-HS
(USB-C version) and a USB-C adjustable buck module set to 3.6 V. Workflow:
plug two USB-C cables into the rear wall, drop the board in, press, flash,
release -- the springs eject the board themselves.

Board facts (verified, pcb-v7-zero-opens):
  board          20.00 x 19.00 x 1.20 mm
  register holes NPTH O1.20 at (+-8.75, 0)
  J3 pads        (-8..0, +3.0), 2.0 mm pitch: SWDIO SWCLK RESET VSTOR GND

EJECTION -- a real BUTTON now (3 printed parts). A seesaw lever lies in the
wiring cavity: its button pokes out the front wall; press DOWN ~2 mm and the
long arm (2:1 advantage) drives a O3 plunger up through the deck at
(0, +6.5) -- the one spot on the board's bottom scanned fully clear of
copper -- popping the board ~4 mm off the posts. The five J3 springs plus
one unwired helper pin at (-5.25, +0.55) (also scanned, 0.92 clear) keep it
level. Lever axle snaps up into downward-opening pivot slots; the plunger's
bottom flange rests on the lever tip plate.

ORIENTATION -- the old ridge/dot marks confused their one user and are gone.
Instead an engraved arrow on the deck points at the cable wall, and the rule
is physical: THE BOARD'S SPACEBAR (ANTENNA/MODULE) EDGE POINTS AT THE CABLES.
An engraved dot on the deck still marks the SWDIO end of the pin row.

TRAY -- one open bay, inner 62 x 36 x 14, swallowing both modules side by
side whatever their exact size (MuseLab publish no dimensions; the common
LCD buck-boost is ~52 x 28). Two 14 x 8 cable slots in the rear wall, four
zip-tie slots in the tray floor, and a wire tunnel into the pin cavity.
Fix the modules with zip ties or a foam shim; set the buck to 3.60 V with a
meter BEFORE its output is ever wired to the VSTOR pin tail.

WIRING (one-time, inside the station, never on a PCB):
  DAPLink SWDIO/SWCLK/GND -> the SWDIO/SWCLK/GND pin tails
  buck OUT+ -> VSTOR tail, buck OUT- -> GND tail (shared with DAPLink GND)
  RESET tail: leave unconnected (park it taped in the cavity)

Usage: python gen_flash_station.py  -> 3dmodels/flash_station.stl / .step
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
LIFTERS = [(-5.25, 0.55)]                   # one unwired helper spring pin
PLUNGER_XY = (0.0, 6.5)                     # ejector plunger, board's clearest
                                            # bottom spot (scanned vs B.Cu)
PLUNGER_BORE = 3.5                          # for the O3.0 printed plunger
PIVOT_Y = -8.5                              # lever axle line, inside cavity
LEVER_W, LEVER_T = 6.0, 3.0                 # bar width (x), thickness (z)
LEVER_X0, LEVER_X1 = 1.5, 7.5               # bar span, clear of the GND tail
AXLE_D = 3.0

# ----- core (same numbers as the proven jig) -----
CLR, POCKET_D = 0.15, 1.0
DECK_T, CAVITY_T = 13.0, 6.0
WALL = 4.0
PIN_HOLE, POST_D, POST_UP = 1.15, 1.05, 2.6

CORE_L = BW + 2 * CLR + 2 * WALL            # 28.3 (x)
CORE_FRONT = -(BH / 2 + CLR + WALL)         # -13.65 (front outer face, -Y)
H = DECK_T + CAVITY_T                       # 19.0

# ----- rear tray -----
TRAY_IX, TRAY_IY, TRAY_DEPTH = 62.0, 36.0, 14.0   # inner
TRAY_WALL = 3.0
TRAY_FLOOR_T = 3.0
SEP_WALL = 2.0                               # deck rear edge -> tray inner
DECK_REAR = BH / 2 + CLR + WALL              # +13.65
TRAY_Y0 = DECK_REAR + SEP_WALL               # 15.65 tray inner front
TRAY_Y1 = TRAY_Y0 + TRAY_IY                  # 51.65
OUT_Y1 = TRAY_Y1 + TRAY_WALL                 # 54.65 rear outer face
OUT_X = max(CORE_L, TRAY_IX + 2 * TRAY_WALL) # 68.0
TRAY_Z0 = TRAY_FLOOR_T
CABLE_SLOT_W, CABLE_SLOT_H = 14.0, 8.0
CABLE_SLOT_X = (-16.0, 16.0)

# ---------------- base block ----------------
cx = 0.0
oy0, oy1 = CORE_FRONT, OUT_Y1
base = (cq.Workplane("XY")
        .moveTo(-OUT_X / 2, oy0).lineTo(OUT_X / 2, oy0)
        .lineTo(OUT_X / 2, oy1).lineTo(-OUT_X / 2, oy1).close()
        .extrude(H))

# under-pocket wiring cavity (open bottom). ABSOLUTE geometry -- the first
# cut used a faces("<Z") workplane whose Y axis is mirrored (view from below)
# and hollowed the TRAY floor at y~41 instead of the pocket at y~0.
_cw, _ch = CORE_L - 6, BH + 2 * CLR + 2 * WALL - 6
base = base.cut(cq.Workplane("XY").workplane(offset=-1)
                .moveTo(-_cw / 2, -_ch / 2).lineTo(_cw / 2, -_ch / 2)
                .lineTo(_cw / 2, _ch / 2).lineTo(-_cw / 2, _ch / 2).close()
                .extrude(CAVITY_T + 1))

# board pocket
base = (base.faces(">Z").workplane(centerOption="CenterOfBoundBox")
        .center(0, -((oy0+oy1)/2))
        .rect(BW + 2 * CLR, BH + 2 * CLR).cutBlind(-POCKET_D))

# front finger notch (kept: handy even with self-eject)
base = (base.faces(">Z").workplane(centerOption="CenterOfBoundBox")
        .center(0, -((oy0+oy1)/2))
        .pushPoints([(0, CORE_FRONT + WALL / 2)])
        .slot2D(12, 8, 0).cutBlind(-POCKET_D - 2))

# wired pin bores + lifter bore, through the deck
floor_z = H - POCKET_D
base = (base.faces(">Z").workplane(offset=-POCKET_D, centerOption="CenterOfBoundBox")
        .center(0, -((oy0+oy1)/2))
        .pushPoints(J3 + LIFTERS).circle(PIN_HOLE / 2).cutThruAll())
# ejector plunger bore
base = base.cut(cq.Workplane("XY", origin=(PLUNGER_XY[0], PLUNGER_XY[1], -1))
                .circle(PLUNGER_BORE / 2).extrude(H + 2))
# front-wall slot for the lever (below the finger notch, which stays up top)
base = base.cut(cq.Workplane("XY").workplane(offset=1.5)
                .moveTo(LEVER_X0 - 1.0, CORE_FRONT - 1)
                .lineTo(LEVER_X1 + 1.0, CORE_FRONT - 1)
                .lineTo(LEVER_X1 + 1.0, CORE_FRONT + WALL + 1)
                .lineTo(LEVER_X0 - 1.0, CORE_FRONT + WALL + 1)
                .close().extrude(6.5))

# tray cavity + cable slots + wire tunnel
tray = (cq.Workplane("XY").workplane(offset=TRAY_Z0)
        .moveTo(-TRAY_IX / 2, TRAY_Y0).lineTo(TRAY_IX / 2, TRAY_Y0)
        .lineTo(TRAY_IX / 2, TRAY_Y1).lineTo(-TRAY_IX / 2, TRAY_Y1).close()
        .extrude(H - TRAY_Z0 + 1))
base = base.cut(tray)
for sx in CABLE_SLOT_X:
    slot = (cq.Workplane("XY").workplane(offset=TRAY_Z0)
            .moveTo(sx - CABLE_SLOT_W / 2, TRAY_Y1 - 1)
            .lineTo(sx + CABLE_SLOT_W / 2, TRAY_Y1 - 1)
            .lineTo(sx + CABLE_SLOT_W / 2, OUT_Y1 + 1)
            .lineTo(sx - CABLE_SLOT_W / 2, OUT_Y1 + 1).close()
            .extrude(CABLE_SLOT_H))
    base = base.cut(slot)
# tunnel: tray front wall -> pin cavity, under the deck
tunnel = (cq.Workplane("XY").workplane(offset=1.5)
          .moveTo(-5, 8).lineTo(5, 8).lineTo(5, TRAY_Y0 + 2)
          .lineTo(-5, TRAY_Y0 + 2).close().extrude(4.0))
base = base.cut(tunnel)
# zip-tie slots in the tray floor (two pairs)
for zx in (-14.0, 14.0):
    for zy in (TRAY_Y0 + 9, TRAY_Y1 - 9):
        base = base.cut(cq.Workplane("XY").workplane(offset=-1)
                        .moveTo(zx - 2, zy - 1).lineTo(zx + 2, zy - 1)
                        .lineTo(zx + 2, zy + 1).lineTo(zx - 2, zy + 1)
                        .close().extrude(TRAY_FLOOR_T + 2))

# ---------------- fused additions (posts + engraved marks) ----------------
adds = []
# pivot bosses hanging from the cavity ceiling, with downward-opening slots
# (0.25 mm lip pinch) that the lever's O3 axle stubs snap up into
for bx in (LEVER_X0 - 2.5, LEVER_X1 + 2.5):
    boss = (cq.Workplane("XY", origin=(bx, PIVOT_Y, 1.6))
            .rect(3.0, 5.0).extrude(CAVITY_T - 1.6 + 1.0))       # into deck 1mm
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
fused = fused.clean()
base = cq.Workplane("XY").newObject([fused])

# ENGRAVED arrow on the deck strip between pocket and tray, pointing +Y at
# the cables: the rule is "the board's SPACEBAR/module edge points at the
# cables". Engraving (cut) prints crisper on a top face than embossing.
arrow = (cq.Workplane("XY").workplane(offset=H - 0.5)
         .moveTo(-3.0, DECK_REAR - 3.2).lineTo(3.0, DECK_REAR - 3.2)
         .lineTo(0.0, DECK_REAR - 0.6).close().extrude(1.0))
base = base.cut(arrow)
# engraved dot marking the SWDIO end of the pin row (west end)
base = base.cut(cq.Workplane("XY", origin=(-(CORE_L / 2 - WALL / 2), 3.0, H - 0.5))
                .circle(0.9).extrude(1.0))

# ---------------- separate parts: lever + plunger ----------------
BTN_Y = -16.5
lever = (cq.Workplane("XY").workplane(offset=1.5)
         .moveTo(LEVER_X0, BTN_Y - 1.5).lineTo(LEVER_X1, BTN_Y - 1.5)
         .lineTo(LEVER_X1, 5.0).lineTo(LEVER_X0, 5.0).close()
         .extrude(LEVER_T))
# tip plate reaching west to sit under the plunger at (0, 6.5)
lever = lever.union(cq.Workplane("XY").workplane(offset=1.5)
                    .moveTo(-2.0, 4.5).lineTo(LEVER_X1, 4.5)
                    .lineTo(LEVER_X1, 8.5).lineTo(-2.0, 8.5).close()
                    .extrude(LEVER_T))
# button cap, pressable above the wall slot
lever = lever.union(cq.Workplane("XY").workplane(offset=1.5)
                    .moveTo(LEVER_X0 - 1.5, BTN_Y - 1.5)
                    .lineTo(LEVER_X1 + 1.5, BTN_Y - 1.5)
                    .lineTo(LEVER_X1 + 1.5, BTN_Y + 3.0)
                    .lineTo(LEVER_X0 - 1.5, BTN_Y + 3.0).close()
                    .extrude(LEVER_T + 4.0))
# axle stubs
for sx in (LEVER_X0 - 2.6, LEVER_X1):
    lever = lever.union(cq.Workplane("YZ", origin=(sx, PIVOT_Y, 3.0))
                        .circle(AXLE_D / 2).extrude(2.6))
lfused = None
for s in lever.solids().vals():
    lfused = s if lfused is None else lfused.fuse(s)
lever = cq.Workplane("XY").newObject([lfused.clean()])

plunger = (cq.Workplane("XY").circle(5.0 / 2).extrude(1.5)
           .faces(">Z").workplane().circle(3.0 / 2).extrude(11.7))

cq.exporters.export(lever, os.path.join(OUT, "flash_station_lever.stl"))
cq.exporters.export(plunger, os.path.join(OUT, "flash_station_plunger.stl"))
cq.exporters.export(base, os.path.join(OUT, "flash_station.stl"))
cq.exporters.export(base, os.path.join(OUT, "flash_station.step"))
print("wrote 3dmodels/flash_station.stl / .step")
print("station %.1f x %.1f x %.1f mm; tray inner %.0f x %.0f x %.0f"
      % (OUT_X, OUT_Y1 - CORE_FRONT, H, TRAY_IX, TRAY_IY, H - TRAY_Z0))
print("7 pin bores: 5 wired at J3 + 2 unwired lifters at", LIFTERS)
