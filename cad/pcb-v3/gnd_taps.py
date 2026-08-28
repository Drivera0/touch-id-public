"""
gnd_taps.py — weld every GND pad to the In2.Cu ground plane.

WHY THIS EXISTS
---------------
pcb-v3 was routed with GND deliberately excluded ("pour last", which is the
normal PCB order). The pour then never happened, so the board reached
"0 open connections, 17/17 preflight checks" with **40 GND pads connected to
nothing at all**. preflight could not see it: check 6 excludes GND by name,
because during routing an unpoured GND is expected.

route_planes.py lays the plane but deliberately places no taps, and the route
step that would weld them rips other nets to do it (its own improvement gate
rejected the attempt: 5 nets broken to gain 1). So the taps are placed here,
deterministically, one via per pad, touching nothing else.

A through-hole via on net GND anywhere legal reaches the In2.Cu plane, so each
pad needs only the shortest legal track to the nearest legal via site.

NOT ALLOWED, and the reason each matters:
  * over a J4/J11 pogo pad -- a through-hole via exits through the mating
    contact. This holds even for J4.5, which is itself GND: the hole would
    still wreck the contact face.
  * inside a no-via rule area (the antenna keep-out).
  * anywhere its clearance ring touches copper of another net.

Usage:  python gnd_taps.py IN.kicad_pcb OUT.kicad_pcb
"""
import collections, math, os, sys
import numpy as np
import sexp

HERE = os.path.dirname(os.path.abspath(__file__))
LAYERS = ["F.Cu", "In1.Cu", "B.Cu"]
PLANE = "In2.Cu"
BOARD_SZ, EDGE = 19.30, 0.30
STEP = 0.05
VIA_D, VIA_DRILL = 0.60, 0.30
GND = "GND"


def rules():
    tw, cl = 0.127, 0.10
    p = os.path.join(HERE, "fab_floor_touchid.txt")
    if os.path.exists(p):
        for line in open(p):
            if "=" in line and not line.strip().startswith("#"):
                k, v = [s.strip() for s in line.split("=", 1)]
                if k == "track_width":
                    tw = float(v)
                elif k == "clearance":
                    cl = float(v)
    return tw, cl


TRACK, CLR = rules()
N = int(round(BOARD_SZ / STEP)) + 1
ORG = -BOARD_SZ / 2.0
g2mm = lambda i: ORG + i * STEP
mm2g = lambda v: int(round((v - ORG) / STEP))
_ax = np.array([g2mm(i) for i in range(N)])
XX, YY = np.meshgrid(_ax, _ax, indexing="xy")
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def seg_mask(x1, y1, x2, y2, r):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    t = np.zeros((N, N)) if L2 == 0 else np.clip(
        ((XX - x1) * dx + (YY - y1) * dy) / L2, 0.0, 1.0)
    return (XX - (x1 + t * dx)) ** 2 + (YY - (y1 + t * dy)) ** 2 <= r * r


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


def main():
    src, dst = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8", errors="replace").read()
    root = sexp.parse(text)
    k, kd, s, f = sexp.kids, sexp.kid, sexp.s, sexp.f
    netname = {s(n[1]): (s(n[2]) if len(n) > 2 else "") for n in k(root, "net")}
    gnd_id = next(i for i, nm in netname.items() if nm == GND)

    pads = sexp.pads(text)
    tracks, vias = [], []
    for sg in k(root, "segment"):
        st, en = kd(sg, "start"), kd(sg, "end")
        tracks.append(dict(x1=f(st[1]), y1=f(st[2]), x2=f(en[1]), y2=f(en[2]),
                           w=f(kd(sg, "width")[1]), layer=s(kd(sg, "layer")[1]),
                           net=netname.get(s(kd(sg, "net")[1]), "")))
    for v in k(root, "via"):
        at = kd(v, "at")
        vias.append(dict(x=f(at[1]), y=f(at[2]), d=f(kd(v, "size")[1]),
                         net=netname.get(s(kd(v, "net")[1]), "")))
    novia = np.zeros((N, N), bool)
    for z in k(root, "zone"):
        ko = kd(z, "keepout")
        if not ko:
            continue
        opt = {s(c[0]): s(c[1]) for c in ko if isinstance(c, list) and len(c) > 1}
        if opt.get("vias") != "not_allowed":
            continue
        poly = kd(z, "polygon")
        pts = [(f(p[1]), f(p[2])) for p in k(kd(poly, "pts"), "xy")] if poly else []
        if pts:
            novia |= poly_mask(np.array(pts))

    # ---- how big is a pad, really -------------------------------------------
    # An axis-aligned w x h box is WRONG for two shapes on this board, and both
    # are on U3/U4 (TPS7A2033, X2SON-4):
    #   * "custom" pads carry their real outline in (primitives); the (size)
    #     field is only the anchor, here 0.148 mm for a pad that is far bigger.
    #   * roundrect pads at rot 45 are not axis aligned at all.
    # Under-covering them let a GND tap run 0.015 mm from U4.3. Both cases fall
    # back to the CIRCUMSCRIBED CIRCLE, which is conservative and cannot
    # under-cover -- taps have the whole board to route in, so paying a little
    # extra margin here costs nothing.
    prim_r = {}
    for fp in k(root, "footprint"):
        for pd in k(fp, "pad"):
            pr = kd(pd, "primitives")
            if pr is None:
                continue
            rr = 0.0
            for gp in pr:
                if not isinstance(gp, list):
                    continue
                ptsn = kd(gp, "pts")
                wln = kd(gp, "width")
                hw = f(wln[1]) / 2 if wln else 0.0
                if ptsn:
                    for xy in k(ptsn, "xy"):
                        rr = max(rr, math.hypot(f(xy[1]), f(xy[2])) + hw)
            if rr:
                prim_r[id(pd)] = rr
    _pr = list(prim_r.values())
    _pr_by_ref = {}
    _i = 0
    for fp in k(root, "footprint"):
        for pd in k(fp, "pad"):
            if id(pd) in prim_r:
                ref = "?"
                for pp in k(fp, "property"):
                    if s(pp[1]) == "Reference":
                        ref = s(pp[2])
                _pr_by_ref[(ref, s(pd[1]))] = prim_r[id(pd)]

    def pad_radius(p):
        """conservative radius, or None to use the axis-aligned box"""
        if p["shape"] == "circle":
            return p["w"] / 2
        if p["shape"] == "custom":
            return _pr_by_ref.get((p["ref"], p["pad"]),
                                  max(p["w"], p["h"]) / 2 + 0.35)
        if abs(p["rot"] % 90.0) > 1e-6:
            return math.hypot(p["w"], p["h"]) / 2
        return None

    def masks(halo):
        m = {L: np.zeros((N, N), bool) for L in LAYERS}
        for p in pads:
            if p["net"] == GND:
                continue
            r = pad_radius(p)
            for L in LAYERS:
                if L not in p["layers"]:
                    continue
                if r is not None:
                    m[L] |= (XX - p["x"])**2 + (YY - p["y"])**2 <= (r + halo)**2
                else:
                    m[L] |= (np.abs(XX - p["x"]) <= p["w"]/2 + halo) & \
                            (np.abs(YY - p["y"]) <= p["h"]/2 + halo)
        for t in tracks:
            if t["net"] == GND or t["layer"] not in m:
                continue
            m[t["layer"]] |= seg_mask(t["x1"], t["y1"], t["x2"], t["y2"], t["w"]/2 + halo)
        for v in vias:
            if v["net"] == GND:
                continue
            hit = (XX - v["x"])**2 + (YY - v["y"])**2 <= (v["d"]/2 + halo)**2
            for L in LAYERS:
                m[L] |= hit
        e = (np.abs(XX) > BOARD_SZ/2 - EDGE - halo) | (np.abs(YY) > BOARD_SZ/2 - EDGE - halo)
        for L in LAYERS:
            m[L] |= e
        return m

    # A grid samples cell CENTRES, so the segment BETWEEN two legal cells can
    # pass closer to an obstacle than either endpoint does -- by up to half the
    # grid diagonal. That is exactly the 0.014-0.016 mm overlaps the DRC found
    # on diagonal steps. Pay it back in the halo.
    GRID_SAFETY = STEP * math.sqrt(2) / 2          # 0.0354 mm at STEP 0.05
    tmask = masks(CLR + TRACK / 2 + GRID_SAFETY)
    vmask = masks(CLR + VIA_D / 2 + GRID_SAFETY)
    # GROW the no-via keep-out by the via's own radius (plus clearance).
    # poly_mask marks cells whose CENTRE is inside; a via centred 0.25 mm
    # OUTSIDE the antenna keep-out still puts 0.05 mm of copper inside it,
    # which is exactly what happened at (-5.20, 4.70). A keep-out applies to
    # the copper, not to the centre point.
    if novia.any():
        _rad = VIA_D / 2 + CLR
        _n2 = novia.copy()
        _steps = int(math.ceil(_rad / STEP))
        for _dx in range(-_steps, _steps + 1):
            for _dy in range(-_steps, _steps + 1):
                if math.hypot(_dx, _dy) * STEP > _rad:
                    continue
                _n2 |= np.roll(np.roll(novia, _dy, axis=0), _dx, axis=1)
        novia = _n2
    via_ok = ~(vmask["F.Cu"] | vmask["In1.Cu"] | vmask["B.Cu"]) & ~novia
    # a via must never pierce a pogo contact -- GND ones included
    for p in pads:
        if p["ref"] in ("J4", "J11"):
            via_ok &= ~((XX - p["x"])**2 + (YY - p["y"])**2
                        <= (p["w"]/2 + VIA_D/2 + CLR)**2)

    # HOLE-TO-HOLE. Copper clearance does not cover this and same-net copper
    # clearance does not apply at all, so a GND tap will happily sit on top of
    # another GND via's DRILL unless this is enforced separately: the first
    # attempt produced 27 via-drill-hole violations that way. Drills must keep
    # H2H between their edges whatever net they belong to.
    H2H = 0.20
    for line in open(os.path.join(HERE, "fab_floor_touchid.txt")):
        if line.strip().startswith("hole_to_hole"):
            H2H = float(line.split("=", 1)[1])

    # MEASURED against check_drc, not assumed: two 0.6/0.3 vias 0.702 mm apart
    # are reported as overlapping by 0.098 mm, i.e. the rule in force is
    # 0.6 + 0.20 = 0.80 mm centre-to-centre -- it prices the PAD diameter, not
    # the drill. Using drill/2 + H2H + drill/2 = 0.50 left 19 violations.
    def _drill_block(mask, x, y, d):
        need = max(d, VIA_D) + H2H
        return mask & ~((XX - x)**2 + (YY - y)**2 < need**2)

    for v in vias:                              # every existing via, any net
        via_ok = _drill_block(via_ok, v["x"], v["y"], VIA_DRILL)
    for fp in k(root, "footprint"):             # NPTH mounting holes
        at = kd(fp, "at")
        for pd in k(fp, "pad"):
            dr = kd(pd, "drill")
            if dr is None:
                continue
            pat = kd(pd, "at")
            via_ok = _drill_block(via_ok, f(at[1]) + f(pat[1]),
                                  f(at[2]) + f(pat[2]), f(dr[1]))

    gpads = [p for p in pads if p["net"] == GND]
    have = {}
    new_v, new_t = [], []
    # GND copper already connected to the plane: existing GND tracks and vias,
    # plus everything this run welds. Grown as we go.
    tied = {L: np.zeros((N, N), bool) for L in LAYERS}
    for v in vias:
        if v["net"] == GND:
            hit = (XX - v["x"])**2 + (YY - v["y"])**2 <= (v["d"]/2)**2
            for L in LAYERS:
                tied[L] |= hit

    def tapped(p):
        """already a GND via inside/next to this pad?"""
        for v in vias + new_v:
            if v["net"] != GND:
                continue
            if math.hypot(v["x"] - p["x"], v["y"] - p["y"]) <= p["w"]/2 + VIA_D/2:
                return True
        return False

    order = sorted(gpads, key=lambda p: (p["ref"], p["pad"]))
    for p in order:
        L = "F.Cu" if "F.Cu" in p["layers"] else ("B.Cu" if "B.Cu" in p["layers"] else None)
        if L is None or tapped(p):
            continue
        # BFS from the pad across track-legal cells to the nearest legal via site
        seen = np.zeros((N, N), bool)
        q = collections.deque()
        i0, i1 = mm2g(p["x"] - p["w"]/2), mm2g(p["x"] + p["w"]/2)
        j0, j1 = mm2g(p["y"] - p["h"]/2), mm2g(p["y"] + p["h"]/2)
        # Seed only cells that are themselves legal. Seeding the whole pad
        # unconditionally let a track leave from an illegal cell, and the first
        # segment out of the pad then grazed a 0.4 mm VBAT_SENSE trunk by
        # 0.014 mm -- the endpoints were checked, the segment between them was
        # not. Fall back to the pad centre only if nothing in the pad is legal.
        for j in range(max(j0, 0), min(j1, N-1)+1):
            for i in range(max(i0, 0), min(i1, N-1)+1):
                if not seen[j, i] and not tmask[L][j, i]:
                    seen[j, i] = True; q.append((i, j, None))
        if not q:
            ci, cj = mm2g(p["x"]), mm2g(p["y"])
            if 0 <= ci < N and 0 <= cj < N:
                seen[cj, ci] = True; q.append((ci, cj, None))
        prev = {}
        goal = None
        goal_is_via = True
        while q:
            i, j, par = q.popleft()
            prev[(i, j)] = par
            if via_ok[j, i]:
                goal = (i, j); goal_is_via = True; break
            # reaching GND copper that is ALREADY welded to the plane is just
            # as good as a via of one's own, and it is what saves the pads
            # boxed in too tightly for a 0.6 mm via to fit anywhere near them
            # Deep inside, not grazing the edge: every neighbour must be tied
            # copper too. Landing on the boundary produced a 0.050 mm endpoint
            # gap that the DRC called a same-net soft joint -- a joint that
            # looks connected on screen and may not be.
            if tied[L][j, i] and all(
                    0 <= i+di < N and 0 <= j+dj < N and tied[L][j+dj, i+di]
                    for di, dj in DIRS):
                goal = (i, j); goal_is_via = False; break
            for di, dj in DIRS:
                ni, nj = i+di, j+dj
                if 0 <= ni < N and 0 <= nj < N and not seen[nj, ni] and not tmask[L][nj, ni]:
                    seen[nj, ni] = True; q.append((ni, nj, (i, j)))
        if goal is None:
            have[p["ref"] + "." + p["pad"]] = "NO VIA SITE REACHABLE"
            continue
        path = []
        cur = goal
        while cur is not None:
            path.append(cur); cur = prev[cur]
        path.reverse()
        if goal_is_via:
            new_v.append(dict(x=g2mm(goal[0]), y=g2mm(goal[1]), d=VIA_D, net=GND))
            # a tap just placed is an obstacle for every tap after it, or they
            # cluster into each other's drill exclusion
            via_ok = _drill_block(via_ok, g2mm(goal[0]), g2mm(goal[1]), VIA_DRILL)
        # collapse to corner points
        if len(path) > 1:
            pts = [path[0]]
            for idx in range(1, len(path)-1):
                a_, b_, c_ = path[idx-1], path[idx], path[idx+1]
                if (b_[0]-a_[0], b_[1]-a_[1]) != (c_[0]-b_[0], c_[1]-b_[1]):
                    pts.append(path[idx])
            pts.append(path[-1])
            for a_, b_ in zip(pts, pts[1:]):
                new_t.append((g2mm(a_[0]), g2mm(a_[1]), g2mm(b_[0]), g2mm(b_[1]), L))
                tied[L] |= seg_mask(g2mm(a_[0]), g2mm(a_[1]),
                                    g2mm(b_[0]), g2mm(b_[1]), TRACK/2)
        if goal_is_via:
            hit = (XX - g2mm(goal[0]))**2 + (YY - g2mm(goal[1]))**2 <= (VIA_D/2)**2
            for L2 in LAYERS:
                tied[L2] |= hit
        have[p["ref"] + "." + p["pad"]] = "%.2f mm" % (
            sum(math.hypot(t[2]-t[0], t[3]-t[1]) for t in new_t[-max(1, len(path)):]))

    # SNAP NEAR-COINCIDENT ENDPOINTS. Two taps that finish a single grid step
    # apart leave a 0.05 mm gap the DRC calls a "same-net soft joint": copper
    # that looks joined on screen and may not be. Weld them to one point.
    _ends = []
    for (x1, y1, x2, y2, L) in new_t:
        _ends += [(x1, y1), (x2, y2)]
    _canon = {}
    for e in _ends:
        for c in _canon:
            if abs(c[0]-e[0]) <= STEP*1.01 and abs(c[1]-e[1]) <= STEP*1.01:
                _canon[e] = _canon[c]; break
        else:
            _canon[e] = e
    _snapped = 0
    _nt = []
    for (x1, y1, x2, y2, L) in new_t:
        a_ = _canon[(x1, y1)]; b_ = _canon[(x2, y2)]
        if a_ != (x1, y1) or b_ != (x2, y2):
            _snapped += 1
        if a_ != b_:                      # a segment collapsed to a point is dropped
            _nt.append((a_[0], a_[1], b_[0], b_[1], L))
    new_t = _nt
    if _snapped:
        print(f"  snapped {_snapped} endpoint(s) onto a shared point")

    body = []
    for (x1, y1, x2, y2, L) in new_t:
        body.append(f'\t(segment (start {x1:.4f} {y1:.4f}) (end {x2:.4f} {y2:.4f}) '
                    f'(width {TRACK}) (layer "{L}") (net {gnd_id}))')
    for v in new_v:
        body.append(f'\t(via (at {v["x"]:.4f} {v["y"]:.4f}) (size {VIA_D}) '
                    f'(drill {VIA_DRILL}) (layers "F.Cu" "B.Cu") (net {gnd_id}))')
    if body:
        cut = text.rstrip().rfind(")")
        text = text[:cut] + "\n".join(body) + "\n" + text[cut:]
    open(dst, "w", encoding="utf-8").write(text)
    fail = [k_ for k_, v_ in have.items() if not v_.endswith("mm")]
    print(f"GND pads: {len(gpads)}   taps placed: {len(new_v)}   "
          f"segments: {len(new_t)}   no tap found: {len(fail)}")
    if fail:
        # NOT necessarily a fault. This script models tracks and vias; it does
        # NOT model the poured zones, so a pad sitting in the middle of the
        # F.Cu pour looks stranded here and is in fact perfectly connected.
        # check_connected.py understands the fill and is the authority.
        print("  no tap placed for:", ", ".join(fail),
              "\n  -> these are served by the pour if anything. CONFIRM WITH "
              "check_connected.py, which models the zone fill; this script does not.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
