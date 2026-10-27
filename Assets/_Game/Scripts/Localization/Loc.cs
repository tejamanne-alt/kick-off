using System.Collections.Generic;
using DribbleToSchool.Core;
using UnityEngine;

namespace DribbleToSchool.Localization
{
    /// <summary>
    /// Tiny string-table localization. Keys live in StringTables; missing keys
    /// fall back to English, then to the provided fallback, then to the key.
    /// The language follows Settings, or the device language on first launch.
    /// </summary>
    public static class Loc
    {
        public static readonly string[] Languages = { "en", "es" };
        public static readonly string[] LanguageNames = { "English", "Español" };

        public static event System.Action Changed;

        static string current;
        static Dictionary<string, string> table;

        public static string Current
        {
            get
            {
                if (current == null) Load();
                return current;
            }
        }

        public static void SetLanguage(string code)
        {
            GameSettings.Language = code;
            current = null;
            Load();
            if (Changed != null) Changed();
        }

        static void Load()
        {
            string code = GameSettings.Language;
            if (string.IsNullOrEmpty(code))
                code = Application.systemLanguage == SystemLanguage.Spanish ? "es" : "en";
            current = System.Array.IndexOf(Languages, code) >= 0 ? code : "en";
            table = StringTables.For(current);
        }

        /// <summary>Translate a key.</summary>
        public static string T(string key, string fallback = null)
        {
            if (string.IsNullOrEmpty(key)) return fallback ?? "";
            if (table == null) Load();
            string s;
            if (table.TryGetValue(key, out s)) return s;
            if (current != "en" && StringTables.For("en").TryGetValue(key, out s)) return s;
            return fallback ?? key;
        }

        /// <summary>Translate and format, e.g. F("hud.coins", 3, 10).</summary>
        public static string F(string key, params object[] args)
        {
            return string.Format(T(key), args);
        }
    }
}
