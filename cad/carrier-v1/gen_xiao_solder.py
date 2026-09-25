"""gen_xiao_solder.py -- which XIAO pads carry a signal and which are just glue.
Pad positions imported from gen_carrier so the picture cannot drift."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import gen_carrier as G

NET_OF = {"D8": "SWCLK", "D10": "SWDIO", "D7": "nRESET", "GND": "GND"}
y0 = G.XIAO_CY - (G.XIAO_N - 1) * G.XIAO_PITCH / 2.0

fig, ax = plt.subplots(figsize=(9.5, 10.5), dpi=150)
ax.add_patch(Rectangle((-G.XIAO_BODY_W/2, G.XIAO_CY - G.XIAO_BODY_H/2),
                       G.XIAO_BODY_W, G.XIAO_BODY_H, fc="#eceff1", ec="#90a4ae",
                       lw=1.4, ls="--", zorder=1))
ax.text(0, G.XIAO_CY, "XIAO RP2040\nsits here", ha="center", va="center",
        color="#78909c", fontsize=11, zorder=2)

live, dead = 0, 0
for names, x, ha, dx in ((G.XIAO_LEFT, -G.XIAO_ROWS/2, "right", -2.4),
                         (G.XIAO_RIGHT, G.XIAO_ROWS/2, "left", 2.4)):
    for i, nm in enumerate(names):
        y = y0 + i * G.XIAO_PITCH
        net = NET_OF.get(nm)
        if net:
            live += 1
            ax.add_patch(Rectangle((x - G.XIAO_PAD_W/2, y - G.XIAO_PAD_H/2),
                                   G.XIAO_PAD_W, G.XIAO_PAD_H,
                                   fc="#e53935", ec="#8e0000", lw=1.6, zorder=4))
            ax.text(x + dx, y, f"{nm}  →  {net}", ha=ha, va="center",
                    fontsize=11, color="#b71c1c", fontweight="bold", zorder=5)
        else:
            dead += 1
            ax.add_patch(Rectangle((x - G.XIAO_PAD_W/2, y - G.XIAO_PAD_H/2),
                                   G.XIAO_PAD_W, G.XIAO_PAD_H,
                                   fc="#cfd8dc", ec="#78909c", lw=1.1, zorder=4))
            ax.text(x + dx, y, nm, ha=ha, va="center", fontsize=10,
                    color="#78909c", zorder=5)

ax.annotate("", xy=(-G.XIAO_ROWS/2, 12.2), xytext=(G.XIAO_ROWS/2, 12.2),
            arrowprops=dict(arrowstyle="<->", color="#455a64", lw=1.3))
ax.text(0, 11.6, f"{G.XIAO_ROWS} mm between rows", ha="center", va="top",
        fontsize=10, color="#455a64")
ax.annotate("", xy=(-13.4, y0), xytext=(-13.4, y0 + G.XIAO_PITCH),
            arrowprops=dict(arrowstyle="<->", color="#455a64", lw=1.3))
ax.text(-14.0, y0 + G.XIAO_PITCH/2, f"{G.XIAO_PITCH} mm pitch\npads "
        f"{G.XIAO_PAD_W} x {G.XIAO_PAD_H}", fontsize=10, color="#455a64",
        va="center", ha="right")

ax.set_title(f"XIAO RP2040 — {live+dead} pads, only {live} carry anything\n"
             f"(red = wired, grey = not connected to a thing)", fontsize=14)
ax.text(0, 9.6, "Solder the 4 red ones and you have a working programmer.\n"
        "Add 2 or 3 grey ones on the left row so the module cannot lift or tilt.\n"
        "Soldering all 14 is fine too — at 2.54 mm pitch this is the easiest\n"
        "part on the board, far easier than the 0805 resistors.",
        ha="center", va="top", fontsize=11, color="#37474f")
ax.set_xlim(-23, 22); ax.set_ylim(5.0, 36.5)
ax.set_aspect("equal"); ax.axis("off")
fig.tight_layout()
fig.savefig("xiao-solder-guide.png", dpi=150, facecolor="white")
print(f"wrote xiao-solder-guide.png  ({live} live, {dead} dead)")
