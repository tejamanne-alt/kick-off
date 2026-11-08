using System;
using System.Collections.Generic;
using DribbleToSchool.Core;
using DribbleToSchool.Progression;
using UnityEngine;

namespace DribbleToSchool.Cosmetics
{
    /// <summary>
    /// Which bag each kid wears (the Locker Room's Bags tab) and the colour bags are worn in (Settings). Bags are
    /// optional: each kid who was modelled without a bag of their own (<see cref="PlayerInfo.wearsBags"/>) has their own
    /// choice, a bag or none, and the same bag can be worn by any of them. A kid nobody has chosen for wears
    /// <see cref="DefaultId"/>. The colour is one for all bags; the first swatch is the bag as it was made.
    /// </summary>
    public static class Bags
    {
        public const string NoneId = "bag_none";
        public const string DefaultId = "bag_kickoff";
        /// <summary>The red race-car backpack (a car's face, headlights and wheels; tools/blender/meshy_bag.py --id RaceCar).</summary>
        public const string RaceCarId = "bag_racecar";

        /// <summary>The pink glitter unicorn backpack (a unicorn's horn and ears, rainbow chevrons; meshy_bag.py --id Unicorn).</summary>
        public const string UnicornId = "bag_unicorn";

        /// <summary>The bags every kid has from the start (SaveSystem owns them in every save).</summary>
        public static readonly string[] Starter = { NoneId, DefaultId, RaceCarId, UnicornId };

        /// <summary>
        /// The colours bags can be worn in (Settings): the first, the bag's own colours; the rest recolour its cloth
        /// (the zips, the logo and the mesh pockets keep theirs). The string-table key of each is "bagColour." + its name.
        /// </summary>
        public static readonly Swatch[] Colours =
        {
            new Swatch("original", new Color(0.53f, 0.08f, 0.73f), false),
            new Swatch("red", new Color(0.86f, 0.13f, 0.16f), true),
            new Swatch("orange", new Color(0.98f, 0.52f, 0.1f), true),
            new Swatch("yellow", new Color(1f, 0.8f, 0.15f), true),
            new Swatch("green", new Color(0.2f, 0.7f, 0.3f), true),
            new Swatch("blue", new Color(0.16f, 0.42f, 0.9f), true),
            new Swatch("pink", new Color(0.98f, 0.45f, 0.72f), true),
            new Swatch("black", new Color(0.16f, 0.16f, 0.19f), true),
        };

        public struct Swatch
        {
            public readonly string name;
            /// <summary>What the cloth is recoloured to (or, for the original, how the swatch is drawn).</summary>
            public readonly Color color;
            /// <summary>False for the bag's own colours.</summary>
            public readonly bool tints;

            public Swatch(string name, Color color, bool tints)
            {
                this.name = name;
                this.color = color;
                this.tints = tints;
            }
        }

        /// <summary>Fired when a kid's bag changes (the bag colour is a setting: GameSettings.Changed).</summary>
        public static event Action Changed;

        /// <summary>The bag <paramref name="playerId"/> wears: a bag's id, or <see cref="NoneId"/>.</summary>
        public static string For(string playerId)
        {
            var list = SaveSystem.Data.bags;
            if (list != null)
                foreach (var choice in list)
                    if (choice != null && choice.player == playerId) return string.IsNullOrEmpty(choice.bag) ? NoneId : choice.bag;
            return DefaultId;
        }

        /// <summary>Put <paramref name="bagId"/> (or <see cref="NoneId"/>) on <paramref name="playerId"/> and save.</summary>
        public static void Set(string playerId, string bagId)
        {
            var d = SaveSystem.Data;
            if (d.bags == null) d.bags = new List<BagChoice>();
            BagChoice found = null;
            foreach (var choice in d.bags)
                if (choice != null && choice.player == playerId) found = choice;
            if (found == null) d.bags.Add(found = new BagChoice { player = playerId });
            found.bag = bagId;
            SaveSystem.Save();
            if (Changed != null) Changed();
        }

        /// <summary>Can <paramref name="playerId"/> wear the Locker Room's bags (they were modelled without one)?</summary>
        public static bool CanWear(string playerId)
        {
            return PlayerRoster.Get(playerId).wearsBags;
        }

        /// <summary>The bag colour chosen in Settings (an index into <see cref="Colours"/>).</summary>
        public static Swatch Colour()
        {
            return Colours[Mathf.Clamp(GameSettings.BagColour, 0, Colours.Length - 1)];
        }

        /// <summary>A bag item's id from the name of its mesh in a kid's model ("Bag_KickOff" is "bag_kickoff").</summary>
        public static string IdOfMesh(string meshName)
        {
            return "bag_" + meshName.Substring(meshName.IndexOf('_') + 1).ToLowerInvariant();
        }
    }
}
