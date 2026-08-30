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
BOARD = os.environ.get("BOARD") or os.path.join(HERE, "pcb-v3-handoff.kicad_pcb")
STEP = 0.05
def _rules():
    """Read the design rules from fab_floor_touchid.txt -- do NOT hard-code.

    These were frozen at 0.20/0.20 and stayed there after the board moved to
    0.127/0.10, so every "no path" this script reported was measured with a
    track 57% wider than the real one. stitch_open.py's docstring had already
    flagged it; the fix was applied to a scratch copy and never committed, so
    it kept lying on the next run. Same failure as the via sizes in
    gnd_taps.py: a constant that shadows the file everything else reads.
    """
    tw, cl, vd, vk = 0.127, 0.10, 0.45, 0.20
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "fab_floor_touchid.txt")
    if os.path.exists(p):
        for line in open(p):
            if "=" in line and not line.strip().startswith("#"):
                k, v = [s.strip() for s in line.split("=", 1)]
                if k == "track_width":
                    tw = float(v)
                elif k == "clearance":
                    cl = float(v)
                elif k == "via_diameter":
                    vd = float(v)
                elif k == "via_drill":
                    vk = float(v)
    return tw, cl, vd, vk


TRACK, CLR, VIA_D, VIA_DRILL = _rules()
# JLC: "Via hole to Track 0.2mm" -- a DRILL rule, invisible to copper checkers,
# and the binding one for any via smaller than 0.45 on this fab floor.
HOLE_TO_TRACK = 0.20
try:
    for _l in open(os.path.join(HERE, "fab_floor_touchid.txt")):
        if "=" in _l and not _l.strip().startswith("#"):
            _k, _v = [x.strip() for x in _l.split("=", 1)]
            if _k == "via_hole_to_track":
                HOLE_TO_TRACK = float(_v)
except OSError:
    pass
BOARD_SZ, EDGE = 19.30, 0.30
LAYERS = ["F.Cu", "In1.Cu", "B.Cu"]        # ROUTABLE layers
# In2.Cu is the GND plane and is not routed on -- but it is still COPPER.
# The v4 board has segments on it, and a through via pierces it, so it
# must appear in the obstacle map or a via can be dropped straight onto
# an In2.Cu track. Building masks only over LAYERS also crashed outright
# the moment an In2.Cu segment appeared (KeyError).
ALL_CU = LAYERS + ["In2.Cu"]
VIA_COST = 40          # in grid steps
N = int(round(BOARD_SZ / STEP)) + 1
ORG = -BOARD_SZ / 2.0

def g2mm(i):  return round(ORG + i * STEP, 4)
def mm2g(v):  return int(round((v - ORG) / STEP))

t = open(BOARD, encoding="utf-8", errors="replace").read()
# KiCad 8 wrote a top-level table -- (net 2 "GND") -- and referenced it from
# every item as (net 2). KiCad 10 dropped the table and writes the NAME inline
# on each item: (net "GND"). This file was built entirely on the KiCad 8 form,
# so on a KiCad 10 board every regex below missed, every pad and track read as
# net "", and emit() would have written (net None) into the board. It would
# have produced a corrupt file rather than an error.
#
# KICAD10 tells emit() which dialect to write back. Never guess it from the
# KiCad version string: what matters is the encoding THIS file uses.
nn = dict(re.findall(r'\(net (\d+) "([^"]*)"\)', t))
KICAD10 = not nn
if KICAD10:
    nn = {}
name2id = {v: k for k, v in nn.items()}

# one matcher for both dialects: (net 2 "GND") | (net 2) | (net "GND")
_NET_RE = re.compile(r'\(net (?:(\d+)(?: "([^"]*)")?|"([^"]*)")\)')


def netname(block):
    """Net NAME of an item, whichever dialect the file uses."""
    m = _NET_RE.search(block)
    if not m:
        return ""
    num, inline_name, only_name = m.group(1), m.group(2), m.group(3)
    if only_name is not None:
        return only_name
    if inline_name is not None:
        return inline_name
    return nn.get(num, "")

def rot(px, py, a):
    r = math.radians(a); c, s = math.cos(r), math.sin(r)
    return px * c + py * s, -px * s + py * c      # KiCad Y-down: +angle is CW

# ---------------------------------------------------------------- geometry --
pads = []      # (net, layers set, cx, cy, w, h, shape)
for fm in re.finditer(r'\(footprint "touchid:([^"]+)"(.*?)\n\t\)', t, re.S):
    blk = fm.group(2)
    at = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', blk)
    fx, fy, fa = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
    # "([^"]*)" not "([^"]+)": mounting holes are written (pad "" np_thru_hole
    # circle ...) with an EMPTY number, so requiring one character dropped both
    # MH pads -- 1.3 mm holes the router was free to route straight through.
    for pm in re.finditer(r'\(pad "([^"]*)" \w+ (\w+)(.*?)\n\t\t\)', blk, re.S):
        pb = pm.group(3)
        # (at X Y) OR (at X Y ROT). Demanding exactly two numbers made every
        # ROTATED pad fail this match and hit the `continue` below -- so the
        # router never saw them at all and would happily route straight
        # through one. On this board that silently hid U3.5 and U4.5, the
        # X2SON thermal pads at (at 0 0 45), one of which is an open pad we
        # are trying to fix.
        a_ = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', pb)
        s_ = re.search(r'\(size ([\d.]+) ([\d.]+)\)', pb)
        l_ = re.search(r'\(layers ([^)]*)\)', pb)
        pad_net = netname(pb)
        if not (a_ and s_):
            continue
        dx, dy = rot(float(a_.group(1)), float(a_.group(2)), fa)
        lays = set((l_.group(1).replace('"', '').split()) if l_ else [])
        if "*.Cu" in lays:
            lays |= set(LAYERS) | {"In2.Cu"}
        prot = fa + float(a_.group(3) or 0)
        pads.append(dict(net=pad_net, layers=lays,
                         x=fx + dx, y=fy + dy,
                         w=float(s_.group(1)), h=float(s_.group(2)),
                         rot=prot,
                         shape=pm.group(2), ref=fm.group(1), num=pm.group(1)))

tracks = []
for m in re.finditer(r'\(segment\b(.*?)\n\t\)', t, re.S):
    b = m.group(1)
    s_ = re.search(r'\(start ([-\d.]+) ([-\d.]+)\)', b)
    e_ = re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', b)
    w_ = re.search(r'\(width ([\d.]+)\)', b)
    l_ = re.search(r'\(layer "([^"]+)"\)', b)
    if s_ and e_ and w_ and l_:
        tracks.append(dict(net=netname(b),
                           x1=float(s_.group(1)), y1=float(s_.group(2)),
                           x2=float(e_.group(1)), y2=float(e_.group(2)),
                           w=float(w_.group(1)), layer=l_.group(1)))
vias = []
for m in re.finditer(r'\(via\b(.*?)\n\t\)', t, re.S):
    b = m.group(1)
    a_ = re.search(r'\(at ([-\d.]+) ([-\d.]+)\)', b)
    s_ = re.search(r'\(size ([\d.]+)\)', b)
    if a_ and s_:
        vias.append(dict(net=netname(b),
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

def blocked_masks(net, halo, ko="tracks"):
    """per-layer boolean: may the CENTRE of a feature sit here?

    ko selects WHICH keep-outs to fold in -- "tracks" for a track mask,
    "vias" for a via mask. They are not the same set and conflating them is
    catastrophic here: In2.Cu carries a board-wide keep-out that bans tracks
    and expressly ALLOWS vias (it is the plane guard). Folding that into the
    via mask marks all 19.3x19.3 mm of In2.Cu as blocked, and since a through
    via must be legal on every layer, via_ok becomes zero everywhere -- on a
    board that already contains 105 vias. Copper obstacles (pads, tracks,
    vias) still apply on every layer for both kinds.
    """
    m = {L: np.zeros((N, N), bool) for L in ALL_CU}
    for p in pads:
        if p["net"] == net:
            continue
        for L in ALL_CU:
            if L not in p["layers"]:
                continue
            r = round(p.get("rot", 0)) % 180
            if p["shape"] == "circle":
                m[L] |= ((XX - p["x"])**2 + (YY - p["y"])**2) <= (p["w"]/2 + halo)**2
            elif r == 0 or r == 90:
                # 90 swaps width and height. Ignoring that hid a real
                # 0.0915 mm violation at C9.1 once already.
                pw, ph = (p["w"], p["h"]) if r == 0 else (p["h"], p["w"])
                m[L] |= (np.abs(XX - p["x"]) <= pw/2 + halo) & \
                        (np.abs(YY - p["y"]) <= ph/2 + halo)
            else:
                # Off-axis pad (the X2SON thermals sit at 45 deg). Block the
                # CIRCUMSCRIBED circle. That over-blocks the corners slightly,
                # which costs a little routing room and can never let a track
                # through copper -- the right way round for an obstacle map.
                rad = math.hypot(p["w"], p["h"]) / 2
                m[L] |= ((XX - p["x"])**2 + (YY - p["y"])**2) <= (rad + halo)**2
    for s in tracks:
        if s["net"] == net:
            continue
        dx, dy = s["x2"] - s["x1"], s["y2"] - s["y1"]
        L2 = dx*dx + dy*dy
        tt = np.zeros((N, N)) if L2 == 0 else np.clip(
            ((XX - s["x1"]) * dx + (YY - s["y1"]) * dy) / L2, 0, 1)
        d2 = (XX - (s["x1"] + tt*dx))**2 + (YY - (s["y1"] + tt*dy))**2
        if s["layer"] in m:
            m[s["layer"]] |= d2 <= (s["w"]/2 + halo)**2
    for v in vias:
        if v["net"] == net:
            continue
        hit = ((XX - v["x"])**2 + (YY - v["y"])**2) <= (v["d"]/2 + halo)**2
        for L in ALL_CU:
            m[L] |= hit
    for k in keepouts:
        if not (k["no_tracks"] if ko == "tracks" else k["no_vias"]):
            continue
        pm = poly_mask(k["pts"])
        for L in ALL_CU:
            if L in k["layers"]:
                m[L] |= pm
    # The edge band depends on the FEATURE, not always on the track. `halo` is
    # CLR + feature_radius, so feature_radius = halo - CLR: TRACK/2 for a track
    # mask, VIA_D/2 for a via mask. Hard-coding TRACK/2 gave vias a track-sized
    # margin and put a GND via 0.025 mm inside the board-edge rule -- caught by
    # check_drc as VIA-BOARD-EDGE, and invisible to every clearance checker
    # because the board edge is not copper.
    _fr = max(0.0, halo - CLR)
    edge = (np.abs(XX) > BOARD_SZ/2 - EDGE - _fr) | \
           (np.abs(YY) > BOARD_SZ/2 - EDGE - _fr)
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
    vmask = blocked_masks(net, max(CLR + VIA_D/2, VIA_DRILL/2 + HOLE_TO_TRACK), ko="vias")
    via_ok = ~(vmask["F.Cu"] | vmask["In1.Cu"] | vmask["B.Cu"] | vmask["In2.Cu"])
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
    # Write back in the dialect THIS file uses. On a KiCad 10 board there is no
    # net table, name2id is empty, and the old code emitted the literal string
    # "None" as the net id -- a corrupt board that still parses.
    nid = ('"%s"' % net) if KICAD10 else name2id.get(net)
    if nid is None:
        raise SystemExit("net %r not in the board's net table -- refusing to "
                         "emit copper with no net" % net)
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
