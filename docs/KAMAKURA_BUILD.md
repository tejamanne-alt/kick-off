# Building Kamakura: the assets, then the levels, in order

How Kamakura's new routes (`docs/CITIES.md`) get from the user's 17 reference images (`review/kamakura/refs`) and its map
into the game. Every prompt is here in the order it is used, and on the prompts page at the end of the Kamakura tab
(`tools/prompts_page`).

## What "identical" means here

The target is assets that look like the reference images: the same shapes and proportions, every part, the same colours,
materials, wear and painted style. To get there and stay honest about it:
- **Image-to-3D is very close, not pixel-perfect.** Meshy rebuilds the shape from the views it is given and paints the
  texture from them. Every asset is therefore checked against its source: rendered from the game camera beside the
  reference picture, in all four looks, and redone until it matches (an acceptance board: `docs/LEARNINGS.md` rule 4, A8).
- **The sources are made at the highest resolution:** model sheets at 4K, Meshy textures at its highest setting. They are
  kept in `review/kamakura/` for good. **In the game** each asset's texture is baked into the Kamakura kit's atlas at the
  size the camera shows it, within the phone's budgets (`docs/ART_DIRECTION.md`: a building 6,000 triangles, a street prop
  1,500, a tree 6,000, a gameplay structure 5,000; `docs/PERFORMANCE.md`). A vending machine is about 120 px tall on the
  phone at 864 lines: a 4K texture there costs memory on the Nord CE5 and shows nothing more.
- **No light painted in.** The game lights every surface itself (`ToonCharacter`/`Toon`, the city's light, the filters).
  So the sheets are drawn in flat, shadowless light, and Meshy textures with shading baked in are redone or delit (Tripo's
  `delight`). A texture with shadows painted in is shaded twice.
- **The painted look comes from the textures and the toon shader together.** The level pictures are painted backgrounds;
  the textures carry that paint, the toon shading keeps it flat.

## The pipeline: who does what

| Step | Who | Tool | Output |
|---|---|---|---|
| 1. Model sheets | the user | Gemini, Nano Banana Pro (2.1 for the plates) | one 2 x 2 sheet per asset: front, right, back, three-quarter; `review/kamakura/sheets/<id>_<name>.png` |
| 2. 3D models | Claude (or the user in meshy.ai) | Meshy Multi-Image to 3D, through the user's Higgsfield account | a textured GLB per asset: `review/kamakura/models/<id>_<name>.glb` |
| 3. The kit | Claude | Blender 5.2.3 (`bpy`) with pymeshlab, xatlas, trimesh | real size, cleaned, cut to budget, baked into the Kamakura atlas, FBX in `Assets/_Game/Art/Models/Kamakura` |
| 4. The levels | Claude | the level builder (`Editor/`) | Kamakura's routes, leg by leg, in route order |

- **Plants are not made in Meshy:** image-to-3D turns foliage into lumps. They are built by script as leaf-card trees
  (`tools/blender/kit_plants.py`), shaped from KM-P2's silhouettes and painted from the foliage sheets below.
- **Ground and walls** use tileable textures made from the plates (KM-P3) and the level pictures.
- **Animals** come from the animals kit, repainted (the cat); the black kite and the tanuki are new models in it.
- **The far layers** (hills, the back rows of roofs, the sea) are painted cards cut from the level pictures, so they match
  them exactly.

**Meshy settings** (Higgsfield model `meshy_multi_image_to_3d`, the sheet's four views cropped apart; `get_cost` first):

| Kind | Views | `target_polycount` (cut to budget after) | Other settings |
|---|---|---|---|
| Street prop, small set piece | 4 | 3,000 (budget 1,500) | `should_texture` on, `enable_pbr` off, `should_remesh` on, `topology` triangle, `symmetry_mode` on for symmetric things (vending machine, torii, lantern), else auto |
| Vehicle | 4 | 8,000 (budget 5,000) | as above, symmetry auto |
| Building, gameplay structure | 4 | 12,000 (budget 6,000 / 5,000) | as above, symmetry off |

If a model comes back with shading baked into its texture, run Tripo P2 (`tripo_p2_image_to_3d`, `delight` on, `auto_size`
on, `texture_quality` detailed) on the front view, or Meshy Retexture with the sheet as the style image. Meshy's terms:
a free Meshy plan gives CC BY 4.0 models; through Higgsfield, check the terms on the account before the game ships.

## The order

1. **Textures** (KM-T): the plates made tileable, and the grounds of the levels.
2. **Street props** (KM-A01 to A18): everything on the props sheet, used in every route.
3. **Vehicles** (KM-V): the tram, the kei truck, the scooter, the bicycle, the rickshaw.
4. **Plants** (KM-F): the foliage and bark sheets.
5. **Buildings and set pieces** (KM-B), in route order, the shared ends first: the home, the school, then route 1, 2, 3.
6. **The kit** (BUILD KM-K): Blender, all of the above into the Kamakura kit.
7. **The levels** (BUILD KM-L): the city's plumbing, then each route's legs in order, each mini-game system just before
   the first leg that needs it, then the map screen, then the switch from the old 23 levels.

## The prompts

### Step 0: the model sheet base prompt

Paste this first in a new Gemini chat (Nano Banana Pro). Then send one asset per message, attaching its source images.

```text
BASE KM-S0, the model sheet base prompt. You are making model sheets for a game's 3D artists and an image-to-3D
generator. Read all of this, then follow it for every image in this chat.

THE GOAL
Each image is one object from the reference pictures I attach, shown as a model sheet so that it can be rebuilt in 3D
exactly. It must be the same object: copy its shape, proportions, every part and detail, its colours, materials, wear
and painted style exactly as the reference shows them. Do not redesign, simplify, tidy up or improve anything. Where the
reference does not show a side, continue it plainly in the same materials and colours. Keep the painted look of the
reference (a detailed hand-painted anime background style), not a photograph and not a cartoon.

THE SHEET
- One square picture divided into four equal panels in a 2 x 2 grid, with a thin plain gap between them:
  top left the FRONT (the side that faces the street), top right the RIGHT SIDE, bottom left the BACK, bottom right a
  THREE-QUARTER view from the front left.
- In every panel the whole object, centred, at the same scale, filling about 80% of the panel, nothing cropped.
- Straight, orthographic-looking views for front, side and back: no perspective distortion, verticals vertical.
- A plain, even mid-grey background (#808080) in every panel. No floor, no other objects, no people.
- Light: flat, even and shadowless, as on an overcast day in a studio. No cast shadows, no dark corners added, no
  highlights or reflections painted in, no rim light. Colours exactly as the lit parts of the reference.
- Signs and lettering on the object are copied as they are in the reference. Add no labels, captions, arrows, numbers,
  logos or watermarks of your own.

FORMAT: aspect ratio 1:1, the largest size you can make.

Then wait for my first object.
```

### Step 1: textures

Gemini, Nano Banana 2.1 or Pro, a new chat. Attach the named source image each time.

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
TEXTURE KM-T07, the lane and its walking strip. Attach KM1-1. Make a seamless texture of the road surface along the
front of the attached picture, seen straight down: grey asphalt with fine cracks and patches, the white edge line and
the green-painted walking strip beside it. Tileable along its length (left edge into right edge). Flat shadowless light,
the same colours. FORMAT: aspect ratio 4:1, the largest size you can make.
```

```text
TEXTURE KM-T08, stone paving. Attach KM1-3. Make a seamless, tileable square texture of the pale grey stone paving of the
shopping street in the attached picture, seen straight down, flat shadowless light, the same colours. FORMAT: aspect
ratio 1:1, the largest size you can make.
```

```text
TEXTURE KM-T09, the shrine's gravel. Attach KM1-4. Make a seamless, tileable square texture of the pale raked gravel of
the shrine path in the attached picture, seen straight down, flat light, the same colours. FORMAT: aspect ratio 1:1, the
largest size you can make.
```

```text
TEXTURE KM-T10, sand, dry and wet. Attach KM2-2. Make a seamless texture of the beach in the attached picture seen
straight down: pale dry sand at the top half shading into darker wet sand with a line of seaweed and shells, tileable
along its length (left into right). Flat light, the same colours. FORMAT: aspect ratio 4:1, the largest size you can make.
```

```text
TEXTURE KM-T11, boardwalk planks. Attach KM2-1. Make a seamless texture of the weathered boardwalk planks on the sand in
the attached picture, seen straight down, sand drifted in the gaps, tileable along its length. Flat light, the same
colours. FORMAT: aspect ratio 4:1, the largest size you can make.
```

```text
TEXTURE KM-T12, rock shelf. Attach KM2-4. Make a seamless, tileable square texture of the dark wave-cut rock shelves in
the attached picture seen straight down: barnacles, seaweed, small tide pools. Flat light, the same colours. FORMAT:
aspect ratio 1:1, the largest size you can make.
```

```text
TEXTURE KM-T13, wet stone paving. Attach KM3-1. Make a seamless, tileable square texture of the wet, mossy stone paving at
the foot of the attached picture seen straight down, rain-darkened, with fallen leaves and small puddles. Flat light, the
same colours. FORMAT: aspect ratio 1:1, the largest size you can make.
```

```text
TEXTURE KM-T14, the forest trail. Attach KM3-2. Make a seamless, tileable square texture of the earth trail in the
attached picture seen straight down: wet dark earth, fallen leaves, small roots and stones. Flat light, the same colours.
FORMAT: aspect ratio 1:1, the largest size you can make.
```

```text
TEXTURE KM-T15, the hilltop lawn. Attach KM3-3. Make a seamless, tileable square texture of the wet lawn in the attached
picture seen straight down. Flat light, the same colours. FORMAT: aspect ratio 1:1, the largest size you can make.
```

### Step 2: street props

In the model sheet chat. Each message names its source pictures: attach them with it.

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
four of the bonsai pine. Same colours and painted style. FORMAT: aspect ratio 1:1, the largest size you can make.
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
ASSET KM-B01, the home. Attach KM1-1. The kid's two-storey house at the left of the picture: dark-stained timber walls,
grey kawara roofs with the lower porch roof, the balcony rail, aluminium windows, the air-conditioner units, the gas meter,
the entrance door; with its dark board fence and gate in front (not the plants or the bicycle: they are separate). Real
size: 8 m wide, 7 m deep, 7.5 m to the ridge. Same rules as before.
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
rules") and docs/KAMAKURA_BUILD.md first. The model sheets are in review/kamakura/sheets (KM-A, KM-V, KM-B), the textures
in review/kamakura/textures (KM-T), the foliage in review/kamakura/foliage (KM-F).
1. For each sheet, crop its four views and run Meshy Multi-Image to 3D through Higgsfield with the settings in
   docs/KAMAKURA_BUILD.md (preflight the cost and tell me the total before generating). Save each GLB in
   review/kamakura/models.
2. Write tools/blender/kit_buildings_km.py: import each GLB, set its real size from the sheet's stated size, front to -Y,
   origin at the centre of its footprint on the ground; weld open edges and rebuild normals as polish_lib does for scans;
   decimate to the budget keeping texture seams; bake every texture into the Kamakura atlas (4096 x 4096, xatlas packing,
   islands padded for the whole mip chain); the kit's one material; export one FBX per model and the manifest into
   Assets/_Game/Art/Models/Kamakura.
3. The plants: extend kit_plants.py with Kamakura's (black pine, camphor, cedar, cherry in leaf, bamboo, hydrangea, azalea,
   persimmon, bonsai, morning glory, mossy stone), shaped from KM-P2's silhouettes, dressed with the KM-F sheets.
4. Review: render every model beside its source picture from the game camera, in all four looks, and the whole kit at
   play size (review/kamakura/kit_*.jpg). List every model's triangles against its budget and the atlas's memory. Show me
   the boards before anything goes into a level.
```

### Step 7: the levels (Claude Code, in this order)

```text
BUILD KM-L00, Kamakura's routes in the game. Read CLAUDE.md, docs/LEARNINGS.md, docs/CITIES.md ("Kamakura") and
docs/KAMAKURA_BUILD.md first. Add Kamakura's three new routes beside the original town's 23 levels (which stay until
KM-L99): level ids KM1-1 ... KM3-3 in Editor/GeneratedContent.cs, their stops in Levels/RouteTable.cs, scenes
<id>_KM. Trace the routes, stops and level nodes from review/kamakura/refs/KM-MAP1_plan.png onto KM-MAP2_clean.png into
Kamakura's map layout (as TownMapLayout.json is for the original); 2-5 and 3-3 end at the school gate. Build the home stem
(the lane from the house to the vending-machine corner) and the school approach (from the great red gate past the arched
bridge to the school gate) once, as pieces every route's first and last legs use. Nothing is shown to players yet.
```

```text
BUILD KM-L11, KM1-1 Hase Lanes (dribble). Build the level from review/kamakura/refs/KM1-1_hase_lanes.png, left to right:
the home and its fence (the home stem's start), the persimmon, the potted plants and morning glories, the bicycle, the
convex mirror, the red and the blue vending machines, the little shrine with its torii and steps, the lane, the level
crossing (bells, lamps, barriers: the tram passes, wait for it), the beige house behind, the poles and the gantry, Hase
Station's platform with the hydrangeas (the stop). The play lane is the green walking strip. Hazards: a line of
first-graders in yellow caps walking to school (don't bump them), a delivery scooter, the cat on the wall. Then: the
coin audit, LevelFeasibility, and a side-by-side of preview_street.py through the game camera against the reference.
```

```text
BUILD KM-L13, KM1-3 Komachi-dori (dribble). From review/kamakura/refs/KM1-3_komachi_dori.png, left to right: the station
square (the taxi sign, the barriers, the bicycles, the red gateway), the convex mirror and the pole, the soft-serve stand,
the croquette shop, the rice-cracker shop, the souvenir shop with its banners, the "beware of kites" sign, the rickshaw,
the shrine's side gate (the stop). Stone paving. Hazards: dense sightseers, the rickshaw as a slow moving obstacle to ride
behind, a black kite diving at a snack (the gull-style hazard, with the new kite model). Same checks as KM-L11.
```

```text
BUILD KM-L14, KM1-4 The Shrine Bridge (dribble, ends at school). From review/kamakura/refs/KM1-4_the_shrine_bridge.png:
the shrine's gravel, the purification pavilion, the lanterns, the arched stone bridge over the lotus pond (a hump to
jump), the fortune racks, the stairs and hall behind, then the school approach to the school gate (the end). Pigeons.
Same checks.
```

```text
BUILD KM-L12, the ride (mini-game M1) and KM1-2 Ride the Enoden. Build the ride system once (docs/CITIES.md, M1: tap the
card reader in time, board before the chime ends, keep the ball still against the sway with the stick and KICK's hold,
press STOP at your stop; a missed stop makes the next leg longer). Then KM1-2: a fixed side-on camera inside the tram,
built from review/kamakura/refs/KM1-2_ride_the_enoden.png (the benches, straps, poles, windows, door, route map,
next-stop display, stop button; the houses outside slide past as painted layers); three stops, Yuigahama, Wadazuka,
Kamakura; the grandmother boarding at Yuigahama (give up your seat for a bonus). Tests for the ride's rules.
```

```text
BUILD KM-L21, KM2-1 Down to Yuigahama (dribble). From review/kamakura/refs/KM2-1_down_to_yuigahama.png: the home stem,
then the houses, the lane, the surf shop, the tunnel under the coast road (dark: DarkZone), the surf rental hut, the
boardwalk onto the sand (the stop). Same checks.
```

```text
BUILD KM-L22, KM2-2 Yuigahama Morning (dribble). From review/kamakura/refs/KM2-2_yuigahama_morning.png: along the beach
past the surfboards, the fishing boats on their rollers with the nets and crates, the lifeguard tower, the litter sacks,
the sea wall and the beach houses, to the road and Grandma's shop (the stop). Tide on the sand (Tide), a black kite
circling. Same checks.
```

```text
BUILD KM-L23, the errand (mini-game M2) and KM2-3 Grandma's Whitebait Shop. Build the errand system once (docs/CITIES.md,
M2), then KM2-3 at the shop from review/kamakura/refs/KM2-3_grandmas_whitebait_shop.png: fold the furoshiki's four
corners in the order shown, tie the knot in two timed taps; the bento then rides on the backpack for the rest of the
route (the Delivered badge). Tests for the errand's rules.
```

```text
BUILD KM-L24, drop and come back (M4) and KM2-4 The Kite Thief. Build the drop-and-come-back system once (docs/CITIES.md,
M4), then KM2-4 from review/kamakura/refs/KM2-4_the_kite_thief.png: the rock shelves with tide pools, the steps, the pine
with the kite; the kite snatches the rice ball and drops it on a rock behind; dribble back for it before a wave covers it,
then on to the great wooden torii at the foot of the avenue (the stop). Same checks.
```

```text
BUILD KM-L25, KM2-5 Wakamiya-oji (dribble, ends at school). From review/kamakura/refs/KM2-5_wakamiya_oji.png: the raised
footpath between lanterns and cherry trees, the bakery, the pottery shop, the sweets shop, the crossing with the volunteer's
flag (wait, then cross), the great red torii, then the school approach to the school gate (the end; KM1-4's school, not the
one in this picture). Same checks.
```

```text
BUILD KM-L31, KM3-1 Hydrangea Steps (dribble, the June rain). From review/kamakura/refs/KM3-1_hydrangea_steps.png: the
home stem, the back gate, the mossy wall, the stone steps between hydrangea banks (wet stone: the ball runs on), the
lantern, the rest hut and umbrella stand, the trail signpost (the stop). The rain's light: Kamakura's June drizzle
(docs/CITIES.md: about 6,800 K, no hard shadows; a CityClimate for the route). Same checks.
```

```text
BUILD KM-L32, KM3-2 The Hiking Trail (dribble). From review/kamakura/refs/KM3-2_the_hiking_trail.png: roots as steps, the
signpost, the stream and the wooden footbridge, the cave tomb with its pagoda, the tanuki (a new animal), ferns, the rail
fence, to Genjiyama park (the stop). Same checks.
```

```text
BUILD KM-L33, KM3-3 Genjiyama Down to School (dribble, ends at school). From
review/kamakura/refs/KM3-3_genjiyama_down_to_school.png: the lawn and the statue, the benches, the bell tower (the
morning bell: a timing moment), the bamboo grove, the stone steps down, then the school approach to the school gate (the
end; KM1-4's school). Same checks.
```

```text
BUILD KM-L90, Kamakura's map screen. Show Kamakura's map (KM-MAP2_clean, at the game's 3200 x 1800) with its three routes,
stops and level nodes from the layout traced in KM-L00, on the map screen when Kamakura is chosen. The same checks as the
original map (TownMapTests, MapViewTests, MapIndicatorTests).
```

```text
BUILD KM-L99, Kamakura switches to its new routes. Once every new level has passed on the Nord CE5: Kamakura plays its
three new routes instead of the original 23 levels; a save upgrade keeps every sticker, coin and star already earned
(persisted ids never change: docs/LEARNINGS.md H7); the Holiday Run's Kamakura stages follow the new streets.
```

## Cost (est., none generated)

- **Generation:** about 55 model sheets and 20 texture and foliage sheets in Gemini; about 55 Meshy models through
  Higgsfield (credits per model shown by `get_cost` before any run).
- **In the game:** one 4096 x 4096 Kamakura atlas (16 MB uncompressed, about 4 MB compressed) plus the plants' atlas;
  every model within its budget. A street on screen is about the original town's in triangles. Checked on the Nord CE5
  before the switch (KM-L99).
