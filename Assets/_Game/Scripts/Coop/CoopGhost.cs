using DribbleToSchool.Presentation;
using UnityEngine;

namespace DribbleToSchool.Coop
{
    /// <summary>
    /// Another player's kid and ball in this phone's copy of the leg, drawn where their phone says they are (Coop/CoopLevelLink
    /// feeds it their motion, a fraction of a second in the past so it moves smoothly between samples). It is only a picture:
    /// no collider, no physics, nothing in the level reacts to it, as racing ghosts are. It runs in its own lane just behind
    /// the kid's (further along the footpath), with a ring of the player's colour at its feet and their name over its head
    /// (Coop/CoopHud). The kid model is a copy of the level's own model of that kid, posed by a simple version of the
    /// kid's animation (run, jump, slide).
    /// </summary>
    public class CoopGhost : MonoBehaviour
    {
        public uint uid;
        public byte slot;

        CharacterRig rig;
        Transform visual, ballRoot;
        SpriteRenderer ring;
        float phase, facing = 1f, slideBlend;
        bool shown;
        float runSpeed = 6.5f;

        /// <summary>Where the name tag goes (over the head), in the world.</summary>
        public Vector3 TagPoint { get { return transform.position + Vector3.up * 1.25f; } }
        public bool Shown { get { return shown; } }

        /// <summary>
        /// Builds the ghost from a copy of a kid's visual (<paramref name="kidVisual"/>, taken while it still stands in its rest
        /// pose) and of the ball's mesh, in lane <paramref name="laneZ"/>.
        /// </summary>
        public void Build(GameObject kidVisual, Vector3 visualLocalPosition, Quaternion visualLocalRotation, GameObject ballShell, Color color, float laneZ, float kidRunSpeed)
        {
            runSpeed = Mathf.Max(1f, kidRunSpeed);
            var holder = new GameObject("Holder");
            holder.SetActive(false);   // copies made under an inactive parent run nothing until they are cleaned
            holder.transform.SetParent(transform, false);

            if (kidVisual != null)
            {
                var copy = Instantiate(kidVisual, holder.transform);
                copy.name = "Kid";
                copy.SetActive(true);
                copy.transform.localPosition = visualLocalPosition;
                copy.transform.localRotation = visualLocalRotation;
                Strip(copy);
                visual = copy.transform;
                rig = copy.GetComponentInChildren<CharacterRig>(true);
                foreach (var r in copy.GetComponentsInChildren<Renderer>(true)) Tint(r, color, 0.18f);
            }
            if (ballShell != null)
            {
                ballRoot = new GameObject("Ball").transform;
                ballRoot.SetParent(holder.transform, false);
                var shell = Instantiate(ballShell, ballRoot);
                shell.transform.localPosition = Vector3.zero;
                shell.transform.localRotation = Quaternion.identity;
                Strip(shell);
                foreach (var r in shell.GetComponentsInChildren<Renderer>(true)) Tint(r, color, 0.35f);
            }

            // A flat ring of the player's colour on the ground under the feet.
            var ringGo = new GameObject("Ring");
            ringGo.transform.SetParent(holder.transform, false);
            ringGo.transform.localPosition = new Vector3(0f, -0.58f, 0f);
            ringGo.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);
            ringGo.transform.localScale = new Vector3(0.9f, 0.9f, 1f);
            ring = ringGo.AddComponent<SpriteRenderer>();
            ring.sprite = UI.Kit.ProceduralSprites.SoftEdgeDisc;
            ring.color = new Color(color.r, color.g, color.b, 0.55f);
            ring.sortingOrder = 18;

            transform.position = new Vector3(transform.position.x, transform.position.y, laneZ);
            holder.SetActive(true);
            shown = true;
            SetShown(false);   // hidden until the first motion from that player arrives
        }

        /// <summary>Everything but the look: physics, the player's animation and gameplay scripts would react to the level.</summary>
        static void Strip(GameObject go)
        {
            foreach (var c in go.GetComponentsInChildren<Component>(true))
            {
                if (c == null) continue;
                // (a trail is a Renderer too: it goes before the renderers are kept, or every ghost's ball smears the street)
                if (c is TrailRenderer) { DestroyImmediate(c); continue; }
                // (a kid's renderers load their mesh as they appear: LazyRenderer stays)
                if (c is Transform || c is Renderer || c is MeshFilter || c is CharacterRig || c is BagWear || c is LazyRenderer) continue;
                if (c is Collider2D || c is Collider || c is Rigidbody2D || c is Rigidbody || c is MonoBehaviour)
                    DestroyImmediate(c);
            }
        }

        static void Tint(Renderer r, Color color, float amount)
        {
            if (r == null || r is SpriteRenderer) return;
            var block = new MaterialPropertyBlock();
            r.GetPropertyBlock(block);
            block.SetColor("_Color", Color.Lerp(Color.white, color, amount));
            r.SetPropertyBlock(block);
        }

        void SetShown(bool on)
        {
            if (shown == on) return;
            shown = on;
            foreach (Transform child in transform) child.gameObject.SetActive(on);
        }

        /// <summary>Where the player is now (<paramref name="visible"/> false hides the ghost: another leg, or nothing heard).</summary>
        public void Show(CoopMotion m, bool visible, float dt)
        {
            SetShown(visible);
            if (!visible) return;
            var p = transform.position;
            transform.position = new Vector3(m.x, m.y, p.z);
            if (ballRoot != null) ballRoot.localPosition = new Vector3(m.ballDx, m.ballDy, 0f);
            Pose(m, dt);
        }

        void Pose(CoopMotion m, float dt)
        {
            if (rig == null) return;
            float speed = Mathf.Abs(m.vx);
            float runK = Mathf.Clamp01(speed / runSpeed);
            var p = RigPose.Neutral;
            bool low = m.Has(CoopMotion.Low);
            // (a finished player's ghost is gone: it is at school. So there is no celebration to draw.)
            if (!m.Has(CoopMotion.Grounded))
            {
                float rising = Mathf.Clamp01(m.vy / 6f), falling = Mathf.Clamp01(-m.vy / 8f);
                p.legF = Mathf.Lerp(18f, 52f, rising); p.kneeF = Mathf.Lerp(-25f, -82f, rising);
                p.legB = Mathf.Lerp(-12f, -30f, rising); p.kneeB = Mathf.Lerp(-35f, -42f, rising);
                p.armF = Mathf.Lerp(Mathf.Lerp(60f, 80f, falling), -35f, rising); p.elbowF = Mathf.Lerp(30f, 85f, rising);
                p.armB = Mathf.Lerp(Mathf.Lerp(-40f, 70f, falling), 55f, rising); p.elbowB = Mathf.Lerp(25f, 60f, rising);
                p.lean = Mathf.Lerp(2f, 8f, rising);
            }
            else
            {
                phase += dt * 1.9f * speed * Mathf.PI * 0.5f;
                float s = Mathf.Sin(phase);
                p.legF = s * 42f * runK; p.legB = -s * 42f * runK;
                p.kneeF = -Mathf.Lerp(3f, 14f + 80f * Sq(Mathf.Max(0f, Mathf.Cos(phase + 0.9f))), runK);
                p.kneeB = -Mathf.Lerp(3f, 14f + 80f * Sq(Mathf.Max(0f, Mathf.Cos(phase + Mathf.PI + 0.9f))), runK);
                p.armF = -s * 34f * runK - 6f * runK; p.armB = s * 34f * runK - 6f * runK;
                p.elbowF = Mathf.Lerp(12f, 70f + 25f * Mathf.Max(0f, -s), runK);
                p.elbowB = Mathf.Lerp(12f, 70f + 25f * Mathf.Max(0f, s), runK);
                p.bob = Mathf.Abs(s) * 0.05f * runK - 0.02f * runK;
                p.lean = 7f * runK;
                p.headTilt = KidAnimator.RunHeadTilt(phase, p.lean, runK);
            }
            // The slide: leaning far back, feet first (as the kid's own animation, simplified).
            slideBlend = Mathf.MoveTowards(slideBlend, low ? 1f : 0f, dt / (low ? 0.07f : 0.18f));
            if (slideBlend > 0f)
            {
                float k = Mathf.SmoothStep(0f, 1f, slideBlend);
                const float lean = 58f;
                p.lean = Mathf.Lerp(p.lean, -lean, k);
                p.legF = Mathf.Lerp(p.legF, 82f - lean, k); p.kneeF = Mathf.Lerp(p.kneeF, -6f, k);
                p.legB = Mathf.Lerp(p.legB, 135f - lean, k); p.kneeB = Mathf.Lerp(p.kneeB, -80f, k);   // (the back knee up, its foot planted)
                p.armB = Mathf.Lerp(p.armB, 24f - lean, k); p.armF = Mathf.Lerp(p.armF, 95f - lean, k);
                p.headTilt = Mathf.Lerp(p.headTilt, -44f, k);
                p.bob = Mathf.Lerp(p.bob, -0.32f, k);
            }
            rig.Pose(p);

            float target = m.Has(CoopMotion.FacingRight) ? 1f : -1f;
            facing = Mathf.MoveTowards(facing, target, dt * 7f);
            if (visual != null) visual.localRotation = Quaternion.Euler(0f, CharacterRig.FacingYaw(facing), 0f);
            if (ring != null) ring.enabled = m.Has(CoopMotion.Grounded) || low;
        }

        static float Sq(float f) { return f * f; }
    }
}
