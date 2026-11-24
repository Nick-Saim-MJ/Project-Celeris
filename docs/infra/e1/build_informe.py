"""Genera el Informe de Análisis y Diseño de Red (CE0311, S1, E1) en DOCX y PDF (H3, `make informe`).

    python docs/infra/e1/build_informe.py [--pdf] [--salida DIR]

Cómo se construye (reproducible):
- Parte de una COPIA de la plantilla docs/fuentes/CE03/S1_E1_Analisis_y_Diseno_de_Red.docx: conserva su portada,
  sus estilos, el campo de la tabla de contenidos y los títulos de las 11 secciones; quita todo el texto guía y las
  tablas de ejemplo.
- El texto de cada sección sale de docs/infra/e1/informe/NN-*.md (sintaxis en informe/README.md). Los preliminares
  (control de versiones, glosario) salen de 00-*.md y los anexos de A…F-*.md.
- Toda tabla con datos de red (VLAN, rangos, rutas, VPN, flujos, componentes, pruebas, matriz, amenazas,
  detecciones, objetivos, trazabilidad, supuestos, ensayo) se genera aquí desde `Infra` (celeris_infra); nunca a mano.
- Las figuras son los PNG de entregables/CE0311/diagramas/ (H1); las de la sección 5 van en páginas apaisadas.
- `--pdf` abre el DOCX en LibreOffice headless o, si no está, en Microsoft Word (COM, Windows): actualiza la tabla de
  contenidos, guarda el DOCX, exporta el PDF y registra en docs/infra/e1/informe-paginas.json el número de páginas y la
  página de cada sección y figura (lo usan V-80+ y la autoevaluación).
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ / "infra"))
sys.path.insert(0, str(RAIZ / "infra" / "gen"))
from celeris_infra import Infra, resultados_mas_recientes  # noqa: E402
from drawio import commit_fuente  # noqa: E402
import xlsx_componentes as gx  # noqa: E402

PLANTILLA = RAIZ / "docs" / "fuentes" / "CE03" / "S1_E1_Analisis_y_Diseno_de_Red.docx"
TEXTO = AQUI / "informe"
DIAGRAMAS = RAIZ / "entregables" / "CE0311" / "diagramas"
SALIDA = RAIZ / "entregables" / "CE0311"
PAGINAS_JSON = AQUI / "informe-paginas.json"
EVIDENCIAS_E = sorted((RAIZ / "evidencias").glob("*-E"))

# Página A4 de la plantilla (twips): márgenes de 2 cm.
A4_CORTO, A4_LARGO, MARGEN = 11906, 16838, 1134
ANCHO_VERTICAL = A4_CORTO - 2 * MARGEN       # 9638
ANCHO_APAISADO = A4_LARGO - 2 * MARGEN        # 14570
CM_TWIPS = 567
COLOR_CABECERA = "1F3864"
TAM_TEXTO = 10.5
TAM_TABLA = 8.5
COMPLETAR = "[COMPLETAR"


FUENTES = ("infra/inventory.yaml", "infra/pruebas.yaml", "infra/trazabilidad.yaml")


def huella_fuente() -> str:
    """SHA-256 del contenido de los tres YAML (finales de línea normalizados). A diferencia del commit, no depende del
    historial de git: el CI clona solo el último commit y ahí `git log` no encuentra el commit real de la fuente."""
    import hashlib
    h = hashlib.sha256()
    for f in FUENTES:
        h.update((RAIZ / f).read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()[:16]


def nombre_docx(x: Infra) -> str:
    return f"Informe_Diseno_Red_v{x.inv['meta']['inventario_version']}.docx"


# ==================================================================================================
# Datos que el texto cita con {{dato:clave}}
# ==================================================================================================
def _coma(v: float) -> str:
    return f"{v:.1f}".replace(".", ",")


def _resultado(r: dict, tid: str) -> dict:
    return next((t for t in (r or {}).get("resultados", []) if t["id"] == tid), {})


def _matriz_pruebas_xlsx() -> str:
    xs = sorted(SALIDA.glob("Matriz_Pruebas_Conectividad_v*.xlsx"),
                key=lambda p: [int(n) for n in re.findall(r"\d+", p.stem.rsplit("_v", 1)[1])])
    return xs[-1].name if xs else "Matriz_Pruebas_Conectividad (pendiente)"


def verificaciones_e() -> dict:
    for d in reversed(EVIDENCIAS_E):
        f = d / "verificaciones.json"
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))
    return {}


def datos(x: Infra) -> dict[str, str]:
    _, r = resultados_mas_recientes(x.raiz)
    res = (r or {}).get("meta", {}).get("resumen", {})
    t05 = _resultado(r, "T05").get("valor_medido", {}).get("convergencia_s")
    t09 = _resultado(r, "T09").get("valor_medido", {}).get("tiempo_de_cambio_s")
    ve = verificaciones_e()
    vr = ve.get("resumen", {})
    s01 = re.search(r"\d+", x.supuestos["S-01"]["valor"]).group(0)
    return {
        "n_lab": str(len(x.inv["rangos_lab"]["laboratorios"])),
        "n_pcs": s01,
        "n_pcs_lab": str(int(s01) // len(x.inv["rangos_lab"]["laboratorios"])),
        "enlace": x.supuestos["S-02"]["valor"],
        "n_vlan": str(sum(1 for z in x.zonas.values() if z["tipo"] == "interna" and z.get("vlan"))),
        "t05": f"{_coma(t05)} s" if t05 is not None else "— (sin medición)",
        "t09": f"{_coma(t09)} s" if t09 is not None else "— (sin medición)",
        "l_pasa": str(res.get("PASA", 0)), "l_falla": str(res.get("FALLA", 0)),
        "l_parcial": str(res.get("PARCIAL", 0)), "l_no_aplica": str(res.get("NO_APLICA", 0)),
        "l_fecha": (r or {}).get("meta", {}).get("fecha", "—"),
        "n_componentes": str(len(x.componentes)),
        "n_retirados": str(len(x.componentes_retirados)),
        "n_pruebas": str(len(x.pruebas)),
        "matriz_xlsx": f"Matriz_Componentes_Red_v{x.inv['meta']['inventario_version']}.xlsx",
        "matriz_pruebas_xlsx": _matriz_pruebas_xlsx(),
        "e_verificaciones": str(len(ve.get("comprobaciones", []))),
        "e_resultado": f"{vr.get('PASA', 0)} PASA y {vr.get('FALLA', 0)} FALLA" if vr else "sin datos",
    }


# ==================================================================================================
# Tablas generadas desde la fuente única: cada función devuelve (cabeceras, filas, anchos en cm, apaisada?)
# ==================================================================================================
def lst(v, sep=", ") -> str:
    v = [str(i) for i in (v or []) if i not in (None, "")]
    return sep.join(v) if v else "—"


def ids(v) -> list[str]:
    def clave(s):
        m = re.match(r"([A-Za-z-]+?)-?(\d+)(\w*)$", s)
        return (m.group(1), int(m.group(2)), m.group(3)) if m else (s, 0, "")
    return sorted(set(v), key=clave)


def proto_txt(f: dict) -> str:
    partes = []
    for p in f.get("protocolos") or []:
        nombre = p["proto"].upper() if p["proto"] != "ipv6" else "IPv6"
        puertos = "/".join(str(n) for n in p.get("puertos") or [])
        partes.append(f"{nombre} {puertos}".strip())
    return ", ".join(partes) or "—"


def t_control_versiones(x, d):
    meta = x.inv["meta"]
    commit = commit_fuente()
    try:
        fecha = subprocess.run(["git", "log", "-1", "--format=%cs", commit], cwd=RAIZ, capture_output=True, text=True,
                               check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        fecha = meta["fecha"]
    return (["Versión", "Fecha", "Fuente (inventario · commit)", "Autores", "Cambios"],
            [[meta["inventario_version"], fecha, f"inventario v{meta['inventario_version']} · commit {commit}",
              gx.autores(), "Primera edición con la arquitectura v0.4: figuras regeneradas (H1), matriz de componentes v"
              f"{meta['inventario_version']} (H2) e informe completo (H3)."]],
            [1.6, 2.2, 4.0, 3.4, 5.8], False)


def t_objetivos(x, d):
    filas = [[o["id"], o["objetivo"], o["indicador"], o["meta"], o["responsable"], lst(o.get("objetivo_proyecto")),
              lst(ids(x.pruebas_de_objetivo(o["id"])))] for o in x.traz["objetivos"]]
    return (["ID", "Objetivo", "Indicador", "Meta", "Responsable", "OB", "Pruebas"], filas,
            [1.3, 2.8, 4.4, 3.0, 2.0, 1.4, 2.1], False)


def t_vlan(x, d):
    orden = sorted([z for z in x.zonas.values() if z["tipo"] in ("interna", "transito", "reservada", "externa") and
                    (z.get("cidr") or z.get("vlan"))], key=lambda z: (z.get("vlan") is None and z["tipo"] != "transito",
                                                                     z.get("vlan") or 0, z["id"]))
    filas = []
    for z in orden:
        filas.append([str(z["vlan"]) if z.get("vlan") is not None else "—", z["id"], z.get("cidr") or "—",
                      z.get("gateway") or "—",
                      f"{z['hosts_utiles']:,}".replace(",", " ") if z.get("hosts_utiles") is not None else "—",
                      z["proposito"]])
    return (["VLAN", "Zona", "Red / CIDR", "Gateway", "Hosts útiles", "Propósito"], filas,
            [1.2, 2.3, 2.9, 2.3, 1.6, 6.7], False)


def t_rangos_lab(x, d):
    rl = x.inv["rangos_lab"]
    filas = [[l["id"], l["cidr"], str(l["hosts_utiles"]), "Habilitado" if l.get("habilitado") else "Deshabilitado"]
             for l in rl["laboratorios"]]
    filas.append([rl["reserva"]["id"], rl["reserva"]["cidr"], str(rl["reserva"]["hosts_utiles"]), rl["reserva"]["descripcion"]])
    inf = rl["infraestructura"]
    filas.append([inf["id"], inf["cidr"], "254", inf["descripcion"]])
    return (["Rango", "Red", "Hosts útiles", "Estado / uso"], filas, [3.0, 3.6, 2.2, 8.2], False)


def t_rutas_aws(x, d):
    sup = {s["id"]: s["cidr"] for s in x.inv["supernets"]}
    saltos = {"internet_gateway": "Internet Gateway", "vgw": "VGW (VPN)", "gateway_endpoint_s3": "Gateway Endpoint de S3"}
    filas = []
    for t in x.inv["aws"]["tablas_de_rutas"]:
        for r in t["rutas"]:
            dest = r["destino"]
            dest = sup.get(dest.split(":", 1)[1], dest) if dest.startswith("supernet:") else (
                "Prefijo administrado de S3" if dest == "prefijo_s3" else dest)
            salto = r["salto"]
            salto = f"{salto.split(':', 1)[1]} (instancia NAT temporal)" if salto.startswith("nat:") else saltos.get(salto, salto)
            nota = r.get("nota", "")
            if r.get("solo_en_simulacro"):
                nota = (nota + "; " if nota else "") + "solo durante el simulacro T59"
            filas.append([t["id"], lst(t["subredes"]), dest, salto, nota or "—"])
    return (["Tabla", "Subredes", "Destino", "Siguiente salto", "Nota"], filas, [2.4, 2.6, 3.6, 4.2, 4.2], False)


def t_servicios_base(x, d):
    sb = x.inv["servicios_base"]
    filas = [
        ["DHCP", sb["dhcp"]["diseno"], sb["dhcp"]["por_que"], lst(sb["dhcp"].get("controles"))],
        ["DNS", f"{sb['dns']['servidor']['software']} en {sb['dns']['servidor']['componente']} "
                f"({sb['dns']['servidor']['ip']}), DNSSEC; hacia arriba {sb['dns']['hacia_arriba']}", sb["dns"]["por_que"],
         lst(sb["dns"]["flujos"] + sb["dns"]["pruebas"])],
        ["PAC", f"{sb['pac']['url']}; {sb['pac']['distribucion']}; lo sirven {sb['pac']['servido_por']}",
         sb["pac"]["por_que"], lst(sb["pac"]["flujos"] + sb["pac"]["pruebas"])],
        ["NTP", f"{sb['ntp']['servidor']['software']} en {sb['ntp']['servidor']['componente']}; hacia arriba "
                f"{sb['ntp']['hacia_arriba']}; clientes {sb['ntp']['clientes']}", sb["ntp"]["por_que"],
         lst(sb["ntp"]["flujos"] + sb["ntp"]["pruebas"])],
        ["IPv6", f"{sb['ipv6']['postura']} ({lst(sb['ipv6']['controles'])})", sb["ipv6"]["por_que"],
         lst(sb["ipv6"]["flujos"] + sb["ipv6"]["pruebas"])],
        ["DNS cifrado", f"{sb['dns_cifrado']['dot']}; {sb['dns_cifrado']['doh']}", sb["dns_cifrado"]["por_que"],
         lst(sb["dns_cifrado"]["flujos"] + sb["dns_cifrado"]["pruebas"])],
        ["Wi-Fi de estudiantes", sb["wifi"]["diseno"], sb["wifi"]["por_que"], lst(sb["wifi"]["flujos"] + sb["wifi"]["pruebas"])],
    ]
    return (["Servicio", "Diseño", "Por qué", "Flujos / pruebas / controles"], filas, [2.2, 6.6, 5.4, 2.8], False)


def t_zonas_confianza(x, d):
    filas = []
    for z in x.zonas.values():
        if not z.get("confianza") or z["tipo"] in ("reservada", "perimetro", "transito"):
            continue
        conf = z["confianza"] + (f" ({z['confianza_nota']})" if z.get("confianza_nota") else "")
        if z.get("cambio"):
            conf += f" [{z['cambio']}]"
        filas.append([z["id"], str(z["vlan"]) if z.get("vlan") is not None else "—", conf, z.get("regla_diseno") or "—",
                      z.get("admin") or "—"])
    return (["Zona", "VLAN", "Confianza", "Regla de diseño", "Administra"], filas, [2.4, 1.2, 3.0, 7.6, 2.8], False)


def t_defensa(x, d):
    return (["Capa", "Controles"], [[c["capa"], c["controles"]] for c in x.traz["defensa_profundidad"]], [4.0, 13.0], False)


def t_vpn(x, d):
    v = x.inv["vpn"]
    on, aws = v["extremo_onpremise"], v["extremo_aws"]
    tun = "; ".join(f"{t['id']} {t['rol']} {t['red_interna']}" + (" (AS-path prepending)" if t.get("bgp_as_path_prepending") else "")
                    for t in v["tuneles"])
    f1, f2, b = v["fase1"], v["fase2"], v["bgp"]
    filas = [
        ["Dispositivo", on["dispositivo"], aws["dispositivo"]],
        ["IP pública", f"{on['ip_publica']} en {on['ip_publica_en']} ({on['ip_publica_nota']})", aws["ip_publica"]],
        ["IP interna del extremo", on["ip_interna"], "—"],
        ["Identidad IKE", f"{on['identidad_ike']['tipo'].upper()} {on['identidad_ike']['valor']}", "—"],
        ["NAT-T", ("Sí: " + on["nat_t_nota"]) if on["nat_t"] else "No", "Soportado"],
        ["Redes anunciadas", lst(on["redes_anunciadas"]) + f" (futuro: {on['redes_anunciadas_futuro']})", lst(aws["redes_anunciadas"])],
        ["ASN (BGP)", str(on["asn"]), f"{aws['asn']} ({aws['asn_nota']})"],
        ["Tipo de túnel", v["tipo"], "Ídem"],
        ["Túneles e interfaces", tun, "Ídem"],
        ["Ruteo", f"{b['protocolo']}; keepalive {b['keepalive_s']} s, hold {b['hold_s']} s; {b['respaldo']}", "Ídem"],
        ["Fase 1 (IKE)", f"{f1['cifrado']}, PRF {f1['prf']}, DH {f1['dh']}, vida {f1['vida_s']} s", "Ídem"],
        ["Fase 2 (ESP)", f"{f2['cifrado']}, PFS {f2['pfs']}, vida {f2['vida_s']} s", "Ídem"],
        ["DPD", f"{v['dpd']['intervalo_s']} s, acción {v['dpd']['accion']}", "Ídem"],
        ["MTU / MSS", f"MTU {v['mtu']} en las VTI; MSS {v['mss_clamping']}", "—"],
        ["IPv6", v["ipv6"], "—"],
        ["Flujos transportados", lst(v["flujos_sobre_vpn"]), "Ídem"],
        ["Convergencia (meta)", f"≤ {v['convergencia_meta_s']} s medidos (T05); Modo L emulado: {d['t05']}", "—"],
        ["Secretos", v["secretos"], "—"],
    ]
    return (["Parámetro", "Extremo campus (FW01)", "Extremo AWS (VGW)"], filas, [3.2, 8.8, 5.0], False)


def t_flujos(x, d):
    filas = []
    for f in x.flujos.values():
        if f["estado"] != "activo":
            continue
        destino = lst(f["destino"]) + (f" ({f['destino_detalle']})" if f.get("destino_detalle") else "")
        accion = "Bloquear" if f["accion"] != "permitir" else ("Permitir (solo piloto)" if f["modo"] == "piloto" else "Permitir")
        prot = (f.get("proteccion") or {}).get("detalle") or "—"
        filas.append([f["id"], lst(f["origen"]), destino, proto_txt(f), f["proposito"], prot, accion, f.get("regla_fw") or "—"])
    return (["F", "Origen", "Destino", "Protocolo · puerto", "Propósito", "Protección en tránsito", "Acción", "Regla en FW01"],
            filas, [1.0, 2.6, 3.4, 2.6, 3.4, 6.6, 2.0, 4.1], True)


def t_componentes(x, d):
    etiqueta = {"existente": " (existente)", "fuera_de_alcance": " (fuera de alcance)", "temporal": " (temporal)"}
    filas = [[c["id"] + etiqueta.get(c["estado"], ""), gx.ip_planeada(c), ", ".join(c["zonas"]), c["funcion"], c["criticidad"]]
             for c in x.componentes.values()]
    return (["Componente", "IP planeada", "Zona", "Función", "Criticidad"], filas, [3.2, 4.6, 2.6, 5.0, 1.6], False)


def _l(r: dict, tid: str) -> str:
    t = _resultado(r, tid)
    if not t:
        return "sin ensayo"
    out = t["resultado"]
    vm = t.get("valor_medido") or {}
    if tid == "T05" and vm.get("convergencia_s") is not None:
        out += f" ({_coma(vm['convergencia_s'])} s)"
    return out


def t_pruebas_vpn(x, d):
    _, r = resultados_mas_recientes(x.raiz)
    sel = [t for t in x.pruebas.values() if "R3" in t.get("criterios_rubrica", []) or t["categoria"] == "vpn"
           or any("AWS" in c for c in t.get("celdas_matriz", []))]
    filas = [[t["id"], f"{t['nombre']} ({lst(t['origen'] if isinstance(t['origen'], list) else [t['origen']])} → "
                       f"{lst(t['destino'] if isinstance(t['destino'], list) else [t['destino']])})",
              t["resultado_esperado"], lst(t["flujos"]), lst(t["modos"]), _l(r, t["id"])] for t in sel]
    return (["T", "Prueba de conectividad planeada", "Resultado esperado", "Flujos", "Modos", "Modo L (emulado)"], filas,
            [1.1, 6.2, 4.0, 1.8, 1.4, 2.5], False)


def t_fw_interfaces(x, d):
    fw = x.componentes["FW01"]
    filas = []
    for i in fw["ips"]:
        z = x.zonas.get(i["zona"], {})
        nombre = "WAN" if i["interfaz"] == "wan" else (f"VLAN {z.get('vlan')}" if z.get("vlan") else i["interfaz"])
        filas.append([nombre, i["ip"] or "—", i["zona"], i.get("nota") or z.get("proposito") or "—"])
    for t in x.inv["vpn"]["tuneles"]:
        filas.append([t["id"], t["red_interna"], "PERIMETRO", f"Túnel IPsec {t['rol']} hacia el VGW (BGP)"])
    return (["Interfaz", "IP", "Zona", "Uso"], filas, [2.2, 3.2, 2.6, 9.0], False)


def _celda(c: dict) -> str:
    e = c.get("estado")
    if e == "permitido":
        txt = "✔ " + lst(c.get("flujos"))
        if c.get("bloqueados"):
            txt += "; ✖ " + lst(c["bloqueados"])
        return txt
    if e == "denegado":
        return "✖" + (" " + lst(c["bloqueados"]) if c.get("bloqueados") else "")
    return "—"


def t_segmentacion(x, d):
    criticas = x.celdas_denegadas_criticas()
    filas = []
    for (zo, zd), c in x.matriz_esperada().items():
        par = f"{zo}>{zd}"
        if c.get("estado") == "permitido":
            pr = ids(x.pruebas_positivas_de_celda(par, c.get("flujos", [])) + x.pruebas_de_celda(par))
            res = "PERMITIDO solo " + lst(c.get("flujos")) + (f"; BLOQUEADO {lst(c['bloqueados'])}" if c.get("bloqueados") else "")
            filas.append([f"{zo} → {zd}", res + (f" ({c['nota']})" if c.get("nota") else ""), lst(pr)])
        elif c.get("estado") == "denegado" and par in criticas:
            filas.append([f"{zo} → {zd}", f"DENEGADO ({criticas[par]})", lst(ids(x.pruebas_negativas_de_celda(par)))])
    return (["Origen → destino", "Resultado esperado", "Pruebas"], filas, [4.2, 9.4, 3.4], False)


def t_matriz_completa(x, d):
    orden = x.orden_matriz
    m = x.matriz_esperada()
    filas = [[o] + [_celda(m.get((o, dd), {})) for dd in orden] for o in orden]
    return (["Origen ↓ / Destino →"] + orden, filas, [1.4] + [1.0] * len(orden), True)


def t_matriz_notas(x, d):
    filas = [[f"{zo} → {zd}", c["nota"]] for (zo, zd), c in x.matriz_esperada().items() if c.get("nota")]
    return (["Celda", "Nota"], filas, [4.0, 13.0], False)


def t_detecciones(x, d):
    filas = [[t["id"], t["tecnologia"], t["ubicacion_detalle"], t["que_detecta"], lst(t["attack"]),
              f"{t['validacion']['escenario']} ({lst(t['validacion']['pruebas'])})"] for t in x.detecciones.values()]
    return (["DET", "Tecnología", "Ubicación", "Qué detecta", "ATT&CK", "Validación (prueba)"], filas,
            [1.3, 2.8, 2.9, 4.0, 1.8, 4.2], False)


def t_continuidad(x, d):
    filas = []
    for c in x.componentes.values():
        if c["criticidad"] != "Alta" or c["estado"] in ("existente", "fuera_de_alcance"):
            continue
        relevo = gx.relevo_de(x, c)
        filas.append([c["id"], c["si_falla"], lst(relevo) if relevo else "Ninguno (punto único de falla)"])
    return (["Componente (criticidad Alta)", "Si falla: impacto y mitigación", "Otro componente asume su función"], filas,
            [3.2, 10.4, 3.4], False)


def t_amenazas(x, d):
    filas = [[a["id"], a["zona_activo"], "/".join(a["stride"]), a["amenaza"], a["control"], lst(a["iso_27002"]),
              lst(a["componentes"]), lst(a["pruebas"])] for a in x.amenazas.values()]
    return (["AM", "Zona / activo", "STRIDE", "Amenaza", "Control", "ISO/IEC 27002", "Componentes", "Pruebas"], filas,
            [1.2, 2.0, 1.2, 3.4, 3.6, 1.6, 2.4, 1.6], False)


def _traz_od(x, od):
    comps = [c for c in x.componentes.values() if od in c.get("objetivos", [])]
    flujos = [f for f in x.flujos.values() if od in (f.get("objetivos") or [])]
    adr = ids({a for c in comps for a in c.get("adr", [])} | {a for f in flujos for a in (f.get("adr") or [])})
    return comps, flujos, adr


def t_necesidades(x, d):
    filas = []
    for ob in x.traz.get("objetivos_proyecto", []):
        ods = [o["id"] for o in x.traz["objetivos"] if ob["id"] in o.get("objetivo_proyecto", [])]
        filas.append([ob["id"], ob["necesidad"], ob["indicador"], ob["meta"], lst(ods)])
    sin = [o["id"] for o in x.traz["objetivos"] if not o.get("objetivo_proyecto")]
    if sin:
        filas.append(["—", "Sin objetivo del proyecto asignado (D1.6)", "—", "—", lst(sin)])
    return (["OB", "Necesidad", "Indicador", "Meta", "Objetivos de diseño"], filas, [1.3, 3.2, 6.0, 3.0, 3.5], False)


def t_trazabilidad(x, d):
    filas = []
    for o in x.traz["objetivos"]:
        comps, flujos, adr = _traz_od(x, o["id"])
        filas.append([o["id"], o["objetivo"], lst(o.get("objetivo_proyecto")), lst(adr), lst(ids(c["id"] for c in comps)),
                      lst(ids(f["id"] for f in flujos)), lst(ids(x.pruebas_de_objetivo(o["id"])))])
    return (["OD", "Objetivo", "OB", "Decisiones", "Componentes", "Flujos", "Pruebas"], filas,
            [1.2, 2.6, 1.3, 2.6, 3.6, 2.5, 3.2], False)


def t_decisiones(x, d):
    usadas = set()
    for o in x.traz["objetivos"]:
        usadas |= set(_traz_od(x, o["id"])[2])
    filas = [[k, v["decision"]] for k, v in x.decisiones.items() if k in usadas]
    return (["Decisión", "Qué se decidió"], filas, [2.0, 15.0], False)


def t_supuestos(x, d):
    filas = [[k, s["supuesto"], s["valor"], s["validacion"], s.get("responsable") or "—"] for k, s in x.supuestos.items()
             if s.get("estado") != "retirado"]
    retirados = [f"{k} ({s.get('retirado_motivo', 'retirado')}; {s.get('cambio', '')})".replace("; )", ")")
                 for k, s in x.supuestos.items() if s.get("estado") == "retirado"]
    if retirados:
        filas.append(["—", "Supuestos retirados en v0.4 (no aplican)", "; ".join(retirados), "—", "—"])
    return (["S", "Supuesto", "Valor usado", "Cómo validarlo", "Responsable"], filas, [1.3, 4.0, 5.2, 4.2, 2.3], False)


def t_ensayo_l(x, d):
    _, r = resultados_mas_recientes(x.raiz)
    filas = []
    for t in (r or {}).get("resultados", []):
        nota = t.get("motivo") or ""
        if t["resultado"] == "PASA":
            vm = t.get("valor_medido") or {}
            nota = "; ".join(f"{k} = {v}" for k, v in list(vm.items())[:2]) or "—"
        if len(nota) > 160:
            nota = nota[:157].rstrip() + "…"
        filas.append([t["id"], t["nombre"], t["resultado"], lst(t.get("modos")), nota])
    return (["T", "Prueba", "Resultado (emulado)", "Modos", "Medición o motivo"], filas, [1.1, 4.4, 2.2, 1.5, 7.8], False)


TABLAS = {n[2:]: f for n, f in globals().items() if n.startswith("t_") and callable(f)}


# ==================================================================================================
# Utilidades de python-docx / OOXML
# ==================================================================================================
def _run_fmt(run, tam=TAM_TEXTO, negrita=False, cursiva=False, color=None, mono=False):
    run.font.name = "Consolas" if mono else "Calibri"
    rpr = run._r.get_or_add_rPr()
    fuentes = rpr.find(qn("w:rFonts"))
    if fuentes is None:
        fuentes = OxmlElement("w:rFonts")
        rpr.insert(0, fuentes)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fuentes.set(qn(a), "Consolas" if mono else "Calibri")
    run.font.size = Pt(tam)
    run.font.bold = negrita or None
    run.font.italic = cursiva or None
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


INLINE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*)")


def texto_inline(par, texto, tam=TAM_TEXTO, negrita=False, cursiva=False, color=None):
    for trozo in INLINE.split(texto):
        if not trozo:
            continue
        if trozo.startswith("**") and trozo.endswith("**"):
            _run_fmt(par.add_run(trozo[2:-2]), tam, True, cursiva, color)
        elif trozo.startswith("`") and trozo.endswith("`"):
            _run_fmt(par.add_run(trozo[1:-1]), tam * 0.92, negrita, cursiva, color, mono=True)
        elif trozo.startswith("*") and trozo.endswith("*") and len(trozo) > 2:
            _run_fmt(par.add_run(trozo[1:-1]), tam, negrita, True, color)
        else:
            _run_fmt(par.add_run(trozo), tam, negrita, cursiva, color)


def _espaciado(par, antes=0, despues=160):
    pf = par.paragraph_format
    pf.space_before = Pt(antes / 20)
    pf.space_after = Pt(despues / 20)


def _borde(tc_pr):
    b = OxmlElement("w:tcBorders")
    for lado in ("top", "left", "bottom", "right"):
        e = OxmlElement(f"w:{lado}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:space"), "0")
        e.set(qn("w:color"), "808080")
        b.append(e)
    tc_pr.append(b)


def _sombra(tc_pr, color):
    s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear")
    s.set(qn("w:color"), "auto")
    s.set(qn("w:fill"), color)
    tc_pr.append(s)


def _texto(e) -> str:
    """Texto de un elemento OOXML (solo w:t; itertext de python-docx repite el texto)."""
    return "".join(e.xpath(".//w:t/text()"))


_TMP_IMG = Path(tempfile.mkdtemp(prefix="informe-img-"))


def png_reducido(png: Path, ancho_cm: float, dpi: int = 220) -> Path:
    """Copia del PNG a `dpi` para el ancho impreso: el original (escala 3, ~6800 px) haría un DOCX de más de 20 MB."""
    from PIL import Image
    ancho_px = int(ancho_cm / 2.54 * dpi)
    with Image.open(png) as im:
        if im.size[0] <= ancho_px:
            return png
        alto = round(im.size[1] * ancho_px / im.size[0])
        destino = _TMP_IMG / png.name
        im.convert("RGB").resize((ancho_px, alto), Image.LANCZOS).save(destino, optimize=True)
    return destino


class Constructor:
    def __init__(self, x: Infra):
        self.x = x
        self.d = datos(x)
        self.doc = Document(str(PLANTILLA))
        cuerpo = self.doc.element.body
        self.sect_final = cuerpo[-1]
        par = self.doc.paragraphs
        self.ppr_lista = copy.deepcopy(next(p for p in par if p.style.name == "List Paragraph")._p.pPr)
        self.ppr_pie = copy.deepcopy(next(p for p in par if p.text.startswith("Figura 1.1"))._p.pPr)
        # La plantilla da formato directo a sus títulos (Calibri, negrita, 1F3864): se replica en los títulos nuevos.
        h1 = next(p for p in par if p.style.name == "Heading 1" and p.text[:1].isdigit())
        h2 = next(p for p in par if p.style.name == "Heading 2")
        self.fmt_titulo = {1: (copy.deepcopy(h1._p.pPr), copy.deepcopy(h1.runs[0]._r.rPr)),
                           2: (copy.deepcopy(h2._p.pPr), copy.deepcopy(h2.runs[0]._r.rPr))}
        self._fuente_por_defecto()
        self.ancla = None
        self.apaisado_abierto = False
        self.ultimo_fue_figura = False
        self.figuras: list[str] = []
        self.completar: list[str] = []

    # ---------------------------------------------------------------- inserción
    def _mover(self, elemento):
        self.ancla.addnext(elemento)
        self.ancla = elemento
        return elemento

    def parrafo(self, texto="", estilo="Normal", tam=TAM_TEXTO, negrita=False, cursiva=False, color=None, alinear=None,
                despues=160, antes=0):
        p = self.doc.add_paragraph(style=estilo)
        if texto:
            texto_inline(p, self.sustituir(texto), tam, negrita, cursiva, color)
        _espaciado(p, antes, despues)
        if alinear:
            p.alignment = alinear
        self._mover(p._p)
        self.ultimo_fue_figura = False
        return p

    def titulo(self, texto, nivel, salto=False):
        ppr, rpr = self.fmt_titulo[min(nivel, 2)]
        p = self.doc.add_paragraph()
        p._p.insert(0, copy.deepcopy(ppr))
        r = p.add_run(self.sustituir(texto))
        r._r.insert(0, copy.deepcopy(rpr))
        if nivel == 3:
            p.style = self.doc.styles["Heading 3"]
            r.font.size = Pt(11)
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
        if salto:
            p.paragraph_format.page_break_before = True
        self._mover(p._p)
        self.ultimo_fue_figura = False
        return p

    def vineta(self, texto):
        p = self.doc.add_paragraph()
        p._p.insert(0, copy.deepcopy(self.ppr_lista))
        texto_inline(p, self.sustituir(texto))
        self._mover(p._p)
        self.ultimo_fue_figura = False

    def numerado(self, texto):
        p = self.doc.add_paragraph(style="List Paragraph")
        p.paragraph_format.left_indent = Cm(0.9)
        p.paragraph_format.first_line_indent = Cm(-0.5)
        _espaciado(p, 0, 60)
        texto_inline(p, self.sustituir(texto))
        self._mover(p._p)
        self.ultimo_fue_figura = False

    def nota(self, texto):
        p = self.parrafo(texto, cursiva=False, color="1F3864", despues=200, antes=60)
        ppr = p._p.get_or_add_pPr()
        bdr = OxmlElement("w:pBdr")
        izq = OxmlElement("w:left")
        izq.set(qn("w:val"), "single")
        izq.set(qn("w:sz"), "18")
        izq.set(qn("w:space"), "8")
        izq.set(qn("w:color"), "2E74B5")
        bdr.append(izq)
        ppr.append(bdr)
        p.paragraph_format.left_indent = Cm(0.4)

    def tabla(self, cab, filas, anchos_cm, apaisada=False):
        ancho_total = ANCHO_APAISADO if apaisada else ANCHO_VERTICAL
        tw = [int(a * CM_TWIPS) for a in anchos_cm]
        escala = ancho_total / sum(tw)
        tw = [int(w * escala) for w in tw]
        t = self.doc.add_table(rows=1 + len(filas), cols=len(cab))
        tbl = t._tbl
        tblpr = tbl.tblPr
        for tag, val in (("w:tblW", str(sum(tw))),):
            e = OxmlElement(tag)
            e.set(qn("w:w"), val)
            e.set(qn("w:type"), "dxa")
            tblpr.append(e)
        lay = OxmlElement("w:tblLayout")
        lay.set(qn("w:type"), "fixed")
        tblpr.append(lay)
        mar = OxmlElement("w:tblCellMar")
        for lado in ("top", "left", "bottom", "right"):
            e = OxmlElement(f"w:{lado}")
            e.set(qn("w:w"), "60" if lado in ("top", "bottom") else "80")
            e.set(qn("w:type"), "dxa")
            mar.append(e)
        tblpr.append(mar)
        grid = tbl.tblGrid
        for gc, w in zip(grid.findall(qn("w:gridCol")), tw):
            gc.set(qn("w:w"), str(w))
        tam = TAM_TABLA if not apaisada else 7.5
        for i, fila in enumerate([cab] + filas):
            row = t.rows[i]
            if i == 0:
                trpr = row._tr.get_or_add_trPr()
                h = OxmlElement("w:tblHeader")
                h.set(qn("w:val"), "true")
                trpr.append(h)
            cant = OxmlElement("w:cantSplit")
            row._tr.get_or_add_trPr().append(cant)
            for j, valor in enumerate(fila):
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
                lineas = self.sustituir(str(valor)).split("\n")
                p = cel.paragraphs[0]
                for k, linea in enumerate(lineas):
                    if k:
                        p = cel.add_paragraph()
                    _espaciado(p, 0, 0)
                    texto_inline(p, linea, tam, negrita=(i == 0), color="FFFFFF" if i == 0 else None)
        self._mover(tbl)
        p = self.parrafo("", despues=120)
        return p

    def salto_seccion(self, apaisada: bool):
        """Cierra la sección en curso: el sectPr de este párrafo describe las páginas ANTERIORES."""
        previo = self.ancla
        if (previo is not None and previo.tag == qn("w:p") and not _texto(previo) and previo.find(".//" + qn("w:sectPr")) is None
                and previo.find(".//" + qn("w:drawing")) is None and previo.find(".//" + qn("w:br")) is None):
            p_el = previo                       # reutiliza el párrafo separador vacío: evita una página en blanco
        else:
            p_el = None
        p = self.doc.add_paragraph() if p_el is None else None
        ppr = (p._p if p is not None else p_el).get_or_add_pPr()
        s = copy.deepcopy(self.sect_final)
        pg = s.find(qn("w:pgSz"))
        if apaisada:
            pg.set(qn("w:w"), str(A4_LARGO))
            pg.set(qn("w:h"), str(A4_CORTO))
            pg.set(qn("w:orient"), "landscape")
        else:
            pg.set(qn("w:w"), str(A4_CORTO))
            pg.set(qn("w:h"), str(A4_LARGO))
            if qn("w:orient") in pg.attrib:
                del pg.attrib[qn("w:orient")]
        tipo = s.find(qn("w:type"))
        if tipo is not None:
            tipo.set(qn("w:val"), "nextPage")
        ppr.append(s)
        if p is not None:
            self._mover(p._p)

    def figura(self, fid: str, observar: str):
        fig = self.x.figuras[fid]
        png = DIAGRAMAS / f"{fid}.png"
        if not png.exists():
            raise SystemExit(f"Falta {png.relative_to(RAIZ)}: ejecute make diagrams-check (H1)")
        apaisada = fid != "FIG-1.1"
        if apaisada and not self.ultimo_fue_figura:
            self.salto_seccion(apaisada=False)
        from PIL import Image
        with Image.open(png) as im:
            ratio = im.size[0] / im.size[1]
        if apaisada:
            ancho_cm = min(ANCHO_APAISADO / CM_TWIPS, 12.2 * ratio)
        else:
            ancho_cm = min(ANCHO_VERTICAL / CM_TWIPS, 11.0 * ratio)
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _espaciado(p, 0, 60)
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(str(png_reducido(png, ancho_cm)), width=Cm(ancho_cm))
        self._mover(p._p)
        pie = self.doc.add_paragraph()
        pie._p.insert(0, copy.deepcopy(self.ppr_pie))
        _espaciado(pie, 40, 40)
        pie.paragraph_format.keep_with_next = True
        _run_fmt(pie.add_run(fig["leyenda"]), 9, cursiva=True, color="595959")
        self._mover(pie._p)
        obs = self.parrafo(observar, tam=9.5, despues=120, alinear=WD_ALIGN_PARAGRAPH.CENTER if not apaisada else None)
        if apaisada:
            self.salto_seccion(apaisada=True)
        self.figuras.append(fid)
        self.ultimo_fue_figura = apaisada
        del obs

    # ---------------------------------------------------------------- texto
    def sustituir(self, texto: str) -> str:
        def dato(m):
            k = m.group(1)
            if k not in self.d:
                raise SystemExit(f"{{{{dato:{k}}}}} no existe (ver datos() en build_informe.py)")
            return self.d[k]
        texto = re.sub(r"\{\{dato:([a-z0-9_]+)\}\}", dato, texto)
        if COMPLETAR in texto:
            self.completar += re.findall(r"\[COMPLETAR[^\]]*\]", texto)
        return texto

    def bloques(self, lineas: list[str]):
        """Convierte líneas Markdown (subconjunto) en bloques."""
        out, buf, tabla = [], [], []

        def cerrar():
            if buf:
                out.append(("p", " ".join(s.strip() for s in buf)))
                buf.clear()
            if tabla:
                filas = [[c.strip() for c in l.strip().strip("|").split("|")] for l in tabla
                         if not re.fullmatch(r"\|[\s:|-]+\|", l.strip())]
                out.append(("tabla_md", filas))
                tabla.clear()

        for l in lineas:
            s = l.rstrip("\n")
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
            m = re.match(r"^(#{1,3}) (.+)$", s)
            if m:
                cerrar()
                out.append((f"h{len(m.group(1))}", m.group(2).strip()))
            elif s.startswith("- "):
                cerrar()
                out.append(("li", s[2:].strip()))
            elif re.match(r"^\d+\. ", s) and not buf:
                out.append(("num", s.strip()))
            elif s.startswith("> "):
                cerrar()
                out.append(("nota", s[2:].strip()))
            elif m := re.fullmatch(r"\{\{tabla:([a-z_]+)\}\}", s.strip()):
                cerrar()
                out.append(("tabla", m.group(1)))
            elif m := re.fullmatch(r"\{\{figura:([A-Z0-9.\-a-z]+)\|(.+)\}\}", s.strip()):
                cerrar()
                out.append(("figura", m.group(1), m.group(2)))
            else:
                buf.append(s)
        cerrar()
        return out

    def _es_apaisado(self, b) -> bool:
        if b[0] == "figura":
            return b[1] != "FIG-1.1"
        return b[0] == "tabla" and b[1] in TABLAS and TABLAS[b[1]](self.x, self.d)[3]

    def render(self, bloques, salto_h1=False):
        # Un título o párrafo corto que presenta una figura o tabla apaisada viaja con ella a la página apaisada:
        # así no queda una página vertical casi vacía antes del salto de sección.
        entrada = set()
        for i, b in enumerate(bloques):
            if self._es_apaisado(b):
                # una tabla fluye a la página siguiente, una figura no: la entrada de una figura debe caber con ella
                es_tabla = b[0] == "tabla"
                tipos, limite = (("p", "h1", "h2", "h3"), 1200) if es_tabla else (("p", "h2", "h3"), 600)
                j, chars = i - 1, 0
                while j >= 0 and bloques[j][0] in tipos and chars + len(bloques[j][1]) < limite:
                    chars += len(bloques[j][1])
                    entrada.add(j)
                    j -= 1
        for i, b in enumerate(bloques):
            tipo = b[0]
            if i in entrada:
                if not self.ultimo_fue_figura:
                    self.salto_seccion(apaisada=False)
                    self.ultimo_fue_figura = True
                estado = True
            else:
                estado = None
            self._render1(b, salto_h1)
            if estado:
                self.ultimo_fue_figura = True

    def _render1(self, b, salto_h1):
        if True:
            tipo = b[0]
            if tipo in ("h1", "h2", "h3"):
                self.titulo(b[1], int(tipo[1]), salto=salto_h1 and tipo == "h1")
            elif tipo == "p":
                self.parrafo(b[1])
            elif tipo == "li":
                self.vineta(b[1])
            elif tipo == "num":
                self.numerado(b[1])
            elif tipo == "nota":
                self.nota(b[1])
            elif tipo == "tabla_md":
                filas = b[1]
                n = len(filas[0])
                self.tabla(filas[0], filas[1:], [17.0 / n] * n)
            elif tipo == "tabla":
                if b[1] not in TABLAS:
                    raise SystemExit(f"{{{{tabla:{b[1]}}}}} no existe (ver TABLAS en build_informe.py)")
                cab, filas, anchos, apaisada = TABLAS[b[1]](self.x, self.d)
                if apaisada and not self.ultimo_fue_figura:
                    self.salto_seccion(apaisada=False)
                self.tabla(cab, filas, anchos, apaisada)
                if apaisada:
                    self.salto_seccion(apaisada=True)
                    self.ultimo_fue_figura = True
            elif tipo == "figura":
                self.figura(b[1], b[2])

    # ---------------------------------------------------------------- plantilla
    def portada(self):
        par = self.doc.paragraphs

        def poner(p, texto):
            runs = p.runs
            runs[0].text = texto
            for r in runs[1:]:
                r._r.getparent().remove(r._r)
        for p in par[:12]:
            t = p.text
            if t.startswith("Plantilla y guía"):
                poner(p, "Informe de análisis y diseño de red — Celeris Edge")
            elif t.startswith("Preparado por"):
                poner(p, f"Preparado por: {gx.autores()} [COMPLETAR: nombres completos de los autores]")
                self.completar.append("[COMPLETAR: nombres completos de los autores]")
            elif t.startswith("Docente / curso"):
                poner(p, "Docente / curso: [COMPLETAR: docente/curso]")
                self.completar.append("[COMPLETAR: docente/curso]")
            elif t.startswith("Análisis y Diseño de Red"):
                pass
            elif re.fullmatch(r"20\d\d", t.strip()):
                meta = self.x.inv["meta"]
                poner(p, f"Versión {meta['inventario_version']} · inventario {meta['fecha']} · commit {commit_fuente()}")

    def limpiar_guia(self):
        """Quita texto guía y tablas de ejemplo; deja títulos de sección, el campo TOC y los saltos de página."""
        cuerpo = self.doc.element.body
        hijos = list(cuerpo.iterchildren())
        inicio = next(i for i, e in enumerate(hijos) if e.tag == qn("w:p") and _texto(e).strip() == "Tabla de contenidos")
        titulos = []
        for e in hijos[inicio + 1:]:
            if e.tag == qn("w:sectPr") or e.tag == qn("w:sdt"):
                continue
            if e.tag == qn("w:p"):
                estilo = e.find(qn("w:pPr") + "/" + qn("w:pStyle"))
                nombre = estilo.get(qn("w:val")) if estilo is not None else ""
                if nombre in ("Heading1", "Heading2"):
                    titulos.append(e)
                    continue
                if e.find(".//" + qn("w:br")) is not None and not _texto(e).strip():
                    continue  # salto de página antes de la sección 1
            cuerpo.remove(e)
        return hijos[inicio], titulos

    def secciones_md(self):
        """{título exacto: bloques}, en el orden de los archivos 01–11; y bloques de preliminares y anexos."""
        por_titulo, extras_pre, extras_anexo = {}, [], []
        for f in sorted(TEXTO.glob("*.md")):
            if f.name == "README.md":
                continue
            bl = self.bloques(f.read_text(encoding="utf-8").splitlines())
            if f.name.startswith("00-"):
                extras_pre += bl
                continue
            if re.match(r"[A-Z]-", f.name):
                extras_anexo += bl
                continue
            actual = None
            for b in bl:
                if b[0] in ("h1", "h2"):
                    actual = b[1]
                    if actual in por_titulo:
                        raise SystemExit(f"Título repetido en el texto: {actual}")
                    por_titulo[actual] = []
                elif actual is None:
                    raise SystemExit(f"{f.name}: contenido antes del primer título")
                else:
                    por_titulo[actual].append(b)
        return por_titulo, extras_pre, extras_anexo

    def _fuente_por_defecto(self):
        """Calibri como fuente por defecto del documento: las entradas de la tabla de contenidos que Word crea al
        actualizarla (estilos TOC 1–3) heredarían Times New Roman."""
        rpr = self.doc.styles.element.find(qn("w:docDefaults") + "/" + qn("w:rPrDefault") + "/" + qn("w:rPr"))
        if rpr is None:
            return
        f = rpr.find(qn("w:rFonts"))
        if f is None:
            f = OxmlElement("w:rFonts")
            rpr.insert(0, f)
        for a in ("w:ascii", "w:hAnsi", "w:cs"):
            f.set(qn(a), "Calibri")
        for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme"):
            if qn(a) in f.attrib:
                del f.attrib[qn(a)]

    def _quitar_separadores_antes_de_salto(self):
        """Un separador vacío tras una tabla que llena la página produce una página en blanco si el párrafo siguiente
        empieza con salto de página: se quita."""
        for p in list(self.doc.element.body.iter(qn("w:p"))):
            if p.find(qn("w:pPr") + "/" + qn("w:pageBreakBefore")) is None:
                continue
            prev = p.getprevious()
            if (prev is not None and prev.tag == qn("w:p") and not _texto(prev) and prev.find(".//" + qn("w:sectPr")) is None
                    and prev.find(".//" + qn("w:drawing")) is None and prev.getprevious() is not None
                    and prev.getprevious().tag == qn("w:tbl")):
                prev.getparent().remove(prev)

    def _cabecera(self):
        for s in self.doc.sections:
            for h in (s.header, s.first_page_header):
                for t in h._element.iter(qn("w:t")):
                    if "Plantilla de informe" in (t.text or ""):
                        t.text = t.text.replace("Plantilla de informe", "Informe Celeris Edge")

    def construir(self) -> Document:
        self.portada()
        h_toc, titulos = self.limpiar_guia()
        # El título «Tabla de contenidos» no debe listarse en la propia tabla (\o usa el estilo): se le quita el estilo
        # Heading 1 y conserva su formato directo.
        estilo_toc = h_toc.find(qn("w:pPr") + "/" + qn("w:pStyle"))
        if estilo_toc is not None:
            estilo_toc.getparent().remove(estilo_toc)
        por_titulo, pre, anexos = self.secciones_md()
        esperados = [f"{s['id']}. {s['titulo']}" if "." not in s["id"] else f"{s['id']} {s['titulo']}"
                     for s in self.x.traz["docx_secciones"]]
        reales = [_texto(t).strip() for t in titulos]
        if reales != esperados:
            raise SystemExit(f"Los títulos de la plantilla no coinciden con trazabilidad.yaml docx_secciones:\n{reales}\n{esperados}")
        sobran = set(por_titulo) - set(reales)
        if sobran:
            raise SystemExit(f"Títulos del texto que no están en la plantilla: {sorted(sobran)}")
        # preliminares antes de la tabla de contenidos
        self.ancla = h_toc.getprevious()
        self.render(pre)
        salto = self.doc.add_paragraph()
        salto.add_run().add_break(__import__("docx").enum.text.WD_BREAK.PAGE)
        self._mover(salto._p)
        # secciones 1–11
        for t, nombre in zip(titulos, reales):
            self.ancla = t
            if nombre[0].isdigit() and "." in nombre and nombre.split(" ")[0].count(".") == 1 and nombre.split(".")[1][:1] == " ":
                pass
            self.render(por_titulo.get(nombre, []))
            if self.ultimo_fue_figura:
                pass
        # anexos al final
        self.render(anexos, salto_h1=True)
        self._quitar_separadores_antes_de_salto()
        self._cabecera()
        self.doc.core_properties.title = "Informe de análisis y diseño de red — Celeris Edge (CE0311)"
        self.doc.core_properties.author = gx.autores()
        self.doc.core_properties.comments = f"Generado por docs/infra/e1/build_informe.py desde commit {commit_fuente()}"
        return self.doc


# ==================================================================================================
# PDF, tabla de contenidos y páginas
# ==================================================================================================
def _pids_word() -> set[int]:
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq WINWORD.EXE", "/FO", "CSV", "/NH"], capture_output=True, text=True)
    return {int(c.split('","')[1]) for c in r.stdout.splitlines() if c.startswith('"WINWORD')}


def _word(docx: Path, pdf: Path, salida_json: Path) -> dict:
    ps = rf"""
$ErrorActionPreference = 'Stop'
$w = New-Object -ComObject Word.Application
$w.Visible = $false
$w.DisplayAlerts = 0
try {{
  $d = $w.Documents.Open('{docx}')
  foreach ($t in $d.TablesOfContents) {{ $t.Update() }}
  $d.Fields.Update() | Out-Null
  $d.Repaginate()
  $out = @()
  foreach ($p in $d.Paragraphs) {{
    $txt = $p.Range.Text.Trim()
    if ($p.OutlineLevel -le 2 -or $txt -like 'Figura *') {{
      $out += [pscustomobject]@{{ texto = $txt; nivel = $p.OutlineLevel; pagina = $p.Range.Information(3) }}
    }}
  }}
  $total = $d.ComputeStatistics(2)
  [pscustomobject]@{{ motor = 'Microsoft Word (COM)'; paginas = $total; marcas = $out }} | ConvertTo-Json -Depth 4 |
    Out-File -Encoding utf8 '{salida_json}'
  $d.Save()
  $d.ExportAsFixedFormat('{pdf}', 17)
  try {{ $d.Close(0) }} catch {{ }}
}} finally {{
  try {{ $w.Quit(0) }} catch {{ }}
  try {{ [void][Runtime.InteropServices.Marshal]::ReleaseComObject($w) }} catch {{ }}
}}
"""
    antes = _pids_word()
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], capture_output=True, text=True,
                           timeout=600)
    finally:
        # Word a veces queda vivo (oculto) aunque se llame a Quit(): se cierra solo la instancia que abrió este script.
        for pid in _pids_word() - antes:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        bloqueo = docx.with_name("~$" + docx.name[2:])   # archivo de propietario que Word deja si se le cierra a la fuerza
        if bloqueo.exists():
            bloqueo.unlink()
    if r.returncode != 0 or not pdf.exists():
        raise RuntimeError(r.stderr.strip() or "Word no exportó el PDF")
    return json.loads(salida_json.read_text(encoding="utf-8-sig"))


def _libreoffice(exe: str, docx: Path, pdf: Path) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([exe, "--headless", "--convert-to", "pdf", "--outdir", tmp, str(docx)], capture_output=True,
                           text=True, timeout=600)
        hecho = Path(tmp) / (docx.stem + ".pdf")
        if r.returncode != 0 or not hecho.exists():
            raise RuntimeError(r.stderr.strip() or "LibreOffice no convirtió el DOCX")
        shutil.move(str(hecho), pdf)
    paginas = None
    try:
        from pypdf import PdfReader
        paginas = len(PdfReader(str(pdf)).pages)
    except Exception:  # noqa: BLE001 - pypdf es opcional
        pass
    return {"motor": "LibreOffice headless", "paginas": paginas, "marcas": [],
            "nota": "LibreOffice no actualiza la tabla de contenidos; ábrala en Word y pulse F9 antes de entregar"}


def exportar_pdf(docx: Path) -> dict:
    pdf = docx.with_suffix(".pdf")
    if pdf.exists():
        pdf.unlink()
    lo = shutil.which("soffice") or shutil.which("libreoffice")
    with tempfile.TemporaryDirectory() as tmp:
        if lo:
            info = _libreoffice(lo, docx, pdf)
        elif sys.platform == "win32":
            info = _word(docx, pdf, Path(tmp) / "paginas.json")
        else:
            raise SystemExit("No hay LibreOffice (soffice) ni Microsoft Word para generar el PDF")
    info["docx"] = docx.relative_to(RAIZ).as_posix()
    info["pdf"] = pdf.relative_to(RAIZ).as_posix()
    info["commit_fuente"] = commit_fuente()
    info["huella_fuente"] = huella_fuente()
    return info


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", default=str(SALIDA))
    ap.add_argument("--pdf", action="store_true", help="actualiza la tabla de contenidos y exporta el PDF")
    a = ap.parse_args(argv)
    x = Infra.cargar()
    c = Constructor(x)
    doc = c.construir()
    salida = Path(a.salida)
    salida.mkdir(parents=True, exist_ok=True)
    ruta = salida / nombre_docx(x)
    doc.save(str(ruta))
    print(ruta.relative_to(RAIZ) if ruta.is_relative_to(RAIZ) else ruta)
    print(f"figuras: {len(c.figuras)} ({', '.join(c.figuras)}) · [COMPLETAR] pendientes: {len(set(c.completar))}")
    if a.pdf:
        info = exportar_pdf(ruta)
        info["figuras"] = c.figuras
        info["completar"] = sorted(set(c.completar))
        PAGINAS_JSON.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"PDF: {info['pdf']} · {info.get('paginas')} páginas · {info['motor']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
