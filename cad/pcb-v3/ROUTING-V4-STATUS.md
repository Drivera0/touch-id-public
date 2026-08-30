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


---

## 2026-08-29 (end of day) — where v4 stands

### Passing, and stable across several KiCad round-trips

| check | |
|---|---|
| 2 copper clearance | **PASS** — 0 violating pairs |
| 4 netlist ↔ board | **PASS** — 134 pins, U5 + R8/R9/C14 + `CELL_NEG` all correct |
| 5 dangling nets | PASS |
| 7 antenna keep-out | **PASS** — held through five fills |
| 18 zones filled | PASS — In2.Cu, and new F.Cu / B.Cu pours |
| 20 dangling track ends | PASS |
| 21 every part sourced | PASS — 24 LCSC codes |
| **22 no via pierces a pogo contact** | **PASS** — 80 vias vs 10 pads |

### 2 real blockers

**6 — 7 open pads.** Down from 16 at the start of the day.

| pad | net | why |
|---|---|---|
| C3.2, C9.2 | GND | **no legal via site within 3.5 mm.** Mid-shelf on the bottom row, 0402 neighbours 0.74 mm each side; a 0.45 via + 0.10 clearance does not fit between them. Geometry, not search. |
| C12.2, C5.2 | GND | sites exist at **1.65 / 2.15 mm**, but `gnd_taps`' A* cannot route a track that far through the congestion |
| U4.2 | GND | site exists 0.90 mm away, same problem |
| U2.18, U2.19 | VBAT, VSTOR | the 0.5 mm-pitch QFN escape problem, older than the PCM work |

**17 — GND not fully connected**, which is the same five GND pads.

### 6b is a FALSE POSITIVE — do not chase it

`check_drc` ignores pad rotation and twelve 0402s here are at rot 90. Its six
"violations" are one VSTOR segment against six pads, each off by 0.014 mm,
which is exactly the w/h swap. `check_board` — shapely, rotation-aware — says
**0**, and the hand arithmetic gives 0.1065 mm against a 0.10 rule. **Check 2
is authoritative.**

### What NOT to do next: hand-place taps

I tried it and produced three faults in one commit — two vias **0.502 and
0.614 mm inside J4.5's pogo contact**, and one track **shorting GND to
SENSOR_MCU_3V3 at 0.0000 mm**. The via sites were individually legal; I
validated where copper would END and never asked what the path CROSSED.
`gnd_taps` and `stitch_open` both run an A* that treats every foreign object as
an obstacle along the whole route. Do not substitute a straight line for that.

Also note the site search must exclude **J4/J11 even though J4.5 is itself
GND** — the rule is about the hole ruining a contact face, not clearance.
Skipping GND pads as blockers is correct for clearance and wrong for pogo.

### The real next step

Improve `gnd_taps`' path search so it can reach sites 1.65–2.15 mm away
through congestion — it already has the correct obstacle model, the pogo rule
and the A*. That is a change to one script with a clear success test
(`taps placed` goes up, check 2 and check 22 stay clean), not more copper
placed by hand.

---

## ROOT CAUSE of the stranded GND pads — found by looking, not theorising

Dumping every pad, track and via within 2 mm of C5.2 answered in one pass what
three hypotheses had failed to:

```
C5.2   at (-6.910,-1.920)   nearest pogo J4.5 at 0.417 mm   ring 1.425  -> INSIDE
C12.2  at (-7.780,-3.050)   nearest pogo J4.5 at 1.013 mm   ring 1.425  -> INSIDE
C3.2   at (-1.400,-8.320)   nearest pogo J4.2 at 3.479 mm               -> outside
C9.2   at ( 1.300,-8.320)   nearest pogo J11.1 at 2.424 mm              -> outside
U4.2   at (-8.040, 0.075)   nearest pogo J4.5 at 2.444 mm               -> outside
```

**C5 and C12 are placed on top of the J4 pogo block.** Their GND pads sit
inside J4.5's no-via ring (pogo pad 1.10 + via 0.225 + clearance 0.10 =
**1.425 mm**), so **no via can ever be placed near them** — not by `gnd_taps`,
not by stitching, not by hand. There were no vias at all within 2 mm of C5.2.

And a GND pad on **F.Cu** with no via cannot reach a plane on **In2.Cu**. The
pour cannot rescue it either: a pour island there would need its own via.

This is why the last three fixes did nothing:

| attempt | why it could not have worked |
|---|---|
| relax `gnd_taps`' via search | the sites it rejected were inside J4.5 — it was right |
| pour clearance 0.25 → 0.10 | a pour still needs a via to reach the plane |
| 50 stitching vias | none could be placed in the forbidden ring either |

### The fix is PLACEMENT, and it belongs in build_pcb_v3.py

The 0402 packer treats the pogo zone as *legal but expensive* — parts land
there once every other slot is taken. That was reasoned about **routing**
(`_POGO_ZONE`'s comment is about via access for the part's own escape) but the
consequence for a part with a **GND pad** was never drawn: it cannot be tapped,
so its ground pin is stranded no matter how the board is routed afterwards.

**Proposed rule: a pad on GND may not be placed inside a pogo no-via ring.**
Cheap to state, and it is a placement-time constraint rather than another
routing patch. C5 (0603, cell bulk cap) and C12 would move; both have
alternatives elsewhere on the left strip.

C3.2, C9.2 and U4.2 are a separate, ordinary crowding problem and are not
affected by this rule.

---

## The C5 fix is right, and it exposed a deeper one: U5 sits in the pogo block

**C5 is fixed and that part is settled.** As an 0603 there was exactly ONE
position on the whole board with both pads clear of every pogo ring, and it was
inside the antenna keep-out, which forbids pads. So C5 became the **same 0402
part as C1/C2** (`C77000`, 10 uF 10 V) and now goes through the packer, which
bans GND pads from pogo rings. 10 V is ample against a 4.30 V cell, and with
BT1 itself on VBAT the cell dominates the bulk impedance — C5 is there for
switching transients, not storage. One fewer distinct LCSC code, too.

**But it cascaded, and the cascade is informative.** Freeing C5 into the 0402
pool changed the packing, R9 lost the near-U5 spot it had been getting by luck,
and `PCM_VM` came back with no copper.

Chasing that turned up the real problem:

```
U5 centre (-6.35,-7.90)      U5.3 (V-) at (-5.10,-7.45)
J4.2      (-4.70,-7.22)      0.461 mm from U5.3   <-- INSIDE its no-via ring
U5.4 (S2, GND)                1.128 mm from a pogo pad
```

**U5 is placed inside the J4 pogo block.** Its own ground pin is in a ring, and
so is the area beside its V- pin. R9 is 2.7k from `PCM_VM` to **GND** — it
carries a GND pad, so the new rule correctly bans it from every ring, which
means it cannot be placed beside the pin it connects to. Reordering and
re-targeting the objective (to the PIN rather than the part centre, which was
itself a real fix) only move R9 around the outside of the ban.

This is not a routing problem and not a packer problem. **U5's own position is
the constraint**, and it was chosen by a single objective: minimise
`S1 -> BT1-2`, which drove it to the bottom-left corner — straight into J4.

### What that means for the next session

`U5`'s placement search needs a second term. Minimising the cell path is right,
but it must also keep **U5.4 (S2, GND) out of every pogo ring** and leave a
legal 0201 site beside **U5.3** for R9. Both are cheap to test inside the
existing trial loop, which already rejects candidates that starve the packer.

**The board currently in the vault predates all of today's build-script
changes** (C5 as 0402, the GND/pogo ban, the pin-targeted 0201 objective). It
is the 7-open-pad revision with every other check passing. Regenerating from
the current script is not worth doing until U5's placement question above is
settled, because the result would be worse: `PCM_VM` unrouted.

---

## FINAL STATE, end of 2026-08-29

### 2 blockers — the fewest reached, down from 5

| check | |
|---|---|
| 2 copper clearance | **PASS** 0 violating pairs |
| 4 netlist ↔ board | **PASS** 134 pins — U5, R8/R9/C14, `CELL_NEG` all correct |
| 5 dangling nets | PASS |
| 6b router DRC @ 0.10 | **PASS** clean |
| 7 antenna keep-out | **PASS** 0 objects inside |
| 18 zones filled | PASS — In2.Cu, F.Cu, B.Cu |
| 20 dangling track ends | **PASS** 1392 ends, all landed |
| 21 every part sourced | PASS 23 LCSC codes |
| 22 no via pierces a pogo contact | **PASS** 101 vias vs 10 pads |
| **6** | **BLOCKER — 8 open pads** |
| **17** | **BLOCKER — GND, the same pads** |

### The 8, and what each needs

| pad | net | |
|---|---|---|
| U2.18, U2.19 | VBAT, VSTOR | the 0.5 mm-pitch QFN escape. Predates the PCM work; `ROUTING-RESULT.md` named it in August |
| J4.5 | GND | the pogo pad itself, on B.Cu. The B.Cu pour should reach it — worth checking why it does not |
| R9.2, U3.x, U4.x | GND | left strip. `stitch_open` "routed" three of these with 0.10–0.24 mm tracks and the count did not move: **those stitches connect nothing** |

### Do not trust a short stitch

`stitch_open` reported `ROUTED 1 seg, 0 via, 0.10 mm` for U4.2, U4.5 and U3.2
and all three are still open. A sub-0.25 mm track with no via is almost always
a stitch to copper that is not actually on the net's connected island. **Check
the count moved before believing a stitch.** Its ROUTED tally is not evidence —
this is the second distinct way that script has misreported today.

### Where the effort should go next

1. **J4.5** first — it is one pad, on the B.Cu pour, on the net that matters
   most, and "the pour does not reach a same-net pad" is a bounded question.
2. **U2** next, and it is a placement question, not a routing one: 20 pins at
   0.5 mm pitch inside a 4.32 mm strip leaves ~0.21 mm of escape ring per side.
3. The left-strip GND pads last — they are the least critical of the three and
   the most entangled with everything else.

---

## STOP POINT — the last round of "correct" rules made the board worse

Two rules were added that are defensible in isolation and bad in combination:

* the **0201 placer** now honours the pogo ring for GND pads (R9 carries one)
* **U5's V-** must clear every ring by 0.30 mm

Each fixes a real thing. Together they pushed U5 to 3.39 mm from the cell pad,
R9 13.3 mm from U5, and the rebuild came out at **15 open pads, 5 dangling
ends and a DRC violation** — against **8 open pads and everything else clean**
on the board already in the vault.

**Both changes are reverted.** `build_pcb_v3.py` is back to the revision that
produced the good board. The rules are recorded here rather than in the script,
because re-adding them needs the U5 objective reworked at the same time, not
bolted on:

> R9 is 2.7k from `PCM_VM` to **GND**. Banning it from pogo rings is correct,
> but U5 must then be placed somewhere its V- pin has a ring-free neighbourhood
> AND its S1 stays near BT1-2 AND the packer still fits 23 passives. That is a
> four-way constraint and the current search optimises one term with two
> rejections bolted on. It wants a proper cost function, not another `continue`.

### What actually shipped today

The board in the vault is the best artifact produced:

| | |
|---|---|
| open pads | **8**, from 16 |
| clearance, netlist, DRC, antenna, dangling ends, sourcing, pogo vias | **all PASS** |
| J4.5 | **connected**, by the anchor-via technique |

`gnd_via_anchor.py` is committed and is the one tool from today worth reusing:
it places a via and no track, so it has no path to get wrong, and its legality
predicate carries every trap this board produced — pogo rings including J4.5,
the keep-out grown by the via radius, rotated pads, all-layer tracks,
hole-to-hole, and the R2.0 corners.

Its verdict on the current board: **all 41 GND pads already have a via within
2.5 mm.** So the remaining opens are not a via-proximity problem. They are pour
CONNECTIVITY, and the authority on that is KiCad's own DRC, which has never
been consulted. **Run it before any more surgery.**

---

## The eight open pads, diagnosed against the pour KiCad actually computed

The connectivity numbers we had been working from came from `check_connected`,
which does not read the fill geometry in the file -- it builds a MODEL of where
fill could go. `pour_truth.py` now reads the real `(filled_polygon ...)` blocks
KiCad writes when you fill zones, and does union-find over pads, vias, tracks
and each polygon.

**Both methods name the same eight pads.** They are real, not an artifact.

### What the pour actually looks like

The F.Cu GND fill is **15 separate islands**, and four of them contain no via:

| island | area | holds |
|---|---|---|
| 4 | 0.931 mm2 | U4.2, U4.5 |
| 10 | 3.157 mm2 | C7.2 |
| 13 | 0.402 mm2 | R9.2 |
| 14 | 0.387 mm2 | U5.4 |

This kills the theory `gnd_via_anchor` was built on. It asked "is there a via
within 2.5 mm of this GND pad?" and got yes for all 41. Wrong question. Copper
does not care about distance, it cares about which PIECE of copper it is. A via
1 mm away in a neighbouring island does nothing.

### Why each remaining pad is open -- measured, not guessed

**R9.2 and U5.4 -- the island is physically too narrow.** Widest point in
island 13 is **0.215 mm** from an edge and in island 14 **0.207 mm**. A 0.45 mm
via needs 0.225 mm. Short by 10 and 18 microns.

**C7.2 -- trapped inside a pogo ring.** Island 10 lies wholly within 1.425 mm
of **J11.2**, which is `HARV_2`, a live net. Every one of the 2740 candidate
via sites is inside that ring. A route out exists but its only via site is
0.025 mm inside the board-edge rule.

**U4.2 and U4.5 -- sealed in a 1.15 x 1.50 mm pocket** with **zero** legal via
sites reachable. Not boxed in at the pad (129 of 169 cells free) -- boxed in
by the pocket.

**U2.18 (VBAT) and U2.19 (VSTOR) -- the QFN escape.** Reachable region is the
pin row itself, **3.10 x 0.90 mm, no via site anywhere in it**. Pins sit on a
0.5 mm pitch with 0.24 mm pads, so the gap between neighbours is 0.26 mm and a
0.127 track needs 0.327 mm. There is no way between the pins and no way down.

### The conclusion that matters

**These six are placement problems, not routing problems.** No router will
close them, because the copper they need to reach is not reachable from where
the parts sit. Closing them means moving U2, U4, R9, U5 and C7 -- or accepting
a finer fab rung.

### What was closed

`close_open.py` closed **SENSOR_SW_EN (U4.3)**, which was never routed at all
(one 0.106 mm stub off U1.19). 8 open pads -> **7**. Clearance 0, router DRC
clean, pogo vias clear, no dangling ends.

### Tools written, and what each got wrong first

* `pour_truth.py` -- reads the real pour. First run reported 34 opens because
  KiCad 10 writes the zone net inline as `(net "GND")` and it looked for
  `net_name`. Now hard-fails on an unreadable zone net rather than failing soft.
* `close_open.py` -- routes ONE open pad to its net's existing copper. Four
  false starts, each caught by making it check its own work: it aimed only at
  pads (so GND ignored 212 mm2 of plane sitting under it); it placed two vias
  0.427 mm apart; it "closed" U4.2 with zero segments by landing on stranded
  copper; and it put a via 0.025 mm inside the board edge. It now self-verifies
  by re-reading the file it wrote.
* `island_via.py` -- proves no via fits in islands 4/10/13/14 and says why.

### handroute.py was broken in three ways on this board

Found while porting it, all silent failures:

1. **KiCad 10 net dialect** -- every net regex assumed the KiCad 8 table, so
   every pad and track read as net `""` and `emit()` would have written the
   literal `(net None)` into the board.
2. **Rotated pads were skipped entirely** -- the pad regex demanded `(at X Y)`
   with exactly two numbers, so `(at 0 0 45)` failed and hit `continue`. That
   hid **U3.5 and U4.5**, the X2SON thermal pads, from the obstacle map. The
   router was free to route straight through them.
3. **Mounting holes were skipped** -- written `(pad "" np_thru_hole circle)`
   with an empty pad number, and the regex required one character. Two 1.3 mm
   holes it could route through.

Plus a board-edge band computed with `TRACK/2` for every mask, giving vias a
track-sized margin. Obstacle map now sees 145/145 pads, matching `pour_truth`
independently.

---

## U4.2 and U4.5 closed by moving ONE track (7 -> 5)

Island 4 -- the 0.931 mm2 scrap of F.Cu GND holding U4.2 and U4.5 -- had no
legal via site, and the diagnostic named a single cause: every candidate was
blocked by **one In1.Cu SENSOR_3V3 segment** running diagonally underneath.
The F.Cu island shape was never the problem; the island is fine. A through via
pierces In1.Cu, and that is where the track was.

Rerouting the whole SENSOR_3V3 net is not available: `handroute` cannot rebuild
it at all (it fails with "no path to U3.1"), and the CONTROL confirmed that
failure is nothing to do with the keep-out being added -- the net simply cannot
be re-created in the current congestion.

So only the offending segment was moved:

    was   (-7.250,-1.150) -> (-9.000, 0.600)   2.47 mm diagonal, straight
                                               through the island
    now   a detour around it, 7.80 mm, 2 vias

**Kept at the full 0.400 mm width.** SENSOR_3V3 is the sensor supply, and
quietly re-laying a power net at the 0.127 mm signal width to make it fit would
have been a real electrical change disguised as a routing fix. The extra 5.3 mm
at 0.4 mm wide on 1 oz copper is about **6.5 mOhm** -- roughly 1.3 mV at
200 mA, against a 25 mV budget. Check 10 still reports 1.2 mV.

Then one GND via in the freed island connects both pads.

Result: **5 open pads**, clearance 0, router DRC clean, pogo contacts clear, no
dangling ends, IR drop unchanged.

### The five that remain are still placement problems

R9.2 and U5.4 (islands 10 and 18 microns too narrow), C7.2 (island wholly
inside J11.2's pogo ring, and its one route out needs a via 0.025 mm inside the
board-edge rule), and U2.18/U2.19 (no via site anywhere in the QFN pin row).
Nothing about the U4 fix generalises to them -- U4's blocker was removable
copper on another layer, theirs is the position of the parts themselves.

---

## The last five: one decision, not five problems

`CELL_NEG` was tried and DISCARDED. The wall boxing U2's pin row was 190 cells
of a single 0.300 mm `CELL_NEG` track crossing at y = -0.500, which looked like
the U4 fix all over again. Detouring it (same length, 3 vias) did widen the
corridor from 0.90 mm to 1.50 mm tall -- and still produced **zero** via sites.
The wall is now the pads themselves: U2's own neighbours plus **L1**, the
inductor sitting immediately north. Nothing was kept.

C7.2 is worse than it first looked. It can reach 9 legal via sites, but **none
of them sit over connected ground copper** -- and that holds on B.Cu too,
because the J11 pogo pads void the bottom pour right there.

### What actually decides all five: via size

| pad | standard 0.45/0.20 | advanced 0.25/0.15 |
|---|---|---|
| R9.2 | island half-width 0.215 mm, needs 0.225 | needs 0.125 — **fits** |
| U5.4 | island half-width 0.207 mm, needs 0.225 | needs 0.125 — **fits** |
| U2.18 | **0** reachable via sites | 26277 |
| U2.19 | **0** reachable via sites | 32067 |
| C7.2 | 9, none over connected copper | 38865 |

All five are the same problem wearing five costumes: **a 0.45 mm via is too big
for the space left around these parts.** Two miss by 10 and 18 microns.

So it is one decision:

**A. Move parts.** L1 and U2 for the QFN escape, R9/U5/C7 for the ground pads.
Correct, costs nothing, and means regenerating placement -- which regressed the
board badly once already this week.

**B. Buy the finer fab rung.** 0.25/0.15 vias makes every one of the five
routable as the board stands. A paid step up at JLC; the exact price should be
read off the order form rather than assumed.

Note U2.18 is VBAT and U2.19 is VSTOR -- the charger's battery and storage
rails. These are not optional nets. **The board is not manufacturable until
they connect**, by one route or the other.

---

## CORRECTION: the finer via fixes three of five, not five

I recommended buying the finer fab rung on a measurement that was WRONG, and
JLC's own capabilities page corrected it.

The missing rule is **"Via hole to Track 0.2mm"**. It constrains the DRILL, not
the copper, so no copper-clearance checker on this project can see it. At
0.45/0.20 the copper rule dominates -- 0.225 + 0.10 = 0.325 against
0.10 + 0.20 = 0.30 -- so it never bit and its absence never showed. Below a
0.45 via the hole rule takes over, and shrinking the via stops buying room.

Re-measured with the drill rule applied:

| via / hole | binding halo | R9.2 | U5.4 | U2.18 | U2.19 | C7.2 |
|---|---|---|---|---|---|---|
| 0.45 / 0.20 | 0.325 | no | no | 0 | 0 | 9 |
| 0.40 / 0.20 | 0.300 | fits | fits | **0** | **0** | 20976 |
| 0.35 / 0.20 | 0.300 | fits | fits | **0** | **0** | 20976 |
| 0.30 / 0.15 | 0.275 | fits | fits | **0** | **0** | 24693 |
| 0.25 / 0.15 | 0.275 | fits | fits | **0** | **0** | 24693 |

**U2.18 and U2.19 gain nothing from any via JLC can make.** The earlier figures
of 26277 and 32067 were the drill rule being ignored.

### What was actually bought: via 0.40 / drill 0.20

The drill deliberately STAYS at 0.20 -- JLC's "preferred minimum" hole, still
mechanical drilling, still 6:1 aspect ratio on a 1.20 mm board. A 0.15 hole
buys almost nothing here and moves toward laser-drilled HDI, a different
product.

Closed **U5.4** (via inside its island) and **C7.2** (2.20 mm route to a via
over the plane). **5 open pads -> 3.**

`preflight` check 8 now reads the via floor from the fab floor file instead of
a constant, and new **check 8b** is a standing WARN: the via rung is a dropdown
at checkout and appears nowhere in the Gerbers, so a board drawn at 0.40 and
ordered on the default rung is built to rules it does not satisfy. No
file-based check can ever catch that, so it stays visible on every run.

### The last three

**R9.2** -- its island is wide enough for a 0.40 via (0.215 vs 0.200 needed),
but only 12 cells qualify and the best is blocked by **J4.1's pogo ring** plus
a VBAT_SENSE In1.Cu track. R9 sits too close to a pogo pad.

**U2.18 (VBAT) and U2.19 (VSTOR)** -- no via site in the pin row at any
manufacturable via size. Detouring the one CELL_NEG track that crossed the
corridor was tried and discarded: it widened the corridor from 0.90 to 1.50 mm
and still produced zero via sites, because the wall is the pads themselves --
U2's own neighbours and L1 immediately north.

All three need parts moved. These are the charger's battery and storage rails;
**the board is not manufacturable until they connect.**
