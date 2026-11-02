using UnityEngine;

namespace DribbleToSchool.Levels
{
    /// <summary>
    /// The kid's house, the one every story level starts in front of (docs/WORLD_MAP.md, "Every level starts at home"). The
    /// level builder (<c>LevelBuildKit.TrackBuilder.HomeFront</c>) makes it from the Buildings kit's HouseGable with these
    /// colours, and the map screen draws the same house, so the two always match: a cream house with a warm red front
    /// door under a slate roof, number 7.
    /// </summary>
    public static class HomeInfo
    {
        /// <summary>The Buildings kit model (Art/Models/Buildings/HouseGable.fbx).</summary>
        public const string HouseModel = "HouseGable";

        /// <summary>The number on the gatepost.</summary>
        public const string HouseNumber = "7";

        /// <summary>
        /// The front door's place on the model, in metres from the middle of its front wall (to the left: the
        /// door of a HouseGable is on its left, as seen from the street).
        /// </summary>
        public const float DoorFromMiddle = -2.4f;

        /// <summary>The walls (the model's part 1).</summary>
        public static readonly Color WallColor = new Color(0.97f, 0.93f, 0.82f);

        /// <summary>The front door (the model's part 2: its doors, shutters and window boxes take the colour).</summary>
        public static readonly Color DoorColor = new Color(0.80f, 0.22f, 0.17f);

        /// <summary>The roof (the model's part 3).</summary>
        public static readonly Color RoofColor = new Color(0.34f, 0.37f, 0.45f);
    }
}
