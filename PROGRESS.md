# Build Progress

This file is the resume point. A new session should read it first. All eight phases are done, followed by the Holiday Run (endless mode), the new touch controls and the double jump and slide polish (see "Holiday Run, controls and animation"), and Co-op over Bluetooth (see "Co-op over Bluetooth"); next comes on-device playtesting and tuning (see "After Phase 8").

## Status

| Phase | Scope | State |
|---|---|---|
| 1 | Kid controller, ball physics, dribble, slingshot kick, test track | Done |
| 2 | Level flow: checkpoints, lose/respawn, bell timer, results, pause, camera | Done |
| 3 | Hazard system + Chapters 1-2 (L01-L10) | Done |
| 4 | Coins, stickers, save system, shop, cosmetics, chapter map (uGUI kit) | Done |
| 5 | Chapters 3-5 (L11-L23) + ball skill challenges | Done |
| 6 | Procedural storybook art, kid animation, parallax, FX, synthesized audio, haptics | Done |
| 7 | uGUI HUD/menus, settings, tutorial, localization, accessibility | Done |
| 8 | Store service + full-game unlock, analytics, perf, Android/iOS build setup | Done |

## Conventions (keep these)

- **Read `docs/LEARNINGS.md` first** (every past mistake, its cause and its rule) and `docs/PERFORMANCE.md` (device tiers and budgets). Add a learning whenever something has to be fixed, reverted or redone.
- **Scenes are generated.** `Editor/GeneratedContent.cs` holds the level table (chapter, id, name, scene, bell, streak target, layout). `Editor/GreyboxLevels.cs` holds the layouts, and `Editor/LevelBuildKit.cs` holds the track pieces and the gameplay rig. Bump `GeneratedContent.Version` whenever layouts or the rig change.
- **Compile check without Unity.** Scripts are compiled with Mono `mcs` against the UnityEngine 2021.3 module DLLs (NuGet `UnityEngine.Modules`) and `UnityEditor.dll` (NuGet `Unity3D.SDK` 2021.1). The Unity 6 renames (`linearVelocity`, `linearDamping`, `angularDamping`) are mapped back by sed, and the Input System is stubbed. Four configs: legacy input, Input System, editor and tests (with an NUnit stub). Stay at C# 7.3 (no target-typed `new`, no switch expressions).
- **Presentation listens to `Core/GameEvents`.** Gameplay raises typed events; audio, FX, haptics and analytics subscribe to them.
- Restartable objects implement `IResettable`. `LevelManager.BeginRun` resets them; respawning at a checkpoint doesn't.
- The compile check also references `UnityEngine.UI.dll` (NuGet `Unity3D.UnityEngine.UI` 2020.3) and Mono's `netstandard.dll` facade. The Input System stub includes `InputSystemUIInputModule`.
- **One component per file, named like it.** Every MonoBehaviour and ScriptableObject is in a file called `<ClassName>.cs`, alone (`Tests/Editor/ScriptConventionTests.cs` checks it). Unity can only point a scene at a script by its file name: a component in another file is saved into the generated scenes with a script reference that cannot be resolved, and the player then stops while loading them with `The file '...' is corrupted! Remove it and launch unity again! [Position out of bounds!]`. (The Holiday Run's four markers once shared `RunMarkers.cs`, which did exactly that.) Plain classes, enums and structs can share files.
- **Menus are uGUI built from code** with `UI/Kit/UIKit.cs`: canvas at 1920x1080 matched on height, procedural sprites, `UIButtonFx` presses, `UIPopIn` entrances. No prefabs.
- **The shop's contents** live in `Editor/CosmeticsTable.cs`. Cosmetic art is drawn at runtime by `Cosmetics/CosmeticArt.cs`.
- **Progress** is saved to `persistentDataPath/save.json` by `Progression/SaveSystem.cs` (atomic write, corrupt files backed up). Coin economy constants are in `Progression/Rewards.cs`.
- **Art is code.** `Art/ProceduralArt.cs` draws everything on `Art/PixelCanvas.cs` (anti-aliased shapes, ink outline, watercolour grain, wrap-aware tiling). `Editor/ArtBaker.cs` bakes it to `Assets/_Game/Art/Generated` (FullRect meshes, 9-slice borders). Chapter palettes are in `Art/ChapterTheme.cs`.
- **Previewing art and audio without Unity.** The scratchpad harnesses compile ProceduralArt/Synth against tiny Unity stubs (a Color/Vector2/Mathf/Perlin reimplementation) and render PNG/WAV. Use them to eyeball changes before committing.
- **Audio is code.** `Audio/Synth.cs`, `SoundBank.cs` (29 SFX), `Mixdown.cs` (stereo tracks, reverb, filters, noise), `Instruments.cs`, `MusicGenerator.cs` (7 loops) and `AmbienceGenerator.cs` (13 beds and their cues: Kamakura's seven, Miami's six) are pure C#. `AudioDirector` (auto-booted, DontDestroyOnLoad) maps GameEvents to SFX and haptics, and crossfades the music and ambience of the place (`Soundscape`, by route).
- **All UI text goes through `Localization/Loc.T(key)`.** Tables live in `Localization/StringTables.cs` (en, es). Lose reasons are keys (`lose.*`); level names are `level.<id>`.
- No Cinemachine yet: `CameraRig/CameraFollow2D.cs` covers look-ahead, the dead zone and bounds.

## Phase 3 summary

- Hazards (`Scripts/Hazards`): Pedestrian (bounces the ball, the kid passes), Crossing with traffic light and passing car (red = lose), Dog (chases low balls and noses them back), SlowZone (puddle/sand), WindArea (headwind or updraft, optional gusts), MovingPlatform (carries the kid via `IMovingSurface`), BallSwitch + Gate, Springboard (flush trigger pad).
- Chapter 1 Home Street: L01 Out the Door, L02 Parked Cars, L03 Up the Hill, L04 Garden Gate, L05 Puddle Lane.
- Chapter 2 Market and Crossings: L06 Market Morning, L07 First Crossing, L08 Corner Shop, L09 Fruit Stalls, L10 Rush Hour.

## Phase 4 summary

- Coins (kid or ball collects; restored on restart) and one hidden sticker per level (often placed high, so a kicked ball can collect it).
- 3rd star = beat the bell + hit the streak target + collect every coin. (Changed later: see "One stick, a guided tour, and a Controls page"; the third star is now every coin and the sticker, on its own.)
- Rewards: coins collected + 1 per perfect touch + 10 per new star + 15 per new sticker + 10 for collecting every coin.
- `FrontEnd` scene (the first scene in the build) has three screens. Title has a bouncing equipped ball, Play and Locker Room. The Chapter Map has a winding path of nodes with stars, locks and a pulsing next level, plus chapter tabs. The Locker Room covers balls, flags, outfits and trails, with buy and equip.
- Levels: the kid wears the equipped outfit, has a flag on the backpack, and the ball shows its skin and trail.
- Editor menu: Open Menu, Reset Save Data, Give 1000 Coins (testing).

## Phase 5 summary

- New hazards:
  - Seagull: swoops and knocks the ball.
  - Tide: water that rises and falls, with a lose zone.
  - DarkZone + DarknessOverlay: a light pool around the kid inside tunnels.
  - PipeSpawner: rolling pipes.
  - SwingPlatform: a pendulum seat that carries the kid.
  - Fountain: an updraft WindArea with a spray visual.
- Challenges (`Scripts/Challenges`): `ChallengeObjective` base (clock, score, star thresholds, lower-is-better), JuggleChallenge (kid stands still via `KidController.autoRun`), AccuracyChallenge with ChallengeTarget, SlalomChallenge with SlalomGate (low bars and hoops, +3 s per miss, finishes at the GoalZone).
- Challenges are optional. One per chapter, unlocked by the chapter's first story level and skipped by "Next level". They show as gold "!" nodes on the map. A 0-star challenge result is not saved.
- Chapter 3 The Beach: L11 Boardwalk, L12 Low Tide, L13 Seagull Bay, L14 Sandcastle Sprint, C03 Beach Slalom.
- Chapter 4 Underpass: L15 The Underpass, L16 Building Site, L17 Cranes, L18 Tunnel Run, C04 Site Targets.
- Chapter 5 Park & School: L19 Park Gates, L20 Fountain Square, L21 Playground, L22 Duck Pond, L23 The Final Bell, C05 Juggle Champion.
- Also C01 Keepy-Uppy (Ch1) and C02 Window Shopping (Ch2). Total: 23 story levels + 5 challenges.

## Phase 6 summary

- Storybook look for every scene:
  - Inked paper blocks (9-sliced) and wooden crates.
  - Tiled ground with a chapter edge: grass, cobbles, sand, kerb or park path.
  - Drawn cars, dogs, gulls and pedestrians.
  - Wooden signposts.
- Parallax backdrop per chapter: a sky gradient and sun on the camera, drifting clouds, a far strip (hills, towers, sea or skyline), mid props (houses, shops, palms, huts, cranes, pillars, trees, the school) and a near strip (hedges, bunting, dune grass, site fence).
- The kid is a paper-doll rig (CharacterRig + KidAnimator): run cycle, idle breathing, jump and fall poses, kick swing, landing squash, celebration and stumble. Pedestrians walk with WalkerAnimator.
- Ball: squash and stretch along velocity and on impacts (BallVisual), plus a ground shadow.
- FX: pooled sprite particles (FxPool) driven by FxDirector. Dust, sparkles, splashes, feathers and confetti, screen shake (can be turned off in settings), a slow-motion goal moment, and the camera zooms out while aiming.
- Audio: synthesized SFX for every event, lo-fi music per chapter plus a menu theme, a referee whistle at the start and the school bell.
- Haptics: Taptic Engine on iOS (`Assets/Plugins/iOS/DTSHaptics.mm`), short amplitude vibrations on Android.
- GameSettings gained music and SFX volume, haptics, screen shake, left-handed, colour-blind aim and language (the UI comes in Phase 7).

## Phase 7 summary

- In-level HUD is now uGUI (`UI/GameHud.cs`):
  - Info card (level, timer, bell clock, coins, streak or challenge status) and a round pause button.
  - Drawn jump button and brake zone, which follow the left-handed setting.
  - Aim meter, toasts, Ready/GO and the respawn fade.
  - Pause menu, and an animated results screen: stars pop in with chimes, coins count up, then Retry / Map / Next.
- Developer tuning sliders moved to `UI/DevTuningPanel.cs`. They only exist in the editor and development builds (Tab key or the Tune button).
- Menus:
  - Title has Play, Locker Room, Stickers, Settings and Credits, plus a first-launch splash.
  - Sticker Album (`FrontEnd/AlbumScreen.cs`) shows procedural die-cut stickers per level (`UI/StickerArt.cs`).
  - Shared Settings modal (`UI/SettingsPanel.cs`): music and SFX volume, vibration, screen shake, school bell (cozy mode), left-handed, colour-blind aim, language, and reset progress with a confirmation.
- Localization: every UI string is shipped in English and Spanish, with device-language detection. Changing language rebuilds the open screens.
- Tutorial: `Tutorial/TutorialHint.cs` triggers show a once-per-player hint card the first time each mechanic appears. There are 18 hints, placed in L01, L04-L07, L09, L12, L13, L15-L17, L19-L21 and C01.
- Accessibility: large touch targets, left-handed mirroring, colour-blind trajectory colours, and toggles for screen shake, vibration and the bell timer.

## Phase 8 summary

- Business model (Option A): `Store/Monetization.cs`, `IStoreService`, `MockStore` (dev purchases succeed; release builds report unavailable), and `UnityIapStore` (IAP 4.x, compiled only with the `DTS_UNITY_IAP` define). The unlock panel shows the localized price, Buy and Restore. Chapters after chapter 1 are gated only when `RequireUnlock` is on (off by default).
- Analytics: `Analytics/AnalyticsService.cs` (local JSON-lines file plus the console in dev; add sinks for a backend) and `AnalyticsTracker` covering app_open, level_start, level_complete, level_quit, ball_lost (with x position, for balancing) and purchase.
- Performance: the HUD only rebuilds text when values change; profiler markers on FX and music upload; menus let the screen sleep while levels keep it awake; pooled particles and allocation-free physics queries throughout.
- Build: `Editor/BuildScripts.cs` applies store player settings, sets the rendered app icon (the procedural one if the art is missing), signs from environment variables, and offers menu and CI builds (AAB, dev APK, iOS). The iOS privacy manifest is at `Assets/Plugins/iOS/PrivacyInfo.xcprivacy`.
- `docs/RELEASE.md` has the full release guide, store listing copy, privacy answers and a checklist.

## Post-phase work

- Runtime review: 11 issues found and fixed (lose-zone placement on L17, the L22 gap, cozy-mode lateness, GameInput across scene loads, tunnel coverage, crash-safe saves, analytics quit events, UI animation delays, trail on respawn, button pulse jitter, settings left open after resume).
- Edit-mode tests in `Assets/_Game/Tests/Editor` cover content tables, localization parity, challenge rules, and the generated audio and art.
- First device playtest feedback:
  - Controls: the kid no longer auto-runs. ◀ ▶ buttons walk back and forward, and letting go stops and traps the ball. Dribbling works in both directions and the kid turns around.
  - The kick moved from "touch the ball" to a KICK button left of JUMP: drag the way the ball should go (forward or back), or tap for a quick pass. The button glows when the ball is in reach.
  - A ball kicked back past the level start is lost, and play resumes at the last checkpoint. The start wall stops the kid but not the ball. The "left the ball behind" rule is gone, because you can walk back for it.
  - Signs: posts are now planted in the ground under each sign, with two legs on wide boards. Signs over gaps move to the near edge. SCHOOL hangs as a banner on the gate. The ball gate slides up into a wooden frame instead of floating.
  - Ground and pit fills now reach below the camera's lowest view, so no sky colour shows under the level.
- Character animation: arms and legs are now two pieces each (thigh and shin, upper arm and forearm), with knee and elbow joints and shirt-coloured sleeves. The kid's run folds the knee in the swing and plants a straight leg, and the arms drive with bent elbows. The jump tucks the knee, the kick cocks the knee back and then snaps it straight, and landings crouch. Pedestrians stroll with soft knees. All of this is `RigPose` in `CharacterRig`.
- Art direction moved to an anime look, matching the reference shots:
  - `Art/CharacterArt.cs` draws the teen (512 px per unit, cel-shaded, thin line).
  - `Art/SceneryArt.cs` draws the deep-blue skies, cumulus clouds, per-chapter far strips, large mid props, the tileable utility-pole line and the near strips.
  - Chapter 1's ground is now asphalt with a white kerb.
  - The menu sky matches.
  - The kid wears shorts with bare knees and long socks, and has smooth hair (a rounded cap, a soft fringe at the brow and a shine band). His head is a little bigger so he reads as younger. Adults keep long trousers.
- Real-world scale: about 0.9 m per unit, so the kid is 1.4 m (1.55 units).
  - Mid-layer props are drawn at true size. `PixelCanvas` can render the same drawing code larger at full sharpness.
  - Sizes: house 7.5 m to the ridge, shops 7 m, school about 9 m plus its clock tower, apartments 13 m, overpass clearance 5.8 m.
  - Vending machines 1.85 m, utility poles 10 m tall and about 21 m apart.
  - The parked car is 3 m long (its colliders were updated to match, and it is still jumpable). Adults are 1.7 m.
- Crossings: a side street running away from the camera with a pedestrian signal (green man, flashing green man, red man).
  - Cars are drawn front-on and moved in depth. They queue at the stop line while the man is green, then drive through the crossing and past the camera on red.
  - This replaces a car that drove along the pavement.
- Fountains are plaza floor fountains: three pulsing jets from a flush grate, with splash droplets.
  - The lift follows the visible jet height (`Hazards/Fountain.cs`), replacing a wind column beside a basin.
- Fix: every level had been built with chapter 1 scenery.
  - Cause: creating each new scene could unload the level definition, so `def != null` failed and the chapter fell back to 1.
  - The chapter is now passed in from the level table, and the shared assets are reloaded per level.
- The background house row leaves the side street clear at crossings, while the crossing is near screen centre (`BlocksOpenArea`).
- The tide is a tapering lens of sea with a foam crest that washes over darker wet sand and sloshes gently, replacing a flat blue box.
- 3D street (generated content v17):
  - The camera is now perspective (FOV 30, slight downward pitch). Physics stays 2D on z = 0, and the kick feel no longer depends on the camera size.
  - `Scripts/World`: procedural meshes for street slabs (strips by depth, kerbs, end caps), boxes, houses (four roof styles, facade submesh), pole lines with LineRenderer wires, the look globals (sun, haze) and static batching.
  - `Shaders/Toon.shader` (cel bands, world-space texture projection, haze) and `Shaders/SpriteHaze.shader` for cut-outs.
  - `Art/SurfaceArt.cs`: tileable asphalt, paving, kerb, cobbles, sand, gravel, grass, concrete, block wall, roof tiles, sea and hoarding textures, plus facades for houses, shops, apartments, the school and warehouses.
  - `Editor/StreetBuilder.cs`: per-chapter strips and scenery. Crossings are real side streets with zebra stripes; cars drive along them in depth. Holes, the tide, the tunnel, fountains and the goal are 3D.
  - Remaining 2D cut-outs: characters, the ball, trees, clouds, and small decor (switch posts, swings, pipes, springboards).
- 3D characters and props (generated content v18):
  - Kid and pedestrians are one skinned mesh each (`World/SkinBuilder`, `Presentation/CharacterBody3D`): tubes blended across the knee and elbow, ellipsoid head, eyes, hair shell with fringe and shine. Outfit changes rebuild the mesh. `CharacterRig` keeps its base scale (adults were being reset to kid size) and squashes in depth too.
  - Facing turns through the camera (`CharacterRig.FacingYaw`) for the kid, pedestrians, dog and gull.
  - 3D ball (skin texture projected on the front), coins, parked and crossing cars (`World/Car3D`), pipes, switch lamp, sign boards, posts and frames (`Decor` is now a 3D box), swing A-frame, springboard, targets, slalom gates, dog and seagull (`World/BlobShape`). `World/Tint` recolours sprites or 3D parts.
  - Ground shadows for the kid and ball (`Presentation/GroundShadow`).
  - The 2D paper-doll parts and the unused car, dog and seagull sprites are gone.
- Controls and type: `UI/Kit/TouchButton` see-through glass buttons (no border, faint tint, soft white icons) that brighten and shrink when held, with a faint ripple and a halo on KICK when the ball is in reach; haptic click on press and soft tap on release (`Haptics.Press/Release`, rigid/soft styles on iOS, predefined effects on Android). Menu buttons push down onto a base. Fonts: Lilita One (display) and Varela Round (body).
- Footpath layout (generated content v19), from playtest feedback:
  - The kid runs on the footpath (z = 0) with the house walls behind and the two-lane road in front, toward the camera. The road (edge lines, centre dashes, manholes) and the strip behind the footpath never break.
  - Gaps open holes only in the footpath lane: drain works with a pipe, dark walls, a concrete lip, safety cones before and after and a striped barrier. Water gaps are rain-flooded trenches (a tidal stream on the beach). Raised ground makes a stepped walkway with a retaining wall above the road.
  - Puddles and soft sand are irregular shapes (`World/PuddleShape`) with wet rims and reflected sky.
  - Footpath obstacles look real: stone steps, flower planters, stacked drinks crates; rocks on the beach and hedges in the park (`TrackBuilder.Obstacle`).
  - The gate is a sliding steel gate with a no-entry sign, buzzed open by kicking the ball at an intercom on a gooseneck post (a push-button bollard when low). `Gate` can slide a panel aside and switch its collider off.
  - Decor is kept out of the kid's line or is solid: pedestrians and the dog walk just behind it, signs, flags, poles, pipes and target posts stand at the back of the footpath.
  - The level ends at the school's front gate: a stone arch with a tiled roof and name board in the school wall, gates open, the school across the yard.
- Beach, underpass, school and sky (generated content v20):
  - Tides wash up from the sea: `World/TideWash` is a sheet of sea with a foam edge whose front runs up the sand from the water's edge and over the path at high water, curling back toward the sea at its ends (`World/Shoreline`), over darker wet sand with a wavy edge (`World/WavyStrip`). The lose zone still rises with the tide.
  - The beach is 3D: lifeguard towers, parasols (`World/ParasolShape`) with towels and cool boxes, wet rocks at the water's edge, dune grass, foam along the shore and lines of breaking crests out at sea.
  - The sand is one smooth surface (generated content v36): `World/SandField` works it out from the ground spans and `World/SandDunes` meshes it with smooth normals. Steps ease into S-curved slopes (at most about 22 degrees) with colliders that follow the curve. Raised ground swells into dunes that roll off both sides of the lane, gentle hummocks lie away from the path (none where the tide comes in), and the wet sand runs on under the sea, so the foam meets the sand at the waterline. Props stand on the sand where they are (`TrackBuilder.SandHeight`). The beach levels have no pits; rocks on the dunes take their place.
  - Clouds are 3D cumulus (`World/CloudShape`): flat bottoms, piled tops, cel-shaded with blue-grey undersides, with little haze (`_Haze` on the toon shader).
  - The underpass is evenly dim (no spotlight round the kid) and lit by lamps under the deck whose additive light cones and floor pools light whoever walks under them (`World/LampGlow`).
  - The level ends when the kid and the ball are both through the school gate (`GoalZone`). The school stands across the end of the road: its gate arch faces back down the footpath at the kid, bollards close the road, the building faces down the street.
- The kid is made in Blender (`tools/blender`): a skin-modifier body with one subdivision, a rounded head with a painted anime face (atlas texture), soft hair clumps with a shine band, a cut-out shirt with sleeves, tie, shorts, long socks, sneakers, a school bag with its strap; an armature with bone-heat weights (clothes copy the body's weights); about 17k triangles; exported as `Art/Models/Kid.fbx` with `KidAtlas.png`.
  - `ModelImportSettings` imports it in metres without materials or clips, readable, bones kept as transforms.
  - `LevelBuildKit.BuildKidModel` turns it to face +x, sizes it, and maps its bones to the `CharacterRig` (front = the limbs nearer the camera). The procedural kid remains as a fallback.
  - `CharacterRig` now swings each joint about the body's side axis measured from the joint's rest pose, so it drives imported bones and the procedural pivots alike.
  - `ModelOutfit` recolours the shirt and shorts for the shop's outfits from part ids in UV channel 2.
- Pedestrians are the Blender-made adult (`Art/Models/Adult.fbx`, `kid.py --adult`): adult proportions, long sleeves, trousers, leather shoes, a side parting. `ModelOutfit` dresses each one when the level loads (coat, trousers and hair colours; hair is part 3). Both models carry a Nose marker bone so the builder knows which way they face.
- The playable characters are two original teens made in Blender (`tools/blender/teen.py` and its modules), in a soft hand-painted anime style. The girl (`Art/Models/Girl.fbx`) has a chestnut high ponytail with a yellow scrunchie, freckles, a sky-blue blouse with a rounded white collar, a navy pleated skirt that follows her legs, knee socks, loafers and a yellow backpack. The boy (`Art/Models/Boy.fbx`) has short dark hair with a quiff and a cowlick, a plaster on his cheek, a green ringer T-shirt, khaki shorts, red sneakers and a navy backpack. Both have oblong-oval faces painted at 4x and downscaled, sculpted bodies with mitten hands, and fitted hair with tapered locks. Both are built into each level; `Presentation/CharacterChoice` shows the one picked in Settings → Player (saved as `GameSettings.Character`) and passes the shop's outfits to both. The school uniform keeps each model's own clothes (`IOutfit.ResetOutfit`); other outfits recolour the top (part 1) and the skirt or shorts (part 2), starting from the colours in each model's `.json`. The pennant sits on whichever backpack is showing. The younger kid (`Kid.fbx`) is the fallback. Four primary-school kids joined the teens later: see "The player roster and the primary-school kids" below.
- The sky is painted (`ProceduralArt.Sky`, 512 x 256): the chapter colours deepening upward, a glowing haze on the horizon, soft horizontal brush streaks and wisps of high cirrus behind the 3D cumulus.

## Realism and cozy pass

- The level ends as soon as the kid and the ball are both through the school gate: the goal covers the whole school ground past the arch, at any height.
- A ball the kid can no longer reach sends the run back to the last checkpoint with "The ball can't be reached" (`lose.unreachable`). That happens when it goes over a locked gate while the kid is still on this side (`Gate` is an `IBallStrander`), or when it comes to rest on top of the gate or the underpass deck (`Core/BallTrap`). `LevelManager` waits `strandedDelay` (1.2 s) before acting.
- Side streets run far back from the footpath, and the second rows of houses and flats (and the distant cranes) now leave a gap for them, so no building stands on a road.
- Moving platforms always have a visible cause:
  - Building sites: a pallet hanging from a tower crane, which slews its jib and runs its trolley to follow the load (`World/CraneRig`).
  - Vertical lifts: a builder's hoist climbing a rack mast.
  - Park and beach water: a plank raft on a ferry rope between bank posts.
- Springboards are round garden trampolines.
- The park's swing crossings are rope swings hanging from a tree over a stream (water instead of a dry pit).
- The Cranes level reads as a building site with trenches, crane-carried pallets and a builder's lift.
- Warm sunlight against cool shadows, with soft cel edges and a gentle sky fill in both toon shaders (`_DtsSunColor`, set by `WorldLook.sunColor`).
- Cars are original Blender models (`tools/blender/car.py`, `Art/Models/Cars`): a hatchback for parked cars (repainted in softened colours by `World/CarPaint`), and a van, an estate with roof-rack cargo, a small pickup and a compact off-roader for side-street traffic in their own paint. Their wheels roll as they drive (`World/WheelSpin`). The procedural `Car3D` remains as the fallback.
- Building fronts get 3D dressing lined up with their painted facades: sills and lintels, window boxes of flowers, door canopies with lamps and potted plants, downpipes, and balconies with railings, plants and towels on the flats.

## Painterly world and asset kits

The look follows `docs/ART_DIRECTION.md`: clear anime daylight (generated content v37; it was a golden-hour haze before playtesting showed it tinted everything yellow and hid the kid). In v38 the palette was measured against the reference shots and calmed: olive summer greens instead of bright lime (leaves, grass, hedges, palms), a lighter cerulean sky, deeper neutral-cool shade, slightly warm greys, and a grade with 0.88 saturation and 1.12 contrast. The ball is 34 cm across (`LevelBuildKit.BallRadius`), larger than a real 22 cm football so it reads at a glance on a phone. In v39 the camera moved in, like the references: a 34 degree lens about 12 m back and under 3 m up, showing 7.2 m of height at the kid (it was 9.6 m from 18 m back), so the kid is about a quarter of the screen tall with their feet low in the frame and about 10 m of street ahead of them. Narrower screens (16:9, tablets) pull back just enough to keep at least 14 m of street in view (`CameraFollow2D.minHalfWidth`).
- **Light and air:** the toon shaders share `Shaders/DtsLook.cginc`:
  - a near-white sun with a crisp, slightly soft step into cool blue-grey shade;
  - shade tinted by the sky above and a neutral bounce from the ground below;
  - a rim light;
  - soft real-time sun shadows;
  - a little blue distance haze that eases out over about 700 m.
  
  The rest of the atmosphere:
  - `WorldLook` sets the light per chapter (`ChapterTheme.mood`): a fresh morning, a bright late morning, a brilliant beach midday, a clear city day and a summer afternoon.
  - A sky dome draws a deep blue gradient paling to the horizon; the sun sits high, so only its glow shows.
  - `PostFX` adds a faint bloom, a neutral grade with a little extra contrast and a light vignette.
- **Kick-style round (generated content v43):**
  - Trees are crowns of many small clover-leaf clumps on cut-out cards over a dark core, with branches showing through (`kit_plants_leaves.py`, `Toon.shader` `_ALPHATEST_ON`); new BroadleafWide, BroadleafSmall, BroadleafYoung and a cloud-pruned GardenPine.
  - The town has eight new shopfronts with invented names (a small supermarket, a café, a bookshop, a florist, a noodle house, a convenience store, two narrow tiled buildings), three new house types and new street props (A-frame boards, banner flags, utility boxes, bike racks, bins, pots), dealt so nothing repeats too soon (`kit_buildings_town.py`, `kit_street_m4.py`).
  - The teens are slim anime students: white short-sleeved shirt, long navy trousers (the girl a pleated skirt), dark hair, white sneakers; the boy carries a satchel.
  - The kid can slide (SLIDE button, swipe down, S/Down) under obstacles drawn for each chapter (`TrackBuilder.SlideUnder`), and double jump.
  - Side streets end at a T-junction with a back road and buildings; lots, shopfronts and back-row buildings never straddle a step in the ground; ground steps read as retaining walls; clouds paint their own white and cyan shade (`_Lighting` 0.25 on the cloud material).
- **Characters stand out:** the kid has the boldest ink outline and a bright rim round the whole silhouette (`ToonCharacter`, set per material in `ArtBaker.CharacterMaterial`). The teens are modelled in the school uniform (a white shirt, navy trousers or skirt, a red tie), which is also what the school outfit is (`CosmeticApplier` resets to the model's own clothes for it); before, the boy was modelled in a sage shirt and khaki shorts, the same tones as the grass and paths.
- **Ground:** the surfaces are painterly 512 px tiles over 8 x 8 units, wrapping both ways (`Art/GroundArt.cs`):
  - asphalt with repairs and sealed cracks;
  - neutral grey bevelled paving with moss in the joints;
  - irregular cobbles;
  - peachy rippled sand with shells;
  - fresh green clumpy lawn with flowers;
  - light gravel with a few leaves;
  - turquoise to deep blue water.
  
  The toon shader adds world-scale patches (`_Macro`), so the repeat never shows.
- **Asset kits:** seven kits of original Blender models replace the procedural boxes, blobs and flat cut-outs. Each has one atlas, a manifest and recolourable parts (`tools/blender/kit_*.py`, `Art/Models/<Kit>/`).

  | Kit | Models | What's in it |
  |---|---|---|
  | Plants | 19 | Trees, bushes, hedges, grasses and flowers. They sway in the breeze by a baked wind weight. |
  | Buildings | 9 | Houses, shops, flats, warehouse, school, garage. Recoloured from curated paint schemes. |
  | Street | 36 | Poles and wires, lamps, walls, fences, hoardings, vending machines, signals, road furniture, pots, crates. |
  | Terrain | 19 | Rocks, piles, cliffs, a headland, and the far landscape: rows that tile seamlessly at 70, 230, 440 and 640 m. |
  | Leisure | 24 | Beach life, the park's playground, pond, bandstand and lamps. Also gameplay pieces: trampoline, swings, fountain, raft, signs, flags, targets. |
  | Works | 29 | The sliding gate, bollard and intercom, the crane load and hoist, pipes, underpass, school arch, and building-site yards. |
  | Animals | 12 | The dog, gulls, wildlife with idle motions (`World/CritterIdle`), and the coin, sticker and star. |

  `LevelBuildKit.KitModel` places a model facing the camera through its `Attach.Front` marker, and `ModelTint` recolours its parts. Every placement falls back to the old procedural look if a model is missing. Gameplay pieces keep their exact colliders, pivots and slides.
- **Preview:** `tools/blender/preview_street.py` lays the kits out the way the street builder does and renders a stretch of each chapter through the game camera. Use it to judge layout and scale without Unity.

## Kick Off: the front end in the game's look

The game is now called **Kick Off** (product name, logo, credits, store text, en + es). It was later renamed **Kick Off 2**, with the app id `com.astradite.kickoff2`: the "2" reads as "to" (kick off to school), not a sequel, and the logo letters it in sunny yellow after OFF. Code namespaces, shader names, the save file and its keys, the IAP product id and the bundle id are unchanged.

- **Launch screen:** a live 3D scene, not a flat backdrop. `LevelBuildKit.BuildMenuStage` (Editor/LevelBuildKit.Menu.cs, called by `GeneratedContent.BuildFrontEndScene`) builds chapter 1's camera look, the sky dome with cumulus round where the menu camera looks, the home street running away down the left (StreetBuilder), and every playable kid under a `CharacterChoice` on the footpath with a ball. `FrontEnd/MenuStage` frames the kid (by their height in `PlayerRoster`) in a screen rect each screen gives (title: right of the button column; Locker Room: the showcase; map and album: tilted up to the sky), eases between shots and drifts. `FrontEnd/MenuKid` does keepy-uppy (foot, foot, thigh) on the `CharacterRig`. If the stage can't be built, the menu paints a flat daylight sky (`MenuBackdrop`). **Kick Off > Rebuild Menu (FrontEnd)** rebuilds just this scene.
- **Logo:** `UI/KickOffLogo`, built in code: Lilita One "KICK OFF" leaning forward with a gradient face, navy extrusion and thick ink outline (`UI/Kit/UILogoText`, one mesh), on a turf badge with the centre circle chalked on it (`ProceduralSprites.PitchBadge`), a ball flying in on chalk speed lines, and the tagline on a slanted ribbon.
- **Kit:** `UITheme`/`UIKit` restyled: slightly see-through white panels and bold buttons with a thin dark line (`ProceduralSprites.RoundedEdge`, `CircleEdge`), logo-style titles, navy ribbon headers on modals (`UIKit.Header`), section labels, `UIKit.Row`/`Fit` for computed layouts, `UISafeArea` for notches. Pause, results, unlock and the HUD's cards use it too.
- **Player:** `UI/PlayerPicker`: a card for each kid of `Core/PlayerRoster` (a row for the high-school teens, a row for the primary-school kids) with portraits of the real models (`tools/blender/portrait_teen.py` into `Resources/UI`, imported as sprites by `Editor/UiArtImportSettings`). From the title screen (tap the kid or the player card) and in the Locker Room; Settings shows the chosen kid and opens the same picker. `GameSettings.Character` drives the menu kid and every level's `CharacterChoice` live.
- **Settings:** two columns of grouped rows (Audio; Gameplay; Player; Language) with fixed row heights in columns that stretch with the card, labels that shrink to fit; fits 4:3 to 21:9 in both languages.
- **Locker Room:** the 3D teen stands in the showcase on the left trying on the selected outfit, flag or ball (`CosmeticApplier.Preview`), with the item card below and the tabs and grid on a white panel on the right.
- **App icon:** redrawn in the daylight look (sky, cumulus, pitch with the centre circle, the ball on speed lines).

## Stickers worth collecting

- **23 stickers**, one per story level and themed to it, in `Resources/UI/Stickers/L01..L23.png` (512 px die-cut vinyl: badge in the chapter colour with a sunburst, the subject popping out, a blank name ribbon the UI letters in the player's language, a thick border). Made by `tools/blender/sticker_art.py` (renders the real kit models, cars, the boy and a modelled hand bell in the toon look) and `sticker_compose.py` (PIL). `UI/StickerBook` holds each sticker's rarity (12 normal, 6 holo, 5 gold for the chapter finales) and loads the art (the old procedural badge is the fallback); strings are `sticker.<level>`, `.text`, `.hint`.
- **Rewards:** `CosmeticItem.unlock` (Coins / StickerSet / StickerCount) and `unlockValue`. Eleven items in `CosmeticsTable` are earned, never sold: a set reward per chapter (Home Street Hero ball, Market Day outfit, Surf's Up ball, Site Safety flag, Cherry Blossom outfit) and collector rewards at 5 (Confetti trail), 10 (Gold Seal flag), 15 (Holo Foil ball), 20 (Holo Streak trail) and 23 (Golden Album ball and Album Legend outfit). Two patterns were added at the end of `CosmeticPattern` (Holo, Foil) so saved numbers don't shift. `Cosmetics/StickerRewards` works rewards out from the stickers in the save; the menu grants anything earned but not owned when it loads (`FrontEndController`) and celebrates it once (`UI/StickerRewardPanel`), so older saves catch up. The save format is unchanged.
- **UI:** the album is a collector's book (`FrontEnd/AlbumScreen`); `UI/StickerView` draws a sticker (shadow, art, lettered ribbon, masked `UISheen` on holo and gold, silhouette when missing); `UI/StickerDetail` is the close-up (tilting with `UIWobble`, flavour line, where it was found, what it counts toward; for a missing one the hint and Play this level). The Locker Room shows sticker rewards with a sticker and "Find 3 more stickers" / "Complete set: The Beach (2/4)", and its button opens the album. In levels, the pickup badge shows the level's sticker on its face (`Pickups/Sticker`).

## Holiday Run, controls and animation

**Nothing in this section has been run in Unity or on a device.** It was written and checked with the Mono compile harness (four configs: legacy input, Input System, editor, tests), numeric replicas of the layout and stage-table checks, and Blender renders of the poses. The first-run checklist is in [`docs/HOLIDAY_RUN.md`](docs/HOLIDAY_RUN.md#what-has-been-checked-and-what-has-not).

- **Touch controls (`Input/GameInput.cs`).** The three action buttons used to sit in a row; sliding and kicking were easy to confuse. Then a fan of different-sized buttons; now (after playtesting on a phone) three round buttons of one size: JUMP at the bottom of a stack at the right edge, SLIDE straight above it, KICK beside the stack on JUMP's baseline where SLIDE used to be, each a different colour and nearly see-through until touched (`UI/Kit/TouchButton`: glass 6%, rim 20%, icon and label about a third; held, they come up; KICK highlights while the ball is in reach). Sizes are in screen heights, so they match on every phone. `GameInput.LayoutOn` is a pure function of the screen size and safe area (`ControlLayout`, `Round`), and a touch goes to whichever button's edge it is nearest (`ClassifyDown`, `Consider`), so there are no gaps or overlaps to hit by mistake. `Tests/Editor/ControlLayoutTests.cs` checks spacing, size, the stack, on-screen, mirroring and notches on six screen shapes from 4:3 to 21:9 and both handednesses. **Second pass (thumb playtest on the Holiday Run):** the walk arrow sat under the kid (the kid stood 28% of the way across, the forward arrow's ring at 25%) so the left thumb hid them, and the slide button at the top of the right-hand stack was out of reach of the thumb that is busy walking. Now the camera stands the kid at 38% or further right as the control layout needs (`GameInput.KidSafeScreenX` = the right edge of every button on the left half + 0.14 of the screen height; `CameraFollow2D.LeadFor` turns a screen fraction into a lead; a standing kid is 4.5% nearer the middle), the arrows are tucked closer to the corner (smaller back arrow, forward arrow 0.42 screen heights in) and the SLIDE button moved to the walking thumb (up and to the left of the forward arrow; **Settings > Controls > Slide button by the arrows** puts it back above JUMP); a flick down on either arrow slides without letting go (`GameInput.FlickDown`: 0.3 inch within 0.3 s of the finger's highest recent point, once until the finger comes back up) so the kid keeps walking into the slide; the right thumb keeps JUMP and KICK. Not verified on a device: how the flick feels (the distance and window are `flickDownInches` and `flickWindow`), the slide button's reach, and the camera's 38%.
- **Double jump and slide (`Presentation/KidAnimator.cs`, `FxDirector.cs`, `FxPool.cs`).** The double jump is a launch squash, a stretch, a somersault around the body's centre and an open landing; the slide has a lunge, a lean, a spring out of it and a dust trail. New effects (ring burst, speed streaks, dust plume), a camera punch, synthesized sounds, and haptics go with them. `Core/GameEvents` carries the new events.
- **Characters.** See "The teens: uniform, tie and skin" below.
- **Holiday Run (`Scripts/Holiday`).** The campaign with no destination, through the whole story world: 23 stages (one per story level, 120 m each, in story order) streamed as additive scenes (`RunWorldStreamer`; only about three exist at a time), a lap a day. (The first version was an auto-run runner; playtesting showed the kid should be played as in the campaign, so it was reworked: the real ball and walking and kicking, no auto-run, no crash on obstacles.) `HolidayRunDirector` owns the rules (three balls, score, combo, close shaves, power-ups, revive with banked coins, missions, saving); `LevelManager` is the host with `endless` on (the campaign's checkpoint respawn, dynamic checkpoints, no bell or goal, and `RunOver` ends the run with the last ball); `BallSmasher` lets a hard kick break crates; `HolidayAtmosphere` blends each chapter's light into the next. Kick Off > Rebuild All Levels also rebuilds the Holiday Run (`Editor/HolidayRunBuilder.cs`, `HolidayPatterns.cs`, `LevelBuildKit.Holiday.cs`). Design, tuning and the verification checklist: [`docs/HOLIDAY_RUN.md`](docs/HOLIDAY_RUN.md).
- **Reach and feasibility (`Holiday/JumpReach.cs`, `Editor/LevelFeasibility.cs`).** The Holiday Run's trenches had been drawn for the old 6.5 to 14 m/s auto-run (plain gaps up to 3.4 m, wide ones 4 to 5.2 m: past even a double jump). `JumpReach` replays the kid's jump from `PlayerTuning`, the engine's gravity and the physics step (single 2.3 m / 1.30 m, double 3.6 m / 2.07 m at the 4.2 m/s walk) and gives the limits: plain gap 1.4 to 1.9 m (never over 2.0), wide 2.7 to 3.1 (never over 3.2), walls 0.5 / 1.0 / 1.7 m (nothing over 1.8), 6 m of run-up and 4 m of landing round a gap. `HolidayPatterns` and its `Validate` use them, `JumpReachTests` pins them to `PlayerTuning`, and the track builder records every pit, step, wall, barrier and roof so `LevelFeasibility` warns at build time about anything a kid cannot get past, in the story levels (audited: 23 holes, 61 walls, 11 platforms, 48 barriers; one lift moved 0.5 m) and in the Holiday Run alike. The stages are fuller too: things to smash in every stage, 1 to 4 beats of walkers and dogs, 2 to 4 floating balloons, lanterns or beach balls (a `RunBreakable` that is a trigger, burst by a ball flying through it), a trail and arcs of coins, star coins, a bonus double-jump arc, a power-up in every second stage and a middle checkpoint. See [`docs/HOLIDAY_RUN.md`](docs/HOLIDAY_RUN.md#how-a-stage-is-made).
- **Things to watch on first run.** Streamed stages must not look like new levels to the audio and analytics (they ignore additive loads); the first stage must be on before the kid is let go (`RunWorldStreamer.IsReady`, `HolidayRunDirector.FreezeKid`); at the school gate the kid is teleported home before the stages are asked for, so the world loads round them.

## The teens: uniform, tie and skin

- **Uniform.** The boy has a white short-sleeved shirt buttoned to a pointed collar and tucked into navy trousers at the natural waist, a thin brown belt with a brass buckle, a red striped tie (the satchel's strap lies over it) and white sneakers. The girl has her white blouse with the navy collar tucked under the waistband of her pleated skirt, the same tie (knot in the collar gap, tip at the waistband), knee socks and loafers. The tie is outfit part 4 in the model's second UV channel, with its colour as `accent` in `Boy.json` / `Girl.json`; `ModelOutfit.SetAccent` recolours it for shop outfits (`IAccentOutfit`), and the stripes survive because they are brightness variations of the accent only.
- **No bare skin through the clothes.** The launch screen's keepy-uppy raised the boy's thigh through the cloth: the trousers' knee was one hinge across long flat triangles (no vertices for 15 cm round it, edges up to 53 cm), the hidden skin was coarse with coarsely transferred weights, and the waist pull was damped. Now the trousers and the skin under them share analytic skin weights with a wide soft knee blend, rings are put back at the knees and hips after decimation, and skin that lies under clothes carries the garment's colour and part id, so a sliver that does poke through shows more cloth, never skin. The shirt's armpits are a soft web (no black wedges when an arm goes up), and the girl's skirt follows a lifted thigh from above the hip joint. Boy 26.5k triangles, girl 26.4k.
- **The audit.** `tools/blender/review_poses.py` renders a built teen in every pose `KidAnimator` and `MenuKid` use (the double jump's tuck at four angles of somersault, the slide and its lunge, the kick wind-up and contact, the menu's keepy-uppy foot and thigh touches, each asymmetric pose again with the other leg raised) from the game's camera yaws into a contact sheet, with an optional magenta map of any skin under clothes that shows in the pose. Its pose table is copied from the game's code: when the poses change, change it too, and run it again.
- **Known leftovers.** On the girl, with the far leg raised, the lifted skirt panel shows a small dark wedge (about 1.5 cm) at the top of its fold, and the raised thigh shows below the lifted hem (as a skirt would). The ink outline is slightly ragged on a few thin shells (collar points, the tie's edge, sleeve hems). The boy's white collar on a white shirt reads mainly through its outline at 215 px. Only the two teens were audited; the pedestrians (`Adult.fbx`) swing their legs about 25 degrees and bend their knees about 40, far milder than the teens' extremes, so they were not.

## The player roster and the primary-school kids

**Not run in Unity or on a device.** Checked with the Mono compile harness (four configs), the roster and outfit tests under a work-alike NUnit, an independent Blender re-import of every model (one mesh `Kid`, armature `KidRig`, 19 bones, one material, `Col`, UV2.x part ids 0 to 4), and the Blender pose audit.

- **The roster (`Core/PlayerRoster.cs`).** One list of every playable kid: id (what `GameSettings.Character` saves; `boy` and `girl` are unchanged, so saved choices stay valid and a stale id falls back to the boy), model name (the files are `Art/Models/<model>.fbx`, `.json`, `<model>Atlas.png` and `Resources/UI/Player<model>.png`), name key, school (`SchoolLevel.High` or `Primary`), neck height (where `BuildModelCharacter` puts the Head bone) and standing height (for the menu camera). To add a kid: build the model, add a row, add the name to both string tables. A kid whose model is missing is left out with a warning (`LevelBuildKit.BuildCast`, `ArtBaker`).
- **Building and showing them.** `LevelBuildKit.BuildCast` (LevelBuildKit.Cast.cs) builds every kid under the level's `Kid` (story levels, the Holiday Run's core scene) or the menu's `Teen`, and a `CharacterChoice` that shows the picked one. The shop's outfits go only to the kid on screen and are remembered (`Presentation/OutfitMemory`), then replayed on whichever kid is shown next, so six models do not each get a recoloured mesh copy at every level start. `KidAnimator` measures each rig's rest pose when it wakes, so the slide and the double-jump somersault fit every size. `ArtBaker` makes one material per kid.
- **The school uniform is each kid's own clothes.** `CosmeticApplier` used to dress the school outfit as white and navy over whoever was modelled; it now calls `ResetOutfit` for it. The teens' `.json` colours are the school outfit's, so they look the same, and the primary-school kids keep their own greys, navies and neckerchiefs. Every other outfit still recolours the top and the bottom (and the neckerchief or bow takes the outfit's third colour); the Holiday outfit's see-through accent hides it.
- **The picker.** `UI/PlayerPicker`: a row of cards for each school (the shorter row centred) under a heading, the chosen card orange with a tick. `SettingsPanel` shows the chosen kid and opens the picker (six cards would not fit its column). The title screen's player card and `MenuStage` read the roster: the camera frames each kid by their own height, easing when it changes.
- **The four (`tools/blender/primary.py` and `primary_*.py`, built with the teens' modules through `teen_build.py`).** About five heads tall with bigger heads and eyes, short limbs, small hands; white polo or blouse, long white socks, a hard rectangular school backpack (a randoseru) on the `Bag` bone. The boys wear shorts (knee-length, bare knees and shins), the girls a skirt or a pinafore. The accent (outfit part 4) is a small separate shell (a neckerchief or a bow), so the Holiday outfit can collapse it.
  - **Kai (`PrimaryBoy`):** fair skin, short black crop with a tuft, navy shorts, white sneakers, blue backpack, yellow neckerchief. 17.2k triangles, neck height 1.065 for 1.30 m.
  - **Mia (`PrimaryGirl`):** fair skin, freckles, brown twin bunches with red ties, white blouse with a navy round collar, navy pleated skirt, knee socks, brown shoes, red backpack, red bow. 16.9k, 1.038 for 1.27 m.
  - **Leo (`PrimaryBoy2`):** tan skin, chestnut spiky hair, round glasses, a grin, grey shorts, grey sneakers, green backpack, red neckerchief. 18.6k, 1.082 for 1.34 m.
  - **Zoe (`PrimaryGirl2`):** medium-brown skin, a mole, black bob with a yellow hairband, white blouse, grey pinafore, white socks, black shoes, purple backpack, yellow bow. 17.1k, 1.051 for 1.29 m.
  - Neck height = the Head bone's height x the standing height / the model's own height (1.380 / 1.345 / 1.440 / 1.380 of 1.685 / 1.646 / 1.784 / 1.694); one shared value would make all four the same height. Hair ties, the hairband and the glasses are part 0, so shop outfits never recolour them; girl 1's collar and all of girl 2's pinafore are part 2.
- **The audit.** `review_poses.py --leaks` (35 poses x 3 yaws per kid, its pose table re-checked against `KidAnimator` and `MenuKid`, including the double-jump tuck and the slide lunge): no bare-skin sliver under any garment; the magenta leak map shows only the neck ring under the collar, sock cuffs and shoe collars.
- **Known leftovers.** On the girls, when a thigh is raised past about 60 degrees (run knee-up and stride, jump rise, kicks, keepy-uppy) the skirt's hem on that side rides up in a diagonal notch and the knee comes out through the front as skirt-coloured leg (the teen girl does the same); the double-jump tuck bunches the skirt round the knees. On the boys, a few-pixel crease at the hip when a leg is lifted, and a slightly uneven hem at close range. Leo's grin is a small pale dash at portrait size and his glasses read as a dark smudge at 215 px; the neckerchief reads as a flat bandana from the front.
- **First run (what could not be seen).** Unity's import of the new models and the toon shader on them (Leo's thin hair spikes especially), `ModelOutfit` recolouring and the accent collapse on them, the kids' feet on the ground (`TeenFeet`), their size against the collider and the camera, the pennant on a randoseru, the picker and the Settings row at several aspect ratios, and the camera easing when the kid changes. If a kid floats or sinks, change its neck height in `PlayerRoster`.

## Every level starts at home

**Not run in Unity, and the scenes were never seen.** Checked with the Mono compile harness (four configs), an offline replica of the layouts (the real `GreyboxLevels.cs` against a recording `TrackBuilder` stub that uses the real `HomeLeadInRules`, run with and without the lead-in), the pure tests under a work-alike NUnit, and a numeric port of the scenery's lot loops. The design is in [`docs/WORLD_MAP.md`](docs/WORLD_MAP.md) ("Every level starts at home").

- **What changed.** Every story level (L01 to L23; not the challenges, the test track or the Holiday Run) starts on the doorstep of the kid's house and walks 12 m of home street before the layout's own x = 0. `TrackBuilder.LeadIn` (set by `LevelBuildKit.BuildScene`) shifts the Start checkpoint, `Walls`/`MinX` (so the camera's `minX`, `LevelManager.startBoundaryX` and `StartWall` follow) and the layout's first ground span back by `LevelBuildKit.HomeLeadIn`; nothing else in a layout moves, so the feasibility audit is unchanged. The home street keeps chapter 1's look in every level: a chapter-1 level is one street; in chapters 2 to 5 the track has a seam where the home street's slabs and scenery (`AsChapter(1, ...)`) meet the route's own, built with the Holiday Run's chunk machinery (`StageSpec.level`, `StreetBuilder.SceneryWithSeam`). `TrackBuilder.HomeFront` is the one house and garden (the Buildings kit's HouseGable with a red door, gate and pillars, picket fence, hedges, path, beds, pots, bike, bins, post box, a parent at the door); `Levels/HomeInfo.cs` holds its model and colours for the map to share. A route sign ("School ->" and the route's name) stands 2.3 m before the seam. Bells grew by 3 s (`GeneratedContent.Bell`); L01's first hint and walk sign moved with the start; `GeneratedContent.Version` is 55.
- **What was checked offline.** All 29 layouts run with and without the lead-in: only the start, the back wall and the first span differ, 0 problems in the feasibility audit (as before), every story layout calls `Goal` exactly once, no hint lies behind the doorstep; `Tests/Editor/HomeLeadInTests.cs` (the pure part runs under the work-alike NUnit; the part that needs the editor only compiles here); for 400 seeds per level the lot loops of both passes tile their stretches without a lot across the seam, a side street or the school.
- **What could not be checked (look at these first in Unity).** The home front itself: whether every kit model stands where intended (the gate leaf's hinge and swing, the door under the gate, the parent on the step, the plate with the number, how the red part-2 tint reads on the door and shutters), its density and whether it reads as home from the start view; the **seam** in all four chapters (surfaces at slightly different heights meet at a cap that should show only as a step; the ragged patches of road surface, the kerb stone and bollards; the straight line of the ground behind the houses along the seam, where the lawn meets the market's paving, the site's concrete, the park's grass and the beach's sand, and on the beach the lawn's cap against the sea); the distant land of a level now comes from one pass over the whole level (so a beach level shows the sea behind the home street too); the route sign's board width against the wall behind it; poles and wires at the seam in chapter 4; that nothing from the two passes overlaps (back rows keep clear of the seam, QuietAreas keep lots out of the plot); the extra scenery cost; and that the first run still teaches walking from the doorstep. The route sign is English in every language, like all the levels' signs.
- **Known leftovers.** Chapter-1 levels are the old builder with its start 12 m back: their houses are dealt again along the street (the same recipe, not the same houses). The challenges' and the test track's scenes are built exactly as before.
## The town map: a picture, a layout, and the routes drawn over them

**Not run in Unity or on a device.** Checked with the Mono compile harness (four configs), `TownMapTests` and `RouteTableTests` under a work-alike NUnit, and a fake-Unity harness (not in the repo) that builds the real `ChapterMapScreen` with the real `UIKit`, `ProceduralSprites`, `LevelUnlocks`, `SaveSystem`, `Loc` and `TownMap` and renders the layout it computes (canvas widths 1440, 1920 and 2520, English and Spanish, four progress states, taps on chips, strip chips and nodes, the paywall, no picture, no layout). The renders are for looking at the layout, not pixel truth.

- **What it is.** The chapter map is now a town map (`FrontEnd/ChapterMapScreen.cs`): a rendered picture of the town (`Resources/UI/TownMap.jpg`, 3200 x 1800) with the six routes of `Levels/RouteTable.cs` drawn over it from the kid's house to the school, every story level a numbered node on its route and each challenge a gold "!" node beside its route, a strip of the focused route's levels and a chip for each route along the bottom. Where everything is on the picture comes from `Resources/TownMapLayout.json` (`Levels/TownMap.cs` reads it; `Tests/Editor/TownMapTests.cs` checks it). The picture's central 2400 x 1350 (the core) is scaled to fit between the title and the strip (`UI/Kit/UIFitRect`) at any aspect ratio from 4:3 to 21:9. Routes and glyphs are drawn as UI meshes (`UI/Kit/MapPainter`, `UIMapMesh`, `MapGlyphs`). Format, checks and the screen in detail: [`docs/WORLD_MAP.md`](docs/WORLD_MAP.md). New strings: `map.choose`, `map.levels`, `map.here`, `district.*` (English and Spanish).
- **The picture and layout are the real render** (they replaced the first placeholder): a top-down Blender render of the town built from the art kits, like the user's reference (dense blocks of houses and gardens on a rounded grid, round tree crowns, soft shadows), made by `tools/blender/town_map.py` together with its layout; `tools/blender/town_map_check.py` validates the layout (all checks pass: the contract, the street names, every story node in its route's area, the railway crossings). The tests' numbers (190 px node spacing, 12 px of the route, 120 px from home and school, 320 px near the ends) are the agreed contract. Known rough spots of the art: L18's second bridge lies under its node; C05 is in the east third of the park rather than at its very end; the grid is road-heavy; shops' awnings, people, gulls and puddles are small at map scale; the beach route's line runs low, near the strip at the bottom of the screen.
- **Not verified.** Everything in Unity: the import of the picture (`Editor/UiArtImportSettings` now has an exception for `UI/TownMap`: opaque texture, up to 4096, no mipmaps, kept NPOT) and `Resources.Load<Texture2D>` of it, `JsonUtility` reading the real layout, a `RawImage` of it under the scaling `UIFitRect` (it runs every `LateUpdate`), the nodes' and chips' invisible tap boxes (child images whose taps go up to the button), text legibility over the real picture, and the memory of the texture (a few MB compressed; 23 MB if a device falls back to uncompressed). On a phone the 1080-unit canvas makes the 24 unit level names about 9 dp tall, and the tap boxes (nodes 118 units, route chips 110, strip slots 100 x 104) come to 36 to 43 dp, under the 48 dp goal in GAME_PROMPT.md: check both on a device. Level names are now placed by the screen with their real sizes (see "The levels and the map agree").

## The levels and the map agree

**Not run in Unity.** Checked with the Mono compile harness (four configs), the offline feasibility audit (29 layouts, 0 problems, as before) and `TownMapTests` under the work-alike NUnit. The rules and the level-by-level table are in [`docs/WORLD_MAP.md`](docs/WORLD_MAP.md) ("Level and map").

- **The railway.** On the map only the underpass route (L15, L18) and the park route (L23) cross the railway, and they pass under it, because those are the only levels with a tunnel. In the levels every tunnel is now that railway's bridge (`TrackBuilder.Tunnel` calls `RailwayBridgeFace`): a red band (the red of the map's train) along the front of the deck and, every 8 m or so, a white plate with a red train on its rail, built from boxes on the fascia's flat face 3.7 m in front of the track, with no colliders. The signs say it: L15 "Under the railway - it's dark in there!", L18 "Tunnel Run! Twice under the railway" (moved 0.6 m left so its legs stand clear of the barrier at 6.5), and a new sign "Under the railway - nearly at school!" before L23's tunnel (x = 77.4, on the far pavement behind the puddle). `GeneratedContent.Version` is 57.
- **Street names.** The map writes the route signs' names along their routes: Home Street, Market Street, Seaside Road. `TownMapTests.TheStreetsTheRoutesFollowAreNamedAsTheLevelsSignsNameThem` checks that on the real layout (it is skipped for the placeholder).
- **The map's side** (what each node's surroundings show, the railway crossings, C05 on a lawn in the park, the street names) is the art pipeline's brief; its validator checks what the JSON cannot hold (the railway and the areas).
- **The names on the map** are placed by the screen where they fit, with their real sizes (`Levels/TownMapNames.cs`), since the layout's fixed 300 x 56 px name box was smaller than the names the screen draws (half of them, and most Spanish ones, take two lines or more than 300 px). The focused route's names avoid its nodes and stars, the pins, the place names and each other; the other routes' nodes are drawn at 70 % without stars while a route is in focus; the house's name no longer hides under L01. Checked on the final layout with the screen harness for every route in English and Spanish at 1440, 1920 and 2520 wide (with the label font's real metrics): no name touches a node, a pin, a place name or another name. `TownMapTests.EveryFocusedRoutesNamesFindRoomInEveryLanguage` replaces the old fixed-box test, and `NameWidthsAndLineBreaksFollowTheLabelFont` pins the font table to the font. In Unity the legacy `Text` may space the lines a little differently from the table (it uses the font's line height at the bold labels' 0.95 spacing): check that two-line names keep their gap.
- **Look at in Unity.** Whether the band and the plates read on the deck from the play camera (at 3.4 m tunnels the fascia is near the top of the frame), that they do not flicker against the kit deck's face (they stand 2 to 7 cm in front of it), and the new and longer signs against what stands behind them.

## The app icon

**Not seen on a device or in Unity.** Rendered and checked offline: the Blender render and the composite, previews masked as iOS and Android show them from 300 px down to 40 px, the formats (App Store 1024 px opaque RGB, Play 512 px at 267 KB) and the compile harness (four configs).

- **The picture.** The teen boy in his uniform (white shirt, red striped tie, satchel), running to the right (to school, as in every level) with a friendly wave, after a big classic football that bounces at his feet; a morning sky with the sun rising behind his head and soft rays, the Kick Off 2 logo's mown green pitch with a chalk line, its chalk speed lines with a navy edge, and its sunny "2" (gold to orange, leaning forward, inked) in the top right corner. Rendered from the game's own model in the toon look (`tools/blender/app_icon.py`), composed by `tools/blender/app_icon_compose.py` (see `tools/blender/README.md`, "App icon").
- **Files.** `marketing/appstore/icon_1024.png` (new), `marketing/googleplay/icon_512.png` (replaces the procedural one), and in the game `Assets/_Game/Art/Icon/AppIcon.png` plus Android's adaptive layers (`AppIconBackground.png`, `AppIconForeground.png`: the face and the ball inside the safe circle, no "2").
- **Build.** `BuildScripts.ApplyIcon` sets the art as the icon for every platform and, on Android, the adaptive icon's two layers and the round and legacy icons (found by name through `PlayerSettings`' Unity 6 or older icon calls, so the editor compiles without Android Build Support). If the art is missing it bakes the procedural icon as before (`ProceduralArt.AppIcon`).
- **Check in Unity.** That **Apply Store Player Settings** fills Player Settings > Icon for iOS and Android (Adaptive, Round, Legacy) with these pictures, and how the adaptive icon looks on a phone's home screen (the launcher's mask and its parallax).

## Legs between stops, a town map that zooms, the beach's sea and school, and two small fixes

**Not run in Unity, and no scene was seen.** Checked offline with a compile harness (Roslyn C# 9 against the Unity 2021.3 module and 2021.1 editor reference assemblies, uGUI built from source; five configurations: the Android and iOS players, the runtime with editor defines, the editor assembly and the edit-mode tests, all clean), the edit-mode tests that need no native Unity run under Mono with a reflection runner (110 of 145 pass, including every new test, `TownMapTests` with a managed stand-in for `JsonUtility`; the other 35 need Unity's native runtime and could not run here before these changes either), numeric checks of the tide's profiles, and a mock render of the new map screen's geometry (the real picture and layout, not Unity's UI).

- **Every route is one trip; a level is a leg of it** (`Levels/RouteTable`: `Stops`, `From`, `To`; docs/WORLD_MAP.md "The legs" and "Every route is one trip"). Only a route's first level starts at home and only its last ends at the school; the levels between run from stop to stop, the next level starting where the last ended: Home Street via the bus stop, granny's house, the church and Sam's house; Market Street via the bakery, the post office, the flower shop and the library; Seaside Road via the surf school, the lifeguard tower and the beach cafe; the Underpass via the station; the site via the site office; the Park Path via the bandstand, the park cafe, the boathouse and grandpa's allotment. `TrackBuilder.Start` builds the stop a level starts at (`BeginAtStop`; no seam, the lead-in is the route's own street) and `Goal` the one it ends at (`StopGoal`: the set piece, a chalk line, the goal zone), the school's arch only for a route's last level. 17 set pieces from the kits (`Editor/StreetBuilder.Stops.cs`), people at seven of them (`LevelBuildKit.Stops.cs`), a spire shape for the church (`World/SpireShape`). The route sign names the level's destination; the HUD shows the leg under the level's name ("Granny's house » Church"); the results say "Made it to the church!" (new strings `stop.*`, `stop.*.to`, `leg.fromTo`, `results.madeTo`, `results.reachedTo`, English and Spanish). The lead-in keeps its 12 m everywhere, so the bells are unchanged. `HomeLeadInRules.StartsAtHome` became `HasLeadIn` (every story level), and `LevelBuildKit.StartsAtHome` now means the first level of a route. New and changed tests: `RouteTableTests` (the chain home, stops, school; names; a set piece per stop), `HomeLeadInTests` (signs name the destination), `TownMapTests.StopMarkersSitOnTheirRouteBetweenTheirLevelsClearOfEveryNode`.
- **The town map fills the screen and pans and zooms** (`UI/Kit/UIMapView`, `UI/Kit/MapViewMath`, `FrontEnd/ChapterMapScreen`). The picture is behind the header and the bars; at zoom 1 everything drawn on it fits between them (0.6 canvas units a picture pixel at 16:9, was 0.48), up to 3x by pinch, wheel or the + / - / fit buttons, drag to pan with a fling, never sliding off the screen. Nodes, pins, names and lines grow on screen with the zoom to the power 0.4 (`ItemScale`), each about its own point, so they come apart and stay easy to tap; the lines and pins are drawn again at the new widths. The stops are markers on the routes (`TownMap.StopPosition`), named when zoomed in where the name fits. The title row is gone (the header says "Choose your way to school" and shrinks to fit); `UIFitRect` is no longer used by the map. Tests: `MapViewTests`.
- **The tide is the sea running up the sand** (`World/TideWash`): its sheet now follows the beach's real profile (`SandField.Shore`, public) on 17 rows and runs on just under the sea's surface (`seaY`, set by `Finish` from the lowest ground), where it used to cut under the sand's slope and leave a strip of sand up to 12 cm proud between the wash and the sea; the shoreline's foam line stops where a tide washes (`TrackBuilder.TideStretches`, `StreetBuilder.ShoreRuns`), so nothing cuts the water in two. Checked numerically: the wash is at least 1.8 cm over the sand wherever the sand is above the sea.
- **The school is on land** (`StreetBuilder.SchoolHeadland`, only L14 now ends at the school on the beach): the coast turns away 26 m before the gate behind a sea wall with rocks, grass behind the dry sand, a paved yard past the gate (calm sand under it), the sea 46 m behind the footpath; the beach's props, foam and crests stop short of it.
- **The teens are named** Ren and Hana (`player.boy`, `player.girl`; `settings.boy` / `settings.girl` are gone).
- **The title screen's ball** is a real ball's size for the kid juggling it (`LevelBuildKit.MenuBallRadiusTeen` 0.115 m, `MenuBallRadiusPrimary` 0.1 m, against the levels' 0.17 m; `MenuKid` scales the shared ball to the shown kid's). `GeneratedContent.Version` is 58.
- **Look at these first in Unity.** Every stop's set piece (where each kit model stands, the name boards' size and height against each shop's front, the church built from boxes and House3D, the people's poses and colours, the chalk line) at both its level's end and the next level's start, especially on the beach's sand; the market's row of shops either side of a stop's plot; the map's pinch and drag on a phone (the drag threshold, taps on nodes still playing levels, a pinch begun on a node), the + / - / fit buttons, the item scaling (the pop-in on the nodes' inner body, the redraw of the lines at each step), the stop names' placement, and the header title on a 4:3 screen; the tide's sheet against the sand and the sea at low and high water in L12 and the Holiday Run (and that the foam's ends meet the wash's curl); L14's headland (the sea wall's angle, the rocks, the grass and yard against the sand, the sea's three pieces meeting, the school's trees); the menu ball's size against each kid and its shadow.

## School trips: the legs add up, the bell is for the whole way

**Not run in Unity, and no scene or popup was seen.** Checked offline: the compile harness (legacy input, Input System, editor and edit-mode tests, all clean), and the new `SchoolTripTests` (18 tests) run under Mono with a reflection runner against the real `RouteTable`, `SaveData`, `SaveSystem`, `SchoolTrips`, `LevelUnlocks`, `Monetization` and `GameSettings` sources: all 18 pass, and a copy with two rules deliberately broken fails 6 of them. The older pure tests (29) still pass. Every new string is in English and Spanish (402 keys each, checked by loading both tables), and both UI fonts have the "·" the new lines use. `RouteTableTests.TheTripTestsWalkTheStoryInTheLevelTablesOrder`, `EveryRouteHasASchoolBellForTheWholeTrip` and `GameLogicTests.TripsSurviveTheSaveFile` need Unity (the level table, JsonUtility) and were only compiled.

- **A route is a stage and one trip** (docs/WORLD_MAP.md, "School trips"; `Progression/SchoolTrips`). Each leg's `bellTime` is its own target (a pace); the school bell of the trip is the sum of the route's targets (Home Street 5:40, Market Street 6:25, Seaside Road 5:32, the Underpass 2:56, the site 2:51, the Park Path 7:15). Each route's trip is saved (`SaveData.trips`, `TripRecord`; `SaveData.CurrentVersion` 2). Finishing the first leg starts a new trip, a later leg replaces its time and forgets the ones after it, and the last leg judges a trip walked from home without a break: on time marks the route on time for good (and keeps the best trip), late forgets the whole trip. The bell rings on the last leg only, at the trip so far plus this leg's time; when it rings the trip is forgotten at once, so restarting the last leg can't save it. A last leg played on its own is untimed. Cozy mode records and judges nothing.
- **Unlocking** (`LevelUnlocks.StoryOpen`, `HeldBackBy`, `NextToPlay`): as before, plus a level after a route's last leg needs that route on time (or cozy mode). A level already finished stays open (so switching cozy mode off never locks what was played). `NextToPlay` returns the route's first leg when a late trip holds back the first level that can't be played, so the map focuses the stage to walk again. Old saves: `SchoolTrips.Upgrade` marks every route whose last level a version 1 save had finished as on time.
- **LevelManager:** works out the route, the leg, the trip so far and the trip's bell at each run's start (`SetUpTrip`), and the bell or the pace from the settings at the start and on resuming (`RefreshTimers`; resuming also no longer turned the bell on in a challenge). `LevelResult` has the pace, the trip and whether the next level is still locked; star 2 is the pace, or the whole trip on time on a timed last leg. `NextLevel` after a leg goes to the same route's next leg when it is open (after L15, L18 once open), `LoadTripStart` to the route's first leg.
- **HUD:** the bell slot shows "Target 0:28" on a leg (orange under 10 s, then "Behind") and "Bell 0:28" for the rest of the trip on a timed last leg ("LATE!" after). On a later leg of a continuous trip the leg line reads "Home » Bakery · Trip 2:15" (rebuilt once a second).
- **Results:** a stop's leg says "Made it to the bakery!", "Kept the pace: the bakery in 1:03" and "Trip so far 2:15 · school bell at 6:25"; a timed last leg "Made it to school on time!" or "Late for school!" with "Whole trip before the bell (4:58 of 5:40)", and when late a red note, a **From home** button as the main one and Next hidden while the next level is locked; an untimed last leg its pace and a note to walk from home. The stars no longer cover the first line (they were placed by their top edge, so the middle one hung 35 units over it; now they are centred where they were meant to be and the lines start lower), the card grows with its lines (up to the screen's height; a challenge's four lines no longer reach the coins), each line's dot is centred on it and a long line shrinks to fit.
- **Look at these first in Unity.** The results card in each case (a stop's leg, on time, late with and without the next level open, untimed, cozy, a challenge) at 16:9 and 4:3, in English and Spanish: the stars against the first line, the red note's two lines, four buttons in a row; the HUD's leg line with the trip on a long stop name (it shrinks to fit), the target turning orange and "Behind"; the bell ringing at once on a last leg begun after a slow trip; switching cozy mode in the pause menu mid-leg; an old save (version 1) keeping its levels open; the map focusing the route to walk again after a late trip.

## One stick, a guided tour, and a Controls page

**Not run in Unity or on a device.** Checked offline: the compile harness (legacy input, Input System, editor and edit-mode tests, all clean), the rewritten `ControlLayoutTests` (18) under Mono with a small Unity stand-in and the real `GameInput`, the trip tests (18) and the map tests (23) on the merged tree, string-table parity (430 keys in each language, none missing or doubled), and mock renders of the stick and of two tour steps at the real layout positions (not Unity's UI).

- **One stick for the left thumb** (`Input/GameInput`, `UI/Kit/StickView`). The walk arrows and the SLIDE button are gone. A see-through glass ring with a knob rests in the bottom-left corner (like the reference the user sent). A touch anywhere in its area brings the ring to the thumb, kept whole on screen, and the ring follows a thumb that drifts past it. Push right to dribble forward, left to walk back, let go to stop; past a dead zone of 0.22 of the radius. **Pull down to slide** (0.5 of the radius down and more down than sideways); the way it leans picks the slide's way (down-right forward, down-left back, straight down the way the kid is going), and it slides once per pull until the knob comes back above 0.3. Swipe down elsewhere still slides. Nothing is drawn inside the ring but the knob (at first there were small arrow marks; the user asked for them to go); a light click on grab and a firmer one on the slide. `GameInput.ReadStick` and `StickCenterFor` are pure and tested. The "Slide button by the arrows" setting is gone. The camera keeps the kid clear of the stick's whole area (38% of the way across on phones, as before).
- **JUMP's icon** (`ProceduralSprites.JumpIcon`, after a reference picture the user sent) is a figure springing up and forward in bold rounded pictogram strokes: a round head, the front arm thrown up and the back arm down, the front knee driven up and the back leg pushing off, with a thin gap where that leg meets the body. It replaces the plain arrow (and a first leaping-kid version over a ground line). KICK shows the football (`ProceduralSprites.BallIcon`) again: a kicking-boot icon was tried and the user asked for the ball back. **JUMP and KICK are bigger** (radius 0.145 of the screen height, was 0.125; JUMP 0.18 in and KICK 0.515 in, both 0.185 up) and every touch control has a **thin, bright rim** (`ProceduralSprites.ThinRing`, nearly white at 70% at rest, full when held); left-handed, the kid now stands up to 0.47 of the way in on phones (`ControlLayoutTests`).
- **The guided tour** (`UI/ControlsTour`), the first time any level starts (story or Holiday Run): the run is held before the clock starts (`LevelManager.Hold`: time and the world stop, the kid takes no input, no pausing, but `GameInput` stays live), the screen dims with a round spotlight and a pulsing ring over one control at a time, and a caption card across the top says what it does: walk, slide, JUMP, KICK, a tap anywhere else, the pause button. A ghost thumb acts each move out; doing it ticks the step off ("Nice!") and moves on; Next and Skip are always there. Remembered with the tutorial hints (`TutorialHint.AllIds` has `controls`), so Reset progress brings it back and the store screenshots skip it.
- **The Controls page** (`UI/ControlsGuide`): Pause > Controls (story levels and the Holiday Run) and Settings > Controls > How the controls work. One row per move with a small picture of its control on a dark tile, a left-handed note, and **Play the guided tour** (there and then in a level, through `ControlsTour.Replay`; from the menus it turns the tour back on for the next level).
- **The third star is collecting everything** (`Progression/StarRules`, `StarRulesTests`): every coin and the level's sticker (just the coins where there is none), with no streak and no time needed; each of the three goals is a star of its own, so a slow run that collects everything gets two. The results' third line reads "Every coin (13/17) and the sticker" and its dot is that goal alone. `LevelDefinition.perfectStreakTarget` is no longer used for stars. Challenges keep their own score stars.
- **No more being walled in by crates** (a playtest: in L16 the pipes rolling down from 71 shoved the crate stacks at 48 and 52 back against the scaffold gantry the kid slides under at 45; the kid came out of the slide into the crates, could not stand up and could not get on). Crates can still be kicked or walked forward but are never pushed back past where they started (`Core/OneWayBody`, on every crate; the Holiday Run's solid crates drop it with their body). A pipe that has stopped against something is cleared after a second instead of piling up (`PipeSpawner.stallSpeed`, `stallTime`). Going back to a checkpoint now puts back what lies ahead of it: crates where the level put them, rolling pipes cleared (`Core/IResetAhead`, `ResettableBody.ResetAhead`, `PipeSpawner.ResetAhead`, `LevelManager.ResetAhead` in the respawn). And as a safety net in every level and the Holiday Run, if the player tries to move (or the kid is low under something) for 5 s without getting 0.75 m anywhere, a **Stuck? Back to the checkpoint** button comes up under the header (`UI/StuckHelper`). A scan of all the layouts for the same pattern (crates within 2 m of a slide-under's ends, crates or slide-unders in a pipe's path) found L16's two stacks and L18's stack at 92 in the pipes from 110 (both covered now) and a stack 1.55 m after Rush Hour's stall awning (2.5 m high: the kid walks under it, no trap). `GeneratedContent.Version` is 60. The feasibility audit: 29 layouts, 0 problems.
- **Lighter rims:** the touch controls' rims are 42% at rest (85% held) and thinner (`ThinRing`, 2.6% of the radius).
- **Challenges explain themselves** (`UI/ChallengeGuide`, `UI/Kit/UIInputBlocker`, `ChallengeGuideTests`): a How to play card when a challenge is started (once per visit; again from Pause > How to play) with its goal, the three star marks from its thresholds, its time (and the slalom's 3 s per missed gate), and two or three control tips with the Controls page's pictures (keepy-uppy: KICK to pop it up, a tap each time it drops, the stick to stay under it; targets: the aimed drag from KICK, the stick to fetch the ball, JUMP onto the ramp, crates and pallet for the high ones; slalom: dribble low with the stick, pull down to slide under the boardwalk, drag up from KICK through the hoops). The run is held under it; `LevelManager.Hold` is now counted. The challenges' old English-only `instructions` are only a fallback. Checked: the card laid out by a small harness and rendered (C01, C03 in English at 16:9, C04 in Spanish at 4:3).
- **The map points out what to play and what a late trip holds back** (`ChapterMapScreen`: `Survey`, `BeaconFor`, `Halo`, `Tag`, `TagShift`, `BuildBanner`; `LevelUnlocks.FirstHeldBack`; `UI/Kit/UIGlow`, `UIBob`; sprites `Clock`, `PlayIcon`, `RetryIcon`; `MapIndicatorTests`). The next level to play has a glowing gold halo and ring and a bobbing **PLAY** tag over its node (on any route, not only the focused one); when it is the first leg of a stage to walk again after a late trip, the halo is orange and the tag says **TRY AGAIN**. The level a late trip holds back is a red disc with an alarm clock, a red halo and a **LATE!** tag, and a banner under the header says what happened and what to do ("Late for school on Seaside Road! Walk it again from home and beat the bell to open level 15.") with **From home** (the map's room above the picture shrinks to fit it). The route chips carry a badge (a red clock on the late route, a gold play sign on the route of the next level), and the strip's next marker and its locked chip take the same colours. Tags are 58 px of the picture on a 96 px pill, reserved before the level names are placed (the names keep off them) and slid sideways off neighbouring nodes. Checked with the screen harness on its real layout (late and on-time progress, English 16:9 and Spanish 4:3).
- **The map says why a level is locked after a late trip** (`ChapterMapScreen.ShowLate`, `LevelUnlocks.HeldBackBy(catalog, level)`): such a level's button can be tapped, and a card says the bell rang before the kid got to school and offers **From home** (the route's first leg).
- Hints, the Holiday Run's tips, L01's signs and the docs talk about the stick (`GeneratedContent.Version` is 59).
- **Look at these first on a device.** The stick's feel: the dead zone, how far down a slide needs, the ring following the thumb, whether a sideways push dips into slides by mistake (`stickDeadZone`, `stickSlideDown`, `stickSlideRelease`, `stickRoamIn`, `stickRoamUp`); the ring's and knob's opacity over bright and dark streets; the jump and kick icons at the buttons' size. The tour: the spotlight's place on each control in both hands and on a notched phone, the ghost thumb's paths, the caption card against the info card, that trying each move ticks it off (the kick's drag shows its aim preview while held), the Holiday Run starting it after the first stages load, and replaying it from Pause > Controls mid-level. The Controls page at 4:3 in Spanish (the longest texts shrink to fit). The map's late-trip card.

## The map: every route starts from home, every stop at its place

**Not run in Unity, and no scene was seen.** Checked offline: the Blender generator (layout and the full 3200 x 1800 render), `tools/blender/town_map_check.py` on the installed layout (all checks pass, including the new trip checks and the zones), `TownMapTests` (20, the new ones included) under Mono with the work-alike NUnit against the real `TownMap`, `TownMapNames` and `RouteTable` (the new tests fail on the old layout, as they should: L15 1148 px past the shared stem, L11 1656, L16 595, L06 on the stem, no stop placed), the compile harness (legacy input, Input System, editor and edit-mode tests, all clean), the feasibility audit (29 layouts, 0 problems, the same counts as before: L15's two covered walkways keep the roofs its tunnels had), and the real `ChapterMapScreen` laid out by the screen harness with each route in focus (English and Spanish).

- **The problem.** On the map the fourth chapter's first level (L15) sat 1400 px along its route, just before the railway, and so did L16 (half way through the site) and L11 (at the far end of Seaside Road): they read as starting in the middle of the road, though every route's first level starts at home. The stops were drawn halfway between their levels, not where they are.
- **The stops are at their places** (`town_map_layout.STOPS`, `Resources/TownMapLayout.json` "stops", `Levels/TownMap.StopPoint` / `StopPosition`, which snaps the point onto the route and falls back to halfway for a layout without stops). The picture shows each one (`tools/blender/town_map_sets_stops.py`): the bus stop's shelter, granny's pink bungalow, St Mary's with its tower and spire at the top of Hill Road and Sam's yellow house on Elm Street; the bakery on the market square, the post office, the flower shop and the library on Market Street; the surf school's hut on the boardwalk where the beach begins, the lifeguard tower, the beach cafe's kiosk; the station's brick ticket hall on Station Road at the foot of the railway bridge; the site office at a security gate halfway through the building site; the bandstand, the park cafe, the boathouse at the duck pond's end and grandpa's allotment by the railway. The level names on the map keep off their route's stop markers (`TownMapNames.Place`).
- **Every node on its own leg, near its start** (the solver, `town_map_nodes`: each story node strictly inside its leg, 100 px from every stop; a route's first node past the stem it shares with other routes near home; later nodes anchored 128 px after their stop). First nodes, px along the route before -> after: L01 186 -> 180, L06 124 (on the stem shared with the beach) -> 441, L11 1862 -> 231, L15 1436 -> 337, L16 877 -> 425, L19 720 -> 720. Later nodes now sit 105 to 230 px after the stop they start from. To make room, the street and market nodes moved along their streets (L06 to L09 east by 260 to 310 px, L10 round the corner onto the Main Road, L03 and L04 west by 50 and 85), and the solver's and validator's name rule now measures the other routes' nodes at the 70 % the screen draws them while a route is in focus (as it already did for its own names).
- **What the picture shows changed with the nodes** (README "Level and map", docs/WORLD_MAP.md): L15 is the walk from home up the West Street and along Station Road past the building site's covered walkways to the station's hall; only L18 goes under the railway (twice: the main line and the station's loop; the hall that used to bridge the road east of the loop is gone). L11 is the walk down to Seaside Road (a beach shop on its corner, the sign to the beach) and along it out onto the boardwalk to the surf school. L16 starts on Yard Road and goes in at the site's gate; L17 starts at the site office and has the cranes. The market square, the crossings, the corner shop, the fruit stalls and the rush hour follow their nodes; L05's puddles are on the East Street up to the school; the park's playground, pond and the school garden's fountain moved with their nodes. Level zones are per level now (`LEVEL_ZONE`), and every stop has one (`STOP_ZONE`).
- **One level changed: L15** (`Editor/GreyboxLevels.cs`, `TrackBuilder.CoveredWalkway` in `LevelBuildKit.cs`). It now reaches the station only at its end, so its two dark stretches are no longer the railway's bridge but the building site's covered walkways on Station Road: the same roof, ceiling collider, lamps and darkness as `Tunnel` (the feasibility audit sees the same two roofs), with the site's hoarding along the back, a boarded roof over the footpath, the site's blue boards with hazard stripes along its front and scaffold tubes at the back and the ends, and no red railway band or train plates; its sign reads "Covered walkway - it's dark in there!". L18's and L23's tunnels and signs already agree with the map. `GeneratedContent.Version` is 61.
- **The generator** reads RouteTable's stops again (its route parser had not known the fifth argument since the stops were added, so neither `town_map.py` nor `town_map_check.py` ran), and the checker checks the trip: every stop placed, on its route between its levels and clear of every node, every node on its own leg, the first past the stem and within 500 px of it, every later one within 260 px of its stop.
- **Look at these in Unity.** L15's covered walkways (the hoarding stretched up to the roof, the boarded roof's depth over the footpath, the hazard band and the blue boards facing the camera, the end tubes not in the way of the play view, the lamps under the boards); the new picture on the map screen at the fit and zoomed in (the stops' set pieces beside their markers, the church's spire and its shadow, the station's hall at the foot of the bridge, the beach shop at the corner of Seaside Road); the stop names when zoomed in; the level names, which keep off the stop markers now. Wording to consider (strings are another session's): the tutorial hint `tut.tunnel` ("It's dim in the underpass") is now shown in L15's covered walkway, and `sticker.L15.hint` says "between the two tunnels".

- **L15 is "Station Dash"** ("Carrera a la estación"; it was "The Underpass"): since the map change it runs from home along Station Road to the station, under covered walkways, and only L18 goes under the railway (the route keeps its name, The Underpass). "Station Road" could not be used: it is a street on the map, and `town_map_check.py` keeps streets from sharing a level's name. Its dim-walkway hint (`tut.tunnel`: "It's dim under there...") and sticker hint (`sticker.L15.hint`: between the two covered walkways) say what it has now.

## No rolling pipes: the site's vehicle gates, builders and commuters

**Not run in Unity.** Checked offline: the four compile configurations, the feasibility audit (29 layouts, 0 problems), the Holiday Run's pattern and stage tests and the pure level tests (29/29), string-table parity.

- **The rolling pipes are gone** from the game (a playtest found them unrealistic, and they had shoved crates into the kid's way): `Hazards/PipeSpawner`, `TrackBuilder.Pipes`, the Holiday Run's `RunPipes`, `PatternKind.Pipes`, `StageTraits.Pipes` and the `pipes` hint. Pipes still lie stacked on the sites as scenery.
- **The site's vehicle gate** (`TrackBuilder.SiteExit` in `Editor/LevelBuildKit.Site.cs`; `Hazards/BanksmanBoard`): how a real site keeps walkers and its vehicles apart. A concrete access road comes out of the site across the footpath (hatched yellow and black where they meet), the sliding gate stands open on its posts, and a banksman in hi-vis and a hard hat holds a lollipop board: **GO** (green: cross), GO flashing (hurry), **STOP** (red, the board tipped toward the gate: the site's digger, then its white pickup, come out of the site and across the footpath to the road). Caught in the gateway on STOP, the ball is lost ("Beep beep! Wait for the banksman's GO", `lose.digger`). It is a `Crossing` with its own look and timing (GO 4 s, flashing 1.4 s, STOP 4.6 s; `Crossing.loseKey`).
- **Builders** (`TrackBuilder.Builder`): passers-by of the site in hi-vis, navy trousers and a yellow hard hat who keep them on and walk alone (`Walker(..., builder)`): the ball bounces off them, the kid slips past.
- **L16 Building Site**: a site gate right after the start (9 to 14 m, with the `siteexit` hint: "While the banksman shows STOP, the digger comes out... Wait for GO, then cross"), the boardwalk ramps as before, the scaffold to slide under, one crate stack (the second made way for) a second site gate (52.5 to 57.5 m), the second boardwalk, a builder walking the footpath before the gate switch. **L18 Tunnel Run**: commuters from the station walk through both road tunnels (`Pedestrian`) where the pipes rolled. **Holiday Run**: its Tunnel Run stage has pedestrians instead of pipes. `GeneratedContent.Version` is 62.
- **Look at these first in Unity:** the digger and the pickup coming out of the gate (they drive toward the camera in depth, as a crossing's cars do: which end of the digger leads, its speed), the banksman and his board (height, the words' size, the tip toward the gate on STOP), the hatching against the footpath's slabs, the open sliding gate against the hoarding, and the builder's hard hat (the hair colour stands in for it).

## A clean, clear map

**Not run in Unity.** Checked offline: the four compile configurations, `TownMapTests` (20) under Mono, string-table parity, and the real `ChapterMapScreen` laid out and drawn by the screen harness (fresh, midway, late and on-time progress; English and Spanish; 16:9 and 4:3).

- **The problem.** With all six routes drawn in full (casing, nodes, stops and branches on every one), "You are here", the district names and every street name on top, the fitted map was busy: it was hard to see which route was in focus and where to go next.
- **Only the route in focus is drawn in full** (`FrontEnd/ChapterMapScreen.cs`): its line with the white casing and dashed centre, its numbered nodes, its stops, its challenge's branch and node, its level names. The **other routes** are thin, faint lines in their colours (17 px, half see-through, no casing) with nothing on them, except the two things the map has to point out wherever they are (`Drawn`): the next level to play (its PLAY tag) and a level a late trip holds back (its LATE tag). A chip at the bottom still brings any route into focus.
- **Calmer picture and nodes**: a light, even wash over the picture (`PictureWash`) so the lines and names stand out crisply; locked nodes are a pale shade of their route's colour with the lock, not grey, so the levels to play are the strong colours; the next level's halo is smaller and softer (1.9x the disc, 25 to 60 %).
- **Less text at the fit**: the "You are here" pill is gone (the PLAY tag says where to go and the house pin is named; its string `map.here` is removed), the district names and the other routes' street names appear once the view is zoomed in to 1.4x or more (`DetailZoom`, `UpdateZoomDetail`), and the focused route's own street (Home Street, Market Street, Seaside Road) is always named. The tags' sideways shift and the names' room ignore the nodes that are not drawn.
- **Look at these in Unity:** the fitted map with each route in focus (the faint lines readable on the busy parts of the picture, the wash not too milky), the PLAY or LATE tag on another route's node, the pale locked nodes against the picture, and the names popping in at 1.4x while pinching.

## The coach: how to do what comes next, at the top of the screen

**Not run in Unity.** Checked offline: the four compile configurations; `ActionCoachTests` under Mono against the real `CoachPlan`, `CoachCatalog`, `LevelFeasibility`, `JumpReach` and string tables (7 of 8 pass there; the eighth, keepy-uppy's steps, needs Unity's `Vector2`, and its checks pass against a stand-in); the feasibility audit (29 layouts, 0 problems); `TownMapTests`, the Holiday Run and level tests (29/29); string parity; every story level's spots listed beside its signs (200 spots in 29 layouts); and the coach card drawn by the screen harness (16:9, 4:3 and 19.5:9, English and Spanish).

- **The problem.** In keepy-uppy the only instruction was the sign at the start and a one-time tip that faded after 8 s, and the challenge guide said "tap KICK", which is a forward pass. Elsewhere, how to do a special action (slide under, chip over, wait for the green man) was on the street signs and in a tip shown once per player.
- **The coach** (`UI/ActionCoach`, `UI/CoachCatalog`): a card at the top between the info card and the pause button (under the info card where that is narrower than 620), with the Controls page's picture (`ControlsGuide.Draw` at a size; a new `Wait` picture, a clock) and a title naming the control over a line or two of how-to. It takes no touches, hides while held, paused, respawning or during the tour, and on a narrow screen while the Stuck? button is up. It replaces the old hint banner: the first-time tips (`TutorialHint`) show on it too (for 8 s, holding 3 s against a how-to that is not yet close).
- **Challenges:** the step to do now, all the way through, settling for 0.3 s so the ball's bounces don't flick it: keepy-uppy, pop it up from KICK (a short drag straight up) or tap the open screen as it drops, get under it, fetch it; the targets, aim from KICK or fetch it; the slalom, keep it low or chip it through the next gate, then slide to the finish. The guide's juggle tips now say the same (`guide.juggle.kick`, `guide.juggle.touch`), the status lines beside the clock are in the string tables (`challenge.status.*`; they were English only), and keepy-uppy no longer shows its juggle count twice.
- **Story levels:** every special action has a how-to from 6 m before it until it is passed (`Tutorial/ActionSpot`, placed by `Editor/CoachPlan` when the level is built): barriers (slide), walls by height (a kerb, chip it over, a high wall to lob and double jump unless a trampoline just before it is the way), steps in the ground (not on the beach, whose sand slopes), crate stacks, parked cars, the step and high wall, pits and trenches by width (a jump, or a double jump; wider ones are crossed on a bridge, whose how-to that is), trampolines (only the kid's bounce just after a fountain), moving platforms, hoists, rope swings, call-button gates, zebra crossings, the site's vehicle gates, the tide, dogs, passers-by and builders, gulls and fountains. Neighbours of a kind join (two cars in a row). Inside a long stretch (gulls along the whole beach) what comes up next shows first. After three passes with the ball a move's card is its title alone; Reset progress forgets that. The Holiday Run and the menu street place none.
- **Settings > Gameplay > How-to tips** (`GameSettings.CoachTips`, on by default) turns the how-tos and steps off; the first-time tips stay. The store screenshots show no coach (`ActionCoach.Suppressed`). `GeneratedContent.Version` is 63.
- **Look at these in Unity:** keepy-uppy's steps switching as the ball goes up and comes down (and that "Step 2" holds through a run of juggles); the card's place and size on a phone, a 4:3 tablet and with the dev Tune button; a how-to coming up before each obstacle in L01 to L05 and the crossings and site gates; the compact title once a move is learned (its width is measured from the font); the Wait clock's colour on the tile.

## The camera stays on the kid, trenches with two banks, and a trophy for walking every way to school

**Not run in Unity.** Checked offline: the four compile configurations; `CameraFollowTests` (4) on the camera's two rules; `RouteRewardsTests` (3) under Mono with a stand-in Unity; the Holiday Run and level tests (29/29), `TownMapTests` (20), the coach's tests; the feasibility audit (29 layouts, 0 problems) and a new sweep of every level for holes whose banks differ and props placed off the ground; string parity; and the celebration and the map's chips drawn by the screen harness.

- **The camera** (`CameraRig/CameraFollow2D`): a ball kicked far ahead pulled the view 30 % of the way to it, so the kid went off the left of the screen. Now it leans toward the ball only while it is close (fully within 3 m, fading out by 6 m), never more than 1.2 m across or 0.5 m up (`BallLean`), and the kid always stays at least 15 % of the screen's width in from either side, even while the view catches up after a trampoline's throw (`KeepInView`). A ball out of view is shown at that side of the screen: the ball in a white disc with an arrow pointing out and how far away it is ("12 m"), above the buttons (`UI/BallMarker`, in the levels and the Holiday Run; `hud.ballAway`).
- **Trenches and cones** (`Editor/LevelBuildKit.cs`): the cones at a hole stood at the hole's own height on both banks, so where a bank was lower they floated (L17's last trench, dug into the raised site deck, had the street 2 m below as its far bank, and no wall at that end). Cones and the barrier are now laid once all the ground is known, each cone on its own bank's ground (none over no ground), the barrier reaching over a bank only where it is level. **L17 Cranes:** the last trench's far bank is the deck again (90 to 92 m, a checkpoint on it), a ramp takes the kid down to the street (92 to 98 m), and the site barrier and the gate moved 4 m on (`Goal` 106). **L20 Fountain Square:** its stream (60 to 62 m) had been laid over unbroken ground, so it could not be fallen into; the path is now split round it. The only hole left with unequal banks is L17's builder's-lift trench at the foot of the deck, by design (its cones now stand on the deck's edge).
- **Walking to school** (`Cosmetics/RouteRewards`, `UI/SchoolRewardPanel`): a route is walked once every story level on it is done. Each earns its medal (gold, on a ribbon in the route's colour; new procedural sprites `Medal`, `MedalRibbon`, `Trophy`), shown over its chip on the map. Three routes earn the Way Finder flag; all six earn the Top of the Class trophy, the Top of the Class ball and the Victory Lap trail (a new `CosmeticUnlock.SchoolRoutes`, never sold; the Locker Room shows a medal, "4 / 6" and "Walk 2 more ways to school", and sends to the map). The results of the finishing leg say a medal or the trophy is waiting; the menu celebrates once (before any sticker reward), remembered in the save (`schoolMedals`, `schoolTrophy`). The store screenshots grant and mark them first. `GeneratedContent.Version` is 64.
- **Look at these in Unity:** a long kick ahead and back in the park levels (the kid stays put on the screen, the marker shows the ball and counts down as you walk to it); L17's last trench (cones on both edges, the walls at both ends, the ramp down, the moved barrier and gate); L20's stream; the celebration after finishing a route's last leg and after the sixth (the trophy, the medals' ribbons, the prizes' pictures); the medals on the map's chips.

## The boy's new face and hair

**Not run in Unity.** Checked offline: the boy rebuilt with `tools/blender/teen.py` (no errors; 27,237 triangles, up from 26,509), his player card and the review sheet rendered with the game's toon shading (faces from the front, three-quarters and the side, the poses, the back, and at the in-game size); the girl's atlas repainted byte-for-byte the same as before; the four compile configurations.

- **The look** (after reference pictures the user sent; the boy stays our own character, in the style of hand-drawn 1990s anime films):
  - **Hair** (`teen_hair.py`): a fuller blue-black mop: a fringe parted over his left eye and swept across the forehead toward his right in long pointed locks (one between the eyes), and a fuller cap. The knot-like cowlick at the crown is gone; a few spiky tufts lift up and back at the back of the crown instead. The colours are now a dark navy with a soft slate-blue shine (`Boy.json`'s hair colour follows).
  - **Face** (`face_teen.py`): tall dark eyes that are nearly all iris with one bright highlight (the same side in both eyes) under a heavy lid line, no lid crease, a faint lower lid; thin brows slanting up and out; blush drawn as three short hatched lines on each cheek over a soft blush; a smaller nose and a small smile; no plaster. Lighter, peachier skin (`teen_outfit.palette`).
  - **Head** (`teen_head.py`): a slimmer, longer oval narrowing steadily into a soft, slightly pointed chin (it was squarer).
- **Hair texture:** a new tile in the atlas beside the white corner (`face_teen.HAIR_TILE`, `_hair_tile`): near-white with fine dark strand lines (longer, darker ones where the clumps part) and a soft shade at the roots, multiplied over the hair's cel colours. `teen_hair` lays it out per vertex: across and along each lock (each lock starting at a different place along the strands) and down the cap from the crown, repeated round it without a seam; `Part.uv` can now be a list by vertex (`teen_build`). Only the boy uses it; the girl's hair and the primary-school kids' are as they were.
- **In the game:** `Boy.fbx`, `Boy.json`, `BoyAtlas.png` and his player card `PlayerBoy.png` are replaced. `GeneratedContent.Version` is 65, so the levels rebuild with his new default hair colour (the outfit recolour compares against it).
- **Not redone:** the app icon (`app_icon.py`) and the L01 sticker (`sticker_art.py`) were made from the old boy and still show him; they can be re-rendered from the new `Boy.blend` with the commands in `tools/blender/README.md`.
- **Look at these in Unity:** the hair's strand lines at play size and up close on the menu's launch screen (the atlas' compression and mip maps soften them), the eyes and the hatched blush at play size, and the hair's colour under each chapter's light.

## The boy from the user's model, and his bicycle

**Not run in Unity.** Checked offline: `tools/blender/meshy_boy.py` run end to end on the supplied model (no errors; the boy 30,001 triangles, the bicycle 19,999); his review sheet, his player card and the pose audit (every pose the game uses, from the game's camera yaws) rendered with the game's toon shading; close-ups with back faces culled (as `ToonCharacter` draws) for holes; a recolour test (the shop's formula on the vertex colours: red shirt, blue trousers, brown hair) rendered; the four compile configurations.

- **The model:** the user supplied a textured model (from an AI model generator) of a boy walking a green bicycle: one fused, scan-like mesh of about 270,000 triangles with one 2048 texture, no rig, his arms bent holding the handlebar and a stride in his legs. `meshy_boy.py` (new; `tools/blender/README.md`, "The boy") makes the game's boy from it in the teens' contract (`Kid` / `KidRig`, vertex colours times the atlas, the outfit part in UV 2, the game's bones, Nose and Bag markers, `Boy.json`):
  - **Split** the boy from the bicycle by texture colour and the bicycle's plane (his right sleeve crosses it, so his cream shirt always stays his); the handlebar's grips in his fists dropped.
  - **Joints** found on the mesh (the legs' cross-sections and the crotch, the lifted heel, each arm's skin and the corner of its centreline for the elbow, the shoulders, the neck).
  - **Cut apart** what touched in the scan but must move on its own: his thighs and shoes, his left fist from the belt; each side's holes closed with patches that never span two sides (a patch across the legs made them stretch into a web when he ran).
  - **Re-posed** to the rest pose the game swings from: arms hanging, legs straight under the hips (the back leg stretched 0.3 % to stand level), feet flat, head lifted from looking down at the bicycle. Weights from bone heat, made again on the new pose; below the crotch a leg takes nothing from the other leg's bones.
  - **Recolourable:** the shirt, trousers and hair are parts 1, 2 and 3; their texels in the atlas are divided by their colour, which their vertex colours carry, so the shop's outfits recolour them and the default looks as the model did (cream shirt, charcoal trousers, navy-black hair). Skin, face, belt and shoes don't change. He has no tie and no bag: the shop's accent shows nothing on him, the pennant still rides on his Chest bone.
- **In the game:** `Boy.fbx`, `Boy.json`, `BoyAtlas.png` and his card `PlayerBoy.png` replaced. His Head joint is at 0.846 of his height, so at the same neck height (1.5) he stands 1.77 m (`PlayerRoster`, was 1.73). His **bicycle** is a prop of its own (`Bicycle.fbx`, `BicycleAtlas.png`, made to the game's metres): parked on the lawn of the home front at the start of every story level (`LevelBuildKit.OwnBicycle`, the character shader with its atlas from `ArtBaker`), in place of the Street kit's bicycle, which stays the fallback. `GeneratedContent.Version` is 66.
- **Not redone:** the app icon (`app_icon.py`) and the L01 sticker (`sticker_art.py`) still show the earlier boy; `teen.py --boy` still builds that boy (and would overwrite these files).
- **Look at these in Unity:** his texture at play size (it carries all the detail: the hand-painted face, the shirt's lines), the cut seams on the inner legs and the fists (closed with flat one-colour patches), the bicycle's thin frame and spokes at the home front (and whether it faces and leans the right way), and his outline width against the street.
- **Note:** the supplied file is named after a character from an animated film; the game calls him only "the boy". Whether the model can be shipped is a question of the generator's licence and the character's likeness, for the user to settle before release.

## Every place sounds like itself; a real double jump

**Not run in Unity.** Checked offline: the audio code (`Synth`, `Mixdown`, `Instruments`, `MusicGenerator`, `AmbienceGenerator`, `Soundscape`, `SoundBank`) compiled and run under .NET 8 (C# 9) in a scratchpad harness that renders every loop, bed, cue and sound effect to WAV: no invalid samples, no clipping, loudness as designed, spectrograms looked at; `AudioDirector` compiled against stand-in Unity types. The animation and FX changes were not compiled.

- **Music by place** (`Audio/MusicGenerator`): one 16-bar stereo loop (A and B halves, each with its own chords and lead, a drum fill into each) for each of the six routes and the menu, keyed by `Soundscape` (`Audio/Soundscape`; the underpass and the building site, both chapter 4, now differ). Menu: lo-fi electric piano sevenths, vinyl crackle. Home Street: strummed acoustic guitar, glockenspiel then a whistled flute tune, claps, shaker. Market: accordion oom-pah, a swung accordion tune then a tremolo mandolin, tambourine and brushes. Beach: calypso with marimba off-beats, steel pan, congas, a ukulele. Underpass: a dark, echoing groove (pulsing synth bass, electric-piano stabs in a big reverb, sixteenth hats). Building site: a bouncy D-dorian work-song with a square-wave whistle, clavinet-like stabs and an anvil on the off-beats. Park: harp arpeggios, strings, flute and celesta. Tunes are built from motifs that come back; strong beats land on chord tones. A new mixer (`Audio/Mixdown`) pans each instrument, adds a shared reverb sized for the place whose tail wraps round the loop, and matches every loop to one loudness. New instruments in `Audio/Instruments`.
- **Ambience** (`Audio/AmbienceGenerator`): a 30-second seamless stereo bed for each place, and cues played over it at random times, sides and pitches (`AmbientCue`): Home Street (traffic, cars and vans passing with a Doppler drop, horns, bicycle bells, a dog, the church bell, sparrows, a pigeon); Market (a murmuring crowd, cups at the cafe, a shop's door bell, a trolley on the cobbles, pigeons taking off, the clock, laughter); Beach (waves breaking and drawing back, surf, wind, gulls calling and laughing near and far, a buoy's bell, a ship's horn, a splash); Underpass (rumble and strip-light hum, water dripping in the echo, a train crossing overhead with its wheels clacking, footsteps, pigeons' wings, cars above); Building site (diesel generators, wind, a reversing lorry's alarm, jackhammers, hammering, a digger revving, a drill, air brakes, dropped pipes, a passing truck); Park (leaves, the fountain, robins, great tits, a blackbird, wood pigeons, ducks, a woodpecker, a dog, a bicycle bell); the menu a soft breeze and birds. Everything sits under the music (the bed about 8 dB below it at the default volumes).
- **AudioDirector**: works out the soundscape every frame (the level's route, the Holiday Run's current stage's route, or the menu), synthesizes music and ambience on worker threads, crossfades both, schedules the cues (passing vehicles pan across), keeps the last three places ready, and turns everything down in the pause menu. **Settings** gains an **Ambience** slider between Music and Sound effects (`GameSettings.AmbienceVolume`, `settings.ambience`; the card is 30 px taller, rows 4 px shorter).
- **Sound effects** (`Audio/SoundBank`): jump (a trainer's push-off, grit, a swish of clothes), double jump (a rush of air and a breath, no chime), landing (two feet, grit), ball bounce, coin, dog, gull, splash, the goal's crowd (a cheer and applause) and the bump's "oof" redone with filtered noise and formants.
- **Double jump** (`Presentation/FxDirector`, `Presentation/KidAnimator`): no shock rings, stars, glitter, landing ring or crescent of light (and no camera pull-back). The somersault is gone: the second jump is a second push, upright: the lead knee driven up, the other leg stamping down, both arms swung up hard; then both knees gathered up, arms out for balance, and the legs reaching for the ground (`airJumpDuration`, was `flipDuration`; `flipDegrees`, `flipCentreLift`, `swooshSize` and `ProceduralSprites.Swoosh` removed). The ordinary jump's pose drives the lead knee with the take-off leg left long behind; the cartoon stretch on take-off and squash on landing are a third of what they were. The physics are unchanged (levels are built to the jump's reach).
- **Tests:** `MusicLoopsForEverySoundscape`, `EveryRouteHasItsOwnMusicAndAmbience`, `AmbienceSitsUnderTheMusicAndNeverClips`.
- **Listen and look in Unity:** the balance of music, ambience and effects on a phone's speaker and on headphones (`MusicGain`, `AmbienceGain`, `MusicGenerator.Loudness`, `AmbienceGenerator.BedLoudness`, each cue's `volume`); how long the first synthesis takes on a slow phone (about a second per loop on a desktop; the music starts when ready); the crossfades between stages in the Holiday Run; the new double jump's pose at play speed.

## The music, chilled out

**Not run in Unity.** Checked offline as before (the audio code under .NET 8, every loop rendered and measured; `AudioDirector` against stand-in Unity types).

- The user found the loops harsh and asked for cool, chill music in the style of lo-fi / chillhop beats. `Audio/MusicGenerator` is now one chillhop arranger (`Chill`) with a `Style` per soundscape; all the music is original. Shared sound: rootless jazz voicings of seventh, ninth and thirteenth chords (the chord parser gained `maj9`, `m9`, `9`, `13`, `m7b5`); a Rhodes-style piano or a mellow picked guitar; a round sub or upright bass with walk-ups; a swung boom-bap kit (snare a hair late, ghost notes, dark hats); the chords ducking under each kick; a soft lead; vinyl; the drums dropping out for the last half bar.
- Per place: menu (Rhodes, vibes, 80 bpm), Home Street (guitar and Rhodes, flute then vibes, 86), market (ii-V-I, upright bass, melodica, 90), beach (marimba off-beats, steel pan, kalimba, congas, side-stick, 84), underpass (minor ninths, half-time, big reverb, 76), building site (dorian, guitar and kalimba, busier kick, 88), park (harp, strings, flute, half-time, 78).
- `Audio/Mixdown` gained a tape master: a two-pole low-pass (`tone`), saturation (`drive`), a seamless wow (`wowCents`, `wowCycles`), and side-chain ducking (`Duck`, `Track.duck`). `Audio/Instruments` is now the soft band only (Rhodes, pad, strings, vibes, kalimba, flute, melodica, a soft-picked string, marimba, steel pan, sub and upright bass, the dusty kit, vinyl); the square lead, accordion, mandolin, clap, tambourine, anvil and bright hats are gone. Energy above 3 kHz is 15 to 20 dB lower than before. `Loudness` is 0.14 (was 0.16).
- **More energy** (the user found it too sleepy): tempos 92 to 104 bpm (were 76 to 90), no half-time grooves, lighter swing; a punchier kick and snare with sixteenth hats, ghost notes, an open hat in the second half and a snare fill into each half (the drums no longer drop out); a bouncing bass line (octave pops, pushes, walk-ups); the Rhodes plays short rhythmic stabs and the guitar funky sixteenth chops; the leads use the bouncier rhythms; less ducking on the keys, less wow and saturation, the tape's low-pass opened 700 Hz. Still well under the old loops' top end (about 10 dB less above 3 kHz).

## The music goes West Coast

**Not run in Unity.** Checked offline as before (the audio code under .NET 8, every loop rendered and measured).

- The user asked for a more American, Californian style. `Audio/MusicGenerator` is now an arranger (`Arrange`) of sunny West Coast styles, all original, one per soundscape: a fingerpicked sunset with an organ for the menu (96 bpm), jangly beach pop on Home Street (strummed clean guitars, claps, tambourine, "ooh"s, glockenspiel; 118), West Coast funk in the market (Rhodes stabs, sixteenth guitar chops, the synth whistle; 106), surf rock at the beach (palm-muted eighths, a twangy tremolo-picked lead through spring reverb, an organ, tom fills; 132), a smooth West Coast groove in the underpass (held Rhodes ninths, a gliding whistle, sub bass, claps, swung hats; 94), garage surf on the building site (D mixolydian; 126) and sunny folk-pop in the park (strummed and fingerpicked acoustic, "ooh"s; 112). Each half opens with a crash and a fill leads into it.
- New in `Audio/Instruments`: `CleanGuitar` (chorused, or palm-muted), `Jangle` (strums), `SurfLead`, `Organ`, `Whistle`, `Oohs`, `Glock`, `Clap`, `Tambourine`, `Crash`, `PickBass`. The tape wow and heavy low-pass are off; the mix stays warm (energy above 3 kHz about 26 to 30 dB under the whole, against 18 to 20 for the first, harsh loops).

## The look, matched to the reference shots (generated content v67)

The user's reference shots and our own screenshots were measured side by side (verified swatches of the same surfaces, plus tone and saturation statistics with the HUD masked out), then the game's light, grade and ground colours were solved against them with a Python copy of `DtsShade`, `Sky.shader` and the PostFX grade (it reproduces our old screenshots to within about 10 levels). This reverses most of v38's "calmed" palette. On-screen targets are now written into `docs/ART_DIRECTION.md`.

- **What was wrong.** The sky was too light and cyan ((73, 134, 206) at the top against (57, 109, 175)); paving rendered cream, nearly white ((235, 223, 201) against about (196, 190, 187)) because three warm multipliers stacked (the sun's colour, the shader's warm world-scale patches and the grade's gain); whites clipped to 255; the darkest tones sat at 0.11 luminance (the references' at 0.04); cast shadows were only 0.6 of the lit ground (the references' 0.2 to 0.3, dark navy) and mostly hidden, as the sun shines from behind the camera; tree crowns were bright and olive with no dark inside; sand was yellow ((255, 230, 183) against (222, 187, 161)); the sea a saturated deep cyan; walls in sun showed rows of little dashes (shadow acne).
- **Light** (`ChapterTheme` moods, `WorldLook` defaults): a near-white sun (1, 0.985, 0.96); the cobalt sky, zenith (0.249, 0.449, 0.719), horizon (0.301, 0.53, 0.718) before the grade; a mid-blue haze (0.34, 0.54, 0.75) at 0.45 from 50 m, so distance goes deeper blue instead of pale; shadow strength 1.
- **Deeper ground shadows** (`DtsLook.cginc`): a sun shadow falling across a lit face takes the shade colour, and on upward-facing ground it is multiplied again by the new `_DtsCastShadow` (0.6, 0.6, 0.64, `WorldLook.castShadow`, `Mood.castShadow`), so the road and paving get the dark navy shadows while walls in shadow keep the plain shade. The world-scale patches lean rosy and cool instead of yellow and blue.
- **Shade across the near road** (`StreetBuilder.CanopyShadows`, every chapter but the beach, in plain levels, in a level's home street and in the Holiday Run's stages): street trees on our side of the road that cast shadows but are not drawn (ShadowsOnly), placed from the sun the scene is lit by (a level's home street uses the level's own sun) so their dappled shade lands across the foreground (depth about -5, crowns squashed front to back so it stops short of the footpath), as in the references. They sway with the breeze like the other trees.
- **The grade** (`PostFX`, rewritten): balance (1, 1, 1.01), a toe (below 0.28 tones sink toward 0.7 of themselves), contrast 1.1, a shoulder from 0.8 easing toward 0.96 (no more clipped whites), vibrance 1.12 on greys and soft colours and 1.0 on strong ones, a faint cool shadow tint and faintly mauve mid-greys. `Mood.lift`/`gain` became `shadowTint`/`balance`; the grade's colours are sent as vectors so they are never colour-space converted. Bloom 0.12.
- **Materials**: paving 0.69 (was 0.8) and kerb 0.8, neutral to faintly rosy; concrete 0.71; asphalt a mid mauve-grey; rosy peach sand; fresher, sunnier lawns; a soft turquoise sea; tree and bush tints true leaf greens (about (0.29, 0.39, 0.2)), hedges a deep green; leaves take sun shadows at 0.7 (was 0.4) so crowns go dark inside; contact shadows under the kid and ball near-black navy at 0.62 (was 0.4); building contact shadows darker; the horizon's bright band fainter.
- **Shadow acne**: shadow bias 0.1, normal bias 0.9, high-resolution shadow maps, 35 m shadow distance.
- **Menus**: `UITheme.SkyTop` is the on-screen cobalt; `SkyBottom` stays a lighter blue so panels and text on it read; the splash background matches.
- Checked: the runtime and editor scripts compile (Mono against the reference DLLs, as above); `GroundArt` was run under Mono with small Unity stubs to render the new textures, and a numpy ray-traced street through the game camera (old vs new light, textures and grade) was compared with the references. Not checked: the shaders in Unity, and the look on a device. On the first open, look at L01 and L13 against the reference shots, check that the canopy shade lands on the near road and not the footpath in every chapter (and in the Holiday Run), and that no acne is left on the house fronts.

## The look, exactly on the reference numbers (generated content v68)

Following up v67, the light, grade and materials were solved again so the predicted on-screen colour of every surface on the comparison card equals the reference value (sky top and low, a white wall in sun, paving and asphalt in sun and in tree shade, sand, sea, lawn, a tree's sunlit clumps and the inside of its crown). The model is the same Python copy of the shader and grade, calibrated on today's screenshots.

- Grade shoulder 0.84 easing to 0.972 (was 0.8 to 0.96), and a sun of (1, 0.979, 0.962): white walls (paint 0.95, 0.95, 0.93) come out at (227, 223, 217).
- Sky zenith (0.234, 0.421, 0.67), horizon (0.306, 0.537, 0.733) before the grade (beach and city keep their small offsets).
- Per-surface shadow tints (`ArtBaker.SurfaceShadowTint`): paving, kerb and concrete (1.137, 1.057, 1.132), shade about (70, 68, 88); asphalt (0.203, 0.234, 0.081), shade about (26, 25, 34). One global cast colour can't give both: the references darken the road far more than the paving.
- Materials: paving slab (0.667, 0.678, 0.685); asphalt base (0.536, 0.516, 0.526); sand (0.801, 0.677, 0.597); sea mid (0.373, 0.657, 0.752); lawn lush (0.637, 0.734, 0.379); each texture's other colours scaled with its base.
- Leaves: summer tints about (0.24, 0.33, 0.21), the Plants kit's shade tint (0.728, 0.006, 2: the top of the shader's low-precision range) so crowns go a cool, nearly neutral dark inside, leaf shadows 0.685.
- Not checked in Unity or on a device; the same first-open checks as v67 apply, and look at whether the plants' cooler shade suits grass and flowers as well as trees.

## A California coast town (generated content v69)

(Since v71 this is the California skin, not the levels' own look: see below.) A sunny California coast town, after the user's reference photos (suburban streets of stucco villas, Craftsman porches, palms, a beach pier, beach-town main streets).

- **The Coast kit** (`Art/Models/Coast`, `tools/blender/kit_buildings_cal.py`, built by `kit_buildings.py --kit Coast` with its own atlas because the Buildings atlas is full): `VillaStucco` (two storeys of stucco, hipped terracotta roof, arched entry and picture window, iron balconette, a garage under its own hip), `VillaRanch` (single storey, a garage forward of it, solar panels, a porch column), `CraftsmanPorch` (white lap siding, a deep front porch with columns and a rail), `BeachCondo` (white, glass balconies, a roof deck), `ShopBeach` ("SURF & SUN": stepped parapet, awning, sign), `ShopMission` ("Casa Del Mar": a curved Mission parapet, arched windows, a tiled pent roof on brackets), `PierSpan` (12 m of timber deck on concrete pile bents, white rails, a lamp) and `PierEnd` (a wider platform with an octagonal roundhouse). The new `hip` roof and the atlas' `hip` feature paint Spanish barrel tiles.
- **Plants**: `PalmFan` (a 16.5 m California fan palm with a skirt of dry fronds) and `PalmDate` (a thick-trunked date palm). The other plants are unchanged.
- **Streets** (`StreetBuilder.Coast.cs` and the chapter builders): the home street deals villas, ranch houses, Craftsman porches and the gabled house on wider lots (10.5 to 14.5), set back for their porches and garages, behind picket fences, low hedges or open lawns (no more block walls); date palms in the front gardens and side yards, young fan palms in the back gardens; a back row and a far row of villas; the market deals the surf and Mission shops among the town's shops (the noodle house and convenience store are out), date palms between the shops instead of drinks machines, and beach condos among the flats behind; the beach gets a pier once per level (13 spans and the end) and date palms along its back; every chapter but the beach has a skyline of tall fan palms 64 to 110 back. `KitOf` says which kit a building model lives in.
- **Japanese details replaced**: the utility pole is a wooden pole with a wooden crossarm and no hazard sleeve; the shop signs are English and Californian (Sunset Market, café marina, Seaside Books, Malibu boutique, a vertical "DENTAL" sign).
- `preview_street.py` mirrors the new layout (it rendered chapters 1 to 3 for review). The Buildings, Street and Plants kits still rebuild identically apart from the intended changes (the pole, the signs' pixels, the two palms).
- Not checked in Unity: the new FBXs' import, the levels with the new houses (lot fits, porches clear of the fences, the pier at every beach level and the Holiday Run's), and performance with the extra palms and the pier.

## High-detail textures for the California town and the plants

- **Coast kit**: its own 4096 x 4096 atlas (`KIT_ATLAS`, set by `kit_buildings.py --kit Coast`) painted at 96 px/m on the fronts, 48 on the sides and 56 on the roofs (it was 34, 23 and 25 on a 2048 x 4096 sheet): a villa's front is about 1290 px across (was about 410), a shop's about 900. Glass, wood and the Coast signs are tiles at twice the size; the Buildings kit's other signs and shop interiors are left out of the Coast atlas. The piers keep half that density (they are seen from far off).
- **Hipped roofs in geometry**: each hip is now stepped courses of tiles (inset rings with a proud, shadowed lip at each row's lower edge), under the painted barrel tiles, so the courses catch the light.
- Fixes found at the new detail: the fanlights over arched windows show clear glass (they showed a curtain), the Mission shop's arched windows no longer leave holes beside the arch, and the bracket in front of its sign is gone.
- **Plants atlas** 2048 x 2048 (was 1024): every leaf sprite, bark, birch, cherry, palm trunk, frond and hedge tile at twice the resolution. The UV insets keep their 1024 values and the painters' pixel sizes scale with the atlas, so the models are unchanged (identical manifest; the FBXs differ only in their timestamps) and every mark stays where it was, sharper.
- The Buildings kit (the town's older houses and shops) stays at its 2048 x 4096 atlas, which is full; doubling it would need an 8192-tall sheet.

## The California town remodelled for quality (generated content v70)

The user found the first Coast models plain next to their reference shots (weathered, lived-in anime streets) and real California photos. The models were remodelled for that look:

- **Weathered stucco** (`kit_buildings_atlas.py`, the `stucco` wall style, Coast kit only): broad soft blotches of the mix and the sun, a sand finish, faint trowel arcs, patches of newer paint, dust settled under eaves and ledges, longer rain streaks under sills and fixtures, soil and splash up the base, an occasional hairline crack from an opening's corner.
- **Glass that reads as glass** (`glass_hi`): dark, deep panes with the sky caught only along the top, reflected tree crowns, the room behind just visible (ceiling, back wall, furniture), the frame's shadow; sheer curtains, a blind, a lit lamp as variants; no painted glare stripe. Shopfronts show a lit interior; the condo's balconies are glass sheets, not solid panels.
- **Clay tiles**: burnt and sun-bleached tiles among the terracotta, deep channels, rain-darkened lower courses, lichen freckles. **Garage doors**: dust at the base, drips, a glazed top section.
- **Lived-in detail** (`kit_buildings_cal.py`): white aluminium gutters and downpipes, ground-standing AC condensers on pads with the line set up the wall and a disconnect box (no wall-hung split units), meters, foundation and garage vents, clay roof vents, hose taps, house numbers, a mailbox, window surrounds and grid muntins, rooftop condensers and rainwater heads on the flat roofs, surfboards at the surf shop, hanging baskets at the Mission shop; solar panels seated on the ranch's front hip.
- **Palms**: the fan palm's crown denser with a skirt of dry fronds (24 fronds, 11 dry), the date palm fuller (30 fronds).
- **Colour**: muted, sun-softened stucco and clay schemes (`StreetBuilder.Coast.cs`, the kit's base colours).
- **The home street** now deals only the Coast houses (the European gabled house is out of its decks), on 12.9 to 15 lots so every house fits.
- Checked: close-up and street renders in Blender (Eevee), the C# compile. Not checked in Unity.

## The California skin, the boy's satchel, quieter park, glass HUD (generated content v71)

- **California is now a skin, the original streets are back.** Each level has two scenes: its original (built exactly as before v69: the concrete utility pole, the Japanese shop names, the gabled houses and block walls) and `<scene>_CA`, built with `LevelBuildKit.California` set, which gives the Coast kit's streets (`StreetBuilder.Coast.cs`: `CA` gates every change, and the original path keeps its random draws in their old order so it comes out as it was). The skin's assets are separate files: `Street/UtilityPoleWood.fbx` (`kit_street_m1.utility_pole(wood=True)`) and `Buildings/BuildingsCAAtlas.png` (`KIT_SIGNS=CA kit_buildings.py`; ArtBaker makes `KitBuildingsCA` from it and `KitModel` draws the Buildings kit with it in the California scenes). `BuildingsAtlas.png` and `UtilityPole.fbx` are main's again.
- **Unlock and switch**: `Progression/CaliforniaSkin` is unlocked when every story level (every leg of every route) is finished; Settings has a "California skin" toggle under Controls (locked, with "Finish every level to unlock", until then), saved in `SaveData.californiaSkin`. `LevelManager.LoadLevel` loads the `_CA` scene while it is on (and the build has it). The results card's "every way walked" line points to it. The Holiday Run keeps the original look.
- **The teen boy's satchel**: the supplied boy model has no bag, so `LevelBuildKit.Satchel` hangs a leather satchel (`Presentation/SatchelShape`: flap, welt, strap and brass buckle) on his Bag bone at the hip, its strap over his chest on the Chest bone, in every scene he is built in.
- **Park audio**: the leaves in the park's ambience bed were a bright 2.6 to 2.9 kHz fluttering hiss at 80 % that drowned the music, the fountain and the birds. They are now a soft 1.3 to 1.5 kHz rustle at 30 % with a slower flutter, the birds are louder in the bed, and the whole bed sits at RMS 0.045 (`AmbienceGenerator.ParkBedLoudness`; the other places stay at 0.075), so the park's music and sounds carry. (Checked by generating every place's music and ambience in a harness: all render; the park bed measures RMS 0.045.)
- **Glass HUD**: the level card (top left), the pause button, the coach's tips, the controls tour's caption with its Next and Skip, and "Stuck?" are frosted glass like the touch controls (`UIKit.Glass`, `UIKit.GlassButton`, `UIKit.GlassText`, `ProceduralSprites.RoundedRim`, `UITheme.Glass*`): a faint smoky pane under a thin bright rim, white lettering on a soft drop. The Holiday Run's score card and pause button too.
- Checked: the C# compile (runtime and editor). Not checked in Unity: the `_CA` scenes' build (it doubles the level build time), the satchel's fit on the boy's rig, the glass HUD's legibility over bright scenes.

## Ambience at realistic levels

- **Each place has its own bed loudness** (`AmbienceGenerator.BedLoudness`, RMS; every bed was 0.075): beach surf 0.06, building site 0.055, underpass 0.048, home street 0.045, market 0.035, park 0.035, menu 0.03. The cues (cars, gulls, the shop bell...) scale with the square root of their place's ratio to the old 0.075.
- **The market**: its bed was twelve chattering voices, a crowd's wall of talk on a street with a handful of people. Now four soft, distant conversations (more reverb, at about a quarter of the gain) under the town's hum and the breeze; the cafe's clinks softer; the laugh cue half as loud and half as often.
- **The Ambience slider defaults to 0.5** (was 0.8; `GameSettings.DefaultAmbienceVolume`). A slider already moved keeps its value.
- At the default, against before: the market about 11 dB quieter, the street 8, the beach 6. Checked by rendering every place's bed in a harness (the RMS above); not listened to in Unity.

## Add-ons and Filters; music by country; a runner's coin

- **Settings, Add-ons & Filters** (`UI/AddOnsPanel`, opened from a button under Controls; `Progression/AddOns` replaces `CaliforniaSkin`). Add-ons are cards to choose from: **Original, Kamakura, Japan** (the original streets: Japanese shop names, concrete poles, block walls, the railway), **California, Santa Monica, USA** (unlocked by finishing every story level: the `_CA` scenes), and **India, Mumbai** and **Tokyo, Japan** shown as coming soon. Filters list **Original** (the only one so far) with "comic-book, sketch and more coming soon". Saved as `SaveData.addOn` and `SaveData.filter`; an older save's California switch carries over. A choice applies from the next level loaded.
- **Music by country** (`MusicCountry`, `MusicGenerator.Generate(scape, country)`): the original town now has Japanese city pop and J-pop, one loop per place, mostly on the "royal road" chords (IVmaj7, V7, iiim7, vim7), with pentatonic yonanuki tunes (new `Mode.Yona`, `Mode.YonaMinor`) on a koto-like pluck (`Lead.Koto`) or a breathy bamboo flute (`Lead.Flute`), Rhodes, guitars and a glockenspiel. The West Coast music (surf, beach pop, funk, folk-pop) is now California's. `AudioDirector` keys the music by place and country and takes the country from the loaded scene's add-on (the menu: the chosen add-on; the Holiday Run: the original).
- **Coin**: an endless runner's crisp arcade "bling" (a short triangle blip up into a bright, fast-ringing bell with a little shimmer; 0.32 s, was 0.55), played at 0.26 (was 0.5). **Whistle** (level start): softer, lower (2.25 kHz, was 2.6), shorter (0.38 s), less breath, at 0.28 (was 0.6).
- Checked: the C# compile; every place's loop renders in both countries' styles (RMS 0.14 each), the coin and whistle render. Not listened to in Unity.

## The comic halftone filter (generated content v72)

- **Settings > Add-ons & Filters** now offers **Comic halftone** beside Original (`AddOns.ComicFilter`, saved as `SaveData.filter`). It applies at once and in every scene: `World/PostFX` reads the setting every frame. The "more filters" line moved beside the Filters heading ("Sketch and more filters coming soon") so two filter cards fit a row; the note says a filter applies at once.
- **The look** (`Shaders/PostFX.shader`, passes 4 and 5; the grade is now `GradeColour` + `Vignette`, shared with pass 3): punchier colour, cel bands on the street's mid and dark tones (the light tones stay smooth), a 45-degree halftone dot screen in the shade, hatching in the deepest shade, an ink line from the camera's depth and normals (outlines and creases from the shapes, never the textures; fades out by 90 m), then the red and blue plates out of register toward the frame's edges, warm paper and a faint grain, and the vignette last. Every size is in pixels at 1080 lines and scales with the screen. The tunables are on the PostFX component (with **Force Comic** for looking at it in the editor).
- **Faces and eyes stay as drawn.** `ToonCharacter` writes a new `_ComicWorld` into the picture's alpha (both the toon pass and the ink hull): 0 for the kids, the passers-by and the ball, 1 for the cars and the bicycle (`ArtBaker`). On a figure the filter draws no bands and no creases, slips the plates hardly at all and puts only light dots, so the painted eyes, brows, blush and highlights come through untouched under the figure's own outline. (The first mock-ups traced lines from the picture, which turned eyes into black dots.)
- **Cost:** while the filter is on, the camera also renders `DepthTextureMode.DepthNormals` (one more pass over the opaque scene) and the picture takes two full-screen passes instead of one. Off, nothing changes. A camera buffer without alpha (RGB111110 HDR) has no mask: everything is then drawn like the street.
- **Checked:** the C# compile (runtime and editor, Mono against the 2021.3 module DLLs; the Unity 6-only build and signing scripts left out as before); every PostFX pass compiled as HLSL by glslang with stand-ins for UnityCG; a numpy port of passes 4 and 5 (`review/filter/shader_port.py`) run over Blender renders of the game's own models (buildings kit, the Hatch, Boy, PrimaryGirl, the ball) from the game camera, with colour, depth, normals and the mask (`review/filter/render_street.py`, `apply_filter.py`). With the mask the girl's eyes match the unfiltered render; without it the line crosses her ear and hairline.
- **Comic words** (`UI/ComicPops`, `UI/ComicLettering`, `Resources/Shaders/ComicLettering`, Bangers in `Resources/Fonts`, SIL OFL): while the filter is on, the big moments pop up as comic sound-effect lettering by where they happen, above the kid's head so faces stay in view: THWACK! (a hard kick; THUMP! a medium one), NICE TOUCH! / NICE x3!, BOINK! on a juggle and "10 IN A ROW!" every fifth, WHOOSH! (double jump), SKRRT! (slide), BOING! (springboard), SPLASH!, SQUAWK! (gull), WOOF! (dog), OOF! (passer-by), CLICK! (gate button), WHOOPS! (ball lost), MADE IT! (GOAL! in a challenge) in the middle of the screen. The loudest have an ink starburst. The lettering is the mock-ups': a thick ink stroke and hard drop shadow, a yellow-to-orange fill (cool white-to-cyan for the bouncy ones, white-to-pink for the ouches) with halftone dots over its lower part. They slam in past full size, settle, hold and swell as they fade (unscaled time, so the goal's slow motion doesn't slow them). Few at once: at most three, a quieter word gives way to a louder one that has just popped, no word twice in a row. Booted once (`RuntimeInitializeOnLoadMethod`) and listening to `GameEvents`, so story levels, challenges and the Holiday Run all have them; an overlay canvas under the HUD that takes no touches and keeps words inside the middle of the screen. With the words on, the HUD's toasts that were only exclamations (perfect touch, juggle count, squawk, oops) give way to them; the toasts that tell you something stay. Spanish words too (¡ZAS!, ¡QUÉ TOQUE!, ¡LLEGUÉ!...). Previewed with the code's numbers over the filtered frame (`review/filter/pops_preview.py`, `5_word_pops.jpg`); not seen in Unity.
- **Not checked in Unity:** the shader on device GPUs (Metal, Vulkan, GLES3), the depth-normals texture's orientation (the shader flips it where Unity's picture is flipped), the cost on a low-end phone, how leaf cards that sway in the wind line up with their (unswayed) depth-normals edges, and the alpha mask under sprites and particles drawn over a figure (they lift the mask a little where they overlap).

## Comic filter on the characters; Add-ons & Filters on the title screen; coins at head height

- **The comic filter now takes the characters and the ball too** (`Shaders/PostFX.shader`): the punchier colour, the cel bands, the full halftone dots (`PostFX.characterDots` 1, was 0.45) and the hatching apply to everything. A figure (ToonCharacter `_ComicWorld` 0) still gets no creases from the ink line (a nose, a cheek or an eye's edge would cross the painted face: the first mock-ups' black-dot eyes) and its plates slip half as far, so the eyes stay crisp; its outline is the depth jump plus its own ink hull. Checked with the shader port over the Blender renders: dots on the skirt, satchel and trousers, deeper shade, the girl's eyes as drawn.
- **Add-ons & Filters moved to the title screen**, after Stickers (`FrontEnd/TitleScreen`: the row is now Locker Room, Stickers, Add-ons & Filters, Settings, four 176-unit buttons; the new one orange with a two-line label, `menu.addons`). Its row in Settings is gone; the "every way walked" message points to the title screen.
- **Coins at head height** (`Pickups/Coin`): the kid's capsule is 1.2 m tall but the teens stand about 1.6 m, so a coin at head height (Tunnel Run's row at 1.6 m in the underpass, and others like it) passed through the drawn head untouched unless you jumped. A coin is now also taken when it overlaps the kid as drawn: a column from the feet up to the visible model's height (measured once from its skinned meshes, 1.2 to 1.9 m), as wide as the capsule plus the coin, scaled down with the capsule during a slide. Measured once a frame for all the coins; the trigger still works as before (and for the ball).
- **The comic words' starburst** (`UI/ComicPops.BurstSprite`) is a star polygon with straight edges and sharp points (14 spikes of uneven length, a thin ink edge, a pale heart at half size), no longer a curved "sunflower"; drawn at boot, not on the first pop.
- Checked: the C# compile (runtime, editor), the PostFX passes through glslang, the previews (`review/filter/5_word_pops.jpg`). Not run in Unity.

## Coin pickup across every level

- **The cause:** the kid's capsule is 1.2 m tall but the kids are drawn about 1.6 m, so a coin at head height went through the drawn head untouched unless you jumped. 23 coins in 9 levels sit in that gap, 1.48 to 1.74 m above the ground under them (Up the Hill 3, Market Morning 4, First Crossing 2, Corner Shop 2, Fruit Stalls 2, Rush Hour 2, Sandcastle Sprint 2, Building Site 2, Tunnel Run 4). Since the last change a coin is also taken when it overlaps the kid as drawn (`Coin.KidReach`), which takes all 23 with no jump, in the Holiday Run too (it uses the same Coin).
- **A safety net in every scene** (`Coin.Settle`, when a level starts): a coin sunk into a static solid (a wall, a ceiling, a step, the ground) or hung higher above the ground under it than a double jump reaches (`JumpReach.HighestCoin`, 3.55 m) moves to the nearest clear, reachable spot straight up or down (up to 3 m) and says so in the editor's console and development builds. Coins over an open pit are left as they are (they show the jump). Crates, moving platforms and one-way platforms don't count as solid.
- **An audit of every layout** (`tools/coin_audit.py`): rebuilds each story level's and challenge's colliders from `GreyboxLevels.cs` with LevelBuildKit's sizes (ground, platforms, walls, parked cars, steps, awnings, slide-under barriers, gates, tunnel and walkway roofs), what the kid can stand on (those, ramps, crate stacks, moving platforms, within a sideways jump of 1.2 m) and the springboards' and fountains' reach, and checks every coin: buried, down a pit, or out of reach. All 441 coins pass. The coins up in the fountain jets (Fountain Square's 5 m one) are the ball's to collect, as the sign says. Planted bad coins (in a wall, in a tunnel roof, 4.2 m up, down a pit) are all caught. Run it after changing a layout: `python3 tools/coin_audit.py`.
- Checked: the C# compile; the audit. Not run in Unity.

## The pencil sketch filter

- **Add-ons & Filters** now offers **Pencil sketch** beside Original and Comic halftone (`AddOns.SketchFilter`). The filter cards are two a row (two rows now); the cards are a little shorter (132, gap 16) so two rows of add-ons and two of filters fit the modal. "More filters coming soon" stays beside the heading.
- **The look** (`Shaders/PostFX.shader` pass 6, one full-screen pass; `World/PostFX` settings under "Pencil sketch filter", with **Force Sketch** for the editor): warm drawing paper with a fibre grain; a faint wash of the picture's colour (`sketchWash` 0.12; 0.6 makes it coloured pencil), patchy like a wash; pencil hatching by tone (45 degrees below 0.78, crossed below 0.52, a denser third set below 0.3), strokes of finite length with gaps, a wobble and pencil grain; the sky left open; the outline drawn twice with a wandering offset (`lineJitter`), from the same depth-and-normals ink line as the comic filter; the paper's edge darker. The kids, passers-by and ball keep their colour (`figureWash` 0.75), lighter hatching and no creases, so the kid is easy to find and the painted eyes stay clean. Noise from a 256 x 256 random texture made once in code.
- **The comic words** (THWACK!, WOOF!, MADE IT!...) show with the sketch filter too (`ComicPops.On`), and the HUD's exclamation toasts give way to them as with the comic filter. **On the sketch they are drawn in pencil:** `ComicLettering.sketch` draws a thin graphite line (0.05 of the size) twice, the second a little off, and a faint smudge for a shadow; the fill runs from paper white into a soft coloured-pencil wash (warm, cool or pink by the word) with pencil hatching over its lower part (`_Hatch` in `Resources/Shaders/ComicLettering`, 6 px strokes at 45 degrees with a grain) instead of halftone dots; and the starburst is the same sharp star in pencil (`BurstSprite(true)`: a yellow wash hatched across the spikes, a paper heart, a thin graphite edge and a second outline turned slightly). Previewed with the code's numbers (`review/sketch/5_sketch_words.jpg`).
- Previewed before building (`review/sketch/`: `sketch_port.py` over the Blender renders of the game's models; pencil and coloured pencil). Checked: the C# compile (runtime, editor), every PostFX pass through glslang (it caught `line`, a reserved word in HLSL). Not run in Unity.

## Max, the backpack boy (generated content v73)

- **A third teen to play**: Max (`PlayerRoster` id `backpackBoy`, model `BackpackBoy`), from a textured Meshy model the user supplied: ginger hair, a light denim jacket open over a grey hoodie and a white T-shirt, dark jeans, white sneakers and a brown backpack on both shoulders. He stands 1.75 m (his Head bone 1.536 m up) and is listed with Ren and Hana in the picker's high-school row; "Max" in English and Spanish.
- **The model** (`tools/blender/meshy_teen.py`, see "The backpack boy" in `tools/blender/README.md`): the A-posed scan decimated to 30,000 triangles and scaled like the teen boy; the joints found on the mesh; weights by nearness to the bones in the A-pose (bone heat finds no solution on the scan's layered shells); the arms brought down and the legs in, made the rest pose; the backpack on its own Bag bone (on the Chest) so it swings as he runs and the shop's pennant clips to its top; outfit parts jacket / jeans / hair for the shop's recolours. Files: `Art/Models/BackpackBoy.fbx`, `.json`, `BackpackBoyAtlas.png`, `Resources/UI/PlayerBackpackBoy.png` (the card, `portrait_teen.py --yaw 28`).
- **Checked**: every game pose from the game's yaws with `review_poses.py` (`review/backpack_boy/poses.jpg`; the joints: `joints.jpg`), and the card beside Ren's. `PlayerRosterTests` now expects three teens. Generated content v73, so the levels and the menu rebuild with him in the cast. Not run in Unity.

## Leo from a supplied model, in sneakers (generated content v74)

- **Leo is new** (`PlayerRoster` id `primaryBoy2`, model `PrimaryBoy2`, kept so saved choices stay valid): made from the "first day" Meshy model the user supplied, a primary-school boy with short black hair in a white sweatshirt with purple sleeves, khaki cargo joggers with a red drawstring and a purple backpack. 1.32 m (Head bone 1.104 m up). The scripted boy 2 (`primary.py --boy2`) is no longer used.
- **Shoes**: the model was barefoot, so `meshy_teen.py` gives him sneakers: a shoe shape lofted round each foot (as wide and high as the foot, a tongue up to the collar, a flat 3 cm sole), white with a purple band and heel tab and an off-white sole, coloured by vertex colour over a white patch painted into the atlas's largest unused area; the shoe and the foot inside it are skinned to the foot bone, the shin taking a share up the collar.
- **`meshy_teen.py` now takes profiles** (`--profile backpack_boy` for Max, `first_day` for Leo): the backpack's colour, the outfit parts' colour rules, shoes, height, how much the pack swings, colours that are never an arm's. For Leo it also had to learn arms that hang by the body rather than in an A-pose (each arm found from its own cross-sections, the elbow on the arm's line) and arms that touch it (his forearms rest on his pockets: cut free where a point is relatively nearer the arm than the body, the holes closed, and only each arm's own piece takes its bones). Max was rebuilt with the same script (his joints and parts unchanged within a few mm; the pose sheet looks the same).
- **Checked**: every game pose with `review_poses.py` (`review/leo/poses.jpg`, the feet close up in `review/leo/shoes.jpg`), Max's main poses again, and both cards. Known limits: with his arms raised high (the celebration) Leo's sweatshirt creases sharply at the shoulders, and the hole fills where his arms were cut free can show as a small pale patch on the trousers close up. Generated content v74. Not run in Unity.

## Zoe from a supplied model (generated content v75)

- **Zoe is new** (`PlayerRoster` id `primaryGirl2`, model `PrimaryGirl2`, kept so saved choices stay valid): made from the "rainbow unicorn" Meshy model the user supplied, a primary-school girl with black hair in a long braid, a pink rainbow-unicorn jacket over a white T-shirt, terracotta trousers, black shoes and a backpack in the jacket's print. She stands 1.29 m (her Head bone 1.070 m up). The scripted girl 2 (`primary.py --girl2`) is no longer used.
- **`meshy_teen.py --profile unicorn`**: her pack has no colour of its own, so it is found by its shape (what stands behind her back line, bar the hair), and takes half the game's swing. The jacket is outfit part 1, the trousers 2, the hair with the braid 3. Changes to the script that all three models now share:
  - the arm search drops a scrap by the shoulder (her hood's edge);
  - the crotch must hold for two heights;
  - the neck may not fall below the chin (her hood and braid made the narrowest section fall on her shoulders);
  - a loose bit of a hand left by the arm cut goes with the arm.

  Max's and Leo's joints come out the same with it.
- **Checked**: every game pose with `review_poses.py` (`review/zoe/poses.jpg`, the joints in `review/zoe/joints.jpg`) and her card (`portrait_teen.py --yaw -28 --span-heads 2.3`, the girls turn left). Known limits: the jacket's loose hem folds sharply when she tucks and slides, and a recoloured jacket loses its rainbow (the shop tints it in shades of one colour). Generated content v75. Not run in Unity.

## Mia from a supplied model (generated content v76)

- **Mia is new** (`PlayerRoster` id `primaryGirl`, model `PrimaryGirl`, kept so saved choices stay valid): made from the "little explorer in red" Meshy model the user supplied, an A-posed primary-school girl with shoulder-length black hair and a headband, a white T-shirt, wide red shorts, white socks, pink sneakers and a beige backpack with a bow. She stands 1.27 m (Head bone 1.028 m up). The scripted girl 1 (`primary.py --girl`) is no longer used; Kai is now the only scripted primary kid.
- **`meshy_teen.py --profile explorer`**: her backpack is found by its shape (its beige is close to her skin), and her parts by each face's own texture colour (her texture is cut into many small islands). Two changes to the script shared by all four models: the arm is now the longest run of following outlines (her sleeve's edge was a short run of its own), and when wide shorts hide the crotch the legs are found below the hems and the shorts parted down the middle. Max's, Leo's and Zoe's joints come out the same.
- **Checked**: every game pose including the menu's balance and keepy-ups (`review/mia/poses.jpg`), her outfit parts tinted (`outfit_parts.jpg`), the close-up face, side, back and in-game-size sheet against the street (`sheet.jpg`), and her card. The scanned faces show soft-edged patches of tone up close; that is lighting baked into the scan's texture (smoothing the face, clearing sharp edges and sparing the face in the decimation were tried and changed nothing visible). Generated content v76. Not run in Unity.

## Kai from a supplied model; all four primary kids now from supplied models (generated content v77)

- **Kai is new** (`PlayerRoster` id `primaryBoy`, model `PrimaryBoy`, kept so saved choices stay valid): made from the "little star in plaid" Meshy model the user supplied, a primary-school boy with short black hair, a loose red plaid flannel shirt over a white hood, light-blue cargo jeans, chunky black-and-white sneakers and a grey backpack. 1.30 m (Head bone 1.092 m up). `primary.py` no longer builds any kid in the game.
- **`meshy_teen.py --profile plaid`**: his baggy sleeves are fused to his shirt all the way down, so only his hands show apart from the body. For such arms the shoulders come from the torso's outline, the sleeve is split from the shirt along the seam (faces kept, so nothing is missing at rest; each side's opening closed in its rim's colour), the fingertips fused to the pockets go with the hands, loose crumbs are dropped and only each arm's own piece takes its bones. The grey pack is found by a grey colour rule judged per face.
- **Shared changes** that all five supplied models now get: the hole filling after an arm cut never bridges an arm to the body (it did on Kai), and an arm's own piece takes the chest's pull only above the elbow. Leo, Zoe, Mia and Max were rebuilt with it (Max unchanged in triangles; the others a few dozen fewer) and spot-checked in the run, kick, slide and celebration; their cards are unchanged.
- **Checked**: every Kai pose (`review/kai/poses.jpg`), his outfit parts tinted (`outfit_parts.jpg`), close-ups and in-game size (`sheet.jpg`) and his card. Known limits: flat single-colour patches on his shirt's sides where the sleeves were split, and his plaid stretches at the shoulders as his arms swing. Generated content v77. Not run in Unity.

## Leo and Zoe: arms split from the body instead of cut (generated content v78)

- Compared side by side with Max in the same poses (`review/primary_vs_max.jpg`), the primary kids broke up where their arms had been cut free of their bodies: dark shards of the inside showed through the cut's holes as the arms swung (Leo's shirt and sleeve, Zoe's wrist). Leo and Zoe now get Kai's seam split (`'split': True` in `meshy_teen.py`): no faces are cut out, and each side's opening is closed. The dark shards are gone; Zoe's near sleeve stays whole.
- Tried and dropped: bone-heat weights on a watertight voxel copy (Blender's solver fails on it too) and a much wider weight blend at the shoulders (no visible change).
- What remains: the scans fuse arms that hang against the body, so the hidden sleeve undersides are flat patches, and loose jackets and shirts smear as the arms lift. Generating the models in an A-pose (as Max and Mia were) is what makes them clean. Generated content v78. Not run in Unity.

## Rigid heads: the scanned kids' faces no longer fold (generated content v79)

- On the launch screen the kid's head tilts to follow the ball; on all five supplied kids (Max too) about a quarter of the face was weighted partly to the Neck bone (by nearness the jaw and cheeks were as close to it as to the Head bone), so the lower face lagged and folded. `meshy_teen.py` now makes the head rigid: everything within the head's radius above the jaw follows the Head bone alone, fading to the neck over 6 cm below it. Measured: front-of-head vertices with less than 0.95 Head weight went from 18-29 % to 0 on every kid. Before and after in the menu's balance pose and the tuck: `review/faces_head_tilt_before_after.png`. Generated content v79. Not run in Unity.

## The original primary-school kids are back (generated content v80)

- The four primary-school kids made from supplied models (Kai, Mia, Leo, Zoe) are set aside: in the game their sleeves and jackets smeared as their arms swung (Meshy fuses arms that hang against the body), short of Max's quality. The scripted anime kids (`primary.py`) are back in `Art/Models` and `Resources/UI`, with their old neck heights in `PlayerRoster`. The supplied versions can be rebuilt any time with `meshy_teen.py --profile plaid / explorer / first_day / unicorn`; the way to make them as clean as Max is to generate them in an A-pose.
- Max keeps the rigid-head fix (his face no longer folds on the menu). Generated content v80. Not run in Unity.

## The supplied primary-school kids are back (generated content v81)

- At the user's request the supplied Kai, Mia, Leo and Zoe are in the game again (v80 had put the scripted kids back), now with the rigid-head fix: their faces no longer fold as the head follows the ball. The known limit stays: sleeves and loose jackets smear on Kai, Leo and Zoe as their arms swing (the scans fuse arms that hang against the body). Generated content v81. Not run in Unity.

## Mia's backpack matches her reference photos (generated content v82)

- The user's reference photos of Mia show a light denim backpack with a bow on beige straps; the model had made it all beige. `meshy_teen.py` (`'pack_tint'`, `tint_pack`) recolours the pack's beige in the atlas on the faces that follow the Bag bone, keeping the shading; the straps stay beige. The rest already matched the photos (white T-shirt with a red line, red shorts with white piping, white socks, pink shoes, leopard headband). The seam split was tried on her and dropped: it tore her short sleeves; the cut she had stays. Checked in the run, kick and celebration (`review/mia/denim_backpack.jpg`) and her card. Not run in Unity.

## Mia: straps stay on the shoulders, smoother shoulders (generated content v83)

- The backpack's straps slid off Mia's shoulders as her arms swung (the shoulders' skin went with the arm by nearness). `meshy_teen.py`'s `'shoulders'` blend now moves the short sleeve with the arm over a smooth, wide shoulder blend; the straps stay on (`review/mia/straps.jpg`). Every action audited (`review/mia/all_actions.jpg`): idle, balance, run, jump rise, tucks, kicks, slides, landing and keepy-ups are clean; poses with the arms high (jump fall, launch, open, celebration) still crease the T-shirt at the shoulders and show small dark patches under the arms where the arm cut's holes are closed. Several other settings were tried (sleeve radius, blend length, no arm cut, a cut kept below the hem) and were worse. Generated content v83. Not run in Unity.

## The level camera closer in (generated content v85)

- On a phone the kid stood about a quarter of the screen tall and looked small. `CameraFollow2D` now frames 5.4 m of height at the gameplay plane instead of 7.2 m (`viewHalfHeight` 2.7, `BaseViewHalfHeight` 2.7), so the kid is about a third of the screen tall (the camera about 9 m back with the same 34 degree lens). Narrow screens still pull back to keep at least 5.5 m of street either side (`minHalfWidth`, was 7), and the focus sits 1.15 m above the kid (was 1.4) so the feet keep their place low in the frame. Aiming a kick still zooms out by 1.2. The trade-off: about a quarter less street ahead is in view. Generated content v85, so every level and the Holiday Run rebuild their cameras. Not run in Unity.

## Zoe from the user's rainbow-friends drawings (generated content v88)

- Zoe (`primaryGirl2`, id and name kept) is the Meshy model the user made from four drawings of her: black hair in a long braid, a hot-pink animal-print bomber over a grey hood and pink T-shirt, coral cargo joggers, dark clogs. The model had printed the jacket's pattern on her backpack; `meshy_teen.py --profile rainbow` repaints the backpack as in the drawings (glitter pink, a unicorn panel with chevrons, a horn and ears) and makes it ride the Bag and Chest bones only, so it no longer swings with the arms. Every action audited (`review/zoe/all_actions.jpg`, the backpack from round the back in `review/zoe/backpack.jpg`): runs, kicks, slides, tucks, landing and keepy-ups hold together; with the arms raised high (jump fall, launch, open, celebration) the jacket creases at the shoulders, as on Mia. 1.29 m, neck height 1.064. Not modelled: the rainbow straps, the gold zips. Generated content v88. Not run in Unity.

## Higher-quality kids: detail, rest pose, skinning, backpack (generated content v89)

- In the game the supplied kids' hands looked like mittens, their arms hung stiffly straight and Zoe's backpack showed as a lump at the waist. All five (Max, Kai, Leo, Mia, Zoe) are rebuilt by `meshy_teen.py`:
  - **Detail:** 100,000 triangles each instead of 30,000; fingers, faces, hair and shoe details keep their shape.
  - **Rest pose:** the arms hang relaxed about 15 degrees from the sides, forearms softly bent (`ARM_DOWN`, `FOREARM_DOWN`).
  - **Skinning:** `BuildModelCharacter` sets `SkinQuality.Bone4` on the kids' renderers. With no QualitySettings in the project, phones default to 2 bones a vertex, which would cut the models' 4-bone blends at shoulders, hips and backpacks.
  - **Zoe's backpack:** found whole now (`pack_wide`: every back-facing face inside the pack's outline, behind the body's middle, clear of the arms by `pack_arm_gap`), so all of it is repainted and rides the Bag and Chest bones; before, only its pocket and a strip were, and its sides moved with the arms.
- Checked: every action of all five at the game's camera angle (`review/hq/*_all_actions.jpg`), Zoe close up and her backpack from round the back. Max is clean in every action and Mia nearly so. Kai, Leo and Zoe are clean in runs, kicks, slides, landing and keepy-ups; with the arms raised high (jump fall, launch, open, celebration, the tucks) their sleeves still smear at the shoulders: their scans fuse the arms to the body. Max's neck height 1.533 (was 1.537). Generated content v89. Not run in Unity.

## Leo from his rigged model; the Locker Room's bags (generated content v90)

- **Leo** is rebuilt from the clean model the user supplied without a bag, which came rigged (Meshy's Mixamo-style skeleton and skin weights). The new `tools/blender/meshy_rigged.py` keeps that skeleton and those weights (merged into the game's bones) instead of guessing them from the mesh, so every action is clean, the arms-up ones too (`review/leo_bags/leo_all_actions.jpg`, `leo_arms_up.jpg`, with the bag `bag_all_actions.jpg`, `bag_straps.jpg`). 100k triangles, his relaxed rest pose like the others; neck height 1.114 (was 1.104); a new card.
- **Bags** (`Cosmetics/Bags`, `CosmeticCategory.Bag`): a fifth Locker Room tab. Bags are optional and each kid's own choice (`SaveData.bags`, by player id); the same bag can be worn by any kid who wears bags. "No Bag" and the purple Kick Off Backpack are free and owned from the start; a kid nobody has chosen for wears the backpack. In the Bags tab the showcase kid turns to show their back (`MenuStage.ShowBack`) and tries each bag on; a kid modelled with a bag of their own keeps it ("Has their own bag"). Settings > Player has a **Bag colour** row: the bag's own colours or seven others (`GameSettings.BagColour`).
- The supplied backpack is made ready by `tools/blender/meshy_bag.py prep` (30k triangles, its cloth marked in the atlas's alpha) and fitted to Leo by `fit`: sized to his back, the straps over his shoulders, down his chest and under his arms, skinned to the Bag bone (swinging 0.3 as much as a sewn-on bag: `CharacterRig.bagSwing`) and the Chest. It is a second mesh in his FBX, shown by `Presentation/BagWear` (with the pennant, which only shows with a bag on). `ToonCharacter` recolours the marked cloth to the Settings colour (`_MaskTint`, `_MaskBase`), keeping its shading; the logo, the mascot and the zips keep their colours (`review/leo_bags/bag_colours.jpg`).
- Only Leo wears the Locker Room's bags for now: Max, Kai, Mia and Zoe were modelled with their backpacks fused on. Supplied again without bags, they would go through the same `fit`. Tests: `BagsTests`. Not run in Unity.

## Kai from his rigged model, wearing the Locker Room's bags (generated content v91)

- **Kai** is rebuilt from the clean, bagless model the user supplied, which came rigged like Leo's: `meshy_rigged.py --profile plaid` (meshy_teen's plaid colour rules). Two extra bones on its shins (the jeans' cuffs) go with their parent's game bone. 100k triangles; every action clean (`review/kai_bags/kai_all_actions.jpg`); neck height 1.101 (was 1.092); a new card. He now wears the Locker Room's bags (`PlayerInfo.wearsBags`), the Kick Off Backpack by default, chosen in the Bags tab and coloured in Settings like Leo's.
- **Bag fit** (`meshy_bag.py fit`): the back's width and the torso's sides now come from the shoulder joints (1.24 and 0.74 of their span), since Kai's loose shirt is partly skinned to the arms and measured far too narrow (a small bag, straps pulled into the chest). The padded straps are narrowed to 70 % where they leave the bag, for both kids: at their modelled width they read as a vest on a child (`review/kai_bags/straps.jpg`). Leo is refitted.
- Not run in Unity.

## The Race Car Backpack (generated content v92)

- A second Locker Room bag from the supplied model: a red race-car backpack with a car's face, headlights, a grille and wheels (`Bag_RaceCar`, `bag_racecar`), free and owned from the start like the Kick Off one (`Bags.Starter`). Leo and Kai can each wear it, the Kick Off one, or none; Settings' colour recolours its red body and keeps the face, windows, lights, wheels and brown back panel (`review/race_car_bag/`).
- `meshy_bag.py prep --hue lo,hi --sat s`: each bag's cloth colour (red wraps through 0); the straps' side is found by the gap between the straps (the car's lights stand out further at the front); `fit` keeps a kid's other bags. `review_poses.py --bag` shows one. The Settings swatch for the bags' own colours shows the bag the chosen kid wears.
- Not run in Unity.

## Zoe from her rigged model, wearing the Locker Room's bags (generated content v93)

- **Zoe** is rebuilt from the clean, bagless rigged model the user supplied (`meshy_rigged.py --profile rainbow`: meshy_teen's colour rules for her, without its search for a backpack by shape). 100k triangles; every action clean (`review/zoe_bags/zoe_all_actions.jpg`); neck height 1.099 (was 1.064); a new card. She now wears the Locker Room's bags like Leo and Kai: the Kick Off and the Race Car backpacks are both fitted to her (`review/zoe_bags/race_car.jpg`).
- The re-uploaded rigged model was identical to the first; the still and untextured ones were not needed. Not run in Unity.

## The Sparkle Unicorn Backpack (generated content v94)

- A third Locker Room bag from the supplied model: pink glitter with a unicorn's horn and ears, rainbow chevrons and gold zips (`Bag_Unicorn`, `bag_unicorn`), free and owned from the start. Fitted to Leo, Kai and Zoe; Settings' colour recolours its pink cloth and keeps the horn, ears, chevrons and zips (`review/unicorn_bag/`).
- `meshy_bag.py prep`: a carry handle standing over the back panel no longer counts as the bag's top (the top is capped at the last level where the bag is half its width); the Kick Off and Race Car bags measure as before.
- Not run in Unity.

## Mia from her rigged model; every primary kid wears the Locker Room's bags (generated content v95)

- **Mia** is rebuilt from the clean, bagless rigged model the user supplied (`meshy_rigged.py --profile explorer`), checked against the user's four reference drawings: leopard-print headband, white "Kick Off" T-shirt with a red stripe, red shorts with white piping, white "Kick Off" socks, pink sneakers. 100k triangles (over half of them her hair, all above the neck); every action clean (`review/mia_bags/mia_all_actions.jpg`); neck height 1.050 (was 1.028); a new card. All three bags are fitted to her (`review/mia_bags/bags.jpg`).
- Kai, Mia, Leo and Zoe now all wear the Locker Room's bags; the three teens keep the bags they were modelled with. Not run in Unity.

## The Denim Bow Backpack (generated content v96)

- A fourth Locker Room bag from the supplied model: light denim with a big denim bow and tan straps (`Bag_DenimBow`, `bag_denimbow`), free and owned from the start, fitted to all four primary-school kids. Settings' colour recolours the denim and bow and keeps the tan straps (`review/denim_bow_bag/`).
- `meshy_bag.py prep`: straps looping up above a bag no longer count as its body (the top is capped at the last level reaching a third of the way to its front); the other three bags measure exactly as before.
- Not run in Unity.

## The Race Car Backpack a third bigger (generated content v97)

- It looked small on the kids: it was sized by its widest point, and its wheels and side mirrors stand out a quarter beyond its body. `meshy_bag.py prep --size-by panel` sizes it by its back panel's width instead (0.895 against 1.186 at its widest), so on the kids it is now about the Kick Off backpack's size (`review/race_car_bag/bigger.jpg`). Refitted to all four primary kids; the other bags are unchanged. Not run in Unity.

## Hana from her rigged model, wearing the Locker Room's bags (generated content v98)

- **Hana**, the high-school girl, is rebuilt from the clean, bagless rigged model the user supplied (`meshy_rigged.py --profile varsity`), checked against the reference drawings: long wavy dark-brown hair, freckles and hoop earrings, a maroon varsity jacket with an "H", cream sleeves and striped cuffs over a cream hoodie, charcoal cargo jeans, cream platform sneakers. 100k triangles; every action clean (`review/hana_bags/hana_all_actions.jpg`); neck height 1.446 (was 1.43); a new card. She replaces the earlier scripted Hana (white blouse, navy skirt, tie, yellow backpack).
- She wears the Locker Room's bags; all four are fitted to her, resting on her long hair (`meshy_bag.py fit` now measures the back with only the arms left out; the other kids' fits are unchanged) (`review/hana_bags/bags.jpg`). Not run in Unity.

## Max from his rigged model, wearing the Locker Room's bags (generated content v99)

- **Max** is rebuilt from the clean, bagless rigged model the user supplied (`meshy_rigged.py --profile denim`), checked against the reference drawings: spiky ginger hair and freckles, a light denim jacket over a grey hoodie and a white T-shirt, charcoal jeans, white sneakers with black stripes. 100k triangles; every action clean (`review/max_bags/max_all_actions.jpg`); neck height 1.547 (was 1.533); a new card. All four bags are fitted to him (`review/max_bags/bags.jpg`).
- Every kid but Ren now wears the Locker Room's bags; Ren keeps the satchel he was modelled with. Not run in Unity.

## The Golden Trail Backpack (generated content v100)

- A fifth Locker Room bag from the supplied model: a classic tan canvas backpack with silver zips and dark mesh side pockets (`Bag_GoldenTrail`, `bag_goldentrail`), free and owned from the start, fitted to all six kids who wear bags (Hana, Max, Kai, Mia, Leo, Zoe). Settings' colour recolours the canvas and keeps the zips and mesh (`review/golden_trail_bag/`). Not run in Unity.

## Ren removed (generated content v101)

- Ren, the high-school boy (`boy`, `Art/Models/Boy.fbx`), is gone from the game: out of `PlayerRoster`, the player picker, the string tables and the screenshot tour, with his card (`Resources/UI/PlayerBoy.png`), his model and atlas, his satchel (`Presentation/SatchelShape`, `LevelBuildKit.Satchel`) and his own bicycle (`Bicycle.fbx`, `LevelBuildKit.OwnBicycle`, `ArtBaker` bicycle material; the home garden has the street kit's bicycle instead).
- **Hana is now the default player.** Saved choices keep working: a save that picked Ren now plays Hana (`PlayerRoster.Normalize`), and his bag choice is ignored. Six kids remain (Hana and Max; Kai, Mia, Leo and Zoe), and all of them wear the Locker Room's bags.
- Tests: `PlayerRosterTests` (two teens, Hana the default, "boy" falls back to her), `BagsTests` (every kid wears bags). Not run in Unity.

## The game's logo as the app icon

- The app icon is now the logo artwork the user supplied (`marketing/source/icon_artwork.png`, 1254 px): a boy with a backpack kicking a ball along the footpath on the way to school, past stones, a bottle and a can, the school ahead, under the "Kick OFF 2" logo. `tools/app_icon_from_image.py` (new) trims its 3-4 px black border and writes the App Store icon (`marketing/appstore/icon_1024.png`), the Google Play icon (`marketing/googleplay/icon_512.png`), the in-game icon every build applies (`Assets/_Game/Art/Icon/AppIcon.png`, `BuildScripts.ApplyIcon`) and Android's adaptive layers (the whole picture inside the launcher's safe area). Checked in iOS's and Android's masks from 300 to 40 px (`review/app_icon/sizes.png`): the logo and the kick read down to 80 px. Earlier icon renders (`tools/blender/app_icon*.py`) are kept but not used.

## The banner as Google Play's feature graphic

- Google Play's feature graphic (`marketing/googleplay/feature_graphic_1024x500.png`, required to publish) showed Ren and the old Hana. It is now the banner artwork the user supplied (`marketing/source/banner_artwork.png`, 1774 x 887: the boy kicking the ball along the footpath on the way to school, the school ahead, the "Kick OFF 2" logo). It is drawn 2 : 1, so `tools/feature_graphic_from_image.py` (new) scales it to 1024 x 512 and trims 6 px off the top and bottom. (Wider art would be kept whole over an out-of-focus enlargement of itself.) The App Store has no banner, so nothing changes there.

## The title screen's logo matches the icon and the banner

- The "Kick OFF 2" logo on the title screen, the launch splash and the credits was drawn in code (Lilita One lettering on a turf badge). It is now the lettering of the app icon and the store banner, cut out of the banner artwork (`marketing/source/banner_artwork.png`) by `tools/logo_from_banner.py` (new: everything the logo's navy outline closes in, plus the swoosh's yellow tail; the one connected piece kept) into `Resources/UI/KickOffLogo.png` (814 x 304, transparent). `UI/KickOffLogo` shows it at the same size and place, breathing gently, over the tagline ribbon (none in the credits); it falls back to the drawn logo if the picture is missing. Not run in Unity.

## Spacing and overlaps in the menus

- `UIKit.Place` pins a rect by its anchor unless given a pivot, so a button anchored to a card's bottom edge at y 90 spans 90 up to 196, not 37 to 143. Credits put the version line at 180 to 220 and Done at 90 to 196: the version hid behind Done. And the new logo picture still took the old round badge's 680 x 560 box, leaving a wide gap under it.
- Fixed: `UI/KickOffLogo`'s box is now exactly the lettering and the ribbon (title screen, splash, credits sit where they look). Credits are laid out top down by explicit edges: the logo under the header, the text, the version, Done. Looked for the same trap across the menus: the level results (the coins and sticker line overlapped the buttons' tops; moved up), the challenge guide (the goal, stars and time rows overlapped by 5 to 10 px; respaced), the unlock panel (the status line was under Buy; moved above it), the sticker reward cards (the picture sat low, over the name; centred as meant), the pause menu (eight buttons in a development build ran off the card; closer together). The rest (the HUD's aim bar, the pause stacks, the player picker, the school reward cards) were checked and are fine. Not run in Unity (`review/logo/credits_mock.png` is the credits laid out from the new numbers).

## Astradite in the app and the stores

- The credits now say "A game by Astradite" under the logo (`credits.by`, en and es) and end with "© 2026 Astradite Private Limited" under the version (`KickOffLogo.Studio`, `Company`, `Copyright`); laid out like the rest of the credits, top down by explicit edges.
- The legal entity, Astradite Private Limited, is named where it counts: the App Store copyright, the privacy policy (`docs/PRIVACY_POLICY.md`, `site/privacy.html`) and the website's footers. `docs/RELEASE.md` says to open both developer accounts as organisations in the company's name (the stores then show it as the seller; Play's 12-tester closed test is waived; both want a D-U-N-S number). Unity's company name stays "Astradite": on desktop it is part of the save folder.

## Long content on small screens

- The canvas is matched on height (1920x1080 reference), so every phone gets the same 1080 units of height; a small phone loses only its safe area, and labels shrink by best fit. Scrolling is only needed where a list can grow.
- **Add-Ons** (`UI/AddOnsPanel.cs`): the list is a clamped vertical scroll area that only scrolls when its content is taller than the card (710 of 724 units today, so it stays still; new add-ons or filters will scroll).
- **Level results** (`UI/GameHud.cs`): the most lines plus the note (1041 units) could pass the 1000-unit card, so the line spacing squeezes down to 80% when it has to (`resultsSqueeze`) instead of scrolling a results card.
- Unchanged, because they already scroll (Album, Shop) or hold a fixed amount that fits (Settings, the kid picker, the challenge guide's three tips, the Holiday Run's three missions).

## Co-op over Bluetooth: race friends to school (up to four phones)

- **A third mode** (title screen: CO-OP beside HOLIDAY RUN, under PLAY): up to four phones in the same room, iPhones and Android phones together, race the whole way from home to school over Bluetooth LE. Design, rules, protocol, native bridge and a device checklist: [`docs/COOP.md`](docs/COOP.md).
- **Players.** A name typed for the others (empty: "Player 1, 2, 3..." by seat) and a four-character tag from a random install id (`#K7QX`), shown after the name everywhere so two players with the same name are told apart (the host keeps tags unique; names can't contain `#`). The kid from the player picker is the kid the others see.
- **Lobby.** HOST A RACE / JOIN A RACE (lobbies nearby, nearest first, with their host, count, phase and signal). Four seats with ready and connection state. **Any player** chooses the stage (one of the six routes, or Random) and the location (the add-ons, or Random), as in a fighting game's stage select: the last choice the host gets wins, the lobby shows who chose, readies reset. A location unlocked on one phone plays for all once it is picked. Filters stay each phone's own (Add-ons & Filters). All ready (two or more): a 3-second countdown, a loading barrier (at most 15 s), then 3-2-1-GO at the same instant on every phone (NTP-style clock sync over the pings).
- **Race.** Each phone runs its own kid through the route's legs (each leg loads at once after the last); the others are ghosts (a stripped copy of the level's model of their kid, posed from their motion 160 ms in the past, in lanes just behind; colour ring; name tags, at the screen's edge with the distance when out of view). Standings under the pause button with a bar for each player's progress. No bell, no pace, nothing saved as story progress; the race clock runs through pauses. First through the school gate wins; the others carry on; finishers keep their time and place even after leaving. Coins collected plus a place bonus; `coopRaces` and `coopWins` in the save.
- **Resilience** (`Coop/Session/CoopSession`): every phone keeps playing through a dropout; a racer out of touch for 20 s is listed last, and back in the race (racing, or finished with the real time) if they return before the next race; leaving is final and listed last too; the host's loss starts a migration (look for it 4 s, then the next seat takes over with a higher epoch; finishes survive on every phone and are relayed to a new host); two hosts of one session after a split: the one with more players keeps the race (then the lower epoch, then the lower seat), and the runs are merged; a host in the background or with Bluetooth off for 3 s steps down; a frozen host is given up on; scene loads announce a short silence; a phone's own stall isn't held against the others; the race clock counts a phone's sleep and corrects a guessed or jumped start; lobby seats held 10 s; the host can remove a player; the screen kept on in a session.

**Release audit (after the first version).** A full pass for correctness, robustness, efficiency and store readiness: the session split into host and client files; a randomized "chaos" sweep (2,000 storms of radio loss, range splits, freezes and leaves, checking one host, identical standings, no lost finish and fair treatment of steady phones) found and fixed split-brain hosts, stale verdicts and a zombie host; fuzzing of every message; the iOS beacon packed into the 8 characters iOS can advertise; framing that can't misread a cut message; late native events filtered by generation; both plugins rewritten around per-player queues that drop only whole messages; the leg loads made asynchronous; coins banked at the gate and the place bonus once the result is final; a word filter for names; a content fingerprint so two different builds never race. See `docs/COOP.md` "What has been checked".
- **Code.** `Coop/Net` and `Coop/Session` are pure C# (no Unity); `Coop/Transport` wraps the native plugins `Plugins/iOS/DTSCoopBLE.mm` (CoreBluetooth) and `Plugins/Android/DtsCoopBle.java` (android.bluetooth.le), which pack the same events. The level sees a race through `Core/ILevelRace` (`LevelManager.Race`): `LevelManager` skips the bell, the pace and saving, holds the first leg's intro for GO and hands the goal to the race; `GameHud` shows the race clock and countdown, a race pause menu (Leave race), and no tour or results card. `FrontEndScreen` gained `Tick` and `HandleBack`; `AddOns.SceneFor(scene, addOn)`. Build: `Editor/IosPostBuild` adds NSBluetoothAlwaysUsageDescription, CoreBluetooth and ARC for the plugin; `Editor/AndroidBluetoothPermissions` adds the Bluetooth permissions (nearby devices on 12+, location up to 11) and `bluetooth_le` not required. The privacy policy, the store listings and `docs/RELEASE.md` say what Co-op shares with nearby phones.
- **Editor.** No Bluetooth: practice bots (real sessions on an in-memory radio) join or host, ready up and run the legs; the race HUD has editor-only buttons to send a bot out of range, bring it back, make the bot host leave, and switch your own pretend Bluetooth off.

**Not run in Unity or on a device.** Checked offline: the four compile configurations (iOS and Android players, runtime with editor defines, editor assembly and edit-mode tests) against the Unity 2021.3 reference assemblies; `Tests/Editor/CoopSessionTests.cs` (38 tests: whole lobbies and races on the in-memory radio, plus the wire format, framing, beacons, the native event decoder, names, tags, standings, the split rule, clock sync and ghost interpolation) under Mono with a work-alike NUnit, all passing, and 8 of them failing on a copy with two rules deliberately broken; the Android plugin compiled with `javac` against Android 14's framework classes (no warnings in it); string parity (711 keys in each language). The iOS plugin was not compiled (no Apple SDK here). The device checklist is in `docs/COOP.md`.

## The classic cartoon filter (generated content v102)

- **A fourth filter in Add-ons & Filters: Classic cartoon** (`AddOns.ClassicFilter`, saved as `SaveData.filter`; strings `filter.classic` and `.about`, en and es: "Classic cartoon", "Inked characters, painted scenery" / "Dibujos clásicos", "Personajes entintados, fondos pintados"). It fills the panel's empty fourth filter slot, so the panel keeps its size. Applies at once, in every scene (every level, the challenges, the Holiday Run, co-op races, the menu's live street and the Locker Room), like the other filters. Matched to the classic Road Runner shorts the review sent, through four rounds of artwork (`review/cartoon/`: the boards, the Blender renders of the game's own models and camera, and `classic_port.py`, the reference).
- **The look** (`Shaders/PostFX.shader` passes 7 to 9, `Shaders/DtsCartoon.cginc`; the values in `World/ClassicLook.cs`): an animation cel over a painted background. Pass 7 grades the picture (in display values) keeping the code in alpha; pass 8 is a cored soft Kuwahara (four 3x3 sectors, 25 reads; of what it takes away, weak texture stays away and strong detail comes back, so frames, shop names and spokes stay crisp), then the cels' colour (saturated, three soft tones) or the painted scenery's (reds, oranges, yellows and beiges pushed to orange and gold, blues and greens kept, quiet colours lifted, warm shadows), the clouds white and the sky a flat turquoise; pass 9 sharpens the scenery a little, adds faint brush streaks (across the ground, down the walls), darker strokes of the scenery's own colour where colours meet and where a nearer form overlaps a farther one, and the cels' warm-black outline, drawn only on the far side of their edges (outside a figure, or on a farther part behind a nearer one), so it never covers a face; then a faint grain and vignette. `ClassicLook.Calmer` switches everything (camera and menus) to the calmer setting the review also saw (gentler saturation, less orange, softer warm shadows, a paler sky). `PostFX.forceClassic` shows it in the editor.
- **What each pixel is** rides in the picture's alpha: 0 a person or the ball (ToonCharacter, as before), 0.125 a cel (the cars: `_ComicWorld` 0.125, was 1; the Animals kit, i.e. the animals and the coins, stars and stickers; the pushable crates; `LevelBuildKit.celModels`: swing seats, targets, slalom and checkpoint flags, each wearing its kit's new `Kit<kit>Cel` material), 0.5 foliage (the plants kit), 0.75 a cloud, 1 the scenery (`Toon.shader`'s new `_FilterMask`, set by `ArtBaker`). The comic and sketch filters read alpha x 8, so they see what they always saw.
- **The menus' pictures** (`UI/CartoonPicture`, `Resources/Shaders/CartoonPicture`, the same colour code): the kids' cards (title screen, picker, co-op), every Locker Room item's picture (shop, rewards, album), the stickers, the bag in Settings and the logo as cels (the stickers, cards and items outlined outside their shape; the logo keeps its own outline), the town map painted. They follow the filter at once (`AddOns.FilterChanged`). **Buttons** (`UI/Kit/CartoonButton`, every `UIKit.Button`): an ink rim round the key and a hard ink shadow while the filter is on. Text is never filtered; the comic words don't pop with this filter.
- **Cost:** three full-screen passes (the grade, about 27 reads, about 45 reads) instead of one, plus the depth and normals pass the other filters already ask for, only while the filter is on. If older phones struggle, pass 8 can run at half resolution.
- **Checked:** the runtime scripts compiled with Roslyn against the Unity 2021.3 engine modules and uGUI 6000.0 (built from source here; Unity 6's Rigidbody2D renames mapped back); the edited editor scripts parsed with no errors on the changed lines (no UnityEditor assembly here); every PostFX pass (0 to 9) and the picture shader compiled by glslang's HLSL front-end, in gamma and linear colour space, flipped UVs and the UI's clip keywords (it caught two bugs: a missing shared uniform and `line`, a reserved word); a numpy mirror of passes 8 and 9 in the shader's own order (`review/cartoon/shader_mirror.py`) against the approved boards: mean difference 0.004 to 0.007. **Not run in Unity:** look at the filter on a device (and its frame time), the materials after the rebuild (v102), the town map and stickers with the UI material (masks and scroll views), and the buttons' rim.

## Holding the ball like a real dribbler

- **The stick sets the pace** (`Input/GameInput`: `StickPace`, `stickMinPace` 0.3, `stickFullSpeedAt` 0.7): how far the knob is pushed, not just which way: a third of a run just past the dead zone, rising evenly to full speed at 70% of the ring. The keys and the tour's scripted walk always run. The run cycle already follows the speed, so a jog looks like one.
- **The touch follows the pace** (`Ball/BallController.TouchLead`, `BallTuning.walkLeadFraction` 0.1, `walkTouchLift` 0.3): every touch used to send the ball 1.6 m/s faster than the kid, at any pace, so it always ran away. Now a touch at a walk adds a tenth of that (and a lower hop); flat out, the whole of it, as before. A 1D simulation with the game's tuning: at a jog the ball stays 0.27 to 0.56 m ahead (0.43 on average); flat out about 0.3 to 0.9 m, as before (the full-pace touch is unchanged).
- **A foot on the ball** (`BallController.HoldBall`, `IsHeldUnderFoot`; `BallTuning.soleHoldOffset`, `dragBackSpeed`): letting go of the stick with the ball at the feet, the kid holds it under the sole (it used to be slowed once and roll on). It rides along on moving ground. Pushing on carries on dribbling with a small touch; pushing the other way is a drag-back: the ball rolls back under the kid at 2.4 m/s as they turn and comes out in front (simulated: never more than 4 cm behind the feet). The kid stands with the near foot lifted onto it (`KidController.FootOnBall`, `KidAnimator`).
- **Hold KICK for close control** (`GameInput.BallControlHeld`, `ReadKick`, `ReleaseKick`, `kickHoldTime` 0.22 s; `L` / `Left Shift` on a keyboard): a tap still kicks (the quick pass), a drag still aims; a still press past 0.22 s keeps the ball at the feet instead, and letting go after it kicks nothing (a thumb that wanders while holding never starts an aim, so no slow motion mid-dribble). While held the ball is kept 0.25 to 0.45 m ahead (nearer at a walk), with a little touch every stride (the leg swings, the touch sound plays), the kid at 70% speed (`KidController.ControlPace`; not in the Holiday Run's auto-run, whose stages are laid out for its pace); turning, the ball comes round the feet; standing still, a foot goes on it. The ball stays a physics ball (a hold steers its speed, never its position) and nothing holds it for 0.35 s after a kick, so a dog's steal (a kick) still takes it.
- **Help text** (`tour.walk`, `tour.kick`, `controls.walk`, `controls.kick`, en and es) and the README's controls. The Tune panel has a CLOSE CONTROL section (the stick's pace, the hold time, the walk touch, the drag-back, the hold's speed, lead and grip) for tuning on a phone. `trapDamping` is gone (the foot hold replaces the old one-off trap).
- **Checked:** the runtime scripts compile (Roslyn, Unity 2021.3 modules, uGUI 6000.0); `Tests/Editor/DribbleControlTests` (7 tests: the stick's pace, the kick button's tap, hold and aim, the touch's lead) all pass against the functions' own source with a work-alike `Mathf` (Unity's needs the engine), and fail when those rules are deliberately broken; the 1D simulation above. **Not run in Unity or on a phone:** how the pace feels under the thumb, the hold time against real taps, the foot-on-ball stance, and the close-control touches' rhythm.

## Stairs up to the pier (generated content v103)

- The California beach's pier had no way up: its deck stands 4.5 m over the sand. It now has a landing at deck height
  in front of its first span and a flight of stairs down to the sand on the left and the right, each with a
  mid-landing halfway (`World/PierStairs.cs`, one mesh): timber treads on white cut stringers with white risers, the
  pier's white rails on both sides, concrete piles under the landings, a pad at each foot, a globe lamp on each of the
  landing's front corners, and a boardwalk path on the sand from each foot toward the lane.
- `StreetBuilder.Coast` `Pier` measures the sand at each flight's foot and sizes the flight to it (risers of about 0.19 m,
  treads 0.27 m; a mid-landing when the drop is more than about 2.7 m). The pier is now placed before the lifeguard
  towers, and the towers, palms and parasols keep clear of the stairs and their paths.
- The pictures it was designed from: `review/pier_stairs/` (`render_pier.py`, with the stairs ported to
  `pier_stairs.py`). Tests: `Tests/Editor/PierStairsTests.cs`.
- **Checked:** the runtime scripts compile (Roslyn, Unity 2021.3 modules, uGUI 6000.0); the editor scripts bind with
  UnityEditor's declarations stubbed, with no errors in the edited files; `PierStairsTests` (4 tests: comfortable,
  even risers that add up to the drop, a mid-landing halfway on a long flight, the reach the builder keeps clear) pass
  against the plan's own source and fail when its rules are broken. **Not run in Unity:** the stairs in the rebuilt
  California beach levels (v103), and how they sit on the sand where it is not flat.

## Up and over the pier in Low Tide (generated content v104)

- **In California, Low Tide's course now climbs the pier** (`GreyboxLevels.LowTide`, `TrackBuilder.CanClimbPier`): its
  stairs stand across the lane at 48.6 to 62.5, where the original level has the sandcastle wall and a short tide. The
  kid dribbles the ball up one flight onto the landing in front of the pier's deck, over it, and down the other flight;
  the camera follows them up and back down (CameraFollow2D already tracks height past its dead zone). The same five
  coins (two on the way up, one on top, two on the way down) and the sticker, now high over the landing (a double jump
  from the top). The original Low Tide, and the other beach levels' piers (stairs behind the lane), are as they were.
- **The climb** (`Editor/LevelBuildKit.Pier.cs`, `TrackBuilder.PierClimb`): one collider up the steps' nosings, across
  the landing and down (what a foot or a ball rides over, with no seams to catch on), recorded for the feasibility check
  as two ramps and a ledge. The deck stands 2.3 m over the lane (the pier's piles go deeper into the sand there), and
  the flights are gentler than the pier's other stairs: risers of 13.5 cm on 35 cm treads, about 21 degrees, no steeper
  than the dunes. `StreetBuilder.Coast` `PierOnCourse` builds the pier with its near end just behind the lane and the
  stairs across it (`World/PierStairs`, `onCourse`: a 2 m landing, the deck's edge railed either side of it, rails on
  both sides of each flight, the camera's side running unbroken from one foot, up, across the landing's front and down
  to the other, and the back of the landing left open onto the pier; no lamps).
- **The kid keeps to slopes** (`Player/KidController`: `GroundNormal`, `IsWalkableSlope`, `AlongSlope`, `SlopeRise`):
  on the ground, on a slope up to about 45 degrees, not jumping, and not on something moving, the kid goes along the
  slope at the stick's pace and gravity no longer pulls them down it. The body is frictionless (so it never sticks to a
  wall), and on anything steeper than about 18 degrees gravity used to win: a kid who stopped on a steep ramp slid back
  down and could not start up again until the bottom. This applies to every ramp and dune in the game, not only the
  pier: standing on a slope the kid now stays put, and runs up and down slopes at an even pace. A Box2D simulation of the
  game's run and dribble (the kid's tuning, frictionless capsule, gravity x3 and x1.4 falling; the ball's touches) over
  the climb: before, running straight through worked (3.97 of 4.2 m/s on the way up at 21 degrees) but a kid stopped
  halfway up slid back down to the foot of the steps; after, the stick's full pace up and down, and a standing start on the steps
  goes up.
- **Checked:** the runtime scripts compile (Roslyn, Unity 2021.3 modules, uGUI 6000.0); the editor scripts bind with
  UnityEditor's declarations stubbed, with no errors in the edited files; `Tests/Editor/PierClimbTests` (3 tests: the
  flights are 18 to 22 degrees with no mid-landing and add up to the climb, the climb passes the feasibility check and
  the deck alone does not, the kid's slope rules) and `PierStairsTests` pass against the rules' own source and the real
  `LevelFeasibility`, and fail when the steps are made steeper or the kid's slope rule is taken out. The pictures:
  `review/pier_stairs/course_board.jpg` (`render_pier.py ... course`). **Not run in Unity or on a phone:** the climb's
  feel with the ball (a ball let go on the steps rolls back down them, and one knocked on at the top runs away down the
  far flight, as on real steps), the kid's feet on the steps, and the slope rule on the other levels' ramps and dunes.

## Two piers along the seaside walk (generated content v105)

- The California beach had a pier on every leg (Boardwalk, Low Tide, Seagull Bay, Sandcastle Sprint and the Beach
  Slalom challenge), which felt repetitive. A pier is now something a level asks for: `TrackBuilder.SeasidePier()` (a
  pier behind the lane, placed by `StreetBuilder.Beach` clear of the stops, with its stairs down to the sand) or
  `PierClimb` (a pier the course climbs). Two along the whole walk: Low Tide's, which the course climbs, and Sandcastle
  Sprint's, behind the lane near the walk's end. Boardwalk, Seagull Bay and the Beach Slalom have none. The original
  (non-California) levels never had piers and are unchanged.

## Fewer repeats across the levels (generated content v106)

An audit of what comes round again and again (`review/repetition/README.md`), and the fixes:

- **Each level its own scenery.** Every story level starts its street at the same x and many end at the same x, and the
  scenery's seeds were made of the chapter and those ends only: the background (tree bands, back rows), the near trees'
  shade, the birds, the poles and lamps were the same in every level of a chapter, and Fountain Square and Playground
  (both 110 m) had the same street. Each level now salts its seeds with its own name (`StreetBuilder.LevelSalt`, FNV-1a,
  the same on every machine), starts its pole line at its own place, and sees its own stretch of the distant hills.
  Holiday Run stages keep their own seeds (their seams still meet).
- **Things to slide under:** three new models in the Barriers kit (`tools/blender/kit_barriers_models.py`): a
  **washing line** (the home street), a **market barrow** on cartwheels (the market) and a **wobble bridge** (the park),
  and seven slide-unders re-chosen so no look comes round more than three times in a chapter (most twice): Puddle Lane,
  Corner Shop, Fruit Stalls, Low Tide, Sandcastle Sprint, Duck Pond and The Final Bell. The Holiday Run's chapters get
  the new looks too. Each comes in a few colours.
- **Obstacles to jump:** every knee-high wall on the home street and in the market was the same planter, every tall one
  drinks crates or (in the park) a hedge, every low step a grey stone. Now each chapter has a few looks, picked by the
  obstacle's place and the level (`TrackBuilder.ObstacleModel`): the wheelie bins out on bin day, a flower bed or the
  stone step (home street); fruit crates stacked three or five high, pallets (market); an old block wall among the
  hedges (park); pallets or the stone step (building site). The colliders are exactly as they were.
- **Boxes to knock over:** a taped **moving box** on the home street and a **plastic crate** on the building site (new in
  the Street kit), the wooden crate elsewhere; all three are cels for the classic cartoon filter.
- **The beach:** a lifeguard tower every 55 to 80 m (was 30 to 45), each painted its own way (four roof colours, three
  bodies) and set a little back or forward; rocks at the water's edge are a cluster, a big lone rock or a pair of
  boulders (the large boulders were unused); palms in four greens.
- **The market's back row** was blocks of flats only: now and then a tall shop with rooms over it, or a long terrace.
- **Not changed (needs art):** every adult in the game is the same body, recoloured. `review/repetition/PEOPLE_PROMPTS.md`
  has image prompts for six new passers-by (for an image-to-3D tool, then `tools/blender/meshy_rigged.py`).
- **Checked:** the runtime scripts compile; the editor scripts bind with UnityEditor stubbed, with no new errors; the
  Barriers and Street kits rebuild from their scripts (the Street atlas is unchanged, so its other models are untouched).
  **Not run in Unity:** the rebuilt levels (v106).

## The jogger: the first of the new passers-by (generated content v107)

- **A second body for the grown-ups:** the jogger (a woman in a running jacket, leggings and trainers), made by the
  user with an image-to-3D tool, rigged on its Mixamo skeleton, brought in with `tools/blender/meshy_rigged.py
  --profile jogger --tris 30000` (`Art/Models/Jogger.fbx`, `.json`, `JoggerAtlas.png`; 30k triangles, as several walk
  by at once). Her parts: 1 the jacket (its collar too), 2 the leggings (and the waistband under the hem), 3 the
  ponytail and the hair at the front (two pieces of the scan); the skin, the trainers and the watch stay as made.
- **Who walks by** (`TrackBuilder.Walker`): about one passer-by in three is the jogger, chosen by the walker and the
  level (`LevelBuildKit.PasserbyModels`; `ArtBaker` makes a material for each). Her clothes are chosen the same way,
  so she is dressed differently from level to level: one of ten sporty jackets (`JoggerTops`), dark leggings
  (`JoggerLeggings`) and natural dark hair (`JoggerHair`); and as every passer-by changes coat each time they come
  round again (`Pedestrian.Redress`), she changes into another of her jackets. Builders stay in hi-vis on the adult.
- **Checked:** the runtime scripts compile; the editor scripts bind with no new errors; the parts and four of her
  outfits rendered in the game's look (`review/passersby/walkers.jpg`, `render_walkers.py`). **Not run in Unity.**

## Five more passers-by: Mom, the office worker, the courier, the shopkeeper, Grandad (generated content v108)

- **The rest of the cast:** the user's five rigged models for the prompts in `review/repetition/PEOPLE_PROMPTS.md`,
  each brought in with `tools/blender/meshy_rigged.py --profile <mom|office|courier|shopkeeper|grandad> --tris 30000`
  (`Art/Models/Mom`, `OfficeWorker`, `Courier`, `Shopkeeper`, `Grandad`: `.fbx`, `.json`, `Atlas.png`). Their profiles
  share one setup (`Faces`) and say only which colours are which part: 1 the top (Mom's coral jumper, the navy blazer,
  the red polo, the lilac tunic, the mustard cardigan), 2 the legwear (wide-leg trousers, suit trousers, cargo shorts,
  trousers, cords; the long trousers' hems too, which sit on the feet's bones), 3 the hair, or what is worn on the
  head instead (Mom's bun, the office worker's hair and beard, the courier's cap, the hijab, Grandad's flat cap). The
  skin, the shirts under the tops, the shoes, belts and socks stay as made.
- **Who walks by** (`TrackBuilder.Walker`, `NextPasserby`): the six rigged passers-by and the procedural adult take
  turns, in an order and from a start of the level's own, so each comes along once before any comes again (builders
  stay the adult in hi-vis). Each has its own wardrobe (`LevelBuildKit.Passersby`, which the jogger's colours moved
  into): its top, legwear and hair, cap or hijab are chosen by the walker and the level, so the same people are
  dressed differently from level to level.
- **Changes of clothes** (`Pedestrian.Redress`): a passer-by coming round again changes into another top from its
  wardrobe and, now, legwear from it too (`Pedestrian.legwears`), not the top's colour darkened (the courier was due
  dark-red shorts); with the same one random draw as before, so a walk goes on the same. The adult darkens as before.
- **Checked:** the runtime scripts compile; the editor scripts bind with no new errors; `PasserbyTests` (every
  wardrobe whole; the turn order brings each along once before any again, for any number of bodies) pass, and fail
  without the step kept prime; each model's parts rendered front and back (flat colours, recoloured); all six in four
  levels' outfits in the game's look
  (`review/passersby/walkers.jpg`, `render_walkers.py`, which reads the wardrobes from the code). **Not run in Unity.**
- **Whole faces, and the office worker's beard (generated content v109):** the scratch lines across the passers-by's
  faces were cracks: the scans come with their vertices split wherever the texture is cut (every texture piece a
  loose patch), and cutting them to 30k triangles moved each patch's border on its own (the office worker went from 44
  open edges to 30,262). `meshy_rigged.py` now welds the patches first (`weld`: closed again, the texture's seams kept in
  the corners' UVs), cuts the triangles holding back the vertices on the texture's colour lines
  (`decimate_keeping_edges`, so a beard's or a hem's edge keeps small faces and a face rarely straddles it), and paints
  the part map with the uncoloured faces last (`meshy_boy.paint(plain_last=True)`: no white flecks beside a dark
  part). The hair part leaves out the eyes (dark pieces ringed by their whites) and now takes the brows; the office
  worker's hair, beard, moustache and brows are one part, so his wardrobe has light hair too (dark blond, blond,
  auburn, grey, silver). All six passers-by rebuilt, the jogger with them (her rules on the shared setup).
  `review/passersby/faces.jpg`: the faces before and after, and the office worker in four hair colours.

## Every grown-up a rigged passer-by, at a grown-up's height; a smoother dribble (generated content v110)

- **No more procedural adult** (the white-headed mannequin): the six rigged passers-by take turns on the footpath on
  their own (`NextPasserby`, a full cycle of the six); a walker's friend is another of them in their own wardrobe (and
  changes from it: `Pedestrian.companionCoats`, `companionLegwears`); the builders on the footpath and the banksman are
  the courier in hi-vis with his cap in a hard hat's yellow; the parent at the kid's front door is Mom; at the stops,
  Granny is the shopkeeper's model, the lifeguard the courier, Grandpa at the allotment Grandad, the one waiting at
  the bus stop the office worker, the traveller at the station Mom (`Person` takes the model's name). The procedural
  adult is left only as the fallback should a model be missing from a build (`GrownUpLook`).
- **Heights** (`Passerby.neck`, game units): the jogger, the office worker, the courier and Grandad stand as tall as
  the old adult (`AdultNeck`, 1.22 times the kid's 1.3); Mom and the shopkeeper stay as they were (1.393, 1.37).
- **The dribble** (`KidAnimator`): the recording showed the kid at a gentle push (about a fifth of a run, KICK held)
  with her legs barely cycling and her planted foot skating, and every dribbling touch (a close-control touch each
  0.41 s) playing the whole kick: the thigh wound back and whipped through, fighting the stride and holding a wide
  pose. Now the steps quicken with the pace (`StrideRate`: a run's cadence times the square root of the pace) and each
  is as long as the ground covered while the foot is down (`StrideSwing`), so the planted foot stays put (at a fifth of
  a run it slid 0.79 units/s, 1.48 with the touches; now about 0.3); standing blends in as the steps die away; and a
  dribbling touch is the swinging foot reaching through the ball within the stride (kicks and keepy-ups keep the kick).
  The close-control pace eases in and out (`BallController`) instead of jolting the speed as the ball comes in and out
  of reach. `review/dribble/`: the old and new gait on the kid, side by side (`render_gait.py`, `gait.py`).
- **Checked:** the runtime scripts compile; the editor scripts bind with no new errors; `PasserbyTests` (heights, the
  six-way turn order) and `GaitTests` (the steps quicken; the planted foot sweeps back at the body's speed at a walk and
  a jog; the run's stride flat out) pass, and fail on the old stride or a short Grandad. **Not run in Unity.**

## Smooth frames on mid-range phones; polished characters; illustrated kids (generated content v111)

**Why.** The user's OnePlus Nord CE5 recordings showed about 28 fps in Up the Hill (comic filter) and 21 to 23 fps on
the title screen, with frames from 17 to 79 ms. The user also said every character looked low quality in every mode,
the primary-school kids like photographs of real children, and even Hana and Max like low-quality assets. Six read-only
audits (GPU, CPU, assets and memory, character rendering, the Blender pipeline, the project history) found the causes,
listed in `docs/LEARNINGS.md` B1 to B6 and C1 to C12.

**Performance** (`docs/PERFORMANCE.md`):
- **`Core/GraphicsQuality` + `FramePacer`.** A tier per device: Low / Medium / High, with the Nord CE5 on Medium. The 3D
  picture is drawn at 720 / 864 / 1080 lines on Android (`Screen.SetResolution`, only on whole scene loads), and the
  touch thresholds follow it (`TouchDpi`). Sun shadows are none / hard, 1 cascade, 25 m / soft, 2 cascades, 35 m (from
  `WorldLook`); bloom is on High only. vSync is off, physics catches up at most 0.1 s, collision callbacks are reused
  and uploads time-sliced. The governor steps the tier down, then 60 fps to 40 or 30, when frames come late for 6 s,
  and remembers it, trying one step up again after 5 sessions.
- **Cameras** render without HDR or MSAA (runtime in `PostFX.OnEnable`, and in the scene builders).
- **`PostFX`** draws every pass once into a tiny target on its first frame, so shaders are built before play.
- **Android build settings** (`BuildScripts.ApplyAndroidPerformanceSettings`, by reflection where the API moved):
  Optimized Frame Pacing, Blit Type Auto, frame timing stats, batched GPU skinning, incremental GC, and every graphics
  tier without HDR or screen-space (cascaded) shadows, so no depth pre-pass and no shadow-collect pass.
- **Models** import without tangents; no shader reads them (`ModelImportSettings` v8).
- **Per-frame CPU and GC work**, each change reviewed by a second reader:
  - buttons, the touch buttons, the stick, the HUD's buttons and the menu's tap zone write their rects only on
    change and snap to rest;
  - `ProceduralShape.Update` is editor-only;
  - coins far off screen rest;
  - the developer panel is disabled in release;
  - `GameSettings` caches its values (PlayerPrefs is a JNI call on Android);
  - music and ambience upload one clip per frame, and the wanted soundscape is cached;
  - haptics cache their Java objects and drop pulses closer than 35 ms;
  - the comic words' glyphs are drawn ahead at each scene load;
  - outfit recolouring reuses a `Color32` buffer and skips identical requests.

**Characters** (`tools/blender/README.md`, "Polishing the characters"; `review/characters_v2/`):
- **The cause.** All six playable kids were torn into thousands of pieces. The fix `weld()` was made for the
  passers-by (`318993d`) after the kids had been built, and was never applied to them. Their scanned normals were
  shattered, and their atlases had thousands of islands with unpadded gaps. The kids' faces were photographs.
- **`polish_character.py`** (through `polish_all.py`, from the pre-polish originals at `f1b17b1`):
  - welds open edges within 2 mm;
  - turns back-to-front triangles round;
  - rebuilds the normals from the surface around each vertex (hair as one volume, the inner face leaned forward);
  - cuts each kid to 32k triangles, each bag to 8k and each passer-by to 14k, holding the head, hands and texture
    seams;
  - fills every atlas gap for the whole mip chain.
  Bones, rest pose, weights, outfit parts, vertex colours, bags and neck heights are unchanged. The FBXs went from
  90 MB to 28 MB.
- **`face_paint.py`** gives Kai, Leo, Mia and Zoe illustrated faces in their own skin tones: drawn eyes with highlights,
  brows, a nose stroke, each kid's own expression (Kai's grin, the others' smiles) and a little blush, placed where the
  scan's features were. Their outfits, hair and the user's designs stay as they were.
- **`ToonCharacter`:**
  - the outline is measured in pixels, never under 1.25 px, and set back 1.2 cm so inner folds draw no ink;
  - the light/shade step is anti-aliased;
  - the rim is narrower and takes the albedo's colour, so dark hair has no white flecks;
  - the player's outline is 0.0024, the thickest on screen as the art direction says (it was thinner than the
    passers-by's).
- **New player cards** (`Resources/UI/Player*.png`), rendered with `portrait_teen.py`, whose rim now matches the
  shader.
- **Reviewed** in Blender with the game's toon look: characters cast no shadows, as in the game, and the filters
  come from the numpy ports of `PostFX.shader`. The boards in `review/characters_v2/` show all six faces before and
  after, every look (Original, Comic halftone, Pencil sketch, Classic cartoon), and the player cards.

**Reverts recorded late** (`docs/LEARNINGS.md` A7):
- v84: Mia rebuilt in the scripted anime style, reverted at the user's request (the user's own design is kept; this
  restyle keeps it);
- v86: the camera closer still, reverted as v87 because collectibles fell out of view.

**Checked:**
- every script compiles against the Unity 2021 reference assemblies with empty uGUI/Input System stubs, with no
  error the clean tree doesn't have (a planted error is caught);
- `ToonCharacter`'s passes compile with glslang (a planted error is caught);
- the FBX round trip keeps every bone (max difference 5e-6) and every outfit part (no face across two parts, at most
  four bones a vertex).

**Not run in Unity or on a device.** Check on the Nord CE5, as in `docs/PERFORMANCE.md`:
- the frame rate and pacing in every look;
- the tier picked (the `[Graphics]` log line);
- touch at 864 lines;
- the new characters in every pose (`review_poses.py --leaks` was run on Mia: every pose clean,
  `review/characters_v2/mia_poses.jpg`; the other five were not rerun);
- the generated content v111 rebuild.

**Still to do:**
- bake the audio;
- fewer draws on the title screen;
- cheaper filter normals;
- recolour outfits in the shader;
- regenerate the store art and stickers that show the kids.

## Only the chosen kid and the bag they wear are loaded (generated content v112)

- **Why.** Every scene (the menu, every level, the Holiday core) was saved with all six playable kids and the five
  bags fitted to each, and only switched one kid and one bag on (`CharacterChoice`, `BagWear`). So every scene loaded
  them all: after the polish, about 545k vertices (~83 MB with the readable copies) and 11 atlases, for one kid on
  screen.
- **How:**
  - **The builder.** `LevelBuildKit.BuildCast` now saves each kid's and bag's renderer without a mesh or material.
    It moves both into a `Presentation/CastPart` asset at `Resources/Cast/<Model>/<Renderer>.asset`, and adds a
    `Presentation/LazyRenderer` (execution order -1000). That loads them as the object becomes active and lets them
    go as it is hidden. It keeps the renderer's built bounds, so culling is unchanged.
  - **What loads at start.** `CharacterChoice` runs first (-2000), so the kids not chosen are hidden before anything
    on them wakes. The builder saves every bag hidden, and `BagWear` shows the one worn. A scene now loads one kid
    and one bag: about 46k vertices (~7 MB) and two atlases.
  - **Switching kids.** When the menu switches kids, `CharacterChoice` loads the new kid's meshes before putting the
    remembered outfit back on, and asks Unity to unload what the old kid let go.
  - **Outfits.** `ModelOutfit.ForgetMesh` drops a released kid's recoloured copy.
  - **Co-op.** Ghosts keep `LazyRenderer` when stripped, so each loads its kid (and its bag, through its own
    `BagWear`) as it appears. The templates stay empty.
- **In the editor**, outside play, the generated scenes show the kids without their meshes (they load in play).
  Generated scenes are never edited by hand.
- **Checked.** The scripts compile against the reference assemblies with no new errors. The new types each have a
  file of their own (`ScriptConventionTests`).
- **Not run in Unity.** Check in the editor and on the phone:
  - the kid appears in the menu, a level, the Holiday Run and a co-op race;
  - switching kids in the menu and trying bags in the Locker Room;
  - a non-school outfit after a switch;
  - the Memory Profiler showing one kid's meshes per scene.

## The kids keep their own faces, with Max's finish (generated content v113)

- **Why.** The user rejected the drawn faces of v111 (`face_paint.py`): "They look terrible and look like aliens. The nose,
  eyes and mouth are rendered the worst. Max's eyes and facial features look good enough." The user asked for them to be
  reverted, and if possible made like Max. `docs/LEARNINGS.md` C14 has the cause: doll-eye shapes on a realistic
  child's head. Max reads as drawn because of his finish, not his shapes.
- **Reverted.** Kai, Leo, Mia and Zoe are rebuilt from their own scanned faces. The mesh polish of v111 (welding,
  normals, 32k triangles, filled atlas gaps) is kept.
- **Max's finish** (`tools/blender/face_ink.py`, run by `polish_all.py`): nothing is redrawn or moved.
  - **Eyes:** each eye's opening is found in the scan, and a dark lash line is drawn along its own top edge. The boys'
    lines end at the corner; the girls' end in a small flick. A faint line goes under the eye. The white is cleaned,
    the iris gets a little more contrast, and the scan's highlights stay.
  - **Brows** keep their own outline, filled with one dark brown.
  - **Mouth:** the lips' parting is darkened along its own curve, and the lips keep their colour.
  - **Nose:** as scanned.
  - **Skin:** flattened toward its own tone, keeping half its shading.
  - `polish_all.py --no-ink` gives the plain scans if the user prefers them.
- **New player cards** for the four kids (`Resources/UI/Player*.png`, `portrait_teen.py`).
- **Cost:** none. Only the four kids' 2048 atlases changed. The FBXs are the ones v111/v112 ship, since the geometry
  comes from the same originals by the same polish.
- **Reviewed** in Blender with the game's toon look (`review/characters_v2/`):
  - `faces_v113.jpg`: each kid as the rejected v111 face, the plain scan and v113, close up front and turned, next to
    Max at the same scale;
  - `player_cards_v113.jpg`: the same three on the player cards;
  - `faces_before_after.jpg`, `player_cards_before_after.jpg`, `cast_a_all_looks.jpg`, `cast_b_all_looks.jpg` and
    `mia_poses.jpg` (every pose clean, `review_poses.py --leaks`): redone with v113, so no board shows the rejected
    faces as the current state.
- **Checked:** the scripts compile against the reference assemblies with no new errors (only `GeneratedContent.Version`
  changed).
- **Not run in Unity or on a device.** Check the four kids on the Nord CE5 in every look, and ask the user to choose
  between the finish and the plain scans (`--no-ink`) from the board.

## Faces that stay whole, no white tears, Mia's eye (generated content v114)

**Why.** The user sent a recording of the title screen (Hana juggling) and three screenshots:
- Mia's right eye didn't look good;
- "lots of white tears in all the characters, from hair to face to clothing";
- Hana's face "is getting folded" as she animates.
The user asked for a check on every character, playable and not.

**What was wrong**, each found by splitting the render (`docs/LEARNINGS.md` C15 to C18):
- **Folded faces.** The rigged scans' automatic weights put the lower face partly on the Neck bone: 38% of Hana's face
  and three-quarters of her jaw, over 1,000 of Mom's face vertices, and every jaw some. The menu nods the head 6 to 20°
  to watch the ball, and the lower face squashed into the neck. The face's normal lean also skipped those vertices, so
  the light/shade step ran across the mouth and chin as a jagged crease.
- **White tears.** In a render of the vertex colours alone, white specks and slivers showed in every dark garment. They
  are light streaks the scans painted into the clothes (folds, highlights, unpainted seams), left out of their garment
  as a white vertex colour times a light texel.
- **White scratches.** The rim light whitened every colour by 45%, so it drew each crease of dark trousers and each
  clump of dark hair as a light line.
- **Mia's right eye** was scanned narrower and squinting.

**Fixed** (`tools/blender/polish_lib.py`, run on all twelve characters by `polish_all.py`):
- `rigid_head`: the head above a cut through the Head joint, dipping under the chin, follows the Head alone, blending
  to the neck below it.
- `face_lean`: the whole face, jaw and chin included, leans toward a sphere behind it, so it shades as one rounded
  shape.
- `absorb_tears`: a greyish face of no outfit part joins the garment that covers 65% of the surface within 2 cm of it.
  It then shades and recolours with that garment. Skin, the jacket's "H", the hoodie and stripes stay.
- **`ToonCharacter`'s rim** is whitened by 45% of the colour's lightness. Light clothes and skin keep their edge, and
  dark clothes and hair keep a faint sheen. Its Blender mirrors were updated in the same change: `portrait_teen.py`,
  `review_teen.py`, `review_poses.py`, and `review/cartoon/render_scenes.py`, which also gets the review scenes and
  diagnostics it had been missing.
- **Mia's right eye** is her left one, mirrored (`face_ink.py`).
- **New player cards** for all six playable kids.

**Cost:**
- One `max` of three channels per character pixel in `ToonCharacter`.
- The meshes are the same size (32k / 14k triangles) and the atlases the same.

**Reviewed** in `review/characters_v2/` (Blender, the game's toon look):
- `tears_v114.jpg`: every character before and after;
- `head_tilt_v114.jpg`: heads nodded 20° and 44°;
- `mia_eye_v114.jpg`;
- `player_cards_v114.jpg`.

**Not run in Unity or on a device.** Check on the phone:
- the title screen's juggling, and a slide;
- every look;
- the shop's recolours of Hana's jacket and Max's jeans.

## The middle of the body moves (generated content v115)

- **Why.** The user's recordings of Hana and Max dribbling: "the characters' bodies are so stiff, the chest to abdomen
  part. Because of that hand movement, it looks like hanging from a fixed thing." `CharacterRig` swung the limbs and
  pitched the whole body as one, and never moved the models' Hips, Spine or Chest bones (`docs/LEARNINGS.md` C19).
- **`CharacterRig.Torso`** works the trunk out from the limbs' own pose, so every animator gets it: the run, the walk,
  the passers-by, the menu's keepy-uppies, kicks, co-op ghosts.
  - **Chest:** turns up to ±15° with the arms' swing (a run about 12°, a walk about 5°).
  - **Pelvis:** turns up to ±10° the other way with the legs.
  - **Lower back:** shares the chest's turn against the pelvis, so the twist runs through the waist.
  - **Sway:** the torso sways 3° over the standing leg and dips 2° as the legs reach apart.
  - **Breathing:** the chest breathes (0.9°, each character at its own moment).
  - **Head:** turns, sways and dips back, so the eyes stay level and on the way ahead.
  - The turns use the sine of each limb's swing (how far the hand or foot reaches in front), so arms raised overhead
    turn nothing. All six amplitudes can be tuned on the component.
- **The builder** (`LevelBuildKit.BuildModelCharacter`) puts the Hips, Spine and Chest bones on the rig.
- **Weights:** no change. The torso already blends from Hips to Spine to Chest over about 30 cm, so the turn bends
  through the waist.
- **Cost:** three more joints per character per frame (a few quaternion products).
- **Reviewed:** `review/cartoon/render_scenes.py` mirrors it (`TORSO=0` gives the old rigid torso), and its `gait`
  scene renders a run or a walk cycle. See `review/characters_v2/torso_run_v115.gif` (Hana's run, before and after),
  `torso_run_v115.jpg` and `torso_walk_v115.gif` (Mom's walk).
- **Checked:** the scripts compile against the reference assemblies with no new errors.
- **Not run in Unity or on a device.** Check the turn's direction on the phone first: the near shoulder comes forward
  with the near arm. If it is mirrored, flip the sign in `Torso`. Then look at a run, a walk, the menu's juggling and a
  kick.

## The last white tears, and review boards that match the game (generated content v116)

- **Why.** On the v114 boards the user found:
  - black spots on Kai's face;
  - white tears still at Hana's and Max's trouser hems above the shoe;
  - white streaks on Max's jeans below the jacket (his belt);
  - white tears along Mia's hairline.
  The user asked for similar faults to be fixed on every character.
- **Kai's spots were the review renderer's** (`docs/LEARNINGS.md` C20). Its ink hull was a Solidify on the figure
  itself, which threw away the smoothed normals the game shades with, and it was never set back from the camera as
  `ToonCharacter`'s is. In a render with the ink coloured magenta, the spots turned magenta. The hull is now a copy of
  the figure set back 1.2 cm, and the figure keeps its normals. Kai's face (and every chin's "brown patch") renders
  clean, as the game draws it.
- **The tears were real.** `polish_lib.absorb_tears` gets a second test. A pale face of no outfit part joins the
  garment when the garment wins against only the neighbours that look like the face, while that kind stays sparse
  round it. This catches a hem against a white shoe, a belt's streaks against a hoodie's hem, and a fringe's tips
  against the face. A printed letter has many of its own kind round it and stays: Leo's "AWESOME 01" and Hana's "H"
  are checked.
  - Rebuilt: all twelve characters (`polish_all.py`).
  - Absorbed faces: Max about 1,680 (was 570), Hana 1,600 (was 970), Mia 1,190 (was 1,060).
  - Hana's striped cuffs, cut into jagged white triangles at 32k, are now plain maroon.
- **The face must be nearly grey, white or cream** for the second test (saturation under 0.21). On the first try it
  took Mia's beige patterned headband (0.25 and up) for streaks. Hana's cream cuff stripes (about 0.17), cut into jagged
  triangles at 32k, still go.
- **The player cards** (Blender renders shipped in the game) had the review renderer's fault: `portrait_teen.py` put
  the hull on the figure, so the cards' faces had black specks round the nose. The cards, `review_teen.py` and
  `review_poses.py` now share `tools/blender/ink_hull.py` (the figure keeps its normals; the hull is set back), and all
  six cards are rendered again.
- **Boards:** `review/characters_v2/tears_v116.jpg` (every character, v115 and v116, both with the corrected renderer),
  `kai_face_v116.jpg` and `player_cards_v116.jpg`.
- **Cost:** none (same meshes and atlases).
- **Not run in Unity or on a device.**

## Opens in Unity 6.5 without Safe Mode; a clean console

- **Why.** The user opened the project in a newer Unity 6 and it offered Safe Mode: "The project you are opening
  contains compilation errors". The console listed:
  - `CharacterRig.cs(100,28): error CS0619: 'Object.GetInstanceID()' is obsolete: 'Use GetEntityId instead.'`;
  - five CS0675 warnings in `RoomBeacon`;
  - "This project uses Input Manager, which is marked for deprecation".
- **The cause** (`docs/LEARNINGS.md` A11). `GetInstanceID` (added in v115 to spread the characters' breathing) is an
  error from Unity 6.5, a warning in 6.4 and fine in 6.0. Every check here compiles against Unity 2021's reference
  assemblies, so it passed. Unity compiles the editor scripts only after the game's, so nothing behind that error had
  been checked in 6.5 either.
- **Fixed:**
  - `CharacterRig` spreads the breathing by a golden-ratio counter, with no id.
  - `RoomBeacon` widens each field through `uint` (the bits are unchanged).
  - `Editor/InputHandling` sets Active Input Handling to the Input System package when the editor loads, and offers
    the restart it needs. The game's input already uses the Input System when it is on (`GameInput`, `UIKit`'s
    `InputSystemUIInputModule`), and nothing else reads input.
  - Initialised five fields that only `JsonUtility` or a player build fills, so their warnings don't appear in the
    editor or the build log.
- **The check that would have caught it:** `tools/unity_api_check`.
  - It resolves every Unity API the scripts use with Roslyn, for every `#if` combination, and checks each against the
    `[Obsolete]` list in Unity's own C# reference source for a given version.
  - For 6000.5 and 6000.7 the only error in the whole project (game, editor, tests) was `GetInstanceID`. The check
    flags the old code and passes the new.
  - `ScriptConventionTests.NoScriptCallsAnApiANewerUnityRemoved` guards the known removed calls inside Unity.
- **Checked:**
  - The compile check: no new errors.
  - Roslyn: no compiler warnings left in any `#if` combination. The same scan shows the five CS0675 on the old
    `RoomBeacon`.
  - `unity_api_check` for 6000.5 and 6000.7: no errors.
- **Not run in Unity.** Open the project in the user's Unity:
  - accept the restart;
  - confirm the console is clean;
  - play a level with touch on the phone, since the input now goes through the Input System;
  - run the edit-mode tests.

## The tests compile again (fix for #49)

- **Why.** After #49 the user's console showed nine errors on `Tests/Editor/ScriptConventionTests.cs` line 78, and still
  the Input Manager warning. The new test's pattern held `\"` inside a C# verbatim string, which ends the string
  (`docs/LEARNINGS.md` A12). The editor assembly, with the tests and the new `InputHandling`, stopped compiling, so the
  input setting was never applied either.
- **Fixed:** the pattern uses `""`, the verbatim string's quote.
- **The gap:** the test file is behind `#if UNITY_INCLUDE_TESTS`, which no check defined, so it was never even parsed.
  `tools/unity_api_check/run.sh` now parses every script under every combination of the scripts' `#if` symbols, the
  tests included, with NUnit referenced so they bind. It exits with an error on any syntax error.
- **Checked:**
  - No syntax errors in any combination.
  - No compile errors beyond those the tree before #49 already had (the checks' stand-ins for uGUI and the Input
    System), tests included.
  - Planted back, the old line 78 is caught with Unity's own errors.
  - `run.sh 6000.5`: no errors.
- **Not run in Unity.** Open the project:
  - accept the "Restart Unity" prompt (Active Input Handling switching to the Input System);
  - confirm the console is clean;
  - run the edit-mode tests.

## No warnings in Xcode's GameAssembly; a quiet Holiday Run build

- **Why.** With the project compiling in Unity 6.5, the user built to an iPhone. Xcode showed 13 issues in GameAssembly:
  - one "The selected platform is no longer supported by libc++";
  - twelve libtool "'x.o' has no symbols".
  The Unity console had the Input Manager warning, and four "Holiday Run stage 11 to 14: 'Waves' was left outside the
  Stage object" warnings from the level build (`docs/LEARNINGS.md` A13).
- **Fixed:**
  - **iOS minimum:** `BuildScripts.IosMinimumVersion` (15.0) is applied when the editor loads, with the signing
    (`AppleSigning.Apply`), so a build from Unity's own Build button has it too. It is never lowered.
  - **Every Xcode target:** `IosPostBuild` raises every `IPHONEOS_DEPLOYMENT_TARGET` in the exported project to at least
    15.0, GameAssembly's included.
  - **libtool:** `IosPostBuild` adds `-no_warning_for_no_symbols` to GameAssembly's libtool flags (and the
    project's). IL2CPP files of assemblies with no code are expected.
  - **Waves:** the beach's waves are built under the animals' root, with the other moving things outside the static batch,
    which the Holiday Run builder already files under each Stage. Today's levels already have them moved, so the
    generated content isn't rebuilt for this; the next rebuild is quiet.
  - **Input Manager:** nothing to change. The warning is Unity's, printed at start-up. It stops once the editor is
    restarted from the "Restart Unity" prompt that `InputHandling` shows (A11).
- **Checked:**
  - No syntax or new compile errors in any `#if` combination. The post-build code was checked against stand-ins for
    the Xcode API.
  - No compiler warnings.
  - `unity_api_check` 6000.5: clean.
  - The deployment-target rewrite was tested on sample project lines (13.0 and "12.4" raised, 16.0 and 15.0 kept).
- **Not run in Unity or Xcode.**
  - Restart Unity from the prompt.
  - Export the iOS project again. Choose Replace, or delete `Builds/iOS` first, as `docs/RELEASE.md` says to after a
    Unity change.
  - Confirm Xcode's issue navigator is empty.

## Every APK installs over the one before it

- **Why.** An APK the user built and sent to the Nord CE5 over WhatsApp failed to install ("Installation failed.
  Please try again.") over the test builds already on the phone (`docs/LEARNINGS.md` A14). An APK from Unity's own
  Build button carried the store build number as its version code, far below the test builds' (about a million and
  up), and Android refuses a lower version code over an installed copy.
- **Fixed:** `Editor/AndroidApkVersionCode` writes the always-rising test version code (`BuildScripts.TestVersionCode`)
  into every APK's generated Gradle project (`launcher/build.gradle`), however it is built. Player Settings' store build
  number is never changed. App bundles keep it.
- **Not fixable in code:** an APK signed with another key than the copy on the phone (built on another computer, or
  with the release key) still needs that copy uninstalled once.
- **Checked:** no syntax or new compile errors in any `#if` combination, no warnings, `unity_api_check` 6000.5 clean.
  **Not run in Unity:** build an APK with Unity's Build button and look for "[Build] APK version code" in the console.

## Image prompts for a Florida add-on (docs only)

- **`docs/IMAGE_PROMPTS.md`**: copy-paste ChatGPT prompts for the reference images a new add-on town is modelled from. It has a base prompt for any place (the side-scroller's straight-on camera and empty play lane, the game's midday cobalt light, no people, invented signs), a Florida block (A1A beach-town Art Deco and MiMo, concrete-block ranch houses, hurricane shutters, sabal palms, concrete poles, span-wire signals) and one shot per chapter, with the six supplied street illustrations as F3-1 to F3-6, plus props, plants and texture-plate sheets.
- **Photorealistic, lit like the game:** the images are modelling references for script-built Blender kits; the toon look comes from the shaders and grade. The supplied illustrations are used for content and layout only (they are a sunset).
- **Add-ons:** none for Blender (`bpy` scripts) or Unity (built-in pipeline, own shaders).
- No game code or assets changed; the Florida add-on itself (`_FL` scenes, its kit) is not built.

## The Florida add-on: chapter 3, its own music (generated content v117)

- **Add-ons & Filters** lists **Florida, Cocoa Beach, USA · Seaside Road** after California (`Progression/AddOns.Florida`, id
  `florida`, scenes `<scene>_FL`). It is unlocked as California is, by finishing every story level. So far it has only chapter
  3 (`AddOn.chapters`, `AddOns.FloridaChapters`): while it is chosen, every other chapter's levels are locked
  (`LevelUnlocks.NotInTown`, in `IsUnlocked`, `NextToPlay` (which falls back to the first beach level short of three stars),
  `LevelManager.NextLevel` (Next finishes after the beach), `nextLocked`, and a guard in `LoadLevel`). A locked level's node
  or strip chip says why when tapped (`map.notInTownTitle`, `map.notInTown`) and offers Seaside Road. California's rule is
  unchanged.
- **Florida replaces Tokyo** in Add-ons & Filters: the Tokyo city add-on (`japan`, `_JP`, listed as coming soon) is gone,
  with its strings, and Florida's card stands where it stood (the list: Original, California, India, Florida). The co-op
  locations (only the add-ons that can be chosen) are still Original, California, Florida.
- **Co-op:** Florida only runs Seaside Road. The picker shuts the pairs that don't fit (`coop.place.only`,
  `coop.route.notIn`). The host's random picks only choose a pair that fits (`CoopSession.LocationFits`, set to
  `CoopLocations.Fits`), and a stale Florida choice on another route runs in the original streets. Adding a location changes
  the content hash, so an older build is turned away as another version.
- **Florida's own music** (`MusicCountry.Florida`, appended so the clip keys of the others stay; `MusicGenerator.FloridaStyleOf`):
  - the beach: soca with steel pans and a marimba;
  - Home Street: a Cuban son (a marimba montuno, an upright bass's tumbao, the 3-2 son clave, bongos, congas, a guiro);
  - the market: Miami salsa;
  - the underpass: a neon Miami night groove;
  - the building site: a calypso drive;
  - the park: a one-drop;
  - the menu: a trop-rock sunset.
  New instruments: `Instruments.Clave`, `Bongo`, `Guiro`. New parts: the off-beat `Skank`, the `Montuno` and reggae's
  `OrganBubble`.
- **The Florida kit** (`tools/blender/kit_buildings_fl.py`, `kit_buildings.py --kit Florida`, `Art/Models/Florida`: 39
  models, 9.8 MB with the atlas), after the user's references in `review/florida/refs`. Review sheets and street previews are
  in `review/florida/`. It holds the beach front, the diner and motel, the rental shop, five Art Deco shops, the street's
  things and Seagrove High. Its signs and patterns are painted by the kit (`kit_buildings_atlas.EXTRA`). The Plants kit gains
  `PalmSabal`, `PalmSabalTall` and `SawPalmetto` (`fan_leaf`, `sabal`). Every model is within ART_DIRECTION's budgets: the
  motel 5,992 triangles, the diner 4,520, the sabals 5,340 and 5,012, the street things 90 to 1,132.
- **The `_FL` scenes** (`GeneratedContent.BuildFlorida`, `LevelSpec.FloridaPath`, built for chapter 3's levels and C03; kept
  by `DeleteStaleScenes`; required by `AllScenesExist`):
  - The kid's beach is unchanged: its sand, tides, channels, dunes and sea, and every gameplay piece.
  - `StreetBuilder.Florida` puts the town on seawall terraces behind the lane, running out over the sea. It leaves open beach
    over the tides, channels, dunes' slopes, stops and pier.
  - The beach's parasols, towers, rocks and palms keep to the gaps (`InStrip`).
  - The strip runs in the references' order. Each level starts it where the one before left off (L11 at the beach front, L12
    at the diner, L13 at the motel, L14 at the Deco shops).
  - Toward the school: the bus shelter, a mailbox and the school-zone beacon. The school is `TrackBuilder.FloridaSchool`
    (`LevelBuildKit.Florida.cs`).
  - The lifeguard towers become Florida's stand, the surf school's and the café's huts the snack shack.
  - L11's home street before the beach is the Coast kit's suburb, with sabals for its date and fan palms (`FloridaPalm`).
  - The Buildings kit draws with its English-sign atlas.
- **Cost:** nothing in the original or California scenes (Florida's code only runs with `LevelBuildKit.Florida` set). In a
  `_FL` scene, per the estimates below; none of this has been measured:
  - textures: one more 4096 x 4096 atlas, about 16 MB in memory at RGBA32, a quarter of that compressed;
  - geometry on screen: about 12k triangles of buildings, 25k to 35k of sabals and a few hundred of street things;
  - collision: the terraces are three boxes per run and have no colliders.
  - It must be checked on the Nord CE5 (L13's motel stretch is the heaviest).
- **Checked:**
  - compile: no new compile errors in any `#if` set; `unity_api_check` 6000.7 clean.
  - tests: the co-op session tests run outside Unity (68 pass; a planted bug in the new rule made its test fail).
  - music: Florida's loops render in a harness at the target loudness, with no NaN samples.
  - kits: the Coast kit rebuilds byte-identical; the Plants kit rebuilds identical apart from the three new palms (same
    atlas, no existing manifest entry changed).
  - previews: `preview_street.py --florida` renders through the game camera.
- **Not run in Unity:** the `_FL` scenes' build, the new FBXs' import, the terraces against the real tides and stops in each
  level, the school end, the map's new note, the co-op picker, the music in game, and the frame rate on the phone.

## The audit: work nobody sees (generated content v118)

- **Why.** The user asked for a performance audit across the game and every supported device: faster, with the same
  assets and the same gameplay. Four reviews ran in parallel: gameplay scripts; UI, menus, co-op and audio; GPU and
  shaders; loading, memory and builds. Each finding was checked in the code before anything changed, and only changes
  that keep the picture, the sound and the play exactly the same went in (`docs/LEARNINGS.md` B8). The costs and what
  is still to do are in `docs/PERFORMANCE.md`, "The November 2026 audit".
- **Off screen, or nothing changed: skip it.**
  - `TideWash` rebuilds its sheet only when it is on screen and its level or clock moved (each wash re-uploaded a mesh
    every frame), and reads its transform once.
  - `Lapping` (about 45 breaking-wave crests a beach level) rests out of view; its pose follows the clock alone.
  - `Fountain` keeps the jet's height (the ball's lift) but poses its jets and droplets only on screen.
  - `Crossing` writes its signal's colours and its cars only when they change (the queue mostly stands still).
  - `Springboard`, `DarknessOverlay` and collected coins stop writing once at rest (a collected coin switches itself
    off until the level resets it).
  - `WindArea` finds its streaks' renderers once and switches them only when a gust starts or stops.
  - `FxPool` returns at once with no live particle and keeps its transforms; the ambient animals read their position
    once and write position and rotation together; `WheelSpin` reads its car's position once.
- **Built every frame: build it on change.**
  - `GameInput`: one touch layout a frame (it was worked out about five times), and no new delegate every frame.
  - The challenges' status line is built again only when a number in it or the language changes.
  - The coach card compares what it shows field by field (it built a string every frame) and writes its rect on change.
  - The Holiday HUD's buttons get the same write-on-change as the story HUD's.
  - The co-op join list is keyed on what it draws (the signal word and the order), not the raw strength, which jitters:
    it was rebuilt about twice a second for nothing.
  - `ModelOutfit` works out each vertex's part and shade once, so a passer-by's recolour is one multiply a channel (the
    same Color32 rounding as before).
  - `KidController` finds a moving surface through the ground collider's body: static ground skips the search.
  - The ball and passers-by fill a reused list with the kid's colliders.
- **Hidden: don't draw it.**
  - The map screen's opaque mat hides the whole 3D menu street: while it shows, the menu camera draws nothing and its
    filter rests (`MenuStage.Covered`, `FrontEndScreen.CoversStage`).
  - The story HUD's clear fade is switched off while clear, as the Holiday HUD's already was.
  - The sky dome is drawn after the opaque geometry (`Sky.shader`), so only the sky that shows is shaded.
  - The Fields, the Sea and the menu's field cast no shadows (they lie under everything), and the distant hills and the
    clouds receive none (far past the shadow distance). Generated content v118.
- **Garbage and memory.**
  - The music and ambience generators reuse their work buffers within a place's synthesis (`Scratch` in `Mixdown.cs`),
    and a part the arrangement never plays gets no buffer. Every one of the 95 clips is bit-identical to before (a hash of
    each, `tools/audio_hash`). Garbage per new place: Market 170 → 113 MB, the others 13–25 MB less.
  - The ambient cues' samples are let go once Unity has its copy (up to 8 MB a place).
  - A Holiday Run stage's combined street meshes (`StaticBatcher`) and tide meshes are destroyed with the stage. They
    belong to no scene, so they stayed after it unloaded: a lap's worth more each day of the run.
  - The kid picker frees the kid just hidden a second after the last tap, not on every tap (a hitch per tap).
  - The async upload buffer is 16 MB (was 32): the largest texture is about 10 MB.
- **Loading and I/O.**
  - Every scripted build is LZ4HC (LZ4 for the development APK). On Android only LZ4 builds use the async upload
    pipeline, so textures no longer go up in the frame their scene comes in. Set the Build Profile's Compression Method
    to LZ4HC for Unity's Build button too (`docs/RELEASE.md`).
  - The map's picture (3200 × 1800) is read in the background from the title screen, one tap before the map opens.
  - Analytics writes its file on a worker thread, in order.
  - iOS: the accelerometer is off; nothing reads it.
- **Left for later, with the reasons** (`docs/PERFORMANCE.md` "Still to do"): the audio bake (Vorbis needs a listening
  A/B), the Holiday stage wake (measure first), the filter normals and the classic cartoon's shader savings (need a
  shader compile and screenshot diffs), async scene loads, nested canvases for the menu animations (every button needs
  testing), occlusion culling for the title screen, shader recolouring so meshes need not be readable, the noise texture
  (within 1/255 only), the co-op and haptics JNI calls, and pinning the remaining player settings. iOS still has
  screen-space shadows (a look change, so it is the user's call).
- **Checked:**
  - No syntax errors in any `#if` combination; the compiler errors are exactly a clean tree's (the stand-ins' misses);
    no warnings. `unity_api_check` 6000.7 (the newest branch): clean.
  - The audio: all 95 clips hashed before and after, identical. Merged with the Florida add-on (#53), whose 7 new
    music loops are in `tools/audio_hash/expected.txt` too; the 95 from before are unchanged.
- **Not run in Unity or on the phone.** Every saving above is an estimate. On the Nord CE5:
  - Rebuild the generated content (v118) and play Low Tide, a story level with a crossing, and a Holiday Run lap.
  - Compare the frame times, and the Memory Profiler after two Holiday Run days.
  - Open the map in each look: it should look the same, and the GPU should go nearly idle.
  - Check the sky and the far hills look the same.

## KICK says "hold to control"

- The KICK button carries a small second line under its name, **HOLD TO CONTROL** (`hud.kickHold`; Spanish *MANTÉN PARA
  CONTROLAR*): holding KICK keeps the ball at the kid's feet, which only the controls tour and the guide said before.
  `TouchButton.AddHint` puts it along the bottom of the disc, moves the name up a little and shrinks the line to fit the
  disc's narrower bottom. It is on the levels' HUD (`GameHud`) and the Holiday Run's (`HolidayRunHud`, which redoes it when
  the language changes).
- Checked: no new compile errors in any `#if` set, `unity_api_check` 6000.7 clean, a mock-up on the user's screenshot at
  the button's real size (both languages fit inside the disc). Not run in Unity.
- **Inside the circle:** the first version's hint box reached 0.51 of the disc from its centre at its lower corners, just
  outside the circle (the mock-up's flat patch also crossed the rim, though the game draws no background there). The label
  and the hint now take `TouchButton.HintLabelArea` and `HintArea`, whose corners lie at most `TextReach` (0.45) from the
  centre, clear of the rim; `TouchButtonTests` checks it.

## Feet on the ground, no stray patches in any outfit, a flower bed (generated content v119)

**Why.** The user's screenshots of Mia in the Holiday kit (teal top, khaki shorts):
- "lots of white tears/patches across all the models";
- the flower obstacle looked "attached to the floor";
- when sliding or kicking, "the foot/legs are going into the ground";
- black spots on Max's forehead (his player card).
They asked for each to be fixed on every character. Later: "Don't wipe out the eyebrows, keep them as they were."

**Feet and legs through the ground** (`docs/LEARNINGS.md` C21). Posed on the shipped models and measured
(`tools/blender/ground_check.py`), the slide put the back foot and shin 17 to 25 cm under the pavement on all six
kids, a landing 1 to 5 cm, a kick from a stride and the run's passing step 2 to 3 cm.
- **The slide's back leg** is tucked with its knee up and its foot planted (`KidAnimator.SlidePose`, and
  `CoopGhost`'s copy), instead of the shin folded down under a level thigh.
- **`CharacterRig` keeps the model on the ground.** `LevelBuildKit.MeasureGroundPoints` stores about 140 points of
  each model's surface (the extremes of the soles, shins, knees, seat, forearms and hands, in their bones' frames).
  After every pose the rig lifts the body just enough that none is lower than the lowest stands at rest. Every
  animator gets it: the kid, the menu, co-op ghosts, passers-by.
- **Measured after:** at most 0.6 cm under the ground on any of the six kids in any pose checked. The slide now
  lifts the body 7 to 15 cm above where the pose put it: the trailing foot and the planted hand meet the ground.
- `review/characters_v2/slide_ground_v119.jpg`: Mia and Max from the side, before and after.

**Patches in a recoloured outfit** (C22). Rendered flat in the Holiday kit (`tools/blender/outfit_render.py`), every
scanned character showed faces left out of a garment (Mia's white collar and sleeve hems, the red and white streaks
down her shorts, Max's navy waistband and hems, red and white slivers in Kai's plaid, Hana's dark jacket slivers) or
tagged with one they don't belong to (khaki flecks on Mia's socks), and a green and pink zebra in Mia's shorts.
`polish_lib.settle_parts`, run on all twelve characters by `polish_all.py`:
- a face of no part joins the part round it when it is painted like it (by colour ratio) or is a sparse pale streak;
  only faces of no part move into a part, judged once where a rule could cascade;
- a stray island of a garment on something else leaves it and shows its texel as painted;
- a saturated garment's texels become grey shading (no zebra);
- along the hairline, light paint on the skin within 2 cm of the hair takes the skin's colour (Max's forehead).
- **The brows are untouched:** nothing within 7 mm of a mark on the face that isn't joined to the hair is changed,
  and a pixel difference of every head shows changes on the hairlines only.
- Boards: `outfits_holiday_v119.jpg` (all twelve, Holiday kit, before and after), `heads_brows_kept_v119.jpg`,
  `heads_changed_pixels_v119.jpg`, `max_forehead_v119.jpg`, `player_cards_v119.jpg` (all six cards re-rendered).
- **Still to do:** Max's grey fringe tips are fainter but not gone; Max's waistband keeps a few navy patches; one
  jacket-tagged wedge in the office worker's shirt (a peninsula of the jacket, not an island) stays.

**The flower obstacle** (E9). Chapter 1's low obstacle could be three flower patches standing on the bare paving, their
leaves flat on it. It is now a raised bed (`LevelBuildKit.FlowerBed`): a stone kerb, soil, the patches growing out of it
to a little over the box's top.

**Cost** (`docs/PERFORMANCE.md`): about 140 points transformed per posed model character per frame (one matrix per
bone, est. 0.01 to 0.03 ms each on the Nord CE5). Meshes and atlases are the same size.

**Checked:** no new compile errors in any `#if` set (a planted error is caught), `unity_api_check` 6000.7 clean, the
ground measured on all six kids, every character rendered before and after. **Not run in Unity or on a device.** Check
on the phone: a slide (the trailing foot on the pavement, the slide still clears the bars), kicks, a landing, the run
(no visible change in its bounce), the flower bed in L01, and Mia, Max and Kai in the Holiday kit.

## Unity pinned to 6000.6.7f1

- `ProjectSettings/ProjectVersion.txt` pins **6000.6.7f1** (was 6000.0.68f1), at the user's request. Unity Hub opens
  the project in it, and `ci/android/build_android.sh` and `ci/ios/build_ios.sh` pick it first when Hub has it. It
  generates the iOS UIScene life cycle (any 6000.4+ does).
- Packages (`Packages/manifest.json`) are unchanged: Unity raises any below its minimums when it opens the project.
- README, `docs/RELEASE.md` and `tools/unity_api_check/README.md` name the version.
- Checked: `tools/unity_api_check/run.sh 6000.6` (the pinned branch) and `6000.7` (the newest): clean. Not opened in
  6000.6.7f1 here: check the console after the first open.

## Mia's white stripes, standing still on platforms, a splash you can see, a still slide (generated content v120)

**Why.** The user's screenshots of Mia in her own colours (white streaks down the sides of her red shorts, white specks
along her hair) and three recordings: on Duck Pond's moving platforms the kid walked on the spot; a ball falling in the
water showed only the word "Splash!"; in a slide one leg vibrated (`docs/LEARNINGS.md` C23).

- **Mia's white.** Decimation left a few very large triangles (up to 20 cm²) across the shorts' white side stripe, the
  red and the bare leg at once, which no outfit part can fit.
  - `polish_lib.split_mixed` splits large two-colour triangles (largest first, up to ~1,000 more triangles a figure:
    32.7k to 33.0k for the kids, 14.1k to 14.7k for the passers-by).
  - `settle_parts`:
    - judges skin by a face's own texels (a white and red blend averages to pink);
    - joins small pale clusters near a garment or the hair to it whole (in the hair only specks, so the shopkeeper's
      white under-scarf stays);
    - joins a mostly pure-white face to the garment closing it in;
    - never pulls a face with bare skin in it into a garment.
  - All twelve characters rebuilt, the six player cards rendered again. The brows are untouched (the head pixel
    difference, `heads_changed_pixels_v120.jpg`, shows the hairlines only).
  - Boards: `mia_white_v120.jpg` and `cast_own_and_holiday_v120.jpg` (every character in its own colours and the
    Holiday kit, before and after).
  - Still there: a few small white slivers by Mia's fist and the shirt's hem at her waistband.
- **Platforms.** The walk cycle follows `KidController.StrideSpeedX`: the speed over the surface under the feet, so a kid
  standing on a moving platform stands still until the player moves.
- **The splash.** It was raised by the water's lose zone, two metres under the surface, as the screen faded.
  - A `WaterSplash` trigger at the surface of every trench, stream and tidal channel raises it where the ball or the kid
    goes in. A kid's fall splashes harder than a ball.
  - `FxDirector.Splash` draws two foam rings flat on the water, a crown of drops, a column up the middle, hanging spray,
    and the drops landing back in rings.
- **The slide** holds its pose: the trailing leg's ±5° scuff (3 to 5 times a second) and the body's judder are gone.
- **Cost:** up to ~1k triangles a figure; the splash is ~40 pooled particles once per splash.
- **Checked:**
  - no new compile errors in any `#if` set;
  - `unity_api_check` 6000.6 clean;
  - every character rendered before and after.

  **Not run in Unity or on a device.** Check on the phone:
  - Duck Pond: stand on a platform, then walk on it;
  - the ball and the kid falling into water (Duck Pond, a beach channel);
  - a slide;
  - Mia close up on the title screen.

## Input System 1.20.1 for Unity 6.6

- **Why.** Opened in the pinned 6000.6.7f1, the editor failed to compile Input System 1.11.2: about a hundred CS0619
  errors on `TreeView`, `TreeViewItem` and `TreeViewState`, which 6.6 makes obsolete as an error (`docs/LEARNINGS.md`
  A15).
- **Fix:** `Packages/manifest.json` takes Input System 1.20.1, which uses `TreeView<int>` from 6.2 on. The game's calls
  into it are unchanged.
- `tools/unity_api_check/package_minimums.py`, run by `run.sh`, fails when a package is too old for the pinned Unity.
  It catches the old manifest and passes the new one.
- **On the user's machine:** close Unity, delete `Packages/packages-lock.json` and
  `Library/PackageCache/com.unity.inputsystem@*`, then reopen. Unity keeps the old copy otherwise.
- **Not opened in Unity here.**

## Florida's Home Street: a canal suburb that plays differently (generated content v121)

- **Why.** The user asked for a Florida Home Street from five references (ranch houses with red doors, awnings and screened
  porches, pink and yellow ranches, Old Florida cottages with porch swings and picket fences, a Mission church with a bell
  tower, a bus shelter, live oaks with Spanish moss, a canal with docks, a boat lift, a No Wake sign and a concrete bridge rail)
  that is "more exciting rather than the same gameplay across all cities". Mid-way the user also asked for "good garden space
  and lawn areas in front of a few homes".
- **Chapter 1 in Florida.** `AddOns.FloridaChapters` is `{ 1, 3 }` (`addon.florida.place`: "Home Street, Seaside Road"), so
  chapter 1's levels and C01 each get a `<scene>_FL` scene and are open while Florida is chosen. Every Florida level's home
  street before its seam (chapter 3's too) is now Florida's, not the Coast kit's villas.
- **Florida-only gameplay** (`LevelBuildKit.FloridaPlay`, `TrackBuilder.InFlorida`; the original and California layouts are
  untouched):
  - **L01 and L04: lawn sprinklers** (`Sprinkler`, a fountain with the sprinkler's look) throw the ball up to an arc of coins.
  - **L02: the groundskeeper's golf cart** (`GolfCart`, a `MovingPlatform` with a 0.95 m flat bed) drives up and down where
    the original has a parked car: hop on and ride, or slip past.
  - **L03: a canal under a bascule drawbridge** (`Drawbridge`, `Hazards/Drawbridge`) replaces the flooded trench. The canal is
    5 m, wider than a double jump. Its two leaves are kinematic bodies on a cycle: down 6 s, then bells, flashing lights and
    gate arms (1.6 s), up (2.2 s), held (2.4 s), down (2.2 s). Wait for it. The worst wait is 8.4 s, inside L03's 80 s bell.
    `LevelFeasibility.AddDrawbridge` counts the leaves as the bridge over the hole
    (`ADrawbridgeCrossesACanalNoJumpCould`).
  - **L05: an afternoon thunderstorm**, with gusts against the kid and then behind, instead of the rainy morning.
  - Each has its how-to: `coach.drawbridge`, `coach.sprinkler`, `coach.golfcart` (en, es; `CoachPlan.Actions`,
    `CoachCatalog`).
- **The street** (`StreetBuilder.FloridaHome`, and Florida branches in `StreetBuilder`):
  - houses: `RanchFL`, `RanchSmallFL` and `CottageFL` in faded pastels (`RanchPaints`, `CottagePaints`), front yards mostly
    open lawn (fewer pickets, fewer hedges), rural mailboxes at the kerb;
  - **deep gardens:** about one lot in three (`GardenLot`, by place) sets its house 3.2 m further back behind a mown lawn,
    with a walk from the gate to the door, beds along the front, an island bed with a saw palmetto or a young sabal, and
    hibiscus at the corners (`FrontGardenFL`);
  - live oaks with Spanish moss between the rows (`StreetOaks`), and sabals in the gardens;
  - the back row and the far row are Florida's houses;
  - the horizon is only the pine flatwoods' tree line: Florida is flat (`DistantHills`).
  - The kid's house is a seafoam ranch with the red door (`HomeInfoFL`, a wider plot). Granny's is a pink cottage, Sam's a
    yellow ranch, St Mary's the Mission church (`MissionChurchFL`), the bus stop the aluminium shelter (`BusStopFL`).
  - The canal runs back to the end of the ground, with docks and boats on lifts, the No Wake sign on its pile, and the
    concrete balustrades along its banks behind the street. `TrackBuilder.Canals` keeps houses, back rows and far rows off
    it and cuts it from the verge; it is not an open area, which would pave a side street over it.
- **Kits:**
  - The Florida kit gains 14 models (`kit_buildings_fl.py`): the two ranches, the cottage, the church, the mailbox post, the
    golf cart, the sprinkler, the drawbridge's leaf, tower, gate post and arm, the balustrade, the dock and the No Wake sign.
  - Every existing model's manifest entry is unchanged, but the atlas is repainted with the new tiles, so every Florida FBX is
    re-exported with it.
  - The Plants kit gains `LiveOak` (5,080 triangles), and nothing else in it changed (same atlas, same entries).
- **Cost** (estimates, not measured):
  - Nothing changes in the original or California scenes.
  - In a chapter 1 `_FL` scene, against California's suburb, which it replaces: the houses are lighter (1,774 to 3,070
    triangles against the villas' 3,877 to 5,276).
  - A live oak (5,080) costs about what a palm does, and one to three are on screen.
  - A deep garden adds about 6k to 7k (up to 7 flower patches at 711, a saw palmetto at 864, two shrubs at 780), and one is
    on screen at a time.
  - The drawbridge set is about 4k triangles.
  - The flat horizon drops the hills and both mountain ranges.
  - No new textures: it uses the same Florida atlas.
  - Physics: two kinematic leaves and one moving platform.
  - It must be checked on the Nord CE5, first L03's canal.
- **Checked:**
  - compile: no new compile errors in any `#if` set; `unity_api_check` 6000.6 and 6000.7 clean;
  - tests: `LevelFeasibilityTests` 9 pass outside Unity;
  - the coin audit: 447 coins, 0 problems;
  - the coach texts are within the card's limits (36 and 140) in both languages;
  - previews: `preview_street.py --chapter 1 --florida [--canal a:b --lift deg] [--home x]` mirrors the street. Its renders are
    in `review/florida/home_street_*.jpg`.
- **Not run in Unity:** building the `_FL` scenes, importing the new FBXs, the drawbridge's leaves under the kid and the ball,
  the golf cart's ride, the sprinklers' throw, the storm's gusts, the stops, and the frame rate on the phone.

## Five cities, a city picker, Filters on their own (generated content v122)

- **Why.** The user asked to drop the add-ons (the same levels in another country's streets: "boring with same gameplay
  styles") for **five cities as chapters of their own**, Florida, Madrid, New York, Mumbai and Kamakura, each with **2 to 3
  routes** from home to school and **3 to 5 levels a route**. The routes are realistic: transit (bus, tram, metro, subway,
  local train, ferry), errands for an aunt or uncle, shopping for classwork, something dropped and fetched back, and a
  mini-game instead of a routine dribble on every route longer than three levels. The user also asked for each city's own
  colour temperature and climate, ChatGPT Images prompts for one city and one level at a time, Blender with its add-ons, and
  the look and feel of a recent big-budget open-world game (four reference screenshots, kept out of the repository), with
  the filters still easy to apply.
- **Asked, not answered.** Three questions (Kamakura's 23 levels, California, how far to push the look) closed unanswered
  when the session's worker restarted, so the recommended options were taken: Kamakura keeps its 23 levels until its new
  routes are built; California leaves (below); the look goes into light, grade and baked texture, not new render passes.
- **The design: `docs/CITIES.md`.** Each city: its home, school, light and climate (season, time, the sun's and the shade's
  colour temperatures, air, weather, palette), and three routes of 3, 4 and 5 legs, every leg described (12 a city, 60 in
  all, 15 of them mini-games). The mini-games are five systems skinned per city: the ride (board, balance, get off at your
  stop; express or local, change lines), the errand (an aunt's basket from a balcony, throwing a boat's line, wrapping a
  bento, a pretzel-cart rush, sorting dabbawalas' tiffins), shopping for classwork (in each city's money), drop and come back,
  and wait-then-cross. Also: how the cinematic look is reached on the Nord CE5 and stays filter-safe, and what each city
  still needs.
- **The prompts: `docs/IMAGE_PROMPTS.md`, rewritten.** A base prompt (photoreal and cinematic in each city's own light, the
  side-scroller's straight-on camera, an empty play lane, no people, invented signs, no game's content), a block per city
  with its colour temperatures and climate, then one prompt per level (all 60), a look target per city, and sheets and
  plates in neutral light for the atlases. The Florida add-on's earlier prompts are in the history.
- **The game:**
  - **Filters** (`UI/FiltersPanel`, `Progression/Filters`) replace Add-ons & Filters on the title screen, and sit beside
    Settings in the level's, the race's and the Holiday Run's pause menus (one row shared, so no card grows), so a filter can
    be tried over the level itself. Saved as before (`SaveData.filter`).
  - **The city picker** (`UI/CityPicker`, `Progression/Cities`) after PLAY and HOLIDAY RUN: five cards. After PLAY,
    Kamakura (its 23 levels) and Florida (its 9: Home Street and the beach, unlocked by finishing Kamakura's levels, as
    before) can be chosen, and the map opens in that city. After HOLIDAY RUN only Kamakura can (no other city has a run yet).
    Madrid, New York and Mumbai show as coming soon. The chosen city is saved in `SaveData.addOn` as before (Kamakura keeps
    the id "original").
  - **California is not a city:** it left the list, and its `<scene>_CA` scenes are no longer built (`DeleteStaleScenes`
    removes them). A save that chose it plays Kamakura. Its Coast kit and builder code stay: Florida's streets share them.
  - **Co-op locations** are the cities that can be played (Kamakura, Florida): the content hash changes, so older builds
    are turned away as another version.
  - **Florida's climate** (`CityClimate`: a 5,000 K sun, 8,500 K shade, humid air, a touch of teal in the grade's shadows) is
    applied as its scenes are built (`LevelBuildKit.ThemeFor`). Kamakura's look is the reference and doesn't change.
    `review/cities/florida_climate_v122.jpg` shows Home Street before and after through the game camera.
- **Tools:** Blender 5.2.3 (`bpy`) with Pillow, its bundled add-ons turned on, and Mesa's EGL for headless EEVEE
  (`tools/blender/README.md`, "Installing Blender and its add-ons"); `tools/city_climate/run.sh` runs the game's own climate
  code and writes moods for `preview_street.py --mood-json`.
- **Cost:**
  - The build loses California's 28 `_CA` scenes (23 levels and 5 challenges): 39 level scenes instead of 67. The Coast kit's
    models that only California used leave the build with them; the ones Florida's scenes use stay, with the Coast atlas.
    The APK should shrink noticeably (B7); measure it.
  - Florida's climate and the grade tint are different values in the same shader inputs: no runtime cost.
  - The picker and the Filters screen are built only while open.
- **Checked:**
  - compile: every `#if` set against the clean tree, no new error kinds, and two planted errors were caught in every set;
    `unity_api_check` 6000.6 and 6000.7 clean;
  - the climate maths: `tools/city_climate/run.sh` runs the game's own code and passes the test's assertions;
  - the kits build, and the preview renders.
- **Not run in Unity:** the picker and the Filters screen (layout in both languages at 4:3, 16:9 and 21:9), the pause menus'
  shared row, the rebuild without `_CA` scenes, Florida's scenes in the new light (measure them against Florida's look target
  once the user has made it), and the APK size and frame rate on the phone.

## Florida's own routes: by bus, by the river, under the line (generated content v123)

- **Why.** The user asked to "implement all the levels from Florida". Since v122 a city is not a reskin of the original
  town's levels (LEARNINGS D8, the user's own rule), so Florida gets the three routes designed in `docs/CITIES.md` rather
  than `_FL` copies of chapters 2, 4 and 5. The user offered reference images from ChatGPT; the 16 Florida prompts
  (`docs/IMAGE_PROMPTS.md`: FL-0, FL1-1 to FL3-3, FL-P1 to FL-P3) were asked for, and the routes, the play and the
  mini-games were built first, as none of them needs a picture.
- **City-owned routes** (`Levels/RouteTable`): `RouteTable.Florida` (FL1 Calle Ocho Bus, FL2 The River Way, FL3 Under the
  Line), its eight stops (`FloridaStops`, `StopKind.Dock` new), Florida's own chapter (6, "Miami"), and for a route: its
  city, and where a ride takes the kid between two legs (`arrive`, `rides`). `RouteTable.All` stays Kamakura's; lookups by
  level id search `Every`; `ForCity`, `ById`, `RideBefore`, `NodeNumber` are new. Level ids are the route's and the leg's
  (`FL2-3`), never reused. `LevelDefinition` gains `city` and `isMiniGame` (and `HasStickerSlot`).
- **The cities' levels are their own:** `Cities.Has(level)` / `InTown(level)` lock another city's levels;
  `LevelUnlocks.PreviousStory` stops at a city's edge (Florida's first leg doesn't wait on Kamakura's last), and
  `NextToPlay` reads the chosen city's story only. The level table builds Florida's legs in Florida's streets and light
  (`LevelSpec.Florida`, `look`: the chapter whose street it borrows until Florida's districts exist), and no longer builds
  the original town's `_FL` copies (`DeleteStaleScenes` removes them). The Florida branches in `GreyboxLevels` are gone, so
  the original levels are exactly what Kamakura always built.
- **The twelve legs** (`Editor/FloridaLevels.cs`, set pieces in `LevelBuildKit.FloridaCity`):
  - FL1-1 Little Havana Morning: roosters and hens (`Hazards/Rooster`: a fast ball makes them flutter up out of the way, a
    slow one bounces off), a sprinkler, the domino park's tables under a pergola, a fruit stall's awning, the cafecito queue.
  - FL1-2 The Metrobus (M1, `Challenges/BusRide`): the bus pulls in; tap CARD at the reader on green, board with the ball
    before the doors shut (or the next bus comes); ride with the sway pushed onto the ball (a balance bar; KICK held keeps it
    at your feet through the hard brakes at the lights); the stop sign names each stop, tap STOP for Brickell Avenue; miss it
    and the walk back adds 15 s (`LevelManager.AddPenalty`). Stars: off with the ball, at your stop, never a wobble.
  - FL1-3 Brickell Avenue: rental scooters across the sidewalk (lying and standing), the bay wind between the towers, a
    construction gantry, the Miami River's drawbridge (6 m).
  - FL1-4 Bayfront to School: pelicans (a bigger, slower gull swoop), the fountain plaza's jets, an iguana, the crossing
    guard's crossing, Bayside Elementary.
  - FL2-1 Riverside Street: iguanas (`Hazards/Iguana`: they bolt along the path when the kid comes near), sprinklers, the
    golf cart, a mango bough.
  - FL2-2 Uncle Rey's Boat (M2, `Challenges/MooringLine`): his boat drifts and bobs off the dock; throw the line (the ball
    becomes its knot, the rope pays out from a bollard) onto both cleats with KICK's aim; tied, he hands over the science
    project. Stars: tied, in five throws, in two.
  - FL2-3 The Riverwalk: three drawbridges over the river's slips, bollards, crates, an iguana.
  - FL2-4 The Drugstore (M3, `Challenges/DrugstoreShopping`): poster board, a glue stick and markers from a shelf of eight
    things, paid in dollars and cents from a wallet (fewest pieces for the exact $6.77 is the third star), the change
    checked if you paid too much; 75 s.
  - FL2-5 Downpour to School: bursts of tropical rain (`Hazards/Downpour`, warned 1.6 s ahead) to wait out under the arcades
    (`TrackBuilder.Arcade`), flooded gutters, gusts. Out in a burst the science project gets wet; soaked, no Delivered bonus
    (`Progression/Errands`: carried from FL2-2, dropped when a trip starts again from home, 60 coins at school if dry).
  - FL3-1 The Underline: fitness stations to climb, pull-up bars to slide under, the dog run, cyclists, a ditch.
  - The people mover (`Levels/Rides`, `Core/RideCutscene`, built by `Editor/RideBuilder`): 15 s along the guideway over the
    bay, skippable; played only when the trip goes on from FL3-1 (Next), not from the map.
  - FL3-2 Biscayne Boulevard: pelicans on the lamps, the street sweeper (`TrackBuilder.Sweeper`, a moving truck to ride),
    a crossing, a boom barrier.
  - FL3-3 Museum Park to School: the banyans' roots as steps and an arch, skateboarders, a sprinkler, the kite fliers' wind.
  - Coach cards for the chickens, the iguanas, the downpour and the sweeper; stickers for the nine street legs; every
    string in English and Spanish (`Localization/StringTables.Florida.cs`).
- **Mini-games as legs** (`Challenges/MiniGameObjective`): a challenge objective with `IsRouteLeg`, so the trip runs through
  it (its time counts, the bell judges a last leg), its stars come from what it asks (`StarText`, shown in the guide and the
  results), and a failed one offers Retry, not Next. The challenge guide has tips for each (`ChallengeGuide.Kind` Ride,
  Throw, Shop).
- **Florida's map** (`tools/miami_map/miami_map.py`): its own picture and layout from one plan (the river, the bay,
  Little Havana, Brickell, downtown, Museum Park), a flat stand-in until it can be rendered from Florida's kit.
  `TownMap.Use(city)` picks a city's map; the map screen is built again when another city is chosen; a leg's node shows its
  number along its route.
- **Also city-aware:** Florida's music on its legs and a soundscape per leg (`Soundscapes.ForFloridaLeg`); the album and the
  sticker counts skip mini-game legs; co-op races run Kamakura's routes only (Florida's are not raceable yet).
- **Cost** (estimates, not measured):
  - Scenes: the 11 Florida copies (L01 to L05, C01, L11 to L14, C03) go; 12 legs and the ride scene come: two more scenes.
  - Per frame: the chickens and the iguanas are a few lines each, idle off screen or at rest (B8); the downpour toggles two
    sheets of thin rain streaks (about 300 sprites over the street, some 60 on screen, each 0.03 x 0.9 m: little overdraw)
    and rewrites its pill only on change; the mini-games run only in their own scenes.
  - Memory: Miami's map picture is 3200 x 1800 like the town's, loaded only while the map shows Florida (the town's is not).
  - Everything new is grey boxes on the shared materials: no new textures in the levels.
  - It must be checked on the Nord CE5, first FL2-5's rain and the bus's sway.
- **Checked:**
  - compile: no new error kinds in any `#if` set against the clean tree; three planted errors caught;
    `unity_api_check` 6000.6 and 6000.7 (see below);
  - logic outside Unity: the routes, stops, rides, node numbers, every Florida string in both languages, the coach cards'
    lengths, the errand and the drugstore's money (a `dotnet` harness over the game's own files); `FloridaRoutesTests`
    holds the same checks, and Miami's map layout, for Unity's test runner;
  - the coin audit (`tools/coin_audit.py`, now over both layout files): 596 coins, 0 problems;
  - Miami's map: every node and stop on its route (the generator asserts it), viewed with the routes drawn over it.
- **Not run in Unity:** building the twelve legs and the ride (LevelFeasibility runs as they are built), every new hazard
  and mini-game, the map screen for Florida, the results and guide cards for mini-games, the frame rate on the phone.
- **Next:** the reference images, then Florida's kit and each leg's own district (`docs/CITIES.md`, "Still to do for
  Florida"). (Done in v124, below.)

## Florida in Miami's own streets: a real bus, real things, a rendered map (generated content v124)

- **Why.** The user, from the phone, on v123: the bus level was "not at all understandable", "green flat objects on the
  footpath" nobody could name, and the Florida levels "naive and repeatable and redundant to Kamakura"; they should show
  "the real Florida things and aesthetics" and be "a visual feast". v123 had built Florida's legs in Kamakura chapters'
  streets with grey boxes for its own things (LEARNINGS D9).
- **The Miami kit** (`tools/blender/kit_buildings_mia.py`, `kit_buildings.py --kit Miami`, its own 4096 atlas): 41 models.
  Little Havana (the ventanita cafe window, the tabaqueria, the fruteria, mural walls, the domino park and its tables, a
  fruit cart, roosters, hens, iguanas), Brickell (glass condo and office towers and their podiums, a site fence, a coffee
  kiosk), downtown (two Deco blocks with canvas arcades over the sidewalk, a Mediterranean Revival building, the Spanish
  tower), the river and the bay (a freighter, a tug, Uncle Rey's fishing boat, bollards, coiled line, the Riverwalk's and the
  bay's rails, a cruise ship, pelicans on their pilings), the Underline (the Metrorail guideway with its mural piers,
  fitness bars), Museum Park's museum, and the trip's things (the city bus and its near side, a stop sign for route 8, the
  pharmacy and the drugstore's aisle, rental scooters lying and standing, a street sweeper). Largest: 5.5k triangles (a
  condo tower). The Plants kit gains the royal palm (3.3k) and the banyan (6.2k).
- **Each leg its own district** (`tools/blender/miami_plan.py` writes `Art/Models/Miami/MiamiDistricts.json`; the game builds
  it in `StreetBuilder.Miami`; `preview_street.py --miami <leg>` renders the same plan through the game camera): the plan
  gives each leg its ground (a street with its asphalt and kerbs, Little Havana's yards, a promenade to a seawall, a park),
  its water and land, and every model's place. Palms stand only between buildings or behind the lane (E10). A leg with a
  plan builds none of the chapters' streets, poles, hills or side-street ends; its look chapter only sets the light and the
  ground's rules: FL1-1 and FL3-1 look as the home street does (no seam into another chapter's street), FL2-3 is no longer
  the beach (its sand, tides and boulders), FL3-2 is the city's. FL2-1 keeps Florida's Home Street. The generator refuses a
  plan with anything standing in open water.
- **The Metrobus** (`LevelBuildKit.Metrobus`, `Challenges/BusRide`): the kit's 12 m bus kneels at the stop on the kid's
  left, its front door toward the kid; its near side (`BusNearMIA`: the doors, the windows, the near wheels) is taken away as
  the kid comes to the door, so the inside shows: blue seats over the wheel housings, yellow poles, the stop cord, the next-stop
  sign, the reader's light by the driver. It pulls in from the road and out into it, never through the kid. Outside, the
  plan's Calle Ocho and then Brickell (310 m, so the ride goes from one into the other once) slide past the windows with the
  stop's shelter and sign. `BusRide` gains `inward` (which side of the door the inside is), `nearSide` and `pullOutZ`.
- **No more grey boxes:** the scooters (the "green flat objects"), the roosters, hens and iguanas (their hazards unchanged),
  the domino table, the arcades (the Deco blocks: a shelter is now the model's 10 m, centred on the stretch), the sweeper,
  Uncle Rey's boat (the fishing boat, its bollard and line, Uncle Rey a cast figure) and the drugstore's aisle. Each falls back
  to its old stand-in only without the kit. Florida's stops are Miami's (`StreetBuilder.MiamiStop`: route 8's shelter and
  sign, the bayfront's coffee kiosk, the dock, the pharmacy, the Metrorail and Metromover signs, Museum Park's palms), not
  Kamakura's station, bandstand and kiosk; Florida's obstacles are bollards, hydrants and planters, not bins and crates.
- **Miami's map** is rendered in Blender from the kits (`tools/blender/miami_map_render.py`), an aerial view from the south
  at 42 degrees on `miami_map.py`'s layout (unchanged, so the routes and nodes land where they did): Little Havana's
  ranch houses under palms and live oaks with Calle Ocho's coloured shops and the 8 bus, the river and its docks, Brickell's
  towers, downtown and the Mediterranean Revival tower, the guideways, Bayfront and Museum Parks, the port with a cruise
  ship, Miami Beach's strip. `miami_map.py --flat` still draws the old picture.
- **Cost** (estimates against `docs/PERFORMANCE.md`, not measured):
  - Draws: a leg places 50 to 140 plan models (the town's levels place more), all on the Miami, Florida and Plants atlases;
    the chapters' streets, pole lines and hills are not built for them. The Metrobus's strip is about 550 models on one moving
    transform (two copies of 310 m), almost all off screen and culled; one transform moves a frame.
  - Triangles on screen: the towers are 3 to 5.5k each, a royal palm 3.3k; a Brickell shot shows about 4 towers and 6 palms.
  - Memory: the Miami atlas, 4096 x 4096 (as the Florida and Coast kits'), loaded only in Florida's legs; the map picture is
    1.1 MB as JPEG, 3200 x 1800 like the town's.
  - It must be checked on the Nord CE5: Brickell (FL1-3) and the Metrobus first.
- **Checked:** compile (no new error kinds in any `#if` set), `unity_api_check` 6000.6 and 6000.7, the coin audit (596
  coins, 0 problems), the plan's water check, `MiamiKitTests` (every model the game and the plan place is in its kit, the plan
  covers the legs, nothing on the ground in open water) checked by the same rules in Python; every leg, the bus inside and out
  and the map rendered and looked at.
- **Not run in Unity:** building the legs (LevelFeasibility), the bus ride's near side and pull-out, the kit models' facing
  in the game (the review renders use the kit's own axes), the frame rate on the phone.

## Nothing of Kamakura's in Florida (generated content v125)

- **Why.** The user: "Get even most out of Florida... make sure nothing overlaps between Kamakura and Florida." An audit of
  every track piece Florida's layouts call found the original town's looks still built by chapter in Florida's legs
  (LEARNINGS D10).
- **Florida's own play pieces** (`tools/blender/kit_buildings_mia_play.py`, 20 more Miami kit models; `TrackBuilder.MiamiLook`):
  - The slide-unders a Florida leg uses, each with its look's own solid and play (`<Look>MIA`): a Cuban fruit stand under a
    striped awning (FL1-1), a sidewalk shed under a building site (FL1-3), a fishing boat on its stands (FL1-4, FL2-3), a mango
    bough (FL2-1), a mural-painted roll shutter (FL2-5), the Underline's gym rig (FL3-1), a garage boom gate (FL3-2), a
    banyan's roots (FL3-3).
  - A work zone's barricades and drums at the pits, crates of mangoes, the US walk signal (hand over walking man, the SW 8 ST
    blade) with Miami's pickups, SUVs and vans in Florida paint at the crossings, white-and-teal signboards, Art Deco checkpoint
    poles, the bayfront's splash fountain, coral keystone ledges, the road's shade from live oaks and royal palms.
  - The Animals kit's brown pelican (the gull's rig, 1.4 m) for the pelicans.
  - Walkers in Miami's summer clothes; people at every Florida stop (an abuelo waiting for the 8, a commuter, the coffee window's
    lady, a neighbour fishing off the dock, a jogger, a painter).
- **The plan:** Riverside Street (FL2-1) is now a district (ranch houses, cottages, live oaks, mailboxes on posts, the river's
  freighter and crane beyond); white ibises on the lawns; forecourts on Brickell and Biscayne (royal palms, benches, coffee
  kiosks, fruit carts, scooters) and Biscayne's kerb; a Miami tower crane (`CraneMIA`); only Florida's own trees.
- **The people mover's ride** (`RideBuilder`): the Metromover's car on the kit's guideway, the bayfront's balustrade, royal palms
  and banyans, a cruise ship, a freighter, a tug and Brickell's towers.
- **The school** reads Bayside Elementary on its marquee and wall (the Florida kit, repainted). The map drops the shared trees
  and the town's hatchbacks, and gains Brickell's cranes.
- **Miami's soundscapes** (`Audio/AmbienceGenerator`, `Soundscape`: Havana, MiamiRiver, Bay, Downtown, Underline, MuseumPark,
  appended so Kamakura's keep their numbers): a cafe radio's son through a wall, roosters, hens and dominoes; the river's
  seawall slaps, outboards, a tug's horn, the drawbridge's bell, halyards and laughing gulls; the bay's chop, palm rattle, a
  cruise ship's horn and pelicans diving; downtown's traffic, AC hum, bus brakes, crane beeps and flocks of parrots; the
  Metrorail overhead, bicycle bells and cicadas; Museum Park's mockingbirds, grackles and sprinklers. Their levels sit with
  Kamakura's (beds 0.037 to 0.05; no cue louder than the existing loudest; no hiss: LEARNINGS G2). Music by place
  (`Soundscapes.MusicOf`) keeps ten legs' music; FL2-1 now plays the Beach's soca and FL1-3 the Street's son.
- **Tests** (`MiamiKitTests`): the plan places only Florida's own models; every slide-under look in `FloridaLevels` has its
  Miami model; every Florida stop has its Miami set piece; the pelican is in the Animals kit; no Florida leg plays a Kamakura
  soundscape. `tools/audio_hash/expected.txt`: the 102 existing clips unchanged, 57 new.
- **Cost** (estimates, not measured): the new models are 0.2k to 3.5k triangles (the crane about 3k, far off); a leg places
  some 10 to 30 more plan models (ibises, forecourts); the ride scene's kit models replace its boxes. Each Miami soundscape
  takes about 0.45 to 0.9 s and 53 to 75 MB to generate on the desktop, as Kamakura's do (Havana the heaviest, as Market is).
  Check on the Nord CE5: FL1-1's soundscape generation and FL1-3.
- **Checked:** compile (no new error kinds in any `#if` set), `unity_api_check` 6000.7, the coin audit, the plan's checks and
  the new tests' rules in Python, the audio harness (no NaN, levels), review renders of every new model and of the legs with
  their new pieces.
- **Not run in Unity:** building the legs and the ride, the new pieces' facing and solids in play, the stops' people, hearing the
  soundscapes, the frame rate on the phone.

## Kamakura as Kamakura: its own homes, shops, temples, tram, trees and birds (generated content v126)

- **Why.** The user: "update the Kamakura assets appropriately and realistically wrt houses, animals, trees, objects and
  other assets", with a brief for the city (`docs/KAMAKURA_BRIEF.md`, kept word for word). The original town was built from
  shared kits that read as no city in particular: picket fences, post boxes and garages, a bodega, Victorian lamps, spruce
  forests, palms and gulls (LEARNINGS D11).
- **Homes** (`Kamakura` kit, `kit_buildings_kmhouse.py`): two-storey timber-and-mortar houses with kawara or standing-seam roofs,
  aluminium sliders with screens, futon rails, sliding entrance doors, name plates, AC units, gas meters and pipes
  (HouseTileKM, HouseMetalKM, HouseOldKM, HouseShedKM, HouseCarportKM with a kei car under it, BungalowKM, ApartmentKM);
  block walls, dark board fences and gates in front of them; plant shelves, laundry poles, corrugated sheds, hydrangeas and
  azaleas in the front gardens. No picket fences, post boxes or garages in Kamakura.
- **Shops** (`kit_buildings_kmshop.py`): low shopfronts with noren, wooden signboards, lanterns and tables of goods, each with an
  invented, correctly written name: 汐見堂 (sembei), そば処 小波, 若葉庵 (wagashi), 鎌倉みやげ すずなり, 鮮魚 かもめ屋, 純喫茶 灯台,
  日本茶 緑風園; nobori banners, vending machines with invented drinks, a green phone, scooters and bicycles out front.
- **Temples, street and tram** (`KamakuraStreet` kit, `kit_buildings_kamst.py`): a vermilion torii (若潮神社), a timber temple
  gate with a heavy tiled roof, a shrine hall, stone lanterns and steps, moss-covered stone walls and an ema rack, set as a
  temple ground in the park (`KamakuraTempleGrounds`); the two-car green-and-cream tram on its single track, with its wire
  poles and a level crossing (black-and-yellow bar, red lamps) on the site's street; kei trucks and cars, a scooter and a
  rickshaw. Also modelled: convex mirrors, a bus-stop pole, tactile strips and decorated manholes (not yet placed).
- **Lanes:** no raised kerb in Kamakura's home street: a flush lane, a white edge line and the green walking strip.
- **Trees and birds:** black pines (on the beach in place of palms), camphor, cedar, cherry in full leaf, bamboo, hydrangea,
  azalea and persimmon (Plants kit; existing models untouched); black kites over the coast and crows on the roofs (Animals
  kit, the gull's and the pigeon's rigs). Kamakura's far hills are rolling layers in the sea haze, no spruce band.
- **Florida:** the US walk signal's lamps now light (its attach points were named `Attach.Attach.Red`: LEARNINGS A16).
- **Tests** (`KamakuraKitTests`): every model name `StreetBuilder.Kamakura` uses is in its kit; both kits are in
  `LevelBuildKit.Kits`; the kite has its wings and the crow its head.
- **Cost** (estimates, not measured): two more 4096 atlases loaded in Kamakura's scenes (about 9 to 11 MB each with mips once
  compressed for the phone, as Miami's); 15 MB + 5.6 MB of FBX in the project. Houses and shops are 2.1k to 6k triangles
  (median 2.8k), close to the shared kit's they replace; the street pieces 0.2k to 5.9k (median 1k; the shrine hall and the tram
  the heaviest, one each in a level); the temple ground adds about 15 to 25 models in the park, the tram line a track row and a
  pole every 30 m. Check on the Nord CE5: the park's first temple ground and chapter 4 with the tram.
- **Checked:** compile (no new error kinds in any `#if` set), `unity_api_check` 6000.6 and 6000.7, the coin audit (596 coins,
  no problems; no layout changed), the new tests' rules in Python, review sheets of every new model, and all five chapters
  through the game camera before and after (`preview_street.py --kamakura`; `review/kamakura/`).
- **Not run in Unity:** building the levels with the new kits, the models' facing and the green strip in the engine, the tram's
  and crossing's placement in play, the frame rate on the phone.
- **Still to do:** a Kamakura lifeguard tower for the beach (the shared one is still there), the site's warehouses, the
  remaining Victorian park lamps, placing mirrors, bus poles, manholes and tactile strips; the black pine could lean more.

## The Kamakura audit (generated content v127)

- **Why.** The user: "Run an audit across all levels in Kamakura city". Written up in `docs/KAMAKURA_AUDIT.md`: every track piece
  each of the 23 levels and 5 challenges calls, the streets, the stops, home and school, the people, animals, sounds and words,
  against `docs/KAMAKURA_BRIEF.md`, with a per-level list and the fixes ranked.
- **Found:** v126 reached the streets but not the play. Only the swooping bird has a Kamakura branch among the track pieces.
  The stops (St Mary's, the bus shelter, the brick station, the bandstand, the allotments), the kid's picket-fenced home and
  the brick school have none. The walkers, the English town's birdsong and church bell, "Seagull Bay" and every English board
  are the shared town's. Six Kamakura street models (rickshaw, kei truck, convex mirror, manhole, tactile strip, bus-stop pole)
  are never placed.
- **Fixed now:** the home street's road lines, drains and manholes sat 14 cm under Kamakura's flush road (LEARNINGS E13).
- **Cost:** none (the markings move up 14 cm).
- **Checked:** compile (no new error kinds), `unity_api_check` 6000.7. Not run in Unity.

## No mini-games (generated content v128)

- **Why.** The user: "remove the mini games completely and do not replace them with anything else in both Kamakura and
  Florida." (LEARNINGS E14; a standing preference now.)
- **Florida:**
  - Its three mini-game legs are gone: FL1-2 The Metrobus, FL2-2 Uncle Rey's Boat and FL2-4 The Drugstore. Each route is now
    three dribbles: FL1 Little Havana Morning, Brickell Avenue and Bayfront to School (the bus between Calle Ocho and Brickell
    is not shown; FL1-2 starts at the Brickell stop); FL2 Riverside Street, The Riverwalk and Downpour to School.
  - The legs after them took their numbers: FL1-3 is now FL1-2, FL1-4 FL1-3, FL2-3 FL2-2, FL2-5 FL2-3. Their scenes, strings,
    stickers, soundscapes, plan districts and map nodes moved with them. Each district is seeded by its old id, so every street
    is the one reviewed in v125 (checked: identical).
  - Save version 3 (`Progression/FloridaLegs`) moves an older save's records, stickers and trip times onto the new numbers
    and drops the removed legs' records.
- **Removed with them:**
  - The code: `Challenges/MiniGameObjective`, `BusRide`, `MooringLine`, `DrugstoreShopping`, and the route-leg path through
    `LevelManager` (`IsRouteLeg`, `CompleteLeg`, `AddPenalty`).
  - The HUD's and the guide's mini-game star lines and Ride, Throw and Shop tips, and the level definition's `isMiniGame`.
  - The errand they handed over: `Progression/Errands`, the science project, its Delivered badge and coins, and the save's
    `carrying` fields.
  - The downpour's stake: it now only warns and sends the kid for cover.
  - The track builder's `AfterRig`, and the Metrobus's moving street strip (`MiamiStreetStrip`) with the plan's bus, dock and
    interior districts.
  - Two kit models: the bus's cut-away near side and the drugstore's aisle, with their tiles in the kit source. The full bus
    and the fishing boat stay: the map's picture uses them.
  - Every mini-game string in both languages. The chapter's subtitle is now "Calle Ocho, the river and the bay".
  - Nothing replaces any of it.
- **Kamakura:** its two designed mini-games (KM1-2 Ride the Enoden, KM2-3 Grandma's Whitebait Shop) are out of its routes in
  `docs/CITIES.md` and their reference prompts are out of `docs/IMAGE_PROMPTS.md`. The legs after them are renumbered there,
  and the Kite Thief's rice ball is now the kid's own lunch. No Kamakura level in the game had a mini-game.
- **Not changed:** the people mover's ride between FL3's legs (a scene that plays by itself, not a mini-game), Kamakura's
  five skill challenges, and Madrid's, New York's and Mumbai's designs (still with their mini-games, pending the user).
- **Tests** (`FloridaRoutesTests`):
  - three routes of three legs, every leg a dribble from its stop;
  - the legs meet at their stops;
  - `TheMiniGamesAreGoneForGood`: no mini-game type, errand or string comes back;
  - the save upgrade.
  `MiamiKitTests` list the nine legs.
- **Cost:** it saves. Three fewer level scenes, the heaviest among them (the bus's strip was about 550 models on one moving
  root); 1,660 fewer lines of scripts; two FBX (72 KB) out of the project. The atlas keeps the two models' tiles until the
  Miami kit is next rebuilt.
- **Checked:**
  - compile: no new error kinds in any `#if` set;
  - `unity_api_check` 6000.6 and 6000.7;
  - the coin audit: 590 coins, no problems; 6 fewer, the bus's and the boat's;
  - the route, string, plan, map and kit rules of the changed tests, in Python;
  - the upgrade's expected values, by hand.
- **Not run in Unity:** rebuilding the levels (the generated content's version is 128, so it rebuilds on open and deletes the
  three old scenes and the renamed ones' old copies), the save upgrade on a real save, the map screen.

## The phone's Florida levels: stale builds stopped, gates, rain, birds, kerbs, puddles (generated content v129)

- **Why.** The user's screenshots of Downpour to School and The Riverwalk: "Lots of issues wrt gates, rain and everything. Run
  an audit and fix all the issues." (LEARNINGS A17, E15.)
- **First finding: the phone ran old levels.** "Project: soaked" (removed in v128), the market's English shops, Kamakura's park
  trees and a red slab for an arcade are the v123 streets. The generated levels were rebuilt only on an editor session's first
  script load, so a pull with Unity open never rebuilt them, and nothing stopped a build shipping them. Now:
  - `GeneratedContent.AutoBuild` rebuilds when the code's version is newer, on any script load.
  - `BuildScripts` rebuilds stale levels first.
  - `GeneratedContentBuildCheck` fails any other player build while the levels are out of date.
  - A Florida leg that can't find its Miami district logs an error and keeps the levels out of date.
- **Gates** (`LevelBuildKit.Drawbridge`, `Hazards/Drawbridge`):
  - The arms fall across the path toward the camera, ending at the lane's front edge, instead of along the street behind the kid.
  - While an arm is down, a one-way blocker at its post (2.4 m back from the hinge) stops the kid and the ball coming toward
    the water. It never shuts in a kid already over.
  - The right-hand leaf is mirrored, not turned round: turned, its railing stood in front of the lane on every drawbridge.
  - The coach says to wait at the gate.
- **Rain** (`World/RainCurtain`, `Hazards/Downpour`):
  - Streaks fall round the camera, slanted by the wind, splashing on the paving and rippling the puddles, with none under the
    arcades. It is one mesh, steady between bursts and heavy in them, replacing still streaks that hung in the air.
  - The light greys and the shadows soften as a burst comes (`WorldLook`).
  - Out in a burst, the kid runs at 80%: the shelters matter again.
  - The warning pill sits under the HUD card instead of across it.
- **Birds:** startled pigeons and the pigeon and crow flocks fly on the black kite's rig painted all over (on the gull's they
  flew as white gulls). Kamakura's beach flocks are kites.
- **Florida's low kerbs** (six levels) are raised planting beds, not bare grey blocks.
- **Puddles** (every city) mirror the street: deep slate water, a sky band on the far side, a soft wet edge.
- **Cost** (estimates, not measured):
  - The rain is one draw call of up to about 2,100 vertices rewritten each frame (about 0.1 ms on the CPU) and thin alpha
    streaks (little overdraw).
  - The storm light rewrites a dozen shader globals while it changes.
  - The gates' blockers are two colliders per bridge.
  - Check on the Nord CE5: Downpour to School in a burst.
- **Checked:**
  - compile (no new error kinds in any `#if` set);
  - `unity_api_check` 6000.6 and 6000.7;
  - the coin audit;
  - the drawbridge through the game camera with its leaves down and up (`preview_street.py --miami FL2-2 --canal 20:25
    --lift 70`).
- **Not run in Unity:** the rain, the storm light and the gates in play, the build check, the phone. Rebuild the levels in
  Unity (it now does so by itself when it sees v129) and build again.

## No brown blocks, no stranded balls, Florida's streets made to stick (generated content v130)

- **Why.** The user, with screenshots and a recording: "what are those brown blocks? Are they any placeholder?"; at the bridge
  "the red light is just somewhere at random place"; "why the green tails in Kamakura?"; the ball "penetrates through the
  sheds" or "stays on top of the sheds and have to restart the level": "show alert that ball cannot be retrieved and restart
  from last checkpoint". Across all the levels. (LEARNINGS A18, E16.)
- **Florida's streets:** the recording showed every Florida leg still on Kamakura's streets after v129, while v129's check
  passed.
  - The builder now records each leg whose Miami district it really built; any leg missing from that record fails the
    rebuild of the levels with a dialog, and the build check refuses them.
  - The plan is read from the project folder, again whenever it changes.
  - The fallback's error names the missing input.
  - *Rebuild the levels in Unity. If the dialog appears, the Console's first error says which part was missing.*
- **Platforms and ramps** (`LevelBuildKit.Dressing`; 32 uses across both cities):
  - Platforms are retaining walls with their coping. In a park: a lawn bed with shrubs along its back (Kamakura's granite,
    Miami's coral keystone). In a street: a paved terrace. On a site: concrete with a safety edge.
  - Ramps are solid wedges under their slope.
  - The colliders are unchanged.
- **Stranded balls:**
  - Kamakura's market awnings (L06 to L10) are striped canopies on two poles (it was a red box), in the city's colours, and a
    ball on one goes back to the checkpoint (`BallTrap`).
  - Miami's arcade canopies stop the ball from below and shed it from above (a low ridge).
  - Anywhere else, a ball resting more than 2.4 m above the feet of a kid standing near it for 3.5 s gives the alert "The
    ball can't be reached - back to the checkpoint" and the run goes back to the last checkpoint (`LevelManager.BallOutOfReach`).
- **The drawbridge's lamps:** a black two-lamp signal head on a mast before each gate, dark red lenses that light in turn.
  They were loose discs on the tower wall.
- **Kamakura's green strip** (expected: the green walking strip painted along Japanese lanes) is now green paint on the
  asphalt, about 1.5 m wide, not 2.5 m of green paving slabs that read as tiles.
- **Cost:**
  - A platform is 3 to 4 boxes and a few small shrubs in parks, about 2 to 3k triangles at most.
  - A ramp is two small meshes.
  - An awning is about 20 boxes, less than 1k triangles.
  - The reach check is a few comparisons a frame.
- **Checked:**
  - compile (no new error kinds in any `#if` set);
  - `unity_api_check` 6000.6 and 6000.7;
  - the coin audit;
  - the drawbridge's signals through the game camera (`preview_street.py --canal`).
- **Not run in Unity:** the new looks in the game, the canopies' and awnings' physics with the real ball, the reach check's
  timing, the phone.

## Florida in its own streets at last (generated content v131)

- **Why.** v130's check stopped the build, and its error said why: "level id=(none)". `LevelBuildKit.BuildScene` read the level's
  id after making the new scene, which unloads the level's definition, so it was always empty. No Florida leg ever found its
  Miami district: every one was built on a Kamakura street from v124 on, while the Blender previews showed the districts
  (LEARNINGS A19).
- **Fixed:**
  - The id is read before the new scene; a test holds it.
  - Miami's arcade canopies are raised to 3.4 m, clear of a double jump's head (LevelFeasibility flagged five in Downpour to
    School).
  - The feasibility check counts a step up from one platform to the next (Museum Park's 1.9 m platform after the 1.0 m one).
- **Also seen:** Unity's "Input Manager is marked for deprecation" warning lasts until the editor restarts after
  `EditorTools/InputHandling` switches the project to the Input System (it offers to restart).
- **Checked:** compile (no new error kinds), `unity_api_check` 6000.6 and 6000.7, the coin audit.
- **Not run in Unity:** the Miami districts in a built scene for the first time. They were previewed in Blender from the same
  plan; look at each Florida leg once.

## Florida's new music, and only two cities (v132; no generated content changes)

- **Florida's music, redone ("it looks sad").** The user asked for music inspired by Justice and Tame Impala. Every one of
  Florida's seven loops is new and original (`Audio/MusicGenerator.FloridaStyleOf`):
  - **French electro, filter house** on Home Street (122 BPM, D Mixolydian), the market (118, E Dorian disco-funk), the
    beach (124, A major, with a choir of "ooh"s) and the building site (126, G major, the hardest). Four on the floor with a
    punchy kick that pumps the whole mix (a deep sidechain duck), a growling overdriven saw bass on rolling octaves, chopped
    disco chord stabs whose resonant filter opens over the first half, pumping quaver chords, a gliding saw lead, crunchy
    snares, claps, the open hat on every off-beat and a snare roll into each half.
  - **Psychedelic synth-pop** for the menu (112, E major sevenths), the park (114, D major) and the underpass (116, D Dorian
    night groove). A lush pad through a four-stage phaser sweeping every two bars, a fuzzy melodic bass, big squashed
    laid-back drums with a tambourine and rolling tom fills, a dreamy hollow lead, tape wobble and a long reverb.
  - New in `Audio/Instruments` (band-limited PolyBLEP oscillators): `SawStab`, `PhaserPad`, `SawLead`, `PsychLead`,
    `ElectroBass`, `FuzzBass`, `PunchKick`, `CrunchSnare` and `Tom`. A style's pump, master drive, tape wow and dance rhythms
    are now its own settings; their defaults are the old fixed values, so Kamakura's and California's music is unchanged,
    sample for sample (`tools/audio_hash`: only Florida's 13 music lines changed).
  - MP3 previews of all seven went to the user. LEARNINGS G3.
- **Cost** (`docs/PERFORMANCE.md`; desktop .NET 8, per loop): 362 to 512 ms and 38 to 43 MB of garbage to make, against 355 to
  585 ms and 38 to 56 MB for the old Florida loops; same loop length and memory once made. No frame-time cost: it is made on
  the worker thread as before.
- **Madrid, New York and Mumbai removed** (the user's request). `Progression/Cities.All` is Kamakura and Florida. Their
  names and lines are gone from both languages, and the city picker sizes itself to its rows. A save that chose one of them
  plays Kamakura (as California's does), and a test holds that. Their designs and ChatGPT prompts are out of
  `docs/CITIES.md` and `docs/IMAGE_PROMPTS.md`, and the mini-game systems with them (M1 to M3; no city has mini-games). The
  prompts page generator and the climate harness list the two cities. Florida's picker line now reads "Three ways to school
  through Miami".
- **Checked:**
  - `tools/audio_hash`: only Florida's music changed; new `expected.txt`.
  - Loudness and peaks per loop: RMS 0.136 to 0.140 (the target), peaks under 0.52.
  - Spectrograms: the pump and the glides as meant, aliasing below -80 dB.
  - `tools/city_climate` and `tools/prompts_page`.
  - Compile: no new error kinds.
  - `unity_api_check` 6000.6 and 6000.7.
- **Not heard on the phone yet:** play a Florida leg and the menu once with the default volumes, against the Miami beds.

## No canopy over the ball, and Florida's tunes written (generated content v133)

- **Why.** The user's recording of Biscayne Boulevard (FL3-2): the ball kicked up went through a shop's teal canopy and fell
  back through it, after v130's fix. And "still the BG music is bad for Florida. The background beats are good enough."
  (LEARNINGS E17, G4.)
- **The canopy.** It was the Miami district's Deco block ("Flagler Shoes"), placed as scenery with its 3 m canvas arcade
  hanging 0.7 m in front of the ball's plane and no collider (only the level's own arcades had one, v130).
  - Nothing that stands behind the lane may now reach over the ball. `StreetBuilder.Model` places every street model in both
    cities, and `tools/blender/miami_plan.py` writes the Miami plan. Both push such a model back until its front is 0.45 m
    behind the ball (`StreetBuilder.ClearOfTheBall`), and the Unity console says what moved.
  - The district's three Deco arcades (Biscayne Boulevard twice, downtown once) now stand at 3.5 m instead of 2.35 m. The
    street lamps moved back 13 cm, and nothing else in the plan changed (diffed).
  - Kamakura's streets: the shops and homes, the original town's buildings, the parasols and the site's machines all keep at
    least 0.65 m behind the ball, so the rule moves nothing there; it guards against the next one.
  - A test runs the rule over the whole plan.
  - Checked from the game camera (`preview_street.py`, FL3-2 at x 29, with a crate in the ball's plane at 2.9 m): before, the
    canvas hid the crate; after, the crate is in front of it.
- **Florida's tunes.** The drums and bass are as they were. Everything melodic is new:
  - Each loop is two four-bar chord cycles under two written hooks, in place of v132's random tunes: a bouncing riff down
    D - A/C# - Bm7 - G on Home Street, octave chops on F major's I and ii-V in the market, a beach anthem in A, a stabbing
    repeated-note riff on the site, dreamy lines on the menu's E major sevenths, a riff rocking Cmaj7 - Fmaj7 in the park,
    a laid-back climb in F under the underpass.
  - The synths hold their pitch: a glide only between tied notes, no vibrato on the electro lead, no tape wow. A new bright
    synth pluck plays the riffs. The chord stabs are less resonant and less driven, their filter opening from 1.6 kHz.
  - `tools/music_hooks/check.py` reads the hooks from the code and fails if a note on a strong beat is off its chord, or out
    of range. All seven pass, and a planted wrong note fails it.
  - MP3 previews of all seven went to the user. Only Florida's 13 music lines changed in `tools/audio_hash`.
- **Cost:**
  - Music: 360 to 457 ms and 38 to 43 MB to make each loop, as v132.
  - Canopies: no new objects; three models stand further back.
- **Checked:**
  - `tools/audio_hash` and `tools/music_hooks/check.py`;
  - loudness and peaks (RMS 0.135 to 0.141, peaks under 0.51);
  - the hook's pitches in a spectrogram (steady, as written);
  - the Miami plan diff and the before-and-after render;
  - compile (no new error kinds);
  - `unity_api_check` 6000.6 and 6000.7.
- **Not run in Unity:** the rebuilt FL3-2 and FL2-3 with the ball, and the new tunes on the phone.

## The sketch in black and white, the cartoon in natural colour (v134; no generated content changes)

- **Why.** The user, with a screenshot of Biscayne Boulevard in the classic cartoon filter: "Make the sketch filter completely
  black and white. The cartoon filter has yellow/orange tint. Instead make the colors more natural." (And: "Now the music is
  good for Florida.") LEARNINGS D12.
- **The pencil sketch** (`Shaders/PostFX.shader` pass 6, `World/PostFX`):
  - Black and white only: white paper, a grey wash of the tone (a little deeper on the kids and the ball, so the kid stands
    out), neutral graphite.
  - The pass returns grey whatever paper and graphite colours a scene saved.
  - The comic words drawn with it (`UI/ComicPops`) are grey too: the lettering's wash, the star's wash and the graphite.
  - Its line in Filters reads "Black-and-white pencil lines and hatching".
- **The classic cartoon** (`World/ClassicLook`, which the camera's passes and the menus' pictures share):
  - The scenery keeps its own hues. Warm colours are no longer pushed toward orange, shadows no longer browned, and beige and
    sand no longer lifted to ochre and gold (vibrance 1.8 to 0.35, saturation 1.35 to 1.1).
  - The outline is a neutral black, and the sky a natural blue instead of turquoise.
  - The calmer setting follows.
  - The cels, the strokes, the brush and the crisp detail are unchanged.
- **Previews** through the filters' Python ports, on Blender renders of the home street and the beach:
  `review/cartoon/7_natural_colour_v134.jpg` and `review/sketch/6_black_and_white_v134.jpg` (before on the left).
  - The ports (`classic_port.py`, `sketch_port.py`) carry the new values.
  - The new sketch has no colour in any pixel.
- **Tests:** `FilterLookTests` checks that the cartoon has no warm push, neutral ink and a blue sky, and that the sketch has
  neutral paper and graphite and a pass that returns grey.
- **Cost:** none. The same passes with different numbers; the sketch adds three dot products a pixel.
- **Not run in Unity:** the shader change has not been compiled here (no Unity). Look at a street in each filter once on
  the phone.

## Both cities open, Florida first (v135; no generated content changes)

- **Why.** The user: "by default make both Florida and Kamakura cities open for play. Put Florida first and then Kamakura."
- `Progression/Cities`: Florida no longer waits for every Kamakura level (`needsEveryLevel` off), and `Cities.All` (the
  picker's order) is Florida, then Kamakura.
  - Florida's first leg of each route was already open on its own (`LevelUnlocks.PreviousStory` stops at a city's edge).
  - The store's chapter paywall is off (`Monetization.RequireUnlock`). If it is ever turned on, Florida's chapter 6 would
    sit behind the Full Game purchase.
- **Unchanged:**
  - A new player with no saved choice still has Kamakura selected until they pick (`Cities.Selected`). The picker asks on
    every PLAY.
  - The Holiday Run is Kamakura's only, and co-op races run Kamakura's routes.
  - Co-op's location list (cities on Kamakura's routes) is the same on every phone.
- **Tests:** the picker's order, and both cities open from the start (`GameLogicTests`).
- **Cost:** none.

## The ball meets what it sees, in every level (generated content v136)

- **Why.** The user's recording of Biscayne Boulevard (FL3-2): a ball chipped onto the street sweeper's back rolled into its
  cab and out through its front. "Run a strict audit for this pass-through issue across all levels and cities and fix the
  issue effectively." (LEARNINGS E18.)
- **The cause.** The sweeper's collider was the part the kid rides: a box from 0.3 m to its flat back at 1.2 m. The kit's
  truck is 2.43 m tall with its cab over the front. Every play piece is built that way, a hand-drawn collider for the kid's
  play under the kit's model, and nothing compared the two.
- **The audit.** `tools/ball_solidity/silhouette.py` (Blender) measures every model a level piece places, set as the piece
  sets it, where its surfaces cross the ball's plane (|z| <= 0.17 m: the ball's radius and a margin), on a 4 cm grid.
  - 69 models were measured: vehicles, slide-unders, obstacles, crates, signs, the crane, the hoist, the raft, the gates, the
    swing, fountains, targets, the school arches, the bollards.
  - Beyond their colliders: the sweeper's cab; the golf cart's body; the domino table's stools; the arcade canopies'
    thickness; a standing scooter's handlebar; the crane load's beams and hook; the posts above the slide-unders' gaps; the
    tunnel lamps; the hanging "SCHOOL" banner.
  - Already clear of the plane: the signs (planted at z 1.55), the checkpoint flags (z 1.35), the drawbridge gates' posts
    and raised arms (z 1.8), the slalom poles (z +-0.9), the stops' dressing, the street's dressing (E17).
- **The fix, every level, both cities** (`LevelBuildKit.BallShells`, run at the end of every level's build):
  - Each mesh's triangles are clipped to the ball's plane and drawn onto a 5 cm grid (`BallShellGeometry`).
  - Where a surface is not already on a collider (within 6 cm), thin box colliders are added for the ball only
    (`World/BallShell` ignores the kid's colliders, again after each slide, as pedestrians do). No jump, slide, ride or
    feasibility check changes.
  - Merged into as few boxes as the shape allows: 14 for the sweeper in the offline check.
  - They go on the piece's moving body when it has one: the sweeper's cab rides with it, and a drawbridge leaf's turn with it.
  - Left alone:
    - pickups and zones (a trigger is their only collider);
    - animals, plants, people, water and rain, the street's slabs;
    - a surface lying under 12 cm above a collider (a lip the ball rolls over);
    - anything that moves without a body of its own (a crossing's bars, the crane's trolley);
    - the builder's own decoration with no collider, unless it is a kit model.
  - Each level's build logs the pieces it shelled and anything it left out. That is the audit's record in the Console, every
    rebuild.
  - Offline check with the sweeper's real mesh, its box and the ground, by the same rules: the cab's outline (front, roof
    and back, 1.2 to 2.43 m) and the brush under it get shells; nothing that was already solid gets one.
- **Tests:** `BallShellTests` covers the slab clipping, an edge-on surface still marking its line, the merged boxes covering
  exactly their cells, and every level's build ending with the shells (ball only). The geometry also ran outside Unity
  against stand-ins: all its checks passed.
- **Cost** (`docs/PERFORMANCE.md`):
  - Static thin boxes, only where a surface lacked a collider (tens to a few hundred a level, see the Console).
  - On a moving piece, a few more shapes on its body.
  - No new renderers. Box2D's broadphase handles static boxes cheaply.
  - Build time: one pass over the meshes in the ball's plane.
- **Not run in Unity:** the pass itself (2D physics queries in the editor), the shells with the real ball, and the phone.
  Rebuild the levels and read each level's "ball shells" line in the Console. Then chip the ball onto the sweeper on
  Biscayne Boulevard: it should stop at the cab.

## The game is Kick Off 2 School (v137; no generated content changes)

- **Why.** The user: "Rename the game to Kick Off 2 School".
- **Everywhere players see it:**
  - The built app's name (`BuildScripts.ProductName`), so the home screen, Settings > Apps and the stores read "Kick Off 2
    School".
  - The title (`menu.title`) and the credits' version line (`KickOffLogo.GameName`).
  - The Bluetooth permission prompts (Android's in-game line, iOS's usage strings, both languages) and the iOS privacy
    manifest.
  - The support and privacy pages (`site/`), the store listings, the privacy policy and the release guide.
- **The logo:** the "Kick OFF 2" lettering is the user's banner artwork, so it is unchanged. The slanted navy ribbon under it
  now reads **S C H O O L** (`KickOffLogo.RibbonWord`, a brand, the same in Spanish) where it had the tagline "Dribble all
  the way to school". So the logo reads "Kick Off 2 School", at the same size: the title screen, splash and credits lay out
  as before.
- **Unchanged on purpose:**
  - The app ID `com.astradite.kickoff2`: fixed once uploaded, and phones keep their saves under it.
  - The company, Astradite.
  - The code's namespace.
  - The history in PROGRESS and LEARNINGS.
- **Still the old name in pictures:**
  - The app icon and the store banner and key art carry the "Kick OFF 2" lettering, from the user's artwork.
  - New artwork with "School" in it would replace them (and `Resources/UI/KickOffLogo.png`, through
    `tools/logo_from_banner.py`).
  - In the editor (not on phones), a build's new product name moves `persistentDataPath`, so the editor's own test save
    starts fresh.
- **Cost:** none.

## Florida's music: longer, softer, quieter; nothing tuned under it (v138; no generated content changes)

- **Why.** "Still the background continuous music is bad in Florida." Asked what was wrong (too repetitive, a place's tune,
  the sound, too loud), the user answered all of them. (LEARNINGS G5.)
- **Longer, and it changes** (`MusicGenerator.ArrangeFlorida`): every Florida loop is 32 bars, 61 to 69 s (was 31 s), in
  four sections:
  1. an opening (chords, bass, a light groove, the first hook once, four bars to breathe);
  2. the groove (the full kit, the second comp, the first hook twice);
  3. the lift (the second chord cycle and hook);
  4. a breakdown (the kick out, the bass holding, the first hook an octave down on a Rhodes), building back with a fill
     into the loop's start.
- **Softer:**
  - Rhodes chords in place of the saw stabs on the busy streets (the stabs remain only on the site, softened).
  - The saw lead is gone: soft plucks, a warm hollow lead, vibes.
  - Rounder bass, a less squashed snare, a darker phased pad.
  - The pump is about half as deep. The hats, open hats and claps are softer, and the shaker and tambourine come in only
    in the full sections.
  - Master drive 0.08 to 0.12 (was up to 0.24), tone 6.5 to 7.5 kHz (was up to 9.5).
- **Quieter:** Florida's loops are mixed to an RMS of 0.11 to 0.115, against 0.14 for the other countries' music.
- **Nothing tuned under the music:**
  - Little Havana's bed (FL1-1, now the first level played) had a cafe radio playing a son in another key all the way
    through. It is gone.
  - Downtown's air conditioners (FL1-2, FL2-3, FL3-2) keep their fan but lose a 120 Hz hum chord that was half a semitone
    off the music's notes.
- **Checked:**
  - `tools/audio_hash`: only Florida's music and those two beds changed.
  - `tools/music_hooks/check.py`: the hooks still fit their chords.
  - The sections show in the spectrogram as planned.
  - Previews of four legs as heard in game (music and bed at the default volumes) went to the user.
- **Cost** (desktop .NET 8, per Florida place, once a session):
  - 0.8 to 1.6 s of worker time and 81 to 91 MB of garbage to make a loop (was 0.4 to 0.5 s and 38 to 43 MB). It is made
    off the main thread as the place is entered, while the last music plays on.
  - On the phone the new loop may come in a few seconds after a level starts, the first time each place is entered.
  - A clip now holds about 11 MB (was about 5.7).
  - Baking the music offline (`docs/PERFORMANCE.md`, "Still to do" 1) would remove all of it.
- **Not heard on the phone yet.**

## Side streets clear, nothing hanging in the air, Florida's music on a new band (generated content v139)

- **Why.** The user's screenshots: "In Florida the road crossings are positioned in wrong places. At one place they are
  coming from building and shop. Another place the road is from the ocean and the load is filled with green grass. Also
  in some places the poles are floating in the air with no base. Analyze and look for these issues across all levels in
  all cities. Also change Florida music. Only the background beat is good." (LEARNINGS E19, G6.)
- **Side streets** (Florida's two crossings: Bayfront FL1-3, Biscayne Boulevard FL3-2; Kamakura's were already clear):
  - `miami_plan.py` reads each leg's crossings. It keeps its rows out of them, refuses any model that would stand in a side
    street (from the lane back to its end, 72 m), and on the bayfront starts the land 4 m before a crossing. The bay now
    ends at x 73.2, not 78.
  - `StreetBuilder.Miami` leaves out any plan model still in a side street, with a warning, and cuts the district's land
    round each, so the road's asphalt shows.
  - The other seven districts are unchanged. The two with crossings are re-laid in the same style: stepping past a side
    street moves the rows' random picks after it.
  - A test parses each crossing from FloridaLevels and checks the plan: no model in the street, no water under it.
  - Before and after: `review/florida/crossings_v139.jpg`.
- **Nothing hanging** (`tools/model_support/support.py`, every kit model of both cities: a piece must reach the ground
  through the pieces it touches):
  - `MuseumMIA`: the canopy's nine columns went from 1.2 m (the plinth's height, 3 m in front of the plinth) to the ground,
    and the hanging gardens now reach their canopy.
  - `DockFL`: the boat lift has its cradle, cross beams and bunks under the hull.
  - The rest it lists are by design:
    - the flag and the sign board, which stand on their own post models;
    - the bus's inside;
    - wall lamps, signs, a shutter rail and a lantern, 11 to 23 cm off their walls;
    - the tram on its bogies;
    - the church's bell;
    - an apartment's roof railing;
    - the portable's step.
  - Left as it is: potted plants by four Kamakura doors sit a few cm over their pots. That would need the Kamakura kit
    rebuilt.
  - The museum came from the v125 kit script with the fix applied: its rebuilt atlas is byte-identical to the committed
    one. Today's script packs a different layout since v128 removed two models (LEARNINGS E19).
- **Florida's music:**
  - The drums are as they were. Everything else is new: sunny pop-funk on guitars (funk chops, jangle, palm-muted chords,
    a clean guitar tune), Rhodes, organ, glockenspiel, vibes and the whistle, with a picked bass.
  - New chord cycles in major keys and 14 new written hooks, all passing `tools/music_hooks/check.py`.
  - Each tune voice and comp is levelled against the others: the guitar's tune had measured 17 dB under the Rhodes chords.
  - The whistle no longer slides up from 0 Hz on a note that isn't tied to the one before.
  - Loudness 0.109 to 0.116 RMS, peaks under 0.5. Previews of four legs, as heard in game, went to the user.
  - Only Florida's music changed in `tools/audio_hash`.
- **Cost:**
  - The district: a few models fewer, and the land in a few more pieces.
  - The museum's columns: about 60 triangles more.
  - The dock's cradle: 4 boxes.
  - The music: as v138.
- **Checked:**
  - the plan diff;
  - the before-and-after renders from the game camera;
  - the support check;
  - compile (no new error kinds);
  - `unity_api_check` 6000.6 and 6000.7.
- **Not run in Unity:** rebuild the levels, then look at Bayfront's and Biscayne's crossings and the museum.

## The sweeper's cab is solid, and Bayfront's side street leads to a port (generated content v140)

- **Why.** The user's screenshots: "Now the kid is able to pass through the sweeping machine. Also still the road is from
  the ocean. Instead add a port behind the scene." (LEARNINGS E20.)
- **The sweeper** (`LevelBuildKit.Sweeper`, Biscayne Boulevard FL3-2):
  - The cab has its own collider on the sweeper's moving body, x 0.92 to 1.86 from the truck's middle and up to its
    2.43 m roof (`SweeperCabFrom`, `SweeperCabTo`, `SweeperCabTop`). The kit-less stand-in gets one round its own cab.
  - The way past: jump onto the 1.2 m back, then double-jump over the cab (2.07 m against 1.23 m). From the street the cab
    is too tall.
  - The ball shells are as they were: the cab's collider now covers what the ball saw too.
- **The port** (Bayfront FL1-3, behind its crossing at x 78 to 84):
  - `miami_plan.py` lays it out, and the plan carries it as built shapes (`boxes`, `labels`). `StreetBuilder.Miami` and
    `preview_street.py` build the same.
  - The road runs back between the quay and the school's lawn to the port's gate at z 62: booths either side, raised
    barriers, and a "PORT GATE 3" sign gantry 5 m over the street. A fence runs either side of the gate.
  - The quay runs along the water's edge (x 73.2) on concrete, with its wall, fenders, a yellow edge line, bollards and
    line coils.
  - Alongside the quay: a freighter beside the street, another under the cranes, and a tug.
  - Three ship-to-shore cranes stand on the quay: legs, portal, boom out over the water, A-frame with its stays, trolley and
    spreader.
  - Past the fence: a concrete yard, with 191 containers in stacks one to four high, light masts, and two trucks waiting
    under the cranes.
  - Nothing low stands in the street: the builder refuses any plan shape below 4.5 m in a side street, with an error.
  - A model's footprint is now turned as it stands when checked against a side street (`InSideStreet`, `in_street`): a
    freighter moored end on is 7 m wide, not 30. The other eight districts' plans are unchanged.
  - FL1-3's other picks moved: the port draws on the leg's random numbers.
  - Before and after: `review/florida/port_v140.jpg`.
- **Tests** (`MiamiKitTests`):
  - The port: quay at the water's edge, cranes, containers, the gate before the street's end and clear over it, a
    freighter alongside, concrete ground, nothing in the street.
  - The sweeper: the cab's collider reaches the kit cab's roof, and a double jump from the back clears it.
- **Cost** (`docs/PERFORMANCE.md`), Bayfront only:
  - 375 static boxes (12 triangles each, about 4,500 triangles) and one text mesh, combined by the district's
    `StaticBatcher` into a few draw calls (flat colours, plus the concrete surface for the quay's wall).
  - Two freighters, a tug, bollards and line coils from the kit (15 models more).
  - The sweeper: one more box collider on a body that already moves.
- **Checked:**
  - the plan diff;
  - renders from the game camera (before and after) and a wide shot;
  - compile (no new error kinds);
  - `unity_api_check` 6000.6 and 6000.7.
- **Not run in Unity:**
  - Rebuild the levels.
  - On Biscayne Boulevard: get onto the sweeper's back and over its cab, and walk into the cab from the back (it should
    stop you).
  - On Bayfront: look up the side street.

## The Sketch and Cartoon filters removed (generated content v141)

- **Why.** The user: "Remove the Sketch and Cartoon filters." (LEARNINGS D13.)
- **What's left:** Filters offers the original look and the comic halftone, as one row of cards. Both are as they were.
  A save that had the sketch or the classic cartoon chosen opens in the original look.
- **Removed:**
  - `World/PostFX`: the sketch (pass 6) and the classic cartoon (passes 7 to 9), their settings and the noise texture
    they shared.
  - `Shaders/PostFX.shader`: those passes and their helpers. `Shaders/DtsCartoon.cginc` and `World/ClassicLook.cs` are
    deleted.
  - The menus:
    - `UI/CartoonPicture` and `Resources/Shaders/CartoonPicture` are deleted. The player cards, Locker Room items,
      stickers, logo and town map are drawn as themselves; they always were, unless the cartoon was chosen.
    - `UI/Kit/CartoonButton` is deleted, and so is every UIKit button's hidden ink rim (one image fewer per button).
  - The comic words: their pencil version (`ComicPops`' pencil lettering and starburst, `ComicLettering.sketch`, the
    lettering shader's hatching). They now pop with the comic filter only.
  - The cards' strings (English and Spanish).
  - `FilterLookTests`, replaced by `FilterRemovalTests`. `GameLogicTests` holds the two saved ids.
  - README, ART_DIRECTION, PERFORMANCE and CITIES no longer describe them.
- **Kept on purpose:**
  - The scene's alpha codes for cels, foliage and clouds, and the kits' "Cel" material copies: they change nothing on
    screen now (LEARNINGS D13).
  - `review/sketch` and `review/cartoon`: the boards and ports they were approved from. `review/cartoon/render_scenes.py`
    is also one of ToonCharacter's Blender mirrors.
- **Cost:** less.
  - The PostFX shader has 6 passes instead of 10, so fewer to build at warm-up.
  - Every UI button has one image fewer.
  - The ComicPops pencil starburst (a 256 x 256 texture) is no longer drawn at boot.
- **Version 141:** generated scenes are rebuilt, so none keeps a button with the removed component.
- **Checked:**
  - compile (no new error kinds);
  - `unity_api_check` 6000.6 and 6000.7.
- **Not run in Unity:** open Filters (two cards), and switch between the original and the comic in a level.

## Ground to the horizon, and the port road at every route's school (generated content v142)

- **Why.** The user's screenshots: "The tall buildings seem to float on water or void in all levels. Add the realistic
  grounds. Also add the port and road beside school in the last level of all routes. One of the levels has it right."
  (LEARNINGS E21.)
- **The ground** (`miami_plan.py`: `Plan.ground`, `city`, `plazas`, `far_shore`), every Florida leg:
  - Land or water from the street's own strips out to 2,400 m, and 1,700 m either side of the leg. The water runs to the
    horizon and to the sides where it reaches a leg's ends; land fills the rest.
  - A city of low blocks (5 to 24 m, Miami's pale colours) from 200 m back. The first rows are low, so from the street
    they are roofs over the houses.
  - A paved plaza under each tower.
  - The far shores across the bay (Bayfront, Museum Park): a seawall face, and a waterfront of low buildings and some
    taller ones, which the towers rise behind.
  - Riverside Street (FL2-1): the Miami River behind the yards, with its banks. The freighter is moored on it (it stood on
    a lawn), and the crane stands on the far bank.
  - The Riverwalk (FL2-2): its far bank runs to the horizon, with a bank face, and the city behind its towers.
  - The plan's checks sample the camera's whole view for holes, and fail on anything standing off the ground and any
    boat off the water. `MiamiKitTests.TheGroundReachesTheHorizonUnderEveryTower` holds the same.
- **The port road beside the school on every route's last leg** (Bayfront FL1-3 already had it):
  - **Downpour (FL2-3):** Crossing(100, 106) before the school; the sign reads "The sun's back! Wait for the green man".
    The walker at 98 to 104 is gone. Downtown meets the bay in a 60 m basin behind its blocks, with its quay along the
    port road; seven towers that stood where the basin is are left out. The street's own paving ends at the basin (the
    plan's `back`).
  - **Museum Park (FL3-3):** Crossing(89, 95) after the last checkpoint (the low wall at 90 is gone; coins at 97 to 102).
    The bay ends at the quay, 4 m before the road.
  - One `port()` builds all three: the quay, its wall out to the horizon, cranes, freighters, gate, fence, yard and
    containers. It clears whatever the district stood where the port now is.
  - The cruise ships keep clear of the land now beside the bays.
- **Builder** (`StreetBuilder.Miami`):
  - the water's far edge (`z1`);
  - the strips' depth (`back`).
  - Everything else is the plan's land and shapes, built as in v140.
- **Preview:** water to `z1`, strips to `back`. `--camup H` looks from H m above the street at its far ground (a check
  only, not the game's view).
- **Before and after:** `review/florida/ground_ports_v142.jpg`. From the top:
  - Museum Park's school;
  - Downpour's school;
  - Bayfront's far shore;
  - the Underline from above, where the towers stood on the sky.
- **Tests** (`MiamiKitTests`):
  - the port road at all three schools;
  - the side streets clear in all four legs with a crossing;
  - the ground to the horizon in all nine legs.
- **Cost** (`docs/PERFORMANCE.md`), per leg:
  - 50 to 125 city blocks and 4 to 27 plazas: static boxes of 12 triangles, under 2,000 triangles, combined by the
    district's `StaticBatcher`;
  - on the far shores, about 50 waterfront boxes;
  - 2 to 7 more land quads.
  - Downpour and Museum Park gain the port: about 400 boxes, as Bayfront's (about 4,500 triangles), and 15 models.
  - No new materials: flat colours and the concrete and grass surfaces.
  - Overdraw: the blocks stand where the sky was; the haze covers them.
- **Play:** Downpour and Museum Park each have one more crossing to wait at. Their target times are as they were. Check
  them on the phone.
- **Checked:**
  - the plan's checks;
  - renders from the game camera, before and after, and from above;
  - compile (no new error kinds);
  - `unity_api_check` 6000.6 and 6000.7.
- **Not run in Unity:** rebuild the levels and look along each leg's skyline and both new port roads.

## Florida's music, new: Miami Latin pop (v143)

- **Why.** The user: "Create a fresh new music for Florida by scraping the existing one." Asked first, they chose Latin pop
  / Miami from four directions, and to keep the drums (LEARNINGS G7).
- **What's new** (everything over the kit; `MusicGenerator.FloridaStyleOf`, `ArrangeFlorida`):
  - **Instruments** (`Instruments`):
    - `Piano`: a bright acoustic piano. Eight partials, a touch sharp as a real string's, the high ones dying first, the
      low ones doubled a cent apart, a hammer thump, and the damper at the note's end. It runs on rotating phasors, with
      nothing above 9.5 kHz.
    - `Brass`: a horn voice. Two saws through a filter that blooms open as the note speaks and settles warm, a breath of
      air, and a held pitch (a late, slight vibrato only on long notes).
    - `Cowbell`: the campana.
  - **The band:**
    - a piano montuno and a tres montuno: syncopated two-bar figures in octaves, the eighth before a chord change already
      on the next chord;
    - a pop tumbao bass that anticipates each chord on the "and" of four;
    - the horn section, a trumpet with a sax an octave under, on the hooks, plus their hits after the opening hook on the
      busy streets;
    - the congas' tumbao all through, the son clave (2-3) in the groove and the lift, the cowbell on the beat in the busy
      streets' lift, a guiro in the calm places, and the bongos' martillo in the breakdown;
    - "ooh"s in the lift.
  - **The seven places,** each with new chords and two new written hooks (14 in all, all passing
    `tools/music_hooks/check.py`):
    - **Street** (downtown: Brickell, Biscayne, the Downpour): F major, 122 BPM, the classic I-IV-V-IV montuno, horns on both hooks.
    - **Market** (Little Havana): C major, 118 BPM, a cha-cha I-vi-IV-V; marimba, then piano, then horns.
    - **Beach:** G major, 124 BPM; horns, then the piano over "ooh"s, with an off-beat guitar.
    - **Site:** D major, 126 BPM; repeated-note horn riffs.
    - **Underpass:** Bb major, 116 BPM, Latin jazz-pop; a flute, then the piano, over held Rhodes chords.
    - **Park:** D major, 114 BPM; marimba, then flute.
    - **Menu:** E major, 112 BPM; the piano, then soft horns.
- **Kept:**
  - the drums, exactly (`SynthDrums`: Kit.Electro on the busy streets, Kit.Psych in the calm places);
  - the 32-bar, four-section form (opening, groove, lift, breakdown);
  - the loudness (0.11 to 0.115 RMS, peaks 0.44 to 0.56).
- **Levels:** each tune voice measured on its own per note (RMS) and levelled to the horns (0.17):
  - the piano in octaves x1.35;
  - the tres x7 (it measured 0.02);
  - the tres montuno x1.5 against the piano's.
- **Checked:**
  - `check.py`;
  - `tools/audio_hash`: only Florida's music changed, and the new `expected.txt` is in the commit;
  - a spectrogram of the Street loop (the four sections, the tune over the montuno);
  - compile with no warnings;
  - `unity_api_check` 6000.6 and 6000.7.
  - Previews of all seven places (MP3) went to the user.
- **Cost:** 0.8 to 1.1 s of worker time and 98 to 108 MB of garbage to make a loop, once per place a session (v139: 0.8
  to 1.6 s and 81 to 91 MB). It is off the main thread, as before. Baking the music offline (`docs/PERFORMANCE.md`,
  "Still to do" 1) would remove it all.
- **Not heard in game yet:** how it sits under each district's bed on the phone.

## Florida's music, new again: tropical house, no string sounds (v144)

- **Why.** The user: "Still not good. Scrap it and create a new one. Don't include the string music." Asked first, they
  chose tropical house, no string sound of any kind, and new drums (LEARNINGS G8). v143's Latin pop is gone (its piano,
  horns and cowbell instruments and its arranger).
- **The new instruments** (`Instruments`):
  - `PanFlute`: a round tone, a breath chiff and a held pitch;
  - `SoftPad`: a soft synth chord, triangle-like, not strings, on rotating phasors;
  - `SynthBass`: a round bass with its 2nd and 3rd harmonics, for small speakers;
  - `SoftKick`: soft and round;
  - `Snap`: a finger snap.
- **The band:**
  - the pad breathing under the kick;
  - the synth bass, which pushes the root on the "and"s and lifts an octave on four;
  - an arpeggio in eighths on a marimba, kalimba or synth pluck;
  - the tunes on marimba, steel pan, kalimba, vibes, glockenspiel, synth pluck and pan flute;
  - "ooh"s in the drop.
- **The kit** (`TropicalDrums`, new): a soft four-on-the-floor kick the mix breathes under, snaps on two and four (with
  claps in the drop), a shaker on the sixteenths, off-beat hats (open in the drop), a rim on the 3-3-2, and a clap roll in
  the last bar.
- **The form** stays v138's 32 bars in four sections. The third is now a drop, with the second hook, "ooh"s, claps and
  open hats.
- **The seven places,** each with new chords and two new hooks (14, all passing `tools/music_hooks/check.py`):
  - **Street** (downtown): A major, 116 BPM, I-V-vi-IV; a pluck riff, then the pan flute.
  - **Market** (Little Havana): C major, 112 BPM, vi-IV-I-V; marimba, then steel pan.
  - **Beach** (the bay, the river): G major, 110 BPM; steel pan, then pan flute.
  - **Site:** D major, 118 BPM; pluck, then steel pan.
  - **Underpass** (the Underline): F major, 108 BPM; pan flute, then vibes.
  - **Park** (Museum Park): E major, 106 BPM; marimba, then pan flute.
  - **Menu:** Bb major, 100 BPM; kalimba, then pan flute.
- **Levels:**
  - Each tune voice was measured on its own per note and levelled to the steel pan (0.23 RMS for a half-second note).
  - The loops sit at 0.103 to 0.109 RMS, peaks 0.42 to 0.49, a touch under v143.
- **Checked:**
  - `check.py`;
  - `tools/audio_hash`: only Florida's music changed, and the new `expected.txt` is in the commit;
  - a spectrogram of the Beach loop (the sections, the tune over the arpeggio and pad);
  - compile with no warnings;
  - `unity_api_check` 6000.6 and 6000.7.
  - Previews of all seven places went to the user.
- **Cost:** 0.9 to 1.05 s and 91 to 103 MB of garbage to make a loop, off the main thread, once per place a session (as
  v143).
- **Not heard in game yet.**

## Kamakura's music, new: cozy Japanese, Florida's synth bass, no strings (v145)

- **Why.** The user: "Update the Kamakura music too with same bass, cozy music but in Japanese style." Asked first, they
  chose the bass only (Florida's `SynthBass`; Kamakura keeps its own gentler drums) and no string sounds (LEARNINGS G9).
  The J-pop it replaces had guitars and a koto-like pluck.
- **New instruments** (`Instruments`):
  - `ShoPad`: the Japanese mouth organ's held reed chord, slow to swell, breathing;
  - `Woodblock`: the temple's mokugyo;
  - `TempleBowl`: the rin, ringing for seconds;
  - `WindChime`: the summer furin.
- **The band** (`KamakuraStyleOf`, `ArrangeKamakura`):
  - the sho's chords;
  - the synth bass, laid back (`CozyBass`);
  - an arpeggio on the kalimba or the music box;
  - the tunes on the shakuhachi (`Flute`), the shinobue (`PanFlute`, high), the kalimba, the music box (`Glock`), the vibes
    and the marimba;
  - "ooh"s in some places' lift;
  - a temple bowl at the opening and the rest, and wind chimes at every section's turn;
  - a little vinyl.
- **The kit** (`CozyDrums`, its own): the boomy kick on the one and the "and" of three, a soft snare with a side-stick on two
  and four, swung hats, a shaker in the lift, a woodblock, soft taiko into the loop. In the rest, only the woodblock and
  quiet hats.
- **The form:** 32 bars in four sections (opening, groove, lift, rest), loops of 77 to 91 s.
- **The seven places,** written on the yonanuki pentatonic (no fourth, no seventh) over the royal road and ii-V-I-vi (14
  hooks, all passing `tools/music_hooks/check.py`, which now checks both cities):
  - **Street:** D major, 92 BPM; music box, then shinobue.
  - **Market:** F major, 96 BPM; kalimba, then shinobue.
  - **Beach:** G major, 94 BPM; shinobue, then music box.
  - **Site:** C major, 100 BPM; marimba, then shinobue.
  - **Underpass:** Eb major, 86 BPM; shakuhachi, then vibes.
  - **Park:** E major, 88 BPM; shakuhachi, then shinobue.
  - **Menu:** Bb major, 84 BPM; kalimba, then shakuhachi.
- **Levels:**
  - the shakuhachi levelled to the other tunes (x1.35, it measured 0.17);
  - the sho's chord to Florida's pad's level (0.14 RMS);
  - the loops at 0.118 to 0.121 RMS (was 0.14), peaks 0.51 to 0.61.
- **Checked:**
  - `check.py`;
  - `tools/audio_hash`: only Kamakura's music changed, and the new `expected.txt` is in the commit;
  - a spectrogram of the Street loop;
  - compile with no warnings;
  - `unity_api_check` 6000.6 and 6000.7.
  - Previews of all seven went to the user.
- **Cost:** 1.0 to 1.5 s and 120 to 139 MB of garbage to make a loop (longer loops and more parts than the old J-pop's
  16 bars), once per place a session, off the main thread. This is the heaviest music yet. Baking the music offline
  (`docs/PERFORMANCE.md`, "Still to do" 1) would remove it all. Check it on the phone, for a hitch as Kamakura's places
  change.
- **Not heard in game yet.**

## The places' ambience off (v146)

- **Why.** The user: "Remove that continuous background music from all music". Asked which layer, they named the places'
  ambience beds (LEARNINGS G10).
- **Changed:**
  - `AudioDirector.AmbienceOn` is false. No place's bed (traffic, waves, crowd...) or cues (a car going by, a gull...)
    are synthesized or played, in Florida or Kamakura.
  - The music and the sound effects play as before.
  - Settings hides the Ambience slider while it is off.
  - `AmbienceGenerator` is kept (its tests still run): setting the flag back to true brings everything back.
- **Test:** `GameLogicTests.ThePlacesAmbienceIsOff`.
- **Cost:** less. No bed synthesis at each new place (it had cost 40 to 118 MB of garbage and up to a second of worker
  time), no bed or cue clips in memory (up to 8 MB a place), and two fewer playing audio sources.
- **Checked:**
  - compile (no new error kinds);
  - `unity_api_check` 6000.6 and 6000.7.
- **Not run in Unity:** play a level of each city: the music only, and the sound effects.

## Kamakura plays Florida's music (v147)

- **Why.** The user: "Use the same Florida music for Kamakura too."
- **Changed:**
  - `MusicGenerator.Generate` plays Florida's styles and arranger for Kamakura (`MusicCountry.Japan`), so the two cities'
    loops are the same samples.
  - `AudioDirector` asks for Florida's music in Kamakura (`MusicGenerator.PlayedAs`), so a loop is made and kept once for
    both cities.
  - Kamakura's own music from v145 is removed: `KamakuraStyleOf`, `ArrangeKamakura`, `CozyBass`, `CozyDrums`, and the
    sho pad, woodblock, temple bowl and wind chime. Git history has them.
  - `tools/music_hooks/check.py` checks Florida's seven styles again.
- **Test:** `GameLogicTests.EveryCountrysMusicIsItsOwn` now checks that Kamakura's loop equals Florida's (and that
  California's still differs).
- **Cost:** less. Kamakura's loops no longer cost their own synthesis: v145's were 1.0 to 1.5 s and 120 to 139 MB each.
  Moving between the cities reuses a loop already made.
- **Checked:**
  - `tools/audio_hash`: every Kamakura music line now equals Florida's, and nothing else changed;
  - compile with no warnings;
  - `unity_api_check` 6000.6 and 6000.7.

## App Review 2.3.10: no Android in the iOS app or its store text

- **Why.** App Review rejected iOS 1.0 (7) on 27 November 2026 under Guideline 2.3.10 (Accurate Metadata): "Revise the
  app's description to remove Android references." (`docs/LEARNINGS.md` H8.)
- **Changed:**
  - `StringTables`: Co-op's "How it works" no longer says "iPhone and Android alike" (English) or "iPhone y Android
    juntos" (Spanish). The Android-only Location tip (`coop.radio.location`) keeps its wording: iOS never shows it.
  - `docs/APP_STORE_LISTING.md`: the App Review notes no longer say "iPhone and Android together"; a rule at the top
    against naming other platforms; the Build field now says to pick the newest build (8 or later).
- **Test:** `GameLogicTests.NoTextOnIosNamesAnotherPlatform`: no string but the Android-only one names Android, Google or
  the Play Store. Checked against the old tables, where it catches both languages' Co-op text.
- **Cost:** none (two shorter strings).
- **To do (the user):** upload a new iOS build (1.0, build 8 or later), paste the corrected review notes into App Store
  Connect, check the live description, promotional text and keywords for "Android" or "Google", pick the new build and
  resubmit. The Google Play listing is unchanged.
- **Not run in Unity:** open Co-op on an iPhone and read "How it works".

## Version 1.0.1

- **Why.** The user: "bump the version from 1.0.0 to 1.0.1", for the App Store resubmission after the 2.3.10 rejection.
- **Changed:**
  - `BuildScripts.AppVersion` (was `DefaultVersion`, `1.0.0`) is `1.0.1`, and it now decides the version. Player Settings
    aren't in git, so before, the version stayed whatever each machine's Player Settings had. `BuildScripts.ApplyVersion`
    raises Player Settings > Version to it whenever the editor loads (`AppleSigning.Apply`) and before every scripted
    build, and never lowers a higher one. `DTS_VERSION` still overrides it.
  - `docs/RELEASE.md` (section 3), `docs/APP_STORE_LISTING.md` (Version `1.0.1`; rename the rejected `1.0` record in App
    Store Connect to match), the Android build script's usage line.
- **Test:** `GameLogicTests.TheAppVersionOnlyGoesUp`.
- **Cost:** none (editor only).
- **Checked:** `unity_api_check` 6000.7; compile errors match a clean tree's (iOS and Android editor sets, tests included).
- **Not run in Unity:** open the editor and check that Player Settings > Version reads 1.0.1.

## Two outfits named for their colours (generated content v148)

- **Why.** The user: "rename the outfits Yellow Rain Coat and Cozy hoodie to just some other names like orange pop, royal
  purple etc. because they are not either raincoats or hoodies. We just change color of existing outfit." (LEARNINGS F5.)
- **Changed:** `CosmeticsTable`: "Yellow Raincoat" is **Lemon Zest** and "Cosy Hoodie" is **Slate Grey**. Colours, prices
  and ids (`outfit_raincoat`, `outfit_hoodie`) are unchanged, so saves that own or wear them carry on.
- **Generated content v148** (143 to 147 were music only and changed no generated content), so the editor rebuilds the
  levels and the cosmetics catalog it shows the names from.
- **Cost:** none at runtime.
- **Checked:** compile errors match a clean tree's; `unity_api_check` 6000.7.
- **Not run in Unity:** open the Locker Room's Outfits tab and read the two names. The App Store's Locker Room screenshot
  (`08_locker_room`) shows the old names if it shows these outfits: take it again with the screenshot tour.

## After Phase 8 (next steps)

1. Open in Unity 6 and fix any compile differences from the 2021 reference DLLs. Likely candidates are deprecated-API warnings for the `BuildTargetGroup` overloads in `BuildScripts`. The shaders (`DtsLook.cginc`, `Toon`, `ToonCharacter`, `Sky`, `PostFX`) haven't been compiled yet; check the Console. Check once in the editor that the dog's legs and the gulls' wings swing the right way. The kit parts' axes were derived from the FBX conversion, not seen.
2. Playtest on devices and tune the feel (tuning assets plus the Tune panel), then the bell times and streak targets (the level table).
   Co-op needs real phones (two iPhones, two Android phones, and a mix): the checklist at the end of [`docs/COOP.md`](docs/COOP.md). Compile `Plugins/iOS/DTSCoopBLE.mm` in Xcode first: it has only been syntax-checked against stand-in headers here. Store forms: `docs/GOOGLE_PLAY_LISTING.md` (a mixed audience, so the location permission older Android needs for a Bluetooth scan is allowed) and `docs/APP_STORE_LISTING.md` (user-generated content: Yes, with the filter and the host's Remove).
3. Optional: swap `CameraFollow2D` for Cinemachine, and add more languages to `StringTables`.
