"""Genera el Informe de Análisis y Diseño de Centro de Datos Híbrido (CE0331, S1, E2) en DOCX y PDF (`make informe-dc`).

    python docs/infra/e2/build_informe.py [--pdf] [--salida DIR]

Mismo método que CE0311 (docs/infra/e1/build_informe.py, del que se reutiliza la clase Constructor, la portada institucional y
la exportación a PDF; no se duplican):
- Parte de una COPIA de la plantilla docs/fuentes/CE03/S1_E2_Analisis_y_Diseno_de_Centro_de_Datos_Hibrido.docx: conserva sus
  estilos, el campo de la tabla de contenidos y los títulos de las 12 secciones; quita el texto guía y las tablas de ejemplo.
- El texto sale de docs/infra/e2/informe/NN-*.md (00 = preliminares, A… = anexos; sintaxis igual a la de CE0311).
- Toda tabla con datos (VM, vSwitch, rack, rutas, SG, dimensionamiento, costo, RTO/RPO, matriz) se genera aquí desde
  infra/centro_datos.yaml e infra/inventory.yaml; nunca a mano. Las cifras del texto son {{dato:clave}}.
- Figuras: DC-0…DC-3 (entregables/CE0331/diagramas/) y FIG-5.4 de CE0311 tal cual (integración híbrida).
- `--pdf` abre el DOCX en Word (COM) o LibreOffice: actualiza la tabla de contenidos, guarda el DOCX, exporta el PDF y registra las
  páginas en docs/infra/e2/informe-paginas.json (lo usan V-95+ y la autoevaluación).
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ / "infra"))
sys.path.insert(0, str(RAIZ / "infra" / "gen"))

from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm  # noqa: E402

from celeris_infra import Infra  # noqa: E402
from centro_datos import CentroDatos, coma  # noqa: E402
from drawio_dc import huella_dc  # noqa: E402

_spec = importlib.util.spec_from_file_location("e1_informe", RAIZ / "docs" / "infra" / "e1" / "build_informe.py")
e1 = importlib.util.module_from_spec(_spec)
sys.modules["e1_informe"] = e1
_spec.loader.exec_module(e1)

PLANTILLA = RAIZ / "docs" / "fuentes" / "CE03" / "S1_E2_Analisis_y_Diseno_de_Centro_de_Datos_Hibrido.docx"
TEXTO = AQUI / "informe"
SALIDA = RAIZ / "entregables" / "CE0331"
DIAGRAMAS = SALIDA / "diagramas"
PAGINAS_JSON = AQUI / "informe-paginas.json"
CAMBIOS_MD = RAIZ / "docs" / "infra" / "e1" / "CAMBIOS-INVENTARIO.md"
EVIDENCIAS_E = sorted((RAIZ / "evidencias").glob("*-E"))
FIGURAS_INFORME = ["DC-0", "DC-1", "DC-2", "DC-3", "FIG-5.4"]
AREA = "Infraestructura Tecnológica"

_X: Infra | None = None
_CD: CentroDatos | None = None


def fuentes() -> tuple[Infra, CentroDatos]:
    global _X, _CD
    if _X is None:
        _X = Infra.cargar()
        _CD = CentroDatos.cargar(_X)
    return _X, _CD


def pct(v: float, d: int = 1) -> str:
    return coma(v * 100, d) + " %"


def nombre_docx(cd: CentroDatos) -> str:
    return f"Informe_Centro_Datos_v{cd.meta['version']}.docx"


# ==================================================================================================
# Cifras que el texto cita con {{dato:clave}}
# ==================================================================================================
def datos(x: Infra) -> dict[str, str]:
    x, cd = fuentes()
    t1, t2, dm, c = cd.totales("F1"), cd.totales("F2"), cd.dimensionar(), cd.costo()
    g = cd.ec2_gw()
    cob = _cobertura()
    ids = {i for f in cob.values() for i in f["ids"]}
    eve = _verificaciones_e()
    nat = next(a for a in c["nat_alternativas"] if "NAT Gateway" in a["opcion"])
    en = cd.raw["energia"]
    return {
        "version": cd.meta["version"], "n_vm": str(len(cd.vms)), "n_vm_f1": str(t1["vms"]),
        "vcpu_f1": str(t1["vcpu"]), "ram_f1": str(t1["ram_gb"]), "disco_f1": coma(t1["disco_gb"], 0),
        "vcpu_f2": str(t2["vcpu"]), "ram_f2": str(t2["ram_gb"]), "disco_f2": coma(t2["disco_gb"], 0), "disco_sin_cache_f2": coma(t2["disco_sin_cache_gb"], 0),
        "nucleos_nec": coma(dm["nucleos_necesarios"], 2), "nucleos_host": str(dm["nucleos_host"]), "nuc_sens": coma(dm["nucleos_sensibles"], 2), "nuc_resto": coma(dm["nucleos_resto"], 2),
        "vcpu_sens": str(dm["vcpu_sensibles"]), "vcpu_resto": str(dm["vcpu_resto"]),
        "h_cpu": pct(dm["holgura_cpu"]), "h_ram": pct(dm["holgura_ram"]), "m_ram": pct(dm["margen_ram_tras_crecimiento"]), "h_disco": pct(dm["holgura_disco"]),
        "ram_host": str(dm["ram_host"]), "ram_esxi": coma(dm["ram_con_sobrecarga"], 1), "ram_crec": coma(dm["ram_con_crecimiento"], 1),
        "ram_libre": coma(dm["ram_libre_tras_crecimiento"], 1), "disco_libre": coma(dm["disco_capacidad"] - dm["disco_con_copia"], 0),
        "disco_req": coma(dm["disco_requerido"], 0), "disco_tot": coma(dm["disco_con_copia"], 0), "disco_cap": coma(dm["disco_capacidad"], 0),
        "uso_disco": pct(dm["uso_disco"]), "rel_cpu": coma(dm["relacion_vcpu_nucleos"], 2),
        "costo_total": coma(c["total"], 2), "costo_meta": str(c["meta"]), "costo_lab_h": coma(c["lab_hora"], 4), "costo_sim": coma(c["simulacro_total"], 2),
        "nat_gw_mes": coma(nat["mensual"], 2), "nat_gw_pct": pct(nat["mensual"] / c["total"], 0),
        "gw_margen_cpu": pct(g["margen_cpu"], 0), "gw_margen_ram": pct(g["margen_ram"], 0), "gw_base": coma(g["linea_base_vcpu"], 2),
        "gw_cred_g": str(g["creditos_por_hora"]), "gw_cred_c": coma(g["creditos_consumidos_por_hora"], 0),
        "n_elementos": str(len(ids)), "n_figuras": str(len(FIGURAS_INFORME)), "n_servicios": str(len(cd.servicios)),
        "consumo_w": str(en["consumo_w"]), "autonomia": f"{en['autonomia_min'][0]}–{en['autonomia_min'][1]}",
        "n_verif_e": str((eve.get("resumen") or {}).get("PASA", 0)), "fecha_e": eve.get("fecha", ""),
        "huella": huella_dc(), "inv_version": x.inv["meta"]["inventario_version"],
    }


def _cobertura() -> dict:
    ruta = RAIZ / "docs" / "infra" / "e2" / "cobertura-figuras.json"
    if not ruta.exists():
        raise SystemExit("Falta docs/infra/e2/cobertura-figuras.json: ejecute make diagrams-dc-check")
    return json.loads(ruta.read_text(encoding="utf-8"))


def _verificaciones_e() -> dict:
    for d in reversed(EVIDENCIAS_E):
        f = d / "verificaciones.json"
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))
    return {}


# ==================================================================================================
# Tablas generadas desde los YAML: nombre → (x, d) → (cabecera, filas, anchos_cm, apaisada)
# ==================================================================================================
def lst(v, sep=", ") -> str:
    return sep.join(str(i) for i in v) if v else "—"


def t_control_versiones(x, d):
    x, cd = fuentes()
    return (["Versión", "Fecha", "Fuente (centro de datos · inventario)", "Autores", "Cambios"],
            [[cd.meta["version"], cd.meta["fecha"], f"centro_datos.yaml v{cd.meta['version']} · inventario v{x.inv['meta']['inventario_version']} · huella {huella_dc()}",
              e1.equipo(), "Primera edición: diagramas DC-0…DC-3, matriz de componentes y dimensionamiento (XLSX) e informe completo."]],
            [1.6, 2.2, 4.8, 3.2, 5.2], False)


def t_objetivos(x, d):
    x, cd = fuentes()
    res = {"DC-OBJ-1": f"CPU {d['h_cpu']}, RAM {d['h_ram']} ({d['m_ram']} aun reservando el 20 % de crecimiento), disco {d['h_disco']}",
           "DC-OBJ-2": f"US$ {d['costo_total']} al mes; laboratorio efímero US$ {d['costo_lab_h']} por hora",
           "DC-OBJ-3": "Consola: RTO 2 h y RPO 15 min (CT-03); descargas: RTO ≈ 0 (CT-01)",
           "DC-OBJ-4": "S3 con Object Lock de 30 días (modo compliance) para la base de la consola y las configuraciones",
           "DC-OBJ-5": "Se mide en S2 al recrear EC2-GW y la VPC con OpenTofu"}
    filas = [[o["id"], o["objetivo"], o["indicador"], o["meta"], res[o["id"]], o["responsable"], o["verificable"]] for o in cd.raw["objetivos"]]
    return (["ID", "Objetivo", "Indicador", "Meta", "Resultado del diseño", "Responsable", "Se comprueba en"], filas, [1.8, 2.6, 2.6, 3.2, 4.6, 1.6, 1.6], False)


def t_limites_esxi(x, d):
    x, cd = fuentes()
    return (["Límite de ESXi gratuito", "Consecuencia en este diseño"], [[l["limite"], l["consecuencia"]] for l in cd.host["hipervisor"]["limites"]], [5.5, 11.5], False)


def t_rack(x, d):
    x, cd = fuentes()
    r = cd.raw["rack"]
    filas = []
    for o in r["ocupacion"]:
        u = f"U{o['u'][0]}" if o["u"][0] == o["u"][1] else f"U{o['u'][0]}–U{o['u'][1]}"
        ids = o.get("componente") or o.get("id")
        if o.get("extra"):
            ids += " + " + ", ".join(o["extra"])
        filas.append([u, o["elemento"], ids])
    for a, b in r["libres_derivado"]:
        filas.append([f"U{a}–U{b}", "Libres (no figuran en D2.4)", "—"])
    filas.sort(key=lambda f: -max(int(n) for n in re.findall(r"\d+", f[0])))
    return (["Unidad", "Equipo (D2.4)", "ID"], filas, [2.2, 10.0, 4.8], False)


def t_host(x, d):
    x, cd = fuentes()
    h = cd.host
    ds = cd.datastores
    filas = [["Hipervisor", f"{h['hipervisor']['producto']} {h['hipervisor']['version']}, licencia gratuita"],
             ["CPU", f"{h['cpu']['nucleos']} núcleos"], ["RAM", f"{h['ram_gb']} GB"],
             ["Formato", f"{h['chasis']['formato_u']}U"], ["Controladora", h["controladora_raid"]],
             ["DS-VM", f"{ds['DS-VM']['medio']}: {coma(ds['DS-VM']['capacidad_gb'] / 1000, 2)} TB útiles; {ds['DS-VM']['contiene']}"],
             ["DS-CACHE1, DS-CACHE2", f"{ds['DS-CACHE1']['medio']} cada uno (1 TB); un datastore de caché por nodo"],
             ["Gestión fuera de banda", "IPMI01 (iDRAC/iLO), 10.20.10.11"], ["Gestión del hipervisor", "vmk0, 10.20.10.10, PG-MGMT"],
             ["Consumo y UPS", f"≈ {cd.raw['energia']['consumo_w']} W; UPS01 online de {coma(cd.raw['energia']['capacidad_kva'])} kVA, autonomía {d['autonomia']} min (a confirmar con el fabricante)"]]
    return (["Recurso de ESX01", "Valor [S-08]"], filas, [4.6, 12.4], False)


def t_nic(x, d):
    x, cd = fuentes()
    filas = [[n["id"], f"{n['velocidad_gbps']} GbE" if n["velocidad_gbps"] else "libre", n["vswitch"] or "—", n["destino"] or "—", n["uso"]] for n in cd.nics.values()]
    return (["NIC", "Velocidad", "vSwitch", "Destino", "Uso"], filas, [1.8, 2.0, 2.2, 2.4, 8.6], False)


def t_vswitch(x, d):
    x, cd = fuentes()
    filas = []
    for s in cd.vswitches.values():
        t = s["teaming"]
        for i, pg in enumerate(s["port_groups"]):
            vlan = "sin etiqueta" if pg["vlan"] is None else str(pg["vlan"])
            vm = ", ".join(v["componente"] for v in cd.vms if pg["id"] in v["port_groups"])
            filas.append([s["id"] if i == 0 else "", ", ".join(s["uplinks"]) if i == 0 else "",
                          (t["politica"] if t else "Una NIC, sin teaming") if i == 0 else "", pg["id"], vlan, pg["zona"] or "todas (trunk)", vm])
    return (["vSwitch", "Uplinks", "Teaming", "Port group", "VLAN", "Zona", "VM conectadas"], filas, [1.8, 2.2, 3.4, 2.8, 1.5, 2.2, 3.3], False)


def t_vms(x, d):
    x, cd = fuentes()
    filas = []
    for fase in ("F1", "F2"):
        for v in [v for v in cd.vms if v["fase"] == fase]:
            filas.append([v["componente"], v["fase"], str(v["vcpu"]), str(v["ram_gb"]), cd.vm_texto_disco(v), v["so"], x.componentes[v["componente"]]["funcion"],
                          " + ".join(v["port_groups"])])
        t = cd.totales(fase)
        filas.append([f"**Total {fase}**", "", f"**{t['vcpu']}**", f"**{t['ram_gb']}**", f"**{coma(t['disco_gb'], 0)}**", "", "", ""])
    return (["VM", "Fase", "vCPU", "RAM (GB)", "Disco (GB)", "SO", "Función", "Port group"], filas, [1.8, 1.0, 1.1, 1.4, 2.2, 2.4, 4.4, 2.7], False)


def t_region(x, d):
    x, cd = fuentes()
    return (["Opción", "A favor", "En contra", "Decisión"], [[o["region"], o["a_favor"], o["en_contra"], o["decision"]] for o in cd.aws["region"]["opciones"]], [2.0, 4.6, 4.0, 6.4], False)


def t_subredes(x, d):
    x, cd = fuentes()
    c = x.componentes
    res = next(r for r in x.inv["reservas"] if r["id"] == "RES-AWS-CRECIMIENTO")
    filas = [["VPC (AWS-VPC)", c["AWS-VPC"]["cidr"], "—", "Aislamiento de los recursos del proyecto"],
             ["pub-a (AWS-PUB-A)", c["AWS-PUB-A"]["cidr"], "Pública, AZ a", "EC2-GW 10.30.0.10; NAT-DR solo en el simulacro"],
             ["app-a (AWS-APP-A)", c["AWS-APP-A"]["cidr"], "Privada, AZ a", "Vacía; EC2-DR solo en el simulacro"],
             ["Reserva", res["cidr"], "—", "Crecimiento; sin subredes"]]
    return (["Subred", "CIDR", "Tipo", "Uso"], filas, [3.6, 3.0, 3.0, 7.4], False)


def t_rutas_aws(x, d):
    return e1.t_rutas_aws(x, d)


def t_instancias_ec2(x, d):
    x, cd = fuentes()
    filas = []
    for i in cd.aws["instancias"]:
        c = x.componentes[i["componente"]]
        subred = "pub-a" if i["componente"] in ("EC2-GW", "NAT-DR") else "app-a"
        r = f"{i['vcpu']} vCPU, {i['ram_gib']} GiB" + (f", {i['ebs_gb']} GB {i['ebs_tipo']}" if i.get("ebs_gb") else "")
        filas.append([i["componente"], i["tipo"], r, subred, "Temporal (T59)" if i.get("temporal") else "Permanente", i["por_que"]])
    return (["Instancia", "Tipo", "Recursos", "Subred", "Vida", "Por qué ese tipo"], filas, [1.8, 1.5, 3.2, 1.3, 2.0, 7.2], False)


def _regla(r, lado):
    pts = r.get("puertos") or ([r["puerto"]] if r.get("puerto") else [])
    p = f"{r['proto'].upper()}/{','.join(str(i) for i in pts)}" if pts else r["proto"].upper() if r["proto"] != "todo" else "todo"
    if r.get("rango"):
        p = f"{r['proto'].upper()}/{r['rango'][0]}–{r['rango'][1]}"
    otro = (r.get("origen") or r.get("destino") or "—").split(":", 1)[-1]
    return f"{lado} {p} {'desde' if lado == 'entrada' else 'hacia'} {otro}" + (f" ({r['flujo']})" if r.get("flujo") else "")


def t_sg_nacl(x, d):
    x, cd = fuentes()
    aws = x.inv["aws"]
    filas = []
    for sg in aws["security_groups"]:
        reglas = [_regla(r, "entrada") for r in sg["ingress"]] + [_regla(r, "salida") for r in sg["egress"]] or ["sin reglas de entrada"]
        filas.append([sg["id"], "Security Group · " + sg["componente"], "\n".join(reglas) if sg["ingress"] else "Sin entrada desde Internet\n" + "\n".join(_regla(r, "salida") for r in sg["egress"])])
    for n in aws["nacl"]:
        reglas = [("permitir " if r["accion"] == "allow" else "denegar ") + _regla({**r}, "entrada") for r in n["ingress"]]
        filas.append([n["id"], "NACL · subred " + ", ".join(n["subredes"]), "\n".join(reglas)])
    return (["Nombre", "Alcance", "Reglas"], filas, [2.4, 4.0, 10.6], False)


def t_vpn_dc(x, d):
    v = x.inv["vpn"]
    on, aws = v["extremo_onpremise"], v["extremo_aws"]
    f1, f2 = v["fase1"], v["fase2"]
    filas = [["Dispositivo", on["dispositivo"], aws["dispositivo"]],
             ["IP pública", f"{on['ip_publica']} en {on['ip_publica_en']}, NAT 1:1 a {on['ip_interna']} (UDP 500/4500)", aws["ip_publica"]],
             ["Identidad IKE", f"IP {on['identidad_ike']['valor']}", "—"],
             ["Redes anunciadas", ", ".join(on["redes_anunciadas"]), ", ".join(aws["redes_anunciadas"])],
             ["ASN (BGP)", str(on["asn"]), f"{aws['asn']} ({aws['asn_nota']})"],
             ["Túneles", "; ".join(f"{t['id']} {t['red_interna']} ({t['rol']})" for t in v["tuneles"]), "Idem; el VGW usa un túnel a la vez"],
             ["Fase 1 (IKEv2)", f"{f1['cifrado']}, PRF {f1['prf']}, DH {f1['dh']}, {f1['vida_s']} s", "Idem"],
             ["Fase 2 (ESP)", f"{f2['cifrado']}, PFS {f2['pfs']}, {f2['vida_s']} s", "Idem"],
             ["Flujos que transporta", ", ".join(v["flujos_sobre_vpn"]) + " (panel remoto y eventos al SIEM)", "Idem"]]
    return (["Parámetro", "Extremo campus (FW01)", "Extremo AWS (VGW)"], filas, [3.2, 8.2, 5.6], False)


def t_matriz(x, d):
    import xlsx_centro_datos as gd
    x, cd = fuentes()
    filas = gd.filas_componentes(x, cd, _cobertura())
    return (["ID", "Componente", "Entorno", "Tipo", "Función", "Criticidad", "Recursos asignados", "Figuras"],
            [[f["id"], f["nombre"], f["entorno"], f["tipo"], f["funcion"], f["crit"], f["recursos"], f["figuras"]] for f in filas],
            [2.2, 4.0, 1.8, 3.2, 5.6, 1.5, 5.2, 1.7], True)


def t_dim(x, d):
    x, cd = fuentes()
    return (["Recurso", "Cálculo", "Requerido", "Capacidad del host", "Holgura", "Estado"],
            [["CPU (F2)", f"{d['vcpu_sens']} vCPU sensibles ÷ 2 + {d['vcpu_resto']} vCPU ÷ 4 = {d['nuc_sens']} + {d['nuc_resto']}", f"{d['nucleos_nec']} núcleos", f"{d['nucleos_host']} núcleos", d["h_cpu"], "Cumple ≥ 15 %"],
             ["RAM (F2)", f"{d['ram_f2']} GB × 1,1 = {d['ram_esxi']} GB; × 1,2 = {d['ram_crec']} GB", f"{d['ram_crec']} GB", f"{d['ram_host']} GB", f"{d['h_ram']} tras ESXi; {d['m_ram']} tras el crecimiento", "Cumple ≥ 15 % en ambos casos"],
             ["Disco de VM (F2)", f"{d['disco_sin_cache_f2']} GB × 1,3 = {d['disco_req']} GB; + 200 GB de copia local = {d['disco_tot']} GB", f"{d['disco_tot']} GB", f"{d['disco_cap']} GB (DS-VM)", d["h_disco"], "Cumple ≥ 15 %"],
             ["Caché por nodo", "500 GB como punto de partida [S-04]", "500 GB", "1 000 GB (NVMe)", "50,0 %", "Cumple ≥ 15 %"],
             ["Red hacia un laboratorio", "40 PCs a la vez ≈ 1 Gbps (REQ-NF-02)", "1 Gbps", "2 × 10 GbE", "95 %", "Cumple; se mide con iperf3 en S2"]],
            [2.4, 5.2, 2.2, 2.6, 2.6, 2.0], False)


def t_gw(x, d):
    x, cd = fuentes()
    g = cd.ec2_gw()
    c = g["carga_diseno"]
    filas = [["CPU", f"{g['vcpu']} vCPU; línea base {pct(g['linea_base_por_vcpu'], 0)} por vCPU = {d['gw_base']} vCPU sostenidos", f"{coma(c['cpu_medio_vcpu'], 2)} vCPU de media", d["gw_margen_cpu"]],
             ["RAM", f"{g['ram_gib']} GiB = 1 024 MiB", f"{c['ram_mib']} MiB", d["gw_margen_ram"]],
             ["Créditos de CPU", f"Gana {g['creditos_por_hora']} créditos por hora", f"Consume {d['gw_cred_c']} por hora", f"Saldo +{g['creditos_por_hora'] - int(d['gw_cred_c'])} por hora"],
             ["Sesiones y solicitudes", "—", f"{c['sesiones_simultaneas']} sesiones, {c['solicitudes_por_s']} solicitudes por segundo", "Supuesto S-33; se mide en S2"]]
    return (["Recurso", "Capacidad de t3.micro", "Carga de diseño", "Margen"], filas, [3.0, 6.0, 5.0, 3.0], False)


def t_costo(x, d):
    x, cd = fuentes()
    c = cd.costo()
    filas = [[l["concepto"], coma(l["cantidad"], 0) + " " + l["unidad"], coma(l["precio_unitario"], 4 if l["precio_unitario"] < 0.1 else 2), coma(l["total"], 2)] for l in c["lineas"]]
    filas.append(["**Total mensual 24×7**", "", "", f"**{coma(c['total'], 2)}**"])
    return (["Concepto", "Cantidad", "Precio (US$)", "US$/mes"], filas, [8.0, 3.2, 3.0, 2.8], False)


def t_nat(x, d):
    x, cd = fuentes()
    c = cd.costo()
    filas = [[a["opcion"], coma(a["precio_hora"], 4), coma(a["mensual"], 2), pct(a["mensual"] / c["total"], 0), a.get("nota", "")] for a in c["nat_alternativas"]]
    filas.append(["**Diseño elegido: NAT-DR solo en el simulacro T59**", coma(0.0104, 4), f"{coma(c['simulacro_total'], 2)} por simulacro de {c['simulacro_horas']} h", "—", "EC2-DR (t3.small) y NAT-DR (t3.micro) juntos; se destruyen al terminar"])
    return (["Opción", "US$/h", "US$/mes", "% del costo 24×7", "Nota"], filas, [5.2, 1.6, 3.2, 2.0, 5.0], False)


def t_continuidad(x, d):
    x, cd = fuentes()
    filas = [[s["id"], s["servicio"], cd.criticidad_servicio(s), s["redundancia"], s["respaldo"], s["rto_texto"], s["rpo_texto"]] for s in cd.servicios.values()]
    return (["ID", "Servicio", "Criticidad", "Redundancia", "Respaldo", "RTO", "RPO"], filas, [1.2, 3.0, 1.6, 4.0, 4.2, 1.8, 1.4], False)


def t_regla_respaldo(x, d):
    x, cd = fuentes()
    r = cd.continuidad["regla_3_2_1_1_0"]
    filas = [[str(c["n"]), c["que"], c["donde"], c["medio"], "Sí" if c["fuera_del_sitio"] else "No", "Sí" if c["inmutable"] else "No"] for c in r["copias"]]
    return (["Copia", "Qué es", "Dónde", "Medio", "Fuera del sitio", "Inmutable"], filas, [1.2, 5.0, 3.8, 3.2, 2.0, 1.8], False)


def t_decisiones(x, d):
    x, cd = fuentes()
    return (["ID", "Decisión"], [[i, x.decisiones[i]["decision"]] for i in cd.raw["contexto"]["decisiones"]], [1.8, 15.2], False)


def t_supuestos(x, d):
    x, cd = fuentes()
    usados = ["S-04", "S-08", "S-11", "S-12", "S-13", "S-14", "S-26", "S-29", "S-30", "S-33"]
    filas = [[s, x.supuestos[s]["supuesto"], re.sub(r"\s+", " ", str(x.supuestos[s]["valor"])), x.supuestos[s]["validacion"]] for s in usados]
    return (["ID", "Supuesto", "Valor", "Cómo se valida"], filas, [1.3, 4.2, 7.0, 4.5], False)


def t_ci(x, d):
    txt = CAMBIOS_MD.read_text(encoding="utf-8")
    filas = []
    for m in re.finditer(r"^### (CI-(\d+)) — (.+?)\n- \*\*Estado:\*\* (.+?)\n", txt, re.M):
        if int(m.group(2)) >= 77:
            filas.append([m.group(1), m.group(3), "Abierto" if m.group(4).startswith("abierto") else "Resuelto"])
    return (["CI", "Asunto", "Estado"], filas, [1.8, 12.0, 2.4], False)


def t_emulada(x, d):
    ve = _verificaciones_e()
    filas = [[c["id"], c["comprobacion"], c["resultado"] + " (emulado)"] for c in ve.get("comprobaciones", [])]
    return (["Comprobación", "Qué se verificó en el AWS Emulator", "Resultado"], filas, [2.2, 11.8, 3.0], False)


TABLAS = {n[2:]: f for n, f in globals().items() if n.startswith("t_") and callable(f)}


# ==================================================================================================
# Constructor del documento (hereda de CE0311)
# ==================================================================================================
class ConstructorDC(e1.Constructor):
    def _es_apaisado(self, b) -> bool:
        if b[0] == "figura":
            return b[1] != "DC-0"
        return b[0] == "tabla" and b[1] in TABLAS and TABLAS[b[1]](self.x, self.d)[3]

    def figura(self, fid: str, observar: str):
        x, cd = fuentes()
        if fid == "FIG-5.4":
            ref = cd.raw["referencia_hibrida"]
            png, leyenda = RAIZ / ref["origen"], ref["leyenda"]
        else:
            png, leyenda = DIAGRAMAS / f"{fid}.png", cd.raw["figuras"][fid]["leyenda"]
        if not png.exists():
            raise SystemExit(f"Falta {png.relative_to(RAIZ)}: ejecute make diagrams-dc")
        apaisada = fid != "DC-0"
        if apaisada and not self.ultimo_fue_figura:
            self.salto_seccion(apaisada=False)
        from PIL import Image
        with Image.open(png) as im:
            ratio = im.size[0] / im.size[1]
        ancho_cm = min(e1.ANCHO_APAISADO / e1.CM_TWIPS, 12.6 * ratio) if apaisada else min(e1.ANCHO_VERTICAL / e1.CM_TWIPS, 11.0 * ratio)
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        e1._espaciado(p, 0, 60)
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(str(e1.png_reducido(png, ancho_cm, dpi=260)), width=Cm(ancho_cm))
        self._mover(p._p)
        pie = self.doc.add_paragraph()
        pie._p.insert(0, copy.deepcopy(self.ppr_pie))
        e1._espaciado(pie, 40, 40)
        pie.paragraph_format.keep_with_next = True
        e1._run_fmt(pie.add_run(leyenda), 9, cursiva=True, color="595959")
        self._mover(pie._p)
        self.parrafo(observar, tam=9.5, despues=120, alinear=WD_ALIGN_PARAGRAPH.CENTER if not apaisada else None)
        if apaisada:
            self.salto_seccion(apaisada=True)
        self.figuras.append(fid)
        self.ultimo_fue_figura = apaisada

    def portada(self):
        super().portada()
        x, cd = fuentes()

        def poner(par, texto):
            runs = par.runs
            runs[0].text = texto
            for r in runs[1:]:
                r._r.getparent().remove(r._r)
        for par in self.doc.paragraphs[:40]:
            t = par.text.strip()
            if t.startswith("Análisis y Diseño de Red"):
                poner(par, "Análisis y Diseño de Centro de Datos Híbrido: Informe de análisis y diseño del centro de datos híbrido Celeris Edge")
            elif t.startswith("Versión "):
                poner(par, f"Versión {cd.meta['version']} · centro de datos {cd.meta['fecha']} · inventario v{x.inv['meta']['inventario_version']} · huella {huella_dc()}")

    def construir(self):
        x, cd = fuentes()
        self.portada()
        h_toc, titulos = self.limpiar_guia()
        estilo_toc = h_toc.find(qn("w:pPr") + "/" + qn("w:pStyle"))
        if estilo_toc is not None:
            estilo_toc.getparent().remove(estilo_toc)
        por_titulo, pre, anexos = self.secciones_md()
        reales = [e1._texto(t).strip() for t in titulos]
        sobran = set(por_titulo) - set(reales)
        if sobran:
            raise SystemExit(f"Títulos del texto que no están en la plantilla: {sorted(sobran)}")
        faltan = [t for t in reales if t not in por_titulo and re.match(r"^\d+\. ", t)]
        if faltan:
            raise SystemExit(f"Secciones de la plantilla sin texto: {faltan}")
        self.ancla = h_toc.getprevious()
        self.render(pre)
        salto = self.doc.add_paragraph()
        salto.add_run().add_break(__import__("docx").enum.text.WD_BREAK.PAGE)
        self._mover(salto._p)
        for t, nombre in zip(titulos, reales):
            self.ancla = t
            self.render(por_titulo.get(nombre, []))
        self.render(anexos, salto_h1=True)
        self._quitar_separadores_antes_de_salto()
        self._cabecera()
        self.doc.core_properties.title = "Informe de análisis y diseño de centro de datos híbrido — Celeris Edge (CE0331)"
        self.doc.core_properties.author = e1.equipo()
        self.doc.core_properties.comments = f"Generado por docs/infra/e2/build_informe.py; huella de la fuente {huella_dc()}"
        return self.doc


def _parchear_e1():
    e1.PLANTILLA, e1.TEXTO, e1.TABLAS, e1.datos, e1.AREA = PLANTILLA, TEXTO, TABLAS, datos, AREA
    e1.EVIDENCIAS_E = EVIDENCIAS_E


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", default=str(SALIDA))
    ap.add_argument("--pdf", action="store_true", help="actualiza la tabla de contenidos y exporta el PDF")
    a = ap.parse_args(argv)
    x, cd = fuentes()
    _parchear_e1()
    c = ConstructorDC(x)
    doc = c.construir()
    salida = Path(a.salida)
    salida.mkdir(parents=True, exist_ok=True)
    ruta = salida / nombre_docx(cd)
    doc.save(str(ruta))
    print(ruta.relative_to(RAIZ) if ruta.is_relative_to(RAIZ) else ruta)
    print(f"figuras: {len(c.figuras)} ({', '.join(c.figuras)}) · [COMPLETAR] pendientes: {len(set(c.completar))}")
    if a.pdf:
        info = e1.exportar_pdf(ruta)
        info["figuras"] = c.figuras
        info["completar"] = sorted(set(c.completar))
        info["commit_fuente"] = huella_dc()
        info["huella_fuente"] = huella_dc()
        info["version"] = cd.meta["version"]
        import hashlib
        info["fig54_sha256"] = hashlib.sha256((RAIZ / cd.raw["referencia_hibrida"]["origen"]).read_bytes()).hexdigest()
        PAGINAS_JSON.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"PDF: {info['pdf']} · {info.get('paginas')} páginas · {info['motor']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
