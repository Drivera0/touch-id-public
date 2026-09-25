"""
check_overlay.py -- carrier PCB top view with the frame's opening drawn on top.
Everything comes from gen_carrier (single source of truth).  Board-local mm,
+Y drawn UP, +Y = spacebar edge = the wall the frame's arrow is on.
"""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import gen_carrier as G

CCX, CCY = (G.BX0+G.BX1)/2, (G.BY0+G.BY1)/2
CLR, WALL = 0.5, 5.0
CAR_W, CAR_H = G.BX1-G.BX0, G.BY1-G.BY0
OUT_W, OUT_H = CAR_W+2*CLR+2*WALL, CAR_H+2*CLR+2*WALL
# frame opening, expressed back in BOARD-LOCAL coords
OPEN_W, OPEN_H = 24.0, 22.0
OCX, OCY = 0.0, 2.0
ox0, ox1, oy0, oy1 = OCX-OPEN_W/2, OCX+OPEN_W/2, OCY-OPEN_H/2, OCY+OPEN_H/2
# frame outer wall, board-local
fx0, fx1 = CCX-OUT_W/2, CCX+OUT_W/2
fy0, fy1 = CCY-OUT_H/2, CCY+OUT_H/2

fig, ax = plt.subplots(figsize=(8.2, 9.0))
ax.add_patch(Rectangle((fx0,fy0), OUT_W, OUT_H, fill=False, ec="#bbb", lw=1.4, ls=":"))
ax.text(fx1-0.5, fy1-0.8, "frame outer wall", ha="right", va="top", fontsize=7.5, color="#999")

ax.add_patch(Rectangle((G.BX0,G.BY0), CAR_W, CAR_H, fill=False, ec="#1b5e20", lw=2.4))
ax.text(G.BX0+0.8, G.BY1-1.0, "CARRIER PCB  47 x 58", ha="left", va="top",
        fontsize=9, color="#1b5e20", weight="bold")

ax.add_patch(Rectangle((ox0,oy0), OPEN_W, OPEN_H, fc="#ffe9c7", ec="#e08a00", lw=2.2, alpha=.85, zorder=0))
ax.text(ox1+0.8, oy1-0.5, "frame opening\n24 x 22", ha="left", va="top",
        fontsize=8.5, color="#a05b00", weight="bold")

ax.add_patch(Rectangle((G.DX0_,G.DY0_), G.DX1_-G.DX0_, G.DY1_-G.DY0_,
                       fill=False, ec="#00897b", lw=1.8))
ax.text(0, G.DY0_-1.0, "TouchID board 20 x 19", ha="center", va="top",
        fontsize=8, color="#00897b")

lbl = {"PP":"pogo pin","DW":"dowel"}
for p in G.parts:
    ref, px, py, rot, pads = p[0], p[1], p[2], p[3], p[4]
    xs=[px+q[1] for q in pads]; ys=[py+q[2] for q in pads]
    if ref.startswith("PP"):
        for x,y in zip(xs,ys): ax.add_patch(Circle((x,y),.55,fc="#c9a227",ec="#7a5c00",lw=.8,zorder=3))
    elif ref.startswith("DW"):
        for x,y in zip(xs,ys): ax.add_patch(Circle((x,y),.6,fc="#888",ec="#222",lw=.8,zorder=3))
    else:
        x0,x1,y0,y1 = min(xs),max(xs),min(ys),max(ys)
        pad=1.2
        ax.add_patch(Rectangle((x0-pad,y0-pad), x1-x0+2*pad, y1-y0+2*pad,
                               fill=False, ec="#5c6bc0", lw=1.3, zorder=3))
        nm = {"U1":"U1  XIAO RP2040","J1":"J1 power in","J2":"J2 SWD escape",
              "TP1":"TP1","TP2":"TP2"}.get(ref, ref)
        ax.text((x0+x1)/2, y1+pad+0.6, nm, ha="center", va="bottom",
                fontsize=7.5, color="#3949ab", zorder=4)

for (x,y) in G.MH:
    ax.add_patch(Circle((x,y),1.2,fc="#fff",ec="#333",lw=1.2,zorder=3))
ax.text(G.MH[0][0], G.MH[0][1]-2.2, "M3 screw holes (x4)", ha="left", va="top", fontsize=7.5, color="#333")

ax.annotate("", xy=(CCX, fy1-1.2), xytext=(CCX, fy1-7.0),
            arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#b00"))
ax.text(CCX, fy1-8.2, "+Y  SPACEBAR EDGE\n(frame's arrow is on this wall)",
        ha="center", va="top", fontsize=8, color="#b00", weight="bold")

ax.text(G.BX1+1.0, 3.0,
        "the pogo pins are DOWN-LEFT of\nthe board's centre, so the frame's\nwindow is too.  Both are off-centre\nby the same amount -- that is what\nmakes them line up.",
        ha="left", va="center", fontsize=8, color="#444")

ax.set_xlim(fx0-3, fx1+26); ax.set_ylim(fy0-3, fy1+3)
ax.set_aspect("equal"); ax.axis("off")
ax.set_title("Carrier PCB with the frame's opening laid over it", fontsize=11)
fig.tight_layout(); fig.savefig("overlay-check.png", dpi=185)

print(f"board centre        ({CCX:+.2f}, {CCY:+.2f})")
print(f"pogo pin row        x -8.00..0.00  y +3.00")
print(f"opening (board-loc) x {ox0:+.2f}..{ox1:+.2f}  y {oy0:+.2f}..{oy1:+.2f}")
print(f"pogo row offset from board centre: dx {(-4.0)-CCX:+.2f}  dy {3.0-CCY:+.2f}")
print(f"opening  offset from board centre: dx {OCX-CCX:+.2f}  dy {OCY-CCY:+.2f}")
print("wrote overlay-check.png")
