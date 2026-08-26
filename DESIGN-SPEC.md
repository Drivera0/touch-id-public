---
title: TouchID master design spec — every verified dimension and constraint
type: project
tags:
  - touchid
  - hardware
  - spec
  - master
updated: 2026-08-20
---

# TouchID — master design spec

**This is the authoritative reference.** Every number here was verified against a
vendor drawing, a caliper measurement, or a boolean/geometric check — not taken
from a spec table, a generator script, or a screenshot. If another note in this
vault disagrees with this file, this file wins and the other note is stale.

Read this before changing anything. Sources of truth, in order:

| Thing | Authoritative file |
|---|---|
| The board | `cad/pcb-v2/pcb-v2.kicad_pcb` |
| The housing | `cad/scripts/touchid_module_v4.py` → `cad/exports/touchid_housing_v4_*.step` |
| What was actually manufactured | `cad/pcb-v2/production-file-old-version.zip` (order Y6, scrap) |
| Outstanding work | `cad/pcb-v2/OPEN-ISSUES.md` |

---

## 1. Coordinate conventions — get this right first

**Board (KiCad):** footprint origin at global (148.5011, 105.0036). Board-local
coordinates in this document are `global − origin`. Board-local +Y is KiCad-up.

**Housing (CadQuery):**
- `Z = 0` is the housing back plane **and** the PCB top face
- PCB occupies `z −1.2 … 0`
- Flush top face at `z = +7.16`; total module height **8.36 mm** including the PCB
- **Nothing on the housing may go below z = 0.** The PCB underside at −1.2 is the
  module's lowest plane, so the pogo pads are the only things that can touch the
  keyboard.

**Altium ↔ KiCad Gerber transform** (verified, do not re-derive):
```
kicad_x = gerber_x + 48.5011
kicad_y = 113.8036 − gerber_y      <-- Y IS MIRRORED
```

---

## 2. Board

| | Value |
|---|---|
| Outline | **19.30 × 19.30 mm, R2.0 corners** (was 19.60 × 17.60) |
| Thickness / layers | 1.2 mm, 2 layer, 1 oz, ENIG |
| Area | 369.04 mm² |
| Mounting holes | **Ø1.30 at (+8.10, −8.10) and (−8.10, +8.10)** — diagonal |
| Nets | 9: `+3V3, BOOT_IO9, FP_INT, FP_RX, FP_TX, GND, USB_DN, USB_DP, VBAT` |
| Object count | 95 pads, 175 tracks, 18 vias, 2 zones |
| Track widths | 0.254 main, 0.15 on U2's escape |
| Vias | Ø0.6 / drill 0.3 |

**Why only that one diagonal is possible:** the (−,−) corner is permanently
blocked by pogo pad **J4-1**, whose position is set by the keyboard. The (+,−)
corner needed C4 moved. Both (+,+) and (−,+) are clear but adjacent, not diagonal.

**Board outline nominal 19.30 vs the 19.54 housing lip:** JLCPCB's outline
tolerance is ±0.2, so worst case 19.50 — still inside. **Do not go bigger.**

### Component positions (board-local)

| Ref | Position | Notes |
|---|---|---|
| U1 | centred; body x ±6.60, y ±8.30 | courtyard 13.6 × 17.0; copper x ±6.30, y −8.00…2.60 |
| U2 | (−7.60, −3.00) | |
| C1 | (−7.60, −4.80) | 0402 |
| C2 | (−7.60, −6.70) | 0402 |
| C3-1 / C3-2 | (7.600, −3.470) / (7.600, −1.630) | **moved +1.05 in Y** |
| C4-1 / C4-2 | (7.600, −6.520) / (7.600, −4.680) | **moved +1.20 in Y** |
| J2-1…3 | (−7.60, 2.90 / 4.40 / 5.90) | Ø1.2, 1.5 mm pitch |
| J2-4…6 | (+7.60, 2.90 / 4.40 / 5.90) | |
| J4 (pogo, B.Cu) | x −8.30…−3.60, y −8.32…−1.12 | Ø2.2 @ 2.5 mm pitch — **fixed by keyboard** |
| J11 (pogo, B.Cu) | x 2.35…7.05, y −8.30…−3.60 | **fixed by keyboard** |
| TP-DP/DN/IO9 (B.Cu) | (−2.00 / 0.00 / +2.00, 1.30) | Ø1.8 |

### Keepouts

- **Antenna keepout** (F.Cu + B.Cu): x [−6.66, 6.60], y [2.95, **+9.30**] —
  extended into the new space. The ESP32 antenna is at **board +Y** because the
  footprint is rotated 180°.
- The 16 board-edge keepouts were **deleted** — an artifact of the original
  Altium import; Altium enforces edge clearance by design rule.

---

## 3. Land patterns — all traced to vendor drawings

### U1 — ESP32-C3-MINI-1-N4, JLCPCB `C2838502`

61 pads, confirmed pad-for-pad against the as-ordered Gerber apertures:

| Count | Size | Role |
|---|---|---|
| 26 | 0.4 × 0.8 | perimeter |
| 22 | 0.8 × 0.4 | perimeter |
| 8 | 1.45 × 1.45 | thermal grid |
| 4 | 0.7 × 0.7 | corner |
| 1 | custom, chamfered | thermal slot 9 |

- Perimeter: 48 pads, **0.8 mm pitch**, 0.4 mm wide
- Thermal grid: 3×3 at x ∈ {−1.975, 0, +1.975}, y ∈ {0.725, 2.700, 4.675} (fp-local)
- **Chamfered thermal pad** at fp-local (−1.97501, 0.725), polygon
  `(0.725,0.725) (−0.725,0.725) (−0.725,−0.125) (−0.125,−0.725) (0.725,−0.725)`,
  on **F.Cu + F.Mask + F.Paste**. Global bbox x [149.7511, 151.2011],
  y [103.5536, 105.0036], cut corner +x/+y.
- Body 13.2 × 16.6 × 2.4 mm

> **CPL trap:** U1's placement origin is the **body centre**, not the pad-ring
> centre. They differ by **2.70 mm**. Getting this backwards misplaces the module
> by more than three pad pitches.

### U2 — TPS7A2033DQNR, X2SON-4 (DQN), JLCPCB `C46459900`

Source: TI package drawing **DQN0004A 4215302/E**.

| Feature | Value |
|---|---|
| Copper pads | **0.46 × 0.31** at (±0.43, ±0.325), inner corner chamfered 0.209289 |
| Mask opening | **0.36 × 0.21** (`solder_mask_margin −0.05`) |
| Thermal copper | **0.58 × 0.58 rotated 45°** |
| Thermal mask | 0.48 (margin −0.05) |
| Thermal paste | 0.45 (`solder_paste_margin −0.065`) |

> **The trap that cost a board:** TI's LAND PATTERN EXAMPLE is marked
> **SOLDER MASK DEFINED**. Its `4X (0.36)`, `4X (0.21)` and `⌀(0.48)` are
> **mask openings, not copper.** Copper is 0.05 mm larger on every side. Reading
> them as copper silently shrinks every pad.

Pinout (top view — **not** the SOT-23-5 order): 1 OUT/`+3V3`, 2 GND, 3 EN/`VBAT`,
4 IN/`VBAT`, 5 thermal/`GND`.

### C1, C2 — 1 µF 25 V X5R 0402, `C52923` (Samsung CL05A105KA5NQNC, Basic)

Pads 0.60 × 0.55, centres 0.96 → gap 0.41, span 1.51. **All four inside
Samsung's 1005 ±0.10 land table.** No change needed.

### C3, C4 — 47 µF 6.3 V X5R 0805, `C16780` (Samsung CL21A476MQYNNNE, Basic)

Pads **1.40 × 0.96**, centres **1.84** → gap 0.88, span 2.80. Inside Samsung's
2012 ±0.20 table on all four dimensions.

> Body is 2.00 × 1.25 × **1.25** mm — a **tall** 0805, not the common 0.85 mm
> part. Matters for housing clearance.

---

## 4. Housing v4

Source `cad/scripts/touchid_module_v4.py`. `MODE = "diagonal"` is the build that
matches the current board.

| | Value |
|---|---|
| Outer lip | **19.54 × 19.54**, R2.0 |
| Top tier | **18.37 × 18.37** |
| Lip height / body height | 2.90 / 7.16 (8.36 total with PCB) |
| **Lip wall** | **0.80** (was 1.40) |
| Lip cavity | **17.94 × 17.94** |
| Top plate | 2.00 |

**Why the wall came down:** at 1.40 the cavity was 16.74 and the ESP32 module is
16.6 long — **0.14 mm total clearance, 0.07 per side.** That is not a fit.
0.80 gives 1.34 total. Comfortable for moulding, thin for FDM.

### Fasteners

| | Value |
|---|---|
| PCB screws | **M1.2**, pilot Ø0.95, boss r1.20, boss height 4.0 |
| Positions | **(+8.10, −8.10) and (−8.10, +8.10)** on the corner diagonal |
| Ear screw | **M2 unchanged**, Ø2.0 hole, `ear_diag` 13.84, corner (−1,−1) |

`boss_c = 8.10` balances two opposing limits: moving **out** along the diagonal
buys clearance from U1 (0.00 at c=7.45, 0.31 at 8.10, 0.50 at 8.30) but eats the
outer wall (1.98 at 7.45, 1.06 at 8.10, 0.21 at 8.70).

> **Boss radius cannot exceed 1.202 mm anywhere on the diagonal** — that is the
> perpendicular distance from U1's corner (6.6, 8.3) to the line y = x. The
> corner buys position, not size.

### Sensor seat — Hi-Link HLK-ZW0905

**No counterbore.** The barrel locates in a **Ø15.60** window and the 0.20 mm
flange bears flat on the top face, bonded down. Press load still lands on
plastic, which was the point of the original seat.

- Window Ø15.60 in an 18.37 face → **1.39 mm of wall**
- ZW0905 flange Ø18.00 on that face → **0.185 mm margin per side** (essentially
  the whole top is sensor)
- Barrel bottom at z 4.96; U1 top at 2.40 → **2.56 mm for the hand-soldered wires**

Verified by boolean: housing ∩ U1 = 0.000 mm³, housing ∩ sensor = 0.000 mm³,
U1 ∩ sensor = 0.000 mm³.

---

## 5. Sensor — HLK-ZW0905

| | Value |
|---|---|
| Module outline | **Ø18.00 ±0.05** |
| Barrel | Ø15.50 ±0.05 |
| Total thickness | 2.40 ±0.20 |
| Flange (step) | **0.20 ±0.05** |
| Back connector | 4.50 tall — **must be desoldered**, wires go to the pads |
| Protocol | **0xEF01**, UART 3.3 V, 57600 default |

Pinout (ZW09xx family): 1 GND, 2 RXD, 3 TXD, 4 VDD 3.3 V, 5 Detect, 6 SENSOR 3.3 V.

**J2's existing nets already match** — `+3V3, GND, FP_TX, FP_RX, FP_INT, +3V3`.
Two 3.3 V pins is correct: VDD and the separate SENSOR rail.

> **Ø18.00 is the smallest round module that exists.** ZW0919 Ø18.10 ·
> ZW0901/ZW0906/ZW0623 Ø21.00 · ZW3020/ZW101/ZW111 Ø21 · GROW R502-B Ø22 ·
> R503 Ø28.

> **The spec-table trap:** vendors advertise these as "Φ12.8 mm" or "Φ14 mm".
> **That is the sensor package — the black window — not the module outline.**
> Hi-Link's own ZW3020 page lists both rows: module Φ21, package Φ13.6. Always
> open the §2.3 mechanical drawing and read 模组外形 (module outline).

---

## 6. The constraint that decides the layout

U1 is 13.2 mm wide in a 17.94 mm cavity, leaving **4.74 mm of spare width** to
split between the two sides.

- A top-side FPC connector needs **3.25** (2.90 body + clearances)
- A screw boss needs **2.60** even at M1.2

3.25 + 2.60 = **5.85 against 4.74**. To fit both you would need a cavity of
19.55, i.e. an outer envelope of 21.15 — larger than the whole 19.54 module.

**So it is a plug-in connector OR diagonal screws, never both.** Corner bosses
narrow the gap (short by 0.46 at M1.2 / 0.20 at M1.0) but only reach parity at
M1.0 on a 0.6 mm wall, at exactly zero margin. **We chose diagonal screws** —
which is free, because no small round sensor has a flex tail to plug in anyway.

For reference if this ever reopens: the connector would be JLCPCB `C5213748`
(HC-FPC-05-09-6RLTAG, 0.5 mm, 6-pin, 5.00 × 2.90 × **1.00**, land 3.30).
Vertical/top-entry FPC parts are **larger on all three axes**, not smaller.

---

## 7. Traps this project has already paid for

Each of these produced a confident wrong answer at least once.

1. **TI land-pattern dimensions are mask openings** when the detail says SOLDER
   MASK DEFINED. Copper is larger.
2. **Vendor spec-table diameters are the package, not the module.**
3. **Regex checkers go blind when the file format changes.** Correcting the net
   schema made `check_board` report `tracks 0` and every net `None` — while
   still printing a confident summary. Same class as the orphan-paren incident.
4. **Never trust a generator script as evidence of what shipped.** Reading
   `build_board.py` instead of the artwork produced a false accusation that U1
   was defective.
5. **Total-area comparisons hide redistribution.** U1's thermal copper matched
   to 0.2% while one pad was in the wrong place.
6. **Altium's KiCad importer maps every layer to copper** — verified via
   `get_pcb_layers`: 9 signal layers where there should be 2, with mask, silk,
   paste and the board outline all on copper. It renders convincingly.
7. **Writing the file in Python text mode converts CRLF → LF.** Write bytes.
8. **Deleting segment blocks silently deletes vias.** Print via counts before
   and after.
9. **A pad's own copper blocks its escape.** Exclude the source pad from its own
   obstacle map when routing.
10. **The board file had no net declarations at all** — `(net "NAME")` with no
    ordinal. Not KiCad's schema, so nothing could open it. That is why DRC was
    never run.

---

## 8. Verification commands

Run in this order. `sexp_check.py` must pass before any other result means anything.

```
cd cad/pcb-v2
python sexp_check.py    pcb-v2.kicad_pcb    # structure — run first, always
python check_board.py   pcb-v2.kicad_pcb    # clearance, honours pad shape
python check_connect.py pcb-v2.kicad_pcb    # per-net island count
```

Expected now: parses clean, 95 pads / 175 tracks / 18 vias / 2 zones, 0 bare LF;
**one** sub-0.127 pair (`+3V3`/`VBAT` at exactly 0.1270); **2 nets split** —
`GND` and `VBAT`, which is deliberate: C3-1, C3-2, C4-1 and C4-2 are the four
pads left unrouted for the autorouter.

Housing: `python cad/scripts/touchid_module_v4.py` prints the seat and clearance
figures and re-exports both modes.

---

## 9. New multimeter testing — TO FILL IN

You mentioned new measurements. Existing pin data is in
[[touchid/Pin Test Results|Pin Test Results]] (`cad/pin-test-results.csv`), which
currently records: J4-5 = GND, J11-1/2/3 = VBAT (3.680 V wired / 3.466 V
wireless), J4-1/3/4 pulled to 3.293 V, J11-4 floating.

Open questions that measurement should close:

- [ ] **Slot outline by caliper** — confirms the 19.30 board and the 19.54 lip
- [ ] **Slot depth / clearance above the pogo blocks**
- [ ] **Sleep sweep on J11-1** — does VBAT survive keyboard sleep?
- [ ] **Load test on J11-1** (100–330 Ω to J4-5) — does the rail hold ≥3.3 V
      through the pogo contacts under the ESP32's ~350 mA TX peaks?
- [ ] **Continuity J11-1/2/3** to each other — one rail, or three nets?
- [ ] **Pogo pad positions** re-verified against the keyboard now the outline is square

Paste the new readings here or into `Pin Test Results` and I will fold them in.

## Related

- [[touchid/cad/pcb-v2/OPEN-ISSUES|Open issues]]
- [[touchid/cad/pcb-v2/PCB-IMPROVEMENTS|PCB improvements]]
- [[touchid/Module Mechanical v3|Module mechanical v4]]
- [[touchid/JLCPCB DFM Report|JLCPCB DFM Report]]
- [[touchid/Sensor Connector Plan|Sensor connector plan]]
