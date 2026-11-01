using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// What the camera sees this frame, worked out once and shared by everything that lives
    /// around the street (pedestrians, animals, birds): how wide the view is at a given depth,
    /// whether a point is in it, and where the kid and the ball are. People and animals use it to
    /// come and go out of sight rather than pop in view, and to rest while far off-screen.
    /// </summary>
    public static class AmbientView
    {
        static int frame = -1;
        static Camera cam;
        static bool ortho, valid;
        static Vector3 camPos;
        static float tanHalfV = 0.3f, tanHalfH = 0.6f, pitchTan, orthoHalfH = 4f, orthoHalfW = 8f;
        static Vector3 kid, ball, lastBall;
        static bool hasKid, hasBall;
        static float kidSpeed, ballSpeed;

        static void Refresh()
        {
            if (frame == Time.frameCount) return;
            frame = Time.frameCount;
            if (cam == null || !cam.isActiveAndEnabled) cam = Camera.main;
            valid = cam != null;
            if (valid)
            {
                var t = cam.transform;
                camPos = t.position;
                ortho = cam.orthographic;
                float aspect = Mathf.Max(0.1f, cam.aspect);
                if (ortho)
                {
                    orthoHalfH = cam.orthographicSize;
                    orthoHalfW = orthoHalfH * aspect;
                }
                else
                {
                    tanHalfV = Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad);
                    tanHalfH = tanHalfV * aspect;
                    // The camera looks down the street tilted down a little (CameraFollow2D.pitch).
                    Vector3 f = t.forward;
                    pitchTan = f.z > 0.01f ? -f.y / f.z : 0f;
                }
            }

            var level = Core.LevelManager.Current;
            hasKid = level != null && level.kid != null;
            if (hasKid)
            {
                kid = level.kid.transform.position;
                kidSpeed = Mathf.Abs(level.kid.SpeedX);
            }
            hasBall = level != null && level.ball != null;
            if (hasBall)
            {
                ball = level.ball.transform.position;
                float dt = Time.deltaTime;
                ballSpeed = dt > 0f ? Vector3.Distance(ball, lastBall) / dt : 0f;
                if (ballSpeed > 40f) ballSpeed = 0f;   // a respawn, not a kick
                lastBall = ball;
            }
        }

        /// <summary>False when there is no camera (then everything counts as far off-screen).</summary>
        public static bool Valid { get { Refresh(); return valid; } }

        public static float CameraX { get { Refresh(); return camPos.x; } }

        /// <summary>Half the view's width at depth z (world units).</summary>
        public static float HalfWidthAt(float z)
        {
            Refresh();
            if (!valid) return 0f;
            if (ortho) return orthoHalfW;
            return Mathf.Max(0.5f, z - camPos.z) * tanHalfH;
        }

        public static float LeftEdge(float z) { return CameraX - HalfWidthAt(z); }
        public static float RightEdge(float z) { return CameraX + HalfWidthAt(z); }

        /// <summary>The height the middle of the view looks at, at depth z.</summary>
        public static float CenterYAt(float z)
        {
            Refresh();
            if (!valid || ortho) return camPos.y;
            return camPos.y - Mathf.Max(0f, z - camPos.z) * pitchTan;
        }

        /// <summary>Half the view's height at depth z.</summary>
        public static float HalfHeightAt(float z)
        {
            Refresh();
            if (!valid) return 0f;
            if (ortho) return orthoHalfH;
            return Mathf.Max(0.5f, z - camPos.z) * tanHalfV;
        }

        /// <summary>Is x (at depth z) inside the view's width, widened by margin either side?</summary>
        public static bool InViewX(float x, float z, float margin)
        {
            Refresh();
            if (!valid) return false;
            return Mathf.Abs(x - camPos.x) <= HalfWidthAt(z) + margin;
        }

        /// <summary>Is the point (x, y, z) in view, the view widened by margin all round?</summary>
        public static bool InView(float x, float y, float z, float margin)
        {
            if (!InViewX(x, z, margin)) return false;
            return Mathf.Abs(y - CenterYAt(z)) <= HalfHeightAt(z) + margin;
        }

        /// <summary>How far x lies outside the view's sides at depth z (negative while inside).</summary>
        public static float OutsideBy(float x, float z)
        {
            Refresh();
            if (!valid) return 1000f;
            return Mathf.Abs(x - camPos.x) - HalfWidthAt(z);
        }

        public static bool HasKid { get { Refresh(); return hasKid; } }
        public static Vector3 KidPosition { get { Refresh(); return kid; } }
        /// <summary>The kid's run speed along the street (m/s).</summary>
        public static float KidSpeed { get { Refresh(); return kidSpeed; } }
        public static bool HasBall { get { Refresh(); return hasBall; } }
        public static Vector3 BallPosition { get { Refresh(); return ball; } }
        public static float BallSpeed { get { Refresh(); return ballSpeed; } }

        /// <summary>
        /// How close the kid (or a fast ball) is to (x, z) on the ground plane: what makes birds
        /// and small animals start. Large when there is no kid.
        /// </summary>
        public static float ThreatDistance(float x, float z)
        {
            Refresh();
            float d = 1000f;
            if (hasKid)
            {
                float dx = x - kid.x, dz = z - kid.z;
                d = Mathf.Sqrt(dx * dx + dz * dz);
            }
            if (hasBall && ballSpeed > 3f)
            {
                float dx = x - ball.x, dz = z - ball.z;
                d = Mathf.Min(d, Mathf.Sqrt(dx * dx + dz * dz) + 0.5f);
            }
            return d;
        }

        /// <summary>The x the kid is at (or the camera's, without a kid): which way is "away".</summary>
        public static float ThreatX { get { Refresh(); return hasKid ? kid.x : camPos.x; } }
    }
}
