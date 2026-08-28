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

def pads(board_text):
    """-> list of dicts with global geometry."""
    root = parse(board_text)
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
            net = kid(pd, 'net')
            gx, gy = rot(px, py, fa)
            out.append(dict(ref=ref, pad=s(pd[1]), shape=s(pd[3]),
                            x=fx + gx, y=fy + gy,
                            w=f(sz[1]), h=f(sz[2]),
                            rot=(fa + (f(kid(pd,'at')[3]) if len(pat) > 3 else 0)) % 360,
                            layers=lay, net=s(net[2]) if net and len(net) > 2 else ''))
    return out
