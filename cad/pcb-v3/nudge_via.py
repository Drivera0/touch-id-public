"""
nudge_via.py -- move a VIA (and everything anchored on it) to a legal spot.

WHY THIS EXISTS
---------------
push_off_pads moves TRACKS off things. Nothing moved a VIA, and the router
leaves via violations this project cannot otherwise clear: it grades a track
against a via's DRILL rather than its ANNULUS, so it will happily lay copper
0.0901 mm from a 0.40 mm via against a 0.100 rule and call it routed. No
clearance setting fixes that -- passing 0.11 changed nothing -- and no net
ordering fixes it either; the pair comes out identical every run.

The via is usually the cheaper thing to move. It is one object, the space
around it is often free, and the tracks that end on it simply re-aim.

WHAT IT WILL NOT DO
-------------------
A via with tracks on it is a GROUP: move the via without its track ends and the
net comes apart; move the ends without the via and you get a dangling stub. So
every segment anchored on the via is re-aimed and RE-CHECKED against every
foreign pad, track and via before the move is accepted. If any of them cannot
be made legal, the via stays where it is and the file is not written. A fix
that trades one violation for another is not a fix -- push_off_pads learned
that the hard way, and did exactly that with a dragged via earlier today.

Usage:  python nudge_via.py IN.kicad_pcb OUT.kicad_pcb
"""
import math
import os
import re
import sys

import pour_truth as pt

HERE = os.path.dirname(os.path.abspath(__file__))
CLR = 0.10
VIA_D = 0.40
MARGIN = 0.005          # aim this far past the rule
MAX_MOVE = 1.20         # mm


def fab_floor():
    global CLR, VIA_D
    p = os.path.join(HERE, "fab_floor_touchid.txt")
    if not os.path.exists(p):
        return
    for line in open(p):
        line = line.split("#")[0]
        if "=" in line:
            k, v = [s.strip() for s in line.split("=", 1)]
            if k == "clearance":
                CLR = float(v)
            elif k == "via_diameter":
                VIA_D = float(v)


def pad_dist(px, py, p):
    """TRUE distance to a pad -- rotated rectangle, not a bounding box."""
    if p["shape"] == "circle":
        return math.hypot(px - p["x"], py - p["y"]) - p["w"] / 2.0
    a = math.radians(p["rot"])
    ca, sa = math.cos(a), math.sin(a)
    dx, dy = px - p["x"], py - p["y"]
    lx = dx * ca + dy * sa
    ly = -dx * sa + dy * ca
    return math.hypot(max(abs(lx) - p["w"] / 2.0, 0.0),
                      max(abs(ly) - p["h"] / 2.0, 0.0))


def main():
    src, dst = sys.argv[1], sys.argv[2]
    fab_floor()
    pads, segs, vias, _polys = pt.parse(src)

    def via_gap(v, s):
        return (pt.seg_dist(v["x"], v["y"], s["x1"], s["y1"], s["x2"], s["y2"])
                - v["d"] / 2.0 - s["w"] / 2.0)

    # ---- which vias are actually in violation? ----
    bad = []
    for v in vias:
        worst = None
        for s in segs:
            if s["net"] == v["net"]:
                continue
            g = via_gap(v, s)
            if g < CLR and (worst is None or g < worst):
                worst = g
        for o in vias:
            if o is v or o["net"] == v["net"]:
                continue
            g = math.hypot(v["x"] - o["x"], v["y"] - o["y"]) - v["d"] / 2 - o["d"] / 2
            if g < CLR and (worst is None or g < worst):
                worst = g
        for p in pads:
            if p["net"] == v["net"]:
                continue
            g = pad_dist(v["x"], v["y"], p) - v["d"] / 2
            if g < CLR and (worst is None or g < worst):
                worst = g
        if worst is not None:
            bad.append((worst, v))
    bad.sort(key=lambda q: q[0])

    print("rules: clearance %.3f  via %.2f" % (CLR, VIA_D))
    print("vias in violation: %d" % len(bad))
    if not bad:
        print("nothing to nudge")
        return 1

    def spot_ok(x, y, net, skip_via, moved_ends):
        """the via AND every segment that would follow it"""
        for p in pads:
            if p["net"] == net:
                continue
            if pad_dist(x, y, p) < VIA_D / 2 + CLR + MARGIN:
                return False
        for o in vias:
            if o is skip_via or o["net"] == net:
                continue
            if math.hypot(x - o["x"], y - o["y"]) < VIA_D / 2 + o["d"] / 2 + CLR + MARGIN:
                return False
        for s in segs:
            if s["net"] == net or s in moved_ends:
                continue
            if pt.seg_dist(x, y, s["x1"], s["y1"], s["x2"], s["y2"]) \
                    < s["w"] / 2 + VIA_D / 2 + CLR + MARGIN:
                return False
        # every anchored segment, re-aimed
        for s, tag in moved_ends:
            ox = s["x2"] if tag == "1" else s["x1"]
            oy = s["y2"] if tag == "1" else s["y1"]
            if abs(ox - x) < 1e-9 and abs(oy - y) < 1e-9:
                return False
            for p in pads:
                if p["net"] == s["net"]:
                    continue
                n = max(2, int(math.dist((x, y), (ox, oy)) / 0.02) + 1)
                for k in range(n + 1):
                    f = k / n
                    if pad_dist(x + f * (ox - x), y + f * (oy - y), p) \
                            < s["w"] / 2 + CLR:
                        return False
            for o in segs:
                if o is s or o["net"] == s["net"]:
                    continue
                if o["layer"] != s["layer"]:
                    continue
                for (ax, ay) in ((o["x1"], o["y1"]), (o["x2"], o["y2"])):
                    if pt.seg_dist(ax, ay, x, y, ox, oy) < (o["w"] + s["w"]) / 2 + CLR:
                        return False
            for o in vias:
                if o is skip_via or o["net"] == s["net"]:
                    continue
                if pt.seg_dist(o["x"], o["y"], x, y, ox, oy) \
                        < o["d"] / 2 + s["w"] / 2 + CLR:
                    return False
        return True

    moves = {}
    fixed = failed = 0
    for gap, v in bad:
        anchored = []
        for s in segs:
            for tag in ("1", "2"):
                if abs(s["x" + tag] - v["x"]) < 1e-6 and abs(s["y" + tag] - v["y"]) < 1e-6:
                    anchored.append((s, tag))
        best = None
        step = 0.01
        n = int(MAX_MOVE / step)
        for i in range(-n, n + 1):
            for k in range(-n, n + 1):
                x = round(v["x"] + i * step, 4)
                y = round(v["y"] + k * step, 4)
                d = math.hypot(x - v["x"], y - v["y"])
                if d < 1e-9 or d > MAX_MOVE:
                    continue
                if best is not None and d >= best[0]:
                    continue
                if spot_ok(x, y, v["net"], v, anchored):
                    best = (d, x, y)
        if best is None:
            print("  %-12s at (%7.3f,%7.3f) gap %+.4f -- NO legal spot within %.2f mm"
                  % (v["net"], v["x"], v["y"], gap, MAX_MOVE))
            failed += 1
            continue
        moves[(round(v["x"], 4), round(v["y"], 4))] = (best[1], best[2])
        print("  %-12s at (%7.3f,%7.3f) gap %+.4f -> (%7.3f,%7.3f)  moved %.3f mm, %d track end(s)"
              % (v["net"], v["x"], v["y"], gap, best[1], best[2], best[0], len(anchored)))
        fixed += 1

    if not moves:
        print("\nnothing moved")
        return 1

    raw = open(src, encoding="utf-8", errors="replace", newline="").read()
    crlf = "\r\n" in raw
    t = raw.replace("\r\n", "\n")
    n = 0

    def rep(m):
        nonlocal n
        key = (round(float(m.group(2)), 4), round(float(m.group(3)), 4))
        if key in moves:
            n += 1
            nx, ny = moves[key]
            return "(%s %g %g)" % (m.group(1), nx, ny)
        return m.group(0)

    t = re.sub(r"\((start|end|at) ([-\d.]+) ([-\d.]+)\)", rep, t)
    if sum(1 for c in t if c == "(") != sum(1 for c in t if c == ")"):
        sys.exit("unbalanced -- refusing to write")
    open(dst, "w", encoding="utf-8",
         newline="\r\n" if crlf else "\n").write(t)
    print("\nnudged %d via(s), %d could not move; rewrote %d coordinates"
          % (fixed, failed, n))
    print("wrote %s" % dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
