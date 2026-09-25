"""assembly_view.py -- the one picture that says how it goes together.
Drawn in the orientation Dan has on screen right now: ARROW WALL AT THE TOP,
looking straight down, +X to the right.  Frame-centred mm."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import gen_carrier as G

CCX, CCY = 7.5, 9.0
def F(x, y): return (x - CCX, y - CCY)          # board-local -> frame-centred
def R(ax, x0, y0, x1, y1, **kw):
    a, b = F(x0, y0); c, d = F(x1, y1)
    ax.add_patch(Rectangle((a, b), c-a, d-b, **kw))

fig, ax = plt.subplots(figsize=(8.0, 9.2))
OUT_W, OUT_H = 58.0, 69.0
ax.add_patch(Rectangle((-OUT_W/2, -OUT_H/2), OUT_W, OUT_H, fc="#ececec", ec="#333", lw=2.4))
ax.add_patch(Rectangle((-24, -29.5), 48, 59, fc="#f7f7f7", ec="#aaa", lw=1.2, ls="--"))
ax.add_patch(Rectangle((-19.5, -18), 24, 22, fc="#ffdca8", ec="#e08a00", lw=2.6, zorder=2))
ax.add_patch(Rectangle((-19.5, -12), 24, 10, fc="#cfe9ff", ec="none", zorder=1))

# carrier, sitting in the recess the CORRECT way round
R(ax, G.BX0, G.BY0, G.BX1, G.BY1, fill=False, ec="#1b5e20", lw=2.6, zorder=3)
R(ax, G.DX0_, G.DY0_, G.DX1_, G.DY1_, fill=False, ec="#00897b", lw=2.0, zorder=4)
R(ax, -8.5, 15.88, 8.5, 31.12, fc="#5c6bc0", alpha=.30, ec="#3949ab", lw=1.6, zorder=4)
R(ax, -3.0, -14.0, 3.0, -12.0, fc="#c62828", alpha=.45, ec="#8e0000", lw=1.4, zorder=4)
R(ax, 15.0, 12.0, 27.2, 14.0, fc="#7e57c2", alpha=.35, ec="#4527a0", lw=1.2, zorder=4)

for x in (-8., -6., -4., -2., 0.):
    ax.add_patch(Circle(F(x, 3.0), .75, fc="#ffcc33", ec="#5a4200", lw=1.0, zorder=6))
for (x, y) in G.MH_DUT:
    ax.add_patch(Circle(F(x, y), .8, fc="#5ec8ff", ec="#023", lw=1.0, zorder=6))
for (x, y) in G.MH:
    ax.add_patch(Circle(F(x, y), 1.2, fc="#fff", ec="#333", lw=1.3, zorder=6))

ax.annotate("", xy=(0, 33.2), xytext=(0, 26.5),
            arrowprops=dict(arrowstyle="-|>", lw=2.6, color="#b00"), zorder=7)
ax.text(0, 35.6, "ARROW WALL", ha="center", va="bottom", fontsize=11, color="#b00", weight="bold")
ax.text(0, 24.0, "the XIAO end of the carrier\ngoes at THIS end",
        ha="center", va="top", fontsize=9.5, color="#3949ab", weight="bold", zorder=8)
ax.text(0, -24.5, "the 3.6 V connector end\ngoes at THIS end", ha="center", va="center",
        fontsize=9.5, color="#8e0000", weight="bold")

ax.text(6.5, -7.0, "WINDOW\n24 x 22", ha="left", va="center", fontsize=9,
        color="#a05b00", weight="bold")
ax.text(6.5, -13.5, "blue = seat bar", ha="left", va="center", fontsize=8, color="#2b7fb8")
ax.text(-30.5, 23.5, "U1 XIAO", ha="right", va="center", fontsize=8.5, color="#3949ab")
ax.text(30.5, 4.0, "J2", ha="left", va="center", fontsize=8.5, color="#4527a0")
ax.text(-30.5, -22.0, "J1 3.6 V", ha="right", va="center", fontsize=8.5, color="#8e0000")
ax.text(30.5, -7.0, "gold = 5 pogo pins\nblue = 2 dowels\nboth sit in the window",
        ha="left", va="center", fontsize=8.5, color="#333")

ax.set_xlim(-46, 46); ax.set_ylim(-40, 40)
ax.set_aspect("equal"); ax.axis("off")
ax.set_title("HOW IT GOES TOGETHER -- arrow wall at the top, looking down", fontsize=11.5)
fig.tight_layout(); fig.savefig("assembly-view.png", dpi=180)
print("wrote assembly-view.png")
