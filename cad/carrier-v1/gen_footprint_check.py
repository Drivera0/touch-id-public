"""
gen_footprint_check.py -- a 1:1 paper check for the ONE assumed footprint.

Every number on this sheet is now traced to a primary source.  The XIAO land
pattern comes from Seeed's own "XIAO Series Package and PCB Design", page 3
(XIAO RP2040, SKU 102010428).  The pogo/dowel pattern is parsed live out of
pcb-v7-zero-opens.kicad_pcb.

Print at 100% / "actual size" (NOT "fit to page"), check the 50 mm ruler with
calipers, then lay a real XIAO RP2040 on the pad pattern as a final sanity
check before spending money.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
import gen_carrier as G

HERE = os.path.dirname(os.path.abspath(__file__))
MM = 1/25.4

fig = plt.figure(figsize=(210*MM, 297*MM), dpi=300)      # A4 portrait
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 210); ax.set_ylim(0, 297)
ax.set_aspect("equal"); ax.axis("off")

def txt(x, y, t, s=9, **kw): ax.text(x, y, t, fontsize=s, **kw)

txt(15, 282, "carrier-v1 — 1:1 FOOTPRINT CHECK", 14, weight="bold")
txt(15, 275, "Print at 100% / actual size. NOT 'fit to page'.", 9)
txt(15, 270, "1. Check the ruler below with calipers — it must read 50.0 mm.", 8)
txt(15, 265, "2. Lay a real XIAO RP2040 on the pad pattern. Pads must line up.", 8)
txt(15, 260, "3. Both patterns below are traced to primary sources — see README.", 8)

# --- ruler ---
y = 245
ax.plot([15, 65], [y, y], color="black", lw=1.2)
for i in range(11):
    x = 15 + i*5
    ax.plot([x, x], [y, y + (3 if i % 2 == 0 else 1.8)], color="black", lw=0.8)
txt(15, y-5, "0", 7); txt(63, y-5, "50 mm", 7)

# --- XIAO pad pattern, 1:1 ---
cx, cy = 60.0, 175.0
txt(15, 228, f"XIAO RP2040 land pattern — {G.XIAO_ROWS} mm rows, {G.XIAO_PITCH} mm "
             f"pitch, {G.XIAO_N}/side, pads {G.XIAO_PAD_W} x {G.XIAO_PAD_H}", 9, weight="bold")
txt(15, 223, "Source: Seeed 'XIAO Series Package and PCB Design' p.3 (CONFIRMED)", 7)
ax.add_patch(Rectangle((cx-G.XIAO_BODY_W/2, cy-G.XIAO_BODY_H/2),
                       G.XIAO_BODY_W, G.XIAO_BODY_H,
                       fc="none", ec="black", lw=0.8, ls="--"))
txt(cx, cy+G.XIAO_BODY_H/2+3, "module body 21.0 x 17.8", 7, ha="center")
txt(cx, cy+21.0/2+7, "USB-C THIS END", 8, ha="center", weight="bold")
y0 = cy - (G.XIAO_N-1)*G.XIAO_PITCH/2
for i in range(G.XIAO_N):
    for sx, names in ((-1, G.XIAO_LEFT), (1, G.XIAO_RIGHT)):
        px, py = cx + sx*G.XIAO_ROWS/2, y0 + i*G.XIAO_PITCH
        ax.add_patch(Rectangle((px-G.XIAO_PAD_W/2, py-G.XIAO_PAD_H/2),
                               G.XIAO_PAD_W, G.XIAO_PAD_H,
                               fc="#999999", ec="black", lw=0.5))
        txt(px + sx*(G.XIAO_PAD_W/2+0.8), py-0.6, names[i], 6,
            ha="left" if sx > 0 else "right")
ax.annotate("", xy=(cx-G.XIAO_ROWS/2, cy-12.5), xytext=(cx+G.XIAO_ROWS/2, cy-12.5),
            arrowprops=dict(arrowstyle="<->", lw=0.8))
txt(cx, cy-13.2, f"{G.XIAO_ROWS} mm centre-to-centre (Seeed p.3)", 7, ha="center")

# --- pogo + dowel pattern, 1:1 (this one IS traced to the board file) ---
px0, py0 = 60.0, 110.0
txt(15, 132, "Pogo + dowel pattern — traced to pcb-v7-zero-opens.kicad_pcb (confirmed)",
    9, weight="bold")
ax.add_patch(Rectangle((px0-10, py0-9.5), 20, 19, fc="none", ec="black", lw=0.8, ls="--"))
txt(px0, py0+9.5+3, "your board 20.0 x 19.0", 7, ha="center")
for (x, y_), nm in zip(G.J3, G.J3_NAME):
    ax.add_patch(Circle((px0+x, py0+y_), G.POGO_PAD/2, fc="none", ec="black", lw=0.7))
    ax.add_patch(Circle((px0+x, py0+y_), G.POGO_DRILL/2, fc="black"))
    txt(px0+x, py0+y_+2.2, nm, 5, ha="center", rotation=90)
for (x, y_) in G.MH_DUT:
    ax.add_patch(Circle((px0+x, py0+y_), G.DOWEL_PAD/2, fc="none", ec="black", lw=0.7))
    ax.add_patch(Circle((px0+x, py0+y_), G.DOWEL_DRILL/2, fc="black"))
    txt(px0+x, py0+y_-3.0, "dowel", 5, ha="center")
txt(px0, py0-13, "2.00 mm pitch — pads are O1.20 on your board", 6, ha="center")

txt(15, 80, "If the XIAO does not fit, the board is still usable:", 9, weight="bold")
txt(15, 74, "J2 (SWD ESC) carries SWDIO / SWCLK / RESET / VSTOR / GND for an external probe.", 8)

fig.savefig(os.path.join(HERE, "carrier-footprint-check.pdf"))
print("wrote carrier-footprint-check.pdf (A4, 1:1)")
