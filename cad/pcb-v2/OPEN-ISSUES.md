---
title: Open issues — everything still outstanding
type: project
tags:
  - touchid
  - hardware
updated: 2026-08-20
---

# Open issues

Single list of everything not yet closed, newest findings first.

## The Altium import — attempted 2026-08-20, blocked on layer mapping

**The import itself works.** File → Import Wizard → KiCad Design Files, add
`pcb-v2.kicad_pro` (it pulls the `.kicad_pcb` in automatically). Analysis
result: **0 errors**, 572 warnings, and every warning is the same benign class —
`Unknown child uuid / tenting / covering / plugging / capping / filling of
setup`, i.e. KiCad 10 keywords Altium's importer doesn't recognise. Metadata,
not geometry or netlist.

> Worth noting: 0 errors was impossible before the net-schema fix. The file
> genuinely could not be parsed by anything until then.

**Where it stops: the "Current Board Layer Mapping" page.** Altium reads *every*
KiCad layer as `Conductive Layer` and assigns them sequential internal copper
layers:

| KiCad layer | Altium proposes | Should be |
|---|---|---|
| F.Cu | Top Layer | correct |
| B.Cu | **Mid Layer2** | Bottom Layer |
| F.Mask | **Mid Layer1** | Top Solder |
| B.Mask | **Mid Layer3** | Bottom Solder |
| F.SilkS / B.SilkS | **Mid Layer5 / 7** | Top / Bottom Overlay |
| F.Paste / B.Paste | **Mid Layer13 / 15** | Top / Bottom Paste |
| Edge.Cuts | **Mid Layer25** | Mechanical 1 / board outline |

Accepting the defaults produces a ~25-layer board with the solder mask,
silkscreen, paste and board outline all sitting on inner copper. Every cell is
an editable dropdown, so it is fixable — but the list scrolls one row at a time
and "Bottom Layer" sits past Mid Layer30, for each of ~25 layers. **I stopped
rather than grind through it**, because a silent mis-selection there produces
exactly the kind of confidently-wrong board this project has already paid for
twice. The wizard was cancelled cleanly; nothing half-imported was left behind.

Three ways forward, best first:

1. **Do the mapping by hand.** Trivial with a mouse — drag the dropdown
   scrollbar or type to jump. ~25 dropdowns, ten minutes. The wizard path is
   six clicks to get back to that page.
2. **Export ODB++ or IPC-2581 from KiCad instead.** Those formats tag each
   layer's *function* explicitly, so Altium needs no manual mapping. KiCad 10
   is installed on this machine.
3. **Stay in KiCad.** DRC and Gerber plot are the actual blocking items and
   KiCad does both natively, now that the file opens.

## Board / electrical

- **4 pads unrouted — C3-1, C3-2, C4-1, C4-2.** Deliberate: their tracks were
  ripped when the caps moved to clear the new corner hole. This is the
  autorouter's job.
- **+3V3 / VBAT pair at exactly 0.1270 mm**, JLCPCB's stated minimum. Zero
  margin. Passed on the scrapped board too, but there's no reason to keep it.
- **J2 is still six hand-solder pads split across both strips** (16.40 mm
  overall) and **still carries `F.Paste`** — the stencil will print solder domes
  on pads meant for hand-soldered wires. Decide deliberately; `B.Paste` has
  already been removed from the pogo pads and test points.
- **KiCad DRC has never been run. Gerbers have never been plotted. Plotted
  Gerbers have never been independently verified.** This is the check whose
  absence caused the scrapped order. It is now unblocked.
- **BOM / CPL need rebuilding.** Trap: U1's CPL origin is the **body centre**,
  not the pad-ring centre — they differ by 2.70 mm.
- **Pogo pad positions have not been re-verified** against the keyboard since
  the outline changed to 19.30 square. They are set by the keyboard, so they
  should not have moved in absolute terms — but that needs confirming, not
  assuming.

## Mechanical

- **ZW0905 flange margin is 0.185 mm per side** on the 18.37 mm top face.
  Essentially zero; the sensor covers almost the whole top.
- **ZW0905's 4.50 mm back connector must be removed** and the six pads
  hand-wired — it would otherwise foul U1. ZW0919 has it on a side tab instead.
- **Rear retention shelf has not been re-checked** against the new 0.80 mm wall.
- **0.80 mm wall is thin for FDM.** Fine for injection moulding.
- **The sensor has not been bought.** ZW0905 is no longer listed in Hi-Link's
  own store — orderable via sales@hlktech.com / Alibaba / Rajguru, but not
  one-click. Confirm the module outline against the §2.3 drawing on arrival,
  never the spec table.

## Tooling

- **Stale scripts in `cad/kicad/`** — `verify_board.py` and `build_board.py`
  both target `pcb-v2-corrected.kicad_pcb`, which does not exist.

## Related

- [[touchid/cad/pcb-v2/PCB-IMPROVEMENTS|PCB improvements]]
- [[touchid/docs/design/Module Mechanical v3|Module mechanical v4]]
- [[touchid/docs/build/JLCPCB DFM Report|JLCPCB DFM Report]]
