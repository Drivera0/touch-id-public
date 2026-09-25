"""
verify_fab.py -- read the PLOTTED files back and check them against the board.
Nothing here trusts the generator; it re-derives everything from the output.
"""
import re, sys, math
sys.path.insert(0, "/mnt/user-data/uploads/touchid/cad/carrier-v1")
FAB = "carrier-fab/"
BX0, BX1, BY0, BY1 = -16.0, 31.0, -20.0, 38.0   # from gen_carrier.py

fails = []
def FAIL(m): fails.append(m)

# ---- drill files: Excellon, INCH or METRIC, with tool table ----
def read_drl(path):
    txt = open(path).read()
    metric = "METRIC" in txt
    tools = {t: float(d) for t, d in re.findall(r"T(\d+)C([\d.]+)", txt)}
    holes, cur = [], None
    for line in txt.splitlines():
        m = re.fullmatch(r"T(\d+)", line.strip())
        if m and m.group(1) in tools: cur = tools[m.group(1)]; continue
        m = re.fullmatch(r"X([-\d.]+)Y([-\d.]+)", line.strip())
        if m and cur is not None:
            x, y = float(m.group(1)), float(m.group(2))
            if not metric: x, y = x*25.4, y*25.4
            holes.append((round(x,4), round(y,4), round(cur,3)))
    return holes, metric

pth, pth_metric = read_drl(FAB+"carrier-v1-PTH.drl")
npth, _         = read_drl(FAB+"carrier-v1-NPTH.drl")
print(f"PTH  holes: {len(pth):3d}   units: {'mm' if pth_metric else 'inch'}")
print(f"NPTH holes: {len(npth):3d}")

# drill origin = aux axis = (BX0, BY1); gerber/drill Y is UP, KiCad Y is DOWN
def to_board(x, y): return (round(x + BX0, 3), round(BY1 - y, 3))

from collections import Counter
print("\nPTH by diameter:")
for d, n in sorted(Counter(h[2] for h in pth).items()):
    print(f"   O{d:<6} x{n}")
print("NPTH by diameter:")
for d, n in sorted(Counter(h[2] for h in npth).items()):
    print(f"   O{d:<6} x{n}")

EXPECT_PTH = {1.05: 7, 1.02: 5, 1.0: 2+2, 0.4: 4}   # pogo+dowel, J2, J1+TP, vias
got = Counter(h[2] for h in pth)
for d, n in EXPECT_PTH.items():
    if got.get(d, 0) != n:
        FAIL(f"PTH O{d}: expected {n}, got {got.get(d,0)}")
if len(npth) != 4 or set(h[2] for h in npth) != {3.2}:
    FAIL(f"NPTH: expected 4 x O3.2, got {len(npth)} {set(h[2] for h in npth)}")

# ---- the five pogo holes, back in board coordinates ----
# Expected positions come straight out of the DUT's OWN board file, so this
# check runs gerber -> drill file -> board coords -> pcb-v7-zero-opens.kicad_pcb
# without trusting anything the carrier generator produced.
DUT = "/mnt/user-data/uploads/touchid/cad/v7-release/pcb-v7-zero-opens.kicad_pcb"
dsrc = open(DUT, encoding="utf-8").read()
def blocks(s, tag):
    i=0; out=[]
    while True:
        i = s.find("("+tag+" ", i)
        if i < 0: break
        d=0; j=i
        while True:
            if s[j]=="(": d+=1
            elif s[j]==")":
                d-=1
                if d==0: break
            j+=1
        out.append(s[i:j+1]); i=j+1
    return out
want = []
for fp in blocks(dsrc, "footprint"):
    nm  = re.search(r'\(footprint "([^"]+)"', fp).group(1)
    ref = re.search(r'\(property\s+"Reference"\s+"([^"]*)"', fp)
    ref = ref.group(1) if ref else ""
    fat = re.search(r'\n\s*\(at ([-\d.]+) ([-\d.]+)', fp)
    ox, oy = float(fat.group(1)), float(fat.group(2))
    if ref != "J3" and not nm.endswith(":MH"): continue
    for pd in blocks(fp, "pad"):
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+)', pd)
        want.append((ox+float(at.group(1)), oy+float(at.group(2))))
want = sorted(want)
print(f"\nDUT file gave {len(want)} reference points (5 x J3 + 2 x MH)")
if len(want) != 7: FAIL(f"expected 7 reference points from the DUT, got {len(want)}")
print("Pogo + dowel holes recovered from the DRILL FILE (board coords):")
pogo = sorted([to_board(h[0], h[1]) for h in pth if h[2] == 1.05])
for (gx, gy), (wx, wy) in zip(pogo, want):
    ok = abs(gx-wx) < 0.002 and abs(gy-wy) < 0.002
    print(f"   ({gx:7.3f},{gy:6.3f})  vs board ({wx:6.2f},{wy:5.2f})  {'OK' if ok else 'MISMATCH'}")
    if not ok: FAIL(f"drill hole {(gx,gy)} != board {(wx,wy)}")

# ---- Edge.Cuts extents ----
edge = open(FAB+"carrier-v1-Edge_Cuts.gbr").read()
fmt = re.search(r"%FSLAX(\d)(\d)Y\d\d\*%", edge)
dec = int(fmt.group(2))
pts = [(int(a)/10**dec, int(b)/10**dec)
       for a, b in re.findall(r"X(-?\d+)Y(-?\d+)D0[12]\*", edge)]
xs, ys = [p[0] for p in pts], [p[1] for p in pts]
bw, bh = max(xs)-min(xs), max(ys)-min(ys)
print(f"\nEdge.Cuts: {bw:.3f} x {bh:.3f} mm  (board is {BX1-BX0:.0f} x {BY1-BY0:.0f})")
if abs(bw-(BX1-BX0)) > 0.02 or abs(bh-(BY1-BY0)) > 0.02:
    FAIL(f"outline {bw:.3f} x {bh:.3f} != {BX1-BX0} x {BY1-BY0}")
if abs(min(xs)) > 0.02 or abs(min(ys)) > 0.02:
    FAIL(f"outline not at the drill origin: starts at ({min(xs):.3f},{min(ys):.3f})")

# ---- every hole inside the outline ----
for (x, y, d) in pth + npth:
    if not (0 <= x <= bw and 0 <= y <= bh):
        FAIL(f"hole O{d} at ({x:.2f},{y:.2f}) is OUTSIDE the outline")

# ---- layer set ----
import os, glob
have = sorted(os.path.basename(f) for f in glob.glob(FAB+"*.gbr"))
need = ["F_Cu","B_Cu","F_Mask","B_Mask","F_Silkscreen","B_Silkscreen",
        "F_Paste","B_Paste","Edge_Cuts"]
print(f"\ngerber layers: {len(have)} files")
for n in need:
    if not any(n+".gbr" in h for h in have): FAIL(f"missing layer {n}")

print()
for f in fails: print("FAIL:", f)
print(("VERIFY: %d failures" % len(fails)) if fails else "VERIFY: 0 failures")
sys.exit(1 if fails else 0)
