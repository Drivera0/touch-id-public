# OPENS CLOSED — pcb-v7-zero-opens.kicad_pcb (2026-08-31)

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
