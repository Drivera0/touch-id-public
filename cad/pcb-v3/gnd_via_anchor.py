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
# READ THE FAB FLOOR. These were frozen at 0.45/0.20 and HALF 9.65 -- the via
# rung and the board this project had MONTHS ago. The board is 20.00 x 19.00
# and the fab floor has said via 0.40 since 2026-08-29.
#
# Both errors push the same way: a 0.45 via needs 0.025 mm more room per side
# than the 0.40 we actually buy, and in a tight pocket that is decisive. U5.4
# and R9.2 were reported as "NO legal site within 2.50 mm" while sites for a
# 0.40 via existed 1.485 and 1.381 mm away. It would also have PLACED 0.45
# vias on a board preflight check 8 grades at 0.40.
def _floor():
    v = {}
    _fp = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "fab_floor_touchid.txt")
    if os.path.exists(_fp):
        for _l in open(_fp):
            _l = _l.split("#")[0]
            if "=" in _l:
                _k, _val = [s.strip() for s in _l.split("=", 1)]
                try:
                    v[_k] = float(_val)
                except ValueError:
                    pass
    return v


_FL = _floor()
VIA_D = _FL.get("via_diameter", 0.40)
VIA_DRILL = _FL.get("via_drill", 0.20)
# The outline is NOT square any more. One HALF silently applied the X extent to
# Y as well; on 20.00 x 19.00 that is 0.35 mm wrong in one axis and 0.15 in the
# other, in opposite directions.
HALF_X, HALF_Y = 10.00, 9.50
HALF = min(HALF_X, HALF_Y)          # legacy name; prefer the axis
EDGE, CORNER_R = _FL.get("board_edge", 0.30), 2.00
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
    if abs(vx) > HALF_X - EDGE - r or abs(vy) > HALF_Y - EDGE - r:
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
    rmax = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
    t, pads, segs, vias, novia = load(src)
    gnd = [p for p in pads if p["net"] == "GND" and p["ref"] not in POGO_REFS]
    # pogo GND pads get an anchor too, just not one on top of them
    gnd += [p for p in pads if p["net"] == "GND" and p["ref"] in POGO_REFS]
    print("rules: via %.2f/%.2f  clearance %.2f  search radius %.2f" %
          (VIA_D, VIA_DRILL, CLR, rmax))
    print("GND pads: %d" % len(gnd))
    placed, already, nosite = [], 0, []
    # WHICH GND PADS ARE ACTUALLY CONNECTED, per the pour KiCad computed.
    #
    # This used to skip any pad with a via within rmax (2.50 mm) and call it
    # "already anchored". That is a PROXY for connected, and it is not the same
    # thing: a via 1.4 mm away touches nothing. U5.4 and R9.2 were skipped on
    # exactly that basis while sitting 2.30 and 2.78 mm from the nearest GND
    # copper, open, with legal via sites 1.4 mm away that this tool never tried.
    #
    # Ask the fill instead. Pads the pour genuinely reaches need nothing; pads
    # it does not reach are the whole job.
    _connected = set()
    try:
        import subprocess as _sp, sys as _sy, re as _re
        _out = _sp.run([_sy.executable, os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "pour_truth.py"), src],
            capture_output=True, text=True).stdout
        _blk = _re.search(r"^  OPEN  GND\b(.*?)(?=^  (?:OPEN|OK)\b|\Z)",
                          _out, _re.S | _re.M)
        _open_refs = set(_re.findall(r"^\s+(\S+)\s+at ", _blk.group(1), _re.M)) \
            if _blk else set()
        if "pads open against the pour" in _out:
            _connected = {"%s.%s" % (q["ref"], q["pad"]) for q in gnd} - _open_refs
    except Exception as _e:
        print("  [pour read failed: %s]" % _e)
        _connected = set()
    print("  pads the pour already reaches : %d" % len(_connected))

    for p in sorted(gnd, key=lambda q: (q["ref"], q["pad"])):
        _tag = "%s.%s" % (p["ref"], p["pad"])
        if _connected:
            if _tag in _connected:
                already += 1
                continue
        elif any(math.hypot(p["x"] - v[0], p["y"] - v[1]) <= rmax for v in vias):
            # fallback only when the pour could not be read (unfilled board)
            already += 1
            continue
        # CARTESIAN SCAN, NEAREST FIRST -- the polar one stepped over the answer.
        #
        # It swept radius in 0.05 increments and angle in 4 degree increments,
        # so at r = 1.5 consecutive probes are 0.10 mm apart and any legal
        # pocket smaller than that falls between them. It reported "NO legal
        # site within 2.50 mm" for U5.4 while THIS function accepts 292 sites
        # inside 3.0 mm, the nearest at 1.485 -- a radius the sweep never tried,
        # since it only ever tested exact multiples of 0.05.
        #
        # A grid at the router's own 0.02 pitch cannot skip a pocket that a
        # 0.40 via would fit in, and sorting by distance keeps the anchor as
        # close to the pad as it can be.
        found = None
        _step = 0.02
        _n = int(rmax / _step)
        _cands = []
        for _i in range(-_n, _n + 1):
            for _k in range(-_n, _n + 1):
                _vx = round(p["x"] + _i * _step, 4)
                _vy = round(p["y"] + _k * _step, 4)
                _d = math.hypot(_vx - p["x"], _vy - p["y"])
                if _d < max(0.30, VIA_D / 2 + CLR) or _d > rmax:
                    continue
                _cands.append((_d, _vx, _vy))
        for _d, _vx, _vy in sorted(_cands):
            if legal(_vx, _vy, pads, segs, vias, novia):
                found = (_vx, _vy, round(_d, 2))
                break
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
