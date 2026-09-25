"""
gen_measure_guide.py -- what to put the calipers on.
One pin, drawn lying in your hand, at 25x. Numbers from gen_frame.
"""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, FancyBboxPatch
import gen_frame as F

GOLD, SILVER = "#d4a017", "#c3cbd1"
fig, ax = plt.subplots(figsize=(15, 7.6), dpi=150)

# the pin lying horizontally: tip at the left, tail at the right
x = 0.0
tip_x = x
ax.add_patch(Polygon([(x, 0), (x + F.PIN_HEAD_L, F.PIN_HEAD_D/2),
                      (x + F.PIN_HEAD_L, -F.PIN_HEAD_D/2)],
                     closed=True, fc=SILVER, ec="#5a6670", lw=1.5, zorder=3))
x += F.PIN_HEAD_L
ax.add_patch(Rectangle((x, -F.PIN_SHANK_D/2), F.PIN_SHANK_L, F.PIN_SHANK_D,
                       fc=SILVER, ec="#5a6670", lw=1.5, zorder=3))
x += F.PIN_SHANK_L
barrel_x0 = x
ax.add_patch(Rectangle((x, -F.PIN_TUBE_D/2), F.PIN_TUBE_L, F.PIN_TUBE_D,
                       fc=GOLD, ec="#7a5c00", lw=1.5, zorder=3))
barrel_x1 = x + F.PIN_TUBE_L

def dim(x0, x1, y, label, col, lw=2.0, fs=14, weight="bold", above=True):
    ax.annotate("", xy=(x0, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="<->", color=col, lw=lw))
    for xx in (x0, x1):
        ax.plot([xx, xx], [y - 0.28, y + 0.28], color=col, lw=lw*0.7)
    ax.text((x0 + x1)/2, y + (0.45 if above else -0.45), label, ha="center",
            va="bottom" if above else "top",
            color=col, fontsize=fs, fontweight=weight)

# THIS is the number
ax.add_patch(FancyBboxPatch((barrel_x0 - 0.12, -0.95), F.PIN_TUBE_L + 0.24, 1.9,
                            boxstyle="round,pad=0.10", fc="#fff8e1",
                            ec="#e6a700", lw=2.5, zorder=1))
dim(barrel_x0, barrel_x1, 2.2, f"MEASURE THIS  —  the gold barrel only\n"
    f"drawing says {F.PIN_TUBE_L} mm", "#b26a00", fs=15)

# not this
dim(tip_x, barrel_x0, -2.2, f"the plunger, {F.PIN_L - F.PIN_TUBE_L:.2f} mm\n"
    f"silver, and it slides in and out", "#5a6670", lw=1.4, fs=11,
    weight="normal", above=False)
dim(tip_x, barrel_x1, -4.4, f"NOT this  —  the whole pin, {F.PIN_L} mm", "#9aa3aa",
    lw=1.4, fs=12, weight="normal", above=False)

ax.annotate("pointy end\ntouches your board", xy=(0.3, 0.55), xytext=(-1.2, 4.2),
            fontsize=11, color="#5a6670", ha="center",
            arrowprops=dict(arrowstyle="->", color="#5a6670", lw=1.2))
ax.annotate("flat end\nrests on the shelf", xy=(barrel_x1 - 0.3, 0.55),
            xytext=(barrel_x1 + 0.6, 4.2), fontsize=11, color="#7a5c00",
            ha="center", arrowprops=dict(arrowstyle="->", color="#7a5c00", lw=1.2))

ax.set_title("Which bit is the gold barrel\n"
             "(one P75-E2 pin, lying sideways, about 25x life size)",
             fontsize=15)
ax.text(F.PIN_L/2, -6.0,
        "The gold barrel is the fat brass tube. The silver bit and the pointy "
        "tip are one piece — the plunger — and it\nslides in and out of that "
        "tube. Squeeze the tip and you will see it move; the gold does not.",
        ha="center", va="top", fontsize=12, color="#37474f")
ax.set_xlim(-3.4, F.PIN_L + 3.4); ax.set_ylim(-8.2, 5.4)
ax.set_aspect("equal"); ax.axis("off")
fig.tight_layout()
fig.savefig("measure-guide.png", dpi=150, facecolor="white")
print("wrote measure-guide.png")
