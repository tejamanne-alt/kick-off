# Kick Off 2: notes for anyone working on this repo

- **Before changing anything,** read `docs/LEARNINGS.md`: every past mistake, its cause and the rule it set. Add an entry there whenever something has to be fixed, reverted or redone.
- **Every asset is reviewed by `docs/ASSET_REVIEW.md` before the user sees it or a level uses it** (strict): all
  eight views (front, back, top, bottom, left, left 3/4, right, right 3/4), its motions animated (walk, run, fly, swim,
  idle as they apply), every check listed with its result. The motions are the game's behaviour code ported, never
  invented for the review: an animal's gait lives in `Assets/_Game/Scripts/World/LegGait.cs` and its mirror in
  `tools/blender/asset_review.py`; change both together.
- **Performance budgets and device tiers** are in `docs/PERFORMANCE.md`. Every change states its cost against them. Nothing is "done" until it has run on the reference phone (OnePlus Nord CE5).
- **Characters** are rebuilt from their pre-polish originals by `tools/blender/polish_all.py` (see `tools/blender/README.md`, "Polishing the characters"). When `Shaders/ToonCharacter.shader` changes, update its Blender mirrors in the same change: `review/cartoon/render_scenes.py`, `tools/blender/portrait_teen.py`, `review_teen.py` and `review_poses.py`.
- **History** is in `PROGRESS.md`, and the conventions are under "Conventions (keep these)".
- **Unity versions:** the checks compile against Unity 2021 references, but the user may open the project in a newer Unity 6. Before pushing script changes, run `tools/unity_api_check/run.sh` against the newest `6000.x` branch (`tools/unity_api_check/README.md`): it also parses every script under every `#if` combination, the tests included.
