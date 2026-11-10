# Kick Off 2: art direction

The look is clear anime daylight over a believable everyday town: a deep blue sky with big white
cumulus, clean neutral streets and buildings, fresh greens, and characters drawn so they stand
out from all of it. We borrow that *feeling* (bright, crisp, lived-in) and build every asset
ourselves. We don't reproduce any other game's assets, characters or vehicles.

## What makes the look

1. **A deep cobalt sky.** On screen the sky is a rich, fairly dark cobalt, about (57, 109, 175) at the
   top of the view, and it stays deep almost to the horizon, only a little lighter there, about
   (70, 127, 190). Big white cumulus with cool cyan-grey undersides sit far off. Distance takes on a
   mid sky blue: far hills and headlands go a deeper blue (about (50, 87, 134)), they never pale
   toward white.
2. **Near-white sun, crisp shade, dark ground shadows.** A high sun, only a hair warm, so lit faces
   show their true colour and whites stay white. Shade sides are a cool blue-grey at about 0.6 of
   the lit value, with a crisp but soft edge between the two (anime, not a long ramp). Sun shadows
   cast on the ground are much deeper: a dark, cool navy at roughly a quarter to a third of the lit
   ground (road (119, 110, 114) in sun, (26, 25, 34) in a tree's shade). Contact shadows under
   people and the ball are near black. The dappled shade of trees out of the frame often lies in
   a dark band across the near road, framing the shot (StreetBuilder.CanopyShadows).
3. **Whites are paper, not light.** Nothing clips to pure white: lit white walls are about
   (227, 223, 217), the brightest highlights roll off just below white. No yellow or cream cast
   anywhere; neutral greys lean faintly mauve (asphalt about (133, 122, 126), light paving about
   (196, 190, 187)).
4. **True, quiet materials.** Paving and concrete are mid greys, asphalt a mid mauve-grey, walls
   white, pale grey or light stucco under dark slate, charcoal, blue-grey or terracotta roofs. Colour
   comes in small, deliberate, saturated doses: a shop awning, a red or blue vending machine, a door,
   a sign, a bicycle, a traffic cone.
5. **Chunky, simple forms with crafted detail.** Shapes are bold and softly bevelled. Detail comes
   from a few well-chosen parts (AC units, gutters, poles and wires, letterboxes, planters, bikes)
   rather than surface noise.
6. **Natural vegetation, with deep shade.** Broadleaf trees are broad, irregular crowns of many
   small clover-like leaf clumps gathered into a few lobes: a fresh yellow-green where the sun
   catches the outer clumps (about (103-138, 143-187, 79-89)), going very dark, nearly black-green,
   in the shade inside the crown, a ragged scalloped outline with little sky holes, and dark
   branches showing through the gaps. True leaf greens, neither olive nor lime; conifers and pruned
   garden pines a dark blue-green; hedges a deep clipped green; lawns a fresh, sunny yellow-green
   (about (150-185, 165-195, 85-115)). Cherry blossom is an occasional accent, never the main colour.
7. **Water and sand.** A soft, clear turquoise sea (about (105, 175, 201)) with crisp white foam
   lines; rosy peach sand (about (222, 187, 161)), never yellow, darker where it is wet.
8. **Characters pop.** The kid is the clearest thing on screen: flat cel shading in two bands, a
   dark ink outline thicker than anyone else's, a bright rim round the silhouette, and a
   high-contrast uniform (white shirt, navy shorts) against the mid-tone street. Pedestrians use
   the same style with a lighter line.

The numbers above are on-screen sRGB, measured from the reference shots (median of verified
swatches). The light that produces them is in `Art/ChapterTheme.cs` (per chapter) and
`World/WorldLook.cs`; the grade is `World/PostFX.cs`: a neutral balance, a toe for the deep
shadows, contrast 1.1, a shoulder from 0.84 easing to 0.972, vibrance 1.12 on quiet colours, and
faint cool shadows and mauve mid-greys. Each ground surface also has its own shadow tint
(`ArtBaker.SurfaceShadowTint`): shade on paving stays a cool slate while shade on the road goes
near black, as in the references. When the look is tuned again, measure the game's
screenshots against these numbers rather than by eye: the eye adapts, and an earlier "calmer"
pass (paler sky, olive greens, less saturation, a warm gain) drifted away from the references.

## The comic halftone filter

An optional look (Add-ons & Filters on the title screen, `World/PostFX.cs`, passes 4 and 5 of
`Shaders/PostFX.shader`) that redraws the graded picture as a printed comic, over every model in
every scene:

1. **Colour:** saturation 1.4 and contrast 1.15 on the street; the street's mid and dark tones
   stepped into cel bands (4 steps, 70 percent), the light tones left smooth so lit white walls and
   paving never break into blotches.
2. **Halftone:** a 45-degree dot screen (8.5 px a cell at 1080 lines, scaled with the screen) in
   tones below 0.66, the dots a darker, bluer ink of the colour under them; hatching in the deepest
   shade.
3. **Ink line:** from the camera's depth and normals: outlines where the depth jumps, creases where
   the surface turns. Never from the picture, so textures never draw lines. It thins away by 90 m.
4. **Print:** the red and blue plates slip up to 4 px toward the frame's edges (none at the centre),
   on warm paper with a faint grain; the vignette comes last.

**Figures keep their faces.** `ToonCharacter` writes `_ComicWorld` into the picture's alpha: 0 for
the kids, the passers-by and the ball (the cars and the bicycle are 1, drawn like the street). A
figure takes no bands, no creases and almost no plate slip, and lighter dots (45 percent), so its
painted eyes, brows and highlights stay exactly as drawn, and its own ink outline does the rest.
**Sound-effect words** (`UI/ComicPops`): the big moments pop up as hand-lettered words (Bangers)
with a thick ink stroke, a hard drop shadow, a gradient fill with halftone dots in its lower part,
and an ink starburst behind the loudest. They sit above the action, clear of the kid's face.

Previews of the real models through a numpy port of the shader are in `review/filter/`.

## The pencil sketch filter

An optional look (Add-ons & Filters, pass 6 of `Shaders/PostFX.shader`): warm drawing paper, a faint
wash of the colour, pencil hatching for the tone in up to three directions as it darkens, the sky left
open, and the outline drawn twice with a wandering offset from the depth and normals. The figures
keep their colour (75 percent) and get no creases, so the kid stands out on the page and the painted
eyes stay clean. Raising `sketchWash` from 0.12 to about 0.6 turns it into coloured pencil. Previews
are in `review/sketch/`.

## How it applies to our game

The game is a side view of a street, so the camera sees the front of everything. Assets are judged
mostly from the front and a three-quarter angle. The camera sits close and low (about 9 m back,
under 3 m up, a 34 degree lens), so the kid is about a third of the screen tall and the street
around them has real depth.

| Chapter | Mood | Light | Signature assets |
|---|---|---|---|
| 1 Home street | Fresh, clear morning | High white sun, cool shade | Gabled houses, block walls, gardens, poles and wires, trees behind |
| 2 Market | Busy, bright late morning | High sun | Shop fronts with coloured awnings, market stalls, crates of produce, flats behind |
| 3 Beach | Brilliant midday | Deepest sky, soft turquoise sea | Dunes, beach grass, palms, lifeguard tower, parasols, headlands |
| 4 Underpass and building site | Clear city day | Slightly paler sky | Tower crane, hoarding, scaffold, concrete pipes, warehouses |
| 5 Park and school | Summer afternoon | Clear, a touch warmer | Green trees, a few blossoms, birches, hedges, pond, school |

**The original town and the add-ons.** The original streets above are Kamakura, Japan: a seaside
town south of Tokyo (Japanese shop names, concrete poles, block walls, the railway). Add-ons put the
same levels in another country's streets, with that country's music, chosen in Add-ons and
Filters (Progression/AddOns, UI/AddOnsPanel); India is listed as coming soon, and Florida took the place of the Tokyo city
add-on that was listed beside it.
**California** (Santa Monica), unlocked by finishing every story level, has a `<scene>_CA` scene for
each level, built beside the original with `LevelBuildKit.California` set. It is a sunny California coast town (the Coast kit, `tools/blender/kit_buildings_cal.py`): stucco
villas and single-storey ranch houses under hipped terracotta barrel-tile roofs, white two-storey
Craftsman houses with deep front porches, white beach condos with glass balconies, beach-town shops
(a stepped-parapet surf shop, a Spanish Revival shop with arched windows and a tiled pent roof),
front gardens behind picket fences or low hedges or open to the street, wooden utility poles
(`UtilityPoleWood`), date palms along the streets and very tall, slim fan palms on the skyline, a
timber pier on concrete piles running out from the beach, and English shop signs
(`BuildingsCAAtlas.png`). A fan palm is 16.5 m tall, and the camera's top edge sits at about
2.4 m + 0.23 x the distance, so grown fan palms stand 60 m or more back (StreetBuilder.PalmSkyline),
where their crowns show over the roofs; near the street they are young ones or date palms.
**Florida** (Cocoa Beach, on the A1A), unlocked the same way, so far has only chapter 3, the beach: each of its levels has a
`<scene>_FL` scene (`LevelBuildKit.Florida`, `StreetBuilder.Florida`, the Florida kit `tools/blender/kit_buildings_fl.py`),
after the user's photographic references in `review/florida/refs` (F3-1 to F3-6, made with `docs/IMAGE_PROMPTS.md`). The kid's
beach is unchanged (the sand, the tides, the channels, the dunes and the sea about 9.6 m behind the lane: the tide's wash, the
sand's mesh and the wet sand all depend on that depth); the town stands behind it on seawall terraces running out over the
sea, a low kerb along the sand and paving on top, and the beach stays open wherever a tide or a channel crosses, a dune's
slope runs, or a stop stands, so the sea shows between the terraces and the tide still runs up from it. The strip runs in the
references' order (the restroom with its showers, the snack shack and its kayaks, the diner, the motel with its pool, the
rental shop, the Art Deco shops in pastel stucco with racing stripes, eyebrows and glass block) and each level takes it up
where the one before left off. The promenade carries sabal palms (Florida's state tree: a grey trunk with its old leaf bases,
a round crown of fan leaves), teal lamps, benches and bins; tall old sabals stand up over the roofs. The lifeguard towers are
the Florida stand, the stops' huts the snack shack, the home street before the beach the Coast kit's stucco villas with sabals
for their palms, and the school Seagrove High (cream and teal concrete block, an aluminium fence, a marquee, the US and Florida
flags). Every name on a sign is invented.

## Production rules (Blender kits)

- **Space:** metres, Z up, the model's front (the side the game camera sees) faces **-Y**. The origin
  is at the centre of the model's footprint on the ground (z = 0), unless a kit says otherwise.
- **Export:** one FBX per model with a single root object named after the model. Child empties named
  `Attach.<what>` mark attachment points (wire ends, lamp lights, hooks). Use `kit_lib.export_model`.
- **Material:** one per kit, vertex colours times the kit atlas. Keep the atlas's plain white corner
  at UV (0.97, 0.03) for flat-coloured parts; paint wear, panel lines, windows and signs into the atlas.
- **Recolourable parts:** UV channel 2, x = part id. 0 is fixed; 1 to 3 are tint groups (wall paint,
  foliage, fabric) the game can recolour at load, keeping each vertex's brightness relative to the
  part's base colour. The kit manifest records each part's base colour (sRGB).
- **Normals:** smooth or custom split normals so light falls softly. Stylized flat planes are fine on
  rocks and cliffs, as long as they are intended.
- **Budgets (triangles):** building 6,000; tree 6,000 (leaf-card crowns; 2,500 otherwise); bush 1,200; grass 800; street prop 1,500;
  boulder 600; landscape strip 6,000; gameplay structure 5,000.
- **Review:** render every kit with `review_kit.py` and look at it critically before handing it over;
  check street layouts in daylight with `preview_street.py`.
