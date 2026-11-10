using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.Pickups
{
    /// <summary>
    /// A coin collected by the kid or the ball. Spins, bobs, and pops when taken.
    /// Restored when the level restarts.
    ///
    /// The kid's physics capsule is 1.2 m tall, shorter than the kid on screen (the teens stand about 1.6 m):
    /// a coin at head height (the underpass's rows at 1.6 m) went straight through the drawn head untouched.
    /// So a coin is also taken when it overlaps the kid as drawn: the column from the feet up to the model's
    /// height, scaled down with the capsule while the kid slides (<see cref="KidReach"/>, measured once a frame
    /// for every coin).
    ///
    /// And when the level starts, each coin makes sure the kid can get to it (<see cref="Settle"/>): a coin sunk into
    /// a solid (a wall, a ceiling, a step, the ground) or hung higher above the ground under it than a double jump
    /// reaches (<see cref="Holiday.JumpReach.HighestCoin"/>) moves to the nearest clear, reachable spot straight up or
    /// down, and says so in the editor's console so its layout can be put right. Coins over an open pit (the arcs
    /// that show the jump) are left where they are.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class Coin : MonoBehaviour, IResettable
    {
        public int value = 1;
        public Transform visual;

        public bool Collected { get; private set; }

        Vector3 basePosition;
        float phase;
        float collectedAt;
        // The visual may not be at full size (shrunk by the pop, or as built): set it back on the next idle frame, once,
        // instead of writing the scale every frame for every coin.
        bool resize = true;

        /// <summary>How far past the side of the view (world units) a coin stops spinning and bobbing: room for the coin, its
        /// bob and its shadow, which the chapters' lowest sun (ChapterTheme, about 0.8 m sideways per metre of height) throws
        /// up to about 3 m to the side of the highest coins (some 3.7 m up), plus slack for the tilted view.</summary>
        const float RestBeyond = 4f;

        void Awake()
        {
            var col = GetComponent<Collider2D>();
            col.isTrigger = true;
            var circle = col as CircleCollider2D;
            if (circle != null) radius = circle.radius * Mathf.Abs(transform.lossyScale.x);
            basePosition = visual != null ? visual.localPosition : Vector3.zero;
            phase = transform.position.x * 0.7f;
        }

        void Start() { Settle(); }

        // ---- Settling into a reachable spot ----
        static readonly Collider2D[] overlaps = new Collider2D[16];
        static readonly RaycastHit2D[] hits = new RaycastHit2D[16];
        static int syncedFrame = -1;
        static float highestCoin = -1f;

        /// <summary>A collider the kid can't pass through and that stays put: ground, walls, ceilings, parked cars...
        /// Not triggers, not things that move (the kid, the ball, crates, moving platforms), not one-way platforms.</summary>
        static bool Solid(Collider2D c)
        {
            if (c == null || c.isTrigger) return false;
            var rb = c.attachedRigidbody;
            if (rb != null && rb.bodyType != RigidbodyType2D.Static) return false;
            return !(c.usedByEffector && c.GetComponent<PlatformEffector2D>() != null);
        }

        static ContactFilter2D SolidFilter()
        {
            var filter = new ContactFilter2D();
            filter.useTriggers = false;
            filter.useLayerMask = false;
            return filter;
        }

        bool Free(Vector2 p)
        {
            int n = Physics2D.OverlapCircle(p, radius * 0.9f, SolidFilter(), overlaps);
            for (int i = 0; i < n; i++) if (Solid(overlaps[i])) return false;
            return true;
        }

        /// <summary>The ground under p (any standable top, one-way platforms included): false over an open pit.</summary>
        static bool GroundUnder(Vector2 p, out float top)
        {
            top = 0f;
            int n = Physics2D.Raycast(p, Vector2.down, SolidFilter(), hits, 60f);
            float best = float.MaxValue;
            bool found = false;
            for (int i = 0; i < n; i++)
            {
                var c = hits[i].collider;
                if (c == null || c.isTrigger) continue;
                var rb = c.attachedRigidbody;
                if (rb != null && rb.bodyType == RigidbodyType2D.Dynamic) continue;   // a crate or the ball is no floor
                if (hits[i].distance < best) { best = hits[i].distance; top = hits[i].point.y; found = true; }
            }
            return found;
        }

        bool Reachable(Vector2 p)
        {
            float top;
            if (!GroundUnder(p, out top)) return true;   // over a pit: the arc that shows the jump
            return p.y - top <= highestCoin;
        }

        /// <summary>Moves the coin to the nearest clear spot the kid can reach, straight up or down (up to 3 m), if it isn't in one.</summary>
        void Settle()
        {
            if (highestCoin < 0f) highestCoin = Holiday.JumpReach.HighestCoin(Holiday.JumpReach.Defaults) - 0.1f;
            if (syncedFrame != Time.frameCount) { Physics2D.SyncTransforms(); syncedFrame = Time.frameCount; }
            Vector2 p = transform.position;
            if (Free(p) && Reachable(p)) return;
            for (int k = 1; k <= 30; k++)
            {
                // Down first when it hangs too high, else up first (out of the ground or a step); then the other way.
                float top;
                bool tooHigh = GroundUnder(p, out top) && p.y - top > highestCoin;
                for (int side = 0; side < 2; side++)
                {
                    float dir = (side == 0) == tooHigh ? -1f : 1f;
                    Vector2 q = p + Vector2.up * (dir * k * 0.1f);
                    if (!Free(q) || !Reachable(q)) continue;
                    transform.position = new Vector3(q.x, q.y, transform.position.z);
                    // (only in the editor and development builds: Debug.isDebugBuild)
                    if (Debug.isDebugBuild)
                        Debug.Log("[Coin] " + name + " at (" + p.x.ToString("0.0") + ", " + p.y.ToString("0.00") + ") in " + gameObject.scene.name
                            + (tooHigh ? " was out of reach" : " was inside a solid") + "; moved to y " + q.y.ToString("0.00") + ". Fix its place in the layout.");
                    return;
                }
            }
            if (Debug.isDebugBuild)
                Debug.LogWarning("[Coin] " + name + " at (" + p.x.ToString("0.0") + ", " + p.y.ToString("0.00") + ") in " + gameObject.scene.name + " can't be reached and has no clear spot within 3 m.");
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            if (Collected) return;
            var rb = other.attachedRigidbody;
            if (rb == null) return;
            if (rb.GetComponent<KidController>() == null && rb.GetComponent<BallController>() == null) return;
            TryCollect();
        }

        float radius = 0.28f;   // the trigger's (0.28 a coin, 0.5 a Holiday Run star coin)

        // ---- The kid as drawn, once a frame for all the coins ----
        static KidController reachKid;
        static CapsuleCollider2D reachCapsule;
        static float reachModelHeight, reachStandHeight;
        static int reachFrame = -1;
        static bool reachValid;
        static Vector2 reachFeet;
        static float reachTop, reachHalfWidth;

        /// <summary>The column the kid fills on screen this frame: feet, top and half width (false without a kid).</summary>
        static bool KidReach()
        {
            if (reachFrame == Time.frameCount) return reachValid;
            reachFrame = Time.frameCount;
            reachValid = false;
            var level = LevelManager.Current;
            var kid = level != null ? level.kid : null;
            if (kid == null || !kid.isActiveAndEnabled) return false;
            if (kid != reachKid)
            {
                reachKid = kid;
                reachCapsule = kid.GetComponent<CapsuleCollider2D>();
                reachModelHeight = 0f;
                reachStandHeight = reachCapsule != null ? reachCapsule.size.y : 1.2f;
            }
            if (reachCapsule == null) return false;
            reachFeet = kid.FeetPosition;
            if (reachModelHeight <= 0f)
            {
                // The drawn kid's height over the feet, from the visible model (the cast's chosen kid).
                float top = float.MinValue;
                foreach (var r in kid.GetComponentsInChildren<SkinnedMeshRenderer>())
                    if (r.enabled && r.gameObject.activeInHierarchy) top = Mathf.Max(top, r.bounds.max.y);
                reachModelHeight = top > float.MinValue ? Mathf.Clamp(top - reachFeet.y, reachStandHeight, 1.9f) : reachStandHeight;
            }
            reachStandHeight = Mathf.Max(reachStandHeight, reachCapsule.size.y);
            // Sliding, the capsule is low and so is the kid on screen.
            float h = reachCapsule.size.y;
            reachTop = reachFeet.y + reachModelHeight * Mathf.Clamp01(h / Mathf.Max(reachStandHeight, 0.01f));
            reachHalfWidth = Mathf.Max(reachCapsule.size.x, 0.4f) * 0.5f;
            reachValid = true;
            return true;
        }

        void TryCollect()
        {
            if (Collected) return;
            var level = LevelManager.Current;
            if (level == null || (level.State != LevelState.Playing && level.State != LevelState.Respawning)) return;

            Collected = true;
            collectedAt = Time.time;
            GetComponent<Collider2D>().enabled = false;
            level.CollectCoin(this);
            GameEvents.Raise(GameEventType.Coin, transform.position);
        }

        void Update()
        {
            Vector3 at = transform.position;
            if (!Collected && KidReach())
            {
                if (Mathf.Abs(at.x - reachFeet.x) <= reachHalfWidth + radius && at.y >= reachFeet.y - radius && at.y <= reachTop + radius * 0.5f)
                    TryCollect();
            }
            if (visual == null) return;
            if (Collected)
            {
                // Once the pop is over the visual is hidden: nothing left to move until the level restarts.
                if (!visual.gameObject.activeSelf) return;
                // Quick pop up and shrink away.
                float t = Mathf.Clamp01((Time.time - collectedAt) / 0.3f);
                visual.localPosition = basePosition + Vector3.up * t * 0.6f;
                visual.localScale = Vector3.one * (1f - t);
                resize = true;
                visual.localRotation = Quaternion.Euler(0f, Time.time * 900f + phase * 57f, 0f);
                if (t >= 1f)
                {
                    visual.gameObject.SetActive(false);
                    // Nothing moves until the level restarts: ResetState switches the coin back on (LevelManager finds and
                    // resets it whether it is enabled or not).
                    enabled = false;
                }
                return;
            }
            if (resize)
            {
                visual.localScale = Vector3.one;
                resize = false;
            }
            // Well off screen the spin and the bob are skipped (a level has hundreds of coins, and each wrote two transforms
            // every frame): both follow the clock alone, so a coin is posed exactly right again the frame it comes back
            // into view, the magnet's pull included. Without a camera every coin animates, as before.
            if (World.AmbientView.Valid && !World.AmbientView.InViewX(at.x, at.z, RestBeyond)) return;
            // A real 3D spin about the vertical axis.
            visual.localRotation = Quaternion.Euler(0f, (Time.time * 4f + phase) * Mathf.Rad2Deg, 0f);
            visual.localPosition = basePosition + Vector3.up * Mathf.Sin(Time.time * 2f + phase) * 0.06f;
        }

        public void ResetState()
        {
            Collected = false;
            enabled = true;
            GetComponent<Collider2D>().enabled = true;
            if (visual != null)
            {
                visual.gameObject.SetActive(true);
                visual.localPosition = basePosition;
            }
        }
    }
}
