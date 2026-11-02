# The town, the routes and the way to school

One home, one school, six ways between them. **Every story level is one trip from the front door to the school gate along one route**: it starts on the home front, runs through that route's own streets (the level's chapter look) and ends at the school's arch, the same arch and grounds in every level. The map shows the town with the six routes drawn from the house to the school and each level on its route.

Nothing here has been run in Unity or on a device (see PROGRESS.md for what was checked offline).

## The routes (`Levels/RouteTable.cs`)

| Route (en / es) | Chapter | Levels along it (place) | The challenge beside it |
|---|---|---|---|
| **Home Street** / Mi calle (`street`) | 1 | L01 Out the Door (the front of the house), L02 Parked Cars (Elm Street), L03 Up the Hill (Hill Road), L04 Garden Gate (Garden Lane), L05 Puddle Lane | C01 Keepy-Uppy (the front garden) |
| **Market Street** / Calle del mercado (`market`) | 2 | L06 Market Morning, L07 First Crossing, L08 Corner Shop, L09 Fruit Stalls, L10 Rush Hour | C02 Window Shopping |
| **Seaside Road** / Paseo marítimo (`beach`) | 3 | L11 Boardwalk, L12 Low Tide, L13 Seagull Bay, L14 Sandcastle Sprint | C03 Beach Slalom |
| **The Underpass** / El paso subterráneo (`underpass`) | 4 | L15 The Underpass, L18 Tunnel Run (the road tunnel under the railway) | none |
| **Building Site Shortcut** / Atajo de las obras (`site`) | 4 | L16 Building Site, L17 Cranes | C04 Site Targets |
| **Park Path** / Camino del parque (`park`) | 5 | L19 Park Gates, L20 Fountain Square, L21 Playground, L22 Duck Pond, L23 The Final Bell | C05 Juggle Champion |

Chapters stay the unit of the paywall (`Store/Monetization.IsChapterUnlocked`), of the Holiday Run's stages and of the level catalog; routes are how the map and the levels present them. Chapter 4 has two routes, and its levels alternate between them (15 underpass, 16 and 17 site, 18 underpass). Progression is unchanged: a story level unlocks when the one before it in the catalog is done (`Progression/LevelUnlocks`); a challenge unlocks with its chapter's first level.

## The town (the map's geography)

Map space is 1600 x 900 units, origin top left, y down; the map is drawn in a fixed-aspect frame and scaled to the screen. Positions below are the intended composition; tune them for looks.

- **Home** at the south-west (about 200, 700): the kid's house on Home Street, in a neighbourhood of small houses on a street grid. **The school** at the north-east (about 1360, 190), near the sea: the stone arch, the wall and the grounds, with its name.
- **The sea and the beach** along the east and south-east: the coast runs from the school's side down to the south-east corner, with a sand strip, a boardwalk, a lifeguard tower, parasols and palms. The beach route follows the coast road from home along the south and up the shore to the school.
- **The park** in the north-west and north: a fenced green area (its boundary drawn as a fence line) with a gate on its south side, a fountain square, a playground, a duck pond and trees. The park route enters at the gate and crosses to the school from the west.
- **The market** in the middle of the south: a block of shops with awnings, a market square, a zebra crossing and the main road with traffic. The market route runs along Market Street to the school.
- **The railway** across the middle from the west edge to the east, with the **underpass** (a road tunnel under the line) and the **building site** (fenced, with a tower crane and a digger) beside it. The underpass route goes through the tunnel; the site route is the shortcut through the site's gate.
- **Home Street's route** is the direct way: from the house up the hill and through the garden lanes, between the park and the market.
- A **town boundary** (a dotted line a little inside the frame), main streets with names, side streets, a few blocks of buildings, a compass and a "you are here" at home. Streets are realistic: the routes follow them (and the park's paths, the coast road, the tunnel) and meet only at the two ends, at most sharing a short stem near home and near the school.

## The map screen (`FrontEnd/ChapterMapScreen.cs`, data in `Levels/TownMap.cs`)

- Draws the town (land, sea, beach, park, market blocks, railway, site, streets, boundary, labels), the **house** and the **school**, and the **six routes** as coloured lines with a white casing from home to the school; each level is a numbered node on its route (stars below, a lock when locked, the next level to play pulses); each challenge a gold "!" node beside its route.
- The route that holds the next level to play (or the chapter asked for through `FrontEndController.RequestedChapter`) is in focus: full colour, thicker; the others are dimmed. A strip of route chips (name, stars out of the total) along the bottom focuses a route; a node can be tapped at any time.
- Paywalled chapters (`Monetization`) keep today's behaviour: their nodes are locked and an unlock button (`UnlockPanel`) appears for the focused route.
- Fits any aspect ratio from 4:3 to 21:9 without overlaps (the map is scaled to fit, the sea and land colours fill the rest), uses the safe area, and every string goes through `Loc` in English and Spanish.

## Every level starts at home (`Editor/LevelBuildKit*.cs`, `StreetBuilder*.cs`)

- Each story level gets a **home lead-in** of about 12 m before its own start: the kid starts on the doorstep of the house with the ball, walks along the front of the house and its garden, and reaches the route's own street where the level begins (x = 0 as before, so every layout and its feasibility audit is unchanged).
- The lead-in is the **home street's look** (chapter 1: lawns, houses, walls, poles) in every level, even on the beach, at the site and in the park, with a short **route signpost** ("School -> Seaside Road") where the route's own environment takes over.
- The **home front** is one set piece built from the kits: the house with its door, a garden gate, picket fence, mailbox, flower pots, a bike and a parent at the door.
- The school end is the existing `TrackBuilder.Goal` arch in every level.
- Challenges (C01 to C05) are ball-skill arenas and keep their own start.
- The Holiday Run keeps its own world: all 23 stages in story order from the home street to the school gate.
