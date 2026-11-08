using DribbleToSchool.Localization;
using DribbleToSchool.UI;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.Coop
{
    /// <summary>
    /// The co-op standings as a list of cards (the results at the school gate, Coop/CoopHud, and the lobby while a race runs,
    /// FrontEnd/CoopScreen): in order (CoopRules.Standings), each with its place (gold for the winner), the kid's portrait,
    /// "Name #TAG" and what became of them: their time, how far along they are, or that they were disconnected or left,
    /// listed last. A finisher who has since gone is still listed with their time ("left after finishing").
    /// </summary>
    public static class CoopStandingsView
    {
        public static void Build(RectTransform parent, CoopSession s, float rowHeight)
        {
            var standings = CoopRules.Standings(s.Players);
            float y = 0f;
            int position = 0;
            foreach (var p in standings)
            {
                bool me = p.uid == s.Uid;
                var face = UIKit.Card(parent, "P" + (p.slot + 1), me ? new Color(1f, 0.97f, 0.88f, 0.97f) : UITheme.Paper);
                var rt = (RectTransform)face.transform.parent;
                rt.anchorMin = new Vector2(0f, 1f);
                rt.anchorMax = new Vector2(1f, 1f);
                rt.pivot = new Vector2(0.5f, 1f);
                rt.offsetMin = new Vector2(0f, -y - rowHeight + 10f);
                rt.offsetMax = new Vector2(0f, -y);
                y += rowHeight;

                Color c = CoopPalette.Of(p.slot);
                if (!p.IsOut && p.status != PlayerStatus.Lobby) position++;
                string badge = p.IsOut ? "-" : p.status == PlayerStatus.Finished ? p.place.ToString() : p.status == PlayerStatus.Lobby ? (p.slot + 1).ToString() : position.ToString();
                var disc = UIKit.Icon(face.transform, "Place", ProceduralSprites.CircleEdge, p.status == PlayerStatus.Finished && p.place == 1 ? UITheme.Gold : p.IsOut ? UITheme.Locked : c, rowHeight - 26f);
                UIKit.Place(disc.rectTransform, new Vector2(0f, 0.5f), new Vector2(14f, 0f), new Vector2(rowHeight - 26f, rowHeight - 26f), new Vector2(0f, 0.5f));
                var num = UIKit.Label(disc.transform, "N", badge, (int)(rowHeight * 0.38f), Color.white, TextAnchor.MiddleCenter, true);
                UIKit.Stretch(num.rectTransform);

                float x = 14f + rowHeight - 26f + 12f;
                var portrait = PlayerPicker.Portrait(CoopProfile.CharacterId(p.character));
                if (portrait != null)
                {
                    var frame = UIKit.Icon(face.transform, "Kid", ProceduralSprites.CircleEdge, new Color(c.r, c.g, c.b, 0.35f), rowHeight - 22f);
                    UIKit.Place(frame.rectTransform, new Vector2(0f, 0.5f), new Vector2(x, 0f), new Vector2(rowHeight - 22f, rowHeight - 22f), new Vector2(0f, 0.5f));
                    var mask = UIKit.Rect(frame.transform, "Mask");
                    UIKit.Stretch(mask, 4f);
                    mask.gameObject.AddComponent<RectMask2D>();
                    var img = UIKit.Icon(mask, "Portrait", portrait, Color.white, rowHeight);
                    img.rectTransform.anchorMin = Vector2.zero;
                    img.rectTransform.anchorMax = Vector2.one;
                    img.rectTransform.offsetMin = new Vector2(-4f, -8f);
                    img.rectTransform.offsetMax = new Vector2(4f, 4f);
                    x += rowHeight - 22f + 14f;
                }

                var name = UIKit.Label(face.transform, "Name", Name(p, me), (int)(rowHeight * 0.36f), UITheme.Ink, TextAnchor.MiddleLeft, true);
                name.supportRichText = true;
                name.rectTransform.anchorMin = new Vector2(0f, 0f);
                name.rectTransform.anchorMax = new Vector2(0.62f, 1f);
                name.rectTransform.offsetMin = new Vector2(x, 6f);
                name.rectTransform.offsetMax = new Vector2(0f, -6f);
                UIKit.Fit(name, 18);

                var state = UIKit.Label(face.transform, "State", StateOf(p, s), (int)(rowHeight * 0.32f), p.IsOut ? UITheme.Red : p.status == PlayerStatus.Finished ? UITheme.Navy : UITheme.InkSoft, TextAnchor.MiddleRight, true);
                state.rectTransform.anchorMin = new Vector2(0.58f, 0f);
                state.rectTransform.anchorMax = new Vector2(1f, 1f);
                state.rectTransform.offsetMin = new Vector2(0f, 6f);
                state.rectTransform.offsetMax = new Vector2(-22f, -6f);
                UIKit.Fit(state, 16);
                foreach (var g in rt.GetComponentsInChildren<Graphic>()) g.raycastTarget = false;
            }
            parent.sizeDelta = new Vector2(parent.sizeDelta.x, Mathf.Max(parent.sizeDelta.y, y));
        }

        static string Name(CoopPlayer p, bool me)
        {
            string text = CoopProfile.DisplayName(p) + " <color=#1c213380><size=" + 22 + ">#" + p.tag + "</size></color>";
            if (p.isHost) text += "  <color=#2a4fa0><size=20>" + Loc.T("coop.host") + "</size></color>";
            if (me) text += "  <color=#e0731c><size=20>" + Loc.T("coop.you") + "</size></color>";
            return text;
        }

        public static string StateOf(CoopPlayer p, CoopSession s)
        {
            switch (p.status)
            {
                case PlayerStatus.Finished:
                    string time = CoopRules.FormatTime(p.finishMs, true);
                    return p.connected ? time : Loc.F("coop.standing.finishedGone", time);
                case PlayerStatus.Disconnected: return Loc.T("coop.standing.out");
                case PlayerStatus.Left: return Loc.T("coop.standing.left");
                case PlayerStatus.Racing:
                    if (!p.connected) return Loc.T("coop.standing.lost");
                    return Loc.F("coop.standing.racing", Mathf.RoundToInt(p.progress * 100f));
                default:
                    if (!p.connected) return Loc.T("coop.standing.lost");
                    return p.ready ? Loc.T("coop.ready") : Loc.T("coop.notReady");
            }
        }
    }
}
