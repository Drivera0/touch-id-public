# CARRIER + JIG — DESIGN SPEC v1 (DRAFT, 2026-09-17)

Replaces the printed flash jig (`cad/v7-release/flash-jig/`), which failed on
arrival. **Nothing here is ordered or final — this doc is for the user to
correct before any CAD is generated.**

## 1. Why the printed jig failed (root causes, not symptoms)

Both faults were errors in `cad/pcb-v3/gen_flash_jig.py`, verified against the
source on 2026-09-17:

| Fault | Cause | Number |
|---|---|---|
| Pogo bores did not open; had to be burned through, leaving loose holes | O1.15 bore through 11.0 mm of unbroken deck = **9.6:1 aspect ratio**. MJF cannot clear powder from that. Burning them open also destroyed the O1.45 x 1.0 counterbore, which was the only feature centring each pin head. | bore 1.15, deck 12.0 − 1.0 counterbore |
| Eject lever would not fit the wall slot | Button cap is **9.00 x 7.00 mm**; the slot is **8.00 x 6.50 mm**. Zero print clearance anywhere. | interference 0.5 mm/side in X, 0.5 mm in Z |
| Lever would not rotate far enough | Tip plate top is z=4.50, cavity ceiling z=7.00 → **2.50 mm of swing**. Ejecting the board 4 mm needs **4.3 mm** of plunger travel. | short by 1.8 mm |
| Lever would not stay on its pivot | Axle stubs at z=3.00, pivot slots at z=3.50 (0.50 mm mismatch). The O3.4 slot cuts through the full 3.0 mm boss width, leaving two 0.8 mm tabs. | — |
| Registration posts snapped off | O1.05 printed posts, 2.6 mm tall, in MJF nylon. | — |

**The governing lesson: the printed part must carry no precision and no small
features.** Every tight dimension moves onto a PCB, where the fab holds
+/-0.05 mm for free.

## 2. Board facts — extracted from the board file 2026-09-17

Source: `cad/v7-release/pcb-v7-zero-opens.kicad_pcb`, parsed directly. NOT from
any doc. Coordinates are board-local, same frame as `gen_flash_jig.py`
(+Y = spacebar edge; see memory `touchid-spacebar-edge-is-plus-y` — file Y is
used as-is, never negated).

* Board **20.00 x 19.00 x 1.20 mm**
* **J3 flashing pads: five SMD circles, O1.20 mm, on B.Cu**, 2.00 mm pitch, at
  (−8.00, +3.00) (−6.00, +3.00) (−4.00, +3.00) (−2.00, +3.00) (0.00, +3.00)
  — SWDIO, SWCLK, RESET, VSTOR, GND
* **Mounting holes: two O1.20 NPTH at (+8.75, 0) and (−8.75, 0)** — 17.50 mm apart
* J4: six O2.0 pads on B.Cu at x −6.50/−4.00, y −8.25/−5.75/−3.25 (keyboard pogo — DO NOT TOUCH)
* J11: four O2.0 pads on B.Cu at x +4.00/+6.50, y −8.25/−5.75 (keyboard pogo — DO NOT TOUCH)

> **CHANGE FROM EARLIER ASSUMPTIONS: the J3 pads are O1.20, not O2.0.**
> The tip must land inside a 1.2 mm circle, so registration has to be good to
> roughly +/-0.35 mm. This is why printed posts were never going to be enough.

## 3. Architecture — three layers

```
        your board (20 x 19 x 1.2)   drops over 2 metal dowels, face up
   ┌──────────────────────────────┐
   │  NEST PCB   34 x 30 x 1.6    │  5 clearance holes + 2 dowel holes
   └──────────────────────────────┘
        ║          ║                  4 x M3 standoffs, 10 mm
   ┌──────────────────────────────────────────────┐
   │  CARRIER PCB   80 x 80 x 1.6                 │  pins, programmer, power
   └──────────────────────────────────────────────┘
   ┌──────────────────────────────────────────────┐
   │  PRINTED JIG — frame with a big hole + lip   │  optional, see 6
   └──────────────────────────────────────────────┘
```

Two plates, not one, because a P75-E2 is **16.5 mm long**. Soldered into a
single 1.6 mm board it would stand ~14 mm proud and wobble. The nest grips each
barrel just below the tip; carrier + nest together support the pin at two points
10 mm apart, which is what actually holds the tip on a 1.2 mm pad.

## 4. Pin height — the arithmetic

P75-E2 (confirmed): length **16.5**, barrel **O1.02**, head **O1.3**, full stroke
**2.50 mm**, spring **100 g**, minimum pitch **1.91 mm** (so the 2.00 mm J3 pitch
is in spec).

```
protrusion above nest = 16.5 − tail − t_carrier − h_standoff − t_nest
                      = 16.5 − 1.8  − 1.6       − 10.0       − 1.6   = 1.5 mm
```

* Standoffs **10 mm** (stock size), both plates **1.6 mm**
* Pin tail stands **1.8 mm** proud below the carrier — that is what you solder to
* Tip stands **1.5 mm** proud above the nest
* Board pressed flat onto the nest → **1.5 mm compression**, 60% of full stroke
* Force ≈ 5 pins x ~60 g = **~300 g**. Finger pressure is enough for the ~5 s a
  flash takes; no clamp needed in v1.

**Assembly method for setting pin height:** bolt the stack together first, lay a
1.5 mm shim (a scrap of 1.6 mm PCB) across the nest, push each pin up from below
until its tip touches the shim, then solder the tail. All five end up identical.

**Drop the 6th "helper" pin.** It existed on the old jig to keep the lift level.
The dowels do that now.

## 5. Registration — metal dowels (user's choice, 2026-09-17)

Two **O1.0 mm dowels**, soldered into the carrier at (+8.75, 0) and (−8.75, 0),
passing up through clearance holes in the nest and standing ~2.5 mm above it.

* Carrier holes: plated, **O1.05**, dowel soldered in
* Nest holes: **O1.10** slip fit — supports the dowel near its top, same
  two-point principle as the pins
* Slop in the board's O1.20 hole over a O1.00 dowel = **+/-0.10 mm radial** —
  comfortably inside the +/-0.35 mm the J3 pads need

Metal, bought, and supported at two heights, so nothing can snap off the way the
printed posts did. Do not size the dowel to the hole: per memory
`touchid-no-edge-is-clampable`, the board's O1.20 is a press-fit hole and a tight
post burrs it.

**OPEN — dowel sourcing is not settled.** O1.0 stainless dowel pins do not
solder; brass rod does but is soft; a cut drill blank is hard steel and also
will not solder. Needs a live sourcing check before layout is frozen. Do not
assume a part number.

## 6. The printed jig — big hole and a lip (user's idea, adopted)

The frame carries **no precision and no small features**. Everything it does is
coarse.

* Outer ~**70 x 60 mm**, wall 5 mm, height ~**22 mm** (clears the 1.8 mm tails,
  the solder joints and the wires underneath)
* **One large rectangular opening**, ~50 x 40 mm, straight through
* A **5 mm wide lip** around the opening, recessed **1.8 mm**, so the carrier
  drops in and sits flush
* Four **O3.4 mm** holes through the lip corners for M3
* **Smallest feature anywhere: 3.4 mm.** Nothing can clog, nothing can snap.
* Verify with the existing `cad/scripts/wall_check.py` before ordering

Soldering access is the whole point of the opening: every pin tail and every
wire is reached from underneath, in free air.

**This part is optional for v1.** Four M3 standoffs screwed into the underside of
the carrier are already feet. Build the frame if you want the stability and a
place to mount a hold-down later; skip it if you want to test sooner.

## 7. Carrier PCB — zones kept far apart (user's requirement)

Carrier is **80 x 80 mm**. JLCPCB's cheapest tier runs to 100 x 100 mm, so the
extra area is free, and it is what lets the programmer module sit clear of the
nest. Nothing is crowded and every joint is reachable with an iron.

### Plan view (board-local mm, origin = centre of your board)

```
  y=+40 ┌──────────────────────────────────────────────┐
        │          ┌────────────────────┐              │   USB-C faces +Y,
        │          │   XIAO RP2040      │              │   cable runs off
  y=+17 │          └────────────────────┘              │   the north edge
        │      ┌──────────────────────────────┐        │
        │      │   NEST  34 x 30              │        │
        │      │      ┌──────────────┐        │        │
  SWD → │      │      │ YOUR BOARD   │        │        │ ← VSTOR / GND
 header │      │      │   20 x 19    │        │        │   test points
        │      │      └──────────────┘        │        │
        │      └──────────────────────────────┘        │
  y=−17 │               [ DP100 IN ]                   │
  y=−40 └──────────────────────────────────────────────┘
       x=−40                                        x=+40
```

**Nothing overlaps. Verified 2026-09-17:**

| Check | Value |
|---|---|
| Module bottom edge y = +17.00, your board's top edge y = +9.50 | **7.50 mm horizontal gap** |
| Module gap to nest edge / to carrier north edge | 2.00 mm / 2.00 mm |
| Module top surface 3.50 above carrier; your board's underside 11.60 above carrier | **8.10 mm vertical clearance** |
| Standoffs at (+/-13.5, +/-11.5) vs module footprint | no clash |

The module is in the north strip, a long way outside the nest. Even if it were
directly underneath your board it would still clear by 8 mm, because the
standoffs lift everything 11.6 mm.

| Zone | What | Why there |
|---|---|---|
| **Centre** | 5 pogo pins + 2 dowels, inside a 20 x 19 outline | under the nest |
| **North (+Y)** | USB-C socket + RP2040 programmer module | one cable to the PC |
| **South (−Y)** | **2-pin JST-XH, keyed, DP100 in** | opposite the USB, no confusion; see §9 |
| **East** | 4-pin 2.54 mm SWD escape header | external probe if the built-in one misbehaves |
| **West** | VSTOR / GND test points | meter it before the board goes in |

Nest is only 34 x 30 mm (reaches +/-17 x +/-15), so everything except the pins
sits outside its shadow and stays accessible with the stack assembled. Standoff
holes at (+/-13.5, +/-11.5), clear of the 20 x 19 board envelope.

**Sizing history — two corrections, both caught by the user.** The north strip
must hold the programmer module between the nest edge (y = +15) and the carrier
edge. At 60 x 50 that strip was **10 mm** deep and the module needs 21 mm — it
did not fit anywhere. 80 x 70 gave 20 mm, still short once the module is turned
so its USB-C faces outward. **80 x 80 gives 25 mm**, which fits with 2 mm at
each end.

Silkscreen: an arrow for the spacebar (+Y) edge, and every pin labelled.
Wrong-way-round insertion puts 3.6 V on ground copper.

## 8. Flashing over USB-C (user's requirement)

**Do not design an RP2040 from scratch.** Use a ready-made USB-C RP2040 module:
no crystal, no QSPI flash, no USB-C footprint, no 3.3 V regulator to get wrong.
Either candidate runs Raspberry Pi's open-source `debugprobe` firmware, loaded
by drag-and-drop UF2 — no probe needed to program the programmer — and presents
as CMSIS-DAP, which is what pyOCD wants.

| Candidate | Size | Mounting | Note |
|---|---|---|---|
| **Seeed XIAO RP2040** | **21 x 17.8 x 3.5 mm** (confirmed, Seeed wiki) | 2.54 mm headers, 7 per side — **socket it**, no castellation soldering, removable | same form factor as the XIAO nRF52840 already being bought |
| Waveshare RP2040-Zero | ~18 x 23.5 mm (**unconfirmed**, see §11) | castellations, soldered down | cheaper, permanent |

**Recommended: XIAO RP2040 in a pair of 7-pin 2.54 mm female headers.** It is
removable, so a bad `debugprobe` build or a dead module is a 10-second swap
rather than a rework job, and 2.54 mm headers are the easiest thing on the board
to solder.

### Mounting side: TOP of the carrier, not underneath

Decided 2026-09-17. Reasons, in order:

1. **The underside is the soldering side.** Pin tails and their wires are the
   only things down there, by design (§6, §7) — putting a module in that space
   defeats the big opening in the jig.
2. **USB-C access.** The carrier sits flush with the frame's top face, so a
   port on top is unobstructed. Underneath it would face into the frame and
   need a slot cut in the wall.
3. **Replaceability.** On top it can be unplugged or desoldered without
   disturbing a single pogo joint.
4. **Hand-soldering.** Castellations and headers are both far easier to work
   from above.

Height is not the constraint either way: the module is 3.5 mm and the nest sits
10 mm up — but it sits outside the nest footprint regardless.

**Rejected: Raspberry Pi Debug Probe.** Checked 2026-09-17 — it is **micro-USB,
not USB-C**, and Raspberry Pi specify it for targets "with 3V3 I/O". Both
disqualify it here.

**The 4-pin SWD header in §7 is kept regardless.** It costs four pads. On a first
spin it is the only way to tell a bad board from a bad programmer — plug in a
known-good external probe and the question answers itself.

### The 3.6 V problem — unresolved, and it may delete a whole circuit block

The module's pins run at 3.3 V. The target runs at 3.6 V and drives back on
SWDIO. 3.6 V into a 3.3 V-powered RP2040 pin sits at the absolute-maximum limit
(IOVDD + 0.3 V).

Raspberry Pi solve this on the Debug Probe with **100 R series resistors (R12,
R13)** plus **74AUP1T17GW level-shifting buffers (U4, U5)** on SWCLK and SWDIO.
That topology is copyable. **However:** SWDIO is bidirectional and I have not
resolved from the schematic how they control its direction. That must be pinned
down before layout.

**Before building any of it, answer this question:** does the board actually need
3.6 V *during flashing*, or only afterwards? `HANDOFF-FIRMWARE.md` says "the
board must see 3.6 V on VSTOR while flashing … the probe's 3.3 V is NOT enough
for full rails", but the nRF52840 itself runs from 1.7 V. If 3.3 V is enough to
flash, and 3.6 V is only needed to test the radio afterwards, then **flash at
3.3 V and raise the supply afterwards** — and the entire level-shifting block
disappears. This is the single highest-value open question in this spec.

## 9. Power — DP100 plugs in (user's idea, adopted 2026-09-17)

The **DP100** supplies VSTOR. The RP2040 module can only offer 5 V or 3.3 V;
5 V on VSTOR is forbidden (the cell is on that rail) and 3.3 V is the open
question in §8.

**The DP100's output is 4.0 mm banana jacks** (confirmed, DP100 manual), and it
ships with red and black alligator-clip leads. Alligator clips on bare wire mean
polarity can be swapped by accident, and reversed 3.6 V into VSTOR is a dead
board.

**Carrier gets a 2-pin JST-XH (2.5 mm pitch) header on the south edge.** Keyed,
so it physically cannot go in backwards; ~3 A rated against a ~200 mA load;
hand-solderable. Make one cable, once: two 4.0 mm banana plugs at the DP100 end,
JST-XH at the carrier end. After that the supply just plugs in.

**Do NOT put a series Schottky in this path for reverse protection.** A 0.3 V
drop turns 3.6 V into 3.3 V, which is the exact voltage this whole design is
trying not to have. If active protection is wanted, it must be a P-channel
MOSFET high-side block (~10 mV drop, two parts). With a keyed connector this is
optional.

### This deletes the VSTOR jumper

The jumper existed so the rail could be verified with the output live before the
board was connected. With the DP100 on a keyed connector, **the board itself is
now the last thing connected** — it is dropped onto the pins by hand, after
everything else is already powered and measured. The jumper adds nothing.

Routine: plug in DP100 → recall preset → output on → confirm 3.6 on the display
→ meter the west-side test points → **drop the board in last**.

Set up a **saved preset** on the DP100 — 3.6 V, current limit ~0.2 A, OVP ~3.8 V.
Unsaved changes do not survive a restart, so it cannot be left at some other
project's voltage.

## 10. Dongle

Separate purchase, not part of this board. USB-C requirement points at the
**Raytac MDBT50Q-CX-40** — per `docs/dongle/OFF-THE-SHELF-DONGLES.md` the only USB-C
finished dongle found, open DFU bootloader, mainline Zephyr support, same module
family as the knob. DigiKey lists it as shipping.

This is Option C of `docs/dongle/MODULE-TRADE-STUDY.md` — prove the radio and firmware
on dev hardware, decide dongle size later. Buying it commits nothing.

The **XIAO nRF52840 Sense Plus** is still needed and is unaffected by any of this:
it is the knob-side proxy you write firmware on. There is no firmware in this
repo yet; that is the real critical path.

## 11. Confirmed vs unconfirmed

**Confirmed from primary sources:**

* All board geometry in §2 — parsed from `pcb-v7-zero-opens.kicad_pcb`, 2026-09-17
* All jig failure numbers in §1 — computed from `gen_flash_jig.py`
* P75-E2: 16.5 mm, O1.02 barrel, O1.3 head, 2.50 mm full stroke, 100 g, 1.91 mm
  minimum pitch
* Raspberry Pi Debug Probe is micro-USB and specified for 3V3 I/O
* Debug Probe level shifting: 74AUP1T17GW x2, 100 R series

**Unconfirmed — do not design against these yet:**

1. **Dowel material and source** (§5) — no part number identified
2. **SWDIO direction control** in the Debug Probe topology (§8)
3. **Whether 3.3 V is sufficient to flash** (§8) — could remove a whole block
4. **RP2040-Zero physical dimensions** — neither the Waveshare wiki nor the
   product page states them; the wiki figure is the schematic image size, not
   the board. Not needed if the XIAO RP2040 is chosen.
5. **XIAO RP2040 header row spacing** — the 21 x 17.8 x 3.5 mm outline is
   confirmed from Seeed's wiki, but the row-to-row dimension is not stated
   there. Get it from the mechanical drawing before drawing the footprint.
6. `debugprobe` **pin mapping** on whichever module — the stock build targets
   the Pico; a custom build is likely needed
7. Standoff and screw sourcing (M3 x 10 mm, four off)

## 12. Explicitly NOT in v1

* No eject mechanism. 300 g of pin force does not need a machine.
* No hold-down. Add one later if finger pressure annoys you.
* No USB-C power path. The DP100 has a current limit and an over-voltage trip;
  a small regulator would not.
* No VSTOR jumper — deleted by the keyed DP100 connector, see §9.
* No chip-down RP2040. Module first, integrate later if ever.

---

# ADDENDUM A — ONE BOARD INSTEAD OF TWO (2026-09-17)

User asked whether the guide plate can be deleted. Investigated Route A (find a
short pin). **Route A is dead for any catalogue part, and the reason is
diameter, not length.**

## Route A result: the whole Mill-Max discrete range is too fat

From the Mill-Max spring-loaded pin catalogue (Mouser 025-259718.pdf), read
2026-09-17:

| Series | Body dia | Length range | Mounting hole |
|---|---|---|---|
| 0906 | **.072" (1.83 mm)** | .155"–.236" | .020 min |
| 0908 | .072" | .255"–.430" | .020 min |
| 0914 | .072" | .274"–.364" | .029 min |
| 0901 | .072" | .198" | .029 min |
| 0929 | .072" | .340"–.480" | .029 min |
| 0932 | .072" | .228"–.235" | .029 min |
| 0930 | .072" | — | .020 min |

**Every discrete series is .072" (1.83 mm).** Mill-Max's "high-current,
small-scale" line is **.083" (2.1 mm)** — worse.

On the J3 row's **2.00 mm pitch** a 1.83 mm barrel leaves **0.17 mm** between
adjacent pins, before tolerance. That is the same geometry that ruled out the
P125-B: see `JIG-SHOPPING.md` — *"five of those barrels on the J3 row's 2.0 mm
pitch touch each other and short every signal — ruled out by geometry, not
preference."*

So the number flagged as unconfirmed in §11 item 4 is the number that kills the
option. 0906 was never rejected for being 5.9 mm short — it is rejected for
being 1.83 mm wide.

**Remaining Route A candidates are unbranded Ø1.5 x 6 mm pogo pins from Amazon /
AliExpress with no drawing, no tolerances and no datasheet.** Against the repo
ground rule (*never invent a part number; trace every fact to a datasheet*)
those cannot be specified for the one interface whose accuracy the whole fixture
exists to hold. Not recommended.

## But the search found a better answer: mount the P75-E2 upside down

The guide plate exists because ~14 mm of pin stands ABOVE the board. Nothing
requires that. **Put the long part below the board instead.**

P75-E2 geometry (confirmed): conical head **Ø1.3** (contact end), tube **Ø1.02**,
shank/tail **Ø0.74**, total **16.5 mm**, full stroke 2.50 mm, 100 g.

Solder the tube into a **Ø1.05 plated hole** in the carrier so that only
**~2 mm** stands above the top face. The remaining ~14 mm hangs down into the
big opening in the printed frame, in free air, where it is also exactly where
you solder it.

What this buys:

* **One board.** Guide plate, four standoffs and an assembly step all deleted.
* **Tip accuracy comes from the Ø1.05 hole it emerges from** — a 2 mm cantilever
  instead of 14 mm. Better than the two-plate version, not worse.
* On 2.00 mm pitch, Ø1.02 barrels leave **0.98 mm** between them. Comfortable.
* Uses the pin already specified and already cheap (C$1.40 / 10 pcs).
* Dowels solder straight into the carrier; no second plate to pass through.

## The one unknown, and why it is not a blocker

**Is the Ø1.3 conical head the moving plunger, or a fixed flange on the barrel?**
That sets how high the barrel must sit and whether anything retains the plunger.
No manufacturer drawing is reachable — Mill-Max's site 403s, rtlecs 403s, and
every other source is a reseller listing repeating the same four numbers.

**It is measurable.** One pin plus a caliper answers it in under a minute.

**It does not block the PCB.** Hole positions, hole sizes, pad sizes and every
piece of copper are independent of that number. It only affects how far the pin
is pushed in before soldering — an assembly step, set with a shim, adjustable on
the bench.

## Revised stack

```
        your board (20 x 19 x 1.2)   drops over 2 soldered dowels
   ┌────────────────────────────────┐
   │   CARRIER PCB   80 x 80 x 1.6  │   pins ~2 mm proud, 14 mm hanging below
   └────────────────────────────────┘
   ┌────────────────────────────────┐
   │   PRINTED FRAME                │   big hole holds the hanging barrels
   └────────────────────────────────┘
```

**The printed frame is no longer optional.** The barrels hang 14 mm below the
carrier, so the carrier has to stand off the desk. The frame's lip does that,
and its big opening is what the barrels hang into. Frame height must clear
14 mm of barrel plus solder — call it 20 mm minimum, so the ~22 mm in §6 still
works.

## RESOLVED: the hard stop is the pin barrels themselves

Set the tube ~0.5 mm proud of the carrier and the plunger tip ~1.5-2.0 mm
proud.  The board bottoms out on the five barrel rims at ~1.0-1.5 mm of
compression, inside the 2.50 mm stroke.

* the stop is metal, and it is AT the five contact points, so the board cannot
  tilt
* each rim touches only its own J3 pad -- the same net as the pin inside it --
  so contact there is electrically harmless
* no extra parts, and nothing has to touch the DUT's crowded bottom face
* the exact tube height depends on the unresolved plunger geometry above, and
  it is set by hand at assembly with a 1.5 mm shim, so it is adjustable on the
  bench rather than baked into the board

The options below were the candidates before that was worked out; kept for the
record.

## Superseded: other hard-stop options considered

The guide plate was also the surface the board rested on, limiting compression.
With one board the board would rest on the pin tips alone, and could be pressed
past the 2.50 mm stroke.

Options, none yet chosen:

1. Two or three small bumpers at a set height, placed where the board's bottom
   face is clear of pads (left edge has 0.65 mm, right edge 0.96 mm of bare
   laminate per `touchid-no-edge-is-clampable`)
2. Shouldered dowels — the shoulder is the stop, and it sits at the mounting
   holes where the board is definitely clear
3. Let the plunger bottom out in its own barrel (what cheap jigs do; acceptable
   for 5 seconds, not ideal)

Option 2 is the most elegant and needs a sourcing check.


---

# ADDENDUM B — BUILT (2026-09-18)

Both parts generated and checked in.  See `README.md` for ordering.

* `gen_carrier.py` -> `carrier-v1.kicad_pcb`  (80 x 80, 2 layer, 1.6 mm,
  14 footprints, 32 segments, 2 vias)
* `check_carrier.py` -> **0 blockers**.  Verifies pogo/dowel positions against
  `pcb-v7-zero-opens.kicad_pcb` LIVE, plus pad/track/via clearance and the
  no-F.Cu-under-the-DUT rule.
* `gen_frame.py` -> `flash_frame.stl` / `.step` (90.4 x 90.4 x 22, 50.2 cm3,
  watertight).  `wall_check.py` at 1.00 mm: none found.

**Three defects were caught by the checkers during the build, not by eye:**

1. `MH -> MH` self-collision at -3.20 mm.  A checker bug, not a board bug --
   the mounting-hole footprints were being compared against themselves.  Same
   lesson as [[touchid-checkers-lie-more-than-the-board]].
2. Three real routing collisions once track-to-track and track-to-pad checks
   were added: `GND` grazing `J2.2` by 0.020 mm, `SWDIO_R` crossing `SWCLK_R`,
   and `GND` crossing `VSTOR`.  All three were invisible in the first preview.
3. The engraved +Y arrow left a **0.30 mm rim** at the outer edge of the wall
   band; `wall_check.py` flagged 38 thin x-slices.  Resized to leave >= 1.2 mm
   both sides, and `gen_frame.py` now asserts it.

**A design rule was added that had not been stated before:** no F.Cu copper
inside the DUT rectangle except the PP*/DW* pads.  The DUT's BOTTOM face
carries exposed gold (J4 6 x O2.0, J11 4 x O2.0, TP1-TP10) and hovers ~1.5 mm
over the carrier.  Everything that must cross underneath now goes on B.Cu.
`check_carrier.py` enforces it by sampling every F.Cu segment at 0.25 mm.

**One assumption ships unverified:** the XIAO RP2040 socket
(`XIAO_ROWS = 15.24`, pitch 2.54, pin order).  Seeed publish the outline only.
`carrier-footprint-check.pdf` is a 1:1 paper check with a 50 mm calibration
ruler -- print it and lay a real module on it before ordering.  If it is wrong
the board still works through J2.


---

# ADDENDUM C — XIAO FOOTPRINT CONFIRMED, RESET WIRED (2026-09-18)

## The assumed number was wrong

`XIAO_ROWS` was assumed at **15.24 mm**.  The real figure is **17.00 mm**.

Source: Seeed Studio, "XIAO Series Package and PCB Design", **page 3**, XIAO
RP2040 (SKU 102010428), "Recommended PCB land pattern".  Saved locally at
`datasheets/Seeed-XIAO-Series-Package-and-PCB-Design.pdf`.

Getting it took four dead ends -- Mill-Max-style 403s on Seeed's own GitHub
tree, manuals.plus and snapeda; the GitHub API refused; and the page's text
layer contains nothing but the page number, because **every dimension callout
in that drawing is a vector outline, not text**.  It had to be read off a 7x
render of the drawing region.

Confirmed from that page:

| | |
|---|---|
| row spacing | **17.00 mm** centre-to-centre |
| pad | **3.0 wide x 2.0 tall**, SMD |
| pitch | 2.54 mm, 7 per side |
| body | 17.8 x 21 mm |
| right row, USB end first | 5V GND 3V3 D10 D9 D8 D7 |
| left row, USB end first | D0 D1 D2 D3 D4 D5 D6 |

and from the same page's pinout, **D8 = P2 = GP2** and **D10 = P3 = GP3** --
which are exactly `debugprobe`'s default SWCLK and SWDIO.  The pin assignment
is therefore confirmed too, not assumed.

**Consequence: the module is soldered, not socketed.**  Seeed publish an SMD
land pattern and no through-hole alternative, and the castellation hole
spacing is not published.  Socketing would have meant assuming a second
number.  The published land runs 7.0-10.0 mm off centre against a module edge
at 8.9, so 1.1 mm of every pad stays outside the module and each joint is
reworkable from the side.

Earlier draft's left-row order was also reversed; corrected.

## RESET is now driven

The earlier draft left PP3 (RESET) with a pin and a pad but no copper, on the
strength of `HANDOFF-FIRMWARE.md`'s "RESET unused by DAPLink flow -- park it."

That holds for an ordinary flash.  It does not hold for **recovery**: nRESET is
how you get in when firmware has put the nRF52840 somewhere SWD cannot reach,
and this firmware is deep-sleep-heavy by design (6 uA budget, U4 gating,
VBAT_OK permission).  A jig that cannot assert reset is a jig that can be
locked out by its own target.

RESET now runs XIAO **D7 (GP1)** -> **R3 100 R** -> PP3, and to **J2 pin 3**.

## Routing was restructured, not patched

Placing the resistors to the LEFT of the module forced every SWD signal to
travel around it, and three hand-routed attempts each produced new collisions.

The fix was topological, not incremental:

* resistors moved to the **right** of the module, each level with the pin it
  serves, so every stub is a straight horizontal line
* each signal drops to B.Cu on **its own vertical lane**, lanes spaced
  **2.54 mm** apart, and turns left on **its own horizontal lane** (y = 11, 9,
  7) to its pogo pin
* because the lanes are on a 2.54 grid, **J2 sits directly on top of them** --
  a 5-pin header that needs no routing at all, in the same order as J3 itself
  (SWDIO SWCLK RESET VSTOR GND)

## New check: connectivity

The checker proved nothing shorted but never proved nothing was OPEN -- and
J2's SWDIO/SWCLK pads had in fact been floating, with nets assigned and no
copper.  `check_carrier.py` now runs union-find over pads, track endpoints,
T-junctions and vias, per layer, with vias and through-hole pads bridging.

Current state: **GND(5) SWCLK(2) SWCLK_R(3) SWDIO(2) SWDIO_R(3) VSTOR(4)
nRESET(2) nRST_R(3)** -- every net one island, 0 blockers.

## And a third checker bug

Adding the nRESET net shifted every net index, and the checker held its own
hardcoded copy of the net table -- so it reported 22 blockers that were all the
same drift.  It now imports `NETS` and `SILK` from the generator.  That is the
third time this session a checker lied before the board did; see
[[touchid-checkers-lie-more-than-the-board]].

---

# ADDENDUM D — XIAO BELLY PADS, COMPACTED, SILK FIXED (2026-09-18)

## The module's underside is live copper

Seeed's back-view photo (page 3, read at 26x) and the land pattern agree: the
XIAO RP2040 carries exposed pads on its BELLY as well as its edges --

* four round O1.5 pads, 5.85 mm above centre, 2.54 apart: the module's own
  **SWCLK / SWDIO / GND / RST**
* two 1.3 x 2.3 rectangles, 8.6 mm below centre, 2.54 apart: **GND** and
  **VIN (5 V)**

The silkscreen reads "UIN" only because of the stencil font; it is VIN.

The module lies FLAT on this carrier, so foreign copper under it is a short --
and VIN makes that a 5 V short, on a board whose whole safety story is that
5 V never gets near VSTOR.  **New rule, enforced by `check_carrier.py`:** no
track and no via anywhere inside x +-7.0 across the module footprint.  That is
the strip between Seeed's two land columns (which run 7.0-10.0 off centre), so
a track leaving a land at x = +-8.5 is still legal.

VIN is deliberately left unconnected.  The XIAO takes its power from USB-C.

## Solderless press-fit / "hammer" headers: no

A press-fit pin works by interference against a **full** plated barrel, gripping
on all sides.  A 26x render of Seeed's own photo confirms the XIAO's side pads
are castellated **half**-holes, open to the board edge -- there is no barrel to
grip.  No hammer header is made for this form factor either; the products on
the market are 2x20 for the Pi GPIO and 2x20 for the Pico.  And this carrier
has SMD lands, not holes, so there is nothing to press into regardless.

## Compacted: 80 x 80 -> 47 x 58

The old outline was centred on the DUT, which meant half the board was empty
laminate: everything except the pogo pins lives up and to the right of the
target.  The outline is now explicitly **NOT** centred on the DUT --
x -16..31, y -20..38.

| | before | after |
|---|---|---|
| carrier | 80 x 80 = 6400 mm2 | **47 x 58 = 2726 mm2** (-57%) |
| frame | 90.4 x 90.4, 50.2 cm3 | **57.4 x 68.4, 32.8 cm3** (-35%) |

The frame's opening is now **offset** (24 x 22, centred on board-local (0, 2))
so it sits under the pogo pins rather than under the middle of the board, and
`gen_frame.py` asserts that every screw boss lands on solid lip.

Nothing else moved: pogo and dowel coordinates are still parsed live out of
`pcb-v7-zero-opens.kicad_pcb`, and the checker still reports **0 blockers**
with every net one island.

## Silkscreen

Two previews shipped with text sitting on top of other text.  `check_carrier.py`
now has a **silk-vs-pad** rule -- a label overlapping a pad gets masked off and
becomes unreadable -- and the preview renderer reads `SILK` and `NETS` straight
out of the generator so it cannot drift again.  Labels added for the five pogo
pins, both dowels, J1's polarity and J2's five pins.


---

# ADDENDUM E — CONTACTS CANNOT BE MACHINE-PLACED (2026-09-18)

User asked whether JLCPCB could place the pogo pins, and if not, for another
way to keep ONE carrier with the DUT dropped on top.

## The answer is no, and it is geometric

**Every SMD pogo pin in JLCPCB's parts library is O2.0 mm** -- Kinghelm and BAT
Wireless, 2.5 to 6.5 mm lengths, all D=2 mm.  J3 is 2.00 mm pitch.  Five O2.0
barrels in a row touch.

This is now the THIRD independent time this exact constraint has decided a
choice: P125-B (O2.0), the whole Mill-Max discrete range (O1.83), and now every
machine-placeable pogo pin.  **The 2.00 mm pitch of J3 is the hardest
constraint in this fixture.**  Only the P75-E2's O1.02 tube clears it, and it
is not a catalogue placeable part.

So: JLC places U1, R1-R3, J1 and J2.  The five pins and two dowels are
hand-soldered.  There is no third option.

## The architecture did not change

Still one carrier PCB, DUT dropped on top over two dowels.  Nothing about the
board moved.

## What changed: the skill requirement was designed out

The only step that depended on a steady hand was holding each pin at a
consistent height.  New third printed part, `pin_setter.stl` (51 x 62 x 10,
17.6 cm3): carrier goes in face down, components hang in 5 mm reliefs, pins and
dowels drop in and bottom out in a **2.0 mm** and a **4.5 mm** pocket
respectively.  Heights are set by print tolerance.

The two pockets overlap in plan but not where it matters -- the generator
asserts that every pin sits over the shallow floor and every dowel over the
deep one, and refuses to build otherwise.

## Three DFM findings while building it

1. The component reliefs were cut at `REC_W + 2`, overhanging the locating
   recess by 1 mm each side and leaving a **0.80 mm outer wall** -- 30 thin
   slices.  Fixed to `REC_W` exactly.
2. A **cut** text label left 2-4 thin slices.
3. An **embossed** label was worse: raised 5 mm letters are thin features
   themselves, 10-13 slices.  A plain marker notch flagged as well.

The part now ships with no cosmetic features at all and `wall_check.py` reports
**none found**.  Worth remembering: on this project every decorative feature
added so far has been the thing that failed DFM -- the frame's arrow did it
too (Addendum B).


---

# ADDENDUM F — NO WIRES, AND A SETTER ERROR (2026-09-18)

## No wires

The old jig soldered five wires to the pin tails and routed them out through
arches.  The carrier deletes that entirely: the tube solders into a plated
through-hole and copper carries the signal.  **One joint per pin, no wire.**

The only wire left in the system is the DP100 lead -- two banana plugs to a
JST-XH -- made once, off the board.  CA$19-24 of wire and heat-shrink comes off
`JIG-SHOPPING.md`.

## The setter assumes an insertion that is impossible

Caught while confirming the above.  `gen_pin_setter.py` has the carrier face
down with pins dropped in tip-first from the underside, bottoming in a 2.0 mm
pocket.  **The tip end carries the O1.3 head and the hole is O1.05.  The head
cannot pass through it.**

The pin must be inserted from the TOP, tail first.  Which is probably a better
answer anyway: the head cannot pass the hole, so each pin seats itself on the
top pad, all five land at the same height with no fixture, and the head rims
become the DUT's hard stop -- the same mechanism Addendum A reasoned toward,
but arrived at for free instead of by setting barrel heights with a shim.

This turns on the pin dimension that has never been confirmed and could not be
found from any reachable source (Addendum A, open item 2): whether the O1.3
head sits at the contact end.  A caliper on one delivered pin answers it.

**The PCB is unaffected** -- same holes, same sizes, same copper.  Only the
assembly motion changes, and the setter is contingent on the measurement.

Recorded here rather than quietly fixed because the setter was presented in the
previous message as the thing that removed all the skill from assembly, and it
does not do that if it cannot be used.


---

# ADDENDUM G — THE FRAME IS THE ASSEMBLY FIXTURE (2026-09-18)

User caught the orientation: the carrier is soldered **face UP**, not face
down.  Correct, and it collapses the whole problem.

Pins go in from the top (Addendum F: the O1.3 head cannot pass the O1.05 hole).
So the carrier must be face up to receive them -- which is its normal
orientation -- and the tails then hang DOWN, which is where they need to be
soldered.  That is exactly the situation the frame was designed to create:

* the recess locates the carrier face up
* the head seats on the top pad, so every pin sets its own height
* 20.2 mm of clear space under the carrier for ~13 mm of hanging tail
* the 24 x 22 opening is the soldering access, offset to sit under the pin row

**`pin_setter.stl` is superseded.**  It solved a problem the frame already
solved, in an orientation that cannot work.  Two corrections on the same part
in consecutive messages.

The root error is worth naming: the setter was designed from the geometry of
the pocket outward, without once walking through the physical motion of putting
a pin into the hole.  Had that been done, the O1.3-head-versus-O1.05-hole
conflict would have surfaced immediately -- it is the same failure as the v2
printed jig, whose eject lever was dimensioned without checking that the button
could pass through its own slot.

Files kept, not deleted, and marked superseded in README.md.

Unchanged: the PCB.  Same holes, same sizes, same copper, 0 blockers.


---

# ADDENDUM H — WHAT STOPS THE PIN (2026-09-18)

User: "won't they just fall through, how do I know the right height?"  Fair,
and it exposes that Addendum G over-corrected.

## The design leans on one unmeasured number

The hole is O1.05 and the vendor lists a O1.3 head at the contact end.  If that
is right, the pin physically cannot pass and sets its own height -- which is
why O1.05 was chosen over anything larger.  If it is wrong, the pin falls
through and needs a stop beneath it.

**Measure the largest diameter at the contact end of one pin.  > 1.05 = Case A,
<= 1.05 = Case B.**

| | Case A (expected) | Case B |
|---|---|---|
| carrier | face UP, in the FRAME | face DOWN, in the SETTER |
| pin enters from | the top, tail first | the top, head first |
| what stops it | its own head on the hole | the setter's 2.0 mm pocket |
| protrusion | fixed by the pin | 2.0 mm, by print tolerance |
| solder from | below, through the opening | above (board underside is up) |

## Addendum G was too absolute

It declared `pin_setter.stl` superseded.  It is not -- it is the Case-B tool,
and its face-down orientation is correct for that case.  What Addendum F
actually established is narrower: the setter cannot be used in Case A, because
a O1.3 head cannot enter a O1.05 hole.  Both parts stand; the measurement picks
one.

Corrected in README.md.

## Why the PCB is safe to order regardless

Holes, diameters, positions and copper are identical in both cases.  Only the
printed fixture differs, and printing turns around in days.  The board can be
ordered before the pins arrive.

## Error stack, for the record

Contact tip has to land inside the DUT's O1.20 pad, so +-0.60 mm:

  hole position (fab)        +-0.050
  dowel in the DUT's O1.20   +-0.100
  pin tilt in its hole       +-0.019   (0.030 diametral slop over 1.6 mm = 1.07 deg)
  ------------------------------------
  worst case                 +-0.169   -- 72% of budget spare

The dominant term is the DOWEL fit, not the pins.  If that ever needs
tightening, a O1.15 dowel in the DUT's O1.20 hole takes it to +-0.025.


---

# ADDENDUM I — SEAT BAR (user's idea, 2026-09-18)

User: "why not have a floor it can rest on in the 3D print, then we can seat
them properly."  Right, and it is strictly better than the Case A / Case B
split of Addendum H.

## Why it removes the unknown entirely

A pin descending into the hole stops at whichever obstruction it meets FIRST.
Set a bar so the tail lands while the head is still clear of the board, and the
bar always wins.  The head diameter -- the number no reachable source states,
which has now shaped three addenda -- stops mattering.

    protrusion = SEAT_Z - (carrier top - pin length)
    7.30       - (21.80 - 16.50) = 2.00 mm

## Bar, not floor

A full floor would have sealed off the soldering access that the 24 x 22
opening exists to provide.  The bar is 8 mm wide in Y, spans the cavity in X,
and leaves **12.9 mm** of height above it with open space either side.  Every
pin sits >= 4.00 mm inside its footprint.  Volume went 32.8 -> 35.6 cm3.

## Dowels stay on the bench method

The dowels also sit over the bar, but they are fitted FIRST, flush with the
carrier's underside, so they never reach down to it.  Seating them on the bar
instead would need a 19 mm dowel; 6.1 mm cut flush is simpler.

## The parameter that must be checked

`PIN_L = 16.5` is a vendor figure, and the user already owns pins.  **Measuring
one and correcting that line is now the only thing standing between this design
and a known-good assembly** -- and unlike every earlier open question, it needs
no supplier, no datasheet and no search.  The bar height recomputes from it.

The PCB depends on neither `PIN_L` nor `PIN_PROUD`.

## Note on the method

Three addenda (F, G, H) went into working around an unmeasurable head
dimension: an insertion direction, a superseded part, an un-superseding, and a
two-case procedure. The user's single question -- put a floor under it --
deleted all of it. Worth remembering that when a design starts branching on an
unknown, the better move is usually to add a feature that makes the unknown
irrelevant, not to enumerate the branches.


---

# ADDENDUM J — UNDERSIDE JOINTS, AND PADS TOO SMALL TO SOLDER (2026-09-18)

User asked what is soldered under the carrier.  Answer: with JLC assembly,
**only the five pogo tubes**.  Dowels are soldered from the top (fitted flush
underneath), J1/J2 leads are underside but are done flat on the bench or by
JLC's wave, and the test points are bare pads.

## Checking it found a defect

The pogo pads were **O1.60 round on 2.00 mm pitch** -> annular ring
**0.275 mm**.  That is the ring on the ONLY joints made by hand, reaching up
into a frame with a fine iron.  Far too thin.

The pitch constraint that has shaped this whole fixture blocks the obvious fix:
a round pad cannot grow past ~1.8 before the row shorts.

**Fix: oblong pads, stretched perpendicular to the row.**  The pitch is in X,
so Y is free.  1.60 x 2.60 keeps the row gap at 0.400 mm and gives
**0.775 mm** of ring in Y, where the iron goes.  Dowels O1.80 -> O2.40
(ring 0.675); isolated, so they stay round.

`check_carrier.py` gained a rule: any hand-soldered joint with < 0.45 mm of
ring is a blocker.

## And a fourth checker bug

The pad-to-pad clearance test measured centre distance minus the largest
dimension of each pad -- fine for circles, wrong for oblongs.  It reported
**-0.600 mm** across the pogo row, which is actually 0.400 mm clear in X.
Replaced with proper axis-aligned rectangle separation.

Fourth time this session a checker has been wrong before the board was; see
[[touchid-checkers-lie-more-than-the-board]].

## Silk moved

With DW pads at O2.40 the pogo labels at y = -2.0 fouled DW1.  Moved to
y = -3.4.  Caught by the silk-vs-pad rule added in Addendum D.


---

# ADDENDUM K — ONE SIDE, AND THE DOWELS JOIN THE BAR (2026-09-18)

User asked whether both faces need soldering.  **No -- bottom only.**  The hole
is plated, so its barrel already ties the two pads together; one fillet on the
underside is the entire joint, and the oblong pads give 0.775 mm of ring to wet.

Three reasons NOT to solder the top as well:

1. the top face is where the DUT lands.  A fillet there is a bump under the
   board, and the clearance available is only a few tenths of a mm
2. the pin's head sits 2.0 mm above the hole, physically in the way
3. the joint is ~3.6 mm from the plunger end -- a pogo pin has a spring and
   grease inside.  Working from the underside keeps the iron at the far end,
   and it should still be quick

## The dowels were on a different plan, and shouldn't have been

Addendum I left the dowels on the old "lay it flat on the bench, cut to 6.1 mm,
solder from the TOP" method.  Checking the one-side question exposed two
problems with that:

* a solder fillet on the TOP around a dowel is exactly where the DUT has to sit
  flat -- the same objection as (1) above
* a 6.1 mm dowel dropped into the frame would fall straight through the hole
  and land on the seat bar, well below the board

**Fix: cut the dowels to 19.0 mm and seat them on the same bar as the pins.**
From the bar at z=7.30 a 19.0 mm rod reaches 26.30, which is 4.5 mm above the
carrier top at 21.80.  They then pass through the board exactly like the pins
and solder from below in the same operation.

`gen_frame.py` computes and prints the dowel length from the bar height on
every run, so the two cannot drift.

Everything now seats on one datum and solders from one side.


---

# ADDENDUM L — DOWEL MATERIAL RESOLVED (2026-09-18)

User asked whether JLCPCB could print the dowels.  No, twice over:

1. **A printed dowel cannot be soldered.**  It would have to be a press fit or
   glued, into a hole whose fit is the registration datum.
2. **O1.0 x 19.0 mm is a 19:1 aspect ratio.**  The v2 jig's printed registration
   posts were O1.05 x 2.6 mm -- 2.5:1 -- and the user reported they "kept
   breaking off".  Seven times worse, on the feature that decides where the
   board sits.

## But it pointed at the answer

The open item was "a O1.0 rod that both fits and solders".  Stainless dowels
and drill blanks are the right size but take no solder; brass rod solders but
had no confirmed source.

**18 AWG solid copper wire is O1.024 mm.**

| | |
|---|---|
| in the carrier's O1.05 hole | 0.013 mm slop -- snug |
| in the DUT's O1.20 hole | **+-0.088 mm** |
| solders? | it IS copper |
| source | any electronics or hardware shop |
| cut length | **19.0 mm** (from the seat bar, per gen_frame.py) |

Revised error stack to the DUT's O1.20 pad (+-0.600 budget):

    hole position (fab)        +-0.050
    dowel in the DUT's O1.20   +-0.088
    pin tilt in its hole       +-0.019
    ------------------------------------
    worst case                 +-0.157   -- 74% of budget spare

Slightly BETTER than the +-0.100 previously assumed for a nominal O1.0 rod.

O1.0 brass rod remains the alternative if a stiffer dowel is ever wanted;
copper is softer but the rod is supported through 1.6 mm of board plus its
solder fillet and only sees a board being dropped onto it.

**This was the last unresolved item in the bill of materials.**


---

# ADDENDUM M — FAB PACKAGE BUILT (2026-09-18)

`carrier-v1-gerbers.zip` + BOM + CPL are in this folder and verified.

kicad-cli 9.0.9 from the KiCad PPA (the repo's `install_kicad_cli.sh` pins
jammy and fails on this noble container; installed from the 9.0 PPA instead).
Plot flags match the v7 package: corner origin, subtract-soldermask,
no-protel-ext, Excellon PTH/NPTH separate.

**`verify_fab.py` closes the loop back to the source.**  It re-reads the
plotted drill file, converts hole positions out of gerber space into board
coordinates, and compares them against `pcb-v7-zero-opens.kicad_pcb` itself --
not against the carrier generator.  All 7 pogo and dowel holes agree to better
than 0.002 mm; outline 47.000 x 58.000; 20 PTH and 4 NPTH with the expected
diameters; 0 failures.

BOM part numbers confirmed against JLCPCB's library on the day:
C9900176459 (XIAO RP2040, Extended) and C17408 (0805 100R 1%, **Basic**).
J1/J2 excluded on purpose -- THT assembly is not worth it for seven easy joints.

Open items at this point: only whether 3.3 V suffices to flash, which changes
a resistor value and nothing else, and measuring `PIN_L` for the frame.

---

## Addendum N -- zones, and the nine silkscreen warnings

### N.1  There are no zones on this board, so there is nothing to fill

Asked directly: `carrier-v1.kicad_pcb` contains **0 `(zone ...)` entries and
0 `(filled_polygon ...)` entries**. Compare `pcb-v7-zero-opens.kicad_pcb`,
which has 40 zones. The carrier is routed with explicit tracks only.

That is deliberate, not an omission. The board carries two standing rules:

* **Rule 1** -- no F.Cu anywhere inside the DUT rectangle (-10..10, -9.5..9.5)
  except the PP*/DW* pads, because the DUT's bottom face carries exposed gold
  (J4 6 x O2.0, J11 4 x O2.0, TP1-TP10) and hovers ~1.5 mm above this surface.
* **Rule 2** -- no copper at all inside x +-7.0 under the XIAO body, because the
  module's belly carries exposed GND / VIN(5V) / SWD pads.

A ground pour would flood straight into both of those keep-outs. Keeping the
pour out means hand-drawing the keep-out boundary and then trusting KiCad's
fill -- one more thing to get wrong on a board that has 27 segments and
8 nets total. There is no thermal or EMC argument for a pour on a fixture that
carries SWD at a few MHz and 3.6 V at a few mA over 47 x 58 mm.

So the "always refill zones before plotting" step in the main-board handover
does **not** apply here. `check_carrier.py` proves connectivity by union-find
over the tracks and vias themselves, and KiCad's own DRC independently
reports **0 unconnected items**.

### N.2  Nine silkscreen warnings, and what actually caused them

KiCad 9.0.9 DRC on the first plotted board reported 28 warnings: 19
`lib_footprint_issues` (expected and harmless -- footprints are generated
inline rather than pulled from a library, so KiCad cannot find a library
called `carrier`), plus 7 `silk_overlap` and 2 `silk_over_copper`.

Seven of the nine traced to **one** cause: the auto-placed reference
designator field. Every footprint emitted by `gen_carrier.py` carried its
`Reference` property at a fixed `(at 0 -2.6 0)` offset, which is fine on a
dense board with tidy footprints and wrong on this one, where the parts sit
in deliberately open space next to hand-written labels:

| collision | what happened |
|---|---|
| `R2` ref @ (13, 15.82) | landed on R3's pads *and* on the "SWD ESC" legend |
| `TP1` ref @ (-7, -15.6) | landed on "V+" and on "3.6 V IN (KEYED)" |
| `TP2` ref @ (7, -15.6) | landed on "GND" and on "3.6 V IN (KEYED)" |
| `U1` ref @ (0, -2.6) | U1's footprint origin is (0,0), nowhere near the module at y=23.5, so its designator landed in the middle of the pogo row, on the "GND" pin label |

**Fix: `hide_ref` now defaults to `True`.** Nothing is lost. Every part on
this board already carries a plain-language silk label -- `3.6 V IN (KEYED)`,
`V+`, `GND`, `SWD ESCAPE`, the five pogo names, `DW1`/`DW2`, `XIAO RP2040 --
USB-C AT TOP`. R1/R2/R3 are the same 100R part, so their designators carry no
assembly information. JLC place from the CPL file, not from silkscreen.

The two remaining warnings:

* `"GND"` @ (7, -15.2) sat 0.1 mm from `"3.6 V IN (KEYED)"` @ (0, -16.2) --
  two of my own labels, on adjacent scanlines. The bottom row was respaced:
  V+/GND to y=-15.4, the title to y=-17.3, the meter warning to y=-18.9.
* `"SWD ESC   DIO CLK RST V+ GND"` @ (21.08, 15.4) ran under the nRST_R via at
  (21.08, 15.88) and was clipped by the via's mask opening. That one-line
  legend is gone. J2 now gets a `SWD ESCAPE` title at (21.08, 10.0) and five
  0.55 mm labels -- `DIO CLK RST V+ GND` -- at y=11.5, one directly under each
  pin, which is both legal and easier to read than a legend you have to count
  across.

J1 also gained `+` and `-` marks at (-3.1, -13.0) and (3.1, -13.0). The V+/GND
row above belongs to the test points TP1/TP2; without these two marks the
connector's own polarity was never stated on the board.

### N.3  The checker was blind to this whole class

`check_carrier.py` rule 7e only compared silk text against **pads**. It could
not have caught any of the nine, because they were text-vs-text and
text-vs-via. Rule 7e now covers:

* silk vs pad (axis-aligned rectangle overlap, as the pad rule already does)
* silk vs **via**
* silk vs **silk**, every pair
* silk vs the **board outline**

and the character-width estimate went from `0.62 * size` to `0.78 * size`,
which is KiCad's actual stroke-font advance, so the checker now errs toward
failing rather than passing.

### N.4  Result

```
check_carrier.py   PREFLIGHT: 0 blockers
kicad-cli drc      0 errors, 0 unconnected items,
                   19 warnings -- all lib_footprint_issues
verify_fab.py      VERIFY: 0 failures
                   PTH 20 holes (O0.4 x4, O1.0 x4, O1.02 x5, O1.05 x7)
                   NPTH 4 x O3.2, Edge.Cuts 47.000 x 58.000
```

`carrier-silk-top.png` is F.Cu + F.Mask + F.SilkS + Edge.Cuts plotted straight
out of the board file. Where silk appears to sit on a trace in that render --
`+` over the VSTOR run, `3.6 V IN (KEYED)` over the same run -- the trace is
under solder mask on the real board and invisible; silkscreen prints on top of
mask. Only mask *openings* (pads, vias) eat silkscreen ink, and DRC confirms
there are none left under any label.

---

## Addendum O -- the orientation marker was readable two ways

Writing the plain-language walkthrough (`carrier-explained.png`) surfaced a
defect in the silkscreen that no checker would ever have caught, because it is
a defect in *wording*, not geometry.

The label at (0, 11.6) read `^ +Y  SPACEBAR EDGE`.

The KiCad file format is Y-DOWN. Verified empirically rather than argued:
plotted to SVG, the title block at board y=+36.8 lands at the BOTTOM of the
page and the meter warning at y=-18.9 lands at the TOP. The gerber agrees --
with `aux_axis_origin` at (-16, 38), gerber Y = 38 - y, so y=+36.8 becomes
gerber Y=1.2, near the bottom of the board in gerber's Y-up frame. The SVG
page, the KiCad canvas and the gerber are all the same top view, and on all
three **+Y runs downward**.

So the caret points toward -Y. Read as a direction indicator -- "+Y is this
way" -- it is simply wrong. Read as a pointer at the DUT edge immediately
above it, it is right, because that edge is y=+9.5, which *is* the spacebar
edge.

An orientation marker that can be read backwards, on a fixture where backwards
lands SWDIO on the GND pin, is not a marker. Both readings are removed:

* the label is now `SPACEBAR EDGE OF YOUR BOARD LINES UP HERE` at (0, 10.6),
  size 0.65 -- no glyph, no axis name, and it sits directly against the DUT's
  +Y edge so position alone carries the meaning;
* a **drawn box** now marks where the DUT lands: four F.SilkS lines 0.15 wide
  at x +-10.3, y +-9.8, i.e. 0.3 mm outside the 20.00 x 19.00 body. Nearest
  approach to any copper is 0.275 mm, to DW1/DW2's O2.40 pads.

This is the first silkscreen geometry on the board that is not text, so
`gen_carrier.py` gained a `SILK_LINES` list and `check_carrier.py` gained a
matching rule: every silk line is checked against every pad, every via and
every label. The DUT rectangle itself is now a named constant
(`DX0_, DX1_, DY0_, DY1_`) beside `MH_DUT`, so the box that is drawn and the
rectangle the no-F.Cu rule polices are literally the same four numbers.

`gen_explain.py` is new and imports `gen_carrier` for every coordinate it
draws, so the explanatory picture cannot drift from the board either. It is
rendered with `invert_yaxis()` for the same reason the caret was wrong: the
file is Y-down, so that inversion is what makes it a true top view.

Re-verified after the change: `PREFLIGHT: 0 blockers`, `kicad-cli drc` 0 errors
/ 0 unconnected / 19 lib_footprint_issues only, `verify_fab.py: 0 failures`.

---

## Addendum P -- verifying the printed frame, and two faults it had

Before ordering, the frame was checked against the carrier the way the carrier
is checked against the DUT: with a script that interrogates the built solid
rather than re-reading the generator's own `print()` statements.

`verify_frame.py` is new. It loads the CadQuery solid, imports `gen_carrier`
for the pin, dowel and screw positions, and answers every question by
point-in-solid test (`BRepClass3d_SolidClassifier`) at real coordinates:

1. the frame's screw holes ARE the carrier's screw holes, to 1e-4 mm;
2. all seven tails (5 pogo + 2 dowel) land on solid seat bar, and how close
   each one is to falling off its edge;
3. nothing solid sits between the bar and the carrier in any pin's corridor;
4. a 2.5 mm radius of free space exists round every tail at the carrier's
   underside, where the joints are actually made;
5. every tail is inside the 24 x 22 opening, with margin;
6. the recess accepts the carrier at REAL tolerances;
7. no blind bore exceeds 5:1;
8. every boss is solid to O8.0 and drilled clean through, clear of the bar;
9. protrusion + pin-length tolerance stays inside the spring's stroke;
10. the engraved arrow points at +Y.

It found two faults.

### P.1  The recess could not accept the carrier

`CLR` was 0.20 mm per side. JLCPCB route a PCB outline to **+-0.20 mm** and MJF
PA12 holds **+-0.30 mm**. Worst case the carrier is 47.20 x 58.20 and the recess
is 47.10 x 58.10: **the board does not go in, short by 0.10 mm in both axes.**

Nominally it fit, which is why it survived this long. It is exactly the class of
defect that only appears when you write the tolerances down.

`CLR` is now **0.40 mm**, which leaves 0.30 mm of slack in the worst case. This
costs nothing: the carrier is located by its four M3 screws (O3.2 holes on M3 =
0.1 mm of play per side), not by the recess walls. The frame grows to
57.80 x 68.80 x 22.00 mm, 36.6 cm3.

### P.2  The dowels were sitting on the edge of the seat bar

The bar was 8.0 mm wide in Y, centred on the pin row at y=+3. The dowels are at
y=0, so the bar ended 1.00 mm past a dowel's centre -- and a O1.02 dowel has
only **0.49 mm of bar under its far side**. A dowel that tips as you solder it
walks off the edge, and the dowels are what aim the whole fixture.

The bar is now **10.0 mm wide, centred at y=+2.0**, between the pin row and the
dowel row. Every tail is now >= 3.00 mm from an edge. Iron access is unchanged:
the opening still leaves 6 mm of clear cavity on each side of the bar.

### P.3  The arrow, again

`wall_check.py` at a 1.5 mm threshold still found a 30-slice cluster at the
engraved +Y arrow -- its bands were 1.2/1.3 mm. It is now sized from a single
`ARROW_BAND = 1.7` constant, 0.5 mm deep, 10 mm wide, with an assert.

Its reporting frame is trimesh's per-section 2D frame, which is arbitrary, so a
hit could be counted but not located. `thin_world.py` is new and answers in the
part's own millimetres: it voxelises the STL and runs a Euclidean distance
transform, so 2 x EDT is the local thickness at every point. Result:

```
thin < 1.5 mm  (voxel 0.35 mm)   0 voxels
thin < 2.0 mm  (voxel 0.35 mm)   0 voxels
```

**Nothing anywhere in the frame is thinner than 2.0 mm.** JLC3DP's MJF minimum
is 0.8 mm. The remaining single-slice hits `wall_check.py` reports at 1.5 mm are
tangential slices at corners, not features.

### P.4  Drift, closed

`gen_frame.py` was carrying its own typed copies of the carrier outline and the
four screw positions. It now does `import gen_carrier as G` and takes
`BX0/BX1/BY0/BY1` and `MH` from it. A frame built against a stale outline is a
frame that does not fit, and nothing downstream would have caught it.

### P.5  What is still unverified: PIN_L

`PIN_L = 16.5` is the P75-E2 datasheet length. **It has not been measured.** The
seat bar height is `CAR_TOP - PIN_L + PIN_PROUD`, so every 0.1 mm of error in
PIN_L moves the contact tip by 0.1 mm. `gen_frame.py` now prints a banner to
that effect on every run and `verify_frame.py` raises it as a note, gated on a
new `PIN_L_OK` flag that is `False` until someone sets it.

The failure is not catastrophic either way. The pin drops in from the top: its
O1.02 body passes the O1.05 hole, and it stops on whichever it reaches first --
the bar under its tail, or its own O1.3 head shoulder on the carrier's top face.
Both are repeatable across five pins. The bar wins as long as `PIN_PROUD`
(2.0 mm) exceeds the head's exposed length, which is the point of the bar.

A new assert guards the one outcome that would matter:

```
PIN_PROUD + PIN_TOL <= PIN_STROKE - 0.15     # 2.0 + 0.3 <= 2.35
```

The DUT is pressed down until it stops on the carrier's own top face, so the
protrusion IS the compression at full seat. At 2.0 mm of 2.50 mm stroke there is
0.5 mm spare; even if PIN_L is 0.3 mm longer than assumed, 0.2 mm remains and
the pins never hard-bottom.

---

## Addendum Q -- checking the print against JLC3DP's published rules

Addendum P checked the frame against my own rules of thumb. This one checks it
against the vendor's, fetched from
<https://jlc3dp.com/help/article/3d-printing-design-guideline> on 2026-09-18:

| rule | published value |
|---|---|
| tolerance | +-0.3 mm within 100 mm (MJF nylon **and** FDM plastic) |
| min wall, nylon MJF | 5x5 1.0 / 10x10 1.2 / 50x50 1.5 / 100x100 2.0 mm |
| min wall, FDM | 50x50 1.6 / 100x100 2.0 / 200x200 2.5 mm |
| hole depth | O1.5 -> h 1.5..4.5, O2.0 -> h 2.0..6.0, i.e. **3 x diameter** |
| escape holes | >= 2.5 mm; two needed below 3 mm |

Two of those overturned things this project had assumed.

### Q.1  The screw holes were over the depth limit, and the wrong size anyway

The frame had `MH_D = 2.9` through 11.2 mm. I had been calling that "3.9:1,
under the 5:1 limit" -- but 5:1 was **my** number, not JLC's. Theirs works out
to 3 x diameter, and 3.9:1 is over it. This is the same rule the v2 jig's
O1.15 x 11.0 bores broke, which is what started this whole redesign.

Worse, O2.9 was the wrong diameter regardless of depth. An M3's major diameter
is 3.0 mm, so a O2.9 hole leaves **0.05 mm of thread engagement per side** --
a self-tapping screw would have stripped it on the first turn. A plastic-forming
screw wants roughly 0.8 x major.

Now `MH_D = 2.5` and `BOSS_Z = 13.0`:

* depth (17.0 - 13.0) + (20.2 - 17.0) = **7.2 mm**, = 2.9:1, inside their 3:1
* 7.2 mm of engagement at O2.5 is 2.9 x diameter of thread in plastic
* the M3 x 8 screws reach 6.4 mm past the 1.6 mm carrier, so they cannot bottom
  out in a 7.2 mm hole either -- asserted in the generator and re-checked in
  `verify_frame.py`

### Q.2  The orientation arrow moved off the top face for good

The top face is a 5.0 mm band, and any arrow engraved into it leaves 1.2-1.7 mm
of land on each side. Against a published minimum wall of 1.5-2.0 mm for a part
this size, that is arguing about whether a 0.5 mm groove backed by 21.5 mm of
solid counts as a wall. It is not worth arguing about.

The mark is now a **triangle cut into the OUTER +Y face**: 20 x 11 mm, 1.2 mm
deep into a 5.0 mm wall, leaving 3.8 mm behind it. Ten times more legible, on
the side you can see with the jig on the bench, and nothing about it is thin at
any threshold. `verify_frame.py` checks that it is present on +Y, that material
remains behind it, and that the -Y face is untouched -- a mark on both faces
would be worse than none.

It matters because `b2f()` puts the four screw holes on a rectangle at
(+-19.5, +-25), symmetric in both axes, while the opening beneath is offset to
sit under the pin row. A carrier bolted in 180 degrees round lines up perfectly
and puts every pin tail over solid deck.

### Q.3  Material: PLA is no longer the right answer

`README.md` said FDM PLA was enough because "this frame's smallest feature is a
O2.9 hole and it sits on your desk". That was written before the seat bar
existed. The bar is a **height-setting surface that a hot pin tail rests on**:
each pin is soldered at the carrier, 14.5 mm up a brass tube whose other end is
on the bar. PLA softens around 60 C.

How much heat actually arrives at the tail has **not been measured**, so this is
reasoning and is labelled as such in `ORDER.md`. MJF PA12 removes the question;
PETG or ABS are the FDM compromise.

### Q.4  Final state of the print

```
frame            57.80 x 68.80 x 22.00 mm, 35.8 cm3
recess           47.8 x 58.8 x 1.8, worst-case slack 0.30 mm
opening          24 x 22, closest tail 3.25 mm from an edge
seat bar         10 mm wide, top z = 7.30, every tail >= 3.00 mm from an edge
screw holes      O2.5 x 7.2 mm = 2.9:1 (limit 3.0:1), 6.4 mm of screw in it
orientation      20 x 11 x 1.2 triangle on the outer +Y face, 3.8 mm behind it
min wall         nothing under 2.0 mm anywhere (distance transform, 0.35 voxel)
dowels           cut to 19.0 mm
verify_frame.py  0 blockers, 1 note (PIN_L unmeasured)
```

---

## Addendum R -- the whole checklist, not four lines of it

Addendum Q checked four rules off JLC3DP's design guideline. Asked whether that
meant the print was clear to order, the honest answer was: I had checked the
four I went looking for. So the full page was pulled and every numbered rule on
it was turned into a check inside `verify_frame.py`.

Three more things came out of it.

### R.1  Engraved detail has a published minimum, and the old arrow was under it

> Engraved details -- minimum **0.8 mm deep & 0.8 mm wide** (nylon MJF),
> **1.0 mm deep & 1.0 mm wide** (FDM plastic).

The top-face arrow of Addenda P/Q was **0.5 mm deep**. Under both. It had been
argued about twice on wall-thickness grounds and would have failed on a rule
neither of those arguments touched.

The +Y face mark is 1.2 mm deep and 11 mm across at its narrowest -- clear of
both, and now checked rather than assumed.

### R.2  Static-assembly clearance: 0.40 was legal for MJF and not for FDM

> Clearance, static assembly -- **0.2-0.4 mm** (nylon MJF), **0.5 mm** (FDM).

`CLR` was 0.40 -- at the top of the MJF band and under the FDM figure. Since the
material is still an open question (Addendum Q.3), a value that is only legal on
one process is not a value. `CLR` is now **0.50**, legal on both, and the
worst-case recess slack goes from 0.30 to 0.50 mm. The frame grows to
58.00 x 69.00 x 22.00 mm, 35.9 cm3.

### R.3  Hole tolerance makes O2.5 a coin toss for a self-tapping screw

> Tolerances -- holes **+-0.3 mm** (MJF), **+-0.4 mm** (FDM).

Q.1 set `MH_D = 2.5` for thread engagement. Applying their hole tolerance to it,
a O2.5 hole comes back anywhere from 2.2 to 2.8, and at 2.8 an M3 has 0.1 mm of
material per side to form a thread against.

`MH_D` is now **2.4** -- 0.8 x major, the textbook thread-forming hole for a
soft thermoplastic -- with `BOSS_Z` raised to 13.5 so the depth stays inside the
3:1 rule (6.7 mm / 2.4 = 2.8:1). The spread is still wide and is written down in
`ORDER.md` rather than hidden: the carrier is screwed down once and the DUT
swaps without touching the screws, so a loose one is a nuisance, not a failure.

### R.4  Rules that do not apply, said out loud

* **Escape holes** (>= O2.5, two below O3.0): the frame has an open bottom and
  no enclosed voids. Rather than assert that, `verify_frame.py` re-reads the STL
  and counts shells -- an enclosed void is exactly a second shell. 1 shell,
  watertight.
* **Small columns** (D2.0 -> h 2-4, D3.0 -> h 3-6): nothing here is a column.
  The bosses are O8.0 x 3.5 and the seat bar is a wall.
* **Build size**: 58 x 69 x 22 is inside MJF's 370 x 276 x 360 and above FDM's
  30 x 30 x 10 minimum.
* **Protrusions / fasteners > 1.5 mm**: seat bar 10.0, boss wall 2.8.

### R.5  PIN_L is now a BLOCKER

`verify_frame.py` used to raise the unmeasured `PIN_L` as a note, and a note is
something you scroll past. It is now a **blocker**, so the script cannot print
`0 blockers` until `PIN_L_OK` is set. The seat bar's entire job is to put the
contact tip at a known height, and it computes that height from `PIN_L`; an
unmeasured `PIN_L` makes the bar a guess with extra steps.

This makes `verify_frame.py` the print's equivalent of `preflight.py` -- the
single gate in front of spending money. Verified both ways: with `PIN_L_OK`
temporarily set True the script reports `0 blockers` and
`every published JLC3DP rule checked above -- clear to order`; restored to
False it reports `1 blockers`.

---

## Addendum S -- the listing had a drawing, and the drawing broke the design

Dan sent the Amazon listing he bought the pins from (ASIN B0D48VHRY4). Its
third image is a dimensioned drawing. Transcribed in
`datasheets/P75-E2-SOURCE.md`; the numbers that matter:

```
tip cone (O1.3 head)          1.5 mm
plunger shank (O0.74)         2.54 mm
BARREL (O1.02, gold)         12.5 mm
                             ------
overall                      16.54 mm
```

The chain closes exactly, which is more than can be said for the listing's
prose: the title says 16.5 mm and the description says 16 mm.

`Ø1.02`, `Ø1.3`, `Ø0.74` and ~16.5 all match what this project had been
assuming. One number was never in the project at all, and it is the one that
mattered: **the barrel is only 12.5 mm of the 16.54. The other 4.04 mm — head
plus plunger shank — lives outside it.**

### S.1  The bug

The seat bar height was `CAR_TOP - PIN_L + PIN_PROUD`, i.e. derived from the
**total** length, aiming for 2.0 mm of contact tip standing proud of the
carrier. Put the real dimensions through it:

```
bar top z = 21.80 - 16.54 + 2.0 = 7.26
tip       z = 7.26 + 16.54 = 23.80   (2.00 proud -- as intended)
BARREL TOP  = 7.26 + 12.5  = 19.76   (carrier hole spans 20.20..21.80)
```

The barrel's top would sit **0.44 mm below the underside of the board**. What
would actually be inside the Ø1.05 hole is the **Ø0.74 plunger shank** — the
moving part.

Two consequences, either of which ruins the fixture:

1. **Solder it and the pin dies.** The joint is made at the carrier; solder on
   the plunger shank fuses it to the barrel. Five rigid brass posts with no
   spring, pressed against a board that needs compliance.
2. **Even unsoldered, the guide is gone.** Ø0.74 in Ø1.05 is 0.155 mm of radial
   slop, ten times the 0.015 mm the barrel gives. The whole reason for putting
   the precision in the PCB instead of the print evaporates.

Nine addenda of work rest on "the barrel is soldered into the carrier, so the
precision is at the guide". That sentence was never true at 2.0 mm proud.

### S.2  The fix: derive from the barrel, never from the total

```
SEAT_Z    = CAR_TOP - PIN_TUBE_L + TUBE_PROUD   = 21.80 - 12.5 + 0.5 = 9.80
PIN_PROUD = PIN_L - PIN_TUBE_L + TUBE_PROUD     =  16.54 - 12.5 + 0.5 = 4.54
```

`PIN_PROUD` stops being a design choice. It is whatever the pin's own geometry
says once the barrel is seated, and the right answer is to stop choosing it.

Three invariants now assert in `gen_frame.py` and are re-checked against the
built solid in `verify_frame.py`:

1. **barrel top >= carrier top.** Only the Ø1.02 barrel may be in the hole. At
   TUBE_PROUD = 0.5 it stands 0.5 mm above the board for a proper fillet, and
   the Ø0.74 shank starts 0.5 mm clear of the copper.
2. **PIN_PROUD > PIN_STROKE.** 4.54 > 2.50, so the plunger runs out of travel
   before the DUT can descend to the carrier. "No copper under the DUT" stops
   being a drawing rule and becomes a physical one: **the board cannot touch
   this surface, whatever anyone presses.** Minimum gap 2.04 mm.
3. **DOWEL_PROUD >= PIN_PROUD + 2.0.** The dowels were 4.5 mm proud, which is
   *below* the new 4.54 mm tip height -- the DUT would have met a pin before it
   was threaded on either dowel. Now 7.0 mm, a 2.46 mm lead.

Falling out of that: dowels still cut to **19.0 mm** (12.0 inside + 7.0 proud),
unchanged by coincidence. The frame is 58.00 x 69.00 x 22.00, 37.1 cm3.

### S.3  How it is meant to feel now

The DUT is threaded onto both dowels, drops 2.46 mm, then meets five tips. Press
to about 60% of travel -- roughly 300 g, easy to hold for the few seconds a
flash takes -- and the board sits **3.04 mm** above the carrier. Press harder
and the plungers bottom at 2.04 mm and stop. There is no way to reach the
copper.

### S.4  What is still unmeasured

`PIN_STROKE = 2.50` and the 100 g spring force are **not on this listing** and
remain generic P75-series figures. Stroke is load-bearing for invariant 2, so it
is recorded as unconfirmed in `datasheets/P75-E2-SOURCE.md`.

And the blocker moved: it used to say "measure PIN_L". It now says **measure
PIN_TUBE_L** -- the gold section alone -- because that is the number the bar
height is computed from. Get the total length wrong by 0.5 mm and the tips are
0.5 mm off. Get the barrel wrong by 0.5 mm and the wrong part of the pin is in
the board.

---

## Addendum T -- the barrel, measured

Dan put calipers on the gold barrel: **13.00 mm**. The seller's drawing said
12.5. Half a millimetre, and it moves two things:

```
                 drawing 12.5      measured 13.00
seat bar top       9.80 mm            9.30 mm
dowel length      19.0 mm            19.5 mm
```

Nothing else changes, because the design was restructured in Addendum S to
derive from the barrel. `PIN_TUBE_L` is now the only measured pin dimension and
the only one the print is gated on -- `verify_frame.py` reports **0 blockers,
every published JLC3DP rule checked, clear to order**.

### T.1  Why the chain no longer closes, and why that is right

The drawing's four numbers summed exactly: 1.5 + 2.54 + 12.5 = 16.54. With a
measured barrel they cannot all still hold. Rather than keep the old total and
quietly shrink the plunger to make the arithmetic work, the generator keeps the
drawing's **plunger** (head 1.5 + shank 2.54 = 4.04) and lets the overall follow
to 17.04. One number is now real, three are still the drawing's, and the code
says which is which.

### T.2  Two flags, not one

`PIN_L_OK` used to gate everything. It is now split:

* **`TUBE_L_OK`** -- the barrel. This is the ordering gate, and it is now True.
  Get it wrong and the wrong part of the pin sits in the board (Addendum S).
* **`PIN_L_OK`** -- tip to tail. Still False. It sets only how far the contact
  tip stands proud (4.54 mm) and can never change which part of the pin is in
  the hole, so it is a NOTE. Both invariants survive a 1.5 mm error in it.

A blocker that cannot change the outcome is noise, and noise is what gets
scrolled past. Only the barrel earns the blocker.

### T.3  State at order time

```
frame            58.00 x 69.00 x 22.00 mm, 36.9 cm3, 1 shell, watertight
seat bar         top z = 9.30, 10 mm wide, every tail >= 3.00 mm from an edge
barrel in hole   top z = 22.30, 0.50 mm proud, O1.02 in O1.05 = 0.015 mm/side
tip / travel     4.54 mm proud, 2.50 mm stroke -> DUT stops 2.04 mm up, always
working point    60% travel -> DUT sits 3.04 mm up, ~300 g
dowels           cut to 19.5 mm (12.5 inside + 7.0 proud), 2.46 mm of lead
min wall         nothing under 2.0 mm anywhere
screw holes      O2.4 x 6.7 = 2.8:1, 6.4 mm of M3 x 8 in 6.7 mm of plastic
carrier PCB      unchanged -- 0 blockers, 0 DRC errors, 0 fab-file failures
```

---

## Addendum U -- compressed and relaxed, and the number that had no source

Dan measured the pin in both states:

```
gold barrel                 13.00 mm
overall, relaxed            17.00 mm
overall, fully compressed   14.50 mm
```

Three measurements, and everything else is arithmetic on them:

| derived | value | drawing said |
|---|---|---|
| **stroke** = relaxed - compressed | **2.50 mm** | not on the listing at all |
| plunger exposed = relaxed - barrel | 4.00 mm | 4.04 |
| head cone = compressed - barrel | 1.50 mm | 1.5 |
| shank = plunger - head | 2.50 mm | 2.54 |

### U.1  The stroke was the last unsourced load-bearing number

`PIN_STROKE = 2.50` had been carried since the beginning as a generic
P75-series figure. Addendum S then made it structural: invariant 2 is
`PIN_PROUD > PIN_STROKE`, which is what guarantees the plunger runs out of
travel before the DUT can descend onto the carrier's copper. A physical
guarantee resting on a number nobody had checked is not a guarantee.

Measuring relaxed and compressed gives it directly. **2.50 mm, confirmed.**

### U.2  The measurements validate each other

The Ø0.74 shank works out at **2.50 mm** -- exactly the stroke. That is not a
coincidence, it is how the part has to be built: at full compression the shank
disappears into the barrel and only the 1.50 mm head cone is left outside. A
shank longer than the stroke would jam on the barrel's mouth rather than
bottoming internally, and a shank shorter would waste travel.

So the three measurements are mutually consistent, and they agree with the
seller's drawing to within 0.04 mm on every segment. Both facts are now
asserted:

```python
assert abs((PIN_HEAD_L + PIN_SHANK_L + PIN_TUBE_L) - PIN_L) < 1e-9
assert PIN_SHANK_L <= PIN_STROKE + 1e-9
```

### U.3  What moved

Almost nothing, which is the point of having restructured around the barrel in
Addendum S. `SEAT_Z` depends only on `PIN_TUBE_L`, which was already measured in
Addendum T, so **the STL is geometrically unchanged**. Only the derived
tip height shifted:

```
tip proud        4.54 -> 4.50 mm
DUT resting gap  2.04 -> 2.00 mm
dowel lead       2.46 -> 2.50 mm
```

### U.4  What is still unmeasured, and where it bites

The three **diameters** are still the drawing's. The print does not depend on
any of them. The **carrier PCB** depends on one: its holes are Ø1.05 against a
stated Ø1.02 barrel, 0.015 mm per side. If the real barrel is over Ø1.05 the
pins do not go in and the board needs new gerbers.

That is now the only open item, and it is an order-gate for the **PCB**, not
for the print -- recorded in `ORDER.md` and as a note in `verify_frame.py`
rather than a blocker, because it cannot be resolved by anything in this repo.

---

## Addendum V -- the last number, and the budget it changed

Barrel diameter, measured 2026-09-18: **Ø1.00 mm**. The drawing said Ø1.02.

Every dimension this fixture depends on is now a caliper reading. The pin's
entry in `datasheets/P75-E2-SOURCE.md` is measurements with the seller's drawing
kept only as the cross-check it turned out to be.

### V.1  The hole stays at Ø1.05

Ø1.00 in Ø1.05 is 0.05 mm diametral, **0.025 mm per side** -- looser than the
0.015 the drawing implied. The obvious reaction is to shrink the hole toward the
pin. That would be wrong: JLCPCB hold plated holes to about ±0.05 mm, so a
Ø1.02 nominal hole can come back at Ø0.97 and the pins do not go in at all. A
fixture that is slightly loose beats a batch of five boards that reject the
part. **No change to the carrier.**

### V.2  It moved the dominant error term

`verify_frame.py` now computes the tip-to-pad budget instead of quoting one:

```
0.050  carrier hole position (JLCPCB)
0.025  barrel slop in the hole
0.141  barrel cocked over 4.50 mm of overhang
0.088  DUT on the dowels
0.050  DUT pad position
-----
0.354  worst case -> 59% of the 0.600 mm radius a O1.20 pad allows
```

The largest term is no longer the dowels, it is **the barrel cocking in its own
hole**: 0.05 mm of diametral clearance across only 1.6 mm of board is ±1.79°,
and 4.50 mm of overhang turns that into 0.141 mm at the tip.

That is a worst case that assumes something holds each pin cocked. Nothing does
-- the pin hangs through the board with 12.5 mm of barrel below it and rests on
the seat bar, so gravity stands it plumb. The practical mitigation is "do not
nudge them while soldering", which is advice, not geometry.

It also explains why Addendum S's fix was worth the trouble in a second way:
had the Ø0.74 plunger stayed in the Ø1.05 hole, this term would have been
0.155 mm of slop plus a tilt of ±5.5 deg, and the budget would have blown.

### V.3  Everything that is left

```
Ø0.74 shank, Ø1.3 head   nothing depends on either
spring force 100 g       only decides how hard to press
18 AWG dowel wire        assumed Ø1.024, second largest term in the budget.
                         A consumable, cut by hand -- blocks no order, but
                         worth a caliper before cutting two 19.5 mm lengths.
```

Both orders are clear.

---

# ADDENDUM W — THE Y-DOWN TRAP, FIFTH TIME (2026-09-20)

Dan had the carrier PCB and the printed frame in hand and said the frame's
opening looked like it was in the wrong place.  It is not.  **My diagrams were.**

`check_hole_position.py` and `check_overlay.py` (both written this session) plot
with **+Y UP**.  The board renders and displays **Y-DOWN**
(memory: `touchid-y-axis-sign-trap`, `touchid-spacebar-edge-is-plus-y`).  So both
pictures were a vertical MIRROR of the physical part: they put the XIAO at the
top and the spacebar edge at the top, when on the real board J1 / the 3.6 V input
is at the top and the spacebar edge is at the bottom.

Nothing in `gen_carrier.py` or `gen_frame.py` is affected.  The frame is built
from `b2f()` on the carrier's own board-local coordinates, so the opening lands
under the pogo pins regardless of how anything is drawn.  Verified again:

* all 5 pogo pins inside the opening, worst margin 4.00 mm
* both dowels inside, 3.25 mm each
* all 4 screw bosses outside it

**Window position measured from the frame's outer walls, in the orientation you
hold it (J1 end up, arrow wall down):**

| from | to window edge |
|------|----------------|
| top wall (J1 / power-in end) | 16.5 mm |
| bottom wall (engraved arrow, spacebar edge) | 30.5 mm |
| left wall | 9.5 mm |
| right wall | 24.5 mm |

`check_overlay_v2.py` -> `overlay-check-v2.png` draws both parts in the true
orientation.  The two earlier PNGs are kept but are superseded and should not be
used.  **Rule for any future drawing in this repo: plot at (x, -y), or state the
convention on the figure.**

---

# ADDENDUM X — THE V1 FRAME IS SCRAP: A Y-DOWN/Y-UP MIRROR (2026-09-20)

Dan said the window looked like it was in the wrong corner, then said it was
under the XIAO.  He was right both times.  I argued for six messages, produced
five overlay drawings, and did not check the generator until he insisted.

**The bug.**  `gen_frame.py`:

    def b2f(x, y):
        return (x - CCX, y - CCY)        # WRONG

KiCad is **Y-down**; cadquery is **Y-up**.  This fed the carrier's Y-down
coordinates straight into a Y-up solid modeller.  Every Y-asymmetric feature of
the frame came out mirrored: the opening, the seat bar, and the orientation
mark.  X was unaffected, which is why the part looked *nearly* right.

**Consequence.**  The carrier is 47 x 58 in a 48 x 59 recess, so only two
placements exist, and neither works:

| placement | pins land at | window | verdict |
|---|---|---|---|
| +u along +X | frame Y +6.00 | Y -18.0..+4.0 | outside by 2 mm |
| rotated 180 | frame X +7.5..+15.5 | X -19.5..+4.5 | outside |

In the first, the window overlaps the **XIAO** footprint by 11.12 mm.

**Why every check passed.**  `verify_frame.py` line 27:

    b2f = F.b2f

The checker imported the function under suspicion.  It measured the part in the
same mirrored frame the part was built in, agreed with it perfectly, and printed
"FRAME: 0 blockers".  `thin_world.py`, the JLC3DP rule sweep and the tip-to-pad
error budget were all correct *and all irrelevant* — none of them tested the one
relationship that mattered.  Every drawing I made on 2026-09-20 mapped both
parts through the same wrong function, so they agreed with each other too.
This is `touchid-checkers-lie-more-than-the-board` in its purest form.

**The fix** — `gen_frame_v2.py`:

    return (x - CCX, CCY - y)

and the orientation mark moves to the **-Y** outer face, because board +Y (the
DUT spacebar edge) now maps to frame -Y.

**New in v2: TL / TR / BL / BR engraved 0.6 mm into the top face**, in the 5 mm
band over the solid outer wall.  They *define* the canonical view: turn the part
recess-up until the four labels read upright, and TL/TR/BL/BR mean exactly what
they say.  The carrier's corners take the same names — carrier TL goes on frame
TL — so orientation is now a thing you read off the part, not a convention two
people have to agree on in words.

**New in v2: `verify_frame_v2.py` imports nothing from the generator.**  It
re-derives the board->frame mapping from first principles and measures the STL
by ray parity.  Proof that it can disagree: pointed at `flash_frame.stl` (v1) it
exits 1 with *"THERE IS SOLID DECK AT frame (-7.50,+7.00) ... this part has no
window where the carrier needs one"*.  Pointed at v2 it passes 26 checks.

**Standing rule from here on: a checker may not import the code it checks.**

**Cost.**  The v1 print is scrap (C$17.48 + shipping).  The carrier PCB is
UNAFFECTED — its pads come from the DUT in one consistent 2D frame and never
touch the 3D chain.  The Mouser order is unaffected.

## X.1 — arrow moved to the TOP face (same day)

Dan: *"get rid of the arrow on the side and put it on the top so you can see it
from a top down view."*  Correct, and it removes the last reason anyone has to
orbit the model to work out which way it goes.

v1's justification for the side placement was that a 5.0 mm top band could not
carry an arrow without leaving 1.2-1.7 mm bands, flagged by wall_check.py
against JLC3DP's 2.0 mm minimum.  **That flag was spurious**, and the v1 comment
half-admitted it at the time ("whatever the truth about a 0.5 mm groove backed
by 21.5 mm of solid").  A 0.6 mm groove in a face with 21.4 mm of solid block
beneath it creates no thin wall: the material beside the groove is continuous
with the whole part.  The TL/TR/BL/BR labels settle the argument -- same band,
same depth, no flag.

Arrow now: 14.0 x 2.8 mm triangle, 0.6 mm deep, engraved into the top band on
the -Y side, in the clear span between BL and BR, pointing outward at the DUT's
spacebar edge.  Both outer side walls are now completely clean, and
`verify_frame_v2.py` asserts that: it fails if anything is pocketed into either
+/-Y face, and fails if the arrow is missing from the top band or duplicated in
the +Y band.

Everything you need to orient this part is now visible looking straight down.
