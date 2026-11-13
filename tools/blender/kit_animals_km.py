# Kamakura's animals (docs/KAMAKURA_BUILD.md, "The sheets' assets, by id": KM-N01 to N28), from the user's photographic
# sheets KM-P4 and KM-P8. Each animal is a relief shaped from its outline in one view of the sheet, round in section: a
# limb of half-width R is sqrt(d (2R - d)) deep at d from its edge, so a tail is as deep as it is wide, and a body is
# capped softly at its real half-depth; the faces meet at the outline (depth 0 there). The photo is projected onto both
# faces, so straight on it is the photo exactly and turned it has a body; its back face reads as the other flank when
# the game turns the animal round. Each moving part is its own mesh with its origin at its pivot, under an empty root
# named after the model, as the animals kit's rig contract has it (kit_animals.py): a cat's, squirrel's or dog's Tail
# (World/WallCat, World/TreeSquirrel, Hazards/Dog), a standing bird's Head (World/GroundBird), the Shiba's Head and legs
# (Hazards/Dog), a small bird's or an insect's WingL and WingR (GroundBird's flying model, World/FlitButterfly).
# Built here: every animal the game sees side-on, sitting, standing or perched, the small birds in flight and the
# insects. The large birds in flight wait for their four-view sheets (BASE KM-S1, docs/KAMAKURA_BUILD.md Step 4b); the
# frog, the snail, the crab and the starfish sit on photo backgrounds on KM-P8 and need their own cut-outs.
#   blenv/bin/python kit_animals_km.py -- /abs/outdir [--board /abs/board.jpg] [--only KmCatSitting,KmCrowStanding]
#                                        [--cuts /abs/cuts.jpg]
# Writes into outdir: <Model>.fbx per model, KamakuraAnimalsAtlas.png, KamakuraAnimals.json, KamakuraAnimals.blend.
# --cuts writes a sheet of every model's outline with its parts coloured (to check the cuts).
import json
import math
import os
import sys

import bpy
import bmesh
import cv2
import numpy as np
from mathutils import Vector, Euler
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_lib as K
import kit_buildings_km as KB      # its Atlas, the unlit and cut-out review materials, the board's render

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = ARGS[0] if ARGS and not ARGS[0].startswith('--') else os.path.abspath('out_km_animals')
BOARD = ARGS[ARGS.index('--board') + 1] if '--board' in ARGS else None
CUTS = ARGS[ARGS.index('--cuts') + 1] if '--cuts' in ARGS else None
ONLY = set(ARGS[ARGS.index('--only') + 1].split(',')) if '--only' in ARGS else None
REFS = KB.REFS
P4, P8 = 'KM-P4_animals_sheet.png', 'KM-P8_more_animals.png'


def A(cid, sheet, box, view, size, depth, parts=(), refine=False, wings=None, exclude=(), empties=(), step=None,
      thresh=42):
    """One model: its catalogue id (KM-Nxx), sheet, the figure's box (sheet px), its view (side: head to the right,
    standing on its lowest pixel; below: a flyer seen from beneath, head up; above: lying flat, seen from above), its
    size (('w' or 'h', metres) of the figure's outline), its half-depth cap (m), its parts ((name, polygon in sheet px,
    pivot)), refine (GrabCut for colours near the sheet's grey), wings (the body's half-width as a share of the
    figure's width, to split WingL and WingR off a flyer), exclude (polygons left out: a perch wire), empties (extra
    pivots the rig wants with no mesh of their own: (name, pivot)), thresh (how far from the grey a pixel must be to
    count as the figure: lower for see-through wings)."""
    return dict(id=cid, sheet=sheet, box=box, view=view, size=size, depth=depth, parts=list(parts), refine=refine,
                wings=wings, exclude=list(exclude), empties=list(empties), step=step, thresh=thresh)


ANIMALS = {
    # ---------------------------------------------------------------- KM-P4
    'KmCatSitting': A('KM-N01', P4, (500, 18, 858, 284), 'side', ('h', 0.38), 0.075,
                      [('Tail', [(500, 228), (656, 228), (656, 284), (500, 284)], (648, 262))]),
    'KmCatWalking': A('KM-N01', P4, (21, 44, 443, 280), 'side', ('h', 0.30), 0.06,
                      [('Tail', [(21, 113), (112, 113), (102, 166), (66, 214), (21, 214)], (106, 137))]),
    'KmTanukiWalking': A('KM-N02', P4, (1409, 50, 1838, 281), 'side', ('h', 0.36), 0.09,
                         [('Tail', [(1409, 83), (1497, 91), (1497, 194), (1490, 256), (1409, 256)], (1494, 128))],
                         refine=True),
    'KmTanukiSitting': A('KM-N02', P4, (1898, 31, 2280, 282), 'side', ('h', 0.40), 0.09,
                         [('Tail', [(1898, 204), (2034, 204), (2034, 273), (1898, 273)], (2034, 237))], refine=True),
    'KmSquirrelRunning': A('KM-N03', P4, (11, 374, 450, 562), 'side', ('w', 0.40), 0.04,
                           [('Tail', [(11, 374), (148, 374), (144, 488), (11, 496)], (144, 450))]),
    'KmSquirrelSitting': A('KM-N03', P4, (523, 322, 837, 606), 'side', ('h', 0.30), 0.045,
                           [('Tail', [(523, 322), (676, 322), (676, 405), (652, 440), (652, 612), (523, 612)], (650, 594))]),
    'KmShibaStanding': A('KM-N04', P4, (1474, 314, 1808, 605), 'side', ('h', 0.58), 0.09,
                         [('Tail', [(1493, 340), (1586, 340), (1588, 420), (1493, 426)], (1570, 420)),
                          ('Head', [(1705, 314), (1808, 314), (1808, 433), (1728, 433)], (1734, 426)),
                          ('LegFL', [(1673, 507), (1763, 507), (1763, 622), (1673, 622)], (1718, 510)),
                          ('LegBL', [(1493, 500), (1602, 500), (1602, 622), (1493, 622)], (1557, 503))],
                         empties=[('LegFR', (1718, 510)), ('LegBR', (1557, 503))]),
    'KmShibaSitting': A('KM-N04', P4, (1940, 317, 2235, 601), 'side', ('h', 0.62), 0.09,
                        [('Tail', [(1940, 499), (2000, 499), (2000, 601), (1940, 601)], (1997, 550))]),
    'KmKitePerched': A('KM-N05', P4, (89, 625, 358, 931), 'side', ('h', 0.75), 0.07,
                       [('Head', [(278, 625), (360, 625), (360, 700), (290, 712)], (290, 690))]),
    'KmCrowStanding': A('KM-N06', P4, (1426, 638, 1788, 919), 'side', ('w', 0.57), 0.06,
                        [('Head', [(1649, 638), (1781, 638), (1781, 722), (1677, 760)], (1663, 722))]),
    'KmCrowHopping': A('KM-N06', P4, (1882, 659, 2272, 910), 'side', ('w', 0.57), 0.06,
                       [('Head', [(2156, 659), (2272, 659), (2272, 733), (2178, 742)], (2170, 720))]),
    'KmPigeonStanding': A('KM-N07', P4, (76, 942, 359, 1218), 'side', ('w', 0.30), 0.05,
                          [('Head', [(269, 942), (356, 942), (356, 1013), (283, 1035)], (291, 1024))], refine=True),
    'KmPigeonPecking': A('KM-N07', P4, (491, 1027, 847, 1203), 'side', ('w', 0.34), 0.05,
                         [('Head', [(778, 1068), (840, 1068), (840, 1171), (772, 1171)], (789, 1089))], refine=True),
    'KmSparrowPerched': A('KM-N08', P4, (1443, 961, 1755, 1213), 'side', ('w', 0.15), 0.025,
                          [('Head', [(1641, 961), (1749, 961), (1749, 1063), (1650, 1075)], (1665, 1063))], refine=True),
    'KmSparrowHopping': A('KM-N08', P4, (1898, 979, 2235, 1213), 'side', ('w', 0.15), 0.025,
                          [('Head', [(2122, 979), (2229, 979), (2229, 1083), (2135, 1092)], (2144, 1076))], refine=True),
    'KmSparrowFlying': A('KM-N08', P4, (2359, 958, 2696, 1201), 'below', ('w', 0.21), 0.02, wings=0.09, refine=True),
    'KmSwallowPerched': A('KM-N09', P4, (0, 1255, 466, 1525), 'side', ('h', 0.22), 0.02,
                          exclude=[[(0, 1350), (122, 1365), (122, 1415), (0, 1400)],
                                   [(325, 1398), (466, 1412), (466, 1450), (325, 1435)]]),
    'KmSwallowFlying': A('KM-N09', P4, (466, 1265, 908, 1526), 'below', ('w', 0.33), 0.015, wings=0.07),
    'KmGullStanding': A('KM-N10', P4, (960, 1255, 1296, 1527), 'side', ('h', 0.34), 0.06,
                        [('Head', [(1173, 1255), (1290, 1255), (1290, 1352), (1189, 1375)], (1199, 1358))],
                        refine=True),
    'KmEgretStanding': A('KM-N11', P4, (1939, 1238, 2225, 1535), 'side', ('h', 0.55), 0.05,
                         [('Head', [(2110, 1238), (2222, 1238), (2222, 1292), (2122, 1301)], (2127, 1292))]),
    # ---------------------------------------------------------------- KM-P8
    'KmKoiRedWhite': A('KM-N12', P8, (21, 60, 428, 238), 'above', ('w', 0.60), 0.06),
    'KmKoiRedWhiteTurning': A('KM-N12', P8, (505, 48, 874, 238), 'above', ('w', 0.52), 0.06),
    'KmKoiGold': A('KM-N13', P8, (952, 68, 1355, 238), 'above', ('w', 0.55), 0.06),
    'KmKoiGoldTurning': A('KM-N13', P8, (1408, 44, 1807, 256), 'above', ('w', 0.48), 0.06),
    'KmTurtleBasking': A('KM-N14', P8, (1867, 66, 2255, 237), 'side', ('w', 0.36), 0.05, refine=True),
    'KmTurtleSwimming': A('KM-N14', P8, (2327, 16, 2715, 274), 'above', ('w', 0.33), 0.035, refine=True),
    'KmHeronStanding': A('KM-N15', P8, (101, 303, 366, 609), 'side', ('h', 0.90), 0.07,
                         [('Head', [(219, 303), (363, 303), (363, 362), (228, 371)], (278, 359))], refine=True),
    'KmCormorantStanding': A('KM-N16', P8, (1011, 317, 1279, 604), 'side', ('h', 0.85), 0.07,
                             [('Head', [(1160, 317), (1273, 317), (1273, 369), (1168, 378)], (1177, 369))], refine=True),
    'KmCormorantDrying': A('KM-N16', P8, (1390, 323, 1822, 602), 'side', ('w', 0.95), 0.07, refine=True),
    'KmWagtail': A('KM-N17', P8, (2316, 345, 2684, 582), 'side', ('w', 0.21), 0.02,
                   [('Head', [(2550, 345), (2677, 345), (2677, 412), (2560, 423)], (2571, 412))], refine=True),
    'KmWhiteEyePerched': A('KM-N18', P8, (66, 651, 366, 932), 'side', ('w', 0.13), 0.015,
                           [('Head', [(265, 651), (360, 651), (360, 749), (277, 761)], (285, 743))]),
    'KmWhiteEyeFlying': A('KM-N18', P8, (509, 639, 863, 891), 'below', ('w', 0.18), 0.012, wings=0.08),
    'KmBulbulPerched': A('KM-N19', P8, (972, 640, 1277, 912), 'side', ('w', 0.28), 0.025,
                         [('Head', [(1148, 640), (1271, 640), (1271, 740), (1160, 751)], (1171, 734))], refine=True),
    'KmBulbulFlying': A('KM-N19', P8, (1406, 626, 1806, 907), 'below', ('w', 0.40), 0.02, wings=0.07, refine=True),
    'KmDoveStanding': A('KM-N20', P8, (1863, 647, 2225, 905), 'side', ('w', 0.33), 0.05,
                        [('Head', [(2142, 647), (2222, 647), (2222, 727), (2135, 738)], (2155, 724))], refine=True),
    'KmDoveFlying': A('KM-N20', P8, (2314, 646, 2731, 900), 'below', ('w', 0.53), 0.025, wings=0.08, refine=True),
    'KmCalicoWalking': A('KM-N21', P8, (12, 936, 438, 1220), 'side', ('h', 0.30), 0.06,
                         [('Tail', [(12, 993), (102, 993), (98, 1047), (61, 1059), (12, 1059)], (94, 1022))], refine=True),
    'KmCalicoAsleep': A('KM-N21', P8, (967, 965, 1337, 1206), 'side', ('w', 0.42), 0.09, refine=True),
    'KmTuxedoWalking': A('KM-N22', P8, (1392, 969, 1801, 1216), 'side', ('h', 0.30), 0.06,
                         [('Tail', [(1392, 1012), (1479, 1012), (1479, 1063), (1423, 1166), (1392, 1166)], (1471, 1048))], refine=True),
    'KmTuxedoSitting': A('KM-N22', P8, (1872, 936, 2218, 1220), 'side', ('h', 0.38), 0.075,
                         [('Tail', [(1872, 1149), (2002, 1149), (2002, 1209), (1872, 1209)], (2002, 1179))], refine=True),
    'KmTuxedoLying': A('KM-N22', P8, (2308, 995, 2724, 1172), 'side', ('w', 0.60), 0.075,
                       [('Tail', [(2308, 1071), (2404, 1071), (2404, 1113), (2308, 1113)], (2400, 1095))], refine=True),
    'KmSwallowtail': A('KM-N25', P8, (961, 1248, 1334, 1531), 'above', ('w', 0.10), 0.003, wings=0.025),
    'KmDragonfly': A('KM-N26', P8, (1398, 1255, 1814, 1524), 'above', ('w', 0.07), 0.002, wings=0.025, thresh=14),
}


def figure_mask(sheet, spec):
    """The figure in its box: what differs from the sheet's grey, its holes filled, the largest piece. The soft neutral
    shadow under a figure on the ground is left out (darker than the grey, no colour of its own, in the lowest eighth of
    the box only: higher up, a grey bird's own feathers look the same). With refine, GrabCut finds the parts close to
    the sheet's grey (a kite's pale tail, a grey pigeon or heron)."""
    a = np.asarray(sheet.convert('RGB')).astype(np.int32)
    x0, y0, x1, y1 = spec['box']
    r = a[y0:y1, x0:x1]
    border = np.concatenate([r[:4].reshape(-1, 3), r[-4:].reshape(-1, 3), r[:, :4].reshape(-1, 3), r[:, -4:].reshape(-1, 3)])
    bg = np.median(border, 0)
    m = (np.abs(r - bg).sum(-1) > spec['thresh']).astype(np.uint8)
    shadow = np.zeros(m.shape, bool)
    if spec['view'] == 'side':
        lum = r.mean(-1)
        chroma = r.max(-1) - r.min(-1)
        low = np.zeros(m.shape, bool)
        low[int(m.shape[0] * 0.87):] = True
        shadow = low & (chroma < 14) & (lum < bg.mean() - 2) & (lum > bg.mean() - 45)
        m[shadow] = 0
    for poly in spec['exclude']:
        cv2.fillPoly(m, [np.array([(x - x0, y - y0) for x, y in poly], np.int32)], 0)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    m = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8)
    if spec['refine']:
        gc = np.full(m.shape, cv2.GC_PR_BGD, np.uint8)
        hull = cv2.convexHull(cv2.findNonZero(m))
        cv2.fillConvexPoly(gc, hull, cv2.GC_PR_FGD)
        gc[cv2.erode(m, np.ones((5, 5), np.uint8)) > 0] = cv2.GC_FGD
        gc[:3], gc[-3:], gc[:, :3], gc[:, -3:] = cv2.GC_BGD, cv2.GC_BGD, cv2.GC_BGD, cv2.GC_BGD
        for poly in spec['exclude']:
            cv2.fillPoly(gc, [np.array([(x - x0, y - y0) for x, y in poly], np.int32)], cv2.GC_BGD)
        gc[shadow & (gc != cv2.GC_FGD)] = cv2.GC_BGD
        cv2.grabCut(np.ascontiguousarray(r.astype(np.uint8)[:, :, ::-1]), gc, None, np.zeros((1, 65)), np.zeros((1, 65)),
                    6, cv2.GC_INIT_WITH_MASK)
        m = ((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
        m = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8)
    # holes: filled when under 1 % of the box (a kite's grey-brown feather patches), or when they are not the sheet's
    # grey (a dark shell's middle); a larger gap of the sheet's own grey (between a squirrel's tail and back) stays open
    inv = (1 - m).astype(np.uint8)
    hn, hl, hs, _ = cv2.connectedComponentsWithStats(inv, 4)
    for i in range(1, hn):
        x, y, w, h, area = hs[i]
        if x > 0 and y > 0 and x + w < m.shape[1] and y + h < m.shape[0]:
            hole = hl == i
            if area < m.size * 0.01 or np.abs(r[hole].mean(0) - bg).sum() > 30:
                m[hole] = 1
    return m


def part_masks(spec, mask):
    """Each part's pixels ({name: mask}, pivot {name: (x, y)} in sheet px): the polygon parts, the wings of a flyer, and
    the Body (the rest). A flyer's wings are what lies beyond the body's half-width either side of its middle, above the
    lowest point the wings reach."""
    x0, y0, x1, y1 = spec['box']
    h, w = mask.shape
    parts, pivots = {}, {}
    taken = np.zeros_like(mask)
    for name, poly, pivot in spec['parts']:
        pm = np.zeros_like(mask)
        cv2.fillPoly(pm, [np.array([(x - x0, y - y0) for x, y in poly], np.int32)], 1)
        pm &= mask & (1 - taken)
        parts[name], pivots[name] = pm, pivot
        taken |= pm
    if spec['wings']:
        ys, xs = np.nonzero(mask)
        cx = xs.mean()
        bw = spec['wings'] * w
        xx = np.arange(w)[None, :].repeat(h, 0)
        far = np.abs(xx - cx) > 2.2 * bw
        wing_bottom = np.nonzero((mask & far).any(1))[0].max() + 2 if spec['view'] == 'below' else h
        beyond = (np.abs(xx - cx) > bw) & (np.arange(h)[:, None] < wing_bottom)
        rows = np.nonzero((mask & far).any(1))[0]
        shoulder = y0 + int(rows.min() + 0.3 * (rows.max() - rows.min()))
        for name, side in (('WingR', xx < cx), ('WingL', xx >= cx)):
            pm = (mask & beyond & side & (1 - taken)).astype(np.uint8)
            parts[name] = pm
            pivots[name] = (x0 + cx + (bw if name == 'WingL' else -bw), shoulder)
            taken |= pm
    parts['Body'] = (mask & (1 - taken)).astype(np.uint8)
    pivots['Body'] = None
    return parts, pivots


def relief(mask, step):
    """A triangulation of the mask: points along its outline every 5 px and inside it every step px, Delaunay, the
    triangles inside the mask kept. Returns the points (px, in the mask's frame), the triangles, each point's distance
    from the outline, and the local half-width there (the largest distance from the outline nearby: the radius of the
    limb the point is on)."""
    h, w = mask.shape
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    pts = []
    for c in cs:
        c = c[:, 0, :].astype(np.float32)
        L = np.r_[0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]
        for s in np.arange(0, L[-1], 5.0):
            i = min(np.searchsorted(L, s), len(c) - 1)
            pts.append((float(c[i][0]), float(c[i][1])))
    for y in np.arange(step / 2, h, step):
        for x in np.arange(step / 2 + (step / 2 if int(y / step) % 2 else 0), w, step):
            if dist[int(y), int(x)] > step * 0.45:
                pts.append((float(x), float(y)))
    sub = cv2.Subdiv2D((0, 0, w + 1, h + 1))
    uniq = {}
    for p in pts:
        key = (round(p[0], 1), round(p[1], 1))
        if key not in uniq:
            uniq[key] = len(uniq)
            sub.insert(key)
    keys = list(uniq)
    tris = []
    for t in sub.getTriangleList():
        a, b, c = (round(t[0], 1), round(t[1], 1)), (round(t[2], 1), round(t[3], 1)), (round(t[4], 1), round(t[5], 1))
        if a not in uniq or b not in uniq or c not in uniq:
            continue
        cx, cy = (a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3
        if 0 <= int(cy) < h and 0 <= int(cx) < w and mask[int(cy), int(cx)]:
            tris.append((uniq[a], uniq[b], uniq[c]))
    d = np.array([dist[min(int(round(k[1])), h - 1), min(int(round(k[0])), w - 1)] for k in keys], np.float32)
    # the local half-width: the distance field's largest value within a few half-widths, so a tail's points see the
    # tail's own radius, not the body's
    local = dist.copy()
    for k in (9, 17, 33):
        grown = cv2.dilate(dist, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        local = np.where(dist > k / 4.0, grown, local)
    local = np.maximum(cv2.dilate(dist, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))), local)
    r = np.array([local[min(int(round(k[1])), h - 1), min(int(round(k[0])), w - 1)] for k in keys], np.float32)
    return np.array(keys, np.float32), tris, d, r


def build(name, spec, atlas, sheet):
    x0, y0, x1, y1 = spec['box']
    mask = figure_mask(sheet, spec)
    ys, xs = np.nonzero(mask)
    fw, fh = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
    s = (fw if spec['size'][0] == 'w' else fh) / spec['size'][1]           # sheet px to the metre
    if spec['view'] == 'side':      # on the ground (or its perch) at its lowest pixel, under its middle
        bottom = ys.max()
        ox, oy = x0 + xs[ys > bottom - 0.08 * fh].mean(), y0 + bottom
    else:
        ox, oy = x0 + xs.mean(), y0 + ys.mean()
    rgb = np.ascontiguousarray(np.asarray(sheet.convert('RGB'))[y0:y1, x0:x1])
    # the figure's own colours carried outward past its outline (the sheet's grey there would show as a seam where the
    # two faces meet, and as a halo at the edge)
    inner = cv2.erode(mask, np.ones((3, 3), np.uint8))
    rgb = cv2.inpaint(rgb, (1 - inner).astype(np.uint8), 4, cv2.INPAINT_TELEA)
    alpha = cv2.dilate(mask, np.ones((3, 3), np.uint8)) * 255
    pos = atlas.place(Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8), 'RGBA'))
    step = spec['step'] or max(6, int(round(min(fw, fh) / 18)))
    view = spec['view']

    def to_model(gx, gy):
        """Sheet px to model metres (z = 0): side: head +X, up +Z; below: head +X, beneath -Z; above: head +X (as on
        the sheet), the far side +Y."""
        if view == 'side':
            return Vector(((gx - ox) / s, 0.0, (oy - gy) / s))
        if view == 'below':
            return Vector(((oy - gy) / s, (gx - ox) / s, 0.0))
        return Vector(((gx - ox) / s, (oy - gy) / s, 0.0))

    depth_axis = Vector((0, 1, 0)) if view == 'side' else Vector((0, 0, 1))
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    parts, pivots = part_masks(spec, mask)
    tris_total, part_tris = 0, {}
    for part, pm in parts.items():
        if pm.sum() < 30:
            continue
        pts, tris, dist, radius = relief(pm, step)
        cap = spec['depth'] if not part.startswith('Wing') else spec['depth'] * 0.4
        d, R = np.maximum(dist - 1.0, 0.0) / s, np.maximum(radius - 1.0, np.maximum(dist - 1.0, 0.5)) / s
        dz = cap * np.tanh(np.sqrt(np.maximum(d * (2 * R - d), 0.0)) / cap)
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new('UVMap')
        piv = to_model(*pivots[part]) if pivots[part] else Vector()
        for sign in (-1, 1):
            vs = [bm.verts.new(to_model(p[0] + x0, p[1] + y0) + depth_axis * (sign * dz[i]) - piv) for i, p in enumerate(pts)]
            for a, b, c in tris:
                order = (a, b, c) if sign < 0 else (a, c, b)
                try:
                    f = bm.faces.new([vs[k] for k in order])
                except ValueError:
                    continue
                for loop, k in zip(f.loops, order):
                    loop[uvl].uv = atlas.uv(pos, pts[k][0], pts[k][1])
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(name + '.' + part)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name + '.' + part, me)
        bpy.context.scene.collection.objects.link(o)
        o.parent = root
        o.location = piv
        KB.keep_uv_white(o)
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        part_tris[part] = len(me.polygons)
        tris_total += len(me.polygons)
    for ename, epiv in spec['empties']:
        e = bpy.data.objects.new(name + '.' + ename, None)
        bpy.context.scene.collection.objects.link(e)
        e.parent = root
        e.location = to_model(*epiv)
    front = bpy.data.objects.new(name + '.Attach.Front', None)
    bpy.context.scene.collection.objects.link(front)
    front.parent = root
    front.location = (0, -1, 0)
    lo = [min((o.matrix_world @ v.co)[k] for o in root.children if o.type == 'MESH' for v in o.data.vertices) for k in range(3)]
    hi = [max((o.matrix_world @ v.co)[k] for o in root.children if o.type == 'MESH' for v in o.data.vertices) for k in range(3)]
    info = dict(id=spec['id'], sheet=spec['sheet'], box=list(spec['box']), view=view, px_per_m=round(s, 1),
                tris=tris_total, parts=part_tris, empties=[e[0] for e in spec['empties']],
                size=[round(hi[k] - lo[k], 3) for k in range(3)])
    return root, info, mask, parts


def export(root, path):
    """One FBX per model with the game's part names (Body, Tail, WingL...): the Blender names carry the model's name
    first only so that two models' parts can live in one file."""
    kids = [root] + list(root.children_recursive)
    old = {o: o.name for o in kids}
    for o in kids[1:]:
        o.name = o.name.split('.', 1)[1]
    K.export_model(root, path)
    for o, n in old.items():
        o.name = n


def cuts_sheet(results, out):
    """Every model's outline with its parts coloured (Body grey, Tail orange, Head cyan, legs green, wings magenta)."""
    col = {'Body': (150, 150, 150), 'Tail': (255, 150, 0), 'Head': (0, 220, 255), 'LegFL': (60, 220, 60),
           'LegBL': (30, 150, 30), 'WingL': (230, 60, 230), 'WingR': (150, 40, 200)}
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
    tiles = []
    for name, (sheet, spec, mask, parts) in results.items():
        x0, y0, x1, y1 = spec['box']
        photo = np.asarray(sheet.convert('RGB'))[y0:y1, x0:x1].astype(np.float32)
        over = photo * 0.35
        for part, pm in parts.items():
            over[pm > 0] = photo[pm > 0] * 0.45 + np.array(col.get(part, (255, 255, 255))) * 0.55
        im = Image.fromarray(over.clip(0, 255).astype(np.uint8))
        im.thumbnail((380, 300))
        t = Image.new('RGB', (380, 324), (25, 25, 28))
        t.paste(im, (0, 24))
        ImageDraw.Draw(t).text((4, 2), name, fill=(240, 240, 240), font=font)
        tiles.append(t)
    cols = 6
    rows = (len(tiles) + cols - 1) // cols
    sheet_im = Image.new('RGB', (cols * 384, rows * 328), (10, 10, 12))
    for i, t in enumerate(tiles):
        sheet_im.paste(t, ((i % cols) * 384, (i // cols) * 328))
    sheet_im.save(out, quality=88)
    print('cuts', out, sheet_im.size)


def board(roots, infos, atlas_path, out, sheets):
    """Each model: its sheet, the model straight on, the model turned (from in front and to the left, a little above;
    a flyer from below and to the side, as one is seen overhead; a thing lying flat from in front and above)."""
    mat = KB.unlit(atlas_path, cut=True)
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            o.data.materials.clear()
            o.data.materials.append(mat)
    tmp = os.path.dirname(out)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20)
    tiles = []
    for name, root in roots.items():
        info = infos[name]
        spec = ANIMALS[name]
        meshes = {o.name for o in root.children_recursive if o.type == 'MESH'}
        pts = [o.matrix_world @ v.co for o in root.children_recursive if o.type == 'MESH' for v in o.data.vertices]
        lo = Vector([min(p[k] for p in pts) for k in range(3)])
        hi = Vector([max(p[k] for p in pts) for k in range(3)])
        c = (lo + hi) / 2
        ext = max(hi - lo)
        x0, y0, x1, y1 = spec['box']
        a = sheets[spec['sheet']].crop(spec['box'])
        a.thumbnail((300, 220))
        size = (300, 220)
        if info['view'] == 'side':
            w = (hi.x - lo.x) * 1.08
            b = KB.render(os.path.join(tmp, 'a_front.png'), (c.x, c.y - 10, c.z), (c.x, c.y, c.z), ortho=max(w, (hi.z - lo.z) * 1.08 * 300 / 220),
                          size=size, only=meshes)
            t = KB.render(os.path.join(tmp, 'a_turn.png'), (c.x - 1.1 * ext, c.y - 1.6 * ext, c.z + 0.6 * ext), tuple(c),
                          fov=40, size=size, only=meshes)
        elif info['view'] == 'below':
            b = KB.render(os.path.join(tmp, 'a_front.png'), (c.x, c.y, c.z - 10), (c.x - 0.002, c.y, c.z),
                          ortho=(hi.y - lo.y) * 1.08, size=size, only=meshes)
            t = KB.render(os.path.join(tmp, 'a_turn.png'), (c.x + 0.4 * ext, c.y - 1.8 * ext, c.z - 0.8 * ext), tuple(c),
                          fov=36, size=size, only=meshes)
        else:
            b = KB.render(os.path.join(tmp, 'a_front.png'), (c.x, c.y - 0.002, c.z + 10), (c.x, c.y, c.z),
                          ortho=(hi.x - lo.x) * 1.08, size=size, only=meshes)
            t = KB.render(os.path.join(tmp, 'a_turn.png'), (c.x - 0.5 * ext, c.y - 1.5 * ext, c.z + 1.0 * ext), tuple(c),
                          fov=36, size=size, only=meshes)
        tile = Image.new('RGB', (930, 250), (40, 40, 46))
        tile.paste(a, (5 + (300 - a.width) // 2, 26 + (220 - a.height) // 2))
        tile.paste(b, (315, 26))
        tile.paste(t, (625, 26))
        ImageDraw.Draw(tile).text((6, 2), '%s  %s  %d tris  %s' % (name, info['id'], info['tris'],
                                                                  ' '.join(p for p in info['parts'] if p != 'Body')),
                                  fill=(235, 235, 240), font=font)
        tiles.append(tile)
    cols = 3
    rows = (len(tiles) + cols - 1) // cols
    sheet_im = Image.new('RGB', (cols * 940, rows * 258 + 50), (25, 25, 28))
    ImageDraw.Draw(sheet_im).text((10, 12), 'Each: your sheet  |  the model straight on  |  turned', fill=(240, 240, 240),
                                  font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26))
    for i, t in enumerate(tiles):
        sheet_im.paste(t, ((i % cols) * 940 + 5, 50 + (i // cols) * 258))
    sheet_im.save(out, quality=88)
    print('board', out, sheet_im.size)


def main():
    os.makedirs(OUT, exist_ok=True)
    K.reset()
    atlas = KB.Atlas(4096)
    sheets = {}
    roots, infos, results = {}, {}, {}
    for name, spec in ANIMALS.items():
        if ONLY and name not in ONLY:
            continue
        sheet = sheets.setdefault(spec['sheet'], Image.open(os.path.join(REFS, spec['sheet'])).convert('RGB'))
        root, info, mask, parts = build(name, spec, atlas, sheet)
        roots[name], infos[name], results[name] = root, info, (sheet, spec, mask, parts)
        print('%-22s %s %5d triangles  %s  %s m' % (name, info['id'], info['tris'],
                                                   ', '.join('%s %d' % kv for kv in info['parts'].items()), info['size']))
    if CUTS:
        cuts_sheet(results, CUTS)
    atlas_path = os.path.join(OUT, 'KamakuraAnimalsAtlas.png')
    atlas.img.save(atlas_path)
    mat = K.material('KamakuraAnimals', atlas_path)
    for name, root in roots.items():
        for o in root.children_recursive:
            if o.type == 'MESH':
                o.data.materials.clear()
                o.data.materials.append(mat)
        export(root, os.path.join(OUT, name + '.fbx'))
    json.dump({'kit': 'KamakuraAnimals', 'atlas': 'KamakuraAnimalsAtlas.png',
               'material': 'Toon, _ALPHATEST_ON, _Cutoff 0.5 (every model is a cut-out)', 'models': infos},
              open(os.path.join(OUT, 'KamakuraAnimals.json'), 'w'), indent=1)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'KamakuraAnimals.blend'))
    if BOARD:
        board(roots, infos, atlas_path, BOARD, sheets)


if __name__ == '__main__':
    main()
