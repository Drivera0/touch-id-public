# TouchID Module — Design v3 (body caliper-measured)

Drop-in replacement for the NuPhy Air75 V3 knob module's slot (see [[touchid/docs/bench/Hardware Teardown|Hardware Teardown]]). Same envelope, but the top face is flat and flush with the metal enclosure, with a round fingerprint sensor centered in it.

Body envelope is now **caliper-measured** (2026-08-18): 18.64 × 18.64 mm body, 8.44 mm total height, with a **19.72 mm square lip, 4.20 mm tall, at the back (PCB side)** — confirmed against the side photo: the wide tier is adjacent to the PCB, and the narrower 18.64 section rises to the flush face. Ear hole is 30.4 mm diagonally from the opposite lip corner → hole center 16.46 mm from module center. Pads, screws, posts, and chamfers are still photo estimates.

## What the photos show

- **Knob module**: ~19.5 mm square black housing, chamfered corners, corner mounting ear with countersunk M2 screw into a threaded boss in the slot. Housing top shoulder = flush plane; knob (~Ø17, ~5.7 mm tall) protrudes above it. Housing depth back→flush face ≈ 7.5 mm.
- **Module PCB**: ~19.4 mm square white board, ~1.2 mm thick, 2 clipped corners, 2 mounting screws, 2 alignment-post holes, gold pogo-pad groups on the outward face (knob = J7; switch module = J12/J8).
- **Slot**: two spring-pin arrays — per the FCC teardown these are **J4 = 6 pins (2×3)** and **J11 = 4 pins (2×2)**, 10 contacts total (est. 2.54 mm pitch — could be 2.0) — plus a threaded boss at one corner and a small black component near the pins (possibly module detection; identify during the pin test).

## Design summary

| Item | Value |
|---|---|
| Top tier footprint | 18.64 × 18.64 mm meas. (modeled 18.50 with fit clearance), R2.0 corners |
| Back lip tier | 19.72 × 19.72 mm meas.; the measured 4.20 tall **includes the 1.2 PCB edge** → plastic lip 3.0 (= arm, flush both faces) |
| Height | assembled 8.44 meas. = housing 7.24 + PCB 1.20 (PCB is the module bottom) |
| PCB screws | relocated to (±8.3, 0), bosses Ø4.6 with inner flats at |x|=6.75 (ESP32 clearance) |
| Alignment | **no posts** (removed per sign-off) — the two M2 screws at (±8.3, 0) locate the PCB |

## Hardware (wireless-only BOM)

| Ref | Part | Why |
|---|---|---|
| U1 | **ESP32-C3-MINI-1** (13.2 × 16.6 × 2.4) | BLE MCU, fits the 16.8 cavity; antenna end toward the top wall |
| U2 | **TPS7A2033DQNR** (X2SON-4/DQN, 1×1 mm, 3.3 V 300 mA LDO, LCSC C46459900) | only package small enough for the strips beside the ESP32 — needs JLCPCB assembly, not hand-solderable. **Changed 2026-08-19 from TPS7A0233 (TPS7A02):** VBAT is raw Li-ion (3.466 V battery … ~4.2 V charging), leaving only 166 mV headroom to 3.3 V. TPS7A02's 270 mV dropout @200 mA would have fallen out of regulation, and 200 mA was short of the ESP32-C3's 350 mA peak. TPS7A20 = 140 mV @ 300 mA, same package **and same pinout**. |
| — | **LDO pinout correction (critical)** | The generator originally used the SOT-23-5 (DBV) pin order. The DQN package is **pin 1 = OUT, 2 = GND, 3 = EN, 4 = IN** (TI SBVS277C Table 5-1 / SBVS338H Fig 4-3) — IN and OUT were swapped, which would have back-driven the regulator. Fixed, and a centre thermal pad (tied to GND) added per TI. |
| Sensor | **HLK-ZW111** (round, `0xEF01`-family UART, ~€4) | smallest round option; **verify OD from its datasheet** before final print — R502-B (Ø22) and ZW101 (Ø21) do NOT fit; fallback: ZW0608 (19×19 sq) as a top-face-replacement variant |
| C1/C2 | 1 µF + 1 µF 0402 | LDO in/out (left strip) |
| C3/C4 | 2× 47 µF 0805 | VBAT bulk for BLE TX bursts (right strip) |
| J2 | 6 SMD wire pads (top side) | sensor pigtail: 3V3, GND, TX, RX, INT, VT |

Board: `cad/kicad/touchid_module.kicad_pcb` (`build_board.py` + `build_board_official.py`) — **all components on the top side** (user requirement: nothing under the board). ESP32-C3-MINI-1 centered (official Espressif footprint, rotated 180° so the antenna faces the keyboard interior); the LDO and caps fit the 1.6 mm side strips only as **micro packages** (X2SON-4 LDO, 0402/0805 caps) → order with **JLCPCB SMT assembly** (~$10 extra), not hand-solderable. Sensor wire pads (J2, normal size) topside in the strips; programming pads are flat copper on the bottom (zero height). No posts, screws at (±8.3, 0). Zero overlaps verified programmatically. **Routed + DRC-CLEAN 2026-08-19** (0 violations, 0 warnings; 55/55 connections, 0 contentions) — master file is now `cad/kicad/altium/touchid_module.PcbDoc`. Board is **19.6 × 17.6 mm** (caliper-measured, NOT square), pogo pads Ø2.2 on **2.5 mm pitch**. Superseded note below:

**Routed 2026-08-19** in Altium Designer (`cad/kicad/Imported touchid_module/touchid_module.PcbDoc`): imported via Altium's KiCad importer, Situs-autorouted 16/16 connections, DRC clean (0 violations). Rules used: clearance 0.127 mm (JLC 5 mil min; needed for the 0.14 mm LDO-pad-to-cap gap), signal width 0.254 mm, power nets (VBAT/GND/+3V3) 0.254–0.6 mm, vias Ø0.6/0.3 mm. Antenna keep-outs placed on both copper layers (93.4–106.6, y-band under the ESP32 antenna) — both layers verified clear. Note: the Altium .PcbDoc is now the routed master; the .kicad_pcb remains the unrouted generator output.
| Ear hole | 16.46 mm diagonal from center (30.4 meas. to opposite lip corner) |
| Walls | 1.4 mm → lip-tier cavity 16.8 mm sq, clears ESP32-C3-MINI-1 (16.6) by 0.2 |
| Top plate | 1.6 mm, Ø12.4 sensor window |
| Sensor seat | Ø14.2 counterbore from inside, 0.8 mm retaining lip |
| Ear | R3.4 tab, Ø2.3 hole, Ø4.4 × 90° csk, 1.8 mm thick at back plane |
| PCB | ~19.7 sq (lip size — verify) × 1.2, 2× Ø2.2 csk holes at (±8.3, 0) |
| Pogo pads | Pad-side view, ear bottom-right: J4 mate 6 pads (2×3) at (+5.6, +5.3) **measured from underside photo**; J11 mate 4 pads (2×2) at (−5.4, +6.8) estimated; Ø2.2 @2.54 |
| PCB screws | **Relocated to (±8.3, 0)** — symmetric; the knob's positions blocked the ESP32-C3-MINI-1. Bosses Ø4.6 with inner flats at |x|=6.75 |
| PCB 3D | `cad/scripts/touchid_pcb.py` → `exports/touchid_pcb_assembly.step/.stl`; full module: `exports/touchid_module_assembly.step`; exploded: `exports/touchid_full_assembly.step` + `viewers/touchid_exploded_viewer.html` |
| Fiducials | Knob PCB's two ringed pads = MARK fiducials (per FCC notes), not contacts |

Sensor mounts from inside against the lip (face flush or ≤0.5 mm proud) so press force lands on the housing, not solder joints — per [[touchid/docs/design/Mechanical and Housing|Mechanical and Housing]]. FPC folds down to the carrier PCB; carrier screws into the housing bosses; pads face down onto J4/J11. Interior clear height between carrier PCB and sensor underside ≈ 4–4.5 mm — enough for the ESP32-C3-MINI-1 (2.4 mm tall) planned in [[touchid/docs/design/Firmware and PCB|Firmware and PCB]]; cavity is 16.2 mm square, so the C3-MINI-1 (13.2 × 16.6) is a *tight* diagonal or needs the wall thinned to 1.4 on two sides — check during PCB layout.

For the final print, follow the material plan already in the vault: PETG (or SLA tough resin) with brass heat-set inserts. The two PCB bosses (Ø5.2, pilot Ø1.7) are sized for M2 self-tappers for the prototype; for inserts, open the pilot holes to the insert OD in `touchid_module.py` (`pcb_screw_pilot_d`).

## Files (in `cad/`)

- `scripts/` — parametric sources; run any of them to regenerate outputs
  - `touchid_module.py` (housing, CadQuery) / `touchid_module.scad` (same in OpenSCAD)
  - `touchid_pcb.py` (PCB + hardware 3D), `build_assembly_parts.py` (exploded parts), `make_drawing.py` (drawings)
- `exports/` — STL/STEP/DXF: housing print files, assemblies, `touchid_full_assembly.step` (Fusion import)
- `drawings/` — dimensioned drawing (+ blank fill-in version), board view PNG, measurement sheet
- `viewers/` — `touchid_exploded_viewer.html` (browser 3D with explode slider)
- `kicad/` — the KiCad project (`touchid_module.kicad_pcb` + generators + Espressif library)
- `archive/` — superseded files (old 3D viewer, legacy footprint)
- `pin-test-results.csv` — raw pin test data

## ✅ DONE — silkscreen labelling (fixed 2026-08-19)

The six J2 signal names are now on **F.SilkS** and therefore printed:
`3V3 / GND / TX` down the left edge, `RX / INT / VT` down the right, placed
**outboard** of the pads at |x| = 8.9 (pad edge 8.2, board edge 9.8) — ≥0.25 mm
clear of the soldermask openings and ≥0.45 mm from the board edge. Verified
present in the exported GTO. They could not go inboard at |x| = 6.1: that is on
top of the ESP32's pads and the fab would clip them.
Component designators (U2, C1–C4) remain on F.Fab — not needed physically since
JLCPCB places those parts.

## Superseded note — silkscreen labelling (deferred 2026-08-19)

The top-side labels (`3V3 GND TX / RX INT VT` for the J2 sensor pads, plus the
U2 / C1–C4 designators) are on **F.Fab**, which is a documentation layer and is
**not printed on the board**. Printed silkscreen is currently only:

- top: "Antenna Area" (from the Espressif footprint)
- bottom: J4-1…6, J11-1…4, DP/DN/IO9, `driver0`, `fingerprint module v1 2026`

So on the physical board the six sensor pads are unmarked — a real hazard when
soldering the sensor pigtail (swapped TX/RX, or VT on the wrong pin, can damage
`0xEF01`-family sensors). Fix next revision: move those texts to **F.SilkS** and
reposition **outboard** of the pad columns (pad edge at |x| = 8.2, board edge at
9.8 → ~1.6 mm of room; text ~0.4 mm). They cannot simply be switched layers in
place: at x = ∓6.1 they sit over the ESP32 pads and the fab would clip them.

Identify pads physically meanwhile: the only Ø1.2 mm round pads on the top side,
two columns of three at the antenna end (opposite the gold pogo pads).
Left column top→bottom: 3V3, GND, TX. Right: RX, INT, VT.

## Caliper pass 2 — 2026-08-20 (supersedes 2026-08-18)

| Feature | Was | Now |
|---|---|---|
| Body tier | 18.64 sq | **18.52 sq** |
| Back lip | 19.72 sq | **19.66 sq** |
| Lip height incl. PCB | 4.20 | **4.10** (plastic 2.90) |
| Assembled height | 8.44 | **8.36** (housing 7.16 + PCB 1.20) |
| Arm width | 5.18 | **5.12** (tip radius 2.56) |
| Arm tip → opposite corner | 30.4 | **30.14** |
| Arm tip → screw hole | — | **1.40 to near edge** → 2.40 to centre |
| Ear hole Ø | 2.3 | **2.0** |
| Arm thickness | 3.0 | **2.94** |
| Ear hole from centre | 13.87 | **13.84** |

**The lip is square (19.66) but the PCB is 19.60 × 17.60** — the board does not
fill the lip footprint in Y. Not a contradiction: the PCB seats on a back rim,
which must be cut to the board's real rectangle rather than to a square.

Drawing regenerated as **v5** with numbered callouts (matching the measurement
sheet) and FRONT / REAR / LEFT / RIGHT labels on all three plan views. Callouts
and side labels now live in `make_drawing.py`, so they survive regeneration.

### Open — retention tab (front edge)
A rectangular tab projecting from the **front** face, sliding under the metal
top case to act as a pivot/ledge while the opposite corner is screwed down.
Callouts **37 / 38** are reserved on the drawing; needs length, width,
thickness and its height above the back plane before it can be modelled.

## Verify before final print / PCB fab

- [x] Caliper the knob module body: 18.64² × 8.44, lip 19.72² × 4.20, ear diagonal 30.4 ✓ (2026-08-18)
- [ ] Caliper the PCB outline (assumed ≈19.7 matching the lip), ear hole Ø, ear thickness, chamfers
- [ ] Measure pogo pin pitch (2.54 vs 2.0 mm) and array positions — highest-risk estimate
- [ ] Check pad mirroring: footprint pads are as seen looking into the slot; confirm against the knob PCB orientation before fab
- [ ] Confirm boss height in slot vs ear z-position (ear currently at back plane, z 0–1.8)
- [ ] Set `sensor_window_d` / `sensor_body_d` / `sensor_lip_t` to the actual sensor part
- [x] Pin test done (2026-08-18) — see [[touchid/docs/bench/Pin Test Results|Pin Test Results]]: **J11-1/2/3 = VBAT (3.47–3.68 V, switched), J4-5 = GND.** Module powers from the keyboard, no data lines needed. Still pending: sleep sweep + load test on J11.
- [ ] Confirm sensor choice from the shortlist in [[touchid/docs/design/Mechanical and Housing|Mechanical and Housing]] (ZW-series / R502-B, `0xEF01` family) and update `sensor_*` params to its datasheet dims

## Scale caveat

The 19.05 mm pitch assumption used for photo scaling is standard MX; if the Air75 V3's low-profile layout uses tighter spacing, all estimates shrink proportionally (~3% if pitch is 18.5). The vault's own eyeball estimate (~19 mm module) agrees with the 19.4 measured here, so it's likely close — but the caliper pass decides.
