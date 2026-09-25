"""verify_gerbers.py — grade the plotted fab output against the board.

A gerber set can be structurally perfect and still be the WRONG BOARD, or be
missing a layer that nobody notices until the fab builds it. Two failure modes
matter most and neither shows up as an error in KiCad's log:

  * a layer that plotted but is EMPTY (no draw commands) -- e.g. an inner plane
    that lost its pour. The file exists, has a header, and is silently blank.
  * drill data that does not match the board's holes.

So this reads the board and the gerbers separately and compares them.
"""
import glob, math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")
import sexp

HERE = os.path.dirname(os.path.abspath(__file__)) or "."
import sys as _sys
BOARD = (_sys.argv[1] if len(_sys.argv)>1 else None) or os.environ.get("BOARD") \
        or os.path.join(HERE, "pcb-v7-zero-opens.kicad_pcb")  # was hardcoded; same defect as make_bom_cpl
GD = os.path.join(HERE, "..", "v6-handoff", "gerbers")

fails, rows = [], []
def check(ok, what, detail=""):
    rows.append(("PASS" if ok else "FAIL", what, detail))
    if not ok:
        fails.append(what)

# ------------------------------------------------- what the board says -----
text = open(BOARD, encoding="utf-8", errors="replace").read()
root = sexp.parse(text)
k, kd, s, f = sexp.kids, sexp.kid, sexp.s, sexp.f

vias = k(root, "via")
via_drills = [round(f(kd(v, "drill")[1]), 4) for v in vias]

pth, npth = [], []
for fp in k(root, "footprint"):
    for pad in k(fp, "pad"):
        ptype = s(pad[2]) if len(pad) > 2 else ""
        dr = kd(pad, "drill")
        if dr is None:
            continue
        d = round(f(dr[1]), 4)
        (npth if ptype == "np_thru_hole" else pth).append(d)

board_holes = len(vias) + len(pth) + len(npth)

# ------------------------------------------------ the files themselves -----
EXPECT = ["F_Cu", "In1_Cu", "In2_Cu", "B_Cu", "F_Mask", "B_Mask",
          "F_Silkscreen", "B_Silkscreen", "F_Paste", "B_Paste", "Edge_Cuts"]
present = {}
for p in glob.glob(os.path.join(GD, "*.gbr")):
    for e in EXPECT:
        if p.endswith("-%s.gbr" % e):
            present[e] = p
missing = [e for e in EXPECT if e not in present]
check(not missing, "all 11 fabrication layers plotted",
      "missing: %s" % missing if missing else ", ".join(EXPECT))

# ---- no layer may be silently empty, unless the board says it should be ----
# D01 = draw, D03 = flash. A file with a header and neither is a blank layer.
#
# BUT an empty layer is not automatically a fault: this board has all 46
# footprints on the front, so B.Paste has nothing to plot and B.Silkscreen only
# whatever back legend exists. The first version of this check flagged B_Paste
# and was wrong -- it asserted "non-empty" instead of "agrees with the board".
# So the board decides which layers are ALLOWED to be empty.
back_fp = sum(1 for fp in k(root, "footprint")
              if (kd(fp, "layer") and s(kd(fp, "layer")[1]).startswith("B.")))
may_be_empty = set()
if back_fp == 0:
    may_be_empty |= {"B_Paste"}

empties, counts = [], {}
for e, pth_ in sorted(present.items()):
    body = open(pth_, encoding="utf-8", errors="replace").read()
    n = len(re.findall(r"D0[13]\*", body))
    counts[e] = n
    if n == 0 and e not in may_be_empty:
        empties.append(e)
check(not empties, "no layer is empty that the board says should have copper",
      "UNEXPECTEDLY EMPTY: %s" % empties if empties else
      "%d back-side footprints, so %s legitimately empty; "
      % (back_fp, ", ".join(sorted(may_be_empty)) or "nothing")
      + "; ".join("%s=%d" % (e, counts[e]) for e in EXPECT
                  if e in counts and counts[e]))

# ---- units and format must be metric, absolute, 4.6 -----------------------
bad_fmt = []
for e, p in present.items():
    head = open(p, encoding="utf-8", errors="replace").read(4000)
    if "%MOMM*%" not in head:
        bad_fmt.append("%s: not in millimetres" % e)
    if not re.search(r"%FSLAX46Y46\*%", head):
        bad_fmt.append("%s: coordinate format is not 4.6" % e)
    if "%IPNEG*%" in head:
        bad_fmt.append("%s: NEGATIVE image" % e)
    if re.search(r"%MI[AB]1", head):
        bad_fmt.append("%s: MIRRORED" % e)
check(not bad_fmt, "every layer is mm / 4.6 / positive / unmirrored",
      "; ".join(bad_fmt[:4]) if bad_fmt else "11/11 correct")

# ---- the outline must be the board -----------------------------------------
edge = open(present["Edge_Cuts"], encoding="utf-8", errors="replace").read()
xs, ys = [], []
for m in re.finditer(r"X(-?\d+)Y(-?\d+)D0[12]\*", edge):
    xs.append(int(m.group(1)) / 1e6)
    ys.append(int(m.group(2)) / 1e6)
if xs:
    w, h = max(xs) - min(xs), max(ys) - min(ys)
else:
    w = h = 0
# the profile is a 0.05 mm-wide stroke, so its extents run half a width proud
# on each side: 19.30 of board reads as 19.35 across the aperture centres.
# The 19.30 constant here was the OLD square board -- exactly the mistake this
# checker was written to catch, committed by the checker itself. Expect the
# dimensions the BOARD declares (read from its own Edge.Cuts bbox).
_exs=[]; _eys=[]
for _g in k(root, "gr_line") + k(root, "gr_rect") + k(root, "gr_arc"):
    _ly = kd(_g, "layer")
    if _ly is None or s(_ly[1]) != "Edge.Cuts":
        continue
    for _tag in ("start", "end", "mid"):
        _pt = kd(_g, _tag)
        if _pt is not None:
            _exs.append(f(_pt[1])); _eys.append(f(_pt[2]))
_bw = (max(_exs) - min(_exs)) if _exs else 0.0
_bh = (max(_eys) - min(_eys)) if _eys else 0.0
check(abs(w - _bw) < 0.06 and abs(h - _bh) < 0.06,
      "Edge.Cuts outline matches the board (%.2f x %.2f)" % (_bw, _bh),
      "%.3f x %.3f mm across %d profile points (stroke width accounts for <=0.05)"
      % (w, h, len(xs)))

# ---- copper layers must carry roughly what the board carries ---------------
# Not an exact count -- a pour becomes many draws -- but an inner plane that
# lost its fill would collapse to almost nothing, and that is what we catch.
thin = [e for e in ("F_Cu", "In1_Cu", "In2_Cu", "B_Cu") if counts.get(e, 0) < 50]
check(not thin, "all four copper layers carry substantial geometry",
      "SUSPICIOUSLY THIN: %s" % thin if thin else
      "F=%d In1=%d In2=%d B=%d draws"
      % (counts["F_Cu"], counts["In1_Cu"], counts["In2_Cu"], counts["B_Cu"]))

# ------------------------------------------------------------- drilling ----
drl = sorted(glob.glob(os.path.join(GD, "*.drl")))
check(len(drl) >= 1, "drill file(s) present", ", ".join(os.path.basename(d) for d in drl))

tot_holes, drill_sizes, npth_holes = 0, {}, 0
for d in drl:
    body = open(d, encoding="utf-8", errors="replace").read()
    tools = {t: float(v) for t, v in re.findall(r"(T\d+)C([\d.]+)", body)}
    cur = None
    isn = "NPTH" in os.path.basename(d).upper()
    for line in body.splitlines():
        line = line.strip()
        if re.fullmatch(r"T\d+", line):
            cur = line
        elif line.startswith("X") and cur in tools:
            tot_holes += 1
            drill_sizes[round(tools[cur], 4)] = drill_sizes.get(round(tools[cur], 4), 0) + 1
            if isn:
                npth_holes += 1
    if "METRIC" not in body:
        check(False, "drill file %s is metric" % os.path.basename(d), "MISSING METRIC header")

check(tot_holes == board_holes, "drill hole count matches the board",
      "gerbers %d vs board %d  (%d vias + %d PTH pads + %d NPTH)"
      % (tot_holes, board_holes, len(vias), len(pth), len(npth)))
check(npth_holes == len(npth), "NPTH holes match the board",
      "drill NPTH %d vs board %d" % (npth_holes, len(npth)))

want_sizes = {}
for d in via_drills + pth + npth:
    want_sizes[d] = want_sizes.get(d, 0) + 1
check(drill_sizes == want_sizes, "every drill diameter matches the board",
      "gerbers %s vs board %s" % (dict(sorted(drill_sizes.items())),
                                  dict(sorted(want_sizes.items()))))

# ---- the job file ----------------------------------------------------------
job = glob.glob(os.path.join(GD, "*.gbrjob"))
if job:
    import json
    J = json.load(open(job[0], encoding="utf-8"))
    gs = J.get("GeneralSpecs", {})
    check(gs.get("LayerNumber") == 4, "job file declares 4 layers",
          str(gs.get("LayerNumber")))
    # KiCad writes the FINISHED thickness here: laminate + both solder masks.
    # That is 1.20 + 0.02 = 1.22, and it is correct -- 1.20 is what you pick on
    # the order form, 1.22 is what the part measures. Asserting 1.20 here was
    # this checker importing the order-form number into the wrong place.
    _bt = float(gs.get("BoardThickness", 0))
    # Compare against what the BOARD's setup declares, not a constant: this
    # board's stackup reports 1.20 with 0.00 mask (preflight 19 agrees), and
    # KiCad 10 writes that same figure here. The old 1.22 expectation was a
    # different board's stackup baked into the checker.
    _setup = kd(root, "setup"); _thick = kd(_setup, "stackup")
    _decl = 1.20
    _th = kd(_setup, "thickness") if _setup else None
    if _th is not None: _decl = f(_th[1])
    check(abs(_bt - _decl) < 0.025,
          "job file thickness matches the board's declared %.2f mm" % _decl,
          "%s mm in job. ORDER 1.2 mm regardless -- thickness is an order-form pick." % _bt)
    check(len(J.get("FilesAttributes", [])) == 11,
          "job file lists all 11 layers", str(len(J.get("FilesAttributes", []))))
else:
    check(False, "gerber job file present", "missing")

print("=" * 74)
print("GERBER VERIFICATION — plotted output vs the board")
print("=" * 74)
for st, what, det in rows:
    print("  %-5s %-44s %s" % (st, what, det))
print("=" * 74)
print("  %d FAILURE(S)" % len(fails))
print("=" * 74)
sys.exit(1 if fails else 0)
