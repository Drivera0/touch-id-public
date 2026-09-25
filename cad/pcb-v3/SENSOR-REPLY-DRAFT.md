---
title: Reply to the sensor seller — ZW0922 wires
type: project
---

# Reply to send

Written for a seller reading English as a second language: short sentences,
numbered, no idioms. Copy from the block below.

---

> Thank you for confirming the ZW0922.
>
> About the connector — I do not need the connector, but I do need the wires.
>
> **First choice:** please solder six wires directly to the pads, instead of
> the XH-1.00-6P connector. About **40 mm** long. One wire per pin, in this
> order: **sensor_3.3V, WAKEUP, MCU_3.3V, TX, RX, GND**. Different colours if
> possible.
>
> **Second choice:** if you cannot fit the wires, please remove the connector
> and ship the module with clean, bare pads. I will solder the wires myself.
>
> The connector is 4.5 mm tall and does not fit inside my housing, so it must
> be removed either way. Please tell me which option you can do, and the price
> for each.
>
> Two more questions:
>
> 1. Does the ZW0922 keep the low-power finger detect (FD) mode, with
>    sensor_3.3V powered all the time? I need the 10 µA standby current.
> 2. Is the Ø18.00 mm flange diameter held to ±0.05 mm in production? My
>    housing has only 0.16 mm clearance per side.
>
> Thank you.

---

## Why each number is in there

**40 mm of wire.** J2's pads are split — pins **1–3 at x = −8.2**, pins **4–6
at x = +7.8** — so the six wires fan out from the sensor and drop through
*both* ±X windows in the centring collar, one trio each side. Roughly 12 mm
down, 8 mm across, plus slack. Too long is trimmable; too short is scrap.

**The pin order.** It is the ZW0922's own order from spec §4.3, and it matches
board J2 exactly. Giving it explicitly removes any chance of a reversed loom —
this pinout was already wrong once (it was the ZW0901's table, end-for-end).

**The connector must go regardless.** 4.5 mm tall on the module's back face at
z 11.46 puts its tip at z 6.96, and the cell occupies z 2.25 → 10.65. It would
pass **3.69 mm straight through the battery**, and the Ø15.60 riser bore leaves
nowhere sideways to put it.

**FD mode** is what the whole power budget rests on: 10 µA standby is the
second-largest line in the 4.0 mWh/day budget. If it were an option rather than
standard, the harvest maths changes.

**±0.05 on the flange** — the seat face is Ø18.37 against an Ø18.05 worst-case
flange. That is 0.16 mm per side. Not alarming, but not a number to discover
after five housings are printed.
