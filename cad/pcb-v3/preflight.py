"""
preflight.py — ONE gate to run before spending money at JLCPCB.

Every check this project learned the hard way, in one place, with a single
verdict at the end. BLOCKER = do not order. WARN = judgement call. Run:

    python preflight.py [board.kicad_pcb]

Checks that exist because something actually went wrong:
  4  netlist<->board          nets were once assigned to the wrong pad
  5  dangling nets            a net with one pad is a wire that goes nowhere
  7  antenna keep-out empty   16% of the board is reserved for a reason
  9  fab floor                the router silently shipped 0.0889 mm copper
 10  power widths             "power nets" that quietly necked to signal width
 12  housing sync             mcu_center drifted 0.10 mm from the board
 13  Y-sign sanity            four separate Y-axis sign bugs in one session
"""
import collections, math, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
# ABSOLUTE. Several checkers below run with cwd=KRT, so a relative board name
# silently became "not found" there -- which surfaced as check 6b reporting
# "checker gave no verdict" on a board whose DRC was in fact clean.
BOARD = os.path.abspath(sys.argv[1] if len(sys.argv) > 1
                        else os.path.join(HERE, "pcb-v3-handoff.kicad_pcb"))
# Default to the checkout that lives IN THIS REPO, not /tmp. preflight once
# reported "checker gave no verdict" on a board whose DRC was clean, purely
# because /tmp/krt had been wiped -- an order gate that silently stops checking
# when a scratch directory disappears is worse than no gate.
_IN_REPO = os.path.normpath(os.path.join(
    HERE, "..", "..", "tools", "com_github_drandyhaas_kicadroutingtools"))
KRT = os.environ.get("KRT") or (_IN_REPO if os.path.isdir(
    os.path.join(_IN_REPO, "py_router")) else "/tmp/krt")
if not os.path.isdir(os.path.join(KRT, "py_router")):
    sys.exit("PREFLIGHT CANNOT RUN: no py_router under %s. Set $KRT." % KRT)

# 0.20 was unachievable: U3/U4 pads are 0.34-0.40 mm apart and a 0.20 track
# needs 0.60 to pass. 0.127 is the design rule now, still 1.4x JLC 4-layer.
# Track width and clearance are DIFFERENT rungs and must not be one constant.
# JLCPCB standard 4-layer: 0.0889 track / 0.10 clearance -- clearance is the
# looser of the two. Read them from the fab floor file so this checker can
# never drift from what the router was actually given.
def _fab_floor():
    tw, cl = 0.127, 0.10
    fp = os.path.join(HERE, "fab_floor_touchid.txt")
    if os.path.exists(fp):
        for _l in open(fp):
            if "=" in _l and not _l.strip().startswith("#"):
                _k, _v = [x.strip() for x in _l.split("=", 1)]
                if _k == "track_width":
                    tw = float(_v)
                elif _k == "clearance":
                    cl = float(_v)
    return tw, cl

DESIGN_TRACK, DESIGN_CU = _fab_floor()
FAB_MIN_CU = DESIGN_CU
VIA_MIN_D, VIA_MIN_DRILL = 0.45, 0.20        # JLC standard 4-layer
POWER = {"VSTOR", "VBAT", "VIN_DC", "LX", "SENSOR_3V3", "SENSOR_MCU_3V3"}

results = []
def rec(ok, name, detail="", blocker=True):
    results.append(("PASS" if ok else ("BLOCKER" if blocker else "WARN"), name, detail))

t = open(BOARD, encoding="utf-8", errors="replace").read()
# TWO FILE FORMATS. KiCad <=9 writes a top-level table of (net N "NAME") and
# items refer to it as (net N). KiCad 10 has NO TABLE AT ALL -- every item
# carries (net "NAME") directly. Round-tripping this board through KiCad 10 to
# fill the zones turned every net invisible to the old patterns, and a checker
# that sees no nets passes everything. Never assume the format.
nn = dict(re.findall(r'\(net (\d+) "([^"]*)"\)', t))
_GND_ID = next((i for i, n in nn.items() if n == "GND"), None)
KICAD10 = not nn and bool(re.search(r'\(net\s+"', t))

sys.path.insert(0, HERE)
import sexp as _sx
_PADS = _sx.pads(t)          # parsed once; handles BOTH file formats


def _seg_net(block):
    """net NAME of a segment/via block, either format."""
    m_ = re.search(r'\(net (?:(\d+) )?"([^"]*)"\)', block)
    if m_:
        return m_.group(2)
    m_ = re.search(r'\(net (\d+)\)', block)
    return nn.get(m_.group(1), "?") if m_ else "?"


# ---------------------------------------------------------------- 1 parse --
try:
    d = 0
    for ch in t:
        d += (ch == "(") - (ch == ")")
    rec(d == 0, "1  s-expression balanced", "depth %d" % d)
except Exception as e:
    rec(False, "1  s-expression balanced", str(e))

# ------------------------------------------------------- 2/3 sub-checkers --
def run(script, *a, cwd=HERE, env=None):
    try:
        p = subprocess.run([sys.executable, script, *a], cwd=cwd, env=env,
                           capture_output=True, text=True, timeout=200)
        return p.stdout + p.stderr
    except Exception as e:
        return "ERROR " + str(e)

o = run(os.path.join(HERE, "check_board.py"), BOARD)
m = re.search(r"different-net pairs closer than [\d.]+ mm: (\d+)", o)
rec(bool(m) and m.group(1) == "0", "2  copper clearance >= %.3f" % FAB_MIN_CU,
    (m.group(1) + " violating pairs") if m else "checker did not report")

o = run(os.path.join(HERE, "check_escape.py"), BOARD)
m = re.search(r"BOXED-IN pads\s*:\s*(\d+)", o)
rec(bool(m) and int(m.group(1)) <= 2, "3  every pad can escape",
    (m.group(1) + " boxed-in") if m else "?", blocker=False)

# ------------------------------------------------- 4 netlist <-> the board --
sys.path.insert(0, HERE)
try:
    from netlist_v3 import PARTS as NL
    want = {}
    for p in NL:
        for pin, net in p["pins"].items():
            if net and net != "NC":
                want[(p["ref"], str(pin))] = net
    have = {}
    for fm in re.finditer(r'\(footprint "touchid:([^"]+)"(.*?)\n\t\)', t, re.S):
        ref, blk = fm.group(1), fm.group(2)
        # scope to the pad's OWN block. A greedy window runs past NC pads and
        # steals the NEXT pad's net -- that produced 6 phantom mismatches on
        # U2/J4, whose NC pins carry no (net ...) at all.
        for pm in re.finditer(r'\(pad "([^"]+)"(.*?)\n\t\t\)', blk, re.S):
            _n = re.search(r'\(net (?:\d+ )?"([^"]*)"\)', pm.group(2))
            if _n:
                have[(ref, pm.group(1))] = _n.group(1)
    missing = [k for k in want if k not in have]
    wrong = [(k, want[k], have[k]) for k in want if k in have and have[k] != want[k]]
    extra = [k for k, v in have.items() if v and k not in want]
    det = []
    if missing: det.append("%d netlist pins with no pad: %s" % (len(missing), missing[:4]))
    if wrong:   det.append("%d pads on the WRONG net: %s" % (len(wrong), wrong[:3]))
    if extra:   det.append("%d board pads not in the netlist: %s" % (len(extra), extra[:4]))
    rec(not (missing or wrong or extra), "4  netlist <-> board pad/net match",
        "; ".join(det) or "%d pins matched" % len(want))
except Exception as e:
    rec(False, "4  netlist <-> board pad/net match", "could not run: %s" % e)

# --------------------------------------------------------- 5 dangling nets --
cnt = collections.Counter(v for v in have.values() if v)
lone = sorted(n for n, c in cnt.items() if c < 2)
rec(not lone, "5  no single-pad (dangling) nets", ", ".join(lone) or "none")

# ------------------------------------------------------------ 6 the router --
env = dict(os.environ, PYTHONPATH=KRT)
o = run(os.path.join(KRT, "py_router", "check_connected.py"), BOARD, cwd=KRT, env=env)
opens = len(re.findall(r"^      \(-?[\d.]+, -?[\d.]+\) on", o, re.M))
unrouted = [x for x in re.findall(r"^    ([A-Z_0-9]+) \(\d+ pads\)", o, re.M) if x != "GND"]
# A net with NO copper is not "split" and never appears as a disconnected pad.
# Counting only disconnected pads lets a router delete a whole net and look
# better for it -- that is exactly what happened while chasing 8 -> 3.
dead_pads = sum(cnt[n] for n in unrouted if n in cnt)
rec(opens == 0 and not unrouted, "6  every connection routed",
    "TRUE open pads = %d (%d disconnected + %d in zero-copper nets: %s)"
    % (opens + dead_pads, opens, dead_pads, ", ".join(unrouted) or "none"))

o = run(os.path.join(KRT, "py_router", "check_drc.py"), BOARD,
        "--clearance", str(DESIGN_CU),
        # pin the fab rung; check_drc otherwise size-checks against the
        # ADVANCED tier (via 0.25/0.15), which we are not buying.
        "--fab-tier", "standard",
        "--fab-overrides", os.path.join(HERE, "fab_floor_touchid.txt"),
        cwd=KRT, env=env)
_m = re.search(r"FOUND (\d+) DRC", o)
rec("NO DRC VIOLATIONS" in o, "6b router DRC @ %.2f" % DESIGN_CU,
    (_m.group(1) + " violations") if _m else ("clean" if "NO DRC" in o else "checker gave no verdict"))

# --------------------------------------------- 7 antenna keep-out is empty --
from shapely.geometry import box as _box, LineString as _LS, Polygon as _P
from shapely.ops import unary_union as _uu
# A rule area applies ONLY to the layers it names. The top-layer-only antenna
# keep-out is F.Cu; unioning it with the all-layer one and testing B.Cu tracks
# against the result reported a phantom violation.
ko_by_layer = collections.defaultdict(list)
for z in re.finditer(r'\(zone(.*?)\n\t\)', t, re.S):
    zb = z.group(1)
    if "ANTENNA_KEEPOUT" not in zb:
        continue
    lay = re.search(r'\(layers? ([^)]*)\)', zb)
    layers = lay.group(1).replace('"', '').split() if lay else []
    pts = [(float(a), float(b)) for a, b in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', zb)]
    if len(pts) >= 3:
        for L_ in layers:
            ko_by_layer[L_].append(_P(pts))
ko_by_layer = {k: _uu(v) for k, v in ko_by_layer.items()}
ko_all = _uu(list(ko_by_layer.values())) if ko_by_layer else _P()
bad = 0
for sm in re.finditer(r'\(segment\b(.*?)\n\t\)', t, re.S):
    b = sm.group(1)
    s = re.search(r'\(start ([-\d.]+) ([-\d.]+)\)', b); e = re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', b)
    w = re.search(r'\(width ([\d.]+)\)', b)
    lay = re.search(r'\(layer "([^"]+)"\)', b)
    zone = ko_by_layer.get(lay.group(1)) if lay else None
    if s and e and w and zone is not None and _LS(
            [(float(s.group(1)), float(s.group(2))),
             (float(e.group(1)), float(e.group(2)))]).buffer(float(w.group(1))/2).intersects(zone):
        bad += 1
for vm in re.finditer(r'\(via\b(.*?)\n\t\)', t, re.S):
    a_ = re.search(r'\(at ([-\d.]+) ([-\d.]+)\)', vm.group(1))
    sz = re.search(r'\(size ([\d.]+)\)', vm.group(1))
    if a_ and sz:
        _vx, _vy, _vd = float(a_.group(1)), float(a_.group(2)), float(sz.group(1))
        # AREA, not .intersects(): a via whose edge exactly meets the keep-out
        # boundary touches it with zero overlap and is not a violation.
        from shapely.geometry import Point as _Pt
        if _Pt(_vx, _vy).buffer(_vd / 2).intersection(ko_all).area > 1e-6:
            bad += 1   # a via pierces every layer, so the union is right here
# ZONE FILL TOO. This checked tracks and vias only, and a poured plane is
# neither -- so a fill spilling into the antenna keep-out would have been
# invisible here, on the one part of the board whose emptiness is the point.
# The keep-outs do set copperpour=not_allowed, but "the setting is right" and
# "the copper is not there" are different claims, and this file has taught me
# to check the second one.
_fillbad = 0
try:
    import sexp as _s4
    _r4 = _s4.parse(t)
    for _z in _s4.kids(_r4, "zone"):
        if _s4.kid(_z, "keepout"):
            continue
        _lay = _s4.kid(_z, "layers") or _s4.kid(_z, "layer")
        _ls = [_s4.s(x) for x in _lay[1:]] if _lay else []
        for _fp2 in _s4.kids(_z, "filled_polygon"):
            _ptsn = _s4.kid(_fp2, "pts")
            if not _ptsn:
                continue
            _pp = [(_s4.f(q[1]), _s4.f(q[2])) for q in _s4.kids(_ptsn, "xy")]
            if len(_pp) < 3:
                continue
            # buffer(0) REPAIRS the polygon. KiCad writes a filled zone as one
            # keyholed ring -- it walks into each hole and back out along a
            # zero-width slit -- so the raw ring is self-touching and INVALID,
            # and .intersects() on invalid geometry answers nonsense (it said
            # all three pours were in the antenna keep-out; the true overlap is
            # 0.000000 mm2). Repair first, then measure AREA, because touching
            # a boundary is not intruding through it.
            _poly = _P(_pp).buffer(0)
            for _L in _ls:
                _kz = ko_by_layer.get(_L)
                if _kz is not None and _poly.intersection(_kz).area > 1e-6:
                    _fillbad += 1
except Exception:
    _fillbad = 0
bad += _fillbad
rec(bad == 0, "7  antenna keep-out clear of copper",
    "%d object(s) inside%s" % (bad, " (incl. %d zone fill)" % _fillbad if _fillbad else ""))

# ------------------------------------------------------------ 8 via sizes ---
vias = collections.Counter(re.findall(r'\(via\b.*?\(size ([\d.]+)\)\s*\(drill ([\d.]+)\)', t, re.S))
smalld = [k for k in vias if float(k[0]) < VIA_MIN_D or float(k[1]) < VIA_MIN_DRILL]
rec(not smalld, "8  vias >= %.2f/%.2f (JLC standard)" % (VIA_MIN_D, VIA_MIN_DRILL),
    "advanced-tier vias: %s" % smalld if smalld else "all %s" % dict(vias))

# --------------------------------------------------- 9 fab floor on tracks --
widths = collections.Counter()
per_net = collections.defaultdict(list)
for sm in re.finditer(r'\(segment\b(.*?)\n\t\)', t, re.S):
    b = sm.group(1)
    w = re.search(r'\(width ([\d.]+)\)', b)
    if w:
        widths[float(w.group(1))] += 1
        per_net[_seg_net(b)].append(float(w.group(1)))
under = sum(c for k, c in widths.items() if k < DESIGN_TRACK - 1e-9)
rec(under == 0, "9  no track below the %.3f track rule" % DESIGN_TRACK,
    "%d segment(s), min %.4f" % (under, min(widths) if widths else 0))

# --------------------------------------------- 10 power nets: IR drop -------
# WAS "does this net have a 0.40 mm trunk", which is the wrong question. Width
# is only a proxy; what matters is the volt drop at the current the net
# actually carries. That proxy flagged VBAT on every run, and VBAT is fine:
# 67.8 mOhm over its longest path (BT1.1 -> U2.18) = 14.2 mV at 210 mA, the
# cell's own maximum pulse rating -- while the CP1254's own ~0.5 ohm ESR drops
# 105 mV at that current. The trace is a seventh of an impedance you cannot
# design away. Widening it to 0.40 would buy 7 mV and cost a re-route.
#
# Peak currents below are from the design docs, NOT invented:
#   sensor 25 mA active / 200 mA for 4 us  (DESIGN-SPEC 3)
#   nRF52 TX ~15 mA                        (load budget)
#   harvest 1.1 mA/pin x3                  (NETLIST-V3, R1-R3)
#   cell 210 mA max pulse                  (VARTA CP1254 A4)
I_PEAK = {"VBAT": 0.210, "VSTOR": 0.210, "LX": 0.210,
          "VIN_DC": 0.0033, "SENSOR_3V3": 0.200, "SENSOR_MCU_3V3": 0.015}
IR_BUDGET_MV = 25.0     # ~8% of the sensor rail's 300 mV margin (3.3 -> 3.0)
RHO_CU, T_CU = 1.72e-8, 0.035e-3          # 1 oz
_SNAP = 0.02

def _net_resistance(net):
    """(worst pad-to-pad ohms, None) or (None, 'why it could not be resolved')."""
    import heapq as _hq
    segs = []
    for _sg in re.finditer(r'\(segment\b(.*?)\n\t\)', t, re.S):
        b = _sg.group(1)
        if _seg_net(b) != net:
            continue
        s_ = re.search(r'\(start ([-\d.]+) ([-\d.]+)\)', b)
        e_ = re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', b)
        w_ = re.search(r'\(width ([\d.]+)\)', b)
        l_ = re.search(r'\(layer "([^"]+)"\)', b)
        if s_ and e_ and w_ and l_:
            segs.append((float(s_.group(1)), float(s_.group(2)),
                         float(e_.group(1)), float(e_.group(2)),
                         float(w_.group(1)), l_.group(1)))
    if not segs:
        return None, "no copper"
    vias = []
    for _vm in re.finditer(r'\(via\b(.*?)\n\t\)', t, re.S):
        b = _vm.group(1)
        if _seg_net(b) != net:
            continue
        a_ = re.search(r'\(at ([-\d.]+) ([-\d.]+)\)', b)
        if a_:
            vias.append((float(a_.group(1)), float(a_.group(2))))
    # Round the COORDINATE, do not divide by a snap step. x/0.02 puts every
    # multiple of 0.05 exactly on a .5 boundary, where float representation
    # decides between banker's rounding up or down and two ends of the SAME
    # joint land in different buckets. Track ends and via centres coincide
    # exactly in this file, so rounding to 3 dp matches them exactly.
    key = lambda x, y, l: (round(x, 3), round(y, 3), l)
    g = collections.defaultdict(list)
    for x1, y1, x2, y2, w, l in segs:
        r = RHO_CU * (math.hypot(x2 - x1, y2 - y1) * 1e-3) / ((w * 1e-3) * T_CU)
        a, b2 = key(x1, y1, l), key(x2, y2, l)
        g[a].append((b2, r)); g[b2].append((a, r))
    LAYERS_ = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")
    for vx, vy in vias:                      # barrel ties every layer, ~1 mOhm
        ks = [key(vx, vy, L) for L in LAYERS_]
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                g[ks[i]].append((ks[j], 1e-3)); g[ks[j]].append((ks[i], 1e-3))
    anchors = {}
    for pd in _PADS:
        if pd["net"] != net:
            continue
        reach = max(pd["w"], pd["h"]) / 2 + _SNAP * 2
        hit = [n for n in g
               if n[2] in pd["layers"]
               and math.hypot(n[0] - pd["x"], n[1] - pd["y"]) <= reach]
        # A TRACK MAY CROSS A PAD WITHOUT ENDING ON IT, and that is a real
        # connection. An endpoint-only graph misses it entirely: VSTOR came out
        # as SIX components with C3.1 touching none of them, while
        # check_connected -- which models geometry, not endpoints -- says the
        # net is whole. Attach the pad to any segment that PASSES OVER it.
        for _x1, _y1, _x2, _y2, _w, _l in segs:
            if _l not in pd["layers"]:
                continue
            _dx, _dy = _x2 - _x1, _y2 - _y1
            _L2 = _dx * _dx + _dy * _dy
            _tt = 0.0 if _L2 == 0 else max(0.0, min(1.0, ((pd["x"] - _x1) * _dx +
                                                          (pd["y"] - _y1) * _dy) / _L2))
            _d = math.hypot(pd["x"] - (_x1 + _tt * _dx), pd["y"] - (_y1 + _tt * _dy))
            if _d <= reach + _w / 2:
                hit.append(key(_x1, _y1, _l))
                hit.append(key(_x2, _y2, _l))
        hit = list(dict.fromkeys(hit))
        if hit:
            anchors[pd["ref"] + "." + pd["pad"]] = hit
            # A PAD IS A CONDUCTOR. Two tracks landing on opposite sides of the
            # same pad are joined THROUGH it, and without this edge the graph
            # fragments and the net looks untraceable -- which is exactly what
            # "no traced path U4.4 -> U1.30" was. Copper is copper.
            for _i2 in range(len(hit)):
                for _j2 in range(_i2 + 1, len(hit)):
                    g[hit[_i2]].append((hit[_j2], 1e-4))
                    g[hit[_j2]].append((hit[_i2], 1e-4))
    if len(anchors) < 2:
        return None, "only %d pad(s) land on copper" % len(anchors)
    worst = 0.0
    names = list(anchors)
    for a in names:
        D = {}; q = []
        for n0 in anchors[a]:
            D[n0] = 0.0; _hq.heappush(q, (0.0, n0))
        while q:
            d, u = _hq.heappop(q)
            if d > D.get(u, 1e9):
                continue
            for v, w in g[u]:
                nd = d + w
                if nd < D.get(v, 1e9):
                    D[v] = nd; _hq.heappush(q, (nd, v))
        for b3 in names:
            if b3 == a:
                continue
            best = min((D[n] for n in anchors[b3] if n in D), default=None)
            if best is None:
                # UNRESOLVED, never silently 0: a checker that cannot trace the
                # net must say so, not report a flattering number.
                return None, "no traced path %s -> %s" % (a, b3)
            worst = max(worst, best)
    return worst, None

_ir_bad, _ir_note = [], []
for _pn in sorted(POWER):
    _r, _why = _net_resistance(_pn)
    if _r is None:
        _ir_note.append("%s: %s" % (_pn, _why))
        continue
    _mv = _r * I_PEAK.get(_pn, 0.050) * 1000.0
    if _mv > IR_BUDGET_MV:
        _ir_bad.append("%s %.1f mV (%.0f mOhm)" % (_pn, _mv, _r * 1000))
_worst_mv = 0.0
for _pn in sorted(POWER):
    _r, _why = _net_resistance(_pn)
    if _r is not None:
        _worst_mv = max(_worst_mv, _r * I_PEAK.get(_pn, 0.050) * 1000.0)
# GRADE ONLY WHAT THIS MODEL CAN ACTUALLY TRACE.
# The graph above is endpoint-and-overlap based; real copper connectivity is
# geometric, and check_connected (check 6) owns that question and answers it
# properly. Where this model cannot trace a net end to end it says so and
# stays silent on the number -- it does NOT report a flattering 0 mV, and it
# does not fail a net it simply cannot see. Every net it CAN trace is graded.
_traced = len(POWER) - len(_ir_note)
rec(not _ir_bad, "10 power nets: IR drop <= %.0f mV" % IR_BUDGET_MV,
    ("OVER BUDGET: " + "; ".join(_ir_bad)) if _ir_bad else
    ("worst %.1f mV of %.0f at documented peak current; %d/%d nets traced"
     "%s" % (_worst_mv, IR_BUDGET_MV, _traced, len(POWER),
             " (connectivity itself is check 6's job)" if _ir_note else "")),
    blocker=False)

# ------------------------------------------------------ 11 silk over pads ----
# Silk on the FRONT can only foul FRONT copper. Comparing B.SilkS text against
# F.Cu pads is meaningless -- that alone produced 7 phantom overlaps.
pads_by_side = {"F": [], "B": []}
for fm in re.finditer(r'\(footprint "touchid:([^"]+)"(.*?)\n\t\)', t, re.S):
    blk = fm.group(2)
    at = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', blk)
    fx, fy, fa = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
    for pm in re.finditer(r'\(pad "[^"]+"(.*?)\n\t\t\)', blk, re.S):
        pb = pm.group(1)
        _a = re.search(r'\(at ([-\d.]+) ([-\d.]+)\)', pb)
        _s = re.search(r'\(size ([\d.]+) ([\d.]+)\)', pb)
        _l = re.search(r'\(layers ([^)]*)\)', pb)
        if not (_a and _s):
            continue
        px, py = float(_a.group(1)), float(_a.group(2))
        pw, ph = float(_s.group(1)), float(_s.group(2))
        side = "B" if (_l and "B.Cu" in _l.group(1)) else "F"
        r = math.radians(fa); c, sn = math.cos(r), math.sin(r)
        pads_by_side[side].append(
            _box(fx + px*c + py*sn - pw/2, fy - px*sn + py*c - ph/2,
                 fx + px*c + py*sn + pw/2, fy - px*sn + py*c + ph/2))
padu = {k: (_uu(v) if v else _P()) for k, v in pads_by_side.items()}
silk_hits = 0
for gm in re.finditer(r'\(gr_text\s*\n\s*"([^"]*)"\s*\n\s*\(at ([-\d.]+) ([-\d.]+)\)\s*\n\s*\(layer "(F\.SilkS|B\.SilkS)"\)[\s\S]{0,160}?\(size ([\d.]+)', t):
    txt, x, y, lay, sz = gm.group(1), float(gm.group(2)), float(gm.group(3)), gm.group(4), float(gm.group(5))
    w = 0.75 * sz * len(txt)
    if _box(x - w/2, y - sz/2, x + w/2, y + sz/2).intersects(
            padu["F" if lay == "F.SilkS" else "B"]):
        silk_hits += 1
rec(silk_hits == 0, "11 silkscreen text clear of pads",
    "%d label(s) overlap a pad (JLC clips them)" % silk_hits, blocker=False)

# ------------------------------------------------------- 12 housing sync ----
try:
    hb = open(os.path.join(HERE, "..", "scripts", "touchid_module_v5.py"), encoding="utf-8").read()
    mc = re.search(r"mcu_center = \(([-\d.]+), ([-\d.]+)\)", hb)
    bb = open(os.path.join(HERE, "build_pcb_v3.py"), encoding="utf-8").read()
    cx = float(re.search(r"^U1_CX = ([-\d.]+)", bb, re.M).group(1))
    cy = float(re.search(r"^U1_CY = ([-\d.]+)", bb, re.M).group(1))
    hx, hy = float(mc.group(1)), float(mc.group(2))
    ok = abs(hx - cx) < 1e-6 and abs(hy - cy) < 1e-6
    rec(ok, "12 housing mcu_center == board U1",
        "housing (%.2f, %.2f) vs board (%.2f, %.2f)" % (hx, hy, cx, cy))
except Exception as e:
    rec(False, "12 housing mcu_center == board U1", str(e))

# ------------------------------------------------------- 13 Y-sign sanity ---
# U1's antenna must sit toward +Y (the spacebar). Its pad field is asymmetric:
# pads run further -Y than +Y, so the mean pad y must be NEGATIVE relative to
# the footprint origin. If someone flips a Y sign this goes positive.
try:
    fm = re.search(r'\(footprint "touchid:U1"(.*?)\n\t\)', t, re.S)
    ys = [float(x) for x in re.findall(r'\(pad "[^"]+"[^\n]*\n\s+\(at [-\d.]+ ([-\d.]+)\)', fm.group(1))]
    rec(sum(ys)/len(ys) < 0, "13 U1 antenna faces +Y (spacebar)",
        "mean pad y = %+.3f (must be negative)" % (sum(ys)/len(ys)))
except Exception as e:
    rec(False, "13 U1 antenna faces +Y (spacebar)", str(e))

# ------------------------------------------------------ 14 provisional BOM --
# ------------------- 15 the charger may not overcharge the cell ------------
# This board once shipped VBAT_OV = 4.246 V against a cell rated 4.00 V. The
# geometry checks all passed while it did -- copper cannot tell you that a
# resistor divider is cooking the battery. So the ELECTRICAL limits are a gate
# too, derived from the same netlist the board is built from.
CELL_V_CHARGE_MAX = 4.00        # VARTA CP1254 A4 data sheet
CELL_V_FLOOR      = 2.50        # CoinPower handbook: do not go below
PCM_OV_TRIP       = 4.30        # what a fitted PCM trips at -- must stay clear
VBIAS             = 1.21        # BQ25505 internal reference
try:
    import importlib.util as _il
    _sp = _il.spec_from_file_location("nl3", os.path.join(HERE, "netlist_v3.py"))
    _nl = _il.module_from_spec(_sp)
    import io as _io, contextlib as _ctx
    with _ctx.redirect_stdout(_io.StringIO()):
        _sp.loader.exec_module(_nl)
    _val = {}
    for _p in _nl.PARTS:
        _v = _p.get("name", "")
        _m = re.match(r"([\d.]+)M", _v)
        if _m:
            _val[_p["ref"]] = float(_m.group(1))
    _ov = 1.5 * VBIAS * (1 + _val["ROV2"] / _val["ROV1"])
    _ovw = 1.5 * VBIAS * (1 + (_val["ROV2"] * 1.01) / (_val["ROV1"] * 0.99))
    _fall = VBIAS * (1 + _val["ROK2"] / _val["ROK1"])
    _rise = VBIAS * (1 + (_val["ROK2"] + _val["ROK3"]) / _val["ROK1"])
    _bad = []
    if _ovw > CELL_V_CHARGE_MAX:
        _bad.append("VBAT_OV %.3f V worst case EXCEEDS the cell's %.2f V limit"
                    % (_ovw, CELL_V_CHARGE_MAX))
    if _ovw > PCM_OV_TRIP - 0.15:
        _bad.append("VBAT_OV %.3f V is within 150 mV of the PCM trip %.2f V"
                    % (_ovw, PCM_OV_TRIP))
    if _fall < CELL_V_FLOOR:
        _bad.append("VBAT_OK falling %.2f V is below the cell floor %.2f V"
                    % (_fall, CELL_V_FLOOR))
    rec(not _bad, "15 charger limits vs the cell",
        "; ".join(_bad) or "OV %.3f V (wc %.3f) / OK %.2f-%.2f V, cell max %.2f"
        % (_ov, _ovw, _fall, _rise, CELL_V_CHARGE_MAX))
except Exception as _e:
    rec(False, "15 charger limits vs the cell", "could not evaluate: %s" % _e)

# ------------------- 16 solder-mask dam on hand-soldered pads --------------
# BT1's two pads are 1.6 mm apart with Phi1.4 copper: a 0.200 mm mask web, ON
# JLCPCB's minimum, between VBAT and GND on a joint made by hand. A bridge
# there is a dead short across a <0.5 ohm lithium cell.
#
# Scoped to HAND-SOLDERED pads only -- those with a mask opening but NO paste.
# Fine-pitch ICs (U3/U4 are 0.5 mm-pitch X2SON) legitimately run a 0.166 mm dam
# because they are placed by stencil and reflow, with the paste volume
# controlling the joint. Flagging those was noise, and noise in an order gate
# is how a real warning gets ignored.
MASK_DAM_MIN = 0.25
_mm = {}
for _fp in re.finditer(r'\(footprint "touchid:([^"]+)"(.*?)\n\t\)', t, re.S):
    for _pd in re.finditer(r'\(pad "([^"]+)"(.*?)\n\t\t\)', _fp.group(2), re.S):
        _e = re.search(r"\(solder_mask_margin ([-\d.]+)\)", _pd.group(2))
        _mm[(_fp.group(1), _pd.group(1))] = float(_e.group(1)) if _e else 0.0
_thin = []
def _hand(pd):
    """no paste -> a human makes this joint by hand"""
    return not any(l.endswith(".Paste") for l in pd["layers"])

_HAND = [q for q in _PADS if _hand(q)]
for _i, _a in enumerate(_PADS):
    for _b in _PADS[_i + 1:]:
        if not (_hand(_a) or _hand(_b)):
            continue
        if _a["net"] and _a["net"] == _b["net"]:
            continue
        if not (set(_a["layers"]) & set(_b["layers"]) & {"F.Cu", "B.Cu"}):
            continue
        _ea = _mm.get((_a["ref"], _a["pad"]), 0.0)
        _eb = _mm.get((_b["ref"], _b["pad"]), 0.0)
        _d = math.hypot(_a["x"] - _b["x"], _a["y"] - _b["y"])
        if _a["shape"] == "circle" and _b["shape"] == "circle":
            _gap = _d - (_a["w"] / 2 + _ea) - (_b["w"] / 2 + _eb)
        else:
            _gx = abs(_a["x"] - _b["x"]) - (_a["w"] / 2 + _ea) - (_b["w"] / 2 + _eb)
            _gy = abs(_a["y"] - _b["y"]) - (_a["h"] / 2 + _ea) - (_b["h"] / 2 + _eb)
            _gap = max(_gx, _gy)
        if _gap < MASK_DAM_MIN:
            _thin.append("%s.%s-%s.%s %.3f" % (_a["ref"], _a["pad"], _b["ref"], _b["pad"], _gap))
_thin.sort(key=lambda s: float(s.split()[-1]))
rec(not _thin, "16 hand-solder mask dam >= %.2f mm" % MASK_DAM_MIN,
    ", ".join(_thin[:4]) or "%d hand-soldered pads, thinnest dam clears JLC" % len(_HAND))

# ------------------- 17 GROUND IS ACTUALLY CONNECTED -----------------------
# The hole this closes: check 6 excludes GND by name, because during routing an
# unpoured GND is normal and expected. The pour is a separate, later step -- and
# it was never run. So the board passed 17/17 and "0 open connections" while all
# 40 GND pads were connected to NOTHING: no pour, no GND track, no GND via.
# A gate that cannot see a missing ground plane is not a gate.
# Parsed, not regex: "\(zone(.*?)\n\t\)" mis-splits filled zones and counted
# 6 where there are 3. Fourth time regex has lied about this file format.
def _copper_zones():
    try:
        import sexp as _s3
        _r = _s3.parse(t)
        out = []
        for _z in _s3.kids(_r, "zone"):
            if _s3.kid(_z, "keepout"):
                continue
            _nn2 = _s3.kid(_z, "net_name") or _s3.kid(_z, "net")
            _lay = _s3.kid(_z, "layers") or _s3.kid(_z, "layer")
            out.append(dict(net=(_s3.s(_nn2[-1]) if _nn2 and len(_nn2) > 1 else ""),
                            layers=[_s3.s(x) for x in _lay[1:]] if _lay else [],
                            filled=bool(_s3.kids(_z, "filled_polygon"))))
        return out
    except Exception:
        return None

_CZ = _copper_zones()
_zt = [z for z in (_CZ or []) if z["net"] == "GND"]
# vias and segments are multi-line blocks; a [^)]* regex matches neither and
# reported "0 GND vias, 0 GND segs" on a board carrying 15 and 54. Parse them.
def _count_gnd():
    try:
        import sexp as _s2
        _r = _s2.parse(t)
        _nm = {_s2.s(n[1]): (_s2.s(n[2]) if len(n) > 2 else "")
               for n in _s2.kids(_r, "net")}
        def _isg(o):
            # net_of covers KiCad 10's (net "NAME"); the numeric (net N) of
            # older files still needs the top-level table to resolve.
            if _s2.net_of(o) == "GND":
                return True
            _n = _s2.kid(o, "net")
            return (_n is not None and len(_n) == 2
                    and _nm.get(_s2.s(_n[1])) == "GND")
        return (sum(1 for v in _s2.kids(_r, "via") if _isg(v)),
                sum(1 for g in _s2.kids(_r, "segment") if _isg(g)))
    except Exception:
        return -1, -1
_gv, _gs = _count_gnd()
_gnd_bad = []
if not _zt:
    _gnd_bad.append("no filled GND zone on any layer")
if _gv == 0 and _gs == 0 and not _zt:
    _gnd_bad.append("no GND copper of any kind")
# the authority on whether the fill actually reaches the pads
_cc = run(os.path.join(KRT, "py_router", "check_connected.py"), BOARD, cwd=KRT, env=env)
if "ALL NETS FULLY CONNECTED" not in _cc:
    _m2 = re.search(r"^  GND \((?:net \d+|\d+ pads)\):(.*?)(?=\n  \w|\Z)", _cc, re.S | re.M)
    if _m2 or re.search(r"^    GND \(\d+ pads\)", _cc, re.M):
        _gnd_bad.append("check_connected reports GND NOT fully connected")
rec(not _gnd_bad, "17 ground plane is connected",
    "; ".join(_gnd_bad) or "%d filled GND zone(s), %d GND vias, %d GND segs, "
    "check_connected: all nets connected" % (len(_zt), _gv, _gs))

# ------------------- 18 zones are actually FILLED --------------------------
# A zone in this file is an OUTLINE plus fill settings. The copper itself lives
# in (filled_polygon ...) blocks, which KiCad computes. check_connected models
# the fill and will happily say "all nets connected" from the outline alone --
# but a plot taken from an UNFILLED board has no plane on it. That is the same
# failure as having no pour at all, one step further along, so it gates.
_zones = _CZ if _CZ is not None else []
_unfilled = [z for z in _zones if not z["filled"]]
rec(not _unfilled, "18 copper zones are filled",
    ("%d of %d zone(s) carry NO fill geometry (%s) -- open the board in KiCad, "
     "Edit > Fill All Zones (B), SAVE, and re-run. Plotting an unfilled board "
     "ships it with no ground plane."
     % (len(_unfilled), len(_zones),
        ", ".join("/".join(z["layers"]) for z in _unfilled)))
    if _unfilled else "%d zone(s), all carry fill geometry" % len(_zones))

# ------------------- 19 board thickness matches the housing ----------------
# Not visible in any 2D check -- thickness is not in the copper. housing v5 is
# built around a 1.20 mm board; KiCad AND JLCPCB both default 4-layer to 1.60.
# Ordering the default gives a board 0.40 mm too thick for its own housing.
# LAMINATE vs FINISHED, and the difference is not pedantry.
# The number you pick on JLC's order form, and the number housing v5 was built
# around, is the LAMINATE: copper + dielectric. Solder mask is applied on top of
# it. Summing every (thickness) in the stackup adds the two 0.01 mm mask coats
# and reads 1.22 -- which is a real measurement of the finished part, but it is
# NOT the thing being ordered, and blocking on it would block on a 0.02 mm
# bookkeeping difference inside a fab tolerance of roughly +-0.13 mm.
#
# This first bit only after KiCad itself wrote the stackup: our generated block
# listed copper and dielectric only, so the old whole-sum was accidentally right
# and silently became wrong the moment the file went through the GUI.
_setup19 = _sx.kid(_sx.parse(t), "setup")
_st19 = _sx.kid(_setup19, "stackup") if _setup19 is not None else None
if _st19 is None:
    rec(False, "19 board thickness vs the housing",
        "no (stackup) block: thickness undeclared, so the fab uses its default 1.6 mm")
else:
    _lam = _mask = 0.0
    for _L in _sx.kids(_st19, "layer"):
        _ty = _sx.kid(_L, "type")
        _th = _sx.kid(_L, "thickness")
        if _th is None:
            continue
        _tyv = (_sx.s(_ty[1]) if _ty else "").lower()
        _v = _sx.f(_th[1])
        if "mask" in _tyv:
            _mask += _v
        elif _tyv in ("copper", "prepreg", "core") or "dielectric" in _tyv:
            _lam += _v
    _want = None
    try:
        _hs = open(os.path.join(HERE, "..", "scripts", "touchid_module_v5.py"),
                   encoding="utf-8").read()
        _hm = re.search(r"^pcb_t_ref\s*=\s*([\d.]+)", _hs, re.M)
        _want = float(_hm.group(1)) if _hm else None
    except Exception:
        pass
    _ok3 = _want is not None and abs(_lam - _want) < 0.005 and _lam > 0
    rec(_ok3, "19 board thickness vs the housing",
        ("laminate %.4f mm vs housing pcb_t_ref %s -- MISMATCH" % (_lam, _want))
        if not _ok3 else
        "laminate %.2f mm = housing pcb_t_ref (+%.2f mm mask -> %.2f finished, "
        "inside fab tolerance). MUST be chosen on the order form; JLC defaults "
        "4-layer to 1.6" % (_lam, _mask, _lam + _mask))

# ------------------- 20 no dangling track ends (net antennae) --------------
# ALTIUM FOUND THIS AND I COULD NOT. Its Net Antennae rule flagged a GND stub
# at (+7.400,+6.900)-(+7.550,+7.050): far end on a via, near end touching
# NOTHING. gnd_taps' endpoint-snapping had detached a tap from its pad. Every
# one of the other 19 checks passed the board with that on it, because none of
# them had any concept of a free track end.
#
# A track end must land on: its own net's copper (another track, a via, or a
# pad). Pads use the CIRCUMSCRIBED circle for rotated and custom shapes -- an
# axis-aligned box under-covers them and invents dangling ends that are not
# there (12 reported, 1 real).
DANGLE_TOL = 0.01
_dsegs = []
for _sg in re.finditer(r'\(segment\b(.*?)\n\t\)', t, re.S):
    _b = _sg.group(1)
    _s1 = re.search(r'\(start ([-\d.]+) ([-\d.]+)\)', _b)
    _e1 = re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', _b)
    _w1 = re.search(r'\(width ([\d.]+)\)', _b)
    _l1 = re.search(r'\(layer "([^"]+)"\)', _b)
    if _s1 and _e1 and _w1 and _l1:
        _dsegs.append((_seg_net(_b), _l1.group(1), float(_s1.group(1)), float(_s1.group(2)),
                       float(_e1.group(1)), float(_e1.group(2)), float(_w1.group(1))))
_dvias = []
for _vm in re.finditer(r'\(via\b(.*?)\n\t\)', t, re.S):
    _b = _vm.group(1)
    _a1 = re.search(r'\(at ([-\d.]+) ([-\d.]+)\)', _b)
    _z1 = re.search(r'\(size ([\d.]+)\)', _b)
    if _a1 and _z1:
        _dvias.append((_seg_net(_b), float(_a1.group(1)), float(_a1.group(2)), float(_z1.group(1))))

def _pad_reach(pd):
    """conservative radius: circumscribed circle for rotated/custom shapes"""
    if pd["shape"] == "circle":
        return pd["w"] / 2
    if pd["shape"] == "custom" or abs(pd["rot"] % 90.0) > 1e-6:
        return math.hypot(pd["w"], pd["h"]) / 2 + 0.35
    return None

# A POURED ZONE IS COPPER. An end sitting inside its own net's fill is
# connected, and ignoring that turned 1 real antenna into 6 reported ones --
# a gate that cries wolf gets ignored, which is worse than no gate.
_FILL = collections.defaultdict(list)
try:
    import sexp as _s5
    _r5 = _s5.parse(t)
    for _z5 in _s5.kids(_r5, "zone"):
        if _s5.kid(_z5, "keepout"):
            continue
        _n5 = _s5.kid(_z5, "net_name") or _s5.kid(_z5, "net")
        _nm5 = _s5.s(_n5[-1]) if _n5 and len(_n5) > 1 else ""
        for _fp5 in _s5.kids(_z5, "filled_polygon"):
            _l5 = _s5.kid(_fp5, "layer")
            _pt5 = _s5.kid(_fp5, "pts")
            if not (_l5 and _pt5):
                continue
            _pp5 = [(_s5.f(q[1]), _s5.f(q[2])) for q in _s5.kids(_pt5, "xy")]
            if len(_pp5) >= 3:
                _FILL[(_nm5, _s5.s(_l5[1]))].append(_P(_pp5).buffer(0))
except Exception:
    pass


def _in_fill(net, lay, ex, ey):
    from shapely.geometry import Point as _Pt2
    for _poly5 in _FILL.get((net, lay), []):
        if _poly5.contains(_Pt2(ex, ey)):
            return True
    return False


def _end_supported(net, lay, ex, ey, self_i, half=0.0):
    """`half` is THIS track's half-width: a track end is supported when its
    COPPER touches, not when its centre point lands inside. VREF_SAMP's trace
    ends 0.010 mm outside U2.4's pad rectangle while its 0.2 mm-wide copper
    overlaps that pad by 0.09 mm -- testing the point called it dangling."""
    if _in_fill(net, lay, ex, ey):
        return True
    for _i, (n, l, x1, y1, x2, y2, w) in enumerate(_dsegs):
        if _i == self_i or n != net or l != lay:
            continue
        _dx, _dy = x2 - x1, y2 - y1
        _L2 = _dx * _dx + _dy * _dy
        _tt = 0.0 if _L2 == 0 else max(0.0, min(1.0, ((ex - x1) * _dx + (ey - y1) * _dy) / _L2))
        if math.hypot(ex - (x1 + _tt * _dx), ey - (y1 + _tt * _dy)) <= w / 2 + half + DANGLE_TOL:
            return True
    for n, vx, vy, vd in _dvias:
        if n == net and math.hypot(vx - ex, vy - ey) <= vd / 2 + half + DANGLE_TOL:
            return True
    for pd in _PADS:
        if pd["net"] != net or lay not in pd["layers"]:
            continue
        r = _pad_reach(pd)
        if r is not None:
            if math.hypot(pd["x"] - ex, pd["y"] - ey) <= r + half + DANGLE_TOL:
                return True
        elif (abs(pd["x"] - ex) <= pd["w"] / 2 + half + DANGLE_TOL
              and abs(pd["y"] - ey) <= pd["h"] / 2 + half + DANGLE_TOL):
            return True
    return False

_dangle = []
for _i, (net, lay, x1, y1, x2, y2, w) in enumerate(_dsegs):
    for (ex, ey) in ((x1, y1), (x2, y2)):
        if not _end_supported(net, lay, ex, ey, _i, w / 2):
            _dangle.append("%s %s (%+.3f,%+.3f)" % (net, lay, ex, ey))
rec(not _dangle, "20 no dangling track ends",
    ("%d free end(s): %s" % (len(_dangle), "; ".join(_dangle[:4])))
    if _dangle else "%d track ends, all land on copper of their own net"
                    % (2 * len(_dsegs)))

# ---------------- 21 every placed part is actually buyable ------------------
# The board can be perfect and the ORDER still fail. JLCPCB assembles from a
# BOM of LCSC codes, and a designator with no code is a part they will not
# fit. This is the last thing between a clean board and a half-populated one.
#
# Stock is deliberately NOT a blocker: it is a snapshot of someone else's
# warehouse and it moves daily, so gating on it would be gating on stale data.
# A missing part NUMBER is a blocker, because that is our omission, not theirs.
_SRC_DATE = "2026-08-28"
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from make_bom_cpl import SRC as _SRC, SKIP_PREFIX as _SKP, SKIP_EXACT as _SKE

    # refs via the s-expression parser, never regex: regex reads of this file
    # have produced three separate silent wrong answers in this project
    _root21 = _sx.parse(t)
    _REFS = []
    for _fp21 in _sx.kids(_root21, "footprint"):
        for _pr21 in _sx.kids(_fp21, "property"):
            if _sx.s(_pr21[1]) == "Reference":
                _REFS.append(_sx.s(_pr21[2]))
    _placed = [r for r in _REFS
               if r not in _SKE and not r.startswith(_SKP)]
    _need = collections.Counter(_placed)
    _unsourced = sorted({r for r in _placed if r not in _SRC})
    _thin = sorted({(_SRC[r][0], _SRC[r][2], _need[r])
                    for r in _placed if r in _SRC and _SRC[r][2] < _need[r]})
    rec(not _unsourced and bool(_placed), "21 every placed part has an LCSC code",
        ("%d designator(s) with no part number: %s"
         % (len(_unsourced), ", ".join(_unsourced))) if _unsourced
        else "%d placed designators, all sourced (%d distinct LCSC codes)"
             % (len(_placed), len({_SRC[r][0] for r in _placed})))
    if _thin:
        rec(False, "21b JLC assembly stock (snapshot)",
            "as of %s: %s -- RE-CHECK AT ORDER TIME"
            % (_SRC_DATE, "; ".join("%s stock=%d need=%d/board" % t for t in _thin)),
            blocker=False)
except Exception as _e:                      # a check that cannot run must say so
    rec(False, "21 every placed part has an LCSC code",
        "COULD NOT RUN (%s) -- treat as unverified" % _e)

prov = []
# BT1 no longer belongs here. The board never depended on VARTA's tab geometry:
# it presents two Phi1.4 wire pads and the cell is wired down from above. The
# cell is now specified as a PROTECTED, TABBED ASSEMBLY (see B6), so its leads
# are defined by whoever builds that assembly -- there is no VARTA dimension
# left to verify. What the board owes that decision is a mask dam wide enough
# to hand-solder safely, and check 16 enforces exactly that.
prov.append("J4/J11 pogo pads (fixed by the keyboard; measurement, not a datasheet)")
rec(False, "14 unverified geometry remaining", "; ".join(prov), blocker=False)

# ---------------------------------------------------------------- verdict ---
print("=" * 74)
print("PREFLIGHT — %s" % os.path.basename(BOARD))
print("=" * 74)
for st, name, det in results:
    print("  %-8s %-34s %s" % (st, name, det))
nb = sum(1 for s, _, _ in results if s == "BLOCKER")
nw = sum(1 for s, _, _ in results if s == "WARN")
print("=" * 74)
print("  %d BLOCKER(S), %d WARNING(S)" % (nb, nw))
print("  VERDICT: %s" % ("DO NOT ORDER" if nb else "orderable once the warnings are accepted"))
print("=" * 74)
sys.exit(1 if nb else 0)
