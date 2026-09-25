# Pre-order verification for pcb-v2-corrected.kicad_pcb.
#
# The check that matters most is COVERAGE: overlay each part's real land
# pattern (from footprints_lcsc.py, pulled from JLCPCB's own library) onto the
# copper we actually generated, and confirm every terminal sits fully on its
# own pad. That is the check whose absence let a completely wrong ESP32
# footprint reach the point of payment on 2026-08-19.
#
# Run: python verify_board.py    (exit code 0 = clean)

import re, sys, itertools
from shapely.geometry import Point, box
from shapely import affinity
import footprints_lcsc as FP

PCB = "pcb-v2-corrected.kicad_pcb"
MIN_CU   = 0.127     # JLCPCB minimum copper-to-copper
MIN_MASK = 0.100     # minimum solder mask dam JLCPCB will still print
BX, BY   = 9.8, 8.8  # board half-extents
EDGE     = 0.20      # required copper-to-board-edge

fails, warns = [], []
def bad(m):  fails.append(m); print("  FAIL  " + m)
def warn(m): warns.append(m); print("  warn  " + m)

# ---------------------------------------------------------------- load pads
pat = re.compile(
    r'\(pad "([^"]*)" (\w+) (\w+) \(at ([-\d.]+) ([-\d.]+)(?: ([\d.]+))?\)'
    r' \(size ([\d.]+) ([\d.]+)\)(.*?)\(layers ([^)]*)\)([^\n]*)')
pads = []
for m in pat.finditer(open(PCB).read()):
    name, ptype, shape, x, y, rot, w, h, mid, layers, tail = m.groups()
    x, y, rot, w, h = float(x), float(y), float(rot or 0), float(w), float(h)
    mm = re.search(r'solder_mask_margin ([-\d.]+)', tail)
    def geom(exp):
        if shape == "circle":
            return Point(x, y).buffer(w / 2 + exp, 64)
        g = box(x - w/2 - exp, y - h/2 - exp, x + w/2 + exp, y + h/2 + exp)
        return affinity.rotate(g, rot, origin=(x, y)) if rot else g
    pads.append(dict(name=name or "MH", cu=geom(0),
                     mask=geom(float(mm.group(1)) if mm else 0.0),
                     F='F.Cu' in layers, B='B.Cu' in layers,
                     part=(name or "MH").split('-')[0], x=x, y=y))
by = {}
for p in pads:
    by.setdefault(p['part'], []).append(p)

print(f"\n[1] pad inventory  ({len(pads)} pads)")
EXPECT = {'U1': 61, 'U2': 5, 'C1': 2, 'C2': 2, 'C3': 2, 'C4': 2,
          'J2': 6, 'J4': 6, 'J11': 4, 'MH': 2, 'TP': 3}
for part, n in sorted(EXPECT.items()):
    got = len(by.get(part, []))
    print(f"      {part:4s} {got:3d}" + ("" if got == n else f"   expected {n}"))
    if got != n:
        bad(f"{part} has {got} pads, expected {n}")

# ------------------------------------------------------- [2] coverage check
print("\n[2] coverage: does each real terminal sit on its own pad?")
def cover(label, terminals, padname):
    """terminals: list of (key, shapely geom) in board coords.
    All of these parts are on F.Cu, so only F.Cu copper can touch them --
    the pogo pads (J4/J11) and test pads (TP-*) live on B.Cu."""
    for key, g in terminals:
        own = [p for p in pads if p['name'] == padname(key)]
        if not own:
            bad(f"{label}: no pad named {padname(key)}"); continue
        frac = g.intersection(own[0]['cu']).area / g.area
        if frac < 0.999:
            bad(f"{label} {key}: only {frac*100:.1f}% of the terminal is on "
                f"{padname(key)}")
        # and it must not touch anything else
        for q in pads:
            if q is own[0] or not q['F']:
                continue
            if g.intersects(q['cu']) and g.intersection(q['cu']).area > 1e-9:
                bad(f"{label} {key}: terminal also overlaps {q['name']}")

CY = -FP.U1_BODY_DY
u1t = []
for pin, x, y, w, h in FP.u1_perimeter_pads():
    u1t.append((pin, box(x-w/2, CY+y-h/2, x+w/2, CY+y+h/2)))
for pin, x, y in FP.u1_corner_pads():
    s = FP.U1_CORNER_SIDE/2
    u1t.append((pin, box(x-s, CY+y-s, x+s, CY+y+s)))
cover("U1", u1t, lambda k: f"U1-{k}")
for i, (x, y) in enumerate(FP.u1_thermal_pads(), 1):
    s = FP.U1_TH_SIDE/2
    cover("U1", [(i, box(x-s, CY+y-s, x+s, CY+y+s))], lambda k: f"U1-49_{k}")

ux, uy = -7.6, -3.0
cover("U2", [(p, box(ux+dx-FP.U2_PAD_W/2, uy+dy-FP.U2_PAD_H/2,
                     ux+dx+FP.U2_PAD_W/2, uy+dy+FP.U2_PAD_H/2))
             for p, (dx, dy) in FP.U2_PINS.items()], lambda k: f"U2-{k}")

for nm, cx, cy, A, C, O in [("C1",-7.6,-4.8,*(FP.C0402_ALONG,FP.C0402_ACROSS,FP.C0402_OFF)),
                            ("C2",-7.6,-6.7,*(FP.C0402_ALONG,FP.C0402_ACROSS,FP.C0402_OFF)),
                            ("C3", 7.6,-3.10,*(FP.C0805_ALONG,FP.C0805_ACROSS,FP.C0805_OFF)),
                            ("C4", 7.6,-6.71,*(FP.C0805_ALONG,FP.C0805_ACROSS,FP.C0805_OFF))]:
    t = [(i, box(cx-C/2, cy+s*O-A/2, cx+C/2, cy+s*O+A/2))
         for i, s in ((1, -1), (2, +1))]
    cover(nm, t, lambda k, nm=nm: f"{nm}-{k}")
if not fails:
    print("      every terminal fully on its own pad, touching nothing else")

# --------------------------------------------------- [3] copper clearance
print(f"\n[3] copper clearance (min {MIN_CU} mm, or a mask dam >= {MIN_MASK})")
tight = 0
for a, b in itertools.combinations(pads, 2):
    if not ((a['F'] and b['F']) or (a['B'] and b['B'])):
        continue
    if a['part'] == b['part'] and a['part'] in ('U1',):
        continue          # intra-module pads are the vendor's own geometry
    d = a['cu'].distance(b['cu'])
    if d >= MIN_CU:
        continue
    dam = a['mask'].distance(b['mask'])
    if a['part'] == b['part'] and dam >= MIN_MASK:
        tight += 1
        continue
    bad(f"{a['name']} <-> {b['name']}: copper {d:.4f}, mask dam {dam:.4f}")
mins = min(a['cu'].distance(b['cu']) for a, b in itertools.combinations(pads, 2)
           if ((a['F'] and b['F']) or (a['B'] and b['B'])) and a['part'] != b['part'])
print(f"      minimum between different parts : {mins:.4f} mm")
print(f"      sub-{MIN_CU} pairs inside one land, mask-separated : {tight}")

# --------------------------------------------------------- [4] board edge
print(f"\n[4] board edge (need {EDGE} mm to x=+-{BX}, y=+-{BY})")
worst = 99
for p in pads:
    x0, y0, x1, y1 = p['cu'].bounds
    m = min(BX-abs(x0), BX-abs(x1), BY-abs(y0), BY-abs(y1))
    if m < EDGE:
        bad(f"{p['name']} is {m:.3f} mm from the board edge")
    worst = min(worst, m)
print(f"      closest approach : {worst:.3f} mm")

# ------------------------------------------------------------- [5] netlist
print("\n[5] netlist spot-checks")
txt = open(PCB).read()
def net_of(pn):
    m = re.search(r'\(pad "%s".*?\(net (\d+) "([^"]*)"\)' % re.escape(pn), txt)
    return m.group(2) if m else None
for pn, want in [("U1-3", "+3V3"), ("U1-8", "+3V3"), ("U1-5", "+3V3"),
                 ("U1-22", "+3V3"), ("U1-6", "FP_INT"), ("U1-23", "BOOT_IO9"),
                 ("U1-26", "USB_DN"), ("U1-27", "USB_DP"), ("U1-30", "FP_TX"),
                 ("U1-31", "FP_RX"), ("U1-1", "GND"), ("U1-49_1", "GND"),
                 ("U2-1", "+3V3"), ("U2-2", "GND"), ("U2-3", "VBAT"),
                 ("U2-4", "VBAT"), ("U2-5", "GND"),
                 ("C1-1", "+3V3"), ("C2-1", "VBAT"),
                 ("C3-1", "VBAT"), ("C4-1", "VBAT")]:
    got = net_of(pn)
    if got != want:
        bad(f"{pn} is on {got}, expected {want}")
    else:
        print(f"      {pn:9s} {got}")

print("\n" + "="*58)
print(f"{len(fails)} failures, {len(warns)} warnings")
sys.exit(1 if fails else 0)
