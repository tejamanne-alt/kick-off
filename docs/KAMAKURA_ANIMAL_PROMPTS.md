# Kamakura animal prompts

The pictures Kamakura's animals are built from (the animals prompts page is made from this file:
`tools/prompts_page/gen_sheets.py`). Every animal that moves is one skin on bones (`tools/blender/kit_animals_km.py`):
its body, legs, tail, head, wings and fins are cut from its pictures at the joints the pictures show, and moved by the
game's own behaviours (`docs/ASSET_REVIEW.md`). So each animal gets its own views, each a separate full-size picture, in
a pose that shows every part whole. Every rule below comes from something that went wrong before (`docs/LEARNINGS.md`,
D14 to D22, quoted by number).

## How to use them

1. **Make KM1-1's first:** its animals are the first group. Then the rest, group by group.
2. **One chat per base, in Gemini (Nano Banana Pro) or ChatGPT.** Paste the base prompt with KM-0 attached (the look
   target, `review/kamakura/refs/KM-0_look_target.png`), then one animal per message, with the sheet its prompt names
   attached (`refs/KM-P4_animals_sheet.png`, `refs/KM-P8_more_animals.png`).
3. **The tool makes the first view; then ask for each next one** ("Next: LEFT SIDE.", and so on, in the order its base
   lists them), one at a time.
4. **Check each picture before the next** (the list below), and redo one that fails rather than going on.
5. **Save** each picture in the folder its card names, with exactly those file names (rename a phone upload). Tick
   "Made" as you go: the page remembers.

Keep each animal's views in one chat of one tool, so they match. The page's ChatGPT switch gives each prompt ChatGPT's
frame shapes (1:1, 2:3 and 3:2).

## Check each picture before saving it

- A photograph of the real animal in KM-0's look: real fur, feathers or scales, natural colour, sharp. Not a painting or
  an illustration.
- The same individual as the attached sheet, and the same in every view: its markings, colours and proportions (D14:
  one tail, counted from above).
- Every leg there, whole, and apart: four for a four-legged animal, two for a bird, each from where it leaves the body
  to its toes, none hidden behind another, none raised or crossed. The far legs show in the LEFT SIDE as they are, not
  as copies of the near ones (D20: birds built on four legs; D22: the Shiba's far hind leg).
- The joints where the real animal's are and plain to see: a front leg's elbow just under the belly and its wrist low
  down, a hind leg's knee and its hock about two fifths up, a bird's heel (D22).
- The tail, the wings and the fins whole and clear of the body, each fin in one piece (D20: fins cut in two).
- The backdrop the one even colour its prompt names, the same everywhere: no shadow, glow or lighter patch round the
  animal, between its legs, under its belly or between tail and back (D18: a squirrel's grey fur, a kite's wing and a
  heron's pale legs were cut away against a backdrop too near their colour).
- Whiskers faint (D18: the backdrop between a cat's whiskers was taken in as fur).
- An insect's head to the right in every view from above (D18: insects drawn head-up were built with their wings along
  the body).
- Nothing else in the picture: no branch, perch, wire, rock, leaf or water, unless the prompt asks for it.

## The base prompts

### Standing still (animals and birds that walk)

The game makes them walk, trot, hop and peck with their legs cut at the joints (D19 to D22). One photo mid-stride decided
too much: legs overlapping, the far ones hidden, joints guessed. So each is pictured standing square, every leg whole.

```text
BASE KM-S2, the standing model sheet. Attach KM-0. You are making the reference views a game's 3D artists build one
animal or bird from and make walk: they cut each leg from the body at its joints, so every leg must show whole. Read all
of this, then follow it for every animal in this chat.

THE ANIMAL
Each animal is the one on the sheet I attach with it, the same individual: its markings, colours and proportions
exactly as there. A photograph of the real animal in the look of the picture attached now (KM-0: real fur or feathers,
natural colour, sharp detail), not a painting or an illustration.

THE POSE
Standing still and relaxed on level ground, its weight on all its feet, head level and looking ahead, mouth or beak
closed, its tail held as it naturally is, clear of its body. Every leg straight down under the body and whole, from where
it leaves the body to the toes, nothing raised, nothing crossed:
- a four-legged animal: four legs, the near front leg a little ahead of the far front leg and the near hind leg a little
  behind the far hind leg, so from the side all four show whole, side by side, none hidden behind another; each joint
  (the elbow just under the belly, the wrist low down, the knee, the hock about two fifths up) where it is on the real
  animal and plain to see;
- a bird: exactly two legs, straight under it and a little apart so both show whole from the side, the heel joint clear,
  the toes spread flat on the ground line, none curled under the body.

THE VIEWS
One view per image, in this order, each when I ask for it, the same animal at the same scale and in the same pose in
every one, nothing cropped, in the highest detail you can draw (every hair, feather and claw sharp):
  - RIGHT SIDE: a strict profile, head to the right;
  - LEFT SIDE: a strict profile, head to the left: its other flank and its far legs as they really are;
  - FROM ABOVE: looking straight down on its back, head at the top;
  - FRONT: head-on;
  - BACK: from straight behind.
- Orthographic-looking views: no perspective, the body straight, the animal filling about 85 % of the image.
- The backdrop: one plain, even colour, the one its prompt names, the same everywhere: no shadow on it, no ground line,
  no grass, no perch, no other animal, and no glow or lighter patch around the animal, between its legs, under its belly
  or between its tail and its back.
- Our artists cut each leg from the body, so every leg's whole outline shows, clear of the body, the other legs and the
  tail; the gaps between the legs are plain backdrop; fur and feather edges crisp, never blurred into the backdrop;
  whiskers faint.
- Even, soft, shadowless light; colours true.
- No labels, numbers, arrows, logos or watermarks.

FORMAT: RIGHT SIDE and LEFT SIDE 16:9 for a long animal (a cat, a dog, a tanuki, a squirrel with its tail), 1:1 for a
bird; FROM ABOVE the same as the sides; FRONT and BACK 1:1. The largest size you can make.

Then wait for my first animal. Make its RIGHT SIDE first; I will ask for each next view.
```

### In flight (birds the game shows flying)

A bird in flight is seen from the side, from below and, as it banks, from above: built from one view, the black kite had
no body, back or tail shape (D15). Its wings beat in two halves, the inner and the outer (D20, D21).

```text
BASE KM-S1, the bird-in-flight model sheet. Attach KM-0. You are making the reference views a game's 3D artists build one
bird in flight from: they cut each wing into an inner and an outer half that beat, and its tail into a fan that tilts.
Read all of this, then follow it for every bird in this chat.

THE BIRD
Each bird is the one on the sheet I attach with it, the same individual: its markings, colours and proportions exactly as
there. A photograph of the real bird in the look of the picture attached now (KM-0: real feathers, natural colour, sharp
detail), not a painting or an illustration.

THE VIEWS
One view per image, in this order, each when I ask for it, the same bird at the same scale in every one, nothing cropped,
in the highest detail you can draw:
  - SIDE: a strict profile, head to the right, both wings raised straight up above its back (the top of the wingbeat),
    so the whole body, head, beak, tail and tucked feet show clear below them;
  - FROM ABOVE: looking straight down on its back, wings fully spread and level, tail fanned, head at the top;
  - FROM BELOW: looking straight up at its underside, the same spread wings and tail, head at the top;
  - FRONT: head-on, wings fully spread and level, so their thickness and angle show.
- Orthographic-looking views: no perspective, the wings symmetrical, the body straight, the spread wings filling about
  90 % of the image's width.
- The backdrop: one plain, even colour, the one its prompt names, the same everywhere: no shadow, sky, ground or other
  bird, no glow or lighter patch around the bird or between its feathers.
- Each wing's whole outline clear of the body and of the other wing, the bend of the wrist plain to see, the primaries'
  tips sharp, each feather edge crisp; the tail fanned clear of the body; the feet tucked but drawn clearly, never
  hair-thin.
- Even, soft, shadowless light; colours true.
- No labels, numbers, arrows, logos or watermarks.

FORMAT: SIDE 1:1; FROM ABOVE, FROM BELOW and FRONT 16:9 (the spread wings across). The largest size you can make.

Then wait for my first bird. Make its SIDE first; I will ask for each next view.
```

### In the water (fish and water animals)

Koi swim just under the water, the tail swept in links and the pectoral fins sculling; the turtle paddles with four
flippers (D20: fins cut in two; D17: one-sided fins).

```text
BASE KM-S5, the water animals model sheet. Attach KM-0. You are making the reference views a game's 3D artists build one
fish or water animal from: they cut its tail and fins, or its flippers and legs, from the body so they can swim, so each
must show whole. Read all of this, then follow it for every animal in this chat.

THE ANIMAL
Each animal is the one on the sheet I attach with it, the same individual: its markings, colours and proportions exactly
as there. A photograph of the real animal in the look of the picture attached now (KM-0: real scales, shell and skin,
natural colour, sharp detail), not a painting or an illustration. Out of the water, dry: no water, ripples, reflections,
droplets or wet sheen.

THE POSE
Straight and level, as if swimming slowly forward: the body straight from head to tail, the tail fin spread wide, every
fin spread open and clear of the body, each in one piece; a turtle's four flippers stretched out from its shell, apart,
its head and tail out; a crab's eight legs spread apart round its shell and its two claws forward, none crossing; a
starfish's five arms flat and spread.

THE VIEWS
One view per image, in this order, each when I ask for it, the same animal at the same scale and in the same pose in
every one, nothing cropped, in the highest detail you can draw:
  - FROM ABOVE: looking straight down on its back, head to the right;
  - RIGHT SIDE: a strict profile, head to the right;
  - FRONT: head-on.
- Orthographic-looking views: no perspective, the animal filling about 85 % of the image.
- The backdrop: one plain, even colour, the one its prompt names, the same everywhere: no shadow, no water, no rock, no
  glow or lighter patch around the animal or between its fins or legs.
- Every fin, flipper, leg and claw with its whole outline clear of the body and of each other, the backdrop plain between
  them; the thin edges of fins crisp, never blurred into the backdrop.
- Even, soft, shadowless light; colours true.
- No labels, numbers, arrows, logos or watermarks.

FORMAT: FROM ABOVE and RIGHT SIDE 16:9 for a long animal (a koi), 1:1 otherwise (a turtle, a crab, a starfish); FRONT
1:1. The largest size you can make.

Then wait for my first animal. Make it FROM ABOVE first; I will ask for each next view.
```

### Small animals and insects

The swallowtail and the red dragonfly flit; the tree frog and the snail sit on leaves. An insect drawn head-up was built
with its wings along its body, so its flap twisted it (D18).

```text
BASE KM-S6, the small animals and insects model sheet. Attach KM-0. You are making the reference views a game's 3D
artists build one small animal or insect from: they cut an insect's wings from its body so they can beat, and a frog's
legs so it can hop. Read all of this, then follow it for every animal in this chat.

THE ANIMAL
Each animal is the one on the sheet I attach with it, the same individual: its markings, colours and proportions exactly
as there. A photograph of the real animal in the look of the picture attached now (KM-0: natural colour, sharp detail,
as a macro photograph), not a painting or an illustration. Alone: no leaf, stem, stone or water under it.

THE POSE
- A butterfly or a dragonfly: its wings fully spread flat and level, the fore and hind wings apart on each side so each
  wing's whole outline shows, its body straight, its legs tucked, its antennae drawn clearly.
- A frog: sitting upright, its four legs folded under it and apart, each foot flat with its toes spread.
- A snail: crawling, its body stretched out ahead of its shell, its tentacles up.

THE VIEWS
One view per image, in this order, each when I ask for it, the same animal at the same scale and in the same pose in
every one, nothing cropped, in the highest detail you can draw:
  - FROM ABOVE: looking straight down, head to the right;
  - RIGHT SIDE: a strict profile, head to the right;
  - FRONT: head-on.
- Orthographic-looking views: no perspective, the animal filling about 85 % of the image.
- The backdrop: one plain, even colour, the one its prompt names, the same everywhere: no shadow, no glow or lighter
  patch around the animal, between its wings or legs.
- Every wing, leg, antenna and tentacle with its whole outline clear of the body and of each other, never hair-thin; the
  veins of a wing sharp, its see-through parts showing the backdrop.
- Even, soft, shadowless light; colours true.
- No labels, numbers, arrows, logos or watermarks.

FORMAT: FROM ABOVE 16:9 for a spread-winged insect, 1:1 otherwise; RIGHT SIDE and FRONT 1:1. The largest size you can
make.

Then wait for my first animal. Make it FROM ABOVE first; I will ask for each next view.
```

## KM1-1 first

The animals of KM1-1 Hase Lanes: the ginger cat on the block wall (the hazard), sparrows on the pavement, swallows on the
wires and darting low over the lane, a crow on the recycling bins.

```text
ASSET KM-N01, the ginger cat, standing. Use BASE KM-S2. Attach KM-P4. The ginger tabby at the left of KM-P4's top row,
the same cat in all three of its poses there: orange with darker stripes, white paws behind, the ringed tail. Backdrop:
plain mid-grey #808080. Real size: 25 cm at the shoulder, 46 cm long without the tail. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N01_ginger_cat_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

```text
ASSET KM-N08, the tree sparrow, standing. Use BASE KM-S2. Attach KM-P4. The sparrow of KM-P4's fourth row: chestnut cap,
a black spot on its white cheek, a black bib, a streaked brown back, pale legs. Backdrop: plain mid-grey #808080. Real
size: 14 cm long. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N08_tree_sparrow_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

```text
ASSET KM-N08, the tree sparrow in flight. Use BASE KM-S1. Attach KM-P4. The sparrow of KM-P4's fourth row, as it flies
there (the last of the row): its brown wings with two pale bars, its short square tail. Backdrop: plain mid-grey #808080.
Real size: 14 cm long, wings 21 cm across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N08_tree_sparrow_flight/` (`1_side.png`, `2_above.png`, `3_below.png`, `4_front.png`)

```text
ASSET KM-N09, the barn swallow, perched. Use BASE KM-S2. Attach KM-P4. The swallow at the left of KM-P4's bottom row,
standing on a level line instead of its wire: glossy blue-black back, a red face and throat, a cream breast, its long
forked tail streamers held straight out behind, clear of each other. Backdrop: plain pale sand #D8CCB0. Real size: 18 cm
long with its streamers. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N09_barn_swallow_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

```text
ASSET KM-N09, the barn swallow in flight. Use BASE KM-S1. Attach KM-P4. The swallow of KM-P4's bottom row, as it flies
there: long, narrow, swept-back wings, the deeply forked tail with its streamers spread apart. Backdrop: plain pale sand
#D8CCB0. Real size: 18 cm long, wings 33 cm across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N09_barn_swallow_flight/` (`1_side.png`, `2_above.png`, `3_below.png`, `4_front.png`)

```text
ASSET KM-N06, the large-billed crow, standing. Use BASE KM-S2. Attach KM-P4. The crow of KM-P4's third row: glossy black
all over with a blue-purple sheen, the heavy arched bill, a steep forehead. Backdrop: plain mid-grey #808080. Real size:
57 cm long. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N06_large_billed_crow_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

```text
ASSET KM-N06, the large-billed crow in flight. Use BASE KM-S1. Attach KM-P4. The crow of KM-P4's third row, as it flies
there: broad black wings with fingered tips, a rounded tail. Backdrop: plain mid-grey #808080. Real size: 57 cm long,
wings 1 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N06_large_billed_crow_flight/` (`1_side.png`, `2_above.png`, `3_below.png`, `4_front.png`)

## Animals that walk

```text
ASSET KM-N04, the Shiba Inu. Use BASE KM-S2. Attach KM-P4. The Shiba of KM-P4's second row: red with cream cheeks, chest,
belly and the insides of its legs, a red collar, its tail curled over its back. Backdrop: plain mid-grey #808080. Real
size: 39 cm at the shoulder. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N04_shiba_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

```text
ASSET KM-N21, the calico cat. Use BASE KM-S2. Attach KM-P8. The calico of KM-P8's fourth row: white with ginger and
black patches exactly as there. Backdrop: plain mid-grey #808080. Real size: 24 cm at the shoulder. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N21_calico_cat_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

```text
ASSET KM-N22, the black-and-white cat. Use BASE KM-S2. Attach KM-P8. The black-and-white cat of KM-P8's fourth row, its
markings exactly as there. Backdrop: plain pale sand #D8CCB0. Real size: 25 cm at the shoulder. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N22_black_white_cat_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

```text
ASSET KM-N02, the tanuki. Use BASE KM-S2. Attach KM-P4. The tanuki of KM-P4's top row: grizzled grey-brown fur, the dark
mask round its eyes, dark legs, a bushy dark-tipped tail. Backdrop: plain pale sky-blue #A9C7E3 (its fur is too near
grey). Real size: 30 cm at the shoulder, 55 cm long without the tail. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N02_tanuki_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

```text
ASSET KM-N03, the Pallas's squirrel. Use BASE KM-S2. Attach KM-P4. The squirrel of KM-P4's second row: a grey-brown back,
a rufous belly, its long bushy tail held out level behind it, not over its back, the backdrop showing between tail and
back. Backdrop: plain pale sky-blue #A9C7E3 (its fur is too near grey). Real size: 20 cm long without the tail. Same rules
as before.
```
Save: `review/kamakura/sheets/KM-N03_squirrel_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

## Birds on the ground

```text
ASSET KM-N07, the shrine pigeon. Use BASE KM-S2. Attach KM-P4. The pigeon of KM-P4's fourth row: blue-grey, two black
wing bars, a green and purple sheen on its neck, pink legs. Backdrop: plain pale sand #D8CCB0 (its feathers are too near
grey). Real size: 32 cm long. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N07_shrine_pigeon_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

```text
ASSET KM-N20, the oriental turtle dove. Use BASE KM-S2. Attach KM-P8. The turtle dove of KM-P8's third row: a scaly
rufous and black back, a pinkish-grey breast, the black-and-white striped patch on its neck. Backdrop: plain pale sky-blue
#A9C7E3. Real size: 33 cm long. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N20_turtle_dove_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

```text
ASSET KM-N17, the white wagtail. Use BASE KM-S2. Attach KM-P8. The wagtail of KM-P8's second row: black, white and grey,
a black bib and crown, its long tail held level. Backdrop: plain pale sand #D8CCB0. Real size: 18 cm long. Same rules as
before.
```
Save: `review/kamakura/sheets/KM-N17_white_wagtail_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

```text
ASSET KM-N19, the brown-eared bulbul. Use BASE KM-S2. Attach KM-P8. The bulbul of KM-P8's third row, standing on a level
line instead of its branch: grey, streaked pale on its head, a chestnut patch behind its eye, a long tail. Backdrop: plain
pale sand #D8CCB0 (its feathers are too near grey). Real size: 28 cm long. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N19_bulbul_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

```text
ASSET KM-N18, the Japanese white-eye. Use BASE KM-S2. Attach KM-P8. The white-eye of KM-P8's third row, standing on a
level line instead of its branch: olive-green back, a yellow throat, the white ring round its eye. Backdrop: plain
mid-grey #808080. Real size: 12 cm long. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N18_white_eye_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

```text
ASSET KM-N05, the black kite, perched. Use BASE KM-S2. Attach KM-P4. The kite at the left of KM-P4's third row, standing
on a level line instead of its branch: dark brown, paler streaks on its head, yellow feet, its long notched tail.
Backdrop: plain pale sky-blue #A9C7E3 (its wings came out holed against grey, D18). Real size: 60 cm long. Same rules as
before.
```
Save: `review/kamakura/sheets/KM-N05_black_kite_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

```text
ASSET KM-N10, the black-tailed gull. Use BASE KM-S2. Attach KM-P4. The gull of KM-P4's bottom row: a white head and body,
a dark grey back, black wing tips with white spots, yellow legs, a yellow bill with a red and black tip. Backdrop: plain
pale sand #D8CCB0. Real size: 46 cm long. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N10_black_tailed_gull_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

```text
ASSET KM-N11, the little egret. Use BASE KM-S2. Attach KM-P4. The egret of KM-P4's bottom row: all white, its fine head
plumes, black legs with yellow feet. Backdrop: plain mid-grey #808080. Real size: 60 cm long. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N11_little_egret_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

```text
ASSET KM-N15, the grey heron. Use BASE KM-S2. Attach KM-P8. The heron of KM-P8's second row, standing tall, its neck in a
gentle S: grey back, white neck and face, a black stripe over its eye and a black plume, a yellow bill, pale legs.
Backdrop: plain pale sand #D8CCB0 (its pale legs were cut away against grey, D18). Real size: 95 cm long. Same rules as
before.
```
Save: `review/kamakura/sheets/KM-N15_grey_heron_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

```text
ASSET KM-N16, the cormorant, drying its wings. Use BASE KM-S2. Attach KM-P8. The cormorant of KM-P8's second row, as it
stands there on its rock but on a level line instead: upright, its wings held open and spread to dry, each wing's
whole outline clear of its body, glossy black-brown with a yellow face patch. Backdrop: plain pale sand #D8CCB0. Real
size: 84 cm long, wings 1.3 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N16_cormorant_stand/` (`1_right.png`, `2_left.png`, `3_above.png`, `4_front.png`, `5_back.png`)

## Birds in flight

The large birds the game shows flying close, then the small ones.

```text
ASSET KM-N05, the black kite in flight. Use BASE KM-S1. Attach KM-P4. The black kite of KM-P4's third row, as it flies
there: dark brown, a pale patch under each wing near its tip, a shallow notched tail, yellow feet tucked. Backdrop: plain
pale sky-blue #A9C7E3. Real size: 60 cm long, wings 1.6 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N05_black_kite_flight/` (`1_side.png`, `2_above.png`, `3_below.png`, `4_front.png`)

```text
ASSET KM-N10, the black-tailed gull in flight. Use BASE KM-S1. Attach KM-P4. The gull of KM-P4's bottom row, as it flies
there: a white head and body, dark grey back and wings with black tips, a black band across its white tail, a yellow
bill with a red and black tip. Backdrop: plain pale sand #D8CCB0. Real size: 46 cm long, wings 1.2 m across. Same rules
as before.
```
Save: `review/kamakura/sheets/KM-N10_black_tailed_gull_flight/` (`1_side.png`, `2_above.png`, `3_below.png`, `4_front.png`)

```text
ASSET KM-N07, the shrine pigeon in flight. Use BASE KM-S1. Attach KM-P4. The pigeon of KM-P4's fourth row, as it flies
there: blue-grey, two black wing bars, the green and purple sheen on its neck. Backdrop: plain pale sand #D8CCB0. Real
size: 32 cm long, wings 65 cm across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N07_shrine_pigeon_flight/` (`1_side.png`, `2_above.png`, `3_below.png`, `4_front.png`)

```text
ASSET KM-N15, the grey heron in flight. Use BASE KM-S1. Attach KM-P8. The heron of KM-P8's second row, flying as herons
do: its neck folded back in an S, its legs trailing straight behind its tail, broad grey wings with darker flight
feathers. Backdrop: plain pale sand #D8CCB0. Real size: 95 cm long, wings 1.7 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N15_grey_heron_flight/` (`1_side.png`, `2_above.png`, `3_below.png`, `4_front.png`)

```text
ASSET KM-N11, the little egret in flight. Use BASE KM-S1. Attach KM-P4. The egret of KM-P4's bottom row, as it flies
there: all white, its neck folded back, its black legs trailing with their yellow feet. Backdrop: plain mid-grey #808080.
Real size: 60 cm long, wings 95 cm across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N11_little_egret_flight/` (`1_side.png`, `2_above.png`, `3_below.png`, `4_front.png`)

```text
ASSET KM-N16, the cormorant in flight. Use BASE KM-S1. Attach KM-P8. The cormorant of KM-P8's second row, flying with its
neck stretched forward: glossy black-brown, a yellow face patch, a long tail. Backdrop: plain pale sand #D8CCB0. Real
size: 84 cm long, wings 1.3 m across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N16_cormorant_flight/` (`1_side.png`, `2_above.png`, `3_below.png`, `4_front.png`)

```text
ASSET KM-N18, the Japanese white-eye in flight. Use BASE KM-S1. Attach KM-P8. The white-eye of KM-P8's third row, as it
flies there: olive-green wings and back, the white ring round its eye. Backdrop: plain mid-grey #808080. Real size:
12 cm long, wings 18 cm across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N18_white_eye_flight/` (`1_side.png`, `2_above.png`, `3_below.png`, `4_front.png`)

```text
ASSET KM-N19, the brown-eared bulbul in flight. Use BASE KM-S1. Attach KM-P8. The bulbul of KM-P8's third row, as it flies
there: grey, its long tail spread. Backdrop: plain pale sand #D8CCB0. Real size: 28 cm long, wings 40 cm across. Same
rules as before.
```
Save: `review/kamakura/sheets/KM-N19_bulbul_flight/` (`1_side.png`, `2_above.png`, `3_below.png`, `4_front.png`)

```text
ASSET KM-N20, the oriental turtle dove in flight. Use BASE KM-S1. Attach KM-P8. The turtle dove of KM-P8's third row, as
it flies there: rufous and black scaled wings, a dark tail with a white band at its end. Backdrop: plain pale sky-blue
#A9C7E3. Real size: 33 cm long, wings 55 cm across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N20_turtle_dove_flight/` (`1_side.png`, `2_above.png`, `3_below.png`, `4_front.png`)

## In the water

```text
ASSET KM-N12, the red-and-white koi. Use BASE KM-S5. Attach KM-P8. The koi at the left of KM-P8's top row: white with
the red patches exactly where they are there, its fins white. Backdrop: plain mid-grey #808080. Real size: 60 cm long.
Same rules as before.
```
Save: `review/kamakura/sheets/KM-N12_koi_red_white/` (`1_above.png`, `2_right.png`, `3_front.png`)

```text
ASSET KM-N13, the golden koi. Use BASE KM-S5. Attach KM-P8. The golden koi of KM-P8's top row: metallic gold all over,
its fins a paler gold. Backdrop: plain pale sky-blue #A9C7E3. Real size: 60 cm long. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N13_koi_golden/` (`1_above.png`, `2_right.png`, `3_front.png`)

```text
ASSET KM-N14, the pond turtle. Use BASE KM-S5. Attach KM-P8. The turtle at the right of KM-P8's top row: a brown ridged
shell, dark scaly skin, its four flippers out. Backdrop: plain pale sky-blue #A9C7E3. Real size: its shell 25 cm long.
Same rules as before.
```
Save: `review/kamakura/sheets/KM-N14_pond_turtle/` (`1_above.png`, `2_right.png`, `3_front.png`)

```text
ASSET KM-N27, the shore crab. Use BASE KM-S5. Attach KM-P8. The crab of KM-P8's bottom row, out of its rock pool: a dark
olive-green shell, eight legs spread apart round it, its two claws forward. Backdrop: plain pale sand #D8CCB0. Real size:
its shell 4 cm across, its legs 12 cm across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N27_shore_crab/` (`1_above.png`, `2_right.png`, `3_front.png`)

```text
ASSET KM-N28, the starfish. Use BASE KM-S5. Attach KM-P8. The starfish at the right of KM-P8's bottom row, out of its
rock pool: orange-tan, five arms flat and spread, its knobbly upper side. Backdrop: plain pale sky-blue #A9C7E3. Real
size: 15 cm across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N28_starfish/` (`1_above.png`, `2_right.png`, `3_front.png`)

## Small animals and insects

```text
ASSET KM-N25, the Asian swallowtail. Use BASE KM-S6. Attach KM-P8. The butterfly of KM-P8's bottom row: pale yellow wings
with black veins and bands, the blue and red spots near its tails, the tails on its hind wings. Backdrop: plain mid-grey
#808080. Real size: wings 10 cm across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N25_swallowtail/` (`1_above.png`, `2_right.png`, `3_front.png`)

```text
ASSET KM-N26, the red dragonfly. Use BASE KM-S6. Attach KM-P8. The dragonfly of KM-P8's bottom row: a bright red body,
four clear wings with fine dark veins and dark spots near their tips, the hind wings broader than the fore. Backdrop:
plain mid-grey #808080. Real size: wings 7 cm across. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N26_red_dragonfly/` (`1_above.png`, `2_right.png`, `3_front.png`)

```text
ASSET KM-N23, the tree frog. Use BASE KM-S6. Attach KM-P8. The frog at the left of KM-P8's bottom row, off its leaf: a
bright green tree frog with a dark stripe through its eye and pale toe pads. Backdrop: plain pale sand #D8CCB0. Real
size: 4 cm long. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N23_tree_frog/` (`1_above.png`, `2_right.png`, `3_front.png`)

```text
ASSET KM-N24, the land snail. Use BASE KM-S6. Attach KM-P8. The snail of KM-P8's bottom row, off its leaf: a brown
banded spiral shell, a pale grey-brown body stretched out ahead of it. Backdrop: plain pale sky-blue #A9C7E3. Real size:
its shell 3 cm across, 5 cm long crawling. Same rules as before.
```
Save: `review/kamakura/sheets/KM-N24_land_snail/` (`1_above.png`, `2_right.png`, `3_front.png`)
