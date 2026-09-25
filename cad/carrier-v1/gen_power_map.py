"""
gen_power_map.py -- where the power comes from, and why the XIAO needs none
from the bench supply.  Nets imported from gen_carrier.
"""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import gen_carrier as G

USB, BENCH, GND_C = "#1565c0", "#e65100", "#37474f"
fig, ax = plt.subplots(figsize=(14.5, 8.6), dpi=150)

def box(x, y, w, h, label, fc, ec, fs=11, tc="#1c1f23"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.18",
                                fc=fc, ec=ec, lw=2, zorder=3))
    ax.text(x + w/2, y + h/2, label, ha="center", va="center",
            fontsize=fs, zorder=4, color=tc)

def arrow(x0, y0, x1, y1, col, lw=2.6, style="-|>"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style,
                                 mutation_scale=18, color=col, lw=lw, zorder=2))

# --- domain 1: USB ---
box(0.2, 6.4, 2.6, 1.3, "YOUR PC", "#e3f2fd", USB)
box(4.0, 6.4, 3.4, 1.3, "XIAO RP2040\n(the programmer)", "#e3f2fd", USB)
arrow(2.8, 7.05, 4.0, 7.05, USB)
ax.text(3.4, 7.25, "USB-C\n5 V", ha="center", va="bottom", fontsize=10, color=USB)
ax.text(5.7, 7.85, "regulates 5 V down to 3.3 V on board — this is the ONLY "
        "power the XIAO gets", ha="center", va="bottom", fontsize=10, color=USB)

# --- domain 2: bench ---
box(0.2, 1.3, 2.6, 1.3, "DP100\nbench supply", "#fff3e0", BENCH)
box(4.0, 1.3, 3.4, 1.3, "J1  3.6 V IN\n(keyed 2-pin)", "#fff3e0", BENCH)
arrow(2.8, 1.95, 4.0, 1.95, BENCH)
ax.text(3.4, 2.15, "3.6 V", ha="center", va="bottom", fontsize=10, color=BENCH)

# --- the DUT ---
box(10.4, 3.5, 3.2, 3.0, "YOUR\nTOUCHID\nBOARD", "#e8f5e9", "#2e7d32", fs=12)

# signals out of the XIAO
for i, (nm, net, y) in enumerate((("D10", "SWDIO", 5.9), ("D8", "SWCLK", 5.35),
                                  ("D7", "nRESET", 4.8))):
    arrow(7.4, y, 10.4, y, USB, lw=2.0)
    ax.text(8.9, y + 0.12, f"{nm} -> 100 R -> {net}", ha="center", va="bottom",
            fontsize=9.5, color=USB)
ax.text(8.9, 6.25, "3.3 V logic, through R1-R3", ha="center", fontsize=10,
        color=USB, style="italic")

arrow(7.4, 2.6, 10.4, 3.9, BENCH, lw=2.6)
ax.text(9.0, 3.05, "VSTOR — powers your board", ha="center", va="bottom",
        fontsize=10, color=BENCH, rotation=22)

# --- the shared ground ---
ax.plot([5.7, 5.7], [6.4, 0.5], color=GND_C, lw=3, zorder=1)
ax.plot([5.7, 12.0], [0.5, 0.5], color=GND_C, lw=3, zorder=1)
ax.plot([12.0, 12.0], [0.5, 3.5], color=GND_C, lw=3, zorder=1)
ax.plot([5.7, 5.7], [1.3, 0.5], color=GND_C, lw=3, zorder=1)
for x, y in ((5.7, 6.4), (5.7, 1.3), (12.0, 3.5)):
    ax.plot([x], [y], "o", color=GND_C, ms=9, zorder=5)
ax.text(8.6, 0.30, "GND — the fourth wire. One ground shared by all three.",
        ha="center", va="top", fontsize=11.5, color=GND_C, fontweight="bold")

ax.text(0.2, 4.6, "TWO SEPARATE SUPPLIES", fontsize=13, fontweight="bold",
        color="#1c1f23")
ax.text(0.2, 4.15,
        "The XIAO runs off your PC's USB.\n"
        "The bench supply only feeds your\n"
        "board, never the XIAO.\n\n"
        "3V3 and 5V on the XIAO are left\n"
        "unconnected on purpose — 5 V must\n"
        "never reach VSTOR.",
        fontsize=10.5, va="top", color="#37474f")

ax.set_xlim(-0.2, 14.3); ax.set_ylim(-0.4, 8.6)
ax.axis("off")
ax.set_title("Where the power comes from", fontsize=15)
fig.tight_layout()
fig.savefig("power-map.png", dpi=150, facecolor="white")
print("wrote power-map.png")
