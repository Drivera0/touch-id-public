# Merges Espressif's OFFICIAL ESP32-C3-MINI-1 footprint into the board with
# nets assigned to the real pin numbers (verified against the official symbol:
# official/c3mini1_pinmap.json). Run AFTER `OFFICIAL_U1=1 python build_board.py`.
#
# Run: python3 build_board_official.py

import os, json
from kiutils.board import Board
from kiutils.footprint import Footprint
from kiutils.items.common import Position, Net

HERE = os.path.dirname(os.path.abspath(__file__))
OX, OY = 100.0, 100.0
NETS = {1:"VBAT", 2:"GND", 3:"+3V3", 4:"FP_TX", 5:"FP_RX", 6:"FP_INT",
        7:"USB_DP", 8:"USB_DN", 9:"BOOT_IO9"}

# net by REAL pin number (from the official symbol pin map):
#  3=3V3, 8=EN(->3V3), 6=GPIO3(INT), 30=GPIO20/U0RXD(<-sensor TX),
#  31=GPIO21/U0TXD(->sensor RX), 26=USB_D-, 27=USB_D+, 23=GPIO9(BOOT)
pinmap = json.load(open(os.path.join(HERE, "official/c3mini1_pinmap.json")))
NET_BY_PIN = {"3":3, "8":3, "6":6, "30":4, "31":5, "26":8, "27":7, "23":9}
for num, name in pinmap.items():
    if name == "GND":
        NET_BY_PIN.setdefault(num, 2)

fp = Footprint.from_file(os.path.join(HERE, "official/ESP32-C3-MINI-1.kicad_mod"))
# ROTATED 180: antenna points to kicad +y = DOWN toward the keyboard interior
# (module lives in the metal top-right corner; antenna must face the plastic)
fp.position = Position(X=OX, Y=OY, angle=180)
for _p in fp.pads:
    _a = (_p.position.angle or 0) + 180
    _p.position = Position(X=_p.position.X, Y=_p.position.Y, angle=_a % 360)
fp.libId = "Espressif:ESP32-C3-MINI-1"
for g in fp.graphicItems:                    # set the reference text
    if g.__class__.__name__ == "FpText" and getattr(g, "type", "") == "reference":
        g.text = "U1"
assigned = {}
for p in fp.pads:
    n = NET_BY_PIN.get(p.number, 0)
    if n:
        p.net = Net(number=n, name=NETS[n])
        assigned.setdefault(NETS[n], []).append(f"{p.number}({pinmap.get(p.number,'?')})")

# duplicate the Espressif 3D model ref for KiCad 9/10 path variables (the
# footprint ships with only the KiCad 8 one; user runs KiCad 10)
import copy as _copy
extra = []
for _mdl in fp.models:
    for _var in ("KICAD9_3RD_PARTY", "KICAD10_3RD_PARTY"):
        _c = _copy.deepcopy(_mdl)
        _c.path = _mdl.path.replace("KICAD8_3RD_PARTY", _var)
        extra.append(_c)
fp.models += extra

board = Board.from_file(os.path.join(HERE, "touchid_module.kicad_pcb"))
board.footprints.append(fp)
board.to_file(os.path.join(HERE, "touchid_module.kicad_pcb"))

# requote wildcard layer lists (kiutils strips the quotes; KiCad then shows
# the "items on undefined layers - rescue?" dialog)
import re as _re
_p = os.path.join(HERE, "touchid_module.kicad_pcb")
_t = open(_p).read()
_t = _re.sub(r'\(layers ([^)"]+)\)',
             lambda mm: '(layers ' + ' '.join(f'"{tok}"' for tok in mm.group(1).split()) + ')',
             _t)
# zone wildcard layer -> explicit (KiCad 10 rejects "*.Cu")
_t = _t.replace('(layer "*.Cu")', '(layers "F.Cu" "B.Cu")')
open(_p, 'w').write(_t)
print("wildcard layers fixed")

print("U1 merged. Net -> real pins:")
for k, v in sorted(assigned.items()):
    print(f"  {k:9s}: {', '.join(v[:6])}{' ...' if len(v) > 6 else ''}")
