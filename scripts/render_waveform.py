#!/usr/bin/env python3
import csv
import os
import re
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', '/tmp/vhdl-lab-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

root = Path(__file__).resolve().parents[1]
reports = []
for group, title in [('unidirectional', 'Experiment 1: unidirectional bus'),
                     ('bidirectional', 'Experiment 2: bidirectional bus')]:
    out = root / 'artifacts' / group
    text = (out / 'wave.vcd').read_text()
    scale = re.search(r'\$timescale\s+(\d+)\s*(fs|ps|ns)\s+\$end', text)
    unit = int(scale[1]) * {'fs': 1e-6, 'ps': 1e-3, 'ns': 1}[scale[2]]
    codes, data, widths = {}, {}, {}
    time = 0
    for line in text.splitlines():
        fields = line.split()
        if line.startswith('$var'):
            name = fields[4].split('[')[0].upper()
            assert name not in data and name in 'ABCS', 'Unexpected VCD signal'
            codes[fields[3]] = name
            widths[name] = int(fields[2])
            data[name] = []
        elif line.startswith('#'):
            time = int(line[1:]) * unit
        elif line.startswith(('b', 'B')):
            bits, code = fields[0][1:].upper(), fields[1]
            history = data[codes[code]]
            if history and history[-1][0] == time:
                history[-1] = (time, bits)
            else:
                history.append((time, bits))
    assert set(data) == set('ABCS') and widths == {'A': 8, 'B': 8, 'C': 8, 'S': 2}
    assert time == 80, f'Incomplete VCD: {time} ns'
    log = (out / 'simulation.log').read_text()
    assert re.findall(r'PASS\|(route_\d\d)', log) == ['route_00', 'route_01', 'route_10', 'route_11']
    assert 'SUMMARY|4 routing checks passed; completed at 80 ns' in log
    assert 'GHDL_EXIT_STATUS=0' in log and 'FAIL|' not in log

    def display(bits, key):
        if set(bits) <= {'0', '1'}:
            return bits if key == 'S' else f'{int(bits, 2):02X}'
        return bits[0] * 2 if len(set(bits)) == 1 else bits

    def sample(key, ns):
        return display([bits for t, bits in data[key] if t <= ns][-1], key)

    rows = []
    for index, expected in enumerate(['3C', 'A5', '5A', 'F0']):
        ns = 5 + 20 * index
        actual = {key: sample(key, ns) for key in 'ABCS'}
        destination = 'A' if group == 'bidirectional' and index == 0 else 'C'
        source = 'C' if destination == 'A' else 'A' if index < 2 else 'B'
        assert actual['S'] == f'{index:02b}' and actual[destination] == actual[source] == expected
        rows.append({'time_ns': ns, **actual, 'direction': f'{source}->{destination}',
                     'expected': expected, 'actual': actual[destination], 'result': 'PASS'})
    with (out / 'results.csv').open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    fig, ax = plt.subplots(figsize=(15, 4.6))
    for i, key in enumerate('ABCS'):
        y = 3 - i
        history = data[key]
        for j, (start, bits) in enumerate(history):
            stop = history[j+1][0] if j+1 < len(history) else 80
            if stop <= start:
                continue
            value = display(bits, key)
            if 'Z' in bits:
                ax.plot([start, stop], [y, y], '--', color='#8693a4')
            else:
                d = min(.25, (stop-start)/4)
                ax.add_patch(Polygon([(start,y),(start+d,y+.24),(stop-d,y+.24),
                                      (stop,y),(stop-d,y-.24),(start+d,y-.24)],
                                     facecolor='#e6f3fc', edgecolor='#166b91', linewidth=1.3))
            if stop-start >= 1.5:
                ax.text((start+stop)/2, y, value, ha='center', va='center', fontsize=12,
                        color='#166b91', bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': .2})
    ax.set_yticks([3,2,1,0], ['A [7:0]', 'B [7:0]', 'C [7:0]', 'S [1:0]'])
    ax.set_xlim(0,80)
    ax.set_ylim(-.5,3.5)
    ax.set_xticks(range(0,81,5))
    ax.set_xlabel('Time (ns)')
    ax.set_title(title + ' | Actual VCD data', fontsize=16, pad=15)
    ax.grid(axis='x', color='#e5eaf0')
    ax.spines[['left','right','top']].set_visible(False)
    fig.tight_layout()
    fig.savefig(out / 'waveform_rendered.png', dpi=160)
    plt.close(fig)
    reports.append((group, rows))
    print(f'{group}: 4/4 routing assertions and VCD samples PASS; A B C S; 0-80 ns')

report = '''# 8 位数据总线功能仿真实验

## 实验目标

分别设计并仿真单向总线和双向总线，验证控制信号 S 的四种状态下的数据传输。每组仅进行四项数据传输测试，时间范围均为 0–80 ns，波形由上到下只显示 A、B、C、S。

## 设计与测试方案

第一组 `bus_trans_unidirectional.vhd`：A、B 为 8 位输入，C 为 8 位输出；S=00/01 时 A→C，S=10/11 时 B→C。

第二组 `bus_trans.vhd`：A、C 为 8 位双向端口，B 为 8 位输入；S=00 时 C→A，S=01 时 A→C，S=10/11 时 B→C。保留原来的传输逻辑，仅精简代码格式并删除注释。

| 名义区间 | S | 第一组输入 → 预期输出 | 第二组输入 → 预期输出 |
| --- | --- | --- | --- |
| 0–20 ns | 00 | A=3C → C=3C | C=3C → A=3C |
| 20–40 ns | 01 | A=A5 → C=A5 | A=A5 → C=A5 |
| 40–60 ns | 10 | B=5A → C=5A | B=5A → C=5A |
| 60–80 ns | 11 | B=F0 → C=F0 | B=F0 → C=F0 |

两个独立 Testbench 均在 5、25、45、65 ns 断言检查输出。双向总线在 20 ns 释放外部驱动，21 ns 切换 S，22 ns 设置 A；40 ns 释放 A，41 ns 切换 S，42 ns 设置 B。这些交接间隔保证数据稳定后再检查，不安排独立的高阻态或冲突测试。双向端口未被驱动时自然显示 ZZ，内部驱动信号不导出到 VCD、不加入图中。

## 实际结果与波形

以下表格直接从本次 GHDL 生成的 VCD 中采样，PASS 同时要求 GHDL 正常退出、对应 VHDL 断言通过、VCD 采样与预期一致。A/B/C 为 8 位十六进制，S 为二进制。
'''
for index, (group, rows) in enumerate(reports, 1):
    label = '单向总线' if index == 1 else '双向总线'
    report += f'\n### 第一组：{label}\n' if index == 1 else f'\n### 第二组：{label}\n'
    report += '\n| 采样/ns | A | B | C | S | 方向 | 预期输出 | 实际输出 | 结果 |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n'
    for r in rows:
        report += '| ' + ' | '.join(str(r[k]) for k in ['time_ns','A','B','C','S','direction','expected','actual','result']) + ' |\n'
    report += f'\nGTKWave 真实窗口截图：\n\n![{label} GTKWave 截图]({group}/waveform_screenshot.png)\n'
    report += f'\n真实 VCD 的 Python 渲染图：\n\n![{label} VCD 渲染图]({group}/waveform_rendered.png)\n'
report += '''
## 结论与复现

两组均完成 GHDL 分析、展开及 0–80 ns 仿真，每组四项数据传输断言全部 PASS，合计 8/8；对应 VCD 采样也全部通过。VCD 和两种波形图片均只包含 A、B、C、S。原双向总线在实验要求的四种合法选择状态下无需逻辑修复。

在仓库根目录执行：

```bash
./scripts/run_sim.sh
python3 scripts/capture_gtkwave.py
```

每组结果分别保存在 `unidirectional/` 和 `bidirectional/`：`simulation.log` 记录实际命令和断言输出，`wave.vcd` 保留实际事件，`results.csv` 记录采样值，`wave.gtkw` 保存 ABCS 视图，`gtkwave.log` 记录 GUI 载入，`waveform_screenshot.png` 是实际 GTKWave 截图，`waveform_rendered.png` 是 Python 解析 VCD 绘制的时序图。工具版本与安装方法见 `tool_setup.log`。
'''
(root / 'artifacts/experiment_report.md').write_text(report)
