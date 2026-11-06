using System;
using System.Collections.Generic;

namespace DribbleToSchool.Audio
{
    /// <summary>A sound of the place that comes now and then: a car going by, a gull, a reversing truck.</summary>
    public sealed class AmbientCue
    {
        public string name;
        /// <summary>Interleaved stereo at <see cref="Synth.SampleRate"/>, its loudest peak at 0.6.</summary>
        public float[] clip;
        /// <summary>Seconds between one and the next (picked at random in this range).</summary>
        public float minGap, maxGap;
        public float volume;
        /// <summary>Where it is heard, -1 left to 1 right, and how far either side of that it may land.</summary>
        public float pan, panSpread;
        /// <summary>Random pitch either way (0.1 = up to 10 %), so it never repeats exactly.</summary>
        public float pitchVariance;
        /// <summary>Passes across: the pan travels from one side to the other while it plays.</summary>
        public bool sweep;
    }

    /// <summary>The ambience of one soundscape: a seamless stereo bed, and the cues that come and go over it.</summary>
    public sealed class AmbiencePack
    {
        public Soundscape scape;
        public float[] bed;
        public AmbientCue[] cues;
    }

    /// <summary>
    /// The sound of each place, synthesized: a bed that loops (traffic hum and cars going by on Home
    /// Street; a murmuring crowd, cups and pigeons in the market; waves breaking and drawing back on the
    /// beach; the hollow rumble and hum of the underpass; a diesel generator and wind on the building site;
    /// leaves and a fountain in the park; a soft breeze and birds for the menu), and the cues that come now
    /// and then over it (car horns, bicycle bells, a church bell, dogs; a shop's door bell, a clock, a cart on
    /// the cobbles; gulls, a buoy's bell, a ship; dripping water, a train overhead, footsteps; a reversing
    /// truck, a jackhammer, hammering, a digger, a drill, an air brake, dropped pipes; robins, tits, a
    /// blackbird, wood pigeons, ducks and a woodpecker). Played well under the music (AudioDirector).
    /// Pure C#: safe on a worker thread.
    /// </summary>
    public static class AmbienceGenerator
    {
        public const int Channels = 2;
        /// <summary>The bed's loudness (RMS): well under the music's <see cref="MusicGenerator.Loudness"/>.</summary>
        public const float BedLoudness = 0.075f;
        /// <summary>The park is a quiet place: its bed sits lower still, so the music carries it.</summary>
        public const float ParkBedLoudness = 0.045f;
        const double BedSeconds = 30.0;
        const double Fold = 2.0;
        const double TwoPi = Math.PI * 2.0;
        static int Sr { get { return Synth.SampleRate; } }

        public static AmbiencePack Generate(Soundscape scape)
        {
            var pack = new AmbiencePack { scape = scape };
            var cues = new List<AmbientCue>();
            switch (scape)
            {
                case Soundscape.Street: pack.bed = StreetBed(); StreetCues(cues); break;
                case Soundscape.Market: pack.bed = MarketBed(); MarketCues(cues); break;
                case Soundscape.Beach: pack.bed = BeachBed(); BeachCues(cues); break;
                case Soundscape.Underpass: pack.bed = UnderpassBed(); UnderpassCues(cues); break;
                case Soundscape.Site: pack.bed = SiteBed(); SiteCues(cues); break;
                case Soundscape.Park: pack.bed = ParkBed(); ParkCues(cues); break;
                default: pack.bed = MenuBed(); MenuCues(cues); break;
            }
            pack.cues = cues.ToArray();
            return pack;
        }

        // ================= Beds =================

        static int BedLength { get { return (int)(BedSeconds * Sr); } }

        /// <summary>A continuous layer made a little longer than the loop, then folded so its end crossfades into its start.</summary>
        static void Layer(Track into, Func<int, float> sample)
        {
            int len = into.Length, fold = (int)(Fold * Sr);
            var raw = new float[len + fold];
            for (int i = 0; i < raw.Length; i++) raw[i] = sample(i);
            for (int i = 0; i < len; i++)
            {
                float v = raw[i];
                if (i < fold)
                {
                    double a = i / (double)fold * Math.PI * 0.5;
                    v = (float)(raw[i] * Math.Sin(a) + raw[len + i] * Math.Cos(a));
                }
                into.buf[i] += v;
            }
        }

        /// <summary>Low-passed noise with a slow swell: traffic, a city's hum, room tone, surf.</summary>
        static void Rumble(Track t, int seed, double cutoff, double driftHz, float depth, bool brown = true)
        {
            var n = new NoiseSource(seed);
            var f = new Svf();
            var d = new Drift(seed + 1, driftHz);
            Layer(t, i => f.Process(brown ? n.Brown() : n.Pink(), cutoff, 0.6) * (1f - depth + depth * d.Next()));
        }

        /// <summary>Band-passed noise that gusts: wind, leaves, a fountain.</summary>
        static void Airy(Track t, int seed, double centre, double q, double gustHz, float flutter, double flutterHz)
        {
            var n = new NoiseSource(seed);
            var f = new Svf();
            var gust = new Drift(seed + 2, gustHz);
            var fl = new Drift(seed + 3, flutterHz);
            Layer(t, i =>
            {
                float g = gust.Next();
                f.Process(n.Pink(), centre * (0.8 + 0.4 * g), q);
                return f.band * (0.25f + 0.75f * g * g) * (1f - flutter + flutter * fl.Next());
            });
        }

        static float[] Finish(Mixdown mix) { return mix.Render(BedLoudness); }

        static float[] MenuBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.5f, wet = 0.15f };
            Airy(mix.Add(-0.6f, 0f), 11, 900, 0.5, 0.07, 0.2f, 3);
            Airy(mix.Add(0.6f, 0f), 12, 1100, 0.5, 0.06, 0.2f, 3);
            Rumble(mix.Add(0f, 0f, 0.4f), 13, 200, 0.05, 0.4f);
            var birds = mix.Add(0.3f, 0.3f, 0.25f);
            var rng = new Random(14);
            for (double t = 1; t < BedSeconds - 2; t += 3 + rng.NextDouble() * 4)
                Birds.Sparrow(birds, t, rng);
            return Finish(mix);
        }

        static float[] StreetBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.55f, damping = 0.6f, wet = 0.2f };
            Rumble(mix.Add(-0.7f, 0.1f), 21, 180, 0.07, 0.5f);
            Rumble(mix.Add(0.7f, 0.1f), 22, 200, 0.06, 0.5f);
            Rumble(mix.Add(0f, 0.2f, 0.35f), 23, 650, 0.1, 0.4f, false);
            Airy(mix.Add(0.4f, 0f, 0.35f), 24, 1300, 0.6, 0.08, 0.3f, 4);
            // Cars further off, going by both ways, and the odd chirp from the hedges.
            var cars = mix.Add(0f, 0.25f, 0.6f);
            double[] at = { 2, 9.5, 17, 24 };
            for (int i = 0; i < at.Length; i++) Vehicle.Pass(cars, at[i], 5 + i % 2, 0.35f, 30 + i, 0.7);
            var birds = mix.Add(-0.4f, 0.3f, 0.2f);
            var rng = new Random(25);
            for (double t = 3; t < BedSeconds - 2; t += 4 + rng.NextDouble() * 5) Birds.Sparrow(birds, t, rng);
            return Finish(mix);
        }

        static float[] MarketBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.6f, damping = 0.5f, wet = 0.28f };
            // A crowd: people talking all over the square, too many and too far to make out a word.
            var rng = new Random(31);
            for (int v = 0; v < 12; v++)
            {
                float pan = (float)(rng.NextDouble() * 1.6 - 0.8);
                var voice = mix.Add(pan, 0.5f, (float)(0.5 + rng.NextDouble() * 0.5));
                Voices.Chatter(voice, 100 + v * 7, 95 + rng.NextDouble() * 140);
            }
            Airy(mix.Add(0f, 0.4f, 0.5f), 32, 700, 0.5, 0.15, 0.5f, 6);
            Rumble(mix.Add(0f, 0.1f, 0.4f), 33, 190, 0.06, 0.4f);
            // Spoons and cups at the cafe tables, now and then.
            var cafe = mix.Add(0.5f, 0.3f, 0.35f);
            for (double t = 1.3; t < BedSeconds - 1; t += 2.5 + rng.NextDouble() * 4) Things.Clink(cafe, t, rng);
            return Finish(mix);
        }

        static float[] BeachBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.7f, damping = 0.6f, wet = 0.12f };
            // The surf further out never stops; the waves on the sand come in one by one.
            Rumble(mix.Add(-0.5f, 0.1f, 0.7f), 41, 320, 0.09, 0.5f, false);
            Rumble(mix.Add(0.5f, 0.1f, 0.7f), 42, 340, 0.08, 0.5f, false);
            Waves(mix.Add(-0.35f, 0.15f), 43, 0.0);
            Waves(mix.Add(0.35f, 0.15f), 44, 0.35);
            Airy(mix.Add(0f, 0f, 0.4f), 45, 600, 0.5, 0.1, 0.35f, 5);
            return Finish(mix);
        }

        /// <summary>Waves breaking and running up the sand, then drawing back with a hiss, every seven to ten seconds.</summary>
        static void Waves(Track t, int seed, double offset)
        {
            var n = new NoiseSource(seed);
            var lowpass = new Svf();
            var foam = new Svf();
            var rng = new Random(seed);
            int total = t.Length + (int)(Fold * Sr);
            var env = new float[total];
            var bright = new float[total];
            double at = offset * 7;
            while (at < total / (double)Sr)
            {
                double rise = 1.6 + rng.NextDouble() * 1.2, wash = 3.2 + rng.NextDouble() * 2.2;
                float size = (float)(0.6 + rng.NextDouble() * 0.4);
                int s0 = (int)(at * Sr), len = (int)((rise + wash) * Sr);
                for (int i = 0; i < len && s0 + i < total; i++)
                {
                    double tt = i / (double)Sr;
                    double e = tt < rise ? Math.Pow(tt / rise, 2.2) : Math.Exp(-(tt - rise) / (wash * 0.38));
                    double b = tt < rise ? Math.Pow(tt / rise, 3) : Math.Exp(-(tt - rise) / (wash * 0.22));
                    env[s0 + i] = Math.Max(env[s0 + i], (float)(e * size));
                    bright[s0 + i] = Math.Max(bright[s0 + i], (float)(b * size));
                }
                at += 6.5 + rng.NextDouble() * 3.5;
            }
            Layer(t, i =>
            {
                float x = n.Pink();
                float body = lowpass.Process(x, 250 + 2600 * bright[i], 0.7) * (0.15f + env[i]);
                foam.Process(x, 3800, 0.5);
                return body + foam.high * 0.5f * bright[i] * env[i];
            });
        }

        static float[] UnderpassBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.92f, damping = 0.25f, wet = 0.45f };
            Rumble(mix.Add(-0.6f, 0.4f), 51, 140, 0.05, 0.4f);
            Rumble(mix.Add(0.6f, 0.4f), 52, 150, 0.05, 0.4f);
            Rumble(mix.Add(0f, 0.5f, 0.3f), 53, 420, 0.12, 0.6f, false);
            // The strip lights' hum and buzz.
            var hum = mix.Add(-0.5f, 0.2f, 0.06f);
            var d = new Drift(54, 0.3);
            Layer(hum, i =>
            {
                double t = i / (double)Sr;
                double v = Math.Sin(TwoPi * 100 * t) + 0.5 * Math.Sin(TwoPi * 200 * t) + 0.35 * Math.Sin(TwoPi * 300 * t) + 0.15 * Math.Sin(TwoPi * 500 * t);
                return (float)v * (0.7f + 0.3f * d.Next());
            });
            // Cars on the road above, muffled through the deck.
            var above = mix.Add(0f, 0.6f, 0.4f);
            for (int i = 0; i < 3; i++) Vehicle.Pass(above, 3 + i * 9.5, 6, 0.3f, 55 + i, 0.25);
            return Finish(mix);
        }

        static float[] SiteBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.6f, damping = 0.5f, wet = 0.2f };
            Machines.Diesel(mix.Add(-0.55f, 0.2f, 0.8f), 61, 29, 0.0);
            Machines.Diesel(mix.Add(0.6f, 0.35f, 0.35f), 62, 36, 0.4);
            Airy(mix.Add(-0.3f, 0f, 0.5f), 63, 700, 0.5, 0.09, 0.3f, 4);
            Airy(mix.Add(0.3f, 0f, 0.45f), 64, 950, 0.5, 0.08, 0.3f, 4);
            Rumble(mix.Add(0f, 0.1f, 0.4f), 65, 200, 0.05, 0.4f);
            return Finish(mix);
        }

        static float[] ParkBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.65f, damping = 0.5f, wet = 0.2f };
            // Leaves: a soft, low rustle that comes and goes with the breeze, well behind the music, the
            // fountain and the birds (a bright, fluttering hiss here drowned everything else out).
            Airy(mix.Add(-0.65f, 0f, 0.3f), 71, 1300, 0.7, 0.08, 0.2f, 3.5);
            Airy(mix.Add(0.65f, 0f, 0.3f), 72, 1500, 0.7, 0.07, 0.2f, 3.5);
            // The fountain by the pond: a steady splash with a trickle in it.
            var fountain = mix.Add(0.55f, 0.3f, 0.35f);
            var n = new NoiseSource(73);
            var f = new Svf();
            var trickle = new Drift(74, 14);
            Layer(fountain, i => { f.Process(n.White(), 1700, 0.7); return f.band * (0.6f + 0.4f * trickle.Next()); });
            Rumble(mix.Add(0f, 0.1f, 0.3f), 75, 180, 0.05, 0.4f);
            var birds = mix.Add(-0.3f, 0.35f, 0.5f);
            var rng = new Random(76);
            for (double t = 1; t < BedSeconds - 2; t += 2.5 + rng.NextDouble() * 3) Birds.Sparrow(birds, t, rng);
            return mix.Render(ParkBedLoudness);
        }

        // ================= Cues =================

        /// <summary>Render a one-shot through a small mix (a touch of the place's reverb), padded for its tail.</summary>
        static AmbientCue Cue(string name, double seconds, float reverb, float room, Action<Track, Random> draw, int seed,
            float minGap, float maxGap, float volume, float pan, float panSpread, float pitchVariance = 0.06f, bool sweep = false)
        {
            int len = (int)((seconds + (reverb > 0f ? 0.4 + room * 2.2 : 0.05)) * Sr);
            var mix = new Mixdown(len) { roomSize = room, damping = 0.4f, wet = reverb };
            var tr = mix.Add(0f, 1f);
            draw(tr, new Random(seed));
            var clip = mix.Render(0f, 0.6f);
            FadeEdges(clip);
            return new AmbientCue
            {
                name = name, clip = clip, minGap = minGap, maxGap = maxGap, volume = volume,
                pan = pan, panSpread = panSpread, pitchVariance = pitchVariance, sweep = sweep,
            };
        }

        static void FadeEdges(float[] stereo)
        {
            int frames = stereo.Length / 2, fade = Math.Min(frames / 4, (int)(0.03 * Sr));
            for (int i = 0; i < fade; i++)
            {
                float k = i / (float)fade;
                stereo[2 * (frames - 1 - i)] *= k;
                stereo[2 * (frames - 1 - i) + 1] *= k;
            }
        }

        static void MenuCues(List<AmbientCue> c)
        {
            c.Add(Cue("robin", 2.4, 0.2f, 0.5f, (t, r) => Birds.Robin(t, 0.1, r), 101, 7, 16, 0.32f, 0.3f, 0.6f));
            c.Add(Cue("tit", 2.2, 0.2f, 0.5f, (t, r) => Birds.Tit(t, 0.1, r), 102, 10, 22, 0.26f, -0.3f, 0.6f));
        }

        static void StreetCues(List<AmbientCue> c)
        {
            c.Add(Cue("car", 6, 0.15f, 0.5f, (t, r) => Vehicle.Pass(t, 0, 5.5, 1f, r.Next(), 1.0), 201, 7, 15, 0.55f, 0f, 0f, 0.08f, true));
            c.Add(Cue("van", 7, 0.15f, 0.5f, (t, r) => Vehicle.Pass(t, 0, 6.5, 1f, r.Next(), 0.75), 202, 18, 34, 0.5f, 0f, 0f, 0.06f, true));
            c.Add(Cue("horn", 1.2, 0.3f, 0.6f, (t, r) => Vehicle.Horn(t, 0.1, r), 203, 25, 50, 0.22f, 0.4f, 0.5f));
            c.Add(Cue("bicycle", 1.4, 0.2f, 0.5f, (t, r) => Things.BicycleBell(t, 0.05), 204, 28, 55, 0.24f, -0.3f, 0.5f));
            c.Add(Cue("dog", 1.5, 0.35f, 0.6f, (t, r) => Animals.Bark(t, 0.1, r, 2), 205, 22, 45, 0.2f, 0.5f, 0.4f, 0.1f));
            c.Add(Cue("church", 7.5, 0.4f, 0.8f, (t, r) => Things.ChurchBell(t, 0.05, 3), 206, 50, 90, 0.2f, -0.5f, 0.2f, 0f));
            c.Add(Cue("sparrows", 2.5, 0.2f, 0.5f, (t, r) => { Birds.Sparrow(t, 0.1, r); Birds.Sparrow(t, 1.2, r); }, 207, 6, 13, 0.24f, 0f, 0.8f));
            c.Add(Cue("pigeon", 3, 0.2f, 0.5f, (t, r) => Birds.WoodPigeon(t, 0.1), 208, 26, 48, 0.2f, 0.5f, 0.4f, 0.04f));
        }

        static void MarketCues(List<AmbientCue> c)
        {
            c.Add(Cue("shopBell", 1.6, 0.25f, 0.5f, (t, r) => Things.ShopBell(t, 0.05, r), 301, 12, 24, 0.26f, 0f, 0.8f));
            c.Add(Cue("cart", 3.2, 0.2f, 0.5f, (t, r) => Things.Cart(t, 0.05, 3, r), 302, 18, 34, 0.32f, 0f, 0f, 0.06f, true));
            c.Add(Cue("pigeons", 3, 0.2f, 0.5f, (t, r) => { Birds.Pigeon(t, 0.1); Animals.Wings(t, 1.6, r); }, 303, 14, 28, 0.3f, 0f, 0.7f));
            c.Add(Cue("clock", 6, 0.45f, 0.8f, (t, r) => Things.ClockChime(t, 0.05), 304, 55, 95, 0.18f, 0.4f, 0.3f, 0f));
            c.Add(Cue("bicycle", 1.4, 0.2f, 0.5f, (t, r) => Things.BicycleBell(t, 0.05), 305, 26, 50, 0.22f, 0f, 0.7f));
            c.Add(Cue("laugh", 1.2, 0.3f, 0.5f, (t, r) => Voices.Laugh(t, 0.05, r), 306, 16, 30, 0.16f, 0f, 0.8f, 0.12f));
            c.Add(Cue("van", 6, 0.2f, 0.5f, (t, r) => Vehicle.Pass(t, 0, 5.5, 1f, r.Next(), 0.6), 307, 28, 50, 0.35f, 0f, 0f, 0.06f, true));
        }

        static void BeachCues(List<AmbientCue> c)
        {
            c.Add(Cue("gull", 1.6, 0.2f, 0.6f, (t, r) => Birds.Gull(t, 0.05, r, 1 + r.Next(3)), 401, 4, 10, 0.32f, 0f, 0.8f, 0.08f));
            c.Add(Cue("gullLaugh", 2.2, 0.2f, 0.6f, (t, r) => Birds.GullLaugh(t, 0.05, r), 402, 9, 20, 0.28f, 0f, 0.8f, 0.08f));
            c.Add(Cue("gullFar", 1.6, 0.45f, 0.8f, (t, r) => Birds.Gull(t, 0.05, r, 2), 403, 6, 14, 0.14f, 0f, 0.9f, 0.1f));
            c.Add(Cue("buoy", 6, 0.35f, 0.8f, (t, r) => Things.BuoyBell(t, 0.05, r), 404, 35, 65, 0.16f, -0.6f, 0.3f, 0.03f));
            c.Add(Cue("ship", 5, 0.5f, 0.9f, (t, r) => Things.ShipHorn(t, 0.1), 405, 70, 130, 0.14f, 0.6f, 0.3f, 0.02f));
            c.Add(Cue("splash", 1.2, 0.15f, 0.5f, (t, r) => Things.Splash(t, 0.05, r), 406, 15, 32, 0.18f, 0f, 0.8f));
        }

        static void UnderpassCues(List<AmbientCue> c)
        {
            c.Add(Cue("drip", 0.5, 0.6f, 0.9f, (t, r) => Things.Drip(t, 0.02, r), 501, 2.5f, 7, 0.3f, 0f, 0.9f, 0.15f));
            c.Add(Cue("train", 9, 0.4f, 0.9f, (t, r) => Vehicle.Train(t, 0.1, 8.5, r), 502, 30, 55, 0.6f, 0f, 0f, 0.04f, true));
            c.Add(Cue("steps", 4, 0.55f, 0.9f, (t, r) => Things.Footsteps(t, 0.1, 6, r), 503, 18, 34, 0.24f, 0f, 0.8f, 0.06f));
            c.Add(Cue("flutter", 1.5, 0.5f, 0.9f, (t, r) => Animals.Wings(t, 0.05, r), 504, 30, 60, 0.2f, 0f, 0.8f));
            c.Add(Cue("hornEcho", 1.2, 0.6f, 0.95f, (t, r) => Vehicle.Horn(t, 0.1, r), 505, 35, 70, 0.14f, 0f, 0.8f));
            c.Add(Cue("car", 6, 0.55f, 0.9f, (t, r) => Vehicle.Pass(t, 0, 5.5, 1f, r.Next(), 0.6), 506, 12, 24, 0.35f, 0f, 0f, 0.06f, true));
        }

        static void SiteCues(List<AmbientCue> c)
        {
            c.Add(Cue("reversing", 6.5, 0.25f, 0.6f, (t, r) => Machines.Reversing(t, 0.05, 7), 601, 22, 40, 0.24f, 0.5f, 0.4f, 0.02f));
            c.Add(Cue("jackhammer", 3, 0.25f, 0.6f, (t, r) => Machines.Jackhammer(t, 0.05, 1.6 + r.NextDouble() * 1.2, r), 602, 10, 22, 0.32f, -0.4f, 0.5f, 0.05f));
            c.Add(Cue("hammer", 3.6, 0.3f, 0.6f, (t, r) => Machines.Hammering(t, 0.05, 4 + r.Next(4), r), 603, 8, 17, 0.32f, 0f, 0.8f, 0.06f));
            c.Add(Cue("digger", 5, 0.25f, 0.6f, (t, r) => Machines.Digger(t, 0.05), 604, 25, 45, 0.38f, 0.3f, 0.5f, 0.05f));
            c.Add(Cue("drill", 3, 0.25f, 0.6f, (t, r) => Machines.Drill(t, 0.05, r), 605, 20, 40, 0.18f, 0f, 0.8f, 0.06f));
            c.Add(Cue("airBrake", 1.4, 0.3f, 0.6f, (t, r) => Machines.AirBrake(t, 0.05, r), 606, 35, 70, 0.22f, 0f, 0.8f));
            c.Add(Cue("pipes", 2.2, 0.3f, 0.6f, (t, r) => Machines.Pipes(t, 0.05, r), 607, 40, 75, 0.28f, 0f, 0.8f, 0.05f));
            c.Add(Cue("truck", 7, 0.2f, 0.6f, (t, r) => Vehicle.Pass(t, 0, 6.5, 1f, r.Next(), 0.55), 608, 25, 45, 0.45f, 0f, 0f, 0.04f, true));
        }

        static void ParkCues(List<AmbientCue> c)
        {
            c.Add(Cue("robin", 2.4, 0.2f, 0.6f, (t, r) => Birds.Robin(t, 0.1, r), 701, 4, 9, 0.3f, 0f, 0.9f));
            c.Add(Cue("tit", 2.2, 0.2f, 0.6f, (t, r) => Birds.Tit(t, 0.1, r), 702, 5, 12, 0.26f, 0f, 0.9f));
            c.Add(Cue("blackbird", 3, 0.25f, 0.6f, (t, r) => Birds.Blackbird(t, 0.1, r), 703, 8, 18, 0.3f, 0f, 0.9f));
            c.Add(Cue("woodpigeon", 3, 0.25f, 0.6f, (t, r) => Birds.WoodPigeon(t, 0.1), 704, 16, 32, 0.24f, 0f, 0.8f, 0.04f));
            c.Add(Cue("ducks", 1.6, 0.2f, 0.6f, (t, r) => Animals.Quacks(t, 0.05, r), 705, 15, 30, 0.24f, 0.5f, 0.4f, 0.08f));
            c.Add(Cue("woodpecker", 1.4, 0.35f, 0.7f, (t, r) => Birds.Woodpecker(t, 0.05, r), 706, 30, 60, 0.18f, -0.5f, 0.4f, 0.06f));
            c.Add(Cue("dog", 1.5, 0.35f, 0.6f, (t, r) => Animals.Bark(t, 0.1, r, 1 + r.Next(2)), 707, 25, 50, 0.16f, 0f, 0.8f, 0.1f));
            c.Add(Cue("bicycle", 1.4, 0.2f, 0.5f, (t, r) => Things.BicycleBell(t, 0.05), 708, 30, 60, 0.2f, 0f, 0.8f));
        }

        // ================= Sound makers =================

        static int At(double seconds) { return (int)(seconds * Sr); }

        /// <summary>A whistled note sliding from one pitch to another, with an optional trill.</summary>
        static void Whistle(Track t, double at, double dur, double f0, double f1, float amp, double trillHz = 0, double trillDepth = 0, double curve = 1)
        {
            int s = At(at), n = At(dur);
            double ph = 0;
            for (int i = 0; i < n; i++)
            {
                double u = i / (double)n;
                double f = f0 + (f1 - f0) * Math.Pow(u, curve);
                if (trillHz > 0) f *= 1 + trillDepth * Math.Sin(TwoPi * trillHz * i / Sr);
                f = Math.Min(f, Sr * 0.45);
                ph += f / Sr;
                double env = Math.Sin(Math.PI * u);
                t.Add(s + i, (float)(Math.Sin(TwoPi * ph) * env * env) * amp);
            }
        }

        /// <summary>A buzzy, voiced sound shaped by two formants: barks, quacks, gulls, voices.</summary>
        static void Formant(Track t, double at, double dur, Func<double, double> pitch, double f1, double f2, float amp, double noise, int seed,
            double attack = 0.01, double releaseShape = 1.5, double rough = 0)
        {
            int s = At(at), n = At(dur);
            var a = new Svf();
            var b = new Svf();
            var ns = new NoiseSource(seed);
            double ph = 0;
            for (int i = 0; i < n; i++)
            {
                double u = i / (double)n, tt = i / (double)Sr;
                ph += pitch(u) / Sr;
                double p = ph - Math.Floor(ph);
                double src = (2 * p - 1) * (1 - noise) + ns.White() * noise;
                if (rough > 0) src *= 1 - rough * (0.5 + 0.5 * Math.Sin(TwoPi * 75 * tt));
                a.Process((float)src, f1, 4);
                b.Process((float)src, f2, 5);
                double env = Math.Min(1, tt / attack) * Math.Pow(1 - u, releaseShape);
                t.Add(s + i, (float)((a.band + b.band * 0.7) * env) * amp);
            }
        }

        static void NoiseBurst(Track t, double at, double dur, double centre, double q, float amp, int seed, double attack = 0.002, double decay = 30, bool high = false)
        {
            int s = At(at), n = At(dur);
            var f = new Svf();
            var ns = new NoiseSource(seed);
            for (int i = 0; i < n; i++)
            {
                double tt = i / (double)Sr;
                f.Process(ns.White(), centre, q);
                double env = Math.Min(1, tt / attack) * Math.Exp(-tt * decay) * Math.Min(1, (n - i) / (0.01 * Sr));
                t.Add(s + i, (float)((high ? f.high : f.band) * env) * amp);
            }
        }

        /// <summary>A struck metal or bell: inharmonic partials, each with its own decay.</summary>
        static void Strike(Track t, double at, double freq, double[] ratios, double[] amps, double decay, float gain, double dur)
        {
            int s = At(at), n = At(dur);
            for (int k = 0; k < ratios.Length; k++)
            {
                double f = freq * ratios[k];
                if (f > Sr * 0.45) continue;
                double ph = 0, d = decay * (1 + k * 0.5);
                for (int i = 0; i < n; i++)
                {
                    double tt = i / (double)Sr;
                    ph += f / Sr;
                    double fade = Math.Min(1, (n - i) / (0.03 * Sr));
                    t.Add(s + i, (float)(Math.Sin(TwoPi * ph) * Math.Exp(-tt * d) * Math.Min(1, tt / 0.001) * fade * amps[k]) * gain);
                }
            }
        }

        static class Birds
        {
            public static void Sparrow(Track t, double at, Random r)
            {
                int chirps = 2 + r.Next(4);
                for (int i = 0; i < chirps; i++)
                {
                    double f = 3600 + r.NextDouble() * 1400;
                    Whistle(t, at + i * (0.11 + r.NextDouble() * 0.06), 0.05 + r.NextDouble() * 0.03, f, f * (0.75 + r.NextDouble() * 0.15), 0.5f, 0, 0, 0.6);
                }
            }

            /// <summary>A robin's wistful warble: quick runs of high slides and trills, rising and falling.</summary>
            public static void Robin(Track t, double at, Random r)
            {
                double time = at;
                int notes = 8 + r.Next(6);
                for (int i = 0; i < notes; i++)
                {
                    double f = 2800 + r.NextDouble() * 3200;
                    double d = 0.04 + r.NextDouble() * 0.09;
                    bool trill = r.NextDouble() < 0.3;
                    Whistle(t, time, d, f, f * (0.7 + r.NextDouble() * 0.6), 0.45f, trill ? 60 : 0, trill ? 0.06 : 0);
                    time += d + 0.02 + r.NextDouble() * 0.05;
                }
            }

            /// <summary>A great tit's "tea-cher, tea-cher, tea-cher".</summary>
            public static void Tit(Track t, double at, Random r)
            {
                double hi = 5200 + r.NextDouble() * 600, lo = hi * 0.72;
                int reps = 3 + r.Next(2);
                for (int i = 0; i < reps; i++)
                {
                    double s = at + i * 0.38;
                    Whistle(t, s, 0.11, hi, hi * 0.97, 0.45f);
                    Whistle(t, s + 0.14, 0.13, lo, lo * 0.9, 0.4f);
                }
            }

            /// <summary>A blackbird's fluting phrase: low, mellow whistles with glides, and a squeaky flourish.</summary>
            public static void Blackbird(Track t, double at, Random r)
            {
                double time = at;
                int notes = 4 + r.Next(3);
                for (int i = 0; i < notes; i++)
                {
                    double f = 1600 + r.NextDouble() * 1100;
                    double d = 0.12 + r.NextDouble() * 0.2;
                    Whistle(t, time, d, f, f * (0.85 + r.NextDouble() * 0.35), 0.5f, 7, 0.015, 0.8);
                    time += d + 0.04;
                }
                for (int i = 0; i < 3; i++) Whistle(t, time + i * 0.05, 0.04, 5200 + i * 500, 4400, 0.25f);
            }

            /// <summary>A wood pigeon's soft "coo-COO-coo, coo-coo".</summary>
            public static void WoodPigeon(Track t, double at)
            {
                double[] times = { 0, 0.42, 1.0, 1.45, 1.8 };
                double[] durs = { 0.35, 0.5, 0.3, 0.28, 0.28 };
                double[] amps = { 0.6, 1, 0.7, 0.6, 0.6 };
                for (int i = 0; i < times.Length; i++)
                    Formant(t, at + times[i], durs[i], u => 430 + 40 * Math.Sin(Math.PI * u), 450, 900, (float)amps[i] * 0.5f, 0.02, 7 + i, 0.05, 0.6);
            }

            /// <summary>A town pigeon's throaty "croo-croo-croooo".</summary>
            public static void Pigeon(Track t, double at)
            {
                for (int i = 0; i < 3; i++)
                    Formant(t, at + i * 0.45, i == 2 ? 0.6 : 0.32, u => 360 + 60 * Math.Sin(Math.PI * u) - (i == 2 ? 60 * u : 0), 420, 850, 0.5f, 0.05, 30 + i, 0.04, 0.8, 0.4);
            }

            /// <summary>A herring gull's "kyow": a harsh, falling cry, one to three times.</summary>
            public static void Gull(Track t, double at, Random r, int calls)
            {
                for (int i = 0; i < calls; i++)
                {
                    double peak = 1400 + r.NextDouble() * 400, d = 0.32 + r.NextDouble() * 0.15;
                    Formant(t, at + i * (d + 0.08), d, u => u < 0.25 ? peak * (0.75 + u) : peak * (1.0 - 0.45 * (u - 0.25)), 1900, 3300, 0.55f, 0.18, r.Next(), 0.02, 0.9, 0.35);
                }
            }

            /// <summary>A gull's laugh: "ha-ha-ha-ha-haa", quick and falling.</summary>
            public static void GullLaugh(Track t, double at, Random r)
            {
                int n = 5 + r.Next(4);
                double f = 1600 + r.NextDouble() * 300;
                for (int i = 0; i < n; i++)
                {
                    double ff = f * (1 - i * 0.03);
                    Formant(t, at + i * 0.17, 0.12, u => ff * (1 - 0.15 * u), 1800, 3100, 0.5f, 0.2, r.Next(), 0.01, 1.2, 0.3);
                }
            }

            /// <summary>A woodpecker drumming on a trunk: a fast roll of knocks, slowing as it fades.</summary>
            public static void Woodpecker(Track t, double at, Random r)
            {
                double time = at, gap = 0.045;
                for (int i = 0; i < 18; i++)
                {
                    NoiseBurst(t, time, 0.03, 1100, 3, 0.8f * (float)Math.Pow(0.95, i), r.Next(), 0.0008, 120);
                    time += gap;
                    gap *= 1.02;
                }
            }
        }

        static class Animals
        {
            public static void Bark(Track t, double at, Random r, int barks)
            {
                for (int i = 0; i < barks; i++)
                {
                    double f = 380 + r.NextDouble() * 120;
                    Formant(t, at + i * (0.28 + r.NextDouble() * 0.1), 0.17, u => f * (1.15 - 0.35 * u), 800, 1700, 0.7f, 0.25, r.Next(), 0.008, 1.4, 0.2);
                }
            }

            public static void Quacks(Track t, double at, Random r)
            {
                int n = 2 + r.Next(3);
                for (int i = 0; i < n; i++)
                {
                    double f = 260 + r.NextDouble() * 60;
                    Formant(t, at + i * (0.2 + r.NextDouble() * 0.12), 0.16, u => f * (1.1 - 0.3 * u), 1150, 2200, 0.6f, 0.15, r.Next(), 0.01, 1.0, 0.5);
                }
            }

            /// <summary>Wings clapping as a bird takes off.</summary>
            public static void Wings(Track t, double at, Random r)
            {
                int flaps = 7 + r.Next(4);
                for (int i = 0; i < flaps; i++)
                    NoiseBurst(t, at + i * 0.1, 0.09, 900 + r.NextDouble() * 500, 0.8, (float)(0.6 * Math.Pow(0.9, i)), r.Next(), 0.01, 28);
            }
        }

        static class Voices
        {
            /// <summary>One person talking on and off for the whole loop: phrases of syllables (a buzz shaped into
            /// vowels) with the rise and fall of speech, and pauses between. Muffled: a crowd, not words.</summary>
            public static void Chatter(Track t, int seed, double f0)
            {
                var r = new Random(seed);
                var n = new NoiseSource(seed);
                var fa = new Svf();
                var fb = new Svf();
                var lp = new Svf();
                int total = t.Length + (int)(Fold * Sr);
                var amp = new float[total];
                var form1 = new float[total];
                var form2 = new float[total];
                var pitch = new float[total];
                double time = r.NextDouble() * 2;
                while (time < total / (double)Sr)
                {
                    double phrase = 1.2 + r.NextDouble() * 2.5;
                    double end = time + phrase;
                    double inflect = r.NextDouble() < 0.5 ? 1.15 : 0.9;
                    while (time < end)
                    {
                        double syl = 0.09 + r.NextDouble() * 0.16;
                        double v1 = 300 + r.NextDouble() * 500, v2 = 900 + r.NextDouble() * 1300;
                        int s0 = (int)(time * Sr), len = (int)(syl * Sr);
                        double pf = f0 * (1 + (inflect - 1) * ((time - (end - phrase)) / phrase)) * (0.95 + r.NextDouble() * 0.1);
                        float loud = (float)(0.5 + r.NextDouble() * 0.5);
                        for (int i = 0; i < len && s0 + i < total; i++)
                        {
                            double u = i / (double)len;
                            amp[s0 + i] = (float)(Math.Sin(Math.PI * u) * loud);
                            form1[s0 + i] = (float)v1;
                            form2[s0 + i] = (float)v2;
                            pitch[s0 + i] = (float)pf;
                        }
                        time += syl + r.NextDouble() * 0.03;
                    }
                    time += 0.4 + r.NextDouble() * 2.2;
                }
                double ph = 0;
                Layer(t, i =>
                {
                    if (amp[i] <= 0f) { lp.Process(0f, 1500, 0.7); return lp.low; }
                    ph += pitch[i] / Sr;
                    double p = ph - Math.Floor(ph);
                    float src = (float)((2 * p - 1) * 0.7 + n.White() * 0.3);
                    fa.Process(src, Math.Round(form1[i] / 50) * 50, 5);
                    fb.Process(src, Math.Round(form2[i] / 50) * 50, 6);
                    return lp.Process((fa.band + fb.band * 0.5f) * amp[i], 1500, 0.7);
                });
            }

            public static void Laugh(Track t, double at, Random r)
            {
                int n = 4 + r.Next(3);
                double f = 220 + r.NextDouble() * 120;
                for (int i = 0; i < n; i++)
                {
                    double ff = f * (1.1 - i * 0.04);
                    Formant(t, at + i * 0.15, 0.1, u => ff, 750, 1250, 0.6f, 0.4, r.Next(), 0.01, 1.2);
                }
            }
        }

        static class Vehicle
        {
            /// <summary>A car (or with a lower engine, a van or truck) going by: tyres on the road and an engine,
            /// both loudest and brightest as it passes, the engine's note dropping as it goes (the Doppler shift).</summary>
            public static void Pass(Track t, double at, double dur, float gain, int seed, double engine)
            {
                int s = At(at), n = At(dur);
                var ns = new NoiseSource(seed);
                var tyres = new Svf();
                var eng = new Svf();
                double ph = 0;
                double baseHz = 38 + 22 * engine;
                for (int i = 0; i < n; i++)
                {
                    double u = i / (double)n;
                    double x = (u - 0.5) * 6;
                    double near = 1.0 / (1 + x * x);
                    double doppler = 1 + 0.08 * Math.Tanh(-x * 1.5);
                    ph += baseHz * doppler / Sr;
                    double p = ph - Math.Floor(ph);
                    double e = eng.Process((float)((p < 0.3 ? 1 : -1) + ns.White() * 0.3), 220 + 500 * near, 1.2);
                    double tyre = tyres.Process(ns.Pink(), 380 + 1500 * near, 0.6);
                    double env = near * Math.Min(1, u * 8) * Math.Min(1, (1 - u) * 8);
                    t.Add(s + i, (float)((tyre * 1.4 + e * 0.45 * engine) * env) * gain);
                }
            }

            /// <summary>Two short honks on a car's horn.</summary>
            public static void Horn(Track t, double at, Random r)
            {
                int honks = 1 + r.Next(2);
                for (int h = 0; h < honks; h++)
                {
                    int s = At(at + h * 0.32), n = At(h == honks - 1 ? 0.38 : 0.18);
                    var f = new Svf();
                    double p1 = 0, p2 = 0;
                    for (int i = 0; i < n; i++)
                    {
                        double tt = i / (double)Sr;
                        p1 += 415.0 / Sr;
                        p2 += 523.0 / Sr;
                        double sq = ((p1 - Math.Floor(p1)) < 0.5 ? 1 : -1) + ((p2 - Math.Floor(p2)) < 0.5 ? 1 : -1);
                        double env = Math.Min(1, tt / 0.01) * Math.Min(1, (n - i) / (0.02 * Sr));
                        t.Add(s + i, f.Process((float)sq, 1800, 0.9) * (float)env * 0.5f);
                    }
                }
            }

            /// <summary>A train crossing the bridge overhead: a swelling rumble, and the wheels' clack-clack over the rail joints.</summary>
            public static void Train(Track t, double at, double dur, Random r)
            {
                int s = At(at), n = At(dur);
                var ns = new NoiseSource(r.Next());
                var lp = new Svf();
                var mid = new Svf();
                for (int i = 0; i < n; i++)
                {
                    double u = i / (double)n;
                    double env = Math.Pow(Math.Sin(Math.PI * u), 0.8);
                    double rumble = lp.Process(ns.Brown(), 110, 0.8) * 1.6;
                    mid.Process(ns.Pink(), 500 + 300 * env, 0.7);
                    t.Add(s + i, (float)((rumble + mid.band * 0.6) * env) * 0.8f);
                }
                // A pair of bogies at each end of every carriage: clack-clack ... clack-clack.
                double time = at + 0.6;
                while (time < at + dur - 0.5)
                {
                    double u = (time - at) / dur;
                    float g = (float)Math.Pow(Math.Sin(Math.PI * u), 1.2) * 0.9f;
                    NoiseBurst(t, time, 0.08, 600, 1.5, g, r.Next(), 0.001, 45);
                    NoiseBurst(t, time + 0.13, 0.08, 560, 1.5, g * 0.9f, r.Next(), 0.001, 45);
                    time += 0.85 + r.NextDouble() * 0.1;
                }
            }
        }

        static class Things
        {
            public static void Clink(Track t, double at, Random r)
            {
                double f = 2600 + r.NextDouble() * 1400;
                Strike(t, at, f, new[] { 1.0, 1.52, 2.4 }, new[] { 1.0, 0.5, 0.3 }, 18, 0.25f, 0.3);
                if (r.NextDouble() < 0.5) Strike(t, at + 0.09, f * 1.07, new[] { 1.0, 1.52 }, new[] { 1.0, 0.4 }, 22, 0.15f, 0.25);
            }

            public static void BicycleBell(Track t, double at)
            {
                for (int i = 0; i < 2; i++)
                {
                    double s = at + i * 0.32;
                    Strike(t, s, 2650, new[] { 1.0, 1.48, 2.1 }, new[] { 1.0, 0.6, 0.3 }, 3.5, 0.3f, 1.0);
                    Strike(t, s + 0.06, 2650, new[] { 1.0, 1.48, 2.1 }, new[] { 1.0, 0.6, 0.3 }, 3.5, 0.22f, 0.9);
                }
            }

            /// <summary>A church bell tolling in the distance (hum, prime, minor third, fifth and nominal partials).</summary>
            public static void ChurchBell(Track t, double at, int strokes)
            {
                double[] ratio = { 0.5, 1.0, 1.2, 1.5, 2.0, 2.5 };
                double[] amp = { 0.6, 1.0, 0.7, 0.4, 0.5, 0.2 };
                for (int i = 0; i < strokes; i++) Strike(t, at + i * 2.2, 311, ratio, amp, 0.9, 0.3f, 4.5);
            }

            /// <summary>A market clock striking the quarter: four notes.</summary>
            public static void ClockChime(Track t, double at)
            {
                double[] notes = { 659, 523, 587, 392 };
                for (int i = 0; i < notes.Length; i++)
                    Strike(t, at + i * 0.9, notes[i], new[] { 1.0, 2.0, 2.4, 3.0, 4.2 }, new[] { 1.0, 0.5, 0.3, 0.2, 0.1 }, 1.4, 0.3f, 2.6);
            }

            /// <summary>The little bell on a shop's door, swinging as the door opens.</summary>
            public static void ShopBell(Track t, double at, Random r)
            {
                int hits = 4 + r.Next(3);
                for (int i = 0; i < hits; i++)
                    Strike(t, at + i * (0.07 + r.NextDouble() * 0.03), 1960 + r.NextDouble() * 60, new[] { 1.0, 2.6, 4.1 }, new[] { 1.0, 0.4, 0.2 }, 5, 0.25f * (float)Math.Pow(0.82, i), 0.8);
            }

            /// <summary>A trolley rattling over the cobbles.</summary>
            public static void Cart(Track t, double at, double dur, Random r)
            {
                double time = at;
                while (time < at + dur)
                {
                    double u = (time - at) / dur;
                    float g = (float)Math.Sin(Math.PI * u);
                    NoiseBurst(t, time, 0.05, 700 + r.NextDouble() * 400, 1.0, g * (0.4f + (float)r.NextDouble() * 0.4f), r.Next(), 0.001, 70);
                    time += 0.05 + r.NextDouble() * 0.05;
                }
            }

            /// <summary>A buoy's bell rocking on the swell: irregular strokes.</summary>
            public static void BuoyBell(Track t, double at, Random r)
            {
                double time = at;
                for (int i = 0; i < 3; i++)
                {
                    Strike(t, time, 520, new[] { 1.0, 2.0, 2.76, 3.9 }, new[] { 1.0, 0.5, 0.4, 0.2 }, 1.3, 0.3f, 3);
                    time += 1.1 + r.NextDouble() * 0.9;
                }
            }

            public static void ShipHorn(Track t, double at)
            {
                int s = At(at), n = At(3.6);
                double p = 0;
                var f = new Svf();
                for (int i = 0; i < n; i++)
                {
                    double tt = i / (double)Sr;
                    p += 98.0 / Sr;
                    double saw = 2 * (p - Math.Floor(p)) - 1;
                    double env = Math.Min(1, tt / 0.3) * Math.Min(1, (n - i) / (0.6 * Sr));
                    t.Add(s + i, f.Process((float)saw, 500, 1.0) * (float)env * 0.6f);
                }
            }

            public static void Splash(Track t, double at, Random r)
            {
                NoiseBurst(t, at, 0.8, 1400, 0.6, 0.6f, r.Next(), 0.005, 6);
                for (int i = 0; i < 5; i++)
                    Whistle(t, at + 0.08 + i * 0.06 + r.NextDouble() * 0.04, 0.04, 900 + r.NextDouble() * 900, 1800 + r.NextDouble() * 900, 0.2f);
            }

            /// <summary>A drop of water falling into a puddle: a quick rising "plink".</summary>
            public static void Drip(Track t, double at, Random r)
            {
                double f = 900 + r.NextDouble() * 700;
                Whistle(t, at, 0.06, f, f * 1.9, 0.6f, 0, 0, 0.5);
                NoiseBurst(t, at, 0.02, 3000, 1, 0.15f, r.Next(), 0.0005, 200);
            }

            /// <summary>Someone's shoes walking by: heel then toe on concrete.</summary>
            public static void Footsteps(Track t, double at, int steps, Random r)
            {
                for (int i = 0; i < steps; i++)
                {
                    double s = at + i * (0.5 + r.NextDouble() * 0.05);
                    float g = (float)Math.Sin(Math.PI * (i + 0.5) / steps);
                    NoiseBurst(t, s, 0.05, 2200, 1.2, 0.5f * g, r.Next(), 0.0008, 90);
                    NoiseBurst(t, s, 0.08, 250, 1.0, 0.6f * g, r.Next(), 0.002, 50);
                    NoiseBurst(t, s + 0.07, 0.04, 1500, 1.2, 0.25f * g, r.Next(), 0.001, 100);
                }
            }
        }

        static class Machines
        {
            /// <summary>A diesel engine ticking over: a pulse for every firing, a low throb and a rattle.</summary>
            public static void Diesel(Track t, int seed, double hz, double phaseOffset)
            {
                var ns = new NoiseSource(seed);
                var body = new Svf();
                var rattle = new Svf();
                var wander = new Drift(seed + 9, 0.2);
                double ph = phaseOffset;
                Layer(t, i =>
                {
                    double f = hz * (0.97 + 0.06 * wander.Next());
                    ph += f / Sr;
                    double p = ph - Math.Floor(ph);
                    double pulse = Math.Exp(-p * 9) * (0.8 + 0.4 * ns.Value());
                    body.Process((float)pulse, 160, 1.5);
                    rattle.Process((float)(ns.White() * pulse), 1200, 1.0);
                    return body.low * 1.2f + body.band * 0.6f + rattle.band * 0.25f;
                });
            }

            /// <summary>A lorry backing up: the reversing alarm beeping over its engine.</summary>
            public static void Reversing(Track t, double at, int beeps)
            {
                for (int b = 0; b < beeps; b++)
                {
                    int s = At(at + b * 0.9), n = At(0.45);
                    double p = 0;
                    for (int i = 0; i < n; i++)
                    {
                        double tt = i / (double)Sr;
                        p += 1050.0 / Sr;
                        double sq = (p - Math.Floor(p)) < 0.5 ? 1 : -1;
                        double env = Math.Min(1, tt / 0.01) * Math.Min(1, (n - i) / (0.01 * Sr));
                        t.Add(s + i, (float)(sq * 0.25 + Math.Sin(TwoPi * p) * 0.4) * (float)env * 0.6f);
                    }
                }
                Engine(t, at, beeps * 0.9, 34, 34, 0.35f, 4);
            }

            static void Engine(Track t, double at, double dur, double hz0, double hz1, float gain, int seed)
            {
                int s = At(at), n = At(dur);
                var ns = new NoiseSource(seed);
                var f = new Svf();
                double ph = 0;
                for (int i = 0; i < n; i++)
                {
                    double u = i / (double)n;
                    double hz = hz0 + (hz1 - hz0) * Math.Sin(Math.PI * u);
                    ph += hz / Sr;
                    double p = ph - Math.Floor(ph);
                    double pulse = Math.Exp(-p * 8) * (0.8 + 0.4 * ns.Value());
                    double env = Math.Min(1, u * 10) * Math.Min(1, (1 - u) * 10);
                    t.Add(s + i, f.Process((float)pulse, 300 + hz * 4, 1.2) * (float)env * gain * 2f);
                }
            }

            /// <summary>A jackhammer: a fast hammering of hard knocks on concrete, rattling the steel.</summary>
            public static void Jackhammer(Track t, double at, double dur, Random r)
            {
                double time = at, rate = 21 + r.NextDouble() * 4;
                while (time < at + dur)
                {
                    NoiseBurst(t, time, 0.04, 1800, 0.9, 0.55f, r.Next(), 0.0005, 110);
                    NoiseBurst(t, time, 0.05, 180, 1.2, 0.7f, r.Next(), 0.001, 70);
                    time += 1.0 / rate;
                }
                Strike(t, at, 1900, new[] { 1.0, 1.7, 2.9 }, new[] { 0.6, 0.4, 0.3 }, 6, 0.05f, dur);
            }

            /// <summary>Hammering: a hammer driving a nail into a plank, the last blows ringing the steel.</summary>
            public static void Hammering(Track t, double at, int blows, Random r)
            {
                double time = at;
                for (int i = 0; i < blows; i++)
                {
                    bool metal = i >= blows - 2 || r.NextDouble() < 0.3;
                    NoiseBurst(t, time, 0.08, 900 + r.NextDouble() * 300, 1.4, 0.7f, r.Next(), 0.0006, 55);
                    NoiseBurst(t, time, 0.1, 160, 1.0, 0.5f, r.Next(), 0.001, 40);
                    if (metal) Strike(t, time, 1350 + r.NextDouble() * 200, new[] { 1.0, 2.3, 3.7 }, new[] { 1.0, 0.5, 0.3 }, 7, 0.25f, 0.6);
                    time += 0.42 + r.NextDouble() * 0.15;
                }
            }

            /// <summary>A digger revving up to lift, the hydraulics whining, then settling back to idle.</summary>
            public static void Digger(Track t, double at)
            {
                Engine(t, at, 4.5, 30, 52, 0.55f, 5);
                int s = At(at + 0.8), n = At(2.8);
                double p = 0;
                for (int i = 0; i < n; i++)
                {
                    double u = i / (double)n;
                    double f = 520 + 260 * Math.Sin(Math.PI * u * 0.8);
                    p += f / Sr;
                    t.Add(s + i, (float)(Math.Sin(TwoPi * p) * Math.Sin(Math.PI * u) * 0.08));
                }
            }

            /// <summary>A power drill spinning up into the wall and back down.</summary>
            public static void Drill(Track t, double at, Random r)
            {
                int s = At(at), n = At(2.2 + r.NextDouble() * 0.6);
                double p = 0;
                var f = new Svf();
                var ns = new NoiseSource(r.Next());
                for (int i = 0; i < n; i++)
                {
                    double u = i / (double)n;
                    double ramp = Math.Min(1, u * 5) * Math.Min(1, (1 - u) * 4);
                    double hz = 250 + 900 * ramp;
                    p += hz / Sr;
                    double saw = 2 * (p - Math.Floor(p)) - 1;
                    double chatter = 1 - 0.3 * ns.Value() * ramp;
                    t.Add(s + i, f.Process((float)(saw * chatter), 2400, 1.1) * (float)ramp * 0.5f);
                }
            }

            /// <summary>A lorry's air brakes: a sharp hiss of air, then a puff.</summary>
            public static void AirBrake(Track t, double at, Random r)
            {
                NoiseBurst(t, at, 0.9, 4200, 0.6, 0.6f, r.Next(), 0.003, 4, true);
                NoiseBurst(t, at + 0.75, 0.3, 1600, 0.7, 0.3f, r.Next(), 0.005, 12);
            }

            /// <summary>Steel pipes dropped on a pile: a clatter of ringing knocks, bouncing to rest.</summary>
            public static void Pipes(Track t, double at, Random r)
            {
                double time = at, gap = 0.16;
                for (int i = 0; i < 9; i++)
                {
                    double f = 700 + r.NextDouble() * 900;
                    Strike(t, time, f, new[] { 1.0, 2.76, 5.4 }, new[] { 1.0, 0.5, 0.25 }, 5, 0.35f * (float)Math.Pow(0.85, i), 1.2);
                    NoiseBurst(t, time, 0.03, 2000, 1.0, 0.3f * (float)Math.Pow(0.85, i), r.Next(), 0.0005, 120);
                    time += gap * (0.6 + r.NextDouble() * 0.6);
                    gap *= 0.85;
                }
            }
        }
    }
}
