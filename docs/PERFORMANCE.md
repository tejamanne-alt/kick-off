# Performance: tiers, budgets and how to check them

The reference phone is a **OnePlus Nord CE5**:
- Dimensity 8350 Apex, Mali-G615 MC6;
- 2392×1080 panel at 120 Hz.

The target is a steady 60 fps there, or a steady 40 fps when the governor has stepped down. "Steady" means even frame pacing, not just the average.

This first version was written without a device. Every number marked *(est.)* is an estimate from the code, and everything here must be confirmed on the phone (see "Check on the phone" below). The record of what went wrong before is in `docs/LEARNINGS.md`, section B.

## Graphics tiers (`Assets/_Game/Scripts/Core/GraphicsQuality.cs`)

Picked once per device, before the first scene loads, from the GPU name and memory:
- **High:** Adreno 7xx/8xx, Mali G710 and later, Immortalis, Xclipse or Apple, with 6 GB or more. The editor, desktop and iOS are always High.
- **Low:** under 4 GB, under six cores, or older GPUs (Adreno 5xx/60x/61x, Mali T and G5x, the first Mali-G71/G72, 1 to 4-core Mali G6x/G7x, PowerVR).
- **Medium:** everything else. The Nord CE5 is Medium.

| | Low | Medium | High |
|---|---|---|---|
| 3D picture (Android) | 720 lines | 864 lines | 1080 lines (never above the panel) |
| Sun shadows | none (contact and blob shadows stay) | hard, 1 cascade, medium resolution, 25 m | soft, 2 cascades, high resolution, 35 m |
| Bloom | off | off | on |
| Frame rate | 60, stepping down to 40 or 30 | 60 | 60 |

**On every tier:**
- The camera renders to an 8-bit target with no HDR and no MSAA.
- The graphics tiers have no screen-space shadows (`BuildScripts.ApplyTierSettings`), so the scene gets no depth pre-pass and no shadow-collect pass.
- vSync is off, so the frame-rate target and Android's frame pacing set the cadence.
- After a hitch, physics catches up at most 0.1 s.

**Render scale and touch.** The 3D picture's resolution is set with `Screen.SetResolution`, and the panel's own scaler stretches it to full screen for free. The UI keeps its layout through its CanvasScaler. Touch distances in inches use `GraphicsQuality.TouchDpi`, the panel DPI times the render scale. The resolution only changes on a whole scene load, never mid-level, and never as the Holiday Run streams a stage in.

**The governor (`FramePacer`).** Every 2 s it counts the frames that came more than 1.3 frame times late. When over a fifth are late in three windows running, it:
1. steps the tier down: shadows and bloom change at once, the resolution at the next scene load;
2. once at Low, steps the frame rate down to an even share of the panel's refresh (120 Hz: 40, then 30).

It ignores the first 6 s after a scene loads, and the time after resuming from the background. What it learns is saved. After 5 sessions at a lowered tier it tries one step up again, so one hot afternoon doesn't lower the game for good.

## Build settings (`Editor/BuildScripts.cs`, `ApplyAndroidPerformanceSettings`)

- **Optimized Frame Pacing (Swappy):** frames are shown on even vsync intervals.
- **Blit Type Auto:** no extra end-of-frame copy.
- **Frame timing stats:** on.
- **GPU skinning:** batched.
- **Incremental GC:** on.
- **Tier settings:** HDR off and cascaded (screen-space) shadows off in every tier.
- **LZ4HC compression** (LZ4 for development builds), in every build `BuildScripts` makes. On Android only an LZ4
  build uses the async upload pipeline; set the Build Profile's Compression Method to LZ4HC for the Build button too.
- **iOS:** the accelerometer is off (nothing reads it).
- **Async upload:** 4 ms a frame, a 16 MB persistent buffer (the largest texture is about 10 MB).

## Budgets

| Item | Budget | Today |
|---|---|---|
| Playable kid body | 32k triangles; head, hands and texture seams protected | 32k (was 100k), plus up to ~1k from splitting two-colour triangles (v120: 32.7k to 33.0k) |
| Locker Room bag | 8k triangles | 8k (was 30k); the two randoseru 8,000 each, seven bags a kid now (est. +0.75 MB a kid file, +4.5 MB in all; only the worn bag is loaded, so no runtime cost; not yet measured on the Nord CE5) |
| Passer-by | 14k triangles | 14k (was 30k); KM1-1's first-graders (installed, `LevelBuildKit.FirstGraders`) 13,402 and 13,357 in a 2048 atlas each, as the jogger (0.7 MB of FBX each); only where KM1-1 places them, not among the footpath's walkers; not yet measured on the Nord CE5 |
| Character FBX total | | 33 MB with the two randoseru (28 MB before; was 90 MB) |
| Character atlas | 2048 (kids), 1024 (bags), gaps filled for every mip | as listed |
| Skinned renderers drawn | 1 kid + 1 bag + passers-by on screen | as listed |
| A Kamakura street prop | carved from its own views (`km_views.py`), 1,500 triangles, its own texture | KM1-1's seventeen at 1,452 to 1,454 triangles each (the first seven, then the red machine, the recycling bins, the air-conditioner unit, the meters, the letterbox, the control cabinet, the street lamp, the ticket gate, the name board, the plain pole: the plain pole installed with the buildings), one renderer each (the barrier two); a 1024 x 1024 texture each, RGB (about 0.7 MB with mips in ETC2), the bicycle RGBA for its cut-out spokes (about 1.4 MB): about 12 MB for the sixteen, est.; a level loads only those it places; in the project (`Art/Models/Kamakura`, approved), not yet in a level, not yet measured on the Nord CE5 |
| A Kamakura potted plant | carved from its own plant views like a prop (`km_views.py`, `PLANT_ROUND`), 1,500 triangles, its own 1024 texture, RGBA for the gaps between leaves | KM1-1's eight pots (KM-G26 to G33): 1,452 to 1,454 triangles each, one renderer each, a 1024 x 1024 RGBA texture each (about 1.4 MB with mips in ETC2, so about 11 MB for the eight, est.); alpha-tested leaves, a little more fill where one is near the camera; they stand together in front of the home, so a screen shows at most the eight; approved, in the project (`Art/Models/Kamakura`), placed in KM1-1, not yet measured on the Nord CE5. KM1-1's hydrangeas (three), clipped hedge and mossy stone the same: 1,308 to 1,454 triangles, a 1024 RGBA texture each, est. |
| A Kamakura tree | carved from its own plant views (`PLANT_ROUND`), 3,000 triangles, its own 2048 RGBA texture | KM1-1's persimmon (KM-G08) 2,326 triangles, black pine (G01) 2,634, clipped garden pine (G15) 2,760 (rebuilt closed, D32); one renderer each, a 2048 x 2048 RGBA texture each (about 5.6 MB with mips in ETC2, about 17 MB for the three, est.); alpha-tested crowns; in the project, placed in KM1-1, not yet measured on the Nord CE5 |
| The Kamakura home (KM-B01) | projection-modelled from the photographic KM1-1 (`kit_buildings_km.py --install-home`), the house and its fence | 77 triangles, one renderer, the kit's 4096 x 4096 atlas as its texture (about 11 MB with mips in ETC2, est.): most of that atlas is unused now that the garden is its own models, so it is to be cropped to the home's own regions; in the project, placed in KM1-1, not yet measured on the Nord CE5 |
| A Kamakura vehicle | carved from its own views, 4,000 triangles, its own 2048 texture | the tram (KM-V01): 3,878 triangles, one renderer, a 2048 x 2048 RGB texture (about 2.7 MB with mips in ETC2), est.; in the project, not yet in a level, not yet measured on the Nord CE5. The delivery scooter (KM-V03, installed, parked in KM1-1): 2,910 triangles (its budget 3,000), one renderer, a 1024 x 1024 RGBA texture for its cut-out spokes and basket (about 1.4 MB with mips in ETC2), est.; alpha-tested, so a little more fill where it is near the camera |
| A Kamakura building or set piece | modelled from solids measured off its views (`km_views.solids`, D28), a house 5,000 triangles, a set piece 4,000, its own 2048 texture | KM1-1's beige house 4,850 triangles, little shrine 3,880, station platform 3,880 (KM-B04 to B06), and the wire gantry, carved like a prop (a pole and a lattice), 2,910 (KM-B07); a 2048 texture each, RGB for the house and shrine (about 2.7 MB with mips in ETC2), RGBA for the platform's and gantry's cut-outs (about 5.6 MB), est.; flat faces, so fewer triangles go to surfaces that were bumps; in the project (`Art/Models/Kamakura`, approved), not yet in a level, not yet measured on the Nord CE5 |
| A Kamakura level (KM1-1 Hase Lanes) | its own scene (`GeneratedContent.CityLevels`), the Kamakura kit's models placed by `KamakuraLevels` | 42 models (39 different), about 76,000 triangles in all, one renderer each but the batched stand-ins; a screen shows about 4 to 10 of them. Their textures together about 75 MB with mips in ETC2 (est.): heavy for one level on the Nord CE5. To cut before it is shown to players: crop the home's 4096 atlas to its own regions (about 11 MB to 3), the trees' textures to 1024 (about 17 MB to 4), and halve the cut-out props' textures where they stand behind fences; not yet measured on the Nord CE5 |
| KM1-3's set pieces (proposed) | projection-modelled from the photographic KM1-3 (`km_komachi.py`), one shared texture | ten models, 520 triangles in all (the gateway 200, each shop 54 to 62, the side gate 70, the cut-outs 2 to 4), one renderer each; one 4096 x 2048 texture, 54 % filled, RGBA for the cut-outs (about 11 MB with mips in ETC2, about 5 MB in ASTC 6x6; split into a small cut-out texture and the buildings' RGB one, about 5.6 MB in ETC2), est. KM1-3 as laid out: about 22,000 triangles standing and 40 to 50 MB of textures with the shops still to come, est.; not yet in the game, not yet measured on the Nord CE5 |
| KM1-4's set pieces (proposed) | projection-modelled from the photographic KM1-4 in layers at their own depths (`km_shrine_school.py`), one shared texture | nine models, 314 triangles in all (the pavilion 110, the school gate 112, the building 50, the cut-out layers 4 to 6, the wall 10 a copy, laid about 21 times along the shrine), one renderer each; one 4096 x 2048 texture, RGBA for the cut-outs (about 11 MB with mips in ETC2, about 5 MB in ASTC 6x6), est. With the ginkgo (2,678 triangles) and the cherry (2,830), each with its own 2048 RGBA texture (about 5.6 MB each in ETC2): KM1-4 as laid out about 15,000 triangles standing and about 35 MB of textures with what is still to come, est.; the grounds layer covers much of the screen behind the lane with alpha-tested pixels (a little more fill); not yet in the game, not yet measured on the Nord CE5 |
| KM2-1's set pieces (proposed) | projection-modelled from the photographic KM2-1 (`km_surf_lane.py`), one shared texture | ten models, 218 triangles in all (the houses and the hut 52 to 66, the tunnel 14, the cut-outs 2 to 4, the embankment wall 4 a copy, laid about nine times), one renderer each; one 4096 x 2048 texture, RGBA for the cut-outs (about 11 MB with mips in ETC2, about 5 MB in ASTC 6x6), est. KM2-1 as laid out: about 16,000 triangles standing (the home and the kit's models) and about 40 MB of textures with what is still to come, est.; not yet in the game, not yet measured on the Nord CE5 |
| KM2-2's set pieces (proposed) | projection-modelled from the photographic KM2-2 (`km_beach.py`), one shared texture | ten models, 184 triangles in all (the lifeguard tower 144 in boxes and faces, the sea wall 10, the cut-outs 2 to 6; the sea wall laid twice), one renderer each; one 4096 x 2048 texture, RGBA for the cut-outs (about 11 MB with mips in ETC2, about 5 MB in ASTC 6x6), est. KM2-2 as laid out: about 11,500 triangles standing (the dune grass, seven clumps, and the kit's pole) and about 25 MB of textures with what is still to come, est.; not yet in the game, not yet measured on the Nord CE5 |
| KM2-3's set pieces (proposed) | projection-modelled from the photographic KM2-3 (`km_whitebait.py`), one shared texture | ten models, 349 triangles in all (the drying rack 108 in its parts, the shop 56, the neighbour's houses 49, the boxes, crates and sea wall 36 to 44, the cut-outs 2 to 4), one renderer each; one 4096 x 2048 texture, RGBA for the cut-outs (about 11 MB with mips in ETC2, about 5 MB in ASTC 6x6), est. KM2-3 as laid out: about 15,000 triangles standing (the kit's seven pots, pole and scooter) and about 25 MB of textures, est.; not yet in the game, not yet measured on the Nord CE5 |
| KM1-2's ride set (proposed) | from the photographic KM1-2a to c (`km_ride.py`), one shared texture | five models, 30 triangles (the car 22: its wall, benches, floor and ceiling; four cut-outs of 2), one renderer each; one 4096 x 2048 texture, RGBA, the pictures at half their size (about 11 MB with mips in ETC2, about 5 MB in ASTC 6x6), est.; the ride's camera is fixed, so the whole set is on screen at once; not yet in the game, not yet measured on the Nord CE5 |
| Kamakura's lanes (in the game) | each lane picture as one front and its ground (`km_lanes.py`), one texture a leg | 41 models of 4 triangles (nine legs: KM1-3 and KM1-4 three each, the rest five), one renderer each, 20 triangles a leg; one texture a leg, 4096 x 2048 RGB (KM1-4's 4096 x 1024), about 5 MB with mips in ASTC 6x6 or 5.6 MB in ETC2, one leg loaded at a time, est. The fronts are opaque and stand behind everything (no alpha test, little overdraw); each front fills the screen's upper half behind the lane. Not yet measured on the Nord CE5 |
| Kamakura's mini-games (in the game) | uGUI layers built in code (`MiniGames/`), the set pictures in `Resources/UI/Kamakura` | the ride: three pictures, 2048 x 508 (the car, RGBA), 2048 x 508 and 2048 x 338, about 1.5 MB in ASTC 6x6, est.; the errand: 2048 x 683 and 2560 x 512 (imported at 2048 wide), about 1 MB, est. Loaded only on their legs (Resources, by name), no mipmaps. While a layer is open the run is held, so its frame is the level's still frame plus one canvas (about 12 to 20 images and texts, one draw call a picture). The kite thief adds three small Blobs models and a wave strip. Not yet measured on the Nord CE5 |
| Kamakura's map (in the game) | `Resources/UI/KamakuraMap.jpg`, 3200 x 1800, imported as the town map's | about 3.5 MB with no mipmaps in ASTC 6x6, est., on the map screen only (the original town's map is not loaded with it); the layout is 12 nodes on three routes |
| Kamakura's animals (in the game) | the reviewed animals (`kit_animals_km.py`), installed as their own kit (`install_km_animals.py`) | 43 models of 801 to 2,296 triangles, one skinned mesh each (two where far legs stand behind), up to 17 deforming bones, GPU skinned; one shared 2048 x 2048 RGBA cut-out texture (about 2.5 MB with mips in ASTC 6x6, est.; it was 4096, cut to what the camera can use); 1 to 6 placed in a leg (about 2,000 to 9,000 triangles), plus the Shiba or the tanuki as the dog; at most 12 animals awake at once (AmbientAgent's sleep margin), est.; not yet measured on the Nord CE5 |
| The June rain (route 3) | one mesh of streaks (`World/RainFall`), built once, moved whole each frame, the wires' Sprites/Default material | 720 streaks (360 on Low): 2,880 vertices, 1,440 triangles, one draw call, no vertex touched after it is built; each streak a few pixels wide and faded along its length (little overdraw, blended); in the Holiday Run one stage's rain draws at a time, est.; not yet measured on the Nord CE5 |
| Kamakura's Holiday Run | ten stages (`HolidayStages.Kamakura`), each its leg's lane pictures fitted to 120 m | per stage: its lane texture (about 5 MB with mips in ASTC 6x6; two stages loaded at once, about 10 MB), its obstacles as the original run's, 2 or 3 animals; KM1-1's stage its frontage (about 76,000 triangles as in the leg, est.); a lap of 1.2 km, ten scenes in the build instead of 23 (the original stages are no longer built while the switch is on); not yet measured on the Nord CE5 |
| A Kamakura animal | one skinned mesh (two with far legs behind), 2,500 triangles, up to 30 bones, GPU skinned (D21) | 801 to 2,296 triangles, at most 17 deforming bones; 1 or 2 renderers where the rigid parts were 4 to 20 (est.: fewer draw calls, a little skinning work). A flyer's wingbeat (`WingStroke`) and a squirrel's bound (`LegGait.Bound`) add a few sines and quaternion products per animal per frame, and at most 12 animals are awake (est.: negligible); not yet in a level, not yet measured on the Nord CE5 |
| Character meshes in memory per scene | the chosen kid and the bag they wear | about 46k vertices, ~7 MB, plus 2 atlases (was 545k vertices, ~83 MB, plus 11 atlases, since every kid and bag was saved into every scene) |
| Full-screen passes, Original look | grade only (bloom on High) | 1 to 8 |
| Full-screen passes, filters | comic 2, sketch 1, classic 3, plus DepthNormals | unchanged; scaled by the render scale |

**Loading only what is shown.** Every scene still contains all six kids and their bags (`CharacterChoice` and `BagWear` switch them), but the builder saves their renderers empty. A `LazyRenderer` loads the mesh and material from `Resources/Cast/<Model>/<Renderer>` (a `CastPart`) while the object is shown and lets them go when it is hidden. So only the chosen kid and the bag they wear are in memory. When the menu switches kids, it frees the old one a second after the last switch (the sweep was a hitch on every tap). Co-op ghosts load their kid as they appear.

## The November 2026 audit: what each change saves (est., to be measured)

None of these changes what is drawn, played or how the game plays (`docs/LEARNINGS.md` B8).

| Change | Where it pays | Saving *(est.)* |
|---|---|---|
| The 3D menu street draws nothing under the map screen's opaque mat | map screen | 1–2 ms GPU (Original), 3–6 ms (filters), 0.5–1.5 ms render thread |
| Tide washes rebuild only on screen and when changed | Low Tide, Sandcastle Sprint | 0.3–0.45 ms a frame, 3–4 fewer mesh uploads |
| Breaking-wave crests, fountains, crossings, springboards, darkness, collected coins rest | every level | 0.05–0.1 ms a frame |
| Sky dome drawn after the opaque geometry | every look | 0.1–0.2 ms GPU |
| Story HUD's clear fade not drawn; HUD rects and texts written on change | every level, Holiday Run | 0.1–0.5 ms GPU and canvas |
| Fields, Sea and the menu's field cast no shadows; far hills and clouds receive none | Medium, High | 0.05–0.15 ms |
| Passer-by recolour precomputed (one multiply a channel) | each walker's respawn | 0.5–0.7 ms spike down to about 0.2 ms |
| Audio generators reuse their buffers; cue samples freed after upload | every new place (6 a Holiday lap) | 170 → 113 MB of garbage (Market), 13–25 MB less elsewhere; up to 8 MB less held per place |
| Holiday stage meshes destroyed with their stage | Holiday Run | 25–90 MB a lap that no longer accumulates |
| LZ4HC builds | every load, Holiday streaming | texture uploads off the main frame on Android |
| Analytics written on a worker thread | each event | 0.2–1 ms, and a 5–20 ms trim every 200 events |
| Map picture read in the background from the title screen | opening the map | 15–50 ms hitch (+3–6 MB on the title screen) |
| Kid picker frees the old kid a second after the last tap | each tap | most of a 60–200 ms hitch |
| Async upload buffer 32 → 16 MB | always | 16 MB of RAM |
| Per-frame garbage: the input delegate, challenge strings, coach signature | levels | about 4 KB/s and 2 KB/s fewer allocations |
| *(cost, v119)* `CharacterRig` ground contact: ~140 surface points a posed model character | every scene with characters | +0.01 to 0.03 ms a character a frame (est.); no garbage |
| *(v122)* California's 28 `_CA` scenes no longer built; Florida's climate baked into its scenes' light | build size; Florida's scenes | 39 level scenes instead of 67, and the Coast models only California used (B7; measure the APK); the climate costs nothing (the same shader inputs) |

**Still to do.** Each of these is a known cost, ranked by expected gain. The audit reports behind them (with file and line,
the fix and the risk of each) are summarised in PROGRESS "The audit: work nobody sees".
1. **Bake the music and ambience offline.** Runtime synthesis still makes 80–115 MB of garbage at each new place, and 0.8–1.2 s of worker time. The output is deterministic, so a bake plays the same samples; Vorbis needs a listening A/B against PCM on the phone first.
2. **Holiday Run stage wake.** A stage wakes in one frame and combines its street in the next, every ~30 s of running (est. 10–50 ms). Measure (`ProfilerMarker`s), then spread the wake over frames or batch at build time.
3. **Cheaper filter normals.** The DepthNormals pass draws every opaque renderer again. Rebuilding normals from depth only pays when the filters read the main pass's own depth buffer (1–3 ms render thread). Classic needs only the centre normal (low risk); comic and sketch creases need a visual check.
4. **Classic cartoon, the same output for less** (1–2 ms): skip pass 8's smoothing on the sky, drop its `pow`s (the figure mask is 0 or 1), and in pass 9 read depths only where a cel is near. Needs a shader compile and a screenshot diff.
5. **Synchronous scene loads** freeze 1–3 s with nothing on screen: one async loader with an overlay.
6. **Menu canvas animations:** the looping pulses and bobs re-batch the whole menu canvas every frame (0.2–1 ms). Give each its own nested canvas, with a raycaster where it holds a button, and test every button.
7. **Title screen draws** (about 300 renderers): cull distances can't hide anything unseen; baked occlusion culling can. About 47 m of the menu street never shows in any shot.
8. **Readable meshes:** every FBX is imported readable for runtime tinting (5–15 MB per scene). Recolour in the shader (outfits, kits, cars), then turn readability off.
9. **Ground and water noise** (0.35–0.5 ms): 12 hashes a pixel could be a baked texture, but only within 1/255, so it needs a look.
10. **Co-op and haptics JNI:** cache the method IDs; decode only what each event needs.
11. **Unpinned settings:** "Optimize Mesh Data" (it could strip the UV1 that tints read), graphics APIs, ASTC, the quality level, and iOS's tier settings (iOS still has screen-space shadows: a look change, so decide first).
12. **Shader variant warm-up** (a ShaderVariantCollection recorded in the editor). PostFX already warms its own passes.

## Check on the phone

1. Make a release build (not Development; `BuildScripts` "Run on Connected Phone").
2. Turn the screen recorder off while measuring.
3. In logcat, look for the boot line `[Graphics] <GPU>, <MB> MB: device tier ..., tier ..., 60 fps, WxH`. It shows the tier and resolution chosen.
4. Play Up the Hill and the title screen for 2 minutes in each look. Note:
   - the frame rate;
   - whether frames are even (Perfetto, or `adb shell dumpsys SurfaceFlinger --latency`);
   - any `[Graphics] stepped down` lines.
5. Check that touches land where the finger is and that swipes feel the same at 864 lines (the Medium tier).
6. Write the results into `PROGRESS.md`.
