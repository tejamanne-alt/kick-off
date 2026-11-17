using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Localization;
using DribbleToSchool.Player;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.MiniGames
{
    /// <summary>
    /// The ride itself, drawn from the user's set pictures: the car straight across the aisle (KM1-2a, its windows clear), the
    /// town sliding past behind its windows (KM1-2b, whose ends meet), each station's platform in the windows while the car
    /// stands there (KM1-2c), the next-stop display, the ball at the kid's feet and its steady zone, STOP, and the seat.
    /// </summary>
    public class RideOverlay : MiniGameOverlay
    {
        enum Phase { Card, Riding, Braking, Stopped, Arrived }

        Phase phase;
        float t, phaseTime, steadyTime, rideTime, scroll;
        int next;                                 // the stop the display shows next
        bool stopPressed, stopRight, seatGiven, seatOffered;
        RideRules.Ball ball;
        int cardTries;

        RawImage town, station;
        Texture2D townTexture, stationsTexture;
        RectTransform ballRect, ring;
        Image ringImage;
        Text display, message, coinsText;
        HoldKey stopKey, seatKey, leftKey, rightKey, braceKey, cardKey;
        GameObject rideKeys;
        float messageUntil;

        const float CarWidth = 1920f, CarHeight = 640f, CarY = -40f;
        // the car picture's part shown (KM1-2a: its middle, the door near the right) and its windows' band in it
        static readonly Rect CarUv = new Rect(0.12f, 0f, 0.8f, 1f);
        const float WindowTop = 246f / 1024f, WindowBottom = 603f / 1024f;
        const float FloorY = CarY - CarHeight * 0.5f + CarHeight * (1f - 880f / 1024f);

        void Start()
        {
            Open("Ride");
            var shade = UIKit.Panel(root, "Shade", new Color(0.06f, 0.08f, 0.14f));
            UIKit.Stretch(shade.rectTransform, -400f);

            // the town behind the windows, then the car over it
            townTexture = Picture("ride_town");
            stationsTexture = Picture("ride_stations");
            if (townTexture != null) townTexture.wrapMode = TextureWrapMode.Repeat;
            float bandTop = CarY + CarHeight * 0.5f - CarHeight * WindowTop, bandBottom = CarY + CarHeight * 0.5f - CarHeight * WindowBottom;
            float bandH = (bandTop - bandBottom) + 60f;
            float townAspect = townTexture != null ? townTexture.width / (float)townTexture.height : 4f;
            town = Picture(root, "Town", townTexture, new Vector2(0f, (bandTop + bandBottom) * 0.5f), new Vector2(CarWidth, bandH),
                new Rect(0f, 0f, CarWidth / (bandH * townAspect), 1f));
            station = Picture(root, "Station", stationsTexture, new Vector2(0f, (bandTop + bandBottom) * 0.5f), new Vector2(CarWidth, bandH),
                new Rect(0f, 0f, 1f / 3f, 1f));
            station.enabled = false;
            Picture(root, "Car", Picture("ride_car"), new Vector2(0f, CarY), new Vector2(CarWidth, CarHeight), CarUv);

            // the next-stop display over the car, the message line, the coins
            var board = UIKit.Panel(root, "Display", new Color(0.05f, 0.05f, 0.07f, 0.92f));
            UIKit.Place(board.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -70f), new Vector2(760f, 84f));
            display = UIKit.Label(board.transform, "Text", "", 40, new Color(1f, 0.62f, 0.15f), TextAnchor.MiddleCenter, true);
            UIKit.Stretch(display.rectTransform);
            message = Words(root, "Message", "", 40, new Vector2(0f, 330f), new Vector2(1300f, 60f), Color.white);
            coinsText = Words(root, "Coins", "", 34, Vector2.zero, new Vector2(240f, 50f), UITheme.Gold);
            UIKit.Place(coinsText.rectTransform, new Vector2(1f, 1f), new Vector2(-150f, -70f), new Vector2(240f, 50f), new Vector2(0.5f, 0.5f));

            // the ball at the kid's feet and its steady zone along the aisle's floor
            var zone = UIKit.Panel(root, "Zone", new Color(1f, 1f, 1f, 0.18f));
            UIKit.Place(zone.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(0f, FloorY + 4f), new Vector2(560f, 12f));
            var steady = UIKit.Panel(zone.transform, "Steady", new Color(0.4f, 0.9f, 0.5f, 0.55f));
            UIKit.Place(steady.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(280f, 12f));
            var b = UIKit.Icon(root, "Ball", ProceduralSprites.BallIcon, Color.white, 74f);
            ballRect = b.rectTransform;

            // the keys: lean left and right (or the stick), brace (or KICK), STOP and the seat
            rideKeys = UIKit.Rect(root, "Keys").gameObject;
            // (from the screen's bottom corners, where the thumbs are, at any width: MiniGameOverlay.Key)
            leftKey = Key(rideKeys.transform, "Left", "<", UITheme.Blue, new Vector2(0f, 0f), new Vector2(130f, 125f), 150f);
            rightKey = Key(rideKeys.transform, "Right", ">", UITheme.Blue, new Vector2(0f, 0f), new Vector2(320f, 125f), 150f);
            braceKey = Key(rideKeys.transform, "Brace", Loc.T("mini.ride.brace"), UITheme.Accent, new Vector2(1f, 0f), new Vector2(-360f, 125f), 170f);
            stopKey = Key(rideKeys.transform, "Stop", Loc.T("mini.ride.stop"), UITheme.Red, new Vector2(1f, 0f), new Vector2(-140f, 145f), 210f);
            stopKey.Tapped += PressStop;
            seatKey = Key(root, "Seat", Loc.T("mini.ride.seat"), UITheme.Green, new Vector2(0f, -420f), 220f);
            seatKey.Tapped += GiveSeat;
            seatKey.gameObject.SetActive(false);
            rideKeys.SetActive(false);

            // the card reader at Hase's gate: a ring closing over the reader; tap while it is in the green
            var reader = UIKit.Rect(root, "Reader");
            UIKit.Place(reader, new Vector2(0.5f, 0.5f), new Vector2(0f, 60f), new Vector2(300f, 300f));
            ringImage = UIKit.Icon(reader, "Ring", ProceduralSprites.CircleEdge, Color.white, 300f);
            ring = ringImage.rectTransform;
            UIKit.Icon(reader, "Green", ProceduralSprites.CircleEdge, new Color(0.4f, 0.95f, 0.5f, 0.6f), 300f * (1f - RideRules.CardGoodFrom * 0.8f));
            cardKey = Key(reader, "Card", Loc.T("mini.ride.card"), UITheme.Navy, Vector2.zero, 150f);
            cardKey.Tapped += TapCard;
            Say(Loc.T("mini.ride.card"), 99f);
            phase = Phase.Card;
        }

        void Update()
        {
            float dt = Dt;
            t += dt;
            phaseTime += dt;
            if (Time.unscaledTime > messageUntil) message.text = "";
            switch (phase)
            {
                case Phase.Card: Card(); break;
                case Phase.Riding:
                case Phase.Braking: Ride(dt); break;
                case Phase.Stopped: Stopped(); break;
                case Phase.Arrived:
                    if (phaseTime > 2.6f) Finish();
                    break;
            }
            float shown = Mathf.Clamp(ball.offset, -1.2f, 1.2f);
            ballRect.anchoredPosition = new Vector2(shown * 280f, FloorY + 40f);
            ballRect.localRotation = Quaternion.Euler(0f, 0f, -ball.offset * 160f);
            coinsText.text = Earned() + " / " + RideRules.PossibleCoins;
        }

        // ------------------------------------------------------------------ the card at the gate

        void Card()
        {
            float p = Mathf.Repeat(phaseTime, RideRules.CardTime) / RideRules.CardTime;
            float size = 300f * (1f - p * 0.8f);
            ring.sizeDelta = new Vector2(size, size);
            ringImage.color = RideRules.CardTapGood(p) ? new Color(0.4f, 0.95f, 0.5f) : Color.white;
        }

        void TapCard()
        {
            if (phase != Phase.Card) return;
            float p = Mathf.Repeat(phaseTime, RideRules.CardTime) / RideRules.CardTime;
            if (RideRules.CardTapGood(p))
            {
                ring.parent.gameObject.SetActive(false);
                Say(Loc.T("mini.ride.cardGood"), 1.6f);
                Begin(Phase.Riding);
                rideKeys.SetActive(true);
            }
            else
            {
                cardTries++;
                phaseTime = 0f;
                Say(Loc.T("mini.ride.cardLate"), 1.2f);
            }
        }

        // ------------------------------------------------------------------ riding between the stops

        void Ride(float dt)
        {
            var input = GameInput.Instance;
            float lean = (rightKey.Held ? 1f : 0f) - (leftKey.Held ? 1f : 0f);
            if (input != null && Mathf.Abs(input.MoveAxis) > 0.1f) lean = input.MoveAxis;
            bool brace = braceKey.Held || (input != null && input.KickHeld);
            bool braking = phase == Phase.Braking;
            RideRules.Step(ref ball, RideRules.Sway(t) * (braking ? 0.3f : 1f), lean, braking, brace, dt);
            rideTime += dt;
            if (RideRules.Steady(ball)) steadyTime += dt;

            float speed = braking ? Mathf.Lerp(1f, 0f, phaseTime / RideRules.Brake) : 1f;
            scroll += speed * 0.11f * dt;
            if (town != null)
            {
                var uv = town.uvRect;
                uv.x = scroll;
                town.uvRect = uv;
            }
            display.text = Loc.F("mini.ride.next", Loc.T("station." + RideRules.Stations[next]));

            if (phase == Phase.Riding && phaseTime >= RideRules.Between)
            {
                Begin(Phase.Braking);
                Say(Loc.T("mini.ride.brake"), RideRules.Brake);
            }
            else if (phase == Phase.Braking && phaseTime >= RideRules.Brake)
            {
                if (next == RideRules.Destination)
                {
                    rideKeys.SetActive(false);
                    Say(Loc.T(stopPressed ? "mini.ride.arrive" : "mini.ride.missed"), 3f);
                    ShowStation(next);
                    Begin(Phase.Arrived);
                }
                else
                {
                    ShowStation(next);
                    Begin(Phase.Stopped);
                    if (next == RideRules.GrandmaBoards && !seatOffered)
                    {
                        seatOffered = true;
                        seatKey.gameObject.SetActive(true);
                        Say(Loc.T("mini.ride.grandma"), RideRules.Dwell);
                    }
                }
            }
        }

        void Stopped()
        {
            display.text = Loc.T("station." + RideRules.Stations[next]);
            if (phaseTime < RideRules.Dwell) return;
            seatKey.gameObject.SetActive(false);
            station.enabled = false;
            next++;
            Begin(Phase.Riding);
        }

        void ShowStation(int index)
        {
            if (stationsTexture == null) return;
            station.uvRect = new Rect(index / 3f, 0f, 1f / 3f, 1f);
            station.enabled = true;
        }

        void PressStop()
        {
            if (phase != Phase.Riding && phase != Phase.Braking) return;
            if (stopPressed) return;
            if (RideRules.StopIsRight(next))
            {
                stopPressed = stopRight = true;
                Say(Loc.T("mini.ride.stopping"), 2f);
            }
            else Say(Loc.T("mini.ride.notYet"), 1.4f);
        }

        void GiveSeat()
        {
            if (seatGiven || phase != Phase.Stopped) return;
            seatGiven = true;
            seatKey.gameObject.SetActive(false);
            Say(Loc.T("mini.ride.thanks"), 2f);
        }

        // ------------------------------------------------------------------ the end

        int Earned()
        {
            float share = rideTime > 0f ? steadyTime / rideTime : 0f;
            return RideRules.SteadyPay(share) + (stopRight ? RideRules.StopCoins : 0) + (seatGiven ? RideRules.SeatCoins : 0);
        }

        void Finish()
        {
            if (level != null) level.CollectBonus(Earned(), RideRules.PossibleCoins);
            Close(true);
        }

        void Begin(Phase p)
        {
            phase = p;
            phaseTime = 0f;
        }

        void Say(string text, float seconds)
        {
            message.text = text;
            messageUntil = Time.unscaledTime + seconds;
        }
    }
}
