#!/usr/bin/env python3
"""
Convierte Preguntas_OrgB_OSPF.md en un borrador LaTeX (memoria/borrador_orgB.tex) y lo compila,
para leer las respuestas de la organización B como quedarían en la memoria.

Uso (desde la raíz del repo):
    python memoria/generar_borrador_orgB.py          # genera y compila -> memoria/borrador_orgB.pdf

No es la memoria final: solo sirve para visualizar y pulir la redacción.
Se regenera entero cada vez, así que lo que se edita es el .md, no el .tex.
"""
import os, re, sys, subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(os.path.dirname(AQUI), 'Preguntas_OrgB_OSPF.md')
SAL = 'salidas/orgB'

# Pie de cada figura
PIES = {
    'c1_rb4_traceroute_hb2': 'Traceroute de RB4 a HB2',
    'c2_rb3_shutdown_s30': 'Desactivación de la interfaz Serial3/0 de RB3',
    'c2_rb3_vecinos': 'Vecinos OSPF de RB3 tras desactivar Serial3/0',
    'c2_rb4_traceroute_hb2': 'Traceroute de RB4 a HB2 tras la caída del enlace RB3--RB2',
    'c2_rb3_no_shutdown_s30_bis': 'Reactivación de la interfaz Serial3/0 de RB3',
    'c3_rb3_interfaz_antes': 'Estado OSPF de la interfaz Fa0/0 de RB3 antes del cambio',
    'c3_prioridades': 'Prioridad OSPF en las interfaces Fa0/0 de RB4 y RB3',
    'c3_rb3_reinicio_fa00': 'Reinicio de la interfaz Fa0/0 de RB3',
    'c3_rb3_interfaz_despues': 'Estado OSPF de la interfaz Fa0/0 de RB3 después del cambio',
    'c4_rb1_interfaz_s20': 'Estado OSPF de la interfaz Serial2/0 de RB1',
    'c4_rb6_tabla_rutas': 'Tabla de rutas de RB6',
    'c5_rb3_area3_stub': 'Configuración del área 3 como stub en RB3',
    'c5_rb5_area3_stub': 'Configuración del área 3 como stub en RB5',
    'c5_rb6_area3_stub': 'Configuración del área 3 como stub en RB6',
    'c5_rb6_tabla_rutas': 'Tabla de rutas de RB6 con el área 3 stub',
    'c6_rb4_tabla_rutas': 'Tabla de rutas de RB4',
    'c6_rb4_traceroute_rb5': 'Traceroute de RB4 a RB5',
    'c7_rb3_area2_nosummary': 'Configuración del área 2 como totally stub en RB3',
    'c7_rb4_area2_stub': 'Configuración del área 2 como stub en RB4',
    'c7_rb4_tabla_rutas': 'Tabla de rutas de RB4 con el área 2 totally stub',
    'c8_hb5_tracert_rb4_antes': 'Tracert de HB5 a RB4 antes del cambio de costes',
    'c8_rb3_coste_s70': 'Coste OSPF de la interfaz Serial7/0 de RB3',
    'c8_rb5_coste_s20': 'Coste OSPF de la interfaz Serial2/0 de RB5',
    'c8_rb4_traceroute_hb5_despues': 'Traceroute de RB4 a HB5 tras el cambio de costes',
    'c8_hb5_tracert_rb4_despues': 'Tracert de HB5 a RB4 tras el cambio de costes',
    'c9_rb2_tabla_rutas_antes': 'Tabla de rutas de RB2 antes de la agregación',
    'c9_rb3_area_range': 'Configuración de la agregación en RB3',
    'c9_rb2_tabla_rutas_despues': 'Tabla de rutas de RB2 después de la agregación',
}


def esc(t):
    t = t.replace('\\', r'\textbackslash{}')
    for a, b in (('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'), ('_', r'\_'),
                 ('{', r'\{'), ('}', r'\}'), ('~', r'\textasciitilde{}'), ('^', r'\textasciicircum{}')):
        t = t.replace(a, b)
    return t


def inline(t, figs):
    """Convierte el formato markdown de una línea a LaTeX y recoge las figuras citadas."""
    out, i = [], 0
    # citas de figuras: *(Figura: `x`)*  o  *(Figuras: `a`, `b` y `c`)*
    # Si van detrás de "la"/"las" ("como vemos en la (Figura: x)") se escriben sin paréntesis.
    patron = re.compile(r'(\b(?:la|las) )?\*\((Figuras?): (.*?)\)\*')
    def cita(m):
        nombres = re.findall(r'`([a-z0-9_]+)`', m.group(3))
        for n in nombres:
            if n not in figs: figs.append(n)
        refs = [f'\\ref{{fig:{n}}}' for n in nombres]
        txt = refs[0] if len(refs) == 1 else ', '.join(refs[:-1]) + ' y ' + refs[-1]
        palabra = 'Figura' if len(refs) == 1 else 'Figuras'
        if m.group(1):
            return f'{m.group(1)}\x00{palabra}~{txt}\x01'
        return f'\x00({palabra}~{txt})\x01'
    t = patron.sub(cita, t)
    # trozos: código, negrita, texto
    piezas = re.split(r'(\x00.*?\x01|`[^`]+`|\*\*[^*]+\*\*)', t)
    for p in piezas:
        if not p: continue
        if p.startswith('\x00'):
            out.append(p[1:-1])
        elif p.startswith('`'):
            out.append(r'\texttt{' + esc(p[1:-1]) + '}')
        elif p.startswith('**'):
            out.append(r'\textbf{' + esc(p[2:-2]) + '}')
        else:
            out.append(esc(p))
    s = ''.join(out)
    s = s.replace('→', r'$\rightarrow$').replace('–', '--')
    return s


def tabla(lineas, figs):
    filas = [[c.strip() for c in l.strip().strip('|').split('|')] for l in lineas]
    cab, cuerpo = filas[0], [f for f in filas[2:]]
    n = len(cab)
    spec = 'l' * (n - 1) + 'X'
    r = [r'\begin{table}[H]', r'\centering', r'\small', rf'\begin{{tabularx}}{{\linewidth}}{{{spec}}}', r'\toprule',
         ' & '.join(r'\textbf{' + inline(c, figs) + '}' for c in cab) + r' \\', r'\midrule']
    for f in cuerpo:
        r.append(' & '.join(inline(c, figs) for c in f) + r' \\')
    r += [r'\bottomrule', r'\end{tabularx}', r'\end{table}']
    return '\n'.join(r)


def figura(n):
    pie = PIES.get(n, n.replace('_', ' '))
    return f'\\salidacisco{{{SAL}/{n}.txt}}{{{esc(pie)}}}{{fig:{n}}}'


def convertir(md):
    lineas = md.split('\n')
    i0 = next(i for i, l in enumerate(lineas) if l.startswith('## 4.2.1'))
    i1 = next((i for i, l in enumerate(lineas) if l.startswith('## Chuleta')), len(lineas))
    lineas = lineas[i0:i1]
    cuerpo, puestas, parrafo, tab = [], set(), [], []
    num = ['']

    def volcar_parrafo():
        if not parrafo: return
        figs = []
        texto = inline(' '.join(parrafo), figs)
        cuerpo.append(texto + '\n')
        for n in figs:
            if n not in puestas:
                cuerpo.append(figura(n)); puestas.add(n)
        cuerpo.append('')
        parrafo.clear()

    for l in lineas:
        if l.startswith('|'):
            volcar_parrafo(); tab.append(l); continue
        if tab:
            figs = []
            cuerpo.append(tabla(tab, figs)); cuerpo.append(''); tab.clear()
        if l.startswith('## '):
            volcar_parrafo()
            m = re.match(r'^## (4\.2\.\d+)\.\s*(.*)', l)
            num[0] = m.group(1) if m else ''
            titulo = m.group(2) if m else l[3:]
            cuerpo.append(r'\subsubsection{' + inline(titulo, []) + '}')
        elif l.startswith('> '):
            volcar_parrafo()
            q = l[2:].strip().strip('*')
            cuerpo.append(r'\begin{enunciadoborrador}{Enunciado de la cuestión ' + num[0] +
                          r' (solo en el borrador, no va en la memoria)}' + inline(q, []) +
                          r'\end{enunciadoborrador}')
        elif l.strip() in ('', '---'):
            volcar_parrafo()
        else:
            parrafo.append(l.strip())
    volcar_parrafo()
    if tab:
        cuerpo.append(tabla(tab, []))
    faltan = [n for n in PIES if n not in puestas]
    return '\n'.join(cuerpo), faltan


PLANTILLA = r'''% GENERADO por memoria/generar_borrador_orgB.py a partir de Preguntas_OrgB_OSPF.md.
% No editar a mano: se sobrescribe cada vez.
% Estilo: plantilla habitual del equipo (plantilla_memoria_UMU), adaptada a la guía de
% estilo de AR: Times New Roman 12, justificado, apartados numerados, número de página e
% identificación del documento y de los autores en la cabecera.
\documentclass[12pt,a4paper]{article}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish,es-tabla,es-noshorthands]{babel}
\usepackage{newtxtext}                % Times New Roman (guía de estilo de AR)
\usepackage[a4paper,top=2.5cm,bottom=2.5cm,left=2.5cm,right=2.5cm]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{float}
\usepackage{booktabs,tabularx}
\usepackage{caption}
\usepackage{enumitem}
\usepackage{xcolor}
\usepackage{needspace}
\usepackage[most]{tcolorbox}
\usepackage[colorlinks=true,linkcolor=black,citecolor=black,urlcolor=blue]{hyperref}

\setlength{\parindent}{0pt}
\setlength{\parskip}{0.6em}
\setlist[itemize]{label=\raisebox{0.15ex}{\scriptsize$\blacksquare$},leftmargin=1.5em,itemsep=0.3em}
\setlist[enumerate]{leftmargin=1.8em,itemsep=0.3em}

% ---------- Colores y recuadros de la plantilla ----------
\definecolor{umublue}{RGB}{0,0,153}
\definecolor{umuback}{RGB}{245,246,255}
\newtcolorbox{enunciado}[1]{enhanced,breakable,arc=3mm,colback=umuback,
  colframe=umublue,coltitle=white,fonttitle=\bfseries\large,title={#1},
  boxrule=0.6pt,before skip=1em,after skip=1em}
% Enunciado solo para el borrador (gris, para que se vea que no va en la memoria)
\newtcolorbox{enunciadoborrador}[1]{enhanced,breakable,arc=2mm,colback=black!3,
  colframe=black!30,colbacktitle=black!8,coltitle=black!60,fonttitle=\footnotesize\bfseries,
  fontupper=\small\itshape\color{black!70},title={#1},boxrule=0.4pt,before skip=0.6em,after skip=0.8em}

% ---------- Cabecera y pie: identificación del documento y número de página ----------
\usepackage{fancyhdr}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small\asignatura\ --- \titulo}
\fancyhead[R]{\small\autorespie}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0pt}
\setlength{\headheight}{15pt}

% ---------- Títulos de sección ----------
\usepackage{titlesec}
\titleformat{\section}{\normalfont\Large\bfseries}{\thesection.}{0.5em}{}
\titleformat{\subsection}{\normalfont\large\bfseries}{\thesubsection.}{0.5em}{}
\titleformat{\subsubsection}{\normalfont\normalsize\bfseries}{\thesubsubsection.}{0.5em}{}

% ---------- Marcador de contenido pendiente ----------
\newcommand{\pendiente}{\textbf{\textcolor{red}{[PENDIENTE]}}}

% ---------- Salidas de Packet Tracer ----------
\newcommand{\ciscoplacement}{H}
\input{salidas_cisco}

% ---------- Datos de la portada (fichero local, no se sube a GitHub) ----------
\newcommand{\autor}[3]{{\large\textbf{#1}}\par
  {\texttt{#2} - #3}\par\vspace{0.5em}}
\InputIfFileExists{datos_portada}{}{%
  \newcommand{\asignatura}{Arquitectura de Redes}\newcommand{\titulo}{Práctica final}
  \newcommand{\curso}{2026-2027}\newcommand{\grupo}{\pendiente}\newcommand{\profesor}{\pendiente}
  \newcommand{\fecha}{\today}\newcommand{\autores}{\pendiente}\newcommand{\autorespie}{}}

\begin{document}
\sloppy

% ------------------------- PORTADA -----------------------------------
\begin{titlepage}
  \centering
  \vspace*{0cm}
  \rule{\linewidth}{0.4pt}\par\vspace{0.4cm}
  {\fontsize{26}{30}\selectfont\bfseries \titulo}\par\vspace{0.3cm}
  {\large Memoria de la práctica}\par\vspace{0.4cm}
  \rule{\linewidth}{0.4pt}\par\vspace{0.2cm}

  \IfFileExists{logo_um_hd.jpeg}{\includegraphics[width=11.5cm]{logo_um_hd.jpeg}}%
    {\fbox{\parbox[c][5cm][c]{11.5cm}{\centering\color{black!50}[logo de la UM: copiar\\
      \texttt{logo\_um\_hd.jpeg} en la carpeta \texttt{memoria/}]}}}\par\vspace{0.6cm}

  \autores
  \vspace{0.2cm}

  {\asignatura\ --- Curso \curso}\par
  {Grado en Ingeniería Informática --- Universidad de Murcia}\par
  {Grupo de prácticas: \grupo\ --- Profesora: \profesor}\par\vspace{0.4cm}
  {\fecha}
\end{titlepage}

% ------------------------- INDICE ------------------------------------
\pagenumbering{roman}
\begin{center}\color{red}\bfseries BORRADOR: solo el apartado 4.2 (Organización B)\end{center}
\tableofcontents
\newpage
\pagenumbering{arabic}

% ------------------------- CONTENIDO ---------------------------------
\setcounter{section}{3}
\section{Encaminamiento intra-dominio IPv4}
\setcounter{subsection}{1}
\subsection{Organización B}
%%CUERPO%%
\end{document}
'''


def main():
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass
    md = open(MD, encoding='utf-8').read()
    cuerpo, faltan = convertir(md)
    tex = PLANTILLA.replace('%%CUERPO%%', cuerpo)
    ruta = os.path.join(AQUI, 'borrador_orgB.tex')
    with open(ruta, 'w', encoding='utf-8', newline='\n') as f:
        f.write(tex)
    print('-> memoria/borrador_orgB.tex')
    if faltan:
        print('Figuras con pie definido pero no citadas en el .md:', ', '.join(faltan))
    for _ in range(2):
        r = subprocess.run(['pdflatex', '-interaction=nonstopmode', 'borrador_orgB.tex'],
                           cwd=AQUI, capture_output=True, text=True, errors='replace')
    log = open(os.path.join(AQUI, 'borrador_orgB.log'), encoding='latin-1').read()
    errores = [l for l in log.splitlines() if l.startswith('!')]
    over = log.count('Overfull \\hbox')
    print('PDF: memoria/borrador_orgB.pdf' if not errores else 'ERRORES:\n' + '\n'.join(errores[:10]))
    if over: print(f'Aviso: {over} líneas se salen del margen')


if __name__ == '__main__':
    main()
