---
title: TouchID v4 — Altium cross-check
type: project
---

# v4 — importing into Altium to check the work

**v4 is not a redesign.** It is the verified v3 board, frozen, imported into
Altium so a mature DRC gets an independent look at it. **KiCad stays the master.**
If Altium finds something, we fix it in KiCad and re-export — we do not start
editing in two tools at once.

## Why this is worth doing

Altium's DRC would have caught roughly half of what this project found the hard
way, faster and more reliably: the 40 unconnected GND pads (Un-Routed Net), the
unpoured polygons (Un-Poured Polygon), the 0.200 mm mask sliver (Minimum Solder
Mask Sliver), and every clearance/width/hole rule.

It would **not** have caught the other half, and those were the dangerous ones:
the charger set to 4.246 V against a 4.00 V cell, the housing needing 1.2 mm
while the fab defaults to 1.6, the pogo pad geometry, the thermal-relief
judgement. No EDA tool knows what your battery is rated for. `preflight.py`
keeps earning its place regardless.

## THE RISK, and it is not hypothetical

**Altium's KiCad importer is older than KiCad 10's file format.** We already
learned this file format changed underneath us: KiCad 10 dropped the top-level
`(net N "NAME")` table and now writes `(net "NAME")` on every item, which made
this project's own parsers read **134 pads with zero nets** — and a checker that
sees no nets passes everything.

If the importer half-understands the file, Altium's DRC will be checking a board
that is not ours, and a clean report would mean nothing. **So the import is
verified before any DRC result is believed.**

Two files are provided for exactly this reason:

| file | format | zones | use |
|---|---|---|---|
| `touchid-v4.kicad_pcb` | **KiCad 10** | filled | try this first |
| `touchid-v4-kicad9format.kicad_pcb` | KiCad 9 | unfilled | fallback if the importer chokes |

Identical copper — verified: both are 46 footprints / 134 pads / 124 netted /
459 segments / 65 vias / 3 zones. Only the format and the fill differ. If you
use the fallback, **re-pour the planes in Altium** before reading the DRC.

## Step 1 — import

`File ▸ Import Wizard ▸ KiCad Design Files`. Needs the **KiCad Importer
extension** installed (Extensions & Updates). Point it at `touchid-v4.kicad_pcb`.

## Step 2 — VERIFY THE IMPORT before trusting any DRC

Check these against what Altium reports. **Any mismatch means the importer lost
something, and the DRC result is void until it is explained.**

| quantity | expected |
|---|---|
| Components | **46** |
| Pads | **134** (124 carry a net, 10 are deliberate NC) |
| Nets | **27** |
| Track segments | **459** |
| Vias | **65** — all 0.6 mm / 0.3 mm drill |
| Copper zones | **3** (GND on F.Cu, In2.Cu, B.Cu) |
| Keep-out rule areas | **14** |
| Board outline | **19.30 × 19.30 mm**, 2.0 mm corner radii |
| Board thickness | **1.200 mm** |
| NPTH holes | **2** × Ø1.30 |
| Layers | 4 — F.Cu, In1.Cu, In2.Cu, B.Cu |

The 27 nets: `BL_FLAG BL_RETURN GND HARV_1 HARV_2 HARV_3 LX NRF_VDD OK_HYST
OK_PROG RESET SENSOR_3V3 SENSOR_MCU_3V3 SENSOR_RX SENSOR_SW_EN SENSOR_TX
SENSOR_WAKEUP SWCLK SWDIO VBAT VBAT_OK VBAT_OV_SET VBAT_SENSE VIN_DC VRDIV
VREF_SAMP VSTOR`

> **The 10 unnetted pads are correct, not an import failure.** J4 pins 1/2/3/4/6
> are deliberately unconnected — loading them in knob mode generated volume and
> mute events. Do not "fix" them.

## Step 3 — set the rules to match, then DRC

Altium will import with its own defaults. The DRC is meaningless unless the
rules match what the board was actually built to:

| rule | value | why |
|---|---|---|
| Clearance | **0.10 mm** | JLCPCB standard 4-layer |
| Min track width | **0.127 mm** | 1.43× JLC's 0.0889 floor |
| Via | **0.6 mm / 0.3 mm drill** | not the 0.25/0.15 advanced rung |
| Hole to hole | **0.20 mm** | |
| Board edge clearance | **0.30 mm** | |
| Solder mask sliver | **0.25 mm** | BT1's battery pads were at 0.200 |

**Expected result: clean.** KiCad 10's own DRC and KiCadRoutingTools both report
no violations at these rules.

## Step 4 — the 3D models, which is the real prize

Altium's **Manufacturer Part Search** carries real vendor STEP models. The ones
worth pulling:

| ref | part | why it matters |
|---|---|---|
| U1 | Raytac MDBT50Q-1MV2 | biggest part on the board; the cell sits on top of it |
| U2 | TI BQ25505 (VQFN-20) | |
| U3/U4 | TI TPS7A2033 (X2SON-4) | |
| L1 | DMBJ PNLS252012-220M | |

**What this does and does not change.** The current models are extruded boxes
built from datasheet body dimensions, and a box **circumscribes** the real part —
so the existing housing collision check (which found no collisions) is
*conservative*. Real STEP can only reduce apparent interference, never reveal a
new one, **unless a box was drawn too small**. So treat this as confidence and
visualisation, not as a correctness fix.

**No vendor model will exist for J2, J3, J4, J11 or BT1** — the pogo blocks are
keyboard geometry and the cell is wired from above. Those stay as they are.

## What we do with the result

* Altium agrees → we have two independent tools saying the same thing.
* Altium finds something → **investigate it, do not assume Altium is right.**
  Check it against the board file first. Most "blockers" in this project turned
  out to be the checker, not the board.
* Fixes land in KiCad and get re-exported. One master, always.

---

# RESULT — imported 2026-08-28

## The KiCad 10 file imports WRONG. Use the KiCad 9 fallback.

This is the risk this document was written around, and it was real.

**`touchid-v4.kicad_pcb` (KiCad 10) produced a garbage layer mapping:**

| KiCad layer | Altium gave it |
|---|---|
| F.Cu | Top Layer ✓ |
| **B.Cu** | **Mid Layer2** ✗ |
| In1.Cu | Mid Layer4 ✗ |
| In2.Cu | Mid Layer6 ✗ |
| **Edge.Cuts** | **Mid Layer25** ✗ |
| **F.CrtYd** | **Bottom Layer** ✗ |

It mapped by index order, not meaning — the board outline became a copper
layer and the courtyard became the bottom copper. **A DRC on that would have
been meaningless**, and it would have looked like a successful import.

**`touchid-v4-kicad9format.kicad_pcb` maps correctly:**
F.Cu→Top, In1.Cu→Mid Layer1, In2.Cu→Mid Layer2, B.Cu→Bottom, F/B.Mask→Solder
Mask, F/B.SilkS→Overlay, F/B.Paste→Paste, Edge.Cuts→Keep Out Layer,
courtyards and F.Fab→Mechanical.

> The importer predates KiCad 10's format, exactly as suspected. Its analysis
> log flags the new constructs it does not understand — `uuid`, `stroke`,
> `embedded_fonts`, via `tenting`/`covering`/`plugging`/`capping`/`filling`,
> `duplicate_pad_numbers_are_jumpers` — with **errors: 0**, which is precisely
> why "no errors" is not the same as "imported correctly".

## Fidelity check — what actually came across

| quantity | expected | Altium | |
|---|---|---|---|
| Nets | 27 | **27** | PASS — exact name-for-name match |
| Components | 46 | **46** | PASS |
| Copper layers | 4, in order | Top / Mid1 / Mid2 / Bottom | PASS |
| **Board thickness** | **1.200 mm** | **0.142 mm** | **FAIL** |
| **Dielectrics** | 3 (prepreg/core/prepreg) | **none — "No Dielectric", height 0** | **FAIL** |

**The stackup was dropped by the importer, not missing from the file** —
verified: the source carries `(stackup ...)` with all three dielectrics summing
to 1.200 mm. Altium kept the copper layers and discarded the dielectric between
them.

`Un0` / `Un1` are the two NPTH mounting holes, which carry no reference in
KiCad; the importer auto-named them and said so in its log. Expected, not a
fault.

## Before any Altium DRC result means anything

1. **Set the board thickness** — Design ▸ Layer Stack Manager, 1.2 mm total.
   Nothing thickness-dependent (3D, via aspect ratio, impedance) is valid until
   this is done.
2. **Repour the polygons** — this file's zones are unfilled by design, so GND
   will read as unconnected until Altium pours it.
3. **Set the rules** to the table in section 3 above. Altium's defaults are
   ~0.254 mm clearance and would flag this whole board.

**Do not read a DRC taken before those three steps.**
