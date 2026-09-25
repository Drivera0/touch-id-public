"""
gen_pinl_explain.py -- the bug the seller's drawing exposed, in one picture.

Left:  what the frame was built to do before the drawing was read.
Right: what it does now.
All numbers imported from gen_frame so the picture cannot drift from the part.
"""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
import gen_frame as F

CAR_BOT, CAR_TOP = F.H - F.REC_D, F.H - F.REC_D + F.CAR_T
GOLD, GREY = "#c9a227", "#b0bec5"


def pin(ax, x, seat):
    z = seat
    ax.add_patch(Rectangle((x-F.PIN_TUBE_D/2, z), F.PIN_TUBE_D, F.PIN_TUBE_L,
                           fc=GOLD, ec="#7a5c00", lw=1))
    z += F.PIN_TUBE_L
    ax.add_patch(Rectangle((x-F.PIN_SHANK_D/2, z), F.PIN_SHANK_D, F.PIN_SHANK_L,
                           fc=GREY, ec="#546e7a", lw=1))
    z += F.PIN_SHANK_L
    ax.add_patch(Polygon([(x-F.PIN_HEAD_D/2, z), (x+F.PIN_HEAD_D/2, z),
                          (x+0.1, z+F.PIN_HEAD_L), (x-0.1, z+F.PIN_HEAD_L)],
                         closed=True, fc=GREY, ec="#37474f", lw=1))
    return seat + F.PIN_TUBE_L


def panel(ax, seat, title, verdict, ok, ylo, yhi):
    ax.add_patch(Rectangle((-9, seat-1.6), 18, 1.6, fc="#b0bec5", ec="#546e7a"))
    ax.text(0, seat-0.8, "the shelf inside the print", ha="center",
            va="center", fontsize=8)
    ax.add_patch(Rectangle((-9, CAR_BOT), 18, F.CAR_T, fc="#2e7d32", ec="#1b5e20"))
    ax.text(9.4, CAR_BOT+0.8, "carrier", fontsize=8, va="center", color="#1b5e20")
    top = pin(ax, 0, seat)
    col = "#2e7d32" if ok else "#c62828"
    ax.annotate("", xy=(4.2, CAR_BOT), xytext=(4.2, CAR_TOP),
                arrowprops=dict(arrowstyle="<->", color=col, lw=1.6))
    ax.annotate(verdict, xy=(4.2, (CAR_BOT+CAR_TOP)/2), xytext=(11.0, CAR_TOP+5.0),
                fontsize=10, color=col, va="center", ha="left", fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=col, lw=1.2))
    ax.set_title(title, fontsize=10.5)
    ax.set_xlim(-11, 24); ax.set_ylim(ylo, yhi)
    ax.set_aspect("equal"); ax.axis("off")


fig, (a1, a2) = plt.subplots(1, 2, figsize=(13.5, 8.2), dpi=150)

OLD_SEAT = CAR_TOP - F.PIN_L + 2.0          # the old rule: 2 mm of pin proud
YLO, YHI = OLD_SEAT - 3, CAR_TOP + 9
panel(a1, OLD_SEAT, "BEFORE — shelf set from the pin's TOTAL length\n"
      f"(bar at z={OLD_SEAT:.2f}, aiming for 2.0 mm of tip proud)",
      "the GREY plunger is in the hole.\nSolder there and the spring dies —\n"
      "five rigid posts.", False, YLO, YHI)
panel(a2, F.SEAT_Z, "AFTER — shelf set from the GOLD BARREL\n"
      f"(bar at z={F.SEAT_Z:.2f}, barrel {F.TUBE_PROUD} mm proud)",
      "the GOLD barrel fills the hole.\nSolder there and the spring works,\n"
      "with 0.015 mm of slop.", True, YLO, YHI)

fig.suptitle("4.04 mm of this pin lives OUTSIDE its barrel: a 1.5 mm head and a "
             "2.54 mm plunger shank.\n"
             "Set the shelf from the total length and the wrong part ends up in "
             "the board.", fontsize=12)
fig.tight_layout(rect=[0, 0.01, 1, 0.9])
fig.savefig("pinl-explained.png", dpi=150, facecolor="white")
print(f"wrote pinl-explained.png   old bar z={OLD_SEAT:.2f}, new bar z={F.SEAT_Z:.2f}")
