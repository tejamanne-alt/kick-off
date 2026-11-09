# Co-op: race your friends to school over Bluetooth

The third mode beside PLAY and HOLIDAY RUN (the **CO-OP** button on the title screen). Up to **four phones in the same
room**, iPhones and Android phones together, race from the front door to the school gate over Bluetooth LE. No internet,
no accounts, no server.

## How it plays

- **Your name and tag.** On the co-op screen you type the name the others will see. Leave it empty and you are
  **Player 1, Player 2, Player 3...** by your seat in the lobby. A name the word filter refuses is dropped (the player
  is told, and plays as Player N). Every phone also has a **tag**: four characters made from a random seed kept on that
  install (`#K7QX`). It is shown after the name everywhere ("Sam #K7QX", "Sam #M2PZ"), so
  two players who type the same name can always be told apart. The host makes sure no two tags in a lobby clash, and
  a name can't contain `#`, so nobody can fake someone else's tag. The kid you picked (the player picker) is the kid the
  others see.
- **Host or join.** One phone taps **HOST A RACE**. The others tap **JOIN A RACE** and see the lobbies nearby: whose race
  it is, how many are in, whether it has already started, and the signal (nearest first).
- **The lobby.** Four seats: who is in, their tag, the host, ready or not, and a lost connection. **Any player can choose
  the stage and the location**, as in a fighting game's stage select (one choice is enough for everyone): the choice goes
  to the host, the last one it receives wins, the lobby shows who chose, and everybody's READY is cleared so nobody starts
  on a stage they didn't see. The stages are the six routes from home to school (2 to 5 legs each, about 2 to 6 minutes),
  plus Random; the locations are the add-ons (the original Kamakura streets, California) plus Random. A location only one
  player has unlocked plays for everyone once that player picks it. Where chapters are sold (`Monetization.RequireUnlock`),
  a stage outside the chooser's purchase can't be chosen by them.
- **Filters are your own.** The comic and pencil filters stay each phone's own choice, from Add-ons & Filters on the title
  screen, as before. They are not part of the lobby.
- **The start.** When everyone (at least two) is READY, a 3-second countdown starts (anyone un-readying, changing the
  stage, joining or dropping out stops it). Every phone loads the route's first leg; the race waits until they all have
  (at most 15 s), then counts **3, 2, 1, GO** to the same instant on every phone.
- **The race.** Each phone runs its own kid in its own copy of the level, with the usual controls and rules (losing the
  ball sends you back to the checkpoint). The others appear as **ghosts**: their kid and ball, in lanes just behind
  yours, with a ring of their colour at their feet and their name over their head (at the edge of the screen, with the
  distance, when they are out of view). Ghosts are only pictures: nothing collides with them. At each stop the next leg
  loads at once ("Made it to the bus stop! Next: Granny's house"). The HUD's clock is the race clock; pausing doesn't
  stop it (the others don't wait). The standings card under the pause button shows everyone in order, each with a bar of
  how far along the whole route they are, and their leg or their time.
- **The finish.** The first kid through the school gate with the ball wins. Times are taken from the shared race clock,
  so the order is the true order whatever the radio's delay. **The others carry on** to finish; a finisher can watch the
  standings, go back to the lobby or leave, and **keeps their time and place even after leaving** (or switching
  Bluetooth off) once the host has listed it (leaving before that asks first: "the others haven't seen your finish
  yet"). When nobody is still on the way the race is over; the host can start **NEW RACE** with the same players.
  Finishing earns the coins collected on the way (saved at the gate) plus a place bonus (40 / 25 / 15 / 10, given once
  the result is final, so a finish heard late can't leave two winners); a sticker found on a leg goes into the album.

## Resilience

The rules a co-op race follows when phones lose each other (all in `Coop/Session/CoopSession.cs`, timings in
`CoopTiming`). The race never waits on the radio: every phone keeps playing its own run while the connection is out,
and catches up when it is back.

| What happens | What the game does |
|---|---|
| A player's Bluetooth goes off, or they walk out of range, mid-race | Everyone else carries on. Their row says "Signal lost". Their own phone keeps racing and shows a banner with the seconds left before they are listed last (`RaceGrace`, **20 s**). Back in time: nothing is lost, their ghost reappears. |
| They stay away longer | The others list them **last** ("Away"), after everyone who finished or is still racing. Their own phone says so ("the others list you last for now: keep running") and their run goes on. If they come back **before the host starts the next race**, they are back in the race where they are (racing, or finished with their real time: a finish made while away counts). |
| A player is still away when the next race starts | That race goes ahead without them; they rejoin the lobby when they are back. |
| A player leaves the race (pause > Leave race) | Listed last as "Left"; the race goes on. Leaving is final. |
| Only two players, and one drops | The other carries on and wins by finishing. (Ending the race on the one who stayed would punish the wrong player.) If the dropped one comes back, both runs count. |
| A player who already finished leaves or loses Bluetooth | Their time and place stay in the standings ("2:31.4 · left"). The race goes on for the others. Every phone relays the finishes it knows to a new host, so a finish one phone saw survives the host changing. |
| **The host** drops (Bluetooth off, out of range, left, app closed) | The others look for the host for 4 s (`ReconnectWindow`; a blip and it's back). Then the next player by seat **takes over as host** with the same session (a higher epoch) and the others join them; if that one is gone too, the next takes over 4 s later. Every phone has the whole standings, so finished times survive. A host that leaves on purpose says so, and the hand-over is immediate. |
| The host's Bluetooth stays off, or its app goes to the background | Past 3 s (`HostDeafGrace`) it stops hosting and hands the race over as above; back, it joins the new host as a player. |
| A host keeps advertising but no longer answers (frozen) | After two attempts that connect but are never answered, players give up on it (until its advertisement changes, or 30 s) and the next player takes over. |
| The host was the winner and left | The new host keeps them first in the list. |
| The old host comes back | It finds the new host of its session and joins it (it doesn't take the race back), with its run intact. |
| Two groups that lost each other each raced on with a host of their own | Each host listens for the other every 12 s; the one with **more players keeps the race** (a tie: the lower epoch, then the lower seat). The other host's group joins it, and every run, finish and time is merged. |
| A phone loads a scene (a new leg, the lobby) | It tells the others to expect a few seconds' silence (`Busy`), so the load isn't taken for a lost connection; and a phone that froze for a moment doesn't count the others' silence during it. |
| A phone sleeps (power button) mid-race | Its race clock counts the time it slept (a Stopwatch stops while a phone sleeps: without this it would gain that time). A clock that jumps anyway is caught by the clock sync and the race start corrected. |
| The lobby's host goes before a race | Players look for it for 8 s, then the lobby closes ("The lobby closed"). |
| The host's lobby can't be advertised (Bluetooth off, a phone that can't advertise) | Hosting fails before anyone could join: the phone is back on the start screen with the reason. |
| A player drops out of the lobby | Their seat (and tag) is kept 10 s (`LobbyGrace`). |
| A first join fails (Android's status 133, a busy radio) | It is tried again, up to three times. |
| A phone never finishes loading the first leg | The race waits at most 15 s (`LoadTimeout`) and starts without it; it joins in as soon as it is loaded. |
| A fifth phone, a different version (protocol or content), a race already under way | Turned away with the reason ("Lobby full", "A different version of the game", "That race has already started"). The content check is a fingerprint of the kids, routes and locations, so two builds that number them differently never race. |
| The screen would dim and lock in a session | It is kept on while in a session (a locked phone drops off the radio). |
| An app closed and opened again mid-race | It has a new id for this launch: it joins as a new player rather than being mistaken for the run it lost. Its tag stays the same. |

## Architecture

```
Coop/
  Net/          (pure C#, no Unity: tested offline)
    CoopWire.cs        ByteWriter / ByteReader (little-endian; UTF-8 cut between characters; never throws on a short message)
    CoopFraming.cs     messages <-> radio packets (1 header byte: first and last flags + message number)
    CoopMessages.cs    the messages and their layouts
    ClockSync.cs       NTP-style host clock estimate (min round trip of the last 12 pings); clocks
    RoomBeacon.cs      what a host advertises (service data on Android, an 8-character name on iOS)
    ICoopLink.cs       the radio interface the session runs on
    InMemoryRadio.cs   a pretend radio for tests and the editor's bots (latency, range, power, supervision timeout)
    NativeEvents.cs    the packed events the native plugins send up
    LinkEventFilter.cs drops late native events of a connection or hosting run the game has left
  Session/      (pure C#)
    CoopPlayer.cs      a player, statuses, motion samples and their interpolation (MotionTrack), the selection
    CoopRules.cs       names, tags, standings, places, race over, which host keeps a split session
    CoopSession.cs     the lobby and race state machine (shared state, the radio, timers); with
    CoopSession.Host.cs   the host role: seats, snapshots, timeouts, the split rule, stepping down
    CoopSession.Client.cs the player role: joining, the clock, losing the host, taking over
  Transport/
    IosBleLink.cs      Plugins/iOS/DTSCoopBLE.mm (CoreBluetooth)
    AndroidBleLink.cs  Plugins/Android/DtsCoopBle.java (android.bluetooth.le); runtime permissions
  CoopService.cs     DontDestroyOnLoad: owns the link and the session, ticks them, hooks each leg's scene up
  CoopRaceMode.cs    this phone's run through the route's legs (Core/ILevelRace for the level and the HUD)
  CoopLevelLink.cs   per leg: ghosts, reporting the kid, the HUD
  CoopGhost.cs       another player's kid and ball (a stripped copy of the level's model, posed from their motion)
  CoopHud.cs         standings, banner, feed, name tags, between-legs message, results
  CoopStandingsView.cs, CoopProfile.cs (name, tag seed, launch id, palette), CoopBots.cs (editor practice bots)
FrontEnd/CoopScreen.cs   start / join / lobby / race faces
UI/CoopStagePicker.cs    stage and location select; yes/no
Core/ILevelRace.cs       what a level sees of a race (LevelManager.Race)
```

**Topology.** BLE between iPhones and Android phones means GATT: the host is a **GATT server** that advertises the
game's service; every other phone connects to it as a **client** (a star; BLE has no mesh between the two platforms).
Three connections per host is well within both stacks' limits, which is why the lobby holds four.

**Authority.** The host keeps the lobby (who, seats, tags, stage, phase, standings) and sends a versioned **snapshot**
to everyone (on change, at most every 120 ms, and at least once a second as a heartbeat). Players send their own state:
profile (name, kid, ready, loaded), progress (leg, status, finish time) and motion. Everything is **state, not events**:
messages are repeated or superseded, so a message lost across a reconnection is never needed again. Each phone simulates
only its own kid (the level's physics are not deterministic across devices, and BLE is too slow to share them); the
race compares runs, it doesn't share a world, as ghost races do.

**The race clock.** Players ping the host twice a second (that is also the heartbeat). From each round trip
`ClockSync` estimates the host's clock (`offset = host - (sent + received) / 2`, trusting the quickest of the last 12).
The host announces GO as an instant on its clock, 3.5 s ahead; each phone turns it into its own and locks it when the
race starts, so the clock doesn't twitch when the host changes. A locked start is checked once more, and moved if it is
out by more than a second, when it was a guess (a phone that took over before it ever synced), after a reconnection,
or when the sync sees a clock jump (a sample no honest round trip explains). The session's clock counts the time a
phone slept. Finish times are durations since GO.

**Ghosts** are drawn 160 ms in the past (`InterpolationDelayMs`), blended between the two samples around that moment,
and carried along their velocity for at most 250 ms if a sample is late. Samples are stamped with the sender's race
clock, which every phone shares.

## Wire protocol

Protocol version 1 (`CoopMessages.Protocol`; the beacon carries it, so the Join list marks other versions). Every message
starts with its type byte. Little-endian; strings are a length byte and UTF-8.

| Type | Direction | Fields |
|---|---|---|
| 1 Hello | player > host | protocol u8, launch id u32, session id u32 (0: new), name str, kid u8, content fingerprint u32, tag seed u32 |
| 2 Welcome | host > player | session id u32, epoch u8, slot u8, tag str |
| 3 Reject | host > player | reason u8 (1 full, 2 race under way, 3 version) |
| 4 Snapshot | host > all | version u32, session u32, epoch u8, phase u8, race id u8, selection (route, add-on, chosen by), race selection, phase time u32 (host ms), count u8, then per player: slot, id u32, tag, name, kid, flags (host, ready, connected), loaded race, status, leg, progress u16, finish ms u32, out ms u32, place |
| 5 Profile | player > host | seq u16, name, kid, ready, loaded race |
| 6 Progress | player > host | seq u16, race id, status, leg, progress u16, finish ms u32, out ms u32 |
| 7 Motion | player > host | race ms u32, leg, flags, progress u16, x f32, y f32, vx, vy, ball dx, ball dy (cm, i16) |
| 8 Motions | host > all | count, then slot + motion each |
| 9 Ping / 10 Pong | player <> host | sent ms u32 / sent ms u32, host ms u32 |
| 11 Select | player > host | route u8, add-on u8 (255: random) |
| 12 Leave | player > host | |
| 13 Closing | host > all | the lobby closed (before a race) |
| 14 HostLeaving | host > all | the host leaves a race: hand over now |
| 15 Busy | either way | ms u16: this phone is about to go quiet (a scene load); don't take it for a lost connection |
| 16 Known | player > new host | count, then player records (as in the snapshot): the finishes this phone knows, so a host change loses none |

**Framing** (`CoopFraming`): a message is split into packets of the link's size (20 bytes on the oldest phones; the
plugins raise the MTU, typically to 182 or more). Header byte: bit 7 set on a message's last packet, bit 6 on its
first, bits 0-5 the message number (mod 64). The native layers send a connection's packets in order; when a queue
overflows (a phone that stopped listening) they drop whole messages, oldest first, never part of one. A message is only
put together from its first packet to its last, all of one number: a tail whose start was lost (a drop, a reconnection)
is thrown away, never read as a message of its own.

**Traffic.** Ten motions a second each way while racing, a snapshot a second, two pings: about 1 KB/s per player at
the host, a few dozen packets a second (a test checks the host stays under 360 a second with 20-byte packets).

**Beacon** (`RoomBeacon`): `[protocol][session id x4][epoch][players: count | host's seat << 4][phase][host name, UTF-8,
at most 10 bytes]`. An Android host puts it in its scan response as service data under the 16-bit key `0x4B4F`. An iOS
host can't advertise service data, and beside the game's 128-bit service UUID its advertisement has room for an
8-character name: `K` and seven URL-safe base-64 characters packing 42 bits, protocol (3), session id (24), epoch (6),
players (3), the host's seat (2), phase (2). (So session ids are 24 bits and epochs stop at 63 everywhere; an iOS lobby
shows as "a friend's race" until joined.) Scanners read either. The same host heard under two addresses (an Android
address that rotated) is one room.

## Native bridge

Both plugins expose the same calls (init, start/stop host, update beacon, kick, start/stop scan, connect, disconnect,
send, poll, shutdown, open settings) and pack their events the same way, read by `Net/NativeEvents.cs`:
`[type u8][peer i32][state u8][rssi i16][address u16+UTF-8][data u16+bytes][name u16+UTF-8]`.

- **Generations.** Start host and connect take a number from the game (`Net/LinkEventFilter.cs`), one per hosting run
  and per connection attempt. The plugin writes it into the state byte of every event about that run or connection
  (the state byte is otherwise only used by Radio events), and the game drops events with an old number: a late
  "disconnected" of a host the game has already left can't drop the next connection, and an old packet can't land in it.
  A kicked player's events are dropped the same way. Host peer numbers are never reused while the app runs.
- **Queues.** Each player has a queue of its own at the host, served in turn; a queue longer than its limit drops its
  oldest whole messages (the framing's first flag marks where one starts). The events waiting for the game are capped
  too (a game that stopped polling: scan reports go first, then whole messages; connection events are always kept).

- **GATT layout.** Service `8C5F0001-2B7E-4D5A-9E3B-4B4F32C0FFEE`; characteristic `...0002` notifies the players (host to
  player), `...0003` takes writes without response (player to host).
- **iOS** (`Plugins/iOS/DTSCoopBLE.mm`, compiled with ARC (it refuses to compile without), CoreBluetooth linked, both by
  `Editor/IosPostBuild`): `CBPeripheralManager` hosts, `CBCentralManager` scans and joins; one serial queue; a central's
  subscription is its connection (iOS tells a peripheral nothing else; a second subscription without an unsubscribe is
  a new connection); a full transmit queue waits for `peripheralManagerIsReadyToUpdateSubscribers`; writes wait for
  `canSendWriteWithoutResponse`. Advertising restarts are serialised (a new name waits for the start in flight; answers
  of a run that has ended are ignored; "already advertising" is success); a failure before the lobby is announced is
  HostFailed, after it advertising is retried with a growing pause. Reconnecting to the host just left waits for the old
  connection's end, so that end isn't read as the new attempt failing. A host that takes the game's service down
  (`didModifyServices`) ends the connection. A peripheral can't hang up on a central, so a kicked player is simply no
  longer listened to and times out. Scanning and advertising are renewed when the app is active again. The Bluetooth
  prompt's text is `NSBluetoothAlwaysUsageDescription`; Bluetooth starts (and iOS asks, and offers to switch Bluetooth
  on when it is off) only when the co-op screen opens.
- **Android** (`Plugins/Android/DtsCoopBle.java`, compiled by Gradle with the build; kept from R8 by a keep rule that
  `Editor/AndroidBluetoothPermissions` adds to `proguard-unity.txt`, since C# reaches it only by name): `BluetoothGattServer`
  and an advertising set (legacy, connectable, scannable; the beacon's scan response is updated in place, so the address
  doesn't change with every update) host, `BluetoothLeScanner` + `BluetoothGatt` join; one handler thread, every task and
  public call guarded (a revoked permission or a dead binder is logged, never a crash). One notification in flight across
  the whole server, players served in turn (a phone that leaves two unanswered is skipped until heard from); one write in
  flight to the host; 1 s watchdogs on both and a 50 ms retry when the stack is busy; service discovery asked twice; MTU
  247 requested; connection priority HIGH. At most 4 scan starts in any 30 s (Android silently blocks a fifth), and a
  stop is delayed a second so a stop and start cost nothing. Hosting failures before the lobby is announced are
  HostFailed ("noAdvertise" on a phone that can't advertise, "timeout" after 6 s); after it, advertising is retried at 1,
  2, 4, then 8 s. Late callbacks of a closed server, connection or advertising start are ignored. A phone that subscribes
  again without having gone is a new connection. Permissions (added to the manifest by the same hook): `BLUETOOTH_SCAN`
  (`neverForLocation`), `BLUETOOTH_CONNECT`, `BLUETOOTH_ADVERTISE` on Android 12+; `BLUETOOTH`, `BLUETOOTH_ADMIN` and
  `ACCESS_FINE_LOCATION` up to Android 11 (where scanning also needs Location switched on: the Join screen says so; see
  the Families note in `docs/GOOGLE_PLAY_LISTING.md`). `android.hardware.bluetooth_le` is declared not required. Some
  Android phones can't advertise: they can't host, but can join ("This phone can't host over Bluetooth. You can still
  join a race.").

## Trying it in the editor

The editor has no Bluetooth, so `CoopService` runs the pretend radio with **practice bots**: real `CoopSession`s that
join your lobby when you host (or host one for you to find when you join), ready up once you have company, and run
each leg at their own pace (their ghosts glide along the ground). The number of bots is `PlayerPrefs` key
`coop.editorBots` (1 to 3, default 2). In a race the HUD has editor-only buttons: **Bot out of range** (it is listed last
after 20 s, and back in the race when brought back), **Bots back**, **Bot host leaves** (when you joined a bot's lobby: watch the hand-over)
and **My Bluetooth** (switch your own pretend Bluetooth off and on).

## Tests

`Tests/Editor/CoopSessionTests.cs` (edit-mode, pure C#, 67 tests): whole lobbies and races on the in-memory radio.

- **Lobby.** Joining in slot order with default names and unique tags; a fifth player turned away; the same name told
  apart by the tag; any player choosing the stage (everyone sees who; readies reset; the last choice wins); the
  countdown only when all are ready; a random stage resolved once; the host closing the lobby; a seat kept through a
  lobby blip; a lost lobby closing; a host's blink; a lobby that can't be advertised; the host removing a player (who
  can't come back); a first join that fails being tried again; a different content fingerprint turned away.
- **Race.** Every phone's race clock within 25 ms on a slow link; the clock put right after a phone slept, and left alone
  when the host changes; finishers placed by time while the others carry on; the winner leaving and keeping first
  place; a racer out of range listed last after the grace period, and back in the race when they return; Bluetooth off
  for 5 s and back with nothing lost; a phone that knows it is listed last; two players split and reunited with both
  runs kept; a finish made while out of touch counting; a player still away when the next race starts; the host's
  Bluetooth going off for good and the next player taking over with finishes intact; the winning host leaving; two
  players, one drops; a phone loading a scene (Busy); a host loading one; a host whose Bluetooth stays off stepping
  down; a host in the background handing over; an iOS host glancing at Control Center keeping the race; a frozen
  ("zombie") host given up on; a finish nobody has seen yet; a new race with the same players; ghost samples; traffic
  within BLE's means; the loading barrier's timeout.
- **Pieces.** The wire format (round trips, truncated messages rejected), framing (a tail whose start was lost is
  never read as a message), beacons from service data and from the 8-character name (every field, 2,000 random
  beacons), 24-bit session ids, the native event decoder, the late-event filter (old connections, old hosting runs,
  kicked players), names (the word filter, with real names it must not catch), tags, standings, the result merge, the
  split rule and its tie-breaks, the clock sync (and its jump detection), ghost interpolation.
- **Chaos and fuzz** (`CoopChaosTests`, `CoopFuzzTests`): randomized storms of radio loss, range splits, freezes and
  leaves on four phones, each checked for one host with everyone joined to it, identical standings everywhere, the
  race over at the end, every phone's own status matching the host's, places 1..k without gaps, steady phones never
  listed out, and no finish lost that a phone staying to the end had seen; and random bytes, and a stranger's noise,
  fed to every message reader.

## What has been checked, and what has not

**Not run in Unity or on a device.** Checked offline (no Unity here):
- the four compile configurations (iOS and Android players, the runtime with editor defines, the editor assembly with
  the edit-mode tests) against the Unity 2021.3 reference assemblies, with no warnings;
- the 67 co-op tests under Mono with a work-alike NUnit (all pass), and the same chaos run at scale: 2,000 storms (half
  with players leaving), 0 failing an invariant; mutation checks (the sleep re-anchor switched off, rules deliberately
  broken) make the tests that cover them fail;
- the iOS plugin syntax- and ARC-checked with clang (`-fobjc-arc -Wall -Wextra`, no warnings) against stand-in headers
  that declare the Foundation, CoreBluetooth and UIKit calls it uses (not Apple's SDK: compile it in Xcode first);
- the Android plugin compiled with `javac --release 11 -Xlint:all` against the Android 14 framework classes (no
  warnings in it; nothing above API 26 is reached unguarded), and its outbound queue (whole-message drops, turns)
  exercised on a desktop JVM;
- string parity: 718 keys in each language.

First-run checklist on devices:

1. Two phones of each kind if possible (iPhone + Android is the important pair). Allow Bluetooth on each. HOST on one,
   JOIN on the others: the lobby shows names, tags, kids and seats.
2. Same name on two phones: the tags differ. Leave a name empty: "Player N" for the seat.
3. Change the stage and the location from a non-host phone: every lobby updates, READY clears. Pick California from a
   phone that has it unlocked while another hasn't: both race in California.
4. All READY: 3-2-1 in the lobby, then the first leg loads on every phone, then 3-2-1-GO together (film two phones side
   by side to compare).
5. Ghosts: in the right place, running, jumping and sliding, name tags readable, edge markers for ghosts out of view.
   Check the lane offset doesn't hide them behind street props in each chapter.
6. Finish order with two players finishing close together.
7. Resilience: Bluetooth off for 5 s on a racer (back in), 30 s (listed last, then back in the race with their run when
   Bluetooth is on again), walk out of range and back; the host's Bluetooth off (another phone takes over within about
   8 s; the race goes on); the winner leaving; the host leaving after winning; an app put in the background for 10 s; an
   iPhone host pulling down Control Center for a moment (nothing should drop); the power button pressed mid-race for
   10 s (the race clock must still agree with the others'); an Android host's address rotating during a long lobby.
8. The host removing a player in the lobby: the removed phone is told and can't rejoin; a relaunch can't either.
9. Android 8-11 phone with Location off: the Join screen asks for it.
10. A phone that can't advertise (some cheap Android phones): HOST says it can't; JOIN works.
11. Battery and heat over a 6-minute route with four phones.
12. A release (minified) Android build: Co-op still finds the plugin (the R8 keep rule).
