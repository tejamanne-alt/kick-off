# Blender character pipeline

The kid is modelled, textured, rigged and weighted by script in Blender (run as the
`bpy` Python module, no window needed), then exported to `Assets/_Game/Art/Models/Kid.fbx`.

```
python -m venv blenv && blenv/bin/pip install bpy==5.2.3
python face.py face.png                         # paints the face / atlas texture
blenv/bin/python kid.py -- $PWD/Kid.fbx          # builds Kid.blend and Kid.fbx (face.png next to kid.py)
python face.py face_adult.png --adult
blenv/bin/python kid.py -- $PWD/Adult.fbx --adult  # the adult pedestrians: long sleeves, trousers, adult proportions
blenv/bin/python render_kid.py -- $PWD/Kid.blend $PWD/preview.png BLENDER_EEVEE 500 600   # toon previews
cp Kid.fbx ../../Assets/_Game/Art/Models/Kid.fbx
cp face.png ../../Assets/_Game/Art/Models/KidAtlas.png
cp Adult.fbx ../../Assets/_Game/Art/Models/Adult.fbx
cp face_adult.png ../../Assets/_Game/Art/Models/AdultAtlas.png
blenv/bin/python teen.py -- $PWD/Boy.fbx --boy     # the playable teen boy (also paints BoyAtlas.png, writes Boy.json)
blenv/bin/python teen.py -- $PWD/Girl.fbx --girl   # the playable teen girl
blenv/bin/python review_teen.py -- $PWD/Girl.blend $PWD/girl_sheet.png   # review sheet: faces, poses, side, back, in-game size
cp Boy.fbx Boy.json BoyAtlas.png Girl.fbx Girl.json GirlAtlas.png ../../Assets/_Game/Art/Models/
```

The teens are original characters in a soft hand-painted anime style; Settings → Player picks
which one walks to school (both are built into each level, `CharacterChoice` shows one).
- Girl: chestnut high ponytail with a yellow scrunchie and a side-swept fringe, freckles, a
  sky-blue blouse with a rounded white collar, a navy pleated skirt, knee socks, loafers and a
  yellow backpack.
- Boy: short dark hair with a side parting, a quiff and a cowlick, a plaster on his cheek, a
  green ringer T-shirt, khaki shorts with turned-up hems, red sneakers and a navy backpack.
- Both faces are an oblong-oval: fairly straight sides from the cheekbones to the mouth, rounding
  into the chin (hers rounded, his softly squared).

The teens are built from modules on a shared `Part` contract (`teen_lib.py`): `teen_body.py`
(joints, a sculpted body, bones, teen proportions), `teen_outfit.py` (clothes, shoes, backpack,
the outfit colours), `teen_head.py` (the head and ears), `face_teen.py` (the painted face atlas)
and `teen_hair.py`. `teen.py` colours, rigs, joins and exports them; the `.json` it writes holds
the top, legwear and hair colours, which the level builder gives `ModelOutfit` as its defaults.

What the model carries:
- One skinned mesh, one material: vertex colours times the atlas (the face is painted in the
  atlas' upper-left quadrant; everything else samples its white corner).
- UV channel 2, x: the outfit part (0 skin and fixed parts, 1 shirt, 2 shorts or trousers, 3 hair) for `ModelOutfit`.
- Bones: Hips, Spine, Chest, Neck, Head, Upper/LowerLeg, Foot, Upper/LowerArm, Hand (.L/.R), Bag (the kid), and Nose, an unweighted marker in front of
  the face that tells the game which way the model faces.
  The game poses them in code (`CharacterRig`), measuring each swing from the bone's rest pose.

Rendering previews with Eevee needs EGL (on Debian/Ubuntu: `libegl1 libegl-mesa0 libgl1-mesa-dri`).

## Cars

Five original cars in a chunky, cozy style (`car.py`, previews with `review_car.py`): `hatch` (the
parked car; its body and cabin match the parked-car colliders), `wagon` (estate with roof-rack
cargo), `van`, `pickup` (a small cab-over truck with produce in the bed) and `fourby` (a compact
off-roader with a bull-bar, spare wheel and roof basket).

```
blenv/bin/python car.py -- $PWD/Hatch.fbx --type hatch       # also Wagon/Van/Pickup/Fourby
blenv/bin/python review_car.py -- $PWD/Hatch.blend $PWD/hatch_sheet.png
cp Hatch.fbx Hatch.json HatchAtlas.png ../../Assets/_Game/Art/Models/Cars/
```

Each car is one "Body" mesh plus four wheel meshes ("Wheel.FL/FR/RL/RR", origin at the hub, axle on
local X) and a "Front" marker at the front bumper. Vertex colours times the car's own atlas (panel
lines, grime, lights); body paint is part 1 in UV2 so `CarPaint` can repaint it. The `.json` holds
the base paint (sRGB, as in the FBX) and the wheel radius for `WheelSpin`.
