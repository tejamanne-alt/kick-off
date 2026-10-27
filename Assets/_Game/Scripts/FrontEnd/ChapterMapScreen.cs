using System.Collections.Generic;
using DribbleToSchool.Levels;
using DribbleToSchool.Progression;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>
    /// The chapter map: a winding path of level nodes with stars and locks,
    /// chapter tabs along the bottom, and the next level gently pulsing.
    /// </summary>
    public class ChapterMapScreen : FrontEndScreen
    {
        RectTransform pathLayer;
        Text chapterTitle;
        Text chapterStars;
        readonly List<Button> tabs = new List<Button>();

        public override string Title { get { return "Way to School"; } }

        protected override void Build(RectTransform root)
        {
            chapterTitle = UIKit.Title(root, "ChapterTitle", "", 60, Color.white);
            UIKit.Place(chapterTitle.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -200f), new Vector2(1400f, 90f));
            chapterStars = UIKit.Label(root, "ChapterStars", "", UITheme.SizeBody, UITheme.Ink, TextAnchor.MiddleCenter, true);
            UIKit.Place(chapterStars.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -265f), new Vector2(800f, 50f));

            pathLayer = UIKit.Rect(root, "Path");
            pathLayer.anchorMin = new Vector2(0f, 0.2f);
            pathLayer.anchorMax = new Vector2(1f, 0.72f);
            pathLayer.offsetMin = new Vector2(80f, 0f);
            pathLayer.offsetMax = new Vector2(-80f, 0f);

            var tabRow = UIKit.Rect(root, "Tabs");
            tabRow.anchorMin = new Vector2(0.5f, 0f);
            tabRow.anchorMax = new Vector2(0.5f, 0f);
            tabRow.pivot = new Vector2(0.5f, 0f);
            tabRow.anchoredPosition = new Vector2(0f, 40f);
            var catalog = Controller.levels;
            int count = catalog != null ? catalog.chapters.Count : 0;
            tabRow.sizeDelta = new Vector2(count * 330f, 110f);
            for (int i = 0; i < count; i++)
            {
                var info = catalog.chapters[i];
                int number = info.number;
                var tab = UIKit.Button(tabRow, "Tab" + number, number + "  " + info.title, info.color, () => ShowChapter(number), 30);
                UIKit.Place((RectTransform)tab.transform, new Vector2(0f, 0.5f), new Vector2(i * 330f, 0f), new Vector2(310f, 96f), new Vector2(0f, 0.5f));
                tabs.Add(tab);
            }
        }

        public override void OnShow()
        {
            int requested = FrontEndController.RequestedChapter;
            FrontEndController.RequestedChapter = 0;
            if (requested <= 0)
            {
                var next = Controller.levels != null ? LevelUnlocks.NextToPlay(Controller.levels) : null;
                requested = next != null ? next.chapter : 1;
            }
            ShowChapter(requested);
        }

        void ShowChapter(int number)
        {
            var catalog = Controller.levels;
            for (int i = pathLayer.childCount - 1; i >= 0; i--) Object.Destroy(pathLayer.GetChild(i).gameObject);

            var info = catalog.Chapter(number);
            var levels = catalog.LevelsInChapter(number);
            chapterTitle.text = info != null ? "Chapter " + number + ": " + info.title : "Chapter " + number;
            chapterStars.text = levels.Count > 0
                ? "Stars " + LevelUnlocks.StarsInChapter(catalog, number) + " / " + levels.Count * 3
                : "";

            // Selected tab in full colour, others washed out (the press animation owns their scale).
            for (int i = 0; i < tabs.Count; i++)
            {
                Color c = catalog.chapters[i].color;
                tabs[i].targetGraphic.color = catalog.chapters[i].number == number ? c : Color.Lerp(c, Color.white, 0.55f);
            }

            if (levels.Count == 0)
            {
                var soon = UIKit.Title(pathLayer, "ComingSoon", "Coming soon!", 72, Color.white);
                UIKit.Stretch(soon.rectTransform);
                return;
            }

            Color chapterColor = info != null ? info.color : UITheme.Accent;
            var next = LevelUnlocks.NextToPlay(catalog);
            var positions = new List<Vector2>();
            // Story levels wind along the path; challenges sit beside it, top right.
            var story = levels.FindAll(l => !l.isChallenge);
            var challenges = levels.FindAll(l => l.isChallenge);
            for (int i = 0; i < story.Count; i++)
            {
                float x = story.Count == 1 ? 0.4f : Mathf.Lerp(0.06f, challenges.Count > 0 ? 0.8f : 0.94f, i / (float)(story.Count - 1));
                float y = 0.5f + Mathf.Sin(i * 1.35f + number) * 0.28f;
                positions.Add(new Vector2(x, y));
            }
            for (int i = 0; i < challenges.Count; i++)
                positions.Add(new Vector2(0.95f, 0.85f - i * 0.4f));
            levels = new List<LevelDefinition>(story);
            levels.AddRange(challenges);

            // Dotted path between story nodes, drawn first so nodes sit on top.
            for (int i = 0; i + 1 < story.Count; i++)
            {
                for (int d = 1; d < 6; d++)
                {
                    Vector2 p = Vector2.Lerp(positions[i], positions[i + 1], d / 6f);
                    var dot = UIKit.Icon(pathLayer, "Dot", ProceduralSprites.Circle, new Color(1f, 1f, 1f, 0.85f), 22f);
                    UIKit.Place(dot.rectTransform, p, Vector2.zero, new Vector2(22f, 22f), new Vector2(0.5f, 0.5f));
                }
            }

            for (int i = 0; i < levels.Count; i++)
                BuildNode(levels[i], positions[i], chapterColor, levels[i] == next, i);
        }

        void BuildNode(LevelDefinition def, Vector2 anchor, Color color, bool isNext, int index)
        {
            var catalog = Controller.levels;
            bool unlocked = LevelUnlocks.IsUnlocked(catalog, def);
            int stars = SaveSystem.StarsFor(def.levelId);

            var holder = UIKit.Rect(pathLayer, "Node_" + def.levelId);
            UIKit.Place(holder, anchor, Vector2.zero, new Vector2(170f, 170f), new Vector2(0.5f, 0.5f));
            UIKit.PopIn(holder.gameObject, index * 0.05f);
            if (isNext && unlocked) holder.gameObject.AddComponent<UIPulse>();

            var inner = UIKit.Rect(holder, "Inner");
            UIKit.Stretch(inner);
            Color face = def.isChallenge ? UITheme.Gold : color;
            var button = UIKit.Button(inner, "Button", "", unlocked ? face : UITheme.Locked, () => Controller.PlayLevel(def));
            UIKit.Stretch((RectTransform)button.transform);
            button.interactable = unlocked;
            // Round buttons: swap the rounded-rect faces for circles.
            foreach (var img in button.GetComponentsInChildren<Image>())
            {
                if (img.name == "Face" || img.name == "Shadow") { img.sprite = ProceduralSprites.Circle; img.type = Image.Type.Simple; }
                if (img.name == "Shine") img.gameObject.SetActive(false);
            }

            if (unlocked)
            {
                string number = def.isChallenge ? "!" : def.levelId.TrimStart('L').TrimStart('0');
                var label = UIKit.Title(button.transform.Find("Face"), "Number", number, 72, Color.white);
                UIKit.Stretch(label.rectTransform);
            }
            else
            {
                var lockIcon = UIKit.Icon(button.transform.Find("Face"), "Lock", ProceduralSprites.Lock, new Color(1f, 1f, 1f, 0.9f), 80f);
                UIKit.Place(lockIcon.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(80f, 80f));
            }

            var starRow = UIKit.Stars(holder, "Stars", stars, 44f);
            UIKit.Place(starRow, new Vector2(0.5f, 0f), new Vector2(0f, -36f), starRow.sizeDelta, new Vector2(0.5f, 0.5f));

            var name = UIKit.Label(holder, "Name", def.displayName, 30, UITheme.Ink, TextAnchor.MiddleCenter, true);
            UIKit.Place(name.rectTransform, new Vector2(0.5f, 0f), new Vector2(0f, -86f), new Vector2(320f, 44f), new Vector2(0.5f, 0.5f));
        }
    }
}
