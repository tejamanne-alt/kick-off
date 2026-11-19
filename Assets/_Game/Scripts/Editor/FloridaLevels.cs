using UnityEngine;
using TrackBuilder = DribbleToSchool.EditorTools.LevelBuildKit.TrackBuilder;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Florida's own levels (docs/CITIES.md, "Florida (Miami), USA"): three routes from the ranch house in Little Havana to
    /// Bayside Elementary downtown, each leg one stretch of the real trip with play of its own. The same units and rules as the
    /// original town's (GreyboxLevels: metres, the kid runs about 4.2 m/s, plain gaps up to 2 m, a double jump about 3.6 m far
    /// and 2.2 m up; x = 0 is where the leg's own street begins, 12 m after the stop it starts at).
    /// - FL1 Calle Ocho Bus: Little Havana Morning (roosters and hens, the domino park, a sprinkler), then from the stop where the
    ///   bus is left (not played) Brickell Avenue (scooters across the sidewalk, the bay wind between the towers, the river's
    ///   drawbridge), Bayfront to School (pelicans off the posts, the fountain plaza, the crossing guard's corner).
    /// - FL2 The River Way: Riverside Street (iguanas on the seawall, sprinklers, the golf cart), the Riverwalk (three drawbridges
    ///   over the river's slips), Downpour to School (bursts of rain to shelter from under the arcades, flooded gutters, gusts).
    /// Every leg is a dribble: the mini-game legs (the Metrobus, Uncle Rey's Boat, the Drugstore) were removed in v128.
    /// - FL3 Under the Line: the Underline (fitness stations, the dog run, cyclists on the bike path), the people mover between
    ///   (Levels/Rides), Biscayne Boulevard (pelicans on the lamps, the street sweeper), Museum Park to School (the banyans' roots,
    ///   skateboarders, the kite fliers' wind off the bay).
    /// Every leg's layout passes LevelFeasibility (run by the builder) and the coin audit. The streets are the look chapter's in
    /// Florida's streets until Florida's own districts are modelled from the references.
    /// </summary>
    public static class FloridaLevels
    {
        static readonly Color CoatA = new Color(0.95f, 0.55f, 0.45f);
        static readonly Color CoatB = new Color(0.25f, 0.6f, 0.62f);
        static readonly Color CoatC = new Color(0.95f, 0.82f, 0.35f);
        static readonly Color CoatD = new Color(0.55f, 0.4f, 0.75f);
        static readonly Color DogTan = new Color(0.8f, 0.62f, 0.4f);
        static readonly Color DogBlack = new Color(0.22f, 0.2f, 0.2f);

        // ===================== FL1 Calle Ocho Bus =====================

        /// <summary>FL1-1: home to the bus stop on Calle Ocho, through Little Havana's morning.</summary>
        public static void LittleHavana(TrackBuilder t)
        {
            t.Walls(-8f, 112f);
            t.Start(0f);
            t.Ground(-8f, 112f);
            t.Sign("Little Havana!\nChickens rule these streets", new Vector2(3f, 3.4f));

            t.Rooster(9f, 15f);
            t.Rooster(12f, 18f, true, 0f, 1.3f);
            t.Sign("Roll it fast and they\nflutter out of the way", new Vector2(12f, 3.6f));
            t.CoinRow(8f, 18f, 0.5f, 5);

            t.Sprinkler(25f);
            t.CoinArc(24.2f, 25.8f, 2.7f, 0.6f, 3);
            t.Wall(31f, 0.3f, 0f, 0.6f);
            t.Checkpoint(34f);

            // The little park: domino tables under the pergola, to hop over or stand on.
            t.Sign("Domino park:\nhop over the tables", new Vector2(38f, 3.6f));
            t.DominoTable(41f);
            t.DominoTable(46.5f);
            t.CoinRow(40.6f, 41.4f, 1.3f, 2);
            t.CoinRow(46.1f, 46.9f, 1.3f, 2);
            t.Sticker(new Vector2(46.5f, 3.1f));

            t.SlideUnder(54f, TrackBuilder.SlideLook.StallAwning);
            t.CoinRow(53.2f, 54.8f, 0.32f, 3);
            t.Rooster(59f, 66f, false, 0f, 2.1f);
            t.Rooster(61f, 68f, true, 0f, 0.4f);
            t.Checkpoint(70f);

            t.Wall(77f, 0.8f);
            t.Sign("A cafecito window:\nmind the queue", new Vector2(80f, 3.4f));
            t.Pedestrian(82f, 88f, CoatA);
            t.Puddle(91f, 94f);
            t.CoinArc(75.8f, 78.2f, 1.2f, 1.2f, 3);
            t.CoinRow(91.5f, 93.5f, 0.6f, 3);
            t.Goal(104f);
        }

        /// <summary>FL1-2: Brickell Avenue, from the bus stop between the towers to the river's drawbridge and the bayfront.</summary>
        public static void BrickellAvenue(TrackBuilder t)
        {
            t.Walls(-8f, 128f);
            t.Start(0f);
            t.Ground(-8f, 82f);
            t.Sign("Brickell Avenue:\nscooters everywhere!", new Vector2(3f, 3.4f));

            t.Scooter(9f);
            t.Scooter(13f, 0f, true);
            t.Scooter(16.5f);
            t.CoinArc(8.2f, 9.8f, 0.6f, 0.9f, 3);
            t.CoinArc(15.7f, 17.3f, 0.6f, 0.9f, 3);

            t.Checkpoint(21f);
            t.Sign("Wind off the bay,\nbetween the towers", new Vector2(24f, 3.6f));
            t.Wind(24f, 38f, 0f, 5f, new Vector2(-5f, 0f), 3.6f);
            t.SlideUnder(31f, TrackBuilder.SlideLook.ScaffoldGantry);
            t.CoinRow(30.2f, 31.8f, 0.32f, 3);
            t.CrateStack(41f);
            t.Pedestrian(45f, 51f, CoatB);

            t.Checkpoint(55f);
            t.Scooter(59f);
            t.Scooter(62f);
            t.Wall(67f, 0.9f);
            t.CoinArc(65.8f, 68.2f, 1.3f, 1.2f, 3);
            t.Sticker(new Vector2(41f, 3.8f));

            t.Checkpoint(72f);
            // The Miami River: its bascule bridge rising for a tug.
            t.Drawbridge(82f, 88f, 0f, 2f);
            t.Sign("The river's drawbridge!\nWait for it to come down", new Vector2(79.5f, 3.8f));
            t.Ground(88f, 128f);
            t.Checkpoint(90f);
            t.Pedestrian(98f, 106f, CoatC);
            t.Wall(110f, 0.3f, 0f, 0.6f);
            t.CoinRow(94f, 104f, 0.5f, 5);
            t.Goal(118f);
        }

        /// <summary>FL1-3: along the bayfront to Bayside Elementary.</summary>
        public static void Bayfront(TrackBuilder t)
        {
            t.Walls(-8f, 116f);
            t.Start(0f);
            t.Ground(-8f, 116f);
            t.Sign("Bayfront Park:\npelicans on every post", new Vector2(3f, 3.4f));

            t.Pelican(22f, 8f, 2.6f);
            t.CoinRow(10f, 20f, 0.5f, 5);
            t.Wall(25f, 0.3f, 0f, 0.6f);
            t.Checkpoint(28f);

            t.Sign("The fountain plaza:\nride the jets", new Vector2(31f, 3.6f));
            t.Fountain(34f, 0f, 2.8f, 16f);
            t.Fountain(38f, 0f, 3.2f, 18f);
            t.CoinArc(33.5f, 38.5f, 2.4f, 0.8f, 5);
            t.Sticker(new Vector2(38f, 4.6f));
            t.SlideUnder(45f, TrackBuilder.SlideLook.BoatTrestles);

            t.Checkpoint(50f);
            t.Pelican(66f, 52f, 2.4f, 1.6f);
            t.Iguana(56f, 61f);
            t.Wall(64f, 0.8f);
            t.CoinArc(62.8f, 65.2f, 1.2f, 1.2f, 3);

            t.Checkpoint(70f);
            t.Sign("The crossing guard's corner:\nwait for the green man", new Vector2(74f, 3.6f));
            t.Crossing(78f, 84f);
            t.CoinRow(88f, 96f, 0.5f, 4);
            t.Goal(104f);
        }

        // ===================== FL2 The River Way =====================

        /// <summary>FL2-1: home down Riverside Street to Uncle Rey's dock on the Miami River.</summary>
        public static void RiversideStreet(TrackBuilder t)
        {
            t.Walls(-8f, 100f);
            t.Start(0f);
            t.Ground(-8f, 100f);
            t.Sign("Down to the river:\nmind the iguanas!", new Vector2(3f, 3.4f));

            t.Sprinkler(14f);
            t.CoinArc(13.2f, 14.8f, 2.7f, 0.6f, 3);
            t.Iguana(21f, 27f);
            t.Sign("Iguanas bolt when you\ncome close: let them go", new Vector2(20f, 3.8f));
            t.CoinRow(20f, 28f, 0.5f, 4);
            t.Checkpoint(31f);

            t.GolfCart(35f, 43f);
            t.Sign("Golf cart!\nHop on and ride", new Vector2(36f, 3.6f));
            t.CoinRow(37f, 39f, 1.95f, 3);
            t.Checkpoint(47f);

            t.Iguana(52f, 58f);
            t.Iguana(56f, 61f);
            t.Sprinkler(64f);
            t.Wall(70f, 0.8f);
            t.CoinArc(68.8f, 71.2f, 1.2f, 1.2f, 3);
            t.Sticker(new Vector2(64f, 4.4f));
            t.Checkpoint(73f);
            t.SlideUnder(78f, TrackBuilder.SlideLook.AppleBough);   // (a mango tree's bough over the sidewalk)
            t.CoinRow(77.2f, 78.8f, 0.32f, 3);
            t.Goal(90f);
        }

        /// <summary>FL2-2: the Riverwalk, under the drawbridges over the river's slips, to the drugstore.</summary>
        public static void Riverwalk(TrackBuilder t)
        {
            t.Walls(-8f, 124f);
            t.Start(0f);
            t.Ground(-8f, 20f);
            t.Sign("The Riverwalk:\nthree drawbridges!", new Vector2(3f, 3.4f));
            t.Wall(9f, 0.45f, 0f, 0.5f);     // mooring bollards
            t.Wall(13f, 0.45f, 0f, 0.5f);
            t.CoinArc(8.2f, 9.8f, 0.9f, 0.9f, 3);
            t.CoinArc(12.2f, 13.8f, 0.9f, 0.9f, 3);

            t.Drawbridge(20f, 25f, 0f, 0f);
            t.Ground(25f, 52f);
            t.Checkpoint(27f);
            t.CrateStack(34f);
            t.Iguana(39f, 45f);
            t.Sticker(new Vector2(34f, 3.8f));

            t.Drawbridge(52f, 57f, 0f, 3f);
            t.Ground(57f, 86f);
            t.Checkpoint(59f);
            t.SlideUnder(66f, TrackBuilder.SlideLook.BoatTrestles);
            t.CoinRow(65.2f, 66.8f, 0.32f, 3);
            t.Pedestrian(71f, 78f, CoatD);

            t.Drawbridge(86f, 91f, 0f, 6f);
            t.Ground(91f, 124f);
            t.Checkpoint(93f);
            t.Wall(100f, 0.45f, 0f, 0.5f);
            t.Wall(103f, 0.8f);
            t.CoinRow(94f, 99f, 0.5f, 3);
            t.CoinArc(101.8f, 104.2f, 1.2f, 1.2f, 3);
            t.Goal(114f);
        }

        /// <summary>FL2-3: downtown in a tropical cloudburst, from arcade to arcade, to the school.</summary>
        public static void Downpour(TrackBuilder t)
        {
            t.Walls(-8f, 128f);
            t.Start(0f);
            t.Ground(-8f, 128f);
            t.Sign("A cloudburst!\nShelter under the arcades", new Vector2(3f, 3.4f));
            t.DowntownDownpour(-8f, 128f, 104f);

            t.Arcade(6f, 14f);
            t.Puddle(17f, 21f);
            t.Wall(23f, 0.3f, 0f, 0.6f);
            t.Checkpoint(25f);
            t.Arcade(27f, 34f, 0f, new Color(0.96f, 0.82f, 0.7f));
            t.Wind(34f, 46f, 0f, 5f, new Vector2(-4.5f, 0f), 3.8f);
            t.Puddle(38f, 42f);
            t.CoinRow(38.5f, 41.5f, 0.6f, 3);

            t.Arcade(46f, 54f);
            t.Checkpoint(50f);
            t.SlideUnder(57f, TrackBuilder.SlideLook.RollShutter);
            t.CoinRow(56.2f, 57.8f, 0.32f, 3);
            t.Puddle(60f, 64f);
            t.Arcade(67f, 74f, 0f, new Color(0.82f, 0.9f, 0.88f));
            t.Sticker(new Vector2(70.5f, 2.2f));

            t.Checkpoint(76f);
            t.Wind(76f, 88f, 0f, 5f, new Vector2(4f, 0f), 3.4f);
            t.Puddle(80f, 84f);
            t.Wall(86f, 0.8f);
            t.CoinArc(84.8f, 87.2f, 1.2f, 1.2f, 3);
            t.Arcade(89f, 96f);
            t.Pedestrian(98f, 104f, CoatB);
            t.Sign("The sun's back!", new Vector2(106f, 3.4f));
            t.CoinRow(106f, 114f, 0.5f, 4);
            t.Goal(118f);
            t.FloridaDone();
        }

        // ===================== FL3 Under the Line =====================

        /// <summary>FL3-1: home along the Underline, the park under the elevated railway, to the station.</summary>
        public static void Underline(TrackBuilder t)
        {
            t.Walls(-8f, 110f);
            t.Start(0f);
            t.Ground(-8f, 110f);
            t.Sign("The Underline:\na park under the trains", new Vector2(3f, 3.4f));

            t.Sign("Fitness stations:\nup the steps!", new Vector2(10f, 3.6f));
            t.Platform(13f, 15f, 0.8f);
            t.Platform(16.5f, 18.5f, 1.5f);
            t.CoinRow(16.8f, 18.2f, 2.2f, 2);
            t.SlideUnder(25f, TrackBuilder.SlideLook.PipeRack);    // (the pull-up bars)
            t.CoinRow(24.2f, 25.8f, 0.32f, 3);
            t.Checkpoint(29f);

            t.Sign("The dog run!", new Vector2(33f, 3.4f));
            t.Dog(34f, 42f, DogTan);
            t.Dog(38f, 45f, DogBlack);
            t.CoinArc(36f, 42f, 1.6f, 1f, 4);
            t.Checkpoint(48f);

            t.Sign("Bike path!\nCyclists coming through", new Vector2(51f, 3.6f));
            t.Pedestrian(52f, 66f, CoatC, 0f, 3.4f);
            t.Pedestrian(55f, 68f, CoatA, 0f, 3f);
            t.Sticker(new Vector2(17.5f, 3.6f));
            t.Checkpoint(71f);

            t.Wall(75f, 0.9f);
            t.Pit(81f, 83f);
            t.Sign("Chip it over the\ndrainage ditch", new Vector2(79f, 3.2f));
            t.CoinArc(73.8f, 76.2f, 1.3f, 1.2f, 3);
            t.CoinArc(80.5f, 83.5f, 0.7f, 1.3f, 3);
            t.CoinRow(88f, 94f, 0.5f, 3);
            t.Goal(100f);
        }

        /// <summary>FL3-2: off the people mover, along Biscayne Boulevard to Museum Park.</summary>
        public static void BiscayneBoulevard(TrackBuilder t)
        {
            t.Walls(-8f, 112f);
            t.Start(0f);
            t.Ground(-8f, 112f);
            t.Sign("Biscayne Boulevard:\npelicans on the lamps", new Vector2(3f, 3.4f));

            t.Pelican(18f, 6f, 2.6f);
            t.CoinRow(8f, 16f, 0.5f, 4);
            t.Checkpoint(22f);
            t.Sign("The street sweeper!\nRide its back, or let it pass", new Vector2(25f, 3.8f));
            t.Sweeper(26f, 44f);
            t.CoinRow(30f, 34f, 2.3f, 3);
            t.Sticker(new Vector2(36f, 3.8f));

            t.Checkpoint(48f);
            t.Pelican(62f, 48f, 2.5f, 2f);
            t.Wall(54f, 0.3f, 0f, 0.6f);
            t.Wall(58f, 0.8f);
            t.CoinArc(56.8f, 59.2f, 1.2f, 1.2f, 3);

            t.Checkpoint(64f);
            t.Crossing(70f, 76f);
            t.SlideUnder(84f, TrackBuilder.SlideLook.BoomBarrier);
            t.CoinRow(83.2f, 84.8f, 0.32f, 3);
            t.Scooter(90f);
            t.CoinRow(92f, 98f, 0.5f, 3);
            t.Goal(102f);
        }

        /// <summary>FL3-3: through Museum Park under the banyans, to Bayside Elementary.</summary>
        public static void MuseumPark(TrackBuilder t)
        {
            t.Walls(-8f, 116f);
            t.Start(0f);
            t.Ground(-8f, 116f);
            t.Sign("Museum Park:\nclimb the banyan's roots", new Vector2(3f, 3.4f));

            t.Platform(13f, 16f, 0.9f);
            t.Platform(17.5f, 21f, 1.7f);
            t.CoinRow(18f, 20.5f, 2.4f, 3);
            t.SlideUnder(28f, TrackBuilder.SlideLook.OakBough);       // (an arch of the banyan's aerial roots)
            t.CoinRow(27.2f, 28.8f, 0.32f, 3);
            t.Checkpoint(32f);

            t.Sign("Skateboarders!", new Vector2(35f, 3.4f));
            t.Pedestrian(36f, 48f, CoatD, 0f, 3.2f);
            t.Sprinkler(52f);
            t.CoinArc(51.2f, 52.8f, 2.7f, 0.6f, 3);
            t.Checkpoint(55f);

            t.Sign("Kite fliers' wind\noff the bay", new Vector2(58f, 3.6f));
            t.Wind(58f, 72f, 0f, 5f, new Vector2(-4f, 0f), 3f);
            t.Platform(76f, 79f, 1f);
            t.Platform(80.5f, 83.5f, 1.9f);
            t.CoinRow(81f, 83f, 2.6f, 3);
            t.Sticker(new Vector2(82f, 4.2f));
            t.Checkpoint(86f);
            t.Wall(90f, 0.3f, 0f, 0.6f);
            t.CoinRow(92f, 100f, 0.5f, 4);
            t.Goal(106f);
        }
    }
}
