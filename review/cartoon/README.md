# Classic cartoon filter: artwork for review

A fourth filter for **Add-ons & Filters**, beside Original, Comic halftone and Pencil sketch, in the look of the
classic Road Runner shorts the review sent as reference: **inked cels over painted backgrounds**. This folder is the
artwork to approve **before** it is built. Nothing in the game has changed yet. Only the rendering style is borrowed:
the game keeps its own name for the filter ("Classic cartoon"), its own kids, streets and art, and no Looney Tunes
names, characters or pictures.

Every board shows three versions side by side: **Today | Classic cartoon | Calmer**.

| Board | What it shows |
|---|---|
| `1_levels.jpg` | Every chapter (Home Street, Market, Beach, Building Site, Park & School) and the California add-on |
| `2_characters.jpg` | All six kids, a passer-by, the dog, cat, gull and ball close up, and every face at 2x |
| `3_ui_art.jpg` | The menus' pictures: the six player cards, the five Locker Room bags, the logo, all 23 stickers, the town map |
| `4_screens.jpg` | Mock-ups: the title screen, and the Add-ons & Filters panel with a fourth card, Classic cartoon |
| `5_details.jpg` | Detail at 100%: today, the first version, the crisper version now, and calmer |
| `frames/*.jpg` | Each scene at full size (1920 x 1080): today, classic cartoon, calmer, to zoom into |

## Review so far

- **Strength:** the classic cartoon look is good; a calmer setting is shown beside it (gentler saturation, less
  orange, softer warm shadows, a paler sky).
- **Menu buttons:** an ink edge and a hard shadow while the filter is on. Agreed.
- **Pop-up sound-effect words** (THWACK!, BOING!...): not with this filter. Agreed.
- **Detail:** the first version lost detail. Now crisper (see `5_details.jpg`):
  - The smoothing is a smaller brush (2.5 px, was 4 px), and it is **cored**: of what it takes away, only weak
    texture (stains, noise) stays away; anything with real contrast (a window frame, a letter, a spoke, a brick
    joint, a seam) comes back exactly as drawn.
  - The strokes between colours are 1 px (were 1.4) and steeper, so they read as lines, not halos.
  - A light sharpen on the scenery, before and after; none on the faces or the foliage.
  - The kids' outline is anti-aliased (read half a pixel off with bilinear filtering), not stair-stepped.
  - Faces: only strong detail is kept (eyes, brows, mouths), the painted shading's patches are smoothed, and the
    tone steps are softer, so skin is clean rather than blotchy.
  - Much fainter brush streaks (0.025, were 0.07) and film grain (0.012, were 0.035).

## What was matched from the reference

| In the Road Runner frames | In the filter (`classic_port.py`) |
|---|---|
| Characters are cels: flat colour in one or two tones, a bold dark-brown ink line all round | The kids, passers-by and ball, and the things the kid plays with (coins, animals, cars, crates, cones, the pipe), are cels: flat tones and a smooth 4 px warm-black outline near the camera |
| Backgrounds are painted, not inked: soft airbrushed tone, brush texture | The scenery has no black lines: smoothed texture, soft tone steps, faint brush streaks |
| Forms in the background are separated by darker strokes of their own colour | Where colours meet, and where a nearer form overlaps a farther one, a darker stroke of the same colour |
| Hot, warm, saturated colour; shadows rich and warm, never grey | Reds, oranges, yellows and beiges pushed to orange and gold; quiet colours lifted; shadows pushed to warm browns. Blues and greens keep their hue |
| Flat turquoise sky, soft white clouds | A turquoise sky, pale at the horizon; white clouds with soft blue-grey shade |
| 1950s film print | A faint grain and a soft vignette |

What a filter cannot do: redraw the kids and streets with a hand animator's shapes and squash-and-stretch. Their
shapes stay the game's; the rendering is the cartoon's.

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

(`cartoon_port.py` run on its own is the first take from before the Road Runner reference came in: bold black
outlines on everything and bright flat colour.)

## If approved: what gets built

- `Shaders/PostFX.shader`: a classic cartoon pass (the cels, the painted background, the sky, the print), with its
  settings on `World/PostFX` (and a **Force** toggle for the editor), the calmer setting as a preset of the same
  settings. The camera's depth and normals are already asked for by the other filters.
- The mask in the picture's alpha gains values: 0 the cels (`ToonCharacter` already writes 0 for the people and the
  ball; coins, animals, cars and the hazards' materials get the same), 0.5 foliage (the plants kit, `Toon.shader`),
  1 the scenery.
- `Progression/AddOns`: a fourth filter, strings `filter.classic` ("Classic cartoon", "Inked characters, painted
  scenery") in English and Spanish. It fills the fourth card slot, so the panel keeps its size.
- One camera filter covers every level, the challenges, the Holiday Run, co-op races, the menu's live street and the
  Locker Room. A UI material does the 2D version for the player cards, bags, stickers and logo (cels) and the town map
  (painted). The menu buttons take an ink edge and a hard shadow while the filter is on. Text is never filtered, and
  the comic words do not pop with this filter.
- Cost: two smoothings (the cels' and the scenery's), the strokes, the outline and a light sharpen. The final
  sharpen needs a second, cheap pass; if the whole is heavy on older phones, the scenery's smoothing can run at half
  resolution.

## Open question

Which one ships, Classic cartoon or Calmer? (Or both, with Calmer as a "Cartoon strength" setting.)
