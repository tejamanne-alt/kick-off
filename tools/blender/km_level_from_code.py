# A Kamakura level as the game builds it, for preview_km_level.py: reads the level's layout method in
# Assets/_Game/Scripts/Editor/KamakuraLevels.cs (t.KmModel, t.KmStandIn, HouseStandIn, t.FirstGraderLine, t.LevelCrossing,
# t.Goal) and what the street adds (StreetBuilder.Kamakura: the home at the door, Hase Station at the stop; LevelBuildKit:
# the crossing's signals, barriers and tram), and writes them as a layout (review/kamakura/levels/<id>/built.json) in the
# game's own depths: every model's street face KamakuraDepth (0.75 m) further back than the proposed layout's front, the
# game's footpath 1.5 m either side of the lane (StreetBuilder.PathHalf). So the board shows the level the code builds.
#   python3 tools/blender/km_level_from_code.py HaseLanes review/kamakura/levels/KM1-1/layout.json review/kamakura/levels/KM1-1/built.json
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
DEPTH = 0.75                                   # LevelBuildKit.KamakuraDepth
NUM = r'(-?[0-9.]+)f?'

method, proposed, out = sys.argv[1:4]
src = open(os.path.join(REPO, 'Assets/_Game/Scripts/Editor/KamakuraLevels.cs')).read()
colours = {name: [float(v) for v in vals.split(',')] for name, vals in
           re.findall(r'(\w+) = new Color\(([0-9., f]+)\)', src.replace('f,', ',').replace('f)', ')'))}
body = re.search(r'public static void ' + method + r'\(TrackBuilder t\)\s*\{(.*?)\n        \}', src, re.S).group(1)
lay = json.load(open(proposed))
placements, markers, people, play = [], [], [], []


def colour(name):
    return [round(c, 3) for c in colours.get(name.strip(), [0.7, 0.7, 0.7])[:3]]


def model(name, x, front, yaw=0, note=''):
    p = dict(model=name, x=round(x, 2), front=round(front + DEPTH, 3), note=note)
    if yaw:
        p['yaw'] = yaw
    placements.append(p)


def stand_in(what, x, front, w, d, h, rgb, base=0.0):
    markers.append(dict(what=what, x=x, front=round(front + DEPTH, 3), w=w, d=d, h=h, base=base, rgb=rgb, solid=True))


for line in body.split('\n'):
    line = line.split('//')[0]
    m = re.search(r't\.KmModel\("(\w+)", ' + NUM + ', ' + NUM + r'(?:, ' + NUM + ')?', line)
    if m:
        model(m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4) or 0))
        continue
    m = re.search(r't\.KmStandIn\("(\w+)", ' + NUM + ', ' + NUM + ', ' + NUM + ', ' + NUM + ', ' + NUM + r', (\w+)', line)
    if m:
        stand_in(m.group(1), *[float(m.group(i)) for i in range(2, 7)], colour(m.group(7)))
        continue
    m = re.search(r'HouseStandIn\(t, ' + NUM + ', ' + NUM + ', ' + NUM + r', (\w+)\)', line)
    if m:
        x, front, w = float(m.group(1)), float(m.group(2)), float(m.group(3))
        stand_in('house to come', x, front, w, 7.0, 5.6, colour(m.group(4)))
        stand_in('its roof', x, front - 0.4, w + 0.8, 7.8, 1.2, colour('Tiles'), 5.6)
        continue
    m = re.search(r't\.FirstGraderLine\(' + NUM + ', ' + NUM + ', ' + r'(\d+)', line)
    if m:
        a, b, n = float(m.group(1)), float(m.group(2)), int(m.group(3))
        step = (b - a) / n
        for i in range(n):
            people.append(dict(model=('FirstGraderBoy', 'FirstGraderGirl')[i % 2], x=round(a + i * step + step * 0.4, 2),
                               outfit=['-', '-', '-']))
        play.append(dict(x=a, what='first-graders walking to school in a line'))
        continue
    m = re.search(r't\.LevelCrossing\(' + NUM + ', ' + NUM, line)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        c = (a + b) / 2
        model('KmCrossingSignal', a - 1.1, 0.95, note='the bells and lamps, this side')
        model('KmCrossingSignal', b + 1.1, 0.95, note='the far bells and lamps')
        model('KmCrossingBarrier', a - 0.1, 0.95, note='its barrier')
        model('KmCrossingBarrier', b + 0.1, 0.95, note='the far barrier')
        model('KmTram', c, 9.0 - DEPTH, 90, 'the tram coming down the tracks (the crossing\'s traffic)')
        markers.append(dict(what='rails', x=c, front=-10.0, w=2.4, d=44.0, h=0.06, base=0.0, rgb=[0.3, 0.28, 0.26], solid=True))
        play.append(dict(x=a, what='the level crossing'))
        continue
    m = re.search(r't\.Goal\(' + NUM, line)
    if m:
        gx = float(m.group(1))
        model('KmTicketGate', gx, 1.3, note='Hase\'s ticket gate: the stop')
        model('KmStationPlatform', gx + 5.4, 2.3)
        model('KmStationSign', gx + 11.4, 1.4)
        play.append(dict(x=gx, what='Hase Station: the stop'))
model('KmHome', -12.0, 1.6, note='the home at the door (StreetBuilder.HomeFrontKM)')
play.insert(0, dict(x=-12.0, what='start: the front door'))

built = dict(level=lay['level'], name=lay['name'],
             about='KM1-1 as the game builds it (KamakuraLevels.' + method + ', read by tools/blender/km_level_from_code.py): '
                   'the game\'s footpath 1.5 m either side of the lane, every model 0.75 m further back than the proposed '
                   'layout\'s front.',
             length=[-20, 96],
             ground=[dict(what='road', z=[-8.1, -1.7], rgb=[0.36, 0.37, 0.38]),
                     dict(what='kerb', z=[-1.7, -1.5], rgb=[0.7, 0.69, 0.66]),
                     dict(what='footpath (the play lane at z 0)', z=[-1.5, 1.5], rgb=[0.62, 0.6, 0.57]),
                     dict(what='frontage', z=[1.5, 40.0], rgb=[0.6, 0.58, 0.55])],
             placements=placements, markers=markers, people=people, play=play)
json.dump(built, open(out, 'w'), indent=1)
print('%s: %d models, %d stand-ins, %d first-graders' % (out, len(placements), len(markers), len(people)))
