using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;

namespace DribbleToSchool.Analytics
{
    /// <summary>Somewhere analytics events go (local file, console, or a backend you add).</summary>
    public interface IAnalyticsSink
    {
        void Send(string eventName, IList<KeyValuePair<string, string>> fields);
    }

    /// <summary>
    /// Privacy-first gameplay analytics: events stay on the device by default
    /// (a capped JSON-lines file, plus the console in development builds).
    /// Nothing personal is recorded. Add your own sink (e.g. a backend) with
    /// AddSink once you have consent and a privacy policy that covers it.
    /// </summary>
    public static class AnalyticsService
    {
        static readonly List<IAnalyticsSink> sinks = new List<IAnalyticsSink>();
        static bool initialised;

        public static void AddSink(IAnalyticsSink sink)
        {
            Init();
            if (sink != null && !sinks.Contains(sink)) sinks.Add(sink);
        }

        /// <summary>Track an event with alternating key/value pairs: Track("level_complete", "level", "L01", "stars", 3).</summary>
        public static void Track(string eventName, params object[] keyValues)
        {
            Init();
            var fields = new List<KeyValuePair<string, string>>();
            for (int i = 0; i + 1 < keyValues.Length; i += 2)
                fields.Add(new KeyValuePair<string, string>(Convert.ToString(keyValues[i]),
                    Convert.ToString(keyValues[i + 1], System.Globalization.CultureInfo.InvariantCulture)));
            foreach (var sink in sinks)
            {
                try { sink.Send(eventName, fields); }
                catch (Exception e) { Debug.LogWarning("[Analytics] " + e.Message); }
            }
        }

        static void Init()
        {
            if (initialised) return;
            initialised = true;
            sinks.Add(new LocalFileSink());
            if (Application.isEditor || Debug.isDebugBuild) sinks.Add(new ConsoleSink());
        }

        class ConsoleSink : IAnalyticsSink
        {
            public void Send(string eventName, IList<KeyValuePair<string, string>> fields)
            {
                var sb = new StringBuilder("[Analytics] ").Append(eventName);
                foreach (var f in fields) sb.Append(' ').Append(f.Key).Append('=').Append(f.Value);
                Debug.Log(sb.ToString());
            }
        }

        /// <summary>Appends JSON lines to persistentDataPath/analytics.jsonl, trimmed to the newest ~2000 events.</summary>
        class LocalFileSink : IAnalyticsSink
        {
            const int MaxLines = 2000;
            readonly string path = Path.Combine(Application.persistentDataPath, "analytics.jsonl");
            int writes;

            public void Send(string eventName, IList<KeyValuePair<string, string>> fields)
            {
                var sb = new StringBuilder("{\"t\":\"").Append(DateTime.UtcNow.ToString("o")).Append("\",\"e\":\"").Append(Escape(eventName)).Append('"');
                foreach (var f in fields) sb.Append(",\"").Append(Escape(f.Key)).Append("\":\"").Append(Escape(f.Value)).Append('"');
                sb.Append('}');
                try
                {
                    File.AppendAllText(path, sb.ToString() + "\n");
                    if (++writes % 200 == 0) Trim();
                }
                catch (Exception) { }
            }

            void Trim()
            {
                var lines = File.ReadAllLines(path);
                if (lines.Length <= MaxLines) return;
                var keep = new string[MaxLines];
                Array.Copy(lines, lines.Length - MaxLines, keep, 0, MaxLines);
                File.WriteAllLines(path, keep);
            }

            static string Escape(string s)
            {
                return (s ?? "").Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", " ");
            }
        }
    }
}
