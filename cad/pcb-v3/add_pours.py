"""
add_pours.py -- put the F.Cu and B.Cu ground pours onto a ROUTED board.

WHY THIS EXISTS
---------------
build_pcb_v3.py has a pour emitter but ships it OFF (EMIT_GND_POURS = False),
and that is correct: a pour spanning the whole board on three layers is one
giant obstacle to every non-GND net, so routing with pours down blocks every
pad escape. Pours go on LAST, which is the normal PCB order anyway.

The problem was that "last" had no script. The F.Cu and B.Cu pours existed only
inside pcb-v5-routed-wip.kicad_pcb, put there by hand in KiCad, so every
regeneration of the board silently lost them -- and a board with no F.Cu/B.Cu
pour reads as MANY open pads for a reason that has nothing to do with routing.
That is exactly what happened on the 0201 rebuild: 10 opens, seven of them GND
pads on the bottom side, purely because no B.Cu pour existed to connect them.

A missing step that only lives in someone's hands is not a step. So it is here.

WHAT IT WRITES
--------------
The settings are lifted from the pours in pcb-v5-routed-wip that actually
worked, NOT invented:

    connect_pads yes (clearance 0.1)     min_thickness 0.1
    thermal_gap 0.2                      thermal_bridge_width 0.2
    island_removal_mode 0
    polygon inset 0.5 mm from the board half-extents

min_thickness 0.1 rather than the emitter's 0.25 is the one that matters most:
it lets copper flow through the narrow necks between parts, which is the
difference between a pour in 5 pieces and a pour in 15.

In2.Cu is NOT written here -- route_planes.py lays that plane down, and writing
a second In2.Cu zone would give the board two overlapping planes on one layer.

Usage:  python add_pours.py IN.kicad_pcb OUT.kicad_pcb
"""
import re
import sys

HALF_X, HALF_Y = 10.00, 9.50
INSET = 0.50                 # matches the pours that worked in v5
TAG = "GND_POUR"


def main():
    src, dst = sys.argv[1], sys.argv[2]
    raw = open(src, encoding="utf-8", errors="replace", newline="").read()
    crlf = "\r\n" in raw
    t = raw.replace("\r\n", "\n")

    # ---- resolve GND the way the file spells it, both dialects ----
    # KiCad 8 writes a (net N "NAME") table and refers by number; KiCad 10 drops
    # the table and writes (net "NAME") inline. Guessing wrong here is the same
    # bug that once made pour_truth report 34 opens on an 8-open board.
    m = re.search(r'\(net (\d+) "GND"\)', t)
    if m:
        netline = '\t\t(net %s)\n\t\t(net_name "GND")' % m.group(1)
    elif '(net "GND")' in t:
        netline = '\t\t(net "GND")'
    else:
        sys.exit("no GND net found in %s -- refusing to guess" % src)

    # ---- idempotent: drop any pour we put here before ----
    spans = []
    for mm in re.finditer(r"\(zone[\s\n]", t):
        i = mm.start()
        d = 0
        j = i
        while True:
            c = t[j]
            if c == '"':
                j += 1
                while t[j] != '"':
                    j += 2 if t[j] == "\\" else 1
            elif c == "(":
                d += 1
            elif c == ")":
                d -= 1
                if d == 0:
                    break
            j += 1
        if TAG in t[i:j + 1]:
            spans.append((i, j + 1))
    for a, b in sorted(spans, reverse=True):
        e = b
        while e < len(t) and t[e] in "\n\t ":
            e += 1
        s = a
        while s > 0 and t[s - 1] in "\t ":
            s -= 1
        t = t[:s] + t[e:]
    if spans:
        print("removed %d existing %s zone(s)" % (len(spans), TAG))

    x, y = HALF_X - INSET, HALF_Y - INSET
    pts = " ".join("(xy %g %g)" % p for p in
                   [(-x, -y), (x, -y), (x, y), (-x, y)])
    body = []
    for lay in ("F.Cu", "B.Cu"):
        body.append(
            '\t(zone\n'
            '%s\n'
            '\t\t(layer "%s")\n'
            '\t\t(name "%s_%s")\n'
            '\t\t(hatch edge 0.5)\n'
            '\t\t(connect_pads yes\n\t\t\t(clearance 0.1)\n\t\t)\n'
            '\t\t(min_thickness 0.1)\n'
            '\t\t(fill yes\n'
            '\t\t\t(thermal_gap 0.2)\n'
            '\t\t\t(thermal_bridge_width 0.2)\n'
            '\t\t\t(island_removal_mode 0)\n'
            '\t\t)\n'
            '\t\t(polygon\n\t\t\t(pts\n\t\t\t\t%s\n\t\t\t)\n\t\t)\n'
            '\t)\n' % (netline, lay, TAG, lay.replace(".", "_"), pts))

    i = t.rstrip().rfind(")")
    t = t[:i] + "".join(body) + t[i:]
    print("added F.Cu and B.Cu GND pours, %.2f x %.2f mm (inset %.2f)"
          % (2 * x, 2 * y, INSET))

    d = 0
    for c in t:
        if c == "(":
            d += 1
        elif c == ")":
            d -= 1
    if d != 0:
        sys.exit("unbalanced -- refusing to write")
    open(dst, "w", encoding="utf-8",
         newline="\r\n" if crlf else "\n").write(t)
    print("wrote %s" % dst)
    print("\nNow fill zones in KiCad, then run pour_truth.py -- the pour has no\n"
          "filled_polygon geometry until KiCad computes it, and pour_truth will\n"
          "refuse to give a verdict without it.")


if __name__ == "__main__":
    main()
