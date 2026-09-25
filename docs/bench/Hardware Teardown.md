---
title: Hardware Teardown
type: reference
tags:
  - touchid
  - hardware
  - reference
---

# Hardware Teardown — Air75 V3 internals

> [!abstract] Source
> Everything here comes from the **FCC filing** for FCC ID `2BE3OAIR75V3` (Shenzhen NuPhy Technology). The circuit **schematic was filed but sealed** under long-term confidentiality, so it's metadata-only and not viewable. The **internal photos are public**, and they include both sides of the corner daughterboard. Report No. on the photos: STS2507035.
> Filing index: https://fccid.io/2BE3OAIR75V3

## The corner module slot

The swappable knob/keyswitch sits on a small **daughterboard** silkscreened `Air75V3 VER1.5 2025.5.12` / `BSJ RoHS`. It carries:

| Ref | What it is | Notes |
|---|---|---|
| **J4** | Pogo-pin header, **6 pins** (2×3) — the **LEFT** block looking into the slot | Main module contacts |
| **J11** | Pogo-pin header, **4 pins** (2×2) — the **RIGHT** block | Secondary contacts |
| **J10** | FFC/FPC connector (~8-conductor), labelled 下接 ("connects down") | Links daughterboard → main PCB |
| **J6** | FFC connector on reverse, labelled 上接 ("connects up") | Other side of the same link |
| **S1, S2** | Slide switches | The Mac/Win + connection-mode toggles on the keyboard's edge |
| **TVS13/14/15** | TVS diodes | ESD protection on the pins (expected — pins get touched during module swaps) |
| round hole | Knob shaft / retention screw pass-through | Orientation reference |
| MARK1–4 | Fiducials | Assembly alignment marks |

> [!important] 10 contacts, not 12
> Earlier guess was two 6-pin headers (12). The clear FCC photo shows **J4 = 6, J11 = 4 → 10 total**. Confirmed against the physical unit: 6 on the left, 4 on the right.

> [!note] The signal bottleneck
> 10 pogo contacts feed into only an ~8-conductor FFC (J10), and some of those conductors are used by the S1/S2 slide switches. So **only a handful of the 10 pins carry live signals** — the rest are likely duplicated-for-reliability contacts or split between the keyswitch vs knob modules. A rotary knob needs ~4 lines (encoder A, encoder B, press, ground). Which pins are live — and whether any carry **power** — is what [[touchid/docs/bench/Pin Test Procedure|the pin test]] determines.

## Main board

- **MCU:** WCH **CH592M** — a RISC-V Bluetooth LE SoC. (This is why V2 firmware can't be reused: the V2 uses an ARM chip. Different instruction set entirely.)
- **Battery:** Li-ion, **4000 mAh, 3.6 V nominal** (label: model DHDIC 3240162, 15.2 Wh, made by Huizhou Donghui Energy). This is the power source the module would ideally tap.
- On-board PCB antenna (visible in FCC Photo 4), tucked in a corner near plastic — a reminder that the metal frame blocks Bluetooth. See antenna notes in [[touchid/docs/design/Firmware and PCB|Firmware and PCB]].

## Why this matters for the build

The slot is only guaranteed to be a **mechanical mount**. The exciting open question is electrical: if one of the 10 pins carries usable power (3.3 V rail or the raw battery line), the module can be **powered by the keyboard** and go fully wireless. If not, the fallback is a thin wire to the battery connector, or the module carrying its own small LiPo. That single fact is decided by [[touchid/docs/bench/Pin Test Procedure|the pin test]].

## Related

- [[touchid/docs/bench/Pin Test Procedure|Pin Test Procedure]]
- [[touchid/docs/design/Architecture and Design|Architecture and Design]]
- [[touchid/docs/design/OVERVIEW|Project README]]
