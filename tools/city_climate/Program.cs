using System;
using System.Globalization;
using DribbleToSchool.Art;
using DribbleToSchool.Progression;
using UnityEngine;

// Runs the game's own CityClimate (Progression/Cities.cs) on the game's own chapter moods (Art/ChapterTheme.cs), checks what
// the city tests check, and writes each mood for tools/blender/preview_street.py --mood-json.
//   run.sh <City> <chapter>... <out dir>      e.g. run.sh Florida 1 3 /tmp/moods
static class Program
{
    static string V(Color c) { return string.Format(CultureInfo.InvariantCulture, "[{0:F4},{1:F4},{2:F4}]", c.r, c.g, c.b); }

    static void Check(bool ok, string what)
    {
        Console.WriteLine((ok ? "ok    " : "FAIL  ") + what);
        if (!ok) Environment.ExitCode = 1;
    }

    static float Max(Color c) { return Math.Max(c.r, Math.Max(c.g, c.b)); }

    static void Main(string[] args)
    {
        var mood = ChapterTheme.For(3).mood;
        var same = Climates.Kamakura.Apply(mood);
        Check(same.sun == mood.sun && same.horizon == mood.horizon && same.hazeStrength == mood.hazeStrength, "Kamakura's climate changes nothing");
        Vector3 warm = CityClimate.Blackbody(3000f), cool = CityClimate.Blackbody(9000f);
        Check(warm.x / warm.z > cool.x / cool.z, "a hotter blackbody is bluer");
        foreach (var name in new[] { "Florida", "Madrid", "NewYork", "Mumbai" })
        {
            var m = Climates.Get(name).Apply(mood);
            Check(Math.Abs(Max(m.sun) - Max(mood.sun)) < 0.002f, name + ": the sun keeps its brightness");
            Check(m.hazeStrength <= 0.8001f, name + ": the haze never hides the street");
        }

        string city = args[0], dir = args[args.Length - 1];
        for (int i = 1; i < args.Length - 1; i++)
        {
            int chapter = int.Parse(args[i]);
            var before = ChapterTheme.For(chapter).mood;
            var m = Climates.Get(city).Apply(before);
            Console.WriteLine("{0}, chapter {1}: sun {2} -> {3}, shade {4} -> {5}, horizon {6} -> {7}, haze {8:F3} from {9:F0} m -> {10:F3} from {11:F0} m",
                city, chapter, V(before.sun), V(m.sun), V(before.ambientSky), V(m.ambientSky), V(before.horizon), V(m.horizon),
                before.hazeStrength, before.hazeStart, m.hazeStrength, m.hazeStart);
            System.IO.File.WriteAllText(System.IO.Path.Combine(dir, city.ToLowerInvariant() + "_ch" + chapter + ".json"), string.Format(CultureInfo.InvariantCulture,
                "{{\"sun\": {0}, \"glow\": {1}, \"shade\": {2}, \"horizon\": {3}, \"zenith\": {4}, \"haze\": {5}, \"haze_k\": {6}, \"haze_start\": {7}, \"haze_end\": {8}}}\n",
                V(m.sun), V(m.glow), V(m.ambientSky), V(m.horizon), V(m.zenith), V(m.haze), m.hazeStrength, m.hazeStart, m.hazeEnd));
        }
    }
}
