"""
verify_frame_v2.py -- INDEPENDENT go/no-go for flash_frame_v2.stl.

WHY THIS FILE EXISTS.  verify_frame.py (v1) began with `b2f = F.b2f`.  It
imported the very function that was wrong, so every check it ran was performed
in the same mirrored coordinate system as the part, agreed with it perfectly,
and reported "0 blockers" on a frame whose window sits under the XIAO.  A
checker that shares the suspect's alibi is not a checker.

So this file imports NOTHING from gen_frame.  It re-derives the board -> frame
mapping from physical first principles, and it measures the STL itself.

THE MAPPING, DERIVED FROM SCRATCH
  * The carrier is a physical board.  Looking down at its component side --
    which is how it sits in the recess -- you see its KiCad top view.
  * In that view +x_file runs RIGHT and +y_file runs DOWN.  (Check it against
    the board itself: J1 is at y=-13 and prints at the TOP of the render; the
    XIAO is at y=+16..+31 and prints at the BOTTOM.)
  * The frame is a solid printed in a right-handed system with Z up, so viewed
    from +Z its +X runs right and its +Y runs UP.
  * Therefore, with the carrier centred in the recess:
        frame X = u - CCX
        frame Y = CCY - v          <-- the sign v1 got wrong
"""
import numpy as np, struct, sys

CCX, CCY = 7.5, 9.0
def b2f(u, v):
    return (u - CCX, CCY - v)

PINS   = [(u, 3.0) for u in (-8.0, -6.0, -4.0, -2.0, 0.0)]
DOWELS = [(-8.75, 0.0), (8.75, 0.0)]
XIAO   = (-8.5, 15.88, 8.5, 31.12)
SCREWS = [(-12.0, -16.0), (27.0, -16.0), (-12.0, 34.0), (27.0, 34.0)]

STL = sys.argv[1] if len(sys.argv) > 1 else "flash_frame_v2.stl"
b = open(STL, "rb").read()
n = struct.unpack("<I", b[80:84])[0]
T = (np.frombuffer(b, dtype=np.uint8, count=n*50, offset=84)
       .reshape(n, 50)[:, 12:48].copy().view("<f4").reshape(n, 3, 3).astype(float))
A, B, C = T[:,0,:], T[:,1,:], T[:,2,:]
E1, E2 = B-A, C-A
V = T.reshape(-1,3); lo, hi = V.min(0), V.max(0)
D = np.array([0.0137, 0.0071, 1.0]); D /= np.linalg.norm(D)
P = np.cross(D, E2); det = np.einsum('ij,ij->i', E1, P)
ok = np.abs(det) > 1e-12; inv = np.where(ok, 1.0/np.where(ok, det, 1), 0.0)
def solid(pts, chunk=256):
    pts = np.atleast_2d(np.asarray(pts, float)); out = np.zeros(len(pts), bool)
    for s in range(0, len(pts), chunk):
        p = pts[s:s+chunk][:, None, :]; Tv = p - A[None]
        u = np.einsum('knj,nj->kn', Tv, P) * inv
        Q = np.cross(Tv, E1[None]); v = (Q @ D) * inv
        t = np.einsum('nj,knj->kn', E2, Q) * inv
        out[s:s+chunk] = ((ok & (u>=0)&(u<=1)&(v>=0)&(u+v<=1)&(t>1e-9)).sum(1) % 2) == 1
    return out

H = hi[2]; REC_D = 1.8; CAR_T = 1.6
DECK_PROBE_Z = 18.5
fails = []
def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  -- ' + detail) if detail else ''}")
    if not cond: fails.append(name)

print(f"STL {STL}")
print(f"bbox  {hi[0]-lo[0]:.2f} x {hi[1]-lo[1]:.2f} x {hi[2]-lo[2]:.2f} mm\n")

# --- window extents, measured ------------------------------------------
xs = np.arange(lo[0]+0.05, hi[0], 0.15) + 0.013
ys = np.arange(lo[1]+0.05, hi[1], 0.15) + 0.007
py = b2f(0.0, 2.0)[1]; pxc = b2f(0.0, 2.0)[0]
rowy = np.full_like(xs, py); coly = np.full_like(ys, pxc)
row = solid(np.column_stack([xs, rowy, np.full_like(xs, DECK_PROBE_Z)]))
col = solid(np.column_stack([coly, ys, np.full_like(ys, DECK_PROBE_Z)]))
def run_containing(coord, sol, target):
    i = int(np.argmin(np.abs(coord - target)))
    if sol[i]: return None
    a = i
    while a > 0 and not sol[a-1]: a -= 1
    c = i
    while c < len(sol)-1 and not sol[c+1]: c += 1
    return coord[a], coord[c]
wx = run_containing(xs, row, pxc); wy = run_containing(ys, col, py)
print("WINDOW, measured from the mesh")
if wx is None or wy is None:
    print(f"  *** THERE IS SOLID DECK AT frame ({pxc:+.2f},{py:+.2f}),")
    print(f"  *** which is exactly where the pin tails and dowels have to pass.")
    print(f"  *** This part has no window where the carrier needs one.")
    print("\n*** 1 BLOCKER: no opening under the pin row")
    sys.exit(1)
print(f"  X {wx[0]:+7.2f} .. {wx[1]:+7.2f}    Y {wy[0]:+7.2f} .. {wy[1]:+7.2f}\n")

print("GEOMETRY")
pts = [(("pin  %+.0f" % u), b2f(u, v)) for u, v in PINS] + \
      [(("dowel %+.2f" % u), b2f(u, v)) for u, v in DOWELS]
for nm, (X, Y) in pts:
    inside = wx[0] < X < wx[1] and wy[0] < Y < wy[1]
    m = min(X-wx[0], wx[1]-X, Y-wy[0], wy[1]-Y)
    check(f"{nm} inside the window", inside, f"frame ({X:+.2f},{Y:+.2f}) margin {m:+.2f} mm")

# seat bar must be directly under every pin tail
for u, v in PINS:
    X, Y = b2f(u, v)
    zs = np.arange(1.0, 17.0, 0.25)
    col2 = solid(np.column_stack([np.full_like(zs, X), np.full_like(zs, Y), zs]))
    top = zs[col2].max() if col2.any() else None
    check(f"seat bar under pin u={u:+.0f}", top is not None and 9.0 < top < 9.6,
          f"material up to z={top:.2f}" if top is not None else "NOTHING under this pin")

x0, y0 = b2f(XIAO[0], XIAO[1]); x1, y1 = b2f(XIAO[2], XIAO[3])
ylo, yhi = sorted([y0, y1])
gap = max(wy[0] - yhi, ylo - wy[1])
check("XIAO footprint clear of the window", gap > 0, f"gap {gap:+.2f} mm")

for u, v in SCREWS:
    X, Y = b2f(u, v)
    check(f"screw hole at ({X:+.1f},{Y:+.1f})", not solid([(X, Y, 15.0)])[0])

# --- orientation mark: board +Y is the spacebar edge -> frame -Y ---------
print("\nMARKINGS")
def face_pocket(fixed, axis, z=10.0):
    scan = np.arange(-20, 20.1, 0.5)
    pts = [(c, fixed, z) if axis == 0 else (fixed, c, z) for c in scan]
    return (~solid(pts)).any()
check("side walls are now clean -- nothing on the -Y face", not face_pocket(lo[1]+0.5, 0))
check("side walls are now clean -- nothing on the +Y face", not face_pocket(hi[1]-0.5, 0))

def band_cut(ysign):
    gx = np.arange(-8.0, 8.01, 0.12)
    gy = np.arange(ysign*(hi[1]-4.2), ysign*(hi[1]-0.8), 0.12*ysign)
    X, Y = np.meshgrid(gx, gy)
    return (~solid(np.column_stack([X.ravel(), Y.ravel(),
                                    np.full(X.size, H-0.3)]))).sum()
n_lo, n_hi = band_cut(-1), band_cut(+1)
check("arrow engraved into the TOP face, -Y band", n_lo > 200, f"{n_lo} engraved points")
check("nothing engraved in the +Y band (arrow points one way only)", n_hi < 20,
      f"{n_hi} engraved points")

# --- corner labels -------------------------------------------------------
LBL_X, LBL_Y = hi[0]-6.0, hi[1]-2.5
zl = H - 0.3
for txt, sx, sy in (("TL",-1,1), ("TR",1,1), ("BL",-1,-1), ("BR",1,-1)):
    gx = np.arange(sx*LBL_X-2.6, sx*LBL_X+2.6, 0.12)
    gy = np.arange(sy*LBL_Y-1.8, sy*LBL_Y+1.8, 0.12)
    X, Y = np.meshgrid(gx, gy)
    cut = (~solid(np.column_stack([X.ravel(), Y.ravel(), np.full(X.size, zl)]))).sum()
    check(f"corner label {txt} engraved", cut > 60, f"{cut} engraved sample points")

print()
if fails:
    print(f"*** {len(fails)} BLOCKER(S): " + "; ".join(fails))
    sys.exit(1)
print("FRAME v2: 0 blockers -- window is over the pins, bar is under them,")
print("labels are cut, mark is on the spacebar face.  Checked without importing")
print("a single line of gen_frame.")
