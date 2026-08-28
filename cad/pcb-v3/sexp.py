"""Minimal s-expression parser + pad extraction for .kicad_pcb.
Regex parsing of this format has produced real bugs (a pad-net regex once ran
past NC pads and stole the next pad's net). Parse it properly."""
import math

def parse(text):
    i, n = 0, len(text)
    def node():
        nonlocal i
        assert text[i] == '('; i += 1
        out = []
        while i < n:
            c = text[i]
            if c == '(':
                out.append(node())
            elif c == ')':
                i += 1; return out
            elif c == '"':
                i += 1; s = []
                while text[i] != '"':
                    if text[i] == '\\': i += 1
                    s.append(text[i]); i += 1
                i += 1; out.append('"' + ''.join(s))
            elif c.isspace():
                i += 1
            else:
                j = i
                while i < n and not text[i].isspace() and text[i] not in '()"': i += 1
                out.append(text[j:i])
        return out
    while text[i] != '(': i += 1
    return node()

def kids(nd, tag):
    return [c for c in nd if isinstance(c, list) and c and c[0] == tag]
def kid(nd, tag):
    k = kids(nd, tag); return k[0] if k else None
def s(v):  # strip string marker
    return v[1:] if isinstance(v, str) and v.startswith('"') else v
def f(v):  return float(s(v))

def rot(px, py, adeg):
    """KiCad .kicad_pcb is Y-DOWN: a POSITIVE angle is CLOCKWISE."""
    r = math.radians(adeg); c, sn = math.cos(r), math.sin(r)
    return px * c + py * sn, -px * sn + py * c

def net_of(node):
    """Net NAME from a (net ...) child, in EITHER KiCad file format.

    KiCad <=9 :  a top-level table of (net N "NAME"), and items say (net N).
    KiCad 10  :  NO table at all; every item carries (net "NAME") directly.

    Round-tripping the board through KiCad 10 silently turned every net name
    into "" here, because the old code read index [2] and v10 puts the name at
    index [1]. 134 pads, 0 nets -- and a checker that sees no nets passes
    everything. Handle both, and never assume the format.
    """
    n = kid(node, "net")
    if n is None or len(n) < 2:
        return ""
    if len(n) > 2:                       # (net N "NAME")
        return s(n[2])
    v = s(n[1])                          # (net "NAME") or (net N)
    return "" if str(v).lstrip("-").isdigit() else v


def net_table(board_text):
    """id -> name, empty on KiCad 10 (which has no table)."""
    root = parse(board_text)
    out = {}
    for n in kids(root, "net"):
        if len(n) > 2:
            out[s(n[1])] = s(n[2])
    return out


def pads(board_text):
    """-> list of dicts with global geometry."""
    root = parse(board_text)
    _tbl = {}
    for _n in kids(root, "net"):
        if len(_n) > 2:
            _tbl[s(_n[1])] = s(_n[2])
    out = []
    for fp in kids(root, 'footprint'):
        at = kid(fp, 'at'); fx, fy = f(at[1]), f(at[2])
        fa = f(at[3]) if len(at) > 3 else 0.0
        ref = '?'
        for p in kids(fp, 'property'):
            if s(p[1]) == 'Reference': ref = s(p[2])
        for pd in kids(fp, 'pad'):
            pat = kid(pd, 'at'); px, py = f(pat[1]), f(pat[2])
            sz = kid(pd, 'size')
            lay = [s(x) for x in kid(pd, 'layers')[1:]]
            net = kid(pd, "net")
            if net is not None and len(net) == 2 and str(s(net[1])).lstrip("-").isdigit():
                _nm = _tbl.get(s(net[1]), "")     # KiCad <=9: (net N) -> table
            elif net is not None and len(net) > 2:
                _nm = s(net[2])                   # KiCad <=9: (net N "NAME")
            elif net is not None:
                _nm = s(net[1])                   # KiCad 10:  (net "NAME")
            else:
                _nm = ""
            gx, gy = rot(px, py, fa)
            out.append(dict(ref=ref, pad=s(pd[1]), shape=s(pd[3]),
                            x=fx + gx, y=fy + gy,
                            w=f(sz[1]), h=f(sz[2]),
                            rot=(fa + (f(kid(pd,'at')[3]) if len(pat) > 3 else 0)) % 360,
                            layers=lay, net=_nm))
    return out
