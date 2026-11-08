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
blenv/bin/python meshy_boy.py -- /abs/boy_with_bicycle.fbx $PWD   # the playable teen boy, from a supplied textured model
    # (Boy.fbx/.blend/.json, BoyAtlas.png, and his bicycle: Bicycle.fbx, BicycleAtlas.png; see "The boy" below)
blenv/bin/python meshy_teen.py -- /abs/backpack_boy.fbx $PWD --profile backpack_boy   # Max, from a supplied A-posed model
    # (BackpackBoy.fbx/.blend/.json, BackpackBoyAtlas.png, BackpackBoy_joints.png; see "The backpack boy" below)
blenv/bin/python meshy_rigged.py -- /abs/awesome_little_explorer_running.fbx $PWD/rigged   # Leo, from his rigged model
blenv/bin/python meshy_rigged.py -- /abs/little_explorer_running.fbx $PWD/rigged --profile plaid   # Kai, likewise
blenv/bin/python meshy_bag.py -- fit $PWD/rigged/PrimaryBoy.blend $PWD/BagKickOff.blend $PWD   # ...the bag fitted to Kai
blenv/bin/python meshy_bag.py -- prep /abs/purple_kick_off_backpack.fbx $PWD --id KickOff   # the Locker Room's bag
blenv/bin/python meshy_bag.py -- fit $PWD/rigged/PrimaryBoy2.blend $PWD/BagKickOff.blend $PWD   # ...fitted to Leo
blenv/bin/python meshy_bag.py -- icon $PWD/BagKickOff.blend $PWD/bag_kickoff.png   # its Locker Room picture
    # (PrimaryBoy2.fbx/.blend/.json, PrimaryBoy2Atlas.png; see "Leo and the bags" below; primary.py --boy2 would overwrite it)
blenv/bin/python meshy_teen.py -- /abs/little_star_in_plaid.fbx $PWD --profile plaid   # Kai, from a supplied model
    # (PrimaryBoy.fbx/.blend/.json, PrimaryBoyAtlas.png; primary.py --boy would overwrite it)
blenv/bin/python meshy_teen.py -- /abs/little_explorer.fbx $PWD --profile explorer   # Mia, from a supplied model
    # (PrimaryGirl.fbx/.blend/.json, PrimaryGirlAtlas.png; primary.py --girl would overwrite it)
blenv/bin/python meshy_teen.py -- /abs/rainbow_unicorn.fbx $PWD --profile unicorn   # Zoe, from a supplied model
    # (PrimaryGirl2.fbx/.blend/.json, PrimaryGirl2Atlas.png; primary.py --girl2 would overwrite it)
blenv/bin/python teen.py -- $PWD/Boy.fbx --boy     # (the earlier, scripted boy; it would overwrite the files above)
blenv/bin/python teen.py -- $PWD/Girl.fbx --girl   # the playable teen girl
blenv/bin/python primary.py -- $PWD/PrimaryBoy.fbx --boy      # the four primary-school kids (see below); also
blenv/bin/python primary.py -- $PWD/PrimaryGirl.fbx --girl    # teen.py ... --primary-boy / --primary-girl /
blenv/bin/python primary.py -- $PWD/PrimaryBoy2.fbx --boy2    # --primary-boy2 / --primary-girl2 (the earlier, scripted Leo)
blenv/bin/python primary.py -- $PWD/PrimaryGirl2.fbx --girl2
blenv/bin/python review_teen.py -- $PWD/Girl.blend $PWD/girl_sheet.png [--bg shot1.png,shot2.png,shot3.png]
    # review sheet with the game's toon shading: faces, poses, side, back, and the teen at in-game
    # size (215 px tall, in-game outline) standing and running in front of game screenshots
    # (the primary kids' bigger heads: add --face-dz 0.07 --face-scale 0.5)
blenv/bin/python review_poses.py -- $PWD/Boy.blend $PWD/boy_poses.png --jobs 3 --leaks
    # the pose audit (see below): the teen in every pose the game uses, from the game's camera yaws
cp Boy.fbx Boy.json BoyAtlas.png Bicycle.fbx BicycleAtlas.png Girl.fbx Girl.json GirlAtlas.png ../../Assets/_Game/Art/Models/
cp BackpackBoy.fbx BackpackBoy.json BackpackBoyAtlas.png ../../Assets/_Game/Art/Models/
cp PrimaryBoy2.fbx rigged/PrimaryBoy2.json rigged/PrimaryBoy2Atlas.png ../../Assets/_Game/Art/Models/   # (Leo, with his bags)
cp BagKickOff.json BagKickOffAtlas.png ../../Assets/_Game/Art/Models/ && cp bag_kickoff.png ../../Assets/_Game/Resources/UI/
cp PrimaryGirl2.fbx PrimaryGirl2.json PrimaryGirl2Atlas.png ../../Assets/_Game/Art/Models/   # (Zoe, from meshy_teen.py)
cp PrimaryGirl.fbx PrimaryGirl.json PrimaryGirlAtlas.png ../../Assets/_Game/Art/Models/   # (Mia, from meshy_teen.py)
cp PrimaryBoy.fbx rigged/PrimaryBoy.json rigged/PrimaryBoyAtlas.png ../../Assets/_Game/Art/Models/   # (Kai, with his bags)
cp Primary*.fbx Primary*.json Primary*Atlas.png ../../Assets/_Game/Art/Models/
blenv/bin/python portrait_teen.py -- $PWD/Boy.blend $PWD/PlayerBoy.png --yaw 28     # the menus' player cards
blenv/bin/python portrait_teen.py -- $PWD/Girl.blend $PWD/PlayerGirl.png --yaw -28  # (they face each other)
blenv/bin/python portrait_teen.py -- $PWD/BackpackBoy.blend $PWD/PlayerBackpackBoy.png --yaw 28
cp PlayerBoy.png PlayerGirl.png PlayerBackpackBoy.png ../../Assets/_Game/Resources/UI/
blenv/bin/python portrait_teen.py -- $PWD/PrimaryBoy.blend $PWD/PlayerPrimaryBoy.png --yaw 28 --span-heads 2.3     # the primary kids' cards
blenv/bin/python portrait_teen.py -- $PWD/PrimaryGirl.blend $PWD/PlayerPrimaryGirl.png --yaw -28 --span-heads 2.3  # (boys turn right,
blenv/bin/python portrait_teen.py -- $PWD/rigged/PrimaryBoy2.blend $PWD/PlayerPrimaryBoy2.png --yaw 28 --span-heads 2.3   #  girls left)
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
- Boy: made from a textured model the user supplied (a boy walking his bicycle, hand-painted in the look of 1990s anime
  films; see "The boy" below), not by the teen scripts: black hair in a full, rounded cut with a ragged fringe, a long
  oval face, big dark eyes, light skin; a cream short-sleeved school shirt with a breast pocket, buttoned to its collar
  and tucked into charcoal trousers with a black belt, black canvas shoes on white soles. No tie and no bag (the shop's
  accent has nothing to recolour on him; the pennant rides on his Chest bone as before).
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
heights (1.5 and 1.43) the boy stands about 1.77 m and the girl about 1.65 m (hair included).

What the model carries:
- One skinned mesh, one material: vertex colours times the atlas (the face is painted in the
  atlas' upper-left quadrant, the ears' folds in the upper-right; everything else samples its white
  corner, except the boy's hair, which samples the hair tile beside it: `face_teen.HAIR_TILE`, fine
  dark strand lines and a soft shade at the roots, laid across and along each lock and down the cap
  from the crown by `teen_hair`, so the hair reads as strands while keeping its flat cel colours).
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

### The boy (`meshy_boy.py`)

The playable boy comes from a textured, single-mesh model the user supplied: a boy walking his green bicycle, both in one
fused scan-like surface (about 270,000 triangles), with one 2048 base-colour texture and no rig. `meshy_boy.py` turns it
into the same contract as the teens (one skinned mesh `Kid` under `KidRig`, one material of vertex colours times the
atlas, the outfit part in UV 2, the game's bones, a Nose marker, `Boy.json`), and the bicycle into a prop:
- split: each vertex is his or the bicycle's by its texture colour and side: the bicycle stands in its own plane at his
  right, green, grey and black; he is skin, his cream shirt (his right sleeve crosses that plane) and anything else off
  it; the handlebar's grips in his hands are dropped; he is the largest connected piece of that. Face normals are made
  consistent.
- tidy: scaled to 2.14 tall with his feet on z = 0, his hips over the origin, facing -y.
- joints, from the mesh itself: the crotch is the highest cross-section of two outlines, each leg's centreline the
  centres of its outlines below; the knee half way down, the ankle above each heel (his right heel is lifted, mid-stride);
  each arm's skin below the sleeve is a piece of its own, its far end the fingertips, the elbow the corner of the arm's
  centreline (the centres of rings of equal distance from the fingertips); shoulders inside the sleeves' outline, the
  neck at the collar, the Head joint at 0.85 of his height.
- separate: what touches in the scan but must move apart is cut: his thighs and shoes (each vertex below the crotch goes
  with the nearer leg's bones), his left fist from the belt (only below the elbow, where the arm's surface is skin or
  faces away from its bones), and the black scraps of the grips in his fists; each side's holes are closed with a fan of
  triangles in one colour, never across two sides.
- rig and re-pose: the game's bones on the joints as they stand, bone-heat weights (a vertex the heat misses takes its
  nearest bone; below the crotch a leg takes nothing from the other leg's bones; smoothed; four bones a vertex); then
  arms hanging (both were holding the handlebar), forearms a touch forward, legs straight under the hips with both
  ankles at the flat foot's height (the bent back leg, which measures short, stretches 0 to 7 %), feet flat and ahead,
  the head lifted 16 degrees (he looked down at the bicycle). That is baked into the mesh and made the rest pose
  (`CharacterRig` swings every joint from its rest), and the weights are made again on it.
- paint: the part of each face by its texture colour, its bones and its height: the hair (the biggest dark piece of the
  head) 3, the shirt 1 above the belt, the trousers 2 below it, the face, skin, forearms, hands, belt and shoes 0. In
  the atlas (the source texture) the shirt's, trousers' and hair's texels are divided by their part's colour (a band of
  its brighter texels, so the atlas there is about white with the shading below it; the trousers' white flecks are
  clamped away), which their vertex colours carry instead and `Boy.json` names, so the shop's outfits recolour them
  (`ModelOutfit`) and the default looks as the model did.
- the bicycle: 20,000 triangles (its frame and spokes are thin shells that fall apart below that), along x and leaning
  4 degrees away from the camera as if on its stand, in the game's metres (the scale the game gives him, from his neck
  height of 1.5), its texture at 1024. The level builder parks it on the lawn of the home front
  (`LevelBuildKit.OwnBicycle`, in place of the Street kit's bicycle; that one stays the fallback).

It writes `debug_joints.png` (the joints over his vertices) next to its outputs. Check the result with `review_teen.py`
and `review_poses.py` as for the teens. 30,000 triangles; the Head joint at 0.846 of his height, so at the game's neck
height of 1.5 he stands 1.77 m (`PlayerRoster`).

### The backpack boy and the primary-school kids (`meshy_teen.py`)

Five kids come from textured, single-mesh models the user supplied (Meshy, about 300,000 triangles, one 2048
base-colour texture plus normal, roughness and metallic maps that are not used, no rig). `meshy_teen.py` makes each in
the game's contract (one skinned mesh `Kid` under `KidRig`, one material of vertex colours times the atlas, the outfit part
in UV 2, the game's bones, Nose and Bag markers, `<Name>.json`), reusing `meshy_boy.py`'s helpers (mesh queries,
cross-sections, the painting of the atlas). What differs between the models is a profile (`PROFILES`): the backpack's
colour, the outfit parts' colour rules, whether he needs shoes, how tall he stands, how much the backpack swings and the
colours that are never an arm's.
- **Max** (`--profile backpack_boy`, `BackpackBoy`): a teen in an A-pose; ginger hair, a light denim jacket open over a
  grey hoodie and a white T-shirt, dark navy jeans, white sneakers with black stripes, a brown backpack on both shoulders.
  Parts: the jacket 1, the jeans (and their waistband where the jacket hangs open) 2, the hair 3. 1.75 m, Head bone at
  0.878 of it (neck height 1.537).
- **Leo** (`--profile first_day`, `PrimaryBoy2`, in place of the scripted boy 2): a primary-school boy standing with his
  arms down, his forearms and hands resting on his trouser pockets, and barefoot; short black hair, a white sweatshirt
  with purple raglan sleeves and a "0" on the front, khaki cargo joggers with a red drawstring, a purple backpack. Parts:
  the sweatshirt's white 1 (its purple stays), the joggers 2, the hair 3. 1.32 m, Head bone at 0.836 of it (neck height
  1.104). His sneakers are made by the script (below). The backpack takes half the game's swing (it is fused to much of
  his back).
- **Zoe** (`--profile unicorn`, `PrimaryGirl2`, in place of the scripted girl 2): a primary-school girl standing with her
  arms down, her hands by her pockets; black hair pulled back into a long braid down her back, a pink jacket in a
  rainbow-unicorn print with a white hood lining, open over a white T-shirt, terracotta trousers, black shoes, and a
  backpack in the jacket's own print. Parts: the jacket 1 (the shop's colours turn its print into shades of one
  colour), the trousers 2, the hair with the braid 3. 1.29 m, Head bone at 0.830 of it (neck height 1.070). Her pack has
  no colour of its own (`'pack': 'shape'`): it is whatever, bar the dark hair, stands 3 cm or more behind her back line
  (the back's furthest point where it is least, between the crotch and the chest), and it takes half the game's swing.
- **Zoe, rainbow friends** (`--profile rainbow`, `PrimaryGirl2`, in place of the earlier unicorn Zoe): from the user's
  four-view drawings via Meshy; black hair in a long braid, a hot-pink animal-print bomber over a grey hood and a pink
  T-shirt, coral cargo joggers, dark clogs, a pink backpack. Meshy printed the jacket's pattern on the backpack, so
  `paint_pack` repaints it from the drawings: glitter pink, with a unicorn panel facing out (chevrons in pink, purple,
  yellow and teal under a purple horn and blue ears). The pack is found by its shape (`pack_faces`: behind the back
  line, from the body's least depth at the seat; not the braid, nor the arms) and rides the Bag and Chest bones alone
  (`pack_rigid`), so it no longer swings with the arms. Parts: the jacket 1, the joggers 2, the hair 3. 1.29 m, Head
  bone at 0.825 of it (neck height 1.064).
- **Mia** (`--profile explorer`, `PrimaryGirl`, in place of the scripted girl 1): a primary-school girl in an A-pose;
  shoulder-length black hair with a sparkly headband, a white T-shirt, wide red shorts, bare legs, white socks, pink
  sneakers and a backpack with a bow (found by its shape: its beige is close to her skin). The model made the pack
  beige; in the reference photos it is light denim on beige straps, so `'pack_tint'` recolours the pack's beige texels
  on the faces that follow the Bag bone (`tint_pack`), keeping their shading; the straps over her shoulders stay beige.
  `'shoulders'`: round each upper arm (within `SH_R` of the arm's thickness) the arm's weight rises smoothly along
  its bone from `SH_IN` inside the shoulder joint to `SH_OUT` past it, so the short sleeve moves with the arm and
  the backpack's straps, lying on the shoulders, stay there as the arms swing (they slid off with the arm before). Parts: the T-shirt 1,
  the shorts with their waistband 2, the hair 3, each judged by the texture at the face's own centre (`face_colours`:
  her texture is cut into many small islands, so a vertex's averaged corners mix neighbouring islands). 1.27 m, Head
  bone at 0.809 of it (neck height 1.028). Her wide shorts hide where her legs meet: the legs show only below their
  hems, so the crotch is put 0.10 of her height above where they part, and the cut between the legs (`legs_apart`)
  parts the shorts down the middle.
- **Kai** (`--profile plaid`, `PrimaryBoy`, in place of the scripted boy 1): a primary-school boy standing with his
  hands by his pockets; short black hair, a loose red plaid flannel shirt over a white hood, light-blue cargo jeans,
  chunky black-and-white sneakers and a grey backpack. Parts: the shirt with its hood 1, the jeans 2, the hair 3, by each
  face's own colour. 1.30 m, Head bone at 0.840 of it (neck height 1.092). His grey pack is found by colour (a grey: any
  hue, little saturation), judged per face (`'face_colours'`). His baggy sleeves are fused to the shirt all the way
  down, so only his hands show apart from the body: the shoulders are then taken from the torso's outline and each arm
  runs straight from it to the hand (`hand_only`); the sleeve is split from the shirt up to the armpit along the seam
  (faces kept, the edges between the two sides split, `bmesh.ops.split_edges`, so nothing is missing at rest; each
  side's opening closed in its rim's colour), the fingertips fused to the pockets go with the hands, loose crumbs are
  dropped, and only each arm's own piece takes its bones (the chest's pull ends at the elbow). Leo and Zoe, whose
  forearms rest against their pockets, get the same split (`'split': True`): cutting a strip out between arm and body
  left holes that showed dark shards of the inside as the arms swung.

Why the scanned kids are not as clean in motion as Max: Max was generated in an A-pose, his arms clear of his body, so
nothing has to be cut apart. Leo, Zoe and Kai stand with their arms against their bodies, and Meshy fuses them: the
underside of the sleeve and the side of the shirt under it were never made, so the split closes them with flat
patches, and loose jackets and shirts smear as the arms lift. Mia, generated in an A-pose, is the cleanest of the four.
The way to make a kid as clean as Max is to generate the model in an A-pose (Meshy's pose option), arms a hand's width
from the body.

The steps:
- tidy: decimated to 100,000 triangles first (30,000 before: it squashed the hands into mittens and the faces' features), scaled to the teen boy's 2.14 (the game scales by the neck anyway) with the
  feet on z = 0, the head centred over the origin (Leo stands unevenly). The models already face -y.
- joints, from the mesh: each arm from its own cross-sections, going down from the shoulders: the outermost small outline
  on that side, beside the body (not behind it: the backpack), from where it parts from the torso down to the hand,
  passing over short gaps where it touches the body; of the runs of outlines that follow on from one another the
  longest is the arm (a sleeve's edge by the shoulder, Zoe's hood and Mia's sleeve, are short runs of their own); a
  straight line is fitted through them, the fingertips just below
  the lowest. The crotch is the highest cross-section (the arms left out), with the one 1 cm below it, of two outlines of a size
  side by side (none above 0.30 of the height, under wide shorts: see Mia) (a
  jacket's hem and a backpack's bottom are one in front of the other, so they don't count); each leg's centreline below
  it, the knee half way to the ankle. The neck is the narrowest cross-section of the middle (the Head joint 2 cm over
  it), but no lower than 3 % of the height under the chin (where the front steps back 4 cm going down the face: Zoe's
  hood and braid make her narrowest section fall on her shoulders), the shoulders 0.065 of the height below it on the arm's line (kept inside the torso), the wrist 0.2 up from the
  fingertips and the elbow half way down, both on the arm's line; the spine and the chest at 0.41 and 0.68 of the way
  from the crotch to the shoulders, 12 cm behind the front (a backpack makes the back no guide).
- separate: legs joined below the crotch would be cut apart (neither model's are). Arms touching the body (Leo's) are
  cut free: below the armpit a point is the arm's if it is nearer the arm's line than the body's axis (the spine, or a
  leg), each distance in that part's own thickness (the arm's from its cross-sections, the torso's from the shoulders'
  width, a leg's from its cross-sections), leaving out the colours that are never an arm's (his joggers); the arm is
  what of that joins the fingertips; a small loose piece by the forearm or the hand (a bit of a hand the cut left
  behind, Zoe's) goes with the arm. The faces between go and each hole is closed (`holes_fill`, then a fan for what
  is left), in the texture's colour at its rim.
- weights by nearness to the bones (an exponential falloff of 2.2 cm past the nearest bone, smoothed, four bones a
  vertex): bone heat finds no solution on these scans (layered, open shells; hundreds of non-manifold edges). Below the
  crotch each leg takes only its own bones and the hips'; nothing else takes a leg's bones; only the head above the jaw
  takes the Head bone, and everything within the head's radius above 2 cm under the Head joint takes it alone (rigid),
  fading to the neck over 6 cm below (`HEAD_BLEND`): by nearness the jaw and cheeks took half their weight from the
  Neck bone and the face folded when the menu kid's head turned to follow the ball; below the armpits each arm (a piece of its own once cut free) alone takes its arm's bones, and
  only those and the chest's.
- re-pose: the arms hang relaxed, about 15 degrees from the sides with the forearms bent about 17 degrees forward (they hung straight down against the body before), the legs are turned in under the hips so the ankles stand 3 cm outside
  them (the feet turned back flat); baked in and made the rest pose, keeping the weights.
- the backpack: the biggest piece of the profile's colour more than a few centimetres behind the back (the arms' sleeves
  left out) follows a Bag bone (on the Chest, its head at the pack's top, so the shop's pennant clips there), fading
  into the back over 6 cm and a little smoothing, so the game's swing bends the pack rather than tearing it off; the
  straps over the front stay on the chest.
- paint: by the profile's colour rules (above); no accent part. As for the boy, those parts' texels in the atlas are
  divided by their colour, which their vertex colours and the json carry.
- shoes (Leo): each foot's vertices below the collar (3.5 cm over the ankle joint) give a sneaker: a loft from heel to toe
  of rounded-box cross-sections as wide as the foot there below the ankle joint (a trouser cuff hanging lower would
  make it bulge) and 1.6 cm out from it, its top the foot's height smoothed along the foot (never below the foot) and
  rising in a tongue from the toe box to the collar, each section grown till every point of the foot near it is inside
  (spread along the shoe, so neighbours never fold), then each side and the top filled so they have no dip along the
  shoe (the foot's triangles would cut through one: a slit of skin showed in the kick); the ends rounded and closed, a
  flat sole 3 cm thick a little wider than the upper (everything is raised by it). Coloured by vertex colour over a
  white patch painted in the atlas's largest unused area: a white upper, a purple band above the sole and a purple heel
  tab (his sleeves' and backpack's purple), an off-white sole with a grey tread; outfit part 0. The shoe and the leg in
  it are skinned alike (`shin_share`): the foot bone up to 1.5 cm over the ankle joint, the shin's share rising to half
  at the collar and to all of it 5 cm above (the game swings the shin, not the foot, so the shoe moves with the leg).

It writes `<Name>_joints.png` (the joints over the vertices, before the re-pose). Both were checked with
`review_poses.py` (every game pose from the game's yaws; Leo's feet close up with `--focus 0,0.3`) and their cards with
`portrait_teen.py --yaw 28` (Leo's `--span-heads 2.3` like the other primary kids). Known limits: where Kai's
sleeves were split from his shirt the closed openings show as flat patches of one colour on the shirt's sides, and his
plaid stretches at the shoulders as his arms swing; with his arms raised
high (the celebration) Leo's sweatshirt creases sharply at the shoulders; the hole fills where his arms were cut free
can show as a small pale patch on the trousers close up. The scanned faces (Leo, Zoe, Mia) show soft-edged patches of
tone up close on the cards: that is lighting Meshy baked into small texture islands, not the geometry (smoothing the
face's shape, clearing the import's sharp edges and sparing the face in the decimation were all tried on Mia and
changed nothing visible).

### Leo, Kai and the bags (`meshy_rigged.py`, `meshy_bag.py`)

Kai's second supplied model came the same way and goes through the same steps (`--profile plaid`, meshy_teen's colour
rules for him); its skeleton has two extra bones on the shins (the jeans' cuffs), which go with their parent's game bone,
as any extra bone does. Leo's second supplied model came rigged: Meshy's own Mixamo-style skeleton (66 `mixamorig:` bones, fingers included)
and skin weights, in an A-pose, with no bag, exported with a running animation. `meshy_rigged.py` keeps all of that
instead of guessing from the mesh as `meshy_teen.py` must: the animation is dropped for the rest pose, the mesh is
decimated to 100k triangles (its weights carried along), scaled like the others, and the game's joints are the
skeleton's own (the spine's three bones become Hips, Spine and Chest; the collar bones go into the Chest, the fingers
into the Hand, the toes into the Foot), each vertex keeping its four strongest bones. The arms then hang relaxed and the
legs come in under the hips (`meshy_teen.repose`), the Nose marker goes on the face and the Bag marker on the middle of
his upper back, where the bags hang. Parts: 1 the sweatshirt's white (its navy panel and print stay), 2 the khaki
joggers, 3 the hair. Every pose is clean, the arms-up ones included (the scans with arms fused to the body could not be).

The bags are optional, chosen per kid in the Locker Room (`Cosmetics/Bags`). `meshy_bag.py prep` turns a supplied
backpack (one textured mesh, its padded straps hanging in a "D" as if worn) into `Bag<Id>.blend`: 30k triangles, the
straps toward the wearer (-y), the back panel's top middle at the origin, the body one unit tall; and `Bag<Id>Atlas.png`
(1024), the texture with the cloth marked in its alpha (0: the purple cloth; 1: the zips, the logo, the mascot, the black
mesh pockets), which the game's character shader recolours to the Settings colour, keeping the cloth's light and shade
(`_MaskTint`, against `_MaskBase`: the cloth's colour in `Bag<Id>.json`). `fit` hangs it on a kid: sized to 92 % of the
back's width (1.24 times the span between the shoulder joints: a loose shirt's skin weights can't say where the arm
starts; or the marker-to-hips height), the padded straps narrowed to 70 % where they leave the bag (sized for the bag,
they read as a vest on a child), its panel just behind the back, then the straps' "D" made as deep as the
chest, its top run lifted over the shoulder, its lower front run drawn out toward the side (under the arm: 0.74 of a shoulder joint's reach out), anything
left under the clothes pushed out 1.2 cm and smoothed; the body is skinned to the Bag bone (the game swings it at 0.3 of
a sewn-on bag's swing: `CharacterRig.bagSwing`), the straps to the Chest, blending where they meet the bag. The kid is
exported again with the bag as a second mesh, `Bag_<Id>`, which `LevelBuildKit` gives the bag's material and
`Presentation/BagWear` shows when that kid wears it. A new bag: `prep` it, `fit` it to each kid who wears bags (re-export
them), `icon` it into `Resources/UI/bag_<id>.png`, and add a row to `CosmeticsTable` (id `bag_<id>`). `review_poses.py`
renders the bags with the kid (`--tint r,g,b,lum` previews a Settings colour).

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
| `PrimaryBoy` | boy 1 (Kai) | now made from a supplied rigged model by `meshy_rigged.py --profile plaid` (see "Leo, Kai and the bags" above): short black hair, a red plaid flannel shirt over a white hood, light-blue cargo jeans, chunky black-and-white sneakers; no bag of his own (he wears the Locker Room's). The scripted boy 1 below is what `primary.py --boy` still builds | plaid shirt / light-blue jeans / none / grey / black |
| (scripted boy 1) | | fair skin, round dark eyes, short black hair with a broad fringe and a small tuft; a polo with a flat collar, navy shorts, long white crew socks, white sneakers | white / navy / yellow neckerchief / blue / black |
| `PrimaryGirl` | girl 1 (Mia) | now made from a supplied model by `meshy_teen.py` (see "Mia" above): shoulder-length black hair with a headband, a white T-shirt, red shorts, white socks, pink sneakers, a beige backpack with a bow. The scripted girl 1 below is what `primary.py --girl` still builds | white T-shirt / red / none / beige / black |
| (scripted girl 1) | | fair skin with freckles, big warm-brown eyes, a centre-parted fringe and two bunches at the sides with red ties; a blouse with a round navy collar, a navy pleated skirt, white knee socks, brown school shoes | white / navy / red bow / red / dark brown |
| `PrimaryBoy2` | boy 2 (Leo) | now made from a supplied rigged model by `meshy_rigged.py` (see "Leo, Kai and the bags" above): short curly black hair; a white long-sleeved "AWESOME 01" sweatshirt with a navy chest panel, khaki cargo joggers, white-and-navy sneakers; no bag of his own (he wears the Locker Room's). The scripted boy 2 below (tanned, chestnut spikes, round glasses; a polo and grey shorts) is what `primary.py --boy2` still builds | white sweatshirt / khaki / none / the Locker Room's / black |
| `PrimaryGirl2` | girl 2 (Zoe) | now made from a supplied model by `meshy_teen.py` (see "Zoe" above): black hair in a long braid, a pink rainbow-unicorn jacket over a white T-shirt, terracotta trousers, black shoes, a backpack in the jacket's print. The scripted girl 2 below is what `primary.py --girl2` still builds | unicorn jacket / terracotta / none / the jacket's print / black |
| (scripted girl 2) | | medium-brown skin with a beauty mark, hazel eyes, a black bob with a straight fringe and a yellow hairband; a blouse with a round white collar under a grey pinafore (bib and straps), white socks, black school shoes | white / grey / yellow bow / purple / black |

The game scales every model so that its Head bone sits at the neck height it is given (`LevelBuildKit.BuildModelCharacter`;
the teen boy's 1.5 stands 1.73 m, the girl's 1.43 stands 1.65 m), so only proportions matter. They are 5.2, 5.2, 4.9 (his
spikes add 6 cm) and 5.1 heads tall counting the hair, and `primary_spec.HEIGHT` says how tall each should stand; a build
prints the neck height that gives it:

| File | Standing height (hair included) | Neck height to give the game | Triangles |
|---|---|---|---|
| `PrimaryBoy` (Kai, `meshy_rigged.py`) | 1.30 m | 1.101 | 100,000 (+ the Kick Off backpack, 30,000) |
| `PrimaryGirl` (Mia, `meshy_teen.py`) | 1.27 m | 1.028 | 29,925 |
| `PrimaryBoy2` (Leo, `meshy_rigged.py`) | 1.32 m | 1.114 | 99,999 (+ the Kick Off backpack, 30,000) |
| `PrimaryGirl2` (Zoe, `meshy_teen.py --profile rainbow`) | 1.29 m | 1.064 | 29,898 |

(The scripted models are 1.685, 1.646, 1.784 and 1.694 m tall as exported, their Head bones at 1.38, 1.345, 1.44 and 1.38 m; neck
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

## App icon

The store icon: the teen boy running to school after a big football, in the game's toon look, under a morning sky with the
sun rising behind him, on the logo's mown pitch with its chalk speed lines, and the logo's sunny "2" in the corner.

```
blenv/bin/python app_icon.py -- $PWD/Boy.blend $PWD/icon_layers      # kid.png (2048) and ball.png (1024), transparent
python3 app_icon_compose.py $PWD/icon_layers ../.. --two --preview $PWD/icon_preview
```

`app_icon.py` poses the boy (a sprint: the near arm back, the far hand up, a stride, leaning in, his face turned a little
toward us) and shoots him with a 46 mm lens, lit from behind his left shoulder with a warm rim; the ball is a truncated
icosahedron (crisp pentagons and seams). `app_icon_compose.py` draws the rest at 2048 px and writes:

| File | What |
|---|---|
| `marketing/appstore/icon_1024.png` | App Store icon, 1024 × 1024, opaque (iOS rounds the corners) |
| `marketing/googleplay/icon_512.png` | Google Play listing icon, 512 × 512 |
| `Assets/_Game/Art/Icon/AppIcon.png` | the icon in the app for every platform (`BuildScripts.ApplyIcon`; Unity scales it) |
| `Assets/_Game/Art/Icon/AppIconBackground.png`, `AppIconForeground.png` | Android's adaptive icon: the sky and pitch; the kid and the ball with his face and the ball inside the 66 dp circle every launcher's mask keeps (no "2": a round mask would clip it) |

Without `--two` the corner is plain sky. `--preview` writes the icon masked as iOS (rounded square) and Android (circle) show
it, from 300 px down to 40 px: check the face, the ball and the "2" still read at the small sizes after any change.

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
| Plants | `kit_plants.py` | conifers, broadleaf trees (five), a cloud-pruned garden pine, birch, cherry, palms (a tall California fan palm and a date palm among them), bushes, hedge blocks, grasses, reeds, flowers; the trees' and bushes' leaves are cut-out leaf-clump cards (`kit_plants_leaves.py`) |
| Buildings | `kit_buildings.py` | gabled and long houses, bungalow, fruit shop and bakery, flats, warehouse, school, garage; the town's shops and houses (`kit_buildings_town.py`): a small supermarket, cafe, bookshop, florist, noodle house, convenience store, two narrow tiled three-storey buildings, a white house with a corrugated lean-to and a garden pine, a flat-roofed house with a balcony, a house with a carport; `KIT_SIGNS=CA` writes only `BuildingsCAAtlas.png`, the same atlas with English shop names, for the California skin |
| Coast | `kit_buildings.py --kit Coast` | the California skin's town (built into the levels' `_CA` scenes only; `kit_buildings_cal.py`, its own 4096 x 4096 atlas at about 2.8 x the Buildings kit's texel density: 96 px/m on the fronts, so a villa's front is some 1300 px across): a stucco villa with a garage, a ranch house with solar panels, a Craftsman house with a front porch, a beach condo, a surf shop, a Spanish Revival shop, a pier span and the pier's end with its roundhouse; hipped roofs of barrel tiles (the atlas' `hip` feature) |
| Street | `kit_street.py` | utility pole (concrete; `UtilityPoleWood` for the California skin), lamp, pedestrian signal, walls, fences, hoarding, planters, benches, vending machines, signs, crates, pots, stalls, awnings, A-frame board, banner flag, electrical cabinet, bicycle hoops, wheelie bins, doorstep pots |
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
their name goes on, the 17 stops between the levels at their places, and the anchors for the district and street names. Both come from one layout
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
| park | up the West Street, west by Rose Street and Park Lane to the park gate, east through the park (a path past the bandstand, the cafe, the boathouse and grandpa's allotment, then a short tunnel under the railway), down the East Street to the school |
| underpass | up the West Street to Station Road, east past the building site to the station's hall at the foot of the railway bridge, through the road tunnels under the railway (two tracks), down the East Street |
| site | up the West Street to Yard Road, east through the building site (a track between two fenced yards, the site office at a security gate halfway), the East Street |
| street | Elm Street straight east (Elm Street, Hill Road, Garden Lane), the East Street (Puddle Lane) |
| market | down the West Street to Market Street, east through the market, up the East Street |
| beach | Seaside Road along the south, then the boardwalk along the sand to the school's promenade and back west along School Lane |

The railway comes down from the north and ends at a small station just south of Station Road, its
ticket hall on Station Road at the foot of the bridge. Only the park and underpass routes cross it, and
they go under it; no route has a level crossing.

### TownMapLayout.json

UTF-8, plain objects (it reads with `JsonUtility`), image pixels with the origin top-left:

```
{ "image": "UI/TownMap", "width": 3200, "height": 1800, "core": {x:400, y:225, w:2400, h:1350},
  "places":    [ {id:"home", x, y}, {id:"school", x, y} ],
  "routes":    [ {id, points:[{x, y} ...]} ...  in RouteTable order: street, market, beach, underpass, site, park ],
  "nodes":     [ {id, x, y, label} ... 28: L01 to L23 then C01 to C05; label is "below", "above", "left" or "right" ],
  "districts": [ {id, x, y} ... neighbourhood, market, beach, park, railway, site, school, sea ],
  "streets":   [ {name, x, y, angle} ... 12 names on straight stretches; angle in degrees, clockwise on screen positive (y down), as the game reads it ],
  "stops":     [ {id, route, x, y} ... the 17 stops of RouteTable in its order, each where the picture shows the place, on its route ] }
```

Each route starts at the home and ends at the school (within 25 px), is smooth (30 to 90 points,
follows its roads), at least 1200 px long and keeps 90 px from the other routes except within 300
px of the home and the school. A story node lies on its route (within 12 px), in play order, on its
own leg (between the stop or home it starts at and the stop or school it ends at), near the start of
it: a route's first node past the stem it shares with other routes near home (where the route is 75 px
from every other route) and at most 500 px along beyond it, every later node at most 260 px along after
its stop (the layout's anchors put them 128 px after it). A stop lies on its route (within 2 px) between
its two levels' nodes, 100 px from every node. A challenge node is 130 to 260 px beside its route; nodes
are 190 px apart and 120 px from the places.
A level's name is a 300 x 56 px box 10 px off the node's 150 px disc on the node's `label` side. The
map screen draws the names of the focused route's levels only, over every route line, with the other
routes' nodes at 70 % while a route is in focus, so a name keeps 30 px from its own route's centre line
and only must not cross the other routes' lines, it keeps 6 px from its own route's node discs and from
the other routes' discs as drawn then (70 %), 6 px from its own route's stop markers, and 6 px from the
names of the levels of its own route (names of different routes may overlap). The street whose name is a route's name (Home Street, Market Street,
Seaside Road) lies within 60 px of that route on a stretch the route uses; Elm Street, Hill Road,
Garden Lane and Puddle Lane are beside L02 to L05; no street is called after a level except Puddle
Lane (L05); the road through the railway tunnels is Station Road.

`town_map_check.py` (pure Python, no bpy or numpy) checks all of this against `RouteTable.cs` and
`StringTables.cs`, plus the level / map rules below when `town_map_layout.py` sits next to it, and
exits 1 with every broken rule printed.

### How it is made

| Module | What it does |
|---|---|
| `town_map_layout.py` | the layout as data: junctions, roads (control points of smooth curves), the areas (sea, sand, park, school, market, site, station), the stops (`STOPS`), where each level is (`STORY`: an anchor, or None for 128 px after its stop), the zones of the levels and stops, the district and street-name wishes |
| `town_map_graph.py`, `town_map_build.py` | the road graph; each route is the shortest path through its waypoints, smoothed and resampled to 30 to 90 points; districts and street names are put on straight stretches clear of the nodes; writes the JSON |
| `town_map_nodes.py` | places the 28 nodes and their name sides: an exact constraint search (arc consistency, challenge nodes first) near the anchors the layout gives, each story node inside its own leg and 100 px from every stop |
| `town_map_levels.py` | the level / map checks: zones and railway crossings (below) |
| `town_map_raster.py`, `town_map_ground.py` | the flat ground painted as a texture: land, sea with foam, sand, lawns, roads with kerbs, pavements and paint, boardwalks, railway bed, paths |
| `town_map_place.py` | houses and shops along the roads' frontages, infill, garden fences and hedges, trees (round crowns and kit conifers), cars on the kerbs, lamps |
| `town_map_sets.py`, `town_map_sets_nature.py`, `town_map_sets_works.py` | the set pieces placed from the solved nodes: the home and what each level shows beside its node and along its leg |
| `town_map_sets_stops.py` | the stops at their places: the bus stop, granny's, the church, Sam's, the four shops, the surf school, the lifeguard tower, the beach cafe, the station's hall, the site office, the bandstand, the park cafe, the boathouse, the allotment |
| `town_map_kit.py`, `town_map_scene.py` | the Blender side: kit FBXs and characters as linked duplicates, a low sun with soft shadows, a camera looking down with a long lens |
| `town_map_plan.py` | the debug overlay: routes, nodes, stops and name boxes drawn over the picture |
| `town_map_check.py` | the validator |

## Level and map

What the levels contain is what the map shows at their nodes and along their legs, and what the levels
forbid, the map does not show. The layout (`town_map_layout.py`: `STOPS`, `LEVEL_ZONE`, `STOP_ZONE`,
`CHECK_ZONES`, `CHALLENGE_ZONES`) and `town_map_levels.py` check it on every build and in `town_map_check.py`.

Every route is one trip from home (Levels/RouteTable.cs): its first level starts at home, each later one
at the stop the level before it ended at. So a level's node sits near the START of its leg: a route's
first node on the first stretch the route has to itself, past the West Street or Elm Street it shares
with other routes outside the house; every later node shortly after the stop it starts from. The stops
are real places in the picture (`town_map_sets_stops.py`), and a level's scene lies from beside its node
on along its leg to the stop it ends at.

Rules: (1) only the underpass route (under two tracks, both in L18) and the park route (once, by a short
tunnel, in L23) cross the railway, and they go under it; the street, market, beach and site routes never
cross it, not even by a level crossing; L15 reaches the station's hall at the foot of the railway bridge
only at its end, so its dark stretches are the building site's covered walkways, not the railway; (2) the
school is by the sea and has a football pitch; (3) the site route has no tunnel; (4) the home, and the
start of every route, is the residential street round the red-door house. Every story node lies in the
zone of its level: L01 to L05 `residential`, L06 to L10 `market`, L11 `to_the_sea` (the West Street down
from the market corner and Seaside Road), L12 to L14 `sand`, L15 `station_road` (the West Street up from
the stem and Station Road to the railway), L18 `underpass` (Station Road at the railway), L16 `yard_road`
(Yard Road to the site's gate), L17 `site_works` (the site between its gates), L19 to L22 `park`, L23
`school_garden` (past the park's tunnel); every stop in its zone: the station `station_front` (the foot of
the bridge), the surf school `sand_start`, the site office `site_works`, the allotment `by_the_railway`, the
shops `market`, the beach stops `sand`, the park stops `park`, Home Street's stops `residential`; C03 on the
sand, C04 in the site yard, C05 on the park's lawns.

The picture shows this at each node (80 to 200 px along its route from it) and along its leg:

| Level | Route | Where its node is, and what the map shows along its leg |
|---|---|---|
| L01 | street | just out of the house on Elm Street: the home's front garden (fence with a gate, flower beds, post box) and the first kerb with red tactile paving, to the bus stop's shelter |
| L02 | street | after the bus stop: four cars parked nose to tail on the kerb, painters' trestles with paint pots on the pavement, to granny's pink bungalow |
| L03 | street | after granny's: Hill Road, terraces with retaining walls and steps climbing the hill, a small stream under the road, garden apple trees, up to St Mary's (tower and spire) |
| L04 | street | after the church: Garden Lane, a garden wall with three gates, apple trees behind it, a parked car, to Sam's yellow house |
| L05 | street | round the corner on the East Street: Puddle Lane, four big puddles, parked cars and cones up to School Lane and the gate |
| L06 | market | on Market Street just round the corner from the West Street: the market square, a plaza with two rows of awning stalls, crowds, crates, to the bakery on the square |
| L07 | market | after the bakery: three zebra crossings in a row with traffic lights, a delivery van with a roller conveyor at the post office |
| L08 | market | after the post office: the corner shop (steps, awning, roll shutter, crates), to the flower shop |
| L09 | market | after the flower shop: fruit stalls with awnings, a toy shop with trampolines out front, a zebra crossing, to the library |
| L10 | market | after the library, on the Main Road (the East Street): rush hour at the junction, a queue of cars back along Market Street, a crossing, crowds |
| L11 | beach | on the West Street just past the market corner: down to Seaside Road (the beach shop on the corner with board racks, buckets and spades and beach balls, the sign to the beach, people heading down), along it and out on the boardwalk to the surf school's hut |
| L12 | beach | after the surf school: wet sand with several tidal channels, boats on trestles, to the lifeguard tower |
| L13 | beach | after the lifeguard tower: seagulls, a rescue-board stand, a breezy bay with rocks and flags, to the beach cafe's kiosk |
| L14 | beach | after the beach cafe: sandcastles, surf racks, the boardwalk crossing the promenade, the school |
| L15 | underpass | on the West Street just past the stem it shares with the site and park routes: up to Station Road and along it past the building site's covered walkways (boarded roofs over the south pavement, scaffolding), puddles, a ramp and a platform, crates, site barriers, to the station's ticket hall at the foot of the railway bridge (no railway crossing) |
| L16 | site | on Yard Road just past the stem: the site's west gate (a vehicle gate with its banksman), ramps and platforms, pipe racks, scaffolding, crates, builders, to the site office |
| L17 | site | after the site office's security gate (boom barrier and cabin): tower cranes swinging pallets over open trenches, the builder's lift, a digger, skips, out at the east gate |
| L18 | underpass | after the station: the cutting under the main line and the station's loop (two bridges), scaffolding, barriers, puddles, commuters walking through, a ramp and a platform, a boom barrier at the East Street |
| L19 | park | just inside the park gate: dogs, a net tunnel, a fallen tree, to the bandstand |
| L20 | park | after the bandstand: three fountains, trampolines, a play tower, to the park cafe |
| L21 | park | after the park cafe: a playground with rope swings over a stream, trampolines, a climbing frame, a net tunnel, to the boathouse |
| L22 | park | after the boathouse at the pond's west end: a duck pond with stepping stones, a rope ferry (a raft on a rope), a fountain, then past the lawn arena to grandpa's allotment by the railway |
| L23 | park | after the allotment: the short tunnel under the railway, the school garden (a fountain, a swing, seagulls), the crossing of the East Street, the school's steps |
| C01 | street | an open spot by the house: a small court with goals |
| C02 | market | shop windows: the shop parade with awnings |
| C03 | beach | slalom flags on the sand east of the school |
| C04 | site | targets on a slab in the building site's yard |
| C05 | park | a lawn arena with mown stripes and goals at the school end of the park |
