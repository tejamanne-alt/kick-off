# Installs Kamakura's animals (kit_animals_km.py's output) into the game as their own kit, Art/Models/KamakuraAnimals:
# every model's FBX, the manifest (each model's "game" entry says which behaviour moves it and how: LevelBuildKit.KmGame),
# and the shared texture, made 2048 square (an animal is under about 50 px tall on the phone: docs/LEARNINGS.md D41) with
# its cut-out kept at alpha 0.5 and its colour bled 8 px out under the transparent texels, so filtering at the outline never
# darkens it.
#   blenv/bin/python install_km_animals.py /abs/kit_animals_km_outdir [/abs/Assets/_Game/Art/Models/KamakuraAnimals]
import glob
import os
import shutil
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1]
DST = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, '..', '..', 'Assets', '_Game', 'Art', 'Models', 'KamakuraAnimals')
SIZE = 2048

os.makedirs(DST, exist_ok=True)
for fbx in glob.glob(os.path.join(SRC, '*.fbx')):
    shutil.copy(fbx, DST)
shutil.copy(os.path.join(SRC, 'KamakuraAnimals.json'), DST)

a = np.asarray(Image.open(os.path.join(SRC, 'KamakuraAnimalsAtlas.png')).convert('RGBA')).astype(np.float32) / 255
alpha = cv2.resize(a[..., 3], (SIZE, SIZE), interpolation=cv2.INTER_AREA)
# colour resized premultiplied, so the transparent texels' colour doesn't bleed into the edge
rgb = cv2.resize(a[..., :3] * a[..., 3:4], (SIZE, SIZE), interpolation=cv2.INTER_AREA)
rgb = np.where(alpha[..., None] > 0.02, rgb / np.maximum(alpha[..., None], 1e-3), 0).clip(0, 1) * 255
mask = (alpha >= 0.5).astype(np.float32)
grown = mask.copy()
for _ in range(8):
    total = cv2.blur(rgb * grown[..., None], (3, 3))
    weight = cv2.blur(grown, (3, 3))
    edge = (grown == 0) & (weight > 0)
    rgb[edge] = total[edge] / weight[edge][:, None]
    grown = np.maximum(grown, edge.astype(np.float32))
out = np.dstack([rgb.clip(0, 255), mask * 255]).round().astype(np.uint8)
Image.fromarray(out, 'RGBA').save(os.path.join(DST, 'KamakuraAnimalsAtlas.png'), optimize=True)
print('installed', len(glob.glob(os.path.join(DST, '*.fbx'))), 'animals into', os.path.abspath(DST))
