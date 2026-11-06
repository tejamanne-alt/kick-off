namespace DribbleToSchool.Core
{
    /// <summary>
    /// Anything that must go back to its starting state when a level restarts
    /// (moving hazards, gates, crates). Respawning at a checkpoint does not reset these; what must also go back then is an
    /// <see cref="IResetAhead"/>.
    /// </summary>
    public interface IResettable
    {
        void ResetState();
    }
}
