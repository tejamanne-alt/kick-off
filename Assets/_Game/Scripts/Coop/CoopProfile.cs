using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using UnityEngine;

namespace DribbleToSchool.Coop
{
    /// <summary>
    /// Who this phone is in Co-op: the name the player typed for other phones, kept in PlayerPrefs (empty: the default
    /// "Player 2" for their slot); a seed kept with it that the host turns into the tag shown after the name ("#K7QX"), the
    /// same on every visit, so friends recognise each other and two players who type the same name are still told apart;
    /// and an id for this run of the app, new at every launch. (A phone whose app was closed mid-race and opened again has
    /// lost its run: with a new id it joins as a new player, instead of being mistaken for the one that was racing.)
    /// </summary>
    public static class CoopProfile
    {
        const string NameKey = "coop.name";
        // (the key the seed has always been kept under: it was the install id before ids became one per launch)
        const string TagSeedKey = "coop.uid";

        static uint launchUid;

        /// <summary>This run of the app's id (never 0).</summary>
        public static uint Uid
        {
            get
            {
                if (launchUid == 0) launchUid = Random32();
                return launchUid;
            }
        }

        /// <summary>The seed of this install's tag (never 0), made the first time it is asked for.</summary>
        public static uint TagSeed
        {
            get
            {
                int stored = PlayerPrefs.GetInt(TagSeedKey, 0);
                if (stored != 0) return (uint)stored;
                uint seed = Random32();
                PlayerPrefs.SetInt(TagSeedKey, (int)seed);
                PlayerPrefs.Save();
                return seed;
            }
        }

        static uint Random32()
        {
            var bytes = System.Guid.NewGuid().ToByteArray();
            uint id = System.BitConverter.ToUInt32(bytes, 0) ^ System.BitConverter.ToUInt32(bytes, 4);
            return id != 0 ? id : 0x4B4Fu;
        }

        /// <summary>The name for other phones, cleaned (CoopRules.CleanName); empty for the default.</summary>
        public static string Name
        {
            get { return CoopRules.CleanName(PlayerPrefs.GetString(NameKey, "")); }
            set
            {
                PlayerPrefs.SetString(NameKey, CoopRules.CleanName(value));
                PlayerPrefs.Save();
            }
        }

        /// <summary>The kid this phone plays, as an index into the roster (what the others' ghosts show).</summary>
        public static byte Character
        {
            get { return (byte)Mathf.Max(0, PlayerRoster.IndexOf(GameSettings.Character)); }
        }

        /// <summary>The roster id for a player's kid index (the default kid for an unknown one).</summary>
        public static string CharacterId(byte index)
        {
            return index < PlayerRoster.All.Length ? PlayerRoster.All[index].id : PlayerRoster.DefaultId;
        }

        /// <summary>"Player 2" in the language of this phone.</summary>
        public static string DefaultFormat { get { return Loc.T("coop.defaultName"); } }

        public static string DisplayName(CoopPlayer p) { return CoopRules.DisplayName(p, DefaultFormat); }

        /// <summary>"Hana #K7QX".</summary>
        public static string FullName(CoopPlayer p) { return CoopRules.FullName(p, DefaultFormat); }
    }

    /// <summary>Each slot's colour (their ghost's ring and name tag, their dot on the race bar) and how a status reads.</summary>
    public static class CoopPalette
    {
        static readonly Color[] Slots =
        {
            new Color(0.98f, 0.54f, 0.18f),   // 1 orange
            new Color(0.22f, 0.55f, 0.95f),   // 2 blue
            new Color(0.25f, 0.75f, 0.42f),   // 3 green
            new Color(0.72f, 0.42f, 0.92f),   // 4 purple
        };

        public static Color Of(int slot)
        {
            return Slots[Mathf.Clamp(slot, 0, Slots.Length - 1)];
        }

        /// <summary>"1st", "2nd"... in this phone's language.</summary>
        public static string Place(int place)
        {
            if (place <= 0) return "";
            string key = place <= 4 ? "coop.place." + place : "coop.place.n";
            return Loc.F(key, place);
        }
    }
}
