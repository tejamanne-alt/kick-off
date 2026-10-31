# Build Progress

This file is the resume point. A new session should read it first. All eight phases are done; next comes on-device playtesting and tuning (see "After Phase 8").

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

- **Scenes are generated.** `Editor/GeneratedContent.cs` holds the level table (chapter, id, name, scene, bell, streak target, layout). `Editor/GreyboxLevels.cs` holds the layouts, and `Editor/LevelBuildKit.cs` holds the track pieces and the gameplay rig. Bump `GeneratedContent.Version` whenever layouts or the rig change.
- **Compile check without Unity.** Scripts are compiled with Mono `mcs` against the UnityEngine 2021.3 module DLLs (NuGet `UnityEngine.Modules`) and `UnityEditor.dll` (NuGet `Unity3D.SDK` 2021.1). The Unity 6 renames (`linearVelocity`, `linearDamping`, `angularDamping`) are mapped back by sed, and the Input System is stubbed. Three configs: legacy input, Input System, editor. Stay at C# 7.3 (no target-typed `new`, no switch expressions).
- **Presentation listens to `Core/GameEvents`.** Gameplay raises typed events; audio, FX, haptics and analytics subscribe to them.
- Restartable objects implement `IResettable`. `LevelManager.BeginRun` resets them; respawning at a checkpoint doesn't.
- The compile check also references `UnityEngine.UI.dll` (NuGet `Unity3D.UnityEngine.UI` 2020.3) and Mono's `netstandard.dll` facade. The Input System stub includes `InputSystemUIInputModule`.
- **Menus are uGUI built from code** with `UI/Kit/UIKit.cs`: canvas at 1920x1080 matched on height, procedural sprites, `UIButtonFx` presses, `UIPopIn` entrances. No prefabs.
- **The shop's contents** live in `Editor/CosmeticsTable.cs`. Cosmetic art is drawn at runtime by `Cosmetics/CosmeticArt.cs`.
- **Progress** is saved to `persistentDataPath/save.json` by `Progression/SaveSystem.cs` (atomic write, corrupt files backed up). Coin economy constants are in `Progression/Rewards.cs`.
- **Art is code.** `Art/ProceduralArt.cs` draws everything on `Art/PixelCanvas.cs` (anti-aliased shapes, ink outline, watercolour grain, wrap-aware tiling). `Editor/ArtBaker.cs` bakes it to `Assets/_Game/Art/Generated` (FullRect meshes, 9-slice borders). Chapter palettes are in `Art/ChapterTheme.cs`.
- **Previewing art and audio without Unity.** The scratchpad harnesses compile ProceduralArt/Synth against tiny Unity stubs (a Color/Vector2/Mathf/Perlin reimplementation) and render PNG/WAV. Use them to eyeball changes before committing.
- **Audio is code.** `Audio/Synth.cs`, `SoundBank.cs` (26 SFX) and `MusicGenerator.cs` (6 loops) are pure C#. `AudioDirector` (auto-booted, DontDestroyOnLoad) maps GameEvents to SFX and haptics and crossfades music per chapter.
- **All UI text goes through `Localization/Loc.T(key)`.** Tables live in `Localization/StringTables.cs` (en, es). Lose reasons are keys (`lose.*`); level names are `level.<id>`.
- No Cinemachine yet: `CameraRig/CameraFollow2D.cs` covers look-ahead, the dead zone and bounds.

## Phase 3 summary

- Hazards (`Scripts/Hazards`): Pedestrian (bounces the ball, the kid passes), Crossing with traffic light and passing car (red = lose), Dog (chases low balls and noses them back), SlowZone (puddle/sand), WindArea (headwind or updraft, optional gusts), MovingPlatform (carries the kid via `IMovingSurface`), BallSwitch + Gate, Springboard (flush trigger pad).
- Chapter 1 Home Street: L01 Out the Door, L02 Parked Cars, L03 Up the Hill, L04 Garden Gate, L05 Puddle Lane.
- Chapter 2 Market and Crossings: L06 Market Morning, L07 First Crossing, L08 Corner Shop, L09 Fruit Stalls, L10 Rush Hour.

## Phase 4 summary

- Coins (kid or ball collects; restored on restart) and one hidden sticker per level (often placed high, so a kicked ball can collect it).
- 3rd star = beat the bell + hit the streak target + collect every coin.
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
- Build: `Editor/BuildScripts.cs` applies store player settings, bakes the procedural 1024 px icon, signs from environment variables, and offers menu and CI builds (AAB, dev APK, iOS). The iOS privacy manifest is at `Assets/Plugins/iOS/PrivacyInfo.xcprivacy`.
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
- The playable characters are two original teens made in Blender (`tools/blender/teen.py` and its modules), in a soft hand-painted anime style. The girl (`Art/Models/Girl.fbx`) has a chestnut high ponytail with a yellow scrunchie, freckles, a sky-blue blouse with a rounded white collar, a navy pleated skirt that follows her legs, knee socks, loafers and a yellow backpack. The boy (`Art/Models/Boy.fbx`) has short dark hair with a quiff and a cowlick, a plaster on his cheek, a green ringer T-shirt, khaki shorts, red sneakers and a navy backpack. Both have oblong-oval faces painted at 4x and downscaled, sculpted bodies with mitten hands, and fitted hair with tapered locks. Both are built into each level; `Presentation/CharacterChoice` shows the one picked in Settings → Player (saved as `GameSettings.Character`) and passes the shop's outfits to both. The school uniform keeps each model's own clothes (`IOutfit.ResetOutfit`); other outfits recolour the top (part 1) and the skirt or shorts (part 2), starting from the colours in each model's `.json`. The pennant sits on whichever backpack is showing. The younger kid (`Kid.fbx`) is the fallback.
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

The look follows `docs/ART_DIRECTION.md`: clear anime daylight (generated content v37; it was a golden-hour haze before playtesting showed it tinted everything yellow and hid the kid). In v38 the palette was measured against the reference shots and calmed: olive summer greens instead of bright lime (leaves, grass, hedges, palms), a lighter cerulean sky, deeper neutral-cool shade, slightly warm greys, and a grade with 0.88 saturation and 1.12 contrast. The ball is 34 cm across (`LevelBuildKit.BallRadius`), larger than a real 22 cm football so it reads at a glance on a phone.
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
- **Characters stand out:** the kid has the boldest ink outline and a bright rim round the whole silhouette (`ToonCharacter`, set per material in `ArtBaker.CharacterMaterial`). The school uniform dresses both teens in a white shirt and navy shorts (`CosmeticApplier`); before, it left the boy in the sage shirt and khaki shorts he was modelled in, the same tones as the grass and paths.
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

## After Phase 8 (next steps)

1. Open in Unity 6 and fix any compile differences from the 2021 reference DLLs. Likely candidates are deprecated-API warnings for the `BuildTargetGroup` overloads in `BuildScripts`. The shaders (`DtsLook.cginc`, `Toon`, `ToonCharacter`, `Sky`, `PostFX`) haven't been compiled yet; check the Console. Check once in the editor that the dog's legs and the gulls' wings swing the right way. The kit parts' axes were derived from the FBX conversion, not seen.
2. Playtest on devices and tune the feel (tuning assets plus the Tune panel), then the bell times and streak targets (the level table).
3. Optional: swap `CameraFollow2D` for Cinemachine, and add more languages to `StringTables`.
