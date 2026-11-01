using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// Who walks to school: two cards, the boy and the girl, each with a portrait of the real
    /// model (rendered in the game's toon look by tools/blender/portrait_teen.py into
    /// Resources/UI) on a patch of sky and their name; the chosen one framed in orange with a
    /// tick. Picking sets GameSettings.Character, which the menu's 3D teen and every level's
    /// CharacterChoice follow live. Used in Settings and as its own small picker (title screen,
    /// Locker Room).
    /// </summary>
    public static class PlayerPicker
    {
        public static readonly string[] Ids = { "boy", "girl" };
        static readonly Sprite[] portraits = new Sprite[2];

        /// <summary>The portrait for "boy" or "girl" (Resources/UI/PlayerBoy.png, PlayerGirl.png), or null if missing.</summary>
        public static Sprite Portrait(string id)
        {
            int i = id == "girl" ? 1 : 0;
            if (portraits[i] != null) return portraits[i];
            string path = "UI/Player" + (i == 1 ? "Girl" : "Boy");
            var sprite = Resources.Load<Sprite>(path);
            if (sprite == null)
            {
                // Imported as a plain texture (no UiArtImportSettings): make the sprite here.
                var tex = Resources.Load<Texture2D>(path);
                if (tex != null) sprite = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), 100f);
            }
            portraits[i] = sprite;
            return sprite;
        }

        /// <summary>
        /// The two cards side by side, filling <paramref name="area"/> with <paramref name="gap"/>
        /// between them. They rebuild themselves when one is picked; <paramref name="onPicked"/> runs after.
        /// </summary>
        public static void Cards(RectTransform area, float gap = 28f, System.Action onPicked = null)
        {
            for (int i = area.childCount - 1; i >= 0; i--) Object.Destroy(area.GetChild(i).gameObject);
            for (int i = 0; i < Ids.Length; i++)
            {
                string id = Ids[i];
                bool chosen = GameSettings.Character == id;
                var card = UIKit.Button(area, "Card_" + id, "", chosen ? UITheme.Accent : UITheme.Paper, () =>
                {
                    if (GameSettings.Character != id) GameSettings.Character = id;
                    Cards(area, gap, onPicked);
                    if (onPicked != null) onPicked();
                });
                var rt = (RectTransform)card.transform;
                rt.anchorMin = new Vector2(i * 0.5f, 0f);
                rt.anchorMax = new Vector2(i * 0.5f + 0.5f, 1f);
                rt.offsetMin = new Vector2(i == 0 ? 0f : gap * 0.5f, UIButtonFx.Depth);
                rt.offsetMax = new Vector2(i == 0 ? -gap * 0.5f : 0f, 0f);
                var face = card.transform.Find("Face");
                var shine = face.Find("Shine");
                if (shine != null) shine.gameObject.SetActive(false);

                // A window of sky with the portrait standing in it.
                float nameHeight = Mathf.Clamp(area.rect.height * 0.2f, 56f, 84f);
                var window = UIKit.Panel(face, "Window", UITheme.SkyBottom, ProceduralSprites.RoundedEdge);
                window.rectTransform.anchorMin = Vector2.zero;
                window.rectTransform.anchorMax = Vector2.one;
                window.rectTransform.offsetMin = new Vector2(10f, nameHeight);
                window.rectTransform.offsetMax = new Vector2(-10f, -10f);
                window.raycastTarget = false;
                window.gameObject.AddComponent<RectMask2D>();
                var sky = UIKit.Icon(window.transform, "Sky", ProceduralSprites.VerticalGradient, UITheme.SkyTop, 10f);
                sky.preserveAspect = false;
                UIKit.Stretch(sky.rectTransform);
                var cloud = UIKit.Icon(window.transform, "Cloud", ProceduralSprites.SoftDisc, new Color(1f, 1f, 1f, 0.7f), 10f);
                cloud.preserveAspect = false;
                cloud.rectTransform.anchorMin = new Vector2(i == 0 ? -0.2f : 0.45f, 0.62f);
                cloud.rectTransform.anchorMax = new Vector2(i == 0 ? 0.55f : 1.2f, 0.92f);
                cloud.rectTransform.offsetMin = cloud.rectTransform.offsetMax = Vector2.zero;

                var portrait = Portrait(id);
                var image = UIKit.Icon(window.transform, "Portrait", portrait != null ? portrait : ProceduralSprites.BallIcon, Color.white, 10f);
                image.rectTransform.anchorMin = new Vector2(0f, 0f);
                image.rectTransform.anchorMax = new Vector2(1f, portrait != null ? 1f : 0.7f);
                image.rectTransform.offsetMin = new Vector2(0f, 0f);
                image.rectTransform.offsetMax = new Vector2(0f, portrait != null ? 0f : -10f);
                image.rectTransform.pivot = new Vector2(0.5f, 0f);
                if (!chosen) image.color = new Color(0.9f, 0.92f, 0.96f);

                var name = UIKit.Label(face, "Name", Loc.T("settings." + id), 40, chosen ? Color.white : UITheme.Ink, TextAnchor.MiddleCenter, true);
                name.rectTransform.anchorMin = new Vector2(0f, 0f);
                name.rectTransform.anchorMax = new Vector2(1f, 0f);
                name.rectTransform.pivot = new Vector2(0.5f, 0f);
                name.rectTransform.offsetMin = new Vector2(12f, 4f);
                name.rectTransform.offsetMax = new Vector2(-12f, nameHeight - 2f);
                UIKit.Fit(name, 26);
                if (chosen)
                {
                    var sh = name.gameObject.AddComponent<Shadow>();
                    sh.effectColor = new Color(0.3f, 0.12f, 0f, 0.45f);
                    sh.effectDistance = new Vector2(0f, -3f);

                    // The tick badge in the top corner.
                    var badge = UIKit.Icon(face, "Chosen", ProceduralSprites.CircleEdge, UITheme.Green, 60f);
                    UIKit.Place(badge.rectTransform, new Vector2(1f, 1f), new Vector2(10f, 10f), new Vector2(60f, 60f), new Vector2(0.5f, 0.5f));
                    var tick = UIKit.Icon(badge.transform, "Tick", ProceduralSprites.Check, Color.white, 40f);
                    UIKit.Place(tick.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(38f, 38f));
                }
            }
        }

        /// <summary>The picker on its own: a modal with the two cards, large, and Done.</summary>
        public static GameObject Open(Transform canvas, System.Action onClose = null)
        {
            GameObject root;
            var card = UIKit.Modal(canvas, "PlayerPicker", new Vector2(940f, 760f), out root);
            UIKit.Header(card.transform, Loc.T("player.title"), 620f);
            var area = UIKit.Rect(card.transform, "Cards");
            area.anchorMin = new Vector2(0.5f, 0f);
            area.anchorMax = new Vector2(0.5f, 1f);
            area.offsetMin = new Vector2(-360f, 190f);
            area.offsetMax = new Vector2(360f, -90f);
            Cards(area, 40f);
            var done = UIKit.Button(card.transform, "Done", Loc.T("settings.done"), UITheme.Green, () =>
            {
                Object.Destroy(root);
                if (onClose != null) onClose();
            }, 44);
            UIKit.Place((RectTransform)done.transform, new Vector2(0.5f, 0f), new Vector2(0f, 95f), new Vector2(360f, 110f));
            return root;
        }
    }
}
