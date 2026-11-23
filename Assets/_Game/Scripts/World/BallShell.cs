using System.Collections.Generic;
using DribbleToSchool.Core;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Colliders for the ball only, where a piece's visible model crosses the ball's plane beyond its designed colliders (built
    /// with each level: Editor/LevelBuildKit.BallShells, docs/LEARNINGS.md E18). The ball bounces off the sweeper's cab, a cart's
    /// body, a canopy's edge; the kid passes as the level was tuned (its jumps, slides and rides are the designed colliders'), so
    /// these colliders ignore the kid's, again whenever the kid's collider changes shape for a slide.
    /// </summary>
    public class BallShell : MonoBehaviour
    {
        readonly List<Collider2D> own = new List<Collider2D>();
        static readonly List<Collider2D> kidColliders = new List<Collider2D>();
        KidController kid;

        void Start()
        {
            GetComponents(own);
            var level = LevelManager.Current;
            kid = level != null ? level.kid : null;
            if (kid == null) return;
            IgnoreKid();
            kid.ShapeChanged += IgnoreKid;
        }

        void OnDestroy()
        {
            if (kid != null) kid.ShapeChanged -= IgnoreKid;
        }

        void IgnoreKid()
        {
            if (kid == null) return;
            kid.GetComponentsInChildren(kidColliders);
            for (int k = 0; k < kidColliders.Count; k++)
                for (int i = 0; i < own.Count; i++)
                    if (own[i] != null) Physics2D.IgnoreCollision(own[i], kidColliders[k], true);
            kidColliders.Clear();
        }
    }
}
