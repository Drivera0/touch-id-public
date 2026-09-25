"""
check_hole_position.py -- is the frame's big opening where it should be?

Pure-python re-derivation of the frame's plan geometry from gen_carrier (the
single source of truth) + the constants in gen_frame.py.  No cadquery needed.
Draws a labelled top view so the printed part can be held against it.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import gen_carrier as G

CAR_W, CAR_H = G.BX1 - G.BX0, G.BY1 - G.BY0
CCX, CCY = (G.BX0 + G.BX1) / 2, (G.BY0 + G.BY1) / 2
CLR, WALL = 0.5, 5.0
OUT_W, OUT_H = CAR_W + 2*CLR + 2*WALL, CAR_H + 2*CLR + 2*WALL
REC_W, REC_H = CAR_W + 2*CLR, CAR_H + 2*CLR
OPEN_W, OPEN_H = 24.0, 22.0

def b2f(x, y):
    return (x - CCX, y - CCY)

OCX, OCY = b2f(0.0, 2.0)
ox0, ox1 = OCX - OPEN_W/2, OCX + OPEN_W/2
oy0, oy1 = OCY - OPEN_H/2, OCY + OPEN_H/2

print(f"frame        {OUT_W:.1f} x {OUT_H:.1f}   (X {-OUT_W/2:+.1f}..{OUT_W/2:+.1f}, Y {-OUT_H/2:+.1f}..{OUT_H/2:+.1f})")
print(f"recess       {REC_W:.1f} x {REC_H:.1f}")
print(f"opening      {OPEN_W:.1f} x {OPEN_H:.1f}  centre ({OCX:+.2f}, {OCY:+.2f})  -> OFF-CENTRE BY DESIGN")
print(f"  edges      X {ox0:+.2f}..{ox1:+.2f}   Y {oy0:+.2f}..{oy1:+.2f}")
print(f"  wall gap   -X {ox0-(-OUT_W/2):.1f}   +X {OUT_W/2-ox1:.1f}   -Y {oy0-(-OUT_H/2):.1f}   +Y {OUT_H/2-oy1:.1f}")
print()

pins = [b2f(x, 3.0) for x in (-8.0, -6.0, -4.0, -2.0, 0.0)]
dowels = [b2f(x, y) for (x, y) in G.MH_DUT]
screws = [b2f(x, y) for (x, y) in G.MH]

def inside(p, name):
    ok = ox0 < p[0] < ox1 and oy0 < p[1] < oy1
    m = min(p[0]-ox0, ox1-p[0], p[1]-oy0, oy1-p[1])
    print(f"  {name:<16} ({p[0]:+7.2f},{p[1]:+7.2f})  {'IN ' if ok else 'OUT'}  margin {m:+.2f} mm")
    return ok

print("must fall INSIDE the opening:")
allok = True
for i, p in enumerate(pins, 1):
    allok &= inside(p, f"pogo pin {i}")
for i, p in enumerate(dowels, 1):
    allok &= inside(p, f"dowel {i}")
print()
print("must fall OUTSIDE the opening (they are solid bosses):")
for i, p in enumerate(screws, 1):
    out = not (ox0 < p[0] < ox1 and oy0 < p[1] < oy1)
    print(f"  screw boss {i}    ({p[0]:+7.2f},{p[1]:+7.2f})  {'OK (outside)' if out else 'CLASH'}")
    allok &= out
print()
print("VERDICT:", "opening is correct" if allok else "*** OPENING IS WRONG ***")

# ---------------- drawing ----------------
fig, ax = plt.subplots(figsize=(7.2, 8.4))
ax.add_patch(Rectangle((-OUT_W/2, -OUT_H/2), OUT_W, OUT_H, fill=False, lw=2.5, ec="#333"))
ax.add_patch(Rectangle((-REC_W/2, -REC_H/2), REC_W, REC_H, fill=False, lw=1.0, ec="#999", ls="--"))
ax.add_patch(Rectangle((ox0, oy0), OPEN_W, OPEN_H, fc="#ffe9c7", ec="#e08a00", lw=2.0))
ax.add_patch(Rectangle(b2f(G.DX0_, G.DY0_), G.DX1_-G.DX0_, G.DY1_-G.DY0_,
                       fill=False, ec="#2a7", lw=1.6, ls="-"))
for p in screws:
    ax.add_patch(Circle(p, 1.2, fc="#fff", ec="#333", lw=1.2))
for p in pins:
    ax.add_patch(Circle(p, 0.55, fc="#c9a227", ec="#7a5c00", lw=0.8))
for p in dowels:
    ax.add_patch(Circle(p, 0.6, fc="#888", ec="#333", lw=0.8))

ax.annotate("", xy=(0, OUT_H/2 - 1.5), xytext=(0, OUT_H/2 - 7.5),
            arrowprops=dict(arrowstyle="-|>", lw=2, color="#b00"))
ax.text(0, OUT_H/2 - 9.5, "ARROW IS ON THIS WALL\n(+Y = SPACEBAR EDGE)",
        ha="center", va="top", fontsize=8, color="#b00", weight="bold")

ax.text(ox0 + OPEN_W/2, oy1 + 1.2, f"OPENING  {OPEN_W:.0f} x {OPEN_H:.0f}\ncentre ({OCX:+.1f}, {OCY:+.1f}) - NOT centred, on purpose",
        ha="center", va="bottom", fontsize=8, color="#a05b00", weight="bold")
ax.text(b2f(0, G.DY0_)[0], b2f(0, G.DY0_)[1] - 1.2, "TouchID board sits here",
        ha="center", va="top", fontsize=8, color="#2a7")
ax.text(OUT_W/2 - 2, OUT_H/2 - 14, "this end is empty because\nthe XIAO + J2 live up here\non the carrier, above the\nDUT -- nothing to reach",
        ha="right", va="top", fontsize=7.5, color="#555")

for lbl, x, y, dy in [(f"{ox0-(-OUT_W/2):.1f}", (-OUT_W/2+ox0)/2, oy0+OPEN_H/2, 0),
                      (f"{OUT_W/2-ox1:.1f}", (ox1+OUT_W/2)/2, oy0+OPEN_H/2, 0)]:
    ax.text(x, y, lbl+" mm", ha="center", va="center", fontsize=7.5, color="#666")

ax.set_xlim(-OUT_W/2-4, OUT_W/2+4); ax.set_ylim(-OUT_H/2-4, OUT_H/2+4)
ax.set_aspect("equal"); ax.axis("off")
ax.set_title("Flash frame, looking straight down\n(gold = pogo pins, grey = dowels, white = screw bosses)",
             fontsize=10)
fig.tight_layout()
fig.savefig("hole-position-check.png", dpi=190)
print("\nwrote hole-position-check.png")
