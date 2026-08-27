"""
TouchID v3 netlist — every pin of every part, connected or explicitly NC.

Run it. It checks itself:
  * every pin of every part appears exactly once
  * every net has >= 2 connections (a 1-pin net is a wiring error)
  * pin counts match the datasheets in PART-LIBRARY.md
  * flags carried from PART-LIBRARY.md §9 are printed loudly

This file is the source of truth for Task D. Do not hand-edit a netlist
somewhere else and expect them to agree.

Sources for every pin assignment are in PART-LIBRARY.md.
"""
import sys
from collections import defaultdict

# ---------------------------------------------------------------- parts ----
# (ref, part, expected_pin_count, {pin: net})
# net "NC" means deliberately not connected. It is not a hole in the design.

PARTS = []


def part(ref, name, npins, pins, note=""):
    PARTS.append(dict(ref=ref, name=name, npins=npins, pins=pins, note=note))


# ---- U1: Raytac MDBT50Q-1MV2, 61 pins (Ver. K §2.5) ----
# VDDH is pin 30. VDD (28) is the REG0 OUTPUT, not a supply input.
_u1 = {}
for p in (1, 2, 15, 33, 55):
    _u1[p] = "GND"
_u1[28] = "NRF_VDD"        # REG0 output — decouple only, never drive
_u1[30] = "VSTOR"          # VDDH.  2.5-5.5 V.  <-- the cell rail
_u1[31] = "NRF_DCCH"       # REG0 DC/DC node — see FLAGS
_u1[32] = "GND"            # VBUS: USB unused, tie to GND
_u1[34] = "NC"             # D-  (USB disabled, Raytac §8.5: leave NC)
_u1[35] = "NC"             # D+
_u1[51] = "SWDIO"
_u1[53] = "SWCLK"
_u1[40] = "RESET"          # P0.18 / nRESET
# functional assignments
_u1[9] = "VBAT_SENSE"      # P0.03 / AIN1  — cell voltage divider tap
_u1[11] = "BL_FLAG"        # P0.02 / AIN0  — J11-4 backlight flag (ANALOG)
_u1[16] = "VBAT_OK"        # P0.27         — BQ25505 storage-good
_u1[19] = "SENSOR_SW_EN"   # P0.26         — load-switch enable
_u1[22] = "SENSOR_TX"      # P0.06         — sensor TX  -> nRF RX
_u1[23] = "SENSOR_WAKEUP"  # P0.07         — sensor finger-detect out
_u1[24] = "SENSOR_RX"      # P0.08         — nRF TX     -> sensor RX
for p in range(1, 62):
    _u1.setdefault(p, "NC")
part("U1", "Raytac MDBT50Q-1MV2 (nRF52840)", 61, _u1,
     "17/18 = XL1/XL2 left NC: internal LFRC, no 32.768 kHz crystal. "
     "Saves a 3215 crystal + 2 caps; costs ~2 uA of the 6 uA sleep budget.")

# ---- U2: TI BQ25505, VQFN-20 + thermal pad (SLUSBJ3F §5) ----
part("U2", "TI BQ25505", 21, {
    1:  "GND",           # VSS
    2:  "VIN_DC",        # + CIN 4.7u, + L1
    3:  "GND",           # VOC_SAMP -> GND = MPPT at 50 % of VOC
    4:  "VREF_SAMP",     # CREF 10 nF low-leakage to GND
    5:  "GND",           # EN, active low -> enabled
    6:  "GND",           # NC pin, datasheet: tie to the PowerPad
    7:  "VBAT_OV_SET",   # ROV1 5.6M to GND, ROV2 7.5M to VRDIV -> 4.246 V
    8:  "VRDIV",         # top of BOTH divider chains
    9:  "NC",            # VB_SEC_ON — no external PMOS. "Leave floating."
    10: "NC",            # VB_PRI_ON — ditto
    11: "OK_HYST",       # chain: VRDIV-ROK3-OK_HYST-ROK2-OK_PROG-ROK1-GND
    12: "OK_PROG",
    13: "VBAT_OK",
    14: "NC",            # VBAT_PRI — no primary cell. "Leave floating."
    15: "GND",           # VSS
    16: "GND",           # NC pin, datasheet: tie to GND
    17: "GND",           # NC pin, datasheet: tie to GND
    18: "VBAT",          # VBAT_SEC — the CP1254 hangs here
    19: "VSTOR",         # boost output = the system rail
    20: "LX",            # LBOOST -> L1 -> VIN_DC
    21: "GND",           # thermal pad
}, "VSTOR (19) is the load rail; the cell sits on VBAT_SEC (18). "
   "The brief says 'BQ25505 VBAT <-> cell' but the part has no pin called "
   "VBAT — this is TI's own topology, Figure 16.")

# ---- U3: TI TPS7A2033DQNR, X2SON-4 + thermal (DESIGN-SPEC §3) ----
part("U3", "TI TPS7A2033 3.3 V LDO (sensor rail)", 5, {
    1: "SENSOR_3V3",     # OUT, + 22 uF local
    2: "GND",
    3: "VSTOR",          # EN tied high -> always on
    4: "VSTOR",          # IN
    5: "GND",            # thermal
}, "Always on. Feeds the ZW0905's 10 uA standby rail.")

# ---- U4: TI LM66100, SC-70-6 (SLVSEZ8A §5) ----
part("U4", "TI LM66100 load switch (sensor MCU rail)", 6, {
    1: "SENSOR_3V3",     # VIN
    2: "GND",
    3: "SENSOR_SW_EN",   # CE — see FLAGS, this does not work as drawn
    4: "GND",            # N/C pin: "tie to GND or leave floating"
    5: "GND",            # ST unused: "connect to GND if not required"
    6: "SENSOR_MCU_3V3", # VOUT
}, "Wired exactly as NEXT-SESSION specifies. See FLAGS — the datasheet says "
   "a GPIO cannot switch this off.")

# ---- connectors ----
part("J11", "Keyboard slot, 4-pin pogo block (RIGHT)", 4, {
    1: "HARV_1",   2: "HARV_2",   3: "HARV_3",
    4: "BL_RETURN",
}, "1/2/3 are the RGB LED anodes. 4 is the LED common return.")

part("J4", "Keyboard slot, 6-pin pogo block (LEFT)", 6, {
    1: "NC", 2: "NC", 3: "NC", 4: "NC",
    5: "GND",        # the ONLY J4 pin used — real chassis ground
    6: "NC",
}, "J4-1/3/4 must stay unconnected: loading them in knob mode generated "
   "volume/mute events (session 3).")

part("J2", "Sensor pads, HLK-ZW0905 (CORRECTED pinout)", 6, {
    1: "SENSOR_3V3",
    2: "SENSOR_WAKEUP",
    3: "SENSOR_MCU_3V3",
    4: "SENSOR_TX",
    5: "SENSOR_RX",
    6: "GND",
}, "DESIGN-SPEC §5 as corrected 2026-08-27. The old table was the ZW0901's, "
   "reversed end-for-end.")

part("BT1", "VARTA CP1254 A4", 2, {1: "VBAT", 2: "GND"},
     "3.0 V discharge cut-off, 4.30 +-0.05 V charge, 210 mA pulse.")

# ---- SWD + test points ----
part("J3", "SWD pads", 5, {
    1: "SWDIO", 2: "SWCLK", 3: "RESET", 4: "VSTOR", 5: "GND",
}, "Pads, not a connector. Pin 4 is the rail, so a programmer can see "
   "target voltage.")

_tp = {
    "TP1": "VIN_DC", "TP2": "VSTOR", "TP3": "VBAT", "TP4": "VBAT_OK",
    "TP5": "SENSOR_3V3", "TP6": "SENSOR_MCU_3V3", "TP7": "BL_RETURN",
    "TP8": "GND", "TP9": "GND", "TP10": "GND",
}
for _r, _n in _tp.items():
    part(_r, "test point, B.Cu", 1, {1: _n},
         "keep on the -Y half — the +Y half is the antenna keep-out")

# ---- passives ----
def rc(ref, name, a, b, note=""):
    part(ref, name, 2, {1: a, 2: b}, note)


# harvest current limiting — also what isolates the three channels,
# which is why no ORing diodes are needed
rc("R1", "1k 0402", "HARV_1", "VIN_DC", "caps awake draw to ~1.1 mA/pin")
rc("R2", "1k 0402", "HARV_2", "VIN_DC")
rc("R3", "1k 0402", "HARV_3", "VIN_DC")

# BQ25505 programming — all 0402 so they can be swapped by hand
rc("ROV1", "5.6M 0402", "VBAT_OV_SET", "GND", "VBAT_OV = 1.5*1.21*13.1/5.6 = 4.246 V")
rc("ROV2", "7.5M 0402", "VRDIV", "VBAT_OV_SET")
rc("ROK1", "4.53M 0402", "OK_PROG", "GND", "VBAT_OK falling = 3.12 V")
rc("ROK2", "7.15M 0402", "OK_HYST", "OK_PROG")
rc("ROK3", "1.33M 0402", "VRDIV", "OK_HYST", "VBAT_OK rising = 3.47 V")

rc("L1", "22uH", "LX", "VIN_DC", "LBOOST -> VIN_DC. Package NOT verified.")
rc("C1", "4.7uF 0603", "VIN_DC", "GND", "CIN, datasheet minimum")
rc("C2", "4.7uF 0603", "VSTOR", "GND", "CSTOR")
rc("C3", "0.1uF 0402", "VSTOR", "GND", "CSTOR HF")
rc("C4", "10nF 0402 low-leak", "VREF_SAMP", "GND", "CREF, 9-11 nF window")
rc("C5", "10uF 0805", "VBAT", "GND", "CBAT bulk beside the cell")

rc("C6", "1uF 0402", "SENSOR_3V3", "GND", "LDO input side of U3 is VSTOR; this is OUT")
rc("C7", "22uF 0805", "SENSOR_3V3", "GND",
   "holds the ZW0905's 200 mA / 4 us scan transient to 36 mV. 1.25 mm TALL.")
rc("C8", "1uF 0402", "SENSOR_MCU_3V3", "GND")

rc("C9", "1uF 0402", "NRF_VDD", "GND", "REG0 output decoupling")
rc("C10", "0.1uF 0402", "VSTOR", "GND", "VDDH decoupling, at the module")
rc("C11", "1uF 0402", "NRF_DCCH", "GND", "see FLAGS — mode not settled")

# cell voltage sense. 4.7M/1M from a 4.25 V rail -> 0.745 V at the tap,
# inside the SAADC's 0-0.6 V internal-reference range only at gain 1/2.
rc("R4", "4.7M 0402", "VSTOR", "VBAT_SENSE")
rc("R5", "1M 0402", "VBAT_SENSE", "GND")
rc("C12", "10nF 0402", "VBAT_SENSE", "GND", "SAADC sampling reservoir")

# backlight flag. NOT a divider — see FLAGS.
rc("R6", "100k 0402", "BL_RETURN", "BL_FLAG", "series protection only")
rc("C13", "10nF 0402", "BL_FLAG", "GND")

# ------------------------------------------------------------- the check ----
FLAGS = [
    ("U4 / SENSOR_SW_EN",
     "LM66100 CE is a COMPARATOR input referenced to VIN, not a logic input. "
     "Datasheet V_OFF: turning the switch OFF needs V_CE > V_IN + 80 mV = "
     "3.38 V with V_IN = SENSOR_3V3. An nRF52840 GPIO reaches VDD, 3.3 V at "
     "most. It can turn the switch ON and cannot turn it OFF. "
     "Cheapest fix: a second TPS7A2033 from VSTOR with its logic-level EN on "
     "the GPIO — same footprint as U3, already traced, deletes U4."),
    ("U1 pin 30 / VSTOR",
     "Raytac Ver. K §5.2 gives t_R VDDH = 100 ms MAX for 0 -> 3.7 V. A cell "
     "charged from harvest rises over hours. Gate VDDH with a switch driven "
     "by VBAT_OK so the module sees an edge, not a ramp."),
    ("U1 pin 31 / NRF_DCCH",
     "REG0 DC/DC vs LDO is not settled. DC/DC needs a 10 uH 0603 (IDC >= "
     "80 mA) between DCCH and VDDH; LDO mode does not. Raytac §8.1-8.3 are "
     "drawings that would not extract. C11 is a placeholder. Confirm before "
     "layout."),
    ("BL_FLAG / R6",
     "NEXT-SESSION specifies '1M/220k' on J11-4. The MEASUREMENTS say that "
     "cannot work: J11-4 reads 0.316 V awake and 0.000 V asleep "
     "(Pin Test Results, 3-6 ohm source). Both are below any digital V_IL, so "
     "a GPIO cannot tell them apart, and a 1M/220k divider would shrink "
     "0.32 V to 0.06 V. This netlist uses a 100k series resistor into an "
     "SAADC pin and reads it as an ANALOG value, threshold ~0.15 V."),
    ("SENSOR_3V3 headroom",
     "U3 is a 3.3 V fixed LDO fed from VSTOR, which falls to 3.0 V at the "
     "cell's discharge cut-off. Output then equals VSTOR minus dropout, "
     "below the ZW0905's 3.0 V minimum. The firmware floor must be set from "
     "U3's dropout at 25 mA, NOT at the 3.0 V the brief assumes. Dropout not "
     "yet traced."),
    ("BT1",
     "VARTA: 'Cell must not be used without external safety electronics "
     "(PCM).' There is no PCM in this netlist. PART-LIBRARY §9 item 4."),
]


def main():
    print("=" * 74)
    print("TouchID v3 netlist check")
    print("=" * 74)
    nets = defaultdict(list)
    bad = 0
    for p in PARTS:
        got = sorted(p["pins"])
        if len(got) != p["npins"]:
            print(f"  [FAIL] {p['ref']}: {len(got)} pins defined, "
                  f"datasheet says {p['npins']}")
            bad += 1
        for pin, net in p["pins"].items():
            if net != "NC":
                nets[net].append(f"{p['ref']}-{pin}")
    print(f"  parts                : {len(PARTS)}")
    print(f"  pins defined         : {sum(len(p['pins']) for p in PARTS)}")
    nc = sum(1 for p in PARTS for n in p['pins'].values() if n == "NC")
    print(f"  deliberate no-connect: {nc}")
    print(f"  nets                 : {len(nets)}")

    print("\n  --- nets ---")
    for n in sorted(nets, key=lambda k: (-len(nets[k]), k)):
        c = nets[n]
        mark = "  " if len(c) >= 2 else "!!"
        if len(c) < 2:
            bad += 1
        print(f"  {mark} {n:<16} {len(c):>2}  {', '.join(c)}")

    print("\n" + "=" * 74)
    print("FLAGS — carried from PART-LIBRARY.md §9. Not cosmetic.")
    print("=" * 74)
    for where, txt in FLAGS:
        print(f"\n  * {where}")
        for line in [txt[i:i + 68] for i in range(0, len(txt), 68)]:
            print(f"      {line}")

    print("\n" + "=" * 74)
    if bad:
        print(f"  {bad} PROBLEM(S) — netlist is NOT complete")
        return 1
    print("  every pin accounted for; no single-pin nets")
    print("  NOTE: 'complete' means structurally complete. Six FLAGS above "
          "are\n        unresolved DESIGN questions, not wiring errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
