# Kamakura's own shops (the Kamakura kit: kit_buildings_kam.py). See kit_buildings_kambase.py.
#
# Low two-storey shops of the old lanes by the station and the shrine approach, the family's home upstairs: dark or silvered
# timber ground floors, mortar or boarded upper floors, grey kawara roofs (one in dark standing-seam metal, one flat with a
# parapet), tiled pent roofs (hisashi) over the shopfronts, noren curtains over sliding glass doors, hand-painted wooden
# signboards and paper lanterns, canvas awnings, goods out front; upstairs aluminium sliding windows with insect screens,
# AC units on brackets, a balcony with laundry, bamboo blinds. Weathered as the brief asks: sun-faded noren and signs,
# silvered and blackened timber, black mould under the eaves and sills, salt bloom and cracked mortar, rust at fixings,
# soot over the tea roaster's vent, moss at the foot of the walls.
#   ShopSembeiKM    手焼きせんべい 汐見堂 (Shiomi-do): a counter window with jars of crackers and a grill, indigo noren.
#   ShopSobaKM      そば処 小波 (Sazanami): dark timber, a lattice window, a white noren, a menu board, a lantern.
#   ShopWagashiKM   和菓子 若葉庵 (Wakaba-an): a glass case of sweets, a pale noren, a hanging signboard, a bench.
#   ShopSouvenirKM  鎌倉みやげ すずなり (Suzunari): tables of tenugui, chopsticks, bells and postcards, an awning, a nobori.
#   ShopFishKM      鮮魚 かもめ屋 (Kamome-ya): styrofoam boxes of whitebait and horse mackerel on ice, a price board.
#   ShopKissaKM     純喫茶 灯台 (Todai): a brown-tiled coffee house with a sample case, a wooden sign, an andon sign.
#   ShopTeaKM       日本茶 緑風園 (Ryokufu-en): a roaster in the window and its vent, tea jars, a dark noren.
#   NoboriKM        a shop's banner flag: 湘南名物 生しらす丼.
# Every name is invented. Signs, noren, menus, price cards and goods are this module's atlas tiles (TILES, paint()).
# The weathering of the walls is painted into each shop's projected wall maps: kit_buildings_atlas.wall_map is wrapped
# here, for this module's models only, to add the km_* features (boards, mould, salt, cracks, rust, moss, soot).
from kit_buildings_kambase import *
from PIL import Image, ImageDraw, ImageFilter
import kit_buildings_atlas as ATL

# ---------------------------------------------------------------- the shops' own colours
KS_MAT = {
    # timber walls painted with boards on the front map (km_boards): weathered dark, silvered
    'kstimb': (0, (0.44, 0.38, 0.33), 'grime', 0.0), 'kssilv': (0, (0.70, 0.67, 0.61), 'grime', 0.0),
    # near-black posts and beams, cedar, a darker stain
    'ksdark': (0, (0.20, 0.17, 0.15), 'white', 0.18), 'kscedar': (0, (0.56, 0.42, 0.30), 'white', 0.15),
    'ksblack': (0, (0.10, 0.09, 0.09), 'white', 0.0),
    # styrofoam, stainless, plastic blue, the bench's red felt, cream canvas, green hose, glazed jars, wet concrete
    'ksstyro': (0, (0.95, 0.95, 0.94), 'white', 0.08), 'ksstain': (0, (0.64, 0.65, 0.66), 'white', 0.05),
    'ksblue': (0, (0.16, 0.38, 0.66), 'white', 0.1), 'ksred': (0, (0.74, 0.12, 0.11), 'white', 0.05),
    'kscream': (0, (0.92, 0.89, 0.80), 'white', 0.1), 'kshose': (0, (0.20, 0.50, 0.30), 'white', 0.0),
    'ksjar': (0, (0.36, 0.24, 0.16), 'white', 0.25), 'ksjar2': (0, (0.52, 0.48, 0.38), 'white', 0.25),
    'ksfloor': (0, (0.40, 0.40, 0.39), 'white', 0.0), 'ksshade': (0, (0.20, 0.18, 0.17), 'white', 0.0),
    'ksbase': (0, (0.22, 0.23, 0.24), 'white', 0.1), 'ksglow': (0, (0.98, 0.56, 0.22), 'white', 0.0),
    'ksnobb': (0, (0.14, 0.30, 0.56), 'white', 0.0), 'ksfelt': (0, (0.62, 0.14, 0.12), 'white', 0.0),
    'kspaper': (0, (0.90, 0.86, 0.76), 'white', 0.0), 'ksrope': (0, (0.70, 0.62, 0.46), 'white', 0.0),
}
for _k, _v in KS_MAT.items():
    if _k not in MAT:
        MAT[_k] = _v; MATS.append(_k); MID[_k] = len(MATS) - 1

# ---------------------------------------------------------------- the shops' tiles (about 100 to 130 px a metre)
TILES = [
    # signboards, noren, lanterns, banners
    ('ks_sg_sembei', 704, 128), ('ks_sg_soba', 576, 112), ('ks_sg_wagashi', 112, 352), ('ks_sg_souv', 768, 96),
    ('ks_sg_fish', 768, 48), ('ks_sg_kissa', 416, 112), ('ks_sg_kissa2', 96, 320), ('ks_sg_tea', 512, 112),
    ('ks_nr_sembei', 384, 144), ('ks_nr_soba', 288, 128), ('ks_nr_wagashi', 320, 112), ('ks_nr_tea', 320, 144),
    ('ks_lt_sembei', 96, 128), ('ks_lt_soba', 96, 128), ('ks_lt_souv', 96, 128),
    ('ks_nobori', 80, 320), ('ks_nobori2', 80, 320),
    # menus, prices, cases, goods
    ('ks_menu_soba', 128, 288), ('ks_price_fish', 160, 224), ('ks_sample', 320, 128), ('ks_case', 320, 128),
    ('ks_jar', 64, 96), ('ks_grill', 192, 96), ('ks_tenugui', 224, 144), ('ks_goods1', 256, 96), ('ks_goods2', 256, 96),
    ('ks_cards', 64, 192), ('ks_fish', 256, 192),
    # interiors through glass and open fronts' back walls
    ('ks_int_sembei', 288, 224), ('ks_int_soba', 192, 224), ('ks_int_wagashi', 224, 224), ('ks_int_tea', 224, 224),
    ('ks_int_kissa', 256, 96), ('ks_back_sembei', 256, 192), ('ks_back_souv', 512, 192), ('ks_back_fish', 448, 192),
    ('ks_back_tea', 256, 192),
    # upstairs: sliding windows with screens, a bamboo blind
    ('ks_win_a', 144, 112), ('ks_win_b', 144, 112), ('ks_sudare', 128, 160),
]

_MINE = set()          # this module's model names (rows() fills it): the wall-map wrapper touches only these


# ================================================================ wall-map weathering (km_* features)
def _weather(B, mp, sub, U, V, w, h):
    feats = [(k, kw) for k, kw in B.feats.get(mp, []) if k.startswith('km_')]
    if not feats:
        return sub
    a0, a1, b0, b1 = B.maps[mp]
    A = a0 + U * (a1 - a0); Z = b0 + V * (b1 - b0)
    ppm = w / (a1 - a0)
    H_, W_ = U.shape
    seed = (sum(map(ord, B.name)) * 13 + sum(map(ord, mp)) * 7) % 9973
    r = np.random.default_rng(seed)
    nz = ATL._noise
    n1 = nz(H_, W_, ((a1 - a0) / 0.3, (b1 - b0) / 0.3), seed + 31)
    n2 = nz(H_, W_, ((a1 - a0) / 1.1, (b1 - b0) / 1.1), seed + 32)
    n3 = nz(H_, W_, ((a1 - a0) / 0.06, (b1 - b0) / 0.6), seed + 33)
    ss = ATL._ss
    for kind, kw in feats:
        if kind == 'km_boards':
            s0, s1, z0, z1 = kw['a0'], kw['a1'], kw['b0'], kw['b1']
            bw = kw.get('bw', 0.2); horiz = kw.get('horiz', False); sil = kw.get('silver', 0.5)
            inside = (A >= s0) & (A <= s1) & (Z >= z0) & (Z <= z1)
            if not inside.any(): continue
            if horiz:
                q = (Z - z0) / bw; idx = np.floor(q); f = q - idx
                tone = np.sin(idx * 12.9898 + 4.1) * 43758.5453; tone = tone - np.floor(tone)
                grain = nz(H_, W_, ((a1 - a0) / 0.9, (b1 - b0) / 0.012), seed + 41)
                shade = (0.80 + 0.16 * tone) * (0.9 + 0.12 * grain)
                shade = shade * (1 - 0.5 * ss(0.14, 0.0, f)) * (1 + 0.06 * ss(0.8, 1.0, f))
                bat = (A - s0) % kw.get('batten', 0.91)
                bd = np.minimum(bat, kw.get('batten', 0.91) - bat)
                shade = shade * (1 - 0.35 * ss(0.035, 0.02, bd)) * (1 + 0.05 * ss(0.025, 0.0, bd))
            else:
                q = (A - s0) / bw; idx = np.floor(q); f = q - idx
                tone = np.sin(idx * 12.9898 + 7.3) * 43758.5453; tone = tone - np.floor(tone)
                grain = nz(H_, W_, ((a1 - a0) / 0.012, (b1 - b0) / 0.9), seed + 42)
                shade = (0.80 + 0.16 * tone) * (0.9 + 0.12 * grain)
                d = np.minimum(f, 1 - f) * bw
                shade = shade * (1 - 0.6 * ss(1.8 / ppm, 0.5 / ppm, d))
                if kw.get('battens'):
                    shade = shade * (1 - 0.25 * ss(0.03, 0.0, np.abs(((A - s0) % 0.45) - 0.225)))
            # silvered patches where the sun and rain have bleached it, blackened ones where water stands
            silver = ss(0.45, 0.8, n2 * 0.7 + n1 * 0.3) * sil
            shade = shade * (1 - silver) + np.minimum(1.0, shade * 1.22) * silver
            shade = shade * (1 - 0.45 * ss(z0 + 0.55, z0, Z) * (0.5 + 0.5 * n1))
            black = ss(0.62, 0.8, n3 * 0.5 + n2 * 0.5) * ss(z0 + 1.6, z0, Z)
            shade = shade * (1 - 0.35 * black)
            # nail heads bleeding rust along the rails
            for zr in kw.get('nails', ()):
                m = ss(0.012, 0.0, np.abs(Z - zr)) * ss(0.3, 0.6, np.sin((A - s0) / bw * math.pi * 2) * 0.5 + 0.5)
                shade = shade * (1 - 0.25 * m)
            sub = np.where(inside[..., None], sub * shade[..., None], sub)
        elif kind == 'km_mould':
            s0, s1, zb, L, k = kw['a0'], kw['a1'], kw['b'], kw.get('L', 0.9), kw.get('k', 0.7)
            inside = ((A >= s0) & (A <= s1) & (Z <= zb + 0.01)).astype(np.float32)
            t = np.clip((zb - Z) / L, 0, 2)
            streak = 0.35 + 0.65 * n3
            m = (1 - ss(0.0, 1.0, t + (n1 - 0.5) * 0.7)) * streak * (0.45 + 0.55 * ss(0.2, 0.7, n2)) * inside
            edge = ss(0.0, 0.25, np.minimum(A - s0, s1 - A))
            sub = ATL._mul(sub, m * edge, (0.40, 0.42, 0.38), k)
        elif kind == 'km_salt':
            s0, s1, z0, z1, k = kw['a0'], kw['a1'], kw['b0'], kw['b1'], kw.get('k', 0.7)
            inside = ((A >= s0) & (A <= s1) & (Z >= z0) & (Z <= z1)).astype(np.float32)
            soft = ss(0.0, 0.25, np.minimum(Z - z0, z1 - Z))
            m = ss(0.42, 0.72, n2 * 0.55 + n1 * 0.45) * inside * soft
            sub = ATL._blend(sub, m, (0.99, 1.0, 1.0), 0.75 * k)
            sp = (np.random.default_rng(seed + 5).random(U.shape) > 0.97).astype(np.float32) * m
            sub = ATL._blend(sub, sp, (1.0, 1.0, 1.0), 0.8)
            # the tide line at its top edge, a little darker
            tl = ss(0.05, 0.0, np.abs(Z - (z0 + (z1 - z0) * (0.7 + 0.2 * n2)))) * inside * ss(0.5, 0.7, n1)
            sub = ATL._mul(sub, tl, (0.86, 0.85, 0.83), 0.5 * k)
        elif kind == 'km_crack':
            for (x, z, ang, length) in kw.get('pts', ()):
                sub = ATL._crack(sub, A, Z, x, z, ang, length, ppm, r, dark=(0.55, 0.52, 0.48))
                if r.random() < 0.6:
                    sub = ATL._crack(sub, A, Z, x + math.cos(ang) * length * 0.5, z + math.sin(ang) * length * 0.5,
                                     ang + r.choice((-1, 1)) * 0.9, length * 0.45, ppm, r, dark=(0.58, 0.55, 0.5))
        elif kind == 'km_rust':
            L = kw.get('L', 0.5)
            for (x, z) in kw['pts']:
                wd = kw.get('w', 0.035)
                m = ss(wd, 0.0, np.abs(A - x) + (n3 - 0.5) * 0.02) * ((Z - (z - L)) / L).clip(0, 1) ** 1.4 * (Z < z)
                sub = ATL._mul(sub, m.astype(np.float32), (0.70, 0.46, 0.30), 0.8)
        elif kind == 'km_moss':
            s0, s1, hh = kw['a0'], kw['a1'], kw.get('h', 0.35)
            m = ss(hh, 0.0, Z) * ss(0.42, 0.7, n1 * 0.6 + n2 * 0.4) * ((A >= s0) & (A <= s1))
            sub = ATL._mul(sub, m.astype(np.float32), (0.58, 0.68, 0.40), 0.75)
        elif kind == 'km_soot':
            x, z, wd, L = kw['a'], kw['b'], kw.get('w', 0.5), kw.get('L', 1.2)
            t = np.clip((Z - z) / L, 0, 1)
            m = ss(wd * (0.4 + 0.8 * t), 0.0, np.abs(A - x) + (n1 - 0.5) * 0.15) * (Z >= z - 0.05) * (1 - t) ** 0.7
            sub = ATL._mul(sub, m.astype(np.float32), (0.30, 0.29, 0.28), 0.85)
        elif kind == 'km_wet':
            s0, s1, hh = kw['a0'], kw['a1'], kw.get('h', 0.2)
            m = ss(hh, 0.0, Z) * ((A >= s0) & (A <= s1))
            sub = ATL._mul(sub, m.astype(np.float32), (0.7, 0.7, 0.72), 0.6)
    return sub


if not getattr(ATL, '_ks_wrapped', False):
    _orig_wall_map = ATL.wall_map

    def _wall_map(B, mp):
        f = _orig_wall_map(B, mp)
        if B.name not in _MINE:
            return f

        def g(U, V, w, h):
            return _weather(B, mp, f(U, V, w, h), U, V, w, h)
        return g
    ATL.wall_map = _wall_map
    ATL._ks_wrapped = True


# ================================================================ shared pieces
GF = 2.95          # the ground floor's beam top


def reg_door(B, wf, x0, x1, z1, name='Door'):
    a0, _ = wf.ab(x0, 0); a1, _ = wf.ab(x1, 0)
    B.feat(wf.mp, 'opening', a0=min(a0, a1), a1=max(a0, a1), b0=0.0, b1=z1)
    c3 = wf.P((x0 + x1) / 2, 0.0, 0)
    B.doors.append({'name': name, 'center': [round(c3.x, 3), round(c3.y, 3), round(c3.z, 3)],
                    'size': [round(x1 - x0, 3), round(z1, 3)], 'wall': wf.mp})


def km_shell(B, ops, zones=None, slope=0.42, eave=0.6, side_ops=(), roof='kawara', pipe_x=None):
    """Walls round a two-storey shop under a ridge along the street (gables at the sides): the front with its openings
    (timber zone on the ground floor unless zones says otherwise), mortar sides and back, a kawara (or standing-seam
    metal) roof with dark barge boards, a gutter and a downpipe. Returns the frames and the roof's top."""
    W, H, D = B.W, B.H, B.D
    F, Rt, Bk, Lf = frames(B)
    k = slope
    rise = D / 2 * k
    zones = [(-W / 2, W / 2, 0.0, GF, 'kstimb')] if zones is None else zones
    wall(B, F, -W / 2, W / 2, H, list(ops), 0.0, zones=list(zones))
    wall(B, Rt, 0, D, [(0, H), (D / 2, H + rise), (D, H)], list(side_ops), 0.0)
    wall(B, Lf, -D, 0, [(-D, H), (-D / 2, H + rise), (0, H)], [(-b, -a, z0, z1) for a, b, z0, z1 in side_ops], 0.0)
    wall(B, Bk, -W / 2, W / 2, H, [], 0.0)
    z0 = H - eave * k
    if roof == 'metal':
        top = pitched(B, 'x', -eave, D + eave, -W / 2, W / 2, z0, (D / 2 + eave) * k, t=0.1, row=20.0, lip=0.0, mat='roof',
                      barge=(True, True), barge_mat='ksdark', soffit='soffit', fascia_mat='ksdark', over=0.12, barge_w=0.18,
                      feat=False)
        B.feat('roof', 'ribs', x0=-W / 2 - 0.12, x1=W / 2 + 0.12, y0=-eave, y1=D + eave, pitch=0.45)
    else:
        top = pitched(B, 'x', -eave, D + eave, -W / 2, W / 2, z0, (D / 2 + eave) * k, t=0.16, row=0.28, mat='roof',
                      barge=(True, True), barge_mat='ksdark', soffit='soffit', fascia_mat='ksdark', over=0.12, barge_w=0.22)
    rafters(B, -W / 2 - 0.1, W / 2 + 0.1, -eave, 0.0, z0, H, step=0.5, r=0.035)
    eave_gutter(B, [(-W / 2 - 0.1, -eave + 0.02), (W / 2 + 0.1, -eave + 0.02)], z0 - 0.05, mat='pipe', size=0.11)
    px = W / 2 - 0.13 if pipe_x is None else pipe_x
    downpipe(B, [(px, -eave - 0.04, z0 - 0.12), (px, -eave - 0.04, z0 - 0.3), (px, -0.07, z0 - 0.62), (px, -0.07, 0.18),
                 (px, -0.18, 0.04)], r=0.04, mat='pipe', brackets=[(px, -0.07, z) for z in (1.2, 3.6, z0 - 0.8)])
    # weathering: soffit shade, black mould under the eaves, salt bloom and splash at the foot, cracks in the mortar
    B.feat('front', 'ao', a0=-W / 2, a1=W / 2, b=H, length=0.55, k=0.55)
    B.feat('front', 'km_mould', a0=-W / 2, a1=W / 2, b=H, L=1.0, k=0.75)
    for mp, (s0, s1) in (('right', (0.0, D)), ('left', (0.0, D))):
        B.feat(mp, 'km_mould', a0=s0, a1=s1, b=H, L=1.3, k=0.6)
        B.feat(mp, 'km_salt', a0=s0, a1=s1, b0=0.0, b1=1.1, k=0.9)
        B.feat(mp, 'km_moss', a0=s0, a1=s1, h=0.35)
        B.feat(mp, 'km_crack', pts=[(s0 + D * 0.3, 1.6, 0.9, 0.7), (s0 + D * 0.7, 4.2, -1.0, 0.6), (s0 + D * 0.5, 6.4, -0.6, 0.5)])
    B.feat('front', 'km_moss', a0=-W / 2, a1=W / 2, h=0.25)
    B.attach.append(('Wire', (round(-W / 2 + 0.4, 3), -0.05, round(H - 0.5, 3))))
    return F, Rt, Bk, Lf, top


def posts(B, wf, xs, z1=GF, beam=(GF - 0.3, GF), w=0.16, mat='ksdark'):
    """Square timber posts at xs (clamped inside the front) and the beam over the shopfront."""
    W = B.W
    for x in xs:
        a = max(-W / 2, min(W / 2 - w, x - w / 2))
        put(B, wf, fbox((a, 0.0, 0.0), (a + w, z1, 0.07), 0.012, mat))
    put(B, wf, fbox((-W / 2, beam[0], 0.0), (W / 2, beam[1], 0.09), 0.015, mat))


def hisashi(B, x0, x1, z, out=0.85, rise=0.36, kind='kawara'):
    """A pent roof over the shopfront: z is its underside at the front edge."""
    if kind == 'kawara':
        pitched(B, 'x', -out, out, x0, x1, z, rise, t=0.1, row=0.25, lip=0.03, mat='kawara', slopes=(0,), ridge=False,
                barge=(True, True), over=0.02, barge_w=0.12, fmap='roofb', fascia_mat='ksdark', soffit='ksdark',
                barge_mat='ksdark')
    else:
        shed(B, x0, x1, -out, 0.0, z, z + rise, t=0.06, pitch=0.2, depth=0.025, mat='kmmetal', edge_mat='kmmetal',
             fascia_mat='ksdark', soffit='ksdark', feat=False)
    B.add(box((x0 - 0.02, -0.07, z + rise + 0.04), (x1 + 0.02, 0.0, z + rise + 0.2), 'galvw', skip=('+y', '-z')))
    rafters(B, x0, x1, -out, 0.0, z, z + rise)
    B.feat('front', 'ao', a0=x0, a1=x1, b=z + rise, length=0.6, k=0.5)
    B.feat('front', 'km_mould', a0=x0, a1=x1, b=z + rise - 0.02, L=0.5, k=0.5)
    B.feat('front', 'km_rust', pts=[(x, z + rise + 0.04) for x in np.linspace(x0 + 0.3, x1 - 0.3, 5)], L=0.3, w=0.03)


def rafters(B, x0, x1, y0, y1, z0, z1, step=0.45, r=0.028):
    """Exposed rafters (taruki) under an eave or a pent roof, from its front edge (y0, underside z0) back to the wall."""
    for x in np.arange(x0 + 0.2, x1 - 0.1, step):
        B.add(tube([(x, y0 + 0.06, z0 - r * 0.7), (x, y1, z1 - r * 0.7)], r, 'ksdark', 4, caps=False))


def km_room(B, x0, x1, z0, z1, depth, back=None, floor='ksfloor', ceil='ksdark'):
    """The shop behind an open front: its back wall (an atlas tile of shelves) and dim sides."""
    mb = MB()
    uvb = (lambda co: reg_uv(back, (co.x - x0) / (x1 - x0), (co.z - z0) / (z1 - z0))) if back else None
    mb.face([(x0, depth, z0), (x1, depth, z0), (x1, depth, z1), (x0, depth, z1)], 'tex' if back else 'interior', (0, -1, 0), 0.85, uvb)
    mb.face([(x0, 0, z0), (x0, depth, z0), (x0, depth, z1), (x0, 0, z1)], 'interior', (1, 0, 0), 0.75)
    mb.face([(x1, 0, z0), (x1, 0, z1), (x1, depth, z1), (x1, depth, z0)], 'interior', (-1, 0, 0), 0.75)
    mb.face([(x0, 0, z1), (x1, 0, z1), (x1, depth, z1), (x0, depth, z1)], ceil, (0, 0, -1), 0.6)
    mb.face([(x0, 0, z0), (x0, depth, z0), (x1, depth, z0), (x1, 0, z0)], floor, (0, 0, 1), 0.75)
    B.add(mb.bm())


def sliding_doors(B, wf, x0, x1, z1, region, n=2, frame='ksdark', kick=0.24, bars=(), depth=0.17, name='Door'):
    """Wooden-framed sliding glass doors in an opening: leaves on alternating tracks, a kick panel, horizontal glazing bars,
    the shop's interior (an atlas tile) behind the glass, a stone threshold."""
    mb = MB()
    reveal(mb, x0, x1, 0.0, z1, depth, bottom=False)
    lw = (x1 - x0) / n
    for i in range(n):
        a = x0 + i * lw - (0.03 if i > 0 else 0.0); b = x0 + (i + 1) * lw + (0.03 if i < n - 1 else 0.0)
        zf = -depth + (0.06 if i % 2 == 0 else 0.1)
        st, top = 0.05, 0.06
        o = (a, 0.0, b, z1); ii = (a + st, kick, b - st, z1 - top)
        ring(mb, o, ii, zf, zf, frame, 'front')
        ring(mb, ii, ii, zf, zf - 0.025, frame, 'in', 0.8)
        mb.face([(a, 0.0, zf - 0.035), (a, z1, zf - 0.035), (a, z1, zf), (a, 0.0, zf)], frame, (-1, 0, 0), 0.7)
        mb.face([(b, 0.0, zf), (b, z1, zf), (b, z1, zf - 0.035), (b, 0.0, zf - 0.035)], frame, (1, 0, 0), 0.7)
        zg = zf - 0.025
        mb.face([(ii[0], ii[1], zg), (ii[2], ii[1], zg), (ii[2], ii[3], zg), (ii[0], ii[3], zg)], 'tex', (0, 0, 1), 1.0,
                lambda co: reg_uv(region, (co.x - x0) / (x1 - x0), co.y / z1, 0.0))
        for zb in bars:
            bar(mb, ii[0], zb - 0.014, ii[2], zb + 0.014, zg, zf - 0.006, frame)
        hx = b - st - 0.05 if i % 2 == 0 else a + st + 0.05
        bar(mb, hx - 0.012, 0.95, hx + 0.012, 1.15, zf, zf + 0.012, 'ksblack')
    put(B, wf, mb.bm())
    put(B, wf, fbox((x0 - 0.02, 0.0, -depth), (x1 + 0.02, 0.05, 0.12), 0.01, 'kmstone'))
    reg_door(B, wf, x0, x1, z1, name)


def noren(B, wf, x0, x1, ztop, length, region, n=3, w=0.1, rod='ksdark', seed=0):
    """A noren on its rod: a joined top band, n panels below (gaps between), each a little lifted by the breeze."""
    rng = np.random.default_rng(seed + 3)
    put(B, wf, tube([(x0 - 0.07, ztop + 0.025, w + 0.005), (x1 + 0.07, ztop + 0.025, w + 0.005)], 0.017, rod, 6))
    for x in (x0 - 0.05, x1 + 0.05):
        put(B, wf, box((x - 0.012, ztop + 0.04, 0.0), (x + 0.012, ztop + 0.065, w + 0.02), 'ksblack', skip=('-z',)))
    band = min(0.14, length * 0.17)
    zb = ztop - length

    def uv(co):
        return reg_uv(region, (co.x - x0) / (x1 - x0), (co.y - zb) / length)
    mb = MB()
    mb.face([(x0, ztop - band, w), (x1, ztop - band, w), (x1, ztop, w), (x0, ztop, w)], 'tex', (0, 0, 1), 1.0, uv)
    gap = 0.03
    cw = (x1 - x0) / n
    for i in range(n):
        a = x0 + i * cw + (gap / 2 if i > 0 else 0.0); b = x0 + (i + 1) * cw - (gap / 2 if i < n - 1 else 0.0)
        zs = [ztop - band, ztop - band - (length - band) * 0.5, zb + rng.uniform(0.0, 0.025)]
        ws = [w, w + rng.uniform(0.004, 0.018), w + rng.uniform(0.01, 0.045)]
        for j in range(2):
            mb.face([(a, zs[j + 1], ws[j + 1]), (b, zs[j + 1], ws[j + 1]), (b, zs[j], ws[j]), (a, zs[j], ws[j])], 'tex', (0, 0, 1), 1.0, uv)
    put(B, wf, mb.bm())
    a0, _ = wf.ab(x0, 0); a1, _ = wf.ab(x1, 0)
    B.feat(wf.mp, 'ao', a0=min(a0, a1), a1=max(a0, a1), b=ztop, length=0.12, k=0.3)


def chochin(B, P, region, h=0.56, r=0.19, hang=0.3):
    """A paper lantern (chochin) at the world point P (its centre), its lettering facing the street, hung on a wire."""
    x, y, z = P
    prof = [(0.0, -h / 2), (r * 0.55, -h * 0.47), (r * 0.86, -h * 0.34), (r, -h * 0.13), (r, h * 0.13), (r * 0.86, h * 0.34),
            (r * 0.55, h * 0.47), (0.0, h / 2)]
    body, _ = lathe(prof, 10, 'tex')
    uv_fn(body, list(body.faces), region, lambda co: (0.5 + 0.5 * co.x / r, (co.z + h / 2) / h), 0.0)
    xform(body, T(x, y, z)); B.add(body)
    for zz, sg in ((-h / 2, -1), (h / 2, 1)):
        cp, _ = lathe([(r * 0.6, 0.0), (r * 0.6, 0.07 * sg), (0.0, 0.075 * sg)], 10, 'ksblack')
        xform(cp, T(x, y, z + zz - 0.025 * sg)); B.add(cp)
    B.add(tube([(x, y, z + h / 2 + 0.05), (x, y, z + h / 2 + hang)], 0.008, 'ksblack', 4))


def kanban(B, wf, x0, x1, z0, z1, region, out=0.1, frame='ksdark', fw=0.05, cap=False):
    """A wooden signboard on the wall: a thick board with a framing edge, the painted face (an atlas tile), iron brackets."""
    put(B, wf, fbox((x0, z0, 0.0), (x1, z1, out), 0.012, frame))
    decal(B, wf, x0 + fw, x1 - fw, z0 + fw, z1 - fw, out + 0.003, region)
    if cap:
        put(B, wf, fbox((x0 - 0.08, z1, -0.0), (x1 + 0.08, z1 + 0.07, out + 0.1), 0.015, frame))
    for x in (x0 + 0.25, x1 - 0.25):
        put(B, wf, box((x - 0.015, z0 - 0.06, 0.0), (x + 0.015, z0, out), 'ksblack', skip=('-z',)))
    a0, _ = wf.ab(x0, 0); a1, _ = wf.ab(x1, 0)
    B.feat(wf.mp, 'ao', a0=min(a0, a1), a1=max(a0, a1), b=z0, length=0.35, k=0.45)
    B.feat(wf.mp, 'km_rust', pts=[(wf.ab(x0 + 0.25, 0)[0], z0 - 0.05), (wf.ab(x1 - 0.25, 0)[0], z0 - 0.05)], L=0.6)
    B.attach.append(('Sign', tuple(round(c, 3) for c in wf.P((x0 + x1) / 2, (z0 + z1) / 2, out))))


def up_window(B, wf, u0, u1, v0, v1, glass='ks_win_a', seed=0, rail=False, register=True):
    """An aluminium sliding window with its insect screen (in the glass tile), an aluminium sill; a hand rail on request."""
    window(B, wf, u0, u1, v0, v1, depth=0.1, fw=0.045, cols=2, frame='kmalu', glass=glass, sill='kmalu', head=None,
           mull=0.035, cheap=True, seed=seed, register=register)
    if rail:
        for zz in (v0 + 0.32, v0 + 0.62):
            put(B, wf, tube([(u0 - 0.04, zz, 0.12), (u1 + 0.04, zz, 0.12)], 0.016, 'kmalu', 4))
        for x in np.linspace(u0 + 0.05, u1 - 0.05, 4):
            put(B, wf, box((x - 0.015, v0 + 0.05, 0.0), (x + 0.015, v0 + 0.66, 0.13), 'kmalu', skip=('-z',)))
    a0, _ = wf.ab(u0, 0); a1, _ = wf.ab(u1, 0)
    B.feat(wf.mp, 'km_mould', a0=min(a0, a1) - 0.05, a1=max(a0, a1) + 0.05, b=v0 - 0.08, L=0.7, k=0.55)
    B.feat(wf.mp, 'km_salt', a0=min(a0, a1) - 0.2, a1=max(a0, a1) + 0.2, b0=v0 - 0.9, b1=v0 - 0.1, k=0.5)


def sudare(B, wf, x0, x1, ztop, length, w=0.07):
    decal(B, wf, x0, x1, ztop - length, ztop, w, 'ks_sudare')
    put(B, wf, tube([(x0 - 0.03, ztop + 0.015, w + 0.005), (x1 + 0.03, ztop + 0.015, w + 0.005)], 0.012, 'kscedar', 4))


def ac_front(B, wf, x, y, w=0.74, h=0.52):
    ac_unit(B, wf, x, y, 0.0, w=w, h=h, d=0.26)
    a0, _ = wf.ab(x - w / 2 + 0.1, 0); a1, _ = wf.ab(x + w / 2 - 0.1, 0)
    B.feat(wf.mp, 'km_rust', pts=[(a0, y - 0.04), (a1, y - 0.04)], L=0.7)


def jar(B, P, region='ks_jar', r=0.12, h=0.3, lid='ksred'):
    """A glass jar of crackers on the counter (the crackers painted in the glass tile), a plastic lid."""
    x, y, z = P
    body, _ = lathe([(0.0, 0.0), (r * 0.94, 0.0), (r, 0.02), (r, h * 0.8), (r * 0.82, h * 0.92), (r * 0.66, h * 0.95)], 9, 'tex')
    uv_fn(body, list(body.faces), region, lambda co: (0.5 + 0.5 * co.x / r, co.z / h), 0.0)
    xform(body, T(x, y, z)); B.add(body)
    ld, _ = lathe([(r * 0.7, h * 0.93), (r * 0.72, h * 0.95), (r * 0.72, h * 1.05), (0.0, h * 1.07)], 9, lid)
    xform(ld, T(x, y, z)); B.add(ld)


def styro(B, c, region, cell, w=0.56, d=0.38, h=0.15, tilt=0.3, yaw=0.0):
    """A styrofoam fish box tilted toward the street, its catch on ice (a cell of the fish tile) inside the rim."""
    x, y, z = c
    M = T(x, y, z) @ R(yaw, 'Z') @ R(tilt, 'X')
    body = cbox2((-w / 2, -d / 2, 0.0), (w / 2, d / 2, h), 0.012, 'ksstyro')
    xform(body, M); B.add(body)
    cu, cv = cell
    mb = MB()
    i = 0.035
    mb.face([(-w / 2 + i, -d / 2 + i, h + 0.004), (w / 2 - i, -d / 2 + i, h + 0.004), (w / 2 - i, d / 2 - i, h + 0.006),
             (-w / 2 + i, d / 2 - i, h + 0.006)], 'tex', (0, 0, 1), 1.0,
            lambda co: reg_uv(region, (cu + (co.x + w / 2) / w) / 4.0, (cv + (co.y + d / 2) / d) / 2.0, 0.01))
    tb = mb.bm(); xform(tb, M); B.add(tb)


def goods_table(B, x0, x1, y0, y1, z, region, tilt=0.3, skirt='ksfelt', t0=0.0, t1=1.0):
    """A display table out front, its top tilted toward the street (goods painted in an atlas tile), a cloth skirt."""
    zb = z + (y1 - y0) * math.tan(tilt)
    mb = MB()
    mb.face([(x0, y0, z), (x1, y0, z), (x1, y1, zb), (x0, y1, zb)], 'tex', (0, -0.3, 1), 1.0,
            lambda co: reg_uv(region, (co.x - x0) / (x1 - x0), t0 + (t1 - t0) * (co.y - y0) / (y1 - y0), 0.0))
    mb.face([(x0, y0 - 0.012, 0.1), (x1, y0 - 0.012, 0.1), (x1, y0 - 0.012, z + 0.01), (x0, y0 - 0.012, z + 0.01)], skirt, (0, -1, 0), 1.0)
    for x, sg in ((x0 - 0.005, -1), (x1 + 0.005, 1)):
        mb.face([(x, y0 - 0.012, 0.1), (x, y1, 0.1), (x, y1, zb), (x, y0 - 0.012, z + 0.01)], skirt, (sg, 0, 0), 0.85)
    B.add(mb.bm())


def endai(B, x0, x1, y0, y1, h=0.43):
    """A shop's bench (endai) under a red felt cloth (hi-mosen) that hangs over its front and ends."""
    for x in (x0 + 0.08, x1 - 0.14):
        for yy in (y0 + 0.05, y1 - 0.1):
            B.add(box((x, yy, 0.0), (x + 0.06, yy + 0.05, h - 0.04), 'kscedar', skip=('-z',)))
    B.add(box((x0 + 0.08, y0 + 0.07, 0.12), (x1 - 0.08, y0 + 0.1, 0.17), 'kscedar', skip=('-z',)))
    B.add(cbox2((x0, y0, h - 0.045), (x1, y1, h), 0.008, 'kscedar'))
    mb = MB()
    e = 0.015; t = h + 0.012
    mb.face([(x0 - e, y0 - e, t), (x1 + e, y0 - e, t), (x1 + e, y1 + e, t), (x0 - e, y1 + e, t)], 'ksred', (0, 0, 1), 1.0)
    mb.face([(x0 - e, y0 - e, h - 0.14), (x1 + e, y0 - e, h - 0.14), (x1 + e, y0 - e, t), (x0 - e, y0 - e, t)], 'ksred', (0, -1, 0), 0.9)
    for x, sg in ((x0 - e, -1), (x1 + e, 1)):
        mb.face([(x, y0 - e, h - 0.14), (x, y1 + e, h - 0.14), (x, y1 + e, t), (x, y0 - e, t)], 'ksred', (sg, 0, 0), 0.8)
    B.add(mb.bm())


def chatsubo(B, P, s=1.0, mat='ksjar'):
    """A big glazed tea jar with a paper cover tied over its mouth."""
    x, y, z = P
    jb, _ = lathe([(0.0, 0.0), (0.12 * s, 0.0), (0.17 * s, 0.05 * s), (0.22 * s, 0.19 * s), (0.215 * s, 0.31 * s),
                   (0.15 * s, 0.43 * s), (0.105 * s, 0.47 * s), (0.11 * s, 0.5 * s), (0.0, 0.52 * s)], 10,
                  [mat, mat, mat, mat, mat, mat, 'kspaper', 'kspaper'])
    xform(jb, T(x, y, z)); B.add(jb)
    B.add(tube([(x + 0.115 * s * math.cos(a), y + 0.115 * s * math.sin(a), z + 0.47 * s) for a in np.linspace(0, 2 * PI, 9)],
               0.008, 'ksred', 3, caps=False))


def stand_board(B, x, y, w, h, region, z0=0.12, lean=0.12, t0=0.0, t1=1.0):
    """A standing signboard leaning back on its legs (a menu or a sign), face toward the street."""
    mb = MB()
    top = (x, y + h * math.sin(lean), z0 + h * math.cos(lean))
    mb.face([(x - w / 2, y, z0), (x + w / 2, y, z0), (x + w / 2, top[1], top[2]), (x - w / 2, top[1], top[2])], 'tex', (0, -1, 0.1), 1.0,
            lambda co: reg_uv(region, (co.x - x + w / 2) / w, t0 + (t1 - t0) * (co.z - z0) / (top[2] - z0), 0.0))
    B.add(mb.bm())
    fr = cbox2((x - w / 2 - 0.03, y + 0.004, z0 - 0.03), (x + w / 2 + 0.03, y + 0.03, z0), 0.005, 'kscedar')
    B.add(fr)
    for sx in (-1, 1):
        B.add(tube([(x + sx * (w / 2 + 0.01), y + 0.02, 0.0), (x + sx * (w / 2 + 0.01), top[1] + 0.02, top[2])], 0.018, 'kscedar', 4))
        B.add(tube([(x + sx * (w / 2 - 0.02), y + 0.4, 0.0), (x + sx * (w / 2 - 0.02), top[1] + 0.03, top[2] - 0.02)], 0.014, 'kscedar', 4))
    B.add(cbox2((x - w / 2 - 0.03, top[1] + 0.005, top[2]), (x + w / 2 + 0.03, top[1] + 0.035, top[2] + 0.03), 0.005, 'kscedar'))


# ================================================================ painting the tiles
def _rgb(c):
    return tuple(int(round(max(0.0, min(1.0, v)) * 255)) for v in c[:3])


def _arr(dr):
    return np.asarray(dr._image, np.float32) / 255.0


def _set(dr, a):
    dr._image.paste(Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB'))


def _nz(h, w, cx, cy, seed):
    return ATL._noise(int(h), int(w), (max(2, int(cx)), max(2, int(cy))), seed)


INK = (0.08, 0.07, 0.07)
PAPERW = (0.95, 0.93, 0.87)


class _Ink:
    """Lettering drawn into a mask, then laid on with a brush's rough edge and uneven ink (hand-painted signs, noren)."""
    def __init__(self, dr, seed=0):
        self.dr = dr; self.mask = Image.new('L', dr._image.size, 0); self.md = ImageDraw.Draw(self.mask)
        self.seed = seed; self.size = 8

    def chars(self, s, box, vertical=False, frac=0.9, bold=0.05, fill=1.0):
        """Characters spaced evenly along a box (left to right, or top to bottom)."""
        x0, y0, x1, y1 = box
        n = max(1, len(s))
        if vertical:
            step = (y1 - y0) / n; size = min((x1 - x0) * frac, step * frac)
        else:
            step = (x1 - x0) / n; size = min((y1 - y0) * frac, step * frac)
        f = SG._font(SG.KANA, max(6, int(size)))
        if f is None: return
        sw = max(1, int(size * bold * 0.55))
        for i, ch in enumerate(s):
            if ch == ' ': continue
            c = ((x0 + x1) / 2, y0 + step * (i + 0.5)) if vertical else (x0 + step * (i + 0.5), (y0 + y1) / 2)
            self.md.text(c, ch, font=f, fill=int(255 * fill), anchor='mm', stroke_width=sw, stroke_fill=int(255 * fill))
        self.size = max(self.size, size)

    def line(self, s, xy, size, anchor='mm', bold=0.03, maxw=None, latin=False):
        paths = SG.LATIN_SOFT if latin else SG.KANA
        f = SG._font(paths, max(6, int(size)))
        if f is None: return
        while maxw and f.size > 6 and self.md.textlength(s, font=f) > maxw:
            f = SG._font(paths, f.size - 1)
        sw = max(0, int(f.size * bold))
        self.md.text(xy, s, font=f, fill=255, anchor=anchor, stroke_width=sw, stroke_fill=255)
        self.size = max(self.size, f.size)

    def apply(self, ink, rough=0.6, alpha=1.0, dry=0.14):
        m = self.mask
        sz = self.size
        if rough:
            m = m.filter(ImageFilter.GaussianBlur(max(0.8, sz * 0.018)))
        a = np.asarray(m, np.float32) / 255.0
        H_, W_ = a.shape
        if rough:
            n = _nz(H_, W_, W_ / (sz * 0.1 + 1), H_ / (sz * 0.1 + 1), self.seed)
            a = np.clip((a - 0.5 + (n - 0.5) * 0.3 * rough) * 5 + 0.5, 0, 1) * (a > 0.02)
            n2 = _nz(H_, W_, W_ / (sz * 0.45 + 1), H_ / (sz * 0.45 + 1), self.seed + 3)
            a = a * (1 - dry + dry * n2)
        img = _arr(self.dr)
        img = img * (1 - a[..., None] * alpha) + np.array(ink, np.float32) * a[..., None] * alpha
        _set(self.dr, img)


def _ink(dr, s, box, ink, vertical=False, frac=0.9, bold=0.05, seed=0, rough=0.6):
    m = _Ink(dr, seed); m.chars(s, box, vertical, frac, bold); m.apply(ink, rough)


def _text(dr, s, xy, size, ink, anchor='mm', bold=0.03, maxw=None, latin=False, seed=0, rough=0.4):
    m = _Ink(dr, seed); m.line(s, xy, size, anchor, bold, maxw, latin); m.apply(ink, rough)


def _wood(dr, box, base, seed, k, vertical=False, planks=1, silver=0.0, edge=0.35, rings=0.12):
    """Planks of weathered wood: grain, growth rings, darker plank edges and joints, sun-silvered patches."""
    a = _arr(dr)
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    h, w = y1 - y0, x1 - x0
    if h < 2 or w < 2: return
    r = np.random.default_rng(seed)
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    across = X if vertical else Y
    S = w if vertical else h
    pw = S / planks
    pi = np.clip(np.floor(across / pw), 0, planks - 1).astype(int)
    tone = r.uniform(0.88, 1.08, planks)[pi]
    if vertical:
        g1 = _nz(h, w, w / (3 * k), h / (90 * k), seed); g2 = _nz(h, w, w / (40 * k), h / (160 * k), seed + 1)
    else:
        g1 = _nz(h, w, w / (90 * k), h / (3 * k), seed); g2 = _nz(h, w, w / (160 * k), h / (40 * k), seed + 1)
    ringl = np.sin((across + g2 * 60 * k) / (5.5 * k)) * 0.5 + 0.5
    v = tone * (0.9 + 0.14 * g1) * (1 - rings * ATL._ss(0.75, 1.0, ringl))
    d = np.minimum(across - pi * pw, (pi + 1) * pw - across)
    v = v * (1 - edge * ATL._ss(pw * 0.18, 0.0, d)) * (1 - 0.5 * ATL._ss(2.2 * k, 0.4 * k, d))
    col = np.ones((h, w, 3), np.float32) * np.array(base, np.float32) * v[..., None]
    if silver:
        n = _nz(h, w, w / (60 * k) + 2, h / (60 * k) + 2, seed + 2)
        m = (silver * ATL._ss(0.3, 0.75, n))[..., None]
        grey = col.mean(-1, keepdims=True) * 0.35 + np.array((0.60, 0.58, 0.54)) * 0.65 * v[..., None]
        col = col * (1 - m) + grey * m
    a[y0:y1, x0:x1] = col
    _set(dr, a)


def _age(dr, seed, fade=0.0, grime=0.0, stains=0, speck=0.0, fade_col=(0.86, 0.85, 0.82), frayed=0.0):
    """Sun-fade (stronger low down and in blotches), grime, vertical water stains, speckles, a frayed lower edge."""
    a = _arr(dr); H_, W_ = a.shape[:2]
    r = np.random.default_rng(seed)
    n1 = _nz(H_, W_, 5, 4, seed); n2 = _nz(H_, W_, W_ / 14 + 2, H_ / 14 + 2, seed + 1)
    yy = np.linspace(0, 1, H_, dtype=np.float32)[:, None]
    if fade:
        lum = a.mean(-1, keepdims=True)
        pale = lum * 0.5 + a * 0.2 + np.array(fade_col, np.float32) * 0.3
        m = (fade * (0.5 + 0.5 * n1) * (0.55 + 0.45 * yy))[..., None]
        a = a * (1 - m) + pale * m
    if grime:
        g = grime * (0.4 * n1 + 0.6 * n2) * (0.35 + 0.65 * yy)
        a = a * (1 - 0.45 * g[..., None])
        e = np.minimum(np.minimum(np.arange(W_)[None, :], W_ - 1 - np.arange(W_)[None, :]) / (0.06 * W_ + 1),
                       np.minimum(np.arange(H_)[:, None], H_ - 1 - np.arange(H_)[:, None]) / (0.08 * H_ + 1))
        a = a * (1 - grime * 0.25 * np.clip(1 - e, 0, 1)[..., None])
    for _ in range(stains):
        x = r.uniform(0.05, 0.95) * W_; wd = r.uniform(0.01, 0.04) * W_; L = r.uniform(0.2, 0.8)
        X = np.arange(W_)[None, :]
        m = ATL._ss(wd, 0.0, np.abs(X - x) + (n2 - 0.5) * wd) * ATL._ss(L, 0.0, yy) * r.uniform(0.15, 0.35)
        a = a * (1 - m[..., None])
    if speck:
        sp = (r.random((H_, W_)) > 1 - speck * 0.02).astype(np.float32)
        sp = np.asarray(Image.fromarray((sp * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)), np.float32) / 255
        a = a * (1 - 0.3 * sp[..., None])
    if frayed:
        edge = (1 - yy) < frayed * (0.4 + 0.6 * n2)
        a = np.where(edge[..., None], a * 0.82 + 0.18 * np.array(fade_col), a)
    _set(dr, a)


def _glass(dr, w, h, k, seed=0, k_ref=0.55):
    """Reflections over a pane: the sky's light at the top, a few diagonal streaks."""
    a = _arr(dr); H_, W_ = a.shape[:2]
    yy = np.linspace(0, 1, H_, dtype=np.float32)[:, None]; xx = np.linspace(0, 1, W_, dtype=np.float32)[None, :]
    sky = np.array((0.80, 0.86, 0.92), np.float32)
    m = (0.28 * (1 - yy) ** 2 * k_ref)[..., None]
    a = a * (1 - m) + sky * m
    r = np.random.default_rng(seed)
    for _ in range(3):
        c = r.uniform(-0.2, 1.0); wd = r.uniform(0.03, 0.09)
        s = ATL._ss(wd, 0.0, np.abs((xx + yy * 0.45) - c)) * 0.22 * k_ref
        a = a * (1 - s[..., None]) + s[..., None] * sky
    _set(dr, a)


def _shelves(dr, x0, y0, x1, y1, rows, k, seed, cols, shelf=(0.42, 0.30, 0.20), wall=(0.28, 0.22, 0.17), item=(0.06, 0.16)):
    """Shelves of goods: a wall, plank shelves, items of the given colours in rows."""
    r = np.random.default_rng(seed)
    dr.rectangle([x0, y0, x1, y1], fill=_rgb(wall))
    hh = (y1 - y0) / rows
    for i in range(rows):
        yb = y0 + hh * (i + 1)
        x = x0 + 3 * k
        while x < x1 - 6 * k:
            iw = (x1 - x0) * r.uniform(*item)
            ih = hh * r.uniform(0.45, 0.85)
            c = cols[r.integers(len(cols))]
            c2 = tuple(min(1, v * r.uniform(0.8, 1.1)) for v in c)
            dr.rectangle([x, yb - ih, min(x + iw, x1 - 2 * k), yb - 4 * k], fill=_rgb(c2))
            if r.random() < 0.6:
                dr.rectangle([x + iw * 0.2, yb - ih * 0.75, x + iw * 0.8, yb - ih * 0.45], fill=_rgb(PAPERW))
            x += iw + r.uniform(1, 5) * k
        dr.rectangle([x0, yb - 4 * k, x1, yb], fill=_rgb(shelf))
        dr.rectangle([x0, yb, x1, yb + 2 * k], fill=_rgb((0.12, 0.1, 0.09)))


def _lantern_tile(text, body, ink):
    def f(dr, w, h, k):
        a = np.zeros((int(h), int(w), 3), np.float32)
        xx = np.linspace(-1, 1, int(w), dtype=np.float32)[None, :]; yy = np.linspace(0, 1, int(h), dtype=np.float32)[:, None]
        light = 0.72 + 0.32 * np.sqrt(np.clip(1 - xx ** 2, 0, 1)) - 0.12 * np.abs(yy - 0.5)
        a[:] = np.array(body, np.float32) * light[..., None]
        ribs = (np.sin(yy * 2 * math.pi * 16) > 0.86).astype(np.float32) * 0.18
        a = a * (1 - ribs[..., None])
        _set(dr, a)
        _ink(dr, text, (w * 0.22, h * 0.14, w * 0.78, h * 0.86), ink, vertical=True, frac=0.92, bold=0.06, seed=len(text))
        _age(dr, 7 + len(text), fade=0.25, grime=0.35, stains=3)
    return f


# ---------------------------------------------------------------- signboards
def t_sg_sembei(dr, w, h, k):
    _wood(dr, (0, 0, w, h), (0.80, 0.68, 0.50), 11, k, planks=2, silver=0.35)
    _ink(dr, '汐見堂', (w * 0.24, h * 0.08, w * 0.76, h * 0.92), INK, frac=0.86, bold=0.07, seed=1)
    _ink(dr, '手焼き', (w * 0.05, h * 0.1, w * 0.17, h * 0.9), INK, vertical=True, frac=0.9, bold=0.06, seed=2)
    _ink(dr, 'せんべい', (w * 0.83, h * 0.08, w * 0.95, h * 0.92), INK, vertical=True, frac=0.92, bold=0.06, seed=3)
    sx, sy, s = w * 0.205, h * 0.7, h * 0.16
    dr.rectangle([sx - s / 2, sy - s / 2, sx + s / 2, sy + s / 2], fill=_rgb((0.70, 0.16, 0.12)))
    _ink(dr, '汐', (sx - s / 2, sy - s / 2, sx + s / 2, sy + s / 2), (0.93, 0.88, 0.80), frac=0.8, bold=0.02, seed=4, rough=0.3)
    _age(dr, 12, fade=0.25, grime=0.55, stains=6, speck=0.4)


def t_sg_soba(dr, w, h, k):
    _wood(dr, (0, 0, w, h), (0.17, 0.14, 0.12), 21, k, planks=1, silver=0.25, rings=0.2)
    _ink(dr, '小波', (w * 0.3, h * 0.06, w * 0.9, h * 0.94), (0.93, 0.91, 0.85), frac=0.88, bold=0.06, seed=5)
    _ink(dr, 'そば処', (w * 0.09, h * 0.1, w * 0.22, h * 0.9), (0.93, 0.91, 0.85), vertical=True, frac=0.9, bold=0.06, seed=6)
    _age(dr, 22, fade=0.18, grime=0.4, stains=5, speck=0.3)


def t_sg_wagashi(dr, w, h, k):
    _wood(dr, (0, 0, w, h), (0.78, 0.64, 0.46), 31, k, vertical=True, planks=1, silver=0.3)
    dr.rectangle([w * 0.04, h * 0.02, w * 0.96, h * 0.98], outline=_rgb((0.30, 0.20, 0.14)), width=int(3 * k))
    _ink(dr, '若葉庵', (w * 0.32, h * 0.05, w * 0.94, h * 0.78), INK, vertical=True, frac=0.92, bold=0.06, seed=7)
    _ink(dr, '和菓子', (w * 0.06, h * 0.42, w * 0.36, h * 0.95), INK, vertical=True, frac=0.86, bold=0.05, seed=8)
    s = w * 0.26; sx, sy = w * 0.62, h * 0.88
    dr.rectangle([sx - s / 2, sy - s / 2, sx + s / 2, sy + s / 2], fill=_rgb((0.68, 0.15, 0.12)))
    _age(dr, 32, fade=0.25, grime=0.5, stains=4, speck=0.3)


def t_sg_souv(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_rgb((0.94, 0.92, 0.86)))
    dr.rectangle([4 * k, 4 * k, w - 4 * k, h - 4 * k], outline=_rgb((0.72, 0.14, 0.12)), width=int(4 * k))
    _ink(dr, '鎌倉みやげ', (w * 0.05, h * 0.18, w * 0.42, h * 0.82), (0.72, 0.14, 0.12), frac=0.8, bold=0.06, seed=9)
    _ink(dr, 'すずなり', (w * 0.46, h * 0.08, w * 0.93, h * 0.92), INK, frac=0.88, bold=0.07, seed=10)
    for cx in (w * 0.44, w * 0.955):
        cy, s = h * 0.55, h * 0.18
        dr.ellipse([cx - s, cy - s, cx + s, cy + s], fill=_rgb((0.86, 0.68, 0.24)))
        dr.line([(cx - s * 0.7, cy + s * 0.15), (cx + s * 0.7, cy + s * 0.15)], fill=_rgb((0.4, 0.3, 0.1)), width=int(2 * k))
        dr.line([(cx, cy - s), (cx, cy - s * 1.6)], fill=_rgb((0.72, 0.14, 0.12)), width=int(2 * k))
    _age(dr, 42, fade=0.2, grime=0.5, stains=7, speck=0.2)


def t_sg_fish(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_rgb((0.18, 0.34, 0.56)))
    dr.rectangle([0, h * 0.06, w, h * 0.12], fill=_rgb((0.92, 0.92, 0.9)))
    _ink(dr, '鮮魚', (w * 0.12, h * 0.18, w * 0.34, h * 0.94), (0.95, 0.95, 0.93), frac=0.86, bold=0.06, seed=11, rough=0.3)
    _ink(dr, 'かもめ屋', (w * 0.40, h * 0.16, w * 0.80, h * 0.96), (0.95, 0.95, 0.93), frac=0.9, bold=0.07, seed=12, rough=0.3)
    for cx in (w * 0.06, w * 0.88):
        cy = h * 0.55; s = h * 0.32
        dr.arc([cx - s, cy - s * 0.4, cx, cy + s * 0.6], 200, 340, fill=_rgb((0.95, 0.95, 0.93)), width=int(3 * k))
        dr.arc([cx, cy - s * 0.4, cx + s, cy + s * 0.6], 200, 340, fill=_rgb((0.95, 0.95, 0.93)), width=int(3 * k))
    _age(dr, 52, fade=0.35, grime=0.4, stains=5)


def t_sg_kissa(dr, w, h, k):
    _wood(dr, (0, 0, w, h), (0.36, 0.22, 0.14), 61, k, planks=1, silver=0.1, rings=0.18)
    dr.rectangle([5 * k, 5 * k, w - 5 * k, h - 5 * k], outline=_rgb((0.86, 0.74, 0.50)), width=int(2 * k))
    cream = (0.94, 0.86, 0.66)
    _ink(dr, '純喫茶', (w * 0.05, h * 0.25, w * 0.30, h * 0.75), cream, frac=0.8, bold=0.05, seed=13, rough=0.3)
    _ink(dr, '灯台', (w * 0.33, h * 0.08, w * 0.70, h * 0.92), cream, frac=0.9, bold=0.06, seed=14, rough=0.3)
    _text(dr, 'COFFEE', (w * 0.85, h * 0.5), h * 0.3, cream, maxw=w * 0.24, latin=True, seed=15, rough=0.3)
    _age(dr, 62, fade=0.3, grime=0.35, stains=4, speck=0.3)


def t_sg_kissa2(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_rgb((0.95, 0.92, 0.80)))
    dr.rectangle([3 * k, 3 * k, w - 3 * k, h - 3 * k], outline=_rgb((0.50, 0.16, 0.12)), width=int(4 * k))
    _ink(dr, '珈琲', (w * 0.12, h * 0.05, w * 0.88, h * 0.62), (0.48, 0.14, 0.10), vertical=True, frac=0.92, bold=0.05, seed=16, rough=0.2)
    _ink(dr, '灯台', (w * 0.25, h * 0.66, w * 0.75, h * 0.95), (0.20, 0.14, 0.10), vertical=True, frac=0.9, bold=0.04, seed=17, rough=0.2)
    _age(dr, 63, fade=0.25, grime=0.55, stains=5, fade_col=(0.9, 0.85, 0.66))


def t_sg_tea(dr, w, h, k):
    _wood(dr, (0, 0, w, h), (0.70, 0.56, 0.38), 71, k, planks=2, silver=0.45)
    ink = (0.10, 0.16, 0.10)
    _ink(dr, '緑風園', (w * 0.22, h * 0.08, w * 0.86, h * 0.92), ink, frac=0.86, bold=0.07, seed=18)
    _ink(dr, '日本茶', (w * 0.05, h * 0.1, w * 0.17, h * 0.9), ink, vertical=True, frac=0.9, bold=0.06, seed=19)
    sx, sy, s = w * 0.93, h * 0.3, h * 0.2
    dr.rectangle([sx - s / 2, sy - s / 2, sx + s / 2, sy + s / 2], fill=_rgb((0.68, 0.16, 0.12)))
    _age(dr, 72, fade=0.3, grime=0.55, stains=6, speck=0.4)


# ---------------------------------------------------------------- noren
def t_nr_sembei(dr, w, h, k):
    a = _arr(dr); H_, W_ = a.shape[:2]
    n = _nz(H_, W_, W_ / (4 * k), 3, 81)
    a[:] = np.array((0.15, 0.21, 0.38), np.float32) * (0.92 + 0.12 * n)[..., None]
    _set(dr, a)
    white = (0.93, 0.92, 0.88)
    dr.rectangle([0, h * 0.13, w, h * 0.145], fill=_rgb(white))
    for i, ch in enumerate('汐見堂'):
        _ink(dr, ch, (w * i / 3 + w * 0.05, h * 0.24, w * (i + 1) / 3 - w * 0.05, h * 0.86), white, frac=0.85, bold=0.06, seed=20 + i, rough=0.35)
    cx, cy, s = w * 0.5, h * 0.065, h * 0.05
    dr.ellipse([cx - s, cy - s, cx + s, cy + s], outline=_rgb(white), width=int(2 * k))
    _age(dr, 82, fade=0.45, grime=0.25, stains=4, fade_col=(0.62, 0.66, 0.74), frayed=0.03)


def t_nr_soba(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_rgb((0.93, 0.92, 0.87)))
    _ink(dr, '手打ちそば', (w * 0.25, h * 0.02, w * 0.75, h * 0.15), INK, frac=0.85, bold=0.05, seed=24, rough=0.3)
    _ink(dr, '小', (w * 0.06, h * 0.22, w * 0.46, h * 0.9), INK, frac=0.86, bold=0.07, seed=25)
    _ink(dr, '波', (w * 0.54, h * 0.22, w * 0.94, h * 0.9), INK, frac=0.86, bold=0.07, seed=26)
    _age(dr, 83, fade=0.15, grime=0.5, stains=6, fade_col=(0.86, 0.82, 0.70), frayed=0.03)


def t_nr_wagashi(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_rgb((0.90, 0.86, 0.76)))
    brown = (0.36, 0.22, 0.14)
    for i, ch in enumerate('若葉庵'):
        _ink(dr, ch, (w * i / 3 + w * 0.06, h * 0.26, w * (i + 1) / 3 - w * 0.06, h * 0.88), brown, frac=0.8, bold=0.05, seed=27 + i, rough=0.35)
    for x in (w * 0.08, w * 0.92):
        dr.ellipse([x - h * 0.06, h * 0.04, x + h * 0.06, h * 0.16], fill=_rgb((0.48, 0.62, 0.36)))
    _age(dr, 84, fade=0.2, grime=0.35, stains=3, fade_col=(0.88, 0.85, 0.78), frayed=0.03)


def t_nr_tea(dr, w, h, k):
    a = _arr(dr); H_, W_ = a.shape[:2]
    n = _nz(H_, W_, W_ / (4 * k), 3, 85)
    a[:] = np.array((0.13, 0.17, 0.13), np.float32) * (0.9 + 0.14 * n)[..., None]
    _set(dr, a)
    white = (0.92, 0.91, 0.86)
    _ink(dr, '茶', (w * 0.2, h * 0.14, w * 0.8, h * 0.92), white, frac=0.95, bold=0.07, seed=30, rough=0.4)
    _ink(dr, '緑風園', (w * 0.8, h * 0.4, w * 0.95, h * 0.94), white, vertical=True, frac=0.8, bold=0.04, seed=31, rough=0.3)
    _age(dr, 86, fade=0.4, grime=0.25, stains=4, fade_col=(0.45, 0.48, 0.42), frayed=0.03)


# ---------------------------------------------------------------- banners
def t_nobori(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_rgb((0.14, 0.32, 0.62)))
    dr.rectangle([0, 0, w * 0.12, h], fill=_rgb((0.95, 0.95, 0.93)))
    for i in range(7):
        y = h * (0.05 + i * 0.15)
        dr.rectangle([w * 0.12, y, w * 0.22, y + h * 0.03], fill=_rgb((0.95, 0.95, 0.93)))
    _ink(dr, '湘南名物', (w * 0.3, h * 0.03, w * 0.96, h * 0.22), (0.98, 0.84, 0.30), vertical=True, frac=0.9, bold=0.05, seed=33, rough=0.25)
    _ink(dr, '生しらす丼', (w * 0.22, h * 0.25, w * 1.0, h * 0.98), (0.97, 0.97, 0.95), vertical=True, frac=0.92, bold=0.07, seed=34, rough=0.3)
    _age(dr, 87, fade=0.3, grime=0.2, stains=2)


def t_nobori2(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_rgb((0.78, 0.14, 0.12)))
    dr.rectangle([0, 0, w * 0.12, h], fill=_rgb((0.95, 0.95, 0.93)))
    for i in range(7):
        y = h * (0.05 + i * 0.15)
        dr.rectangle([w * 0.12, y, w * 0.22, y + h * 0.03], fill=_rgb((0.95, 0.95, 0.93)))
    _ink(dr, '鎌倉みやげ', (w * 0.22, h * 0.06, w * 1.0, h * 0.96), (0.97, 0.97, 0.95), vertical=True, frac=0.92, bold=0.07, seed=35, rough=0.3)
    _age(dr, 88, fade=0.35, grime=0.2, stains=2)


# ---------------------------------------------------------------- menus, prices, cases, goods
def t_menu_soba(dr, w, h, k):
    _wood(dr, (0, 0, w, h), (0.74, 0.60, 0.42), 91, k, vertical=True, planks=1, silver=0.4)
    dr.rectangle([3 * k, 3 * k, w - 3 * k, h - 3 * k], outline=_rgb((0.25, 0.18, 0.12)), width=int(3 * k))
    _ink(dr, '品書', (w * 0.2, h * 0.02, w * 0.8, h * 0.12), INK, frac=0.85, bold=0.05, seed=36, rough=0.3)
    items = [('もりそば', '七〇〇'), ('かけそば', '七〇〇'), ('天ざる', '一六〇〇'), ('しらす丼', '一二〇〇')]
    cw = (w * 0.9) / len(items)
    for i, (it, pr) in enumerate(items):
        x1 = w * 0.95 - i * cw; x0 = x1 - cw
        _ink(dr, it, (x0, h * 0.15, x1, h * 0.62), INK, vertical=True, frac=0.92, bold=0.04, seed=37 + i, rough=0.25)
        _ink(dr, pr, (x0, h * 0.64, x1, h * 0.97), (0.55, 0.12, 0.10), vertical=True, frac=0.86, bold=0.04, seed=41 + i, rough=0.25)
    _age(dr, 92, fade=0.25, grime=0.45, stains=4, speck=0.3)


def t_price_fish(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_rgb((0.96, 0.96, 0.94)))
    dr.rectangle([0, 0, w, h], outline=_rgb((0.55, 0.56, 0.58)), width=int(4 * k))
    red = (0.80, 0.12, 0.10)
    _text(dr, '本日のおすすめ', (w * 0.5, h * 0.09), h * 0.08, red, maxw=w * 0.9, seed=43, bold=0.08, rough=0.5)
    rows = [('生しらす', '100g 480円'), ('釜揚げしらす', '100g 380円'), ('地あじ', '1尾 180円'), ('さざえ', '1個 300円'), ('真いか', '1杯 450円')]
    for i, (a, b) in enumerate(rows):
        y = h * (0.24 + i * 0.16)
        _text(dr, a, (w * 0.06, y), h * 0.075, INK, anchor='lm', maxw=w * 0.9, seed=44 + i, bold=0.07, rough=0.5)
        _text(dr, b, (w * 0.94, y + h * 0.065), h * 0.065, red, anchor='rm', maxw=w * 0.7, seed=50 + i, bold=0.07, rough=0.5)
    _age(dr, 93, grime=0.35, stains=3, speck=0.3)


def _dish(dr, cx, cy, s, kind, k):
    if kind == 'napo':
        dr.ellipse([cx - s, cy - s * 0.25, cx + s, cy + s * 0.35], fill=_rgb((0.96, 0.96, 0.94)))
        dr.ellipse([cx - s * 0.7, cy - s * 0.45, cx + s * 0.7, cy + s * 0.2], fill=_rgb((0.90, 0.42, 0.18)))
        for i in range(6):
            dr.arc([cx - s * 0.6 + i * s * 0.12, cy - s * 0.4, cx + s * 0.1 + i * s * 0.08, cy + s * 0.1], 180, 330,
                   fill=_rgb((0.98, 0.62, 0.30)), width=int(2 * k))
        dr.ellipse([cx - s * 0.2, cy - s * 0.4, cx, cy - s * 0.25], fill=_rgb((0.30, 0.55, 0.22)))
    elif kind == 'cake':
        dr.ellipse([cx - s, cy - s * 0.1, cx + s, cy + s * 0.35], fill=_rgb((0.96, 0.96, 0.94)))
        for j in range(3):
            y = cy - j * s * 0.22
            dr.ellipse([cx - s * 0.65, y - s * 0.2, cx + s * 0.65, y + s * 0.12], fill=_rgb((0.78, 0.52, 0.24)))
            dr.ellipse([cx - s * 0.6, y - s * 0.26, cx + s * 0.6, y + s * 0.05], fill=_rgb((0.94, 0.76, 0.42)))
        dr.rectangle([cx - s * 0.12, cy - s * 0.72, cx + s * 0.12, cy - s * 0.58], fill=_rgb((0.99, 0.94, 0.62)))
    elif kind == 'soda':
        dr.polygon([(cx - s * 0.35, cy - s * 0.8), (cx + s * 0.35, cy - s * 0.8), (cx + s * 0.22, cy + s * 0.2), (cx - s * 0.22, cy + s * 0.2)],
                   fill=_rgb((0.36, 0.78, 0.42)))
        dr.ellipse([cx - s * 0.35, cy - s * 1.1, cx + s * 0.35, cy - s * 0.65], fill=_rgb((0.97, 0.96, 0.9)))
        dr.ellipse([cx + s * 0.05, cy - s * 1.3, cx + s * 0.25, cy - s * 1.08], fill=_rgb((0.86, 0.1, 0.12)))
        dr.rectangle([cx - s * 0.05, cy + s * 0.2, cx + s * 0.05, cy + s * 0.4], fill=_rgb((0.85, 0.88, 0.88)))
        dr.ellipse([cx - s * 0.3, cy + s * 0.32, cx + s * 0.3, cy + s * 0.45], fill=_rgb((0.85, 0.88, 0.88)))
    elif kind == 'coffee':
        dr.ellipse([cx - s * 0.75, cy, cx + s * 0.75, cy + s * 0.3], fill=_rgb((0.96, 0.96, 0.94)))
        dr.rectangle([cx - s * 0.4, cy - s * 0.4, cx + s * 0.4, cy + s * 0.12], fill=_rgb((0.97, 0.97, 0.95)))
        dr.ellipse([cx - s * 0.4, cy - s * 0.5, cx + s * 0.4, cy - s * 0.3], fill=_rgb((0.30, 0.17, 0.10)))
        dr.arc([cx + s * 0.3, cy - s * 0.3, cx + s * 0.62, cy], 270, 90, fill=_rgb((0.97, 0.97, 0.95)), width=int(3 * k))


def t_sample(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_rgb((0.48, 0.12, 0.12)))
    dr.rectangle([0, h * 0.72, w, h], fill=_rgb((0.86, 0.84, 0.80)))
    items = [('napo', 'ナポリタン', '750円'), ('cake', 'ホットケーキ', '650円'), ('soda', 'クリームソーダ', '600円'),
             ('coffee', 'ブレンド', '500円')]
    cw = w / len(items)
    for i, (kind, name, pr) in enumerate(items):
        cx = cw * (i + 0.5)
        _dish(dr, cx, h * 0.52, cw * 0.32, kind, k)
        dr.rectangle([cx - cw * 0.42, h * 0.76, cx + cw * 0.42, h * 0.97], fill=_rgb((0.97, 0.96, 0.92)))
        _text(dr, name, (cx, h * 0.82), h * 0.085, INK, maxw=cw * 0.8, seed=60 + i, rough=0.2)
        _text(dr, pr, (cx, h * 0.92), h * 0.08, (0.7, 0.1, 0.1), maxw=cw * 0.6, seed=64 + i, rough=0.2)
    _glass(dr, w, h, k, 3, 0.6)
    _age(dr, 94, fade=0.25, grime=0.3, speck=0.4, fade_col=(0.86, 0.80, 0.66))


def _sweet(dr, cx, cy, s, kind, k):
    if kind == 'kashiwa':
        dr.ellipse([cx - s, cy - s * 0.55, cx + s, cy + s * 0.55], fill=_rgb((0.30, 0.42, 0.20)))
        dr.ellipse([cx - s * 0.75, cy - s * 0.42, cx + s * 0.5, cy + s * 0.4], fill=_rgb((0.95, 0.94, 0.90)))
    elif kind == 'sakura':
        dr.ellipse([cx - s, cy - s * 0.6, cx + s, cy + s * 0.6], fill=_rgb((0.95, 0.70, 0.74)))
        dr.ellipse([cx - s * 0.5, cy - s * 0.65, cx + s * 1.1, cy + s * 0.2], fill=_rgb((0.44, 0.52, 0.28)))
    elif kind == 'dora':
        dr.ellipse([cx - s, cy - s * 0.7, cx + s, cy + s * 0.7], fill=_rgb((0.56, 0.32, 0.14)))
        dr.ellipse([cx - s * 0.75, cy - s * 0.5, cx + s * 0.75, cy + s * 0.4], fill=_rgb((0.70, 0.44, 0.20)))
    elif kind == 'daifuku':
        dr.ellipse([cx - s, cy - s * 0.75, cx + s, cy + s * 0.75], fill=_rgb((0.96, 0.95, 0.93)))
        for j in range(4):
            dr.ellipse([cx - s * 0.5 + j * s * 0.3, cy - s * 0.1, cx - s * 0.38 + j * s * 0.3, cy + s * 0.02], fill=_rgb((0.36, 0.2, 0.2)))
    elif kind == 'ajisai':
        dr.ellipse([cx - s, cy - s * 0.75, cx + s, cy + s * 0.75], fill=_rgb((0.54, 0.50, 0.80)))
        for j in range(6):
            a = j * 1.05
            x, y = cx + math.cos(a) * s * 0.45, cy + math.sin(a) * s * 0.35
            dr.ellipse([x - s * 0.22, y - s * 0.18, x + s * 0.22, y + s * 0.18], fill=_rgb((0.70, 0.66, 0.92)))
    elif kind == 'warabi':
        for j in range(5):
            x = cx - s * 0.6 + (j % 3) * s * 0.5; y = cy - s * 0.25 + (j // 3) * s * 0.4
            dr.rectangle([x - s * 0.22, y - s * 0.2, x + s * 0.22, y + s * 0.2], fill=_rgb((0.86, 0.76, 0.52)))


def t_case(dr, w, h, k):
    """The wagashi case: its front (the lower half: rows seen through the glass) and its top (the upper half)."""
    kinds = ['kashiwa', 'sakura', 'dora', 'daifuku', 'ajisai', 'warabi']
    names = [('柏餅', '220円'), ('桜餅', '200円'), ('どら焼き', '250円'), ('豆大福', '230円'), ('紫陽花', '380円'), ('わらび餅', '450円')]
    cw = w / 6
    # front: a shelf of trays, a price card under each
    dr.rectangle([0, h * 0.5, w, h], fill=_rgb((0.88, 0.86, 0.80)))
    for i, kd in enumerate(kinds):
        cx = cw * (i + 0.5)
        dr.rectangle([cx - cw * 0.44, h * 0.82, cx + cw * 0.44, h * 0.86], fill=_rgb((0.20, 0.14, 0.10)))
        for j in range(3):
            _sweet(dr, cx - cw * 0.26 + j * cw * 0.26, h * 0.77, cw * 0.12, kd, k)
        dr.rectangle([cx - cw * 0.4, h * 0.88, cx + cw * 0.4, h * 0.985], fill=_rgb((0.97, 0.96, 0.92)))
        _text(dr, names[i][0], (cx, h * 0.915), h * 0.04, INK, maxw=cw * 0.75, seed=70 + i, rough=0.15)
        _text(dr, names[i][1], (cx, h * 0.96), h * 0.035, (0.7, 0.1, 0.1), maxw=cw * 0.6, seed=76 + i, rough=0.15)
        _sweet(dr, cx - cw * 0.15, h * 0.62, cw * 0.11, kd, k); _sweet(dr, cx + cw * 0.15, h * 0.62, cw * 0.11, kd, k)
    # top: lacquer trays of sweets seen from above
    dr.rectangle([0, 0, w, h * 0.5], fill=_rgb((0.84, 0.82, 0.76)))
    for i, kd in enumerate(kinds):
        cx = cw * (i + 0.5)
        dr.rectangle([cx - cw * 0.45, h * 0.04, cx + cw * 0.45, h * 0.46], fill=_rgb((0.22, 0.12, 0.10)))
        for j in range(6):
            _sweet(dr, cx - cw * 0.22 + (j % 2) * cw * 0.44, h * (0.11 + (j // 2) * 0.13), cw * 0.15, kd, k)
    _glass(dr, w, h, k, 5, 0.7)
    _age(dr, 95, grime=0.2, speck=0.3)


def t_jar(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_rgb((0.72, 0.74, 0.70)))
    r = np.random.default_rng(97)
    y = h * 0.95
    while y > h * 0.18:
        tone = r.uniform(0.85, 1.05)
        dr.ellipse([w * 0.08, y - h * 0.05, w * 0.92, y + h * 0.02], fill=_rgb((0.62 * tone, 0.40 * tone, 0.20 * tone)))
        if r.random() < 0.4:
            dr.ellipse([w * 0.3, y - h * 0.04, w * 0.7, y + h * 0.0], fill=_rgb((0.10, 0.14, 0.10)))
        y -= h * 0.055
    dr.rectangle([w * 0.3, h * 0.5, w * 0.7, h * 0.7], fill=_rgb((0.96, 0.94, 0.88)))
    _ink(dr, '醤油', (w * 0.32, h * 0.52, w * 0.68, h * 0.68), (0.6, 0.1, 0.1), vertical=True, frac=0.9, bold=0.03, seed=79, rough=0.1)
    _glass(dr, w, h, k, 6, 0.9)


def t_grill(dr, w, h, k):
    a = _arr(dr); H_, W_ = a.shape[:2]
    n = _nz(H_, W_, W_ / (6 * k), H_ / (6 * k), 99)
    a[:] = np.array((0.12, 0.08, 0.06)) + np.array((0.86, 0.32, 0.08)) * ATL._ss(0.55, 0.85, n)[..., None]
    _set(dr, a)
    r = np.random.default_rng(98)
    for i in range(7):
        cx = w * (0.08 + i * 0.14); cy = h * (0.3 if i % 2 else 0.68); s = h * 0.24
        t = r.uniform(0.8, 1.05)
        dr.ellipse([cx - s, cy - s, cx + s, cy + s], fill=_rgb((0.74 * t, 0.52 * t, 0.28 * t)))
        dr.ellipse([cx - s * 0.8, cy - s * 0.8, cx + s * 0.75, cy + s * 0.7], fill=_rgb((0.62 * t, 0.38 * t, 0.18 * t)))
    for x in np.arange(0, w, 7 * k):
        dr.line([(x, 0), (x, h)], fill=_rgb((0.25, 0.25, 0.26)), width=int(1.4 * k))
    for y in (h * 0.05, h * 0.95):
        dr.line([(0, y), (w, y)], fill=_rgb((0.3, 0.3, 0.3)), width=int(3 * k))


def t_tenugui(dr, w, h, k):
    """Four tenugui hanging from a rod: waves, hydrangeas, plovers, a sea of fish."""
    cw = w / 4
    defs = [((0.16, 0.24, 0.44), (0.93, 0.93, 0.9)), ((0.95, 0.94, 0.90), (0.36, 0.42, 0.76)), ((0.78, 0.20, 0.16), (0.96, 0.94, 0.9)),
            ((0.30, 0.52, 0.48), (0.95, 0.94, 0.88))]
    for i, (bg, fg) in enumerate(defs):
        x0 = cw * i + 2 * k; x1 = cw * (i + 1) - 2 * k
        dr.rectangle([x0, 0, x1, h], fill=_rgb(bg))
        if i == 0:
            for yy in np.arange(h * 0.12, h, h * 0.12):
                for xx in np.arange(x0, x1, cw * 0.25):
                    dr.arc([xx, yy, xx + cw * 0.25, yy + h * 0.14], 180, 360, fill=_rgb(fg), width=int(2 * k))
        elif i == 1:
            r = np.random.default_rng(5)
            for _ in range(10):
                cx, cy = r.uniform(x0 + 8 * k, x1 - 8 * k), r.uniform(h * 0.12, h * 0.95)
                for j in range(5):
                    a = j * 1.26
                    dr.ellipse([cx + math.cos(a) * 5 * k - 3 * k, cy + math.sin(a) * 5 * k - 3 * k,
                                cx + math.cos(a) * 5 * k + 3 * k, cy + math.sin(a) * 5 * k + 3 * k], fill=_rgb(fg))
        elif i == 2:
            for yy in np.arange(h * 0.15, h, h * 0.16):
                for xx in np.arange(x0 + cw * 0.1, x1 - 4 * k, cw * 0.3):
                    dr.arc([xx, yy, xx + cw * 0.12, yy + h * 0.06], 200, 340, fill=_rgb(fg), width=int(2 * k))
                    dr.arc([xx + cw * 0.12, yy, xx + cw * 0.24, yy + h * 0.06], 200, 340, fill=_rgb(fg), width=int(2 * k))
        else:
            for yy in np.arange(h * 0.18, h, h * 0.14):
                for xx in np.arange(x0 + cw * 0.08, x1 - 10 * k, cw * 0.32):
                    dr.ellipse([xx, yy, xx + cw * 0.2, yy + h * 0.05], fill=_rgb(fg))
                    dr.polygon([(xx + cw * 0.2, yy + h * 0.025), (xx + cw * 0.28, yy), (xx + cw * 0.28, yy + h * 0.05)], fill=_rgb(fg))
        dr.rectangle([x0, 0, x1, h * 0.09], fill=_rgb(tuple(v * 0.8 for v in bg)))
        dr.rectangle([x0 + cw * 0.2, h * 0.86, x1 - cw * 0.2, h * 0.94], fill=_rgb(PAPERW))
        _text(dr, '六六〇円', ((x0 + x1) / 2, h * 0.9), h * 0.05, INK, maxw=cw * 0.55, seed=80 + i, rough=0.1)
    _age(dr, 96, fade=0.15, grime=0.2)


def t_goods1(dr, w, h, k):
    """A table seen from above: stacks of folded tenugui (left), chopsticks in boxes and a tray of them (right)."""
    dr.rectangle([0, 0, w, h], fill=_rgb((0.70, 0.18, 0.15)))
    cols = [(0.16, 0.24, 0.44), (0.95, 0.94, 0.9), (0.78, 0.20, 0.16), (0.30, 0.52, 0.48), (0.86, 0.70, 0.30), (0.52, 0.42, 0.66)]
    r = np.random.default_rng(101)
    for i in range(10):
        x = w * (0.02 + (i % 5) * 0.105); y = h * (0.08 if i < 5 else 0.52)
        c = cols[i % len(cols)]
        dr.rectangle([x, y, x + w * 0.095, y + h * 0.4], fill=_rgb(c))
        dr.line([(x, y + h * 0.13), (x + w * 0.095, y + h * 0.13)], fill=_rgb(tuple(v * 0.75 for v in c)), width=int(2 * k))
        if r.random() < 0.7:
            for j in range(4):
                dr.ellipse([x + w * (0.01 + 0.02 * j), y + h * 0.2, x + w * (0.02 + 0.02 * j), y + h * 0.28], fill=_rgb(cols[(i + 1) % 6]))
    for i in range(4):
        x = w * (0.56 + i * 0.11)
        dr.rectangle([x, h * 0.06, x + w * 0.1, h * 0.94], fill=_rgb((0.20, 0.14, 0.12)))
        for j in range(5):
            c = [(0.66, 0.12, 0.10), (0.10, 0.09, 0.09), (0.78, 0.60, 0.36), (0.40, 0.22, 0.14)][(i + j) % 4]
            xx = x + w * (0.012 + j * 0.018)
            dr.rectangle([xx, h * 0.1, xx + w * 0.008, h * 0.9], fill=_rgb(c))
    for i, s in enumerate(('三百円', '五百円')):
        x = w * (0.2 + i * 0.6)
        dr.rectangle([x, h * 0.84, x + w * 0.12, h * 0.98], fill=_rgb(PAPERW))
        _text(dr, s, (x + w * 0.06, h * 0.91), h * 0.1, INK, maxw=w * 0.11, seed=85 + i, rough=0.1)
    _age(dr, 102, fade=0.15, grime=0.2)


def t_goods2(dr, w, h, k):
    """Small bells on red cords, folding fans, a box of postcards, picture tins."""
    dr.rectangle([0, 0, w, h], fill=_rgb((0.20, 0.30, 0.46)))
    for i in range(18):
        cx = w * (0.03 + (i % 9) * 0.052); cy = h * (0.25 if i < 9 else 0.68); s = h * 0.1
        dr.line([(cx, cy - s * 1.9), (cx, cy - s)], fill=_rgb((0.80, 0.14, 0.12)), width=int(2 * k))
        dr.ellipse([cx - s, cy - s, cx + s, cy + s], fill=_rgb((0.86, 0.70, 0.26) if i % 3 else (0.80, 0.80, 0.78)))
        dr.line([(cx - s * 0.6, cy + s * 0.2), (cx + s * 0.6, cy + s * 0.2)], fill=_rgb((0.35, 0.26, 0.08)), width=int(1.5 * k))
    for i in range(3):
        cx = w * (0.56 + i * 0.075); cy = h * 0.55
        dr.pieslice([cx - h * 0.3, cy - h * 0.4, cx + h * 0.3, cy + h * 0.2], 200, 340, fill=_rgb([(0.92, 0.6, 0.66), (0.5, 0.6, 0.86), (0.96, 0.9, 0.7)][i]))
    for i in range(3):
        x = w * (0.78 + i * 0.07)
        dr.rectangle([x, h * 0.12, x + w * 0.062, h * 0.88], fill=_rgb([(0.62, 0.78, 0.86), (0.86, 0.80, 0.62), (0.72, 0.84, 0.66)][i]))
        dr.rectangle([x + w * 0.006, h * 0.16, x + w * 0.056, h * 0.5], fill=_rgb([(0.30, 0.50, 0.70), (0.66, 0.36, 0.30), (0.36, 0.56, 0.36)][i]))
    for i, s in enumerate(('すず 四百円', 'はがき 百円')):
        x = w * (0.18 + i * 0.6)
        dr.rectangle([x, h * 0.86, x + w * 0.2, h * 0.99], fill=_rgb(PAPERW))
        _text(dr, s, (x + w * 0.1, h * 0.925), h * 0.1, INK, maxw=w * 0.19, seed=87 + i, rough=0.1)
    _age(dr, 103, fade=0.15, grime=0.2)


def t_cards(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_rgb((0.30, 0.31, 0.33)))
    pics = [((0.50, 0.70, 0.90), (0.22, 0.46, 0.66)), ((0.86, 0.84, 0.78), (0.42, 0.32, 0.26)), ((0.62, 0.80, 0.94), (0.86, 0.88, 0.90)),
            ((0.56, 0.74, 0.50), (0.56, 0.52, 0.82)), ((0.96, 0.80, 0.60), (0.30, 0.42, 0.62)), ((0.52, 0.72, 0.88), (0.28, 0.56, 0.36))]
    for j in range(5):
        for i in range(2):
            x0 = w * (0.05 + i * 0.47); y0 = h * (0.03 + j * 0.19)
            a, b = pics[(i + j * 2) % len(pics)]
            dr.rectangle([x0, y0, x0 + w * 0.42, y0 + h * 0.17], fill=_rgb(PAPERW))
            dr.rectangle([x0 + w * 0.03, y0 + h * 0.012, x0 + w * 0.39, y0 + h * 0.15], fill=_rgb(a))
            dr.rectangle([x0 + w * 0.03, y0 + h * 0.09, x0 + w * 0.39, y0 + h * 0.15], fill=_rgb(b))
            if (i + j) % 3 == 0:
                dr.polygon([(x0 + w * 0.1, y0 + h * 0.09), (x0 + w * 0.21, y0 + h * 0.03), (x0 + w * 0.32, y0 + h * 0.09)], fill=_rgb((0.42, 0.50, 0.66)))
    _age(dr, 104, fade=0.2, grime=0.2)


def t_fish(dr, w, h, k):
    """Four boxes' catch on crushed ice: whitebait (shirasu), horse mackerel (aji), turban shells (sazae), squid (ika);
    the bottom row the same in shallow trays."""
    cw, chh = w / 4, h / 2
    r = np.random.default_rng(105)
    a = _arr(dr); H_, W_ = a.shape[:2]
    n = _nz(H_, W_, W_ / (3 * k), H_ / (3 * k), 106)
    a[:] = np.array((0.82, 0.88, 0.92), np.float32) * (0.9 + 0.16 * n)[..., None]
    _set(dr, a)
    for row in range(2):
        y0, y1 = chh * row, chh * (row + 1)
        for col in range(4):
            x0, x1 = cw * col, cw * (col + 1)
            kind = col
            if kind == 0:                      # whitebait heaped on a tray
                dr.rounded_rectangle([x0 + cw * 0.08, y0 + chh * 0.12, x1 - cw * 0.08, y1 - chh * 0.12], radius=6 * k,
                                     fill=_rgb((0.86, 0.86, 0.82)))
                for _ in range(260):
                    x, y = r.uniform(x0 + cw * 0.1, x1 - cw * 0.1), r.uniform(y0 + chh * 0.14, y1 - chh * 0.14)
                    ang = r.uniform(0, math.pi)
                    dr.line([(x, y), (x + math.cos(ang) * 4 * k, y + math.sin(ang) * 4 * k)],
                            fill=_rgb((0.97, 0.97, 0.95) if r.random() < 0.7 else (0.62, 0.62, 0.6)), width=int(1.2 * k))
            elif kind == 1:                    # horse mackerel in a row, heads one way
                for j in range(5):
                    cy = y0 + chh * (0.16 + j * 0.17)
                    dr.ellipse([x0 + cw * 0.12, cy - chh * 0.07, x1 - cw * 0.2, cy + chh * 0.07], fill=_rgb((0.52, 0.60, 0.66)))
                    dr.ellipse([x0 + cw * 0.12, cy, x1 - cw * 0.2, cy + chh * 0.07], fill=_rgb((0.86, 0.88, 0.86)))
                    dr.line([(x0 + cw * 0.18, cy + chh * 0.005), (x1 - cw * 0.24, cy + chh * 0.005)], fill=_rgb((0.80, 0.72, 0.34)), width=int(2 * k))
                    dr.polygon([(x1 - cw * 0.21, cy), (x1 - cw * 0.08, cy - chh * 0.06), (x1 - cw * 0.08, cy + chh * 0.06)], fill=_rgb((0.50, 0.56, 0.6)))
                    dr.ellipse([x0 + cw * 0.15, cy - chh * 0.03, x0 + cw * 0.2, cy + chh * 0.02], fill=_rgb((0.1, 0.1, 0.1)))
            elif kind == 2:                    # turban shells
                for j in range(9):
                    cx = x0 + cw * (0.22 + (j % 3) * 0.28); cy = y0 + chh * (0.22 + (j // 3) * 0.28); s = cw * 0.11
                    dr.ellipse([cx - s, cy - s, cx + s, cy + s], fill=_rgb((0.36, 0.38, 0.30)))
                    for t in range(6):
                        aa = t * 1.05 + j
                        dr.line([(cx, cy), (cx + math.cos(aa) * s * 1.25, cy + math.sin(aa) * s * 1.25)], fill=_rgb((0.50, 0.46, 0.36)), width=int(2 * k))
                    dr.ellipse([cx - s * 0.35, cy - s * 0.35, cx + s * 0.35, cy + s * 0.35], fill=_rgb((0.70, 0.62, 0.48)))
            else:                              # squid
                for j in range(3):
                    cy = y0 + chh * (0.22 + j * 0.28)
                    dr.ellipse([x0 + cw * 0.1, cy - chh * 0.08, x0 + cw * 0.62, cy + chh * 0.08], fill=_rgb((0.90, 0.82, 0.80)))
                    dr.polygon([(x0 + cw * 0.08, cy), (x0 + cw * 0.2, cy - chh * 0.1), (x0 + cw * 0.2, cy + chh * 0.1)], fill=_rgb((0.88, 0.78, 0.78)))
                    for t in range(5):
                        dr.line([(x0 + cw * 0.62, cy - chh * 0.04 + t * chh * 0.02), (x1 - cw * 0.08, cy - chh * 0.06 + t * chh * 0.03)],
                                fill=_rgb((0.84, 0.70, 0.70)), width=int(2 * k))
            # the price card stuck in the ice
            px = x0 + cw * 0.62; py = y0 + chh * 0.66
            dr.rectangle([px, py, px + cw * 0.32, py + chh * 0.28], fill=_rgb((0.97, 0.97, 0.95)))
            pr = ['480', '180', '300', '450'][kind]
            _text(dr, pr, (px + cw * 0.16, py + chh * 0.14), chh * 0.18, (0.8, 0.1, 0.1), maxw=cw * 0.3, latin=True, seed=110 + col, rough=0.2)
    _age(dr, 107, grime=0.15)


# ---------------------------------------------------------------- interiors
def t_int_sembei(dr, w, h, k):
    _shelves(dr, 0, 0, w, h * 0.62, 3, k, 111, [(0.80, 0.60, 0.32), (0.66, 0.16, 0.12), (0.92, 0.88, 0.76), (0.30, 0.38, 0.30)])
    dr.rectangle([0, h * 0.62, w, h], fill=_rgb((0.36, 0.26, 0.18)))
    dr.rectangle([w * 0.1, h * 0.55, w * 0.9, h * 0.66], fill=_rgb((0.50, 0.36, 0.22)))
    for i in range(6):
        cx = w * (0.15 + i * 0.13)
        dr.rounded_rectangle([cx - w * 0.045, h * 0.42, cx + w * 0.045, h * 0.56], radius=4 * k, fill=_rgb((0.70, 0.66, 0.56)))
        dr.ellipse([cx - w * 0.035, h * 0.45, cx + w * 0.035, h * 0.52], fill=_rgb((0.66, 0.44, 0.22)))
    dr.rectangle([w * 0.62, h * 0.05, w * 0.95, h * 0.16], fill=_rgb(PAPERW))
    _text(dr, '醤油 一枚 百円', (w * 0.785, h * 0.105), h * 0.06, INK, maxw=w * 0.3, seed=120, rough=0.2)
    _glass(dr, w, h, k, 9, 0.7)
    _age(dr, 112, grime=0.15)


def t_back_sembei(dr, w, h, k):
    _shelves(dr, 0, 0, w, h * 0.7, 3, k, 113, [(0.80, 0.60, 0.32), (0.92, 0.88, 0.76), (0.66, 0.16, 0.12), (0.78, 0.70, 0.52)],
             wall=(0.40, 0.30, 0.22))
    dr.rectangle([0, h * 0.7, w, h], fill=_rgb((0.42, 0.32, 0.22)))
    for i in range(4):
        x = w * (0.05 + i * 0.25)
        dr.rectangle([x, h * 0.04, x + w * 0.2, h * 0.16], fill=_rgb(PAPERW))
        _text(dr, ['ざらめ', 'のり巻', 'ごま', 'えび'][i], (x + w * 0.1, h * 0.1), h * 0.07, INK, maxw=w * 0.18, seed=121 + i, rough=0.2)
    _age(dr, 114, grime=0.3)


def t_int_soba(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_rgb((0.42, 0.32, 0.22)))
    dr.rectangle([0, h * 0.68, w, h], fill=_rgb((0.30, 0.24, 0.18)))
    for i in range(7):
        x = w * (0.05 + i * 0.13)
        dr.rectangle([x, h * 0.08, x + w * 0.1, h * 0.3], fill=_rgb(PAPERW))
        _ink(dr, ['もり', 'かけ', '天ざる', 'とろろ', 'にしん', '鴨南蛮', 'しらす'][i], (x, h * 0.09, x + w * 0.1, h * 0.29), INK,
             vertical=True, frac=0.9, bold=0.03, seed=130 + i, rough=0.1)
    for cx in (w * 0.25, w * 0.72):
        dr.rectangle([cx - w * 0.18, h * 0.58, cx + w * 0.18, h * 0.63], fill=_rgb((0.56, 0.40, 0.26)))
        for sx in (-0.12, 0.12):
            dr.rectangle([cx + w * sx - w * 0.05, h * 0.66, cx + w * sx + w * 0.05, h * 0.72], fill=_rgb((0.50, 0.36, 0.24)))
        dr.ellipse([cx - w * 0.06, h * 0.40, cx + w * 0.06, h * 0.52], fill=_rgb((0.98, 0.86, 0.60)))
    _glass(dr, w, h, k, 10, 0.6)
    _age(dr, 115, grime=0.15)


def t_int_wagashi(dr, w, h, k):
    _shelves(dr, 0, 0, w, h * 0.58, 2, k, 116, [(0.86, 0.80, 0.66), (0.66, 0.36, 0.30), (0.48, 0.56, 0.36), (0.92, 0.90, 0.84)],
             wall=(0.62, 0.54, 0.42), item=(0.1, 0.2))
    dr.rectangle([0, h * 0.58, w, h], fill=_rgb((0.52, 0.42, 0.30)))
    dr.rectangle([w * 0.55, h * 0.06, w * 0.9, h * 0.22], fill=_rgb(PAPERW))
    _ink(dr, '柏餅あります', (w * 0.57, h * 0.08, w * 0.88, h * 0.2), INK, frac=0.9, bold=0.04, seed=140, rough=0.2)
    _glass(dr, w, h, k, 11, 0.7)
    _age(dr, 117, grime=0.15)


def t_int_tea(dr, w, h, k):
    _shelves(dr, 0, 0, w, h * 0.66, 3, k, 118, [(0.24, 0.40, 0.24), (0.80, 0.68, 0.30), (0.12, 0.12, 0.12), (0.62, 0.30, 0.20)],
             wall=(0.40, 0.32, 0.22), item=(0.07, 0.11))
    dr.rectangle([0, h * 0.66, w, h], fill=_rgb((0.34, 0.26, 0.18)))
    _glass(dr, w, h, k, 12, 0.7)
    _age(dr, 119, grime=0.15)


def t_back_tea(dr, w, h, k):
    _shelves(dr, 0, 0, w, h * 0.72, 3, k, 120, [(0.24, 0.40, 0.24), (0.80, 0.68, 0.30), (0.12, 0.12, 0.12), (0.62, 0.30, 0.20)],
             wall=(0.38, 0.30, 0.22), item=(0.06, 0.1))
    dr.rectangle([0, h * 0.72, w, h], fill=_rgb((0.30, 0.24, 0.18)))
    for i, s in enumerate(('煎茶', 'ほうじ茶', '玄米茶')):
        x = w * (0.06 + i * 0.32)
        dr.rectangle([x, h * 0.02, x + w * 0.24, h * 0.12], fill=_rgb(PAPERW))
        _text(dr, s, (x + w * 0.12, h * 0.07), h * 0.07, INK, maxw=w * 0.22, seed=150 + i, rough=0.2)
    _age(dr, 121, grime=0.3)


def t_back_souv(dr, w, h, k):
    _shelves(dr, 0, 0, w, h * 0.75, 3, k, 122, [(0.80, 0.24, 0.20), (0.92, 0.88, 0.76), (0.20, 0.30, 0.52), (0.86, 0.70, 0.30),
                                                 (0.36, 0.56, 0.40), (0.95, 0.70, 0.74)], wall=(0.70, 0.64, 0.54))
    dr.rectangle([0, h * 0.75, w, h], fill=_rgb((0.50, 0.44, 0.38)))
    for i in range(6):
        x = w * (0.04 + i * 0.16)
        dr.rectangle([x, h * 0.03, x + w * 0.1, h * 0.12], fill=_rgb(PAPERW))
        _text(dr, ['あじさい飴', '手ぬぐい', 'お箸', '湯のみ', '絵はがき', 'すず'][i], (x + w * 0.05, h * 0.075), h * 0.06, INK,
              maxw=w * 0.095, seed=160 + i, rough=0.2)
    _age(dr, 123, grime=0.3)


def t_back_fish(dr, w, h, k):
    a = _arr(dr); H_, W_ = a.shape[:2]
    X = np.arange(W_)[None, :]; Y = np.arange(H_)[:, None]
    t = 9 * k
    joint = ((X % t) < 1.2 * k) | ((Y % t) < 1.2 * k)
    a[:] = np.where(joint[..., None], np.array((0.62, 0.64, 0.64)), np.array((0.86, 0.90, 0.90)))
    _set(dr, a)
    dr.rectangle([w * 0.05, h * 0.18, w * 0.38, h * 0.92], fill=_rgb((0.78, 0.80, 0.82)))
    dr.rectangle([w * 0.07, h * 0.22, w * 0.36, h * 0.78], fill=_rgb((0.42, 0.52, 0.58)))
    for j in range(3):
        y = h * (0.3 + j * 0.15)
        for i in range(5):
            x = w * (0.09 + i * 0.053)
            dr.rectangle([x, y, x + w * 0.045, y + h * 0.1], fill=_rgb([(0.92, 0.9, 0.86), (0.86, 0.4, 0.34), (0.94, 0.86, 0.7)][(i + j) % 3]))
    dr.rectangle([w * 0.45, h * 0.55, w * 0.8, h * 0.92], fill=_rgb((0.76, 0.78, 0.80)))
    dr.rectangle([w * 0.45, h * 0.5, w * 0.8, h * 0.56], fill=_rgb((0.86, 0.88, 0.90)))
    dr.rectangle([w * 0.84, h * 0.2, w * 0.96, h * 0.42], fill=_rgb(PAPERW))
    _text(dr, '活〆', (w * 0.9, h * 0.31), h * 0.1, (0.7, 0.1, 0.1), maxw=w * 0.1, seed=170, rough=0.3)
    dr.rectangle([0, h * 0.92, w, h], fill=_rgb((0.36, 0.38, 0.38)))
    _age(dr, 124, grime=0.35, stains=6)


def t_int_kissa(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_rgb((0.52, 0.36, 0.24)))
    dr.ellipse([w * 0.4, h * 0.2, w * 0.6, h * 0.6], fill=_rgb((0.98, 0.84, 0.56)))
    a = _arr(dr); H_, W_ = a.shape[:2]
    X = np.arange(W_)[None, :].astype(np.float32); Y = np.arange(H_)[:, None].astype(np.float32)
    lace = (np.sin(X / (3 * k)) * np.sin(Y / (3 * k)) > 0.3) | (np.abs(np.sin((X + Y) / (7 * k))) > 0.92)
    cover = (Y < H_ * 0.62) & ((X < W_ * 0.44) | (X > W_ * 0.56))
    a = np.where((cover & lace)[..., None], a * 0.25 + 0.75 * np.array((0.95, 0.94, 0.9)), a)
    a = np.where((cover & ~lace)[..., None], a * 0.6 + 0.4 * np.array((0.9, 0.88, 0.84)), a)
    _set(dr, a)
    _glass(dr, w, h, k, 13, 0.6)


def _win(dr, w, h, k, curtain, frosted=False, seed=0):
    dr.rectangle([0, 0, w, h], fill=_rgb((0.18, 0.18, 0.2)))
    if frosted:
        dr.rectangle([0, 0, w * 0.5, h], fill=_rgb((0.74, 0.76, 0.76)))
    else:
        dr.rectangle([w * 0.05, 0, w * 0.22, h], fill=_rgb(curtain))
        dr.rectangle([w * 0.22, h * 0.0, w * 0.5, h * 0.08], fill=_rgb(tuple(v * 0.9 for v in curtain)))
    a = _arr(dr); H_, W_ = a.shape[:2]
    X = np.arange(W_)[None, :]; Y = np.arange(H_)[:, None]
    mesh = (((X % int(2 * k + 1)) == 0) | ((Y % int(2 * k + 1)) == 0)) & (X > W_ * 0.5)
    a = np.where((X > W_ * 0.5)[..., None] & np.ones_like(a, bool), a * 0.62 + 0.1, a)
    a = np.where(mesh[..., None], a * 0.75, a)
    _set(dr, a)
    _glass(dr, w, h, k, seed, 0.9)


def t_win_a(dr, w, h, k): _win(dr, w, h, k, (0.84, 0.78, 0.62), seed=14)
def t_win_b(dr, w, h, k): _win(dr, w, h, k, (0.62, 0.72, 0.80), frosted=True, seed=15)


def t_sudare(dr, w, h, k):
    dr.rectangle([0, 0, w, h], fill=_rgb((0.22, 0.18, 0.14)))
    y = 0.0
    r = np.random.default_rng(130)
    while y < h:
        t = r.uniform(0.85, 1.05)
        dr.rectangle([0, y, w, y + 2.4 * k], fill=_rgb((0.74 * t, 0.62 * t, 0.42 * t)))
        y += 3.2 * k
    for x in (w * 0.15, w * 0.5, w * 0.85):
        dr.line([(x, 0), (x, h)], fill=_rgb((0.36, 0.26, 0.18)), width=int(2 * k))
    dr.rectangle([0, h * 0.94, w, h], fill=_rgb((0.42, 0.30, 0.20)))
    _age(dr, 131, fade=0.35, grime=0.4, stains=4, fade_col=(0.70, 0.66, 0.58))


def paint(img, pp):
    """Paints this module's tiles: pp(img, name, painter(dr, w, h, k), background rgb)."""
    for name, fn in (('ks_sg_sembei', t_sg_sembei), ('ks_sg_soba', t_sg_soba), ('ks_sg_wagashi', t_sg_wagashi),
                     ('ks_sg_souv', t_sg_souv), ('ks_sg_fish', t_sg_fish), ('ks_sg_kissa', t_sg_kissa),
                     ('ks_sg_kissa2', t_sg_kissa2), ('ks_sg_tea', t_sg_tea), ('ks_nr_sembei', t_nr_sembei),
                     ('ks_nr_soba', t_nr_soba), ('ks_nr_wagashi', t_nr_wagashi), ('ks_nr_tea', t_nr_tea),
                     ('ks_lt_sembei', _lantern_tile('せんべい', (0.80, 0.18, 0.13), INK)),
                     ('ks_lt_soba', _lantern_tile('そば', (0.82, 0.20, 0.14), INK)),
                     ('ks_lt_souv', _lantern_tile('みやげ', (0.82, 0.20, 0.14), INK)),
                     ('ks_nobori', t_nobori), ('ks_nobori2', t_nobori2), ('ks_menu_soba', t_menu_soba),
                     ('ks_price_fish', t_price_fish), ('ks_sample', t_sample), ('ks_case', t_case), ('ks_jar', t_jar),
                     ('ks_grill', t_grill), ('ks_tenugui', t_tenugui), ('ks_goods1', t_goods1), ('ks_goods2', t_goods2),
                     ('ks_cards', t_cards), ('ks_fish', t_fish), ('ks_int_sembei', t_int_sembei),
                     ('ks_int_soba', t_int_soba), ('ks_int_wagashi', t_int_wagashi), ('ks_int_tea', t_int_tea),
                     ('ks_int_kissa', t_int_kissa), ('ks_back_sembei', t_back_sembei), ('ks_back_souv', t_back_souv),
                     ('ks_back_fish', t_back_fish), ('ks_back_tea', t_back_tea), ('ks_win_a', t_win_a),
                     ('ks_win_b', t_win_b), ('ks_sudare', t_sudare)):
        pp(img, name, fn, (0.5, 0.5, 0.5))


# ================================================================ the shops
def shop_sembei(B):
    """A rice-cracker shop: an open counter window with glass jars of senbei and the grill, sliding glass doors under an
    indigo noren, a tiled pent roof, the big hand-painted signboard across the upper floor, red paper lanterns."""
    W, H, D = B.W, B.H, B.D
    win = (-3.32, -0.12, 0.0, 2.55)
    dor = (0.1, 3.32, 0.0, 2.55)
    up = [(-2.8, -1.05, 4.6, 5.55), (0.15, 1.9, 4.6, 5.55)]
    F, Rt, Bk, Lf, top = km_shell(B, [win, dor] + up, side_ops=[(5.2, 6.2, 4.3, 5.3)])
    posts(B, F, [-W / 2, -0.11, W / 2])
    B.feat('front', 'km_boards', a0=-W / 2, a1=W / 2, b0=0.0, b1=GF, bw=0.21, silver=0.6)
    # the counter window: the shop behind, the counter with its jars and the grill
    km_room(B, win[0], win[1], 0.0, win[3], 1.7, back='ks_back_sembei')
    put(B, F, fbox((win[0], 0.0, -0.3), (win[1], 0.86, 0.24), 0.01, 'kstimb'))
    put(B, F, fbox((win[0] - 0.02, 0.86, -0.45), (win[1] + 0.02, 0.92, 0.34), 0.012, 'kscedar'))
    for i, x in enumerate((-3.0, -2.62, -2.24, -1.86)):
        jar(B, (x, -0.06, 0.92), r=0.135, h=0.32, lid=('ksred', 'ksred', 'kscream', 'ksred')[i])
    B.add(cbox2((-1.42, -0.3, 0.92), (-0.38, 0.12, 1.1), 0.015, 'ksblack'))
    mb = MB()
    mb.face([(-1.36, -0.25, 1.105), (-0.44, -0.25, 1.105), (-0.44, 0.07, 1.105), (-1.36, 0.07, 1.105)], 'tex', (0, 0, 1), 1.0,
            lambda co: reg_uv('ks_grill', (co.x + 1.36) / 0.92, (co.y + 0.25) / 0.32, 0.0))
    B.add(mb.bm())
    B.add(cbox2((-1.42, -0.32, 1.1), (-0.38, -0.27, 1.16), 0.008, 'ksstain'))
    # the doors, the noren, the pent roof, the signboard, the lanterns
    sliding_doors(B, F, dor[0], dor[1], dor[3], 'ks_int_sembei', n=4, bars=(1.15,))
    noren(B, F, dor[0] + 0.2, dor[1] - 0.2, 2.5, 1.0, 'ks_nr_sembei', n=3, seed=1)
    hisashi(B, -W / 2 + 0.02, W / 2 - 0.25, 2.8, out=0.85, rise=0.36)
    kanban(B, F, -2.75, 2.75, 3.42, 4.32, 'ks_sg_sembei', out=0.12, cap=True)
    for x in (-3.05, -0.12):
        chochin(B, (x, -0.58, 2.24), 'ks_lt_sembei', hang=0.58)
    # upstairs: the family's windows (one under a bamboo blind), the AC on its brackets
    up_window(B, F, *up[0], glass='ks_win_a', seed=1)
    up_window(B, F, *up[1], glass='ks_win_b', seed=2, rail=True)
    sudare(B, F, up[0][0] - 0.05, up[0][1] + 0.05, up[0][3] + 0.06, 0.62)
    ac_front(B, F, 2.7, 4.75)
    meter_box(B, F, 3.2, 1.55, w=0.3, h=0.42)
    up_window(B, Rt, 5.2, 6.2, 4.3, 5.3, glass='ks_win_b', seed=3, register=False)
    B.feat('front', 'km_crack', pts=[(-1.0, 5.6, 1.2, 0.5), (2.1, 4.55, -0.6, 0.45), (3.2, 3.9, 2.2, 0.4)])
    B.feat('front', 'km_salt', a0=-W / 2, a1=W / 2, b0=3.3, b1=4.4, k=0.4)
    B.feat('front', 'km_wet', a0=-W / 2, a1=W / 2, h=0.25)
    return top + 0.15


def shop_soba(B):
    """A soba restaurant: a dark timber front (vertical boards below, lapped boards above), a lattice window, a wooden
    sliding door under a white noren with the house's name, a tiled pent roof, a lantern, a menu board, the name board."""
    W, H, D = B.W, B.H, B.D
    lat = (-3.45, -0.95, 0.42, 2.3)
    dor = (-0.5, 1.4, 0.0, 2.12)
    up = [(-3.0, -1.3, 4.6, 5.55), (1.1, 2.8, 4.6, 5.55)]
    F, Rt, Bk, Lf, top = km_shell(B, [lat, dor] + up, zones=[(-W / 2, W / 2, 0.0, H, 'kstimb')], side_ops=[(5.0, 6.0, 4.3, 5.3)])
    posts(B, F, [-W / 2, -0.75, 1.62, W / 2], beam=(2.42, 2.62))
    B.feat('front', 'km_boards', a0=-W / 2, a1=W / 2, b0=0.0, b1=2.62, bw=0.19, silver=0.35)
    B.feat('front', 'km_boards', a0=-W / 2, a1=W / 2, b0=2.62, b1=H, bw=0.21, horiz=True, silver=0.5)
    # the lattice: a stone sill, paper screens behind close slats
    put(B, F, fbox((lat[0] - 0.06, 0.0, -0.02), (lat[1] + 0.06, lat[2], 0.1), 0.015, 'kmstone'))
    mb = MB()
    reveal(mb, *lat, 0.1)
    mb.face([(lat[0], lat[2], -0.1), (lat[1], lat[2], -0.1), (lat[1], lat[3], -0.1), (lat[0], lat[3], -0.1)], 'kmpaper', (0, 0, 1), 0.72)
    x = lat[0] + 0.02
    while x < lat[1] - 0.03:
        bar(mb, x, lat[2], x + 0.026, lat[3], -0.09, -0.01, 'ksdark')
        x += 0.052
    for zz in (lat[2] + 0.02, (lat[2] + lat[3]) / 2, lat[3] - 0.05):
        bar(mb, lat[0], zz, lat[1], zz + 0.04, -0.06, 0.0, 'ksdark')
    put(B, F, mb.bm())
    # the door, its noren and the transom lattice over it
    sliding_doors(B, F, dor[0], dor[1], dor[3], 'ks_int_soba', n=2, bars=(0.75, 1.45))
    noren(B, F, dor[0] + 0.05, dor[1] - 0.05, 2.1, 0.92, 'ks_nr_soba', n=2, seed=2)
    hisashi(B, -W / 2 + 0.02, W / 2 - 0.25, 2.66, out=0.88, rise=0.38)
    chochin(B, (-0.73, -0.55, 2.05), 'ks_lt_soba', hang=0.66)
    kanban(B, F, -2.3, 2.3, 3.4, 4.25, 'ks_sg_soba', out=0.11, frame='ksblack', cap=True)
    # the menu board on the wall, a planter by the door
    put(B, F, fbox((1.95, 0.9, 0.0), (2.6, 2.28, 0.05), 0.01, 'ksdark'))
    decal(B, F, 2.0, 2.55, 0.95, 2.23, 0.052, 'ks_menu_soba')
    pot(B, (3.25, -0.32, 0.0), 0.2, 0.36, 'ksjar2', 'tall', seed=21, scale=1.1)
    pot(B, (2.75, -0.3, 0.0), 0.15, 0.22, 'pot', 'bush', seed=22)
    # upstairs
    up_window(B, F, *up[0], glass='ks_win_b', seed=4)
    up_window(B, F, *up[1], glass='ks_win_a', seed=5)
    ac_front(B, F, -0.1, 4.75)
    up_window(B, Rt, 5.0, 6.0, 4.3, 5.3, glass='ks_win_a', seed=6, register=False)
    # the kitchen's flue up the side
    fx, fy = W / 2 - 0.6, D + 0.16
    B.add(tube([(fx, D, 1.8), (fx, fy, 1.8), (fx, fy, H + 2.2)], 0.12, 'galvw', 8))
    cp, _ = lathe([(0.0, -0.05), (0.26, 0.0), (0.0, 0.16)], 8, 'galvw')
    xform(cp, T(fx, fy, H + 2.32)); B.add(cp)
    B.feat('front', 'km_wet', a0=-W / 2, a1=W / 2, h=0.22)
    return top + 0.15


def shop_wagashi(B):
    """A Japanese sweets shop: a glass case of wagashi under its window, sliding glass doors under a pale noren, a wooden
    signboard hanging from the pent roof, a bench under a red felt cloth out front; white plaster above."""
    W, H, D = B.W, B.H, B.D
    dor = (-3.05, -0.95, 0.0, 2.2)
    case = (-0.68, 1.88, 0.0, 1.1)
    cwin = (-0.68, 1.88, 1.2, 2.35)
    up = [(-2.6, -0.6, 4.25, 5.5), (0.9, 2.5, 4.25, 5.5)]
    F, Rt, Bk, Lf, top = km_shell(B, [dor, case, cwin] + up, side_ops=[(5.0, 6.0, 4.2, 5.2)])
    posts(B, F, [-W / 2, -0.82, 2.0, W / 2], beam=(2.4, 2.65))
    B.feat('front', 'km_boards', a0=-W / 2, a1=W / 2, b0=0.0, b1=2.65, bw=0.2, silver=0.5)
    sliding_doors(B, F, dor[0], dor[1], dor[3], 'ks_int_wagashi', n=2, bars=(0.9,))
    noren(B, F, dor[0] + 0.05, dor[1] - 0.05, 2.16, 0.78, 'ks_nr_wagashi', n=3, seed=3)
    # the display case: a dark wooden base, a glass box of sweets (front and top from one tile), its frame
    x0, x1 = case[0] + 0.02, case[1] - 0.02
    put(B, F, fbox((case[0], 0.0, -0.45), (case[1], 0.72, 0.32), 0.012, 'ksdark'))
    put(B, F, fbox((case[0] - 0.02, 0.72, -0.45), (case[1] + 0.02, 0.76, 0.34), 0.008, 'kscedar'))
    g0, g1, gw = 0.76, 1.1, 0.3
    mb = MB()
    mb.face([(x0, g0, gw), (x1, g0, gw), (x1, g1, gw), (x0, g1, gw)], 'tex', (0, 0, 1), 1.0,
            lambda co: reg_uv('ks_case', (co.x - x0) / (x1 - x0), 0.5 * (1 - (co.y - g0) / (g1 - g0)) + 0.0, 0.0))
    mb.face([(x0, g1, gw), (x1, g1, gw), (x1, g1, -0.42), (x0, g1, -0.42)], 'tex', (0, 1, 0), 1.0,
            lambda co: reg_uv('ks_case', (co.x - x0) / (x1 - x0), 0.5 + 0.5 * (gw - co.z) / (gw + 0.42), 0.0))
    for xx, sg in ((x0, -1), (x1, 1)):
        mb.face([(xx, g0, -0.42), (xx, g0, gw), (xx, g1, gw), (xx, g1, -0.42)], 'kmalu', (sg, 0, 0), 0.75)
    put(B, F, mb.bm())
    for xx in (x0, x1):
        put(B, F, box((xx - 0.015, g0, gw - 0.015), (xx + 0.015, g1, gw + 0.015), 'kmalu'))
    put(B, F, box((x0, g1 - 0.015, gw - 0.015), (x1, g1 + 0.015, gw + 0.015), 'kmalu'))
    window(B, F, *cwin, depth=0.12, fw=0.05, cols=3, frame='ksdark', glass='ks_int_wagashi', sill=None, head=None, cheap=True, seed=7)
    # pent roof, the hanging signboard on its rods, the bench
    hisashi(B, -W / 2 + 0.02, W / 2 - 0.25, 2.75, out=0.85, rise=0.36)
    sx, sy = 2.6, -0.42
    B.add(cbox2((sx - 0.24, sy - 0.02, 1.08), (sx + 0.24, sy + 0.025, 2.42), 0.006, 'kscedar'))
    mb = MB()
    mb.face([(sx - 0.22, sy - 0.021, 1.1), (sx + 0.22, sy - 0.021, 1.1), (sx + 0.22, sy - 0.021, 2.4), (sx - 0.22, sy - 0.021, 2.4)], 'tex',
            (0, -1, 0), 1.0, lambda co: reg_uv('ks_sg_wagashi', (co.x - sx + 0.22) / 0.44, (co.z - 1.1) / 1.3, 0.0))
    B.add(mb.bm())
    B.add(cbox2((sx - 0.29, sy - 0.05, 2.42), (sx + 0.29, sy + 0.05, 2.48), 0.008, 'ksdark'))
    for xx in (sx - 0.18, sx + 0.18):
        B.add(tube([(xx, sy, 2.48), (xx, sy, 2.95)], 0.007, 'ksblack', 4))
    endai(B, 0.95, 2.6, -0.95, -0.55)
    pot(B, (-0.2, -0.75, 0.0), 0.17, 0.26, 'pot2', 'flowers', seed=31)
    # upstairs: white plaster, a window behind a bamboo blind, one with a hand rail, the AC
    up_window(B, F, *up[0], glass='ks_win_a', seed=8, rail=True)
    up_window(B, F, *up[1], glass='ks_win_b', seed=9)
    sudare(B, F, up[1][0] - 0.05, up[1][1] + 0.05, up[1][3] + 0.06, 0.8)
    ac_front(B, F, 2.75, 3.75, w=0.66, h=0.48)
    up_window(B, Rt, 5.0, 6.0, 4.2, 5.2, glass='ks_win_a', seed=10, register=False)
    B.feat('front', 'km_crack', pts=[(-0.6, 4.2, -0.8, 0.5), (0.9, 5.5, 0.8, 0.4), (-2.9, 3.6, 1.4, 0.35)])
    B.feat('front', 'km_salt', a0=-W / 2, a1=W / 2, b0=3.25, b1=4.0, k=0.5)
    return top + 0.15


def shop_souvenir(B):
    """A souvenir shop on the shrine approach: open to the lane under a striped canvas awning, tables of tenugui and
    chopsticks, bells and postcards out front, tenugui hanging in the doorway, a nobori, red lanterns; the family's
    balcony upstairs with its name board on the railing and the washing out."""
    W, H, D = B.W, B.H, B.D
    op = (-3.82, 3.82, 0.0, 2.62)
    up = [(-2.7, -0.7, 3.45, 5.35), (0.7, 2.7, 3.45, 5.35)]
    F, Rt, Bk, Lf, top = km_shell(B, [op] + up, side_ops=[(5.0, 6.0, 4.2, 5.2)])
    posts(B, F, [-W / 2, W / 2], beam=(2.62, 2.95))
    B.feat('front', 'km_boards', a0=-W / 2, a1=W / 2, b0=0.0, b1=2.95, bw=0.2, silver=0.5)
    km_room(B, op[0], op[1], 0.0, op[3], 2.6, back='ks_back_souv')
    # the rolled-up shutter's box, the awning, the lanterns
    put(B, F, fbox((op[0], 2.64, 0.0), (op[1], 2.94, 0.26), 0.03, 'kmalu'))
    awning(B, F, -W / 2 + 0.05, W / 2 - 0.25, 3.12, 0.92, 0.42, 15, mat_a='accent', mat_b='kscream', valance=0.2, scallops=False)
    for x in (-3.45, 3.25):
        chochin(B, (x, -0.42, 2.3), 'ks_lt_souv', h=0.5, r=0.17, hang=0.32)
    # tenugui hanging in the doorway
    put(B, F, tube([(-1.55, 2.45, 0.06), (0.15, 2.45, 0.06)], 0.012, 'kscedar', 4))
    mb = MB()
    for i in range(4):
        a = -1.5 + i * 0.41; b = a + 0.36
        mb.face([(a, 1.6, 0.065), (b, 1.6, 0.065), (b, 2.44, 0.06), (a, 2.44, 0.06)], 'tex', (0, 0, 1), 1.0,
                lambda co, i=i, a=a: reg_uv('ks_tenugui', (i + (co.x - a) / 0.36) / 4, (co.y - 1.6) / 0.84, 0.0))
    put(B, F, mb.bm())
    # the tables out front, the postcard rack, the nobori
    goods_table(B, -3.45, -1.6, -0.92, -0.32, 0.78, 'ks_goods1', tilt=0.32)
    goods_table(B, 0.4, 2.3, -0.92, -0.32, 0.78, 'ks_goods2', tilt=0.32, skirt='ksnobb')
    for xx in (-3.38, -1.67, 0.47, 2.23):
        B.add(tube([(xx, -0.4, 0.0), (xx, -0.4, 0.95)], 0.02, 'kmalu', 4))
    B.add(cbox2((-1.08, -0.62, 0.15), (-0.52, -0.42, 1.62), 0.01, 'ksbase'))
    mb = MB()
    mb.face([(-1.05, -0.625, 0.2), (-0.55, -0.625, 0.2), (-0.55, -0.625, 1.58), (-1.05, -0.625, 1.58)], 'tex', (0, -1, 0), 1.0,
            lambda co: reg_uv('ks_cards', (co.x + 1.05) / 0.5, (co.z - 0.2) / 1.38, 0.0))
    B.add(mb.bm())
    for xx in (-1.02, -0.58):
        B.add(box((xx - 0.02, -0.58, 0.0), (xx + 0.02, -0.46, 0.15), 'ksbase'))
    _nobori(B, 3.42, -0.75, 'ks_nobori2', top=2.4)
    reg_door(B, F, 2.4, 3.3, 2.62)
    # upstairs: the balcony, its name board, the washing, glass doors, the AC on the balcony floor
    balcony(B, -3.0, 2.95, 3.32, out=0.72, h=0.95)
    kanban(B, F.off(0.78), -2.75, 2.75, 3.4, 4.1, 'ks_sg_souv', out=0.05, frame='ksdark')
    for o, g, s in ((up[0], 'ks_win_a', 11), (up[1], 'ks_win_b', 12)):
        window(B, F, *o, depth=0.1, fw=0.05, cols=2, frame='kmalu', glass=g, sill='kmalu', head=None, mull=0.04, cheap=True, seed=s)
    laundry(B, F, -2.6, 0.9, 5.05, 0.45, seed=13, n=4)
    for xx in (-2.75, 1.05):
        put(B, F, box((xx - 0.015, 5.0, 0.0), (xx + 0.015, 5.08, 0.5), 'kmalu', skip=('-z',)))
    ground_ac(B, (2.35, -0.32, 3.32), w=0.7, h=0.5, d=0.26)
    B.feat('front', 'km_crack', pts=[(-3.4, 5.6, -0.7, 0.5), (3.4, 4.0, 1.9, 0.45)])
    B.feat('front', 'km_salt', a0=-W / 2, a1=W / 2, b0=3.0, b1=3.6, k=0.6)
    B.feat('front', 'ao', a0=-3.0, a1=2.95, b=3.2, length=0.4, k=0.4)
    return top + 0.15


def shop_fish(B):
    """A fishmonger of the Shonan coast: open to the lane under a blue canvas awning with the shop's name on its valance,
    styrofoam boxes and trays on ice on a sloping stand (whitebait, horse mackerel, turban shells, squid), a hand-written
    price board, a hose on its reel and a bucket, the wet floor; a dark standing-seam roof."""
    W, H, D = B.W, B.H, B.D
    op = (-3.32, 3.32, 0.0, 2.6)
    up = [(-2.8, -1.0, 4.2, 5.4), (0.6, 2.4, 4.2, 5.4)]
    F, Rt, Bk, Lf, top = km_shell(B, [op] + up, zones=[], side_ops=[(5.0, 6.0, 4.2, 5.2)], roof='metal', slope=0.36)
    posts(B, F, [-W / 2, W / 2], beam=(2.6, 2.95), mat='ksdark')
    km_room(B, op[0], op[1], 0.0, op[3], 3.0, back='ks_back_fish', floor='ksfloor')
    put(B, F, fbox((op[0], 2.62, 0.0), (op[1], 2.92, 0.26), 0.03, 'kmalu'))
    # the awning: blue canvas on a pipe frame, the name on its valance
    x0, x1 = -W / 2 + 0.05, W / 2 - 0.25
    zw, zf, out, val = 3.3, 2.82, 0.95, 0.32
    mb = MB()
    mb.face([(x0, 0.0, zw), (x0, -out, zf), (x1, -out, zf), (x1, 0.0, zw)], 'accent', (0, -0.45, 1), 1.0)
    mb.face([(x0, 0.0, zw - 0.02), (x1, 0.0, zw - 0.02), (x1, -out, zf - 0.02), (x0, -out, zf - 0.02)], 'accent', (0, 0.45, -1), 0.62)
    mb.face([(x0, -out - 0.005, zf - val), (x1, -out - 0.005, zf - val), (x1, -out - 0.005, zf), (x0, -out - 0.005, zf)], 'tex', (0, -1, 0), 1.0,
            lambda co: reg_uv('ks_sg_fish', (co.x - x0) / (x1 - x0), (co.z - zf + val) / val, 0.0))
    mb.face([(x0, -out, zf), (x0, -out, zf - val), (x0, -out + 0.25, zf - val + 0.1), (x0, 0.0, zw - 0.02)], 'accent', (-1, 0, 0), 0.8)
    mb.face([(x1, 0.0, zw - 0.02), (x1, -out + 0.25, zf - val + 0.1), (x1, -out, zf - val), (x1, -out, zf)], 'accent', (1, 0, 0), 0.8)
    B.add(mb.bm())
    B.add(tube([(x0, -out + 0.02, zf - 0.03), (x1, -out + 0.02, zf - 0.03)], 0.02, 'galvw', 5))
    for xx in (x0 + 0.1, x1 - 0.1):
        B.add(tube([(xx, -0.02, zw - 0.7), (xx, -out + 0.03, zf - 0.05)], 0.018, 'galvw', 5))
    B.feat('front', 'ao', a0=x0, a1=x1, b=zw, length=0.6, k=0.5)
    # the stand: a sloping front tier and a higher back one, boxes and trays on ice
    put(B, F, fbox((-3.0, 0.55, -0.3), (1.95, 0.6, 0.72), 0.008, 'ksstain'))
    put(B, F, fbox((-2.95, 0.0, -0.25), (1.9, 0.55, 0.62), 0.005, 'ksshade'))
    for xx in (-2.98, -0.55, 1.88):
        put(B, F, box((xx - 0.025, 0.0, 0.62), (xx + 0.025, 0.55, 0.69), 'ksstain', skip=('-z',)))
    for xx in (-2.4, -1.1, 0.4):
        B.add(cbox2((xx, -0.55, 0.0), (xx + 0.5, -0.2, 0.28), 0.01, 'ksblue'))
    for (cx, cy, cz, cell, tilt) in ((-2.6, -0.62, 0.62, (0, 0), 0.32), (-1.98, -0.62, 0.62, (1, 0), 0.32),
                                     (-1.36, -0.62, 0.62, (1, 1), 0.32), (-0.74, -0.62, 0.62, (2, 0), 0.32),
                                     (-0.12, -0.62, 0.62, (3, 0), 0.32), (0.5, -0.62, 0.62, (0, 1), 0.32),
                                     (1.12, -0.62, 0.62, (2, 1), 0.32), (1.62, -0.62, 0.62, (3, 1), 0.32)):
        styro(B, (cx, cy, cz), 'ks_fish', cell, w=0.56 if cx < 1.5 else 0.42, tilt=tilt)
    put(B, F, fbox((-3.0, 0.6, -0.8), (1.95, 1.0, -0.25), 0.01, 'ksstain'))
    for i, cx in enumerate((-2.55, -1.6, -0.65, 0.3, 1.25)):
        styro(B, (cx, 0.5, 1.02), 'ks_fish', ((i + 1) % 4, i % 2), w=0.82, d=0.5, h=0.12, tilt=0.4)
    # the price board hung from the awning frame, the hose and the bucket
    px0, px1, pz0, pz1, py = 2.12, 2.72, 1.25, 2.1, -0.55
    B.add(cbox2((px0 - 0.02, py, pz0 - 0.02), (px1 + 0.02, py + 0.02, pz1 + 0.02), 0.005, 'kmalu'))
    mb = MB()
    mb.face([(px0, py - 0.002, pz0), (px1, py - 0.002, pz0), (px1, py - 0.002, pz1), (px0, py - 0.002, pz1)], 'tex', (0, -1, 0), 1.0,
            lambda co: reg_uv('ks_price_fish', (co.x - px0) / (px1 - px0), (co.z - pz0) / (pz1 - pz0), 0.0))
    B.add(mb.bm())
    for xx in (px0 + 0.08, px1 - 0.08):
        B.add(tube([(xx, py + 0.01, pz1), (xx, py + 0.01, zf - 0.02)], 0.005, 'ksblack', 3))
    hose_reel(B, F, 3.05, 0.55)
    B.add(tube([(3.0, -0.05, 0.03), (2.8, -0.35, 0.03), (2.45, -0.5, 0.03), (2.35, -0.75, 0.03), (2.6, -0.85, 0.03)], 0.02, 'kshose', 5))
    bk, _ = lathe([(0.12, 0.0), (0.15, 0.3), (0.16, 0.3), (0.0, 0.26)], 10, 'ksblue')
    xform(bk, T(2.95, -0.62, 0.0)); B.add(bk)
    B.add(tube([(2.81, -0.62, 0.3), (2.95, -0.62, 0.42), (3.09, -0.62, 0.3)], 0.006, 'ksblack', 3, caps=False))
    B.add(cbox2((-3.25, -0.6, 0.0), (-2.7, -0.22, 0.3), 0.01, 'ksblue'))
    # upstairs: windows, the AC, a laundry pole under the eave
    up_window(B, F, *up[0], glass='ks_win_b', seed=14)
    up_window(B, F, *up[1], glass='ks_win_a', seed=15, rail=True)
    ac_front(B, F, -0.2, 4.4)
    for xx in (-2.9, -0.9):
        put(B, F, box((xx - 0.015, 5.55, 0.0), (xx + 0.015, 5.6, 0.42), 'kmalu', skip=('-z',)))
    laundry(B, F, -2.95, -0.85, 5.58, 0.4, seed=16, n=3)
    up_window(B, Rt, 5.0, 6.0, 4.2, 5.2, glass='ks_win_b', seed=17, register=False)
    B.feat('front', 'km_salt', a0=-W / 2, a1=W / 2, b0=2.9, b1=4.1, k=1.0)
    B.feat('front', 'km_crack', pts=[(-0.9, 5.5, -1.1, 0.6), (2.8, 3.6, 1.0, 0.5), (-3.2, 3.3, 0.5, 0.5)])
    B.feat('front', 'km_rust', pts=[(x, 2.95) for x in (-3.0, -1.2, 0.9, 2.7)], L=0.6)
    B.feat('front', 'km_wet', a0=-W / 2, a1=W / 2, h=0.4)
    reg_door(B, F, 2.0, 3.3, 2.6)
    return top + 0.1


def shop_kissa(B):
    """An old coffee house (kissaten): a two-storey box faced in brown scratch tiles with a flat roof behind a parapet, a
    wooden door with small panes under a scalloped awning, a sample case with its plastic dishes and a lace-curtained
    window above it, the house's wooden sign, a standing andon sign, potted plants; an aerial on the roof."""
    W, H, D = B.W, B.H, B.D
    pp = 0.55
    dr_ = (0.95, 1.93, 0.0, 2.12)
    case = (-2.65, -0.45, 0.82, 1.55)
    cwin = (-2.65, -0.45, 1.7, 2.4)
    up = [(-2.6, -0.8, 3.85, 5.25), (0.7, 2.5, 3.85, 5.25)]
    F, Rt, Bk, Lf = frames(B)
    wall(B, F, -W / 2, W / 2, H + pp, [dr_, case, cwin] + up, 0.0)
    wall(B, Rt, 0, D, H + pp, [(5.0, 6.0, 3.9, 4.9)], 0.0)
    wall(B, Lf, -D, 0, H + pp, [(-6.0, -5.0, 3.9, 4.9)], 0.0)
    wall(B, Bk, -W / 2, W / 2, H + pp, [], 0.0)
    flat_top(B, H, pp, coping_mat='kmalu')
    B.feat('front', 'tilegrid', a0=-W / 2, a1=W / 2, b0=0.0, b1=H + pp, tw=0.108, th=0.06, bond=0.0, var=0.22, k=0.32)
    for mp in ('right', 'left'):
        B.feat(mp, 'km_mould', a0=0.0, a1=D, b=H + pp, L=1.4, k=0.6)
        B.feat(mp, 'km_salt', a0=0.0, a1=D, b0=0.0, b1=1.1, k=0.9)
    B.feat('front', 'km_mould', a0=-W / 2, a1=W / 2, b=H + pp - 0.05, L=0.9, k=0.6)
    B.feat('front', 'km_moss', a0=-W / 2, a1=W / 2, h=0.25)
    put(B, F, fbox((-W / 2, 0.0, 0.0), (W / 2, 0.3, 0.05), 0.01, 'kmstoned'))
    # the door, its step and scalloped awning
    door(B, F, *dr_, depth=0.22, mat='ksdark', glass=0.62, panels=((1, 1),), casing=False, glass_region='ks_int_kissa', name='Door')
    put(B, F, fbox((dr_[0] - 0.12, 0.0, -0.22), (dr_[1] + 0.12, 0.1, 0.35), 0.01, 'kmstone'))
    awning(B, F, dr_[0] - 0.3, dr_[1] + 0.3, 2.62, 0.62, 0.32, 5, mat_a='accent', mat_b='accent', valance=0.2, scallops=True, arms=False)
    # the sample case set into the wall, the lace-curtained window over it
    mb = MB()
    reveal(mb, *case, 0.32)
    mb.face([(case[0], case[2], -0.3), (case[1], case[2], -0.3), (case[1], case[3], -0.3), (case[0], case[3], -0.3)], 'tex', (0, 0, 1), 1.0,
            lambda co: reg_uv('ks_sample', (co.x - case[0]) / (case[1] - case[0]), (co.y - case[2]) / (case[3] - case[2]), 0.0))
    ring(mb, (case[0], case[2], case[1], case[3]), (case[0] + 0.05, case[2] + 0.05, case[1] - 0.05, case[3] - 0.05), 0.02, 0.02, 'ksdark', 'front')
    put(B, F, mb.bm())
    put(B, F, fbox((case[0] - 0.08, case[2] - 0.08, -0.05), (case[1] + 0.08, case[2], 0.14), 0.01, 'kscedar'))
    window(B, F, *cwin, depth=0.12, fw=0.05, cols=2, frame='ksdark', glass='ks_int_kissa', sill='kscedar', head=None, cheap=True, seed=18)
    kanban(B, F, -2.85, 0.4, 2.62, 3.24, 'ks_sg_kissa', out=0.09, frame='ksdark')
    # the andon sign, the plants
    ax, ay = 2.62, -0.5
    B.add(cbox2((ax - 0.19, ay - 0.13, 0.0), (ax + 0.19, ay + 0.13, 0.12), 0.01, 'ksdark'))
    B.add(cbox2((ax - 0.17, ay - 0.11, 0.12), (ax + 0.17, ay + 0.11, 1.32), 0.012, 'kscream'))
    mb = MB()
    mb.face([(ax - 0.15, ay - 0.112, 0.18), (ax + 0.15, ay - 0.112, 0.18), (ax + 0.15, ay - 0.112, 1.27), (ax - 0.15, ay - 0.112, 1.27)], 'tex',
            (0, -1, 0), 1.0, lambda co: reg_uv('ks_sg_kissa2', (co.x - ax + 0.15) / 0.3, (co.z - 0.18) / 1.09, 0.0))
    B.add(mb.bm())
    B.add(cbox2((ax - 0.2, ay - 0.14, 1.32), (ax + 0.2, ay + 0.14, 1.38), 0.01, 'ksdark'))
    pot(B, (-3.0, -0.35, 0.0), 0.22, 0.38, 'pot', 'tall', seed=41, scale=1.15)
    pot(B, (-0.15, -0.38, 0.0), 0.17, 0.26, 'pot2', 'flowers', seed=42)
    pot(B, (0.45, -0.32, 0.0), 0.16, 0.28, 'pot3', 'bush', seed=43)
    # upstairs, the aerial, the downpipe
    up_window(B, F, *up[0], glass='ks_win_a', seed=19, rail=True)
    up_window(B, F, *up[1], glass='ks_win_b', seed=20)
    ac_front(B, F, -0.0, 3.95, w=0.66, h=0.48)
    up_window(B, Rt, 5.0, 6.0, 3.9, 4.9, glass='ks_win_a', seed=21, register=False)
    antenna(B, 1.6, D - 2.0, H)
    wall_pipe(B, W / 2 - 0.14, -0.08, H + pp - 0.1)
    B.feat('front', 'km_crack', pts=[(-1.6, 3.6, 0.6, 0.6), (2.6, 5.6, -0.9, 0.5)])
    B.feat('front', 'km_salt', a0=-W / 2, a1=W / 2, b0=0.0, b1=0.8, k=0.7)
    B.feat('front', 'km_rust', pts=[(-2.6, 2.6), (0.15, 2.6)], L=0.5)
    B.attach.append(('Wire', (round(-W / 2 + 0.4, 3), -0.05, round(H - 0.4, 3))))
    return H + pp + 0.1


def shop_tea(B):
    """A tea shop: a roaster turning in the open window beside tea jars and shelves of tins, its stainless vent up the front
    with soot above it, sliding glass doors under a dark noren with 茶 on it, the signboard; silvered boards upstairs."""
    W, H, D = B.W, B.H, B.D
    dor = (-2.82, -0.42, 0.0, 2.2)
    win = (-0.18, 2.32, 0.0, 2.4)
    up = [(-2.4, -0.7, 4.4, 5.5), (0.5, 2.0, 4.4, 5.5)]
    F, Rt, Bk, Lf, top = km_shell(B, [dor, win] + up,
                                  zones=[(-W / 2, W / 2, 0.0, GF, 'kstimb'), (-W / 2, W / 2, GF, H, 'kssilv')],
                                  side_ops=[(5.0, 6.0, 4.3, 5.3)])
    posts(B, F, [-W / 2, -0.3, 2.45, W / 2], beam=(2.42, 2.68))
    B.feat('front', 'km_boards', a0=-W / 2, a1=W / 2, b0=0.0, b1=2.68, bw=0.2, silver=0.4)
    B.feat('front', 'km_boards', a0=-W / 2, a1=W / 2, b0=2.68, b1=H, bw=0.24, silver=0.9, battens=True, nails=(3.6, 4.9))
    sliding_doors(B, F, dor[0], dor[1], dor[3], 'ks_int_tea', n=2, bars=(0.9, 1.6))
    noren(B, F, dor[0] + 0.05, dor[1] - 0.05, 2.16, 0.95, 'ks_nr_tea', n=2, seed=4)
    # the window: shelves of tins behind, the roaster on its stand, jars on a low platform
    km_room(B, win[0], win[1], 0.0, win[3], 1.3, back='ks_back_tea')
    put(B, F, fbox((win[0], 0.0, -0.4), (win[1], 0.42, 0.18), 0.01, 'kscedar'))
    rx0, rx1, ry, rz = 0.95, 1.85, 0.05, 1.05
    B.add(tube([(rx0, ry, rz), (rx1, ry, rz)], 0.24, 'ksstain', 10))
    for xx in (rx0 - 0.03, rx1 + 0.03):
        B.add(tube([(xx, ry, rz - 0.26), (xx, ry, rz + 0.26)], 0.03, 'ksdark', 4))
    for xx in (rx0 + 0.05, rx1 - 0.05):
        for yy in (ry - 0.18, ry + 0.18):
            B.add(box((xx - 0.025, yy - 0.025, 0.42), (xx + 0.025, yy + 0.025, rz - 0.18), 'ksdark', skip=('-z',)))
    B.add(cbox2((rx0, ry - 0.2, 0.55), (rx1, ry + 0.2, 0.72), 0.01, 'ksdark'))
    B.add(box((rx0 + 0.1, ry - 0.205, 0.58), (rx1 - 0.1, ry - 0.2, 0.66), 'ksglow'))
    hp, _ = lathe([(0.04, 0.0), (0.06, 0.05), (0.2, 0.3), (0.2, 0.34), (0.0, 0.34)], 8, 'ksstain')
    xform(hp, T(rx0 + 0.25, ry, rz + 0.18)); B.add(hp)
    B.add(tube([(rx1 - 0.1, ry, rz + 0.2), (rx1 - 0.1, ry, 2.25), (W / 2 - 0.3, ry, 2.25)], 0.08, 'ksstain', 8))
    vx = W / 2 - 0.35
    B.add(tube([(vx, 0.02, 2.25), (vx, -0.22, 2.25), (vx, -0.22, 5.3), (vx, -0.5, 5.3)], 0.085, 'ksstain', 8))
    hood_, _ = lathe([(0.0, 0.0), (0.16, 0.04), (0.17, 0.08), (0.0, 0.14)], 8, 'ksstain')
    xform(hood_, T(vx, -0.5, 5.3) @ R(PI / 2, 'X')); B.add(hood_)
    for z in (2.9, 3.9, 4.8):
        B.add(box((vx - 0.02, -0.15, z - 0.02), (vx + 0.02, 0.0, z + 0.02), 'ksblack', skip=('+y',)))
    B.feat('front', 'km_soot', a=vx, b=5.1, w=0.45, L=0.9)
    B.feat('front', 'km_rust', pts=[(vx, 2.9), (vx, 3.9), (vx, 4.8)], L=0.5)
    chatsubo(B, (0.15, -0.12, 0.42), 1.0)
    chatsubo(B, (0.62, -0.1, 0.42), 0.8, 'ksjar2')
    chatsubo(B, (-0.1, -0.62, 0.0), 1.25)
    # pent roof (it stops short of the vent), the signboard, upstairs
    hisashi(B, -W / 2 + 0.02, vx - 0.18, 2.72, out=0.82, rise=0.36)
    kanban(B, F, -2.25, 1.85, 3.42, 4.2, 'ks_sg_tea', out=0.11, cap=True)
    up_window(B, F, *up[0], glass='ks_win_b', seed=22)
    up_window(B, F, *up[1], glass='ks_win_a', seed=23, rail=True)
    ac_front(B, F, -0.1, 4.6, w=0.62, h=0.46)
    up_window(B, Rt, 5.0, 6.0, 4.3, 5.3, glass='ks_win_a', seed=24, register=False)
    return top + 0.15


def _nobori(B, x, y, region, top=2.6, cw=0.44, rb=0.23):
    """A nobori: a weighted water base, an aluminium pole, a top bar, the banner (front printed, back plain) in a breeze."""
    q = rb / 0.23
    base, _ = lathe([(0.0, 0.0), (0.21 * q, 0.0), (0.23 * q, 0.03), (0.23 * q, 0.13), (0.19 * q, 0.16), (0.05, 0.18), (0.04, 0.22),
                     (0.0, 0.22)], 10, 'ksbase')
    xform(base, T(x, y, 0.0)); B.add(base)
    B.add(tube([(x, y, 0.18), (x, y, top)], 0.016, 'kmalu', 6))
    kb, _ = lathe([(0.0, 0.0), (0.025, 0.01), (0.02, 0.04), (0.0, 0.05)], 6, 'kmalu')
    xform(kb, T(x, y, top)); B.add(kb)
    zt = top - 0.1
    B.add(tube([(x, y, zt + 0.03), (x + cw + 0.03, y, zt + 0.03)], 0.008, 'kmalu', 4))
    zb = 0.6
    n = 4
    front, back = MB(), MB()
    for i in range(n):
        a = x + 0.03 + cw * i / n; b = x + 0.03 + cw * (i + 1) / n
        wa = 0.025 * math.sin(i * 1.7); wb = 0.025 * math.sin((i + 1) * 1.7)
        uv = (lambda co, a0=x + 0.03: reg_uv(region, (co.x - a0) / cw, (co.z - zb) / (zt - zb), 0.0))
        front.face([(a, y + wa, zb), (b, y + wb, zb), (b, y + wb, zt), (a, y + wa, zt)], 'tex', (0, -1, 0), 1.0, uv)
        back.face([(a, y + wa + 0.003, zb), (a, y + wa + 0.003, zt), (b, y + wb + 0.003, zt), (b, y + wb + 0.003, zb)],
                  'ksnobb' if 'nobori2' not in region else 'ksred', (0, 1, 0), 0.9)
    B.add(front.bm()); B.add(back.bm())


def nobori(B):
    """A shop's nobori banner on its own: 湘南名物 生しらす丼."""
    _nobori(B, -0.11, 0.1, 'ks_nobori', top=2.6, cw=0.38, rb=0.19)
    return 2.65


def balcony(B, x0, x1, z, out=0.75, h=0.95, step=0.11):
    """A small balcony on the upper floor: a concrete slab on two steel brackets, an aluminium railing (top rail, bottom
    rail, close bars)."""
    B.add(cbox2((x0, -out, z - 0.12), (x1, 0.0, z), 0.015, 'conc'))
    for xx in (x0 + 0.25, x1 - 0.25):
        B.add(tube([(xx, -0.02, z - 0.55), (xx, -out + 0.08, z - 0.12)], 0.022, 'ksdark', 4))
    pts = [(x0 + 0.03, -0.03, z + h), (x0 + 0.03, -out + 0.03, z + h), (x1 - 0.03, -out + 0.03, z + h), (x1 - 0.03, -0.03, z + h)]
    B.add(tube(pts, 0.025, 'kmalu', 6))
    B.add(tube([(p[0], p[1], z + 0.06) for p in pts], 0.016, 'kmalu', 4))
    for xx in np.arange(x0 + 0.03, x1 - 0.02, step):
        B.add(tube([(xx, -out + 0.03, z + 0.06), (xx, -out + 0.03, z + h)], 0.01, 'kmalu', 4, caps=False))
    for yy in np.arange(-out + 0.03 + step, -0.05, step):
        for xx in (x0 + 0.03, x1 - 0.03):
            B.add(tube([(xx, yy, z + 0.06), (xx, yy, z + h)], 0.01, 'kmalu', 4, caps=False))
    B.feat('front', 'ao', a0=x0, a1=x1, b=z - 0.12, length=0.5, k=0.45)
    B.feat('front', 'km_rust', pts=[(x0 + 0.25, z - 0.55), (x1 - 0.25, z - 0.55)], L=0.8)


# ================================================================ the kit's rows
def rows(pal):
    """This module's rows of the kit's SPECS (name, W, H, D, roof, builder, pal(...), front-map top, styles, extra maps)."""
    shop = {'wall': 'stucco', 'ppm': 64}
    dark = dict(soffit=(0.30, 0.25, 0.21), trim=(0.30, 0.26, 0.22), pipe=(0.70, 0.71, 0.70), stone=(0.62, 0.61, 0.57),
                conc=(0.74, 0.73, 0.70))

    def pb(W, out=0.9):
        return {'roofb': (-W / 2 - 0.2, W / 2 + 0.2, -out - 0.3, 0.3)}
    R = [
        ('ShopSembeiKM', 7.0, 6.0, 8.0, 1.8, shop_sembei, pal((0.84, 0.79, 0.68), (0.30, 0.24, 0.18), (0.36, 0.38, 0.42), **dark),
         8.3, shop, pb(7.0)),
        ('ShopSobaKM', 7.5, 6.0, 8.0, 1.8, shop_soba, pal((0.80, 0.77, 0.70), (0.20, 0.17, 0.15), (0.33, 0.35, 0.39), **dark),
         8.3, shop, pb(7.5)),
        ('ShopWagashiKM', 6.5, 6.0, 8.0, 1.8, shop_wagashi, pal((0.92, 0.90, 0.85), (0.42, 0.30, 0.20), (0.38, 0.40, 0.44), **dark),
         8.3, shop, pb(6.5)),
        ('ShopSouvenirKM', 8.0, 6.0, 8.0, 1.8, shop_souvenir, pal((0.88, 0.84, 0.74), (0.20, 0.44, 0.32), (0.36, 0.38, 0.42), **dark),
         8.3, shop, {}),
        ('ShopFishKM', 7.0, 6.0, 8.0, 1.5, shop_fish, pal((0.78, 0.78, 0.75), (0.20, 0.36, 0.58), (0.24, 0.26, 0.29), **dark),
         7.9, shop, {}),
        ('ShopKissaKM', 6.5, 6.3, 8.0, 0.0, shop_kissa, pal((0.42, 0.31, 0.24), (0.50, 0.14, 0.12), (0.50, 0.50, 0.50), **dark),
         7.3, shop, {}),
        ('ShopTeaKM', 6.0, 6.0, 8.0, 1.8, shop_tea, pal((0.86, 0.82, 0.72), (0.18, 0.26, 0.20), (0.35, 0.37, 0.41), **dark),
         8.3, shop, pb(6.0)),
        ('NoboriKM', 0.6, 2.6, 0.4, 0.0, nobori, pal((0.85, 0.85, 0.85), (0.14, 0.32, 0.62), (0.5, 0.5, 0.5)), 2.8, {'ppm': 16}, {}),
    ]
    _MINE.update(r[0] for r in R)
    return R
