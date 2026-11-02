#if UNITY_INCLUDE_TESTS
using System.Collections.Generic;
using DribbleToSchool.Presentation;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>A kid who was hidden when the shop dressed the player comes out in the same clothes when shown.</summary>
    public class OutfitMemoryTests
    {
        /// <summary>A kid that writes down what it is told.</summary>
        class Kid : IOutfit, IAccentOutfit
        {
            public readonly List<string> calls = new List<string>();
            public void SetOutfit(Color shirt, Color legwear) { calls.Add("outfit " + shirt + " " + legwear); }
            public void ResetOutfit() { calls.Add("reset"); }
            public void SetAccent(Color accent) { calls.Add("accent " + accent); }
        }

        [Test]
        public void NothingRememberedMeansTheClothesTheKidWasMadeIn()
        {
            var kid = new Kid();
            new OutfitMemory().ReplayOn(kid);
            Assert.AreEqual(new[] { "reset" }, kid.calls.ToArray());
        }

        [Test]
        public void ARememberedOutfitIsReplayedInOrder()
        {
            var memory = new OutfitMemory();
            memory.SetOutfit(Color.red, Color.blue);
            memory.SetAccent(Color.yellow);
            var kid = new Kid();
            memory.ReplayOn(kid);
            Assert.AreEqual(new[] { "reset", "outfit " + Color.red + " " + Color.blue, "accent " + Color.yellow }, kid.calls.ToArray());
        }

        [Test]
        public void TheLatestOutfitWins()
        {
            var memory = new OutfitMemory();
            memory.SetOutfit(Color.red, Color.blue);
            memory.SetOutfit(Color.green, Color.black);
            var kid = new Kid();
            memory.ReplayOn(kid);
            Assert.AreEqual("outfit " + Color.green + " " + Color.black, kid.calls[1]);
        }

        [Test]
        public void ResettingForgetsTheOutfitAndTheAccent()
        {
            var memory = new OutfitMemory();
            memory.SetOutfit(Color.red, Color.blue);
            memory.SetAccent(Color.yellow);
            memory.Reset();
            Assert.IsFalse(memory.Dressed);
            Assert.IsFalse(memory.Accented);
            var kid = new Kid();
            memory.ReplayOn(kid);
            Assert.AreEqual(new[] { "reset" }, kid.calls.ToArray());
        }

        [Test]
        public void AnAccentWithNoOpacityIsReplayedSoTheTieStaysOff()
        {
            var memory = new OutfitMemory();
            memory.SetOutfit(Color.white, Color.gray);
            var noTie = new Color(1f, 1f, 1f, 0f);
            memory.SetAccent(noTie);
            var kid = new Kid();
            memory.ReplayOn(kid);
            Assert.AreEqual("accent " + noTie, kid.calls[kid.calls.Count - 1]);
        }

        [Test]
        public void ReplayingOnSomethingThatCannotBeDressedDoesNothing()
        {
            var memory = new OutfitMemory();
            memory.SetOutfit(Color.red, Color.blue);
            memory.ReplayOn(null);               // neither of these may throw
            memory.ReplayOn("not an outfit");
        }
    }
}
#endif
