"""Coin audit for the story levels and challenges: reads Editor/GreyboxLevels.cs, rebuilds each level's
colliders the way LevelBuildKit's TrackBuilder lays them (ground, platforms, walls, parked cars, steps,
awnings, slide-under barriers, gates, tunnel and walkway roofs) and the surfaces the kid can stand on
(those, ramps, crate stacks, moving platforms), and checks every coin (Coin, CoinRow, CoinArc):

  buried   - the coin overlaps a solid (the kid can't get into it; Coin.Settle would have to move it)
  sunk     - the coin is below the ground or deep in a pit
  too high - the coin is higher than a double jump reaches from anything the kid can stand on under it or
             within a sideways jump of it (1.2 m) (JumpReach.HighestCoin 3.55 m; 4.73 m within reach of a
             springboard's throw); a coin in a fountain's jet, no higher than the jet, is the ball's

    python3 tools/coin_audit.py [Assets/_Game/Scripts/Editor/GreyboxLevels.cs]

Exits 1 when it finds a problem. The numbers come from LevelBuildKit (collider sizes) and JumpReach
(the reach), as of generated content v72."""
import re, sys

HIGHEST = 3.55            # JumpReach.HighestCoin(Defaults)
SPRING_HIGHEST = 4.73     # JumpReach.SpringHeadroom(Defaults): a springboard's throw
COIN_R = 0.28
SIDE = 1.2               # a sideways jump off the edge of something
SLIDE_GAP = 0.85
SLIDE = {  # SlideLook: half length, top, trap (a ball trap: not stood on)
    'PlankTrestles': (1.3, 0.953, False), 'BoomBarrier': (0.06, 0.95, False), 'AccessPlatform': (0.93, 2.0, False),
    'AppleBough': (0.85, 1.09, False), 'StallAwning': (1.1, 1.217, True), 'RollShutter': (0.1, 3.15, True),
    'DeliveryConveyor': (0.32, 0.96, False), 'SurfRack': (1.3, 2.37, True), 'BoatTrestles': (1.72, 1.53, False),
    'Boardwalk': (0.8, 1.94, False), 'RescueBoardStand': (1.5, 1.065, False), 'ScaffoldGantry': (1.32, 4.25, True),
    'BeamTrestles': (2.18, 1.3, False), 'PipeRack': (2.05, 2.04, False), 'SiteBarrier': (0.06, 0.94, False),
    'FallenTrunk': (0.35, 1.55, False), 'OakBough': (1.05, 1.19, False), 'NetTunnel': (1.04, 0.96, False),
    'PlayTower': (1.0, 2.0, False),
}


class V(tuple):
    def __new__(cls, *a):
        return tuple.__new__(cls, a)


class Names(dict):
    def __missing__(self, key):
        return None


def args_of(text):
    """The argument list of one call, evaluated (unknown names are None, SlideLook values their names)."""
    t = re.sub(r'(?<=[0-9.])f\b', '', text)
    t = t.replace('new Vector2', 'V').replace('new Color', 'V')
    t = re.sub(r'TrackBuilder\.SlideLook\.(\w+)', r'"\1"', t)
    t = re.sub(r'\bMathf\.', 'math_', t)
    try:
        return eval('(' + t + ',)', {'V': V, '__builtins__': {}}, Names())
    except Exception:
        return None


def calls(body):
    """(name, raw args) for every t.Name(...) in a level's body, parentheses balanced."""
    out = []
    for m in re.finditer(r'\bt\.([A-Z]\w*)\(', body):
        i, depth = m.end(), 1
        while depth and i < len(body):
            depth += {'(': 1, ')': -1}.get(body[i], 0)
            i += 1
        out.append((m.group(1), body[m.end():i - 1], body.count('\n', 0, m.start())))
    return out


def levels(src):
    for m in re.finditer(r'public static void (\w+)\(TrackBuilder t\)\s*\{', src):
        i, depth = m.end(), 1
        while depth:
            depth += {'{': 1, '}': -1}.get(src[i], 0)
            i += 1
        yield m.group(1), src[m.end():i - 1], src.count('\n', 0, m.start()) + 1


def audit(name, body, line0):
    solids, tops, ramps, springs, coins, holes, jets = [], [], [], [], [], [], []

    def solid(x0, x1, y0, y1, what, stand=True):
        solids.append((min(x0, x1), max(x0, x1), y0, y1, what))
        if stand:
            tops.append((min(x0, x1), max(x0, x1), y1, what))

    for fn, raw, ln in calls(body):
        a = args_of(raw)
        if a is None:
            continue
        g = lambda i, d=0.0: a[i] if len(a) > i and isinstance(a[i], (int, float)) else d
        if fn == 'Ground':
            solid(g(0), g(1), g(2) - 6, g(2), 'ground')
        elif fn in ('Pit', 'Water'):
            holes.append((g(0), g(1), g(2), fn.lower()))
        elif fn == 'Platform':
            solid(g(0), g(1), g(3), g(2), 'platform')
        elif fn == 'Wall':
            w, gt, h = g(3, 0.4), g(2), g(1)
            solid(g(0) - w / 2, g(0) + w / 2, gt, gt + h, 'wall')
        elif fn == 'ParkedCar':
            x, gt = g(0), g(2)
            solid(x - 1.65, x + 1.65, gt + 0.2, gt + 0.95, 'parked car')
            solid(x - 0.17 - 0.95, x - 0.17 + 0.95, gt + 0.95, gt + 1.55, 'parked car')
        elif fn == 'StepAndHighWall':
            x, gt = g(0), g(1)
            solid(x - 1, x + 1, gt, gt + 0.8, 'step')
            solid(x + 1.0, x + 1.5, gt, gt + 1.8, 'high wall')
        elif fn == 'Awning':
            x, h, gt = g(0), g(1), g(2)
            solid(x - 1.1, x + 1.1, gt + h - 0.1, gt + h + 0.1, 'awning')
        elif fn == 'CrateStack':
            x, gt = g(0), g(1)
            tops.append((x - 0.35, x + 1.07, gt + 1.42, 'crate stack'))   # crates move: stood on, not solid
        elif fn == 'SlideUnder':
            look = a[1] if len(a) > 1 else None
            half, top, trap = SLIDE.get(look, (1.0, 1.5, False))
            gt = g(2)
            solid(g(0) - half, g(0) + half, gt + SLIDE_GAP, gt + top, 'slide-under ' + str(look), stand=not trap)
        elif fn == 'SwitchAndGate':
            gx, gh, gt = g(1), g(2, 2.4), g(3)
            solid(gx - 0.175, gx + 0.175, gt, gt + gh, 'gate', stand=False)
        elif fn in ('Tunnel', 'CoveredWalkway'):
            x0, x1, gt, h = g(0), g(1), g(2), g(3, 3.3)
            solid(x0 - 0.5, x1 + 0.5, gt + h, gt + h + 1.2, fn.lower() + ' roof', stand=False)
        elif fn == 'Ramp':
            p, q = a[0], a[1]
            if isinstance(p, tuple) and isinstance(q, tuple):
                ramps.append((p, q) if p[0] <= q[0] else (q, p))
        elif fn == 'MovingPlatform':
            c, w, tr = a[0], g(1, 2.6), a[2] if len(a) > 2 else V(0, 0)
            if isinstance(c, tuple) and isinstance(tr, tuple):
                lo, hi = c[0] - w / 2 - abs(tr[0]), c[0] + w / 2 + abs(tr[0])
                tops.append((lo, hi, c[1] + 0.175 + max(0, tr[1]), 'moving platform'))
        elif fn == 'Fountain':
            jets.append((g(0), g(1), g(2)))
        elif fn == 'Springboard':
            springs.append(g(0))
        elif fn == 'Coin':
            p = a[0]
            if isinstance(p, tuple):
                coins.append((p[0], p[1], ln))
        elif fn == 'CoinRow':
            x0, x1, y, n = g(0), g(1), g(2), int(g(3, 1))
            for i in range(n):
                t = 0.5 if n == 1 else i / (n - 1)
                coins.append((x0 + (x1 - x0) * t, y, ln))
        elif fn == 'CoinArc':
            x0, x1, base, h, n = g(0), g(1), g(2), g(3), int(g(4, 1))
            for i in range(n):
                t = 0.5 if n == 1 else i / (n - 1)
                coins.append((x0 + (x1 - x0) * t, base + 4 * t * (1 - t) * h, ln))

    problems = []
    for x, y, ln in coins:
        where = '%s (line %d): coin at (%.2f, %.2f)' % (name, line0 + ln, x, y)
        for x0, x1, y0, y1, what in solids:
            # the circle against the box
            dx = max(x0 - x, 0, x - x1)
            dy = max(y0 - y, 0, y - y1)
            if dx * dx + dy * dy < (COIN_R * 0.9) ** 2:
                problems.append(where + ' is buried in the ' + what + ' (%.2f to %.2f, %.2f to %.2f up)' % (x0, x1, y0, y1))
                break
        # what the kid can jump at it from: under it, or within a sideways jump
        under = [top for x0, x1, top, _ in tops if x0 - SIDE <= x <= x1 + SIDE and top <= y + 0.05]
        for (ax, ay), (bx, by) in ramps:
            if ax - SIDE <= x <= bx + SIDE and bx > ax:
                xc = min(max(x, ax), bx)
                ry = ay + (by - ay) * (xc - ax) / (bx - ax)
                if ry <= y + 0.05:
                    under.append(ry)
        if any(abs(x - jx) <= 0.55 and y <= jgt + jh for jx, jgt, jh in jets):
            continue   # the ball rides the jet up to it
        if not under:
            pit = [h for h in holes if h[0] <= x <= h[1]]
            if pit and y < pit[0][2] - 0.3:
                problems.append(where + ' is down in the ' + pit[0][3] + ' (%.1f below the banks)' % (pit[0][2] - y))
            continue
        ground = max(under)
        reach = SPRING_HIGHEST if any(sx - 1.0 <= x <= sx + 6.0 for sx in springs) else HIGHEST
        if y - ground > reach:
            problems.append(where + ' is %.2f m above the %s under it: higher than %s reaches (%.2f m)'
                            % (y - ground, 'surface', 'a springboard throw' if reach == SPRING_HIGHEST else 'a double jump', reach))
    return len(coins), problems


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'Assets/_Game/Scripts/Editor/GreyboxLevels.cs'
    src = open(path).read()
    total, found = 0, []
    for name, body, line0 in levels(src):
        n, probs = audit(name, body, line0)
        total += n
        found += probs
    for p in found:
        print(p)
    print('%d coins checked, %d problems' % (total, len(found)))
    sys.exit(1 if found else 0)


if __name__ == '__main__':
    main()
