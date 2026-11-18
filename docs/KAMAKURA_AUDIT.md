# Kamakura audit: what in its 23 levels and 5 challenges is not yet Kamakura (November 2026, after v126)

Measured against the user's brief (`docs/KAMAKURA_BRIEF.md`). Done the way Florida's was (LEARNINGS D10): every track piece each
layout calls, every street and set piece, the stops, home and school, the people, animals, sounds and words. Sources: a read of
the builders (`StreetBuilder*.cs`, `LevelBuildKit*.cs`, `GreyboxLevels.cs`, `Audio/`, `Localization/StringTables.cs`), review sheets
of the shared kits, and all five chapters rendered through the game camera (`preview_street.py --kamakura`). Nothing here was
run in Unity. Per-level wall variants (bins, crates) were worked out from `LevelSalt`, not seen.

Verdicts: **W** wrong for Kamakura (Western, American or British things, English signs, wrong species or season),
**G** generic but plausible in Japan, **B** a grey box (a primitive standing for an object).

## The short answer

v126 made Kamakura's **streets** Japanese: houses, shops, walls, gardens, the shopping street, the temple ground, the tram
line, the trees, kites and crows. Almost nothing a level **does** was touched:

- **Track pieces:** only one has a Kamakura branch (the swooping bird is now a black kite, `LevelBuildKit.cs:2287`). There is
  no `KamakuraLook`, the counterpart of Florida's `MiamiLook`. So every slide-under, wall, ramp, crossing, car, gate and
  sign is the shared town's.
- **Start and finish:** the stops, the kid's home and the school have no Kamakura branch (`StreetBuilder.Stops.cs`,
  `StreetBuilder.Home.cs`, `LevelBuildKit.cs:3909-4047`). Every level therefore starts or ends at one of these:
  - a picket-fenced house with wheelie bins;
  - "ST MARY'S CHURCH" with a spire;
  - a glass bus shelter;
  - a brick "STATION";
  - a bandstand;
  - "ALLOTMENTS";
  - a red-brick school with a clock tower under a "SCHOOL" banner.
- **People, sound and words:**
  - The walkers wear the shared wardrobes.
  - The park sings with robins, blackbirds and wood pigeons, and the street rings a church bell.
  - L13 is "Seagull Bay", though its birds are now kites.
  - Every board is in English.
- **Music:** already Japanese (city pop, yonanuki tunes, koto and flute). Nothing to change.

**One bug from v126, fixed with this audit:** in Kamakura's home street, the road's edge lines, centre dashes, drains and
manholes sat 14 cm under the asphalt. v126 laid the lane flush, but the markings were still placed at the old sunken road's
height (`StreetBuilder.cs:173`; LEARNINGS E13).

## 1. What every level starts and ends at

Route stops are listed in `RouteTable.cs:166-187` and `:254-259`.

| Place | Levels | Now | Verdict | Kamakura version |
|---|---|---|---|---|
| Home (the kid's house, also on the map) | start of L01 L06 L11 L15 L16 L19 | Buildings `HouseGable`, picket fence and gate, wheelie bins, round post box, broadleaf tree; route sign "X → via Home Street" (`StreetBuilder.Home.cs:34-93`) | W | `HouseTileKM` behind `BlockWallKM` and `GateKM`, `PotShelfKM`, a persimmon, a name plate (`KamakuraFront`/`KamakuraGarden` already do this) |
| Bus stop | L01 → L02 | glass shelter of primitives, "BUS STOP", "TIMES", round "BUS" plate, litter bin (`Stops.cs:207-234`) | W, B | `BusStopPoleKM` (modelled, never placed: しおかぜバス) and a bench |
| Granny's | L02 → L03 | weatherboard `Bungalow`, picket fence, "Granny's" (`Stops.cs:307-327`) | W | `HouseOldKM`, `BoardFenceKM`, `GateKM`, hydrangeas |
| Church | L03 → L04 | stone nave, spire and cross, "ST MARY'S CHURCH" (`Stops.cs:362-448`) | W | a shrine or temple: `ToriiKM`, `StoneStepsKM`, `StoneLanternKM`, `ShrineHallKM`, `EmaRackKM`, cedars |
| Sam's house | L04 → L05 | `HouseFlat`, picket fence (`Stops.cs:333-355`) | W | `HouseMetalKM` or `HouseCarportKM` with a block wall |
| Bakery, post office, florist, library | L06–L10 | the town's café, a dental surgery, florist and bookshop under English boards (`Stops.cs:71-106`) | W | Japanese boards; the bakery as `ShopWagashiKM`; to model: a post office (〒), a florist, a small library |
| Surf school, beach café, lifeguard | L11–L13 | garage huts, "SURF SCHOOL", "BEACH CAFE", the shared lifeguard tower, a palm (`Stops.cs:474-557`) | W/G | a 海の家 beach hut, a 監視所 on stilts, black pines (surf shops may keep English names) |
| Station | L15 → L18 | the brick warehouse, a red band and "STATION", a clock disc, a swan-neck lamp (`Stops.cs:566-588`) | W, B | a small timber tram station with its name board and `TramKM` at the platform (to model) |
| Site office | L16 → L17 | cabin, portaloo, mixer, "SITE OFFICE" | G | Japanese board 現場事務所 |
| Bandstand | L19 → L20 | Leisure `Gazebo`, a Victorian `ParkLamp`, "BANDSTAND" (`Stops.cs:612-626`) | W | an azumaya pavilion (to model) and stone lanterns |
| Park café | L20 → L21 | the town café, "PARK CAFE" | W | `ShopTeaKM` |
| Boathouse | L21 → L22 | a garage, duck pond, raft, "BOATHOUSE" | G/W | a rental-boat hut on a lotus pond |
| Allotments | L22 → L23 | garage shed, picket fence, birch, "ALLOTMENTS" | W | a vegetable plot: `CorrugatedShedKM`, bamboo or board fence |
| School | the goal of L05 L10 L14 L17 L18 L23 C03 | Works `SchoolArch` (a stone arch), Buildings `School` (red brick, clock tower), "SCHOOL" banner (`LevelBuildKit.cs:3937-4043`) | W | to model: a concrete gate post with an invented kanji name plate and a rolling gate; a white three-storey school with its clock |

The people at the stops (`LevelBuildKit.Stops.cs:93-160`) are W/G:

- Granny is the hijab model in a headscarf.
- Grandpa wears tweed.
- The builder and the lifeguard are the courier model.

## 2. Track pieces (`GreyboxLevels.cs` → `LevelBuildKit.cs`)

| Piece | Levels | Now | Verdict | Kamakura version |
|---|---|---|---|---|
| Slide-under `AppleBough` | L03 L04 | a garden apple tree (apples don't grow in Kamakura) | W | a pine or persimmon bough on a bamboo crutch |
| `StallAwning` | L06 L07 L10 | striped fruit stall with oranges, lemons, bananas | W | a vegetable table under a plain canopy, or a sembei shop's table |
| `BarrowCart` | L08 L09 | a costermonger's barrow of melons and loaves | W | `RickshawKM` (modelled, never placed) |
| `WashingLine` | L05 | British H-frame clothes posts | W | a 物干し pole with futons, from `LaundryPoleKM` |
| `OakBough` | L20 L22 | an English oak with ivy | W | a camphor bough on a crutch, with a shimenawa |
| `BoatTrestles` | L12 L14 | a clinker rowing boat | G/W | a white FRP fishing boat on beach rollers |
| `ScaffoldGantry` | L15 L16 | netted scaffold, orange banner | G | mesh sheet with a 安全第一 banner |
| `RollShutter` | L06 L08 L10 | shutter with an apple sign | G | blank or Japanese sign |
| `FallenTrunk` | L19 L23 | a broadleaf log | G | a cedar log |
| Others (`PlankTrestles`, `BoomBarrier`, `AccessPlatform`, `DeliveryConveyor`, `Boardwalk`, `SurfRack`, `RescueBoardStand`, `SiteBarrier`, `PipeRack`, `BeamTrestles`, `NetTunnel`, `PlayTower`, `WobbleBridge`) | | | G | none needed |
| Wall (chapter 1) | L02 L03 L05 | a pair of round litter bins (Japan has almost none on its streets) | W | a crow-net rubbish point or `PotShelfKM` |
| Wall (beach), L12 | L12 | a boulder under a "Sandcastle!" sign | mismatch | the Leisure `SandCastle` |
| Wall (park) | chapter 5 | a hedge block | G | `MossWallKM` |
| ParkedCar | L02 ×4, L04, L05 ×2, L10 | a European hatchback in red, blue, green, yellow or purple | G | `KeiCarKM` in white, silver, black or pastel; check it against the 3.3 m collider and give it wheel meshes for `Car()` |
| Crossing | L07 ×3, L09, L10 ×3, L23 | cobbled side street (chapter 2); stop line on the left half (right-hand traffic); yellow centre dashes; vans, 4×4s and pickups crossing (`StreetBuilder.cs:238-267`, `LevelBuildKit.cs:1728`) | W | asphalt; stop line on the right half; white dashes; cars offset for driving on the left; `KeiCarKM`, `KeiTruckKM`, `ScooterKM` |
| SiteExit | L16 ×2 | brick pillars; a banksman with an English STOP/GO board (a British custom); a pickup (`Site.cs:65-87`) | W | a traffic guard (交通誘導員) in navy and a white helmet with a red flag; `KeiTruckKM` |
| Builder | L16 | courier model in hi-vis polo, shorts and a cap | W | long work trousers, white helmet, mesh vest |
| Awning | L06 L08 L09 ×2 L10 | a red box on a grey post | B | a faded shop canvas awning or eave (to model) |
| Platform, Ramp | L03 L08 L09 L15 L16 L17 L18 L21 L23 C04 | concrete boxes ("Shop steps", "stall roof", "School steps!") | B | stone steps, a shop's step, site staging, school steps |
| Water (park) | L20 L21 L22 L23 | a stream with traffic cones and a road barrier | B/mismatch | a stone-edged stream with stepping stones, no cones |
| Tunnel | L18 ×2, L23 | red-train plates | G | the tram's green and cream |
| Checkpoint | all story levels | white pennant on a steel pole | G | `NoboriKM` banner |
| Sign | every level | Leisure notice board with English text, some British words ("Kerb", "Zebra crossing… GREEN man", "banksman", "Seagulls swoop low") | G board, W words | a 掲示板 with a little roof (to model); reword the lines whose objects change |
| Target, SlalomGate | C02 C03 C04 | bullseyes ("Hit every shop sign"); primitive bars and hoops | G, B | hanging wooden shop signboards; beach flag poles with a rope |
| CoveredWalkway | L15 ×2 | hoarding with a procedural roof | G/B | white steel site panels |
| Swing | L21 ×3, L23 | rope swing on a generic broadleaf | G | a camphor |
| Dog | L19–L23 | honey-coloured retriever type; loose in temple grounds | G | a Shiba variant; on leads (a gameplay call) |
| Pit, Puddle, Sand, Tide, Wind, Crate, Fountain, Springboard, MovingPlatform | | | G/OK | none needed |

## 3. The streets themselves (what v126 did not reach)

| Chapter | Still placed in Kamakura | Verdict | Kamakura version |
|---|---|---|---|
| 1 Home street | swan-neck `StreetLamp` and round `Bin` every 21 m (`StreetBuilder.cs:1536`) | W | an LED lamp on the utility pole (to model) |
| | gap fillers: shared block wall, pillar, broadleaf or conifer (`1068`) | W | `BlockWallKM`, KM trees |
| | side-street trees: broadleaf and birch (`890`) | W | cherry in leaf, camphor |
| | plain concrete poles | G | a pole with a transformer and crowded wires (to model) |
| | `ConvexMirrorKM`, `ManholeKM`, `TactileStripKM` never placed | | at side-street mouths, in the road, at crossings |
| 2 Market | cobbled lane and side streets (`72`, `238`, `862`) | W | asphalt or tiled paving |
| | swan-neck lamps between shops (`1979`) | W | shopping-street lamps (to model) or lanterns |
| | lemon-tree pot, wheelie bins, orange crates, sacks between shops (`1984-1994`) | W/G | `PotShelfKM`, `NoboriKM`, `ScooterKM`, mikan crates |
| | the konbini's blank red and blue vending machines (`1904`) | G | `VendingKM`, `VendingKM2` |
| | "KANATA 24" konbini, "MINAMO" boutique: romaji signs | G | Japanese-script signs |
| 3 Beach | the shared `LifeguardTower` (`2226`) | W | a 監視所 hut on stilts (to model) |
| | standing herring gulls and gull flocks (`1293`, `1451`) | W next to the kites | kites perched on posts and pines; soaring kites |
| | palms by the school (`1137`, `2113`) | W | black pines |
| | the sea wall is a concrete box (`2089`) | B | a stepped sea wall with tetrapods (to model) |
| 4 Site and city | the corrugated `Warehouse` lots (`1008`, `2476`) | W | a small workshop or garage-shop (to model) |
| | a tall shop and the boutique pair (`2463`) | G | `ShopKissaKM` or a small mixed-use block |
| | mesh site fence, British skip, portaloo (`2447`, `2525`) | G | white 仮囲い panels with 安全第一 |
| | the tram line at z 12.5 may run through the backs of the deepest lots: unconfirmed | ? | check in Unity |
| 5 Park | `CherryBlossom` in flower in May, broadleaf, birch (`2585`) | W | `CherryLeaf`, camphor, cedar |
| | octagonal `Gazebo` bandstand (`2672`), picnic tables, cast-iron benches | W/G | azumaya, timber or stone benches |
| | mallards on the duck pond | G | spot-billed ducks with ducklings, koi, a heron |
| | red squirrel with ear tufts | W | Pallas's squirrel (grey-brown) |
| Holiday Run | spruce forest and snowy mountain ranges not gated on Kamakura (`StreetBuilder.Holiday.cs:414`); palms, `ParkLamp`, wheelie bins, post box in its theme lots | W | as `DistantHills` does; black pines, lanterns |
| Menu street | chapter 1's street; the far side is a flat green field (`LevelBuildKit.Menu.cs:79`) | B | a row of KM house fronts |
| Town map | an American grid suburb: orange roofs, lawns, palms, the spire, a bandstand, "Elm Street", "Hill Road", "Station Road" (`Resources/UI/TownMap.jpg`, `TownMapLayout.json`) | W | re-render from the KM kits once the scenes change; invented Japanese street names |
| Rides | none for Kamakura | | a tram ride from `TramKM` (as Miami's people mover) |

## 4. People, animals, sound and words

**People:**

- **Walkers:** shared bright wardrobes (`LevelBuildKit.cs:748-806`); Florida has its own, Kamakura has none.
  - The hijab shopkeeper walks one turn in six.
  - Hair includes blond and ginger.
  - The courier wears a backwards cap and shorts.
  - A parent walks the child to school; in Japan children walk in groups, in yellow caps with randoseru.
  - Fix: a Kamakura wardrobe like `MiamiTops`. A May morning is navy, white, beige and grey, with a Cool Biz salaryman.
- **Might add:** a surfer cycling with a board on a side rack, a monk sweeping, a crossing volunteer with a yellow flag.
- **Faces:** whether the passer-by scans read as East Asian needs eyes on the models.

**Animals:**

- OK: kites, crows and pigeons on the ground, crabs and butterflies.
- Wrong or generic:
  - Gulls on the beach.
  - Crow flocks that fly the gull model.
  - A Eurasian red squirrel.
  - Mallards.
  - Always the same ginger cat (fine, but vary the coats).
  - A retriever type rather than a Shiba.

**Sound** (`Audio/AmbienceGenerator.cs`):

- Wrong:
  - Robin and great tit on the menu.
  - A church bell (`:620`) and a wood pigeon in the street.
  - A shop door bell in the market (Japanese shops have sliding doors).
  - Herring gulls on the beach.
  - Robin, blackbird and wood pigeon in the park (`:670-673`).
  - A hammered school bell (Japan plays the "kin-kon-kan-kon" chime).
  - A square-wave crossing beep (Japan's crossings chirp "piyo-piyo").
- Missing:
  - Crows and the kite's "pīhyororo".
  - Bush warbler, bulbul, turtle dove.
  - A temple bell.
  - The level crossing's "kan-kan" and the tram's horn.
  - A bamboo water spout in the temple ground.
- OK: music, sparrows, tits, the site, the buoy bell and ship horn, and the 50 Hz hum (eastern Japan).

**Words:**

- **Seagulls, now kites:** "Seagull Bay" (L13), the "Cheeky Gull… three chips" sticker, the seagull coach and tutorial lines, and chapter 3's "Sand, waves and seagulls". Kamakura really posts "beware of kites" signs: "Cheeky Kite".
- **Traffic direction:** the L07 sticker says "Look left, look right"; Japan drives on the left and teaches right, left, right.
- **School bell:** L23's sticker is a hand bell, "Ding-dong".
- **Names:** the stop names "Church", "Bandstand", "Boathouse", "Allotments", the route names "Home Street / Market Street / Seaside Road / Park Path" and the map's street names are English.
- **Spanish:** the Spanish table mirrors all of this.
- **Font:** in-world Japanese can only be baked into kit textures; there is no Japanese font for TextMesh.

**Traffic:** cars are not shown driving on the left (see Crossing). No moving tram; the level crossings never close, flash or ring.

## 5. Per level

| Level | Wrong or grey-box items |
|---|---|
| L01 | home front; goal: bus shelter with English boards |
| L02 | bus shelter; litter-bin wall; 4 hatchbacks; goal: Granny's picket fence |
| L03 | Granny's; apple bough; litter-bin walls ×2; ramp (box); goal: St Mary's |
| L04 | St Mary's; apple bough; hatchback; gates with brick pillars; goal: Sam's picket fence |
| L05 | Sam's; washing line; litter-bin wall; 2 hatchbacks; goal: brick school, "SCHOOL" |
| L06 | home front; fruit-stall awning; red-box awning; goal: "BAKERY" |
| L07 | bakery; 3 crossings (cobbles, right-hand traffic, pickups); fruit stall; goal: "POST OFFICE" on a dental surgery |
| L08 | post office; barrow; shop steps and ramp (boxes); awning (box); goal: "FLOWERS" |
| L09 | florist; barrow; 2 awnings and a "stall roof" (boxes); crossing; goal: "LIBRARY" on a bookshop |
| L10 | library; fruit stall; 3 crossings; awning; hatchback; goal: school |
| L11 | home front; goal: "SURF SCHOOL" garage hut |
| L12 | boulder signed "Sandcastle!"; rowing boat; goal: shared lifeguard tower |
| L13 | "Seagull Bay" and its sign (the birds are kites); goal: "BEACH CAFE" kiosk with a palm |
| L14 | rowing boat; goal: school beside palms |
| L15 | home front; 2 ramps and a platform (boxes); hoarding walkway; goal: brick "STATION" |
| L16 | home front; 2 site exits (STOP/GO banksman, pickup); builder in shorts; 4 ramps and 2 platforms (boxes); goal: "SITE OFFICE" |
| L17 | ramp (box); goal: school |
| L18 | brick station; 2 tunnels with red-train plates; 2 ramps and a platform (boxes); goal: school |
| L19 | home front; goal: bandstand with a Victorian lamp |
| L20 | bandstand; oak bough; park stream with cones; goal: "PARK CAFE" |
| L21 | 2 streams with cones; "Climbing frame" (box); goal: "BOATHOUSE" |
| L22 | oak bough; pond trenches with cones; goal: "ALLOTMENTS" |
| L23 | allotments; stream with cones; "School steps!" (box); goal: school |
| C01, C05 | English sign only |
| C02 | bullseyes for "shop signs" |
| C03 | slalom bars and hoops (boxes); goal: school |
| C04 | 2 ramps and a platform (boxes) |
| Every level | English boards, shared walkers, park and street birdsong of an English town |

## 6. What to do, in order of how much Kamakura it buys

1. **The stops, home and school** (seen at the start and end of every level). This needs KM branches in `StopFront`, `HomeFront` and the goal, from existing models where they fit:
   - shrine for the church;
   - bus pole;
   - Japanese houses for Granny, Sam and home;
   - tea house for the park café.
   
   To model:
   - the station;
   - the school and its gate;
   - the post office, florist and library;
   - the beach hut and lifeguard hut;
   - the pavilion.
   
   Every board baked in Japanese.
2. **Sound:** a Kamakura set of cues: crows, kites, bush warbler, bulbul, turtle dove, temple bell, crossing "kan-kan", the chime for the school bell. No modelling, so cheap.
3. **A `KamakuraLook` for track pieces**, as `MiamiLook`:
   - KM slide-unders for the apple bough, fruit stall, barrow (the rickshaw), washing line and oak bough;
   - real awnings, steps and stepping-stone streams instead of boxes and cones;
   - kei cars and trucks;
   - the site's traffic guard.
   
   Plus a test like `MiamiKitTests`.
4. **Gulls to kites** everywhere (beach, flocks, every word), and the left-hand traffic fixes (stop line, dashes, cars, the L07 sticker).
5. **The walkers' Kamakura wardrobe** and the builder; the squirrel, the ducks, the dog.
6. **The streets' leftovers:**
   - lamps;
   - market cobbles;
   - lifeguard tower;
   - warehouses;
   - park trees in flower;
   - bandstand;
   - Holiday Run's mountains;
   - menu street's field;
   - mirrors, manholes and tactile strips placed.
7. **A moving tram** with working crossings, a Kamakura tram ride, and the map re-rendered with Japanese street names.

### Questions for the user before fixing

- **Names:** keep the English names of places and people ("Sam's house", "Granny's") as part of the story, with Japanese boards in the world?
- **Signs:** should the in-level tutorial signs stay as UI in the player's language, or become in-world Japanese boards with the words in the HUD?
- **Lifeguard:** Kamakura's beaches are usually staffed only in July and August, so a lifeguard in May is unlikely. Keep it, or make it a surf-rescue hut?
- **Dogs:** loose dogs in a temple park are unlikely in Japan. Should they get owners and leads, which changes their play?
