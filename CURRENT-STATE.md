---
title: CURRENT STATE — read this first
type: project
updated: 2026-08-30
---

# TouchID — current state

**Read this before touching anything.** `DESIGN-SPEC.md` remains the technical
master for *how the thing works*; this file is the authoritative record of
*what is decided, what is ordered, and what is still open*.

Anything in `_archive/` is superseded. Do not take a number from there.

---

## Standing rules (unchanged since the start)

* **Never invent a dimension, land pattern or part number.**
* **Do not order anything or spend money** unless asked.
* **Do not delete or overwrite originals** — `pcb-v2.kicad_pcb` and
  `touchid_module_v4.py` stay untouched.
* **Commit at every milestone.**
* **Run the checkers before claiming anything works** — `sexp_check.py` first,
  then `preflight.py`. Never eyeball the individual checkers.
* **When blocked, leave a note and move on.**

---

## The board — clean, NOT yet re-packaged for the fab

| | |
|---|---|
| file | `cad/pcb-v3/pcb-v6-handoff.kicad_pcb` |
| size / layers | **20.00 × 19.00 mm** (20 horizontal), 4 layer, **1.20 mm laminate** |
| finish | ENIG |
| status | **1 open pad** (C14.2) · clearance 0 · schema clean · see the 2026-08-30 pass below |
| fixings | two **Ø1.20 press-fit pin holes** at (±8.75, 0) — corner coords (1.25, 9.50) and (18.75, 9.50) |
| gerbers | **none exist for this board.** The old package is archived under `cad/_archive/2026-08-30-superseded-by-v6/v3-handoff-pkg/` |
| BOM / CPL | **regenerate** into `cad/v6-handoff/assembly/`. `make_bom_cpl.py` is repointed and its origin bug is fixed |

> [!warning] The handoff package is for a board that no longer exists
> The archived package was plotted from the 19.30 mm SQUARE board with corner
> screws. The board is now 20.00 × 19.00 with press-fit pins on the side
> centres, seven parts in 0201, and different divider values. **Do not order
> from those Gerbers.** They have to be re-plotted and re-verified from the
> file above.

### 2026-08-30 pass — 1 open pad, and SIX checker bugs found

    open pads     1   C14.2 on CELL_NEG (see below)
    clearance     0 different-net pairs inside 0.100
    schema        top-level child kinds all known to KiCad
    housing       all 8 boolean clearance checks pass

**C14.2 has ZERO legal via sites within 1.8 mm** and its nearest own-net pad
(U5.1) is 2.163 mm away through the PCM cluster, the densest on the board. It is
a hand-jumper or a PCM re-plan, not another routing attempt.

**The checkers were wronger than the board.** Six real defects, all of which had
been passing boards as clean:

| what | effect |
|---|---|
| `check_board` parsed copper with a POSITIONAL regex | saw 54 of 77 vias; missed a real 0.0853 mm violation |
| `blocked_masks` never inflated keep-outs | close_open laid 20 VSTOR segments inside the antenna keep-out |
| `blocked_masks` tested cell CENTRES, router draws SEGMENTS | two GND tracks 0.0853/0.0920 mm from vias |
| `(size)` on a CUSTOM pad is the anchor, not the copper | U3/U4 pads read 3x too small by TWO parsers |
| `stitch_open` resolved nets from the net TABLE | wrote `(net None)` on KiCad 10 boards -- netless copper that SHORTED a pad |
| `push_off_pads` only pushed off PADS | a track grazing a foreign via was invisible to it |

`close_open` also **writes a degraded board when it fails** -- it rips the net
before retrying and does not restore, so a no-path run saved a file missing 33
segments, 23 vias and every filled polygon. NOT YET FIXED; discard its output on
failure.

### What "0 blockers" does and does not mean

It means every rule this project can check is satisfied: 0 open pads against
the pour KiCad actually computed, 0 copper-clearance violations, router DRC
clean, no dangling ends, all 75 vias clear of the pogo contacts, both pin holes
clear in copper *and* drill.

It does **not** mean the design is proven. Nothing has been fabricated or
powered. The harvest test that DESIGN-SPEC calls "gates everything above" has
not been run, cold-start on harvest alone is untested, and the cell is still
unchosen — VBAT_OV is tuned against an assumed one.

### Fixed on 2026-08-30 — both were order-blocking

* **Both press-fit pins were drilled through copper.** L1 pad 2 sat 0.288 mm
  inside the right hole, U4 pad 2 0.120 mm inside the left. Every board since
  the pins moved to the side centres had this, including the one being treated
  as the best result. The keep-out rule existed only in `_legal_mask`, which
  **only the 0402 packer consults** — L1/U2/U3/U4/C7 are placed explicitly and
  skipped it. `check()` now tests every pad; preflight 23 tests tracks and vias.
* **JLC has two hole rules and only one was known.** Via hole-to-hole 0.20 mm,
  **pad** hole-to-hole **0.45 mm**. The pin is a 1.20 mm np_thru_hole *pad*, so
  vias beside it owe 0.45 — two were short by 26 and 9 µm. `PIN_HOLE_NO_VIA`
  rings now prevent it; preflight 23b re-grades via spacing at JLC's real 0.20,
  because `check_drc` grades it at a hardcoded 0.5 that no flag overrides.

**Panelises with edge rails for Standard PCBA** — 0201 parts require the
Standard tier, which this order already is. The housing lip figure below was
computed for the 19.30 mm square board and **must be re-derived** for 20 × 19.

**Keep "Confirm Parts Placement = Yes."** Only U1–U4 can be rotated wrong; the
other 25 placements are two-pad symmetric.

### Parts that changed recently

| ref | now | was | why |
|---|---|---|---|
| **C1, C2** | **`C77000`** Murata GRM155R61A106ME44D **10 µF 10 V** 0402 | `C2858031` 4.7 µF 25 V | 4.7 µF nominal delivered only ~2.3–2.8 µF at 3.9 V bias. Same 0402 land — **no board change** |
| **U1** | **CONSIGNED** — customer ships MDBT50Q to JLC's warehouse | JLC-supplied | JLC assembly stock was 0 with an ~11-day backorder |
| C5 | `C70225` | `C18164635` | JLC's BOM matcher would not auto-select the old one |

---

## The sensor — settled

**HLK-ZW0922.** The ZW0905 is **discontinued**; this is its replacement and it
is a **drop-in** — same Ø18.00 flange, Ø15.50 barrel, 0.20 step, and the
**identical 6-pin order** at J2. Electricals identical too (10 µA standby,
15/25 mA active, 200 mA × 4 µs peak, <200 mV ripple).

> **The "Φ12.8 mm" in its spec table is the sensor package, not the module.**
> The real outline is only in the §2.3 drawing. Sizing anything from that table
> builds the wrong part. This trap has now appeared in two Hi-Link datasheets.

Full analysis: `cad/pcb-v3/SENSOR-ZW0922.md`. Spec PDF and a rendered copy of
the drawing are in `cad/pcb-v3/datasheets/`.

**Open with the seller:** wires fitted to the pads vs bare pads (the 4.5 mm
connector must come off either way — it would pass 3.69 mm through the cell),
finger-detect mode standard, and the Ø18.00 ±0.05 tolerance in production.

---

## The housing — built, but resting on an unmeasured number

`cad/scripts/touchid_module_v6.py` (v5 is archived) → regenerate the STL

| | current |
|---|---|
| riser | **6.50 mm** (was 4.50) |
| top face | **z 13.66** (was 11.66) |
| **total module height** | **14.86 mm incl. PCB** |
| cell pocket | **Ø14.00** (was Ø12.50), collar wall 1.585 |
| cell modelled | **Ø13.5 × 8.4** assembled |
| clearance above cell | **0.81 mm** (was 1.61) |
| mesh | watertight, 0 holes, 0 non-manifold, 1 body, 1230.38 mm³ |
| checks | **8/8 boolean clearance checks pass** |

Corner walls were fixed from **0.150 mm to 0.810–1.050** by filleting the cavity
corners r1.6 **at the first cut** — the cavity is cut twice and a later cut
cannot restore material.

> [!success] **Slot depth is NOT a constraint — resolved 2026-08-29.**
> The module seats on the pogo pins and **stands proud**. The housing lip props
> against the keyboard's enclosure, the rear shelf slides under the metal top
> case as a pivot, and a countersunk M2 screw through the mounting arm holds
> the opposite corner. Nothing limits `riser_h` from above.
>
> The locating geometry was measured off the knob module from the start — top
> tier 18.52, lip 19.66, shelf 11.00 x 1.18 x 2.62, arm 5.12, arm-tip diagonal
> 30.14. **This was carried as "the biggest open risk" for nine days and it was
> never a risk.** The height comparison against the flush 8.36 mm knob was the
> wrong question: that module had nothing on top of it, and ours has a sensor
> you have to reach.

---

## The cell — decided, awaiting quote

**LiPol LPM1254 with PCM and wires fitted.** Enquiry sent 2026-08-28.

| | |
|---|---|
| assembled | **Ø13 ±0.5 × 6.5 ±0.3** → Ø13.5 × 6.8 worst case |
| capacity | 65 / 70 / **80 mAh** by variant |
| protection | over-charge **4.25 V ±50 mV**, over-discharge 2.75 V, over-current **0.2–0.75 A** |
| wires | UL10064 32AWG, 30 ±3 mm, no connector |
| buy | LiPol, **MOQ 5**, PayPal/card, DHL door-to-door |

**The 80 mAh variant beats the CP1254 it replaces** (77 mAh) while adding a
factory PCM and factory wires. It fits the housing as built.

**Why not VARTA:** no protected CP1254 exists. Their "IP W" assembly is kapton
+ tags + wires with **no PCM** (proven by the drawing: +0.2 mm over the bare
cell cannot contain one), it is Ø12.9 assembled, both A4X parts are NRND, and
**no North American distributor carries CoinPower at all**.

**You may not attach leads yourself** — CoinPower handbook §8.7 prohibits
soldering to the cell; only the manufacturer may. Hence a pre-wired assembly.
**BT1 is two wire-landing pads, not a cell footprint.**

`VBAT_OV` = 3.912 V (3.955 wc) sits 295 mV below the 4.25 V trip. **The cell's
charge voltage is 4.30 V** — the 4.00 V figure in older notes is the
*rapid-charge* footnote and does not apply at harvest currents.

Ranking and the enquiry text: `cad/pcb-v3/CELL-DECIDED.md`,
`cad/pcb-v3/CELL-ENQUIRY-DRAFT.md`.

---

## Open items

**Blocking an order:**

0. **Gerbers, BOM and CPL do not exist for the current board.** `cad/v3-handoff/`
   is the 19.30 mm square board with corner screws. Re-plot and re-verify from
   `pcb-v6-routed-ZERO-OPENS.kicad_pcb` before anything else.
1. ~~Slot depth~~ — **resolved, was never a constraint.** See above.
2. **J4/J11 pogo geometry** — preflight WARN 14. Measurement, not a datasheet.
3. **JLCPCB customs "Product Description"** — a legal declaration, yours to make.
4. **Two order-form settings are not in the Gerbers** and default wrong:
   select the **small-via rung** (board is drawn 0.40/0.20; JLC charges more
   below 0.45 and builds to the wrong rules if it is not selected) and
   **1.20 mm thickness** (JLC defaults 4-layer to 1.6).

**Waiting on others:**

5. LiPol quote (cell). VBAT_OV is currently tuned against an ASSUMED cell.
6. Sensor seller (wires vs bare pads).
7. **U1 (C5118826) and U5 (C6989585) are both 0 stock at JLC** and consigned —
   re-check at order time.

**Not blocking:**

8. The **330 Ω loaded-while-asleep** harvest test — DESIGN-SPEC calls it
   "gates everything above".
9. Cold-start robustness with the new C1/C2: run the cell flat and check it
   restarts on harvest alone. The 10 µF is the best part that fits either way.
10. **The JLCONE project holds a stale housing STL** — pre-fillet and
   pre-riser-change. Replace before ordering 3D prints.

---

## Traps this project has actually fallen into

Kept because each cost real time and all are easy to repeat.

* **KiCad is Y-DOWN** — positive footprint angle is **clockwise**. Four separate
  sign bugs came from this.
* **Vendor spec tables lie about module size.** "Φ12.8 mm" is a sensor package;
  the module is Ø18.00. Read the drawing.
* **Datasheet footnotes are not headline specs.** 4.00 V was a rapid-charge
  derating that got hard-coded into a safety gate as the cell's limit.
* **Generated files get hand-edited.** `NETLIST-V3.md` says "do not hand-edit"
  and was edited anyway; the edits were silently wiped on regeneration. Edit
  `netlist_v3.py`.
* **The checkers lie more than the board does.** Most "blockers" here were
  checker bugs — a scan that read the *unrouted* file, a parser that matched
  `"(segment "` with a trailing space and silently read 0 of 288 tracks, a
  clearance scan that ignored component bodies. **Sanity-check the checker
  before believing it about the board.**
* **Two derivations of the same wrong assumption still agree.** The CPL origin
  bug survived an "independent" check because both rested on the same false
  premise about the gerbers.
