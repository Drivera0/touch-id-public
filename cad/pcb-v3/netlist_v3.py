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
_u1[31] = "NC"             # DCCH — REG0 in LDO mode leaves this unconnected
                           # (Raytac Ver.K §8.2 block diagram, p.41). DC/DC
                           # would need a 10 uH 0603 to VDDH; not fitted.
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

# ---- U4: TI TPS7A2033DQNR — SWITCHED sensor-MCU rail ----
# Was an LM66100. Changed 2026-08-27: the LM66100's CE is a comparator
# referenced to VIN and needs V_CE > V_IN + 80 mV = 3.38 V to switch OFF,
# which an nRF52840 GPIO (3.3 V max) cannot reach. See B3 in NEXT-SESSION.
# The TPS7A2033 has a LOGIC-LEVEL enable, is the same part as U3 with a
# footprint already traced to TI drawing DQN0004A, and draws 0.07 uA typ
# when disabled (vs the LM66100's 0.12 uA) — so the swap costs nothing.
part("U4", "TI TPS7A2033 3.3 V LDO (switched sensor-MCU rail)", 5, {
    1: "SENSOR_MCU_3V3", # OUT
    2: "GND",
    3: "SENSOR_SW_EN",   # EN — logic level, driven by an nRF GPIO
    4: "VSTOR",          # IN — from the cell rail, NOT cascaded off U3
    5: "GND",            # thermal
}, "Fed from VSTOR rather than cascaded off SENSOR_3V3: cascading would "
   "leave no headroom, and this also keeps the sensor's 25 mA scan current "
   "off the always-on standby rail.")

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

part("J2", "Sensor pads, HLK-ZW0922 (was ZW0905 — discontinued)", 6, {
    1: "SENSOR_3V3",
    2: "SENSOR_WAKEUP",
    3: "SENSOR_MCU_3V3",
    4: "SENSOR_TX",
    5: "SENSOR_RX",
    6: "GND",
}, "DESIGN-SPEC §5 as corrected 2026-08-27. The old table was the ZW0901's, "
   "reversed end-for-end. **2026-08-28: the ZW0905 is DISCONTINUED; the "
   "replacement HLK-ZW0922 has this SAME pin order** (spec V1.0 §4.3), so no "
   "board change. See cad/pcb-v3/SENSOR-ZW0922.md.")

# BT1 IS TWO WIRE-LANDING PADS, NOT A CELL FOOTPRINT. O1.4 at (-7.61, -4.30)
# and (-7.61, -5.90), 1.6 mm pitch, solder_mask_margin -0.1 for a 0.4 mm dam
# (preflight check 16). The cell never touches this board -- it sits in the
# housing pocket and reaches BT1 through its leads.
# YOU SOLDER THE CELL'S LEADS HERE. YOU NEVER PUT AN IRON ON THE CELL:
# CoinPower handbook 8.7 prohibits attaching connectors to the cell; only the
# manufacturer may. Hence a pre-wired assembly. See BUY-YOURSELF.md.
#
# 4.30 V IS CORRECT and has always been. A 2026-08-28 "correction" to 4.00 V
# was WRONG: 4.00 is footnote 3 of the A4/A4X datasheets and applies only to
# RAPID charge at 140 mA. TouchID charges from harvest at microamps, so it
# never applies. The real ceiling on VBAT_OV is the PCM's trip minus 150 mV.
#
# THE CELL NO LONGER NEEDS A PCM. As of 2026-08-29 the protection is ON THIS
# BOARD (U5, Mitsumi MC3651DF1AAM), so BT1 takes a plain BARE 1254-class cell
# with factory-attached leads -- an ordinary retail product, which is what
# finally unblocks sourcing. The hunt for a protected+wired cell is over: none
# exists that an individual can buy. See PCM-ONBOARD.md and BUY-YOURSELF.md.
#
# NOTE PIN 2 IS NOW CELL_NEG, NOT GND. The cell's negative lead goes to the
# PCM, and the board grounds through it.
part("BT1", "Cell wire pads — bare 1254-class cell + factory leads", 2,
     {1: "VBAT", 2: "CELL_NEG"},
     "3.0 V discharge cut-off, 4.30 +-0.05 V charge, 210 mA pulse (CP1254 A4X "
     "figures). Two O1.4 wire-landing pads on 1.6 mm pitch — NOT a cell "
     "footprint. Solder the cell's LEADS here; never put an iron on the cell "
     "(CoinPower handbook 8.7). 4.30 V is the cell's charge voltage; the 4.00 V "
     "in some notes is the RAPID-charge footnote and does not apply here.")

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
# WAS 5.6M / 7.5M = 4.246 V, which OVERCHARGES THE CELL.
# VARTA CP1254 A4 max charging voltage is 4.00 +-0.05 V, so 4.246 V is 246 mV
# over the limit -- and it sits only 54 mV under the 4.30 V point where a PCM
# trips on over-charge. That makes the safety device the de-facto regulator,
# which the CoinPower handbook explicitly warns against.
# 6.04M / 6.98M -> 3.912 V nominal, 3.955 V worst case with 1% parts:
# under the cell's limit in every corner, and 345 mV below the PCM trip.
# Costs ~10% of usable capacity (still ~60 days of autonomy) and BUYS cycle
# life -- charging a Li-ion to a lower ceiling is the single biggest lever on
# how many cycles it survives.
rc("ROV1", "6.04M 0402 1%", "VBAT_OV_SET", "GND",
   "VBAT_OV = 1.5*1.21*(1+6.98/6.04) = 3.912 V, 3.955 V worst case. The cell's "
   "charge voltage is 4.30 V, NOT the 4.00 V some notes claimed — 4.00 is the "
   "rapid-charge footnote. The binding ceiling is the PCM's over-charge trip "
   "minus 150 mV, so pick the cell's PCM before retuning this divider.")
rc("ROV2", "6.98M 0402 1%", "VRDIV", "VBAT_OV_SET")
# The OK divider was re-derived onto 0201 values JLC actually stocks. The old
# 4.53M/7.15M pair exists in 0201 from six manufacturers and NONE of them stock
# it -- 0 at LCSC retail and 0 in JLC's assembly library, pre-order only.
# 4.3M/6.8M/1.33M are in stock (C423523 / C423449 / C423747) and hold the
# thresholds: falling 3.123 V, rising 3.498 V, chain 12.43 M (was 13.01 M).
rc("ROK1", "4.3M 0201", "OK_PROG", "GND",
   "VBAT_OK falling = 1.21*(1+6.8/4.3) = 3.123 V (was 3.120 at 4.53M/7.15M)")
rc("ROK2", "6.8M 0201", "OK_HYST", "OK_PROG")
rc("ROK3", "1.33M 0201", "VRDIV", "OK_HYST",
   "VBAT_OK rising = 1.21*(1+(6.8+1.33)/4.3) = 3.498 V (was 3.470)")

rc("L1", "22uH", "LX", "VIN_DC", "LBOOST -> VIN_DC. Package NOT verified.")
# C1/C2 DC BIAS IS AN OPEN ITEM AND IT IS NOT A FREE FIX. Measured on the
# routed board 2026-08-28: neither can grow from its 0402 land (1.34 x 0.54)
# to an 0603 land (2.20 x 1.00) in place -- C1 collides with 12 neighbouring
# pads/tracks, C2 with 62. So if no 0402 part clears 4.7 uF EFFECTIVE, this
# stops being a BOM swap and becomes a re-place and re-route.
# Real bias is 3.912 V max on VSTOR (not the 4.3 V older notes assumed -- that
# dated from VBAT_OV = 4.246) and ~3.68 V on VIN_DC. See SOURCING.md.
rc("C1", "10uF 10V X5R 0402", "VIN_DC", "GND",
   "CIN. Was 4.7uF — Murata's DC-bias curve showed that part delivering only "
   "~2.3-2.8 uF at this board's 3.9 V, against the BQ25505's 4.7 uF minimum. "
   "Specify by C_eff, never by marked value.")
rc("C2", "10uF 10V X5R 0402", "VSTOR", "GND",
   "CSTOR. Same change as C1. 0603 was not an option — it collides with 62 "
   "neighbouring pads/tracks here (12 at C1), so the land is fixed at 0402 "
   "and more nominal capacitance in the same land was the only lever.")
rc("C3", "0.1uF 0402", "VSTOR", "GND", "CSTOR HF")
rc("C4", "10nF 0402 low-leak", "VREF_SAMP", "GND", "CREF, 9-11 nF window")
rc("C5", "10uF 10V X5R 0402", "VBAT", "GND", "CBAT bulk beside the cell")

rc("C6", "1uF 0402", "SENSOR_3V3", "GND", "LDO input side of U3 is VSTOR; this is OUT")
# The REQUIREMENT is Hi-Link's "sensor-rail ripple < 200 mV" (DESIGN-SPEC 3).
# The old note claimed 36 mV, but 36 mV was merely what a full 22 uF happens to
# give -- it was never the spec, and quoting it hid how much margin there is.
#
#   200 mA x 4 us = 0.8 uC.  droop = 0.8 uC / C_effective
#     C_eff 22 uF -> 36 mV      C_eff 8 uF -> 100 mV
#     C_eff 4 uF  -> 200 mV  <- the vendor limit, the real floor
#
# THE PART MUST BE SPECIFIED BY C_eff AT 3.3 V, NOT BY ITS MARKED VALUE.
# A 22 uF 0603 in the common 6.3 V rating keeps only ~20-30% at 3.3 V DC bias
# (~4-7 uF), and after -20% tolerance and X5R temperature drift the worst case
# lands ON the 4 uF floor. That is not margin, it is a coin toss.
#
# A 10 V rating in the SAME 0603 case derates far less at 3.3 V and roughly
# doubles the delivered capacitance for no area, no height and no cost.
# Verify the exact figure on the vendor's DC-bias curve before ordering.
rc("C7", "22uF 10V X5R 0603", "SENSOR_3V3", "GND",
   "ZW0905 200 mA / 4 us scan transient. REQUIREMENT: ripple < 200 mV "
   "(Hi-Link), so C_eff at 3.3 V bias must be >= 4 uF, target >= 8 uF. "
   "Do NOT substitute a 6.3 V part -- it derates onto the floor.")
rc("C8", "1uF 0402", "SENSOR_MCU_3V3", "GND")

rc("C9", "1uF 0402", "NRF_VDD", "GND", "REG0 output decoupling")
rc("C10", "0.1uF 0402", "VSTOR", "GND", "VDDH decoupling, at the module")
# C11 deleted 2026-08-27: REG0 runs in LDO mode, so DCCH is left unconnected
# and needs no capacitor (Raytac Ver.K §8.2).

# VDDH cold-start hold-off. VBAT_OK is push-pull and referenced to VSTOR, so
# it sits low until storage is good and then rises with the rail the nRF is
# on. Wiring it to nRESET holds the CPU in reset through the slow ramp and
# releases it once the rail is up — the standard supervisor trick, using a
# signal the BQ25505 already provides. See B2.
rc("R7", "1k 0402", "VBAT_OK", "RESET",
   "1k so an SWD programmer can still override RESET")

# cell voltage sense. 4.7M/1M from a 4.25 V rail -> 0.745 V at the tap,
# inside the SAADC's 0-0.6 V internal-reference range only at gain 1/2.
rc("R4", "4.7M 0402", "VSTOR", "VBAT_SENSE")
rc("R5", "1M 0402", "VBAT_SENSE", "GND")
rc("C12", "10nF 0402", "VBAT_SENSE", "GND", "SAADC sampling reservoir")

# backlight flag. NOT a divider — see FLAGS.
rc("R6", "100k 0402", "BL_RETURN", "BL_FLAG", "series protection only")
rc("C13", "10nF 0402", "BL_FLAG", "GND")

# ======================= U5 — ON-BOARD CELL PROTECTION =======================
# Mitsumi MC3651DF1AAM, PLP-4E. Added 2026-08-29.
#
# WHY IT IS HERE AND NOT ON THE CELL: no protected 1254-class cell exists that
# an individual can buy (see BUY-YOURSELF.md). Putting the PCM on the board
# means ANY bare cell with factory leads will do -- an ordinary retail product.
# It also lets the housing riser come back down from 6.50 to 4.50 mm.
#
# TOPOLOGY (datasheet "Typical application circuit", p.6). The PCM sits in the
# NEGATIVE path; the positive goes straight through:
#
#     cell + (B+) --------------------------------------> VBAT   (= P+)
#     cell - (B-) --> CELL_NEG --> U5 S1 ... U5 S2 -----> GND    (= P-)
#                         R8:  VBAT     -> PCM_VDD
#                         R9:  PCM_VM   -> GND
#                         C14: PCM_VDD  -> CELL_NEG
#
# BT1 pin 2 IS NO LONGER GND. It is CELL_NEG, and the only things on that net
# are the cell lead, U5's S1 and C14. Everything else grounds THROUGH the PCM,
# which is the entire point: a short anywhere downstream gets interrupted.
#
# The datasheet calls these R1/R2/C1. Renamed R8/R9/C14 because this board
# already has an R1, R2 and C1 doing something completely different.
#
# *** PIN 5 (D) IS THE FET DRAIN AND MUST BE ELECTRICALLY OPEN. ***
# It is the node between the two series FETs. Connecting it to GND bypasses the
# protection and leaves a part that looks healthy and does nothing. Solder it
# for mechanical anchorage only.
part("U5", "Mitsumi MC3651DF1AAM cell protection, PLP-4E", 5, {
    1: "CELL_NEG",     # S1  — cell negative / discharge FET source
    2: "PCM_VDD",      # VDD — cell positive sense, through R8
    3: "PCM_VM",       # V-  — charger negative sense, through R9
    4: "GND",          # S2  — charge FET source = pack negative
    5: "NC",           # D   — drain. MUST STAY OPEN.
}, "Over-charge 4.280 V, over-discharge 2.700 V, discharge over-current "
   "0.315 A -- 2.2x the cell's 140 mA rating, and the reason this part beat "
   "the AP6683's 0.9 A. Iq 3.0 uA typ / 4.5 max = 6.7 % of the 4.0 mWh/day "
   "budget. Digi-Key 2508-MC3651DF1AAMCT-ND, US$1.33 at qty 1.")

rc("R8", "330R 0201", "VBAT", "PCM_VDD",
   "Datasheet R1. VDD series protection; 330R typ, 470R max.")
rc("R9", "2.7k 0201", "PCM_VM", "GND",
   "Datasheet R2. FUNCTIONAL, not optional -- every over-current figure in the "
   "datasheet is measured with R2 = 2.7k. Omit it and 0.315 A is not 0.315 A.")
rc("C14", "0.1uF 0201", "PCM_VDD", "CELL_NEG",
   "Datasheet C1. Across VDD and S1, for supply-voltage fluctuation.")

# The datasheet's C2 (S1 to V-) and C3 (across the pack) are drawn DASHED, and
# the text says "use either C2 or C3, or both, by request of your application".
# Neither is fitted: the pack side already carries C5 (10uF) on VBAT/GND, and
# board area is the scarce resource. Revisit if ESD testing says otherwise.


# ------------------------------------------------------------- the check ----
RESOLVED = [
    ("B3  U4 / SENSOR_SW_EN — FIXED",
     "The LM66100 is gone. Its CE is a comparator referenced to VIN and "
     "needs 3.38 V to switch off; an nRF GPIO reaches 3.3 V. U4 is now a "
     "second TPS7A2033 with a logic-level EN, fed from VSTOR."),
    ("B2  U1 pin 30 / VDDH cold start — MITIGATED",
     "Raytac t_R VDDH = 100 ms max; a harvest-charged cell ramps over hours. "
     "R7 ties BQ25505 VBAT_OK to nRESET, holding the CPU in reset until "
     "storage passes 3.47 V and releasing it on a clean rail. Zero new parts. "
     "VALIDATE ON THE FIRST BOARD — this is the standard supervisor trick but "
     "it has not been proven on this hardware."),
    ("B7  U1 pin 31 / DCCH — SETTLED",
     "REG0 runs in LDO mode: DCCH unconnected, no 10 uH inductor, VDD "
     "decoupled by C9. Confirmed from Raytac Ver.K §8.2 block diagram p.41, "
     "which shows DCCH with no connection. Costs ~29 % of the nRF's own "
     "energy, which is under 5 % of the daily budget; board area wins."),
    ("B5  SENSOR_3V3 headroom — QUANTIFIED",
     "TPS7A20 dropout is specified only as 140 mV MAX at 300 mA (DQN, VOUT "
     "2.5-5.5 V). At the sensor's 25 mA it is far lower, but the datasheet "
     "gives that only as a curve. Taking the worst case, SENSOR_3V3 holds "
     "3.0 V as long as VSTOR >= 3.14 V, so set the FIRMWARE FLOOR AT 3.15 V, "
     "not the 3.0 V in the brief. The capacity between 3.15 and 3.0 V is a "
     "small tail of the CP1254 curve."),
    ("B8  L1 — IDENTIFIED",
     "LCSC C2849435 = DMBJ PNLS252012-220M, 22 uH. The part code gives "
     "2.5 x 2.0 x 1.2 mm, so it clears housing v5's 1.65 mm under-ledge "
     "headroom. DCR and Isat still not traced — TI characterised the "
     "BQ25505 with a Coilcraft LPS4018-223."),
]

FLAGS = [
    ("BL_FLAG / R6",
     "NEXT-SESSION specifies '1M/220k' on J11-4. The MEASUREMENTS say that "
     "cannot work: J11-4 reads 0.316 V awake and 0.000 V asleep "
     "(Pin Test Results, 3-6 ohm source). Both are below any digital V_IL, so "
     "a GPIO cannot tell them apart, and a 1M/220k divider would shrink "
     "0.32 V to 0.06 V. This netlist uses a 100k series resistor into an "
     "SAADC pin and reads it as an ANALOG value, threshold ~0.15 V."),
    ("B6  BT1 PCM — RESOLVED AS A PROCUREMENT ITEM. It cannot go on this board.",
     "VARTA CoinPower handbook 6.3: a CoinPower cell MUST run with a PCM "
     "providing over-charge, over-discharge, over-current AND short-circuit "
     "protection. It names acceptable parts: SGM41100V, Ricoh R5613L, Seiko "
     "S8211CAY/S8200A, Mitsumi MM3077LY, TI BQ29700/29707, Diodes AP9211. "
     "MEASURED on pcb-v3: 9.1 % of the top layer is free, and there is NO "
     "free spot anywhere -- not even 1.3 x 1.3 mm -- where a VIA IS LEGAL. "
     "Every remaining gap sits over a J4/J11 pogo pad, and a through-hole "
     "via there exits through the mating contact. The AP9211 (2.0 x 3.0, "
     "the only single-chip option, FETs included) does not fit at all. "
     "So the PCM goes ON THE CELL: buy the CP1254 as a protected, tabbed "
     "assembly and solder its two leads to BT1's wire pads. That also "
     "retires the 'VARTA publishes no tab geometry' warning, because the "
     "assembly's leads are specified by whoever builds it. "
     "IF a future revision puts the PCM on the board instead, it needs "
     "~2.0 x 3.0 mm WITH via access, which means freeing area -- most "
     "plausibly a narrower BLE module, since U1 is 10.5 x 15.5 on a "
     "19.3 mm square."),
    ("B6b VBAT_OV WAS OVERCHARGING THE CELL — FIXED",
     "ROV1/ROV2 were 5.6M/7.5M, giving VBAT_OV = 4.246 V. The CP1254 A4's "
     "maximum charging voltage is 4.00 +-0.05 V, so the charger was set "
     "246 mV ABOVE the cell limit -- and only 54 mV under the 4.30 V "
     "over-charge trip of the very PCM that B6 adds, which would have made "
     "the safety device the working regulator. Now 6.04M/6.98M = 3.912 V "
     "nominal, 3.955 V worst case with 1 % parts."),
    ("Load budget grew — 3.3 -> 4.0 mWh/day",
     "The always-on LDO's own quiescent current was never counted. TPS7A20 "
     "IGND is 6.5 uA typ / 10 uA over -40..85 C, against the sensor's 10 uA "
     "standby. Add the cell-sense divider (4.7M+1M across VSTOR = 0.75 uA). "
     "New total ~4.0 mWh/day: scans 1.93, sensor standby 0.89, U3 quiescent "
     "0.58, nRF sleep 0.53, divider 0.07. Harvest still covers it about 4.7x "
     "on four hours of backlight, down from 6x. U4 disabled adds nothing "
     "(0.07 uA)."),
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
    print("RESOLVED since the first pass — the design changed, read these")
    print("=" * 74)
    for where, txt in RESOLVED:
        print(f"\n  + {where}")
        for line in [txt[i:i + 68] for i in range(0, len(txt), 68)]:
            print(f"      {line}")

    print("\n" + "=" * 74)
    print("STILL OPEN. Not cosmetic.")
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
    print("  NOTE: structurally complete, and the two architecture faults are")
    print("        fixed. The items under STILL OPEN are design/procurement")
    print("        decisions, not wiring errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
