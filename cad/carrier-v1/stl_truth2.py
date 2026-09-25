"""
stl_truth2.py -- as stl_truth.py, but with a TILTED ray.

The first version cast straight up (0,0,1).  This part is entirely axis-aligned,
so that ray grazes shared triangle edges and the parity count is unreliable --
it reported a 57.5 mm wide 'opening', which is nonsense.  A slightly tilted
direction removes the degeneracy.  Sanity probes at the bottom prove the test
works before any conclusion is drawn from it.
"""
import numpy as np, struct

def load(path):
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b, dtype=np.uint8, count=n*50, offset=84).reshape(n, 50)
    return a[:, 12:48].copy().view("<f4").reshape(n, 3, 3).astype(np.float64)

T = load("flash_frame.stl")
A, B, C = T[:,0,:], T[:,1,:], T[:,2,:]
E1, E2 = B-A, C-A
V = T.reshape(-1,3); lo, hi = V.min(0), V.max(0)

D = np.array([0.0137, 0.0071, 1.0]); D /= np.linalg.norm(D)
P = np.cross(D, E2)
det = np.einsum('ij,ij->i', E1, P)
ok = np.abs(det) > 1e-12
inv = np.zeros_like(det); inv[ok] = 1.0/det[ok]

def inside(pts):
    pts = np.atleast_2d(np.asarray(pts, float))
    out = np.zeros(len(pts), bool)
    for k, p in enumerate(pts):
        Tv = p - A
        u = np.einsum('ij,ij->i', Tv, P) * inv
        Q = np.cross(Tv, E1)
        v = (Q @ D) * inv
        t = np.einsum('ij,ij->i', E2, Q) * inv
        hit = ok & (u >= 0) & (u <= 1) & (v >= 0) & (u+v <= 1) & (t > 1e-9)
        out[k] = (hit.sum() % 2) == 1
    return out

print("SANITY PROBES (these must all pass or nothing below is trustworthy)")
checks = [((0, 0, -1.0),      False, "below the part"),
          ((0, 0, 40.0),      False, "above the part"),
          ((27.0, 0, 10.0),   True,  "inside the +X outer wall"),
          ((0, 30.0, 10.0),   True,  "inside the +Y outer wall"),
          ((0, 0, 5.0),       False, "inside the open cavity"),
          ((15.0, 15.0, 18.5),True,  "deck, away from the opening"),
          ((0, 0, 21.0),      False, "inside the carrier recess")]
allok = True
for pt, want, why in checks:
    got = bool(inside([pt])[0])
    flag = "ok " if got == want else "FAIL"
    allok &= (got == want)
    print(f"  {flag}  {str(pt):<22} expected {'SOLID ' if want else 'HOLLOW'}  got {'SOLID ' if got else 'HOLLOW'}   {why}")
if not allok:
    raise SystemExit("\nsanity probes failed -- stopping")
print("  all sanity probes pass\n")

Z = 18.5
xs = np.arange(-28.77, 28.77, 0.20)
ys = np.arange(-34.27, 34.27, 0.20)
row = inside(np.column_stack([xs, np.full_like(xs,-6.93), np.full_like(xs,Z)]))
col = inside(np.column_stack([np.full_like(ys,-7.47), ys, np.full_like(ys,Z)]))
gx, gy = xs[~row], ys[~col]
print(f"OPENING measured in the STL at z={Z}")
print(f"  X  {gx.min():+7.2f} .. {gx.max():+7.2f}    width  {gx.max()-gx.min():.2f} mm   (design 24.00)")
print(f"  Y  {gy.min():+7.2f} .. {gy.max():+7.2f}    height {gy.max()-gy.min():.2f} mm   (design 22.00)")
ocx, ocy = (gx.min()+gx.max())/2, (gy.min()+gy.max())/2
print(f"  centre ({ocx:+.2f}, {ocy:+.2f})            (design -7.50, -7.00)")
print(f"  wall gaps   -X {gx.min()-lo[0]:5.2f}  +X {hi[0]-gx.max():5.2f}"
      f"   -Y {gy.min()-lo[1]:5.2f}  +Y {hi[1]-gy.max():5.2f}")
print( "  design      -X  9.50  +X 24.50   -Y 16.50  +Y 30.50\n")

print("ORIENTATION MARK -- scanning 0.5 mm inside each outer face, z=10")
for name, pts, axis in [
    ("+Y face", [(x, hi[1]-0.5, 10.0) for x in np.arange(-20, 20.1, 0.5)], 0),
    ("-Y face", [(x, lo[1]+0.5, 10.0) for x in np.arange(-20, 20.1, 0.5)], 0),
    ("+X face", [(hi[0]-0.5, y, 10.0) for y in np.arange(-20, 20.1, 0.5)], 1),
    ("-X face", [(lo[0]+0.5, y, 10.0) for y in np.arange(-20, 20.1, 0.5)], 1)]:
    ins = inside(pts)
    holes = np.array(pts)[~ins]
    if len(holes):
        c = holes[:, axis]
        print(f"  {name}: POCKET FOUND, spans {c.min():+.1f} .. {c.max():+.1f} "
              f"({c.max()-c.min():.1f} mm wide)  <-- the mark")
    else:
        print(f"  {name}: solid all along")

# ---- the X scan above reported min/max of ALL hollow samples, which lumps the
#      two FINGER NOTCHES in the outer walls together with the opening.  Print
#      the contiguous runs instead.
def runs(coord, hollow):
    out, start = [], None
    for c, h in zip(coord, hollow):
        if h and start is None: start = c
        if not h and start is not None: out.append((start, prev)); start = None
        prev = c
    if start is not None: out.append((start, coord[-1]))
    return out

print("\nHOLLOW (through) RUNS along X at y=-6.93, z=18.5:")
for a, b in runs(xs, ~row):
    print(f"   {a:+7.2f} .. {b:+7.2f}   ({b-a:5.2f} mm)")
print("\nHOLLOW (through) RUNS along Y at x=-7.47, z=18.5:")
for a, b in runs(ys, ~col):
    print(f"   {a:+7.2f} .. {b:+7.2f}   ({b-a:5.2f} mm)")
