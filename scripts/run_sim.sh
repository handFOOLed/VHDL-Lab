#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/vhdl-lab-matplotlib}"
GHDL="${GHDL:-ghdl}"
if ! command -v "$GHDL" >/dev/null 2>&1; then
    GHDL=/workspace/tooling/bin/ghdl
fi
build=$(mktemp -d /tmp/vhdl-lab.XXXXXX)
trap 'rm -rf "$build"' EXIT
for group in unidirectional bidirectional; do
    top=tb_bus_trans
    design=bus_trans
    if [[ "$group" == unidirectional ]]; then
        top=tb_bus_trans_unidirectional
        design=bus_trans_unidirectional
    fi
    out="artifacts/$group"
    mkdir -p "$out"
    rm -f "$out"/{wave.vcd,results.csv,waveform_rendered.png,waveform_screenshot.png,gtkwave.log}
    (
        set -x
        "$GHDL" --version
        "$GHDL" -a --std=08 --workdir="$build" "$design.vhd" "$top.vhd"
        "$GHDL" -e --std=08 --workdir="$build" "$top"
        "$GHDL" -r --std=08 --workdir="$build" "$top" --assert-level=error --read-wave-opt="scripts/$group.opt" --vcd="$out/wave.vcd"
        echo GHDL_EXIT_STATUS=0
    ) >"$out/simulation.log" 2>&1
    cat "$out/simulation.log"
    printf '[dumpfile] "wave.vcd"\n[size] 1800 450\n[signals_width] 340\n@22\n%s.a[7:0]\n%s.b[7:0]\n%s.c[7:0]\n@28\n%s.s[1:0]\n' "$top" "$top" "$top" "$top" >"$out/wave.gtkw"
done
python3 scripts/render_waveform.py
