"""
render_frame.py -- a real section through the printed frame at the pin row,
with the carrier, the pins, the dowels and the DUT drawn on top of it.

The outline is a genuine trimesh cross-section of flash_frame.stl, not a
sketch, so anything wrong with the print shows up here.
"""
import numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
import gen_frame as F, gen_carrier as G

m = trimesh.load("flash_frame.stl")
_, bar_y = F.b2f(0.0, F.BAR_Y)

def section_xz(y):
    s = m.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    p2, T = s.to_2D()
    out = []
    for poly in p2.polygons_full:
        for ring in [poly.exterior] + list(poly.interiors):
            pts = np.array(ring.coords)
            h = np.c_[pts, np.zeros(len(pts)), np.ones(len(pts))] @ T.T
            out.append(h[:, [0, 2]])          # world x, world z
    return out

fig, (axp, ax) = plt.subplots(2, 1, figsize=(14, 12.4), dpi=150,
                              gridspec_kw=dict(height_ratios=[1.15, 1]))
# --- plan view: a real z-section through the cavity, showing the bar ---
def section_xy(z):
    """returns (outer rings, hole rings) in world XY -- the holes matter:
    filling them grey too is what made the first plot look like a solid slab"""
    s_ = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    p2, T = s_.to_2D()
    def w(ring):
        pts = np.array(ring.coords)
        return (np.c_[pts, np.zeros(len(pts)), np.ones(len(pts))] @ T.T)[:, [0, 1]]
    outer = [w(poly.exterior) for poly in p2.polygons_full]
    holes = [w(r) for poly in p2.polygons_full for r in poly.interiors]
    return outer, holes

out_, hol_ = section_xy(F.SEAT_Z - 0.5)
for ring in out_:
    axp.add_patch(Polygon(ring, closed=True, fc="#cfd8dc", ec="#546e7a", lw=1.3, zorder=1))
for ring in hol_:
    axp.add_patch(Polygon(ring, closed=True, fc="white", ec="#546e7a", lw=1.1, zorder=2))
for ring in section_xy(F.DECK_Z + 1.0)[1]:
    axp.add_patch(Polygon(ring, closed=True, fc="none", ec="#ff7043",
                          lw=1.4, ls="--", zorder=3))
for (bx, by) in G.J3:
    fx, fy = F.b2f(bx, by)
    axp.add_patch(plt.Circle((fx, fy), 0.51, fc="#ab47bc", ec="#4a148c", zorder=6))
for (bx, by) in G.MH_DUT:
    fx, fy = F.b2f(bx, by)
    axp.add_patch(plt.Circle((fx, fy), 0.51, fc="#ff8a65", ec="#bf360c", zorder=6))
for (x, y) in F.MH:
    axp.add_patch(plt.Circle((x, y), F.MH_D/2, fc="white", ec="#546e7a", zorder=6))
axp.text(-26.0, F.b2f(0, F.BAR_Y)[1], "SEAT\nBAR\n%g wide\ntop z=%.2f"
         % (F.BAR_W, F.SEAT_Z),
         ha="center", va="center", fontsize=8, color="#37474f", zorder=8)
axp.text(14.0, -22.0, "dashed = the 24 x 22 opening\nthrough the deck above",
         fontsize=8.5, color="#d84315", zorder=8)
axp.text(0, 31.5, "the notch in this edge is the orientation triangle, cut into "
         "the outer face.\nThis is the +Y / spacebar edge.",
         ha="center", fontsize=9, color="#37474f", zorder=8)
axp.set_xlim(-32, 32); axp.set_ylim(-38, 38)
axp.invert_yaxis()        # same top view as carrier-explained.png: +Y downward
axp.set_aspect("equal"); axp.axis("off")
axp.set_title("PLAN -- section through the cavity at the seat bar", fontsize=11)

for ring in section_xz(bar_y - 0.01):
    ax.add_patch(Polygon(ring, closed=True, fc="#cfd8dc", ec="#546e7a", lw=1.4, zorder=1))

CAR_BOT, CAR_TOP = F.H - F.REC_D, F.H - F.REC_D + F.CAR_T
X0, X1 = F.b2f(G.BX0, 0)[0], F.b2f(G.BX1, 0)[0]
ax.add_patch(Rectangle((X0, CAR_BOT), X1-X0, F.CAR_T, fc="#2e7d32", ec="#1b5e20",
                       lw=1.2, zorder=4))
ax.text((X0+X1)/2, CAR_BOT+F.CAR_T/2, "CARRIER PCB  1.6", ha="center", va="center",
        color="white", fontsize=8, zorder=5)

# pins: tube from the seat bar up through the carrier, tip PIN_PROUD proud
# the real P75-E2 profile: O1.02 barrel, then O0.74 plunger shank, then the
# O1.3 head cone.  Drawing it as one uniform tube is what hid the bug.
for (bx, by) in G.J3:
    fx, _ = F.b2f(bx, by)
    z = F.SEAT_Z
    ax.add_patch(Rectangle((fx-F.PIN_TUBE_D/2, z), F.PIN_TUBE_D, F.PIN_TUBE_L,
                           fc="#c9a227", ec="#7a5c00", lw=0.8, zorder=6))
    z += F.PIN_TUBE_L
    ax.add_patch(Rectangle((fx-F.PIN_SHANK_D/2, z), F.PIN_SHANK_D, F.PIN_SHANK_L,
                           fc="#cfd8dc", ec="#546e7a", lw=0.8, zorder=6))
    z += F.PIN_SHANK_L
    ax.add_patch(Polygon([(fx-F.PIN_HEAD_D/2, z), (fx+F.PIN_HEAD_D/2, z),
                          (fx+0.12, z+F.PIN_HEAD_L), (fx-0.12, z+F.PIN_HEAD_L)],
                         closed=True, fc="#b0bec5", ec="#37474f", lw=0.8, zorder=6))
# dowels
DL = CAR_TOP - F.SEAT_Z + F.DOWEL_PROUD
for (bx, by) in G.MH_DUT:
    fx, _ = F.b2f(bx, by)
    ax.add_patch(Rectangle((fx-0.51, F.SEAT_Z), 1.02, DL, fc="#ff8a65",
                           ec="#bf360c", lw=0.8, zorder=6))
# the DUT, resting on the pin tips
DUT_BOT = CAR_TOP + F.PIN_PROUD
dx0, _ = F.b2f(-10.0, 0); dx1, _ = F.b2f(10.0, 0)
ax.add_patch(Rectangle((dx0, DUT_BOT), dx1-dx0, 1.2, fc="#1565c0", ec="#0d47a1",
                       lw=1.2, zorder=7))
ax.text((dx0+dx1)/2, DUT_BOT+0.6, "YOUR BOARD  1.2", ha="center", va="center",
        color="white", fontsize=8, zorder=8)

def dim(x, y0, y1, label, col="#c62828", dx=0.0):
    ax.annotate("", xy=(x, y0), xytext=(x, y1), zorder=9,
                arrowprops=dict(arrowstyle="<->", color=col, lw=1.2))
    ax.text(x+dx+0.6, (y0+y1)/2, label, color=col, fontsize=9, va="center", zorder=9)

dim(-27.0, 0, F.SEAT_Z, f"seat bar {F.SEAT_Z:.2f}")
dim(-24.0, F.SEAT_Z, CAR_TOP, f"pin inside the frame {CAR_TOP-F.SEAT_Z:.1f}")
dim(-21.0, CAR_TOP, CAR_TOP+F.PIN_PROUD, f"tip proud {F.PIN_PROUD:.2f}")
dim(-18.0, CAR_TOP, F.SEAT_Z+F.PIN_TUBE_L, f"barrel {F.TUBE_PROUD} proud")
dim(13.0, F.SEAT_Z, F.SEAT_Z+DL, f"dowel cut to {DL:.1f}")
dim(24.0, 0, F.H, f"frame {F.H}")

ax.axhline(F.DECK_Z, color="#90a4ae", lw=0.7, ls=":", zorder=2)
ax.text(X1+1.0, F.DECK_Z, f"deck {F.DECK_Z}", fontsize=8, color="#546e7a", va="bottom")
ax.text(0, -3.6, "SECTION THROUGH THE PIN ROW  (frame outline is a real "
        "cross-section of flash_frame.stl)", ha="center", fontsize=10, color="#37474f")
ax.text(0, -5.4, "GOLD = the O1.02 barrel, the only part you may solder.  GREY = "
        "the O0.74 plunger and its O1.3 head, which must stay clear of the board.",
        ha="center", fontsize=9, color="#78909c")

ax.set_xlim(-31, 33); ax.set_ylim(-7, 32)
ax.set_aspect("equal"); ax.axis("off")
fig.tight_layout()
fig.savefig("frame-section.png", dpi=150, facecolor="white")
print("wrote frame-section.png")
