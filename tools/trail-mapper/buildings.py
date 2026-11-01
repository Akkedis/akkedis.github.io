import os
"""Find NGI 1:50k building symbols (small solid black squares) near a point."""
import math, sys, numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ngi import fetch
from router import merc, unmerc
from PIL import Image
from lib import hav
def buildings_near(lat, lon, radius_m=350):
    x, y = merc(lat, lon); R = int(radius_m / 4) + 4
    x0, y0 = int(x - R), int(y - R); W = H = 2 * R
    img = Image.new("RGB", (W + 512, H + 512))
    tx0, ty0 = x0 // 256, y0 // 256
    for tx in range(tx0, (x0 + W) // 256 + 1):
        for ty in range(ty0, (y0 + H) // 256 + 1):
            img.paste(fetch(15, tx, ty).convert("RGB"), ((tx - tx0) * 256, (ty - ty0) * 256))
    a = np.asarray(img).astype(int)[(y0 - ty0 * 256):(y0 - ty0 * 256) + H, (x0 - tx0 * 256):(x0 - tx0 * 256) + W]
    black = a.max(axis=2) < 100
    seen = np.zeros_like(black); found = []
    for yy, xx in zip(*np.nonzero(black)):
        if seen[yy, xx]: continue
        st = [(yy, xx)]; seen[yy, xx] = True; comp = []
        while st and len(comp) < 200:
            p = st.pop(); comp.append(p)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    q = (p[0] + dy, p[1] + dx)
                    if 0 <= q[0] < H and 0 <= q[1] < W and black[q] and not seen[q]: seen[q] = True; st.append(q)
        P = np.array(comp); h = np.ptp(P[:, 0]) + 1; w = np.ptp(P[:, 1]) + 1
        if 3 <= h <= 12 and 3 <= w <= 12 and len(comp) >= 0.75 * h * w and max(h, w) <= 1.8 * min(h, w):
            cy, cx = P.mean(axis=0); found.append(unmerc(x0 + cx, y0 + cy))
    found.sort(key=lambda p: hav(p, (lat, lon)))
    return found
def farmstead(lat, lon, radius_m=350):
    """centroid of the building cluster nearest the point"""
    b = buildings_near(lat, lon, radius_m)
    if not b: return None
    first = b[0]; cl = [p for p in b if hav(p, first) < 80]
    return (round(sum(p[0] for p in cl) / len(cl), 5), round(sum(p[1] for p in cl) / len(cl), 5)), len(cl), round(hav(first, (lat, lon)))
