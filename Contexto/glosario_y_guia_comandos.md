# Guía Rápida, Glosario y Quick Lookup de Comandos
## Asignatura: Arquitectura de Redes (Grado en Ingeniería Informática)

Documento de referencia rápida elaborado a partir de los boletines de prácticas (Boletines 1 a 4), el guion de la Práctica Final y la guía de estilo de la asignatura.

---

## Índice
1. [Glosario de Conceptos Teóricos y Prácticos](#1-glosario-de-conceptos-teóricos-y-prácticos)
   - [1.1 Arquitectura del Router y Simulación (Boletines 1 y 2)](#11-arquitectura-del-router-y-simulación-boletines-1-y-2)
   - [1.2 Direccionamiento IPv4 y VLSM (Boletín 3)](#12-direccionamiento-ipv4-y-vlsm-boletín-3)
   - [1.3 Protocolo RIPv2 y Vectores de Distancia (Boletín 4)](#13-protocolo-ripv2-y-vectores-de-distancia-boletín-4)
   - [1.4 Protocolo OSPFv2 y Estado de Enlace (Práctica Final)](#14-protocolo-ospfv2-y-estado-de-enlace-práctica-final)
   - [1.5 Redistribución de Rutas e Interconexión (Práctica Final)](#15-redistribución-de-rutas-e-interconexión-práctica-final)
2. [Estructura de Modos del Cisco IOS](#2-estructura-de-modos-del-cisco-ios)
3. [Quick Lookup de Comandos Cisco IOS](#3-quick-lookup-de-comandos-cisco-ios)
   - [3.1 Comandos Básicos y Gestión de Memoria](#31-comandos-básicos-y-gestión-de-memoria)
   - [3.2 Configuración de Interfaces](#32-configuración-de-interfaces)
   - [3.3 Rutas Estáticas y Ruta por Defecto](#33-rutas-estáticas-y-ruta-por-defecto)
   - [3.4 Protocolo RIPv2](#34-protocolo-ripv2)
   - [3.5 Protocolo OSPFv2 (Áreas, Tipos, DR/BDR, Costes y Agregación)](#35-protocolo-ospfv2-áreas-tipos-drbdr-costes-y-agregación)
   - [3.6 Redistribución entre RIP y OSPF](#36-redistribución-entre-rip-y-ospf)
   - [3.7 Comandos de Consulta y Diagnóstico (`show`)](#37-comandos-de-consulta-y-diagnóstico-show)
   - [3.8 Comandos de Depuración (`debug`)](#38-comandos-de-depuración-debug)
   - [3.9 Comandos en Hosts / PCs](#39-comandos-en-hosts--pcs)
4. [Recomendaciones para la Memoria y Entrevista](#4-recomendaciones-para-la-memoria-y-entrevista)

---

# 1. Glosario de Conceptos Teóricos y Prácticos

### 1.1 Arquitectura del Router y Simulación (Boletines 1 y 2)

* **Router**: Dispositivo de capa de red (Capa 3 OSI) encargado de interconectar diferentes redes lógicas y reenviar paquetes determinando el mejor camino (*routing*).
* **Componentes de Memoria**:
  * **RAM / DRAM**: Memoria volátil de trabajo. Almacena la tabla de encaminamiento (`routing table`), la caché ARP, búferes de paquetes, colas de salida y el fichero de configuración activo (**`running-config`**). Se borra al reiniciar o apagar el equipo.
  * **NVRAM (Non-Volatile RAM)**: Memoria no volátil de lectura/escritura rápida. Almacena el fichero de configuración de inicio (**`startup-config`**) que el router carga durante el arranque.
  * **Flash**: Memoria ROM reescribible no volátil. Contiene la imagen binaria del sistema operativo Cisco IOS (*Internetwork Operating System*).
  * **ROM**: Memoria de solo lectura integrada en la placa base. Contiene el código de diagnóstico inicial (**POST** - *Power-On Self-Test*) y el programa de carga inicial (**Bootstrap**).
* **Proceso de Arranque (Bootstrapping)**:
  1. Ejecución del POST desde la ROM.
  2. Carga del programa Bootstrap.
  3. Localización y descompresión de la imagen del IOS desde la Flash a la RAM.
  4. Carga y aplicación de la `startup-config` de la NVRAM a la RAM (`running-config`). Si no existe, inicia el asistente de configuración interactivo (*Setup mode*).
* **Interfaces y Nomenclatura**:
  * **LAN**: Interfaces basadas en Ethernet (`FastEthernet`, `GigabitEthernet`).
  * **WAN**: Interfaces serie para enlaces punto a punto (`Serial`), habitualmente en módulos WIC (*WAN Interface Cards*) o NM (*Network Modules*).
  * **Nomenclatura**: `Tipo-Enlace slot#/puerto#` (ej. `FastEthernet0/0`) o en modelos modulares `Tipo-Enlace slot#/subslot#/puerto#` (ej. `Serial0/0/0`).
  * **Puertos de Gestión (Out-of-band)**: 
    * `Console`: Conexión directa serie mediante cable *rollover* / USB para administración inicial fuera de banda.
    * `AUX`: Conexión auxiliar para acceso mediante módem (*dial-in*).
* **Packet Tracer - Modos de Operación**:
  * **Modo Tiempo Real (Real-time)**: Simulación continua donde los eventos ocurren con el reloj del sistema.
  * **Modo Simulación**: Permite congelar el tiempo y avanzar paquete a paquete (*Capture/Forward*), inspeccionando cabeceras PDU (*Protocol Data Unit*) en cada capa OSI y filtrando por tipo de protocolo (ICMP, RIP, OSPF, ARP, etc.).

---

### 1.2 Direccionamiento IPv4 y VLSM (Boletín 3)

* **Direccionamiento Classful**: Esquema tradicional rígido dividido en Clases A (`/8`), B (`/16`) y C (`/24`), que provoca un gran desperdicio de direcciones IP.
* **Classless / CIDR (Classless Inter-Domain Routing)**: Asignación de bloques contiguos con máscaras de longitud de prefijo arbitraria (`/n`), desacoplados del concepto de clases.
* **VLSM (Variable Length Subnet Masking)**: Técnica que permite aplicar diferentes máscaras de subred a subredes dentro de un mismo bloque de red, adaptando el tamaño de cada subred al número real de hosts requeridos.
* **Cálculo de Subredes con VLSM**:
  1. **Ordenación**: Se deben ordenar las necesidades de subred de **mayor a menor** número de hosts requeridos (incluyendo siempre las interfaces de routers correspondientes).
  2. **Cálculo de bits de Host ($|H|$)**:
     $$2^{|H|} - 2 \ge \text{Hosts requeridos} \implies |H| = \lceil \log_2(\text{Hosts} + 2) \rceil$$
  3. **Cálculo de la máscara**: $\text{Máscara} = / (32 - |H|)$.
  4. **Bloques Disjuntos**: Cada subred comienza en el siguiente múltiplo de su tamaño de bloque ($2^{|H|}$), garantizando que no existan solapamientos.
  5. **Direcciones reservadas por subred**:
     * **Dirección de Red**: Todos los bits de host a 0. Identifica la subred.
     * **Dirección de Broadcast**: Todos los bits de host a 1. Envío a todos los hosts de la subred.
     * **Rango Útil de Hosts**: Desde `(Dirección de Red + 1)` hasta `(Dirección de Broadcast - 1)`.
* **Enlaces Punto a Punto (P2P Serial)**: Requieren 2 hosts $\implies |H| = 2$ bits $\implies$ máscara `/30` (`255.255.255.252`, 4 IPs por bloque: 1 red, 2 útiles, 1 broadcast).

---

### 1.3 Protocolo RIPv2 y Vectores de Distancia (Boletín 4)

* **RIP (Routing Information Protocol)**: Protocolo de pasarela interior (IGP) basado en el algoritmo de vector de distancias (**Bellman-Ford**).
* **RIPv1 vs RIPv2**:
  * **RIPv1**: Classful, no envía máscaras de subred en las actualizaciones, difusión por broadcast (`255.255.255.255`).
  * **RIPv2**: Classless (soporta VLSM y CIDR), incluye máscaras de subred, envía actualizaciones por multicast (`224.0.0.9`) y soporta autenticación.
* **Métrica**: Número de saltos (*hop count*).
  * Métrica máxima utilizable: **15 saltos**.
  * **16 saltos = Inalcanzable** (*Infinity / Unreachable*).
* **Distancia Administrativa (AD)**: Valor de confiabilidad del origen de la ruta (a menor valor, más preferida):
  * Conectada directamente: `0`
  * Ruta estática: `1`
  * OSPF: `110`
  * RIP: `120`
* **Mecanismos para Evitar Bucles de Encaminamiento (Count-to-Infinity)**:
  * **Split Horizon (Horizonte Dividido)**: Prohíbe a un router anunciar una ruta por la misma interfaz por la que la aprendió.
  * **Poison Reverse (Envenenamiento de Ruta)**: Variante de Split Horizon donde la ruta sí se anuncia por la interfaz de entrada, pero con métrica infinita (`16 hops`), indicando explícitamente que es inalcanzable por ese camino.
  * **Triggered Updates (Actualizaciones Disparadas)**: Envío inmediato de mensajes de actualización tan pronto como se detecta un fallo o cambio topológico, sin esperar a que expire el temporizador periódico.
  * **Holddown Timer**: Temporizador que congela los cambios sobre una ruta caída durante un tiempo determinado para evitar que anuncios desactualizados reinserten rutas incorrectas.
* **Temporizadores de RIP (Timers)**:
  * **Update (30 s)**: Intervalo entre envíos periódicos de la tabla completa de rutas.
  * **Invalid (180 s)**: Tiempo sin recibir noticias de una ruta antes de marcarla como inválida (métrica 16).
  * **Holddown (180 s)**: Tiempo de espera en el que no se aceptan nuevas rutas con métrica igual o peor hacia un destino caído.
  * **Flush (240 s)**: Tiempo total tras el cual una ruta inválida se elimina definitivamente de la tabla de rutas.
* **Interfaces Pasivas (`passive-interface`)**: Evita el envío de actualizaciones RIP periódicas a través de interfaces conectadas a LANs de hosts finales (ahorrando ancho de banda y CPU, y mejorando la seguridad), mientras que la subred conectada se sigue anunciando al resto de routers vecinos.
* **Agregación Automática (`no auto-summary`)**: Por defecto RIPv2 resume a nivel de clase (*classful boundary*). Con `no auto-summary` se anuncian los prefijos con su máscara exacta de subred (imprescindible con VLSM).

---

### 1.4 Protocolo OSPFv2 y Estado de Enlace (Práctica Final)

* **OSPF (Open Shortest Path First)**: Protocolo de pasarela interior (IGP) de **estado de enlace** (*Link-State*) que utiliza el algoritmo de **Dijkstra** (árbol de caminos más cortos, *Shortest Path First - SPF*).
* **Características Clave**:
  * Convergencia rápida y libre de bucles.
  * Métrica basada en **Coste** acumulado:
    $$\text{Coste} = \frac{\text{Ancho de banda de referencia (por defecto } 10^8 \text{ bps)}}{\text{Ancho de banda de la interfaz (bps)}}$$
  * Anuncios mediante paquetes multicast: `224.0.0.5` (todos los routers OSPF) y `224.0.0.6` (todos los DR/BDR).
  * Distancia administrativa por defecto: **110**.
* **Router ID (RID)**: Identificador único de 32 bits de cada router en el dominio OSPF. Criterio de selección:
  1. Configuración explícita con el comando `router-id <IP>`.
  2. Si no se define, la dirección IP más alta configurada en una interfaz virtual *Loopback* activa.
  3. Si no hay loopbacks, la dirección IP más alta configurada en cualquier interfaz física activa.
* **Tipos de Redes OSPF**:
  * **Punto a punto (P2P)**: Enlaces directos entre dos routers (ej. serie). No se eligen DR ni BDR.
  * **Broadcast Multi-access**: Redes compartidas como Ethernet con múltiples routers. Se eligen DR y BDR para reducir las adyacencias de orden $O(N^2)$ a $O(N)$.
* **Elección de DR y BDR**:
  * **DR (Designated Router)**: Router centralizador que recopila y distribuye los LSA de la red multiacceso.
  * **BDR (Backup Designated Router)**: Router de respaldo que asume el rol de DR si este falla.
  * **DROther**: Resto de routers de la red que establecen adyacencia total (*FULL*) únicamente con el DR y el BDR, permaneciendo en estado *2-WAY* entre sí.
  * **Criterio de Elección**:
    1. **Prioridad OSPF (`ip ospf priority <0-255>`)**: La prioridad más alta gana (por defecto `1`). Si prioridad = `0`, el router nunca será elegido DR ni BDR.
    2. En caso de empate en prioridad: El router con el **Router ID más alto**.
* **Jerarquía de Áreas OSPF**:
  * **Área 0 / Backbone Area**: Área central a la que deben estar conectadas directa o virtualmente todas las demás áreas.
  * **Áreas Estándar**: Aceptan rutas intra-área, inter-área y externas.
  * **Stub Area (Área Troncal / Área de Extremo)**: 
    * **Bloquea LSAs de tipo 4 y tipo 5 (rutas externas al SA)**.
    * Los ABR inyectan automáticamente una **ruta por defecto de tipo 3 (Summary LSA, `0.0.0.0/0`)**.
    * Reduce considerablemente la memoria y la tabla de rutas de los routers internos del área.
  * **Totally Stub Area (Área Totalmente de Extremo - Propietaria de Cisco)**:
    * **Bloquea LSAs de tipo 3 (inter-área), tipo 4 y tipo 5 (externas)**.
    * Únicamente permite rutas intra-área y una **única ruta por defecto de tipo 3 (`0.0.0.0/0`)** inyectada por el ABR.
    * Configuración: Se añade el modificador `no-summary` en el ABR (`area <id> stub no-summary`).
* **Roles de Routers en OSPF**:
  * **Internal Router**: Todos sus interfaces pertenecen a la misma área.
  * **ABR (Area Border Router)**: Conecta una o más áreas al Área 0 Backbone. Mantiene bases de datos LSDB independientes por cada área a la que pertenece.
  * **ASBR (Autonomous System Border Router)**: Router frontera que conecta el dominio OSPF con otros Sistemas Autónomos o redistribuye rutas procedentes de otros protocolos (ej. RIP, BGP, estáticas).
* **Tipos de LSA (Link-State Advertisements)**:
  1. **Tipo 1 - Router LSA**: Generado por cada router para describir sus enlaces directos dentro de su propia área. No cruza los ABR (se queda en el área local).
  2. **Tipo 2 - Network LSA**: Generado por el DR en redes multiacceso para listar los routers conectados al segmento. No cruza el área.
  3. **Tipo 3 - Summary LSA (Network)**: Generado por los ABR para anunciar redes aprendidas en un área hacia otras áreas (rutas inter-área, identificadas con `O IA` en la tabla de rutas).
  4. **Tipo 4 - Summary ASBR LSA**: Generado por los ABR para anunciar la ubicación del router ASBR al resto de áreas.
  5. **Tipo 5 - AS External LSA**: Generado por el ASBR para describir rutas externas redistribuidas al dominio OSPF (identificadas como `O E1` o `O E2` en la tabla de rutas).
* **Sumarización de Rutas en ABR (`area range`)**:
  * Agrupa múltiples subredes de un área en un único prefijo agregado anunciado al Área 0, reduciendo drásticamente las tablas de rutas de los demás routers.

---

### 1.5 Redistribución de Rutas e Interconexión (Práctica Final)

* **Redistribución de Rutas**: Proceso mediante el cual un router fronterizo (ASBR) toma información de rutas aprendidas por un protocolo de encaminamiento (ej. OSPF) y las inyecta en otro protocolo (ej. RIP) y viceversa.
* **Métrica Semilla (Seed Metric / Default Metric)**:
  * Al pasar rutas de un protocolo a otro, las métricas no son comparables (saltos en RIP vs coste en OSPF).
  * Es imprescindible asignar una métrica válida al inyectar rutas en el nuevo protocolo:
    * En RIP: Si se redistribuye OSPF a RIP, se debe especificar una métrica en saltos (ej. `metric 1` o `metric 2`), ya que por defecto la métrica semilla es infinita.
    * En OSPF: Al redistribuir RIP a OSPF, se debe añadir el parámetro **`subnets`** para permitir la redistribución de subredes no classful (VLSM).

---

# 2. Estructura de Modos del Cisco IOS

```
Modo Usuario EXEC            (Prompt: Router>)
   │
   │  enable
   ▼
Modo Privilegiado EXEC       (Prompt: Router#)
   │
   │  configure terminal
   ▼
Modo Configuración Global    (Prompt: Router(config)#)
   │
   ├── interface <id>   ──►  Modo Config. Interfaz   (Prompt: Router(config-if)#)
   ├── router <proto>   ──►  Modo Config. Protocolo  (Prompt: Router(config-router)#)
   └── line <consola/vty> ─► Modo Config. Línea      (Prompt: Router(config-line)#)
```

### Comandos de Navegación y Control:
* `enable`: Pasa de Modo Usuario a Modo Privilegiado.
* `disable`: Desciende de Modo Privilegiado a Modo Usuario.
* `configure terminal` (o `conf t`): Entra a Configuración Global desde Modo Privilegiado.
* `exit`: Retrocede un nivel en la jerarquía de configuración.
* `end` o combinación `Ctrl + Z`: Sale de cualquier submodo directamente al Modo Privilegiado (`Router#`).
* `?`: Muestra los comandos disponibles o la ayuda de parámetros del comando actual.
* `<Tab>`: Autocompleta el comando en curso.
* `Ctrl + P` o `Flecha Arriba`: Comando anterior en el historial.
* `Ctrl + N` o `Flecha Abajo`: Comando siguiente en el historial.

---

# 3. Quick Lookup de Comandos Cisco IOS

### 3.1 Comandos Básicos y Gestión de Memoria

| Comando | Modo | Descripción |
|---|---|---|
| `hostname <NOMBRE>` | `(config)#` | Asigna un nombre al router/switch |
| `no ip domain-lookup` | `(config)#` | Desactiva búsquedas DNS ante errores tipográficos en consola |
| `show running-config` (o `sh run`) | `#` | Muestra la configuración activa en la memoria RAM |
| `show startup-config` (o `sh start`) | `#` | Muestra la configuración de inicio guardada en la NVRAM |
| `copy running-config startup-config` | `#` | Guarda los cambios de la RAM en la NVRAM |
| `write` (o `wr`) | `#` | Forma abreviada para guardar la configuración en la NVRAM |
| `erase startup-config` | `#` | Borra la configuración de inicio de la NVRAM |
| `reload` | `#` | Reinicia el router |
| `show history` | `#` | Muestra el historial de comandos recientes |
| `terminal history size <N>` | `#` | Modifica el tamaño del búfer del historial de comandos |

---

### 3.2 Configuración de Interfaces

| Comando | Modo | Descripción |
|---|---|---|
| `interface <TIPO_IF>` | `(config)#` | Entra a la configuración de la interfaz (ej. `interface FastEthernet0/0`, `interface Serial0/1/0`) |
| `ip address <IP> <MASCARA>` | `(config-if)#` | Asigna una dirección IP y máscara de red a la interfaz |
| `no shutdown` (o `no shut`) | `(config-if)#` | Activa/levanta administrativamente la interfaz |
| `shutdown` | `(config-if)#` | Desactiva administrativamente la interfaz (útil para pruebas de caída) |
| `clock rate <VALOR>` | `(config-if)#` | Establece la frecuencia de reloj en el extremo DCE de un cable serie (ej. `clock rate 64000`) |
| `description <TEXTO>` | `(config-if)#` | Añade una etiqueta descriptiva a la interfaz |
| `show ip interface brief` (o `sh ip int br`) | `#` | Resumen tabular de estado (`Status`/`Protocol`) e IP de todas las interfaces |
| `show interfaces [<TIPO_IF>]` | `#` | Muestra detalles completos de capa 1, capa 2, estadísticas y MTU |

---

### 3.3 Rutas Estáticas y Ruta por Defecto

| Comando | Modo | Descripción |
|---|---|---|
| `ip route <RED_DESTINO> <MASCARA> <IP_SIG_SALTO>` | `(config)#` | Crea una ruta estática hacia una red específica indicando el siguiente salto |
| `ip route <RED_DESTINO> <MASCARA> <IF_SALIDA>` | `(config)#` | Crea una ruta estática indicando la interfaz de salida |
| `ip route 0.0.0.0 0.0.0.0 <IP_GATEWAY>` | `(config)#` | Configura una ruta por defecto (*Default Gateway*) |
| `no ip routing` | `(config)#` | Deshabilita el reenvío IP para que el router actúe como un host terminal |

---

### 3.4 Protocolo RIPv2

| Comando | Modo | Descripción |
|---|---|---|
| `router rip` | `(config)#` | Habilita el proceso de enrutamiento RIP y entra al submodo |
| `version 2` | `(config-router)#` | Habilita la versión 2 de RIP (soporte de máscaras/VLSM y multicast) |
| `network <DIRECCION_RED_CLASSFUL>` | `(config-router)#` | Declara las redes locales que participan en RIP (ej. `network 172.81.0.0`) |
| `no auto-summary` | `(config-router)#` | Desactiva la sumarización automática en los límites de red con clase |
| `passive-interface <IFNAME>` | `(config-router)#` | Suprime el envío de mensajes RIP por la interfaz indicada (ej. `passive-interface FastEthernet0/0`) |
| `default-information originate` | `(config-router)#` | Propaga una ruta por defecto en las actualizaciones RIP hacia los vecinos |
| `timers basic <update> <invalid> <holddown> <flush>` | `(config-router)#` | Modifica los temporizadores de RIP en segundos (por defecto: `30 180 180 240`) |
| `show ip rip database` | `#` | Muestra la base de datos de rutas y métricas de RIP |
| `show ip protocols` | `#` | Muestra protocolos activos, temporizadores, redes anunciadas e interfaces pasivas |

---

### 3.5 Protocolo OSPFv2 (Áreas, Tipos, DR/BDR, Costes y Agregación)

| Comando | Modo | Descripción |
|---|---|---|
| `router ospf <PROCESS_ID>` | `(config)#` | Habilita OSPF con un identificador de proceso local (ej. `router ospf 1`) |
| `router-id <IP_ID>` | `(config-router)#` | Asigna manualmente el Router ID de OSPF (ej. `router-id 1.1.1.1`) |
| `network <IP_SUBRED> <WILDCARD> area <AREA_ID>` | `(config-router)#` | Asocia una subred a un área OSPF (ej. `network 173.81.16.0 0.0.0.31 area 0`) |
| `passive-interface <IFNAME>` | `(config-router)#` | Marca una interfaz como pasiva (no envía ni recibe paquetes Hello) |
| `area <AREA_ID> stub` | `(config-router)#` | Configura el área como **Stub Area** (se debe ejecutar en **todos** los routers del área) |
| `area <AREA_ID> stub no-summary` | `(config-router)#` | Configura el área como **Totally Stub Area** (se ejecuta **únicamente en el ABR**) |
| `area <AREA_ID> range <IP_RED> <MASCARA>` | `(config-router)#` | Realiza la **agregación/sumarización de rutas** de un área en el ABR (ej. `area 1 range 173.81.16.0 255.255.255.192`) |
| `ip ospf priority <0-255>` | `(config-if)#` | Configura la prioridad en la interfaz para la elección de DR/BDR (`0` = no elegible, `255` = máxima prioridad) |
| `ip ospf cost <VALOR>` | `(config-if)#` | Modifica manualmente el coste OSPF de la interfaz (útil para forzar caminos óptimos) |
| `auto-cost reference-bandwidth <MBPS>` | `(config-router)#` | Cambia el ancho de banda de referencia para el cálculo de costes |
| `show ip ospf` | `#` | Muestra información general del proceso OSPF, áreas y Router ID |
| `show ip ospf neighbor` | `#` | Lista los vecinos OSPF, estado de adyacencia (`FULL`, `2WAY`) y rol (`DR`, `BDR`, `DROTHER`) |
| `show ip ospf interface [<IFNAME>]` | `#` | Muestra temporizadores Hello/Dead, coste, tipo de red y estado del router (DR/BDR/DROTHER) |
| `show ip ospf database` | `#` | Muestra el resumen de la base de datos LSDB (Router LSAs, Network LSAs, Summary LSAs, etc.) |
| `clear ip ospf process` | `#` | Reinicia el proceso OSPF (fuerza la reelección de DR/BDR y refresca la LSDB) |

---

### 3.6 Redistribución entre RIP y OSPF

Configuración realizada en el router frontera ASBR (RB1 en la práctica final):

#### Redistribuir OSPF dentro de RIP:
```ios
RB1(config)# router rip
RB1(config-router)# version 2
RB1(config-router)# redistribute ospf 1 metric 2
```
*(Nota: En RIP es obligatorio asignar una métrica en saltos; sin ella, las rutas OSPF se redistribuyen con métrica infinita y son descartadas).*

#### Redistribuir RIP dentro de OSPF:
```ios
RB1(config)# router ospf 1
RB1(config-router)# redistribute rip subnets
```
*(Nota: La palabra clave `subnets` es imprescindible para que OSPF redistribuya las subredes con VLSM y no solo las redes con clase).*

---

### 3.7 Comandos de Consulta y Diagnóstico (`show`)

| Comando | Modo | Finalidad |
|---|---|---|
| `show ip route` | `#` | Muestra la tabla de encaminamiento completa |
| `show ip route rip` | `#` | Filtra la tabla mostrando únicamente las rutas aprendidas por RIP (`R`) |
| `show ip route ospf` | `#` | Filtra mostrando únicamente las rutas OSPF (`O`, `O IA`, `O E1`, `O E2`) |
| `show ip route connected` | `#` | Muestra las redes directamente conectadas (`C`) |
| `show ip route static` | `#` | Muestra las rutas estáticas (`S` o `S*`) |
| `show ip protocols` | `#` | Revisa parámetros de los protocolos de enrutamiento activos, timers y filtros |
| `show arp` | `#` | Muestra la tabla de correspondencias IP-MAC |
| `ping <IP>` | `#` o `>` | Comprueba conectividad ICMP extremo a extremo |
| `traceroute <IP>` | `#` o `>` | Muestra salto a salto el camino recorrido por los paquetes |

#### Leyenda de Códigos Comunes en `show ip route`:
* **`C`**: Conectada directamente (*Connected*).
* **`S`**: Ruta estática (*Static*).
* **`S*`**: Ruta estática candidata por defecto (*Candidate Default*).
* **`R`**: Ruta aprendida por RIPv2 (Distancia administrativa `120`).
* **`O`**: Ruta OSPF intra-área (Distancia administrativa `110`).
* **`O IA`**: Ruta OSPF inter-área (LSA Tipo 3).
* **`O*IA`**: Ruta por defecto OSPF inyectada por el ABR en áreas Stub / Totally Stub.
* **`O E1` / `O E2`**: Rutas OSPF externas al Sistema Autónomo (LSA Tipo 5 procedentes de redistribución).
* **`[AD/Métrica]`**: Ejemplo `[120/2]` indica Distancia Administrativa 120 y Métrica 2.

---

### 3.8 Comandos de Depuración (`debug`)

> [!WARNING]
> La salida de depuración consume recursos de CPU en tiempo real. Al finalizar la captura o comprobación, desactiva siempre los procesos de depuración con `no debug ...` o `undebug all`.

| Comando | Modo | Finalidad |
|---|---|---|
| `debug ip rip` | `#` | Muestra en tiempo real los mensajes RIP enviados y recibidos, vectores de distancias y métricas |
| `no debug ip rip` | `#` | Desactiva la depuración de RIP |
| `debug ip routing` | `#` | Monitoriza en tiempo real las altas, modificaciones y bajas de rutas en la tabla de encaminamiento |
| `no debug ip routing` | `#` | Desactiva la depuración de la tabla de rutas |
| `debug ip ospf events` | `#` | Muestra eventos generales de OSPF (adyacencias, transiciones de estado) |
| `debug ip ospf packet` | `#` | Muestra paquetes OSPF recibidos/enviados |
| `undebug all` (o `un all`) | `#` | Desactiva todas las depuraciones activas simultáneamente |

---

### 3.9 Comandos en Hosts / PCs (Command Prompt de Packet Tracer)

| Comando | Descripción |
|---|---|
| `ipconfig` | Muestra la dirección IP, máscara de subred y Gateway configurados en el PC |
| `ipconfig /all` | Muestra detalles completos incluyendo dirección física MAC |
| `ping <IP>` | Envía paquetes ICMP Echo Request para verificar conectividad con otro host o router |
| `tracert <IP>` | Traza la ruta completa salto a salto desde el host emisor hasta el destino |
| `arp -a` | Muestra la tabla de correspondencia ARP del host |

---

# 4. Recomendaciones para la Memoria y Entrevista

De acuerdo con el guion de la Práctica Final y la **Guía de estilo para elaborar el documento de prácticas**:

1. **Estructura y Portada**:
   - Portada obligatoria con: Nombre de la asignatura, título del trabajo, nombre completo, DNI, correo electrónico de cada miembro y grupo/subgrupo de prácticas.
   - Sin encabezados ni numeración en la portada. Numeración correlativa en el resto del documento.
   - Índice de contenidos (recomendado también índice de tablas y figuras).
2. **Justificación Técnica**:
   - No limitarse a pegar capturas: **explicar y razonar cada decisión** (diseño VLSM, cálculo de máscaras, elección de interfaces pasivas, selección de DR/BDR, funcionamiento de split horizon y poison reverse, convergencia ante fallos, motivos para áreas stub vs totally stub).
   - Incluir bloques de configuración relevantes con sintaxis limpia y comentarios.
3. **Figuras y Tablas**:
   - Todas las figuras y tablas deben llevar título numerado (ej. *Figura 1. Topología de la Organización A*, *Tabla 3. Plan de direccionamiento VLSM*).
   - Mantener tamaños legibles y cabeceras repetidas si una tabla ocupa varias páginas.
4. **Preparación para la Entrevista Individual**:
   - La entrevista se realiza frente a la terminal de comandos de Packet Tracer.
   - Es imprescindible dominar los comandos `show` (`show ip route`, `show ip interface brief`, `show ip ospf neighbor`, `show ip protocols`, `show ip ospf database`) para demostrar el funcionamiento del diseño sin mirar documentación externa.
