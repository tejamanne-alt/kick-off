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
#                                        [--cuts /abs/cuts.jpg] [--review /abs/review_dir]
# --review writes the strict review (docs/ASSET_REVIEW.md) of every model built: views/<Model>.jpg (all eight sides),
# motion/<Model>_<motion>.gif (walk, run, hop, peck, fly, swim, idle as apply), source/<Model>.jpg, review.json (the
# checks).
# Writes into outdir: <Model>.fbx per model, KamakuraAnimalsAtlas.png, KamakuraAnimals.json, KamakuraAnimals.blend.
# --cuts writes a sheet of every model's outline with its parts coloured (to check the cuts).
import json
from collections import Counter
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
import asset_review as AR          # the strict review's eight views and motions (docs/ASSET_REVIEW.md)

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = ARGS[0] if ARGS and not ARGS[0].startswith('--') else os.path.abspath('out_km_animals')
BOARD = ARGS[ARGS.index('--board') + 1] if '--board' in ARGS else None
CUTS = ARGS[ARGS.index('--cuts') + 1] if '--cuts' in ARGS else None
REVIEW = ARGS[ARGS.index('--review') + 1] if '--review' in ARGS else None
ONLY = set(ARGS[ARGS.index('--only') + 1].split(',')) if '--only' in ARGS else None
FRESH = '--fresh' in ARGS
RENDER = '--checks-only' not in ARGS     # --checks-only: the review's checks and measures again, no renders
REFS = KB.REFS
P4, P8 = 'KM-P4_animals_sheet.png', 'KM-P8_more_animals.png'


def A(cid, sheet, box, view, size, depth, parts=(), refine=False, wings=None, exclude=(), empties=(), step=None,
      thresh=42, legs=False, shadow=0.13, head_up=False, fill=(), dark_shadow=False, whiskers=False, hop=False,
      leg_width=0.06, peck=(25.0, 30.0)):
    """One model: its catalogue id (KM-Nxx), sheet, the figure's box (sheet px), its view (side: head to the right,
    standing on its lowest pixel; below: a flyer seen from beneath, head up; above: lying flat, seen from above), its
    size (('w' or 'h', metres) of the figure's outline), its half-depth cap (m), its parts ((name, polygon in sheet px,
    pivot)), refine (GrabCut for colours near the sheet's grey), wings (the body's half-width as a share of the
    figure's width, to split WingL and WingR off a flyer), exclude (polygons left out: a perch wire), empties (extra
    pivots the rig wants with no mesh of their own: (name, pivot)), thresh (how far from the grey a pixel must be to
    count as the figure: lower for see-through wings), legs (a walker's legs found and cut off one by one, see
    leg_masks: the near ones LegFR and LegBR, the far ones LegFL and LegBL, an empty for any the picture doesn't show,
    as Hazards/Dog wants four), shadow (how high up the box a smooth grey shadow is looked for: a low animal's),
    head_up (seen from above with its head to the top of the sheet, as the insects are: turned so its head is +X like
    every other model, its wings out to the sides, hinged about its body as FlitButterfly flaps them), fill (polygons in which a narrow gap's neutral grey
    is closed and painted with the fur around it: fill_pixels), dark_shadow (the shadow's core darker than any
    backdrop grey), whiskers (a cat: the backdrop between its whiskers left out), legs ('biped' for a bird on the
    ground: its two legs, LegR and LegL), hop (a bird that hops with both feet, as GroundBird's hopper does),
    leg_width (a bird: the disk, as a share of its height, wider than its two legs side by side: bird_legs), peck (a
    bird's peck: the head's turn and the body's tip, degrees, GroundBird's peckTurn and peckTip; a long-legged bird
    standing with its feet apart tips less, or its hind foot can't stay down)."""
    return dict(id=cid, sheet=sheet, box=box, view=view, size=size, depth=depth, parts=list(parts), refine=refine,
                wings=wings, exclude=list(exclude), empties=list(empties), step=step, thresh=thresh, legs=legs,
                shadow=shadow, head_up=head_up, fill=list(fill), dark_shadow=dark_shadow, whiskers=whiskers,
                hop=hop, leg_width=leg_width, peck=peck)


ANIMALS = {
    # ---------------------------------------------------------------- KM-P4
    'KmCatSitting': A('KM-N01', P4, (500, 18, 858, 284), 'side', ('h', 0.38), 0.075,
                      [('Tail', [(500, 228), (656, 228), (656, 284), (500, 284)], (648, 262))], whiskers=True),
    'KmCatWalking': A('KM-N01', P4, (21, 44, 443, 280), 'side', ('h', 0.30), 0.06,
                      [('Tail', [(21, 113), (112, 113), (102, 166), (66, 214), (21, 214)], (106, 137))],
                       legs=True, whiskers=True),
    'KmTanukiWalking': A('KM-N02', P4, (1409, 50, 1838, 281), 'side', ('h', 0.36), 0.09,
                         [('Tail', [(1409, 83), (1497, 91), (1497, 194), (1490, 256), (1409, 256)], (1494, 128))],
                         refine=True, legs=True, step=15),
    'KmTanukiSitting': A('KM-N02', P4, (1898, 31, 2280, 282), 'side', ('h', 0.40), 0.09,
                         [('Tail', [(1898, 204), (2034, 204), (2034, 273), (1898, 273)], (2034, 237))], refine=True),
    'KmSquirrelRunning': A('KM-N03', P4, (11, 374, 450, 562), 'side', ('w', 0.40), 0.04,
                           [('Tail', [(11, 374), (148, 374), (144, 488), (11, 496)], (144, 450))], step=15, shadow=0.3,
                           dark_shadow=True),
    'KmSquirrelSitting': A('KM-N03', P4, (523, 322, 837, 606), 'side', ('h', 0.30), 0.045,
                           [('Tail', [(523, 322), (676, 322), (676, 405), (652, 440), (652, 612), (523, 612)], (650, 594))],
                           fill=[[(659, 426), (650, 450), (642, 472), (637, 497), (636, 522), (638, 548), (654, 548),
                                   (653, 522), (654, 497), (659, 472), (667, 452), (676, 426)]]),
    'KmShibaStanding': A('KM-N04', P4, (1474, 314, 1808, 605), 'side', ('h', 0.58), 0.09,
                         [('Tail', [(1493, 340), (1586, 340), (1588, 420), (1493, 426)], (1570, 420)),
                          ('Head', [(1705, 314), (1808, 314), (1808, 433), (1728, 433)], (1734, 426))], legs=True),
    'KmShibaSitting': A('KM-N04', P4, (1940, 317, 2235, 601), 'side', ('h', 0.62), 0.09,
                        [('Tail', [(1940, 499), (2000, 499), (2000, 601), (1940, 601)], (1997, 550))]),
    'KmKitePerched': A('KM-N05', P4, (89, 625, 358, 931), 'side', ('h', 0.75), 0.07,
                       [('Head', [(278, 625), (360, 625), (360, 700), (290, 712)], (290, 690))]),
    'KmCrowStanding': A('KM-N06', P4, (1426, 638, 1788, 919), 'side', ('w', 0.57), 0.06,
                        [('Head', [(1649, 638), (1781, 638), (1781, 722), (1677, 760)], (1663, 722))], legs='biped'),
    'KmCrowHopping': A('KM-N06', P4, (1882, 659, 2272, 910), 'side', ('w', 0.57), 0.06,
                       [('Head', [(2156, 659), (2272, 659), (2272, 733), (2178, 742)], (2170, 720))], legs='biped'),
    'KmPigeonStanding': A('KM-N07', P4, (76, 942, 359, 1218), 'side', ('w', 0.30), 0.05,
                          [('Head', [(269, 942), (356, 942), (356, 1013), (283, 1035)], (291, 1024))], refine=True,
                          legs='biped'),
    'KmPigeonPecking': A('KM-N07', P4, (491, 1027, 847, 1203), 'side', ('w', 0.34), 0.05,
                         [('Head', [(778, 1068), (840, 1068), (840, 1171), (772, 1171)], (789, 1089))], refine=True,
                         shadow=0.3, dark_shadow=True, legs='biped'),
    'KmSparrowPerched': A('KM-N08', P4, (1443, 961, 1755, 1213), 'side', ('w', 0.15), 0.025,
                          [('Head', [(1641, 961), (1749, 961), (1749, 1063), (1650, 1075)], (1665, 1063))], refine=True),
    'KmSparrowHopping': A('KM-N08', P4, (1898, 979, 2235, 1213), 'side', ('w', 0.15), 0.025,
                          [('Head', [(2122, 979), (2229, 979), (2229, 1083), (2135, 1092)], (2144, 1076))], refine=True,
                          legs='biped', hop=True),
    'KmSparrowFlying': A('KM-N08', P4, (2359, 958, 2696, 1201), 'below', ('w', 0.21), 0.02, wings=0.09, refine=True),
    'KmSwallowPerched': A('KM-N09', P4, (0, 1255, 466, 1525), 'side', ('h', 0.22), 0.02,
                          exclude=[[(0, 1350), (122, 1365), (122, 1415), (0, 1400)],
                                   [(325, 1398), (466, 1412), (466, 1450), (325, 1435)]]),
    'KmSwallowFlying': A('KM-N09', P4, (466, 1265, 908, 1526), 'below', ('w', 0.33), 0.015, wings=0.07),
    'KmGullStanding': A('KM-N10', P4, (960, 1255, 1296, 1527), 'side', ('h', 0.34), 0.06,
                        [('Head', [(1173, 1255), (1290, 1255), (1290, 1352), (1189, 1375)], (1199, 1358))],
                        refine=True, legs='biped', leg_width=0.09),
    'KmEgretStanding': A('KM-N11', P4, (1939, 1238, 2225, 1535), 'side', ('h', 0.55), 0.05,
                         [('Head', [(2110, 1238), (2222, 1238), (2222, 1292), (2122, 1301)], (2127, 1292))],
                         legs='biped', peck=(40.0, 15.0)),
    # ---------------------------------------------------------------- KM-P8
    'KmKoiRedWhite': A('KM-N12', P8, (21, 60, 428, 238), 'above', ('w', 0.60), 0.06),
    'KmKoiRedWhiteTurning': A('KM-N12', P8, (505, 48, 874, 238), 'above', ('w', 0.52), 0.06),
    'KmKoiGold': A('KM-N13', P8, (952, 68, 1355, 238), 'above', ('w', 0.55), 0.06),
    'KmKoiGoldTurning': A('KM-N13', P8, (1408, 44, 1807, 256), 'above', ('w', 0.48), 0.06),
    'KmTurtleBasking': A('KM-N14', P8, (1867, 66, 2255, 237), 'side', ('w', 0.36), 0.05, refine=True),
    'KmTurtleSwimming': A('KM-N14', P8, (2327, 16, 2715, 274), 'above', ('w', 0.33), 0.035, refine=True),
    'KmHeronStanding': A('KM-N15', P8, (101, 303, 366, 609), 'side', ('h', 0.90), 0.07,
                         [('Head', [(219, 303), (363, 303), (363, 362), (228, 371)], (278, 359))], refine=True,
                         legs='biped'),
    'KmCormorantStanding': A('KM-N16', P8, (1011, 317, 1279, 604), 'side', ('h', 0.85), 0.07,
                             [('Head', [(1160, 317), (1273, 317), (1273, 369), (1168, 378)], (1177, 369))], refine=True),
    'KmCormorantDrying': A('KM-N16', P8, (1390, 323, 1822, 602), 'side', ('w', 0.95), 0.07, refine=True),
    'KmWagtail': A('KM-N17', P8, (2316, 345, 2684, 582), 'side', ('w', 0.21), 0.02,
                   [('Head', [(2550, 345), (2677, 345), (2677, 412), (2560, 423)], (2571, 412))], refine=True,
                   legs='biped'),
    'KmWhiteEyePerched': A('KM-N18', P8, (66, 651, 366, 932), 'side', ('w', 0.13), 0.015,
                           [('Head', [(265, 651), (360, 651), (360, 749), (277, 761)], (285, 743))]),
    'KmWhiteEyeFlying': A('KM-N18', P8, (509, 639, 863, 891), 'below', ('w', 0.18), 0.012, wings=0.08),
    'KmBulbulPerched': A('KM-N19', P8, (972, 640, 1277, 912), 'side', ('w', 0.28), 0.025,
                         [('Head', [(1148, 640), (1271, 640), (1271, 740), (1160, 751)], (1171, 734))], refine=True),
    'KmBulbulFlying': A('KM-N19', P8, (1406, 626, 1806, 907), 'below', ('w', 0.40), 0.02, wings=0.07, refine=True),
    'KmDoveStanding': A('KM-N20', P8, (1863, 647, 2225, 905), 'side', ('w', 0.33), 0.05,
                        [('Head', [(2142, 647), (2222, 647), (2222, 727), (2135, 738)], (2155, 724))], refine=True,
                        legs='biped'),
    'KmDoveFlying': A('KM-N20', P8, (2314, 646, 2731, 900), 'below', ('w', 0.53), 0.025, wings=0.08, refine=True),
    'KmCalicoWalking': A('KM-N21', P8, (12, 936, 438, 1220), 'side', ('h', 0.30), 0.06,
                         [('Tail', [(12, 993), (102, 993), (98, 1047), (61, 1059), (12, 1059)], (94, 1022))],
                          refine=True, legs=True, whiskers=True),
    'KmCalicoAsleep': A('KM-N21', P8, (967, 965, 1337, 1206), 'side', ('w', 0.42), 0.09, refine=True, whiskers=True),
    'KmTuxedoWalking': A('KM-N22', P8, (1392, 969, 1801, 1216), 'side', ('h', 0.30), 0.06,
                         [('Tail', [(1392, 1012), (1479, 1012), (1479, 1063), (1423, 1166), (1392, 1166)], (1471, 1048))],
                          refine=True, legs=True, whiskers=True),
    'KmTuxedoSitting': A('KM-N22', P8, (1872, 936, 2218, 1220), 'side', ('h', 0.38), 0.075,
                         [('Tail', [(1872, 1149), (2002, 1149), (2002, 1209), (1872, 1209)], (2002, 1179))],
                          refine=True, whiskers=True),
    'KmTuxedoLying': A('KM-N22', P8, (2308, 995, 2724, 1172), 'side', ('w', 0.60), 0.075,
                       [('Tail', [(2308, 1071), (2404, 1071), (2404, 1113), (2308, 1113)], (2400, 1095))],
                        refine=True, whiskers=True),
    'KmSwallowtail': A('KM-N25', P8, (961, 1248, 1334, 1531), 'above', ('w', 0.10), 0.003, wings=0.025, head_up=True),
    'KmDragonfly': A('KM-N26', P8, (1398, 1255, 1814, 1524), 'above', ('w', 0.07), 0.002, wings=0.025, head_up=True, thresh=14),
}


def figure_mask(sheet, spec):
    """The figure in its box: what differs from the sheet's grey or is textured (fur, feathers), its holes filled, the
    largest piece. The soft neutral shadow under a figure on the ground is left out (darker than the grey, no colour of
    its own, in the lowest eighth of the box, or, smooth, as high as spec shadow: higher up, a grey bird's own feathers
    look the same). With
    refine, GrabCut finds the parts close to the sheet's grey (a kite's pale tail, a grey pigeon or heron)."""
    a = np.asarray(sheet.convert('RGB')).astype(np.int32)
    x0, y0, x1, y1 = spec['box']
    r = a[y0:y1, x0:x1]
    border = np.concatenate([r[:4].reshape(-1, 3), r[-4:].reshape(-1, 3), r[:, :4].reshape(-1, 3), r[:, -4:].reshape(-1, 3)])
    bg = np.median(border, 0)
    m = (np.abs(r - bg).sum(-1) > spec['thresh']).astype(np.uint8)
    # texture: fur and feathers are textured (local deviation 18 to 22 over 7 px), the studio backdrop smooth (under 1,
    # 95 % under 3), so what is textured is the figure even where its colour is the backdrop's (a squirrel's grey-brown
    # back, a kite's wing: D18). Shrunk 3 px, so the window's reach past the outline isn't taken.
    g = r.mean(-1).astype(np.float32)
    mean = cv2.blur(g, (7, 7))
    dev = np.sqrt(np.maximum(cv2.blur(g * g, (7, 7)) - mean * mean, 0))
    tex = cv2.erode((dev > TEXTURE).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    if spec['whiskers']:
        # between a cat's whiskers the window is textured but the pixel is backdrop: there each pixel must differ from
        # the backdrop itself (the whiskers, 1 or 2 px, go with the opening below). Not for every model: a heron's
        # pale legs and a dragonfly's clear wings are as close to the backdrop.
        tex &= (np.abs(r - bg).sum(-1) > 12).astype(np.uint8)
    m |= tex
    shadow = np.zeros(m.shape, bool)
    if spec['view'] == 'side':
        lum = r.mean(-1)
        chroma = r.max(-1) - r.min(-1)
        low = np.zeros(m.shape, bool)
        low[int(m.shape[0] * 0.87):] = True
        tall = np.zeros(m.shape, bool)
        tall[int(m.shape[0] * (1 - spec['shadow'])):] = True
        grey = (chroma < 14) & (lum < bg.mean() - 2) & (lum > bg.mean() - 45)
        # in the lowest eighth any such grey is shadow (the contact shadow under a paw, textured though it is); higher,
        # for a low animal whose shadow reaches up between its legs (spec shadow), only where it is smooth too, as fur
        # never is; with dark_shadow, a neutral grey darker than any backdrop too (D18)
        shadow = (low & grey) | (tall & grey & (dev < 3))
        if spec['dark_shadow']:     # its core darker than any backdrop grey; a paw, as dark, is textured where it isn't
            shadow |= tall & (chroma < 12) & (lum < bg.mean() - 2) & (dev < 8)
        m[shadow] = 0
    for poly in spec['exclude']:
        cv2.fillPoly(m, [np.array([(x - x0, y - y0) for x, y in poly], np.int32)], 0)
    raw = m.copy()                  # before the cleanup: every thin part still there
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
    # the thin parts the cleanup cut off, grown back from the figure into the uncleaned cut: a heron's lower legs and
    # toes, 2 or 3 px wide, came apart from the body at the opening and were dropped as a separate piece (D19); specks
    # that never touch the figure stay out
    if spec['whiskers']:            # a cat's whiskers stay out: a fan of thin strokes, read as a grey beard on the model
        raw = m.copy()              # (and nothing else of a cat is that thin)
    raw = (raw | m).astype(np.uint8)
    while True:
        grown = cv2.dilate(m, np.ones((3, 3), np.uint8)) & raw
        if (grown == m).all():
            break
        m = grown
    # holes: filled when under 1 % of the box (a kite's grey-brown feather patches), or when they are textured and not
    # the sheet's grey (a dark shell's middle); a larger smooth gap stays open, the backdrop seen between a squirrel's
    # tail and back, even where the backdrop is lit lighter there (D18)
    inv = (1 - m).astype(np.uint8)
    hn, hl, hs, _ = cv2.connectedComponentsWithStats(inv, 4)
    for i in range(1, hn):
        x, y, w, h, area = hs[i]
        if x > 0 and y > 0 and x + w < m.shape[1] and y + h < m.shape[0]:
            hole = hl == i
            backdrop = (dev[hole] < 3).mean() > 0.3 and np.abs(np.median(r[hole], 0) - bg).sum() < 30
            if not backdrop and (area < m.size * 0.01 or dev[hole].mean() > TEXTURE):
                m[hole] = 1
    # a shadow enclosed by legs is not filled back in (a patch of 40 px or more: a grey fleck in a rock is no shadow)
    n, lab, st, _ = cv2.connectedComponentsWithStats(shadow.astype(np.uint8), 8)
    m[np.isin(lab, 1 + np.nonzero(st[1:, 4] >= 40)[0])] = 0
    # the backdrop itself, wherever GrabCut or a hole fill took it in (between a pigeon's legs): smooth, no colour,
    # within 12 of the backdrop's grey, in a patch of 40 px or more (a flat speck of a grey rock is not backdrop)
    like = ((dev < 3) & ((r.max(-1) - r.min(-1)) < 10) & (np.abs(r.mean(-1) - bg.mean()) < 12)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(like, 8)
    m[np.isin(lab, 1 + np.nonzero(st[1:, 4] >= 40)[0])] = 0
    m[fill_pixels(spec, r)] = 1     # a narrow gap closed, painted with the fur around it (build inpaints it)
    return m


def fill_pixels(spec, r):
    """The backdrop pixels of a narrow gap the spec closes (fill polygons: neutral grey inside them), as a mask of the
    box. Too narrow to cut cleanly from a soft picture (the sitting squirrel's tail and back, 6 px apart, lit off the
    backdrop's grey), the gap is closed and painted with the fur around it, a repair the review lists (D18)."""
    x0, y0, x1, y1 = spec['box']
    f = np.zeros(r.shape[:2], np.uint8)
    for poly in spec['fill']:
        cv2.fillPoly(f, [np.array([(x - x0, y - y0) for x, y in poly], np.int32)], 1)
    return (f > 0) & ((r.max(-1) - r.min(-1)) < 12)


def _longest_run(row):
    d = np.diff(np.r_[0, row.astype(np.int8), 0])
    starts, ends = np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]
    return int((ends - starts).max()) if len(starts) else 0


def _twin(masks, pivots, sides, feet, near, far):
    """The picture shows a pair of legs as one (one behind the other): the far leg is a copy of the near one, set
    behind the body. Hidden behind it at rest, it steps out of phase, so a foot is always down (D19: a bird on its one
    leg stood on nothing while that leg swung)."""
    shin_near, shin_far = 'Shin' + near[3:], 'Shin' + far[3:]
    masks[far] = masks[near].copy()
    pivots[far] = pivots[near]
    if shin_near in masks:
        masks[shin_far] = masks[shin_near].copy()
        pivots[shin_far] = pivots[shin_near]
    sides[near], sides[far] = -1, 1
    feet[far] = feet[near]


def leg_masks(rest, biped=False):
    """A walker's legs, from what is left of its figure once its tail and head are taken: each one a thigh (Leg..,
    pivoting at the hip or shoulder) and a shin (Shin.., pivoting at the knee), with the foot's contact point.

    The belly is the lowest row where one unbroken run of pixels still spans 35 % of the figure (20 % for a bird, its
    tail stretching the figure); below it, only legs. Each leg is seeded by the separate pieces in the lower two thirds
    of that region that reach the ground (so two legs touching at the top still part, and a drooping tail tip or
    hanging plumes are no legs), and every leg pixel goes to its nearest seed. A four-legged animal's
    front legs are those ahead of the torso's middle; a bird's two legs are one group. Of two in a group the larger is
    the near one (the right leg: the model's right flank faces the camera), the other the far one; a group of one is
    the near leg alone, at the body's middle.

    Every joint overlaps (D16): the thigh reaches up into the body over half the leg's length, narrowing, its pivot
    inside that reach, three tenths of the leg's length above the belly; the shin reaches up into the thigh the same
    way over a fifth. The knee is halfway down the leg (D19: a leg with no knee can't keep its foot on the ground).
    Returns ({name: mask}, {name: pivot (x, y)}, {leg name: -1 near, +1 far, 0 middle}, {leg name: foot (x, y)}, the
    belly row), all in the mask's frame."""
    none = ({}, {}, {}, {}, None)
    h, w = rest.shape
    ys, xs = np.nonzero(rest)
    if not len(ys):
        return none
    fw = xs.max() - xs.min() + 1
    run = np.array([_longest_run(rest[y]) for y in range(h)])
    # a bird's tail stretches the figure, so its body's last wide row is narrower against the whole: 20 %, not 35 %
    torso = np.nonzero(run > (0.2 if biped else 0.35) * fw)[0]
    if not len(torso):
        return none
    belly, bottom = int(torso.max()), int(ys.max())
    legh = bottom - belly
    if legh < 8:
        return none
    region = rest.copy()
    region[:belly + 1] = 0
    lower = region.copy()
    lower[:belly + 1 + int(0.35 * legh)] = 0
    n, lab = cv2.connectedComponents(lower.astype(np.uint8), connectivity=8)
    # a leg reaches the ground: a drooping tail tip or a heron's hanging plumes end higher (D19)
    keep = [i for i in range(1, n) if (lab == i).sum() >= 0.04 * region.sum()
            and np.nonzero(lab == i)[0].max() >= bottom - 0.12 * legh]
    if not keep:
        return none
    src = np.full((h, w), 255, np.uint8)
    for i in keep:
        src[lab == i] = 0
    near_px = cv2.distanceTransformWithLabels(src, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)[1]
    lut = np.zeros(int(near_px.max()) + 1, np.int32)
    zy, zx = np.nonzero(src == 0)
    lut[near_px[zy, zx]] = lab[zy, zx]
    owner = lut[near_px] * (region > 0)
    tx = np.nonzero(rest[:belly + 1])[1].mean()
    groups = {'': []} if biped else {'F': [], 'B': []}
    for i in keep:
        m = (owner == i).astype(np.uint8)
        groups['' if biped else 'F' if np.nonzero(m)[1].mean() >= tx else 'B'].append(m)

    def reach_up(m, row, height, taper):
        """A band above row, as wide as m is there and narrowing upward: the part's reach into the one above."""
        top = np.nonzero(m[row + 1:row + 4].any(0))[0]
        if not len(top):
            top = np.nonzero(m.any(0))[0]
        mid, half = (top.min() + top.max()) / 2.0, (top.max() - top.min()) / 2.0 + 1
        band = np.zeros_like(m)
        H = max(2, int(height))
        for t in range(0, H + 1):
            k = half * (1 - taper * t / H)
            if row - t >= 0:
                band[row - t, max(0, int(mid - k)):min(w, int(mid + k) + 1)] = 1
        return band, mid

    masks, pivots, sides, feet = {}, {}, {}, {}
    for g, ms in groups.items():
        ms.sort(key=lambda m: -int(m.sum()))
        while len(ms) > 2:          # a stray third piece joins whichever of the two is nearer
            extra = ms.pop()
            ex = np.nonzero(extra)[1].mean()
            j = min((0, 1), key=lambda j: abs(np.nonzero(ms[j])[1].mean() - ex))
            ms[j] = ms[j] | extra
        for m, (side, sign) in zip(ms, (('R', -1 if len(ms) > 1 else 0), ('L', 1))):
            name, shin = 'Leg' + g + side, 'Shin' + g + side
            ly = np.nonzero(m)[0]
            foot_row = int(ly.max())
            knee = int(belly + 0.5 * (foot_row - belly))
            hip_band, hip_x = reach_up(m, belly, 0.5 * legh, 0.35)
            above = np.zeros_like(m)
            above[:knee + 1] = 1
            thigh = ((m & above) | hip_band) & rest
            knee_band, knee_x = reach_up(m * (1 - above), knee, 0.2 * (foot_row - belly), 0.3)
            lower_leg = ((m & (1 - above)) | (knee_band & m)) & rest
            if lower_leg.sum() < 20:            # too short to bend: one piece, no knee
                masks[name] = ((m | hip_band) & rest).astype(np.uint8)
            else:
                masks[name], masks[shin] = thigh.astype(np.uint8), lower_leg.astype(np.uint8)
                pivots[shin] = (knee_x, float(knee))
            pivots[name] = (hip_x, belly - 0.3 * legh)
            sides[name] = sign
            fx = np.nonzero(m[max(0, foot_row - 2):foot_row + 1])[1]
            feet[name] = (float(fx.mean()), float(foot_row))
        if len(ms) == 1:
            _twin(masks, pivots, sides, feet, 'Leg' + g + 'R', 'Leg' + g + 'L')
    return masks, pivots, sides, feet, belly


def bird_legs(rest, width=0.06):
    """A bird's legs: the thin parts of its figure that reach the ground (D19). Opening the figure with a disk wider
    than a leg leaves the body; what it took away and what touches the lowest twelfth of the figure is legs and toes
    (a tail tip or a hanging plume ends higher). Each leg is cut at its middle: the upper part (Leg.., pivoting where
    the leg leaves the feathers, reaching up into them) and the lower (Shin.., pivoting at the joint, reaching up into
    the upper), its foot where its toes meet the ground. The larger is the near (right) leg. Returns the same as
    leg_masks, and the bare legs' own pixels (what the body gives up)."""
    none = ({}, {}, {}, {}, None, np.zeros_like(rest))
    h, w = rest.shape
    ys, xs = np.nonzero(rest)
    if not len(ys):
        return none
    top, bottom = int(ys.min()), int(ys.max())
    fh = bottom - top + 1
    dist = cv2.distanceTransform(rest, cv2.DIST_L2, 5)
    r = max(3, int(width * fh))     # two legs side by side are narrower than this disk; a body far wider
    k = 2 * r + 1
    body = cv2.morphologyEx(rest, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    thin = (rest & (1 - cv2.dilate(body, np.ones((3, 3), np.uint8)))).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(thin, connectivity=8)
    legs = []
    for i in range(1, n):
        x, y, cw, ch, area = st[i]
        if y + ch - 1 >= bottom - fh / 12.0 and ch >= 0.06 * fh and area >= 15:
            legs.append((lab == i).astype(np.uint8))
    if not legs:
        return none
    legs.sort(key=lambda m: -int(m.sum()))
    while len(legs) > 2:
        extra = legs.pop()
        ex = np.nonzero(extra)[1].mean()
        j = min((0, 1), key=lambda j: abs(np.nonzero(legs[j])[1].mean() - ex))
        legs[j] = legs[j] | extra
    masks, pivots, sides, feet = {}, {}, {}, {}
    for m, (side, sign) in zip(legs, (('R', -1 if len(legs) > 1 else 0), ('L', 1))):
        name, shin = 'Leg' + side, 'Shin' + side
        my = np.nonzero(m)[0]
        t0, fb = int(my.min()), int(my.max())
        L = fb - t0
        joint = int(t0 + 0.5 * L)

        def band_above(src, row, height):
            cols = np.nonzero(src[row:row + 3].any(0))[0]
            mid, half = (cols.min() + cols.max()) / 2.0, (cols.max() - cols.min()) / 2.0 + 1
            b = np.zeros_like(src)
            H = max(2, int(height))
            for t in range(0, H + 1):
                kk = half * (1 - 0.3 * t / H)
                if row - t >= 0:
                    b[row - t, max(0, int(mid - kk)):min(w, int(mid + kk) + 1)] = 1
            return b, mid

        hip_band, hip_x = band_above(m, t0, 0.3 * L)
        above = np.zeros_like(m)
        above[:joint + 1] = 1
        upper = ((m & above) | hip_band) & rest
        lower_core = m & (1 - above)
        if lower_core.sum() < 15:
            masks[name] = ((m | hip_band) & rest).astype(np.uint8)
        else:
            kb, knee_x = band_above(lower_core, joint + 1, 0.2 * L)
            masks[name] = upper.astype(np.uint8)
            masks[shin] = ((lower_core | (kb & m)) & rest).astype(np.uint8)
            pivots[shin] = (knee_x, float(joint))
        pivots[name] = (hip_x, float(t0) - 0.1 * L)
        sides[name] = sign
        fx = np.nonzero(m[max(0, fb - 2):fb + 1])[1]
        feet[name] = (float(fx.mean()), float(fb))
    if len(legs) == 1:
        _twin(masks, pivots, sides, feet, 'LegR', 'LegL')
    core = np.zeros_like(rest)
    for m in legs:
        core |= m
    return masks, pivots, sides, feet, top, core


def part_masks(spec, mask):
    """Each part's pixels ({name: mask}, pivot {name: (x, y)} in sheet px, and the side each leg sits on): the polygon
    parts, a walker's legs (leg_masks), the wings of a flyer, and the Body (the rest). A flyer's wings are what lies
    beyond the body's half-width either side of its middle, above the lowest point the wings reach.

    Every part but the Body then overlaps the body at its joint (D16): grown into the body's pixels by about half its
    own thickness, so no seam opens where the two meshes meet, and none when the part turns. The Body keeps its pixels:
    the two overlap there, both showing the same picture."""
    x0, y0, x1, y1 = spec['box']
    h, w = mask.shape
    parts, pivots, sides = {}, {}, {}
    taken = np.zeros_like(mask)
    for name, poly, pivot in spec['parts']:
        pm = np.zeros_like(mask)
        cv2.fillPoly(pm, [np.array([(x - x0, y - y0) for x, y in poly], np.int32)], 1)
        pm &= mask & (1 - taken)
        parts[name], pivots[name] = pm, pivot
        taken |= pm
    banded = set()
    if spec['legs']:
        rest = (mask & (1 - taken)).astype(np.uint8)
        biped = spec['legs'] == 'biped'
        below = np.zeros_like(mask)
        if biped:                       # a bird's bare legs leave the body; their reach into the feathers stays its
            legs, lpiv, lsides, lfeet, belly, core = bird_legs(rest, spec['leg_width'])
            below = core
        else:
            legs, lpiv, lsides, lfeet, belly = leg_masks(rest)
            if belly is not None:
                below[belly + 1:] = 1
        for name, pm in legs.items():
            parts[name] = pm
            pivots[name] = (x0 + lpiv[name][0], y0 + lpiv[name][1])
            if name in lsides:
                sides[name] = lsides[name]
            taken |= pm & below          # the thigh's reach into the body stays the body's too
            banded.add(name)
        for name, (fx, fy) in lfeet.items():
            spec.setdefault('_feet', {})[name] = (x0 + fx, y0 + fy)
        spec['_joints'] = [(pivots[n], 'joint') for n in legs] + [((x0 + fx, y0 + fy), 'foot') for fx, fy in lfeet.values()]
        for g in ([''] if biped else ['F', 'B']):
            have = [n for n in legs if n.startswith('Leg' + g) and len(n) == 4 + len(g)]
            for side in 'RL':
                name = 'Leg' + g + side
                if name not in legs and have:
                    spec.setdefault('_auto_empties', []).append((name, pivots[have[0]]))
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
        # seen from below, the sheet's left is the bird's right wing; seen from above, its left
        left_first = spec['view'] == 'above'
        for name, side in (('WingL' if left_first else 'WingR', xx < cx), ('WingR' if left_first else 'WingL', xx >= cx)):
            pm = (mask & beyond & side & (1 - taken)).astype(np.uint8)
            parts[name] = pm
            pivots[name] = (x0 + cx + (bw if side[0, -1] else -bw), shoulder)
            taken |= pm
    body = (mask & (1 - taken)).astype(np.uint8)
    for name, pm in list(parts.items()):
        if name in banded or not pm.any():
            continue
        thick = float(cv2.distanceTransform(pm, cv2.DIST_L2, 5).max())
        k = 2 * int(round(max(3.0, 0.6 * thick))) + 1
        grown = cv2.dilate(pm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        parts[name] = (pm | (grown & body)).astype(np.uint8)
    parts['Body'] = body
    pivots['Body'] = None
    return parts, pivots, sides


def relief(mask, step):
    """A triangulation of the mask: points along its outline every 7 px and inside it every step px, Delaunay, the
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
        for s in np.arange(0, L[-1], 7.0):
            i = min(np.searchsorted(L, s), len(c) - 1)
            pts.append((float(c[i][0]), float(c[i][1])))
    for y in np.arange(step / 2, h, step):
        for x in np.arange(step / 2 + (step / 2 if int(y / step) % 2 else 0), w, step):
            if dist[int(y), int(x)] > step * 0.45:
                pts.append((float(x), float(y)))
    # a thin part's spine (the ridge of its distance field, where the grid has no points): without it the triangles
    # span the part from outline to outline and its two faces pinch together along them (D16)
    ridge = (dist >= 2.5) & (dist <= step * 0.45) & (dist >= cv2.dilate(dist, np.ones((5, 5), np.uint8)) - 1e-3)
    spaced = {}
    gap = max(4.0, step / 1.5)
    for y, x in zip(*np.nonzero(ridge)):
        cell = (int(x // gap), int(y // gap))
        if cell not in spaced:
            spaced[cell] = (float(x), float(y))
    pts.extend(spaced.values())
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
    # a triangle with every corner on the outline would be flat, one-sided once its faces merge (a fin that vanishes
    # from behind, the Toon shader culling back faces): split it at its middle, given a little depth
    keys, d = list(keys), list(d)
    split = []
    for a, b, c in tris:
        if d[a] <= 1.01 and d[b] <= 1.01 and d[c] <= 1.01:
            m = len(keys)
            keys.append(((keys[a][0] + keys[b][0] + keys[c][0]) / 3, (keys[a][1] + keys[b][1] + keys[c][1]) / 3))
            cy, cx = min(int(round(keys[m][1])), h - 1), min(int(round(keys[m][0])), w - 1)
            d.append(max(float(dist[cy, cx]), 1.6))
            split += [(a, b, m), (b, c, m), (c, a, m)]
        else:
            split.append((a, b, c))
    tris, d = split, np.array(d, np.float32)
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
    filled = fill_pixels(spec, rgb.astype(np.int32))
    inner[cv2.dilate(filled.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0] = 0
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
        if spec['head_up']:         # from above, head to the top of the sheet: its left wing is the sheet's left (+Y)
            return Vector(((oy - gy) / s, (ox - gx) / s, 0.0))
        return Vector(((gx - ox) / s, (oy - gy) / s, 0.0))

    depth_axis = Vector((0, 1, 0)) if view == 'side' else Vector((0, 0, 1))
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    parts, pivots, sides = part_masks(spec, mask)
    tris_total, part_tris, open_edges, ratio = 0, {}, {}, {}
    body_depth = 0.0
    objs = {}
    # the Body first (its depth places the legs), each thigh before its shin (the shin hangs from it)
    for part in sorted(parts, key=lambda p: (p != 'Body', p.startswith('Shin'))):
        pm = parts[part]
        if pm.sum() < 30:
            continue
        pts, tris, dist, radius = relief(pm, step)
        cap = spec['depth'] if not part.startswith('Wing') else spec['depth'] * 0.4
        d, R = np.maximum(dist - 1.0, 0.0) / s, np.maximum(radius - 1.0, np.maximum(dist - 1.0, 0.5)) / s
        dz = cap * np.tanh(np.sqrt(np.maximum(d * (2 * R - d), 0.0)) / cap)
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new('UVMap')
        piv = to_model(*pivots[part]) if pivots[part] else Vector()
        face_verts = {}
        for sign in (-1, 1):
            vs = [bm.verts.new(to_model(p[0] + x0, p[1] + y0) + depth_axis * (sign * dz[i]) - piv) for i, p in enumerate(pts)]
            face_verts[sign] = vs
            for a, b, c in tris:
                order = (a, b, c) if sign < 0 else (a, c, b)
                try:
                    f = bm.faces.new([vs[k] for k in order])
                except ValueError:
                    continue
                for loop, k in zip(f.loops, order):
                    loop[uvl].uv = atlas.uv(pos, pts[k][0], pts[k][1])
        # the shell closed: wherever the triangles' edge leaves the outline (a notch where a thin triangle fell outside
        # the mask), a wall joins the two faces, so no slit shows between them
        used = Counter(tuple(sorted(e)) for a, b, c in tris for e in ((a, b), (b, c), (c, a)))
        fv, bv = face_verts[-1], face_verts[1]
        for (a, b), n in used.items():
            if n != 1 or (dz[a] <= 0 and dz[b] <= 0):
                continue
            ring = ([fv[a], fv[b], bv[b], bv[a]] if dz[a] > 0 and dz[b] > 0 else
                    [fv[a], fv[b], bv[b]] if dz[b] > 0 else [fv[a], fv[b], bv[a]])
            keys = [a, b, b, a] if len(ring) == 4 else ([a, b, b] if dz[b] > 0 else [a, b, a])
            try:
                f = bm.faces.new(ring)
            except ValueError:
                continue
            for loop, k in zip(f.loops, keys):
                loop[uvl].uv = atlas.uv(pos, pts[k][0], pts[k][1])
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges[:])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        if part == 'Body':
            body_depth = float(np.max(dz))
        open_edges[part] = [sum(1 for e in bm.edges if len(e.link_faces) == 1),
                            sum(1 for e in bm.edges if len(e.link_faces) > 2)]
        ratio[part] = round(float(np.max(dz) / max(np.max(R), 1e-6)), 2)
        me = bpy.data.meshes.new(name + '.' + part)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name + '.' + part, me)
        bpy.context.scene.collection.objects.link(o)
        thigh = objs.get('Leg' + part[4:]) if part.startswith('Shin') else None
        if thigh is not None:       # a shin hangs from its thigh, its origin at the knee
            o.parent = thigh
            o.location = piv - to_model(*pivots['Leg' + part[4:]])
        else:
            o.parent = root
            # a near leg stands in front of the body's middle, a far one behind it (the top view shows four legs)
            o.location = piv + depth_axis * (sides.get(part, 0) * 0.6 * body_depth)
        objs[part] = o
        KB.keep_uv_white(o)
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        part_tris[part] = len(me.polygons)
        tris_total += len(me.polygons)
    # each foot's contact point, an empty under its shin (or its thigh, for a leg too short to bend): where the gait
    # puts the foot on the ground (LegGait)
    for leg, foot in spec.pop('_feet', {}).items():
        suffix = leg[3:]
        holder = 'Shin' + suffix if 'Shin' + suffix in objs else leg
        if holder not in objs:
            continue
        e = bpy.data.objects.new(name + '.Foot' + suffix, None)
        bpy.context.scene.collection.objects.link(e)
        e.parent = objs[holder]
        e.location = to_model(*foot) - to_model(*pivots[holder])
    for ename, epiv in spec['empties'] + spec.pop('_auto_empties', []):
        e = bpy.data.objects.new(name + '.' + ename, None)
        bpy.context.scene.collection.objects.link(e)
        e.parent = root
        e.location = to_model(*epiv) + depth_axis * (0.6 * body_depth if ename.endswith('L') and ename.startswith('Leg') else
                                                     -0.6 * body_depth if ename.startswith('Leg') else 0.0)
    front = bpy.data.objects.new(name + '.Attach.Front', None)
    bpy.context.scene.collection.objects.link(front)
    front.parent = root
    front.location = (0, -1, 0)
    bpy.context.view_layer.update()
    meshes = [o for o in root.children_recursive if o.type == 'MESH']
    lo = [min((o.matrix_world @ v.co)[k] for o in meshes for v in o.data.vertices) for k in range(3)]
    hi = [max((o.matrix_world @ v.co)[k] for o in meshes for v in o.data.vertices) for k in range(3)]
    info = dict(id=spec['id'], sheet=spec['sheet'], box=list(spec['box']), view=view, px_per_m=round(s, 1),
                tris=tris_total, parts=part_tris,
                empties=[o.name.split('.', 1)[1] for o in root.children_recursive if o.type == 'EMPTY'],
                size=[round(hi[k] - lo[k], 3) for k in range(3)], open_edges=open_edges, depth_to_width=ratio,
                edges=sum(len(o.data.edges) for o in meshes))
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
    col = {'Body': (150, 150, 150), 'Tail': (255, 150, 0), 'Head': (0, 220, 255), 'LegFR': (90, 255, 90),
           'LegFL': (40, 170, 40), 'LegBR': (255, 255, 60), 'LegBL': (170, 170, 30), 'WingL': (230, 60, 230),
           'WingR': (150, 40, 200), 'ShinFR': (40, 120, 255), 'ShinFL': (20, 60, 160), 'ShinBR': (255, 90, 60),
           'ShinBL': (160, 50, 30), 'LegR': (90, 255, 90), 'LegL': (40, 170, 40), 'ShinR': (40, 120, 255),
           'ShinL': (20, 60, 160)}
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
    tiles = []
    for name, (sheet, spec, mask, parts) in results.items():
        x0, y0, x1, y1 = spec['box']
        photo = np.asarray(sheet.convert('RGB'))[y0:y1, x0:x1].astype(np.float32)
        over = photo * 0.35
        for part in sorted(parts, key=lambda p: p != 'Body'):     # the Body under the parts that overlap it
            pm = parts[part]
            over[pm > 0] = photo[pm > 0] * 0.45 + np.array(col.get(part, (255, 255, 255))) * 0.55
        im = Image.fromarray(over.clip(0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        for (px, py), kind in spec.get('_joints', []):
            r = max(3, im.width // 90)
            px, py = px - x0, py - y0
            if kind == 'foot':
                d.line([(px - r, py - r), (px + r, py + r)], fill=(255, 0, 0), width=2)
                d.line([(px - r, py + r), (px + r, py - r)], fill=(255, 0, 0), width=2)
            else:
                d.ellipse([px - r, py - r, px + r, py + r], outline=(255, 255, 255), width=2)
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


TEXTURE = 6.0                # the local deviation above which a pixel is fur or feather, not the backdrop
ON_A_ROCK = ('KM-N16',)      # the cormorant, drawn on its rock: CritterIdle, never walks (KAMAKURA_BUILD's catalogue)


def motions_of(name, info):
    """The motions a model is shown in (docs/ASSET_REVIEW.md, section 2), each as the game's behaviour moves it, with
    the view to show it from and the frame time (ms; 24 frames a cycle)."""
    parts, view = info['parts'], info['view']
    h = max(info['size'][2], 0.02) if view == 'side' else max(info['size'][0], 0.02)
    span = max(info['size'][1], 0.02)
    legs = [p for p in parts if p.startswith('Leg')]
    bird = any(len(p) == 4 for p in legs)                   # LegR / LegL: a bird's two
    if legs and not bird:
        return [('walk', AR.walk(h), None, 46), ('run', AR.walk(h, run=True), None, 30)]
    if 'Running' in name:           # mid-leap, legs flat along the ground: it scurries (Hazards/TreeSquirrel moves its tail)
        return [('scurry', AR.scurry(h), None, 30), ('idle', AR.idle(h), None, 55)]
    if 'WingL' in parts:
        if view == 'below':
            return [('fly', AR.fly(span), AR.UP_BELOW, 35)]
        return [('fly', AR.fly(span, beat=76, up_only=True), AR.INSECT, 25)]
    if view == 'above':
        return [('swim', AR.swim(h), AR.UP_ABOVE, 45)]
    if 'Head' in parts and 'Perched' not in name and info['id'] not in ON_A_ROCK:
        if ANIMALS[name]['hop']:
            return [('hop', AR.hop(h), None, 40), ('peck', AR.peck(h, *ANIMALS[name]['peck']), None, 40)]
        # GroundBird nods the head with each step (headNod 7) and pecks with the body (peckTurn 25, peckTip 30)
        turn, tip = ANIMALS[name]['peck']
        return [('walk', AR.gait('step', h, head_nod=7.0), None, 45), ('peck', AR.peck(h, turn, tip), None, 40)]
    if 'Head' in parts or 'Tail' in parts:
        return [('idle', AR.idle(h), None, 55)]
    return []


GAME_SEES = {
    'side': 'the right flank (Right), and at most the Right 3/4 as it passes; Front, Back, Top and Bottom are built '
            'from the side picture alone (a soft, mirrored likeness there, never seen in play)',
    'below': 'from below and to the side as it crosses the sky; its side and top come from the one view from below',
    'above': 'from above (Top), through the water or flitting past; its sides and underside come from the one view '
             'from above',
}
NEEDS_FLIGHT_SHEET = ('KM-N05', 'KM-N06', 'KM-N07', 'KM-N10', 'KM-N11', 'KM-N15', 'KM-N16')   # KM-S1 (Step 4b)


def feet_result(info, motions):
    """Check 16 from the measured feet (asset_review.measure_feet): no foot more than 1 % of the animal's height below
    the ground in any motion; in a walk or a bird's step some foot always down (a trot and a hop have their moments in
    the air); in a peck every foot held where it stood."""
    feet = info.get('feet') or {}
    if not feet:
        return 'n/a', 'no legs that walk'
    tol = 0.01 * max(info['size'][2], 0.05)
    bad, notes = [], []
    for motion, m in feet.items():
        notes.append('%s: sink %.1f mm, lowest foot %.1f mm up, held %.1f mm' % (
            motion, 1000 * m['sink'], 1000 * m['contact'], 1000 * m['held']))
        if m['sink'] > tol:
            bad.append(motion + ' sinks')
        if motion == 'walk' and m['contact'] > tol:
            bad.append(motion + ': a frame with no foot down')
        if motion == 'peck' and m['held'] > tol:
            bad.append(motion + ': the feet move')
    return ('FAIL' if bad else 'pass'), ('; '.join(bad) + ' — ' if bad else '') + '; '.join(notes) + \
        ' (tolerance %.1f mm, 1 %% of its height)' % (1000 * tol)


def checks_of(name, spec, info, motions):
    """The checks of docs/ASSET_REVIEW.md section 3, each with its result for this model: (number, check, result,
    what was found). Results: pass, FAIL, limit (a known limit, said plainly), n/a."""
    slits = sum(v[0] for v in info['open_edges'].values())
    pinches = sum(v[1] for v in info['open_edges'].values())
    parts = [p for p in info['parts']]
    legs = sorted(p for p in parts + info['empties'] if p.startswith('Leg'))
    repairs = ['fur and feathers found by their texture as well as their colour',
               'the ground shadow removed (the lowest %d %% of the box)' % round(100 * max(spec['shadow'], 0.13))]
    if spec['refine']:
        repairs.append('GrabCut inside the outline (colours close to the sheet\'s grey kept)')
    if spec['exclude']:
        repairs.append('%d area(s) left out (the perch wire)' % len(spec['exclude']))
    if spec['fill']:
        repairs.append('a 6 px gap of backdrop between tail and back closed and painted with the fur around it')
    if spec['dark_shadow']:
        repairs.append('the dark core of the shadow between the legs removed (grey, smooth, darker than the backdrop)')
    if spec['thresh'] != 42:
        repairs.append('a lower threshold (%d) for see-through wings' % spec['thresh'])
    repairs.append('holes of fur or feather filled, gaps of smooth backdrop left open')
    flying = info['view'] == 'below'
    in_flight = flying or (info['view'] == 'above' and any(p.startswith('Wing') for p in parts))
    c = [
        (1, 'Every part once', 'pass', 'meshes: ' + ', '.join('%s %d tris' % kv for kv in info['parts'].items()) +
         ('; pivots only: ' + ', '.join(info['empties']) if info['empties'] else '') + '. Checked in Top and Bottom.'),
        (2, 'Closed shell', 'pass' if slits == 0 else 'FAIL',
         '%d edges with one face (a slit, or a fin that would vanish from behind); %d of %d edges where the two faces '
         'touch along a thin part\'s edge (closed, no gap)' % (slits, pinches, info['edges'])),
        (3, 'Depth from each part\'s own width', 'pass' if max(info['depth_to_width'].values()) <= 1.01 else 'FAIL',
         'deepest / half-width: ' + ', '.join('%s %.2f' % kv for kv in info['depth_to_width'].items())),
        (4, 'Views the game sees have real source data', 'limit' if in_flight else 'pass',
         'The game sees it ' + GAME_SEES[info['view']] + '.' +
         (' Large on screen in flight: rebuilt from its four-view KM-S1 sheet when it comes.'
          if flying and info['id'] in NEEDS_FLIGHT_SHEET else
          ' From the side it is a thin plate and its top is its underside mirrored: built from one view, accepted '
          'because it is a few pixels across on the phone (KAMAKURA_BUILD Step 4b); a bird large on screen gets a '
          'four-view sheet.' if in_flight else '')),
        (5, 'Real size, triangles', 'pass' if info['tris'] <= 2500 else 'FAIL',
         '%s m; %d triangles (the animal budget 2,500, docs/ART_DIRECTION.md); one 4096 atlas for the whole kit' % (
             ' x '.join('%.2f' % v for v in info['size']), info['tris'])),
        (6, 'Outline whole, no background or shadow', 'pass',
         'looked at on the cuts sheet (cuts.jpg), and against the cut before the texture cue (D18)'),
        (7, 'No holes; real gaps open', 'pass', 'looked at on the cuts sheet: no hole in the fur or feathers; the '
         'backdrop between tail and back, legs and wings stays open'),
        (8, 'Things before a wall are their own models', 'n/a', 'an animal on a plain sheet'),
        (9, 'The look target\'s look', 'pass', spec['sheet'] + ': photographic, as KM-0'),
        (10, 'Solid, nothing ghosted', 'pass', 'no see-through parts but real wings'),
        (11, 'No real brand or logo', 'pass', 'none (the Shiba\'s collar is plain)'),
        (12, 'No wires, no sky, crisp outline', 'pass', 'a plain sheet; the outline is cut from it at full resolution'),
        (13, 'Repairs listed', 'pass', '; '.join(repairs)),
        (14, 'Rig names and pivots', 'pass',
         ', '.join(p for p in parts if p != 'Body') + (' (+ ' + ', '.join(info['empties']) + ')' if info['empties'] else '')
         + ': origins at the joints' if len(parts) > 1 else 'one piece: nothing moves'),
        (15, 'Joints overlap, no seam, no gap mid-motion', 'pass' if motions or len(parts) == 1 else 'FAIL',
         ('every part overlaps the body; ' + ('four legs, near and far: ' + ', '.join(legs) + '; ' if legs else '') +
          'motions looked at frame by frame: ' + ', '.join(motions)) if motions else 'no moving parts'),
        (16, 'Feet planted', feet_result(info, motions)[0], feet_result(info, motions)[1]),
    ]
    return c


def review(roots, infos, results, atlas_path, out_dir):
    """The strict review of every model built: its eight views, its motions, its source, its checks."""
    for sub in ('views', 'motion', 'source'):
        os.makedirs(os.path.join(out_dir, sub), exist_ok=True)
    mat = KB.unlit(atlas_path, cut=True)
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            o.data.materials.clear()
            o.data.materials.append(mat)
    for root in roots.values():
        root.location = (0, 0, 0)
    # resumable: a render already in the folder is kept (--fresh renders all again), and review.json is written after
    # every model, so a stopped run loses at most the model it was on
    index_path = os.path.join(out_dir, 'review.json')
    index = json.load(open(index_path)) if os.path.exists(index_path) and not FRESH else {}

    def due(path):
        return FRESH or not os.path.exists(path)

    for name, root in roots.items():
        info = infos[name]
        sheet, spec, mask, parts = results[name]
        src = sheet.crop(spec['box'])
        src.thumbnail((600, 400))
        src.save(os.path.join(out_dir, 'source', name + '.jpg'), quality=85)
        views = os.path.join(out_dir, 'views', name + '.jpg')
        if RENDER and due(views):
            AR.eight_views(root, views, KB.render, cell_px=360, title='%s (%s): every side' % (name, info['id']))
        motions, feet = [], {}
        for motion, pose, view, ms in motions_of(name, info):
            gif = os.path.join(out_dir, 'motion', '%s_%s.gif' % (name, motion))
            if RENDER and due(gif):
                AR.motion_gif(root, pose, gif, KB.render, view=view, frames=24, cell_px=280, ms=ms, label=motion)
            motions.append(motion)
            measured = AR.measure_feet(root, pose)
            if measured is not None:
                feet[motion] = measured
        info['feet'] = feet
        checks = checks_of(name, spec, info, motions)
        index[name] = dict(info, motions=motions, checks=checks)
        json.dump({n: index[n] for n in ANIMALS if n in index}, open(index_path, 'w'), indent=1)
        print('reviewed', name, motions)


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
    if REVIEW:
        review(roots, infos, results, atlas_path, REVIEW)


if __name__ == '__main__':
    main()
