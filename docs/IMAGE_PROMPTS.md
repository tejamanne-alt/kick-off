# Kick Off 2 School: ChatGPT Images prompts for the cities

Copy-paste prompts for the reference images each city is modelled and lit from. The cities, their routes and legs are
designed in `docs/CITIES.md`. Every level here has its own prompt, under the same id (`KM1-1` is Kamakura, route 1,
leg 1).

There are three layers, pasted in order:
1. **The base prompt:** the same for every city.
2. **The city block:** the place, its buildings, materials, plants, street, vehicles, and its own light and climate.
3. **One shot per message:** a level (its street from start to end), the city's look target, or an asset sheet.
   (Madrid's, New York's and Mumbai's prompts went with those cities in v132.)

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

## How to use them in ChatGPT

1. **One chat per city.** Start a new chat. Paste the **base prompt** and that city's **block** together as the first
   message. ChatGPT may answer with a test image or a question: say "Ready for the shots."
2. **Then one shot per message, one level at a time,** in the order listed. For the next leg of the same route, attach
   the previous leg's image: the shot says what continues.
3. Ask for the **widest landscape format** (3:2). The phone's screen is about 2.2:1, so the important things are kept in
   the middle band.
4. If the pictures drift (people creeping in, a vanishing-point street, the wrong light, brand names), paste the base
   prompt again with "Keep to these rules."
5. Save each result as `review/<city>/refs/<id>_<what>.png`, for example `review/kamakura/refs/KM1-1_hase_lanes.png`,
   outside `Assets/` so nothing reaches a build. Then ask for the city's kit to be built from them.

The order per city: the **look target** first (it fixes the light for the chat), then every level, then the sheets and
plates.

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
- Eye height about 2.5 m, about 9 m from the building fronts. A natural 35-50 mm lens, verticals vertical, no fisheye.
  The horizon a little above the middle.
- Layers from front to back: an EMPTY, continuous walking surface across the bottom fifth of the picture (the play
  lane: a sidewalk, path, boardwalk, platform or sand, flat, with nothing standing on it except at its edges), then the
  kerb or edge, the row of fronts, a back row of roofs, trees and towers, and the far skyline or hills.
- The picture reads left to right as the leg: where it starts on the left, where it ends on the right.
- Everything sharp from front to back: no depth of field, bokeh, motion blur, vignette, lens flare or film grain.
- The widest landscape format (3:2).

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

SHEETS AND PLATES
When a shot is a SHEET (objects on a plain background) or a PLATE (a flat, straight-on texture), ignore the camera and
light above and follow the shot.

The city block follows. Then wait for my shots, one per message.
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
LEVEL KM1-2, Komachi-dori: Kamakura Station to the shrine end. Follow the base prompt and the Kamakura block.
Left: the station square's red torii-shaped gateway sign (invented name) and a taxi rank. Then the shopping street:
two-storey shopfronts with noren curtains, hand-painted signboards, paper lanterns, a sweet-potato ice cream stand, a
whitebait croquette shop with a fryer at the window, a rice cracker shop with crackers grilling, a souvenir shop with
racks of chopsticks and fans, a parked rickshaw with its black hood up, banner flags on poles, a "beware of black kites"
sign with a bird drawn on it. The street is paved in pale stone, shared with no cars. Right: the street ends at a side
gate onto the shrine's grounds.
```

```text
LEVEL KM1-3, The Shrine Bridge: through the shrine to school. Follow the base prompt and the Kamakura block.
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
with its whitebait shops, their trays drying on racks. The play lane is firm wet sand.
```

```text
LEVEL KM2-3, The Kite Thief: along the rocks. Follow the base prompt and the Kamakura block.
Continue the beach from the previous image (attached). The sand gives way to a low headland of dark, wave-cut rock shelves
with tide pools, barnacles and seaweed, a path of worn steps along their top, waves washing over the lowest shelf. On a
dry rock in the middle, a single rice ball in its wrapper, dropped. A black kite on a pine branch above. Right: the beach
continues to a large wooden gateway (a torii) standing at the start of a straight avenue inland.
```

```text
LEVEL KM2-4, Wakamiya-oji: the avenue to school. Follow the base prompt and the Kamakura block.
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
LEVEL FL1-2, Brickell Avenue: the towers to the river. Follow the base prompt and the Florida block.
Left: a bus stop at the foot of a glass condo tower with a palm-lined valet loop. Then a wide avenue sidewalk under glass
and concrete towers, a construction site behind printed mesh fencing with a tower crane above, three rental scooters left
across the sidewalk, a coffee kiosk, royal palms in tree grates. Right: the Miami River and a bascule drawbridge with its
operator's tower, gates and warning lights; a tug moored below.
```

```text
LEVEL FL1-3, Bayfront to School. Follow the base prompt and the Florida block.
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
LEVEL FL2-2, The Riverwalk: under the bridges. Follow the base prompt and the Florida block.
A concrete-and-timber riverwalk along the Miami River, side-on: three bascule drawbridges crossing overhead in turn,
the nearest with its leaves partly raised; bollards and coiled lines; crates; moored small freighters with rust streaks;
a tugboat; towers behind; railings along the water's edge. The play lane is the riverwalk.
```

```text
LEVEL FL2-3, Downpour to School. Follow the base prompt and the Florida block, with this light: a sudden tropical
cloudburst. Dark blue-grey storm cloud overhead, heavy rain streaks, sheets of water on the street, gutters overflowing,
light about 6,500 K and flat, a bright break of sun at the far right with steam rising.
Left: downtown's older street: Art Deco and Mediterranean Revival buildings with deep arcades and canvas awnings, a
flooded crosswalk, rain pouring off awning edges in sheets, a bus shelter. Right: the storm breaking, wet palms shining,
the school's covered walkway and gate (the school from FL1-3).
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
skateboard ledges, a kite-flier's kite tied to a bench (no person), the bay behind. Right: the school (as FL1-3).
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
