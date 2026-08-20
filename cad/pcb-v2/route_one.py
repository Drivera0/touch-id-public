# Grid router for a single connection. Builds an obstacle map from the real
# copper (honouring pad shape), inflates it by clearance + half trace width,
# then A*-searches for a path. Returns nothing rather than something illegal.
import re, math, heapq, sys
from shapely.geometry import box, Point, LineString
from shapely.ops import unary_union
from shapely import affinity
from shapely.prepared import prep

PCB="pcb-v2.kicad_pcb"; NET="+3V3"; W=0.15; CLR=0.13; GRID=0.05
SRC_PAD=("U1","22")   # the source pad must NOT be an obstacle
VIA_D, VIA_CLR = 0.6, 0.15
START=(145.3011, 97.4036)          # U1 pin 22
BX0,BY0,BX1,BY1 = 138.7011, 96.2036, 158.3011, 113.8036   # board outline
EDGE=0.25

t=open(PCB).read()
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

obst={'F':[], 'B':[]}; target={'F':[], 'B':[]}
src_geom=[None]
for fp in blocks('footprint "'):
    _ref=re.search(r'\(property "Reference" "([^"]*)"',fp); _ref=_ref.group(1) if _ref else '?'
    m=re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)',fp)
    fx,fy,fa=float(m.group(1)),float(m.group(2)),float(m.group(3) or 0)
    for pm in re.finditer(r'\(pad "([^"]*)" (\w+) (\w+)\s*\n\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)\s*\n\s*\(size ([\d.]+) ([\d.]+)\)(.*?)\n\t\t\)',fp,re.S):
        nm,pt,sh,px,py,pa,w,h,tail=pm.groups()
        dx,dy=rot(float(px),float(py),fa)
        rr=re.search(r'\(roundrect_rratio ([\d.]+)\)',tail); net=re.search(r'\(net "([^"]*)"\)',tail)
        g=shp(sh,fx+dx,fy+dy,float(w),float(h),float(rr.group(1)) if rr else None,float(pa or 0)+fa)
        L=[l for l in ('F','B') if (l+'.Cu') in tail] or (['F','B'] if pt=='thru_hole' else [])
        if (_ref,nm)==SRC_PAD:
            src_geom[0]=g
            continue                      # source pad: not an obstacle
        for l in L:
            (target if (net and net.group(1)==NET) else obst)[l].append(g)
for m in re.finditer(r'\(segment\s*\n\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\n\s*\(end ([-\d.]+) ([-\d.]+)\)\s*\n\s*\(width ([\d.]+)\)\s*\n\s*\(layer "([^"]+)"\)\s*\n\s*\(net "([^"]*)"\)',t):
    sx,sy,ex,ey,w,lay,net=m.groups()
    g=LineString([(float(sx),float(sy)),(float(ex),float(ey))]).buffer(float(w)/2,cap_style=2)
    l='F' if lay=='F.Cu' else 'B'
    (target if net==NET else obst)[l].append(g)
for b in blocks('via'):
    m=re.search(r'\(at ([-\d.]+) ([-\d.]+)\)\s*\n\s*\(size ([\d.]+)\)',b); net=re.search(r'\(net "([^"]*)"\)',b)
    if not m: continue
    g=Point(float(m.group(1)),float(m.group(2))).buffer(float(m.group(3))/2,32)
    for l in ('F','B'): (target if (net and net.group(1)==NET) else obst)[l].append(g)

infl={l: prep(unary_union(obst[l]).buffer(CLR+W/2)) if obst[l] else None for l in 'FB'}
via_infl={l: prep(unary_union(obst[l]).buffer(VIA_CLR+VIA_D/2)) if obst[l] else None for l in 'FB'}
tgt={l: prep(unary_union(target[l])) if target[l] else None for l in 'FB'}
inner=box(BX0+EDGE, BY0+EDGE, BX1-EDGE, BY1-EDGE)

def ok(l,x,y):
    p=Point(x,y)
    return inner.contains(p) and not (infl[l] and infl[l].contains(p))
def via_ok(x,y):
    p=Point(x,y)
    return inner.contains(p) and not any(via_infl[l] and via_infl[l].contains(p) for l in 'FB')
def hit(l,x,y):
    return tgt[l] is not None and tgt[l].intersects(Point(x,y).buffer(W/2))

sx,sy=START
def key(l,x,y): return (l, round(x/GRID), round(y/GRID))
start=('F', sx, sy)
seen={key(*start):0}; pq=[(0.0,0.0,start,None)]; par={}
STEPS=[(GRID,0),(-GRID,0),(0,GRID),(0,-GRID),(GRID,GRID),(GRID,-GRID),(-GRID,GRID),(-GRID,-GRID)]
goal=None; n=0
while pq:
    f,g,(l,x,y),pv=heapq.heappop(pq)
    k=key(l,x,y)
    if k in par: continue
    par[k]=(pv,(l,x,y))
    n+=1
    if n>400000: break
    if hit(l,x,y) and (abs(x-sx)+abs(y-sy))>0.5: goal=(l,x,y); break
    for dx,dy in STEPS:
        nx,ny=x+dx,y+dy
        if not ok(l,nx,ny): continue
        ng=g+math.hypot(dx,dy)
        kk=key(l,nx,ny)
        if kk in seen and seen[kk]<=ng: continue
        seen[kk]=ng; heapq.heappush(pq,(ng,ng,(l,nx,ny),k))
    ol='B' if l=='F' else 'F'
    if via_ok(x,y) and ok(ol,x,y):
        ng=g+3.0
        kk=key(ol,x,y)
        if not (kk in seen and seen[kk]<=ng):
            seen[kk]=ng; heapq.heappush(pq,(ng,ng,(ol,x,y),k))
print(f"explored {n} nodes")
if not goal:
    print("NO LEGAL PATH FOUND"); sys.exit(1)
path=[]; k=key(*goal)
while k is not None:
    pv,node=par[k]; path.append(node); k=pv
path.reverse()
print(f"path: {len(path)} nodes, from {path[0]} to {path[-1]}")
# collapse collinear runs into segments
segs=[]; i=0
while i<len(path)-1:
    l=path[i][0]; j=i
    while j+1<len(path) and path[j+1][0]==l:
        if j+2<len(path) and path[j+2][0]==l:
            ax,ay=path[j+1][1]-path[j][1], path[j+1][2]-path[j][2]
            bx,by=path[j+2][1]-path[j+1][1], path[j+2][2]-path[j+1][2]
            if abs(ax*by-ay*bx)>1e-9: break
        j+=1
    if j>i: segs.append((l,path[i][1],path[i][2],path[j][1],path[j][2]))
    if j+1<len(path) and path[j+1][0]!=l: segs.append(('VIA',path[j][1],path[j][2],None,None))
    i=j+1 if j>i else i+1
print(f"\n{len([s for s in segs if s[0]!='VIA'])} segments, {len([s for s in segs if s[0]=='VIA'])} vias")
for s in segs: print("  ",s)
import json; json.dump(segs, open("/tmp/route22.json","w"))
