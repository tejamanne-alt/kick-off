using System.Collections.Generic;
using DribbleToSchool.Core;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.Progression;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>
    /// The Locker Room: browse balls, flags, outfits and trails; preview the
    /// selected item large; buy with coins or equip what you own.
    /// </summary>
    public class ShopScreen : FrontEndScreen
    {
        static readonly CosmeticCategory[] Categories =
            { CosmeticCategory.Ball, CosmeticCategory.Flag, CosmeticCategory.Outfit, CosmeticCategory.Trail };
        static readonly string[] CategoryNames = { "Balls", "Flags", "Outfits", "Trails" };

        CosmeticCategory category = CosmeticCategory.Ball;
        CosmeticItem selected;

        readonly List<Button> tabButtons = new List<Button>();
        RectTransform grid;
        Image previewIcon;
        Text previewName;
        Text previewRarity;
        Button actionButton;
        Text actionLabel;
        RectTransform previewPrice;
        Text previewPriceText;

        public override string Title { get { return "Locker Room"; } }

        protected override void Build(RectTransform root)
        {
            // Category tabs
            var tabRow = UIKit.Rect(root, "Tabs");
            UIKit.Place(tabRow, new Vector2(0.5f, 1f), new Vector2(0f, -205f), new Vector2(4 * 290f, 100f), new Vector2(0.5f, 0.5f));
            for (int i = 0; i < Categories.Length; i++)
            {
                var cat = Categories[i];
                var tab = UIKit.Button(tabRow, "Tab" + cat, CategoryNames[i], UITheme.Blue, () => SelectCategory(cat), 36);
                UIKit.Place((RectTransform)tab.transform, new Vector2(0f, 0.5f), new Vector2(i * 290f, 0f), new Vector2(270f, 90f), new Vector2(0f, 0.5f));
                tabButtons.Add(tab);
            }

            // Preview panel (left)
            var preview = UIKit.Card(root, "Preview", UITheme.Paper);
            var previewRoot = (RectTransform)preview.transform.parent;
            previewRoot.anchorMin = new Vector2(0f, 0f);
            previewRoot.anchorMax = new Vector2(0f, 1f);
            previewRoot.pivot = new Vector2(0f, 0.5f);
            previewRoot.offsetMin = new Vector2(60f, 60f);
            previewRoot.offsetMax = new Vector2(60f + 560f, -280f);

            previewIcon = UIKit.Icon(preview.transform, "Icon", null, Color.white, 300f);
            UIKit.Place(previewIcon.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -60f), new Vector2(320f, 320f), new Vector2(0.5f, 1f));
            previewIcon.gameObject.AddComponent<UIPulse>().amount = 0.03f;

            previewName = UIKit.Label(preview.transform, "Name", "", 52, UITheme.Ink, TextAnchor.MiddleCenter, true);
            UIKit.Place(previewName.rectTransform, new Vector2(0.5f, 0f), new Vector2(0f, 300f), new Vector2(520f, 70f), new Vector2(0.5f, 0.5f));
            previewRarity = UIKit.Label(preview.transform, "Rarity", "", 32, UITheme.InkSoft, TextAnchor.MiddleCenter, true);
            UIKit.Place(previewRarity.rectTransform, new Vector2(0.5f, 0f), new Vector2(0f, 245f), new Vector2(520f, 50f), new Vector2(0.5f, 0.5f));

            previewPriceText = UIKit.CoinAmount(preview.transform, "Price", 0, 48, UITheme.Ink);
            previewPrice = (RectTransform)previewPriceText.transform.parent;
            UIKit.Place(previewPrice, new Vector2(0.5f, 0f), new Vector2(0f, 185f), new Vector2(300f, 60f), new Vector2(0.5f, 0.5f));

            actionButton = UIKit.Button(preview.transform, "Action", "Equip", UITheme.Green, OnAction, 48);
            UIKit.Place((RectTransform)actionButton.transform, new Vector2(0.5f, 0f), new Vector2(0f, 80f), new Vector2(380f, 120f), new Vector2(0.5f, 0.5f));
            actionLabel = actionButton.GetComponentInChildren<Text>();

            // Item grid (right)
            ScrollRect scroll;
            grid = UIKit.ScrollArea(root, "Grid", true, out scroll);
            var gridRoot = (RectTransform)scroll.transform;
            gridRoot.anchorMin = new Vector2(0f, 0f);
            gridRoot.anchorMax = new Vector2(1f, 1f);
            gridRoot.offsetMin = new Vector2(660f, 40f);
            gridRoot.offsetMax = new Vector2(-60f, -280f);
            var layout = grid.gameObject.AddComponent<GridLayoutGroup>();
            layout.cellSize = new Vector2(240f, 290f);
            layout.spacing = new Vector2(28f, 28f);
            layout.padding = new RectOffset(10, 10, 20, 30);
            var fitter = grid.gameObject.AddComponent<ContentSizeFitter>();
            fitter.verticalFit = ContentSizeFitter.FitMode.PreferredSize;
        }

        public override void OnShow()
        {
            SelectCategory(category);
        }

        void SelectCategory(CosmeticCategory cat)
        {
            category = cat;
            for (int i = 0; i < tabButtons.Count; i++)
                tabButtons[i].targetGraphic.color = Categories[i] == cat ? UITheme.Accent : UITheme.Blue;

            var items = Controller.cosmetics != null ? Controller.cosmetics.InCategory(cat) : new List<CosmeticItem>();
            selected = null;
            string equippedId = EquippedId(cat);
            foreach (var item in items)
            {
                if (item.id == equippedId) selected = item;
            }
            if (selected == null && items.Count > 0) selected = items[0];
            RebuildGrid(items);
            RefreshPreview();
        }

        void RebuildGrid(List<CosmeticItem> items)
        {
            for (int i = grid.childCount - 1; i >= 0; i--) Object.Destroy(grid.GetChild(i).gameObject);
            for (int i = 0; i < items.Count; i++) BuildCard(items[i], i);
        }

        void BuildCard(CosmeticItem item, int index)
        {
            bool owned = SaveSystem.Owns(item.id);
            bool equipped = EquippedId(item.category) == item.id;

            var button = UIKit.Button(grid, "Card_" + item.id, "", item == selected ? UITheme.Gold : UITheme.Paper, () => Select(item));
            var face = button.transform.Find("Face");
            UIKit.PopIn(button.gameObject, index * 0.02f);

            var strip = UIKit.Panel(face, "Rarity", UITheme.RarityColor(item.rarity), ProceduralSprites.RoundedSmall);
            UIKit.Place(strip.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -10f), new Vector2(200f, 14f), new Vector2(0.5f, 1f));
            strip.raycastTarget = false;

            var icon = UIKit.Icon(face, "Icon", CosmeticArt.Icon(item), Color.white, 150f);
            UIKit.Place(icon.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -36f), new Vector2(150f, 150f), new Vector2(0.5f, 1f));

            var name = UIKit.Label(face, "Name", item.displayName, 28, UITheme.Ink, TextAnchor.MiddleCenter, true);
            UIKit.Place(name.rectTransform, new Vector2(0.5f, 0f), new Vector2(0f, 72f), new Vector2(225f, 40f), new Vector2(0.5f, 0.5f));

            if (equipped || owned)
            {
                var status = UIKit.Label(face, "Status", equipped ? "Equipped" : "Owned", 28, equipped ? UITheme.Green : UITheme.InkSoft, TextAnchor.MiddleCenter, true);
                UIKit.Place(status.rectTransform, new Vector2(0.5f, 0f), new Vector2(0f, 32f), new Vector2(225f, 40f), new Vector2(0.5f, 0.5f));
            }
            else
            {
                bool affordable = SaveSystem.Data.coins >= item.price;
                var price = UIKit.CoinAmount(face, "Price", item.price, 30, affordable ? UITheme.Ink : UITheme.Red);
                UIKit.Place((RectTransform)price.transform.parent, new Vector2(0.5f, 0f), new Vector2(0f, 32f), new Vector2(200f, 40f), new Vector2(0.5f, 0.5f));
            }
        }

        void Select(CosmeticItem item)
        {
            selected = item;
            RebuildGrid(Controller.cosmetics.InCategory(category));
            RefreshPreview();
        }

        void RefreshPreview()
        {
            if (selected == null)
            {
                previewIcon.enabled = false;
                previewName.text = "";
                previewRarity.text = "";
                actionButton.gameObject.SetActive(false);
                previewPrice.gameObject.SetActive(false);
                return;
            }

            previewIcon.enabled = true;
            previewIcon.sprite = CosmeticArt.Icon(selected);
            previewName.text = selected.displayName;
            previewRarity.text = selected.rarity.ToString();
            previewRarity.color = UITheme.RarityColor(selected.rarity);

            bool owned = SaveSystem.Owns(selected.id);
            bool equipped = EquippedId(selected.category) == selected.id;
            previewPrice.gameObject.SetActive(!owned);
            previewPriceText.text = selected.price.ToString();
            actionButton.gameObject.SetActive(true);

            if (equipped)
            {
                actionLabel.text = "Equipped";
                actionButton.interactable = false;
                actionButton.targetGraphic.color = UITheme.Green;
            }
            else if (owned)
            {
                actionLabel.text = "Equip";
                actionButton.interactable = true;
                actionButton.targetGraphic.color = UITheme.Green;
            }
            else
            {
                bool affordable = SaveSystem.Data.coins >= selected.price;
                actionLabel.text = affordable ? "Buy" : "Need more coins";
                actionButton.interactable = affordable;
                actionButton.targetGraphic.color = affordable ? UITheme.Accent : UITheme.Locked;
            }
        }

        void OnAction()
        {
            if (selected == null) return;
            if (!SaveSystem.Owns(selected.id))
            {
                if (!SaveSystem.TrySpend(selected.price)) return;
                SaveSystem.Grant(selected.id);
                GameEvents.Raise(GameEventType.Purchase, Vector2.zero);
            }
            Equip(selected);
            SaveSystem.Save();
            Select(selected);
        }

        static void Equip(CosmeticItem item)
        {
            var d = SaveSystem.Data;
            switch (item.category)
            {
                case CosmeticCategory.Ball: d.equippedBall = item.id; break;
                case CosmeticCategory.Flag: d.equippedFlag = item.id; break;
                case CosmeticCategory.Outfit: d.equippedOutfit = item.id; break;
                case CosmeticCategory.Trail: d.equippedTrail = item.id; break;
            }
        }

        static string EquippedId(CosmeticCategory cat)
        {
            var d = SaveSystem.Data;
            switch (cat)
            {
                case CosmeticCategory.Ball: return d.equippedBall;
                case CosmeticCategory.Flag: return d.equippedFlag;
                case CosmeticCategory.Outfit: return d.equippedOutfit;
                default: return d.equippedTrail;
            }
        }
    }
}
