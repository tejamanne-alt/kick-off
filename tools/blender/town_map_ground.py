# The ground of the town map, painted flat (everything that has no height: land, lawns, lots, roads with kerbs and paint,
# pavements, the railway bed, sand, the sea with foam, paths, the pitch). town_map_raster has the painting helpers; the
# buildings, trees, cars and other models stand on top of this in Blender and cast their shadows on it.
import math, zlib, random
import numpy as np
from PIL import Image, ImageDraw
import town_map_raster as R
import town_map_graph as G

# sRGB colours
ASPHALT = (0.39, 0.39, 0.41)
PAVEMENT = (0.74, 0.72, 0.68)
KERB = (0.84, 0.83, 0.79)
KERB_SHADE = (0.24, 0.24, 0.26)
PATH = (0.84, 0.79, 0.68)
LAWN = (0.47, 0.59, 0.35)
GARDEN = (0.50, 0.62, 0.37)
GARDEN2 = (0.44, 0.57, 0.34)
PARK_LAWN = (0.46, 0.60, 0.35)
FIELD = (0.66, 0.72, 0.38)
FIELD2 = (0.58, 0.68, 0.36)
FIELD3 = (0.74, 0.74, 0.40)
SAND = (0.93, 0.83, 0.62)
SAND_DRY = (0.96, 0.88, 0.69)
SAND_WET = (0.80, 0.70, 0.52)
SEA_SHALLOW = (0.45, 0.83, 0.80)
SEA_MID = (0.20, 0.62, 0.74)
SEA_DEEP = (0.10, 0.40, 0.62)
FOAM = (0.97, 0.98, 0.97)
BALLAST = (0.58, 0.56, 0.52)
SLEEPER = (0.36, 0.31, 0.27)
RAIL = (0.78, 0.78, 0.80)
DIRT = (0.64, 0.55, 0.43)
GRAVEL = (0.66, 0.62, 0.56)
WHITE = (0.93, 0.93, 0.9)
CONCRETE = (0.74, 0.73, 0.70)
WOOD = (0.62, 0.45, 0.30)


def seed_of(name):
    return zlib.crc32(name.encode()) % 1000


class Masks:
    """Boolean masks of the road network at the picture's own resolution, shared by the painter and the placement code.
    The blocks' corners are rounded (a kerb radius) by closing the masks with a disc, but only close to a junction, so the
    long thin wedges between diverging roads stay open for gardens."""

    def __init__(self, L, B, kerb=26, kerb_pave=34, reach=36):
        self.W, self.H = R.IMG_W, R.IMG_H
        graph = B['graph']
        W, H = self.W, self.H
        pave = np.zeros((H, W), bool)
        road = np.zeros((H, W), bool)
        path = np.zeros((H, W), bool)
        board = np.zeros((H, W), bool)
        cover_r = np.zeros((H, W), np.uint8)
        cover_p = np.zeros((H, W), np.uint8)
        ox, oy = R.ORIGIN

        def stroke(pts, width):
            """(x0, y0, boolean array) of a thick polyline, limited to its bounding box."""
            pts = [(p[0] + ox, p[1] + oy) for p in pts]
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            x0, y0 = max(0, int(min(xs) - width) - 2), max(0, int(min(ys) - width) - 2)
            x1, y1 = min(W, int(max(xs) + width) + 3), min(H, int(max(ys) + width) + 3)
            if x1 <= x0 or y1 <= y0:
                return None
            im = Image.new('L', (x1 - x0, y1 - y0), 0)
            d = ImageDraw.Draw(im)
            q = [(p[0] - x0, p[1] - y0) for p in pts]
            d.line(q, fill=255, width=int(width), joint='curve')
            return x0, y0, np.asarray(im) > 0

        for r in graph.roads:
            cls = L.CLASSES[r.cls]
            if r.cls in ('path', 'board'):
                st = stroke(r.curve, cls['total'])
                if st:
                    x0, y0, a = st
                    (board if r.cls == 'board' else path)[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] |= a
                continue
            st = stroke(r.curve, cls['total'])
            if st:
                x0, y0, a = st
                pave[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] |= a
                cover_p[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] += a.astype(np.uint8)
            st = stroke(r.curve, cls['road'])
            if st:
                x0, y0, a = st
                road[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] |= a
                cover_r[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] += a.astype(np.uint8)
        self.pave, self.road, self.path, self.board = pave, road, path, board
        # fillets only near the places where two roads meet
        near_r = R.dilate_disc(cover_r >= 2, reach)
        near_p = R.dilate_disc(cover_p >= 2, reach + 8)
        self.road_c = road | (R.close_disc(road, kerb) & near_r)
        self.pave_c = pave | (R.close_disc(pave, kerb_pave) & near_p) | self.road_c
        self.junction = R.dilate_disc(cover_r >= 2, 4)
        self.cover = cover_r


def draw_layer(cv, fn):
    """A full-canvas mask drawn by fn(ImageDraw, C) at the canvas' resolution; returns float32 0..1."""
    im = Image.new('L', (cv.W, cv.H), 0)
    fn(ImageDraw.Draw(im), cv.C)
    return np.asarray(im, np.float32) / 255.0


def up(mask_bool, cv):
    """A 1x boolean mask as a smooth canvas-sized float mask."""
    im = Image.fromarray((mask_bool * 255).astype(np.uint8)).resize((cv.W, cv.H), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255.0


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def soft_mask(cv, pts, edge=5.0, wobble=0.28, seed=1):
    """A polygon's mask with a soft, slightly broken edge (so areas never end in a straight tile boundary). (x0, y0, array)"""
    pad = int(edge * 3)
    m = cv.poly_mask(pts, blur=edge * 0.5)
    if m is None:
        return None
    x0, y0, a = m
    h, w = a.shape
    n = cv.noise(7, seed)[y0:y0 + h, x0:x0 + w]
    a = smoothstep(0.40, 0.60, a + wobble * 0.3 * n)
    return x0, y0, a


def paint_land(cv, L):
    """The base: lawn-green land with big soft patches (no tiles anywhere)."""
    n1 = cv.noise(380, 5)
    n2 = cv.noise(70, 6)
    n3 = cv.noise(12, 7)
    base = np.array(LAWN, np.float32)
    cv.px[...] = base[None, None, :] * (1 + 0.06 * n1[..., None] + 0.035 * n2[..., None] + 0.02 * n3[..., None])
    cv.px[..., 0] += 0.035 * n1
    cv.px[..., 2] -= 0.025 * n1


# ------------------------------------------------------------------ the sea and the sand
def coast_curve(L):
    """The coast as a smooth curve (the layout's COAST points are its control points)."""
    return G.catmull_rom(list(L.COAST), step=6.0)[0]


def coast_distance(curve, grid=8):
    """A coarse grid (1/grid of the picture) of the signed distance in picture px to the coast curve (core coords): positive in
    the sea (the right of its direction of travel, closed far outside the picture), negative on the land."""
    gw, gh = R.IMG_W // grid, R.IMG_H // grid
    xs = ((np.arange(gw) + 0.5) * grid - R.ORIGIN[0]).astype(np.float32)
    ys = ((np.arange(gh) + 0.5) * grid - R.ORIGIN[1]).astype(np.float32)
    X, Y = np.meshgrid(xs, ys)
    best = np.full((gh, gw), 1e9, np.float32)
    for i in range(len(curve) - 1):
        ax, ay = curve[i]; bx, by = curve[i + 1]
        dx, dy = bx - ax, by - ay
        l2 = dx * dx + dy * dy
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / l2, 0, 1)
        d = np.hypot(X - (ax + t * dx), Y - (ay + t * dy))
        best = np.minimum(best, d)
    # the sign: even-odd test against the sea polygon (the curve closed through two far points on the right)
    poly = list(curve) + [(3400.0, 1650.0), (3400.0, -300.0)]
    inside = np.zeros((gh, gw), bool)
    for i in range(len(poly)):
        ax, ay = poly[i]; bx, by = poly[(i + 1) % len(poly)]
        if ay == by:
            continue
        inside ^= ((ay > Y) != (by > Y)) & (X < (bx - ax) * (Y - ay) / (by - ay) + ax)
    return np.where(inside, best, -best).astype(np.float32)


def paint_coast(cv, L):
    """Sea with a depth gradient, light shallows, wave lines and foam; sand with ripples and a wet band at the water."""
    curve = coast_curve(L)
    d = coast_distance(curve, 8)
    d = np.asarray(Image.fromarray(d).resize((cv.W, cv.H), Image.BICUBIC), np.float32)     # picture px; + = sea
    nfine = cv.noise(5, 41)
    nmid = cv.noise(34, 42)
    nbig = cv.noise(160, 43)
    ds = d + 6 * nmid                              # a wobbling shoreline
    # sea colour by depth
    t1 = smoothstep(0, 70, ds)
    t2 = smoothstep(40, 380, ds)
    sea = (np.array(SEA_SHALLOW, np.float32)[None, None, :] * (1 - t1[..., None]) + np.array(SEA_MID, np.float32)[None, None, :] * t1[..., None])
    sea = sea * (1 - t2[..., None]) + np.array(SEA_DEEP, np.float32)[None, None, :] * t2[..., None]
    sea = sea * (1 + 0.035 * nmid[..., None] + 0.02 * nfine[..., None])
    # wave lines: bands parallel to the shore, broken up by noise
    waves = np.zeros_like(d)
    for k, (dist, wid) in enumerate(((22, 2.2), (46, 2.6), (84, 3.0), (140, 3.4))):
        band = np.exp(-((ds - dist - 5 * nmid) / wid) ** 2)
        waves = np.maximum(waves, band * smoothstep(-0.1, 0.35, nbig + 0.35 * nmid + 0.15 * k))
    foam = np.exp(-((ds - 3) / 3.4) ** 2) * (0.75 + 0.25 * nfine) * (0.6 + 0.4 * smoothstep(-0.5, 0.2, nmid))
    foam2 = np.exp(-((ds - 11) / 2.2) ** 2) * smoothstep(-0.05, 0.4, nbig + nmid * 0.5)
    sea_mask = smoothstep(-1.5, 1.5, ds)
    cv.blend_full(sea_mask, sea)
    cv.blend_full(np.clip(waves * 0.55, 0, 1) * sea_mask, FOAM)
    cv.blend_full(np.clip(foam, 0, 1) * smoothstep(-6, 2, ds), FOAM)
    cv.blend_full(np.clip(foam2, 0, 1) * sea_mask * 0.7, FOAM)
    # sand: everywhere inside the sand polygon, wet and dark near the water
    sand = list(L.SAND_LAND) + [tuple(p) for p in curve[::-1]]
    m = soft_mask(cv, sand, edge=7, seed=51)
    if m is not None:
        x0, y0, a = m
        h, w = a.shape
        dd = ds[y0:y0 + h, x0:x0 + w]
        ripple = 0.5 + 0.5 * np.sin((dd * 0.33) + 3.0 * cv.noise(60, 52)[y0:y0 + h, x0:x0 + w])
        col = np.array(SAND, np.float32)[None, None, :] * np.ones((h, w, 1), np.float32)
        dry = smoothstep(-150, -50, dd)
        col = col * (1 - dry[..., None]) + np.array(SAND_DRY, np.float32)[None, None, :] * dry[..., None]
        col = col * (1 + 0.025 * (ripple[..., None] - 0.5) + 0.03 * cv.noise(20, 53)[y0:y0 + h, x0:x0 + w, None] + 0.02 * nfine[y0:y0 + h, x0:x0 + w, None])
        wet = smoothstep(-34, -2, dd)
        col = col * (1 - 0.7 * wet[..., None]) + np.array(SAND_WET, np.float32)[None, None, :] * (0.7 * wet[..., None])
        cv.blend((x0, y0, a * (1 - sea_mask[y0:y0 + h, x0:x0 + w])), np.clip(col, 0, 1))
        # the sea's edge over the wet sand
        cv.blend_full(np.clip(foam, 0, 1) * smoothstep(-6, 2, ds) * 0.8, FOAM)


# ------------------------------------------------------------------ fields and the north ring
def paint_fields(cv, L):
    """The country north of the town: fields in strips of different greens with hedgerows, a track, wood floors."""
    poly = L.AREAS['fields']['poly']
    m = soft_mask(cv, poly, edge=16, wobble=1.4, seed=61)
    if m is None:
        return
    x0, y0, a = m
    h, w = a.shape
    sl = (slice(y0, y0 + h), slice(x0, x0 + w))
    # meadows in big soft patches of different greens (no bands, no tiles)
    n1 = cv.noise(300, 62)[sl]
    n2 = cv.noise(110, 63)[sl]
    n3 = cv.noise(16, 64)[sl]
    mix = smoothstep(-0.3, 0.3, n1 + 0.4 * n2)[..., None]
    mix2 = smoothstep(0.05, 0.45, cv.noise(210, 65)[sl] + 0.3 * n2)[..., None]
    col = np.array(FIELD2, np.float32) * (1 - mix) + np.array(FIELD, np.float32) * mix
    col = col * (1 - 0.7 * mix2) + np.array(FIELD3, np.float32) * (0.7 * mix2)
    col = col * (1 + 0.05 * n2[..., None] + 0.03 * n3[..., None])
    cv.blend((x0, y0, a), np.clip(col, 0, 1))


# ------------------------------------------------------------------ lots
def paint_lots(cv, lots):
    rng = random.Random(5)
    greens = [GARDEN, GARDEN2, (0.52, 0.66, 0.35), (0.56, 0.68, 0.38), (0.49, 0.64, 0.33)]
    for lot in lots:
        r = random.Random(lot.seed)
        if lot.kind == 'market':
            col = PAVEMENT
        elif lot.kind == 'flats':
            col = (0.60, 0.68, 0.42)
        else:
            col = r.choice(greens)
        m = cv.poly_mask(lot.poly, blur=0.4)
        if m is None:
            continue
        x0, y0, a = m
        h, w = a.shape
        tex = np.array(col, np.float32)[None, None, :] * (1 + 0.035 * cv.noise(30, 71)[y0:y0 + h, x0:x0 + w, None] + 0.025 * cv.noise(6, 72)[y0:y0 + h, x0:x0 + w, None])
        cv.blend((x0, y0, a), np.clip(tex, 0, 1), 0.92 if lot.kind == 'residential' else 0.95)
        # the path from the gate to the door
        (b0, b1) = lot.path
        pm = cv.line_mask([b0, b1], 5.0, cap=False)
        if pm is not None and lot.kind != 'market':
            cv.blend(pm, PATH)
        # flower beds along the path, a patio, a vegetable patch or a pool behind
        if lot.kind == 'residential':
            q = lot.poly
            ex = (q[1][0] - q[0][0], q[1][1] - q[0][1])
            n = math.hypot(*ex) or 1
            ex = (ex[0] / n, ex[1] / n)
            ey = (q[3][0] - q[0][0], q[3][1] - q[0][1])
            m2 = math.hypot(*ey) or 1
            ey = (ey[0] / m2, ey[1] / m2)
            if r.random() < 0.5:
                for k in range(r.randint(2, 4)):
                    u = r.uniform(0.1, 0.9) * n
                    v = r.uniform(2, 10)
                    c = (q[0][0] + ex[0] * u + ey[0] * v, q[0][1] + ex[1] * u + ey[1] * v)
                    fm = cv.disc_mask(c, r.uniform(1.8, 3.2))
                    cv.blend(fm, r.choice([(0.92, 0.55, 0.62), (0.98, 0.84, 0.35), (0.90, 0.42, 0.36), (0.80, 0.62, 0.86)]), 0.9)
            if r.random() < 0.3:
                c = (q[3][0] + ex[0] * n * 0.5 - ey[0] * 14 , q[3][1] + ex[1] * n * 0.5 - ey[1] * 14)
                if r.random() < 0.4:
                    pm2 = cv.rect_mask(c, 18, 10, 0.0)
                    cv.blend(pm2, (0.78, 0.76, 0.72), 0.9)
                elif r.random() < 0.4:
                    pm2 = cv.rect_mask(c, 20, 8, 0.0)
                    cv.blend(pm2, (0.55, 0.44, 0.30), 0.9)
                    for kk in range(4):
                        pm3 = cv.line_mask([(c[0] - 9, c[1] - 3 + kk * 2), (c[0] + 9, c[1] - 3 + kk * 2)], 0.8, cap=False)
                        cv.blend(pm3, (0.40, 0.60, 0.28), 0.9)
                elif r.random() < 0.3:
                    pm2 = cv.rect_mask(c, 17, 11, 0.0)
                    cv.blend(pm2, (0.85, 0.92, 0.92), 1.0)
                    pm3 = cv.rect_mask(c, 14, 8, 0.0)
                    cv.blend(pm3, (0.38, 0.75, 0.86), 1.0)


# ------------------------------------------------------------------ roads
def paint_roads(cv, L, B, masks):
    ss = cv.ss
    graph = B['graph']
    pave_a = up(masks.pave_c, cv)
    road_a = up(masks.road_c, cv)
    n_fine = cv.noise(6, 21)
    n_mid = cv.noise(50, 22)
    # pavement with slab lines
    pav = np.array(PAVEMENT, np.float32)[None, None, :] * (1 + 0.03 * n_fine[..., None] + 0.035 * n_mid[..., None])
    cv.blend_full(pave_a, pav)
    ring_out = R.dilate_disc(masks.road_c, 2) & ~masks.road_c
    ring_in = masks.road_c & ~R.erode_disc(masks.road_c, 1)
    cv.blend_full(up(ring_out, cv), KERB)
    asph = np.array(ASPHALT, np.float32)[None, None, :] * (1 + 0.035 * n_fine[..., None] + 0.055 * n_mid[..., None] + 0.03 * cv.noise(9, 23)[..., None])
    cv.blend_full(road_a, asph)
    cv.blend_full(up(ring_in, cv), KERB_SHADE, 0.55)
    # paths: light stone
    cv.blend_full(up(masks.path, cv), np.array(PATH, np.float32)[None, None, :] * (1 + 0.03 * n_fine[..., None]))
    # boardwalks: weathered planks across the walk, a darker gap between them, posts along both edges
    cv.blend_full(up(masks.board, cv), np.array((0.66, 0.50, 0.34), np.float32)[None, None, :] * (1 + 0.05 * n_fine[..., None] + 0.04 * n_mid[..., None]))

    def planks(d, C):
        for r in graph.roads:
            if r.cls != 'board':
                continue
            pts = G.resample(r.curve, 3.0)
            for i in range(0, len(pts) - 1, 2):
                a, b = pts[i], pts[i + 1]
                tx, ty = b[0] - a[0], b[1] - a[1]
                n = math.hypot(tx, ty) or 1.0
                nx, ny = -ty / n, tx / n
                hw = L.CLASSES['board']['road'] / 2
                d.line([C((a[0] - nx * hw, a[1] - ny * hw)), C((a[0] + nx * hw, a[1] + ny * hw))], fill=255, width=max(1, int(0.9 * ss)))
    cv.blend_full(draw_layer(cv, planks), (0.38, 0.27, 0.18), 0.75)

    def board_edges(d, C):
        for r in graph.roads:
            if r.cls != 'board':
                continue
            pts = G.resample(r.curve, 3.0)
            hw = L.CLASSES['board']['road'] / 2
            for sgn in (-1, 1):
                line = []
                for i, a in enumerate(pts):
                    b = pts[min(i + 1, len(pts) - 1)]
                    c0 = pts[max(i - 1, 0)]
                    tx, ty = b[0] - c0[0], b[1] - c0[1]
                    n = math.hypot(tx, ty) or 1.0
                    line.append(C((a[0] - ty / n * hw * sgn, a[1] + tx / n * hw * sgn)))
                d.line(line, fill=255, width=max(1, int(1.6 * ss)), joint='curve')
    cv.blend_full(draw_layer(cv, board_edges), (0.46, 0.33, 0.22), 0.9)

    def dashes(d, C):
        for r in graph.roads:
            cls = L.CLASSES[r.cls]
            if not cls.get('centre'):
                continue
            pts = r.curve
            total = G.poly_length(pts)
            on, off = 22.0, 34.0
            s = 40.0
            while s + on < total - 40:
                a, _ = G.point_at(pts, s)
                b, _ = G.point_at(pts, s + on)
                mid = G.lerp(a, b, 0.5)
                mx, my = int(mid[0] + R.ORIGIN[0]), int(mid[1] + R.ORIGIN[1])
                if 0 <= mx < R.IMG_W and 0 <= my < R.IMG_H and not masks.junction[my, mx]:
                    d.line([C(a), C(b)], fill=255, width=max(1, int(2.6 * ss)))
                s += on + off
    cv.blend_full(draw_layer(cv, dashes), WHITE, 0.9)
    # a few cracks and stains on the asphalt
    rng = random.Random(9)

    def cracks(d, C):
        for r in graph.roads:
            cls = L.CLASSES[r.cls]
            if r.cls in ('path', 'board'):
                continue
            pts = r.curve
            total = G.poly_length(pts)
            for _ in range(int(total / 150)):
                s = rng.uniform(20, total - 20)
                p, t = G.point_at(pts, s)
                nx, ny = -t[1], t[0]
                off = rng.uniform(-cls['road'] * 0.4, cls['road'] * 0.4)
                q = (p[0] + nx * off, p[1] + ny * off)
                pts2 = [q]
                a = rng.uniform(0, 6.28)
                for k in range(rng.randint(3, 6)):
                    a += rng.uniform(-0.8, 0.8)
                    q = (q[0] + math.cos(a) * rng.uniform(3, 8), q[1] + math.sin(a) * rng.uniform(3, 8))
                    pts2.append(q)
                d.line([C(p_) for p_ in pts2], fill=255, width=max(1, int(0.9 * ss)))
    cv.blend_full(draw_layer(cv, cracks), (0.12, 0.12, 0.13), 0.5)


def paint_rail(cv, L, rail=None):
    rail = rail or L.RAIL
    pts = rail['pts']
    w = rail['width']
    m = cv.line_mask(pts, w + 12, cap=False)
    cv.blend(m, cv.textured(m, (0.50, 0.47, 0.42), amp=(0.04, 0.05, 0.05), cells=(120, 18, 4), seed=31))
    m = cv.line_mask(pts, w, cap=False)
    cv.blend(m, cv.textured(m, BALLAST, amp=(0.04, 0.06, 0.07), cells=(100, 14, 3), seed=33))
    total = G.poly_length(pts)
    curve = G.resample(G.catmull_rom(pts)[0], 3.0)
    gauge = 9.0

    def sleepers(d, C):
        s = 0.0
        while s < total:
            p, t = G.point_at(curve, s)
            nx, ny = -t[1], t[0]
            a = (p[0] + nx * 11.5, p[1] + ny * 11.5)
            b = (p[0] - nx * 11.5, p[1] - ny * 11.5)
            d.line([C(a), C(b)], fill=255, width=max(1, int(2.3 * cv.ss)))
            s += 7.0
    cv.blend_full(draw_layer(cv, sleepers), SLEEPER, 0.9)
    for off in (-gauge / 2, gauge / 2):
        shifted = []
        for i, p in enumerate(curve):
            a = curve[max(0, i - 1)]; b = curve[min(len(curve) - 1, i + 1)]
            tx, ty = b[0] - a[0], b[1] - a[1]
            n = math.hypot(tx, ty) or 1
            shifted.append((p[0] - ty / n * off, p[1] + tx / n * off))
        m = cv.line_mask(shifted, 1.7, cap=False)
        cv.blend(m, RAIL)


def paint_area(cv, poly, base, amp=(0.05, 0.03, 0.02), cells=(160, 40, 9), seed=3, tint=None, edge=6.0, wobble=0.3):
    m = soft_mask(cv, poly, edge=edge, wobble=wobble, seed=seed)
    if m is None:
        return None
    cv.blend(m, cv.textured(m, base, amp, cells, seed, tint))
    return m


def paint_all(cv, L, B, masks, lots=(), sets=None):
    paint_land(cv, L)
    paint_fields(cv, L)

    def areas(only_far):
        for name, a in L.AREAS.items():
            kind = a.get('kind', name)
            if (kind == 'far') != only_far:
                continue
            col = dict(park=PARK_LAWN, school=(0.52, 0.66, 0.38), site=DIRT, wood=(0.31, 0.46, 0.28), station=CONCRETE, plaza=PAVEMENT, common=PARK_LAWN,
                       far=(0.36, 0.50, 0.34), market=(0.75, 0.73, 0.68)).get(kind)
            if col is not None:
                soft = kind in ('wood', 'far')
                paint_area(cv, a['poly'], col, seed=seed_of(name), edge=26 if soft else 6, wobble=1.7 if soft else 0.25)
    areas(False)
    paint_coast(cv, L)              # the sand and the sea over any area that reaches the shore; the far shore stands on the water
    areas(True)
    paint_lots(cv, lots)
    paint_roads(cv, L, B, masks)
    if sets is not None:
        sets.paint(cv, 'pre')                       # the ground under the set pieces (plazas, yards, embankments, water)
    paint_rail(cv, L)
    if getattr(L, 'RAIL2', None):
        paint_rail(cv, L, L.RAIL2)
    if sets is not None:
        sets.paint(cv, 'post')                      # the paint on top (crossings, platform edges, puddles)
