using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// One sticker on screen: the die-cut art over a crisp shadow, its name lettered on the art's
    /// ribbon in the player's language, and for holo and gold stickers a band of light sweeping
    /// across it (masked to the sticker's shape). A sticker not found yet shows as a pale
    /// silhouette of its shape with a question mark.
    /// </summary>
    public static class StickerView
    {
        static readonly Color Silhouette = new Color(0.7f, 0.74f, 0.84f);

        /// <summary>Builds the sticker <paramref name="size"/> pixels square under <paramref name="parent"/> (place the returned rect).</summary>
        public static RectTransform Build(Transform parent, string levelId, Color chapterColor, bool found, float size, bool letterName = true, float sheenOffset = 0f)
        {
            var root = UIKit.Rect(parent, "Sticker_" + levelId);
            root.sizeDelta = new Vector2(size, size);
            var sprite = StickerBook.Art(levelId, chapterColor);

            var shadow = UIKit.Icon(root, "Shadow", sprite, new Color(0.04f, 0.07f, 0.2f, found ? 0.26f : 0.12f), size);
            UIKit.Stretch(shadow.rectTransform);
            shadow.rectTransform.offsetMin += new Vector2(size * 0.012f, -size * 0.022f);
            shadow.rectTransform.offsetMax += new Vector2(size * 0.012f, -size * 0.022f);

            var face = UIKit.Icon(root, "Face", sprite, found ? Color.white : Silhouette, size);
            UIKit.Stretch(face.rectTransform);
            if (found) CartoonPicture.On(face);   // (an unfound sticker's silhouette stays plain)

            if (!found)
            {
                var mark = UIKit.Title(face.transform, "Unknown", "?", Mathf.RoundToInt(size * 0.36f), Color.white);
                UIKit.Stretch(mark.rectTransform);
                mark.rectTransform.offsetMin = new Vector2(0f, size * 0.12f);
                return root;
            }

            if (letterName && StickerBook.HasArt(levelId))
            {
                var name = UIKit.Label(face.transform, "Name", StickerBook.Name(levelId), Mathf.RoundToInt(size * 0.075f), Color.white, TextAnchor.MiddleCenter, true);
                Rect r = StickerBook.RibbonRect;
                name.rectTransform.anchorMin = new Vector2(r.xMin, r.yMin);
                name.rectTransform.anchorMax = new Vector2(r.xMax, r.yMax);
                name.rectTransform.offsetMin = new Vector2(0f, size * 0.004f);
                name.rectTransform.offsetMax = Vector2.zero;
                UIKit.Fit(name, Mathf.Max(10, Mathf.RoundToInt(size * 0.045f)));
                name.horizontalOverflow = HorizontalWrapMode.Wrap;
                var sh = name.gameObject.AddComponent<Shadow>();
                sh.effectColor = new Color(0f, 0f, 0.1f, 0.5f);
                sh.effectDistance = new Vector2(0f, -Mathf.Max(1f, size * 0.006f));
            }

            var rarity = StickerBook.Rarity(levelId);
            if (rarity != StickerRarity.Normal)
            {
                // The sheen only shows inside the sticker's own shape.
                var mask = face.gameObject.AddComponent<Mask>();
                mask.showMaskGraphic = true;
                var band = UIKit.Icon(face.transform, "Sheen", rarity == StickerRarity.Holo ? ProceduralSprites.HoloSheen : ProceduralSprites.GoldSheen, Color.white, size);
                band.preserveAspect = false;
                var rt = band.rectTransform;
                rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 0.5f);
                rt.sizeDelta = new Vector2(size * 0.55f, size * 1.8f);
                rt.localRotation = Quaternion.Euler(0f, 0f, -28f);
                var sheen = band.gameObject.AddComponent<UISheen>();
                sheen.offset = sheenOffset;
                sheen.period = rarity == StickerRarity.Gold ? 3.4f : 2.6f;
                band.transform.SetAsLastSibling();
            }
            return root;
        }
    }
}
