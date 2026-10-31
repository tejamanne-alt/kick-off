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
blenv/bin/python review_teen.py -- $PWD/Girl.blend $PWD/girl_sheet.png [--bg shot1.png,shot2.png,shot3.png]
    # review sheet with the game's toon shading: faces, poses, side, back, and the teen at in-game
    # size (215 px tall, in-game outline) standing and running in front of game screenshots
cp Boy.fbx Boy.json BoyAtlas.png Girl.fbx Girl.json GirlAtlas.png ../../Assets/_Game/Art/Models/
```

The teens are original characters in a flat-shaded anime style (two cel bands, a thin dark ink
line, few details, a clear silhouette) with realistic, slim teen proportions: long legs and a
small head (about 7 heads tall). Settings → Player picks which one walks to school (both are
built into each level, `CharacterChoice` shows one). Both wear a school uniform modelled in the
shop's School Uniform colours (a white top and navy legwear), so that outfit recolours to itself.
- Boy: a near-black messy mop of big chunky pointed locks (a fringe falling to the brows, locks
  over the tops of the ears, the back flicking out at the nape, a cowlick at the crown), dark
  eyes, a plaster on his cheek, warm tanned skin; a loose white short-sleeved shirt with an open
  collar worn untucked, straight navy trousers resting on the shoes, white canvas sneakers on a
  grey sole, and a red satchel on a cross-body strap (over his left shoulder, hanging at the back
  of his right hip).
- Girl: a near-black high ponytail with a yellow scrunchie and a side-swept fringe, freckles,
  warm skin; a white blouse with a rounded navy collar (it takes the skirt's colour), a navy
  pleated skirt, knee socks, loafers and a yellow backpack.
- Both faces are an oblong-oval: fairly straight sides from the cheekbones to the mouth, rounding
  into the chin (hers rounded, his softly squared). The face's normals lean toward one forward
  direction, so the cel bands cross the face as one clean shape.

The teens are built from modules on a shared `Part` contract (`teen_lib.py`): `teen_body.py`
(joints, a sculpted body, bones, teen proportions: `lift` stretches the body, `head_scale`
shrinks the head about the neck), `teen_outfit.py` (clothes, shoes, bags, the outfit colours),
`teen_head.py` (the head and ears), `face_teen.py` (the painted face atlas) and `teen_hair.py`.
`teen.py` colours, rigs, joins and exports them; the `.json` it writes holds the top, legwear and
hair colours, which the level builder gives `ModelOutfit` as its defaults. At the game's neck
heights (1.5 and 1.43) the boy stands about 1.73 m and the girl about 1.65 m (hair included).

What the model carries:
- One skinned mesh, one material: vertex colours times the atlas (the face is painted in the
  atlas' upper-left quadrant; everything else samples its white corner).
- UV channel 2, x: the outfit part (0 skin and fixed parts, 1 shirt or blouse, 2 trousers or skirt (and her collar), 3 hair) for `ModelOutfit`.
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

## Asset kits

Everything in the street is built from kits of original models in the look set out in
`docs/ART_DIRECTION.md`. Each kit is one script that writes one FBX per model, one shared atlas
(`<Kit>Atlas.png`) and a manifest (`<Kit>.json`: each model's size, bounds, triangle count and the
sRGB base colour of its recolourable parts). `kit_lib.py` holds the shared helpers and the export
contract: the front faces -Y, the origin is on the ground, `Attach.*` empties mark attachment points
(`Attach.Front` 1 m in front of the model tells the game which way it faces), one material of
vertex colours times the atlas, and recolourable parts in UV2.x.

| Kit | Script | What's in it |
|---|---|---|
| Plants | `kit_plants.py` | conifers, broadleaf trees, birch, cherry, palms, bushes, hedge blocks, grasses, reeds, flowers |
| Buildings | `kit_buildings.py` | gabled and long houses, bungalow, two shops, flats, warehouse, school, garage |
| Street | `kit_street.py` | utility pole, lamp, pedestrian signal, walls, fences, hoarding, planters, benches, vending machines, signs, crates, pots, stalls, awnings |
| Terrain | `kit_terrain.py` | boulders, rock clusters, cliffs, a headland, mountain ranges, rolling hills, a forest strip, dunes, sand and gravel piles |
| Leisure | `kit_leisure.py` | lifeguard tower, parasols, beach things, trampoline, swing tree and frame, fountain, raft, sign board, checkpoint flag, targets, playground |
| Works | `kit_works.py` | sliding gate, call bollard, intercom, tower crane, crane hook and load, hoist, site backdrop, underpass, school arch and wall |
| Animals | `kit_animals.py` | dog, seagulls, pigeon, cat, duck, crab, butterfly, squirrel (moving parts as child objects), coin, sticker, star |

```
blenv/bin/python kit_plants.py -- $PWD/out/plants                       # writes the FBXs, atlas, manifest and Plants.blend
blenv/bin/python review_kit.py -- $PWD/out/plants/Plants.blend $PWD/plants_sheet.png [--models A,B] [--cols 4]
cp out/plants/*.fbx out/plants/PlantsAtlas.png out/plants/Plants.json ../../Assets/_Game/Art/Models/Plants/
```

The game places kit models with `LevelBuildKit.KitModel` (StreetBuilder for the scenery,
TrackBuilder for gameplay pieces), recolours their parts with `ModelTint`, and falls back to the
old procedural look for any model a kit doesn't have.

`preview_street.py` lays the kits out the way StreetBuilder does and renders a stretch of street
through the game camera in each chapter's light and haze (Blender's shading, not the toon ramp, so
judge layout, scale, silhouettes and colour):

```
blenv/bin/python preview_street.py -- $PWD/out $PWD/street_ch1.png --chapter 1 [--seed 7] [--wide]
```
