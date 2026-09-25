# The journey: how the board got built

> **Still a work in progress.** Everything below is design work. The board
> hasn't been manufactured or tested yet, and the firmware hasn't run on real
> hardware. See [Project status](README.md#project-status).

A guided tour of this repo's history. Each milestone is a **git tag**. Click a
commit to see its diff, or use a compare link to see everything that changed
between two milestones.

![Board progression](docs/renders/board-progression.png)


---

## 1. Salvage the first board (Aug 20): `m01` → `m02`

The first design was an ESP32-C3 board drawn in Altium. Before changing
anything, it got imported into KiCad and checked against the original.

- [Import the Altium board into KiCad, verified exact](https://github.com/Drivera0/touch-id-public/commit/5adc480)
- [Nine orphan `)` made the board file unparseable](https://github.com/Drivera0/touch-id-public/commit/0b921c6), so a syntax gate was added and has run on every edit since
- [Every land pattern traced back to its vendor drawing](https://github.com/Drivera0/touch-id-public/commit/9491082), which found errors on U1, U2 and C3/C4

**Lesson:** a footprint you haven't traced to a datasheet is a guess.

## 2. The master spec and the v3 rebuild (Aug 26 – 27): `m03` → `m05`

The ESP32 was too wide for the slot. The rebuild moved to a BLE-only nRF52840
module on a 4-layer board, and `DESIGN-SPEC.md` became the single source of
truth.

- [DESIGN-SPEC.md becomes the master file](https://github.com/Drivera0/touch-id-public/commit/f3cd050)
- [pcb-v3 built: 4 layers, 177 pads, all three checkers pass](https://github.com/Drivera0/touch-id-public/commit/07b3699)
- [Two checker bugs, including KiCad's Y-down rotation sign (79 phantom shorts)](https://github.com/Drivera0/touch-id-public/commit/332d8c4)
- [U2's land was 0.25 mm off its own centreline](https://github.com/Drivera0/touch-id-public/commit/954c17a)
- [The "open connections" metric was lying](https://github.com/Drivera0/touch-id-public/commit/dac4bf2). A net with zero copper never showed as disconnected, so deleting a net scored as a win.
- [Zero open connections, 15/15 preflight checks](https://github.com/Drivera0/touch-id-public/commit/eb00146)

Compare: [m03 … m05](https://github.com/Drivera0/touch-id-public/compare/m03-design-spec-master...m05-v3-zero-opens)

**Lesson:** when a check fails, suspect the checker first. It was wrong more
often than the board.

## 3. "The board had no ground" (Aug 28): `m06` → `m07`

- [THE BOARD HAD NO GROUND](https://github.com/Drivera0/touch-id-public/commit/f7fea49). Every check passed, and none of them looked for it. The ground pour went in, and a gate was added so it can't happen again.
- [KiCad 10 changed the file format and every parser went blind](https://github.com/Drivera0/touch-id-public/commit/10ab2b4)
- [Altium's DRC found a real defect the KiCad checks couldn't see](https://github.com/Drivera0/touch-id-public/commit/53b6aae). The board was then [re-imported clean](https://github.com/Drivera0/touch-id-public/commit/77dadf8).
- [The pick-and-place file was in the wrong coordinate space](https://github.com/Drivera0/touch-id-public/commit/539baa0)
- [A housing corner wall was 0.15 mm, not 0.8](https://github.com/Drivera0/touch-id-public/commit/792c414)

**Lesson:** cross-check with a second, independent tool.

## 4. Choosing the cell (Aug 28): `m08`

The module needs stored energy, and nothing that fits the cavity is simple.

- [The CP1254 "IP Wires" is not protected and doesn't fit](https://github.com/Drivera0/touch-id-public/commit/12323db)
- [The charge limit is 4.30 V, not 4.00 (a misread footnote)](https://github.com/Drivera0/touch-id-public/commit/4137b64)
- [Cell decided: LiPol LPM1254 with a factory PCM and wires](https://github.com/Drivera0/touch-id-public/commit/5ced9d4)
- [Sensor: the ZW0905 was discontinued; the HLK-ZW0922 is a drop-in](https://github.com/Drivera0/touch-id-public/commit/70e8e7d)

## 5. The long routing fight (Aug 29 – 30): `m09` → `m10`

Adding a protection IC to a 20 × 19 mm board started two days of placement,
routing and ground-pour work.

- [My "it doesn't fit" result was a fourth scanner bug](https://github.com/Drivera0/touch-id-public/commit/e0b85e4)
- [Slot depth was never a constraint: the module stands proud by design](https://github.com/Drivera0/touch-id-public/commit/6a840f6)
- [Reverted three hand-placed ground taps, all of them faulty](https://github.com/Drivera0/touch-id-public/commit/764f574)
- [pour_truth.py judges connectivity against the fill KiCad actually computed](https://github.com/Drivera0/touch-id-public/commit/119ffc2), not a model of it
- [Both press-fit pins had been drilled through copper](https://github.com/Drivera0/touch-id-public/commit/e9f7472)
- [Custom pads: `(size)` is the anchor, not the copper, so every parser read 3× low](https://github.com/Drivera0/touch-id-public/commit/db73654)
- [Rejected a smaller module (BC840M), because it needs a larger board](https://github.com/Drivera0/touch-id-public/commit/8be544b)
- [v5: DRC clean](https://github.com/Drivera0/touch-id-public/commit/e4fab08), then [v6: zero open pads, zero blockers](https://github.com/Drivera0/touch-id-public/commit/03f5192)

Compare: [m09 … m10](https://github.com/Drivera0/touch-id-public/compare/m09-v5-drc-clean...m10-v6-orderable)

**Lesson:** a smaller part isn't always a smaller board. Ceramic-antenna
modules need less keep-out than trace-antenna ones.

## 6. v7 and release (Aug 31 – Sep 1): `m11` → `m13`

- [The protected cell was confirmed, so the on-board PCM was deleted](https://github.com/Drivera0/touch-id-public/commit/537ce61). That removed four parts and healed the last stranded pad.
- `m11`: preflight at 0 blockers, 0 open pads, ground fully connected. The v7 board files are private; the render is above.
- [Pogo-pin flashing jig](https://github.com/Drivera0/touch-id-public/commit/772dad4)
- [Housing v6.5 after JLC's DFM review](https://github.com/Drivera0/touch-id-public/commit/aaf1e26)

## 7. Firmware and the product direction (Aug 31 – Sep 1)

The firmware history is merged in: Zephyr on the nRF52840, the sensor driver,
the auth crypto and the helper apps. The design docs are in `docs/firmware/`; the source
code stays private.

- [Gut the ESP32 fork and start the nRF52840 Zephyr firmware for pcb-v7](https://github.com/Drivera0/touch-id-public/commit/7e738a8)
- [LESC-only pairing, HMAC challenge-response and a hash ratchet](https://github.com/Drivera0/touch-id-public/commit/e65e55e), specified in `docs/firmware/AUTH-CRYPTO.md`
- [Mac keycard proven: `sudo` authenticates by smart card, gated on a touch](https://github.com/Drivera0/touch-id-public/commit/ee9d09f)
- [A smart card you can't remove is a lockout, so that got fixed](https://github.com/Drivera0/touch-id-public/commit/1fa024d)
- [Knob-to-dongle transport: proprietary 2.4 GHz (ESB), not BLE](https://github.com/Drivera0/touch-id-public/commit/b42cfc9)
- [Product pivot: FIDO2 is the core of the product](https://github.com/Drivera0/touch-id-public/commit/80575e5)

---

### Every tag

| Tag | What |
|---|---|
| `as-ordered-Y6` | The first (ESP32) board, exactly as ordered from JLCPCB |
| `pre-v3-rebuild` | Save point before the v3 rebuild |
| `m01-altium-import` | Altium board imported into KiCad, verified exact |
| `m02-land-patterns-traced` | Every land pattern traced to a vendor drawing |
| `m03-design-spec-master` | DESIGN-SPEC.md becomes the master |
| `m04-v3-built` | pcb-v3: 4-layer nRF52840 board |
| `m05-v3-zero-opens` | Zero open connections, 15/15 checks |
| `m06-board-had-no-ground` | Ground pour and its gate |
| `m07-altium-drc-clean` | Altium cross-check: 0 warnings, 0 violations |
| `m08-cell-decided` | Protected LPM1254 cell chosen |
| `m09-v5-drc-clean` | v5: DRC clean |
| `m10-v6-orderable` | v6: zero blockers |
| `m11-v7-zero-opens` | v7 final: gate recorded green |
| `m12-flash-jig` | Pogo-pin flashing jig |
| `m13-housing-v6.5` | Housing v6.5 after JLC DFM |
