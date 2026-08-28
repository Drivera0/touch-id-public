"""
nudge.py — move a via (and everything joined to it) by a few hundredths.

The router is allowed to place copper exactly ON the clearance rule, and it
does: the OK_PROG via east of U2 landed at precisely 0.1000 mm from an OK_HYST
track. That is legal and it is also the worst place to be -- any etch variation
at all makes it a violation, and a float comparison of `d < rule` flips on
rounding alone.

This moves the via and every track endpoint sitting on it, so the connection is
preserved. It is separate from the router on purpose: re-routing to fix one via
churns the whole board, and a 0.05 mm nudge does not.

Usage:  python nudge.py BOARD X Y NEWX NEWY
"""
import sys
import sexp

TOL = 1e-6


def main():
    board, x, y, nx, ny = (sys.argv[1], float(sys.argv[2]), float(sys.argv[3]),
                           float(sys.argv[4]), float(sys.argv[5]))
    text = open(board, encoding="utf-8", errors="replace").read()
    root = sexp.parse(text)
    k, kd, s, f = sexp.kids, sexp.kid, sexp.s, sexp.f

    hit = [v for v in k(root, "via")
           if abs(f(kd(v, "at")[1]) - x) < 1e-4 and abs(f(kd(v, "at")[2]) - y) < 1e-4]
    if not hit:
        print(f"no via at ({x}, {y})")
        return 1

    moved_ends = 0
    for sg in k(root, "segment"):
        for tag in ("start", "end"):
            p = kd(sg, tag)
            if abs(f(p[1]) - x) < 1e-4 and abs(f(p[2]) - y) < 1e-4:
                moved_ends += 1

    # Match the NUMBERS, not a formatting guess. KiCad writes these with six
    # decimals ("8.950000 -4.550000"); a f"{x:g}" template silently matched
    # nothing and reported success while changing the file not at all.
    import re

    def sub(m):
        tag, a, b = m.group(1), float(m.group(2)), float(m.group(3))
        if abs(a - x) < 1e-4 and abs(b - y) < 1e-4:
            sub.n += 1
            return f"({tag} {nx:.6f} {ny:.6f})"
        return m.group(0)
    sub.n = 0
    text = re.sub(r"\((at|start|end) (-?[\d.]+) (-?[\d.]+)\)", sub, text)
    n = sub.n
    if n == 0:
        print("NOTHING MATCHED — file unchanged")
        return 1
    open(board, "w", encoding="utf-8").write(text)
    print(f"via ({x}, {y}) -> ({nx}, {ny}): {n} coordinate(s) rewritten "
          f"(1 via + {moved_ends} track end(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
