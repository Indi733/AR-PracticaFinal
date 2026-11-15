# Organización B (OSPF): cuestiones del apartado 4.2

Borrador de la memoria. Cada cuestión es un apartado numerado con texto seguido. Las salidas de Packet Tracer no van dentro del texto: se citan como *(Figura: `nombre`)*, que es el fichero `memoria/salidas/orgB/nombre.txt`. Al pasarlo a LaTeX, cada cita se cambia por `\salidacisco{...}` y `\ref{...}`. Las salidas que no van en la memoria están en `memoria/salidas/orgB/extra/`.

Revisión de la redacción:
- Revisadas a mano: 4.2.1, 4.2.2 y 4.2.3.
- Por revisar: 4.2.4 a 4.2.9.

Pendiente:
- Cuestión 9: confirmar si en el área 3 se esperaba un único resumen /25 (ahora está agregado solo lo exacto, según los apuntes).

---

## 4.2.1. Traceroute de RB4 a HB2

> *Realice un traceroute entre R B4 y el H B2. Justifica el camino que siguen los paquetes.*

Como podemos ver en la *(Figura: `c1_rb4_traceroute_hb2`)*, los paquetes que salen de RB4 hacia HB2 (173.81.16.2) pasan primero por RB3 (173.81.16.65), luego por RB2 (173.81.17.9) y finalmente llegan a HB2, así que el camino es RB4 → RB3 → RB2 → HB2.

Esto tiene sentido por cómo funcionan las áreas en OSPF. RB4 solo está en el área 2 y HB2 está en la LAN B2, que es del área 1, y para ir de un área a otra hay que pasar siempre por el área 0. RB3 es el ABR que une el área 2 con la 0 y RB2 el que une la 0 con la 1, así que el tráfico tiene que pasar por los dos.

Entre RB3 y RB2 hay dos caminos posibles: el enlace directo o dar la vuelta por RB1. Todos los enlaces del área 0 son serie e iguales, así que el directo, que es un solo enlace, es más barato que pasar por RB1, que son dos. Como OSPF elige siempre el camino de menor coste, va por el directo.

---

## 4.2.2. Caída del enlace entre RB3 y RB2

> *Deshabilite ahora la interfaz del router R B3 que conecta con el R B2. Espere a que la red converja de nuevo. A continuación, realiza el traceroute de nuevo entre R B4 y H B2 y justifica el camino que ahora siguen los paquetes. Cuando termine este ejercicio, vuelva a activar la interfaz desactivada.*

La interfaz de RB3 que conecta con RB2 es la Serial3/0 (173.81.17.10), la desactivamos con `shutdown` *(Figura: `c2_rb3_shutdown_s30`)* y en los mensajes vemos que RB3 pierde a RB2 como vecino (mensaje `FULL to DOWN`). De hecho, en los vecinos OSPF de RB3 *(Figura: `c2_rb3_vecinos`)* ya solo aparecen 4 y RB2 no está.

Una vez converge la red y repetimos el traceroute *(Figura: `c2_rb4_traceroute_hb2`)*, ahora salen cuatro saltos: RB3 (173.81.16.65), RB1 (173.81.17.5), RB2 (173.81.17.2) y HB2. Así que el camino es RB4 → RB3 → RB1 → RB2 → HB2. El tráfico sigue pasando por el área 0 para ir de RB3 a RB2, pero como ya no hay enlace directo, la única opción que queda es dar la vuelta por RB1.

Con esto vemos que OSPF se recupera solo cuando cae un enlace y encuentra otro camino sin que tengamos que tocar nada. Al reactivar la interfaz con `no shutdown` *(Figura: `c2_rb3_no_shutdown_s30_bis`)* vemos que la adyacencia con RB2 vuelve a `FULL` y que RB2 vuelve a aparecer entre los vecinos de RB3, así que el camino vuelve a ser el directo.

---

## 4.2.3. RB4 como DR y RB3 como BDR en la LAN B3

> *Realice la configuración necesaria para que R B4 y R B3 se conviertan en Designated Router (DR) y Backup Designated Router (BDR), respectivamente, de la LAN B3. Muestre que efectivamente se ha realizado el cambio.*

En la LAN B3, OSPF elige un DR y un BDR. Para elegirlos se mira la prioridad de la interfaz (por defecto 1), y si hay empate gana el router ID más alto. Al principio los dos routers tenían prioridad 1, así que ganaba RB3, que tiene un router ID mayor (173.81.17.10) que RB4 (173.81.16.97). Lo vemos en la *(Figura: `c3_rb3_interfaz_antes`)*, donde RB3 aparece como `State DR, Priority 1`.

Para cambiarlo, con `ip ospf priority` hemos puesto prioridad 100 a la interfaz de RB4 en la LAN B3 y prioridad 50 a la de RB3 *(Figura: `c3_prioridades`)*. Así RB4, con más prioridad, será el DR, y RB3 será el BDR.

Pero si en la red ya hay un DR, se mantiene aunque cambiemos las prioridades. Así que para forzar una nueva elección reiniciamos la interfaz Fa0/0 de RB3 con `shutdown` y `no shutdown` *(Figura: `c3_rb3_reinicio_fa00`)*. Al caer RB3, RB4, que era el BDR, pasa a ser el DR, y cuando RB3 vuelve se queda como BDR.

Si volvemos a mirar la interfaz de RB3 *(Figura: `c3_rb3_interfaz_despues`)*, ahora aparece como `State BDR, Priority 50` y el DR es RB4 (173.81.16.97).

---

## 4.2.4. Tabla de rutas de RB6

> *Muestre las tablas de rutas de R B6 y comente los aspectos más relevantes.*

RB6 es un router interno del área 3, es decir, todas sus interfaces están en esa área. Como podemos ver en su tabla de rutas *(Figura: `c4_rb6_tabla_rutas`)*, conoce las 11 subredes de la organización B, y las rutas se pueden dividir en tres grupos.

Primero, las tres redes en las que tiene una interfaz, que aparecen como conectadas (`C`): la LAN B6 (173.81.16.160/27), el enlace con RB3 (173.81.16.196/30) y el enlace con RB5 (173.81.16.200/30).

Segundo, las otras redes del área 3, que aparecen como `O`. Para entender sus costes, si miramos el coste de las interfaces con `show ip ospf interface`, vemos que un enlace serie tiene coste 64 *(Figura: `c4_rb1_interfaz_s20`)* y una interfaz FastEthernet coste 1 (como ya salía en la *(Figura: `c3_rb3_interfaz_antes`)*), y el coste de una ruta es la suma de los enlaces por los que pasa. Así, la LAN B5 (173.81.16.128/27) tiene coste 65, por RB5: 64 del enlace serie más 1 de la LAN. Y el enlace entre RB3 y RB5 (173.81.16.192/30) aparece con dos caminos a la vez, uno por RB3 y otro por RB5, porque los dos cuestan lo mismo (64 + 64 = 128), así que OSPF usa los dos y reparte el tráfico entre ellos.

Tercero, las redes de las otras áreas, que aparecen como `O IA` y salen todas por RB3 (173.81.16.197). Esto es así porque RB3 es el único ABR del área 3, así que cualquier tráfico que salga del área tiene que pasar por él. Por ejemplo, la LAN B3 le cuesta 65 (64 hasta RB3 + 1) y el enlace entre RB1 y RB2, que es lo más lejano, le cuesta 192 (64 + 64 + 64).

Por último, RB6 no tiene ruta por defecto (`Gateway of last resort is not set`), porque de momento conoce todas las redes de la organización.

---

## 4.2.5. Área 3 como stub area

> *Realice la configuración necesaria para que el área 3 sea una stub area. Analizando las tablas de rutas que considere relevantes, ¿qué diferencias observa con respecto a la configuración anterior? ¿Por qué?*

Para que el área 3 sea stub hay que poner `area 3 stub` en todos los routers del área, que son RB3, RB5 y RB6 *(Figuras: `c5_rb3_area3_stub`, `c5_rb5_area3_stub` y `c5_rb6_area3_stub`)*. Al aplicarlo vemos que las adyacencias se caen (`Adjacency forced to reset`) y no vuelven hasta que los tres routers lo tienen configurado, porque todos los routers del área tienen que estar de acuerdo en que es stub.

En un área stub el ABR filtra los LSA de tipo 4 y 5, es decir, lo relacionado con rutas externas al sistema autónomo, y a cambio mete una ruta por defecto hacia él. Si comparamos la tabla de RB6 de ahora *(Figura: `c5_rb6_tabla_rutas`)* con la de la cuestión anterior, vemos que aparece una ruta nueva, `O*IA 0.0.0.0/0` por RB3, que es esa ruta por defecto, con coste 65. Por eso también `Gateway of last resort` pasa de `not set` a 173.81.16.197.

El resto de la tabla es igual, con las mismas 11 subredes. Esto es normal porque una stub solo filtra los LSA de tipo 4 y 5 y deja pasar las rutas entre áreas (tipo 3), y como todavía no hemos hecho la redistribución, en la organización B no hay ninguna ruta externa que filtrar. Así que el área ya es stub, pero su efecto principal se verá cuando hagamos la redistribución en la sección 5.

---

## 4.2.6. Tabla de rutas de RB4 y camino óptimo a RB5

> *Muestre las tablas de rutas de R B4 y comente los aspectos más relevantes. ¿Cuál es el camino óptimo para alcanzar R B5?*

RB4 es un router interno del área 2. En su tabla de rutas *(Figura: `c6_rb4_tabla_rutas`)* vemos que también conoce las 11 subredes de la organización. Solo tiene dos redes conectadas (`C`), la LAN B3 y la LAN B4, que son las únicas redes del área 2, así que no hay ninguna ruta `O` intra-área. Todas las demás son `O IA` y salen por RB3 (173.81.16.65), que es el único ABR del área 2. Tampoco tiene ruta por defecto, porque aunque el área 3 es stub, eso solo afecta a los routers del área 3.

Los costes cuadran con la topología: las redes que están a un enlace serie de RB3 cuestan 65 (1 de la LAN B3 + 64), las LAN que hay detrás cuestan 66, y las que necesitan dos enlaces serie cuestan 129, como el enlace entre RB5 y RB6 o el de RB1 y RB2.

Para ver el camino óptimo hasta RB5 hemos hecho un traceroute a su IP de la LAN B5, 173.81.16.129 *(Figura: `c6_rb4_traceroute_rb5`)*. Salen dos saltos: RB3 (173.81.16.65) y RB5, que responde con la IP de su interfaz del enlace con RB3 (173.81.16.194). Así que el camino óptimo es RB4 → RB3 → RB5, usando el enlace directo entre RB3 y RB5, con coste 1 + 64 + 1 = 66 (es la ruta de la LAN B5 en la tabla). Dar la vuelta por RB6 costaría 1 + 64 + 64 + 1 = 130.

---

## 4.2.7. Área 2 como totally stub area

> *Realice la configuración necesaria para que el área 2 sea una totally stub area. Analizando las tablas de rutas que considere relevantes, demuestre que se trata de una totally stub área. ¿Qué diferencias observa con respecto a la configuración anterior? ¿Por qué?*

Para que el área 2 sea totally stub, en el ABR (RB3) hay que poner `area 2 stub no-summary` *(Figura: `c7_rb3_area2_nosummary`)*, y en el router interno (RB4) basta con `area 2 stub` *(Figura: `c7_rb4_area2_stub`)*. Igual que en la cuestión 5, la adyacencia entre RB3 y RB4 se reinicia hasta que los dos coinciden.

En una área totally stub el ABR filtra los LSA de tipo 3, 4 y 5, así que además de las rutas externas tampoco entran los resúmenes de las otras áreas, y solo se inyecta un LSA de tipo 3 con la ruta por defecto. Si comparamos la tabla de RB4 de ahora *(Figura: `c7_rb4_tabla_rutas`)* con la de la cuestión anterior, la diferencia es enorme: antes tenía 11 subredes y ahora solo tiene sus 2 redes conectadas y una ruta por defecto, `O*IA 0.0.0.0/0` por RB3, con coste 2. Han desaparecido todas las rutas `O IA`.

Esto es lo que demuestra que es totally stub y no una stub normal, porque en una stub, como el área 3, seguirían apareciendo todas las `O IA` además de la ruta por defecto. Y la conectividad no se pierde: RB4 ya no conoce las redes de fuera, pero manda todo a RB3 por la ruta por defecto y RB3, que sí conoce toda la red, lo lleva hasta el destino. Tiene sentido hacerlo en el área 2 porque solo tiene una salida, RB3, así que no hace falta que RB4 conozca todas las rutas si de todas formas las va a mandar a RB3.

---

## 4.2.8. Camino entre RB4 y HB5 pasando por RB6

> *Realice la configuración necesaria (sin desactivar las interfaces) para que el camino óptimo bidireccional entre R B4 y H B5 pase a través de R B6. Muestre que efectivamente se ha realizado el cambio.*

Como vimos en la cuestión 6, el camino de RB4 hacia la LAN B5 usa el enlace directo entre RB3 y RB5. Y lo mismo pasa en la vuelta: el tracert desde HB5 hasta RB4 (173.81.16.66) pasa por RB5 y RB3, sin pasar por RB6 *(Figura: `c8_hb5_tracert_rb4_antes`)*.

OSPF siempre elige el camino de menor coste, así que la idea es encarecer el enlace directo con `ip ospf cost`. El camino alternativo por RB6 cuesta 64 + 64 = 128, así que basta con que el enlace directo cueste más de 128; nosotros le pusimos 200. El coste es de cada interfaz de salida, así que hay que cambiarlo en los dos extremos del enlace para que el cambio sea bidireccional: en la Serial7/0 de RB3, que es por donde sale la ida *(Figura: `c8_rb3_coste_s70`)*, y en la Serial2/0 de RB5, que es por donde sale la vuelta *(Figura: `c8_rb5_coste_s20`)*.

Después del cambio, el traceroute de RB4 a HB5 pasa por RB3, RB6 (173.81.16.198), RB5 y HB5 *(Figura: `c8_rb4_traceroute_hb5_despues`)*, y el tracert de HB5 a RB4 pasa por RB5, RB6 (173.81.16.201), RB3 y RB4 *(Figura: `c8_hb5_tracert_rb4_despues`)*. Así que el camino pasa por RB6 en los dos sentidos, sin haber desactivado ninguna interfaz. Ahora el camino por RB6 cuesta 129 (64 + 64 + 1), menos que los 201 que costaría el enlace directo (200 + 1).

---

## 4.2.9. Agregación de rutas en los ABR

> *Configura ahora los routers ABR de cada área para que realicen la agregación de las subredes que se encuentran en su área. Comprueba que se ha realizado esta agregación de redes mostrando la tabla de rutas del R B2 antes y después de aplicar dicha agregación.*

Cuando un ABR anuncia las redes de su área hacia el área 0, manda un LSA de tipo 3 por cada red. Si las redes del área son contiguas, puede mandar uno solo que las englobe a todas, y así el resto de routers necesita menos entradas en su tabla de rutas. Por eso, al diseñar el direccionamiento de la organización B, a cada área le dimos un rango de direcciones contiguo. Antes de agregar, RB2 recibe de RB3 todas las redes de las áreas 2 y 3 sueltas: 7 rutas `O IA` y 11 subredes en total *(Figura: `c9_rb2_tabla_rutas_antes`)*.

Para cada área buscamos la máscara que englobe todas sus redes sin incluir redes que no son del área, como vimos en teoría con el supernetting:

| Área | Redes | Agregado |
|---|---|---|
| 1 | LAN B2 (173.81.16.0/26) | No hace falta, solo tiene una red |
| 2 | LAN B3 (.64/27) y LAN B4 (.96/27) | 173.81.16.64/26 |
| 3 | LAN B5 (.128/27) y LAN B6 (.160/27) | 173.81.16.128/26 |
| 3 | Enlaces .192/30 y .196/30 | 173.81.16.192/29 |
| 3 | Enlace .200/30 | Se queda suelto |

En el área 3 no podemos usar un único /25, porque iría de la .128 a la .255 e incluiría las direcciones de la .204 a la .255, que no son de ninguna red. Así que agregamos solo lo que encaja justo, y el enlace .200 se queda suelto, porque juntarlo con los otros dos metería las direcciones de la .204 a la .207.

La agregación se hace en el ABR de cada área con `area AREA-ID range DIRECCIÓN MÁSCARA`. El ABR de las áreas 2 y 3 es RB3, así que ahí configuramos los tres rangos *(Figura: `c9_rb3_area_range`)*. El ABR del área 1 es RB2, pero como esa área solo tiene la LAN B2, no hay nada que agregar.

Después de agregar, en la tabla de RB2 *(Figura: `c9_rb2_tabla_rutas_despues`)* vemos que las dos LAN del área 2 se han convertido en una sola ruta, 173.81.16.64/26; las dos LAN del área 3, en 173.81.16.128/26; y los enlaces .192 y .196, en 173.81.16.192/29. El enlace .200 sigue igual. Así que la tabla pasa de 11 a 8 subredes, y las rutas hacia las áreas 2 y 3 pasan de 7 a 4. Todas siguen saliendo por RB3, así que el camino no cambia, solo que RB2 necesita menos entradas.

---

## Chuleta de direcciones (no va en la memoria)

| Red | Área | Dirección | Interfaces |
|---|---|---|---|
| P2P B1-2 | 0 | 173.81.17.0/30 | RB1 S2/0 .1 · RB2 S2/0 .2 |
| P2P B1-3 | 0 | 173.81.17.4/30 | RB1 S3/0 .5 · RB3 S2/0 .6 |
| P2P B2-3 | 0 | 173.81.17.8/30 | RB2 S3/0 .9 · RB3 S3/0 .10 |
| LAN B2 | 1 | 173.81.16.0/26 | RB2 Fa0/0 .1 · HB2 .2 |
| LAN B3 | 2 | 173.81.16.64/27 | RB3 Fa0/0 .65 · RB4 Fa0/0 .66 |
| LAN B4 | 2 | 173.81.16.96/27 | RB4 Fa1/0 .97 · HB4 .98 |
| LAN B5 | 3 | 173.81.16.128/27 | RB5 Fa0/0 .129 · HB5 .130 |
| LAN B6 | 3 | 173.81.16.160/27 | RB6 Fa0/0 .161 · HB6 .162 |
| P2P B3-5 | 3 | 173.81.16.192/30 | RB3 S7/0 .193 · RB5 S2/0 .194 |
| P2P B3-6 | 3 | 173.81.16.196/30 | RB3 S6/0 .197 · RB6 S2/0 .198 |
| P2P B5-6 | 3 | 173.81.16.200/30 | RB6 S3/0 .201 · RB5 S3/0 .202 |

Router ID: RB1 = 173.81.17.5, RB2 = 173.81.17.9, RB3 = 173.81.17.10, RB4 = 173.81.16.97, RB5 = 173.81.16.202, RB6 = 173.81.16.201.
