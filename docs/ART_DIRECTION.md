# Dribble To School: art direction

The reference is the look of cozy, stylized open-world driving games: warm, hazy, painterly
light over chunky, hand-crafted shapes. We borrow that *feeling* and build every asset ourselves.
We don't reproduce any other game's assets, characters or vehicles.

## What makes the look (from the reference shots)

1. **Atmosphere first.** Distance dissolves into a warm haze: every layer further away is lighter,
   less saturated and closer to the sky colour (peach, rose, lavender). Big landforms read as
   flat silhouettes stacked in depth. The horizon glows on the sun's side.
2. **Golden-hour light.** A low, warm sun (cream to apricot) against cool lilac and teal shadows.
   The shadow side is never black: it carries the sky's colour. Soft bloom around the sun and
   the brightest highlights, and a gentle rim light where surfaces turn away from the camera
   toward the sun.
3. **Chunky, simple forms with crafted detail.** Shapes are bold and slightly exaggerated (big
   tyres, thick bumpers, fat roof racks, stout trunks), softly bevelled, and never faceted by
   accident. Detail comes from a few well-chosen parts (lamps, racks, cargo, ladders, hinges,
   gutters) rather than surface noise.
4. **Painted, lived-in surfaces.** Mostly flat colour with soft gradients (darker at the bottom
   and in crevices, lighter on top), plus sparse painted wear: mud splashes, grime in seams,
   chipped edges, rust spots, sun-faded paint. No photo textures.
5. **Vegetation with clear silhouettes.** Conifers are stacks of layered, drooping fronds with a
   crisp spiky outline. Broadleaf trees are clumpy, lumpy masses with light tops and dark
   undersides, in rich seasonal colour (gold, orange, red, lime). Birch-white trunks. Grass is a
   warm golden or fresh green carpet with a soft, uneven top edge.
6. **Big, soft rocks.** Large boulders and cliffs built from a few broad planes with rounded edges,
   in lavender-grey with warm lit tops.
7. **Water.** Turquoise, clear near the edge and deeper teal further out, with a crisp white foam
   line where it meets the shore.
8. **Palette harmony.** Warm golds, oranges and creams balanced by cool lavenders, teals and blues.
   Saturated but soft. Paint colours are slightly faded and dusty, never neon.
9. **Night and weather moods.** Deep blue or violet skies with stars, warm glowing headlights and
   windows, rain streaks. Used sparingly for special levels.

## How it applies to our game

The game is a side view of a street, so the camera sees the front of everything. Assets are judged
mostly from the front and a three-quarter angle.

| Chapter | Mood | Light | Signature assets |
|---|---|---|---|
| 1 Home street | Fresh early morning | Soft gold, long shadows | Gabled houses, block walls, gardens, poles and wires, conifers behind |
| 2 Market | Busy, bright late morning | Warm, high sun | Shop fronts with awnings, market stalls, crates of produce, flats behind |
| 3 Beach | Pastel afternoon | Pink-gold, sea haze | Dunes, beach grass, palms, lifeguard tower, parasols, headlands |
| 4 Underpass and building site | Hazy, dusty | Peach haze | Tower crane, hoarding, scaffold, concrete pipes, warehouses |
| 5 Park and school | Golden autumn | Low gold sun | Red, orange and yellow trees, birches, hedges, pond, school |

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
- **Budgets (triangles):** building 6,000; tree 2,500; bush and grass 800; street prop 1,500;
  boulder 600; landscape strip 6,000; gameplay structure 5,000.
- **Review:** render every kit with `review_kit.py` (warm sun, lilac shadow, hazy sky, a ground plane)
  and look at it critically before handing it over.
