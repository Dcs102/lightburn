#!/usr/bin/env python3
"""Launch a LightBurn exe under wine, dismiss the code-46 dialog, and rapidly
capture the main window (mouse-oscillation + grab loop) before it exits.
Usage: cap_launch.py <exe_path> <out_main.png> [label]
"""
import sys, subprocess, time, os
from PIL import ImageGrab
import numpy as np

WINE = "/var/home/Dcs102/.local/share/Steam/steamapps/common/Proton - Experimental/files/bin/wine"
ENV = dict(os.environ)
ENV['WINEPREFIX'] = '/var/home/Dcs102/lightburn/work/native/prefix'
ENV['DISPLAY'] = ':0'
ENV['XAUTHORITY'] = '/run/user/1000/xauth_smhqjo'
ENV['WINEDEBUG'] = '-all'

exe = sys.argv[1]
out_main = sys.argv[2]
label = sys.argv[3] if len(sys.argv) > 3 else 'main'

def windows():
    out = subprocess.run(['wmctrl', '-lG'], capture_output=True, text=True).stdout
    res = []
    for line in out.splitlines():
        p = line.split(None, 6)
        if len(p) >= 6 and 'ightBurn' in (p[6] if len(p) > 6 else ''):
            res.append((p[0], int(p[2]), int(p[3]), int(p[4]), int(p[5]), p[6] if len(p) > 6 else ''))
    return res

def find(title_sub):
    for w in windows():
        if title_sub.lower() in w[5].lower():
            return w
    return None

# launch
logf = open('cap_launch.log', 'w')
proc = subprocess.Popen([WINE, exe], env=ENV, stdout=logf, stderr=subprocess.STDOUT,
                        stdin=subprocess.DEVNULL, start_new_session=True)
print("launched", proc.pid)

# wait for code-46 dialog, dismiss it (may appear once)
dlg_wid = None
for _ in range(120):  # up to 60s
    time.sleep(0.5)
    d = find('License System Error')
    if d:
        dlg_wid = d[0]
        subprocess.run(['xdotool', 'windowactivate', '--sync', dlg_wid], stderr=subprocess.DEVNULL)
        time.sleep(0.8)
        subprocess.run(['xdotool', 'key', '--window', dlg_wid, 'Return'], stderr=subprocess.DEVNULL)
        print("dismissed dialog", dlg_wid)
        break

# wait for main window (<untitled> - LightBurn)
main = None
for _ in range(60):  # up to 30s
    time.sleep(0.4)
    m = find('<untitled>')
    if m:
        main = m
        break
if not main:
    print("MAIN WINDOW NEVER APPEARED; windows now:", windows())
    sys.exit(2)
print("main window:", main[0], main[5])

# rapid capture loop over the main window bbox
x, y, w, h = main[1], main[2], main[3], main[4]
cx, cy = x + w // 2, y + h // 2
img = ImageGrab.grab(); SW, SH = img.size
best, bestscore = None, -1
for i in range(60):
    dx = (i % 7) * 40 - 120
    dy = (i % 5) * 25 - 50
    subprocess.run(['xdotool', 'mousemove', str(cx + dx), str(cy + dy)], stderr=subprocess.DEVNULL)
    time.sleep(0.04)
    f = ImageGrab.grab()
    g = np.array(f.convert('L'))
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(SW, x + w), min(SH, y + h)
    if x1 <= x0 or y1 <= y0:
        continue
    crop = g[y0:y1, x0:x1]
    score = int(crop[crop > 10].size)
    if score > bestscore:
        bestscore = score
        best = f.crop((x0, y0, x1, y1))
if best is None or bestscore < 500:
    print("capture failed (bestscore=%s)" % bestscore); sys.exit(3)
bg = np.array(best.convert('L'))
best.save(out_main)
print(f"SAVED {out_main} size={best.size} litpx={bestscore} mean={bg.mean():.1f} nz={(bg>10).mean():.3f}")
# also record all windows present at capture time (evidence of no License Page for cracked)
print("windows at capture:", [(w[0], w[5]) for w in windows()])
