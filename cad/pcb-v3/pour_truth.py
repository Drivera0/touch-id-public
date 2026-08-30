"""
pour_truth.py -- connectivity judged against the pour KiCad ACTUALLY COMPUTED.

WHY THIS EXISTS
---------------
check_connected.py does not read the fill geometry in the board file. It builds
a MODEL of where fill could go (plane_fill_model) and credits a zone only where
the model says copper can provably exist. That is the right instinct for an
unfilled board, but it is a prediction, and this project has been burned by
predictions all week: check_drc ignored pad rotation, stitch_open reported
ROUTED for connections it never made, gnd_taps modelled a square board that has
R2.0 corners. Every one of those was a checker being wrong about the board.

KiCad has already answered this question. When the user fills zones, KiCad
writes the resulting copper into the file as (filled_polygon ...) -- the real
outcome of the real fill algorithm, islands removed, thermals applied. That is
ground truth, and it is sitting in the file unread.

So this reads the polygons and asks the only question that matters for a pour-
connected pad: DOES THIS PAD SIT IN COPPER THAT REACHES THE REST OF THE NET?

HOW IT JOINS THINGS
-------------------
Union-find over four kinds of node -- pads, vias, track segments, and each
filled polygon -- joined only by geometric contact on a shared layer:

  * a via spans F.Cu..B.Cu, so it touches every layer's copper at its site;
    this is what lets a pad on F.Cu reach the In2.Cu plane.
  * a pad is IN a polygon if any of its centre, corners, or edge midpoints
    falls inside, or if a polygon edge crosses the pad rectangle. Corner-only
    contact is real contact: a thermal spoke lands exactly there.
  * pad rotation is applied. Twelve 0402s here sit at rot 90 where w and h
    swap, and ignoring that hid a real 0.0915 mm violation once already.
  * polygons of the same net on the same layer are NOT joined to each other.
    If KiCad emitted them as separate islands they are separate copper, and
    pretending otherwise would reintroduce exactly the optimism being checked.

WHAT A FAILURE HERE MEANS
-------------------------
A pad this reports as open is open on the board as KiCad filled it. There is no
further pour to hope for. A pad check_connected reports and this does not was
stranded by the model, not by the copper.

Usage:  python pour_truth.py BOARD.kicad_pcb [NET ...]
"""
import math
import re
import sys


# ---------------------------------------------------------------- parsing


def blocks(src, tag):
    """Yield each balanced (tag ...) block. Paren-counting, not regex: zone
    bodies contain thousands of nested pts and no regex survives them."""
    for m in re.finditer(r"\(" + tag + r"[\s\n]", src):
        i = m.start()
        d = 0
        j = i
        while True:
            c = src[j]
            if c == '"':                       # skip strings; nets have parens
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
        yield src[i:j + 1]


def _f(s):
    return float(s)


def parse(path):
    t = open(path, encoding="utf-8", errors="replace").read()

    # ---- pads (need the footprint transform: pads are in local coords)
    pads = []
    for fb in blocks(t, "footprint"):
        m = re.search(r"\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", fb)
        if not m:
            continue
        fx, fy, frot = _f(m.group(1)), _f(m.group(2)), _f(m.group(3) or 0)
        ref = "?"
        r = re.search(r'\(property "Reference" "([^"]*)"', fb)
        if r:
            ref = r.group(1)
        for pb in blocks(fb, "pad"):
            pm = re.match(r'\(pad "([^"]*)"\s+(\S+)\s+(\S+)', pb)
            if not pm:
                continue
            num, ptype, pshape = pm.group(1), pm.group(2), pm.group(3)
            am = re.search(r"\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", pb)
            sm = re.search(r"\(size ([\d.]+) ([\d.]+)\)", pb)
            if not am or not sm:
                continue
            px, py, prot = _f(am.group(1)), _f(am.group(2)), _f(am.group(3) or 0)
            w, h = _f(sm.group(1)), _f(sm.group(2))
            a = math.radians(frot)
            # KiCad footprint rotation is CLOCKWISE in this Y-down space.
            gx = fx + px * math.cos(a) + py * math.sin(a)
            gy = fy - px * math.sin(a) + py * math.cos(a)
            grot = frot + prot
            nm = re.search(r'\(net (?:\d+ )?"([^"]*)"\)', pb)
            net = nm.group(1) if nm else ""
            lm = re.search(r"\(layers ([^)]*)\)", pb)
            lays = re.findall(r'"?([\w.*]+)"?', lm.group(1)) if lm else []
            through = ptype in ("thru_hole", "np_thru_hole")
            pads.append(dict(ref=ref, pad=num, x=gx, y=gy, w=w, h=h,
                             rot=grot, net=net, layers=lays, through=through,
                             shape=pshape))

    # ---- segments / arcs
    segs = []
    for b in blocks(t, "segment"):
        s = re.search(r"\(start ([-\d.]+) ([-\d.]+)\)", b)
        e = re.search(r"\(end ([-\d.]+) ([-\d.]+)\)", b)
        w = re.search(r"\(width ([\d.]+)\)", b)
        l = re.search(r'\(layer "([^"]+)"\)', b)
        n = re.search(r'\(net (?:\d+ )?"?([^")]*)"?\)', b)
        if s and e and w and l:
            segs.append(dict(x1=_f(s.group(1)), y1=_f(s.group(2)),
                             x2=_f(e.group(1)), y2=_f(e.group(2)),
                             w=_f(w.group(1)), layer=l.group(1),
                             net=(n.group(1) if n else "")))

    # ---- vias
    vias = []
    for b in blocks(t, "via"):
        a = re.search(r"\(at ([-\d.]+) ([-\d.]+)\)", b)
        s = re.search(r"\(size ([\d.]+)\)", b)
        n = re.search(r'\(net (?:\d+ )?"?([^")]*)"?\)', b)
        if a and s:
            vias.append(dict(x=_f(a.group(1)), y=_f(a.group(2)),
                             d=_f(s.group(1)), net=(n.group(1) if n else "")))

    # ---- the pour KiCad actually computed
    polys = []
    for zb in blocks(t, "zone"):
        if "keepout" in zb:
            continue
        # KiCad 10 writes the zone net INLINE as (net "GND"). KiCad 8 wrote
        # (net 2) plus (net_name "GND"). Accept both -- looking only for
        # net_name silently gave every polygon a blank net, no pad matched any
        # pour, and this reported 34 opens against a board with 8. A parser
        # that fails soft is worse than one that crashes.
        n = (re.search(r'\(net_name "([^"]*)"\)', zb)
             or re.search(r'\(net (?:\d+ )?"([^"]*)"\)', zb))
        znet = n.group(1) if n else ""
        if not znet:
            raise SystemExit(
                "zone with no readable net -- refusing to report connectivity "
                "from a half-parsed pour. Header was:\n" + zb[:200])
        zl = re.search(r'\(layer "([^"]+)"\)', zb)
        zlay = zl.group(1) if zl else None
        for fb in blocks(zb, "filled_polygon"):
            fl = re.search(r'\(layer "([^"]+)"\)', fb)
            lay = fl.group(1) if fl else zlay
            pts = [(_f(a), _f(b2))
                   for a, b2 in re.findall(r"\(xy ([-\d.]+) ([-\d.]+)\)", fb)]
            if len(pts) >= 3 and lay:
                polys.append(dict(net=znet, layer=lay, pts=pts))
    return pads, segs, vias, polys


# ---------------------------------------------------------------- geometry


def in_poly(x, y, pts):
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y):
            if x < (xj - xi) * (y - yi) / (yj - yi + 1e-30) + xi:
                inside = not inside
        j = i
    return inside


def seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def pad_pts(p):
    """Centre, corners and edge midpoints, rotation applied. Corner contact is
    real contact -- a thermal spoke lands exactly on one."""
    w, h = p["w"], p["h"]
    a = math.radians(p["rot"])
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for lx, ly in ((0, 0),
                   (-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2),
                   (0, -h / 2), (0, h / 2), (-w / 2, 0), (w / 2, 0)):
        out.append((p["x"] + lx * ca + ly * sa, p["y"] - lx * sa + ly * ca))
    return out


def pad_r(p):
    return math.hypot(p["w"], p["h"]) / 2.0


def pad_touches_poly(p, poly):
    for (x, y) in pad_pts(p):
        if in_poly(x, y, poly["pts"]):
            return True
    # a polygon edge slicing across the pad without any test point inside
    cx, cy, r = p["x"], p["y"], pad_r(p)
    pts = poly["pts"]
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        if seg_dist(cx, cy, x1, y1, x2, y2) <= r:
            return True
    return False


def pad_layers(p, all_cu):
    if p["through"] or any(l == "*.Cu" for l in p["layers"]):
        return set(all_cu)
    return {l for l in p["layers"] if l.endswith(".Cu")}


# ---------------------------------------------------------------- union-find


class UF:
    def __init__(self):
        self.p = {}

    def add(self, k):
        self.p.setdefault(k, k)

    def find(self, k):
        while self.p[k] != k:
            self.p[k] = self.p[self.p[k]]
            k = self.p[k]
        return k

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


TOUCH = 1e-4          # copper either meets or it does not; no grace band


def analyse(pads, segs, vias, polys, nets=None):
    all_cu = sorted({s["layer"] for s in segs} |
                    {p["layer"] for p in polys} |
                    {"F.Cu", "In1.Cu", "In2.Cu", "B.Cu"})
    # EVERY net with two or more pads -- NOT only nets that already have
    # copper. Intersecting with "nets that have copper" meant a net whose
    # copper had just been ripped up vanished from the report entirely, and a
    # completely UNROUTED net read as zero open pads. That is the same class of
    # silent under-reporting this file exists to replace.
    _cnt = {}
    for p in pads:
        if p["net"]:
            _cnt[p["net"]] = _cnt.get(p["net"], 0) + 1
    live = sorted(n for n, c in _cnt.items() if c >= 2)
    if nets:
        live = [n for n in live if n in nets]

    report = {}
    for net in live:
        np_ = [p for p in pads if p["net"] == net]
        ns = [s for s in segs if s["net"] == net]
        nv = [v for v in vias if v["net"] == net]
        nz = [q for q in polys if q["net"] == net]
        if len(np_) < 2:
            continue
        if not ns and not nv and not nz:
            # no copper at all: every pad is its own island
            report[net] = dict(pads=np_, polys=[], groups=len(np_),
                               stray=np_[1:], main_segs=[], main_vias=[])
            continue

        uf = UF()
        for i, _ in enumerate(np_):
            uf.add(("P", i))
        for i, _ in enumerate(ns):
            uf.add(("S", i))
        for i, _ in enumerate(nv):
            uf.add(("V", i))
        for i, _ in enumerate(nz):
            uf.add(("Z", i))

        # --- segment to segment (same layer, endpoints meet)
        for i in range(len(ns)):
            for j in range(i + 1, len(ns)):
                a, b = ns[i], ns[j]
                if a["layer"] != b["layer"]:
                    continue
                tol = (a["w"] + b["w"]) / 2 + TOUCH
                if (seg_dist(a["x1"], a["y1"], b["x1"], b["y1"], b["x2"], b["y2"]) <= tol or
                        seg_dist(a["x2"], a["y2"], b["x1"], b["y1"], b["x2"], b["y2"]) <= tol or
                        seg_dist(b["x1"], b["y1"], a["x1"], a["y1"], a["x2"], a["y2"]) <= tol or
                        seg_dist(b["x2"], b["y2"], a["x1"], a["y1"], a["x2"], a["y2"]) <= tol):
                    uf.union(("S", i), ("S", j))

        # --- pads
        for i, p in enumerate(np_):
            pl = pad_layers(p, all_cu)
            r = pad_r(p)
            for j, s in enumerate(ns):
                if s["layer"] not in pl:
                    continue
                if min(seg_dist(p["x"], p["y"], s["x1"], s["y1"], s["x2"], s["y2"]),
                       0 if any(abs(px - s["x1"]) < r and abs(py - s["y1"]) < r
                                for px, py in pad_pts(p)) else 9e9) <= r + s["w"] / 2 + TOUCH:
                    uf.union(("P", i), ("S", j))
            for j, v in enumerate(nv):
                if math.hypot(p["x"] - v["x"], p["y"] - v["y"]) <= r + v["d"] / 2 + TOUCH:
                    uf.union(("P", i), ("V", j))
            for j, q in enumerate(nz):
                if q["layer"] in pl and pad_touches_poly(p, q):
                    uf.union(("P", i), ("Z", j))

        # --- vias: a through via touches every layer at its site
        for i, v in enumerate(nv):
            for j, s in enumerate(ns):
                if seg_dist(v["x"], v["y"], s["x1"], s["y1"], s["x2"], s["y2"]) \
                        <= v["d"] / 2 + s["w"] / 2 + TOUCH:
                    uf.union(("V", i), ("S", j))
            for j, q in enumerate(nz):
                if in_poly(v["x"], v["y"], q["pts"]):
                    uf.union(("V", i), ("Z", j))
                    continue
                pts = q["pts"]
                for k in range(len(pts)):
                    x1, y1 = pts[k]
                    x2, y2 = pts[(k + 1) % len(pts)]
                    if seg_dist(v["x"], v["y"], x1, y1, x2, y2) <= v["d"] / 2 + TOUCH:
                        uf.union(("V", i), ("Z", j))
                        break
            for j in range(i + 1, len(nv)):
                w = nv[j]
                if math.hypot(v["x"] - w["x"], v["y"] - w["y"]) \
                        <= (v["d"] + w["d"]) / 2 + TOUCH:
                    uf.union(("V", i), ("V", j))

        # --- segments sitting in the pour (a track ending in the plane)
        for i, s in enumerate(ns):
            for j, q in enumerate(nz):
                if q["layer"] != s["layer"]:
                    continue
                if in_poly(s["x1"], s["y1"], q["pts"]) or \
                        in_poly(s["x2"], s["y2"], q["pts"]):
                    uf.union(("S", i), ("Z", j))

        groups = {}
        for i in range(len(np_)):
            groups.setdefault(uf.find(("P", i)), []).append(i)
        big = max(groups.values(), key=len) if groups else []
        stray = [np_[i] for g in groups.values() if g is not big for i in g]
        # Which SEGMENTS and VIAS belong to the main group. Anything routing at
        # stranded copper is aiming at a piece that is itself disconnected --
        # it will report success and leave the pad open. Callers need to be
        # able to tell the two apart.
        root = uf.find(("P", big[0])) if big else None
        main_segs = [ns[i] for i in range(len(ns))
                     if root is not None and uf.find(("S", i)) == root]
        main_vias = [nv[i] for i in range(len(nv))
                     if root is not None and uf.find(("V", i)) == root]
        report[net] = dict(pads=np_, polys=nz, groups=len(groups), stray=stray,
                           main_segs=main_segs, main_vias=main_vias)
    return report


def main():
    path = sys.argv[1]
    want = sys.argv[2:] or None
    pads, segs, vias, polys = parse(path)
    print("board  : %s" % path)
    print("parsed : %d pads  %d segments  %d vias  %d FILLED polygons"
          % (len(pads), len(segs), len(vias), len(polys)))
    if not polys:
        print("\n!! NO filled_polygon geometry in this file.")
        print("   Fill zones in KiCad first -- otherwise every pour-connected")
        print("   pad will read as open and the verdict is meaningless.")
        return 2
    by = {}
    for q in polys:
        by.setdefault((q["net"], q["layer"]), 0)
        by[(q["net"], q["layer"])] += 1
    for (n, l), c in sorted(by.items()):
        print("         pour %-14s %-8s %d island(s)" % (n, l, c))

    rep = analyse(pads, segs, vias, polys, want)
    print()
    bad = 0
    for net in sorted(rep):
        r = rep[net]
        if r["groups"] == 1:
            print("  OK    %-16s %2d pads, one piece" % (net, len(r["pads"])))
        else:
            bad += len(r["stray"])
            print("  OPEN  %-16s %2d pads in %d pieces"
                  % (net, len(r["pads"]), r["groups"]))
            for p in r["stray"]:
                print("          %-8s at (%7.3f,%7.3f)  layers %s"
                      % (p["ref"] + "." + p["pad"], p["x"], p["y"],
                         ",".join(p["layers"])))
    print()
    print("=" * 66)
    print("  pads open against the pour KiCad actually computed : %d" % bad)
    print("=" * 66)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
