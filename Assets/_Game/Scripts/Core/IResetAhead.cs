namespace DribbleToSchool.Core
{
    /// <summary>
    /// Something that also goes back to how it started when the kid is sent back to a checkpoint behind it (a crate knocked
    /// into the way, rolling pipes): so going back to a checkpoint always finds the way ahead as the level was built.
    /// </summary>
    public interface IResetAhead
    {
        /// <summary>The kid is back at the checkpoint at <paramref name="checkpointX"/>: put back what lies ahead of it.</summary>
        void ResetAhead(float checkpointX);
    }
}
