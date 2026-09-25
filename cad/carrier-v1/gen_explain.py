"""
gen_explain.py -- an annotated top view of carrier-v1, drawn STRAIGHT OUT OF
gen_carrier.py so the picture cannot drift from the board.  Orientation is the
physical top view: the file is Y-down, so +Y runs DOWNWARD here, exactly as the
board plots and exactly as KiCad shows it.
"""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Ellipse
import gen_carrier as G

fig, ax = plt.subplots(figsize=(14.0, 9.6), dpi=150)
ax.add_patch(Rectangle((G.BX0, G.BY0), G.BX1-G.BX0, G.BY1-G.BY0,
                       fc="#1b5e20", ec="#0d3010", lw=2, zorder=0))

# where the DUT lands
ax.add_patch(Rectangle((-10, -9.5), 20, 19, fc="#ffffff10", ec="#ffe082",
                       lw=1.6, ls="--", zorder=2))
ax.text(-0.5, -8.9, "YOUR TOUCHID BOARD\nSITS HERE  20.00 x 19.00", ha="center",
        va="top", color="#ffe082", fontsize=9, zorder=3)

# XIAO body
ax.add_patch(Rectangle((-G.XIAO_BODY_W/2, G.XIAO_CY-G.XIAO_BODY_H/2),
                       G.XIAO_BODY_W, G.XIAO_BODY_H,
                       fc="#37474f", ec="#90a4ae", lw=1.4, zorder=2))
ax.text(0, G.XIAO_CY, "XIAO RP2040\n(USB-C here)", ha="center", va="center",
        color="white", fontsize=9, zorder=3)

COL = {"pogo": "#e040fb", "dowel": "#ff8a65", "power": "#ffd54f",
       "swd": "#4fc3f7", "smd": "#f06292", "mh": "#eeeeee", "via": "#b0bec5"}

def pad(ref, num, x, y, w, h, drill, kind):
    if drill:
        # oblong pads really are oblong -- PP* are 1.60 x 2.60, stretched
        # across the row so there is ring enough to hand-solder
        ax.add_patch(Ellipse((x, y), w, h, fc=COL[kind], ec="none", zorder=4))
        ax.add_patch(Circle((x, y), drill/2, fc="#1b5e20", ec="none", zorder=5))
    else:
        ax.add_patch(Rectangle((x-w/2, y-h/2), w, h, fc=COL[kind], ec="none", zorder=4))

KIND = {"PP": "pogo", "DW": "dowel", "TP": "power", "J1": "power",
        "J2": "swd", "U1": "smd", "R1": "smd", "R2": "smd", "R3": "smd"}
for (ref, px, py, rot, pads, hide) in G.parts:
    k = KIND.get(ref[:2], KIND.get(ref, "smd"))
    for (num, dx, dy, shape, w, h, drill, layers, net) in pads:
        pad(ref, num, px+dx, py+dy, w, h, drill, k)
for (x, y) in G.MH:
    ax.add_patch(Circle((x, y), 1.6, fc=COL["mh"], ec="none", zorder=4))
    ax.add_patch(Circle((x, y), 1.6, fc="#1b5e20", ec=COL["mh"], lw=1.2, zorder=5))
for (x, y, net) in G.V:
    ax.add_patch(Circle((x, y), 0.4, fc=COL["via"], ec="none", zorder=4))

def call(tx, ty, px, py, text, col):
    ax.annotate(text, xy=(px, py), xytext=(tx, ty), color=col, fontsize=10,
                ha="left" if tx > px else "right", va="center", zorder=9,
                arrowprops=dict(arrowstyle="-", color=col, lw=1.3,
                                shrinkA=2, shrinkB=4),
                bbox=dict(fc="#00000099", ec=col, lw=0.8, boxstyle="round,pad=0.35"))

call(-24, 3.0, -8.0, 3.0,
     "5 x POGO PIN  O1.05\nthe pins that touch\nyour board's J3 pads\n2.00 mm apart", COL["pogo"])
call(-24, -3.5, -8.75, 0.0,
     "2 x DOWEL  O1.05\ncopper posts your board\ndrops over -- these set\nthe position", COL["dowel"])
call(-24, -13.0, -7.0, -13.0,
     "POWER IN\nJ1 = 2-pin plug (+ / -)\nTP1/TP2 = big holes to\nmeter with a multimeter", COL["power"])
call(39, 13.0, 26.16, 13.0,
     "5 x SWD ESCAPE  O1.02\nspare header -- only if you\never want an external\ndebugger instead", COL["swd"])
call(39, 21.0, 8.9, 25.0,
     "XIAO RP2040\nthe only part YOU solder.\nUSB-C plugs in here", "#90a4ae")
call(39, 18.42, 13.0, 18.42,
     "R1-R3  100R\nJLC fit these", COL["smd"])
call(-24, -19.0, -12.0, -16.0,
     "4 x MOUNT  O3.2 (no copper)\nM3 screws into the\n3D-printed frame", COL["mh"])
call(39, 32.0, 21.08, 15.88,
     "4 x VIA  O0.4\ntiny -- they just take a\nsignal to the other side.\nNothing goes in them", COL["via"])

ax.annotate("", xy=(12.5, 10.0), xytext=(12.5, -10.0), zorder=8,
            arrowprops=dict(arrowstyle="->", color="#ffe082", lw=2))
ax.text(13.2, 5.0, "+Y\nspacebar\nedge", color="#ffe082", fontsize=9,
        va="center", zorder=9)

ax.set_xlim(-40, 58); ax.set_ylim(G.BY0-3, G.BY1+2)
ax.invert_yaxis()                       # file is Y-down: this IS the top view
ax.set_aspect("equal"); ax.axis("off")
ax.set_title("TouchID carrier v1 -- top view, 47 x 58 mm\n"
             "(this is the side you look at with the XIAO facing you)",
             color="#222", fontsize=13)
fig.tight_layout()
fig.savefig("carrier-explained.png", dpi=150, facecolor="white")
print("wrote carrier-explained.png")
