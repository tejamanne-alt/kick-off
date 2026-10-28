using UnityEngine;

namespace DribbleToSchool.Art
{
    /// <summary>
    /// Textures for the 3D street. Surfaces are tileable 256 x 256 squares covering 4 x 4 world
    /// units (64 px per unit, 0.9 m per unit), projected in world space by the toon shader.
    /// Facades are drawn at 40 px per unit to the exact size of the building face they cover.
    /// </summary>
    public static partial class ProceduralArt
    {
        public enum Surface { Asphalt, Paving, Kerb, Cobbles, Sand, Gravel, Grass, Concrete, BlockWall, RoofTiles, Sea, Hoarding }

        public enum FacadeKind { HouseGable, HouseLong, Bungalow, Shop0, Shop1, Apartment, School, Warehouse }

        /// <summary>World size (units) of each facade texture: width x height of the wall it covers.</summary>
        public static Vector2 FacadeSize(FacadeKind kind)
        {
            switch (kind)
            {
                case FacadeKind.HouseGable: return new Vector2(7f, 6f);
                case FacadeKind.HouseLong: return new Vector2(10f, 5.6f);
                case FacadeKind.Bungalow: return new Vector2(7f, 3.4f);
                case FacadeKind.Shop0:
                case FacadeKind.Shop1: return new Vector2(8f, 7.4f);
                case FacadeKind.Apartment: return new Vector2(12f, 14f);
                case FacadeKind.School: return new Vector2(32f, 10f);
                default: return new Vector2(11f, 5.6f);
            }
        }

        const float FacadePpu = 40f;

        // ---------------------------------------------------------------- surfaces

        public static PixelCanvas SurfaceTexture(Surface surface)
        {
            const int w = 256;
            var c = new PixelCanvas(w, w);
            var rng = new System.Random((int)surface * 97 + 5);
            switch (surface)
            {
                case Surface.Asphalt:
                    c.Clear(new Color(0.53f, 0.53f, 0.57f));
                    Speckle(c, rng, 900, 1.2f, new Color(0.42f, 0.42f, 0.46f), new Color(0.62f, 0.62f, 0.66f));
                    for (int i = 0; i < 3; i++)   // hairline cracks
                    {
                        float x = Rand(rng, 0f, w), y = Rand(rng, 0f, w);
                        for (int k = 0; k < 5; k++)
                        {
                            float nx = x + Rand(rng, -26f, 26f), ny = y + Rand(rng, -14f, 14f);
                            float ax = x, ay = y;
                            c.Wrapped(o => c.Line(new Vector2(ax + o, ay), new Vector2(nx + o, ny), 1.3f, new Color(0.36f, 0.36f, 0.4f)));
                            x = nx; y = ny;
                        }
                    }
                    break;
                case Surface.Paving:
                    Slabs(c, rng, 64, 64, new Color(0.82f, 0.8f, 0.76f), new Color(0.66f, 0.64f, 0.62f), 0.05f);
                    break;
                case Surface.Kerb:
                    Slabs(c, rng, 64, 256, new Color(0.88f, 0.88f, 0.86f), new Color(0.7f, 0.7f, 0.7f), 0.03f);
                    break;
                case Surface.Concrete:
                    c.Clear(new Color(0.78f, 0.78f, 0.76f));
                    Speckle(c, rng, 500, 1.4f, new Color(0.7f, 0.7f, 0.69f), new Color(0.84f, 0.84f, 0.82f));
                    c.FillRect(0, 0, w, 2, new Color(0.66f, 0.66f, 0.65f));
                    c.FillRect(0, 0, 2, w, new Color(0.66f, 0.66f, 0.65f));
                    break;
                case Surface.Cobbles:
                    c.Clear(new Color(0.5f, 0.46f, 0.43f));
                    for (int row = 0; row < 16; row++)
                        for (int col = 0; col < 16; col++)
                        {
                            float x = col * 16f + (row % 2) * 8f, y = row * 16f;
                            Color stone = Color.Lerp(new Color(0.66f, 0.6f, 0.55f), new Color(0.78f, 0.72f, 0.66f), (float)rng.NextDouble());
                            c.Wrapped(o => c.FillRoundRect(x + o + 1.5f, y + 1.5f, x + o + 14.5f, y + 14.5f, 5f, stone));
                        }
                    break;
                case Surface.Sand:
                    c.Clear(new Color(0.93f, 0.84f, 0.64f));
                    Speckle(c, rng, 1400, 1f, new Color(0.84f, 0.74f, 0.55f), new Color(0.98f, 0.92f, 0.78f));
                    for (int i = 0; i < 9; i++)   // wind ripples
                    {
                        float y = i * 28f + Rand(rng, 0f, 10f);
                        c.Fill((x, yy) => Mathf.Abs(yy - (y + Mathf.Sin(x / w * Mathf.PI * 4f) * 4f)) < 1.2f ? 0.6f : 0f, new Color(0.84f, 0.74f, 0.56f));
                    }
                    break;
                case Surface.Gravel:
                    c.Clear(new Color(0.8f, 0.72f, 0.6f));
                    Speckle(c, rng, 1600, 1.6f, new Color(0.66f, 0.6f, 0.52f), new Color(0.9f, 0.84f, 0.74f));
                    break;
                case Surface.Grass:
                    c.Clear(new Color(0.42f, 0.66f, 0.34f));
                    for (int i = 0; i < 900; i++)
                    {
                        float x = Rand(rng, 0f, w), y = Rand(rng, 0f, w), lx = Rand(rng, -3f, 3f);
                        Color g = Color.Lerp(new Color(0.3f, 0.54f, 0.28f), new Color(0.55f, 0.78f, 0.4f), (float)rng.NextDouble());
                        c.Wrapped(o => c.Line(new Vector2(x + o, y), new Vector2(x + o + lx, y + 5f), 1.5f, g));
                    }
                    break;
                case Surface.BlockWall:
                    // Concrete blocks 0.8 x 0.4 units in stretcher bond.
                    c.Clear(new Color(0.6f, 0.6f, 0.58f));
                    for (int row = 0; row < 10; row++)
                        for (int col = 0; col < 6; col++)
                        {
                            float bw = 256f / 5f, bh = 25.6f;
                            float x = col * bw + (row % 2) * bw * 0.5f, y = row * bh;
                            Color block = Color.Lerp(new Color(0.7f, 0.7f, 0.68f), new Color(0.78f, 0.78f, 0.75f), (float)rng.NextDouble());
                            c.Wrapped(o => c.FillRect(x + o + 1.5f, y + 1.5f, x + o + bw - 1.5f, y + bh - 1.5f, block));
                        }
                    break;
                case Surface.RoofTiles:
                    c.Clear(new Color(0.3f, 0.33f, 0.4f));
                    for (int row = 0; row < 16; row++)
                    {
                        float y = row * 16f;
                        c.FillRect(0, y, w, y + 3f, new Color(0.24f, 0.27f, 0.33f));
                        c.FillRect(0, y + 3f, w, y + 5f, new Color(0.4f, 0.43f, 0.5f));
                        for (int k = 0; k < 8; k++)
                        {
                            float x = k * 32f + (row % 2) * 16f;
                            c.Wrapped(o => c.FillRect(x + o, y + 3f, x + o + 1.5f, y + 16f, new Color(0.26f, 0.29f, 0.35f)));
                        }
                    }
                    break;
                case Surface.Sea:
                    c.Clear(new Color(0.2f, 0.52f, 0.8f));
                    for (int i = 0; i < 120; i++)
                    {
                        float x = Rand(rng, 0f, w), y = Rand(rng, 0f, w), len = Rand(rng, 6f, 30f);
                        Color crest = new Color(0.85f, 0.95f, 1f, Rand(rng, 0.5f, 0.95f));
                        c.Wrapped(o => c.Line(new Vector2(x + o, y), new Vector2(x + o + len, y + 1f), 2f, crest));
                    }
                    break;
                case Surface.Hoarding:
                    // White site hoarding panels with a green band.
                    c.Clear(new Color(0.92f, 0.93f, 0.92f));
                    c.FillRect(0, 150, w, 166, new Color(0.3f, 0.6f, 0.4f));
                    c.FillRect(0, 174, w, 180, new Color(0.3f, 0.6f, 0.4f));
                    for (int i = 0; i < 4; i++) c.FillRect(i * 64f, 0, i * 64f + 3f, w, new Color(0.78f, 0.79f, 0.8f));
                    break;
            }
            return c;
        }

        static void Speckle(PixelCanvas c, System.Random rng, int count, float size, Color dark, Color light)
        {
            for (int i = 0; i < count; i++)
            {
                float x = Rand(rng, 0f, c.Width), y = Rand(rng, 0f, c.Height);
                Color col = rng.NextDouble() < 0.5 ? dark : light;
                c.Wrapped(o => c.FillCircle(x + o, y, size, col));
            }
        }

        /// <summary>A grid of slabs w x h pixels with joints, each a slightly different shade.</summary>
        static void Slabs(PixelCanvas c, System.Random rng, int sw, int sh, Color slab, Color joint, float vary)
        {
            c.Clear(joint);
            for (int y = 0; y < c.Height; y += sh)
                for (int x = 0; x < c.Width; x += sw)
                {
                    float k = 1f + Rand(rng, -vary, vary);
                    c.FillRect(x + 1.5f, y + 1.5f, x + sw - 1.5f, y + sh - 1.5f, new Color(slab.r * k, slab.g * k, slab.b * k));
                }
        }

        // ---------------------------------------------------------------- facades

        /// <summary>The street face of a building, drawn to <see cref="FacadeSize"/> at 40 px per unit.</summary>
        public static PixelCanvas Facade(FacadeKind kind)
        {
            Vector2 size = FacadeSize(kind);
            int w = Mathf.RoundToInt(size.x * FacadePpu), h = Mathf.RoundToInt(size.y * FacadePpu);
            var c = new PixelCanvas(w, h);
            const float u = FacadePpu;   // one world unit (0.9 m)
            switch (kind)
            {
                case FacadeKind.HouseGable:
                {
                    Color wall = new Color(0.95f, 0.94f, 0.9f);
                    c.Clear(wall);
                    c.FillRect(0, 3f * u, w, 3f * u + 5f, new Color(0.86f, 0.86f, 0.84f));    // floor band
                    Window(c, 0.8f * u, 3.7f * u, 2.9f * u, 5f * u);                             // first floor
                    Window(c, 3.8f * u, 3.7f * u, 6.3f * u, 5f * u);
                    Window(c, 3.9f * u, 1f * u, 6.3f * u, 2.3f * u);                             // ground floor
                    Door(c, 0.5f * u, 2.2f * u, 1.2f * u);
                    c.FillRect(2.2f * u, 0, 2.6f * u, 3f * u, new Color(0.62f, 0.3f, 0.24f));    // brick pillar
                    for (float y = 4; y < 3f * u; y += 9) c.FillRect(2.2f * u, y, 2.6f * u, y + 2, new Color(0.5f, 0.24f, 0.2f));
                    c.FillRect(3f * u, 1.2f * u, 3.4f * u, 1.8f * u, new Color(0.84f, 0.85f, 0.85f)); // meter box
                    AcUnit(c, 4.1f * u, 0f, u);
                    c.FillRect(w - 6, 0, w - 2, h, new Color(0.62f, 0.64f, 0.66f));              // downpipe
                    Weathering(c, 3);
                    break;
                }
                case FacadeKind.HouseLong:
                {
                    Color wall = new Color(0.93f, 0.91f, 0.86f);
                    c.Clear(wall);
                    c.FillRect(0, 2.9f * u, w, 2.9f * u + 6f, new Color(0.38f, 0.38f, 0.42f));  // lower roof skirt
                    for (int i = 0; i < 3; i++) Window(c, (0.8f + i * 3.1f) * u, 3.5f * u, (2.9f + i * 3.1f) * u, 4.8f * u);
                    Window(c, 5.6f * u, 0.9f * u, 9.2f * u, 2.3f * u);
                    Door(c, 1f * u, 2.2f * u, 1.4f * u);
                    c.FillRect(3.2f * u, 0, 4.8f * u, 2.6f * u, new Color(0.66f, 0.6f, 0.52f));   // wooden lattice panel
                    for (float x = 3.25f * u; x < 4.8f * u; x += 6) c.FillRect(x, 0, x + 2, 2.6f * u, new Color(0.52f, 0.46f, 0.4f));
                    Weathering(c, 4);
                    break;
                }
                case FacadeKind.Bungalow:
                {
                    Color wall = new Color(0.88f, 0.89f, 0.9f);
                    c.Clear(wall);
                    for (float x = 2; x < w; x += 9) c.FillRect(x, 0, x + 2, h, new Color(0.78f, 0.79f, 0.82f));   // corrugated siding
                    Window(c, 1f * u, 1.2f * u, 1.9f * u, 2.8f * u, false);
                    c.FillRect(2.6f * u, 0, 3.1f * u, h, new Color(0.62f, 0.3f, 0.24f));
                    for (float y = 4; y < h; y += 9) c.FillRect(2.6f * u, y, 3.1f * u, y + 2, new Color(0.5f, 0.24f, 0.2f));
                    Door(c, 3.6f * u, 2.2f * u, 1.1f * u);
                    c.FillRect(5.2f * u, 1.6f * u, 6.2f * u, 2.4f * u, new Color(0.86f, 0.86f, 0.86f));
                    Weathering(c, 5);
                    break;
                }
                case FacadeKind.Shop0:
                case FacadeKind.Shop1:
                {
                    bool fruit = kind == FacadeKind.Shop0;
                    Color wall = fruit ? new Color(0.95f, 0.9f, 0.82f) : new Color(0.86f, 0.9f, 0.94f);
                    Color awn = fruit ? new Color(0.25f, 0.45f, 0.75f) : new Color(0.78f, 0.25f, 0.25f);
                    c.Clear(wall);
                    for (int i = 0; i < 3; i++) Window(c, (0.8f + i * 2.5f) * u, 5f * u, (2.4f + i * 2.5f) * u, 6.3f * u);
                    c.FillRect(0, 3.8f * u, w, 4.6f * u, Color.Lerp(awn, Color.white, 0.75f));        // sign board
                    for (int i = 0; i < 5; i++) c.FillRect((1.2f + i * 1.25f) * u, 4f * u, (1.9f + i * 1.25f) * u, 4.4f * u, Mul(awn, 0.8f));
                    if (fruit)
                    {
                        c.FillRect(0.4f * u, 0, 5.6f * u, 3.4f * u, new Color(0.42f, 0.5f, 0.6f));     // open front
                        for (int i = 0; i < 12; i++)
                            c.FillCircle((0.8f + (i % 6) * 0.8f) * u, (0.6f + (i / 6) * 0.7f) * u, 0.22f * u,
                                new[] { new Color(1f, 0.6f, 0.2f), new Color(0.9f, 0.3f, 0.3f), new Color(0.95f, 0.85f, 0.3f), new Color(0.5f, 0.75f, 0.3f) }[i % 4]);
                        Door(c, 6.2f * u, 2.3f * u, 1.3f * u);
                    }
                    else
                    {
                        c.FillRect(0.4f * u, 0, 7.6f * u, 3.4f * u, new Color(0.2f, 0.19f, 0.21f));    // half-raised shutter
                        c.FillRect(0.4f * u, 1.9f * u, 7.6f * u, 3.4f * u, new Color(0.78f, 0.79f, 0.8f));
                        for (float y = 1.95f * u; y < 3.4f * u; y += 7) c.FillRect(0.4f * u, y, 7.6f * u, y + 2, new Color(0.66f, 0.67f, 0.7f));
                        for (int i = 0; i < 4; i++) c.FillRect((2.2f + i * 1f) * u, 1.1f * u, (3f + i * 1f) * u, 1.9f * u, new Color(0.18f, 0.24f, 0.45f)); // noren
                    }
                    Weathering(c, 6);
                    break;
                }
                case FacadeKind.Apartment:
                {
                    Color wall = new Color(0.92f, 0.88f, 0.82f);
                    c.Clear(wall);
                    for (int floor = 0; floor < 5; floor++)
                    {
                        float y = (0.6f + floor * 2.7f) * u;
                        for (int i = 0; i < 3; i++) Window(c, (1f + i * 3.8f) * u, y, (3.4f + i * 3.8f) * u, y + 1.5f * u, false);
                        if (floor > 0)
                        {
                            c.FillRect(0, y - 0.25f * u, w, y - 0.1f * u, new Color(0.84f, 0.84f, 0.84f));    // balcony slab
                            for (float x = 2; x < w; x += 10) c.FillRect(x, y - 0.1f * u, x + 3, y + 0.75f * u, new Color(0.7f, 0.7f, 0.72f));
                            c.FillRect(0, y + 0.72f * u, w, y + 0.8f * u, new Color(0.7f, 0.7f, 0.72f));
                        }
                    }
                    Weathering(c, 7);
                    break;
                }
                case FacadeKind.School:
                {
                    Color wall = new Color(0.95f, 0.94f, 0.9f);
                    c.Clear(wall);
                    for (int floor = 0; floor < 3; floor++)
                        for (int i = 0; i < 12; i++)
                            Window(c, (0.8f + i * 2.6f) * u, (0.9f + floor * 3.1f) * u, (2.9f + i * 2.6f) * u, (2.5f + floor * 3.1f) * u, false);
                    c.FillRect(0, 9.6f * u, w, h, new Color(0.84f, 0.84f, 0.82f));
                    Door(c, 14.6f * u, 2.6f * u, 2.8f * u);
                    Weathering(c, 8);
                    break;
                }
                default:
                {
                    // Warehouse: corrugated metal with a roller door.
                    Color wall = new Color(0.78f, 0.74f, 0.7f);
                    c.Clear(wall);
                    for (float x = 2; x < w; x += 8) c.FillRect(x, 0, x + 3, h, Mul(wall, 0.9f));
                    c.FillRect(1.5f * u, 0, 5.5f * u, 3.6f * u, new Color(0.62f, 0.62f, 0.66f));
                    for (float y = 3; y < 3.6f * u; y += 7) c.FillRect(1.5f * u, y, 5.5f * u, y + 2, new Color(0.52f, 0.52f, 0.56f));
                    Door(c, 7.5f * u, 2.2f * u, 1f * u);
                    Window(c, 8.8f * u, 2.6f * u, 10.2f * u, 3.6f * u, false);
                    Weathering(c, 9);
                    break;
                }
            }
            return c;
        }

        static void Door(PixelCanvas c, float x, float height, float width)
        {
            c.FillRect(x, 0, x + width, height, new Color(0.46f, 0.34f, 0.26f));
            c.FillRect(x + 4, 0, x + width - 4, height - 4, new Color(0.38f, 0.28f, 0.22f));
            for (float px = x + 8; px < x + width - 6; px += 8) c.FillRect(px, 0, px + 2, height - 4, new Color(0.5f, 0.38f, 0.3f));
            c.FillRect(x - 6, height, x + width + 6, height + 6, new Color(0.5f, 0.53f, 0.58f));   // canopy
        }

        static void AcUnit(PixelCanvas c, float x, float y, float u)
        {
            c.FillRoundRect(x, y, x + 1.2f * u, y + 0.8f * u, 3, new Color(0.9f, 0.91f, 0.92f));
            c.FillCircle(x + 0.42f * u, y + 0.4f * u, 0.28f * u, new Color(0.35f, 0.37f, 0.4f));
            c.FillCircle(x + 0.42f * u, y + 0.4f * u, 0.09f * u, new Color(0.7f, 0.72f, 0.74f));
        }

        /// <summary>Soft rain streaks and grime near the ground, so walls aren't flat paint.</summary>
        static void Weathering(PixelCanvas c, int seed)
        {
            c.Shade((x, y) => y < 18f ? (18f - y) / 18f * 0.35f : 0f, new Color(0.55f, 0.55f, 0.55f));
            c.Shade((x, y) => Mathf.PerlinNoise(x * 0.05f + seed, y * 0.006f) > 0.7f ? 0.05f : 0f, new Color(0.6f, 0.6f, 0.62f));
        }

        // ---------------------------------------------------------------- cut-out plants

        /// <summary>A cloud-pruned garden pine, standing on the canvas bottom.</summary>
        public static PixelCanvas Pine()
        {
            var c = Prop(0.9f);
            Color pine = new Color(0.2f, 0.42f, 0.3f), lit = new Color(0.38f, 0.6f, 0.4f);
            c.Line(new Vector2(256, 0), new Vector2(276, 140), 16, Bark);
            c.Line(new Vector2(276, 140), new Vector2(236, 280), 13, Bark);
            c.Line(new Vector2(236, 280), new Vector2(262, 400), 10, Bark);
            c.Line(new Vector2(270, 180), new Vector2(340, 220), 8, Bark);
            c.Line(new Vector2(244, 250), new Vector2(170, 300), 8, Bark);
            foreach (var pad in new[] { new Vector3(350, 220, 56), new Vector3(166, 300, 52), new Vector3(300, 330, 46), new Vector3(262, 420, 40), new Vector3(200, 200, 40) })
            {
                c.FillEllipse(pad.x, pad.y, pad.z * 1.4f, pad.z * 0.6f, pine);
                c.FillEllipse(pad.x + 8, pad.y + 8, pad.z * 1.15f, pad.z * 0.4f, lit);
            }
            return c;
        }

        /// <summary>A round garden shrub, standing on the canvas bottom.</summary>
        public static PixelCanvas Bush()
        {
            var c = new PixelCanvas(256, 160);
            Foliage(c, 128, 70, 110, 62, Leaf, LeafDark, 41, 30);
            return c;
        }
    }
}
