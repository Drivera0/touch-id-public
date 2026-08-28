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
BOARD = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "pcb-v3-handoff.kicad_pcb")
KRT = os.environ.get("KRT", "/tmp/krt")

FAB_MIN_CU, DESIGN_CU = 0.127, 0.20
VIA_MIN_D, VIA_MIN_DRILL = 0.45, 0.20        # JLC standard 4-layer
POWER = {"VSTOR", "VBAT", "VIN_DC", "LX", "SENSOR_3V3", "SENSOR_MCU_3V3"}

results = []
def rec(ok, name, detail="", blocker=True):
    results.append(("PASS" if ok else ("BLOCKER" if blocker else "WARN"), name, detail))

t = open(BOARD, encoding="utf-8", errors="replace").read()
nn = dict(re.findall(r'\(net (\d+) "([^"]*)"\)', t))

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
rec(opens == 0 and not unrouted, "6  every connection routed",
    "%d open pad(s); unrouted nets: %s" % (opens, ", ".join(unrouted) or "none"))

o = run(os.path.join(KRT, "py_router", "check_drc.py"), BOARD, "--clearance", str(DESIGN_CU),
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
rec(bad == 0, "7  antenna keep-out clear of copper", "%d object(s) inside" % bad)

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
under = sum(c for k, c in widths.items() if k < DESIGN_CU - 1e-9)
rec(under == 0, "9  no track below the %.2f design rule" % DESIGN_CU,
    "%d segment(s), min %.4f" % (under, min(widths) if widths else 0))

# ------------------------------------------------------- 10 power net width --
# "power route neck-down" deliberately narrows to signal width where a 0.4 mm
# track enters a 0.24 mm pad. What matters is that the net's TRUNK is 0.4, not
# that its minimum is -- testing min() flagged all six as thin every run.
nofat = [n for n in POWER if n in per_net and max(per_net[n]) < 0.399]
necks = {n: sum(1 for x in per_net[n] if x < 0.399) for n in POWER if n in per_net}
rec(not nofat, "10 power nets have a 0.40 trunk",
    ("no 0.40 segment on: " + ", ".join(nofat)) if nofat else
    "all 6 trunks 0.40 (%d neck-down segs at pads, by design)" % sum(necks.values()),
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
prov = []
if "VARTA gives CP1254" in open(os.path.join(HERE, "build_pcb_v3.py"), encoding="utf-8").read():
    prov.append("BT1 cell-tab pads (VARTA publishes no tab geometry)")
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
