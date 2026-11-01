import os
"""Combined OSM + NGI 1:50k raster router.

Routes between waypoints on an 8 m cost grid where
  - cells on an OSM way (track/path/road)        -> cheap
  - cells on a black/red line of the NGI 1:50k map -> cheap (tracks, roads, fences, dam walls)
  - open country                                 -> expensive
  - open water (blue fill, not under a line)     -> very expensive
Search is limited to a corridor around a guide line (the previous route).
"""
import json, math, heapq, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngi import fetch            # NGI 1:50k tile fetcher (z15, cached)

Z = 15          # NGI max native zoom (~4 m/px here)
POOL = 2        # 2x2 pixels -> one cell (~8 m)
COST_LINE, COST_OPEN, COST_WATER = 1.0, 10.0, 300.0

def merc(lat, lon, z=Z):
    n = 2 ** z * 256
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y

def unmerc(x, y, z=Z):
    n = 2 ** z * 256
    lon = x / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lat, lon

def text_mask(black):
    """Black map text (labels, spot heights) and building squares: small compact solid blobs.
    Track dashes are thin strokes and are kept."""
    H, W = black.shape
    lab = np.zeros((H, W), np.int32); out = np.zeros((H, W), bool)
    ys, xs = np.nonzero(black); nid = 0
    for y0, x0 in zip(ys.tolist(), xs.tolist()):
        if lab[y0, x0]: continue
        nid += 1; st = [(y0, x0)]; lab[y0, x0] = nid; comp = []
        while st:
            y, x = st.pop(); comp.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < H and 0 <= xx < W and black[yy, xx] and not lab[yy, xx]:
                        lab[yy, xx] = nid; st.append((yy, xx))
            if len(comp) > 400: break
        if len(comp) > 400:          # big connected feature (road, long track) - keep; mark rest visited lazily
            continue
        P = np.array(comp, float); h = np.ptp(P[:, 0]) + 1; w = np.ptp(P[:, 1]) + 1; a = len(comp)
        if a < 10 or max(h, w) > 30: continue
        ev = np.linalg.eigvalsh(np.cov(P.T) + 1e-6 * np.eye(2))
        elong = math.sqrt(ev[1] / ev[0])
        if elong < 2.6:                     # roundish blob: letter, digit or building -> not a path
            for y, x in comp: out[y, x] = True
    return out

class Grid:
    def __init__(self, guide, osm_lines, buffer_m=350):
        xs, ys = zip(*[merc(*p) for p in guide])
        pad = 160 + buffer_m / 4
        self.x0 = int((min(xs) - pad) // 256 * 256); self.y0 = int((min(ys) - pad) // 256 * 256)
        x1 = int((max(xs) + pad) // 256 * 256 + 256); y1 = int((max(ys) + pad) // 256 * 256 + 256)
        W, H = x1 - self.x0, y1 - self.y0
        # --- NGI raster
        img = Image.new("RGB", (W, H), (255, 255, 255))
        for tx in range(self.x0 // 256, x1 // 256):
            for ty in range(self.y0 // 256, y1 // 256):
                img.paste(fetch(Z, tx, ty).convert("RGB"), (tx * 256 - self.x0, ty * 256 - self.y0))
        a = np.asarray(img).astype(np.int16)
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        black = np.maximum(np.maximum(r, g), b) < 110
        red = (r > 150) & (g < 120) & (b < 110)
        water = (r >= 190) & (r <= 222) & (g >= 212) & (g <= 236) & (b >= 236)
        # erase map grid / sheet-edge lines: long straight horizontal or vertical black runs
        def runs(m, axis, L=300):
            mm = m if axis == 1 else m.T
            out = np.zeros_like(mm)
            for i in range(mm.shape[0]):
                row = mm[i]
                if row.sum() < L: continue
                d = np.diff(np.concatenate(([0], row.astype(np.int8), [0])))
                st, en = np.where(d == 1)[0], np.where(d == -1)[0]
                for a_, b_ in zip(st, en):
                    if b_ - a_ >= L: out[i, a_:b_] = True
            return out if axis == 1 else out.T
        grid = runs(black, 1) | runs(black, 0)
        for ax in (0, 1):                      # rows/columns that are black over most of the window
            frac = black.mean(axis=ax)
            idx = np.where(frac > 0.45)[0]
            if ax == 0: grid[:, idx] = True
            else: grid[idx, :] = True
        grid = grid | np.roll(grid, 1, 0) | np.roll(grid, -1, 0) | np.roll(grid, 1, 1) | np.roll(grid, -1, 1)
        black = black & ~grid
        black = black & ~text_mask(black)
        ngi = black | red
        h, w = H // POOL, W // POOL
        pool = lambda m: m[:h * POOL, :w * POOL].reshape(h, POOL, w, POOL).any(axis=(1, 3))
        poolall = lambda m: m[:h * POOL, :w * POOL].reshape(h, POOL, w, POOL).all(axis=(1, 3))
        ngi = pool(ngi); water = poolall(water)
        ngi = ngi | np.roll(ngi, 1, 0) | np.roll(ngi, -1, 0) | np.roll(ngi, 1, 1) | np.roll(ngi, -1, 1)  # bridge dash gaps
        # --- OSM raster
        om = Image.new("L", (w, h), 0); d = ImageDraw.Draw(om)
        for line in osm_lines:
            pts = [self.cell(*p) for p in line]
            if any(0 <= c <= w and 0 <= rr <= h for c, rr in pts):
                d.line([(c, rr) for c, rr in pts], fill=255, width=2)
        osm = np.asarray(om) > 0
        # --- corridor
        cm = Image.new("L", (w, h), 0); d = ImageDraw.Draw(cm)
        d.line([self.cell(*p) for p in guide], fill=255, width=int(2 * buffer_m / (4 * POOL)))
        self.corr = np.asarray(cm) > 0
        cost = np.full((h, w), COST_OPEN, dtype=np.float32)
        cost[water] = COST_WATER
        cost[ngi] = COST_LINE; cost[osm] = 0.85 * COST_LINE
        self.cost, self.osm, self.ngi, self.h, self.w = cost, osm, ngi, h, w

    def cell(self, lat, lon):
        x, y = merc(lat, lon)
        return int((x - self.x0) / POOL), int((y - self.y0) / POOL)

    def latlon(self, c, r):
        return unmerc(self.x0 + (c + .5) * POOL, self.y0 + (r + .5) * POOL)

    def snap(self, c, r, R=6):
        """move a waypoint onto the nearest line cell within R cells"""
        best = None
        for dc in range(-R, R + 1):
            for dr in range(-R, R + 1):
                cc, rr = c + dc, r + dr
                if 0 <= cc < self.w and 0 <= rr < self.h and self.cost[rr, cc] <= COST_LINE:
                    dd = dc * dc + dr * dr
                    if best is None or dd < best[0]: best = (dd, cc, rr)
        return (best[1], best[2]) if best else (c, r)

    def route(self, a, b):
        for q in (self.cell(*a), self.cell(*b)):          # always let the search reach the waypoints
            c0, r0 = q; R = 40
            self.corr[max(0, r0 - R):r0 + R, max(0, c0 - R):c0 + R] = True
        s = self.snap(*self.cell(*a)); t = self.snap(*self.cell(*b))
        dist = {s: 0.0}; prev = {}; pq = [(0.0, 0.0, s)]
        tc, tr = t
        N8 = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
        while pq:
            _, dcur, u = heapq.heappop(pq)
            if u == t: break
            if dcur > dist[u]: continue
            c, r = u
            for dc, dr, f in N8:
                v = (c + dc, r + dr)
                if not (0 <= v[0] < self.w and 0 <= v[1] < self.h): continue
                if not self.corr[v[1], v[0]] and v != t: continue
                nd = dcur + f * (self.cost[r, c] + self.cost[v[1], v[0]]) / 2
                if nd < dist.get(v, 1e18):
                    dist[v] = nd; prev[v] = u
                    hh = math.hypot(v[0] - tc, v[1] - tr) * COST_LINE
                    heapq.heappush(pq, (nd + hh, nd, v))
        if t not in dist: return None
        path = [t]
        while path[-1] != s: path.append(prev[path[-1]])
        return path[::-1]

import sys as _s; _s.setrecursionlimit(100000)
def rdp(pts, eps):
    if len(pts) < 3: return pts
    a, b = np.array(pts[0], float), np.array(pts[-1], float)
    ab = b - a; L = np.hypot(*ab)
    P = np.array(pts, float)
    D = P - a
    d = np.abs(ab[0] * D[:, 1] - ab[1] * D[:, 0]) / L if L else np.hypot(D[:, 0], D[:, 1])
    i = int(d.argmax())
    if d[i] > eps: return rdp(pts[:i + 1], eps)[:-1] + rdp(pts[i:], eps)
    return [pts[0], pts[-1]]

def route_day(grid, waypoints):
    """returns list of {'k': 'o'|'n'|'h', 'c': [[lat,lon],...]} pieces (o=OSM, n=NGI only, h=open country)"""
    cells = []
    for a, b in zip(waypoints, waypoints[1:]):
        p = grid.route(a, b)
        if p is None: raise RuntimeError(f"no route {a}->{b}")
        cells += p if not cells else p[1:]
    # remove out-and-back spurs: if the path returns within 1 cell of where it was <=80 cells ago, cut the loop
    i = 0; out_cells = []
    for cell in cells:
        cut = None
        for j in range(len(out_cells) - 7, max(-1, len(out_cells) - 120), -1):
            if abs(out_cells[j][0] - cell[0]) <= 3 and abs(out_cells[j][1] - cell[1]) <= 3 and len(out_cells) - j > 6:
                cut = j
        if cut is not None: out_cells = out_cells[:cut + 1]
        else: out_cells.append(cell)
    cells = out_cells
    out_cells = []
    for cell in cells:
        cut = None
        for j in range(len(out_cells) - 7, max(-1, len(out_cells) - 120), -1):
            if abs(out_cells[j][0] - cell[0]) <= 3 and abs(out_cells[j][1] - cell[1]) <= 3 and len(out_cells) - j > 6:
                cut = j
        if cut is not None: out_cells = out_cells[:cut + 1]
        else: out_cells.append(cell)
    cells = out_cells
    kind = lambda c, r: 'o' if grid.osm[r, c] else ('n' if grid.ngi[r, c] else 'h')
    ks = [kind(c, r) for c, r in cells]
    # smooth: open-country runs shorter than 5 cells (40 m) inherit neighbour kind
    i = 0
    while i < len(ks):
        j = i
        while j < len(ks) and ks[j] == ks[i]: j += 1
        if ks[i] == 'h' and j - i < 5:
            ks[i:j] = [ks[i - 1] if i else (ks[j] if j < len(ks) else 'n')] * (j - i)
        i = j
    pieces = []
    for (c, r), k in zip(cells, ks):
        if pieces and pieces[-1]['k'] == k: pieces[-1]['cells'].append((c, r))
        else:
            if pieces: pieces[-1]['cells'].append((c, r))
            pieces.append({'k': k, 'cells': [(c, r)]})
    out = []
    for p in pieces:
        simp = rdp(p['cells'], 1.0)
        out.append({'k': p['k'], 'c': [[round(v, 6) for v in grid.latlon(c, r)] for c, r in simp]})
    return out
