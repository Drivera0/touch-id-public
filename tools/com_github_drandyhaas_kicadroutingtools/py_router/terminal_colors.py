"""
ANSI color codes for terminal output.

Provides consistent color formatting across all scripts.

Colors are emitted only when the output can actually render them. A routing
run redirected to a log file (`route.py ... > step4_route.log`, every stress
worker, every CI capture) otherwise embeds thousands of raw `\033[93m` bytes
in the file, which breaks grep/diff on the logs for no benefit.

Resolution order (decided once, at import):

  1. ``NO_COLOR`` set (any value)     -> disabled  (https://no-color.org/)
  2. ``FORCE_COLOR``/``KICAD_FORCE_COLOR`` set -> enabled
  3. otherwise                        -> enabled iff stdout is a TTY

The GUI plugin needs case 2: its log pane *parses* these escapes and renders
real colors (`swig_gui._do_append_log`), but the engine writes through a
``StdoutRedirector``, not a terminal. ``kicad_routing_plugin/__init__.py``
sets ``KICAD_FORCE_COLOR`` so the GUI keeps its colored log.
"""

import os
import sys


def _color_enabled() -> bool:
    if os.environ.get('NO_COLOR') is not None:
        return False
    if os.environ.get('FORCE_COLOR') or os.environ.get('KICAD_FORCE_COLOR'):
        return True
    try:
        return bool(sys.stdout.isatty())
    except Exception:
        # A redirector without isatty() (or a closed stream): stay quiet rather
        # than stamp escapes into something that probably can't render them.
        return False


COLOR_ENABLED = _color_enabled()

# Standard ANSI color codes
RED = '\033[91m' if COLOR_ENABLED else ''
GREEN = '\033[92m' if COLOR_ENABLED else ''
YELLOW = '\033[93m' if COLOR_ENABLED else ''
RESET = '\033[0m' if COLOR_ENABLED else ''
