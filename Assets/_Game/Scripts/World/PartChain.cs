using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A moving part in links (docs/LEARNINGS.md D19): a tail (Tail, Tail2, Tail3), a wing (WingL, WingL2), a fish's tail.
    /// Each link hangs from the one before, named like it with a number after. A swish or a beat set on the chain bends
    /// it link by link: each link takes a share of the angle (the first the most), and each further link follows the one
    /// before it a moment late, so the motion runs down the part like a whip, where one rigid piece swung from its root
    /// reads as a stick. A part with no links moves whole, as before (the original kit's models).
    ///
    /// The asset review renders the same (tools/blender/asset_review.py: chain_angles): change the two together.
    /// </summary>
    public class PartChain
    {
        /// <summary>Seconds each link lags the one before it.</summary>
        public const float Lag = 0.06f;

        readonly Transform[] links;
        readonly Quaternion[] rest;
        readonly Vector3[] axes;
        readonly float[] angle;

        public int Links { get { return links.Length; } }

        PartChain(Transform[] links, Vector3 axis)
        {
            this.links = links;
            rest = new Quaternion[links.Length];
            axes = new Vector3[links.Length];
            angle = new float[links.Length];
            // the same axis in the world for every link, in each link's own space (a link may come in turned)
            Vector3 world = links.Length > 0 ? links[0].rotation * axis : axis;
            for (int i = 0; i < links.Length; i++)
            {
                rest[i] = links[i].localRotation;
                axes[i] = Quaternion.Inverse(links[i].rotation) * world;
            }
        }

        /// <summary>The chain that starts at first: first, then its child named first's name with 2, that one's with
        /// 3, and so on. axis: the swing axis in the first link's space.</summary>
        public static PartChain Find(Transform first, Vector3 axis)
        {
            var found = new System.Collections.Generic.List<Transform>();
            if (first != null)
            {
                found.Add(first);
                for (int n = 2; n < 10; n++)
                {
                    Transform next = null, last = found[found.Count - 1];
                    for (int i = 0; i < last.childCount && next == null; i++)
                        if (last.GetChild(i).name == first.name + n) next = last.GetChild(i);
                    if (next == null) break;
                    found.Add(next);
                }
            }
            return new PartChain(found.ToArray(), axis);
        }

        /// <summary>Link i's share of a chain of n links' angle: n - i over 1 + 2 + .. + n (a chain of three: one half,
        /// a third, a sixth), so the whole bends by the angle asked for.</summary>
        public static float Share(int i, int n)
        {
            return (n - i) / (n * (n + 1) * 0.5f);
        }

        /// <summary>Bend the chain toward degrees (about its axis, from the rest pose): the first link now, each further
        /// one following the link before it Lag seconds late.</summary>
        public void Set(float degrees, float dt)
        {
            if (links.Length == 0) return;
            angle[0] = degrees;
            float follow = dt > 0f ? 1f - Mathf.Exp(-dt / Lag) : 0f;
            for (int i = 1; i < links.Length; i++) angle[i] += (angle[i - 1] - angle[i]) * follow;
            for (int i = 0; i < links.Length; i++)
                if (links[i] != null)
                    links[i].localRotation = rest[i] * Quaternion.AngleAxis(angle[i] * Share(i, links.Length), axes[i]);
        }

        /// <summary>Every link back in its rest pose, the lag forgotten.</summary>
        public void Rest()
        {
            for (int i = 0; i < links.Length; i++)
            {
                angle[i] = 0f;
                if (links[i] != null) links[i].localRotation = rest[i];
            }
        }
    }
}
