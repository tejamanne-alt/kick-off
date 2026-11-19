using System.Collections.Generic;

namespace DribbleToSchool.Localization
{
    /// <summary>
    /// Florida's own strings (docs/CITIES.md: its three routes, nine legs, stops, the ride and its hazards),
    /// added to each language's table (StringTables.For). Place names on signs stay in English, as every level's signs do.
    /// </summary>
    public static partial class StringTables
    {
        static Dictionary<string, string> FloridaEnglish()
        {
            return new Dictionary<string, string>
            {
                { "city.florida.about", "Three ways to school: Calle Ocho, the river, under the line" },
                { "chapter.6", "Miami" },
                { "route.fl1", "Calle Ocho Bus" }, { "route.fl2", "The River Way" }, { "route.fl3", "Under the Line" },
                { "stop.calleOcho", "Calle Ocho bus stop" }, { "stop.brickell", "Brickell Avenue" }, { "stop.bayfront", "Bayfront Park" },
                { "stop.reysDock", "Uncle Rey's dock" }, { "stop.drugstore", "Drugstore" }, { "stop.underline", "Underline station" },
                { "stop.biscayne", "Biscayne station" }, { "stop.museumPark", "Museum Park" },
                { "stop.calleOcho.to", "the bus stop on Calle Ocho" }, { "stop.brickell.to", "Brickell Avenue" },
                { "stop.bayfront.to", "Bayfront Park" }, { "stop.reysDock.to", "Uncle Rey's dock" }, { "stop.drugstore.to", "the drugstore" },
                { "stop.underline.to", "the station" }, { "stop.biscayne.to", "Biscayne Boulevard" }, { "stop.museumPark.to", "Museum Park" },
                { "district.littleHavana", "Little Havana" }, { "district.brickell", "Brickell" }, { "district.river", "Miami River" },
                { "district.downtown", "Downtown" }, { "district.bay", "Biscayne Bay" }, { "district.museumPark", "Museum Park" },

                { "level.FL1-1", "Little Havana Morning" }, { "level.FL1-2", "Brickell Avenue" },
                { "level.FL1-3", "Bayfront to School" }, { "level.FL2-1", "Riverside Street" },
                { "level.FL2-2", "The Riverwalk" }, { "level.FL2-3", "Downpour to School" },
                { "level.FL3-1", "The Underline" }, { "level.FL3-2", "Biscayne Boulevard" }, { "level.FL3-3", "Museum Park to School" },

                { "sticker.FL1-1", "Cafecito" }, { "sticker.FL1-1.text", "A thimble of sweet Cuban coffee from the walk-up window. Grown-ups only, sadly." },
                { "sticker.FL1-1.hint", "Over the second domino table: a double jump from its top." },
                { "sticker.FL1-2", "Sky Crane" }, { "sticker.FL1-2.text", "The tower cranes over Brickell swing all morning. This one waved." },
                { "sticker.FL1-2.hint", "High over the stack of crates after the bay wind." },
                { "sticker.FL1-3", "Pelican Post" }, { "sticker.FL1-3.text", "Every post on the bayfront has its pelican, and every pelican has opinions." },
                { "sticker.FL1-3.hint", "Up in the fountains' spray: ride the second jet." },
                { "sticker.FL2-1", "Sun Lizard" }, { "sticker.FL2-1.text", "Iguanas bask on every seawall, and leave in a hurry." },
                { "sticker.FL2-1.hint", "Above the second sprinkler: let its spray lift you." },
                { "sticker.FL2-2", "Bascule Bridge" }, { "sticker.FL2-2.text", "Up for the tugs, down for the cars: the river's bridges never sit still." },
                { "sticker.FL2-2.hint", "Over the crates between the first two bridges." },
                { "sticker.FL2-3", "Storm Brolly" }, { "sticker.FL2-3.text", "Summer in Miami: sunshine, a cloudburst, sunshine again. Always carry one." },
                { "sticker.FL2-3.hint", "Under the fourth arcade, out of the rain." },
                { "sticker.FL3-1", "Underline Mural" }, { "sticker.FL3-1.text", "Flowers, waves and birds painted up the pillars under the trains." },
                { "sticker.FL3-1.hint", "Above the tall fitness step." },
                { "sticker.FL3-2", "Clean Sweep" }, { "sticker.FL3-2.text", "The sweeper hums along Biscayne before the city wakes up." },
                { "sticker.FL3-2.hint", "Ride the street sweeper's back to reach it." },
                { "sticker.FL3-3", "Banyan Roots" }, { "sticker.FL3-3.text", "A banyan grows roots from its branches until it stands like a little forest." },
                { "sticker.FL3-3.hint", "At the top of the second banyan's roots." },

                { "ride.peopleMover", "The people mover: round the bay to Biscayne Boulevard" }, { "ride.skip", "Skip" },

                { "hazard.downpour.coming", "It's going to pour: get under cover!" },
                { "hazard.downpour.burst", "Cloudburst!" },

                { "coach.chickens.title", "Chickens: they get out of the way" },
                { "coach.chickens.text", "Roll the ball at a chicken fast and it flutters up out of the way. Bump one slowly and the ball bounces back." },
                { "coach.iguana.title", "Iguana: let it run" },
                { "coach.iguana.text", "Come close and the iguana dashes off along the path. Wait for it to go, or chip the ball over it." },
                { "coach.downpour.title", "Cloudburst: take cover" },
                { "coach.downpour.text", "When the warning shows, get under an arcade or an awning until the burst passes: out in it, the rain slows you down." },
                { "coach.sweeper.title", "Street sweeper: ride its back" },
                { "coach.sweeper.text", "Chip the ball onto the sweeper's flat back (drag up from KICK), JUMP on after it and ride. Or let it pass." },
            };
        }

        static Dictionary<string, string> FloridaSpanish()
        {
            return new Dictionary<string, string>
            {
                { "city.florida.about", "Tres caminos al cole: la Calle Ocho, el río y bajo el tren" },
                { "chapter.6", "Miami" },
                { "route.fl1", "El bus de la Calle Ocho" }, { "route.fl2", "Por el río" }, { "route.fl3", "Bajo el tren" },
                { "stop.calleOcho", "Parada de la Calle Ocho" }, { "stop.brickell", "Avenida Brickell" }, { "stop.bayfront", "Bayfront Park" },
                { "stop.reysDock", "Muelle del tío Rey" }, { "stop.drugstore", "Farmacia" }, { "stop.underline", "Estación del Underline" },
                { "stop.biscayne", "Estación de Biscayne" }, { "stop.museumPark", "Museum Park" },
                { "stop.calleOcho.to", "a la parada de la Calle Ocho" }, { "stop.brickell.to", "a la avenida Brickell" },
                { "stop.bayfront.to", "a Bayfront Park" }, { "stop.reysDock.to", "al muelle del tío Rey" }, { "stop.drugstore.to", "a la farmacia" },
                { "stop.underline.to", "a la estación" }, { "stop.biscayne.to", "al bulevar Biscayne" }, { "stop.museumPark.to", "a Museum Park" },
                { "district.littleHavana", "Pequeña Habana" }, { "district.brickell", "Brickell" }, { "district.river", "Río Miami" },
                { "district.downtown", "Centro" }, { "district.bay", "Bahía Vizcaína" }, { "district.museumPark", "Museum Park" },

                { "level.FL1-1", "Mañana en la Pequeña Habana" }, { "level.FL1-2", "Avenida Brickell" },
                { "level.FL1-3", "Por la bahía al cole" }, { "level.FL2-1", "La calle del río" },
                { "level.FL2-2", "El paseo del río" }, { "level.FL2-3", "Aguacero hasta el cole" },
                { "level.FL3-1", "El Underline" }, { "level.FL3-2", "Bulevar Biscayne" }, { "level.FL3-3", "Por Museum Park al cole" },

                { "sticker.FL1-1", "Cafecito" }, { "sticker.FL1-1.text", "Un dedalito de café cubano de la ventanita. Solo para mayores, qué pena." },
                { "sticker.FL1-1.hint", "Sobre la segunda mesa de dominó: doble salto desde arriba." },
                { "sticker.FL1-2", "Grúa del cielo" }, { "sticker.FL1-2.text", "Las grúas de Brickell giran toda la mañana. Esta te saludó." },
                { "sticker.FL1-2.hint", "Muy alto sobre las cajas después del viento de la bahía." },
                { "sticker.FL1-3", "Poste del pelícano" }, { "sticker.FL1-3.text", "Cada poste de la bahía tiene su pelícano, y cada pelícano su opinión." },
                { "sticker.FL1-3.hint", "Arriba en el chorro de las fuentes: sube con el segundo." },
                { "sticker.FL2-1", "Lagarto al sol" }, { "sticker.FL2-1.text", "Las iguanas toman el sol en los muros del río, y se van con prisa." },
                { "sticker.FL2-1.hint", "Sobre el segundo aspersor: deja que su chorro te suba." },
                { "sticker.FL2-2", "Puente levadizo" }, { "sticker.FL2-2.text", "Arriba para los remolcadores, abajo para los coches: los puentes del río nunca paran." },
                { "sticker.FL2-2.hint", "Sobre las cajas entre los dos primeros puentes." },
                { "sticker.FL2-3", "Paraguas de tormenta" }, { "sticker.FL2-3.text", "Verano en Miami: sol, aguacero y sol otra vez. Lleva siempre uno." },
                { "sticker.FL2-3.hint", "Bajo el cuarto soportal, a cubierto de la lluvia." },
                { "sticker.FL3-1", "Mural del Underline" }, { "sticker.FL3-1.text", "Flores, olas y pájaros pintados en los pilares bajo el tren." },
                { "sticker.FL3-1.hint", "Encima del escalón alto de gimnasia." },
                { "sticker.FL3-2", "Barrido limpio" }, { "sticker.FL3-2.text", "La barredora zumba por Biscayne antes de que despierte la ciudad." },
                { "sticker.FL3-2.hint", "Súbete a la barredora para llegar." },
                { "sticker.FL3-3", "Raíces de banyán" }, { "sticker.FL3-3.text", "El banyán echa raíces desde las ramas hasta parecer un bosquecito." },
                { "sticker.FL3-3.hint", "En lo alto de las raíces del segundo banyán." },

                { "ride.peopleMover", "El tren elevado: por la bahía hasta el bulevar Biscayne" }, { "ride.skip", "Saltar" },

                { "hazard.downpour.coming", "Va a diluviar: ¡a cubierto!" },
                { "hazard.downpour.burst", "¡Aguacero!" },

                { "coach.chickens.title", "Gallinas: se apartan" },
                { "coach.chickens.text", "Si el balón va rápido hacia una gallina, sale volando. Si la tocas despacio, el balón rebota." },
                { "coach.iguana.title", "Iguana: déjala correr" },
                { "coach.iguana.text", "Al acercarte, la iguana sale corriendo por el camino. Espera a que se vaya o pasa el balón por encima." },
                { "coach.downpour.title", "Aguacero: a cubierto" },
                { "coach.downpour.text", "Cuando salga el aviso, ponte bajo un soportal o un toldo hasta que pase: bajo la lluvia vas más lento." },
                { "coach.sweeper.title", "Barredora: súbete detrás" },
                { "coach.sweeper.text", "Pasa el balón a la parte plana de la barredora (arrastra hacia arriba desde CHUTA), SALTA detrás y viaja. O déjala pasar." },
            };
        }
    }
}
