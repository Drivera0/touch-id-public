---
title: Superseded by v6 — DO NOT TOUCH
type: project
archived: 2026-08-30
---

# Everything in this folder is DEAD. Do not build from it.

It is kept only for its reasoning and its git history. **Do not take a number,
a Gerber, a part choice or a dimension from anything in here.** If you need a
figure, get it from the live files listed at the bottom.

## Why it was archived

The board changed shape and fixings, and then two order-blocking defects were
found in the old revision.

| | old (here) | live (v6) |
|---|---|---|
| outline | **19.30 mm square** | **20.00 × 19.00 mm** (20 horizontal) |
| fixings | screws at the **corners** | **Ø1.20 press-fit pins** at (±8.75, 0) |
| OK divider | 4.53M / 7.15M / 1.33M, 0402 | **4.3M / 6.8M / 1.33M, 0201** |
| 1k group R1/R2/R3/R7 | 0402 | **0201** |
| open pads | 2 at best | **0** |

## The two defects these files contain

1. **Both press-fit pins are drilled through copper.** L1 pad 2 sits 0.288 mm
   inside the right hole; U4 pad 2 0.120 mm inside the left. Every board in
   `boards/` has this, including `pcb-v5-routed-wip.kicad_pcb`, which was being
   treated as the best result. **These boards cannot be manufactured.**
2. **Two vias break JLCPCB's *pad* hole-to-hole rule** (0.45 mm — different from
   the 0.20 mm *via* rule) by 26 and 9 microns.

Neither shows up in a copper-clearance or DRC report, which is why they
survived so long. `build_pcb_v3.py check()` and `preflight` checks 23 / 23b now
catch both.

## What is in here

* `boards/` — every superseded `.kicad_pcb`, v3 through the v6 work-in-progress.
* `v3-handoff-pkg/` — the **complete fab package for the 19.30 mm square
  board**: Gerbers, BOM, CPL, reports, housing STL and the two upload zips.
  This is the most dangerous folder in the project, because it looks finished
  and it is wrong for the board that now exists. **Do not order from it.**

## Live files to use instead

| | |
|---|---|
| board | `cad/pcb-v3/pcb-v6-handoff.kicad_pcb` |
| generator | `cad/pcb-v3/build_pcb_v3.py` → writes `pcb-v6.kicad_pcb` |
| status | `CURRENT-STATE.md` |
| technical master | `DESIGN-SPEC.md` |

`pcb-v2.kicad_pcb` and `touchid_module_v4.py` are NOT in here. They are
protected originals and stay where they are, untouched, by standing rule.
