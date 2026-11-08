using System.Collections.Generic;

namespace DribbleToSchool.Core
{
    /// <summary>Which school a playable kid goes to: the picker shows the two groups apart.</summary>
    public enum SchoolLevel
    {
        High,
        Primary,
    }

    /// <summary>
    /// One playable kid. The files are all named from <see cref="model"/> (tools/blender): the
    /// model, its colours and atlas in Art/Models (Boy.fbx, Boy.json, BoyAtlas.png) and the
    /// portrait the picker shows in Resources/UI (PlayerBoy.png).
    /// </summary>
    public sealed class PlayerInfo
    {
        /// <summary>What GameSettings.Character stores. The first two are the original boy and girl: saved choices stay valid.</summary>
        public readonly string id;
        /// <summary>The model's name: Art/Models/&lt;model&gt;.fbx, &lt;model&gt;.json, &lt;model&gt;Atlas.png and Resources/UI/Player&lt;model&gt;.png.</summary>
        public readonly string model;
        /// <summary>The string-table key of the name shown on cards.</summary>
        public readonly string nameKey;
        public readonly SchoolLevel level;
        /// <summary>Where the model's Head bone sits above its feet in the game (LevelBuildKit.BuildModelCharacter scales to it).</summary>
        public readonly float neckHeight;
        /// <summary>How tall the kid stands (metres): the menu's camera frames the whole kid from it.</summary>
        public readonly float height;
        /// <summary>
        /// Modelled without a bag of their own, so they wear the Locker Room's bags (Cosmetics/Bags; each bag is fitted
        /// to them in their model file by tools/blender/meshy_bag.py). The others carry the bag they were modelled with.
        /// </summary>
        public readonly bool wearsBags;

        public PlayerInfo(string id, string model, string nameKey, SchoolLevel level, float neckHeight, float height, bool wearsBags = false)
        {
            this.wearsBags = wearsBags;
            this.id = id;
            this.model = model;
            this.nameKey = nameKey;
            this.level = level;
            this.neckHeight = neckHeight;
            this.height = height;
        }

        /// <summary>Resources path of the portrait (without the extension).</summary>
        public string PortraitPath { get { return "UI/Player" + model; } }
    }

    /// <summary>
    /// Every kid the player can be, in the order the picker lists them. The level builders put all
    /// of them in each scene (CharacterChoice shows the chosen one), the picker and the title
    /// screen read the names and portraits, and the menu camera reads the heights. To add a kid:
    /// build the model with tools/blender, add a row here and its name to the string tables.
    /// </summary>
    public static class PlayerRoster
    {
        /// <summary>Who plays until another is picked.</summary>
        public const string DefaultId = "boy";

        public static readonly PlayerInfo[] All =
        {
            // The high-school teens, Ren and Hana (tools/blender, see its README): about 1.77 m and 1.65 m.
            new PlayerInfo("boy", "Boy", "player.boy", SchoolLevel.High, 1.5f, 1.77f),
            // Hana (girl) is made from a supplied rigged model by tools/blender/meshy_rigged.py --profile varsity: 1.65 m, her Head bone at
            // 0.877 of it. She has no bag of her own: she wears the Locker Room's (wearsBags).
            new PlayerInfo("girl", "Girl", "player.girl", SchoolLevel.High, 1.446f, 1.65f, true),
            // Max, the backpack boy (tools/blender/meshy_teen.py, from a supplied model): about 1.75 m, his Head bone at 0.878 of it.
            new PlayerInfo("backpackBoy", "BackpackBoy", "player.backpackBoy", SchoolLevel.High, 1.533f, 1.75f),
            // The primary-school kids (tools/blender, see its README: primary.py prints each one's neck height): 1.27 to 1.34 m.
            // Neck height = the Head bone's height x the standing height / the model's own height.
            // Kai (primaryBoy) is made from a supplied rigged model by tools/blender/meshy_rigged.py --profile plaid: 1.30 m, his Head bone at 0.847 of it.
            // He has no bag of his own: he wears the Locker Room's (wearsBags).
            new PlayerInfo("primaryBoy", "PrimaryBoy", "player.primaryBoy", SchoolLevel.Primary, 1.101f, 1.30f, true),
            // Mia (primaryGirl) is made from a supplied rigged model by tools/blender/meshy_rigged.py --profile explorer: 1.27 m, her Head bone at 0.827 of it.
            // She has no bag of her own: she wears the Locker Room's (wearsBags).
            new PlayerInfo("primaryGirl", "PrimaryGirl", "player.primaryGirl", SchoolLevel.Primary, 1.050f, 1.27f, true),
            // Leo (primaryBoy2) is made from a supplied rigged model by tools/blender/meshy_rigged.py: 1.32 m, his Head bone at 0.844 of it.
            // He has no bag of his own: he wears the Locker Room's (wearsBags).
            new PlayerInfo("primaryBoy2", "PrimaryBoy2", "player.primaryBoy2", SchoolLevel.Primary, 1.114f, 1.32f, true),
            // Zoe (primaryGirl2) is made from a supplied rigged model by tools/blender/meshy_rigged.py --profile rainbow: 1.29 m, her Head bone at 0.852 of it.
            // She has no bag of her own: she wears the Locker Room's (wearsBags).
            new PlayerInfo("primaryGirl2", "PrimaryGirl2", "player.primaryGirl2", SchoolLevel.Primary, 1.099f, 1.29f, true),
        };

        /// <summary>The position of <paramref name="id"/> in <see cref="All"/>, or -1.</summary>
        public static int IndexOf(string id)
        {
            for (int i = 0; i < All.Length; i++)
                if (All[i].id == id) return i;
            return -1;
        }

        /// <summary><paramref name="id"/> if it names a kid, else the default (a stale or hand-edited save).</summary>
        public static string Normalize(string id)
        {
            return IndexOf(id) >= 0 ? id : DefaultId;
        }

        /// <summary>The kid called <paramref name="id"/>; the default one for an unknown id.</summary>
        public static PlayerInfo Get(string id)
        {
            int i = IndexOf(id);
            return All[i >= 0 ? i : IndexOf(DefaultId)];
        }

        /// <summary>The kids of one school, in picker order.</summary>
        public static List<PlayerInfo> Of(SchoolLevel level)
        {
            var list = new List<PlayerInfo>();
            foreach (var info in All)
                if (info.level == level) list.Add(info);
            return list;
        }
    }
}
