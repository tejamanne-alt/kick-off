using System.Collections.Generic;
using DribbleToSchool.Core;
using DribbleToSchool.Presentation;
using UnityEditor;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    public static partial class LevelBuildKit
    {
        /// <summary>Every playable kid built under one parent (see <see cref="BuildCast"/>).</summary>
        public struct Cast
        {
            /// <summary>The first kid that loaded: what the level treats as "the" kid (animator, fallbacks).</summary>
            public CharacterParts main;
            /// <summary>All the kids that loaded, in roster order (just <see cref="main"/> when only a fallback character could be built).</summary>
            public List<CharacterParts> all;
            /// <summary>What the shop's outfits dress: the CharacterChoice when there are several kids, else the kid's own outfit.</summary>
            public MonoBehaviour outfit;
            /// <summary>The backpack pennants of all the kids (the shop's backpack flags).</summary>
            public List<SpriteRenderer> flags;
            /// <summary>The Locker Room's bags on the kids who wear them (one BagWear a kid).</summary>
            public List<BagWear> bags;
        }

        /// <summary>
        /// The playable kids of the <see cref="PlayerRoster"/>, each modelled in Blender, built under
        /// <paramref name="parent"/> (the level's Kid, the menu's Teen) with their feet on the kid's,
        /// and a CharacterChoice on <paramref name="parent"/> that shows the one Settings picked. A
        /// kid whose model is missing is left out with a warning; with none at all, the younger
        /// Blender kid, or the procedural one, plays. The caller adds what animates them (KidAnimator,
        /// MenuKid) to each <see cref="Cast.all"/> rig.
        /// </summary>
        static Cast BuildCast(Transform parent)
        {
            var cast = new Cast { all = new List<CharacterParts>(), flags = new List<SpriteRenderer>(), bags = new List<BagWear>() };
            var ids = new List<string>();
            foreach (var info in PlayerRoster.All)
            {
                Material material;
                if (!Art.players.TryGetValue(info.model, out material) || material == null)
                {
                    Debug.LogWarning("[Kick Off] " + ModelsDir + "/" + info.model + ".fbx is missing: " + info.id + " is left out of the player choice.");
                    continue;
                }
                var parts = BuildModelCharacter(parent, info.model, material, info.neckHeight, TeenFeet(info.neckHeight), true);
                if (parts.rig == null) continue;   // BuildModelCharacter has said why
                parts.visual.name = info.model;
                if (parts.bags != null && info.wearsBags)
                {
                    var wear = parts.visual.gameObject.AddComponent<BagWear>();
                    wear.playerId = info.id;
                    wear.bags = parts.bags.ToArray();
                    wear.bagIds = new string[parts.bags.Count];
                    for (int b = 0; b < parts.bags.Count; b++) wear.bagIds[b] = DribbleToSchool.Cosmetics.Bags.IdOfMesh(parts.bags[b].name);
                    wear.onBag = parts.onBag != null ? parts.onBag.ToArray() : new GameObject[0];
                    cast.bags.Add(wear);
                }
                else if (parts.bags != null)
                {
                    // (a kid with a bag of their own whose model has bags fitted all the same: never worn)
                    foreach (var r in parts.bags) Object.DestroyImmediate(r.gameObject);
                }
                cast.all.Add(parts);
                ids.Add(info.id);
            }

            if (cast.all.Count == 0)
            {
                // Without the playable models: the younger Blender kid, or the procedural one.
                var fallback = BuildModelCharacter(parent, "Kid", Art.kid, 1.3f, Vector3.zero, true);
                if (fallback.rig == null)
                    fallback = BuildCharacter(parent, "Visual", Vector2.zero, 1f, KidColor, new Color(0.22f, 0.23f, 0.42f),
                        new Color(0.16f, 0.15f, 0.2f), true);   // glossy near-black hair
                cast.all.Add(fallback);
            }

            cast.main = cast.all[0];
            cast.outfit = cast.main.outfit;
            foreach (var parts in cast.all)
                if (parts.flag != null) cast.flags.Add(parts.flag);

            if (cast.all.Count > 1)
            {
                var choice = parent.gameObject.AddComponent<CharacterChoice>();
                choice.ids = ids.ToArray();
                choice.characters = new GameObject[cast.all.Count];
                choice.outfits = new MonoBehaviour[cast.all.Count];
                for (int i = 0; i < cast.all.Count; i++)
                {
                    choice.characters[i] = cast.all[i].visual.gameObject;
                    choice.outfits[i] = cast.all[i].outfit;
                }
                cast.outfit = choice;
            }
            return cast;
        }
    }
}
