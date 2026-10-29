# The teens' clothes, shoes and bag. Base space: see teen_lib.
import bpy, math
from mathutils import Vector
from teen_lib import C, Part, new_obj, activate, apply_mods, bake, smooth, finish, shell, shade
from teen_body import arm_dist

# Outfit colours the game needs to know (ModelOutfit's defaults): the part 1 and part 2 colours.
def palette(girl):
    return {
        'skin': (1.0, 0.89, 0.8, 1) if girl else (0.97, 0.83, 0.71, 1),
        'top': (0.86, 0.4, 0.42, 1) if girl else (0.97, 0.97, 0.95, 1),      # part 1
        'legwear': (0.86, 0.4, 0.42, 1) if girl else (0.24, 0.28, 0.38, 1),  # part 2
    }

# The Bag bone (base space): head at the top edge of the bag, tail toward its bottom.
def bag_bone(girl):
    return (0, 0.1, 1.02), (0, 0.13, 0.9)


def skin_color(girl):
    """The body's colour (bare skin; socks are painted onto the legs here)."""
    skin = palette(girl)['skin']; sock = (0.97, 0.97, 0.98, 1)
    return lambda co, c: sock if (girl and co.z < 0.3) else skin


def build_outfit(girl, body):
    pal = palette(girl)
    top_col, leg_col = pal['top'], pal['legwear']
    parts = []
    if girl:
        dress = shell(body, 'Dress', lambda c: c.z < 1.245 and ((c.z > 0.84 and abs(c.x) < 0.14) or arm_dist(c, girl) < 0.1), 0.012,
                      lambda c: 0.01 if (abs(c.x) > 0.13 and arm_dist(c, girl) > 0.06) else 0)
        finish(dress); parts.append(Part(dress, top_col, 1))
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=1, depth=1, end_fill_type='NOTHING', location=(0, 0.005, 0.76))
        skirt = C.object; skirt.name = 'Skirt'; bake(skirt)
        for v in skirt.data.vertices:
            t = max(0, min(1, (0.93 - v.co.z) / 0.35))
            v.co.x *= 0.118 + 0.09 * t; v.co.y = (v.co.y - 0.005) * (0.092 + 0.075 * t) + 0.005
            v.co.z = 0.93 - 0.35 * t
        skirt.modifiers.new('sub', 'SUBSURF').levels = 1
        so = skirt.modifiers.new('solid', 'SOLIDIFY'); so.thickness = 0.008; so.offset = 1
        finish(skirt); parts.append(Part(skirt, lambda co, c: shade(leg_col, 0.85) if co.z < 0.6 else leg_col, 2, 'Hips'))
        bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.1, location=(0, 0.005, 0.93))
        belt = C.object; belt.scale = (0.125, 0.098, 0.14); belt.name = 'Belt'
        finish(belt); parts.append(Part(belt, (0.8, 0.66, 0.42, 1), 0, 'Hips'))
    else:
        shirt = shell(body, 'Shirt', lambda c: c.z < 1.245 and ((c.z > 0.9 and abs(c.x) < 0.14) or arm_dist(c, girl) < 0.27), 0.013,
                      lambda c: 0.006 if (abs(c.x) > 0.13 and arm_dist(c, girl) > 0.22) else 0)
        finish(shirt); parts.append(Part(shirt, top_col, 1))
        trousers = shell(body, 'Trousers', lambda c: c.z > 0.07 and c.z < 0.96 and abs(c.x) < 0.135, 0.016)
        finish(trousers); parts.append(Part(trousers, lambda co, c: shade(leg_col, 0.8) if co.z < 0.1 else leg_col, 2))
        for s in (1, -1):   # the rolled cuffs
            a = Vector((s * 0.172, 0, 0.95)); b = Vector((s * 0.178, 0, 0.75)); p = a + (b - a) * 0.12
            bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.047, depth=0.045, location=p)
            cuff = C.object; cuff.rotation_euler = (b - a).to_track_quat('Z', 'Y').to_euler(); cuff.name = 'Cuff'
            b2 = cuff.modifiers.new('b', 'BEVEL'); b2.width = 0.01; b2.segments = 2
            finish(cuff); parts.append(Part(cuff, top_col, 1))
    # Collar: a soft band round the neck.
    bpy.ops.mesh.primitive_torus_add(major_radius=0.056, minor_radius=0.013, location=(0, 0.004, 1.245))
    collar = C.object; collar.scale = (1, 0.92, 0.85); collar.name = 'Collar'
    finish(collar); parts.append(Part(collar, (0.97, 0.95, 0.92, 1) if girl else top_col, 0 if girl else 1))

    # Shoes
    shoe, sole = ((0.42, 0.26, 0.18, 1), (0.25, 0.16, 0.12, 1)) if girl else ((0.3, 0.31, 0.35, 1), (0.95, 0.95, 0.95, 1))
    for s, n in ((1, 'L'), (-1, 'R')):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(s * 0.078, -0.03, 0.045)); sh = C.object
        sh.scale = (0.085, 0.2, 0.085 if girl else 0.09); bake(sh)
        b = sh.modifiers.new('b', 'BEVEL'); b.width = 0.035; b.segments = 3; sh.modifiers.new('s', 'SUBSURF').levels = 1
        finish(sh)
        for v in sh.data.vertices:
            f = max(0, (-0.03 - v.co.y) / 0.1)
            if f > 0: v.co.z = v.co.z * (1 - 0.3 * f)
        parts.append(Part(sh, lambda co, c: sole if co.z < 0.025 else shoe, 0, 'Foot.' + n))

    # A canvas satchel on the back of the hip, its strap over the shoulder and across the chest.
    bag_col = (0.66, 0.5, 0.32, 1)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.0, 0.13, 0.9)); bag = C.object; bag.scale = (0.24, 0.07, 0.19); bag.name = 'Bag'
    b = bag.modifiers.new('b', 'BEVEL'); b.width = 0.03; b.segments = 3
    finish(bag); parts.append(Part(bag, lambda co, c: bag_col if co.y > 0.1 or co.z < 0.95 else shade(bag_col, 0.85), 0, 'Bag'))
    curve = bpy.data.curves.new('strap', 'CURVE'); curve.dimensions = '3D'; curve.extrude = 0.016
    spl = curve.splines.new('NURBS')
    path = [(0.11, 0.12, 0.98), (0.13, 0.1, 1.12), (0.1, 0.03, 1.255), (0.0, -0.11, 1.12), (-0.11, -0.1, 0.98), (-0.13, 0.0, 0.9), (-0.11, 0.11, 0.95)]
    spl.points.add(len(path) - 1)
    for p, c in zip(spl.points, path): p.co = (c[0], c[1], c[2], 1)
    spl.use_endpoint_u = True; spl.order_u = 3
    strap = new_obj('Strap', curve); activate(strap); bpy.ops.object.convert(target='MESH')
    strap.modifiers.new('solid', 'SOLIDIFY').thickness = 0.006
    finish(strap); parts.append(Part(strap, shade(bag_col, 0.75), 0))
    return parts
