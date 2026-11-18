using System.Collections.Generic;
using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.Challenges
{
    /// <summary>
    /// M3, shopping for classwork (docs/CITIES.md), as Miami's corner drugstore (FL2-4): poster board, a glue stick and markers
    /// for the science project's sign.
    /// 1. **Find them.** The list shows what to get; the shelf holds those and other things. Tap each thing on the list (a tap on
    ///    something that isn't is a slip: "Not on the list!").
    /// 2. **Pay.** At the counter the till shows the total. Tap notes and coins from your wallet onto the counter (tap one there to
    ///    take it back) until they add up, the fewest you can, and PAY.
    /// 3. **Check the change.** If you paid too much the cashier counts your change: pick the amount that is right.
    /// Stars: paid for everything; no slips; and the exact money with the fewest notes and coins it can be paid with.
    /// The money is worked in cents (<see cref="Fewest"/> is the plain greedy count, exact for US money).
    /// The kid stands in the aisle; the shopping is done on the screen (the stick and the buttons are off meanwhile).
    /// </summary>
    public class DrugstoreShopping : MiniGameObjective
    {
        /// <summary>A thing on the shelf (its name's string key and its price in cents).</summary>
        [System.Serializable]
        public struct Item
        {
            public string key;
            public int cents;
            public bool onList;
            public Item(string key, int cents, bool onList) { this.key = key; this.cents = cents; this.onList = onList; }
        }

        public Item[] shelf =
        {
            new Item("mini.shop.item.poster", 199, true),
            new Item("mini.shop.item.sunscreen", 699, false),
            new Item("mini.shop.item.glue", 129, true),
            new Item("mini.shop.item.notebook", 249, false),
            new Item("mini.shop.item.markers", 349, true),
            new Item("mini.shop.item.gum", 100, false),
            new Item("mini.shop.item.ruler", 99, false),
            new Item("mini.shop.item.crayons", 229, false),
        };

        /// <summary>The kid's wallet, in cents: a ten, a five, three ones, four quarters, three dimes, two nickels and four pennies.</summary>
        public int[] wallet = { 1000, 500, 100, 100, 100, 25, 25, 25, 25, 10, 10, 10, 5, 5, 1, 1, 1, 1 };

        /// <summary>The denominations, largest first (cents).</summary>
        public static readonly int[] Money = { 1000, 500, 100, 25, 10, 5, 1 };

        enum Phase { Shelf, Pay, Change, Done }

        Phase phase;
        int slips;
        readonly HashSet<int> basket = new HashSet<int>();
        readonly List<int> onCounter = new List<int>();     // indices into wallet
        RectTransform panel;
        bool built;

        public override string StarText(int star)
        {
            if (star == 1) return Loc.T("mini.shop.star1");
            if (star == 2) return Loc.T("mini.shop.star2");
            return Loc.T("mini.shop.star3");
        }

        /// <summary>What the list comes to, in cents.</summary>
        public int Total
        {
            get
            {
                int t = 0;
                foreach (var i in shelf) if (i.onList) t += i.cents;
                return t;
            }
        }

        /// <summary>The fewest notes and coins that make exactly <paramref name="cents"/> (US money: the greedy count is exact).</summary>
        public static int Fewest(int cents)
        {
            int n = 0;
            foreach (int m in Money)
            {
                n += cents / m;
                cents %= m;
            }
            return n;
        }

        /// <summary>
        /// The stars for a finished shop (pure: the tests use it): one for paying, one for no slips, one for the exact money in the
        /// fewest pieces.
        /// </summary>
        public static int StarsFor(int slips, int paidCents, int pieces, int totalCents)
        {
            return 1 + (slips == 0 ? 1 : 0) + (paidCents == totalCents && pieces == Fewest(totalCents) ? 1 : 0);
        }

        /// <summary>Money as it reads at the till ("$6.77").</summary>
        public static string Dollars(int cents) { return "$" + (cents / 100) + "." + (cents % 100).ToString("00"); }

        public override void ResetState()
        {
            base.ResetState();
            slips = 0;
            basket.Clear();
            onCounter.Clear();
            phase = Phase.Shelf;
            if (built) Show();
        }

        protected override void Update()
        {
            base.Update();
            var level = Level;
            if (level == null) return;
            bool playing = Running;
            if (playing && !built)
            {
                built = true;
                Show();
            }
            if (panel != null) panel.gameObject.SetActive(playing && phase != Phase.Done);
            // The shopping is on the screen: the kid stands in the aisle meanwhile.
            if (playing && level.kid != null) level.kid.InputEnabled = false;
            status = playing ? Loc.F("mini.shop.status", basket.Count, 3) : "";
        }

        // ------------------------------------------------------------------ the screens

        void Show()
        {
            if (panel != null) Destroy(panel.gameObject);
            var card = UIKit.Card(Hud.transform, "Shop", UITheme.Panel);
            panel = card.rectTransform;
            UIKit.Place(panel, new Vector2(0.5f, 0.5f), new Vector2(0f, -40f), new Vector2(1500f, 680f));
            switch (phase)
            {
                case Phase.Shelf: ShowShelf(); break;
                case Phase.Pay: ShowPay(); break;
                case Phase.Change: ShowChange(); break;
            }
        }

        Text Heading(string text)
        {
            var t = UIKit.Label(panel, "Heading", text, 40, UITheme.Ink, TextAnchor.MiddleCenter, true);
            UIKit.Place(t.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -50f), new Vector2(1400f, 70f));
            UIKit.Fit(t, 26);
            return t;
        }

        void ShowShelf()
        {
            var list = new List<string>();
            foreach (var i in shelf) if (i.onList) list.Add((basket.Contains(System.Array.IndexOf(shelf, i)) ? "[x] " : "[ ] ") + Loc.T(i.key));
            Heading(Loc.T("mini.shop.list") + "   " + string.Join("   ", list.ToArray()));
            for (int k = 0; k < shelf.Length; k++)
            {
                int index = k;
                var item = shelf[k];
                bool got = basket.Contains(k);
                var b = UIKit.Button(panel, "Item" + k, Loc.T(item.key) + "\n" + Dollars(item.cents), got ? UITheme.Green : UITheme.Paper, () => Pick(index), 30, UITheme.Ink);
                UIKit.Place((RectTransform)b.transform, new Vector2(0.5f, 0.5f), new Vector2((k % 4 - 1.5f) * 350f, k < 4 ? 90f : -120f), new Vector2(320f, 170f));
                b.interactable = !got;
            }
            Say(slips > 0 ? "mini.shop.slip" : "mini.shop.find");
        }

        void Pick(int index)
        {
            if (!Running || phase != Phase.Shelf) return;
            if (!shelf[index].onList)
            {
                slips++;
                Say("mini.shop.slip");
                return;
            }
            basket.Add(index);
            GameEvents.Raise(GameEventType.Coin, Level.kid.transform.position + Vector3.up);
            if (basket.Count >= 3) phase = Phase.Pay;
            Show();
        }

        int Paid
        {
            get
            {
                int c = 0;
                foreach (int w in onCounter) c += wallet[w];
                return c;
            }
        }

        void ShowPay()
        {
            Heading(Loc.F("mini.shop.total", Dollars(Total), Dollars(Paid)));
            for (int w = 0; w < wallet.Length; w++)
            {
                int index = w;
                bool there = onCounter.Contains(w);
                var b = UIKit.Button(panel, "Money" + w, Dollars(wallet[w]), there ? UITheme.Gold : wallet[w] >= 100 ? new Color(0.62f, 0.82f, 0.62f) : new Color(0.86f, 0.82f, 0.7f),
                    () => Move(index), 28, UITheme.Ink);
                int row = w < 9 ? 0 : 1, col = w < 9 ? w : w - 9;
                UIKit.Place((RectTransform)b.transform, new Vector2(0.5f, 0.5f), new Vector2((col - 4f) * 152f, there ? 150f - row * 10f : -40f - row * 130f), new Vector2(140f, 110f));
            }
            var pay = UIKit.Button(panel, "Pay", Loc.T("mini.shop.pay"), UITheme.Accent, PayNow, 40);
            UIKit.Place((RectTransform)pay.transform, new Vector2(0.5f, 0f), new Vector2(0f, 70f), new Vector2(360f, 100f));
            pay.interactable = Paid >= Total;
            Say(Paid >= Total ? "mini.shop.payNow" : "mini.shop.count");
        }

        void Move(int index)
        {
            if (!Running || phase != Phase.Pay) return;
            if (!onCounter.Remove(index)) onCounter.Add(index);
            Show();
        }

        void PayNow()
        {
            if (!Running || phase != Phase.Pay || Paid < Total) return;
            if (Paid == Total) Done();
            else
            {
                phase = Phase.Change;
                Show();
            }
        }

        void ShowChange()
        {
            int change = Paid - Total;
            Heading(Loc.F("mini.shop.changeQ", Dollars(Paid), Dollars(Total)));
            // The right change and two near misses, in an order that depends on the amount (not always first).
            var options = new List<int> { change, change + 10, Mathf.Max(1, change - 100 > 0 ? change - 100 : change + 100) };
            int turn = change % 3;
            for (int k = 0; k < 3; k++)
            {
                int amount = options[(k + turn) % 3];
                var b = UIKit.Button(panel, "Change" + k, Dollars(amount), UITheme.Paper, () => ChooseChange(amount), 40, UITheme.Ink);
                UIKit.Place((RectTransform)b.transform, new Vector2(0.5f, 0.5f), new Vector2((k - 1) * 420f, -40f), new Vector2(380f, 150f));
            }
            Say("mini.shop.change");
        }

        void ChooseChange(int amount)
        {
            if (!Running || phase != Phase.Change) return;
            if (amount != Paid - Total)
            {
                slips++;
                Say("mini.shop.countAgain");
                return;
            }
            Done();
        }

        void Done()
        {
            phase = Phase.Done;
            if (panel != null) panel.gameObject.SetActive(false);
            Say("mini.shop.thanks");
            GameEvents.Raise(GameEventType.SwitchPressed, Level.kid.transform.position + Vector3.up);
            Pass(StarsFor(slips, Paid, onCounter.Count, Total));
        }
    }
}
