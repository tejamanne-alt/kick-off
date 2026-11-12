# Kick Off 2: image prompts for the five cities (ChatGPT and Gemini)

Copy-paste prompts for the reference images each city is modelled and lit from, for **ChatGPT** (ChatGPT Images) and
**Gemini** (Nano Banana). They are the same prompts: only the format line and how each message is sent differ ("The two
versions" below). The page made by `tools/prompts_page` does both for you: pick the tool at the top, and each Copy button
gives that tool's version. The cities, their routes and legs are
designed in `docs/CITIES.md`. Every level here has its own prompt, under the same id (`KM1-1` is Kamakura, route 1,
leg 1).

There are three layers, pasted in order:
1. **The base prompt:** the same for every city.
2. **The city block:** the place, its buildings, materials, plants, street, vehicles, and its own light and climate.
3. **One shot per message:** a level (its street from start to end), a mini-game's set, the city's look target, or an
   asset sheet, ending with its format line.

## What the images are for

The game never shows these images. Every building, prop and plant is modelled by script in Blender
(`tools/blender/kit_*.py`), and its atlas is painted by script too. The images set three things:
- **What to model and how:** proportions, construction, materials, weathering. So they are photorealistic: a photograph
  can be measured, an illustration invents.
- **The city's light and colour:** colour temperature, sun height, haze, how the shade goes blue. The game's light
  (`World/WorldLook`) and grade (`World/PostFX`) are tuned to the **look target** of each city. The base prompt asks
  for the cinematic, sun-drenched, lived-in quality of the user's reference shots without copying any game.
- **Colour for the atlas:** the **plates** and **sheets** are in flat, neutral light, so their colours can be read true.
  A street shot in golden light can't be colour-picked; a plate can.

The straight-on side view matters: the game is a side-scroller, so a street is seen as a row of fronts. A picture
looking down a street can't be measured into one.

## The two versions

**Ask for the widest picture each tool makes.** The game is a side-scroller and a leg is a long strip of street, so a
wider picture shows more of it at once, as the phone does (its screen is about 2.2:1).

| | ChatGPT (ChatGPT Images 2.0 and later) | Gemini (Nano Banana 2.1, the app's default) |
|---|---|---|
| Street and set shots (levels, mini-game sets) | **3:1**, the widest it makes | **4:1** (it also makes 8:1, too thin a strip to show a three-storey front with its roofs and sky) |
| Look target | 21:9 | 21:9 |
| Sheet | 16:9 | 16:9 |
| Plate (six squares in a grid) | 3:2 | 3:2 |
| The first message | the base prompt and the city block | the base prompt (its Gemini format line) and the city block |
| Each shot | the shot, ending with its format line | the city block again, then the shot, ending with its format line |

Neither app has a ratio picker for these: the ratio is asked for in words, so every shot ends with a `FORMAT:` line (the
page adds it). Gemini follows its latest message most closely and lets earlier instructions fade over a long chat, so a
Gemini shot carries the city block with it. If Gemini says it can't make 4:1 (Nano Banana Pro stops at 21:9), ask for 21:9.

**Which Gemini model:** Nano Banana 2.1 for every street shot: it is the Gemini app's default, makes 4:1, and its
photographs hold up well against Pro's for a fraction of the cost. Nano Banana Pro (Gemini 3 Pro Image; on a Google AI Pro
or Ultra plan, "Redo with Pro" in the image's three-dot menu) for the look targets, the sheets and any shot where 2.1
misses part of a long prompt: it follows long, detailed prompts more closely and draws signs and small text better. For
an exact ratio and 4K, Google AI Studio sets both as settings instead of words. (Model names and menus as of November
2026: check the app if they have moved.)

## How to use them

1. **One chat per city, in one tool.** Start a new chat and paste the **first message**: the base prompt and that city's
   block together (in Gemini, the base prompt with its Gemini format line). If it answers with a test image or a question,
   say "Ready for the shots."
2. **Then one shot per message, one level at a time,** in the order listed, each ending with its `FORMAT:` line. In
   Gemini, paste the city block above each shot. For the next leg of the same route, attach the previous leg's image:
   the shot says what continues.
3. If the pictures drift (people creeping in, a street seen at an angle, edges bending, the wrong light, brand names, a
   narrower picture), paste the base prompt again with "Keep to these rules."
4. **Check each picture before saving it** (what comparing Kamakura's pictures with their models caught,
   `docs/LEARNINGS.md` D12): it looks like the city's look target (Kamakura's KM-0 is a photograph, not a painting);
   every building is solid (nothing see-through, ghosted or half-drawn); no real brand or logo, vending machines
   included; no power line crossing in front of a building; every word legible; what stands in front of a wall stands
   apart; a building seen before is the same building. If one fails, ask for just that fix ("Make the right half of the
   house solid; change nothing else") or make the picture again.
5. Save each result as `review/<city>/refs/<id>_<what>.png`, for example `review/kamakura/refs/KM1-1_hase_lanes.png`,
   outside `Assets/` so nothing reaches a build, with exactly that name (a phone upload can add `.PNG` or name it
   `IMG_1234.png`: rename it). Then ask for the city's kit to be built from them.
6. Keep each city in one tool, so its pictures match each other. Different cities can use different tools.

The order per city: the **look target** first (it fixes the light for the chat), then every level, then the sheets and
plates.

**Format lines** (end each shot with the one for its kind; the page adds them):
- ChatGPT, a street or set shot: `FORMAT: one straight-on ultra-wide panorama, aspect ratio 3:1 (the widest you can make).`
- Gemini, a street or set shot: `FORMAT: one straight-on ultra-wide panorama, aspect ratio 4:1.`
- Look target: `FORMAT: a cinematic widescreen frame, aspect ratio 21:9.`
- Sheet: `FORMAT: aspect ratio 16:9.`
- Plate: `FORMAT: aspect ratio 3:2 (three squares by two).`

## The base prompt (paste first, with the city block)

```text
You are making reference images for a video game's art team. Read all of this, then follow it for every image in this chat.

THE GAME
A side-scrolling soccer platformer for phones, rendered in 3D but seen and played from the side: a kid dribbles a football
from home to school through a real city. Each level is one leg of that trip, from one stop to the next. Our 3D artists
model the game's buildings, props and plants from your images, and tune the game's light and colour to them. So we need
both accuracy and atmosphere.

THE LOOK
Photorealistic and cinematic, like a still from a modern big-budget open-world game or a film shot on location:
- Believable light: a warm direct sun against cool blue shade, soft bounce light from the ground and walls, deep contact
  shadows under things.
- Air you can see: atmospheric haze that lightens and softens the distance, warmer toward the sun.
- Rich, real, weathered materials: sun-faded paint, water streaks under sills, grime at the foot of walls, rust bleeding
  from fixings, chipped plaster and paint, patched paving, oil stains, worn kerbs, moss in damp corners.
- A dense, lived-in street: wires and poles, signs, vents, pipes, shutters, planters, bicycles, parked vehicles, a little
  litter, puddles that mirror the sky.
- Natural colour: saturated where the city is colourful, never a colour filter or a tint over the whole picture.
Do not imitate any specific game or film, and include nothing from one: no logos, landmarks, signs or characters from a game.

CAMERA (every street image, unless a shot says otherwise)
- A straight-on side view: the street runs left to right, parallel to the picture, and the building fronts face the
  camera squarely. No diagonal streets, no vanishing point, no aerial or low-angle views.
- One continuous panorama, as if the camera slid sideways along the street, always about 9 m from the building fronts at
  an eye height of about 2.5 m: every front is seen square-on across the whole width, verticals stay vertical, and
  nothing curves or bends toward the edges. No fisheye or wide-angle stretching. The horizon a little above the middle.
- Layers from front to back: an EMPTY, continuous walking surface across the bottom fifth of the picture (the play
  lane: a sidewalk, path, boardwalk, platform or sand, flat, with nothing standing on it except at its edges), then the
  kerb or edge, the row of fronts, a back row of roofs, trees and towers, and the far skyline or hills.
- The picture reads left to right as the leg: where it starts on the left, where it ends on the right.
- Everything sharp from front to back: no depth of field, bokeh, motion blur, vignette, lens flare or film grain.
- FORMAT: a street or set shot is one ultra-wide panorama at 3:1, the widest landscape you can make; a look target is a
  21:9 widescreen frame; a sheet 16:9; a plate 3:2. Every shot ends with its own FORMAT line: use exactly that ratio.

LIGHT
Use exactly the light the city block describes: the season, the time of day, the colour temperature of the sun and of
the shade, the sun's height and side, the haze and the weather. Keep it the same in every image of this chat unless a
shot says otherwise. Highlights stay just under pure white; the darkest shadows keep a little colour.

CONTENT
- Real-world proportions: doors about 2.1 m, kerbs about 15 cm, storeys about 3 m. Ordinary scale cues: doors, steps,
  bins, parked vehicles.
- All signs, shop names, posters and adverts are INVENTED, in the city's own language and script, short and legible. No
  real brands, chains, logos or trademarks, and no readable licence plates.
- ABSOLUTELY NO PEOPLE: no pedestrians, drivers, passengers, shopkeepers, figures, silhouettes, crowds, mannequins or
  reflections of people. Where a person would stand (a counter, a balcony, a driver's seat), leave it empty. No animals
  unless a shot asks for one. Parked vehicles are empty and nothing is moving.
- Add no text, labels, captions, borders, logos or watermarks of your own.

BUILT INTO 3D (our artists cut your pictures into models, so each must be clean)
- Every building, wall and object is solid and whole: nothing transparent, ghosted, faded, double-exposed, half-drawn or
  blending into what is behind it. Only glass is see-through.
- A building that appears in more than one image is the same building in each: when I attach its earlier picture, copy
  it exactly.
- Overhead power lines and cables run from pole to pole above the rooflines or against the sky. None crosses in front of
  a building's front or roof. The poles and their wires stay.
- No real brands anywhere, vending machines, drink panels, cans and bottles included: invented names, and no lettering,
  script, colour scheme or symbol that resembles a real brand.
- Every word legible, in correct characters of the city's script: no garbled or made-up characters.
- What stands in front of a wall (pots, plants, bins, bicycles, signs) stands apart, with the wall showing between the
  pieces: nothing overlaps anything else, and together they hide at most the lowest third of a front.
- Crisp outlines against the sky: rooflines, trees, poles.

SHEETS AND PLATES
When a shot is a SHEET (objects on a plain background) or a PLATE (a flat, straight-on texture), ignore the camera and
light above and follow the shot.
- A sheet's objects never touch or overlap each other.
- A plate shows about 2 m by 2 m of real surface unless the shot gives another size, evenly weathered all over, with no
  single mark that would stand out when it repeats (no nests or clumps, paint splashes, big stains, holes or signs).

The city block follows. Then wait for my shots, one per message.
```

**In Gemini,** replace the base prompt's FORMAT line with:

```text
- FORMAT: a street or set shot is one ultra-wide panorama at 4:1; a look target is a 21:9 widescreen frame; a sheet 16:9;
  a plate 3:2. Every shot ends with its own FORMAT line: use exactly that ratio.
```

## Kamakura, Japan

### The Kamakura block (paste right after the base prompt)

```text
CITY: KAMAKURA, JAPAN
A seaside temple town on the Shonan coast of Kanagawa, an hour south of Tokyo. It must read as Kamakura and the Shonan
coast at first glance: not Kyoto, not central Tokyo, not a theme park.

BUILDINGS
- Homes: two-storey timber-and-mortar houses with grey glazed kawara tile roofs or dark standing-seam metal roofs,
  dark-stained board fences and walls, beige or white mortar walls, aluminium sliding windows with insect screens, small
  balconies with futon rails, sliding entrance doors, house name plates by the door.
- Lanes 3 to 4 m wide with no raised sidewalk (a green-painted walking strip along the edge), lined by concrete block walls
  and hedges, with tiny front gardens of potted plants.
- Shops: low two-storey shopfronts with noren curtains over sliding glass doors, hand-painted wooden signboards and
  paper lanterns, shop awnings, tables of goods out front.
- Temples and shrines: timber gates with heavy tiled roofs, vermilion torii, stone lanterns, stone steps, moss-covered
  stone walls, wooden prayer plaques.
- Lived in: air-conditioner units on brackets, gas meters, exposed pipes, corrugated sheet sheds, bicycles, plastic
  plant pots, laundry poles.

WEATHERING
Timber gone silver-grey or near black, sea-salt bloom on walls, moss on every damp stone, rust on corrugated sheet and
railings, black mould under eaves, sun-faded noren, cracked mortar.

PLANTS
Leaning Japanese black pines near the sea, camphor trees and Japanese cedars on the hills, cherry trees in full green
leaf, bamboo groves, hydrangeas, azaleas, moss, morning glories and potted bonsai at house fronts, a persimmon tree.

STREET
Asphalt lanes with white edge lines, concrete utility poles crowded with wires and transformers, round convex mirrors at
corners, yellow tactile paving, decorated manhole covers, drink vending machines, green public phones, bicycle parking,
bus stops with timetable poles. The tram: a single-track line with its overhead wire on poles, level crossings with
black-and-yellow striped bars, red flashing lights and bells.

VEHICLES (parked and empty)
A small two-car green-and-cream tram (an invented livery), kei trucks, scooters, small cars, a rickshaw with a black hood.

LIGHT AND CLIMATE
A clear May morning, about 7:45. The sun 40 degrees up, behind the camera to the left. Direct sun about 5,400 K: near
white, a hair warm. Shade about 9,000 K: a clean cool blue-grey. A deep cobalt sky with big cumulus over the sea. A soft
sea haze turns far hills blue and lightens them a little. The air is damp and clean, and stone and leaves still hold
the night's dew.
```

### Kamakura shots

```text
LOOK TARGET KM-0, Kamakura in its light. Follow the base prompt and the Kamakura block, but the camera is free.
A wide cinematic view from a hillside path down over Kamakura's tiled roofs to the sea: temple roofs among the trees, the
little tram crossing a lane, Yuigahama beach's curve with surfers' boards on the sand (no people), the coast road, the
headland and Enoshima island in a soft blue haze, cumulus over the sea. This picture sets the light and colour of every
Kamakura image.
```

#### KM1 The Enoden

```text
LEVEL KM1-1, Hase Lanes: home to Hase Station. Follow the base prompt and the Kamakura block.
Left: the kid's home, a two-storey timber-and-mortar house with a dark board fence, a persimmon tree, potted morning
glories, a bicycle under the eaves, a cat on the block wall (the one animal). Then a narrow lane between block walls, a
corner with two drink vending machines and a convex mirror, a tiny shrine gate with a small vermilion torii. In the
middle, a tram level crossing on the lane: the striped bars up, red lights, a warning sign, the single track crossing the
lane between house walls. Right: Hase Station, a small open platform with a low canopy, a ticket gate with an IC card
reader, a bank of blue hydrangeas behind the fence, the tram's overhead wire. The play lane is the lane's green walking
strip.
```

```text
LEVEL KM1-2, Ride the Enoden (mini-game set). Follow the base prompt and the Kamakura block, but the camera is inside.
Inside a small, old commuter tram car, seen straight across the aisle at standing eye height, side-on to the far wall:
a long bench seat of green moquette, wide windows showing house walls and gardens passing a metre away, hanging straps
and grab poles, a priority-seat sticker, a route map above the windows with five invented station names, a next-stop
display, a stop button, a sliding door at the right with a door chime speaker. Warm morning sun through the windows in
bright patches on the floor. Empty: no passengers.
```

```text
LEVEL KM1-3, Komachi-dori: Kamakura Station to the shrine end. Follow the base prompt and the Kamakura block.
Left: the station square's red torii-shaped gateway sign (invented name) and a taxi rank. Then the shopping street:
two-storey shopfronts with noren curtains, hand-painted signboards, paper lanterns, a sweet-potato ice cream stand, a
whitebait croquette shop with a fryer at the window, a rice cracker shop with crackers grilling, a souvenir shop with
racks of chopsticks and fans, a parked rickshaw with its black hood up, banner flags on poles, a "beware of black kites"
sign with a bird drawn on it. The street is paved in pale stone, shared with no cars. Right: the street ends at a side
gate onto the shrine's grounds.
```

```text
LEVEL KM1-4, The Shrine Bridge: through the shrine to school. Follow the base prompt and the Kamakura block.
Left: the shrine grounds' pale gravel path. A steeply arched stone bridge over a lotus pond, a stone basin with ladles
under a small roof, rows of stone lanterns, white-paper fortunes tied to a rack, big old ginkgo and camphor trees, a
broad flight of stone steps rising behind to a vermilion hall (far, small). Right: beside the shrine's wooded hill, the
school: a three-storey white concrete school with a clock on its face, a sandy sports ground behind a green fence, a
cherry tree by the gate, a sign board at the gate with an invented school name. The play lane is the gravel path, then
the pavement to the gate.
```

#### KM2 The Shonan Coast

```text
LEVEL KM2-1, Down to Yuigahama: home to the boardwalk. Follow the base prompt and the Kamakura block.
Left: the same home as KM1-1 seen from its other side, then a lane of low houses with surfboards leaning by doors and
wetsuits on hangers. Then the coast road on a low embankment, and the pedestrian tunnel under it: a short concrete tunnel
with tiled walls, dim inside, its mouth framed by a "beach" sign. Right: out of the tunnel onto a wooden boardwalk with a
surf shop with boards on racks, outdoor beach showers, a bicycle rack with board carriers, sand drifting over the boards.
```

```text
LEVEL KM2-2, Yuigahama Morning: along the beach. Follow the base prompt and the Kamakura block.
A long sandy beach seen side-on, the sea behind: dark grey-brown volcanic sand going pale where dry, a tide line of
seaweed and shells, a few surfboards stuck upright in the sand, two small fishing boats pulled up on wooden rollers with
nets heaped beside them, a lifeguard tower, white sacks of collected litter tied at the top, low waves breaking, a black
kite (the one animal) gliding above. Behind the sand, a row of leaning black pines and beach houses. Right: the beach road
with Grandma's whitebait shop (next shot). The play lane is firm wet sand.
```

```text
LEVEL KM2-3, Grandma's Whitebait Shop (mini-game set). Follow the base prompt and the Kamakura block.
The front of a small family whitebait shop on the beach road, straight on: a two-storey timber house with the shop on
the ground floor, an open front with a glass counter, a hand-painted wooden sign (invented name) and a noren curtain,
wooden racks of shallow bamboo trays with tiny white fish drying in the sun, polystyrene boxes stacked, a hose reel, a
scooter with a delivery box. On the counter, centred, a lacquered bento box on a square of patterned cloth (a furoshiki)
laid out flat, its four corners spread. Nobody at the counter.
```

```text
LEVEL KM2-4, The Kite Thief: along the rocks. Follow the base prompt and the Kamakura block.
Continue the beach from the previous image (attached). The sand gives way to a low headland of dark, wave-cut rock shelves
with tide pools, barnacles and seaweed, a path of worn steps along their top, waves washing over the lowest shelf. On a
dry rock in the middle, a single rice ball in its wrapper, dropped. A black kite on a pine branch above. Right: the beach
continues to a large wooden gateway (a torii) standing at the start of a straight avenue inland.
```

```text
LEVEL KM2-5, Wakamiya-oji: the avenue to school. Follow the base prompt and the Kamakura block.
A wide, straight avenue seen side-on along its length: down its middle a raised footpath edged with stone and lined with
stone lanterns and cherry trees in green leaf (this path is the play lane, raised about 60 cm above the road). Along the
far side, shops waking up: a bakery, a pottery shop, a sweet shop, shutters half open. At a junction in the middle, a
pedestrian crossing with a yellow "crossing volunteer" flag in a holder on a pole. Right: a large vermilion gate across
the avenue, and beside it the school's gate and its cherry tree.
```

#### KM3 The Temple Hills (June rain)

```text
LEVEL KM3-1, Hydrangea Steps: home up the temple hillside. Follow the base prompt and the Kamakura block, with this
light: a June morning in light drizzle, overcast, about 6,800 K, soft and shadowless, everything wet and glistening,
mist in the trees.
Left: the home's back gate. Then stone steps climbing a temple's hillside in long flights, banks of blue, violet and pink
hydrangeas pressing in from both sides, moss on every step, puddles in the worn hollows, a stone lantern, a small timber
rest hut with a tiled roof, clear umbrellas left in a stand, a view between trees down to wet tiled roofs. Right: the steps
end at a trail sign at the woods' edge.
```

```text
LEVEL KM3-2, The Hiking Trail: over the wooded ridge. Follow the base prompt and the Kamakura block, with KM3-1's
drizzle and mist.
A narrow earth trail along a wooded ridge, side-on: tree roots crossing it like steps, a short wooden footbridge over a
gully, the dark square mouth of an old cave tomb cut into a sandstone cliff with a moss-covered stone pagoda inside,
Japanese cedars and camphor trees dripping, ferns, a wooden trail signpost with invented place names, a raccoon dog (the
one animal) at the trail's edge. The play lane is the trail.
```

```text
LEVEL KM3-3, Genjiyama Down to School. Follow the base prompt and the Kamakura block, with KM3-1's drizzle, lifting at
the right into brighter cloud.
Left: a hilltop park's lawn with a small bronze statue on a stone plinth (invented, unnamed), benches. Then a dense grove
of tall green bamboo creaking in the wind, a temple bell tower with a big bronze bell under its tiled roof and the hanging
log that strikes it, and stone steps down through the trees to the town. Right: the school's back gate in a hedge, the
school's white wall and windows beyond.
```

#### Kamakura sheets and plates

```text
SHEET KM-P1, Kamakura street props and vehicles. Follow the base prompt's content rules, but ignore its camera and light.
On a plain mid-grey background, each object apart with space round it, every one shown straight from the front and from a
three-quarter angle, all at the same scale, in even soft studio light with a small soft shadow under each: a concrete
utility pole top with transformer and wires, a convex corner mirror, a tram level crossing (bars, lights, bell box), a
drink vending machine, a bus stop timetable pole, a bicycle with a front basket, a kei truck, a scooter with a delivery
box, a rickshaw, a stone lantern, a small torii, a paper lantern, a noren curtain, a hand-painted wooden shop sign, a
whitebait drying rack. No labels.
```

```text
SHEET KM-P2, Kamakura plants. Follow the base prompt's content rules, but ignore its camera and light.
On a plain mid-grey background, each plant apart, from the side, at the same scale, with a 1.8 m grey pole for scale (not
a person), in even soft studio light: a leaning Japanese black pine, a camphor tree, a Japanese cedar, a cherry tree in
green leaf, a clump of bamboo, a blue hydrangea bush, an azalea, a persimmon tree, a potted bonsai, a morning glory on a
trellis, a mossy stone with ferns. No labels.
```

```text
PLATE KM-P3, Kamakura texture plates. Ignore the base prompt's camera and light.
Six square texture plates in a grid, each a flat, straight-on, edge-to-edge surface with no perspective, in flat, even,
shadowless overcast light (no cast shadows, no shading, no highlights), true colours with their weathering: dark-stained
timber boards, beige mortar wall with sea-salt bloom, grey kawara roof tiles, a concrete block wall with moss, worn
stone steps, a sliding aluminium window with screen. No text.
```

```text
SHEET KM-P4, Kamakura animals and birds. Attach KM-0, KM1-1, KM2-2, KM2-4 and KM3-2 (their photographic versions once
made). Follow the base prompt's content rules, but ignore its camera and light; this sheet asks for animals.
Japan's animals and birds as they live in Kamakura on a May morning, for a game's 3D artists, on a plain mid-grey
background (#808080). Thirty figures, evenly spaced in a grid six across and five down, each apart with space round it,
no lines between them. Each figure fills its own space, not to one scale (the real sizes give the proportions). Side
views are strict profiles facing right; front views are straight on; "from below" looks straight up at the bird flying
overhead, wings fully spread, level and symmetrical. Each animal is the same individual in all its views: the same
markings, colours and proportions. Photographed in the look of KM-0 (the first picture attached): real animals with real
fur and feathers, natural colour, sharp detail, not a painting or an illustration, in even soft daylight with a small
soft shadow under the ones on the ground. No clothes, no cartoon faces or expressions.
Row 1: the ginger cat from the block wall in KM1-1 (an orange tabby with a long tail, 25 cm at the shoulder): walking,
side view; sitting, side view; sitting, front view. The tanuki from the trail in KM3-2 (a Japanese raccoon dog:
grizzled grey-brown coat, dark eye mask, dark legs, bushy tail; 30 cm at the shoulder, 60 cm long): walking, side view;
sitting, side view; standing, front view.
Row 2: a Pallas's squirrel, as at Kamakura's temples (olive-brown back, chestnut-red belly, bushy grizzled tail; 20 cm
and an 18 cm tail): running, side view; sitting up holding a nut, side view; sitting up, front view. A Shiba Inu (red
coat with cream cheeks, chest and belly, curled tail, pricked ears, a red collar and no lead; 38 cm at the shoulder):
standing, side view; sitting, side view; sitting, front view.
Row 3: the black kite from the pine in KM2-4 and the sky in KM2-2 (dark brown, a pale patch under each wing near the
tip, a shallow notched tail; 60 cm long, wings 1.6 m across): perched, side view; gliding, from below; diving at a
snack, side view, wings half folded back and talons reaching forward. A large-billed crow (glossy black, heavy arched
bill, steep forehead; 57 cm, wings 1 m across): standing, side view; hopping, side view; flying, from below.
Row 4: a shrine pigeon, as at Tsurugaoka Hachimangu (blue-grey, two black wing bars, a green and purple sheen on the
neck; 32 cm, wings 65 cm across): standing, side view; pecking, side view; flying, from below. A Eurasian tree sparrow
(chestnut cap, a black spot on a white cheek, black bib; 14 cm): perched, side view; hopping, side view; flying, from
below.
Row 5: a barn swallow, back for the summer (glossy blue-black back, red throat and forehead, cream belly, long tail
streamers; 18 cm): perched, side view; flying, from below. A black-tailed gull (white head and body, dark grey back, a
black band across its white tail, a yellow bill with a red and black tip, yellow legs; 46 cm, wings 1.2 m across):
standing, side view; flying, from below. A little egret (all white, black bill and legs, yellow feet, two long plumes
on the nape; 60 cm, wings 95 cm across): standing, side view; flying, from below.
No people, no labels, no text.
```

#### Kamakura map

Added once all 17 of Kamakura's images were in (`review/kamakura/refs`). In Gemini, with Nano Banana Pro, attach these
seven: KM-0 (the look target), KM1-1 (home), KM1-4 (the school), KM2-1, KM2-5, KM3-1 and KM3-3. Send the plan, then the
clean map.

```text
MAP KM-MAP1, the plan. You are the lead game architect and level designer of a side-scrolling soccer game for phones: a
kid dribbles a football from home to school through Kamakura, Japan. Design Kamakura's school-run map: one picture of the
town seen from directly above, with every route from the kid's home to the school on real streets. The seven images I
attached are Kamakura's reference pictures for the same game: the map must look like the same place, with the same
buildings, materials, plants, colours and light. Ignore the sparkle mark in their corners.

THE TOWN (north at the top)
- The sea and Yuigahama beach along the south edge, with the coast road behind the sand; wooded hills with temple roofs
  across the north and the west; the town between them, a close grid of narrow lanes.
- HOME in Hase, in the south-west, between the tram line and the coast road: the kid's two-storey dark-timber house from
  the first level picture (the persimmon tree, the potted plants, the bicycle, the cat on the block wall).
- SCHOOL in the north-east, beside the great shrine at the head of the long avenue Wakamiya-oji: the white concrete school
  with the clock from the second level picture, its sandy sports ground behind a green fence, the cherry tree by its gate.
- The single-track tram (green and cream) runs from Hase east to Kamakura Station between the houses, crossing the lanes
  at level crossings with black-and-yellow bars.

THE ROUTES
- Every route starts at the same front door (HOME) and ends at the same school gate (SCHOOL).
- Shared at both ends, like a real school run. The first 5 to 15% of every route is the home stem: the same narrow lane
  from the front door to the corner with the two vending machines and the convex mirror. The last 5 to 15% is the school
  approach: the same short way from the shrine's great red gate past the arched stone bridge and the lotus pond to the
  school gate. The middle 70 to 90% of each route is its own: the routes fan out from the vending-machine corner, never
  share a street in their middles (crossing at a junction or a level crossing is fine), and meet again only at the
  shrine's great red gate.
- Each route follows real streets, lanes, footpaths, steps and crossings; route 1 rides the tram between two stations.
- The stops along each route, in order (each level ends at one stop, and the next level starts there):
  Route 1, the tram (4 levels): 1-1 Hase Station, the tram's little platform east of home, past a small shrine gate and a
  level crossing. 1-2 Kamakura Station, the end of the line: ride the tram east through Yuigahama and Wadazuka stations.
  1-3 the top of Komachi-dori, the narrow shopping street running north from the station to the shrine's great red gate.
  1-4 SCHOOL, along the school approach.
  Route 2, the coast (5 levels): 2-1 the boardwalk, down a lane of surf shops and under the coast road through a short
  pedestrian tunnel. 2-2 Grandma's whitebait shop on the beach road, after a walk east along the sand past the fishing
  boats and the lifeguard tower (2-3 is played at the shop). 2-4 the first great torii at the foot of Wakamiya-oji, past
  low rock shelves and steps at the beach's eastern end. 2-5 SCHOOL, north up Wakamiya-oji's raised footpath between stone
  lanterns and cherry trees to the shrine's great red gate, then the school approach.
  Route 3, the temple hills (3 levels): 3-1 the trail head, up a temple's stone steps between banks of hydrangeas,
  north-west of home. 3-2 Genjiyama park, along the wooded ridge trail: a wooden footbridge over a gully, a cave tomb cut
  in the cliff. 3-3 SCHOOL, down through the bamboo grove past the temple bell tower and the stone steps to the shrine's
  great red gate, then the school approach.
- Real distances: a walking leg 150 to 400 m, the tram ride about 2 km. The whole map covers about 3 km from west to
  east.

THE LOOK
- A straight-down aerial view of the town, looking directly down from high above: grey kawara-tiled roofs, treetops,
  lanes with their white edge lines and green walking strips, crossings, the tram track, shrine and temple roofs among the
  trees, the beach and its surf. No tilt, no perspective.
- In the painted style of the six level pictures: a detailed, hand-painted anime background, with clean shapes, crisp
  edges and rich, true colours. In the look target's light: a clear May morning with the sun low in the east, soft
  shadows all falling west, a little haze over the sea.
- Streets readable at a glance, block by block, as on a well-made game's world map. Do not imitate any specific game.
- No people. No text, labels, logos or watermarks of your own.
- Everything the routes need lies inside the central three-quarters of the picture; the edges are more of the town, the
  hills and the sea, not a border or a frame.

FIRST, THE PLAN: draw the routes on the map as a key. Each route a thick coloured line (route 1 red, route 2 blue, route 3
yellow), dashed where it rides the tram; HOME a white house symbol; SCHOOL a white flag; each stop a white circle with its
number (1-1, 1-2 and so on). Where routes share the home stem and the school approach, run their lines side by side.

FORMAT: aspect ratio 16:9, the largest size you can make.
```

```text
MAP KM-MAP2, the clean map. Now make exactly the same map again with every line, symbol, number and label removed: only
the town seen from above. Change nothing else: the same streets, buildings, trees, water and light. FORMAT: aspect ratio
16:9, the largest size you can make.
```

## Florida (Miami), USA

### The Florida block (paste right after the base prompt)

```text
CITY: MIAMI, FLORIDA, USA
The old neighbourhoods of Miami near the river and the bay: Cuban Little Havana, the working Miami River with its
drawbridges, the glass towers of Brickell, downtown by Biscayne Bay. It must read as Miami at first glance: not Los
Angeles, not the Caribbean, not the Gulf coast.

BUILDINGS
- Homes: single-storey 1950s concrete-block ranch houses in pastel stucco (seafoam, coral, flamingo pink, butter
  yellow), low hip roofs of white concrete tile or barrel tile, jalousie and awning windows, iron window grilles, chain-link
  or iron fences, carports, terrazzo steps, a Virgen-blue door here and there.
- Little Havana: one- and two-storey shops with walk-up cafe windows, hand-painted signs in Spanish and English, striped
  awnings, murals on side walls, a small park with domino tables under a pergola.
- The river: working docks of timber and concrete, fishing boats and small freighters, bascule drawbridges with operator
  towers, mangroves on the banks, bollards and coiled lines.
- Brickell and downtown: glass and concrete residential towers with balconies, construction cranes, Mediterranean Revival
  and Art Deco older buildings, arcades and covered walkways, an elevated railway on concrete piers.
- Built for the weather: accordion and roll-down storm shutters, impact glass, gutters, drainage grates.
- Lived in: wall AC units dripping, exposed conduit, meters, satellite dishes, garden hoses, plastic chairs.

WEATHERING
Sun-bleached paint and awnings, black mildew on shaded walls, rust streaks from fixings, hard-water stains, cracked
sidewalks lifted by tree roots, salt-crusted metal by the water, peeling murals.

PLANTS
Royal palms, coconut palms leaning, sabal palms, huge banyan trees with aerial roots, mango and avocado trees in yards,
sea grape, bougainvillea, hibiscus, crotons, bird of paradise, coarse St. Augustine lawns with sandy patches.

STREET
Concrete sidewalks with expansion joints, brick-paver crosswalks, span-wire and mast-arm traffic signals, wooden and
concrete utility poles with heavy overhead wires, bus stops with benches and shelters, newspaper boxes, fire hydrants,
rental scooters, bike racks, school-zone signs with flashing beacons, iguanas on seawalls (only when a shot asks).

VEHICLES (parked and empty)
A city bus in an invented livery, a yellow school bus, a fishing boat, a tugboat, pickup trucks, old sedans, golf carts.

LIGHT AND CLIMATE
A hot, humid late-August morning, about 7:50. The sun 30 degrees up, low in the east, to the left and slightly behind the
camera. Direct sun about 5,000 K: warm. Shade about 8,500 K: a teal-blue. Humid air: a pale, milky horizon under a deep
blue zenith, a warm glow round the sun, towering cumulus. The pavement is still damp from a night shower in places, with
puddles mirroring the sky. Pastels glow in the low sun.
```

### Florida shots

```text
LOOK TARGET FL-0, Miami in its light. Follow the base prompt and the Florida block, but the camera is free.
A wide cinematic view across Biscayne Bay at morning: a causeway bridge on concrete piers, a small sandy beach with
palms and folded umbrellas in the foreground, turquoise water with boat wakes, a marina, and downtown's towers and cranes
standing in the humid haze, cumulus building over the city. No people. This picture sets the light and colour of every
Florida image.
```

#### FL1 Calle Ocho Bus

```text
LEVEL FL1-1, Little Havana Morning: home to the bus stop. Follow the base prompt and the Florida block.
Left: the kid's home, a seafoam-green 1950s ranch house with a red door, a chain-link fence, a mango tree, a lawn sprinkler,
a carport with a parked, empty old sedan, a rooster and two hens in the yard (the only animals). Then a side street of
pastel ranch houses with iron grilles, a corner with a walk-up cafe window (an invented name, hand-painted), a mural on a
side wall, a fruit cart with mangoes under an umbrella, a small park with domino tables under a pergola. Right: a bus stop
on the main street, a bench, a shelter, a route sign.
```

```text
LEVEL FL1-2, The Metrobus (mini-game set). Follow the base prompt and the Florida block, but the camera is inside.
Inside a city bus, seen straight across the aisle, side-on to the far row of windows: blue plastic seats, yellow grab
bars and a pull cord running along the windows, a next-stop LED display, a route map with invented stop names, a ticket
reader by the front door at the left, the street passing in the windows (palms, pastel shops, a tower). Warm sun slanting
in. Empty: no driver, no passengers.
```

```text
LEVEL FL1-3, Brickell Avenue: the towers to the river. Follow the base prompt and the Florida block.
Left: a bus stop at the foot of a glass condo tower with a palm-lined valet loop. Then a wide avenue sidewalk under glass
and concrete towers, a construction site behind printed mesh fencing with a tower crane above, three rental scooters left
across the sidewalk, a coffee kiosk, royal palms in tree grates. Right: the Miami River and a bascule drawbridge with its
operator's tower, gates and warning lights; a tug moored below.
```

```text
LEVEL FL1-4, Bayfront to School. Follow the base prompt and the Florida block.
Left: the drawbridge's far end. Then a bayfront promenade: royal palms in rows, wooden posts with pelicans on them (the
only animals), a fountain plaza with jets, the turquoise bay and a moored cruise ship far across the water. Right: the
school: a cream-and-teal concrete school with covered walkways on metal posts, a palm-lined bus loop with a parked, empty
yellow school bus, an aluminium picket fence and gate, a school-zone sign with flashing beacons, a crossing guard's
painted crosswalk.
```

#### FL2 The River Way

```text
LEVEL FL2-1, Riverside Street: home to the river. Follow the base prompt and the Florida block.
Left: the same home as FL1-1 from its side. Then a street of pastel ranch houses running down to the river, a seawall
with green iguanas sunning on it (the only animals), a lawn sprinkler mid-spray, a parked golf cart, mangroves, a "No
Wake" sign. Right: a small timber dock with a cleat at its edge, an empty berth.
```

```text
LEVEL FL2-2, Uncle Rey's Boat (mini-game set). Follow the base prompt and the Florida block.
A working dock on the Miami River seen side-on: a weathered white fishing boat with a blue hull stripe, outriggers and a
small cabin, drifting a metre off the dock; two steel cleats on the dock's edge, a coiled mooring line on the boat's
bow, fenders hanging, crates and a cooler on deck, and on the cabin roof a big school science project: a model of the
Everglades on a board. Mangroves and another dock behind. No people on board.
```

```text
LEVEL FL2-3, The Riverwalk: under the bridges. Follow the base prompt and the Florida block.
A concrete-and-timber riverwalk along the Miami River, side-on: three bascule drawbridges crossing overhead in turn,
the nearest with its leaves partly raised; bollards and coiled lines; crates; moored small freighters with rust streaks;
a tugboat; towers behind; railings along the water's edge. The play lane is the riverwalk.
```

```text
LEVEL FL2-4, The Drugstore (mini-game set). Follow the base prompt and the Florida block, but the camera is inside.
Inside a small corner drugstore, straight-on to one long aisle of shelves: poster boards in white and colours, glue
sticks, packs of markers, rulers, notebooks, snacks; price tags in dollars; and at the right end a counter with a till and
a card reader. Fluorescent light with warm sun from the door. Invented brand-free packaging. Nobody at all.
```

```text
LEVEL FL2-5, Downpour to School. Follow the base prompt and the Florida block, with this light: a sudden tropical
cloudburst. Dark blue-grey storm cloud overhead, heavy rain streaks, sheets of water on the street, gutters overflowing,
light about 6,500 K and flat, a bright break of sun at the far right with steam rising.
Left: downtown's older street: Art Deco and Mediterranean Revival buildings with deep arcades and canvas awnings, a
flooded crosswalk, rain pouring off awning edges in sheets, a bus shelter. Right: the storm breaking, wet palms shining,
the school's covered walkway and gate (the school from FL1-4).
```

#### FL3 Under the Line

```text
LEVEL FL3-1, The Underline: home to the station. Follow the base prompt and the Florida block.
A linear park under an elevated railway on round concrete piers, side-on: the piers painted with original murals
(abstract tropical flowers, waves, birds; invented art, no faces, no lettering), a paved path with a painted bike lane
beside it, fitness equipment, a fenced dog run, native planting and palms, the guideway's shadow across the path with sun
between. Right: a station's stairs and escalator up to the elevated platform.
```

```text
LEVEL FL3-2, Biscayne Boulevard. Follow the base prompt and the Florida block.
A wide boulevard sidewalk, side-on: a median of royal palms, an old Spanish-style tower with a cupola (invented, not a
real building) behind palms, modern towers behind it, pelicans on lamp posts (the only animals), a parked street sweeper
truck, bus shelters, the elevated people-mover's track crossing above on slim piers.
```

```text
LEVEL FL3-3, Museum Park to School. Follow the base prompt and the Florida block.
A bayside park, side-on: two huge banyan trees whose aerial roots form arches and low steps, a lawn with sprinklers,
skateboard ledges, a kite-flier's kite tied to a bench (no person), the bay behind. Right: the school (as FL1-4).
```

#### Florida sheets and plates

```text
SHEET FL-P1, Miami street props and vehicles. Follow the base prompt's content rules, but ignore its camera and light.
On a plain mid-grey background, each object apart, front and three-quarter views, same scale, even soft studio light: a
span-wire traffic signal, a mast-arm signal, a wooden utility pole top with transformer, a bus shelter and bench, a
newspaper box, a fire hydrant, a rental scooter, a bike rack, a walk-up cafe window with its ledge, a domino table with
stools, a fruit cart with umbrella, a mooring cleat and bollard, a coiled line, a bascule bridge gate arm, a school-zone
beacon sign, a golf cart, a city bus in an invented livery. No labels.
```

```text
SHEET FL-P2, Miami plants and animals. Follow the base prompt's content rules, but ignore its camera and light.
On a plain mid-grey background, from the side, same scale, with a 1.8 m grey pole for scale (not a person): a royal palm,
a leaning coconut palm, a sabal palm, a young banyan with aerial roots, a mango tree, sea grape, bougainvillea, hibiscus,
crotons, bird of paradise, mangrove shrubs; and a green iguana, a rooster, a hen and a brown pelican. No labels.
```

```text
PLATE FL-P3, Miami texture plates. Ignore the base prompt's camera and light.
Six square plates in a grid, flat and straight-on, in flat, shadowless overcast light, true colours with weathering:
pastel stucco with mildew, white concrete roof tile, a jalousie window with iron grille, a painted mural wall (abstract,
invented), weathered dock timber, sidewalk concrete with expansion joints and a root crack. No text.
```

## Madrid, Spain

### The Madrid block (paste right after the base prompt)

```text
CITY: MADRID, SPAIN
The old centre of Madrid: Lavapies, La Latina, the Plaza Mayor, the Paseo del Prado and El Retiro park. It must read as
Madrid at first glance: not Barcelona, not Seville, not Paris.

BUILDINGS
- Four- to six-storey 19th-century apartment buildings, facades in ochre, terracotta, salmon, cream and pale grey
  render, tall windows with wrought-iron balconies (geraniums in pots, laundry on lines, rolled green blinds), green or
  brown wooden shutters, carved stone door surrounds, big wooden street doors with brass knockers, slate and zinc mansard
  roofs with dormers, chimneys and TV aerials.
- Ground floors: bars and small shops with roll-down metal shutters (some covered in graffiti tags, invented and
  illegible), ceramic tile shop signs, painted wooden fronts, a pharmacy cross.
- Arcaded squares with granite columns, red-brick neo-Mudejar buildings, iron-and-glass Victorian halls, wooden kiosks.
- Lived in: AC units on balconies, satellite dishes, cables along facades, scaffolding with green mesh on one facade.

WEATHERING
Render patched in two shades, soot over doorways, pigeon-stained cornices, rust drips from balcony brackets, worn granite
kerbs, cobbles polished by feet, peeling posters on hoardings.

PLANTS
London plane trees with mottled bark (leaves going yellow-brown), horse chestnuts, Mediterranean stone pines, cypresses,
clipped box hedges and rose beds in the park, geraniums on every balcony.

STREET
Granite kerbs, grey stone setts and small cobbles in the old lanes, wide pavements of square grey slabs, black iron
bollards, green park benches, cast-iron street lamps on wall brackets, blue street-name plaques of glazed tile with
pictures, a Metro entrance with a red diamond-shaped sign (invented name), bus stops with glass shelters, a newspaper kiosk.

VEHICLES (parked and empty)
A blue city bus in an invented livery, a street-cleaning truck with water hoses, a delivery van, small cars, a scooter.

LIGHT AND CLIMATE
A dry, bright early-October morning at about 8:30, just after the late sunrise. The sun is only 12 degrees up, low in
the east, to the left: long golden shafts down the streets and long shadows across them. Direct sun about 4,200 K:
golden. Shade about 9,500 K: a clear blue. Very dry high-plateau air: almost no haze, crisp edges into the distance, a
deep saturated blue sky with a few high cirrus. The cobbles are wet in places from the street-cleaning hoses.
```

### Madrid shots

```text
LOOK TARGET MD-0, Madrid in its light. Follow the base prompt and the Madrid block, but the camera is free.
A wide cinematic view from a rooftop terrace across Madrid's old centre at sunrise: terracotta roofs, dormers and
chimneys, church domes and towers catching the low golden sun, long shadows in the streets below, a crane, the deep blue
dry sky, the far mountains faint and blue. No people. This picture sets the light and colour of every Madrid image.
```

#### MD1 The Metro

```text
LEVEL MD1-1, Lavapies Morning: home to the Metro. Follow the base prompt and the Madrid block.
Left: the kid's home, a five-storey ochre apartment building with iron balconies, geraniums, laundry, green shutters, a
big wooden street door, a ground-floor bar with its metal shutter half up. Then a sloping cobbled street: a
street-cleaning truck parked with its hose laid out and a wet sheen on the cobbles, a fruit shop with crates on the
pavement, a facade under scaffolding with green mesh and a covered walkway, a small plaza with benches and a plane tree.
Right: a Metro entrance, stairs going down under a red diamond sign (invented station name).
```

```text
LEVEL MD1-2, Change at Sol (mini-game set). Follow the base prompt and the Madrid block, but the camera is inside.
Inside a Metro station, side-on: a long tiled corridor with a junction, coloured line signs (a yellow line 3 and a red
line 2 with arrows and invented end-station names), then a platform with a curved tiled vault, a train at the platform
with doors open (an invented livery), a platform screen showing minutes to the next train, a ticket gate with a card
reader at the left. Cool fluorescent light. Nobody at all.
```

```text
LEVEL MD1-3, El Retiro: through the park. Follow the base prompt and the Madrid block.
Left: the park's iron gate with stone piers. Then a wide gravel avenue under horse chestnuts and plane trees, fallen
leaves in drifts, the lake behind a stone balustrade with blue rowing boats tied in a row, a striped puppet theatre booth,
a chestnut roaster's small kiosk with a chimney, green benches, a stone fountain. Low golden sun through the trees.
```

```text
LEVEL MD1-4, To School by the Lime Trees. Follow the base prompt and the Madrid block.
Left: the park's east gate. Then a street of apartment buildings, a crossing with a traffic light and a raised island,
a newspaper kiosk, lime trees in tree pits. Right: the school: a three-storey red-brick school with tall white-framed
windows, a tiled name plaque (invented), a walled playground with a football cage, a gate with lime trees.
```

#### MD2 Tia Carmen

```text
LEVEL MD2-1, To La Latina. Follow the base prompt and the Madrid block.
Left: the same home as MD1-1 from a side street. Then a steep, narrow lane of old taverns with carved wooden fronts and
their shutters down, tiled signs (invented), a delivery van unloading crates of bread, iron bollards, the dome of a
large church at the lane's end. Right: Tia Carmen's building (next shot) with a third-floor balcony.
```

```text
LEVEL MD2-2, The Basket (mini-game set). Follow the base prompt and the Madrid block.
A salmon-pink apartment building straight on, five storeys: on the third-floor iron balcony, flower pots and a wicker
basket hanging from a long rope tied to the railing, reaching halfway down the facade, swaying. In the basket a paper bag
and a school folder. Below, a narrow pavement of granite slabs, freshly wet, a big wooden street door, a bar's shutter.
Nobody on the balcony or in the street.
```

```text
LEVEL MD2-3, Plaza Mayor. Follow the base prompt and the Madrid block.
Through an arched passage into a vast arcaded square, side-on along one side: arcades on granite columns with cafe
terraces under them (chairs and tables stacked, parasols closed), the facades above in deep red-brown with rows of
iron balconies, one facade painted with bright allegorical murals (invented, no faces in detail), cobbles, pigeons on the
ground (the only animals), lamp posts. The play lane runs under the arcade.
```

```text
LEVEL MD2-4, The Papeleria (mini-game set). Follow the base prompt and the Madrid block, but the camera is inside.
Inside a small old stationery shop, straight on: wooden shelves to the ceiling with rolls of coloured poster card, boxes
of coloured pencils, compasses and rulers on hooks, notebooks, folders, a glass counter with a till and a card reader at
the right, prices in euros, a hand-written sign. Warm light. Nobody at all.
```

```text
LEVEL MD2-5, Paseo del Prado to School. Follow the base prompt and the Madrid block.
Left: a broad boulevard's central walk under rows of plane trees, the iron railings of a botanic garden, a great marble
fountain on a roundabout (invented, a sea god and horses, unnamed) with a traffic island crossing. Then up a street
beside the park's iron fence. Right: the school (as MD1-4).
```

#### MD3 The Book Hill

```text
LEVEL MD3-1, The Atocha Roundabout. Follow the base prompt and the Madrid block.
Left: the home street's corner. Then an old railway station's great iron-and-glass hall with tall palms visible inside
through the glass (invented, unnamed), a wide roundabout with crossings, traffic islands and lights, a bus stop. Right:
the foot of a steep street lined with small wooden stalls.
```

```text
LEVEL MD3-2, Cuesta de Moyano: the hill of book stalls. Follow the base prompt and the Madrid block.
A steep street climbing from left to right (about one in eight), side-on: a row of small wooden book stalls painted grey,
their hinged shutters open as counters with second-hand books in rows, a park railing behind them with trees above, a
statue of a writer (invented, unnamed) on a plinth, leaves blowing down the slope.
```

```text
LEVEL MD3-3, The Rose Garden to School. Follow the base prompt and the Madrid block.
Left: a park's rose garden with iron arches, clipped box hedges and a round pond with a small fountain. Then a gravel path,
a chestnut roaster's kiosk with smoke, a park gate. Right: the school (as MD1-4).
```

#### Madrid sheets and plates

```text
SHEET MD-P1, Madrid street props and vehicles. Follow the base prompt's content rules, but ignore its camera and light.
On a plain mid-grey background, each object apart, front and three-quarter views, same scale, even soft studio light: a
wrought-iron balcony with geraniums, a roll-down shop shutter, a wall-bracket street lamp, a black iron bollard, a green
park bench, a tiled street-name plaque, a newspaper kiosk, a Metro entrance sign, a glass bus shelter, a street-cleaning
truck with hoses, a blue city bus in an invented livery, a delivery van, a chestnut roaster's kiosk, a puppet theatre
booth, a wooden book stall, a wicker basket on a rope. No labels.
```

```text
SHEET MD-P2, Madrid plants. Follow the base prompt's content rules, but ignore its camera and light.
On a plain mid-grey background, from the side, same scale, with a 1.8 m grey pole for scale (not a person): a London plane
tree in autumn, a horse chestnut, a stone pine, a cypress, a lime tree, a clipped box hedge, a rose bed, pots of geraniums;
and a pigeon. No labels.
```

```text
PLATE MD-P3, Madrid texture plates. Ignore the base prompt's camera and light.
Six square plates in a grid, flat and straight-on, in flat, shadowless overcast light, true colours with weathering:
ochre render patched in two shades, terracotta render, granite setts, square grey pavement slabs, a green wooden shutter,
a slate-and-zinc mansard roof. No text.
```

## New York, USA

### The New York block (paste right after the base prompt)

```text
CITY: NEW YORK CITY, USA
Brooklyn Heights, DUMBO and Lower Manhattan (City Hall, Tribeca, the Financial District) in late October. It must read
as New York at first glance: not Boston, not Chicago, not London.

BUILDINGS
- Brooklyn: four-storey brownstone row houses with high stoops and cast-iron railings, carved lintels, tall parlour
  windows, cornices; red-brick row houses; cellar doors of diamond-plate steel set in the sidewalk; Halloween decorations
  on stoops (pumpkins, gourds, cobwebs, a cardboard skeleton).
- DUMBO and Tribeca: brick and cast-iron warehouses, loading docks with steel canopies, fire escapes, painted ghost
  signs (invented), cobbled streets with old rail tracks.
- Lower Manhattan: stone and glass towers, granite plazas, old churches with graveyards, security bollards and planters.
- Lived in: scaffolding sidewalk sheds of green plywood and steel, black garbage bags piled at the kerb, AC units in
  windows, water towers on rooftops, intercom panels, standpipes.

WEATHERING
Sooty brick, efflorescence, rust on fire escapes, chewing-gum spots on sidewalks, cracked slate sidewalks, layers of old
paint on railings, steam stains, flyers on lamp posts.

PLANTS
London plane trees and honey locusts on the sidewalks, ginkgos turning bright gold, small trees in tree pits with low iron
guards, ivy on brick, potted mums on stoops.

STREET
Grey concrete and bluestone sidewalks, granite kerbs, subway entrances with green globe lamps and railings, newsstands,
green street-name signs on poles, WALK and DON'T WALK pedestrian signals with countdowns, fire hydrants, mailboxes,
striped orange-and-white steam chimneys from street repairs, steam rising from manholes, bike-share docks.

VEHICLES (parked and empty)
Yellow taxis, a subway train in an invented livery, a commuter ferry, a food cart (pretzels and coffee), a delivery truck.

LIGHT AND CLIMATE
A cold, clear late-October morning at about 7:50. The sun is 15 degrees up, low in the east, to the left: it rakes down
the cross streets in long golden shafts, while the avenues and narrow streets lie in deep blue shade. Direct sun about
4,000 K: golden. Shade about 10,000 K: deep blue. Crisp air with a light haze over the river, steam rising white and
glowing where the sun catches it. A clear pale-to-deep blue sky.
```

### New York shots

```text
LOOK TARGET NY-0, New York in its light. Follow the base prompt and the New York block, but the camera is free.
A wide cinematic view from the Brooklyn waterfront across the East River at sunrise: the stone towers and cables of a
great suspension bridge, the Lower Manhattan skyline catching low golden light on one side and deep blue shade on the
other, a commuter ferry crossing with its wake, steam from rooftops, autumn trees along the promenade. No people. This
picture sets the light and colour of every New York image.
```

#### NY1 The Brooklyn Bridge

```text
LEVEL NY1-1, Brownstone Stoops: home to the bridge. Follow the base prompt and the New York block.
Left: the kid's home, a brownstone with a high stoop, pumpkins and a cardboard skeleton on the steps, cast-iron railings,
a ginkgo turning gold, a steel cellar door in the sidewalk, open. Then a row of brownstones and brick houses, black garbage
bags piled at the kerb, a scaffolding sidewalk shed over one house, a fire hydrant, parked empty cars. Right: the stair up to
the bridge's pedestrian ramp.
```

```text
LEVEL NY1-2, The Bridge: across the East River. Follow the base prompt and the New York block.
On the bridge's elevated wooden-plank promenade, side-on: the plank walkway (the play lane) with an iron railing, a painted
bike lane beside it, a massive granite tower with two pointed arches, steel cables fanning in a web overhead, the river far
below, the Manhattan skyline ahead on the right in low golden light, lamp posts, a "keep right" sign.
```

```text
LEVEL NY1-3, Uncle Sal's Cart (mini-game set). Follow the base prompt and the New York block.
At the edge of a city park by a granite plaza, straight on: a stainless-steel food cart with a striped umbrella, pretzels
on hooks, coffee urns, a bagel bin, a menu board in dollars (invented name), napkins, a tip cup. Behind, the park's iron
fence and trees. Nobody at the cart.
```

```text
LEVEL NY1-4, City Hall Park to School. Follow the base prompt and the New York block.
Left: a city park: a round fountain with gas-style lamps, benches, plane trees with squirrels (the only animals), an iron
fence. Then a street with a WALK signal and countdown. Right: the school: a five-storey red-brick and limestone public
school with a fenced rooftop yard, a playground behind a fence, a carved name above the door (invented: "P.S. 412").
```

#### NY2 The Subway

```text
LEVEL NY2-1, Court Street: home to Borough Hall. Follow the base prompt and the New York block.
Left: the corner of the home's brownstone street. Then a busier street: a halal food cart (closed), a newsstand, a striped
steam chimney over a street repair with barriers, a crosswalk with its countdown signal, plane trees. Right: a subway
entrance's stairs with green globe lamps and railings.
```

```text
LEVEL NY2-2, Express or Local (mini-game set). Follow the base prompt and the New York block, but the camera is inside.
A subway platform side-on: a tiled wall with mosaic station name (invented), steel columns painted, an LED arrival board
listing an express and a local train with minutes, a train at the platform with doors open (stainless steel, invented
livery), and through its windows its interior: poles, seats, a route map. Turnstiles at the left. Nobody at all.
```

```text
LEVEL NY2-3, Tribeca Cobbles. Follow the base prompt and the New York block.
A cobbled street of brick and cast-iron warehouses, side-on: loading docks a metre high with steel canopies over them (the
dock tops are raised walkways), fire escapes, a painted ghost sign (invented), steam rising from a manhole, a film crew's
equipment cases stacked on the kerb (no people), low golden light down a cross street.
```

```text
LEVEL NY2-4, The Art Store (mini-game set). Follow the base prompt and the New York block, but the camera is inside.
Inside an art-supply store, straight on to one aisle: canvas boards in sizes, tubes and jars of acrylic paint in colour
order, brushes in pots, sketchbooks, a counter with a till and card reader at the right, price tags in dollars, a "sales
tax" note by the till. Nobody at all.
```

```text
LEVEL NY2-5, Hudson River Park to School. Follow the base prompt and the New York block.
A riverside greenway, side-on: a path with a bike lane, piers reaching into the river, a small skate park, lawns with
autumn trees, wind off the water, the river and New Jersey's shore behind. Right: the school (as NY1-4).
```

#### NY3 The Ferry

```text
LEVEL NY3-1, DUMBO Cobbles: home to the ferry. Follow the base prompt and the New York block.
Left: the corner of the home's street. Then cobbled streets with old rail tracks set in them, brick warehouses, the steel
underside of a great bridge crossing high overhead, a carousel in a glass pavilion by the water. Right: a ferry landing with
a gangway and a covered waiting deck.
```

```text
LEVEL NY3-2, The Wall Street Pier. Follow the base prompt and the New York block.
A ferry pier, side-on: the gangway, a covered pier shed, bollards, an elevated highway's concrete deck overhead casting a
long shadow, then a narrow cobbled lane of old low buildings with taverns' signs (invented).
```

```text
LEVEL NY3-3, The Financial District to School. Follow the base prompt and the New York block.
A narrow street between stone and glass towers in deep blue shade with one golden shaft of sun, security bollards and
granite planters, an old church's graveyard behind iron railings, a subway grate. Right: north to the school (as NY1-4).
```

#### New York sheets and plates

```text
SHEET NY-P1, New York street props and vehicles. Follow the base prompt's content rules, but ignore its camera and light.
On a plain mid-grey background, each object apart, front and three-quarter views, same scale, even soft studio light: a
stoop with cast-iron railings, a steel cellar door (open and shut), a scaffolding sidewalk shed bay, a pile of garbage
bags, a fire hydrant, a subway entrance with globe lamps, a newsstand, a WALK signal on its pole, a green street-name sign,
a striped steam chimney, a manhole with steam, a bike-share dock, a food cart, a security bollard and planter, a yellow
taxi, a commuter ferry. No labels.
```

```text
SHEET NY-P2, New York plants and animals. Follow the base prompt's content rules, but ignore its camera and light.
On a plain mid-grey background, from the side, same scale, with a 1.8 m grey pole for scale (not a person): a London plane
tree, a honey locust, a ginkgo in gold, a tree pit with an iron guard, ivy on a brick panel, potted mums, pumpkins and
gourds; and a grey squirrel, a pigeon and six different dogs on leashes held by a hook (no person). No labels.
```

```text
PLATE NY-P3, New York texture plates. Ignore the base prompt's camera and light.
Six square plates in a grid, flat and straight-on, in flat, shadowless overcast light, true colours with weathering:
brownstone, sooty red brick, painted cast-iron facade, bluestone sidewalk, granite cobbles, a rusty fire escape. No text.
```

## Mumbai, India

### The Mumbai block (paste right after the base prompt)

```text
CITY: MUMBAI, INDIA
South Mumbai in the monsoon: Girgaon's old lanes, Girgaon Chowpatty and Marine Drive, Churchgate, the cricket grounds of
the Fort, Kala Ghoda and the old market. It must read as Mumbai at first glance: not Delhi, not Kolkata, not a generic
"Indian street".

BUILDINGS
- Girgaon: old two-storey wooden houses with carved verandahs, painted balconies and tiled roofs (a heritage village of
  the old city), and three- to five-storey chawls with long open galleries, painted in faded blue, pink, green and cream.
- Marine Drive: a long curve of four- to six-storey Art Deco apartment buildings in cream and pastel, rounded corners,
  sunshades, decorative railings.
- The Fort: Victorian Gothic stone buildings with arcaded ground floors, pointed arches, carved stone, clock towers.
- Shops: small open-fronted shops with roll-down shutters, painted and printed signs in Marathi, Hindi and English
  (invented names), awnings of blue tarpaulin, glass jars and hanging goods.
- Lived in: blue and orange tarpaulins over roofs and balconies for the rain, AC units, tangled cables, water tanks on
  roofs, potted tulsi, scooters under covers, laundry on lines, painted rangoli at doorsteps.

WEATHERING
Black monsoon staining down every wall, green moss and ferns in cracks, peeling paint in layers, rusted grilles and
shutters, rain-darkened stone, water pooling everywhere.

PLANTS
Coconut palms, banyan and peepal trees with roots on walls, gulmohar trees, rain trees, bougainvillea, potted tulsi,
marigold garlands, moss and ferns on walls.

STREET
Uneven paver-block footpaths with high kerbs painted black and yellow, open gutters with grates, puddles, handcarts,
black-and-yellow taxis, bus stops with shelters and route boards, cricket nets, traffic police umbrellas on stands, chai
stalls, cobbler's stools, footbridges over railway tracks.

VEHICLES (parked and empty)
Black-and-yellow taxis, a red double-decker bus (invented livery), a local train in an invented livery with open doors,
handcarts loaded with sacks, scooters, a sweet-corn roaster's cart.

LIGHT AND CLIMATE
The monsoon, in July, at about 11:15 in the morning. A low, thick grey cloud over everything, dark rain bands over the sea.
Soft overcast light about 6,800 K, no hard shadows, gentle shading under eaves and arcades. Everything wet: shining
streets, puddles mirroring the grey-white sky, dripping eaves, a light drizzle, sea mist softening the distance. Greens
are deep and saturated, painted walls glow against the grey.
```

### Mumbai shots

```text
LOOK TARGET MB-0, Mumbai in its light. Follow the base prompt and the Mumbai block, but the camera is free.
A wide cinematic view along Marine Drive's curving sea wall in the monsoon: waves bursting over the wall in white spray,
tetrapods below, the wet promenade shining, the curve of Art Deco buildings fading into sea mist, dark rain bands over a
grey-green sea, palms bending. No people. This picture sets the light and colour of every Mumbai image.
```

#### MB1 Marine Drive

```text
LEVEL MB1-1, Wadi Lanes and Chowpatty: home to the beach. Follow the base prompt and the Mumbai block.
Left: the kid's home, an old two-storey wooden house with a carved verandah, a painted balcony, a tiled roof under a blue
tarpaulin, potted tulsi, a scooter under a cover, a cat on the step (the only animal). Then a narrow lane of such houses,
then a busy road's footpath, then a wide grey-sand city beach: closed snack carts under tarpaulins, monsoon waves, crows
on the sand.
```

```text
LEVEL MB1-2, The Sea Wall: Marine Drive. Follow the base prompt and the Mumbai block.
A wide seaside promenade seen side-on with the sea behind: a low sea wall, concrete tetrapods below it, a wave bursting
over the wall in a tall white spray in the middle of the picture, the promenade wet and shining (the play lane), lamp posts,
a sweet-corn roaster's cart with its brazier covered. Behind, across a road with black-and-yellow taxis, the curve of Art
Deco apartment buildings.
```

```text
LEVEL MB1-3, The Tiffin Sort (mini-game set). Follow the base prompt and the Mumbai block.
At the end of a busy railway terminus platform under its roof, side-on: long wooden crates on the floor and on a handcart,
filled with dozens of round steel tiffin carriers in cloth bags, each lid painted with coloured codes (invented letters,
numbers and symbols); bicycles with tiffin racks; a local train behind at the platform. Nobody at all.
```

```text
LEVEL MB1-4, Across the Maidan to School. Follow the base prompt and the Mumbai block.
A huge flat green cricket ground in the rain, side-on: several pitches with stumps set up, cricket nets, puddles on the
grass, an iron railing along the path (the play lane). Behind on the far side a row of Art Deco buildings, and on the
right a Gothic stone building with a clock tower. Right: the school: a stone Victorian building with arched verandahs, a
gate with a guard's booth, a playground of red earth.
```

#### MB2 The Local Train

```text
LEVEL MB2-1, To Charni Road: home to the station. Follow the base prompt and the Mumbai block.
Left: the corner of the home's lane. Then a busy road's footpath: a chai stall under a tarpaulin with a kettle on a
stove, a cobbler's stool under a big umbrella, two handcarts loaded with sacks, stray dogs (the only animals), puddles,
shops with roll-down shutters half up. Right: a railway footbridge's steep stairs up and over the tracks.
```

```text
LEVEL MB2-2, The Fast Local (mini-game set). Follow the base prompt and the Mumbai block.
A suburban railway platform seen side-on: a long local train at the platform with its doors wide open (no doors fitted,
as on these trains), steel grab poles at each doorway, ceiling fans and luggage racks inside, a yellow edge line on the
platform, an indicator board with an invented train and times, the platform's tin roof dripping. Nobody at all.
```

```text
LEVEL MB2-3, Churchgate Subway: the underground market. Follow the base prompt and the Mumbai block, but the camera is inside.
A wide underground pedestrian walkway, side-on: small shop stalls on both sides with bags, umbrellas, phone covers and
belts hanging from their fronts at head height, tiled floor wet from the rain, fluorescent tubes with dim stretches
between, steps rising at the right toward grey daylight.
```

```text
LEVEL MB2-4, The Stationery Shop (mini-game set). Follow the base prompt and the Mumbai block, but the camera is inside.
A small open-fronted stationery and photocopy shop, straight on: rolls of chart paper in colours, geometry boxes, glue
bottles, notebooks with brown paper covers, a photocopy machine with a "Xerox" style sign (invented name), a glass counter,
prices in rupees, a garland of marigolds over the door. Nobody at all.
```

```text
LEVEL MB2-5, Kala Ghoda to School. Follow the base prompt and the Mumbai block.
An old district of stone buildings and narrow lanes, side-on: flooded gutters and puddles across the footpath, a big
painted wall (an invented abstract mural), a stone library's portico with columns (shelter), a banyan with roots on a
wall, a taxi. Right: the school (as MB1-4).
```

#### MB3 The Red Bus (a break in the rain)

```text
LEVEL MB3-1, Girgaon Road: home to the bus stop. Follow the base prompt and the Mumbai block, with this light: a break in
the rain, bright, hazy sun about 5,600 K, steam rising from the wet street, clouds still heavy at the edges.
A busy main road's footpath, side-on: chawls with long galleries above, a festival pavilion being built of bamboo poles
and lashings, a flower seller's marigold garlands, handcarts, black-and-yellow taxis, a bus stop with a shelter and a
route board.
```

```text
LEVEL MB3-2, The Old Market. Follow the base prompt and the Mumbai block, with MB3-1's light.
A covered market's front, side-on: a Gothic market hall with a clock tower, fruit stalls with crates of mangoes, bananas
and pomegranates, porters' baskets on the ground, a handcart, pigeons (the only animals), striped awnings.
```

```text
LEVEL MB3-3, The Arcaded Road to School. Follow the base prompt and the Mumbai block, with MB3-1's light.
A road of Victorian stone buildings with a continuous arcade along the ground floor (the play lane runs under it), shops
and booksellers' stalls in the arcade, a fountain on a busy roundabout with a traffic police umbrella stand. Right: the
school (as MB1-4).
```

#### Mumbai sheets and plates

```text
SHEET MB-P1, Mumbai street props and vehicles. Follow the base prompt's content rules, but ignore its camera and light.
On a plain mid-grey background, each object apart, front and three-quarter views, same scale, even soft studio light: a
black-and-yellow taxi, a red double-decker bus (invented livery), a handcart with sacks, a chai stall, a cobbler's stool and
umbrella, a sweet-corn cart, a roll-down shop shutter, a bus stop with route board, a traffic police umbrella stand, a
black-and-yellow kerb section, a gutter grate, a stack of tiffin carriers with painted lids, a tiffin crate, cricket stumps
and a net, a bamboo scaffold frame. No labels.
```

```text
SHEET MB-P2, Mumbai plants and animals. Follow the base prompt's content rules, but ignore its camera and light.
On a plain mid-grey background, from the side, same scale, with a 1.8 m grey pole for scale (not a person): a coconut palm,
a banyan with aerial roots, a peepal tree, a gulmohar, a rain tree, bougainvillea, potted tulsi, marigold garlands, moss
and ferns on a wall panel; and a crow, a pigeon and a stray dog. No labels.
```

```text
PLATE MB-P3, Mumbai texture plates. Ignore the base prompt's camera and light.
Six square plates in a grid, flat and straight-on, in flat, shadowless overcast light, true colours with weathering:
monsoon-stained painted plaster, carved wooden verandah boards, Gothic carved basalt stone, paver-block footpath, a rusty
rolling shutter, a blue tarpaulin. No text.
```

## The map prompt (added to a city once all its images are in)

Each city's map is one picture of its neighbourhood from straight above, with every route from home to school on real
streets: the picture the game's map screen shows, with the routes, stops and level nodes drawn over it by the game
(`docs/WORLD_MAP.md`). A city's map prompt is written, and added to the end of its tab on the prompts page, **only once
the user has shared all of that city's images**. It names that city's streets, stops, home stem and school approach
(`docs/CITIES.md`), and describes the look of those images, so the map matches them.

How it is used, in Gemini (Nano Banana Pro, for its closer following of a long prompt; 16:9 at the largest size):
1. A new chat. Attach the city's look target and the first and last level of each route (seven images).
2. Send the map prompt: it asks for **the plan**, the map with the routes drawn on it as a key.
3. Send the clean-map message: the same map with every line, symbol and label taken off. That clean picture is the map
   screen's picture; the plan is kept to trace the routes, stops and level nodes into the map's layout file.
4. Save both as `review/<city>/refs/<CITY>-MAP_plan.png` and `review/<city>/refs/<CITY>-MAP_clean.png`.

The user's reference for how a top-down street map should read (roofs, treetops, road markings, crossings, block by block)
was a screenshot of another game's store art. It is not stored, and nothing of its look is copied.

The template each city's prompt is filled from (`{...}` are the city's own):

```text
You are the lead game architect and level designer of a side-scrolling soccer game for phones: a kid dribbles a football
from home to school through {CITY}. Design the city's school-run map: one picture of the neighbourhood seen from
directly above, with every route from the kid's home to the school on real streets. The images I attached are this
city's reference pictures for the same game: the map must look like the same place, with the same buildings, materials,
plants, colours and light. Ignore any watermark or sparkle mark in them.

THE ROUTES
- Every route starts at the same front door (HOME) and ends at the same school gate (SCHOOL).
- Shared at both ends, like a real school run: the first 5 to 15% of every route is the same stretch from the front door
  ({HOME_STEM}), and the last 5 to 15% is the same approach to the gate ({SCHOOL_APPROACH}). The middle 70 to 90% of each
  route is its own streets: the routes fan out from the home stem, never share a street in their middles (crossing at a
  junction is fine), and come back together only for the school approach.
- Each route follows real streets, footpaths, steps, crossings and parks, the way a child there would really walk. Where
  it rides (a tram, bus, train, metro or ferry), it boards at a real stop and gets off at another, along that line's track,
  road or water.
- The stops along each route, in order (each level ends at one stop, and the next level starts there):
{ROUTES}
- Real distances: a walking leg 150 to 400 m, a ride 1 to 3 km. The whole map covers about {SPAN}.

THE LOOK
- A straight-down aerial view, like a drone photograph taken from high above looking directly down at the
  neighbourhood: roofs, treetops, roads with their lane and crossing markings, kerbs and pavements, parked vehicles, rail
  tracks, water. No tilt, no perspective. North at the top.
- {STYLE}, like the attached images, in their light: {LIGHT}. Soft shadows, all falling the same way.
- Streets readable at a glance, block by block, as on a well-made game's world map. Do not imitate any specific game.
- No people. No text, labels, logos or watermarks of your own.
- Everything the routes need lies inside the central three-quarters of the picture; the edges are more of the city, not a
  border or a frame.

FIRST, THE PLAN: draw the routes on the map as a key. Each route a thick coloured line (route 1 red, route 2 blue, route 3
yellow), dashed where it rides; HOME a white house symbol; SCHOOL a white flag; each stop a white circle with its number
(1-1, 1-2 and so on for route 1). Where routes share a street, run their lines side by side.

FORMAT: aspect ratio 16:9, the largest size you can make.
```

The clean-map message, sent after the plan:

```text
Now make exactly the same map again with every line, symbol, number and label removed: only the city seen from above.
Change nothing else: the same streets, buildings, trees, water and light. FORMAT: aspect ratio 16:9, the largest size
you can make.
```

## Add-ons for Blender and Unity

- **Blender:** the kits are built by script with the `bpy` module (`bpy==5.2.3`, `tools/blender/README.md`). The add-ons
  that come with it cover the work: FBX and glTF export, Node Wrangler for the atlas-painting node trees, Cycles for
  baking ambient occlusion into vertex colours, UV Layout, Rigify. `tools/blender/README.md` says how to install and turn
  them on. To look at a reference next to a model: Add > Image > Reference, or File > Import > Images as Planes (built
  in). Nothing from the extensions site is needed.
- **Unity:** nothing to install. The game uses the built-in render pipeline with its own shaders (no URP or HDRP), its
  settings applied from code. Don't add URP or HDRP, Asset Store shaders, or photo-texture or photogrammetry packs: they
  would change every scene's look, break the four filters (which read the figure mask in the picture's alpha) and break
  the budgets in `docs/PERFORMANCE.md`. Don't import the reference images into `Assets/`.

The prompts and the images cost nothing in the game. What each city costs once built is in `docs/CITIES.md`, "Where we
are".
