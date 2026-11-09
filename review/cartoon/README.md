# Classic cartoon filter: artwork for review

A fourth filter for **Add-ons & Filters**, beside Original, Comic halftone and Pencil sketch, in the look of the
classic Road Runner shorts the review sent as reference: **inked cels over painted backgrounds**. This folder is the
artwork to approve **before** it is built. Nothing in the game has changed yet. Only the rendering style is borrowed:
the game keeps its own name for the filter ("Classic cartoon"), its own kids, streets and art, and no Looney Tunes
names, characters or pictures.

| Board | What it shows |
|---|---|
| `1_levels.jpg` | Every chapter (Home Street, Market, Beach, Building Site, Park & School) and the California add-on: the game today beside the filter |
| `2_characters.jpg` | All six kids, a passer-by, the dog, cat, gull and ball close up, and every face at 2x |
| `3_ui_art.jpg` | The menus' pictures: the six player cards, the five Locker Room bags, the logo, all 23 stickers, the town map |
| `4_screens.jpg` | Mock-ups: the title screen with the filter on, and the Add-ons & Filters panel with a fourth card, Classic cartoon |
| `frames/*.jpg` | Each scene at full size (1920 x 1080), today above the filter, to zoom into |

## What was matched from the reference

| In the Road Runner frames | In the filter (`classic_port.py`) |
|---|---|
| Characters are cels: flat colour in one or two tones, a bold dark-brown ink line all round | The kids, passers-by and ball, and the things the kid plays with (coins, animals, cars, crates, cones, the pipe), are cels: smoothed flat, snapped to three tones, a 4 px warm-black outline near the camera |
| Backgrounds are painted, not inked: soft airbrushed tone, brush texture | The scenery has no black lines: a painterly smoothing, soft tone steps, brush streaks across the ground and down the walls |
| Forms in the background are separated by darker strokes of their own colour | Where colours meet, and where a nearer form overlaps a farther one, a darker stroke of the same colour |
| Hot, warm, saturated colour; shadows rich and warm, never grey | Reds, oranges, yellows and beiges pushed to orange and gold; quiet colours lifted; shadows pushed to warm browns. Blues and greens keep their hue (a blue house stays blue, grass goes olive rather than lime) |
| Flat turquoise sky, soft white clouds | A turquoise sky, pale at the horizon; the clouds white with soft blue-grey shade |
| 1950s film print | A faint grain and a soft vignette |

The painted eyes and mouths are kept as drawn (the cels get no inner lines), and shop lettering survives the
smoothing (thin, strong detail is kept). What a filter cannot do: redraw the kids and streets with a hand animator's
shapes and squash-and-stretch. Their shapes stay the game's; the rendering is the cartoon's.

## How the artwork was made

The levels are not painted over: they are the game's own models, atlases and camera, rendered in Blender with the
toon shading (`render_scenes.py`), and the filter is a numpy port written the way the shader will run
(`classic_port.py`, on helpers in `cartoon_port.py`), so what you see is what the build should produce. The menus'
pictures are the game's own PNGs.

```
python -m venv blenv && blenv/bin/pip install bpy==5.2.3     # (EEVEE needs libegl1 and Mesa)
blenv/bin/python render_scenes.py -- $PWD/../../Assets/_Game/Art/Models /abs/renders <scene> 1920 1080
    # scenes: home market beach site park california cast_a cast_b menu
python3 -I compose_boards.py /abs/renders .
```

(`cartoon_port.py` run on its own is the first, cleaner take: bold black outlines on everything and bright flat
colour, before the Road Runner reference came in.)

## If approved: what gets built

- `Shaders/PostFX.shader`: a classic cartoon pass (the cels, the painted background, the sky, the print), with its
  settings on `World/PostFX` (and a **Force** toggle for the editor). The camera's depth and normals are already asked
  for by the other filters.
- The mask in the picture's alpha gains values: 0 the cels (`ToonCharacter` already writes 0 for the people and the
  ball; coins, animals, cars and the hazards' materials get the same), 0.5 foliage (the plants kit, `Toon.shader`),
  1 the scenery.
- `Progression/AddOns`: a fourth filter, strings `filter.classic` ("Classic cartoon", "Inked characters, painted
  scenery") in English and Spanish. It fills the fourth card slot, so the panel keeps its size.
- One camera filter covers every level, the challenges, the Holiday Run, co-op races, the menu's live street and the
  Locker Room. A UI material does the 2D version for the player cards, bags, stickers and logo (cels) and the town map
  (painted); the menu buttons take an ink edge and a hard shadow while the filter is on. Text is never filtered.
- Cost: two smoothings (the cels' and the background's), the strokes and the outline, in one full-screen pass plus
  the grade. If it is heavy on older phones, the background's smoothing can run at half resolution.

## Open questions for the review

1. Strength: as shown, or hotter (more orange, closer to the desert frames) or calmer?
2. The menu buttons' ink edge and hard shadow with the filter on: yes or no?
3. The comic sound-effect words (THWACK!, BOING!...) that pop with the comic and sketch filters: show them with this
   filter too, in a cartoon lettering?
