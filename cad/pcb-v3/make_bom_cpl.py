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
1. ORIGIN. **The CPL must live in the SAME coordinate space as the gerbers**,
   because that is the only thing the fab can align it against. Getting this
   wrong does not corrupt one part, it moves EVERY part by the same offset.

   This emits "lower-left corner" coordinates:
       X = x + 9.65        Y = 9.65 - y
   giving 0..19.30, which is the convention JLCPCB's own documentation
   describes -- **and it is only correct because the gerbers are now plotted
   from that same origin.** The board carries `(aux_axis_origin -9.65 9.65)`
   (KiCad is Y-DOWN, so +9.65 is the bottom edge) and is plotted with
   "use drill/place file origin" ON, so Edge_Cuts.gbr also runs 0..19.30.
   The Excellon drill files follow the same origin.

   It was briefly the other way round and JLCPCB's viewer caught it: gerbers
   centred on (0,0) against a corner-based CPL drew every component floating
   beside the board, offset by exactly the 9.65 mm half-width in both axes.
   Either convention works; only agreement matters.

   verify_handoff.py does not settle this by re-deriving a formula -- two
   derivations of the same wrong ASSUMPTION still agree. It reads the outline
   out of Edge_Cuts.gbr and requires every placement to fall inside it.

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

# ---------------------------------------------------------------- sourcing --
# Every line below was read from JLCPCB's OWN assembly library on 2026-08-28
# (POST /api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList
# /v2), not from LCSC's shop and not from a datasheet. That distinction matters:
# LCSC SELLS parts JLCPCB cannot PLACE, and the two stock figures are different
# numbers drawn from different warehouses. A part with LCSC stock and no JLC
# assembly stock will silently come back as "cannot be assembled" after you pay.
#
# ref -> (LCSC code, JLC library type, JLC assembly stock at time of check,
#         what it actually is)
#
# NOTHING here is invented. Values were matched against the JLC record's own
# "describe" string, and every package was compared to the land on this board.
SRC = {
    "U1":   ("C5118826",  "extended",       0, "Raytac MDBT50Q-1MV2, SMD-61P"),
    "U2":   ("C882746",   "extended",     829, "TI BQ25505RGRR, VQFN-20-EP 3.5x3.5"),
    "U3":   ("C46459900", "extended",    4371, "TI TPS7A2033DQNR, X2SON-4 1x1"),
    "U4":   ("C46459900", "extended",    4371, "TI TPS7A2033DQNR, X2SON-4 1x1"),
    "L1":   ("C2849435",  "extended",    2288, "DMBJ PNLS252012-220M 22uH, 1008, 1.02R, 500mA"),

    # C1/C2 WERE C2858031 (Murata GRM155R61E475ME15D, 4.7uF 25V X5R 0402).
    # Changed 2026-08-28 because 4.7 uF NOMINAL does not deliver 4.7 uF EFFECTIVE.
    # Murata's own characteristics data for the 16 V sibling GRM155R61C475ME15
    # (same 4.7uF, same 0402, same X5R), section 5 DC Voltage Characteristics:
    #     0 V ~4.7 uF | 5 V ~2.0 uF (-57%) | 10 V ~1.0 uF | 15 V ~0.5 uF
    # At this board's ~3.9 V bias that is roughly 2.3-2.8 uF against the
    # BQ25505's 4.7 uF requirement. Our 25 V part biases somewhat better than
    # that 16 V curve, but not by the ~2x needed to close the gap.
    #
    # 0603 IS NOT AVAILABLE AS A FIX: growing either from the 0402 land
    # (1.34 x 0.54) to 0603 (2.20 x 1.00) collides with 12 neighbouring
    # pads/tracks at C1 and 62 at C2. The land is fixed, so the only lever is
    # more nominal capacitance in the SAME 0402 -- which makes this a BOM
    # change with ZERO board impact.
    #
    # Chose C77000 over the C6119763 that SOURCING.md originally suggested:
    # C6119763 is HRE CGA0402X5R106M100GT, an unknown brand that publishes no
    # DC-bias curve -- and "Murata because Murata publishes the curve" was the
    # entire reason C1/C2 was a Murata part. C77000 keeps that, keeps the 10 V
    # rating (biases better than the 6.3 V 0J parts), and has 543,698 in JLC's
    # assembly library against HRE's 157,884.
    # Rail is 3.912 V max, so 10 V is 2.5x derating.
    "C1":   ("C77000",    "extended",  543698, "Murata GRM155R61A106ME44D 10uF 10V X5R 0402"),
    "C2":   ("C77000",    "extended",  543698, "Murata GRM155R61A106ME44D 10uF 10V X5R 0402"),
    # ---- the cell-protection block (PCM), added 2026-08-29 ----
    # U5 is CONSIGNED from Digi-Key (2508-MC3651DF1AAMCT-ND, cut tape, in stock
    # at qty 1), because JLC's own stock for C6989585 is 0 with a minimum of 5.
    "U5":   ("C6989585",  "extended",       0, "Mitsumi MC3651DF1AAM 1S protection, PLP-4E -- CONSIGNED from Digi-Key"),
    # R8/R9/C14 are 0201, not 0402. The board is at capacity: 26 slots for 25
    # parts and U5's courtyard costs 4. These three carry the PCM's 3 uA
    # quiescent and fault-sense current -- no heat, no voltage stress -- so
    # they are the safest parts on the board to shrink. 0201 needs Standard
    # PCBA (Economic stops at 0402), which this order already is, panelised to
    # 71.3 mm with rails and fiducials. See PCM-ONBOARD.md.
    "R8":   ("C274872",   "extended",  993538, "YAGEO RC0201FR-07330RL 330R 1% 0201"),
    "R9":   ("C273271",   "extended",   12827, "YAGEO RC0201FR-072K7L 2.7k 1% 0201"),
    # 25 V, NOT the cheaper 10 V part. DC bias already forced C1/C2 from 4.7uF
    # to 10uF once; at 4.3 V a 10 V X5R gives most of its capacitance away.
    "C14":  ("C76939",    "extended", 2377451, "Murata GRM033R61E104KE14D 100nF 25V X5R 0201"),
    "C3":   ("C1525",     "BASIC",   35834447, "Samsung CL05B104KO5NNNC 100nF 16V X7R 0402"),
    "C10":  ("C1525",     "BASIC",   35834447, "Samsung CL05B104KO5NNNC 100nF 16V X7R 0402"),
    "C4":   ("C22400107", "extended",   72632, "Murata GRM1555C1H103JE01D 10nF 50V C0G 0402"),
    # C5 was C18164635 (CCTC TCC0603X5R106K160CT). Identical spec, 1.1 M in
    # stock, and JLCPCB's part search finds it instantly by code -- but its BOM
    # matcher refused to auto-select it on EVERY upload, through a clean
    # 4-column file and a fully-specified comment alike. The only categorical
    # difference against parts that always match is `idleFlag`: null on the
    # CCTC part, true on this one and on C7's. Swapped rather than accept a
    # manual click on every future upload; same 10uF 16V X5R +-10% 0603.
    # C5 was an 0603 (C70225, 16 V). Moved to the SAME 0402 part as C1/C2 because
    # as an 0603 there was nowhere on the board its GND pad could sit outside a
    # pogo no-via ring -- one legal position existed and it was inside the
    # antenna keep-out. 10 V is ample against a 4.30 V cell, and with BT1 itself
    # on VBAT the cell dominates the bulk impedance; C5 is there for switching
    # transients, not for storage. Bonus: one fewer distinct LCSC code.
    "C5":   ("C77000",    "extended",  543698, "Murata GRM155R61A106ME44D 10uF 10V X5R 0402"),
    "C6":   ("C52923",    "BASIC",   11865003, "Samsung CL05A105KA5NQNC 1uF 25V X5R 0402"),
    "C8":   ("C52923",    "BASIC",   11865003, "Samsung CL05A105KA5NQNC 1uF 25V X5R 0402"),
    "C9":   ("C52923",    "BASIC",   11865003, "Samsung CL05A105KA5NQNC 1uF 25V X5R 0402"),
    "C7":   ("C20416425", "extended", 1168621, "CCTC TCC0603X5R226M100CT 22uF 10V X5R 0603"),
    "C12":  ("C15195",    "BASIC",    8405016, "Samsung CL05B103KB5NNNC 10nF 50V X7R 0402"),
    "C13":  ("C15195",    "BASIC",    8405016, "Samsung CL05B103KB5NNNC 10nF 50V X7R 0402"),

    "R1":   ("C11702",    "BASIC",   13920787, "UNI-ROYAL 0402WGF1001TCE 1k 1% 0402"),
    "R2":   ("C11702",    "BASIC",   13920787, "UNI-ROYAL 0402WGF1001TCE 1k 1% 0402"),
    "R3":   ("C11702",    "BASIC",   13920787, "UNI-ROYAL 0402WGF1001TCE 1k 1% 0402"),
    "R7":   ("C11702",    "BASIC",   13920787, "UNI-ROYAL 0402WGF1001TCE 1k 1% 0402"),
    "R4":   ("C3013173",  "extended",  263891, "FOJAN FRC0402F4704TS 4.7M 1% 0402"),
    "R5":   ("C26083",    "BASIC",    3470670, "UNI-ROYAL 0402WGF1004TCE 1M 1% 0402"),
    "R6":   ("C25741",    "BASIC",   14849306, "UNI-ROYAL 0402WGF1003TCE 100k 1% 0402"),
    "ROK1": ("C137964",   "extended",    9229, "YAGEO RC0402FR-074M53L 4.53M 1% 0402"),
    "ROK2": ("C477783",   "extended",    4637, "YAGEO RC0402FR-077M15L 7.15M 1% 0402"),
    "ROK3": ("C5713265",  "extended",  103945, "FOJAN FRC0402F1334TS 1.33M 1% 0402"),
    "ROV1": ("C172106",   "extended",    2040, "Walsin WR04W6044FTL 6.04M 1% 0402"),
    "ROV2": ("C137942",   "extended",    2674, "YAGEO RC0402FR-076M98L 6.98M 1% 0402"),
}
LCSC = {r: v[0] for r, v in SRC.items()}

# Per-line warnings that survive into the BOM so they cannot be forgotten.
WARN = {
    "U1": "CONSIGNED - customer ships MDBT50Q to JLC's warehouse, so JLC's own "
           "stock of 0 does not block the order. Confirm receipt before build.",
    "C1": "10uF NOMINAL, ~4-5 uF effective at 3.9 V bias. Was 4.7uF, which "
           "measured only ~2.3-2.8 uF. Specify by C_eff, never by marked value.",
    "C2": "10uF NOMINAL, ~4-5 uF effective at 3.9 V bias. Was 4.7uF, which "
           "measured only ~2.3-2.8 uF. Specify by C_eff, never by marked value.",
    "C7": "10 V rating is REQUIRED, not a preference. Do not substitute 6.3 V.",
    "C4": "C0G on purpose - CREF leakage sets the BQ25505's reference droop.",
    "ROV1": "Sets VBAT_OV. Only 2040 in stock, single source. Do not substitute blind.",
    "ROV2": "Sets VBAT_OV. Only 2674 in stock, single source. Do not substitute blind.",
    "ROK2": "Only 4637 in stock, single source.",
    "ROK1": "Only 9229 in stock, single source.",
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
                         X=round(x + HALF, 4),        # -> board lower-left
                         Y=round(HALF - y, 4),        # KiCad Y-down -> Y up
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

    # ---- BOM, grouped by PART NUMBER -------------------------------------
    # Grouping by the value STRING put U3 and U4 on two separate lines, because
    # the netlist describes them differently ("sensor rail" vs "switched
    # sensor-MCU rail") even though they are the same TPS7A2033DQNR. JLCPCB's
    # matcher then saw one part on two lines, assigned the quantity to one and
    # ZERO to the other, and reported "1 part not selected".
    #
    # A BOM line is one PURCHASABLE ITEM, so the key has to be the part number.
    # Unsourced lines keep falling back to the value string, so they still
    # cannot silently merge with each other.
    groups = collections.OrderedDict()
    for r in rows:
        key = SRC[r["ref"]][0] if r["ref"] in SRC else "\0" + r["value"]
        groups.setdefault(key, []).append(r["ref"])
    # rebuild as {comment: refs}, comment taken from the first designator
    _named = collections.OrderedDict()
    _first = {}
    for key, refs in groups.items():
        val = next((x["value"] for x in rows if x["ref"] == refs[0]), "")
        _named[val] = refs
        _first[val] = refs[0]
    groups = _named
    # TWO FILES, and the difference matters.
    #
    # touchid-v3-BOM.csv is the one JLCPCB gets: EXACTLY the four columns their
    # template defines, nothing else. The previous version carried four extra
    # metadata columns (library, stock, part fitted, note) because they are
    # useful to a human -- and JLCPCB's matcher, which has to work out which
    # column holds the part number, dropped C5 to "No Part Selected" on every
    # single upload even though C18164635 was sitting right there with 1.1 M in
    # stock. Do not put anything in the upload file that the template does not
    # ask for; the annotated copy below keeps all of it for us.
    bom = os.path.join(OUT, "touchid-v3-BOM.csv")
    bom_note = os.path.join(OUT, "touchid-v3-BOM-annotated.csv")
    unsourced, zero_stock, extended = [], [], set()
    fh2 = open(bom_note, "w", newline="", encoding="utf-8")
    w2 = csv.writer(fh2)
    w2.writerow(["Comment", "Designator", "Footprint",
                 "JLCPCB Part # (LCSC Part #)",
                 "JLC library", "JLC stock", "Part fitted", "NOTE"])
    with open(bom, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Comment", "Designator", "Footprint",
                    "JLCPCB Part # (LCSC Part #)"])
        for v, refs in groups.items():
            pkg = ""
            m = re.search(r"\b(0402|0603|0805|X2SON-4|VQFN-20)\b", v)
            if m:
                pkg = m.group(1)
            # every designator on a line must resolve to the SAME LCSC code,
            # otherwise the line is not one purchasable item
            codes = {SRC[r][0] for r in refs if r in SRC}
            missing = [r for r in refs if r not in SRC]
            if missing or len(codes) != 1:
                unsourced.append((v, refs, missing))
                w.writerow([v, ",".join(refs), pkg, ""])
                w2.writerow([v, ",".join(refs), pkg, "", "", "", "",
                             "*** SOURCE THIS -- no LCSC number known ***"
                             + (("  (" + LAND_REF[pkg] + ")")
                                if pkg in LAND_REF else "")])
                continue
            lc, lib, stock, desc = SRC[refs[0]]
            if lib != "BASIC":
                extended.add(lc)
            need = len(refs)
            # dedupe: C1 and C2 share one warning, print it once
            note = "  ".join(dict.fromkeys(WARN[r] for r in refs if r in WARN))
            if stock < need:
                zero_stock.append((v, refs, stock, need))
                note = ("*** JLC ASSEMBLY STOCK %d, NEED %d PER BOARD *** "
                        % (stock, need)) + note
            w.writerow([v, ",".join(refs), pkg, lc])
            w2.writerow([v, ",".join(refs), pkg, lc, lib, stock, desc, note])

    fh2.close()
    print("wrote %s   (%d parts placed)" % (cpl, len(rows)))
    print("wrote %s   (%d BOM lines, 4 columns - THIS IS THE UPLOAD FILE)"
          % (bom, len(groups)))
    print("wrote %s   (same lines + library/stock/notes, for humans)" % bom_note)
    print()
    print("SOURCING")
    print("  lines fully sourced : %d / %d" % (len(groups) - len(unsourced),
                                               len(groups)))
    print("  distinct JLC extended part types : %d  (JLC charges a one-off"
          " setup fee per type)" % len(extended))
    if unsourced:
        print("  *** UNSOURCED ***")
        for v, refs, missing in unsourced:
            print("      %-34s %s   missing=%s" % (v, ",".join(refs), missing))
    if zero_stock:
        print("  *** INSUFFICIENT JLC ASSEMBLY STOCK ***")
        for v, refs, stock, need in zero_stock:
            print("      %-34s %s   stock=%d need=%d/board"
                  % (v, ",".join(refs), stock, need))
    if not unsourced and not zero_stock:
        print("  every line sourced and in stock.")
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
