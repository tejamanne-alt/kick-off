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
        /// <summary>A few phones on one radio, ticked together.</summary>
        sealed class Room
        {
            public readonly ManualClock clock = new ManualClock { NowMs = 1000 };
            public readonly InMemoryRadio radio;
            public readonly List<CoopSession> phones = new List<CoopSession>();
            public readonly List<InMemoryLink> links = new List<InMemoryLink>();
            public readonly List<List<CoopNotice>> notices = new List<List<CoopNotice>>();

            public Room(int count, int packetSize = 20)
            {
                radio = new InMemoryRadio(clock) { PacketSize = packetSize };
                for (int i = 0; i < count; i++)
                {
                    var link = radio.CreateDevice("phone" + i);
                    var session = new CoopSession(link, clock, (uint)(1000 + i * 7919), i == 0 ? "Hana" : "", (byte)i, 42 + i);
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
                    foreach (var p in phones) p.Tick();
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
                    foreach (var p in phones)
                        if (p.InSession && p.MyStatus == PlayerStatus.Racing)
                            p.ReportMotion(new CoopMotion { x = (float)(p.RaceTimeMs / 200.0), y = 0f, flags = CoopMotion.Grounded, progress = (float)Math.Min(0.9, p.RaceTimeMs / 120000.0) });
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
        public void APlayerWhoWalkedAwayAndCameBackLateStaysDisqualifiedAndDoesNotTakeTheRaceOver()
        {
            var room = new Room(3);
            room.Gather();
            room.StartRace();
            room.Move(1000);
            room.radio.Isolate(room.links[2]);
            room.Move(CoopTiming.RaceGrace + 6000);   // long enough to have tried hosting alone
            room.radio.Rejoin(room.links[2]);
            room.Move(12000);
            Assert.IsTrue(room[0].IsHost, "the original host (more players) keeps the race");
            Assert.IsFalse(room[2].IsHost, "the lone phone handed over");
            Assert.AreEqual(ConnectionState.Joined, room[2].Connection);
            Assert.AreEqual(PlayerStatus.Disconnected, room.On(0, 2).status);
            Assert.AreEqual(PlayerStatus.Disconnected, room[2].MyStatus, "its own phone agrees its run no longer counts");
            Assert.AreEqual(PlayerStatus.Racing, room.On(0, 1).status, "nobody else was disqualified");
            room[2].ReportFinished();
            room.Run(600);
            Assert.AreEqual(PlayerStatus.Disconnected, room.On(0, 2).status, "a late finish doesn't count");
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
            var b = new RoomBeacon { protocol = 1, sessionId = 0x01020304, epoch = 2, players = 3, maxPlayers = 4, phase = RoomPhase.Racing, hostName = "Hana" };
            RoomBeacon fromData, fromName;
            Assert.IsTrue(RoomBeacon.TryParse(b.ToBytes(), out fromData));
            Assert.IsTrue(RoomBeacon.TryParseLocalName(b.ToLocalName(), out fromName));
            foreach (var x in new[] { fromData, fromName })
            {
                Assert.AreEqual(0x01020304u, x.sessionId);
                Assert.AreEqual(2, x.epoch);
                Assert.AreEqual(3, x.players);
                Assert.AreEqual(4, x.maxPlayers);
                Assert.AreEqual(RoomPhase.Racing, x.phase);
                Assert.AreEqual("Hana", x.hostName);
            }
            Assert.LessOrEqual(b.ToLocalName().Length, 28, "fits an iOS advertisement's name");
            RoomBeacon junk;
            Assert.IsFalse(RoomBeacon.TryParseLocalName("Jane's iPhone", out junk));
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
        public void TheClockSyncTrustsTheQuickestRoundTrip()
        {
            var sync = new ClockSync();
            // The host's clock is 5000 ms ahead. A slow reply (queued 300 ms one way) and a quick one.
            sync.AddSample(1000, 6000 + 300, 1000 + 320);
            sync.AddSample(2000, 7000 + 10, 2000 + 20);
            Assert.AreEqual(5000.0, sync.Offset, 1.0);
            Assert.AreEqual(20.0, sync.RoundTrip, 0.001);
        }

        [Test]
        public void TheNativePluginsEventsAreRead()
        {
            var w = new ByteWriter();
            var beacon = new RoomBeacon { protocol = 1, sessionId = 99, epoch = 0, players = 2, maxPlayers = 4, phase = RoomPhase.Lobby, hostName = "Max" };
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
            Assert.AreEqual("Max", events[2].beacon.hostName);
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
