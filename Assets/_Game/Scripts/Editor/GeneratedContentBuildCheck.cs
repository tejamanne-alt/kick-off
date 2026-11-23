using UnityEditor.Build;
using UnityEditor.Build.Reporting;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Stops a player build (Unity's own Build button included) when the generated levels on disk were built by an older version
    /// of the code, or a Florida leg was built without its Miami district: the phone would get the old levels, whatever the code
    /// says (docs/LEARNINGS.md A17). BuildScripts rebuilds them before it builds; this catches every other way in.
    /// </summary>
    public class GeneratedContentBuildCheck : IPreprocessBuildWithReport
    {
        public int callbackOrder { get { return -100; } }

        public void OnPreprocessBuild(BuildReport report)
        {
            if (!GeneratedContent.OutOfDate) return;
            throw new BuildFailedException("[Kick Off] The generated levels are out of date (built by v" + GeneratedContent.BuiltVersion
                + ", the code is v" + GeneratedContent.Version + ", or some are missing or unfinished: see the Console). Run Kick Off > "
                + "Rebuild All Levels, then build again.");
        }
    }
}
