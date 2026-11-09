#if UNITY_INCLUDE_TESTS
using System;
using System.Collections.Generic;
using DribbleToSchool.Coop;
using DribbleToSchool.Coop.Net;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// Whole co-op lobbies and races between pretend phones on an in-memory radio (Coop/Net/InMemoryRadio): joining, the
    /// stage chosen by any player, the synced start, finishing order, players dropping out (disqualified after the grace
    /// period and listed last), coming back within it, the winner leaving, and the host changing hands. Pure C#: runs
    /// without Unity's native side.
    /// </summary>
    public class CoopSessionTests
    {
        /// <summary>The test room for the other test classes (chaos).</summary>
        public sealed class RoomHandle
        {
            readonly Room room;
            public RoomHandle(int count, double latency) { room = new Room(count) { }; room.radio.LatencyMs = latency; }
            public CoopSession this[int i] { get { return room.phones[i]; } }
            public InMemoryRadio Radio { get { return room.radio; } }
            public List<InMemoryLink> Links { get { return room.links; } }
            public HashSet<int> Frozen { get { return room.frozen; } }
            public void Gather() { room.Gather(); }
            public void StartRace() { room.StartRace(); }
            public void Move(double ms) { room.Move(ms); }
        }

        /// <summary>One phone's own clock: the room's, plus whatever it lost (a Stopwatch stands still while a phone sleeps).</summary>
        sealed class PhoneClock : ICoopClock
        {
            readonly ICoopClock room;
            public double lost;
            public PhoneClock(ICoopClock room) { this.room = room; }
            public double NowMs { get { return room.NowMs - lost; } }
        }

        /// <summary>A few phones on one radio, ticked together.</summary>
        sealed class Room
        {
            public readonly ManualClock clock = new ManualClock { NowMs = 1000 };
            public readonly List<PhoneClock> clocks = new List<PhoneClock>();
            public readonly InMemoryRadio radio;
            public readonly List<CoopSession> phones = new List<CoopSession>();
            public readonly List<InMemoryLink> links = new List<InMemoryLink>();
            public readonly List<List<CoopNotice>> notices = new List<List<CoopNotice>>();
            /// <summary>Phones whose app is frozen (a scene loading, a phone call): not ticked, so they neither hear nor send.</summary>
            public readonly HashSet<int> frozen = new HashSet<int>();

            public Room(int count, int packetSize = 20)
            {
                radio = new InMemoryRadio(clock) { PacketSize = packetSize };
                for (int i = 0; i < count; i++)
                {
                    var link = radio.CreateDevice("phone" + i);
                    var own = new PhoneClock(clock);
                    clocks.Add(own);
                    var session = new CoopSession(link, own, (uint)(1000 + i * 7919), i == 0 ? "Hana" : "", (byte)i, 42 + i);
                    var list = new List<CoopNotice>();
                    session.Noticed += n => list.Add(n);
                    links.Add(link);
                    phones.Add(session);
                    notices.Add(list);
                }
            }

            public CoopSession this[int i] { get { return phones[i]; } }

            public void Run(double ms, double step = 16)
            {
                for (double t = 0; t < ms; t += step)
                {
                    clock.Advance(step);
                    for (int i = 0; i < phones.Count; i++) if (!frozen.Contains(i)) phones[i].Tick();
                }
            }

            /// <summary>Phone 0 hosts; every other phone finds it and joins.</summary>
            public void Gather()
            {
                phones[0].Host();
                Run(200);
                for (int i = 1; i < phones.Count; i++)
                {
                    phones[i].Browse();
                    Run(400);
                    CoopRoom found = null;
                    foreach (var r in phones[i].Rooms) found = r;
                    Assert.IsNotNull(found, "phone " + i + " should hear the lobby");
                    phones[i].Join(found.address);
                    Run(600);
                    Assert.AreEqual(ConnectionState.Joined, phones[i].Connection, "phone " + i + " joined");
                }
                Run(1500);
            }

            /// <summary>Everyone ready, through the countdown and the loading to the race under way.</summary>
            public void StartRace()
            {
                foreach (var p in phones) if (p.InSession) p.SetReady(true);
                Run(CoopTiming.StartCountdown + 600);
                Assert.AreEqual(SessionPhase.Loading, phones[0].Phase, "loading after the countdown");
                foreach (var p in phones) if (p.InSession) p.ReportLoaded(p.RaceId);
                Run(800);
                Assert.AreEqual(SessionPhase.Racing, phones[0].Phase);
                Run(CoopTiming.RaceCountdown + 500);
                foreach (var p in phones) if (p.InSession) Assert.IsTrue(p.RaceStarted, "the race has started on every phone");
            }

            /// <summary>Every phone still racing reports a little motion, as the game does each frame.</summary>
            public void Move(double ms)
            {
                for (double t = 0; t < ms; t += 100)
                {
                    for (int i = 0; i < phones.Count; i++)
                    {
                        var p = phones[i];
                        if (!frozen.Contains(i) && p.InSession && p.MyStatus == PlayerStatus.Racing)
                            p.ReportMotion(new CoopMotion { x = (float)(p.RaceTimeMs / 200.0), y = 0f, flags = CoopMotion.Grounded, progress = (float)Math.Min(0.9, p.RaceTimeMs / 120000.0) });
                    }
                    Run(100);
                }
            }

            public CoopPlayer On(int phone, int ofPhone)
            {
                return phones[phone].Find(phones[ofPhone].Uid);
            }

            public bool Heard(int phone, NoticeType type)
            {
                return notices[phone].Exists(n => n.type == type);
            }
        }

        // ---------- The lobby ----------

        [Test]
        public void PlayersJoinInSlotOrderWithDefaultNamesAndUniqueTags()
        {
            var room = new Room(4);
            room.Gather();
            var host = room[0];
            Assert.AreEqual(4, host.Players.Count);
            var tags = new HashSet<string>();
            for (int i = 0; i < 4; i++)
            {
                var p = room.On(0, i);
                Assert.AreEqual(i, p.slot, "slots in order of joining");
                Assert.IsTrue(tags.Add(p.tag), "tags differ");
                Assert.AreEqual(CoopRules.TagLength, p.tag.Length);
                // Every phone sees the same lobby.
                for (int j = 1; j < 4; j++) Assert.AreEqual(p.tag, room.On(j, i).tag);
            }
            Assert.AreEqual("Hana", CoopRules.DisplayName(room.On(2, 0), "Player {0}"), "a typed name");
            Assert.AreEqual("Player 3", CoopRules.DisplayName(room.On(1, 2), "Player {0}"), "an untyped name is Player <slot>");
            Assert.IsTrue(room.On(3, 0).isHost);
        }

        [Test]
        public void AFifthPlayerIsTurnedAway()
        {
            var room = new Room(5);
            room[0].Host();
            room.Run(200);
            for (int i = 1; i < 5; i++)
            {
                room[i].Browse();
                room.Run(400);
                foreach (var r in room[i].Rooms) { room[i].Join(r.address); break; }
                room.Run(800);
            }
            Assert.AreEqual(4, room[0].Players.Count);
            Assert.IsFalse(room[4].InSession);
            Assert.IsTrue(room.notices[4].Exists(n => n.type == NoticeType.Rejected && n.code == (int)RejectReason.Full));
        }

        [Test]
        public void TheSameNameTypedTwiceIsToldApartByTheTag()
        {
            var room = new Room(3);
            room.Gather();
            room[1].SetName("Sam");
            room[2].SetName("  Sam ");
            room.Run(1500);
            var a = room.On(0, 1);
            var b = room.On(0, 2);
            Assert.AreEqual("Sam", a.name);
            Assert.AreEqual("Sam", b.name);
            Assert.AreNotEqual(CoopRules.FullName(a, "Player {0}"), CoopRules.FullName(b, "Player {0}"));
        }

        [Test]
        public void AnyPlayerCanChooseTheStageAndEveryoneSeesWho()
        {
            var room = new Room(3);
            room.Gather();
            room[0].SetReady(true);
            room[2].SetReady(true);
            room.Run(500);
            room[2].Select(3, 1);
            room.Run(800);
            for (int i = 0; i < 3; i++)
            {
                Assert.AreEqual(3, room[i].Selection.route, "phone " + i);
                Assert.AreEqual(1, room[i].Selection.addOn);
                Assert.AreEqual(room.On(0, 2).slot, room[i].Selection.chosenBy, "chosen by player 3");
            }
            // A new stage: everyone looks again before the race.
            foreach (var p in room[0].Players) Assert.IsFalse(p.ready);
            Assert.IsFalse(room[2].MyReady);
            // The last choice wins.
            room[1].Select(5, 0);
            room.Run(800);
            Assert.AreEqual(5, room[0].Selection.route);
            Assert.AreEqual(5, room[2].Selection.route);
        }

        [Test]
        public void TheRaceStartsOnlyWhenEveryoneIsReadyAndUnreadyingStopsTheCountdown()
        {
            var room = new Room(3);
            room.Gather();
            room[0].SetReady(true);
            room[1].SetReady(true);
            room.Run(CoopTiming.StartCountdown + 1000);
            Assert.AreEqual(SessionPhase.Lobby, room[0].Phase, "one player is not ready");
            room[2].SetReady(true);
            room.Run(1000);
            Assert.AreEqual(SessionPhase.Starting, room[0].Phase);
            Assert.AreEqual(SessionPhase.Starting, room[1].Phase);
            room[1].SetReady(false);
            room.Run(600);
            Assert.AreEqual(SessionPhase.Lobby, room[0].Phase, "un-readying stops the countdown");
        }

        [Test]
        public void ALobbyOfOneCannotStart()
        {
            var room = new Room(1);
            room[0].Host();
            room[0].SetReady(true);
            room.Run(CoopTiming.StartCountdown + 1000);
            Assert.AreEqual(SessionPhase.Lobby, room[0].Phase);
        }

        [Test]
        public void ARandomStageIsResolvedOnceForEveryone()
        {
            var room = new Room(2);
            room.Gather();
            room[1].Select(CoopSelection.Random, CoopSelection.Random);
            room.Run(600);
            room.StartRace();
            var s = room[0].RaceSelection;
            Assert.Less(s.route, room[0].RouteCount);
            Assert.Less(s.addOn, room[0].AddOnCount);
            Assert.AreEqual(s.route, room[1].RaceSelection.route);
            Assert.AreEqual(s.addOn, room[1].RaceSelection.addOn);
        }

        [Test]
        public void TheHostClosingTheLobbySendsEveryoneBack()
        {
            var room = new Room(3);
            room.Gather();
            room[0].Leave();
            room.Run(1500);
            Assert.IsFalse(room[1].InSession);
            Assert.IsFalse(room[2].InSession);
            Assert.IsTrue(room.Heard(1, NoticeType.LobbyClosed));
        }

        // ---------- The race ----------

        [Test]
        public void EveryPhoneCountsTheRaceFromTheSameMoment()
        {
            var room = new Room(4);
            room.radio.LatencyMs = 60;   // a slow link: the clock sync takes the delay out
            room.Gather();
            room.StartRace();
            double hostTime = room[0].RaceTimeMs;
            for (int i = 1; i < 4; i++)
                Assert.AreEqual(hostTime, room[i].RaceTimeMs, 25.0, "phone " + i + "'s race clock");
        }

        [Test]
        public void APhoneWhoseClockStoodStillWhileItSleptIsPutBackOnTheRaceClock()
        {
            foreach (double nap in new[] { 3000.0, 12000.0 })
            {
                var room = new Room(3);
                room.Gather();
                room.StartRace();
                room.Move(2000);
                // Phone 2 sleeps: its app stops, and its clock stands still all the while.
                room.frozen.Add(2);
                room.Run(nap);
                room.clocks[2].lost += nap;
                room.frozen.Remove(2);
                room.Move(4000);
                Assert.AreEqual(room[0].RaceTimeMs, room[2].RaceTimeMs, 50.0, "after a " + nap + " ms sleep, the race clock is everyone's again");
                Assert.AreEqual(PlayerStatus.Racing, room.On(0, 2).status);
            }
        }

        [Test]
        public void TheRaceClockDoesNotTwitchWhenTheHostChanges()
        {
            var room = new Room(3);
            room.radio.LatencyMs = 60;
            room.Gather();
            room.StartRace();
            room.Move(1000);
            double before = room[2].RaceTimeMs - room.clock.NowMs;
            room.radio.SetPower(room.links[0], false);
            room.Move(8000);
            Assert.AreEqual(SessionRole.Host, room[1].Role);
            Assert.AreEqual(before, room[2].RaceTimeMs - room.clock.NowMs, 0.001, "a few milliseconds of estimate are left alone");
        }

        [Test]
        public void TheHostCanRemoveAPlayerWhoThenCannotComeBack()
        {
            var room = new Room(3);
            room.Gather();
            uint uid = room[2].Uid;
            Assert.IsFalse(room[1].RemovePlayer(uid), "only the host can");
            Assert.IsTrue(room[0].RemovePlayer(uid));
            room.Run(2500);
            Assert.IsFalse(room[2].InSession, "sent away");
            Assert.IsTrue(room.notices[2].Exists(n => n.type == NoticeType.Rejected && n.code == (int)RejectReason.Removed), "and told why");
            for (int i = 0; i < 2; i++) Assert.IsNull(room[i].Find(uid), "the seat is free on every phone");
            Assert.AreEqual(2, room[1].Players.Count);
            // Trying again is turned away the same way.
            room.notices[2].Clear();
            room[2].Browse();
            room.Run(800);
            CoopRoom lobby = null;
            foreach (var r in room[2].Rooms) lobby = r;
            Assert.IsNotNull(lobby);
            room[2].Join(lobby.address);
            room.Run(3000);
            Assert.IsFalse(room[2].InSession);
            Assert.IsTrue(room.notices[2].Exists(n => n.type == NoticeType.Rejected && n.code == (int)RejectReason.Removed));
            Assert.AreEqual(2, room[0].Players.Count, "nobody new in the lobby");
            // No removing in a race (its players are only ever listed out or left).
            room.StartRace();
            Assert.IsFalse(room[0].RemovePlayer(room[1].Uid));
        }

        [Test]
        public void AnIosHostThatGlancesAtControlCenterKeepsTheRace()
        {
            foreach (double pause in new[] { 1500.0, 9000.0 })
            {
                var room = new Room(3);
                room[0].KeepHostingWhilePaused = true;
                room.Gather();
                room.StartRace();
                room.Move(1000);
                // The game is paused (no frames) while the radio carries on.
                room[0].SetAppPaused(true);
                room.frozen.Add(0);
                room.Run(pause);
                room.frozen.Remove(0);
                room[0].SetAppPaused(false);
                room.Move(9000);
                int hosts = 0;
                for (int i = 0; i < 3; i++) if (room[i].IsHost) hosts++;
                Assert.AreEqual(1, hosts, "one host after a " + pause + " ms pause");
                if (pause < CoopTiming.HostDeafGrace)
                {
                    Assert.IsTrue(room[0].IsHost, "a glance changes nothing");
                    Assert.IsFalse(room.notices[1].Exists(n => n.type == NoticeType.NewHost), "nobody took over");
                }
                else Assert.IsFalse(room[0].IsHost, "a long pause hands the race over");
                for (int i = 0; i < 3; i++)
                {
                    Assert.AreEqual(3, room[i].Players.Count);
                    Assert.AreEqual(PlayerStatus.Racing, room.On(i, 0).status, "the host's run goes on either way");
                }
            }
        }

        [Test]
        public void ALobbyThatCannotStartAdvertisingIsNoLobby()
        {
            var room = new Room(1);
            room.radio.SetPower(room.links[0], false);
            room.Run(100);
            room[0].Host();
            room.Run(500);
            Assert.IsFalse(room[0].InSession, "back out of the session, not hosting a lobby nobody can find");
            Assert.IsTrue(room.notices[0].Exists(n => n.type == NoticeType.HostFailed), "and told why");
        }

        [Test]
        public void AFinishNobodyHasSeenYetIsSaidToBeAtRisk()
        {
            var room = new Room(2);
            room.Gather();
            room.StartRace();
            room.Move(1500);
            room[1].ReportFinished();
            Assert.IsTrue(room[1].FinishUnconfirmed, "only this phone knows of it");
            Assert.IsFalse(room[0].FinishUnconfirmed);
            room.Move(1000);
            Assert.IsFalse(room[1].FinishUnconfirmed, "the host has listed it");
            room[0].ReportFinished();
            Assert.IsFalse(room[0].FinishUnconfirmed, "a host's own finish goes out with its snapshots");
        }

        [Test]
        public void FinishersArePlacedByTimeAndTheOthersCarryOn()
        {
            var room = new Room(3);
            room.Gather();
            room.StartRace();
            room.Move(2000);
            uint first = room[2].ReportFinished();
            room.Move(1500);
            uint second = room[0].ReportFinished();
            room.Move(800);
            Assert.Less(first, second);
            for (int i = 0; i < 3; i++)
            {
                Assert.AreEqual(PlayerStatus.Finished, room.On(i, 2).status);
                Assert.AreEqual(1, room.On(i, 2).place, "player 3 won, as every phone sees it");
                Assert.AreEqual(2, room.On(i, 0).place);
                Assert.AreEqual(PlayerStatus.Racing, room.On(i, 1).status, "player 2 is still on the way");
                Assert.AreEqual(SessionPhase.Racing, room[i].Phase);
            }
            room[1].ReportFinished();
            room.Run(800);
            Assert.AreEqual(SessionPhase.Over, room[0].Phase);
            Assert.AreEqual(SessionPhase.Over, room[1].Phase);
            Assert.AreEqual(3, room.On(1, 1).place);
        }

        [Test]
        public void TheWinnerLeavingKeepsTheirPlaceAndTheRaceGoesOn()
        {
            var room = new Room(3);
            room.Gather();
            room.StartRace();
            room.Move(1000);
            room[1].ReportFinished();
            room.Move(600);
            room[1].Leave();
            room.Move(3000);
            Assert.IsFalse(room[1].InSession);
            var winner = room.On(0, 1);
            Assert.AreEqual(PlayerStatus.Finished, winner.status, "the winner is still listed as finished");
            Assert.AreEqual(1, winner.place);
            Assert.IsFalse(winner.connected);
            Assert.AreEqual(SessionPhase.Racing, room[0].Phase, "the others carry on");
            room[2].ReportFinished();
            room[0].ReportFinished();
            room.Run(800);
            Assert.AreEqual(SessionPhase.Over, room[2].Phase);
            var standings = CoopRules.Standings(room[2].Players);
            Assert.AreEqual(room[1].Uid, standings[0].uid, "the winner tops the final list");
        }

        [Test]
        public void ARacerOutOfRangeIsDisqualifiedAfterTheGracePeriodAndListedLast()
        {
            var room = new Room(4);
            room.Gather();
            room.StartRace();
            room.Move(1500);
            room.radio.Isolate(room.links[2]);   // player 3 walks off
            room.Move(CoopTiming.RaceGrace + 6000);
            for (int i = 0; i < 4; i++)
            {
                if (i == 2) continue;
                var gone = room.On(i, 2);
                Assert.AreEqual(PlayerStatus.Disconnected, gone.status, "phone " + i + " sees player 3 disqualified");
                Assert.AreEqual(SessionPhase.Racing, room[i].Phase, "the race goes on");
            }
            room[1].ReportFinished();
            room.Move(200);
            var standings = CoopRules.Standings(room[0].Players);
            Assert.AreEqual(room[1].Uid, standings[0].uid);
            Assert.AreEqual(room[2].Uid, standings[standings.Count - 1].uid, "the disqualified player is at the bottom");
            Assert.IsTrue(room.Heard(0, NoticeType.PlayerOut));
        }

        [Test]
        public void BluetoothSwitchedOffBrieflyRejoinsTheRaceWithNothingLost()
        {
            var room = new Room(3);
            room.Gather();
            room.StartRace();
            room.Move(1000);
            room.radio.SetPower(room.links[1], false);
            room.Move(5000);
            Assert.IsTrue(room.Heard(1, NoticeType.RadioOff));
            Assert.IsFalse(room.On(0, 1).connected, "the host noticed");
            room.radio.SetPower(room.links[1], true);
            room.Move(6000);
            Assert.AreEqual(ConnectionState.Joined, room[1].Connection, "back in");
            Assert.IsTrue(room.On(0, 1).connected);
            Assert.AreEqual(PlayerStatus.Racing, room.On(0, 1).status, "within the grace period: still racing");
            Assert.IsTrue(room[0].IsHost, "the host stayed the host");
            room[1].ReportFinished();
            room.Run(600);
            Assert.AreEqual(PlayerStatus.Finished, room.On(2, 1).status);
        }

        [Test]
        public void WhenTheHostGoesTheNextPlayerTakesOverAndTheRaceGoesOn()
        {
            var room = new Room(4);
            room.Gather();
            room.StartRace();
            room.Move(1000);
            room[3].ReportFinished();   // a finish the old host knew about
            room.Move(800);
            room.radio.SetPower(room.links[0], false);   // the host's Bluetooth goes off for good
            room.Move(CoopTiming.ReconnectWindow + CoopTiming.ScanBeforeHost + 8000);
            Assert.IsTrue(room[1].IsHost, "player 2 (the lowest slot left) took over");
            Assert.IsTrue(room.Heard(1, NoticeType.YouAreHost));
            Assert.AreEqual(ConnectionState.Joined, room[2].Connection);
            Assert.AreEqual(ConnectionState.Joined, room[3].Connection);
            Assert.IsTrue(room.On(2, 1).isHost, "everyone sees the new host");
            Assert.AreEqual(PlayerStatus.Finished, room.On(2, 3).status, "the earlier finish survived the change of host");
            Assert.AreEqual(1, room.On(2, 3).place);
            Assert.AreEqual(SessionPhase.Racing, room[2].Phase);
            // The race clock did not jump.
            Assert.AreEqual(room[1].RaceTimeMs, room[2].RaceTimeMs, 30.0);
            // The old host never came back: disqualified after the grace period, the others finish.
            room.Move(CoopTiming.RaceGrace);
            Assert.AreEqual(PlayerStatus.Disconnected, room.On(1, 0).status);
            room[1].ReportFinished();
            room[2].ReportFinished();
            room.Run(800);
            Assert.AreEqual(SessionPhase.Over, room[3].Phase);
            var standings = CoopRules.Standings(room[3].Players);
            Assert.AreEqual(room[3].Uid, standings[0].uid);
            Assert.AreEqual(room[0].Uid, standings[3].uid, "the old host is last");
        }

        [Test]
        public void TheWinningHostLeavingHandsTheRaceOnAndStaysTheWinner()
        {
            var room = new Room(3);
            room.Gather();
            room.StartRace();
            room.Move(1000);
            room[0].ReportFinished();
            room.Move(600);
            room[0].Leave();
            room.Move(8000);
            Assert.IsFalse(room[0].InSession);
            Assert.IsTrue(room[1].IsHost || room[2].IsHost, "someone took over");
            Assert.AreEqual(ConnectionState.Joined, room[room[1].IsHost ? 2 : 1].Connection);
            var host = room.On(2, 0);
            Assert.AreEqual(PlayerStatus.Finished, host.status);
            Assert.AreEqual(1, host.place, "the old host keeps the win");
            room[1].ReportFinished();
            room[2].ReportFinished();
            room.Run(800);
            Assert.AreEqual(SessionPhase.Over, room[1].Phase);
            Assert.AreEqual(room[0].Uid, CoopRules.Standings(room[2].Players)[0].uid);
        }

        [Test]
        public void TwoPlayersOneDropsTheOtherFinishesAlone()
        {
            var room = new Room(2);
            room.Gather();
            room.StartRace();
            room.Move(1000);
            room.radio.Isolate(room.links[1]);
            room.Move(CoopTiming.RaceGrace + 4000);
            Assert.AreEqual(PlayerStatus.Disconnected, room.On(0, 1).status);
            Assert.AreEqual(SessionPhase.Racing, room[0].Phase, "the host carries on alone");
            room[0].ReportFinished();
            room.Run(800);
            Assert.AreEqual(SessionPhase.Over, room[0].Phase);
            Assert.AreEqual(1, room.On(0, 0).place);
        }

        [Test]
        public void APlayerWhoWalkedAwayIsListedOutThenBackInTheRaceWhenTheyReturn()
        {
            var room = new Room(3);
            room.Gather();
            room.StartRace();
            room.Move(1000);
            room.radio.Isolate(room.links[2]);
            room.Move(CoopTiming.RaceGrace + 6000);   // long enough to have tried hosting alone
            Assert.AreEqual(PlayerStatus.Disconnected, room.On(0, 2).status, "listed out while away");
            // (it can't tell it is the one that walked off: it hosts alone, waiting for the others)
            Assert.IsTrue(room[2].Alone || room[2].ListedOut, "its own phone shows it is out of touch");
            room.radio.Rejoin(room.links[2]);
            room.Move(12000);
            Assert.IsTrue(room[0].IsHost, "the original host (more players) keeps the race");
            Assert.IsFalse(room[2].IsHost, "the lone phone handed over");
            Assert.AreEqual(ConnectionState.Joined, room[2].Connection);
            Assert.AreEqual(PlayerStatus.Racing, room.On(0, 2).status, "back in touch: back in the race");
            Assert.AreEqual(PlayerStatus.Racing, room.On(0, 1).status, "nobody else was put out");
            Assert.AreEqual(PlayerStatus.Racing, room.On(0, 0).status, "the lone phone's view of the others didn't win");
            Assert.IsTrue(room.Heard(0, NoticeType.PlayerBack));
            room[2].ReportFinished();
            room.Run(600);
            Assert.AreEqual(PlayerStatus.Finished, room.On(0, 2).status, "their finish counts");
        }

        [Test]
        public void APhoneWithBluetoothOffKnowsItIsListedLastAndIsBackWhenItReturns()
        {
            var room = new Room(3);
            room.Gather();
            room.StartRace();
            room.Move(1000);
            room.radio.SetPower(room.links[2], false);
            room.Move(CoopTiming.RaceGrace + 3000);
            Assert.IsTrue(room[2].ListedOut);
            Assert.IsTrue(room.Heard(2, NoticeType.YouAreOut));
            Assert.AreEqual(PlayerStatus.Disconnected, room.On(0, 2).status);
            room.radio.SetPower(room.links[2], true);
            room.Move(8000);
            Assert.IsFalse(room[2].ListedOut);
            Assert.AreEqual(PlayerStatus.Racing, room.On(1, 2).status);
        }

        [Test]
        public void TwoPlayersSplitAndReunitedBothKeepTheirRuns()
        {
            // Two phones: nobody can tell which one walked away. Neither run may be lost when they meet again.
            var room = new Room(2);
            room.Gather();
            room.StartRace();
            room.Move(1000);
            room.radio.Isolate(room.links[0]);   // the host walks off
            room.Move(CoopTiming.RaceGrace + 8000);
            uint finish = room[1].ReportFinished();   // the other one gets to school meanwhile
            room.Move(2000);
            room.radio.Rejoin(room.links[0]);
            room.Move(20000);
            int hosts = (room[0].IsHost ? 1 : 0) + (room[1].IsHost ? 1 : 0);
            Assert.AreEqual(1, hosts, "one host again");
            for (int i = 0; i < 2; i++)
            {
                Assert.AreEqual(PlayerStatus.Finished, room.On(i, 1).status, "phone " + i + " has the finish");
                Assert.AreEqual(finish, room.On(i, 1).finishMs);
                Assert.AreEqual(PlayerStatus.Racing, room.On(i, 0).status, "phone " + i + ": the walker races on");
            }
            room[0].ReportFinished();
            room.Run(800);
            Assert.AreEqual(SessionPhase.Over, room[1].Phase);
            Assert.AreEqual(room[1].Uid, CoopRules.Standings(room[0].Players)[0].uid);
        }

        [Test]
        public void AFinishMadeWhileOutOfTouchCountsWhenThePhoneIsBack()
        {
            var room = new Room(3);
            room.Gather();
            room.StartRace();
            room.Move(1500);
            room.radio.Isolate(room.links[2]);
            room.Move(5000);
            uint early = room[2].ReportFinished();   // at school, but nobody heard
            room.Move(CoopTiming.RaceGrace);
            room[0].ReportFinished();
            room[1].ReportFinished();
            room.Run(800);
            Assert.AreEqual(SessionPhase.Over, room[0].Phase, "the race ended without them");
            Assert.AreEqual(PlayerStatus.Disconnected, room.On(0, 2).status);
            room.radio.Rejoin(room.links[2]);
            room.Move(12000);
            Assert.AreEqual(PlayerStatus.Finished, room.On(1, 2).status, "their finish arrived");
            Assert.AreEqual(1, room.On(1, 2).place, "and it was the quickest");
            Assert.AreEqual(early, room.On(1, 2).finishMs);
            Assert.AreEqual(SessionPhase.Over, room[0].Phase);
        }

        [Test]
        public void APlayerStillOutWhenTheNextRaceStartsIsGoneFromIt()
        {
            var room = new Room(3);
            room.Gather();
            room.StartRace();
            room.Move(1000);
            room.radio.Isolate(room.links[2]);
            room.Move(CoopTiming.RaceGrace + 4000);
            room[0].ReportFinished();
            room[1].ReportFinished();
            room.Run(800);
            Assert.AreEqual(SessionPhase.Over, room[0].Phase);
            room[0].NewRace();
            room.Run(800);
            Assert.AreEqual(2, room[0].Players.Count, "the absent player's seat went with the race");
            Assert.AreEqual(SessionPhase.Lobby, room[1].Phase);
        }

        [Test]
        public void AfterTheRaceTheHostCanStartAnotherWithTheSamePlayers()
        {
            var room = new Room(2);
            room.Gather();
            room.StartRace();
            room[0].ReportFinished();
            room[1].ReportFinished();
            room.Run(800);
            Assert.AreEqual(SessionPhase.Over, room[1].Phase);
            room[0].NewRace();
            room.Run(800);
            Assert.AreEqual(SessionPhase.Lobby, room[1].Phase);
            foreach (var p in room[1].Players) Assert.AreEqual(PlayerStatus.Lobby, p.status);
            Assert.IsFalse(room[1].MyReady);
            room.StartRace();
            Assert.AreEqual(2, room[1].RaceId);
        }

        [Test]
        public void APlayerWhoDropsOutOfTheLobbyBrieflyKeepsTheirSeatAndTag()
        {
            var room = new Room(3);
            room.Gather();
            var before = room.On(0, 2).Clone();
            room.radio.SetPower(room.links[2], false);
            room.Run(3000);
            Assert.IsFalse(room.On(0, 2).connected, "the host saw them go");
            room.radio.SetPower(room.links[2], true);
            room.Run(5000);
            Assert.AreEqual(ConnectionState.Joined, room[2].Connection);
            var after = room.On(0, 2);
            Assert.IsTrue(after.connected);
            Assert.AreEqual(before.slot, after.slot, "the same seat");
            Assert.AreEqual(before.tag, after.tag, "the same tag");
            Assert.AreEqual(3, room[0].Players.Count);
        }

        [Test]
        public void ALobbyWhoseHostIsGoneForGoodCloses()
        {
            var room = new Room(2);
            room.Gather();
            room.radio.SetPower(room.links[0], false);
            room.Run(CoopTiming.LobbyReconnect + CoopTiming.HeartbeatTimeout + 2000);
            Assert.IsFalse(room[1].InSession);
            Assert.IsTrue(room.Heard(1, NoticeType.LobbyClosed));
        }

        [Test]
        public void AHostWhoseBluetoothBlinksKeepsItsLobby()
        {
            var room = new Room(3);
            room.Gather();
            room.radio.SetPower(room.links[0], false);
            room.Run(2000);
            room.radio.SetPower(room.links[0], true);
            room.Run(6000);
            Assert.AreEqual(ConnectionState.Joined, room[1].Connection);
            Assert.AreEqual(ConnectionState.Joined, room[2].Connection);
            Assert.AreEqual(3, room[0].Players.Count);
            foreach (var p in room[0].Players) Assert.IsTrue(p.connected);
        }

        [Test]
        public void ARacerWhoLeavesIsListedLastAndTheRaceGoesOn()
        {
            var room = new Room(3);
            room.Gather();
            room.StartRace();
            room.Move(1500);
            room[2].Leave();
            room.Move(1500);
            Assert.AreEqual(PlayerStatus.Left, room.On(0, 2).status);
            Assert.AreEqual(PlayerStatus.Left, room.On(1, 2).status);
            Assert.IsTrue(room.Heard(1, NoticeType.PlayerLeft));
            room[1].ReportFinished();
            room.Run(600);
            var standings = CoopRules.Standings(room[0].Players);
            Assert.AreEqual(room[1].Uid, standings[0].uid);
            Assert.AreEqual(room[2].Uid, standings[2].uid, "the one who left is last");
            room[0].ReportFinished();
            room.Run(600);
            Assert.AreEqual(SessionPhase.Over, room[1].Phase);
        }

        [Test]
        public void TheRaceDoesNotWaitForeverForAPhoneThatNeverLoads()
        {
            var room = new Room(3);
            room.Gather();
            foreach (var p in room.phones) p.SetReady(true);
            room.Run(CoopTiming.StartCountdown + 600);
            Assert.AreEqual(SessionPhase.Loading, room[0].Phase);
            room[0].ReportLoaded(room[0].RaceId);
            room[1].ReportLoaded(room[1].RaceId);   // player 3's phone is slow
            room.Run(2000);
            Assert.AreEqual(SessionPhase.Loading, room[0].Phase, "waits for everyone...");
            room.Run(CoopTiming.LoadTimeout);
            Assert.AreEqual(SessionPhase.Racing, room[0].Phase, "...but not forever");
            room.Run(CoopTiming.RaceCountdown + 500);
            Assert.IsTrue(room[2].RaceStarted, "the slow phone races too");
        }

        [Test]
        public void APhoneLoadingASceneSaysSoAndIsNotDroppedMeanwhile()
        {
            var room = new Room(3);
            room.Gather();
            room.StartRace();
            room.Move(1000);
            room[1].ExpectSilence(10000);
            room.Run(200);
            room.frozen.Add(1);   // the next leg loading on a slow phone
            room.Move(8000);
            Assert.IsTrue(room.On(0, 1).connected, "the host waited for it");
            room.frozen.Remove(1);
            room.Move(2000);
            Assert.AreEqual(ConnectionState.Joined, room[1].Connection);
            Assert.IsFalse(room.Heard(0, NoticeType.PlayerLost), "nobody was told it was lost");
        }

        [Test]
        public void AHostLoadingASceneKeepsItsPlayers()
        {
            var room = new Room(3);
            room.Gather();
            room.StartRace();
            room.Move(1000);
            room[0].ExpectSilence(10000);
            room.Run(200);
            room.frozen.Add(0);
            room.Move(8000);
            room.frozen.Remove(0);
            room.Move(2000);
            Assert.IsTrue(room[0].IsHost);
            Assert.AreEqual(ConnectionState.Joined, room[1].Connection);
            Assert.AreEqual(ConnectionState.Joined, room[2].Connection);
            Assert.IsFalse(room.Heard(1, NoticeType.ConnectionLost), "the players never took it for lost");
        }

        [Test]
        public void AHostWhoseBluetoothStaysOffStepsDownAndRejoinsTheNewHost()
        {
            var room = new Room(3);
            room.Gather();
            room.StartRace();
            room.Move(1000);
            room.radio.SetPower(room.links[0], false);
            room.Move(12000);
            Assert.IsFalse(room[0].IsHost, "it stopped being the host");
            Assert.IsTrue(room[1].IsHost, "the next seat took over");
            room.radio.SetPower(room.links[0], true);
            room.Move(8000);
            Assert.AreEqual(ConnectionState.Joined, room[0].Connection, "it joined the new host");
            for (int i = 0; i < 3; i++)
                foreach (var p in room[1].Players) Assert.AreEqual(PlayerStatus.Racing, p.status, "nobody is out: " + p);
        }

        [Test]
        public void AHostPutInTheBackgroundHandsTheRaceOver()
        {
            var room = new Room(3);
            room.Gather();
            room.StartRace();
            room.Move(1000);
            room[0].SetAppPaused(true);
            room.frozen.Add(0);
            room.Move(12000);
            Assert.IsTrue(room[1].IsHost, "the others took over at once rather than wait for a host in the background");
            room.frozen.Remove(0);
            room[0].SetAppPaused(false);
            room.Move(8000);
            Assert.IsFalse(room[0].IsHost);
            Assert.AreEqual(ConnectionState.Joined, room[0].Connection);
            Assert.AreEqual(PlayerStatus.Racing, room.On(1, 0).status, "back in time: still racing");
        }

        [Test]
        public void AHostThatKeepsAdvertisingButNeverAnswersIsGivenUp()
        {
            var room = new Room(3);
            room.Gather();
            room.StartRace();
            room.Move(1000);
            room.frozen.Add(0);   // frozen without a word: its radio still advertises the lobby (Android in the background)
            room.Move(30000);
            Assert.IsTrue(room[1].IsHost || room[2].IsHost, "someone took over");
            Assert.AreEqual(ConnectionState.Joined, room[room[1].IsHost ? 2 : 1].Connection);
        }

        [Test]
        public void AFirstJoinThatFailsIsTriedAgain()
        {
            var room = new Room(2);
            room[0].Host();
            room.Run(200);
            room[1].Browse();
            room.Run(400);
            room.radio.FailConnects = 2;   // Android's status 133, twice
            foreach (var r in room[1].Rooms) { room[1].Join(r.address); break; }
            room.Run(4000);
            Assert.AreEqual(ConnectionState.Joined, room[1].Connection);
            Assert.IsFalse(room.Heard(1, NoticeType.ConnectFailed));
        }

        [Test]
        public void APhoneWhoseGameListsTheContentDifferentlyIsTurnedAway()
        {
            var room = new Room(2);
            room[0].ContentHash = 111;
            room[1].ContentHash = 222;
            room[0].Host();
            room.Run(200);
            room[1].Browse();
            room.Run(400);
            foreach (var r in room[1].Rooms) { room[1].Join(r.address); break; }
            room.Run(2000);
            Assert.IsFalse(room[1].InSession);
            Assert.IsTrue(room.notices[1].Exists(n => n.type == NoticeType.Rejected && n.code == (int)RejectReason.Version));
            Assert.AreEqual(1, room[0].Players.Count);
        }

        [Test]
        public void GhostsGetTheOtherPlayersMotionTenTimesASecond()
        {
            var room = new Room(3, 185);
            room.Gather();
            room.StartRace();
            room.Move(2000);
            var p0 = room.On(2, 0);
            Assert.Greater(p0.track.Count, 8, "the host's motion reached player 3");
            CoopMotion m;
            Assert.IsTrue(p0.track.Sample(room[2].RaceTimeMs - 150, out m));
            Assert.Greater(m.x, 0f);
            Assert.AreEqual(0, room.On(2, 2).track.Count, "a phone doesn't draw its own ghost");
        }

        [Test]
        public void TrafficStaysWithinWhatBluetoothCarries()
        {
            var room = new Room(4);   // 20-byte packets: the slowest phones
            room.Gather();
            room.StartRace();
            int before = room.links[0].PacketsSent;
            room.Move(5000);
            double perSecond = (room.links[0].PacketsSent - before) / 5.0;
            // The host sends to three players; BLE manages several hundred small packets a second.
            Assert.Less(perSecond, 360.0, "host packets a second");
        }
    }

    /// <summary>
    /// Races on a radio that misbehaves at random: phones walk out of range and back, Bluetooth goes off and on, apps freeze
    /// (a scene loading, a phone call), players finish and leave, the host among them, at random latencies and packet sizes,
    /// with two to four players. Once it all calms down: one host with everyone joined to it; every phone agreeing on the
    /// same standings to the letter and on its own result; places 1, 2, 3 without gaps; a phone that never had any trouble
    /// never listed out; and a finish any remaining phone saw never lost, even when the finisher (or the host) left.
    /// (The offline sweep behind this ran 2000 such storms clean; the test runs a sample of them.)
    /// </summary>
    public class CoopChaosTests
    {
        [Test]
        public void EveryPhoneSettlesOnTheSameFairStandingsWhateverTheRadioDid()
        {
            var failures = new List<string>();
            for (int seed = 1; seed <= 60; seed++)
            {
                string why = Run(seed, seed % 2 == 0);
                if (why != null) failures.Add("seed " + seed + ": " + why);
            }
            Assert.IsEmpty(failures, string.Join("\n", failures.ToArray()));
        }

        static string Run(int seed, bool leaves)
        {
            var rng = new Random(seed);
            int n = 2 + rng.Next(3);
            var room = new CoopSessionTests.RoomHandle(n, rng.Next(10, 120));
            room.Radio.PacketSize = rng.Next(2) == 0 ? 20 : 182;
            room.Gather();
            room.StartRace();
            var steady = new HashSet<int>();
            for (int i = 0; i < n; i++) if (rng.Next(3) == 0) steady.Add(i);
            var left = new HashSet<int>();
            var finishSeenBy = new Dictionary<uint, List<int>>();
            double storm = 60000 + rng.Next(180000);
            for (double t = 0; t < storm; )
            {
                double wait = 300 + rng.Next(4000);
                room.Move(wait);
                t += wait;
                int who = rng.Next(n);
                int kind = rng.Next(leaves ? 8 : 7);
                if (steady.Contains(who) && kind <= 5) continue;
                switch (kind)
                {
                    case 0: room.Radio.Isolate(room.Links[who]); break;
                    case 1: room.Radio.Rejoin(room.Links[who]); break;
                    case 2: room.Radio.SetPower(room.Links[who], false); break;
                    case 3: room.Radio.SetPower(room.Links[who], true); break;
                    case 4: room.Frozen.Add(who); break;
                    case 5: room.Frozen.Remove(who); break;
                    case 6:
                        if (room[who].InSession && room[who].MyStatus == PlayerStatus.Racing && rng.Next(3) == 0) room[who].ReportFinished();
                        break;
                    case 7:
                        if (left.Contains(who) || rng.Next(4) != 0 || n - left.Count <= 2) break;
                        if (room[who].MyStatus == PlayerStatus.Finished)
                        {
                            var seen = new List<int>();
                            for (int j = 0; j < n; j++)
                            {
                                if (j == who || left.Contains(j)) continue;
                                var q = room[j].Find(room[who].Uid);
                                if (q != null && q.status == PlayerStatus.Finished) seen.Add(j);
                            }
                            if (seen.Count > 0) finishSeenBy[room[who].Uid] = seen;
                        }
                        room[who].Leave();
                        left.Add(who);
                        steady.Remove(who);
                        break;
                }
            }
            // Calm: everyone back, in range, awake.
            room.Frozen.Clear();
            for (int i = 0; i < n; i++) { room.Radio.SetPower(room.Links[i], true); room.Radio.Rejoin(room.Links[i]); }
            room.Move(60000);
            for (int i = 0; i < n; i++) if (!left.Contains(i) && room[i].InSession && room[i].MyStatus == PlayerStatus.Racing) room[i].ReportFinished();
            room.Move(15000);

            var stay = new List<int>();
            for (int i = 0; i < n; i++) if (!left.Contains(i)) stay.Add(i);
            int hosts = 0;
            foreach (int i in stay)
            {
                if (!room[i].InSession) return "phone " + i + " is in no session";
                if (room[i].IsHost) hosts++;
                else if (room[i].Connection != ConnectionState.Joined) return "phone " + i + " is " + room[i].Connection;
            }
            if (hosts != 1) return hosts + " hosts";
            string first = Describe(room[stay[0]]);
            foreach (int i in stay)
            {
                string other = Describe(room[i]);
                if (other != first) return "phone " + stay[0] + " sees " + first + " but phone " + i + " sees " + other;
            }
            var s0 = room[stay[0]];
            if (s0.Phase != SessionPhase.Over) return "race not over: " + first;
            foreach (int i in stay)
            {
                var me = room[i].Me;
                if (me == null) return "phone " + i + " has no seat";
                if (me.status != room[i].MyStatus) return "phone " + i + " thinks " + room[i].MyStatus + " but the lobby says " + me.status;
            }
            foreach (int i in steady)
            {
                var me = s0.Find(room[i].Uid);
                if (me != null && (me.status == PlayerStatus.Disconnected || me.status == PlayerStatus.Left)) return "phone " + i + " had no trouble but is " + me.status;
            }
            foreach (var kv in finishSeenBy)
            {
                bool witness = false;
                foreach (int j in kv.Value) if (!left.Contains(j)) witness = true;
                var p = s0.Find(kv.Key);
                if (witness && (p == null || p.status != PlayerStatus.Finished)) return "a finisher who left lost their finish";
            }
            int place = 0;
            foreach (var p in CoopRules.Standings(s0.Players))
                if (p.status == PlayerStatus.Finished && p.place != ++place) return "places out of order: " + first;
            return null;
        }

        static string Describe(CoopSession s)
        {
            var parts = new List<string> { s.Phase.ToString() };
            foreach (var p in CoopRules.Standings(s.Players)) parts.Add(p.uid + ":" + p.status + ":" + p.place + ":" + p.finishMs);
            return string.Join(" ", parts.ToArray());
        }
    }

    /// <summary>Garbage from the radio (a stranger's device, a corrupted packet) is never fatal.</summary>
    public class CoopFuzzTests
    {
        [Test]
        public void RandomBytesNeverThrow()
        {
            var rng = new Random(7);
            var events = new List<LinkEvent>();
            var motions = new List<KeyValuePair<byte, CoopMotion>>();
            var r = new Reassembler();
            for (int i = 0; i < 20000; i++)
            {
                var bytes = new byte[rng.Next(0, 300)];
                rng.NextBytes(bytes);
                if (bytes.Length > 0 && rng.Next(2) == 0) bytes[0] = (byte)rng.Next(1, 16);   // a plausible message type
                SnapshotMsg s; HelloMsg h; WelcomeMsg w; ProfileMsg pr; ProgressMsg pg; SelectMsg sel; CoopMotion m; RoomBeacon b;
                CoopMessages.Read(new ByteReader(bytes), out s);
                CoopMessages.Read(new ByteReader(bytes), out h);
                CoopMessages.Read(new ByteReader(bytes), out w);
                CoopMessages.Read(new ByteReader(bytes), out pr);
                CoopMessages.Read(new ByteReader(bytes), out pg);
                CoopMessages.Read(new ByteReader(bytes), out sel);
                CoopMessages.ReadMotion(new ByteReader(bytes), out m);
                CoopMessages.ReadMotions(new ByteReader(bytes), motions);
                RoomBeacon.TryParse(bytes, out b);
                RoomBeacon.TryParseLocalName(System.Text.Encoding.UTF8.GetString(bytes), out b);
                events.Clear();
                NativeEvents.Decode(bytes, bytes.Length, events);
                r.Add(bytes, bytes.Length);
            }
        }

        [Test]
        public void ASessionFedGarbageCarriesOn()
        {
            var clock = new ManualClock { NowMs = 1000 };
            var radio = new InMemoryRadio(clock) { PacketSize = 185 };
            var host = new CoopSession(radio.CreateDevice("h"), clock, 11, "Host", 0, 3);
            var stranger = radio.CreateDevice("x");
            host.Host();
            for (int i = 0; i < 20; i++) { clock.Advance(16); host.Tick(); }
            stranger.Connect("h");
            var rng = new Random(3);
            for (int i = 0; i < 3000; i++)
            {
                var packet = new byte[rng.Next(1, 185)];
                rng.NextBytes(packet);
                stranger.Send(0, packet);
                clock.Advance(16);
                host.Tick();
                LinkEvent e;
                while (stranger.Poll(out e)) { }
            }
            Assert.IsTrue(host.InSession);
            Assert.AreEqual(1, host.Players.Count, "a stranger sending noise never gets a seat");
        }
    }

    /// <summary>The wire format, framing, beacons and the naming and standings rules.</summary>
    public class CoopProtocolTests
    {
        [Test]
        public void ASnapshotSurvivesTheWire()
        {
            var s = new SnapshotMsg { version = 77, sessionId = 0xDEADBEEF, epoch = 3, phase = SessionPhase.Racing, raceId = 2, phaseAtHostMs = 123456 };
            s.selection = new CoopSelection { route = 4, addOn = 1, chosenBy = 2 };
            s.players.Add(new CoopPlayer { slot = 0, uid = 5, tag = "K7QX", name = "Hana", character = 1, isHost = true, ready = true, status = PlayerStatus.Finished, finishMs = 98765, place = 1, progress = 1f });
            s.players.Add(new CoopPlayer { slot = 2, uid = 9, tag = "M2PZ", name = "Ünïcødé 🐱", character = 4, connected = false, status = PlayerStatus.Disconnected, outMs = 4321, progress = 0.5f });
            var w = new ByteWriter();
            CoopMessages.Write(w, s);
            SnapshotMsg back;
            Assert.IsTrue(CoopMessages.Read(new ByteReader(w.ToArray()), out back));
            Assert.AreEqual(77u, back.version);
            Assert.AreEqual(0xDEADBEEF, back.sessionId);
            Assert.AreEqual(SessionPhase.Racing, back.phase);
            Assert.AreEqual(4, back.selection.route);
            Assert.AreEqual(2, back.selection.chosenBy);
            Assert.AreEqual(123456u, back.phaseAtHostMs);
            Assert.AreEqual(2, back.players.Count);
            Assert.AreEqual("Hana", back.players[0].name);
            Assert.IsTrue(back.players[0].isHost && back.players[0].ready);
            Assert.AreEqual(98765u, back.players[0].finishMs);
            Assert.AreEqual("Ünïcødé 🐱", back.players[1].name);
            Assert.IsFalse(back.players[1].connected);
            Assert.AreEqual(PlayerStatus.Disconnected, back.players[1].status);
            Assert.AreEqual(0.5f, back.players[1].progress, 0.0001f);
        }

        [Test]
        public void ATruncatedMessageIsRejectedNotThrown()
        {
            var w = new ByteWriter();
            var s = new SnapshotMsg();
            s.players.Add(new CoopPlayer { name = "Max" });
            CoopMessages.Write(w, s);
            var bytes = w.ToArray();
            for (int cut = 1; cut < bytes.Length; cut++)
            {
                SnapshotMsg back;
                Assert.IsFalse(CoopMessages.Read(new ByteReader(bytes, 0, cut), out back), "cut at " + cut);
            }
        }

        [Test]
        public void MessagesAreSplitToThePacketSizeAndPutBackTogether()
        {
            var message = new byte[333];
            for (int i = 0; i < message.Length; i++) message[i] = (byte)(i * 7);
            var packets = CoopFraming.Split(message, message.Length, 20, 5);
            Assert.AreEqual(18, packets.Count);   // 19 bytes of payload each
            foreach (var p in packets) Assert.LessOrEqual(p.Length, 20);
            var r = new Reassembler();
            byte[] whole = null;
            foreach (var p in packets) whole = r.Add(p, p.Length) ?? whole;
            Assert.IsNotNull(whole);
            Assert.AreEqual(message.Length, whole.Length);
            for (int i = 0; i < message.Length; i++) Assert.AreEqual(message[i], whole[i]);
        }

        [Test]
        public void AHalfMessageCutOffByAReconnectionIsDropped()
        {
            var r = new Reassembler();
            var a = CoopFraming.Split(new byte[60], 60, 20, 1);
            var b = CoopFraming.Split(new byte[] { 9, 8, 7 }, 3, 20, 2);
            r.Add(a[0], a[0].Length);   // the rest of message 1 never comes
            var got = r.Add(b[0], b[0].Length);
            Assert.IsNotNull(got);
            Assert.AreEqual(3, got.Length);
            Assert.AreEqual(9, got[0]);
        }

        [Test]
        public void NamesAreCutBetweenCharacters()
        {
            var bytes = ByteWriter.Utf8Truncate("ééééé", 5);   // two bytes each
            Assert.AreEqual(4, bytes.Length);
            Assert.AreEqual("éé", System.Text.Encoding.UTF8.GetString(bytes));
        }

        [Test]
        public void TheBeaconReadsTheSameFromServiceDataAndFromAnAdvertisedName()
        {
            var b = new RoomBeacon { protocol = 1, sessionId = 0xA1B2C3, epoch = 2, players = 3, hostSlot = 2, phase = RoomPhase.Racing, hostName = "Hana" };
            RoomBeacon fromData, fromName;
            Assert.IsTrue(RoomBeacon.TryParse(b.ToBytes(), out fromData));
            Assert.IsTrue(RoomBeacon.TryParseLocalName(b.ToLocalName(), out fromName));
            foreach (var x in new[] { fromData, fromName })
            {
                Assert.AreEqual(1, x.protocol);
                Assert.AreEqual(0xA1B2C3u, x.sessionId);
                Assert.AreEqual(2, x.epoch);
                Assert.AreEqual(3, x.players);
                Assert.AreEqual(2, x.hostSlot);
                Assert.AreEqual(RoomPhase.Racing, x.phase);
            }
            Assert.AreEqual("Hana", fromData.hostName);
            Assert.AreEqual("", fromName.hostName, "an iOS host's name comes with its snapshot, not its advertisement");
            Assert.AreEqual(RoomBeacon.LocalNameLength, b.ToLocalName().Length, "fits beside the service UUID in iOS's 31 bytes");
            foreach (char c in b.ToLocalName()) Assert.IsTrue(c < 128, "plain ASCII");
            RoomBeacon junk;
            Assert.IsFalse(RoomBeacon.TryParseLocalName("Jane's iPhone", out junk));
            Assert.IsFalse(RoomBeacon.TryParseLocalName("KAAAAAA", out junk), "too short");
            Assert.IsFalse(RoomBeacon.TryParseLocalName("K!!!!!!!", out junk), "not base64");
            Assert.IsFalse(RoomBeacon.TryParseLocalName(null, out junk));
        }

        [Test]
        public void EveryBeaconFieldSurvivesTheShortName()
        {
            var rng = new Random(7);
            for (int i = 0; i < 2000; i++)
            {
                var b = new RoomBeacon
                {
                    protocol = (byte)rng.Next(8),
                    sessionId = (uint)rng.Next(1, 1 << 24),
                    epoch = (byte)rng.Next(RoomBeacon.MaxEpoch + 1),
                    players = (byte)rng.Next(1, CoopRules.MaxPlayers + 1),
                    hostSlot = (byte)rng.Next(CoopRules.MaxPlayers),
                    phase = (RoomPhase)rng.Next((int)RoomPhase.Over + 1),
                };
                RoomBeacon back;
                Assert.IsTrue(RoomBeacon.TryParseLocalName(b.ToLocalName(), out back));
                Assert.AreEqual(b.protocol, back.protocol);
                Assert.AreEqual(b.sessionId, back.sessionId);
                Assert.AreEqual(b.epoch, back.epoch);
                Assert.AreEqual(b.players, back.players);
                Assert.AreEqual(b.hostSlot, back.hostSlot);
                Assert.AreEqual(b.phase, back.phase);
            }
        }

        [Test]
        public void SessionIdsAndEpochsFitTheBeacon()
        {
            var clock = new ManualClock();
            var radio = new InMemoryRadio(clock);
            for (uint i = 1; i <= 50; i++)
            {
                var s = new CoopSession(radio.CreateDevice("ID" + i), clock, i * 2654435761u, "P", 0, (int)i);
                s.Host();
                Assert.AreNotEqual(0u, s.SessionId);
                Assert.AreEqual(s.SessionId & RoomBeacon.SessionMask, s.SessionId, "24 bits");
                s.Shutdown();
            }
        }

        [Test]
        public void ATailWhoseStartWasLostIsNeverReadAsAMessage()
        {
            var a = new byte[50];
            var b = new byte[50];
            for (int i = 0; i < 50; i++) { a[i] = (byte)i; b[i] = (byte)(200 + i); }
            var pa = CoopFraming.Split(a, a.Length, 20, 5);
            var pb = CoopFraming.Split(b, b.Length, 20, 6);
            Assert.AreEqual(3, pa.Count);
            var rx = new Reassembler();
            // a's first packet was dropped: its middle and end must not come out as a message
            Assert.IsNull(rx.Add(pa[1], pa[1].Length));
            Assert.IsNull(rx.Add(pa[2], pa[2].Length));
            // b's start was dropped too, and its tail carries a different number
            Assert.IsNull(rx.Add(pb[2], pb[2].Length));
            // a whole message after them comes through intact
            byte[] got = null;
            foreach (var p in pb) got = rx.Add(p, p.Length) ?? got;
            CollectionAssert.AreEqual(b, got);
            // a message cut short by a new one: the new one wins, the old one never appears
            rx.Add(pa[0], pa[0].Length);
            got = null;
            foreach (var p in pb) got = rx.Add(p, p.Length) ?? got;
            CollectionAssert.AreEqual(b, got);
            // after a reconnection the half-read message is forgotten
            rx.Add(pa[0], pa[0].Length);
            rx.Reset();
            Assert.IsNull(rx.Add(pa[1], pa[1].Length));
            Assert.IsNull(rx.Add(pa[2], pa[2].Length));
        }

        [Test]
        public void NamesAreCleanedForOtherScreens()
        {
            Assert.AreEqual("Sam", CoopRules.CleanName("  Sam  "));
            Assert.AreEqual("Big Sam", CoopRules.CleanName("Big \t  Sam"));
            Assert.AreEqual("SamK7QX", CoopRules.CleanName("Sam#K7QX"), "no fake tags");
            Assert.AreEqual("", CoopRules.CleanName("   "));
            Assert.AreEqual(CoopRules.MaxNameLength, CoopRules.CleanName("abcdefghijklmnopqrstuvwxyz").Length);
            Assert.AreEqual("ab", CoopRules.CleanName("a\u0007b"));
        }

        [Test]
        public void TagsAreStableAndNeverShared()
        {
            Assert.AreEqual(CoopRules.TagFor(1234, 0), CoopRules.TagFor(1234, 0));
            var players = new List<CoopPlayer> { new CoopPlayer { uid = 1, tag = CoopRules.TagFor(2, 0) } };
            string tag = CoopRules.UniqueTag(2, players);
            Assert.AreNotEqual(players[0].tag, tag, "a clash gets another tag");
            foreach (char c in tag) Assert.IsTrue("0O1IL".IndexOf(c) < 0, "no look-alike characters");
            var seen = new HashSet<string>();
            for (uint uid = 1; uid <= 2000; uid++) seen.Add(CoopRules.TagFor(uid, 0));
            Assert.Greater(seen.Count, 1990, "tags spread out");
        }

        [Test]
        public void StandingsPutFinishersFirstThenRacersThenThoseWhoDroppedOut()
        {
            var list = new List<CoopPlayer>
            {
                new CoopPlayer { slot = 0, status = PlayerStatus.Disconnected, progress = 0.9f },
                new CoopPlayer { slot = 1, status = PlayerStatus.Racing, progress = 0.4f },
                new CoopPlayer { slot = 2, status = PlayerStatus.Finished, finishMs = 90000 },
                new CoopPlayer { slot = 3, status = PlayerStatus.Finished, finishMs = 80000 },
                new CoopPlayer { slot = 4, status = PlayerStatus.Racing, progress = 0.7f },
                new CoopPlayer { slot = 5, status = PlayerStatus.Left, progress = 0.2f },
            };
            var order = CoopRules.Standings(list);
            var slots = new List<int>();
            foreach (var p in order) slots.Add(p.slot);
            Assert.AreEqual("3,2,4,1,0,5", string.Join(",", slots.ConvertAll(s => s.ToString()).ToArray()));
            CoopRules.AssignPlaces(list);
            Assert.AreEqual(1, list[3].place);
            Assert.AreEqual(2, list[2].place);
            Assert.AreEqual(0, list[0].place);
            Assert.IsFalse(CoopRules.RaceOver(list));
        }

        [Test]
        public void ASplitSessionAgreesWhichHostKeepsTheRace()
        {
            var a = new RoomBeacon { sessionId = 7, epoch = 0, players = 3 };
            var b = new RoomBeacon { sessionId = 7, epoch = 1, players = 1 };
            Assert.IsTrue(CoopRules.ShouldYieldTo(b, a), "fewer players hand over");
            Assert.IsFalse(CoopRules.ShouldYieldTo(a, b));
            var c = new RoomBeacon { sessionId = 7, epoch = 2, players = 3 };
            Assert.IsTrue(CoopRules.ShouldYieldTo(c, a), "a tie goes to the older host");
            Assert.IsFalse(CoopRules.ShouldYieldTo(a, c));
            Assert.IsFalse(CoopRules.ShouldYieldTo(a, new RoomBeacon { sessionId = 8, epoch = 1, players = 4 }), "another session");
        }

        [Test]
        public void TwoTakersOverAtTheSameEpochAgreeByTheirSeats()
        {
            var a = new RoomBeacon { sessionId = 7, epoch = 3, players = 2, hostSlot = 1 };
            var b = new RoomBeacon { sessionId = 7, epoch = 3, players = 2, hostSlot = 2 };
            Assert.IsTrue(CoopRules.ShouldYieldTo(b, a), "the lower seat keeps the race");
            Assert.IsFalse(CoopRules.ShouldYieldTo(a, b));
            Assert.IsFalse(CoopRules.ShouldYieldTo(a, a), "a host never yields to itself");
        }

        [Test]
        public void ResultsMergeTheWayEveryPhoneCanAgreeOn()
        {
            var p = new CoopPlayer { status = PlayerStatus.Racing };
            Assert.IsTrue(CoopRules.MergeResult(p, PlayerStatus.Finished, 9000, 0));
            Assert.AreEqual(PlayerStatus.Finished, p.status);
            Assert.IsFalse(CoopRules.MergeResult(p, PlayerStatus.Left, 0, 9500), "a finish is never undone");
            Assert.IsFalse(CoopRules.MergeResult(p, PlayerStatus.Racing, 0, 0));

            var out1 = new CoopPlayer { status = PlayerStatus.Disconnected, outMs = 5000 };
            Assert.IsTrue(CoopRules.MergeResult(out1, PlayerStatus.Racing, 0, 0), "back in touch: back in the race");
            Assert.AreEqual(PlayerStatus.Racing, out1.status);
            var out2 = new CoopPlayer { status = PlayerStatus.Disconnected, outMs = 5000 };
            Assert.IsTrue(CoopRules.MergeResult(out2, PlayerStatus.Finished, 70000, 0), "a finish made while out of touch counts");
            Assert.AreEqual(70000u, out2.finishMs);

            var gone = new CoopPlayer { status = PlayerStatus.Left, outMs = 30000 };
            Assert.IsFalse(CoopRules.MergeResult(gone, PlayerStatus.Racing, 0, 0), "leaving is final");
            Assert.IsFalse(CoopRules.MergeResult(gone, PlayerStatus.Finished, 40000, 0), "no finish after leaving");
            Assert.IsTrue(CoopRules.MergeResult(gone, PlayerStatus.Finished, 20000, 0), "a finish from before leaving is kept");
        }

        [Test]
        public void RudeNamesAreDroppedAndOrdinaryNamesAreKept()
        {
            foreach (var name in new[] { "Kshitij", "Nazir", "Wankhede", "Fukuda", "Vergara", "Zora", "Scunthorpe", "Diputado", "Cassie", "Dick", "Hancock", "Shital", "Pornpimol", "Folarin", "Nigella", "Sexton", "Matsushita", "Teja", "Hana", "Mia 2" })
                Assert.AreEqual(name, CoopRules.CleanName(name), name + " is an ordinary name");
            foreach (var name in new[] { "fuck", "FUUUCK", "BigFuckFace", "b1tch", "Shit", "puta", "Putas", "N4Z1", "bullshit", "mierda", "pendejo", "Hitler", "motherfucker" })
                Assert.AreEqual("", CoopRules.CleanName(name), name + " is dropped (the player is Player N instead)");
        }

        [Test]
        public void TheClockSyncTrustsTheQuickestRoundTrip()
        {
            var sync = new ClockSync();
            // The host's clock is 5000 ms ahead. A slow reply (queued 300 ms one way) and a quick one.
            sync.AddSample(1000, 6000 + 300, 1000 + 320);
            sync.AddSample(2000, 7000 + 10, 2000 + 20);
            Assert.AreEqual(5000.0, sync.Offset, 1.0);
            Assert.AreEqual(20.0, sync.RoundTrip, 0.001);
            Assert.AreEqual(0, sync.Jumps);
            // This phone slept 30 s and its clock stood still: the host's is now 35 s ahead. No round trip explains that.
            sync.AddSample(3000, 38000 + 10, 3000 + 20);
            Assert.AreEqual(1, sync.Jumps);
            Assert.AreEqual(1, sync.Samples, "the old samples are dropped");
            Assert.AreEqual(35000.0, sync.Offset, 1.0);
            // An ordinary slow reply is no jump.
            sync.AddSample(4000, 39000 + 400, 4000 + 420);
            Assert.AreEqual(1, sync.Jumps);
        }

        [Test]
        public void TheRealClockCountsTimeTheStopwatchMissed()
        {
            var c = new StopwatchClock();
            double a = c.NowMs, b = c.NowMs;
            Assert.GreaterOrEqual(b, a, "it only goes forward");
        }

        static LinkEvent Ev(LinkEventType type, int peer, byte gen)
        {
            return new LinkEvent { type = type, peer = peer, state = (RadioState)gen };
        }

        [Test]
        public void LateNativeEventsFromAnOldConnectionAreDropped()
        {
            var f = new LinkEventFilter();
            byte first = f.Connect();
            var e = Ev(LinkEventType.Connected, 0, first);
            Assert.IsTrue(f.Pass(ref e));
            Assert.AreEqual(RadioState.Unknown, e.state, "the generation is not mistaken for a radio state");
            // The game leaves that host and connects to another; the first one's goodbye and last packet arrive late.
            f.Disconnect();
            byte second = f.Connect();
            Assert.AreNotEqual(first, second);
            e = Ev(LinkEventType.Disconnected, 0, first); Assert.IsFalse(f.Pass(ref e), "the old connection's goodbye");
            e = Ev(LinkEventType.Data, 0, first); Assert.IsFalse(f.Pass(ref e), "the old connection's packet");
            e = Ev(LinkEventType.Connected, 0, second); Assert.IsTrue(f.Pass(ref e));
            e = Ev(LinkEventType.Data, 0, second); Assert.IsTrue(f.Pass(ref e));
            // After Disconnect nothing of the client role passes, not even its own generation.
            f.Disconnect();
            e = Ev(LinkEventType.Disconnected, 0, second); Assert.IsFalse(f.Pass(ref e), "Disconnect raises no event on this side");
            // A failure ends the attempt.
            byte third = f.Connect();
            e = Ev(LinkEventType.ConnectFailed, 0, third); Assert.IsTrue(f.Pass(ref e));
            e = Ev(LinkEventType.Connected, 0, third); Assert.IsFalse(f.Pass(ref e), "nothing after the failure");
            // Radio events keep their state.
            e = new LinkEvent { type = LinkEventType.Radio, state = RadioState.Off }; Assert.IsTrue(f.Pass(ref e));
            Assert.AreEqual(RadioState.Off, e.state);
        }

        [Test]
        public void LateNativeEventsFromAnOldHostingRunOrAKickedPlayerAreDropped()
        {
            var f = new LinkEventFilter();
            var e = Ev(LinkEventType.Connected, 1, 0); Assert.IsFalse(f.Pass(ref e), "not hosting");
            byte run = f.StartHost();
            e = Ev(LinkEventType.HostStarted, 0, run); Assert.IsTrue(f.Pass(ref e));
            e = Ev(LinkEventType.Connected, 1, run); Assert.IsTrue(f.Pass(ref e));
            e = Ev(LinkEventType.Connected, 2, run); Assert.IsTrue(f.Pass(ref e));
            f.Kick(2);
            e = Ev(LinkEventType.Data, 2, run); Assert.IsFalse(f.Pass(ref e), "a kicked player's packet");
            e = Ev(LinkEventType.Disconnected, 2, run); Assert.IsFalse(f.Pass(ref e), "Kick raises no event on this side");
            e = Ev(LinkEventType.Data, 1, run); Assert.IsTrue(f.Pass(ref e));
            f.StopHost();
            byte again = f.StartHost();
            e = Ev(LinkEventType.HostStarted, 0, run); Assert.IsFalse(f.Pass(ref e), "the old run's start");
            e = Ev(LinkEventType.Disconnected, 1, run); Assert.IsFalse(f.Pass(ref e), "the old run's player");
            e = Ev(LinkEventType.HostStarted, 0, again); Assert.IsTrue(f.Pass(ref e));
            e = Ev(LinkEventType.HostFailed, 0, again); Assert.IsTrue(f.Pass(ref e));
            e = Ev(LinkEventType.Connected, 3, again); Assert.IsFalse(f.Pass(ref e), "a failed run takes no players");
            e = new LinkEvent { type = (LinkEventType)200 }; Assert.IsFalse(f.Pass(ref e), "unknown events are dropped");
        }

        [Test]
        public void TheNativePluginsEventsAreRead()
        {
            var w = new ByteWriter();
            var beacon = new RoomBeacon { protocol = 1, sessionId = 99, epoch = 0, players = 2, hostSlot = 0, phase = RoomPhase.Lobby, hostName = "Max" };
            NativeEvents.Encode(w, new LinkEvent { type = LinkEventType.Radio, state = RadioState.On }, null, null);
            NativeEvents.Encode(w, new LinkEvent { type = LinkEventType.Found, address = "AA:BB", rssi = -55 }, beacon.ToBytes(), null);    // an Android host
            NativeEvents.Encode(w, new LinkEvent { type = LinkEventType.Found, address = "UUID-1", rssi = -70 }, null, beacon.ToLocalName()); // an iOS host
            NativeEvents.Encode(w, new LinkEvent { type = LinkEventType.Found, address = "junk" }, null, "Some speaker");                     // not a lobby
            NativeEvents.Encode(w, new LinkEvent { type = LinkEventType.Data, peer = 3 }, new byte[] { 1, 2, 3 }, null);
            NativeEvents.Encode(w, new LinkEvent { type = LinkEventType.HostFailed }, null, "noAdvertise");
            var events = new List<LinkEvent>();
            var bytes = w.ToArray();
            NativeEvents.Decode(bytes, bytes.Length, events);
            Assert.AreEqual(5, events.Count, "the junk advertisement is skipped");
            Assert.AreEqual(RadioState.On, events[0].state);
            Assert.AreEqual("AA:BB", events[1].address);
            Assert.AreEqual(-55, events[1].rssi);
            Assert.AreEqual(99u, events[1].beacon.sessionId);
            Assert.AreEqual(99u, events[2].beacon.sessionId);
            Assert.AreEqual("", events[2].beacon.hostName, "an iOS host advertises no name");
            Assert.AreEqual(3, events[3].peer);
            Assert.AreEqual(3, events[3].data.Length);
            Assert.AreEqual("noAdvertise", events[4].error);
            // A cut-off buffer gives the whole events before the cut, and no garbage.
            var partial = new List<LinkEvent>();
            NativeEvents.Decode(bytes, bytes.Length - 3, partial);
            Assert.AreEqual(4, partial.Count);
        }

        [Test]
        public void GhostsAreDrawnBetweenSamplesAndCarriedOnOnlyBriefly()
        {
            var track = new MotionTrack();
            track.Add(new CoopMotion { raceMs = 1000, x = 10f, vx = 5f, flags = CoopMotion.Grounded });
            track.Add(new CoopMotion { raceMs = 1100, x = 10.5f, vx = 5f, flags = CoopMotion.Grounded });
            CoopMotion m;
            Assert.IsTrue(track.Sample(1050, out m));
            Assert.AreEqual(10.25f, m.x, 0.001f);
            Assert.IsTrue(track.Sample(5000, out m));
            Assert.AreEqual(10.5f + 5f * MotionTrack.MaxExtrapolationMs / 1000f, m.x, 0.001f, "no further than the extrapolation limit");
            track.Add(new CoopMotion { raceMs = 1200, leg = 1, x = 0f });
            Assert.AreEqual(1, track.Count, "a new leg starts the track again");
        }
    }
}
#endif
