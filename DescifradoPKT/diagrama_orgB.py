#!/usr/bin/env python3
"""
Genera un diagrama HTML de la Organización B (OSPF) leyendo directamente practica_final.pkt.

Uso (desde la carpeta del repo):
    python DescifradoPKT/diagrama_orgB.py                      # lee practica_final.pkt -> DescifradoPKT/diagrama_orgB.html
    python DescifradoPKT/diagrama_orgB.py otro.pkt salida.html

El descifrado del .pkt está en DescifradoPKT/pkt.py. Solo lee el .pkt; nunca lo modifica.
"""
import sys, os, json, ipaddress, datetime
import xml.etree.ElementTree as ET

# 1) Descifrado: ver DescifradoPKT/pkt.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pkt import leer_xml as pkt_a_xml

# =====================================================================
# 2) Diseño de la práctica (enunciado): áreas, hosts y posiciones
# =====================================================================
AREA_SEGMENTO = {
    'P2P B1-2': 0, 'P2P B1-3': 0, 'P2P B2-3': 0,
    'LAN B2': 1,
    'LAN B3': 2, 'LAN B4': 2,
    'LAN B5': 3, 'LAN B6': 3, 'P2P B3-5': 3, 'P2P B3-6': 3, 'P2P B5-6': 3,
}
HOSTS_LAN = {'LAN B2': 60, 'LAN B3': 20, 'LAN B4': 30, 'LAN B5': 16, 'LAN B6': 20}

# Coordenadas del dibujo (viewBox 1180 x 860), imitando la figura 2 del enunciado
POS = {
    'RB1': (190, 130), 'RB2': (700, 130), 'SB2': (890, 130), 'HB2': (1065, 130),
    'RB3': (460, 370), 'SB3': (300, 500), 'RB4': (125, 540), 'SB4': (125, 680), 'HB4': (310, 760),
    'RB5': (560, 610), 'SB5': (560, 740), 'HB5': (745, 790),
    'RB6': (905, 460), 'SB6': (955, 615), 'HB6': (1080, 705),
}
LAN_LABEL = {'LAN B2': (890, 190), 'LAN B3': (318, 550), 'LAN B4': (112, 752),
             'LAN B5': (560, 806), 'LAN B6': (895, 672)}
AREA_HULL = {
    0: [(95, 60), (500, 40), (790, 60), (805, 190), (560, 430), (380, 440), (95, 210)],
    1: [(640, 55), (900, 45), (1160, 60), (1160, 205), (900, 225), (640, 205)],
    2: [(430, 300), (535, 380), (430, 560), (420, 830), (30, 835), (25, 470), (230, 420)],
    3: [(420, 330), (620, 300), (1010, 385), (1165, 620), (1160, 830), (820, 845), (470, 840), (470, 580), (395, 430)],
}
AREA_LABEL = {0: (445, 205, 'ÁREA 0 · backbone'), 1: (1035, 205, 'ÁREA 1'),
              2: (55, 455, 'ÁREA 2'), 3: (1080, 405, 'ÁREA 3')}

def corto(ifn):
    for largo, c in (('FastEthernet', 'Fa'), ('GigabitEthernet', 'Gi'), ('Serial', 'S'), ('Ethernet', 'E')):
        if ifn.startswith(largo): return c + ifn[len(largo):]
    return ifn

def wildcard(mask):
    return str(ipaddress.IPv4Address(0xFFFFFFFF ^ int(ipaddress.IPv4Address(mask))))

# =====================================================================
# 3) Extracción
# =====================================================================
def parse_router(eng):
    rc = eng.find('RUNNINGCONFIG')
    lines = [(l.text or '').rstrip() for l in rc] if rc is not None else []
    ifaces, ospf, cur, in_ospf, hostname = {}, None, None, False, None
    for ln in lines:
        s = ln.strip()
        if not ln.startswith(' '):
            cur, in_ospf = None, False
            if s.startswith('hostname '): hostname = s.split()[1]
            elif s.startswith('interface '):
                cur = {'name': s.split()[1], 'ip': None, 'mask': None, 'shutdown': False, 'extra': []}
                ifaces[cur['name']] = cur
            elif s.startswith('router ospf'):
                ospf = {'pid': s.split()[2], 'networks': [], 'passive': [], 'extra': [], 'lines': [s]}
                in_ospf = True
            continue
        if cur is not None:
            if s.startswith('ip address ') and len(s.split()) >= 4:
                cur['ip'], cur['mask'] = s.split()[2], s.split()[3]
            elif s == 'shutdown': cur['shutdown'] = True
            elif s.startswith(('ip ospf', 'bandwidth')): cur['extra'].append(s)
        elif in_ospf:
            ospf['lines'].append(s)
            p = s.split()
            if p[0] == 'network' and len(p) >= 5:
                ospf['networks'].append({'net': p[1], 'wc': p[2], 'area': int(p[4]) if p[4].isdigit() else p[4], 'usada': False})
            elif p[0] == 'passive-interface': ospf['passive'].append(p[1])
            else: ospf['extra'].append(s)
    return hostname, ifaces, ospf, lines

def area_configurada(ospf, ip):
    if not ospf or not ip: return None
    a = int(ipaddress.IPv4Address(ip))
    for n in ospf['networks']:
        try:
            wc = int(ipaddress.IPv4Address(n['wc'])); net = int(ipaddress.IPv4Address(n['net']))
        except ValueError:
            continue
        if (a & ~wc & 0xFFFFFFFF) == (net & ~wc & 0xFFFFFFFF):
            n['usada'] = True
            return n['area']
    return None

def construir(xml_bytes, pkt_name):
    root = ET.fromstring(xml_bytes)
    version = root.findtext('VERSION')
    devs, ids = {}, {}
    for d in root.find('NETWORK/DEVICES'):
        e = d.find('ENGINE')
        name, typ = e.findtext('NAME'), e.findtext('TYPE')
        ids[e.findtext('SAVE_REF_ID')] = name
        devs[name] = (typ, e)
    orgB = lambda n: n and n[:2] in ('RB', 'SB', 'HB')

    routers, hosts = {}, {}
    for name, (typ, e) in devs.items():
        if not orgB(name): continue
        if typ == 'Router':
            hn, ifs, ospf, lines = parse_router(e)
            routers[name] = {'hostname': hn, 'ifs': ifs, 'ospf': ospf, 'lines': lines}
        elif typ == 'Pc':
            ip = mask = gw = None
            for port in e.iter('PORT'):
                if port.findtext('IP'):
                    ip, mask = port.findtext('IP'), port.findtext('SUBNET'); break
            gw = e.findtext('GATEWAY') or None
            hosts[name] = {'ip': ip, 'mask': mask, 'gw': gw}

    # Enlaces físicos
    links = []
    for l in root.find('NETWORK/LINKS'):
        c = l.find('CABLE')
        a, b = ids.get(c.findtext('FROM')), ids.get(c.findtext('TO'))
        if not (orgB(a) and orgB(b)): continue
        pa, pb = [p.text for p in c.findall('PORT')][:2]
        links.append({'a': a, 'ai': pa, 'b': b, 'bi': pb, 'tipo': l.findtext('TYPE')})

    # Segmentos: P2P (router-router) y LAN (agrupados por switch)
    segs = {}
    for lk in links:
        a, b = lk['a'], lk['b']
        if a.startswith('RB') and b.startswith('RB'):
            x, y = sorted([(a, lk['ai']), (b, lk['bi'])])
            name = f'P2P B{x[0][2:]}-{y[0][2:]}'
            segs[name] = {'name': name, 'kind': 'p2p', 'ends': [x, y], 'hosts': [], 'switch': None}
            lk['seg'] = name
    for lk in links:
        sw = lk['a'] if lk['a'].startswith('SB') else lk['b'] if lk['b'].startswith('SB') else None
        if not sw: continue
        other, oi = (lk['b'], lk['bi']) if lk['a'] == sw else (lk['a'], lk['ai'])
        name = 'LAN B' + sw[2:]
        s = segs.setdefault(name, {'name': name, 'kind': 'lan', 'ends': [], 'hosts': [], 'switch': sw})
        lk['seg'] = name
        if other.startswith('RB'): s['ends'].append((other, oi))
        elif other.startswith('HB'): s['hosts'].append(other)

    issues = []
    def issue(sev, dev, text, fix=None): issues.append({'sev': sev, 'dev': dev, 'text': text, 'fix': fix})

    seg_list = []
    for name in sorted(segs, key=lambda n: (AREA_SEGMENTO.get(n, 9), n)):
        s = segs[name]
        area = AREA_SEGMENTO.get(name)
        net = None
        ends = []
        for dev, ifn in s['ends']:
            itf = routers.get(dev, {}).get('ifs', {}).get(ifn, {})
            ip, mask = itf.get('ip'), itf.get('mask')
            if ip and mask and net is None:
                net = ipaddress.IPv4Interface(f'{ip}/{mask}').network
            ends.append({'dev': dev, 'iface': ifn, 'short': corto(ifn), 'ip': ip, 'mask': mask})
        for h in s['hosts']:
            hh = hosts.get(h, {})
            if hh.get('ip') and hh.get('mask') and net is None:
                net = ipaddress.IPv4Interface(f"{hh['ip']}/{hh['mask']}").network
        d = {'name': name, 'kind': s['kind'], 'area': area, 'switch': s['switch'], 'hosts': s['hosts'],
             'ends': ends, 'net': str(net.network_address) if net else None,
             'prefix': net.prefixlen if net else None, 'mask': str(net.netmask) if net else None,
             'wc': wildcard(str(net.netmask)) if net else None,
             'capacidad': (net.num_addresses - 2) if net else None, 'req': HOSTS_LAN.get(name)}
        if s['kind'] == 'lan':
            d['solo_un_router'] = len(ends) == 1
        if net is None:
            issue('error', name, f'{name}: ninguna interfaz tiene IP, no se puede deducir la red.')
        else:
            for e in ends:
                if e['ip'] and ipaddress.IPv4Address(e['ip']) not in net:
                    issue('error', e['dev'], f"{e['dev']} {e['short']} ({e['ip']}) no está en la red {net} de {name}.")
            for h in s['hosts']:
                hh = hosts.get(h, {})
                if hh.get('ip') and ipaddress.IPv4Address(hh['ip']) not in net:
                    issue('error', h, f"{h} ({hh['ip']}) no está en la red {net} de {name}.")
            if d['req'] and d['capacidad'] < d['req']:
                issue('error', name, f"{name}: /{net.prefixlen} da {d['capacidad']} hosts y se piden {d['req']}.")
        seg_list.append(d)
    seg_by_iface = {(e['dev'], e['iface']): s for s in seg_list for e in s['ends']}

    # Routers: estado por interfaz, rol, comandos sugeridos
    r_out = {}
    for name in sorted(routers):
        r = routers[name]
        ospf = r['ospf']
        if r['hostname'] != name:
            issue('info', name, f"{name} tiene hostname «{r['hostname']}».", f'hostname {name}')
        if ospf is None:
            issue('error', name, f'{name} no tiene «router ospf» configurado.')
        ifs_out, areas, fixes_if, nets_sug, pasivas_sug = [], set(), [], [], []
        for ifn, itf in r['ifs'].items():
            seg = seg_by_iface.get((name, ifn))
            if not seg and not itf['ip']: continue   # puerto libre sin configurar
            a_exp = seg['area'] if seg else None
            a_cfg = area_configurada(ospf, itf['ip'])
            if a_exp is not None: areas.add(a_exp)
            if not itf['ip']: estado = 'sin-ip'
            elif itf['shutdown']: estado = 'shutdown'
            elif a_cfg is None: estado = 'sin-ospf'
            elif a_exp is not None and a_cfg != a_exp: estado = 'area-mal'
            else: estado = 'ok'
            sc = corto(ifn)
            if seg and not itf['ip']:
                issue('error', name, f'{name} {sc} ({seg["name"]}) no tiene IP.')
            if itf['ip'] and itf['shutdown']:
                issue('error', name, f'{name} {sc} está en shutdown.', f'interface {ifn}\n no shutdown')
                fixes_if.append(f'interface {ifn}\n no shutdown')
            if itf['ip'] and ospf is not None and a_cfg is None and seg:
                issue('warn', name, f'{name} {sc} ({seg["name"]}) no entra en ningún «network» de OSPF.')
            if a_cfg is not None and a_exp is not None and a_cfg != a_exp:
                issue('error', name, f'{name} {sc} está en el área {a_cfg} y debería ir en la {a_exp}.')
            pasiva = bool(ospf and ifn in ospf['passive'])
            if seg and seg['kind'] == 'lan' and ospf is not None:
                if seg.get('solo_un_router') and not pasiva:
                    issue('warn', name, f'{name} {sc}: {seg["name"]} solo tiene hosts, debería ser pasiva.')
                if not seg.get('solo_un_router') and pasiva:
                    issue('error', name, f'{name} {sc} es pasiva, pero en {seg["name"]} hay otro router OSPF: no formarán adyacencia (ni DR/BDR).',
                          f'router ospf {ospf["pid"]}\n no passive-interface {ifn}')
            if seg and seg['net']:
                nets_sug.append(f" network {seg['net']} {seg['wc']} area {a_exp}")
                if seg['kind'] == 'lan' and seg.get('solo_un_router'): pasivas_sug.append(f' passive-interface {ifn}')
            ifs_out.append({'name': ifn, 'short': sc, 'ip': itf['ip'], 'mask': itf['mask'],
                            'prefix': ipaddress.IPv4Network(f"0.0.0.0/{itf['mask']}").prefixlen if itf['mask'] else None,
                            'seg': seg['name'] if seg else None, 'net': seg['net'] if seg else None,
                            'area_exp': a_exp, 'area_cfg': a_cfg, 'estado': estado, 'pasiva': pasiva,
                            'extra': itf['extra']})
        sobran = []
        if ospf:
            for n in ospf['networks']:
                if not n['usada']:
                    issue('error', name, f"{name}: «network {n['net']} {n['wc']} area {n['area']}» no coincide con ninguna interfaz.",
                          f"router ospf {ospf['pid']}\n no network {n['net']} {n['wc']} area {n['area']}")
                    sobran.append(f" no network {n['net']} {n['wc']} area {n['area']}")
        rol = 'ABR' if len(areas) > 1 and 0 in areas else ('backbone' if areas == {0} else 'interno')
        pid = ospf['pid'] if ospf else '1'
        sug = []
        if r['hostname'] != name: sug.append(f'hostname {name}')
        sug += fixes_if
        sug.append('\n'.join([f'router ospf {pid}'] + sobran + sorted(set(nets_sug)) + pasivas_sug))
        r_out[name] = {'hostname': r['hostname'], 'ifs': ifs_out, 'areas': sorted(areas), 'rol': rol,
                       'ospf': ospf and {'pid': ospf['pid'], 'lines': ospf['lines']},
                       'sugerido': '\n!\n'.join(sug)}

    # Hosts
    h_out = {}
    for name in sorted(hosts):
        h = hosts[name]
        seg = next((s for s in seg_list if name in s['hosts']), None)
        gw_exp = seg['ends'][0]['ip'] if seg and seg['ends'] else None
        if not h['ip']: issue('error', name, f'{name} no tiene IP.')
        if not h['gw']: issue('warn', name, f'{name} no tiene puerta de enlace (debería ser {gw_exp}).')
        elif gw_exp and h['gw'] != gw_exp: issue('error', name, f"{name} usa la puerta de enlace {h['gw']} y debería ser {gw_exp}.")
        h_out[name] = {**h, 'gw_exp': gw_exp, 'seg': seg['name'] if seg else None,
                       'prefix': ipaddress.IPv4Network(f"0.0.0.0/{h['mask']}").prefixlen if h['mask'] else None}

    # Agregación por área (para «area X range» en el ABR)
    resum = []
    for area in sorted({s['area'] for s in seg_list if s['area'] is not None}):
        nets = [ipaddress.IPv4Network(f"{s['net']}/{s['prefix']}") for s in seg_list if s['area'] == area and s['net']]
        if not nets: continue
        lo = min(int(n.network_address) for n in nets); hi = max(int(n.broadcast_address) for n in nets)
        p = 32
        while p > 0 and (lo >> (32 - p)) != (hi >> (32 - p)): p -= 1
        sup = ipaddress.IPv4Network((lo >> (32 - p) << (32 - p), p))
        abrs = [n for n, r in r_out.items() if r['rol'] == 'ABR' and area in r['areas']] if area else []
        resum.append({'area': area, 'net': str(sup.network_address), 'prefix': p, 'mask': str(sup.netmask),
                      'abr': abrs, 'redes': [str(n) for n in nets],
                      'cmd': f'area {area} range {sup.network_address} {sup.netmask}' if area else None})

    links_draw = [lk for lk in links if lk['a'] in POS and lk['b'] in POS]
    sev_order = {'error': 0, 'warn': 1, 'info': 2}
    issues.sort(key=lambda i: (sev_order[i['sev']], i['dev']))
    return {
        'pkt': pkt_name, 'version': version,
        'generado': datetime.datetime.now().strftime('%d/%m/%Y %H:%M'),
        'routers': r_out, 'hosts': h_out, 'segments': seg_list, 'links': links_draw,
        'issues': issues, 'resumen': resum,
        'layout': {'pos': POS, 'lan_label': LAN_LABEL, 'hull': AREA_HULL, 'area_label': AREA_LABEL},
    }

# =====================================================================
# 4) HTML
# =====================================================================
def main():
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pkt = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base, 'practica_final.pkt')
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diagrama_orgB.html')
    fragmento = '--fragmento' in sys.argv   # sin <!doctype>, para publicar como Artifact
    xml = pkt_a_xml(open(pkt, 'rb').read())
    data = construir(xml, os.path.basename(pkt))
    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plantilla_orgB.html'), encoding='utf-8').read()
    payload = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    html = tpl.replace('/*__DATA__*/{}', payload)
    if not fragmento:
        html = '<!doctype html>\n<html lang="es"><head><meta charset="utf-8">' \
               '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n' + html + '\n</html>'
    open(out, 'w', encoding='utf-8').write(html)
    n = {s: sum(1 for i in data['issues'] if i['sev'] == s) for s in ('error', 'warn', 'info')}
    print(f"OK -> {out}\n   PT {data['version']} · {len(data['routers'])} routers · {len(data['segments'])} redes · "
          f"{n['error']} errores, {n['warn']} avisos, {n['info']} notas")
    for i in data['issues']:
        print(f"   [{i['sev']:5}] {i['text']}")

if __name__ == '__main__':
    main()
