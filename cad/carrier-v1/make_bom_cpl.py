"""
make_bom_cpl.py -- JLCPCB assembly files for carrier-v1.

CPL is derived from the board file, in the SAME corner-based space as the
gerbers (drill/place origin = aux_axis_origin = the board's bottom-left),
so placements and gerbers agree.  Y is flipped because KiCad is Y-down and
the CPL is Y-up, exactly like the gerbers.
"""
import re, csv, sys

BOARD = "carrier-v1.kicad_pcb"
BX0, BY1 = -16.0, 38.0          # aux_axis_origin

src = open(BOARD, encoding="utf-8").read()
def blocks(s, tag):
    i=0; out=[]
    while True:
        i=s.find("("+tag+" ", i)
        if i<0: break
        d=0; j=i
        while True:
            if s[j]=="(": d+=1
            elif s[j]==")":
                d-=1
                if d==0: break
            j+=1
        out.append(s[i:j+1]); i=j+1
    return out

# ref -> (LCSC part, description, value, side, rotation offset)
# CONFIRMED against JLCPCB's parts library 2026-09-18:
#   C9900176459  Seeed XIAO RP2040        Extended, SMT assembly
#   C17408       UNI-ROYAL 0805W8F1000T5E 100R 0805 1% -- BASIC part
# J1 and J2 are NOT placed: through-hole assembly costs more than it saves for
# two and five easy joints, and hand-soldering them is a few minutes on the
# bench.  Their holes arrive clean (JLC protect unused through-holes from
# solder ingress).
PARTS = {
 "U1": ("C9900176459", "Seeed Studio XIAO RP2040",  "XIAO RP2040"),
 "R1": ("C17408",      "RES 100R 0805 1% Basic",    "100R"),
 "R2": ("C17408",      "RES 100R 0805 1% Basic",    "100R"),
 "R3": ("C17408",      "RES 100R 0805 1% Basic",    "100R"),
}
SKIP = {"PP1","PP2","PP3","PP4","PP5","DW1","DW2","TP1","TP2",
        "MH1","MH2","MH3","MH4","J1","J2"}

rows = []
for fp in blocks(src, "footprint"):
    ref = re.search(r'\(footprint "carrier:([^"]+)"', fp).group(1)
    if ref in SKIP: continue
    at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', fp)
    x, y = float(at.group(1)), float(at.group(2))
    rot  = float(at.group(3)) if at.group(3) else 0.0
    rows.append((ref, round(x - BX0, 4), round(BY1 - y, 4), rot))
rows.sort()

with open("carrier-v1-CPL.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator","Mid X","Mid Y","Layer","Rotation"])
    for ref, x, y, rot in rows:
        w.writerow([ref, f"{x}mm", f"{y}mm", "Top", f"{rot}"])

groups = {}
for ref, *_ in rows:
    lcsc, desc, val = PARTS[ref]
    groups.setdefault((lcsc, desc, val), []).append(ref)
with open("carrier-v1-BOM.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Comment","Designator","Footprint","LCSC Part #"])
    for (lcsc, desc, val), refs in sorted(groups.items(), key=lambda k: k[1][0]):
        fpname = {"XIAO RP2040":"XIAO-RP2040_SMD","100R":"R0805"}[val]
        w.writerow([val, ",".join(sorted(refs)), fpname, lcsc])

print(f"CPL: {len(rows)} placements")
for ref, x, y, rot in rows:
    print(f"   {ref:<4} ({x:7.3f}, {y:7.3f}) mm  rot {rot:g}  Top")
print(f"\nBOM: {len(groups)} lines")
missing = [d for (l, d, v) in groups if not l]
for (l, d, v), refs in sorted(groups.items(), key=lambda k: k[1][0]):
    print(f"   {v:<14} {','.join(sorted(refs)):<12} {l or '** NO LCSC PART YET **'}")

# sanity: every placement inside the outline
W, H = 47.0, 58.0
for ref, x, y, rot in rows:
    if not (0 <= x <= W and 0 <= y <= H):
        print(f"FAIL: {ref} at ({x},{y}) outside the {W}x{H} outline"); sys.exit(1)
print("\nall placements inside the outline: OK")
print(f"unresolved LCSC part numbers: {len(missing)}")
