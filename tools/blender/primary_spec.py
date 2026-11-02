# The four primary-school kids: who they are, in one table. primary.py builds one of them with the
# teen pipeline (teen_build.py): the teen modules take a teen_lib.Variant where they take the teens'
# `girl` flag, and hand it on to the primary_* modules that know the younger body, the uniform and
# the faces.
#
#   PrimaryBoy   boy 1: fair, short black hair with a straight fringe; navy shorts, a yellow
#                neckerchief, a blue randoseru
#   PrimaryGirl  girl 1: fair, dark-brown twin tails with red ties and a fringe; navy pleated skirt,
#                a red bow, a red randoseru
#   PrimaryBoy2  boy 2: tanned, chestnut tousled spiky hair, round glasses; grey shorts, a red
#                neckerchief, a green randoseru
#   PrimaryGirl2 girl 2: medium-brown skin, a black bob with a yellow hairband; a grey pinafore
#                (jumper skirt), a yellow bow, a purple randoseru
#
# Colours are sRGB (0..1), what you would pick on screen; lin() makes Blender's linear values.
import math
from teen_lib import Variant


def lin(c):
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c[:3])


# The school uniform's colours as the shop's School Uniform recolours to them (the teens use the same)
SHIRT_WHITE = (0.9695, 0.9695, 0.9898)
NAVY = (0.2195, 0.2313, 0.4196)
GREY = (0.47, 0.49, 0.53)

NAMES = ('PrimaryBoy', 'PrimaryGirl', 'PrimaryBoy2', 'PrimaryGirl2')

# How tall each stands in the game (metres, hair included). The game scales a model so that its Head bone sits at
# the neck height it is given (LevelBuildKit.BuildModelCharacter: the teen boy's 1.5 stands 1.73 m), so a build
# prints the neck height that gives its kid this height (about 1.04 to 1.08 for these).
HEIGHT = {'PrimaryBoy': 1.30, 'PrimaryGirl': 1.27, 'PrimaryBoy2': 1.34, 'PrimaryGirl2': 1.29}

SPECS = {
    'PrimaryBoy': dict(
        girl=False, lift=0.08, build='boy',
        skin=(0.953, 0.776, 0.639), top=SHIRT_WHITE, legwear=NAVY, accent=(0.98, 0.78, 0.18), hair=(0.075, 0.07, 0.085), hair_shine=(0.30, 0.30, 0.38),
        garment='shorts', accessory='neckerchief', bag_colour=(0.16, 0.34, 0.74), hair_style='crop', face='boy1',
        shoe=(0.93, 0.94, 0.96), sole=(0.55, 0.58, 0.66), sock_high=False),
    'PrimaryGirl': dict(
        girl=True, lift=0.045, build='girl',
        skin=(0.976, 0.800, 0.690), top=SHIRT_WHITE, legwear=NAVY, accent=(0.86, 0.17, 0.22), hair=(0.20, 0.115, 0.09), hair_shine=(0.46, 0.31, 0.25),
        garment='skirt', accessory='bow', bag_colour=(0.80, 0.10, 0.14), hair_style='twin', face='girl1',
        shoe=(0.40, 0.24, 0.16), sole=(0.22, 0.15, 0.12), sock_high=True),
    'PrimaryBoy2': dict(
        girl=False, lift=0.14, build='boy',
        skin=(0.722, 0.502, 0.357), top=SHIRT_WHITE, legwear=GREY, accent=(0.86, 0.17, 0.22), hair=(0.40, 0.235, 0.12), hair_shine=(0.66, 0.46, 0.26),
        garment='shorts', accessory='neckerchief', bag_colour=(0.10, 0.52, 0.34), hair_style='spiky', face='boy2',
        shoe=(0.62, 0.64, 0.68), sole=(0.30, 0.31, 0.35), sock_high=False, glasses=(0.10, 0.075, 0.07)),
    'PrimaryGirl2': dict(
        girl=True, lift=0.08, build='girl',
        skin=(0.80, 0.60, 0.45), top=SHIRT_WHITE, legwear=GREY, accent=(0.98, 0.78, 0.18), hair=(0.06, 0.05, 0.07), hair_shine=(0.30, 0.28, 0.37),
        garment='pinafore', accessory='bow', bag_colour=(0.52, 0.28, 0.72), hair_style='bob', face='girl2',
        shoe=(0.13, 0.12, 0.15), sole=(0.30, 0.28, 0.30), sock_high=False),
}


def make(name):
    """The Variant for one of NAMES."""
    s = dict(SPECS[name])
    girl = s.pop('girl')
    V = Variant(name, girl, **s)
    V.hscale = (1.0, 1.0, 1.0)         # the head keeps the size it is modelled at (teen_body.head_scale)
    V.k = 0.76                         # a primary kid's limbs are about this much of a teen's: scales the teens' skin-weight widths
    V.skin_lin = lin(V.skin)
    V.head_width = 1.0                 # (primary_head.shape: a wider or narrower face)
    # build_body: the polygonising cell, the triangle budgets (uniform pass, skin hidden by clothes,
    # skin covered only at rest), the neck's, and where the thinned-out legs get their rings back
    V.cell = 0.0056
    V.body_tris = (2700, 300, 300)
    V.neck_tris = 320
    V.ear_seg = (14, 6)
    V.refine_zone = dict(knee=0.11, hip_below=0.10, hip_above=0.04)
    V.refine_len = 0.04
    return V
