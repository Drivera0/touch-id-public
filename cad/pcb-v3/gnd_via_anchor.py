"""
gnd_via_anchor.py — give every GND pad its own via down to the plane.

WHY THIS EXISTS, AND WHY IT IS NOT gnd_taps.py
----------------------------------------------
gnd_taps routes a TRACK from a stranded GND pad to a legal via site. That is a
PATH problem, and paths are where this board bites: my own hand-placed taps put
two vias through J4.5's pogo contact and shorted GND to SENSOR_MCU_3V3, and
stitch_open has twice reported "ROUTED" for connections it did not make.

This does something strictly weaker and far safer: it places a VIA ONLY, with
no track at all, near each GND pad, and lets the copper pour do the connecting.
A via has no path to get wrong. The only question is whether the hole is legal,
and that is a point test.

It works because of a measured result: a single via at (-9.10,-3.95), 2.57 mm
from J4.5 and on the far side of a VBAT_SENSE segment, connected J4.5 on the
next fill. The pour reaches around obstacles; it just needs somewhere to reach
DOWN to the In2.Cu plane.

WHY EVERY PAD AND NOT JUST THE OPEN ONES
----------------------------------------
Each re-fill reshapes the pour: fixing C5/C12/U3 stranded C7.2 and U5.4
instead. Anchoring only the currently-open pads chases a moving target. Anchor
them all and the reshuffling has nothing left to strand.

THE LEGALITY PREDICATE IS THE WHOLE POINT
-----------------------------------------
Every trap this board produced in one day, in one function:

  * J4/J11 pogo rings -- INCLUDING J4.5, which is itself GND. The rule is that
    the hole ruins a keyboard contact, not that the copper is a different net,
    so "skip same-net pads" is wrong here and put two vias through a contact.
  * the antenna keep-out GROWN BY THE VIA RADIUS. A keep-out applies to the
    copper, not the centre point: 13 vias centred outside it still reached in.
  * non-GND pads WITH ROTATION APPLIED. Twelve 0402s here sit at rot 90, where
    w and h swap; ignoring that hid a real 0.0915 mm violation.
  * tracks on ALL FOUR LAYERS. A through-hole via pierces every one, so F.Cu
    and In1.Cu traffic blocks a hole even when the pad is on B.Cu.
  * hole-to-hole against existing AND newly placed vias.
  * the R2.0 corner arcs, not just the square bounding box.

Usage:  python gnd_via_anchor.py IN.kicad_pcb OUT.kicad_pcb [max_radius_mm]
Then FILL ZONES IN KICAD and re-run preflight -- nothing here connects anything
until the pour is regenerated.
"""
import json, math, os, re, sys

import sexp

HERE = os.path.dirname(os.path.abspath(__file__))
VIA_D, VIA_DRILL = 0.45, 0.20
HALF, EDGE, CORNER_R = 9.65, 0.30, 2.00
H2H = 0.20
POGO_REFS = ("J4", "J11")


def _rules():
    """clearance from the fab floor -- never hard-coded."""
    cl = 0.10
    p = os.path.join(HERE, "fab_floor_touchid.txt")
    if os.path.exists(p):
        for line in open(p):
            if "=" in line and not line.strip().startswith("#"):
                k, v = [s.strip() for s in line.split("=", 1)]
                if k == "clearance":
                    cl = float(v)
                elif k == "via_diameter":
                    globals()["VIA_D"] = float(v)
                elif k == "via_drill":
                    globals()["VIA_DRILL"] = float(v)
    return cl


CLR = _rules()


def _blocks(src, tag):
    for m in re.finditer(r"\(" + tag + r"[\s\n]", src):
        i = m.start(); d = 0; j = i
        while True:
            if src[j] == "(":
                d += 1
            elif src[j] == ")":
                d -= 1
                if d == 0:
                    break
            j += 1
        yield src[i:j + 1]


def load(path):
    t = open(path, encoding="utf-8", errors="replace").read()
    pads = sexp.pads(t)
    segs = []
    for m in re.finditer(
            r'\(segment[\s\S]{0,200}?\(start ([-\d.]+) ([-\d.]+)\)'
            r'[\s\S]{0,60}?\(end ([-\d.]+) ([-\d.]+)\)'
            r'[\s\S]{0,80}?\(width ([\d.]+)\)'
            r'[\s\S]{0,60}?\(layer "([^"]+)"\)'
            r'[\s\S]{0,80}?\(net "?([^")]*)"?\)', t):
        segs.append(tuple(map(float, m.groups()[:5])) + (m.group(6), m.group(7)))
    vias = [[float(m.group(1)), float(m.group(2)), float(m.group(3))]
            for m in re.finditer(r'\(via[\s\S]{0,200}?\(at ([-\d.]+) ([-\d.]+)\)'
                                 r'[\s\S]{0,120}?\(size ([\d.]+)\)', t)]
    novia = []
    for b in _blocks(t, "zone"):
        if "keepout" not in b or "(vias not_allowed)" not in b:
            continue
        pts = [(float(a), float(c))
               for a, c in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', b)]
        if len(pts) >= 3:
            novia.append(pts)
    return t, pads, segs, vias, novia


def _in_poly(x, y, pts):
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]; xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-30) + xi:
            inside = not inside
        j = i
    return inside


def legal(vx, vy, pads, segs, vias, novia):
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
    # keep-out grown by the via radius: the COPPER must stay out, not the centre
    for pts in novia:
        if _in_poly(vx, vy, pts):
            return False
        for i in range(len(pts)):
            ax, ay = pts[i]; bx, by = pts[(i + 1) % len(pts)]
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            t = 0 if L2 == 0 else max(0, min(1, ((vx - ax) * dx + (vy - ay) * dy) / L2))
            if math.hypot(vx - (ax + t * dx), vy - (ay + t * dy)) < r:
                return False
    for p in pads:
        if p["ref"] in POGO_REFS:          # incl. J4.5, which is itself GND
            if math.hypot(vx - p["x"], vy - p["y"]) < max(p["w"], p["h"]) / 2 + r + CLR:
                return False
            continue
        if p["net"] == "GND":
            continue
        pw, ph = ((p["w"], p["h"]) if round(p["rot"]) % 180 == 0
                  else (p["h"], p["w"]))          # ROTATION APPLIED
        if abs(vx - p["x"]) < pw / 2 + r + CLR and abs(vy - p["y"]) < ph / 2 + r + CLR:
            return False
    for (x1, y1, x2, y2, w, lay, net) in segs:    # every layer: a via pierces all
        if net == "GND":
            continue
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0, min(1, ((vx - x1) * dx + (vy - y1) * dy) / L2))
        if math.hypot(vx - (x1 + t * dx), vy - (y1 + t * dy)) < w / 2 + r + CLR:
            return False
    for (ox, oy, od) in vias:
        if math.hypot(vx - ox, vy - oy) < (od + VIA_D) / 2 + H2H:
            return False
    return True


def main():
    src, dst = sys.argv[1], sys.argv[2]
    rmax = float(sys.argv[3]) if len(sys.argv) > 3 else 2.5
    t, pads, segs, vias, novia = load(src)
    gnd = [p for p in pads if p["net"] == "GND" and p["ref"] not in POGO_REFS]
    # pogo GND pads get an anchor too, just not one on top of them
    gnd += [p for p in pads if p["net"] == "GND" and p["ref"] in POGO_REFS]
    print("rules: via %.2f/%.2f  clearance %.2f  search radius %.2f" %
          (VIA_D, VIA_DRILL, CLR, rmax))
    print("GND pads: %d" % len(gnd))
    placed, already, nosite = [], 0, []
    for p in sorted(gnd, key=lambda q: (q["ref"], q["pad"])):
        # already anchored?
        if any(math.hypot(p["x"] - v[0], p["y"] - v[1]) <= rmax for v in vias):
            already += 1
            continue
        found = None
        r = max(0.30, VIA_D / 2 + CLR)
        while r <= rmax and not found:
            for a in range(0, 360, 4):
                vx = p["x"] + r * math.cos(math.radians(a))
                vy = p["y"] + r * math.sin(math.radians(a))
                if legal(vx, vy, pads, segs, vias, novia):
                    found = (round(vx, 4), round(vy, 4), round(r, 2))
                    break
            r += 0.05
        if found:
            vias.append([found[0], found[1], VIA_D])
            placed.append((p["ref"] + "." + p["pad"], found))
        else:
            nosite.append(p["ref"] + "." + p["pad"])
    body = "".join(
        '\t(via (at %.4f %.4f) (size %s) (drill %s) (layers "F.Cu" "B.Cu") (net "GND"))\n'
        % (f[0], f[1], VIA_D, VIA_DRILL) for _k, f in placed)
    i = t.rstrip().rfind(")")
    open(dst, "w", encoding="utf-8").write(t[:i] + body + t[i:])
    print("  already within %.2f mm of a via : %d" % (rmax, already))
    print("  anchor vias placed             : %d" % len(placed))
    for k, f in placed:
        print("     %-8s -> (%7.3f,%7.3f)  %.2f mm" % (k, f[0], f[1], f[2]))
    if nosite:
        print("  NO legal site within %.2f mm   : %d  %s"
              % (rmax, len(nosite), ", ".join(nosite)))
    print("wrote %s" % dst)
    print("NOW FILL ZONES IN KICAD -- nothing here connects until the pour is redone.")


if __name__ == "__main__":
    main()
