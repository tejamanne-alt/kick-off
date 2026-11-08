#if UNITY_INCLUDE_TESTS
using System.IO;
using System.Linq;
using DribbleToSchool.Core;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Progression;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>The Locker Room's bags (Cosmetics/Bags): optional, each kid's own choice, one colour from Settings.</summary>
    public class BagsTests
    {
        [Test]
        public void TheStarterBagsAreFreeShopItems()
        {
            var rows = CosmeticsTable.Rows();
            foreach (string id in Bags.Starter)
            {
                var row = rows.FirstOrDefault(r => r.id == id);
                Assert.AreEqual(id, row.id, "missing bag item: " + id);
                Assert.AreEqual(CosmeticCategory.Bag, row.category);
                Assert.AreEqual(0, row.price, "owned from the start: " + id);
            }
        }

        [Test]
        public void EveryBagItemNamesAMeshFittedToTheKids()
        {
            // "bag_kickoff" is the mesh "Bag_KickOff" in a kid's model, made from Art/Models/BagKickOff.json and its atlas.
            Assert.AreEqual("bag_kickoff", Bags.IdOfMesh("Bag_KickOff"));
            foreach (var row in CosmeticsTable.Rows().Where(r => r.category == CosmeticCategory.Bag && r.id != Bags.NoneId))
            {
                var json = Directory.GetFiles(Path.Combine(Application.dataPath, "_Game/Art/Models"), "Bag*.json")
                    .FirstOrDefault(f => Bags.IdOfMesh("Bag_" + Path.GetFileNameWithoutExtension(f).Substring(3)) == row.id);
                Assert.IsNotNull(json, "no Bag<Id>.json for " + row.id);
                Assert.IsTrue(File.Exists(json.Replace(".json", "Atlas.png")), "no atlas for " + row.id);
            }
        }

        [Test]
        public void TheFirstColourIsTheBagsOwnAndTheRestRecolour()
        {
            Assert.IsFalse(Bags.Colours[0].tints);
            Assert.Greater(Bags.Colours.Length, 4);
            for (int i = 1; i < Bags.Colours.Length; i++) Assert.IsTrue(Bags.Colours[i].tints, Bags.Colours[i].name);
            Assert.AreEqual(Bags.Colours.Length, Bags.Colours.Select(c => c.name).Distinct().Count());
        }

        [Test]
        public void SomeKidWearsTheLockerRoomsBags()
        {
            Assert.IsTrue(PlayerRoster.All.Any(p => p.wearsBags));
            Assert.IsTrue(Bags.CanWear("primaryBoy2"), "Leo was modelled without a bag");
            Assert.IsTrue(Bags.CanWear("primaryBoy"), "so was Kai");
            Assert.IsTrue(Bags.CanWear("primaryGirl2"), "and Zoe");
            Assert.IsTrue(Bags.CanWear("primaryGirl"), "and Mia");
            Assert.IsTrue(Bags.CanWear("girl"), "and Hana");
            Assert.IsFalse(Bags.CanWear("backpackBoy"), "Max carries the bag he was modelled with");
        }

        [Test]
        public void NewSavesHaveNoBagChoicesYet()
        {
            var d = new SaveData();
            Assert.IsNotNull(d.bags);
            Assert.IsEmpty(d.bags);
        }
    }
}
#endif
