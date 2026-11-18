using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.Challenges
{
    /// <summary>
    /// M1, the ride (docs/CITIES.md), as Miami's Metrobus (FL1-2): board, ride, get off at your stop.
    /// 1. **Board.** The bus pulls in. Walk to the card reader by the door and tap CARD when it shows green, then get on with the
    ///    ball before the doors close. Too slow, and the bus goes without you: the next one comes along a few seconds later.
    /// 2. **Ride.** The bus pulls away, sways and brakes hard at the lights. Keep the ball at your feet: push the stick against the
    ///    sway (the balance bar shows how far the ball has rolled from you) and hold KICK through a hard brake (it keeps the ball
    ///    at your feet: the sway doesn't move a held ball).
    /// 3. **Get off.** The sign over the aisle names the next stop. Tap STOP while it says yours (Brickell Avenue), and walk off
    ///    with the ball when the doors open. Miss it and you get off at the one after: the walk back is added to your time.
    /// Stars: off the bus with the ball; at your own stop; and the ball never rolled away from you in the sway.
    /// The bus stands still and the street outside slides past its windows; the sway is pushed onto the ball and the kid. It pulls in
    /// from the road and out into it (<see cref="pullOutZ"/>), so it never drives through the kid at the stop, and its near side
    /// (<see cref="nearSide"/>) is taken away as the kid comes to the door, so the inside shows (nothing tall between the camera and
    /// the kid: docs/LEARNINGS.md E10).
    /// </summary>
    public class BusRide : MiniGameObjective
    {
        [Header("The bus (built by Editor/LevelBuildKit.FloridaCity)")]
        public Transform busBody;
        [Tooltip("How far right of its place the bus is when it pulls in or drives off.")]
        public float driveOffset = 30f;
        [Tooltip("The bus's floor and walls: there only while the bus is at the stop or riding.")]
        public Collider2D[] busColliders;
        [Tooltip("Shut while the bus rides: the doorway.")]
        public Collider2D door;
        public float doorX = 4.6f, readerX = 3.8f;
        [Tooltip("Which way from the doorway the inside is: +1 the bus stands right of its door (it pulls in from the right), -1 left.")]
        public float inward = 1f;
        [Tooltip("The bus's near side (its windows and doors toward the camera): hidden while the kid is at the door or aboard.")]
        public GameObject nearSide;
        [Tooltip("How far toward the camera the bus is out in the road as it pulls in and out (0: along the kerb).")]
        public float pullOutZ;
        public Renderer readerLight;
        [Tooltip("The street seen through the windows, slid left as the bus drives (wrapping every stripLength metres).")]
        public Transform street;
        public float stripLength = 60f;
        [Tooltip("The stops along the way as the sign shows them; the kid's is targetStop.")]
        public string[] stopNames = { "SW 8 St & 17 Av", "SW 8 St & 12 Av", "Brickell Av", "SE 1 St" };
        public int targetStop = 2;
        [Tooltip("Seconds added to the trip for the walk back from the stop after yours.")]
        public float walkBackPenalty = 15f;

        enum Phase { Arriving, Boarding, Leaving, Riding, Stopped, GettingOff, Done }

        Phase phase;
        float phaseTime, segmentTime, speed, push;
        int segment;
        bool paid, requested, wobbling, wobbled, missedStop;
        Image balanceMarker;
        RectTransform balanceBar;
        Text sign;
        Button stopButton, cardButton;

        static readonly Color Green = new Color(0.25f, 0.9f, 0.4f), Red = new Color(0.95f, 0.25f, 0.2f);

        public override string StarText(int star)
        {
            if (star == 1) return Loc.T("mini.bus.star1");
            if (star == 2) return Loc.F("mini.bus.star2", stopNames[Mathf.Clamp(targetStop, 0, stopNames.Length - 1)]);
            return Loc.T("mini.bus.star3");
        }

        void Start()
        {
            BuildHud();
            ResetState();
        }

        public override void ResetState()
        {
            base.ResetState();
            paid = requested = wobbling = wobbled = missedStop = false;
            segment = 0;
            speed = push = 0f;
            Enter(Phase.Arriving);
        }

        void Enter(Phase next)
        {
            phase = next;
            phaseTime = 0f;
            bool here = next != Phase.Arriving && next != Phase.Leaving;
            if (busColliders != null)
                foreach (var c in busColliders) if (c != null) c.enabled = here || next == Phase.Leaving && KidInside;
            if (door != null) door.enabled = next == Phase.Riding;
            if (next == Phase.Riding) segmentTime = 0f;
        }

        bool KidInside { get { return Level != null && Level.kid != null && Across(Level.kid.transform.position.x) > 0.6f; } }
        bool BallInside { get { return Level != null && Level.ball != null && Across(Level.ball.transform.position.x) > 0.3f; } }

        protected override void Update()
        {
            base.Update();
            if (!Running) { RefreshHud(); return; }
            float dt = Time.deltaTime;
            phaseTime += dt;
            switch (phase)
            {
                case Phase.Arriving:
                    Say("mini.bus.coming");
                    PlaceBus(Mathf.Lerp(inward * driveOffset, 0f, Ease(phaseTime / 2.5f)),
                        Mathf.Lerp(pullOutZ, 0f, Ease((phaseTime - 1.2f) / 1.3f)));
                    if (phaseTime >= 2.5f) { paid = false; Enter(Phase.Boarding); }
                    break;
                case Phase.Boarding:
                    Boarding();
                    break;
                case Phase.Leaving:
                    Say("mini.bus.missed");
                    // Out into the road first, then away: past the kid at the stop, not through them.
                    PlaceBus(Mathf.Lerp(0f, -inward * driveOffset, Ease(phaseTime / 2.5f)), Mathf.Lerp(0f, pullOutZ, Ease(phaseTime / 0.6f)));
                    if (phaseTime >= 5f) Enter(Phase.Arriving);     // the next bus along
                    break;
                case Phase.Riding:
                    Riding(dt);
                    break;
                case Phase.Stopped:
                    speed = 0f;
                    if (phaseTime >= 2.5f) { requested = false; Enter(Phase.Riding); }   // not yours: the doors shut, on it goes
                    break;
                case Phase.GettingOff:
                    speed = 0f;
                    Say(missedStop ? "mini.bus.walkBack" : "mini.bus.off");
                    var kid = Level.kid.transform.position;
                    var ball = Level.ball.transform.position;
                    if (Across(kid.x) < -0.8f && Across(ball.x) < 0f && Mathf.Abs(ball.x - kid.x) < 2.5f)
                    {
                        phase = Phase.Done;
                        Pass(1 + (missedStop ? 0 : 1) + (wobbled ? 0 : 1));
                    }
                    break;
            }
            ScrollStreet(dt);
            ShowNearSide();
            RefreshHud();
        }

        /// <summary>The near side is there while the bus pulls in or away, and while the kid is well short of the door.</summary>
        void ShowNearSide()
        {
            if (nearSide == null || Level == null || Level.kid == null) return;
            bool atStop = phase != Phase.Arriving && phase != Phase.Leaving;
            bool show = !atStop || Across(Level.kid.transform.position.x) < -2.5f;
            if (nearSide.activeSelf != show) nearSide.SetActive(show);
        }

        /// <summary>How far past the doorway into the bus x is (negative: outside, at the stop).</summary>
        float Across(float x) { return (x - doorX) * Mathf.Sign(inward); }

        void Boarding()
        {
            PlaceBus(0f, 0f);
            bool green = Mathf.Repeat(phaseTime, 1.8f) < 0.75f;
            if (readerLight != null) World.Tint.Set(readerLight, paid ? Green : green ? Green : Red);
            if (!paid)
            {
                Say("mini.bus.card");
                if (phaseTime > 14f) Enter(Phase.Leaving);       // nobody got on: the bus goes
                return;
            }
            float left = 7f - (phaseTime - paidAt);
            if (KidInside && BallInside)
            {
                Say("mini.bus.hold");
                Enter(Phase.Riding);
                return;
            }
            Say(KidInside ? "mini.bus.ball" : "mini.bus.board", Mathf.CeilToInt(Mathf.Max(0f, left)));
            if (left <= 0f) Enter(Phase.Leaving);
        }

        float paidAt;

        void TapCard()
        {
            if (phase != Phase.Boarding || paid || !Running) return;
            bool green = Mathf.Repeat(phaseTime, 1.8f) < 0.75f;
            if (!green)
            {
                Say("mini.bus.wait");
                return;
            }
            paid = true;
            paidAt = phaseTime;
            GameEvents.Raise(GameEventType.SwitchPressed, new Vector3(readerX, 1.2f, 0f));
        }

        void PullCord()
        {
            if (phase != Phase.Riding || requested || !Running) return;
            requested = true;
            GameEvents.Raise(GameEventType.SwitchPressed, Level.kid.transform.position + Vector3.up * 1.6f);
        }

        /// <summary>
        /// One stop to the next: away (2 s), along with the sway (5 s, a hard brake for the lights in the middle of the second and
        /// third), and in to the stop (2 s), stopping there only if STOP was pressed, at the stop after the kid's, or at the last.
        /// </summary>
        void Riding(float dt)
        {
            segmentTime += dt;
            float t = segmentTime;
            bool lights = segment == 1 || segment == 2;
            bool stopping = requested || segment == targetStop + 1 || segment == stopNames.Length - 1;
            if (t < 2f) { push = -3.2f * (1f - t / 2f) - 0.6f; speed = Mathf.Lerp(0f, 9f, t / 2f); }
            else if (t < 7f)
            {
                speed = 9f;
                push = 1.5f * Mathf.Sin(t * 0.9f + segment) + 0.7f * Mathf.Sin(t * 2.3f);
                if (lights && t > 4.2f && t < 4.6f) Say("mini.bus.brakeSoon");
                else if (lights && t >= 4.6f && t < 5.7f) { push = 9f; speed = Mathf.Lerp(9f, 2f, (t - 4.6f) / 1.1f); }
                else Say(requested ? "mini.bus.stopping" : "mini.bus.ride", stopNames[Mathf.Min(segment, stopNames.Length - 1)]);
            }
            else if (t < 9f)
            {
                push = stopping ? 4f : 0.5f;
                speed = stopping ? Mathf.Lerp(9f, 0f, (t - 7f) / 2f) : 9f;
            }
            else
            {
                push = 0f;
                if (stopping) ArriveAt(segment);
                else segment++;
                segmentTime = 0f;
            }
            ApplySway(dt);
        }

        void ArriveAt(int stop)
        {
            segment = stop + 1;
            if (stop == targetStop || stop > targetStop)
            {
                missedStop = stop != targetStop;
                if (missedStop && Level != null) Level.AddPenalty(walkBackPenalty);
                Enter(Phase.GettingOff);
                return;
            }
            Say("mini.bus.notYours", stopNames[targetStop]);
            Enter(Phase.Stopped);
        }

        /// <summary>The bus's push on what stands in it (a held ball stays at the kid's feet); the balance bar's measure.</summary>
        void ApplySway(float dt)
        {
            var level = Level;
            if (level == null || level.ball == null || level.kid == null) return;
            var ball = level.ball;
            if (!ball.IsHeldUnderFoot && !ball.InCloseControl)
                ball.Body.linearVelocity += new Vector2(push * dt, 0f);
            else if (Mathf.Abs(push) > 6f)
                ball.Body.linearVelocity += new Vector2(push * 0.12f * dt, 0f);
            level.kid.Body.linearVelocity += new Vector2(push * 0.3f * dt, 0f);
            float off = Mathf.Abs(ball.transform.position.x - level.kid.transform.position.x);
            if (!wobbling && off > 1.6f) { wobbling = true; wobbled = true; Say("mini.bus.wobble"); }
            else if (wobbling && off < 0.8f) wobbling = false;
        }

        void PlaceBus(float dx, float dz = 0f)
        {
            if (busBody == null) return;
            var p = busBody.localPosition;
            busBody.localPosition = new Vector3(dx, p.y, dz);
        }

        void ScrollStreet(float dt)
        {
            if (street == null) return;
            var p = street.localPosition;
            float x = p.x - speed * dt;
            if (x < -stripLength) x += stripLength;
            street.localPosition = new Vector3(x, p.y, p.z);
        }

        static float Ease(float t)
        {
            t = Mathf.Clamp01(t);
            return t * t * (3f - 2f * t);
        }

        // ------------------------------------------------------------------ the HUD: the stop sign, the balance bar, CARD and STOP

        void BuildHud()
        {
            var signCard = UIKit.Panel(Hud.transform, "StopSign", new Color(0.05f, 0.05f, 0.06f, 0.92f), ProceduralSprites.Rounded);
            UIKit.Place(signCard.rectTransform, new Vector2(1f, 1f), new Vector2(-330f, -180f), new Vector2(560f, 92f));
            sign = UIKit.Label(signCard.transform, "Text", "", 34, new Color(1f, 0.62f, 0.15f), TextAnchor.MiddleCenter, true);
            UIKit.Stretch(sign.rectTransform, 10f);
            UIKit.Fit(sign, 20);

            var bar = UIKit.Panel(Hud.transform, "Balance", new Color(0f, 0f, 0f, 0.35f), ProceduralSprites.Rounded);
            balanceBar = bar.rectTransform;
            UIKit.Place(balanceBar, new Vector2(0.5f, 0f), new Vector2(0f, 300f), new Vector2(520f, 34f));
            var mid = UIKit.Panel(bar.transform, "Middle", new Color(1f, 1f, 1f, 0.5f));
            UIKit.Place(mid.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(4f, 34f));
            balanceMarker = UIKit.Icon(bar.transform, "Ball", ProceduralSprites.Circle, Color.white, 40f);

            cardButton = BigButton("Card", "mini.bus.cardButton", new Vector2(1f, 0f), new Vector2(-230f, 420f), new Vector2(300f, 130f), UITheme.Green, TapCard);
            stopButton = BigButton("Stop", "mini.bus.stopButton", new Vector2(1f, 0f), new Vector2(-230f, 420f), new Vector2(300f, 130f), UITheme.Red, PullCord);
        }

        void RefreshHud()
        {
            if (sign == null) return;
            bool riding = phase == Phase.Riding || phase == Phase.Stopped;
            int next = Mathf.Min(segment, stopNames.Length - 1);
            string line = riding ? Loc.F("mini.bus.next", stopNames[next]) : "";
            if (sign.text != line) sign.text = line;
            sign.transform.parent.gameObject.SetActive(riding);
            status = riding ? line : "";
            balanceBar.gameObject.SetActive(riding);
            if (riding && Level != null && Level.ball != null && Level.kid != null)
            {
                float off = Mathf.Clamp((Level.ball.transform.position.x - Level.kid.transform.position.x) / 2f, -1f, 1f);
                balanceMarker.rectTransform.anchoredPosition = new Vector2(off * 240f, 0f);
                balanceMarker.color = Mathf.Abs(off) > 0.75f ? UITheme.Red : Mathf.Abs(off) > 0.4f ? UITheme.Gold : UITheme.Green;
            }
            bool atReader = phase == Phase.Boarding && !paid && Level != null && Level.kid != null &&
                            Mathf.Abs(Level.kid.transform.position.x - readerX) < 1.8f;
            cardButton.gameObject.SetActive(atReader);
            stopButton.gameObject.SetActive(phase == Phase.Riding);
            stopButton.interactable = !requested;
        }
    }
}
