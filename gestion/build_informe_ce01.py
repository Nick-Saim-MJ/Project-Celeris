"""Generador común de los informes de CE01 Gestión de TI (E1–E4) en DOCX y PDF.

    python gestion/build_informe_ce01.py --entregable E1 [--pdf] [--salida DIR] [--solo-validar]

Por entregable lee gestion/eN/:

| Archivo | Para qué |
| --- | --- |
| informe/NN-*.md | Cuerpo, en orden de nombre. `00-*.md` es el resumen ejecutivo (va antes del índice) |
| informe/X-*.md (letra) | Anexos escritos a mano, después del título «Anexos» |
| informe/portada.yaml | titulo, entregable, curso, semestre, lugar (opcional; hay valores por defecto) |
| figuras/figuras.yaml | id → archivo PNG, titulo, fuente, horizontal (CI-90) |
| tablas.py | TABLAS = {id: {"titulo", "fuente", "filas": función → [[cabecera], [fila], …]}} (opcional) |
| datos/*.json | {"datos": {clave: "texto ya formateado"}} para {{dato:clave}} (lo escriben los scripts de análisis) |
| autoevaluacion.yaml | criterio de la rúbrica → evidencia (títulos de sección o id de figura/tabla) |

Marcas en el Markdown:
  {{dato:clave}}       cifra calculada (gestion/ce01_datos.py o datos/*.json). Ninguna cifra se escribe a mano.
  {{ref:id}}           «Figura 1.3» / «Tabla 1.2» (numeración IEEE por entregable, CI-100)
  {{figura:id}}        figura del registro, en su propio bloque
  {{tabla:id}}         tabla generada (tablas.py o las comunes: supuestos-citados)
  «Tabla: id | Título | Fuente» en la línea anterior a una tabla escrita a mano le da título, número y fuente.

Salida: entregables/CE01/EN/Informe_CE01_EN_vX.Y.docx (+ .pdf con --pdf, vía Word COM). Al final agrega el anexo de
supuestos citados y el anexo «Autoevaluación contra la rúbrica».

Falla (código ≠ 0) y lista todos los problemas si:
  a) falta un título del contenido mínimo o uno de sus ítems como subtítulo (docs/fuentes/CE01/contenido-minimo.yaml),
     o el contenido mínimo no está cotejado con el texto literal del EPE (CI-99);
  b) queda un {{…}} sin resolver o un {{ref:}} a un id que no existe;
  c) una figura citada no existe (ni en el registro ni su PNG);
  d) una cifra con US$, %, h, min, GB, TB, Mbps, W o kWh aparece en el texto fuera de un {{dato:}} o de una tabla generada;
  e) una figura no tiene un párrafo previo que la cite con {{ref:id}} ni uno posterior que interprete sus resultados
     (≥ estilo.numeracion.palabras_min_interpretacion palabras); una tabla no tiene título o nadie la cita;
  f) un criterio de la rúbrica no tiene evidencia en autoevaluacion.yaml, o la evidencia no existe en el informe.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(RAIZ / "docs" / "software" / "e1"))
import build_informe_ce02 as base  # noqa: E402  (motor Markdown → DOCX de CE02, que a su vez usa el de CE0311)
import ce01_datos  # noqa: E402

CONTENIDO = RAIZ / "docs" / "fuentes" / "CE01" / "contenido-minimo.yaml"
SALIDA = RAIZ / "entregables" / "CE01"
ENTREGABLES = ("E1", "E2", "E3", "E4")
TABLAS_COMUNES = ("supuestos-citados", "autoevaluacion")     # anexos generados al final de cada informe

# Cifra con unidad escrita a mano (chequeo d). Los {{…}} y las citas [S-xx] se quitan antes de buscar.
CIFRA = re.compile(r"US\$\s*\d|(?<![\w.-])\d[\d   .,]*\s?(?:%|h\b|horas?\b|min\b|GB\b|TB\b|Mbps\b|Gbps\b|kWh\b|W\b)")
MARCA = re.compile(r"\{\{[^{}]*\}\}")


class InformeInvalido(Exception):
    def __init__(self, problemas: list[str]):
        super().__init__("\n".join(problemas))
        self.problemas = problemas


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKC", t)
    t = re.sub(r"[*`_]", "", t)
    t = re.sub(r"^\s*(?:\d+(?:\.\d+)*\.?|[A-Z]\.)\s+", "", t)      # «1.1 Contexto…» → «Contexto…»
    return re.sub(r"\s+", " ", t).strip().casefold()


def _cubre(exigido: str, titulos: set[str]) -> bool:
    """¿Algún título del informe empieza con el texto exigido? Lo que va entre paréntesis en el EPE («(si aplica)»,
    «(SMART)», «(opcional según complejidad)») no se exige; el informe puede ampliar el título («Análisis FODA y TOWS»)."""
    base = _norm(re.sub(r"\s*\([^)]*\)", "", exigido)).rstrip(".")
    return any(t.startswith(base) for t in titulos)


def _hex(nombre: str) -> str:
    return ce01_datos.estilo()["paleta"][nombre].lstrip("#").upper()


# ==================================================================================================
# Fuentes de un entregable
# ==================================================================================================
@dataclass
class Fuentes:
    ent: str
    dir: Path
    contenido: dict
    cuerpo: list[tuple[str, list]] = field(default_factory=list)     # (archivo, bloques)
    anexos: list[tuple[str, list]] = field(default_factory=list)
    figuras: dict = field(default_factory=dict)
    tablas: dict = field(default_factory=dict)
    datos: dict = field(default_factory=dict)
    autoeval: list = field(default_factory=list)
    portada: dict = field(default_factory=dict)

    @property
    def numero(self) -> int:
        return int(self.ent[1:])


def cargar_fuentes(ent: str, base_dir: Path = AQUI, contenido: Path = CONTENIDO) -> Fuentes:
    d = base_dir / ent.lower()
    if not (d / "informe").is_dir():
        raise InformeInvalido([f"No existe {d / 'informe'}: el entregable {ent} todavía no tiene texto"])
    cont = yaml.safe_load(contenido.read_text(encoding="utf-8"))
    f = Fuentes(ent, d, cont)
    for md in sorted((d / "informe").glob("*.md")):
        bl = base.bloques(base.leer(md))
        (f.cuerpo if md.name[0].isdigit() else f.anexos).append((md.name, bl))
    reg = d / "figuras" / "figuras.yaml"
    f.figuras = (yaml.safe_load(reg.read_text(encoding="utf-8")) or {}) if reg.exists() else {}
    if (d / "tablas.py").exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location(f"tablas_{ent.lower()}", d / "tablas.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        f.tablas = dict(getattr(mod, "TABLAS", {}))
    f.datos = dict(ce01_datos.datos())
    for js in sorted((d / "datos").glob("*.json")) if (d / "datos").is_dir() else []:
        f.datos.update({k: str(v) for k, v in json.loads(js.read_text(encoding="utf-8")).get("datos", {}).items()})
    ae = d / "autoevaluacion.yaml"
    f.autoeval = (yaml.safe_load(ae.read_text(encoding="utf-8")) or []) if ae.exists() else []
    pt = d / "informe" / "portada.yaml"
    f.portada = (yaml.safe_load(pt.read_text(encoding="utf-8")) or {}) if pt.exists() else {}
    return f


# ==================================================================================================
# Pre-paso: numeración y chequeos (no escribe nada)
# ==================================================================================================
def _texto_bloque(b) -> str:
    if b[0] in ("p", "nota") or b[0].startswith("h"):
        return b[1]
    if b[0] in ("li", "num"):
        return b[2]
    if b[0] == "tabla" and not isinstance(b[1], str):
        return " ".join(" ".join(f) for f in b[1])
    return ""


def _es_titulo_tabla(b) -> bool:
    return b[0] == "p" and b[1].startswith("Tabla:")


def _partes_titulo_tabla(b) -> tuple[str, str, str]:
    partes = [x.strip() for x in b[1][len("Tabla:"):].split("|")]
    return (partes + ["", "", ""])[:3]


def numerar(f: Fuentes) -> dict[str, str]:
    """{id: «Figura 1.3» | «Tabla 1.2»} en orden de aparición (cuerpo y anexos escritos a mano)."""
    e, nf, nt, num = f.numero, 0, 0, {}
    fmt_f = ce01_datos.estilo()["numeracion"]["figura"].rstrip(".")
    fmt_t = ce01_datos.estilo()["numeracion"]["tabla"].rstrip(".")
    for _, bl in f.cuerpo + f.anexos:
        for k, b in enumerate(bl):
            if b[0] == "figura":
                nf += 1
                num.setdefault(b[1].split("|")[0].strip(), fmt_f.format(e=e, n=nf))
            elif b[0] == "tabla" and isinstance(b[1], str):
                nt += 1
                num.setdefault(b[1].strip(), fmt_t.format(e=e, n=nt))
            elif b[0] == "tabla" and k > 0 and _es_titulo_tabla(bl[k - 1]):
                nt += 1
                num.setdefault(_partes_titulo_tabla(bl[k - 1])[0], fmt_t.format(e=e, n=nt))
    for t in TABLAS_COMUNES:          # anexos generados
        nt += 1
        num.setdefault(t, fmt_t.format(e=e, n=nt))
    return num


def comprobar(f: Fuentes, exigir_cotejado: bool = True) -> list[str]:
    """Todos los problemas del entregable (vacío = se puede generar)."""
    p: list[str] = []
    meta = f.contenido.get("meta", {})
    if exigir_cotejado and not meta.get("cotejado"):
        p.append(f"a) docs/fuentes/CE01/contenido-minimo.yaml no está cotejado con el texto literal del EPE ({meta.get('cambio', 'CI-99')})")
    cont = f.contenido["entregables"][f.ent]
    todo = f.cuerpo + f.anexos
    titulos = {_norm(b[1]) for _, bl in todo for b in bl if b[0].startswith("h")}
    for c in cont["contenido_minimo"]:
        if not _cubre(c["titulo"], titulos):
            p.append(f"a) falta el título del contenido mínimo {c['id']} «{c['titulo']}»")
        for item in c.get("incluye", []):
            if not _cubre(item, titulos):
                p.append(f"a) falta el subtítulo del contenido mínimo {c['id']} «{item}»")

    num = numerar(f)
    palabras_min = ce01_datos.estilo()["numeracion"]["palabras_min_interpretacion"]
    refs_usadas: set[str] = set()
    for archivo, bl in todo:
        for k, b in enumerate(bl):
            texto = _texto_bloque(b)
            for m in MARCA.finditer(texto):
                tipo, _, arg = m.group(0)[2:-2].partition(":")
                if tipo == "dato" and arg not in f.datos:
                    p.append(f"b) {archivo}: {{{{dato:{arg}}}}} no existe en ce01_datos.datos() ni en datos/*.json")
                elif tipo == "ref":
                    refs_usadas.add(arg)
                    if arg not in num:
                        p.append(f"b) {archivo}: {{{{ref:{arg}}}}} no apunta a ninguna figura ni tabla")
                elif tipo not in ("dato", "ref"):
                    p.append(f"b) {archivo}: marca desconocida {m.group(0)}")
            limpio = re.sub(r"\[S-\d{2}(?:[,–-]\s*S-\d{2})*\]", "", MARCA.sub("", texto))
            if b[0] != "code":
                for m in CIFRA.finditer(limpio):
                    p.append(f"d) {archivo}: cifra escrita a mano «{m.group(0).strip()}» en «{limpio.strip()[:70]}…»; use {{{{dato:…}}}}")
            if b[0] == "figura":
                fid = b[1].split("|")[0].strip()
                reg = f.figuras.get(fid)
                if not reg:
                    p.append(f"c) {archivo}: la figura «{fid}» no está en figuras/figuras.yaml")
                elif not (f.dir / "figuras" / reg.get("archivo", "")).is_file():
                    p.append(f"c) {archivo}: la figura «{fid}» no tiene su PNG ({reg.get('archivo')})")
                elif not reg.get("titulo") or not reg.get("fuente"):
                    p.append(f"c) {archivo}: la figura «{fid}» necesita `titulo` y `fuente` en figuras.yaml")
                antes = bl[k - 1] if k > 0 else None
                despues = bl[k + 1] if k + 1 < len(bl) else None
                if not antes or antes[0] != "p" or f"{{{{ref:{fid}}}}}" not in antes[1]:
                    p.append(f"e) {archivo}: la figura «{fid}» necesita un párrafo previo que la introduzca con {{{{ref:{fid}}}}}")
                if not despues or despues[0] != "p" or len(MARCA.sub("x", despues[1]).split()) < palabras_min:
                    p.append(f"e) {archivo}: la figura «{fid}» necesita un párrafo posterior de interpretación (≥ {palabras_min} palabras)")
            if b[0] == "tabla" and isinstance(b[1], str):
                if b[1] not in f.tablas and b[1] not in TABLAS_COMUNES:
                    p.append(f"b) {archivo}: {{{{tabla:{b[1]}}}}} no existe en tablas.py")
            elif b[0] == "tabla":
                if k == 0 or not _es_titulo_tabla(bl[k - 1]):
                    p.append(f"e) {archivo}: tabla sin título; anteponga «Tabla: id | Título | Fuente» "
                             f"(empieza con «{' | '.join(b[1][0])[:50]}»)")
                else:
                    tid, tit, fue = _partes_titulo_tabla(bl[k - 1])
                    if not tid or not tit or not fue:
                        p.append(f"e) {archivo}: «{bl[k - 1][1][:60]}» debe tener id, título y fuente separados por «|»")
    for tid, etiqueta in num.items():
        if tid in TABLAS_COMUNES:
            continue
        if tid not in refs_usadas:
            p.append(f"e) {etiqueta} («{tid}») no se cita en el texto con {{{{ref:{tid}}}}}")

    criterios = {c["criterio"] for c in cont["rubrica"]}
    evidencia = {a.get("criterio"): a for a in f.autoeval}
    for c in criterios - set(evidencia):
        p.append(f"f) autoevaluacion.yaml: el criterio «{c}» no tiene evidencia")
    for c, a in evidencia.items():
        if c not in criterios:
            p.append(f"f) autoevaluacion.yaml: «{c}» no es un criterio de la rúbrica de {f.ent}")
        for ev in a.get("evidencia", []):
            if ev not in num and _norm(ev) not in titulos:
                p.append(f"f) autoevaluacion.yaml: la evidencia «{ev}» de «{c}» no es un título ni una figura/tabla del informe")
    return p


# ==================================================================================================
# Documento
# ==================================================================================================
class InformeCE01(base.Informe):
    def __init__(self, f: Fuentes):
        # No se llama a base.Informe.__init__ (lee datos de CE02): se arma lo mismo con los datos de CE01.
        base.COLOR_CABECERA = _hex("azul_upeu")          # cabeceras y títulos en el azul de la paleta (CI-100)
        self.f = f
        self.d = f.datos
        self.num = numerar(f)
        self.fecha = ce01_datos.cargar()["meta"]["fecha"]
        self.portada_cfg = {
            "titulo": "Celeris Edge: caché de descargas para los laboratorios de cómputo del Campus Juliaca",
            "entregable": f"Entregable {f.numero} · {f.contenido['entregables'][f.ent]['nombre']}",
            "curso": "Gestión de Tecnologías de Información (CE01)",
            "semestre": "[COMPLETAR: semestre académico]",
            "lugar": "Juliaca",
            **f.portada,
        }
        from docx import Document
        import copy
        self.doc = Document(str(base.PORTADA))
        self.cuerpo = self.doc.element.body
        for ref in self.cuerpo[-1].findall(qn("w:headerReference")) + self.cuerpo[-1].findall(qn("w:footerReference")):
            self.cuerpo[-1].remove(ref)
        self.sect_base = copy.deepcopy(self.cuerpo[-1])
        self.horizontal = False
        self.n_fig = 0
        self.figuras: list[str] = []
        self.completar: list[str] = []
        self.supuestos_citados: set[str] = set()
        self._estilos()

    # ------------------------------------------------------------------ texto
    def sustituir(self, t: str) -> str:
        self.supuestos_citados |= set(re.findall(r"S-\d{2}", " ".join(re.findall(r"\[(S-[^\]]+)\]", t))))
        t = re.sub(r"\{\{ref:([^{}]+)\}\}", lambda m: self.num[m.group(1)], t)
        t = re.sub(r"\{\{dato:([^{}]+)\}\}", lambda m: self.d[m.group(1)], t)
        if MARCA.search(t):
            raise InformeInvalido([f"b) marca sin resolver: {MARCA.search(t).group(0)}"])
        return super().sustituir(t)

    def nota(self, texto):
        p = self.parrafo(texto, despues=8, antes=4, color=_hex("azul_upeu"))
        ppr = p._p.get_or_add_pPr()
        bdr = OxmlElement("w:pBdr")
        izq = OxmlElement("w:left")
        for k, v in (("w:val", "single"), ("w:sz", "18"), ("w:space", "8"), ("w:color", _hex("ambar_upeu"))):
            izq.set(qn(k), v)
        bdr.append(izq)
        ppr.append(bdr)
        p.paragraph_format.left_indent = Cm(0.4)

    def _fuente(self, texto: str):
        fmt = ce01_datos.estilo()["numeracion"]["fuente"]
        self.parrafo(fmt.format(fuente=texto.rstrip(".")), tam=8.5, despues=8, cursiva=True, color="595959",
                     alinear=WD_ALIGN_PARAGRAPH.CENTER)

    def titulo_tabla(self, tid: str, titulo: str):
        p = self.parrafo(f"**{self.num[tid]}.** {titulo}", tam=9, despues=2, antes=4, alinear=WD_ALIGN_PARAGRAPH.CENTER)
        p.paragraph_format.keep_with_next = True

    def tabla_con_titulo(self, tid: str, titulo: str, fuente: str, filas: list[list[str]]):
        self.titulo_tabla(tid, titulo)
        self.tabla(filas, tam=7.5 if len(filas[0]) >= 6 else base.TAM_TABLA)
        self._fuente(fuente)

    def figura_ce01(self, fid: str):
        reg = self.f.figuras[fid]
        png = self.f.dir / "figuras" / reg["archivo"]
        from PIL import Image
        with Image.open(png) as im:
            ratio = im.size[0] / im.size[1]
        fig = ce01_datos.estilo()["figura"]
        ancho_max = fig["ancho_h_cm"] if self.horizontal else fig["ancho_v_cm"]
        self._imagen(png, min(ancho_max, fig["alto_max_cm"] * ratio) * float(reg.get("escala", 1)))
        pie = self.parrafo(f"**{self.num[fid]}.** {reg['titulo']}", tam=9, despues=0, cursiva=True, color="595959",
                           alinear=WD_ALIGN_PARAGRAPH.CENTER)
        pie.paragraph_format.keep_with_next = True
        self._fuente(reg["fuente"])
        self.figuras.append(fid)
        self.n_fig += 1

    # ------------------------------------------------------------------ render
    def _horizontal(self, bl, k) -> bool:
        """¿bl[k] es el párrafo que introduce una figura horizontal?"""
        return (k + 1 < len(bl) and bl[k][0] == "p" and bl[k + 1][0] == "figura"
                and bool(self.f.figuras.get(bl[k + 1][1].strip(), {}).get("horizontal")))

    def render(self, bl, salto_h1=True):
        bl = self._unir_listas_cortas(bl)
        k = 0
        while k < len(bl):
            b = bl[k]
            t = b[0]
            sig = bl[k + 1] if k + 1 < len(bl) else None
            # Un título seguido de una figura horizontal abre la sección horizontal antes del título: así no queda
            # solo en una página vertical (el salto de sección ya abre página).
            if t in ("h1", "h2", "h3", "h4") and self._horizontal(bl, k + 1):
                self.seccion(True)
                self.titulo(b[1], min(int(t[1]), 3), salto=False)
                k += 1
                continue
            # figura horizontal (CI-90): el párrafo que la introduce, la figura y su interpretación van en la sección
            if self._horizontal(bl, k):
                self.seccion(True)
                self.parrafo(b[1])
                self.figura_ce01(sig[1].strip())
                if k + 2 < len(bl) and bl[k + 2][0] == "p":
                    self.parrafo(bl[k + 2][1])
                    k += 1
                self.seccion(False)
                k += 2
                continue
            if t in ("h1", "h2", "h3", "h4"):
                nivel = min(int(t[1]), 3)
                self.titulo(b[1], nivel, salto=salto_h1 and nivel == 1)
            elif _es_titulo_tabla(b) and sig and sig[0] == "tabla" and not isinstance(sig[1], str):
                tid, tit, fue = _partes_titulo_tabla(b)
                self.tabla_con_titulo(tid, tit, fue, sig[1])
                k += 1
            elif t == "p":
                self.parrafo(b[1])
            elif t in ("li", "num"):
                self.lista(b[2], b[1], "-" if t == "li" else b[3])
            elif t == "nota":
                self.nota(b[1])
            elif t == "code":
                self.codigo(b[1])
            elif t == "tabla" and isinstance(b[1], str):
                tid = b[1].strip()
                spec = self.f.tablas[tid]
                self.tabla_con_titulo(tid, spec["titulo"], spec["fuente"], spec["filas"]())
            elif t == "tabla":
                self.tabla(b[1])
            elif t == "figura":
                self.figura_ce01(b[1].strip())
            k += 1

    # ------------------------------------------------------------------ anexos generados
    def anexo_supuestos(self, letra: str):
        self.titulo(f"Anexo {letra}. Supuestos citados en el informe", 2, salto=True)
        ids = sorted(self.supuestos_citados)
        self.parrafo(f"La {self.num['supuestos-citados']} reúne los supuestos que cita el informe. Ninguno se presenta "
                     "como dato: cada uno indica cómo se valida (Marco común M5).")
        filas = [["ID", "Supuesto", "Valor usado", "Cómo validarlo", "Responsable"]]
        for sid in ids:
            s = ce01_datos.texto_supuesto(sid)
            filas.append([sid, s["supuesto"], str(s["valor"]), s["validacion"], s.get("responsable") or "—"])
        if len(filas) == 1:
            filas.append(["—", "El informe no cita supuestos", "—", "—", "—"])
        self.titulo_tabla("supuestos-citados", "Supuestos que cita el informe")
        self.tabla(filas, tam=7.5)
        self._fuente("infra/trazabilidad.yaml")

    def anexo_autoevaluacion(self, letra: str):
        self.titulo(f"Anexo {letra}. Autoevaluación contra la rúbrica", 2, salto=True)
        self.parrafo(f"La {self.num['autoevaluacion']} contrasta cada criterio de la rúbrica oficial con su descriptor "
                     "de nivel Excelente y con el lugar del informe donde está la evidencia.")
        cont = self.f.contenido["entregables"][self.f.ent]["rubrica"]
        ev = {a["criterio"]: a for a in self.f.autoeval}
        filas = [["Criterio", "Nivel Excelente (rúbrica)", "Dónde está la evidencia"]]
        for c in cont:
            a = ev.get(c["criterio"], {})
            donde = "; ".join(self.num.get(x, x) for x in a.get("evidencia", []))
            filas.append([c["criterio"], c.get("excelente") or "[COMPLETAR: descriptor literal del EPE]", donde])
        self.titulo_tabla("autoevaluacion", "Autoevaluación contra la rúbrica")
        self.tabla(filas, tam=8)
        self._fuente("docs/fuentes/CE01 (rúbrica) y gestion/" + self.f.ent.lower() + "/autoevaluacion.yaml")

    # ------------------------------------------------------------------ partes
    def portada(self):
        base.fecha_ce02 = lambda: self.fecha
        super().portada()

    def construir(self):
        f = self.f
        self.portada()
        cuerpo = list(f.cuerpo)
        if cuerpo and cuerpo[0][0].startswith("00"):
            self.render(cuerpo.pop(0)[1], salto_h1=False)
        self.indice()
        for _, bl in cuerpo:
            self.render(bl)
        self.titulo("Anexos", 1, salto=True)
        letras = iter("ABCDEFGHIJ")
        for _, bl in f.anexos:
            self.render(bl, salto_h1=False)
            next(letras)
        self.anexo_supuestos(next(letras))
        self.anexo_autoevaluacion(next(letras))
        self._pie_de_pagina()
        cp = self.doc.core_properties
        cp.title = f"{f.contenido['entregables'][f.ent]['nombre']} — Celeris Edge (CE01 {f.ent})"
        cp.author = base.equipo()
        cp.comments = f"Generado por gestion/build_informe_ce01.py desde commit {base.commit_fuente()}"
        return self.doc

    def _pie_de_pagina(self):
        """El mismo pie que CE02, con el texto de CE01."""
        texto = f"Celeris Edge · CE01 {self.f.ent} {self.f.contenido['entregables'][self.f.ent]['nombre']} · página "
        secs = self.doc.sections
        for s_ in secs:
            s_.different_first_page_header_footer = False
        secs[0].footer.is_linked_to_previous = False
        for p in secs[0].footer.paragraphs:
            for r in list(p.runs):
                r._r.getparent().remove(r._r)
        if len(secs) > 1:
            pf = secs[1].footer
            pf.is_linked_to_previous = False
            p = pf.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            base._run_fmt(p.add_run(texto), 8, color="595959")
            r = p.add_run()
            base._run_fmt(r, 8, color="595959")
            for tipo, instr in (("begin", None), (None, " PAGE "), ("end", None)):
                if tipo:
                    fc = OxmlElement("w:fldChar")
                    fc.set(qn("w:fldCharType"), tipo)
                    r._r.append(fc)
                else:
                    it = OxmlElement("w:instrText")
                    it.set(qn("xml:space"), "preserve")
                    it.text = instr
                    r._r.append(it)
            for s_ in secs[2:]:
                s_.footer.is_linked_to_previous = True


# ==================================================================================================
def nombre_docx(ent: str) -> str:
    v = ce01_datos.cargar()["meta"]["versiones_informe"][ent]
    return f"Informe_CE01_{ent}_v{v}.docx"


def generar(ent: str, salida: Path = SALIDA, pdf: bool = False, base_dir: Path = AQUI, contenido: Path = CONTENIDO,
            exigir_cotejado: bool = True, solo_validar: bool = False) -> Path | None:
    f = cargar_fuentes(ent, base_dir, contenido)
    problemas = comprobar(f, exigir_cotejado)
    if problemas:
        raise InformeInvalido(problemas)
    if solo_validar:
        return None
    inf = InformeCE01(f)
    doc = inf.construir()
    dest = Path(salida) / ent
    dest.mkdir(parents=True, exist_ok=True)
    ruta = dest / nombre_docx(ent)
    doc.save(str(ruta))
    if pdf:
        pdf_ruta = ruta.with_suffix(".pdf")
        if pdf_ruta.exists():
            pdf_ruta.unlink()
        with tempfile.TemporaryDirectory() as tmp:
            info = base._word(ruta, pdf_ruta, Path(tmp) / "paginas.json")
        info.update({"docx": ruta.name, "pdf": pdf_ruta.name, "commit_fuente": base.commit_fuente(),
                     "figuras": inf.figuras, "completar": sorted(set(inf.completar))})
        (f.dir / "informe" / "paginas.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n",
                                                         encoding="utf-8", newline="\n")
    return ruta


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entregable", required=True, choices=ENTREGABLES)
    ap.add_argument("--salida", default=str(SALIDA))
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument("--solo-validar", action="store_true", help="Solo los chequeos a)–f); no escribe el DOCX")
    a = ap.parse_args(argv)
    try:
        ruta = generar(a.entregable, Path(a.salida), a.pdf, solo_validar=a.solo_validar)
    except (InformeInvalido, ce01_datos.DatosCE01Error) as e:
        problemas = getattr(e, "problemas", [str(e)])
        print(f"CE01 {a.entregable}: {len(problemas)} problema(s); no se generó el informe", file=sys.stderr)
        for x in problemas:
            print("  -", x, file=sys.stderr)
        return 1
    print(f"CE01 {a.entregable}: chequeos a)–f) en verde" + (f" · {ruta.relative_to(RAIZ)}" if ruta else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
