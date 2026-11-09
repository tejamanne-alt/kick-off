using System.Collections.Generic;

namespace DribbleToSchool.Coop.Net
{
    /// <summary>
    /// Keeps late native events away from the session. The Bluetooth stacks answer on their own threads and in their own
    /// time: a disconnection, a last packet or a "hosting started" can arrive after the game has already moved on (left that
    /// host and connected to another, stopped hosting and started again, kicked a player). Read as current, such an event
    /// would drop the new connection or put an old packet into it.
    ///
    /// So every connection attempt and every hosting run gets a number (a generation), handed to the plugin when it starts.
    /// The plugin writes it into the state byte of every event about that connection or run (the state byte is only
    /// otherwise used by Radio events), and anything with an old number is dropped here. A kicked player's events are
    /// dropped too: the link contract says Kick, StopHost and Disconnect raise no event on the caller's side.
    /// Used by <c>IosBleLink</c> and <c>AndroidBleLink</c>; pure C#, tested offline.
    /// </summary>
    public sealed class LinkEventFilter
    {
        byte hostGen, connectGen;
        bool hosting, connecting;
        readonly HashSet<int> kicked = new HashSet<int>();

        /// <summary>A hosting run starts: the number its events will carry.</summary>
        public byte StartHost()
        {
            hostGen++;
            hosting = true;
            kicked.Clear();
            return hostGen;
        }

        public void StopHost()
        {
            hostGen++;
            hosting = false;
            kicked.Clear();
        }

        public void Kick(int peer)
        {
            if (peer > 0) kicked.Add(peer);
        }

        /// <summary>A connection attempt starts (any earlier one is over): the number its events will carry.</summary>
        public byte Connect()
        {
            connectGen++;
            connecting = true;
            return connectGen;
        }

        public void Disconnect()
        {
            connectGen++;
            connecting = false;
        }

        /// <summary>True when <paramref name="e"/> belongs to what the game is doing now (its state byte is then cleared, except on Radio events).</summary>
        public bool Pass(ref LinkEvent e)
        {
            switch (e.type)
            {
                case LinkEventType.Radio:
                case LinkEventType.Found:
                case LinkEventType.PacketSize:
                    return true;

                case LinkEventType.HostStarted:
                case LinkEventType.HostFailed:
                    if (!hosting || (byte)e.state != hostGen) return false;
                    if (e.type == LinkEventType.HostFailed) hosting = false;
                    e.state = RadioState.Unknown;
                    return true;

                case LinkEventType.Connected:
                case LinkEventType.Disconnected:
                case LinkEventType.Data:
                case LinkEventType.ConnectFailed:
                    if (e.peer == 0)
                    {
                        if (!connecting || (byte)e.state != connectGen) return false;
                        if (e.type == LinkEventType.Disconnected || e.type == LinkEventType.ConnectFailed) connecting = false;
                    }
                    else
                    {
                        if (e.peer < 0 || e.type == LinkEventType.ConnectFailed) return false;
                        if (!hosting || (byte)e.state != hostGen) return false;
                        if (kicked.Contains(e.peer))
                        {
                            if (e.type == LinkEventType.Disconnected) kicked.Remove(e.peer);
                            return false;
                        }
                    }
                    e.state = RadioState.Unknown;
                    return true;

                default:
                    return false;   // (an event this version doesn't know)
            }
        }
    }
}
