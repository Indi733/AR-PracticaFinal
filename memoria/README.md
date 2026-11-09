# Salidas de Packet Tracer para la memoria

Aquí van todas las salidas de la consola de Packet Tracer (tablas de rutas, traceroute, `show ip ospf`, etc.) que salen como figuras en la memoria en LaTeX. Así salen **exactamente igual que en la consola**: misma fuente (Courier), mismos espacios y columnas alineadas.

La idea es que **cada salida va en su propio `.txt`** y LaTeX la lee del fichero. Así no hay que copiar nada a mano dentro del `.tex`, que es donde se rompe la alineación.

## Estructura

```
memoria/
  salidas_cisco.tex      formato de las figuras (se incluye en el preámbulo)
  nueva_salida.py        guarda una salida desde el portapapeles
  generar_prueba.py      genera un PDF con todas las salidas para revisarlas
  salidas/
    orgA/                cuestiones de la organización A (RIP)
    orgB/                cuestiones de la organización B (OSPF)
    interconexion/       cuestiones de la sección 5
```

## Añadir una salida (3 pasos)

1. En Packet Tracer, selecciona la salida en la consola del router y **cópiala (Ctrl+C)**. Mejor si coges también la línea del comando (`RA4#show ip route`).
2. Desde la raíz del repo:
   ```bash
   python memoria/nueva_salida.py orgA c1_ra4_tabla_rutas
   ```
   Guarda el portapapeles tal cual en `memoria/salidas/orgA/c1_ra4_tabla_rutas.txt`. Solo quita las líneas vacías o de prompt suelto (`RA4#`) que sobran al principio y al final.
3. Te imprime la línea para pegar en la memoria:
   ```latex
   \salidacisco{salidas/orgA/c1_ra4_tabla_rutas.txt}{PIE DE FIGURA}{fig:orgA-c1-ra4-tabla-rutas}
   ```

Si el portapapeles no funciona, usa `--stdin` y pega el texto en la terminal (al terminar, Ctrl+Z y Enter). Si quieres rehacer una salida que ya existe, añade `--forzar`.

**Nombres:** `cN_<router>_<qué es>`, en minúsculas y con guiones bajos. Por ejemplo `c1_ra4_tabla_rutas`, `c3_ha5_tracert_ra2` o `c2_rb3_vecinos`. Con el número de cuestión delante, se ordenan solas.

## Usarlo en la memoria

En el preámbulo del documento principal:
```latex
\input{salidas_cisco}
```
Y donde vaya cada figura:
```latex
\salidacisco{salidas/orgB/c1_rb4_traceroute_hb2.txt}{Traceroute de RB4 a HB2}{fig:c1-traceroute}

Como podemos ver en la Figura~\ref{fig:c1-traceroute}, los paquetes pasan por RB3 y RB2...
```

Las rutas son relativas a la carpeta `memoria/`. Si el `.tex` principal está en otra carpeta, ajusta la ruta o mueve allí `salidas/` y `salidas_cisco.tex`.

## Revisar cómo quedan

```bash
python memoria/generar_prueba.py --pdf
```
Genera `memoria/prueba_salidas.pdf` con todas las salidas de las tres carpetas. Si una salida tiene líneas de más de 82 caracteres (sin contar los mensajes de log), el pie lo avisa.

## Cosas a tener en cuenta

- **No edites los `.txt` a mano**, salvo para quitar algo que no quieras enseñar. Lo que interesa es que sean la salida real.
- **No acortes con `...`**: la salida va completa.
- La consola tiene 80 columnas, y con `\footnotesize` y márgenes de 2,5 cm caben enteras. Si la plantilla final tiene márgenes más grandes y alguna tabla se parte, usa `\salidacisco[\scriptsize]{...}{...}{...}` para esa figura.
- Los mensajes largos de log (`%OSPF-5-ADJCHG ...`) se parten en varias líneas, igual que hace la consola.
