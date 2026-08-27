"""
Extract every pad from pcb-v2.kicad_pcb and report it in BOTH candidate
board-local frames, so the sign discrepancy flagged in NEXT-SESSION Task C
can be settled from the file instead of assumed.

DESIGN-SPEC §1 makes two statements that cannot both be literally true:
    "Board-local coordinates in this document are `global - origin`."
    "Board-local +Y is KiCad-up."
KiCad file Y increases DOWNWARD, so "+Y is KiCad-up" requires
`origin_y - global_y`, not `global_y - origin_y`.

Frame A ("literal")  : x = gx - ox ,  y = gy - oy
Frame B ("KiCad-up") : x = gx - ox ,  y = oy - gy

Read-only. Does not modify the board.
"""
import re
import sys
from collections import defaultdict

PCB = sys.argv[1] if len(sys.argv) > 1 else "pcb-v2.kicad_pcb"
OX, OY = 148.5011, 105.0036          # DESIGN-SPEC §1 footprint origin

raw = open(PCB, "rb").read().decode("utf-8", "replace")

# Pull every (pad ...) block by paren-matching, so a format change cannot make
# a regex silently return zero rows (DESIGN-SPEC §7 trap 3).
pads = []
i = 0
while True:
    i = raw.find("(pad ", i)
    if i < 0:
        break
    depth, j = 0, i
    while j < len(raw):
        if raw[j] == "(":
            depth += 1
        elif raw[j] == ")":
            depth -= 1
            if depth == 0:
                break
        j += 1
    pads.append(raw[i:j + 1])
    i = j + 1

print(f"pad blocks found by paren-matching : {len(pads)}")
if len(pads) == 0:
    sys.exit("NO PADS PARSED — the format changed. Do not trust anything below.")

rows = []
for blk in pads:
    m = re.match(r'\(pad\s+"([^"]*)"\s+(\S+)\s+(\S+)', blk)
    num, ptype, shape = (m.group(1), m.group(2), m.group(3)) if m else ("?", "?", "?")
    mat = re.search(r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\)", blk)
    if not mat:
        continue
    gx, gy = float(mat.group(1)), float(mat.group(2))
    msz = re.search(r"\(size\s+(-?[\d.]+)\s+(-?[\d.]+)\)", blk)
    sx, sy = (float(msz.group(1)), float(msz.group(2))) if msz else (0, 0)
    mly = re.search(r"\(layers\s+([^)]*)\)", blk)
    layers = mly.group(1).replace('"', "").strip() if mly else ""
    mnet = re.search(r'\(net\s+\d+\s+"([^"]*)"\)', blk)
    net = mnet.group(1) if mnet else ""
    rows.append(dict(num=num, type=ptype, shape=shape, gx=gx, gy=gy,
                     sx=sx, sy=sy, layers=layers, net=net,
                     ax=gx - OX, ay=gy - OY,          # frame A
                     bx=gx - OX, by=OY - gy))         # frame B

print(f"pads with an (at ...)              : {len(rows)}")

# ---- the pogo pads: round, on B.Cu, ~2.2 diameter ----
pogo = [r for r in rows
        if "B.Cu" in r["layers"] and abs(r["sx"] - 2.2) < 0.3 and abs(r["sx"] - r["sy"]) < 0.01]
print(f"round B.Cu pads of ~2.2 dia        : {len(pogo)}   (DESIGN-SPEC says 10)")

print("\n  pad   net            global x, y        FRAME A (gy-oy)     FRAME B (oy-gy)")
print("  " + "-" * 78)
for r in sorted(pogo, key=lambda r: (r["gx"], r["gy"])):
    print(f"  {r['num']:>4}  {r['net']:<12}  {r['gx']:8.3f} {r['gy']:8.3f}"
          f"   {r['ax']:7.3f} {r['ay']:7.3f}"
          f"     {r['bx']:7.3f} {r['by']:7.3f}")


def block(rs, label):
    if not rs:
        return
    print(f"\n  {label}: {len(rs)} pads")
    for f, xk, yk in (("A", "ax", "ay"), ("B", "bx", "by")):
        xs = [r[xk] for r in rs]
        ys = [r[yk] for r in rs]
        print(f"    frame {f}: x {min(xs):+7.3f} .. {max(xs):+7.3f}"
              f"    y {min(ys):+7.3f} .. {max(ys):+7.3f}"
              f"   (bbox +-1.1 -> {min(xs)-1.1:+7.3f}..{max(xs)+1.1:+7.3f},"
              f" {min(ys)-1.1:+7.3f}..{max(ys)+1.1:+7.3f})")
    ys = sorted({round(r["ay"], 3) for r in rs})
    xs = sorted({round(r["ax"], 3) for r in rs})
    print(f"    distinct x centres: {xs}")
    print(f"    distinct y centres: {ys}   -> {len(ys)} rows")


left = [r for r in pogo if r["ax"] < 0]
right = [r for r in pogo if r["ax"] > 0]
block(left, "LEFT block  (-x)  = J4  (6-pin, per Pin Test Procedure)")
block(right, "RIGHT block (+x)  = J11 (4-pin, per Pin Test Procedure)")

# ---- everything else, for context ----
print("\n\n  --- all other pads, grouped by footprint-ish net ---")
byn = defaultdict(list)
for r in rows:
    if r in pogo:
        continue
    byn[r["net"]].append(r)
for net in sorted(byn):
    rs = byn[net]
    xs = [r["ax"] for r in rs]
    ys = [r["ay"] for r in rs]
    print(f"  {net or '(none)':<12} {len(rs):>3} pads   frame A"
          f"  x {min(xs):+7.3f}..{max(xs):+7.3f}   y {min(ys):+7.3f}..{max(ys):+7.3f}")
