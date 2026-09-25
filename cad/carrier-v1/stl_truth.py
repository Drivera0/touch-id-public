"""
stl_truth.py -- interrogate flash_frame.stl DIRECTLY.  No cadquery, no trimesh,
no trusting gen_frame.py.  Binary STL parsed with numpy; inside/outside by
ray-parity along +Z.  The question this answers: relative to the ORIENTATION
MARK, is the opening on the correct side, or is the part mirrored?
"""
import numpy as np, struct, sys

def load(path):
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b, dtype=np.uint8, count=n*50, offset=84).reshape(n, 50)
    f = a[:, 12:48].copy().view("<f4").reshape(n, 3, 3).astype(np.float64)
    return f

T = load("flash_frame.stl")
V = T.reshape(-1, 3)
lo, hi = V.min(0), V.max(0)
print(f"triangles {len(T)}")
print(f"bbox  X {lo[0]:+8.3f} .. {hi[0]:+8.3f}   ({hi[0]-lo[0]:.3f} mm)")
print(f"      Y {lo[1]:+8.3f} .. {hi[1]:+8.3f}   ({hi[1]-lo[1]:.3f} mm)")
print(f"      Z {lo[2]:+8.3f} .. {hi[2]:+8.3f}   ({hi[2]-lo[2]:.3f} mm)")

A, B, C = T[:,0,:], T[:,1,:], T[:,2,:]
E1, E2 = B-A, C-A
def inside(pts):
    """ray parity along +Z (Moller-Trumbore with direction (0,0,1))"""
    pts = np.atleast_2d(np.asarray(pts, float))
    out = np.zeros(len(pts), bool)
    d = np.array([0.0, 0.0, 1.0])
    P = np.cross(d, E2)                     # (n,3)
    det = np.einsum('ij,ij->i', E1, P)
    ok = np.abs(det) > 1e-12
    inv = np.zeros_like(det); inv[ok] = 1.0/det[ok]
    for k, p in enumerate(pts):
        Tv = p - A
        u = np.einsum('ij,ij->i', Tv, P) * inv
        Q = np.cross(Tv, E1)
        v = (Q @ d) * inv
        t = np.einsum('ij,ij->i', E2, Q) * inv
        hit = ok & (u >= 0) & (u <= 1) & (v >= 0) & (u+v <= 1) & (t > 1e-9)
        out[k] = (hit.sum() % 2) == 1
    return out

CX, CY = (lo[0]+hi[0])/2, (lo[1]+hi[1])/2
print(f"\ngeometric centre of bbox: ({CX:+.3f}, {CY:+.3f})")

# ---- 1. where is the through-opening?  scan the deck at z = 18.5 ----
Z = 18.5
xs = np.arange(lo[0]+0.2, hi[0]-0.2, 0.25)
ys = np.arange(lo[1]+0.2, hi[1]-0.2, 0.25)

row = inside(np.column_stack([xs, np.full_like(xs, -7.0), np.full_like(xs, Z)]))
gapx = xs[~row]
col = inside(np.column_stack([np.full_like(ys, -7.5), ys, np.full_like(ys, Z)]))
gapy = ys[~col]
print(f"\nOPENING measured in the STL at z={Z}:")
print(f"  X  {gapx.min():+7.2f} .. {gapx.max():+7.2f}   width  {gapx.max()-gapx.min():.2f} mm")
print(f"  Y  {gapy.min():+7.2f} .. {gapy.max():+7.2f}   height {gapy.max()-gapy.min():.2f} mm")
ocx, ocy = (gapx.min()+gapx.max())/2, (gapy.min()+gapy.max())/2
print(f"  centre ({ocx:+.2f}, {ocy:+.2f})   -> offset from part centre ({ocx-CX:+.2f}, {ocy-CY:+.2f})")
print(f"  wall gaps:  -X {gapx.min()-lo[0]:.2f}   +X {hi[0]-gapx.max():.2f}"
      f"   -Y {gapy.min()-lo[1]:.2f}   +Y {hi[1]-gapy.max():.2f}")

# ---- 2. which outer face carries the engraved mark? ----
# the mark is a 1.2 mm deep pocket, x within +-10, z 5..16.
print("\nORIENTATION MARK -- probing 0.6 mm inside each outer face at z=10:")
for name, pt in [("+Y face", (0.0, hi[1]-0.6, 10.0)),
                 ("-Y face", (0.0, lo[1]+0.6, 10.0)),
                 ("+X face", (hi[0]-0.6, 0.0, 10.0)),
                 ("-X face", (lo[0]+0.6, 0.0, 10.0))]:
    ins = inside([pt])[0]
    print(f"  {name}  point {pt}  -> {'SOLID' if ins else 'HOLLOW  <-- pocket / mark here'}")

# ---- 3. verdict ----
print("\n--- VERDICT ---")
markY = None
if not inside([(0.0, hi[1]-0.6, 10.0)])[0]: markY = +1
if not inside([(0.0, lo[1]+0.6, 10.0)])[0]: markY = -1
if markY is None:
    print("could not find the mark -- inconclusive")
else:
    side = "+Y (max Y)" if markY > 0 else "-Y (min Y)"
    print(f"mark is on the {side} face")
    print(f"opening sits {'-Y' if ocy < CY else '+Y'} of centre "
          f"({abs(ocy-CY):.2f} mm) and {'-X' if ocx < CX else '+X'} of centre "
          f"({abs(ocx-CX):.2f} mm)")
    away = (markY > 0 and ocy < CY) or (markY < 0 and ocy > CY)
    print(f"opening is on the {'FAR side from' if away else 'SAME side as'} the mark")
    print("\nEXPECTED (design): mark on +Y, opening at (-7.50, -7.00) from centre")
    okx = abs((ocx-CX) - (-7.50)) < 0.35
    oky = abs((ocy-CY) - (-7.00)) < 0.35
    if markY > 0 and okx and oky:
        print("MATCH -- the STL is NOT mirrored and the opening is in the right corner.")
    else:
        print("*** MISMATCH -- investigate ***")
