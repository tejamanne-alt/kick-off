# Building Kamakura: the assets, then the levels, in order

How Kamakura's new routes (`docs/CITIES.md`) get from the user's 17 reference images (`review/kamakura/refs`) and its map
into the game. Every prompt is here in the order it is used, and on the prompts page at the end of the Kamakura tab
(`tools/prompts_page`).

## What "identical" means here

The target is assets that look like the reference images: the same shapes and proportions, every part, the same colours,
materials and wear, in the look of KM-0, the look target (a photograph, not a painting). The way there is **projection modelling in Blender**, proven on the home and the red
vending machine (`review/kamakura/kit_proof_board.jpg`, `tools/blender/kit_buildings_km.py`):
- **The fronts are your pictures,** in their photographic versions (see "First: your pictures in KM-0's look"). Each model is built by script to the measurements of the picture it comes from (the
  home, from the photographic KM1-1: 120 px to the metre, the pavement at y 893), and the picture's own pixels are projected onto every face that faces
  the street. Straight on, the model is the picture, pixel for pixel; turned, it is a real 3D shape: the fence in front,
  the house set back, the roofs sloping away.
- **Sides, backs and roofs out of view** take the city's photographic plates (KM-P3: boards, tiles, mortar, block,
  stone), in the picture's colours, at real size (160 px to the metre), assembled piece by piece so nothing repeats in a
  grid: walls board by board (each a random board of the plate, started at a random height, some upside down), roofs
  tile by tile from the plate's clean tiles (nests and debris left out). Or a side the props sheet shows, straightened
  when it is drawn at an angle (the vending machine's side, from KM-P1). On trial: the street-facing roofs in KM-P3's
  tiles too, the picture's ridge cap and gutters kept as strips (the board's last rows).
- **Things standing in front of a building are their own models:** plants, pots, bicycles, signs that stand off the wall.
  Painted on, they smear when the camera turns. They are cut out of the picture (OpenCV's GrabCut, per group, with
  hints) and stand in front as cut-outs on half an elliptic cylinder: straight on exactly the picture, turned round; the
  wall or fence behind gets them painted out (its boards carried down). The home's pots, hydrangeas and bonsai are
  done this way (`KmHomeGarden`, eight groups).
- **The home is built from the photographic KM1-1** (`refs/photo`), which has the house whole: its upper storey solid,
  its entrance under the gable (the sliding lattice doors, the light, the walls with the nameplate, the step) with the
  fence open in front of it (the restyle added it from `review/kamakura/refs/parts/KM-x2_entrance.png`), the pots either
  side. The persimmon and the bicycle are gone from it: a level places them as their own models (KM-G08, KM-A08).
- **No real brands:** a logo that reads as a real one is repainted with an invented name in the city's script
  (うみかぜ), in its own colours (`rebrand_machines`: both vending machines in the photographic KM1-1).
- **The pictures' glitches are not copied:** a clean picture replaces one with a glitch, or else the glitch is repaired,
  noted in the script at the pixels it touches. Things that only pass in front (power lines across a roof) are taken
  off (`dewire`); a picture's sky is painted out of the roofs' outlines (`unsky`, `pale=True` for a photograph's pale
  sky).
- **The pictures' light comes with them.** The photographs carry KM-0's sun and shade, so the Kamakura kit is drawn as
  the clouds are: `Toon` with `_Lighting` 0.25, the pictures' light kept as it is and a quarter of the game's sun added.
  The city's climate, the haze and every filter still apply. It is not lit twice.
- **The highest resolution where it shows:** the fronts at the pictures' full resolution (the home's front is 1,340 px
  across), in the Kamakura atlas (4096 x 4096), within the phone's budgets (`docs/ART_DIRECTION.md`: a building 6,000
  triangles, a street prop 1,500, a tree 6,000, a gameplay structure 5,000; `docs/PERFORMANCE.md`). The proof's home is
  57 triangles, its fence 20, its pots and plants 128, and the vending machine 10: the detail is in the picture, not
  the mesh.
- Every asset is checked against its source: rendered straight on and turned, beside the picture, and in all four looks,
  and redone until it matches (an acceptance board: `docs/LEARNINGS.md` rule 4, A8).

## The pipeline: who does what

| Step | Who | Tool | Output |
|---|---|---|---|
| 1. The pictures, in KM-0's look | the user | Gemini: the painted ones made again as photographs (RESTYLE, below) | `review/kamakura/refs/photo` (the originals stay in `refs`) |
| 2. The models | Claude | Blender 5.2.3 (`bpy`), by script, with the pictures projected (`tools/blender/kit_buildings_km.py`) | real size, within budget, in the Kamakura atlas, FBX in `Assets/_Game/Art/Models/Kamakura` |
| 3. Extra views, only when asked | the user | Gemini, Nano Banana Pro: a model sheet (Step 0) | only for an asset whose side or back is seen in play and that no picture shows; Claude asks for it by its id |
| 4. Organic shapes, only when asked | the user in meshy.ai | Meshy Multi-Image to 3D, from a model sheet's four views | only what boxes and slopes can't build: so far the bronze statue (KM-B32) |
| 5. The levels | Claude | the level builder (`Editor/`) | Kamakura's routes, leg by leg, in route order |

- **Where each look comes from, after the restyles:** every level picture is a photograph now (`refs/photo`). The props
  and plants sheets KM-P1, KM-P2 and KM-P5 stayed illustrations through two passes, so they give shapes and the sides a
  picture doesn't show: a prop's front is projected from the photographic level picture it stands in, a prop in no level
  picture gets a single-object sheet (KM-S0) when its look matters, and plants take their leaves from KM-P6 and the
  foliage sheets. KM-P3, P4, P6, P7 and P8 are photographs as made.
- **The sheets and plates come in pairs:** KM-P1 and KM-P5 (props and vehicles), KM-P2 and KM-P6 (plants and trees, the
  home's pots among them), KM-P3 and KM-P7 (texture plates), KM-P4 and KM-P8 (animals and birds). The second of each
  pair (in the Kamakura tab, right after the first) adds what the level pictures show and the first one doesn't, in
  KM-0's look.
- **Plants are built by script** as leaf-card trees (`tools/blender/kit_plants.py`), shaped from KM-P2's silhouettes and
  painted from the foliage sheets below and the pictures' own leaves.
- **Ground and walls** use tileable textures made from the plates (KM-P3) and the level pictures.
- **Animals and birds** are built from KM-P4 and KM-P8, the sheets of Kamakura's animals and birds (in the Kamakura tab,
  with the other sheets), like the props: each one's side view projected onto its sides, its front and from-below views
  onto the rest. The animals kit's cat, dog, pigeon, gull and squirrel take Kamakura's coats from it; the black kite, the
  crow, the tanuki, the sparrow, the swallow and the egret are new models in it.
- **The far layers** (hills, the back rows of roofs, the sea) are cards cut from the level pictures, so they match
  them exactly.

**Why not Meshy for everything:** image-to-3D rebuilds the shape and repaints the texture from a few views, so it comes
back close but not identical (softened edges, repainted signs, light baked in), at about 12,000 triangles a building
that then have to be cut to budget; and the sheets it needs are themselves redrawings of the pictures. Projection keeps
your pictures' own pixels, costs no credits, and is fully repeatable.

**Meshy, for the exceptions, two ways.** Meshy runs on the user's meshy.ai account (the cloud sessions can't reach
meshy.ai's website, and there is no Meshy connector):
- **The user in meshy.ai** (the default). Claude cuts the asset's sheet into its four views
  (`tools/blender/crop_sheet_views.py` into `review/kamakura/sheets/views/`: `<id>_1_front.png`, `_2_right`, `_3_back`,
  `_4_three_quarter`) and pushes them. In meshy.ai, Image to 3D with several images: upload the four, the newest Meshy
  model, topology triangle, target polycount 12,000 (cut to budget after), texture on at the highest quality the plan
  offers, PBR off, symmetry auto; generate, download the GLB, save it as `review/kamakura/models/<id>_<name>.glb`, push.
- **Claude through Meshy's API** (optional): the user creates an API key in their Meshy account (if their plan includes
  the API) and enters it in the secure credential form Claude shows (never in the chat). Claude then runs the same
  settings and says how many credits it will take before generating.

Claude cleans the GLB, sets its real size and projects the picture onto it like any other model. **Meshy's terms:** on a
free plan its models are CC BY 4.0 (Meshy must be credited); on a paid plan they are private, with full commercial use.
For the stores, generate on a paid plan or credit Meshy in the game's credits.

## The order

0. **Your pictures in KM-0's look** (BASE KM-R0, then RESTYLE): the painted ones made again as photographs, KM1-1 first
   as the test.
1. **Textures** (KM-T): the plates made tileable, and the grounds of the levels.
2. **Street props** (KM-A01 to A18): everything on the props sheet, used in every route.
3. **Vehicles** (KM-V): the tram, the kei truck, the scooter, the bicycle, the rickshaw.
4. **Plants** (KM-F): the foliage and bark sheets.
5. **Buildings and set pieces** (KM-B), in route order, the shared ends first: the home, the school, then route 1, 2, 3.
6. **The kit** (BUILD KM-K): Blender, all of the above into the Kamakura kit.
7. **The levels** (BUILD KM-L): the city's plumbing, then each route's legs in order, each mini-game system just before
   the first leg that needs it, then the map screen, then the switch from the old 23 levels.

## The sheets' assets, by id

The eight sheets and plates in `review/kamakura/refs` (KM-P1 to KM-P8) give the levels more than their pictures show.
Each asset has an id the level prompts below use. What a level's picture shows is built from the picture (projected);
a sheet gives the same object's other sides and every extra copy. The props are built like the vending machine, the
plants by `kit_plants.py`, the plates assembled piece by piece like KM-P3, the animals in the animals kit.

**Props and vehicles** (KM-P1: KM-A01 to A18, KM-V01 to V04; KM-P5, new):

| Id | Asset (KM-P5) | Real size |
|---|---|---|
| KM-A19 | the blue drink vending machine | 1.83 m tall |
| KM-A20 | the can and bottle recycling bins, a row of three | 1.0 m tall |
| KM-A21 | the green public phone box | 2.3 m tall |
| KM-A22 | an air-conditioner outdoor unit on its stand (the home's) | 0.9 m tall |
| KM-A23 | the gas and electricity meters on their wall board | 0.8 m wide |
| KM-A24 | a house letterbox | 0.45 m tall |
| KM-A25 | a grey roadside control cabinet | 1.6 m tall |
| KM-A26 | a concrete street-lamp pole with its curved arm | 7 m tall |
| KM-A27 | a bicycle rack with parked bicycles | 2.4 m long |
| KM-A28 | Hase Station's ticket gate with its IC card reader | 1.0 m tall |
| KM-A29 | a station name board on two posts | 1.8 m wide |
| KM-A30 | the yellow "beware of black kites" sign | 2.2 m tall |
| KM-A31 | nobori banner flags in a weighted stand | 2.4 m tall |
| KM-A32 | an A-frame chalkboard menu and a wooden stool | 1.0 m tall |
| KM-A33 | the souvenir rack of chopsticks and fans | 1.4 m tall |
| KM-A34 | stacked red and green plastic crates | 0.9 m tall |
| KM-A35 | stacked polystyrene fish boxes and a hose reel | 0.8 m tall |
| KM-A36 | a surfboard rack with a wetsuit on a hanger | 2.0 m tall |
| KM-A37 | crab traps and a heap of fishing nets with floats | 1.2 m long |
| KM-A38 | the rice ball in its wrapper (the Kite Thief's) | 10 cm across |
| KM-V01 | the tram: KM-P5 adds its front | 12 m long |
| KM-V05 | a small white compact car (its number plate blanked) | 3.9 m long |
| KM-B20 | the fishing boat on its rollers: KM-P5 adds its 3D shape | 5 m long |

**Plants** (KM-P2 and KM-P6), built as leaf-card plants (`kit_plants.py`), dressed with the sheets' own leaves:

| Id | Plant | Sheet |
|---|---|---|
| KM-G01 to G11 | black pine, camphor, Japanese cedar, cherry in green leaf, bamboo clump, blue hydrangea, azalea, persimmon, potted bonsai, morning glory on a trellis, mossy stone with ferns | KM-P2 |
| KM-G12 | a big old ginkgo | KM-P6 |
| KM-G13 | a Japanese maple | KM-P6 |
| KM-G14 | a zelkova park tree | KM-P6 |
| KM-G15 | a clipped garden pine | KM-P6 |
| KM-G16 | a cherry in pink blossom | KM-P6 |
| KM-G17 | tall timber bamboo | KM-P6 |
| KM-G18 | a Japanese cedar's foot with its roots and ferns | KM-P6 |
| KM-G19, G20 | hydrangea bushes, pink and violet | KM-P6 |
| KM-G21 | a clipped hedge | KM-P6 |
| KM-G22 | lotus leaves and flowers | KM-P6 |
| KM-G23 | dune grass with a beach shrub | KM-P6 |
| KM-G24 | a clump of ferns | KM-P6 |
| KM-G25 | a boulder with moss and ivy | KM-P6 |
| KM-G26 to G33 | the home's pots: the bonsai pine, the bonsai in a dark bowl, the round shrub planter, the pink flowers, the white flowers, the hydrangea planter, the morning glories, the plant on its stone stand (their backs and sides, behind the cut-outs) | KM-P6 |

**Plates** (KM-P3: KM-T01 to T06; KM-P7, new): KM-T16 rusty corrugated iron, KM-T17 silver-grey timber boards, KM-T18
vermilion torii timber over its black base, KM-T19 a mossy random-stone wall, KM-T20 streaked white concrete, KM-T21
ceramic siding.

**Animals** (KM-P4 and KM-P8), each moved by one of the game's ambient behaviours (`World/`), or a hazard (`Hazards/`):

| Id | Animal | Sheet | Behaviour |
|---|---|---|---|
| KM-N01 | the ginger cat | KM-P4 | WallCat |
| KM-N02 | the tanuki | KM-P4 | TreeSquirrel's dash, into the undergrowth instead of up a tree |
| KM-N03 | a Pallas's squirrel | KM-P4 | TreeSquirrel |
| KM-N04 | a Shiba Inu (red collar) | KM-P4 | Dog (the hazard: noses a low ball back; chip it over) |
| KM-N05 | the black kite | KM-P4 | perched (CritterIdle), circling (SkyFlock), the snack dive (Seagull) |
| KM-N06 | a large-billed crow | KM-P4 | GroundBird |
| KM-N07 | a shrine pigeon | KM-P4 | GroundBird; SkyFlock over the town |
| KM-N08 | a tree sparrow | KM-P4 | GroundBird, in twos and threes |
| KM-N09 | a barn swallow | KM-P4 | perched on the wires (CritterIdle); SkyFlock, low and fast |
| KM-N10 | a black-tailed gull | KM-P4 | GroundBird on the sand; SkyFlock over the sea |
| KM-N11 | a little egret | KM-P4 | GroundBird, wading at the water's edge |
| KM-N12, N13 | koi, red-and-white and golden | KM-P8 | PondDuck, just under the water |
| KM-N14 | a pond turtle | KM-P8 | basking on a stone (CritterIdle); slides in when the kid comes close |
| KM-N15 | a grey heron | KM-P8 | GroundBird, slow; standing at the pond's edge |
| KM-N16 | a cormorant | KM-P8 | on a rock, wings held open to dry (CritterIdle) |
| KM-N17 | a white wagtail | KM-P8 | GroundBird, tail wagging |
| KM-N18 | a Japanese white-eye | KM-P8 | in a tree's crown (CritterIdle), darting between trees |
| KM-N19 | a brown-eared bulbul | KM-P8 | GroundBird; perched in the trees |
| KM-N20 | an oriental turtle dove | KM-P8 | GroundBird |
| KM-N21 | a calico cat | KM-P8 | WallCat; asleep on a step (CritterIdle) |
| KM-N22 | a black-and-white cat | KM-P8 | WallCat, stretched out on a wall top |
| KM-N23 | a tree frog | KM-P8 | on a leaf (CritterIdle: its throat; a hop when the ball lands near) |
| KM-N24 | a land snail | KM-P8 | on a wet leaf or step (CritterIdle, creeping) |
| KM-N25 | an Asian swallowtail | KM-P8 | FlitButterfly |
| KM-N26 | a red dragonfly | KM-P8 | FlitButterfly, straighter and faster, hanging still in the air |
| KM-N27 | a shore crab | KM-P8 | ShoreCrab |
| KM-N28 | a starfish | KM-P8 | in a tide pool (still) |

**Rules for the levels:** the dressing never stands on the play lane (only hazards do); ambient animals score nothing
and stop nothing; no more than 12 animals awake on screen at once (AmbientAgent rests the rest); every addition keeps the
level's side-by-side with its picture true: it goes where the picture has room for it (behind a fence, in a pond, on a
wire, in the sky, at the lane's edges), never over something the picture shows.

## The map plan

Kamakura's map screen, traced from the route design (`docs/CITIES.md`), not from a generated plan: the user's map
pictures showed the town well, but both of Gemini's plans broke the design (the second sent route 1 up route 2's avenue,
put Kamakura Station at the torii, drew route 2 twice and gave level 1-4 no node; both put the circles at the legs' ends,
where the game puts a level's node near its start). `tools/city_map/kamakura.py` holds the plan, checks it and writes:
- `review/kamakura/map/KM-MAP3_plan_game.png`: the plan drawn on the clean map at the game's sizes (nodes 150 px, stop
  markers, the tram dashed);
- `review/kamakura/map/KamakuraMapLayout.json`: the layout in TownMapLayout's format (home, school, three routes, twelve
  nodes, nine stops, districts, street names, the tram ride), in the game's 3200 x 1800 picture;
- `review/kamakura/map/checks.txt`: every check below, with the measurements.

**The routes, on the map's own roads:**
- **Home** is the two-storey house on the lane west of the tram line's end; all three routes leave its gate together
  to the corner (9.1 %, 7.4 % and 5.8 % of their lengths: the user's 5 to 15 %).
- **KM1 The Enoden (red):** along the lane by the tracks to **Hase Station** (KM1-1), the tram along the line to
  **Kamakura Station** (KM1-2, dashed), up the red-paved Komachi-dori to the **shrine's side gate** (KM1-3), then
  straight on up the street along the shrine's east side to the zebra crossing at the top, and right to the school gate
  (KM1-4; the user: "after 1-3 go straight and right to school, instead of shrine route").
- **KM2 The Shonan Coast (blue):** down the lane, across the coast road and through the tunnel to **the boardwalk**
  (KM2-1), along the sand past the boats to **Grandma's shop** (KM2-2), from the shop to the **lifeguard tower** (KM2-3,
  the errand), along the beach to the rocks and back to the avenue's foot, under **the great torii** (KM2-4), up
  Wakamiya-oji between the cherries and lanterns to the central steps (KM2-5). It crosses the tram line once, at right
  angles, at the great torii: the one crossing.
- **KM3 The Temple Hills (yellow):** up the lane to the hydrangea steps and the temple at their top, the **trail sign**
  (KM3-1), the ridge walkway past the cave tomb to **Genjiyama park** (KM3-2), through the bamboo to the bell tower,
  down its steps and along to the torii (KM3-3).
- **The school approach:** routes 2 and 3 meet under the upper vermilion torii and share the road east to the school
  gate; route 1 joins it at the zebra crossing (5.6 %, 11.2 % and 13.5 % of their lengths: the user's 5 to 15 %). KM1-4's
  node sits 100 px past its stop (not the usual 120) to keep clear of the school's pin.

**The frame:** the clean map sits in the game's 3200 x 1800 picture at 0.83 game px per map px (x 458 to 2742, y 209
to 1484), so every node and both places fall in the core's inner area. The ring round it is MAP KM-MAP3 (the map zoomed
out, in the Kamakura map group of `docs/IMAGE_PROMPTS.md`); Claude puts the clean map back over its middle pixel for
pixel (aligned by phase correlation, the seam blended), so the layout stays true.

**The checks** (the map screen's, `Tests/Editor/TownMapTests.cs`, with Kamakura's two rules): every route from home to
school and 1200 px or longer; the shared ends 5 to 15 % at home and at most 15 % at the school (instead of the
original's 320 px); 90 px apart in the middles but for the one crossing (176 px long); every node in the core's inner
area, within 12 px of its route, in playing order, 190 px or more from every other (closest 219, 2-3 and 2-4); a
route's first node 150 px into its own stretch; every later node 120 px past the stop it starts from; every stop on its
route between its levels' nodes, 96 px or more from every node. All pass.

**Two notes for the levels:** the map's tram line has no level crossing at home (KM1-1's picture has one: the level
keeps it); the map's great torii at the avenue's foot is vermilion, KM2-4's is grey wood (the level follows its
picture).

## The prompts

### First: your pictures in KM-0's look

KM-0 is the bar for every asset and background (a photograph: real materials, a deep cobalt sky with cumulus, sea haze).
Twelve level pictures, the props and plants sheets and the second props sheet (KM-P5) came out painted instead, so each is made again as a photograph
of the same place, with its layout kept, since the models are measured from it. A new Gemini chat with Nano Banana 2.1
(it keeps the 4:1 shape; Pro stops at 21:9): paste KM-R0 with KM-0 attached, then one RESTYLE per message, attaching that
picture. KM1-1 (the home's picture) first, as the test: push it and Claude rebuilds the home from it; then the rest. Save
each as review/kamakura/refs/photo/ with the same file name (PNG). If a picture drifts from KM-0's look, attach KM-0 again
with it; if objects move, say "Same layout as the attached picture, object for object", or try again. A picture that
comes back still an illustration takes the second pass: BASE KM-R1 in a new chat, then its RESTYLE prompt again,
attaching its first-pass result from refs/photo; save it over that result.

```text
BASE KM-R0, the photographic restyle. Attach KM-0. You are turning a game's painted street pictures into photographs for
its 3D artists. Read all of this, then follow it for every picture in this chat.

THE GOAL
I will attach one painted picture at a time. Make the same picture again as a photograph of the same place, in the look
of the picture attached now (KM-0, Kamakura in its light). Our artists measure each picture and project it onto their 3D
models, so nothing may move.

KEEP EXACTLY
- The frame: the same shape, the same framing and horizon, the same straight-on side view.
- Every building, wall, fence, pole, wire, sign, vehicle, plant and object: in the same place, at the same size, with the
  same outline, the same number of storeys, windows, doors, posts and panels. Add nothing, remove nothing, move nothing.
- The colours of things: the same paint, timber, tiles, signs and flowers.
- Signs keep their Japanese text.
- The picture's weather and time of day.

ALSO FIX (the only changes to the layout)
- Anything see-through, ghosted, faded or half-drawn becomes solid and whole, continuing what is around it.
- Power lines crossing in front of a building's front or roof are removed. The poles, and the lines above the roofs, stay.
- A logo that resembles a real brand (a vending machine's drink panel above all) becomes an invented Japanese name in the
  same place, at the same size, in the same colours.
- Garbled text becomes a short, legible invented name in the same place and size.

CHANGE TO KM-0'S LOOK
- A real photograph, not a painting or an illustration: no outlines, no brush strokes, no flat or cel shading, no anime
  look.
- Real materials at full detail: the grain of weathered timber, glazed kawara tiles with their sheen and dirt, mortar with
  salt bloom, rust, moss, chipped paint, worn asphalt and stone.
- KM-0's light for a clear morning: the sun 40 degrees up behind the camera to the left, near-white direct sun, clean cool
  blue-grey shade, deep contact shadows, a deep cobalt sky with big cumulus, a soft sea haze turning far hills blue. A
  picture in another light keeps it, photographed (a drizzle stays soft and shadowless); a sheet keeps its studio light.
- Natural, rich colour as in KM-0, with no colour filter or tint over the whole picture.
- No people: where a person would be, leave it empty. No animals except those in the picture. Add no text, labels, logos
  or watermarks.
- Sharp from front to back: no depth of field, vignette, lens flare or film grain.

Then wait for my first picture.
```

```text
RESTYLE KM1-1, Hase Lanes. Attach KM1-1 (and the entrance part, below). Make it a photograph in KM-0's look, by the rules above: every object exactly
where it is, at its size and with its outline; only the look changes. Keep: the kid's home with its fence, the persimmon,
the pots and the bicycle; the ginger cat on the block wall; the convex mirror, the two vending machines, the little shrine
and its vermilion torii; the level crossing; Hase Station's platform and the hydrangeas. Make the right third of the
home's upper storey, its air conditioner, and the right half of the entrance gable solid: continue them as their left
halves show them. Give the vending machine's red panel an invented Japanese name. One change to the layout: open the
home's fence under the entrance gable, a gap about 2.8 m wide (x 873 to 1208), showing the entrance in the second
picture I attach (review/kamakura/refs/parts/KM-x2_entrance.png: the sliding lattice doors, the light, the walls either
side with the nameplate, the step) at the same size; the pots and flowers closed up to the left of the gap, the bonsai
to its right, the bicycle and the last morning glory gone.
FORMAT: exactly the attached picture's shape, 4:1.
```

```text
RESTYLE KM1-2, Ride the Enoden. Attach KM1-2. Make it a photograph in KM-0's look, by the rules above: every object exactly
where it is, at its size and with its outline; only the look changes. Keep: the tram car's green bench, the straps and poles, the
route map and its invented station names, the door, the warm sun patches on the floor, and the houses and gardens outside
the windows, photographed too, a little brighter than the car.
FORMAT: exactly the attached picture's shape, 4:1.
```

```text
RESTYLE KM1-3, Komachi-dori. Attach KM1-3. Make it a photograph in KM-0's look, by the rules above: every object exactly
where it is, at its size and with its outline; only the look changes. Keep: the red gateway sign and the taxi sign; every shop with its
noren, its signboard (the same Japanese text), lanterns and goods; the rickshaw; the "beware of kites" sign with its bird;
the side gate at the right.
FORMAT: exactly the attached picture's shape, 4:1.
```

```text
RESTYLE KM1-4, The Shrine Bridge. Attach KM1-4. Make it a photograph in KM-0's look, by the rules above: every object exactly
where it is, at its size and with its outline; only the look changes. Keep: the arched stone bridge over the lotus pond, the basin
under its little roof, the stone lanterns, the fortune racks, the steps up to the vermilion hall; then the school with its
clock, the sports ground, the green fence, the gate with its notice board, the cherry tree.
FORMAT: exactly the attached picture's shape, 4:1.
```

```text
RESTYLE KM2-1, Down to Yuigahama. Attach KM2-1. Make it a photograph in KM-0's look, by the rules above: every object exactly
where it is, at its size and with its outline; only the look changes. Keep: the houses, the surfboards by the doors, the tunnel under the
road with its sign, the surf shop, the boardwalk with sand drifting over it, the beach and the sea at the right.
FORMAT: exactly the attached picture's shape, 4:1.
```

```text
RESTYLE KM2-2, Yuigahama Morning. Attach KM2-2. Make it a photograph in KM-0's look, by the rules above: every object exactly
where it is, at its size and with its outline; only the look changes. Keep: the beach and the sea, the boats on their rollers with their nets,
the lifeguard tower, the litter sacks, the surfboards, the kite in the sky, the pines and the beach houses, the road at the
right. The sand is Yuigahama's: dark grey-brown, paler where dry.
FORMAT: exactly the attached picture's shape, 4:1.
```

```text
RESTYLE KM2-3, Grandma's Whitebait Shop. Attach KM2-3. Make it a photograph in KM-0's look, by the rules above: every object exactly
where it is, at its size and with its outline; only the look changes. Keep: the shop and its sign (the same text), the drying racks
with the whitebait, the counter with the bento on its cloth, the boxes, the hose reel, the scooter; the sea wall and the
beach at the right.
FORMAT: exactly the attached picture's shape, 4:1.
```

```text
RESTYLE KM2-4, The Kite Thief. Attach KM2-4. Make it a photograph in KM-0's look, by the rules above: every object exactly
where it is, at its size and with its outline; only the look changes. Keep: the rock shelves with their tide pools and seaweed, the worn steps, the
waves, the rice ball on its rock, the kite on its pine branch, the grey wooden torii and the stone lanterns of the avenue
at the right.
FORMAT: exactly the attached picture's shape, 4:1.
```

```text
RESTYLE KM2-5, Wakamiya-oji. Attach KM2-5. Make it a photograph in KM-0's look, by the rules above: every object exactly
where it is, at its size and with its outline; only the look changes. Keep: the shops with their signs (the same text), the crossing, the raised
path with its lanterns, the great vermilion torii, the school's gate and its cherry tree.
FORMAT: exactly the attached picture's shape, 4:1.
```

```text
RESTYLE KM3-1, Hydrangea Steps. Attach KM3-1. Make it a photograph in KM-0's look, by the rules above: every object exactly
where it is, at its size and with its outline; only the look changes. This one keeps its own light: a June drizzle, overcast, soft and
shadowless, everything wet and glistening, mist in the trees (not KM-0's sun). Keep: the back gate, the stone steps, the
hydrangeas, the lantern, the rest hut and its umbrellas, the trail sign.
FORMAT: exactly the attached picture's shape, 4:1.
```

```text
RESTYLE KM3-2, The Hiking Trail. Attach KM3-2. Make it a photograph in KM-0's look, by the rules above: every object exactly
where it is, at its size and with its outline; only the look changes. This one keeps its own light: KM3-1's drizzle and mist. Keep: the trail
and its roots, the signpost, the footbridge, the cave tomb with its pagoda, the tanuki, the rail fence.
FORMAT: exactly the attached picture's shape, 4:1.
```

```text
RESTYLE KM3-3, Genjiyama Down to School. Attach KM3-3. Make it a photograph in KM-0's look, by the rules above: every object exactly
where it is, at its size and with its outline; only the look changes. This one keeps its own light: KM3-1's drizzle, lifting at the
right into brighter cloud. Keep: the bronze statue on its plinth, the benches, the bell tower and its bell, the bamboo, the
steps, the school's back gate and the school.
FORMAT: exactly the attached picture's shape, 4:1.
```

```text
RESTYLE KM-P1, the props sheet. Attach KM-P1. Make it a photograph in KM-0's look, by the rules above: every object exactly
where it is, at its size and with its outline; only the look changes. Each object a photograph of the real thing, on the same plain mid-grey
background, in the same place and at the same size, in even soft studio light with a small soft shadow under each. Keep
the signs' Japanese text.
FORMAT: exactly the attached picture's shape, 16:9.
```

```text
RESTYLE KM-P2, the plants sheet. Attach KM-P2. Make it a photograph in KM-0's look, by the rules above: every object exactly
where it is, at its size and with its outline; only the look changes. Each plant a photograph of the real plant, on the same plain mid-grey
background, in the same place and at the same size, with its grey scale poles, in even soft studio light.
FORMAT: exactly the attached picture's shape, 4:1.
```

```text
RESTYLE KM-P5, the second props sheet. Attach KM-P5. Make it a photograph in KM-0's look, by the rules above: every
object exactly where it is, at its size and with its outline; only the look changes. Each object a photograph of the
real thing, on the same plain mid-grey background, in even soft studio light with a small soft shadow under each. Keep
the signs' Japanese text where it is legible; garbled text becomes a short invented name. The small car: no badge on
its grille and no readable number plate (a plain white plate). The tram keeps its green-and-cream colours.
FORMAT: exactly the attached picture's shape, 16:9.
```

```text
BASE KM-R1, the second pass. Attach KM-0 and review/kamakura/refs/photo/KM2-3_grandmas_whitebait_shop.png. Some of my
pictures came back from the first pass still as illustrations: outlines, flat colours, painted texture. That is the one
thing that must change, and it must change completely. The second picture attached is one that came out right: the
same layout as its painted original, but a real photograph in the look of KM-0. Make every picture I send now like it.
For each: keep every object where it is, at its size, with its outline, exactly as before (all the KEEP EXACTLY and ALSO
FIX rules of KM-R0 still hold), and replace every surface with real photographed material: real timber grain, real
stone, real leaves, real metal and paint, real light and shadow, real depth. No outlines, no ink lines, no cel shading,
no painted brush texture anywhere, not even at the edges of objects. A sheet keeps its plain grey background and its
studio light, its objects photographed like product photos. Then wait for my first picture.
```

### Step 0: the model sheet base prompt (only when Claude asks for a sheet)

Claude builds every asset from the pictures first. A sheet is needed only when an asset's side or back is seen in play
and no picture shows it, or for a Meshy exception (the statue); Claude then names the asset's id. Paste this first in a
new Gemini chat (Nano Banana Pro), then send that asset's ASSET prompt from Steps 2, 3 and 5, attaching its source images.

```text
BASE KM-S0, the model sheet base prompt. You are making model sheets for a game's 3D artists and an image-to-3D
generator. Read all of this, then follow it for every image in this chat.

THE GOAL
Each image is one object from the reference pictures I attach, shown as a model sheet so that it can be rebuilt in 3D
exactly. It must be the same object: copy its shape, proportions, every part and detail, its colours, materials and wear
exactly as the reference shows them. Do not redesign, simplify, tidy up or improve anything. Where the
reference does not show a side, continue it plainly in the same materials and colours. Make it look like a photograph of the
real object, in the look of KM-0 (real materials, natural colour), not a painting, an illustration or a cartoon.

THE SHEET
- One square picture divided into four equal panels in a 2 x 2 grid, with a thin plain gap between them:
  top left the FRONT (the side that faces the street), top right the RIGHT SIDE, bottom left the BACK, bottom right a
  THREE-QUARTER view from the front left.
- In every panel the whole object, centred, at the same scale, filling about 80% of the panel, nothing cropped.
- Straight, orthographic-looking views for front, side and back: no perspective distortion, verticals vertical.
- A plain, even mid-grey background (#808080) in every panel. No floor, no other objects, no people.
- Light: flat, even and shadowless, as on an overcast day in a studio. No cast shadows, no dark corners added, no
  highlights or reflections painted in, no rim light. Colours exactly as the lit parts of the reference.
- Signs and lettering on the object are copied as they are in the reference, unless they resemble a real brand: then an
  invented name in the same place, size and colours. Every word legible. Add no labels, captions, arrows, numbers,
  logos or watermarks of your own.
- The object alone, solid and whole: no wires, plants, bins or other objects in front of it or touching it, nothing
  see-through but glass. Where the reference hides part of it behind something, show that part plainly.

FORMAT: aspect ratio 1:1, the largest size you can make.

Then wait for my first object.
```

### Step 1: textures

Claude builds walls and roofs from KM-P3 itself (board by board, tile by tile), so KM-T01 to T03 (boards, mortar, tiles)
are needed only when Claude asks for more variety; the grounds (KM-T07 on) are still made here. Gemini, Nano Banana 2.1
or Pro, a new chat. Attach the named source image each time. The grounds come from the level pictures: make them after
the restyle, attaching each picture's photographic version (review/kamakura/refs/photo) and KM-0, so they come out as
photographs, never painted.

```text
TEXTURE KM-T01, dark-stained timber boards. Attach KM-P3. Make the top-left plate of the attached image (dark-stained
vertical timber boards) into one seamless, tileable square texture: the same boards, grain, knots, nails and pale
weathering streaks, the same colours, flat shadowless light, no perspective. Its left edge must continue into its right
edge and its top into its bottom with no visible seam. FORMAT: aspect ratio 1:1, the largest size you can make.
```

```text
TEXTURE KM-T02, beige mortar wall. Attach KM-P3. Make the top-middle plate (beige mortar with cracks and white salt
bloom) into one seamless, tileable square texture, exactly as above: same colours, flat light, no seam at any edge.
FORMAT: aspect ratio 1:1, the largest size you can make.
```

```text
TEXTURE KM-T03, grey kawara roof tiles. Attach KM-P3. Make the top-right plate (grey glazed kawara roof tiles with dirt in
the joints) into one seamless, tileable square texture, the tile rows running straight across, exactly as above.
FORMAT: aspect ratio 1:1, the largest size you can make.
```

```text
TEXTURE KM-T04, concrete block wall with moss. Attach KM-P3. Make the bottom-left plate (a concrete block wall with moss
in the joints and at its foot) into one seamless, tileable square texture, exactly as above. FORMAT: aspect ratio 1:1,
the largest size you can make.
```

```text
TEXTURE KM-T05, worn stone. Attach KM-P3. From the bottom-middle plate (worn stone steps), make one seamless, tileable
square texture of the stone's top surface: the same grey stone, wear, moss in the cracks and dark water stains, seen
straight down, exactly as above. FORMAT: aspect ratio 1:1, the largest size you can make.
```

```text
TEXTURE KM-T06, the aluminium sliding window. Attach KM-P3. Copy the bottom-right plate (a two-pane aluminium sliding
window with a screen) as one straight-on texture of the whole window, edge to edge, flat shadowless light, the same
colours. It is a single window, not tileable. FORMAT: aspect ratio 1:1, the largest size you can make.
```

```text
TEXTURE KM-T07, the lane and its walking strip. Attach KM1-1 (its photographic version) and KM-0. Photographed in KM-0's
look, not painted. Make a seamless texture of the road surface along the front of the attached picture, seen straight
down: grey asphalt with fine cracks and patches, the white edge line and the green-painted walking strip beside it.
Tileable along its length (left edge into right edge). Flat shadowless light, the same colours. FORMAT: aspect ratio
4:1, the largest size you can make.
```

```text
TEXTURE KM-T08, stone paving. Attach KM1-3 (its photographic version) and KM-0. Photographed in KM-0's look, not
painted. Make a seamless, tileable square texture of the pale grey stone paving of the shopping street in the attached
picture, seen straight down, flat shadowless light, the same colours. FORMAT: aspect ratio 1:1, the largest size you can
make.
```

```text
TEXTURE KM-T09, the shrine's gravel. Attach KM1-4 (its photographic version) and KM-0. Photographed in KM-0's look, not
painted. Make a seamless, tileable square texture of the pale raked gravel of the shrine path in the attached picture,
seen straight down, flat light, the same colours. FORMAT: aspect ratio 1:1, the largest size you can make.
```

```text
TEXTURE KM-T10, sand, dry and wet. Attach KM2-2 (its photographic version) and KM-0. Photographed in KM-0's look, not
painted. Make a seamless texture of the beach in the attached picture seen straight down: pale dry sand at the top half
shading into darker wet sand with a line of seaweed and shells, tileable along its length (left into right). Flat light,
the same colours. FORMAT: aspect ratio 4:1, the largest size you can make.
```

```text
TEXTURE KM-T11, boardwalk planks. Attach KM2-1 (its photographic version) and KM-0. Photographed in KM-0's look, not
painted. Make a seamless texture of the weathered boardwalk planks on the sand in the attached picture, seen straight
down, sand drifted in the gaps, tileable along its length. Flat light, the same colours. FORMAT: aspect ratio 4:1, the
largest size you can make.
```

```text
TEXTURE KM-T12, rock shelf. Attach KM2-4 (its photographic version) and KM-0. Photographed in KM-0's look, not painted.
Make a seamless, tileable square texture of the dark wave-cut rock shelves in the attached picture seen straight down:
barnacles, seaweed, small tide pools. Flat light, the same colours. FORMAT: aspect ratio 1:1, the largest size you can
make.
```

```text
TEXTURE KM-T13, wet stone paving. Attach KM3-1 (its photographic version) and KM-0. Photographed in KM-0's look, not
painted. Make a seamless, tileable square texture of the wet, mossy stone paving at the foot of the attached picture
seen straight down, rain-darkened, with fallen leaves and small puddles. Flat light, the same colours. FORMAT: aspect
ratio 1:1, the largest size you can make.
```

```text
TEXTURE KM-T14, the forest trail. Attach KM3-2 (its photographic version) and KM-0. Photographed in KM-0's look, not
painted. Make a seamless, tileable square texture of the earth trail in the attached picture seen straight down: wet
dark earth, fallen leaves, small roots and stones. Flat light, the same colours. FORMAT: aspect ratio 1:1, the largest
size you can make.
```

```text
TEXTURE KM-T15, the hilltop lawn. Attach KM3-3 (its photographic version) and KM-0. Photographed in KM-0's look, not
painted. Make a seamless, tileable square texture of the wet lawn in the attached picture seen straight down. Flat
light, the same colours. FORMAT: aspect ratio 1:1, the largest size you can make.
```

### Step 2: street props

The ASSET prompts of Steps 2, 3 and 5 make model sheets: send one only when Claude asks for it by its id (Step 0). They
also list each asset's parts, source pictures and real size, which is what Claude builds it to. In the model sheet chat,
each message names its source pictures: attach them with it.

```text
ASSET KM-A01, the concrete utility pole with a transformer. Attach KM-P1 and KM1-1. The left pole on the props sheet: a
grey concrete pole with steel crossarms, white insulators, a cylindrical transformer, cable clamps and its number plates,
as on the street in KM1-1. Real size: 10 m tall above the ground (show it all), 0.35 m across at the foot.
Same rules: the 2 x 2 model sheet, flat light, grey background, identical to the reference.
```

```text
ASSET KM-A02, the plain concrete utility pole. Attach KM-P1. The second pole on the props sheet: crossarms, insulators and
a grey box, no transformer. Real size: 10 m tall, 0.35 m across. Same rules as before.
```

```text
ASSET KM-A03, the convex corner mirror. Attach KM-P1 and KM1-1. The round mirror with an orange hood on its bent green
post. Real size: 2.6 m tall, the mirror 0.6 m across. Same rules as before.
```

```text
ASSET KM-A04, the level-crossing barrier. Attach KM-P1 and KM1-1. The black-and-yellow striped barrier arm on its striped
motor box, the arm raised. Real size: the box 1.1 m tall, the arm 3.5 m long. Same rules as before.
```

```text
ASSET KM-A05, the level-crossing signal. Attach KM-P1 and KM1-1. The striped post with the yellow-and-black crossbuck,
the two red lamps, the direction lamp, the bell box and the striped guard frame at its foot. Real size: 3.6 m tall. Same
rules as before.
```

```text
ASSET KM-A06, the red drink vending machine. Attach KM-P1 and KM1-1. The red-and-white machine with its rows of drinks,
coin slot and the drawer at the bottom. Real size: 1.83 m tall, 1.0 m wide, 0.75 m deep. Same rules as before.
(Then ask for the same machine in the blue livery of KM1-1's second machine: "Now the same model sheet, the machine
painted exactly like the blue machine in KM1-1.")
```

```text
ASSET KM-A07, the bus stop pole. Attach KM-P1. The round stop sign on a white post with the timetable board, on a round
concrete base. Real size: 2.3 m tall. Same rules as before.
```

```text
ASSET KM-A08, the city bicycle. Attach KM-P1 and KM1-1. The dark brown city bicycle with the front basket, stand down.
Real size: 1.8 m long, 1.0 m tall. Same rules as before.
```

```text
ASSET KM-A09, the stone lantern, tall. Attach KM-P1 and KM1-4. The tall mossy stone lantern. Real size: 2.2 m tall. Same
rules as before.
```

```text
ASSET KM-A10, the stone lantern, small. Attach KM-P1 and KM3-1. The short stone lantern. Real size: 1.3 m tall. Same rules
as before.
```

```text
ASSET KM-A11, the small vermilion torii. Attach KM-P1 and KM1-1. The vermilion torii with black top beam and black feet.
Real size: 2.6 m tall, 2.8 m wide. Same rules as before.
```

```text
ASSET KM-A12, the paper lantern. Attach KM-P1. The white paper lantern with its black lettering and red emblem, hanging
from its hook. Real size: 0.6 m tall. Same rules as before.
```

```text
ASSET KM-A13, the noren curtain. Attach KM-P1. The blue-white-blue shop curtain on its pole. Real size: 1.4 m wide, 1.0 m
tall. Same rules as before.
```

```text
ASSET KM-A14, the shop signboards. Attach KM-P1. The two wooden shop signs with brushed lettering, each on its own as a
straight-on texture (front only is enough; show the back as plain wood). Real size: 1.4 m by 0.45 m. Same rules as before.
```

```text
ASSET KM-A15, the whitebait drying rack. Attach KM-P1 and KM2-3. The wooden rack with three shelves of shallow bamboo
trays of drying whitebait. Real size: 1.6 m wide, 0.8 m deep, 1.2 m tall. Same rules as before.
```

```text
ASSET KM-A16, the trail signpost. Attach KM3-1 and KM3-2. The wooden post with two pointing boards (hiking course). Real
size: 1.9 m tall. Same rules as before.
```

```text
ASSET KM-A17, the umbrella stand. Attach KM3-1. The metal stand of clear umbrellas by the rest hut. Real size: 0.9 m tall.
Same rules as before.
```

```text
ASSET KM-A18, the park bench. Attach KM3-3. The wooden slatted bench on its legs. Real size: 1.8 m long, 0.8 m tall. Same
rules as before.
```

### Step 3: vehicles

```text
ASSET KM-V01, the tram. Attach KM1-1, KM-0 and KM1-2. The single green-and-cream tram car (an invented livery), with its
pantograph, headlights, the door and window rows; its interior seen through the windows matches KM1-2. Real size: 12 m
long, 2.5 m wide, 3.8 m tall to the pantograph's foot. Same rules as before.
```

```text
ASSET KM-V02, the kei truck. Attach KM-P1. The small white pickup truck, empty, with its rust spots. Real size: 3.4 m
long, 1.48 m wide, 1.8 m tall. Same rules as before.
```

```text
ASSET KM-V03, the scooter with a delivery box. Attach KM-P1 and KM2-3. The green-and-white step-through scooter with a
front basket and the white box on its rear rack. Real size: 1.8 m long, 1.1 m tall. Same rules as before.
```

```text
ASSET KM-V04, the rickshaw. Attach KM-P1 and KM1-3. The rickshaw with the folded black hood, the red seat and the long
shafts resting on the ground. Real size: 2.6 m long with the shafts, 1.6 m tall. Same rules as before.
```

### Step 4: plants

A new Gemini chat. These paint the leaves and bark the script-built trees are dressed in.

```text
FOLIAGE KM-F01, needles and sprays. Attach KM-P2. Paint isolated clumps of foliage exactly like the attached plants, on a
pure white background, flat shadowless light, no stems crossing each other, spread out in a grid with space between
them: eight clumps of the black pine's needles (top left plant), eight sprays of the Japanese cedar (the tall conifer),
four of the bonsai pine. Same colours, photographed like KM-0. FORMAT: aspect ratio 1:1, the largest size you can make.
```

```text
FOLIAGE KM-F02, broad leaves. Attach KM-P2. As KM-F01, on white: eight clumps of the camphor tree's leaves, eight of the
cherry's (in green leaf), six of the persimmon's leaves with two orange fruits among them. FORMAT: aspect ratio 1:1, the
largest size you can make.
```

```text
FOLIAGE KM-F03, bamboo. Attach KM-P2 and KM3-3. As KM-F01, on white: ten bamboo leaf sprays, and four straight lengths of
the green bamboo culm with its nodes, upright. FORMAT: aspect ratio 1:1, the largest size you can make.
```

```text
FOLIAGE KM-F04, flowers. Attach KM-P2 and KM3-1. As KM-F01, on white: eight blue and four pink-violet hydrangea flower
heads with their leaves, six clumps of the azalea in bloom, six morning-glory vines with flowers. FORMAT: aspect ratio
1:1, the largest size you can make.
```

```text
FOLIAGE KM-F05, bark and moss. Attach KM-P2. Five straight-on, seamless vertical bark strips side by side, each tileable
top to bottom: the black pine's, the camphor's, the cedar's, the cherry's (with its dark band) and the persimmon's; and a
sixth strip of the moss and ferns from the mossy stone. Flat light, the same colours. FORMAT: aspect ratio 1:1, the
largest size you can make.
```

### Step 5: buildings and set pieces

In the model sheet chat, in this order: the two shared ends first.

```text
ASSET KM-B01, the home. Attach review/kamakura/refs/photo/KM1-1_hase_lanes.png. The kid's two-storey house at the left
of the picture: dark-stained timber walls, grey kawara roofs (the hipped upper roof, and the skirt roof round the ground
floor with the entrance gable), aluminium windows, the balcony rail, the two air-conditioner units, the entrance under
the gable with its sliding lattice doors; with its dark board fence either side of the entrance (not the pots or the
plants: they are separate). Real size: 11.2 m wide with the fence, 8.2 m deep, 6.8 m to the ridge. Same rules as
before.
```

```text
ASSET KM-B02, the school. Attach KM1-4. The three-storey white concrete school with the clock on its end wall, its
windows, stair tower and roof plant, as seen behind its gate. Real size: 40 m long, 12 m deep, 13 m tall. Same rules as
before; the front is the side facing the sports ground.
```

```text
ASSET KM-B03, the school gate. Attach KM1-4. The two square concrete gate pillars with the school's name plate, the
sliding iron gate, the wall either side and the wooden notice board. Real size: the pillars 2.2 m tall, 6 m apart. Same
rules as before.
```

```text
ASSET KM-B04, the beige stucco house. Attach KM1-1. The two-storey beige house behind the level crossing: stucco walls, a
low tiled roof, balconies, windows. Real size: 9 m wide, 8 m deep, 7.5 m tall. Same rules as before.
```

```text
ASSET KM-B05, the little shrine. Attach KM1-1. The small shrine up the stone steps: the stone retaining wall, the steps,
the stone lantern, and the small shrine building at the top (the torii is KM-A11). Real size: the wall 1.5 m tall, the
shrine 2.5 m tall. Same rules as before.
```

```text
ASSET KM-B06, Hase Station's platform. Attach KM1-1. The short platform with its corrugated canopy on steel posts, the
timetable boards, the IC card reader on its post and the railings. Real size: 10 m long, 3 m deep, 3.2 m tall. Same rules
as before.
```

```text
ASSET KM-B07, the overhead wire gantry. Attach KM1-1. The steel lattice pole and arm that carry the tram's overhead wire.
Real size: 7.5 m tall, the arm 4 m. Same rules as before.
```

```text
ASSET KM-B08, Kamakura Station's gateway. Attach KM1-3. The big red torii-shaped gateway with its signboard over the
station square. Real size: 6 m tall, 6 m wide. Same rules as before.
```

```text
ASSET KM-B09, the croquette shop. Attach KM1-3. The second building from the left of the shop row: the two-storey timber
shop with the croquette signboard, the counter, the curtains, the stools. Real size: 6 m wide, 7 m tall. Same rules as
before.
```

```text
ASSET KM-B10, the rice-cracker shop. Attach KM1-3. The shop with the large "senbei" signboard, the grill and the jars of
crackers. Real size: 6 m wide, 7 m tall. Same rules as before.
```

```text
ASSET KM-B11, the sweets and souvenir shop. Attach KM1-3. The first and the last shops of the row: the soft-serve stand
with its displays, and the souvenir shop with its racks of fans and chopsticks and the rusty roof. Make one sheet for each
(two images). Real size: each 5 to 6 m wide, 7 m tall. Same rules as before.
```

```text
ASSET KM-B12, the shrine's side gate. Attach KM1-3. The wooden gate with its moss-covered tiled roof, the fence beside it
and the stone lanterns. Real size: 3.5 m tall, 3 m wide. Same rules as before.
```

```text
ASSET KM-B13, the purification pavilion. Attach KM1-4. The small timber pavilion over the stone water basin. Real size:
2.8 m tall, 2.4 m wide. Same rules as before.
```

```text
ASSET KM-B14, the arched stone bridge. Attach KM1-4. The steeply arched stone bridge with its stone railings over the
lotus pond (the bridge only; the pond is made separately). Real size: 9 m long, 3 m wide, 1.8 m high at the crown. Same
rules as before.
```

```text
ASSET KM-B15, the fortune racks. Attach KM1-4. The two wooden racks hung with white paper fortunes. Real size: 1.8 m tall,
1.6 m wide each. Same rules as before.
```

```text
ASSET KM-B16, the shrine hall on its steps. Attach KM1-4. The vermilion hall and gate at the top of the stone stairs, with
the stone stairs. Real size: the hall 7 m tall, the stairs 6 m high. Same rules as before.
```

```text
ASSET KM-B17, the surf shop. Attach KM2-1. The two-storey surf shop with the wetsuits hanging, the boards leaning and the
small porch. Real size: 6 m wide, 7 m tall. Same rules as before.
```

```text
ASSET KM-B18, the coast road tunnel. Attach KM2-1. The concrete pedestrian tunnel portal under the coast road, with the
rusty sign, the guardrail above and the road signs. Real size: the portal 3 m tall, 3.5 m wide, the embankment 5 m tall.
Same rules as before.
```

```text
ASSET KM-B19, the surf rental hut. Attach KM2-1. The dark timber hut with racks of surfboards and the bicycles at its side.
Real size: 6 m wide, 5.5 m tall. Same rules as before.
```

```text
ASSET KM-B20, the fishing boat. Attach KM2-2. The small weathered fishing boat on wooden rollers with its nets and crates
(make the boat alone; the nets and crates as a second sheet). Real size: 5.5 m long, 1.6 m wide. Same rules as before.
```

```text
ASSET KM-B21, the lifeguard tower. Attach KM2-2. The wooden lifeguard tower with its ladder and flag. Real size: 4.5 m
tall to the platform's roof. Same rules as before.
```

```text
ASSET KM-B22, Grandma's whitebait shop. Attach KM2-3. The two-storey timber shop with its signboard, the noren, the glass
counter, the polystyrene boxes and the hose reel (the drying racks and the scooter are separate). Real size: 7 m wide, 7 m
tall. Same rules as before.
```

```text
ASSET KM-B23, the sea wall with steps. Attach KM2-3 and KM2-2. A section of the concrete sea wall with the steps down to
the beach. Real size: 2.5 m tall, the section 8 m long. Same rules as before.
```

```text
ASSET KM-B24, the great wooden torii. Attach KM2-4. The large unpainted grey wooden torii at the foot of the avenue. Real
size: 8 m tall, 8 m wide. Same rules as before.
```

```text
ASSET KM-B25, the avenue's shops. Attach KM2-5. The bakery, the pottery shop and the sweets shop: one sheet each (three
images). Real size: each 6 m wide, 7 m tall. Same rules as before.
```

```text
ASSET KM-B26, the great red torii. Attach KM2-5. The large vermilion torii in front of the school. Real size: 9 m tall,
9 m wide. Same rules as before.
```

```text
ASSET KM-B27, the home's back gate. Attach KM3-1. The roofed wooden gate in the dark fence, with the mossy stone wall.
Real size: 2.8 m tall. Same rules as before.
```

```text
ASSET KM-B28, the rest hut. Attach KM3-1. The small open timber rest hut with its tiled roof and bench. Real size: 3 m
tall, 2.5 m wide. Same rules as before.
```

```text
ASSET KM-B29, the cave tomb. Attach KM3-2. The rock face with the square cave cut into it and the stone pagoda inside
(the cliff as a shallow set piece, seen from the front). Real size: the opening 2.5 m tall, the cliff 6 m wide. Same rules
as before.
```

```text
ASSET KM-B30, the wooden footbridge. Attach KM3-2. The short wooden footbridge with its rails. Real size: 4 m long, 1.2 m
wide. Same rules as before.
```

```text
ASSET KM-B31, the bell tower. Attach KM3-3. The bell tower: the tiled roof on four posts, the bronze bell and the hanging
log, on its stone base. Real size: 5 m tall. Same rules as before.
```

```text
ASSET KM-B32, the statue. Attach KM3-3. The bronze seated statue on its stone plinth with the plaque. Real size: 2.6 m
tall with the plinth. Same rules as before.
```

### Step 6: the kit (Claude Code)

```text
BUILD KM-K, the Kamakura kit. Read CLAUDE.md, docs/LEARNINGS.md, docs/PERFORMANCE.md, docs/ART_DIRECTION.md ("Production
rules") and docs/KAMAKURA_BUILD.md first. The pictures are in review/kamakura/refs, with the eight sheets and plates
(KM-P1 to P8: every asset's id in "The sheets' assets, by id"), the textures in review/kamakura/textures (KM-T), the
foliage in review/kamakura/foliage (KM-F), any model sheets in review/kamakura/sheets. The animals (KM-N) go into the
animals kit, built from KM-P4 and KM-P8 like the props.
1. The models, in this plan's order, in tools/blender/kit_buildings_km.py (the home and the vending machine are its
   proof): measure each asset in its source picture (pixels to the metre from a known size), build it by script at real
   size (front to -Y, origin on the ground), project the picture's pixels onto the faces toward the street, sample its
   materials for the sides, back and roofs, repair the picture's glitches (each one noted). Cut out what stands in front
   of a building into its own model. Where a side or back seen in play has no picture, ask me for that asset's sheet by
   its id. Only the statue (KM-B32), or a shape boxes and slopes can't build, comes from Meshy (the GLB from me in
   review/kamakura/models, or through Meshy's API if I have given my key in the secure credential form, telling me the
   credits first).
2. The kit: every model in the Kamakura atlas (4096 x 4096, padded for the whole mip chain), one material (Toon, _Lighting
   0.25: the pictures carry their own light), one FBX per model and the manifest into Assets/_Game/Art/Models/Kamakura.
3. The plants: extend kit_plants.py with Kamakura's (black pine, camphor, cedar, cherry in leaf, bamboo, hydrangea, azalea,
   persimmon, bonsai, morning glory, mossy stone), shaped from KM-P2's silhouettes, dressed with the KM-F sheets and the
   pictures' own leaves.
4. Review: render every model beside its source picture, straight on and turned, from the game camera, in all four looks,
   and the whole kit at play size (review/kamakura/kit_*.jpg). List every model's triangles against its budget and the
   atlas's memory. Show me the boards before anything goes into a level.
```

### Step 7: the levels (Claude Code, in this order)

```text
BUILD KM-L00, Kamakura's routes in the game. Read CLAUDE.md, docs/LEARNINGS.md, docs/CITIES.md ("Kamakura") and
docs/KAMAKURA_BUILD.md first. Add Kamakura's three new routes beside the original town's 23 levels (which stay until
KM-L99): level ids KM1-1 ... KM3-3 in Editor/GeneratedContent.cs, their stops in Levels/RouteTable.cs (the ids in
review/kamakura/map/KamakuraMapLayout.json: hase, kamakuraStation, shrineSideGate, boardwalk, grandmasShop,
lifeguardTower, greatTorii, trailSign, genjiyama), scenes <id>_KM. The map's layout is that file (docs/KAMAKURA_BUILD.md,
"The map plan"; tools/city_map/kamakura.py writes and checks it). Build the home stem (out of the gate to the corner)
and the school approach (from under the upper torii along the road to the school gate; route 1 joins it at the zebra
crossing) once, as pieces every route's first and last legs use. Nothing is shown to players yet.
(Done in part: Levels/CityRoutes.cs holds Kamakura's routes, legs and stops beside RouteTable, which stays the original
town's six until KM-L99; the names are in StringTables; CityRoutesTests checks them against docs/CITIES.md and the map
plan. The level ids join GeneratedContent's table, with their scenes, as each level is built, KM-L11 on.)
Every level then places the sheets' assets its prompt lists, by id (docs/KAMAKURA_BUILD.md, "The sheets' assets, by id"),
by that section's rules for the levels.
```

```text
BUILD KM-L11, KM1-1 Hase Lanes (dribble). Build the level from review/kamakura/refs/KM1-1_hase_lanes.png, left to right:
the home and its fence (the home stem's start), the persimmon, the potted plants and morning glories, the bicycle, the
convex mirror, the red and the blue vending machines, the little shrine with its torii and steps, the lane, the level
crossing (bells, lamps, barriers: the tram passes, wait for it), the beige house behind, the poles and the gantry, Hase
Station's platform with the hydrangeas (the stop). The play lane is the green walking strip. Hazards: a line of
first-graders in yellow caps walking to school (don't bump them), a delivery scooter, the cat on the wall.
From the sheets: on the home, its air conditioners' backs and stands (KM-A22), its meters and letterbox (KM-A23, A24)
and the backs of its pots (KM-G26 to G33); the blue
vending machine (KM-A19) beside the red, the recycling bins (KM-A20) beside them; a control cabinet (KM-A25) by the
crossing; street lamps (KM-A26) on the poles; the tram's front at the crossing (KM-V01); Hase's ticket gate and name
board (KM-A28, A29); pink and violet hydrangeas (KM-G19, G20) among the blue. Animals: the ginger cat on the block wall
(KM-N01, WallCat: the hazard above); sparrows on the pavement (KM-N08); swallows on the wires, darting low over the
lane (KM-N09); a crow on the recycling bins (KM-N06). Then: the coin audit, LevelFeasibility, and a side-by-side of
preview_street.py through the game camera against the reference.
```

```text
BUILD KM-L13, KM1-3 Komachi-dori (dribble). From review/kamakura/refs/KM1-3_komachi_dori.png, left to right: the station
square (the taxi sign, the barriers, the bicycles, the red gateway), the convex mirror and the pole, the soft-serve stand,
the croquette shop, the rice-cracker shop, the souvenir shop with its banners, the "beware of kites" sign, the rickshaw,
the shrine's side gate (the stop). Stone paving. Hazards: dense sightseers, the rickshaw as a slow moving obstacle to ride
behind, a black kite diving at a snack (KM-N05: the Seagull dive). From the sheets: the phone box and a bicycle rack in
the station square (KM-A21, A27), the bins (KM-A20), a street lamp (KM-A26); along the shops the kite sign (KM-A30),
nobori flags (KM-A31), the chalkboard and stools (KM-A32), the souvenir rack (KM-A33), crates (KM-A34); the shops' tin
roofs in rusty corrugated iron (KM-T16). Animals: pigeons in the station square (KM-N07, GroundBird: they burst up as
the ball comes), a calico cat asleep on a shop's step (KM-N21), sparrows under the stools (KM-N08). Same checks as
KM-L11.
```

```text
BUILD KM-L14, KM1-4 The Shrine Bridge (dribble, ends at school). From the shrine's side gate straight on up the street
along the shrine's east side, then right to the school (the map plan). The play lane is the street's pavement; the
shrine is seen over its low stone wall, as review/kamakura/refs/KM1-4_the_shrine_bridge.png shows it: the gravel, the
purification pavilion, the lanterns, the arched stone bridge over the lotus pond, the fortune racks, the stairs and hall
behind. At the top, the zebra crossing (wait for the green man: M5), then right along the road to the school gate (the
end). From the sheets: the big ginkgo leaning over the wall (KM-G12), the lotus in the pond (KM-G22), the hall's
vermilion timber (KM-T18), the shrine's mossy stone wall along the street (KM-T19), the cherry in blossom at the school
gate (KM-G16), a clipped hedge along the school (KM-G21). Animals: koi under the lotus (KM-N12, N13), a turtle basking
on a stone in the pond (KM-N14), a grey heron at the pond's edge (KM-N15: it lifts off slowly as the kid passes),
pigeons and turtle doves on the pavement (KM-N07, N20: they burst up as the ball comes), a swallowtail and a red
dragonfly over the lotus (KM-N25, N26), a white-eye in the cherry (KM-N18). Same checks.
```

```text
BUILD KM-L12, the ride (mini-game M1) and KM1-2 Ride the Enoden. Build the ride system once (docs/CITIES.md, M1: tap the
card reader in time, board before the chime ends, keep the ball still against the sway with the stick and KICK's hold,
press STOP at your stop; a missed stop makes the next leg longer). Then KM1-2: a fixed side-on camera inside the tram,
built from review/kamakura/refs/KM1-2_ride_the_enoden.png (the benches, straps, poles, windows, door, route map,
next-stop display, stop button; the houses outside slide past as painted layers); three stops, Yuigahama, Wadazuka,
Kamakura; the grandmother boarding at Yuigahama (give up your seat for a bonus). From the sheets: the stations seen
through the doors at each stop with their ticket gates and name boards (KM-A28, A29); swallows on the wires and pigeons
on the platforms (KM-N09, N07) in the passing layers. Tests for the ride's rules.
```

```text
BUILD KM-L21, KM2-1 Down to Yuigahama (dribble). From review/kamakura/refs/KM2-1_down_to_yuigahama.png: the home stem,
then the houses, the lane, the surf shop, the tunnel under the coast road (dark: DarkZone), the surf rental hut, the
boardwalk onto the sand (the stop). From the sheets: surfboard racks with wetsuits (KM-A36), the bicycle rack with
board carriers (KM-A27), a letterbox at each house (KM-A24); the surf huts in silver-grey timber (KM-T17), the tunnel
and the road's embankment in streaked concrete (KM-T20), the neighbours' houses in ceramic siding (KM-T21); dune grass
at the boardwalk's end (KM-G23), the garden pines (KM-G15). Animals: a Shiba Inu on its patch of the lane before the
tunnel (KM-N04, the Dog hazard: it noses a low ball back; chip it over), a black-and-white cat stretched out on a wall
(KM-N22), sparrows and a wagtail on the boardwalk (KM-N08, N17). Same checks.
```

```text
BUILD KM-L22, KM2-2 Yuigahama Morning (dribble). From review/kamakura/refs/KM2-2_yuigahama_morning.png: along the beach
past the surfboards, the fishing boats on their rollers with the nets and crates, the lifeguard tower, the litter sacks,
the sea wall and the beach houses, to the road and Grandma's shop (the stop). Tide on the sand (Tide), a black kite
circling (KM-N05). From the sheets: the boats in 3D (KM-B20), crab traps and nets (KM-A37), fish boxes (KM-A35), dune
grass at the foot of the sea wall (KM-G23), the sea wall in streaked concrete (KM-T20). Animals: gulls standing on the
sand and crossing over the sea (KM-N10), an egret wading at the water's edge (KM-N11), shore crabs at the tide line
(KM-N27), a crow at the litter sacks (KM-N06). Same checks.
```

```text
BUILD KM-L23, the errand (mini-game M2) and KM2-3 Grandma's Whitebait Shop. Build the errand system once (docs/CITIES.md,
M2), then KM2-3 at the shop from review/kamakura/refs/KM2-3_grandmas_whitebait_shop.png: fold the furoshiki's four
corners in the order shown, tie the knot in two timed taps; the bento then rides on the backpack for the rest of the
route (the Delivered badge). From the sheets: the fish boxes and hose reel (KM-A35), crates (KM-A34). Animals: a
calico cat on the shop's step, watching the drying whitebait (KM-N21), a gull on the sea wall eyeing it too (KM-N10), a
swallow at its nest under the shop's eave (KM-N09). Tests for the errand's rules.
```

```text
BUILD KM-L24, drop and come back (M4) and KM2-4 The Kite Thief. Build the drop-and-come-back system once (docs/CITIES.md,
M4), then KM2-4 from review/kamakura/refs/KM2-4_the_kite_thief.png: the rock shelves with tide pools, the steps, the pine
with the kite; the kite snatches the rice ball and drops it on a rock behind; dribble back for it before a wave covers it,
then on to the great wooden torii at the foot of the avenue (the stop). From the sheets: the rice ball itself (KM-A38),
the kite (KM-N05: perched on the pine, then the snatch), the black pines (KM-G01), dune grass on the headland (KM-G23).
Animals: a cormorant drying its wings on a rock (KM-N16), shore crabs and starfish in the tide pools (KM-N27, N28),
gulls over the waves (KM-N10). Same checks.
```

```text
BUILD KM-L25, KM2-5 Wakamiya-oji (dribble, ends at school). From review/kamakura/refs/KM2-5_wakamiya_oji.png: the raised
footpath between lanterns and cherry trees, the bakery, the pottery shop, the sweets shop, the crossing with the volunteer's
flag (wait, then cross), the great red torii, then the school approach to the school gate (the end; KM1-4's school, not the
one in this picture). From the sheets: nobori flags and a chalkboard at the shops (KM-A31, A32), the vending machines
(KM-A06, A19) with crates and bins beside them (KM-A34, A20), street lamps (KM-A26); the great torii in vermilion timber
(KM-T18); the side buildings in ceramic siding (KM-T21); a small car parked across the road (KM-V05); the cherries along
the path in green leaf (KM-G04) and the one
by the school's gate in blossom (KM-G16), a clipped hedge (KM-G21). Animals: white-eyes and a bulbul in the cherries
(KM-N18, N19), pigeons on the raised path (KM-N07), a crow on the bins (KM-N06). Same checks.
```

```text
BUILD KM-L31, KM3-1 Hydrangea Steps (dribble, the June rain). From review/kamakura/refs/KM3-1_hydrangea_steps.png: the
home stem, the back gate, the mossy wall, the stone steps between hydrangea banks (wet stone: the ball runs on), the
lantern, the rest hut and umbrella stand, the trail signpost (the stop). The rain's light: Kamakura's June drizzle
(docs/CITIES.md: about 6,800 K, no hard shadows; a CityClimate for the route). From the sheets: the hydrangea banks in
blue, pink and violet (KM-G06, G19, G20), ferns (KM-G24), mossy boulders (KM-G25), the home's back wall in mossy stone
(KM-T19). Animals, for the rain: tree frogs on the hydrangea leaves (KM-N23: one hops off when the ball lands near),
snails on the wet steps' edges (KM-N24), a bulbul calling from a branch (KM-N19). No butterflies in the rain. Same
checks.
```

```text
BUILD KM-L32, KM3-2 The Hiking Trail (dribble). From review/kamakura/refs/KM3-2_the_hiking_trail.png: roots as steps, the
signpost, the stream and the wooden footbridge, the cave tomb with its pagoda, the tanuki (a new animal), ferns, the rail
fence, to Genjiyama park (the stop). The tanuki is KM-N02 (it watches, then dashes into the undergrowth when the kid
comes close). From the sheets: the cedars' feet with their roots and ferns (KM-G18), ferns (KM-G24), mossy boulders
(KM-G25). Animals: a Pallas's squirrel crossing the trail and up a cedar (KM-N03, TreeSquirrel), a tree frog by the
stream (KM-N23), a crow in the canopy (KM-N06), a snail on the footbridge's rail (KM-N24). Same checks.
```

```text
BUILD KM-L33, KM3-3 Genjiyama Down to School (dribble, ends at school). From
review/kamakura/refs/KM3-3_genjiyama_down_to_school.png: the lawn and the statue, the benches, the bell tower (the
morning bell: a timing moment), the bamboo grove, the stone steps down, then the school approach to the school gate (the
end; KM1-4's school). From the sheets: the park's zelkovas and a maple (KM-G14, G13), the timber bamboo grove
(KM-G17), the bins by the benches (KM-A20), the school's clipped hedge (KM-G21), mossy boulders by the steps (KM-G25).
Animals: Pallas's squirrels on the lawn, dashing up the zelkovas (KM-N03, TreeSquirrel), turtle doves and a crow on the
lawn (KM-N20, N06), a wagtail on the wet school yard (KM-N17). Same checks.
```

```text
BUILD KM-L90, Kamakura's map screen. The picture: KM-MAP3 (the map zoomed out) with KM-MAP2_clean put back over its
middle at 0.83 (x 458, y 209; aligned by phase correlation, the seam blended), 3200 x 1800, as Resources/UI/KamakuraMap.
The layout: review/kamakura/map/KamakuraMapLayout.json into Resources. The map screen shows the chosen city's picture
and layout (TownMap reading a city's files; the tram ride drawn dashed). Run TownMapTests, MapViewTests and
MapIndicatorTests on it, with Kamakura's two rules (one right-angle crossing; the shared ends by the user's 5 to 15 %),
and check it on the Nord CE5.
```

```text
BUILD KM-L99, Kamakura switches to its new routes. Once every new level has passed on the Nord CE5: Kamakura plays its
three new routes instead of the original 23 levels; a save upgrade keeps every sticker, coin and star already earned
(persisted ids never change: docs/LEARNINGS.md H7); the Holiday Run's Kamakura stages follow the new streets.
```

## Cost (est., none generated)

- **Generation:** the 20 texture and foliage sheets in Gemini; a model sheet only where Claude asks for one; one Meshy
  model (the statue) on the user's meshy.ai account. Everything else is built from the pictures already made.
- **In the game:** one 4096 x 4096 Kamakura atlas (64 MB uncompressed, 16 MB as ASTC 4x4 or 7.5 MB at 6x6, a third more
  with mipmaps) plus the plants' atlas;
  every model within its budget. A street on screen is about the original town's in triangles. Checked on the Nord CE5
  before the switch (KM-L99).
