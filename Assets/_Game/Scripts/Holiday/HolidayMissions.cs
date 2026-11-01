using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using UnityEngine;

namespace DribbleToSchool.Holiday
{
    /// <summary>One mission as the screens show it.</summary>
    public struct MissionView
    {
        public string id;
        public string text;       // localized: "Run 800 m in one go"
        public int target;
        public int progress;      // 0..target
        public int reward;        // coins
        public bool done;
    }

    /// <summary>How a mission counts the runs, which is also how its progress carries over from one run to the next.</summary>
    public enum MissionMeasure
    {
        /// <summary>The best single run ("in one go"): progress is the most any one run has had, so a worse run never takes it back.</summary>
        BestRun,
        /// <summary>Every run added up ("in total"): progress grows by what each run did.</summary>
        Total,
    }

    /// <summary>
    /// One kind of mission in the pool: what it counts, how, and its three tiers (easy to hard) of
    /// target and coin reward. The text is the localization key "holiday.m.&lt;id&gt;" with the target
    /// as {0}; <see cref="singularKey"/>, when given, is the wording for a target of exactly one.
    /// </summary>
    public sealed class MissionDefinition
    {
        public readonly string id;
        public readonly string textKey;
        public readonly string singularKey;
        public readonly MissionMeasure measure;
        /// <summary>The number out of a run's stats this mission counts.</summary>
        public readonly Func<RunStats, int> stat;
        /// <summary>The target of each tier, easy to hard (never change them in place).</summary>
        public readonly int[] targets;
        /// <summary>The coins each tier pays.</summary>
        public readonly int[] rewards;

        public MissionDefinition(string id, MissionMeasure measure, Func<RunStats, int> stat, int[] targets, int[] rewards, string singularKey = null)
        {
            this.id = id;
            this.measure = measure;
            this.stat = stat;
            this.targets = targets;
            this.rewards = rewards;
            this.singularKey = singularKey;
            textKey = "holiday.m." + id;
        }
    }

    /// <summary>
    /// Three missions at a time (from a pool of twelve: run so far in one go, collect coins, slide, double
    /// jump, near misses, smash crates, power-ups, reach a stage, finish a day, the combo, jumps, obstacles),
    /// saved in SaveData.holidayMissions. Finishing one pays coins and a new one takes its place; the new
    /// one is of a kind not on the list, and asks for more each time that kind has been finished before.
    /// Everything here works on a <see cref="SaveData"/>, so the tests can use a throwaway one; the
    /// parameterless forms use the player's save.
    /// </summary>
    public static class HolidayMissions
    {
        /// <summary>How many missions are on the go at once.</summary>
        public const int ActiveCount = 3;

        /// <summary>Progress never grows past this, so adding up many runs can't overflow.</summary>
        const int MaxProgress = 1000000000;

        /// <summary>
        /// The pool. The targets and rewards are first guesses to be tuned by playing (a stage is 120 m, a day
        /// is 23 stages, and the combo tops out at the director's maxMultiplier of 5): the first tier should be
        /// done within a run or two, the last one should take a good run or many of them.
        /// </summary>
        static readonly MissionDefinition[] Pool =
        {
            // ---- the best single run ("in one go") ----
            new MissionDefinition("distance", MissionMeasure.BestRun, s => s.distance, new[] { 600, 1400, 2800 }, new[] { 60, 120, 240 }),
            new MissionDefinition("coins", MissionMeasure.BestRun, s => s.coins, new[] { 30, 80, 160 }, new[] { 50, 110, 220 }),
            new MissionDefinition("stage", MissionMeasure.BestRun, s => s.stagesReached, new[] { 6, 12, 23 }, new[] { 70, 140, 250 }),
            new MissionDefinition("multiplier", MissionMeasure.BestRun, s => s.maxMultiplier, new[] { 3, 4, 5 }, new[] { 50, 90, 150 }),
            new MissionDefinition("obstacles", MissionMeasure.BestRun, s => s.obstacles, new[] { 25, 60, 120 }, new[] { 60, 130, 240 }),
            // ---- every run added up ("in total") ----
            new MissionDefinition("slides", MissionMeasure.Total, s => s.slides, new[] { 15, 40, 100 }, new[] { 60, 120, 220 }),
            new MissionDefinition("doubleJumps", MissionMeasure.Total, s => s.doubleJumps, new[] { 10, 30, 80 }, new[] { 60, 120, 220 }),
            new MissionDefinition("nearMisses", MissionMeasure.Total, s => s.nearMisses, new[] { 3, 10, 25 }, new[] { 70, 140, 250 }),
            new MissionDefinition("smashes", MissionMeasure.Total, s => s.smashes, new[] { 5, 15, 40 }, new[] { 60, 120, 230 }),
            new MissionDefinition("powerUps", MissionMeasure.Total, s => s.powerUps, new[] { 3, 8, 20 }, new[] { 60, 120, 220 }),
            new MissionDefinition("jumps", MissionMeasure.Total, s => s.jumps, new[] { 40, 120, 300 }, new[] { 50, 110, 200 }),
            new MissionDefinition("days", MissionMeasure.Total, s => s.days, new[] { 1, 2, 4 }, new[] { 100, 160, 250 }, "holiday.m.days.one"),
        };

        static readonly ReadOnlyCollection<MissionDefinition> PoolView = new ReadOnlyCollection<MissionDefinition>(Pool);

        static System.Random shared;

        /// <summary>Every kind of mission there is.</summary>
        public static IList<MissionDefinition> Definitions { get { return PoolView; } }

        static System.Random Shared { get { return shared ?? (shared = new System.Random()); } }

        // ================================================================ the player's save

        /// <summary>The active missions with their saved progress (topped up to three).</summary>
        public static IList<MissionView> Active()
        {
            return Active(SaveSystem.Data, null);
        }

        /// <summary>The active missions as they would stand if the run ended now with these stats (changes nothing).</summary>
        public static IList<MissionView> Preview(RunStats stats)
        {
            return Preview(SaveSystem.Data, stats, null);
        }

        /// <summary>
        /// Apply a finished run: update every mission's progress, replace the finished ones and save.
        /// Returns the coins the finished missions paid; <paramref name="completed"/> gets those missions.
        /// The wallet is the caller's to fill: the director banks this with the run's own coins.
        /// </summary>
        public static int Commit(RunStats stats, List<MissionView> completed)
        {
            int paid = Apply(SaveSystem.Data, stats, completed, null);
            SaveSystem.Save();
            return paid;
        }

        // ================================================================ any save

        /// <summary>
        /// The active missions of <paramref name="data"/> with their saved progress. A list that is empty,
        /// short or damaged (missing entries, kinds that are no longer in the pool, the same kind twice,
        /// a target that isn't positive) is put right first, so there are always three distinct missions.
        /// </summary>
        public static IList<MissionView> Active(SaveData data, System.Random rng)
        {
            Prepare(data, rng);
            var views = new List<MissionView>(data.holidayMissions.Count);
            foreach (var record in data.holidayMissions) views.Add(View(Find(record.id), record, record.progress));
            return views;
        }

        /// <summary>
        /// The active missions as they would stand if the run ended now. Never counts the run: the only thing
        /// this may do is the tidy-up and top-up <see cref="Active(SaveData, System.Random)"/> does, so that the
        /// missions it shows are the ones <see cref="Apply"/> will count the run on.
        /// </summary>
        public static IList<MissionView> Preview(SaveData data, RunStats stats, System.Random rng)
        {
            Prepare(data, rng);
            var views = new List<MissionView>(data.holidayMissions.Count);
            foreach (var record in data.holidayMissions)
            {
                var def = Find(record.id);
                views.Add(View(def, record, Advance(def, record.progress, stats)));
            }
            return views;
        }

        /// <summary>
        /// <see cref="Commit"/> on any save, without writing it to disk: counts the run into every
        /// mission, and each one that reaches its target is added to <paramref name="completed"/>, tallied
        /// (so its next one is a tier harder) and replaced, in the same place, by a new mission of another
        /// kind. Returns the coins the finished missions pay.
        /// </summary>
        public static int Apply(SaveData data, RunStats stats, List<MissionView> completed, System.Random rng)
        {
            rng = rng ?? Shared;
            Prepare(data, rng);
            var list = data.holidayMissions;

            int paid = 0;
            var finished = new List<int>();
            for (int i = 0; i < list.Count; i++)
            {
                var record = list[i];
                var def = Find(record.id);
                record.progress = Advance(def, record.progress, stats);
                if (record.progress < record.target) continue;

                var view = View(def, record, record.progress);
                paid += view.reward;
                if (completed != null) completed.Add(view);
                Tally(data, def.id);
                finished.Add(i);
            }

            // The new ones are of other kinds than the missions still going and than the ones just finished
            // (so the player isn't handed the same task straight away), unless the pool runs out of choice.
            var justFinished = new HashSet<string>();
            foreach (int i in finished) justFinished.Add(list[i].id);
            foreach (int i in finished)
            {
                var inUse = new HashSet<string>();
                for (int j = 0; j < list.Count; j++)
                    if (j != i) inUse.Add(list[j].id);
                list[i] = Fresh(data, inUse, justFinished, rng);
            }
            return paid;
        }

        // ================================================================ keeping the list in order

        static void Prepare(SaveData data, System.Random rng)
        {
            if (data == null) throw new ArgumentNullException("data");
            Sanitize(data);
            TopUp(data, rng ?? Shared);
        }

        /// <summary>Throw away what can't be played, so a damaged save (a hand edit, an older build) never breaks the screen.</summary>
        static void Sanitize(SaveData data)
        {
            if (data.holidayMissions == null) data.holidayMissions = new List<HolidayMissionRecord>();
            if (data.holidayMissionTally == null) data.holidayMissionTally = new List<HolidayMissionTally>();
            var list = data.holidayMissions;
            var seen = new HashSet<string>();
            for (int i = 0; i < list.Count; i++)
            {
                var record = list[i];
                bool playable = record != null && !string.IsNullOrEmpty(record.id) && Find(record.id) != null && record.target > 0 && seen.Add(record.id);
                if (!playable)
                {
                    list.RemoveAt(i);
                    i--;
                    continue;
                }
                if (record.progress < 0) record.progress = 0;
            }
            if (list.Count > ActiveCount) list.RemoveRange(ActiveCount, list.Count - ActiveCount);
        }

        static void TopUp(SaveData data, System.Random rng)
        {
            var list = data.holidayMissions;
            if (list.Count >= ActiveCount) return;
            var inUse = new HashSet<string>();
            foreach (var record in list) inUse.Add(record.id);
            var nothingElse = new HashSet<string>();
            while (list.Count < ActiveCount)
            {
                var fresh = Fresh(data, inUse, nothingElse, rng);
                list.Add(fresh);
                inUse.Add(fresh.id);
            }
        }

        /// <summary>
        /// A new mission of a kind not in <paramref name="mustAvoid"/> (the ones on the go) and, if there is
        /// choice, not in <paramref name="preferToAvoid"/>; its tier is how many of that kind have been finished.
        /// </summary>
        static HolidayMissionRecord Fresh(SaveData data, ICollection<string> mustAvoid, ICollection<string> preferToAvoid, System.Random rng)
        {
            var candidates = new List<MissionDefinition>(Pool.Length);
            foreach (var def in Pool)
                if (!mustAvoid.Contains(def.id) && !preferToAvoid.Contains(def.id)) candidates.Add(def);
            if (candidates.Count == 0)
                foreach (var def in Pool)
                    if (!mustAvoid.Contains(def.id)) candidates.Add(def);
            if (candidates.Count == 0) candidates.AddRange(Pool);

            var chosen = candidates[rng.Next(candidates.Count)];
            int tier = Mathf.Min(CompletedCount(data, chosen.id), chosen.targets.Length - 1);
            return new HolidayMissionRecord { id = chosen.id, target = chosen.targets[tier], progress = 0 };
        }

        // ================================================================ the numbers

        static MissionDefinition Find(string id)
        {
            for (int i = 0; i < Pool.Length; i++)
                if (Pool[i].id == id) return Pool[i];
            return null;
        }

        /// <summary>Progress after a run: the best run so far, or everything so far plus this run.</summary>
        static int Advance(MissionDefinition def, int progress, RunStats stats)
        {
            int value = Mathf.Max(0, def.stat(stats));
            if (def.measure == MissionMeasure.BestRun) return Mathf.Max(progress, value);
            return (int)Math.Min((long)progress + value, MaxProgress);
        }

        static int CompletedCount(SaveData data, string id)
        {
            foreach (var tally in data.holidayMissionTally)
                if (tally != null && tally.id == id) return Mathf.Max(0, tally.done);
            return 0;
        }

        static void Tally(SaveData data, string id)
        {
            foreach (var tally in data.holidayMissionTally)
            {
                if (tally == null || tally.id != id) continue;
                tally.done = Mathf.Min(Mathf.Max(0, tally.done) + 1, 1000);
                return;
            }
            data.holidayMissionTally.Add(new HolidayMissionTally { id = id, done = 1 });
        }

        /// <summary>What a mission with this target pays (the tier it matches, or the nearest above it).</summary>
        static int RewardOf(MissionDefinition def, int target)
        {
            for (int i = 0; i < def.targets.Length; i++)
                if (target <= def.targets[i]) return def.rewards[i];
            return def.rewards[def.rewards.Length - 1];
        }

        static MissionView View(MissionDefinition def, HolidayMissionRecord record, int progress)
        {
            string key = record.target == 1 && def.singularKey != null ? def.singularKey : def.textKey;
            return new MissionView
            {
                id = def.id,
                text = Loc.F(key, record.target.ToString("N0")),
                target = record.target,
                progress = Mathf.Clamp(progress, 0, record.target),
                reward = RewardOf(def, record.target),
                done = progress >= record.target,
            };
        }
    }
}
