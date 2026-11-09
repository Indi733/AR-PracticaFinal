#!/usr/bin/env python3
"""
Regenera memoria/prueba_salidas.tex con TODAS las salidas de memoria/salidas/,
para compilarlo y revisar cómo quedan antes de meterlas en la memoria.

Uso (desde la raíz del repo):
    python memoria/generar_prueba.py            # solo genera el .tex
    python memoria/generar_prueba.py --pdf      # además lo compila con pdflatex
"""
import os, re, sys, glob, subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
SECCIONES = [('orgA', 'Organización A (RIP)'), ('orgB', 'Organización B (OSPF)'),
             ('interconexion', 'Interconexión y redistribución')]


def esc(s):
    return s.replace('\\', r'\textbackslash{}').replace('_', r'\_').replace('%', r'\%').replace('&', r'\&').replace('#', r'\#')


def main():
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass
    partes = [r'''% GENERADO por memoria/generar_prueba.py: no editar a mano.
% Compila todas las salidas para revisarlas. No es la memoria.
\documentclass[a4paper,11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[spanish]{babel}
\usepackage[margin=2.5cm]{geometry}
\input{salidas_cisco}
\begin{document}
''']
    total = 0
    for carpeta, titulo in SECCIONES:
        ficheros = sorted(glob.glob(os.path.join(AQUI, 'salidas', carpeta, '*.txt')))
        if not ficheros:
            continue
        partes.append(f'\\section*{{{titulo}}}\n')
        for f in ficheros:
            nombre = os.path.splitext(os.path.basename(f))[0]
            # Los mensajes de log (%OSPF-5-ADJCHG...) son largos y es normal que se partan;
            # solo avisamos si una línea de tabla o de salida normal no cabe.
            ancho = max((len(l.rstrip('\n')) for l in open(f, encoding='utf-8')
                         if not re.search(r'%[A-Z]+-\d-', l)), default=0)
            aviso = ' (OJO: más de 82 columnas, alguna línea se partirá)' if ancho > 82 else ''
            partes.append(f'\\salidacisco{{salidas/{carpeta}/{nombre}.txt}}'
                          f'{{\\texttt{{{esc(nombre)}}}{esc(aviso)}}}{{fig:{carpeta}-{nombre.replace("_", "-")}}}\n')
            total += 1
        partes.append('\\clearpage\n')
    partes.append('\\end{document}\n')
    tex = os.path.join(AQUI, 'prueba_salidas.tex')
    with open(tex, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(''.join(partes))
    print(f'{total} salidas -> memoria/prueba_salidas.tex')

    if '--pdf' in sys.argv:
        for _ in range(2):  # dos pasadas para las referencias
            r = subprocess.run(['pdflatex', '-interaction=nonstopmode', 'prueba_salidas.tex'],
                               cwd=AQUI, capture_output=True, text=True, errors='replace')
        if r.returncode == 0:
            print('PDF: memoria/prueba_salidas.pdf')
        else:
            print('pdflatex ha fallado; mira memoria/prueba_salidas.log')


if __name__ == '__main__':
    main()
