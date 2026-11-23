"""Gancho V-80+ — Informe DOCX/PDF (H3): 11 secciones, sin texto guía, IDs vigentes, IP del inventario, figuras y evidencias.

Lee entregables/CE0311/Informe_Diseno_Red_v<versión>.docx y .pdf (los genera docs/infra/e1/build_informe.py con `make informe`):
    V-80  DOCX y PDF existen y abren; el PDF y docs/infra/e1/informe-paginas.json corresponden al mismo commit de la fuente.
    V-81  Las 11 secciones de la plantilla, en orden, con todas sus subsecciones y contenido bajo cada título.
    V-82  Ningún texto guía de la plantilla, marcador «[ Espacio para diagrama…», «____» ni red de ejemplo 192.168.x.x.
    V-83  Ningún ID retirado en v0.4 (componente, zona, flujo o prueba), salvo en una frase que diga que está retirado.
    V-84  Toda IP o red citada está en el inventario (o es de documentación RFC 5737 y figura en él).
    V-85  7 figuras: una imagen por figura de trazabilidad.yaml, con su leyenda exacta y una frase «Qué observar».
    V-86  Cifras repetidas coherentes con la fuente: número de VLAN, PCs, laboratorios, resultados y mediciones del Modo L.
    V-87  Evidencia por criterio de la rúbrica (R1–R8): secciones con contenido, figuras y pruebas citadas en el texto.
    V-88  Marcas [COMPLETAR] pendientes — advertencia: datos que el equipo debe completar antes de entregar.
    V-89  Control de versiones y portada citan la versión del inventario y el commit actual de la fuente.
"""
import ipaddress
import json
import re
import sys
from pathlib import Path

GRUPO = "P5"
PRIMER_ID = "V-80"
DESCRIPCION = "Informe DOCX: 11 secciones, tablas generadas del inventario, figuras y leyendas"

_INFRA = Path(__file__).resolve().parents[1]
_E1 = _INFRA.parent / "docs" / "infra" / "e1"
for _p in (str(_INFRA), str(_INFRA / "gen"), str(_E1)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

GENERAR = "make informe (python docs/infra/e1/build_informe.py --pdf)"
RFC5737 = [ipaddress.ip_network(n) for n in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")]
IP_RE = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})(/\d{1,2})?(?![\d.]*\d)")


def _texto(e) -> str:
    return "".join(e.xpath(".//w:t/text()"))


def _cuerpo(doc):
    """[(sección, texto)] en orden de documento, incluidas las celdas de tabla; sección = ID del último título 1/2."""
    from docx.oxml.ns import qn
    actual, out, titulos = "portada", [], []
    # Word en español guarda los IDs de estilo localizados («Ttulo1»): se resuelven por el nombre interno.
    nombres = {st.style_id: st.name.replace(" ", "") for st in doc.styles}
    for e in doc.element.body.iterchildren():
        if e.tag == qn("w:p"):
            estilo = e.find(qn("w:pPr") + "/" + qn("w:pStyle"))
            nombre = nombres.get(estilo.get(qn("w:val")), "") if estilo is not None else ""
            t = _texto(e).strip()
            if nombre in ("Heading1", "Heading2") and t:
                m = re.match(r"^(\d+(?:\.\d+)?)\.? ", t)
                actual = m.group(1) if m else ("anexo-" + t.split(".")[0].split()[-1] if t.startswith("Anexo") else t)
                titulos.append((nombre, t, actual))
                continue
            out.append((actual, t))
        elif e.tag == qn("w:tbl"):
            for fila in e.iter(qn("w:tr")):
                out.append((actual, " | ".join(_texto(c).strip() for c in fila.iter(qn("w:tc")))))
    return out, titulos


def _ips_inventario(infra) -> tuple[set[str], list]:
    """Cadenas IP/CIDR que aparecen en los tres YAML y las redes que declaran."""
    texto = "\n".join((infra.raiz / "infra" / f).read_text(encoding="utf-8")
                      for f in ("inventory.yaml", "pruebas.yaml", "trazabilidad.yaml"))
    tokens = {m.group(1) + (m.group(2) or "") for m in IP_RE.finditer(texto)}
    redes = []
    for t in tokens:
        if "/" in t:
            try:
                redes.append(ipaddress.ip_network(t, strict=False))
            except ValueError:
                pass
    return tokens, redes


def run(infra):
    from docx import Document
    from validate import E, Resultado, W, estado_de

    import build_informe as bi
    from drawio import commit_fuente

    ruta = bi.SALIDA / bi.nombre_docx(infra)
    pdf = ruta.with_suffix(".pdf")
    rel = ruta.relative_to(infra.raiz).as_posix()
    res = []

    def resultado(cid, titulo, hs, detalle=""):
        res.append(Resultado(cid, titulo, estado_de(hs), hs, detalle))

    # ------------------------------------------------------------------ V-80
    h = []
    try:
        doc = Document(str(ruta))
    except Exception as exc:  # noqa: BLE001 - inexistente o corrupto
        resultado("V-80", "Informe: DOCX y PDF", [E(f"{rel} no existe o no abre: {exc.__class__.__name__}", GENERAR)])
        return res
    commit = commit_fuente()
    paginas = None
    if not pdf.exists():
        h.append(E(f"Falta {pdf.relative_to(infra.raiz).as_posix()}", GENERAR))
    else:
        try:
            from pypdf import PdfReader
            paginas = len(PdfReader(str(pdf)).pages)
        except ImportError:
            pass
        except Exception as exc:  # noqa: BLE001
            h.append(E(f"El PDF no abre: {exc!r}", GENERAR))
        if pdf.stat().st_mtime + 1 < ruta.stat().st_mtime:
            h.append(W("El PDF es anterior al DOCX: puede no reflejar la última versión", GENERAR))
    info = {}
    if bi.PAGINAS_JSON.exists():
        info = json.loads(bi.PAGINAS_JSON.read_text(encoding="utf-8"))
        if info.get("commit_fuente") != commit:
            h.append(E(f"informe-paginas.json es del commit {info.get('commit_fuente')}, la fuente está en {commit}", GENERAR))
    else:
        h.append(W("Falta docs/infra/e1/informe-paginas.json (páginas por sección)", GENERAR))
    resultado("V-80", "Informe: DOCX y PDF existen, abren y son del commit actual", h,
              f"{rel}; PDF {paginas or '?'} páginas; motor {info.get('motor', '?')}")

    cuerpo, titulos = _cuerpo(doc)
    texto_total = "\n".join(t for _, t in cuerpo) + "\n" + "\n".join(t for _, t, _ in titulos)
    por_seccion: dict[str, str] = {}
    for s, t in cuerpo:
        por_seccion[s] = por_seccion.get(s, "") + "\n" + t

    # ------------------------------------------------------------------ V-81
    h = []
    esperados = [f"{s['id']}. {s['titulo']}" if "." not in s["id"] else f"{s['id']} {s['titulo']}"
                 for s in infra.traz["docx_secciones"]]
    reales = [t for _, t, sid in titulos if re.match(r"^\d", t)]
    if reales != esperados:
        faltan = [t for t in esperados if t not in reales]
        sobran = [t for t in reales if t not in esperados]
        h.append(E(f"Títulos de sección distintos de la plantilla. Faltan: {faltan or '—'}; sobran: {sobran or '—'}"
                   + ("" if faltan or sobran else "; el orden no coincide"), GENERAR))
    n1 = sum(1 for nombre, t, _ in titulos if nombre == "Heading1" and re.match(r"^\d+\. ", t))
    if n1 != 11:
        h.append(E(f"El informe tiene {n1} secciones numeradas de nivel 1; la plantilla exige 11"))
    for s in infra.traz["docx_secciones"]:
        hijos = [x for x in infra.traz["docx_secciones"] if x["id"].startswith(s["id"] + ".")]
        if hijos:
            continue
        if len(por_seccion.get(s["id"], "").strip()) < 150:
            h.append(E(f"La sección {s['id']} ({s['titulo']}) no tiene contenido suficiente", "Completar docs/infra/e1/informe/"))
    resultado("V-81", "Informe: 11 secciones de la plantilla, en orden y con contenido", h, f"{len(reales)} títulos de sección")

    # ------------------------------------------------------------------ V-82
    h = []
    plantilla = Document(str(bi.PLANTILLA))
    guia = set()
    cuerpo_p, _ = _cuerpo(plantilla)
    for s, t in cuerpo_p:
        if s == "portada" or len(t) <= 40:
            continue
        # Lo que la plantilla prescribe y el informe debe conservar: leyendas de figura y cabeceras de tabla.
        if t.startswith("Figura ") or (" | " in t and all(len(c) < 40 for c in t.split(" | "))):
            continue
        guia.add(t)
    restos = sorted({g[:70] + "…" for g in guia if g in texto_total})
    if restos:
        h.append(E(f"{len(restos)} párrafos o filas de texto guía de la plantilla siguen en el informe: {restos[:3]}", GENERAR))
    for marca in ("[ Espacio para diagrama", "____", "Plantilla y guía de estructura", "Esta tabla se actualiza automáticamente"):
        if marca in texto_total:
            h.append(E(f"Queda el marcador de plantilla «{marca}»", GENERAR))
    if re.search(r"\b192\.168\.\d", texto_total):
        h.append(E("Aparece una red 192.168.x.x de ejemplo: el plan usa 10.20.0.0/16 y 10.30.0.0/16", GENERAR))
    resultado("V-82", "Informe: sin texto guía ni marcadores de la plantilla", h, f"{len(guia)} textos guía comprobados")

    # ------------------------------------------------------------------ V-83
    h = []
    retirados = {**infra.componentes_retirados, **infra.zonas_retiradas, **infra.flujos_retirados, **infra.pruebas_retiradas}
    encontrados = {}
    for rid in retirados:
        for m in re.finditer(rf"(?<![\w-]){re.escape(rid)}(?![\w-])", texto_total):
            contexto = texto_total[max(0, m.start() - 90): m.end() + 90]
            if "retir" in contexto.lower():
                continue
            encontrados.setdefault(rid, contexto.replace("\n", " ").strip())
    for rid, ctx in sorted(encontrados.items()):
        h.append(E(f"ID retirado en v0.4 citado como vigente: {rid} («…{ctx[:110]}…»)",
                   "Quitarlo del texto o indicar que está retirado"))
    resultado("V-83", "Informe: ningún ID retirado en v0.4 presentado como vigente", h, f"{len(retirados)} IDs retirados buscados")

    # ------------------------------------------------------------------ V-84
    h = []
    tokens, redes = _ips_inventario(infra)
    citadas = {m.group(1) + (m.group(2) or "") for m in IP_RE.finditer(texto_total)}
    fuera = []
    for c in sorted(citadas):
        if c in tokens:
            continue
        try:
            obj = ipaddress.ip_network(c, strict=False) if "/" in c else ipaddress.ip_address(c)
        except ValueError:
            fuera.append(f"{c} (no es una IP válida)")
            continue
        if "/" not in c and any(obj in r for r in redes if r.prefixlen >= 16):
            if any(obj in r for r in RFC5737) and c not in tokens:
                fuera.append(f"{c} (RFC 5737 sin asignar en el inventario)")
            continue  # host dentro de una red del inventario (p. ej., gateway .1 o un rango de laboratorio)
        fuera.append(c)
    for c in fuera:
        h.append(E(f"IP o red que no está en el inventario: {c}", "Usar la del inventario o registrar CI-nn"))
    resultado("V-84", "Informe: toda IP o red citada coincide con el inventario", h, f"{len(citadas)} IP/redes distintas citadas")

    # ------------------------------------------------------------------ V-85
    h = []
    imagenes = len(doc.inline_shapes)
    figs = infra.traz["figuras"]
    if imagenes != len(figs):
        h.append(E(f"El informe tiene {imagenes} imágenes; trazabilidad.yaml declara {len(figs)} figuras", GENERAR))
    lineas = [t for _, t in cuerpo]
    for f in figs:
        if f["leyenda"] not in lineas:
            h.append(E(f"Falta la leyenda de {f['id']}: «{f['leyenda']}»", GENERAR))
            continue
        i = lineas.index(f["leyenda"])
        if not (i + 1 < len(lineas) and lineas[i + 1].startswith("Qué observar")):
            h.append(E(f"{f['id']} no tiene la frase «Qué observar» bajo su leyenda", "Revisar {{figura:…}} en el texto"))
    resultado("V-85", "Informe: 7 figuras con leyenda y «qué observar»", h, f"{imagenes} imágenes")

    # ------------------------------------------------------------------ V-86
    h = []
    d = bi.datos(infra)
    reglas = [
        (r"\b(\d+) VLAN\b", {d["n_vlan"]}, "VLAN internas"),
        (r"\b(\d+) PCs\b", {d["n_pcs"], d["n_pcs_lab"]}, "PCs (por laboratorio o en total)"),
        (r"\b(\d+) pruebas PASA\b", {d["l_pasa"]}, "pruebas PASA del Modo L"),
        (r"\b(\d+) NO_APLICA\b", {d["l_no_aplica"]}, "pruebas NO_APLICA del Modo L"),
        (r"\b(\d+) componentes\b", {d["n_componentes"], d["n_retirados"]}, "componentes vigentes o retirados"),
    ]
    for patron, validos, que in reglas:
        malos = sorted({m.group(1) for m in re.finditer(patron, texto_total)} - validos)
        if malos:
            h.append(E(f"Cifra de {que} incoherente: {', '.join(malos)} (la fuente da {' o '.join(sorted(validos))})",
                       "Usar {{dato:…}} en el texto"))
    for clave, que in (("t05", "convergencia de la VPN (T05)"), ("t09", "conmutación a EDGE02 (T09)")):
        if d[clave] not in texto_total:
            h.append(E(f"La medición de {que}, {d[clave]}, no aparece en el informe", "Usar {{dato:" + clave + "}}"))
        otro = re.findall(rf"{clave.upper()}[^.]{{0,60}}?(\d+,\d) s", texto_total)
        malos = sorted(set(otro) - {d[clave].split()[0]})
        if malos:
            h.append(E(f"Otra cifra para {que}: {', '.join(malos)} s", "Usar {{dato:" + clave + "}}"))
    resultado("V-86", "Informe: cifras repetidas coherentes con la fuente", h,
              f"{d['n_vlan']} VLAN · {d['n_componentes']} componentes · T05 {d['t05']} · T09 {d['t09']}")

    # ------------------------------------------------------------------ V-87
    h = []
    cubiertos = []
    citadas_t = set(re.findall(r"\bT\d{2}\b", texto_total))
    for rid, r in infra.rubrica.items():
        falta_r = []
        for ev in r["evidencias"]:
            t, ref = ev["tipo"], ev["ref"]
            if t == "seccion_docx" and len(por_seccion.get(ref, "").strip()) < 150 and not any(
                    k.startswith(ref + ".") and len(v.strip()) >= 150 for k, v in por_seccion.items()):
                h.append(E(f"{rid}: la sección {ref} no tiene contenido", "Completar docs/infra/e1/informe/"))
                falta_r.append(ref)
            elif t == "figura" and ref not in {f["id"] for f in figs if f["leyenda"] in lineas}:
                h.append(E(f"{rid}: falta la figura {ref}", GENERAR))
                falta_r.append(ref)
            elif t == "prueba" and ref in infra.pruebas and ref not in citadas_t:
                h.append(W(f"{rid}: la prueba {ref} es evidencia del criterio y no se cita en el informe"))
                falta_r.append(ref)
        if not falta_r:
            cubiertos.append(rid)
    resultado("V-87", "Informe: evidencia citada para cada criterio de la rúbrica", h,
              f"criterios con toda su evidencia: {', '.join(cubiertos) or 'ninguno'}")

    # ------------------------------------------------------------------ V-88
    pendientes = sorted(set(re.findall(r"\[COMPLETAR[^\]]*\]", texto_total)))
    resultado("V-88", "Informe: marcas [COMPLETAR] pendientes",
              [W(f"Pendiente: {p}", "Completar antes de entregar") for p in pendientes], f"{len(pendientes)} pendientes")

    # ------------------------------------------------------------------ V-89
    h = []
    version = infra.inv["meta"]["inventario_version"]
    fila = next((t for s, t in cuerpo if t.startswith(f"{version} |")), None)
    if fila is None:
        h.append(E(f"El control de versiones no tiene una fila para la versión {version}", GENERAR))
    elif f"commit {commit}" not in fila:
        h.append(E(f"El control de versiones no cita el commit actual de la fuente ({commit})", GENERAR))
    portada = " ".join(t for s, t in cuerpo if s == "portada")
    if f"commit {commit}" not in portada or f"Versión {version}" not in portada:
        h.append(E(f"La portada no cita «Versión {version}» y el commit {commit}", GENERAR))
    resultado("V-89", "Informe: control de versiones con versión del inventario y commit", h, f"v{version} · commit {commit}")
    return res
