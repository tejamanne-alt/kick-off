# Shared base of Kamakura's own kits (kit_buildings.py --kit Kamakura / --kit KamakuraStreet): the buildings kit's helpers,
# Kamakura's materials, and a label painter for Japanese signs. The kits' modules (kit_buildings_kmhouse.py, the homes;
# kit_buildings_kmshop.py, the shops; kit_buildings_kamst.py, the temples and shrines, street things, the tram and vehicles)
# do `from kit_buildings_kambase import *`.
#
# The look is the user's brief for Kamakura (docs/IMAGE_PROMPTS.md, KAMAKURA; docs/ART_DIRECTION.md): a seaside temple town on
# the Shonan coast on a clear May morning; two-storey timber-and-mortar homes under grey glazed kawara or dark standing-seam
# metal roofs, dark-stained board fences, beige or white mortar, aluminium sliding windows with insect screens, futon rails,
# sliding entrance doors and name plates; shops with noren, hand-painted wooden signboards and paper lanterns; temples and
# shrines; concrete poles, mirrors, vending machines; weathering everywhere (silvered or blackened timber, salt bloom, moss on
# damp stone, rust on corrugated sheet, black mould under eaves, faded noren, cracked mortar). Every name is invented.
#
# Contract (as the rest of the buildings kit, kit_buildings.py): metres, Z up, the origin at the centre of the front's base,
# the street face looking along -Y, parts 1 wall / 2 accent / 3 roof; Attach.* empties (doors via door(..., name='Door')).
import math
import numpy as np
from mathutils import Vector
from kit_buildings_geo import *
from kit_buildings_parts import *
from kit_buildings_bits import *
from kit_buildings_town import (decal, flat_ac, paper_lantern, garden_pine, storefront, roller_shutter, hood, amado, ground_ac,
                                round_bin, bucket_flowers, town_shell)
import kit_buildings_signs as SG

# ---------------------------------------------------------------- Kamakura's own colours (registered into the kit's MAT)
KAM_MAT = {
    # timber: fresh cedar, weathered silver-grey, dark-stained / near black
    'kmcedar': (0, (0.70, 0.52, 0.36), 'white', 0.1), 'kmsilver': (0, (0.56, 0.54, 0.50), 'white', 0.25),
    'kmdark': (0, (0.20, 0.17, 0.15), 'white', 0.2),
    # mortar walls: beige, white, salt-bloomed grey
    'kmbeige': (0, (0.86, 0.80, 0.68), 'white', 0.15), 'kmwhite': (0, (0.92, 0.91, 0.88), 'white', 0.15),
    'kmgreyw': (0, (0.74, 0.74, 0.72), 'white', 0.2),
    # roofs: grey glazed kawara, dark standing-seam metal, corrugated sheet and its rust
    'kmkawara': (0, (0.36, 0.38, 0.42), 'white', 0.15), 'kmmetal': (0, (0.22, 0.24, 0.27), 'white', 0.1),
    'kmcorr': (0, (0.62, 0.63, 0.62), 'white', 0.25), 'kmrust': (0, (0.55, 0.30, 0.18), 'white', 0.3),
    # aluminium (window frames, rails), insect screen, noren indigo, vermilion, moss, stone
    'kmalu': (0, (0.74, 0.75, 0.75), 'white', 0.05), 'kmscreen': (0, (0.30, 0.32, 0.33), 'white', 0.0),
    'kmindigo': (0, (0.16, 0.22, 0.40), 'white', 0.1), 'kmvermil': (0, (0.84, 0.25, 0.14), 'white', 0.1),
    'kmmoss': (0, (0.34, 0.44, 0.22), 'white', 0.3), 'kmstone': (0, (0.62, 0.61, 0.57), 'white', 0.25),
    'kmstoned': (0, (0.44, 0.44, 0.41), 'white', 0.3), 'kmpaper': (0, (0.95, 0.92, 0.84), 'white', 0.1),
    'kmblock': (0, (0.70, 0.70, 0.68), 'white', 0.25), 'kmgreen': (0, (0.26, 0.48, 0.36), 'white', 0.1),
}
for _k, _v in KAM_MAT.items():
    if _k not in MAT:
        MAT[_k] = _v; MATS.append(_k); MID[_k] = len(MATS) - 1


def _c(rgb):
    return tuple(int(round(max(0.0, min(1.0, v)) * 255)) for v in rgb[:3])


def jp_label(dr, w, h, s, frac, ink, cx=0.5, cy=0.5, maxw=0.9, vertical=False):
    """Japanese lettering (IPA Gothic) centred at (cx, cy) of a tile, fitted to maxw of its width; vertical stacks the
    characters top to bottom (a hanging signboard)."""
    f = SG._font(SG.KANA, max(8, int(h * frac)))
    if f is None:
        return
    if vertical:
        n = max(1, len(s))
        size = int(min(h * 0.9 / n, w * 0.8))
        f = SG._font(SG.KANA, max(8, size))
        y0 = h * cy - size * n / 2
        for i, ch in enumerate(s):
            tw = dr.textlength(ch, font=f)
            dr.text((w * cx - tw / 2, y0 + i * size), ch, font=f, fill=_c(ink))
        return
    while dr.textlength(s, font=f) > w * maxw and f.size > 8:
        f = SG._font(SG.KANA, f.size - 2)
    tw = dr.textlength(s, font=f)
    dr.text((w * cx - tw / 2, h * cy - f.size * 0.55), s, font=f, fill=_c(ink))
