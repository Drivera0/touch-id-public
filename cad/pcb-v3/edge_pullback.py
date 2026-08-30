"""
edge_pullback.py -- pull copper back inside a board edge that has MOVED IN.

WHY THIS EXISTS
---------------
Shrinking the board in Y left 10 copper items outside the 0.30 mm edge rule.
The obvious fix -- shove everything below a threshold up to a common line -- was
tried and produced 19 clearance violations and 22 DRC errors, because a uniform
move drags copper into whatever happens to be sitting above it. The correct
move is per-item and minimal, and it has to be CHECKED, not assumed.

WHAT IT ACTUALLY MOVES
----------------------
A via and every track endpoint sitting on that via are ONE object. Move the via
without its endpoints and the net comes apart; move the endpoints without the
via and you get a dangling stub. So coincident points are grouped and move
together, and a group is only accepted if EVERY member is legal afterwards.

A track endpoint is not a point for checking purposes either -- moving it
re-aims the whole segment. Each candidate position therefore re-tests the
FULL segment against foreign copper, not just the endpoint.

SEARCH ORDER
------------
Minimal first: straight inward by exactly the amount needed, then progressively
further and sideways. The first legal position wins, so copper moves as little
as possible and existing routing is disturbed as little as possible.

Usage:  python edge_pullback.py IN.kicad_pcb OUT.kicad_pcb
"""
import math
import os
import re
import sys

import pour_truth as pt

HERE = os.path.dirname(os.path.abspath(__file__))
HALF_X, HALF_Y = 10.00, 9.50
EDGE, CORNER_R, H2H = 0.30, 2.00, 0.25
CLR, VIA_D, VIA_DRILL, HOLE_TO_TRACK = 0.10, 0.40, 0.20, 0.20


def fab_floor():
    global CLR, VIA_D, VIA_DRILL, HOLE_TO_TRACK, EDGE
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
            elif k == "via_hole_to_track":
                HOLE_TO_TRACK = float(v)
            elif k == "board_edge":
                EDGE = float(v)


def via_halo(d):
    """copper rule or drill rule, whichever binds"""
    return max(d / 2.0 + CLR, VIA_DRILL / 2.0 + HOLE_TO_TRACK)


def inside_edge(x, y, r):
    if abs(x) > HALF_X - EDGE - r or abs(y) > HALF_Y - EDGE - r:
        return False
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * (HALF_X - CORNER_R), sy * (HALF_Y - CORNER_R)
            if x * sx > cx * sx and y * sy > cy * sy:
                if math.hypot(x - cx, y - cy) > CORNER_R - EDGE - r:
                    return False
    return True


def spans(src, tag):
    out = []
    for m in re.finditer(r"\(" + tag + r"[\s\n]", src):
        i = m.start()
        d = 0
        j = i
        while True:
            c = src[j]
            if c == '"':
                j += 1
                while src[j] != '"':
                    j += 2 if src[j] == "\\" else 1
            elif c == "(":
                d += 1
            elif c == ")":
                d -= 1
                if d == 0:
                    break
            j += 1
        out.append((i, j + 1))
    return out


def main():
    src, dst = sys.argv[1], sys.argv[2]
    fab_floor()
    pads, segs, vias, polys = pt.parse(src)

    def seg_clear(x1, y1, x2, y2, w, layer, net):
        """the WHOLE segment against foreign copper on its own layer"""
        for p in pads:
            if p["net"] == net:
                continue
            if layer not in pt.pad_layers(p, ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]):
                continue
            pw, ph = ((p["w"], p["h"]) if round(p["rot"]) % 180 == 0
                      else (p["h"], p["w"]))
            rr = math.hypot(pw, ph) / 2
            if pt.seg_dist(p["x"], p["y"], x1, y1, x2, y2) < rr + w / 2 + CLR:
                return False
        for s in segs:
            if s["net"] == net or s["layer"] != layer:
                continue
            for (ax, ay) in ((s["x1"], s["y1"]), (s["x2"], s["y2"])):
                if pt.seg_dist(ax, ay, x1, y1, x2, y2) < s["w"] / 2 + w / 2 + CLR:
                    return False
            for (ax, ay) in ((x1, y1), (x2, y2)):
                if pt.seg_dist(ax, ay, s["x1"], s["y1"], s["x2"], s["y2"]) \
                        < s["w"] / 2 + w / 2 + CLR:
                    return False
        for v in vias:
            if v["net"] == net:
                continue
            if pt.seg_dist(v["x"], v["y"], x1, y1, x2, y2) < via_halo(v["d"]) + w / 2:
                return False
        return True

    def via_clear(x, y, d, net, skip):
        if not inside_edge(x, y, d / 2):
            return False
        halo = via_halo(d)
        for p in pads:
            if p["net"] == net:
                continue
            pw, ph = ((p["w"], p["h"]) if round(p["rot"]) % 180 == 0
                      else (p["h"], p["w"]))
            if abs(x - p["x"]) < pw / 2 + halo and abs(y - p["y"]) < ph / 2 + halo:
                return False
        for s in segs:
            if s["net"] == net:
                continue
            if pt.seg_dist(x, y, s["x1"], s["y1"], s["x2"], s["y2"]) < s["w"] / 2 + halo:
                return False
        for v in vias:
            if v is skip:
                continue
            if math.hypot(x - v["x"], y - v["y"]) < (VIA_DRILL + VIA_DRILL) / 2 + H2H:
                return False
        return True

    # ---- collect every point that breaches, grouped by coincidence
    groups = {}
    for v in vias:
        if not inside_edge(v["x"], v["y"], v["d"] / 2):
            groups.setdefault((round(v["x"], 4), round(v["y"], 4)),
                              {"vias": [], "ends": []})["vias"].append(v)
    for s in segs:
        for tag in ("1", "2"):
            x, y = s["x" + tag], s["y" + tag]
            if not inside_edge(x, y, s["w"] / 2):
                groups.setdefault((round(x, 4), round(y, 4)),
                                  {"vias": [], "ends": []})["ends"].append((s, tag))
    # a track endpoint that lands on a breaching via joins that via's group
    for key, g in list(groups.items()):
        for s in segs:
            for tag in ("1", "2"):
                k = (round(s["x" + tag], 4), round(s["y" + tag], 4))
                if k == key and (s, tag) not in g["ends"]:
                    g["ends"].append((s, tag))

    print("rules: clearance %.2f  via %.2f/%.2f  edge %.2f  hole-to-track %.2f"
          % (CLR, VIA_D, VIA_DRILL, EDGE, HOLE_TO_TRACK))
    print("breaching point groups: %d" % len(groups))

    moves = {}
    for (gx, gy), g in sorted(groups.items()):
        need = 0.0
        for v in g["vias"]:
            need = max(need, abs(gy) + v["d"] / 2 - (HALF_Y - EDGE))
        for (s, tag) in g["ends"]:
            need = max(need, abs(gy) + s["w"] / 2 - (HALF_Y - EDGE))
        sgn = -1.0 if gy > 0 else 1.0
        found = None
        step = 0.025
        for k in range(0, 81):                       # up to 2.0 mm inward
            dy = need + k * step
            for dx in (0.0, 0.05, -0.05, 0.10, -0.10, 0.20, -0.20,
                       0.35, -0.35, 0.50, -0.50):
                nx, ny = gx + dx, gy + sgn * dy
                ok = True
                for v in g["vias"]:
                    if not via_clear(nx, ny, v["d"], v["net"], v):
                        ok = False
                        break
                if ok:
                    for (s, tag) in g["ends"]:
                        ox = s["x2"] if tag == "1" else s["x1"]
                        oy = s["y2"] if tag == "1" else s["y1"]
                        if abs(ox - nx) < 1e-9 and abs(oy - ny) < 1e-9:
                            ok = False
                            break
                        if not seg_clear(nx, ny, ox, oy, s["w"], s["layer"], s["net"]):
                            ok = False
                            break
                if ok:
                    found = (nx, ny)
                    break
            if found:
                break
        if not found:
            print("  (%7.3f,%7.3f) NO legal position within 2 mm" % (gx, gy))
            continue
        moves[(gx, gy)] = found
        print("  (%7.3f,%7.3f) -> (%7.3f,%7.3f)   moved %.3f mm   %d via(s), %d end(s)"
              % (gx, gy, found[0], found[1],
                 math.hypot(found[0] - gx, found[1] - gy),
                 len(g["vias"]), len(g["ends"])))

    if not moves:
        print("nothing moved")
        return 1

    # ---- rewrite coordinates by span, never by str.replace
    raw = open(src, encoding="utf-8", errors="replace", newline="").read()
    crlf = "\r\n" in raw
    t = raw.replace("\r\n", "\n")
    edits = []
    for tag in ("segment", "via"):
        for (a, b) in spans(t, tag):
            blk = t[a:b]
            for m in re.finditer(r"\((start|end|at) ([-\d.]+) ([-\d.]+)\)", blk):
                key = (round(float(m.group(2)), 4), round(float(m.group(3)), 4))
                if key in moves:
                    nx, ny = moves[key]
                    edits.append((a + m.start(2), a + m.end(2), "%g" % round(nx, 4)))
                    edits.append((a + m.start(3), a + m.end(3), "%g" % round(ny, 4)))
    for s, e, txt in sorted(edits, reverse=True):
        t = t[:s] + txt + t[e:]
    d = 0
    for c in t:
        if c == "(":
            d += 1
        elif c == ")":
            d -= 1
    if d != 0:
        sys.exit("unbalanced after edit -- refusing to write")
    open(dst, "w", encoding="utf-8",
         newline="\r\n" if crlf else "\n").write(t)
    print("rewrote %d coordinates -> %s" % (len(edits), dst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
