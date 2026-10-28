using System.Collections.Generic;
using System.IO;
using DribbleToSchool.Art;
using UnityEditor;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Bakes the procedural anime-style art (Art/ProceduralArt.cs) into sprite
    /// assets with the right import settings, so scenes reference real sprites
    /// and look right in the editor too.
    /// </summary>
    public static class ArtBaker
    {
        const string Dir = LevelBuildKit.Root + "/Art/Generated";

        public class ArtSet
        {
            public Sprite block, crate, groundFill, sun, puff, spark, drop, shadow, dog, seagull, car;
            public Sprite carFront, walkFigure, standFigure, waterJet, sideStreet, tideWater;
            public Sprite[] clouds = new Sprite[3];
            public Sprite[] edge = new Sprite[6];
            public Sprite[] sky = new Sprite[6];
            public Sprite[] far = new Sprite[6];
            public Sprite[] near = new Sprite[6];
            /// <summary>Utility-pole strip per chapter (null where the chapter has none).</summary>
            public Sprite[] poles = new Sprite[6];
            public Sprite[,] mid = new Sprite[6, 3];
            public readonly Dictionary<string, Sprite> parts = new Dictionary<string, Sprite>();

            // 3D street
            public Sprite pine, bush, headland;
            public readonly Dictionary<ProceduralArt.Surface, Material> surfaces = new Dictionary<ProceduralArt.Surface, Material>();
            public readonly Dictionary<ProceduralArt.FacadeKind, Material> facades = new Dictionary<ProceduralArt.FacadeKind, Material>();
            /// <summary>Plain toon material for tinted solids (walls, trims, obstacles).</summary>
            public Material solid;
            public Material crateMaterial;
            /// <summary>Sprite material with distance haze, for cut-outs placed in depth.</summary>
            public Material hazeSprite;
            public Material wire;
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
            for (int i = 0; i < 3; i++) Queue(pending, "Cloud" + i, ProceduralArt.Cloud(i * 17 + 3), new ImportSpec(48, 0));
            Queue(pending, "Poles", ProceduralArt.PoleLine(1), new ImportSpec(64, 0));
            Queue(pending, "Puff", ProceduralArt.Puff(), new ImportSpec(64, 0));
            Queue(pending, "Spark", ProceduralArt.Spark(), new ImportSpec(64, 0));
            Queue(pending, "Drop", ProceduralArt.Drop(), new ImportSpec(64, 0));
            Queue(pending, "Shadow", ProceduralArt.Shadow(), new ImportSpec(64, 0));
            Queue(pending, "Dog", ProceduralArt.Dog(), new ImportSpec(192, 0));
            Queue(pending, "Seagull", ProceduralArt.Seagull(), new ImportSpec(160, 0));
            Queue(pending, "Car", ProceduralArt.Car(), new ImportSpec(115, 0));
            Queue(pending, "CarFront", ProceduralArt.CarFront(), new ImportSpec(115, 0));
            Queue(pending, "SignalWalk", ProceduralArt.SignalFigure(true), new ImportSpec(160, 0));
            Queue(pending, "SignalStand", ProceduralArt.SignalFigure(false), new ImportSpec(160, 0));
            Queue(pending, "WaterJet", ProceduralArt.WaterJet(), new ImportSpec(64, 0));
            Queue(pending, "SideStreet", ProceduralArt.SideStreet(), new ImportSpec(64, 0));
            Queue(pending, "TideWater", ProceduralArt.TideWater(), new ImportSpec(64, 0));
            foreach (string part in PartNames) Queue(pending, "Part_" + part, ProceduralArt.Part(part), new ImportSpec(ProceduralArt.PartPpu(part), 0));
            Queue(pending, "Pine", ProceduralArt.Pine(), new ImportSpec(80, 0));
            Queue(pending, "Bush", ProceduralArt.Bush(), new ImportSpec(110, 0));
            Queue(pending, "Headland", ProceduralArt.Headland(), new ImportSpec(64, 0));
            foreach (ProceduralArt.Surface surface in System.Enum.GetValues(typeof(ProceduralArt.Surface)))
                Queue(pending, "Surface_" + surface, ProceduralArt.SurfaceTexture(surface), ImportSpec.Texture(true));
            foreach (ProceduralArt.FacadeKind kind in System.Enum.GetValues(typeof(ProceduralArt.FacadeKind)))
                Queue(pending, "Facade_" + kind, ProceduralArt.Facade(kind), ImportSpec.Texture(false));
            Queue(pending, "CrateFace", ProceduralArt.Crate(), ImportSpec.Texture(false));

            for (int ch = 1; ch <= 5; ch++)
            {
                var t = ChapterTheme.For(ch);
                Queue(pending, "Ch" + ch + "_Edge", ProceduralArt.GroundEdge(t.edge, t.groundEdge, t.groundFill), new ImportSpec(128, 0));
                Queue(pending, "Ch" + ch + "_Sky", ProceduralArt.Sky(t.skyTop, t.skyBottom), new ImportSpec(32, 0));
                Queue(pending, "Ch" + ch + "_Far", ProceduralArt.Far(t.scenery, t.far, ch * 7), new ImportSpec(40, 0));
                Queue(pending, "Ch" + ch + "_Near", ProceduralArt.Near(t.scenery, t.near, ch * 5), new ImportSpec(64, 0));
                for (int v = 0; v < 3; v++)
                    Queue(pending, "Ch" + ch + "_Mid" + v, ProceduralArt.MidProp(t.scenery, v, t.mid), new ImportSpec(80, 0));
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
            set.carFront = Load("CarFront");
            set.walkFigure = Load("SignalWalk");
            set.standFigure = Load("SignalStand");
            set.waterJet = Load("WaterJet");
            set.sideStreet = Load("SideStreet");
            set.tideWater = Load("TideWater");
            var poles = Load("Poles");
            foreach (string part in PartNames) set.parts[part] = Load("Part_" + part);
            set.pine = Load("Pine");
            set.bush = Load("Bush");
            set.headland = Load("Headland");
            BakeMaterials(set);
            for (int ch = 1; ch <= 5; ch++)
            {
                set.edge[ch] = Load("Ch" + ch + "_Edge");
                set.sky[ch] = Load("Ch" + ch + "_Sky");
                set.far[ch] = Load("Ch" + ch + "_Far");
                set.near[ch] = Load("Ch" + ch + "_Near");
                set.poles[ch] = HasPoles(ChapterTheme.For(ch).scenery) ? poles : null;
                for (int v = 0; v < 3; v++) set.mid[ch, v] = Load("Ch" + ch + "_Mid" + v);
            }
            return set;
        }

        static readonly string[] PartNames = ProceduralArt.PartNames;

        /// <summary>Streets with overhead power lines: the suburb, the market and the city.</summary>
        static bool HasPoles(SceneryStyle style)
        {
            return style == SceneryStyle.Houses || style == SceneryStyle.Market || style == SceneryStyle.City;
        }

        struct ImportSpec
        {
            public float ppu;
            public int border;
            /// <summary>Import as a plain texture (for 3D materials) rather than a sprite.</summary>
            public bool texture;
            public bool repeat;
            public ImportSpec(float ppu, int border) { this.ppu = ppu; this.border = border; texture = false; repeat = false; }
            public static ImportSpec Texture(bool repeat) { return new ImportSpec(100, 0) { texture = true, repeat = repeat }; }
        }

        const string MaterialDir = Dir + "/Materials";

        /// <summary>Toon materials for every surface and facade, plus the haze sprite and wire materials.</summary>
        static void BakeMaterials(ArtSet set)
        {
            LevelBuildKit.EnsureFolder(MaterialDir);
            var toon = Shader.Find("DribbleToSchool/Toon");
            foreach (ProceduralArt.Surface surface in System.Enum.GetValues(typeof(ProceduralArt.Surface)))
            {
                var m = ToonMaterial("Surface_" + surface, toon, LoadTexture("Surface_" + surface), true);
                if (surface == ProceduralArt.Surface.Sea) m.SetVector("_Scroll", new Vector4(0.02f, 0.01f, 0f, 0f));
                set.surfaces[surface] = m;
            }
            foreach (ProceduralArt.FacadeKind kind in System.Enum.GetValues(typeof(ProceduralArt.FacadeKind)))
                set.facades[kind] = ToonMaterial("Facade_" + kind, toon, LoadTexture("Facade_" + kind), false);
            set.solid = ToonMaterial("Solid", toon, null, false);
            set.crateMaterial = ToonMaterial("Crate", toon, LoadTexture("CrateFace"), false);

            set.hazeSprite = LoadOrCreateMaterial("HazeSprite", Shader.Find("DribbleToSchool/SpriteHaze"));
            set.wire = LoadOrCreateMaterial("Wire", Shader.Find("Sprites/Default"));
            AssetDatabase.SaveAssets();
        }

        static Material ToonMaterial(string name, Shader shader, Texture2D texture, bool worldUV)
        {
            var m = LoadOrCreateMaterial(name, shader);
            m.mainTexture = texture;
            m.SetFloat("_WorldUV", worldUV ? 1f : 0f);
            m.SetFloat("_WorldUVScale", 0.25f);   // surface textures cover 4 x 4 units
            EditorUtility.SetDirty(m);
            return m;
        }

        static Material LoadOrCreateMaterial(string name, Shader shader)
        {
            string path = MaterialDir + "/" + name + ".mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null)
            {
                m = new Material(shader != null ? shader : Shader.Find("Sprites/Default"));
                AssetDatabase.CreateAsset(m, path);
            }
            else if (shader != null && m.shader != shader)
            {
                m.shader = shader;
            }
            return m;
        }

        static Texture2D LoadTexture(string name)
        {
            return AssetDatabase.LoadAssetAtPath<Texture2D>(PathFor(name));
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
            if (spec.texture)
            {
                importer.textureType = TextureImporterType.Default;
                importer.mipmapEnabled = true;
                importer.wrapMode = spec.repeat ? TextureWrapMode.Repeat : TextureWrapMode.Clamp;
                importer.filterMode = FilterMode.Trilinear;
                importer.anisoLevel = 4;
                importer.textureCompression = TextureImporterCompression.CompressedHQ;
                importer.SaveAndReimport();
                return;
            }
            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Single;
            importer.spritePixelsPerUnit = spec.ppu;
            // Character parts are drawn at 4x their on-screen size; mipmaps keep them from shimmering.
            importer.mipmapEnabled = spec.ppu >= 256f;
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
