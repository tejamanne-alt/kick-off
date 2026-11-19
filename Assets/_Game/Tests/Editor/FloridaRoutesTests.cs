#if UNITY_INCLUDE_TESTS
using System.Collections.Generic;
using DribbleToSchool.Challenges;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// Florida's own routes (docs/CITIES.md, "Florida (Miami), USA"): three routes of three legs from the ranch house in Little
    /// Havana to Bayside Elementary, its own level ids (FL1-1...), its stops, the people mover between FL3's first two legs, no
    /// mini-games (removed in v128), older saves moved onto the renumbered legs, and everything a player reads in both languages.
    /// </summary>
    public class FloridaRoutesTests
    {
        static List<KeyValuePair<string, int>> Table(out List<bool> challenge)
        {
            List<string> scenes;
            return GeneratedContent.CityLevelTable(Cities.FloridaId, out challenge, out scenes);
        }

        [Test]
        public void FloridaHasThreeRoutesOfThreeLegs()
        {
            Assert.AreEqual(3, RouteTable.Florida.Length);
            Assert.AreEqual(new[] { "fl1", "fl2", "fl3" }, new[] { RouteTable.Florida[0].id, RouteTable.Florida[1].id, RouteTable.Florida[2].id });
            Assert.AreEqual(new[] { 3, 3, 3 }, new[] { RouteTable.Florida[0].levels.Length, RouteTable.Florida[1].levels.Length, RouteTable.Florida[2].levels.Length });
            foreach (var route in RouteTable.Florida)
            {
                Assert.AreEqual(RouteTable.FloridaId, route.city);
                Assert.AreEqual(RouteTable.FloridaChapter, route.chapter);
                Assert.AreEqual(route.levels.Length - 1, route.stops.Length, route.id);
                for (int i = 0; i < route.levels.Length; i++)
                    Assert.AreEqual(route.id.ToUpperInvariant() + "-" + (i + 1), route.levels[i], "a leg's id is its route's and its number");
                foreach (string stop in route.stops) Assert.IsNotNull(RouteTable.StopById(stop), route.id + ": " + stop);
            }
            Assert.AreSame(RouteTable.Florida, RouteTable.ForCity(Cities.FloridaId));
            Assert.AreSame(RouteTable.All, RouteTable.ForCity(Cities.KamakuraId));
            Assert.AreEqual(RouteTable.All.Length + RouteTable.Florida.Length, RouteTable.Every.Length);
        }

        [Test]
        public void FloridasLevelTableIsItsRoutesLegsInOrder()
        {
            List<bool> challenge;
            var table = Table(out challenge);
            var legs = new List<string>();
            foreach (var route in RouteTable.Florida) legs.AddRange(route.levels);
            Assert.AreEqual(legs.Count, table.Count);
            for (int i = 0; i < table.Count; i++)
            {
                Assert.AreEqual(legs[i], table[i].Key);
                Assert.AreEqual(RouteTable.FloridaChapter, table[i].Value);
                Assert.IsFalse(challenge[i], table[i].Key + ": Florida's legs are story levels");
                Assert.IsTrue(GeneratedContent.BellTime(table[i].Key) > 0f, table[i].Key + " has a target time");
            }
        }

        [Test]
        public void EveryFloridaLegIsADribbleFromItsStop()
        {
            foreach (var route in RouteTable.Florida)
                foreach (string id in route.levels)
                {
                    Assert.IsTrue(GeneratedContent.HasLeadIn(id), id + ": a leg starts with the walk from home or its stop");
                    Assert.IsTrue(GeneratedContent.BellTime(id) > HomeLeadInRules.BellSeconds, id + ": a street of its own after the walk");
                }
        }

        [Test]
        public void TheMiniGamesAreGoneForGood()
        {
            // The user's decision (v128): no mini-games in Kamakura or Florida, and nothing in their place.
            var assembly = typeof(ChallengeObjective).Assembly;
            foreach (string type in new[] { "MiniGameObjective", "BusRide", "MooringLine", "DrugstoreShopping" })
                Assert.IsNull(assembly.GetType("DribbleToSchool.Challenges." + type), type + " is back");
            Assert.IsNull(assembly.GetType("DribbleToSchool.Progression.Errands"), "the errand (the science project) was the boat's");
            foreach (string code in Loc.Languages)
                foreach (string key in StringTables.For(code).Keys)
                    Assert.IsFalse(key.StartsWith("mini.") || key.StartsWith("guide.ride.") || key.StartsWith("guide.throw.") || key.StartsWith("guide.shop."),
                        code + ": " + key + " belongs to a mini-game");
            foreach (string title in new[] { "The Metrobus", "Uncle Rey's Boat", "The Drugstore" })
                foreach (var route in RouteTable.Florida)
                    foreach (string id in route.levels)
                        Assert.AreNotEqual(title, StringTables.For("en")["level." + id], id);
        }

        [Test]
        public void TheLegsMeetAtTheirStopsAndThePeopleMoverTakesFL3OnToBiscayne()
        {
            // FL1: Little Havana ends at the bus stop on Calle Ocho; the bus isn't played, so Brickell Avenue starts at its stop there.
            Assert.AreSame(RouteTable.Home, RouteTable.From("FL1-1"));
            Assert.AreEqual("calleOcho", RouteTable.To("FL1-1").id);
            Assert.AreEqual("brickell", RouteTable.From("FL1-2").id);
            Assert.IsNull(RouteTable.RideBefore("FL1-2"), "no ride, no mini-game: the next leg simply starts there");
            Assert.AreEqual("bayfront", RouteTable.To("FL1-2").id);
            Assert.AreEqual("bayfront", RouteTable.From("FL1-3").id);
            Assert.AreSame(RouteTable.School, RouteTable.To("FL1-3"));
            // FL2: Riverside Street to Uncle Rey's dock, the Riverwalk to the drugstore, the downpour to school.
            Assert.AreEqual("reysDock", RouteTable.To("FL2-1").id);
            Assert.AreEqual("reysDock", RouteTable.From("FL2-2").id);
            Assert.AreEqual("drugstore", RouteTable.To("FL2-2").id);
            Assert.AreEqual("drugstore", RouteTable.From("FL2-3").id);
            Assert.AreSame(RouteTable.School, RouteTable.To("FL2-3"));
            // FL3: the Underline ends at the station, the people mover arrives on Biscayne, where FL3-2 starts.
            Assert.AreEqual("underline", RouteTable.To("FL3-1").id);
            Assert.AreEqual(Rides.PeopleMover, RouteTable.RideBefore("FL3-2"));
            Assert.AreEqual("biscayne", RouteTable.From("FL3-2").id);
            Assert.IsNull(RouteTable.RideBefore("FL3-3"));
            Assert.IsNull(RouteTable.RideBefore("L02"), "Kamakura's routes have no rides yet");
            Assert.AreEqual(RouteTable.Florida[2], RouteTable.Of("FL3-2"));
        }

        [Test]
        public void EveryFloridaStopHasASetPieceAShortSignNameAndItsNamesInEveryLanguage()
        {
            var ids = new HashSet<string>();
            foreach (var stop in RouteTable.Stops) ids.Add(stop.id);
            foreach (var stop in RouteTable.FloridaStops)
            {
                Assert.IsTrue(ids.Add(stop.id), stop.id + " is another stop's id");
                Assert.Less(stop.signName.Length, 20, stop.id + ": the name is too long for the route sign");
                Assert.Contains(stop.id, StreetBuilder.SetPieces);
                foreach (string code in Loc.Languages)
                {
                    var table = StringTables.For(code);
                    Assert.IsTrue(table.ContainsKey(stop.NameKey), code + ": " + stop.NameKey);
                    Assert.IsTrue(table.ContainsKey(stop.ToKey), code + ": " + stop.ToKey);
                }
            }
        }

        [Test]
        public void EverythingFloridaShowsIsInEveryLanguage()
        {
            var keys = new List<string> { "chapter.6", "ride.skip" };
            foreach (string ride in Rides.All) keys.Add(Rides.NameKey(ride));
            foreach (var route in RouteTable.Florida)
            {
                keys.Add(route.NameKey);
                foreach (string id in route.levels)
                {
                    keys.Add("level." + id);
                    keys.Add("sticker." + id); keys.Add("sticker." + id + ".text"); keys.Add("sticker." + id + ".hint");
                }
            }
            foreach (string action in new[] { "chickens", "iguana", "downpour", "sweeper" })
            {
                keys.Add("coach." + action + ".title");
                keys.Add("coach." + action + ".text");
            }
            foreach (string code in Loc.Languages)
            {
                var table = StringTables.For(code);
                foreach (string key in keys) Assert.IsTrue(table.ContainsKey(key), code + ": " + key);
                foreach (string action in new[] { "chickens", "iguana", "downpour", "sweeper" })
                {
                    Assert.LessOrEqual(table["coach." + action + ".title"].Length, 36, code + ": coach." + action + ".title");
                    Assert.LessOrEqual(table["coach." + action + ".text"].Length, 140, code + ": coach." + action + ".text");
                }
            }
        }

        [Test]
        public void FloridasMapHasItsRoutesFromHomeToSchoolWithEveryLegAndStopOnThem()
        {
            try
            {
                TownMap.Use(Cities.FloridaId);
                Assert.IsTrue(TownMap.Available, "MiamiMapLayout.json: " + TownMap.Problem);
                Assert.AreEqual("UI/MiamiMap", TownMap.Image);
                Assert.AreEqual(RouteTable.Florida.Length, TownMap.Routes.Length);
                var core = TownMap.Core;
                var nodes = new List<TownNode>();
                for (int r = 0; r < RouteTable.Florida.Length; r++)
                {
                    var route = RouteTable.Florida[r];
                    var line = TownMap.Routes[r];
                    Assert.AreEqual(route.id, line.id, "the map's routes in RouteTable's order");
                    Assert.Less(UnityEngine.Vector2.Distance(line.points[0], TownMap.Home), 25f, route.id + " starts at home");
                    Assert.Less(UnityEngine.Vector2.Distance(line.points[line.points.Length - 1], TownMap.School), 25f, route.id + " ends at school");
                    float along = -1f;
                    foreach (string id in route.levels)
                    {
                        var node = TownMap.Node(id);
                        Assert.IsNotNull(node, id + " has a node");
                        Assert.Less(TownMap.DistanceTo(line.points, node.pos), 12f, id + " is on its route");
                        float at = TownMap.DistanceAlong(line.points, node.pos);
                        Assert.Greater(at, along, id + " follows the leg before it along the route");
                        along = at;
                        Assert.IsTrue(core.Contains(node.pos), id + " is inside the picture's core");
                        nodes.Add(node);
                    }
                    for (int i = 0; i < route.stops.Length; i++)
                        Assert.IsNotNull(TownMap.StopPosition(route.id, i), route.id + "'s stop " + route.stops[i] + " is drawn");
                }
                for (int i = 0; i < nodes.Count; i++)
                    for (int j = i + 1; j < nodes.Count; j++)
                        Assert.GreaterOrEqual(UnityEngine.Vector2.Distance(nodes[i].pos, nodes[j].pos), 190f, nodes[i].levelId + " and " + nodes[j].levelId);
                foreach (string code in Loc.Languages)
                    foreach (string key in TownMap.LocKeys())
                        Assert.IsTrue(StringTables.For(code).ContainsKey(key), code + ": " + key);
            }
            finally
            {
                TownMap.Use(Cities.KamakuraId);   // (the other tests read the town's map)
            }
        }

        [Test]
        public void TheMapNumbersALegByItsPlaceOnItsRoute()
        {
            Assert.AreEqual("3", RouteTable.NodeNumber("FL2-3"));
            Assert.AreEqual("1", RouteTable.NodeNumber("FL1-1"));
            Assert.AreEqual("7", RouteTable.NodeNumber("L07"));
            Assert.AreEqual("23", RouteTable.NodeNumber("L23"));
            Assert.AreEqual("!", RouteTable.NodeNumber("C02"));
        }

        [Test]
        public void AnOlderSavesFloridaRecordsFollowTheirLegsToTheirNewNumbers()
        {
            var data = new SaveData { version = 2 };
            foreach (string id in new[] { "FL1-1", "FL1-2", "FL1-3", "FL1-4", "FL2-2", "FL2-3", "FL2-4", "FL2-5", "FL3-2", "L07" })
                data.levels.Add(new LevelRecord { levelId = id, completed = true, bestStars = id == "FL1-4" ? 3 : 1 });
            data.stickers.AddRange(new[] { "FL1-3", "FL2-5", "L07" });
            data.trips.Add(new TripRecord { routeId = "fl1", legTimes = new List<float> { 70f, 50f, 80f, 75f } });
            data.trips.Add(new TripRecord { routeId = "fl2", legTimes = new List<float> { 71f, 40f, 85f, 55f, 90f } });
            data.trips.Add(new TripRecord { routeId = "street", legTimes = new List<float> { 1f, 2f, 3f, 4f, 5f } });

            FloridaLegs.Upgrade(data);

            var ids = new List<string>();
            foreach (var record in data.levels) ids.Add(record.levelId);
            Assert.AreEqual(new[] { "FL1-1", "FL1-2", "FL1-3", "FL2-2", "FL2-3", "FL3-2", "L07" }, ids.ToArray(),
                "the mini-games' records dropped, the legs after them renumbered, the rest untouched");
            Assert.AreEqual(3, data.Level("FL1-3").bestStars, "Bayfront's record (FL1-4 before) moved with it");
            Assert.AreEqual(new[] { "FL1-2", "FL2-3", "L07" }, data.stickers.ToArray());
            Assert.AreEqual(new[] { 70f, 80f, 75f }, SchoolTrips.Find(data, "fl1").legTimes.ToArray());
            Assert.AreEqual(new[] { 71f, 85f, 90f }, SchoolTrips.Find(data, "fl2").legTimes.ToArray());
            Assert.AreEqual(5, SchoolTrips.Find(data, "street").legTimes.Count, "Kamakura's trips are left alone");

            // A save already at version 3 is never moved again.
            data.version = SaveData.CurrentVersion;
            FloridaLegs.Upgrade(data);
            Assert.AreEqual(3, data.Level("FL1-3").bestStars);
            Assert.IsNull(FloridaLegs.NewId("FL2-4"));
            Assert.AreEqual("FL2-3", FloridaLegs.NewId("FL2-5"));
            Assert.AreEqual("FL3-1", FloridaLegs.NewId("FL3-1"));
        }
    }
}
#endif
