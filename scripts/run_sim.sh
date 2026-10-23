#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/vhdl-lab-matplotlib}"
GHDL="${GHDL:-ghdl}"
if ! command -v "$GHDL" >/dev/null 2>&1 && [[ -x /workspace/tooling/bin/ghdl ]]; then
    GHDL=/workspace/tooling/bin/ghdl
fi
mkdir -p artifacts
build_dir=$(mktemp -d /tmp/vhdl-lab.XXXXXX)
trap 'rm -rf "$build_dir"' EXIT
# Never let old outputs masquerade as results of a failed new simulation.
rm -f artifacts/wave.vcd artifacts/results.csv artifacts/waveform_rendered.png artifacts/waveform_screenshot.png
{
    set -x
    "$GHDL" --version
    "$GHDL" -a --std=08 --workdir="$build_dir" bus_trans.vhd tb_bus_trans.vhd
    "$GHDL" -e --std=08 --workdir="$build_dir" tb_bus_trans
    "$GHDL" -r --std=08 --workdir="$build_dir" tb_bus_trans --assert-level=error --vcd=artifacts/wave.vcd
} >artifacts/simulation.log 2>&1
set +x
cat artifacts/simulation.log
python3 scripts/render_waveform.py
