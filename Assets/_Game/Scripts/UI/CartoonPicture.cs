using System.Collections.Generic;
using DribbleToSchool.Progression;
using DribbleToSchool.World;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// A picture in the menus (a kid's card, a bag, a sticker, the logo, the town map) drawn in the classic cartoon
    /// filter's look while it is chosen (Resources/Shaders/CartoonPicture, the same colour as the camera's pass:
    /// World/ClassicLook), and as itself otherwise. It follows the filter at once (AddOns.FilterChanged): choosing it in
    /// Add-ons &amp; Filters turns the pictures already on screen. Text is never filtered: only these pictures are.
    /// A cel (a kid, a bag, a sticker) is outlined outside its shape; the logo keeps its own outline; the town map is
    /// painted like the scenery.
    /// </summary>
    [DisallowMultipleComponent]
    public class CartoonPicture : MonoBehaviour
    {
        /// <summary>How a picture is drawn by the filter.</summary>
        public enum Kind { Cel, CelNoOutline, Painted }

        public Kind kind;
        Graphic graphic;

        static Shader shader;
        static readonly Dictionary<Kind, Material> materials = new Dictionary<Kind, Material>();
        static readonly int PaintedId = Shader.PropertyToID("_Painted");
        static readonly int OutlineId = Shader.PropertyToID("_OutlineTexels");

        /// <summary>Draw <paramref name="graphic"/> (an Image or a RawImage) in the filter's look while it is chosen; returns it.</summary>
        public static T On<T>(T graphic, Kind kind = Kind.Cel) where T : Graphic
        {
            if (graphic == null) return null;
            var picture = graphic.GetComponent<CartoonPicture>();
            if (picture == null) picture = graphic.gameObject.AddComponent<CartoonPicture>();
            picture.kind = kind;
            picture.Refresh();
            return graphic;
        }

        void OnEnable()
        {
            AddOns.FilterChanged += Refresh;
            Refresh();
        }

        void OnDisable()
        {
            AddOns.FilterChanged -= Refresh;
        }

        void Refresh()
        {
            if (graphic == null) graphic = GetComponent<Graphic>();
            if (graphic == null) return;
            var wanted = AddOns.ClassicOn ? MaterialFor(kind) : null;
            // (null: the graphic's own default UI material)
            if (graphic.material != (wanted != null ? wanted : graphic.defaultMaterial)) graphic.material = wanted;
        }

        /// <summary>The shared material for a kind of picture (null where the shader can't run: the picture stays as it is).</summary>
        static Material MaterialFor(Kind kind)
        {
            if (shader == null) shader = Resources.Load<Shader>("Shaders/CartoonPicture");
            if (shader == null || !shader.isSupported) return null;
            Material m;
            if (!materials.TryGetValue(kind, out m) || m == null)
            {
                m = new Material(shader) { name = "CartoonPicture" + kind, hideFlags = HideFlags.HideAndDontSave };
                m.SetFloat(PaintedId, kind == Kind.Painted ? 1f : 0f);
                m.SetFloat(OutlineId, kind == Kind.Cel ? 3f : 0f);
                materials[kind] = m;
            }
            ClassicLook.Active.Apply(m);   // (the classic or the calmer setting)
            return m;
        }
    }
}
