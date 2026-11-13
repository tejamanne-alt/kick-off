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
import re
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
      leg_width=0.06, peck=(25.0, 30.0), swim=None, flippers=None, outline=7.0, leg_area=(), leg_lines=None,
      leg_drop=(), leg_seeds=None, front_fins=(), curl=False, beat=None, beard=(), heel=False, keep_body=(),
      bob=None, hind=False, spine=False, grey_shadow=False):
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
    standing with its feet apart tips less, or its hind foot can't stay down), swim (a fish seen from above: the side its
    head is on, 'left' or 'right'; its rear becomes a Tail in links, swept as it swims), flippers (a turtle seen from
    above: its head's side; its four flippers become parts that paddle), outline (px between the mesh's outline points:
    wider for a model of many parts to keep it in budget; the alpha cut-out keeps the edge crisp).

    Legs drawn where the picture's can't be found by shape (D20; sheet px): leg_area (polygons: every pixel of the figure
    in them is a bird's bare leg or foot), leg_lines ((near, far): each a list of polylines, the leg from where it leaves
    the feathers to its foot and each toe; a pixel goes to the leg whose lines it lies nearest; far None: the near leg's
    copy stands for it, as when the two overlap all along), leg_drop (polygons taken out of the model: a leg raised
    mid-step, which can't plant), leg_seeds (a four-legged animal's group whose legs touch all the way down: {'B': (near
    lines, far lines or None)}, standing in for the pieces leg_masks seeds from; far None: the near leg's copy; a third
    entry True: the far leg found from its lines only to be taken out, the near leg's copy standing in, D21: the
    squirrel's far legs reach under its belly mid-stride, their thighs a patch of belly that swung out below it as a
    flap in a bound). front_fins (a fish's fins near the first cut
    of its tail: polygons kept whole with the body, not split across two links), curl (a tail curled over the back: it
    wags side to side about the body's long axis, never swung up and down in the picture's plane), beat (an insect's
    wingbeat, (middle, swing) degrees: FlitButterfly's beatMid and beatSwing; a butterfly's 38, 38 by default). beard
    (a cat: polygons under its chin where the backdrop between its whiskers was taken in as a grey block, D20: there
    every pixel of the backdrop's own neutral grey is cut out, and the strands left hanging opened away). heel (a bird
    whose picture shows a bare shank above the heel, the egret's: each drawn leg line's second point is the heel, where
    the leg bends; else the heel is where the bare leg leaves the feathers). keep_body (polygons of the body no part's
    overlap may grow into: the egret's back beside its head plumes, which would have turned with the head). bob (a bird
    on the ground: how far its head thrusts and holds with each step, as a share of its leg's length: a pigeon's head
    holds still in the air while its body walks under it, then thrusts forward, D21; None: a small nod only). hind (an
    insect whose hind wings beat apart from its forewings: a dragonfly's, D21). spine (a four-legged animal whose back
    flexes and stretches as it bounds: the squirrel's, D21: its rear half a bone of its own, Hips, carrying the hind legs
    and the tail). grey_shadow (an animal whose shadow lies close around its feet: low in the box, any pixel with no
    colour of its own is shadow, even where the paw beside it makes its window look textured; D21: the squirrel's feet
    carried pale shards of ground. Not for a grey or black animal, whose own fur is as neutral)."""
    return dict(id=cid, sheet=sheet, box=box, view=view, size=size, depth=depth, parts=list(parts), refine=refine,
                wings=wings, exclude=list(exclude), empties=list(empties), step=step, thresh=thresh, legs=legs,
                shadow=shadow, head_up=head_up, fill=list(fill), dark_shadow=dark_shadow, whiskers=whiskers,
                hop=hop, leg_width=leg_width, peck=peck, swim=swim, flippers=flippers, outline=outline,
                leg_area=list(leg_area), leg_lines=leg_lines, leg_drop=list(leg_drop), leg_seeds=leg_seeds,
                front_fins=list(front_fins), curl=curl, beat=beat, beard=list(beard), heel=heel,
                keep_body=list(keep_body), bob=bob, hind=hind, spine=spine, grey_shadow=grey_shadow)


ANIMALS = {
    # ---------------------------------------------------------------- KM-P4
    'KmCatSitting': A('KM-N01', P4, (500, 18, 858, 284), 'side', ('h', 0.38), 0.075,
                      [('Tail', [(500, 228), (600, 228), (630, 243), (645, 246), (649, 256), (649, 284), (500, 284)], (648, 262))],
                      whiskers=True),
    'KmCatWalking': A('KM-N01', P4, (21, 44, 443, 280), 'side', ('h', 0.30), 0.06,
                      [('Tail', [(21, 113), (112, 113), (102, 166), (66, 214), (21, 214)], (106, 137))],
                       legs=True, whiskers=True, beard=[[(398, 114), (432, 114), (432, 146), (398, 146)]], outline=9.0),
    'KmTanukiWalking': A('KM-N02', P4, (1409, 50, 1838, 281), 'side', ('h', 0.36), 0.09,
                         [('Tail', [(1409, 83), (1497, 91), (1497, 150), (1480, 196), (1472, 215), (1462, 248), (1409, 256)],
                           (1494, 128))],
                         refine=True, legs=True, step=19, outline=9.0),
    'KmTanukiSitting': A('KM-N02', P4, (1898, 31, 2280, 282), 'side', ('h', 0.40), 0.09,
                         [('Tail', [(1898, 204), (1990, 204), (2000, 215), (2003, 240), (2005, 273), (1898, 273)], (2002, 237))],
                         refine=True),
    'KmSquirrelRunning': A('KM-N03', P4, (11, 374, 450, 562), 'side', ('w', 0.40), 0.04,
                           [('Tail', [(11, 374), (148, 374), (144, 488), (11, 496)], (144, 450))], step=15, shadow=0.3,
                           dark_shadow=True, legs=True, spine=True, grey_shadow=True,
                           leg_seeds={'F': ([[(352, 480), (375, 505), (400, 522), (415, 530)]],
                                            [[(318, 495), (335, 515), (355, 530)]], True),
                                      'B': ([[(162, 488), (153, 510), (155, 532), (168, 537)]],
                                            [[(195, 500), (210, 512), (232, 520)]], True)}),
    'KmSquirrelSitting': A('KM-N03', P4, (523, 322, 837, 606), 'side', ('h', 0.30), 0.045,
                           [('Tail', [(523, 322), (676, 322), (676, 405), (652, 440), (652, 612), (523, 612)], (650, 594))],
                           fill=[[(659, 426), (650, 450), (642, 472), (637, 497), (636, 522), (638, 548), (654, 548),
                                   (653, 522), (654, 497), (659, 472), (667, 452), (676, 426)]]),
    'KmShibaStanding': A('KM-N04', P4, (1474, 314, 1808, 605), 'side', ('h', 0.58), 0.09,
                         [('Tail', [(1493, 340), (1586, 340), (1588, 420), (1493, 426)], (1570, 420)),
                          ('Head', [(1705, 314), (1808, 314), (1808, 433), (1728, 433)], (1734, 426))], legs=True,
                         step=22, outline=9.0, curl=True,
                         leg_seeds={'F': ([[(1683, 505), (1686, 545), (1692, 586)]], None),
                                    'B': ([[(1500, 500), (1492, 545), (1496, 585)]], [[(1548, 485), (1525, 530), (1519, 572)]])},
                         leg_drop=[[(1701, 568), (1712, 566), (1720, 571), (1720, 587), (1709, 587), (1706, 580),
                                    (1701, 576)]]),
    'KmShibaSitting': A('KM-N04', P4, (1940, 317, 2235, 601), 'side', ('h', 0.62), 0.09,
                        [('Tail', [(1943, 545), (1949, 524), (1962, 513), (1980, 509), (1996, 512), (2004, 521), (2001, 540),
                                   (1998, 560), (1993, 579), (1975, 586), (1954, 582), (1943, 566)], (1997, 550))],
                        curl=True),
    'KmKitePerched': A('KM-N05', P4, (89, 625, 358, 931), 'side', ('h', 0.75), 0.07,
                       [('Head', [(278, 625), (360, 625), (360, 700), (290, 712)], (290, 690))]),
    'KmCrowStanding': A('KM-N06', P4, (1426, 638, 1788, 919), 'side', ('w', 0.57), 0.06,
                        [('Head', [(1665, 638), (1781, 638), (1781, 700), (1726, 690), (1718, 718), (1712, 730), (1690, 734),
                                  (1676, 720), (1668, 690)], (1673, 712))], legs='biped',
                        leg_area=[[(1598, 856), (1630, 854), (1652, 884), (1695, 886), (1695, 906), (1598, 906)]],
                        leg_lines=([[(1622, 857), (1636, 875), (1646, 889)], [(1640, 892), (1686, 895)],
                                    [(1640, 896), (1688, 900)], [(1630, 893), (1606, 898)], [(1625, 898), (1612, 902)]],
                                   None, [[(1607, 857), (1620, 873), (1630, 886)]])),
    'KmCrowHopping': A('KM-N06', P4, (1882, 659, 2272, 910), 'side', ('w', 0.57), 0.06,
                       [('Head', [(2156, 659), (2272, 659), (2272, 733), (2178, 742)], (2170, 720))], legs='biped',
                       leg_area=[[(2078, 858), (2097, 855), (2128, 882), (2168, 884), (2168, 900), (2076, 900)]],
                       leg_lines=([[(2088, 858), (2105, 872), (2118, 885)], [(2118, 887), (2084, 891)],
                                   [(2118, 887), (2162, 891)]], None),
                       leg_drop=[[(2111, 826), (2156, 822), (2198, 834), (2198, 852), (2150, 868), (2118, 868),
                                  (2111, 848)]]),
    'KmPigeonStanding': A('KM-N07', P4, (76, 942, 359, 1218), 'side', ('w', 0.30), 0.05,
                          [('Head', [(269, 942), (356, 942), (356, 1013), (283, 1035)], (281, 1022))], refine=True,
                          legs='biped',
                          leg_area=[[(240, 1182), (246, 1176), (253, 1170), (258, 1166), (266, 1166), (274, 1180),
                                     (312, 1186), (312, 1208), (228, 1208), (228, 1192)]],
                          leg_lines=([[(246, 1176), (250, 1186), (256, 1194)], [(256, 1194), (236, 1198)],
                                      [(256, 1194), (298, 1201)], [(256, 1194), (272, 1204)]],
                                     [[(256, 1170), (262, 1180), (268, 1188)], [(268, 1188), (305, 1191)],
                                      [(262, 1186), (240, 1188)]])),
    'KmPigeonPecking': A('KM-N07', P4, (491, 1027, 847, 1203), 'side', ('w', 0.34), 0.05,
                         [('Head', [(778, 1068), (840, 1068), (840, 1171), (772, 1171)], (789, 1089))], refine=True,
                         shadow=0.3, dark_shadow=True, legs='biped', peck=(35.0, 18.0),
                         leg_area=[[(668, 1179), (676, 1172), (684, 1167), (692, 1164), (697, 1153), (714, 1151),
                                    (730, 1162), (745, 1168), (800, 1170), (800, 1196), (652, 1196), (652, 1182)]],
                         leg_lines=([[(683, 1166), (692, 1176), (700, 1185)], [(700, 1185), (660, 1180)],
                                     [(700, 1185), (738, 1187)], [(700, 1185), (712, 1193)]],
                                    [[(703, 1154), (712, 1163), (721, 1170)], [(721, 1171), (788, 1177)],
                                     [(718, 1169), (688, 1169)]])),
    'KmSparrowPerched': A('KM-N08', P4, (1443, 961, 1755, 1213), 'side', ('w', 0.15), 0.025,
                          [('Head', [(1648, 961), (1749, 961), (1749, 1052), (1718, 1060), (1690, 1060), (1672, 1045),
                                     (1662, 1018), (1650, 992)], (1680, 1052))], refine=True),
    'KmSparrowHopping': A('KM-N08', P4, (1898, 979, 2235, 1213), 'side', ('w', 0.15), 0.025,
                          [('Head', [(2125, 979), (2229, 979), (2229, 1030), (2190, 1040), (2180, 1062), (2160, 1068), (2142, 1060),
                                    (2132, 1040), (2125, 1015)], (2136, 1048))], refine=True,
                          legs='biped', hop=True,
                          leg_area=[[(2060, 1139), (2078, 1139), (2094, 1158), (2108, 1176), (2110, 1192), (2084, 1192),
                                     (2060, 1152)]],
                          leg_lines=([[(2068, 1141), (2078, 1152), (2088, 1166), (2100, 1178)]], None),
                          leg_drop=[[(2112, 1134), (2195, 1138), (2195, 1160), (2150, 1162), (2132, 1180), (2114, 1180),
                                     (2112, 1160)]]),
    'KmSparrowFlying': A('KM-N08', P4, (2359, 958, 2696, 1201), 'below', ('w', 0.21), 0.02, wings=0.09, refine=True),
    'KmSwallowPerched': A('KM-N09', P4, (0, 1255, 466, 1525), 'side', ('h', 0.22), 0.02,
                          exclude=[[(0, 1350), (122, 1365), (122, 1415), (0, 1400)],
                                   [(325, 1398), (466, 1412), (466, 1450), (325, 1435)]]),
    'KmSwallowFlying': A('KM-N09', P4, (466, 1265, 908, 1526), 'below', ('w', 0.33), 0.015, wings=0.07),
    'KmGullStanding': A('KM-N10', P4, (960, 1255, 1296, 1527), 'side', ('h', 0.34), 0.06,
                        [('Head', [(1180, 1255), (1290, 1255), (1290, 1310), (1245, 1312), (1242, 1336), (1222, 1345), (1200, 1342),
                                  (1188, 1325), (1182, 1300)], (1190, 1326))],
                        refine=True, legs='biped', leg_width=0.09,
                        leg_area=[[(1143, 1448), (1178, 1442), (1181, 1492), (1216, 1498), (1216, 1524), (1140, 1524)]],
                        leg_lines=([[(1153, 1447), (1155, 1475), (1156, 1505)], [(1156, 1506), (1200, 1511)],
                                    [(1156, 1506), (1185, 1518)], [(1156, 1506), (1148, 1512)]],
                                   [[(1166, 1444), (1167, 1475), (1170, 1499)], [(1170, 1500), (1208, 1504)],
                                    [(1170, 1500), (1190, 1500)]])),
    'KmEgretStanding': A('KM-N11', P4, (1939, 1238, 2225, 1535), 'side', ('h', 0.55), 0.05,
                         [('Plume', [(2038, 1272), (2075, 1266), (2100, 1257), (2113, 1257), (2113, 1274), (2082, 1299),
                                     (2038, 1299)], (2110, 1265)),
                          ('Head', [(2040, 1262), (2110, 1238), (2222, 1238), (2222, 1292), (2122, 1301), (2105, 1284),
                                    (2072, 1294), (2040, 1290)], (2127, 1292))],
                         legs='biped', peck=(40.0, 15.0), heel=True,
                         exclude=[[(2068, 1294), (2086, 1294), (2086, 1297), (2068, 1297)]],
                         keep_body=[[(2050, 1294), (2112, 1294), (2112, 1320), (2050, 1320)]],
                         leg_area=[[(2040, 1404), (2080, 1404), (2078, 1430), (2095, 1498), (2160, 1503), (2160, 1532),
                                    (2015, 1532), (2015, 1500), (2036, 1442)]],
                         leg_lines=([[(2058, 1405), (2047, 1440), (2050, 1505)], [(2050, 1508), (2088, 1522)],
                                     [(2050, 1508), (2068, 1520)], [(2050, 1508), (2025, 1512)]],
                                    [[(2073, 1405), (2065, 1440), (2085, 1504)], [(2086, 1507), (2150, 1515)],
                                     [(2086, 1507), (2120, 1513)], [(2086, 1507), (2066, 1511)]])),
    # ---------------------------------------------------------------- KM-P8
    'KmKoiRedWhite': A('KM-N12', P8, (21, 60, 428, 238), 'above', ('w', 0.60), 0.06, swim='right',
                       front_fins=[[(282, 104), (287, 80), (294, 67), (306, 70), (327, 99), (327, 104)],
                                   [(284, 179), (326, 177), (331, 200), (321, 231), (300, 233), (284, 210)]]),
    'KmKoiRedWhiteTurning': A('KM-N12', P8, (505, 48, 874, 238), 'above', ('w', 0.52), 0.06, swim='right',
                              front_fins=[[(714, 79), (732, 66), (762, 77), (786, 86), (790, 90), (776, 96), (750, 108),
                                           (730, 106)],
                                          [(797, 166), (810, 152), (822, 144), (832, 160), (836, 192), (830, 208),
                                           (812, 208), (798, 190)]]),
    'KmKoiGold': A('KM-N13', P8, (952, 68, 1355, 238), 'above', ('w', 0.55), 0.06, swim='left',
                   front_fins=[[(1050, 111), (1056, 90), (1070, 76), (1092, 74), (1100, 95), (1098, 111)],
                               [(1045, 185), (1095, 185), (1100, 210), (1088, 230), (1062, 231), (1046, 212)]]),
    'KmKoiGoldTurning': A('KM-N13', P8, (1408, 44, 1807, 256), 'above', ('w', 0.48), 0.06, swim='left',
                          front_fins=[[(1508, 96), (1512, 62), (1525, 50), (1550, 54), (1557, 80), (1552, 95)],
                                      [(1506, 178), (1556, 174), (1560, 200), (1550, 233), (1525, 236), (1506, 215)]]),
    'KmTurtleBasking': A('KM-N14', P8, (1867, 66, 2255, 237), 'side', ('w', 0.36), 0.05, refine=True),
    'KmTurtleSwimming': A('KM-N14', P8, (2327, 16, 2715, 274), 'above', ('w', 0.33), 0.035, refine=True,
                          flippers='right'),
    'KmHeronStanding': A('KM-N15', P8, (101, 303, 366, 609), 'side', ('h', 0.90), 0.07,
                         [('Head', [(212, 303), (363, 303), (363, 362), (228, 371), (212, 367)], (278, 359))], refine=True,
                         legs='biped',
                         leg_area=[[(172, 505), (183, 490), (200, 481), (216, 473), (225, 520), (262, 575), (345, 583),
                                    (345, 604), (140, 604), (140, 592), (172, 560)]],
                         leg_lines=([[(207, 476), (204, 516), (215, 586)], [(215, 588), (197, 592)],
                                     [(215, 588), (257, 590)], [(215, 588), (245, 598)]],
                                    [[(192, 483), (184, 512), (200, 579)], [(200, 581), (177, 584)],
                                     [(200, 581), (232, 582)]]), heel=True),
    'KmCormorantStanding': A('KM-N16', P8, (1011, 317, 1279, 604), 'side', ('h', 0.85), 0.07,
                             [('Head', [(1160, 317), (1273, 317), (1273, 369), (1168, 378)], (1177, 369))], refine=True),
    'KmCormorantDrying': A('KM-N16', P8, (1390, 323, 1822, 602), 'side', ('w', 0.95), 0.07, refine=True),
    'KmWagtail': A('KM-N17', P8, (2316, 345, 2684, 582), 'side', ('w', 0.21), 0.02,
                   [('Head', [(2550, 345), (2677, 345), (2677, 412), (2560, 423)], (2559, 410)),
                    ('Tail', [(2316, 490), (2445, 463), (2455, 475), (2455, 495), (2316, 520)], (2450, 482))],
                   refine=True, legs='biped', exclude=[[(2522, 544), (2561, 544), (2561, 553), (2522, 553)]],
                   leg_area=[[(2536, 500), (2556, 499), (2585, 545), (2620, 552), (2620, 570), (2518, 570), (2518, 545)]],
                   leg_lines=([[(2550, 503), (2561, 525), (2574, 549)], [(2572, 552), (2614, 559)],
                               [(2572, 556), (2600, 566)], [(2565, 556), (2541, 557)], [(2565, 559), (2542, 564)]],
                              None, [[(2540, 507), (2552, 528), (2565, 547)]])),
    'KmWhiteEyePerched': A('KM-N18', P8, (66, 651, 366, 932), 'side', ('w', 0.13), 0.015,
                           [('Head', [(258, 651), (362, 651), (362, 712), (318, 718), (312, 732), (296, 738), (280, 726),
                                      (270, 705), (262, 685)], (294, 730))]),
    'KmWhiteEyeFlying': A('KM-N18', P8, (509, 639, 863, 891), 'below', ('w', 0.18), 0.012, wings=0.08),
    'KmBulbulPerched': A('KM-N19', P8, (972, 640, 1277, 912), 'side', ('w', 0.28), 0.025,
                         [('Head', [(1160, 640), (1271, 640), (1271, 700), (1232, 705), (1228, 722), (1205, 730),
                                    (1180, 728), (1160, 712), (1150, 695)], (1195, 725))], refine=True),
    'KmBulbulFlying': A('KM-N19', P8, (1406, 626, 1806, 907), 'below', ('w', 0.40), 0.02, wings=0.07, refine=True,
                        # its tail fans out wider than its body: drawn from the base of its feathers, under the white
                        # puffs of its coverts (no narrowing finds it, D21)
                        parts=[('Tail', [(1550, 812), (1670, 812), (1670, 907), (1550, 907)], (1608, 812))]),
    'KmDoveStanding': A('KM-N20', P8, (1863, 647, 2225, 905), 'side', ('w', 0.33), 0.05,
                        [('Head', [(2142, 647), (2222, 647), (2222, 727), (2135, 738)], (2139, 722))], refine=True,
                        legs='biped', peck=(35.0, 18.0),
                        leg_area=[[(2062, 862), (2068, 856), (2085, 853), (2100, 851), (2108, 862), (2135, 868),
                                   (2158, 880), (2158, 893), (2050, 893), (2050, 872)]],
                        leg_lines=([[(2092, 856), (2098, 866), (2100, 876)], [(2100, 878), (2152, 885)],
                                    [(2100, 878), (2122, 889)], [(2100, 878), (2080, 885)]],
                                   [[(2072, 858), (2078, 866), (2082, 872)], [(2082, 873), (2056, 878)],
                                    [(2082, 873), (2128, 874)]])),
    'KmDoveFlying': A('KM-N20', P8, (2314, 646, 2731, 900), 'below', ('w', 0.53), 0.025, wings=0.08, refine=True),
    'KmCalicoWalking': A('KM-N21', P8, (12, 936, 438, 1220), 'side', ('h', 0.30), 0.06,
                         [('Tail', [(12, 1110), (30, 1112), (50, 1106), (70, 1100), (88, 1090), (100, 1076), (114, 1090),
                                    (100, 1112), (88, 1124), (72, 1136), (55, 1144), (35, 1142), (12, 1142)],
                           (106, 1088))],
                          refine=True, legs=True, whiskers=True, step=19, outline=9.0,
                          beard=[[(385, 1048), (408, 1048), (408, 1070), (385, 1070)]]),
    'KmCalicoAsleep': A('KM-N21', P8, (967, 965, 1337, 1206), 'side', ('w', 0.42), 0.09, refine=True, whiskers=True),
    'KmTuxedoWalking': A('KM-N22', P8, (1392, 969, 1801, 1216), 'side', ('h', 0.30), 0.06,
                         [('Tail', [(1392, 1012), (1479, 1012), (1479, 1063), (1423, 1166), (1392, 1166)], (1471, 1048))],
                          refine=True, legs=True, whiskers=True, outline=9.0),
    'KmTuxedoSitting': A('KM-N22', P8, (1872, 936, 2218, 1220), 'side', ('h', 0.38), 0.075,
                         [('Tail', [(1872, 1149), (1960, 1149), (1960, 1166), (1975, 1170), (1986, 1180), (1988, 1205),
                                    (1872, 1209)], (1985, 1186))],
                          refine=True, whiskers=True),
    'KmTuxedoLying': A('KM-N22', P8, (2308, 995, 2724, 1172), 'side', ('w', 0.60), 0.075,
                       [('Tail', [(2310, 1100), (2340, 1094), (2370, 1088), (2398, 1083), (2402, 1092), (2400, 1099), (2385, 1105),
                                  (2370, 1112), (2355, 1119), (2340, 1124), (2318, 1124), (2310, 1115)], (2398, 1092))],
                        refine=True, whiskers=True),
    'KmSwallowtail': A('KM-N25', P8, (961, 1248, 1334, 1531), 'above', ('w', 0.10), 0.003, wings=0.025, head_up=True),
    'KmDragonfly': A('KM-N26', P8, (1398, 1255, 1814, 1524), 'above', ('w', 0.07), 0.002, wings=0.025, head_up=True, thresh=14,
                     beat=(4.0, 24.0), hind=True),
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
    ground = np.zeros(m.shape, bool)
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
        if spec['grey_shadow']:     # beside a paw the window is textured by the paw, not by the pixel itself (D21): the
            # shadow and the backdrop showing between the feet, low down, without colour of their own
            ground = tall & (chroma < 8) & (lum > bg.mean() - 60) & (lum < bg.mean() + 15)
            shadow |= ground
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
    if ground.any():                # grey_shadow: the ground between the feet stays out however small its patch, or
        n, lab, st, _ = cv2.connectedComponentsWithStats(ground.astype(np.uint8), 8)    # the hole fill puts it back
        m[np.isin(lab, 1 + np.nonzero(st[1:, 4] >= 6)[0])] = 0
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
        m = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8)
    if spec['beard']:
        # under a cat's chin, the backdrop between its whiskers: neutral and within the backdrop's own range of grey
        # (lighter where the whiskers' glow lies on it), cut out; fur there has colour or is far brighter (D20)
        zone = _polys(spec['beard'], m.shape, x0, y0) > 0
        lum = r.mean(-1)
        m[zone & ((r.max(-1) - r.min(-1)) < 14) & (lum > bg.mean() - 10) & (lum < bg.mean() + 45)] = 0
        opened = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        m[zone] = opened[zone]
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
        m = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8)
    m[fill_pixels(spec, r)] = 1     # a narrow gap closed, painted with the fur around it (build inpaints it)
    if spec['leg_area']:
        # scaly toes: their pale highlights are as light as the backdrop and were cut away along their edges, so the
        # toes read as broken fragments (the crows', D20); within the drawn legs, gaps of up to 4 px are closed
        zone = _polys(spec['leg_area'], m.shape, x0, y0) > 0
        closed = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        m[zone & (closed > 0)] = 1
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


def _twin(masks, pivots, sides, feet, near, far, own=None):
    """The picture shows a pair of legs as one (one behind the other): the far leg is a copy of the near one, set
    behind the body. Hidden behind it at rest, it steps out of phase, so a foot is always down (D19: a bird on its one
    leg stood on nothing while that leg swung)."""
    for pre in ('Leg', 'Shin', 'Toe'):
        a, b = pre + near[3:], pre + far[3:]
        if a in masks:
            masks[b] = masks[a].copy()
            pivots[b] = pivots[a]
            if own is not None and a in own:
                own[b] = own[a].copy()
    sides[near], sides[far] = -1, 1
    feet[far] = feet[near]


def leg_masks(rest, biped=False, seeds=None, origin=(0, 0), own=None):
    """A walker's legs, from what is left of its figure once its tail and head are taken: each one a thigh (Leg..,
    pivoting at the hip or shoulder) and a shin (Shin.., pivoting at the knee), with the foot's contact point.

    The belly is the lowest row where one unbroken run of pixels still spans 35 % of the figure (20 % for a bird, its
    tail stretching the figure); below it, only legs. Each leg is seeded by the separate pieces in the lower two thirds
    of that region that reach down to within a quarter of a leg of the ground (so two legs touching at the top still
    part, and a paw lifted mid-step still counts), and every leg pixel goes to its nearest seed. A four-legged animal's
    front legs are those ahead of the torso's middle; a bird's two legs are one group. Of two in a group the larger is
    the near one (the right leg: the model's right flank faces the camera), the other the far one; a group of one is
    the near leg alone, at the body's middle.

    seeds: a group whose two legs touch all the way down, found as one piece and copied (the Shiba's: four legs each
    end, D20): {'F' or 'B': (near lines, far lines)}, polylines in sheet px (origin: the mask's corner on the sheet),
    seeding the group's two legs in place of the piece. A leg takes only what lies within two fifths of a leg's length
    of its seed: fur hanging between two legs stays the body's (D20: the tanuki's thighs took its whole belly, and
    their straight tops showed as steps across it when they turned).

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
    # a leg reaches the ground, or near it: a paw lifted mid-step still counts (the calico's far hind leg, 10 px up);
    # the tail is taken before legs are looked for
    keep = [i for i in range(1, n) if (lab == i).sum() >= 0.04 * region.sum()
            and np.nonzero(lab == i)[0].max() >= bottom - 0.25 * legh]
    if not keep:
        return none
    tx = np.nonzero(rest[:belly + 1])[1].mean()
    drawn = seeds or {}
    seed_lab = np.zeros((h, w), np.int32)
    info = {}                   # seed label: (group, its side if drawn)
    for i in keep:
        g = '' if biped else 'F' if np.nonzero(lab == i)[1].mean() >= tx else 'B'
        if g not in drawn:
            info[len(info) + 1] = (g, None)
            seed_lab[lab == i] = len(info)
    # a third entry True: the far leg is found from its lines only to take it out, and the near one is copied for it
    copy_far = {g for g, entry in drawn.items() if len(entry) > 2 and entry[2]}
    gone = np.zeros((h, w), np.uint8)
    for g, entry in drawn.items():
        near, far = entry[:2]
        for lines, side in ((near, 'R'), (far, 'L')):
            if not lines:               # no far leg drawn: the near one is copied for it
                continue
            canvas = np.zeros((h, w), np.uint8)
            for line in lines:
                cv2.polylines(canvas, [np.array([(x - origin[0], y - origin[1]) for x, y in line], np.int32)],
                              False, 1, 3)
            info[len(info) + 1] = (g, side)
            seed_lab[(canvas > 0) & (region > 0)] = len(info)
    src = np.where(seed_lab > 0, 0, 255).astype(np.uint8)
    dist, near_px = cv2.distanceTransformWithLabels(src, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    lut = np.zeros(int(near_px.max()) + 1, np.int32)
    zy, zx = np.nonzero(src == 0)
    lut[near_px[zy, zx]] = seed_lab[zy, zx]
    owner = lut[near_px] * (region > 0) * (dist <= 0.4 * legh)
    groups = {'': []} if biped else {'F': [], 'B': []}
    for i, (g, side) in info.items():
        m = (owner == i).astype(np.uint8)
        if m.any():
            groups[g].append((m, side))

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
    for g, found in groups.items():
        # drawn legs come near first; found ones, the larger is the near one
        found.sort(key=lambda t: (t[1] != 'R', -int(t[0].sum())) if t[1] else (0, -int(t[0].sum())))
        if g in copy_far:           # the far leg's pixels leave the model; the near leg's copy stands in (below)
            for m, side in found:
                if side == 'L':
                    gone |= m
            found = [t for t in found if t[1] != 'L']
        ms = [m for m, _ in found]
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
                if own is not None:
                    own[name] = (m & rest).astype(np.uint8)
            else:
                masks[name], masks[shin] = thigh.astype(np.uint8), lower_leg.astype(np.uint8)
                pivots[shin] = (knee_x, float(knee))
                if own is not None:     # each part's own pixels, without its reach into the one above (the weights')
                    own[name] = (m & above & rest).astype(np.uint8)
                    own[shin] = (m & (1 - above) & rest).astype(np.uint8)
            pivots[name] = (hip_x, belly - 0.3 * legh)
            sides[name] = sign
            fx = np.nonzero(m[max(0, foot_row - 2):foot_row + 1])[1]
            feet[name] = (float(fx.mean()), float(foot_row))
            paw = np.zeros_like(m)              # the paw: the lowest fifth of the leg, kept level at its wrist (_foot)
            paw[int(foot_row - 0.2 * legh):] = 1
            _foot(m, paw, rest, shin, 'Toe' + g + side, feet[name], 0.1 * legh, masks, pivots, name, own_px=own)
        if len(ms) == 1:
            _twin(masks, pivots, sides, feet, 'Leg' + g + 'R', 'Leg' + g + 'L', own)
    if own is not None and gone.any():
        own['_gone'] = (gone & rest).astype(np.uint8)
    return masks, pivots, sides, feet, belly


def bird_legs(rest, width=0.06, own=None):
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
        _bird_leg(m, rest, side, sign, masks, pivots, sides, feet, own=own)
    if len(legs) == 1:
        _twin(masks, pivots, sides, feet, 'LegR', 'LegL', own)
    core = np.zeros_like(rest)
    for m in legs:
        core |= m
    return masks, pivots, sides, feet, top, core


def _foot(m, toes, keep, shin, toe, foot, reach, masks, pivots, thigh=None, ankle=None, own_px=None):
    """A leg's foot as its own part, Toe.. under the shin, pivoting at the ankle (where it meets the shin), which the
    gait keeps level with the ground; the Foot point hangs under it (D20: a bird's long toes, rigid in its shin, tipped
    into the floor whenever the shin turned, by up to a fifth of its height; a paw by up to 3 %; and a tall paw kept
    level about its contact point sheared off the shin, so the joint is the ankle, like every other joint). toes: the
    foot's own pixels; they leave the shin, and the foot reaches up into the shin by reach px, so the ankle stays
    covered as the shin turns over it. ankle: the joint (x, y), else the middle of the foot's top row."""
    own = (m & toes).astype(np.uint8)
    if shin not in masks or own.sum() < 15:
        return
    k = 2 * max(2, int(round(reach))) + 1
    up = cv2.dilate(own, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) & masks[shin] & (1 - own)
    masks[toe] = ((own | up) & keep).astype(np.uint8)
    for part in (shin, thigh):              # nothing of the foot stays on a part that turns with the leg
        if part in masks:
            masks[part] = (masks[part] & (1 - own)).astype(np.uint8)
    if own_px is not None:
        own_px[toe] = (own & keep).astype(np.uint8)
        for part in (shin, thigh):
            if part in own_px:
                own_px[part] = (own_px[part] & (1 - own)).astype(np.uint8)
    if ankle is None:
        ys = np.nonzero(own)[0]
        top = int(ys.min())
        ankle = (float(np.nonzero(own[top:top + 3])[1].mean()), float(top))
    pivots[toe] = (float(ankle[0]), float(ankle[1]))


def _spread(m):
    """A thin leg's toes: the rows at its foot where it spreads wider than twice the leg above (an egret's)."""
    ys = np.nonzero(m)[0]
    if not len(ys):
        return np.zeros_like(m)
    t0, fb = int(ys.min()), int(ys.max())
    widths = m.sum(1)
    leg = np.median(widths[t0:t0 + max(1, int(0.7 * (fb - t0)))])
    top = fb
    while top > t0 and widths[top - 1] > 2 * leg:
        top -= 1
    rows = np.zeros_like(m)
    rows[max(t0, top - 1):fb + 1] = 1
    return rows


def _bird_leg(m, keep, side, sign, masks, pivots, sides, feet, toes=None, ankle_x=None, ankle=None, heel=None,
              own=None):
    """One bird's leg (m: its bare pixels), jointed as a bird's is (D20): the bare leg is one rigid bone, the tarsus,
    hinged at the heel where it leaves the feathers (the joint that bends backward); the thigh is a bone hidden in the
    body, from a hip up and forward of the heel, its mesh only the feathers over the heel. So: Shin.. the whole bare
    leg, pivoting at the heel; Leg.. that band of feathers, pivoting at the hip; the toes a level foot of their own at
    the ankle (_foot; toes: their pixels, else the rows where the leg spreads), the Foot point under them. Cutting the
    bare leg at its middle (a knee no bird has) left the leg straight at rest: to step, the pecking pigeon's body
    dipped half a leg and its knee folded to -127 degrees, laying the shin into the ground. keep: the pixels a reach
    may cover. ankle_x, ankle: the foot's contact and the ankle, where a drawn leg's line ends. heel: (x, y) where the
    leg bends, when the picture shows a bare shank above it (the egret's): the shank is the thigh's, the hip up the
    shank's line into the body, half the shank again above where it leaves the feathers."""
    w = m.shape[1]
    name, shin = 'Leg' + side, 'Shin' + side
    whole = m
    toes = _spread(m) if toes is None else toes
    fb_whole = int(np.nonzero(m)[0].max())
    tarsus = (m & (1 - toes)).astype(np.uint8)
    if tarsus.sum() >= 30:
        m = tarsus
    my = np.nonzero(m)[0]
    t0, fb = int(my.min()), int(my.max())
    L = max(4, fb - t0)

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

    feathers, top_x = band_above(m, t0, max(6, 0.3 * L))
    if heel is None:
        reach, _ = band_above(m, t0, max(4, 0.15 * L))
        # the hip: up and forward of the heel, inside the body (the thigh bone slants down and back to the heel). The
        # thigh's mesh is the feathered drumstick from the hip to the heel, so as it swings it stays joined to the body
        # (D20: a band of feathers over the heel alone floated off the belly mid-stride)
        hip = (top_x + 0.57 * L, t0 - 0.57 * L)
        # as thick as twice the bare leg (its median row, not its top, where the feathers may flare), at most a third
        # of the leg's length: a disc of belly swinging with the thigh would show (D20, the hopping sparrow's)
        widths = m.sum(1)
        bare = float(np.median(widths[widths > 0]))
        drum = np.zeros_like(m)
        cv2.line(drum, (int(round(top_x)), t0), (int(round(hip[0])), int(round(hip[1]))), 1,
                 int(max(6, min(2 * bare, 0.35 * L))))
        masks[name] = ((feathers | drum) & keep).astype(np.uint8)
        masks[shin] = ((m | reach) & keep).astype(np.uint8)
        pivots[shin] = (top_x, float(t0))
        pivots[name] = hip
        if own is not None:
            # the skin the thigh moves: only the feathers just over the heel, blended into the body (D21): skinned with
            # the whole drumstick, the heron's thigh dragged its breast feathers out below its body as it strode
            own[name] = (feathers & keep & (1 - m)).astype(np.uint8)
            own[shin] = (m & keep).astype(np.uint8)
    else:
        hx, hy = heel
        above = np.zeros_like(m)
        above[:int(hy) + 1] = 1
        lower = (m & (1 - above)).astype(np.uint8)
        reach, _ = band_above(lower, int(hy) + 1, max(4, 0.15 * (fb - hy)))
        masks[name] = (((m & above) | feathers) & keep).astype(np.uint8)
        masks[shin] = ((lower | (reach & m)) & keep).astype(np.uint8)
        pivots[shin] = (float(hx), float(hy))
        pivots[name] = (top_x + 0.3 * (top_x - hx), t0 - 0.3 * (hy - t0))
        if own is not None:     # the bare shank only: the breast feathers over it stay the body's (D21, the heron)
            own[name] = ((m & above) & keep).astype(np.uint8)
            own[shin] = (lower & keep).astype(np.uint8)
    sides[name] = sign
    fx = np.nonzero(whole[max(0, fb_whole - 2):fb_whole + 1])[1]
    feet[name] = (float(fx.mean()) if ankle_x is None else float(ankle_x), float(fb_whole))
    _foot(whole, toes, keep, shin, 'Toe' + side, feet[name], 0.08 * L, masks, pivots, None, ankle, own_px=own)


def _polys(polys, shape, x0, y0):
    """The pixels inside polygons given in sheet px, in a mask whose corner is the sheet's (x0, y0)."""
    m = np.zeros(shape, np.uint8)
    for poly in polys:
        cv2.fillPoly(m, [np.array([(x - x0, y - y0) for x, y in poly], np.int32)], 1)
    return m


def _line_dist(lines, shape, x0, y0):
    """Each pixel's distance from the nearest of polylines given in sheet px."""
    canvas = np.full(shape, 255, np.uint8)
    for line in lines:
        cv2.polylines(canvas, [np.array([(x - x0, y - y0) for x, y in line], np.int32)], False, 0, 1)
    return cv2.distanceTransform(canvas, cv2.DIST_L2, 5)


def drawn_legs(rest, spec, own=None):
    """A bird's legs as drawn on its sheet (D20), where bird_legs can't find them by their thinness: two legs touching
    all the way down (the gull's, the heron's: found as one, then copied, a bird on four legs), legs as thick as the
    disk (the pigeons', the dove's: only a toe was found), a leg raised mid-step (the hopping crow's and sparrow's, left
    in the body as a third). Every pixel of the figure in leg_area is a leg's: the one whose leg_lines it lies nearest;
    the far leg's lines None, the near leg is copied for it (_twin). leg_drop's pixels leave the model: a leg raised
    mid-step can't plant, and the standing leg's copy stands in for it. A third entry in leg_lines: the far leg's own
    lines, where it stands beside the near one all the way down (the standing crow's, the wagtail's two tarsi): its
    pixels leave the model and the near leg, with every toe, is copied for it, so each leg is one leg. Returns as bird_legs does; the core is every
    pixel the body gives up (the legs' and the dropped)."""
    x0, y0 = spec['box'][:2]
    shape = rest.shape
    drop = _polys(spec['leg_drop'], shape, x0, y0) & rest
    keep = (rest & (1 - drop)).astype(np.uint8)
    area = _polys(spec['leg_area'], shape, x0, y0) & keep
    near_lines, far_lines = spec['leg_lines'][:2]
    dn = _line_dist(near_lines, shape, x0, y0)
    if len(spec['leg_lines']) > 2:      # a far leg seen beside the near one, taken out: the near one's copy stands in
        hidden = area & (_line_dist(spec['leg_lines'][2], shape, x0, y0) < dn)
        drop = (drop | hidden).astype(np.uint8)
        area = (area & (1 - hidden)).astype(np.uint8)
        keep = (keep & (1 - hidden)).astype(np.uint8)
    ms = [(area & (dn <= (_line_dist(far_lines, shape, x0, y0) if far_lines else np.inf))).astype(np.uint8)]
    if far_lines:
        ms.append((area & (1 - ms[0])).astype(np.uint8))
        # each leg its connected whole: a piece of the far foot cut off by the near leg in front of it (the standing
        # pigeon's far back toe) would float as a fleck when the far foot steps (D20); it goes to the leg it touches
        for i in (0, 1):
            n, lab, st, _ = cv2.connectedComponentsWithStats(ms[i], 8)
            if n <= 2:
                continue
            main = 1 + int(np.argmax(st[1:, 4]))
            for j in range(1, n):
                if j == main:
                    continue
                piece = (lab == j).astype(np.uint8)
                ms[i] &= (1 - piece)
                if (cv2.dilate(piece, np.ones((3, 3), np.uint8)) & ms[1 - i]).any():
                    ms[1 - i] |= piece
                else:
                    drop = (drop | piece).astype(np.uint8)
    masks, pivots, sides, feet = {}, {}, {}, {}
    for m, lines, (side, sign) in zip(ms, (near_lines, far_lines), (('R', -1 if len(ms) > 1 else 0), ('L', 1))):
        # the foot: what lies nearer the toes' lines than the leg's own (the first line), and everything below the
        # ankle (the leg line's end): nothing of the shin hangs past the joint, or it dips as the shin turns
        toes = None
        if len(lines) > 1:
            below = np.zeros(shape, np.uint8)
            below[int(lines[0][-1][1] - y0) + 1:] = 1
            toes = ((_line_dist(lines[1:], shape, x0, y0) < _line_dist(lines[:1], shape, x0, y0)) | below).astype(np.uint8)
        heel = (lines[0][1][0] - x0, lines[0][1][1] - y0) if spec['heel'] and len(lines[0]) > 2 else None
        _bird_leg(m, keep, side, sign, masks, pivots, sides, feet, toes, lines[0][-1][0] - x0,
                  (lines[0][-1][0] - x0, lines[0][-1][1] - y0) if len(lines) > 1 else None, heel, own=own)
    if len(ms) == 1:
        _twin(masks, pivots, sides, feet, 'LegR', 'LegL', own)
    return masks, pivots, sides, feet, int(np.nonzero(rest)[0].min()), (area | drop).astype(np.uint8)


def _geodesic(mask, seed):
    """Each pixel's distance from seed (x, y) through the mask's own pixels (8-connected steps): how far along a curled
    tail or a bending fish a pixel lies. -1 where the mask doesn't reach."""
    h, w = mask.shape
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    if n > 2:       # start in the part's largest piece: a stray pixel nearer the seed would hold the walk to itself
        mask = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8)
    ys, xs = np.nonzero(mask)
    i = int(np.argmin((xs - seed[0]) ** 2 + (ys - seed[1]) ** 2))
    dist = np.full(mask.shape, -1, np.int32)
    front = np.zeros_like(mask)
    front[ys[i], xs[i]] = 1
    seen = front.copy()
    k, step = np.ones((3, 3), np.uint8), 0
    while front.any():
        dist[front > 0] = step
        grown = cv2.dilate(front, k) & mask & (1 - seen)
        seen |= grown
        front = grown
        step += 1
    return dist


def split_links(region, seed, starts, name, own=None):
    """A part cut into links along its length (D19): region's pixels by their distance from seed through the part
    (_geodesic), the links starting at the shares starts of its full length (the first at 0). Each link but the first
    reaches back into the one before by about half the part's thickness there, so no gap opens as it bends. Returns
    ([(link name, mask, pivot (x, y) in the mask's frame)], the distances); names: name, name2, name3..."""
    dist = _geodesic(region, seed)
    D = max(1, int(dist.max()))
    thick = float(cv2.distanceTransform(region, cv2.DIST_L2, 5).max())
    out = []
    bounds = [int(round(b * D)) for b in starts] + [D + 1]
    for k in range(len(starts)):
        lo, hi = bounds[k], bounds[k + 1]
        core = ((dist >= lo) & (dist < hi)).astype(np.uint8)
        if core.sum() < 15:
            continue
        band = (dist >= max(0, lo - 2)) & (dist <= lo + 2)
        bys, bxs = np.nonzero(band)
        pivot = (float(bxs.mean()), float(bys.mean())) if len(bys) else (float(seed[0]), float(seed[1]))
        if own is not None:     # the link's own pixels, without its reach back (the weights')
            own[name if k == 0 else name + str(k + 1)] = core.copy()
        if k > 0:       # reach back into the link before
            back = ((dist >= lo - max(3, int(0.6 * thick))) & (dist < lo)).astype(np.uint8)
            core = core | back
        out.append((name if k == 0 else name + str(k + 1), core.astype(np.uint8), pivot))
    return out, dist


def flipper_masks(mask, head):
    """A turtle's four flippers, seen from above: the thin parts of its figure outside the shell (opening the figure with
    a disk a fifth of its width leaves the shell), the four largest that are not its head or tail (the pieces at the two
    ends of its length). Front or back by where they sit along the length (head toward head), right or left across it
    (seen from above, head up the model's +X, its left the sheet's side above the length). Each pivots where it meets the
    shell. Returns {FlipperFR: (mask with its reach into the shell, pivot, its own pixels)...}."""
    ys, xs = np.nonzero(mask)
    fw = xs.max() - xs.min() + 1
    k = 2 * max(3, int(0.1 * fw)) + 1
    shell = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(shell, 8)
    if n < 2:
        return {}
    shell = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8)
    rest = (mask & (1 - shell)).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(rest, 8)
    cx, cy = np.nonzero(shell)[1].mean(), np.nonzero(shell)[0].mean()
    ax = 1.0 if head == 'right' else -1.0           # the length runs along the sheet's x
    pieces = sorted(range(1, n), key=lambda i: -st[i, 4])[:6]
    along = {i: (cen[i][0] - cx) * ax for i in pieces}
    ends = {max(pieces, key=lambda i: along[i]), min(pieces, key=lambda i: along[i])}   # the head and the tail
    flips = [i for i in pieces if i not in ends][:4]
    out = {}
    for i in flips:
        m = (lab == i).astype(np.uint8)
        g = 'F' if along[i] > 0 else 'B'
        sd = 'L' if cen[i][1] < cy else 'R'         # above the length on the sheet: its left
        near = cv2.dilate(shell, np.ones((5, 5), np.uint8)) & m
        py, px = np.nonzero(near) if near.any() else np.nonzero(m)
        # each reaches a little into the shell, so its root stays covered as it paddles
        reach = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))) & shell
        out['Flipper' + g + sd] = ((m | reach) & mask, (float(px.mean()), float(py.mean())), m)
    return out


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
    own = {'_drop': np.zeros_like(mask)}     # each part's own pixels, without its overlaps: the skin's weights (D21)
    taken = np.zeros_like(mask)
    solo = _polys(spec['keep_body'], mask.shape, x0, y0) & mask     # the body's alone: no part's overlap grows into
    #                                                                   it (keep_body; a koi's front fins, below)
    for name, poly, pivot in spec['parts']:
        pm = np.zeros_like(mask)
        cv2.fillPoly(pm, [np.array([(x - x0, y - y0) for x, y in poly], np.int32)], 1)
        pm &= mask & (1 - taken)
        parts[name], pivots[name] = pm, pivot
        own[name] = pm.copy()
        taken |= pm
    # a bird's head in two links (D21): its neck (Head, at the nape) and its head (Head2), so a peck or a look about
    # bends the neck and turns the head on it, the skin following, where one rigid piece swung from the nape
    if ('Head' in parts and spec['view'] == 'side' and spec['legs'] is not True and not spec['whiskers']
            and parts['Head'].any()):
        # the neck turns about its middle where it meets the body, as a real neck bends about its spine: about the nape
        # (the drawn pivot) the back of the head rose into a point as the head went down to peck (D21)
        hm = parts['Head']
        rest_of = (mask & (1 - hm)).astype(np.uint8)
        seam = hm & cv2.dilate(rest_of, np.ones((5, 5), np.uint8))
        sy_, sx_ = np.nonzero(seam)
        if len(sy_):
            pivots['Head'] = (x0 + float(sx_.mean()), y0 + float(sy_.mean()))
        px, py = pivots['Head']
        links, _ = split_links(parts['Head'], (px - x0, py - y0), (0.0, 0.3), 'Head', own)
        if len(links) > 1:
            for nm, m, pv in links:
                parts[nm] = m
                if nm != 'Head':
                    pivots[nm] = (x0 + pv[0], y0 + pv[1])
    # the body carries on under a drawn tail (below), never under a head: there the band ran up the neck's outline
    # and stood as a spike at the nape when the head turned (D20); a head's own overlap covers its neck seam
    drawn_parts = np.zeros_like(mask)
    for name in parts:
        if name.startswith('Tail'):
            drawn_parts |= parts[name]
    banded = set()
    if spec['legs']:
        rest = (mask & (1 - taken)).astype(np.uint8)
        # a leg (or a paw) taken out of the model: raised mid-step, or peeking out behind the near one where the far
        # leg is otherwise hidden (its copy stands in for it); it leaves the body too
        drop = _polys(spec['leg_drop'], mask.shape, x0, y0) & rest
        rest = (rest & (1 - drop)).astype(np.uint8)
        taken |= drop
        own['_drop'] |= drop
        biped = spec['legs'] == 'biped'
        below = np.zeros_like(mask)
        if biped:                       # a bird's bare legs leave the body; their reach into the feathers stays its
            if spec['leg_lines']:
                legs, lpiv, lsides, lfeet, belly, core = drawn_legs(rest, spec, own)
            else:
                legs, lpiv, lsides, lfeet, belly, core = bird_legs(rest, spec['leg_width'], own)
            below = core
            taken |= core               # a leg raised mid-step and taken out (leg_drop) leaves the body too
            legs_own = np.zeros_like(mask)
            for n in legs:
                if n in own and not n.startswith('Leg'):
                    legs_own |= own[n]
            own['_drop'] |= (core & (1 - legs_own)).astype(np.uint8)
        else:
            legs, lpiv, lsides, lfeet, belly = leg_masks(rest, seeds=spec['leg_seeds'], origin=(x0, y0), own=own)
            if belly is not None:
                # the body keeps a skirt below its belly, a sixth of the leg deep: a thigh turning off it shows fur
                # there, not the backdrop (D20)
                legh = int(np.nonzero(rest)[0].max()) - belly
                below[belly + 1 + int(0.15 * legh):] = 1
            gone = own.pop('_gone', None)
            if gone is not None:        # a far leg taken out for its copy (leg_seeds' third entry): below the skirt
                gone = (gone & below).astype(np.uint8)
                taken |= gone
                own['_drop'] |= gone
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
            if spec['head_up'] and pm.any():
                # an insect's wings end where the wings do, out from the body: the abdomen's edges below them (wider
                # than the body's half-width) stay the body's, or they flap (D21)
                wy = np.nonzero((pm & (np.abs(xx - cx) > 4.0 * bw)).any(1))[0]
                if len(wy):
                    pm[wy.max() + 3:] = 0
                    pm[:max(0, wy.min() - 3)] = 0
                # its antennae stay the body's too: thin strokes the wings' broad shapes don't reach
                broad = cv2.morphologyEx(pm, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
                pm = (pm & cv2.dilate(broad, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))).astype(np.uint8)
            root_x = x0 + cx + (bw if side[0, -1] else -bw)
            if spec['hind'] and pm.any():
                # a dragonfly's hind wing apart from its forewing (D21: they beat out of step): cut at the row where the
                # wing is narrowest near the body, between the two wings' roots (the head is up the sheet)
                # the wings overlap at their roots; out toward their tips the backdrop shows between them
                out_wing = pm & (np.abs(xx - cx) > 4.0 * bw)
                ry = np.nonzero(out_wing.any(1))[0]         # the wings' own rows (not the abdomen's, below them)
                lo, hi = int(ry.min() + 0.2 * (ry.max() - ry.min())), int(ry.min() + 0.8 * (ry.max() - ry.min()))
                counts = out_wing.sum(1)
                gap = lo + int(np.argmin(counts[lo:hi + 1]))
                hind = pm.copy()
                hind[:gap + 1] = 0
                pm[gap + 1:] = 0
                hname = 'Hind' + name[-1]
                hy = np.nonzero(hind & (np.abs(xx - cx) < 2.5 * bw))[0]
                parts[hname], own[hname] = hind, hind.copy()
                pivots[hname] = (root_x, y0 + (float(hy.min()) if len(hy) else gap + 1.0))
                taken |= hind
                fy = np.nonzero(pm & (np.abs(xx - cx) < 2.5 * bw))[0]
                shoulder_here = y0 + (float(np.median(fy)) if len(fy) else shoulder)
            else:
                shoulder_here = shoulder
            parts[name] = pm
            own[name] = pm.copy()
            pivots[name] = (root_x, shoulder_here)
            taken |= pm
    if spec['spine'] and spec['legs'] is True:
        # the rear half of the body (behind the middle between the shoulders and the hips) a bone of its own, so the
        # back flexes and stretches as it bounds (D21): pivoting on the back's centre line there
        fx = [pivots[n][0] for n in parts if n.startswith('LegF') and n in pivots]
        bx = [pivots[n][0] for n in parts if n.startswith('LegB') and n in pivots]
        if fx and bx:
            split = 0.5 * (np.mean(fx) + np.mean(bx)) - x0
            rest_body = (mask & (1 - taken)).astype(np.uint8)
            xx = np.arange(w)[None, :].repeat(h, 0)
            hips = (rest_body & (xx < split)).astype(np.uint8)
            col = np.nonzero(rest_body[:, int(split)])[0]
            if hips.sum() > 50 and len(col):
                parts['Hips'], own['Hips'] = hips, hips.copy()
                pivots['Hips'] = (x0 + split, y0 + 0.5 * (col.min() + col.max()))
                taken |= hips
    if spec['wings'] and spec['view'] == 'below' and 'Tail' not in parts:
        # a flying bird's tail a part of its own (D21): what lies behind its vent, where the body below the belly's
        # widest row narrows to under 55 % of it; a flat fan, tilting with each beat. A tail that fans out wider than
        # the body (the bulbul's) is drawn in its spec instead
        rest_body = (mask & (1 - taken)).astype(np.uint8)
        widths = rest_body.sum(1)
        rows = np.nonzero(widths)[0]
        if len(rows):
            lower = rows[rows > rows.min() + 0.35 * (rows.max() - rows.min())]
            widest = int(lower[np.argmax(widths[lower])]) if len(lower) else int(rows.max())
            vent = widest
            while vent < rows.max() and widths[vent] >= 0.55 * widths[widest]:
                vent += 1
            tail = rest_body.copy()
            tail[:vent] = 0
            if tail.sum() > 40:
                vx = np.nonzero(rest_body[vent])[0]
                parts['Tail'], own['Tail'] = tail, tail.copy()
                pivots['Tail'] = (x0 + float(vx.mean() if len(vx) else w / 2), y0 + float(vent))
                taken |= tail
    # tails and wings in links, a fish's rear as a tail in links, a turtle's flippers: not one rigid piece (D19)
    if 'Tail' in parts and spec['view'] == 'side':
        px, py = pivots['Tail']
        links, _ = split_links(parts['Tail'], (px - x0, py - y0), (0.0, 0.4, 0.7), 'Tail', own)
        if len(links) > 1:
            for nm, m, pv in links:
                parts[nm] = m
                if nm != 'Tail':
                    pivots[nm] = (x0 + pv[0], y0 + pv[1])
                    banded.add(nm)
    for wing in ('WingL', 'WingR'):         # a bird's wing bends at the wrist; an insect's doesn't
        if wing in parts and parts[wing].any() and not spec['head_up']:
            px, py = pivots[wing]
            links, _ = split_links(parts[wing], (px - x0, py - y0), (0.0, 0.5), wing, own)
            if len(links) > 1:
                for nm, m, pv in links:
                    parts[nm] = m
                    if nm != wing:
                        pivots[nm] = (x0 + pv[0], y0 + pv[1])
                        banded.add(nm)
    if spec['swim']:
        rest = (mask & (1 - taken)).astype(np.uint8)
        ys, xs = np.nonzero(rest)
        end = xs.max() if spec['swim'] == 'right' else xs.min()
        seed = (float(end), float(ys[xs == end].mean()))
        links, _ = split_links(rest, seed, (0.0, 0.45, 0.65, 0.82), 'Front', own)
        # a pectoral fin near the first cut stays whole with the body (D20: the cut, measured through the fish, ran
        # across the fins, and their outer halves swung with the tail as loose flecks)
        fins = _polys(spec['front_fins'], mask.shape, x0, y0) & rest
        solo |= fins
        # each pectoral fin its own part (D21: a koi sculls them), hinged where it meets the body
        cy = float(np.nonzero(rest)[0].mean())
        for poly in spec['front_fins']:
            fm = (_polys([poly], mask.shape, x0, y0) & rest).astype(np.uint8)
            if fm.sum() < 15:
                continue
            fy, fx = np.nonzero(fm)
            fname = 'FinL' if fy.mean() < cy else 'FinR'       # above the length on the sheet: its left (+Y)
            root = np.argsort(np.abs(fy - cy))[:max(3, len(fy) // 20)]
            parts[fname], own[fname] = fm, fm.copy()
            pivots[fname] = (x0 + float(fx[root].mean()), y0 + float(fy[root].mean()))
            taken |= fm
        links = [(nm, (m & (1 - fins)).astype(np.uint8) if k else (m | fins).astype(np.uint8), pv)
                 for k, (nm, m, pv) in enumerate(links)]
        own.pop('Front', None)
        for k, (nm, m, pv) in enumerate(links[1:]):
            name = 'Tail' if k == 0 else 'Tail' + str(k + 1)
            own[name] = (own.pop(nm) & (1 - fins)).astype(np.uint8)
            parts[name] = m
            pivots[name] = (x0 + pv[0], y0 + pv[1])
            if k > 0:
                banded.add(name)
            taken |= m & (1 - links[k][1])      # the tail's own pixels leave the body; its reach back stays the body's
    if spec['flippers']:
        rest = (mask & (1 - taken)).astype(np.uint8)
        for name, (m, pv, fown) in flipper_masks(rest, spec['flippers']).items():
            parts[name] = m.astype(np.uint8)
            own[name] = fown.astype(np.uint8)
            pivots[name] = (x0 + pv[0], y0 + pv[1])
            banded.add(name)
            taken |= fown               # its own pixels leave the body; its reach into the shell stays the shell's
    body = (mask & (1 - taken)).astype(np.uint8)
    if 'Head' in parts and parts['Head'].any():
        # the strip of body between a head's outline and the figure's edge (the back of the neck, where the drawn
        # outline runs inside the figure) is the head's: left in the body, it stood up as a spike at the nape whenever
        # the head turned (D20). Body within a third of the head's thickness of both the head and the edge.
        hm = parts['Head']
        D = max(3.0, 0.3 * float(cv2.distanceTransform(hm, cv2.DIST_L2, 5).max()))
        near_head = cv2.distanceTransform((1 - hm).astype(np.uint8), cv2.DIST_L2, 5) <= D
        near_edge = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5) <= D
        strip = (body > 0) & near_head & near_edge & (solo == 0)
        parts['Head'] = (hm | strip).astype(np.uint8)
        own['Head'] = (own['Head'] | strip).astype(np.uint8)
        body[strip] = 0
    if drawn_parts.any():
        # the body carries on under a drawn tail's edge, as far as the tail may sway off it: D20, the Shiba's rump
        # showed the backdrop through a slit under its curled tail
        fh = int(np.ptp(np.nonzero(mask)[0])) + 1
        k = 2 * max(2, int(round(0.03 * fh))) + 1
        body |= (cv2.dilate(body, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) & drawn_parts).astype(np.uint8)
    for name, pm in list(parts.items()):
        if name in banded or not pm.any():
            continue
        thick = float(cv2.distanceTransform(pm, cv2.DIST_L2, 5).max())
        k = 2 * int(round(max(3.0, 0.6 * thick))) + 1
        grown = cv2.dilate(pm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        parts[name] = (pm | (grown & body & (1 - solo))).astype(np.uint8)
    parts['Body'] = body
    pivots['Body'] = None
    own['Body'] = body.copy()
    return parts, pivots, sides, own


def relief(mask, step, outline=7.0):
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
        for s in np.arange(0, L[-1], outline):
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


def root_child(root, part):
    for o in root.children_recursive:
        if o.name.split('.', 1)[-1] == part:
            return o
    return None


def _parent_of(part):
    """The part a part hangs from: a shin from its thigh, a link (Tail3, WingL2) from the link before."""
    if part.startswith('Shin'):
        return 'Leg' + part[4:]
    if part.startswith('Toe'):
        return 'Shin' + part[3:]
    if part == 'Plume':             # a crest's long plumes hang from the head (the egret's: D21)
        return 'Head2'
    m = re.match(r'^(Tail|WingL|WingR|Head)(\d)$', part)
    if m:
        n = int(m.group(2))
        return m.group(1) if n == 2 else m.group(1) + str(n - 1)
    return None


def _depth(part):
    up, d = _parent_of(part), 0
    while up:
        d += 1
        up = _parent_of(up)
    return d


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
        if spec['swim'] == 'left' or spec['flippers'] == 'left':   # facing left: mirrored, its head +X as every model's
            return Vector(((ox - gx) / s, (oy - gy) / s, 0.0))
        return Vector(((gx - ox) / s, (oy - gy) / s, 0.0))

    depth_axis = Vector((0, 1, 0)) if view == 'side' else Vector((0, 0, 1))
    parts, pivots, sides, own = part_masks(spec, mask)
    biped = spec['legs'] == 'biped'
    # the far legs (behind the body: LegFL.., a bird's LegL) are a mesh of their own behind the body; every other part
    # is one continuous mesh with the body that bends at its joints (D21: rigid photo pieces turning over the body
    # showed their straight edges and corners at every joint, below the neck and at the tops of the legs)
    far_sfx = {n[3:] for n, sd in sides.items() if sd == 1 and n.startswith('Leg')}

    def suffix(p):
        return p[4:] if p.startswith('Shin') else p[3:] if p[:3] in ('Leg', 'Toe') else None

    def is_far(p):
        return p[:3] in ('Leg', 'Shi', 'Toe') and suffix(p) in far_sfx

    def parent(p):
        if p == 'Body':
            return None
        up = _parent_of(p) or 'Body'
        if up == 'Body' and 'Hips' in parts and (p == 'Tail' or p.startswith('LegB')):
            up = 'Hips'             # the back's rear half carries the hind legs and the tail (D21)
        return up

    bones = ['Body'] + sorted((p for p in parts if p != 'Body'), key=lambda p: (_depth(p), p))
    deform = [b for b in bones if b == 'Body' or (b in own and own[b].any())]
    gi = {b: i for i, b in enumerate(deform)}           # vertex group index of each deforming bone

    def thick(m):
        return 2.0 * float(cv2.distanceTransform(m.astype(np.uint8), cv2.DIST_L2, 5).max()) if m.any() else 0.0

    def blend(b):
        """The half-width (px) over which bone b and its parent share the skin at their joint: wide at a shoulder or a
        hip so the flank moves with the leg as a real one does, narrow at an ankle or a wing's root."""
        t = thick(own[b]) if b in own else 0.0
        if b.startswith('Leg'):
            return max(4.0, (0.6 if biped else 0.9) * t)
        if b.startswith('Shin'):
            return max(3.0, (0.6 if biped else 0.5) * t)
        if b.startswith('Toe'):
            sh = 'Shin' + b[3:]
            return max(2.0, 0.5 * thick(own[sh]) if sh in own else 2.0)
        if b == 'Head2':
            return max(3.0, 0.2 * t)
        if b.startswith('Head'):
            return max(4.0, 0.35 * t)
        if b.startswith('Tail'):
            return max(6.0, 0.6 * t) if spec['swim'] else max(4.0, 0.7 * t)
        if b.startswith('Wing'):
            return 3.0 if spec['head_up'] else max(4.0, (0.5 if b[-1] == '2' else 0.3) * t)
        if b == 'Hips':
            return max(6.0, 0.25 * t)
        if b.startswith('Flipper') or b.startswith('Fin'):
            return max(3.0, 0.4 * t)
        if b.startswith('Hind'):
            return 3.0
        return max(3.0, 0.4 * t)

    def weights(layer, members, pts):
        """Each point's bone weights (npts x len(deform)): every pixel of layer belongs to the deepest member bone whose
        own pixels hold it (the Body elsewhere); across each joint the two bones share it, half and half at the line
        between their pixels, fading to the one alone at the blend's width either side."""
        h, w = layer.shape
        lab = np.full((h, w), -1, np.int32)
        lab[layer > 0] = gi['Body']
        for b in sorted(members, key=lambda b: (_depth(b), b)):
            lab[(own[b] > 0) & (layer > 0)] = gi[b]
        present = [b for b in deform if (lab == gi[b]).any()]
        dist = {b: cv2.distanceTransform((lab != gi[b]).astype(np.uint8), cv2.DIST_L2, 5) for b in present}
        # a point just off the layer (a split triangle's centre) takes the nearest labelled pixel's bone
        src = np.where(lab >= 0, 0, 255).astype(np.uint8)
        _, near = cv2.distanceTransformWithLabels(src, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
        zy, zx = np.nonzero(src == 0)
        lut_y = np.zeros(int(near.max()) + 1, np.int32)
        lut_x = np.zeros(int(near.max()) + 1, np.int32)
        lut_y[near[zy, zx]], lut_x[near[zy, zx]] = zy, zx
        py = np.clip(np.round(pts[:, 1]).astype(int), 0, h - 1)
        px = np.clip(np.round(pts[:, 0]).astype(int), 0, w - 1)
        ny, nx = lut_y[near[py, px]], lut_x[near[py, px]]
        L = lab[ny, nx]
        W = np.zeros((len(pts), len(deform)), np.float32)
        W[np.arange(len(pts)), L] = 1.0
        children = {b: [c for c in present if parent(c) == b] for b in present}
        for b in present:
            sel = L == gi[b]
            if not sel.any():
                continue
            P = parent(b)
            if P in present:
                f = 0.5 * np.clip(1.0 - dist[P][ny[sel], nx[sel]] / blend(b), 0.0, 1.0)
                W[sel, gi[b]] -= f
                W[sel, gi[P]] += f
            for c in children[b]:
                g = 0.5 * np.clip(1.0 - dist[c][ny[sel], nx[sel]] / blend(c), 0.0, 1.0) * W[sel, gi[b]]
                W[sel, gi[b]] -= g
                W[sel, gi[c]] += g
        return W / np.maximum(W.sum(1, keepdims=True), 1e-6)

    def leg_share(W, far):
        """How much of each point is leg (near or far as asked): it stands that far out from the body's middle."""
        out = np.zeros(len(W), np.float32)
        for b, i in gi.items():
            if b[:3] in ('Leg', 'Shi', 'Toe') and is_far(b) == far and suffix(b) is not None:
                out += W[:, i] * (0.5 if (biped and b.startswith('Leg')) else 1.0)
        return out

    covered = np.zeros_like(mask)
    for b, m in own.items():
        if not b.startswith('_'):
            covered |= m
    # a bird's toes are built in the round (below): its photo's toes, a side view of a foot, were a flat plate from any
    # other angle, big and stuck to the ground (D21)
    def photo_part(b):
        return not (biped and b.startswith('Toe'))

    near_members = [b for b in deform if b != 'Body' and not is_far(b) and photo_part(b)]
    far_members = [b for b in deform if is_far(b) and photo_part(b)]
    main = own['Body'].copy()
    for b in near_members:
        main |= own[b]
    main |= (mask & (1 - covered) & (1 - own['_drop'])).astype(np.uint8)   # anything left over is body
    # the far legs' own pixels (a bird's: its bare legs, not the feathered drumstick, which is the body's texture) and a
    # short reach into the body, hidden behind it: with each part's whole reach up into the body, a far thigh carried a
    # patch of flank or breast that swung out in front of the animal (D21: the heron's, the user's "extended parts")
    fh = int(np.ptp(np.nonzero(mask)[0])) + 1
    far_layer = np.zeros_like(mask)
    for b in far_members:
        if biped and b.startswith('Leg') and not spec['heel']:     # the drumstick's feathers (with heel: bare shank)
            continue
        far_layer |= own[b]
    if far_layer.any():
        k = 2 * max(3, int(round(0.06 * fh))) + 1
        # into the body only: grown over a near leg beside it, the far leg dragged a ghost of that leg with it (D21)
        far_layer = (far_layer | (cv2.dilate(far_layer, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
                                  & own['Body']))
        far_layer = far_layer.astype(np.uint8)
    layers = [('Skin', main.astype(np.uint8), near_members, False)]
    if far_layer.any():
        layers.append(('SkinFar', far_layer.astype(np.uint8), far_members, True))

    root = bpy.data.objects.new(name, bpy.data.armatures.new(name))
    bpy.context.scene.collection.objects.link(root)
    tris_total, mesh_tris, open_edges, ratio, dominant = 0, {}, {}, {}, Counter()
    body_depth = 0.0
    built = []
    for mname, layer, members, far in layers:
        pts, tris, dist, radius = relief(layer, step, spec['outline'])
        W = weights(layer, members, pts)
        wing = np.zeros(len(pts), np.float32)
        for b, i in gi.items():
            if b.startswith('Wing') or b.startswith('Hind') or (b == 'Tail' and view == 'below'):
                wing += W[:, i]
        cap = spec['depth']
        d, R = np.maximum(dist - 1.0, 0.0) / s, np.maximum(radius - 1.0, np.maximum(dist - 1.0, 0.5)) / s
        dz_round = cap * np.tanh(np.sqrt(np.maximum(d * (2 * R - d), 0.0)) / cap)
        # a wing or a flying bird's tail is a thin, even plate, its edge rounded over a couple of pixels (D21: rounded
        # like a limb, each feather a ridge, the wings read as pleated fans and the tail as a ringed stub)
        dz_flat = 0.22 * cap * np.tanh(np.maximum(dist - 1.0, 0.0) / 2.5)
        wing = np.clip(wing, 0.0, 1.0)
        dz = (1.0 - wing) * dz_round + wing * dz_flat
        if not far:
            body_depth = float(np.max(dz[W[:, gi['Body']] > 0.9])) if (W[:, gi['Body']] > 0.9).any() else float(np.max(dz))
        off = (0.6 * body_depth * leg_share(W, True)) if far else (-0.6 * body_depth * leg_share(W, False))
        if view != 'side':
            off = np.zeros(len(pts), np.float32)
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new('UVMap')
        dl = bm.verts.layers.deform.verify()
        face_verts = {}
        for sign in (-1, 1):
            vs = []
            for i, p in enumerate(pts):
                v = bm.verts.new(to_model(p[0] + x0, p[1] + y0) + depth_axis * (sign * dz[i] + off[i]))
                for j in np.nonzero(W[i] > 1e-3)[0]:
                    v[dl][int(j)] = float(W[i, j])
                vs.append(v)
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
        open_edges[mname] = [sum(1 for e in bm.edges if len(e.link_faces) == 1),
                             sum(1 for e in bm.edges if len(e.link_faces) > 2)]
        ratio[mname] = round(float(np.max(dz) / max(np.max(R), 1e-6)), 2)
        for i in range(len(pts)):
            dominant[deform[int(np.argmax(W[i]))]] += 1
        me = bpy.data.meshes.new(name + '.' + mname)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name + '.' + mname, me)
        bpy.context.scene.collection.objects.link(o)
        for b in deform:                    # the groups in the deform layer's order
            o.vertex_groups.new(name=b)
        o.parent = root
        mod = o.modifiers.new('Armature', 'ARMATURE')
        mod.object = root
        KB.keep_uv_white(o)
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        mesh_tris[mname] = len(me.polygons)
        tris_total += len(me.polygons)
        built.append(o)

    if biped:
        # each foot's toes joined into the skin its leg is in (one skinned mesh, two with far legs: D21's budget)
        for far in (False, True):
            o = bird_toes(name, own, pivots, deform, is_far, body_depth, to_model, s, x0, y0, atlas, pos, far)
            if o is None:
                continue
            target = next((b for b in built if b.name.endswith('.SkinFar' if far else '.Skin')), built[0])
            n = len(o.data.polygons)
            with bpy.context.temp_override(active_object=target, object=target,
                                           selected_objects=[target, o], selected_editable_objects=[target, o]):
                bpy.ops.object.join()
            key = 'SkinFar' if target.name.endswith('.SkinFar') else 'Skin'
            mesh_tris[key] += n
            tris_total += n

    # the skeleton: a bone at each part's pivot, named as the part (the game's behaviours find them by name), every bone
    # pointing along +Y with no roll, so its rest frame is the model's own (turning a bone turns its part as turning the
    # part's mesh did); a Foot under each foot at its contact point and a Tip at the front of its toes (LegGait); the
    # pivots a behaviour wants without a part of their own (spec empties, a dog's missing far legs) as bones that hold
    # nothing
    feet = spec.pop('_feet', {})
    tips = {}
    for leg, foot in feet.items():
        t = 'Toe' + leg[3:]
        if t in own and own[t].any():
            fx_, fy_ = toe_front(own[t])
            tips[leg[3:]] = (x0 + fx_, y0 + fy_)
    extra = [(e, p, 'Body') for e, p in spec['empties'] + spec.pop('_auto_empties', [])]
    bpy.context.view_layer.objects.active = root
    root.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = root.data.edit_bones
    blen = max(0.005, 0.05 * spec['size'][1])          # drawn length only: a bone turns about its head

    def new_bone(bname, head, par, deforming):
        b = eb.new(bname)
        b.head = head
        b.tail = head + Vector((0.0, blen, 0.0))
        b.roll = 0.0
        b.use_deform = deforming
        if par is not None:
            b.parent = eb[par]
        return b

    new_bone('Body', Vector((0.0, 0.0, 0.0)), None, True)
    for b in bones[1:]:
        new_bone(b, to_model(*pivots[b]), parent(b), b in gi)
    for leg, foot in feet.items():
        sfx = leg[3:]
        holder = 'Toe' + sfx if 'Toe' + sfx in eb else 'Shin' + sfx if 'Shin' + sfx in eb else leg
        if holder in eb:
            new_bone('Foot' + sfx, to_model(*foot), holder, False)
            if sfx in tips and 'Toe' + sfx in eb:
                new_bone('Tip' + sfx, to_model(*tips[sfx]), 'Toe' + sfx, False)
    for ename, epiv, par in extra:
        if ename not in eb:
            new_bone(ename, to_model(*epiv), par, False)
    bpy.ops.object.mode_set(mode='OBJECT')
    root.select_set(False)
    for pb in root.pose.bones:
        pb.rotation_mode = 'XYZ'
    front = bpy.data.objects.new(name + '.Attach.Front', None)
    bpy.context.scene.collection.objects.link(front)
    front.parent = root
    front.location = (0, -1, 0)
    bpy.context.view_layer.update()
    head = {b.name: b.head_local.copy() for b in root.data.bones}

    def knee_to_end(sfx):           # the shin's bone: knee to ankle, or to the foot with no toe
        end = 'Toe' + sfx if 'Toe' + sfx in head else 'Foot' + sfx
        return (head[end] - head['Shin' + sfx]).length

    lengths = [(head['Shin' + n[3:]] - head[n]).length + knee_to_end(n[3:])
               for n in head if n.startswith('Leg') and 'Shin' + n[3:] in head and 'Foot' + n[3:] in head]
    lo = [min(v.co[k] for o in built for v in o.data.vertices) for k in range(3)]
    hi = [max(v.co[k] for o in built for v in o.data.vertices) for k in range(3)]
    info = dict(id=spec['id'], sheet=spec['sheet'], box=list(spec['box']), view=view, px_per_m=round(s, 1),
                tris=tris_total, meshes=mesh_tris, parts={b: dominant.get(b, 0) for b in deform},
                empties=[b.name for b in root.data.bones if not b.use_deform] + ['Attach.Front'],
                size=[round(hi[k] - lo[k], 3) for k in range(3)], open_edges=open_edges, depth_to_width=ratio,
                edges=sum(len(o.data.edges) for o in built),
                leg_length=round(sum(lengths) / len(lengths), 4) if lengths else None)
    return root, info, mask, {b: m for b, m in own.items() if not b.startswith('_')}


def toe_front(m):
    """The front of a foot's toes on the ground: the front-most pixel in the band at the foot's bottom (a third of the
    foot's height), not in its lowest rows only, which a back toe drawn lower than the front ones may hold alone (D21:
    the dove's far foot was planted on its back toe and walked backwards)."""
    ty, tx = np.nonzero(m)
    bottom = int(ty.max())
    band = ty >= bottom - max(3, int(0.35 * (bottom - int(ty.min()))))
    return float(tx[band].max()), float(bottom)


def bird_toes(name, own, pivots, deform, is_far, body_depth, to_model, s, x0, y0, atlas, pos, far=None):
    """A bird's feet in the round (D21): for each foot, three toes forward (straight ahead and spread 28 degrees either
    side) and one back, each a tapered tube from under the ankle to its claw, a little arched, lying on the ground; their
    lengths, thickness and the side they stand on come from the photo's toes, and each is mapped along the photo's toe
    (its scales and its dark claw) so it keeps the picture's colour. Weighted to the foot's Toe bone, they lift, curl
    and plant with it. Returns the mesh object, or None."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    dl = bm.verts.layers.deform.verify()
    gi = {b: i for i, b in enumerate(deform)}
    sides, sections = 6, 5
    made = False
    for t in [b for b in deform if b.startswith('Toe') and (far is None or is_far(b) == far)]:
        m = own.get(t)
        if m is None or m.sum() < 10:
            continue
        ty, tx = np.nonzero(m)
        bottom = int(ty.max())
        ax, ay = pivots[t][0] - x0, pivots[t][1] - y0          # the ankle, in the mask's frame
        low = ty >= bottom - max(3, int(0.35 * (bottom - int(ty.min()))))
        front, rear = toe_front(m)[0], float(tx[low].min())
        cols = np.bincount(tx)
        th = float(np.percentile(cols[cols > 0], 30)) if (cols > 0).any() else 3.0
        th = max(2.0, min(th, 0.5 * max(1.0, front - ax)))
        Lf = max(2.0, front - ax) / s
        Lh = min(max((ax - rear) / s if rear < ax else 0.4 * Lf, 0.3 * Lf), 0.6 * Lf)
        r0 = min(0.5 * th / s, 0.22 * Lf)
        yoff = (0.6 if is_far(t) else -0.6) * body_depth
        A = to_model(ax + x0, ay + y0)
        gz = to_model(ax + x0, bottom + y0).z      # this foot's own ground: a far foot is drawn higher (its Tip there)
        sy = bottom - th / 2.0                                   # the photo's toe runs along this row
        for yaw, L, sx0, sx1 in ((0.0, Lf, ax, front), (28.0, 0.8 * Lf, ax, front), (-28.0, 0.8 * Lf, ax, front),
                                 (180.0, Lh, ax, rear if rear < ax else ax - Lh * s)):
            a = math.radians(yaw)
            d = Vector((math.cos(a), math.sin(a), 0.0))
            up = Vector((0.0, 0.0, 1.0))
            side = d.cross(up)
            rings = []
            for k in range(sections + 1):
                u = k / sections
                c = Vector((A.x, yoff, gz)) + d * (L * u)
                # each toe leaves the ankle (where the leg ends) and reaches the ground within a fifth of its length,
                # then lies on it, arching a little, its claw down
                c.z = (gz + r0 * (1.0 - 0.55 * u) + 0.5 * r0 * math.sin(math.pi * u)
                       + max(0.0, A.z - gz - r0) * max(0.0, 1.0 - u / 0.2) ** 2)
                r = r0 * (1.0 - 0.65 * u)
                ring = []
                for j in range(sides):
                    ang = 2 * math.pi * j / sides
                    v = bm.verts.new(c + side * (r * math.cos(ang)) + up * (r * math.sin(ang)))
                    v[dl][gi[t]] = 1.0
                    ring.append((v, sx0 + (sx1 - sx0) * u, sy - 0.45 * th * math.sin(ang)))
                rings.append(ring)
            tipc = Vector((A.x, yoff, 0.0)) + d * (L * 1.06)
            tipc.z = gz + 0.25 * r0
            tip = bm.verts.new(tipc)
            tip[dl][gi[t]] = 1.0
            tip_uv = (sx1, sy)

            def face(vs):
                try:
                    f = bm.faces.new([v for v, _, _ in vs])
                except ValueError:
                    return
                for loop, (_, ux, uy) in zip(f.loops, vs):
                    loop[uvl].uv = atlas.uv(pos, ux, uy)

            for k in range(sections):
                for j in range(sides):
                    j2 = (j + 1) % sides
                    face([rings[k][j], rings[k][j2], rings[k + 1][j2], rings[k + 1][j]])
            for j in range(sides):
                face([rings[-1][j], rings[-1][(j + 1) % sides], (tip, tip_uv[0], tip_uv[1])])
            face(list(reversed(rings[0])))
            made = True
    if not made:
        bm.free()
        return None
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name + '.SkinToes')
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name + '.SkinToes', me)
    bpy.context.scene.collection.objects.link(o)
    for b in deform:
        o.vertex_groups.new(name=b)
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    return o


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
           'ShinL': (20, 60, 160), 'Tail2': (255, 200, 60), 'Tail3': (255, 235, 140), 'WingL2': (255, 120, 255),
           'WingR2': (200, 100, 240), 'FlipperFR': (0, 200, 180), 'FlipperFL': (0, 140, 120), 'FlipperBR': (0, 230, 230),
           'FlipperBL': (0, 160, 160)}
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


def part_map(sheet, spec, parts, out):
    """One model's parts on its picture at full size, each its own colour, outlined and named (D20: two legs in one
    part, a raised leg left in the body, a fin cut in two, all hidden at the cuts sheet's thumbnail size). Joints are
    white rings, feet red crosses."""
    x0, y0, x1, y1 = spec['box']
    photo = np.asarray(sheet.convert('RGB'))[y0:y1, x0:x1].astype(np.float32)
    over = photo * 0.3 + 60
    rng = np.random.RandomState(7)
    # the near legs drawn last: a far leg copied from the near one lies under it
    names = sorted(parts, key=lambda p: (p != 'Body', p[:3] in ('Leg', 'Shi', 'Toe') and p.endswith('R'), p))
    colours = {p: (np.array([150, 150, 150]) if p == 'Body' else rng.randint(60, 256, 3)) for p in names}
    for p in names:
        pm = parts[p] > 0
        over[pm] = photo[pm] * 0.4 + colours[p] * 0.6
    im8 = over.clip(0, 255).astype(np.uint8).copy()
    for p in names:
        cs, _ = cv2.findContours(parts[p].astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(im8, cs, -1, tuple(int(v) for v in colours[p]), 1)
    im = Image.fromarray(im8)
    sc = max(1, int(1000 / max(im.size)))
    im = im.resize((im.width * sc, im.height * sc), Image.NEAREST)
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 13)
    for p in names:
        ys, xs = np.nonzero(parts[p])
        if len(ys):
            d.text((xs.mean() * sc - 12, ys.mean() * sc - 7), p, fill=(255, 255, 255), font=font,
                   stroke_width=2, stroke_fill=(0, 0, 0))
    for (px, py), kind in spec.get('_joints', []):
        px, py, r = (px - x0) * sc, (py - y0) * sc, 4
        if kind == 'foot':
            d.line([(px - r, py - r), (px + r, py + r)], fill=(255, 0, 0), width=2)
            d.line([(px - r, py + r), (px + r, py - r)], fill=(255, 0, 0), width=2)
        else:
            d.ellipse([px - r, py - r, px + r, py + r], outline=(255, 255, 255), width=2)
    im.save(out, quality=88)


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


# how far each walking bird's head thrusts and holds with each step, as a share of its leg's length (D21): a pigeon's,
# a dove's and a wagtail's strongly; a heron's and an egret's as they stalk; a crow's and a gull's a little
HEAD_BOB = {'KM-N07': 0.16, 'KM-N20': 0.16, 'KM-N17': 0.16, 'KM-N15': 0.10, 'KM-N11': 0.10, 'KM-N06': 0.06,
            'KM-N10': 0.06}


# each small bird's beat in flight (WingStroke, D21): raised, beaten below level, folded at the wrist and swept back on
# the upstroke (degrees): a sparrow's and a white-eye's deep and well folded, a swallow's shallower and swept far back, a
# dove's deep and less folded
STROKE = {'KM-N08': (50.0, 40.0, 65.0, 20.0), 'KM-N09': (35.0, 32.0, 50.0, 28.0), 'KM-N18': (50.0, 40.0, 65.0, 20.0),
          'KM-N19': (45.0, 38.0, 60.0, 18.0), 'KM-N20': (55.0, 45.0, 45.0, 15.0)}


def head_bob_of(name, info):
    """GroundBird's headSlide for this bird (metres)."""
    spec = ANIMALS[name]
    share = spec['bob'] if spec['bob'] is not None else HEAD_BOB.get(info['id'], 0.0)
    return share * (info.get('leg_length') or 0.0)


def game_settings(name, info):
    """How the game moves a model (for the level builder; the review renders the same numbers, motions_of): the
    behaviour component and the settings that differ from its defaults. Parts in links (Tail2.., WingL2) and jointed
    legs (Shin.., Foot..) are found by name at run time (PartChain, LegGait); axes are the model's (side: its side
    axis, the swing seen from the game's camera; up: its vertical)."""
    spec, parts = ANIMALS[name], info['parts']
    legs = [p for p in parts if p.startswith('Leg')]
    bird = any(len(p) == 4 for p in legs)
    if 'Running' in name:           # TreeSquirrel: its dash, four legs and its back bounding
        return {'component': 'TreeSquirrel', 'tail': 'Tail', 'tailAxis': 'side', 'hips': 'Hips', 'hipsAxis': 'side',
                'legs': 'LegGait.Bound (its four legs and its back bound, D21)'}
    if legs and not bird:
        if spec['whiskers']:
            return {'component': 'WallCat', 'tail': 'Tail', 'tailAxis': 'side', 'legs': 'LegGait (tucked in a bound)'}
        # a tail curled over the back wags side to side about the body's long axis (D20)
        return {'component': 'Dog', 'tail': 'Tail', 'tailAxis': 'long' if spec['curl'] else 'side',
                'head': 'Head' if 'Head' in parts else None, 'legs': 'LegGait (walk into trot)'}
    if 'WingL' in parts:
        if info['view'] == 'below':
            up, down, fold, sweep = STROKE.get(info['id'], (45.0, 38.0, 55.0, 18.0))
            out = {'component': 'GroundBird (flying model) or SkyFlock', 'wings': ['WingR', 'WingL'], 'wingAxis': 'long',
                   'wingUp': up, 'wingDown': down, 'wingFold': fold, 'wingSweep': sweep, 'wingSweepAxis': 'up'}
            if 'Tail' in parts:     # GroundBird's flyingTail, tilting with each beat
                out.update(flyingTail='Tail', flyingTailAxis='side')
            return out
        out = {'component': 'FlitButterfly', 'wingL': 'WingL', 'wingR': 'WingR', 'wingAxis': 'long'}
        if spec['beat']:            # a dragonfly beats its wings about flat; a butterfly claps them up (the default)
            out.update(beatMid=spec['beat'][0], beatSwing=spec['beat'][1])
        if 'HindL' in parts:        # its hind wings ahead of its forewings (D21)
            out.update(hindL='HindL', hindR='HindR', hindLead=1.6)
        return out
    if spec['swim']:
        out = {'component': 'PondDuck', 'tail': 'Tail', 'tailAxis': 'up', 'tailSweep': 22, 'tailBeat': 1.6,
               'headRecoil': 0.15}
        if 'FinL' in parts or 'FinR' in parts:
            out.update(fins=[f for f in ('FinL', 'FinR') if f in parts], finAxis='up', finSweep=25, finBeat=0.8)
        return out
    if spec['flippers']:
        return {'component': 'PondDuck', 'flippers': ['FlipperFR', 'FlipperFL', 'FlipperBR', 'FlipperBL'],
                'flipperAxis': 'up', 'flipperSweep': 28, 'flipperStroke': 0.9}
    if bird and info['id'] not in ON_A_ROCK:
        turn, tip = spec['peck']
        bob = head_bob_of(name, info)
        out = {'component': 'GroundBird', 'head': 'Head', 'headAxis': 'side', 'hopper': bool(spec['hop']),
               'headSlide': round(bob, 4), 'headNod': 2 if bob >= 0.1 * (info.get('leg_length') or 0.0) else 5,
               'peckTurn': turn, 'peckTip': tip, 'legs': 'LegGait (stepped, hopped, planted; feet rolled)'}
        if 'Tail' in parts:
            out.update(tail='Tail', tailAxis='side', tailPump=14, tailPumpRate=3)
        if 'Plume' in parts:        # a crest's plumes hang from the head (D21)
            out.update(plume='Plume', plumeAxis='side')
        return out
    if 'Tail' in parts and info['view'] == 'side':
        if 'Squirrel' in name:
            return {'component': 'TreeSquirrel', 'tail': 'Tail', 'tailAxis': 'side'}
        if spec['whiskers'] and 'Sitting' in name:
            return {'component': 'WallCat', 'tail': 'Tail', 'tailAxis': 'side'}
        amp, speed = (15.0, 6.0) if 'Shiba' in name else (12.0, 1.2) if spec['whiskers'] else (8.0, 1.0)
        return {'component': 'CritterIdle', 'motions': [{'part': 'Tail', 'axis': 'long' if spec['curl'] else 'side',
                                                          'amplitude': amp, 'speed': speed}]}
    if 'Head' in parts:
        amp, speed = (14.0, 0.7) if info['id'] in ON_A_ROCK else (22.0, 0.9)
        return {'component': 'CritterIdle', 'motions': [{'part': 'Head', 'axis': 'up', 'amplitude': amp, 'speed': speed,
                                                          'snap': True}]}
    return {'component': None, 'note': 'still: nothing of it moves'}


FRAME_MS = 30           # the shortest frame a GIF shows reliably; a quicker motion is shown slowed, and says so


def _timed(motion, pose, view, period, label=None):
    """A motion at its real speed over 24 frames, or slowed to FRAME_MS a frame (its label says how much)."""
    ms = period * 1000.0 / 24
    slow = max(1, math.ceil(FRAME_MS / ms))
    return (motion, pose, view, int(round(ms * slow)), (label or motion) + ('  x1/%d' % slow if slow > 1 else ''))


def motions_of(name, info):
    """The motions a model is shown in (docs/ASSET_REVIEW.md, section 2): each the game's own behaviour for it (the
    catalogue in docs/KAMAKURA_BUILD.md), ported (asset_review.py), at its real speed. Returns (motion, pose, view,
    frame ms, label)."""
    spec = ANIMALS[name]
    parts, view = info['parts'], info['view']
    h = max(info['size'][2], 0.02) if view == 'side' else max(info['size'][0], 0.02)
    span = max(info['size'][1], 0.02)
    legs = [p for p in parts if p.startswith('Leg')]
    bird = any(len(p) == 4 for p in legs)                   # LegR / LegL: a bird's two
    L = info.get('leg_length') or 0.45 * h
    cat = spec['whiskers']
    if 'Running' in name:           # TreeSquirrel's dash: long bounds, its legs and back bounding (D21)
        pose, period = AR.dash(h)
        return [_timed('dash', pose, None, period)]
    if legs and not bird:
        # Dog (and the walkers that use LegGait): a walk at 0.5 m/s for a cat, 0.8 for the dog and the tanuki; a trot
        # at 2 m/s; the cycle as long as the planted feet need not to skate
        walk_v, run_v = (0.5 if cat else 0.8), 2.0
        tw = AR.GAITS['walk']['stride'] * L / (walk_v * AR.GAITS['walk']['duty'])
        tr = AR.GAITS['trot']['stride'] * L / (run_v * AR.GAITS['trot']['duty'])
        if cat:     # WallCat's tail on the move: 3 + 17 (..), 3.2 radians a second
            wag_w = wag_r = (17.0, 3.0, 3.2 / (2 * math.pi))
        elif 'Shiba' in name:   # Dog: 25 degrees, 8 radians a second walking, 13 dashing
            wag_w, wag_r = (25.0, 0.0, 8 / (2 * math.pi)), (25.0, 0.0, 13 / (2 * math.pi))
        else:       # the tanuki's brush swaying with its gait
            wag_w = wag_r = (10.0, 0.0, 6 / (2 * math.pi))
        axis = 'x' if spec['curl'] else 'y'         # a curled tail sways about the long axis (D20)
        out = [_timed('walk', AR.gait('walk', h, tail=wag_w, period=tw, tail_axis=axis), None, tw),
               _timed('run', AR.gait('trot', h, tail=wag_r, period=tr, tail_axis=axis), None, tr)]
        if cat:
            pose, period = AR.bound(h)
            out.append(_timed('bound', pose, None, period))
        return out
    if 'WingL' in parts:
        if view == 'below':         # GroundBird's take-off flight, 40 degrees at 15 radians a second
            up, down, fold, sweep = STROKE.get(info['id'], (45.0, 38.0, 55.0, 18.0))
            pose, period = AR.flight(span, up, down, fold, sweep)
            return [_timed('fly', pose, AR.UP_BELOW, period)]
        # FlitButterfly: beatMid + beatSwing sin, 50 radians a second (a butterfly's 38 + 38 sin; a dragonfly's about flat)
        mid, swing = spec['beat'] or (38.0, 38.0)
        return [_timed('fly', AR.fly(span, mid, swing, 1.6), AR.INSECT, 2 * math.pi / 50)]
    if spec['swim']:                # PondDuck's koi: the tail swept 22 degrees, 1.6 times a second; fins and recoil
        pose, period = AR.pond(tail=(22.0, 1.6), recoil=0.15,
                               fins=(25.0, 0.8) if ('FinL' in parts or 'FinR' in parts) else None)
        return [_timed('swim', pose, AR.UP_ABOVE, period)]
    if spec['flippers']:            # PondDuck's turtle: the flippers paddled 28 degrees, 0.9 strokes a second
        pose, period = AR.pond(flippers=(28.0, 0.9))
        return [_timed('swim', pose, AR.UP_ABOVE, period)]
    if bird and info['id'] not in ON_A_ROCK:
        turn, tip = spec['peck']
        peck = _timed('peck', AR.peck(h, turn, tip, 0.22 / 0.45), None, 0.22 / 0.45)   # GroundBird's 0.22 s peck, a pause
        pump = (14.0, 0.0, 3.0) if 'Tail' in parts else None                  # a wagtail's tail: 14 degrees, 3 a second
        if spec['hop']:             # GroundBird's hopper: one crouch-spring-land every 2 pi / 18 s
            return [_timed('hop', AR.hop(h), None, 2 * math.pi / 18), peck]
        tw = 4 * math.pi / 15       # GroundBird's walk: phase 15 radians a second, a stride every two nods
        bob = head_bob_of(name, info)
        nod = 2.0 if bob >= 0.1 * L else 5.0
        return [_timed('walk', AR.gait('step', h, head_nod=nod, tail=pump, period=tw, bob=bob), None, tw), peck]
    if 'Tail' in parts and view == 'side':
        if 'Squirrel' in name:      # TreeSquirrel sitting up: its tail flicked
            pose, period = AR.flick()
            return [_timed('flick', pose, None, period)]
        if cat and 'Sitting' in name:   # WallCat sitting: 1.6 radians a second
            pose, period = AR.swish(1.6)
            return [_timed('swish', pose, None, period)]
        # CritterIdle: the Shiba sitting wags, a lying cat or a sitting tanuki swishes slowly
        amp, speed = (15.0, 6.0) if 'Shiba' in name else (12.0, 1.2) if cat else (8.0, 1.0)
        pose, period = AR.critter('Tail', 'x' if spec['curl'] else 'y', amp, speed)
        return [_timed('idle', pose, None, period)]
    if 'Head' in parts:             # CritterIdle: a perched bird, or one on its rock, looking about
        amp, speed = (14.0, 0.7) if info['id'] in ON_A_ROCK else (22.0, 0.9)
        pose, period = AR.critter('Head', 'z', amp, speed, snap=True)
        return [_timed('idle', pose, None, period)]
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
        (1, 'Every part once', 'pass', 'skinned meshes: ' + ', '.join('%s %d tris' % kv for kv in info['meshes'].items()) +
         '; bones: ' + ', '.join(info['parts']) +
         ('; marker bones: ' + ', '.join(info['empties']) if info['empties'] else '') + '. Checked in Top and Bottom.'),
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
         + ': bones at the joints, each named as the behaviour finds it' if len(parts) > 1 else 'one piece: nothing moves'),
        (15, 'Joints overlap, no seam, no gap mid-motion', 'pass' if motions or len(parts) == 1 else 'FAIL',
         ('one skin bending at every joint, the bones sharing it across each (D21: no part edge to show); ' +
          ('legs, near and far: ' + ', '.join(legs) + '; ' if legs else '') +
          'motions looked at frame by frame, full size: ' + ', '.join(motions)) if motions else 'no moving parts'),
        (16, 'Feet planted', feet_result(info, motions)[0], feet_result(info, motions)[1]),
        (17, 'Each part holds only itself', 'pass', parts_note(spec, info)),
    ]
    return c


def parts_note(spec, info):
    """What check 17 looked at: the model's part map (parts/<Model>.jpg) at full size, part by part (D20)."""
    parts = [p for p in info['parts'] if p != 'Body']
    if not parts:
        return 'one piece: looked at on its part map'
    said = ['looked at on its part map at full size, part by part: ' + ', '.join(parts)]
    copied = info.get('copied', [])
    if copied:
        why = ('the far leg, reaching under the belly mid-stride (its thigh a patch of belly, a flap when it swings), '
               'taken out' if spec['leg_seeds'] and any(len(e) > 2 and e[2] for e in spec['leg_seeds'].values()) else
               'the far leg, beside the near one all the way down in the picture, taken out' if
               spec['leg_lines'] and len(spec['leg_lines']) > 2 else
               'the leg raised mid-step in the picture taken out: it can\'t plant' if spec['leg_drop'] and
               spec['legs'] == 'biped' else
               'the far leg shows only as a paw behind the near one: the paw taken out' if spec['leg_drop'] else
               'the picture shows one leg where the other is hidden behind it')
        said.append('%s a copy of the near leg, set behind (%s)' % (', '.join(copied), why))
    elif any(p.startswith('Leg') for p in parts):
        said.append('every leg the picture shows is its own part, its own pixels only')
    if spec['leg_lines'] or spec['leg_seeds']:
        said.append('legs drawn on the sheet where their shape couldn\'t part them')
    if spec['front_fins']:
        said.append('the pectoral fins kept whole with the body')
    if spec['curl']:
        said.append('the curled tail sways about the long axis; the rump carries on under it')
    return '; '.join(said)


def review(roots, infos, results, atlas_path, out_dir):
    """The strict review of every model built: its eight views, its motions, its source, its checks."""
    for sub in ('views', 'motion', 'source', 'parts'):
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
        part_map(sheet, spec, parts, os.path.join(out_dir, 'parts', name + '.jpg'))
        info['copied'] = [b for a, b in (('LegR', 'LegL'), ('LegFR', 'LegFL'), ('LegBR', 'LegBL'))
                          if a in parts and b in parts and np.array_equal(parts[a], parts[b])]
        views = os.path.join(out_dir, 'views', name + '.jpg')
        if RENDER and due(views):
            AR.eight_views(root, views, KB.render, cell_px=360, title='%s (%s): every side' % (name, info['id']))
        motions, feet = [], {}
        for motion, pose, view, ms, label in motions_of(name, info):
            gif = os.path.join(out_dir, 'motion', '%s_%s.gif' % (name, motion))
            if RENDER and due(gif):
                AR.motion_gif(root, pose, gif, KB.render, view=view, frames=24, cell_px=280, ms=ms, label=label)
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
    for name in infos:
        infos[name]['game'] = game_settings(name, infos[name])
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
