"""
push_off_pads.py -- shove tracks that graze a foreign pad just far enough away.

WHY THIS KEEPS HAPPENING
------------------------
The router lays copper right on the clearance rule and, on this board, slightly
inside it against ROTATED 0402 pads: 0.0915 where 0.100 is required, over and
over, on different nets each re-route. The shortfalls are 1 to 9 microns. They
are real -- check_board measures the rotated rectangle correctly -- but they are
not a layout problem, they are the router shaving the rule.

Hand-nudging one segment at a time has been done twice now and it does not
scale. This does it by rule: find every track that is closer to a foreign pad
than the clearance, work out the shortest push that clears it, and move the
segment -- taking every coincident endpoint with it so nothing comes apart.

WHAT IT WILL NOT DO
-------------------
It refuses to move a segment whose push would take it inside something else.
Each candidate push is re-tested against every foreign pad, track and via
before it is accepted; if no push in the ladder is clean, the segment is left
alone and reported. A fix that trades one violation for another is not a fix,
which is the mistake the uniform edge-nudge made earlier this week.

Usage:  python push_off_pads.py IN.kicad_pcb OUT.kicad_pcb
"""
import math
import os
import re
import sys

import pour_truth as pt

HERE = os.path.dirname(os.path.abspath(__file__))
CLR = 0.10
MARGIN = 0.010          # aim this far past the rule, not exactly at it


def fab_floor():
    global CLR
    p = os.path.join(HERE, "fab_floor_touchid.txt")
    if not os.path.exists(p):
        return
    for line in open(p):
        if "=" in line and not line.strip().startswith("#"):
            k, v = [s.strip() for s in line.split("=", 1)]
            if k == "clearance":
                CLR = float(v)


def pad_dist(px, py, p):
    """TRUE distance to a pad: circles by radius, rectangles as ROTATED rects.
    A circumscribed circle over-reports and a bounding box under-reports; both
    have produced phantom verdicts on this board."""
    if p["shape"] == "circle":
        return math.hypot(px - p["x"], py - p["y"]) - p["w"] / 2.0
    a = math.radians(p["rot"])
    ca, sa = math.cos(a), math.sin(a)
    dx, dy = px - p["x"], py - p["y"]
    lx = dx * ca + dy * sa
    ly = -dx * sa + dy * ca
    return math.hypot(max(abs(lx) - p["w"] / 2.0, 0.0),
                      max(abs(ly) - p["h"] / 2.0, 0.0))


def seg_pad_gap(s, p):
    """closest approach of a segment's copper to a pad's copper"""
    best = 1e9
    n = max(2, int(math.dist((s["x1"], s["y1"]), (s["x2"], s["y2"])) / 0.01) + 1)
    for k in range(n + 1):
        f = k / n
        x = s["x1"] + f * (s["x2"] - s["x1"])
        y = s["y1"] + f * (s["y2"] - s["y1"])
        best = min(best, pad_dist(x, y, p) - s["w"] / 2.0)
    return best


def main():
    src, dst = sys.argv[1], sys.argv[2]
    fab_floor()
    pads, segs, vias, polys = pt.parse(src)

    def layers_of(p):
        return pt.pad_layers(p, ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"])

    def seg_ok(x1, y1, x2, y2, s):
        """the WHOLE segment against every foreign object on its layer"""
        probe = dict(s)
        probe.update(x1=x1, y1=y1, x2=x2, y2=y2)
        for p in pads:
            if p["net"] == s["net"] or s["layer"] not in layers_of(p):
                continue
            if seg_pad_gap(probe, p) < CLR:
                return False
        for o in segs:
            if o is s or o["net"] == s["net"] or o["layer"] != s["layer"]:
                continue
            for (ax, ay) in ((o["x1"], o["y1"]), (o["x2"], o["y2"])):
                if pt.seg_dist(ax, ay, x1, y1, x2, y2) < (o["w"] + s["w"]) / 2 + CLR:
                    return False
            for (ax, ay) in ((x1, y1), (x2, y2)):
                if pt.seg_dist(ax, ay, o["x1"], o["y1"], o["x2"], o["y2"]) \
                        < (o["w"] + s["w"]) / 2 + CLR:
                    return False
        for v in vias:
            if v["net"] == s["net"]:
                continue
            if pt.seg_dist(v["x"], v["y"], x1, y1, x2, y2) < v["d"] / 2 + s["w"] / 2 + CLR:
                return False
        return True

    def seg_via_gap(s, v):
        """closest approach of a segment's copper to a VIA's copper"""
        return (pt.seg_dist(v["x"], v["y"], s["x1"], s["y1"], s["x2"], s["y2"])
                - v["d"] / 2.0 - s["w"] / 2.0)

    moves = {}          # (x,y) -> (nx,ny)
    fixed = failed = 0
    for s in segs:
        worst = None
        for p in pads:
            if p["net"] == s["net"] or s["layer"] not in layers_of(p):
                continue
            g = seg_pad_gap(s, p)
            if g < CLR and (worst is None or g < worst[0]):
                worst = (g, p)
        # VIAS TOO. This checked pads only, and a via is not a pad -- so a
        # track grazing a foreign via was invisible here and survived every
        # run. gnd_taps left exactly that twice: a GND track 0.0853 mm from a
        # RESET via and 0.0920 mm from a SENSOR_WAKEUP via, against 0.100.
        # A via pierces every layer, so there is no layer test to do.
        for v in vias:
            if v["net"] == s["net"]:
                continue
            g = seg_via_gap(s, v)
            if g < CLR and (worst is None or g < worst[0]):
                worst = (g, dict(x=v["x"], y=v["y"], w=v["d"], h=v["d"],
                                 rot=0.0, shape="circle", net=v["net"],
                                 ref="via", pad=""))
        if worst is None:
            continue
        g, p = worst
        need = CLR - g + MARGIN
        # push perpendicular to the segment, away from the pad
        dx, dy = s["x2"] - s["x1"], s["y2"] - s["y1"]
        L = math.hypot(dx, dy)
        if L < 1e-9:
            continue
        nx, ny = -dy / L, dx / L
        mx, my = (s["x1"] + s["x2"]) / 2, (s["y1"] + s["y2"]) / 2
        if (mx - p["x"]) * nx + (my - p["y"]) * ny < 0:
            nx, ny = -nx, -ny
        done = False
        for mult in (1.0, 1.5, 2.0, 3.0, 4.0):
            d = need * mult
            a = (round(s["x1"] + nx * d, 4), round(s["y1"] + ny * d, 4))
            b = (round(s["x2"] + nx * d, 4), round(s["y2"] + ny * d, 4))
            if seg_ok(a[0], a[1], b[0], b[1], s):
                moves[(round(s["x1"], 4), round(s["y1"], 4))] = a
                moves[(round(s["x2"], 4), round(s["y2"], 4))] = b
                print("  %-13s @%-7s gap %.4f -> pushed %.3f mm off %s.%s"
                      % (s["net"], s["layer"], g, d, p["ref"], p["pad"]))
                fixed += 1
                done = True
                break
        if not done:
            print("  %-13s @%-7s gap %.4f off %s.%s -- NO clean push, left alone"
                  % (s["net"], s["layer"], g, p["ref"], p["pad"]))
            failed += 1

    if not moves:
        print("nothing to push")
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
            nx2, ny2 = moves[key]
            return "(%s %g %g)" % (m.group(1), nx2, ny2)
        return m.group(0)

    t = re.sub(r"\((start|end|at) ([-\d.]+) ([-\d.]+)\)", rep, t)
    if sum(1 for c in t if c == "(") != sum(1 for c in t if c == ")"):
        sys.exit("unbalanced -- refusing to write")
    open(dst, "w", encoding="utf-8",
         newline="\r\n" if crlf else "\n").write(t)
    print("\npushed %d segment(s), %d could not move; rewrote %d coordinates"
          % (fixed, failed, n))
    print("wrote %s" % dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
