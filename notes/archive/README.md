---
title: Archive — superseded notes
type: project
---

# Archive

**Nothing in this folder is current. Do not take a number from here.**

These documents were correct when written and are kept for their reasoning, not
their figures. Every one of them contains dimensions or part numbers that have
since changed. If you want the current state, read **`CURRENT-STATE.md`** at the
vault root, and **`DESIGN-SPEC.md`** for the technical master.

| archived | was | superseded by | why |
|---|---|---|---|
| `NEXT-SESSION-2026-08-27.md` | the session entry point | `CURRENT-STATE.md` | riser 4.50, top face z 11.66, CP1254 as the cell, ZW0905 as the sensor, 2.26 mm above the cell — **all now wrong** |
| `HOUSING-V5-NOTES-2026-08-27.md` | housing v5 design note | `CURRENT-STATE.md` §housing | riser 4.50 → **6.50**, top face 11.66 → **13.66**, pocket Ø12.50 → **Ø14.00**, clearance 1.61 → **0.81 mm** |
| `PCM-SELECTION-2026-08-28.md` | picking a protection IC to fit inline | `CELL-DECIDED.md` | **its whole premise is dead** — the chosen cell (LiPol LPM1254) ships with a PCM already fitted, so there is no separate PCM to select |

## What is still worth reading in them

**`NEXT-SESSION-2026-08-27.md`** — the standing working rules it set out are
still in force and have been carried into `CURRENT-STATE.md`:

> Never invent a dimension, land pattern or part number · Do not order anything
> without being asked · Do not delete or overwrite originals · Commit at every
> milestone · Run the checkers before claiming anything works, `sexp_check.py`
> first · When blocked, leave a note and move on.

**`PCM-SELECTION-2026-08-28.md`** — the survey work is sound and would matter
again if the LiPol cell falls through and a bare cell has to be protected by
hand. It establishes that the on-board route is closed (largest free square on
the top layer is **0.9 mm** against a 1.3 mm minimum land) and that ready-made
PCM boards are all **2.2–3.0 mm** thick against 1.61 mm of space at the time.

**`HOUSING-V5-NOTES-2026-08-27.md`** — the *reasoning* for why the cell rests on
the MCU lid through a 0.20 mm insulating pad, rather than on ledges, is still
the live design and is not written down as clearly anywhere else.
