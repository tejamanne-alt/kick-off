# What the placement code needs to know about the kit models without importing them (pure Python): the footprint and
# height of each one, from the kits' manifests (Assets/_Game/Art/Models/<Kit>/<Kit>.json, Cars/<Name>.json).
# Models face -Y, their origin is on the ground at the middle of the front; sizes are metres.
import os, json

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', '_Game', 'Art', 'Models'))
_cache = {}


def _manifest(kit):
    if kit not in _cache:
        if kit == 'Cars':
            _cache[kit] = None
        else:
            _cache[kit] = json.load(open(os.path.join(MODELS_DIR, kit, kit + '.json'), encoding='utf-8'))['models']
    return _cache[kit]


def bounds(kit, name):
    """(xmin, xmax, ymin, ymax, height) in metres."""
    if kit == 'Cars':
        d = json.load(open(os.path.join(MODELS_DIR, 'Cars', name + '.json'), encoding='utf-8'))
        return (-d['width'] / 2, d['width'] / 2, -d['length'] / 2, d['length'] / 2, d['height'])
    m = _manifest(kit)[name]
    return (m['min'][0], m['max'][0], m['min'][1], m['max'][1], m['max'][2])


def width(kit, name):
    b = bounds(kit, name)
    return b[1] - b[0]


def depth(kit, name):
    b = bounds(kit, name)
    return b[3] - b[2]


def door_x(kit, name):
    """Where the front door is along the front wall, in metres from the model's middle (0 if the model has none)."""
    if kit == 'Cars':
        return 0.0
    m = _manifest(kit)[name]
    for d in m.get('doors', []):
        if d.get('name') in ('Door', 'Shopfront', 'Shutter', 'RollerDoor', 'GarageDoor'):
            return float(d['center'][0])
    return 0.0
