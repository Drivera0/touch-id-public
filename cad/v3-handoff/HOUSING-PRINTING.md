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

## The mesh had a real defect — fixed at source, not in Fusion

The exported STL was **not watertight**: 2 **non-manifold edges**, each shared
by four faces instead of two, at `(0, ±8.385)` spanning `z 2.90 … 5.16`.

**There were no holes and no gaps** — 0 boundary edges, 1 closed body. What
looks like holes in a viewer is the deliberate geometry: the ±X wire windows,
the open back cavity, the sensor bore.

**Cause:** `collar_od` was `body_w - 2*wall_t` = **16.77**, which is *exactly*
the top-tier cavity width. The collar arc was therefore perfectly **tangent**
to the cavity wall, and the union joined two coincident surfaces along a line
rather than through a volume. The coordinates gave it away — 8.385 is
16.77 / 2, and 2.90 → 5.16 is exactly `collar_z0 → collar_z1`.

**Fix:** grow the arc 0.2 mm so the boolean has real overlap.

```
watertight            : True      (was False)
hole edges            : 0         (unchanged — there never were any)
non-manifold edges    : 0         (was 2)
volume                : 1111.44 mm³  (was 1101.53)
```

All eight boolean clearance checks still pass.

> **This was fixed in `touchid_module_v5.py`, deliberately not in Fusion.**
> The housing is *generated output* from a parametric CadQuery script. Patching
> the mesh by hand would have desynchronised the STL from its source, and the
> next run of the script would have silently reintroduced the defect.

**It is not a free change.** The cavity is rectangular and the collar is a
circular arc, so they only touch at ±Y; across the rest of the ±45° span the
extra radius adds material into open cavity, hence **+9.9 mm³**. It collides
with nothing — above the MCU, outside the unchanged Ø12.50 cell pocket — and
it happens to thicken the collar/wall junction, one of the places flagged thin
below.

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
  this is a taper artifact — any filleted edge reads thin locally.
* a **broad triangular region on the inner cavity wall at a corner.**

### The corner wall is 0.15 mm, and that is the real defect

Measured by ray-casting the mesh at the lip tier, z = 1.5:

| direction | wall |
|---|---|
| along −x (flat side) | **0.800 mm** |
| along −y (flat side) | 0.795 mm |
| **along the −45° corner diagonal** | **0.150 mm** |

The flat sides are exactly the intended `wall_t = 0.8`. **At the corners the
wall collapses to 0.15 mm** — a fifth of that, and deep inside JLC's red
(< 0.5 mm) band.

**Cause:** the outer lip is a **rounded** square (corner radius ≈ 2.38 mm pulls
the outside surface *inward* at each corner) while the inner cavity is a
**sharp** rectangle (its corner pokes *outward*). The two surfaces converge:
outer corner sits at d = 12.840 along the diagonal, inner cavity corner at
d = 12.690.

This is not a taper artifact and it is not local to one corner — it is **all
four**, by construction. It is also the honest explanation for JLC's red
heatmap regions, which I initially and wrongly put down to fillet tapering.

### The fix

**Fillet the cavity's inner corners.** Pulling the inner corner back restores
wall without touching `wall_t`, so it costs no cavity width on the flats where
U1 actually needs it:

> to reach 0.8 mm at the corner, the inner corner must move from 12.690 to
> 12.040 along the diagonal → a cavity corner radius of about **1.6 mm**.

Safe to do: U1 spans x −6.05…4.45, y −6.75…8.75, and its nearest corner is
~4.5 mm clear of the cavity corner at (8.98, 8.98), so a 1.6 mm corner fillet
cannot touch it. It also adds material around the M1.2 screw bosses at
(±8.10, ∓8.10), which sit on that same diagonal — so it reinforces the bosses
for free.

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
