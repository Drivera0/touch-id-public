---
title: KiCadRoutingTools — settings for pcb-v3, and why it was freezing
type: guide
tags:
  - touchid
  - pcb
  - routing
updated: 2026-08-27
---

# Routing pcb-v3 with KiCadRoutingTools

Two parts: **why it froze** (fixed, but you need to know the rule), then a
tab-by-tab settings sheet.

---

## 1. Why it froze — and it was my fault, not the plugin's

The plugin's own parser says it outright:

> *"every zone consumer (obstacle map, plane connectivity) treats `pcb.zones`
> as copper"* — `py_router/kicad_parser.py:5163`

The board I handed you had **GND copper pours spanning the entire 19.30 mm
square on three of the four layers** (F.Cu, In2.Cu, B.Cu). To any net that
isn't GND — which is all 26 you're routing — that is one enormous block of
foreign copper covering the whole board. Every pad escape is blocked the
instant it leaves the pad.

So the router grinds through 200,000 iterations per net, fails, rips up,
retries. And because the plugin routes **in-process inside KiCad**, the GUI
cannot repaint while that happens. It isn't crashed. It's working, hopelessly,
with the window frozen and the progress bar unable to update.

**Fixed.** `build_pcb_v3.py` now has `EMIT_GND_POURS = False` and the board
ships with **12 zones instead of 15** — the twelve are all keep-out *rule
areas*, which the parser explicitly skips (`GetIsRuleArea()`), so your antenna
and screw keep-outs are still enforced.

> ### The rule to remember
> **Route first. Pour last.** This is the normal order on any PCB, and this
> tool makes it mandatory. Never autoroute a board that already has copper
> pours on it.

You must **re-open `pcb-v3.kicad_pcb`** — I rewrote it. If KiCad still has the
old one loaded, close without saving first.

### If it still appears frozen

It may genuinely be working. Before killing it:

- The window will be unresponsive for the whole run — that is normal, the
  router runs in KiCad's process.
- Check the **Log** tab afterwards; it records what happened.
- If you want live progress and the ability to stop, **run the CLI instead**
  (§4). That is the more debuggable path and I would use it by preference.

---

## 2. Settings that revert

**They do not persist across reopening the board.** They have reset on you at
least twice already. Re-check all four of these every single time:

| Setting | Must be | Why |
|---|---|---|
| **In2.Cu** in Layers | **unticked** | Carries the solid ground plane. If the router may use it, it cuts the plane to ribbons — and the continuous return path is the only reason this board is 4 layers |
| **Allow via-in-pad** | **unticked** | Vias in pads wick solder, and JLC charges to plug them |
| **GND** in the net list | **unticked** | Handled by the plane and stitching vias, not tracks. 40 connections of spaghetti otherwise |
| **Layer Costs** | `1.0 1.0 3.0 2.0` | See below |

---

## 3. Tab by tab

### Route tab — Net Selection

Click **Select** (ticks all 27), then untick **GND**. Should read
**"Ready - 26 nets selected to route"**.

Leave `Hide connected` ticked; `Hide differential` and `Separate by net class`
unticked. Component and both filter boxes empty.

### Route tab — Parameters

| Field | Set to | Note |
|---|---|---|
| Obey design rule constraints | **ticked** | Makes the greyed values fallbacks only — the real rules come from `pcb-v3.kicad_pro` |
| Track Width | **unticked** (greyed 0.3) | Leave it. The netclass gives 0.2 signal / 0.4 power |
| Min Clearance | **unticked** (greyed 0.25) | Leave unticked. Ticking it *clamps* your net classes down to the routed value |
| Via Size / Via Drill | unticked (0.6 / 0.3) | Matches the netclass and JLC standard |
| Min Hole Clearance | unticked (0.5) | JLC minimum |
| Fab Tier | **standard** | |
| Min Edge Clearance | unticked (0.3) | Matches the project file |
| **Grid Step** | **0.05** | Was 0.1. Our pads sit on a 0.05 grid and the BQ25505's pins are **0.24 mm wide** — on a 0.1 grid you throw away resolution exactly where the board is tightest. The board is 19 mm; it costs nothing |
| Via Cost | 75 | Default, fine |
| **Max Rip-up** | **3**, then 8 if needed | Raise it *only* if the first run leaves nets unrouted |
| Rip-up Abandon Metric | stranded | Default |
| Rip-up Blocker Select | count | Default |

### Route tab — Layers

**F.Cu ✓ · In1.Cu ✓ · In2.Cu ✗ · B.Cu ✓**

Don't press *Check Stackup (AI)* — it writes back into these controls and can
re-tick In2.Cu.

### Route tab — Options

| Option | Set to | Note |
|---|---|---|
| Allow via-in-pad | **unticked** | |
| Same-net Pad Clearance | 0.25 | Default |
| Stub layer swaps | ticked | Helps routability |
| Move copper text to silkscreen | ticked | Harmless here — all reference text is hidden |
| Add teardrops | unticked | JLC doesn't need them; complicates the file |
| Fix DRC settings after routing | **UNTICKED** | **Correction (2026-08-27).** I previously said this was safe. It is not: it *loosened three Board Setup values to the routed floors*, i.e. it rewrites your design rules to match whatever the router did. Never leave it on. |
| Follow User-layer guide path | unticked | |
| Keep out of User-layer polygon(s) | **unticked** | Our keep-outs are native KiCad rule areas, which the router reads directly. This option is for polygons drawn on a User layer |
| **Power Nets** | `VSTOR VBAT VIN_DC LX SENSOR_3V3 SENSOR_MCU_3V3` | |
| **Power Widths** | `0.4 0.4 0.4 0.4 0.4 0.4` | Must be the same length as the net list |
| Power route neck-down | **ticked** | Full width in open board, necked down entering the BQ25505's 0.24 mm pads. Only works if Power Nets is filled |
| Coplanar Nets / No BGA Zones / Rip Pre-Existing | empty | |
| Force re-route selected nets | unticked | Nothing is routed yet |
| **Keep all input copper** | **ticked** | Makes input copper read-only for the cleanup passes. Protects the twelve keep-out zones |
| Smooth routes | ticked | |
| **Layer Costs** | **`1.0 1.0 3.0 2.0`** | Was `1.0 3.0 3.0 3.0`, which is the *2-layer* default. Docs: 4+ layer boards default to all 1.0. In1.Cu is the empty inner layer we left free for signals — charging it 3× defeats the point. B.Cu at 2.0 keeps a mild preference away from the back, which carries the ten pogo pads and the test points |

### Advanced options tab — leave it alone

Every default is sensible for this board. Specifically **do not** enable Bus
Routing, Length Matching or Time matching: this board has no buses, no
differential pairs and nothing high-speed. Its fastest signal is a 57600-baud
UART to the sensor.

Impedance stays unticked — no controlled-impedance nets here.

The only one worth touching if you get failures is **Max Iterations**
(200000). Raise it before raising Max Rip-up.

### Differential tab — skip entirely

There are no differential pairs. USB is disabled on the MDBT50Q (D+/D− are
NC), so there is nothing for this tab to do.

### Fanout tab — skip

BGA/QFN fanout is for parts with inner pad rows you cannot escape on one
layer. Our densest part is the BQ25505 at 0.5 mm pitch with a single perimeter
ring and one thermal pad — the router escapes that directly. The MDBT50Q's
staggered rings are 0.8 mm pitch, also fine.

### Planes tab — **this is step 2, after routing**

This is where the ground plane comes back. Once signals are routed:

1. Select **GND** only in the net list
2. Target Layers: **In2.Cu** (add F.Cu and B.Cu if you also want top/bottom pour)
3. **Thermal via arrays under exposed pads** — leave **ticked**. This is what
   stitches the BQ25505's thermal pad and the two TPS7A2033 thermal pads down
   to the plane. TI requires it
4. Thermal relief pad connections — unticked (solid connections; better
   thermally, and nothing here is hand-soldered on GND)
5. **Add GND vias near signal vias** — leave unticked. It's for high-speed
   return paths, and we have none
6. **Create Planes**

### AI tab — not for this board

It needs Claude Code installed (it found yours at `C:\Users\drive\.local\bin`),
and it does not route — it fills in the parameter fields. Everything it would
infer is already derived from primary sources: the netclass comes from the real
netlist, the stackup was chosen deliberately, and there are no diff pairs or
high-speed nets to analyse.

The hazard is that its buttons write back into the GUI controls — including
possibly re-ticking In2.Cu or via-in-pad, the two things we deliberately set
against the defaults.

*Review Routed Board* afterwards is reasonable as a second look. Treat anything
it flags as a prompt to check harder, not as confirmation — the three checkers
are the real gate.

---

## 4. The CLI, which I'd use instead

The GUI freezing is a symptom of routing in-process. The CLI shows live
progress, can be stopped, and writes to a **new file** so the input is never at
risk:

```
cd <KiCadRoutingTools>
python py_router/route.py ^
  "C:\Users\drive\Documents\Obsidian Vaults\Foundation\touchid\cad\pcb-v3\pcb-v3.kicad_pcb" ^
  "...\pcb-v3-routed.kicad_pcb" ^
  --nets "*" "!GND" ^
  --layers F.Cu In1.Cu B.Cu ^
  --layer-costs 1.0 1.0 3.0 2.0 ^
  --grid-step 0.05 ^
  --power-nets VSTOR VBAT VIN_DC LX SENSOR_3V3 SENSOR_MCU_3V3 ^
  --power-nets-widths 0.4 0.4 0.4 0.4 0.4 0.4
```

Then the plane step:

```
python py_router/route_planes.py "...\pcb-v3-routed.kicad_pcb" --overwrite ^
  --nets GND --plane-layers In2.Cu
```

---

## 5. After routing — verify before believing it

Run all four, in this order. `sexp_check` first, always — if the file doesn't
parse, nothing else you read from it means anything.

```
cd cad\pcb-v3
python sexp_check.py    pcb-v3-routed.kicad_pcb    # structure
python check_board.py   pcb-v3-routed.kicad_pcb    # clearance
python check_connect.py pcb-v3-routed.kicad_pcb    # islands per net
python <KRT>\py_router\check_drc.py pcb-v3-routed.kicad_pcb
```

What to expect:

- `sexp_check` — PARSE OK, **0 bare LF**
- `check_board` — **0** pairs under 0.127
- `check_connect` — **0 nets split**. This is the one that proves it actually
  routed. Right now it says 27 split, which is just the unrouted state
- `check_drc` — NO DRC VIOLATIONS

---

## 6. Two things I'd still hand-route afterwards

**LX and VIN_DC.** That's the BQ25505's boost switching loop —
U2 pin 20 → L1 → U2 pin 2. It wants to be physically small and tight, and no
autorouter knows that. It's about four segments in KiCad's interactive router.
If the autorouter takes a scenic path there it costs real efficiency on a
design whose entire budget is 4 mWh/day.

**Check the thermal vias landed.** After Create Planes, confirm the BQ25505's
pad 21 and both TPS7A2033 pad 5s actually got via arrays down to In2.Cu. TI
requires the thermal pad soldered and stitched for the part to work at all.
