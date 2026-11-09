using System.Collections.Generic;
using DribbleToSchool.Coop.Net;
using UnityEngine;

namespace DribbleToSchool.Coop
{
    /// <summary>
    /// Pretend phones for trying Co-op in the editor, where there is no Bluetooth: each bot is a real CoopSession on the
    /// same pretend radio as the player (Net/InMemoryRadio), so the lobby, the stage choice, the countdown, the race, the
    /// ghosts, the standings and the drop-outs all run through the real code. Bots join the player's lobby (Host) or host one
    /// for the player to find (Join), get ready once the player is, and run each leg at their own steady pace. The race HUD's
    /// editor buttons send a bot out of range, bring it back, or switch the player's own pretend Bluetooth off.
    /// </summary>
    public sealed class CoopBots
    {
        sealed class Bot
        {
            public CoopSession session;
            public InMemoryLink link;
            public bool joining, host;
            public double readyAt;
            public float speed;
            public int leg;
            public float x;
            public double lastTick;
            public bool loadedReported;
            public bool finished;
        }

        /// <summary>A bot's leg is this long when the player is not on it (a level's street is about this long).</summary>
        const float DefaultLegLength = 150f;
        static readonly string[] Names = { "Sam", "", "Sam" };   // the same name twice (tags tell them apart), and a default one

        readonly InMemoryRadio radio;
        readonly ICoopClock clock;
        readonly List<Bot> bots = new List<Bot>();
        readonly System.Random random = new System.Random();

        public CoopBots(InMemoryRadio radio, ICoopClock clock)
        {
            this.radio = radio;
            this.clock = clock;
        }

        public int Count { get { return bots.Count; } }

        Bot Make(int i)
        {
            var link = radio.CreateDevice("bot" + i + "_" + random.Next(100000));
            var bot = new Bot
            {
                link = link,
                session = new CoopSession(link, clock, (uint)random.Next(1, int.MaxValue), Names[i % Names.Length], (byte)((i + 1) % Core.PlayerRoster.All.Length)),
                speed = 3.8f + (float)random.NextDouble() * 1.6f,
            };
            bots.Add(bot);
            return bot;
        }

        /// <summary>Bots come to the player's lobby, one after another.</summary>
        public void JoinLobby(int count)
        {
            Clear();
            for (int i = 0; i < count; i++)
            {
                var bot = Make(i);
                bot.joining = true;
                bot.readyAt = clock.NowMs + 1500 + i * 900;
                bot.session.Browse();
            }
        }

        /// <summary>One bot hosts a lobby the player can find with Join; the others join it.</summary>
        public void HostLobby(int count)
        {
            Clear();
            var host = Make(0);
            host.host = true;
            host.session.Host();
            for (int i = 1; i < count; i++)
            {
                var bot = Make(i);
                bot.joining = true;
                bot.readyAt = clock.NowMs + 1500 + i * 900;
                bot.session.Browse();
            }
        }

        public void Clear()
        {
            foreach (var b in bots) { b.session.Shutdown(); b.link.Shutdown(); }
            bots.Clear();
        }

        /// <summary>Send one racing bot out of range (it is disqualified if it stays away too long).</summary>
        public void DropOne()
        {
            foreach (var b in bots)
                if (b.session.InSession && b.session.MyStatus == PlayerStatus.Racing) { radio.Isolate(b.link); return; }
            if (bots.Count > 0) radio.Isolate(bots[0].link);
        }

        /// <summary>Make the bot that hosts leave (the race goes on with a new host).</summary>
        public void HostLeaves()
        {
            foreach (var b in bots)
                if (b.session.IsHost) { b.session.Leave(); return; }
        }

        public void BringBack()
        {
            foreach (var b in bots) radio.Rejoin(b.link);
        }

        public void Tick(CoopRaceMode race)
        {
            double now = clock.NowMs;
            foreach (var b in bots)
            {
                b.session.Tick();
                var s = b.session;
                if (b.joining && !s.InSession)
                {
                    foreach (var room in s.Rooms)
                        if (room.beacon.phase == RoomPhase.Lobby && room.beacon.players < CoopRules.MaxPlayers && now >= b.readyAt - 1000)
                        {
                            s.Join(room.address);
                            break;
                        }
                    continue;
                }
                if (!s.InSession) continue;
                b.joining = false;

                if (s.Phase == SessionPhase.Lobby || s.Phase == SessionPhase.Starting)
                {
                    b.leg = 0; b.x = 0f; b.finished = false; b.loadedReported = false;
                    // Ready a moment after joining, and again after someone changes the stage (that un-readies everyone).
                    if (!s.MyReady && now >= b.readyAt && HasCompany(s)) { s.SetReady(true); b.readyAt = now + 1200; }
                    if (!s.MyReady && now > b.readyAt) b.readyAt = now + 1200;
                }
                else if (s.Phase == SessionPhase.Loading)
                {
                    if (!b.loadedReported) { b.loadedReported = true; s.ReportLoaded(s.RaceId); }
                    b.lastTick = now;
                }
                else if (s.Phase == SessionPhase.Racing && s.RaceStarted && s.MyStatus == PlayerStatus.Racing && !b.finished)
                {
                    float dt = (float)((now - b.lastTick) / 1000.0);
                    b.lastTick = now;
                    var legs = race != null && race.Route != null ? race.LegCount : 3;
                    float length = race != null && race.Leg == b.leg && CoopLevelLink.Current != null ? CoopLevelLink.Current.LegLength : DefaultLegLength;
                    b.x += b.speed * Mathf.Clamp(dt, 0f, 0.25f);
                    if (b.x >= length)
                    {
                        b.leg++;
                        b.x = 0f;
                        if (b.leg >= legs) { b.finished = true; s.ReportFinished(); continue; }
                    }
                    s.ReportLeg(b.leg, (b.leg + b.x / length) / legs);
                    var link = CoopLevelLink.Current;
                    float startX = link != null ? link.StartX : 0f;
                    float groundY = link != null ? link.StartY : 0f;
                    s.ReportMotion(new CoopMotion
                    {
                        x = startX + b.x,
                        y = groundY,
                        vx = b.speed,
                        flags = CoopMotion.Grounded | CoopMotion.FacingRight | CoopMotion.InPlay,
                        ballDx = 0.55f,
                        ballDy = -0.35f,
                        progress = (b.leg + b.x / length) / legs,
                    });
                }
                else b.lastTick = now;
            }
        }

        /// <summary>Someone else is in the lobby (a bot readies once it has company; the race starts when the player readies too).</summary>
        static bool HasCompany(CoopSession s)
        {
            int others = 0;
            foreach (var p in s.Players)
            {
                if (p.uid == s.Uid) continue;
                others++;
            }
            return others > 0;
        }
    }
}
