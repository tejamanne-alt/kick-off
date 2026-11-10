# Kick Off 2: AI image prompts for a new town (ChatGPT)

These prompts make the reference images for a new add-on town: a base prompt that works for any place, a
**Florida** block, and one prompt per shot. They were written for a Florida add-on (a third town next to
Kamakura and California, `<scene>_FL` beside `<scene>_CA`). Its chapter 3 is built from the six photographic
references these prompts made (`review/florida/refs`, F3-1 to F3-6); the other chapters' shots are still to make.

## Photorealistic or not: photorealistic, but lit like the game

The game never shows these images. Every building, prop and plant is modelled by script in Blender
(`tools/blender/kit_*.py`, as the California Coast kit was in `kit_buildings_cal.py`), and its atlas is painted
by script too. The toon look comes from the game's own shaders and grade (`Art/ChapterTheme.cs`,
`World/WorldLook.cs`, `World/PostFX.cs`). The images are only **references**: what to model, at what
proportions, in which materials, colours and weathering. So:

- **Ask for photorealistic images.** A photograph shows true proportions and real construction: how an
  accordion shutter folds, how far an eyebrow ledge sticks out, where a downpipe runs, how a motel's walkway is
  hung. Those can be measured and rebuilt. An illustration (like the six Florida street references) bends the
  perspective and invents detail that cannot be measured.
- **Light them like the game, not like the illustrated references.** Ask for clear midday, a high near-white
  sun, a deep cobalt sky and big cumulus (`docs/ART_DIRECTION.md`, "What makes the look"). The illustrated
  references are a sunset. Under orange light no colour can be read against the game's palette, and every
  colour would have to be guessed.
- **Keep everything sharp, with no people.** Depth of field or motion blur hides the detail we model from.
- **Texture plates are different** (a facade, a sign or a material painted into an atlas): straight-on
  elevation, flat shadowless light, no perspective. The game adds its own light and shade, so a plate with a
  shadow baked into it would be shaded twice.

**Using the illustrated Florida street references.** They show what is on the street and how it is laid out,
not the style. They make one continuous strip in this order: 1 (beach), 2 (diner), 3 (motel), 4 (shops),
6 (the block before the school), 5 (the school). Each overlaps the next: the snack shack appears in 1 and 2,
the skate rental in 2 and 3, the surf shop in 3 and 4, Shellback in 4 and 6, the school bus in 6 and 5. They
carry an image generator's sparkle mark in the corner, and the base prompt tells ChatGPT to ignore it.

## How to use them in ChatGPT

1. Start a new chat. Attach the street references you have (optional). Paste **Message 1** (the base prompt)
   followed by the **Florida block**, as a single message.
2. Send one **shot** per message after that. For a continuous street, attach the previous picture and keep the
   "continue" line in the shot.
3. Ask for the widest landscape picture it offers. The phone's screen is about 2.2 : 1, wider than any
   generator's frame, so the important things stay in the middle band.
4. If the pictures drift (sunset light creeping back, people appearing, a vanishing-point street), paste
   Message 1 again.
5. Save the results as `review/florida/refs/<chapter>_<shot>_<what>.png` (for example
   `review/florida/refs/ch3_F3-2_diner.png`), outside `Assets/` so they never reach a build. Then ask for the
   Florida kit to be built from them.

## Message 1: the base prompt (any location)

```text
You are making photographic reference images for a video game's art team. Read all of this, then follow
it for every image in this chat.

THE GAME
A 2D side-scrolling platformer for phones (rendered in 3D but played and seen from the side): a kid
dribbles a soccer ball along the sidewalk from home to school. The camera looks straight across the
street at the fronts of the buildings, like a stage set seen from the front row. Our 3D artists will
model the game's buildings, props and plants from your images, so accuracy matters more than drama.

CAMERA (every image unless a shot says otherwise)
- Straight-on side view: the street runs left to right, parallel to the image, and building fronts face
  the camera squarely. No diagonal streets, no vanishing-point perspective, no aerial or low-angle shots.
- Eye height about 2.5 m, about 9 m from the building fronts. A natural 35-50 mm lens, no fisheye or
  wide-angle distortion, verticals stay vertical. Horizon a little above the middle.
- Layers from front to back: an EMPTY, continuous sidewalk across the bottom quarter of the image (the
  play lane: flat, nothing standing on it except things at its edges), then the curb, the building row,
  a back row of roofs and trees, and a far skyline.
- Everything sharp from front to back: no depth of field, bokeh, motion blur, vignette, lens flare, film
  grain or HDR halos.
- The widest landscape format available.

LIGHT AND COLOR (must match the game's light)
- Clear midday. A high sun slightly behind the camera and to the left, near-white, only a hair warm:
  fronts are lit and shadows are crisp.
- A deep cobalt-blue sky that stays deep almost down to the horizon, with big white cumulus clouds with
  cool grey undersides far off. Distant land goes a deeper blue, never a hazy white.
- Shaded sides a cool blue-grey; shadows on the ground deep and cool; dark contact shadows under
  objects.
- NO sunset, golden hour, dusk, night, orange or yellow cast, or color filter. Whites stay just under
  pure white (no blown highlights); asphalt and concrete are neutral mid-greys.
- Color comes in small, saturated doses (an awning, a door, a sign, a bike) against quiet, true
  materials.

CONTENT
- Photorealistic, like a professional architectural photograph of a real, lived-in, slightly weathered
  street: sun-faded paint, rain streaks under sills, dust and splash at the base of walls, patched
  paving, cracked curbs, small repairs.
- Real-world proportions: doors about 2.1 m high, curbs 15 cm, storeys about 3 m. Include ordinary
  scale cues (doors, steps, a trash can, a parked car).
- Detail comes from real parts: gutters, downpipes, AC units, meters, poles and wires, mailboxes,
  planters, signs, bike racks.
- Signs in plain English with INVENTED business names. No real brands, logos, chains or trademarks, and
  no readable license plates.
- ABSOLUTELY NO PEOPLE: no pedestrians, drivers, figures, silhouettes, crowds, mannequins or
  reflections of people. No animals. Parked cars are empty, and nothing is moving.
- Do not add text, labels, captions, borders, logos or watermarks to the image.
- Keep the same time of day, sun direction and weather in every image of this chat.

REFERENCE IMAGES I ATTACH
Illustrated references show only what is in the street and how it is laid out. Do not copy their
drawing style, their colors or their sunset light, and ignore any watermark or sparkle mark in them.

The location follows. Then wait for my shots, one per message.
```

## The Florida block (paste right after Message 1)

```text
LOCATION: FLORIDA, USA
A small Atlantic beach town on Florida's east coast, along the coast road (A1A), like the beach towns of
the Space Coast and Daytona: a laid-back 1950s-70s beach strip with Art Deco and Miami Modern (MiMo)
buildings, and everyday neighborhoods behind it. It must read as Florida at first glance, not as
California, Mexico or the Mediterranean.

BUILDINGS
- Concrete block and stucco everywhere, smooth or lightly textured, in faded pastels: seafoam, aqua,
  coral, flamingo pink, butter yellow, pale lavender and white, with contrasting trim.
- Art Deco and MiMo shops and motels: flat roofs behind parapets, rounded corners, horizontal "eyebrow"
  ledges over the windows, racing stripes, porthole windows, glass-block panels, breeze-block screens,
  cantilevered concrete canopies, angled roadside signs with neon tubes.
- Two-storey motels with open exterior walkways and metal railings, doors onto the walkway, an outside
  stair, a kidney-shaped pool behind a fence, a neon VACANCY sign.
- Homes: single-storey concrete-block ranch houses with low hip roofs in white or grey concrete tile,
  barrel tile or standing-seam metal; jalousie and awning windows; screened porches and screened pool
  enclosures; carports; terrazzo steps.
- Some Old Florida wood-frame houses: raised on piers, lap siding, a deep front porch, a silver
  standing-seam metal roof, louvered shutters.
- Built for hurricanes: accordion and roll-down storm shutters folded beside the windows, shutter tracks
  over openings, impact-glass shopfronts.
- Lived in: wall-hung and ground AC units with drip stains, exposed conduit, electric meters, dark
  mildew on shaded walls, rust bleeding from fixtures, sun-bleached awnings.

PLANTS
- Sabal palms (cabbage palms, the state tree) are the main street palms: straight grey trunks, some with
  criss-crossed "boot" leaf bases, some smooth, with round crowns of fan leaves. Also tall royal palms
  (smooth pale trunks, a green crownshaft), leaning coconut palms near the beach and clumping areca
  palms in gardens. NOT the very tall, skinny California fan palms.
- Saw palmetto, sea grape and yucca on the dunes, sea oats along the dune crests; live oaks hung with
  Spanish moss in the neighborhoods; bougainvillea, hibiscus, crotons and bird of paradise in the
  gardens; coarse blue-green St. Augustine lawns with sandy patches on the verges.

STREET
- Concrete sidewalks with expansion joints, brick-paver crosswalks, crushed-shell or sandy parking
  lots, sand drifting against the curbs near the beach.
- Square concrete utility poles (some wooden) with overhead lines; traffic signals hung from span wires,
  mast-arm signals at the bigger junctions.
- Blue "Hurricane Evacuation Route" signs, numbered "Beach Access" signs, sea-turtle nesting and
  lights-out signs, crosswalk beacons, school-zone signs with flashing lights.
- Fire hydrants (yellow, or silver with colored caps), blue mailboxes, newspaper boxes, bike racks,
  bus-stop benches, beach showers, trash cans, parked golf carts and beach cruiser bikes, surfboard
  racks.

BEACH
Dune crossovers on raised wooden walkways with handrails, a brightly painted lifeguard stand, pale,
fine sand with bits of shell (warm off-white, never pure white or blown out), shallow green-to-turquoise
water with white foam lines, a long wooden fishing pier.

WEATHER
A clear summer day: tall cumulus over the sea, no haze, no rain.
```

To make a Miami Beach version instead, replace the block's first paragraph with: *"Miami Beach, Florida: the
Art Deco and MiMo streets behind the ocean (pastel three-storey hotels with neon, terrazzo, porches with
deco railings), royal palms and coconut palms, a wide beach with colorful lifeguard stands."*

## The shots

Each is one message. The level names are the original town's (`docs/WORLD_MAP.md`). Shots F3-1 to F3-6
follow the six illustrated references, in their order.

### Chapter 3, Seaside Road (L11 to L14): the beach to the school

```text
SHOT F3-1, the beach front. Follow the base prompt and the Florida block.
Seen from the beach-side sidewalk looking across a low dune toward the sea: a wooden dune crossover
with handrails rising over the dune on the left, a brightly painted lifeguard stand on the sand, a
volleyball net, a small concrete-block restroom with beach showers, a wooden snack shack on the right,
racks of kayaks and paddleboards under a canvas shade, sea oats and sea grape on the dune, a "Beach
Access 23" sign, a sea-turtle nesting sign. Sea and horizon behind. A row of sabal palms. The play lane
across the bottom is a wooden boardwalk becoming a concrete sidewalk.
```

```text
SHOT F3-2, the beach access and the diner. Follow the base prompt and the Florida block.
Continue the same street from the previous image: its left sixth repeats the right sixth of the image
I attach. A shell-surfaced parking lot with timber wheel stops, a chrome-and-stucco 1950s roadside
diner with a tall angled neon pole sign (invented name), booths visible through its windows, a "Beach
Access" walkway between dunes, two cobra-head street lights, a bus-stop bench, a blue hurricane
evacuation route sign, a parked, empty, sun-faded small car, saw palmetto and sea grape in the verges.
```

```text
SHOT F3-3, the motel strip. Follow the base prompt and the Florida block.
Continue the same street from the previous image (attached). A two-storey MiMo motel in faded aqua and
white with an open walkway, metal railings, an outside stair, an angled neon sign with VACANCY, a pool
fence; a beach rental shop (bikes, skateboards, boogie boards out front); a square concrete utility pole
with wires and a span-wire traffic signal; a yellow fire hydrant; a bus-stop bench; a parked, empty,
weathered pickup truck. Sabal palms in front, a royal palm behind.
```

```text
SHOT F3-4, the shop row. Follow the base prompt and the Florida block.
Continue the same street from the previous image (attached). A row of one- and two-storey Art Deco
shops in pastel stucco with eyebrow ledges and glass block: a surf shop with surfboards leaning by the
door, a Cuban cafe with a walk-up coffee window, a bait-and-tackle shop, an ice-cream parlor, an empty
shopfront with folded accordion shutters. Striped awnings, a cafe table and chairs, bike hoops, a trash
can, a parked, empty car. Tall sabal palms in tree pits along the curb.
```

```text
SHOT F3-5, the last block before the school. Follow the base prompt and the Florida block.
Continue the same street from the previous image (attached). The last shops on the left; then a
chain-link fence around a small grass sports field with a soccer goal; concrete steps rising to a
wooden beach-access crossover with the sea and a fishing pier beyond; a school-zone sign with flashing
lights; a blue mailbox; a parked, empty, yellow school bus at a bus stop on the right; palms along the
shore.
```

```text
SHOT F3-6, the school. Follow the base prompt and the Florida block.
Continue the same street from the previous image (attached). A Florida public high school: long one-
and two-storey concrete-block buildings in cream and teal with flat roofs, open-air covered walkways on
metal posts, a few portable classrooms, a front gate in an aluminum picket fence, an LED marquee sign
with an invented school name, a flagpole with the US and Florida flags, a bus loop with a parked, empty
yellow school bus, bike racks, a crosswalk with a flashing school-zone beacon, sabal palms and a live
oak. No students, nobody at all.
```

### Chapter 1, Home Street (L01 to L05)

```text
SHOT F1-1, the home street. Follow the base prompt and the Florida block.
A quiet residential street: single-storey concrete-block ranch houses in pastel stucco with low hip
roofs (white concrete tile, barrel tile, metal), jalousie windows, carports, screened porches, storm
shutters, mailboxes on posts, St. Augustine lawns, crotons and hibiscus, sabal palms and a live oak
with Spanish moss shading the sidewalk. One house has a red front door: the kid's home. A parked, empty
car in a driveway.
```

```text
SHOT F1-2, the Old Florida street and the church. Follow the base prompt and the Florida block.
A street of Old Florida wood-frame houses raised on piers with deep porches and silver metal roofs, a
grandmother's small pink bungalow with a porch swing, and at the end a white Spanish Mission-style
church with a bell tower and red barrel-tile roof. Live oaks with Spanish moss over the street, picket
fences, a bus-stop shelter.
```

```text
SHOT F1-3, up the hill: the canal bridge. Follow the base prompt and the Florida block.
Florida is flat, so the climb is a sidewalk rising gently onto a low concrete bridge over a residential
canal: seawalls, wooden docks, a boat on a lift, mangroves along the far bank, houses with screened
pool enclosures backing onto the water. Concrete bridge railings, a "No Wake" sign, palms.
```

### Chapter 2, Market Street (L06 to L10)

```text
SHOT F2-1, Market Street. Follow the base prompt and the Florida block.
A small downtown main street: two-storey Mediterranean Revival and Art Deco buildings in stucco with
barrel-tile pent roofs, arched windows, iron balconies and colored awnings: a bakery, a post office, a
flower shop, a library with columns. Brick-paver crosswalks, span-wire traffic signals, newspaper
boxes, planters with bougainvillea, royal palms down the median.
```

```text
SHOT F2-2, the farmers' market. Follow the base prompt and the Florida block.
A Saturday farmers' market on a small plaza: white canopy tents and wooden stalls with crates of
oranges, grapefruit, mangoes, key limes and tomatoes, buckets of flowers, chalkboard price signs, a
cart selling fresh-squeezed orange juice. No vendors, no shoppers, nobody at all. Shops behind.
```

### Chapter 4, the Underpass and the Building Site (L15 to L18)

```text
SHOT F4-1, the station and the railway underpass. Follow the base prompt and the Florida block.
A Spanish Mission-style railway station in cream stucco with a red tile roof and a covered platform,
the single-track coastal railway on a concrete embankment, and a road and sidewalk passing under a
concrete railway bridge; railroad crossing signs, a freight car parked on a siding, palms and saw
palmetto along the tracks.
```

```text
SHOT F4-2, the building site. Follow the base prompt and the Florida block.
A condo tower under construction behind a chain-link fence hung with printed mesh: a concrete frame with
rebar sticking out of the columns, a tower crane, stacks of concrete block and rebar, concrete pipes,
a site office trailer, porta-johns, a security gate, a sand pile, puddles in limestone fill. No
workers, nobody at all.
```

### Chapter 5, the Park (L19 to L23)

```text
SHOT F5-1, the park. Follow the base prompt and the Florida block.
A city park: a retention lake with a fountain aerator and a boathouse, a bandstand, a small cafe kiosk,
a playground under big colored shade sails, a concrete path with benches, a huge live oak with Spanish
moss, a banyan tree, sabal palms, a "No Swimming" sign. Nobody at all.
```

### Asset sheets (for the kit's models)

```text
SHOT P-1, the street props sheet. Follow the base prompt's color and content rules, but ignore its camera.
A product-style sheet of Florida street props on a plain mid-grey background, each standing apart with
space around it, every one shown twice: straight from the front and from a three-quarter angle, all at
the same scale. A square concrete utility pole top with crossarm and insulators, a span-wire traffic
signal, a cobra-head street light, a yellow fire hydrant, a blue mailbox, a newspaper box, a bus-stop
bench, a beach shower, a trash can, a hurricane evacuation route sign, a beach access sign, a sea-turtle
sign, a school-zone flashing sign, a bike rack, a golf cart. Even, soft studio light, a small soft
shadow under each. No labels.
```

```text
SHOT P-2, the plants sheet. Follow the base prompt's color and content rules, but ignore its camera.
Florida plants on a plain mid-grey background, each standing apart, from the side, at the same scale,
with a 1.8 m person-sized grey pole for scale (not a person): a sabal palm with boots, a smooth sabal
palm, a royal palm, a leaning coconut palm, an areca palm clump, a young live oak with Spanish moss,
saw palmetto, sea grape, sea oats, yucca, a croton, a hibiscus, a bougainvillea, a bird of paradise.
Even, soft studio light. No labels.
```

```text
SHOT P-3, a texture plate. Ignore the base prompt's camera and light.
A flat, straight-on elevation of [the motel's front wall / a shop front / a stucco wall section],
exactly front-on with no perspective at all, filling the frame edge to edge, lit by flat, even,
shadowless overcast light (no cast shadows, no shading, no highlights, no sky). True colors of the
materials, weathering and stains included. No people, no text other than the building's own sign.
```

## Add-ons for Blender and Unity: none needed

- **Blender:** nothing to install. The kits are built by script with the `bpy` module (`bpy==5.2.3`,
  `tools/blender/README.md`), which uses no add-ons. The images are read by eye: they set what the script
  models and paints. To look at a picture inside Blender next to a model, the built-in tools are enough: Add >
  Image > Reference, or File > Import > Images as Planes (built in since Blender 4.2). Only to rebuild a scene
  by hand from a perspective photo would a camera matcher help (fSpy, a free app with a Blender importer), and
  the straight-on shots above don't need one.
- **Unity:** nothing to install. The game uses the built-in render pipeline with its own shaders
  (`Packages/manifest.json` has no URP or HDRP), and its settings are applied from code. Don't add URP or HDRP,
  Asset Store toon shaders, or photo-texture and photogrammetry packs: they would change every scene's look,
  bypass the atlas pipeline and break the budgets in `docs/PERFORMANCE.md`. Don't import the reference images
  into `Assets/`.

**Cost:** these prompts and the images cost nothing in the game. A Florida add-on built from them would cost
about what California did: its own building kit and atlas (the Coast kit's is 4096 x 4096), loaded only in its
own `_FL` scenes; models within the kit budgets in `docs/ART_DIRECTION.md` (a building 6,000 triangles, a tree
6,000, a street prop 1,500); and a level build twice as long again for the extra scenes. It must be checked on
the Nord CE5 like any other change.
