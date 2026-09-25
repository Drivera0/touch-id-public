"""
gen_diameter_guide.py -- what "barrel diameter" means and why 1.05 is the line.
Left: where the calipers go (across, not along).  Right: the fit that depends on it.
"""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyBboxPatch
import gen_frame as F

GOLD, SILVER = "#d4a017", "#c3cbd1"
HOLE_D = 1.05                       # the carrier's pogo hole

fig, (ax, bx) = plt.subplots(1, 2, figsize=(16, 7.4), dpi=150,
                             gridspec_kw=dict(width_ratios=[1.45, 1]))

# ---------------- left: side view, calipers ACROSS the tube ----------------
x = 0.0
ax.add_patch(Polygon([(x, 0), (x + F.PIN_HEAD_L, F.PIN_HEAD_D/2),
                      (x + F.PIN_HEAD_L, -F.PIN_HEAD_D/2)],
                     closed=True, fc=SILVER, ec="#5a6670", lw=1.5, zorder=3))
x += F.PIN_HEAD_L
ax.add_patch(Rectangle((x, -F.PIN_SHANK_D/2), F.PIN_SHANK_L, F.PIN_SHANK_D,
                       fc=SILVER, ec="#5a6670", lw=1.5, zorder=3))
x += F.PIN_SHANK_L
bx0 = x
ax.add_patch(Rectangle((x, -F.PIN_TUBE_D/2), F.PIN_TUBE_L, F.PIN_TUBE_D,
                       fc=GOLD, ec="#7a5c00", lw=1.5, zorder=3))
bx1 = x + F.PIN_TUBE_L
mid = (bx0 + bx1) / 2

# caliper jaws, closed ACROSS the tube
for sgn in (1, -1):
    ax.add_patch(Rectangle((mid - 1.6, sgn*F.PIN_TUBE_D/2), 3.2, sgn*0.5,
                           fc="#455a64", ec="#263238", lw=1.2, zorder=5))
ax.annotate("", xy=(mid, -F.PIN_TUBE_D/2 - 0.5), xytext=(mid, 2.6),
            arrowprops=dict(arrowstyle="-", color="#b26a00", lw=1.2), zorder=4)
ax.annotate("", xy=(mid + 2.4, -F.PIN_TUBE_D/2), xytext=(mid + 2.4, F.PIN_TUBE_D/2),
            arrowprops=dict(arrowstyle="<->", color="#b26a00", lw=2.2), zorder=6)
ax.text(mid, 2.9, "MEASURE ACROSS THE TUBE", color="#b26a00", ha="center",
        fontsize=13.5, fontweight="bold", va="bottom", zorder=6)

ax.annotate("", xy=(bx0, -4.3), xytext=(bx1, -4.3),
            arrowprops=dict(arrowstyle="<->", color="#9aa3aa", lw=1.4))
ax.text(mid, -4.7, f"NOT along it — that is the length, {F.PIN_TUBE_L} mm,\n"
        "which you already gave me", ha="center", va="top",
        color="#9aa3aa", fontsize=11)

ax.text(bx0 - 2.2, -2.0, "the silver parts are thinner —\nkeep the jaws on the GOLD",
        fontsize=11, color="#5a6670", ha="center", va="top")
ax.plot([bx0 - 2.2, bx0 + 0.6], [-1.9, -F.PIN_TUBE_D/2 - 0.15], color="#5a6670", lw=1.1)

ax.set_title("Where the calipers go", fontsize=15, pad=18)
ax.set_xlim(-5.0, F.PIN_L + 4.0); ax.set_ylim(-6.4, 4.4)
ax.set_aspect("equal"); ax.axis("off")

# ---------------- right: the fit it decides ----------------
CY = 0.55
bx.add_patch(Circle((0, CY), HOLE_D/2, fc="#eef5ef", ec="#2e7d32", lw=3, zorder=1))
bx.add_patch(Circle((0, CY), F.PIN_TUBE_D/2, fc=GOLD, ec="#7a5c00", lw=2, zorder=2))
bx.annotate(f"carrier hole  O{HOLE_D}", xy=(HOLE_D/2*0.71, CY + HOLE_D/2*0.71),
            xytext=(0.95, 1.30), color="#2e7d32", fontsize=12, fontweight="bold",
            ha="left", va="center",
            arrowprops=dict(arrowstyle="-", color="#2e7d32", lw=1.3))
bx.annotate(f"the barrel — O{F.PIN_TUBE_D}?", xy=(-F.PIN_TUBE_D/2*0.71, CY - F.PIN_TUBE_D/2*0.71),
            xytext=(-1.60, 0.02), color="#5d4037", fontsize=12, fontweight="bold",
            ha="left", va="center",
            arrowprops=dict(arrowstyle="-", color="#5d4037", lw=1.3))
bx.text(0, -0.35, "the gap between them is 0.015 mm per side,\nif the drawing's "
        "O1.02 is right", ha="center", va="top", fontsize=10.5, color="#607d8b")

bx.add_patch(FancyBboxPatch((-1.35, -1.12), 2.7, 0.42,
                            boxstyle="round,pad=0.07", fc="#e8f5e9",
                            ec="#2e7d32", lw=1.8))
bx.text(0, -0.91, "1.05 or under   →   it fits, order the board",
        ha="center", va="center", fontsize=12, color="#1b5e20", fontweight="bold")
bx.add_patch(FancyBboxPatch((-1.35, -1.76), 2.7, 0.42,
                            boxstyle="round,pad=0.07", fc="#fdecea",
                            ec="#c62828", lw=1.8))
bx.text(0, -1.55, "over 1.05   →   tell me, I widen the holes",
        ha="center", va="center", fontsize=12, color="#b71c1c", fontweight="bold")

bx.set_title("Why it matters — shown about 400x life size", fontsize=15, pad=18)
bx.set_xlim(-1.75, 1.75); bx.set_ylim(-2.15, 1.55)
bx.set_aspect("equal"); bx.axis("off")

fig.suptitle("Barrel DIAMETER = how fat the gold tube is, about 1 mm",
             fontsize=16)
fig.text(0.5, 0.025, "Close the jaws gently until they just touch — a brass tube "
         "this thin will squash if you crank them. Take it halfway along the gold, "
         "away from either end.",
         ha="center", fontsize=11.5, color="#37474f")
fig.tight_layout(rect=[0, 0.055, 1, 0.94])
fig.savefig("diameter-guide.png", dpi=150, facecolor="white")
print("wrote diameter-guide.png")
