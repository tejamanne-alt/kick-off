# The Kamakura kit (kit_buildings.py --kit Kamakura): Kamakura's own homes (kit_buildings_kmhouse.py) and shops
# (kit_buildings_kmshop.py) on its own 4096 x 4096 atlas. See kit_buildings_kambase.py for the look and the contract.
from kit_buildings_kambase import *
import kit_buildings_kmhouse as KMH
import kit_buildings_kmshop as KMS

TILES = list(KMH.TILES) + list(KMS.TILES)


def paint(img, put):
    """The kit's own tiles (kit_buildings_atlas.paint calls this through EXTRA)."""
    pp = SG.put_pil
    KMH.paint(img, pp)
    KMS.paint(img, pp)


def pal_kam(pal):
    """The kit's SPECS rows (name, W, H, D, roof, builder, palette, front-map top, styles, extra maps)."""
    return KMH.rows(pal) + KMS.rows(pal)
