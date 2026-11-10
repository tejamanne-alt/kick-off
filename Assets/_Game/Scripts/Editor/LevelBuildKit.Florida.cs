using DribbleToSchool.Core;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The school at the end of Seaside Road in the Florida add-on (review/florida/refs, F3-6): Seagrove High, a Florida
    /// public high school of cream and teal concrete block, its front to the street, behind a white aluminium fence and an
    /// open gate between stucco piers, its marquee by the way in, the US and Florida flags, a covered walkway in to its doors
    /// and a portable classroom beyond. The way through the gate and the goal are the same as every school end's.
    /// </summary>
    public static partial class LevelBuildKit
    {
        public partial class TrackBuilder
        {
            /// <summary>Builds Florida's school at the gate line wx (the level's goal is at x). False without the Florida kit.</summary>
            bool FloridaSchool(Transform school, float x, float wx, float groundTop)
            {
                if (!Florida || KitModel(school, "Florida", "SchoolGateFL", new Vector3(wx, groundTop, 0f), 90f) == null) return false;
                float farZ = StreetBuilder.PathHalf + 0.35f, nearZ = -StreetBuilder.PathHalf - 0.3f;
                // The fence runs back from the far pier, in 2.4 m sections.
                for (float z = 2.5f + 1.2f; z < 15f; z += 2.4f)
                    KitModel(school, "Florida", "FenceAluFL", new Vector3(wx, groundTop, z), 90f);
                RoadBollards(school, wx, nearZ, groundTop);
                // The marquee by the way in, the school across its yard with a walkway to its doors, the flags, a portable.
                KitModel(school, "Florida", "MarqueeFL", new Vector3(wx - 3.4f, groundTop, farZ + 1.2f));
                KitModel(school, "Florida", "SchoolFL", new Vector3(x + 17f, groundTop, 7.5f));
                KitModel(school, "Florida", "WalkwayFL", new Vector3(x + 4.6f, groundTop, farZ + 0.6f));
                KitModel(school, "Florida", "FlagpoleFL", new Vector3(x + 9.5f, groundTop, 5.4f));
                KitModel(school, "Florida", "PortableFL", new Vector3(x + 40f, groundTop, 4.5f));
                KitModel(school, "Plants", "BroadleafWide", new Vector3(x + 2.2f, groundTop, 5.6f), 40f);
                KitModel(school, "Plants", "PalmSabal", new Vector3(wx - 1.2f, groundTop, farZ + 1.6f), 20f, 0.9f);

                // Through the gate: the whole school ground past the gate line counts, as at every school (SchoolGrounds).
                const float grounds = 40f;
                var goalGo = new GameObject("GoalZone");
                goalGo.transform.SetParent(school, false);
                goalGo.transform.position = new Vector3(wx + grounds * 0.5f, groundTop + 8f, 0f);
                var trigger = goalGo.AddComponent<BoxCollider2D>();
                trigger.isTrigger = true;
                trigger.size = new Vector2(grounds, 20f);
                goalGo.AddComponent<GoalZone>();
                school.gameObject.AddComponent<StaticBatcher>();
                return true;
            }
        }
    }
}
