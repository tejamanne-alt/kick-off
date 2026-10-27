namespace DribbleToSchool.Core
{
    /// <summary>
    /// Anything that must go back to its starting state when a level restarts
    /// (moving hazards, gates, crates). Respawning at a checkpoint does not reset.
    /// </summary>
    public interface IResettable
    {
        void ResetState();
    }
}
