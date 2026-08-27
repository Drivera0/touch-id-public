---
title: Next session — autonomous rebuild brief
type: project
tags:
  - touchid
  - handoff
updated: 2026-08-27
---

# Next session — autonomous rebuild brief

**Read this file first, before touching anything.** It is written for a session
running **unattended** while Daniel is at work. He cannot answer questions. Every rule
below exists because of a mistake this project has already paid for.

> [!tip] How to start this
> Open a session in this folder and say: **"work through NEXT-SESSION.md"**.
> Scope agreed with Daniel: **Tasks A through E, in order.** Get as far as you can;
> three tasks done properly beats five started.
>
> **Before walking away, approve the permission mode** so the session is not left
> waiting on a prompt for hours. Claude cannot grant itself permissions — if a prompt
> fires and nobody is at the machine, everything after it stalls.

---

## 0. Restore point

Committed and tagged immediately before this work began:

```
git tag         pre-v3-rebuild
git commit      cf507c3  "Save point before the v3 rebuild"
```

If anything goes badly wrong:

```
cd <vault>/touchid
git reset --hard pre-v3-rebuild      # discard everything since
git stash list                       # check nothing valuable was stashed
```

**Never** `git reset --hard` without first checking `git status` — there may be work
worth keeping. Prefer `git stash` over discarding.

---

## 1. Hard rules for an unattended session

1. **Never invent a dimension, a land pattern or a part number.** This project came
   one step from paying for boards with invented U1/U2 footprints. If a number cannot
   be traced to a datasheet, an LCSC page or a caliper measurement, **stop and write it
   into the Blocked list at the bottom of this file** instead of guessing.
2. **Do not order anything. Do not spend money.** No JLCPCB orders, no cart, no
   checkout, not even a quote that requires an account action.
3. **Do not delete or overwrite originals.** Work on copies. `pcb-v2.kicad_pcb` stays
   as it is; the new board is a new file.
4. **Commit at every milestone** with a clear message. Small commits, so anything can
   be unwound.
5. **Run the checkers before claiming anything works.** `sexp_check.py` must pass
   before any other result means anything.
6. **When blocked, leave a note and move to the next task.** Do not burn the session
   on one stuck item, and do not guess your way past it.

---

## 2. What is already decided — do not re-litigate

All of this is measured or datasheet-sourced. It is in `DESIGN-SPEC.md`; this is the
summary so the next session doesn't re-derive it.

| Thing | Decision |
|---|---|
| Power source | **Harvest J11 while the backlight is awake** (~300 Ω, 18–24 mW). Asleep is ~11 kΩ and near-useless. Wired vs wireless is irrelevant |
| Ground-path control test | **Passed** — 0.096 V both on the rail and on the USB-C shell. The measurements are real |
| Storage | **VARTA CP1254 A4**, Ø12.1 × 5.4 mm, 77 mAh. Supercaps are ruled out on three independent counts |
| Harvester | **TI BQ25505** (LCSC C882746). MPPT ratio by pin strap: VOC_SAMP to GND = VOC/2 |
| Current limit | **1 kΩ series on each of J11-1/2/3.** Caps the awake draw at 3.3 mA, below the ~10.7 mA that visibly dimmed keys. These resistors also isolate the three channels, so **no ORing diodes are needed** |
| MCU | **Raytac MDBT50Q-1MV2** (nRF52840). Cell connects to **VDDH (pin 30)**, *not* VDD |
| Sensor rail | **TPS7A2033** always-on for SENSOR_3.3V, with a local 22 µF for the 200 mA/4 µs transient |
| MCU rail | **LM66100** load switch for MCU_3.3V, gated by an MCU GPIO |
| Sensor | **HLK-ZW0905**. 3.0 V min, 10 µA standby, 25 mA active. Datasheet in `datasheets/` |
| Housing | **v5 adds a 4.50 mm riser column**, moving the sensor seat to z 11.66 and the barrel bottom to z 9.46. This is what makes the cell fit |
| Board | **4 layers**, 19.30 × 19.30 mm, outline and mounting holes unchanged |
| Radio | BLE for now. A 2.4 GHz dongle may be added later in **firmware only** — no board change |

### Load budget (datasheet numbers, not estimates)

| | mWh/day |
|---|---|
| 50 scans at 25 mA for 1.5 s | 1.93 |
| Sensor standby, 10 µA | 0.89 |
| nRF52 sleep, ~6 µA | 0.53 |
| **Total** | **≈ 3.3** |

Awake harvest covers this in about **11 minutes of backlight per day**.

---

## 3. Tasks, in order

Get as far as you can. **Do not skip ahead** — later tasks depend on earlier ones.
Finishing three tasks properly beats starting five.

### Task A — Verified part library

Build a footprint + 3D dimension set, every entry traced to a source.

| Part | LCSC | What to get |
|---|---|---|
| Raytac MDBT50Q-1MV2 | not at LCSC | Land pattern from Raytac's own spec (Ver. K). **Antenna keep-out in mm.** Confirm VDDH is pin 30 |
| TI BQ25505 | C882746 | **VQFN-20 RGR0020A.** See the trap below |
| TI TPS7A2033 | C46459900 | X2SON-4 DQN — already traced in `DESIGN-SPEC.md` §3, reuse it |
| TI LM66100 | C2869734 | SC-70-6 (DCK) |
| 22 µH inductor | C2849435 | 1008, and its **height** |
| Passives | see §BOM | 0402 / 0603 / 0805 |

> **The BQ25505 trap.** TI QFN thermal pads are routinely **solder-mask-defined**, so
> the printed numbers are *mask openings* and the copper is larger on every side. This
> is the exact class of error that scrapped order Y6 (see `DESIGN-SPEC.md` §7 trap 1).
> Trace it from TI's package drawing, and write down which dimensions are copper and
> which are mask.

**Done when:** every footprint has a cited source, and any dimension that could not be
verified is listed in Blocked rather than estimated.

### Task B — Housing v5

Extend `cad/scripts/touchid_module_v4.py` into `touchid_module_v5.py`. **Do not edit
v4 in place.**

- Circular riser column, **+4.50 mm**, inner bore Ø15.60, outer ≈ Ø18.37, top face at
  z 11.66. Sensor barrel bottom lands at z 9.46
- A seat or pocket for the **CP1254** (Ø12.1 × 5.4) in the bore, above the MCU
- Keep everything else: 19.54 lip, 0.80 wall, diagonal M1.2 bosses, ear screw

**Boolean-verify all of these and print the volumes:**

- housing ∩ MCU module = 0
- housing ∩ sensor = 0
- housing ∩ cell = 0
- cell ∩ sensor barrel = 0
- cell ∩ MCU module = 0
- cell ∩ bosses = 0
- nothing below z = 0

Expected clearance above the cell is ~2.26 mm with a 2.05 mm-tall MDBT50Q. **If the
model disagrees with that, trust the model and write down the discrepancy.**

**Done when:** the script runs clean, prints all clearances, and exports STEP to
`cad/exports/`.

### Task C — Antenna orientation ⚠ determine carefully

Daniel's instruction: **the antenna points toward the spacebar.**

Established from the board file: all ten pogo pads sit on **one half** of the board,
spanning |y| 1.12–8.32 with x from −8.30 to +7.05. The other half is free — so an
antenna keep-out at the opposite edge is geometrically possible.

> ⚠ **There is a sign-convention discrepancy that must be resolved before layout.**
> `DESIGN-SPEC.md` §2 lists the J4 pogo pads at **y −8.32…−1.12**, but extracting them
> from `pcb-v2.kicad_pcb` with the documented transform puts them at **+1.12…+8.32**.
> The magnitudes agree exactly; only the sign differs. One of the two is wrong.
>
> **Resolve it from the file and the physical pin-numbering convention in
> `Pin Test Procedure.md`** ("REAR toward screen" / "FRONT toward spacebar"), not by
> assuming. Then state plainly in the new spec which edge faces the spacebar. Getting
> this backwards puts the antenna under the metal frame and wastes a board run.

**Done when:** the spacebar edge is identified with reasoning written down, and the
MDBT50Q's keep-out is shown to fit there without overlapping any pogo pad.

### Task D — Schematic

Nets and connections:

```
J11-1/2/3 --[1k each]--> VIN_HARVEST --> BQ25505 (VOC_SAMP -> GND for VOC/2 MPPT)
BQ25505 VBAT <-> CP1254 cell (+ bulk cap)
cell --> MDBT50Q VDDH (pin 30)          <-- NOT VDD
cell --> TPS7A2033 --> SENSOR_3.3V (always on, local 22 uF)
SENSOR_3.3V --> LM66100 --> MCU_3.3V    <-- gated by MCU GPIO
J11-4 --[1M/220k]--> MCU GPIO           <-- backlight-awake flag
cell  --[4.7M/1M]--> MCU ADC            <-- cell voltage, 3.0 V floor in firmware
J4-5  --> GND (the only J4 pin used)
```

**J2 sensor connector — use the CORRECTED pinout:**

| Pin | Net |
|---|---|
| 1 | SENSOR_3.3V |
| 2 | WAKEUP |
| 3 | MCU_3.3V |
| 4 | TX |
| 5 | RX |
| 6 | GND |

> The old table in `DESIGN-SPEC.md` was the **ZW0901's** and had power and ground
> reversed end-for-end. It is fixed in the file now; do not reintroduce it.

Also place: SWD pads (SWDIO, SWCLK, RESET, VDD, GND) and bottom-side test points for
VIN_HARVEST, VSTOR, VBAT, VBAT_OK, both 3.3 V rails, the J11-4 flag node, and several
grounds.

Set VBAT_OV to **4.25 V** via R = 5.6 MΩ / 7.5 MΩ. All programming resistors 0402 so
they can be swapped by hand.

**Done when:** a complete netlist exists and every pin of every part is accounted for —
connected or deliberately marked no-connect.

### Task E — Board layout, 4 layers

New file, e.g. `cad/pcb-v3/pcb-v3.kicad_pcb`. Do not modify pcb-v2.

- 19.30 × 19.30, R2.0 corners, mounting holes at (+8.10, −8.10) and (−8.10, +8.10)
- **Pogo pads keep their exact existing coordinates** — they are set by the keyboard
- 4-layer stackup with a solid ground plane
- Antenna at the spacebar edge per Task C, keep-out clear of copper **on every layer**
- Fix the carried-over issues from `cad/pcb-v2/OPEN-ISSUES.md`:
  - the `+3V3`/`VBAT` pair at exactly 0.1270 mm — give it real margin
  - **remove `F.Paste` from J2** — those pads are hand-soldered, a stencil would print
    solder domes on them
  - no unrouted pads left for "the autorouter"

Then run, in this order:

```
python sexp_check.py    pcb-v3.kicad_pcb     # structure — always first
python check_board.py   pcb-v3.kicad_pcb     # clearance
python check_connect.py pcb-v3.kicad_pcb     # per-net island count
```

**Done when:** all three pass, and any remaining violation is written into Blocked
with the reason.

---

## 4. Traps this project has already paid for

From `DESIGN-SPEC.md` §7 — read it in full, but these bite hardest here:

1. **TI land-pattern numbers are mask openings** when marked solder-mask-defined.
   Copper is larger. Directly relevant to the BQ25505.
2. **Vendor spec-table diameters are the package, not the module.**
3. **Regex checkers go blind when the file format changes** — a checker printing a
   confident summary is not evidence. Print counts and sanity-check them.
4. **Never trust a generator script as evidence of what shipped.** Read the artwork.
5. **Total-area comparisons hide redistribution.** Compare pad-by-pad.
6. **Writing the file in Python text mode converts CRLF → LF.** Write bytes.
7. **Deleting segment blocks silently deletes vias.** Print via counts before and after.
8. **A pad's own copper blocks its escape.** Exclude the source pad from its obstacle map.

---

## 5. Where things live

| | |
|---|---|
| Master spec | `DESIGN-SPEC.md` — **authoritative; if another note disagrees, this wins** |
| Open issues | `cad/pcb-v2/OPEN-ISSUES.md` |
| Current board | `cad/pcb-v2/pcb-v2.kicad_pcb` — **read-only for this session** |
| Housing v4 | `cad/scripts/touchid_module_v4.py` — **do not edit in place** |
| Checkers | `cad/pcb-v2/sexp_check.py`, `check_board.py`, `check_connect.py` |
| Datasheets | `datasheets/` — ZW0905 spec and the 0xEF01 protocol manual |
| Measurements | `Pin Test Results.md`, `two-tests.html`, `harvest-test.html` |

---

## 6. Blocked — append here, do not guess

Anything that could not be verified goes here with enough detail that Daniel can close
it in five minutes. Leave the task unfinished rather than filling the gap with a
plausible number.

Full detail for each of these is in **`PART-LIBRARY.md` §9**. Summarised here in the
order that unblocks the most work.

### B1 — MDBT50Q-1MV2 land pattern and antenna keep-out, in mm ⛔ blocks Task E

The one item that stopped the session. Raytac Ver. K §2.2 and §2.3 (pp. 9–15) are
vector drawings with **no text layer**, so text extraction returns them blank. One
browser screenshot at 65 % was captured before the browser pane stopped compositing
frames — it is not readable at footprint precision and **must not be used**.

Without it, U1 cannot be placed, so Task E cannot start. Rule 1 was followed: nothing
was invented.

**Fastest close, ~5 min:** Raytac's *Footprint & Design Guide* package (§2.4 of the
approval sheet) at `raytac.com/download/index.php?index_id=43` contains Altium / Eagle /
Protel footprints plus 2D/3D drawings. Read the footprint file — exact pad coordinates,
no drawing interpretation at all.
**Or:** open the Ver. K PDF at pp. 9–15 at ≥200 % and read the dimensions off.
**Or, possibly best:** **JLCPCB lists this part as `C5118826`.** Both DESIGN-SPEC and
this brief say "not at LCSC" — that appears to be wrong. A JLC-catalogued part means an
assembly-verified land pattern, which closes this outright.

### B2 — VDDH rise time. The cell cannot connect straight to pin 30

Raytac Ver. K §5.2: **t_R VDDH = 100 ms max** for 0 → 3.7 V. A CP1254 charged from
harvest rises over *hours*. Every cold start from a flat cell violates this.

The parts to fix it are already in the design: **BQ25505 VBAT_OK (pin 13)** is exactly a
"storage is charged" output and can gate a switch feeding VDDH, so the module sees an
edge instead of a ramp. Needs: which switch, and the VBAT_OK thresholds.
The netlist currently sets VBAT_OK rising 3.47 V / falling 3.12 V
(ROK1 4.53M, ROK2 7.15M, ROK3 1.33M, sum 13.01 MΩ, inside TI's 11–15 MΩ window).

### B3 — The LM66100 cannot be switched off by an nRF GPIO

Its **CE is a comparator input referenced to VIN**, not a logic input. Datasheet: to
turn the switch *off* needs V_CE > V_IN + 80 mV = **3.38 V** with V_IN = SENSOR_3.3V.
An nRF52840 GPIO reaches VDD — **3.3 V at most**. It turns the switch on; it cannot
turn it off. The standby saving the whole architecture depends on is the thing that
does not work.

**Cheapest fix uses a part already traced here:** a second **TPS7A2033** from VSTOR,
output SENSOR_MCU_3V3, with its **logic-level EN (pin 3)** on the GPIO. Same footprint
as U3, already verified against DQN0004A, and it deletes the LM66100 from the BOM.
Not applied — swapping a part is your call, not an unattended session's. The netlist is
wired as this brief specifies, with the flag on it.

### B4 — J11-4 cannot be read as a digital backlight flag

The brief says `J11-4 --[1M/220k]--> MCU GPIO`. **Your own measurements rule that out.**
`Pin Test Results.md`: J11-4 reads **0.316 V awake and 0.000 V asleep**, source 3–6 Ω.
Both sit far below any digital V_IL, so a GPIO cannot tell them apart — and a 1M/220k
divider would shrink 0.32 V to 0.06 V, into the ADC's offset.

The netlist uses **100 kΩ series into an SAADC pin, read as an analog value**, threshold
≈ 0.15 V. Confirm that is acceptable. Note DESIGN-SPEC §9 already says this flag is
optional — the 10 µA sensor standby removed the need for backlight gating.

### B5 — SENSOR_3.3V has no headroom at end of discharge

U3 is a **fixed 3.3 V** LDO fed from VSTOR, which falls to **3.0 V** at the cell's
discharge cut-off. Below about 3.3 V + dropout the output simply follows the input
minus dropout, i.e. **under the ZW0905's 3.0 V minimum**.

So the firmware floor is **not 3.0 V** as this brief states — it is 3.0 V plus U3's
dropout at 25 mA. **That dropout figure was not traced**; get it from the TPS7A2033
datasheet and set the firmware floor from it. Losing the bottom of the discharge curve
costs real capacity out of only 77 mAh.

### B6 — The CP1254 A4 requires a protection module and there isn't one

VARTA states on the face of the datasheet: *"Cell must not be used without external
safety electronics (PCM)."* BQ25505's VBAT_OV covers overcharge and firmware can cover
undervoltage, but neither is what VARTA means and neither covers a short.
Decide: source the cell as a tabbed assembly with a PCM fitted, or add a protection IC.
Either costs board area or stack height that is not currently budgeted.

### B7 — nRF52840 REG0: DC/DC or LDO?

DC/DC needs a **10 µH 0603, I_DC ≥ 80 mA** between DCCH (31) and VDDH (30); LDO mode
does not. Raytac §8.1–8.3 are drawings that would not extract, so the exact DCCH
treatment for LDO mode is unconfirmed. `C11` in the netlist is a placeholder.
Worth noting the stake is small: the nRF is ~16 % of the daily budget and LDO mode
wastes ~29 % of that — under 5 % of the total, against 6× margin. **Board area probably
wins.** Confirm from Raytac §8.2 before layout.

### B8 — 22 µH inductor `C2849435`: package, height and DCR all unknown

The LCSC page could not be reached. Height is the dimension that matters most here.
For comparison only — **not a substitution** — TI characterised the BQ25505 with a
**Coilcraft LPS4018-223, 4.0 × 4.0 × 1.8 mm**. A 1008 part at the same inductance will
have materially higher DCR, which costs boost efficiency at the µA input currents this
design actually runs at.

### B9 — BQ25505 VBAT_OK divider targets

Not specified in the brief. The netlist picks rising 3.47 V / falling 3.12 V, sitting
just above the CP1254's 3.0 V cut-off. Sign this off, or change it — it couples to B2.

---

## 7. Session log

**2026-08-27, unattended. Tasks A–D done; Task E blocked on B1 and not started.**

Four tasks finished properly rather than five started, per the brief.

### Task A — verified part library ✔ → `PART-LIBRARY.md`

Every dimension carries its source. Traced from vendor drawings:

- **BQ25505** VQFN-20 **RGR0020A 4219031/B**: perimeter pads 0.60 × 0.24 at 0.5 pitch,
  span 3.3, thermal land 2.05 sq, 4 × Ø0.2 vias at ±0.775, stencil 4 × 0.92 at ±0.56.
- **The BQ25505 mask trap is NOT the DQN trap, and the difference matters.** The
  DQN0004A drawing is explicitly annotated *SOLDER MASK DEFINED* — that is what cost
  order Y6. RGR0020A carries only the **generic** both-options detail box, with
  `NON SOLDER MASK DEFINED (PREFERRED)`. So the choice is ours, and NSMD is TI's
  preference: **copper 0.60 × 0.24, mask +0.07 per side**. Written up with the reasoning
  so nobody re-derives it.
- **LM66100** SC-70-6 **DCK0006A 4214835/D**: pads 0.9 × 0.4, pitch 0.65, rows 2.2
  apart, NSMD, mask +0.07.
- **MDBT50Q** electrical, from **Ver. K**: **VDDH is pin 30 — confirmed.** VDD's
  absolute max is **3.9 V**, so a 4.25 V cell on VDD would exceed it by 350 mV; VDDH
  takes 5.8 V. VDDH operating range 2.5–5.5 V, and the cell floor is 3.0 V. The
  instruction now has a datasheet number behind it.
- **CP1254 A4**, VARTA data sheet 2020-02-18: 77 mAh typ, Ø12.1 +0/−0.3,
  **5.4 +0.2/−0.1**, charge 4.30 ± 0.05 V, 210 mA pulse, < 0.5 Ω, charge 0–45 °C.

Three corrections to existing notes:

| Note said | Actually |
|---|---|
| Harvesting PMICs "out of spec above 3.3 V input" | True of the '504. **BQ25505 VIN_DC is specified to 5.1 V.** The choice of the '505 is right, and this is why |
| MDBT50Q "not at LCSC" | **JLCPCB lists it as `C5118826`** |
| CP1254 "Ø12.1 × 5.4" | **5.4 +0.2 → 5.6 max.** A pocket cut for 5.4 will not close |

**VBAT_OV verified independently.** TI's worked example gives
`VBAT_OV = 1.5 · VBIAS · RSUM / ROV1`. With your 5.6 M / 7.5 M: RSUM 13.1 MΩ (inside
11–15), **VBAT_OV = 4.246 V**. Against a 4.30 ± 0.05 V charge spec that is safe and
slightly conservative. The "max 4.00 V" that turns up in searches is VARTA's footnote 3
and applies only to *rapid* charge at 140 mA — a rate harvest cannot approach.

### Task B — housing v5 ✔ → `touchid_module_v5.py`, `HOUSING-V5-NOTES.md`

v4 untouched. Riser OD 18.37 / ID 15.60, z 7.16 → 11.66, wall 1.385. Top face 11.66,
barrel bottom **9.46** — both exactly as specified. STEP + STL exported, plus an
assembly with the cell, module and sensor in place.

**All eight boolean checks return 0.0000 mm³**, zmin −0.0000, zmax 11.6600.

**The model disagrees with the brief and, as instructed, the model wins:**
clearance above the cell is **1.41 mm, not 2.26**.

- −0.20 — the cell is **5.6 mm** worst case, not 5.4.
- −0.65 — the cell **cannot sit at z 1.80**. The MDBT50Q is 2.05 tall and the Ø12.1
  cell sits entirely inside its 15.5 × 10.5 footprint, so z 1.80 would put the cell
  through the module. v5 places it at **2.45**, allowing 0.40 mm because the module lid
  is a grounded shield and the cell can is live.

1.41 mm is still a fit, and it is air. Design decisions taken: the cell rests on two
ledges at ±Y (never on the module), and the centring collar is **two arcs, not a ring**,
leaving ±X open for the six sensor wires to reach J2.

### Task C — antenna orientation ✔ → `ANTENNA-ORIENTATION.md`

**Board-local +Y is the spacebar edge.** `DESIGN-SPEC.md` §2 was **correct as printed**;
the extraction quoted in this brief applied a sign flip the file does not call for.

The `touchid_board` footprint sits at the origin with **rotation 0**, so pad `(at x y)`
*is* `global − origin` — no rotation, no flip. Two independent routes to the answer:

1. **Block shape, using no pad names.** J4 has three rows, J11 two, and your procedure
   shows both flush at the rear. In the file they share the −7.2 and −4.7 rows; J4's
   unshared row is at **−2.220**. So −7.2 is the rear and increasing y is the front.
2. **The ground pin, using a meter reading.** J4-5 is the only J4 pad with a net and it
   is `GND`; the procedure puts J4-5 bottom-left = front-left. In the file it is at
   (−7.200, −2.220) — leftmost x, least-negative y.

Confirmed a third time against the keepout zones, which read +2.950…+9.300 local with
no flip.

**Root cause found and fixed.** DESIGN-SPEC §1 said both *"local = global − origin"* and
*"local +Y is KiCad-up"*. KiCad's file Y increases **downward**, so those contradict;
every table follows the first and is right, and anyone trusting the second negates Y and
gets the board back to front. §1 now says
*"+Y is toward the spacebar; −Y is toward the screen"*, with the warning callout.

**Consequence: pcb-v2's antenna already points at the spacebar.** Task E *preserves* the
orientation rather than reversing it. Free of pogo copper on every layer: **10.770 mm
deep × 19.30 wide** at the +Y edge. The ESP32's existing keepout is 13.255 × 6.350 and
already fits; the MDBT50Q is 2.7 mm narrower. That is a **bound, not the proof asked
for** — the real keep-out numbers are B1.

> Flagged for Task E: pushing U1 to +y so the antenna reaches the edge collides with
> v5's cell ledges. The fix is a rotation — move the ledges to ±X — but then the wire
> windows land at ±Y while **J2 sits at x = ±7.60**. Decide before drawing pcb-v3, then
> re-run `touchid_module_v5.py` with the real `mcu_center`; it re-runs every boolean.

### Task D — schematic ✔ → `cad/pcb-v3/netlist_v3.py`

Executable and self-checking, so it cannot drift out of agreement with itself.
**44 parts · 176 pins · 50 deliberate no-connects · 28 nets · no single-pin nets · all
pin counts match the datasheets.**

Corrected J2 pinout used throughout. SWD pads and ten bottom-side test points placed.
BQ25505 wiring per SLUSBJ3F: VOC_SAMP → GND for VOC/2, EN → GND, the three NC pins tied
to the PowerPad/GND, VB_PRI_ON / VB_SEC_ON / VBAT_PRI left floating as the datasheet
directs.

One deviation, deliberate and documented: the brief says "BQ25505 VBAT ↔ cell", but the
part has **no pin called VBAT**. TI's own topology (Figure 16) puts the cell on
**VBAT_SEC (18)** and the system load on **VSTOR (19)**, connected through the internal
PFET. The netlist follows TI.

Six FLAGS ride in the file itself and print on every run — B2 through B7 above. They are
open **design** questions, not wiring errors.

### Task E — board layout ⛔ not started

Blocked on **B1**. U1 and L1 are the two largest parts and neither has a verified land
pattern, so placement and routing cannot begin without inventing one — the exact thing
rule 1 forbids and that this project has already paid for once.

Groundwork done instead, so whoever picks it up starts from checked facts:

- **Baseline re-verified.** `sexp_check` 95 pads / 175 tracks / 18 vias / 2 zones,
  5522 CRLF, **0 bare LF**. `check_board`: **exactly one** sub-0.127 pair, `+3V3`/`VBAT`
  at 0.1270. `check_connect`: **2 nets split**, GND and VBAT. Reproduces DESIGN-SPEC §8
  precisely — the carried-over fix list is grounded, not copied.
  (Both checkers need `shapely`; it is not installed by default.)
- **The J2 paste issue is real and confirmed pad-by-pad.** All six J2 pads carry
  `F.Paste`. 80 pads have F.Paste, 0 have B.Paste.
- **New constraint for Task E:** J2 sits at y **+2.900 … +5.900** — in the spacebar
  half, the same half as the antenna keep-out. It clears the current keepout in x by
  only **0.40 mm** (pad edge 7.000 vs keepout 6.600). The MDBT50Q being 2.7 mm narrower
  than the ESP32 should relieve this, but it must be checked, not assumed.
- `cad/pcb-v2/extract_pogo.py` added — read-only, paren-matches pad blocks and prints
  its counts first, so it cannot go blind the way trap 3 describes.

**No `pcb-v3.kicad_pcb` was created.** A board file containing an outline and ten pads
but neither of the two parts that set the layout would look like progress and is exactly
the artifact trap 4 warns about.

### Housekeeping

Committed at each milestone: `20ee63d` A · `060b5a0` B · `0a63d3e` C · `cfafbf6` D.
`pcb-v2.kicad_pcb` and `touchid_module_v4.py` were **not modified**. Nothing was
ordered, priced or added to a cart.

One snag worth knowing: git left stale `.git/*.lock` files that the sandbox could not
unlink, which blocked committing until file deletion was granted for the folder. If a
future session sees *"Another git process seems to be running"*, that is what it is.
