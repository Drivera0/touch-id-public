"""
gen_frame.py -- TouchID flashing jig FRAME v1 (printed part).

The frame carries NO precision and NO small features.  Every tight dimension
lives on the carrier PCB, where the fab holds +/-0.05 mm for free.  This is
the direct response to the v2 printed jig, whose O1.15 x 11.0 mm pogo bores
(9.6:1 aspect) could not be cleared of MJF powder and had to be burned open.

SMALLEST FEATURE HERE: O2.9 mm screw holes, through 11.2 mm of boss = 3.9:1.
Everything else is >= 5 mm.

WHAT IT DOES
  * a 47.4 x 58.4 x 1.8 recess at the top -- the 47 x 58 x 1.6 carrier drops in
    and sits 0.2 mm below the frame's top face (so a USB-C cable clears)
  * one big 24 x 22 opening straight through, OFFSET to sit under the pogo
    pins -- the P75-E2 barrels hang ~14 mm down into it, and it is how you
    reach every solder joint from underneath
  * open bottom, 8 mm walls, 20.2 mm of clear height under the carrier
  * four M3 bosses (self-tapping into nylon, 11.2 mm engagement)
  * two finger notches so the carrier can be lifted out
  * an engraved arrow on the +Y wall = the board's SPACEBAR edge

Usage: python3 gen_frame.py  ->  flash_frame.stl + .step
"""
import os
import cadquery as cq
import gen_carrier as G          # the carrier is the single source of truth

OUT = os.path.dirname(os.path.abspath(__file__))

# ---- carrier it holds (board-local outline, DUT at the origin) ----
# Imported, never retyped.  A frame built against a stale copy of the outline
# or the screw positions is a frame that does not fit, and nothing downstream
# would have caught it.
BX0, BX1, BY0, BY1 = G.BX0, G.BX1, G.BY0, G.BY1
CAR_W, CAR_H, CAR_T = BX1 - BX0, BY1 - BY0, 1.6      # 47 x 58 x 1.6
CCX, CCY = (BX0 + BX1) / 2, (BY0 + BY1) / 2          # 7.5, 9.0 board-local
# Per side, carrier <-> recess.  0.20 was too tight to survive real tolerances:
# JLCPCB route the PCB outline to +/-0.20 mm and MJF PA12 holds +/-0.30 mm, so
# the worst-case carrier (47.20) missed the worst-case recess (47.10) by 0.10.
# The carrier is located by its four M3 screws, not by these walls, so a loose
# recess costs nothing and 0.40 leaves 0.30 mm of slack in the worst case.
CLR = 0.50

def b2f(x, y):
    """board-local -> frame-centred"""
    return (x - CCX, y - CCY)

# ---- frame ----
WALL     = 5.0
H        = 22.0
OUT_W, OUT_H = CAR_W + 2*CLR + 2*WALL, CAR_H + 2*CLR + 2*WALL
REC_W, REC_H = CAR_W + 2*CLR, CAR_H + 2*CLR
REC_D    = CAR_T + 0.2                   # 1.8 -> carrier sits 0.2 below top
# Opening: must clear the pin tails (x -8..0, y 3) and both dowels (+-8.75, 0)
# with soldering room.  Board-local 24 x 22 centred on (0, 2).
OPEN_W, OPEN_H = 24.0, 22.0
OPEN_CX, OPEN_CY = b2f(0.0, 2.0)
DECK_Z   = 17.0                          # cavity ceiling; lip = 20.2 - 17.0
CAV_W, CAV_H = OUT_W - 2*WALL, OUT_H - 2*WALL
MH       = [b2f(x, y) for (x, y) in G.MH]

# ---- SEAT BAR (user's idea, 2026-09-18) --------------------------------
# A raised bar inside the cavity that the pin TAILS land on.  Whichever stop
# the pin reaches first as it descends is the one that governs, and a bar set
# for more protrusion is always reached before the head touches the board --
# so this makes the pin's head geometry IRRELEVANT.  No more Case A / Case B.
#
#   protrusion = SEAT_Z - (carrier top face - pin length)
#
# It is a BAR, not a floor: 8 mm wide in Y, spanning the cavity in X, so there
# is open space on both sides to get a soldering iron in from underneath.
# --- P75-E2, MEASURED.  Dan, 2026-09-18, with calipers:
# ---    gold barrel                13.00 mm
# ---    overall, relaxed           17.00 mm
# ---    overall, fully compressed  14.50 mm
# --- Everything below is those three numbers or arithmetic on them.  The
# --- seller's drawing (amazon.ca B0D48VHRY4, see datasheets/P75-E2-SOURCE.md)
# --- is now only a cross-check, and it checks out: it said 12.5 / 16.54, with
# --- a 1.5 mm head and a 2.54 mm shank.
PIN_TUBE_L  = 13.00    # the GOLD BARREL -- the only part that may be soldered
PIN_L       = 17.00    # tip to tail, relaxed
PIN_COMP_L  = 14.50    # tip to tail, plunger pushed all the way in
TUBE_L_OK   = True
PIN_L_OK    = True

# Derived from the three measurements, not assumed:
PIN_STROKE    = PIN_L - PIN_COMP_L            # 2.50 -- was a GENERIC P75 figure
                                              # with no source, and it is what
                                              # proves the DUT cannot reach the
                                              # carrier.  Now measured.
PIN_PLUNGER_L = PIN_L - PIN_TUBE_L            # 4.00 exposed when relaxed
PIN_HEAD_L    = PIN_COMP_L - PIN_TUBE_L       # 1.50 still out at full squash
PIN_SHANK_L   = PIN_PLUNGER_L - PIN_HEAD_L    # 2.50, swallows completely
STROKE_OK   = True

PIN_TUBE_D  = 1.00     # MEASURED 2026-09-18.  The drawing said 1.02; 1.00 means
                       # 0.05 mm of diametral clearance in the carrier's O1.05
                       # hole rather than 0.03 -- looser than planned but still
                       # a guide, and it fits, which is what the PCB order was
                       # waiting on.
PIN_TUBE_D_OK = True
PIN_SHANK_D = 0.74     # still the drawing's; nothing depends on it
PIN_HEAD_D  = 1.3      # still the drawing's
CARRIER_HOLE_D = 1.05  # from gen_carrier.POGO_DRILL

assert abs((PIN_HEAD_L + PIN_SHANK_L + PIN_TUBE_L) - PIN_L) < 1e-9, \
    "the measured dimension chain does not close"
assert PIN_STROKE > 0 and PIN_COMP_L < PIN_L, \
    "compressed length must be shorter than relaxed"
# The shank must vanish into the barrel at full compression, or the plunger
# would jam on the barrel's mouth instead of bottoming internally.
assert PIN_SHANK_L <= PIN_STROKE + 1e-9, \
    f"shank {PIN_SHANK_L} cannot retract into a {PIN_STROKE} mm stroke"

# THE THING THAT DROVE THIS WHOLE REVISION
# ---------------------------------------
# 4.04 mm of this pin -- the O1.3 head and the O0.74 plunger shank -- lives
# OUTSIDE the barrel.  The earlier design set the bar for "2.0 mm of pin proud
# of the carrier", which put the barrel's top 0.40 mm BELOW the board and left
# the O0.74 PLUNGER sitting in the O1.05 hole.  Soldering there would have
# welded the plunger to the board: five rigid posts with no spring at all, and
# 0.155 mm of radial slop instead of 0.015.
#
# So the bar height is now derived from the BARREL, never from the total
# length.  The barrel fills the board and stands TUBE_PROUD above it for a
# proper fillet; how far the contact tip ends up proud is then whatever the
# pin's own geometry says, not a number anybody gets to choose.
PIN_TOL     = 0.10     # calipers, not a datasheet -- residual uncertainty
TUBE_PROUD  = 0.5      # barrel above the carrier's top face, for the fillet
BAR_W       = 10.0     # width in Y
BAR_Y       = 2.0      # centred BETWEEN the pin row (y=3) and the dowels (y=0)
                       # -- at BAR_W 8 / BAR_Y 3 the dowels sat 1.00 mm from the
                       # bar edge, and a O1.02 dowel had 0.49 mm of bar under
                       # its far side.  10 / 2.0 gives every tail >= 3.00 mm.
DOWEL_PROUD = 7.0      # how far the dowel stands above the carrier.  It has to
                       # beat the contact tip by enough that the DUT is already
                       # threaded on both dowels before any pad touches a pin.
# Screw holes.  Two things were wrong with O2.9 x 11.2:
#  * O2.9 is a CLEARANCE hole for M3, not a self-tapping one -- an M3 major
#    diameter is 3.0, so the thread would have had 0.05 mm of bite per side and
#    would have stripped on the first turn.  A plastic-forming screw wants
#    roughly 0.8 x major; 2.5 gives real engagement in PA12 or PLA.
#  * JLC3DP's own hole table tops out at O2.0 -> h = 2.0..6.0 mm, i.e. a
#    depth limit of 3 x diameter.  11.2 mm on O2.9 is 3.9:1 and over it.  This
#    is the same rule the v2 jig's O1.15 x 11.0 bores broke.
# 7.2 mm of engagement at O2.5 is 2.88:1, and the M3 x 8 screws reach 6.4 mm
# past the 1.6 mm carrier, so they cannot bottom out either.
# 0.8 x major is the textbook thread-forming hole for a soft thermoplastic:
# 0.8 x 3.0 = 2.4.  Note JLC3DP hold holes to +-0.3 mm (MJF) / +-0.4 mm (FDM),
# so this can come back anywhere from 2.0 to 2.8 -- at the loose end an M3 has
# 0.1 mm of material per side to form against.  The carrier is screwed down
# once and the DUT swaps without touching the screws, so that is acceptable;
# if one ever feels loose, a longer screw or a drop of CA fixes it.
MH_D     = 2.4
BOSS_D   = 8.0
BOSS_Z   = 13.5                          # bosses hang from DECK_Z down to here
SCREW_L  = 8.0                           # M3 x 8 self-tapping
JLC_HOLE_ASPECT = 3.0                    # jlc3dp.com/help/article/3d-printing-design-guideline

assert REC_W <= CAV_W + 1e-9 and REC_H <= CAV_H + 1e-9, \
    "recess must not undercut the walls"
for (mx, my) in MH:                      # every screw must land on solid lip
    assert not (abs(mx - OPEN_CX) < OPEN_W/2 + 2.0 and
                abs(my - OPEN_CY) < OPEN_H/2 + 2.0), \
        f"mounting hole ({mx:.1f},{my:.1f}) is too close to the opening"

_hole_depth = (DECK_Z - BOSS_Z) + (H - REC_D - DECK_Z)
assert _hole_depth <= JLC_HOLE_ASPECT * MH_D, \
    (f"screw hole O{MH_D} x {_hole_depth:.1f} mm is {_hole_depth/MH_D:.1f}:1, "
     f"over JLC3DP's {JLC_HOLE_ASPECT}:1")
assert SCREW_L - CAR_T < _hole_depth, \
    f"an M{MH_D} x {SCREW_L} screw bottoms out in a {_hole_depth:.1f} mm hole"

base = cq.Workplane("XY").box(OUT_W, OUT_H, H, centered=(True, True, False))

# cavity: open bottom, up to the deck
base = base.cut(cq.Workplane("XY", origin=(0, 0, -1))
                .rect(CAV_W, CAV_H).extrude(DECK_Z + 1))

# bosses hanging from the deck (added BEFORE the holes are drilled)
bosses = None
for (x, y) in MH:
    b = cq.Workplane("XY", origin=(x, y, BOSS_Z)).circle(BOSS_D/2).extrude(DECK_Z - BOSS_Z)
    bosses = b if bosses is None else bosses.union(b)
base = base.union(bosses)

# the big opening, straight through the deck
base = base.cut(cq.Workplane("XY", origin=(OPEN_CX, OPEN_CY, DECK_Z - 1))
                .rect(OPEN_W, OPEN_H).extrude(H - DECK_Z + 2))

# carrier recess
base = base.cut(cq.Workplane("XY", origin=(0, 0, H - REC_D))
                .rect(REC_W, REC_H).extrude(REC_D + 1))

# finger notches: lift the carrier out.  Cut from the recess wall outward,
# full height of the recess + lip, on the -X and +X sides.
for sx in (-1, 1):
    base = base.cut(cq.Workplane("XY", origin=(sx*(REC_W/2 + 3.0), 0, DECK_Z))
                    .rect(10.0, 18.0).extrude(H - DECK_Z + 1))

# seat bar: pin tails land on its top face
CAR_TOP = (H - REC_D) + CAR_T
CAR_BOT = H - REC_D
SEAT_Z  = CAR_TOP - PIN_TUBE_L + TUBE_PROUD
PIN_PROUD = PIN_L - PIN_TUBE_L + TUBE_PROUD    # DERIVED, not chosen: 4.54
assert 2.0 <= SEAT_Z <= DECK_Z - 4.0, \
    f"seat bar at z={SEAT_Z:.2f} is not sensible inside a {H} mm frame"
# INVARIANT 1 -- only the barrel may be in the hole.  Its top must clear the
# carrier's top face, so the O0.74 plunger never enters the O1.05 hole and can
# never be caught by solder.
assert SEAT_Z + PIN_TUBE_L >= CAR_TOP, \
    (f"barrel top {SEAT_Z+PIN_TUBE_L:.2f} is below the carrier top {CAR_TOP:.2f} "
     f"-- the plunger shank would sit in the hole and get soldered")

# INVARIANT 2 -- the plunger must run out of travel BEFORE the DUT can reach
# the carrier.  That turns "no copper under the DUT" from a drawing rule into a
# physical one: the board cannot touch this surface, whatever anyone presses.
assert PIN_PROUD > PIN_STROKE, \
    (f"tip stands {PIN_PROUD:.2f} proud but the spring travels {PIN_STROKE} -- "
     f"the DUT could be pressed flat onto the carrier's copper")

# INVARIANT 3 -- the dowels must have the DUT threaded before a pad meets a pin
assert DOWEL_PROUD >= PIN_PROUD + 2.0, \
    (f"dowels stand {DOWEL_PROUD} proud, tips {PIN_PROUD:.2f} -- only "
     f"{DOWEL_PROUD-PIN_PROUD:.2f} mm of guide before contact")
_, bar_y = b2f(0.0, BAR_Y)
base = base.union(cq.Workplane("XY", origin=(0, bar_y, 0))
                  .rect(CAV_W, BAR_W).extrude(SEAT_Z))

# screw holes
for (x, y) in MH:
    base = base.cut(cq.Workplane("XY", origin=(x, y, BOSS_Z - 1))
                    .circle(MH_D/2).extrude(H))

# ---- ORIENTATION MARK on the OUTER +Y FACE -------------------------------
#
# Why this matters: b2f() puts the four screw holes on a RECTANGLE,
# (+-19.5, +-25), symmetric in both axes, so the carrier bolts down just as
# happily rotated 180 degrees.  The opening underneath is NOT symmetric -- it is
# offset to sit under the pin row -- so a carrier fitted backwards puts every
# pin tail over solid deck instead of over the seat bar.  This mark is the only
# thing standing between you and that.
#
# Why it is HERE and not on the top face: the top face is a 5.0 mm band, and an
# arrow engraved into it leaves bands of 1.2-1.7 mm.  That was flagged twice by
# wall_check.py and sits under JLC3DP's 2.0 mm minimum wall for a part this
# size, whatever the truth about a 0.5 mm groove backed by 21.5 mm of solid.
# The OUTER face has 5.0 mm of wall to spend: a 1.2 mm deep pocket leaves 3.8 mm
# and nothing on this part is thin at any threshold.  It is also ten times more
# legible, and it is on the side you can see with the jig sitting on the bench.
MARK_D   = 1.2                     # depth into the 5.0 mm outer wall
MARK_W   = 20.0                    # width in X
MARK_Z0, MARK_Z1 = 5.0, 16.0       # base and apex heights
assert WALL - MARK_D >= 2.0, "orientation mark must leave >=2.0 mm of wall"
assert MARK_W/2 + 2.0 <= OUT_W/2 and MARK_Z1 + 2.0 <= H and MARK_Z0 >= 2.0, \
    "orientation mark must leave >=2.0 mm of face on every side"
mark = (cq.Workplane("XZ", origin=(0, OUT_H/2 + 0.5, 0))
        .moveTo(-MARK_W/2, MARK_Z0).lineTo(MARK_W/2, MARK_Z0)
        .lineTo(0.0, MARK_Z1).close().extrude(MARK_D + 0.5))
base = base.cut(mark)

cq.exporters.export(base, os.path.join(OUT, "flash_frame.stl"))
cq.exporters.export(base, os.path.join(OUT, "flash_frame.step"))

bb = base.val().BoundingBox()
print(f"frame  {bb.xlen:.2f} x {bb.ylen:.2f} x {bb.zlen:.2f} mm")
print(f"  recess    {REC_W} x {REC_H} x {REC_D} deep  "
      f"(carrier top sits {REC_D-CAR_T:.1f} below frame top)")
print(f"  opening   {OPEN_W} x {OPEN_H} at frame ({OPEN_CX:.1f}, {OPEN_CY:.1f})")
print(f"  lip       {DECK_Z}..{H-REC_D} = {H-REC_D-DECK_Z:.1f} mm thick; "
      f"narrowest lip {min((REC_W/2)-(abs(OPEN_CX)+OPEN_W/2), (REC_H/2)-(abs(OPEN_CY)+OPEN_H/2)):.1f} mm")
print(f"  clear under carrier: {H-REC_D:.1f} mm   (barrels hang ~14 mm)")
print(f"  smallest feature: O{MH_D} through {_hole_depth:.1f} mm "
      f"= {_hole_depth/MH_D:.1f}:1 aspect  (JLC3DP limit {JLC_HOLE_ASPECT}:1)")
print(f"  +Y MARK   triangle {MARK_W} x {MARK_Z1-MARK_Z0} x {MARK_D} deep on the "
      f"outer +Y face, {WALL-MARK_D} mm of wall left behind it")
print(f"  SEAT BAR  top z = {SEAT_Z:.2f}, {BAR_W} mm wide, spans the cavity in X")
print(f"    barrel {PIN_TUBE_L} long -> its top stands {TUBE_PROUD} proud of the")
print(f"      carrier, so the O1.02 barrel fills the hole and the O0.74")
print(f"      plunger stays clear of it")
print(f"    contact tip therefore stands {PIN_PROUD:.2f} mm proud (derived)")
print(f"    spring travel {PIN_STROKE} -> the DUT can never come closer than "
      f"{PIN_PROUD-PIN_STROKE:.2f} mm to the carrier")
print(f"    iron clearance above the bar: {(H-REC_D)-SEAT_Z:.1f} mm")
print(f"    change PIN_TUBE_L / TUBE_PROUD at the top and re-run")
print(f"  volume {base.val().Volume()/1000:.1f} cm3")
print(f"  CUT THE DOWELS TO {CAR_TOP - SEAT_Z + DOWEL_PROUD:.1f} mm "
      f"({CAR_TOP - SEAT_Z:.1f} inside the frame + {DOWEL_PROUD} proud)")
if not (TUBE_L_OK and PIN_L_OK and STROKE_OK):
    print()
    print("  " + "!"*66)
    print(f"  !! PIN_TUBE_L = {PIN_TUBE_L} is MEASURED -- the print is gated on")
    print(f"  !! that one and it is satisfied.")
    print(f"  !! PIN_L = {PIN_L:.2f} is still implied from the drawing's 4.04 mm")
    print(f"  !! plunger.  It only moves the tip height ({PIN_PROUD:.2f} proud),")
    print(f"  !! never which part of the pin sits in the board, so it is a note.")
    print(f"  !! Measure tip-to-tail when convenient and set PIN_L_OK = True.")
    print("  " + "!"*66)
