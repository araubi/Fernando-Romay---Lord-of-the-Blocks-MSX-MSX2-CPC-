# Fernando Martín Basket Master – Executive (Dinamic, 1987, MSX1)
## Análisis del desensamblado

> **Actualización (versión CAS + snapshot openMSX):** el desensamblado se ha rehecho a partir del `.cas`. El `.tsx` contiene **datos corruptos** (ver §8), y `9327h` valía `C1` en vez de `C3`, por lo que el listado anterior decodificaba mal esa rutina.

**Archivo analizado:** `…v0_8_1b_.tsx` – no es TypeScript, es una **imagen de cinta MSX en formato TSX** (extensión de TZX para MSX, bloques `4Bh` KCS). Metadatos: *makeTSX v0.8.1b*, TOSEC `Fernando Martin Basket Master – Executive (1987)(Dinamic)(ES)[!][RUN'CAS-'][v0.8.1b]`. Se carga con `RUN"CAS:"`.

Archivos generados:

| Archivo | Contenido |
|---|---|
| `basket_master_msx.asm` | Desensamblado completo de la imagen de memoria final del juego (`84D0h–DD18h`, ~22 KB, 7.200 líneas) |
| `basket_master_cargadores.asm` | Programa BASIC y los dos *stubs* de carga (ficheros 1 y 2) con comentarios línea a línea |
| este documento | Mapa de la cinta, de memoria, arquitectura y rutinas identificadas |

---

## 1. Estructura de la cinta

| Bloque | Tipo | Contenido |
|---|---|---|
| 0–3 | Info | makeTSX, orden de carga, nombre TOSEC, metadatos |
| 4–5 | BASIC | cabecera `BASKET` + programa de 4 líneas |
| 6–7 | Binario | **Fichero 1**: `B3B0h–DD18h`, exec `CF08h` (10.601 bytes) |
| 8–9 | Binario | **Fichero 2**: `8534h–CFF3h`, exec `CF08h` (19.136 bytes) |
| 10–11 | Binario | **Fichero 3**: `84D0h–CD30h`, exec `84D0h` (18.529 bytes) – **el juego** |

Programa BASIC:

```basic
10 KEYOFF:CLEAR 200,34000!:COLOR 1,1,1:SCREEN 2
20 BLOAD"cas:",R
30 BLOAD"cas:",R
40 BLOAD"cas:",R
```

`CLEAR 200,34000` fija HIMEM en `84D0h` (34000), justo donde se carga el fichero 3, y `,R` ejecuta cada binario nada más cargarlo.

## 2. Qué hace cada fichero

**Fichero 1 (exec `CF08h`)** – pantalla de presentación. Vuelca `1800h` bytes a la tabla de patrones de SCREEN 2 (VRAM `0000h`) y expande `300h` bytes a la tabla de colores (VRAM `2000h`) repitiendo cada byte 8 veces. Además trae la **biblioteca residente** (`CFF4h–DD18h`) que sobrevivirá hasta el final.

**Fichero 2 (exec `CF08h`)** – sobrescribe el stub anterior (mismo exec). Hace un truco de slots curioso:
1. Parchea la propia biblioteca (`D3CCh` pasa a leer el PPI `A8h` en vez de llamar a `RSLREG`; las `CALL ENASLT` de `D414h/D440h` apuntan a una copia de ENASLT en RAM en `CF7Ah`), de modo que puede cambiar slots **sin depender de la BIOS**.
2. Busca RAM para la **página 0**, copia `0B40h` bytes `C394h → 0007h` y restaura la ROM.
3. Busca RAM para la **página 1**, copia `3E60h` bytes `8534h → 415Ah` y restaura la ROM.

Así deja datos (gráficos/tablas) en **RAM oculta bajo la ROM**. Al arrancar, el juego activa la RAM de página 1 (`LIB_INIT`). La llamada a `CF36h` (desde `A53Ah`) copia `0007h → E740h`, pero en el snapshot de openMSX ambas zonas conservan el patrón inicial de RAM (`FFFEh`): ese bloque de página 0 no llega a contener datos útiles (probable resto del cargador). El resto de este fichero (`8534h–CD30h`) lo pisa el fichero 3.

**Fichero 3 (exec `84D0h`)** – el juego. Memoria final resultante:

| Rango | Procedencia | Contenido |
|---|---|---|
| `84D0–CD30` | Fichero 3 | código y datos del juego |
| `CD31–CFF3` | Cola de F2 | stub de slots (`CF08–CFF3`) |
| `CFF4–DD18` | Cola de F1 | biblioteca residente + datos |
| `4000–4122` | RAM pág. 1 | tabla IM2, teclado, contadores, variables de la biblioteca |
| `415A–7FB9` | RAM pág. 1 (copiado por F2) | datos gráficos |

## 3. Arranque del juego (`84E8h`)

1. `CALL A0A1h` → `A53Ah`: fija color, **llama a `CF36h`** (copia `0B40h` bytes de la RAM de página 0, `0007h`, a `E740h`, es decir, trae los datos ocultos por el fichero 2 a RAM normal) y salta a `AC44h` (configuración).
2. Parchea `D4CAh` con `RET` (para que `LIB_INIT` no borre la pantalla), llama a **`LIB_INIT` (`D358h`)** y restaura el `CALL`.
3. Muestra la pantalla/menú (`AA7C`, `CC76`), bucle `MENU_PRINCIPAL` (`8508h`).
4. Entra en el **bucle principal** (`8554h`), una iteración por frame.

### Bucle principal (`8554h`)
```
COPIA_BUFFER_0E00     ; LDIR 0E00h bytes B498h -> C298h
LA092 / L8A23 / L9382 ; lógica de partido (reloj, estado)
ACTUALIZA_JUGADOR (IX=V940B, IY=V9425)   ; jugador 1
ACTUALIZA_JUGADOR (IX=V9425, IY=V940B)   ; jugador 2
LA09E / L9385 / API_JUEGO / LB1FE …      ; marcador, sprites, fin de partido
```
Los dos jugadores son **estructuras de 26 bytes** (`940Bh` y `9425h`), accedidas con `IX/IY` (`IX+0` banderas de estado; `IX+2/3` y `IX+4/5` son palabras de 16 bits, probablemente coordenadas). La rutina `ACTUALIZA_JUGADOR` (`93BBh`) recibe «el propio» en IX y «el rival» en IY.

### Tablas de salto del juego
- `84D0h` (8 entradas): `INICIO` y 7 modos de juego (`8C60`, `8ADD`, `90EF`, `8C16`, `870E`, `8F76`, `8E5A`).
- `9379h` (27 entradas): «API» interna (impresión, marcador, físicas de jugadores…). Ej.: `9397h` → imprimir cadena terminada en `FFh` en la posición HL.
- `A08Ch` (8 entradas): rutinas de pantalla/fase. Por sus textos: `A098h → A82Ch` dibuja el menú principal (`1 JUGADOR…`); `A08Fh → A1AAh` pantallas de falta/fin de juego (textos de `A362h`+).
- `AC44h` (3 entradas): menú de configuración (redefinir teclas, etc.).

## 4. Biblioteca residente (`D160h`)

La tabla `D160h` tiene 27 saltos. Identificadas (comprobadas leyendo el código):

| Dirección | Nombre | Función |
|---|---|---|
| `D358` | `LIB_INIT` | Busca RAM en página 1 (prueba de escritura con la cadena `DiNaMiC`), monta **IM 2** (tabla de 257 bytes `41h` en `4000h`, vector `4141h = JP D48B`), hook `FEE4h → D8DF`, pila en `F55Ch`. Si falla: **«Insuficiente Ram»** |
| `D3CC` / `D3FA` / `D453` | | slot actual de una página / búsqueda de RAM por slots / test de RAM |
| `D46F` | `LIB_SALIR_A_BASIC` | `IM 1`, restaura slot, `INITXT`. Se dispara con el código de tecla 5 |
| `D48B` | `ISR_IM2` | Interrupción de VBLANK: contadores (`4111h`, `4114h`) y lectura de teclado/joystick |
| `D4CA` | `CLS_SCREEN2` | Borra patrones, color y nombres |
| `D517` | `FILL_VRAM` | HL=dirección VRAM, BC=longitud, A=valor |
| `D53C` | `MEMSET0` | Pone a 0 BC bytes desde HL |
| `D545 / D54D / D555` | `SET_BORDER / SET_COLOR_BG / SET_COLOR_FG` | Registro 7 del VDP y atributo de color actual (`D1BC`) |
| `D564 / D56A` | `KEYSCAN` | `SNSMAT` filas 0–8 → `4104h…`; `GTSTCK/GTTRIG` joystick |
| `D5A9` | `KEY_DECODE` | Matriz → código de tecla (tabla en `(D1CE)`) en `4110h` |
| `D5DE` | `KEY_TEST` | A = fila×8+bit → Z si pulsada (13 usos) |
| `D606` | `RND` | Congruencial lineal sobre el contador de frames `4114h` |
| `D61B` | `RAND_RANGO` | Aleatorio entre `(D098)` y `(D09A)` |
| `D724 / D73B` | `MUL16 / DIV16` | HL×BC, HL÷BC (resto en DE) |
| `D75B / D769` | `MUL8 / DIV8` | 8 bits |
| `D7C7` | `ESPERA_TECLA` | Espera pulsar y soltar |
| `D7F9 / D7FC` | `PRINT_NUM8/16` | Imprime decimal (con signo `-`) |
| `D8B8` | `PRINT_STRING_INLINE` | Imprime la cadena que sigue al `CALL` hasta `00h` |

Variables de la biblioteca en página 1: `4104–410C` matriz de teclado, `410F/4110` tecla actual, `4111–4113` contador de ticks, `4114` contador de frames/semilla RND, `4102/4103` posición del cursor de texto (probable).

## 5. Textos encontrados (castellano)

`JUGADOR 1`, `MARTIN F.`, `DOBLES`, `PERSONAL`, `* FUERA *`, `CANASTA !`, `CAMPO ATRAS`, `EXPULSADO POR PERSONALES`, `FIN DE JUEGO`, `TIEMPO !!`, `CANASTAS`, `PERSONALES`, `TIROS LIBRES`, `REBOTES`, `TRIPLES`.
Menú: `1 JUGADOR`, `2 JUGADORES`, `3 NIVEL` (`NOVATO / AMATEUR / NBA`), `4 CAMBIAR NOMBRES`, `5 ELEGIR CONTROL` (`CAMPO IZQUIERDO / DERECHO`, redefinir `ARRIBA/ABAJO/IZQUIERDA/DERECHA/FUNCION/PAUSA`).

## 6. Zonas de datos (no ejecutables)

`B258–CC75` (~6,7 KB) y `CCE7–CF07`, `D9B6–DD18`, `D1B1–D240` y bloques menores a lo largo de `93xx–AExx`: gráficos, tablas y cadenas por su patrón de bytes (no se han decodificado una a una).

## 7. Límites de este trabajo (para ser honestos)

- El **flujo de código está completo** para lo alcanzable por saltos/llamadas desde las entradas conocidas (12.339 de 22.601 bytes). Código llamado solo mediante tablas de punteros o `JP (HL)` puede aparecer como `DB`.
- Los **comentarios manuales** cubren arranque, cargadores, biblioteca (ISR, teclado, VDP, matemáticas) y estructura del bucle principal. **La lógica interna del baloncesto** (físicas, IA, reglas) está desensamblada y etiquetada (`Lxxxx` / `Vxxxx`) pero **no comentada línea a línea**.
- Algunas funciones de `D160h` (`D163`, `D166`, `D1AE`, …) y varias de `9379h` están sin nombre; las etiquetas `MODO_xxxx` son provisionales.
- Hipótesis no verificada: el hook `FEE4h` actúa como salida de caracteres para `RST 18h`; y el bloque `0007h`/`E740h` parece no usarse (ver §2).
- Los nombres BIOS (`CHKRAM`, `ENASLT`, `SNSMAT`…) se asignan a cualquier constante `<4000h` que coincida; un `LD BC,CHKRAM` equivale a `LD BC,0000h`.

## 8. Comparación TSX vs CAS vs RAM de openMSX

| Fichero | Diferencias TSX ↔ CAS | Qué es |
|---|---|---|
| 3 (juego) | **1 byte**: `9327h` TSX=`C1`, CAS=`C3` | Error de un bit en el TSX: `JP A0ADh` pasa a `POP BC` y el flujo cae en basura → cuelgue |
| 2 | 51 bytes (`CED5–CF07`) | Datos de cola |
| 1 | ~490 bytes (`CEB1–CF07`, `CF3E–D106`, `D117–D15F`, `D9B8–DA17`) | Datos (zona tipo música/fuente) |

Contraste con la RAM de un snapshot del `.omr` en pleno juego: el fichero 3 coincide al 99,7 % con el CAS; `9327h = C3`; en la biblioteca la RAM coincide con el CAS (`D117–D15F` 73/73; `D9B8–DA17` 96/96) y **no** con el TSX (56/73 y 79/96). Conclusión: **el CAS es el dump correcto; el TSX es defectuoso**, lo que explica que falle en openMSX.

El snapshot también confirma el análisis: tabla IM 2 de 257 bytes `41h` en `4000h`, `4141h = JP D48B` (la ISR), hook `FEE4h = JP D8DF`, `D3CC–D3CE` parcheados por el stub del fichero 2, datos del fichero 2 en `415Ah`, y que `C298h–CD30h` se reescribe en ejecución (copia de `B498h`).

## 9. Sobre el `.omr`

Es un *replay* de openMSX 21.0 (gzip + XML): máquina **Sony HB-20P** (MSX1 español, 64 KB), cinta = tu `.cas` en estado `PLAY`, 9 snapshots y 572 pulsaciones de teclado registradas. Desde aquí no puedo ejecutarlo (no tengo openMSX ni acceso a tu `D:\`). Para verlo en tu equipo, en la consola de openMSX (`F10`): `reverse loadreplay "ruta\FernandoMartinEx.omr"`. Si la ruta de la cinta guardada en el replay no existe en tu PC, openMSX puede quejarse; en ese caso, arranca la HB-20P, `cassetteplayer insert tu.cas` y escribe `RUN"CAS:"`.
