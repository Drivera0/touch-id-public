---
title: How to route pcb-v4 — the recipe that works
type: project
updated: 2026-08-29
---

# Routing recipe for v4

**Order matters more than any router setting on this board.** Every net that
kept failing did so because something else took its corridor first. The fix was
never a better search — it was going earlier.

## The recipe

```
python build_pcb_v3.py                       # -> pcb-v3.kicad_pcb
# inject the 10 pogo no-via rule areas (r = 1.45 mm)   [script below]
# STAGE 1 — the nets that cannot wait
route.py k0 -> k1  --nets BL_RETURN HARV_1 HARV_2 HARV_3 \
                           PCM_VDD PCM_VM CELL_NEG VREF_SAMP SENSOR_SW_EN
# STAGE 2 — everything else, EXCLUDING stage 1 by name
route.py k1 -> k3  --nets "*" "!GND" "!BL_RETURN" "!HARV_1" ... --keep-input-copper
# strip the temporary pogo zones
python stitch_open.py   k4 k5      (ABSOLUTE path -- see below)
route_planes.py         k6 --nets GND --plane-layers In2.Cu
python gnd_taps.py      k6 k7
# KiCad: Edit > Fill All Zones (B), SAVE
python preflight.py     pcb-v4-routed-wip.kicad_pcb
```

## Why each stage exists

**Stage 1 — pogo nets.** `BL_RETURN`, `HARV_1..3` terminate on J11's pads,
which are **B.Cu**, so they need an F.Cu→B.Cu via. Routed late, the only
remaining spot is inside the pogo contact, and the router took it: two vias
0.450 mm and 0.065 mm inside J11's pads. Routed FIRST with the no-via zones
in place, **all four succeed and check 22 passes.** The rule was always
satisfiable; the router just had to go before the board filled up.

**Stage 1 — PCM nets.** Same story. Routed late, `PCM_VDD`, `PCM_VM` and
`VREF_SAMP` came out with **no copper at all** — not "open", *absent*, which
`stitch_open`'s NO-PATH count cannot see and which flattered a worse board.

**Stage 2 must EXCLUDE stage 1 by name.** `--keep-input-copper` is not enough:
if a stage-1 net is still in `--nets "*"`, stage 2 rips and re-routes it, and
`PCM_VM` lost its copper again exactly that way.

## Traps in the tooling (all cost real time)

| | |
|---|---|
| `stitch_open` needs an **absolute** board path | it runs `check_connected` with `cwd=KRT`; a relative path resolves there, finds nothing, and it prints "nothing open" on a board with 8 open pads |
| `check_connect.py` ignores zone fill | reports 19 nets split on a fully connected board. **`preflight` check 6/17 is the gate**, not this |
| `check_drc` needs the `.kicad_pro` beside the board | without it, it grades at a 0.20 default instead of 0.10: 48 violations, of which 38 were phantom |
| the router **rewrites your design rules** | it wrote `min_clearance 0.1187` — whatever it achieved — into the `.kicad_pro`. Restore from `fab_floor_touchid.txt` |
| KiCad **rewrites track geometry** on format migration | 20240108 -> 20260206 turned a path skirting the antenna keep-out into a diagonal cutting the corner, 0.2635 mm deep. `gnd_taps` now leaves 0.30 mm of slack |
| pads whose `size` is a lie | U3/U4 are `custom` pads with a 0.1485 mm **anchor**; the copper is in `(primitives)`. Bit three separate scripts |
