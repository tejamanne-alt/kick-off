# Kick Off 2: the five cities

The game is five cities, and each city is a chapter of its own: **Kamakura** (Japan), **Florida** (Miami, USA),
**Madrid** (Spain), **New York** (USA) and **Mumbai** (India). PLAY asks which city to play, then opens that city's map.
HOLIDAY RUN asks the same, then runs endlessly through that city's streets. The add-ons are gone: a city is not a reskin
of another city's levels. Each has its own streets, its own light, its own way of getting to school and its own play.

This is the design. What is built so far, and what each city still needs, is at the end ("Where we are").

## The shape of a city

- **One home, one school, two or three routes.** Every route is one trip from the kid's front door to the school gate,
  through real neighbourhoods of the city, the way a child there would really go: on foot, by bus, by tram, by metro,
  by local train, by ferry.
- **Each route is three to five levels**, and each level is one leg of the trip, from one stop to the next (as the
  original town's routes are: `docs/WORLD_MAP.md`). The level that ends at a stop and the next one, which starts there,
  build the same stop.
- **Three kinds of leg:**
  - **A dribble.** The game as it plays now: a street with its hazards, coins, stickers and a target time, ending at a stop.
  - **A ride, between legs** (three-leg routes only). When a route takes a bus, tram or ferry between two dribbles,
    the ride is a short scene that plays by itself (12 to 20 s, skippable): the kid boards, the city slides past the
    window, the kid gets off where the next leg starts.
  - **A mini-game** (routes of four or five legs). At least one leg, and two on most five-leg routes, is a realistic
    activity instead of a dribble: riding the transit yourself, an errand for an aunt, an uncle or a grandparent, shopping for classwork,
    or a city-specific task. Doing it opens the next leg. A mini-game is short (30 to 60 s), can be retried at once,
    and is played with the same controls as the game (the stick, KICK and its hold, jump, slide, and taps).
- **Twist legs.** Some dribbles carry a story beat that changes how they play: something is dropped and the kid must
  go back for it, a downpour hits, or the kid carries something that must arrive dry. These keep the trip from feeling
  like the same street every time.
- **What an errand gives you rides along.** The bento, the science project or the poster board sits on the kid's
  backpack for the rest of the trip. Getting it to school unharmed is the trip's **Delivered** badge (a sticker). It is
  never needed to finish.

## The mini-games: five systems, skinned per city

Each is one system in code, dressed differently by each city. That way five cities cost five mini-games, not fifteen.

### M1. The ride: tram, bus, metro, subway, local train, people mover
1. **Board.** The card reader turns green: tap it in time (the gate opens). Board before the door chime ends.
2. **Ride.** The car sways round bends, brakes and pulls away. Keep the ball still under your foot: push the stick
   against the sway (a balance bar), and hold KICK through a hard brake (KICK's hold to control, which the game already
   has). Each city adds a moment of real etiquette: give your seat to an elderly passenger (Kamakura), make room for a
   stroller (New York), work your way to the door before your stop (Mumbai).
3. **Get off.** The next-stop display and the announcement name each stop. Tap STOP (the bell, the cord, the door
   button) at yours. Miss it, and you get off at the next one: the next leg starts further back and is longer, while
   the trip's clock runs on.
- **Passed:** off at the right stop with the ball. Coins for a smooth ride; a star for never wobbling.
- Some rides add a **choice**: express or local (New York), change lines by following the right colour (Madrid), or
  change loops (Miami).

### M2. The errand: an aunt, an uncle or a grandparent
A short physical task with the relative, who then hands the item over:
- **The basket from the balcony** (Madrid): an aunt lowers a wicker basket from her third floor. The wind swings it.
  Stay under it and catch it, keeping the ball off the wet street with keepy-uppies while you wait.
- **Throw the line** (Florida): the uncle's boat drifts in to the dock. Aim the mooring line at the cleat with KICK's
  drag-aim, the same as aiming a kick, and throw. Two hits and the boat is tied.
- **Wrap the bento** (Kamakura): grandma shows the order. Fold the furoshiki's four corners, then tie the knot in
  two timed taps.
- **The pretzel cart rush** (New York): the uncle's cart has three morning customers. Each order shows in a bubble;
  tap the right items before each customer walks off.
- **The tiffin sort** (Mumbai): the uncle is a dabbawala. Sort the tiffins by their painted codes into the right
  crates before the train leaves, and find your own.

### M3. Shopping for classwork
A list of three or four items (poster board, a glue stick, a compass, markers). Find them on the shelves (tap), then
pay at the counter: pick coins and notes that add up, the fewest you can, and check the change. Each city has its own
shop, money and things on the list: a Madrid *papelería* in euros, a New York art store in dollars with sales tax added,
a Mumbai stationery-and-photocopy shop in rupees, a Miami drugstore in dollars.

### M4. Drop and come back (a twist leg)
Halfway, something is lost: a kite (the bird) snatches a snack and drops it on the rocks, or the wind blows the
homework back down the street. The leg turns round: dribble back to it before something takes it (the tide, a street
sweeper, a dog), then forward again with the time you lost. The camera's look-ahead and the coach follow the turn.

### M5. Wait, then cross
The city's own way of crossing is a short timing moment, built from the existing `Crossing` and `Drawbridge`:
- the Enoden's level-crossing bells and bars, and the crossing volunteer's flag (Kamakura);
- the drawbridges (Miami);
- WALK and DON'T WALK with its countdown (New York);
- the traffic police's whistle at a roundabout (Madrid, Mumbai).

## The look: cinematic, in each city's own light

**The target.** The user's references are screenshots of a recent big-budget open-world game set in Florida. They are
not stored in the repository. We take their **qualities**, never their content: no landmarks, signs, logos,
characters or murals copied from it.
- **Warm direct sun against cool blue shade.** The colour temperature difference is what makes daylight feel hot.
- **Air you can see.** Haze that lifts and softens the distance (warm toward the sun, blue away from it), and towers
  that fade into it.
- **Weathered, lived-in materials:** sun-bleached paint, water streaks under sills, grime at the foot of walls, rust
  bleeding from fixings, chipped murals, patched paving.
- **Density:** wires and poles, signs, billboards, parked vehicles, litter, puddles that mirror the sky.
- **Skies with character:** big cumulus, high cirrus, and at dusk pink and violet cloud lit from below.

**How we get it on a phone, and keep every filter working.** The filters (comic, sketch, classic cartoon) read the
lit picture, the camera's depth and normals, and the figure mask in alpha. So everything below lives in the stages
that come *before* them, and every filter works in every city with no per-city filter work:
1. **The city's light** (`World/WorldLook`, its globals): the sun's colour from its colour temperature, its height,
   the shade's colour, the haze's colour, strength and distance, and the sky's gradient. No cost: the same shader
   numbers, different values.
2. **The city's grade** (`World/PostFX`'s grade parameters: white balance, split tone, saturation, contrast). Every
   filter's first step is this grade. No cost.
3. **Richness baked into the atlas:** weathering, streaks, grime, sun-bleach and rust painted into each kit's atlas
   tiles, and ambient occlusion baked into the vertex colours (the kits already multiply vertex colour by the atlas:
   `docs/ART_DIRECTION.md`, "Production rules"). No runtime cost.
4. **Density from cheap props:** wires, signs and litter are a few hundred triangles each, within the kit budgets.
5. **Puddles reflect the sky** with a view-angle gradient: no reflection pass.

**What we don't do,** and why: HDR targets, screen-space reflections, realtime global illumination, volumetric fog,
normal and roughness maps. Each is a full-screen pass or a big texture cost on the Nord CE5, which ran at 28 fps before
the budgets (`docs/PERFORMANCE.md`). The filters also assume an 8-bit picture with the figure mask in alpha
(`docs/LEARNINGS.md` B1, D5).

**Filter-safe rules for new assets:**
- Draw lines from geometry, never from texture (D5). Murals, signs and weathering are flat paint in the atlas, so the
  ink line never traces them.
- Every new material uses `Toon` (the scenery) or `ToonCharacter` (people): both write the figure mask the filters read.
- Each city gets a filter board before it ships: its reference street in all four looks, faces at 3x (`docs/LEARNINGS.md` A8).

### Each city's light and climate

The colour temperature of the direct sun and of the shade is what a real morning there looks like, in the season the
school trip happens. The game's existing look, Kamakura's, was measured from reference shots (`docs/ART_DIRECTION.md`).
The other cities are set *relative* to it, so the measured look stays the anchor.

| City | Season, time | Direct sun | Shade | Sky and air | Weather in play | Palette |
|---|---|---|---|---|---|---|
| **Kamakura** | May, 7:45 (route 3: June rains) | ~5,400 K, 40° up, a hair warm | ~9,000 K, cool blue-grey | Deep cobalt over a soft sea haze; distant hills go blue | Clear; route 3 in a light June drizzle (~6,800 K, no hard shadows) | Dark-stained timber, grey roof tiles, white plaster, moss, vermilion torii, hydrangea blue |
| **Florida** (Miami) | Late August, 7:50 | ~5,000 K, 30° up, warm | ~8,500 K, teal-blue | Humid: a pale, milky horizon under a deep zenith; towering cumulus; warm glow round the sun | Hot and clear, then a sudden tropical downpour on one leg | Faded pastels (seafoam, coral, flamingo pink, butter yellow), white stucco, palm greens, turquoise water |
| **Madrid** | Early October, 8:30, just after sunrise | ~4,200 K, 12° up: low and golden, long shadows | ~9,500 K, clear blue | Very dry high-plateau air: almost no haze, a saturated deep blue sky, crisp edges | Dry and bright; plane-tree and chestnut leaves falling | Ochre, terracotta, cream and salmon facades, green shutters, black wrought iron, grey granite, slate and zinc roofs |
| **New York** | Late October, 7:50 | ~4,000 K, 15° up, raking down the cross streets | ~10,000 K: the avenues' canyons in deep blue shade | Crisp and clear; shafts of sun across the streets; steam from vents and stacks | Cold clear morning, wind on the bridge and the river | Brownstone chocolate, red brick, cast-iron cream and grey, black fire escapes, taxi yellow, ginkgo gold, pumpkin orange |
| **Mumbai** | July (the monsoon), 11:15 (the afternoon school shift) | Overcast ~6,800 K, soft, no hard shadows (route 3: a break in the clouds, ~5,600 K, steamy) | ~7,500 K | Low grey cloud and sea mist; dark rain bands over the sea; everything wet and reflective | Showers come and go; puddles, flooded gutters, waves over the sea wall | Wet black asphalt, rain-stained colonial stone, painted chawls (blue, pink, green), red buses, black-and-yellow taxis, marigold orange, blue tarpaulins |

## Kamakura, Japan

**The place.** A seaside temple town on the Shonan coast, an hour south of Tokyo. The Enoden, a little green-and-cream
tram, squeezes between houses and crosses lanes on bell-rung level crossings. Black kites wheel over the beach and snatch
food from hands; the signs warn about them. Wakamiya-oji avenue runs straight from the beach to the great shrine, with a
raised path down its middle. Hiking trails cross the wooded hills between temples.
- **Home:** a two-storey timber-and-mortar house in a lane in **Hase**, near the Great Buddha: a dark-stained board
  fence, a persimmon tree, potted morning glories, a bicycle under the eaves, a cat on the block wall.
- **School:** *Yukinoshita Elementary* (invented name), beside the shrine's wooded hill: a three-storey concrete school,
  a sandy sports ground, a cherry tree by the gate, shoe lockers inside the door.
- **Signature:** the tram, the kites, the sea, the steps.
- **Music:** the original town's J-pop and city pop (`MusicCountry.Japan`).

| Route | Legs | The trip |
|---|---|---|
| **KM1 The Enoden** | 4 | Home -> Hase Station -> *(ride the tram)* -> Kamakura Station -> Komachi-dori -> School |
| **KM2 The Shonan Coast** | 5 | Home -> Yuigahama beach -> Grandma's whitebait shop -> along the sand -> Wakamiya-oji -> School |
| **KM3 The Temple Hills** (June rain) | 3 | Home -> hydrangea temple steps -> the hiking trail over the hills -> down through Genjiyama park -> School |

### KM1 The Enoden (4 legs)
1. **KM1-1 Hase Lanes** (dribble). Home to Hase Station. Narrow lanes between block walls, a vending machine corner, a
   small shrine gate. An Enoden level crossing (bells and bars, the tram passing a metre from the walls: M5). A line
   of first-graders in yellow caps walking to school: don't bump them. A delivery scooter. Ends at Hase Station's
   short platform.
2. **KM1-2 Ride the Enoden** (mini-game M1). Tap the IC card, board before the chime ends, ride three stops
   (Yuigahama, Wadazuka, Kamakura) as the car sways between houses. Give your seat to the grandmother who boards at
   Yuigahama for a bonus. Get off at Kamakura, the end of the line.
3. **KM1-3 Komachi-dori** (dribble). The shopping street from the station: shop curtains (*noren*), a sweet-potato ice
   cream stand, a whitebait croquette shop, sightseers (dense pedestrians), a rickshaw puller (a slow moving obstacle
   to ride behind), and a black kite diving at a sightseer's snack (a gull-style hazard). "Beware of kites" signs.
4. **KM1-4 The Shrine Bridge** (dribble). Into the shrine's grounds: the steep arched stone bridge over the lotus pond
   (a hump to jump), pigeons, the big stone steps, the vermilion gate, then the school's gate on the hill beside.

### KM2 The Shonan Coast (5 legs)
1. **KM2-1 Down to Yuigahama** (dribble). Home, under the coast road through a dim pedestrian tunnel (`DarkZone`), out
   past surf shops with boards on racks and beach showers, onto the boardwalk.
2. **KM2-2 Yuigahama Morning** (dribble). The beach: surfers' boards on the sand, the tide (`Tide`), fishing boats
   pulled up on rollers, beach-cleaning sacks, a kite circling. Ends at Grandma's shop on the beach road.
3. **KM2-3 Grandma's Whitebait Shop** (mini-game M2, the bento). Her shop's whitebait trays drying on racks out front.
   Fold the furoshiki's corners in the order she shows, tie the knot in time: the bento rides on your backpack.
4. **KM2-4 The Kite Thief** (twist M4). A black kite snatches the rice ball off the bento and drops it on the rocks
   behind you as the tide comes in. Dribble back for it before a wave covers it, then on along the sand to the
   avenue's first gate.
5. **KM2-5 Wakamiya-oji** (dribble). Up the avenue from the beach: the raised path between stone lanterns and cherry
   trees in full leaf, a crossing volunteer with a yellow flag at each junction (M5), shops waking up on both sides, and
   the second and third shrine gates. Then the school. Deliver the bento for the badge.

### KM3 The Temple Hills, in the June rain (3 legs)
1. **KM3-1 Hydrangea Steps** (dribble). Up a temple's hillside path: stone steps between banks of blue and violet
   hydrangeas, moss slick with rain (the ball runs on), umbrellas, puddles in the worn steps, a stone lantern.
2. **KM3-2 The Hiking Trail** (dribble). Over the wooded ridge: tree roots as steps, a short wooden bridge over a
   gully, the dark mouth of a cave tomb cut in the rock, cedars dripping, a raccoon dog crossing the path.
3. **KM3-3 Genjiyama Down to School** (dribble). Down through the park on the hill: a bamboo grove creaking in the wind,
   a temple bell rung for the morning (a timing moment: the boom shakes the leaves' drops loose), the stone steps down
   to the town and the school's back gate.

## Florida (Miami), USA

**The place.** Miami in the hot, wet season: Cuban Little Havana, the Miami River with its working boats and its many
drawbridges, the glass towers of Brickell, the bay. Heat, humidity, sudden storms, iguanas on the seawalls, roosters in
the street, pelicans on the posts. Florida's existing kit (Art Deco and MiMo shops, ranch houses, canal docks and the
drawbridge, sabal palms) carries over to it.
- **Home:** a 1950s concrete-block ranch house in **Little Havana**, near the river: seafoam stucco, a red door, a
  chain-link fence, a mango tree, a rooster in the yard, a carport with a parked, empty car.
- **School:** *Bayside Elementary* (invented name), downtown between the bay and the park: a cream-and-teal
  concrete school with covered walkways on posts, a palm-lined bus loop, a crossing guard's corner.
- **Signature:** the water and its bridges, the heat and the storms, the wildlife, Cuban Miami.
- **Music:** Florida's (`MusicCountry.Florida`: son, salsa, soca).

| Route | Legs | The trip |
|---|---|---|
| **FL1 Calle Ocho Bus** | 4 | Home -> the bus stop on Calle Ocho -> *(ride the bus)* -> Brickell Avenue -> Bayfront Park -> School |
| **FL2 The River Way** | 5 | Home -> the river -> Uncle Rey's boat -> the Riverwalk -> the drugstore -> School, in a downpour |
| **FL3 Under the Line** | 3 | Home -> the linear park under the elevated railway -> *(the people mover)* -> Biscayne Boulevard -> Museum Park -> School |

### FL1 Calle Ocho Bus (4 legs)
1. **FL1-1 Little Havana Morning** (dribble). Home to the bus stop. Roosters and hens crossing (they flutter up when
   the ball comes), a walk-up cafe window, dominoes tables in the little park, mural walls, a fruit cart with mangoes,
   lawn sprinklers (Florida's existing `Sprinkler`).
2. **FL1-2 The Metrobus** (mini-game M1). Wave the bus down, tap the transit card, find a spot. The bus brakes hard at
   the lights (hold KICK). Pull the cord at Brickell Avenue: miss it and walk back from the next stop.
3. **FL1-3 Brickell Avenue** (dribble). Glass towers, a valet loop, rental scooters left across the sidewalk, a crane
   overhead, the bay wind between towers (`WindArea`), then the river's drawbridge rising for a tug (`Drawbridge`, M5).
4. **FL1-4 Bayfront to School** (dribble). The bay walk: royal palms, pelicans taking off from the posts, a fountain
   plaza, cruise ships across the water, the crossing guard's corner, the school.

### FL2 The River Way (5 legs)
1. **FL2-1 Riverside Street** (dribble). Home down to the Miami River: ranch houses, iguanas sunning on a seawall that
   scuttle across your path, sprinklers, a golf cart.
2. **FL2-2 Uncle Rey's Boat** (mini-game M2, the science project). His fishing boat drifts in. Throw the line onto the
   cleats with KICK's aim. He hands over your science project, a model of the Everglades, which rides on your backpack.
3. **FL2-3 The Riverwalk** (dribble). The boardwalk along the river under three bascule bridges, each rising in turn for
   a freighter or a tug. Mooring bollards, coiled lines, crates.
4. **FL2-4 The Drugstore** (mini-game M3). Poster board, glue and markers for the project's sign, paid in dollars at a
   corner drugstore.
5. **FL2-5 Downpour to School** (twist). Downtown, the sky turns: a tropical cloudburst. Shelter under arcades and
   awnings at the heaviest bursts, or the project gets wet (the Delivered badge is lost). Flooded gutters slow you
   (`SlowZone`), lightning flashes, gusts (`WindArea`). Then the sun and the steam rising off the street, and the
   school.

### FL3 Under the Line (3 legs)
1. **FL3-1 The Underline** (dribble). Home to the station, along the linear park under the elevated railway:
   concrete pillars painted with original murals (the user's first reference shot, without its content), fitness
   stations, a dog park, a bike path to cross.
2. *(Ride: the people mover, a free driverless car on an elevated loop, round the bay's edge.)*
3. **FL3-2 Biscayne Boulevard** (dribble). Palm medians, an old Spanish-style tower, pelicans on lamp posts, a street
   sweeper truck.
4. **FL3-3 Museum Park to School** (dribble). Banyans whose aerial roots make platforms, skateboarders, kite-fliers'
   lines in the bay wind, sprinklers on the lawn, the school.

## Madrid, Spain

**The place.** The old centre of Madrid on a dry, bright October morning. The sun rises late here (about 8:10), so the
walk to a 9:00 school runs in the first low golden light, with long shadows down streets of ochre and terracotta
buildings and their iron balconies. Street-cleaning trucks hose the cobbles at dawn. The Metro's colour-coded lines,
the plazas' arcades and pigeons, El Retiro's lake and chestnut kiosks.
- **Home:** a 19th-century apartment building in **Lavapies**: wrought-iron balconies with geraniums, green wooden
  shutters, laundry on lines, a ground-floor bar with its metal shutter half up.
- **School:** *Colegio Publico Los Tilos* (invented name), in the streets east of El Retiro: a red-brick school with
  tall windows, a walled playground with a football cage, lime trees at the gate.
- **Signature:** balconies and the aunt's basket, the Metro, plazas, the park, the low sun.
- **Music:** to make (`MusicCountry` entry): rumba and flamenco-pop guitars, a chotis organ for the plazas.

| Route | Legs | The trip |
|---|---|---|
| **MD1 The Metro** | 4 | Home -> Lavapies station -> *(ride line 3, change at Sol to line 2)* -> El Retiro -> School |
| **MD2 Tia Carmen** | 5 | Home -> La Latina -> Tia Carmen's balcony -> Plaza Mayor -> the stationery shop -> Paseo del Prado -> School |
| **MD3 The Book Hill** | 3 | Home -> the Atocha roundabout -> the hill of book stalls -> El Retiro's rose garden -> School |

### MD1 The Metro (4 legs)
1. **MD1-1 Lavapies Morning** (dribble). Home to the Metro. The street-cleaning truck's hose jets sweep across the
   cobbles (they push the ball: time your pass), bar shutters rolling up, a fruit shop's crates on the pavement,
   scaffolding over a facade (a walkway to climb), the plaza's benches.
2. **MD1-2 Change at Sol** (mini-game M1, with a choice). Tap the card at the gate. Line 3 (yellow) to Sol, then
   change: follow the red line 2 signs through the tiled corridors (pick the right turn three times), board toward the
   right end of the line, and get off at Retiro, three stops on (Sevilla, Banco de Espana, Retiro).
3. **MD1-3 El Retiro** (dribble). Out of the Metro by the park's gate: the lake with rowing boats, a puppet theatre's
   striped booth, a chestnut roaster's kiosk with smoke, roller skaters, falling leaves that hide puddles.
4. **MD1-4 To School by the Lime Trees** (dribble). Out of the park's east gate: a crossing with a municipal policeman's
   whistle (M5), a kiosk, the school's gate.

### MD2 Tia Carmen (5 legs)
1. **MD2-1 To La Latina** (dribble). Home through steep lanes of old taverns with their shutters down, a delivery van
   unloading bread, the dome of a big church at the end of the street.
2. **MD2-2 The Basket** (mini-game M2, lunch and the forgotten homework). Tia Carmen lowers a wicker basket on a
   rope from her third-floor balcony. The wind swings it. Stay under it and catch it, keeping the ball up with
   keepy-uppies off the freshly hosed street.
3. **MD2-3 Plaza Mayor** (dribble). Through an archway into the great arcaded square: the arcades' columns as cover,
   pigeons that burst up as the ball comes (`Seagull`), cafe terraces' chairs and parasols, the painted facade.
4. **MD2-4 The Papeleria** (mini-game M3). A stationery shop off Sol: poster board (*cartulina*), a compass and
   coloured pencils for maths, paid in euros.
5. **MD2-5 Paseo del Prado** (dribble). The boulevard's plane trees, the botanic garden's railings, a great fountain on
   a roundabout (crossing with the policeman's whistle), then up beside the park's fence to school.

### MD3 The Book Hill (3 legs)
1. **MD3-1 The Atocha Roundabout** (dribble). Home past the old railway station's iron-and-glass hall with palms
   inside, round the big roundabout's crossings.
2. **MD3-2 Cuesta de Moyano** (dribble). The steep street lined with wooden book stalls: the ball rolls back down if you
   stop (a slope), open stall shutters as platforms, leaves blowing down the hill.
3. **MD3-3 The Rose Garden to School** (dribble). Into El Retiro from the south: the rose garden's arches, a fountain,
   the chestnut kiosk, out to the school.

## New York, USA

**The place.** New York in late October: a cold, clear morning, the low sun raking down the cross streets in golden
shafts while the avenues lie in deep blue shade, steam rising from the street. Pumpkins on brownstone stoops. The kid
lives in Brooklyn and goes to school in Lower Manhattan, and the three routes are the three ways across the East River:
walking the bridge, the subway under it, the ferry over it.
- **Home:** a brownstone in **Brooklyn Heights**: a high stoop with iron railings, pumpkins and a cardboard skeleton for
  Halloween, a cellar door in the sidewalk, a ginkgo tree turning gold.
- **School:** *P.S. 412, the Chambers Street School* (invented name), in Tribeca: a five-storey red-brick and limestone
  school with a fenced rooftop yard and a playground, a WALK signal at the corner.
- **Signature:** the river crossings, the subway, steam, stoops, crowds and signals.
- **Music:** to make (`MusicCountry` entry): a boom-bap beat with jazz horns, a Latin boogaloo for the bodegas.

| Route | Legs | The trip |
|---|---|---|
| **NY1 The Brooklyn Bridge** | 4 | Home -> the bridge's ramp -> over the bridge -> Uncle Sal's cart at City Hall -> School |
| **NY2 The Subway** | 5 | Home -> Borough Hall station -> *(the express or the local)* -> Tribeca -> the art store -> the river park -> School |
| **NY3 The Ferry** | 3 | Home -> DUMBO's landing -> *(the ferry across)* -> the Wall Street pier -> the Financial District -> School |

### NY1 The Brooklyn Bridge (4 legs)
1. **NY1-1 Brownstone Stoops** (dribble). Home through Brooklyn Heights: stoops, an open steel cellar door in the
   sidewalk (a gap), black garbage bags piled at the curb (soft obstacles), a dog walker with six dogs on leashes
   (`Dog`), a scaffolding sidewalk shed (a low roof and a walkway on top).
2. **NY1-2 The Bridge** (dribble). The elevated wooden promenade: the granite towers' arches, steel cables in a web
   overhead, the bike lane beside you (cyclists ringing their bells: a lane hazard), gusts off the river (`WindArea`),
   and the whole skyline ahead.
3. **NY1-3 Uncle Sal's Cart** (mini-game M2). Uncle Sal's pretzel and coffee cart by City Hall Park: help with the
   morning rush (three orders in time), and he hands over a bag of bagels for your class.
4. **NY1-4 City Hall Park to School** (dribble). The park's fountain, gas-style lamps, squirrels (`TreeSquirrel`),
   pigeons, then west along the street to the WALK signal (M5) and the school.

### NY2 The Subway (5 legs)
1. **NY2-1 Court Street** (dribble). Home to Borough Hall: a subway entrance with its green globe lamps, a newsstand,
   a halal cart, a striped steam chimney from a street repair, a crosswalk with its countdown.
2. **NY2-2 Express or Local** (mini-game M1, with a choice). Tap at the turnstile. Down on the platform the board says
   which train comes next: the express skips your stop, the local stops there. Pick the right train, "stand clear of
   the closing doors", hold the pole through the curves under the river, make room for a stroller, get off at
   Chambers Street.
3. **NY2-3 Tribeca Cobbles** (dribble). Cobbled streets, cast-iron facades, loading docks with steel canopies (raised
   platforms), steam from a vent that lifts the ball (a springboard), a film crew's equipment cases.
4. **NY2-4 The Art Store** (mini-game M3). Canvas board, acrylic paints and a brush for art class, paid in dollars, sales
   tax added at the till.
5. **NY2-5 Hudson River Park to School** (dribble). The river greenway: piers, a skate park, joggers, wind off the
   river, the school.

### NY3 The Ferry (3 legs)
1. **NY3-1 DUMBO Cobbles** (dribble). Home down to the old waterfront: cobbles with old rail tracks set in them, the
   steel bridge overhead with trains rumbling across (the screen shakes), a glass-boxed carousel, the ferry landing.
2. *(Ride: the ferry across the East River, spray and gulls and the skyline.)*
3. **NY3-2 The Wall Street Pier** (dribble). Off the ferry onto the pier: the elevated highway's shadow, bollards, a
   narrow cobbled lane of old buildings.
4. **NY3-3 The Financial District to School** (dribble). Narrow canyons between towers, security bollards and planters,
   an old church's graveyard railings, then north to the school.

## Mumbai, India

**The place.** South Mumbai in the monsoon. The kid goes on the afternoon school shift, so leaves home at 11:00, when the
city is fully awake and the dabbawalas are sorting the lunch tiffins at the stations. Rain comes in bands off the sea,
the waves burst over the sea wall, the streets run with water, and between showers everything shines.
- **Home:** an old two-storey wooden house in **Girgaon**, in a lane of houses with carved verandahs and painted
  balconies (a heritage village of the old city): potted tulsi, a scooter under a blue tarpaulin, a cat.
- **School:** *Fort Public School* (invented name), by the big cricket ground: a stone Victorian building with arched
  verandahs, a gate with a guard's booth, a playground of red earth.
- **Signature:** the monsoon, the sea wall, the local train, the dabbawalas, cricket.
- **Music:** to make (`MusicCountry` entry): a filmi brass band, tabla and dholak, a Koli fishing-song lilt for the sea.

| Route | Legs | The trip |
|---|---|---|
| **MB1 Marine Drive** | 4 | Home -> Girgaon Chowpatty -> along the sea wall -> the dabbawalas at Churchgate -> across the cricket ground -> School |
| **MB2 The Local Train** | 5 | Home -> Charni Road station -> *(the fast local)* -> Churchgate's underground market -> the stationery shop -> Kala Ghoda -> School |
| **MB3 The Red Bus** (a break in the rain) | 3 | Home -> Girgaon's main road -> *(the red bus)* -> the old market -> the arcaded road -> School |

### MB1 Marine Drive (4 legs)
1. **MB1-1 Wadi Lanes and Chowpatty** (dribble). Home through the lanes of wooden houses, out onto Girgaon Chowpatty
   beach: snack carts under tarpaulins (shut till evening), monsoon waves on the sand (`Tide`), crows.
2. **MB1-2 The Sea Wall** (dribble). Marine Drive's promenade: tetrapods below the wall, waves bursting over it in
   timed sprays that soak and push (a fountain-style hazard, M5's timing), the Art Deco apartment fronts across the
   road, umbrellas, a sweet-corn roaster's cart.
3. **MB1-3 The Tiffin Sort** (mini-game M2). Uncle is a dabbawala at Churchgate. Sort the tiffins by the colour and
   letter codes painted on their lids into the right crates before the train leaves, and find your own lunch.
4. **MB1-4 Across the Maidan to School** (dribble). The cricket ground in the rain: a dozen matches at once, and their
   balls fly across your path (dodge them, or kick one back for a bonus), the Gothic and Art Deco fronts on either
   side, then the school.

### MB2 The Local Train (5 legs)
1. **MB2-1 To Charni Road** (dribble). Home to the station: a chai stall, a cobbler under an umbrella, handcarts loaded
   with sacks (moving obstacles), stray dogs, the footbridge's steps over the tracks.
2. **MB2-2 The Fast Local** (mini-game M1). The platform crowd surges as the train comes in, and it doesn't wait:
   board in the gap before it moves, find a place inside away from the open door, keep the ball through the sway, work
   to the door before Churchgate, step off.
3. **MB2-3 Churchgate Subway** (dribble). The underground walkway packed with stalls: hanging bags, phone covers and
   umbrellas as low obstacles, dim stretches (`DarkZone`), steps up into the rain.
4. **MB2-4 The Stationery Shop** (mini-game M3). Chart paper, a geometry box and glue at a stationery-and-photocopy shop,
   paid in rupees. Keep the chart paper rolled and dry from here on for the badge.
5. **MB2-5 Kala Ghoda to School** (dribble). The art district's lanes: flooded gutters (`SlowZone`), puddles, a
   painted wall, a stone library's portico as shelter from a burst of rain, the school.

### MB3 The Red Bus, in a break in the rain (3 legs)
1. **MB3-1 Girgaon Road** (dribble). Home to the bus stop on the main road: black-and-yellow taxis, a festival
   pavilion being built of bamboo (scaffold platforms), handcarts, a flower seller's marigolds.
2. *(Ride: the red double-decker bus along the road past the great Gothic railway terminus.)*
3. **MB3-2 The Old Market** (dribble). The covered market's clock tower and its fruit stalls: crates of mangoes and
   bananas, porters with baskets on their heads (moving obstacles), pigeons.
4. **MB3-3 The Arcaded Road to School** (dribble). Under the arcades of the old Fort's stone buildings, past a fountain
   on a busy roundabout (the traffic policeman's whistle), to the school.

## The Holiday Run in each city

The endless run strings the city's dribble legs into stages, in the city's own light, with its own hazards and music.
Kamakura's run exists now (the original town's 23 stages). Each other city gets its own once its streets are built.
Until then the HOLIDAY RUN picker shows it as coming soon.

## Where we are

**Built now:**
- PLAY and HOLIDAY RUN each open a city picker (`UI/CityPicker`).
- The Add-ons & Filters button and screen are now **Filters** only (`UI/FiltersPanel`), also reachable from the pause
  menu.
- The cities are `Progression/Cities`. **Kamakura** plays the original town's 23 levels (its routes in this document
  replace them once built). **Florida** plays its 9 levels so far (Home Street and the beach in Florida's streets).
  **Madrid**, **New York** and **Mumbai** show as coming soon.
- California (Santa Monica) is not one of the five: it left the picker, and its scenes are no longer built.
- Each playable city's light follows its climate here (`Progression/Cities`, `CityClimate`).

**To build, city by city:**
1. **References:** the user makes them with `docs/IMAGE_PROMPTS.md` (one city and one level at a time) and saves them
   in `review/<city>/refs`.
2. **The kit:** about 40 to 60 models a city (`tools/blender/kit_buildings_<city>.py`), within the budgets in
   `docs/ART_DIRECTION.md`, with weathering and ambient occlusion baked in, and reviewed in all four looks.
3. **The mechanics:** the five mini-game systems (M1 to M5) once, then each city's dressing and hazards.
4. **The levels:** each route's legs in `Editor/GeneratedContent.cs` and `Editor/GreyboxLevels.cs`, with the stops in
   `Levels/RouteTable.cs`. Level ids are the route's id and leg (`KM1-1`), never reused.
5. **Music** for the three new countries.
6. **Kamakura's new routes** replace the original 23 levels last, with a save upgrade that keeps every sticker and coin
   already earned (persisted ids never change: `docs/LEARNINGS.md` H7).

**Cost per new city** (est., none built): one building kit and its 4096 x 4096 atlas (about 16 MB in memory
uncompressed, a quarter of that compressed), loaded only in that city's scenes; 12 levels' scenes; models within the
kit budgets. Mini-games are small scenes with a fixed camera and few objects, lighter than a street. Each city must
be checked on the Nord CE5 before it ships.
