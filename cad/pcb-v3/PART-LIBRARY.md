
## 2026-08-27 — footprint provenance ledger (post JLCPCB re-source)

| part | source | status |
|---|---|---|
| U1 MDBT50Q | Raytac Ver. K p.11 × JLCPCB C5118826, cross-checked to 0.0002 mm | **verified** |
| U2 BQ25505 | TI RGR0020A 4219031/B. JLC C882746 is *wider* (0.665×0.28 vs 0.60×0.24), closing the pad gap 0.26→0.22 mm | **verified, TI kept on purpose** |
| U3/U4 TPS7A2033 | TI DQN0004A 4215302/E, verbatim from pcb-v2 | **verified** |
| 0402 (22 parts) | JLCPCB C1525 CL05B104KO5NNNC: 0.50×0.54 @ 0.84 | **verified** |
| 0603 (C5, C7) | JLCPCB C19666 CL10A475KO8NNNC: 0.80×0.90 @ 1.40 | **verified** (was IPC nominal) |
| L1 22 µH | JLCPCB C2849435, corroborated: the 252012 datasheet gives terminals **2.0 mm wide**, so a 2.2 mm pad is right and my 0.96 mm never was | **verified** — caveat: LCSC links a *Sunlord SWPA* datasheet, not DMBJ's own drawing |
| **BT1 CP1254** | my own wire pads. VARTA does not publish tab geometry | **NOT verified — by choice.** Cell is wired from above |
| **J4 / J11 pogo** | carried from pcb-v2 unchanged; DESIGN-SPEC marks them "**fixed by keyboard**" | **NOT re-verified this session.** Rests on a physical measurement of the keyboard slot |

The pogo pads are the one dimension that cannot be closed from a datasheet —
they are the mechanical interface to Daniel's keyboard and only a measurement
of the real slot can confirm them. If they are wrong the module does not make
contact, so they are the highest-consequence unverified number on the board.
