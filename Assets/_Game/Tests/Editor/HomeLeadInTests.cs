#if UNITY_INCLUDE_TESTS
using System;
using System.Collections.Generic;
using System.Linq;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Holiday;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// Every story level starts at a stop and walks a stretch of street before its own street begins: the first level of a route on
    /// the doorstep of the kid's house and the home street, every other level at the stop where the level before it ended
    /// (docs/WORLD_MAP.md, "Every route is one trip, a level is a leg of it"; Editor/HomeLeadInRules.cs, LevelBuildKit.Home.cs,
    /// LevelBuildKit.Stops.cs, StreetBuilder.Home.cs, StreetBuilder.Stops.cs). These are the rules that need no scene; what the
    /// layouts and the audit say with the lead-in on is checked by the offline harness.
    /// </summary>
    public class HomeLeadInTests
    {
        // The seconds each story level's street takes, as the Levels table had them before the lead-in: the bell is these plus the walk from the door.
        static readonly Dictionary<string, float> StreetSeconds = new Dictionary<string, float>
        {
            { "L01", 50f }, { "L02", 55f }, { "L03", 80f }, { "L04", 60f }, { "L05", 80f },
            { "L06", 60f }, { "L07", 70f }, { "L08", 70f }, { "L09", 75f }, { "L10", 95f },
            { "L11", 70f }, { "L12", 75f }, { "L13", 80f }, { "L14", 95f },
            { "L15", 65f }, { "L16", 80f }, { "L17", 85f }, { "L18", 105f },
            { "L19", 65f }, { "L20", 75f }, { "L21", 80f }, { "L22", 80f }, { "L23", 120f },
        };

        [Test]
        public void TheLeadInIsAboutThreeSecondsOfWalking()
        {
            Assert.AreEqual(HomeLeadInRules.Length, LevelBuildKit.HomeLeadIn, "one number for the length");
            Assert.AreEqual(1, HomeLeadInRules.HomeChapter, "the lead-in is the home street");
            float seconds = HomeLeadInRules.Length / JumpReach.Defaults.runSpeed;
            Assert.GreaterOrEqual(HomeLeadInRules.Length, 11f, "OutTheDoor's first hint (x = -10.5) and walk sign (x = -8) stand in the lead-in: move them if it gets shorter");
            Assert.GreaterOrEqual(seconds, 2f, "walking time of the lead-in");
            Assert.LessOrEqual(seconds, 4f, "walking time of the lead-in");
            Assert.AreEqual(Mathf.Ceil(seconds), HomeLeadInRules.BellSeconds, 1e-4f, "the bell grows by the walk, rounded up");
        }

        [Test]
        public void EveryStoryLevelHasALeadInAndOnlyTheFirstOfARouteStartsAtHome()
        {
            List<bool> challenge;
            List<string> scenes;
            var table = GeneratedContent.LevelTable(out challenge, out scenes);
            for (int i = 0; i < table.Count; i++)
                Assert.AreEqual(!challenge[i], GeneratedContent.HasLeadIn(table[i].Key), table[i].Key + (challenge[i] ? " is a challenge: it keeps its own start" : " is a story level: it starts at a stop"));
            Assert.IsFalse(GeneratedContent.HasLeadIn("T00"), "the test track (and any unknown level) keeps its own start");
            Assert.IsFalse(HomeLeadInRules.HasLeadIn(false, false));
            Assert.IsFalse(LevelBuildKit.HasLeadIn(null), "a scene with no level definition (the test track)");
            Assert.IsFalse(LevelBuildKit.StartsAtHome(null));

            var first = ScriptableObject.CreateInstance<LevelDefinition>();
            first.levelId = "L06";
            var later = ScriptableObject.CreateInstance<LevelDefinition>();
            later.levelId = "L07";
            var arena = ScriptableObject.CreateInstance<LevelDefinition>();
            arena.levelId = "C02";
            arena.isChallenge = true;
            try
            {
                Assert.IsTrue(LevelBuildKit.HasLeadIn(first));
                Assert.IsTrue(LevelBuildKit.StartsAtHome(first), "L06 is the market route's first level: it starts at home");
                Assert.IsTrue(LevelBuildKit.HasLeadIn(later));
                Assert.IsFalse(LevelBuildKit.StartsAtHome(later), "L07 starts at the bakery, where L06 ended");
                Assert.IsFalse(LevelBuildKit.HasLeadIn(arena));
                Assert.IsFalse(LevelBuildKit.StartsAtHome(arena));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(first);
                UnityEngine.Object.DestroyImmediate(later);
                UnityEngine.Object.DestroyImmediate(arena);
            }
        }

        [Test]
        public void EveryStoryBellGrewByTheWalkFromTheDoor()
        {
            List<bool> challenge;
            List<string> scenes;
            var table = GeneratedContent.LevelTable(out challenge, out scenes);
            int story = 0;
            for (int i = 0; i < table.Count; i++)
            {
                string id = table[i].Key;
                if (challenge[i])
                {
                    Assert.AreEqual(0f, GeneratedContent.BellTime(id), 1e-4f, id + ": a challenge has no bell");
                    continue;
                }
                story++;
                Assert.IsTrue(StreetSeconds.ContainsKey(id), id + " is not in the test's table of street seconds");
                Assert.AreEqual(StreetSeconds[id] + HomeLeadInRules.BellSeconds, GeneratedContent.BellTime(id), 1e-4f, id + "'s bell: its street plus the walk");
            }
            Assert.AreEqual(StreetSeconds.Count, story, "every story level has its street seconds here");
        }

        [Test]
        public void TheRouteSignNamesWhereTheLevelGoesAndTheRouteAndEndsBeforeTheSeam()
        {
            var english = StringTables.For("en");
            foreach (var route in RouteTable.All)
                foreach (string level in route.levels)
                {
                    string name = english[route.NameKey];
                    var to = RouteTable.To(level);
                    string text = HomeLeadInRules.SignText(to.signName, name);
                    Assert.IsTrue(text.StartsWith(to.signName + " ->"), level + ": the sign points to where the level ends (" + to.signName + ")");
                    Assert.IsTrue(text.Contains(name), level + ": the sign names the route");
                    // SignBoard sizes a board by its longest line: 0.135 m a character and 0.6 m of margin. The board, centred before the seam, stays on the lead-in's side.
                    float width = text.Split('\n').Max(line => line.Length) * 0.135f + 0.6f;
                    Assert.Less(width * 0.5f, HomeLeadInRules.SignBeforeSeam - 0.1f, level + "'s sign (" + width.ToString("0.0") + " m) reaches the seam");
                    Assert.Less(width, HomeLeadInRules.Length - 4f, level + "'s sign is too wide for the lead-in");
                }
            Assert.IsTrue(HomeLeadInRules.SignText(null, "Park Path").StartsWith("School ->"), "no destination: the school");
        }

        [Test]
        public void TheSeamIsOnTheSandsHalfUnitLattice()
        {
            Assert.AreEqual(0f, HomeLeadInRules.SeamX(0f), 1e-5f, "a layout that starts at 0 has its seam at 0");
            Assert.AreEqual(0.5f, HomeLeadInRules.SeamX(0.3f), 1e-5f);
            Assert.AreEqual(-0.5f, HomeLeadInRules.SeamX(-0.3f), 1e-5f);
            Assert.AreEqual(1f, HomeLeadInRules.SeamX(1.1f), 1e-5f);
        }

        [Test]
        public void TheLeadInGoesOnTheLayoutsFirstSpanSoThereIsNoJointInTheGround()
        {
            const float lead = HomeLeadInRules.Length;
            // A story layout calls Walls(-8) and Ground(-8, ...): the first span grows back with the walls; later ones stay.
            Assert.AreEqual(-8f - lead, HomeLeadInRules.GroundFrom(-8f, true, -8f, lead), 1e-5f);
            Assert.AreEqual(20f, HomeLeadInRules.GroundFrom(20f, false, -8f, lead), 1e-5f, "a later span");
            Assert.AreEqual(-8f, HomeLeadInRules.GroundFrom(-8f, true, -8f, 0f), 1e-5f, "no lead-in: as the layout says");
            Assert.AreEqual(5f, HomeLeadInRules.GroundFrom(5f, true, -8f, lead), 1e-5f, "a first span that starts elsewhere is left to the safety net");
            Assert.AreEqual(-8f, HomeLeadInRules.GroundFrom(-8f, true, float.NaN, lead), 1e-5f, "Ground before Walls");

            // The safety net: ground from the walls to a first span that starts later.
            float to;
            Assert.IsTrue(HomeLeadInRules.GroundBefore(-20f, 5f, out to));
            Assert.AreEqual(5f, to, 1e-5f);
            Assert.IsFalse(HomeLeadInRules.GroundBefore(-20f, -20f, out to), "ground already reaches the wall");
        }

        [Test]
        public void TheHouseIsTheKitsHouseWithItsDoorWhereTheBuilderAssumes()
        {
            Assert.AreEqual("HouseGable", HomeInfo.HouseModel);
            // The builder puts the model so that its door is under the gate: the door's place must be the manifest's.
            var info = LevelBuildKit.KitInfo("Buildings", HomeInfo.HouseModel);
            Assert.IsNotNull(info, "Buildings.json describes " + HomeInfo.HouseModel);
            var doors = info["doors"] as List<object>;
            Assert.IsNotNull(doors);
            Assert.IsNotEmpty(doors);
            var center = ((Dictionary<string, object>)doors[0])["center"] as List<object>;
            Assert.IsNotNull(center);
            Assert.AreEqual(HomeInfo.DoorFromMiddle, Convert.ToSingle(center[0]), 0.01f, "where the HouseGable's front door is");
            // A warm red door: red clearly the strongest.
            Assert.Greater(HomeInfo.DoorColor.r, 0.6f);
            Assert.Greater(HomeInfo.DoorColor.r, HomeInfo.DoorColor.g * 2.5f);
            Assert.Greater(HomeInfo.DoorColor.r, HomeInfo.DoorColor.b * 2.5f);
            Assert.IsFalse(string.IsNullOrEmpty(HomeInfo.HouseNumber));
        }
    }
}
#endif
