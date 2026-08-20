# TouchID full assembly — separate parts for exploded view + Fusion STEP
# Housing frame, z=0 = PCB top face against housing back rim.
# Parts (sandwich, bottom->top): screws, PCB+components, ribbon, sensor, housing
import cadquery as cq
import os

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exports")
stl_dir = os.path.join(out, "explode_parts")
os.makedirs(stl_dir, exist_ok=True)

# ---- shared params (match touchid_module.py / touchid_pcb.py) ----
pcb_sq, pcb_t, corner_r = 19.5, 1.2, 2.0
screw_pos = [(8.3, 0.0), (-8.3, 0.0)]
esp_w, esp_l, esp_h = 13.2, 16.6, 2.4

# ---- PCB + topside components (one part) ----
board = (cq.Workplane("XY").workplane(offset=-pcb_t)
         .rect(pcb_sq, pcb_sq).extrude(pcb_t).edges("|Z").fillet(corner_r))
for (sx, sy) in screw_pos:
    board = board.cut(cq.Workplane("XY").workplane(offset=-pcb_t - 0.1)
                      .center(sx, sy).circle(1.1).extrude(pcb_t + 0.2))
esp = cq.Workplane("XY").rect(esp_w, esp_l).extrude(esp_h).edges("|Z").fillet(0.3)
ant = (cq.Workplane("XY").workplane(offset=esp_h - 0.6)
       .center(0, -(esp_l/2 - 2.5)).rect(esp_w - 1, 4.4).extrude(0.61))
esp = esp.cut(ant)
ldo = cq.Workplane("XY").center(-7.6, 3.0).rect(1.0, 1.0).extrude(0.4)
c1 = cq.Workplane("XY").center(-7.6, 4.4).rect(0.5, 1.0).extrude(0.5)
c2 = cq.Workplane("XY").center(-7.6, 6.2).rect(0.5, 1.0).extrude(0.5)
c3 = cq.Workplane("XY").center(7.6, 3.6).rect(1.25, 2.0).extrude(1.25)
c4 = cq.Workplane("XY").center(7.6, 7.1).rect(1.25, 2.0).extrude(1.25)
pads = None
j4 = [(-x, y) for x in (4.33, 6.87) for y in (7.84, 5.30, 2.76)]
j11 = [(-x, y) for x in (-6.67, -4.13) for y in (8.07, 5.53)]
for (x, y) in j4 + j11:
    p = (cq.Workplane("XY").workplane(offset=-pcb_t - 0.06)
         .center(x, y).circle(1.1).extrude(0.06))
    pads = p if pads is None else pads.union(p)
pcb_part = board.union(esp).union(ldo).union(c1).union(c2).union(c3).union(c4).union(pads)

# ---- sensor puck (Ø13.9, seats in Ø14.2 counterbore under the 0.8 lip) ----
sensor = (cq.Workplane("XY").workplane(offset=3.74)
          .circle(13.9/2).extrude(2.7))
sensor = sensor.edges(">Z").fillet(0.4)

# ---- ribbon cable (FPC): under sensor -> down the left strip -> J2 pads ----
# J2 left pads (housing frame): x -7.6, y -2.9..-5.9. Ribbon 4 wide, 0.15 thick.
rib_y0, rib_w = -4.4, 4.0
rib_h = (cq.Workplane("XY").workplane(offset=3.55)          # horizontal under sensor
         .center(-3.6, rib_y0).rect(7.6, rib_w).extrude(0.15))
rib_v = (cq.Workplane("XY").workplane(offset=0.05)          # vertical drop at x=-7.35
         .center(-7.4, rib_y0).rect(0.15, rib_w).extrude(3.65))
rib_f = (cq.Workplane("XY").workplane(offset=0.05)          # foot on the PCB over J2
         .center(-7.0, rib_y0).rect(1.0, rib_w).extrude(0.15))
ribbon = rib_h.union(rib_v).union(rib_f)

# ---- screws: M2 from below through PCB into the bosses ----
screws = None
for (sx, sy) in screw_pos:
    shaft = (cq.Workplane("XY").workplane(offset=-pcb_t)
             .center(sx, sy).circle(0.95).extrude(pcb_t + 3.6))
    head = (cq.Workplane("XY").workplane(offset=-pcb_t - 1.0)
            .center(sx, sy).circle(1.8).extrude(1.0))
    s = shaft.union(head)
    screws = s if screws is None else screws.union(s)

# ---- housing (import the signed-off STEP) ----
housing = cq.importers.importStep(os.path.join(out, "touchid_module_housing.step"))

# ---- exports ----
parts = [("housing", housing), ("sensor", sensor), ("ribbon", ribbon),
         ("pcb", pcb_part), ("screws", screws)]
for name, solid in parts:
    cq.exporters.export(solid, os.path.join(stl_dir, f"{name}.stl"), tolerance=0.03)
    print("stl:", name)

asm = cq.Assembly()
colors = {"housing": (0.85, 0.86, 0.88), "sensor": (0.13, 0.13, 0.15),
          "ribbon": (0.85, 0.55, 0.25), "pcb": (0.1, 0.3, 0.16),
          "screws": (0.6, 0.6, 0.62)}
for name, solid in parts:
    asm.add(solid, name=name, color=cq.Color(*colors[name]))
asm.save(os.path.join(out, "touchid_full_assembly.step"))
print("exported touchid_full_assembly.step")
