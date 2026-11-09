using System.Collections.Generic;
using DribbleToSchool.Core;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// The celebration for walking to school (Cosmetics/RouteRewards), shown once by the menu: for a route newly walked all the
    /// way, its medal (gold, on a ribbon in the route's colour) with its name, how many of the six ways are walked and what the
    /// next one wins; for the last of them, the Top of the Class trophy over a burst of light with all six medals under it. Any
    /// Locker Room prize the walks have just earned is shown on a card, with a button to the Locker Room.
    /// </summary>
    public static class SchoolRewardPanel
    {
        /// <summary>The medals' and the trophy's gold.</summary>
        public static readonly Color Gold = new Color(1f, 0.78f, 0.22f);
        static readonly Color GoldShade = new Color(0.62f, 0.4f, 0.08f);
        static readonly Color NotYet = new Color(0.78f, 0.8f, 0.85f);

        /// <summary>Every string key the panel uses (the tests check both languages have them).</summary>
        public static readonly string[] Keys =
        {
            "school.medalTitle", "school.medalBody", "school.medalBodyMany", "school.progress", "school.nextReward", "school.nextTrophy",
            "school.trophyTitle", "school.trophyBody", "school.prizes", "reward.great", "menu.locker",
        };

        // The card's rows, from its top edge down (each value is a row's top; the buttons sit along the bottom).
        const float TrophyTop = 92f, TrophySize = 230f, TrophyBodyTop = 336f, TrophyMedalsTop = 404f, TrophyMedal = 84f;
        const float MedalBodyTop = 96f, BigMedalTop = 158f, BigMedal = 160f, RouteNameTop = 326f, ProgressTop = 386f, SmallMedalsTop = 434f,
            SmallMedal = 60f, NextTop = 506f;
        const float PrizeCardHeight = 180f, ButtonsRoom = 170f;

        public static GameObject Open(Transform canvas, LevelCatalog catalog, CosmeticCatalog cosmetics, List<Route> medals, bool trophy,
            List<CosmeticItem> prizes, System.Action openLocker, System.Action onClose)
        {
            GameObject root;
            bool hasPrizes = prizes != null && prizes.Count > 0;
            float contentBottom = trophy ? TrophyMedalsTop + TrophyMedal : NextTop + 44f;
            float prizesTop = contentBottom + 26f;
            float height = (hasPrizes ? prizesTop + 44f + PrizeCardHeight : contentBottom) + ButtonsRoom;
            var card = UIKit.Modal(canvas, "SchoolReward", new Vector2(1240f, height), out root);
            var t = card.transform;
            UIKit.Header(t, Loc.T(trophy ? "school.trophyTitle" : "school.medalTitle"), 660f);
            var top = new Vector2(0.5f, 1f);

            if (trophy)
            {
                // The trophy over a burst of light, a shade behind it for depth, and every way's medal under it.
                float middle = -(TrophyTop + TrophySize * 0.5f);
                var glow = UIKit.Icon(t, "Glow", ProceduralSprites.SoftDisc, new Color(1f, 0.86f, 0.4f, 0.65f), 400f);
                UIKit.Place(glow.rectTransform, top, new Vector2(0f, middle), new Vector2(400f, 400f), new Vector2(0.5f, 0.5f));
                glow.gameObject.AddComponent<UIPulse>().amount = 0.06f;
                var shade = UIKit.Icon(t, "TrophyShade", ProceduralSprites.Trophy, GoldShade, TrophySize);
                UIKit.Place(shade.rectTransform, top, new Vector2(7f, middle - 8f), new Vector2(TrophySize, TrophySize), new Vector2(0.5f, 0.5f));
                var cup = UIKit.Icon(t, "Trophy", ProceduralSprites.Trophy, Gold, TrophySize);
                UIKit.Place(cup.rectTransform, top, new Vector2(0f, middle), new Vector2(TrophySize, TrophySize), new Vector2(0.5f, 0.5f));
                UIKit.PopIn(cup.gameObject, 0.15f).fromScale = 0.3f;
                var body = UIKit.Label(t, "Body", Loc.T("school.trophyBody"), 34, UITheme.Ink, TextAnchor.MiddleCenter, true);
                UIKit.Place(body.rectTransform, top, new Vector2(0f, -TrophyBodyTop), new Vector2(1100f, 50f));
                UIKit.Fit(body, 24);
                MedalRow(t, catalog, RouteTable.All, -TrophyMedalsTop, TrophyMedal, 40f);
            }
            else
            {
                var body = UIKit.Label(t, "Body", Loc.T(medals.Count > 1 ? "school.medalBodyMany" : "school.medalBody"), 32, UITheme.InkSoft, TextAnchor.MiddleCenter);
                UIKit.Place(body.rectTransform, top, new Vector2(0f, -MedalBodyTop), new Vector2(1100f, 50f));
                UIKit.Fit(body, 22);
                // The new medals, big, each with its route's name under it.
                int n = Mathf.Max(1, medals.Count);
                float step = Mathf.Min(260f, 1100f / n), first = -(n - 1) * step * 0.5f;
                for (int i = 0; i < medals.Count; i++)
                {
                    var route = medals[i];
                    var medal = MedalIcon(t, "Medal_" + route.id, ColourOf(catalog, route), BigMedal, true);
                    UIKit.Place(medal, top, new Vector2(first + i * step, -BigMedalTop), new Vector2(BigMedal, BigMedal));
                    UIKit.PopIn(medal.gameObject, 0.15f + i * 0.12f).fromScale = 0.3f;
                    var name = UIKit.Label(t, "Route_" + route.id, Loc.T(route.NameKey), 30, UITheme.Ink, TextAnchor.MiddleCenter, true);
                    UIKit.Place(name.rectTransform, top, new Vector2(first + i * step, -RouteNameTop), new Vector2(step - 10f, 44f));
                    UIKit.Fit(name, 20);
                }
                // How far along: the six medals small, walked or not, and what the next one wins.
                int walked = RouteRewards.Walked(), total = RouteRewards.RouteCount;
                var progress = UIKit.Label(t, "Progress", Loc.F("school.progress", walked, total), 28, UITheme.Navy, TextAnchor.MiddleCenter, true);
                UIKit.Place(progress.rectTransform, top, new Vector2(0f, -ProgressTop), new Vector2(1100f, 40f));
                UIKit.Fit(progress, 20);
                MedalRow(t, catalog, RouteTable.All, -SmallMedalsTop, SmallMedal, 22f);
                var next = RouteRewards.Next(cosmetics);
                if (next != null)
                {
                    int need = RouteRewards.StillNeeded(next);
                    string text = next.unlockValue >= total ? Loc.F("school.nextTrophy", need) : Loc.F("school.nextReward", need, next.displayName);
                    var hint = UIKit.Label(t, "Next", text, 27, UITheme.InkSoft, TextAnchor.MiddleCenter);
                    UIKit.Place(hint.rectTransform, top, new Vector2(0f, -NextTop), new Vector2(1100f, 40f));
                    UIKit.Fit(hint, 20);
                }
            }

            if (hasPrizes)
            {
                // The prizes, each on a card: its picture and its name.
                var heading = UIKit.Label(t, "Prizes", Loc.T("school.prizes").ToUpperInvariant(), 26, UITheme.Accent, TextAnchor.MiddleCenter, true);
                UIKit.Place(heading.rectTransform, top, new Vector2(0f, -prizesTop), new Vector2(600f, 36f));
                float cardW = 230f, gap = 24f, rowW = prizes.Count * cardW + (prizes.Count - 1) * gap;
                for (int i = 0; i < prizes.Count; i++)
                {
                    var item = prizes[i];
                    var face = UIKit.Card(t, "Prize_" + item.id, UITheme.Paper);
                    var holder = (RectTransform)face.transform.parent;
                    UIKit.Place(holder, top, new Vector2(-rowW * 0.5f + i * (cardW + gap) + cardW * 0.5f, -(prizesTop + 44f)), new Vector2(cardW, PrizeCardHeight));
                    UIKit.PopIn(holder.gameObject, 0.4f + i * 0.12f).fromScale = 0.3f;
                    var icon = CartoonPicture.On(UIKit.Icon(face.transform, "Icon", CosmeticArt.Icon(item), Color.white, 100f));
                    UIKit.Place(icon.rectTransform, top, new Vector2(0f, -16f), new Vector2(100f, 100f));
                    var name = UIKit.Label(face.transform, "Name", item.displayName, 28, UITheme.Ink, TextAnchor.MiddleCenter, true);
                    UIKit.Place(name.rectTransform, new Vector2(0.5f, 0f), new Vector2(0f, 14f), new Vector2(cardW - 20f, 40f));
                    UIKit.Fit(name, 20);
                }
            }

            System.Action close = () =>
            {
                Object.Destroy(root);
                if (onClose != null) onClose();
            };
            bool locker = hasPrizes && openLocker != null;
            var great = UIKit.Button(t, "Great", Loc.T("reward.great"), UITheme.Green, () => close(), 42);
            UIKit.Place((RectTransform)great.transform, new Vector2(0.5f, 0f), new Vector2(locker ? 190f : 0f, 40f), new Vector2(330f, 100f), new Vector2(0.5f, 0f));
            if (locker)
            {
                var toLocker = UIKit.Button(t, "Locker", Loc.T("menu.locker"), UITheme.Blue, () => { Object.Destroy(root); openLocker(); }, 38);
                UIKit.Place((RectTransform)toLocker.transform, new Vector2(0.5f, 0f), new Vector2(-190f, 40f), new Vector2(330f, 100f), new Vector2(0.5f, 0f));
            }
            GameEvents.Raise(GameEventType.Purchase, Vector2.zero);   // the shop's happy chime
            return root;
        }

        /// <summary>A row of every route's medal: gold on its ribbon once walked, grey before.</summary>
        static void MedalRow(Transform parent, LevelCatalog catalog, Route[] routes, float y, float size, float gap)
        {
            float rowW = routes.Length * size + (routes.Length - 1) * gap;
            for (int i = 0; i < routes.Length; i++)
            {
                bool walked = RouteRewards.IsWalked(routes[i]);
                var medal = MedalIcon(parent, "Small_" + routes[i].id, walked ? ColourOf(catalog, routes[i]) : NotYet, size, walked);
                UIKit.Place(medal, new Vector2(0.5f, 1f), new Vector2(-rowW * 0.5f + size * 0.5f + i * (size + gap), y), new Vector2(size, size));
            }
        }

        static Color ColourOf(LevelCatalog catalog, Route route)
        {
            var info = catalog != null ? catalog.Chapter(route.chapter) : null;
            return TownMap.RouteColor(route.id, info != null ? info.color : UITheme.Accent);
        }

        /// <summary>A medal <paramref name="size"/> tall: the ribbon in <paramref name="ribbon"/> above, the disc gold (or grey, not yet earned) below.</summary>
        public static RectTransform MedalIcon(Transform parent, string name, Color ribbon, float size, bool earned)
        {
            var holder = UIKit.Rect(parent, name);
            holder.sizeDelta = new Vector2(size, size);
            var strap = UIKit.Icon(holder, "Ribbon", ProceduralSprites.MedalRibbon, ribbon, size * 0.6f);
            UIKit.Place(strap.rectTransform, new Vector2(0.5f, 1f), Vector2.zero, new Vector2(size * 0.6f, size * 0.6f), new Vector2(0.5f, 1f));
            var shade = UIKit.Icon(holder, "DiscShade", ProceduralSprites.Medal, GoldShade, size * 0.66f);
            UIKit.Place(shade.rectTransform, new Vector2(0.5f, 0f), new Vector2(size * 0.025f, -size * 0.025f), new Vector2(size * 0.66f, size * 0.66f), new Vector2(0.5f, 0f));
            var disc = UIKit.Icon(holder, "Disc", ProceduralSprites.Medal, Gold, size * 0.66f);
            UIKit.Place(disc.rectTransform, new Vector2(0.5f, 0f), Vector2.zero, new Vector2(size * 0.66f, size * 0.66f), new Vector2(0.5f, 0f));
            TintMedal(holder, ribbon, earned);
            foreach (var g in holder.GetComponentsInChildren<Graphic>(true)) g.raycastTarget = false;
            return holder;
        }

        /// <summary>Colours a medal made by <see cref="MedalIcon"/>: its ribbon, and its disc gold once earned (grey before).</summary>
        public static void TintMedal(RectTransform medal, Color ribbon, bool earned)
        {
            var strap = medal.Find("Ribbon");
            if (strap != null) strap.GetComponent<Image>().color = ribbon;
            var disc = medal.Find("Disc");
            if (disc != null) disc.GetComponent<Image>().color = earned ? Gold : NotYet;
            var shade = medal.Find("DiscShade");
            if (shade != null) shade.GetComponent<Image>().color = earned ? GoldShade : new Color(0.6f, 0.62f, 0.68f);
        }
    }
}
