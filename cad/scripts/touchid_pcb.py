# TouchID module PCB + attached hardware — 3D model (CadQuery)
# Frame: HOUSING frame (same as touchid_module.py). PCB top face at z=0
# (against the housing back rim); board body z -1.2..0; components rise into
# the housing cavity (z > 0); pogo pads on the outward face (z < -1.2).
#
# Exports:
#   touchid_pcb_assembly.step / .stl  — board + ESP32 + LDO + caps + pads
#   touchid_module_assembly.step      — housing + PCB assembly + sensor puck
#
# Run:  python touchid_pcb.py

import cadquery as cq
import os

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exports")

# ---------------- parameters (mm) ----------------
pcb_sq = 19.5          # board outline (lip is 19.72; -0.2 fit)
pcb_t = 1.2
corner_r = 2.0
screw_pos = [(8.3, 0.0), (-8.3, 0.0)]   # matches relocated housing bosses
screw_hole_d = 2.2
post_holes = []
pad_d = 2.2
pad_t = 0.06
# pad positions: housing frame = mirror-x of pad-side frame
j4 = [(-x, y) for x in (4.33, 6.87) for y in (7.84, 5.30, 2.76)]
j11 = [(-x, y) for x in (-6.67, -4.13) for y in (8.07, 5.53)]

esp_w, esp_l, esp_h = 13.2, 16.6, 2.4   # ESP32-C3-MINI-1
ldo = (1.0, 1.0, 0.4)                   # TPS7A02 X2SON-4 (micro)
cap = (2.0, 1.25, 1.25)                 # 0805 bulk caps
cap4 = (1.0, 0.5, 0.5)                  # 0402

# ---------------- board ----------------
board = (cq.Workplane("XY").workplane(offset=-pcb_t)
         .rect(pcb_sq, pcb_sq).extrude(pcb_t))
board = board.edges("|Z").fillet(corner_r)
for (sx, sy) in screw_pos:
    board = board.cut(cq.Workplane("XY").workplane(offset=-pcb_t - 0.1)
                      .center(sx, sy).circle(screw_hole_d / 2).extrude(pcb_t + 0.2))
for (px, py, pd) in post_holes:
    board = board.cut(cq.Workplane("XY").workplane(offset=-pcb_t - 0.1)
                      .center(px, py).circle(pd / 2).extrude(pcb_t + 0.2))

# ---------------- components ----------------
esp = (cq.Workplane("XY").rect(esp_w, esp_l).extrude(esp_h)
       .edges("|Z").fillet(0.3))
# ROTATED 180: antenna toward housing -y = keyboard interior (away from the
# metal top-right corner of the frame)
ant = cq.Workplane("XY").workplane(offset=esp_h - 0.6).center(0, -(esp_l/2 - 2.5)).rect(esp_w - 1, 4.4).extrude(0.61)
esp = esp.cut(ant)

# ALL parts on TOP (same side as the chip): micro packages in the side
# strips. housing frame x = kicad x, y = -kicad y
ldo_s = cq.Workplane("XY").center(-7.6, 3.0).rect(ldo[0], ldo[1]).extrude(ldo[2])
cap1 = cq.Workplane("XY").center(-7.6, 4.4).rect(cap4[1], cap4[0]).extrude(cap4[2])
cap2 = cq.Workplane("XY").center(7.6, 3.6).rect(cap[1], cap[0]).extrude(cap[2])

pads = None
for (x, y) in j4 + j11:
    p = (cq.Workplane("XY").workplane(offset=-pcb_t - pad_t)
         .center(x, y).circle(pad_d / 2).extrude(pad_t))
    pads = p if pads is None else pads.union(p)

# ---------------- assembly + export ----------------
asm = cq.Assembly()
asm.add(board, name="pcb", color=cq.Color(0.08, 0.08, 0.1))          # black
asm.add(esp, name="esp32_c3_mini", color=cq.Color(0.75, 0.78, 0.8))  # shield
asm.add(ldo_s, name="ldo_3v3", color=cq.Color(0.25, 0.25, 0.28))
asm.add(cap1, name="cap1", color=cq.Color(0.55, 0.45, 0.3))
asm.add(cap2, name="cap2", color=cq.Color(0.55, 0.45, 0.3))
asm.add(pads, name="pogo_pads", color=cq.Color(0.83, 0.68, 0.21))    # gold
asm.save(os.path.join(out, "touchid_pcb_assembly.step"))

merged = board.union(esp).union(ldo_s).union(cap1).union(cap2).union(pads)
cq.exporters.export(merged, os.path.join(out, "touchid_pcb_assembly.stl"),
                    tolerance=0.01)

# ---------------- full module assembly ----------------
# housing geometry comes from its exported STEP:
housing = cq.importers.importStep(os.path.join(out, "touchid_module_housing.step"))

# sensor puck (representative round fingerprint module) seated from inside
sensor = (cq.Workplane("XY").workplane(offset=3.7)
          .circle(13.9 / 2).extrude(2.7))   # top at 7.6 (inside c'bore lip)

full = cq.Assembly()
full.add(housing, name="housing", color=cq.Color(0.85, 0.86, 0.88))
full.add(board, name="pcb", color=cq.Color(0.08, 0.08, 0.1))
full.add(esp, name="esp32", color=cq.Color(0.75, 0.78, 0.8))
full.add(ldo_s, name="ldo", color=cq.Color(0.25, 0.25, 0.28))
full.add(pads, name="pads", color=cq.Color(0.83, 0.68, 0.21))
full.add(sensor, name="fingerprint_sensor", color=cq.Color(0.15, 0.15, 0.17))
full.save(os.path.join(out, "touchid_module_assembly.step"))
print("exported touchid_pcb_assembly.step/.stl + touchid_module_assembly.step")
