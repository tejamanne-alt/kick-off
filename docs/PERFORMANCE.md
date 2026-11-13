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
| Locker Room bag | 8k triangles | 8k (was 30k) |
| Passer-by | 14k triangles | 14k (was 30k) |
| Character FBX total | | 28 MB (was 90 MB) |
| Character atlas | 2048 (kids), 1024 (bags), gaps filled for every mip | as listed |
| Skinned renderers drawn | 1 kid + 1 bag + passers-by on screen | as listed |
| A Kamakura animal | one skinned mesh (two with far legs behind), 2,500 triangles, up to 30 bones, GPU skinned (D21) | 801 to about 2,300 triangles; 1 or 2 renderers where the rigid parts were 4 to 20 (est.: fewer draw calls, a little skinning work); not yet in a level, not yet measured on the Nord CE5 |
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
