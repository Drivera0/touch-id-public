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

---

## 2026-08-29 (later) — the pogo-via finding

> [!error] **`pcb-v3-handoff.kicad_pcb` — the board priced at $115.38 and
> waiting only on U1 — has TWO VIAS DRILLED THROUGH J11's POGO CONTACTS.**
> `(2.95,-4.05)` 0.580 mm into J11.3, and `(2.40,-7.00)` 0.331 mm into J11.1.
> This is pre-existing. It is not caused by the PCM work.

J4/J11 are the pads the keyboard's sprung pogo pins press against. A
through-hole via there exits the underside **in the middle of the contact
face**: the pad stops being a contact. The rule is old and documented, and
`gnd_taps.py` has refused to place such a via since it was written.

**Why it got through:** the rule lived in our *scripts*, not in the *board* and
not in the *gate*.

* the **router** was never told, so it placed them;
* **`stitch_open.py`** was never told either — it welded `GND J4.5` with a via
  **0.382 mm inside J4.5's own pad** (fixed today);
* **`preflight.py` had no check for it at all**, so the order gate passed a
  board with two holes through keyboard contacts.

**Now: `preflight` check 22 — "no via pierces a pogo contact".** It fails both
the current board and the ordered one.

### The fix is not obvious, and three attempts failed

| attempt | result |
|---|---|
| board-level no-via rule areas over all 10 pogo pads | routing collapses: open pads 8 → 12, untapped GND 7 → 17 |
| delete the two vias, re-stitch | 8 → 10 opens: the vias were load-bearing |
| rip BL_RETURN + HARV_1, re-route with the rule applied | router fails all 4 connections |

The minimum legal keep-out radius is **1.45 mm** (pad 1.10 + via pad 0.25 +
clearance 0.10). Ten Ø2.2 pads with 1.45 mm no-via rings remove enough of the
board that the router cannot work.

**So this is a real design problem, not a tooling gap:** `BL_RETURN` and
`HARV_1` terminate on J11 pads, which are **B.Cu**. Reaching them from F.Cu
needs a layer change, the layer change needs a via, and there is nowhere legal
to put one in the congestion around J11.

**The likely answer is to route those two nets on B.Cu for their whole length**
so no transition is needed near the pogo block — which is a placement/topology
change, not a router setting. Not attempted yet.

### Current state

| | |
|---|---|
| blockers | **3** — 8 open pads, GND connectivity, 2 pogo vias |
| DRC | clean |
| antenna keep-out | clear, and holds through a KiCad round-trip |
| U5 + R8/R9/C14 | placed, netlist matches (134 pins), BOM sourced |

---

## 2026-08-29 (end of session) — where v4 actually stands

### Passing, and holding through a KiCad round-trip

| check | |
|---|---|
| 2 copper clearance | PASS |
| 4 netlist ↔ board | **PASS — 134 pins**, U5 + R8/R9/C14 + `CELL_NEG` all correct |
| 5 dangling nets | PASS |
| 6b router DRC @ 0.10 | PASS |
| 7 antenna keep-out | PASS |
| 18 zones filled | PASS |
| 20 dangling track ends | PASS |
| 21 every part sourced | PASS |
| **22 no via pierces a pogo contact** | **PASS** (new check; the pre-PCM board fails it) |

### The 2 remaining blockers

**6 — 10 open pads. Half of them are in one place:**

| region | opens |
|---|---|
| **left strip** | **5** — U3 ×2, C5, R9, U4 |
| right strip | 2 — U2, ROV1 |
| module / SWD / sensor pads | 3 — U1, J3, J2 |

**17 — GND not fully connected** (5 of the above are GND pads).

### The diagnosis: the left strip is over-subscribed

It is **2.72 mm wide** and carries **U3, U4, C5, C12, R9 and C14** — including
two TPS7A2033 in X2SON-4, whose pads are **0.34–0.40 mm apart** when a 0.127
track needs 0.327 to pass between them. Every routing attempt today, under six
router configurations and three placement strategies, has failed in that strip.

This is a **placement** problem, not a routing one. No router setting fixes a
2.72 mm channel with two fine-pitch QFNs in it.

### `stitch_open` reports connections it did not make

It reported `ROUTED` for GND ROV1.2, U3.5 and J3.5; `check_connected` — which
models the zone fill and is preflight's gate — still reports all three open,
and the pad list is byte-identical before and after. ROV1 got "4 seg, **0
via**": F.Cu track ending in free space, and GND's plane is on In2.Cu, which no
F.Cu track reaches without a via. `own_copper()` also still uses the
`max(w,h)/2` box for custom pads — the fourth instance of that trap.
**Do not trust stitch's ROUTED count; re-check with preflight.**

### What to do next, in order

1. **MEASURE THE SLOT DEPTH.** Still unmeasured, still the highest-value
   unknown on the project. The module is 12.86 mm against the 8.36 mm knob it
   replaces. Everything below is wasted if that does not fit.
2. **Relieve the left strip.** The candidates are moving C12/C14 out of it, or
   revisiting whether U3 and U4 both need to be there. This is the change that
   would actually close the routing.
3. Fix `stitch_open`'s `own_copper` (custom pads + no via-less plane reach).
4. Re-derive the electrical claims that were never re-checked after the PCM
   went in: the VDDH 100 ms rise gate, harvest MPPT with the 1 kΩ series
   resistor, and `VBAT_OK` at 3.12 V against the PCM's 2.70 V backstop now
   that all return current flows through U5.

---

## check_drc IGNORES PAD ROTATION — do not trust check 6b alone

`py_router/check_drc.py` builds pad rectangles from `(size w h)` without
applying the pad's `(at x y ROT)`. On this board that is not academic: **twelve
of the twenty-two 0402s sit at rot 90**, where w and h swap.

It has now failed in **both directions on the same board**:

* **False negative.** A GND tap ran **0.0915 mm** from C9.1 (0.500 × 0.540 at
  rot 90) against a 0.10 rule. `check_drc`: *NO DRC VIOLATIONS FOUND*. It
  modelled the pad 0.250 wide in X where the copper is 0.270 — exactly the
  0.020 per side it dropped. `check_board.py` caught it.
* **False positive.** One VSTOR segment reported as overlapping **six** pads by
  0.014 mm each. Same cause, other axis: it used h/2 = 0.270 in Y where the
  rotated pad is w/2 = 0.250. Hand arithmetic gives a **0.1065 mm** gap against
  a 0.10 rule — a pass with margin.

**`check_board.py` is authoritative for clearance.** It parses with shapely and
applies `affinity.rotate`, so rotated and roundrect pads are modelled as drawn.
`check_drc` remains useful for what `check_board` does not cover — via sizes,
board-edge, hole-to-hole — but its pad-clearance verdicts are unreliable on any
board with rotated passives.

**preflight check 6b wraps check_drc, so 6b inherits this.** When 6b and
check 2 disagree, check 2 wins. Verify by hand before acting on either.

### The matching bug in our own scripts, now fixed

`gnd_taps.py` and `stitch_open.py` classified pads with
`abs(rot % 90) > 1e-6` — which catches 45° and **passes 90° straight through**
to a fallback box built from the *unrotated* w and h. That is what let the tap
sit 0.0915 mm from C9.1 in the first place. Both now swap w/h when
`round(rot) % 180 == 90`. Re-running the taps with the fix: **0 clearance
violations**, where the same step previously produced one.
