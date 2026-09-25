"""
check_carrier.py -- go/no-go for carrier-v1, in the spirit of preflight.py.
Verifies the generated board against the REAL DUT file, not against this
repo's prose.  Also renders carrier-preview.png.
"""
import os, re, sys, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
PCB  = os.path.join(HERE, "carrier-v1.kicad_pcb")
DUT  = os.path.normpath(os.path.join(HERE, "..", "v7-release", "pcb-v7-zero-opens.kicad_pcb"))

sys.path.insert(0, HERE)
import gen_carrier as _G          # single source of truth for nets, silk, outline

fails, warns = [], []
def FAIL(m): fails.append(m)
def WARN(m): warns.append(m)

src = open(PCB, encoding="utf-8").read()

# ---- 0. s-expression balance
d = 0
for c in src:
    if c == "(": d += 1
    elif c == ")": d -= 1
    if d < 0: FAIL("unbalanced parens (went negative)")
if d != 0: FAIL(f"unbalanced parens (ends at {d})")

def blocks(s, tag):
    i = 0; out = []
    while True:
        i = s.find("(" + tag + " ", i)
        if i < 0: break
        k = 0; j = i
        while True:
            if s[j] == "(": k += 1
            elif s[j] == ")":
                k -= 1
                if k == 0: break
            j += 1
        out.append(s[i:j+1]); i = j + 1
    return out

# ---- parse our pads
pads = []          # (ref, num, ax, ay, w, h, drill, net)
for fp in blocks(src, "footprint"):
    ref = re.search(r'\(footprint "carrier:([^"]+)"', fp).group(1)
    at  = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', fp)
    ox, oy = float(at.group(1)), float(at.group(2))
    rot = float(at.group(3)) if at.group(3) else 0.0
    for pd in blocks(fp, "pad"):
        pat = re.search(r'\(at ([-\d.]+) ([-\d.]+)', pd)
        sz  = re.search(r'\(size ([\d.]+) ([\d.]+)\)', pd)
        dr  = re.search(r'\(drill ([\d.]+)\)', pd)
        nt  = re.search(r'\(net \d+ "([^"]*)"\)', pd)
        num = re.match(r'\(pad "([^"]*)"', pd).group(1)
        dx, dy = float(pat.group(1)), float(pat.group(2))
        if abs(rot - 90) < 1e-6: dx, dy = -dy, dx
        pads.append((ref, num, ox+dx, oy+dy, float(sz.group(1)), float(sz.group(2)),
                     float(dr.group(1)) if dr else None, nt.group(1) if nt else ""))

# ---- 1. pogo + dowel positions vs the REAL DUT file
dsrc = open(DUT, encoding="utf-8").read()
dut_j3, dut_mh = [], []
for fp in blocks(dsrc, "footprint"):
    nm  = re.search(r'\(footprint "([^"]+)"', fp).group(1)
    ref = re.search(r'\(property\s+"Reference"\s+"([^"]*)"', fp)
    ref = ref.group(1) if ref else ""
    fat = re.search(r'\n\s*\(at ([-\d.]+) ([-\d.]+)', fp)
    ox, oy = float(fat.group(1)), float(fat.group(2))
    for pd in blocks(fp, "pad"):
        pat = re.search(r'\(at ([-\d.]+) ([-\d.]+)', pd)
        x, y = ox + float(pat.group(1)), oy + float(pat.group(2))
        if ref == "J3": dut_j3.append((x, y))
        if nm.endswith(":MH"): dut_mh.append((x, y))
dut_j3.sort(); dut_mh.sort()

ours_pp = sorted((x, y) for (r, n, x, y, *_ ) in pads if r.startswith("PP"))
ours_dw = sorted((x, y) for (r, n, x, y, *_ ) in pads if r.startswith("DW"))
if len(ours_pp) != 5: FAIL(f"expected 5 pogo pads, got {len(ours_pp)}")
for a, b in zip(ours_pp, dut_j3):
    if abs(a[0]-b[0]) > 1e-6 or abs(a[1]-b[1]) > 1e-6:
        FAIL(f"pogo {a} != DUT J3 pad {b}")
for a, b in zip(ours_dw, dut_mh):
    if abs(a[0]-b[0]) > 1e-6 or abs(a[1]-b[1]) > 1e-6:
        FAIL(f"dowel {a} != DUT mounting hole {b}")

# ---- 2. pad-to-pad copper clearance
MINCLR = 0.20
for i in range(len(pads)):
    for j in range(i+1, len(pads)):
        ra, na, ax, ay, aw, ah, ad, anet = pads[i]
        rb, nb, bx, by, bw, bh, bd, bnet = pads[j]
        if ra == rb: continue
        if anet and anet == bnet: continue
        # Axis-aligned rectangle separation, NOT centre-distance minus the
        # largest dimension.  The crude version treated every pad as a circle
        # of its longest side and reported -0.600 mm on the oblong pogo row,
        # which is 0.400 mm clear in X.  Checkers lie more than the board.
        gap = max(abs(ax-bx) - (aw+bw)/2.0, abs(ay-by) - (ah+bh)/2.0)
        if gap < MINCLR:
            FAIL(f"pad clearance {ra}.{na} <-> {rb}.{nb} = {gap:.3f} mm (< {MINCLR})")

# same-footprint neighbours (the 2.0 mm pogo row) reported as info
row = sorted([(x, r) for (r, n, x, y, *_ ) in pads if r.startswith("PP")])
for k in range(len(row)-1):
    g = row[k+1][0] - row[k][0] - _G.POGO_PAD_X
    if g < MINCLR: FAIL(f"pogo row gap {row[k][1]}->{row[k+1][1]} = {g:.3f} mm")
# annular ring on the HAND-SOLDERED joints -- the only ones an iron touches
for ref, hole, px, py in [("PP", _G.POGO_DRILL, _G.POGO_PAD_X, _G.POGO_PAD_Y),
                          ("DW", _G.DOWEL_DRILL, _G.DOWEL_PAD, _G.DOWEL_PAD)]:
    ring = (max(px, py) - hole) / 2
    if ring < 0.45:
        FAIL(f"{ref}* annular ring {ring:.3f} mm -- too thin to hand-solder")

# ---- 3. everything inside the outline (outline is NOT centred on the DUT)
BX0, BX1, BY0, BY1 = _G.BX0, _G.BX1, _G.BY0, _G.BY1
for (r, n, x, y, w, h, d, net) in pads:
    m = max(w, h) / 2 + 0.3
    if x - m < BX0 or x + m > BX1 or y - m < BY0 or y + m > BY1:
        FAIL(f"{r}.{n} at ({x:.2f},{y:.2f}) too close to the board edge")

# ---- 4. nothing intrudes into the DUT's 20 x 19 footprint except PP*/DW*
for (r, n, x, y, w, h, d, net) in pads:
    if r.startswith("PP") or r.startswith("DW"): continue
    if -10.0 <= x <= 10.0 and -9.5 <= y <= 9.5:
        FAIL(f"{r}.{n} sits under the DUT footprint at ({x:.2f},{y:.2f})")

# ---- 5. XIAO module body (21 x 17.8) vs DUT footprint and board edge
xi = [(x, y) for (r, n, x, y, *_ ) in pads if r == "U1"]
cx = sum(p[0] for p in xi)/len(xi); cy = sum(p[1] for p in xi)/len(xi)
mx0, mx1, my0, my1 = cx-17.8/2, cx+17.8/2, cy-21.0/2, cy+21.0/2
if my0 <= 9.5: FAIL(f"XIAO body reaches y={my0:.2f}, overlaps DUT (top edge +9.50)")
if my1 > BY1: FAIL(f"XIAO body reaches y={my1:.2f}, past board edge {BY1}")
if mx0 < BX0 or mx1 > BX1: FAIL(f"XIAO body x {mx0:.2f}..{mx1:.2f} past the outline")
gap_dut = my0 - 9.5
gap_edge = BY1 - my1

# ---- 7. tracks and vias: parse
flat = re.sub(r'\s+', ' ', src)
tracks = [(float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)),
           float(m.group(5)), m.group(6), int(m.group(7)))
          for m in re.finditer(r'\(segment \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)'
                               r' \(width ([\d.]+)\) \(layer "([^"]+)"\) \(net (\d+)\)', flat)]
vias = [(float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)), int(m.group(5)))
        for m in re.finditer(r'\(via \(at ([-\d.]+) ([-\d.]+)\) \(size ([\d.]+)\)'
                             r' \(drill ([\d.]+)\) \(layers "F.Cu" "B.Cu"\) \(net (\d+)\)', flat)]
netname = {i: n for i, n in enumerate([m.group(1) for m in re.finditer(r'\(net \d+ "([^"]*)"\)', flat)])}
# net table comes from the generator -- a hardcoded copy here silently
# mislabelled every net the moment nRESET was added, and reported 22 blockers
# that were all the same drift.
NETS_ORDER = _G.NETS
nn = lambda i: NETS_ORDER[i] if i < len(NETS_ORDER) else str(i)
if not tracks: FAIL("no tracks parsed -- checker regex is wrong, not the board")

def seg_pt(px, py, x1, y1, x2, y2):
    dx, dy = x2-x1, y2-y1
    L2 = dx*dx + dy*dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px-x1)*dx + (py-y1)*dy)/L2))
    return math.hypot(px - (x1+t*dx), py - (y1+t*dy))

def seg_seg(a, b):
    ax1, ay1, ax2, ay2 = a; bx1, by1, bx2, by2 = b
    d1 = (ax2-ax1, ay2-ay1); d2 = (bx2-bx1, by2-by1)
    den = d1[0]*d2[1] - d1[1]*d2[0]
    if abs(den) > 1e-12:
        t = ((bx1-ax1)*d2[1] - (by1-ay1)*d2[0]) / den
        u = ((bx1-ax1)*d1[1] - (by1-ay1)*d1[0]) / den
        if 0 <= t <= 1 and 0 <= u <= 1: return 0.0
    return min(seg_pt(bx1, by1, *a), seg_pt(bx2, by2, *a),
               seg_pt(ax1, ay1, *b), seg_pt(ax2, ay2, *b))

# 7a. track <-> pad
for (x1, y1, x2, y2, w, lay, net) in tracks:
    for (r, n, px, py, pw, ph, d, pnet) in pads:
        if pnet and pnet == nn(net): continue
        if not d and lay != "F.Cu": continue          # SMD pads are F.Cu only
        g = seg_pt(px, py, x1, y1, x2, y2) - w/2 - max(pw, ph)/2
        if g < MINCLR:
            FAIL(f"track {nn(net)} on {lay} -> pad {r}.{n} gap {g:.3f} mm")

# 7b. track <-> track, same layer, different net
for i in range(len(tracks)):
    for j in range(i+1, len(tracks)):
        a_ = tracks[i]; b_ = tracks[j]
        if a_[5] != b_[5]: continue
        if nn(a_[6]) == nn(b_[6]): continue
        g = seg_seg(a_[:4], b_[:4]) - a_[4]/2 - b_[4]/2
        if g < MINCLR:
            FAIL(f"track {nn(a_[6])} <-> {nn(b_[6])} on {a_[5]} gap {g:.3f} mm")

# 7c. via <-> track / pad
for (vx, vy, vs, vd, vnet) in vias:
    for (x1, y1, x2, y2, w, lay, net) in tracks:
        if nn(net) == nn(vnet): continue
        g = seg_pt(vx, vy, x1, y1, x2, y2) - w/2 - vs/2
        if g < MINCLR: FAIL(f"via {nn(vnet)} -> track {nn(net)} gap {g:.3f} mm")
    for (r, n, px, py, pw, ph, d, pnet) in pads:
        if pnet == nn(vnet): continue
        g = math.hypot(vx-px, vy-py) - vs/2 - max(pw, ph)/2
        if g < MINCLR: FAIL(f"via {nn(vnet)} -> pad {r}.{n} gap {g:.3f} mm")

# ---- 6. mounting holes clear of everything
# NOTE: the MH footprints are themselves in `pads`, so skip them or every hole
# reports itself as a collision at -3.20 mm.  (First run did exactly that --
# see memory touchid-checkers-lie-more-than-the-board.)
for (hx, hy) in _G.MH:
    for (r, n, x, y, w, h, d, net) in pads:
        if r.startswith("MH"): continue
        g = math.hypot(hx-x, hy-y) - (3.2 + max(w,h))/2
        if g < 0.5: FAIL(f"MH at ({hx},{hy}) too close to {r}.{n} ({g:.2f} mm)")
    for (x1, y1, x2, y2, w, lay, net) in tracks:
        g = seg_pt(hx, hy, x1, y1, x2, y2) - 1.6 - w/2
        if g < 0.3: FAIL(f"MH at ({hx},{hy}) too close to track {nn(net)} ({g:.2f} mm)")
    for (vx, vy, vs, vd, vnet) in vias:
        g = math.hypot(hx-vx, hy-vy) - 1.6 - vs/2
        if g < 0.3: FAIL(f"MH at ({hx},{hy}) too close to via {nn(vnet)} ({g:.2f} mm)")

# ---- 7d. NO COPPER UNDER THE XIAO BODY except its own 14 lands.  The
# module's belly carries exposed pads: four round (SWCLK, SWDIO, GND, RST)
# 5.85 mm above centre, and two rectangles 8.6 mm below centre -- GND and
# VIN(5V).  VIN is why this matters: 5 V must never reach anything on this
# board.  The module sits flat, so foreign copper under it is a short.
# The forbidden strip is the module's BELLY, between the two land columns.
# Seeed's lands run 7.0-10.0 mm off centre, so nothing of ours may sit inside
# +-7.0; a track leaving a land at x = +-8.5 is fine and must not be flagged.
xb0, xb1 = -7.0, 7.0
yb0, yb1 = _G.XIAO_CY - _G.XIAO_BODY_H/2, _G.XIAO_CY + _G.XIAO_BODY_H/2
def in_xiao(x, y): return xb0 <= x <= xb1 and yb0 <= y <= yb1
for (x1, y1, x2, y2, w, lay, net) in tracks:
    steps = max(2, int(math.hypot(x2-x1, y2-y1) / 0.25))
    for kk in range(steps+1):
        t = kk/steps
        if in_xiao(x1+t*(x2-x1), y1+t*(y2-y1)):
            FAIL(f"track {nn(net)} on {lay} crosses the XIAO belly"); break
for (vx, vy, vs, vd, vnet) in vias:
    if in_xiao(vx, vy): FAIL(f"via {nn(vnet)} sits under the XIAO belly")

# ---- 7e. silkscreen legibility.  Three ways a label dies on a real board:
#   (a) it crosses a PAD  -- the mask opening eats the ink,
#   (b) it crosses a VIA  -- same thing, and this is what clipped the old
#       one-line "SWD ESC ..." legend at the nRST_R via (21.08, 15.88),
#   (c) it crosses ANOTHER LABEL -- unreadable mush.  All seven silk_overlap
#       warnings KiCad raised were of this kind, between my own text and the
#       auto-placed reference designators (now hidden).
# KiCad's stroke font advances about 0.78 x size per character; 0.78 is used
# here rather than a tighter estimate so the checker errs toward failing.
CHW, CHH = 0.78, 1.10

def silk_box(sx, sy, txt, sz, rot):
    tw, th_ = len(txt) * sz * CHW, sz * CHH
    if rot == 90: tw, th_ = th_, tw
    return (sx - tw/2, sx + tw/2, sy - th_/2, sy + th_/2)

SBOX = [(silk_box(*t), t) for t in _G.SILK]

for (bx0, bx1, by0, by1), (sx, sy, txt, sz, rot) in SBOX:
    for (r, n, px, py, pw, ph, d, pnet) in pads:
        if not (bx1 < px-pw/2 or bx0 > px+pw/2 or
                by1 < py-ph/2 or by0 > py+ph/2):
            FAIL(f'silk "{txt}" overlaps pad {r}.{n}')
            break
    for (vx, vy, vs, vd, vnet) in vias:
        if not (bx1 < vx-vs/2 or bx0 > vx+vs/2 or
                by1 < vy-vs/2 or by0 > vy+vs/2):
            FAIL(f'silk "{txt}" overlaps via {nn(vnet)} at ({vx}, {vy})')
            break

# silk LINES (the DUT outline box) get the same treatment: they must clear
# every pad and via, and must not run under a label.
for (lx1, ly1, lx2, ly2) in _G.SILK_LINES:
    hw = _G.SILK_LINE_W / 2.0
    ax0, ax1 = min(lx1, lx2) - hw, max(lx1, lx2) + hw
    ay0, ay1 = min(ly1, ly2) - hw, max(ly1, ly2) + hw
    for (r, n, px, py, pw, ph, d, pnet) in pads:
        if not (ax1 < px-pw/2 or ax0 > px+pw/2 or
                ay1 < py-ph/2 or ay0 > py+ph/2):
            FAIL(f"silk outline ({lx1},{ly1})->({lx2},{ly2}) overlaps pad {r}.{n}")
    for (vx, vy, vs, vd, vnet) in vias:
        if not (ax1 < vx-vs/2 or ax0 > vx+vs/2 or
                ay1 < vy-vs/2 or ay0 > vy+vs/2):
            FAIL(f"silk outline ({lx1},{ly1})->({lx2},{ly2}) overlaps a via")
    for (bx0, bx1, by0, by1), t in SBOX:
        if not (ax1 < bx0 or ax0 > bx1 or ay1 < by0 or ay0 > by1):
            FAIL(f'silk outline runs through label "{t[2]}"')

for i in range(len(SBOX)):
    (ax0, ax1, ay0, ay1), ta = SBOX[i]
    for j in range(i+1, len(SBOX)):
        (bx0, bx1, by0, by1), tb = SBOX[j]
        if not (ax1 < bx0 or ax0 > bx1 or ay1 < by0 or ay0 > by1):
            FAIL(f'silk "{ta[2]}" overlaps silk "{tb[2]}"')

# every visible label must also stay inside the board outline
for (bx0, bx1, by0, by1), (sx, sy, txt, sz, rot) in SBOX:
    if bx0 < _G.BX0 or bx1 > _G.BX1 or by0 < _G.BY0 or by1 > _G.BY1:
        FAIL(f'silk "{txt}" runs off the board edge')

# ---- 8. THE RULE: no F.Cu copper under the DUT except PP*/DW* pads.
# The DUT's bottom face carries exposed gold (J4, J11, TP1-TP10) and hovers
# ~1.5 mm over this surface.
DX0, DX1, DY0, DY1 = -10.0, 10.0, -9.5, 9.5
def in_dut(x, y): return DX0 <= x <= DX1 and DY0 <= y <= DY1
for (x1, y1, x2, y2, w, lay, net) in tracks:
    if lay != "F.Cu": continue
    steps = max(2, int(math.hypot(x2-x1, y2-y1) / 0.25))
    for k in range(steps+1):
        t = k/steps
        if in_dut(x1+t*(x2-x1), y1+t*(y2-y1)):
            FAIL(f"F.Cu track {nn(net)} enters the DUT footprint "
                 f"({x1},{y1})->({x2},{y2})")
            break
for (vx, vy, vs, vd, vnet) in vias:
    if in_dut(vx, vy): FAIL(f"via {nn(vnet)} at ({vx},{vy}) sits under the DUT")

# ---- 9. CONNECTIVITY. The checks above prove nothing SHORTS; this proves
# nothing is OPEN.  Union-find over pads, track endpoints, T-junctions and
# vias, per layer, with vias and through-hole pads bridging the two layers.
par = {}
def find(a):
    par.setdefault(a, a)
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
def uni(a, b): par[find(a)] = find(b)

EPS = 0.01
def on_seg(px, py, t):
    return seg_pt(px, py, *t[:4]) <= EPS

for i, t in enumerate(tracks):
    uni(("t", i, t[5]), ("t", i, t[5]))
# track-to-track, same layer: shared endpoint OR endpoint lying on the other
for i in range(len(tracks)):
    for j in range(i+1, len(tracks)):
        a_, b_ = tracks[i], tracks[j]
        if a_[5] != b_[5]: continue
        pts = [(a_[0], a_[1]), (a_[2], a_[3])]
        qts = [(b_[0], b_[1]), (b_[2], b_[3])]
        if any(on_seg(px, py, b_) for px, py in pts) or \
           any(on_seg(qx, qy, a_) for qx, qy in qts):
            uni(("t", i, a_[5]), ("t", j, b_[5]))
# pads
for (r, n, px, py, pw, ph, d, pnet) in pads:
    if not pnet: continue
    layers = ["F.Cu", "B.Cu"] if d else ["F.Cu"]
    key = ("p", r, n)
    par.setdefault(key, key)
    for i, t in enumerate(tracks):
        if t[5] not in layers: continue
        if seg_pt(px, py, *t[:4]) <= max(pw, ph)/2 + EPS:
            uni(key, ("t", i, t[5]))
# vias bridge layers
for (vx, vy, vs, vd, vnet) in vias:
    vk = ("v", vx, vy); par.setdefault(vk, vk)
    for i, t in enumerate(tracks):
        if seg_pt(vx, vy, *t[:4]) <= vs/2 + EPS:
            uni(vk, ("t", i, t[5]))

bynet = {}
for (r, n, px, py, pw, ph, d, pnet) in pads:
    if pnet: bynet.setdefault(pnet, []).append((r, n))
for net, plist in sorted(bynet.items()):
    if len(plist) < 2: continue
    roots = {find(("p", r, n)) for (r, n) in plist}
    if len(roots) > 1:
        groups = {}
        for (r, n) in plist: groups.setdefault(find(("p", r, n)), []).append(f"{r}.{n}")
        FAIL(f"net {net} is OPEN -- {len(roots)} islands: " +
             " | ".join(",".join(v) for v in groups.values()))
print("connectivity      : " + ", ".join(
    f"{net}({len(pl)})" for net, pl in sorted(bynet.items()) if len(pl) > 1))

# ---- report
print(f"DUT J3 pads       : {dut_j3}")
print(f"carrier pogo holes: {ours_pp}")
print(f"DUT mount holes   : {dut_mh}")
print(f"carrier dowels    : {ours_dw}")
print(f"pads total        : {len(pads)}")
print(f"pogo row gap      : {row[1][0]-row[0][0]-_G.POGO_PAD_X:.3f} mm copper-to-copper")
print(f"hand-solder rings : PP {(_G.POGO_PAD_Y-_G.POGO_DRILL)/2:.3f} mm (in Y), "
      f"DW {(_G.DOWEL_PAD-_G.DOWEL_DRILL)/2:.3f} mm")
print(f"XIAO body         : x {mx0:.2f}..{mx1:.2f}  y {my0:.2f}..{my1:.2f}")
print(f"  gap to DUT      : {gap_dut:.2f} mm")
print(f"  gap to edge     : {gap_edge:.2f} mm")
print(f"tracks / vias     : {len(tracks)} / {len(vias)}")
print(f"F.Cu under DUT    : none (rule enforced)")
print(f"copper under XIAO : none in x +-7.0 (belly pads GND / VIN(5V) / SWD)")
print()
for w in warns: print("WARN:", w)
for f in fails: print("FAIL:", f)
print(("PREFLIGHT: %d blockers" % len(fails)) if fails else "PREFLIGHT: 0 blockers")

# ---------------- preview ----------------
fig, ax = plt.subplots(figsize=(7.2, 8.6), dpi=170)
ax.add_patch(Rectangle((BX0, BY0), BX1-BX0, BY1-BY0, fc="#12502f", ec="#0a3b22", lw=2))
for (x1, y1, x2, y2, w, lay, net) in tracks:
    ax.plot([x1, x2], [y1, y2], color="#d9a441" if lay == "F.Cu" else "#7fa7d4",
            lw=1.3 if w < 0.7 else 2.0, zorder=2, alpha=0.95)
for (vx, vy, vs, vd, vnet) in vias:
    ax.add_patch(Circle((vx, vy), vs/2, fc="#e8c46a", ec="none", zorder=6))
    ax.add_patch(Circle((vx, vy), vd/2, fc="#0d2b1a", ec="none", zorder=7))
# DUT outline
ax.add_patch(Rectangle((-10, -9.5), 20, 19, fc="none", ec="white", lw=1.4, ls="--", zorder=4))
ax.text(-10.4, 0, "your board\n20 x 19", ha="right", va="center",
        color="white", fontsize=6.5, zorder=5)
# XIAO body
ax.add_patch(Rectangle((mx0, my0), 17.8, 21.0, fc="none", ec="#9fe0ff", lw=1.2, ls=":", zorder=4))
ax.text(mx0-1.0, cy, "XIAO\nRP2040", ha="right", va="center",
        color="#9fe0ff", fontsize=6.5)
for (r, n, x, y, w, h, d, net) in pads:
    col = "#e8c46a"
    ax.add_patch(Circle((x, y), max(w, h)/2, fc=col, ec="none", zorder=6) if w == h
                 else Rectangle((x-w/2, y-h/2), w, h, fc=col, ec="none", zorder=6))
    if d: ax.add_patch(Circle((x, y), d/2, fc="#0d2b1a", ec="none", zorder=7))
for (hx, hy) in _G.MH:
    ax.add_patch(Circle((hx, hy), 1.6, fc="#0d2b1a", ec="#cccccc", lw=0.8, zorder=6))
# silkscreen also straight out of the generator
G = _G
for (x, y, t, sz, rot) in G.SILK:
    ax.text(x, y, t, ha="center", va="center", color="white", rotation=rot,
            fontsize=max(3.6, sz*5.0), zorder=8)
pad_ = 6.0
ax.set_xlim(BX0-pad_, BX1+pad_); ax.set_ylim(BY1+pad_, BY0-pad_)   # Y-DOWN, as KiCad
ax.set_aspect("equal"); ax.axis("off")
ax.set_title(f"TouchID carrier v1 — {BX1-BX0:.0f} x {BY1-BY0:.0f} mm, 2 layer "
             f"(KiCad view, Y down)", fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "carrier-preview.png"), facecolor="#1a1a1a")
print("wrote carrier-preview.png")
sys.exit(1 if fails else 0)
