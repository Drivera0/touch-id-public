---
title: Sensor — ZW0905 discontinued, ZW0922 is the replacement
type: project
---

# ZW0905 → ZW0922

**2026-08-28. The seller confirmed the HLK-ZW0905 is discontinued. The
replacement is the HLK-ZW0922.** Spec sheet V1.0, 2024-11-20, supplied by the
seller.

**DESIGN-SPEC called this exact risk** and left it open:

> "**ZW0905 availability.** Hi-Link's product pages `id=1225`/`id=1226` return
> empty while every sibling page renders — consistent with it being delisted.
> Confirm distributor stock before the housing is committed, since **no other
> module on the market has a verified outline under 18.1 mm.**"

It was right, and it has now happened. **The good news: the ZW0922 is a
mechanical and electrical drop-in.** Nothing on the board or in the housing has
to change.

## THE Φ12.8 TRAP — IT IS IN THIS SPEC SHEET TOO

§2.2 "Mechanical characteristics" says **"Dimensions Φ12.8mm"**.

**That is not the module.** It is the sensor package, exactly as it was on the
ZW0905, where this same figure was already caught once. The real outline is in
**§2.3 Dimensions figure**, which is a drawing with no extractable text — it
has to be rendered and read by eye.

**Anyone who sizes a housing from the ZW0922 spec table will build the wrong
part.** Read the drawing.

## What the drawing actually says

From §2.3, top and side views:

| callout | Chinese | meaning | value |
|---|---|---|---|
| `<1>` | 金属环凸出部分 | metal ring **protruding** part = barrel | **Ø15.50 ±0.05** |
| `<2>` | 金属环外形 | metal ring **outline** = flange | **Ø18.00 ±0.05** |
| `<3>` | 装配尺寸 | assembly dimension | 0.95 ±0.05 |
| `<4>` | 台阶厚度 | **step thickness** = flange | **0.20 ±0.05** |
| `<5>` | 金属环+PCB总厚度 | metal ring + PCB **total** | **2.15 ±0.20** |
| — | 连接器高度 | connector height | **4.50** |

## Against the housing, as built

| | housing (v5.2, cut for ZW0905) | ZW0922 | verdict |
|---|---|---|---|
| flange / module OD | 18.00 modelled, seat face Ø18.37 | Ø18.00 ±0.05 → **18.05 max** | **0.160 mm/side** |
| barrel OD | 15.50 modelled, window **Ø15.60** | Ø15.50 ±0.05 → **15.55 max** | **0.050 mm diametral** ← tight |
| flange / step | 0.20 | 0.20 ±0.05 | **match** |
| total thickness | 2.40 | 2.15 ±0.20 → 2.35 max | **thinner — helps** |
| back connector | removed, wires hand-soldered to pads | 4.50 tall, XH-1.00-6P | **same plan as before** |

**Being thinner buys clearance above the cell:**

| sensor thickness | barrel bottom | clear above cell (top z 10.65) |
|---|---|---|
| 2.40 (modelled) | z 11.46 | +0.81 mm |
| 2.35 (ZW0922 max) | z 11.51 | **+0.86 mm** |
| 2.15 (ZW0922 typ) | z 11.71 | **+1.06 mm** |

> [!warning] **The barrel window is the tight spot, and it always was.**
> Ø15.60 window over a Ø15.55 worst-case barrel is **0.05 mm diametral** —
> 0.025 mm per side. This is unchanged from the ZW0905, but it is worth saying
> plainly: **SLA cannot be relied on to hold that.** Expect to ream or sand the
> window on the first print. Widening `sensor_window_d` is cheap if it binds —
> the barrel locates, it does not seal.

## Pinout — identical, pin for pin

| pin | ZW0922 spec §4.3 | board J2 | |
|---|---|---|---|
| 1 | sensor_3.3V | `SENSOR_3V3` | ✓ |
| 2 | WAKEUP (active **high**) | `SENSOR_WAKEUP` | ✓ |
| 3 | MCU_3.3V | `SENSOR_MCU_3V3` | ✓ |
| 4 | TX (module → MCU) | `SENSOR_TX` | ✓ |
| 5 | RX (MCU → module) | `SENSOR_RX` | ✓ |
| 6 | GND | `GND` | ✓ |

**No board change.** J2's corrected pinout (fixed 2026-08-27, when it turned
out to be the ZW0901's table reversed) is correct for the ZW0922 as well.

## Electrical — every number the design was built on still holds

| | ZW0922 | what the design assumed |
|---|---|---|
| supply | 3.0 / **3.3** / 3.6 V | 3.3 V rail from U3 |
| **standby (sensor)** | 8 / **10** / 12 µA | 10 µA typ, 12 µA max — **exact match** |
| **operating (MCU)** | **15** / 25 mA | 15 typ / 25 max — **exact match** |
| **FD peak** | **200 mA for 4 µs** | C7 sized as 200 mA × 4 µs = 0.8 µC — **exact match** |
| ripple limit | **< 200 mV** on sensor_3.3V | C7 specified to < 200 mV — **exact match** |
| UART | 57600 8N1, 3.3 V TTL | as designed |

Hi-Link also recommend the sensor LDO be **≥ 250 mA, ripple < 100 mV,
PSRR > 60 dB**, and that the sensor rail be routed separately from the MCU
rail. The TPS7A2033 (U3/U4) and the separate `SENSOR_3V3` / `SENSOR_MCU_3V3`
nets already do exactly this — the architecture was right.

## What genuinely changed

* **Connector: XH-1.00-6P vertical**, was MX1.0-6P standing paste. Same 6 pins,
  same 1.00 mm pitch, still 4.50 mm tall, and still gets desoldered so the six
  wires can be soldered to the J2 pads. The supplier note about desoldering
  still applies verbatim.
* **Storage: 50 fingerprints.**
* Sensor 112 × 96 px, 508 DPI, round, 8-bit greyscale.
* Comparison time 200 / **700** / 1300 ms — slower than a lock user expects;
  worth measuring against the energy budget, since 700 ms at 15 mA is
  ~10.5 mA·s per match.

## Still to confirm with the seller

1. **Is the ZW0922 the one they will actually ship**, and does the Ø18.00
   flange come with the same 0.05 tolerance in production?
2. **Does it keep the finger-detect (FD) low-power mode** with the sensor rail
   permanently powered? The spec says yes (§4.5), which is what makes the
   10 µA standby budget work — confirm it is not a paid option.
