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
    /// Florida's own routes (docs/CITIES.md, "Florida (Miami), USA"): three routes of 4, 5 and 3 legs from the ranch house in Little
    /// Havana to Bayside Elementary, its own level ids (FL1-1...), its stops, the people mover between FL3's first two legs, the
    /// three mini-game legs, and everything a player reads about them in both languages.
    /// </summary>
    public class FloridaRoutesTests
    {
        static List<KeyValuePair<string, int>> Table(out List<bool> challenge)
        {
            List<string> scenes;
            return GeneratedContent.CityLevelTable(Cities.FloridaId, out challenge, out scenes);
        }

        [Test]
        public void FloridaHasThreeRoutesOfFourFiveAndThreeLegs()
        {
            Assert.AreEqual(3, RouteTable.Florida.Length);
            Assert.AreEqual(new[] { "fl1", "fl2", "fl3" }, new[] { RouteTable.Florida[0].id, RouteTable.Florida[1].id, RouteTable.Florida[2].id });
            Assert.AreEqual(new[] { 4, 5, 3 }, new[] { RouteTable.Florida[0].levels.Length, RouteTable.Florida[1].levels.Length, RouteTable.Florida[2].levels.Length });
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
        public void EveryRouteOfFourOrFiveLegsHasAMiniGameAndTheMiniGamesAreTheDesignsThree()
        {
            var mini = new List<string>();
            foreach (var route in RouteTable.Florida)
            {
                int count = 0;
                foreach (string id in route.levels)
                    if (GeneratedContent.IsMiniGame(id)) { count++; mini.Add(id); }
                if (route.levels.Length >= 4) Assert.GreaterOrEqual(count, 1, route.id + ": a route longer than three legs has a mini-game");
                Assert.IsFalse(GeneratedContent.IsMiniGame(route.levels[0]), route.id + ": a trip starts with a walk from home");
                Assert.IsFalse(GeneratedContent.IsMiniGame(route.levels[route.levels.Length - 1]), route.id + ": and ends with one to school");
            }
            Assert.AreEqual(new[] { "FL1-2", "FL2-2", "FL2-4" }, mini.ToArray());
            foreach (string id in mini) Assert.IsFalse(GeneratedContent.HasLeadIn(id), id + ": a mini-game is played at its stop");
        }

        [Test]
        public void TheLegsMeetAtTheirStopsAndThePeopleMoverTakesFL3OnToBiscayne()
        {
            Assert.AreSame(RouteTable.Home, RouteTable.From("FL1-1"));
            Assert.AreEqual("calleOcho", RouteTable.To("FL1-1").id);
            Assert.AreEqual("calleOcho", RouteTable.From("FL1-2").id);
            Assert.AreEqual("brickell", RouteTable.To("FL1-2").id);
            Assert.AreSame(RouteTable.School, RouteTable.To("FL1-4"));
            // The mini-games of FL2 are played at their stops: Uncle Rey's dock, the drugstore.
            Assert.AreEqual("reysDock", RouteTable.From("FL2-2").id);
            Assert.AreEqual("reysDock", RouteTable.To("FL2-2").id);
            Assert.AreEqual("drugstore", RouteTable.From("FL2-4").id);
            Assert.AreEqual("drugstore", RouteTable.To("FL2-4").id);
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
            var keys = new List<string> { "chapter.6", "ride.skip", "mini.score", "results.delivered", "results.spoiled" };
            foreach (string ride in Rides.All) keys.Add(Rides.NameKey(ride));
            foreach (var route in RouteTable.Florida)
            {
                keys.Add(route.NameKey);
                foreach (string id in route.levels)
                {
                    keys.Add("level." + id);
                    if (GeneratedContent.IsMiniGame(id)) keys.Add("challenge." + id + ".goal");
                    else { keys.Add("sticker." + id); keys.Add("sticker." + id + ".text"); keys.Add("sticker." + id + ".hint"); }
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
        public void TheMapNumbersALegByItsPlaceOnItsRoute()
        {
            Assert.AreEqual("3", RouteTable.NodeNumber("FL2-3"));
            Assert.AreEqual("1", RouteTable.NodeNumber("FL1-1"));
            Assert.AreEqual("7", RouteTable.NodeNumber("L07"));
            Assert.AreEqual("23", RouteTable.NodeNumber("L23"));
            Assert.AreEqual("!", RouteTable.NodeNumber("C02"));
        }

        [Test]
        public void TheScienceProjectRidesToSchoolAndIsDeliveredOnlyUnharmed()
        {
            var data = new SaveData();
            Assert.AreEqual(Errands.ScienceProject, Errands.ItemOf("fl2"));
            Assert.IsNull(Errands.ItemOf("fl1"));
            Errands.Pick(data, Errands.ScienceProject);
            Assert.IsTrue(Errands.CarryingUnharmed(data, Errands.ScienceProject));
            Assert.IsTrue(Errands.Arrive(data, "fl2"));
            Assert.Contains(Errands.ScienceProject, data.delivered);
            Assert.AreEqual("", data.carrying, "put down at school");

            Errands.Pick(data, Errands.ScienceProject);
            Errands.Spoil(data);
            Assert.IsFalse(Errands.Arrive(data, "fl2"), "soaked in the downpour: no badge");
            Assert.AreEqual("", data.carrying);

            Errands.Pick(data, Errands.ScienceProject);
            Errands.Drop(data);
            Assert.IsFalse(Errands.Arrive(data, "fl2"), "a trip started again from home carries nothing");
        }

        [Test]
        public void TheDrugstoreCountsMoneyInCentsAndStarsTheFewestPieces()
        {
            Assert.AreEqual(7, DrugstoreShopping.Fewest(677));      // $5, $1, three quarters, two pennies
            Assert.AreEqual(1, DrugstoreShopping.Fewest(1000));
            Assert.AreEqual(0, DrugstoreShopping.Fewest(0));
            Assert.AreEqual("$6.77", DrugstoreShopping.Dollars(677));
            Assert.AreEqual("$0.05", DrugstoreShopping.Dollars(5));
            Assert.AreEqual(3, DrugstoreShopping.StarsFor(0, 677, 7, 677));
            Assert.AreEqual(2, DrugstoreShopping.StarsFor(0, 700, 7, 677), "paid too much: change, no third star");
            Assert.AreEqual(2, DrugstoreShopping.StarsFor(1, 677, 7, 677), "a slip");
            Assert.AreEqual(1, DrugstoreShopping.StarsFor(2, 1000, 1, 677));
        }
    }
}
#endif
