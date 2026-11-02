#if UNITY_INCLUDE_TESTS
using System.Linq;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.EditorTools;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>The Holiday Run's kid is not in school uniform unless they chose another outfit themselves.</summary>
    public class HolidayOutfitTests
    {
        [Test]
        public void TheHolidayRunSwapsTheSchoolUniformForTheHolidayOutfit()
        {
            Assert.AreEqual(CosmeticApplier.HolidayOutfitId, CosmeticApplier.OutfitIdFor(true, CosmeticApplier.SchoolOutfitId));
            Assert.AreEqual(CosmeticApplier.HolidayOutfitId, CosmeticApplier.OutfitIdFor(true, ""));
            Assert.AreEqual(CosmeticApplier.HolidayOutfitId, CosmeticApplier.OutfitIdFor(true, null));
        }

        [Test]
        public void AnOutfitThePlayerChoseIsKeptEverywhere()
        {
            Assert.AreEqual("outfit_red", CosmeticApplier.OutfitIdFor(true, "outfit_red"));
            Assert.AreEqual("outfit_red", CosmeticApplier.OutfitIdFor(false, "outfit_red"));
            Assert.AreEqual(CosmeticApplier.SchoolOutfitId, CosmeticApplier.OutfitIdFor(false, CosmeticApplier.SchoolOutfitId));
        }

        [Test]
        public void TheHolidayOutfitIsFreeAndHasNoTie()
        {
            var row = CosmeticsTable.Rows().FirstOrDefault(r => r.id == CosmeticApplier.HolidayOutfitId);
            Assert.AreEqual(CosmeticApplier.HolidayOutfitId, row.id, "the Holiday outfit is in the table");
            Assert.AreEqual(0, row.price, "free");
            Assert.AreEqual(CosmeticCategory.Outfit, row.category);
            Assert.Less(row.accent.a, 0.01f, "a see-through accent takes the tie off");
        }
    }
}
#endif
