#!/bin/bash
# Drive the OpenLane RTL->GDS flow for the hand-built CPU.
cd "$HOME/OpenLane" || exit 1
IMG=ghcr.io/the-openroad-project/openlane:ff5509f65b17bfa4068d5336495ab1718987ff69-amd64
docker run --rm \
  -v "$HOME/OpenLane":/openlane \
  -v "$HOME":"$HOME" \
  -e PDK_ROOT="$HOME/.ciel" \
  -e PDK=sky130A \
  -e STD_CELL_LIBRARY=sky130_fd_sc_hd \
  "$IMG" \
  ./flow.tcl -design cpu -tag run1 -overwrite -pdk sky130A
echo "FLOW_EXIT=$?"
