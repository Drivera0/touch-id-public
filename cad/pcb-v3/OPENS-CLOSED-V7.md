# OPENS CLOSED — pcb-v7-zero-opens.kicad_pcb (2026-08-31)

## UPDATE — after the first zone refill (same day)

The user's refill exposed what the stale fills had been hiding: the honest pour
strands GND pads. Three of the "blockers" it reported were bookkeeping, not
geometry — KiCad's save created a fresh `.kicad_pro` with default rules
(clearance 0.2, edge 0.5) and check_drc grades against the project file, so 589
"violations" appeared on copper that had not changed. `make_kicad_pro.py`
regenerated it from the fab floor (note: that tool writes the old key
`copper_edge_clearance`; KiCad 10 reads `min_copper_edge_clearance` — patched
by hand to 0.3). The remaining strandings were real, and were fixed thus:

* **3 island vias** re-placed by `island_via.py`: U3.2/U3.5/C10.2 island at
  (-8.036, 1.874), R9.2/U5.4 island at (8.045, -6.557), J4.5 island at
  (-6.576, -1.696).
* **U4.2/U4.5 island**: no legal via site exists (pin-hole no-via zone + the
  island is a 0.2-0.3 mm ribbon). Hand-laid a 0.45 mm GND stitch at x=-7.72,
  y 0.90→1.35, threading the 0.35 mm gap between U3.1 and U3.4; worst
  clearance on the stitch is 0.25 mm (a SENSOR_SW_EN via).
* **TP10.1**: unbondable where it was — the CELL_NEG and SENSOR_TX In1
  diagonals bracket the pad (no via can clear both) and a single HARV_1 B.Cu
  track at y=-6.80 rings the island against any stitch. It is a bare test pad
  with no routes, so it MOVED to (8.0, 6.7), inside the via-bonded top-right
  B.Cu pour, 0.8 mm clear of everything.
* **U1.32/U1.33 island** — the hard one. It is walled by the pogo no-via
  blanket (no via can sit between the J11 pads: 0.5 mm gap vs 0.6 mm needed)
  and, on every side, by routed copper. The fix is topological: PCM_VDD's
  C14.1 leg was re-routed as a single column at x≈3.3 through
  `U1_SOUTH_GND_ESCAPE` (that rule area is now **tracks allowed** — it was
  reserved to keep the GND escape open, and this change is what actually
  reopens the escape), approaching C14.1 from the south at y≈-8.1. That
  vacates the old channel at x2.45-3.0 entirely, leaving a verified ≥0.25 mm
  copper-free strip from the island's west side down to the GND wall at
  y=-8.55. **The pour bonds U1.32/U1.33 through this strip on the next
  refill** — a shapely simulation of the fill clearances confirms the path.

**Current preflight: 2 BLOCKERS, both U1.32/U1.33 pour-reach — both expected
to clear on the next zone refill.** Everything else passes.

### RESULT AFTER THE SECOND REFILL (2026-08-31)

22 checks PASS. The pour strip worked: **U1.32 is bonded.** The strip's price
was that the PCM column now runs between U1.32 and U1.33, and **U1.33 — the
final pad on the whole board — is stranded** in a cell walled by the PCM
column (W), the corridor elbow (N), the U1_PINCH rule area + U5 cluster (E),
the CELL_NEG feeder (S), and the pogo no-via blanket overhead. Exhaustive
search (close_open, all layers, via-to-plane) confirms NO legal bond exists.
Every alternative was worked through and each dies on hard geometry:
the column must run in one of two N-S slots, the pour needs both, and the
lane between VRDIV and U5.2's halo — the only E-W corridor in the south
half — holds exactly one track. Squeezes measured and lost: 4 μm short
between the GND wall and VRDIV, 22 μm short below C14.2.

**Why this may not matter:** U1.33 is one of the module's many GND
castellations; U1.32 — the same module-internal ground, 0.8 mm away — is
bonded, as are U1's other GND pads and the whole GND net (41 pads, now 2
pieces: main + U1.33 alone). Board-side, U1.33's bond adds only redundancy
and RF stitching. And **the pending cell decision can dissolve the problem
entirely**: if the protected LPM1254 is confirmed, U5/R8/C14 come off the
board, the PCM column and CELL_NEG feeder vanish, and U1.33 bonds trivially
on the next refill.

Resolution options: (a) accept U1.33 unbonded and order (override the gate's
verdict knowingly); (b) wait for the LiPol reply — protected cell confirmed
means the cluster is deleted and this heals itself; (c) move U5 south out of
the pogo shadow — a multi-part, multi-net cascade for a future session.

## RESOLUTION — LiPol confirmed, cluster deleted (2026-08-31, same day)

Option (b) resolved itself within the hour: LiPol quoted the **LPM1254 80 mAh
with factory PCM and wires** (MOQ 5 @ [pricing redacted], 1-2 weeks,
assembled Ø12 × 6.7 — fits the as-built Ø14.00 pocket per the envelope
CELL-SOURCING already evaluated; max discharge **80 mA**, so the 30 mA fear
dies too). Executed per the handover's own plan:

* `netlist_v3.py`: **U5, R8, R9, C14 deleted**; BT1.2 is **GND** again; nets
  PCM_VDD / PCM_VM / CELL_NEG gone. Regenerated with `export_netlist.py`
  (44 parts, 27 nets).
* Board: 4 footprints removed; 80 segs of PCM_VDD/PCM_VM deleted; VBAT's
  east feed branch (38 segs + 1 via, it only served R8.1) deleted; the
  CELL_NEG chain **renamed to GND** (it becomes free ground stitching, and
  its via at (5.1,-7.0) is now a GND via in the pogo interior) with its two
  dead tails trimmed.
* **Every wall around U1.33 vanished with the cluster.** A real-rectangle
  clearance simulation shows 0.2-0.4 mm of pour room straight down x≈3.9
  from the U1.32/33 lobe to the GND wall at y-8.55.
* Bonus: **C6989585 leaves the BOM** — warning 21b now lists only U1's
  MDBT50Q. 29 placed designators, 19 LCSC codes.

Preflight: 22 PASS, and the only blocker is U1.33-vs-the-STALE-fill; the
pour-blind connectivity check reports **0 opens**. **One more KiCad refill
(B, save) and the gate is expected fully green.** The user — not a session —
places the LiPol order (vendor quote).

## GATE GREEN — 2026-08-31, after the third refill

**0 BLOCKERS. 0 open pads against the pour KiCad computed. GND fully
connected. VERDICT: "orderable once the warnings are accepted."** (commit
8f84fec). The three warnings are order-form actions, not board defects.
BOM/CPL regenerated for the 29-part board (`make_bom_cpl.py` was silently
hardcoded to the old handoff board — fixed to take an argument; the old
assembly package contained the four deleted parts).

Remaining before money: plot Gerbers from KiCad (none exist for 20×19; run
`verify_gerbers.py` + `verify_handoff.py` after), re-check U1 MDBT50Q stock,
place the LiPol cell order, and the order-form checkboxes (1.20 mm thickness,
0.40/0.20 via option, Confirm Parts Placement = Yes, depaneling).

---


**Both TRUE open pads from HANDOVER-OPEN-PADS.md are closed. Preflight: 0 BLOCKERS,
VERDICT "orderable once the warnings are accepted."** Board: `pcb-v7-zero-opens.kicad_pcb`
(built from `pcb-v6-handoff.kicad_pcb`; originals untouched).

## ONE STEP LEFT FOR YOU (required before plotting Gerbers)

Open `pcb-v7-zero-opens.kicad_pcb` in KiCad, **refill all zones (press B), save**,
then re-run `sexp_check.py` and `preflight.py`. The new tracks run through areas the
*stored* GND pour fills still occupy — the fills must be recomputed by KiCad or the
plotted Gerbers would short the pours into the new tracks. (The checkers compare
tracks/pads/vias, not stale fills, so preflight cannot see this; it is a known gap.)

## What was done, and why routing alone could not fix it

Both opens were placement problems, as the handover predicted.

**U5.2 (PCM_VDD)** — the R8.2/C14.1 island sat inside pogo no-via zone J11_1, walled on
F.Cu on every side. The decisive discovery: **two of the walls were PCM_VDD's own feeder
nets** (the VBAT descent at x2.6–2.8 and the CELL_NEG feeder at y-7.2). Fix:

* Deleted the dead VBAT feeder branch (8 segs) — this opened a north channel into the pocket.
* **R8 moved** from (2.85,-7.90) to **(8.35,-5.30) rot 90**, east of the pogo block, outside
  U1's body. R8.2 clears the PCM_VM trace by 0.14 mm and R9.1 by 0.15 mm — legal, but tight;
  expect JLC DFM to remark on the R8–R9 spacing.
* C14 stays at its original (3.65,-7.65); its CELL_NEG feeder was restored verbatim.
* PCM_VDD routed R8.2–U5.2–C14.1: 82 segments, all F.Cu (corridor y≈-5.4 + north channel).
* VBAT taps R8.1 from the via room above the east block (+1 via).

**R6.1 (BL_RETURN)** — R6 nudged from (0.15,-7.90) to **(0.20,-7.75) rot 90**. BL_FLAG
re-routed locally through the old fence gap; BL_RETURN routed from R6.1 to J11.4's
existing B.Cu stub via inner layers (+3 vias). Placement chosen by a reachability scan;
the west-strip candidate was tried first and rejected — R6.1's own route sealed R6.2.

Net copper change vs v6-handoff: segments 606→921, vias 90→94. Netlist untouched.
NOTE: R8/C14/R6 positions now diverge from `build_pcb_v3.py`'s placement table —
**the board file is authoritative**; regenerating from the script loses these fixes.

## Two tool defects found (for the next session)

1. **`stitch_open.py` is KiCad-10-dialect-blind**: it reads track nets through the v8 net
   table, sees zero nets on this file, and reports "nothing open" on a board with real opens.
   Same trap as HANDOVER item 2. Not fixed.
2. **`close_open.py` multi-target runs are self-blind**: obstacles come from the file, so a
   second target in the same invocation cannot see the first target's fresh copper. Running
   `R6.2 R6.1` together produced 41 clearance violations including a true short.
   **Run one target per invocation** (write, then re-invoke on the written file). Not fixed.

## Order-time items (unchanged from handover)

Via option 0.40/0.20 at checkout; thickness 1.20 mm (JLC defaults 4-layer to 1.6);
re-check stock of C5118826 (U1) and C6989585 (U5); Confirm Parts Placement = Yes;
no Gerbers exist yet — plot from KiCad after the refill step, then run
`verify_gerbers.py` / `verify_handoff.py`. The cell decision (protected LPM1254 vs bare)
is still open; if the protected cell is confirmed, U5/R8/C14 can come off the board
entirely, which also removes one zero-stock part.
