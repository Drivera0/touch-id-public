"""
match_screenshot.py -- rasterise flash_frame.stl in the SAME on-screen
orientation as Dan's CAD screenshot, and lay the carrier's pogo pins / dowels
on top.  Nothing here comes from gen_frame.py; every pixel is sampled from the
STL that went to JLC.

Dan's viewer is showing the part rotated 180 deg about Z from the canonical top
view, so screen = (-x, -y).  That single fact is why my earlier drawings did not
appear to overlap his screenshots.
"""
import numpy as np, struct
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import gen_carrier as G

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
P = np.cross(D, E2); det = np.einsum('ij,ij->i', E1, P)
ok = np.abs(det) > 1e-12; inv = np.where(ok, 1.0/np.where(ok, det, 1), 0.0)

def inside(pts, chunk=256):
    pts = np.asarray(pts, float); out = np.zeros(len(pts), bool)
    for s in range(0, len(pts), chunk):
        p = pts[s:s+chunk][:, None, :]                  # (k,1,3)
        Tv = p - A[None]                                # (k,n,3)
        u = np.einsum('knj,nj->kn', Tv, P) * inv
        Q = np.cross(Tv, E1[None])
        v = (Q @ D) * inv
        t = np.einsum('nj,knj->kn', E2, Q) * inv
        hit = ok & (u>=0) & (u<=1) & (v>=0) & (u+v<=1) & (t>1e-9)
        out[s:s+chunk] = (hit.sum(1) % 2) == 1
    return out

STEP = 0.30
xs = np.arange(lo[0]+0.01, hi[0], STEP) + 0.013
ys = np.arange(lo[1]+0.01, hi[1], STEP) + 0.007
X, Y = np.meshgrid(xs, ys)
flat = np.column_stack([X.ravel(), Y.ravel()])
print(f"sampling {len(flat)} columns x 2 levels ...")
deck = inside(np.column_stack([flat, np.full(len(flat), 18.5)])).reshape(X.shape)
bar  = inside(np.column_stack([flat, np.full(len(flat),  6.0)])).reshape(X.shape)

img = np.where(deck, 2, np.where(bar, 1, 0))            # 2 deck, 1 seen-through, 0 void
print("  done")

# ---- draw in DAN'S orientation: screen = (-x, -y) ----
fig, ax = plt.subplots(figsize=(7.6, 8.8))
ax.imshow(img, origin="lower", cmap="Greys_r", vmin=0, vmax=2,
          extent=[-xs[0], -xs[-1], -ys[0], -ys[-1]], interpolation="nearest")

for x, y in [(px, py) for px in (-8.,-6.,-4.,-2.,0.) for py in (3.,)]:
    fx, fy = x - 7.5, y - 9.0
    ax.add_patch(Circle((-fx, -fy), .8, fc="#ffcc33", ec="#7a5c00", lw=1.0, zorder=5))
for (x, y) in G.MH_DUT:
    fx, fy = x - 7.5, y - 9.0
    ax.add_patch(Circle((-fx, -fy), .85, fc="#66d9ff", ec="#036", lw=1.0, zorder=5))

ax.text(0, 33.0, "ARROW / SPACEBAR WALL IS AT THE BOTTOM IN THIS VIEW",
        ha="center", va="top", fontsize=8, color="#fff", weight="bold")
ax.annotate("", xy=(0, -33.0), xytext=(0, -26.0),
            arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#ff4444"), zorder=6)
ax.text(12, 12, "the 5 pogo pins (gold)\nand 2 dowels (blue)\nland HERE, inside the\nwindow -- that is the\nwhole point of it",
        ha="left", va="center", fontsize=8.5, color="#111",
        bbox=dict(fc="#ffffffcc", ec="none", pad=3), zorder=7)

ax.set_xlim(30, -30); ax.set_ylim(-36, 36)
ax.invert_xaxis()
ax.set_aspect("equal"); ax.axis("off")
ax.set_title("flash_frame.stl sampled at z=18.5, drawn in YOUR screenshot's\n"
             "orientation, with the carrier's pins laid on top", fontsize=10)
fig.tight_layout(); fig.savefig("match-screenshot.png", dpi=180)
print("wrote match-screenshot.png")
