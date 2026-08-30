---
title: TouchID master design spec — every verified dimension and constraint
type: project
tags:
  - touchid
  - hardware
  - spec
  - master
updated: 2026-08-29
---

# TouchID — master design spec

**This is the authoritative reference.** Every number here was verified against a
vendor drawing, a caliper measurement, or a boolean/geometric check — not taken
from a spec table, a generator script, or a screenshot. If another note in this
vault disagrees with this file, this file wins and the other note is stale.

Read this before changing anything. Sources of truth, in order:

| Thing | Authoritative file |
|---|---|
| **Status: what is decided, ordered, open** | **`CURRENT-STATE.md`** |
| The board | `cad/pcb-v3/pcb-v3-handoff.kicad_pcb` |
| The housing | `cad/scripts/touchid_module_v5.py` → `cad/v3-handoff/housing/` |
| The netlist | `cad/pcb-v3/netlist_v3.py` — **`NETLIST-V3.md` is generated, do not hand-edit** |
| Sourcing / BOM | `cad/pcb-v3/make_bom_cpl.py` → `cad/v3-handoff/assembly/` |
| The sensor | `cad/pcb-v3/SENSOR-ZW0922.md` |
| The cell | `cad/pcb-v3/CELL-DECIDED.md` |
| Go/no-go before ordering | `cad/pcb-v3/preflight.py` |
| Superseded notes — **do not take numbers from here** | `_archive/` |

> The v2-era pointers this table used to carry (`pcb-v2.kicad_pcb`,
> `touchid_module_v4.py`, `pcb-v2/OPEN-ISSUES.md`) were **three revisions stale**.
> Those files still exist and are deliberately untouched, but they are history,
> not authority.

> [!warning] Sections 2, 3 and 6 describe a board that is being replaced
> Every dimension in them is still correct **as a record of what was drawn**, and the
> outline, mounting holes, pogo positions and housing all carry forward unchanged.
> But **U1 (ESP32-C3-MINI-1), U2 (TPS7A2033) and the whole VBAT path are dead** —
> the slot supplies no power. See **§9 Power architecture** below, which is the
> current thinking, and [[touchid/Pin Test Results|Pin Test Results]] for why.

---

## 1. Coordinate conventions — get this right first

**Board (KiCad):** footprint origin at global (148.5011, 105.0036). Board-local
coordinates in this document are `global − origin`, **keeping KiCad's Y-down file
convention — do not negate Y**. Board-local **+Y is toward the spacebar**; −Y is
toward the screen.

> [!warning] Corrected 2026-08-27 — this line used to say "+Y is KiCad-up"
> That was wrong and it cost a session. KiCad's file Y increases downward, so under
> `global − origin` the pogo pads at local y −7.22 are KiCad-**up**, and local +Y is
> KiCad-**down**. Anyone who negated Y to satisfy the old sentence got the J4 pads at
> +1.12…+8.32 instead of −8.32…−1.12 and had the board back to front.
> Every table in this file follows `global − origin` and is correct as printed.
> Full derivation, with two independent confirmations from the file:
> [[touchid/ANTENNA-ORIENTATION|Antenna orientation]].

**Housing (CadQuery):**
- `Z = 0` is the housing back plane **and** the PCB top face
- PCB occupies `z −1.2 … 0`
- **Nothing on the housing may go below z = 0.** The PCB underside at −1.2 is the
  module's lowest plane, so the pogo pads are the only things that can touch the
  keyboard.

**Height — this section was STALE until 2026-08-28.** It read "flush top face at
`z = +7.16`; total module height **8.36 mm**". That is **v4**. v5 added the riser
column and the numbers moved:

| | v4 (what this spec used to say) | v5.0 | **v5.2, as built** |
|---|---|---|---|
| riser | — | 4.50 | **6.50 mm** |
| top face | z 7.16 | z 11.66 | **z 13.66** |
| total module height incl. PCB | 8.36 mm | 12.86 mm | **14.86 mm** |
| sensor barrel bottom | z 4.96 | z 9.46 | **z 11.46** |
| cell pocket | — | Ø12.50 | **Ø14.00** |
| clearance above cell | — | 1.61 mm | **0.81 mm** |

> [!success] **The riser costs nothing — the module stands proud by design.**
> **Corrected 2026-08-29.** This box previously called the riser height "the
> biggest open risk in the project" and demanded a slot measurement. It was
> wrong, and it stood for nine days.
>
> The module does not sit *in* a slot. It **seats on the pogo pins**; the
> housing lip props against the keyboard's enclosure; the rear retention shelf
> slides under the metal top case as a pivot; and a countersunk **M2** screw
> through the mounting arm holds the opposite corner down. There is nothing
> above the module to run out of.
>
> **The 8.36 mm comparison was the wrong question.** That is the knob module's
> height, and the knob sat flush because it had nothing on top of it. Ours
> carries a fingerprint sensor that has to be reachable, so standing proud is
> the intended geometry, not an overrun.
>
> The dimensions that actually locate the module were caliper-measured from the
> start and are unchanged: top tier **18.52**, lip **19.66**, rear shelf
> **11.00 × 1.18 × 2.62**, arm width **5.12**, arm-tip-to-opposite-lip-corner
> diagonal **30.14**. `riser_h` is free to be chosen on cell fit and ergonomics
> alone.

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
| Back connector | XH-1.00-6P, 4.50 tall — **must be desoldered**, wires go to the pads |
| Protocol | **0xEF01**, UART 3.3 V, 57600 default |
| **Supply voltage** | **3.0 min / 3.3 typ / 3.6 max** |
| **Standby current (sensor rail)** | **8 / 10 / 12 µA** |
| **Operating current (algorithm MCU)** | **— / 15 / 25 mA** |

Source: `datasheets/HLK-ZW0905-Specification-V1.0.pdf` §3, obtained 2026-08-27.
Protocol manual: `datasheets/HiLink-Fingerprint-Protocol-0xEF01-V1.1.pdf`.

### Pinout — CORRECTED 2026-08-27

| Pin | Function |
|---|---|
| 1 | SENSOR_3.3V |
| 2 | WAKEUP |
| 3 | MCU_3.3V |
| 4 | TX |
| 5 | RX |
| 6 | GND |

> [!danger] The old pinout in this file was the ZW0901's, not the ZW0905's
> It read `1 GND, 2 RXD, 3 TXD, 4 VDD, 5 Detect, 6 SENSOR` — **reversed**. The claim
> that "J2's existing nets already match" was therefore **wrong**: GND and both 3.3 V
> rails were in the wrong positions. Any board built to the old table would have had
> ground and power swapped end-for-end. Re-check J2's net assignment before ordering.

Two separate 3.3 V rails is still correct, and it is what makes the power design work:
**MCU_3.3V is switched off in standby while SENSOR_3.3V stays powered**, drawing 10 µA
and waiting for a finger. WAKEUP is the output that tells us one arrived.

> [!warning] Two electrical requirements from §3 that affect the board
> 1. **200 mA peak for 4 µs** on the sensor rail during each finger-detect scan.
>    Hi-Link requires sensor-rail ripple **< 200 mV** and recommends a dedicated LDO
>    rated ≥250 mA with PSRR > 60 dB, routed separately from other loads. A local
>    10 µF holds the droop to 80 mV; 22 µF to 36 mV.
> 2. **Pull RX and TX low when the MCU sleeps**, or they leak enough to spoil the
>    10 µA standby figure.

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

## 9. Power architecture

> [!danger] The slot supplies no power
> J11-1/2/3 are **PWM RGB LED drive lines**, not a battery rail. J4 is the
> switch/encoder block. The 2026-08-18 architecture (J11 → LDO → ESP32-C3) is dead.
> Proven by meter *and* by physical inspection: the knob module has no J11 contacts
> and no LED; the button module has all four and an RGB LED.

### The one live possibility: harvest the LED rail

The keyboard turns a module's LED off by **opening the return** (J11-4), not by
dropping the anodes — no continuity J11-4 → J4-5, confirmed 2026-08-26. So while
the backlight sleeps, J11-1/2/3 sit at **3.530 V** through their per-colour limit
resistors with no path through the LED.

Current drawn from those pins and returned through **J4-5** (real chassis ground)
never enters the LED. It lights nothing and dims nothing.

### Load budget — rebuilt on datasheet numbers, 2026-08-27

| | mWh/day |
|---|---|
| 50 scans at **25 mA max** for 1.5 s | 1.93 |
| Sensor standby, 10 µA continuous | 0.89 |
| nRF52 sleep, ~6 µA | 0.53 |
| **Total, worst case** | **≈ 3.3** |
| Total using typical figures (15 mA, 1.0 s) | ≈ 2.2 |

Earlier revisions of this file assumed 50 mA scans and an unknown standby, giving
5.5 mWh/day. The real numbers are **roughly 40% lower**, and the 10 µA standby means
**no press-wake or backlight-gating trick is needed** — the sensor can sit in detect
mode permanently for 0.89 mWh/day.

### Measured harvest — RESOLVED 2026-08-27

Four states measured at 300 Ω on J11-1. **Wired vs wireless is irrelevant. Backlight
awake vs asleep is everything — a 35× difference.**

| State | V open | V @300 Ω | Current | Source R | P at MPP, ×3 pins |
|---|---|---|---|---|---|
| wireless · asleep | 3.758 | 0.101 | 0.34 mA | **10,862 Ω** | 0.98 mW |
| wired · asleep | 3.922 | 0.102 | 0.34 mA | **11,235 Ω** | 1.03 mW |
| wireless · awake | 2.808 | 1.358 | 4.53 mA | **320 Ω** | **18.5 mW** |
| wired · awake | 2.985 | 1.548 | 5.16 mA | **278 Ω** | **24.0 mW** |

The awake figures line up with session 3's 231 Ω. The asleep state is a weak pull-up
inside the driver, not a live rail — when the backlight sleeps the high side switches
off.

**Ground-path control test passed cleanly**: 0.096 V on the `−` rail and 0.096 V on the
USB-C shell, identical. The contact was honest and these numbers are real.

Against a **3.3 mWh/day** load, the awake state needs only **11 minutes of backlight per
day** to break even. The asleep state alone would need 3.4 hours. Both contribute.

> [!warning] Direct-connect harvesting does not work in either state
> Asleep the source is 3.9 V open-circuit into a 3.5–3.7 V cell — a plain diode drives
> ~16 µA. Awake the open-circuit average is only 2.8–3.0 V, i.e. **below** the cell.
> A **boost converter with MPPT** is required in both cases.

> [!danger] Do not let the MPPT run at full aggression while the backlight is awake
> BQ25505 at VOC/2 would draw **4.4–5.4 mA per pin, 13–16 mA total** — above the
> 10.7 mA that visibly dimmed nearby keys in session 3.
>
> Fix: a **series resistor on each pin**. It caps the awake draw and barely touches the
> asleep case, which is already 11 kΩ.
>
> | R series | Awake, 3-pin total | Power ×3 | 4 h/day | Margin |
> |---|---|---|---|---|
> | none | 14.6 mA | 21.1 mW | 84 mWh | 26× |
> | 470 Ω | 5.7 mA | 8.2 mW | 33 mWh | 10× |
> | **1 kΩ** | **3.3 mA** | **4.9 mW** | **19 mWh** | **6×** |
> | 2.2 kΩ | 1.7 mA | 2.5 mW | 10 mWh | 3× |
>
> **1 kΩ is the sensible pick** — a third of the level that dimmed anything, still six
> times the daily budget on four hours of backlight. Verify against real keys before
> committing; the threshold is empirical.

One consequence for the layout: when the backlight is awake the pins carry PWM, so the
"open-circuit" voltage the MPPT samples is a chopped average. The input capacitor needs
to give the sampler something stable to read.

> [!success] Proven 2026-08-27 — harvest while the backlight is on
> The loaded-while-asleep measurement is done and the answer is that **asleep is
> useless (11 kΩ) and awake is excellent (~300 Ω)**. The module harvests while you
> type and coasts on the cell the rest of the time — which fits, because the backlight
> is on exactly when you are at the keyboard. Data and thresholds in the table below.
> Loggers: `two-tests.html`, `harvest-test.html`.

### Storage must be a cell — supercapacitors are ruled out

Three independent failures, any one fatal:

1. **Energy.** The load needs 3.3 V, so a 1 F cap is usable only from ~3.46 down to
   3.30 V — **0.54 J ≈ 42 minutes** against 18.9 J/day. (An earlier "1 F rides four
   hours" figure was wrong: it assumed draining to 2.0 V, which needs a boost
   converter there is no room for.)
2. **Nothing fits.** No part is simultaneously ≥3.3 V rated, low-ESR enough for a
   50 mA pulse, and inside 17.94 × 17.94 × 4.96. CAP-XX's smallest footprint is
   20 mm; Kyocera AVX SCC and Eaton HS are Ø6.3; Eaton KR coin cells are 30–75 Ω ESR;
   SII CPH3225A fits but is 11 mF at 160 Ω.
3. **Headroom.** 3.466–3.680 V source into a 3.3 V load = **166 mV total droop
   budget**, capping storage impedance at 3.3 Ω.

**VARTA CP1254 A4** (77 mAh, <0.5 Ω, 210 mA pulse) is electrically ideal and fails
geometrically twice: 5.4 mm against a 4.96 ceiling, and Ø12.1 cannot be packed beside
any BLE module in a 17.94 square (12.1 + 7.1 = 19.2). That leaves a **semi-custom
thin LiPo strip, roughly 2.5 × 10 × 16 mm, ~20–35 mAh**, beside the module.

> [!danger] Do not draw a pad for a pouch cell from a format code
> `TTWWLL` naming is reliable but internal resistance is not inferable, and it spans
> "fine" to "fails the 166 mV budget." Get a vendor mechanical drawing **and** a
> measured IR/max-discharge spec before any footprint exists. Same failure mode as
> the invented U1/U2 land patterns.

### Power path — ~18 mm², no charger, no PMIC, no supervisor

```
J11-1/2/3  (3.530 V idle when backlight sleeps)
   └─ 3 × LM66100 ideal diode, ORed          SC-70-6, 2.1 × 2.0, 91 mΩ
        └─ cell + bulk cap
             ├─ nRF52 module (direct, 1.7–3.6 V)
             └─ LM66100 #2 as load switch ← MCU GPIO
                  └─ HLK-ZW0905, ~50 mA × 1.5 s
   J11-4 → 100 kΩ pull-up → MCU GPIO         "backlight awake" flag
   return: J4-5 only, never J11-4
```

Three deliberate deletions, each with a reason:

- **No Schottky.** PMEG2005AEL drops 220 mV at 100 mA — more than the entire 166 mV
  budget, and leaks 210 µA against a 62.5 µA average. LM66100 costs 4.6 mV.
- **No charger IC.** MCP73831 needs ≥3.75 V in and this source maxes at 3.68 V. Not
  needed either: a source that cannot exceed 3.68 V **cannot overcharge a 4.2 V
  cell**. It self-limits at ~25–30% SOC. Gate charging on temperature in firmware —
  Li-ion must not charge below 0 °C.
- **No harvesting PMIC, no supervisor.** BQ25504/ADP5091 are out of spec above 3.3 V
  input; every such chip exists to boost sub-volt sources. Boosting 3.5 V → 3.5 V
  loses ~15%; two ideal diodes lose 0.26%. The nRF52's own SAADC reads storage
  voltage and drives the load switch with arbitrary hysteresis, for zero board area.

### MCU shortlist — BLE only, integrated antenna

| Part | Size (mm) | LCSC / JLC | 4.2 V direct | Note |
|---|---|---|---|---|
| **Fanstel BC840** | 7.1 × 9.2 × 1.5 | C5155822, in stock | **yes, VDDH 5.5 V** | narrowest *and* thinnest; ~$17; keep-out 2.5 mm **unverified** |
| **Holyiot 17095** | 9.4 × 9.25 × **?** | **C9900031218** | no | in JLCPCB's SMT catalog → verified land pattern; **height unstated in the datasheet** |
| Raytac MDBT50Q | 15.5 × 10.5 × 2.05 | not at LCSC | yes, VDDH pin 30 | best-documented; 10.5 mm buys only 2.7 over the ESP32 |

Ruled out: **ESP32-H2-MINI-1** is 13.2 × 16.6 — identical to the C3, zero gain.
**u-blox ANNA-B112** is 6.5 × 6.5 but needs an antenna tuning strip drawn on the host
board and **cannot sit in a metal enclosure** — the keyboard's top frame is metal.
No non-Nordic module accepts 4.2 V. TI CC2652RSIP has no integrated antenna.

### Keyboard setting: button, not knob

The button module is the variant that carries J11 contacts and an RGB LED, so it is
the one to model on. A fingerprint reader you press *is* a button. And in knob mode
any stray leakage on J4-1/3/4 reads as volume/mute events — session 3 loaded J4-4 and
it muted the PC and zoomed Chrome.

Note J11 was live and PWMing in **every** measurement, all of which were taken with
the slot **empty** — so the keyboard drives J11 unconditionally and does not gate it
on module presence. Harvesting therefore does not depend on the setting.

### Still open

- [ ] **The 330 Ω loaded-while-asleep test.** Gates everything above.
- [x] ~~ZW0905 minimum operating voltage~~ — **CLOSED 2026-08-27: 3.0 V min.** The
      droop budget is 500 mV from a 3.5 V cell, not 166 mV. Comfortable.
- [x] ~~ZW0905 standby current~~ — **CLOSED 2026-08-27: 10 µA typ, 12 µA max.**
      No press-wake trick needed; the sensor can sit in detect mode permanently.
- [x] ~~Sensor active current~~ — **15 mA typ / 25 mA max**, not the 50 mA assumed.
      Halves the per-scan energy.
- [x] ~~**ZW0905 availability.**~~ **CLOSED 2026-08-28 — it happened. The seller
      confirms the ZW0905 is DISCONTINUED. Replacement: HLK-ZW0922.**
      This item was right to be open, and the delisted product pages were the
      tell. **The ZW0922 is a drop-in** — flange Ø18.00 ±0.05, barrel
      Ø15.50 ±0.05, step 0.20 ±0.05, identical 6-pin order
      (sensor_3.3V / WAKEUP / MCU_3.3V / TX / RX / GND), identical electricals
      (10 µA standby, 15–25 mA active, 200 mA × 4 µs FD peak, <200 mV ripple).
      It is 2.15 ±0.20 thick vs the 2.40 modelled, which *adds* clearance above
      the cell. **No board change, no housing change.** Full analysis:
      `cad/pcb-v3/SENSOR-ZW0922.md`.
      **The Φ12.8 mm trap is in the ZW0922 spec table too** — that is the sensor
      package, not the module. Read the §2.3 drawing, never the table.
- [x] **Slot depth — RESOLVED 2026-08-29, and it was never a constraint.**
      The module does **not** drop into a deep slot. It **seats on the pogo
      pins and stands PROUD**: the housing lip props against the keyboard's
      enclosure, the rear retention shelf slides under the metal top case as a
      pivot, and the mounting arm's countersunk M2 screw holds the opposite
      corner down. Nothing constrains `riser_h` from above.

      The geometry that DOES locate the module was measured off the knob module
      all along and is unchanged: top tier **18.52**, lip **19.66**, rear shelf
      11.00 x 1.18 x 2.62, arm width 5.12, arm-tip-to-opposite-lip-corner
      diagonal 30.14. Those are the numbers that matter, and they are calipers,
      not estimates.

      This retires the "highest-value measurement in the project" framing that
      sat here for nine days. The height comparison against the 8.36 mm knob
      module was never the right question -- the knob sat flush because it had
      nothing on top of it; ours has a sensor you have to touch.

- [ ] Pogo pad positions re-verified now the outline is square
- [ ] If harvest fails: trace **J4-2 and J4-6** for a keyboard-battery tap

## Related

- [[touchid/cad/pcb-v2/OPEN-ISSUES|Open issues]]
- [[touchid/cad/pcb-v2/PCB-IMPROVEMENTS|PCB improvements]]
- [[touchid/Module Mechanical v3|Module mechanical v4]]
- [[touchid/JLCPCB DFM Report|JLCPCB DFM Report]]
- [[touchid/Sensor Connector Plan|Sensor connector plan]]
