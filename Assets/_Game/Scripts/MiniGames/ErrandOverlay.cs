using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.Player;
using DribbleToSchool.Progression;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.MiniGames
{
    /// <summary>
    /// The errand itself, drawn from the user's set pictures: Grandma's counter with the bento on its cloth (KM2-3a) and the
    /// furoshiki at each stage of its wrapping (KM2-3b: flat, the near corner over, the far corner over, the sides crossed,
    /// tied). Grandma shows the order of the four corners; the kid taps them in that order (a wrong one and she shows it
    /// again); then two pulls of the knot, each tapped while the marker is in the gold.
    /// </summary>
    public class ErrandOverlay : MiniGameOverlay
    {
        enum Phase { Showing, Folding, Knot, Done }

        Phase phase;
        float phaseTime;
        ErrandRules.Corner[] order;
        int step, wrong, missed, pulls;
        float messageUntil;

        RawImage cloth;
        Text message, coinsText;
        readonly HoldKey[] corners = new HoldKey[4];
        RectTransform knotBar, knotMarker;
        HoldKey pullKey;

        const float ClothSize = 560f;
        static readonly Vector2 ClothAt = new Vector2(0f, -40f);
        // the corners' keys about the cloth: near (bottom), far (top), left, right
        static readonly Vector2[] CornerAt = { new Vector2(0f, -330f), new Vector2(0f, 250f), new Vector2(-330f, -40f), new Vector2(330f, -40f) };
        static readonly string[] CornerKey = { "mini.errand.near", "mini.errand.far", "mini.errand.left", "mini.errand.right" };

        void Start()
        {
            Open("Errand");
            order = ErrandRules.Order(System.Environment.TickCount & 0x7fff);
            var counter = Picture("errand_counter");
            var shade = UIKit.Panel(root, "Shade", new Color(0.08f, 0.07f, 0.06f));
            UIKit.Stretch(shade.rectTransform, -400f);
            var back = Picture(root, "Counter", counter, Vector2.zero, new Vector2(2160f, 1080f), new Rect(0f, 0f, 1f, 1f));
            back.color = new Color(0.55f, 0.55f, 0.55f);             // dimmed: the cloth is what to look at
            var folds = Picture("errand_folds");
            cloth = Picture(root, "Cloth", folds, ClothAt, new Vector2(ClothSize, ClothSize), Stage(0));
            for (int i = 0; i < 4; i++)
            {
                int c = i;
                corners[i] = Key(root, "Corner" + i, Loc.T(CornerKey[i]), new Color(0.75f, 0.2f, 0.16f), CornerAt[i], 150f);
                corners[i].Tapped += () => Fold((ErrandRules.Corner)c);
            }
            message = Words(root, "Message", "", 44, new Vector2(0f, 430f), new Vector2(1300f, 70f), Color.white);
            coinsText = Words(root, "Coins", "", 34, Vector2.zero, new Vector2(240f, 50f), UITheme.Gold);
            UIKit.Place(coinsText.rectTransform, new Vector2(1f, 1f), new Vector2(-150f, -70f), new Vector2(240f, 50f), new Vector2(0.5f, 0.5f));

            // the knot: a bar with its gold middle and a marker sweeping across it, and the key to pull
            knotBar = UIKit.Panel(root, "KnotBar", new Color(1f, 1f, 1f, 0.25f)).rectTransform;
            UIKit.Place(knotBar, new Vector2(0.5f, 0.5f), new Vector2(0f, -330f), new Vector2(700f, 34f));
            var gold = UIKit.Panel(knotBar, "Gold", new Color(1f, 0.8f, 0.2f, 0.85f));
            UIKit.Place(gold.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero,
                new Vector2(700f * (ErrandRules.KnotTo - ErrandRules.KnotFrom), 34f));
            knotMarker = UIKit.Panel(knotBar, "Marker", Color.white).rectTransform;
            UIKit.Place(knotMarker, new Vector2(0f, 0.5f), Vector2.zero, new Vector2(14f, 64f));
            pullKey = Key(root, "Pull", Loc.T("mini.errand.pull"), UITheme.Accent, new Vector2(1f, 0.5f), new Vector2(-170f, -330f), 190f);
            pullKey.Tapped += Pull;
            knotBar.gameObject.SetActive(false);
            pullKey.gameObject.SetActive(false);

            Show();
        }

        /// <summary>The part of the folds picture (five square stages side by side) for stage <paramref name="k"/> (0 flat to 4 tied).</summary>
        static Rect Stage(int k)
        {
            return new Rect(Mathf.Clamp(k, 0, 4) * 0.2f, 0f, 0.2f, 1f);
        }

        void Show()
        {
            phase = Phase.Showing;
            phaseTime = 0f;
            step = 0;
            cloth.uvRect = Stage(0);
            Say(Loc.T("mini.errand.watch"), 99f);
            foreach (var c in corners) c.enabled = false;
        }

        void Update()
        {
            float dt = Dt;
            phaseTime += dt;
            if (Time.unscaledTime > messageUntil) message.text = "";
            coinsText.text = ErrandRules.Pay(wrong, missed) + " / " + ErrandRules.PossibleCoins;
            switch (phase)
            {
                case Phase.Showing:
                {
                    // each corner of the order lights for 0.7 s, in turn, after a short pause
                    int k = Mathf.FloorToInt((phaseTime - 0.6f) / 0.75f);
                    for (int i = 0; i < 4; i++)
                        corners[i].face.color = k >= 0 && k < 4 && (int)order[k] == i && Mathf.Repeat(phaseTime - 0.6f, 0.75f) < 0.6f
                            ? UITheme.Gold : new Color(0.75f, 0.2f, 0.16f);
                    if (k >= 4)
                    {
                        phase = Phase.Folding;
                        phaseTime = 0f;
                        foreach (var c in corners)
                        {
                            c.enabled = true;
                            c.face.color = c.colour;
                        }
                        Say(Loc.T("mini.errand.yourTurn"), 99f);
                    }
                    break;
                }
                case Phase.Knot:
                {
                    float m = ErrandRules.KnotMarker(phaseTime);
                    knotMarker.anchoredPosition = new Vector2(m * 700f, 0f);
                    break;
                }
                case Phase.Done:
                    if (phaseTime > 2.2f) Finish();
                    break;
            }
        }

        void Fold(ErrandRules.Corner corner)
        {
            if (phase != Phase.Folding) return;
            if (ErrandRules.FoldIsRight(order, step, corner))
            {
                step++;
                corners[(int)corner].gameObject.SetActive(false);
                cloth.uvRect = Stage(Mathf.Min(step, 3));
                if (step >= 4)
                {
                    phase = Phase.Knot;
                    phaseTime = 0f;
                    knotBar.gameObject.SetActive(true);
                    pullKey.gameObject.SetActive(true);
                    Say(Loc.T("mini.errand.knot"), 99f);
                }
                return;
            }
            wrong++;
            Say(Loc.T("mini.errand.again"), 1.6f);
            foreach (var c in corners) c.gameObject.SetActive(true);
            Show();
        }

        void Pull()
        {
            if (phase != Phase.Knot) return;
            if (ErrandRules.PullIsGood(ErrandRules.KnotMarker(phaseTime)))
            {
                pulls++;
                Say(Loc.T(pulls >= ErrandRules.KnotPulls ? "mini.errand.done" : "mini.errand.tighter"), 2.4f);
                if (pulls >= ErrandRules.KnotPulls)
                {
                    cloth.uvRect = Stage(4);
                    knotBar.gameObject.SetActive(false);
                    pullKey.gameObject.SetActive(false);
                    phase = Phase.Done;
                    phaseTime = 0f;
                }
            }
            else
            {
                missed++;
                Say(Loc.T("mini.errand.loose"), 1.2f);
            }
        }

        void Finish()
        {
            if (level != null) level.CollectBonus(ErrandRules.Pay(wrong, missed), ErrandRules.PossibleCoins);
            Close(true);
        }

        void Say(string text, float seconds)
        {
            message.text = text;
            messageUntil = Time.unscaledTime + seconds;
        }
    }
}
