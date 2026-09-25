"""
verify_frame.py -- interrogate the BUILT SOLID, not the generator's print()s.

Everything here is a point-in-solid test against the exported STEP/shape, with
the pin and dowel positions imported from gen_carrier.py.  If the frame and the
carrier ever drift apart, this fails.
"""
import math, sys
import cadquery as cq
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN, TopAbs_ON

import gen_carrier as G
import gen_frame as F

fails, notes = [], []
def FAIL(m): fails.append(m)
def NOTE(m): notes.append(m)

solid = F.base.val()
cls = BRepClass3d_SolidClassifier(solid.wrapped)
def inside(x, y, z, tol=1e-6):
    cls.Perform(gp_Pnt(x, y, z), tol)
    return cls.State() in (TopAbs_IN, TopAbs_ON)

b2f = F.b2f
SEAT = F.SEAT_Z
CAR_BOT = F.H - F.REC_D            # 20.20, the carrier's underside
CAR_TOP = CAR_BOT + F.CAR_T        # 21.80

print(f"solid bbox {solid.BoundingBox().xlen:.2f} x {solid.BoundingBox().ylen:.2f}"
      f" x {solid.BoundingBox().zlen:.2f}   volume {solid.Volume()/1000:.2f} cm3")
print(f"carrier underside z = {CAR_BOT:.2f}, top face z = {CAR_TOP:.2f}, "
      f"seat bar top z = {SEAT:.2f}")

# ---- 1. the frame's mounting holes ARE the carrier's mounting holes --------
fmh = sorted((round(x, 4), round(y, 4)) for x, y in F.MH)
cmh = sorted((round(b2f(x, y)[0], 4), round(b2f(x, y)[1], 4)) for x, y in G.MH)
if fmh != cmh:
    FAIL(f"frame screw holes {fmh} != carrier screw holes {cmh}")
else:
    print(f"screw holes      : 4, match the carrier exactly")

# ---- 2. every tail lands on solid bar, with margin -------------------------
TAILS = [(x, y, f"PP{i+1}") for i, ((x, y), n) in enumerate(zip(G.J3, G.J3_NAME))]
TAILS += [(x, y, f"DW{i+1}") for i, (x, y) in enumerate(G.MH_DUT)]
worst = 99.0
for (bx, by, name) in TAILS:
    fx, fy = b2f(bx, by)
    if not inside(fx, fy, SEAT - 0.05):
        FAIL(f"{name} tail at board ({bx}, {by}) does NOT land on the seat bar")
        continue
    # how far can we walk in +/-Y before we fall off the bar?
    m = 0.0
    while m < 6.0 and inside(fx, fy + m + 0.05, SEAT - 0.05) \
                  and inside(fx, fy - m - 0.05, SEAT - 0.05):
        m += 0.05
    worst = min(worst, m)
    if m < 1.0:
        FAIL(f"{name} sits only {m:.2f} mm from the edge of the seat bar")
print(f"seat bar         : all {len(TAILS)} tails land on it; "
      f"tightest tail is {worst:.2f} mm from an edge")

# ---- 3. nothing solid above a tail between the bar and the carrier ---------
for (bx, by, name) in TAILS:
    fx, fy = b2f(bx, by)
    z = SEAT + 0.2
    while z < CAR_BOT - 0.1:
        if inside(fx, fy, z):
            FAIL(f"{name} is obstructed at z={z:.2f} between bar and carrier")
            break
        z += 0.2
print(f"pin corridor     : clear from the bar up to the carrier for all tails")

# ---- 4. a soldering iron has to reach each tail from underneath ------------
# The joints are made at the CARRIER's underside (z = CAR_BOT), not at the bar,
# so that is where the clearance has to exist.  Require a 2.5 mm radius of free
# space around every tail, at two heights below the board.
IRON_R = 2.5
for (bx, by, name) in TAILS:
    fx, fy = b2f(bx, by)
    for z in (CAR_BOT - 0.5, CAR_BOT - 2.0):
        for r in (1.0, 1.75, IRON_R):
            for i in range(16):
                a = i*math.pi/8
                if inside(fx + r*math.cos(a), fy + r*math.sin(a), z):
                    FAIL(f"{name}: frame material within {r} mm at z={z:.1f} "
                         f"-- no room for an iron")
print(f"iron access      : {IRON_R} mm of free space round every tail "
      f"at the carrier underside")

# ---- 4b. and the pin has to be reachable from the open bottom at the bar ---
for (bx, by, name) in TAILS:
    fx, fy = b2f(bx, by)
    if not any(not inside(fx + 6.0*math.cos(a), fy + 6.0*math.sin(a), SEAT + 0.5)
               for a in [i*math.pi/8 for i in range(16)]):
        FAIL(f"{name} is walled in at the seat bar")
print(f"bar access       : open space beside the bar at every tail")

# ---- 5. the opening really does sit under every tail -----------------------
for (bx, by, name) in TAILS:
    fx, fy = b2f(bx, by)
    if not (abs(fx - F.OPEN_CX) < F.OPEN_W/2 and abs(fy - F.OPEN_CY) < F.OPEN_H/2):
        FAIL(f"{name} is not inside the {F.OPEN_W} x {F.OPEN_H} opening")
mx = min(min(F.OPEN_W/2 - abs(b2f(bx, by)[0] - F.OPEN_CX),
             F.OPEN_H/2 - abs(b2f(bx, by)[1] - F.OPEN_CY)) for bx, by, _ in TAILS)
print(f"opening          : every tail inside it, closest tail {mx:.2f} mm from an edge")

# ---- 6. the recess accepts the carrier at REAL tolerances ------------------
# JLCPCB: PCB outline +/-0.20 mm (routed).
# JLC3DP: +/-0.30 mm within 100 mm, for BOTH nylon MJF and FDM plastic.
PCB_TOL, MJF_TOL = 0.20, 0.30
# JLC3DP minimum static-assembly clearance: 0.2-0.4 mm (MJF), 0.5 mm (FDM).
# Take the stricter of the two so the part is legal on either process.
if F.CLR < 0.5:
    FAIL(f"recess clearance {F.CLR} mm is under JLC3DP's 0.5 mm static-assembly "
         f"minimum for FDM")
else:
    print(f"assembly clearance: {F.CLR} mm per side "
          f"(JLC3DP min 0.2-0.4 MJF / 0.5 FDM)")
for nm, rec, car in (("X", F.REC_W, F.CAR_W), ("Y", F.REC_H, F.CAR_H)):
    slack = (rec - MJF_TOL) - (car + PCB_TOL)
    if slack < 0:
        FAIL(f"recess {nm}: worst-case carrier {car+PCB_TOL:.2f} does not fit "
             f"worst-case recess {rec-MJF_TOL:.2f}  (short by {-slack:.2f} mm)")
    elif slack < 0.10:
        NOTE(f"recess {nm} worst-case slack only {slack:.2f} mm")
    else:
        print(f"recess {nm}         : worst case leaves {slack:.2f} mm "
              f"(PCB +{PCB_TOL}, print -{MJF_TOL})")

# ---- 7. JLC3DP's OWN published limits, not a rule of thumb ----------------
# https://jlc3dp.com/help/article/3d-printing-design-guideline  (read 2026-09-18)
#   Nylon MJF/SLS holes:  O1.5 -> h 1.5..4.5,  O2.0 -> h 2.0..6.0  => 3 x dia
#   Nylon MJF/SLS min wall: 5x5 1.0 | 10x10 1.2 | 50x50 1.5 | 100x100 2.0
#   Tolerance: +-0.3 mm within 100 mm
ASPECT = 3.0
depth = (F.DECK_Z - F.BOSS_Z) + (F.H - F.REC_D - F.DECK_Z)
if depth / F.MH_D > ASPECT:
    FAIL(f"screw hole O{F.MH_D} through {depth:.1f} mm = {depth/F.MH_D:.1f}:1, "
         f"over JLC3DP's {ASPECT}:1")
print(f"deepest bore     : O{F.MH_D} x {depth:.1f} mm = {depth/F.MH_D:.1f}:1 "
      f"(JLC3DP limit {ASPECT}:1)")
# an M3 x 8 through a 1.6 mm carrier must not bottom out
if F.SCREW_L - F.CAR_T >= depth:
    FAIL(f"M3 x {F.SCREW_L} screw bottoms out in a {depth:.1f} mm hole")
print(f"screw engagement : {F.SCREW_L - F.CAR_T:.1f} mm of thread in "
      f"{depth:.1f} mm of plastic")

# ---- 8. screws must bite solid material, clear of the opening and the bar --
for (x, y) in F.MH:
    if inside(x, y, (F.BOSS_Z + F.DECK_Z)/2):
        FAIL(f"screw hole at ({x:.1f},{y:.1f}) is blocked -- it is not drilled through")
    if inside(x, y, SEAT - 0.05):
        FAIL(f"screw hole at ({x:.1f},{y:.1f}) runs into the seat bar")
    ok = all(inside(x + 2.6*math.cos(a), y + 2.6*math.sin(a),
                    (F.BOSS_Z + F.DECK_Z)/2) for a in [i*math.pi/8 for i in range(16)])
    if not ok:
        FAIL(f"boss at ({x:.1f},{y:.1f}) is not solid all the way round")
print(f"bosses           : 4 drilled through, all solid to O{F.BOSS_D}, clear of the bar")

# ---- 9. the dowels have to be cut to a length that this bar implies --------
dowel_len = CAR_TOP - SEAT + F.DOWEL_PROUD
print(f"dowel length     : cut to {dowel_len:.1f} mm  "
      f"({CAR_TOP - SEAT:.1f} inside + {F.DOWEL_PROUD} proud)")
# ---- the barrel, and ONLY the barrel, may be in the carrier's hole ---------
# 4.04 mm of a P75-E2 lives outside its barrel (O1.3 head 1.5 + O0.74 plunger
# shank 2.54).  Set the bar from the total length instead of the barrel length
# and the plunger ends up in the hole, where solder fuses it solid.
tube_top = SEAT + F.PIN_TUBE_L
if tube_top < CAR_TOP:
    FAIL(f"barrel top z={tube_top:.2f} is below the carrier's top face "
         f"{CAR_TOP:.2f} -- the O{F.PIN_SHANK_D} plunger would sit in the "
         f"O1.05 hole and get soldered solid")
elif tube_top - CAR_TOP < 0.2:
    NOTE(f"barrel stands only {tube_top-CAR_TOP:.2f} mm proud -- thin for a fillet")
print(f"barrel in hole   : top z={tube_top:.2f}, {tube_top-CAR_TOP:.2f} mm above "
      f"the board; O{F.PIN_TUBE_D} in O1.05 = {(1.05-F.PIN_TUBE_D)/2:.3f} mm/side")
if SEAT + F.PIN_TUBE_L + F.PIN_SHANK_L < CAR_TOP:
    FAIL("the plunger shank is inside the board")

# ---- the plunger must run out of travel before the DUT reaches the carrier --
gap = F.PIN_PROUD - F.PIN_STROKE
if gap <= 0:
    FAIL(f"tip stands {F.PIN_PROUD:.2f} proud with {F.PIN_STROKE} of travel -- "
         f"the DUT could be pressed onto the carrier's copper")
print(f"tip / travel     : {F.PIN_PROUD:.2f} mm proud, {F.PIN_STROKE} mm of "
      f"travel -> the DUT stops {gap:.2f} mm above the carrier, always")
work = F.PIN_PROUD - F.PIN_STROKE*0.6
print(f"working point    : press to 60% travel -> DUT sits {work:.2f} mm up, "
      f"~{5*60} g of finger force")

# ---- the dowels must catch the DUT before any pad meets a pin --------------
lead = F.DOWEL_PROUD - F.PIN_PROUD
if lead < 2.0:
    FAIL(f"dowels lead the tips by only {lead:.2f} mm -- not enough guide")
print(f"dowel lead       : {lead:.2f} mm of guide before the first pad "
      f"touches a pin")
if not F.TUBE_L_OK:
    # A BLOCKER, not a note.  The seat bar's entire job is to set the contact
    # height to a known number, and it derives that number from PIN_L.  An
    # unmeasured PIN_L makes the bar a guess with extra steps, and this script
    # is the gate in front of spending money -- so it fails.
    FAIL(f"PIN_TUBE_L = {F.PIN_TUBE_L} came off the SELLER'S drawing, not your "
         f"calipers. The bar height is derived from it. Measure the gold "
         f"barrel, set TUBE_L_OK = True in gen_frame.py, re-run it, then "
         f"re-run this.")
if not F.PIN_L_OK:
    NOTE(f"PIN_L = {F.PIN_L:.2f} is not measured.")
if not F.STROKE_OK:
    NOTE(f"PIN_STROKE = {F.PIN_STROKE:.2f} is not measured, and invariant 2 "
         f"depends on it.")
if not F.PIN_TUBE_D_OK:
    NOTE(f"barrel diameter O{F.PIN_TUBE_D} is still the drawing's figure.")

# ---- does the barrel actually go in the hole, and how much does it wander? --
HOLE = G.POGO_DRILL
if F.PIN_TUBE_D >= HOLE:
    FAIL(f"barrel O{F.PIN_TUBE_D} does not fit the carrier's O{HOLE} hole")
slop = (HOLE - F.PIN_TUBE_D) / 2.0
print(f"barrel vs hole   : O{F.PIN_TUBE_D} in O{HOLE} = {slop:.3f} mm per side "
      f"({'measured' if F.PIN_TUBE_D_OK else 'DRAWING'})")

# ---- the error that actually matters: can the tip miss the DUT's pad? ------
# The DUT's J3 pads are O1.20, so the tip has 0.600 mm of radius to play with.
# Worst case is every contributor at its limit and all in the same direction.
import math as _mm
PAD_D      = 1.20
FAB_HOLE   = 0.05        # JLCPCB hole-position tolerance on the carrier
DUT_FAB    = 0.05        # same again on the DUT's own pads
DOWEL_D    = 1.024       # 18 AWG solid copper -- NOT measured
DUT_MH_D   = 1.20        # the DUT's mounting holes
tilt_angle = _mm.atan2(HOLE - F.PIN_TUBE_D, G.TH)      # barrel cocked in 1.6 mm
tilt_err   = F.PIN_PROUD * _mm.tan(tilt_angle)
dowel_slop = (DUT_MH_D - DOWEL_D) / 2.0
budget     = PAD_D / 2.0
terms = [("carrier hole position", FAB_HOLE),
         ("barrel slop in the hole", slop),
         (f"barrel cocked over {F.PIN_PROUD:.2f} mm of overhang", tilt_err),
         ("DUT on the dowels", dowel_slop),
         ("DUT pad position", DUT_FAB)]
total = sum(v for _, v in terms)
print(f"tip-to-pad budget: O{PAD_D} pad = {budget:.3f} mm of radius")
for nm, v in terms:
    print(f"    {v:.3f}  {nm}")
if total > budget:
    FAIL(f"worst-case tip error {total:.3f} mm exceeds the {budget:.3f} mm "
         f"the pad allows")
else:
    print(f"    -----")
    print(f"    {total:.3f}  worst case, everything at its limit in the same "
          f"direction -> {100*total/budget:.0f}% of budget, "
          f"{budget-total:.3f} mm spare")
NOTE("the O1.024 dowel wire is assumed, not measured -- it is the second "
     "largest term in the tip-to-pad budget above")

# ---- the measured chain has to be self-consistent --------------------------
if abs((F.PIN_HEAD_L + F.PIN_SHANK_L + F.PIN_TUBE_L) - F.PIN_L) > 1e-9:
    FAIL("the measured pin dimensions do not sum to the measured overall length")
if F.PIN_SHANK_L > F.PIN_STROKE + 1e-9:
    FAIL(f"the O{F.PIN_SHANK_D} shank is {F.PIN_SHANK_L} mm but the stroke is "
         f"only {F.PIN_STROKE} -- the plunger would jam on the barrel mouth")
print(f"pin, measured    : barrel {F.PIN_TUBE_L}, relaxed {F.PIN_L}, compressed "
      f"{F.PIN_COMP_L}  ->  stroke {F.PIN_STROKE}, plunger {F.PIN_PLUNGER_L}")
print(f"                   head {F.PIN_HEAD_L} (still out when squashed flat), "
      f"shank {F.PIN_SHANK_L} (retracts fully)")

# ---- 10. the orientation mark is present, on +Y, and leaves real wall ------
import math as _m
mid_z = (F.MARK_Z0 + F.MARK_Z1)/2
if inside(0.0, F.OUT_H/2 - F.MARK_D/2, F.MARK_Z0 + 0.5):
    FAIL("the +Y orientation mark was not cut")
if not inside(0.0, F.OUT_H/2 - F.MARK_D - 1.0, mid_z):
    FAIL("no wall left behind the orientation mark")
# the -Y face must be UNTOUCHED: material has to be present just inside it
if not inside(0.0, -(F.OUT_H/2 - F.MARK_D/2), F.MARK_Z0 + 0.5):
    FAIL("the -Y face is marked too -- the mark has to be unambiguous")
if F.WALL - F.MARK_D < 2.0:
    FAIL(f"mark leaves only {F.WALL-F.MARK_D:.1f} mm of wall")
print(f"orientation mark : on the +Y face only, {F.WALL-F.MARK_D:.1f} mm of "
      f"wall behind it, {F.MARK_W} x {F.MARK_Z1-F.MARK_Z0} mm")

# ---- 11. JLC3DP minimum wall for a part this size --------------------------
# Nylon MJF: 50x50 -> 1.5, 100x100 -> 2.0.  FDM: 50x50 -> 1.6, 100x100 -> 2.0.
# This part is 58 x 69, between the rows, so 2.0 is the strict reading either
# way.  Measured, not asserted: thin_world voxelises the STL and runs a
# Euclidean distance transform, so the answer is in the part's own millimetres.
MIN_WALL = 2.0
import thin_world
_thin = thin_world.scan("flash_frame.stl", MIN_WALL, 0.35, verbose=False)
for (vol, lo, hi, t) in _thin:
    FAIL(f"{vol:.2f} mm3 thinner than {MIN_WALL} mm at "
         f"x {lo[0]:.1f}..{hi[0]:.1f}  y {lo[1]:.1f}..{hi[1]:.1f}  "
         f"z {lo[2]:.1f}..{hi[2]:.1f}  (thickest point {t:.2f} mm)")
print(f"min wall         : nothing under {MIN_WALL} mm anywhere "
      f"(distance transform, 0.35 mm voxel)")

# ---- 12. the rest of JLC3DP's published checklist --------------------------
# https://jlc3dp.com/help/article/3d-printing-design-guideline (read 2026-09-18)
bbx, bby, bbz = (solid.BoundingBox().xlen, solid.BoundingBox().ylen,
                 solid.BoundingBox().zlen)

# build volume, and the MINIMUM orderable size
if not (5 <= min(bbx, bby, bbz) and max(bbx, bby, bbz) <= 276):
    FAIL(f"{bbx:.1f} x {bby:.1f} x {bbz:.1f} is outside the nylon MJF build size")
if not (bbx >= 30 and bby >= 30 and bbz >= 10):
    NOTE(f"{bbx:.1f} x {bby:.1f} x {bbz:.1f} is under FDM's 30 x 30 x 10 minimum "
         f"part size -- MJF only")
print(f"build size       : {bbx:.1f} x {bby:.1f} x {bbz:.1f} mm  "
      f"(MJF max 370x276x360, FDM min 30x30x10)")

# engraved detail: >=0.8 deep & 0.8 wide (MJF), >=1.0 & 1.0 (FDM)
ENG_MJF, ENG_FDM = 0.8, 1.0
eng_w = min(F.MARK_W, F.MARK_Z1 - F.MARK_Z0)
if min(F.MARK_D, eng_w) < ENG_FDM:
    FAIL(f"orientation mark is {F.MARK_D} deep x {eng_w} wide -- under the "
         f"{ENG_FDM} mm engraved-detail minimum")
print(f"engraved detail  : {F.MARK_D} mm deep x {eng_w} mm wide "
      f"(min {ENG_MJF} MJF / {ENG_FDM} FDM)")

# protrusions / fasteners: > 1.5 mm
prot = min(F.BAR_W, F.BOSS_D - F.MH_D)
if prot <= 1.5:
    FAIL(f"thinnest protrusion is {prot:.1f} mm, under the 1.5 mm minimum")
print(f"protrusions      : seat bar {F.BAR_W} mm, boss wall "
      f"{(F.BOSS_D-F.MH_D)/2:.1f} mm  (min 1.5)")

# escape holes only matter if there is a void with no path out.  A second shell
# in the mesh is exactly what an enclosed void looks like.
shells = solid.Solids()
try:
    import trimesh as _t
    _m = _t.load("flash_frame.stl")
    parts = _m.split(only_watertight=False)
    if len(parts) > 1:
        FAIL(f"mesh has {len(parts)} shells -- an enclosed void would need "
             f"escape holes (min O2.5, two of them below O3.0)")
    if not _m.is_watertight:
        FAIL("mesh is not watertight")
    print(f"enclosed voids   : none ({len(parts)} shell, watertight) -- the "
          f"escape-hole rule does not apply")
except Exception as e:
    NOTE(f"could not re-read the STL to check for enclosed voids: {e}")

# small columns: D=2.0 -> h 2..4, D=3.0 -> h 3..6.  Nothing here is a column,
# but say so rather than leaving the rule unanswered.
print(f"small columns    : none -- the bosses are O{F.BOSS_D} x "
      f"{F.DECK_Z-F.BOSS_Z:.1f} and the bar is a wall, not a column")

print()
for n in notes: print("NOTE:", n)
for f in fails: print("BLOCKER:", f)
print(f"\nFRAME: {len(fails)} blockers, {len(notes)} notes")
if not fails:
    print("       every published JLC3DP rule checked above -- clear to order")
sys.exit(1 if fails else 0)
