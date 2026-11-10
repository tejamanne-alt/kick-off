#if UNITY_INCLUDE_TESTS
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.RegularExpressions;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// Unity can only point a scene at a script whose file is named like its class. A MonoBehaviour in a
    /// file of another name (or a second one in a file) is saved into the generated scenes with a script
    /// reference that cannot be resolved, and the player then stops while loading them with "The file ...
    /// is corrupted! Remove it and launch unity again! [Position out of bounds!]". Every component and
    /// every ScriptableObject of the game gets a file of its own, named for it.
    /// </summary>
    public class ScriptConventionTests
    {
        static IEnumerable<Type> GameComponents()
        {
            Type[] types;
            try
            {
                types = typeof(DribbleToSchool.Core.LevelManager).Assembly.GetTypes();
            }
            catch (ReflectionTypeLoadException e)
            {
                types = e.Types.Where(t => t != null).ToArray();
            }
            return types.Where(t => t.Namespace != null && t.Namespace.StartsWith("DribbleToSchool")
                && !t.IsNested && !t.IsAbstract && !t.IsGenericTypeDefinition
                && (typeof(MonoBehaviour).IsAssignableFrom(t) || typeof(ScriptableObject).IsAssignableFrom(t)));
        }

        [Test]
        public void EveryComponentLivesInAFileNamedLikeIt()
        {
            var components = GameComponents().ToList();
            Assert.Greater(components.Count, 50, "the scan should find the game's components");
            foreach (var type in components)
            {
                var files = Directory.GetFiles(Application.dataPath, type.Name + ".cs", SearchOption.AllDirectories);
                Assert.IsTrue(files.Length > 0, type.FullName + " must be in a file called " + type.Name + ".cs (one component per file)");
            }
        }

        [Test]
        public void NoFileHoldsTwoComponents()
        {
            // A file named for one component that also declares another would put that second one in a file of the wrong name.
            var names = new HashSet<string>(GameComponents().Select(t => t.Name));
            var declaration = new Regex(@"^\s*(?:public\s+|internal\s+)?(?:sealed\s+|abstract\s+|partial\s+|static\s+)*class\s+(\w+)", RegexOptions.Multiline);
            var problems = new List<string>();
            foreach (string name in names)
            {
                foreach (string path in Directory.GetFiles(Application.dataPath, name + ".cs", SearchOption.AllDirectories))
                {
                    var also = declaration.Matches(File.ReadAllText(path)).Cast<Match>()
                        .Select(m => m.Groups[1].Value).Where(n => n != name && names.Contains(n)).ToArray();
                    if (also.Length > 0) problems.Add(Path.GetFileName(path) + " also declares " + string.Join(", ", also));
                }
            }
            Assert.IsEmpty(problems, "files that hold two components: " + string.Join("; ", problems.ToArray()));
        }

        /// <summary>
        /// Unity APIs that a newer Unity 6 refuses to compile (an [Obsolete] error), which an older editor still accepts. One
        /// call stops the whole game assembly from compiling, and the editor opens in Safe Mode (docs/LEARNINGS.md A11). The
        /// full check, against Unity's own reference source for any version, is tools/unity_api_check.
        /// </summary>
        static readonly (string pattern, string why)[] RemovedApis =
        {
            (@"\bGetInstanceID\s*\(", "Object.GetInstanceID is an error from Unity 6.5 (use GetEntityId, or no id at all)"),
            (@"\bInstanceIDToObject\s*\(", "EditorUtility.InstanceIDToObject takes an EntityId from Unity 6.5"),
            (@"new\s+Material\s*\(\s*\"", "creating a material from shader source text is an error"),
        };

        [Test]
        public void NoScriptCallsAnApiANewerUnityRemoved()
        {
            var root = Path.Combine(Application.dataPath, "_Game");
            var problems = new List<string>();
            foreach (var file in Directory.GetFiles(root, "*.cs", SearchOption.AllDirectories))
            {
                if (file.EndsWith("ScriptConventionTests.cs")) continue;
                var lines = File.ReadAllLines(file);
                for (int i = 0; i < lines.Length; i++)
                {
                    string code = lines[i].Split(new[] { "//" }, StringSplitOptions.None)[0];
                    foreach (var (pattern, why) in RemovedApis)
                        if (Regex.IsMatch(code, pattern)) problems.Add(Path.GetFileName(file) + ":" + (i + 1) + ": " + why);
                }
            }
            Assert.IsEmpty(problems, string.Join("\n", problems.ToArray()));
        }
    }
}
#endif
