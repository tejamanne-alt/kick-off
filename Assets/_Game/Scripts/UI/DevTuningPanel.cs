using DribbleToSchool.Ball;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// Developer-only live tuning sliders (IMGUI). Available in the editor and
    /// development builds; toggle with Tab or the HUD's Tune button.
    /// </summary>
    public class DevTuningPanel : MonoBehaviour
    {
        public KidController kid;
        public BallController ball;
        public float referenceHeight = 720f;
        public bool visible;

        const float PanelWidth = 380f;
        Vector2 scroll;
        GUIStyle label;

        public static bool Available { get { return Application.isEditor || Debug.isDebugBuild; } }

        /// <summary>Screen rect (bottom-left origin) covered by the panel, for input blocking.</summary>
        public Rect ScreenRect
        {
            get
            {
                float scale = Screen.height / referenceHeight;
                return new Rect(0f, 0f, PanelWidth * scale, Screen.height);
            }
        }

        void Update()
        {
            if (!Available) return;
            var input = GameInput.Instance;
            if (input != null && input.DebugTogglePressed) visible = !visible;
        }

        void OnGUI()
        {
            if (!Available || !visible) return;
            float scale = Screen.height / referenceHeight;
            GUI.matrix = Matrix4x4.Scale(new Vector3(scale, scale, 1f));
            float h = referenceHeight;
            if (label == null)
            {
                label = new GUIStyle(GUI.skin.label) { fontSize = 18 };
                label.normal.textColor = Color.white;
            }

            GUI.color = new Color(0f, 0f, 0f, 0.75f);
            GUI.DrawTexture(new Rect(0f, 0f, PanelWidth, h), Texture2D.whiteTexture);
            GUI.color = Color.white;
            GUILayout.BeginArea(new Rect(10f, 10f, PanelWidth - 20f, h - 20f));
            scroll = GUILayout.BeginScrollView(scroll);

            var p = kid.tuning;
            var b = ball.tuning;
            GUI.changed = false;

            GUILayout.Label("KID", label);
            p.runSpeed = Slider("Run speed", p.runSpeed, 1f, 9f);
            p.acceleration = Slider("Acceleration", p.acceleration, 2f, 40f);
            p.jumpVelocity = Slider("Jump velocity", p.jumpVelocity, 4f, 16f);
            p.gravityScale = Slider("Gravity", p.gravityScale, 1f, 6f);
            p.jumpCutMultiplier = Slider("Short-hop cut", p.jumpCutMultiplier, 0f, 1f);
            p.fallGravityMultiplier = Slider("Fall gravity x", p.fallGravityMultiplier, 1f, 3f);
            p.airJumps = Mathf.RoundToInt(Slider("Air jumps", p.airJumps, 0f, 2f));
            p.airJumpVelocity = Slider("Air jump velocity", p.airJumpVelocity, 3f, 12f);
            p.slideDuration = Slider("Slide time", p.slideDuration, 0.3f, 1.2f);
            p.slideSpeedBoost = Slider("Slide boost x", p.slideSpeedBoost, 1f, 2f);
            p.slideFriction = Slider("Slide friction", p.slideFriction, 0f, 10f);
            p.slideMinSpeed = Slider("Slide min speed", p.slideMinSpeed, 0.5f, 5f);

            GUILayout.Space(8f);
            GUILayout.Label("BALL", label);
            b.gravityScale = Slider("Gravity", b.gravityScale, 0.5f, 4f);
            b.bounciness = Slider("Bounciness", b.bounciness, 0f, 1f);
            b.friction = Slider("Friction", b.friction, 0f, 1f);
            b.rollingResistance = Slider("Rolling resistance", b.rollingResistance, 0f, 2f);
            b.linearDamping = Slider("Air drag", b.linearDamping, 0f, 1f);

            GUILayout.Space(8f);
            GUILayout.Label("DRIBBLE", label);
            b.reachRadius = Slider("Reach", b.reachRadius, 0.3f, 1.5f);
            b.dribbleLeadSpeed = Slider("Lead speed", b.dribbleLeadSpeed, 0.2f, 4f);
            b.touchLift = Slider("Touch lift", b.touchLift, 0f, 4f);
            b.autoTouchVariance = Slider("Auto-touch sloppiness", b.autoTouchVariance, 0f, 0.5f);
            b.perfectTouchBand.x = Slider("Perfect band min", b.perfectTouchBand.x, 0f, 1f);
            b.perfectTouchBand.y = Slider("Perfect band max", b.perfectTouchBand.y, b.perfectTouchBand.x, 1.5f);
            b.juggleUpSpeed = Slider("Juggle pop", b.juggleUpSpeed, 2f, 10f);

            GUILayout.Space(8f);
            GUILayout.Label("KICK", label);
            b.minKickSpeed = Slider("Min kick speed", b.minKickSpeed, 0f, 10f);
            b.maxKickSpeed = Slider("Max kick speed", b.maxKickSpeed, b.minKickSpeed, 25f);
            b.maxDragDistance = Slider("Full-power drag", b.maxDragDistance, 0.5f, 5f);
            b.kickReach = Slider("Kick reach", b.kickReach, 0.3f, 2f);
            b.aimTimeScale = Slider("Aim slow-mo", b.aimTimeScale, 0.1f, 1f);
            b.previewDuration = Slider("Preview seconds", b.previewDuration, 0.1f, 1.5f);

            if (GUI.changed)
            {
                kid.ApplyTuning();
                ball.ApplyTuning();
#if UNITY_EDITOR
                UnityEditor.EditorUtility.SetDirty(p);
                UnityEditor.EditorUtility.SetDirty(b);
#endif
            }

            GUILayout.Space(8f);
            GUILayout.Label(Application.isEditor ? "Editor: saved to the tuning assets." : "Device: lasts until the app closes.", label);
            GUILayout.EndScrollView();
            GUILayout.EndArea();
        }

        float Slider(string name, float value, float min, float max)
        {
            GUILayout.BeginHorizontal();
            GUILayout.Label(name + "  " + value.ToString("0.00"), label, GUILayout.Width(190f));
            value = GUILayout.HorizontalSlider(value, min, max, GUILayout.Width(150f), GUILayout.Height(28f));
            GUILayout.EndHorizontal();
            return value;
        }
    }
}
