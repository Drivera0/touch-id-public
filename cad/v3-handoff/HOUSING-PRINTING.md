---
title: TouchID v3 — printing the housing
type: project
---

# Printing the housing

Quoted 2026-08-28 on JLC3DP, from `housing/touchid_housing_v5_diagonal.stl`.

## The price is not the problem

| | |
|---|---|
| Material | **9600 Resin, white** (SLA) |
| Finish | Sanding — general |
| Qty 1 | **C$0.43** |
| **Qty 5** | **C$2.15** |
| Shipping | **C$2.08** (Global Standard Direct, 8–12 business days) |
| Build | 3 days |
| **Five housings, delivered** | **≈ C$4.23** |

Weight for 5 is 0.13 kg. If ordered alongside the PCB it shares that shipment
anyway. **This is cheaper than any on-campus option** once UBC's BioDevice
Foundry access fees ($300 startup, $40/month) are counted — their SLA machine
time is only $4/hr, but the access model is built for regular users, not a
one-off 20 mm part.

Resin is the right process regardless: the sensor window is **Ø15.60 for a
Ø15.50 barrel — 0.10 mm diametral clearance** — which FDM cannot hold.

## The model is confirmed correct

JLC's viewer independently measured **volume 1101.53 mm³** against the
**1101.56 mm³** `touchid_module_v5.py` computes. Bounding box 11.66 × 22.11 ×
23.29 mm — the 11.66 is `top_h` exactly; the other two include the retention
tab and the mounting arm, which project past the 19.54 lip.

## BUT: JLC's DFM flags thin walls, and it is right

> **"Thin walls detected. There may be a risk of deformation or damage. Are you
> willing to accept these risks and proceed?"**

JLC3DP's stated limits are **wall > 1.2 mm, thinnest part > 0.8 mm**. Their
heatmap bands are: white > 1.2 mm, **yellow 0.5–1.2 mm, red < 0.5 mm.**

**The entire square body reads yellow.** That is expected and known — `wall_t`
is **0.8 mm**, chosen deliberately because thinning the lip wall widened the
cavity from 16.74 to 17.94 mm and is *"what makes either mode work."* The
script's own comment already says 0.8 is *"comfortable for moulding, thin for
FDM."* JLC now says it is thin for resin too.

**More seriously, parts read RED — under 0.5 mm**, below JLC's own minimum:

* a **band along the top rim**, where the wall meets the outer chamfer. Some of
  this is a taper artifact — any filleted edge reads thin locally — so discount
  it.
* a **broad triangular region on the inner cavity wall at a corner.** This one
  is *not* a taper artifact; it is a flat area of genuinely thin material, and
  it sits where the **M1.2 screw boss** is flattened on its inner face
  (`boss_flat_x`, `boss_r = 1.20` at `boss_c = ±8.10`). That is a load-bearing
  corner — the PCB screws into it.

### What this means

Nothing here blocks a print. JLC will build it if you accept the risk, and at
C$2.15 for five the cheapest test is simply to order them and see.

But **do not treat the first print as flight hardware.** Check specifically
whether the screw boss corner survives being screwed into, because that is
where the model is thinnest and where the load is.

**None of our own housing checks would ever have caught this.**
`touchid_module_v5.py` verifies eight boolean intersections — housing ∩ MCU,
∩ sensor, ∩ cell, cell ∩ bosses and so on — all of which ask *"do two solids
overlap?"*. Not one of them asks *"is this wall thick enough to survive?"*
Wall thickness was outside the whole family of checks, exactly like board
thickness and zone fills were on the PCB side. An external tool found it.

### If it does fail

The fix is not obvious, because 0.8 mm was chosen to buy cavity width. Options,
in order of least disruption:

1. Print in a tougher resin than the default 9600 and re-test.
2. Add a local fillet or gusset **only at the boss corners**, which costs no
   cavity width anywhere else.
3. Thicken `wall_t` and re-check that U1 (10.5 × 15.5) still fits the cavity —
   this is the one that risks unpicking the whole layout, so try 1 and 2 first.
