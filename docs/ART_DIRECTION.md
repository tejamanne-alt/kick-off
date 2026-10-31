# Dribble To School: art direction

The look is clear anime daylight over a believable everyday town: a deep blue sky with big white
cumulus, clean neutral streets and buildings, fresh greens, and characters drawn so they stand
out from all of it. We borrow that *feeling* (bright, crisp, lived-in) and build every asset
ourselves. We don't reproduce any other game's assets, characters or vehicles.

## What makes the look

1. **Clear sky, little haze.** The sky is a rich cobalt overhead, paling quickly to a light blue
   at the horizon. Big white cumulus with soft blue undersides sit far off. Distance takes on only
   a little sky blue: far hills are softened, not dissolved, and nothing is tinted warm.
2. **Neutral daylight.** A high, near-white sun. Lit faces show their true colour; shade is a cool
   blue-grey, clearly darker, with a crisp but soft edge between the two (anime, not a long ramp).
   Sun shadows are cool and readable. Only the faintest bloom on the brightest highlights; the
   grade is neutral with a little extra contrast. No golden cast anywhere.
3. **True, quiet materials.** Paving and concrete are neutral greys, asphalt a cool dark grey,
   walls white, pale grey or light stucco under dark slate, charcoal, blue-grey or terracotta
   roofs. Colour comes in small, deliberate doses: a shop awning, a vending machine, a door, a
   sign, a bicycle.
4. **Chunky, simple forms with crafted detail.** Shapes are bold and softly bevelled. Detail comes
   from a few well-chosen parts (AC units, gutters, poles and wires, letterboxes, planters, bikes)
   rather than surface noise.
5. **Fresh vegetation.** Broadleaf trees are clumpy masses in varied summer greens (yellow-green
   in the sun, blue-green in the shade); conifers dark green; lawns a fresh green with a few
   flowers. Cherry blossom is an occasional accent, never the main colour.
6. **Water.** A clear turquoise to deep blue sea with white foam where it meets the sand; peachy
   sand that darkens a little where it is wet.
7. **Characters pop.** The kid is the clearest thing on screen: flat cel shading in two bands, a
   dark ink outline thicker than anyone else's, a bright rim round the silhouette, and a
   high-contrast uniform (white shirt, navy shorts) against the mid-tone street. Pedestrians use
   the same style with a lighter line.

## How it applies to our game

The game is a side view of a street, so the camera sees the front of everything. Assets are judged
mostly from the front and a three-quarter angle.

| Chapter | Mood | Light | Signature assets |
|---|---|---|---|
| 1 Home street | Fresh, clear morning | High white sun, cool shade | Gabled houses, block walls, gardens, poles and wires, trees behind |
| 2 Market | Busy, bright late morning | High sun | Shop fronts with coloured awnings, market stalls, crates of produce, flats behind |
| 3 Beach | Brilliant midday | Deepest sky, clear sea | Dunes, beach grass, palms, lifeguard tower, parasols, headlands |
| 4 Underpass and building site | Clear city day | Slightly paler sky | Tower crane, hoarding, scaffold, concrete pipes, warehouses |
| 5 Park and school | Summer afternoon | Clear, a touch warmer | Green trees, a few blossoms, birches, hedges, pond, school |

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
- **Review:** render every kit with `review_kit.py` and look at it critically before handing it over;
  check street layouts in daylight with `preview_street.py`.
