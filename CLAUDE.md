# Kick Off 2: notes for anyone working on this repo

- **Before changing anything,** read `docs/LEARNINGS.md`: every past mistake, its cause and the rule it set. Add an entry there whenever something has to be fixed, reverted or redone.
- **Performance budgets and device tiers** are in `docs/PERFORMANCE.md`. Every change states its cost against them. Nothing is "done" until it has run on the reference phone (OnePlus Nord CE5).
- **Characters** are rebuilt from their pre-polish originals by `tools/blender/polish_all.py` (see `tools/blender/README.md`, "Polishing the characters"). When `Shaders/ToonCharacter.shader` changes, update its Blender mirrors in the same change: `review/cartoon/render_scenes.py`, `tools/blender/portrait_teen.py`, `review_teen.py` and `review_poses.py`.
- **History** is in `PROGRESS.md`, and the conventions are under "Conventions (keep these)".
- **Unity versions:** the checks compile against Unity 2021 references, but the user may open the project in a newer Unity 6. Before pushing script changes, run `tools/unity_api_check/run.sh` against the newest `6000.x` branch (`tools/unity_api_check/README.md`): it also parses every script under every `#if` combination, the tests included.
