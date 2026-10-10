#!/usr/bin/env python3
"""Move each LightBurn window to a known spot, full-screen capture, crop + RapidOCR."""
import sys, subprocess, os, glob, time
from PIL import Image

ENV = dict(os.environ)
ENV['DISPLAY'] = ':0'
ENV['XAUTHORITY'] = '/run/user/1000/xauth_smhqjo'

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, env=ENV)

# find windows by name
wins = {}
for line in run(['wmctrl', '-l']).stdout.splitlines():
    parts = line.split(None, 2)
    if len(parts) == 3 and 'LightBurn' in parts[2]:
        wins[parts[2]] = parts[0]
print("windows:", wins)

# place: main at (150,150), license page at (1950,200)
plan = []
for name, wid in wins.items():
    if 'License Page' in name:
        pos = (1950, 200)
    else:
        pos = (150, 150)
    run(['xdotool', 'windowmove', wid, str(pos[0]), str(pos[1])])
    plan.append((name, wid, pos))
time.sleep(1.0)

shotdir = os.path.expanduser("~/Pictures/Screenshots")
before = set(glob.glob(shotdir + "/*.png"))
run(['spectacle', '-f', '-b', '-n'])
time.sleep(1.2)
after = set(glob.glob(shotdir + "/*.png"))
new = after - before
shot = max(new, key=os.path.getmtime) if new else sorted(glob.glob(shotdir + "/*.png"))[-1]
print("screenshot:", shot)

im = Image.open(shot).convert('RGB')
SW, SH = im.size
print("screen px:", (SW, SH))

from rapidocr_onnxruntime import RapidOCR
ocr = RapidOCR()

for name, wid, pos in plan:
    g = run(['xdotool', 'getwindowgeometry', '--shell', wid]).stdout
    gd = dict(l.split('=', 1) for l in g.strip().splitlines() if '=' in l)
    x, y = int(gd.get('X', pos[0])), int(gd.get('Y', pos[1]))
    w, h = int(gd.get('WIDTH', 0)), int(gd.get('HEIGHT', 0))
    x0, y0 = max(0, x - 10), max(0, y - 10)
    x1, y1 = min(SW, x + w + 10), min(SH, y + h + 10)
    crop = im.crop((x0, y0, x1, y1))
    out = "ocr_" + ("main" if 'untitled' in name else "licensepage") + ".png"
    crop.save(out)
    print(f"--- {name} -> {out} ({crop.size}) ---")
    res, _ = ocr(out)
    if not res:
        print("  (no text)")
        continue
    for line in sorted(res, key=lambda r: (r[0][0][1], r[0][0][0])):
        box, txt, conf = line
        print(f"  [{float(conf):.2f}] {txt}")
