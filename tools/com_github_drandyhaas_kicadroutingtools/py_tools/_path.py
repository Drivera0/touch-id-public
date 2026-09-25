"""Path bootstrap for the standalone tools (#522 layout).

The engine modules these tools import (kicad_parser, routing_defaults, ...)
live in ../py_router. Import this FIRST in every py_tools script:

    import _path  # noqa: F401

Running `python3 py_tools/<tool>.py` puts py_tools/ at sys.path[0], so this
module always resolves; it then makes the engine importable flat.
"""
import os
import sys

_ENGINE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'py_router'))
if _ENGINE not in sys.path:
    sys.path.insert(0, _ENGINE)
