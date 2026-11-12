# A city's map plan

`kamakura.py` is Kamakura's map screen as data: the three routes traced along the user's clean map's own roads
(`review/kamakura/refs/KM-MAP2_clean.png`) as `docs/CITIES.md` designs them, the stops between the levels at their
places, each level's node near the start of its leg (as `docs/WORLD_MAP.md` puts them), and the checks the map screen
needs (`Tests/Editor/TownMapTests.cs`), with Kamakura's two rules: one right-angle crossing (the avenue crosses the tram
line) and the shared ends by the user's 5 to 15 %.

```
/home/user/blender/blenv/bin/python tools/city_map/kamakura.py [out dir]     # default review/kamakura/map
```

It writes `KM-MAP3_plan_game.png` (the plan drawn on the clean map at the game's sizes), `KamakuraMapLayout.json` (the
layout in the game's 3200 x 1800 picture, TownMapLayout's format, with the map at 0.83 in its middle) and `checks.txt`,
and exits 1 if a check fails. It needs numpy and Pillow (Blender's Python has both). To move a route, edit its points
(map pixels) and run it again: the nodes follow the stops.
