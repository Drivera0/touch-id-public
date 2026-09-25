"""
inject_pogo_zones.py -- put a NO-VIA rule area over every pogo contact.

WHY
---
A through via drilled over a J4/J11 pad exits through the face the keyboard's
sprung pin lands on. It ruins the contact. The rule holds even for J4.5, which
is itself GND -- "same net, so it is fine" is wrong here, and that reasoning
put two vias 0.502 and 0.614 mm inside J4.5 once already.

The router will not invent this constraint, and asking it to fix the result
afterwards does not work: routed late, the only corridor left for the J11 nets
IS the pogo contact, and the router takes it. So the zones go in BEFORE
routing, and ROUTE-V4.md puts those nets in stage 1 for the same reason.

RING SIZE
---------
    pad radius                                   1.00   (2.00 pads, caliper)
  + whichever of these binds:
        via radius + clearance   0.20 + 0.10  =  0.30
        drill radius + JLC via-hole-to-track
                                 0.10 + 0.20  =  0.30
                                              -------
                                                 1.30
A little margin over that, so KiCad's own rewriting of geometry on format
migration cannot eat it: 1.35.

Usage:  python inject_pogo_zones.py IN.kicad_pcb OUT.kicad_pcb
        python inject_pogo_zones.py IN.kicad_pcb OUT.kicad_pcb --strip
"""
import math
import re
import sys

import pour_truth as pt

RING = 1.35
SIDES = 16
TAG = "POGO_NOVIA"


def main():
    src, dst = sys.argv[1], sys.argv[2]
    strip = "--strip" in sys.argv
    raw = open(src, encoding="utf-8", errors="replace", newline="").read()
    crlf = "\r\n" in raw
    t = raw.replace("\r\n", "\n")

    # remove any we put in before (idempotent, and this is the --strip path)
    spans = []
    for m in re.finditer(r"\(zone[\s\n]", t):
        i = m.start()
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
    print("removed %d existing %s zone(s)" % (len(spans), TAG))

    if not strip:
        pads, _s, _v, _p = pt.parse(src)
        pogo = [p for p in pads if p["ref"] in ("J4", "J11")]
        if not pogo:
            sys.exit("no J4/J11 pads found -- wrong board?")
        body = []
        for p in pogo:
            pts = []
            for k in range(SIDES):
                a = 2 * math.pi * k / SIDES
                pts.append("(xy %.4f %.4f)" % (p["x"] + RING * math.cos(a),
                                               p["y"] + RING * math.sin(a)))
            body.append(
                '\t(zone\n'
                '\t\t(net 0)\n'
                '\t\t(net_name "")\n'
                '\t\t(layers "F.Cu" "In1.Cu" "In2.Cu" "B.Cu")\n'
                '\t\t(name "%s_%s_%s")\n'
                '\t\t(hatch edge 0.5)\n'
                '\t\t(connect_pads (clearance 0))\n'
                '\t\t(min_thickness 0.25)\n'
                '\t\t(keepout\n'
                '\t\t\t(tracks allowed)\n'
                '\t\t\t(vias not_allowed)\n'
                '\t\t\t(pads allowed)\n'
                '\t\t\t(copperpour allowed)\n'
                '\t\t\t(footprints allowed)\n'
                '\t\t)\n'
                '\t\t(polygon\n\t\t\t(pts\n\t\t\t\t%s\n\t\t\t)\n\t\t)\n'
                '\t)\n' % (TAG, p["ref"], p["pad"], " ".join(pts)))
        i = t.rstrip().rfind(")")
        t = t[:i] + "".join(body) + t[i:]
        print("injected %d no-via rings of r=%.2f mm" % (len(pogo), RING))

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


if __name__ == "__main__":
    main()
