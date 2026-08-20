# Structural syntax gate for a .kicad_pcb file.
#
# WHY THIS EXISTS (2026-08-20)
# check_board.py and check_connect.py both read the board with REGEX. Regex
# matches the blocks it is looking for and silently ignores everything else,
# so when a block deletion left 9 orphan ")" lines behind, both checkers kept
# reporting a clean, fully-connected board -- while the file was malformed and
# KiCad would have refused to open it. The clearance and connectivity numbers
# were all correct. The file was still broken.
#
# So: parse the file properly BEFORE trusting any regex-based result. Run this
# first, every time, especially after any script edits the board.
#
# Run: python sexp_check.py [board.kicad_pcb]     (exit 0 = parses cleanly)

import sys
from collections import Counter

PCB = sys.argv[1] if len(sys.argv) > 1 else "pcb-v2.kicad_pcb"


def parse(s):
    """Full S-expression parse. Raises SyntaxError with a line number."""
    i, n = 0, len(s)

    def line_of(off):
        return s.count("\n", 0, off) + 1

    def node():
        nonlocal i
        while i < n and s[i] in " \t\r\n":
            i += 1
        if i >= n:
            raise SyntaxError("unexpected end of file")
        if s[i] == "(":
            i += 1
            out = []
            while True:
                while i < n and s[i] in " \t\r\n":
                    i += 1
                if i >= n:
                    raise SyntaxError("unterminated list at end of file")
                if s[i] == ")":
                    i += 1
                    return out
                out.append(node())
        if s[i] == ")":
            raise SyntaxError(f"stray ')' on line {line_of(i)}")
        if s[i] == '"':
            i += 1
            b = []
            while s[i] != '"':
                if s[i] == "\\":
                    i += 1
                b.append(s[i])
                i += 1
            i += 1
            return "".join(b)
        b = []
        while i < n and s[i] not in " \t\r\n()":
            b.append(s[i])
            i += 1
        return "".join(b)

    root = node()
    while i < n and s[i] in " \t\r\n":
        i += 1
    if i < n:
        raise SyntaxError(f"trailing content after the top-level form, "
                          f"line {line_of(i)}")
    return root


def main():
    raw = open(PCB, "rb").read()
    text = raw.decode()

    print(f"{PCB}")
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    print(f"  line endings : {crlf} CRLF, {lf} bare LF"
          + ("" if lf == 0 else "   <-- mixed, git will show a whole-file diff"))

    try:
        root = parse(text)
    except SyntaxError as e:
        print(f"\n  PARSE FAILED: {e}")
        print("  The file is malformed. KiCad will refuse to open it, and any"
              " regex-based\n  check you run on it is meaningless.")
        return 1

    if root[0] != "kicad_pcb":
        print(f"\n  PARSE FAILED: top-level form is '{root[0]}', not 'kicad_pcb'")
        return 1

    c = Counter(x[0] for x in root if isinstance(x, list))
    pads = sum(1 for f in root if isinstance(f, list) and f[0] == "footprint"
               for p in f if isinstance(p, list) and p[0] == "pad")
    print(f"  PARSE OK     : {len(root)} top-level children")
    print(f"  footprints {c['footprint']}   pads {pads}   "
          f"segments {c['segment']}   vias {c['via']}   zones {c['zone']}")

    # A pad outside a footprint is not legal and means a block boundary was
    # mangled -- the same failure mode as the orphan parens.
    loose = sum(1 for x in root if isinstance(x, list) and x[0] == "pad")
    if loose:
        print(f"\n  FAIL: {loose} pad(s) sitting at the top level, outside any"
              " footprint")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
