# VHDL-Lab

两组 8 位总线实验，每组只测试 S 的四种状态，波形从上到下仅显示 **A、B、C、S**。VHDL 源码与测试代码均已精简，无注释。

| S | 第一组：单向总线 | 第二组：双向总线 |
| --- | --- | --- |
| 00 | A → C，3C | C → A，3C |
| 01 | A → C，A5 | A → C，A5 |
| 10 | B → C，5A | B → C，5A |
| 11 | B → C，F0 | B → C，F0 |

第一组设计为 `bus_trans_unidirectional.vhd`，测试为 `tb_bus_trans_unidirectional.vhd`；第二组设计为 `bus_trans.vhd`，测试为 `tb_bus_trans.vhd`。两组仿真均覆盖 0–80 ns，分别在 5、25、45、65 ns 自动断言检查。

## 运行

Debian/Ubuntu 安装依赖：

```bash
sudo apt-get update
sudo apt-get install ghdl gtkwave xvfb imagemagick python3-matplotlib
```

在仓库根目录运行：

```bash
./scripts/run_sim.sh
python3 scripts/capture_gtkwave.py
```

第一条命令执行两组 GHDL 仿真、VCD 采样验证，生成时序图、结果表与报告。第二条用 Xvfb 打开 GTKWave 并实际截取窗口；需允许本机 Unix socket。云环境已安装的 `/workspace/tooling/bin/ghdl` 会被自动识别，也可通过 `GHDL=/path/to/ghdl` 指定。每次仿真会清理旧结果及截图，重新仿真后需要重新截屏。

手动查看第一组波形（第二组将目录改为 `artifacts/bidirectional`）：

```bash
cd artifacts/unidirectional
gtkwave --save=wave.gtkw --rcfile=../../scripts/gtkwaverc \
  --script=../../scripts/gtkwave_view.tcl wave.vcd
```

## 结果

- 第一组：4/4 PASS；[GTKWave 截图](artifacts/unidirectional/waveform_screenshot.png) · [VCD 渲染图](artifacts/unidirectional/waveform_rendered.png)
- 第二组：4/4 PASS；[GTKWave 截图](artifacts/bidirectional/waveform_screenshot.png) · [VCD 渲染图](artifacts/bidirectional/waveform_rendered.png)
- [中文实验报告](artifacts/experiment_report.md)

每组目录包含 `wave.vcd`、`wave.gtkw`、`simulation.log`、`results.csv`、`gtkwave.log` 和两张 PNG。VCD 本身也只导出 A、B、C、S。实际工具安装方法及版本见 [tool_setup.log](artifacts/tool_setup.log)。
