# Kamakura's houses for the Kamakura kit (kit_buildings_kamakura.py, built by kit_buildings.py --kit Kamakura), in the kit's
# stylized look, after the user's KM1-1 lane pictures (review/kamakura/refs/photo/KM1-1a to KM1-1e in the cancelled branch's
# history, commit f8ff5d1) and the branch's own Kamakura home (KmHome) and beige house (HouseKM here):
#   - HomeOldKM: the old wooden home of KM1-1a, two storeys of dark weathered boards under kawara roofs, the upper floor
#     smaller and set back, the ground floor's own roof round it, a gabled porch over the sliding lattice door;
#   - HouseWoodKM: KM1-1a's other wooden house, two full storeys of dark boards, big aluminium windows, a tiled skirt roof
#     between the floors, a kawara hip roof;
#   - HouseWhiteKM: the newer white house of KM1-1a, a plain rendered box under a single-slope metal roof, a solid-walled
#     balcony, small windows; its carport (CarportKM) is its own model, stood beside it by the street;
#   - RiceShopKM: KM1-1c's rice shop, two storeys of beige render with its gable to the street, a roller shutter and the
#     shop's board (米穀店 お米) over it, the family's door beside;
#   - CarportKM: an aluminium carport, four posts under a curved translucent roof;
#   - FenceBoardKM and FenceBambooKM: 2 m runs of a dark board fence (KM1-1a) and a bamboo fence (KM1-1c and d).
#
# The kit's contract (kit_buildings.py): metres, Z up, the origin at the centre of the front wall's base, the street face
# looking along -Y, parts 1 wall / 2 accent / 3 roof (the street can repaint them within each house's own range).
import math
import numpy as np
from kit_buildings_geo import *
from kit_buildings_parts import *
from kit_buildings_bits import *
from kit_buildings_town import amado
from kit_buildings_cal import hip


def kawara_hip(B, x0, x1, y0, y1, ze, rise, over=0.6):
    """A hip roof of grey kawara over the walls' rectangle (the atlas paints it an even silver-grey: the hip's kawara flag)."""
    top = hip(B, x0, x1, y0, y1, ze, rise, over=over, t=0.13, mat='roof', edge='roofw')
    B.feats['roof'][-1][1]['kawara'] = True
    return top


def kawara_pitched(B, ax, a0, a1, r0, r1, z0, rise, **kw):
    """Tiled slopes (kit_buildings_parts.pitched) painted as kawara: no moss or pale spots on them."""
    pitched(B, ax, a0, a1, r0, r1, z0, rise, **kw)
    if kw.get('feat', True):
        B.feats[kw.get('fmap', 'roof')][-1][1]['kawara'] = True


def battens(B, wf, u0, u1, v0, v1, step=0.9, mat='kmwoodd'):
    """The thin vertical battens that hold a board wall's boards (shitami-bari), every `step` along it."""
    n = max(1, int(round((u1 - u0) / step)))
    for k in range(1, n):
        u = u0 + (u1 - u0) * k / n
        put(B, wf, box((u - 0.025, v0, 0.0), (u + 0.025, v1, 0.035), mat))


def posts(B, pts, v0, v1, s=0.075, mat='kmwoodd'):
    for x, y in pts:
        B.add(box((x - s, y - s, v0), (x + s, y + s, v1), mat))


# ================================================================ HomeOldKM: the old wooden home (KM1-1a, KmHome)
def home_old_km(B):
    """The old wooden home: the ground floor W x D of dark boards with battens on a concrete plinth, under its own kawara
    roof all round; the upper floor smaller and set back over it, its boards with a band of white plaster under the eaves,
    under a kawara hip roof; a gabled porch over the sliding lattice door, a lattice window and an aluminium one on the
    ground floor, two wooden-framed windows above, air-conditioners on the walls, the meter."""
    W, H, D = B.W, B.H, B.D
    F, Rt, Bk, Lf = frames(B)
    c = 0.05
    ph = 0.38
    door_o = (-1.5, 0.3, ph, 2.25)
    lat_o = (-4.0, -2.4, 0.95, 2.05)
    alu_o = (1.1, 3.7, 0.8, 2.15)
    wall(B, F, -W / 2 + c, W / 2 - c, H, [door_o, lat_o, alu_o], ph - 0.04, mode='lap', lap=(0.21, 0.024))
    side = [(1.6, 3.0, 0.95, 2.05), (5.0, 6.2, 0.95, 2.05)]
    wall(B, Rt, c, D - c, H, side, ph - 0.04, mode='lap', lap=(0.21, 0.024))
    wall(B, Lf, -D + c, -c, H, [(-b, -a, z0, z1) for a, b, z0, z1 in side], ph - 0.04, mode='lap', lap=(0.21, 0.024))
    wall(B, Bk, -W / 2 + c, W / 2 - c, H, [(-1.0, 1.0, 0.95, 2.05)], ph - 0.04, mode='lap', lap=(0.21, 0.024))
    box_shell_corners(B, ph - 0.04, H, c)
    for path, closed in ring_path(B, gaps=[(door_o[0], door_o[1])]):
        plinth(B, path, ph, out=0.04, mat='conc', closed=closed)
    battens(B, F, -W / 2, door_o[0], ph, H); battens(B, F, door_o[1], alu_o[0], ph, H); battens(B, F, alu_o[1], W / 2, ph, H)
    # the beam along the top of the ground floor's walls
    string_course(B, u_path(B), H - 0.22, H, out=0.05, mat='kmwoodd')

    # the upper floor, set back: its walls from the ground floor's top
    ux0, ux1, uy0, uy1 = -3.3, 3.3, 1.5, D - 1.1
    H1 = H + 2.75
    FU = WF((0, uy0, 0), (1, 0, 0), 'front')
    RU = WF((ux1, 0, 0), (0, 1, 0), 'right')
    LU = WF((ux0, 0, 0), (0, -1, 0), 'left')
    BU = WF((0, uy1, 0), (-1, 0, 0), 'back')
    plaster = H1 - 0.45
    up_w = [(-2.7, -0.7, H + 1.05, H + 2.15), (0.6, 2.6, H + 1.05, H + 2.15)]
    wall(B, FU, ux0, ux1, H1, up_w, H, mode='lap', lap=(0.21, 0.024), zones=[(ux0, ux1, plaster, H1, 'kmcream')])
    wall(B, RU, uy0, uy1, H1, [(uy0 + 1.2, uy0 + 2.4, H + 1.05, H + 2.1)], H, mode='lap', lap=(0.21, 0.024),
         zones=[(uy0, uy1, plaster, H1, 'kmcream')])
    wall(B, LU, -uy1, -uy0, H1, [], H, mode='lap', lap=(0.21, 0.024), zones=[(-uy1, -uy0, plaster, H1, 'kmcream')])
    wall(B, BU, -ux1, -ux0, H1, [(-1.0, 1.0, H + 1.05, H + 2.1)], H, mode='lap', lap=(0.21, 0.024),
         zones=[(-ux1, -ux0, plaster, H1, 'kmcream')])
    posts(B, [(ux0, uy0), (ux1, uy0), (ux0, uy1), (ux1, uy1)], H, H1, s=0.07)
    battens(B, FU, ux0, up_w[0][0], H, plaster); battens(B, FU, up_w[0][1], up_w[1][0], H, plaster)
    battens(B, FU, up_w[1][1], ux1, H, plaster)
    B.add(box((ux0 - 0.04, uy0 - 0.05, plaster - 0.08), (ux1 + 0.04, uy0, plaster), 'kmwoodd'))

    # the roofs: the ground floor's all round (its middle hidden in the upper floor), then the upper floor's
    kawara_hip(B, -W / 2, W / 2, 0.0, D, H, 1.75, over=0.75)
    top = kawara_hip(B, ux0, ux1, uy0, uy1, H1, 1.45, over=0.65)
    eave_gutter(B, [(-W / 2 - 0.77, -0.77), (W / 2 + 0.77, -0.77)], H + 0.02, size=0.1)
    downpipe(B, [(W / 2 + 0.65, -0.8, H - 0.05), (W / 2 + 0.07, -0.12, H - 0.5), (W / 2 + 0.07, -0.12, 0.3),
                 (W / 2 + 0.2, -0.2, 0.08)], r=0.04, brackets=[(W / 2 + 0.07, -0.12, 1.4)])

    # the porch over the door: two posts, a gable to the street with its tiled roof, the sliding lattice doors
    px0, px1, py0 = door_o[0] - 0.55, door_o[1] + 0.55, -1.05
    posts(B, [(px0 + 0.1, py0 + 0.1), (px1 - 0.1, py0 + 0.1)], 0.0, H - 0.35, s=0.07, mat='kmwood')
    B.add(box((px0, py0, H - 0.5), (px1, py0 + 0.16, H - 0.35), 'kmwood'))
    kawara_pitched(B, 'y', px0 - 0.25, px1 + 0.25, py0 - 0.35, 0.0, H - 0.35, 0.75, barge_mat='kmwoodd', fascia_mat='kmwoodd')
    mb = MB()
    gx = (px0 + px1) / 2
    mb.face([(px0, py0, H - 0.35), (px1, py0, H - 0.35), (gx, py0, H + 0.38)], 'kmwood', (0, -1, 0), 0.95)
    B.add(mb.bm())
    B.add(cbox2((px0 - 0.1, py0 - 0.25, 0.0), (px1 + 0.1, 0.0, 0.16), 0.02, 'kmstone'))
    window(B, F, *door_o, cols=4, head=None, sill=None, frame='kmwoodd', glass='glass1', seed=811, bars=6)
    B.doors.append({'name': 'Door', 'center': [round((door_o[0] + door_o[1]) / 2, 3), -0.1, round((door_o[2] + door_o[3]) / 2, 3)],
                    'size': [round(door_o[1] - door_o[0], 3), round(door_o[3] - door_o[2], 3)], 'wall': 'front'})
    # windows: the lattice one, the aluminium one with its shutter box, the upper floor's wooden-framed sashes
    window(B, F, *lat_o, cols=3, head=None, sill='kmwoodd', frame='kmwoodd', glass='glass0', seed=812, bars=7)
    window(B, F, *alu_o, cols=2, head=None, sill='trimw', frame='alu', glass='glass1', seed=813)
    amado(B, F, alu_o[0], alu_o[1], alu_o[3])
    for k, wo in enumerate(up_w):
        window(B, FU, *wo, cols=4, head=None, sill='kmwoodd', frame='kmwoodd', glass=('glass2', 'glass0')[k], seed=814 + k)
    for wf, ops in ((Rt, side), (Lf, [(-b, -a, z0, z1) for a, b, z0, z1 in side])):
        for k, wo in enumerate(ops):
            window(B, wf, *wo, cols=2, frame='kmwoodd', glass='glass0', seed=820 + k, cheap=True, register=False)
    window(B, RU, uy0 + 1.2, uy0 + 2.4, H + 1.05, H + 2.1, cols=2, frame='kmwoodd', glass='glass0', seed=823, cheap=True, register=False)
    window(B, Bk, -1.0, 1.0, 0.95, 2.05, cols=2, frame='alu', glass='glass0', seed=824, cheap=True, register=False)
    window(B, BU, -1.0, 1.0, H + 1.05, H + 2.1, cols=2, frame='alu', glass='glass0', seed=825, cheap=True, register=False)
    # the air-conditioners (one on the upper floor's front, one on the ground floor's), the meter by the door
    ac_unit(B, FU, -0.05, H + 1.15, z=0.0, w=0.62, h=0.46)
    ac_unit(B, F, 4.22, 0.0, z=0.0, w=0.72, h=0.5, brackets=False)
    meter_box(B, F, 0.75, 1.2, w=0.26, h=0.36)
    return top + 0.1


# ================================================================ HouseWoodKM: the wooden house with big windows (KM1-1a)
def house_wood_km(B):
    """Two full storeys of dark boards with battens, big aluminium sliding windows on both floors (the upper ones behind
    a slim rail), a tiled skirt roof across the front between the floors, a kawara hip roof; the door at the right under
    the skirt roof, the meters, an air-conditioner, gutters."""
    W, H, D = B.W, B.H, B.D
    F, Rt, Bk, Lf = frames(B)
    c = 0.05
    ph = 0.36
    door_o = (2.45, 3.4, ph, 2.3)
    low = [(-3.7, -1.0, 0.75, 2.15), (-0.2, 1.4, 1.2, 2.15)]
    up = [(-3.5, -0.5, 3.45, 4.9), (0.3, 2.9, 3.45, 4.9)]
    wall(B, F, -W / 2 + c, W / 2 - c, H, [door_o] + low + up, ph - 0.04, mode='lap', lap=(0.2, 0.024))
    side = [(1.4, 2.8, 0.95, 2.05), (1.4, 2.8, 3.6, 4.7), (4.6, 5.8, 3.6, 4.7)]
    wall(B, Rt, c, D - c, H, side, ph - 0.04, mode='lap', lap=(0.2, 0.024))
    wall(B, Lf, -D + c, -c, H, [(-b, -a, z0, z1) for a, b, z0, z1 in side], ph - 0.04, mode='lap', lap=(0.2, 0.024))
    wall(B, Bk, -W / 2 + c, W / 2 - c, H, [(-2.4, -0.8, 3.6, 4.7), (0.8, 2.0, 1.0, 2.0)], ph - 0.04, mode='lap', lap=(0.2, 0.024))
    box_shell_corners(B, ph - 0.04, H, c)
    for path, closed in ring_path(B, gaps=[(door_o[0], door_o[1])]):
        plinth(B, path, ph, out=0.04, mat='conc', closed=closed)
    cuts = sorted([(o[0], o[1]) for o in [door_o] + low])
    u = -W / 2
    for a, b in cuts:
        if a - u > 0.6: battens(B, F, u, a, ph, 2.75)
        u = b
    if W / 2 - u > 0.6: battens(B, F, u, W / 2, ph, 2.75)
    string_course(B, u_path(B), 2.75, 2.92, out=0.04, mat='kmwoodd')
    # the skirt roof across the front between the floors, a little round the corners
    kawara_pitched(B, 'x', -0.85, 0.85, -W / 2 - 0.35, W / 2 + 0.35, 2.92, 0.36, slopes=(0,), ridge=False, barge_mat='kmwoodd',
                   fascia_mat='kmwoodd')
    top = kawara_hip(B, -W / 2, W / 2, 0.0, D, H, 1.65, over=0.62)
    eave_gutter(B, [(-W / 2 - 0.64, -0.64), (W / 2 + 0.64, -0.64)], H + 0.02, size=0.1)
    downpipe(B, [(-W / 2 - 0.5, -0.68, H - 0.05), (-W / 2 - 0.07, -0.12, H - 0.5), (-W / 2 - 0.07, -0.12, 0.3),
                 (-W / 2 - 0.2, -0.2, 0.08)], r=0.04, brackets=[(-W / 2 - 0.07, -0.12, 1.4), (-W / 2 - 0.07, -0.12, 3.8)])
    for k, wo in enumerate(low):
        window(B, F, *wo, cols=2, head=None, sill='trimw', frame='alu', glass=('glass1', 'glass0')[k], seed=831 + k, bars=(0, 4)[k])
    amado(B, F, low[0][0], low[0][1], low[0][3])
    for k, wo in enumerate(up):
        window(B, F, *wo, cols=2, head=None, sill='trimw', frame='alu', glass=('glass2', 'glass1')[k], seed=833 + k)
        # the slim aluminium rail across the lower half of a tall window
        x0, x1 = wo[0] - 0.05, wo[1] + 0.05
        B.add(box((x0, -0.16, wo[2] + 0.75), (x1, -0.1, wo[2] + 0.8), 'alu'))
        for x in np.linspace(x0, x1, 2 + int((x1 - x0) / 0.9)):
            B.add(box((float(x) - 0.02, -0.16, wo[2]), (float(x) + 0.02, -0.1, wo[2] + 0.8), 'alu'))
    door(B, F, *door_o, mat='accent', glass=0.5, panels=((1, 1),), casing=False, name='Door')
    steps(B, F, door_o[0] - 0.15, door_o[1] + 0.15, [0.14, 0.28], tread=0.3)
    for wf, ops in ((Rt, side), (Lf, [(-b, -a, z0, z1) for a, b, z0, z1 in side])):
        for k, wo in enumerate(ops):
            window(B, wf, *wo, cols=2, frame='alu', glass='glass0', seed=840 + k, cheap=True, register=False)
    window(B, Bk, -2.4, -0.8, 3.6, 4.7, cols=2, frame='alu', glass='glass0', seed=845, cheap=True, register=False)
    window(B, Bk, 0.8, 2.0, 1.0, 2.0, cols=2, frame='alu', glass='glass0', seed=846, cheap=True, register=False)
    meter_box(B, F, 1.8, 1.15, w=0.28, h=0.4)
    ac_unit(B, F, 1.75, 0.0, z=0.0, w=0.74, h=0.52, brackets=False)
    return top + 0.1


# ================================================================ HouseWhiteKM: the newer white house (KM1-1a)
def house_white_km(B):
    """A plain rendered box of two storeys under a single-slope metal roof rising away from the street, small square
    windows, a balcony with solid white walls on the upper floor, the door under a flat canopy, the meters, an
    air-conditioner; its sides' tops follow the roof."""
    W, H, D = B.W, B.H, B.D
    F, Rt, Bk, Lf = frames(B)
    c = 0.05
    ph = 0.3
    hb = H + 1.25                                  # the walls' top at the back
    door_o = (-2.65, -1.75, ph, 2.3)
    low = [(-1.0, 0.2, 1.1, 2.2), (0.9, 2.6, 0.9, 2.2)]
    up = [(-2.6, -1.7, 3.6, 4.6), (-1.1, -0.55, 3.3, 4.8)]
    wall(B, F, -W / 2 + c, W / 2 - c, H, [door_o] + low + up + [(0.6, 2.7, 3.15, 5.0)], ph - 0.04)
    wall(B, Rt, c, D - c, [(c, H), (D - c, hb)], [(1.6, 2.6, 1.1, 2.1), (4.8, 5.8, 3.6, 4.6)], ph - 0.04)
    wall(B, Lf, -D + c, -c, [(-D + c, hb), (-c, H)], [(-5.8, -4.8, 3.6, 4.6)], ph - 0.04)
    wall(B, Bk, -W / 2 + c, W / 2 - c, hb, [(-1.5, 0.5, 3.6, 4.6), (0.6, 1.8, 1.0, 2.0)], ph - 0.04)
    for x, y, v1 in ((-W / 2, 0, H), (W / 2, 0, H), (-W / 2, D, hb), (W / 2, D, hb)):
        corner_board(B, x, y, ph - 0.04, v1, s=0.06, mat='wall')
    for path, closed in ring_path(B, gaps=[(door_o[0], door_o[1])]):
        plinth(B, path, ph, out=0.03, mat='conc', closed=closed)
    # the single-slope metal roof, a thin fascia round it
    s = (hb - H) / D
    shed(B, -W / 2 - 0.35, W / 2 + 0.35, -0.45, D + 0.3, H + 0.04 - 0.45 * s, hb + 0.04 + 0.3 * s, t=0.1, pitch=0.42, depth=0.035)
    eave_gutter(B, [(-W / 2 - 0.37, -0.47), (W / 2 + 0.37, -0.47)], H, size=0.09)
    downpipe(B, [(W / 2 + 0.25, -0.5, H - 0.05), (W / 2 + 0.07, -0.12, H - 0.4), (W / 2 + 0.07, -0.12, 0.3),
                 (W / 2 + 0.2, -0.2, 0.08)], r=0.04, brackets=[(W / 2 + 0.07, -0.12, 1.4), (W / 2 + 0.07, -0.12, 3.8)])
    # the balcony: solid white walls standing out of the upper floor, a cap, the sliding window behind
    bx0, bx1, by0 = 0.5, 2.8, -0.95
    B.add(cbox2((bx0, by0, 2.85), (bx1, 0.0, 3.0), 0.02, 'wall'))
    B.add(cbox2((bx0, by0, 3.0), (bx1, by0 + 0.12, 4.0), 0.02, 'wall'))
    B.add(cbox2((bx0, by0, 3.0), (bx0 + 0.12, 0.0, 4.0), 0.02, 'wall'))
    B.add(cbox2((bx1 - 0.12, by0, 3.0), (bx1, 0.0, 4.0), 0.02, 'wall'))
    B.add(cbox2((bx0 - 0.02, by0 - 0.02, 4.0), (bx1 + 0.02, 0.0, 4.06), 0.01, 'alu'))
    window(B, F, 0.6, 2.7, 3.15, 5.0, cols=2, head=None, sill=None, frame='alu', glass='glass1', seed=851)
    for k, wo in enumerate(low):
        window(B, F, *wo, cols=(1, 2)[k], head=None, sill='trimw', frame='alu', glass=('glass0', 'glass2')[k], seed=852 + k)
    for k, wo in enumerate(up):
        window(B, F, *wo, cols=1, head=None, sill='trimw', frame='alu', glass=('glass2', 'glass0')[k], seed=854 + k)
    door(B, F, *door_o, mat='accent', glass=None, panels=((1, 1),), casing=False, name='Door')
    B.add(cbox2((door_o[0] - 0.35, -0.85, 2.45), (door_o[1] + 0.35, 0.0, 2.55), 0.02, 'alu'))
    steps(B, F, door_o[0] - 0.2, door_o[1] + 0.2, [0.14], tread=0.4)
    window(B, Rt, 1.6, 2.6, 1.1, 2.1, cols=1, frame='alu', glass='glass0', seed=856, cheap=True, register=False)
    window(B, Rt, 4.8, 5.8, 3.6, 4.6, cols=1, frame='alu', glass='glass0', seed=857, cheap=True, register=False)
    window(B, Lf, -5.8, -4.8, 3.6, 4.6, cols=1, frame='alu', glass='glass0', seed=858, cheap=True, register=False)
    window(B, Bk, -1.5, 0.5, 3.6, 4.6, cols=2, frame='alu', glass='glass0', seed=859, cheap=True, register=False)
    window(B, Bk, 0.6, 1.8, 1.0, 2.0, cols=1, frame='alu', glass='glass0', seed=860, cheap=True, register=False)
    meter_box(B, F, -0.4, 0.75, w=0.26, h=0.36)
    ac_unit(B, Rt, 3.4, 0.0, z=0.0, w=0.74, h=0.52, brackets=False)
    return hb + 0.4


# ================================================================ RiceShopKM: the rice shop (KM1-1c)
def rice_shop_km(B):
    """Two storeys of beige render with its gable to the street under kawara, a roller shutter across most of the ground
    floor with its box above and the shop's board over that (米穀店 お米), the family's aluminium door beside it, two
    aluminium windows with shutter boxes upstairs, a small one in the gable, the meter and an air-conditioner."""
    W, H, D = B.W, B.H, B.D
    F, Rt, Bk, Lf = frames(B)
    c = 0.05
    ph = 0.12
    rise = 1.55
    e = rise * 0.35 / (W / 2 + 0.35)             # the roof's underside over the side walls, above the eaves
    apex = H + rise - 0.05
    shutter = (-3.0, 1.2, ph, 2.55)
    door_o = (1.75, 2.75, ph, 2.3)
    up = [(-2.6, -0.6, 3.6, 4.9), (0.6, 2.6, 3.6, 4.9)]
    gable_w = (-0.45, 0.45, H + 0.15, H + 0.85)
    wall(B, F, -W / 2 + c, W / 2 - c, [(-W / 2 + c, H + e), (0.0, apex), (W / 2 - c, H + e)], [shutter, door_o] + up + [gable_w], ph,
         zones=[(-W / 2 + c, W / 2 - c, 2.62, 3.32, 'trim')])
    side = [(2.0, 3.2, 3.6, 4.7), (5.0, 6.2, 3.6, 4.7)]
    wall(B, Rt, c, D - c, H + e, side, ph)
    wall(B, Lf, -D + c, -c, H + e, [(-b, -a, z0, z1) for a, b, z0, z1 in side], ph, mode='rib', mat='galv')
    wall(B, Bk, -W / 2 + c, W / 2 - c, [(-W / 2 + c, H + e), (0.0, apex), (W / 2 - c, H + e)], [(-1.0, 1.0, 3.6, 4.6)], ph)
    box_shell_corners(B, ph, H + e, c)
    kawara_pitched(B, 'y', -W / 2 - 0.35, W / 2 + 0.35, -0.35, D + 0.3, H, rise, barge_mat='trim', fascia_mat='trim')
    eave_gutter(B, [(-W / 2 - 0.37, -0.35), (-W / 2 - 0.37, D + 0.3)], H, size=0.09)
    # the roller shutter: horizontal slats in the opening, its box above, the board over that
    sx0, sx1 = shutter[0], shutter[1]
    sh = WF((0, 0.1, 0), (1, 0, 0), 'front')
    wall(B, sh, sx0, sx1, shutter[3], [], shutter[2], mode='lap', lap=(0.09, 0.012), mat='kmgrey')
    B.add(cbox2((sx0 - 0.1, -0.22, shutter[3]), (sx1 + 0.1, 0.0, shutter[3] + 0.3), 0.03, 'kmgrey'))
    for x in (sx0 - 0.04, sx1 + 0.04):
        B.add(box((x - 0.04, -0.06, ph), (x + 0.04, 0.0, shutter[3]), 'kmgreyd'))
    bx0, bx1, bz0, bz1 = sx0 + 0.2, sx1 - 0.2, 2.95, 3.5
    B.add(cbox2((bx0 - 0.06, -0.12, bz0 - 0.06), (bx1 + 0.06, -0.02, bz1 + 0.06), 0.01, 'kmwoodd'))
    face = [(bx0, -0.125, bz0), (bx1, -0.125, bz0), (bx1, -0.125, bz1), (bx0, -0.125, bz1)]
    mb = MB()
    mb.face(face, 'tex', (0, -1, 0), 1.0, lambda co: reg_uv('km_rice', (co.x - bx0) / (bx1 - bx0), (co.z - bz0) / (bz1 - bz0), 0.0))
    B.add(mb.bm())
    door(B, F, *door_o, mat='alu', glass=0.75, panels=((1, 1),), casing=False, name='Door')
    for k, wo in enumerate(up):
        window(B, F, *wo, cols=2, head=None, sill='trimw', frame='alu', glass=('glass0', 'glass2')[k], seed=861 + k)
        amado(B, F, wo[0], wo[1], wo[3])
    window(B, F, *gable_w, cols=1, head=None, sill='trimw', frame='alu', glass='glass0', seed=863, bars=3)
    for k, wo in enumerate(side):
        window(B, Rt, *wo, cols=2, frame='alu', glass='glass0', seed=864 + k, cheap=True, register=False)
    window(B, Bk, -1.0, 1.0, 3.6, 4.6, cols=2, frame='alu', glass='glass0', seed=866, cheap=True, register=False)
    meter_box(B, F, 1.45, 1.35, w=0.26, h=0.36)
    ac_unit(B, F, 2.25, 2.6, z=0.0, w=0.7, h=0.48)
    return apex + 0.3


# ================================================================ CarportKM, the fences
def carport_km(B):
    """An aluminium carport: four posts, a beam along each side, a gently curved translucent roof (seen from the street
    as a thin sheet over the car's space)."""
    W, D = B.W, B.D
    h = 2.3
    for x in (-W / 2 + 0.1, W / 2 - 0.1):
        for y in (0.3, D - 0.3):
            B.add(cbox2((x - 0.05, y - 0.05, 0.0), (x + 0.05, y + 0.05, h), 0.01, 'alu'))
        B.add(cbox2((x - 0.06, 0.05, h - 0.12), (x + 0.06, D - 0.05, h + 0.02), 0.01, 'alu'))
    prof = [(-W / 2 - 0.2, h + 0.02), (-W / 4, h + 0.16), (0.0, h + 0.2), (W / 4, h + 0.16), (W / 2 + 0.2, h + 0.02)]
    mb = MB()
    for (xa, za), (xb, zb) in zip(prof[:-1], prof[1:]):
        mb.face([(xa, -0.1, za), (xb, -0.1, zb), (xb, D + 0.1, zb), (xa, D + 0.1, za)], 'kmpoly', (0, 0, 1), 1.0)
        mb.face([(xa, D + 0.1, za - 0.02), (xb, D + 0.1, zb - 0.02), (xb, -0.1, zb - 0.02), (xa, -0.1, za - 0.02)], 'alu', (0, 0, -1), 0.8)
    B.add(mb.bm())
    B.add(cbox2((-W / 2 - 0.2, -0.14, h - 0.02), (W / 2 + 0.2, -0.06, h + 0.06), 0.01, 'alu'))
    return h + 0.3


def fence_board_km(B):
    """2 m of dark board fence (KM1-1a): a post at each end, the boards painted on a slab (the km_boards tile), a cap."""
    W, H = B.W, B.H
    mb = cbox2((-W / 2, 0.0, 0.0), (W / 2, 0.06, H - 0.06), 0.01, 'kmwoodd')
    fs = faces_facing(mb, (0, -1, 0), 0.9) + faces_facing(mb, (0, 1, 0), 0.9)
    setmat(mb, 'tex', fs)
    uv_box(mb, fs, 'km_boards', 0.0)
    B.add(mb)
    for x in (-W / 2 + 0.06, W / 2 - 0.06):
        B.add(cbox2((x - 0.06, -0.03, 0.0), (x + 0.06, 0.09, H), 0.01, 'kmwoodd'))
    B.add(cbox2((-W / 2, -0.04, H - 0.07), (W / 2, 0.1, H), 0.01, 'kmwoodd'))
    return H + 0.05


def fence_bamboo_km(B):
    """2 m of bamboo fence (KM1-1c, d): the canes painted on a slab (the km_bamboo tile), three dark rails each side, a
    post at each end, a split-bamboo cap."""
    W, H = B.W, B.H
    mb = cbox2((-W / 2, 0.0, 0.05), (W / 2, 0.05, H - 0.05), 0.01, 'kmbamboo')
    fs = faces_facing(mb, (0, -1, 0), 0.9) + faces_facing(mb, (0, 1, 0), 0.9)
    setmat(mb, 'tex', fs)
    uv_box(mb, fs, 'km_bamboo', 0.0)
    B.add(mb)
    for z in (0.3, H * 0.55, H - 0.25):
        for y0, y1 in ((-0.04, 0.0), (0.05, 0.09)):
            B.add(box((-W / 2, y0, z - 0.03), (W / 2, y1, z + 0.03), 'kmwoodd'))
    for x in (-W / 2 + 0.05, W / 2 - 0.05):
        B.add(tube([(x, 0.025, 0.0), (x, 0.025, H + 0.05)], 0.045, 'kmbamboo', 8))
    B.add(tube([(-W / 2, 0.025, H), (W / 2, 0.025, H)], 0.05, 'kmbamboo', 8))
    return H + 0.1


# ================================================================ the tiles
def t_boards(dr, w, h, k, _c):
    """Dark weathered boards, upright, each its own tone, with dark joints."""
    rng = np.random.default_rng(5)
    n = 14
    bw = w / n
    for i in range(n):
        t = rng.uniform(-0.04, 0.04)
        col = (0.30 + t, 0.22 + t * 0.8, 0.17 + t * 0.6)
        dr.rectangle([i * bw, 0, (i + 1) * bw, h], fill=_c(col))
        for _ in range(3):
            y = rng.uniform(0, h)
            dr.line([(i * bw + bw * 0.2, y), (i * bw + bw * 0.8, y + rng.uniform(-h * 0.02, h * 0.02))], fill=_c((0.26 + t, 0.19 + t, 0.15 + t)), width=max(1, int(k)))
        dr.rectangle([i * bw, 0, i * bw + max(1, 2 * k), h], fill=_c((0.14, 0.11, 0.09)))


def t_bamboo(dr, w, h, k, _c):
    """Bamboo canes side by side, upright, their nodes in staggered rows, straw-gold with green-grey and brown ones."""
    rng = np.random.default_rng(9)
    n = 22
    cw = w / n
    for i in range(n):
        t = rng.uniform(-0.05, 0.05)
        col = (0.80 + t, 0.70 + t, 0.45 + t * 0.6) if rng.random() > 0.2 else (0.68 + t, 0.62 + t, 0.40 + t)
        x0, x1 = i * cw, (i + 1) * cw
        dr.rectangle([x0, 0, x1, h], fill=_c(col))
        dr.rectangle([x0 + cw * 0.15, 0, x0 + cw * 0.35, h], fill=_c(tuple(min(1.0, v * 1.12) for v in col)))
        dr.rectangle([x1 - max(1, 2 * k), 0, x1, h], fill=_c(tuple(v * 0.6 for v in col)))
        y = rng.uniform(0, h * 0.3)
        while y < h:
            dr.rectangle([x0, y, x1, y + max(1, 3 * k)], fill=_c(tuple(v * 0.72 for v in col)))
            y += h * rng.uniform(0.28, 0.36)


def t_rice(dr, w, h, k, _c, label, kana, bold):
    """The rice shop's board: 米穀店 small at the left, お米 large, on a cream board with a dark edge."""
    dr.rectangle([0, 0, w, h], fill=_c((0.95, 0.92, 0.84)))
    dr.rectangle([0, 0, w, h], outline=_c((0.25, 0.18, 0.14)), width=max(2, int(5 * k)))
    label(dr, w * 0.36, h, '米穀店', kana, 0.42, (0.15, 0.12, 0.1), cx=0.55, cy=0.5)
    label(dr, w, h, 'お米', kana, 0.78, (0.12, 0.09, 0.08), cx=0.66, cy=0.5)
