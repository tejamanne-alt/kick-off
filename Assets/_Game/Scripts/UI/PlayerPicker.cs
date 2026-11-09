using System.Collections.Generic;
using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// Who walks to school: a card for every kid of the <see cref="PlayerRoster"/>, in a row for
    /// each school (the high-school teens, the primary-school kids), each with a portrait of the real
    /// model (rendered in the game's toon look by tools/blender into Resources/UI) on a patch of
    /// sky and their name; the chosen one framed in orange with a tick. Picking sets
    /// GameSettings.Character, which the menu's 3D kid and every level's CharacterChoice follow
    /// live. Opened as its own modal from the title screen, the Locker Room and Settings.
    /// </summary>
    public static class PlayerPicker
    {
        const float HeadingHeight = 46f;
        const float NameHeight = 64f;
        static readonly Dictionary<string, Sprite> portraits = new Dictionary<string, Sprite>();

        /// <summary>The portrait of the kid called <paramref name="id"/> (Resources/UI/Player&lt;model&gt;.png), or null if missing.</summary>
        public static Sprite Portrait(string id)
        {
            var info = PlayerRoster.Get(id);
            Sprite sprite;
            if (portraits.TryGetValue(info.id, out sprite) && sprite != null) return sprite;
            sprite = Resources.Load<Sprite>(info.PortraitPath);
            if (sprite == null)
            {
                // Imported as a plain texture (no UiArtImportSettings): make the sprite here.
                var tex = Resources.Load<Texture2D>(info.PortraitPath);
                if (tex != null) sprite = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), 100f);
            }
            portraits[info.id] = sprite;
            return sprite;
        }

        /// <summary>
        /// A window of sky with the kid's portrait standing in it, filling its parent (the caller
        /// insets it). <paramref name="variant"/> moves the cloud so neighbours differ.
        /// </summary>
        static RectTransform SkyWindow(Transform parent, PlayerInfo info, bool chosen, int variant)
        {
            var window = UIKit.Panel(parent, "Window", UITheme.SkyBottom, ProceduralSprites.RoundedEdge);
            window.rectTransform.anchorMin = Vector2.zero;
            window.rectTransform.anchorMax = Vector2.one;
            window.raycastTarget = false;
            window.gameObject.AddComponent<RectMask2D>();
            var sky = UIKit.Icon(window.transform, "Sky", ProceduralSprites.VerticalGradient, UITheme.SkyTop, 10f);
            sky.preserveAspect = false;
            UIKit.Stretch(sky.rectTransform);
            bool left = variant % 2 == 0;
            var cloud = UIKit.Icon(window.transform, "Cloud", ProceduralSprites.SoftDisc, new Color(1f, 1f, 1f, 0.7f), 10f);
            cloud.preserveAspect = false;
            cloud.rectTransform.anchorMin = new Vector2(left ? -0.2f : 0.45f, 0.62f);
            cloud.rectTransform.anchorMax = new Vector2(left ? 0.55f : 1.2f, 0.92f);
            cloud.rectTransform.offsetMin = cloud.rectTransform.offsetMax = Vector2.zero;

            var portrait = Portrait(info.id);
            var image = CartoonPicture.On(UIKit.Icon(window.transform, "Portrait", portrait != null ? portrait : ProceduralSprites.BallIcon, Color.white, 10f));
            image.rectTransform.anchorMin = new Vector2(0f, 0f);
            image.rectTransform.anchorMax = new Vector2(1f, portrait != null ? 1f : 0.7f);
            image.rectTransform.offsetMin = new Vector2(0f, 0f);
            image.rectTransform.offsetMax = new Vector2(0f, portrait != null ? 0f : -10f);
            image.rectTransform.pivot = new Vector2(0.5f, 0f);
            if (!chosen) image.color = new Color(0.9f, 0.92f, 0.96f);
            return window.rectTransform;
        }

        /// <summary>One kid's card in <paramref name="cards"/>, between two horizontal fractions of it.</summary>
        static void Card(RectTransform cards, PlayerInfo info, float from, float to, float gap, int variant, System.Action<PlayerInfo> picked)
        {
            bool chosen = GameSettings.Character == info.id;
            var card = UIKit.Button(cards, "Card_" + info.id, "", chosen ? UITheme.Accent : UITheme.Paper, () => picked(info));
            var rt = (RectTransform)card.transform;
            rt.anchorMin = new Vector2(from, 0f);
            rt.anchorMax = new Vector2(to, 1f);
            rt.offsetMin = new Vector2(gap * 0.5f, UIButtonFx.Depth);
            rt.offsetMax = new Vector2(-gap * 0.5f, 0f);
            var face = card.transform.Find("Face");
            var shine = face.Find("Shine");
            if (shine != null) shine.gameObject.SetActive(false);

            var window = SkyWindow(face, info, chosen, variant);
            window.offsetMin = new Vector2(10f, NameHeight);
            window.offsetMax = new Vector2(-10f, -10f);

            var name = UIKit.Label(face, "Name", Loc.T(info.nameKey), 40, chosen ? Color.white : UITheme.Ink, TextAnchor.MiddleCenter, true);
            name.rectTransform.anchorMin = new Vector2(0f, 0f);
            name.rectTransform.anchorMax = new Vector2(1f, 0f);
            name.rectTransform.pivot = new Vector2(0.5f, 0f);
            name.rectTransform.offsetMin = new Vector2(12f, 4f);
            name.rectTransform.offsetMax = new Vector2(-12f, NameHeight - 2f);
            UIKit.Fit(name, 26);
            if (!chosen) return;

            var sh = name.gameObject.AddComponent<Shadow>();
            sh.effectColor = new Color(0.3f, 0.12f, 0f, 0.45f);
            sh.effectDistance = new Vector2(0f, -3f);

            // The tick badge in the top corner.
            var badge = UIKit.Icon(face, "Chosen", ProceduralSprites.CircleEdge, UITheme.Green, 60f);
            UIKit.Place(badge.rectTransform, new Vector2(1f, 1f), new Vector2(10f, 10f), new Vector2(60f, 60f), new Vector2(0.5f, 0.5f));
            var tick = UIKit.Icon(badge.transform, "Tick", ProceduralSprites.Check, Color.white, 40f);
            UIKit.Place(tick.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(38f, 38f));
        }

        /// <summary>
        /// Every kid's card filling <paramref name="area"/>: one band for each school with its
        /// heading above a row of cards (a shorter row sits in the middle), <paramref name="gap"/>
        /// between cards. The cards rebuild themselves when one is picked; <paramref name="onPicked"/> runs after.
        /// </summary>
        public static void Cards(RectTransform area, float gap = 24f, System.Action onPicked = null)
        {
            for (int i = area.childCount - 1; i >= 0; i--) Object.Destroy(area.GetChild(i).gameObject);
            var schools = new List<SchoolLevel>();
            int columns = 1;
            foreach (var school in new[] { SchoolLevel.High, SchoolLevel.Primary })
            {
                int count = PlayerRoster.Of(school).Count;
                if (count == 0) continue;
                schools.Add(school);
                columns = Mathf.Max(columns, count);
            }

            System.Action<PlayerInfo> picked = info =>
            {
                if (GameSettings.Character != info.id) GameSettings.Character = info.id;
                Cards(area, gap, onPicked);
                if (onPicked != null) onPicked();
            };

            int variant = 0;
            for (int row = 0; row < schools.Count; row++)
            {
                var kids = PlayerRoster.Of(schools[row]);
                var band = UIKit.Rect(area, "School_" + schools[row]);
                band.anchorMin = new Vector2(0f, 1f - (row + 1f) / schools.Count);
                band.anchorMax = new Vector2(1f, 1f - row / (float)schools.Count);
                band.offsetMin = band.offsetMax = Vector2.zero;
                var heading = UIKit.Row(band, "Heading", 0f, HeadingHeight);
                UIKit.SectionLabel(heading, Loc.T(schools[row] == SchoolLevel.High ? "player.high" : "player.primary"));

                var cards = UIKit.Rect(band, "Cards");
                UIKit.Stretch(cards);
                cards.offsetMax = new Vector2(0f, -(HeadingHeight + 4f));
                float first = (columns - kids.Count) * 0.5f;
                for (int i = 0; i < kids.Count; i++)
                    Card(cards, kids[i], (first + i) / columns, (first + i + 1) / columns, gap, variant++, picked);
            }
        }

        /// <summary>The picker on its own: a modal with every kid's card, and Done. <paramref name="onClose"/> runs after it closes.</summary>
        public static GameObject Open(Transform canvas, System.Action onClose = null)
        {
            GameObject root;
            var card = UIKit.Modal(canvas, "PlayerPicker", new Vector2(1340f, 940f), out root);
            UIKit.Header(card.transform, Loc.T("player.title"), 620f);
            var area = UIKit.Rect(card.transform, "Cards");
            area.anchorMin = Vector2.zero;
            area.anchorMax = Vector2.one;
            area.offsetMin = new Vector2(50f, 200f);
            area.offsetMax = new Vector2(-50f, -84f);
            Cards(area);
            var done = UIKit.Button(card.transform, "Done", Loc.T("settings.done"), UITheme.Green, () =>
            {
                Object.Destroy(root);
                if (onClose != null) onClose();
            }, 44);
            UIKit.Place((RectTransform)done.transform, new Vector2(0.5f, 0f), new Vector2(0f, 70f), new Vector2(360f, 110f));
            return root;
        }

        /// <summary>
        /// Settings' player row: a card with the chosen kid's portrait and name, which opens the
        /// picker; it follows the pick when the picker closes.
        /// </summary>
        public static void Summary(RectTransform row, Transform canvas)
        {
            Image portrait = null;
            Text name = null;
            System.Action refresh = () =>
            {
                if (name == null || portrait == null) return;   // Settings was rebuilt meanwhile
                var info = PlayerRoster.Get(GameSettings.Character);
                name.text = Loc.T(info.nameKey);
                var sprite = Portrait(info.id);
                portrait.sprite = sprite != null ? sprite : ProceduralSprites.BallIcon;
            };

            var button = UIKit.Button(row, "Player", "", UITheme.Paper, () => Open(canvas, refresh));
            var rt = (RectTransform)button.transform;
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = new Vector2(0f, UIButtonFx.Depth);
            rt.offsetMax = Vector2.zero;
            var face = button.transform.Find("Face");
            var shine = face.Find("Shine");
            if (shine != null) shine.gameObject.SetActive(false);

            var info0 = PlayerRoster.Get(GameSettings.Character);
            var window = SkyWindow(face, info0, true, 0);
            window.anchorMin = new Vector2(0f, 0f);
            window.anchorMax = new Vector2(0f, 1f);
            window.pivot = new Vector2(0f, 0.5f);
            window.anchoredPosition = new Vector2(12f, 0f);
            window.sizeDelta = new Vector2(190f, -24f);
            portrait = window.Find("Portrait").GetComponent<Image>();

            name = UIKit.Label(face, "Name", "", 46, UITheme.Ink, TextAnchor.LowerLeft, true);
            name.rectTransform.anchorMin = new Vector2(0f, 0.5f);
            name.rectTransform.anchorMax = new Vector2(1f, 1f);
            name.rectTransform.offsetMin = new Vector2(224f, 0f);
            name.rectTransform.offsetMax = new Vector2(-16f, -14f);
            UIKit.Fit(name, 28);

            var hint = UIKit.Label(face, "Hint", Loc.T("player.change") + "  >", 28, UITheme.Accent, TextAnchor.UpperLeft, true);
            hint.rectTransform.anchorMin = new Vector2(0f, 0f);
            hint.rectTransform.anchorMax = new Vector2(1f, 0.5f);
            hint.rectTransform.offsetMin = new Vector2(224f, 14f);
            hint.rectTransform.offsetMax = new Vector2(-16f, -6f);
            UIKit.Fit(hint, 20);
            refresh();
        }
    }
}
