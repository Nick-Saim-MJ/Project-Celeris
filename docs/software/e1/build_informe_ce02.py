"""Genera el Entregable 1 de CE02 «Requerimientos y Diseño del Sistema» en DOCX y PDF.

    python docs/software/e1/build_informe_ce02.py [--pdf] [--salida DIR]

Estructura: la plantilla oficial (docs/fuentes/CE02/E1-plantilla-y-rubrica.md), título por título.

| Parte del informe | Texto |
| --- | --- |
| Portada | portada institucional UPeU (docs/infra/e1/portada-upeu.docx) + informe/portada.yaml + `equipo` del Marco común |
| Resumen ejecutivo | informe/00-resumen.md |
| Sección 0 | informe/05-seccion-0.md; supuestos y decisiones desde infra/trazabilidad.yaml |
| Sección 1 | informe/10-requerimientos.md, con {{incluir:…}} de srs/03…09-*.md (la matriz 1.12.2 pasa al Anexo B) |
| Sección 2 | informe/20-prototipo.md + prototipo/png/ |
| Sección 3 | informe/30-arquitectura.md, con {{incluir:…}} de arquitectura/seccion-3.md + DS-20…DS-22 |
| Sección 4 | informe/40-diseno-detallado.md + diagramas/png/ |
| Anexos | informe/A…D-*.md; la matriz del Anexo B se arma aquí desde el SRS, los ADR y la tabla de B-trazabilidad.md |

El generador falla si la matriz no cuadra: requisitos del SRS ≠ requisitos de la tabla de componentes, componente de
DS-13/DS-22 sin requisito o pantalla sin requisito. `--pdf` abre el DOCX en Microsoft Word (COM), actualiza el índice,
exporta el PDF y deja en informe/paginas.json el número de páginas y la página de cada título.
"""
from __future__ import annotations

import argparse
import copy
import io
import json
import re
import sys
import tempfile
from pathlib import Path

import yaml
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ / "docs" / "infra" / "e1"))
from build_informe import (  # noqa: E402
    COLOR_CABECERA, PORTADA, _borde, _espaciado, _run_fmt, _sombra, _word, commit_fuente, equipo, equipo_lista,
    png_reducido, texto_inline,
)

INFORME = AQUI / "informe"
SRS = AQUI / "srs"
ARQ = AQUI / "arquitectura"
DIAG = AQUI / "diagramas"
PROTO = AQUI / "prototipo"
CE02 = RAIZ / "docs" / "celeris" / "Celeris-CE02-Ingenieria-Software.md"
SALIDA = RAIZ / "entregables" / "CE02"
PAGINAS_JSON = INFORME / "paginas.json"

TAM = 10
TAM_TABLA = 8
ANCHO_V = 17.0           # cm útiles en vertical (A4, márgenes de 2 cm)
ANCHO_H = 25.7           # cm útiles en horizontal
ALTO_FIG = 10.0         # alto máximo de un diagrama en página vertical
ALTO_PAR = 5.6          # alto máximo de cada diagrama de un par (casos de uso | clases)
A4 = (11906, 16838)      # twips
ESC = ""           # marcador de «\*» (asterisco literal)
COMPLETAR = "[COMPLETAR"

# ==================================================================================================
# Fuentes y datos
# ==================================================================================================
def leer(p: Path) -> list[str]:
    return p.read_text(encoding="utf-8").splitlines()


def celdas(linea: str) -> list[str]:
    return [c.strip() for c in linea.strip().strip("|").split("|")]


def tabla_tras(lineas: list[str], titulo: str) -> list[list[str]]:
    """Filas (sin cabecera ni separador) de la primera tabla después del título dado."""
    i = next(k for k, l in enumerate(lineas) if l.strip() == titulo)
    filas, dentro = [], False
    for l in lineas[i + 1:]:
        if l.startswith("|"):
            dentro = True
            if not re.fullmatch(r"\|[\s:|-]+\|", l.strip()):
                filas.append(celdas(l))
        elif dentro:
            break
    return filas[1:]


def matriz_srs() -> list[list[str]]:
    return tabla_tras(leer(SRS / "08-verificacion-trazabilidad.md"), "### 1.12.2 Matriz de trazabilidad")


def comp_infra() -> dict[str, tuple[str, str]]:
    f = tabla_tras(leer(INFORME / "B-trazabilidad.md"), "## Componente e infraestructura por requisito")
    return {r[0]: (r[1], r[2]) for r in f}


def expandir_ids(texto: str) -> set[str]:
    """«REQ-F-31, RN-03, F-37» → {REQ-F-31, REQ-RN-03, REQ-F-37}."""
    return {f"REQ-{m.group(1)}-{m.group(2)}" for m in re.finditer(r"(?<![A-Z])(?:REQ-)?(F|NF|RN)-(\d{2})\b", texto)}


def adr_por_req() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for f in sorted((ARQ / "adr").glob("D-*.md")):
        lineas = leer(f)
        k = lineas.index("## Enlaces")
        enlaces = " ".join(l for l in lineas[k + 1:] if l.strip())
        for r in expandir_ids(enlaces):
            out.setdefault(r, []).append(f.name[:4])
    return out


def componentes_disenados() -> set[str]:
    nodo = re.findall(r"^\s*\[([a-z.]+)\\n", (DIAG / "src" / "DS-13-componentes-codigo.puml").read_text(encoding="utf-8"), re.M)
    consola = re.findall(r'Component(?:Db)?\(\w+, "([a-z]+)', (DIAG / "src" / "DS-22-c4-componentes-consola.puml").read_text(encoding="utf-8"))
    consola = [c for c in consola if c != "router"] + ["router"]
    return {f"node.{c}" for c in nodo} | {f"console.{c}" for c in consola if c != "postgresql"}


def rango_p(texto: str) -> set[str]:
    out = set()
    for a, b in re.findall(r"P-(\d{2})…P-(\d{2})", texto):
        out |= {f"P-{n:02d}" for n in range(int(a), int(b) + 1)}
    out |= set(re.findall(r"P-\d{2}", texto))
    return out


def estados() -> dict[str, int]:
    c = {"Hecho": 0, "Parcial": 0, "Pendiente": 0}
    for f in ("03-requisitos-funcionales.md", "05-reglas-restricciones.md"):
        cab = None
        for l in leer(SRS / f):
            if l.startswith("|") and not l.startswith("| REQ-") and not re.fullmatch(r"\|[\s:|-]+\|", l.strip()):
                cab = celdas(l)
            elif l.startswith("| REQ-") and cab and "Estado" in cab:
                e = celdas(l)[cab.index("Estado")]
                k = next((k for k in c if e.startswith(k)), None)
                if k is None:
                    raise SystemExit(f"estado sin clasificar en {f}: {e}")
                c[k] += 1
    return c


def fecha_ce02() -> str:
    m = re.search(r'^fecha:\s*"(\d{4})-(\d{2})-(\d{2})"', CE02.read_text(encoding="utf-8"), re.M)
    meses = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()
    return f"{int(m.group(3))} de {meses[int(m.group(2)) - 1]} de {m.group(1)}"


def datos() -> dict[str, str]:
    m = matriz_srs()
    reqs = [r[0] for r in m]
    e = estados()
    cu = {c for l in leer(SRS / "06-casos-de-uso.md") for c in re.findall(r"^\| (CU-\d{2}) ", l)}
    nombres = equipo_lista()
    return {
        "equipo": equipo(), "autor1": nombres[0], "autor2": nombres[-1],
        "n_req": str(len(reqs)),
        "n_rf": str(sum(r.startswith("REQ-F-") for r in reqs)),
        "n_rnf": str(sum(r.startswith("REQ-NF-") for r in reqs)),
        "n_rn": str(sum(r.startswith("REQ-RN-") for r in reqs)),
        "n_rf_rn": str(sum(e.values())), "n_hecho": str(e["Hecho"]), "n_parcial": str(e["Parcial"]),
        "n_pendiente": str(e["Pendiente"]),
        "n_cu": str(len(cu)),
        "n_pantallas": str(len(list((PROTO / "png").glob("P-*.png")))),
        "n_adr": str(len(list((ARQ / "adr").glob("D-*.md")))),
        "n_sup": str(sum(1 for v in _traz()["supuestos"].values() if v.get("estado") != "retirado")),
        "n_dec": str(len(_traz()["decisiones"])),
        "n_uml": str(sum(1 for p in (DIAG / "src").glob("DS-*.puml") if not 20 <= int(p.name[3:5]) <= 22)),
    }


TRAZ = RAIZ / "infra" / "trazabilidad.yaml"
# Decisiones de infraestructura: se detallan en el informe de CE03 (D3), no en este.
DEC_INFRA = {"D-15", "D-16", "D-17", "D-18", "D-19", "D-23", "D-26", "D-28", "D-29"}


def _traz() -> dict:
    return yaml.safe_load(TRAZ.read_text(encoding="utf-8"))


def tabla_supuestos() -> list[list[str]]:
    """Sección 0.2: supuestos vigentes de infra/trazabilidad.yaml + qué condicionan (SRS 1.6.5)."""
    plan: dict[str, str] = {}
    for f in tabla_tras(leer(SRS / "02-descripcion-general.md"), "### 1.6.5 Supuestos y dependencias"):
        for sid in re.findall(r"\[(S-\d{2})\]", f[0]):
            plan[sid] = f"{f[1]}. Si no se cumple: {f[2][0].lower()}{f[2][1:]}"
    filas = [["ID", "Supuesto", "Valor usado en el diseño", "Qué condiciona y qué pasa si no se cumple"]]
    for sid, v in sorted(_traz()["supuestos"].items()):
        if v.get("estado") == "retirado":
            continue
        filas.append([sid, v["supuesto"], v["valor"], plan.get(sid, "No condiciona al software")])
    return filas


def tabla_decisiones() -> list[list[str]]:
    """Sección 0.3: las 29 decisiones de infra/trazabilidad.yaml, con su ámbito y dónde se detallan."""
    con_adr = {f.name[:4] for f in (ARQ / "adr").glob("D-*.md")}
    no_vigentes = {r[0]: r[2] for r in tabla_tras(leer(ARQ / "seccion-3.md"), "### Decisiones que no se mantienen")}
    filas = [["ID", "Decisión", "Ámbito", "Situación y dónde se detalla"]]
    for did, v in sorted(_traz()["decisiones"].items()):
        texto = re.sub(r"\s*\(CI-\d+\)", "", v["decision"])
        if did in con_adr:
            filas.append([did, texto, "Software", "Vigente · ADR en 3.2"])
        elif did in DEC_INFRA:
            filas.append([did, texto, "Infraestructura", "Vigente · informe CE03 (D3)"])
        elif did in no_vigentes:
            filas.append([did, texto, "Software", f"No se mantiene: {no_vigentes[did]}"])
        else:
            raise SystemExit(f"Sección 0: {did} no tiene ADR, ni es de infraestructura, ni figura como no vigente")
    return filas


def tabla_gherkin() -> list[list[str]]:
    """Sección 1.6: un renglón por escenario Gherkin del SRS (1.10.4): característica, escenario, requisitos y
    resultado esperado (las líneas «Entonces» y las «Y» que la siguen)."""
    lineas = leer(SRS / "06-casos-de-uso.md")
    i = lineas.index("### 1.10.4 Criterios de aceptación ejecutables (Gherkin)")
    filas = [["Característica", "Escenario", "Requisitos", "Resultado esperado"]]
    req = car = ""
    esc = None
    en_entonces = False
    for l in lineas[i + 1:]:
        t = l.strip()
        if t.startswith("#") and ".feature" in t:
            req = ", ".join(x.removeprefix("@") for x in re.findall(r"@REQ-[A-Z]+-\d{2}", t))
        elif t.startswith("Característica:"):
            car = t.split(":", 1)[1].strip()
        elif t.startswith("Escenario:"):
            esc = [car, t.split(":", 1)[1].strip(), req, ""]
            filas.append(esc)
            en_entonces = False
        elif esc is not None and t.startswith("Entonces "):
            esc[3] = t.removeprefix("Entonces ").strip()
            en_entonces = True
        elif esc is not None and en_entonces and t.startswith("Y "):
            esc[3] += "; " + t.removeprefix("Y ").strip()
        elif t.startswith(("## ", "### ")):
            break
    previo = None
    for f in filas[1:]:
        f[3] = f[3][0].upper() + f[3][1:]
        if f[0] == previo:              # la característica y sus etiquetas se escriben una vez
            f[0] = f[2] = ""
        else:
            previo = f[0]
    return filas


TABLAS = {"supuestos": tabla_supuestos, "decisiones": tabla_decisiones, "gherkin": tabla_gherkin}


def tabla_matriz() -> tuple[list[str], list[list[str]], list[float]]:
    m, ci, adr = matriz_srs(), comp_infra(), adr_por_req()
    reqs = [r[0] for r in m]
    if set(reqs) != set(ci) or len(reqs) != len(ci):
        raise SystemExit(f"Anexo B: el SRS y la tabla de componentes no tienen los mismos requisitos: "
                         f"{sorted(set(reqs) ^ set(ci))}")
    usados = {c.strip(" `") for v in ci.values() for c in v[0].split(",")}
    faltan = componentes_disenados() - usados
    if faltan:
        raise SystemExit(f"Anexo B: componentes de DS-13/DS-22 sin requisito: {sorted(faltan)}")
    pantallas = set().union(*(rango_p(r[3]) for r in m))
    todas = {p.name[:4] for p in (PROTO / "png").glob("P-*.png")}
    if todas - pantallas:
        raise SystemExit(f"Anexo B: pantallas sin requisito: {sorted(todas - pantallas)}")
    cab = ["Requisito", "OB", "CU", "Pantalla", "Componente (C3)", "ADR", "UML", "Prueba (método)", "Infraestructura (CE03)"]
    filas = []
    for r in m:
        req, ob, cu, p, uml, ver, met = r
        filas.append([req, ob, cu, p, ci[req][0], ", ".join(sorted(adr.get(req, []))) or "—", uml, f"{ver} ({met})", ci[req][1]])
    return cab, filas, [1.9, 1.7, 1.7, 1.6, 3.6, 1.6, 1.8, 3.6, 4.2]


# ==================================================================================================
# Markdown → bloques
# ==================================================================================================
# Referencias internas del SRS → numeración de este informe (solo en el texto incluido).
REF_SRS = [
    (r"(?<![\d.])(?:§|sección |secciones )?1\.13\.[12]\b", "Anexo B"),
    (r"(?<![\d.])(?:§|sección )?1\.13\.[3-5]\b", "Anexo B"),
    (r"(?<![\d.])(?:§|sección )?1\.12(?:\.\d)?\b", "Anexo B"),
    (r"(?<![\d.])(?:§|sección )?1\.11\.[34]\b", "Sección 4.4"),
    (r"(?<![\d.])(?:§|sección )?1\.10\.4\b", "1.6"),
    (r"(?<![\d.])(?:§|sección )?1\.10(?:\.\d)?\b", "1.5"),
    (r"(?<![\d.])(?:§|sección )?1\.9\.1\b", "1.3"),
    (r"(?<![\d.])(?:§|sección )?1\.9\.2\b", "1.4"),
    (r"(?<![\d.])(?:§|sección )?1\.7\.3\b", "1.1.3"),
]


def cuerpo_srs(archivo: str, titulo: str, modo: str = "") -> list[str]:
    """Líneas bajo `titulo` en `archivo` (relativo a docs/software/e1) hasta el siguiente título, respetando los bloques
    de código. modo «tabla»: solo la primera tabla; «sin_intro»: sin los párrafos que preceden al primer bloque."""
    lineas = leer(AQUI / archivo)
    if titulo not in lineas:
        raise SystemExit(f"{{{{incluir}}}}: no existe «{titulo}» en {archivo}")
    i = lineas.index(titulo) + 1
    out, codigo = [], False
    for l in lineas[i:]:
        if l.startswith("```"):
            codigo = not codigo
        elif not codigo and re.match(r"^#{1,4} ", l):
            break
        out.append(l)
    if modo == "tabla":
        a = next(k for k, l in enumerate(out) if l.startswith("|"))
        b = next((k for k in range(a, len(out)) if not out[k].startswith("|")), len(out))
        out = out[a:b]
    elif modo == "sin_intro":
        a = next(k for k, l in enumerate(out) if l.startswith(("**", "```", "|", "- ")))
        out = out[a:]
    texto = "\n".join(out)
    for patron, nuevo in REF_SRS:
        texto = re.sub(patron, nuevo, texto)
    return texto.split("\n") + [""]


def expandir(lineas: list[str]) -> list[str]:
    out = []
    for l in lineas:
        m = re.fullmatch(r"\{\{incluir:([^|]+)\|([^|]+?)(?:\|(\w+))?\}\}", l.strip())
        out += cuerpo_srs(m.group(1), m.group(2), m.group(3) or "") if m else [l]
    return out


def bloques(lineas: list[str]) -> list[tuple]:
    out: list[tuple] = []
    buf: list[str] = []
    tabla: list[str] = []
    i = 0

    def cerrar():
        if buf:
            out.append(("p", " ".join(s.strip() for s in buf)))
            buf.clear()
        if tabla:
            filas = [celdas(l) for l in tabla if not re.fullmatch(r"\|[\s:|-]+\|", l.strip())]
            out.append(("tabla", filas))
            tabla.clear()

    while i < len(lineas):
        s = lineas[i].rstrip()
        i += 1
        if s.startswith("```"):
            cerrar()
            codigo = []
            while i < len(lineas) and not lineas[i].startswith("```"):
                codigo.append(lineas[i].rstrip())
                i += 1
            i += 1
            out.append(("code", codigo))
            continue
        if not s.strip():
            cerrar()
            continue
        if s.startswith("|"):
            if buf:
                cerrar()
            tabla.append(s)
            continue
        if tabla:
            cerrar()
        m = re.match(r"^(#{1,4}) (.+)$", s)
        lista = re.match(r"^( *)(- |\d+\. )(.*)$", s)
        if m:
            cerrar()
            out.append((f"h{len(m.group(1))}", m.group(2).strip()))
        elif lista:
            cerrar()
            nivel = len(lista.group(1)) // 2
            out.append(("li" if lista.group(2) == "- " else "num", nivel, lista.group(3).strip(),
                        lista.group(2).strip()))
        elif s.startswith(" ") and out and out[-1][0] in ("li", "num") and not buf:
            t = out[-1]
            out[-1] = (t[0], t[1], t[2] + " " + s.strip(), t[3])
        elif s.startswith("> "):
            cerrar()
            if out and out[-1][0] == "nota" and lineas[i - 2].startswith(">"):
                out[-1] = ("nota", out[-1][1] + " " + s[2:].strip())
            else:
                out.append(("nota", s[2:].strip()))
        elif mm := re.fullmatch(r"\{\{(figura|figura_prototipo|rejilla|tabla|par_uml):(.+)\}\}", s.strip()):
            cerrar()
            out.append((mm.group(1), mm.group(2)))
        else:
            buf.append(s)
    cerrar()
    return out


# ==================================================================================================
# Documento
# ==================================================================================================
class Informe:
    def __init__(self):
        self.d = datos()
        self.portada_cfg = yaml.safe_load((INFORME / "portada.yaml").read_text(encoding="utf-8"))
        self.doc = Document(str(PORTADA))
        self.cuerpo = self.doc.element.body
        # La portada trae encabezados de CE03 («Diseño de Red — …»): se quitan del sectPr final, que es la base de todos.
        for ref in self.cuerpo[-1].findall(qn("w:headerReference")) + self.cuerpo[-1].findall(qn("w:footerReference")):
            self.cuerpo[-1].remove(ref)
        self.sect_base = copy.deepcopy(self.cuerpo[-1])
        self.horizontal = False
        self.n_fig = 0
        self.figuras: list[str] = []
        self.completar: list[str] = []
        self._estilos()

    # ------------------------------------------------------------------ estilos
    def _estilos(self):
        st = self.doc.styles
        st["Normal"].font.name = "Calibri"
        st["Normal"].font.size = Pt(TAM)
        rpr = st.element.find(qn("w:docDefaults") + "/" + qn("w:rPrDefault") + "/" + qn("w:rPr"))
        if rpr is not None:
            f = rpr.find(qn("w:rFonts"))
            if f is None:
                f = OxmlElement("w:rFonts")
                rpr.insert(0, f)
            for a in ("w:ascii", "w:hAnsi", "w:cs"):
                f.set(qn(a), "Calibri")
            for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme"):
                f.attrib.pop(qn(a), None)
        for nombre, tam in (("toc 1", 9.5), ("toc 2", 8.5)):    # índice en una página
            if nombre in [s.name for s in st]:
                t = st[nombre]
                t.font.size = Pt(tam)
                t.paragraph_format.space_before = Pt(1 if nombre == "toc 1" else 0)
                t.paragraph_format.space_after = Pt(0)
                t.paragraph_format.line_spacing = 1.0
        for nombre, tam, antes, despues in (("Heading 1", 15, 0, 8), ("Heading 2", 12.5, 12, 4), ("Heading 3", 11, 8, 3)):
            h = st[nombre]
            h.font.name = "Calibri"
            h.font.size = Pt(tam)
            h.font.bold = True
            h.font.color.rgb = RGBColor.from_string(COLOR_CABECERA)
            h.paragraph_format.space_before = Pt(antes)
            h.paragraph_format.space_after = Pt(despues)
            h.paragraph_format.keep_with_next = True
            rf = h.element.get_or_add_rPr().find(qn("w:rFonts"))
            if rf is not None:
                for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
                    rf.attrib.pop(qn(a), None)
                for a in ("w:ascii", "w:hAnsi", "w:cs"):
                    rf.set(qn(a), "Calibri")

    # ------------------------------------------------------------------ texto
    def sustituir(self, t: str) -> str:
        def dato(m):
            if m.group(1) not in self.d:
                raise SystemExit(f"{{{{dato:{m.group(1)}}}}} no existe")
            return self.d[m.group(1)]
        t = re.sub(r"\{\{dato:([a-z0-9_]+)\}\}", dato, t).replace("\\*", ESC)
        if COMPLETAR in t:
            self.completar += re.findall(r"\[COMPLETAR[^\]]*\]", t)
        return t

    def _inline(self, p, texto, tam=TAM, negrita=False, cursiva=False, color=None):
        texto_inline(p, self.sustituir(texto), tam, negrita, cursiva, color)
        for r in p.runs:
            if ESC in r.text:
                r.text = r.text.replace(ESC, "*")

    def parrafo(self, texto="", tam=TAM, despues=4, antes=0, alinear=None, **kw):
        p = self.doc.add_paragraph()
        if texto:
            self._inline(p, texto, tam, **kw)
        p.paragraph_format.space_before = Pt(antes)
        p.paragraph_format.space_after = Pt(despues)
        if alinear is not None:
            p.alignment = alinear
        return p

    def titulo(self, texto, nivel, salto=False):
        if salto:
            # el párrafo vacío que cierra una tabla al pie de página no debe abrir él solo una página en blanco
            ult = [e for e in self.cuerpo.iterchildren() if e.tag != qn("w:sectPr")][-1]
            if ult.tag == qn("w:p") and not "".join(ult.xpath(".//w:t/text()")).strip()                     and not ult.xpath(".//w:drawing|.//w:sectPr"):
                self.cuerpo.remove(ult)
        p = self.doc.add_paragraph(style=f"Heading {nivel}")
        self._inline(p, texto, {1: 15, 2: 12.5, 3: 11}[nivel], negrita=True, color=COLOR_CABECERA)
        if salto:
            p.paragraph_format.page_break_before = True
        return p

    def lista(self, texto, nivel, marca):
        p = self.doc.add_paragraph()
        sangria = 0.6 + 0.6 * nivel
        p.paragraph_format.left_indent = Cm(sangria)
        p.paragraph_format.first_line_indent = Cm(-0.45)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(sangria))
        signo = ("•", "–", "·")[min(nivel, 2)] if marca == "-" else marca
        _run_fmt(p.add_run(signo + "\t"), TAM)
        self._inline(p, texto)

    def nota(self, texto):
        p = self.parrafo(texto, despues=8, antes=4, color="1F3864")
        ppr = p._p.get_or_add_pPr()
        bdr = OxmlElement("w:pBdr")
        izq = OxmlElement("w:left")
        for k, v in (("w:val", "single"), ("w:sz", "18"), ("w:space", "8"), ("w:color", "2E74B5")):
            izq.set(qn(k), v)
        bdr.append(izq)
        ppr.append(bdr)
        p.paragraph_format.left_indent = Cm(0.4)

    def codigo(self, lineas):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.left_indent = Cm(0.3)
        shd = OxmlElement("w:shd")
        for k, v in (("w:val", "clear"), ("w:color", "auto"), ("w:fill", "F2F2F2")):
            shd.set(qn(k), v)
        p._p.get_or_add_pPr().append(shd)
        for k, l in enumerate(lineas):
            r = p.add_run(l)
            _run_fmt(r, 7.5, mono=True)
            if k < len(lineas) - 1:
                r.add_break()

    def tabla(self, filas, anchos=None, ancho_total=None, tam=TAM_TABLA):
        ancho_total = ancho_total or (ANCHO_H if self.horizontal else ANCHO_V)
        n = len(filas[0])
        if anchos is None:
            def texto(f, j):
                return re.sub(r"[*`]", "", self.sustituir(f[j])) if j < len(f) else ""
            antes = len(self.completar)
            largo = [sum(len(texto(f, j)) for f in filas[1:]) / max(len(filas) - 1, 1) for j in range(n)]
            # mínimo: que la palabra más larga de la columna (un ID, una cabecera) no se parta; tope de 2,6 cm
            minimo = [min(2.6, max(len(w) for f in filas for w in (texto(f, j).split() or [""])) * tam * 0.0205 + 0.3)
                      for j in range(n)]
            del self.completar[antes:]
            peso = [max(l, 1) ** 0.9 for l in largo]
            libre = max(ancho_total - sum(minimo), 0)
            anchos = [m + libre * p / sum(peso) for m, p in zip(minimo, peso)]
        tw = [int(a / sum(anchos) * ancho_total * 567) for a in anchos]
        t = self.doc.add_table(rows=len(filas), cols=n)
        tblpr = t._tbl.tblPr
        w = OxmlElement("w:tblW")
        w.set(qn("w:w"), str(sum(tw)))
        w.set(qn("w:type"), "dxa")
        tblpr.append(w)
        lay = OxmlElement("w:tblLayout")
        lay.set(qn("w:type"), "fixed")
        tblpr.append(lay)
        mar = OxmlElement("w:tblCellMar")
        for lado in ("top", "left", "bottom", "right"):
            e = OxmlElement(f"w:{lado}")
            e.set(qn("w:w"), "30" if lado in ("top", "bottom") else "70")
            e.set(qn("w:type"), "dxa")
            mar.append(e)
        tblpr.append(mar)
        for gc, ww in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), tw):
            gc.set(qn("w:w"), str(ww))
        for i, fila in enumerate(filas):
            row = t.rows[i]
            trpr = row._tr.get_or_add_trPr()
            if i == 0:
                h = OxmlElement("w:tblHeader")
                h.set(qn("w:val"), "true")
                trpr.append(h)
            trpr.append(OxmlElement("w:cantSplit"))
            for j in range(n):
                cel = row.cells[j]
                tcpr = cel._tc.get_or_add_tcPr()
                tcw = OxmlElement("w:tcW")
                tcw.set(qn("w:w"), str(tw[j]))
                tcw.set(qn("w:type"), "dxa")
                tcpr.append(tcw)
                _borde(tcpr)
                if i == 0:
                    _sombra(tcpr, COLOR_CABECERA)
                elif i % 2 == 0:
                    _sombra(tcpr, "F2F5FA")
                p = cel.paragraphs[0]
                _espaciado(p, 0, 0)
                self._inline(p, fila[j] if j < len(fila) else "", tam, negrita=(i == 0),
                             color="FFFFFF" if i == 0 else None)
        self.parrafo("", despues=2, tam=4)

    # ------------------------------------------------------------------ figuras
    def _imagen(self, png: Path, ancho_cm: float, p=None):
        p = p or self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_after = Pt(2)
        p.add_run().add_picture(str(png_reducido(png, ancho_cm)), width=Cm(ancho_cm))
        return p

    def _pie(self, texto, observar=None):
        self.n_fig += 1
        pie = self.parrafo(f"Figura {self.n_fig}. {texto}", tam=9, despues=2, cursiva=True, color="595959",
                           alinear=WD_ALIGN_PARAGRAPH.CENTER)
        if observar:
            pie.paragraph_format.keep_with_next = True
            self.parrafo(f"**Qué observar.** {observar}", tam=9.5, despues=10)

    def figura(self, arg: str):
        fid, observar = arg.split("|", 1)
        fid, _, escala = fid.partition("@")  # DS-xx@0.9 reduce el ancho
        png = next((DIAG / "png").glob(f"{fid}-*.png"))
        puml = next((DIAG / "src").glob(f"{fid}-*.puml")).read_text(encoding="utf-8")
        titulo = re.search(r"^title (.+)$", puml, re.M).group(1)
        titulo = re.sub(r"\s*\(CE02 C[\d.]+[^)]*\)|\s*\(C\d\.\d[^)]*\)", "", titulo).replace(" · ", ". ", 1)
        from PIL import Image
        with Image.open(png) as im:
            ratio = im.size[0] / im.size[1]
        ancho_max = ANCHO_H if self.horizontal else ANCHO_V
        self._imagen(png, min(ancho_max, ALTO_FIG * ratio) * float(escala or 1))
        self._pie(titulo, observar)
        self.figuras.append(fid)

    def _titulo_ds(self, fid: str) -> str:
        puml = next((DIAG / "src").glob(f"{fid}-*.puml")).read_text(encoding="utf-8")
        titulo = re.search(r"^title (.+)$", puml, re.M).group(1)
        return re.sub(r"\s*\(CE02 C[\d.]+[^)]*\)|\s*\(C\d\.\d[^)]*\)", "", titulo).replace(" · ", ". ", 1)

    def par_uml(self, arg: str):
        """Dos diagramas de un mismo caso de uso, lado a lado (casos de uso | clases), y una línea «Qué observar»."""
        izq, der, observar = arg.split("|", 2)
        from PIL import Image
        t = self.doc.add_table(rows=1, cols=2)
        t._tbl.tblPr.append(OxmlElement("w:jc"))
        t._tbl.tblPr[-1].set(qn("w:val"), "center")
        t.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for j, fid in enumerate((izq, der)):
            png = next((DIAG / "png").glob(f"{fid}-*.png"))
            with Image.open(png) as im:
                ratio = im.size[0] / im.size[1]
            cel = t.rows[0].cells[j]
            cel.width = Cm(ANCHO_V / 2)
            va = OxmlElement("w:vAlign")             # pies de figura alineados abajo en ambas columnas
            va.set(qn("w:val"), "bottom")
            cel._tc.get_or_add_tcPr().append(va)
            self._imagen(png, min(ANCHO_V / 2 - 0.3, ALTO_PAR * ratio), cel.paragraphs[0])
            self.n_fig += 1
            q = cel.add_paragraph()
            q.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _espaciado(q, 0, 2)
            self._inline(q, f"Figura {self.n_fig}. {self._titulo_ds(fid)}", 8.5, cursiva=True, color="595959")
            self.figuras.append(fid)
        cu = re.search(r"CU-\d{2}", self._titulo_ds(izq)).group(0)
        self.parrafo(f"**Qué observar ({cu}).** {observar[0].upper()}{observar[1:]}", tam=9, despues=8)

    def figura_prototipo(self, arg: str):
        nombre, leyenda, observar = arg.split("|", 2)
        self._imagen(PROTO / "png" / f"{nombre}.png", ANCHO_V)
        self._pie(leyenda, observar)
        self.figuras.append(nombre)

    def rejilla(self, arg: str):
        nombres = arg.split("|")
        md = {r[0]: r[1] for r in tabla_tras(leer(PROTO / "pantallas.md"), "## Pantallas")}
        filas = [nombres[k:k + 3] for k in range(0, len(nombres), 3)]
        t = self.doc.add_table(rows=len(filas), cols=3)
        for i, par in enumerate(filas):
            t.rows[i]._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
            for j, nombre in enumerate(par):
                cel = t.rows[i].cells[j]
                p = cel.paragraphs[0]
                self._imagen(PROTO / "png" / f"{nombre}.png", 5.5, p).paragraph_format.keep_with_next = False
                pid = nombre[:4]
                self.n_fig += 1
                q = cel.add_paragraph()
                q.alignment = WD_ALIGN_PARAGRAPH.CENTER
                _espaciado(q, 0, 100)
                self._inline(q, f"Figura {self.n_fig}. {pid} · {md[pid]}", 8.5, cursiva=True, color="595959")
                self.figuras.append(pid)
        self.parrafo("", despues=4, tam=4)

    # ------------------------------------------------------------------ secciones de página
    def seccion(self, horizontal: bool):
        """Cierra la sección en curso (el sectPr va en el último párrafo y describe las páginas anteriores)."""
        if horizontal == self.horizontal:
            return
        p = self.doc.add_paragraph()
        _espaciado(p, 0, 0)
        p._p.get_or_add_pPr().append(self._sect(self.horizontal))
        self.horizontal = horizontal

    def _sect(self, horizontal: bool):
        s = copy.deepcopy(self.sect_base)
        for ref in s.findall(qn("w:headerReference")) + s.findall(qn("w:footerReference")):
            s.remove(ref)
        pg = s.find(qn("w:pgSz"))
        pg.set(qn("w:w"), str(A4[1] if horizontal else A4[0]))
        pg.set(qn("w:h"), str(A4[0] if horizontal else A4[1]))
        if horizontal:
            pg.set(qn("w:orient"), "landscape")
        else:
            pg.attrib.pop(qn("w:orient"), None)
        tipo = s.find(qn("w:type"))
        if tipo is None:
            tipo = OxmlElement("w:type")
            s.insert(0, tipo)
        tipo.set(qn("w:val"), "nextPage")
        return s

    # ------------------------------------------------------------------ render
    @staticmethod
    def _unir_listas_cortas(bl):
        """Una lista de viñetas de nivel 0 cuyos elementos son todos de ≤ 4 palabras se escribe en una línea
        («a, b, c y d»): en el Word una palabra por renglón gasta media página."""
        out, k = [], 0
        while k < len(bl):
            j = k
            while j < len(bl) and bl[j][0] == "li" and bl[j][1] == 0:
                j += 1
            grupo = bl[k:j]
            if len(grupo) >= 3 and all(len(g[2].rstrip(";.").split()) <= 6 for g in grupo):
                items = [g[2].rstrip(";.").removesuffix(" y").strip() for g in grupo]
                items[-1] = items[-1].removeprefix("y ").strip()
                out.append(("p", ", ".join(items[:-1]) + " y " + items[-1] + "."))
                k = j
            elif grupo:
                out += grupo
                k = j
            else:
                out.append(bl[k])
                k += 1
        return out

    def render(self, bl, salto_h1=True):
        previo = None
        for b in self._unir_listas_cortas(bl):
            t = b[0]
            if t in ("h1", "h2", "h3", "h4"):
                nivel = min(int(t[1]), 3)
                # Cada sección de la plantilla y cada anexo (salvo el que sigue al título «Anexos») abre página.
                salto = salto_h1 and (nivel == 1 or (nivel == 2 and b[1].startswith("Anexo ") and previo != "h1"))
                self.titulo(b[1], nivel, salto=salto)
            elif t == "p":
                self.parrafo(b[1])
            elif t in ("li", "num"):
                self.lista(b[2], b[1], "-" if t == "li" else b[3])
            elif t == "nota":
                self.nota(b[1])
            elif t == "code":
                self.codigo(b[1])
            elif t == "tabla" and isinstance(b[1], str):
                self.tabla(TABLAS[b[1]](), tam=7.5)           # tablas generadas desde infra/trazabilidad.yaml
            elif t == "tabla":
                self.tabla(b[1], tam=7.5 if len(b[1][0]) >= 6 else TAM_TABLA)  # tablas anchas, letra menor
            elif t == "par_uml":
                self.par_uml(b[1])
            elif t == "figura":
                self.figura(b[1])
            elif t == "figura_prototipo":
                self.figura_prototipo(b[1])
            elif t == "rejilla":
                self.rejilla(b[1])
            previo = t

    # ------------------------------------------------------------------ partes
    def portada(self):
        cfg = self.portada_cfg
        hijos = [e for e in self.cuerpo.iterchildren() if e.tag != qn("w:sectPr")]

        def vacio(e):
            return not "".join(e.xpath(".//w:t/text()")).strip() and not e.xpath(".//w:drawing")
        while hijos and vacio(hijos[-1]):
            self.cuerpo.remove(hijos.pop())
        par = [Paragraph(e, self.doc._body) for e in hijos if e.tag == qn("w:p")]
        textos = [p.text.strip() for p in par]

        def poner(p, texto):
            p.runs[0].text = texto
            for r in p.runs[1:]:
                r._r.getparent().remove(r._r)

        def idx(prefijo):
            return next(k for k, t in enumerate(textos) if t.startswith(prefijo))
        # Plantilla CE02: título del sistema, nombre del estudiante, semestre y fecha (nada más).
        titulo = par[idx("Análisis y Diseño de Red")]
        poner(titulo, cfg["titulo"])
        for r in titulo.runs:
            r.font.size = Pt(20)
            r.font.bold = True
            r.font.color.rgb = RGBColor.from_string(COLOR_CABECERA)
        poner(par[idx("Proyecto Fin de Carrera")], cfg["entregable"])
        poner(par[idx("On-Premise")], cfg["curso"])
        for k in (idx("ÁREA"), idx("ÁREA") + 1, idx("SGSI")):
            par[k]._p.getparent().remove(par[k]._p)
        poner(par[idx("RESPONSABLES")], "ESTUDIANTES:")
        j = idx("RESPONSABLES")
        nombres = equipo_lista()
        existentes = [k for k in range(j + 1, len(par)) if textos[k] and not textos[k].startswith(("SGSI", "Juliaca"))][:len(nombres)]
        if len(existentes) < len(nombres):
            raise SystemExit("la portada tiene menos líneas de estudiantes que autores")
        for k, nombre in zip(existentes, nombres):
            poner(par[k], nombre)
        k = idx("Juliaca")
        poner(par[k], self.sustituir(f"Fecha: {fecha_ce02()}"))
        nuevo = copy.deepcopy(par[k]._p)
        par[k]._p.addprevious(nuevo)
        poner(Paragraph(nuevo, self.doc._body), self.sustituir(f"Semestre: {cfg['semestre']}"))
        lugar = copy.deepcopy(par[k]._p)
        par[k]._p.addnext(lugar)
        poner(Paragraph(lugar, self.doc._body), cfg["lugar"])
        # la portada es su propia sección (sin número de página)
        ultimo = [e for e in self.cuerpo.iterchildren() if e.tag == qn("w:p")][-1]
        ultimo.get_or_add_pPr().append(self._sect(False))

    def indice(self):
        p = self.parrafo("Índice", tam=15, despues=8, negrita=True, color=COLOR_CABECERA)
        p.paragraph_format.page_break_before = True
        p = self.doc.add_paragraph()
        r = p.add_run()
        for tipo, texto in (("begin", None), (None, ' TOC \\o "1-2" \\h \\z \\u '), ("separate", None),
                            (None, "Actualice el índice (F9)."), ("end", None)):
            if tipo:
                fc = OxmlElement("w:fldChar")
                fc.set(qn("w:fldCharType"), tipo)
                r._r.append(fc)
            elif texto.startswith(" TOC"):
                it = OxmlElement("w:instrText")
                it.set(qn("xml:space"), "preserve")
                it.text = texto
                r._r.append(it)
            else:
                t = OxmlElement("w:t")
                t.text = texto
                r._r.append(t)

    def md(self, nombre: str) -> list:
        return bloques(expandir(leer(INFORME / nombre)))

    def anexo_b(self):
        lineas = expandir(leer(INFORME / "B-trazabilidad.md"))
        corte = lineas.index("## Componente e infraestructura por requisito")
        bl = bloques(lineas[:corte])
        k = next(i for i, b in enumerate(bl) if b[0] == "tabla" and b[1] == "matriz")
        self.seccion(True)                  # el salto de sección ya abre página: el título va sin salto propio
        self.render(bl[:k], salto_h1=False)
        cab, filas, anchos = tabla_matriz()
        self.tabla([cab] + filas, anchos, ANCHO_H, tam=6.5)
        self.render(bl[k + 1:], salto_h1=False)
        self.seccion(False)

    def construir(self):
        self.portada()
        self.render(self.md("00-resumen.md"), salto_h1=False)
        self.indice()
        for f in ("05-seccion-0.md", "10-requerimientos.md", "20-prototipo.md", "30-arquitectura.md", "40-diseno-detallado.md"):
            self.render(self.md(f))
        self.render([("h1", "Anexos")] + self.md("A-acta-validacion.md"))
        self.anexo_b()
        self.render(self.md("C-diagramas.md"))
        self.render(self.md("D-sustentacion.md"))
        self._pie_de_pagina()
        cp = self.doc.core_properties
        cp.title = "Requerimientos y Diseño del Sistema — Celeris Edge (CE02 E1)"
        cp.author = equipo()
        cp.comments = f"Generado por docs/software/e1/build_informe_ce02.py desde commit {commit_fuente()}"
        return self.doc

    def _pie_de_pagina(self):
        secs = self.doc.sections
        for s in secs:
            s.different_first_page_header_footer = False
        secs[0].footer.is_linked_to_previous = False
        for p in secs[0].footer.paragraphs:
            for r in list(p.runs):
                r._r.getparent().remove(r._r)
        if len(secs) > 1:
            f = secs[1].footer
            f.is_linked_to_previous = False
            p = f.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _run_fmt(p.add_run("Celeris Edge · CE02 E1 Requerimientos y Diseño del Sistema · página "), 8, color="595959")
            r = p.add_run()
            _run_fmt(r, 8, color="595959")
            for tipo, texto in (("begin", None), (None, " PAGE "), ("end", None)):
                if tipo:
                    fc = OxmlElement("w:fldChar")
                    fc.set(qn("w:fldCharType"), tipo)
                    r._r.append(fc)
                else:
                    it = OxmlElement("w:instrText")
                    it.set(qn("xml:space"), "preserve")
                    it.text = texto
                    r._r.append(it)
            for s in secs[2:]:
                s.footer.is_linked_to_previous = True


# ==================================================================================================
def paginas(info: dict) -> dict:
    marcas = info.get("marcas", [])
    anexo = next((m["pagina"] for m in marcas if m["nivel"] == 1 and m["texto"].startswith("Anexos")), None)
    info["paginas_cuerpo"] = (anexo - 1) if anexo else None
    return info


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", default=str(SALIDA))
    ap.add_argument("--pdf", action="store_true")
    a = ap.parse_args(argv)
    inf = Informe()
    doc = inf.construir()
    salida = Path(a.salida)
    salida.mkdir(parents=True, exist_ok=True)
    ruta = salida / "Informe_Requerimientos_Diseno_CE02_E1_v0.4.docx"
    doc.save(str(ruta))
    print(ruta.relative_to(RAIZ) if ruta.is_relative_to(RAIZ) else ruta)
    print(f"figuras: {len(inf.figuras)} · [COMPLETAR]: {len(inf.completar)} ({len(set(inf.completar))} distintos)")
    if a.pdf:
        pdf = ruta.with_suffix(".pdf")
        if pdf.exists():
            pdf.unlink()
        with tempfile.TemporaryDirectory() as tmp:
            info = _word(ruta, pdf, Path(tmp) / "paginas.json")
        info = paginas(info)
        info.update({"docx": ruta.relative_to(RAIZ).as_posix(), "pdf": pdf.relative_to(RAIZ).as_posix(),
                     "commit_fuente": commit_fuente(), "figuras": inf.figuras, "completar": sorted(set(inf.completar))})
        PAGINAS_JSON.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"PDF: {info['pdf']} · {info.get('paginas')} páginas en total · cuerpo (portada a Sección 4): "
              f"{info.get('paginas_cuerpo')} páginas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
