#!/usr/bin/env bash
# route_touchid.sh — reproduce pcb-v3-handoff.kicad_pcb from pcb-v3.kicad_pcb.
#
# Zero open connections needs THREE steps, not one. Recorded here because the
# result is otherwise unreproducible and I would have to rediscover it.
#
#   pass 1  whole board, netclass widths, 0.40 mm power trunks
#   pass 2  rip OK_PROG/OK_HYST and re-route them AFTER VBAT_OK
#   nudge   move one via off the exact clearance limit
#
# WHY PASS 2 EXISTS
# U2's east pins (11 OK_HYST, 12 OK_PROG, 13 VBAT_OK) have 0.26 mm between
# them -- too tight for any track to pass -- so all three must escape eastward
# through the gap between the package and the housing lip. That corridor fits
# about one track. Whichever net routes first takes it. In pass 1 OK_PROG wins
# and then runs 10 mm north up the board edge, walling VBAT_OK's pin in
# completely: a flood fill from that pad reaches x = 8.775 and stops.
# Re-routing VBAT_OK alone cannot fix it -- the corridor is already occupied.
# Ripping the squatter and re-routing it AFTER the pin it was starving does.
#
# Net ORDER is the whole trick, and --ordering original is what respects the
# order given in --nets.
set -euo pipefail
D="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KRT="${KRT:-/tmp/krt}"
FLOOR="$D/fab_floor_touchid.txt"
IN="${1:-$D/pcb-v3.kicad_pcb}"
OUT="${2:-$D/pcb-v3-handoff.kicad_pcb}"
T1=$(mktemp /tmp/tid1.XXXX.kicad_pcb); T2=$(mktemp /tmp/tid2.XXXX.kicad_pcb)

cd "$KRT"
echo "pass 1 — whole board"
PYTHONPATH="$KRT" python3 py_router/route.py "$IN" "$T1" \
  --nets "*" "!GND" --layers F.Cu In1.Cu B.Cu \
  --layer-costs 1.0 1.0 2.0 50.0 --grid-step 0.05 \
  --power-nets VSTOR VBAT VIN_DC LX SENSOR_3V3 SENSOR_MCU_3V3 \
  --power-nets-widths 0.4 0.4 0.4 0.4 0.4 0.4 \
  --keep-input-copper --no-fix-drc-settings \
  --fab-tier standard --fab-overrides "$FLOOR"

echo "pass 2 — VBAT_OK first, then the two nets that were blocking it"
PYTHONPATH="$KRT" python3 py_router/route.py "$T1" "$T2" \
  --nets VBAT_OK OK_PROG OK_HYST --rip-existing-nets OK_PROG OK_HYST \
  --ordering original --track-width 0.127 --clearance 0.10 \
  --layers F.Cu In1.Cu B.Cu --layer-costs 1.0 1.0 2.0 50.0 --grid-step 0.05 \
  --keep-input-copper --no-fix-drc-settings \
  --fab-tier standard --fab-overrides "$FLOOR"

python3 /tmp/strip.py "$T2" "$OUT"

# The router will sit exactly ON the rule if it helps: this via landed at
# precisely 0.1000 mm from an OK_HYST track. Legal, and the worst place to be.
echo "nudge — one via off the clearance limit"
python3 "$D/nudge.py" "$OUT" 8.95 -4.55 9.00 -4.55 || true

# ---------------------------------------------------------------------------
# STEP 4 - THE GROUND PLANE. Do not skip this; the board is inert without it.
# Signals were routed with GND deliberately excluded ("pour last", the normal
# order). If you stop here you get a board with 0 open connections and FORTY
# GND pads connected to nothing -- which is exactly what happened, and it
# passed every check, because check 6 excludes GND by name.
# ---------------------------------------------------------------------------
cp "$D/pcb-v3.kicad_pro" "${OUT%.kicad_pcb}.kicad_pro" 2>/dev/null || true
T3=$(mktemp /tmp/tid3.XXXX.kicad_pcb); cp "$D/pcb-v3.kicad_pro" "${T3%.kicad_pcb}.kicad_pro"
echo "step 4a - pour GND on F.Cu / In2.Cu / B.Cu"
PYTHONPATH="${PYTHONPATH:-}:$KRT" python3 "$KRT/py_router/route_planes.py" "$OUT" \
  --output "$T3" --overwrite --nets GND GND GND --plane-layers F.Cu In2.Cu B.Cu \
  --via-size 0.6 --via-drill 0.3 --track-width 0.127 --clearance 0.10 \
  --no-fix-drc-settings --fab-tier standard --fab-overrides "$FLOOR"

# route_planes lays the plane but places NO taps, and the route step that would
# weld them rips other nets to do it (its own improvement gate rejected that:
# 5 nets broken to gain 1). So the taps go in deterministically.
echo "step 4b - weld every GND pad to the plane"
python3 "$D/gnd_taps.py" "$T3" "$OUT"

cp "$D/pcb-v3.kicad_pro" "$D/pcb-v3-handoff.kicad_pro"   # rules MUST ship with it
echo
echo "now run:  python preflight.py pcb-v3-handoff.kicad_pcb"
echo "  (check 17 is the one that proves ground actually exists)"
