# Lecciones aprendidas

Dos partes: las versiones MSX1 y MSX2, y la versión CPC. La última sección de MSX recoge las reglas comunes a todas.

---

# Lecciones de las versiones MSX1 y MSX2

## Contexto

El hack salió en dos versiones MSX: MSX1 en cinta y en ROM ASCII16 de 64 KB, con sprites por hardware para el relleno blanco de los jugadores; y MSX2 en ROM ASCII16 de 256 KB, todo en SCREEN 5 con doble búfer. Las lecciones salen del hilo original (las partes de análisis, MSX1 y MSX2), del resumen de cambios y de las notas de trabajo.

El juego original (Dinamic, 1987) llega en cinta con un cargador BASIC y tres bloques: presentación y biblioteca residente, datos copiados a la RAM de la página 1 oculta bajo la ROM, y el juego en 84D0h. No usa sprites: lo dibuja todo por software.

## MSX1: TMS9918 y sprites híbridos

En MSX1 la mejora con más impacto fue un modo híbrido: el contorno sigue por software y el relleno blanco va con sprites por hardware. Así los jugadores dejan de coger el color de la zona por la que pasan, sin parpadeo.

- **Por qué híbrido.** Un jugador mide unos 24×48 en dos capas. El TMS9918 solo admite 4 sprites de 16×16 por línea y de un color. Con solo el relleno van 6 sprites por jugador, 2 por línea: con los dos jugadores, justo el límite. Se descartaron todo por hardware (parpadeo) y solo MSX2.
- **Volcado parcial.** Copiar a la VRAM solo lo que cambia compensó el coste de los sprites: 4,08-4,24 fotogramas por vuelta frente a 4,16-4,28 del original.
- **Color clash asumido.** El logo de la pista va en negro sobre cian: cualquier otro color cambia la tinta de las celdas de 8×8 y choca con los jugadores. Las repeticiones quedaron sin sprites, con su color clash como el original, tras probar unos sprites por franjas que daban fantasmas. «Nos ahorramos un quebradero de cabeza», dijo el usuario.
- **Velocidad de la VRAM.** Durante la imagen el TMS9918 necesita 29 ciclos o más entre accesos. El original escribía la barra de energía con dos OUT separados por unos 22 y perdía una fila. Arreglo de 1 byte: ADD HL,HL → EX (SP),HL. Los emuladores propios no lo modelan.
- **Intercambio de jugadores en tiempo de ejecución.** El humano juega siempre a la izquierda. Si elige a Romay se intercambian cabezas, saltos en espejo, nombres y capacidades (conmutadas con XOR sobre los saltos JR C/JR NC); al volver al menú todo queda como estaba.
- **ROM de 64 KB.** Reproduce el cargador BASIC: carga cada bloque y vuelve a seleccionar el cartucho en la página 1 tras cada stub, porque estos cambian los slots.

## MSX2: de SCREEN 4 a SCREEN 5

El MSX2 empezó en SCREEN 4 con sprites y acabó en SCREEN 5 con los jugadores dibujados por el VDP: la sincronización entre fondo y sprites era demasiado frágil.

- **SCREEN 4 (primer intento).** Dos capas de sprites por jugador (ropa y piel) llenaban los 8 sprites por línea. Los índices de paleta se eligieron para que el OR de las capas diera blanco. Problemas: solo 2 colores por cada 8 píxeles, líneas de la pista que desaparecían bajo los jugadores y la pista asomando a través de Itu por ir la SAT un fotograma tarde. Hizo falta doble SAT y tabla de color cambiadas con R5/R14.
- **SCREEN 5 (final).** Fondo de 4 bits por píxel, piezas en un atlas de VRAM, dibujo con LMMM (copia con transparencia) sobre doble búfer y cambio de página (R2) en la interrupción. La repetición va a unos 6 fps, frente a 2 en MSX1.
- **Demasiado rápido.** SCREEN 5 iba más rápido que el MSX1 y se puso un limitador: 5 fotogramas por vuelta en PAL y 6 en NTSC. Primero se apoyó en un contador del juego y se colgaba en WebMSX; luego en un contador propio.
- **Menú y descanso.** El juego sigue dibujando su SCREEN 2 en una sombra en VRAM que se convierte a SCREEN 5. Ese código va en la ROM de la página 1 con interrupciones cortadas, porque la tabla IM2 está en la RAM de esa página. Trocearlo (8 celdas por llamada, copias con HMMM, celdas de un color rellenadas) acabó con las interrupciones perdidas.
- **Compatibilidad.** Solo MSX2: en MSX1 muestra «ESTE JUEGO REQUIERE UN MSX2». En turbo R pasa a Z80 con CHGCPU. Se ponen a 0 R25-R27 del V9958 y a RET los ganchos H.TIMI/H.KEYI que instala la disquetera.
- **Espejo.** Los saltos que el MSX1 volteaba en tiempo de ejecución hubo que voltearlos también en el atlas: Jordan miraba al lado contrario.

## Fallos que aparecieron

Los más caros salieron de suposiciones sobre la máquina (slots, BIOS, mapper) que el emulador propio comparte y por eso no detecta.

| Fallo | Causa | Arreglo y lección |
| --- | --- | --- |
| El juego se colgaba desde la cinta TSX | Fichero corrupto: un C1 en lugar de C3 en 9327h y ~540 bytes distintos | Usar el CAS, verificado al 99,7 % contra la RAM del replay de openMSX. Validar siempre el volcado |
| La ROM MSX1 se reiniciaba tras la presentación | Usaba RAMAD1/RAMAD2, que un MSX1 sin disco deja a 0 | Sacar el slot de RAM del de la página 3. No fiarse de variables de la BIOS |
| La ROM MSX2 no arrancaba en openMSX | La autodetección del mapper empataba ASCII16 con Konami | 64 instrucciones LD (77FFh),A de relleno sin uso. Probar con un segundo emulador con BIOS real |
| Turbo R colgado en la presentación | Su slot 0 está expandido: buscar RAM ahí cambiaba la página 3 en uso | Usar el slot de la página 3 y restaurar solo el primario |
| Fila perdida en la barra de energía (del original) | Dos OUT a la VRAM a ~22 ciclos; el TMS pide 29 | EX (SP),HL en lugar de ADD HL,HL (1 byte) |
| MSX2 un 60 % más lento | ENASLT de la BIOS en cada lectura, 4 capas y 24 colores de sprite por fotograma | Blitter propio, salto de filas vacías, OUT A8 directo, colores solo al cambiar. Se había estimado un 10 % |
| Romay recuperaba su cara en los mates | La cabeza va dentro de 14 sprites de cuerpo entero que no pasan por la tabla de cabezas | Retocar esos 14 sprites. Revisar todos los usos de un gráfico |
| Menú roto tras el partido (MSX2) | Una zona dada por libre sí tenía datos (los gráficos del menú) | Restaurarla desde la ROM. Confirmar zonas libres con trazas de acceso |
| «Doble Itu» en el tiro libre | El juego coloca las piezas antes de empezar el fotograma | Vaciar el búfer como el original. Se reprodujo forzando la falta por RAM |
| Línea blanca bajo la pista | La conversión de menú pintaba la línea de fondo de MSX1 | Ignorar esa fila al convertir |
| Cansancio de Jordan «raro» | Un gancho en dirección fija se movió al reensamblar | Ganchos por etiqueta, nunca por dirección |
| Karnov con color de Jordan | Se redefinió una entrada de paleta compartida | Revisar todas las plantillas que usan la entrada |
| Cabeza 17 de Jordan mal | El PNG entregado tenía el fallo, no el motor | Comprobar los datos del usuario antes de tocar el motor |

## Herramientas y método

Todo se hizo con herramientas propias en Python, y cada vez que hubo un fallo difícil sirvió tener un segundo emulador con BIOS real.

- **Desensamblador y ensamblador propios.** El ensamblador se validó reproduciendo byte a byte 5.703 instrucciones del juego. Cada parche comprueba antes el byte original.
- **Emulador propio por capas.** Z80 con slots, ASCII16, IM2 y BIOS simulada; VDP de SCREEN 2; luego SCREEN 4 con sprites modo 2; luego SCREEN 5 con los comandos del VDP y sus tiempos tomados de WebMSX. Un modo con T-states reales (espera M1 y coste de la BIOS) fue el que dio las cifras de rendimiento buenas.
- **Replays de openMSX (.omr).** Cargar el estado del usuario en el emulador propio da un banco de pruebas con su partida exacta.
- **WebMSX sin pantalla.** Con Playwright y BIOS reales de MSX1, MSX2, MSX2+ y turbo R. Encontró lo que el emulador propio no podía: mapper, turbo R y limitador. openMSX no se pudo instalar.
- **Pruebas automáticas.** Partidas con teclas aleatorias de 4.000 a 12.000 fotogramas; fin de partido forzado escribiendo «003» en el reloj; faltas forzadas por RAM.
- **Mediciones.** Perfil por rutina, secciones con interrupciones cortadas, interrupciones perdidas por fotograma y traza de todas las escrituras en VRAM antes de diseñar SCREEN 5.
- **Comprobaciones unitarias.** El cálculo del tiro ejecutado en el emulador frente a la fórmula en Python; el blitter nuevo frente al original en ~400 piezas.
- **Gráficos con el usuario.** Láminas PNG ampliadas (5×5 píxeles por píxel) que él edita y se leen por el centro de cada caja; cada cambio se verifica hasta cero diferencias.
- **git y builds reproducibles.** Un reinicio del entorno borró scripts y emulador antes de usar git. Al final, la build reproduce byte a byte el CAS publicado.

## Lecciones comunes a todas las versiones

Las mismas trampas aparecieron en MSX y en CPC; estas reglas las habrían evitado.

1. **Validar lo que llega.** Volcados contra RAM o VRAM reales, PNG del usuario antes de tocar el motor.
2. **No fiarse de la BIOS ni de la máquina típica.** Slots expandidos, variables sin rellenar, ganchos de la disquetera, mappers autodetectados.
3. **Probar con un segundo emulador con BIOS real.** El propio comparte tus suposiciones y no ve sus fallos.
4. **Medir, no estimar.** Con T-states reales; las estimaciones fallaron por mucho (10 % → 30 % → 60 %). Medir también las capacidades de los jugadores, no calcularlas.
5. **Respetar los tiempos del hardware que el emulador no modela.** VRAM del TMS9918, cambios de tinta a media imagen, resincronización del monitor.
6. **Trocear el trabajo con interrupciones cortadas** y contar las interrupciones perdidas.
7. **Confirmar la memoria "libre" con trazas de acceso.** Fallaron zonas de menú en MSX2 y la pila en CPC.
8. **Ganchos por etiqueta y aserciones sobre los bytes originales.** Las direcciones fijas se mueven al reensamblar.
9. **Replicar lo que el original hacía en tiempo de ejecución** al cambiar la representación de los datos (espejos, cabezas dentro de otros sprites).
10. **Comprobar el comportamiento, no solo que no se cuelgue.** Que la máquina juegue, que cada pantalla se vea, revisar las propias capturas antes de entregarlas.
11. **Decir qué no se ha verificado.** Hardware real, openMSX, Retro Virtual Machine.
12. **A veces gana lo simple.** Repeticiones MSX1 sin sprites; menú del CPC con el fondo del MSX1 en vez de rediseñarlo.
13. **git desde el primer día** y builds que reproduzcan byte a byte lo publicado.

---

# Lecciones del port CPC

## Contexto

En la versión CPC pasamos de una pantalla de 320×200 a una de 256×176, pusimos en el menú el fondo de la versión MSX1 y liberamos unos 5 KB de memoria de vídeo. Quedaron 2.909 bytes libres, frente a 122 al empezar.

Muchas ideas vinieron de un tester con mucho conocimiento del CPC: ajustar el CRTC al tamaño real del juego, aprovechar los huecos entre bloques de vídeo y, como etapa siguiente, ruptura, doble búfer y tiles.

## Pantalla y memoria de vídeo

Ajustar el CRTC al tamaño real del juego libera memoria sin cambiar lo que se ve. Antes de recortar hay que medir qué bytes y líneas usa de verdad cada pantalla, recorriéndolas en el emulador.

- **Medir primero.** Todo el juego cabía en los 256 px centrales (bytes 8-71 de cada línea). La presentación usaba hasta la línea 191; menú, partido y estadísticas, unas 176 líneas.
- **Mismo sitio en el monitor.** Con R1=32 la imagen se recoloca con R2 (46 → 42) para que esos 256 px queden donde estaban. Cambiar R6 solo recorta por abajo y no mueve el sincronismo.
- **64 bytes por línea.** Con R1=32 cada línea mide 64 bytes, igual que el búfer del juego, y las copias siguen usando la misma cadena de LDI.
- **Zonas libres.** Con 22 filas visibles, cada bloque de 2 KB deja libres la fila 0 y desde +5C0h: 640 bytes por bloque. Se añaden a la lista de huecos como memoria normal (código y datos).
- **Tabla de líneas virtual.** La tabla de direcciones de línea guarda la dirección de la columna 8 menos 8. Así el código original que suma "columna" sigue funcionando sin tocarlo, salvo lo que escribe columnas fuera de 8-71.
- **Pantallas de distinto tamaño.** La presentación sigue en 256×192 (R6=24) para no recortar el dibujo. Lo que ocupa de las zonas libres se guarda en un área que aún no se usa al arrancar (el historial de la repetición) y se copia al terminar la presentación.
- **Encuadre común.** Si menú, partido y estadísticas tienen distinta posición vertical, la imagen parece subir y bajar al cambiar de pantalla. Todas usan las líneas 8-183 con el mismo inicio de pantalla.

## Colores por zonas con interrupciones

Cambiar tintas a media pantalla con las interrupciones del gate array da más de cuatro colores en modo 1. Para encajar el cambio se mueve el inicio de la pantalla en memoria, nunca el sincronismo vertical.

- **R13 en vez de R7.** Las interrupciones caen cada 52 líneas desde el VSYNC. Para que caigan entre zonas, la imagen empieza una fila más abajo en memoria (R13=32). Mover el VSYNC (R7) entre pantallas obliga al monitor a volver a engancharse, y en un emulador fiel (Retro Virtual Machine) se nota el tirón.
- **Ajuste fino con espera.** Si la interrupción cae unas líneas antes de donde se necesita, una espera corta dentro del manejador lo arregla (6 líneas = 384 µs, un bucle `dec a / jr nz` de 96 vueltas).
- **Tintas tras el VSYNC.** Cuando el juego vuelve a poner la paleta a media imagen, la parte de arriba sale un cuadro con los colores de abajo: es el destello que se veía al cambiar de nivel. La paleta se enciende justo después del VSYNC y se ponen ya las tintas de la zona de arriba.
- **Nada con la paleta en negro.** Durante los fundidos el manejador no toca tintas.
- **Cinco colores en el menú.** Arriba azul y rojo para el rótulo; desde la línea ~100 esas dos tintas pasan a blanco y rosa para textos y muñecos.
- **Selector de tinta compartido.** Si la interrupción cambia el registro de tinta mientras el código principal está poniendo la paleta, la siguiente tinta del bucle va a la tinta equivocada. Hay que dejar las tintas importantes al final.

## Fallos que aparecieron

Casi todos vinieron de escribir donde no tocaba: tablas desplazadas, saltos mal calculados o memoria que otro usaba en ese momento.

| Fallo | Causa | Cómo evitarlo |
| --- | --- | --- |
| En 1 jugador la máquina no jugaba | La tabla de líneas desplazada del menú seguía activa al dibujar la energía; la dirección dio la vuelta por FFFFh y pisó la rutina de la máquina en 0601h | Restaurar la tabla al salir del menú; que lo que se salga de la pantalla vaya a una línea segura (principio de fila, sin vuelta al sumar 800h) |
| Juego colgado al arrancar | El borrado de pantalla saltaba 840h entre bloques en vez de 800h y acabó pisando la pila | Comprobar a mano la aritmética de cada salto: lo copiado de otra versión con otros tamaños ya no vale |
| Cursor de texto disparatado | El borrado nuevo devolvía HL distinto del original (7571h usa HL+1 como cursor) | Al sustituir una rutina, devolver los mismos registros que la original |
| Pantalla negra tras la presentación | Código colocado en zonas que la presentación aún ocupaba; la interrupción lo ejecutaba antes de copiarlo | En las zonas que llegan tarde, solo datos que se usan después; nada de código |
| Datos del menú corrompidos tras el partido | La pila del original se desborda por encima de C000h al acabar el partido | No usar C000h-C03Fh; en el original caía en pantalla y no se notaba |
| Raya sobre la cabeza del jugador derecho | La cabeza de Romay es más alta y su fila de arriba no se borraba al cambiarla | Borrar la fila sobrante al cambiar de cabeza |
| Destello en el menú al cambiar de nivel | La paleta se reencendía a media imagen | Encenderla tras el VSYNC con las tintas de la zona de arriba |

## Cómo comprobar

Las pruebas que miran "no se cuelga" no bastan: el 1 jugador roto pasó todas las pruebas largas, y la medida de velocidad se hizo con la máquina parada. Lo que sí detectó los fallos:

1. **Inventario de escritores.** Recorrer el juego con un registro de escrituras en pantalla (quién escribe y dónde) en la versión anterior. Lo que escribe fuera de la zona nueva (aquí, columnas fuera de 8-71) es lo que hay que adaptar: el borrado de pantalla, la repetición ampliada y el descompresor.
2. **Vigilar las zonas libres.** Registrar cualquier escritura en ellas desde el menú, descontando las variables y el código que se automodifica dentro de lo colocado. Encontró la franja fuera de pantalla y la pila desbordada.
3. **Comparar memoria con la versión anterior.** Tras recorrer todos los menús, comparar los bytes de código de las dos versiones. La única diferencia debe ser lo esperado.
4. **Comprobar el comportamiento, no solo que no falle.** Que la máquina se mueva sola en 1 jugador y que el segundo jugador no responda a W/S/A/D.
5. **Bisección por parches.** Desactivar cada parche de un módulo por separado para aislar el que rompe algo. Con dos núcleos y un emulador lento, mejor dos pruebas en paralelo que cuatro.
6. **Mirar las capturas.** Todas las pantallas (presentación, menú, elección, posesión, nombres, partido, repetición, descanso, final) después de cada cambio grande.

Ojo con las comparaciones entre versiones: el juego usa el registro R como azar, así que cualquier cambio de tiempos hace que la partida diverja y las capturas no coincidan aunque todo esté bien.

## Trucos de memoria reutilizables

Casi toda la memoria nueva salió de sitios que el juego solo usa en un momento concreto.

- **Pantalla de presentación como cargador.** La presentación se descomprime sobre toda la memoria de vídeo al arrancar; meter en esa misma imagen los datos de las zonas libres los deja colocados sin coste. El bloque que CARGA copia antes de descomprimir puede ir justo detrás del flujo comprimido, así este puede crecer.
- **Áreas que aún no se usan.** El historial de la repetición está sin usar hasta el primer partido: sirve para guardar datos de arranque que luego se copian a su sitio.
- **Bloque de arranque.** El búfer de dibujo está libre durante la carga y la presentación: ahí van el código de arranque y los datos que solo se copian una vez.
- **Compresión por trozos.** Un flujo LZ se puede partir en límites de token y repartir por huecos pequeños (de 64 bytes aquí), con una tabla de punteros; las referencias hacia atrás siguen valiendo porque la salida es continua.
- **Recortar historiales.** La repetición guarda 24 vueltas en vez de 30 sin que se note.
- **Empaquetador con vuelta atrás.** Colocar los trozos de código de mayor a menor en los huecos, con búsqueda con vuelta atrás, aprovecha huecos que un reparto ingenuo deja sin usar.
- **Leer lo libre de verdad.** Antes de usar memoria "libre" del original, comprobar si algo la pisa en tiempo de ejecución: la pila, el desbordamiento de pila o una ruta poco frecuente.

## Próxima etapa: ruptura, doble búfer y tiles

El tester propone rehacer el dibujo del partido en una sola etapa: quitar el búfer oculto de 6,5 KB y dibujar con doble búfer y tiles. Hacerlo por partes no ahorra memoria, porque el búfer sigue haciendo falta hasta el final.

- **Ruptura de pantalla.** Separar con el CRTC la parte fija (público, valla, marcador) de la zona de juego.
- **Doble búfer de 256×96.** La zona de juego ocupa 6 KB; dos copias caben en 12 KB y la memoria de vídeo total quedaría en unos 17 KB (5 KB para público y marcador). Quita el tearing.
- **Tiles.** Reponer el fondo por tiles en vez de copiarlo desde el búfer oculto; quita el búfer y el parpadeo de sprites.
- **Menú y estadísticas sin búfer.** Con la paleta en negro se puede pintar directamente en la memoria de vídeo. Conviene hacerlo a la vez que lo anterior.
