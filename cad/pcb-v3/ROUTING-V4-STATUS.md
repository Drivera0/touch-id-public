---
title: pcb-v4 (PCM on board) — placement DONE, routing NOT DONE
type: project
updated: 2026-08-29
---

# Where the PCM board actually stands

## Placement — done, and it verifies

`build_pcb_v3.py` now places U5 + R8/R9/C14 and the board builds clean:

| | |
|---|---|
| U5 (MC3651) | **(−6.35, −7.90) rot 0**, S1 **2.28 mm** from BT1-2 |
| R8 / R9 / C14 | 0201, at 4.77 / 7.20 / 7.62 mm from U5 |
| 0402 packer | 22/22 placed |
| pads | 143 |
| **preflight check 4** | **PASS — 134 pins matched, netlist ↔ board agree** |
| preflight check 5 | PASS — no dangling nets |

Check 4 passing is the important one: U5's four pins, the three 0201s, and
`BT1-2 → CELL_NEG` are all on the board and match `netlist_v3.py`. Pad 5 (the
FET drain) correctly carries no net.

## Routing — NOT done

Best result so far (`pcb-v4-routed-wip.kicad_pcb`): router `inside_out`
backward + `stitch_open`, leaving **4 pads with NO PATH**:

* `BL_RETURN` R6.1
* `PCM_VDD` R8.2  ← one of ours
* `VBAT` U2.18
* `VBAT_OK` U2.13

`handroute.py` fails on all four too, **even after fixing its stale rules** —
it hardcodes `TRACK, CLR = 0.20, 0.20` while this board moved to 0.127/0.10,
which `stitch_open.py`'s own docstring already warned about. Correcting it did
not rescue these four, so they are genuinely walled in, not a rules artefact.

Also open: **4 copper-clearance violations** (preflight check 2).

## What is NOT measurable in the sandbox

**The In2.Cu ground zone has no fill geometry, and nothing here can fill it** —
there is no KiCad and no `kicad-cli` in the sandbox. Until the zone is filled
(KiCad → Edit → **Fill All Zones (B)** → Save) every GND pad reads as
disconnected, so the "16 true open pads" figure is inflated. **The 4 NO-PATH
pads above are the real number**; the rest is contamination.

## Two instruments that mislead here — do not repeat

1. **`check_connect.py` ignores zone fill.** It reports **19 NET(S) SPLIT on
   the already-ordered handoff board**. Running it on an unfilled board and
   comparing to a filled one is meaningless. `preflight.py` check 6
   ("TRUE open pads") is the metric; check 17 uses `check_connected`, which
   models the fill.
2. **`handroute.py` routes at 0.20/0.20** — 57 % wider than this board's rule.
   Any "no path" it reports is suspect until that is patched. The fix is not
   committed upstream; it was patched in a scratch copy only.

## Shelf phase: tie-break toward −7.90

The phase search finds 26 slots at both −7.30 and −7.90. Taking −7.30 moved
every 0402 off the arrangement that had already routed, and the re-route came
back with **six** walled-in pads instead of four. Ties now resolve toward
−7.90. A free parameter with no measured benefit should not be spent moving
away from working evidence.

## Next

1. Fill zones in KiCad, save, re-run `preflight.py` — get the true open count.
2. Attack the 4 NO-PATH pads. Three are U2/R6 congestion, which
   `ROUTING-RESULT.md` already identified as this board's hard spot (U2 is a
   0.5 mm-pitch QFN with 0.26 mm pad gaps in a 4.32 mm strip). `PCM_VDD` R8.2
   is ours and may respond to nudging R8.
3. Fix the 4 clearance violations.
4. If it will not converge, the BLE-module swap is back on the table — but on
   *routing corridor* evidence, which is what this exercise was for.
