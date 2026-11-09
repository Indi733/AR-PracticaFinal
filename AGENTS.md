# Instrucciones para asistentes de IA

Repositorio de la práctica final de Arquitectura de Redes (Packet Tracer). El enunciado está en `AR_PR07_practica-final.pdf` y su texto en `pdf_text.txt`. El contexto general está en `README.md`.

## Leer el escenario `.pkt` sin abrir Packet Tracer

`practica_final.pkt` está cifrado (formato de Packet Tracer 9). **No hace falta descifrarlo de nuevo**: usa `DescifradoPKT/pkt.py` (Python 3, sin dependencias).

```bash
python DescifradoPKT/pkt.py resumen practica_final.pkt               # routers, interfaces, IPs, OSPF/RIP, PCs y cables
python DescifradoPKT/pkt.py resumen practica_final.pkt --solo RB HB  # solo la organización B
python DescifradoPKT/pkt.py resumen practica_final.pkt --json        # lo mismo en JSON
python DescifradoPKT/pkt.py xml practica_final.pkt -o escenario.xml  # XML completo (incluye <RUNNINGCONFIG> de cada router)
python DescifradoPKT/pkt.py verificar practica_final.pkt             # comprueba el descifrado (tag EAX y round-trip)
```

Para usarlo como módulo: `sys.path.insert(0, 'DescifradoPKT'); import pkt; xml = pkt.leer_xml('practica_final.pkt'); pkt.resumen(xml)`.

- Lee siempre el `.pkt` del disco en ese momento. Lo que el usuario no haya guardado en Packet Tracer no aparece.
- Los nombres de los dispositivos son `RA1..RA6`, `SA*` y `HA*` (organización A, RIP) y `RB1..RB6`, `SB*` y `HB*` (organización B, OSPF). El hostname configurado puede ser distinto (por ejemplo `Router`).

## Editar el `.pkt`

`python DescifradoPKT/pkt.py pkt escenario.xml -o nuevo.pkt` vuelve a cifrar un XML. Es experimental: el cifrado se ha verificado byte a byte, pero cambiar solo el texto del running-config puede no aplicarse en Packet Tracer. Nunca sobrescribas `practica_final.pkt`. Escribe a un fichero nuevo y pide al usuario que lo abra en Packet Tracer para comprobarlo. Lo preferible es darle los comandos IOS para que los teclee.

## Diagrama de la organización B

```bash
python DescifradoPKT/diagrama_orgB.py   # regenera DescifradoPKT/diagrama_orgB.html desde el .pkt
```

Dibuja la topología con interfaces, IPs, redes y áreas OSPF, y lista lo que no cuadra con el diseño (redes mal escritas, interfaces en shutdown, pasivas incorrectas, hosts sin puerta de enlace). El diseño esperado está en `DescifradoPKT/diagrama_orgB.py`: `AREA_SEGMENTO` y `HOSTS_LAN`. La plantilla visual es `DescifradoPKT/plantilla_orgB.html`.

## Direccionamiento (X=3, Y=1, Z=8)

- Organización A: `172.81.48.0/22`
- Organización B: `173.81.16.0/20`. Agregados por área: 1 → `173.81.16.0/26`, 2 → `173.81.16.64/26`, 3 → `173.81.16.128/25`. El área 0 son los P2P en `173.81.17.0/28`.
