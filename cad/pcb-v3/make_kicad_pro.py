"""
make_kicad_pro.py -- write a .kicad_pro whose rules MATCH the fab floor.

WHY THIS EXISTS
---------------
A .kicad_pro is not decoration. KiCad's own DRC grades against the netclass in
it, preflight auto-detects its clearance from it, and the router reads it. A
stale one means every one of those grades the board against rules it was not
built to.

They went stale. On 2026-08-30 the live pcb-v6-handoff.kicad_pro still said

    track 0.2    via 0.6/0.3        <- KiCad's defaults, carried over

against a board actually built at

    track 0.127  via 0.40/0.20      <- fab_floor_touchid.txt

Only one .kicad_pro in the whole folder had ever been correct, and it belonged
to a superseded board. The project had already hit this once -- an old commit
message reads "Ship a matching .kicad_pro so rules are not stale" -- and it
came back, because shipping one by hand is a step someone has to remember.

So it is derived now, from the single file that already defines the fab rung.
Nothing here is typed twice.

Usage:  python make_kicad_pro.py OUT.kicad_pro [TEMPLATE.kicad_pro]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FLOOR = os.path.join(HERE, "fab_floor_touchid.txt")


def floor():
    """The fab rung, read from the one file that owns it."""
    v = {}
    for line in open(FLOOR, encoding="utf-8"):
        line = line.split("#")[0]
        if "=" in line:
            k, val = [s.strip() for s in line.split("=", 1)]
            try:
                v[k] = float(val)
            except ValueError:
                pass
    missing = {"track_width", "clearance", "via_diameter", "via_drill"} - set(v)
    if missing:
        sys.exit("fab floor is missing %s -- refusing to guess" % sorted(missing))
    return v


def main():
    out = sys.argv[1]
    tmpl = sys.argv[2] if len(sys.argv) > 2 else None
    f = floor()

    if tmpl and os.path.exists(tmpl):
        d = json.load(open(tmpl, encoding="utf-8"))
    else:
        d = {"board": {"design_settings": {}}, "net_settings": {}}

    ns = d.setdefault("net_settings", {})
    classes = ns.setdefault("classes", [])
    if not classes:
        classes.append({"name": "Default"})
    for c in classes:
        c["clearance"] = f["clearance"]
        c["track_width"] = f["track_width"]
        c["via_diameter"] = f["via_diameter"]
        c["via_drill"] = f["via_drill"]

    # The design-settings rules KiCad enforces at DRC time. Leaving these at
    # the defaults lets KiCad pass copper it should flag, which is the same
    # class of hole the netclass drift opened.
    ds = d.setdefault("board", {}).setdefault("design_settings", {})
    rules = ds.setdefault("rules", {})
    rules["min_clearance"] = f["clearance"]
    rules["min_track_width"] = f["track_width"]
    rules["min_through_hole_diameter"] = f["via_drill"]
    rules["min_via_diameter"] = f["via_diameter"]
    if "hole_to_hole" in f:
        rules["min_hole_to_hole"] = f["hole_to_hole"]
    if "board_edge" in f:
        rules["copper_edge_clearance"] = f["board_edge"]

    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(d, fh, indent=2)
        fh.write("\n")

    print("wrote %s" % out)
    print("  clearance %.4g  track %.4g  via %.4g/%.4g"
          % (f["clearance"], f["track_width"], f["via_diameter"], f["via_drill"]))
    for k in ("hole_to_hole", "board_edge"):
        if k in f:
            print("  %-13s %.4g" % (k, f[k]))
    print("all taken from fab_floor_touchid.txt -- nothing typed twice")


if __name__ == "__main__":
    main()
