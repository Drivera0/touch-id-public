# TouchID module housing — parametric CadQuery model
#
# ============================ v5 — 2026-08-27 =============================
# v5 = v4 + a circular RISER COLUMN on top of the square body, so a VARTA
# CP1254 A4 cell can live between the BLE module and the sensor barrel.
#
#   riser: OD 18.37, ID 15.60, z 7.16 .. 11.66   (+4.50 mm)
#   sensor barrel bottom moves 4.96 -> 9.46
#   cell: rests on the module lid through a 0.20 mm insulating pad
#
# EVERY dimension used here is traced in PART-LIBRARY.md. Two of them differ
# from the numbers in NEXT-SESSION.md, and the difference is deliberate:
#
#   * CP1254 A4 height is 5.4 +0.2/-0.1 -> MODEL AT 5.6, the worst case.
#     NEXT-SESSION says "5.4". A housing cut for 5.4 will not close on a
#     max-tolerance cell.
#   * The cell cannot sit at z 1.80. The MDBT50Q is 2.05 tall and the cell
#     (O12.1, under the centred sensor bore) sits inside the module's
#     footprint, so it has to go ON TOP of the module -- through a 0.20 mm
#     insulating pad, because the module lid is grounded and the can is live.
#
# Consequence: clearance above the cell is ~1.61 mm, not the 2.26 mm the
# brief expected. The brief says to trust the model. See HOUSING-V5-NOTES.md.
#
# Run:  python touchid_module_v5.py
#       -> prints every clearance, runs the boolean checks, exports STEP+STL
# ==========================================================================
#
# TouchID module housing — parametric CadQuery model (v3, caliper-measured)
# Two-tier body copied from the knob module:
#   tier 1 (back, z 0..lip_h):    19.72 sq lip — PCB mounts against its back
#   tier 2 (top,  z lip_h..body_h): 18.64 sq — top face flush with enclosure
# Coordinate system: Z=0 back (PCB/pogo side), Z=body_h = flush top face.
# Housing top-view frame = mirror-x of the PCB pad-side (underside) frame
# (underside photo: ear bottom-right, J7 top-right -> here ear bottom-left).
#
# MEASURED (calipers): body 18.64 x 18.64 x 8.44 total; lip 19.72 sq x 4.20
# tall; ear-hole -> opposite lip corner diagonal 30.4.
# Still photo-estimated: chamfers, ear tab size, screw/post positions.
#
# Run:  python touchid_module.py   -> exports STL + STEP next to this file

import cadquery as cq
import math, os

# ---------------- parameters (mm) ----------------
# ==== CALIPER PASS 2 — 2026-08-20 (supersedes the 2026-08-18 numbers) ====
FIT = 0.15             # print clearance subtracted from measured widths
body_w = 18.52 - FIT   # top tier (measured 18.52, was 18.64)
body_l = 18.52 - FIT
lip_w = 19.66 - 0.12   # back lip tier (measured 19.66, was 19.72)
lip_l = 19.66 - 0.12
# The measured 4.10 "lip" INCLUDES the 1.2 PCB edge (same width, continuous
# from outside). Plastic lip = 2.90 (= arm height, flush top AND bottom); the
# PCB forms the bottom 1.2 of the assembled 8.36 stack.
pcb_t_ref = 1.2
lip_h = 4.10 - pcb_t_ref    # 2.90 — plastic lip only
body_h = 8.36 - pcb_t_ref   # 7.16 — housing back face -> flush top plane
# NOTE the lip is SQUARE (19.66) but the PCB is 19.60 x 17.60 — the board does
# not fill the lip footprint in Y. The back rim it seats on must therefore be
# cut to the PCB's real rectangle, not to a square.
corner_r = 2.0         # rounded corner radius, both tiers
edge_r  = 0.30         # light break — ONLY the upper trim and the middle
                       # trim. Not the back edge, not the sensor pocket.
top_t = 2.0            # top plate thickness (2.0 leaves a 1.0 mm shoulder
                       # under the sensor bezel counterbore -> takes finger load)
# ==== v4 2026-08-20 ====
# MODE picks which of two mutually exclusive layouts to build. See the .md note:
# U1 is 13.2 wide in the cavity, and a connector strip (3.25) plus an opposite
# boss (2.60 even at M1.2) need more spare width than the envelope can give.
#   "connector" - U1 pushed to -X, 4.17 mm strip for the FPC connector,
#                 BOTH PCB screws on +X.
#   "diagonal"  - U1 centred, PCB screws DIAGONAL at (+8.0,-7.0)/(-8.0,+7.0),
#                 no room for a top-side connector.
MODE = "diagonal"

wall_t = 0.8           # was 1.4. Thinning the lip wall widens the cavity from
                       # 16.74 to 17.94, which is what makes either mode work.
                       # 0.8 is comfortable for moulding, thin for FDM.

# ---------------- sensor seat ----------------
# The sensor is fitted from the OUTSIDE into a counterbore and lands on an
# annular shoulder. Pressing the finger loads that shoulder, so the sensor
# CANNOT be pushed into the enclosure. (Seating it from the inside against a
# lip does the opposite: finger pressure drives it inwards.)
#
#   top face  ─┬───────┐            ┌────────  <- flush
#              │  bezel sits here   │            counterbore, depth = bezel t
#              ├───┐           ┌────┤
#              │   │ shoulder  │    │         <- takes the press load
#              │   └───────────┘    │
#              └── window ──────────┘         <- barrel passes through
#
# Size limit: the top tier is 18.52 sq, and keeping >=1.2 mm of plastic around
# the pocket caps the sensor bezel at about Ø16.0. Common round modules are
# bigger than that (R503 Ø18, ZW101 Ø21, R502 Ø22) and will NOT sit flush here.
# ==== v4.1 2026-08-20 — seat reworked for Hi-Link HLK-ZW0905 ====
# Measured from the ZW0905 spec §2.3 drawing, NOT from the spec table:
#   module outline  Ø18.00 +-0.05      <- the table's "Φ12.8" is the sensor
#   barrel          Ø15.50 +-0.05         package, not the module. See the note.
#   total thickness   2.40 +-0.20
#   flange (step)     0.20 +-0.05
#   back connector    4.50 tall  -> REMOVED; six wires are soldered to the pads
#
# The old seat (Ø15.70 counterbore over a Ø13.50 window) cannot take a Ø18.00
# flange at all - the top tier is only 18.37 sq, so a Ø18.10 counterbore would
# leave 0.135 mm of wall. So: NO COUNTERBORE. The barrel locates in the window,
# the 0.20 mm flange bears flat on the top face, and the flange is bonded down.
# Press load still lands on plastic, which was the point of the original seat.
# ==== 2026-08-28: ZW0905 is DISCONTINUED. Replacement = HLK-ZW0922. ====
# The ZW0922 is a DROP-IN and these numbers are unchanged. From its own §2.3
# dimensions drawing (spec V1.0 2024-11-20) -- NOT from its spec table, which
# repeats the same "Dimensions O12.8mm" trap the ZW0905 table had: that is the
# sensor PACKAGE, not the module. See cad/pcb-v3/SENSOR-ZW0922.md.
#   <2> O18.00 +-0.05  metal ring outline  = flange   (was 18.00)  MATCH
#   <1> O15.50 +-0.05  metal ring protrusion = barrel (was 15.50)  MATCH
#   <4> 0.20 +-0.05    step thickness       = flange  (was 0.20)   MATCH
#   <5> 2.15 +-0.20    metal ring + PCB total thickness (was 2.40) THINNER
# Modelling 2.40 is the CONSERVATIVE choice: a thinner sensor lifts the barrel
# bottom and gains clearance above the cell (+0.86 at 2.35, +1.06 at 2.15), so
# leaving it at 2.40 keeps the model pessimistic. Do not "correct" it down
# without re-checking the cell stack.
sensor_module_d  = 18.00   # ZW0922 flange OD, O18.00 +-0.05 -> 18.05 max
sensor_barrel_d  = 15.50   # ZW0922 barrel OD, O15.50 +-0.05 -> 15.55 max
sensor_window_d  = sensor_barrel_d + 0.10     # 15.60 locating fit
                           # WARNING: only 0.05 mm DIAMETRAL at worst case.
                           # SLA will not hold that -- expect to ream the
                           # window on the first print. The barrel locates,
                           # it does not seal, so widening this is cheap.
sensor_thk       = 2.40    # total, flange included (ZW0922 is 2.15 +-0.20)
sensor_flange_t  = 0.20    # sits proud of the top face by this much

# ---------------- v5: riser column + cell seat ----------------
# Riser is a plain annulus standing on the square top plate. Its wall is
#   (18.37 - 15.60)/2 = 1.385 mm, the same wall the v4 top plate already has.
# ==== v5.2 2026-08-28 — riser 4.50 -> 6.50, cell -> a PROTECTED assembly ====
# DELIBERATELY OVERSIZED. Build tall enough that a real, protected, pre-wired
# cell fits, prove the electronics, and shrink later. The cost is that the
# module grows to 14.86 mm total against the 8.36 mm knob module it replaces,
# on a slot depth NOBODY HAS MEASURED (DESIGN-SPEC, open questions). Growing
# the riser helps the CELL fit and makes the KEYBOARD fit harder -- opposite
# directions. If the slot turns out shallow this is the first thing to give.
# ==== v5.3 2026-08-29 — TWO VARIANTS, selected by VARIANT below ====
# The PCM moved ONTO THE PCB (Mitsumi MC3651), so the cell no longer carries
# one. A bare cell with factory leads is 5.6 mm tall, not the 8.4 mm a
# protected assembly needs -- which lets the riser come back DOWN and makes the
# module SHORTER, cutting the unmeasured-slot risk from 6.50 mm to 4.50 mm.
#
# Both are kept because the choice is not final: "tall" still works if a
# protected cell assembly turns up, "short" is the plan of record.
#
#   VARIANT = "tall"   riser 6.50, cell O13.5 x 8.4 (protected assembly),
#                      pocket O14.00, module 14.86 mm
#   VARIANT = "short"  riser 4.50, cell O12.5 x 5.6 (BARE cell + leads),
#                      pocket O13.00, module 12.86 mm      <-- plan of record
#
# Override from the command line:  python touchid_module_v5.py short
import sys as _sys
VARIANT = "tall"
for _a in _sys.argv[1:]:
    if _a in ("tall", "short"):
        VARIANT = _a

if VARIANT == "short":
    riser_h = 4.50
else:
    riser_h = 6.50              # clears a PCM-carrying cell assembly
riser_od   = body_w             # 18.37 — flush with the top tier
riser_id   = sensor_window_d    # 15.60 — continuous with the barrel window
top_h      = body_h + riser_h   # 13.66 tall / 11.66 short

# ---- the cell is now an ASSEMBLY, not a bare cell ----
# Target: LiPol LPM1254, 65-80 mAh Li-ion coin, supplied WITH PCM AND WIRES.
#   bare cell   O12.0 x 5.4
#   assembled   O12.5 x 8.4   <- PCM adds ~+0.5 dia / ~+3.0 thickness
# A bare CP1254 was O12.1 x 5.6. These numbers are the FINISHED assembly, which
# is what actually has to fit -- the old ones described a cell you are not
# allowed to attach wires to (CoinPower handbook 8.7). See BUY-YOURSELF.md.
# LIPOL CONTRADICT THEMSELVES ON DIAMETER, so this is built to the WORSE one:
#   website rule  "+0.5 mm dia"        -> assembled O12.5
#   LPM1254 datasheet drawing          -> finished pack **O13 +-0.5 -> 13.5 max**
# O13.5 is modelled. A pocket cut for 12.5 would not close on the datasheet
# part, and this is a 3D print -- being 1 mm generous costs nothing, being 1 mm
# short costs a reprint and a wait. Resolve it with LiPol before production.
#
# The datasheet publishes NO assembled thickness, so 8.4 is still the website's
# "+3.0 mm" blanket adder on a 5.4 cell -- NOT a per-model figure. There is
# 0.81 mm of slack above it, so an assembly up to 9.2 still fits.
#
# It DOES publish the protection, and the numbers are good for this cell:
#   over-charge   4.25 V +-50 mV (release 4.00)   <- VBAT_OV 3.912 sits clear
#   over-discharge 2.75 V +-50 mV (restore 3.50)
#   over-current  0.2 .. 0.75 A                   <- right-sized for 140 mA
#   charge        4.2 V +-50 mV
if VARIANT == "short":
    # BARE cell with factory-attached leads. No PCM on the cell -- it is on the
    # board (MC3651). Sized for the widest bare 1254-class cell: an LIR1254 is
    # O12.5 nominal, a VARTA CP1254 A4X is O12.1 +0.0/-0.3, and either may carry
    # a thin kapton wrap. Height 5.4 +0.2/-0.1 -> 5.6 max (VARTA A4X datasheet).
    cell_d_max = 12.5           # widest bare 1254-class cell
    cell_h_max = 5.6            # VARTA A4X worst case; LIR1254 is the same 5.4
    cell_fit   = 0.50
else:
    # PROTECTED ASSEMBLY. LiPol LPM1254 with PCM + wires, datasheet worst case.
    cell_d_max = 13.5           # LPM1254 ASSEMBLED dia, datasheet worst case
    cell_h_max = 8.4            # LPM1254 ASSEMBLED height (website adder)
    cell_fit   = 0.50
cell_pocket_d = cell_d_max + cell_fit          # 13.00 short / 14.00 tall

# The cell has to clear the BLE module's metal lid. The lid is grounded and
# the cell can is live, so this gap is electrical, not just mechanical.
mcu_l, mcu_w, mcu_h = 15.5, 10.5, 2.05         # MDBT50Q-1MV2, Raytac Ver. K
# SETTLED by pcb-v3: the module is 15.5 (y) x 10.5 (x) and sits OFF-CENTRE in
# x, because the BQ25505's ~3.98 mm land will not fit beside a centred module
# on a 19.30 board. See build_pcb_v3.py.
mcu_center = (-0.80, 1.00)   # tracks build_pcb_v3.py U1_CX/U1_CY.
                             # Was 0.90 while the board said 1.00 --
                             # 0.10 mm of drift between the mechanical
                             # model and the board it is built around.
mcu_l, mcu_w = 10.5, 15.5       # (x, y) in board orientation

# The cell rests on the module's lid through an INSULATING PAD.
# v5's first pass used two ledges growing in from the cavity wall at +-Y.
# That only worked while the module was centred: once pcb-v3 pushed it to
# x -0.80, y +1.20, the cell (O12.1 at the origin, under the centred sensor
# bore) no longer overhangs the module anywhere except a 1.6 mm sliver on
# +X, so no ledge can reach it from two sides. Resting it on the lid is
# simpler and gains clearance. The lid is grounded and the cell can is live,
# hence the pad -- it is not optional.
cell_insulator_t = 0.20         # PET / Kapton disc, O12.5, under the cell
cell_z0 = mcu_h + cell_insulator_t             # 2.25
cell_z1 = cell_z0 + cell_h_max                 # 7.85

# No seat ledges in this revision -- see the note above.

# ---------------- rear retention shelf ----------------
# Rectangular shelf on the REAR face that slides under the metal top case and
# acts as a pivot while the opposite (ear) corner is screwed down.
# MEASURED 2026-08-20 off the knob module.
tab_w        = 11.00   # width along the rear face
tab_out      = 1.18    # how far it projects beyond the lip
tab_h        = 2.62    # overall height of the feature above the back plane
tab_t        = 1.36    # shelf plate thickness
tab_gusset   = 1.10    # triangular support at each end, under the shelf
# shelf occupies the TOP of the feature; underneath is open
tab_z0       = None   # set below: shelf underside sits on the lip top

# mounting arm ("thread arm", corner tab at the back plane, csk M2 screw)
# MEASURED 2026-08-20: arm width 5.12; arm TIP to opposite lip corner
# diagonal = 30.14; arm tip to the NEAR EDGE of the screw hole = 1.40.
# Hole is Ø2.0, so tip -> hole CENTRE = 1.40 + 1.0 = 2.40, which agrees with a
# semicircular tip of radius arm_w/2 = 2.56 to within 0.16 (measurement noise),
# i.e. the hole is concentric with the rounded tip as assumed.
#   tip from centre = 30.14 - 19.66*0.70710678 = 16.24
#   hole centre     = 16.24 - 2.40             = 13.84
arm_w = 5.12           # arm width (measured 2026-08-20)
ear_r = arm_w / 2      # 2.56 rounded tip radius
tip_diag_meas = 30.14  # arm tip -> opposite lip corner, measured
tip_to_hole = 2.40     # arm tip -> hole CENTRE (1.40 to near edge + Ø2.0/2)
ear_diag = tip_diag_meas - 19.66 * 0.70710678 - tip_to_hole   # = 13.84
ear_t = lip_h          # arm depth == the lip height exactly, so the arm
                       # top is flush with the middle trim (measured 2.94 ~ 2.90)
# arm spans z 0 .. 3.0 — flush with the lip at both faces; the PCB sits
# below the housing back (z -1.2 .. 0), flush with the arm's bottom plane
# at the module's overall back once assembled on the slot boss
ear_hole_d = 2.0       # measured 2026-08-20 (was 2.3) — M2 clearance
ear_csk_d = 2.90       # countersink top Ø (90 deg) -> csk_h = 0.45 deep.
                       # Just a lead-in chamfer now. An M2 csk head (~3.7 across)
                       # will sit proud; this is a visual/deburr chamfer, not a
                       # true flush-head seat.
ear_corner = (-1, -1)  # bottom-left in housing top view

# PCB mounting — screws RELOCATED to (+-8.3, 0) (symmetric, our choice; the
# knob's positions intruded on the ESP32-C3-MINI-1 footprint). Bosses get a
# flat on the inner side at |x| = 6.75 so the 13.2-wide module clears.
# M1.2 self-tapping (was M2): pilot ~0.8x nominal, boss OD ~2x nominal.
pcb_screw_pilot_d = 0.95
pcb_screw_depth = 4.0
boss_r = 1.20
# Bosses sit ON the corner diagonal at (+-c, +-c), tucked into the cavity
# corners so they fuse into BOTH walls and stay out of the side strips.
# c = 8.10 chosen from two opposing limits:
#   moving OUT along the diagonal buys clearance from U1 (0.31 at c=8.10,
#   0.00 at c=7.45) but eats the outer wall (1.06 at c=8.10, 0.21 at c=8.70).
# The boss radius cannot exceed 1.202 anywhere on the diagonal - that is the
# perpendicular distance from U1's corner (6.6, 8.3) to the line y=x.
boss_c = 8.10
if MODE == "diagonal":
    pcb_screw_pos = [(boss_c, -boss_c), (-boss_c, boss_c)]
else:
    pcb_screw_pos = [(boss_c, boss_c), (boss_c, -boss_c)]
boss_flat_x = 5.00          # boss inner face is 6.90; nothing to shave
post_d = 2.0
post_h = 2.0            # protrudes through the 1.2 PCB by 0.8
post_pos = []   # NO alignment posts (removed per drawing sign-off; screws locate the PCB)

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exports")
u = 0.70710678

def tier(w, l, z0, z1):
    """All four vertical corners rounded — the module sits amongst keycaps, so
    nothing should present a sharp edge."""
    s = cq.Workplane("XY").workplane(offset=z0).rect(w, l).extrude(z1 - z0)
    return s.edges("|Z").fillet(corner_r)

# ---------------- build ----------------
lip_tier = tier(lip_w, lip_l, 0, lip_h)
top_tier = tier(body_w, body_l, lip_h, body_h)
body = lip_tier.union(top_tier)

# MIDDLE TRIM break — done here, while the step is still one clean closed loop.
# Once the shelf and arm merge into it the loop is broken and OCCT refuses.
_mid = [e for e in body.edges().vals()
        if abs(e.BoundingBox().zmax - lip_h) < 0.02
        and abs(e.BoundingBox().zmin - lip_h) < 0.02
        and abs(max(abs(e.BoundingBox().xmax), abs(e.BoundingBox().xmin),
                    abs(e.BoundingBox().ymax), abs(e.BoundingBox().ymin))
                - lip_w / 2) < 0.4]
# (using only xmax/ymax silently dropped the -X/-Y corner arc -> the break
#  stopped dead at that corner. All four extremes must be tested.)
try:
    body = body.newObject(_mid).fillet(edge_r)
    print(f"  middle trim: filleted {len(_mid)} edges")
except Exception as e:
    print(f"  (middle trim skipped: {type(e).__name__})")

# Snapshot the OUTER profile *after* the trim break. Bosses and ribs are
# intersected with this, so they stop at the fillet instead of filling it in
# (that was making the smoothing appear to stop half way along each side).
outline_prism = body

# stepped interior cavity (bigger in the lip tier for the MCU module)
#
# THE CORNERS ARE FILLETED HERE, and it has to be here rather than only in the
# v4 re-cut further down. The cavity is cut TWICE, and a later cut can only
# REMOVE material -- it can never put a sharp corner back. Filleting only the
# re-cut fixed three corners and missed the fourth, because the three that
# improved had the mounting arm or a screw boss unioned into them afterwards,
# which refilled them; the plain +x+y corner had nothing added and stayed at
# 0.300 mm.
cav_corner_r = 1.60
cav_lo = (lip_w - 2 * wall_t, lip_l - 2 * wall_t)      # z 0..lip_h
cav_hi = (body_w - 2 * wall_t, body_l - 2 * wall_t)    # z lip_h..body_h-top_t


def _cavity_cutter(w, h, z0, dz):
    """Rounded-corner cavity prism. See the wall-thickness note below."""
    return (cq.Workplane("XY").workplane(offset=z0)
            .rect(w, h).extrude(dz)
            .edges("|Z").fillet(cav_corner_r))


body = body.cut(_cavity_cutter(cav_lo[0], cav_lo[1], -0.5, lip_h + 0.5))
body = body.cut(_cavity_cutter(cav_hi[0], cav_hi[1], lip_h,
                               body_h - top_t - lip_h))

# sensor bore: through-window all the way, then a counterbore cut DOWN from the
# TOP face so the bezel drops in from outside and lands on the shoulder.
body = (body.faces(">Z").workplane()
        .circle(sensor_window_d / 2).cutThruAll())
# no counterbore - see the ZW0905 note above

# ---- v5: circular riser column ----
# Annulus standing on the square top plate. Continuous bore, so the sensor
# barrel drops straight through the riser and lands at z 9.46.
riser = (cq.Workplane("XY").workplane(offset=body_h)
         .circle(riser_od / 2).circle(riser_id / 2).extrude(riser_h))
body = body.union(riser)

# (cell seat and collar are added AFTER the v4 cavity re-cut further down —
#  putting them here would get carved straight back out again.)

# ---- rear retention shelf (slides under the metal top case) ----
# Underside sits ON the top of the lip tier (z = lip_h) so the pocket it forms
# starts where the lower trim ends. Two triangular gussets above it tie the
# shelf back into the upper tier, blending both trims.
_y_lip  = lip_l / 2          # +Y is REAR
_y_top  = body_l / 2         # upper tier face, 0.59 further in
tab_z0  = lip_h                       # shelf underside
tab_z1  = tab_z0 + tab_t              # shelf top
gus_h   = tab_h - tab_t               # gusset rise above the shelf
shelf = (cq.Workplane("XY").workplane(offset=tab_z0)
         .center(0, (_y_top + _y_lip + tab_out) / 2)
         .rect(tab_w, (_y_lip + tab_out) - _y_top).extrude(tab_t))
body = body.union(shelf)
for _x0 in (-tab_w / 2, tab_w / 2 - tab_gusset):
    # triangular brace UNDER the shelf, running back down the lip wall
    gus = (cq.Workplane("YZ").workplane(offset=_x0)
           .moveTo(_y_lip, tab_z0)
           .lineTo(_y_lip + tab_out, tab_z0)
           .lineTo(_y_lip, tab_z0 - gus_h)
           .close().extrude(tab_gusset))
    body = body.union(gus)

# ---- mounting ear: circle + connecting bar along the corner diagonal ----
sx, sy = ear_corner
ex, ey = sx * ear_diag * u, sy * ear_diag * u
arm_z0 = 0.0                    # arm bottom flush with the back plane
ear = (cq.Workplane("XY").workplane(offset=arm_z0)
       .center(ex, ey).circle(ear_r).extrude(ear_t))
# short bar only bridging the rounded corner gap (kept OUT of the cavity)
bar_in, bar_out = 9.0, ear_diag        # reach well inside the lip so the
                                       # arm fuses with the trim, not just kisses it
bar_cx = sx * (bar_in + bar_out) / 2 * u
bar_cy = sy * (bar_in + bar_out) / 2 * u
bar_rot = 45 if sx * sy > 0 else -45
bar = (cq.Workplane("XY").workplane(offset=arm_z0)
       .center(bar_cx, bar_cy).rect(bar_out - bar_in, 2 * ear_r).extrude(ear_t)
       .rotate((bar_cx, bar_cy, 0), (bar_cx, bar_cy, 1), bar_rot))
arm = ear.union(bar)
# same break as the two trims (edge_r), so every softened edge matches
for _sel, _what in ((">Z", "arm top"), ("<Z", "arm bottom")):
    for _r in (edge_r, edge_r * 0.75, edge_r * 0.5):
        try:
            arm = arm.edges(_sel).fillet(_r)
            print(f"  {_what}: filleted at r={_r:.2f}")
            break
        except Exception:
            continue
    else:
        print(f"  ({_what} break skipped)")
body = body.union(arm)

# --- v4 FIX: the ear bar reaches radius 9.0 along the corner diagonal, which is
# inside the cavity footprint. Re-cut both cavity tiers so the bar cannot fill
# the corner and foul the ESP32 module.
#
# v5.1: the cavity corners are now FILLETED, and that is a structural fix, not
# cosmetic. Measured on the previous build at z = 1.5:
#
#     wall along -x flat side      0.800 mm      <- the intended wall_t
#     wall along -y flat side      0.795 mm
#     wall along the -45 diagonal  0.150 mm      <- the corners
#
# The outer lip is a ROUNDED square, so its corner radius (~2.38) pulls the
# outside surface INWARD at each corner, while the inner cavity was a SHARP
# rectangle whose corner pokes OUTWARD. They converge: outer corner at
# d = 12.840 along the diagonal, inner at d = 12.690. That left 0.15 mm of
# material on ALL FOUR corners, well inside JLCPCB's red (<0.5 mm) DFM band --
# and it is the true cause of the red regions their thin-wall heatmap flagged.
#
# Rounding the INNER corner pulls it back to d = 12.040 and restores 0.80 mm.
# Doing it on the inside costs nothing where it matters: wall_t stays 0.8 on
# the flats, U1's nearest corner is ~4.5 mm clear of the cavity corner, and the
# extra material lands around the M1.2 bosses at (+-8.10, -+8.10), which sit on
# that same diagonal -- so the bosses get reinforced for free.
body = body.cut(_cavity_cutter(cav_lo[0], cav_lo[1], -0.5, lip_h + 0.5))
body = body.cut(_cavity_cutter(cav_hi[0], cav_hi[1], lip_h,
                               body_h - top_t - lip_h))

# ---- v5: no cell seat ledges ----
# The cell sits on the module lid through cell_insulator_t. Nothing to build.
seat_z0 = seat_z1 = None

# ---- v5: cell centring collar ----
# Two arcs, ID = cell_pocket_d, OD = the top-tier cavity, so they fuse into
# the cavity wall at +-Y. The +-X sides are deliberately left OPEN: that is
# where the six hand-soldered sensor wires drop past the cell to J2 at
# (+-7.60, 2.90 / 4.40 / 5.90).
collar_z0 = lip_h                       # 2.90 — top-tier cavity starts here
collar_z1 = body_h - top_t              # 5.16 — the bore starts here
# collar_od WAS body_w - 2*wall_t = 16.77, which is EXACTLY the top-tier cavity
# width. That made the arc perfectly TANGENT to the cavity wall, so the union
# below joined two coincident surfaces along a line instead of through a
# volume -- and the exported STL carried two NON-MANIFOLD edges because of it,
# at (0, +-8.385) spanning z 2.90..5.16, each shared by four faces instead of
# two. No holes, no gaps: a closed mesh with two bad edges.
#
# Growing the arc by 0.2 mm gives the boolean a real volume to work with, and
# the mesh comes out watertight with zero non-manifold edges.
#
# BE HONEST ABOUT THE COST: this is NOT a pure topology change. The cavity is
# RECTANGULAR and the collar is a CIRCULAR arc, so the two only touch at
# exactly +-Y. Everywhere else across the +-45 deg span the extra radius adds
# material into open cavity, not into the wall -- volume goes 1101.53 ->
# 1111.44 mm^3, about +9.9 mm^3.
#
# That material collides with nothing: all eight boolean checks still pass, it
# sits above the MCU (which ends at z 2.05) and outside the cell pocket (ID is
# unchanged at 12.50). And it lands as a skirt at the collar/wall junction,
# which is one of the places JLC's DFM flagged as thin -- so it helps there.
collar_wall_bite = 0.20
collar_od = body_w - 2 * wall_t + 2 * collar_wall_bite   # 17.17
collar_half_ang = 45.0

def _collar(deg_mid):
    a0 = math.radians(deg_mid - collar_half_ang)
    a1 = math.radians(deg_mid + collar_half_ang)
    ro, ri = collar_od / 2, cell_pocket_d / 2
    n, pts = 16, []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        pts.append((ro * math.cos(a), ro * math.sin(a)))
    for i in range(n + 1):
        a = a1 - (a1 - a0) * i / n
        pts.append((ri * math.cos(a), ri * math.sin(a)))
    return (cq.Workplane("XY").workplane(offset=collar_z0)
            .polyline(pts).close().extrude(collar_z1 - collar_z0))

for _d in (90.0, 270.0):
    body = body.union(_collar(_d).intersect(outline_prism))

# ear screw hole + 90-deg countersink opening at the arm's top face (z=ear_t)
arm_top = arm_z0 + ear_t
hole = (cq.Workplane("XY").workplane(offset=arm_z0 - 0.5)
        .center(ex, ey).circle(ear_hole_d / 2).extrude(ear_t + 1))
csk_h = (ear_csk_d - ear_hole_d) / 2
cone = cq.Solid.makeCone(ear_hole_d / 2, ear_csk_d / 2, csk_h,
                         cq.Vector(ex, ey, arm_top - csk_h), cq.Vector(0, 0, 1))
body = body.cut(hole).cut(cq.Workplane("XY").add(cone))
# NOTE: no screwdriver relief cut here. The upper tier is already 0.59 per
# side narrower than the lip, which clears the screw head; the old relief
# cylinder was carving a notch out of the ear corner.

# PCB screw bosses inside cavity + pilot holes from the back
for (px, py) in pcb_screw_pos:
    boss = cq.Workplane("XY").center(px, py).circle(boss_r).extrude(pcb_screw_depth + 0.5)
    boss = boss.intersect(outline_prism)
    # shave the inner flat so the ESP32 module clears
    keep = (cq.Workplane("XY")
            .center((abs(px) + 20) / 2 * (1 if px > 0 else -1), py)
            .rect(abs(px) + 20 - 2 * boss_flat_x, 30).extrude(pcb_screw_depth + 0.5))
    boss = boss.intersect(keep)
    body = body.union(boss)
    # pilot hole cut at absolute coordinates (face-selection was unreliable
    # once a boss merged into the wall — one hole ended up missing)
    pilot = (cq.Workplane("XY").workplane(offset=-0.1)
             .center(px, py).circle(pcb_screw_pilot_d / 2)
             .extrude(pcb_screw_depth + 0.1))
    body = body.cut(pilot)

# alignment posts on the back face (protrude outward, through PCB holes)
for (px, py) in post_pos:
    post = cq.Workplane("XY").center(px, py).circle(post_d / 2).extrude(-post_h)
    body = body.union(post)
    in_cavity = (abs(px) + post_d / 2 < cav_lo[0] / 2 and
                 abs(py) + post_d / 2 < cav_lo[1] / 2)
    if in_cavity:
        wy = (lip_l / 2) * (1 if py >= 0 else -1)
        rib = (cq.Workplane("XY")
               .center(px, (py + wy) / 2).rect(3.0, abs(wy - py))
               .extrude(2.0).intersect(outline_prism))
        body = body.union(rib)

# ---------------- export ----------------

# ---------------- soften the two trim edges only ----------------
# Requested: break the UPPER trim (top face perimeter) and the MIDDLE trim
# (top edge of the lip). Leave the back edge sharp and leave the sensor
# pocket sharp so the bezel seats squarely.
def _fillet(sel_edges, r, what):
    global body
    if not sel_edges:
        print(f"  (no edges found for {what})"); return
    try:
        body = body.newObject(sel_edges).fillet(r)
    except Exception as e:
        print(f"  (skipped {what}: {type(e).__name__})")

# upper trim: outer perimeter of the top face, EXCLUDING the sensor pocket
_top_edges = []
for e in body.faces(">Z").edges().vals():
    bb = e.BoundingBox()
    if max(abs(bb.xmax), abs(bb.xmin), abs(bb.ymax), abs(bb.ymin)) > body_w / 2 - 0.6:
        _top_edges.append(e)
_fillet(_top_edges, edge_r, "upper trim")
print(f"  upper trim: {len(_top_edges)} edges selected")



# ---------------- matching PCB blank ----------------
# Square board, sized so that worst-case JLCPCB outline tolerance (~+-0.2)
# still sits inside the 19.54 lip. Screw holes are M1.2 clearance.
pcb_sq_v4 = 19.30
pcb_hole_d = 1.30
pcb = (cq.Workplane("XY").workplane(offset=-pcb_t_ref)
       .rect(pcb_sq_v4, pcb_sq_v4).extrude(pcb_t_ref)
       .edges("|Z").fillet(corner_r))
for (px, py) in pcb_screw_pos:
    pcb = pcb.cut(cq.Workplane("XY").workplane(offset=-pcb_t_ref - 0.1)
                  .center(px, py).circle(pcb_hole_d / 2).extrude(pcb_t_ref + 0.2))

# ================= v5 VERIFICATION — boolean, not arithmetic =================
# NEXT-SESSION Task B asks for all of these to be proved by intersection and
# for the volumes to be printed. A number computed by hand is not evidence;
# an intersection volume is.

def _vol(shape):
    try:
        return shape.val().Volume()
    except Exception:
        return 0.0

# --- reference solids, all at their assembled positions ---
mcu_solid = (cq.Workplane("XY")
             .center(*mcu_center).rect(mcu_l, mcu_w).extrude(mcu_h))
# the insulating pad, so the boolean checks see the real stack
pad_solid = (cq.Workplane("XY").workplane(offset=mcu_h)
             .center(0, 0).circle(cell_pocket_d / 2).extrude(cell_insulator_t))

cell_solid = (cq.Workplane("XY").workplane(offset=cell_z0)
              .circle(cell_d_max / 2).extrude(cell_h_max))

_barrel_bot = top_h - (sensor_thk - sensor_flange_t)     # 9.46
sensor_barrel = (cq.Workplane("XY").workplane(offset=_barrel_bot)
                 .circle(sensor_barrel_d / 2).extrude(top_h - _barrel_bot))
sensor_flange = (cq.Workplane("XY").workplane(offset=top_h)
                 .circle(sensor_module_d / 2).extrude(sensor_flange_t))
sensor_solid = sensor_barrel.union(sensor_flange)

boss_solids = None
for (px, py) in pcb_screw_pos:
    _b = cq.Workplane("XY").center(px, py).circle(boss_r).extrude(pcb_screw_depth + 0.5)
    boss_solids = _b if boss_solids is None else boss_solids.union(_b)

print("\n" + "=" * 66)
print("v5 BOOLEAN CHECKS  (all must be 0.000 mm^3)")
print("=" * 66)

_checks = [
    ("housing  n  MCU module ", body,          mcu_solid),
    ("housing  n  sensor     ", body,          sensor_solid),
    ("housing  n  cell       ", body,          cell_solid),
    ("cell     n  sensor     ", cell_solid,    sensor_solid),
    ("cell     n  MCU module ", cell_solid,    mcu_solid),
    ("cell     n  bosses     ", cell_solid,    boss_solids),
    ("MCU      n  sensor     ", mcu_solid,     sensor_solid),
    ("MCU      n  bosses     ", mcu_solid,     boss_solids),
]
_fails = 0
for _name, _a, _b in _checks:
    try:
        v = _vol(_a.intersect(_b))
    except Exception as e:
        v = float("nan")
        print(f"  {_name}: intersect raised {type(e).__name__}")
    flag = "OK  " if (v == v and v < 1e-6) else "FAIL"
    if flag == "FAIL":
        _fails += 1
    print(f"  [{flag}] {_name} = {v:10.4f} mm^3")

# --- nothing below z = 0 ---
_bb = body.val().BoundingBox()
_below = "OK  " if _bb.zmin > -1e-6 else "FAIL"
if _below == "FAIL":
    _fails += 1
print(f"  [{_below}] housing zmin              = {_bb.zmin:10.4f} mm  (must be >= 0)")
print(f"         housing zmax              = {_bb.zmax:10.4f} mm  (expect {top_h:.2f})")
print(f"         housing volume            = {_vol(body):10.2f} mm^3")

print("\n" + "-" * 66)
print("v5 CLEARANCES")
print("-" * 66)
print(f"  riser            : +{riser_h:.2f}  OD {riser_od:.2f}  ID {riser_id:.2f}"
      f"  wall {(riser_od - riser_id) / 2:.3f}")
print(f"  top face         : z {top_h:.2f}   (v4 was {body_h:.2f})")
print(f"  sensor barrel bot: z {_barrel_bot:.2f}   (v4 was {body_h - (sensor_thk - sensor_flange_t):.2f})")
print(f"  MCU module top   : z {mcu_h:.2f}")
print(f"  cell seat        : rests on the module lid through a "
      f"{cell_insulator_t:.2f} mm insulating pad"
      f"")
print(f"  cell             : z {cell_z0:.2f} .. {cell_z1:.2f}"
      f"   (O{cell_d_max} x {cell_h_max} MAX-tolerance)")
print(f"  cell over MCU    : {cell_z0 - mcu_h:.2f} mm (the pad)")
print(f"  CLEARANCE ABOVE CELL -> barrel : {_barrel_bot - cell_z1:.2f} mm")
print(f"     NEXT-SESSION expected 2.26 mm."
      f"  Discrepancy = {(_barrel_bot - cell_z1) - 2.26:+.2f} mm")
print(f"       cause 1: cell height max is 5.6, not 5.4        -0.20")
print(f"       cause 2: cell sits on the 2.05 module + pad     "
      f"{-(cell_z0 - 1.80):+.2f}")
print(f"  module centre    : {mcu_center}")
print(f"  tallest board part: L1 at 1.20 (C5/C7 are now 0603, ~0.90) — clear")
print(f"  cell radial slop in collar      : "
      f"{(cell_pocket_d - cell_d_max) / 2:.2f} mm per side")
print(f"  wire windows                    : +-X, open from z {collar_z0:.2f}"
      f" to {collar_z1:.2f}, {90 - collar_half_ang:.0f} deg each side of the X axis")
print("=" * 66)
if _fails:
    print(f"  *** {_fails} CHECK(S) FAILED — do not export this as good ***")
else:
    print("  all boolean checks passed")
print("=" * 66 + "\n")

_tag = "v5_" + MODE + "_" + VARIANT
cq.exporters.export(pcb, os.path.join(out_dir, f"touchid_pcb_{_tag}.step"))
cq.exporters.export(pcb, os.path.join(out_dir, f"touchid_pcb_{_tag}.stl"), tolerance=0.01)

_asm = cq.Assembly()
_asm.add(body,         name="housing", color=cq.Color(0.74, 0.74, 0.72))
_asm.add(pcb,          name="pcb",     color=cq.Color(0.13, 0.34, 0.21))
_asm.add(mcu_solid,    name="mdbt50q", color=cq.Color(0.20, 0.20, 0.22))
_asm.add(cell_solid,   name="cp1254",  color=cq.Color(0.85, 0.72, 0.25))
_asm.add(sensor_solid, name="zw0905",  color=cq.Color(0.10, 0.10, 0.12))
_asm.export(os.path.join(out_dir, f"touchid_assembly_{_tag}.step"))

cq.exporters.export(body, os.path.join(out_dir, f"touchid_housing_{_tag}.stl"),
                    tolerance=0.01)
cq.exporters.export(body, os.path.join(out_dir, f"touchid_housing_{_tag}.step"))
print(f"exported touchid_housing_{_tag}.stl / .step and "
      f"touchid_assembly_{_tag}.step to", out_dir)
print(f"  wall {wall_t}  lip cavity {lip_w - 2*wall_t:.2f} sq"
      f"  screws M1.2 at {pcb_screw_pos}")
print(f"  ear screw: M2, unchanged, hole d{ear_hole_d}")
_face = riser_od
print(f"  sensor seat: window d{sensor_window_d:.2f} in the d{_face:.2f} riser"
      f" -> {(_face - sensor_window_d) / 2:.3f} mm of wall")
print(f"    ZW0905 flange d{sensor_module_d} on the {_face:.2f} top face"
      f" -> {(_face - sensor_module_d) / 2:.3f} mm margin/side")
