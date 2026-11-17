using DribbleToSchool.Core;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace DribbleToSchool.MiniGames
{
    /// <summary>
    /// What every mini-game shares (docs/CITIES.md, "The mini-games"): a full-screen layer over the level, built in code like
    /// the HUD (UIKit), that holds the run while it plays (LevelManager.Hold: the kid stands, the clock waits) and runs on
    /// unscaled time; its pictures are the user's set pictures in Resources/UI/Kamakura. When it closes it lets the run go on
    /// and says whether it was done.
    /// </summary>
    public abstract class MiniGameOverlay : MonoBehaviour
    {
        /// <summary>The set pictures' Resources folder.</summary>
        public const string Pictures = "UI/Kamakura/";

        protected LevelManager level;
        protected RectTransform root;
        Canvas canvas;
        bool holding;

        /// <summary>Called once when the mini-game closes: true when it was done.</summary>
        public System.Action<bool> Finished;

        protected float Dt { get { return Mathf.Min(Time.unscaledDeltaTime, 0.05f); } }

        /// <summary>Open the layer and hold the run.</summary>
        protected void Open(string name)
        {
            level = LevelManager.Current;
            canvas = UIKit.CreateCanvas(name, 40);
            root = UIKit.Stretch(UIKit.Rect(canvas.transform, "Root"));
            if (level != null)
            {
                level.Hold(true);
                holding = true;
            }
        }

        /// <summary>Close the layer, let the run go on, and say how it went.</summary>
        protected void Close(bool done)
        {
            if (holding && level != null) level.Hold(false);
            holding = false;
            if (canvas != null) Destroy(canvas.gameObject);
            canvas = null;
            var finished = Finished;
            Finished = null;
            Destroy(this);
            if (finished != null) finished(done);
        }

        protected virtual void OnDestroy()
        {
            if (holding && level != null) level.Hold(false);
            holding = false;
            if (canvas != null) Destroy(canvas.gameObject);
        }

        /// <summary>One of the set pictures (Resources/UI/Kamakura/&lt;name&gt;), or null.</summary>
        protected static Texture2D Picture(string name)
        {
            return Resources.Load<Texture2D>(Pictures + name);
        }

        /// <summary>A picture laid in the layer: its rect, at <paramref name="position"/> from the screen's middle.</summary>
        protected RawImage Picture(Transform parent, string name, Texture2D texture, Vector2 position, Vector2 size, Rect uv)
        {
            var rt = UIKit.Rect(parent, name);
            UIKit.Place(rt, new Vector2(0.5f, 0.5f), position, size);
            var image = rt.gameObject.AddComponent<RawImage>();
            image.texture = texture;
            image.uvRect = uv;
            image.raycastTarget = false;
            if (texture == null) image.color = new Color(0.2f, 0.24f, 0.3f);
            return image;
        }

        /// <summary>Text in the layer, outlined so it reads on any picture.</summary>
        protected Text Words(Transform parent, string name, string text, int size, Vector2 position, Vector2 box, Color colour)
        {
            var t = UIKit.Label(parent, name, text, size, colour, TextAnchor.MiddleCenter, true);
            UIKit.Place(t.rectTransform, new Vector2(0.5f, 0.5f), position, box);
            var outline = t.gameObject.AddComponent<Outline>();
            outline.effectColor = new Color(0.05f, 0.07f, 0.16f, 0.85f);
            outline.effectDistance = new Vector2(3f, -3f);
            return t;
        }

        /// <summary>A round key in the layer that is pressed while a finger is on it (<see cref="HoldKey.Held"/>), and taps.</summary>
        protected HoldKey Key(Transform parent, string name, string label, Color colour, Vector2 position, float size)
        {
            var rt = UIKit.Rect(parent, name);
            UIKit.Place(rt, new Vector2(0.5f, 0.5f), position, new Vector2(size, size));
            var disc = rt.gameObject.AddComponent<Image>();
            disc.sprite = ProceduralSprites.Circle;
            disc.color = colour;
            var key = rt.gameObject.AddComponent<HoldKey>();
            key.face = disc;
            key.colour = colour;
            var t = UIKit.Label(rt, "Label", label, Mathf.RoundToInt(size * 0.24f), Color.white, TextAnchor.MiddleCenter, true);
            UIKit.Stretch(t.rectTransform);
            return key;
        }
    }
}
