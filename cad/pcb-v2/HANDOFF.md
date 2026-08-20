---
title: TouchID PCB — handoff
type: project
tags:
  - touchid
  - hardware
  - jlcpcb
updated: 2026-08-20
---

# TouchID PCB v2 — handoff

Scope of this document: **`cad/pcb-v2/` only**. Everything needed to continue is
in this folder.

## Situation in one paragraph

JLCPCB order [order #] / Y6 was paid for and built with a **wrong U2 land
pattern**. That board is `cad/pcb-initial-failure/` and is scrap. `pcb-v2` is
the corrected design. U2 is fixed, both ESP32 strapping pins are now tied high,
and the board passes clearance and connectivity checks. It has **not** yet been
DRC'd in KiCad, plotted to Gerbers, or verified as plotted output.

---

## Authoritative files in `cad/pcb-v2/`

| File | Role |
|---|---|
| `pcb-v2.kicad_pcb` | **The design.** Single source of truth. CRLF line endings. |
| `pcb-v2.kicad_pro` / `.kicad_prl` | KiCad project files |
| `pcb-v2.PcbDoc` / `.PrjPcb` | **STALE.** Pre-fix Altium doc. Do not trust. |
| `production-file-old-version.zip` | JLCPCB CAM output for the ordered (bad) board. Ground truth for "what was actually manufactured". |
| `sexp_check.py` | **Run first, always.** Real S-expression parse. |
| `check_board.py` | Copper clearance, honours pad shape |
| `check_connect.py` | Per-net island count |
| `route_one.py` | Grid router for a single connection |
| `COORDINATE-MAP.txt` | Gerber ↔ KiCad transform, verified 80/80 pads |

### Coordinate transform (verified, do not re-derive)

```
kicad_x = gerber_x + 48.5011
kicad_y = 113.8036 - gerber_y      <-- Y IS MIRRORED
```

Altium and KiCad use opposite Y conventions; the importer mirrors Y. Any
coordinate taken from a Gerber or from Altium must go through this.

---

## Verification workflow

Run in this order. **`sexp_check.py` must pass before any other result means
anything.**

```
python sexp_check.py    pcb-v2.kicad_pcb     # structure
python check_board.py   pcb-v2.kicad_pcb     # clearance
python check_connect.py pcb-v2.kicad_pcb     # connectivity
```

Current expected output: parses to one `kicad_pcb` form, 96 pads, 187 segments,
18 vias, 18 zones, 0 bare LF; 4 sub-0.127 pairs (all explained below); all 9
nets single-island.

---

## Done and verified

- **U2 land pattern fixed.** Was 0.30 × 0.30 pads at (±0.52, ±0.52) with an
  unrotated 0.55 thermal. Now 0.36 × 0.30 at (±0.421, ±0.3249) with a 0.48
  diamond at 45°, per LCSC C46459900 / TI DQN0004A 4215302/E. Terminal coverage
  went 15–25% → **100%**; mask dam 0 → **0.1749 mm**.
- **U2 escape re-routed** at 0.15 mm after the pad move created a short.
- **U1 pin 5 (GPIO2) → +3V3** via a 0.668 mm stub.
- **U1 pin 22 (GPIO8) → +3V3** via 4 segments + 3 vias (see "pin 22" below).
- **9 orphan `)` repaired.** The file was unparseable; KiCad would have refused
  to open it. Caused by block deletion leaving trailing parens.

### Why pin 5 and pin 22 mattered

GPIO2, GPIO8 and GPIO9 are **strapping pins**. For a few ms after reset the chip
samples their voltage to choose a boot mode, then they become normal I/O.
Espressif Table 4-1 gives GPIO2 and GPIO8 a default of **Floating** — no
internal pull. A floating CMOS input drifts to whatever coupling or humidity
pushes it to, so boot mode becomes a coin flip: works on the bench, fails
intermittently in the field. Table 4-3 requires GPIO8 = 1 for joint download
boot, the mode used to flash firmware over USB. Both are now tied high.

---

## Open issues, ranked

> **2026-08-20 update.** Issues 1, 2 and the C1–C4 half of issue 5 are now
> closed. Every footprint has been traced to the vendor drawing behind its
> JLCPCB part number; see `JLCPCB DFM Report.md`, which has been rewritten. What
> changed in `pcb-v2.kicad_pcb`:
>
> - **U1 pad 49** rebuilt as one custom pad at (−1.97501, 0.725) carrying
>   Espressif's chamfer polygon on F.Cu + F.Mask + F.Paste; the detached
>   copper-only island deleted. The polygon's global bbox and cut corner now
>   match the Y6 `G36` region exactly.
> - **U2** rebuilt to TI 4215302/E *copper*: 0.46 × 0.31 chamfered pads at
>   (±0.43, ±0.325), mask 0.36 × 0.21, thermal 0.58 diamond / 0.48 mask /
>   0.45 paste. The previous fix had used TI's mask-opening numbers as copper
>   and then shrank the mask again, leaving 31 % less wetted copper than TI
>   specifies.
> - **C3/C4** re-spaced to Samsung's 2012 ±0.20 land table: 1.40 × 0.96 pads,
>   1.84 mm centres (gap 0.88, span 2.80). The GND return run between them moved
>   0.15 mm outboard and the VBAT jog beside U2 moved 0.06 mm, both to clear the
>   larger pads.
> - **C1/C2 were already fully in spec** against Samsung's 1005 table and were
>   not touched.
>
> Post-edit state: `sexp_check` parses clean (95 pads, 187 segments, 18 vias,
> 18 zones, 0 bare LF), all 9 nets single-island, and `check_board` now reports
> **one** sub-0.127 pair instead of four — only the pre-existing +3V3/VBAT pair
> at exactly 0.1270. The three U2 pairs at 0.0697 mm are gone; the chamfers are
> what clears the diamond.
>
> Issue 3 (DRC, plot, independent Gerber verification, BOM/CPL rebuild) is still
> open and still blocks ordering. Issue 6 (sensor not sourced) is unchanged. One
> new item: the file uses `(net "NAME")` in pads with no net declaration block,
> which is not KiCad's schema — confirm KiCad actually opens and plots it before
> assuming the export will work.

### 1. ~~U1's chamfered thermal pad is misplaced by exactly 1.45 mm~~ — CLOSED 2026-08-20

Found 2026-08-20 by diffing the current board against
`production-file-old-version.zip`.

U1's 3×3 thermal grid sits at kicad x ∈ {146.5261, 148.5011, 150.4761},
y ∈ {100.3286, 102.3036, 104.2786}.

**Ordered board (ground truth, from the Gerber):** eight 1.45 × 1.45 squares
plus, at the 9th slot (150.4761, 104.2786), a 1.45 × 1.45 square with one corner
chamfered — drawn as the file's single `G36` region.

**Current KiCad board:** eight 1.45 squares, a **0.8 × 0.8** rect at the 9th
slot, and the chamfered polygon sitting at bbox centre **(149.0261, 102.8286)** —
off by exactly **(1.45, 1.45)**, overlapping the centre pads.

So the KiCad importer mishandled the custom pad. Total thermal copper is
18.7069 mm² vs the ordered 18.7425 mm², which is close enough to look fine and
is **misleading** — the copper is redistributed, not equivalent.

All thermal pads are GND, so there is no short and no electrical fault. But if
Gerbers are plotted from this file as-is, U1's thermal pattern will not match
the ordered artwork.

> Caveat before acting: this rests on my reading of KiCad custom-pad primitive
> semantics (primitives relative to the pad anchor, anchor relative to the
> footprint origin with footprint rotation applied). The exact 1.45 offset and
> the Gerber both support it, but confirm by opening the board in KiCad and
> looking at U1's thermal grid before editing anything.

### 2. ~~`JLCPCB DFM Report.md` is substantially wrong~~ — CLOSED 2026-08-20, rewritten

It claims U1's footprint is defective. **It is not.** Parsing the ordered
Gerber's apertures proves U1 is correct: 26 × `R,0.4×0.8` + 22 × `R,0.8×0.4` =
48 perimeter pads on 0.8 mm pitch, 9 thermal, 4 × 0.7 corner pads = 61 pads,
already rotated 180° with the antenna away from the pogo pads. That section was
written from a stale generator script, not from the artwork. **U2 was the only
real defect.** Rewrite before sending anything to JLCPCB.

### 3. Not yet run — blocks ordering

- KiCad **DRC** (`kicad-cli pcb drc --output drc.json`)
- **Gerber plot** (`kicad-cli pcb export gerbers`)
- **Independent verification of the plotted Gerbers**, parsing apertures the
  same way the ordered ones were parsed. This is the check whose absence caused
  the original failure. Do not skip it.
- **Rebuild BOM/CPL.** Trap: U1's CPL origin is the **pad-ring centre, not the
  body centre**, and they differ by **2.70 mm**. Getting this backwards
  misplaces the module by more than three pad pitches.

### 4. Stale scripts in `cad/kicad/`

`verify_board.py` and `build_board.py` both target `pcb-v2-corrected.kicad_pcb`,
which does not exist. Worse, `verify_board.py` expects pads named `U1-3`, but
the imported board names them `3` inside footprints `U1` and `Un0`. So the
**coverage check — the most valuable script in the project — is not currently
running against the real board.** Repointing it is worth doing before the next
order.

### 5. Accepted as-is

- ~~**C1–C4 still use the old, smaller land patterns.** The 0805 land is
  ~0.51 mm short in the toe direction~~ — **wrong, and now fixed.** The span was
  inside Samsung's range all along; the real deviations were the gap (+0.17) and
  the pad width (−0.10). C1/C2 were already fully in spec. C3/C4 corrected
  2026-08-20.
- **One +3V3/VBAT track pair at exactly 0.1270 mm**, JLCPCB's stated minimum.
  Zero margin, but passed on the ordered board too. Still open.
- ~~**Three U2 pairs at 0.0697 mm**~~ — gone. They were an artefact of the
  intermediate U2 fix, not inherent to X2SON-4. TI's chamfered pads clear the
  diamond thermal with 0.22 mm to spare.
- **J2's six Ø1.2 mm pads carry F.Paste.** They are hand-soldered wire pads for
  the sensor pigtail, so the stencil will print six solder domes on 1.5 mm
  pitch. Decide before plotting.

### 6. Long-standing

A **≤16 mm round fingerprint sensor** is still not sourced. It could still change
the board.

---

## The Altium question — unresolved, read before starting

The request was: fix the remaining issues in Altium, and replace the stale
`pcb-v2.PcbDoc` by exporting the KiCad board back to Altium.

**KiCad cannot export `.PcbDoc`.** There is no such exporter. KiCad writes
Gerbers, ODB++, IPC-2581, Specctra DSN and STEP. So the round trip is not a
single step. Options:

1. **Altium's Import Wizard.** The Gerber header shows the user is on **Altium
   Designer 26.9.1**, which is recent enough to have KiCad import. Most direct
   path — verify it round-trips nets and footprints, not just copper.
2. **ODB++ or IPC-2581 from KiCad → Altium.** Carries netlist; more reliable
   than Gerber, less direct than option 1.
3. **Stay in KiCad.** Everything above was fixed by editing the `.kicad_pcb`
   text directly with scripted checks, which has worked well.

**Relevant history:** driving the Altium GUI by computer use was previously
attempted and abandoned. Modal dialogs did not appear in screenshots, panels
dropped into eyedropper picker modes, and Altium repeatedly restarted and lost
the project. A DelphiScript approach (`FixPads.pas`) ran but produced no visible
change and its result dialog could not be read. That is why the project moved to
KiCad text editing. Going back to Altium risks re-introducing those problems —
worth a deliberate decision rather than drifting into it.

---

## Traps this project has already hit

Each of these produced a confident wrong answer at least once.

1. **Regex checkers are blind to structure.** `check_board.py` and
   `check_connect.py` reported a clean, fully-connected board while the file had
   9 orphan parens and would not open. Their numbers were all correct. The file
   was still broken. Hence `sexp_check.py`.
2. **Pad shape matters.** Modelling circular pads as rectangles inflates them by
   up to 0.207 × d (0.46 mm on a 2.2 mm pogo pad) and produced 8 false
   violations. Altium's DRC was right; the checker was wrong.
3. **Never trust a generator script as evidence of what shipped.** Reading
   `build_board.py` instead of the artwork produced a false accusation that U1
   was defective, which nearly went to JLCPCB.
4. **Total-area comparisons hide redistribution.** The thermal copper totals
   matched to 0.2% while one pad was in the wrong place.
5. **Gerber parsing specifics:** Altium writes pads as `D03` flashes with
   **modal coordinates** — `D03*` often sits alone on its line and takes its
   position from the preceding move. Format is `%FSLAX44Y44%`, so divide by 1e4.
   Rounded-rect pads carry their real size in `%AMROUNDEDRECT...` macro bodies,
   not the `%ADD` line.
6. **Writing the file in Python text mode converts CRLF → LF**, making git report
   all ~6,100 lines changed. Write bytes.
7. **Deleting segment blocks silently deletes vias** if you rebuild the file
   between the first and last segment — vias are interleaved with segments.
   Always print the via count before and after.
8. **A pad's own copper blocks its escape.** When routing, exclude the source pad
   from its own obstacle map. Also, 0.4 mm gaps between 0.8 mm pitch pads cannot
   take a trace, so the only escape is along the pad's long axis.

---

## Git

Repo is local and private, at the project root. Recent history:

```
232d83c Repair 9 orphan ')' that made the board file unparseable; add a syntax gate
3bae0b6 Route U1-22 (GPIO8) to +3V3; both strapping pins now tied high
a64a17c Re-route U2's escape for the new pad positions; short resolved
cccd5f2 WIP: U2 pads moved, local routing NOT yet corrected - board has a short
856468f Fix U2 land pattern (TPS7A2033DQNR, LCSC C46459900, X2SON-4)
0b82417 Import the Altium board into KiCad, verified exact
3df7968 Baseline: TouchID module as it stands before the U2 land pattern fix
```

Tag `as-ordered-Y6` marks the artwork that was actually manufactured.

---

## Suggested next step

Resolve **issue 1** (the misplaced chamfered thermal) by opening `pcb-v2.kicad_pcb`
in KiCad and looking at U1's thermal grid, since that determines whether the
board is ready to plot. Then **issue 2** (rewrite the DFM report), because that
is the document that would actually be sent to JLCPCB and it currently
misdescribes the fault.
