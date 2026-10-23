#!/usr/bin/env python3
"""Capture a real GTKWave window on an isolated Xvfb display."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

root = Path(__file__).resolve().parents[1]
out = root / 'artifacts'
(out / 'waveform_screenshot.png').unlink(missing_ok=True)
local = Path('/workspace/tooling/gui/root/usr')

def executable(name):
    path = shutil.which(name) or str(local / 'bin' / name)
    if not Path(path).is_file():
        raise FileNotFoundError(name)
    return path

env = os.environ.copy()
if local.is_dir():
    env['GSETTINGS_SCHEMA_DIR'] = str(local / 'share/glib-2.0/schemas')
    env['GSETTINGS_BACKEND'] = 'memory'
env['LD_LIBRARY_PATH'] = str(local / 'lib/x86_64-linux-gnu') + ':' + env.get('LD_LIBRARY_PATH', '')
with tempfile.TemporaryDirectory(prefix='vhdl-gtk-') as tmp, (out / 'gtkwave.log').open('w') as log:
    env['XDG_CONFIG_HOME'] = tmp
    env['XDG_CACHE_HOME'] = tmp
    # -displayfd selects an unused display; TCP listeners are disabled.
    display_file = Path(tmp) / 'display'
    with display_file.open('w') as fd:
        server = subprocess.Popen([executable('Xvfb'), '-displayfd', str(fd.fileno()),
            '-screen', '0', '1800x600x24', '-nolisten', 'tcp'],
            pass_fds=(fd.fileno(),), stdout=log, stderr=log, env=env)
    viewer = None
    try:
        for _ in range(100):
            if display_file.read_text().strip():
                break
            if server.poll() is not None:
                raise RuntimeError('Xvfb failed; see artifacts/gtkwave.log')
            time.sleep(.05)
        env['DISPLAY'] = ':' + display_file.read_text().strip()
        if env['DISPLAY'] == ':':
            raise RuntimeError('Xvfb display initialization timed out')
        command = [executable('gtkwave'), '--save=wave.gtkw', '--rcfile=../scripts/gtkwaverc', '--script=../scripts/gtkwave_view.tcl', 'wave.vcd']
        log.write('Command: ' + ' '.join(command) + '\n')
        log.flush()
        viewer = subprocess.Popen(command, cwd=out, env=env, stdout=log, stderr=log)
        for _ in range(120):
            if viewer.poll() is not None:
                raise RuntimeError('GTKWave exited; see artifacts/gtkwave.log')
            if 'GTKWave ready:' in (out / 'gtkwave.log').read_text():
                break
            time.sleep(.1)
        else:
            raise RuntimeError('GTKWave initialization timed out')
        time.sleep(1)
        subprocess.run([executable('import'), '-window', 'root', str(out / 'waveform_screenshot.png')],
                       check=True, env=env, stdout=log, stderr=log)
        print('Captured actual GTKWave/Xvfb display: artifacts/waveform_screenshot.png')
    finally:
        for proc in (viewer, server):
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
