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
blenv/bin/python review_poses.py -- $PWD/Boy.blend $PWD/boy_poses.png --jobs 3 --leaks
    # the pose audit (see below): the teen in every pose the game uses, from the game's camera yaws
cp Boy.fbx Boy.json BoyAtlas.png Girl.fbx Girl.json GirlAtlas.png ../../Assets/_Game/Art/Models/
blenv/bin/python portrait_teen.py -- $PWD/Boy.blend $PWD/PlayerBoy.png --yaw 28     # the menus' player cards
blenv/bin/python portrait_teen.py -- $PWD/Girl.blend $PWD/PlayerGirl.png --yaw -28  # (they face each other)
cp PlayerBoy.png PlayerGirl.png ../../Assets/_Game/Resources/UI/
blenv/bin/python sticker_art.py -- <kits dir> <cars dir> <teens dir> $PWD/stickers_raw   # the album's 23 sticker subjects
python3 sticker_compose.py $PWD/stickers_raw $PWD/stickers                                # die-cut vinyl stickers (normal / holo / gold)
cp stickers/L*.png ../../Assets/_Game/Resources/UI/Stickers/
```

The teens are original characters in a flat-shaded anime style (two cel bands, a thin dark ink
line, few details, a clear silhouette) with realistic, slim teen proportions: long legs and a
small head (about 7 heads tall). Settings → Player picks which one walks to school (both are
built into each level, `CharacterChoice` shows one). Both wear a school uniform modelled in the
shop's School Uniform colours (a white top and navy legwear), so that outfit recolours to itself.
- Boy: a near-black messy mop of big chunky pointed locks (a fringe falling to the brows, locks
  over the tops of the ears, the back flicking out at the nape, a cowlick at the crown), dark
  eyes, a plaster on his cheek, warm tanned skin; a white short-sleeved school shirt, buttoned up
  to a pointed collar and tucked into straight navy trousers (the waistband is at the natural
  waist, with a little blousing over a thin dark-brown belt and its small brass buckle), a red
  striped tie, white canvas sneakers on a grey sole, and a red satchel on a cross-body strap (over
  his left shoulder, across the tie, hanging at the back of his right hip).
- Girl: a near-black high ponytail with a yellow scrunchie and a side-swept fringe, freckles,
  warm skin; a white blouse with a rounded navy collar (it takes the skirt's colour) tucked under
  the waistband of a navy pleated skirt, a red striped tie, knee socks, loafers and a yellow
  backpack.
- The tie (both): a small knot under the collar, a narrow neck part that widens into a blade with
  a pointed tip, lying flat on the shirt and ending at the belt (his) or the skirt's waistband
  (hers). Red (the default accent, sRGB 0.78 0.20 0.24) with thin darker diagonal stripes that are
  brightness variations of the red only, so the game's recolour (which keeps each vertex's
  brightness relative to the default colour) keeps them whatever the accent is.
- Both faces are an oblong-oval: fairly straight sides from the cheekbones to the mouth, rounding
  into the chin (hers rounded, his softly squared). The face's normals lean toward one forward
  direction, so the cel bands cross the face as one clean shape.

The teens are built from modules on a shared `Part` contract (`teen_lib.py`): `teen_body.py`
(joints, a sculpted body, bones, teen proportions: `lift` stretches the body, `head_scale`
shrinks the head about the neck), `teen_outfit.py` (clothes, shoes, bags, the outfit colours),
`teen_head.py` (the head and ears), `face_teen.py` (the painted face atlas) and `teen_hair.py`.
`teen.py` colours, rigs, joins and exports them; the `.json` it writes holds the top, legwear,
accent (the tie) and hair colours, which the level builder gives `ModelOutfit` as its defaults.
(`teen.py ... --fast` skips the head, hair and face atlas: for iterating on the clothes.) At the game's neck
heights (1.5 and 1.43) the boy stands about 1.73 m and the girl about 1.65 m (hair included).

What the model carries:
- One skinned mesh, one material: vertex colours times the atlas (the face is painted in the
  atlas' upper-left quadrant; everything else samples its white corner).
- UV channel 2, x: the outfit part (0 skin and fixed parts, 1 shirt or blouse, 2 trousers or skirt (and her collar), 3 hair, 4 accent: the tie) for `ModelOutfit`.
  Skin that lies under clothes is not skin-coloured: it takes the colour and the part of the garment over it (1 or 2), so a
  bent knee or a lifted thigh that makes it poke through the cloth shows more cloth, never a sliver of bare skin (and its ink outline
  is the cloth's). Only skin that is really bare (his head, neck and arms below the sleeves, her legs below the skirt) is skin.
- Bones: Hips, Spine, Chest, Neck, Head, Upper/LowerLeg, Foot, Upper/LowerArm, Hand (.L/.R), Bag (the kid), and Nose, an unweighted marker in front of
  the face that tells the game which way the model faces.
  The game poses them in code (`CharacterRig`), measuring each swing from the bone's rest pose.

How the clothes survive the poses (what the pose audit below checks):
- The trousers have analytic skin weights (`leg_skin_weights` in `teen_outfit.py`), and so does the skin under them:
  the waistband and the tucked-in shirt stay with the hips, the legs' pull ramps in over a hand's breadth round
  each hip joint, and each knee cross-fades over a wide band (wider at the back of the knee), so the cloth and the
  skin under it bend alike and a knee bent to 140 degrees stays a round bend. Decimation leaves long flat tubes with
  no vertices near a joint, so the trousers and the skin get rings back at the knees and hips (`refine_edges`).
- The shirt's and blouse's armpits are a soft web (`bind_loose_shirt`): the side follows the arm a little beside each
  sleeve, so an arm thrown up or forward folds the armpit instead of tearing it open. The tie follows the shirt's weights
  (`bind_follow`); the satchel's strap rides over the tie (`F.tie_top`).
- Her skirt's pull on the thighs starts above the hip joints (`bind_skirt`), so a lifted thigh rides up inside it rather
  than through it; her thighs and knees take the analytic weights below the hips.

### Pose audit

`review_poses.py` renders a built teen (`Boy.blend` / `Girl.blend`) in every pose the game uses
(`KidAnimator`, `MenuKid`: idle, the menu's balance, run at three phases, jump rise and fall, the
double jump's tuck at 0/90/180/270 degrees of somersault, kick wind-up and contact, slide, landing,
celebrate, the menu's keepy-uppy foot and thigh touches; each asymmetric pose again with the other
leg raised, "(L)") from the game's camera yaws, into one contact sheet. It poses the bones exactly
as `CharacterRig` does (the game's angles in degrees about the side axis; a positive `lean` tips
the body forward, a positive `headTilt` tips the head back; `--list` prints every pose). Yaw 66
is the game's own look (the teen turned 24 degrees toward the camera from side-on), 24 a
three-quarter front view, 90 the side; the menu poses use 42 (it turns 48 degrees) in place of 66.

```
blenv/bin/python review_poses.py -- $PWD/Boy.blend $PWD/boy_poses.png --jobs 3 --leaks
blenv/bin/python review_poses.py -- $PWD/Boy.blend $PWD/knees.png --poses run_kneeup,kick_contact --yaws 66,90 --focus 0.3,0.7 --cell 600x600
```

`--leaks` also writes `<out>_leaks.png` and prints a pixel count per cell: the body's skin that
lies under clothes at rest is painted magenta wherever it shows in the pose (the skin under the
clothes is clothes-coloured in the model, so this finds geometry poking through the cloth, which is
what a bare-skin sliver used to be). It is a cue to look at the cell, not a verdict: his armpits
and her skirt lifting show a few legitimately. `--focus a,b` frames only that band of the standing
height (0 feet, 1 crown) for close-ups, `--cell WxH` is the cell size, `--dist` the camera distance
(12 m like the game's, 0 for orthographic). `--yaws -66,-90` look from the other side (the game turns the
teen both ways), `--body-only` removes the clothes to see what the skin does under them. The pose table is copied
from `KidAnimator.cs` / `MenuKid.cs`: when the game's poses change, change it too.

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
| Plants | `kit_plants.py` | conifers, broadleaf trees (five), a cloud-pruned garden pine, birch, cherry, palms, bushes, hedge blocks, grasses, reeds, flowers; the trees' and bushes' leaves are cut-out leaf-clump cards (`kit_plants_leaves.py`) |
| Buildings | `kit_buildings.py` | gabled and long houses, bungalow, fruit shop and bakery, flats, warehouse, school, garage; the town's shops and houses (`kit_buildings_town.py`): a small supermarket, cafe, bookshop, florist, noodle house, convenience store, two narrow tiled three-storey buildings, a white house with a corrugated lean-to and a garden pine, a flat-roofed house with a balcony, a house with a carport |
| Street | `kit_street.py` | utility pole, lamp, pedestrian signal, walls, fences, hoarding, planters, benches, vending machines, signs, crates, pots, stalls, awnings, A-frame board, banner flag, electrical cabinet, bicycle hoops, wheelie bins, doorstep pots |
| Terrain | `kit_terrain.py` | boulders, rock clusters, cliffs, a headland, mountain ranges, rolling hills, a forest strip, dunes, sand and gravel piles |
| Leisure | `kit_leisure.py` | lifeguard tower, parasols, beach things, trampoline, swing tree and frame, fountain, raft, sign board, checkpoint flag, targets, playground |
| Works | `kit_works.py` | sliding gate, call bollard, intercom, tower crane, crane hook and load, hoist, site backdrop, underpass, school arch and wall |
| Animals | `kit_animals.py` | dog, seagulls, pigeon, cat, duck, crab, butterfly, squirrel (moving parts as child objects), coin, sticker, star |
| Barriers | `kit_barriers.py` | things to slide under, each spanning the footpath with a clear 0.85 m gap over the kid's line (`kit_barriers_models.py`, built with the Works kit's geometry and atlas modules): painters' boards on trestles, a car-park barrier arm, a hedge trimmer's work platform, a propped apple bough; a market stall under its awning, a half-raised roll shutter, a delivery roller conveyor; a surf rack, a rowing boat upturned on trestles, a boardwalk crossing, a lifeguard's rescue-board stand; a sheeted scaffold, steel beams on trestles, a pipe rack, a site barrier; a fallen trunk, an old oak's propped bough, a rope-net tunnel, a play tower. The manifest's `slideHalf` / `slideTop` (or `slideRadius` / `slideCentre`) give the solid the game builds a collider for |

```
blenv/bin/python kit_plants.py -- $PWD/out/plants                       # writes the FBXs, atlas, manifest and Plants.blend
blenv/bin/python review_kit.py -- $PWD/out/plants/Plants.blend $PWD/plants_sheet.png [--models A,B] [--cols 4]
cp out/plants/*.fbx out/plants/PlantsAtlas.png out/plants/Plants.json ../../Assets/_Game/Art/Models/Plants/
```

The buildings kit's atlas is 2048 x 4096 (each building has its own grime maps; the shops' signs,
interiors seen through glass, curtains and posters are painted by `kit_buildings_signs.py`, with
invented names, using whatever fonts the machine has). Shops and houses are dealt along the street
from shuffled decks (StreetBuilder's `Deck`), so every kind turns up and none stands twice in a row.

The game places kit models with `LevelBuildKit.KitModel` (StreetBuilder for the scenery,
TrackBuilder for gameplay pieces), recolours their parts with `ModelTint`, and falls back to the
old procedural look for any model a kit doesn't have.

`preview_street.py` lays the kits out the way StreetBuilder does and renders a stretch of street
through the game camera in each chapter's light and haze (Blender's shading, not the toon ramp, so
judge layout, scale, silhouettes and colour):

```
blenv/bin/python preview_street.py -- $PWD/out $PWD/street_ch1.png --chapter 1 [--seed 7] [--wide]
```
