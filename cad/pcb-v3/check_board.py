# Geometry checker for pcb-v2.kicad_pcb
#
# Reads the board as text and measures real copper-to-copper clearance between
# objects on different nets.
#
# IMPORTANT: pad SHAPE matters. An earlier version of this script modelled every
# pad as a rectangle, which inflates a circular pad's outline by up to 0.207*d
# at the corners (0.46 mm on a 2.2 mm pogo pad) and produced eight false
# "violations" on pads I had never touched. Always honour the shape token.
#
# Run: python check_board.py [board.kicad_pcb]

import re, sys, math
from shapely.geometry import box, Point, LineString
from shapely import affinity

PCB = sys.argv[1] if len(sys.argv) > 1 else "pcb-v2.kicad_pcb"
MIN_CU = 0.127          # JLCPCB minimum copper to copper

t = open(PCB).read()
# --- 2026-08-20: the board now uses KiCad's real net schema ---
# Top level declares (net <n> "NAME"); pads carry (net <n> "NAME") but tracks
# and vias carry only (net <n>). Expand the bare ordinals back to names here so
# every regex below keeps working unchanged.
_NETNAMES = dict(__import__("re").findall(r'\(net (\d+) "([^"]*)"\)', t))
t = __import__("re").sub(r'\(net (\d+)\)',
                         lambda _m: '(net %s "%s")' % (_m.group(1), _NETNAMES.get(_m.group(1), "")),
                         t)


# ---------------------------------------------------------------- footprints
def blocks(tag):
    out, i = [], 0
    while True:
        i = t.find('\t(%s' % tag, i)
        if i < 0:
            return out
        d, j = 0, i
        while True:
            if t[j] == '(': d += 1
            elif t[j] == ')':
                d -= 1
                if d == 0: break
            j += 1
        out.append(t[i:j + 1]); i = j

def rot(px, py, a):
    """Footprint-local -> board coordinates.

    KiCad's file format is Y-DOWN, so a POSITIVE footprint angle is
    mathematically CLOCKWISE. Using the textbook CCW matrix here mirrored every
    rotated footprint's pads in Y -- which swapped pad 1 and pad 2 on all 21
    rotated 0402s and made check_board report 79 phantom SHORTs on a board the
    router and its own DRC both call clean. Verified against R6 (at 1.5,-7.9,
    rot 90): the router lands BL_RETURN at y -7.40, which is pad 1 only under
    this sign.
    """
    r = math.radians(a); c, s = math.cos(r), math.sin(r)
    return px * c + py * s, -px * s + py * c

def pad_shape(shape, x, y, w, h, rratio, angle):
    """Copper outline of one pad, honouring its shape."""
    if shape == 'circle':
        g = Point(x, y).buffer(w / 2, 64)
    elif shape == 'oval':
        r = min(w, h) / 2
        g = LineString([(x - (w/2 - r), y), (x + (w/2 - r), y)]).buffer(r, 64) \
            if w >= h else \
            LineString([(x, y - (h/2 - r)), (x, y + (h/2 - r))]).buffer(r, 64)
    elif shape == 'roundrect':
        r = (rratio or 0.25) * min(w, h)
        g = box(x - w/2 + r, y - h/2 + r, x + w/2 - r, y + h/2 - r).buffer(r, 32)
    else:                                   # rect, custom (approximated)
        g = box(x - w/2, y - h/2, x + w/2, y + h/2)
    return affinity.rotate(g, angle, origin=(x, y)) if angle else g

pads = []
for fp in blocks('footprint "'):
    ref = re.search(r'\(property "Reference" "([^"]*)"', fp)
    ref = ref.group(1) if ref else '?'
    m = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', fp)
    fx, fy, fa = float(m.group(1)), float(m.group(2)), float(m.group(3) or 0)
    for pm in re.finditer(
            r'\(pad "([^"]*)" (\w+) (\w+)\s*\n\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)'
            r'\s*\n\s*\(size ([\d.]+) ([\d.]+)\)(.*?)\n\t\t\)', fp, re.S):
        nm, ptype, shape, px, py, pa, w, h, tail = pm.groups()
        dx, dy = rot(float(px), float(py), fa)
        x, y = fx + dx, fy + dy
        rr = re.search(r'\(roundrect_rratio ([\d.]+)\)', tail)
        net = re.search(r'\(net (?:\d+ )?"([^"]*)"\)', tail)
        pads.append(dict(
            ref=ref, nm=nm, shape=shape, net=net.group(1) if net else None,
            g=pad_shape(shape, x, y, float(w), float(h),
                        float(rr.group(1)) if rr else None, float(pa or 0) + fa),
            F='F.Cu' in tail, B='B.Cu' in tail, x=x, y=y))

# ------------------------------------------------------------------- copper
trk = []
for m in re.finditer(
        r'\(segment\s*\n\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\n\s*\(end ([-\d.]+) ([-\d.]+)\)'
        r'\s*\n\s*\(width ([\d.]+)\)\s*\n\s*\(layer "([^"]+)"\)\s*\n\s*\(net (?:\d+ )?"([^"]*)"\)', t):
    sx, sy, ex, ey, w, lay, net = m.groups()
    trk.append(dict(g=LineString([(float(sx), float(sy)), (float(ex), float(ey))])
                    .buffer(float(w) / 2, cap_style=2, resolution=16),
                    lay=lay, net=net, s=(float(sx), float(sy)), e=(float(ex), float(ey))))

vias = []
for m in re.finditer(r'\(via\s*\n\s*\(at ([-\d.]+) ([-\d.]+)\)\s*\n\s*\(size ([\d.]+)\)'
                     r'\s*\n\s*\(drill ([\d.]+)\)\s*\n\s*\(layers "([^"]+)" "([^"]+)"\)'
                     r'(.*?)\n\t\)', t, re.S):
    x, y, s, d, l1, l2, tail = m.groups()
    net = re.search(r'\(net (?:\d+ )?"([^"]*)"\)', tail)
    vias.append(dict(g=Point(float(x), float(y)).buffer(float(s) / 2, 64),
                     net=net.group(1) if net else None, F=True, B=True))

print(f"{PCB}")
print(f"  pads {len(pads)}   tracks {len(trk)}   vias {len(vias)}")
shp = {}
for p in pads: shp[p['shape']] = shp.get(p['shape'], 0) + 1
print(f"  pad shapes: {shp}")

viol = []
for lay, key in (("F.Cu", 'F'), ("B.Cu", 'B')):
    objs = [(p['net'], p['g'], f"pad {p['ref']}:{p['nm']}") for p in pads if p[key]]
    objs += [(v['net'], v['g'], "via") for v in vias]
    objs += [(s['net'], s['g'], f"track {s['s']}->{s['e']}") for s in trk if s['lay'] == lay]
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            na, ga, la = objs[i]; nb, gb, lb = objs[j]
            if na is not None and nb is not None and na == nb:
                continue
            d = ga.distance(gb)
            if d < MIN_CU:
                viol.append((d, lay, na, la, nb, lb))

print(f"\n  different-net pairs closer than {MIN_CU} mm: {len(viol)}")
for d, lay, na, la, nb, lb in sorted(viol, key=lambda v: (v[0], str(v[1]), str(v[2]), str(v[3]), str(v[4]), str(v[5]))):
    tag = "SHORT" if d <= 0.0 else "tight"
    print(f"    {tag}  {lay}  {d:.4f}  [{na}] {la}  <->  [{nb}] {lb}")
sys.exit(1 if viol else 0)
