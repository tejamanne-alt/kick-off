using System.Collections.Generic;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// The 3D body of a character, skinned to its CharacterRig: one smooth mesh from the
    /// sneakers to the hair, so knees and elbows bend as skin rather than as separate
    /// pieces, and the character has real depth when it turns. The schoolkid wears a white
    /// shirt and red tie, shorts, long socks, sneakers and a messenger bag; adults wear a
    /// long-sleeved top and trousers. Built when the scene loads from these settings (the
    /// mesh is not saved), and rebuilt when the outfit changes.
    /// Geometry is laid out in the rig's space (facing +x, feet at y = -0.6, about 1.55 tall).
    /// </summary>
    [ExecuteAlways]
    [RequireComponent(typeof(SkinnedMeshRenderer))]
    public class CharacterBody3D : MonoBehaviour, IOutfit
    {
        public CharacterRig rig;
        [Tooltip("Schoolkid: shorts, long socks, short sleeves, tie and bag. Off: an adult in trousers and long sleeves.")]
        public bool kidOutfit = true;
        public Color skin = new Color(0.98f, 0.84f, 0.72f);
        public Color shirt = new Color(0.97f, 0.97f, 0.99f);
        [Tooltip("Shorts (the kid) or trousers (adults).")]
        public Color legwear = new Color(0.22f, 0.23f, 0.42f);
        public Color hair = new Color(0.16f, 0.15f, 0.2f);
        public Color shoes = new Color(0.96f, 0.96f, 0.97f);
        public Color socks = new Color(0.97f, 0.97f, 0.98f);
        public Color tie = new Color(0.78f, 0.2f, 0.24f);
        public Color bag = new Color(0.2f, 0.28f, 0.52f);
        public Color eyes = new Color(0.2f, 0.13f, 0.14f);
        [Tooltip("Girth multiplier (adults are a little broader).")]
        public float build = 1f;

        // Bone order in the skinned mesh.
        const int Body = 0, LegF = 1, KneeF = 2, LegB = 3, KneeB = 4, ArmF = 5, ElbowF = 6, ArmB = 7, ElbowB = 8, Head = 9, Bag = 10;
        const int Segments = 16;

        Mesh mesh;

        void OnEnable() { Rebuild(); }

        void OnDestroy()
        {
            if (mesh == null) return;
            if (Application.isPlaying) Destroy(mesh);
            else DestroyImmediate(mesh);
        }

        /// <summary>Re-dress the character (the shop's outfits) and rebuild the mesh.</summary>
        public void SetOutfit(Color shirtColor, Color legwearColor)
        {
            shirt = shirtColor;
            legwear = legwearColor;
            Rebuild();
        }

        public void Rebuild()
        {
            if (rig == null || rig.body == null) return;
            var bones = new[]
            {
                rig.body, rig.legFront, rig.kneeFront, rig.legBack, rig.kneeBack,
                rig.armFront, rig.elbowFront, rig.armBack, rig.elbowBack, rig.head, rig.bag != null ? rig.bag : rig.body,
            };
            foreach (var bone in bones) if (bone == null) return;

            // Measure and bind in the rest pose (all joints straight, no squash).
            var savedRotations = new Quaternion[bones.Length];
            for (int i = 0; i < bones.Length; i++) { savedRotations[i] = bones[i].localRotation; bones[i].localRotation = Quaternion.identity; }

            var b = new SkinBuilder();
            Matrix4x4 toRig = rig.body.worldToLocalMatrix;
            BuildTorso(b);
            BuildLeg(b, toRig.MultiplyPoint3x4(rig.legFront.position), LegF, KneeF);
            BuildLeg(b, toRig.MultiplyPoint3x4(rig.legBack.position), LegB, KneeB);
            BuildArm(b, toRig.MultiplyPoint3x4(rig.armFront.position), ArmF, ElbowF);
            BuildArm(b, toRig.MultiplyPoint3x4(rig.armBack.position), ArmB, ElbowB);
            BuildHead(b, toRig.MultiplyPoint3x4(rig.head.position));
            if (kidOutfit && rig.bag != null) BuildBag(b, toRig.MultiplyPoint3x4(rig.bag.position));
            b.Transform(transform.worldToLocalMatrix * rig.body.localToWorldMatrix);

            var bindposes = new Matrix4x4[bones.Length];
            for (int i = 0; i < bones.Length; i++) bindposes[i] = bones[i].worldToLocalMatrix * transform.localToWorldMatrix;
            for (int i = 0; i < bones.Length; i++) bones[i].localRotation = savedRotations[i];

            if (mesh == null)
            {
                mesh = new Mesh();
                mesh.name = name + " (procedural)";
                mesh.hideFlags = HideFlags.DontSave;
            }
            b.Fill(mesh, bindposes);

            var smr = GetComponent<SkinnedMeshRenderer>();
            smr.sharedMesh = mesh;
            smr.bones = bones;
            smr.rootBone = rig.body;
            smr.quality = SkinQuality.Bone2;
            smr.localBounds = new Bounds(new Vector3(0f, 0.2f, 0f), new Vector3(2.6f, 2.6f, 1.6f));
            smr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            smr.receiveShadows = false;
        }

        // ---------- Body parts (rig space) ----------

        static SkinBuilder.Ring R(Vector3 c, float rx, float rz, Color color, int b0, int b1 = -1, float w1 = 0f)
        {
            return new SkinBuilder.Ring { center = c, x = Vector3.right, z = Vector3.forward, rx = rx, rz = rz, color = color, b0 = b0, b1 = b1 < 0 ? b0 : b1, w1 = w1 };
        }

        /// <summary>Torso half-depth (front to back) and half-width at height y.</summary>
        static void TorsoSize(float y, out float rx, out float rz)
        {
            float[] ys = { 0.03f, 0.1f, 0.2f, 0.3f, 0.4f, 0.48f, 0.54f, 0.585f, 0.615f };
            float[] xs = { 0.066f, 0.088f, 0.084f, 0.081f, 0.089f, 0.092f, 0.086f, 0.068f, 0.042f };
            float[] zs = { 0.095f, 0.132f, 0.125f, 0.12f, 0.13f, 0.14f, 0.147f, 0.12f, 0.066f };
            int i = 0;
            while (i < ys.Length - 2 && y > ys[i + 1]) i++;
            float t = Mathf.Clamp01((y - ys[i]) / (ys[i + 1] - ys[i]));
            rx = Mathf.Lerp(xs[i], xs[i + 1], t);
            rz = Mathf.Lerp(zs[i], zs[i + 1], t);
        }

        void BuildTorso(SkinBuilder b)
        {
            float g = build;
            // Shorts or trousers up to the waist, a belt, the shirt above. Rings are doubled
            // where the colour changes so the edges are crisp.
            float waist = kidOutfit ? 0.21f : 0.19f;
            float beltLo = waist - 0.012f, beltHi = waist + 0.006f;
            Color belt = Color.Lerp(legwear, Color.black, 0.35f);
            var rings = new List<SkinBuilder.Ring>();
            System.Action<float, Color, float> add = (y, c, grow) =>
            {
                float rx, rz;
                TorsoSize(y, out rx, out rz);
                rings.Add(R(new Vector3(0f, y, 0f), rx * g * grow, rz * g * grow, c, Body));
            };
            add(0.03f, legwear, 1f);
            add(0.1f, legwear, 1f);
            add(0.16f, legwear, 1f);
            add(beltLo, legwear, 1f);
            add(beltLo, belt, 1.025f);
            add(beltHi, belt, 1.025f);
            add(beltHi, shirt, 1.01f);
            foreach (float y in new[] { 0.3f, 0.4f, 0.48f, 0.54f, 0.585f, 0.615f }) add(y, shirt, 1f);
            b.Tube(rings, Segments + 4);

            // Neck, blending into the head, and a collar.
            var neck = new List<SkinBuilder.Ring>
            {
                R(new Vector3(0.02f, 0.55f, 0f), 0.04f * g, 0.045f * g, skin, Body),
                R(new Vector3(0.025f, 0.62f, 0f), 0.038f * g, 0.042f * g, skin, Body, Head, 0.5f),
                R(new Vector3(0.03f, 0.69f, 0f), 0.04f * g, 0.044f * g, skin, Head),
            };
            b.Tube(neck, 12);
            var collar = new List<SkinBuilder.Ring>
            {
                R(new Vector3(0.012f, 0.578f, 0f), 0.06f * g, 0.072f * g, shirt, Body),
                R(new Vector3(0.018f, 0.612f, 0f), 0.05f * g, 0.056f * g, shirt, Body),
            };
            b.Tube(collar, Segments, false, false);

            if (kidOutfit)
            {
                // Red school tie down the front of the shirt.
                float rx, rz;
                TorsoSize(0.44f, out rx, out rz);
                b.Ellipsoid(new Vector3(rx * g + 0.004f, 0.44f, 0f), new Vector3(0.012f, 0.1f, 0.026f), Body, tie, 10, 8);
                TorsoSize(0.555f, out rx, out rz);
                b.Ellipsoid(new Vector3(rx * g + 0.008f, 0.556f, 0f), new Vector3(0.016f, 0.022f, 0.024f), Body, Color.Lerp(tie, Color.black, 0.15f), 10, 8);
            }
        }

        void BuildLeg(SkinBuilder b, Vector3 hip, int thigh, int shin)
        {
            float g = build;
            Vector3 down = Vector3.down;
            float sockTop = 0.47f;
            Color bare = kidOutfit ? skin : legwear;
            float[] ls = { -0.05f, 0f, 0.1f, 0.2f, 0.29f, 0.36f, 0.42f, 0.48f, 0.56f, 0.64f };
            float[] rs = { 0.078f, 0.078f, 0.073f, 0.066f, 0.057f, 0.052f, 0.056f, 0.057f, 0.046f, 0.036f };
            var rings = new List<SkinBuilder.Ring>();
            for (int i = 0; i < ls.Length; i++)
            {
                float l = ls[i];
                // The knee: thigh above, shin below, blended through the joint.
                float w = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.3f, 0.42f, l));
                Color c = kidOutfit && l >= sockTop ? socks : bare;
                if (kidOutfit && i > 0 && ls[i - 1] < sockTop && l >= sockTop)
                {
                    // A crisp sock top.
                    float r0 = Mathf.Lerp(rs[i - 1], rs[i], Mathf.InverseLerp(ls[i - 1], l, sockTop));
                    float ws = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.3f, 0.42f, sockTop));
                    rings.Add(R(hip + down * sockTop, r0 * g, r0 * g * 1.02f, skin, thigh, shin, ws));
                    rings.Add(R(hip + down * sockTop, r0 * g * 1.04f, r0 * g * 1.06f, socks, thigh, shin, ws));
                }
                rings.Add(R(hip + down * l, rs[i] * g, rs[i] * g * 1.02f, c, thigh, shin, w));
            }
            if (!kidOutfit)
            {
                // Trouser hem over the ankle.
                rings.Add(R(hip + down * 0.62f, 0.05f * g, 0.052f * g, legwear, shin));
            }
            b.Tube(rings, Segments, true, true);

            if (kidOutfit)
            {
                // Shorts leg: a wide, slightly flared tube that ends above the knee.
                var shorts = new List<SkinBuilder.Ring>
                {
                    R(hip + down * -0.07f, 0.094f * g, 0.096f * g, legwear, Body, thigh, 0.6f),
                    R(hip + down * 0.04f, 0.093f * g, 0.095f * g, legwear, thigh),
                    R(hip + down * 0.17f, 0.091f * g, 0.093f * g, legwear, thigh),
                    R(hip + down * 0.19f, 0.088f * g, 0.09f * g, Color.Lerp(legwear, Color.black, 0.2f), thigh),
                };
                b.Tube(shorts, Segments, false, true);
            }

            // Sneaker: white upper, grey sole, a blue stripe; flat underneath.
            Vector3 shoeCentre = hip + new Vector3(0.045f, -0.675f, 0f);
            float sole = hip.y - 0.72f;
            Color stripe = new Color(0.35f, 0.45f, 0.75f);
            Color upper = kidOutfit ? shoes : new Color(0.24f, 0.2f, 0.2f);
            Color soleColor = kidOutfit ? new Color(0.62f, 0.64f, 0.68f) : new Color(0.15f, 0.13f, 0.13f);
            b.Ellipsoid(shoeCentre, Vector3.right, Vector3.up, Vector3.forward, new Vector3(0.088f, 0.055f, 0.052f) * g, shin,
                d => d.y < -0.55f ? soleColor : (kidOutfit && d.y < -0.1f && d.y > -0.35f && d.x < 0.3f ? stripe : upper),
                null, 18, 12, 0.85f, sole);
        }

        void BuildArm(SkinBuilder b, Vector3 shoulder, int upper, int fore)
        {
            float g = build;
            Vector3 down = Vector3.down;
            float[] ls = { -0.04f, -0.01f, 0.05f, 0.12f, 0.19f, 0.24f, 0.29f, 0.36f, 0.43f };
            float[] rs = { 0.03f, 0.046f, 0.049f, 0.045f, 0.04f, 0.036f, 0.038f, 0.034f, 0.027f };
            float cuff = 0.41f;
            var rings = new List<SkinBuilder.Ring>();
            for (int i = 0; i < ls.Length; i++)
            {
                float l = ls[i];
                float w = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.19f, 0.29f, l));
                Color c = kidOutfit ? skin : (l < cuff ? shirt : skin);
                if (!kidOutfit && i > 0 && ls[i - 1] < cuff && l >= cuff)
                {
                    rings.Add(R(shoulder + down * cuff, 0.034f * g, 0.035f * g, shirt, fore));
                    rings.Add(R(shoulder + down * cuff, 0.03f * g, 0.031f * g, skin, fore));
                }
                rings.Add(R(shoulder + down * l, rs[i] * g, rs[i] * g, c, upper, fore, w));
            }
            b.Tube(rings, Segments, true, true);

            if (kidOutfit)
            {
                // Short sleeve with a little flare at the hem.
                var sleeve = new List<SkinBuilder.Ring>
                {
                    R(shoulder + down * -0.045f, 0.03f * g, 0.03f * g, shirt, Body, upper, 0.5f),
                    R(shoulder + down * -0.02f, 0.052f * g, 0.054f * g, shirt, Body, upper, 0.7f),
                    R(shoulder + down * 0.03f, 0.063f * g, 0.063f * g, shirt, upper),
                    R(shoulder + down * 0.13f, 0.06f * g, 0.059f * g, shirt, upper),
                };
                b.Tube(sleeve, Segments, true, true);
            }

            // Hand: a soft mitten shape and a thumb.
            Vector3 hand = shoulder + new Vector3(0.006f, -0.468f, 0f);
            b.Ellipsoid(hand, new Vector3(0.029f, 0.044f, 0.022f) * g, fore, skin);
            b.Ellipsoid(hand + new Vector3(0.021f, 0.01f, 0f), new Vector3(0.011f, 0.021f, 0.012f) * g, fore, skin, 10, 8);
        }

        void BuildHead(SkinBuilder b, Vector3 pivot)
        {
            Vector3 c = pivot + new Vector3(0.012f, 0.18f, 0f);
            Vector3 r = new Vector3(0.146f, 0.156f, 0.137f);
            Color blush = Color.Lerp(skin, new Color(1f, 0.55f, 0.5f), 0.35f);

            // Skull, with a faint blush on the cheeks.
            b.Ellipsoid(c, Vector3.right, Vector3.up, Vector3.forward, r, Head,
                d => d.x > 0.45f && d.y < -0.15f && d.y > -0.5f && Mathf.Abs(d.z) > 0.35f ? blush : skin, null, 26, 18);
            // Jaw and chin, tapering forward a little (an anime face).
            b.Ellipsoid(c + new Vector3(0.045f, -0.088f, 0f), new Vector3(0.092f, 0.072f, 0.09f), Head, skin, 16, 10);
            // Ears and a small nose.
            foreach (float s in new[] { -1f, 1f })
                b.Ellipsoid(c + new Vector3(-0.008f, -0.022f, s * 0.132f), new Vector3(0.026f, 0.038f, 0.016f), Head, skin, 10, 8);
            b.Ellipsoid(c + new Vector3(0.148f, -0.03f, 0f), new Vector3(0.013f, 0.016f, 0.01f), Head, skin, 8, 6);

            // Eyes on both sides of the face: white, a big dark iris, a highlight, a brow.
            foreach (float s in new[] { -1f, 1f })
            {
                Vector3 dir = new Vector3(Mathf.Cos(0.62f), -0.06f, s * Mathf.Sin(0.62f)).normalized;
                Vector3 p = c + Vector3.Scale(dir, r);
                Vector3 n = new Vector3(dir.x / r.x, dir.y / r.y, dir.z / r.z).normalized;
                Vector3 side = Vector3.Cross(Vector3.up, n).normalized;
                Vector3 up = Vector3.Cross(n, side).normalized;
                Vector3 front = Vector3.right;
                b.Ellipsoid(p + n * 0.001f, n, up, side, new Vector3(0.007f, 0.03f, 0.026f), Head, d => Color.white, null, 12, 8);
                Vector3 irisAt = p + n * 0.004f + front * 0.006f;
                b.Ellipsoid(irisAt, n, up, side, new Vector3(0.008f, 0.031f, 0.018f), Head,
                    d => d.y > 0.55f ? new Color(0.1f, 0.07f, 0.09f) : Color.Lerp(eyes, new Color(0.45f, 0.3f, 0.28f), Mathf.Clamp01(-d.y) * 0.6f), null, 12, 8);
                b.Ellipsoid(irisAt + n * 0.006f + up * 0.012f + front * 0.004f, n, up, side, new Vector3(0.004f, 0.008f, 0.007f), Head, d => Color.white, null, 8, 6);
                // Upper lid line and brow.
                b.Ellipsoid(p + n * 0.007f + up * 0.03f, n, up, side, new Vector3(0.005f, 0.006f, 0.027f), Head, d => new Color(0.12f, 0.09f, 0.11f), null, 10, 6);
                b.Ellipsoid(p + n * 0.012f + up * 0.06f, n, up, side, new Vector3(0.005f, 0.006f, 0.024f), Head, d => Color.Lerp(hair, Color.black, 0.2f), null, 10, 6);
            }
            // A small mouth.
            Vector3 mouthDir = new Vector3(0.9f, -0.45f, 0f).normalized;
            Vector3 mouth = c + new Vector3(0.045f, -0.088f, 0f) + Vector3.Scale(mouthDir, new Vector3(0.092f, 0.072f, 0.09f));
            b.Ellipsoid(mouth, new Vector3(0.004f, 0.004f, 0.016f), Head, new Color(0.62f, 0.32f, 0.32f), 8, 6);

            // Smooth hair: a glossy shell over the crown and the back of the head, with a soft
            // fringe over the forehead and locks at the temples. A light band is the shine.
            Color shine = Color.Lerp(hair, Color.white, 0.32f);
            Vector3 hr = r * 1.085f;
            Vector3 hc = c + new Vector3(-0.006f, 0.01f, 0f);
            b.Ellipsoid(hc, Vector3.right, Vector3.up, Vector3.forward, hr, Head,
                d => d.y > 0.42f && d.y < 0.58f && d.x < 0.5f ? shine : hair,
                d =>
                {
                    float t = Mathf.Clamp01((1f - d.x) * 0.5f);
                    float threshold = 0.32f - 0.95f * Mathf.Pow(t, 1.15f);
                    return d.y > threshold;
                }, 30, 20);
            // Fringe: soft, flat locks lying on the forehead, ending above the brows.
            foreach (float z in new[] { -0.42f, -0.14f, 0.14f, 0.42f })
            {
                Vector3 dir = new Vector3(0.82f, 0.5f, z).normalized;
                Vector3 n = new Vector3(dir.x / hr.x, dir.y / hr.y, dir.z / hr.z).normalized;
                Vector3 p = hc + Vector3.Scale(dir, hr) - n * 0.012f;
                Vector3 side = Vector3.Cross(Vector3.up, n).normalized;
                Vector3 along = Vector3.Cross(n, side).normalized;
                b.Ellipsoid(p - along * 0.018f, n, along, side, new Vector3(0.016f, 0.05f, 0.042f), Head, d => hair, null, 12, 8);
            }
            // Locks over the temples, in front of the ears.
            foreach (float s in new[] { -1f, 1f })
            {
                Vector3 dir = new Vector3(0.28f, 0.0f, s * 0.96f).normalized;
                Vector3 n = new Vector3(dir.x / hr.x, dir.y / hr.y, dir.z / hr.z).normalized;
                Vector3 p = hc + Vector3.Scale(dir, hr) - n * 0.012f;
                b.Ellipsoid(p, n, Vector3.up, Vector3.Cross(n, Vector3.up).normalized, new Vector3(0.014f, 0.06f, 0.03f), Head, d => hair, null, 12, 8);
            }
        }

        void BuildBag(SkinBuilder b, Vector3 pivot)
        {
            // A school bag worn on the back of the hips, hanging from its strap (the pivot is
            // at its top). The flap and the outside are a shade lighter.
            Color flap = Color.Lerp(bag, Color.white, 0.12f);
            Vector3 c = pivot + new Vector3(-0.007f, -0.1f, 0f);
            b.Ellipsoid(c, Vector3.right, Vector3.up, Vector3.forward, new Vector3(0.042f, 0.1f, 0.13f), Bag,
                d => d.y > 0.3f || (d.x < -0.3f && d.y > -0.3f) ? flap : bag, null, 16, 12, 0.35f);
            b.Ellipsoid(c + new Vector3(-0.042f, -0.01f, 0f), new Vector3(0.007f, 0.036f, 0.02f), Bag, new Color(0.82f, 0.84f, 0.9f), 8, 6);

            // The strap: from the bag up the near side, across the chest, over the far shoulder
            // and down the back to the bag again.
            Color strap = new Color(0.2f, 0.26f, 0.48f);
            var path = new List<Vector3>();
            path.Add(c + new Vector3(0.01f, 0.085f, -0.1f));
            float[,] around = { { 0.33f, -110f }, { 0.4f, -65f }, { 0.46f, -25f }, { 0.52f, 20f }, { 0.57f, 60f }, { 0.61f, 92f }, { 0.565f, 125f }, { 0.48f, 155f }, { 0.4f, 175f } };
            for (int i = 0; i < around.GetLength(0); i++)
            {
                float y = around[i, 0], a = around[i, 1] * Mathf.Deg2Rad, rx, rz;
                TorsoSize(y, out rx, out rz);
                float lift = y > 0.59f ? 0.022f : 0.012f;
                path.Add(new Vector3(Mathf.Cos(a) * (rx * build + lift), y + (y > 0.59f ? 0.012f : 0f), Mathf.Sin(a) * (rz * build + lift)));
            }
            path.Add(c + new Vector3(0.01f, 0.09f, 0.03f));
            var rings = new List<SkinBuilder.Ring>();
            for (int i = 0; i < path.Count; i++)
            {
                Vector3 prev = path[Mathf.Max(0, i - 1)], next = path[Mathf.Min(path.Count - 1, i + 1)];
                Vector3 t = (next - prev).normalized;
                Vector3 outward = new Vector3(path[i].x, 0f, path[i].z);
                if (path[i].y > 0.59f) outward = Vector3.up;
                outward = (outward - t * Vector3.Dot(outward, t)).normalized;
                Vector3 across = Vector3.Cross(t, outward).normalized;
                int bone = i == 0 || i == path.Count - 1 ? Bag : Body;
                rings.Add(new SkinBuilder.Ring { center = path[i], x = outward, z = across, rx = 0.006f, rz = 0.022f, color = strap, b0 = bone, b1 = bone });
            }
            b.Tube(rings, 8, true, true);
        }
    }
}
