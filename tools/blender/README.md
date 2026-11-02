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
blenv/bin/python primary.py -- $PWD/PrimaryBoy.fbx --boy      # the four primary-school kids (see below); also
blenv/bin/python primary.py -- $PWD/PrimaryGirl.fbx --girl    # teen.py ... --primary-boy / --primary-girl /
blenv/bin/python primary.py -- $PWD/PrimaryBoy2.fbx --boy2    # --primary-boy2 / --primary-girl2
blenv/bin/python primary.py -- $PWD/PrimaryGirl2.fbx --girl2
blenv/bin/python review_teen.py -- $PWD/Girl.blend $PWD/girl_sheet.png [--bg shot1.png,shot2.png,shot3.png]
    # review sheet with the game's toon shading: faces, poses, side, back, and the teen at in-game
    # size (215 px tall, in-game outline) standing and running in front of game screenshots
    # (the primary kids' bigger heads: add --face-dz 0.07 --face-scale 0.5)
blenv/bin/python review_poses.py -- $PWD/Boy.blend $PWD/boy_poses.png --jobs 3 --leaks
    # the pose audit (see below): the teen in every pose the game uses, from the game's camera yaws
cp Boy.fbx Boy.json BoyAtlas.png Girl.fbx Girl.json GirlAtlas.png ../../Assets/_Game/Art/Models/
cp Primary*.fbx Primary*.json Primary*Atlas.png ../../Assets/_Game/Art/Models/
blenv/bin/python portrait_teen.py -- $PWD/Boy.blend $PWD/PlayerBoy.png --yaw 28     # the menus' player cards
blenv/bin/python portrait_teen.py -- $PWD/Girl.blend $PWD/PlayerGirl.png --yaw -28  # (they face each other)
cp PlayerBoy.png PlayerGirl.png ../../Assets/_Game/Resources/UI/
blenv/bin/python portrait_teen.py -- $PWD/PrimaryBoy.blend $PWD/PlayerPrimaryBoy.png --yaw 28 --span-heads 2.3     # the primary kids' cards
blenv/bin/python portrait_teen.py -- $PWD/PrimaryGirl.blend $PWD/PlayerPrimaryGirl.png --yaw -28 --span-heads 2.3  # (boys turn right,
blenv/bin/python portrait_teen.py -- $PWD/PrimaryBoy2.blend $PWD/PlayerPrimaryBoy2.png --yaw 28 --span-heads 2.3   #  girls left)
blenv/bin/python portrait_teen.py -- $PWD/PrimaryGirl2.blend $PWD/PlayerPrimaryGirl2.png --yaw -28 --span-heads 2.3
cp PlayerPrimary*.png ../../Assets/_Game/Resources/UI/
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
`teen.py` colours, rigs, joins and exports them (the steps live in `teen_build.py`, which the primary-school kids
share); the `.json` it writes holds the top, legwear,
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
double jump's launch, tuck at 0/90/180/270 degrees of somersault and open-out, kick wind-up and contact,
the slide's lunge and its settled lean, landing,
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

## Primary-school kids

Four more playable characters in the same flat-shaded anime style (two cel bands, a thin dark ink line, a clear
silhouette), younger and cuter than the teens and built by the same pipeline: about five heads tall (the teens
are six and a half to seven), a big round head that is not scaled down, big eyes set low in a round face, a short
neck, a round tummy, short limbs and small hands. They wear a Japanese elementary-school uniform: a short-sleeved
white polo (boys) or blouse (girls), shorts (boys) or a skirt / a pinafore (girls) that end above the knee, white
socks (long crew socks for the boys), shoes, and a hard rectangular school backpack (a *randoseru*: a box with a flap
and a lock, on two wide straps) on the Bag bone, a different colour on each. No tie: the accent (outfit part 4) is a
small neckerchief or a bow at the collar, a few separate little shells that share no vertex with the clothes, so
a game mode can make them vanish by collapsing their vertices.

| File | Who | Look | Shirt / legwear / accent / bag / hair |
|---|---|---|---|
| `PrimaryBoy` | boy 1 | fair skin, round dark eyes, short black hair with a broad fringe and a small tuft; a polo with a flat collar, navy shorts, long white crew socks, white sneakers | white / navy / yellow neckerchief / blue / black |
| `PrimaryGirl` | girl 1 | fair skin with freckles, big warm-brown eyes, a centre-parted fringe and two bunches at the sides with red ties; a blouse with a round navy collar, a navy pleated skirt, white knee socks, brown school shoes | white / navy / red bow / red / dark brown |
| `PrimaryBoy2` | boy 2 | tanned skin, tousled chestnut spikes, round glasses, a wide grin; a polo, grey shorts, white crew socks, grey sneakers | white / grey / red neckerchief / green / chestnut |
| `PrimaryGirl2` | girl 2 | medium-brown skin with a beauty mark, hazel eyes, a black bob with a straight fringe and a yellow hairband; a blouse with a round white collar under a grey pinafore (bib and straps), white socks, black school shoes | white / grey / yellow bow / purple / black |

The game scales every model so that its Head bone sits at the neck height it is given (`LevelBuildKit.BuildModelCharacter`;
the teen boy's 1.5 stands 1.73 m, the girl's 1.43 stands 1.65 m), so only proportions matter. They are 5.2, 5.2, 4.9 (his
spikes add 6 cm) and 5.1 heads tall counting the hair, and `primary_spec.HEIGHT` says how tall each should stand; a build
prints the neck height that gives it:

| File | Standing height (hair included) | Neck height to give the game | Triangles |
|---|---|---|---|
| `PrimaryBoy` | 1.30 m | 1.065 | 17,173 |
| `PrimaryGirl` | 1.27 m | 1.038 | 16,918 |
| `PrimaryBoy2` | 1.34 m | 1.082 | 18,559 |
| `PrimaryGirl2` | 1.29 m | 1.051 | 17,099 |

(The models are 1.685, 1.646, 1.784 and 1.694 m tall as exported, their Head bones at 1.38, 1.345, 1.44 and 1.38 m; neck
height = Head bone height x standing height / model height. A single neck height of 1.05 would put all four at 1.28 to
1.30 m, indistinguishable by height.)

```
blenv/bin/python primary.py -- $PWD/PrimaryBoy.fbx --boy        # PrimaryBoy.fbx/.blend/.json and PrimaryBoyAtlas.png
blenv/bin/python primary.py -- $PWD/PrimaryGirl.fbx --girl      # (--boy2, --girl2 for the others; --fast skips head and hair)
blenv/bin/python review_teen.py -- $PWD/PrimaryBoy.blend $PWD/boy_sheet.png --face-dz 0.07 --face-scale 0.5
blenv/bin/python review_poses.py -- $PWD/PrimaryBoy.blend $PWD/pboy_poses.png --jobs 3 --leaks
blenv/bin/python portrait_teen.py -- $PWD/PrimaryBoy.blend $PWD/PlayerPrimaryBoy.png --yaw 28 --span-heads 2.3
```

How they reuse the teen pipeline instead of copying it:
- `primary_spec.py` is the table of who they are (palette, proportions, garment, accent, hair style, face); `make(name)` returns
  a `teen_lib.Variant`. A Variant stands in for the teens' `girl` flag (it is truthy for the girls, hashes by identity), so the
  teen modules' signed-distance primitives, polygoniser, binders, collars and skirt run unchanged; the few teen functions
  that hold the teens' own numbers (`lift`, `head_scale`, `tj`, `field`, `fields`, `cover`, `palette`, the face, hair and
  head builders, `build_body`'s budgets) hand a Variant on to the matching `primary_<what>` module. The teens' output is
  unchanged by it (checked by hashing the rebuilt meshes, weights and bones against the old ones).
- `teen_build.py` holds the steps both entry points share (colour, grow, rig, weight, join, export); `teen.py` and `primary.py`
  just say what to build.
- `primary_body.py`: the body field (a rounder torso, small hands, short legs; everything above the hips hangs from the neck joint,
  so a taller kid only has longer legs). `primary_head.py`: the head shape (full cheeks, short lower face, small round chin) and
  the glasses. `primary_face.py`: the four faces (bigger, lower, rounder eyes; each with its own character) painted into each
  kid's own 2048 atlas like the teens'. `primary_hair.py`: the four styles on the teens' cap-and-locks machinery, 2.5 to 4.2
  thousand triangles each (a crop, twin bunches, radial spikes, a bob with a hairband). `primary_outfit.py`: the clothes,
  shoes, randoseru and accents.
- The primary kids' limbs are about three quarters of a teen's: `Variant.k` scales the widths of the teens' skin-weight blends
  (knees, hips, armpits, skirt) by it (`teen_outfit.ksc`).

What is specific to them:
- Boys' shorts are a loose A-line tube round each thigh (the two hems never touch), cut above the knee: the hem sits where the thigh
  still moves as one piece, so it follows the thigh with the teens' analytic leg weights (the cloth and the skin under it
  take the same weights) and a bent knee below it is bare skin. The hands hang beside the hips, so the body field blends arms into
  the torso only up to the armpit (a hand beside a hip is never webbed to it) and `cover` does not count them as covered.
- Girl 1's skirt is the teens' pleated skirt (`teen_outfit._skirt`, which now takes its measures from a dict) with six pleats a
  side; girl 2's pinafore is the same skirt with five, from a high waist, plus a bib and two ribbon straps that lie on the
  body's surface (all in the legwear colour, part 2).
- The neckline is a wide ellipse on the slope of the shoulders under a flat collar that lies round it (`teen_outfit._shirt_collar`
  with a scale; 'point' for the boys' polo, 'round' for the girls' blouse); the neck is a short thick child's neck.
- The backpack is a rounded box (the Bag bone's head is at its top edge, as on the teen girl) with a flap, a lock and
  two straps that follow the ribcage (`primary_outfit.bind_torso`); girl 2's lie over the pinafore.

What the game needs to use them (nothing of this is wired up yet: the picker, `CharacterChoice` and `ArtBaker` know only the
teens): the same model contract as `Boy` / `Girl`, so `LevelBuildKit.BuildModelCharacter(parent, "PrimaryBoy", material,
neckHeight, TeenFeet(neckHeight), true)` with the neck heights above, a `CharacterMaterial("PrimaryBoy", toonCharacter,
"PrimaryBoyAtlas", true)` for each (every kid has its own atlas), `ReadOutfitColors` finds the `.json` by file name, and
the cards are `UI/PlayerPrimaryBoy`, `PlayerPrimaryGirl`, `PlayerPrimaryBoy2`, `PlayerPrimaryGirl2` (512 px, drawn like
`PlayerBoy`). The Bag bone's head is at the top edge of the randoseru, so the shop's pennant clips on as it does on the
teen girl's backpack; `Chest` is not used (that is the teen boy's satchel).

Pose audit (the table in `review_poses.py` is checked against `KidAnimator.cs` / `MenuKid.cs`, with the double jump's launch,
tuck and open-out and the slide's lunge). All four kids were run through it in every pose from three yaws (105 cells each,
`--leaks`) and no bare-skin sliver shows under any garment in any pose. The leak maps hold only what is there at rest: a thin ring of
covered neck skin under the collar, the sock cuffs and the shoe collars (an idle cell has 80 to 160 px of magenta, the
largest count in any cell of any kid is 168 px), and with a raised thigh a few pixels in the crease where a short leg meets
the hip, which render in the cloth's colour. What it still shows:
- The girls' skirts: with a thigh raised past about 60 degrees (run knee-up and stride, jump rise, the kicks, the keepy-uppy
  thigh) the hem on that side rides up in a diagonal notch and the knee comes out through the front opening, covered skin
  in the skirt's colour (as on the teen girl: it is the same skirt); the double jump's tuck bunches the skirt round the knees.
- The boys' shorts: a few-pixel crease at the hip when a leg is lifted, and the hem's edge is a little uneven (its
  rounded rim is shaded per face) when seen from very close.

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

## The town map

`town_map.py` builds the world map's picture and its layout data. The picture
(`Assets/_Game/Resources/UI/TownMap.jpg`, 3200 x 1800) is an aerial view of the town the kid walks
through, rendered in Blender from the game's own kit models (houses, shops, trees, cars, park,
beach, building site, railway); `Assets/_Game/Resources/TownMapLayout.json` is the data the map
screen draws on it: the two places, the six routes as polylines, the 28 level nodes with the side
their name goes on, and the anchors for the district and street names. Both come from one layout
(`town_map_layout.py`), so the picture and the data cannot disagree. The picture holds no text, UI,
route lines or nodes; the game draws those.

```
venv_bpy/bin/python town_map.py -- $PWD/out/town                 # TownMap.jpg, TownMapLayout.json, TownMap_ground.png (about 6 minutes)
venv_bpy/bin/python town_map.py -- $PWD/out/town --debug         # + TownMap_debug.png: routes, nodes and name boxes over the picture
venv_bpy/bin/python town_map.py -- $PWD/out/town --layout-only   # only TownMapLayout.json (a few seconds)
venv_bpy/bin/python town_map.py -- $PWD/out/town --crop 400,225,1600,900 --samples 32   # a close look at part of the picture
python3 town_map_check.py out/town/TownMapLayout.json            # the contract checks (pure Python)
cp out/town/TownMap.jpg ../../Assets/_Game/Resources/UI/TownMap.jpg
cp out/town/TownMapLayout.json ../../Assets/_Game/Resources/TownMapLayout.json
```

`venv_bpy` is any Python with the `bpy` module (`pip install bpy`) plus numpy and Pillow. Options:
`--scale 0.5` renders at half size (the JSON stays in full pixels), `--samples` is Eevee's sample
count (the shipped frame uses 16; shadows are soft and the picture is deterministic: everything is
seeded), `--ss 2` is the ground's supersampling, `--repaint` repaints the ground even if
`TownMap_ground.png` exists, `--keep-ground` re-renders with the existing ground.

### The frame

The picture is 3200 x 1800 with its core (x 400, y 225, 2400 x 1350) where all the content lives;
the ring round it is more town (suburbs west and south, woods north, sea and far shore east). The
map screen puts a title over the top 12% of the core and a strip of route chips over the bottom
20%, so those bands are kept quiet (no landmarks); the home, the school and every node are inside
the core's inner area (x 120 to 2280, y 170 to 1130 in core coordinates). One metre of the town is
8 px, so a house is 60 to 90 px, a residential street 60 px between kerbs (74 with pavements), the
main road 84 px (100), a tree 30 to 60 px. The sun is in the south-west, so shadows fall to the
north-east; the grade is slightly desaturated daylight so that the route lines pop.

### The town

The town is a ladder: the home (the red-door house on Elm Street, next to the West Street) and the
school gate (on School Lane) are the two ends, and the six routes run between them like rungs:

| Route | Where it runs |
|---|---|
| park | up the West Street, west by Rose Street and Park Lane to the park gate, east through the park (a path with a short tunnel under the railway), down the East Street to the school |
| underpass | up the West Street to Station Road, east through the road tunnels under the railway (two tracks), down the East Street |
| site | up the West Street to Yard Road, east through the building site (a track between two fenced yards), the East Street |
| street | Elm Street straight east (Elm Street, Hill Road, Garden Lane), the East Street (Puddle Lane) |
| market | down the West Street to Market Street, east through the market, up the East Street |
| beach | Seaside Road along the south, then the boardwalk along the sand to the school's promenade and back west along School Lane |

The railway comes down from the north and ends at a small station just south of Station Road. Only
the park and underpass routes cross it, and they go under it; no route has a level crossing.

### TownMapLayout.json

UTF-8, plain objects (it reads with `JsonUtility`), image pixels with the origin top-left:

```
{ "image": "UI/TownMap", "width": 3200, "height": 1800, "core": {x:400, y:225, w:2400, h:1350},
  "places":    [ {id:"home", x, y}, {id:"school", x, y} ],
  "routes":    [ {id, points:[{x, y} ...]} ...  in RouteTable order: street, market, beach, underpass, site, park ],
  "nodes":     [ {id, x, y, label} ... 28: L01 to L23 then C01 to C05; label is "below", "above", "left" or "right" ],
  "districts": [ {id, x, y} ... neighbourhood, market, beach, park, railway, site, school, sea ],
  "streets":   [ {name, x, y, angle} ... 12 names on straight stretches; angle in degrees, clockwise on screen positive (y down), as the game reads it ] }
```

Each route starts at the home and ends at the school (within 25 px), is smooth (30 to 90 points,
follows its roads), at least 1200 px long and keeps 90 px from the other routes except within 300
px of the home and the school. A story node lies on its route (within 12 px), in play order; a
challenge node is 130 to 260 px beside its route; nodes are 190 px apart and 120 px from the places.
A level's name is a 300 x 56 px box 10 px off the node's 150 px disc on the node's `label` side. The
map screen draws the names of the focused route's levels only, over every route line, so a name
keeps 30 px from its own route's centre line and only must not cross the other routes' lines, it
keeps 6 px from every node disc, and 6 px from the names of the levels of its own route (names of
different routes may overlap). The street whose name is a route's name (Home Street, Market Street,
Seaside Road) lies within 60 px of that route on a stretch the route uses; Elm Street, Hill Road,
Garden Lane and Puddle Lane are beside L02 to L05; no street is called after a level except Puddle
Lane (L05); the road through the railway tunnels is Station Road.

`town_map_check.py` (pure Python, no bpy or numpy) checks all of this against `RouteTable.cs` and
`StringTables.cs`, plus the level / map rules below when `town_map_layout.py` sits next to it, and
exits 1 with every broken rule printed.

### How it is made

| Module | What it does |
|---|---|
| `town_map_layout.py` | the layout as data: junctions, roads (control points of smooth curves), the areas (sea, sand, park, school, market, site, station), where each level is, the district and street-name wishes |
| `town_map_graph.py`, `town_map_build.py` | the road graph; each route is the shortest path through its waypoints, smoothed and resampled to 30 to 90 points; districts and street names are put on straight stretches clear of the nodes; writes the JSON |
| `town_map_nodes.py` | places the 28 nodes and their name sides: an exact constraint search (arc consistency, challenge nodes first) near the anchors the layout gives |
| `town_map_levels.py` | the level / map checks: zones and railway crossings (below) |
| `town_map_raster.py`, `town_map_ground.py` | the flat ground painted as a texture: land, sea with foam, sand, lawns, roads with kerbs, pavements and paint, boardwalks, railway bed, paths |
| `town_map_place.py` | houses and shops along the roads' frontages, infill, garden fences and hedges, trees (round crowns and kit conifers), cars on the kerbs, lamps |
| `town_map_sets.py`, `town_map_sets_nature.py`, `town_map_sets_works.py` | the set pieces placed from the solved nodes: the home and what each level shows beside its node |
| `town_map_kit.py`, `town_map_scene.py` | the Blender side: kit FBXs and characters as linked duplicates, a low sun with soft shadows, a camera looking down with a long lens |
| `town_map_plan.py` | the debug overlay: routes, nodes and name boxes drawn over the picture |
| `town_map_check.py` | the validator |

## Level and map

What the levels contain is what the map shows at their nodes, and what the levels forbid, the map
does not show. The layout (`town_map_layout.py`: `LEVEL_ZONES`, `CHECK_ZONES`, `CHALLENGE_ZONES`) and
`town_map_levels.py` check it on every build and in `town_map_check.py`.

Rules: (1) only the underpass route (under 1 to 2 tracks) and the park route (once, by a short
tunnel) cross the railway, and they go under it; the street, market, beach and site routes never
cross it, not even by a level crossing; (2) the school is by the sea and has a football pitch; (3)
the site route has no tunnel; (4) the home, and the start of every route, is the residential
street round the red-door house. Every story node lies in the zone of its route: street
`residential`, market `market`, beach `sand` (the sand and the boardwalk), underpass `underpass`
(Station Road at the railway), site `site_works` (Yard Road through the building site), park
`park`; L23 at the school gate; C03 on the sand, C04 in the site yard, C05 on the park's lawns.

The picture shows this beside each node, 80 to 200 px along its route:

| Level | Route | The map shows |
|---|---|---|
| L01 | street | the home's front garden (fence with a gate, flower beds, post box) and the first kerb with red tactile paving |
| L02 | street | four cars parked nose to tail on the kerb, painters' trestles with paint pots on the pavement |
| L03 | street | Hill Road: terraces with retaining walls and steps climbing the hill, a small stream under the road, garden apple trees |
| L04 | street | Garden Lane: a garden wall with three gates, apple trees behind it, a parked car |
| L05 | street | Puddle Lane: a wet lane with four big puddles, cars parked along it |
| L06 | market | the market square: a plaza with two rows of awning stalls, crowds, crates |
| L07 | market | three zebra crossings in a row with traffic lights, a delivery van with a roller conveyor |
| L08 | market | the corner shop: steps, awning, roll shutter, crates |
| L09 | market | fruit stalls with awnings, a toy shop with trampolines out front, a zebra crossing |
| L10 | market | the main road at rush hour: crowds, three crossings, a queue of cars, stalls |
| L11 | beach | the boardwalk over the sand, a surf school's racks, sign and flags |
| L12 | beach | wet sand with several tidal channels, boats on trestles |
| L13 | beach | seagulls, a rescue-board stand, a breezy bay with rocks and flags |
| L14 | beach | sandcastles, surf racks, the boardwalk crossing the promenade, the school |
| L15 | underpass | the dark road in its cutting under the railway, site barriers, puddles, pipes, a builder's lift, ramps and platforms, scaffolding |
| L16 | site | ramps, platforms, pipe racks, rolling pipes, a security gate on the track |
| L17 | site | tower cranes swinging pallets over open trenches, the builder's lift |
| L18 | underpass | the cutting between two bridges (under the main line and the station's loop), scaffolding, a lift, barriers, puddles |
| L19 | park | the park gate, dogs, a net tunnel, a fallen tree |
| L20 | park | three fountains, trampolines, a play tower |
| L21 | park | a playground with rope swings over a stream, trampolines, a climbing frame, a net tunnel |
| L22 | park | a duck pond with stepping stones, a rope ferry (a raft on a rope), a fountain |
| L23 | park | the last stretch to the school gate: the short tunnel under the railway, a crossing, a fountain, a swing, seagulls, the school's steps |
| C01 | street | an open spot by the house: a small court with goals |
| C02 | market | shop windows: the shop parade with awnings |
| C03 | beach | slalom flags on the sand east of the school |
| C04 | site | targets on a slab in the building site's yard |
| C05 | park | a lawn arena with mown stripes and goals at the school end of the park |
