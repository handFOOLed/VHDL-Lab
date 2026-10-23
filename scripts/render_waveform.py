#!/usr/bin/env python3
"""Parse actual GHDL VCD events, cross-check samples, and render bus timing."""
import bisect
import csv
import os
from pathlib import Path
import re

os.environ.setdefault('MPLCONFIGDIR', '/tmp/vhdl-lab-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts'
text = (OUT / 'wave.vcd').read_text()
match = re.search(r'\$timescale\s+(\d+)\s*(fs|ps|ns|us|ms|s)\s+\$end', text)
if not match:
    raise ValueError('Missing VCD timescale')
scale_ns = int(match[1]) * {'fs': 1e-6, 'ps': 1e-3, 'ns': 1, 'us': 1e3, 'ms': 1e6, 's': 1e9}[match[2]]
scopes, codes, events = [], {}, {}
time = 0
for line in text.splitlines():
    fields = line.split()
    if not fields:
        continue
    if fields[0] == '$scope':
        scopes.append(fields[2])
    elif fields[0] == '$upscope':
        scopes.pop()
    elif fields[0] == '$var':
        name = '.'.join(scopes + [fields[4]])
        codes[fields[3]] = name
        events[name] = []
    elif line.startswith('#'):
        time = int(line[1:])
    elif line[0] in 'bB':
        bits, code = fields[0][1:].upper(), fields[1]
        if code in codes:
            history = events[codes[code]]
            if history and history[-1][0] == time:
                history[-1] = (time, bits)
            else:
                history.append((time, bits))
log = (OUT / 'simulation.log').read_text()
completion = re.search(r'simulation finished @(\d+)ns', log)
assert completion, 'Simulation did not finish normally'
end_ns = int(completion[1])
assert 97 <= time * scale_ns <= end_ns == 100, 'Incomplete simulation'
# GHDL omits a final VCD timestamp if no signals change before finish.
# Values after the last event hold through the logged completion time.
names = {'S': 's[1:0]', 'A': 'a[7:0]', 'B': 'b[7:0]', 'C': 'c[7:0]',
         'A drive': 'a_drive[7:0]', 'C drive': 'c_drive[7:0]'}
data = {key: [(t * scale_ns, bits) for t, bits in events['tb_bus_trans.' + name]]
        for key, name in names.items()}

# The only X events must belong to the deliberate contention tests after 80 ns.
assert all('X' not in bits for history in data.values() for ns, bits in history if ns < 80), 'Unexpected X in normal routing'

def sample(key, ns):
    history = data[key]
    index = bisect.bisect_right([t for t, _ in history], ns) - 1
    assert index >= 0
    return history[index][1]

def display(bits, binary=False):
    if set(bits) <= {'0', '1'}:
        return bits if binary else f'{int(bits, 2):02X}'
    if len(set(bits)) == 1:
        return bits[0] * (2 if len(bits) == 8 else len(bits))
    return bits

checks = [
    ('route_00', 5, {'S': '00', 'A': '3C', 'C': '3C', 'A drive': 'ZZ'}),
    ('route_01', 25, {'S': '01', 'A': 'A5', 'C': 'A5', 'C drive': 'ZZ'}),
    ('route_10', 45, {'S': '10', 'A': 'ZZ', 'C': '5A', 'B': '5A'}),
    ('route_11', 65, {'S': '11', 'A': 'ZZ', 'C': 'F0', 'B': 'F0'}),
    ('release_00', 83, {'S': '00', 'A': 'ZZ', 'C': 'ZZ'}),
    ('release_01', 85, {'S': '01', 'A': 'ZZ', 'C': 'ZZ'}),
    ('conflict_00', 87, {'S': '00', 'A': 'XX', 'C': 'FF'}),
    ('recovery_00', 89, {'A': 'FF', 'C': 'FF'}),
    ('conflict_01', 93, {'S': '01', 'A': 'A5', 'C': 'XX'}),
    ('recovery_01', 95, {'A': 'A5', 'C': 'A5'}),
    ('release_final', 97, {'A': 'ZZ', 'C': 'ZZ'}),
]
log = (OUT / 'simulation.log').read_text()
assert re.findall(r'PASS\|([a-z0-9_]+)', log) == [name for name, _, _ in checks]
assert 'simulation finished @100ns' in log and 'FAIL|' not in log
rows = []
for name, ns, expected in checks:
    actual = {key: display(sample(key, ns), key == 'S') for key in names}
    for key, value in expected.items():
        assert actual[key] == value, (name, key, value, actual[key])
    rows.append({'check': name, 'time_ns': ns, **actual,
                 'expected': '; '.join(f'{k}={v}' for k, v in expected.items()), 'result': 'PASS'})
with (OUT / 'results.csv').open('w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

fig, axes = plt.subplots(2, 1, figsize=(17, 9), gridspec_kw={'height_ratios': [1, 1]})
fig.patch.set_facecolor('#f5f7fb')
fig.suptitle('8-bit bidirectional bus | Actual GHDL VCD simulation', fontsize=20, weight='bold', y=.98)
for ax, left, right, title in zip(axes, [0, 80], [80, 100],
        ['Routing tests: 0-80 ns (driver release and settling gaps included)',
         'Release, intentional contention, and recovery: 80-100 ns']):
    ax.set_facecolor('white')
    for index, key in enumerate(names):
        y = 5 - index
        history = data[key]
        for j, (start, bits) in enumerate(history):
            stop = history[j + 1][0] if j + 1 < len(history) else end_ns
            lo, hi = max(left, start), min(right, stop)
            if hi <= lo:
                continue
            value = display(bits, key == 'S')
            z = 'Z' in bits
            x = 'X' in bits
            color = '#d1495b' if x else '#8795a5' if z else '#166b91'
            fill = '#ffe4e9' if x else '#eef1f5' if z else '#e3f3fb'
            dx = min((right - left) * .003, (hi - lo) / 4)
            if z:
                ax.plot([lo, hi], [y, y], color=color, lw=1.4, linestyle='--')
            else:
                ax.add_patch(Polygon([(lo, y), (lo+dx, y+.27), (hi-dx, y+.27),
                                      (hi, y), (hi-dx, y-.27), (lo+dx, y-.27)],
                                     facecolor=fill, edgecolor=color, linewidth=1.2))
            if hi - lo >= (right-left) * .018:
                ax.text((lo+hi)/2, y, value, ha='center', va='center', fontsize=10,
                        color=color, weight='bold', bbox={'facecolor': fill, 'edgecolor': 'none', 'pad': .3})
    for ns in [t for _, t, _ in checks if left < t < right]:
        ax.axvline(ns, color='#b7c3ce', lw=.7, alpha=.5, zorder=0)
    ax.set_yticks(range(5, -1, -1), [k + (' [1:0]' if k == 'S' else ' [7:0]') for k in names])
    ax.set_xlim(left, right)
    ax.set_ylim(-.65, 5.65)
    ax.set_xticks(list(range(left, right+1, 5 if left == 0 else 1)))
    ax.set_xlabel('Time (ns)')
    ax.set_title(title, loc='left', fontsize=12, pad=12)
    ax.grid(axis='x', color='#e7ebef', lw=.7)
    ax.spines[['top', 'right', 'left']].set_visible(False)
fig.text(.1, .017, 'Data: hexadecimal | S: binary | ZZ: high impedance | XX: intentional conflict | '
         '11/11 assertions + VCD samples PASS\nSource: artifacts/wave.vcd; Python rendering of recorded events, not a GTKWave screenshot.',
         fontsize=10, color='#475569')
fig.tight_layout(rect=[.02, .065, .99, .94], h_pad=2)
fig.savefig(OUT / 'waveform_rendered.png', dpi=160)
print(f'VCD verified: {len(rows)}/11 samples PASS; rendered {end_ns:g} ns to artifacts/waveform_rendered.png')
