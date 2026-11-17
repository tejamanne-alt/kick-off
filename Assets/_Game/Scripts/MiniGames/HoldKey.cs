using DribbleToSchool.Core;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace DribbleToSchool.MiniGames
{
    /// <summary>A key in a mini-game's layer: held while a finger is on it, and a tap when it goes down.</summary>
    public class HoldKey : MonoBehaviour, IPointerDownHandler, IPointerUpHandler, IPointerExitHandler
    {
        public Image face;
        public Color colour = Color.white;
        public bool Held { get; private set; }
        public event System.Action Tapped;

        public void OnPointerDown(PointerEventData e)
        {
            Held = true;
            if (face != null) face.color = Color.Lerp(colour, Color.white, 0.35f);
            if (Tapped != null) Tapped();
        }

        public void OnPointerUp(PointerEventData e) { Release(); }
        public void OnPointerExit(PointerEventData e) { Release(); }

        void Release()
        {
            Held = false;
            if (face != null) face.color = colour;
        }

        void OnDisable() { Release(); }
    }
}
