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
nn = dict(re.findall(r'\(net (\d+) "([^"]*)"\)', t))
_GND_ID = next((i for i, n in nn.items() if n == "GND"), None)

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
            _n = re.search(r'\(net \d+ "([^"]*)"\)', pm.group(2))
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
    if a_ and sz and _box(float(a_.group(1))-float(sz.group(1))/2, float(a_.group(2))-float(sz.group(1))/2,
                          float(a_.group(1))+float(sz.group(1))/2, float(a_.group(2))+float(sz.group(1))/2).intersects(ko_all):
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
            _poly = _P(_pp)
            for _L in _ls:
                _kz = ko_by_layer.get(_L)
                if _kz is not None and _poly.intersects(_kz):
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
    w = re.search(r'\(width ([\d.]+)\)', b); n = re.search(r'\(net (\d+)\)', b)
    if w:
        widths[float(w.group(1))] += 1
        per_net[nn.get(n.group(1), "?") if n else "?"].append(float(w.group(1)))
under = sum(c for k, c in widths.items() if k < DESIGN_TRACK - 1e-9)
rec(under == 0, "9  no track below the %.3f track rule" % DESIGN_TRACK,
    "%d segment(s), min %.4f" % (under, min(widths) if widths else 0))

# ------------------------------------------------------- 10 power net width --
# "power route neck-down" deliberately narrows to signal width where a 0.4 mm
# track enters a 0.24 mm pad. What matters is that the net's TRUNK is 0.4, not
# that its minimum is -- testing min() flagged all six as thin every run.
# A power net whose whole run sits inside the neck-down zone of its own pads
# cannot be 0.40 anywhere, and should not be: you cannot land 0.40 copper on a
# 0.24 mm QFN pad without a taper. Only flag a net that is long enough to have
# a trunk and still has none. (LX is 1.9 mm end to end by design -- short loop
# area is the whole point of a switching node.)
def _netlen(n):
    tot = 0.0
    for m in re.finditer(r'\(segment\b(.*?)\n\t\)', t, re.S):
        b = m.group(1); nm = re.search(r'\(net (\d+)\)', b)
        if not nm or nn.get(nm.group(1)) != n:
            continue
        s_ = re.search(r'\(start ([-\d.]+) ([-\d.]+)\)', b)
        e_ = re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', b)
        if s_ and e_:
            tot += math.hypot(float(e_.group(1))-float(s_.group(1)),
                              float(e_.group(2))-float(s_.group(2)))
    return tot
NECK = 2.5   # --neckdown-length default, mm, applied at BOTH ends
nofat = [n for n in POWER if n in per_net and max(per_net[n]) < 0.399
         and _netlen(n) > 2 * NECK]
necks = {n: sum(1 for x in per_net[n] if x < 0.399) for n in POWER if n in per_net}
rec(not nofat, "10 power nets have a 0.40 trunk",
    ("no 0.40 trunk on: " + ", ".join(nofat)) if nofat else
    "trunks OK (%d neck-down segs at pads, by design; short nets exempt)"
    % sum(necks.values()),
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
sys.path.insert(0, HERE)
import sexp as _sx
_PADS = _sx.pads(t)
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
            _nn2 = _s3.kid(_z, "net_name")
            _lay = _s3.kid(_z, "layers") or _s3.kid(_z, "layer")
            out.append(dict(net=_s3.s(_nn2[1]) if _nn2 and len(_nn2) > 1 else "",
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
            _n = _s2.kid(o, "net")
            return _n is not None and _nm.get(_s2.s(_n[1])) == "GND"
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
    _m2 = re.search(r"^  GND \(net \d+\):(.*?)(?=\n  \w|\Z)", _cc, re.S | re.M)
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
_m3 = re.search(r"\(stackup(.*?)\n\t\t\)", t, re.S)
if not _m3:
    rec(False, "19 board thickness vs the housing",
        "no (stackup) block: thickness undeclared, so the fab uses its default 1.6 mm")
else:
    _tot = sum(float(x) for x in re.findall(r"\(thickness ([\d.]+)\)", _m3.group(1)))
    _want = None
    try:
        _hs = open(os.path.join(HERE, "..", "scripts", "touchid_module_v5.py"),
                   encoding="utf-8").read()
        _hm = re.search(r"^pcb_t_ref\s*=\s*([\d.]+)", _hs, re.M)
        _want = float(_hm.group(1)) if _hm else None
    except Exception:
        pass
    _ok3 = _want is not None and abs(_tot - _want) < 0.005
    rec(_ok3, "19 board thickness vs the housing",
        ("stackup %.3f mm vs housing pcb_t_ref %s -- MISMATCH"
         % (_tot, _want)) if not _ok3 else
        "%.2f mm, matches housing pcb_t_ref (SELECT THIS EXPLICITLY WHEN ORDERING)")
    if _ok3:
        results[-1] = (results[-1][0], results[-1][1],
                       "%.2f mm = housing pcb_t_ref. MUST be chosen on the order "
                       "form; JLC defaults 4-layer to 1.6" % _tot)

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
