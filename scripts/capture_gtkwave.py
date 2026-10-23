#!/usr/bin/env python3
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
local = Path('/workspace/tooling/gui/root/usr')
env = os.environ.copy()
if local.is_dir():
    env.update(GSETTINGS_SCHEMA_DIR=str(local / 'share/glib-2.0/schemas'),
               GSETTINGS_BACKEND='memory',
               LD_LIBRARY_PATH=str(local / 'lib/x86_64-linux-gnu') + ':' + env.get('LD_LIBRARY_PATH', ''))

def executable(name):
    path = shutil.which(name) or str(local / 'bin' / name)
    if not Path(path).is_file():
        raise FileNotFoundError(name)
    return path

for group in ('unidirectional', 'bidirectional'):
    out = root / 'artifacts' / group
    (out / 'waveform_screenshot.png').unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix='vhdl-gtk-') as tmp, (out / 'gtkwave.log').open('w') as log:
        env.update(XDG_CONFIG_HOME=tmp, XDG_CACHE_HOME=tmp)
        display = Path(tmp) / 'display'
        with display.open('w') as fd:
            server = subprocess.Popen([executable('Xvfb'), '-displayfd', str(fd.fileno()),
                '-screen', '0', '1800x450x24', '-nolisten', 'tcp'],
                pass_fds=(fd.fileno(),), stdout=log, stderr=log, env=env)
        viewer = None
        try:
            for _ in range(100):
                if display.read_text().strip():
                    break
                if server.poll() is not None:
                    raise RuntimeError(f'{group}: Xvfb failed')
                time.sleep(.05)
            env['DISPLAY'] = ':' + display.read_text().strip()
            if env['DISPLAY'] == ':':
                raise RuntimeError('Xvfb timed out')
            command = [executable('gtkwave'), '--save=wave.gtkw',
                       '--rcfile=' + str(root / 'scripts/gtkwaverc'),
                       '--script=' + str(root / 'scripts/gtkwave_view.tcl'), 'wave.vcd']
            log.write('Command: ' + ' '.join(command) + '\n')
            log.flush()
            viewer = subprocess.Popen(command, cwd=out, env=env, stdout=log, stderr=log)
            for _ in range(120):
                if viewer.poll() is not None:
                    raise RuntimeError(f'{group}: GTKWave exited')
                if 'GTKWave ready:' in (out / 'gtkwave.log').read_text():
                    break
                time.sleep(.1)
            else:
                raise RuntimeError('GTKWave timed out')
            time.sleep(1)
            subprocess.run([executable('import'), '-window', 'root', str(out / 'waveform_screenshot.png')],
                           check=True, env=env, stdout=log, stderr=log)
            print(f'{group}: captured actual GTKWave window with A B C S')
        finally:
            for process in (viewer, server):
                if process is not None and process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
