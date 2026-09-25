#!/bin/bash
# install_kicad_cli.sh -- user-space KiCad 10 kicad-cli in the agent sandbox.
#
# The handover said "kicad-cli is not available in the agent sandbox" and it
# was right about apt (no root) -- but the KiCad PPA is REACHABLE, apt runs
# fine with user-owned state dirs, and dpkg -x needs no root at all. This
# script rebuilds the working setup from 2026-08-31 (KiCad 10.0.6, jammy).
# It plotted the v7 fab package; verify_gerbers + verify_handoff both passed.
#
# Result: /tmp/k10/usr/bin/kicad-cli   (run with the LD_LIBRARY_PATH below)
#
# Usage:  bash install_kicad_cli.sh
#         export LD_LIBRARY_PATH=/tmp/k10/usr/lib/x86_64-linux-gnu:/tmp/k10/usr/lib
#         /tmp/k10/usr/bin/kicad-cli version
#
# Plot flags that produced the verified v7 package (from cad/pcb-v3):
#   kicad-cli pcb export gerbers -o OUT/ \
#     --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,B.Paste,Edge.Cuts \
#     --subtract-soldermask --no-protel-ext --use-drill-file-origin BOARD.kicad_pcb
#   kicad-cli pcb export drill -o OUT/ --format excellon --excellon-separate-th \
#     --drill-origin plot --generate-map --map-format gerberx2 BOARD.kicad_pcb
# --use-drill-file-origin / --drill-origin plot matter: the board's
# aux_axis_origin is (-10, 9.5) = the bottom-left corner, which puts the
# gerbers in the SAME corner-based space as make_bom_cpl.py's CPL. Without
# them the gerbers come out centred and verify_handoff correctly fails 24
# placements outside the outline. --no-protel-ext matters too: the verifiers
# glob for *.gbr.
set -e
mkdir -p /tmp/apt/{state/lists/partial,cache/archives/partial,etc} /tmp/debs10 /tmp/k10
cat > /tmp/apt/etc/sources.list <<'EOF'
deb [trusted=yes] https://ppa.launchpadcontent.net/kicad/kicad-10.0-releases/ubuntu jammy main
deb [trusted=yes] http://archive.ubuntu.com/ubuntu jammy main universe
deb [trusted=yes] http://archive.ubuntu.com/ubuntu jammy-updates main universe
EOF
A="-o Dir::State=/tmp/apt/state -o Dir::Cache=/tmp/apt/cache \
   -o Dir::Etc::sourcelist=/tmp/apt/etc/sources.list -o Dir::Etc::sourceparts=/dev/null \
   -o APT::Get::AllowUnauthenticated=true"
apt-get $A update >/dev/null 2>&1 || true
cd /tmp/debs10
apt-get $A download kicad \
  libgtk-3-0 libwxbase3.2-1 libwxgtk3.2-1 libwxgtk-gl3.2-1 \
  libxdamage1 libnotify4 \
  libocct-foundation-7.6 libocct-modeling-data-7.6 libocct-modeling-algorithms-7.6 \
  libocct-data-exchange-7.6 libocct-ocaf-7.6 libocct-visualization-7.6 \
  libglew2.2 libglu1-mesa libgit2-1.1 libtbb2 libtbbmalloc2 libtbb12 \
  libssh2-1 libmbedtls14 libmbedcrypto7 libmbedx509-1 libhttp-parser2.9 \
  libfreeimage3 libopengl0 libraw20 \
  libnng1 libprotobuf23 libsecret-1-0 libspnav0 libpoppler-glib8 2>&1 | tail -1
for f in *.deb; do dpkg -x "$f" /tmp/k10; done
export LD_LIBRARY_PATH=/tmp/k10/usr/lib/x86_64-linux-gnu:/tmp/k10/usr/lib
/tmp/k10/usr/bin/kicad-cli version
echo "OK -- remember: export LD_LIBRARY_PATH=/tmp/k10/usr/lib/x86_64-linux-gnu:/tmp/k10/usr/lib"
