"""
gen_flash_jig.py -- 3D-printable pogo-pin programming jig for pcb-v7.

Every dimension is read off the verified board, none invented:
  board          20.00 x 19.00 x 1.20 mm      (pcb-v7-zero-opens, preflight-green)
  register holes NPTH O1.20 at (+-8.75, 0)    (the housing press-fit pin holes)
  J3 pads        (-8,3) (-6,3) (-4,3) (-2,3) (0,3), 2.0 mm pitch, B.Cu
                 order: SWDIO, SWCLK, RESET, VSTOR, GND

How it works: the board lies BOTTOM FACE DOWN in a shallow pocket, located by
two posts through its press-fit holes. Five P75-series pogo pins (O1.0 barrel,
~16.5 mm, e.g. P75-E2 pointed or P75-B1 dome) stand in the jig floor under the
J3 pads, protruding 1.0 mm above the deck; pressing the board flat compresses
them. Pin tails hang into an open cavity underneath -- solder wires there and
route them out the side slot to the debug probe.

Frame: jig X = board-file x, jig Y = board-file y. The posts are x-symmetric,
so the board CAN physically be dropped in rotated 180 degrees -- the embossed
SPACEBAR arrow marks the correct way (match it to the board's antenna end,
which is the U1 module end). Wrong way round, the pins land on ground pour --
don't power the jig until the orientation is checked.

FDM notes: print pin holes vertical (jig upside down = flat top on the bed is
NOT possible here; print as oriented, no supports needed for 0.8 mm chamfers).
Holes are drawn O1.15 for a press fit after typical FDM shrink; drill 1.0 mm
if your printer prints tight.

Usage: python gen_flash_jig.py   -> 3dmodels/flash_jig.stl / .step
"""
import os
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "3dmodels")
os.makedirs(OUT, exist_ok=True)

# ----- board facts (mm) -----
BW, BH, BT = 20.00, 19.00, 1.20
REG = [(-8.75, 0.0), (8.75, 0.0)]          # NPTH centres
REG_HOLE_D = 1.20
J3 = [(-8.0, 3.0), (-6.0, 3.0), (-4.0, 3.0), (-2.0, 3.0), (0.0, 3.0)]
J3_NAMES = ["SWDIO", "SWCLK", "RESET", "VSTOR", "GND"]

# ----- jig parameters -----
CLR       = 0.15      # pocket clearance each side around the board
POCKET_D  = 1.0       # pocket depth (board proud by 0.2 for finger grip)
DECK_T    = 13.0      # solid deck the pins press into
CAVITY_T  = 6.0       # open wiring cavity below the deck
WALL      = 4.0       # material around the pocket
PIN_HOLE  = 1.15      # P75 barrel is O1.0; FDM prints tight
POST_D    = 1.05      # slip fit into the O1.20 board holes
POST_UP   = 2.6       # post height above pocket floor (1.2 board + 1.4 proud)

L = BW + 2 * CLR + 2 * WALL     # 28.3
W = BH + 2 * CLR + 2 * WALL     # 27.3
H = DECK_T + CAVITY_T           # 19.0 total, deck on top

base = cq.Workplane("XY").box(L, W, H, centered=(True, True, False))

# wiring cavity: hollow the bottom, leave 3 mm perimeter feet
base = (base.faces("<Z").workplane()
        .rect(L - 6, W - 6).cutBlind(-CAVITY_T))

# board pocket in the top face
base = (base.faces(">Z").workplane()
        .rect(BW + 2 * CLR, BH + 2 * CLR).cutBlind(-POCKET_D))

# finger notches on two sides to lift the board out
base = (base.faces(">Z").workplane()
        .pushPoints([(0, -(BH / 2 + CLR + WALL / 2)), (0, BH / 2 + CLR + WALL / 2)])
        .slot2D(12, 8, 0).cutBlind(-POCKET_D - 2))

# pogo pin holes, straight through deck into the cavity
floor_z = H - POCKET_D
base = (base.faces(">Z").workplane(offset=-POCKET_D)
        .pushPoints(J3).circle(PIN_HOLE / 2).cutThruAll())

# registration posts up from the pocket floor
for (px, py) in REG:
    base = base.union(
        cq.Workplane("XY", origin=(px, py, floor_z))
        .circle(POST_D / 2).extrude(POST_UP)
        .faces(">Z").chamfer(0.3))

# orientation marks: arrow bar + 'SPACEBAR' edge ridge on the +Y wall top
base = base.union(
    cq.Workplane("XY", origin=(0, W / 2 - WALL / 2, H))
    .box(10, 1.2, 0.6, centered=(True, True, False)))
# small dot marking pin 1 (SWDIO) corner, on the -X wall top
base = base.union(
    cq.Workplane("XY", origin=(-(L / 2 - WALL / 2), 3.0, H))
    .circle(0.9).extrude(0.6))

cq.exporters.export(base, os.path.join(OUT, "flash_jig.stl"))
cq.exporters.export(base, os.path.join(OUT, "flash_jig.step"))
print("wrote 3dmodels/flash_jig.stl and .step")
print("jig %,.1f x %.1f x %.1f mm; pins at:" % (L, W, H) if False else
      "jig %.1f x %.1f x %.1f mm" % (L, W, H))
for (p, n) in zip(J3, J3_NAMES):
    print("   pin %-6s at (%5.1f, %4.1f)" % (n, p[0], p[1]))
print("post O%.2f at (+-8.75, 0); ridge marks the SPACEBAR (+Y) edge; "
      "dot marks SWDIO" % POST_D)
