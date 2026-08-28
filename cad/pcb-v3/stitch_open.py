"""
stitch_open.py — attach a stranded pad to copper that is already there.

The batch router leaves a handful of pads open, but the nets they belong to are
otherwise fully routed. Re-routing such a net from scratch (what handroute.py
does) throws away 20 good segments to fix one pin, and usually strands a
different pin instead. This does the thing a person does in the interactive
router: leave the existing copper alone and run ONE trace from the orphan pad to
the nearest metal of its own net.

Grid A* over F.Cu / In1.Cu / B.Cu. Obstacles come from the real board, per
layer, and the design rules come from fab_floor_touchid.txt rather than being
hard-coded -- handroute.py froze TRACK/CLR at 0.20/0.20 and silently kept using
them after the board moved to 0.127/0.10.

Parsing goes through sexp.py, NOT regex. Regex parsing of this format has
produced real bugs in this project (a pad-net pattern that ran past NC pads and
stole the next pad's net, and a layers pattern that missed every B.Cu pad).

Usage:  python stitch_open.py IN.kicad_pcb OUT.kicad_pcb [NET ...]
        (no NET given -> every net with an open pad, per check_connected)
"""
import heapq, math, os, subprocess, sys
import numpy as np
import sexp

HERE = os.path.dirname(os.path.abspath(__file__))
KRT = os.environ.get("KRT") or os.path.normpath(os.path.join(
    HERE, "..", "..", "tools", "com_github_drandyhaas_kicadroutingtools"))
LAYERS = ["F.Cu", "In1.Cu", "B.Cu"]
BOARD_SZ, EDGE = 19.30, 0.30
STEP = 0.025
VIA_D, VIA_DRILL = 0.60, 0.30
VIA_COST_MM = 1.0            # a via is worth about a millimetre of detour


def read_rules():
    """TRACK / CLEARANCE from the fab floor file -- one source of truth."""
    tw, cl = 0.127, 0.10
    p = os.path.join(HERE, "fab_floor_touchid.txt")
    if os.path.exists(p):
        for line in open(p):
            if "=" not in line or line.strip().startswith("#"):
                continue
            k, v = [s.strip() for s in line.split("=", 1)]
            if k == "track_width":
                tw = float(v)
            elif k == "clearance":
                cl = float(v)
    return tw, cl


TRACK, CLR = read_rules()
N = int(round(BOARD_SZ / STEP)) + 1
ORG = -BOARD_SZ / 2.0
g2mm = lambda i: ORG + i * STEP
mm2g = lambda v: int(round((v - ORG) / STEP))

_ax = np.array([g2mm(i) for i in range(N)])
XX, YY = np.meshgrid(_ax, _ax, indexing="xy")


# --------------------------------------------------------------- board read --
def load(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    root = sexp.parse(text)
    k, kd, s, f = sexp.kids, sexp.kid, sexp.s, sexp.f

    netname = {}
    for n in k(root, "net"):
        netname[s(n[1])] = s(n[2]) if len(n) > 2 else ""

    pads = sexp.pads(text)
    for p in pads:
        if "*.Cu" in p["layers"]:
            p["layers"] = LAYERS + ["In2.Cu"]

    tracks = []
    for sg in k(root, "segment"):
        st, en = kd(sg, "start"), kd(sg, "end")
        nid = kd(sg, "net")
        tracks.append(dict(x1=f(st[1]), y1=f(st[2]), x2=f(en[1]), y2=f(en[2]),
                           w=f(kd(sg, "width")[1]),
                           layer=s(kd(sg, "layer")[1]),
                           net=netname.get(s(nid[1]), "") if nid else ""))
    vias = []
    for v in k(root, "via"):
        at = kd(v, "at"); nid = kd(v, "net")
        vias.append(dict(x=f(at[1]), y=f(at[2]), d=f(kd(v, "size")[1]),
                         net=netname.get(s(nid[1]), "") if nid else ""))
    zones = []
    for z in k(root, "zone"):
        ko = kd(z, "keepout")
        if ko is None:
            continue
        lay = kd(z, "layers") or kd(z, "layer")
        lays = [s(x) for x in lay[1:]] if lay else []
        poly = kd(z, "polygon")
        pts = []
        if poly:
            for xy in k(kd(poly, "pts"), "xy"):
                pts.append((f(xy[1]), f(xy[2])))
        if not pts:
            continue
        opt = {s(c[0]): s(c[1]) for c in ko if isinstance(c, list) and len(c) > 1}
        zones.append(dict(layers=lays, pts=np.array(pts),
                          no_tracks=opt.get("tracks") == "not_allowed",
                          no_vias=opt.get("vias") == "not_allowed"))
    return text, netname, pads, tracks, vias, zones


def poly_mask(pts):
    inside = np.zeros((N, N), bool)
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]; xj, yj = pts[j]
        cond = (yi > YY) != (yj > YY)
        with np.errstate(divide="ignore", invalid="ignore"):
            xint = (xj - xi) * (YY - yi) / (yj - yi + 1e-30) + xi
        inside ^= cond & (XX < xint)
        j = i
    return inside


def seg_mask(x1, y1, x2, y2, r):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    t = np.zeros((N, N)) if L2 == 0 else np.clip(
        ((XX - x1) * dx + (YY - y1) * dy) / L2, 0.0, 1.0)
    return (XX - (x1 + t * dx)) ** 2 + (YY - (y1 + t * dy)) ** 2 <= r * r


def build_masks(net, pads, tracks, vias, zones, halo):
    """per-layer: may the CENTRE of a feature of this halo sit here?"""
    m = {L: np.zeros((N, N), bool) for L in LAYERS}
    for p in pads:
        if p["net"] == net:
            continue
        for L in LAYERS:
            if L not in p["layers"]:
                continue
            if p["shape"] == "circle":
                m[L] |= (XX - p["x"]) ** 2 + (YY - p["y"]) ** 2 <= (p["w"] / 2 + halo) ** 2
            else:
                m[L] |= (np.abs(XX - p["x"]) <= p["w"] / 2 + halo) & \
                        (np.abs(YY - p["y"]) <= p["h"] / 2 + halo)
    for t in tracks:
        if t["net"] == net or t["layer"] not in m:
            continue
        m[t["layer"]] |= seg_mask(t["x1"], t["y1"], t["x2"], t["y2"], t["w"] / 2 + halo)
    for v in vias:
        if v["net"] == net:
            continue
        hit = (XX - v["x"]) ** 2 + (YY - v["y"]) ** 2 <= (v["d"] / 2 + halo) ** 2
        for L in LAYERS:
            m[L] |= hit
    for z in zones:
        if not z["no_tracks"]:
            continue
        pm = poly_mask(z["pts"])
        for L in LAYERS:
            if L in z["layers"]:      # a rule area binds ONLY the layers it names
                m[L] |= pm
    edge = (np.abs(XX) > BOARD_SZ / 2 - EDGE - halo) | \
           (np.abs(YY) > BOARD_SZ / 2 - EDGE - halo)
    for L in LAYERS:
        m[L] |= edge
    return m


def own_copper(net, pads, tracks, vias, orphan):
    """cells occupied by this net's EXISTING copper, excluding the orphan pad."""
    own = {L: np.zeros((N, N), bool) for L in LAYERS}
    for p in pads:
        if p["net"] != net or p is orphan:
            continue
        for L in LAYERS:
            if L not in p["layers"]:
                continue
            if p["shape"] == "circle":
                own[L] |= (XX - p["x"]) ** 2 + (YY - p["y"]) ** 2 <= (p["w"] / 2) ** 2
            else:
                own[L] |= (np.abs(XX - p["x"]) <= p["w"] / 2) & \
                          (np.abs(YY - p["y"]) <= p["h"] / 2)
    for t in tracks:
        if t["net"] != net or t["layer"] not in own:
            continue
        own[t["layer"]] |= seg_mask(t["x1"], t["y1"], t["x2"], t["y2"], t["w"] / 2)
    for v in vias:
        if v["net"] != net:
            continue
        hit = (XX - v["x"]) ** 2 + (YY - v["y"]) ** 2 <= (v["d"] / 2) ** 2
        for L in LAYERS:
            own[L] |= hit
    return own


def pad_cells(p, L):
    if L not in p["layers"]:
        return []
    out = []
    i0, i1 = mm2g(p["x"] - p["w"] / 2), mm2g(p["x"] + p["w"] / 2)
    j0, j1 = mm2g(p["y"] - p["h"] / 2), mm2g(p["y"] + p["h"] / 2)
    for j in range(max(j0, 0), min(j1, N - 1) + 1):
        for i in range(max(i0, 0), min(i1, N - 1) + 1):
            if p["shape"] == "circle" and \
               (g2mm(i) - p["x"]) ** 2 + (g2mm(j) - p["y"]) ** 2 > (p["w"] / 2) ** 2:
                continue
            out.append((i, j))
    return out


DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def astar(starts, goal, tmask, via_ok):
    """starts: [(i,j,layer_idx)]  goal: {layer_idx: bool grid}"""
    INF = float("inf")
    dist = {}
    pq = []
    for (i, j, L) in starts:
        dist[(i, j, L)] = 0.0
        heapq.heappush(pq, (0.0, i, j, L, None))
    prev = {}
    gi = [np.argwhere(goal[L]) for L in range(len(LAYERS))]
    tgt = []
    for L in range(len(LAYERS)):
        if len(gi[L]):
            tgt.append((gi[L][:, 1].mean(), gi[L][:, 0].mean()))
    if not tgt:
        return None
    tx = sum(t[0] for t in tgt) / len(tgt)
    ty = sum(t[1] for t in tgt) / len(tgt)

    def h(i, j):
        return math.hypot(i - tx, j - ty) * STEP * 0.9

    while pq:
        d, i, j, L, par = heapq.heappop(pq)
        key = (i, j, L)
        if key in prev:
            continue
        prev[key] = par
        if goal[L][j, i]:
            path = []
            while key is not None:
                path.append(key)
                key = prev[key]
            return path[::-1]
        base = dist[(i, j, L)]
        for di, dj in DIRS:
            ni, nj = i + di, j + dj
            if not (0 <= ni < N and 0 <= nj < N):
                continue
            if tmask[L][nj, ni]:
                continue
            nd = base + math.hypot(di, dj) * STEP
            k2 = (ni, nj, L)
            if nd < dist.get(k2, INF):
                dist[k2] = nd
                heapq.heappush(pq, (nd + h(ni, nj), ni, nj, L, (i, j, L)))
        if via_ok[j, i]:
            for L2 in range(len(LAYERS)):
                if L2 == L or tmask[L2][j, i]:
                    continue
                nd = base + VIA_COST_MM
                k2 = (i, j, L2)
                if nd < dist.get(k2, INF):
                    dist[k2] = nd
                    heapq.heappush(pq, (nd + h(i, j), i, j, L2, (i, j, L)))
    return None


def open_pads(board):
    """(net, x, y, layer) for every pad check_connected reports disconnected."""
    out = []
    r = subprocess.run([sys.executable, os.path.join(KRT, "py_router", "check_connected.py"), board],
                       cwd=KRT, env=dict(os.environ, PYTHONPATH=KRT),
                       capture_output=True, text=True, timeout=300).stdout
    net = None
    for line in r.splitlines():
        st = line.strip()
        if st.endswith("):") and "(net " in st:
            net = st.split(" (net")[0]
        elif st.startswith("(") and " on " in st:
            coord, rest = st.split(") on ")
            x, y = [float(v) for v in coord.lstrip("(").split(",")]
            out.append((net, x, y, rest.split()[0]))
    return out


def main():
    src, dst = sys.argv[1], sys.argv[2]
    want = sys.argv[3:]
    text, netname, pads, tracks, vias, zones = load(src)
    todo = open_pads(src)
    if want:
        todo = [t for t in todo if t[0] in want]
    if not todo:
        print("nothing open");
        open(dst, "w", encoding="utf-8").write(text)
        return 0
    print(f"rules: track {TRACK} clearance {CLR}   grid {STEP} mm")
    print(f"open pads to stitch: {len(todo)}")

    new_seg, new_via = [], []
    for (net, ox, oy, olay) in todo:
        orph = None
        for p in pads:
            if p["net"] == net and abs(p["x"] - ox) < 0.02 and abs(p["y"] - oy) < 0.02:
                orph = p; break
        if orph is None:
            print(f"  {net}: cannot find pad at ({ox},{oy})"); continue

        tmask = build_masks(net, pads, tracks + new_seg, vias + new_via, zones,
                            CLR + TRACK / 2)
        vmask = build_masks(net, pads, tracks + new_seg, vias + new_via, zones,
                            CLR + VIA_D / 2)
        via_ok = ~(vmask["F.Cu"] | vmask["In1.Cu"] | vmask["B.Cu"])
        for z in zones:
            if z["no_vias"]:
                via_ok &= ~poly_mask(z["pts"])

        own = own_copper(net, pads, tracks + new_seg, vias + new_via, orph)
        goal = [own[L] & ~tmask[L] for L in LAYERS]
        if not any(g.any() for g in goal):
            goal = [own[L] for L in LAYERS]

        starts = []
        for li, L in enumerate(LAYERS):
            for (i, j) in pad_cells(orph, L):
                if not tmask[li][j, i] if False else True:
                    starts.append((i, j, li))
        if not starts:
            print(f"  {net}: orphan pad has no usable cell"); continue

        path = astar(starts, goal, [tmask[L] for L in LAYERS], via_ok)
        if path is None:
            print(f"  {net} {orph['ref']}.{orph['pad']}: NO PATH"); continue

        nid = None
        for k, v in netname.items():
            if v == net:
                nid = k; break
        runs, cur = [], [path[0]]
        for a, b in zip(path, path[1:]):
            if a[2] != b[2]:
                runs.append(cur); cur = [b]
                new_via.append(dict(x=g2mm(a[0]), y=g2mm(a[1]), d=VIA_D, net=net))
            else:
                cur.append(b)
        runs.append(cur)
        nseg = 0
        for run in runs:
            if len(run) < 2:
                continue
            # collapse collinear points
            pts = [run[0]]
            for idx in range(1, len(run) - 1):
                x0, y0 = run[idx - 1][0], run[idx - 1][1]
                x1, y1 = run[idx][0], run[idx][1]
                x2, y2 = run[idx + 1][0], run[idx + 1][1]
                if (x1 - x0, y1 - y0) != (x2 - x1, y2 - y1):
                    pts.append(run[idx])
            pts.append(run[-1])
            for a, b in zip(pts, pts[1:]):
                new_seg.append(dict(x1=g2mm(a[0]), y1=g2mm(a[1]),
                                    x2=g2mm(b[0]), y2=g2mm(b[1]),
                                    w=TRACK, layer=LAYERS[a[2]], net=net, nid=nid))
                nseg += 1
        mm = sum(math.hypot(s["x2"] - s["x1"], s["y2"] - s["y1"])
                 for s in new_seg if s["net"] == net)
        print(f"  {net} {orph['ref']}.{orph['pad']}: ROUTED "
              f"{nseg} seg, {sum(1 for v in new_via if v['net'] == net)} via, {mm:.2f} mm")

    body = []
    for s in new_seg:
        body.append(f'\t(segment (start {s["x1"]:.4f} {s["y1"]:.4f}) '
                    f'(end {s["x2"]:.4f} {s["y2"]:.4f}) (width {s["w"]}) '
                    f'(layer "{s["layer"]}") (net {s["nid"]}))')
    for v in new_via:
        nid = None
        for k, val in netname.items():
            if val == v["net"]:
                nid = k; break
        body.append(f'\t(via (at {v["x"]:.4f} {v["y"]:.4f}) (size {VIA_D}) '
                    f'(drill {VIA_DRILL}) (layers "F.Cu" "B.Cu") (net {nid}))')
    if body:
        cut = text.rstrip().rfind(")")
        text = text[:cut] + "\n".join(body) + "\n" + text[cut:]
    open(dst, "w", encoding="utf-8").write(text)
    print(f"wrote {dst}  (+{len(new_seg)} segments, +{len(new_via)} vias)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
