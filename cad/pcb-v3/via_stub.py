"""
via_stub.py -- drop a via on a pad and run one stub to its own net.

WHY THIS EXISTS
---------------
Some pads cannot be reached by any of the automatic repairs, for a reason none
of them model: the pad is too small to leave sideways.

U2.7 is the case that forced it. A 0.24 x 0.60 QFN pin on 0.50 mm pitch has a
0.26 mm gap to its neighbours, and a 0.127 track needs 0.327 -- so no trace can
escape laterally at all. Its net lives on In1.Cu 1.075 mm straight down. The
only way out is a via ON the pad and a stub on the inner layer, which is what a
person draws in KiCad in about ten seconds.

close_open routes to the GND PLANE and will not target an inner-layer trace.
stitch_open routes pad-to-copper but starts from cells beside the pad, and here
there are none. Both correctly reported NO PATH; neither was wrong, they just
do not do this move.

WHAT IT CHECKS BEFORE WRITING
-----------------------------
Everything the other tools check, because a hand-route is exactly where a
mistake goes unnoticed:
  * the via clears every foreign pad, track and via on every layer
  * the via respects the pogo no-via rings and the pin-hole drill rule
  * the stub clears foreign copper ON ITS OWN LAYER along its whole length
  * the stub actually lands on existing copper of the target net
  * both nets are written in the dialect the file already uses
Refuses to write if any of these fails.

Usage:
  python via_stub.py IN.kicad_pcb OUT.kicad_pcb NET VX VY TX TY LAYER
"""
import math
import os
import re
import sys

import pour_truth as pt

HERE = os.path.dirname(os.path.abspath(__file__))
CLR, TRACK, VIA_D, VIA_DRILL = 0.10, 0.127, 0.40, 0.20
H2H, HTT, POGO_RING, MH_R, MH_PAD_H2H = 0.30, 0.20, 1.35, 0.60, 0.45
MH_XY = [(-8.75, 0.0), (8.75, 0.0)]


def floor():
    global CLR, TRACK, VIA_D, VIA_DRILL, H2H, HTT
    p = os.path.join(HERE, "fab_floor_touchid.txt")
    if not os.path.exists(p):
        return
    for line in open(p):
        line = line.split("#")[0]
        if "=" not in line:
            continue
        k, v = [s.strip() for s in line.split("=", 1)]
        try:
            v = float(v)
        except ValueError:
            continue
        if k == "clearance":
            CLR = v
        elif k == "track_width":
            TRACK = v
        elif k == "via_diameter":
            VIA_D = v
        elif k == "via_drill":
            VIA_DRILL = v
        elif k == "hole_to_hole":
            H2H = v
        elif k == "via_hole_to_track":
            HTT = v


def pad_dist(px, py, p):
    if p["shape"] == "circle":
        return math.hypot(px - p["x"], py - p["y"]) - p["w"] / 2.0
    a = math.radians(p["rot"])
    ca, sa = math.cos(a), math.sin(a)
    dx, dy = px - p["x"], py - p["y"]
    lx, ly = dx * ca + dy * sa, -dx * sa + dy * ca
    return math.hypot(max(abs(lx) - p["w"] / 2, 0.0),
                      max(abs(ly) - p["h"] / 2, 0.0))


def main():
    src, dst, net = sys.argv[1], sys.argv[2], sys.argv[3]
    vx, vy, tx, ty = [float(q) for q in sys.argv[4:8]]
    layer = sys.argv[8]
    floor()
    pads, segs, vias, _poly = pt.parse(src)
    fail = []

    # ---- the via, against every layer ----
    halo = max(VIA_D / 2 + CLR, VIA_DRILL / 2 + HTT)
    for p in pads:
        if p["net"] == net or not p["ref"]:
            continue
        if pad_dist(vx, vy, p) < VIA_D / 2 + CLR:
            fail.append("via too close to pad %s.%s" % (p["ref"], p["pad"]))
    for s in segs:
        if s["net"] == net:
            continue
        if pt.seg_dist(vx, vy, s["x1"], s["y1"], s["x2"], s["y2"]) \
                < s["w"] / 2 + halo:
            fail.append("via too close to a %s track on %s" % (s["net"], s["layer"]))
    for v in vias:
        if math.hypot(vx - v["x"], vy - v["y"]) < VIA_DRILL / 2 + v["d"] / 2 + H2H:
            fail.append("via drill too close to another via")
    for p in pads:
        if p["ref"] in ("J4", "J11") and math.hypot(vx - p["x"], vy - p["y"]) < POGO_RING:
            fail.append("via inside %s.%s's pogo ring" % (p["ref"], p["pad"]))
    for hx, hy in MH_XY:
        if math.hypot(vx - hx, vy - hy) - MH_R - VIA_DRILL / 2 < MH_PAD_H2H:
            fail.append("via breaks the pin-hole drill rule")

    # ---- the stub, on its own layer, along its whole length ----
    n = max(2, int(math.dist((vx, vy), (tx, ty)) / 0.02))
    for i in range(n + 1):
        f = i / n
        x, y = vx + f * (tx - vx), vy + f * (ty - vy)
        for s in segs:
            if s["net"] == net or s["layer"] != layer:
                continue
            if pt.seg_dist(x, y, s["x1"], s["y1"], s["x2"], s["y2"]) \
                    < s["w"] / 2 + TRACK / 2 + CLR:
                fail.append("stub grazes a %s track on %s" % (s["net"], layer))
                break
        for p in pads:
            if p["net"] == net or not p["ref"]:
                continue
            if layer not in pt.pad_layers(p, ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]) \
                    and not p["through"]:
                continue
            if pad_dist(x, y, p) < TRACK / 2 + CLR:
                fail.append("stub grazes pad %s.%s" % (p["ref"], p["pad"]))
                break

    # ---- does the stub actually LAND on this net? ----
    landed = any(s["net"] == net and s["layer"] == layer and
                 pt.seg_dist(tx, ty, s["x1"], s["y1"], s["x2"], s["y2"])
                 <= s["w"] / 2 + TRACK / 2 + 1e-6 for s in segs)
    if not landed:
        fail.append("stub end does not touch existing %s copper on %s" % (net, layer))

    if fail:
        print("REFUSING TO WRITE:")
        for f_ in sorted(set(fail)):
            print("   " + f_)
        return 1

    raw = open(src, encoding="utf-8", errors="replace", newline="").read()
    crlf = "\r\n" in raw
    t = raw.replace("\r\n", "\n")
    m = re.search(r'\(net (\d+) "%s"\)' % re.escape(net), t)
    nid = m.group(1) if m else ('"%s"' % net)
    if not m and '(net "%s")' % net not in t:
        sys.exit("net %r not found in the board -- refusing to guess" % net)

    body = ('\t(via\n\t\t(at %g %g)\n\t\t(size %s)\n\t\t(drill %s)\n'
            '\t\t(layers "F.Cu" "B.Cu")\n\t\t(net %s)\n\t)\n'
            % (vx, vy, VIA_D, VIA_DRILL, nid))
    body += ('\t(segment\n\t\t(start %g %g)\n\t\t(end %g %g)\n\t\t(width %s)\n'
             '\t\t(layer "%s")\n\t\t(net %s)\n\t)\n'
             % (vx, vy, tx, ty, TRACK, layer, nid))
    i = t.rstrip().rfind(")")
    t = t[:i] + body + t[i:]
    if sum(1 for c in t if c == "(") != sum(1 for c in t if c == ")"):
        sys.exit("unbalanced -- refusing to write")
    open(dst, "w", encoding="utf-8", newline="\r\n" if crlf else "\n").write(t)
    print("via at (%g, %g) + %.3f mm stub on %s -> %s"
          % (vx, vy, math.dist((vx, vy), (tx, ty)), layer, net))
    print("wrote %s" % dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
