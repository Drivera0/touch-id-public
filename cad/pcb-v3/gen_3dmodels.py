"""
gen_3dmodels.py — STEP bodies for KiCad's 3D viewer (Alt+3), at the dimensions
this project actually verified. Nothing here is a guess.

  0402   1.0 x 0.5 x 0.5    JLCPCB C1525   model name C0402_L1.0-W0.5-H0.5
  0603   1.6 x 0.8 x 0.8    JLCPCB C19666  model name C0603_L1.6-W0.8-H0.8
  QFN20  3.5 x 3.5 x 1.0    JLCPCB C882746 VQFN-20_L3.5-W3.5-H1.0-P0.50
  IND    2.5 x 2.0 x 1.2    Sunlord/DMBJ 252012, datasheet C = 1.2 Max
  MDBT50Q 10.5 x 15.5 x 2.05  Raytac Ver.K (x is the 10.5 side in the
                              footprint frame -- pads run x -4.80..4.80)
  X2SON-4 1.0 x 0.8 x 0.4     TI DQN0004A
  POGO/TP flat copper, 0.05 mm token so the viewer shows something

Each body sits on z=0 (board face) and is centred on the footprint origin,
which is what KiCad expects when the model has no (at) offset.
"""
import os
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "3dmodels")
os.makedirs(OUT, exist_ok=True)

# name: (x, y, z, chamfer)
PARTS = {
    "chip_0402":  (1.00, 0.50, 0.50, 0.06),
    "chip_0603":  (1.60, 0.80, 0.80, 0.08),
    "qfn20_3p5":  (3.50, 3.50, 1.00, 0.10),
    "ind_2520":   (2.50, 2.00, 1.20, 0.15),
    "mdbt50q":    (10.50, 15.50, 2.05, 0.20),
    "x2son4":     (1.00, 0.80, 0.40, 0.05),
}

for name, (L, W, H, ch) in PARTS.items():
    b = cq.Workplane("XY").box(L, W, H, centered=(True, True, False))
    if ch and ch < min(L, W, H) / 2.5:
        b = b.edges("|Z").chamfer(ch)
    p = os.path.join(OUT, name + ".step")
    cq.exporters.export(b.val(), p)
    print("  %-12s %5.2f x %5.2f x %5.2f -> %s" % (name, L, W, H, os.path.basename(p)))

print("\nwrote %d models to %s" % (len(PARTS), os.path.relpath(OUT, HERE)))
