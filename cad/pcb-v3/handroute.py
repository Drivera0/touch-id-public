"""
handroute.py — route ONE net at a time, deliberately, and verify.

The batch router converged at 11 open pads. Each of the three dead nets routes
fine alone, so the failure is ordering/congestion, not geometry. This does what
a person does in the interactive router: pick a net, find a path through what is
actually free, lay it, keep it.

Grid A* over F.Cu / In1.Cu / B.Cu at 0.05 mm. Obstacles are rasterised from the
real board: foreign pads, foreign tracks, foreign vias, and the keep-out rule
areas HONOURED PER LAYER (the In2.Cu plane guard bans tracks on In2.Cu only,
and In2.Cu is not a routing layer here anyway).

Usage:  python handroute.py NET [NET ...]
"""
import heapq, math, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "pcb-v3-handoff.kicad_pcb")
STEP = 0.05
TRACK, CLR, VIA_D, VIA_DRILL = 0.20, 0.20, 0.60, 0.30
BOARD_SZ, EDGE = 19.30, 0.30
LAYERS = ["F.Cu", "In1.Cu", "B.Cu"]
VIA_COST = 40          # in grid steps
N = int(round(BOARD_SZ / STEP)) + 1
ORG = -BOARD_SZ / 2.0

def g2mm(i):  return round(ORG + i * STEP, 4)
def mm2g(v):  return int(round((v - ORG) / STEP))

t = open(BOARD, encoding="utf-8", errors="replace").read()
nn = dict(re.findall(r'\(net (\d+) "([^"]*)"\)', t))
name2id = {v: k for k, v in nn.items()}

def rot(px, py, a):
    r = math.radians(a); c, s = math.cos(r), math.sin(r)
    return px * c + py * s, -px * s + py * c      # KiCad Y-down: +angle is CW

# ---------------------------------------------------------------- geometry --
pads = []      # (net, layers set, cx, cy, w, h, shape)
for fm in re.finditer(r'\(footprint "touchid:([^"]+)"(.*?)\n\t\)', t, re.S):
    blk = fm.group(2)
    at = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', blk)
    fx, fy, fa = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
    for pm in re.finditer(r'\(pad "([^"]+)" \w+ (\w+)(.*?)\n\t\t\)', blk, re.S):
        pb = pm.group(3)
        a_ = re.search(r'\(at ([-\d.]+) ([-\d.]+)\)', pb)
        s_ = re.search(r'\(size ([\d.]+) ([\d.]+)\)', pb)
        l_ = re.search(r'\(layers ([^)]*)\)', pb)
        n_ = re.search(r'\(net \d+ "([^"]*)"\)', pb)
        if not (a_ and s_):
            continue
        dx, dy = rot(float(a_.group(1)), float(a_.group(2)), fa)
        lays = set((l_.group(1).replace('"', '').split()) if l_ else [])
        if "*.Cu" in lays:
            lays |= set(LAYERS) | {"In2.Cu"}
        pads.append(dict(net=n_.group(1) if n_ else "", layers=lays,
                         x=fx + dx, y=fy + dy,
                         w=float(s_.group(1)), h=float(s_.group(2)),
                         shape=pm.group(2), ref=fm.group(1), num=pm.group(1)))

tracks = []
for m in re.finditer(r'\(segment\b(.*?)\n\t\)', t, re.S):
    b = m.group(1)
    s_ = re.search(r'\(start ([-\d.]+) ([-\d.]+)\)', b)
    e_ = re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', b)
    w_ = re.search(r'\(width ([\d.]+)\)', b)
    l_ = re.search(r'\(layer "([^"]+)"\)', b)
    n_ = re.search(r'\(net (\d+)\)', b)
    if s_ and e_ and w_ and l_:
        tracks.append(dict(net=nn.get(n_.group(1), "") if n_ else "",
                           x1=float(s_.group(1)), y1=float(s_.group(2)),
                           x2=float(e_.group(1)), y2=float(e_.group(2)),
                           w=float(w_.group(1)), layer=l_.group(1)))
vias = []
for m in re.finditer(r'\(via\b(.*?)\n\t\)', t, re.S):
    b = m.group(1)
    a_ = re.search(r'\(at ([-\d.]+) ([-\d.]+)\)', b)
    s_ = re.search(r'\(size ([\d.]+)\)', b)
    n_ = re.search(r'\(net (\d+)\)', b)
    if a_ and s_:
        vias.append(dict(net=nn.get(n_.group(1), "") if n_ else "",
                         x=float(a_.group(1)), y=float(a_.group(2)),
                         d=float(s_.group(1))))

keepouts = []   # (layers set, kind, params, bans_tracks, bans_vias)
for z in re.finditer(r'\(zone(.*?)\n\t\)', t, re.S):
    zb = z.group(1)
    if "keepout" not in zb:
        continue
    l_ = re.search(r'\(layers? ([^)]*)\)', zb)
    lays = set((l_.group(1).replace('"', '').split()) if l_ else [])
    pts = [(float(a), float(b)) for a, b in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', zb)]
    if pts:
        keepouts.append(dict(layers=lays, pts=np.array(pts),
                             no_tracks="(tracks not_allowed)" in zb,
                             no_vias="(vias not_allowed)" in zb))

XX, YY = np.meshgrid(np.array([g2mm(i) for i in range(N)]),
                     np.array([g2mm(i) for i in range(N)]), indexing="xy")

def poly_mask(pts):
    """even-odd fill for a convex/simple polygon on the grid"""
    inside = np.zeros((N, N), bool)
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]; xj, yj = pts[j]
        cond = ((yi > YY) != (yj > YY))
        with np.errstate(divide="ignore", invalid="ignore"):
            xint = (xj - xi) * (YY - yi) / (yj - yi + 1e-30) + xi
        inside ^= cond & (XX < xint)
        j = i
    return inside

def blocked_masks(net, halo):
    """per-layer boolean: may the CENTRE of a feature sit here?"""
    m = {L: np.zeros((N, N), bool) for L in LAYERS}
    for p in pads:
        if p["net"] == net:
            continue
        for L in LAYERS:
            if L not in p["layers"]:
                continue
            if p["shape"] == "circle":
                m[L] |= ((XX - p["x"])**2 + (YY - p["y"])**2) <= (p["w"]/2 + halo)**2
            else:
                m[L] |= (np.abs(XX - p["x"]) <= p["w"]/2 + halo) & \
                        (np.abs(YY - p["y"]) <= p["h"]/2 + halo)
    for s in tracks:
        if s["net"] == net:
            continue
        dx, dy = s["x2"] - s["x1"], s["y2"] - s["y1"]
        L2 = dx*dx + dy*dy
        tt = np.zeros((N, N)) if L2 == 0 else np.clip(
            ((XX - s["x1"]) * dx + (YY - s["y1"]) * dy) / L2, 0, 1)
        d2 = (XX - (s["x1"] + tt*dx))**2 + (YY - (s["y1"] + tt*dy))**2
        m[s["layer"]] |= d2 <= (s["w"]/2 + halo)**2
    for v in vias:
        if v["net"] == net:
            continue
        hit = ((XX - v["x"])**2 + (YY - v["y"])**2) <= (v["d"]/2 + halo)**2
        for L in LAYERS:
            m[L] |= hit
    for k in keepouts:
        if not k["no_tracks"]:
            continue
        pm = poly_mask(k["pts"])
        for L in LAYERS:
            if L in k["layers"]:
                m[L] |= pm
    edge = (np.abs(XX) > BOARD_SZ/2 - EDGE - TRACK/2) | \
           (np.abs(YY) > BOARD_SZ/2 - EDGE - TRACK/2)
    for L in LAYERS:
        m[L] |= edge
    return m

# ------------------------------------------------------------------- A* -----
DIRS = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]

def pad_cells(p, L):
    """grid cells inside this pad on layer L (a track centre may start here)"""
    if L not in p["layers"]:
        return []
    i0, i1 = mm2g(p["x"] - p["w"]/2), mm2g(p["x"] + p["w"]/2)
    j0, j1 = mm2g(p["y"] - p["h"]/2), mm2g(p["y"] + p["h"]/2)
    out = []
    for j in range(max(j0,0), min(j1,N-1)+1):
        for i in range(max(i0,0), min(i1,N-1)+1):
            if p["shape"] == "circle":
                if (g2mm(i)-p["x"])**2 + (g2mm(j)-p["y"])**2 > (p["w"]/2)**2:
                    continue
            out.append((i, j))
    return out

def route(net, verbose=True):
    tmask = blocked_masks(net, CLR + TRACK/2)
    vmask = blocked_masks(net, CLR + VIA_D/2)
    via_ok = ~(vmask["F.Cu"] | vmask["In1.Cu"] | vmask["B.Cu"])
    for k in keepouts:                       # a via pierces every layer
        if k["no_vias"]:
            via_ok &= ~poly_mask(k["pts"])

    mine = [p for p in pads if p["net"] == net]
    if len(mine) < 2:
        return None, "net has <2 pads"

    # grow the connected set one pad at a time (MST-ish, nearest first)
    placed = [mine[0]]
    todo = mine[1:]
    laid = []            # (layer_idx, [(i,j)...]) polylines
    via_pts = []
    src_cells = set()
    for L in LAYERS:
        for c in pad_cells(mine[0], L):
            src_cells.add((LAYERS.index(L), c[0], c[1]))

    while todo:
        todo.sort(key=lambda p: min(math.dist((p["x"],p["y"]),(q["x"],q["y"])) for q in placed))
        tgt = todo[0]
        goal = set()
        for L in LAYERS:
            for c in pad_cells(tgt, L):
                goal.add((LAYERS.index(L), c[0], c[1]))
        if not goal or not src_cells:
            return None, "pad %s.%s has no free cell" % (tgt["ref"], tgt["num"])
        gi = np.mean([c[1] for c in goal]); gj = np.mean([c[2] for c in goal])
        def h(s):
            return math.hypot(s[1]-gi, s[2]-gj)
        openq = [(h(s), 0, s) for s in src_cells]
        heapq.heapify(openq)
        best = {s: 0 for s in src_cells}
        came = {}
        found = None
        while openq:
            f, g, cur = heapq.heappop(openq)
            if cur in goal:
                found = cur; break
            if g > best.get(cur, 1e18):
                continue
            l, i, j = cur
            for dx, dy in DIRS:
                ni, nj = i+dx, j+dy
                if not (0 <= ni < N and 0 <= nj < N):
                    continue
                if tmask[LAYERS[l]][nj, ni]:
                    continue
                ng = g + (1.414 if dx and dy else 1.0)
                s2 = (l, ni, nj)
                if ng < best.get(s2, 1e18):
                    best[s2] = ng; came[s2] = cur
                    heapq.heappush(openq, (ng + h(s2), ng, s2))
            if via_ok[j, i]:
                for l2 in range(len(LAYERS)):
                    if l2 == l or tmask[LAYERS[l2]][j, i]:
                        continue
                    ng = g + VIA_COST
                    s2 = (l2, i, j)
                    if ng < best.get(s2, 1e18):
                        best[s2] = ng; came[s2] = cur
                        heapq.heappush(openq, (ng + h(s2), ng, s2))
        if not found:
            return None, "no path to %s.%s" % (tgt["ref"], tgt["num"])
        path = [found]
        while path[-1] in came:
            path.append(came[path[-1]])
        path.reverse()
        for a, b in zip(path, path[1:]):
            if a[0] != b[0]:
                via_pts.append((a[1], a[2]))
            else:
                laid.append((a[0], a[1], a[2], b[1], b[2]))
        for s in path:
            src_cells.add(s)
        # the new copper is now part of the source set
        placed.append(tgt); todo.remove(tgt)
    return (laid, via_pts), None

def emit(net, laid, via_pts):
    nid = name2id.get(net)
    out = []
    # merge collinear runs
    runs = []
    for l, i1, j1, i2, j2 in laid:
        if runs and runs[-1][0] == l and runs[-1][3] == i1 and runs[-1][4] == j1 and \
           (runs[-1][3]-runs[-1][1], runs[-1][4]-runs[-1][2]) == (i2-i1, j2-j1):
            runs[-1] = (l, runs[-1][1], runs[-1][2], i2, j2)
        else:
            runs.append((l, i1, j1, i2, j2))
    for l, i1, j1, i2, j2 in runs:
        out.append('\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(width %s)\n'
                   '\t\t(layer "%s")\n\t\t(net %s)\n\t)'
                   % (g2mm(i1), g2mm(j1), g2mm(i2), g2mm(j2), TRACK, LAYERS[l], nid))
    for i, j in via_pts:
        out.append('\t(via\n\t\t(at %s %s)\n\t\t(size %s)\n\t\t(drill %s)\n'
                   '\t\t(layers "F.Cu" "B.Cu")\n\t\t(net %s)\n\t)'
                   % (g2mm(i), g2mm(j), VIA_D, VIA_DRILL, nid))
    return out

if __name__ == "__main__":
    nets = sys.argv[1:]
    add = []
    for net in nets:
        r, err = route(net)
        if err:
            print("  %-15s FAILED: %s" % (net, err)); continue
        laid, vp = r
        s = emit(net, laid, vp)
        add += s
        print("  %-15s routed: %d segment(s), %d via(s)" % (net, len(s)-len(vp), len(vp)))
    if add:
        body = t.rstrip()
        assert body.endswith(")")
        body = body[:-1].rstrip("\n") + "\n" + "\n".join(add) + "\n)\n"
        open(BOARD, "w", encoding="utf-8", newline="").write(body)
        print("  wrote %s" % os.path.basename(BOARD))
