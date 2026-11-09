# DescifradoPKT

Herramientas para leer `practica_final.pkt` sin abrir Packet Tracer. Python 3, sin instalar nada.

| Archivo | Para qué sirve |
|---|---|
| `pkt.py` | Descifra el `.pkt` (Packet Tracer 9) y resume el escenario: routers, interfaces, IPs, OSPF/RIP, PCs y cables. |
| `diagrama_orgB.py` | Genera `diagrama_orgB.html`: la topología de la organización B con interfaces, IPs, redes y áreas, y una lista de lo que no cuadra con el diseño. |
| `plantilla_orgB.html` | Plantilla visual del diagrama. |

Todos los comandos se ejecutan desde la raíz del repo.

## Ver el escenario

```bash
python DescifradoPKT/pkt.py resumen practica_final.pkt
python DescifradoPKT/pkt.py resumen practica_final.pkt --solo RB HB   # solo la organización B
python DescifradoPKT/pkt.py resumen practica_final.pkt --json
python DescifradoPKT/pkt.py xml practica_final.pkt -o escenario.xml   # XML completo
python DescifradoPKT/pkt.py verificar practica_final.pkt              # comprueba que el descifrado es correcto
```

Solo se ve lo que esté guardado en Packet Tracer (Ctrl+S).

## Diagrama de la organización B

```bash
python DescifradoPKT/diagrama_orgB.py
```

Abre `DescifradoPKT/diagrama_orgB.html` en el navegador. Vuelve a ejecutar el comando cada vez que guardes cambios. El HTML no se sube al repo porque se regenera.

## Editar un `.pkt` (experimental)

```bash
python DescifradoPKT/pkt.py pkt escenario.xml -o nuevo.pkt
```

El cifrado está verificado byte a byte, pero Packet Tracer guarda el estado de los equipos en más sitios que el running-config, así que editar solo el texto puede no aplicarse. El comando no sobrescribe ficheros existentes. Antes de usar el resultado, ábrelo en Packet Tracer y compruébalo.

## Cómo se descifra

Es ingeniería inversa de la comunidad ([pka2xml](https://github.com/mircodz/pka2xml), [pktfile](https://docs.rs/pktfile/latest/pktfile/)):

1. Se invierte el fichero y se hace XOR de cada byte con `(n - i*n) & 0xFF`.
2. Se descifra con Twofish-128 en modo EAX: clave `0x89` ×16, nonce `0x10` ×16 y tag de 16 bytes al final.
3. Se hace XOR de cada byte con `(L - i) & 0xFF`. Esta capa solo existe a partir de Packet Tracer 8.2, y por eso las herramientas antiguas fallan con Packet Tracer 9.
4. Quedan 4 bytes big-endian con el tamaño, seguidos de un flujo zlib que contiene el XML.
