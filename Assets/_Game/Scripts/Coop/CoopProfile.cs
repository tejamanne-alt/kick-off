using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using UnityEngine;

namespace DribbleToSchool.Coop
{
    /// <summary>
    /// Who this phone is in Co-op, kept in PlayerPrefs: the name the player typed for other phones (empty: the default
    /// "Player 2" for their slot), and an install id the host turns into the tag shown after the name ("#K7QX"), the same
    /// on every visit, so friends recognise each other and two players who type the same name are still told apart.
    /// </summary>
    public static class CoopProfile
    {
        const string NameKey = "coop.name";
        const string UidKey = "coop.uid";

        /// <summary>This install's id (never 0), made the first time it is asked for.</summary>
        public static uint Uid
        {
            get
            {
                int stored = PlayerPrefs.GetInt(UidKey, 0);
                if (stored != 0) return (uint)stored;
                var bytes = System.Guid.NewGuid().ToByteArray();
                int id = System.BitConverter.ToInt32(bytes, 0) ^ System.BitConverter.ToInt32(bytes, 4);
                if (id == 0) id = 0x4B4F;
                PlayerPrefs.SetInt(UidKey, id);
                PlayerPrefs.Save();
                return (uint)id;
            }
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
