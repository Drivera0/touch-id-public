"""
close_open.py -- connect ONE open pad to the copper its net already has.

WHY NOT JUST RUN handroute
--------------------------
handroute.route() rebuilds a whole net from scratch as an MST over all its
pads. That is right for a dead net and wrong for these: VSTOR already has 57
segments and 11 pads with exactly ONE stray; VBAT has 33 segments and one
stray. Re-routing those from scratch lays a second, redundant copy of copper
that is already there and already correct.

This asks the only question that is open: what is the shortest legal path from
THIS pad to copper this net already owns?

THREE THINGS THAT ARE EASY TO GET WRONG, AND ARE HANDLED HERE
-------------------------------------------------------------
1. WHICH copper to aim at. Seeding from "any copper of this net" lets the
   search connect a stray pad to ANOTHER stray piece and report success while
   the pad is still open. The target set is built only from pads that
   pour_truth.py places in the net's MAIN group.

2. A net with a plane is not really trying to reach a pad. GND's target is the
   In2.Cu plane, and ANY legal via reaches it. Aiming only at pads is why four
   GND pads read as unroutable while sitting directly above 212 mm2 of copper.
   When the net has a plane polygon, any via-legal cell over that plane ends
   the search -- and the heuristic drops to zero, because with two kinds of
   target a pad-directed heuristic is inadmissible and steers straight past a
   perfectly good via site.

3. Vias must clear EACH OTHER. The grid search places them without mutual
   checks, so a path that changes layer twice in quick succession can put two
   drills 0.427 mm apart -- inside the 0.25 mm hole-to-hole rule, which is
   exactly what the router's DRC caught on the first attempt. The path is
   therefore required to prove itself, and vias get progressively more
   expensive until the search stops using ones it cannot legally place.

Obstacles come from handroute, which now sees all 145 pads including the
rotated thermals and the mounting holes it used to skip.

Usage:  python close_open.py BOARD.kicad_pcb OUT.kicad_pcb REF.PAD [REF.PAD ...]
"""
import heapq
import math
import os
import sys

import numpy as np

if len(sys.argv) < 4:
    sys.exit(__doc__)

SRC, DST = sys.argv[1], sys.argv[2]
TARGETS = sys.argv[3:]
os.environ.setdefault("BOARD", os.path.abspath(SRC))

import handroute as H          # noqa: E402  (must follow $BOARD)
import pour_truth as pt        # noqa: E402

H2H = 0.25          # drill edge-to-edge; the value check_drc enforces


def search(src_cells, goal, plane_ok, tmask, via_ok, via_cost, h):
    """Dijkstra/A* over the routable layers. Returns (end, came, on_plane)."""
    openq = [(h(s), 0, s) for s in src_cells]
    heapq.heapify(openq)
    best = {s: 0 for s in src_cells}
    came = {}
    while openq:
        _f, g, cur = heapq.heappop(openq)
        if cur in goal:
            return cur, came, False
        if plane_ok is not None and plane_ok[cur[2], cur[1]]:
            return cur, came, True      # drop a via; the plane does the rest
        if g > best.get(cur, 1e18):
            continue
        l, i, j = cur
        for dx, dy in H.DIRS:
            ni, nj = i + dx, j + dy
            if not (0 <= ni < H.N and 0 <= nj < H.N):
                continue
            if tmask[H.LAYERS[l]][nj, ni]:
                continue
            ng = g + (1.414 if dx and dy else 1.0)
            s2 = (l, ni, nj)
            if ng < best.get(s2, 1e18):
                best[s2] = ng
                came[s2] = cur
                heapq.heappush(openq, (ng + h(s2), ng, s2))
        if via_ok[j, i]:
            for l2 in range(len(H.LAYERS)):
                if l2 == l or tmask[H.LAYERS[l2]][j, i]:
                    continue
                s2 = (l2, i, j)
                ng = g + via_cost
                if ng < best.get(s2, 1e18):
                    best[s2] = ng
                    came[s2] = cur
                    heapq.heappush(openq, (ng + h(s2), ng, s2))
    return None, came, False


def unwind(end, came, on_plane):
    path = [end]
    while path[-1] in came:
        path.append(came[path[-1]])
    path.reverse()
    laid, vpts = [], []
    for a, b in zip(path, path[1:]):
        if a[0] != b[0]:
            vpts.append((a[1], a[2]))
        else:
            laid.append((a[0], a[1], a[2], b[1], b[2]))
    if on_plane:
        vpts.append((end[1], end[2]))
    return laid, vpts


def h2h_ok(vpts, existing, drill):
    """new vias vs each other AND vs every via already on the board"""
    pts = [(H.g2mm(i), H.g2mm(j)) for i, j in vpts]
    need = drill + H2H
    for a in range(len(pts)):
        for b in range(a + 1, len(pts)):
            if math.dist(pts[a], pts[b]) < need:
                return False
        for v in existing:
            d2 = (drill + v.get("drill", drill)) / 2 + H2H
            if math.dist(pts[a], (v["x"], v["y"])) < d2:
                return False
    return True


def main():
    pads, segs, vias, polys = pt.parse(SRC)
    rep = pt.analyse(pads, segs, vias, polys)
    added = []
    new_vias = []

    for tgt in TARGETS:
        ref, num = tgt.split(".", 1)
        hp = [p for p in H.pads if p["ref"] == ref and p["num"] == num]
        if not hp:
            print("  %-10s NOT FOUND in the obstacle model" % tgt)
            continue
        hp = hp[0]
        net = hp["net"]
        if net not in rep:
            print("  %-10s net %r not analysed" % (tgt, net))
            continue
        stray = {(p["ref"], p["pad"]) for p in rep[net]["stray"]}
        if (ref, num) not in stray:
            print("  %-10s already connected" % tgt)
            continue

        tmask = H.blocked_masks(net, H.CLR + H.TRACK / 2)
        vmask = H.blocked_masks(net, H.CLR + H.VIA_D / 2, ko="vias")
        via_ok = ~(vmask["F.Cu"] | vmask["In1.Cu"] | vmask["B.Cu"]
                   | vmask["In2.Cu"])

        # search OUTWARD from the stray pad
        src_cells = set()
        for L in H.LAYERS:
            if L in hp["layers"]:
                for c in H.pad_cells(hp, L):
                    src_cells.add((H.LAYERS.index(L), c[0], c[1]))
        goal = set()
        for p in H.pads:
            if p["net"] != net or (p["ref"], p["num"]) in stray:
                continue
            if (p["ref"], p["num"]) == (ref, num):
                continue
            for L in H.LAYERS:
                if L in p["layers"]:
                    for c in H.pad_cells(p, L):
                        goal.add((H.LAYERS.index(L), c[0], c[1]))
        # The net's EXISTING TRACKS AND VIAS are targets too, and leaving them
        # out is what made SENSOR_SW_EN unroutable: the only path ends beside a
        # via this net already owns, so the search drilled its own via 0.427 mm
        # away -- a hole-to-hole violation -- instead of simply joining the
        # copper that was already there. Landing on same-net copper is a
        # connection; it needs no via at all.
        for sg in rep[net]["main_segs"]:
            if sg["layer"] not in H.LAYERS:
                continue
            li = H.LAYERS.index(sg["layer"])
            n = max(2, int(math.dist((sg["x1"], sg["y1"]),
                                     (sg["x2"], sg["y2"])) / (H.STEP / 2)) + 1)
            for k in range(n + 1):
                f = k / n
                gx = H.mm2g(sg["x1"] + f * (sg["x2"] - sg["x1"]))
                gy = H.mm2g(sg["y1"] + f * (sg["y2"] - sg["y1"]))
                if 0 <= gx < H.N and 0 <= gy < H.N:
                    goal.add((li, gx, gy))
        for v in rep[net]["main_vias"]:
            gx, gy = H.mm2g(v["x"]), H.mm2g(v["y"])
            if 0 <= gx < H.N and 0 <= gy < H.N:
                for li in range(len(H.LAYERS)):
                    goal.add((li, gx, gy))
        # A target cell the router may not legally occupy is not a target.
        goal = {(l, i, j) for (l, i, j) in goal
                if not tmask[H.LAYERS[l]][j, i]}

        plane_mask = None
        for q in polys:
            if q["net"] == net and q["layer"] not in H.LAYERS:
                pm = H.poly_mask(np.array(q["pts"]))
                plane_mask = pm if plane_mask is None else (plane_mask | pm)
        plane_ok = None if plane_mask is None else (plane_mask & via_ok)
        if plane_ok is not None and not plane_ok.any():
            plane_ok = None

        if not src_cells or (not goal and plane_ok is None):
            print("  %-10s no free cell on the pad or on the net's copper" % tgt)
            continue

        if plane_ok is not None:
            def h(s):
                return 0.0
        else:
            gi = np.mean([c[1] for c in goal])
            gj = np.mean([c[2] for c in goal])

            def h(s, _gi=gi, _gj=gj):
                return math.hypot(s[1] - _gi, s[2] - _gj)

        result = None
        for via_cost in (H.VIA_COST, 120, 400, 1200, 4000):
            end, came, on_plane = search(src_cells, goal, plane_ok,
                                         tmask, via_ok, via_cost, h)
            if not end:
                continue
            laid, vpts = unwind(end, came, on_plane)
            if h2h_ok(vpts, vias + new_vias, H.VIA_DRILL):
                result = (laid, vpts, on_plane, via_cost)
                break

        if not result:
            print("  %-10s NO PATH to %s's connected copper" % (tgt, net))
            continue

        laid, vpts, on_plane, via_cost = result
        if not laid and not vpts:
            print("  %-10s search ended where it started -- NO-OP, rejected "
                  "(this is what a false success looks like)" % tgt)
            continue
        emitted = H.emit(net, laid, vpts)
        added += emitted
        for i, j in vpts:
            new_vias.append(dict(x=H.g2mm(i), y=H.g2mm(j),
                                 d=H.VIA_D, drill=H.VIA_DRILL, net=net))
        print("  %-10s CLOSED on %-14s %3d seg, %d via, %5.2f mm  %-8s%s"
              % (tgt, net, len(emitted) - len(vpts), len(vpts),
                 len(laid) * H.STEP,
                 "-> plane" if on_plane else "-> pad",
                 "" if via_cost == H.VIA_COST else "  (via cost %d)" % via_cost))

    if not added:
        print("\nnothing added")
        return 1

    body = H.t.rstrip()
    assert body.endswith(")")
    body = body[:-1].rstrip("\n") + "\n" + "\n".join(added) + "\n)\n"
    # handroute reads in text mode, so CRLF arrives as \n and writing it back
    # straight converts the whole file to LF -- a one-line change becomes a
    # 16000-line diff. Restore whatever the ORIGINAL used.
    with open(SRC, "rb") as fh:
        crlf = b"\r\n" in fh.read(65536)
    open(DST, "w", encoding="utf-8",
         newline="\r\n" if crlf else "\n").write(body)
    print("\nwrote %s" % DST)

    # SELF-VERIFY. Every claim above is a prediction about copper; this reads
    # the file back and checks it. Reporting "CLOSED" without this is how a
    # tool ends up lying, which has happened here more than once.
    p2, s2, v2, z2 = pt.parse(DST)
    r2 = pt.analyse(p2, s2, v2, z2)
    still = {(q["ref"], q["pad"]) for n in r2 for q in r2[n]["stray"]}
    print("verified against the written file:")
    for tgt in TARGETS:
        ref, num = tgt.split(".", 1)
        was_target = any(ref == a and num == b
                         for a, b in [(t.split(".", 1)) for t in TARGETS])
        if (ref, num) in still:
            print("   %-10s STILL OPEN" % tgt)
        elif was_target:
            print("   %-10s closed" % tgt)
    print("   total open pads now: %d" % len(still))
    print("Still run check_board.py and check_drc.py -- connectivity is not "
          "clearance.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
