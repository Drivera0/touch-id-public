# KiCad Routing Tools - SWIG Action Plugin package

# The GUI log pane parses ANSI escapes and renders them as real colors
# (swig_gui._do_append_log), but the engine prints through a StdoutRedirector,
# which is not a TTY -- so terminal_colors would suppress color. Opt in here:
# this package __init__ runs before any submodule body (the GUI modules use
# relative imports), hence before the engine modules import terminal_colors.
import os as _os
_os.environ.setdefault('KICAD_FORCE_COLOR', '1')
