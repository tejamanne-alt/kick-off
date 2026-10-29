# Blender character pipeline

The kid is modelled, textured, rigged and weighted by script in Blender (run as the
`bpy` Python module, no window needed), then exported to `Assets/_Game/Art/Models/Kid.fbx`.

```
python -m venv blenv && blenv/bin/pip install bpy==5.2.3
python face.py face.png                         # paints the face / atlas texture
blenv/bin/python kid.py -- $PWD/Kid.fbx          # builds Kid.blend and Kid.fbx (face.png next to kid.py)
python face.py face_adult.png --adult
blenv/bin/python kid.py -- $PWD/Adult.fbx --adult  # the adult pedestrians: long sleeves, trousers, adult proportions
blenv/bin/python render_kid.py -- $PWD/Kid.blend $PWD/preview.png BLENDER_EEVEE 500 600   # toon previews
cp Kid.fbx ../../Assets/_Game/Art/Models/Kid.fbx
cp face.png ../../Assets/_Game/Art/Models/KidAtlas.png
cp Adult.fbx ../../Assets/_Game/Art/Models/Adult.fbx
cp face_adult.png ../../Assets/_Game/Art/Models/AdultAtlas.png
```

What the model carries:
- One skinned mesh, one material: vertex colours times the atlas (the face is painted in the
  atlas' upper-left quadrant; everything else samples its white corner).
- UV channel 2, x: the outfit part (0 skin and fixed parts, 1 shirt, 2 shorts or trousers, 3 hair) for `ModelOutfit`.
- Bones: Hips, Spine, Chest, Neck, Head, Upper/LowerLeg, Foot, Upper/LowerArm, Hand (.L/.R), Bag (the kid), and Nose, an unweighted marker in front of
  the face that tells the game which way the model faces.
  The game poses them in code (`CharacterRig`), measuring each swing from the bone's rest pose.

Rendering previews with Eevee needs EGL (on Debian/Ubuntu: `libegl1 libegl-mesa0 libgl1-mesa-dri`).
