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

## Budgets

| Item | Budget | Today |
|---|---|---|
| Playable kid body | 32k triangles; head, hands and texture seams protected | 32k (was 100k) |
| Locker Room bag | 8k triangles | 8k (was 30k) |
| Passer-by | 14k triangles | 14k (was 30k) |
| Character FBX total | | 28 MB (was 90 MB) |
| Character atlas | 2048 (kids), 1024 (bags), gaps filled for every mip | as listed |
| Skinned renderers drawn | 1 kid + 1 bag + passers-by on screen | as listed |
| Full-screen passes, Original look | grade only (bloom on High) | 1 to 8 |
| Full-screen passes, filters | comic 2, sketch 1, classic 3, plus DepthNormals | unchanged; scaled by the render scale |

**Still to do.** Each of these is a known cost, ranked by expected gain:
1. **Build only the chosen kid and the bag they wear.** Every scene still holds all six kids and their 30 bag meshes, inactive: about 3× less than before the polish, but still memory and load time.
2. **Bake the music and ambience offline.** Runtime synthesis makes about 100 MB of garbage at each scene change. Uploads are now spread at one clip per frame.
3. **Fewer draws on the title screen.** Its camera looks down the whole street (about 300 renderers). Shorten the menu street, or add per-layer cull distances.
4. **Cheaper filter normals.** Rebuild the filters' normals from depth instead of a DepthNormals pass. Run the classic cartoon's smoothing pass at half resolution on Low.
5. **Recolour outfits in the shader,** so meshes need not be readable (halves mesh memory).
6. **Shader variant warm-up** (a ShaderVariantCollection recorded in the editor). PostFX already warms its own passes.

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
