#!/usr/bin/env python3
"""
Guarda una salida de Packet Tracer en memoria/salidas/<seccion>/<nombre>.txt,
tal cual, para meterla en la memoria con \\salidacisco.

Uso (desde la raíz del repo):
  1. En Packet Tracer, selecciona la salida en la consola del router y cópiala (Ctrl+C).
  2. Ejecuta:
       python memoria/nueva_salida.py orgA c1_ra4_tabla_rutas
     (sección: orgA, orgB o interconexion; nombre: cN_<router>_<qué es>)
  3. Te imprime la línea de LaTeX lista para pegar.

Opciones:
  --stdin   en vez del portapapeles, pega el texto en la terminal y termina con Ctrl+Z + Enter
            (en Linux/Mac, Ctrl+D).
  --forzar  sobrescribe si el fichero ya existe.

Qué hace con el texto:
  - Lo guarda exactamente igual: espacios, alineación, líneas en blanco intermedias.
  - Solo quita, al principio y al final, las líneas vacías y las que son únicamente el prompt
    (p.ej. "RB3#" o "RA4>"), que salen al copiar de más.
  - Convierte los saltos de línea de Windows (\\r\\n) a \\n.
"""
import sys, os, re, argparse

AQUI = os.path.dirname(os.path.abspath(__file__))
SECCIONES = ('orgA', 'orgB', 'interconexion')
PROMPT_SOLO = re.compile(r'^\s*[A-Za-z0-9_-]+(\([a-z-]+\))?[#>]\s*$')


def leer_portapapeles():
    import tkinter
    r = tkinter.Tk(); r.withdraw()
    try:
        return r.clipboard_get()
    except tkinter.TclError:
        sys.exit('El portapapeles está vacío o no tiene texto. Copia la salida en Packet Tracer (Ctrl+C).')
    finally:
        r.destroy()


def limpiar(texto):
    lineas = texto.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    sobra = lambda l: not l.strip() or PROMPT_SOLO.match(l)
    while lineas and sobra(lineas[0]): lineas.pop(0)
    while lineas and sobra(lineas[-1]): lineas.pop()
    return '\n'.join(lineas) + '\n'


def main():
    for flujo in (sys.stdout, sys.stderr):
        try: flujo.reconfigure(encoding='utf-8')
        except Exception: pass
    ap = argparse.ArgumentParser(description='Guardar una salida de Packet Tracer para la memoria.')
    ap.add_argument('seccion', choices=SECCIONES)
    ap.add_argument('nombre', help='p.ej. c1_ra4_tabla_rutas (sin .txt)')
    ap.add_argument('--stdin', action='store_true', help='leer el texto de la terminal en vez del portapapeles')
    ap.add_argument('--forzar', action='store_true', help='sobrescribir si ya existe')
    a = ap.parse_args()

    nombre = a.nombre[:-4] if a.nombre.endswith('.txt') else a.nombre
    if not re.fullmatch(r'[a-z0-9_]+', nombre):
        sys.exit('Usa solo minúsculas, números y guiones bajos en el nombre, p.ej. c1_ra4_tabla_rutas')
    ruta = os.path.join(AQUI, 'salidas', a.seccion, nombre + '.txt')
    if os.path.exists(ruta) and not a.forzar:
        sys.exit(f'Ya existe {ruta}. Usa --forzar para sobrescribirlo.')

    if a.stdin:
        print('Pega la salida y termina con Ctrl+Z + Enter (Linux/Mac: Ctrl+D):')
        texto = sys.stdin.read()
    else:
        texto = leer_portapapeles()
    texto = limpiar(texto)
    if not texto.strip():
        sys.exit('No hay nada que guardar.')

    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'w', encoding='utf-8', newline='\n') as f:
        f.write(texto)

    n = texto.count('\n')
    ancho = max(len(l) for l in texto.split('\n'))
    print(f'Guardado: memoria/salidas/{a.seccion}/{nombre}.txt  ({n} líneas, la más larga {ancho} caracteres)')
    print(f'Primera línea: {texto.splitlines()[0]}')
    print('\nPara la memoria:')
    print(f'\\salidacisco{{salidas/{a.seccion}/{nombre}.txt}}{{PIE DE FIGURA}}{{fig:{a.seccion}-{nombre.replace("_", "-")}}}')


if __name__ == '__main__':
    main()
