"""Gancho V-95+ — Informe DOCX/PDF del Entregable 2 (CE0331), al estilo de V-80.

Lee entregables/CE0331/Informe_Centro_Datos_v<versión>.docx y .pdf (los genera docs/infra/e2/build_informe.py con `make informe-dc`):
    V-95  DOCX y PDF existen y abren; la huella de infra/centro_datos.yaml e inventory.yaml es la del informe generado.
    V-96  Las 12 secciones de la plantilla, en orden, con todas sus subsecciones y contenido bajo cada título; anexos presentes.
    V-97  Ningún texto guía de la plantilla, marcador «[ Espacio para diagrama…» ni «____»; ningún ID retirado en v0.4 presentado
          como vigente; toda IP o red citada existe en el inventario.
    V-98  Figuras: DC-0…DC-3 y FIG-5.4 (la de CE0311, sin cambios), cada una con su leyenda exacta y una frase «Qué observar».
    V-99  Cifras del texto = cálculo de la fuente (vCPU, RAM, disco, núcleos, holgura, costo); evidencia por criterio de la rúbrica
          (criterios 1 a 8); marcas [COMPLETAR] pendientes (advertencia).
"""
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

GRUPO = "E2"
PRIMER_ID = "V-95"
DESCRIPCION = "Informe del centro de datos: DOCX/PDF, 12 secciones, sin texto guía, figuras con leyenda y cifras coherentes con la fuente"

_INFRA = Path(__file__).resolve().parents[1]
for _p in (str(_INFRA), str(_INFRA / "gen")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

GENERAR = "make informe-dc (python docs/infra/e2/build_informe.py --pdf)"
IP_RE = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})(/\d{1,2})?(?![\d.]*\d)")


def _modulo(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = m
    spec.loader.exec_module(m)
    return m


def run(infra):
    from docx import Document
    from validate import E, Resultado, W, estado_de

    import centro_datos as cdm
    from drawio_dc import huella_dc

    cd = cdm.CentroDatos.cargar(infra)
    raiz = infra.raiz
    v80 = _modulo("checks_v80_para_e2", raiz / "infra" / "checks" / "v80_docx.py")
    bi = _modulo("e2_build_informe", raiz / "docs" / "infra" / "e2" / "build_informe.py")
    ruta = bi.SALIDA / bi.nombre_docx(cd)
    pdf = ruta.with_suffix(".pdf")
    rel = ruta.relative_to(raiz).as_posix()
    res = []

    def resultado(cid, titulo, hs, detalle=""):
        res.append(Resultado(cid, titulo, estado_de(hs), hs, detalle))

    h = []
    try:
        doc = Document(str(ruta))
    except Exception as exc:  # noqa: BLE001
        resultado("V-95", "Informe DC: DOCX y PDF", [E(f"{rel} no existe o no abre: {exc.__class__.__name__}", GENERAR)])
        return res + [Resultado(f"V-{n}", "Omitido: V-95 falló", "FALLA", [E("Sin informe no se evalúa")]) for n in range(96, 100)]
    paginas = None
    if not pdf.exists():
        h.append(E(f"Falta {pdf.relative_to(raiz).as_posix()}", GENERAR))
    else:
        try:
            import pymupdf
            paginas = len(pymupdf.open(str(pdf)))
        except ImportError:
            try:
                from pypdf import PdfReader
                paginas = len(PdfReader(str(pdf)).pages)
            except Exception:  # noqa: BLE001
                pass
        except Exception as exc:  # noqa: BLE001
            h.append(E(f"El PDF no abre: {exc!r}", GENERAR))
    info = {}
    if bi.PAGINAS_JSON.exists():
        info = json.loads(bi.PAGINAS_JSON.read_text(encoding="utf-8"))
        if info.get("huella_fuente") != huella_dc():
            h.append(E("centro_datos.yaml o inventory.yaml cambiaron después de generar el informe (la huella no coincide)", GENERAR))
        if info.get("paginas") and paginas and info["paginas"] != paginas:
            h.append(W(f"El PDF tiene {paginas} páginas y el registro dice {info['paginas']}", GENERAR))
    else:
        h.append(W("Falta docs/infra/e2/informe-paginas.json", GENERAR))
    resultado("V-95", "Informe DC: DOCX y PDF existen, abren y son de la fuente actual", h, f"{rel}; PDF {paginas or '?'} páginas; motor {info.get('motor', '?')}")

    cuerpo, titulos = v80._cuerpo(doc)
    texto_total = "\n".join(t for _, t in cuerpo) + "\n" + "\n".join(t for _, t, _ in titulos)
    por_seccion: dict[str, str] = {}
    for s, t in cuerpo:
        por_seccion[s] = por_seccion.get(s, "") + "\n" + t
    for s in list(por_seccion):               # una sección incluye el contenido de sus subsecciones (5 ⊃ 5.1, 5.2)
        if re.fullmatch(r"\d+\.\d+", s):
            por_seccion[s.split(".")[0]] = por_seccion.get(s.split(".")[0], "") + por_seccion[s]

    # ---- V-96
    h = []
    plantilla = Document(str(bi.PLANTILLA))
    esperados = [p.text.strip() for p in plantilla.paragraphs if p.style.name in ("Heading 1", "Heading 2") and re.match(r"^\d", p.text.strip())]
    reales = [t for _, t, sid in titulos if re.match(r"^\d", t)]
    if reales != esperados:
        for t in esperados:
            if t not in reales:
                h.append(E(f"Falta el título «{t}»", GENERAR))
        if not h:
            h.append(E("Los títulos no están en el orden de la plantilla", GENERAR))
    for sid in [re.match(r"^(\d+(?:\.\d+)?)", t).group(1) for t in esperados]:
        if len(por_seccion.get(sid, "").strip()) < 150:
            h.append(E(f"La sección {sid} tiene menos de 150 caracteres de contenido", "Escriba el texto en docs/infra/e2/informe/"))
    anexos = [t for _, t, _ in titulos if t.startswith("Anexo")]
    if len(anexos) < 3:
        h.append(W("Menos de 3 anexos", "Anexos A (supuestos y CI), B (rúbrica) y C (validación emulada)"))
    resultado("V-96", "Informe DC: 12 secciones de la plantilla, en orden y con contenido", h, f"{len(reales)} títulos de sección · {len(anexos)} anexos")

    # ---- V-97
    h = []
    guias = []
    for p in plantilla.paragraphs:
        t = p.text.strip()
        if len(t) > 35 and p.style.name not in ("Heading 1", "Heading 2") and not t.startswith(("SGSI", "PROYECTO", "Ingeniería", "Esta tabla", "Figura ")):
            guias.append(t)
    for t in plantilla.tables:
        for fila in t.rows:
            for c in fila.cells:
                if c.text.strip().startswith("[ Espacio"):
                    guias.append(c.text.strip().split("\n")[0])
    for g in guias:
        if any(t.strip() == g for _, t in cuerpo):
            h.append(E(f"Texto guía de la plantilla presente: «{g[:70]}…»", GENERAR))
    for patron in ("[ Espacio para diagrama", "____", "192.168.", "Plantilla y guía de estructura", "{{"):
        if patron in texto_total:
            h.append(E(f"Marcador de plantilla presente: {patron}", GENERAR))
    retirados = [*infra.componentes_retirados, *infra.flujos_retirados, *infra.pruebas_retiradas, *infra.zonas_retiradas]
    for rid in retirados:
        for m in re.finditer(rf"(?<![\w-]){re.escape(rid)}(?![\w-])", texto_total):
            ventana = texto_total[max(0, m.start() - 120):m.end() + 120].lower()
            if not re.search(r"retirad|ya no|sin nas|sin idsa|no hay|v0\.4", ventana):
                h.append(E(f"{rid} (retirado en v0.4) aparece sin decir que está retirado", "Quite el ID o aclare que está retirado"))
                break
    tokens = {m.group(1) + (m.group(2) or "") for f in ("inventory.yaml", "pruebas.yaml", "trazabilidad.yaml", "centro_datos.yaml")
              for m in IP_RE.finditer((raiz / "infra" / f).read_text(encoding="utf-8"))}
    ips = {m.group(1) + (m.group(2) or "") for m in IP_RE.finditer(texto_total)}
    fuera = sorted(i for i in ips if i not in tokens)
    for i in fuera:
        h.append(E(f"{i} figura en el informe y no en el inventario", "Use IP y redes del inventario (RFC 5737 para públicas)"))
    resultado("V-97", "Informe DC: sin texto guía, sin IDs retirados como vigentes, toda IP del inventario", h, f"{len(guias)} textos guía comprobados · {len(ips)} IP/redes distintas citadas")

    # ---- V-98
    h = []
    imagenes = len(doc.inline_shapes)
    leyendas = {f: cd.raw["figuras"][f]["leyenda"] for f in ("DC-0", "DC-1", "DC-2", "DC-3")}
    leyendas["FIG-5.4"] = cd.raw["referencia_hibrida"]["leyenda"]
    textos = [t for _, t in cuerpo]
    for fid, ley in leyendas.items():
        n = sum(1 for t in textos if t.strip() == ley)
        if n != 1:
            h.append(E(f"{fid}: la leyenda «{ley[:50]}…» aparece {n} veces (debe ser 1)", GENERAR))
            continue
        i = next(k for k, t in enumerate(textos) if t.strip() == ley)
        if i + 1 >= len(textos) or not textos[i + 1].strip().startswith("Qué observar"):
            h.append(E(f"{fid}: falta la frase «Qué observar» tras la leyenda", "Agregue {{figura:ID|Qué observar: …}}"))
    if imagenes < len(leyendas):
        h.append(E(f"Hay {imagenes} imágenes y se esperaban {len(leyendas)} (más la portada)", GENERAR))
    png54 = raiz / cd.raw["referencia_hibrida"]["origen"]
    sha = hashlib.sha256(png54.read_bytes()).hexdigest() if png54.exists() else None
    if not png54.exists():
        h.append(E("Falta FIG-5.4.png de CE0311", "Se reutiliza tal cual desde entregables/CE0311/diagramas/"))
    elif info.get("fig54_sha256") and info["fig54_sha256"] != sha:
        h.append(E("FIG-5.4.png cambió después de generar el informe", GENERAR))
    elif not info.get("fig54_sha256"):
        h.append(W("El registro no guarda la huella de FIG-5.4.png", GENERAR))
    resultado("V-98", "Informe DC: figuras DC-0…DC-3 y FIG-5.4 (sin cambios) con leyenda y «Qué observar»", h, f"{imagenes} imágenes · {len(leyendas)} leyendas")

    # ---- V-99
    h = []
    d = bi.datos(infra)
    for clave in ("nucleos_nec", "ram_crec", "disco_tot", "costo_total", "h_cpu", "h_ram", "h_disco", "m_ram", "vcpu_f2", "ram_f2", "disco_f2"):
        if d[clave] not in por_seccion.get("9", "") + por_seccion.get("1", ""):
            h.append(E(f"La cifra «{d[clave]}» ({clave}) no figura en las secciones 1 o 9", GENERAR))
    n_filas = sum(1 for s, t in cuerpo if s == "8" and re.match(r"^(?:[A-Za-z0-9-]+) \| ", t))
    if n_filas < int(d["n_elementos"]):
        h.append(E(f"La matriz del informe tiene {n_filas} filas y debe tener {d['n_elementos']}", GENERAR))
    n_srv = sum(1 for s, t in cuerpo if s == "10" and re.match(r"^CT-\d+ \| ", t))
    if n_srv != len(cd.servicios):
        h.append(E(f"La tabla de continuidad tiene {n_srv} servicios y el YAML {len(cd.servicios)}", GENERAR))
    reglas = {
        "1": (["D-25", "D-19"], "2", "criterio de reparto y caché fuera de AWS"),
        "2": (["vSwitch0", "vSwitch1", "PG-FW-TRUNK", "vmnic0", "vmnic2", "teaming"] + sorted(cd.vm_por_id), "5", "topología física e hipervisor con VM"),
        "3": (["10.30.0.0/16", "10.30.0.0/24", "10.30.10.0/24", "IGW01", "sg-gw", "nacl-private", "t3.micro", "us-east-1", "NAT-DR"], "6", "región, VPC, rutas, SG y NACL"),
        "4": (["10.20.0.0/16", "10.30.0.0/16", "FIG-5.4", "VTI1", "VGW"], "7", "integración con el diseño de red"),
        "5": (["núcleos", "RAM", "t3.micro", "holgura", d["nucleos_nec"], d["ram_crec"]], "9", "dimensionamiento frente al host y a EC2-GW"),
        "6": (["Matriz_Componentes_DC", "V-105"], "8", "matriz al 100 % de lo dibujado"),
        "7": (["RTO", "RPO", "3-2-1-1-0", "ESX01", "T59"], "10", "continuidad, respaldo y punto único de falla"),
    }
    for crit, (palabras, sec, que) in reglas.items():
        faltan = [p for p in palabras if p not in por_seccion.get(sec, "")]
        if faltan:
            h.append(E(f"Criterio {crit} ({que}): la sección {sec} no cita {', '.join(faltan[:5])}", "Complete el texto o la tabla"))
    if d["huella"] not in por_seccion.get("portada", "") + texto_total:
        h.append(E("El control de versiones no cita la huella de la fuente", GENERAR))
    pend = sorted(set(re.findall(r"\[COMPLETAR[^\]]*\]", texto_total)))
    for p in pend:
        h.append(W(f"Marca pendiente: {p}", "Complételo antes de entregar"))
    resultado("V-99", "Informe DC: cifras = cálculo de la fuente y evidencia por cada criterio de la rúbrica", h, f"{len(reglas)} criterios con evidencia comprobada · {len(pend)} pendientes")
    return res
