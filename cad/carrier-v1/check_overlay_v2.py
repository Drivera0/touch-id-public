"""
check_overlay_v2.py -- SAME geometry as check_overlay.py, drawn in the
orientation you actually see the board in.

check_overlay.py / check_hole_position.py plotted +Y UP.  The board renders and
displays Y-DOWN (memory: touchid-y-axis-sign-trap), so those two pictures were a
vertical MIRROR of the real part.  The STL and the PCB were never affected --
only my drawings.  Here every point is drawn at (x, -y), which matches the
carrier render and the physical parts.
"""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import gen_carrier as G

CCX, CCY = (G.BX0+G.BX1)/2, (G.BY0+G.BY1)/2
CLR, WALL = 0.5, 5.0
CAR_W, CAR_H = G.BX1-G.BX0, G.BY1-G.BY0
OUT_W, OUT_H = CAR_W+2*CLR+2*WALL, CAR_H+2*CLR+2*WALL
OPEN_W, OPEN_H, OCX, OCY = 24.0, 22.0, 0.0, 2.0

def rect(ax, x0, y0, w, h, **kw):
    """board-local rect -> drawn flipped in Y"""
    ax.add_patch(Rectangle((x0, -(y0+h)), w, h, **kw))
def pt(x, y):
    return (x, -y)

fig, axes = plt.subplots(1, 2, figsize=(13.4, 8.6))

for ax, mode in zip(axes, ("carrier", "frame")):
    # frame outer wall
    rect(ax, CCX-OUT_W/2, CCY-OUT_H/2, OUT_W, OUT_H,
         fill=(mode=="frame"), fc="#e8e8e8", ec="#444",
         lw=2.2 if mode=="frame" else 1.2, ls="-" if mode=="frame" else ":")
    # the opening
    rect(ax, OCX-OPEN_W/2, OCY-OPEN_H/2, OPEN_W, OPEN_H,
         fc="#ffe9c7", ec="#e08a00", lw=2.2, zorder=1)

    if mode == "carrier":
        rect(ax, G.BX0, G.BY0, CAR_W, CAR_H, fill=False, ec="#1b5e20", lw=2.4, zorder=2)
        rect(ax, G.DX0_, G.DY0_, G.DX1_-G.DX0_, G.DY1_-G.DY0_,
             fill=False, ec="#00897b", lw=1.8, zorder=3)
        for p in G.parts:
            ref, px, py, _r, pads = p[0], p[1], p[2], p[3], p[4]
            xs=[px+q[1] for q in pads]; ys=[py+q[2] for q in pads]
            if ref.startswith("PP"):
                for x,y in zip(xs,ys): ax.add_patch(Circle(pt(x,y),.55,fc="#c9a227",ec="#7a5c00",lw=.8,zorder=5))
            elif ref.startswith("DW"):
                for x,y in zip(xs,ys): ax.add_patch(Circle(pt(x,y),.6,fc="#888",ec="#222",lw=.8,zorder=5))
            else:
                x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys); pad=1.2
                rect(ax, x0-pad, y0-pad, x1-x0+2*pad, y1-y0+2*pad,
                     fill=False, ec="#5c6bc0", lw=1.3, zorder=4)
                nm={"U1":"U1  XIAO RP2040","J1":"J1  3.6 V IN","J2":"J2  SWD ESCAPE"}.get(ref)
                if nm: ax.text(*pt((x0+x1)/2, y0-pad-0.8), nm, ha="center", va="bottom",
                               fontsize=8, color="#3949ab", zorder=6)
        ax.text(*pt(0, G.BY0-2.0), "CARRIER PCB, AS YOU SEE IT", ha="center", va="bottom",
                fontsize=10, color="#1b5e20", weight="bold")
        ax.set_title("Carrier PCB + where the frame's window falls", fontsize=11)
    else:
        for (x,y) in G.MH:
            ax.add_patch(Circle(pt(x,y), 2.9, fc="#fff", ec="#333", lw=1.4, zorder=4))
        rect(ax, CCX-(CAR_W+2*CLR)/2, CCY-(CAR_H+2*CLR)/2, CAR_W+2*CLR, CAR_H+2*CLR,
             fill=False, ec="#999", lw=1.0, ls="--", zorder=2)
        ax.text(*pt(OCX, OCY-OPEN_H/2-1.2), f"OPENING {OPEN_W:.0f} x {OPEN_H:.0f}",
                ha="center", va="bottom", fontsize=9, color="#a05b00", weight="bold")
        ax.set_title("Printed frame, same orientation", fontsize=11)

    # the spacebar edge (+Y) is at the BOTTOM in this view
    ytop, ybot = -(CCY-OUT_H/2), -(CCY+OUT_H/2)
    ax.annotate("", xy=(CCX, ybot+1.5), xytext=(CCX, ybot+8.0),
                arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#b00"))
    ax.text(CCX, ybot+9.4, "+Y  SPACEBAR EDGE\nframe's engraved arrow is on THIS wall",
            ha="center", va="bottom", fontsize=8.5, color="#b00", weight="bold")
    ax.text(CCX, ytop-1.4, "J1 / power-in end  (-Y)", ha="center", va="top",
            fontsize=8.5, color="#555")

    ax.set_xlim(CCX-OUT_W/2-5, CCX+OUT_W/2+5)
    ax.set_ylim(ybot-13, ytop+5)
    ax.set_aspect("equal"); ax.axis("off")

fig.suptitle("CORRECTED ORIENTATION -- my earlier two diagrams were flipped top-to-bottom",
             fontsize=12, color="#b00", weight="bold")
fig.tight_layout(rect=[0,0,1,0.95])
fig.savefig("overlay-check-v2.png", dpi=170)
print("wrote overlay-check-v2.png")

print("\nIn this (true) view, measuring the FRAME from its outer walls:")
print(f"  left wall   -> window left edge : {(OCX-OPEN_W/2)-(CCX-OUT_W/2):.1f} mm")
print(f"  right wall  -> window right edge: {(CCX+OUT_W/2)-(OCX+OPEN_W/2):.1f} mm")
print(f"  TOP wall (J1 end)   -> window   : {(OCY-OPEN_H/2)-(CCY-OUT_H/2):.1f} mm")
print(f"  BOTTOM wall (arrow) -> window   : {(CCY+OUT_H/2)-(OCY+OPEN_H/2):.1f} mm")
