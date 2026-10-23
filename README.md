# VHDL-Lab

## 实验一：8 位双向数据总线

原设计为 `bus_trans.vhd`，实体 `bus_trans`。`S=00` 时 C→A，`S=01` 时 A→C，`S=10/11` 时 B→C。

### 安装依赖

Debian/Ubuntu 标准安装方式：

```bash
sudo apt-get update
sudo apt-get install ghdl gtkwave xvfb imagemagick python3-matplotlib
```

本次云环境使用 Debian 签名软件源下载软件包并在 `/workspace/tooling` 下解包，无需修改系统目录；GHDL 包装器位于 `/workspace/tooling/bin/ghdl`，运行脚本会自动识别。实际版本和安装命令记录见 `artifacts/tool_setup.log`。无需 Quartus、开发板、网络服务或凭据。

### 一键仿真与自动验证

```bash
cd /workspace/VHDL-Lab  # 或自己的仓库根目录
./scripts/run_sim.sh
```

要求 Python 3、matplotlib 和支持 VHDL-2008 的 GHDL。可用 `GHDL=/path/to/ghdl ./scripts/run_sim.sh` 指定编译器。

脚本依次执行分析、展开、运行仿真、VCD 解析复核、绘制真实波形；任一步失败均返回非零状态。构建中间文件放入临时目录并自动清理。失败时检查 `artifacts/simulation.log`；重新仿真会移除旧结果和旧截图，防止误用过期产物。

正常输出包含四项传输 PASS，以及七项高阻态、故意冲突和恢复检查 PASS；仿真在 100 ns 正常结束。Python 从实际 VCD 中再次核对 11 个采样点，生成 `artifacts/results.csv` 和 `artifacts/waveform_rendered.png`。

### 手动执行 GHDL

```bash
mkdir -p /tmp/vhdl-lab-work
ghdl -a --std=08 --workdir=/tmp/vhdl-lab-work bus_trans.vhd tb_bus_trans.vhd
ghdl -e --std=08 --workdir=/tmp/vhdl-lab-work tb_bus_trans
ghdl -r --std=08 --workdir=/tmp/vhdl-lab-work tb_bus_trans \
  --assert-level=error --vcd=artifacts/wave.vcd
```

### GTKWave 查看与真实截图

```bash
cd artifacts
gtkwave --save=wave.gtkw --rcfile=../scripts/gtkwaverc \
  --script=../scripts/gtkwave_view.tcl wave.vcd
```

保存的视图包含 S、A、B、C、a_drive、c_drive；S 按二进制显示，所有 8 位数据按十六进制显示，并缩放至整个 VCD 时间范围。

云端无桌面时，在允许本地 Unix socket 的执行环境运行：

```bash
python3 scripts/capture_gtkwave.py
```

该脚本使用 Xvfb、GTKWave 和 ImageMagick，截取真实窗口到 `artifacts/waveform_screenshot.png`，并关闭本次启动的进程。若沙箱禁止 X11 socket，可在获准的执行模式运行，或直接查看独立生成的 `waveform_rendered.png`；后者明确标记为 VCD 渲染图。

### 本次结果

- 编译、展开、运行全部成功；四种传输状态全部 PASS，合计 11/11 项检查通过。
- 原始设计无需修改；正常传输无 X，故意驱动冲突产生预期 X，并验证释放后恢复。
- [中文实验报告](artifacts/experiment_report.md)
- [真实 GTKWave 截图](artifacts/waveform_screenshot.png)
- [VCD 数字时序图](artifacts/waveform_rendered.png)
- [原始 VCD](artifacts/wave.vcd)、[仿真日志](artifacts/simulation.log)、[结果 CSV](artifacts/results.csv)
