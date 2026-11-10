# Learnings: every mistake, its cause, its fix, and the rule it taught

Read this before changing anything. Each entry is something that went wrong, or nearly did, in building Kick Off 2. Every entry gives:
- **What happened**, with the version (`vN` is `GeneratedContent.Version`) or commit;
- **Why**;
- **The fix**;
- **The rule** to follow from now on.

Add a new entry whenever something has to be fixed, reverted or redone, in the same commit as the fix. The rules at the top are the ones broken most often or at the highest cost. The sources are `PROGRESS.md`, the git history (PRs #1 to #45 and later) and the audits of November 2026.

## The rules that matter most

1. **The phone is the truth.** A change to cost, feel or GPU output isn't done until it has run on the low-end reference phone (a OnePlus Nord CE5: Mali-G615 MC6, 2392×1080, 120 Hz). Record the fps and frame pacing in `PROGRESS.md`. Compiling, glslang, numpy shader ports and Blender renders are proxies. They prove "it builds" and "the mock looks right", never "it runs well".
2. **Budget before you add.** Every mesh, texture, shadow setting, full-screen pass and per-frame script has a cost per device tier (`docs/PERFORMANCE.md`). Every change states its delta. The game reached 28 fps by adding cost that was each time noted as "not checked on a low-end phone".
3. **Settings live in code.** `ProjectSettings/` is not in git, so every player, quality, graphics, frame-rate and import setting is applied from code: `Editor/BuildScripts.cs`, `Core/GraphicsQuality.cs`, the asset postprocessors. Never rely on what a fresh checkout defaults to.
4. **Write the target before changing a character.** That means style references, a triangle budget and an acceptance board. Let the user choose from side-by-sides. Never swap a character's source back on your own judgement.
5. **Review characters as players see them.** That means:
   - at the current camera's play size, close up, and on the title screen;
   - from the game's camera angles;
   - in all four looks (Original, Comic halftone, Pencil sketch, Classic cartoon);
   - with characters casting no shadows, as in the game;
   - with the head nodded and turned as the menu and the run move it, not only in the idle pose (C15).
6. **A fix for one asset is a fix for all of them.** When a pipeline bug is found and fixed, rebuild every asset made by the old pipeline in the same change.
7. **Record every revert,** with who decided, why, and "don't retry X".

## A. Process and verification

**A1. Nothing had ever run in Unity or on a device.**
- *What:* 57 sections of `PROGRESS.md` say "Not run in Unity". The shaders were never compiled by Unity. The 60 fps release check (`docs/RELEASE.md`) was never done, although the brief asked for device testing after every phase. The first real performance data was the user's Nord CE5 recording: about 28 fps, with frames from 17 to 79 ms.
- *Why:* there is no Unity in the build environment, so proxies stood in.
- *Fix:* none possible here. Every change since is labelled with what was and wasn't verified.
- *Rule:* rule 1. Say plainly, in the commit and in `PROGRESS.md`, what still has to be checked on a device.

**A2. A compile error reached the user (PR #22, fixed in #23).**
- *What:* `LevelBuildKit`'s own `Cosmetics` member hid the `DribbleToSchool.Cosmetics` namespace in a partial class.
- *Why:* the compile check wasn't run over every changed editor file.
- *Fix:* the type is now fully qualified.
- *Rule:* run the compile check on every commit. In the editor's partial classes, fully qualify types from other namespaces.

**A3. The compile check was blind to method bodies (found November 2026).**
- *What:* against reference DLLs that lack the uGUI and Input System types, Roslyn stops after declaration errors and never binds method bodies. A deliberately wrong API call compiled "clean".
- *Fix:* the check uses empty stubs for `UnityEngine.UI`, `EventSystems` and `InputSystem`, so declarations bind and method bodies get checked. It diffs the errors against a clean-tree baseline, ignoring line numbers, and allow-lists Unity 6-only APIs that are missing from the 2021 references (`Resolution.refreshRateRatio`).
- *Rule:* a check is only trusted after it has caught a planted error. Plant one whenever the harness changes.

**A4. Unity 6 and Xcode warnings only the user could see.**
- *What:* the deprecated `DEVELOPMENT_BUILD` directive; Xcode run-script warnings.
- *Rule:* treat the user's console logs as test results. A property whose name moved between Unity versions (for example `optimizedFramePacing`, `meshDeformation`, the tier settings) is set by reflection and logs when it is missing.

**A5. Shader checks are syntax only.**
- *What:* glslang caught `line` (a reserved word) twice and a missing uniform. Nothing checked GPU behaviour or cost.
- *Rule:* compile every pass with glslang, and plant an error to prove the harness works. Give every full-screen pass a millisecond budget and a resolution scale.

**A6. Tools that copy game code rot silently.**
- *What:* the town-map tools stopped running when `RouteTable` gained an argument. `review_poses.py` hand-copies the game's poses. The Blender review renderers copy `ToonCharacter`'s shading.
- *Rule:* a tool that mirrors C# or a shader either parses the source or fails loudly. When `ToonCharacter.shader` changes, update `review/cartoon/render_scenes.py`, `tools/blender/portrait_teen.py`, `review_teen.py` and `review_poses.py` in the same change. Otherwise the review boards and the menu's player cards drift from the game.

**A7. Reversals with no written record.**
- *What:* Two reversals were left out of `PROGRESS.md`:
  - v84: Mia rebuilt in the scripted anime style (`a4a19ad`), reverted five minutes later at the user's request (`2ea2e7d`). The user wanted their own supplied design, not a generic anime kid.
  - v86: the camera moved closer (`eedac25`), reverted as v87 because collectibles fell out of view.
- *Rule:* rule 7. Gaps in the version numbers must match recorded reverts.

**A8. Approval boards before building: keep doing this.**
- *What:* the comic, sketch and classic-cartoon filters were each approved from boards first. The boards caught eyes turned into black dots, an outline lying over a cheek, and lost detail.
- *Rule:* use the same method for characters (see `review/characters_v2/`) and for cost: put an estimate on the board.

**A9. Claims that stopped being true.**
- *What:* the README says "All art and audio are generated in code". The store text says every character was "made for this game", though the characters come from an image-to-3D generator.
- *Rule:* when an asset's source changes, update the credits, README and store text in the same change. Keep a list of each supplied asset's source and licence.

**A10. Settings that lived in one checkout.**
- *What:* Android version codes went backwards. Phones defaulted to 2 bones per vertex. HDR, MSAA, the Android blit, frame pacing and shadow cascades were all whatever the building machine generated.
- *Fix:* a version code that always rises; `Bone4` set in code; and, from November 2026, `BuildScripts.ApplyAndroidPerformanceSettings` plus `Core/GraphicsQuality`.
- *Rule:* rule 3.

**A11. The editor opened in Safe Mode on Unity 6.5 (introduced in v115, fixed November 2026 without a content rebuild).**
- *What:* the user opened the project in a newer Unity 6 and got "The project you are opening contains compilation errors". The cause was `Object.GetInstanceID()` in `CharacterRig` (added in v115 for the breathing's phase): an error from Unity 6.5 (`[Obsolete("Use GetEntityId instead.", true)]`), a warning in 6.4, fine in 6.0.
  - The console also listed five CS0675 warnings in `RoomBeacon` (int fields widened to `ulong` straight from a signed int, which sign-extends), and "This project uses Input Manager, which is marked for deprecation".
  - Unity compiles the editor scripts only after the game's, so nothing past the first error was ever checked.
- *Why:* every check here compiles against Unity 2021's reference assemblies (no Unity 6 references are published). An API that a newer Unity removed compiles clean, and the project's `6000.0.68f1` says nothing about the editor a user actually opens it in. The Input Manager was the default of a fresh project, as `ProjectSettings` isn't in git (A10).
- *Fix:*
  - `CharacterRig` spreads the breathing by a golden-ratio counter, with no id.
  - `RoomBeacon` widens through `uint`; the bits are the same, since every field is masked small and positive first.
  - `Editor/InputHandling` sets Active Input Handling to the Input System package on load and offers the restart. The game already read input through the Input System when it is on, and `UIKit` builds its `InputSystemUIInputModule`.
  - Five "never assigned" or "never used" field warnings that the editor and player builds would have shown are gone.
  - `tools/unity_api_check` resolves every Unity API the scripts use (Roslyn, every `#if` combination) and checks it against the `[Obsolete]` list of Unity's own C# reference source for any version (`run.sh 6000.5`). For 6000.5 and 6000.7 the only error was `GetInstanceID`; the old code was flagged, the new is clean.
  - `ScriptConventionTests.NoScriptCallsAnApiANewerUnityRemoved` fails on the known removed calls inside any Unity.
- *Rule:*
  - Before a change is pushed, run `tools/unity_api_check/run.sh` against the newest Unity 6 branch, not only the compile check: what the user opens the project in can be newer than `ProjectVersion.txt`.
  - Use no instance ids at all.
  - Widen signed values through an unsigned type.

## B. Performance and mobile

**B1. 28 fps with uneven frames on a mid-range phone (November 2026).**
- *What:* the recording showed about 28 fps in a level and 21 to 23 fps on the title screen, with frame gaps of 17 to 79 ms.
- *Why:* several costs stacked up, and each was added unmeasured:
  - Every frame rendered at the panel's full 2392×1080, into an FP16 HDR target.
  - Screen-space shadows (soft, two cascades, 35 m) added a depth pre-pass of the whole scene and a full-screen shadow-collect pass.
  - Each filter added a DepthNormals pass over the whole scene, plus 2 to 3 full-screen passes.
  - Each 100k-triangle kid (plus a 30k-triangle bag) was drawn 3 to 4 times.
  - Android's "Blit Type Always" added another full-screen copy.
  - There was no frame pacing: a 60 fps target on a 120 Hz panel, so a missed frame showed for 25, 33 or 42 ms in an irregular pattern.
  - Every scene change caused one-off stalls:
    - music and ambience synthesized at runtime (about 100 MB of garbage);
    - audio clips uploaded in one frame;
    - shaders compiled on first use.
- *Fix:*
  - `Core/GraphicsQuality`: device tiers, 720/864/1080 lines, shadows and bloom per tier, and a frame-rate governor that steps down and remembers.
  - Cameras without HDR or MSAA.
  - Tier settings with no screen-space shadows.
  - Optimized Frame Pacing and Blit Type Auto.
  - PostFX warms up every pass on its first frame.
  - Characters at 32k triangles (bags 8k, passers-by 14k).
  - Per-frame CPU fixes.
  - Full detail in `docs/PERFORMANCE.md`.
- *Rule:* rules 1 to 3. Every full-screen effect has a resolution scale and a cheap low-tier path.

**B2. Character cost grew with no budget.**
- *What:* the playable kids grew from 17k to 26k, then 30k, then 100k triangles (v89, to fix "mitten" hands). Every kid FBX also carried five 30k bags. All six kids and 30 bag meshes were built into every scene, readable: about 270 MB of mesh memory, for one kid on screen. That is 3 to 4.5 triangles per pixel at play size.
- *Why:* detail was fixed by raising the global triangle count instead of spending triangles where they show. Mia's hair took over half her 100k.
- *Fix:* the November 2026 polish: 32k for each playable kid, with the head, hands and texture seams protected in decimation; 8k bags; 14k passers-by. The character FBX files went from 90 MB to 28 MB.
- *Then (v112):* the kids' and bags' meshes moved out of the scenes. The builder saves their renderers empty, and a `LazyRenderer` loads each from a `CastPart` under `Resources/Cast/` only while it is shown. So a scene loads one kid and one bag: about 46k vertices instead of 545k.
- *Rule:* a triangle budget per character type (`docs/PERFORMANCE.md`). Decimate with weights: spend triangles on the face, hands and printed detail, not on hair mass.

**B2a. Script order decides what loads.**
- *What:* the scenes are saved with every kid active, and `CharacterChoice` hides all but one as it starts. With lazy meshes, each kid's loader would have run before being hidden, loading every kid anyway. The bags are the same under `BagWear`.
- *Fix:* `CharacterChoice` runs first (execution order -2000) and hides the others before anything on them wakes. The builder saves every bag hidden, and `BagWear` shows the worn one.
- *Rule:* when a component's start-up cost depends on whether its object is shown, decide who runs first: set it with `DefaultExecutionOrder` or with the state the scene is saved in. Never leave it to Unity's unspecified order.

**B3. The filters' cost was never measured.**
- *What:* classic cartoon is about 73 texture reads per pixel, at native resolution, on the title screen too. "If older phones struggle, pass 8 can run at half resolution" was written down and never done.
- *Rule:* rule 2. Measure in milliseconds on the reference phone before shipping a pass.

**B4. Shadows forced to the top setting on every device.**
- *What:* `WorldLook` forced soft, high-resolution, two-cascade shadows at 35 m whenever the game was playing.
- *Fix:* the tier decides: High as before; Medium hard, one cascade, 25 m; Low none (the contact and blob shadows remain).
- *Rule:* shadow resolution, cascades, distance, softness and extra casters are per-tier settings.

**B5. Runtime audio synthesis spikes.**
- *What:* each scene change generated 1.5 to 4 s of audio on two threads, made about 100 MB of garbage, and uploaded 10 to 13 MB of clips in one frame.
- *Fix (partial):* one clip upload per frame.
- *Still to do:* bake the loops offline.
- *Rule:* never synthesize or upload large assets while a level runs. Spread uploads over frames.

**B6. Per-frame waste in scripts.**
- *What:*
  - Buttons rewrote their rects every frame for 5 s after each press, rebuilding the canvas.
  - Hundreds of procedural shapes ran an empty `Update`.
  - Off-screen coins animated.
  - The dev panel's `OnGUI` ran in release builds.
  - Settings were read from PlayerPrefs (a JNI call) every frame.
  - Haptics made a JNI class lookup per pulse.
  - The comic words rasterized glyphs on first use.
  - Outfit recolouring allocated whole colour arrays.
- *Fix:* the November 2026 CPU pass. Each change was reviewed by a second reader and checked to compile.
- *Rule:* write only on change, snap animations to rest, cache what doesn't change, and put editor-only callbacks behind `#if UNITY_EDITOR`.

**B7. Build size.**
- *What:* the APK reached 854 MB. The `_CA` scenes double the level scenes.
- *Rule:* review build size every release. Share assets between skins instead of copying them.

## C. Characters

**C1. All six playable kids were torn into thousands of pieces (found November 2026).**
- *What:* Hana, Max, Kai, Leo, Mia and Zoe each had 66k to 103k open edges. 79 to 91% of their vertices sat on an open edge, and gaps ran from 0.2 to 24 mm. In the game:
  - the dark ink hull showed through the cracks as scratches;
  - each torn edge had one-sided normals, so the rim light and the cel step flared along every seam, drawing light lines across faces and jeans;
  - the filters inked the cracks.
  This was the main cause of the "low-quality assets" look.
- *Why:* the Meshy scans split their vertices along every texture island, and they were decimated before being welded. The weld fix (`meshy_rigged.weld`, commit `318993d`) was made for the passers-by and never applied to the six kids built a day earlier.
- *Fix:* `tools/blender/polish_character.py`:
  - welds open-edge vertices within 2 mm;
  - drops loose vertices;
  - turns back-to-front triangles round;
  - recomputes normals from the surface around each vertex, so they are continuous across any gap left.
  Run on every character by `polish_all.py`.
- *Rule:* rule 6. Always weld UV-split scans before decimating. Treat a rising open-edge count as a build failure. Check normals, not just shapes: render a normal pass.

**C2. Shattered normals made scanned characters blotchy.**
- *What:* the scans' normals deviated a median of about 19° from the smoothed surface, against a cel step about 4.6° wide. The light/shade boundary crossed about 18k edges on Hana (6k with smoothed normals), and the silhouette broke into thousands of tiny contours, each one an ink speck.
- *Fix:* normals smoothed by surface proximity: 12 mm on skin, 20 mm on clothes, 35 mm on hair. Hair also points away from the centre of its own mass, so the rim light shows only at its outline. The inner face leans toward the head's forward direction, so it is lit as one shape.
- *Rule:* scanned or AI-made meshes always get their normals rebuilt for toon shading.

**C3. White flecks on dark hair.**
- *What:* the rim light was added as white whatever the colour under it, and it lit every noisy hair strand.
- *Fix:* the hair volume normals (C2), and a rim in `ToonCharacter` that is narrower and tinted by the albedo.
- *Rule:* a light term that adds light must respect the surface colour, or it speckles dark materials.

**C4. The primary-school kids changed source eight times.**
- *What:*
  - scripted (anime);
  - supplied Meshy scans (v74 to v77);
  - scripted again (v80, Claude's call);
  - supplied again (v81, the user's call);
  - Mia in the anime style (v84, reverted at the user's request);
  - rigged supplied models (v90 to v95).
  Then the user said the kids "look a bit real life" and that even Hana and Max "look like low-quality assets".
- *Why:* there was never a written target for style, fidelity or budget, and the photographic texture (baked lighting, a real child's face) was never addressed.
- *Fix (November 2026):* the user's own designs are kept, but restyled:
  - an illustrated face replaced the photographic one (`tools/blender/face_paint.py`): drawn eyes with highlights, simple brows, a nose stroke, the kid's own mouth, a little blush, in their own skin tone. The user rejected it as alien (C14). Since v113 each kid keeps their own face with Max's finish (`face_ink.py`);
  - the mesh is repaired (C1, C2).
  Reviewed before and after in `review/characters_v2/`.
- *Rule:* rule 4. "Make it a game character" means the user's design with a game finish. It does not mean a generic replacement: that is exactly what was reverted in v84.

**C5. Scans with arms fused to the body.**
- *What:* Leo, Zoe and Kai, scanned with their arms hanging against the body, smeared at the shoulders. Several repair attempts were dropped.
- *Fix:* rigged models in an A-pose (v90 to v95).
- *Rule:* accept a generated character only in an A-pose, with the arms a hand's width from the body and a Mixamo-style rig. Ask for flat, unlit, cel-style colour (no baked lighting, no photographic skin) and game proportions. Reject a fused scan instead of spending days repairing it.

**C6. Guessed weights folded the faces.**
- *What:* weights by nearness put 18 to 29% of the front of the head partly on the Neck bone, so faces folded as the head turned.
- *Fix:* a rigid head above the jaw (v79).
- *Rule:* use the source's own skin weights where they exist, and check weight distributions with numbers.
- *Later:* the source's own weights were no better. The rigged scans folded the same way until v114 (C15).

**C7. Decimation removed joints, and later dragged prints.**
- *What:*
  - The trousers' knee became one long hinge (bare skin showed through).
  - In November 2026, cutting to 32k first stretched Leo's "01" and Kai's plaid into blocks: vertices on texture-island borders moved and dragged the paint with them.
- *Fix:* edge rings put back at the joints, and texture-island border vertices held back in decimation (`polish_lib.seam_vertices`).
- *Rule:* decimation keeps joint loops and texture seams. Compare printed detail before and after.

**C8. Texture-island seams.**
- *What:* atlases of 1,300 to 2,400 tiny UV islands, sampled at mip level 2.4 to 3.3 in a level, where an island is about 4 texels across. Padding was fixed only in the app-icon render (`9d71268`).
- *Fix:* every gap in every character and bag atlas is push-pull filled from its island (`polish_lib.push_pull`).
- *Rule:* pad every game atlas island deeply enough for the whole mip chain. Check at play size with mipmaps on.

**C9. Review renders that weren't the game.**
- *What:*
  - Reviews used a 215 px "in-game size" from before the v85 camera (the kid is about 254 to 350 px tall now).
  - The EEVEE review scenes let characters shadow themselves (hair on face, nose on cheek), which the game never does (`shadowCastingMode` off). That made faces look dirtier in the review than in the game, and hid what the shader really did.
- *Fix:* the November 2026 review scenes turn character shadows off and mirror the new rim.
- *Rule:* rule 5. When reviewing, first confirm the renderer matches the game on one known case.

**C10. Assets still showing replaced characters.**
- *What:* after Ren was removed, the icon and the Play feature graphic still showed him. The App Store header art still shows Ren and the scripted Hana.
- *Rule:* when a character changes, regenerate in the same change every asset that shows them: the player cards (`Resources/UI/Player*.png`, `portrait_teen.py`), the icon, stickers, store art and co-op ghosts.

**C11. Backpack fit, one fix after another.**
- *What:* straps slid off shoulders. A pack sat as a lump. Straps read as a vest. Handles were counted as the bag's top. A bag was sized by its wheels.
- *Rule:* fit accessories by body landmarks (the shoulder joints), not by the mesh's extremes, and review them at child scale.

**C12. The player's outline was thinner than the passers-by's.**
- *What:* 0.0018 against 0.0022 of the screen height, although the art direction says the kid's line is the thickest.
- *Fix:* 0.0024. The outline is now measured in pixels, never under 1.25 px, and set back 1.2 cm from the camera so inner folds draw no ink specks.
- *Rule:* check implementation numbers against `docs/ART_DIRECTION.md` when touching a look.

**C13. Rigs and heights.**
- *What:* `CharacterRig` once reset adults to kid size. One shared neck height would have made all four kids the same height.
- *Rule:* rig code never writes absolute scale. Heights live in the roster table. Check feet on the ground.

**C14. The drawn kid faces looked alien (v111, reverted in v113).**
- *What:* `face_paint.py` replaced Kai's, Leo's, Mia's and Zoe's scanned faces with drawn ones:
  - new eyes, sized from the distance between the scan's eyes (half of it wide, 0.42 of it tall), with big irises and two highlights;
  - a short stroke for the nose;
  - a small stroke for the mouth;
  - blush, on a skin flattened to one tone.
  The user's verdict, with screenshots of Mia close up, in game and on the player cards: "They look terrible and look like aliens. The nose, eyes and mouth are rendered the worst. Max's eyes and facial features look good enough."
- *Why:*
  - The style sheet copied the *shapes* of an anime face (big round eyes, a dot nose, a tiny mouth) onto a child's head with realistic proportions. Doll eyes over a real face read as uncanny.
  - Max's face reads as drawn because of its *finish*: an even skin tone, a bold lash line, solid brows, a clean white and iris, and one line for the mouth. Its proportions are realistic.
  - It was shipped on Blender front views and renders alone. The user saw it first on the phone. Rule 4 says to let the user choose from side-by-sides before replacing a character's face.
- *Fix:*
  - Every kid is rebuilt from their own scanned face.
  - `face_ink.py` gives that face Max's finish without redrawing it:
    - a dark lash line along each eye's own top edge (the boys' lines end at the corner, the girls' end in a small flick), with a faint line under the eye;
    - the brows' own outline, filled with one dark brown;
    - the lips' parting darkened along its own curve;
    - the skin flattened, keeping half its shading.
  - Each eye's opening, brow and mouth is measured from the scan. The nose is left as scanned.
  - `polish_all.py --no-ink` ships the plain scans.
  - Reviewed at in-game, menu and close-up distance and on the player cards (`review/characters_v2/faces_v113.jpg`). Approval still to come from the user.
- *Rule:*
  - Restyle a face by its finish (line weight, flat colour, clean edges), never by replacing its features' shapes or proportions.
  - Keep each kid's own eyes, nose and mouth.
  - Show a face change to the user as a side-by-side before it ships.

**C15. Faces folded as the head nodded (every rigged character, fixed in v114).**
- *What:* the user's recording of the title screen showed Hana's face creasing across the mouth and chin as she watched the ball. The numbers:
  - 38% of Hana's face above the Head joint, and three-quarters of her jaw, were partly on the Neck bone;
  - Mom had over 1,000 face vertices on the Neck, the Shopkeeper about 400, and Max's and every kid's jaw some.
  The menu nods the head 6 to 20° down to watch the ball, and a slide 44°. The part on the Neck stayed behind, and the lower face squashed into the neck. The face lean (C2) took only vertices at least 90% on the Head, so Hana's lower face also kept the scan's noisy normals. The light/shade step then ran across it as a jagged crease that crawled as she moved.
- *Why:*
  - The scans' automatic rigs blend Head and Neck over the whole lower face. C6 was fixed for the scripted kids (v79) but never checked on the rigged scans. That is rule 6 again.
  - Every review used a still pose with the head level.
- *Fix* (`polish_lib.rigid_head`, run on every character by `polish_all.py`):
  - The whole head moves with the Head bone: everything above a cut through the Head joint that dips forward under the chin. Below the cut, the weights blend back to the neck over 12% of the head's height.
  - `face_lean` now takes every head vertex, the jaw included. It leans toward a sphere behind the face instead of one flat forward direction, so the face shades as one rounded shape: lit whole in front light, with a clean curved edge when the sun is to one side.
  - Checked at the menu's -20° and the slide's -44°: `review/characters_v2/head_tilt_v114.jpg`.
- *Rule:*
  - Check skin weights by numbers on every new character: the face is 100% on the Head.
  - Review heads in motion, nodded and turned, never only in the idle pose.

**C16. White tears in dark clothes and hair (every scanned character, fixed in v114).**
- *What:* white specks, slivers and streaks in Hana's jacket and trousers, Max's jeans and the other kids' clothes. The user: "lots of white tears in all the characters, from hair to face to clothing".
- *Why:*
  - A render of the vertex colours alone showed them all; the atlas alone was clean.
  - The rigs' `paint()` (`meshy_boy.py`) gives each garment's faces the garment's colour and divides its texels by it. Faces whose texel wasn't recognised as the garment (light folds, highlights, unpainted seams) stayed "no part": a white vertex colour times a light texel.
  - Cutting to 32k triangles made them bigger.
  - The shop's recolouring left them white.
  - Most of them share no edge with their garment (the scans are cut along every colour line), so a check by connected faces found almost none.
- *Fix* (`polish_lib.absorb_tears`): by surface, not topology. A greyish face of no part joins garment p when p covers 65% of the surface within 2 cm of it (the face itself not counted). This moved 969 of Hana's faces. Skin never moves (its colour is too saturated), and wide features keep their middles: her jacket's "H", the hoodie, the striped cuffs.
- *Rule:* diagnose a colour fault by splitting the render: vertex colours only, atlas only, rim off, ink hull coloured, outfit parts (`review/cartoon/render_scenes.py` `DIAG`). Look at a garment in the parts view before trusting it.

**C17. The rim light drew white scratches on dark clothes and hair, and the review renderer lagged the shader.**
- *What:* with the tears gone, thin white lines remained along every crease of Hana's black trousers and every clump of her hair.
- *Why:* `ToonCharacter`'s rim whitened the colour under it by 45%, whatever that colour was. On near-black cloth (0.02) that adds 0.45 × 0.3: a light line on every inner crease, pocket edge and hair clump, not only round the silhouette. C3 tinted the rim, but not enough for black.
- *Fix:* the rim is whitened by 45% of the colour's lightness (its brightest channel). A light shirt and skin keep their bright edge, and dark hair and clothes keep only a faint sheen of their own colour.
- *Also:* `review/cartoon/render_scenes.py` had never received v111's rim, its characters-cast-no-shadows, or the close-up review scenes. They lived only in a scratch copy, so its renders were not the game's (C9 again). It is now up to date, with the diagnostics above.
- *Rule:*
  - A light term that adds light scales with the surface's own lightness.
  - Copy every scratch copy of a review tool back before committing. The mirrors listed in `CLAUDE.md` include the review renderer.

**C18. Mia's right eye (v114).**
- *What:* after C14, the user found Mia's own right eye (on the left as we look at her) narrower and squinting next to her left: "Take a reference from the right eye and fix it."
- *Fix:* `face_ink.py` replaces it with her left eye, mirrored across the middle of the face, before the lash lines are drawn. Inside the replaced eye the result is written as it is, not as a change, or the old iris showed through as grey specks.
- *Rule:* when one side of a scanned face is worse, mirror the good side rather than redraw it. That keeps the kid's own eye, which C14's rule asks for.

**C19. The torso was one rigid block (every character, fixed in v115).**
- *What:* the user's recordings of Hana and Max dribbling: "the characters' bodies are so stiff, the chest to abdomen part. Because of that hand movement, it looks like hanging from a fixed thing."
- *Why:*
  - `CharacterRig` swung the legs, knees, arms, elbows, head and bag about the body's side axis, and pitched the whole body as one piece.
  - The models' Hips, Spine and Chest bones were never moved; they weren't even on the rig. So the arms swung from a ribcage that never moved.
  - In a real stride:
    - the pelvis turns with the legs and the ribcage the other way with the arms;
    - the trunk sways over the standing leg and dips as the legs reach apart;
    - the chest breathes all the while.
- *Fix* (`CharacterRig.Torso`, worked out from the limbs' own pose, so every animator gets it):
  - the chest turns up to ±15° with the arms' swing, using the sine of each arm's swing so both arms raised overhead turn nothing;
  - the pelvis turns up to ±10° the other way with the legs;
  - the torso sways 3° over the straighter leg and dips 2° at full stride;
  - the chest breathes 0.9°;
  - the head turns, sways and dips back, so the eyes stay level and ahead;
  - the builder puts Hips, Spine and Chest on the rig (v115).
- *Why no weight change:* the torso's weights already blend Hips to Spine to Chest over about 30 cm, so the turn bends through the waist rather than creasing.
- *Reviewed:* `review/cartoon/render_scenes.py` mirrors it (`TORSO=0` gives the old rigid torso). Its `gait` scene renders a run or walk cycle: `review/characters_v2/torso_run_v115.gif`, `torso_walk_v115.gif`.
- *Rule:*
  - Animate the trunk, not only the limbs: a procedural gait needs the pelvis and chest turning against each other.
  - Review motion as motion (a whole cycle), not as one pose.

**C20. The review boards showed faults the game doesn't have, and hid ones it does (found and fixed in v116).**
- *What:* the user, looking at the v114 boards, saw black spots on Kai's face (and brown patches on every chin). The user also saw white tears left at Hana's and Max's trouser hems, on Max's belt, and along Mia's hairline.
- *Why:*
  - **The review renderer.** `review/cartoon/render_scenes.py` drew the ink hull with a Solidify modifier on the figure itself. That threw away the figure's own normals: the smoothed, face-leaned normals the game shades with. Every face was therefore shaded with the scan's raw normals: brown patches, a jagged chin.
  - **The hull's set-back.** The hull was also never set back from the camera as `ToonCharacter`'s `_OutlinePush` (1.2 cm) sets it, so it poked through round every nose and mouth corner as black spots.
  - The game had neither fault. It took a split render (`DIAG=crack` turned the spots magenta) to see it.
  - **The tears were real.** The v114 rule needed the garment to cover 65% of the surface around a face. A trouser hem's pale band sits against the white shoe, a belt's streaks against the hoodie's hem, and a fringe's tips against the face, so the other untagged thing outvoted the garment.
- *Fix:*
  - The renderer's hull is now a copy of the figure (its own surface drawn as nothing), set 1.2 cm back from the camera. The figure keeps its normals. `OUTLINE_PUSH=0` gives the old hull.
  - **The player cards had the same fault.** They are Blender renders shipped in the game: `portrait_teen.py` put the same Solidify on the figure, so the cards' faces had black specks round the nose. The cards, `review_teen.py` and `review_poses.py` now share `tools/blender/ink_hull.py`, and the six cards are rendered again.
  - `absorb_tears` has a second test: the garment against only the neighbours that look like the face (texels within 0.2), while that kind stays sparse round it (a streak, not a printed letter: Leo's "01" and Hana's "H" stay). It runs four rounds, so a band a few faces wide goes too. The face must also be nearly grey, white or cream (saturation under 0.21). On the first try, Mia's beige patterned headband (0.25 and up) passed as "sparse streaks" and went black; the review board caught it before it shipped. Hana's cream cuff stripes (about 0.17) still go.
- *Rule:*
  - Before trusting a review renderer, check it on one known case against the game, and check that each modifier keeps what the game reads (custom normals, vertex colours, UVs). C9 again.
  - Look at a garment's edges (hems, waistbands, fringes) in the parts view, not only its middle.

## D. Art direction and look

**D1. A golden-hour haze hid the kid** (before v37).
- *Rule:* the player's legibility constrains every lighting and grade change.

**D2. Tuning by eye drifted from the references.**
- *What:* v38 "calmed" the palette. v67 measured screenshots against the references and found the sky, paving, whites and shadows all off, because three warm multipliers were stacked.
- *Rule:* measure screenshots against the reference numbers in `docs/ART_DIRECTION.md`. Never tune by eye, and never stack tints.

**D3. The character blended into the ground.**
- *What:* a sage shirt and khaki shorts on grass and paths.
- *Rule:* check character colours against every chapter's palette and every filter.

**D4. California replaced the original town** (v69), and the user wanted the original back (v71).
- *Rule:* add a new regional look beside the shipped one, never in its place, and keep the random draw order.

**D5. Filters damaged faces.**
- *What:* lines traced from the picture turned eyes into black dots. A cartoon outline was drawn over a cheek.
- *Fix:* a figure code in alpha; lines only from depth and normals; outlines only on the far side of an edge.
- *Rule:* filters never derive lines from texture, protect faces through the mask, and are reviewed on faces at 3x.

**D6. Repetition from shared seeds.**
- *What:* every level of a chapter had the same background.
- *Fix:* `StreetBuilder.LevelSalt`.
- *Rule:* salt seeds by level, and audit repetition when content is added.

**D7. Texture detail raised with no memory line** (the Coast atlas at 4096², TownMap.jpg at 23 MB uncompressed).
- *Rule:* every texture increase states its compressed memory per platform.

## E. Levels and world

- **E1. Every level had chapter-1 scenery.** A new-scene call unloaded the level definition. *Rule:* pass data into scene builders explicitly; never hold asset references across a new-scene call.
- **E2. A scene that wouldn't load.** Four components shared `RunMarkers.cs`. *Rule:* one component per file (enforced by `ScriptConventionTests`).
- **E3. Holiday Run trenches nobody could cross.** *Rule:* every gap and wall size comes from `JumpReach`; `LevelFeasibility` checks every layout.
- **E4. The kid trapped in L16 by pushed crates.** *Rule:* physics props near a choke point get one-way constraints and reset-ahead, and every mode has a "Stuck?" escape.
- **E5. Floating cones, a stream you couldn't fall into, a pier starting in mid-air.** *Rule:* place props after the ground is known; every structure has believable access.
- **E6. Coins the drawn kid ran through.** The capsule was 1.2 m tall; the drawn kid is about 1.6 m. *Rule:* collision matches the drawn character; run `tools/coin_audit.py` after a layout change.
- **E7. Camera framing back and forth** (v85 closer; v86 closer still, reverted). *Rule:* any camera change passes a collectible-visibility sweep and the control-layout check.
- **E8. The map and the levels disagreed.** *Rule:* one layout is the source of truth, with validators in both directions.

## F. UI and menus

- **F1. The anchor and pivot trap** caused overlaps in the credits, results, guides and pause menu. *Rule:* lay screens out top down by explicit edges; check 4:3, 16:9 and 21:9 in both languages.
- **F2. Full screens.** The Settings card's two columns are full (718 of 724 units on the left), so a new row overflows. *Rule:* measure the column before adding a row. Graphics quality is automatic for this reason.
- **F3. Map labels too small for Spanish; a test rule stricter than the screen.** *Rule:* measure text with the real font in every language; test rules mirror what is drawn.
- **F4. Wrong instruction text** ("tap KICK" is a pass). *Rule:* check every how-to string against the real input.

## G. Audio

- **G1. Music redone four times on taste.** *Rule:* get reference tracks and adjectives first, then short A/B previews.
- **G2. A park hiss that drowned the music; every bed at the same loudness; coin and whistle too loud.** *Rule:* check spectra and loudness per place, and mix against the music at default volumes.

## H. Co-op, store, release and testing

- **H1. A design that punished the player who stayed connected.** *Rule:* design for reconnection.
- **H2. Distributed bugs that only a 2,000-storm chaos sweep found.** *Rule:* stateful distributed logic gets randomized chaos tests with written invariants.
- **H3. Platform limits found late:** iOS advertisement size, Android scan limits, R8 stripping a JNI-only plugin. *Rule:* write each platform's limits into the design before coding.
- **H4. Version codes going backwards; a debug-signed release bundle.** *Rule:* derive build numbers; release builds refuse to fall back to a debug key.
- **H5. Store and privacy answers that contradict each other** (user-generated content). *Rule:* one source for compliance answers; update every document together.
- **H6. Review notes describing removed controls.** *Rule:* after a control change, update the store text and review notes in the same change.
- **H7. Tests checked by breaking their rules, offline audits, careful save compatibility.** *Keep doing all three:*
  - Planted bad copies make the tests fail.
  - `LevelFeasibility`, the coin audit, the map check and the pose audit run after the relevant change.
  - Persisted ids, enum orders and save keys never change.

## Standing preferences of the user

Never re-propose what is rejected here.
- **Characters:** keep the user's own character designs: outfit, hair, likeness and their reference photos and drawings. Don't replace them with generic anime models (v84 was reverted at once). They should look like polished game characters, not photographs.
- **Kids' faces:**
  - Keep each kid's own scanned eyes, nose and mouth, at their own sizes.
  - No drawn-on doll eyes or stroke noses and mouths (v111 was reverted as "aliens").
  - The target is Max's face: realistic proportions with a drawn finish.
- **Comic filter:** dots and hatching on the characters as well as the street (raised on request).
- **Controls:**
  - nothing inside the stick's ring;
  - a ball icon on the KICK button, not a boot;
  - no auto-run.
- **Town:** the original Japanese seaside town stays the main town; other countries are add-ons.
- **Store art:** use the user's own artwork for the app icon.

## How to add an entry

Add an entry to the right section in the same commit as the fix. Use this shape: what happened (with version or commit), why, the fix, and the rule. If the fix is partial, say what is still to do.
