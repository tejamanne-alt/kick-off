# Kamakura's own homes, fences and garden walls (the Kamakura kit: kit_buildings_kam.py). See kit_buildings_kambase.py.
#
#   HouseTileKM     two storeys of beige mortar under a hipped roof of grey glazed kawara (ridge stack, onigawara), a kawara
#                   pent roof over the genkan, a balcony with futons on its rail, aluminium sliding windows with screens.
#   HouseMetalKM    white mortar below, dark-stained vertical boards above, a dark standing-seam gable to the street, a
#                   balcony with laundry poles, shutter boxes over the windows.
#   HouseOldKM      an old timber house: boards gone silver-grey and near black, wooden lattice (koshi) windows with shoji
#                   behind, a timber sliding door, kawara main roof and pent roof, deep eaves, moss on the north edge.
#   HouseShedKM     a mortar house with a corrugated lean-to shed on one side and a bicycle-wide gap beside it; rust from
#                   the sheets' fixings, water streaks, cracked and patched mortar.
#   HouseCarportKM  a newer house in siding under a slate hip, its door under a canopy, a carport (left empty for a kei car).
#   BungalowKM      one storey under an irimoya kawara roof, an engawa behind sliding glass, a stone step.
#   ApartmentKM     a two-storey wooden "apaato": steel stair and open walkway, six doors with meters and name slots,
#                   barred kitchen windows, bicycle space under the stair.
#   BoardFenceKM, BlockWallKM (4 m runs that tile end to end), GateKM (block posts and an accordion gate).
#
# Weathering (the brief's WEATHERING): black mould under the eaves, salt bloom, cracked mortar, rust from fixings, water
# streaks under sills, silvered and blackened timber, moss. It is painted into each building's own wall and roof maps by
# this module's features ('kh_*'): kit_buildings_atlas paints its own features and ignores others, so the painters below
# wrap its wall_map / roof_map and add theirs on top, for the buildings that ask for them only.
from kit_buildings_kambase import *
import kit_buildings_atlas as ATL
from kit_buildings_atlas import _ss, _mul, _blend, _noise
from kit_buildings_kambase import _c

# ---------------------------------------------------------------- the homes' own colours
KH_MAT = {
    'khbronze': (0, (0.30, 0.27, 0.24), 'white', 0.0),     # bronze-anodised aluminium (doors, frames)
    'khivory': (0, (0.86, 0.84, 0.77), 'white', 0.1),      # pipe ducts, gutters, plastic
    'khgrey': (0, (0.56, 0.57, 0.57), 'white', 0.1),
    'khporch': (0, (0.60, 0.56, 0.51), 'piece', 0.0),      # porch tiles
    'khplaster': (0, (0.86, 0.82, 0.72), 'grime', 0.0),    # old plaster panels (the walls' maps)
    'khcorr': (0, (0.66, 0.67, 0.66), 'grime', 0.0),       # corrugated sheet walls (rust from the walls' maps)
    'khcorrr': (0, (0.66, 0.67, 0.66), 'roof', 0.0),       # corrugated roof sheets (rust from the roof map)
    'khsteel': (0, (0.30, 0.31, 0.32), 'white', 0.1),
    'khhyd1': (0, (0.40, 0.50, 0.86), 'white', 0.25), 'khhyd2': (0, (0.60, 0.48, 0.84), 'white', 0.25),
    'khhyd3': (0, (0.88, 0.58, 0.74), 'white', 0.25),
    'khpotp': (0, (0.64, 0.36, 0.22), 'white', 0.3), 'khpotg': (0, (0.26, 0.34, 0.28), 'white', 0.3),
    'khwood': (0, (0.62, 0.48, 0.34), 'white', 0.15),       # oiled timber (steps, frames)
    'khfloor': (0, (0.52, 0.38, 0.26), 'white', 0.0),       # polished engawa boards
    'khpoly': (0, (0.60, 0.67, 0.66), 'white', 0.0),        # weathered polycarbonate sheet (carport, canopies)
}
for _k, _v in KH_MAT.items():
    if _k not in MAT:
        MAT[_k] = _v; MATS.append(_k); MID[_k] = len(MATS) - 1

# invented family names on the name plates (表札)
NAMES = {'HouseTileKM': '森川', 'HouseMetalKM': '浜田', 'HouseOldKM': '磯村', 'HouseShedKM': '坂口', 'HouseCarportKM': '杉浦',
         'BungalowKM': '竹内'}
ROOMS = ('101', '102', '103', '201', '202', '203')

TILES = [('kh_np_' + k, 48, 128) for k in NAMES] + [
    ('kh_frost', 128, 256), ('kh_screen', 128, 256), ('kh_shoji', 192, 256), ('kh_rooms', 384, 64), ('kh_slot', 64, 32),
    ('kh_apt', 384, 96), ('kh_futon', 256, 128), ('kh_postbank', 192, 128), ('kh_intercom', 48, 64),
]


# ================================================================ weathering painted into the buildings' own maps
def _hash(a, b, c=0.0):
    t = np.sin(a * 12.9898 + b * 78.233 + c * 37.719) * 43758.5453
    return t - np.floor(t)


def _path(rng, x, z, ang, length, wob=0.35):
    pts = [(x, z)]
    n = max(3, int(length / 0.07))
    for _ in range(n):
        ang += rng.normal(0, wob)
        x += math.cos(ang) * length / n; z += math.sin(ang) * length / n
        pts.append((x, z))
    return pts


def _line(sub, A, Z, pts, width, col, alpha, ppm):
    """A soft line of width (m, at least ~1.2 px) along pts, multiplied toward col."""
    lo_a, hi_a = min(p[0] for p in pts) - width - 0.05, max(p[0] for p in pts) + width + 0.05
    lo_z, hi_z = min(p[1] for p in pts) - width - 0.05, max(p[1] for p in pts) + width + 0.05
    cols = np.nonzero((A[0] >= lo_a) & (A[0] <= hi_a))[0]
    rows = np.nonzero((Z[:, 0] >= lo_z) & (Z[:, 0] <= hi_z))[0]
    if len(cols) == 0 or len(rows) == 0: return sub
    sl = (slice(rows[0], rows[-1] + 1), slice(cols[0], cols[-1] + 1))
    a, zz = A[sl], Z[sl]
    d = np.full(a.shape, 9.0)
    for p0, p1 in zip(pts[:-1], pts[1:]):
        d = np.minimum(d, ATL._seg(a, zz, p0, p1))
    w = max(width, 1.2 / ppm)
    sub[sl] = _mul(sub[sl], _ss(w, w * 0.35, d).astype(np.float32), col, alpha)
    return sub


def _wall_feats(B, mp, sub, U, V, w, h):
    feats = [(k, kw) for k, kw in B.feats.get(mp, []) if k.startswith('kh_')]
    if not feats: return sub
    a0, a1, b0, b1 = B.maps[mp]
    A = a0 + U * (a1 - a0); Z = b0 + V * (b1 - b0)
    ppm = w / (a1 - a0)
    H_, W_ = U.shape
    seed = (sum(map(ord, B.name)) * 11 + sum(map(ord, mp))) % 9973
    r = np.random.default_rng(seed)
    nS = _noise(H_, W_, ((a1 - a0) / 0.05, (b1 - b0) / 1.2), seed + 21)       # vertical streaks
    nM = _noise(H_, W_, ((a1 - a0) / 0.7, (b1 - b0) / 0.7), seed + 22)
    nF = _noise(H_, W_, ((a1 - a0) / 0.12, (b1 - b0) / 0.12), seed + 23)

    def inx(s0, s1, soft=0.12):
        return _ss(-soft, soft, A - s0) * _ss(-soft, soft, s1 - A)
    for kind, kw in feats:
        k = kw.get('k', 1.0)
        if kind == 'kh_tone':          # a rectangle's overall tone (makes room for lighter weathering on dark timber)
            m = (A >= kw['a0']) & (A <= kw['a1']) & (Z >= kw['b0']) & (Z <= kw['b1'])
            sub = np.where(m[..., None], sub * np.array(kw['col'], np.float32), sub)
        elif kind == 'kh_grain':       # timber boards: each its own tone, grain, dark joints, silvered low, near black high
            s0, s1, z0, z1, bw = kw['a0'], kw['a1'], kw['b0'], kw['b1'], kw.get('bw', 0.15)
            m = (A >= s0) & (A <= s1) & (Z >= z0) & (Z <= z1)
            vert = kw.get('vert', True)
            q = ((A - s0) if vert else (Z - z0)) / bw
            along = Z if vert else A
            idx = np.floor(q); fq = q - idx
            tone = _hash(idx, kw.get('seed', 1.0))
            grain = np.sin(along * (37.0 + 23 * tone) + idx * 5.1 + nF * 3.0) * 0.5 + 0.5
            hz = np.clip((Z - z0) / max(z1 - z0, 0.1), 0, 1)
            dark, silver = kw.get('dark', 0.45), kw.get('silver', 0.95)
            # silver where the sun and rain reach (low, and every third board), dark under the eaves
            sv = np.clip(0.55 * (1 - hz) + 0.35 * (tone > 0.62) + 0.25 * nM - 0.1, 0, 1)
            f = dark + (silver - dark) * sv
            f = f * (0.92 + 0.08 * grain) * (0.94 + 0.12 * tone)
            jt = np.minimum(fq, 1 - fq) * bw
            f = f * (1 - 0.45 * _ss(1.6 / ppm, 0.5 / ppm, jt))
            col = np.stack([f * 1.0, f * 0.985, f * 0.96], -1)
            sub = np.where(m[..., None], sub * col, sub)
        elif kind == 'kh_mould':       # black mould under eaves, balconies and ledges
            s0, s1, zb, L = kw['a0'], kw['a1'], kw['b'], kw['length']
            t = np.clip((zb - Z) / L, 0, 1)
            m = (1 - t) ** 1.4 * (Z <= zb + 0.01) * (0.3 + 0.7 * nS) * (0.7 + 0.3 * nM)
            m = m + _ss(zb - 0.12, zb, Z) * (Z <= zb + 0.01) * 0.5
            sub = _mul(sub, (inx(s0, s1) * m).astype(np.float32), (0.28, 0.3, 0.26), 0.9 * k)
        elif kind == 'kh_streak':      # long rain streaks running down from a ledge
            s0, s1, zb, L = kw['a0'], kw['a1'], kw['b'], kw['length']
            for _ in range(max(2, int((s1 - s0) / kw.get('every', 0.25)))):
                x = r.uniform(s0, s1); LL = L * r.uniform(0.35, 1.0); wd = r.uniform(0.015, 0.05)
                m = _ss(wd, 0.0, np.abs(A - x)) * np.clip((Z - (zb - LL)) / LL, 0, 1) ** 1.5 * (Z < zb)
                sub = _mul(sub, (m * (0.5 + 0.5 * nS)).astype(np.float32), (0.6, 0.6, 0.58), 0.75 * k)
        elif kind == 'kh_salt':        # sea-salt bloom: pale crusty haze, heaviest low down and at the corners
            s0, s1, z0, z1 = kw['a0'], kw['a1'], kw['b0'], kw['b1']
            m = _ss(0.45, 0.75, nM * 0.65 + nF * 0.35) * inx(s0, s1, 0.3) * _ss(z1, z0, Z) * (Z >= z0 - 0.05)
            sub = _blend(sub, m.astype(np.float32), kw.get('col', (0.98, 0.98, 0.96)), 0.6 * k)
            sp = ((nF > 0.78) & (nM > 0.4)).astype(np.float32) * inx(s0, s1, 0.3) * _ss(z1, z0, Z)
            sub = _blend(sub, sp, (1.0, 1.0, 0.98), 0.35 * k)
        elif kind == 'kh_crack':       # cracks in the mortar, from the openings' corners; some filled and painted over
            for (x, z, ang, length) in kw['cracks']:
                pts = _path(r, x, z, ang, length)
                if kw.get('repair'):
                    sub = _line(sub, A, Z, pts, 0.025, (0.9, 0.9, 0.89), 0.55, ppm)
                sub = _line(sub, A, Z, pts, 0.6 / ppm, (0.42, 0.4, 0.38), 0.85 * k, ppm)
                if r.random() < 0.6:   # a branch
                    j = int(r.integers(1, len(pts) - 1))
                    sub = _line(sub, A, Z, _path(r, pts[j][0], pts[j][1], ang + r.choice((-0.9, 0.9)), length * 0.4),
                                0.5 / ppm, (0.5, 0.48, 0.46), 0.7 * k, ppm)
        elif kind == 'kh_rust':        # rust bleeding from fixings
            L = kw.get('length', 0.5)
            for (x, z) in kw['pts']:
                LL = L * r.uniform(0.5, 1.2); wd = r.uniform(0.012, 0.03)
                m = _ss(wd, 0.0, np.abs(A - x)) * np.clip((Z - (z - LL)) / LL, 0, 1) ** 1.2 * (Z <= z + 0.01)
                m = np.maximum(m, _ss(0.025, 0.0, np.hypot(A - x, Z - z)))
                sub = _mul(sub, (m * (0.6 + 0.4 * nF)).astype(np.float32), (0.62, 0.36, 0.2), 0.85 * k)
        elif kind == 'kh_rustfield':   # rust patches over sheet metal (seams, laps, the foot)
            s0, s1, z0, z1 = kw['a0'], kw['a1'], kw['b0'], kw['b1']
            m = _ss(0.6, 0.8, nM * 0.5 + nF * 0.5) * inx(s0, s1, 0.05) * (Z >= z0) * (Z <= z1)
            m = np.maximum(m, _ss(z0 + 0.35, z0, Z) * (0.4 + 0.6 * nF) * inx(s0, s1, 0.05) * (Z >= z0))
            sub = _mul(sub, m.astype(np.float32), (0.66, 0.42, 0.28), 0.8 * k)
        elif kind == 'kh_blocks':      # concrete blocks: joints, a tone per block, lime run from the joints
            s0, s1, z0, z1, bw, bh = kw['a0'], kw['a1'], kw['b0'], kw['b1'], kw.get('bw', 0.4), kw.get('bh', 0.2)
            m = (A >= s0) & (A <= s1) & (Z >= z0) & (Z <= z1)
            row = np.floor((Z - z0) / bh); xo = A - s0 + (row % 2) * bw * 0.5 * kw.get('bond', 1.0)
            col = np.floor(xo / bw)
            tone = _hash(col, row, 3.0)
            jz = np.minimum((Z - z0) % bh, bh - (Z - z0) % bh); jx = np.minimum(xo % bw, bw - xo % bw)
            f = (0.96 + 0.05 * tone) * (1 - 0.2 * _ss(0.8 / ppm, 0.2 / ppm, np.minimum(jz, jx)))
            sub = np.where(m[..., None], sub * f[..., None].astype(np.float32), sub)
            lime = ((_hash(col, row, 9.0) > 0.8) & (xo % bw < bw * 0.5)).astype(np.float32)
            lm = lime * _ss(0.03, 0.0, np.abs((xo % bw) - bw * 0.3)) * np.clip(1 - ((Z - z0) % bh) / bh, 0, 1) * m
            sub = _blend(sub, lm.astype(np.float32), (1.0, 1.0, 0.98), 0.4)
        elif kind == 'kh_moss':        # moss and grime at the foot of a wall
            s0, s1, zb = kw['a0'], kw['a1'], kw['b']
            m = _ss(zb, zb * 0.2, Z) * (0.35 + 0.65 * _ss(0.3, 0.7, nM)) * (0.6 + 0.4 * nF) * inx(s0, s1, 0.05)
            sub = _mul(sub, m.astype(np.float32), (0.46, 0.58, 0.30), 0.85 * k)
            sub = _mul(sub, (_ss(0.12, 0.0, Z) * inx(s0, s1, 0.05)).astype(np.float32), (0.42, 0.42, 0.38), 0.6 * k)
        elif kind == 'kh_siding':      # ceramic siding: shallow grooves, a tone per panel, the vertical joints
            s0, s1, z0, z1 = kw['a0'], kw['a1'], kw['b0'], kw['b1']
            m = (A >= s0) & (A <= s1) & (Z >= z0) & (Z <= z1)
            ph, pw = kw.get('ph', 0.455), kw.get('pw', 3.03)
            row = np.floor((Z - z0) / ph); col = np.floor((A - s0 + (row % 2) * pw * 0.5) / pw)
            tone = _hash(col, row, 5.0)
            g = (Z - z0) % (ph / 3.0)
            f = (0.95 + 0.06 * tone) * (1 - 0.18 * _ss(1.4 / ppm, 0.4 / ppm, np.minimum(g, ph / 3.0 - g)))
            xo = (A - s0 + (row % 2) * pw * 0.5) % pw
            f = f * (1 - 0.3 * _ss(1.5 / ppm, 0.4 / ppm, np.minimum(xo, pw - xo)))
            sub = np.where(m[..., None], sub * f[..., None].astype(np.float32), sub)
    return sub


def _roof_feats(B, mp, sub, U, V, w, h):
    feats = [(k, kw) for k, kw in B.feats.get(mp, []) if k.startswith('kh_')]
    if not feats: return sub
    a0, a1, b0, b1 = B.maps[mp]
    X = a0 + U * (a1 - a0); Y = b0 + V * (b1 - b0)
    ppm = w / (a1 - a0)
    H_, W_ = U.shape
    seed = (sum(map(ord, B.name)) * 5 + 7) % 9973
    n1 = _noise(H_, W_, ((a1 - a0) / 1.2, (b1 - b0) / 1.2), seed + 31)
    n2 = _noise(H_, W_, ((a1 - a0) / 0.35, (b1 - b0) / 0.35), seed + 32)
    n3 = _noise(H_, W_, ((a1 - a0) / 0.1, (b1 - b0) / 0.1), seed + 33)
    for kind, kw in feats:
        if kind == 'kh_roof':
            lx, ly = (X, Y) if kw['axis'] == 'x' else (Y, X)
            LX0, LX1, LY0, LY1, hh, dg, form = kw['LX0'], kw['LX1'], kw['LY0'], kw['LY1'], kw['h'], kw['dg'], kw['form']
            inside = (lx >= LX0 - 0.03) & (lx <= LX1 + 0.03) & (ly >= LY0 - 0.03) & (ly <= LY1 + 0.03)
            if not inside.any(): continue
            dF, dB, dL, dR = ly - LY0, LY1 - ly, lx - LX0, LX1 - lx
            if form == 'pent':
                dB = np.full_like(dB, 99.0)
            dFB = np.minimum(dF, dB)
            if form in ('gable', 'pent'):
                endL = np.zeros(lx.shape, bool); endR = endL
            else:
                endL = (dL <= dFB) & (dL <= dg); endR = (dR <= dFB) & (dR <= dg)
            end = endL | endR
            d = np.clip(np.where(endL, dL, np.where(endR, dR, dFB)), 0, None)
            s = np.where(end, ly - LY0, lx - LX0)
            backside = (~end) & (dB < dF)
            kind_ = kw['rk']
            if kind_ == 'kawara':
                q = s / 0.3; cell = np.floor(q); fq = q - cell
                cq = d / 0.26; course = np.floor(cq); fc = cq - course
                tone = _hash(cell, course, 1.0 + end * 2.0)
                f = 0.64 + 0.13 * tone
                f = f * (1 - 0.3 * _ss(0.16, 0.0, fc)) * (1 + 0.07 * _ss(0.35, 0.15, fc) * (fc > 0.15))
                f = f * (1 - 0.1 * _ss(0.35, 0.05, np.abs(fq - 0.15)))                 # the pans a little darker
                f = f * (1 + 0.1 * _ss(0.2, 0.0, np.abs(fq - 0.62)))                   # the rolls catch the sky
                hue = np.stack([1 + 0.03 * (tone - 0.5), np.ones_like(tone), 1 + 0.05 * (0.5 - tone)], -1)
                val = f[..., None] * hue
                # dirt washed down the pans to the eaves, a darker eave course
                dirt = _ss(0.25, 0.0, np.abs(fq - 0.15)) * _ss(1.6, 0.0, d) * (0.4 + 0.6 * n2)
                val = val * (1 - 0.25 * dirt)[..., None]
                val = val * (1 - 0.12 * _ss(0.35, 0.0, d))[..., None]
                # pale lichen freckles
                lich = ((n3 > 0.8) & (n2 > 0.5)).astype(np.float32) * (0.5 + 0.5 * n1)
                val = _blend(val, lich, (0.9, 0.9, 0.86), 0.5)
                if kw.get('moss'):
                    side = backside if kw['moss'] == 'back' else (~end & ~backside)
                    m = side * _ss(1.8, 0.2, d) * _ss(0.42, 0.7, n2 * 0.6 + n1 * 0.4) * (0.6 + 0.4 * n3)
                    m = np.maximum(m, side * _ss(0.3, 0.0, np.abs(fq - 0.15)) * _ss(1.2, 0.0, d) * (n1 > 0.45))
                    val = _blend(val, m.astype(np.float32), (0.62, 0.84, 0.38), 0.9)
            elif kind_ == 'seam':
                f = 0.9 + 0.06 * n1 + 0.03 * (n3 - 0.5)
                q = s / 0.45; fq = q - np.floor(q)
                f = f * (1 - 0.18 * _ss(0.06, 0.0, np.minimum(fq, 1 - fq)))
                f = f * (1 + 0.08 * _ss(1.2, 0.0, hh - d))                             # chalky toward the ridge
                streak = _ss(0.6, 0.85, _noise(H_, W_, ((a1 - a0) / 0.08, (b1 - b0) / 1.5), seed + 41)) * _ss(1.5, 0.0, d)
                f = f * (1 - 0.12 * streak)
                val = np.repeat(f[..., None], 3, -1)
            else:   # slate
                cq = d / 0.22; course = np.floor(cq); fc = cq - course
                xo = s + (course % 2) * 0.45; cell = np.floor(xo / 0.9)
                tone = _hash(cell, course, 4.0)
                f = (0.8 + 0.14 * tone) * (1 - 0.32 * _ss(0.1, 0.0, fc))
                jx = np.minimum(xo % 0.9, 0.9 - xo % 0.9)
                f = f * (1 - 0.35 * _ss(1.4 / ppm, 0.3 / ppm, jx))
                f = f * (0.95 + 0.05 * n2)
                val = np.repeat(f[..., None], 3, -1) * np.array((0.99, 1.0, 1.03))
            sub = np.where(inside[..., None], sub * val.astype(np.float32), sub)
        elif kind == 'kh_corr':        # corrugated sheet roof falling along x or y: its ridges, rust from the fixings
            x0, x1, y0, y1, ax = kw['x0'], kw['x1'], kw['y0'], kw['y1'], kw['fall']
            inside = (X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1)
            across, down = (Y, X) if ax == 'x' else (X, Y)
            low = x0 if ax == 'x' else y0
            f = 0.86 + 0.14 * (np.sin(across / 0.076 * 2 * math.pi) * 0.5 + 0.5)
            f = f * (0.92 + 0.08 * n1)
            val = np.repeat(f[..., None], 3, -1)
            rr = np.random.default_rng(seed + 5)
            span = (y0, y1) if ax == 'x' else (x0, x1)
            for pr in kw['purlins']:           # fixing rows (distance along the fall from the low edge)
                for a in np.arange(span[0] + 0.12, span[1], 0.3):
                    if rr.random() < 0.35: continue
                    L = rr.uniform(0.15, 0.6); wd = rr.uniform(0.01, 0.025)
                    dd = down - (low + pr)
                    m = _ss(wd, 0.0, np.abs(across - a)) * np.clip(1 + dd / L, 0, 1) ** 1.3 * (dd <= 0.01)
                    m = np.maximum(m, _ss(0.03, 0.0, np.hypot(across - a, dd)))
                    val = _mul(val, (m * (0.6 + 0.4 * n3)).astype(np.float32), (0.66, 0.4, 0.24), 0.9)
            m = _ss(0.55, 0.8, n1 * 0.5 + n2 * 0.5) * 0.7 + _ss(0.5, 0.0, down - low) * (0.4 + 0.6 * n3)
            val = _mul(val, m.astype(np.float32), (0.7, 0.5, 0.36), 0.75)
            sub = np.where(inside[..., None], sub * val.astype(np.float32), sub)
    return sub


def _wrap(orig, post):
    def wrapped(B, mp):
        f0 = orig(B, mp)
        if not any(k.startswith('kh_') for k, _ in B.feats.get(mp, [])): return f0

        def f(U, V, w, h):
            return np.clip(post(B, mp, f0(U, V, w, h), U, V, w, h), 0, 1)
        return f
    wrapped._kh = True
    return wrapped


if not getattr(ATL.wall_map, '_kh', False):
    ATL.wall_map = _wrap(ATL.wall_map, _wall_feats)
    ATL.roof_map = _wrap(ATL.roof_map, _roof_feats)


# ================================================================ shared pieces
_box = box


def lamp_at(B, p, name='Lamp'):
    B.lamps.append({'name': name, 'center': [round(p.x, 3), round(p.y, 3), round(p.z, 3)]})


def mould(B, mp, a0, a1, b, length=0.8, k=1.0):
    B.feat(mp, 'kh_mould', a0=a0, a1=a1, b=b, length=length, k=k)


def kh_window(B, wf, u0, u1, v0, v1, screen='right', box=None, grille=False, frosted=False, glass='glass1',
              frame='kmalu', depth=0.12, register=True, sill=True, tobukuro=None, streak=1.0, gp=0.085):
    """A Japanese aluminium sliding window: a shallow reveal, the frame, two sashes on their rails (the right one in
    front), an insect screen over one half on the outer rail, the sill's flashing; a shutter box over it (box='shutter'),
    a side box for wooden storm shutters (tobukuro='left'/'right'), or a bar grille in front (grille=True)."""
    mb = MB()
    reveal(mb, u0, u1, v0, v1, depth, mat='reveal', bottom=True)
    zf = -depth + 0.06
    fw = 0.04
    o = (u0, v0, u1, v1); i = (u0 + fw, v0 + fw, u1 - fw, v1 - fw)
    ring(mb, o, i, zf, zf, frame, 'front')
    ring(mb, i, i, zf, -depth + 0.005, frame, 'in', 0.8)
    um = (i[0] + i[2]) / 2
    sw = 0.032
    region = 'kh_frost' if frosted else glass
    for a, b, z in ((i[0], um + 0.02, zf - 0.04), (um - 0.02, i[2], zf - 0.016)):
        so = (a, i[1], b, i[3]); si = (a + sw, i[1] + sw, b - sw, i[3] - sw)
        ring(mb, so, si, z, z, frame, 'front')
        ring(mb, si, si, z, z - 0.012, frame, 'in', 0.8)
        mb.face([(si[0], si[1], z - 0.012), (si[2], si[1], z - 0.012), (si[2], si[3], z - 0.012), (si[0], si[3], z - 0.012)],
                'glass', (0, 0, 1), 1.0, glass_uv(si, region))
        mb.face([(b, i[1], z - 0.03), (b, i[1], z), (b, i[3], z), (b, i[3], z - 0.03)], frame, (1, 0, 0), 0.7)
    if screen and not frosted:
        a, b = (um - 0.02, i[2]) if screen == 'right' else (i[0], um + 0.02)
        z = zf - 0.004
        so = (a, i[1] + 0.005, b, i[3] - 0.005); si = (a + 0.022, i[1] + 0.027, b - 0.022, i[3] - 0.027)
        ring(mb, so, si, z, z, frame, 'front')
        mb.face([(si[0], si[1], z - 0.003), (si[2], si[1], z - 0.003), (si[2], si[3], z - 0.003), (si[0], si[3], z - 0.003)],
                'tex', (0, 0, 1), 1.0, glass_uv(si, 'kh_screen'))
    if grille:
        zg0, zg1 = 0.02, 0.055
        xs = np.arange(u0 + 0.05, u1 - 0.03, gp)
        for x in xs:
            bar(mb, x - 0.011, v0 - 0.02, x + 0.011, v1 + 0.02, zg0, zg1, frame)
        for v in (v0 - 0.04, v1 - 0.0):
            bar(mb, u0 - 0.04, v, u1 + 0.04, v + 0.04, zg0, zg1 + 0.006, frame, ends=True)
        for x in (u0 - 0.04, u1 + 0.02):
            mb.face([(x, v0 - 0.04, 0.0), (x, v0 - 0.04, zg1), (x, v1 + 0.04, zg1), (x, v1 + 0.04, 0.0)], frame,
                    (-1 if x < u0 else 1, 0, 0), 0.75)
    put(B, wf, mb.bm())
    if sill:
        put(B, wf, fbox((u0 - 0.035, v0 - 0.035, -0.02), (u1 + 0.035, v0 + 0.004, 0.055), 0.008, frame))
        a0, b0 = wf.ab(u0, v0 - 0.035); a1, _ = wf.ab(u1, v0)
        B.feat(wf.mp, 'streak', a0=min(a0, a1), a1=max(a0, a1), b=b0, length=0.9 + 0.5 * B.rng.random(), k=streak)
        B.feat(wf.mp, 'kh_streak', a0=min(a0, a1) + 0.05, a1=max(a0, a1) - 0.05, b=b0, length=1.2, k=0.6 * streak, every=0.3)
    if box == 'shutter':
        put(B, wf, fbox((u0 - 0.06, v1 + 0.01, 0.0), (u1 + 0.06, v1 + 0.25, 0.17), 0.02, frame))
        for x in (u0 - 0.055, u1 + 0.005):
            put(B, wf, fbox((x, v0 - 0.02, 0.0), (x + 0.05, v1 + 0.01, 0.06), 0.008, frame))
        a0, b0 = wf.ab(u0 - 0.06, v1); a1, _ = wf.ab(u1 + 0.06, v1)
        B.feat(wf.mp, 'ao', a0=min(a0, a1), a1=max(a0, a1), b=v1 + 0.01, length=0.22, k=0.35)
    if tobukuro:
        tw = (u1 - u0) * 0.5 + 0.06
        x0 = u1 + 0.02 if tobukuro == 'right' else u0 - 0.02 - tw
        put(B, wf, fbox((x0, v0 - 0.04, 0.0), (x0 + tw, v1 + 0.08, 0.17), 0.015, 'accentp'))
        for k in range(1, 4):
            x = x0 + tw * k / 4
            put(B, wf, _box((x - 0.006, v0, 0.17), (x + 0.006, v1 + 0.04, 0.178), 'accentw', skip=('-z',)))
        put(B, wf, fbox((u0 - 0.04, v1 + 0.02, 0.0), (u1 + 0.04, v1 + 0.1, 0.16), 0.01, frame))
    if register:
        c3 = wf.P((u0 + u1) / 2, (v0 + v1) / 2, zf - 0.03)
        B.windows.append({'center': [round(c3.x, 3), round(c3.y, 3), round(c3.z, 3)], 'size': [round(u1 - u0, 3), round(v1 - v0, 3)], 'wall': wf.mp})


def kh_genkan(B, wf, u0, u1, v0, mat='khbronze', frame='khbronze', bars=4, double=True, h=2.1, region='kh_frost'):
    """The entrance: a sliding door of two glazed leaves (frosted, with vertical bars), made with door() so the game finds
    Attach.Door."""
    v1 = v0 + h
    door(B, wf, u0, u1, v0, v1, depth=0.14, mat=mat, panels=((1, 0),), glass=0.9, casing=False, lining=frame, knob=frame,
         double=double, glass_region=region, name='Door')
    lf = wf.off(-0.14 + 0.035)
    mb = MB()
    lw = 0.06
    leaves = [(u0 + lw, (u0 + u1) / 2), ((u0 + u1) / 2, u1 - lw)] if double else [(u0 + lw, u1 - lw)]
    for li, (a, b) in enumerate(leaves):
        zz = 0.0 if li == 0 else 0.012
        for k in range(bars):
            x = a + (b - a) * (k + 1) / (bars + 1)
            bar(mb, x - 0.012, v0 + 0.25, x + 0.012, v1 - 0.12, zz, zz + 0.018, frame)
        bar(mb, a + 0.05, v0 + 0.22, b - 0.05, v0 + 0.27, zz, zz + 0.02, frame)
    put(B, lf, mb.bm())
    a0, b0 = wf.ab(u0, v1); a1, _ = wf.ab(u1, v1)
    B.feat(wf.mp, 'ao', a0=min(a0, a1), a1=max(a0, a1), b=v1 + 0.02, length=0.2, k=0.3)


def porch_light(B, wf, x, y):
    put(B, wf, fbox((x - 0.07, y - 0.1, 0.0), (x + 0.07, y + 0.1, 0.03), 0.01, 'khbronze'))
    put(B, wf, fbox((x - 0.055, y - 0.08, 0.03), (x + 0.055, y + 0.07, 0.12), 0.015, 'lamp'))
    put(B, wf, fbox((x - 0.065, y + 0.07, 0.03), (x + 0.065, y + 0.1, 0.13), 0.01, 'khbronze'))
    lamp_at(B, wf.P(x, y, 0.12))
    a, b = wf.ab(x, y)
    B.feat(wf.mp, 'glow', a=a, b=b, r=0.35)


def name_plate(B, wf, x, y, key, w=0.11, h=0.29, back='khwood'):
    """A house name plate (表札): a timber or stone plate with the family's name in black."""
    put(B, wf, fbox((x - w / 2 - 0.012, y - h / 2 - 0.012, 0.0), (x + w / 2 + 0.012, y + h / 2 + 0.012, 0.025), 0.006, back))
    decal(B, wf, x - w / 2, x + w / 2, y - h / 2, y + h / 2, 0.026, 'kh_np_' + key)


def intercom(B, wf, x, y):
    put(B, wf, fbox((x - 0.055, y - 0.08, 0.0), (x + 0.055, y + 0.08, 0.035), 0.012, 'khivory'))
    decal(B, wf, x - 0.045, x + 0.045, y - 0.065, y + 0.065, 0.036, 'kh_intercom')


def post_box(B, wf, x, y, mat='kmalu'):
    put(B, wf, fbox((x - 0.17, y, 0.0), (x + 0.17, y + 0.36, 0.11), 0.015, mat))
    put(B, wf, box((x - 0.11, y + 0.26, 0.11), (x + 0.11, y + 0.29, 0.116), 'black', skip=('-z',)))
    put(B, wf, fbox((x - 0.13, y + 0.04, 0.11), (x + 0.13, y + 0.2, 0.118), 0.004, mat))


def gas_meter(B, wf, x, y, floor=0.0):
    """A city-gas meter on the wall, its pipe down into the ground and its branch into the wall."""
    put(B, wf, fbox((x - 0.15, y, 0.04), (x + 0.15, y + 0.34, 0.2), 0.025, 'khivory'))
    put(B, wf, box((x - 0.09, y + 0.18, 0.2), (x + 0.09, y + 0.27, 0.205), 'glass', skip=('-z',)))
    put(B, wf, tube([(x - 0.07, y, 0.12), (x - 0.07, floor + 0.3, 0.12), (x - 0.07, floor - 0.05, 0.12)], 0.022, 'pipe', 5))
    put(B, wf, tube([(x + 0.07, y + 0.34, 0.12), (x + 0.07, y + 0.5, 0.12), (x + 0.3, y + 0.5, 0.12), (x + 0.3, y + 0.5, 0.0)],
                    0.02, 'pipe', 5))
    a0, b0 = wf.ab(x - 0.15, y); a1, b1 = wf.ab(x + 0.15, y + 0.34)
    B.feat(wf.mp, 'ao_rect', a0=min(a0, a1), a1=max(a0, a1), b0=b0, b1=b1, k=0.25)


def wall_ac(B, wf, x, y, duct_to=None):
    """An air-conditioner's outdoor unit on wall brackets, with its pipes in an ivory duct up to the wall."""
    ac_unit(B, wf, x, y, 0.0, w=0.78, h=0.55, d=0.28, brackets=True, mat='whitep', pipe=False)
    dx = x + 0.39
    top = duct_to if duct_to is not None else y + 1.0
    put(B, wf, fbox((dx - 0.0, y + 0.18, 0.0), (dx + 0.09, y + 0.3, 0.2), 0.01, 'khivory'))
    put(B, wf, fbox((dx + 0.02, y + 0.18, 0.0), (dx + 0.11, top, 0.08), 0.012, 'khivory'))
    put(B, wf, tube([(x - 0.3, y + 0.02, 0.14), (x - 0.3, y - 0.25, 0.14), (x - 0.25, y - 0.45, 0.16)], 0.012, 'khgrey', 4))


def hydrangea(B, P, r=0.42, seed=0, cols=('khhyd1', 'khhyd2')):
    """A hydrangea bush (Kamakura's flower): dark leaves and round mopheads."""
    rng = np.random.default_rng(seed)
    x, y, z = P
    for k in range(3):
        a = 2 * math.pi * k / 3 + rng.random()
        B.add(blob((x + math.cos(a) * r * 0.45, y + math.sin(a) * r * 0.3, z + r * 0.55), (r * 0.7, r * 0.55, r * 0.6),
                   ['leafd', 'leaf', 'leafd'][k], 6, 2, seed * 7 + k, 0.18, flat_bottom=0.2))
    for k in range(6):
        a = 2 * math.pi * k / 6 + rng.random() * 0.6
        rr = r * rng.uniform(0.2, 0.27)
        c = (x + math.cos(a) * r * 0.62, y + math.sin(a) * r * 0.4 - r * 0.15, z + r * (0.75 + 0.35 * rng.random()))
        B.add(blob(c, (rr, rr, rr * 0.9), cols[k % len(cols)], 6, 2, seed * 13 + k, 0.12))


def concrete_pad(B, x0, x1, y0, y1, z=0.03, mat='conc'):
    B.add(box((x0, y0, 0.0), (x1, y1, z), mat, skip=('-z',)))


# ================================================================ roofs
P_TILE = 0.3                                   # the kawara's channel pitch
WAVE = ((0.0, -1.0), (0.36, -0.45), (0.64, 1.0))


def _wv(s, amp):
    if not amp: return 0.0
    q = (s / P_TILE) % 1.0
    n = len(WAVE)
    for i in range(n):
        a, va = WAVE[i]; b, vb = WAVE[i + 1] if i < n - 1 else (1.0, WAVE[0][1])
        if a <= q <= b: return amp * (va + (vb - va) * (q - a) / (b - a))
    return amp * WAVE[0][1]


def _samples(a, b, amp, kinks=()):
    xs = [a, b] + [k for k in kinks if a + 1e-3 < k < b - 1e-3]
    if amp:
        n = math.floor(a / P_TILE) - 1
        while n * P_TILE < b + P_TILE:
            for f, _ in WAVE:
                s = (n + f) * P_TILE
                if a + 0.01 < s < b - 0.01: xs.append(s)
            n += 1
    xs = sorted(xs)
    out = []
    for s in xs:
        if not out or s - out[-1] > 0.004: out.append(s)
    return out


ONI = [(-0.27, 0.0), (0.27, 0.0), (0.29, 0.15), (0.26, 0.33), (0.19, 0.46), (0.09, 0.55), (0.0, 0.62), (-0.09, 0.55),
       (-0.19, 0.46), (-0.26, 0.33), (-0.29, 0.15)]


def kh_roof(B, X0, X1, Y0, Y1, ze, k, kind='kawara', form='hip', axis='x', dg=1.6, e=0.3, t=0.12, moss=None,
            gable_mat='khplaster', barge='accent', soffit='soffit', mat='roof', fmap='roof', gutter=True, oni=1.0):
    """A roof over the plan rectangle [X0, X1] x [Y0, Y1] (eaves included), its eaves' underside at ze, rising k per metre.
    form: 'hip', 'gable', 'irimoya' (hipped below, gabled above: the gables stand dg in from the ends and overhang e) or
    'pent' (one slope from the eave at Y0 up to the wall at Y1). kind: 'kawara' (rolled tiles in real channels, a stacked
    ridge with onigawara at its ends, hip ridges, rolled verges), 'seam' (standing-seam metal) or 'slate'.
    axis 'x': the ridge runs along X; 'y': along Y. Returns the ridge's top."""
    sw = axis == 'y'
    LX0, LX1, LY0, LY1 = (Y0, Y1, X0, X1) if sw else (X0, X1, Y0, Y1)
    pent = form == 'pent'
    hh = (LY1 - LY0) if pent else (LY1 - LY0) / 2
    ym = LY1 if pent else (LY0 + LY1) / 2
    zt = ze + t
    zr = zt + hh * k
    amp = 0.035 if kind == 'kawara' else 0.0
    dg = hh if form == 'hip' else (0.0 if form in ('gable', 'pent') else dg)
    e = e if form == 'irimoya' else 0.0
    out = []

    # the main (front and back) slopes, in segments along the ridge: (a, b, top(s))
    if form == 'hip':
        segs = [(LX0, LX1, lambda s: min(s - LX0, LX1 - s, hh), (LX0 + hh, LX1 - hh))]
    elif form == 'irimoya':
        g0, g1 = LX0 + dg - e, LX1 - dg + e
        segs = [(LX0, g0, lambda s: min(s - LX0, hh), ()), (g0, g1, lambda s: hh, ()), (g1, LX1, lambda s: min(LX1 - s, hh), ())]
    else:
        segs = [(LX0, LX1, lambda s: hh, ())]
    sides = (1,) if pent else (1, -1)
    for sg in sides:
        base = LY0 if sg > 0 else LY1

        def P(s, d, w=0.0, z0=zt, sg=sg, base=base):
            return (s, base + sg * d, z0 + d * k + w)
        for a, b, top, kinks in segs:
            xs = _samples(a, b, amp, kinks)
            V = []; F = []
            for s in xs:
                w = _wv(s - LX0, amp); d1 = max(top(s), 0.006)
                V.append(P(s, 0.0, w)); V.append(P(s, d1, w))
            for i in range(len(xs) - 1):
                F.append([2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1])
            bm, _f = bm_from(V, F, mat, sm=1 if amp else 0)
            for f in bm.faces:
                if f.normal.z < 0: f.normal_flip()
            bm.normal_update(); out.append(bm)
            mb = MB()
            # the eave's edge (the tile ends' wavy line) and the underside, parallel to the slope
            edge = [P(xs[0], 0.0, 0.0, ze), P(xs[-1], 0.0, 0.0, ze)] + [P(s, 0.0, _wv(s - LX0, amp)) for s in reversed(xs)]
            mb.face(edge, 'roofw', (0, -sg, 0), 0.55)
            pk = [a] + [x for x in kinks] + [b]
            und = [P(s, 0.0, 0.0, ze) for s in (a, b)] + [P(s, max(top(s), 0.006), 0.0, ze) for s in reversed(pk)]
            mb.face(und, soffit, (0, 0, -1), 0.8)
            # verges where a segment ends at a gable (gable: the roof's ends; irimoya: the upper roof's ends)
            for s, sx in ((a, -1), (b, 1)):
                d0 = top(s) if form != 'gable' else 0.0
                if form == 'irimoya' and (a, b) == (segs[1][0], segs[1][1]):
                    d0 = dg - e
                elif form != 'gable':
                    continue
                w = _wv(s - LX0, amp)
                mb.face([P(s, d0, 0.0, ze), P(s, hh, 0.0, ze), P(s, hh, w), P(s, d0, w)], 'roofw', (sx, 0, 0), 0.6)
                if kind == 'kawara':          # the rolled verge tiles (sode-gawara) and the barge board (hafu) under them
                    out.append(tube([P(s + sx * 0.02, d0, 0.04), P(s + sx * 0.02, hh, 0.04)], 0.06, 'roofw', 6, caps=True, sm=1))
                if barge:
                    bx = s + sx * 0.035
                    p0, p1 = P(bx, d0 - 0.05, 0.0, ze + 0.04), P(bx, hh, 0.0, ze + 0.04)
                    q0, q1 = P(bx, d0 - 0.05, 0.0, ze - 0.2), P(bx, hh, 0.0, ze - 0.2)
                    mb.face([q0, q1, p1, p0], barge, (sx, 0, 0), 0.9)
                    mb.face([(q0[0] - sx * 0.05, q0[1], q0[2]), (q1[0] - sx * 0.05, q1[1], q1[2]), q1, q0], barge, (0, 0, -1), 0.6)
            out.append(mb.bm())
            if kind == 'seam':
                for s in np.arange(a + 0.2, b - 0.1, 0.45):
                    d1 = top(s) - 0.04
                    if d1 < 0.1: continue
                    sec = [(0.0, -0.012), (0.035, -0.009), (0.035, 0.009), (0.0, 0.012)]
                    out.append(sweep([P(s, 0.0, 0.0, zt + 0.002), P(s, d1, 0.0, zt + 0.002)], (0, 0, 1), sec, 'roofw', caps=True))
    # the hip ends (hip and irimoya), their channels running along X
    if form in ('hip', 'irimoya'):
        for sx in (1, -1):
            base = LX0 if sx > 0 else LX1

            def Q(s, d, w=0.0, z0=zt, sx=sx, base=base):
                return (base + sx * d, s, z0 + d * k + w)
            top = lambda s: min(s - LY0, LY1 - s, dg)
            xs = _samples(LY0, LY1, amp, (LY0 + dg, LY1 - dg))
            V = []; F = []
            for s in xs:
                w = _wv(s - LY0, amp)
                V.append(Q(s, 0.0, w)); V.append(Q(s, max(top(s), 0.006), w))
            for i in range(len(xs) - 1):
                F.append([2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1])
            bm, _f = bm_from(V, F, mat, sm=1 if amp else 0)
            for f in bm.faces:
                if f.normal.z < 0: f.normal_flip()
            bm.normal_update(); out.append(bm)
            mb = MB()
            mb.face([Q(xs[0], 0.0, 0.0, ze), Q(xs[-1], 0.0, 0.0, ze)] + [Q(s, 0.0, _wv(s - LY0, amp)) for s in reversed(xs)],
                    'roofw', (-sx, 0, 0), 0.55)
            mb.face([Q(LY0, 0.0, 0.0, ze), Q(LY1, 0.0, 0.0, ze), Q(LY1 - dg, dg, 0.0, ze), Q(LY0 + dg, dg, 0.0, ze)], soffit, (0, 0, -1), 0.8)
            if form == 'irimoya':          # the little gable standing on the hip end
                gx = base + sx * dg
                yb = dg + t / k
                tri = [(gx, LY0 + yb, zt + dg * k - 0.02), (gx, LY1 - yb, zt + dg * k - 0.02), (gx, ym, ze + hh * k)]
                mb.face(tri, gable_mat, (-sx, 0, 0), 0.92)
                for j in range(1, 4):      # its battens
                    yy = LY0 + yb + (LY1 - LY0 - 2 * yb) * j / 4
                    zz = ze + min(yy - LY0, LY1 - yy) * k
                    mb.face([(gx - sx * 0.03, yy - 0.025, zt + dg * k), (gx - sx * 0.03, yy + 0.025, zt + dg * k),
                             (gx - sx * 0.03, yy + 0.025, zz), (gx - sx * 0.03, yy - 0.025, zz)], barge or 'accent', (-sx, 0, 0), 0.8)
            out.append(mb.bm())
            if kind == 'seam':
                for s in np.arange(LY0 + 0.25, LY1 - 0.1, 0.45):
                    d1 = top(s) - 0.04
                    if d1 < 0.1: continue
                    sec = [(0.0, -0.012), (0.035, -0.009), (0.035, 0.009), (0.0, 0.012)]
                    out.append(sweep([Q(s, 0.0, 0.0, zt + 0.002), Q(s, d1, 0.0, zt + 0.002)], (0, 0, 1), sec, 'roofw', caps=True))
    # ridges
    if kind == 'kawara':
        stack = [(-0.07, -0.15), (0.06, -0.15), (0.06, -0.135), (0.12, -0.135), (0.12, -0.12), (0.18, -0.12), (0.22, -0.09),
                 (0.25, -0.045), (0.26, 0.0), (0.25, 0.045), (0.22, 0.09), (0.18, 0.12), (0.12, 0.12), (0.12, 0.135),
                 (0.06, 0.135), (0.06, 0.15), (-0.07, 0.15)]
        small = [(-0.05, -0.1), (0.07, -0.1), (0.12, -0.07), (0.14, 0.0), (0.12, 0.07), (0.07, 0.1), (-0.05, 0.1)]
    else:
        stack = [(-0.03, -0.17), (0.02, -0.17), (0.07, -0.05), (0.075, 0.0), (0.07, 0.05), (0.02, 0.17), (-0.03, 0.17)]
        small = [(-0.02, -0.1), (0.03, -0.1), (0.05, 0.0), (0.03, 0.1), (-0.02, 0.1)]
    rmat = 'roofw' if kind == 'kawara' else ('roofw' if kind == 'slate' else 'roofw')
    if not pent:
        if form == 'hip': r0, r1 = LX0 + hh, LX1 - hh
        elif form == 'irimoya': r0, r1 = LX0 + dg - e - 0.05, LX1 - dg + e + 0.05
        else: r0, r1 = LX0 - 0.03, LX1 + 0.03
        if r1 - r0 > 0.05:
            out.append(sweep([(r0, ym, zr - 0.02), (r1, ym, zr - 0.02)], (0, 0, 1), stack, rmat, caps=True))
        else:
            r0 = r1 = (LX0 + LX1) / 2
        if form in ('hip', 'irimoya'):
            corners = [((LX0, LY0), (LX0 + dg, LY0 + dg)), ((LX0, LY1), (LX0 + dg, LY1 - dg)),
                       ((LX1, LY0), (LX1 - dg, LY0 + dg)), ((LX1, LY1), (LX1 - dg, LY1 - dg))]
            for (cx, cy), (ex, ey) in corners:
                d = dg if form == 'irimoya' else hh
                p0 = (cx + (0.05 if ex > cx else -0.05), cy + (0.05 if ey > cy else -0.05), zt + 0.03)
                p1 = (ex if form == 'irimoya' else (r0 if ex < (LX0 + LX1) / 2 else r1), ey if form == 'irimoya' else ym, zt + d * k - 0.01)
                out.append(sweep([p0, p1], (0, 0, 1), small, rmat, caps=True))
                if kind == 'kawara' and oni:
                    ob = extrude_poly([(x * 0.55, y * 0.5) for x, y in ONI], 0.08, rmat)
                    dirv = Vector((p0[0] - p1[0], p0[1] - p1[1], 0)).normalized()
                    side = Vector((-dirv.y, dirv.x, 0))
                    xform(ob, basis(Vector(p0) + dirv * 0.02 + Vector((0, 0, -0.04)), side, (0, 0, 1), dirv))
                    out.append(ob)
            if form == 'irimoya':          # the gables' rakes (kudari-mune) down the upper roof's verges
                for gx in (LX0 + dg - e + 0.12, LX1 - dg + e - 0.12):
                    for sg in (1, -1):
                        yb = LY0 if sg > 0 else LY1
                        out.append(sweep([(gx, yb + sg * (dg - e), zt + (dg - e) * k + 0.02), (gx, ym, zr - 0.02)], (0, 0, 1), small, rmat, caps=True))
        if kind == 'kawara' and oni:
            for x, sx in ((r0 - 0.02, -1), (r1 + 0.02, 1)):
                ob = extrude_poly([(px * oni, py * oni) for px, py in ONI], 0.14, rmat)
                xform(ob, basis((x, ym, zr - 0.1), (0, -sx, 0) if True else (0, 1, 0), (0, 0, 1), (sx, 0, 0)))
                setshade(ob, 0.85)
                out.append(ob)
                boss, _ = lathe([(0.0, 0.0), (0.075, 0.0), (0.075, 0.035), (0.0, 0.05)], 8, rmat)
                xform(boss, basis((x + sx * 0.14, ym, zr - 0.1 + 0.3 * oni), (0, -sx, 0), (0, 0, 1), (sx, 0, 0)))
                out.append(boss)
        elif not pent:
            pass
    else:
        # the pent roof's top: a flashing against the wall, and rolled verges at its ends
        out.append(cbox2((LX0, LY1 - 0.06, zr - 0.04), (LX1, LY1 + 0.005, zr + 0.06), 0.01, 'roofw'))
        if kind == 'kawara':
            for s, sx in ((LX0, -1), (LX1, 1)):
                out.append(tube([(s + sx * 0.02, LY0, zt + 0.04), (s + sx * 0.02, LY1, zr + 0.04)], 0.055, 'roofw', 6, caps=True, sm=1))
                mb = MB()
                mb.face([(s, LY0, ze), (s, LY1, ze + hh * k), (s, LY1, zr), (s, LY0, zt)], 'roofw', (sx, 0, 0), 0.6)
                out.append(mb.bm())
    SWP = Matrix(((0, 1, 0, 0), (1, 0, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))
    for bm in out:
        if sw: xform(bm, SWP)
        B.add(bm)
    B.feat(fmap, 'kh_roof', axis=axis, LX0=LX0, LX1=LX1, LY0=LY0, LY1=LY1, h=hh, dg=dg, form=form, rk=kind, moss=moss)
    if gutter and not pent:
        g = 0.1
        for sg in (1, -1):
            yl = (LY0 - 0.045) if sg > 0 else (LY1 + 0.045)
            path = [(LX0 + 0.05, yl), (LX1 - 0.05, yl)] if sg > 0 else [(LX1 - 0.05, yl), (LX0 + 0.05, yl)]
            if sw: path = [(p[1], p[0]) for p in reversed(path)]
            eave_gutter(B, path, ze + 0.06, mat='pipe', size=g)
    return zr + (0.26 if kind == 'kawara' else 0.08)


def under_z(ze, k, Y0, Y1, y):
    """The roof's underside over the plan line y (a gable's outline on the walls)."""
    return ze + min(y - Y0, Y1 - y) * k


def downpipe_corner(B, x_eave, y_eave, x_wall, y_wall, z_top, side=1):
    """A downpipe from an eave gutter's outlet back to the wall and down it to a shoe."""
    downpipe(B, [(x_eave, y_eave, z_top), (x_eave, y_eave, z_top - 0.15), (x_wall, y_wall, z_top - 0.6), (x_wall, y_wall, 0.3),
                 (x_wall + 0.12 * side, y_wall, 0.1)], r=0.04, brackets=[(x_wall, y_wall, z) for z in np.arange(0.9, z_top - 0.8, 1.6)])


# ================================================================ more shared pieces
def alu_balcony(B, x0, x1, depth, zf, h=1.08, pitch=0.11, slab='conc', mat='kmalu', back_x=True):
    """A balcony slab cantilevered from the front wall, with an aluminium rail of vertical bars on its three sides."""
    B.add(cbox2((x0, -depth, zf - 0.2), (x1, 0.0, zf), 0.015, slab))
    yr = -depth + 0.04
    zt = zf + h
    for x in (x0 + 0.04, (x0 + x1) / 2, x1 - 0.04):
        B.add(box((x - 0.025, yr - 0.025, zf), (x + 0.025, yr + 0.025, zt - 0.03), mat, skip=('-z',)))
    B.add(cbox2((x0, yr - 0.04, zt - 0.06), (x1, yr + 0.04, zt), 0.012, mat))
    B.add(box((x0, yr - 0.02, zf + 0.05), (x1, yr + 0.02, zf + 0.1), mat, skip=('-x', '+x')))
    for x in np.arange(x0 + 0.1, x1 - 0.06, pitch):
        B.add(box((x - 0.011, yr - 0.011, zf + 0.1), (x + 0.011, yr + 0.011, zt - 0.06), mat, skip=('-z', '+z')))
    for x in (x0 + 0.04, x1 - 0.04):
        B.add(cbox2((x - 0.03, -depth, zt - 0.06), (x + 0.03, 0.0, zt), 0.01, mat))
        for y in np.arange(-depth + 0.15, -0.05, pitch):
            B.add(box((x - 0.011, y - 0.011, zf + 0.0), (x + 0.011, y + 0.011, zt - 0.06), mat, skip=('-z', '+z')))
    B.feat('front', 'ao', a0=x0, a1=x1, b=zf - 0.2, length=0.5, k=0.45)
    mould(B, 'front', x0 + 0.1, x1 - 0.1, zf - 0.2, 0.45, 0.7)
    return yr, zt


def futon(B, x0, x1, yr, zr, out=0.72, inn=0.45, u=(0.0, 0.5)):
    """A futon airing over a rail at (yr, zr): a printed cover hanging outside, the other half inside."""
    yo, yi = yr - 0.055, yr + 0.055
    fp = box((x0, yo - 0.03, zr - out), (x1, yo, zr + 0.03), 'cloth4')
    fr = faces_facing(fp, (0, -1, 0), 0.9)
    setmat(fp, 'tex', fr)
    uv_fn(fp, fr, 'kh_futon', lambda co: (u[0] + (co.x - x0) / (x1 - x0) * (u[1] - u[0]), (co.z - (zr - out)) / (out + 0.03)), 0.01)
    B.add(fp)
    B.add(box((x0, yi, zr - inn), (x1, yi + 0.03, zr + 0.03), 'cloth4', skip=('-y',)))
    B.add(tube([(x0, yr, zr + 0.03), (x1, yr, zr + 0.03)], 0.075, 'cloth4', 6))
    for x in (x0 + 0.12, x1 - 0.12):          # the futon clips
        B.add(cbox2((x - 0.03, yo - 0.06, zr - 0.06), (x + 0.03, yo - 0.02, zr + 0.1), 0.008, 'khivory'))


def laundry_poles(B, wf, x0, x1, z, outs=(0.45, 0.8), seed=0, n=5):
    """Wall-mounted drying arms with aluminium poles across them and the washing out."""
    for x in (x0, x1):
        put(B, wf, fbox((x - 0.03, z - 0.05, 0.0), (x + 0.03, z + 0.03, outs[-1] + 0.08), 0.008, 'kmalu'))
        put(B, wf, tube([(x, z - 0.6, 0.02), (x, z - 0.04, outs[-1] * 0.7)], 0.012, 'kmalu', 4))
    for k, o in enumerate(outs):
        put(B, wf, tube([(x0 - 0.15, z + 0.04, o), (x1 + 0.15, z + 0.04, o)], 0.016, 'kmalu', 6))
        if k == 0:
            laundry(B, wf, x0 + 0.1, x1 - 0.1, z + 0.0, o, seed=seed, n=n)


def koshi(B, wf, u0, u1, v0, v1, pitch=0.062, slat=0.026, out=0.1, mat='accent', shoji=True, nuki=True):
    """A wooden lattice (koshi) over a window: close vertical slats in a frame standing out of the wall, shoji paper behind."""
    mb = MB()
    reveal(mb, u0, u1, v0, v1, 0.16, mat='accent', bottom=True)
    if shoji: shoji_face(mb, u0, u1, v0, v1, -0.16)
    for x in np.arange(u0 + pitch * 0.5, u1 - pitch * 0.3, pitch):
        bar(mb, x - slat / 2, v0, x + slat / 2, v1, 0.0, out, mat)
    if nuki:
        for v in (v0 + (v1 - v0) * 0.3, v1 - 0.12):
            bar(mb, u0, v - 0.02, u1, v + 0.02, out, out + 0.02, mat, ends=True)
    put(B, wf, mb.bm())
    put(B, wf, fbox((u0 - 0.06, v1, 0.0), (u1 + 0.06, v1 + 0.09, out + 0.03), 0.012, mat))
    put(B, wf, fbox((u0 - 0.06, v0 - 0.09, 0.0), (u1 + 0.06, v0, out + 0.03), 0.012, mat))
    for x in (u0 - 0.06, u1):
        put(B, wf, fbox((x, v0, 0.0), (x + 0.06, v1, out + 0.01), 0.01, mat))
    a0, b0 = wf.ab(u0, v0 - 0.09); a1, _ = wf.ab(u1, v0)
    B.feat(wf.mp, 'streak', a0=min(a0, a1), a1=max(a0, a1), b=b0, length=0.5, k=0.6)
    c3 = wf.P((u0 + u1) / 2, (v0 + v1) / 2, -0.16)
    B.windows.append({'center': [round(c3.x, 3), round(c3.y, 3), round(c3.z, 3)], 'size': [round(u1 - u0, 3), round(v1 - v0, 3)], 'wall': wf.mp})


def shoji_face(mb, u0, u1, v0, v1, w):
    """Shoji screens (a third of the tile each, about 0.9 m) on a plane at depth w."""
    n = max(1, int(round((u1 - u0) / 0.9)))
    for k in range(n):
        a = u0 + (u1 - u0) * k / n; b = u0 + (u1 - u0) * (k + 1) / n
        mb.face([(a, v0, w), (b, v0, w), (b, v1, w), (a, v1, w)], 'tex', (0, 0, 1), 1.0,
                lambda co, a=a, b=b, k=k: reg_uv('kh_shoji', (co.x - a) / (b - a) / 3.0 + (k % 3) / 3.0, (co.y - v0) / (v1 - v0), 0.0))


def foundation(B, gaps=(), h=0.44, vents=(), wf=None):
    """The exposed concrete foundation (kiso) under the walls, its drip flashing, and vent grilles."""
    for path, closed in ring_path(B, gaps=gaps):
        plinth(B, path, h, out=0.02, mat='stone', closed=closed)
        string_course(B, path, h - 0.01, h + 0.035, out=0.04, mat='kmalu', closed=closed)
    for x in vents:
        decal(B, wf, x - 0.15, x + 0.15, 0.13, 0.26, 0.022, 'vent')


# ================================================================ HouseTileKM
def house_tile(B):
    """Two storeys of beige mortar under a hipped kawara roof: the genkan under a little kawara pent roof, a toilet window
    behind a grille, a living-room window to the floor, a balcony with futons on its rail, an AC on brackets."""
    W, H, D = B.W, B.H, B.D
    F, Rt, Bk, Lf = frames(B)
    v0 = 0.44
    door_o = (-3.35, -1.95)
    wtoi = (-1.2, -0.7, 1.45, 2.05)
    wliv = (0.25, 2.85, 0.52, 2.35)
    wup = (-3.2, -1.6, 3.75, 4.95)
    wst = (-0.95, -0.5, 3.95, 4.75)
    wbal = (0.55, 3.05, 3.1, 5.0)
    wall(B, F, -W / 2, W / 2, H, [(door_o[0], door_o[1], 0.2, 2.3), wtoi, wliv, wup, wst, wbal], v0)
    sr = [(2.2, 3.3, 1.0, 2.1), (2.6, 3.6, 3.8, 4.9), (5.4, 6.0, 1.5, 2.1)]
    sl = [(-3.4, -2.3, 1.0, 2.1), (-4.6, -3.6, 3.8, 4.9)]
    wall(B, Rt, 0, D, H, sr, v0)
    wall(B, Lf, -D, 0, H, sl, v0)
    wall(B, Bk, -W / 2, W / 2, H, [(-1.0, 0.2, 1.2, 2.1)], v0)
    foundation(B, gaps=[door_o], vents=(-0.95, 1.5, 3.4), wf=F)
    # roof: a hipped kawara roof with deep eaves
    over, k = 0.75, 0.45
    X0, X1, Y0, Y1 = -W / 2 - over, W / 2 + over, -over, D + over
    ze = H - over * k
    top = kh_roof(B, X0, X1, Y0, Y1, ze, k, 'kawara', 'hip', moss='back')
    for xe, xw, sd in ((X0 + 0.35, -W / 2 - 0.07, -1), (X1 - 0.35, W / 2 + 0.07, 1)):
        downpipe_corner(B, xe, Y0 - 0.1, xw, 0.25, ze - 0.02, sd)
    # the genkan: porch, sliding door, its little kawara roof, light, name plate, intercom, post box
    B.add(fbox((door_o[0] - 0.3, -1.0, 0.0), (door_o[1] + 0.3, 0.0, 0.18), 0.012, 'khporch'))
    kh_genkan(B, F, door_o[0], door_o[1], 0.2)
    kh_roof(B, -W / 2 - 0.15, -0.3, -0.72, 0.0, 3.05 - 0.72 * 0.4 - 0.1, 0.4, 'kawara', 'pent', t=0.1, fmap='roofb', mat='roofb')
    mould(B, 'front', -W / 2, -0.3, 3.05 - 0.12, 0.5, 0.8)
    porch_light(B, F, door_o[1] + 0.27, 2.05)
    name_plate(B, F, door_o[0] - 0.24, 1.55, B.name)
    intercom(B, F, door_o[0] - 0.24, 1.12)
    post_box(B, F, door_o[1] + 0.32, 0.95)
    # windows
    kh_window(B, F, *wtoi, frosted=True, grille=True, screen=None)
    kh_window(B, F, *wliv, screen='right', box='shutter', glass='glass1')
    kh_window(B, F, *wup, screen='right', box='shutter', glass='glass2')
    kh_window(B, F, *wst, frosted=True, screen=None)
    kh_window(B, F, *wbal, screen='left', glass='glass0', sill=False)
    for kk, o in enumerate(sr):
        kh_window(B, Rt, *o, screen='right', glass=('glass0', 'glass2', 'glass1')[kk], frosted=kk == 2, register=kk == 0)
    for o in sl:
        kh_window(B, Lf, *o, screen='right', glass='glass1', register=False)
    kh_window(B, Bk, -1.0, 0.2, 1.2, 2.1, screen='right', register=False)
    # the balcony: futons airing over its rail, the drying arms above
    yr, zt = alu_balcony(B, 0.2, 3.4, 0.95, 3.06)
    futon(B, 0.55, 1.55, yr, zt, u=(0.0, 0.5))
    futon(B, 1.75, 2.75, yr, zt, out=0.62, u=(0.5, 1.0))
    for x in (0.45, 3.15):
        put(B, F, fbox((x - 0.03, 5.05, 0.0), (x + 0.03, 5.11, 0.8), 0.008, 'kmalu'))
    put(B, F, tube([(0.3, 5.14, 0.72), (3.3, 5.14, 0.72)], 0.016, 'kmalu', 6))
    # life on the walls
    wall_ac(B, F, 3.45, 1.0, duct_to=2.7)
    gas_meter(B, F, -0.2, 0.95)
    put(B, F, tube([(-0.52, 2.75, 0.07), (-0.52, 0.5, 0.07), (-0.52, 0.42, 0.0)], 0.035, 'khgrey', 6))
    put(B, F, tube([(-0.62, 2.12, 0.0), (-0.52, 2.12, 0.07)], 0.03, 'khgrey', 6))
    # the garden: a hydrangea, pots by the door
    hydrangea(B, (1.25, -0.55, 0.0), 0.45, seed=3)
    pot(B, (door_o[0] - 0.55, -0.42, 0.0), 0.17, 0.3, 'khpotp', 'bush', seed=11)
    pot(B, (door_o[1] + 0.55, -0.32, 0.0), 0.13, 0.24, 'khpotg', 'flowers', seed=12)
    # weathering
    mould(B, 'front', -W / 2, W / 2, H, 1.1)
    mould(B, 'right', 0, D, H, 0.9); mould(B, 'left', 0, D, H, 0.9)
    B.feat('front', 'kh_salt', a0=-W / 2, a1=W / 2, b0=0.45, b1=1.7, k=0.6)
    B.feat('right', 'kh_salt', a0=0, a1=D, b0=0.45, b1=2.0, k=0.8)
    B.feat('front', 'kh_crack', cracks=[(wup[0], wup[2] - 0.04, math.pi + 0.9, 0.35), (wliv[1] + 0.04, wliv[3], 0.7, 0.45),
                                       (wtoi[1], wtoi[2] - 0.04, -0.9, 0.3)], k=0.8)
    return top


# ================================================================ HouseMetalKM
def house_metal(B):
    """White mortar below and dark-stained vertical boards above, under a dark standing-seam gable to the street; a balcony
    with its laundry poles, shutter boxes over the windows, a steel canopy over the door."""
    W, H, D = B.W, B.H, B.D
    F, Rt, Bk, Lf = frames(B)
    v0, gf = 0.42, 2.95
    over, k = 0.6, 0.5
    X0, X1, Y0, Y1 = -W / 2 - over, W / 2 + over, -0.45, D + 0.45
    ze = H - over * k
    apex = under_z(ze, k, X0, X1, 0.0)
    gable = [(-W / 2, H), (0.0, apex), (W / 2, H)]
    door_o = (1.55, 2.6)
    wg = (-2.9, -0.8, 0.85, 2.15)
    wsm = (0.05, 0.6, 1.45, 2.0)
    wb = (-2.75, -0.35, 3.15, 5.0)
    wu = (0.75, 2.55, 3.8, 4.95)
    wall(B, F, -W / 2, W / 2, gf, [(door_o[0], door_o[1], 0.2, 2.3), wg, wsm], v0)
    wall(B, F, -W / 2, W / 2, gable, [wb, wu], gf, 'rib', 'accent', rib=(0.16, 0.02))
    sr = [(2.2, 3.4, 1.0, 2.1)]; sru = [(3.0, 4.2, 3.8, 4.9)]
    wall(B, Rt, 0, D, gf, sr, v0); wall(B, Rt, 0, D, H, sru, gf, 'rib', 'accent', rib=(0.16, 0.02))
    wall(B, Lf, -D, 0, gf, [(-4.4, -3.4, 1.0, 2.1)], v0); wall(B, Lf, -D, 0, H, [], gf, 'rib', 'accent', rib=(0.16, 0.02))
    wall(B, Bk, -W / 2, W / 2, gf, [], v0); wall(B, Bk, -W / 2, W / 2, gable, [], gf, 'rib', 'accent', rib=(0.16, 0.02))
    foundation(B, gaps=[door_o], vents=(-0.3, -3.2), wf=F)
    for path, closed in ring_path(B):
        string_course(B, path, gf - 0.02, gf + 0.04, out=0.045, mat='kmalu', closed=closed)
    top = kh_roof(B, X0, X1, Y0, Y1, ze, k, 'seam', 'gable', axis='y', t=0.08, barge='kmmetal')
    for xe, xw, sd in ((X0 + 0.05, -W / 2 - 0.07, -1), (X1 - 0.05, W / 2 + 0.07, 1)):
        downpipe_corner(B, xe - 0.12 * sd, Y0 + 0.25, xw, 0.3, ze - 0.02, sd)
    vent(B, F, 0.0, apex - 0.75, 0.3)
    # the door under a steel canopy
    B.add(fbox((door_o[0] - 0.3, -0.9, 0.0), (door_o[1] + 0.3, 0.0, 0.18), 0.012, 'khporch'))
    kh_genkan(B, F, door_o[0], door_o[1], 0.2, double=False, bars=3)
    put(B, F, fbox((door_o[0] - 0.3, 2.48, 0.0), (door_o[1] + 0.3, 2.56, 0.85), 0.01, 'kmmetal'))
    B.feat('front', 'ao', a0=door_o[0] - 0.3, a1=door_o[1] + 0.3, b=2.48, length=0.4, k=0.5)
    name_plate(B, F, door_o[0] - 0.22, 1.55, B.name, back='stone')
    intercom(B, F, door_o[0] - 0.22, 1.12)
    porch_light(B, F, door_o[1] + 0.22, 2.0)
    # windows
    kh_window(B, F, *wg, screen='right', box='shutter', glass='glass1')
    kh_window(B, F, *wsm, frosted=True, grille=True, screen=None)
    kh_window(B, F, *wb, screen='left', box='shutter', glass='glass0', sill=False)
    kh_window(B, F, *wu, screen='right', box='shutter', glass='glass2')
    kh_window(B, Rt, *sr[0], screen='right', register=False); kh_window(B, Rt, *sru[0], screen='right', box='shutter', register=False)
    kh_window(B, Lf, -4.4, -3.4, 1.0, 2.1, screen='right', register=False)
    # the balcony and its laundry
    alu_balcony(B, -3.1, -0.0, 0.9, 3.12, slab='accentp')
    laundry_poles(B, F, -2.85, -0.25, 5.05, outs=(0.5, 0.78), seed=41, n=5)
    # life
    ground_ac(B, (-0.25, -0.38, 0.0))
    gas_meter(B, Rt, 1.0, 0.9)
    pot(B, (door_o[1] + 0.55, -0.35, 0.0), 0.16, 0.28, 'khpotp', 'tall', seed=21)
    pot(B, (-3.15, -0.4, 0.0), 0.14, 0.24, 'khpotg', 'bush', seed=22)
    # weathering
    B.feat('front', 'kh_grain', a0=-W / 2 - 0.1, a1=W / 2 + 0.1, b0=gf, b1=apex + 0.2, bw=0.16, dark=0.72, silver=1.0, seed=3.0)
    B.feat('front', 'kh_salt', a0=-W / 2, a1=W / 2, b0=gf, b1=gf + 1.6, k=0.5)
    B.feat('front', 'kh_salt', a0=-W / 2, a1=W / 2, b0=0.42, b1=1.5, k=0.5)
    mould(B, 'front', door_o[0] - 0.3, door_o[1] + 0.3, 2.48, 0.35, 0.6)
    mould(B, 'right', 0, D, H, 0.8); mould(B, 'left', 0, D, H, 0.8)
    B.feat('front', 'kh_crack', cracks=[(wg[1] + 0.03, wg[3], 0.8, 0.3)], k=0.7)
    return top


# ================================================================ HouseOldKM
def house_old(B):
    """An old Kamakura house: a ground floor of silvered and blackened boards between dark posts, wooden lattice windows
    with shoji behind, a timber sliding door, an upper floor of old plaster, a kawara pent roof and a deep kawara gable
    roof with moss along its north (back) edge."""
    W, H, D = B.W, B.H, B.D
    F, Rt, Bk, Lf = frames(B)
    v0, gf = 0.3, 2.95
    over, k = 0.95, 0.5
    X0, X1, Y0, Y1 = -W / 2 - 0.5, W / 2 + 0.5, -over, D + over
    ze = H - over * k
    apex = under_z(ze, k, Y0, Y1, D / 2)
    door_o = (-3.95, -2.45)
    k1 = (-1.85, 0.75, 0.75, 2.4)
    k2 = (1.25, 3.95, 0.75, 2.4)
    u1 = (-3.6, -1.7, 3.55, 4.75)
    u2 = (0.7, 3.4, 3.55, 4.75)
    wall(B, F, -W / 2, W / 2, gf, [(door_o[0], door_o[1], 0.3, 2.4), k1, k2], v0, 'lap', 'wall', lap=(0.2, 0.018))
    wall(B, F, -W / 2, W / 2, H, [u1, u2], gf, 'flat', 'khplaster')
    side = [(0, H), (D / 2, apex), (D, H)]
    for wf, top_, ops in ((Rt, side, [(2.0, 3.6, 0.9, 2.2)]), (Lf, [(-u, v) for u, v in reversed(side)], [(-6.0, -4.6, 0.9, 2.2)])):
        a, b = (0, D) if wf is Rt else (-D, 0)
        wall(B, wf, a, b, gf, ops, v0, 'lap', 'wall', lap=(0.2, 0.018))
        wall(B, wf, a, b, [(u, v) for u, v in top_], [], gf, 'flat', 'khplaster')
    wall(B, Bk, -W / 2, W / 2, gf, [], v0, 'lap', 'wall', lap=(0.2, 0.018))
    wall(B, Bk, -W / 2, W / 2, H, [], gf, 'flat', 'khplaster')
    for path, closed in ring_path(B, gaps=[door_o]):
        plinth(B, path, 0.32, out=0.04, mat='kmstoned', closed=closed)
    # the dark frame: posts, the beam between the floors, the beam under the eaves
    for x in (-W / 2 + 0.06, door_o[1] - 0.02 + 0.1, k1[1] + 0.25, W / 2 - 0.06):
        B.add(cbox2((x - 0.065, -0.05, 0.3), (x + 0.065, 0.05, H), 0.01, 'accent'))
    for x in (-1.35, 0.25 + 1.3, 3.75):
        B.add(cbox2((x - 0.055, -0.04, gf), (x + 0.055, 0.04, H), 0.008, 'accent'))
    for z0, z1 in ((gf - 0.02, gf + 0.18), (H - 0.22, H)):
        B.add(cbox2((-W / 2 - 0.02, -0.06, z0), (W / 2 + 0.02, 0.02, z1), 0.01, 'accent'))
    # the roofs
    top = kh_roof(B, X0, X1, Y0, Y1, ze, k, 'kawara', 'gable', moss='back', barge='accent')
    kh_roof(B, -W / 2 - 0.25, W / 2 + 0.25, -0.9, 0.0, 3.25 - 0.9 * 0.4 - 0.1, 0.4, 'kawara', 'pent', t=0.1, fmap='roofb', mat='roofb')
    downpipe(B, [(X0 + 0.4, Y0 - 0.09, ze - 0.02), (X0 + 0.4, Y0 - 0.09, ze - 0.2), (-W / 2 - 0.07, 0.3, ze - 0.7), (-W / 2 - 0.07, 0.3, 0.3),
                 (-W / 2 - 0.2, 0.3, 0.08)], r=0.04, mat='pipe', brackets=[(-W / 2 - 0.07, 0.3, z) for z in (1.0, 2.6, 4.0)])
    # the timber sliding door, the lattice windows
    B.add(fbox((door_o[0] - 0.2, -0.75, 0.0), (door_o[1] + 0.2, 0.0, 0.16), 0.03, 'kmstone'))
    kh_genkan(B, F, door_o[0], door_o[1], 0.3, mat='accent', frame='accent', bars=7, region='kh_shoji')
    koshi(B, F, *k1)
    koshi(B, F, *k2)
    for o in (u1, u2):
        kh_window(B, F, *o, screen=None, frame='accent', glass='glass2', depth=0.1, streak=0.5)
        x0, x1 = o[0] - 0.08, o[1] + 0.08
        put(B, F, fbox((x0, o[2] + 0.42, 0.0), (x1, o[2] + 0.48, 0.22), 0.008, 'accent'))
        for x in np.arange(x0 + 0.05, x1, 0.13):
            put(B, F, box((x - 0.016, o[2] - 0.12, 0.17), (x + 0.016, o[2] + 0.42, 0.205), 'accent', skip=('-z', '+y')))
        put(B, F, fbox((x0, o[2] - 0.16, 0.0), (x1, o[2] - 0.1, 0.22), 0.008, 'accent'))
    window(B, Rt, 2.0, 3.6, 0.9, 2.2, cols=2, frame='accent', glass='glass0', sill='accent', head=None, cheap=True, register=False)
    window(B, Lf, -6.0, -4.6, 0.9, 2.2, cols=2, frame='accent', glass='glass2', sill='accent', head=None, cheap=True, register=False)
    name_plate(B, F, door_o[0] - 0.3, 1.5, B.name, w=0.1, h=0.3, back='kmsilver')
    lp, _ = lathe([(0.0, -0.1), (0.06, -0.1), (0.08, -0.02), (0.06, 0.04), (0.02, 0.06), (0.0, 0.06)], 8, ['lamp', 'lamp', 'black', 'black', 'black'])
    xform(lp, T(door_o[1] + 0.3, -0.22, 2.38)); B.add(lp)
    B.add(tube([(door_o[1] + 0.3, -0.22, 2.44), (door_o[1] + 0.3, -0.22, 2.6), (door_o[1] + 0.3, 0.0, 2.7)], 0.012, 'black', 4))
    lamp_at(B, Vector((door_o[1] + 0.3, -0.22, 2.32)))
    meter_box(B, F, W / 2 - 0.35, 1.5, w=0.24, h=0.34, mat='khivory')
    # the garden: bonsai on a bench, a hydrangea at the corner, a water jar
    bx0, bx1 = 1.6, 3.3
    for x in (bx0 + 0.1, bx1 - 0.1):
        B.add(box((x - 0.04, -0.62, 0.0), (x + 0.04, -0.3, 0.42), 'kmsilver', skip=('-z',)))
    B.add(cbox2((bx0, -0.66, 0.42), (bx1, -0.26, 0.47), 0.01, 'kmsilver'))
    for kk, x in enumerate((bx0 + 0.35, bx0 + 0.85, bx1 - 0.35)):
        pot(B, (x, -0.46, 0.47), 0.11 + 0.02 * (kk % 2), 0.1, 'khpotg' if kk % 2 else 'pot', 'bush', seed=31 + kk, scale=0.8)
    hydrangea(B, (-4.0, -0.55, 0.0), 0.42, seed=8, cols=('khhyd2', 'khhyd1'))
    jar, _ = lathe([(0.0, 0.0), (0.18, 0.0), (0.24, 0.2), (0.25, 0.35), (0.2, 0.42), (0.21, 0.45), (0.0, 0.43)], 9,
                   ['kmstoned', 'kmstoned', 'kmstoned', 'kmstoned', 'kmstoned', 'black'])
    xform(jar, T(-1.25, -0.45, 0.0)); B.add(jar)
    # weathering: boards silver low and near black high, the plaster stained under the eaves and cracked
    for mp, a0, a1 in (('front', -W / 2 - 0.1, W / 2 + 0.1), ('right', -0.5, D + 0.5), ('left', -0.5, D + 0.5)):
        B.feat(mp, 'kh_grain', a0=a0, a1=a1, b0=0.3, b1=gf, vert=False, bw=0.2, dark=0.42, silver=1.0, seed=7.0)
        mould(B, mp, a0, a1, H - 0.2, 1.0, 0.9)
        B.feat(mp, 'kh_salt', a0=a0, a1=a1, b0=gf + 0.2, b1=gf + 1.2, k=0.4)
    mould(B, 'front', -W / 2, W / 2, 3.12, 0.6, 0.9)
    B.feat('front', 'kh_crack', cracks=[(u1[1] + 0.02, u1[3], 0.5, 0.4), (u2[0] - 0.02, u2[2] - 0.1, math.pi + 0.6, 0.5)], k=0.9)
    return top + 0.26


# ================================================================ HouseShedKM
def house_shed(B):
    """A two-storey mortar house with a corrugated lean-to shed on its left and a bicycle-wide gap under the same roof
    between the shed and the house; long water streaks, cracked and patched mortar, rust running from the sheets' fixings."""
    W, H, D = B.W, B.H, B.D
    xm = -W / 2 + 2.2
    F = WF((0, 0, 0), (1, 0, 0), 'front')
    Rt = WF((W / 2, 0, 0), (0, 1, 0), 'right')
    Lm = WF((xm, 0, 0), (0, -1, 0), 'left')
    Bk = WF((0, D, 0), (-1, 0, 0), 'back')
    v0 = 0.42
    over, k = 0.7, 0.45
    X0, X1, Y0, Y1 = xm - 0.45, W / 2 + 0.45, -over, D + over
    ze = H - over * k
    apex = under_z(ze, k, Y0, Y1, D / 2)
    door_o = (-1.65, -0.45)
    wg = (0.5, 2.5, 0.9, 2.1)
    wsm = (3.1, 3.7, 1.45, 2.05)
    wa = (-1.6, 0.2, 3.75, 4.9)
    wb = (1.5, 3.3, 3.75, 4.9)
    wall(B, F, xm, W / 2, H, [(door_o[0], door_o[1], 0.2, 2.3), wg, wsm, wa, wb], v0)
    side = [(0, H), (D / 2, apex), (D, H)]
    wall(B, Rt, 0, D, side, [(2.2, 3.4, 1.0, 2.1), (2.4, 3.6, 3.8, 4.9)], v0)
    wall(B, Lm, -D, 0, [(-u, v) for u, v in reversed(side)], [(-3.4, -2.4, 3.8, 4.9)], v0)
    wall(B, Bk, -W / 2, -xm, H, [], v0)
    for path in ([(door_o[1], 0.0), (W / 2, 0.0), (W / 2, D), (xm, D), (xm, 0.0), (door_o[0], 0.0)],):
        plinth(B, path, 0.44, out=0.02, mat='stone')
        string_course(B, path, 0.43, 0.475, out=0.04, mat='kmalu')
    decal(B, F, 1.35, 1.65, 0.13, 0.26, 0.022, 'vent')
    top = kh_roof(B, X0, X1, Y0, Y1, ze, k, 'kawara', 'gable', barge='accent')
    downpipe_corner(B, X1 - 0.3, Y0 - 0.1, W / 2 + 0.07, 0.25, ze - 0.02, 1)
    # the door under a clear canopy on brackets, the windows
    B.add(fbox((door_o[0] - 0.25, -0.8, 0.0), (door_o[1] + 0.25, 0.0, 0.18), 0.012, 'khporch'))
    kh_genkan(B, F, door_o[0], door_o[1], 0.2, mat='kmalu', frame='kmalu', bars=0)
    put(B, F, fbox((door_o[0] - 0.3, 2.55, 0.0), (door_o[1] + 0.3, 2.6, 0.85), 0.006, 'khpoly'))
    put(B, F, fbox((door_o[0] - 0.3, 2.6, 0.78), (door_o[1] + 0.3, 2.66, 0.85), 0.006, 'kmalu'))
    for x in (door_o[0] - 0.2, door_o[1] + 0.2):
        put(B, F, tube([(x, 2.0, 0.0), (x, 2.56, 0.75)], 0.015, 'kmalu', 4))
    name_plate(B, F, door_o[0] - 0.24, 1.5, B.name, back='kmstone')
    intercom(B, F, door_o[0] - 0.24, 1.1)
    porch_light(B, F, door_o[1] + 0.25, 2.05)
    kh_window(B, F, *wg, screen='right', grille=True, glass='glass1')
    kh_window(B, F, *wsm, frosted=True, screen=None)
    kh_window(B, F, *wa, screen='right', box='shutter', glass='glass2')
    kh_window(B, F, *wb, screen='left', tobukuro='right', glass='glass0')
    kh_window(B, Rt, 2.2, 3.4, 1.0, 2.1, screen='right', register=False)
    kh_window(B, Rt, 2.4, 3.6, 3.8, 4.9, screen='right', register=False)
    kh_window(B, Lm, -3.4, -2.4, 3.8, 4.9, screen='right', register=False)
    wall_ac(B, F, 0.95, 3.05, duct_to=3.7)
    gas_meter(B, F, -0.12, 0.95)
    # the lean-to: a corrugated roof falling to the left over the shed and the bicycle gap
    sx0, sx1, sy1 = -W / 2, -W / 2 + 1.45, 4.2
    xl, zl, zh = -W / 2 - 0.18, 2.3, 2.62
    kl = (zh - zl) / (xm - xl)
    zu = lambda x: zl + (x - xl) * kl - 0.06
    mb = MB()
    ry0, ry1 = -0.32, sy1 + 0.25
    mb.face([(xl, ry0, zl), (xm, ry0, zh), (xm, ry1, zh), (xl, ry1, zl)], 'khcorrr', (0, 0, 1))
    mb.face([(xl, ry0, zl - 0.04), (xl, ry1, zl - 0.04), (xm, ry1, zh - 0.04), (xm, ry0, zh - 0.04)], 'khcorr', (0, 0, -1), 0.75)
    mb.face([(xl, ry0, zl - 0.04), (xm, ry0, zh - 0.04), (xm, ry0, zh), (xl, ry0, zl)], 'galvw', (0, -1, 0), 0.8)
    mb.face([(xl, ry1, zl - 0.04), (xl, ry1, zl), (xm, ry1, zh), (xm, ry1, zh - 0.04)], 'galvw', (0, 1, 0), 0.8)
    mb.face([(xl, ry0, zl - 0.04), (xl, ry0, zl), (xl, ry1, zl), (xl, ry1, zl - 0.04)], 'galvw', (-1, 0, 0), 0.7)
    B.add(mb.bm())
    B.add(cbox2((xm - 0.02, ry0, zh - 0.02), (xm + 0.05, ry1, zh + 0.1), 0.01, 'galvw'))
    B.add(cbox2((sx1 - 0.03, ry0 + 0.02, zu(sx1) - 0.12), (xm, ry0 + 0.1, zu(sx1) - 0.01), 0.01, 'woodd'))
    B.feat('roof', 'kh_corr', x0=xl, x1=xm, y0=ry0, y1=ry1, fall='x', purlins=[0.3, 1.2, 2.2])
    eave_gutter(B, [(xl - 0.045, ry1), (xl - 0.045, ry0)], zl + 0.02, mat='galvw', size=0.09)
    downpipe(B, [(xl - 0.1, ry0 + 0.1, zl - 0.05), (xl - 0.1, ry0 + 0.1, 0.25), (xl - 0.1, ry0 - 0.05, 0.08)], r=0.035, mat='galvw')
    # the shed: corrugated walls, a sliding door of the same sheet
    SF = WF((0, 0, 0), (1, 0, 0), 'front')
    SL = WF((sx0, 0, 0), (0, -1, 0), 'left')
    SR = WF((sx1, 0, 0), (0, 1, 0), 'right')
    SB = WF((0, sy1, 0), (-1, 0, 0), 'back')
    wall(B, SF, sx0, sx1, [(sx0, zu(sx0)), (sx1, zu(sx1))], [], 0.0, 'rib', 'khcorr', rib=(0.1, 0.016))
    wall(B, SL, -sy1, 0, zu(sx0), [], 0.0, 'rib', 'khcorr', rib=(0.1, 0.016))
    wall(B, SR, 0, sy1, zu(sx1), [], 0.0, 'rib', 'khcorr', rib=(0.1, 0.016))
    wall(B, SB, -sx1, -sx0, [(-sx1, zu(sx1)), (-sx0, zu(sx0))], [], 0.0, 'rib', 'khcorr', rib=(0.1, 0.016))
    dx0, dx1 = sx0 + 0.25, sx1 - 0.15
    wall(B, SF.off(0.035), dx0, dx1, 1.95, [], 0.05, 'rib', 'khcorr', rib=(0.1, 0.016))
    for v in (0.02, 1.95):
        put(B, SF, fbox((dx0 - 0.05, v, 0.0), (dx1 + 0.05, v + 0.05, 0.07), 0.006, 'galvw'))
    put(B, SF, fbox((dx1 - 0.12, 0.9, 0.05), (dx1 - 0.08, 1.15, 0.08), 0.005, 'black'))
    concrete_pad(B, sx1, xm, -0.32, sy1 + 0.2)
    rust = [(x, z) for z in (0.25, 1.05, 1.85) for x in np.arange(sx0 + 0.15, sx1, 0.3)]
    B.feat('front', 'kh_rust', pts=rust, length=0.55)
    B.feat('front', 'kh_rustfield', a0=sx0, a1=sx1, b0=0.0, b1=2.4, k=0.8)
    B.feat('left', 'kh_rust', pts=[(y, z) for z in (0.25, 1.05, 1.85) for y in np.arange(0.2, sy1, 0.35)], length=0.5)
    B.feat('left', 'kh_rustfield', a0=0.0, a1=sy1, b0=0.0, b1=2.4, k=0.8)
    # the garden
    hydrangea(B, (2.95, -0.5, 0.0), 0.4, seed=5, cols=('khhyd1', 'khhyd3'))
    pot(B, (door_o[1] + 0.5, -0.35, 0.0), 0.14, 0.26, 'khpotp', 'flowers', seed=51)
    round_bin(B, (sx1 + 0.4, 3.6, 0.0), mat='khgrey')
    # weathering: streaks from the eaves and the sills, cracks (one filled and painted over), mould, salt
    B.feat('front', 'kh_streak', a0=xm, a1=W / 2, b=H, length=2.2, k=0.9, every=0.2)
    mould(B, 'front', xm, W / 2, H, 0.8)
    mould(B, 'right', 0, D, H, 0.8)
    B.feat('front', 'kh_salt', a0=xm, a1=W / 2, b0=0.45, b1=1.6, k=0.6)
    B.feat('front', 'kh_crack', cracks=[(wa[1] + 0.03, wa[2] - 0.03, -0.75, 0.9), (wg[0] - 0.03, wg[3] + 0.02, math.pi - 0.7, 0.7),
                                       (wb[1], wb[3] + 0.03, 0.9, 0.5)], k=1.0)
    B.feat('front', 'kh_crack', cracks=[(wg[1] + 0.03, wg[2] - 0.03, -0.6, 0.8)], k=0.7, repair=True)
    return top + 0.26


# ================================================================ HouseCarportKM
def house_carport(B):
    """A newer two-storey house in ceramic siding under a slate hip, its door under a flat canopy, and on its right a
    carport of slim posts and a clear roof, left empty for the street's kei car."""
    W, H, D = B.W, B.H, B.D
    xr = W / 2 - 3.3
    xl = -W / 2
    F = WF((0, 0, 0), (1, 0, 0), 'front')
    Rt = WF((xr, 0, 0), (0, 1, 0), 'right')
    Lf = WF((xl, 0, 0), (0, -1, 0), 'left')
    Bk = WF((0, D, 0), (-1, 0, 0), 'back')
    v0 = 0.45
    door_o = (0.45, 1.4)
    wg = (-4.5, -2.0, 0.47, 2.4)
    wsm = (-1.3, -0.75, 1.5, 2.05)
    u1, u2, u3 = (-4.3, -2.7, 3.75, 4.95), (-1.9, -0.1, 3.75, 4.95), (0.45, 1.25, 4.0, 4.7)
    lap = (0.455, 0.012)
    wall(B, F, xl, xr, H, [(door_o[0], door_o[1], 0.3, 2.4), wg, wsm, u1, u2, u3], v0, 'lap', lap=lap)
    wall(B, Rt, 0, D, H, [(3.6, 4.6, 1.0, 2.1), (2.6, 3.8, 3.8, 4.9)], v0, 'lap', lap=lap)
    wall(B, Lf, -D, 0, H, [(-4.4, -3.4, 1.0, 2.1)], v0, 'lap', lap=lap)
    wall(B, Bk, -xr, -xl, H, [], v0, 'lap', lap=lap)
    for x, y in ((xr, 0), (xl, 0), (xr, D), (xl, D)):
        corner_board(B, x, y, v0, H - 0.02, s=0.045, mat='trimw', r=0.01)
    path = [(door_o[1], 0.0), (xr, 0.0), (xr, D), (xl, D), (xl, 0.0), (door_o[0], 0.0)]
    plinth(B, path, 0.46, out=0.02, mat='stone')
    string_course(B, path, 0.45, 0.495, out=0.04, mat='kmalu')
    over, k = 0.6, 0.4
    X0, X1, Y0, Y1 = xl - over, xr + over, -over, D + over
    ze = H - over * k
    top = kh_roof(B, X0, X1, Y0, Y1, ze, k, 'slate', 'hip', axis='y', t=0.08)
    eave_gutter(B, [(X0 + 0.05, Y0 - 0.045), (X1 - 0.05, Y0 - 0.045)], ze + 0.06, mat='pipe', size=0.1)
    downpipe_corner(B, X1 - 0.3, Y0 - 0.1, xr + 0.07, 0.25, ze - 0.02, 1)
    # the door under its canopy, two steps
    steps(B, F, door_o[0] - 0.25, door_o[1] + 0.25, [0.3, 0.15], tread=0.35, mat='khporch')
    door(B, F, door_o[0], door_o[1], 0.3, 2.4, depth=0.15, mat='accent', panels=((1, 0),), glass=None, casing=False,
         lining='khbronze', knob='kmalu', name='Door')
    lf = F.off(-0.15 + 0.035)
    decal(B, lf, door_o[0] + 0.16, door_o[0] + 0.28, 0.65, 2.15, 0.006, 'kh_frost')
    put(B, lf, fbox((door_o[1] - 0.16, 0.95, 0.0), (door_o[1] - 0.12, 1.55, 0.05), 0.008, 'kmalu'))
    put(B, F, fbox((door_o[0] - 0.3, 2.62, 0.0), (door_o[1] + 0.3, 2.7, 1.0), 0.012, 'khbronze'))
    B.feat('front', 'ao', a0=door_o[0] - 0.3, a1=door_o[1] + 0.3, b=2.62, length=0.4, k=0.5)
    name_plate(B, F, door_o[0] - 0.22, 1.55, B.name, back='kmstoned')
    intercom(B, F, door_o[0] - 0.22, 1.15)
    porch_light(B, F, door_o[1] + 0.17, 2.1)
    post_box(B, F, -0.3, 0.95, mat='khbronze')
    # windows
    kh_window(B, F, *wg, screen='right', box='shutter', glass='glass1', frame='khbronze')
    kh_window(B, F, *wsm, frosted=True, grille=True, screen=None, frame='khbronze')
    kh_window(B, F, *u1, screen='right', box='shutter', glass='glass2', frame='khbronze')
    kh_window(B, F, *u2, screen='left', box='shutter', glass='glass0', frame='khbronze')
    kh_window(B, F, *u3, frosted=True, screen=None, frame='khbronze')
    kh_window(B, Rt, 3.6, 4.6, 1.0, 2.1, screen='right', frame='khbronze', register=False)
    kh_window(B, Rt, 2.6, 3.8, 3.8, 4.9, screen='right', frame='khbronze', register=False)
    kh_window(B, Lf, -4.4, -3.4, 1.0, 2.1, screen='right', frame='khbronze', register=False)
    # the carport: posts on its outer side, beams cantilevered back to the house, a clear roof; the slab is left empty
    cx0, cx1, cy0, cy1 = xr + 0.05, W / 2, -0.75, D - 1.6
    px = cx1 - 0.1
    for y in (cy0 + 0.35, cy1 - 0.4):
        B.add(cbox2((px - 0.045, y - 0.045, 0.0), (px + 0.045, y + 0.045, 2.42), 0.008, 'khbronze'))
    B.add(cbox2((px - 0.06, cy0, 2.32), (px + 0.06, cy1, 2.5), 0.01, 'khbronze'))
    for y in np.linspace(cy0 + 0.05, cy1 - 0.05, 6):
        B.add(cbox2((cx0, y - 0.025, 2.42), (cx1, y + 0.025, 2.5), 0.006, 'khbronze'))
    B.add(cbox2((cx0, cy0 - 0.02, 2.4), (cx1, cy0 + 0.06, 2.56), 0.008, 'khbronze'))
    mb = MB()
    mb.face([(cx0, cy0, 2.53), (cx1, cy0, 2.53), (cx1, cy1, 2.53), (cx0, cy1, 2.53)], 'khpoly', (0, 0, 1))
    mb.face([(cx0, cy0, 2.515), (cx0, cy1, 2.515), (cx1, cy1, 2.515), (cx1, cy0, 2.515)], 'khpoly', (0, 0, -1), 0.9)
    B.add(mb.bm())
    for x in np.arange(cx0 + 0.03, cx1, 0.8):          # the panels' glazing bars
        B.add(box((x - 0.02, cy0, 2.53), (x + 0.02, cy1, 2.555), 'khbronze', skip=('-z',)))
    concrete_pad(B, cx0, cx1, cy0, cy1 + 0.4, 0.02)
    B.attach.append(('Carport', (round((cx0 + cx1) / 2, 3), 1.6, 0.0)))
    ground_ac(B, (xr + 0.32, 5.6, 0.0), yaw=PI / 2)
    gas_meter(B, Rt, 1.0, 0.95)
    hose_reel(B, Rt, 2.6, 0.5)
    # the garden
    hydrangea(B, (-3.3, -0.5, 0.0), 0.45, seed=9)
    pot(B, (door_o[0] - 0.65, -0.35, 0.0), 0.15, 0.28, 'khpotp', 'tall', seed=61)
    # weathering (newer: a little mould under the eaves, salt low down, the siding's joints)
    B.feat('front', 'kh_siding', a0=xl, a1=xr, b0=v0, b1=H, ph=0.455)
    mould(B, 'front', xl, xr, H, 0.6, 0.6)
    B.feat('front', 'kh_salt', a0=xl, a1=xr, b0=0.45, b1=1.3, k=0.4)
    return top + 0.1


# ================================================================ BungalowKM
def bungalow(B):
    """A one-storey house under an irimoya kawara roof: a raised floor, a lattice genkan door, an engawa (the veranda
    corridor) behind sliding glass doors with shoji behind it, and a stone step to climb to it."""
    W, H, D = B.W, B.H, B.D
    F, Rt, Bk, Lf = frames(B)
    v0 = 0.5
    door_o = (-3.0, -1.7)
    eg = (-1.1, 3.25, 0.52, 2.3)
    wall(B, F, -W / 2, W / 2, H, [(door_o[0], door_o[1], 0.2, 2.3), eg], v0)
    wall(B, Rt, 0, D, H, [(2.0, 3.5, 0.95, 2.05)], v0)
    wall(B, Lf, -D, 0, H, [(-4.2, -3.2, 1.1, 2.0)], v0)
    wall(B, Bk, -W / 2, W / 2, H, [(-1.0, 0.4, 1.1, 2.0)], v0)
    for path, closed in ring_path(B, gaps=[door_o, (eg[0], eg[1])]):
        plinth(B, path, 0.5, out=0.03, mat='stone', closed=closed)
    B.add(box((eg[0], -0.02, 0.0), (eg[1], 0.0, 0.5), 'kmstoned', skip=('+y', '-z')))
    over, k = 1.0, 0.5
    X0, X1, Y0, Y1 = -W / 2 - over, W / 2 + over, -over, D + over
    ze = H - over * k
    top = kh_roof(B, X0, X1, Y0, Y1, ze, k, 'kawara', 'irimoya', dg=2.0, e=0.35, moss='back', gable_mat='khplaster', oni=0.85)
    downpipe_corner(B, X1 - 0.35, Y0 - 0.1, W / 2 + 0.07, 0.3, ze - 0.02, 1)
    # the genkan: a stone slab, a lattice door with frosted glass
    B.add(fbox((door_o[0] - 0.25, -0.9, 0.0), (door_o[1] + 0.25, 0.0, 0.17), 0.03, 'kmstone'))
    kh_genkan(B, F, door_o[0], door_o[1], 0.2, mat='accent', frame='accent', bars=5)
    name_plate(B, F, door_o[0] - 0.22, 1.5, B.name, back='kmsilver')
    post_box(B, F, door_o[0] - 0.22, 0.75, mat='accentp')
    porch_light(B, F, door_o[1] + 0.25, 2.0)
    # the engawa: glass doors (clear) on two tracks, the polished floor behind them, shoji at its back, a ceiling
    mb = MB()
    u0_, u1_, z0, z1 = eg
    dpt = 0.95
    mb.face([(u0_, z0, 0.0), (u1_, z0, 0.0), (u1_, z0, -dpt), (u0_, z0, -dpt)], 'khfloor', (0, 1, 0), 1.0)
    mb.face([(u0_, z1, 0.0), (u0_, z1, -dpt), (u1_, z1, -dpt), (u1_, z1, 0.0)], 'khwood', (0, -1, 0), 0.7)
    mb.face([(u0_, z0, 0.0), (u0_, z0, -dpt), (u0_, z1, -dpt), (u0_, z1, 0.0)], 'wallw', (1, 0, 0), 0.8)
    mb.face([(u1_, z0, 0.0), (u1_, z1, 0.0), (u1_, z1, -dpt), (u1_, z0, -dpt)], 'wallw', (-1, 0, 0), 0.8)
    shoji_face(mb, u0_, u1_, z0, z1, -dpt)
    mb.face([(u0_, z0, -dpt + 0.002), (u1_, z0, -dpt + 0.002), (u1_, z0 + 0.08, -dpt + 0.002), (u0_, z0 + 0.08, -dpt + 0.002)], 'khwood', (0, 0, 1), 0.8)
    n = 4
    for j in range(n):
        a = u0_ + (u1_ - u0_) * j / n - (0.02 if j else 0.0); b = u0_ + (u1_ - u0_) * (j + 1) / n + (0.02 if j < n - 1 else 0.0)
        w0 = -0.05 if j % 2 == 0 else -0.09
        for (x0, x1) in ((a, a + 0.045), (b - 0.045, b)):
            bar(mb, x0, z0, x1, z1, w0 - 0.03, w0, 'accent')
        for (y0, y1) in ((z0, z0 + 0.1), (z1 - 0.06, z1), (z0 + 0.78, z0 + 0.82)):
            bar(mb, a + 0.045, y0, b - 0.045, y1, w0 - 0.03, w0, 'accent', ends=True)
    mb.face([(u0_, z0 - 0.02, 0.01), (u1_, z0 - 0.02, 0.01), (u1_, z0 - 0.02, -0.12), (u0_, z0 - 0.02, -0.12)], 'accent', (0, 1, 0), 0.9)
    put(B, F, mb.bm())
    put(B, F, fbox((u0_ - 0.06, z1, 0.0), (u1_ + 0.06, z1 + 0.12, 0.04), 0.01, 'accent'))
    B.windows.append({'center': [round((u0_ + u1_) / 2, 3), -0.05, round((z0 + z1) / 2, 3)], 'size': [round(u1_ - u0_, 3), round(z1 - z0, 3)], 'wall': 'front'})
    B.feat('front', 'opening', a0=u0_, a1=u1_, b0=z0, b1=z1)
    # the stone step (kutsunugi-ishi) before the glass doors
    B.add(blob((0.95, -0.42, 0.13), (0.62, 0.3, 0.16), 'kmstone', 8, 2, 4, 0.08, flat_bottom=0.45))
    B.add(blob((2.35, -0.6, 0.05), (0.32, 0.22, 0.08), 'kmstoned', 7, 2, 5, 0.1, flat_bottom=0.45))
    kh_window(B, Rt, 2.0, 3.5, 0.95, 2.05, screen='right', frame='khbronze', register=False)
    kh_window(B, Lf, -4.2, -3.2, 1.1, 2.0, frosted=True, grille=True, screen=None, register=False)
    gas_meter(B, Rt, 0.9, 0.9)
    # the garden
    hydrangea(B, (3.0, -0.58, 0.0), 0.48, seed=12, cols=('khhyd1', 'khhyd2', 'khhyd1'))
    hydrangea(B, (-0.55, -0.5, 0.0), 0.36, seed=13, cols=('khhyd3', 'khhyd2'))
    pot(B, (door_o[0] - 0.5, -0.32, 0.0), 0.15, 0.26, 'khpotp', 'grass', seed=71)
    # weathering
    mould(B, 'front', -W / 2, W / 2, H, 0.9)
    mould(B, 'right', 0, D, H, 0.8); mould(B, 'left', 0, D, H, 0.8)
    B.feat('front', 'kh_salt', a0=-W / 2, a1=W / 2, b0=0.5, b1=1.6, k=0.6)
    B.feat('front', 'kh_crack', cracks=[(door_o[0] - 0.02, 2.3, math.pi - 0.5, 0.35)], k=0.7)
    return top + 0.26


# ================================================================ ApartmentKM
def apartment(B):
    """A two-storey wooden apaato of six flats: an open walkway along the front of the upper floor on steel columns, the
    steel stair up to it with bicycle space under it, a door to each flat with its number, a name slot, its meter, a barred
    kitchen window; the mail boxes, the building's name."""
    W, H, D = B.W, B.H, B.D
    F, Rt, Bk, Lf = frames(B)
    v0 = 0.36
    gf = 2.85
    over, k = 1.22, 0.3
    X0, X1, Y0, Y1 = -W / 2 - 0.4, W / 2 + 0.4, -over, D + 0.45
    ze = H - over * k
    hb = under_z(ze, k, Y0, Y1, D)
    ymid = (Y0 + Y1) / 2
    apex = ze + (ymid - Y0) * k
    bays = [(-3.35, -0.2), (-0.2, 2.95), (2.95, 6.0)]
    ops = []
    for xa, xb in bays:
        for z0 in (0.12, gf):
            ops += [(xa + 0.3, xa + 1.1, z0, z0 + 2.0), (xa + 1.75, xa + 2.6, z0 + 1.1, z0 + 1.85)]
    ops += [(-5.3, -4.6, 4.0, 4.6)]
    wall(B, F, -W / 2, W / 2, H, ops, v0)
    side = [(0, H), (ymid, apex), (D, hb)]
    wall(B, Rt, 0, D, side, [(3.0, 4.0, 1.0, 1.9), (3.0, 4.0, 3.9, 4.8)], v0)
    wall(B, Lf, -D, 0, [(-u, v) for u, v in reversed(side)], [(-5.0, -4.0, 3.9, 4.8)], v0)
    wall(B, Bk, -W / 2, W / 2, hb, [(x - 0.9, x + 0.9, z, z + 1.8) for x in (-4.5, -1.5, 1.5, 4.5) for z in (0.6, 3.3)][:6], v0)
    for path, closed in ring_path(B, gaps=[(xa + 0.3, xa + 1.1) for xa, _ in bays]):
        plinth(B, path, 0.38, out=0.02, mat='stone', closed=closed)
    top = kh_roof(B, X0, X1, Y0, Y1, ze, k, 'seam', 'gable', t=0.08, barge='kmmetal')
    downpipe_corner(B, X1 - 0.12, Y0 - 0.1, W / 2 + 0.07, 0.2, ze - 0.02, 1)
    # the walkway: a slab on steel columns, a railing of bars
    wy = 1.15
    B.add(cbox2((-3.35, -wy, gf - 0.17), (W / 2, 0.0, gf - 0.02), 0.012, 'conc'))
    for x in (-3.28, -0.2, 2.95, W / 2 - 0.08):
        B.add(cbox2((x - 0.05, -wy + 0.02, 0.0), (x + 0.05, -wy + 0.12, gf - 0.17), 0.008, 'accentp'))
    yr = -wy + 0.05
    zt = gf + 1.08
    for x in (-3.3, -0.2, 2.95, W / 2 - 0.05):
        B.add(box((x - 0.03, yr - 0.03, gf - 0.02), (x + 0.03, yr + 0.03, zt), 'accentp', skip=('-z',)))
    B.add(cbox2((-3.35, yr - 0.035, zt - 0.05), (W / 2, yr + 0.035, zt + 0.01), 0.01, 'accentp'))
    B.add(box((-3.35, yr - 0.02, gf + 0.05), (W / 2, yr + 0.02, gf + 0.09), 'accentp', skip=('-x', '+x')))
    for x in np.arange(-3.2, W / 2 - 0.08, 0.15):
        B.add(box((x - 0.01, yr - 0.01, gf + 0.09), (x + 0.01, yr + 0.01, zt - 0.05), 'accentp', skip=('-z', '+z')))
    B.add(cbox2((W / 2 - 0.06, -wy, zt - 0.05), (W / 2, 0.0, zt + 0.01), 0.008, 'accentp'))
    for y in np.arange(-wy + 0.18, -0.05, 0.13):
        B.add(box((W / 2 - 0.04, y - 0.01, gf + 0.0), (W / 2 - 0.02, y + 0.01, zt - 0.05), 'accentp', skip=('-z', '+z')))
    B.feat('front', 'ao', a0=-3.35, a1=W / 2, b=gf - 0.17, length=0.6, k=0.5)
    mould(B, 'front', -3.35, W / 2, gf - 0.17, 0.5, 0.8)
    # the stair, rising along the front from the left end to the walkway, the bicycles' space under it
    sx0, sx1, n = -W / 2 + 0.05, -3.35, 15
    rise = (gf - 0.02) / n; run = (sx1 - sx0) / (n - 1)
    sy0, sy1 = -wy + 0.02, -0.3
    for y in (sy0, sy1):
        B.add(sweep([(sx0 + 0.1, y, 0.16), (sx1 + 0.02, y, gf - 0.02)], (0, 0, 1),
                    [(-0.16, -0.025), (0.06, -0.025), (0.06, 0.025), (-0.16, 0.025)], 'accentp', caps=True))
    for i in range(1, n):
        x = sx0 + (i - 1) * run
        B.add(box((x - 0.02, sy0 + 0.02, i * rise - 0.03), (x + run + 0.03, sy1 - 0.02, i * rise), 'khsteel'))
    hy = sy0 - 0.03
    for x in (sx0 + 0.05, (sx0 + sx1) / 2, sx1 - 0.05):
        zb = max(0.0, (x - sx0) / (sx1 - sx0) * (gf - 0.02))
        B.add(box((x - 0.02, hy - 0.02, zb), (x + 0.02, hy + 0.02, zb + 0.95), 'accentp', skip=('-z',)))
    for dz in (0.92, 0.48):
        B.add(tube([(sx0 - 0.05, hy, dz), (sx1 + 0.05, hy, gf - 0.02 + dz)], 0.022, 'accentp', 6))
    put(B, F, tube([(-W / 2 + 0.1, 0.9 + 0.0, 0.08), (-3.4, gf - 0.02 + 0.85, 0.08)], 0.02, 'kmalu', 6))
    concrete_pad(B, -W / 2, -3.35, -wy - 0.05, 0.0, 0.025)
    decal(B, F, -5.75, -5.25, 1.35, 1.6, 0.02, 'kh_apt')
    # the mail boxes, the meters' panel, the building's name
    put(B, F, fbox((-4.75, 0.95, 0.0), (-3.85, 1.55, 0.2), 0.01, 'kmalu'))
    decal(B, F, -4.73, -3.87, 0.97, 1.53, 0.202, 'kh_postbank')
    put(B, F, fbox((-5.6, 3.3, 0.0), (-4.2, 3.68, 0.04), 0.008, 'khwood'))
    decal(B, F, -5.55, -4.25, 3.33, 3.65, 0.042, 'kh_apt')
    # the flats' fronts
    k_ = 0
    for z0 in (0.12, gf):
        for bi, (xa, xb) in enumerate(bays):
            first = k_ == 0
            door(B, F, xa + 0.3, xa + 1.1, z0, z0 + 2.0, depth=0.12, mat='accent', panels=((1, 1),), glass=None, casing=False,
                 lining='khsteel', knob='kmalu', register=first, name='Door')
            lf = F.off(-0.12 + 0.035)
            decal(B, lf, xa + 0.55, xa + 0.85, z0 + 1.42, z0 + 1.55, 0.004, 'kh_slot')
            u0 = k_ / 6.0
            mb = MB()
            mb.face([(xa + 0.45, z0 + 2.06, 0.03), (xa + 0.95, z0 + 2.06, 0.03), (xa + 0.95, z0 + 2.2, 0.03), (xa + 0.45, z0 + 2.2, 0.03)],
                    'tex', (0, 0, 1), 1.0, lambda co, xa=xa, z0=z0, u0=u0: reg_uv('kh_rooms', u0 + (co.x - xa - 0.45) / 0.5 / 6.0, (co.y - z0 - 2.06) / 0.14))
            put(B, F, mb.bm())
            put(B, F, fbox((xa + 0.43, z0 + 2.04, 0.0), (xa + 0.97, z0 + 2.22, 0.028), 0.004, 'kmalu'))
            meter_box(B, F, xa + 1.42, z0 + 1.45, w=0.26, h=0.36, mat='khivory')
            kh_window(B, F, xa + 1.75, xa + 2.6, z0 + 1.1, z0 + 1.85, frosted=True, grille=True, screen=None, register=False, streak=0.8, gp=0.12)
            if z0 < 1.0: gas_meter(B, F, xa + 2.82, z0 + 0.45, floor=z0)
            put(B, F, fbox((xa + 0.6, z0 + 2.32, 0.0), (xa + 0.8, z0 + 2.46, 0.04), 0.008, 'khivory'))
            put(B, F, fbox((xa + 0.62, z0 + 2.34, 0.04), (xa + 0.78, z0 + 2.44, 0.1), 0.02, 'lamp'))
            lamp_at(B, F.P(xa + 0.7, z0 + 2.39, 0.1))
            B.feat('front', 'kh_rust', pts=[(xa + 0.32, z0 + 1.0), (xa + 1.08, z0 + 0.4)], length=0.4, k=0.6)
            k_ += 1
    kh_window(B, F, -5.3, -4.6, 4.0, 4.6, frosted=True, grille=True, screen=None, register=False)
    kh_window(B, Rt, 3.0, 4.0, 1.0, 1.9, frosted=True, grille=True, screen=None, register=False)
    kh_window(B, Rt, 3.0, 4.0, 3.9, 4.8, frosted=True, grille=True, screen=None, register=False)
    # a washing machine by an upper door, a drain pipe from each upper kitchen
    wx = 5.55
    B.add(cbox2((wx - 0.3, -0.62, gf - 0.02), (wx + 0.3, -0.05, gf + 0.88), 0.03, 'white'))
    B.add(cbox2((wx - 0.28, -0.6, gf + 0.88), (wx + 0.28, -0.07, gf + 0.92), 0.02, 'khgrey'))
    B.add(box((wx - 0.25, -0.625, gf + 0.72), (wx + 0.25, -0.62, gf + 0.84), 'khgrey', skip=('+y',)))
    for xa, xb in bays:
        put(B, F, tube([(xa + 2.68, gf + 1.3, 0.06), (xa + 2.68, gf - 0.15, 0.06), (xa + 2.68, 0.3, 0.06), (xa + 2.68, 0.2, 0.0)], 0.03, 'khgrey', 6))
    # weathering: mould under the walkway and the eaves, rust from the steel, salt, a crack or two
    mould(B, 'front', -W / 2, W / 2, H, 1.0)
    B.feat('front', 'kh_salt', a0=-W / 2, a1=W / 2, b0=0.4, b1=1.5, k=0.6)
    B.feat('front', 'kh_salt', a0=-W / 2, a1=W / 2, b0=gf, b1=gf + 1.2, k=0.4)
    B.feat('front', 'kh_crack', cracks=[(bays[0][0] + 1.1, gf + 2.0, 0.6, 0.4), (bays[2][0] + 1.75, 1.1, math.pi + 0.8, 0.35)], k=0.8)
    mould(B, 'right', 0, D, H, 0.8); mould(B, 'left', 0, D, H, 0.8)
    return top + 0.1


# ================================================================ BoardFenceKM
def board_fence(B):
    """A dark-stained board fence (yamato-bari: boards alternately on either face of the rails), its cap board, the
    posts behind; weathered, silvered low down, salt-bloomed. 4 m, tiling end to end (a post every 2 m)."""
    W, H = B.W, B.H
    n = 22
    p = W / n
    rng = np.random.default_rng(3)
    bw = p * 0.62
    for i in range(n):
        for side, y0, y1 in ((0, -0.045, -0.025), (1, 0.025, 0.045)):
            x = -W / 2 + (i + 0.25 + 0.5 * side) * p
            bm = box((x - bw / 2, y0, 0.04), (x + bw / 2, y1, H - 0.08), 'wall', skip=('-z', '+z'))
            B.add(bm, shade=float(rng.uniform(0.84, 1.06)))
    for z in (0.25, H - 0.35):
        B.add(box((-W / 2, -0.025, z - 0.045), (W / 2, 0.025, z + 0.045), 'accent', skip=('-x', '+x')))
    for x in (-W / 4, W / 4):
        B.add(box((x - 0.045, -0.025, 0.0), (x + 0.045, 0.025, H - 0.08), 'accent', skip=('-z',)))
    B.add(box((-W / 2, -0.06, H - 0.08), (W / 2, 0.06, H - 0.04), 'accent', skip=('-x', '+x', '-z')))
    B.add(sweep([(-W / 2, 0.0, H - 0.04), (W / 2, 0.0, H - 0.04)], (0, 0, 1), [(0.0, -0.075), (0.012, -0.075), (0.04, 0.0), (0.012, 0.075), (0.0, 0.075)],
                'accent', caps=False))
    B.feat('front', 'kh_tone', a0=-W, a1=W, b0=-1, b1=H + 1, col=(0.58, 0.56, 0.55))
    B.feat('front', 'kh_grain', a0=-W / 2 - 0.7, a1=W / 2 + 0.7, b0=0.0, b1=H, bw=p / 2, dark=0.75, silver=1.0, seed=5.0)
    B.feat('front', 'kh_salt', a0=-W / 2 - 0.7, a1=W / 2 + 0.7, b0=0.0, b1=H, col=(0.98, 0.98, 0.97), k=0.9)
    B.feat('front', 'kh_moss', a0=-W / 2 - 0.7, a1=W / 2 + 0.7, b=0.35, k=0.8)
    return H


# ================================================================ BlockWallKM
def block_wall(B):
    """A concrete block garden wall, 4 m (tiling end to end): five courses in stack bond with a band of perforated
    decorative blocks, a capping course; lime run from the joints, rust stains, moss and grime at its foot."""
    W, H = B.W, B.H
    t = B.D / 2
    Fw = WF((0, -t, 0), (1, 0, 0), 'front')
    Bw = WF((0, t, 0), (-1, 0, 0), 'back')
    zc = H - 0.2
    holes = []
    for j in range(10):                       # the decorative band: every block pierced by three slots
        xa = -W / 2 + 0.4 * j
        for a in (0.055, 0.17, 0.285):
            holes.append((xa + a, xa + a + 0.06, 0.635, 0.765))
    wall(B, Fw, -W / 2, W / 2, zc, holes, 0.0)
    wall(B, Bw, -W / 2, W / 2, zc, [(-b, -a, c, d) for a, b, c, d in holes], 0.0)
    mb = MB()
    for a, b, c, d in holes:
        mb.face([(a, -t, c), (a, t, c), (a, t, d), (a, -t, d)], 'wall', (1, 0, 0), 0.6)
        mb.face([(b, -t, c), (b, -t, d), (b, t, d), (b, t, c)], 'wall', (-1, 0, 0), 0.6)
        mb.face([(a, -t, d), (a, t, d), (b, t, d), (b, -t, d)], 'wall', (0, 0, -1), 0.45)
        mb.face([(a, -t, c), (b, -t, c), (b, t, c), (a, t, c)], 'wall', (0, 0, 1), 0.75)
    for x, sx in ((-W / 2, -1), (W / 2, 1)):
        mb.face([(x, -t, 0.0), (x, t, 0.0), (x, t, zc), (x, -t, zc)], 'wall', (sx, 0, 0), 0.8)
    B.add(mb.bm())
    B.add(cbox2((-W / 2, -t - 0.01, zc), (W / 2, t + 0.01, H - 0.03), 0.01, 'wall'))
    B.add(sweep([(-W / 2, 0.0, H - 0.035), (W / 2, 0.0, H - 0.035)], (0, 0, 1),
                [(0.0, -t - 0.01), (0.02, -t - 0.01), (0.035, -t * 0.4), (0.035, t * 0.4), (0.02, t + 0.01), (0.0, t + 0.01)], 'wall', caps=True))
    B.feat('front', 'kh_blocks', a0=-W / 2, a1=W / 2, b0=0.0, b1=H, bw=0.4, bh=0.2, bond=0.0)
    B.feat('front', 'kh_streak', a0=-W / 2, a1=W / 2, b=zc, length=0.7, k=0.7, every=0.3)
    B.feat('front', 'kh_rust', pts=[(-1.2, zc - 0.02), (1.4, zc - 0.02)], length=0.5, k=0.7)
    B.feat('front', 'kh_moss', a0=-W / 2 - 0.7, a1=W / 2 + 0.7, b=0.38, k=1.0)
    B.feat('front', 'kh_salt', a0=-W / 2, a1=W / 2, b0=0.0, b1=0.9, k=0.4)
    return H


# ================================================================ GateKM
def gate(B):
    """Two concrete block gate posts with caps and an aluminium accordion gate between them; a post box and an intercom
    on the posts."""
    W, H = B.W, B.H
    pw, pd = 0.3, 0.3
    for sx in (-1, 1):
        x0, x1 = (W / 2 - pw, W / 2) if sx > 0 else (-W / 2, -W / 2 + pw)
        B.add(box((x0, -pd / 2, 0.0), (x1, pd / 2, H - 0.08), 'wall', skip=('-z',)))
        B.add(cbox2((x0 - 0.02, -pd / 2 - 0.02, H - 0.08), (x1 + 0.02, pd / 2 + 0.02, H), 0.015, 'wall'))
    gx0, gx1 = -W / 2 + pw, W / 2 - pw
    zb, ztp = 0.09, 1.08
    nb = 8
    xs = np.linspace(gx0 + 0.04, gx1 - 0.04, nb + 1)
    for x in xs:
        B.add(box((x - 0.012, -0.018, zb), (x + 0.012, 0.018, ztp), 'kmalu', skip=('-z',)))
    for zr in (zb, (zb + ztp) / 2, ztp):
        pass
    zm = (zb + ztp) / 2
    for a, b in zip(xs[:-1], xs[1:]):
        for z0, z1 in ((zb + 0.03, zm), (zm, ztp - 0.03)):
            B.add(tube([(a, -0.01, z0), (b, -0.01, z1)], 0.008, 'kmalu', 4, caps=False))
            B.add(tube([(a, 0.01, z1), (b, 0.01, z0)], 0.008, 'kmalu', 4, caps=False))
    B.add(cbox2((gx0, -0.03, ztp - 0.01), (gx1, 0.03, ztp + 0.04), 0.008, 'kmalu'))
    for x in (xs[0], xs[len(xs) // 2], xs[-1]):
        wh, _ = lathe([(0.0, -0.025), (0.035, -0.025), (0.035, 0.025), (0.0, 0.025)], 8, 'black')
        xform(wh, T(x, 0.0, 0.045) @ R(PI / 2, 'X')); B.add(wh)
    B.add(cbox2((gx1 - 0.08, -0.05, 0.75), (gx1 - 0.01, 0.05, 0.85), 0.01, 'black'))
    PL = WF((-W / 2 + pw / 2, -pd / 2, 0), (1, 0, 0), 'front')
    PR = WF((W / 2 - pw / 2, -pd / 2, 0), (1, 0, 0), 'front')
    intercom(B, PL, 0.0, 0.92)
    put(B, PR, fbox((-0.12, 0.55, 0.0), (0.12, 0.85, 0.09), 0.012, 'khbronze'))
    put(B, PR, box((-0.08, 0.76, 0.09), (0.08, 0.78, 0.095), 'black', skip=('-z',)))
    B.feat('front', 'kh_blocks', a0=-W / 2 - 0.7, a1=W / 2 + 0.7, b0=0.0, b1=H, bw=0.4, bh=0.2, bond=0.0)
    B.feat('right', 'kh_blocks', a0=-0.7, a1=1.0, b0=0.0, b1=H, bw=0.4, bh=0.2, bond=0.0)
    B.feat('left', 'kh_blocks', a0=-0.7, a1=1.0, b0=0.0, b1=H, bw=0.4, bh=0.2, bond=0.0)
    for mp, a0, a1 in (('front', -W / 2 - 0.7, W / 2 + 0.7), ('right', -0.7, 1.0), ('left', -0.7, 1.0)):
        B.feat(mp, 'kh_moss', a0=a0, a1=a1, b=0.35, k=0.9)
    B.feat('front', 'kh_streak', a0=-W / 2, a1=W / 2, b=H - 0.08, length=0.6, k=0.6, every=0.15)
    B.attach.append(('Gate', (0.0, 0.0, 0.0)))
    return H


# ================================================================ the tiles
def t_nameplate(name):
    def f(dr, w, h, k):
        rng = np.random.default_rng(len(name) * 7 + ord(name[0]) % 13)
        base = (0.86, 0.76, 0.6) if ord(name[0]) % 2 else (0.9, 0.88, 0.82)
        dr.rectangle([0, 0, w, h], fill=_c(base))
        for _ in range(int(14 * k)):
            x = rng.uniform(0, w)
            dr.line([(x, 0), (x + rng.uniform(-3, 3) * k, h)], fill=_c(tuple(c * 0.93 for c in base)), width=max(1, int(k)))
        dr.rectangle([k, k, w - k, h - k], outline=_c(tuple(c * 0.75 for c in base)), width=max(1, int(1.5 * k)))
        jp_label(dr, w, h, name, 0.4, (0.08, 0.07, 0.07), cy=0.5, vertical=True)
    return f


def t_frost(U, V, w, h):
    """Patterned obscure glass (kasumi): pale, soft, a little brighter at the top where the sky is."""
    H_, W_ = U.shape
    n = _noise(H_, W_, (12, 24), 501); n2 = _noise(H_, W_, (40, 80), 502)
    v = 0.66 + 0.1 * V + 0.06 * n + 0.04 * n2
    return np.stack([v * 0.97, v * 0.99, v * 1.02], -1).astype(np.float32)


def t_screen(U, V, w, h):
    """An insect screen over glass: dark grey mesh with the room dim behind, a faint sheen of sky at the top."""
    H_, W_ = U.shape
    n = _noise(H_, W_, (6, 10), 511)
    v = 0.24 + 0.08 * V ** 2 + 0.04 * n
    g = (np.sin(U * w * 1.4) * np.sin(V * h * 1.4) > 0.6).astype(np.float32)
    v = v * (1 - 0.06 * g)
    return np.stack([v, v * 1.03, v * 1.07], -1).astype(np.float32)


def t_shoji(dr, w, h, k):
    """Three shoji panels: white paper on a fine wooden grid (kumiko), a wooden kick board at the foot."""
    paper, wood = (0.93, 0.9, 0.81), (0.56, 0.44, 0.3)
    dr.rectangle([0, 0, w, h], fill=_c(paper))
    pw = w / 3
    for p in range(3):
        x0 = p * pw
        dr.rectangle([x0, h * 0.84, x0 + pw, h], fill=_c(wood))
        for c in range(1, 4):
            x = x0 + pw * c / 4
            dr.line([(x, 0), (x, h * 0.84)], fill=_c(wood), width=max(1, int(1.5 * k)))
        for r_ in range(1, 7):
            y = h * 0.84 * r_ / 7
            dr.line([(x0, y), (x0 + pw, y)], fill=_c(wood), width=max(1, int(1.5 * k)))
        dr.rectangle([x0, 0, x0 + pw, h], outline=_c((0.42, 0.33, 0.22)), width=max(2, int(4 * k)))


def t_rooms(dr, w, h, k):
    cw = w / len(ROOMS)
    for i, s in enumerate(ROOMS):
        dr.rectangle([i * cw, 0, (i + 1) * cw, h], fill=_c((0.94, 0.94, 0.92)))
        dr.rectangle([i * cw + 2 * k, 2 * k, (i + 1) * cw - 2 * k, h - 2 * k], outline=_c((0.5, 0.5, 0.5)), width=max(1, int(k)))
        jp_label(dr, w, h, s, 0.62, (0.1, 0.1, 0.12), cx=(i + 0.5) / len(ROOMS), maxw=0.13)


def t_slot(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.72, 0.73, 0.74)))
    dr.rectangle([w * 0.1, h * 0.18, w * 0.9, h * 0.82], fill=_c((0.97, 0.96, 0.93)))


def t_apt(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.93, 0.92, 0.88)))
    dr.rectangle([2 * k, 2 * k, w - 2 * k, h - 2 * k], outline=_c((0.3, 0.3, 0.3)), width=max(1, int(2 * k)))
    jp_label(dr, w, h, '潮見荘', 0.62, (0.1, 0.1, 0.1), maxw=0.8)


def t_futon(dr, w, h, k):
    """Two futon covers: a blue and white flower print, and a pink check."""
    hw = w / 2
    dr.rectangle([0, 0, hw, h], fill=_c((0.86, 0.9, 0.96)))
    rng = np.random.default_rng(77)
    for _ in range(30):
        x, y, r = rng.uniform(0, hw), rng.uniform(0, h), rng.uniform(4, 9) * k
        for a in range(5):
            ang = a * 2 * math.pi / 5
            cx, cy = x + math.cos(ang) * r * 0.6, y + math.sin(ang) * r * 0.6
            dr.ellipse([cx - r * 0.45, cy - r * 0.45, cx + r * 0.45, cy + r * 0.45], fill=_c((0.3, 0.42, 0.72)))
    dr.rectangle([hw, 0, w, h], fill=_c((0.97, 0.84, 0.86)))
    for x in np.arange(hw, w, 14 * k):
        dr.rectangle([x, 0, x + 5 * k, h], fill=_c((0.9, 0.62, 0.68)))
    for y in np.arange(0, h, 14 * k):
        dr.rectangle([hw, y, w, y + 5 * k], fill=_c((0.9, 0.62, 0.68)))


def t_postbank(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.7, 0.71, 0.72)))
    for i, s in enumerate(ROOMS):
        c, r_ = i % 3, i // 3
        x0, y0 = w * c / 3 + 3 * k, h * r_ / 2 + 3 * k
        x1, y1 = w * (c + 1) / 3 - 3 * k, h * (r_ + 1) / 2 - 3 * k
        dr.rectangle([x0, y0, x1, y1], fill=_c((0.8, 0.81, 0.82)), outline=_c((0.45, 0.45, 0.46)), width=max(1, int(k)))
        dr.rectangle([x0 + (x1 - x0) * 0.2, y0 + (y1 - y0) * 0.2, x1 - (x1 - x0) * 0.2, y0 + (y1 - y0) * 0.3], fill=_c((0.15, 0.15, 0.16)))
        jp_label(dr, w, h, s, 0.14, (0.15, 0.15, 0.15), cx=(c + 0.5) / 3, cy=(r_ + 0.68) / 2, maxw=0.2)


def t_intercom(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_c((0.82, 0.81, 0.77)))
    dr.ellipse([w * 0.35, h * 0.1, w * 0.65, h * 0.1 + w * 0.3], fill=_c((0.1, 0.1, 0.12)))
    for y in np.arange(h * 0.38, h * 0.58, 4 * k):
        dr.line([(w * 0.25, y), (w * 0.75, y)], fill=_c((0.4, 0.4, 0.4)), width=max(1, int(k)))
    dr.rounded_rectangle([w * 0.2, h * 0.66, w * 0.8, h * 0.9], radius=4 * k, fill=_c((0.6, 0.62, 0.66)))


def paint(img, pp):
    """Paints this module's tiles: pp(img, name, painter(dr, w, h, k), background rgb)."""
    for key, nm in NAMES.items():
        pp(img, 'kh_np_' + key, t_nameplate(nm), (0.86, 0.76, 0.6))
    ATL.put(img, 'kh_frost', t_frost)
    ATL.put(img, 'kh_screen', t_screen)
    pp(img, 'kh_shoji', t_shoji, (0.93, 0.9, 0.81))
    pp(img, 'kh_rooms', t_rooms, (0.94, 0.94, 0.92))
    pp(img, 'kh_slot', t_slot, (0.72, 0.73, 0.74))
    pp(img, 'kh_apt', t_apt, (0.93, 0.92, 0.88))
    pp(img, 'kh_futon', t_futon, (0.86, 0.9, 0.96))
    pp(img, 'kh_postbank', t_postbank, (0.7, 0.71, 0.72))
    pp(img, 'kh_intercom', t_intercom, (0.82, 0.81, 0.77))


# ================================================================ the rows
def rows(pal):
    """This module's rows of the kit's SPECS (name, W, H, D, roof, builder, pal(...), front-map top, styles, extra maps)."""
    st = {'wall': 'stucco', 'ppm': 64}
    wd = {'wall': 'render', 'ppm': 64}
    wl = {'wall': 'render', 'ppm': 24}
    kaw = (0.52, 0.54, 0.58)
    return [
        ('HouseTileKM', 8.0, 5.7, 7.5, 2.6, house_tile,
         pal((0.86, 0.80, 0.68), (0.30, 0.27, 0.24), kaw, trim=(0.92, 0.90, 0.86), soffit=(0.78, 0.76, 0.70), stone=(0.64, 0.64, 0.62),
             pipe=(0.84, 0.82, 0.75)), 8.8, st, {'roof': (-4.85, 4.85, -0.85, 8.35), 'roofb': (-4.3, -0.15, -0.85, 0.1)}),
        ('HouseMetalKM', 7.0, 5.8, 7.0, 2.0, house_metal,
         pal((0.92, 0.91, 0.88), (0.25, 0.22, 0.2), (0.24, 0.26, 0.29), trim=(0.9, 0.9, 0.88), soffit=(0.84, 0.83, 0.8), stone=(0.64, 0.64, 0.62),
             pipe=(0.3, 0.3, 0.31)), 8.2, st, {'roof': (-4.2, 4.2, -0.55, 7.55)}),
        ('HouseOldKM', 9.0, 5.5, 8.0, 2.7, house_old,
         pal((0.64, 0.61, 0.57), (0.2, 0.17, 0.15), kaw, trim=(0.86, 0.84, 0.78), soffit=(0.36, 0.3, 0.26), stone=(0.55, 0.54, 0.5),
             pipe=(0.5, 0.42, 0.34)), 8.7, wd, {'roof': (-5.05, 5.05, -1.05, 9.05), 'roofb': (-4.85, 4.85, -1.0, 0.1)}),
        ('HouseShedKM', 8.5, 5.6, 7.0, 2.2, house_shed,
         pal((0.84, 0.80, 0.72), (0.34, 0.30, 0.26), kaw, trim=(0.9, 0.88, 0.84), soffit=(0.74, 0.72, 0.68), stone=(0.62, 0.62, 0.6),
             pipe=(0.74, 0.74, 0.74)), 8.2, st, {'roof': (-4.55, 4.8, -0.8, 7.8)}),
        ('HouseCarportKM', 10.0, 5.7, 7.0, 1.7, house_carport,
         pal((0.88, 0.86, 0.82), (0.36, 0.27, 0.2), (0.3, 0.31, 0.34), trim=(0.93, 0.93, 0.91), soffit=(0.9, 0.89, 0.86), stone=(0.66, 0.66, 0.64),
             pipe=(0.36, 0.33, 0.3)), 7.8, wd, {'roof': (-5.7, 2.4, -0.7, 7.7)}),
        ('BungalowKM', 7.0, 2.9, 6.0, 2.3, bungalow,
         pal((0.88, 0.85, 0.78), (0.24, 0.19, 0.16), kaw, trim=(0.9, 0.88, 0.84), soffit=(0.42, 0.34, 0.27), stone=(0.6, 0.6, 0.57),
             pipe=(0.5, 0.42, 0.34)), 5.6, st, {'roof': (-4.6, 4.6, -1.1, 7.1)}),
        ('ApartmentKM', 12.0, 5.6, 8.0, 1.3, apartment,
         pal((0.86, 0.83, 0.76), (0.62, 0.52, 0.38), (0.32, 0.34, 0.36), trim=(0.9, 0.88, 0.84), soffit=(0.8, 0.79, 0.75), stone=(0.62, 0.62, 0.6),
             pipe=(0.74, 0.74, 0.74)), 7.4, st, {'roof': (-6.5, 6.5, -1.4, 8.55)}),
        ('BoardFenceKM', 4.0, 1.8, 0.12, 0.0, board_fence,
         pal((0.42, 0.38, 0.35), (0.22, 0.19, 0.17), (0.3, 0.3, 0.3)), 2.0, wl, {}),
        ('BlockWallKM', 4.0, 1.2, 0.15, 0.0, block_wall,
         pal((0.72, 0.72, 0.70), (0.6, 0.6, 0.6), (0.3, 0.3, 0.3)), 1.4, wl, {}),
        ('GateKM', 1.6, 1.25, 0.3, 0.0, gate,
         pal((0.72, 0.72, 0.70), (0.74, 0.75, 0.75), (0.3, 0.3, 0.3)), 1.4, wl, {}),
    ]
