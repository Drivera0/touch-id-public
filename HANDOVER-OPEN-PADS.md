---
title: HANDOVER — close the last 2 open pads on TouchID
type: project
updated: 2026-08-30
---

# HANDOVER: close the last 2 open pads

You are picking up a 4-layer PCB that is **one blocker away from orderable**.
Everything else passes. Read this file, then `DESIGN-SPEC.md` (the technical
master) and `CURRENT-STATE.md` (what is decided / ordered / open).

---

## Standing rules — these are the user's, follow them exactly

* **Never invent a dimension, land pattern or part number.**
* **Do not order anything or spend money** unless asked.
* **Do not delete or overwrite originals** — `pcb-v2.kicad_pcb` and
  `touchid_module_v4.py` stay untouched.
* **Commit at every milestone.**
* **Run the checkers before claiming anything works** — `sexp_check.py` first,
  then `preflight.py`. Never eyeball the individual checkers.
* **When blocked, leave a note and move on.**

The user prefers concise, direct answers. They are not a PCB engineer; explain
the *why* in plain terms, but do not water down the engineering.

---

## What TouchID is

A fingerprint-sensor module replacing the swappable knob/button module in the
top-right slot of a **NuPhy Air75 V3** keyboard. It is BLE, harvest-powered
from the keyboard's RGB backlight pins, with a small Li-ion coin cell for
storage. Vault lives at `Foundation/touchid`.

---

## The board — verified state, 2026-08-30

    file      cad/pcb-v3/pcb-v6-handoff.kicad_pcb
    size      20.00 x 19.00 mm, 4 layer, 1.20 mm laminate, ENIG
    geometry  50 footprints, 145 pads, 606 segments, 90 vias, 37 zones
    fixings   two O1.20 press-fit pin holes at (+/-8.75, 0)

Reproduce the verdict with:

    cd cad/pcb-v3
    python3 sexp_check.py pcb-v6-handoff.kicad_pcb     # schema/parse first
    python3 preflight.py  pcb-v6-handoff.kicad_pcb     # the order gate

Current result — **1 BLOCKER, 3 WARNINGS, VERDICT: DO NOT ORDER**:

    BLOCKER  6   every connection routed        TRUE open pads = 2
    WARN     8b  order form via rung            0.40/0.20 -- select at checkout
    WARN     19  board thickness                1.20 -- select at checkout
    WARN     21b JLC assembly stock             C5118826=0, C6989585=0
    WARN     14  unverified geometry            J4/J11 pogo pads

**Checks 1-5, 6b, 7-13, 15-18, 20-23b all PASS.** Clearance 0 violations,
router DRC clean, no dangling ends, pours filled and connected, both pin holes
clear in copper and drill, all 90 vias clear of the pogo contacts.

---

## THE BLOCKER: 2 open pads

An open pad = the netlist says two things connect and **the copper does not**.
Fabrication will faithfully reproduce the absence.

### U5.2 — `PCM_VDD` — the serious one

`U5` is the **Mitsumi MC3651DF1AAM** cell-protection IC (JLCPCB `C6989585`).
`U5.2` is its **supply pin**. The protection circuit:

    R8   1 -> VBAT        2 -> PCM_VDD     330R 0201, datasheet R1 series protection
    C14  1 -> PCM_VDD     2 -> CELL_NEG    bypass
    R9   1 -> PCM_VM      2 -> GND         2.7k -- FUNCTIONAL, NOT OPTIONAL
    U5   1 -> CELL_NEG    2 -> PCM_VDD (OPEN)   3 -> PCM_VM   4 -> GND   5 -> NC

**With U5.2 open the protection IC is unpowered and does nothing** — no
over-charge cut at 4.280 V, no over-discharge at 2.700 V, no over-current at
0.315 A, on a lithium cell.

> R9 is not decoration: *"every over-current figure in the datasheet is measured
> with R2 = 2.7k. Omit it and 0.315 A is not 0.315 A."*

**Why it is hard:** U5 sits **inside the pogo block**, so U5.2 has **ZERO legal
via sites within 2.5 mm** (36,305 of the blocked grid points are pogo). It can
never take a via. Its net is on **F.Cu, 2.69 mm away**, so it needs an F.Cu
route or a placement change.

### R6.1 — `BL_RETURN` — functional, not safety

    R6   1 -> BL_RETURN (OPEN)   2 -> BL_FLAG      100k 0402, series protection only
    C13  1 -> BL_FLAG            2 -> GND          filter

`J11.4` is the keyboard's RGB LED **common return**; `R6` is a 100k series
resistor into `BL_FLAG` -> `U1.11` (nRF52840 GPIO). Open, the MCU cannot sense
whether the backlight is on — which is the cue **harvesting depends on**, since
harvest only works backlight-on (300 Ohm awake vs 11 kOhm asleep, a 35x
difference).

**Why it is hard:** R6.1 has 6,465 legal via sites, but its net is **6.6 mm
away at J11.4**. Its placement is a centroid artifact — the placer targeted the
midpoint of J11.4 at (6.50, -5.75) and U1's BL_FLAG pin at (-4.55, -1.70).

---

## READ THIS BEFORE ROUTING: the cell decision may DELETE U5 entirely

**Do not start routing U5.2 until this is resolved.** It may not need to exist.

`CELL-SOURCING.md` (written 2026-08-30 from LiPol's actual datasheet
MD_9241_10) found that the **catalogue LPM1254 ships WITH a PCM**, and that
PCM is functionally identical to U5:

| | cell's own PCM | U5 (MC3651) on board |
|---|---|---|
| over-charge | 4.25 V +/-50 mV | 4.280 V |
| over-discharge | 2.75 V | 2.700 V |
| over-current | 0.2-0.75 A | 0.315 A |

`PCM-ONBOARD.md` moved protection onto the board on the premise that *"a bare
wired 1254 is an ordinary retail product, a protected one is not."* **The
datasheet says the opposite** — the protected part is the catalogue product.

**If the protected cell is confirmed orderable at low quantity, then U5, R8 and
C14 come OFF the board.** That:

* **deletes the U5.2 open pad by deletion**, not by routing — and since U5.2 has
  zero legal via sites, deletion may be the only clean fix;
* frees area **inside the pogo block**, the densest region;
* **removes `C6989585` from the BOM — one of the two zero-stock parts** in
  preflight warning 21b.

**Gating action:** LiPol were emailed **2026-08-28** and no reply is recorded.
`CURRENT-STATE.md` notes **MOQ 5, PayPal/card, DHL door-to-door**. Chase that
reply first. If the user prefers the bare cell, U5 stays and U5.2 **must** be
closed — a bare cell with an unpowered PCM is a safety defect, not an
inconvenience.

**If U5 stays, note:** 0.315 A is **10.5x** the cell's real 30 mA continuous
rating (see corrections below). No PCM IC trips near 66 mA, so **none of them
guards this cell's continuous rating — they guard against shorts.** That is
acceptable, but do not repeat the claim that 0.315 A is "2.2x the cell rating".

---

## Corrections already made — do not re-introduce these errors

1. **The cell is rated 30 mA continuous, not 140 mA.** 140 mA / 210 mA pulse is
   the **VARTA CP1254**, which this design replaced. `PART-LIBRARY.md` section 5
   is a CP1254 table (correctly labelled, now banner-flagged SUPERSEDED) and the
   number was lifted from it. LPM1254 datasheet: **30 mA max continuous**, 12 mA
   standard; the catalogue page for the 65 mAh variant says 65 mA. **Confirm for
   the variant ordered.** The load is 25 mA = 83% of a 30 mA rating.
2. **The cell is BARE unless the protected variant is confirmed.** `PCM-ONBOARD.md`
   (2026-08-29) is the current decision. `CURRENT-STATE.md` said "with PCM" and
   was corrected 2026-08-30.
3. Fixed at source: `netlist_v3.py` is the **single source of truth**;
   `export_netlist.py` regenerates `netlist_v3.csv`, `netlist_v3_nets.csv` and
   `NETLIST-V3.md` from it. Never hand-edit the generated files.

---

## CLOSED QUESTIONS — do not reopen these

**U1 stays the Raytac MDBT50Q-1MV2.** A full smaller-module search was run
2026-08-30 and every candidate failed. See `cad/pcb-v3/MCU-SWAP-BC840M.md`
(marked REJECTED). The mechanism, which will not change:

> MDBT50Q is physically bigger **because its antenna is a ceramic chip**, and
> that is exactly what makes it work here. Every smaller module buys its small
> body with a **PCB trace antenna**, which pays for it in mandatory keep-out.
> Compare **body + keep-out**, never body alone.

| | MDBT50Q (chip ant.) | Fanstel BC840M (trace ant.) |
|---|---|---|
| body | 162.75 mm2 | 87.33 mm2 |
| ground-free area REQUIRED | 84.20 mm2 | **110.55 mm2** |

* **BC840M** also fails outright: datasheet says *"Don't use a module with
  internal antenna inside a metal case"* and *"keep all external metal at least
  30 mm from the antenna area"* — the keyboard's top frame is metal. And it
  needs 10.10 mm antenna + 5 mm ground clearance each side = **20.10 mm on a
  20.00 mm board**, short by 0.10 mm.
* **BC840** (7.1 x 9.2) — range is **4 m** at 1 Mbps vs BC840M's 135 m.
* **Insight SiP ISP1807** (8 x 8 x 1, the most tempting) — **no VDDH**:
  VCC_nRF is 1.7-3.6 V, *absolute max 3.9 V*, revision history says "No
  High-Power Mode availability". Plus an 18.0 x 4.0 mm keep-out.
* **Holyiot 17095** — no VDDH. **Minew MS88SF3** — 18.5 x 12.5, bigger.

**VDDH is architectural, not a convenience.** `U1.28 NRF_VDD` is annotated
*"REG0 output decoupling"* — REG0 is the nRF52840's **internal** high-voltage
regulator, so VDDH is the input and VDD is REG0's *output*. Both TPS7A2033 LDOs
serve the SENSOR rails; there is no 3.3 V rail to retarget.

**A different cell cannot remove the VDDH requirement.** The ceiling is set by
the SOURCE: DESIGN-SPEC records the harvest source *"cannot exceed 3.68 V"* and
there is no charger IC, so VSTOR tops out at 3.68 V whatever cell is fitted —
still above 3.6 V, and nothing is rated between 3.6 and 5.5 V. Small LiFePO4
does not exist at retail at 20-35 mAh (those parts are 20 **Ah**).

**A coin cell HOLDER was evaluated and rejected** (see `CELL-SOURCING.md`):
pocket is O13.00 (plan of record) or O14.00, smallest 12 mm holders are
~15.5-16.0 mm OD; it would take the module from 1.5-1.8x to **2.0-2.1x** the
8.36 mm knob module it replaces on an **unmeasured** slot depth; spring contacts
on a device that is *pressed*; and US **16 CFR 1263 (Reese's Law)** requires a
tool or two independent simultaneous hand movements for replaceable button-cell
compartments, which matters because the user may sell these.

---

## TRAPS — this project has bitten repeatedly

1. **The checkers lie more than the board.** Most "blockers" here have been
   checker bugs. Verify any failure against the board file before acting.
   Six real checker defects were found on 2026-08-30 alone, and several made a
   verdict depend on **file formatting** rather than geometry.
2. **KiCad 8 vs KiCad 10 net dialects.** KiCad 8 writes a top-level
   `(net N "NAME")` table; **KiCad 10 drops it** and writes `(net "NAME")`
   inline. A parser that only knows one dialect sees **zero nets and passes
   everything**. After ANY round-trip through the GUI, re-verify the parsers
   still see nets before believing a result.
3. **KiCad Y is DOWN.** A positive footprint angle is **CLOCKWISE**. Four
   separate sign bugs came from getting this wrong. **+Y is the spacebar edge** —
   never negate Y off the KiCad file.
4. **`(size ...)` on a CUSTOM pad is the ANCHOR, not the copper.** U3/U4
   (TPS7A2033 X2SON-4) have a 0.148 anchor and a 0.46 x 0.31 `gr_poly` land.
   Two parsers read them 3x too small.
5. **Judge pour connectivity against KiCad's own `filled_polygon` output**
   (`pour_truth.py`), never a model of it. A filled zone is a keyholed ring and
   is self-intersecting — `buffer(0)` first and test **area**, not `.intersects()`.
6. **`close_open.py` writes a DEGRADED board when it fails** — it rips the net
   before retrying and does not restore. **Discard its output on a NO PATH
   result.** Still unfixed.
7. **Routing here is a net-ORDER problem, not a routing-quality problem.** Zero
   opens has been reached; one net taking the only corridor walls another's pin
   in. `--ordering mps` beat hand-staging (2 vs 4 disconnected).
8. **The board is at capacity.** Three placement interventions (0201 shrink,
   finer slot grid, corner penalty) changed the board without changing the
   outcome. The two things that worked were **surgical**: moving TP4, and
   clearing one layer under a pad.

---

## Tools in `cad/pcb-v3/`

    sexp_check.py     parse + schema guard. RUN FIRST, ALWAYS.
    preflight.py      THE ORDER GATE. one go/no-go. never eyeball the others.
    pour_truth.py     shared parser; reads KiCad's real filled_polygon
    build_pcb_v3.py   the generator; writes pcb-v6.kicad_pcb
    handroute.py      grid A* + MST multi-point routing, --ordering {mps,...}
    via_stub.py       via ON a pad + inner-layer stub; validates pogo rings,
                      pin-hole drill rule, stub clearance, landing net.
                      THIS TOOL CAUGHT MY OWN POGO-RING ERROR. Use it.
    close_open.py     only-adds invariant (but see trap 6)
    stitch_open.py    pad-to-copper
    nudge_via.py      moves a via AND its anchored track ends as one group
    push_off_pads.py  pushes tracks off pads AND vias; NOT idempotent
    gnd_via_anchor.py skips on real pour connectivity
    add_pours.py      F.Cu/B.Cu GND pours -- regeneration LOSES them, re-run
    make_bom_cpl.py   -> cad/v6-handoff/assembly/
    verify_gerbers.py / verify_handoff.py

---

## Suggested order of work

1. **Chase the LiPol reply** (protected LPM1254, wired, MOQ 5). It may delete
   U5/R8/C14 and with them the U5.2 blocker and one zero-stock part. Cheapest
   highest-value action; ask the user before sending anything.
2. **If protected cell confirmed:** remove U5, R8, C14 from `netlist_v3.py`,
   regenerate, rebuild, re-route, re-run preflight. Expect U5.2 to vanish and
   pogo-block congestion to ease.
3. **If bare cell:** U5.2 **must** be closed. It cannot take a via — F.Cu route
   or move U5. Consider moving U5 out of the pogo shadow before attempting to
   route; this is a placement problem more than a routing one.
4. **R6.1** in either case. 6,465 legal via sites but the net is 6.6 mm away;
   its position is a centroid artifact, so **re-target the placement** rather
   than routing 6.6 mm across a full board.
5. **Re-run the gate.** `sexp_check.py` then `preflight.py`. Only "0 BLOCKERS"
   counts.
6. **Then** plot Gerbers/BOM/CPL. **No Gerbers exist for this board.** The
   archived package is for the 19.30 mm SQUARE board with corner screws — DO NOT
   ORDER FROM IT. `kicad-cli` is not available in the agent sandbox, so the user
   must plot from KiCad; then run `verify_gerbers.py` and `verify_handoff.py`.

**Also unmeasured and cheap to fix: the keyboard SLOT DEPTH.** The housing file
calls it "a slot depth NOBODY HAS MEASURED" and "the first thing to give". The
module is already 1.5-1.8x the 8.36 mm knob module it replaces. Ask the user to
measure it.

---

## Order-time items (not in the Gerbers)

* **Via rung**: board is drawn 0.40/0.20 — JLC charges more below 0.45 diameter.
  **Select the matching via option at checkout.**
* **Thickness**: 1.20 mm. **JLC defaults 4-layer to 1.6** — must be set.
* **Stock**: `C5118826` (U1 MDBT50Q) and `C6989585` (U5 MC3651) were both
  **stock=0** as of 2026-08-28. U1 is consigned; the user cancelled that order.
  Re-check at order time.
* **0201 parts require Standard PCBA** (Economic stops at 0402). This order
  already is Standard.
* Keep **"Confirm Parts Placement = Yes."** Only U1-U4 can be rotated wrong.
