#!/usr/bin/env python3
"""
pkt.py — leer (y, con cuidado, escribir) ficheros .pkt/.pka de Cisco Packet Tracer 7/8/9.
Python 3 puro, sin dependencias.

USO DESDE TERMINAL (desde la carpeta del repo):
    python DescifradoPKT/pkt.py resumen practica_final.pkt           # texto legible: routers, interfaces, IPs, OSPF/RIP, cables, PCs
    python DescifradoPKT/pkt.py resumen practica_final.pkt --json    # lo mismo en JSON
    python DescifradoPKT/pkt.py resumen practica_final.pkt --solo RB # solo dispositivos cuyo nombre empiece por RB
    python DescifradoPKT/pkt.py xml practica_final.pkt -o escenario.xml      # XML completo
    python DescifradoPKT/pkt.py verificar practica_final.pkt                 # comprueba tag EAX y que la reescritura es idéntica
    python DescifradoPKT/pkt.py pkt escenario.xml -o nuevo.pkt               # XML -> .pkt (EXPERIMENTAL, ver abajo)

USO COMO MÓDULO:
    import sys; sys.path.insert(0, 'DescifradoPKT'); import pkt
    xml = pkt.leer_xml('practica_final.pkt')      # bytes del XML
    datos = pkt.resumen(xml)                      # dict con devices / links
    pkt.escribir_pkt(xml, 'copia.pkt')            # XML -> .pkt

FORMATO (PT 8.2+/9; ingeniería inversa de la comunidad: pka2xml, pktfile):
    fichero = ofuscar( TwofishEAX( mascara( tamaño_BE32 + zlib(XML) ) ) + tag )
    1. ofuscación externa: out[i] = in[n-1-i] ^ ((n - i*n) & 0xFF)       (n = len fichero)
    2. Twofish-128 en modo EAX, clave 0x89 x16, nonce 0x10 x16, sin cabecera, tag de 16 bytes al final
    3. máscara interna: b[i] ^= (L - i) & 0xFF                            (L = len del texto en claro)  <- solo PT >= 8.2
    4. 4 bytes big-endian con el tamaño del XML + flujo zlib (formato qCompress de Qt)
    Ficheros de PT < 8.2 no tienen el paso 3: leer_xml() lo detecta y prueba ambos.

SOBRE EDITAR:
    El XML guarda el running-config de cada router (<RUNNINGCONFIG>), pero Packet Tracer también guarda
    el estado interno del equipo en otras etiquetas; cambiar solo el texto del running-config puede no
    aplicarse o dejar el escenario incoherente. Para cambios reales, mejor teclear los comandos en PT.
    Si se edita: escribir SIEMPRE a un fichero nuevo, abrirlo en PT y comprobar antes de sustituir el original.
"""
import sys, os, zlib, struct, json, argparse
import xml.etree.ElementTree as ET

__all__ = ['leer_xml', 'escribir_pkt', 'descifrar', 'cifrar', 'resumen', 'texto_resumen']

# ---------------------------------------------------------------------------
# Twofish (cifrado de bloque; EAX solo necesita la dirección de cifrado)
# ---------------------------------------------------------------------------
_T = (
    ([8,1,7,13,6,15,3,2,0,11,5,9,14,12,10,4],[14,12,11,8,1,2,3,5,15,4,10,6,7,0,9,13],
     [11,10,5,14,6,13,9,0,12,8,15,3,2,4,7,1],[13,7,15,4,1,2,6,14,9,11,3,0,8,5,12,10]),
    ([2,8,11,13,15,7,6,14,3,1,9,4,0,10,12,5],[1,14,2,11,4,12,3,7,6,13,10,5,15,9,0,8],
     [4,12,7,5,1,6,9,10,0,14,13,8,2,11,3,15],[11,9,5,1,12,3,13,14,6,4,7,15,2,0,8,10]),
)
def _ror4(x, n): return ((x >> n) | (x << (4 - n))) & 15
def _q(x, t):
    a0, b0 = x >> 4, x & 15
    a1, b1 = a0 ^ b0, (a0 ^ _ror4(b0, 1) ^ ((8 * a0) & 15)) & 15
    a2, b2 = t[0][a1], t[1][b1]
    a3, b3 = a2 ^ b2, (a2 ^ _ror4(b2, 1) ^ ((8 * a2) & 15)) & 15
    return (16 * t[3][b3] + t[2][a3]) & 255
_Q0 = [_q(i, _T[0]) for i in range(256)]
_Q1 = [_q(i, _T[1]) for i in range(256)]
def _gmul(a, b, poly):
    r = 0
    while b:
        if b & 1: r ^= a
        a <<= 1
        if a & 0x100: a ^= poly
        b >>= 1
    return r & 255
_MDS = [[0x01,0xEF,0x5B,0x5B],[0x5B,0xEF,0xEF,0x01],[0xEF,0x5B,0x01,0xEF],[0xEF,0x01,0xEF,0x5B]]
_RS = [[0x01,0xA4,0x55,0x87,0x5A,0x58,0xDB,0x9E],[0xA4,0x56,0x82,0xF3,0x1E,0xC6,0x68,0xE5],
       [0x02,0xA1,0xFC,0xC1,0x47,0xAE,0x3D,0x19],[0xA4,0x55,0x87,0x5A,0x58,0xDB,0x9E,0x03]]
_MDS_T = [[[_gmul(_MDS[i][j], v, 0x169) for v in range(256)] for j in range(4)] for i in range(4)]
# por posición de byte: (q con L3, q con L2, q1, q2, q3) de la función h
_CADENA = ((_Q1, _Q1, _Q0, _Q0, _Q1), (_Q0, _Q1, _Q1, _Q0, _Q0), (_Q0, _Q0, _Q0, _Q1, _Q1), (_Q1, _Q0, _Q1, _Q1, _Q0))
def _rol(x, n): return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF
def _ror(x, n): return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF

class Twofish:
    """Twofish con clave de 128/192/256 bits. Solo encrypt()."""
    def __init__(self, key):
        k = len(key) // 8
        self.k = k
        Me = [list(key[8*i:8*i+4]) for i in range(k)]
        Mo = [list(key[8*i+4:8*i+8]) for i in range(k)]
        S = []
        for i in range(k):
            m = key[8*i:8*i+8]
            S.append([0] * 4)
            for r in range(4):
                v = 0
                for j in range(8): v ^= _gmul(_RS[r][j], m[j], 0x14D)
                S[-1][r] = v
        self.K = []
        for i in range(20):
            A = self._h(2 * i * 0x01010101, Me)
            B = _rol(self._h((2 * i + 1) * 0x01010101, Mo), 8)
            self.K += [(A + B) & 0xFFFFFFFF, _rol((A + 2 * B) & 0xFFFFFFFF, 9)]
        # g(x) = h(x, S): como h trata cada byte por separado y MDS es lineal, se precalcula por byte
        Sr = S[::-1]
        self.G = [[self._hbyte(pos, b, Sr) for b in range(256)] for pos in range(4)]

    def _hbyte(self, pos, b, L):
        a, b_, c, d, e = _CADENA[pos]
        y = b
        if self.k == 4: y = a[y] ^ L[3][pos]
        if self.k >= 3: y = b_[y] ^ L[2][pos]
        y = e[d[c[y] ^ L[1][pos]] ^ L[0][pos]]
        return sum(_MDS_T[i][pos][y] << (8 * i) for i in range(4))

    def _h(self, x, L):
        return (self._hbyte(0, x & 255, L) ^ self._hbyte(1, (x >> 8) & 255, L) ^
                self._hbyte(2, (x >> 16) & 255, L) ^ self._hbyte(3, x >> 24, L))

    def encrypt(self, blk):
        K, G = self.K, self.G
        g = lambda x: G[0][x & 255] ^ G[1][(x >> 8) & 255] ^ G[2][(x >> 16) & 255] ^ G[3][x >> 24]
        R = [struct.unpack('<I', blk[4*i:4*i+4])[0] ^ K[i] for i in range(4)]
        for r in range(16):
            t0, t1 = g(R[0]), g(_rol(R[1], 8))
            R[2] = _ror(R[2] ^ ((t0 + t1 + K[2*r+8]) & 0xFFFFFFFF), 1)
            R[3] = _rol(R[3], 1) ^ ((t0 + 2 * t1 + K[2*r+9]) & 0xFFFFFFFF)
            if r < 15: R = [R[2], R[3], R[0], R[1]]
        return b''.join(struct.pack('<I', R[i] ^ K[4 + i]) for i in range(4))

def _autotest():
    # vector oficial: clave 0, texto 0
    assert Twofish(bytes(16)).encrypt(bytes(16)).hex().upper() == '9F589F5CF6122C32B6BFEC2F2AE8C35A', 'Twofish roto'

# ---------------------------------------------------------------------------
# EAX
# ---------------------------------------------------------------------------
_CLAVE, _NONCE = bytes([0x89]) * 16, bytes([0x10]) * 16

def _xor(a, b): return bytes(x ^ y for x, y in zip(a, b))
def _dbl(b):
    v = int.from_bytes(b, 'big') << 1
    if v >> 128: v = (v & ((1 << 128) - 1)) ^ 0x87
    return v.to_bytes(16, 'big')
def _omac(tf, t, data):
    data = bytes(15) + bytes([t]) + data
    K1 = _dbl(tf.encrypt(bytes(16))); K2 = _dbl(K1)
    n = (len(data) + 15) // 16
    if len(data) % 16 == 0: last = _xor(data[-16:], K1)
    else:
        rem = data[(n - 1) * 16:]
        last = _xor(rem + b'\x80' + bytes(15 - len(rem)), K2)
    x = bytes(16)
    for i in range(n - 1): x = tf.encrypt(_xor(x, data[16*i:16*i+16]))
    return tf.encrypt(_xor(x, last))
def _ctr(tf, iv, data):
    ctr, out = int.from_bytes(iv, 'big'), bytearray()
    for i in range(0, len(data), 16):
        out += _xor(data[i:i+16], tf.encrypt(ctr.to_bytes(16, 'big')))
        ctr = (ctr + 1) & ((1 << 128) - 1)
    return bytes(out)
def _tag(tf, n_, ct): return _xor(_xor(n_, _omac(tf, 1, b'')), _omac(tf, 2, ct))

# ---------------------------------------------------------------------------
# Capas del formato
# ---------------------------------------------------------------------------
def _desofuscar(raw):
    n = len(raw)
    return bytes(raw[n - 1 - i] ^ ((n - i * n) & 0xFF) for i in range(n))
def _ofuscar(s):
    n = len(s)
    out = bytearray(n)
    for i in range(n): out[n - 1 - i] = s[i] ^ ((n - i * n) & 0xFF)
    return bytes(out)
def _mascara(b):
    L = len(b)
    return bytes(b[i] ^ ((L - i) & 0xFF) for i in range(L))

def descifrar(raw, verificar_tag=True):
    """bytes del .pkt -> (bytes en claro [tamaño+zlib], tag_ok)."""
    _autotest()
    s = _desofuscar(raw)
    tf = Twofish(_CLAVE)
    n_ = _omac(tf, 0, _NONCE)
    ct, tag = s[:-16], s[-16:]
    claro = _ctr(tf, n_, ct)
    ok = (_tag(tf, n_, ct) == tag) if verificar_tag else None
    return claro, ok

def cifrar(claro):
    """bytes en claro [tamaño+zlib, ya con máscara] -> bytes del .pkt."""
    tf = Twofish(_CLAVE)
    n_ = _omac(tf, 0, _NONCE)
    ct = _ctr(tf, n_, claro)
    return _ofuscar(ct + _tag(tf, n_, ct))

def leer_xml(ruta_o_bytes):
    """Ruta (o bytes) de un .pkt/.pka -> bytes del XML."""
    raw = open(ruta_o_bytes, 'rb').read() if isinstance(ruta_o_bytes, (str, os.PathLike)) else ruta_o_bytes
    claro, _ = descifrar(raw, verificar_tag=False)
    for cand in (_mascara(claro), claro):          # PT >= 8.2 con máscara; antiguos sin ella
        try:
            return zlib.decompress(cand[4:])
        except zlib.error:
            pass
    raise ValueError('No se pudo descomprimir: formato de .pkt no reconocido')

def escribir_pkt(xml, ruta, con_mascara=True):
    """bytes/str del XML -> fichero .pkt. No sobrescribe sin querer: comprueba tú la ruta."""
    if isinstance(xml, str): xml = xml.encode('utf-8')
    claro = struct.pack('>I', len(xml)) + zlib.compress(xml, 9)
    if con_mascara: claro = _mascara(claro)
    open(ruta, 'wb').write(cifrar(claro))

# ---------------------------------------------------------------------------
# Resumen legible del escenario
# ---------------------------------------------------------------------------
def _parse_config(lines):
    hostname, ifaces, bloques, cur = None, [], [], None
    for ln in lines:
        s = ln.strip()
        if not s or s == '!': cur = None; continue
        if not ln.startswith(' '):
            cur = None
            if s.startswith('hostname '): hostname = s.split()[1]
            elif s.startswith('interface '):
                cur = {'nombre': s.split()[1], 'ip': None, 'mascara': None, 'shutdown': False, 'otras': []}
                ifaces.append(cur)
            elif s.startswith('router '):
                cur = {'bloque': s, 'lineas': []}; bloques.append(cur)
            continue
        if cur is None: continue
        if 'nombre' in cur:
            p = s.split()
            if p[:2] == ['ip', 'address'] and len(p) >= 4: cur['ip'], cur['mascara'] = p[2], p[3]
            elif s == 'shutdown': cur['shutdown'] = True
            elif s not in ('no ip address',) and not s.startswith(('duplex', 'speed')): cur['otras'].append(s)
        else:
            cur['lineas'].append(s)
    return hostname, ifaces, bloques

def resumen(xml):
    """XML (bytes/str) -> dict {'version', 'dispositivos': [...], 'cables': [...]}."""
    root = ET.fromstring(xml)
    ids, devs = {}, []
    for d in root.find('NETWORK/DEVICES'):
        e = d.find('ENGINE')
        nombre, tipo = e.findtext('NAME'), e.findtext('TYPE')
        modelo = e.find('TYPE').get('model') if e.find('TYPE') is not None else None
        ids[e.findtext('SAVE_REF_ID')] = nombre
        dev = {'nombre': nombre, 'tipo': tipo, 'modelo': modelo}
        rc = e.find('RUNNINGCONFIG')
        if rc is not None and tipo == 'Router':
            lineas = [(l.text or '').rstrip() for l in rc]
            hn, ifs, bl = _parse_config(lineas)
            dev.update(hostname=hn, interfaces=[i for i in ifs if i['ip'] or not i['shutdown']],
                       enrutamiento=bl, running_config=lineas)
        elif tipo in ('Pc', 'Laptop', 'Server'):
            for port in e.iter('PORT'):
                if port.findtext('IP'):
                    dev.update(ip=port.findtext('IP'), mascara=port.findtext('SUBNET')); break
            dev['gateway'] = e.findtext('GATEWAY') or None
        devs.append(dev)
    cables = []
    links = root.find('NETWORK/LINKS')
    for l in (links if links is not None else []):
        c = l.find('CABLE')
        if c is None: continue
        p = [x.text for x in c.findall('PORT')]
        cables.append({'tipo': l.findtext('TYPE'), 'de': ids.get(c.findtext('FROM')), 'puerto_de': p[0] if p else None,
                       'a': ids.get(c.findtext('TO')), 'puerto_a': p[1] if len(p) > 1 else None})
    return {'version': root.findtext('VERSION'), 'dispositivos': devs, 'cables': cables}

def texto_resumen(datos, prefijo=None):
    sel = lambda n: not prefijo or (n or '').startswith(tuple(prefijo))
    out = [f"Packet Tracer {datos['version']}"]
    for d in sorted(datos['dispositivos'], key=lambda d: (d['tipo'] != 'Router', d['nombre'])):
        if not sel(d['nombre']) or d['tipo'] in ('Power Distribution Device',): continue
        if d['tipo'] == 'Router':
            hn = f"  (hostname {d['hostname']})" if d.get('hostname') != d['nombre'] else ''
            out.append(f"\n== {d['nombre']}{hn}")
            for i in d['interfaces']:
                ip = f"{i['ip']} {i['mascara']}" if i['ip'] else 'sin IP'
                extra = (' · ' + ' · '.join(i['otras'])) if i['otras'] else ''
                out.append(f"   {i['nombre']:<18} {ip:<32} {'SHUTDOWN' if i['shutdown'] else 'up'}{extra}")
            for b in d['enrutamiento']:
                out.append(f"   {b['bloque']}")
                out += [f"     {x}" for x in b['lineas'] if x != 'log-adjacency-changes']
        elif 'ip' in d or d['tipo'] in ('Pc', 'Laptop', 'Server'):
            out.append(f"\n== {d['nombre']} ({d['tipo']})  {d.get('ip') or 'sin IP'} {d.get('mascara') or ''}  gw {d.get('gateway') or '—'}")
    cab = [c for c in datos['cables'] if sel(c['de']) or sel(c['a'])]
    if cab:
        out.append('\n== Cables')
        for c in cab:
            out.append(f"   {c['de']} {c['puerto_de']}  <->  {c['a']} {c['puerto_a']}   [{c['tipo']}]")
    return '\n'.join(out)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass
    ap = argparse.ArgumentParser(description='Leer/escribir ficheros de Cisco Packet Tracer (.pkt/.pka).')
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('resumen', help='routers, interfaces, IPs, enrutamiento, PCs y cables')
    a.add_argument('pkt'); a.add_argument('--json', action='store_true')
    a.add_argument('--solo', nargs='*', help='prefijos de nombre, p.ej. --solo RB SB HB')
    a = sub.add_parser('xml', help='volcar el XML completo'); a.add_argument('pkt'); a.add_argument('-o', '--salida')
    a = sub.add_parser('pkt', help='XML -> .pkt (experimental)'); a.add_argument('xml'); a.add_argument('-o', '--salida', required=True)
    a.add_argument('--sin-mascara', action='store_true', help='formato PT < 8.2')
    a = sub.add_parser('verificar', help='comprobar tag EAX y round-trip exacto'); a.add_argument('pkt')
    args = ap.parse_args(argv)

    if args.cmd == 'resumen':
        d = resumen(leer_xml(args.pkt))
        if args.solo:
            d = {**d, 'dispositivos': [x for x in d['dispositivos'] if x['nombre'].startswith(tuple(args.solo))]}
        print(json.dumps(d, ensure_ascii=False, indent=1) if args.json else texto_resumen(d, args.solo))
    elif args.cmd == 'xml':
        x = leer_xml(args.pkt)
        if args.salida: open(args.salida, 'wb').write(x); print(f'{len(x)} bytes -> {args.salida}')
        else: sys.stdout.write(x.decode('utf-8', 'replace'))
    elif args.cmd == 'pkt':
        if os.path.exists(args.salida):
            sys.exit(f'{args.salida} ya existe; elige otro nombre (no sobrescribo).')
        escribir_pkt(open(args.xml, 'rb').read(), args.salida, con_mascara=not args.sin_mascara)
        print(f'-> {args.salida}  (ábrelo en Packet Tracer y comprueba antes de usarlo)')
    elif args.cmd == 'verificar':
        raw = open(args.pkt, 'rb').read()
        claro, ok = descifrar(raw)
        print('tag EAX:', 'OK' if ok else 'NO coincide')
        print('round-trip exacto:', 'OK' if cifrar(claro) == raw else 'distinto')
        x = leer_xml(raw)
        print(f'XML: {len(x)} bytes, PT {ET.fromstring(x).findtext("VERSION")}')

if __name__ == '__main__':
    main()
