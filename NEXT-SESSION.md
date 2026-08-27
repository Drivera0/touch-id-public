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

- _(nothing yet)_

---

## 7. Session log — append as you go

- _(nothing yet)_
