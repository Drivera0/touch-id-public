"""
check_escape.py -- can every pad actually GET OUT?

The autorouter's verdict on pcb-v3 was, over and over:
   "the start/target pads are boxed in by static obstacles
    (neighboring pads + clearance), not by congestion"

That is a PLACEMENT defect, and no routing setting can fix it. This script
tests for it directly, before routing.

CRITERION. A pad escapes if a track of width TRACK, keeping CLR from all
foreign copper, can leave the pad and reach a legal VIA SITE. Once a net
reaches a via it can go anywhere on In1.Cu, which is empty. So "can reach a
via" is very nearly "is routable".

A via site must clear foreign copper on EVERY layer (it is a through hole):
F.Cu pads, B.Cu pogo pads, and the keep-out rule areas.
"""
import re, sys, math
from shapely.geometry import box, Point, LineString, Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity

PCB   = sys.argv[1] if len(sys.argv) > 1 else "pcb-v3.kicad_pcb"
TRACK = 0.20     # signal track width
CLR   = 0.20     # our design clearance
VIA   = 0.60     # via pad diameter
BOARD = 19.30
EDGE  = 0.30     # copper to board edge

t = open(PCB).read()
_NETNAMES = dict(re.findall(r'\(net (\d+) "([^"]*)"\)', t))
t = re.sub(r'\(net (\d+)\)',
           lambda m: '(net %s "%s")' % (m.group(1), _NETNAMES.get(m.group(1), "")), t)

def blocks(tag):
    out, i = [], 0
    while True:
        i = t.find('\t(%s' % tag, i)
        if i < 0: return out
        d, j = 0, i
        while True:
            if t[j] == '(': d += 1
            elif t[j] == ')':
                d -= 1
                if d == 0: break
            j += 1
        out.append(t[i:j+1]); i = j

def rot(px, py, a):
    r = math.radians(a); c, s = math.cos(r), math.sin(r)
    return px*c - py*s, px*s + py*c

def pad_shape(shape, x, y, w, h, rratio, angle):
    if shape == 'circle':
        g = Point(x, y).buffer(w/2, 32)
    elif shape == 'oval':
        r = min(w, h)/2
        g = (LineString([(x-(w/2-r), y), (x+(w/2-r), y)]).buffer(r, 32) if w >= h
             else LineString([(x, y-(h/2-r)), (x, y+(h/2-r))]).buffer(r, 32))
    elif shape == 'roundrect':
        r = (rratio or 0.25)*min(w, h)
        g = box(x-w/2+r, y-h/2+r, x+w/2-r, y+h/2-r).buffer(r, 16)
    else:
        g = box(x-w/2, y-h/2, x+w/2, y+h/2)
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
        x, y = fx+dx, fy+dy
        rr = re.search(r'\(roundrect_rratio ([\d.]+)\)', tail)
        net = re.search(r'\(net (?:\d+ )?"([^"]*)"\)', tail)
        lay = re.search(r'\(layers ([^)]*)\)', tail)
        layers = lay.group(1).replace('"','').split() if lay else []
        pads.append(dict(ref=ref, num=nm, x=x, y=y,
                         net=net.group(1) if net else "",
                         layers=layers,
                         g=pad_shape(shape, x, y, float(w), float(h),
                                     float(rr.group(1)) if rr else None,
                                     (float(pa or 0) + fa) % 360)))

# keep-out rule areas
keepouts = []
for z in blocks('zone'):
    if 'keepout' not in z: continue
    for poly in re.finditer(r'\(polygon\s*\(pts(.*?)\)\s*\)', z, re.S):
        pts = [(float(a), float(b)) for a, b in
               re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', poly.group(1))]
        if len(pts) >= 3:
            keepouts.append(Polygon(pts))
keepouts = unary_union(keepouts) if keepouts else Polygon()

fcu = [p for p in pads if 'F.Cu' in p['layers']]
bcu = [p for p in pads if 'B.Cu' in p['layers']]
board = box(-BOARD/2, -BOARD/2, BOARD/2, BOARD/2)
inner = board.buffer(-(EDGE + TRACK/2))

print("pads: %d   F.Cu: %d   B.Cu: %d   keepout area: %.2f mm2"
      % (len(pads), len(fcu), len(bcu), keepouts.area))

# ---- via sites: clear of ALL layers' foreign copper -------------------------
def via_sites_for(net):
    blk = [p['g'].buffer(CLR + VIA/2) for p in pads
           if p['net'] != net and (set(p['layers']) & {'F.Cu','B.Cu','In1.Cu','In2.Cu','*.Cu'} or '*.Cu' in p['layers'])]
    free = board.buffer(-(EDGE + VIA/2))
    if blk: free = free.difference(unary_union(blk))
    if not keepouts.is_empty: free = free.difference(keepouts.buffer(VIA/2))
    return free

# ---- F.Cu free space for a track centre line of one net --------------------
def track_free_for(net):
    blk = [p['g'].buffer(CLR + TRACK/2) for p in fcu if p['net'] != net]
    free = inner
    if blk: free = free.difference(unary_union(blk))
    if not keepouts.is_empty: free = free.difference(keepouts.buffer(TRACK/2))
    return free

def parts(g):
    if g.is_empty: return []
    return list(g.geoms) if isinstance(g, MultiPolygon) else [g]

nets = sorted({p['net'] for p in fcu if p['net'] and p['net'] != 'GND'})
boxed, ok = [], 0
cache_t, cache_v = {}, {}
for net in nets:
    cache_t[net] = track_free_for(net)
    cache_v[net] = via_sites_for(net)

for p in fcu:
    net = p['net']
    if not net or net == 'GND':
        continue
    tf, vs = cache_t[net], cache_v[net]
    # region of F.Cu free space touching this pad
    reach = [r for r in parts(tf) if r.intersects(p['g'].buffer(0.001))]
    if not reach:
        boxed.append((p, 'no track can leave the pad at all', 0.0)); continue
    reg = unary_union(reach)
    hit = reg.intersection(vs)
    if hit.is_empty:
        boxed.append((p, 'can leave, but reaches no legal via site', reg.area))
    else:
        ok += 1

print("\nescapable pads      : %d" % ok)
print("BOXED-IN pads       : %d" % len(boxed))
if boxed:
    print("\n%-8s %-16s %9s %9s   %s" % ("PAD","NET","X","Y","WHY"))
    for p, why, a in sorted(boxed, key=lambda z: (z[0]['ref'], z[0]['num'])):
        print("%-8s %-16s %9.3f %9.3f   %s"
              % (p['ref']+'.'+p['num'], p['net'], p['x'], p['y'], why))
