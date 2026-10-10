#!/usr/bin/env python3
"""Launch LightBurn under wine; dismiss the modal code-46 dialog once; fast-poll for the
<untitled> main window and grab it immediately (the app exits ~1s after showing it).
Usage: cap4.py <exe_path> <out_main.png> [label]
"""
import sys, subprocess, time, os
from PIL import ImageGrab
import numpy as np

WINE = "/var/home/Dcs102/.local/share/Steam/steamapps/common/Proton - Experimental/files/bin/wine"
EXE, OUT = sys.argv[1], sys.argv[2]
LABEL = sys.argv[3] if len(sys.argv) > 3 else 'main'

env = dict(os.environ)
env.update({
    'WINEPREFIX': '/var/home/Dcs102/lightburn/work/native/prefix',
    'DISPLAY': ':0', 'XAUTHORITY': '/run/user/1000/xauth_smhqjo', 'WINEDEBUG': '-all',
})
os.environ.update({'DISPLAY': ':0', 'XAUTHORITY': '/run/user/1000/xauth_smhqjo'})


def wins():
    r = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
    out = []
    for l in r.stdout.splitlines():
        p = l.split(None, 2)
        if len(p) >= 3:
            out.append((p[0], p[2]))
    return out


def find(sub):
    for wid, t in wins():
        if sub.lower() in t.lower():
            return (wid, t)
    return None


def grab(wid):
    g = subprocess.run(['xdotool', 'getwindowgeometry', '--shell', wid], capture_output=True, text=True).stdout
    geo = dict(l.strip().split('=', 1) for l in g.splitlines() if '=' in l)
    x, y, w, h = int(geo['X']), int(geo['Y']), int(geo['WIDTH']), int(geo['HEIGHT'])
    img = ImageGrab.grab()
    SW, SH = img.size
    crop = img.crop((max(0, x), max(0, y), min(SW, x + w), min(SH, y + h)))
    return crop


logf = open('cap4.log', 'w')
proc = subprocess.Popen([WINE, EXE], env=env, stdout=logf, stderr=subprocess.STDOUT,
                        stdin=subprocess.DEVNULL, start_new_session=True)
print("launched", proc.pid, flush=True)

t0 = time.time()
dismissed = 0
while time.time() - t0 < 120:
    time.sleep(0.5)
    t = int(time.time() - t0)
    main = find('<untitled>')
    if main:
        crop = grab(main[0])
        gray = np.array(crop.convert('L'))
        crop.save(OUT)
        print(f"t={t}s SAVED {OUT} size={crop.size} litpx={int((gray > 10).sum())} mean={gray.mean():.1f}", flush=True)
        print("windows at capture:", wins(), flush=True)
        print("RESULT: CAPTURED", flush=True)
        break
    d = find('License System Error')
    if d and dismissed < 3:
        subprocess.run(['xdotool', 'windowactivate', '--sync', d[0]], stderr=subprocess.DEVNULL)
        time.sleep(0.2)
        subprocess.run(['xdotool', 'key', '--window', d[0], 'Return'], stderr=subprocess.DEVNULL)
        dismissed += 1
        print(f"t={t}s dismissed code-46 dialog #{dismissed}", flush=True)
    if proc.poll() is not None and t > 20:
        print(f"t={t}s PROCESS EXITED (no main window seen)", flush=True)
        break
print("RESULT:", "done", flush=True)
