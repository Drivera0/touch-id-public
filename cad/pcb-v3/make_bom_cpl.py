"""
make_bom_cpl.py — generate the JLCPCB assembly files from the routed board.

JLCPCB places parts from TWO 2D files. It never sees a 3D model:

    BOM  designator -> LCSC part number  (it knows the real part from ITS OWN
                                          library, keyed by that number)
    CPL  designator, X, Y, rotation, layer

WHAT THIS SCRIPT WILL AND WILL NOT DO
-------------------------------------
The CPL is pure geometry and is generated in full, correctly transformed.

The BOM is generated as a SKELETON with the LCSC column blank wherever we do
not genuinely know the number. **It does not invent part numbers.** The few
that are filled in are traced in PART-LIBRARY.md; everything else is yours to
source, and the file says so per line.

TWO TRAPS, BOTH OF WHICH HAVE RUINED REAL BOARDS
------------------------------------------------
1. ORIGIN. KiCad's file is Y-DOWN with this board centred on (0,0); JLC wants
   Y-UP from the board's lower-left corner. Transform applied here:
       X = x + 9.65        Y = 9.65 - y
   Verified against the corners: file(-9.65,+9.65) -> (0,0) and
   file(+9.65,-9.65) -> (19.30,19.30).

2. ROTATION. The number written here is KiCad's footprint angle. **JLC's
   expected orientation for a given package frequently differs**, which is the
   classic way to get a whole reel placed 90 or 180 degrees out. This script
   CANNOT verify that -- only JLC's own part preview can, per part. Every
   rotation below must be eyeballed against that preview before you order.

Excluded from the CPL, deliberately: TP* (bare probe pads), J2/J3/J4/J11 (pads,
not parts -- pogo contacts and hand-wired pads), BT1 (cell wired from above),
and the unreferenced NPTH mounting holes. Nothing there is machine-placed.
"""
import collections, csv, os, re, sys
import sexp

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(HERE, "pcb-v3-handoff.kicad_pcb")
OUT = os.path.join(HERE, "..", "exports")
HALF = 9.65                      # board is 19.30 square, centred on the origin

# Not machine-placed. Everything here is a pad, a hole, or hand-wired.
SKIP_PREFIX = ("TP", "J", "MH")
SKIP_EXACT = {"BT1", "", "Un0", "Un1"}

# LCSC numbers we have actually traced (PART-LIBRARY.md). NOTHING is invented:
# a blank cell below means "we do not know", and that is the honest answer.
LCSC = {
    "U1": "C5118826",            # Raytac MDBT50Q-1MV2, land cross-checked
}
# Footprint-derivation references. These prove the LAND is right; they are NOT
# a claim that this exact part is the one to fit for that value.
LAND_REF = {
    "0402": "land traced from C1525",
    "0603": "land traced from C19666",
}


def main():
    text = open(BOARD, encoding="utf-8", errors="replace").read()
    root = sexp.parse(text)
    k, kd, s, f = sexp.kids, sexp.kid, sexp.s, sexp.f
    sys.path.insert(0, HERE)
    from netlist_v3 import PARTS as NL
    val = {p["ref"]: p["name"] for p in NL}

    rows = []
    for fp in k(root, "footprint"):
        ref = "?"
        for pr in k(fp, "property"):
            if s(pr[1]) == "Reference":
                ref = s(pr[2])
        if ref in SKIP_EXACT or ref.startswith(SKIP_PREFIX):
            continue
        at = kd(fp, "at")
        x, y = f(at[1]), f(at[2])
        rot = f(at[3]) if len(at) > 3 else 0.0
        lay = kd(fp, "layer")
        side = "Bottom" if lay and s(lay[1]).startswith("B.") else "Top"
        rows.append(dict(ref=ref,
                         X=round(x + HALF, 4),        # -> lower-left origin
                         Y=round(HALF - y, 4),        # -> Y up
                         rot=round(rot % 360, 2),
                         side=side,
                         value=val.get(ref, "")))
    rows.sort(key=lambda r: (re.sub(r"\d", "", r["ref"]),
                             int(re.sub(r"\D", "", r["ref"]) or 0)))

    os.makedirs(OUT, exist_ok=True)
    cpl = os.path.join(OUT, "touchid-v3-CPL.csv")
    with open(cpl, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in rows:
            w.writerow([r["ref"], "%.4fmm" % r["X"], "%.4fmm" % r["Y"],
                        r["side"], "%g" % r["rot"]])

    # ---- BOM, grouped by value ------------------------------------------
    groups = collections.OrderedDict()
    for r in rows:
        groups.setdefault(r["value"], []).append(r["ref"])
    bom = os.path.join(OUT, "touchid-v3-BOM.csv")
    with open(bom, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Comment", "Designator", "Footprint",
                    "JLCPCB Part # (LCSC Part #)", "NOTE"])
        for v, refs in groups.items():
            pkg = ""
            m = re.search(r"\b(0402|0603|0805|X2SON-4|VQFN-20)\b", v)
            if m:
                pkg = m.group(1)
            lc = ""
            for rf in refs:
                if rf in LCSC:
                    lc = LCSC[rf]
            note = "" if lc else "*** SOURCE THIS -- no LCSC number known ***"
            if pkg in LAND_REF and not lc:
                note += "  (" + LAND_REF[pkg] + ")"
            w.writerow([v, ",".join(refs), pkg, lc, note])

    print("wrote %s   (%d parts placed)" % (cpl, len(rows)))
    print("wrote %s   (%d BOM lines, %d still need an LCSC number)"
          % (bom, len(groups), sum(1 for v, r in groups.items()
                                   if not any(x in LCSC for x in r))))
    print()
    print("placement extents: X %.3f..%.3f   Y %.3f..%.3f   (board is 0..19.30)"
          % (min(r["X"] for r in rows), max(r["X"] for r in rows),
             min(r["Y"] for r in rows), max(r["Y"] for r in rows)))
    sides = collections.Counter(r["side"] for r in rows)
    print("sides:", dict(sides))
    print("rotations in use:", sorted({r["rot"] for r in rows}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
