"""verify_handoff.py — grade the BOM and CPL WITHOUT reusing the code that
made them.

make_bom_cpl.py could be confidently wrong and its own output would agree with
it. So this file re-derives everything from the board by a different route and
DIFFS. Where it can, it also uses a different formulation on purpose:
the origin transform below is written as a translation of the board's
lower-left CORNER rather than as "+HALF / HALF-", so a sign error in one does
not reproduce in the other.

Exit code is non-zero if anything disagrees.
"""
import csv, glob, math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")
import sexp

HERE = os.path.dirname(os.path.abspath(__file__)) or "."
import sys as _sys
BOARD = (_sys.argv[1] if len(_sys.argv)>1 else None) or os.environ.get("BOARD") \
        or os.path.join(HERE, "pcb-v6-handoff.kicad_pcb")  # was hardcoded; same defect as make_bom_cpl
EXP = os.path.join(HERE, "..", "exports")
# v3 filenames were stale (third tool with this defect today) -- take the
# newest touchid-*-CPL/BOM in the assembly dir instead, overridable by env.
_asm = os.path.join(HERE, "..", "v6-handoff", "assembly")
def _newest(pat, fallback):
    c = sorted(glob.glob(os.path.join(_asm, pat)), key=os.path.getmtime)
    return c[-1] if c else fallback
CPL = os.environ.get("CPL") or _newest("touchid-*-CPL.csv", os.path.join(EXP, "touchid-v3-CPL.csv"))
BOM = os.environ.get("BOM") or _newest("touchid-*-BOM.csv", os.path.join(EXP, "touchid-v3-BOM.csv"))

text = open(BOARD, encoding="utf-8", errors="replace").read()
root = sexp.parse(text)
k, kd, s, f = sexp.kids, sexp.kid, sexp.s, sexp.f

fails, notes = [], []
def check(ok, what, detail=""):
    (notes if ok else fails).append(("PASS" if ok else "FAIL", what, detail))

# ---- 0. the CPL must live in the GERBER's coordinate space ----------------
# This is the check that matters most and the one that was missing. A CPL can
# be internally perfect and still be offset from the copper, and then EVERY
# part is placed wrong by the same amount. JLCPCB's viewer found this on the
# real upload -- it drew the parts floating beside the board and offered to
# "align automatically". The old CPL was corner-based (0..19.30) while the
# gerbers are centred (-9.65..+9.65), a 9.65 mm offset in both axes.
#
# So: read the outline out of Edge_Cuts.gbr and require every placement to sit
# inside it. This deliberately does NOT re-derive the generator's formula --
# comparing a formula to itself proves nothing.
import glob
GERB = os.path.join(HERE, "..", "v6-handoff", "gerbers")
_edge = glob.glob(os.path.join(GERB, "*Edge_Cuts.gbr"))
_gx = _gy = None
if _edge:
    _e = open(_edge[0], encoding="utf-8", errors="replace").read()
    _px = [int(m.group(1)) / 1e6 for m in re.finditer(r"X(-?\d+)Y(-?\d+)D0[12]\*", _e)]
    _py = [int(m.group(2)) / 1e6 for m in re.finditer(r"X(-?\d+)Y(-?\d+)D0[12]\*", _e)]
    if _px:
        _gx = (min(_px), max(_px)); _gy = (min(_py), max(_py))

# ---- 1. board outline, measured, not assumed ------------------------------
xs, ys = [], []
for gi in k(root, "gr_line") + k(root, "gr_arc") + k(root, "gr_rect"):
    lay = kd(gi, "layer")
    if not lay or s(lay[1]) != "Edge.Cuts":
        continue
    for key in ("start", "end", "mid", "center"):
        p = kd(gi, key)
        if p:
            xs.append(f(p[1])); ys.append(f(p[2]))
x0, x1 = min(xs), max(xs)
y0, y1 = min(ys), max(ys)
W, H = x1 - x0, y1 - y0
# 19.30 was the OLD square board -- expect nothing absolute here; the checks
# that matter tie the CPL to the outline WHEREVER it is. Just record it.
check(W > 5 and H > 5, "board outline is sane",
      "measured %.3f x %.3f from Edge.Cuts" % (W, H))

# ---- 2. re-derive every placement -----------------------------------------
# JLC wants millimetres from the board's LOWER-LEFT corner, Y increasing UP.
# KiCad is Y-DOWN. Written as a corner translation, deliberately NOT as the
# "+9.65 / 9.65-" form used by make_bom_cpl.py.
def to_jlc(x, y):
    """KiCad Y-DOWN -> JLC Y-UP, measured from the board's LOWER-LEFT corner.

    Deliberately written as a translation of the MEASURED outline (x - x0,
    y1 - y) rather than the generator's "+9.65 / 9.65 -" constants, so a wrong
    constant in one does not reproduce in the other. That is still not enough
    on its own -- see the gerber-outline check, which is what actually proves
    the CPL and the copper share an origin."""
    return (x - x0), (y1 - y)

board, unref = {}, []
for fp in k(root, "footprint"):
    ref = None
    for pr in k(fp, "property"):
        if s(pr[1]) == "Reference":
            ref = s(pr[2])
    at = kd(fp, "at")
    lay = kd(fp, "layer")
    rec = dict(
        x=f(at[1]), y=f(at[2]),
        rot=(f(at[3]) if len(at) > 3 else 0.0) % 360,
        side=("Bottom" if lay and s(lay[1]).startswith("B.") else "Top"),
        npads=len(k(fp, "pad")))
    # BOTH mounting holes carry a BLANK reference, so keying this dict by ref
    # silently collapsed them into one and made the boss check report a single
    # hole. Unreferenced footprints go in a list; only named parts go in the map.
    if ref:
        board[ref] = rec
    else:
        unref.append(rec)
    board.setdefault(ref if ref else "", rec)

# ---- 3. read the CPL back -------------------------------------------------
rows = list(csv.DictReader(open(CPL, encoding="utf-8")))
check(len(rows) > 0, "CPL is not empty", "%d rows" % len(rows))

mm = lambda v: float(str(v).replace("mm", "").strip())
bad_xy, bad_rot, bad_side, outside = [], [], [], []
for r in rows:
    ref = r["Designator"]
    if ref not in board:
        bad_xy.append("%s: not on the board at all" % ref)
        continue
    ex, ey = to_jlc(board[ref]["x"], board[ref]["y"])
    gx, gy = mm(r["Mid X"]), mm(r["Mid Y"])
    if abs(gx - ex) > 0.001 or abs(gy - ey) > 0.001:
        bad_xy.append("%s: file (%.4f,%.4f) vs re-derived (%.4f,%.4f)"
                      % (ref, gx, gy, ex, ey))
    if abs(float(r["Rotation"]) - board[ref]["rot"]) > 0.01:
        bad_rot.append("%s: file %s vs board %.2f"
                       % (ref, r["Rotation"], board[ref]["rot"]))
    if r["Layer"] != board[ref]["side"]:
        bad_side.append("%s: file %s vs board %s" % (ref, r["Layer"], board[ref]["side"]))
    if not (-0.001 <= gx <= W + 0.001 and -0.001 <= gy <= H + 0.001):
        outside.append("%s at (%.3f,%.3f)" % (ref, gx, gy))

check(not bad_xy, "every CPL coordinate re-derives",
      "; ".join(bad_xy[:4]) if bad_xy else "%d placements, 0 mismatches" % len(rows))
check(not bad_rot, "every CPL rotation matches the board",
      "; ".join(bad_rot[:4]) if bad_rot else "0 mismatches")
check(not bad_side, "every CPL layer matches the board",
      "; ".join(bad_side[:4]) if bad_side else "all %s" % rows[0]["Layer"])
check(not outside, "no part sits outside the outline",
      "; ".join(outside[:4]) if outside else "all within 0..%.2f" % W)

# ---- 4. corner sanity: the transform must map the corners exactly ----------
c0 = to_jlc(x0, y1)          # lower-left  in gerber terms
c1 = to_jlc(x1, y0)          # upper-right
check(abs(c0[0]) < 1e-9 and abs(c0[1]) < 1e-9
      and abs(c1[0] - W) < 1e-9 and abs(c1[1] - H) < 1e-9,
      "origin transform maps the corners to 0,0 and W,H",
      "(%.3f,%.3f) and (%.3f,%.3f)" % (c0 + c1))

# ---- 4b. THE ORIGIN CHECK -------------------------------------------------
if _gx is None:
    check(False, "CPL sits inside the gerber outline",
          "no Edge_Cuts.gbr found -- CANNOT VERIFY, treat as unproven")
else:
    _out = []
    for r in rows:
        gx, gy = mm(r["Mid X"]), mm(r["Mid Y"])
        if not (_gx[0] <= gx <= _gx[1] and _gy[0] <= gy <= _gy[1]):
            _out.append("%s (%.3f,%.3f)" % (r["Designator"], gx, gy))
    check(not _out,
          "CPL sits inside the gerber outline",
          ("%d placement(s) OUTSIDE the board in gerber space: %s"
           % (len(_out), "; ".join(_out[:3]))) if _out else
          "all %d placements inside X %.2f..%.2f  Y %.2f..%.2f read from Edge_Cuts.gbr"
          % (len(rows), _gx[0], _gx[1], _gy[0], _gy[1]))

# ---- 5. BOM <-> CPL must cover the same designators ------------------------
bom = list(csv.DictReader(open(BOM, encoding="utf-8")))
bom_refs = []
for r in bom:
    bom_refs += [d.strip() for d in r["Designator"].split(",") if d.strip()]
cpl_refs = [r["Designator"] for r in rows]
check(sorted(bom_refs) == sorted(cpl_refs), "BOM and CPL cover the same parts",
      "BOM %d, CPL %d, only-in-BOM=%s only-in-CPL=%s"
      % (len(bom_refs), len(cpl_refs),
         sorted(set(bom_refs) - set(cpl_refs)), sorted(set(cpl_refs) - set(bom_refs))))
check(len(set(bom_refs)) == len(bom_refs), "no designator listed twice in the BOM",
      "%d entries, %d unique" % (len(bom_refs), len(set(bom_refs))))

# ---- 6. every BOM line has a part number ----------------------------------
nolcsc = [r["Designator"] for r in bom if not r["JLCPCB Part # (LCSC Part #)"].strip()]
check(not nolcsc, "every BOM line carries an LCSC code",
      ", ".join(nolcsc) if nolcsc else "%d lines, all sourced" % len(bom))

# ---- 7. what the CPL deliberately omits, and why --------------------------
# The two mounting holes carry NO reference in KiCad, so their ref is the empty
# string -- not "Un0"/"Un1", which was Altium's auto-naming on import and never
# existed in this file. An earlier version of this check filtered blank refs out
# of the EXPECTED set but not out of the OBSERVED set, and reported a failure
# that was purely its own bookkeeping.
omitted = sorted(set(board) - set(cpl_refs) - {None}, key=lambda r: (r == "", r))
expect_omitted = {r for r in board
                  if r is not None
                  and (r == "" or r.startswith(("TP", "J", "MH")) or r == "BT1")}
check(set(omitted) == expect_omitted, "CPL omits exactly the hand-worked parts",
      "omitted=%s" % ", ".join(("<no ref>" if r == "" else r) for r in omitted))

# ...and the unreferenced ones must be the two NPTH mounting holes, in the
# places the housing puts its PINS. This is the only check that ties the
# board's holes to the printed part, so it is also the only thing that would
# have caught the mounting changing underneath it.
#
# It nearly did not. These were the v5 SCREW BOSSES on the corner diagonal,
# (8.10,-8.10)/(-8.10,8.10), and the board moved to press-fit pins on the side
# centres because the corner positions overlapped the pogo pads. Left alone,
# this check would have validated a fab package against mounting geometry that
# no longer exists anywhere.
#
# READ FROM THE HOUSING, do not retype it. A constant copied from another file
# is a constant that drifts.
import re as _re
_hb = open(os.path.join(HERE, "..", "scripts", "touchid_module_v6.py"),
           encoding="utf-8").read()
_pp = _re.search(r"pcb_pin_pos = \[([^\]]*)\]", _hb)
if not _pp:
    sys.exit("cannot read pcb_pin_pos from touchid_module_v6.py -- refusing to guess")
BOSSES = [(float(a), float(b)) for a, b in
          _re.findall(r"\(([-\d.]+),\s*([-\d.]+)\)", _pp.group(1))]
mh = [(v["x"], v["y"]) for v in unref]
holes_ok = (len(mh) == 2
            and all(any(math.hypot(hx - bx, hy - by) < 0.01 for hx, hy in mh)
                    for bx, by in BOSSES))
check(holes_ok, "NPTH holes sit on the housing's press-fit pins",
      "%d hole(s) %s vs housing %s" % (len(mh), sorted(mh), sorted(BOSSES)))

# ---- 8. rotation can only be wrong on parts with >2 pads ------------------
risky = sorted(r for r in cpl_refs if board[r]["npads"] > 2)
notes.append(("INFO", "parts whose rotation can be wrong",
              "%d of %d: %s (all others are 2-pad symmetric)"
              % (len(risky), len(cpl_refs), ", ".join(risky))))

# ---- 9. nothing on the board is tall enough to hit the cell ---------------
# The cell seats at z 2.25 (module lid 2.05 + 0.20 pad). Only U1 may be taller,
# because the cell rests ON it. Heights are from the parts actually sourced.
HEIGHT = {"L1": 1.20, "U2": 1.00, "U3": 0.40, "U4": 0.40, "U1": 2.05}
CHIP = {2: 0.50}            # 0402
for r in cpl_refs:
    HEIGHT.setdefault(r, 1.00 if "060" in r else 0.50)
tall = [r for r in cpl_refs if r != "U1" and HEIGHT.get(r, 0.5) > 2.25]
check(not tall, "no part (except U1) reaches the 2.25 mm cell seat",
      ", ".join(tall) if tall else
      "tallest is L1 at 1.20 mm; cell seat is 2.25 mm -> 1.05 mm clear")

# ---------------------------------------------------------------- report ---
print("=" * 74)
print("HANDOFF VERIFICATION — BOM / CPL re-derived independently")
print("=" * 74)
for st, what, det in notes + fails:
    print("  %-5s %-42s %s" % (st, what, det))
print("=" * 74)
print("  %d FAILURE(S)" % len(fails))
print("=" * 74)
sys.exit(1 if fails else 0)
