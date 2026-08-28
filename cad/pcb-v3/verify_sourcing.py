"""Cross-check each sourced part's PACKAGE against the real land on the board.

Sourcing a part is only half the job. JLCPCB places the physical package onto
the land WE drew; if the package we bought is not the package we drew, the part
lands on the wrong pads and the board is scrap. So measure the land.

GEOMETRY NOTE, learned the hard way twice in this project:
  * KiCad's .kicad_pcb is Y-DOWN, so a positive footprint angle is CLOCKWISE:
        gx =  px*cos(a) + py*sin(a)
        gy = -px*sin(a) + py*cos(a)
  * Do NOT bound a pad with its circumscribed circle. That is only correct when
    you need an orientation-independent envelope; for measuring a LAND it
    inflates every elongated pad. The first version of this file did exactly
    that and invented three package mismatches that were not there -- L1's land
    read 4.256 mm when it is 3.256. Rotate the four corners instead.
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")
import sexp
from make_bom_cpl import SRC

BOARD = "pcb-v3-handoff.kicad_pcb"
text = open(BOARD, encoding="utf-8", errors="replace").read()
root = sexp.parse(text)
k, kd, s, f = sexp.kids, sexp.kid, sexp.s, sexp.f

# LAND envelopes (pad extent, NOT body size), long side, in mm.
# A 2-terminal land always overhangs the body at both ends, so these are
# larger than the package name suggests -- an 0402 body is 1.0 mm and its
# land is ~1.4 mm. Ranges are deliberately generous; this test exists to
# catch a WRONG PACKAGE FAMILY, not to grade the land pattern.
EXPECT = {
    "0402": (1.20, 1.70, 2),
    "0603": (2.00, 2.80, 2),
    "1008": (2.90, 3.70, 2),
}


def corners(px, py, w, h, pang, ang):
    """The 4 corners of one pad in footprint coords, both rotations applied."""
    out = []
    ca, sa = math.cos(pang), math.sin(pang)
    for sx in (-0.5, 0.5):
        for sy in (-0.5, 0.5):
            lx, ly = sx * w, sy * h
            # pad's own rotation (same Y-down convention)
            rx = lx * ca + ly * sa
            ry = -lx * sa + ly * ca
            x, y = px + rx, py + ry
            gx = x * math.cos(ang) + y * math.sin(ang)
            gy = -x * math.sin(ang) + y * math.cos(ang)
            out.append((gx, gy))
    return out


rows = []
for fp in k(root, "footprint"):
    ref = "?"
    for pr in k(fp, "property"):
        if s(pr[1]) == "Reference":
            ref = s(pr[2])
    if ref not in SRC:
        continue
    at = kd(fp, "at")
    ang = math.radians(f(at[3]) if len(at) > 3 else 0.0)
    pts, n = [], 0
    for pad in k(fp, "pad"):
        pat, sz = kd(pad, "at"), kd(pad, "size")
        pang = math.radians(f(pat[3]) if len(pat) > 3 else 0.0)
        pts += corners(f(pat[1]), f(pat[2]), f(sz[1]), f(sz[2]), pang, ang)
        n += 1
    if not pts:
        continue
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    rows.append((ref, max(xs) - min(xs), max(ys) - min(ys), n,
                 SRC[ref][0], SRC[ref][3]))

print("%-6s %8s %8s %5s  %-11s %s" % ("ref", "landX", "landY", "pads", "LCSC", "part bought"))
bad = checked = 0
for ref, dx, dy, n, lc, desc in sorted(rows):
    long_side = max(dx, dy)
    for fam, (lo, hi, pads) in EXPECT.items():
        if fam in desc:
            checked += 1
            ok = (lo <= long_side <= hi) and n == pads
            verdict = "OK" if ok else (
                "*** MISMATCH: %s land should be %.2f-%.2f mm, got %.3f ***"
                % (fam, lo, hi, long_side))
            bad += 0 if ok else 1
            break
    else:
        verdict = "(IC/module - land traced by hand, see PART-LIBRARY.md)"
    print("%-6s %8.3f %8.3f %5d  %-11s %-46s %s"
          % (ref, dx, dy, n, lc, desc[:46], verdict))

print()
print("2-terminal lands checked : %d" % checked)
print("package mismatches       : %d" % bad)
if checked == 0:                      # a check that checks nothing must fail
    print("*** THIS TEST GRADED NOTHING - treat as a FAILURE ***")
    sys.exit(2)
sys.exit(1 if bad else 0)
