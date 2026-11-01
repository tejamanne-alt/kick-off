using System.Collections.Generic;
using DribbleToSchool.Core;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.UI;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>
    /// The Locker Room: on the left, the live teen in the street showcase wearing (or juggling)
    /// the selected item, a button to switch player, and a card with the item's name, rarity,
    /// price and Buy / Equip; on the right, tabs for balls, flags, outfits and trails over a
    /// grid of items on a white panel.
    /// </summary>
    public class ShopScreen : FrontEndScreen
    {
        static readonly CosmeticCategory[] Categories =
            { CosmeticCategory.Ball, CosmeticCategory.Flag, CosmeticCategory.Outfit, CosmeticCategory.Trail };
        static readonly string[] CategoryKeys = { "shop.balls", "shop.flags", "shop.outfits", "shop.trails" };

        /// <summary>Width of the left column (showcase and item card), canvas pixels.</summary>
        const float Column = 600f;
        /// <summary>Height of the item card at the bottom of the left column.</summary>
        const float CardHeight = 330f;

        CosmeticCategory category = CosmeticCategory.Ball;
        CosmeticItem selected;

        readonly List<Button> tabButtons = new List<Button>();
        RectTransform grid;
        RectTransform showcase;
        Image previewIcon;
        Text previewName;
        Text previewRarity;
        Button actionButton;
        Text actionLabel;
        RectTransform previewPrice;
        Text previewPriceText;

        public override string Title { get { return Loc.T("menu.locker"); } }

        protected override void Build(RectTransform root)
        {
            // Showcase: an open window onto the street where the 3D teen stands (see FrameStage),
            // the right half of the column above the item card, clear of the player button.
            showcase = UIKit.Rect(root, "Showcase");
            showcase.anchorMin = new Vector2(0f, 0f);
            showcase.anchorMax = new Vector2(0f, 1f);
            showcase.pivot = new Vector2(0f, 0.5f);
            showcase.offsetMin = new Vector2(40f + Column * 0.5f, 40f + CardHeight + 20f);
            showcase.offsetMax = new Vector2(40f + Column, -175f);
            var change = UIKit.Button(root, "Player", Loc.T("player.change"), UITheme.Paper, () => PlayerPicker.Open(Controller.CanvasRoot), 30, UITheme.Navy);
            UIKit.Place((RectTransform)change.transform, new Vector2(0f, 1f), new Vector2(40f, -170f), new Vector2(280f, 72f), new Vector2(0f, 1f));

            // The selected item's card under the showcase.
            var info = UIKit.Card(root, "Item", UITheme.Paper);
            var infoRoot = (RectTransform)info.transform.parent;
            infoRoot.anchorMin = infoRoot.anchorMax = Vector2.zero;
            infoRoot.pivot = Vector2.zero;
            infoRoot.anchoredPosition = new Vector2(40f, 40f);
            infoRoot.sizeDelta = new Vector2(Column, CardHeight);

            // Top: the icon on a disc of sky, name, rarity and price beside it; bottom: Buy / Equip.
            var iconBack = UIKit.Icon(info.transform, "IconBack", ProceduralSprites.CircleEdge, UITheme.SkyBottom, 160f);
            UIKit.Place(iconBack.rectTransform, new Vector2(0f, 1f), new Vector2(26f, -22f), new Vector2(160f, 160f), new Vector2(0f, 1f));
            previewIcon = UIKit.Icon(iconBack.transform, "Icon", null, Color.white, 124f);
            UIKit.Place(previewIcon.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(124f, 124f));
            previewIcon.gameObject.AddComponent<UIPulse>().amount = 0.03f;

            previewName = UIKit.Label(info.transform, "Name", "", 46, UITheme.Ink, TextAnchor.MiddleLeft, true);
            UIKit.Place(previewName.rectTransform, new Vector2(0f, 1f), new Vector2(210f, -56f), new Vector2(Column - 236f, 64f), new Vector2(0f, 0.5f));
            UIKit.Fit(previewName, 28);
            previewRarity = UIKit.Label(info.transform, "Rarity", "", 30, UITheme.InkSoft, TextAnchor.MiddleLeft, true);
            UIKit.Place(previewRarity.rectTransform, new Vector2(0f, 1f), new Vector2(210f, -102f), new Vector2(Column - 236f, 44f), new Vector2(0f, 0.5f));

            previewPriceText = UIKit.CoinAmount(info.transform, "Price", 0, 42, UITheme.Ink);
            previewPrice = (RectTransform)previewPriceText.transform.parent;
            UIKit.Place(previewPrice, new Vector2(0f, 1f), new Vector2(210f, -148f), new Vector2(220f, 52f), new Vector2(0f, 0.5f));
            previewPrice.GetComponent<HorizontalLayoutGroup>().childAlignment = TextAnchor.MiddleLeft;

            actionButton = UIKit.Button(info.transform, "Action", "Equip", UITheme.Green, OnAction, 44);
            UIKit.Place((RectTransform)actionButton.transform, new Vector2(0.5f, 0f), new Vector2(0f, 30f), new Vector2(Column - 60f, 90f), new Vector2(0.5f, 0f));
            actionLabel = actionButton.GetComponentInChildren<Text>();

            // Right: tabs and the item grid on a white panel.
            var panel = UIKit.Card(root, "Items", new Color(1f, 1f, 1f, 0.9f));
            var panelRoot = (RectTransform)panel.transform.parent;
            panelRoot.anchorMin = Vector2.zero;
            panelRoot.anchorMax = Vector2.one;
            panelRoot.offsetMin = new Vector2(Column + 80f, 40f);
            panelRoot.offsetMax = new Vector2(-40f, -175f);

            var tabRow = UIKit.Row(panel.transform, "Tabs", 22f, 84f, 22f, 22f);
            for (int i = 0; i < Categories.Length; i++)
            {
                var cat = Categories[i];
                var tab = UIKit.Button(tabRow, "Tab" + cat, Loc.T(CategoryKeys[i]), UITheme.Paper, () => SelectCategory(cat), 32, UITheme.Navy);
                var rt = (RectTransform)tab.transform;
                rt.anchorMin = new Vector2(i / (float)Categories.Length, 0f);
                rt.anchorMax = new Vector2((i + 1) / (float)Categories.Length, 1f);
                rt.offsetMin = new Vector2(i == 0 ? 0f : 8f, UIButtonFx.Depth);
                rt.offsetMax = new Vector2(i == Categories.Length - 1 ? 0f : -8f, 0f);
                tabButtons.Add(tab);
            }

            ScrollRect scroll;
            grid = UIKit.ScrollArea(panel.transform, "Grid", true, out scroll);
            var gridRoot = (RectTransform)scroll.transform;
            gridRoot.anchorMin = new Vector2(0f, 0f);
            gridRoot.anchorMax = new Vector2(1f, 1f);
            gridRoot.offsetMin = new Vector2(16f, 12f);
            gridRoot.offsetMax = new Vector2(-16f, -126f);
            var layout = grid.gameObject.AddComponent<GridLayoutGroup>();
            layout.cellSize = new Vector2(232f, 280f);
            layout.spacing = new Vector2(22f, 26f);
            layout.padding = new RectOffset(10, 10, 14, 30);
            layout.childAlignment = TextAnchor.UpperCenter;
            var fitter = grid.gameObject.AddComponent<ContentSizeFitter>();
            fitter.verticalFit = ContentSizeFitter.FitMode.PreferredSize;
        }

        public override void OnShow()
        {
            SelectCategory(category);
        }

        public override void OnHide()
        {
            if (Controller.Stage != null) Controller.Stage.ResetLook();
        }

        public override void FrameStage(MenuStage stage)
        {
            stage.Frame(MenuShot.Locker, ViewportRect(showcase));
        }

        void SelectCategory(CosmeticCategory cat)
        {
            category = cat;
            for (int i = 0; i < tabButtons.Count; i++)
            {
                bool on = Categories[i] == cat;
                tabButtons[i].targetGraphic.color = on ? UITheme.Navy : UITheme.Paper;
                tabButtons[i].GetComponentInChildren<Text>().color = on ? Color.white : UITheme.Navy;
            }

            var items = Controller.cosmetics != null ? Controller.cosmetics.InCategory(cat) : new List<CosmeticItem>();
            selected = null;
            string equippedId = EquippedId(cat);
            foreach (var item in items)
            {
                if (item.id == equippedId) selected = item;
            }
            if (selected == null && items.Count > 0) selected = items[0];
            if (Controller.Stage != null) Controller.Stage.ResetLook();
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

            var strip = UIKit.Panel(face, "Rarity", UITheme.RarityColor(item.rarity), ProceduralSprites.RoundedEdgeSmall);
            UIKit.Place(strip.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -12f), new Vector2(180f, 14f), new Vector2(0.5f, 1f));
            strip.raycastTarget = false;

            var icon = UIKit.Icon(face, "Icon", CosmeticArt.Icon(item), Color.white, 140f);
            UIKit.Place(icon.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -36f), new Vector2(140f, 140f), new Vector2(0.5f, 1f));

            var name = UIKit.Label(face, "Name", item.displayName, 28, UITheme.Ink, TextAnchor.MiddleCenter, true);
            UIKit.Place(name.rectTransform, new Vector2(0.5f, 0f), new Vector2(0f, 76f), new Vector2(214f, 40f), new Vector2(0.5f, 0.5f));
            UIKit.Fit(name, 20);

            if (equipped || owned)
            {
                var status = UIKit.Label(face, "Status", Loc.T(equipped ? "shop.equipped" : "shop.owned"), 28, equipped ? UITheme.Green : UITheme.InkSoft, TextAnchor.MiddleCenter, true);
                UIKit.Place(status.rectTransform, new Vector2(0.5f, 0f), new Vector2(0f, 34f), new Vector2(214f, 40f), new Vector2(0.5f, 0.5f));
                UIKit.Fit(status, 20);
            }
            else
            {
                bool affordable = SaveSystem.Data.coins >= item.price;
                var price = UIKit.CoinAmount(face, "Price", item.price, 30, affordable ? UITheme.Ink : UITheme.Red);
                UIKit.Place((RectTransform)price.transform.parent, new Vector2(0.5f, 0f), new Vector2(0f, 34f), new Vector2(200f, 40f), new Vector2(0.5f, 0.5f));
            }
        }

        void Select(CosmeticItem item)
        {
            selected = item;
            RebuildGrid(Controller.cosmetics.InCategory(category));
            RefreshPreview();
            // Try it on the teen (outfits, flags) or the ball they juggle.
            if (Controller.Stage != null)
            {
                Controller.Stage.ResetLook();
                Controller.Stage.TryOn(item);
            }
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
            previewRarity.text = Loc.T("rarity." + selected.rarity);
            previewRarity.color = UITheme.RarityColor(selected.rarity);

            bool owned = SaveSystem.Owns(selected.id);
            bool equipped = EquippedId(selected.category) == selected.id;
            previewPrice.gameObject.SetActive(!owned);
            previewPriceText.text = selected.price.ToString();
            actionButton.gameObject.SetActive(true);

            if (equipped)
            {
                actionLabel.text = Loc.T("shop.equipped");
                actionButton.interactable = false;
                actionButton.targetGraphic.color = UITheme.Green;
            }
            else if (owned)
            {
                actionLabel.text = Loc.T("shop.equip");
                actionButton.interactable = true;
                actionButton.targetGraphic.color = UITheme.Green;
            }
            else
            {
                bool affordable = SaveSystem.Data.coins >= selected.price;
                actionLabel.text = Loc.T(affordable ? "shop.buy" : "shop.needCoins");
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
