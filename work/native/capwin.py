#!/usr/bin/env python3
"""Robust per-window capture on headless Wayland/Xwayland.
Kwin only mirrors frames to the X root during active rendering, so we
oscillate the mouse over the target window (forcing hover repaints) while
grabbing many root frames and keep the highest-content crop of the window bbox.
Usage: capwin.py <wid_hex> <out.png> [x y w h]
  If x y w h omitted, reads geometry from wmctrl -lG for the wid.
"""
import sys, subprocess, time
from PIL import ImageGrab
import numpy as np

def wmctrl_geom(wid):
    out = subprocess.run(['wmctrl', '-lG'], capture_output=True, text=True).stdout
    for line in out.splitlines():
        p = line.split(None, 6)
        if p and p[0] == wid:
            return int(p[2]), int(p[3]), int(p[4]), int(p[5])
    return None

def main():
    wid = sys.argv[1]
    outp = sys.argv[2]
    if len(sys.argv) >= 6:
        x, y, w, h = (int(v) for v in sys.argv[3:7])
    else:
        g = wmctrl_geom(wid)
        if not g:
            print("no geometry for", wid); sys.exit(2)
        x, y, w, h = g
    # center of window to hover over (clamped later by xdotool)
    cx, cy = x + w // 2, y + h // 2
    img = ImageGrab.grab()
    SW, SH = img.size
    best = None
    bestscore = -1
    n = int(sys.argv[7]) if len(sys.argv) > 7 else 40
    for i in range(n):
        # oscillate mouse to force repaints
        dx = (i % 5) * 30 - 60
        dy = (i % 3) * 20 - 20
        subprocess.run(['xdotool', 'mousemove', str(cx + dx), str(cy + dy)],
                       stderr=subprocess.DEVNULL)
        time.sleep(0.05)
        f = ImageGrab.grab()
        g = np.array(f.convert('L'))
        # crop to window bbox (clamped to screen)
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(SW, x + w), min(SH, y + h)
        if x1 <= x0 or y1 <= y0:
            continue
        crop = g[y0:y1, x0:x1]
        score = float(crop[crop > 10].size)  # count of lit pixels in window region
        if score > bestscore:
            bestscore = score
            best = f.crop((x0, y0, x1, y1))
    if best is None:
        print("no frame captured"); sys.exit(3)
    bg = np.array(best.convert('L'))
    best.save(outp)
    print(f"saved {outp} size={best.size} litpx={bestscore} mean={bg.mean():.1f} nz={(bg>10).mean():.3f}")

if __name__ == '__main__':
    main()
