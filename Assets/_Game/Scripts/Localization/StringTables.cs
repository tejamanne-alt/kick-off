using System.Collections.Generic;

namespace DribbleToSchool.Localization
{
    /// <summary>
    /// All UI text. Add a language by adding a table here and its code to Loc.Languages.
    /// Level layouts (signs) stay in English for now; level names are translated.
    /// </summary>
    public static class StringTables
    {
        static Dictionary<string, string> en, es;

        public static Dictionary<string, string> For(string code)
        {
            if (code == "es") return es ?? (es = Spanish());
            return en ?? (en = English());
        }

        static Dictionary<string, string> English()
        {
            return new Dictionary<string, string>
            {
                // Menus
                { "menu.title", "Dribble\nto School" },
                { "menu.play", "PLAY" },
                { "menu.locker", "Locker Room" },
                { "menu.album", "Stickers" },
                { "menu.settings", "Settings" },
                { "menu.credits", "Credits" },
                { "menu.stars", "Stars collected: {0} / {1}" },
                { "menu.map", "Way to School" },
                { "menu.chapter", "Chapter {0}: {1}" },
                { "menu.chapterStars", "Stars {0} / {1}" },
                { "menu.soon", "Coming soon!" },
                { "chapter.1", "Home Street" }, { "chapter.2", "Market" }, { "chapter.3", "The Beach" },
                { "chapter.4", "Underpass" }, { "chapter.5", "Park & School" },

                // Shop
                { "shop.balls", "Balls" }, { "shop.flags", "Flags" }, { "shop.outfits", "Outfits" }, { "shop.trails", "Trails" },
                { "shop.equip", "Equip" }, { "shop.equipped", "Equipped" }, { "shop.owned", "Owned" },
                { "shop.buy", "Buy" }, { "shop.needCoins", "Need more coins" },
                { "rarity.Common", "Common" }, { "rarity.Rare", "Rare" }, { "rarity.Epic", "Epic" },

                // Album & credits
                { "album.title", "Sticker Album" },
                { "album.count", "{0} / {1} stickers found" },
                { "album.missing", "???" },
                { "album.hint", "Each level hides one sticker. Look high and low!" },
                { "credits.title", "Credits" },
                { "credits.body", "Dribble to School\n\nA cozy soccer side-scroller.\nEvery picture and every sound in this game is drawn and composed by code.\n\nMade with Unity.\nThanks for playing!" },

                // Settings
                { "settings.title", "Settings" },
                { "settings.music", "Music" }, { "settings.sfx", "Sound effects" },
                { "settings.haptics", "Vibration" }, { "settings.shake", "Screen shake" },
                { "settings.bell", "School bell timer" }, { "settings.bellHint", "Off = cozy mode, no rush" },
                { "settings.leftHanded", "Left-handed controls" }, { "settings.colorblind", "Colour-blind aim colours" },
                { "settings.language", "Language" },
                { "settings.player", "Player" }, { "settings.boy", "Boy" }, { "settings.girl", "Girl" },
                { "settings.reset", "Reset progress" },
                { "settings.resetConfirm", "Erase all progress, coins and stickers?\nThis can't be undone." },
                { "settings.yes", "Erase" }, { "settings.no", "Keep" },
                { "settings.on", "On" }, { "settings.off", "Off" }, { "settings.done", "Done" },

                // HUD
                { "hud.ready", "Ready..." }, { "hud.go", "GO!" },
                { "hud.bellIn", "Bell {0}" }, { "hud.late", "LATE!" },
                { "hud.perfect", "Perfect x{0}" }, { "hud.juggles", "Juggles {0}" },
                { "hud.jump", "JUMP" }, { "hud.kick", "KICK" },
                { "hud.tooFar", "Too far - get closer to kick" },

                // Toasts
                { "toast.perfect", "Perfect touch!" }, { "toast.perfectN", "Perfect touch x{0}" },
                { "toast.juggle", "Juggle {0}" }, { "toast.checkpoint", "Checkpoint!" },
                { "toast.bell", "BRRRING! The bell! Keep going!" },
                { "toast.dog", "Woof! The dog wants to play" }, { "toast.oops", "Oops - sorry!" },
                { "toast.gate", "Gate open!" }, { "toast.squawk", "Squawk!" }, { "toast.sticker", "Sticker found!" },

                // Losing the ball
                { "lose.ball", "Lost the ball!" }, { "lose.gap", "Into the hole!" }, { "lose.splash", "Splash!" },
                { "lose.tide", "Splash! Wait for the tide" }, { "lose.fell", "Lost the ball!" },
                { "lose.behind", "Left the ball behind!" }, { "lose.honk", "Honk! Wait for the green man" },
                { "lose.checkpoint", "Back to the checkpoint" }, { "lose.offStart", "The ball rolled back home!" },

                // Pause
                { "pause.title", "Paused" }, { "pause.resume", "Resume" }, { "pause.checkpoint", "Back to checkpoint" },
                { "pause.restart", "Restart level" }, { "pause.settings", "Settings" }, { "pause.quit", "Quit to map" },
                { "pause.skip", "Skip level (dev)" },

                // Results
                { "results.made", "Made it to school!" }, { "results.late", "Made it... a bit late!" },
                { "results.challengeDone", "Challenge complete!" }, { "results.challengeFail", "So close - try again!" },
                { "results.reached", "Reached school with the ball" }, { "results.beforeBell", "Before the bell ({0})" },
                { "results.streakCoins", "Streak of {0} and every coin ({1}/{2})" },
                { "results.score", "Score: {0}" }, { "results.reach", "Reach {0}" }, { "results.under", "Under {0}" },
                { "results.starN", "{0}: {1}" },
                { "results.time", "Time {0}" }, { "results.lost", "Balls lost {0}" },
                { "results.coins", "+{0}" }, { "results.newStars", "New stars: {0}" },
                { "results.newSticker", "New sticker for the album!" }, { "results.oldSticker", "Sticker found again" },
                { "results.retry", "Retry" }, { "results.map", "Map" }, { "results.next", "Next" }, { "results.finish", "Finish" },

                // Tutorial hints
                { "tut.dribble", "Hold the arrow buttons to walk. Tap the screen just as you catch up with the ball for a Perfect touch!" },
                { "tut.brake", "Let go of the arrows to stop. Stopping traps the ball under your foot." },
                { "tut.jump", "Tap JUMP or swipe up. Hold for a higher jump." },
                { "tut.kick", "Drag from KICK the way you want the ball to go, then let go. Longer drag = more power. Tap KICK for a quick pass." },
                { "tut.juggle", "Kick the ball up, then tap each time it drops near you to juggle." },
                { "tut.gate", "Locked gate! Kick the ball hard at the call button to buzz it open." },
                { "tut.puddle", "Puddles slow the ball and your feet." },
                { "tut.pedestrian", "The ball bounces off people. Chip it over, or wait for a gap." },
                { "tut.crossing", "Red man means cars are coming! Wait for the green man." },
                { "tut.springboard", "Springboards bounce you and the ball up high." },
                { "tut.tide", "The tide comes in and out. Cross while the water is low." },
                { "tut.seagull", "Seagulls swoop at the ball. Keep it low and close." },
                { "tut.tunnel", "It's dim in the underpass. Keep the ball close, under the lamps." },
                { "tut.pipes", "Pipes roll down the slope. Jump over them!" },
                { "tut.platform", "Chip the ball onto the moving platform, then jump on." },
                { "tut.dog", "Dogs chase low balls. Chip it over their heads!" },
                { "tut.fountain", "The fountain jets lift the ball. Dribble into them!" },
                { "tut.swing", "Chip the ball across, then ride the swing." },

                // Levels
                { "level.L01", "Out the Door" }, { "level.L02", "Parked Cars" }, { "level.L03", "Up the Hill" },
                { "level.L04", "Garden Gate" }, { "level.L05", "Puddle Lane" }, { "level.L06", "Market Morning" },
                { "level.L07", "First Crossing" }, { "level.L08", "Corner Shop" }, { "level.L09", "Fruit Stalls" },
                { "level.L10", "Rush Hour" }, { "level.L11", "Boardwalk" }, { "level.L12", "Low Tide" },
                { "level.L13", "Seagull Bay" }, { "level.L14", "Sandcastle Sprint" }, { "level.L15", "The Underpass" },
                { "level.L16", "Building Site" }, { "level.L17", "Cranes" }, { "level.L18", "Tunnel Run" },
                { "level.L19", "Park Gates" }, { "level.L20", "Fountain Square" }, { "level.L21", "Playground" },
                { "level.L22", "Duck Pond" }, { "level.L23", "The Final Bell" },
                { "level.C01", "Keepy-Uppy" }, { "level.C02", "Window Shopping" }, { "level.C03", "Beach Slalom" },
                { "level.C04", "Site Targets" }, { "level.C05", "Juggle Champion" },
                { "level.test", "Test Track" },
                { "unlock.title", "Unlock the full game" },
                { "unlock.body", "Keep dribbling all the way to school!\n\n4 more chapters, 18 more levels, 4 skill challenges\nand all the stickers to find.\n\nOne purchase. No ads, ever." },
                { "unlock.buy", "Unlock for {0}" }, { "unlock.cta", "Unlock full game" },
                { "unlock.restore", "Restore purchases" }, { "unlock.cancelled", "Purchase cancelled." },
                { "unlock.failed", "The store isn't available right now. Please try again later." },
                { "unlock.nothing", "No previous purchase found." },
            };
        }

        static Dictionary<string, string> Spanish()
        {
            return new Dictionary<string, string>
            {
                { "menu.title", "¡Al Cole\nRegateando!" },
                { "menu.play", "JUGAR" },
                { "menu.locker", "Vestuario" },
                { "menu.album", "Pegatinas" },
                { "menu.settings", "Ajustes" },
                { "menu.credits", "Créditos" },
                { "menu.stars", "Estrellas: {0} / {1}" },
                { "menu.map", "Camino al cole" },
                { "menu.chapter", "Capítulo {0}: {1}" },
                { "menu.chapterStars", "Estrellas {0} / {1}" },
                { "menu.soon", "¡Muy pronto!" },
                { "chapter.1", "Mi calle" }, { "chapter.2", "Mercado" }, { "chapter.3", "La playa" },
                { "chapter.4", "El paso subterráneo" }, { "chapter.5", "Parque y cole" },

                { "shop.balls", "Balones" }, { "shop.flags", "Banderas" }, { "shop.outfits", "Ropa" }, { "shop.trails", "Estelas" },
                { "shop.equip", "Equipar" }, { "shop.equipped", "Equipado" }, { "shop.owned", "Tuyo" },
                { "shop.buy", "Comprar" }, { "shop.needCoins", "Faltan monedas" },
                { "rarity.Common", "Común" }, { "rarity.Rare", "Raro" }, { "rarity.Epic", "Épico" },

                { "album.title", "Álbum de pegatinas" },
                { "album.count", "{0} / {1} pegatinas" },
                { "album.missing", "???" },
                { "album.hint", "Cada nivel esconde una pegatina. ¡Busca arriba y abajo!" },
                { "credits.title", "Créditos" },
                { "credits.body", "Al Cole Regateando\n\nUn juego de fútbol tranquilo.\nCada dibujo y cada sonido está creado con código.\n\nHecho con Unity.\n¡Gracias por jugar!" },

                { "settings.title", "Ajustes" },
                { "settings.music", "Música" }, { "settings.sfx", "Efectos" },
                { "settings.haptics", "Vibración" }, { "settings.shake", "Temblor de cámara" },
                { "settings.bell", "Campana del cole" }, { "settings.bellHint", "Desactivada = modo tranquilo" },
                { "settings.leftHanded", "Controles para zurdos" }, { "settings.colorblind", "Colores para daltónicos" },
                { "settings.language", "Idioma" },
                { "settings.player", "Personaje" }, { "settings.boy", "Chico" }, { "settings.girl", "Chica" },
                { "settings.reset", "Borrar progreso" },
                { "settings.resetConfirm", "¿Borrar todo el progreso, monedas y pegatinas?\nNo se puede deshacer." },
                { "settings.yes", "Borrar" }, { "settings.no", "Mantener" },
                { "settings.on", "Sí" }, { "settings.off", "No" }, { "settings.done", "Listo" },

                { "hud.ready", "¿Listos...?" }, { "hud.go", "¡YA!" },
                { "hud.bellIn", "Campana {0}" }, { "hud.late", "¡TARDE!" },
                { "hud.perfect", "Perfecto x{0}" }, { "hud.juggles", "Toques {0}" },
                { "hud.jump", "SALTO" }, { "hud.kick", "CHUTA" },
                { "hud.tooFar", "Muy lejos: acércate para chutar" },

                { "toast.perfect", "¡Toque perfecto!" }, { "toast.perfectN", "Toque perfecto x{0}" },
                { "toast.juggle", "Toque {0}" }, { "toast.checkpoint", "¡Control!" },
                { "toast.bell", "¡RIIIING! ¡La campana! ¡Sigue!" },
                { "toast.dog", "¡Guau! El perro quiere jugar" }, { "toast.oops", "¡Uy, perdón!" },
                { "toast.gate", "¡Puerta abierta!" }, { "toast.squawk", "¡Cuac!" }, { "toast.sticker", "¡Pegatina!" },

                { "lose.ball", "¡Balón perdido!" }, { "lose.gap", "¡Al hoyo!" }, { "lose.splash", "¡Chof!" },
                { "lose.tide", "¡Chof! Espera a la marea" }, { "lose.fell", "¡Balón perdido!" },
                { "lose.behind", "¡Te dejaste el balón!" }, { "lose.honk", "¡Piii! Espera al muñeco verde" },
                { "lose.checkpoint", "Vuelta al control" }, { "lose.offStart", "¡El balón volvió a casa!" },

                { "pause.title", "Pausa" }, { "pause.resume", "Seguir" }, { "pause.checkpoint", "Volver al control" },
                { "pause.restart", "Reiniciar nivel" }, { "pause.settings", "Ajustes" }, { "pause.quit", "Salir al mapa" },
                { "pause.skip", "Saltar nivel (dev)" },

                { "results.made", "¡Llegaste al cole!" }, { "results.late", "Llegaste... ¡un poco tarde!" },
                { "results.challengeDone", "¡Reto superado!" }, { "results.challengeFail", "¡Casi! Inténtalo otra vez" },
                { "results.reached", "Llegaste con el balón" }, { "results.beforeBell", "Antes de la campana ({0})" },
                { "results.streakCoins", "Racha de {0} y todas las monedas ({1}/{2})" },
                { "results.score", "Puntos: {0}" }, { "results.reach", "Llega a {0}" }, { "results.under", "Menos de {0}" },
                { "results.starN", "{0}: {1}" },
                { "results.time", "Tiempo {0}" }, { "results.lost", "Balones perdidos {0}" },
                { "results.coins", "+{0}" }, { "results.newStars", "Estrellas nuevas: {0}" },
                { "results.newSticker", "¡Pegatina nueva para el álbum!" }, { "results.oldSticker", "Pegatina repetida" },
                { "results.retry", "Repetir" }, { "results.map", "Mapa" }, { "results.next", "Siguiente" }, { "results.finish", "Fin" },

                { "tut.dribble", "Mantén las flechas para caminar. ¡Toca la pantalla justo al alcanzar el balón para un toque perfecto!" },
                { "tut.brake", "Suelta las flechas para pararte. Al pararte controlas el balón." },
                { "tut.jump", "Toca SALTO o desliza hacia arriba. Mantén para saltar más." },
                { "tut.kick", "Arrastra desde CHUTA hacia donde quieras mandar el balón y suelta. Toca CHUTA para un pase rápido." },
                { "tut.juggle", "Levanta el balón y toca cada vez que baje para hacer toques." },
                { "tut.gate", "¡Puerta cerrada! Chuta fuerte al botón del portero automático para abrirla." },
                { "tut.puddle", "Los charcos frenan el balón y tus pies." },
                { "tut.pedestrian", "El balón rebota en la gente. Pásalo por encima o espera." },
                { "tut.crossing", "¡Muñeco rojo: vienen coches! Espera al muñeco verde." },
                { "tut.springboard", "Los trampolines te lanzan alto a ti y al balón." },
                { "tut.tide", "La marea sube y baja. Cruza cuando el agua esté baja." },
                { "tut.seagull", "Las gaviotas atacan el balón. Mantenlo bajo y cerca." },
                { "tut.tunnel", "El paso subterráneo está en penumbra. Mantén el balón cerca, bajo las lámparas." },
                { "tut.pipes", "Los tubos ruedan por la cuesta. ¡Sáltalos!" },
                { "tut.platform", "Sube el balón a la plataforma móvil y salta detrás." },
                { "tut.dog", "Los perros persiguen balones bajos. ¡Pásalo por encima!" },
                { "tut.fountain", "El agua de la fuente levanta el balón. ¡Llévalo dentro!" },
                { "tut.swing", "Pasa el balón al otro lado y súbete al columpio." },

                { "level.L01", "Salir de casa" }, { "level.L02", "Coches aparcados" }, { "level.L03", "Cuesta arriba" },
                { "level.L04", "La verja del jardín" }, { "level.L05", "Calle de los charcos" }, { "level.L06", "Mañana de mercado" },
                { "level.L07", "El primer paso de cebra" }, { "level.L08", "La tienda de la esquina" }, { "level.L09", "Puestos de fruta" },
                { "level.L10", "Hora punta" }, { "level.L11", "El paseo" }, { "level.L12", "Marea baja" },
                { "level.L13", "Bahía de gaviotas" }, { "level.L14", "Carrera de castillos" }, { "level.L15", "El paso subterráneo" },
                { "level.L16", "La obra" }, { "level.L17", "Grúas" }, { "level.L18", "Carrera en el túnel" },
                { "level.L19", "Puertas del parque" }, { "level.L20", "Plaza de la fuente" }, { "level.L21", "Columpios" },
                { "level.L22", "El estanque de patos" }, { "level.L23", "La última campana" },
                { "level.C01", "Toques" }, { "level.C02", "De escaparates" }, { "level.C03", "Eslalon en la playa" },
                { "level.C04", "Dianas en la obra" }, { "level.C05", "Campeón de toques" },
                { "level.test", "Pista de prueba" },
                { "unlock.title", "Desbloquea el juego completo" },
                { "unlock.body", "¡Sigue regateando hasta el cole!\n\n4 capítulos más, 18 niveles, 4 retos\ny todas las pegatinas.\n\nUn solo pago. Sin anuncios." },
                { "unlock.buy", "Desbloquear por {0}" }, { "unlock.cta", "Desbloquear juego completo" },
                { "unlock.restore", "Restaurar compras" }, { "unlock.cancelled", "Compra cancelada." },
                { "unlock.failed", "La tienda no está disponible. Inténtalo más tarde." },
                { "unlock.nothing", "No hay compras anteriores." },
            };
        }
    }
}
