# carrier-v1 — flashing fixture for pcb-v7 (DRAFT, not ordered)

> **Ordering? Read `ORDER.md`, not this file.** It carries the current numbers
> and the one thing that must be measured first. Parts of the tables below
> predate Addenda N-Q and are kept for the reasoning, not the figures.

Replaces `cad/v7-release/flash-jig/`, which arrived unusable.  **Two parts, one
of each service, both from JLCPCB.**  Full reasoning: `CARRIER-DESIGN.md`.

## Files

| file | what | where it goes |
|---|---|---|
| `carrier-v1.kicad_pcb` | THE carrier. **47 x 58 mm**, 2 layer, 1.6 mm | open in KiCad, plot gerbers, **JLCPCB** |
| `gen_carrier.py` | generator — edit this, never the .kicad_pcb | `python3 gen_carrier.py` |
| `check_carrier.py` | go/no-go. Verifies against the REAL board file | `python3 check_carrier.py` |
| `carrier-preview.png` | top view | look before you order |
| `carrier-footprint-check.pdf` | **1:1 paper check for the one assumed footprint** | print at 100%, read below |
| `flash_frame.stl` / `.step` | the printed frame, **58.0 x 69.0 x 22, 37.1 cm3** | **JLC3DP** |
| `gen_frame.py` | frame generator (needs cadquery) | `python3 gen_frame.py` |
| `verify_frame.py` | go/no-go for the print — point-in-solid tests against the built solid | `python3 verify_frame.py` |
| `thin_world.py` | minimum wall thickness in real millimetres (distance transform) | `python3 thin_world.py flash_frame.stl 2.0 0.35` |
| `frame-section.png` | plan + section through the pin row, drawn from the real STL | look before you order |
| `frame-mark.png` | slice through the +Y orientation mark | |
| `pinl-explained.png` | **why the seat bar is set from the BARREL, not the pin's total length** | read before soldering |
| `datasheets/P75-E2-SOURCE.md` | every pin dimension and where it came from | |
| `frame-3d.html` | **interactive 3D assembly** -- drag to rotate, explode slider | open in any browser |
| `pin_setter.stl` / `.step` | ~~assembly fixture~~ **SUPERSEDED by the seat bar in the frame — do not order** | — |
| `gen_pin_setter.py` | its generator | |
| `setter-preview.png` | three views | |

## Everything is now traced to a primary source

`check_carrier.py` reports **0 blockers**, including a full connectivity pass:
every net is one electrical island, no opens.

* pogo + dowel coordinates: parsed live out of `pcb-v7-zero-opens.kicad_pcb`
* **XIAO RP2040 land pattern: Seeed "XIAO Series Package and PCB Design", p.3**
  (SKU 102010428), local copy in `../../datasheets/`.  The callouts are vector
  outlines, not text -- they were read off a 7x render of the drawing.

```
XIAO_ROWS  = 17.00   mm centre-to-centre   (an earlier draft assumed 15.24 -- WRONG)
XIAO_PITCH = 2.54    mm, 7 per side
pads       = 3.0 x 2.0 mm SMD
body       = 17.8 x 21 mm
right row, USB end first: 5V GND 3V3 D10 D9 D8 D7
D8 = P2 = GP2 = SWCLK ; D10 = P3 = GP3 = SWDIO ; D7 = P1 = GP1 = nRESET
```

**It is an SMD land pattern, so the XIAO is soldered, not socketed.**  Each
land runs 7.0-10.0 mm off centre while the module edge sits at 8.9, so 1.1 mm
of every pad stays outside the module: every castellation can be inspected and
reworked with an iron from the side.

**Solderless press-fit / "hammer" headers do not work here.**  Those need a
FULL plated through-hole to grip -- the pin is a fraction oversize and the
barrel holds it on all sides.  The XIAO's side pads are castellated HALF-holes,
open to the board edge (confirmed on a 26x render of Seeed's own photo), so
there is nothing to grip against; and no hammer header is made for this form
factor anyway (they exist for the Pi GPIO 2x20 and the Pico 2x20).  This board
has SMD lands and no holes there at all.

### The module's belly is live copper

The XIAO also carries exposed pads on its UNDERSIDE: four round ones 5.85 mm
above centre (its own SWCLK / SWDIO / GND / RST) and two rectangles 8.6 mm
below centre -- **GND** and **VIN (5 V)**.  The module lies flat on this board,
so foreign copper under it is a short, and VIN makes that dangerous: 5 V must
never reach anything here.  `check_carrier.py` now forbids any track or via
inside x +-7.0 across the module footprint -- the strip between Seeed's two
land columns, which is exactly where those belly pads sit.

Still print `carrier-footprint-check.pdf` at 100% and lay a real module on it
before ordering.  It costs one sheet of paper.  And J2 remains the fallback.

## JLCPCB — ORDER FILES ARE BUILT

**`carrier-v1-gerbers.zip` -- upload this.**  Plotted with kicad-cli 9.0.9,
same flags as the v7 package: corner (drill/place file) origin,
`--subtract-soldermask`, `--no-protel-ext`, Excellon with PTH/NPTH separate.

| setting | value |
|---|---|
| size | **47 x 58 mm** |
| layers | **2** |
| thickness | **1.6 mm** (the default -- unlike pcb-v7, which is 1.2) |
| finish | HASL is fine; every pad here gets soldered |
| quantity | 5 (minimum) |

Fits JLCPCB's cheapest 2-layer tier (<= 100 x 100 mm).

### Assembly (optional)

| file | what |
|---|---|
| `carrier-v1-BOM.csv` | 2 lines, both part numbers CONFIRMED |
| `carrier-v1-CPL.csv` | 4 placements, corner-based, same space as the gerbers |

| ref | part | LCSC | type |
|---|---|---|---|
| U1 | Seeed XIAO RP2040 | **C9900176459** | Extended, SMT |
| R1-R3 | 0805 100R 1% | **C17408** | **Basic** |

**J1 and J2 are deliberately NOT in the BOM.**  Through-hole assembly costs
more than it saves for two and five easy joints; hand-solder them.  JLC protect
unused through-holes from solder ingress, so those holes arrive clean -- as do
all seven pogo/dowel holes.

### Verification chain

`verify_fab.py` reads the PLOTTED output back and checks it against
`pcb-v7-zero-opens.kicad_pcb` -- gerber -> drill file -> board coords -> the
original board.  It trusts nothing the carrier generator produced.

```
PTH  20 holes   O0.4 x4 (vias)  O1.0 x4 (J1,TP)  O1.02 x5 (J2)  O1.05 x7 (pogo,dowel)
NPTH  4 holes   O3.2 x4
7 pogo + dowel holes match the DUT file to < 0.002 mm
Edge.Cuts 47.000 x 58.000 mm, origin at the drill origin
VERIFY: 0 failures
```

### Before you pay

1. **Check U1 stock.**  C9900176459 is an Extended part.  The main board order
   has been paused since 2026-09-01 because U1 went to zero -- do not repeat it.
2. **Print `carrier-footprint-check.pdf` at 100%** and lay a real XIAO on it.
3. Thickness **1.6 mm**, not 1.2.  This board is not pcb-v7.

## JLC3DP — frame order

| setting | value |
|---|---|
| file | `flash_frame.stl` |
| volume | **32.8 cm3** |
| material | **FDM PLA is enough** — see below |

**(Superseded — see `ORDER.md`.)** Do not pay for MJF nylon on this part.  The housings needed MJF because
they carry fine features and go in the product.  This frame's smallest feature
is a O2.4 hole and it sits on your desk.  FDM PLA is a fraction of the price
for 50 cm3.  Choose MJF PA12 only if you want it to match the housings.

DFM notes, checked with `../scripts/wall_check.py`:

* thin-wall scan at 1.00 mm: **none found**.  (v1 of the engraved arrow left a
  0.30 mm rim at the outer edge and flagged 38 slices — same class of finding
  JLC raised on the housings.  Fixed: the arrow now leaves >= 1.2 mm both sides,
  and `gen_frame.py` asserts it.)
* the tool also prints `tier-junction contact at z=2.90 ... MIN band width
  ~0.00 mm`.  **Ignore it.**  z=2.90 is the default junction height carried over
  from the housing project; this frame has no step there.  The 1701.7 mm2 it
  reports is just the plain wall ring (90.4^2 - 80.4^2 = 1708 mm2).
* mesh is watertight, winding consistent.

## Seeing it before you print

`frame-3d.html` is a self-contained viewer: the real `flash_frame.stl` mesh is
embedded in the file, with the carrier, the five P75-E2 barrels, both dowels,
the XIAO and your board drawn to the same numbers the generators use.  The
explode slider pulls the stack apart so the 2 mm of pin standing proud, and the
~13 mm hanging below into the frame's opening, are both visible.

It needs its 3D library from a CDN, so open it in a normal browser rather than
inside a preview pane if it ever comes up blank.

## JLCPCB cannot place the contacts -- this is settled, not a maybe

Checked 2026-09-18 against JLCPCB's own parts library.  **Every SMD pogo pin
they stock is O2.0 mm** (Kinghelm and BAT Wireless, several lengths, all
D=2 mm).  J3 is on **2.00 mm pitch**, so five O2.0 barrels in a row touch.

That is the third time the same wall has stopped the same idea:

| ruled out | body dia | why |
|---|---|---|
| Lee's P125-B | O2.0 | barrels touch on 2.00 pitch |
| Mill-Max discrete range (0906/0908/0914/0901/0929/0930/0932) | O1.83 | 0.17 mm gap, before tolerance |
| every JLCPCB-stocked SMD pogo pin | O2.0 | barrels touch |
| **P75-E2** | **O1.02** | **fits, 0.98 mm gap -- and is not a placeable catalogue part** |

So JLC can place the XIAO, the three resistors and the connectors, but the five
pins and two dowels are hand-soldered whatever we do.  There is no alternative
part; the pitch forbids it.

## NO WIRES ANYWHERE ON THE BOARD

The old printed jig needed **five wires soldered to the pin tails**, routed out
through arches to the DAPLink and the supply -- five wire-to-pin joints, five
more at the probe end, and 30 AWG to strip and tin.  `JIG-SHOPPING.md` budgets
CA$19-24 of wire and heat-shrink for exactly that.

**None of it is needed now.**  The pin tube solders into a plated through-hole
and the board's copper carries the signal to the XIAO.  One joint per pin.

The only wire in the whole system is the **DP100 lead** -- two banana plugs to
one JST-XH -- made once, off the board.  Buy a ready-crimped JST-XH pigtail and
it is two joints.

So from `JIG-SHOPPING.md` you can drop: the five 30 AWG wire colours, the
heat-shrink, and the BOJACK/BNTECHGO kit.  Keep the solder.

## Fitting the pins: the frame has a SEAT BAR

The frame now carries a raised **bar** inside the cavity that the pin TAILS
land on.  Whichever stop a descending pin reaches first is the one that
governs, and a bar set for more protrusion is always reached before the head
touches the board -- so **the pin's head geometry no longer matters at all.**
The earlier Case A / Case B split is gone.

```
protrusion = SEAT_Z - (carrier top face - pin length)
           = 7.30   - (21.80            - 16.50)      = 2.00 mm
```

It is a **bar, not a floor** -- 8 mm wide in Y, spanning the cavity in X, with
**12.9 mm** of clear height above it and open space on both sides, so a
soldering iron still reaches the joints from underneath.  Every pin sits at
least 4.00 mm inside the bar's footprint.

### Not printed dowels

A printed dowel cannot be soldered, and at O1.0 x 19.0 mm it is a **19:1**
aspect ratio.  The v2 jig's printed posts were O1.05 x 2.6 mm -- **2.5:1** --
and they still snapped off.  This would be seven times worse, in the one part
that sets where the board sits.

Use **18 AWG solid copper wire**: O1.024 mm, solders because it is copper,
and a hardware or electronics shop has it.  Two pieces, 19.0 mm each.

### Solder the BOTTOM only -- one joint per pin

The hole is plated, so its barrel already connects the top pad to the bottom
pad.  **One fillet on the underside is the whole joint.**  Do not solder the
top as well:

* the top face is where your board comes down.  Solder there is a bump under
  the DUT, and the clearance it would eat into is only a few tenths of a mm
* the pin's head sits 2.0 mm above the hole, in the way of an iron
* the joint is only ~3.6 mm from the plunger end, and a pogo pin has a spring
  and grease inside -- **be quick, do not dwell**, and work from the far end,
  which is the underside

The oblong pads give **0.775 mm** of ring in Y, so there is plenty to wet from
below.

### Order of work -- one operation, one side

1. carrier into the frame's recess, **top face UP**
2. drop the five pins in from above, tail first -- each lands on the seat bar
   at exactly **2.0 mm** proud
3. drop the two dowels in -- **cut to 19.0 mm**, they seat on the SAME bar and
   stand **4.5 mm** proud
4. stand the frame on blocks, solder all seven from BELOW, reaching in over
   the bar.  12.9 mm of clearance

`gen_frame.py` prints the required dowel length every time it runs, derived
from the bar height, so the two can never drift apart.

### ONE number you must check before printing

`PIN_L = 16.5` at the top of `gen_frame.py` is the vendor figure.  **Measure a
pin you actually have** and, if it differs, change that one line and re-run.
The bar height follows automatically.  `PIN_PROUD = 2.0` is beside it if you
want a different protrusion.

Nothing about the PCB depends on either number.

### Heat-shrink on the tails: not needed

The tails hang ~13 mm in open air, 2.00 mm apart, with 5.3 mm of clearance
above the bench and the frame's walls all round them.  There is nothing for
them to touch.  Sleeve them if you like -- it does no harm -- but it buys
nothing electrically.

## What is soldered on the UNDERSIDE

Only one thing, if JLCPCB assembles the board: **the five pogo pin tubes.**

| Joint | Which face | Who |
|---|---|---|
| U1 XIAO, 14 castellations | TOP | JLC |
| R1-R3 | TOP | JLC |
| J1, J2 leads | **bottom** | JLC (wave), or you, flat on the bench |
| DW1, DW2 dowels | TOP (they sit flush underneath) | you |
| **PP1-PP5 pogo tubes** | **bottom** | **you, in the frame** |
| TP1, TP2 | neither -- bare pads | -- |

So the only work done *inside the frame, reaching underneath* is five joints.
Everything else is either JLC's or done flat on the bench beforehand.

### The pads were too small for that -- fixed

Checking this exposed a real problem.  The pogo pads were O1.60 round on a
2.00 mm pitch, which leaves an annular ring of only **0.275 mm** -- a very thin
target for the one set of joints made by hand, reaching up into a frame.

They are now **oblong, 1.60 x 2.60**, stretched perpendicular to the row.  The
pitch is in X, so lengthening in Y costs nothing: the row gap stays 0.400 mm
while the ring where the iron actually goes becomes **0.775 mm**.  Dowel pads
went O1.80 -> O2.40 (ring **0.675 mm**); they are isolated so they stay round.

`check_carrier.py` now fails any hand-soldered joint with less than 0.45 mm of
ring, so this cannot regress.

## What that leaves, and why it is easy now

Seven joints, all chunky through-holes, all reached from underneath through the
frame's 24 x 22 opening.  The one genuinely skill-dependent part was holding
each pin at a consistent height while soldering -- and `pin_setter.stl` removes
that entirely:

1. lay the carrier **face down** in the setter's 47.4 x 58.4 recess.  The XIAO,
   resistors and connectors hang free in the 5 mm reliefs; the board rests on
   two bare strips either side of the pin row.
2. drop the five P75-E2 in from above -- each falls until its plunger tip
   bottoms in the **2.0 mm** pocket
3. drop the two dowels in -- each bottoms in the **4.5 mm** pocket
4. solder

Every pin ends up 2.0 mm proud and every dowel 4.5 mm, set by print tolerance
instead of by eye.  Smallest feature on the setter is 3.0 mm.

Print it in **FDM PLA** with the frame; together they are ~50 cm3.

> The setter carries no text.  A cut label left thin slices in `wall_check.py`,
> an embossed one was worse (raised 5 mm letters are thin features in their own
> right), and a marker notch flagged too.  Shallow pocket = pins, deep pocket =
> dowels; that is unambiguous without a label.

## Bill of materials

| # | item | qty | status |
|---|---|---|---|
| 1 | carrier PCB | 1 (of 5) | this folder |
| 2 | printed frame | 1 | this folder |
| 3 | **P75-E2** pogo pin, 16.5 mm | 5 (+spares) | already in `../v7-release/flash-jig/JIG-SHOPPING.md` |
| 4 | **Seeed XIAO RP2040** | 1 | soldered to the SMD land pattern |
| 5 | 0805 100 R resistor | 3 | R1 SWDIO, R2 SWCLK, R3 nRESET |
| 6 | JST-XH 2-pin header + crimped lead | 1 | J1, power in |
| 7 | 4.0 mm banana plugs | 2 | DP100 end of that lead |
| 8 | 1x5 2.54 mm male header | 1 | J2, SWD escape |
| 10 | M3 x 8 self-tapping screw | 4 | into the printed bosses |
| 11 | **18 AWG solid copper wire**, cut to 19.0 mm | 2 | DW1/DW2 — see below |

## Why five pogo pins, not six

Your board's J3 is **five pads** — SWDIO, SWCLK, RESET, VSTOR, GND — confirmed
by parsing the board file.  The old printed jig drilled **six** bores: those
five plus one unwired "helper" spring pin at (-5.25, +0.55), whose only job was
to keep the board level while the eject plunger shoved it off the pins.  There
is no eject mechanism now and the two dowels locate the board, so it is gone.

(The other six-pad group on your board is **J4**, the keyboard pogo interface
at y -8.25 / -5.75 / -3.25.  The jig must never touch it.)

**All five are now wired.**  An earlier draft left RESET unconnected because
`HANDOFF-FIRMWARE.md` says the DAPLink flow parks it.  That is true for a
normal flash, but nRESET is the recovery path when firmware puts the nRF52840
somewhere SWD cannot reach it -- and this firmware is deep-sleep heavy by
design.  RESET now goes to XIAO D7 (GP1) through R3, exactly like the other
two, and to J2 pin 3 for an external probe.

## Still unresolved

Two of the three earlier items are now closed.

1. ~~**Dowel material.**~~  **RESOLVED -- 18 AWG solid copper wire**, O1.024 mm.
   0.013 mm slop in the carrier's O1.05 hole, +-0.088 mm in the DUT's O1.20,
   and it solders because it IS copper.  Any electronics shop.  Cut two at
   **19.0 mm**.  (O1.0 brass rod if you want something stiffer.)
2. ~~**P75-E2 head geometry.**~~  **NO LONGER MATTERS.**  The seat bar stops
   every pin by its tail, so whatever the head does is irrelevant.  The only
   pin number that still matters is the **overall length**, and you own the
   pins -- measure one and put it in `PIN_L` at the top of `gen_frame.py`.
3. **Whether 3.3 V is enough to flash.**  Still open.  If it is, R1/R2/R3 can
   be 0 R links and the level-shifting question disappears.  See
   `CARRIER-DESIGN.md` Section 8.  **Does not block anything** -- the resistors
   are fitted either way, only their value changes.

### Current error stack to the DUT's O1.20 pad

    hole position (fab)        +-0.050
    dowel in the DUT's O1.20   +-0.088     <- 18 AWG copper
    pin tilt in its hole       +-0.019
    ------------------------------------
    worst case                 +-0.157     budget +-0.600, 74% spare

## Assembly order

1. Solder R1-R3, J1, J2 and the XIAO — all on the TOP face, spread far apart,
   nothing crowded.  The XIAO's castellations are reachable from outside the
   module on all 14 lands.
2. Drop the carrier into the frame's recess, 4 x M3 into the bosses.
3. From **underneath**, through the big opening: push each P75-E2 down through
   its O1.05 hole until ~2 mm of pin stands above the top face, and solder the
   tube to the bottom pad.  Use a 1.5 mm shim laid across the top as a height
   gauge so all five end up identical.
4. Solder the two dowels into DW1/DW2, ~2.5 mm proud.
5. Plug in the XIAO, load `debugprobe` UF2 by drag-and-drop.

## The hard stop, solved

Earlier drafts had an open question: with one board, what stops you pressing
the DUT past the pin's 2.50 mm stroke?

**The pin barrels themselves.**  Set the tube ~0.5 mm proud and the plunger tip
~1.5-2 mm proud; the board bottoms out on the five barrel rims at ~1.0-1.5 mm
of compression.  The stop is metal, it is at the five contact points so the
board cannot tilt, and each rim touches only its own J3 pad — same net as the
pin inside it, so contact there is harmless.  No extra parts.

The exact tube height depends on unresolved item 2, and it is set by hand at
assembly step 3, so it is adjustable on the bench rather than baked into the
board.
