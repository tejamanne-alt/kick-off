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

## How it applies to our game

The game is a side view of a street, so the camera sees the front of everything. Assets are judged
mostly from the front and a three-quarter angle. The camera sits close and low (about 12 m back,
under 3 m up, a 34 degree lens), so the kid is about a quarter of the screen tall and the street
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
same levels in another country's streets, with that country's music, chosen in Settings, Add-ons and
Filters (Progression/AddOns, UI/AddOnsPanel); India and a Tokyo city add-on are listed as coming soon.
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
