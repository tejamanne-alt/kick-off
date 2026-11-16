# Kamakura plant prompts

The pictures Kamakura's trees, bushes, flowers and potted plants are built from (the plants prompts page is made from this
file: `tools/prompts_page/gen_sheets.py`). A tree or bush is built by script (`tools/blender/kit_plants.py`): its trunk and
branches as solids, shaped from the plant's own views, dressed with leaf clusters cut out of a leaves picture and bark
from a bark picture. Every rule below comes from something that went wrong before (`docs/LEARNINGS.md`, quoted by number).

## How to use them

1. **Make KM1-1's first:** its plants are the first group. Then the routes in order.
2. **A plant's views:** a new chat in Gemini (Nano Banana Pro) or ChatGPT, one chat per plant. Paste BASE KM-S3 with
   KM-0 attached (the look target, `review/kamakura/refs/KM-0_look_target.png`). Then paste the plant's VIEWS prompt with
   the pictures it names attached. The tool makes the FRONT; then send "Next: RIGHT SIDE.", "Next: BACK." (only where
   the prompt asks for it) and "Next: TOP.", one at a time. Each card on the page lists these steps with the files to
   attach.
3. **Leaves and bark:** a separate chat. Paste BASE KM-S4 with KM-0 attached, then one LEAVES or BARK prompt per
   message with the pictures it names.
4. **Check each picture before the next** (the list below); redo one that fails rather than going on. A view that drifts
   from the others is redone, not built from (D25: views that disagree cost a rebuild).
5. **Save** each picture in the folder its card names, with exactly those file names (a phone upload adds `.PNG` or
   calls it `IMG_1234.png`: rename it). Tick "Made" as you go: the page remembers.

Keep each plant's views in one chat of one tool, so they match. The page's ChatGPT switch gives each prompt ChatGPT's
frame shapes (1:1, 2:3 and 3:2).

## Check each picture before saving it

- A photograph in KM-0's look: real bark and leaves, natural colour, sharp. Not a painting or an illustration (D10). The
  attached sheets KM-P2 and KM-P5 stayed illustrations through two restyles: they give the plant's shape only, never its
  look (D12).
- The same plant as the reference, the same individual in every view: its lean, its branches, the shape of its crown,
  its flowers and fruit (D25).
- The whole plant, from the ground (or the pot's foot) to its top leaf: nothing cropped.
- The background one even mid-grey everywhere: no ground line, no shadow on it, no glow or lighter patch round the
  crown or between the leaves (D18: pale parts near the backdrop were cut away).
- The crown open enough to show where the trunk forks and the main limbs run. A solid ball of leaves can't be built into
  branches.
- Nothing else in the picture: no scale post, wall, fence, pot or second plant touching it (D13: a canopy lost because
  its neighbours' leaves were taken for background).
- The TOP straight down: a round pot's rim a full circle, not an ellipse, and the trunk's foot under the crown, not
  below it (D31: three TOPs came as high three-quarter views).
- No mark from the image tool: Gemini puts a small ✦ in the bottom right corner of some pictures. On plain grey it is
  painted out with the grey; anywhere else the picture is made again (D31).
- In a leaves picture, every cluster and leaf apart, the grey showing between all of them; nothing touching the edge.
- In a bark picture, each strip flat (no round shading), its top continuing into its bottom, no single knot, scar or
  patch that would show when it repeats (D12, the plates' rule).

## The base prompts

### Views

```text
BASE KM-S3, the plant views base prompt. Attach KM-0. You are making the reference views a game's 3D artists build one
plant from: they model its trunk, branches and pot as solids and hang leaf clusters on the branches, so they need to see
its whole structure. Read all of this, then follow it for every image in this chat.

THE PLANT
It is the plant in the reference pictures I attach with it, the same one: copy its kind, its height and spread, the lean
of its trunk, where its main limbs fork, the shape and density of its crown, the colour of its leaves, flowers, fruit and
bark, and its pot or stone exactly as the references show them. Do not redesign, tidy up or improve it. Where no
reference shows a side, continue it as the real plant grows. A photograph of the real plant in the look of the picture
attached now (KM-0: real bark, real leaves, natural colour, sharp detail), not a painting, an illustration or a cartoon,
even when a reference is one.

THE VIEWS
One view per image, in this order, each when I ask for it: FRONT (the side that faces the street), RIGHT SIDE (from its
right as you face its FRONT, a quarter turn round), BACK (the side opposite FRONT: only when the plant's prompt asks for
it), TOP (looking straight down, FRONT at the bottom of the image). Every view:
- the same plant: the same lean, the same limbs, the same crown, the same flowers and fruit in the same places;
- the whole plant, from where it meets the ground (or the foot of its pot) to its topmost leaf, centred, nothing
  cropped, filling about 85 % of the image's height or width, whichever it reaches first;
- the same scale in FRONT, RIGHT SIDE and BACK: its height the same number of pixels in each;
- straight on and orthographic-looking: no perspective, the trunk upright where it is upright;
- the crown as open as the real plant in early summer: the trunk and its main limbs showing through the leaves where they
  fork, never a solid ball of leaves; its outline crisp, every cluster's edge sharp;
- the highest detail you can draw: every leaf, needle, petal, bark plate and crack sharp, nothing smeared or soft.

THE BACKGROUND AND LIGHT
- A plain, even mid-grey background (#808080), the same everywhere: no ground plane, no grass or soil around it, no
  shadow on the background, no glow or lighter patch around the crown or between the leaves.
- Flat, even, shadowless light, as on an overcast day in a studio: no cast shadows, no dark hollows added inside the
  crown, no sky reflections or dew sparkle. Colours exactly as the lit parts of the reference.

THE PLANT ALONE
- Nothing else in the picture: no scale post, wall, fence, trellis or pot that isn't the plant's own, no other plant, no
  people, animals or insects. A pot, planter, stone stand or trellis that is part of the plant stays whole, its rim
  and foot in view, and its soil shows from above.
- Add no labels, captions, arrows, numbers, logos or watermarks.

FORMAT: the aspect ratio the plant fills best, the same for FRONT, RIGHT SIDE and BACK: 9:16 for a plant taller than it is
wide (a tree, bamboo), 16:9 for one much wider than it is tall (a hedge, a bed of grass), 1:1 otherwise (a bush, a pot, a
stone); TOP 1:1. The largest size you can make.

Then wait for my first plant.
```

### Leaves and bark

```text
BASE KM-S4, the leaves and bark base prompt. Attach KM-0. You are making the pictures a game's 3D artists dress
script-built trees and bushes with: leaf clusters cut out and hung on the branches, and bark laid flat round the trunks.
Read all of this, then follow it for every image in this chat.

LEAVES (a LEAVES picture: one plant's foliage)
- Six clusters of that plant's foliage, each the end of one twig as it grows on the plant, about 30 to 40 cm across, each
  a little different: two seen from the front, two from a little below, two from the side. Below them, two single leaves
  laid flat (its upper side and its underside), and, where the prompt asks, its flowers and its fruit on their own.
- A grid with plain background between every piece: nothing touches or overlaps anything else or the image's edge; each
  twig's cut end inside the image.
- Every leaf, needle and petal sharp and whole, the pale undersides and the palest petals still clearly not background.
- The same plant as the reference I attach: its leaf shape, size and colour exactly, as in early summer unless the prompt
  says otherwise.

BARK (a BARK picture: three trees' bark side by side)
- Three vertical strips, each one tree's bark as the prompt lists them, left to right, each about 1 m wide by 2 m high
  of the real trunk at its real scale, a narrow band of plain background between them.
- Each strip is the trunk's surface laid flat: straight on, no roundness or shading across it, evenly lit edge to edge.
- Each strip tileable top to bottom: its top edge continues into its bottom edge with no seam.
- Evenly weathered all over: no single knot, scar, label, moss patch or hole that would stand out when it repeats.

FOR EVERY PICTURE
- A photograph of the real thing in the look of the picture attached now (KM-0: natural colour, sharp detail), not a
  painting or an illustration, even when a reference is one.
- A plain, even mid-grey background (#808080) wherever it shows: no shadow on it, no glow around anything.
- Flat, even, shadowless light, as in a studio on an overcast day; colours true.
- Nothing else: no labels, captions, numbers, logos or watermarks.

FORMAT: LEAVES 1:1; BARK 16:9. The largest size you can make.

Then wait for my first picture.
```

## KM1-1 first

The plants of KM1-1 Hase Lanes, the home's pots first: the pots stand in front of the home's fence, and their backs and
sides, hidden in KM1-1, are made from these. Attach the photographic KM1-1 (`refs/photo/KM1-1_hase_lanes.png`) and
KM-P6 (`refs/KM-P6_more_plants.png`) as each prompt says.

```text
VIEWS KM-G26, the bonsai pine in its terracotta bowl. Use BASE KM-S3. Attach KM-P6 and KM1-1. The first plant of KM-P6's bottom row: a
small black pine bonsai, its trunk curving left then up, its foliage in flat cloud-like pads, in a shallow brown
terracotta bowl with moss on the soil; it stands in front of the home's fence in KM1-1. Real size: 0.55 m tall, its bowl
0.45 m long. Make BACK as well. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G26_bonsai_pine_terracotta/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G27, the bonsai in its dark glazed bowl. Use BASE KM-S3. Attach KM-P6 and KM1-1. The second plant of KM-P6's bottom row: a
taller pine bonsai with a twisting trunk and spreading pads, in a dark blue glazed oval bowl. Real size: 0.7 m tall, its
bowl 0.5 m long. Make BACK as well. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G27_bonsai_pine_dark_glazed_bowl/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G28, the round shrub in its long planter. Use BASE KM-S3. Attach KM-P6 and KM1-1. The third plant of KM-P6's bottom row: a dense
clipped box shrub, round on top, in a long rectangular terracotta planter. Real size: 0.75 m tall, the planter 0.8 m
long. Make BACK as well. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G28_round_shrub_terracotta_planter/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G29, the pink flowers in a grey pot. Use BASE KM-S3. Attach KM-P6 and KM1-1. The fourth plant of KM-P6's bottom row: a mound of
small pink flowers and fresh green leaves in a round grey ceramic pot. Real size: 0.4 m tall. Make BACK as well. Same
rules as before.
```
Save: `review/kamakura/sheets/KM-G29_pink_flowers_grey_pot/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G30, the white flowers in a terracotta pot. Use BASE KM-S3. Attach KM-P6 and KM1-1. The fifth plant of KM-P6's bottom row: a
mound of small white daisy-like flowers in a terracotta pot. Real size: 0.4 m tall. Make BACK as well. Same rules as
before.
```
Save: `review/kamakura/sheets/KM-G30_white_flowers_terracotta_pot/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G31, the hydrangea in its white planter. Use BASE KM-S3. Attach KM-P6 and KM1-1. The sixth plant of KM-P6's bottom row: a young
hydrangea with pale green and white flower heads in a weathered white rectangular planter. Real size: 0.65 m tall, the
planter 0.6 m long. Make BACK as well. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G31_hydrangea_white_planter/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G32, the morning glories on their pot trellis. Use BASE KM-S3. Attach KM-P6, KM-P2 and KM1-1. The seventh plant of KM-P6's
bottom row: blue and violet morning glories climbing a small bamboo trellis set in a black plastic pot, the vines
twining round the canes, flowers open. Real size: 0.9 m tall. Make BACK as well. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G32_morning_glories_trellis/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G33, the plant on its stone stand. Use BASE KM-S3. Attach KM-P6 and KM1-1. The last plant of KM-P6's bottom row: a small pot of
pink flowers on a weathered mushroom-shaped stone stand with moss at its foot. Real size: 0.75 m tall. Make BACK as well.
Same rules as before.
```
Save: `review/kamakura/sheets/KM-G33_pink_flowers_stone_stand/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G08, the persimmon tree. Use BASE KM-S3. Attach KM-P2 and KM1-1. The tree at the right end of KM-P2's top row, the persimmon
that grows over the home's fence in KM1-1: a dark, deeply checkered trunk, a few spreading limbs, broad glossy green
leaves and orange fruit hanging among them. Real size: 5 m tall, its crown 4 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G08_persimmon_tree/` (`1_front.png`, `2_right_side.png`, `4_top.png`)

```text
VIEWS KM-G06, the blue hydrangea bush. Use BASE KM-S3. Attach KM-P2 and KM1-1. The hydrangea of KM-P2's top row: a rounded bush of big
blue mophead flower heads among broad serrated leaves, as the banks along Hase Station's fence in KM1-1. Real size: 1.2 m
tall, 1.5 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G06_blue_hydrangea/` (`1_front.png`, `2_right_side.png`, `4_top.png`)

```text
VIEWS KM-G19, the pink hydrangea bush. Use BASE KM-S3. Attach KM-P6 and KM1-1. The first plant of KM-P6's middle row: a rounded bush of
pale pink mophead flower heads among broad serrated leaves. Real size: 1.2 m tall, 1.4 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G19_pink_hydrangea/` (`1_front.png`, `2_right_side.png`, `4_top.png`)

```text
VIEWS KM-G20, the violet hydrangea bush. Use BASE KM-S3. Attach KM-P6 and KM1-1. The second plant of KM-P6's middle row: a rounded bush of
deep violet-blue mophead flower heads. Real size: 1.2 m tall, 1.4 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G20_violet_hydrangea/` (`1_front.png`, `2_right_side.png`, `4_top.png`)

```text
VIEWS KM-G01, the Japanese black pine. Use BASE KM-S3. Attach KM-P2 and KM1-1. The pine at the left of KM-P2's top row, as the pines
behind Hase Station in KM1-1: a trunk leaning and bending as a sea-wind pine does, reddish-grey plated bark, its foliage
in flat horizontal pads of long dark green needles on bare upward limbs. Real size: 9 m tall, its crown 6 m across. Same
rules as before.
```
Save: `review/kamakura/sheets/KM-G01_japanese_black_pine/` (`1_front.png`, `2_right_side.png`, `4_top.png`)

```text
VIEWS KM-G15, the clipped garden pine. Use BASE KM-S3. Attach KM-P6. The fourth tree of KM-P6's top row: a pine trained in a garden, its
trunk bending, its needles clipped into separate rounded pads on bare limbs, as it leans over a block wall in KM1-1's
lane. Real size: 3.5 m tall, 3 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G15_clipped_garden_pine/` (`1_front.png`, `2_right_side.png`, `4_top.png`)
Redo: the TOP only. The one in is a high three-quarter view, not straight down, so it can't give the crown's footprint.

```text
VIEWS KM-G21, the clipped hedge. Use BASE KM-S3. Attach KM-P6. The third plant of KM-P6's middle row: a dense, square-clipped hedge of
small-leaved evergreen, its top and sides flat, a few new shoots standing out. Real size: 1.2 m tall, 2.4 m long, 0.6 m
deep. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G21_clipped_hedge/` (`1_front.png`, `2_right_side.png`, `4_top.png`)

```text
VIEWS KM-G11, the mossy stone with ferns. Use BASE KM-S3. Attach KM-P2. The stone at the right end of KM-P2's bottom row: a rounded grey
stone thick with green moss on its top, small ferns growing at its foot. Real size: 0.9 m tall, 1.1 m across. Same rules
as before.
```
Save: `review/kamakura/sheets/KM-G11_mossy_stone_ferns/` (`1_front.png`, `2_right_side.png`, `4_top.png`)

## Route 1 and the shared ends

The rest of route 1 (KM1-3 Komachi-dori, KM1-4 The Shrine Bridge) and the plants every route uses.

```text
VIEWS KM-G02, the camphor tree. Use BASE KM-S3. Attach KM-P2 and KM1-4. The broad tree second in KM-P2's top row: a thick, furrowed grey-
brown trunk that splits low into heavy spreading limbs, a wide dome of small glossy light-green leaves. Real size: 12 m
tall, its crown 14 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G02_camphor_tree/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G12, the big old ginkgo. Use BASE KM-S3. Attach KM-P6 and KM1-4. The tree at the left of KM-P6's top row: a massive grey trunk,
upswept limbs, fan-shaped leaves in dense green clusters. Real size: 20 m tall, its crown 12 m across. Same rules as
before.
```
Save: `review/kamakura/sheets/KM-G12_big_old_ginkgo/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G04, the cherry tree in green leaf. Use BASE KM-S3. Attach KM-P2. The tree fourth in KM-P2's top row: a dark trunk with
horizontal bands of lenticels (the dark band round it as there), spreading limbs, a rounded crown of fresh green leaves.
Real size: 7 m tall, its crown 7 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G04_cherry_tree_green_leaf/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G13, the Japanese maple. Use BASE KM-S3. Attach KM-P6. The small tree second in KM-P6's top row: a slender smooth grey trunk
dividing low, layered limbs, small finely cut green leaves in airy tiers. Real size: 5 m tall, 5 m across. Same rules as
before.
```
Save: `review/kamakura/sheets/KM-G13_japanese_maple/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G22, the lotus. Use BASE KM-S3. Attach KM-P6 and KM1-4. The fourth plant of KM-P6's middle row: round blue-green lotus leaves on
tall stalks standing out of the water, two pink flowers and a bud above them, as on the pond under the arched bridge.
Real size: 1.2 m tall, a clump 1.5 m across, seen from the water's surface up. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G22_lotus/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G09, the potted bonsai pine. Use BASE KM-S3. Attach KM-P2. The bonsai in KM-P2's bottom row: a black pine bonsai with a curving
trunk and flat foliage pads in a shallow glazed bowl. Real size: 0.6 m tall. Make BACK as well. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G09_potted_bonsai_pine/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)
Redo: the TOP only. The one in is a high three-quarter view, not straight down, so it can't give the crown's footprint.

```text
VIEWS KM-G10, the morning glory on its trellis. Use BASE KM-S3. Attach KM-P2. The morning glory in KM-P2's bottom row: blue and violet
morning glories climbing a square bamboo trellis tied with twine, standing on the ground. Real size: 1.5 m tall, 0.8 m
wide. Make BACK as well. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G10_morning_glory_trellis/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G07, the azalea bush. Use BASE KM-S3. Attach KM-P2. The azalea in KM-P2's top row: a low rounded bush covered in pink-red flowers
over small dark leaves. Real size: 1 m tall, 1.3 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G07_azalea_bush/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

## Route 2: the Shonan coast

```text
VIEWS KM-G14, the zelkova park tree. Use BASE KM-S3. Attach KM-P6 and KM2-5. The tree third in KM-P6's top row: a straight grey trunk
dividing into many upswept limbs, a vase-shaped crown of small serrated green leaves. Real size: 15 m tall, its crown
10 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G14_zelkova/` (`1_front.png`, `2_right_side.png`, `4_top.png`)
Redo: all of it, in a new chat. The pictures in show a cherry in pink blossom, not a zelkova, each with the image
tool's watermark in a corner, and the RIGHT SIDE is missing.

```text
VIEWS KM-G23, the dune grass with a beach shrub. Use BASE KM-S3. Attach KM-P6 and KM2-1. The fifth plant of KM-P6's middle row: a clump
of tall pale-green dune grass and a low grey-green beach shrub growing out of sand, the sand at its foot part of it.
Real size: 0.8 m tall, 2 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G23_dune_grass/` (`1_front.png`, `2_right_side.png`, `4_top.png`)

## Route 3: the temple hills

```text
VIEWS KM-G03, the Japanese cedar. Use BASE KM-S3. Attach KM-P2 and KM3-2. The tall conifer in the middle of KM-P2's top row: a straight
red-brown trunk with long stringy bark, short branches all the way up, a narrow pointed crown of dark green sprays.
Real size: 25 m tall, its crown 6 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G03_japanese_cedar/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G18, the cedar's foot with its roots and ferns. Use BASE KM-S3. Attach KM-P6 and KM3-2. The last plant of KM-P6's top row: the
lowest 4 m of an old cedar's trunk, its buttress roots spreading over the ground, ferns growing among them. Real size:
4 m tall, its roots 3 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G18_cedar_roots_ferns/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G05, the bamboo clump. Use BASE KM-S3. Attach KM-P2 and KM3-3. The bamboo in KM-P2's top row: a dense clump of slender green
culms with their nodes, leaf sprays at their tops leaning out. Real size: 8 m tall, the clump 2 m across. Same rules as
before.
```
Save: `review/kamakura/sheets/KM-G05_bamboo_clump/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G17, the tall timber bamboo. Use BASE KM-S3. Attach KM-P6 and KM3-3. The bamboo sixth in KM-P6's top row: tall, thick green
timber bamboo culms with pale rings at their nodes, sprays of narrow leaves high up. Real size: 12 m tall, the stand 3 m
across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G17_timber_bamboo/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G16, the cherry in pink blossom. Use BASE KM-S3. Attach KM-P6. The tree fifth in KM-P6's top row: a dark banded trunk and limbs
covered in pale pink blossom, few leaves. Real size: 7 m tall, its crown 7 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G16_cherry_blossom/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G24, the clump of ferns. Use BASE KM-S3. Attach KM-P6. The sixth plant of KM-P6's middle row: a round clump of arching green fern
fronds. Real size: 0.8 m tall, 1.2 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G24_fern_clump/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

```text
VIEWS KM-G25, the boulder with moss and ivy. Use BASE KM-S3. Attach KM-P6. The last plant of KM-P6's middle row: a big grey boulder, moss
on its top, ivy trailing down its side, ferns at its foot. Real size: 1.4 m tall, 1.8 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-G25_moss_ivy_boulder/` (`1_front.png`, `2_right_side.png`, `3_back.png`, `4_top.png`)

## Leaves and bark

The leaves the trees and bushes are dressed with, and their bark. KM-F02 and KM-F04 (made earlier, on white, several
plants a picture) are in; the rest come one plant a picture, larger, as D24 asks of anything seen close. Where the tool
makes more than one version of a picture, keep each: `2_leaves.png`, `3_leaves.png` and so on (or `_bark`), more
clusters to choose from.

```text
FOLIAGE KM-F02, broad leaves (made, as it was asked for). Attach KM-P2. Paint isolated clumps of foliage exactly like
the attached plants, on a pure white background, flat shadowless light, no stems crossing each other, spread out in a
grid with space between them: eight clumps of the camphor tree's leaves, eight of the cherry's (in green leaf), six of
the persimmon's leaves with two orange fruits among them. Same colours, photographed like KM-0. FORMAT: aspect ratio 1:1,
the largest size you can make.
```
Save: `review/kamakura/sheets/KM-F02_broad_leaves/` (`1_sheet.png`)

```text
FOLIAGE KM-F04, flowers (made, as it was asked for). Attach KM-P2 and KM3-1. Paint isolated clumps of foliage exactly
like the attached plants, on a pure white background, flat shadowless light, no stems crossing each other, spread out in
a grid with space between them: eight blue and four pink-violet hydrangea flower heads with their leaves, six clumps of
the azalea in bloom, six morning-glory vines with flowers. Same colours, photographed like KM-0. FORMAT: aspect ratio
1:1, the largest size you can make.
```
Save: `review/kamakura/sheets/KM-F04_flowers/` (`1_sheet.png`)

```text
LEAVES KM-F01, the black pine's needles. Use BASE KM-S4. Attach KM-P2 and KM-P6. The needles of the Japanese black pine (KM-P2's top
left): stiff dark green needles in pairs, about 12 cm long, in dense tufts at the ends of the twigs, each with a pale
candle of new growth. Two single tufts below instead of single leaves. The same needles dress the clipped garden pine
and the bonsai pines. Same rules as before.
```
Save: `review/kamakura/sheets/KM-F01_black_pine_needles/` (`1_leaves.png`)

```text
LEAVES KM-F03, bamboo. Use BASE KM-S4. Attach KM-P2 and KM-P6. The leaves of the bamboo (KM-P2's clump, KM-P6's timber bamboo): sprays of
narrow pointed bright-green leaves fanning from thin side twigs. Instead of the single leaves, two straight 1.5 m lengths
of green culm with their nodes, upright, side by side. Same rules as before.
```
Save: `review/kamakura/sheets/KM-F03_bamboo/` (`1_leaves.png`)

```text
LEAVES KM-F06, the Japanese cedar's sprays. Use BASE KM-S4. Attach KM-P2. The foliage of the Japanese cedar (KM-P2's tall conifer): dense
sprays of short, stiff, awl-shaped dark green needles spiralling round the shoots, drooping a little at the tips. Same
rules as before.
```
Save: `review/kamakura/sheets/KM-F06_japanese_cedar/` (`1_leaves.png`)

```text
LEAVES KM-F07, the ginkgo's leaves. Use BASE KM-S4. Attach KM-P6. The fan-shaped leaves of the ginkgo (KM-P6's top left), bright green,
in clusters on short spur shoots. Same rules as before.
```
Save: `review/kamakura/sheets/KM-F07_ginkgo/` (`1_leaves.png`)

```text
LEAVES KM-F08, the Japanese maple's leaves. Use BASE KM-S4. Attach KM-P6. The small, deeply cut, seven-lobed green leaves of the Japanese
maple (KM-P6's top row), on slender red-tinged twigs. Same rules as before.
```
Save: `review/kamakura/sheets/KM-F08_japanese_maple/` (`1_leaves.png`)

```text
LEAVES KM-F09, the zelkova's leaves. Use BASE KM-S4. Attach KM-P6. The small, sharply serrated, pointed green leaves of the zelkova
(KM-P6's top row), alternate along fine twigs. Same rules as before.
```
Save: `review/kamakura/sheets/KM-F09_zelkova/` (`1_leaves.png`)

```text
LEAVES KM-F10, cherry blossom. Use BASE KM-S4. Attach KM-P6. Twigs of the cherry in full pale pink blossom (KM-P6's top row), five-petalled
flowers in clusters, a few new leaves among them. Instead of the single leaves, two single flower clusters. Same rules as
before.
```
Save: `review/kamakura/sheets/KM-F10_cherry_blossom/` (`1_leaves.png`)

```text
LEAVES KM-F11, ferns, moss and ivy. Use BASE KM-S4. Attach KM-P6. Six arching fern fronds (KM-P6's clump of ferns), then, instead of the
single leaves, two flat cushions of green moss and two trailing strands of ivy with their leaves. Same rules as before.
```
Save: `review/kamakura/sheets/KM-F11_ferns_moss_ivy/` (`1_leaves.png`)

```text
LEAVES KM-F12, lotus and dune grass. Use BASE KM-S4. Attach KM-P6. Four lotus leaves on their stalks and two pink lotus flowers (KM-P6's
lotus), then two tufts of the pale dune grass and two sprigs of the grey-green beach shrub. Same rules as before.
```
Save: `review/kamakura/sheets/KM-F12_lotus_dune_grass/` (`1_leaves.png`)

```text
BARK KM-F05, the bark of the pine, the camphor and the cedar. Use BASE KM-S4. Attach KM-P2. Left to right: the Japanese black pine's
(reddish-grey, in thick irregular plates with dark fissures), the camphor's (grey-brown, finely furrowed in long ridges),
the Japanese cedar's (red-brown, in long stringy vertical strips). Same rules as before.
```
Save: `review/kamakura/sheets/KM-F05_pine_camphor_cedar_bark/` (`1_bark.png`)

```text
BARK KM-F13, the bark of the cherry, the persimmon and the ginkgo. Use BASE KM-S4. Attach KM-P2 and KM-P6. Left to right: the cherry's
(dark purple-grey, smooth, with horizontal bands of lenticels), the persimmon's (dark grey, cracked into small square
blocks), the ginkgo's (grey-brown, rough and deeply furrowed). Same rules as before.
```
Save: `review/kamakura/sheets/KM-F13_cherry_persimmon_ginkgo_bark/` (`1_bark.png`)

```text
BARK KM-F14, the bark of the maple and the zelkova, and a bamboo culm. Use BASE KM-S4. Attach KM-P6. Left to right: the Japanese maple's
(smooth grey-green with faint pale streaks), the zelkova's (smooth grey, flaking in small patches to orange-brown), and a
green bamboo culm's surface laid flat (glossy green, one node band across it). Same rules as before.
```
Save: `review/kamakura/sheets/KM-F14_maple_zelkova_bamboo_bark/` (`1_bark.png`)
