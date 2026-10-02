# The journey: how the board got built

> **Still a work in progress.** Everything below is design work. The board
> hasn't been manufactured or tested yet, and the firmware hasn't run on real
> hardware. See [Project status](README.md#project-status).
>
> The design files, board renders and keyboard-slot measurements stay
> private. Every commit is here with its message, but without the private
> files, and messages that would give away the slot contacts are reworded. The module is public as an
> [interactive 3D model](https://drivera0.github.io/whorl-touch-public/).

How the design got built, milestone by milestone. Each milestone is a
[git tag](https://github.com/Drivera0/whorl-touch-public/tags); click a commit
to read its message.

![Whorl Touch taken apart, from the interactive 3D model](images/whorl-touch-apart.png)


---

## 1. Salvage the first board (Aug 20): `m01` → `m02`

The first design was an ESP32-C3 board drawn in Altium. Before changing
anything, it got imported into KiCad and checked against the original.

- [Import the Altium board into KiCad, verified exact](https://github.com/Drivera0/whorl-touch-public/commit/c0a0e6f)
- [Nine orphan `)` made the board file unparseable](https://github.com/Drivera0/whorl-touch-public/commit/6b71473), so a syntax gate was added and has run on every edit since
- [Every land pattern traced back to its vendor drawing](https://github.com/Drivera0/whorl-touch-public/commit/d55f322), which found errors on U1, U2 and C3/C4

**Lesson:** a footprint you haven't traced to a datasheet is a guess.

## 2. The master spec and the v3 rebuild (Aug 26 – 27): `m03` → `m05`

The ESP32 was too wide for the slot. The rebuild moved to a BLE-only nRF52840
module on a 4-layer board, and one design spec became the single source of
truth (it stays private).

- The design spec becomes the master file
- [pcb-v3 built: 4 layers, 177 pads, all three checkers pass](https://github.com/Drivera0/whorl-touch-public/commit/d357334)
- [Two checker bugs, including KiCad's Y-down rotation sign (79 phantom shorts)](https://github.com/Drivera0/whorl-touch-public/commit/fc8540c)
- [U2's land was 0.25 mm off its own centreline](https://github.com/Drivera0/whorl-touch-public/commit/b953dad)
- [The "open connections" metric was lying](https://github.com/Drivera0/whorl-touch-public/commit/37f3c16). A net with zero copper never showed as disconnected, so deleting a net scored as a win.
- [Zero open connections, 15/15 preflight checks](https://github.com/Drivera0/whorl-touch-public/commit/84c035e)


**Lesson:** when a check fails, suspect the checker first. It was wrong more
often than the board.

## 3. "The board had no ground" (Aug 28): `m06` → `m07`

- [THE BOARD HAD NO GROUND](https://github.com/Drivera0/whorl-touch-public/commit/1692c54). Every check passed, and none of them looked for it. The ground pour went in, and a gate was added so it can't happen again.
- [KiCad 10 changed the file format and every parser went blind](https://github.com/Drivera0/whorl-touch-public/commit/eca1690)
- Altium's DRC found a real defect the KiCad checks couldn't see. The board was then re-imported clean.
- [The pick-and-place file was in the wrong coordinate space](https://github.com/Drivera0/whorl-touch-public/commit/34131c6)
- A housing corner wall was 0.15 mm, not 0.8

**Lesson:** cross-check with a second, independent tool.

## 4. Choosing the cell (Aug 28): `m08`

The module needs stored energy, and nothing that fits the cavity is simple.

- [The CP1254 "IP Wires" is not protected and doesn't fit](https://github.com/Drivera0/whorl-touch-public/commit/47fa22a)
- [The charge limit is 4.30 V, not 4.00 (a misread footnote)](https://github.com/Drivera0/whorl-touch-public/commit/97d280d)
- [Cell decided: LiPol LPM1254 with a factory PCM and wires](https://github.com/Drivera0/whorl-touch-public/commit/689705c)
- [Sensor: the ZW0905 was discontinued; the HLK-ZW0922 is a drop-in](https://github.com/Drivera0/whorl-touch-public/commit/5e64939)

## 5. The long routing fight (Aug 29 – 30): `m09` → `m10`

Adding a protection IC to a 20 × 19 mm board started two days of placement,
routing and ground-pour work.

- [My "it doesn't fit" result was a fourth scanner bug](https://github.com/Drivera0/whorl-touch-public/commit/935eb35)
- Slot depth was never a constraint: the module stands proud by design
- Reverted three hand-placed ground taps, all of them faulty
- [pour_truth.py judges connectivity against the fill KiCad actually computed](https://github.com/Drivera0/whorl-touch-public/commit/8d3021e), not a model of it
- [Both press-fit pins had been drilled through copper](https://github.com/Drivera0/whorl-touch-public/commit/9170b3f)
- [Custom pads: `(size)` is the anchor, not the copper, so every parser read 3× low](https://github.com/Drivera0/whorl-touch-public/commit/6880130)
- [Rejected a smaller module (BC840M), because it needs a larger board](https://github.com/Drivera0/whorl-touch-public/commit/a3a3f36)
- v5: DRC clean, then [v6: zero open pads, zero blockers](https://github.com/Drivera0/whorl-touch-public/commit/0410f94)


**Lesson:** a smaller part isn't always a smaller board. Ceramic-antenna
modules need less keep-out than trace-antenna ones.

## 6. v7 and release (Aug 31 – Sep 1): `m11` → `m13`

- [The protected cell was confirmed, so the on-board PCM was deleted](https://github.com/Drivera0/whorl-touch-public/commit/946cf8b). That removed four parts and healed the last stranded pad.
- `m11`: preflight at 0 blockers, 0 open pads, ground fully connected. The v7 board files are private.
- [Pogo-pin flashing jig](https://github.com/Drivera0/whorl-touch-public/commit/e7efebc)
- [Housing v6.5 after JLC's DFM review](https://github.com/Drivera0/whorl-touch-public/commit/0dcda58)

## 7. Firmware and the product direction (Aug 31 – Sep 1)

The firmware history is merged in: Zephyr on the nRF52840, the sensor driver,
the auth crypto and the helper apps. The design docs and the source
code stay private.

- [Gut the ESP32 fork and start the nRF52840 Zephyr firmware for pcb-v7](https://github.com/Drivera0/whorl-touch-public/commit/d6a3725)
- [LESC-only pairing, HMAC challenge-response and a hash ratchet](https://github.com/Drivera0/whorl-touch-public/commit/f7243ab)
- [Mac keycard proven: `sudo` authenticates by smart card, gated on a touch](https://github.com/Drivera0/whorl-touch-public/commit/2de955a)
- [A smart card you can't remove is a lockout, so that got fixed](https://github.com/Drivera0/whorl-touch-public/commit/2353bb1)
- [Knob-to-dongle transport: proprietary 2.4 GHz (ESB), not BLE](https://github.com/Drivera0/whorl-touch-public/commit/f0d7535)
- [Product pivot: FIDO2 is the core of the product](https://github.com/Drivera0/whorl-touch-public/commit/5d12048)

