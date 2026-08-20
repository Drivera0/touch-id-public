import re, math, sys
from shapely.geometry import box, Point, LineString
from shapely import affinity
PCB=sys.argv[1] if len(sys.argv)>1 else "pcb-v2.kicad_pcb"
t=open(PCB).read()
# --- 2026-08-20: the board now uses KiCad's real net schema ---
# Top level declares (net <n> "NAME"); pads carry (net <n> "NAME") but tracks
# and vias carry only (net <n>). Expand the bare ordinals back to names here so
# every regex below keeps working unchanged.
_NETNAMES = dict(__import__("re").findall(r'\(net (\d+) "([^"]*)"\)', t))
t = __import__("re").sub(r'\(net (\d+)\)',
                         lambda _m: '(net %s "%s")' % (_m.group(1), _NETNAMES.get(_m.group(1), "")),
                         t)

def blocks(tag):
    out,i=[],0
    while True:
        i=t.find('\t('+tag,i)
        if i<0: return out
        d,j=0,i
        while True:
            if t[j]=='(': d+=1
            elif t[j]==')':
                d-=1
                if d==0: break
            j+=1
        out.append(t[i:j+1]); i=j
def rot(px,py,a):
    r=math.radians(a);c,s=math.cos(r),math.sin(r);return px*c-py*s,px*s+py*c
def shp(sh,x,y,w,h,rr,ang):
    if sh=='circle': g=Point(x,y).buffer(w/2,32)
    elif sh=='roundrect':
        r=(rr or .25)*min(w,h); g=box(x-w/2+r,y-h/2+r,x+w/2-r,y+h/2-r).buffer(r,16)
    else: g=box(x-w/2,y-h/2,x+w/2,y+h/2)
    return affinity.rotate(g,ang,origin=(x,y)) if ang else g
items=[]
for fp in blocks('footprint "'):
    ref=re.search(r'\(property "Reference" "([^"]*)"',fp); ref=ref.group(1) if ref else '?'
    m=re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)',fp)
    fx,fy,fa=float(m.group(1)),float(m.group(2)),float(m.group(3) or 0)
    for pm in re.finditer(r'\(pad "([^"]*)" (\w+) (\w+)\s*\n\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)\s*\n\s*\(size ([\d.]+) ([\d.]+)\)(.*?)\n\t\t\)',fp,re.S):
        nm,pt,sh,px,py,pa,w,h,tail=pm.groups()
        net=re.search(r'\(net (?:\d+ )?"([^"]*)"\)',tail)
        if not net: continue
        dx,dy=rot(float(px),float(py),fa)
        rr=re.search(r'\(roundrect_rratio ([\d.]+)\)',tail)
        L={l for l in 'FB' if (l+'.Cu') in tail} or ({'F','B'} if pt=='thru_hole' else set())
        items.append((net.group(1), shp(sh,fx+dx,fy+dy,float(w),float(h),
                      float(rr.group(1)) if rr else None,float(pa or 0)+fa), L, f"pad {ref}:{nm}"))
for m in re.finditer(r'\(segment\s*\n\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\n\s*\(end ([-\d.]+) ([-\d.]+)\)\s*\n\s*\(width ([\d.]+)\)\s*\n\s*\(layer "([^"]+)"\)\s*\n\s*\(net (?:\d+ )?"([^"]*)"\)',t):
    sx,sy,ex,ey,w,lay,net=m.groups()
    items.append((net, LineString([(float(sx),float(sy)),(float(ex),float(ey))]).buffer(float(w)/2,cap_style=2),
                  {'F' if lay=='F.Cu' else 'B'}, "track"))
for b in blocks('via'):
    m=re.search(r'\(at ([-\d.]+) ([-\d.]+)\)\s*\n\s*\(size ([\d.]+)\)',b); net=re.search(r'\(net (?:\d+ )?"([^"]*)"\)',b)
    if m and net:
        items.append((net.group(1), Point(float(m.group(1)),float(m.group(2))).buffer(float(m.group(3))/2,32),{'F','B'},"via"))
bad=0
nets={}
for i,(n,g,L,lab) in enumerate(items): nets.setdefault(n,[]).append(i)
for n,idx in sorted(nets.items()):
    par=list(range(len(idx)))
    def f(a):
        while par[a]!=a: par[a]=par[par[a]]; a=par[a]
        return a
    for a in range(len(idx)):
        for b in range(a+1,len(idx)):
            ia,ib=idx[a],idx[b]
            if not (items[ia][2] & items[ib][2]): continue
            if items[ia][1].intersects(items[ib][1]):
                ra,rb=f(a),f(b)
                if ra!=rb: par[ra]=rb
    comp=len(set(f(i) for i in range(len(idx))))
    pads=[items[i][3] for i in idx if items[i][3].startswith('pad')]
    if comp!=1: bad+=1
    print(f"  {n:10s} {len(idx):3d} objects, {len(pads):2d} pads -> {comp} island(s)"
          + ("" if comp==1 else "   <-- BROKEN"))
print(f"\n{'ALL NETS CONNECTED' if bad==0 else str(bad)+' NET(S) SPLIT'}")
sys.exit(1 if bad else 0)
