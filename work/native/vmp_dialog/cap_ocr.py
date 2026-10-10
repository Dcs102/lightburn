#!/usr/bin/env python3
"""Find the LightBurn dialog window, move it on-screen, capture full screen with
spectacle, crop to the window bbox (with margin), and OCR the crop.
Usage: cap_ocr.py <out_prefix> [margin]
"""
import sys, subprocess, os, glob, time
from PIL import Image

OUT = sys.argv[1] if len(sys.argv) > 1 else "cap"
MARGIN = int(sys.argv[2]) if len(sys.argv) > 2 else 30
ENV = dict(os.environ)
ENV['DISPLAY'] = ':0'
ENV['XAUTHORITY'] = '/run/user/1000/xauth_smhqjo'

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, env=ENV, **kw)

# find the LightBurn.exe window id via wmctrl
wid = None
for line in run(['wmctrl', '-l']).stdout.splitlines():
    if 'LightBurn' in line:
        wid = line.split()[0]
        break
if not wid:
    print("NO LightBurn WINDOW FOUND"); sys.exit(2)
print("window id:", wid)

# move it fully on-screen (top-left area), keep size
run(['xdotool', 'windowmove', wid, '150', '150'])
time.sleep(0.6)
geo = run(['xdotool', 'getwindowgeometry', '--shell', wid]).stdout
g = dict(l.split('=', 1) for l in geo.strip().splitlines() if '=' in l)
x, y, w, h = int(g.get('X', 0)), int(g.get('Y', 0)), int(g.get('WIDTH', 0)), int(g.get('HEIGHT', 0))
print(f"geometry: x={x} y={y} w={w} h={h}")

# capture full screen with spectacle (saves to ~/Pictures/Screenshots/)
shotdir = os.path.expanduser("~/Pictures/Screenshots")
before = set(glob.glob(shotdir + "/*.png"))
run(['spectacle', '-f', '-b', '-n'])
time.sleep(1.0)
after = set(glob.glob(shotdir + "/*.png"))
new = after - before
if not new:
    # fall back to most recent
    shots = sorted(glob.glob(shotdir + "/*.png")); shot = shots[-1]
else:
    shot = max(new, key=os.path.getmtime)
print("screenshot:", shot)

im = Image.open(shot).convert('RGB')
SW, SH = im.size
print("screen px:", (SW, SH))
# crop with margin
x0, y0 = max(0, x - MARGIN), max(0, y - MARGIN)
x1, y1 = min(SW, x + w + MARGIN), min(SH, y + h + MARGIN)
crop = im.crop((x0, y0, x1, y1))
crop.save(f"{OUT}_full.png")
print("crop saved:", f"{OUT}_full.png", crop.size)

# OCR the crop (and a 2x upscaled version for robustness)
from rapidocr_onnxruntime import RapidOCR
ocr = RapidOCR()
def ocr_img(path, label):
    res, _ = ocr(path)
    print(f"=== OCR {label} ===")
    if not res:
        print("  (no text detected)")
        return
    for line in sorted(res, key=lambda r: (r[0][0][1], r[0][0][0])):
        box, txt, conf = line
        try:
            cfs = f"{float(conf):.2f}"
        except Exception:
            cfs = str(conf)
        print(f"  [{cfs}] {txt}")

ocr_img(f"{OUT}_full.png", "native crop")
up = crop.resize((crop.width * 2, crop.height * 2), Image.LANCZOS)
up.save(f"{OUT}_x2.png")
ocr_img(f"{OUT}_x2.png", "2x upscaled crop")
