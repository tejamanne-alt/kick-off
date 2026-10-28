using System.Collections.Generic;
using System.IO;
using DribbleToSchool.Art;
using UnityEditor;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Bakes the procedural storybook art (Art/ProceduralArt.cs) into sprite
    /// assets with the right import settings, so scenes reference real sprites
    /// and look right in the editor too.
    /// </summary>
    public static class ArtBaker
    {
        const string Dir = LevelBuildKit.Root + "/Art/Generated";

        public class ArtSet
        {
            public Sprite block, crate, groundFill, sun, puff, spark, drop, shadow, dog, seagull, car;
            public Sprite[] clouds = new Sprite[3];
            public Sprite[] edge = new Sprite[6];
            public Sprite[] sky = new Sprite[6];
            public Sprite[] far = new Sprite[6];
            public Sprite[] near = new Sprite[6];
            public Sprite[,] mid = new Sprite[6, 3];
            public readonly Dictionary<string, Sprite> parts = new Dictionary<string, Sprite>();
        }

        public static ArtSet BakeAll()
        {
            LevelBuildKit.EnsureFolder(Dir);
            var set = new ArtSet();
            var pending = new List<KeyValuePair<string, ImportSpec>>();

            Queue(pending, "Block", ProceduralArt.Block(), new ImportSpec(128, 12));
            Queue(pending, "Crate", ProceduralArt.Crate(), new ImportSpec(128, 14));
            Queue(pending, "GroundFill", ProceduralArt.GroundFill(), new ImportSpec(128, 0));
            Queue(pending, "Sun", ProceduralArt.Sun(new Color(1f, 0.93f, 0.65f)), new ImportSpec(64, 0));
            for (int i = 0; i < 3; i++) Queue(pending, "Cloud" + i, ProceduralArt.Cloud(i * 17 + 3), new ImportSpec(64, 0));
            Queue(pending, "Puff", ProceduralArt.Puff(), new ImportSpec(64, 0));
            Queue(pending, "Spark", ProceduralArt.Spark(), new ImportSpec(64, 0));
            Queue(pending, "Drop", ProceduralArt.Drop(), new ImportSpec(64, 0));
            Queue(pending, "Shadow", ProceduralArt.Shadow(), new ImportSpec(64, 0));
            Queue(pending, "Dog", ProceduralArt.Dog(), new ImportSpec(192, 0));
            Queue(pending, "Seagull", ProceduralArt.Seagull(), new ImportSpec(160, 0));
            Queue(pending, "Car", ProceduralArt.Car(), new ImportSpec(110, 0));
            foreach (string part in PartNames) Queue(pending, "Part_" + part, ProceduralArt.Part(part), new ImportSpec(256, 0));

            for (int ch = 1; ch <= 5; ch++)
            {
                var t = ChapterTheme.For(ch);
                Queue(pending, "Ch" + ch + "_Edge", ProceduralArt.GroundEdge(t.edge, t.groundEdge, t.groundFill), new ImportSpec(128, 0));
                Queue(pending, "Ch" + ch + "_Sky", ProceduralArt.Sky(t.skyTop, t.skyBottom), new ImportSpec(32, 0));
                Queue(pending, "Ch" + ch + "_Far", ProceduralArt.Far(t.scenery, t.far, ch * 7), new ImportSpec(40, 0));
                Queue(pending, "Ch" + ch + "_Near", ProceduralArt.Near(t.scenery, t.near, ch * 5), new ImportSpec(64, 0));
                for (int v = 0; v < 3; v++)
                    Queue(pending, "Ch" + ch + "_Mid" + v, ProceduralArt.MidProp(t.scenery, v, t.mid), new ImportSpec(64, 0));
            }

            // Import everything in one batch, then apply settings.
            AssetDatabase.StartAssetEditing();
            try
            {
                foreach (var kv in pending) AssetDatabase.ImportAsset(kv.Key, ImportAssetOptions.ForceSynchronousImport);
            }
            finally
            {
                AssetDatabase.StopAssetEditing();
            }
            foreach (var kv in pending) ApplySettings(kv.Key, kv.Value);

            set.block = Load("Block");
            set.crate = Load("Crate");
            set.groundFill = Load("GroundFill");
            set.sun = Load("Sun");
            for (int i = 0; i < 3; i++) set.clouds[i] = Load("Cloud" + i);
            set.puff = Load("Puff");
            set.spark = Load("Spark");
            set.drop = Load("Drop");
            set.shadow = Load("Shadow");
            set.dog = Load("Dog");
            set.seagull = Load("Seagull");
            set.car = Load("Car");
            foreach (string part in PartNames) set.parts[part] = Load("Part_" + part);
            for (int ch = 1; ch <= 5; ch++)
            {
                set.edge[ch] = Load("Ch" + ch + "_Edge");
                set.sky[ch] = Load("Ch" + ch + "_Sky");
                set.far[ch] = Load("Ch" + ch + "_Far");
                set.near[ch] = Load("Ch" + ch + "_Near");
                for (int v = 0; v < 3; v++) set.mid[ch, v] = Load("Ch" + ch + "_Mid" + v);
            }
            return set;
        }

        static readonly string[] PartNames = { "Head", "Hair", "Eye", "Torso", "Shorts", "Thigh", "Shin", "UpperArm", "Forearm", "Sleeve", "Backpack" };

        struct ImportSpec
        {
            public float ppu;
            public int border;
            public ImportSpec(float ppu, int border) { this.ppu = ppu; this.border = border; }
        }

        static string PathFor(string name) { return Dir + "/" + name + ".png"; }

        static void Queue(List<KeyValuePair<string, ImportSpec>> pending, string name, PixelCanvas canvas, ImportSpec spec)
        {
            string path = PathFor(name);
            string full = Path.Combine(Directory.GetParent(Application.dataPath).FullName, path);
            File.WriteAllBytes(full, canvas.ToPng());
            pending.Add(new KeyValuePair<string, ImportSpec>(path, spec));
        }

        static void ApplySettings(string path, ImportSpec spec)
        {
            var importer = AssetImporter.GetAtPath(path) as TextureImporter;
            if (importer == null) return;
            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Single;
            importer.spritePixelsPerUnit = spec.ppu;
            importer.mipmapEnabled = false;
            importer.alphaIsTransparency = true;
            importer.filterMode = FilterMode.Bilinear;
            importer.wrapMode = TextureWrapMode.Clamp;
            importer.textureCompression = TextureImporterCompression.CompressedHQ;
            importer.spriteBorder = new Vector4(spec.border, spec.border, spec.border, spec.border);

            var settings = new TextureImporterSettings();
            importer.ReadTextureSettings(settings);
            // Full-rect meshes are required for sliced and tiled drawing.
            settings.spriteMeshType = SpriteMeshType.FullRect;
            importer.SetTextureSettings(settings);
            importer.SaveAndReimport();
        }

        static Sprite Load(string name)
        {
            return AssetDatabase.LoadAssetAtPath<Sprite>(PathFor(name));
        }
    }
}
