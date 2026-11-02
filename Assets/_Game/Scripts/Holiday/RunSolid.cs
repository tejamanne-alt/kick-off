using UnityEngine;

namespace DribbleToSchool.Holiday
{
    /// <summary>
    /// Marks something solid in the kid's way (put on the top-level object of a crate, a wall, a car,
    /// a barrier to slide under...). The director reads a head-on touch of its colliders as a crash,
    /// counts it as cleared once the kid is past it, and scores a near miss for passing close.
    /// </summary>
    public class RunSolid : MonoBehaviour
    {
        [Tooltip("Hitting it head-on ends the run.")]
        public bool deadly = true;

        /// <summary>The director has counted this one as passed.</summary>
        public bool Cleared { get; set; }

        /// <summary>The smallest gap between the kid and this obstacle so far (metres): what makes a near miss.</summary>
        public float Closest { get; set; }

        Collider2D[] colliders;

        /// <summary>The solid colliders (triggers excluded) of this obstacle.</summary>
        public Collider2D[] Colliders
        {
            get
            {
                if (colliders == null)
                {
                    var all = GetComponentsInChildren<Collider2D>(true);
                    var solid = new System.Collections.Generic.List<Collider2D>();
                    foreach (var c in all) if (!c.isTrigger) solid.Add(c);
                    colliders = solid.ToArray();
                }
                return colliders;
            }
        }

        /// <summary>World x of the obstacle's middle.</summary>
        public float CenterX
        {
            get
            {
                var cs = Colliders;
                return cs.Length > 0 ? cs[0].bounds.center.x : transform.position.x;
            }
        }

        /// <summary>World x of its left-hand edge.</summary>
        public float LeftX
        {
            get
            {
                float left = transform.position.x;
                var cs = Colliders;
                if (cs.Length > 0) left = cs[0].bounds.min.x;
                foreach (var c in cs) left = Mathf.Min(left, c.bounds.min.x);
                return left;
            }
        }

        /// <summary>World x of its right-hand edge: the kid is past it once beyond this.</summary>
        public float RightX
        {
            get
            {
                float right = transform.position.x;
                foreach (var c in Colliders) right = Mathf.Max(right, c.bounds.max.x);
                return right;
            }
        }

        protected virtual void OnEnable()
        {
            Cleared = false;
            Closest = float.MaxValue;
            var director = HolidayRunDirector.Current;
            if (director != null) director.Register(this);
        }

        protected virtual void OnDisable()
        {
            var director = HolidayRunDirector.Current;
            if (director != null) director.Unregister(this);
        }
    }
}
