// Prints a hash of every clip the game synthesizes (all 95: the music of each place in each country, each place's bed
// and cues, the sound effects), or what each generation allocates. See README.md.
using System;
using System.Diagnostics;
using System.Security.Cryptography;
using DribbleToSchool.Audio;

static class AudioHash
{
    static string Hash(float[] samples)
    {
        var bytes = new byte[samples.Length * 4];
        Buffer.BlockCopy(samples, 0, bytes, 0, bytes.Length);
        return Convert.ToHexString(SHA256.HashData(bytes)).Substring(0, 16);
    }

    static long Allocated() { return GC.GetTotalAllocatedBytes(true); }

    static void Main(string[] args)
    {
        bool alloc = args.Length > 0 && args[0] == "alloc";
        foreach (MusicCountry country in Enum.GetValues(typeof(MusicCountry)))
            foreach (var scape in Soundscapes.All)
            {
                long a0 = Allocated();
                var sw = Stopwatch.StartNew();
                var music = MusicGenerator.Generate(scape, country);
                if (alloc) Console.WriteLine($"music {country} {scape}: {(Allocated() - a0) / 1e6:F1} MB allocated, {sw.ElapsedMilliseconds} ms");
                else Console.WriteLine($"music {country} {scape}: {Hash(music)}");
            }
        foreach (var scape in Soundscapes.All)
        {
            long a0 = Allocated();
            var sw = Stopwatch.StartNew();
            var pack = AmbienceGenerator.Generate(scape);
            if (alloc) { Console.WriteLine($"ambience {scape}: {(Allocated() - a0) / 1e6:F1} MB allocated, {sw.ElapsedMilliseconds} ms"); continue; }
            Console.WriteLine($"bed {scape}: {Hash(pack.bed)}");
            for (int i = 0; i < pack.cues.Length; i++)
            {
                var c = pack.cues[i];
                Console.WriteLine($"cue {scape} {i} {c.name} gap {c.minGap}-{c.maxGap} volume {c.volume} pan {c.pan} {c.panSpread} pitch {c.pitchVariance} sweep {c.sweep}: {Hash(c.clip)}");
            }
        }
        {
            long a0 = Allocated();
            var sfx = SoundBank.BuildAll();
            if (alloc) Console.WriteLine($"sfx: {(Allocated() - a0) / 1e6:F1} MB allocated");
            else foreach (var kv in sfx) Console.WriteLine($"sfx {kv.Key}: {Hash(kv.Value)}");
        }
    }
}
