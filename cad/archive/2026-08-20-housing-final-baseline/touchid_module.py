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
wall_t = 1.4           # side wall thickness (1.4 leaves 16.8 sq in the lip
                       # tier -> clears an ESP32-C3-MINI-1 (16.6) by 0.2)

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
sensor_bezel_d   = 15.70   # bezel / outer body Ø + 0.20 clearance
sensor_bezel_t   = 1.00    # bezel thickness -> counterbore depth (flush)
sensor_window_d  = 13.50   # through-hole: barrel Ø + clearance
sensor_lip_t     = (sensor_bezel_d - sensor_window_d) / 2   # 1.10 shoulder

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
pcb_screw_pilot_d = 1.7
pcb_screw_depth = 5.0
pcb_screw_pos = [(8.3, 0.0), (-8.3, 0.0)]
boss_flat_x = 6.75      # inner flat on each boss (clearance for ESP32)
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
cav_lo = (lip_w - 2 * wall_t, lip_l - 2 * wall_t)      # z 0..lip_h
cav_hi = (body_w - 2 * wall_t, body_l - 2 * wall_t)    # z lip_h..body_h-top_t
body = (body.faces("<Z").workplane(invert=True)
        .rect(*cav_lo).cutBlind(lip_h))
body = (body.faces("<Z").workplane(invert=True, offset=lip_h)
        .rect(*cav_hi).cutBlind(body_h - top_t - lip_h))

# sensor bore: through-window all the way, then a counterbore cut DOWN from the
# TOP face so the bezel drops in from outside and lands on the shoulder.
body = (body.faces(">Z").workplane()
        .circle(sensor_window_d / 2).cutThruAll())
body = (body.faces(">Z").workplane()
        .circle(sensor_bezel_d / 2).cutBlind(-sensor_bezel_t))

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
    boss = cq.Workplane("XY").center(px, py).circle(2.3).extrude(pcb_screw_depth + 0.5)
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



cq.exporters.export(body, os.path.join(out_dir, "touchid_module_housing.stl"),
                    tolerance=0.01)
cq.exporters.export(body, os.path.join(out_dir, "touchid_module_housing.step"))
print("exported STL + STEP to", out_dir)
