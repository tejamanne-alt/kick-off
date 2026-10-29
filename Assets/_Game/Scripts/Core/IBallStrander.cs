using UnityEngine;

namespace DribbleToSchool.Core
{
    /// <summary>
    /// Something that can leave the ball where the kid can never get it back: a closed gate
    /// the ball has gone over, or a high surface the ball has come to rest on. The level asks
    /// every one of them each frame; when one says yes for a moment, the run goes back to the
    /// last checkpoint and says why.
    /// </summary>
    public interface IBallStrander
    {
        bool Strands(Vector2 ball, Vector2 kid);
    }
}
