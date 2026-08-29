---
title: CURRENT STATE — read this first
type: project
updated: 2026-08-29
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

## The board — settled

| | |
|---|---|
| file | `cad/pcb-v3/pcb-v3-handoff.kicad_pcb` |
| size / layers | 19.30 mm square, 4 layer, **1.20 mm laminate** (1.22 finished) |
| finish | ENIG |
| status | **preflight 0 blockers, 2 warnings** · verify_handoff 0 failures |
| gerbers | `cad/v3-handoff/gerbers/`, plotted **corner origin 0…19.30** |
| BOM / CPL | `cad/v3-handoff/assembly/` — 20 lines, all sourced |

**Panelises to 71.3 × 71.3 mm** with edge rails for Standard PCBA. The housing
lip is 19.54 against a 19.50 worst-case board, so **a 0.1 mm break-off nub stops
it fitting** — take the depaneling service or file the edges.

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

`cad/scripts/touchid_module_v5.py` → `cad/v3-handoff/housing/`

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

> [!danger] **The slot has never been measured, and this is the biggest open risk.**
> The module is **14.86 mm** tall against the **8.36 mm** knob module it
> replaces. `riser_h` came from a task brief, not a measurement. If the slot is
> shallow, the riser shrinks, the cell no longer fits, and the cell search
> restarts. **Measure it before ordering housings or committing to a cell.**

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

1. **Slot depth** — see the housing warning above. Highest value, five minutes.
2. **J4/J11 pogo geometry** — preflight WARN 14. Measurement, not a datasheet.
3. **JLCPCB customs "Product Description"** — a legal declaration, yours to make.

**Waiting on others:**

4. LiPol quote (cell).
5. Sensor seller (wires vs bare pads).

**Not blocking:**

6. The **330 Ω loaded-while-asleep** harvest test — DESIGN-SPEC calls it
   "gates everything above".
7. Cold-start robustness with the new C1/C2: run the cell flat and check it
   restarts on harvest alone. The 10 µF is the best part that fits either way.
8. **The JLCONE project holds a stale housing STL** — pre-fillet and
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
