# Copies the game's own climate code out of Progression/Cities.cs (CityClimate, and every city's climate) for the harness:
# it fails loudly if the source has moved on, rather than mirroring numbers by hand (docs/LEARNINGS.md A6).
import re, sys
src, out = sys.argv[1], sys.argv[2]
s = open(src).read()
try:
    a = s.index('    /// <summary>\n    /// A city\'s weather and light')
    b = s.index('    /// <summary>One of the five cities')
except ValueError:
    sys.exit('extract.py: CityClimate is no longer where this expects it in ' + src + ': update the harness')
cities = re.findall(r'public static readonly City (\w+) = new City\((?:.|\n)*?(new CityClimate\([^;]*?\)|CityClimate\.Reference), new Color', s)
if len(cities) < 5:
    sys.exit('extract.py: found %d cities\' climates, expected 5' % len(cities))
text = 'using DribbleToSchool.Art;\nusing UnityEngine;\nnamespace DribbleToSchool.Progression\n{\n' + s[a:b] + '    public static class Climates\n    {\n'
text += ''.join('        public static CityClimate %s = %s;\n' % c for c in cities)
text += '        public static CityClimate Get(string name)\n        {\n            switch (name)\n            {\n'
text += ''.join('                case "%s": return %s;\n' % (c[0], c[0]) for c in cities)
text += '                default: throw new System.ArgumentException("no city " + name);\n            }\n        }\n    }\n}\n'
open(out, 'w').write(text)
print('cities:', ', '.join(c[0] for c in cities))
