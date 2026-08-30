"""
island_via.py -- drop a via THROUGH the island a stranded pad actually sits in.

THE MEASUREMENT THAT PRODUCED THIS
----------------------------------
gnd_via_anchor asked "is there a via within 2.5 mm of this GND pad?" and got
yes for all 41. That question was wrong. Copper does not care about distance,
it cares about which piece of copper it is. Reading the pour KiCad computed
(pour_truth.py) showed the F.Cu GND fill is 15 separate islands, and exactly
four of them contain NO via at all:

    island  4   0.931 mm2   holds U4.2, U4.5
    island 10   3.157 mm2   holds C7.2
    island 13   0.402 mm2   holds R9.2
    island 14   0.387 mm2   holds U5.4

Those four islands are floating scraps of copper. The pads in them are the five
stranded GND pads, and a via 1 mm away in a NEIGHBOURING island does nothing
for them. One via inside each island connects all five.

WHY "INSIDE THE ISLAND" IS ALSO THE SAFEST PLACE TO DRILL
---------------------------------------------------------
The island is copper KiCad already poured, so it already honours every F.Cu
clearance to every other net. A via whose copper circle lies ENTIRELY inside it
is therefore clearance-legal on F.Cu for free -- no separate pad-clearance test
to get wrong, which is the test that has been got wrong repeatedly here (pad
rotation ignored, keep-outs tested at the centre point rather than grown by the
via radius).

The hole still pierces the other three layers, so those are checked the hard
way: tracks on every layer, non-GND pads with rotation applied, pogo contacts
including J4.5, the antenna keep-out grown by the via radius, hole-to-hole, and
the R2.0 board corners.

AND IT MUST LAND SOMEWHERE
--------------------------
A via connecting an island to nothing is decoration. The via centre is required
to fall inside the In2.Cu GND plane polygon as well, so there is copper at the
far end. That is the whole point: island -> via -> plane.

Usage:  python island_via.py IN.kicad_pcb OUT.kicad_pcb
Then FILL ZONES IN KICAD and re-run pour_truth.py -- nothing here connects
anything until the pour is regenerated.
"""
import math
import os
import sys

import pour_truth as pt

HERE = os.path.dirname(os.path.abspath(__file__))
VIA_D, VIA_DRILL, CLR = 0.45, 0.20, 0.10
HALF, EDGE, CORNER_R, H2H = 9.65, 0.30, 2.00, 0.20
POGO_REFS = ("J4", "J11")
STEP = 0.02


def fab_floor():
    global VIA_D, VIA_DRILL, CLR
    p = os.path.join(HERE, "fab_floor_touchid.txt")
    if not os.path.exists(p):
        return
    for line in open(p):
        if "=" in line and not line.strip().startswith("#"):
            k, v = [s.strip() for s in line.split("=", 1)]
            if k == "clearance":
                CLR = float(v)
            elif k == "via_diameter":
                VIA_D = float(v)
            elif k == "via_drill":
                VIA_DRILL = float(v)


def poly_area(pts):
    s = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def dist_to_edges(x, y, pts):
    return min(pt.seg_dist(x, y, pts[i][0], pts[i][1],
                           pts[(i + 1) % len(pts)][0], pts[(i + 1) % len(pts)][1])
               for i in range(len(pts)))


def fully_inside(x, y, pts, r):
    """circle of radius r entirely within the polygon"""
    return pt.in_poly(x, y, pts) and dist_to_edges(x, y, pts) >= r


def keepouts(path):
    """(vias not_allowed) keep-out outlines -- the antenna exclusion."""
    src = open(path, encoding="utf-8", errors="replace").read()
    out = []
    for b in pt.blocks(src, "zone"):
        if "keepout" not in b or "(vias not_allowed)" not in b:
            continue
        pts = [(float(a), float(c)) for a, c in
               __import__("re").findall(r"\(xy ([-\d.]+) ([-\d.]+)\)", b)]
        if len(pts) >= 3:
            out.append(pts)
    return out


def legal_elsewhere(vx, vy, pads, segs, vias, novia):
    """Everything the hole hits OUTSIDE the island it is being placed in."""
    r = VIA_D / 2.0
    lim = HALF - EDGE - r
    if abs(vx) > lim or abs(vy) > lim:
        return False
    ac = HALF - CORNER_R
    for sx in (-1, 1):
        for sy in (-1, 1):
            if vx * sx > ac and vy * sy > ac and \
                    math.hypot(vx - sx * ac, vy - sy * ac) > CORNER_R - EDGE - r:
                return False
    for pts in novia:                       # keep-out grown by the via radius
        if pt.in_poly(vx, vy, pts) or dist_to_edges(vx, vy, pts) < r:
            return False
    for p in pads:
        if p["ref"] in POGO_REFS:           # incl. J4.5, itself GND
            if math.hypot(vx - p["x"], vy - p["y"]) \
                    < max(p["w"], p["h"]) / 2 + r + CLR:
                return False
            continue
        if p["net"] == "GND":
            continue
        pw, ph = ((p["w"], p["h"]) if round(p["rot"]) % 180 == 0
                  else (p["h"], p["w"]))    # ROTATION APPLIED
        if abs(vx - p["x"]) < pw / 2 + r + CLR and \
                abs(vy - p["y"]) < ph / 2 + r + CLR:
            return False
    for s in segs:                          # every layer: a via pierces all
        if s["net"] == "GND":
            continue
        if pt.seg_dist(vx, vy, s["x1"], s["y1"], s["x2"], s["y2"]) \
                < s["w"] / 2 + r + CLR:
            return False
    for v in vias:
        if math.hypot(vx - v["x"], vy - v["y"]) < (v["d"] + VIA_D) / 2 + H2H:
            return False
    return True


def main():
    src, dst = sys.argv[1], sys.argv[2]
    fab_floor()
    pads, segs, vias, polys = pt.parse(src)
    novia = keepouts(src)
    r = VIA_D / 2.0

    gnd = [q for q in polys if q["net"] == "GND"]
    plane = [q for q in gnd if q["layer"] == "In2.Cu"]
    if not plane:
        sys.exit("no In2.Cu GND plane polygon -- nothing to land a via on")

    print("rules  : via %.2f/%.2f  clearance %.2f  step %.3f"
          % (VIA_D, VIA_DRILL, CLR, STEP))
    print("pour   : %d GND islands, %d on In2.Cu" % (len(gnd), len(plane)))

    # which islands hold pads but no via?
    need = []
    for i, q in enumerate(gnd):
        if q["layer"] == "In2.Cu":
            continue
        held = [p for p in pads if p["net"] == "GND"
                and q["layer"] in pt.pad_layers(p, ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"])
                and pt.pad_touches_poly(p, q)]
        has = any(v["net"] == "GND" and pt.in_poly(v["x"], v["y"], q["pts"])
                  for v in vias)
        if held and not has:
            need.append((i, q, held))

    print("islands holding pads but NO via : %d" % len(need))
    if not need:
        print("nothing to do")
        return 0

    placed = []
    for i, q, held in need:
        names = ", ".join(p["ref"] + "." + p["pad"] for p in held)
        xs = [p[0] for p in q["pts"]]
        ys = [p[1] for p in q["pts"]]
        print("\n  island %-3d %-7s area %6.3f mm2   holds %s"
              % (i, q["layer"], poly_area(q["pts"]), names))

        best = None
        x = min(xs)
        while x <= max(xs):
            y = min(ys)
            while y <= max(ys):
                if fully_inside(x, y, q["pts"], r) and \
                        any(pt.in_poly(x, y, pl["pts"]) for pl in plane) and \
                        legal_elsewhere(x, y, pads, segs, vias, novia):
                    # prefer the roomiest spot: furthest from the island edge
                    m = dist_to_edges(x, y, q["pts"])
                    if best is None or m > best[2]:
                        best = (x, y, m)
                y += STEP
            x += STEP

        if best is None:
            print("     NO legal via site inside this island.")
            print("     (island may be narrower than %.2f mm, or every spot"
                  % VIA_D)
            print("      collides on another layer)")
            continue
        vx, vy, m = best
        vias.append(dict(x=vx, y=vy, d=VIA_D, net="GND"))
        placed.append((vx, vy, names, m))
        print("     via at (%7.3f,%7.3f)  %.3f mm of copper all round"
              % (vx, vy, m))

    if not placed:
        print("\nnothing placed")
        return 1

    t = open(src, encoding="utf-8", errors="replace").read()
    nl = "\r\n" if "\r\n" in t else "\n"
    body = "".join(
        '\t(via (at %.4f %.4f) (size %s) (drill %s) (layers "F.Cu" "B.Cu") (net "GND"))%s'
        % (x, y, VIA_D, VIA_DRILL, nl) for x, y, _n, _m in placed)
    i = t.rstrip().rfind(")")
    open(dst, "w", encoding="utf-8", newline="").write(t[:i] + body + t[i:])
    print("\nplaced %d via(s) -> %s" % (len(placed), dst))
    print("NOW FILL ZONES IN KICAD, then re-run pour_truth.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
