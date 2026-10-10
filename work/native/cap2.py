#!/usr/bin/env python3
"""Launch a LightBurn exe under wine, dismiss ALL 'License System Error' (code-46) dialogs,
wait for the <untitled> main window, capture it, and list every window present.
Usage: cap2.py <exe_path> <out_main.png> [label]
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
os.environ.update({'DISPLAY': ':0', 'XAUTHORITY': '/run/user/1000/xauth_smhqjo'})

exe, out_main = sys.argv[1], sys.argv[2]
label = sys.argv[3] if len(sys.argv) > 3 else 'main'


def all_windows():
    out = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True).stdout
    res = []
    for line in out.splitlines():
        p = line.split(None, 2)
        if len(p) >= 3:
            res.append((p[0], p[2]))
    return res


def find(title_sub):
    for wid, title in all_windows():
        if title_sub.lower() in title.lower():
            return (wid, title)
    return None


logf = open('cap2.log', 'w')
proc = subprocess.Popen([WINE, exe], env=ENV, stdout=logf, stderr=subprocess.STDOUT,
                        stdin=subprocess.DEVNULL, start_new_session=True)
print("launched", proc.pid)

# dismiss every code-46 dialog that appears (loop until none for a few seconds)
dismissed = 0
clean_streak = 0
for _ in range(120):
    time.sleep(0.5)
    d = find('License System Error')
    if d:
        clean_streak = 0
        subprocess.run(['xdotool', 'windowactivate', '--sync', d[0]], stderr=subprocess.DEVNULL)
        time.sleep(0.6)
        subprocess.run(['xdotool', 'key', '--window', d[0], 'Return'], stderr=subprocess.DEVNULL)
        dismissed += 1
    else:
        clean_streak += 1
        if clean_streak >= 4 and find('<untitled>'):
            break

# wait for main window
main = None
for _ in range(60):
    time.sleep(0.4)
    m = find('<untitled>')
    if m:
        main = m
        break
if not main:
    print("MAIN WINDOW NEVER APPEARED; windows now:", all_windows())
    sys.exit(2)
print(f"main window: {main[0]}  title={main[1]!r}  (dismissed {dismissed} code-46 dialogs)")

# capture the main window bbox
g = subprocess.run(['xdotool', 'getwindowgeometry', '--shell', main[0]],
                   capture_output=True, text=True).stdout
geo = dict(l.strip().split('=', 1) for l in g.splitlines() if '=' in l)
x, y, w, h = int(geo['X']), int(geo['Y']), int(geo['WIDTH']), int(geo['HEIGHT'])
img = ImageGrab.grab()
SW, SH = img.size
x0, y0 = max(0, x), max(0, y)
x1, y1 = min(SW, x + w), min(SH, y + h)
crop = img.crop((x0, y0, x1, y1))
gray = np.array(crop.convert('L'))
crop.save(out_main)
print(f"SAVED {out_main} size={crop.size} litpx={int((gray > 10).sum())} mean={gray.mean():.1f}")
print("windows at capture:", all_windows())
