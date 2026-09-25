"""CLI helper: let nets named like negative rails parse as VALUES (#597).

Boards legitimately carry nets named -3V3 / -12V / -5V. Whether
``--power-nets -3V3 +1V1`` parses depends on the PYTHON VERSION's argparse:
3.14's negative-number matcher (``-\\.?\\d``, prefix match) already treats a
dash-digit token as a value, while 3.12's (``^-\\d+$|^-\\d*\\.\\d+$``)
classifies ``-3V3`` as an unknown option -- so the same recorded manifest
replays cleanly on a dev machine and dies with ``unrecognized arguments:
-3V3`` inside a 3.12 container (the eit_mux failure, every arm of the #584
sweep). Same lesson as the math.fsum incident: interpreter-version behavior
divergence, this time in argparse.

``pin_dash_digit_values(parser)`` pins the lenient behavior on every
version: any token starting with ``-<digit>`` is a value, never an option.
Safe because no option string in any front starts with a digit, and it can
only widen what parses (a former hard error). The GUI is unaffected -- it
passes net lists directly to the engine functions, no argparse involved.

Call it on every parser whose options accept net names, right before
``parse_args``. The private attribute is stable across CPython 3.8-3.14;
the hasattr guard makes a future rename degrade to the old behavior
instead of crashing.
"""
from __future__ import annotations

import re

_DASH_DIGIT = re.compile(r"^-\d")


def pin_dash_digit_values(parser):
    if hasattr(parser, "_negative_number_matcher"):
        parser._negative_number_matcher = _DASH_DIGIT
    return parser
