"""Validación V-50+ de los diagramas draw.io (P3) contra la fuente única, e informe de cobertura componente × figura.

Lee entregables/CE0311/diagramas/FIG-*.drawio (XML plano o comprimido), y sus exportaciones .png y .pdf, y comprueba:
    V-50  Las 7 figuras existen en .drawio, .png y .pdf; PNG y PDF llevan el XML embebido; no hay exportaciones viejas.
    V-51  Cada componente aparece en todas las figuras de su campo `figuras`, y en ninguna otra (cobertura).
    V-52  Todo `celeris_id` es un ID del contrato (componente, «ID:interfaz», zona, F-nn, DET-xx, AM-xx, VPN).
    V-53  Toda IP o CIDR rotulada existe en el inventario; en la caja de un componente, es de ese componente.
    V-54  Flujos: FIG-5.5a ∪ FIG-5.5b = todos los F-nn con `figura`; cada flecha lleva la etiqueta «F-nn · proto/puerto ·
          protección» que se deriva del inventario; ninguna figura de flujos dibuja un F-nn de la otra.
    V-55  Cada figura tiene bloque de título, leyenda y panel «Qué aporta y qué pasa si falla» que cubre lo dibujado.
    V-56  Criticidad (borde 3/2/1 px + texto ALTA/MEDIA/BAJA) y color de zona (Okabe-Ito de inventory.yaml).

Escribe docs/infra/e1/cobertura-figuras.md y .json (la matriz XLSX de P4 lee el JSON para la columna «Figuras»).

    python infra/gen/drawio_check.py [--dir entregables/CE0311/diagramas]     # código 1 si hay errores
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import struct
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from celeris_infra import RAIZ, Infra  # noqa: E402
from drawio import CRITICIDAD, FIGURAS, etiqueta_flujo  # noqa: E402

DIR = RAIZ / "entregables" / "CE0311" / "diagramas"
INFORME_MD = RAIZ / "docs" / "infra" / "e1" / "cobertura-figuras.md"
INFORME_JSON = RAIZ / "docs" / "infra" / "e1" / "cobertura-figuras.json"
ROLES = ("titulo", "leyenda", "panel")
RE_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b")


@dataclass
class Hallazgo:
    nivel: str          # error | advertencia | info
    mensaje: str
    corregir: str = ""


@dataclass
class Chequeo:
    id: str
    titulo: str
    hallazgos: list[Hallazgo] = field(default_factory=list)

    @property
    def estado(self) -> str:
        if any(h.nivel == "error" for h in self.hallazgos):
            return "FALLA"
        if any(h.nivel == "advertencia" for h in self.hallazgos):
            return "ADVERTENCIA"
        return "PASA"

    def e(self, msg, fix=""):
        self.hallazgos.append(Hallazgo("error", msg, fix))

    def w(self, msg, fix=""):
        self.hallazgos.append(Hallazgo("advertencia", msg, fix))


# --------------------------------------------------------------------------------------------------
# Lectura de .drawio y de los XML embebidos
# --------------------------------------------------------------------------------------------------
@dataclass
class Elemento:
    attrs: dict
    estilo: str
    texto: str          # etiqueta sin HTML
    es_arista: bool


def _modelo(diagrama: ET.Element) -> ET.Element:
    m = diagrama.find("mxGraphModel")
    if m is not None:
        return m
    crudo = base64.b64decode((diagrama.text or "").strip())
    xml = urllib.parse.unquote(zlib.decompress(crudo, -15).decode("utf-8"))
    return ET.fromstring(xml)


def texto_plano(label: str) -> str:
    t = re.sub(r"<br\s*/?>", "\n", label or "")
    t = re.sub(r"<[^>]+>", "", t)
    return t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&#8203;", "").replace("​", "")


def leer_drawio(ruta: Path) -> list[Elemento]:
    raiz = ET.parse(ruta).getroot()
    diag = raiz.find("diagram")
    root = _modelo(diag).find("root")
    salida = []
    for nodo in root:
        if nodo.tag == "object":
            cell = nodo.find("mxCell")
            attrs = {k: v for k, v in nodo.attrib.items()}
            label = attrs.get("label", "")
        else:
            cell = nodo
            attrs = {}
            label = nodo.get("value", "")
        if cell is None:
            continue
        salida.append(Elemento(attrs, cell.get("style", ""), texto_plano(label), cell.get("edge") == "1"))
    return salida


def png_embebido(ruta: Path) -> bool:
    datos = ruta.read_bytes()
    pos = 8
    while pos < len(datos):
        largo = struct.unpack(">I", datos[pos:pos + 4])[0]
        tipo = datos[pos + 4:pos + 8]
        cuerpo = datos[pos + 8:pos + 8 + largo]
        if tipo in (b"tEXt", b"zTXt"):
            clave, _, resto = cuerpo.partition(b"\0")
            if clave in (b"mxfile", b"mxGraphModel"):
                valor = zlib.decompress(resto[1:]) if tipo == b"zTXt" else resto
                return b"mxfile" in urllib.parse.unquote_to_bytes(valor)
        pos += 12 + largo
    return False


def pdf_embebido(ruta: Path) -> bool:
    """draw.io (pdf-lib) guarda el XML url-codificado en /Subject, a menudo dentro de un /ObjStm comprimido."""
    datos = ruta.read_bytes()
    trozos = [datos]
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", datos, re.S):
        try:
            trozos.append(zlib.decompress(m.group(1)))
        except zlib.error:
            pass
    for t in trozos:
        for m in re.finditer(rb"/Subject\s*(\((?:\\.|[^\\)])*\)|<[0-9A-Fa-f\s]*>)", t):
            v = m.group(1)
            if v.startswith(b"<"):
                v = bytes.fromhex(re.sub(rb"\s", b"", v[1:-1]).decode())
                if v.startswith(b"\xfe\xff"):
                    v = v[2:].decode("utf-16-be").encode()
            if b"mxfile" in urllib.parse.unquote_to_bytes(v):
                return True
    return False


# --------------------------------------------------------------------------------------------------
# Chequeos
# --------------------------------------------------------------------------------------------------
def ips_del_inventario(x: Infra) -> set[str]:
    vistos: set[str] = set()

    def visitar(n):
        if isinstance(n, dict):
            for v in n.values():
                visitar(v)
        elif isinstance(n, list):
            for v in n:
                visitar(v)
        elif isinstance(n, str):
            vistos.update(RE_IP.findall(n))
    visitar(x.inv)
    return vistos


def ips_de_componente(comp: dict) -> set[str]:
    s = {i["ip"] for i in comp["ips"] if i["ip"]}
    if comp.get("cidr"):
        s.add(comp["cidr"])
    for i in comp["ips"]:
        s.update(RE_IP.findall(i.get("nota") or ""))
    return s


def ids_validos(x: Infra) -> set[str]:
    v = set(x.componentes) | set(x.zonas) | set(x.flujos) | set(x.detecciones) | set(x.amenazas) | {x.inv["vpn"]["id"]}
    for c in x.componentes.values():
        v.update(f"{c['id']}:{i['interfaz']}" for i in c["ips"])
    return v


def comprobar(x: Infra, dir_: Path = DIR) -> tuple[list[Chequeo], dict]:
    c50 = Chequeo("V-50", "Figuras .drawio, .png y .pdf presentes, con XML embebido y al día")
    c51 = Chequeo("V-51", "Cobertura componente × figura igual al campo `figuras` del inventario")
    c52 = Chequeo("V-52", "Todo celeris_id es un ID del contrato")
    c53 = Chequeo("V-53", "IP y CIDR rotulados existen en el inventario (y son del componente que los rotula)")
    c54 = Chequeo("V-54", "Flujos F-nn: FIG-5.5a ∪ FIG-5.5b completas y etiquetas derivadas del inventario")
    c55 = Chequeo("V-55", "Título, leyenda y panel «Qué aporta y qué pasa si falla» en cada figura")
    c56 = Chequeo("V-56", "Criticidad (borde + texto) y color de zona según CLAUDE.md")
    chequeos = [c50, c51, c52, c53, c54, c55, c56]

    validos = ids_validos(x)
    ips_inv = ips_del_inventario(x)
    dibujado: dict[str, set[str]] = {}        # figura → componentes presentes (caja propia con celeris_id)
    agrupados: dict[str, set[str]] = {}       # figura → componentes citados dentro de un bloque (FIG-1.1)
    flujos_en: dict[str, set[str]] = {}
    for fig in FIGURAS:
        ruta = dir_ / f"{fig}.drawio"
        if not ruta.exists():
            c50.e(f"Falta {ruta.relative_to(RAIZ)}", "make diagrams-check (python infra/gen/drawio.py)")
            continue
        for ext, fn in ((".png", png_embebido), (".pdf", pdf_embebido)):
            exp = ruta.with_suffix(ext)
            if not exp.exists():
                c50.e(f"Falta {exp.name}", "python infra/gen/exportar_drawio.py (necesita draw.io Desktop)")
            elif not fn(exp):
                c50.e(f"{exp.name} no lleva el XML del diagrama embebido", "Exporte con -e (exportar_drawio.py lo hace)")
            elif exp.stat().st_mtime + 1 < ruta.stat().st_mtime:
                c50.w(f"{exp.name} es anterior a {ruta.name}", "Vuelva a exportar: python infra/gen/exportar_drawio.py")

        elems = leer_drawio(ruta)
        presentes: set[str] = set()
        roles = {e.attrs.get("celeris_rol") for e in elems}
        panel_comps: set[str] = set()
        flujos_fig: set[str] = set()
        for el in elems:
            cid = el.attrs.get("celeris_id")
            if el.attrs.get("celeris_rol") == "panel":
                panel_comps = {s.strip() for s in el.attrs.get("componentes", "").split(",") if s.strip()}
            if not cid:
                continue
            if cid not in validos:
                retirado = cid.split(":")[0] in set(x.componentes_retirados) | set(x.zonas_retiradas) | set(x.flujos_retirados)
                if retirado:
                    c52.e(f"{fig}: dibuja el ID retirado «{cid}» (v0.4); pendiente de I4: regenerar los diagramas", "Un ID retirado no puede aparecer en una figura (V-44): regenere con make diagrams-check (I4)")
                else:
                    c52.e(f"{fig}: celeris_id desconocido «{cid}»", "Use solo IDs de infra/*.yaml")
                continue
            base = cid.split(":")[0]
            # cobertura
            if base in x.componentes and ":" not in cid:
                presentes.add(base)
            for inc in (el.attrs.get("celeris_incluye") or "").split(","):
                if inc.strip() in x.componentes:
                    agrupados.setdefault(fig, set()).add(inc.strip())
            # IP rotuladas
            for ip in RE_IP.findall(el.texto):
                if ip not in ips_inv:
                    c53.e(f"{fig}: «{ip}» en {cid} no está en infra/inventory.yaml", "Corrija el generador o registre el CI-nn")
                elif base in x.componentes and ":" not in cid and el.attrs.get("celeris_tipo") == "componente" \
                        and ip not in ips_de_componente(x.componentes[base]):
                    c53.e(f"{fig}: la caja de {cid} rotula {ip}, que no es de {cid}")
                elif ":" in cid:
                    iface = cid.split(":")[1]
                    propia = next((i["ip"] for i in x.componentes[base]["ips"] if i["interfaz"] == iface), None)
                    if ip != propia:
                        c53.e(f"{fig}: la interfaz {cid} rotula {ip} (inventario: {propia})")
            # flujos
            if cid in x.flujos:
                flujos_fig.add(cid)
                esperado = etiqueta_flujo(x.flujos[cid])
                if el.attrs.get("etiqueta") != esperado:
                    c54.e(f"{fig}: {cid} con etiqueta «{el.attrs.get('etiqueta')}»; se espera «{esperado}»")
                if el.es_arista:
                    f = x.flujos[cid]
                    if f["accion"] == "bloquear" and "dashPattern=1 4" not in el.estilo:
                        c54.e(f"{fig}: {cid} bloqueado sin línea punteada")
                    elif f["accion"] != "bloquear" and f["proteccion"]["tipo"] == "sin_cifrar_riesgo_aceptado" \
                            and "dashPattern=8 4" not in el.estilo:
                        c54.e(f"{fig}: {cid} sin cifrar sin línea discontinua")
                    elif f["proteccion"]["tipo"] not in ("sin_cifrar_riesgo_aceptado", "no_aplica") and "dashed=1" in el.estilo:
                        c54.e(f"{fig}: {cid} cifrado dibujado con línea discontinua")
            # criticidad y color
            if el.attrs.get("celeris_tipo") in ("componente", "interfaz") and not el.es_arista:
                crit = el.attrs.get("criticidad")
                grosor, tag = CRITICIDAD.get(crit, (None, None))
                m = re.search(r"strokeWidth=([\d.]+)", el.estilo)
                if not m or float(m.group(1)) != grosor:
                    c56.e(f"{fig}: {cid} ({crit}) con borde {m.group(1) if m else '—'} px; se espera {grosor} px")
                if tag and tag not in el.texto:
                    c56.e(f"{fig}: {cid} no lleva el texto {tag}")
                if base in x.componentes and ":" not in cid and crit != x.componentes[base]["criticidad"]:
                    c56.e(f"{fig}: {cid} con criticidad {crit}; inventario: {x.componentes[base]['criticidad']}")
            if el.attrs.get("celeris_tipo") == "zona" and cid in x.zonas and x.zonas[cid].get("color"):
                color = x.zonas[cid]["color"].upper()
                m = re.search(r"strokeColor=(#[0-9A-Fa-f]{6})", el.estilo)
                if not m or m.group(1).upper() != color:
                    c56.e(f"{fig}: zona {cid} con borde {m.group(1) if m else '—'}; inventory.yaml: {color}")
                if cid not in el.texto:
                    c56.e(f"{fig}: la zona {cid} no lleva su nombre en texto (el color nunca va solo)")
        dibujado[fig] = presentes
        flujos_en[fig] = flujos_fig
        for r in ROLES:
            if r not in roles:
                c55.e(f"{fig}: falta el bloque «{r}»", "Diagrama.titulo/leyenda/panel en infra/gen/drawio.py")
        sin_panel = sorted(presentes - panel_comps)
        if fig != "FIG-1.1" and sin_panel:
            c55.e(f"{fig}: el panel no explica {', '.join(sin_panel)}")

    # cobertura contra el campo `figuras`
    for c in x.componentes.values():
        esperadas = set(c["figuras"])
        for fig in FIGURAS:
            if fig not in dibujado:
                continue
            if fig in esperadas and c["id"] not in dibujado[fig]:
                c51.e(f"{c['id']} falta en {fig} (campo `figuras`)", "Añádalo a la disposición de la figura en drawio.py")
            if fig not in esperadas and c["id"] in dibujado[fig]:
                c51.e(f"{c['id']} aparece en {fig}, que no está en su campo `figuras`",
                      "Quítelo de la figura o registre el cambio en CAMBIOS-INVENTARIO.md")
        faltan = x.figuras_requeridas(c["id"]) - esperadas
        if faltan:
            c51.w(f"{c['id']}: es extremo directo de flujos de {', '.join(sorted(faltan))} pero esa figura no está en `figuras`")

    # flujos: 5.5a ∪ 5.5b
    for fig in ("FIG-5.5a", "FIG-5.5b"):
        if fig not in flujos_en:
            continue
        esperado = set(x.flujos_de_figura(fig))
        for fid in sorted(esperado - flujos_en[fig], key=lambda s: int(s[1:])):
            c54.e(f"{fig}: falta {fid}")
        for fid in sorted(flujos_en[fig] - esperado, key=lambda s: int(s[1:])):
            c54.e(f"{fig}: dibuja {fid}, asignado a {x.flujos[fid].get('figura') or 'ninguna figura'}")
    sin_figura = sorted((f for f in x.flujos if not x.flujos[f].get("figura")), key=lambda s: int(s[1:]))
    cobertura = {
        "fuente": "infra/inventory.yaml (campo figuras de cada componente)",
        "figuras": FIGURAS,
        "componentes": {c: sorted(f for f in FIGURAS if c in dibujado.get(f, set())) for c in x.componentes},
        "flujos": {f: sorted(fig for fig in flujos_en if f in flujos_en[fig]) for f in x.flujos},
        "agrupados": {f: sorted(v) for f, v in agrupados.items()},
        "flujos_sin_figura": sin_figura,
    }
    return chequeos, cobertura


def _escribir_si_cambia(ruta: Path, texto: str) -> None:
    """No toca el archivo si el contenido no cambia (la matriz XLSX compara su fecha con la del JSON: V-62)."""
    if not ruta.exists() or ruta.read_text(encoding="utf-8") != texto:
        ruta.write_text(texto, encoding="utf-8", newline="\n")


def escribir_informe(x: Infra, chequeos: list[Chequeo], cob: dict) -> None:
    _escribir_si_cambia(INFORME_JSON, json.dumps(cob, ensure_ascii=False, indent=2) + "\n")
    cab = "| Componente | Crit. | " + " | ".join(f.replace("FIG-", "") for f in FIGURAS) + " | Total |"
    sep = "|---|---|" + "---|" * len(FIGURAS) + "---|"
    filas = []
    for cid, figs in cob["componentes"].items():
        celdas = ["✔" if f in figs else "" for f in FIGURAS]
        filas.append(f"| {cid} | {x.componentes[cid]['criticidad']} | " + " | ".join(celdas) + f" | {len(figs)} |")
    por_fig = "| Figura | Componentes | Flujos F-nn |\n|---|---|---|\n" + "\n".join(
        f"| {f} | {sum(1 for v in cob['componentes'].values() if f in v)} | "
        f"{', '.join(k for k, v in cob['flujos'].items() if f in v) or '—'} |" for f in FIGURAS)
    estado = "\n".join(f"| {c.id} | {c.titulo} | {c.estado} | {len(c.hallazgos)} |" for c in chequeos)
    detalle = "\n".join(f"- **{c.id}** [{h.nivel}] {h.mensaje}" + (f" — {h.corregir}" if h.corregir else "")
                        for c in chequeos for h in c.hallazgos) or "Sin hallazgos."
    md = f"""# Cobertura componente × figura (P3)

Generado por `infra/gen/drawio_check.py` desde `entregables/CE0311/diagramas/*.drawio`. No editar a mano.
Un componente cuenta como presente si tiene caja propia con `celeris_id`. Los que un bloque de FIG-1.1 agrupa
(`celeris_incluye`) se listan aparte: la vista ejecutiva no los dibuja uno por uno.

## Resultado de V-50…V-56

| ID | Chequeo | Estado | Hallazgos |
|---|---|---|---|
{estado}

{detalle}

## Por figura

{por_fig}

Agrupados en bloques de FIG-1.1: {', '.join(cob['agrupados'].get('FIG-1.1', [])) or 'ninguno'}.

Flujos sin figura asignada (no se dibujan): {', '.join(cob['flujos_sin_figura']) or 'ninguno'}.

## Matriz componente × figura

{cab}
{sep}
{chr(10).join(filas)}
"""
    _escribir_si_cambia(INFORME_MD, md)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=str(DIR))
    a = ap.parse_args(argv)
    x = Infra.cargar()
    chequeos, cob = comprobar(x, Path(a.dir))
    escribir_informe(x, chequeos, cob)
    for c in chequeos:
        print(f"{c.id} {c.estado:<11} {c.titulo}")
        for h in c.hallazgos:
            print(f"    [{h.nivel}] {h.mensaje}")
    print(f"informe: {INFORME_MD.relative_to(RAIZ)}")
    return 1 if any(c.estado == "FALLA" for c in chequeos) else 0


if __name__ == "__main__":
    sys.exit(main())
