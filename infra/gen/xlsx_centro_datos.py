"""Genera la Matriz de componentes y dimensionamiento del centro de datos (CE0331, Entregable 2) desde infra/centro_datos.yaml + inventario.

Salida: entregables/CE0331/Matriz_Componentes_DC_v<versión>.xlsx con las hojas
    Portada · Componentes · Máquinas virtuales · Dimensionamiento · AWS y costo · Continuidad

- «Componentes» lista el 100 % de lo dibujado en DC-0…DC-3 (lo que lee de docs/infra/e2/cobertura-figuras.json, que escribe V-100+).
- Los totales y el dimensionamiento son FÓRMULAS visibles (Excel/LibreOffice las recalculan al abrir); cada cifra de entrada sale del YAML.
- `--verificar` recalcula una copia (LibreOffice si está; si no, Excel por COM), busca #REF!, #VALUE!… y guarda los valores calculados
  en docs/infra/e2/recalculo-xlsx.json, que V-107 compara con el cálculo en Python.

    python infra/gen/xlsx_centro_datos.py [--salida DIR] [--verificar]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from celeris_infra import RAIZ, Infra  # noqa: E402
from centro_datos import CentroDatos, coma  # noqa: E402
import xlsx_comun as xc  # noqa: E402
import xlsx_componentes as gx  # noqa: E402
from drawio_dc import FIGURAS_DC, huella_dc  # noqa: E402

SALIDA = RAIZ / "entregables" / "CE0331"
COBERTURA = RAIZ / "docs" / "infra" / "e2" / "cobertura-figuras.json"
RECALCULO = RAIZ / "docs" / "infra" / "e2" / "recalculo-xlsx.json"
HOJAS = ["Portada", "Componentes", "Máquinas virtuales", "Dimensionamiento", "AWS y costo", "Continuidad"]
VM_HOJA = "'Máquinas virtuales'"
RELLENO_CRIT = gx.RELLENO_CRIT
NEG = xc.NEGRITA


def nombre_archivo(cd: CentroDatos) -> str:
    return f"Matriz_Componentes_DC_v{cd.meta['version']}.xlsx"


def crit_celda(c, crit):
    c.fill = xc.relleno(RELLENO_CRIT[crit])
    c.font = NEG


def titulo(ws, texto, sub=None, ancho=10):
    ws["A1"] = texto
    ws["A1"].font = Font(name="Calibri", size=14, bold=True)
    if sub:
        ws["A2"] = sub
        ws["A2"].font = Font(name="Calibri", size=10, italic=True, color="595959")
        ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ancho)
        ws.row_dimensions[2].height = 44


# --------------------------------------------------------------------------------------------------
def hoja_portada(wb, x, cd):
    ws = wb.active
    ws.title = "Portada"
    titulo(ws, "Matriz de componentes y dimensionamiento del centro de datos híbrido — CE0331 (S1, E2)", ancho=4)
    filas = [
        ("Proyecto", x.inv["meta"]["proyecto"]),
        ("Versión de la matriz", f"{cd.meta['version']} · {cd.meta['fecha']} · inventario v{x.inv['meta']['inventario_version']} · huella de la fuente {huella_dc()}"),
        ("Fuente única", "infra/centro_datos.yaml (CE03 D2.3–D2.9) e infra/inventory.yaml. Generado por infra/gen/xlsx_centro_datos.py: no editar a mano."),
        ("Hojas", "Componentes (100 % de lo dibujado en DC-0…DC-3) · Máquinas virtuales (totales por fórmula) · Dimensionamiento (fórmulas visibles) · "
                  "AWS y costo (cantidad × precio [S-12]) · Continuidad (RTO/RPO, redundancia y 3-2-1-1-0)"),
        ("Figuras", "DC-0 Topología ejecutiva · DC-1 Topología física · DC-2 Hipervisor · DC-3 AWS / VPC. La integración híbrida es FIG-5.4 de CE0311, sin cambios."),
        ("Cómo leer las fórmulas", "Las celdas con fondo gris claro son datos de entrada (del YAML); las demás son fórmulas. Cambiar un dato de entrada recalcula todo."),
        ("Pendientes", "CI abiertos que afectan esta matriz: ver la sección 11 del informe (CI-87 y CI-88) y el supuesto S-34 (plazo de reposición del servidor)."),
        ("Regla de seguridad", "Sin claves, tokens ni secretos. IP públicas solo de documentación (RFC 5737)."),
    ]
    for i, (k, v) in enumerate(filas, start=3):
        ws.cell(row=i, column=1, value=k).font = NEG
        c = ws.cell(row=i, column=2, value=v)
        c.alignment = xc.AJUSTE
        ws.merge_cells(start_row=i, start_column=2, end_row=i, end_column=4)
        ws.row_dimensions[i].height = 48
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 60
    ws.column_dimensions["C"].width = 30
    ws.column_dimensions["D"].width = 30
    xc.imprimir_a4(ws)


def filas_componentes(x, cd, cob):
    figs_de: dict[str, list[str]] = {}
    for fig, d in cob.items():
        for i in d["ids"]:
            figs_de.setdefault(i, []).append(fig)
    ex = cd.extras()
    filas = []
    for cid in figs_de:
        figs = ", ".join(sorted(figs_de[cid]))
        if cid in x.componentes:
            c = x.componentes[cid]
            filas.append({"id": cid, "nombre": c["nombre"].split("—", 1)[1].strip() if "—" in c["nombre"] else c["nombre"], "entorno": cd.entorno_de(cid),
                          "tipo": cd.tipo_de(cid), "funcion": c["funcion"], "crit": c["criticidad"], "recursos": cd.recursos_de(cid),
                          "estado": {"diseño": "Vigente", "temporal": "Temporal (T59)", "existente": "Existente (DTI)", "fuera_de_alcance": "Fuera de alcance"}[c["estado"]],
                          "figuras": figs, "por_que": c["por_que"], "si_falla": c["si_falla"], "origen": "inventory.yaml"})
        else:
            e = ex[cid]
            filas.append({"id": cid, "nombre": e["nombre"].split("—", 1)[1].strip(), "entorno": e["entorno"], "tipo": e["tipo"], "funcion": e["funcion"],
                          "crit": e["criticidad"], "recursos": e["recursos"], "estado": "Vigente" if e.get("estado", "diseño") != "temporal" else "Temporal (T59)",
                          "figuras": figs, "por_que": e["por_que"], "si_falla": e["si_falla"], "origen": "centro_datos.yaml"})
    orden = {"On-premise": 0, "AWS": 1}
    filas.sort(key=lambda f: (orden[f["entorno"]], f["figuras"] != "DC-0" and 0, f["id"] not in x.componentes, list(x.componentes).index(f["id"]) if f["id"] in x.componentes else 999, f["id"]))
    return filas


def hoja_componentes(wb, x, cd, cob):
    ws = wb.create_sheet("Componentes")
    titulo(ws, "Componentes del centro de datos (100 % de lo dibujado en DC-0…DC-3)",
           "Una fila por elemento dibujado. Entorno, tipo, función, criticidad y recursos asignados salen del inventario y de centro_datos.yaml. "
           "La criticidad de los elementos propios (port groups, NIC, SG…) es la del componente más crítico al que sirven.", 11)
    cols = ["ID", "Componente", "Entorno", "Tipo", "Función", "Criticidad", "Recursos asignados", "Estado", "Figuras", "Por qué existe", "Si falla", "Origen"]
    anchos = [14, 30, 12, 24, 40, 11, 44, 14, 14, 55, 55, 17]
    xc.escribir_encabezado(ws, 4, cols, anchos)
    filas = filas_componentes(x, cd, cob)
    for i, f in enumerate(filas, start=5):
        xc.escribir_fila(ws, i, [f["id"], f["nombre"], f["entorno"], f["tipo"], f["funcion"], f["crit"], f["recursos"], f["estado"], f["figuras"],
                                 f["por_que"], f["si_falla"], f["origen"]], centrar={1, 3, 6, 8, 9})
        crit_celda(ws.cell(row=i, column=6), f["crit"])
        if f["entorno"] == "AWS":
            xc.celda_zona(ws.cell(row=i, column=3), "AWS")
        ws.cell(row=i, column=1).font = NEG
    ult = 4 + len(filas)
    r = ult + 2
    ws.cell(row=r, column=1, value="Resumen").font = NEG
    ws.cell(row=r + 1, column=1, value="Total de elementos")
    ws.cell(row=r + 1, column=2, value=f"=COUNTA(A5:A{ult})")
    for k, n in enumerate(("Alta", "Media", "Baja")):
        ws.cell(row=r + 2 + k, column=1, value=f"Criticidad {n}")
        ws.cell(row=r + 2 + k, column=2, value=f'=COUNTIF(F5:F{ult},"{n}")')
    for k, ent in enumerate(("On-premise", "AWS")):
        ws.cell(row=r + 5 + k, column=1, value=ent)
        ws.cell(row=r + 5 + k, column=2, value=f'=COUNTIF(C5:C{ult},"{ent}")')
    xc.configurar_hoja(ws, 4, len(cols), ult, congelar="C5")
    return ult


def hoja_vm(wb, x, cd):
    ws = wb.create_sheet("Máquinas virtuales")
    titulo(ws, "Máquinas virtuales de ESX01 (D2.4): recursos por VM y totales por fórmula",
           "Datos de entrada (gris) del YAML, idénticos al inventario (V-91). El disco incluye la caché de EDGE01/02, que va en su NVMe. "
           "Ninguna VM supera 8 vCPU (límite de ESXi gratuito).", 14)
    cols = ["VM", "Fase", "vCPU", "RAM (GB)", "Disco VM (GB)", "Caché (GB)", "Disco total (GB)", "SO", "Port group(s)", "Zona", "Datastore", "Sobreasignación", "Núcleos equivalentes", "≤ 8 vCPU"]
    xc.escribir_encabezado(ws, 4, cols, [12, 7, 8, 10, 12, 11, 13, 14, 26, 12, 20, 15, 14, 10])
    r0 = 5
    ratios = cd.raw["dimensionamiento"]["razones_overcommit"]
    for i, v in enumerate(cd.vms):
        r = r0 + i
        comp = x.componentes[v["componente"]]
        zona = ", ".join(z for z in comp["zonas"] if z in ("MGMT", "SERVERS", "LAB", "DMZ-SVC", "DMZ-HONEY", "SECURITY", "EDGE")) or "TRANSITO + trunk"
        xc.escribir_fila(ws, r, [v["componente"], v["fase"], v["vcpu"], v["ram_gb"], v["disco_gb"], v["cache_gb"], f"=E{r}+F{r}", v["so"],
                                 " + ".join(v["port_groups"]), zona, v["datastore"] + (f" / {v['datastore_cache']}" if v["cache_gb"] else ""),
                                 "2:1" if v["sensible"] else "4:1", f'=C{r}/IF(L{r}="2:1",{ratios["sensible"]},{ratios["resto"]})', f'=IF(C{r}<=8,"Sí","NO")'],
                         centrar={2, 3, 4, 5, 6, 7, 12, 13, 14})
        for col in (3, 4, 5, 6):
            ws.cell(row=r, column=col).fill = xc.relleno("E7E6E6")
        ws.cell(row=r, column=1).font = NEG
    r1 = r0 + len(cd.vms) - 1
    t = r1 + 2
    esp = cd.raw["totales_d24"]
    for k, (etq, crit) in enumerate((("Total F1", '"F1"'), ("Total F2 (F1 + F2)", None))):
        rr = t + k
        ws.cell(row=rr, column=1, value=etq).font = NEG
        for col, letra in ((3, "C"), (4, "D"), (5, "E"), (6, "F"), (7, "G"), (13, "M")):
            f = f"=SUMIF(B{r0}:B{r1},{crit},{letra}{r0}:{letra}{r1})" if crit else f"=SUM({letra}{r0}:{letra}{r1})"
            c = ws.cell(row=rr, column=col, value=f)
            c.font = NEG
    ws.cell(row=t + 2, column=1, value="Esperado D2.4: F1").font = NEG
    ws.cell(row=t + 3, column=1, value="Esperado D2.4: F2").font = NEG
    for k, fase in enumerate(("F1", "F2")):
        rr = t + 2 + k
        for col, key in ((3, "vcpu"), (4, "ram_gb"), (7, "disco_gb")):
            ws.cell(row=rr, column=col, value=esp[fase][key]).fill = xc.relleno("E7E6E6")
        ws.cell(row=rr, column=8, value=f'=IF(AND(C{t + k}=C{rr},D{t + k}=D{rr},G{t + k}=G{rr}),"Coincide con D2.4","REVISAR")').font = NEG
    ws.cell(row=t + 5, column=1, value="Nota").font = NEG
    ws.cell(row=t + 5, column=2, value="ENC01 es una PC física del laboratorio, no una VM. Orden de arranque: FW01 → CTRL01 → EDGE01/02 → SIEM01 → resto.")
    xc.configurar_hoja(ws, 4, len(cols), r1, congelar="B5")
    return {"r0": r0, "r1": r1, "t1": t, "t2": t + 1}


def hoja_dim(wb, x, cd, vm):
    ws = wb.create_sheet("Dimensionamiento")
    d = cd.raw["dimensionamiento"]
    h = cd.host
    titulo(ws, "Dimensionamiento frente a la capacidad del host y de EC2-GW (D2.8)",
           "Cada fila dice qué se calcula, la fórmula visible y el resultado. Datos de entrada con fondo gris. Fase dimensionada: F2 (las 11 VM).", 5)
    xc.escribir_encabezado(ws, 4, ["Concepto", "Valor", "Unidad", "Fórmula / explicación", "Estado"], [52, 14, 12, 70, 28])
    ref: dict[str, str] = {}
    fila = [5]
    r0, r1, t2 = vm["r0"], vm["r1"], vm["t2"]

    def sec(texto):
        c = ws.cell(row=fila[0], column=1, value=texto)
        c.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        for col in range(1, 6):
            ws.cell(row=fila[0], column=col).fill = xc.relleno("1F3864")
        c.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        fila[0] += 1

    def f(clave, concepto, valor, unidad="", expl="", entrada=False, fmt=None, estado=None, negrita=False):
        r = fila[0]
        ref[clave] = f"B{r}"
        xc.escribir_fila(ws, r, [concepto, valor, unidad, expl, estado], centrar={2, 3})
        if entrada:
            ws.cell(row=r, column=2).fill = xc.relleno("E7E6E6")
        if fmt:
            ws.cell(row=r, column=2).number_format = fmt
        if negrita:
            for col in (1, 2):
                ws.cell(row=r, column=col).font = NEG
        fila[0] += 1
        return f"B{r}"

    def R(k):
        return ref[k]

    ratios = d["razones_overcommit"]
    sec("1. CPU: núcleos con sobreasignación 2:1 (VM sensibles) y 4:1 (resto)")
    f("vcpu_sens", "vCPU de las VM sensibles (FW01, EDGE01, EDGE02)", f'=SUMIF({VM_HOJA}!L{r0}:L{r1},"2:1",{VM_HOJA}!C{r0}:C{r1})', "vCPU", "Suma de vCPU con sobreasignación 2:1")
    f("vcpu_resto", "vCPU del resto de las VM", f'=SUMIF({VM_HOJA}!L{r0}:L{r1},"4:1",{VM_HOJA}!C{r0}:C{r1})', "vCPU", "Suma de vCPU con sobreasignación 4:1")
    f("vcpu_total", "vCPU totales (F2)", f"={R('vcpu_sens')}+{R('vcpu_resto')}", "vCPU", "Debe coincidir con 27 de D2.4")
    f("r_sens", "Razón de sobreasignación sensible", ratios["sensible"], ":1", "FW01 y los nodos de caché: ruta crítica de datos", entrada=True)
    f("r_resto", "Razón de sobreasignación del resto", ratios["resto"], ":1", "Cargas con poca ocupación de CPU", entrada=True)
    f("nuc_sens", "Núcleos para las VM sensibles", f"={R('vcpu_sens')}/{R('r_sens')}", "núcleos", "vCPU sensibles ÷ 2", fmt="0.00")
    f("nuc_resto", "Núcleos para el resto", f"={R('vcpu_resto')}/{R('r_resto')}", "núcleos", "vCPU del resto ÷ 4", fmt="0.00")
    f("nuc_nec", "Núcleos necesarios", f"={R('nuc_sens')}+{R('nuc_resto')}", "núcleos", "Suma de los dos anteriores", fmt="0.00", negrita=True)
    f("nuc_host", "Núcleos del host ESX01", h["cpu"]["nucleos"], "núcleos", "12 núcleos [S-08]", entrada=True)
    f("h_cpu", "Holgura de CPU", f"=({R('nuc_host')}-{R('nuc_nec')})/{R('nuc_host')}", "%", "(núcleos del host − necesarios) ÷ núcleos del host", fmt="0.0%", negrita=True,
      estado=f'=IF({"B" + str(fila[0])}>={d["holgura_minima"]},"Cumple ≥ 15 %","Por debajo de 15 %")')
    ws.cell(row=fila[0] - 1, column=5).value = f'=IF({R("h_cpu")}>={d["holgura_minima"]},"Cumple ≥ 15 %","Por debajo de 15 %")'
    f("rel_cpu", "Relación vCPU : núcleos física", f"={R('vcpu_total')}/{R('nuc_host')}", ":1", "27 vCPU sobre 12 núcleos", fmt="0.00")
    sec("2. RAM: × 1,1 de sobrecarga de ESXi × 1,2 de crecimiento")
    f("ram_asig", "RAM asignada a las VM (F2)", f"={VM_HOJA}!D{t2}", "GB", "Suma de la hoja Máquinas virtuales")
    f("k_esxi", "Factor de sobrecarga de ESXi", d["sobrecarga_esxi"], "×", "Memoria del hipervisor y sobrecarga por VM", entrada=True)
    f("k_crec", "Factor de crecimiento", d["crecimiento"], "×", "Reserva del 20 % para crecimiento", entrada=True)
    f("ram_esxi", "RAM con sobrecarga de ESXi", f"={R('ram_asig')}*{R('k_esxi')}", "GB", "asignada × 1,1", fmt="0.0")
    f("ram_crec", "RAM requerida con crecimiento", f"={R('ram_esxi')}*{R('k_crec')}", "GB", "asignada × 1,1 × 1,2 (D2.8)", fmt="0.0", negrita=True)
    f("ram_host", "RAM del host ESX01", h["ram_gb"], "GB", "96 GB [S-08]", entrada=True)
    f("h_ram", "Holgura de RAM tras la sobrecarga de ESXi", f"=({R('ram_host')}-{R('ram_esxi')})/{R('ram_host')}", "%", "(RAM del host − asignada × 1,1) ÷ RAM del host", fmt="0.0%", negrita=True)
    ws.cell(row=fila[0] - 1, column=5).value = f'=IF({R("h_ram")}>={d["holgura_minima"]},"Cumple ≥ 15 %","Por debajo de 15 %")'
    f("m_ram", "Margen de RAM tras reservar el crecimiento", f"=({R('ram_host')}-{R('ram_crec')})/{R('ram_host')}", "%", "(RAM del host − asignada × 1,1 × 1,2) ÷ RAM del host", fmt="0.0%", negrita=True)
    ws.cell(row=fila[0] - 1, column=5).value = f'=IF({R("m_ram")}>={d["holgura_minima"]},"Cumple ≥ 15 %","Por debajo de 15 %")'
    f("ram_libre", "RAM libre tras reservar el crecimiento", f"={R('ram_host')}-{R('ram_crec')}", "GB", "RAM del host − requerida con crecimiento", fmt="0.0")
    sec("3. Disco: × 1,3 más la copia local de restic, sobre el datastore RAID 1")
    f("dk_sin", "Disco de las VM sin caché (F2)", f"={VM_HOJA}!E{t2}", "GB", "Suma de la hoja Máquinas virtuales (774 GB en D2.8)")
    f("k_disco", "Factor de disco", d["factor_disco"], "×", "Instantáneas, sobrecarga y crecimiento", entrada=True)
    f("dk_req", "Disco requerido", f"={R('dk_sin')}*{R('k_disco')}", "GB", "774 × 1,3 (≈ 1 006 GB)", fmt="0.0")
    f("dk_copia", "Copia local de restic", d["copia_local_restic_gb"], "GB", "≈ 200 GB (D2.8)", entrada=True)
    f("dk_tot", "Disco total requerido", f"={R('dk_req')}+{R('dk_copia')}", "GB", "requerido + copia local", fmt="0.0", negrita=True)
    f("dk_cap", "Capacidad del datastore DS-VM", cd.datastores["DS-VM"]["capacidad_gb"], "GB", "2 × SSD de 1,92 TB en RAID 1: capacidad útil de uno", entrada=True)
    f("dk_uso", "Uso del datastore", f"={R('dk_tot')}/{R('dk_cap')}", "%", "total ÷ capacidad (≈ 63 %)", fmt="0.0%")
    f("h_disco", "Holgura de disco", f"=({R('dk_cap')}-{R('dk_tot')})/{R('dk_cap')}", "%", "(capacidad − total) ÷ capacidad", fmt="0.0%", negrita=True)
    ws.cell(row=fila[0] - 1, column=5).value = f'=IF({R("h_disco")}>={d["holgura_minima"]},"Cumple ≥ 15 %","Por debajo de 15 %")'
    sec("4. Caché de los nodos (NVMe sin RAID, un datastore por nodo)")
    for k, did in (("c1", "DS-CACHE1"), ("c2", "DS-CACHE2")):
        ds = cd.datastores[did]
        usado = sum(v["cache_gb"] for v in cd.vms if v.get("datastore_cache") == did)
        f(f"{k}_u", f"Caché de {ds['vm']} en {did}", usado, "GB", "500 GB por nodo como punto de partida [S-04]", entrada=True)
        f(f"{k}_c", f"Capacidad de {did}", ds["capacidad_gb"], "GB", "NVMe de 1 TB", entrada=True)
        f(f"{k}_h", f"Holgura de {did}", f"=({R(k + '_c')}-{R(k + '_u')})/{R(k + '_c')}", "%", "(capacidad − caché) ÷ capacidad", fmt="0.0%",
          estado=f'=IF(B{fila[0]}>={d["holgura_minima"]},"Cumple ≥ 15 %","Por debajo de 15 %")')
    sec("5. Red")
    f("red", "Objetivo desde la caché hacia un laboratorio", d["red"]["objetivo_gbps"], "Gbps", d["red"]["razon"], entrada=True)
    f("red_nic", "Enlaces del host hacia SW-CORE01", 20, "Gbps", "2 × 10 GbE en vSwitch0 (vmnic0 y vmnic1): el objetivo cabe con holgura", entrada=True)
    f("red_acc", "Enlace SW-CORE01 ↔ SW-ACC (1 GbE [S-14])", d["red"]["enlace_acceso_gbps"], "Gbps", "1 GbE por SW-ACC, CI-80", entrada=True)
    f("red_h", "Holgura del enlace de acceso frente al objetivo", f"=({R('red_acc')}-{R('red')})/{R('red_acc')}", "%", "(enlace − objetivo) ÷ enlace: sin holgura, un solo laboratorio a la vez (CI-87)", fmt="0.0%",
      estado=f'=IF(B{fila[0]}>={d["holgura_minima"]},"Cumple ≥ 15 %","Sin holgura: CI-87")')
    f("red_riesgo", "Riesgo declarado", "—", "", d["red"]["riesgo"])
    sec("6. EC2-GW frente a su carga (S-33: carga esperada derivada de S-26; se mide en S2)")
    g = cd.ec2_gw()
    f("g_vcpu", f"vCPU de {g['tipo']}", g["vcpu"], "vCPU", "Tipo de instancia de EC2-GW", entrada=True)
    f("g_base", "Línea base de CPU por vCPU", g["linea_base_por_vcpu"], "%", "t3.micro: 10 % por vCPU", entrada=True, fmt="0%")
    f("g_base_tot", "Línea base de CPU de la instancia", f"={R('g_vcpu')}*{R('g_base')}", "vCPU", "2 × 10 % = 0,20 vCPU sostenidos", fmt="0.00")
    f("g_cpu", "Carga de diseño: CPU media", g["carga_diseno"]["cpu_medio_vcpu"], "vCPU", g["carga_diseno"]["nota"], entrada=True, fmt="0.00")
    f("g_h_cpu", "Margen de CPU", f"=({R('g_base_tot')}-{R('g_cpu')})/{R('g_base_tot')}", "%", "(línea base − carga) ÷ línea base", fmt="0.0%", negrita=True,
      estado=f'=IF(B{fila[0]}>={d["holgura_minima"]},"Cumple ≥ 15 %","Por debajo de 15 %")')
    f("g_ram", "RAM de la instancia", g["ram_gib"] * 1024, "MiB", "1 GiB", entrada=True)
    f("g_ram_u", "Carga de diseño: RAM", g["carga_diseno"]["ram_mib"], "MiB", "SO + Caddy + Coraza CRS, estimado", entrada=True)
    f("g_h_ram", "Margen de RAM", f"=({R('g_ram')}-{R('g_ram_u')})/{R('g_ram')}", "%", "(RAM − carga) ÷ RAM", fmt="0.0%", negrita=True,
      estado=f'=IF(B{fila[0]}>={d["holgura_minima"]},"Cumple ≥ 15 %","Por debajo de 15 %")')
    f("g_cred_g", "Créditos de CPU ganados por hora", g["creditos_por_hora"], "créditos/h", "t3.micro gana 12 créditos por hora", entrada=True)
    f("g_cred_c", "Créditos consumidos por hora con la carga de diseño", f"={R('g_cpu')}*60", "créditos/h", "0,10 vCPU × 60 min", fmt="0.0")
    f("g_cred_m", "Saldo de créditos por hora", f"={R('g_cred_g')}-{R('g_cred_c')}", "créditos/h", "Positivo: el saldo de créditos crece", fmt="0.0")
    f("g_sesiones", "Sesiones simultáneas de diseño", g["carga_diseno"]["sesiones_simultaneas"], "sesiones", "Una por laboratorio (S-26), supuesto S-33", entrada=True)
    f("g_rps", "Solicitudes por segundo de diseño", g["carga_diseno"]["solicitudes_por_s"], "req/s", "Cota superior estimada", entrada=True)
    xc.configurar_hoja(ws, 4, 5, fila[0] - 1, congelar="B5", filtro=False)
    ws.sheet_view.zoomScale = 100
    return ref


def hoja_aws(wb, x, cd):
    ws = wb.create_sheet("AWS y costo")
    c = cd.aws["costo_mensual"]
    titulo(ws, "AWS: recursos, costo mensual 24×7 y costo del laboratorio efímero [S-12]",
           f"{c['nota_precios']}. Confirmar en AWS Pricing Calculator. Datos de entrada con fondo gris; "
           "totales por fórmula.", 7)
    xc.escribir_encabezado(ws, 4, ["Recurso / concepto", "Cantidad", "Unidad", "Precio unitario (US$)", "Total (US$/mes)", "Supuesto", "Nota"], [52, 12, 12, 18, 16, 12, 60])
    r = 5
    for l in c["lineas"]:
        xc.escribir_fila(ws, r, [l["concepto"], l["cantidad"], l["unidad"], l["precio_unitario"], f"=B{r}*D{r}", "[S-12]", l.get("nota", "")], centrar={2, 3, 4, 5, 6})
        for col in (2, 4):
            ws.cell(row=r, column=col).fill = xc.relleno("E7E6E6")
        ws.cell(row=r, column=5).number_format = "0.00"
        r += 1
    r1 = r - 1
    ws.cell(row=r, column=1, value="Total mensual 24×7").font = NEG
    ws.cell(row=r, column=5, value=f"=SUM(E5:E{r1})").font = NEG
    ws.cell(row=r, column=5).number_format = "0.00"
    tot = r
    ws.cell(row=r + 1, column=1, value="Meta de D2.3 (US$/mes)")
    ws.cell(row=r + 1, column=5, value=c["meta_usd"]).fill = xc.relleno("E7E6E6")
    ws.cell(row=r + 2, column=1, value="Referencia de D2.5 (≈)")
    ws.cell(row=r + 2, column=5, value=c["referencial_documento_usd"]).fill = xc.relleno("E7E6E6")
    ws.cell(row=r + 3, column=1, value="Margen frente a la meta")
    ws.cell(row=r + 3, column=5, value=f"=E{r + 1}-E{tot}").number_format = "0.00"
    ws.cell(row=r + 4, column=1, value="Resultado").font = NEG
    ws.cell(row=r + 4, column=5, value=f'=IF(E{tot}<=E{r + 1},"Cumple ≤ US$ 75","Excede la meta")').font = NEG
    r += 7
    ws.cell(row=r, column=1, value="Laboratorio efímero (Modo A): costo por hora").font = NEG
    r += 1
    xc.escribir_encabezado(ws, r, ["Concepto", "Cantidad", "Unidad", "Precio por hora (US$)", "Total (US$/h)", "Supuesto", "Nota"])
    r += 1
    le = c["laboratorio_efimero"]
    a = r
    for l in le["lineas"]:
        xc.escribir_fila(ws, r, [l["concepto"], l["cantidad"], "unidades", l["precio_hora"], f"=B{r}*D{r}", "[S-12]", ""], centrar={2, 3, 4, 5, 6})
        ws.cell(row=r, column=5).number_format = "0.0000"
        r += 1
    ws.cell(row=r, column=1, value="Total por hora").font = NEG
    ws.cell(row=r, column=5, value=f"=SUM(E{a}:E{r - 1})").number_format = "0.0000"
    ws.cell(row=r + 1, column=1, value="Meta de D2.3 (US$/h)")
    ws.cell(row=r + 1, column=5, value=le["meta_usd_hora"]).fill = xc.relleno("E7E6E6")
    ws.cell(row=r + 2, column=1, value="Resultado").font = NEG
    ws.cell(row=r + 2, column=5, value=f'=IF(E{r}<E{r + 1},"Cumple < US$ 0,10/h","Excede")').font = NEG
    r += 5
    ws.cell(row=r, column=1, value="Simulacro de recuperación T59 (recursos temporales)").font = NEG
    r += 1
    xc.escribir_encabezado(ws, r, ["Concepto", "Cantidad", "Horas", "Precio por hora (US$)", "Total (US$)", "Supuesto", "Nota"])
    r += 1
    a = r
    for l in c["simulacro"]["lineas"]:
        xc.escribir_fila(ws, r, [l["concepto"], l["cantidad"], c["simulacro"]["horas"], l["precio_hora"], f"=B{r}*C{r}*D{r}", "[S-12]",
                                 "Precio de lista, us-east-1, noviembre de 2026 [S-12]" if "t3.small" in l["concepto"] else ""], centrar={2, 3, 4, 5, 6})
        ws.cell(row=r, column=5).number_format = "0.0000"
        r += 1
    ws.cell(row=r, column=1, value="Total del simulacro").font = NEG
    ws.cell(row=r, column=5, value=f"=SUM(E{a}:E{r - 1})").number_format = "0.0000"
    r += 3
    ws.cell(row=r, column=1, value="Por qué no hay NAT permanente: alternativas descartadas (mensual)").font = NEG
    r += 1
    xc.escribir_encabezado(ws, r, ["Alternativa", "Horas/mes", "Unidad", "Precio por hora (US$)", "Total (US$/mes)", "% del costo de 24×7", "Nota"])
    r += 1
    for al in cd.aws["nat"]["alternativas"]:
        xc.escribir_fila(ws, r, [al["opcion"], al["horas_mes"], "h", al["precio_hora"], f"=B{r}*D{r}", f"=E{r}/E{tot}", al.get("nota", "")], centrar={2, 3, 4, 5, 6})
        ws.cell(row=r, column=5).number_format = "0.00"
        ws.cell(row=r, column=6).number_format = "0%"
        r += 1
    ws.cell(row=r, column=1, value="Diseño elegido: NAT-DR solo en el simulacro (ver arriba); sin NAT permanente, el endpoint de S3 no cuesta por hora.")
    r += 3
    ws.cell(row=r, column=1, value="Recursos AWS del diseño").font = NEG
    r += 1
    xc.escribir_encabezado(ws, r, ["Recurso", "Tipo / CIDR", "vCPU", "RAM (GiB)", "Almacenamiento", "Estado", "Justificación"])
    r += 1
    inv = x.componentes
    filas = [("AWS-VPC", inv["AWS-VPC"]["cidr"], "", "", "", "Vigente", inv["AWS-VPC"]["por_que"]),
             ("AWS-PUB-A", inv["AWS-PUB-A"]["cidr"] + " · pública · AZ a", "", "", "", "Vigente", inv["AWS-PUB-A"]["por_que"]),
             ("AWS-APP-A", inv["AWS-APP-A"]["cidr"] + " · privada · AZ a", "", "", "", "Vigente", inv["AWS-APP-A"]["por_que"])]
    for i in cd.aws["instancias"]:
        filas.append((i["componente"], i["tipo"], i["vcpu"], i["ram_gib"], f"{i['ebs_gb']} GB {i['ebs_tipo']}" if i.get("ebs_gb") else "—",
                      "Temporal (T59)" if i.get("temporal") else "Vigente", i["por_que"]))
    filas.append(("S3", "celeris-backups", "", "", "≈ 300 GB, Object Lock 30 d", "Vigente", inv["S3"]["por_que"]))
    for fila in filas:
        xc.escribir_fila(ws, r, list(fila), centrar={3, 4, 6})
        r += 1
    xc.configurar_hoja(ws, 4, 7, r, congelar="B5", filtro=False)
    return tot


def hoja_continuidad(wb, x, cd):
    ws = wb.create_sheet("Continuidad")
    co = cd.continuidad
    titulo(ws, "Continuidad: RTO y RPO por servicio, redundancia, respaldo y regla 3-2-1-1-0 (D2.9)",
           "RTO/RPO objetivo preliminar: se valida en el entregable de implementación de S2 (prueba T59 para la consola). La criticidad del servicio es la del "
           "componente más crítico que lo presta. Límite de la clase Alta: RTO ≤ 240 min y RPO ≤ 1 440 min.", 11)
    cols = ["ID", "Servicio", "Componentes", "Criticidad", "Redundancia", "Respaldo", "RTO", "RTO (min)", "RPO", "RPO (min)", "Límite RTO de la clase (min)", "¿Cumple?", "Prueba"]
    xc.escribir_encabezado(ws, 4, cols, [8, 28, 18, 11, 36, 38, 26, 10, 16, 10, 14, 14, 9])
    r = 5
    lim = co["limites_por_criticidad"]
    for s in cd.servicios.values():
        crit = cd.criticidad_servicio(s)
        xc.escribir_fila(ws, r, [s["id"], s["servicio"], ", ".join(s["componentes"]), crit, s["redundancia"], s["respaldo"], s["rto_texto"], s["rto_min"] if s["rto_min"] is not None else s["rto_supuesto"],
                                 s["rpo_texto"], s["rpo_min"] if s["rpo_min"] is not None else "n/a", lim[crit]["rto_max_min"] if crit in lim else "—",
                                 f'=IF(K{r}="—","Sin límite de clase",IF(ISNUMBER(H{r}),IF(H{r}<=K{r},"Cumple","Excede"),"Pendiente "&H{r}))', s.get("prueba") or "—"], centrar={1, 4, 8, 10, 11, 12, 13})
        crit_celda(ws.cell(row=r, column=4), crit)
        ws.cell(row=r, column=8).fill = xc.relleno("E7E6E6")
        r += 1
    ultimo = r - 1
    ws.cell(row=r, column=2, value="Servicios con RTO y RPO").font = NEG
    ws.cell(row=r, column=8, value=f"=COUNTA(H5:H{ultimo})")
    ws.cell(row=r + 1, column=2, value="Servicios que exceden su clase").font = NEG
    ws.cell(row=r + 1, column=8, value=f'=COUNTIF(L5:L{ultimo},"Excede")')
    ws.cell(row=r + 2, column=2, value="Objetivo D2.3: RTO de la consola ≤ 120 min").font = NEG
    ws.cell(row=r + 2, column=8, value=f'=IF(H{5 + list(cd.servicios).index("CT-03")}<=120,"Cumple","Excede")')
    r += 5
    ws.cell(row=r, column=1, value="Regla 3-2-1-1-0").font = Font(name="Calibri", size=12, bold=True)
    r += 1
    xc.escribir_encabezado(ws, r, ["N.º", "Copia", "Dónde", "Medio", "Fuera del sitio", "Inmutable"])
    r += 1
    a = r
    for c in co["regla_3_2_1_1_0"]["copias"]:
        xc.escribir_fila(ws, r, [c["n"], c["que"], c["donde"], c["medio"], "Sí" if c["fuera_del_sitio"] else "No", "Sí" if c["inmutable"] else "No"], centrar={1, 5, 6})
        r += 1
    b = r - 1
    ws.cell(row=r, column=1, value="3 copias").font = NEG
    ws.cell(row=r, column=2, value=f"=COUNTA(B{a}:B{b})")
    ws.cell(row=r, column=3, value=f'=IF(B{r}>=3,"Cumple","Falta")')
    ws.cell(row=r + 1, column=1, value="2 medios").font = NEG
    ws.cell(row=r + 1, column=2, value=len(co["regla_3_2_1_1_0"]["medios"]))
    ws.cell(row=r + 1, column=3, value=f'=IF(B{r + 1}>=2,"Cumple","Falta")')
    ws.cell(row=r + 1, column=4, value="; ".join(co["regla_3_2_1_1_0"]["medios"]))
    ws.cell(row=r + 2, column=1, value="1 fuera del sitio").font = NEG
    ws.cell(row=r + 2, column=2, value=f'=COUNTIF(E{a}:E{b},"Sí")')
    ws.cell(row=r + 2, column=3, value=f'=IF(B{r + 2}>=1,"Cumple","Falta")')
    ws.cell(row=r + 3, column=1, value="1 inmutable").font = NEG
    ws.cell(row=r + 3, column=2, value=f'=COUNTIF(F{a}:F{b},"Sí")')
    ws.cell(row=r + 3, column=3, value=f'=IF(B{r + 3}>=1,"Cumple","Falta")')
    ws.cell(row=r + 3, column=4, value=f"{co['regla_3_2_1_1_0']['inmutable']['mecanismo']} de {co['regla_3_2_1_1_0']['inmutable']['dias']} días")
    ws.cell(row=r + 4, column=1, value="0 errores").font = NEG
    ws.cell(row=r + 4, column=2, value=co["regla_3_2_1_1_0"]["cero_errores"])
    ws.merge_cells(start_row=r + 4, start_column=2, end_row=r + 4, end_column=6)
    ws.cell(row=r + 5, column=1, value="Límite").font = NEG
    ws.cell(row=r + 5, column=2, value=co["regla_3_2_1_1_0"]["limite"])
    ws.merge_cells(start_row=r + 5, start_column=2, end_row=r + 5, end_column=6)
    ws.cell(row=r + 5, column=2).alignment = xc.AJUSTE
    ws.row_dimensions[r + 5].height = 34
    r += 8
    sp = co["punto_unico_de_falla"]
    ws.cell(row=r, column=1, value=f"Punto único de falla: {sp['elemento']}").font = Font(name="Calibri", size=12, bold=True)
    ws.cell(row=r + 1, column=1, value="Por qué")
    ws.cell(row=r + 1, column=2, value=sp["por_que"])
    ws.merge_cells(start_row=r + 1, start_column=2, end_row=r + 1, end_column=8)
    for k, m in enumerate(sp["mitigaciones"]):
        ws.cell(row=r + 2 + k, column=1, value=f"Mitigación {k + 1}")
        ws.cell(row=r + 2 + k, column=2, value=m)
        ws.merge_cells(start_row=r + 2 + k, start_column=2, end_row=r + 2 + k, end_column=8)
    k = len(sp["mitigaciones"])
    ws.cell(row=r + 2 + k, column=1, value="Pendiente")
    ws.cell(row=r + 2 + k, column=2, value=sp["pendiente"] + " " + sp["plazo"])
    ws.merge_cells(start_row=r + 2 + k, start_column=2, end_row=r + 2 + k, end_column=8)
    xc.configurar_hoja(ws, 4, len(cols), ultimo, congelar="C5", filtro=False)


# --------------------------------------------------------------------------------------------------
def cargar_cobertura() -> dict:
    if not COBERTURA.exists():
        raise SystemExit("Falta docs/infra/e2/cobertura-figuras.json: ejecute python infra/gen/drawio_dc_check.py (o make validate) tras generar los diagramas")
    return json.loads(COBERTURA.read_text(encoding="utf-8"))


def generar(x: Infra, cd: CentroDatos, salida: Path = SALIDA) -> Path:
    cob = cargar_cobertura()
    wb = Workbook()
    hoja_portada(wb, x, cd)
    hoja_componentes(wb, x, cd, cob)
    vm = hoja_vm(wb, x, cd)
    hoja_dim(wb, x, cd, vm)
    hoja_aws(wb, x, cd)
    hoja_continuidad(wb, x, cd)
    xc.propiedades(wb, "Matriz de componentes y dimensionamiento del centro de datos — CE0331", cd.meta["fecha"])
    ruta = salida / nombre_archivo(cd)
    xc.guardar_reproducible(wb, ruta)
    return ruta


def verificar(ruta: Path, cd: CentroDatos) -> dict:
    """Recalcula una copia y guarda los valores de la hoja Dimensionamiento (concepto → valor) para V-107."""
    res = gx.verificar(ruta)
    valores = {}
    if res.get("motor"):
        with tempfile.TemporaryDirectory() as tmp:
            origen = Path(tmp) / ruta.name
            shutil.copy(ruta, origen)
            destino = Path(tmp) / ("recalc_" + ruta.name)
            gx.recalcular_copia(origen, destino)
            wb = load_workbook(destino, data_only=True)
            ws = wb["Dimensionamiento"]
            for fila in ws.iter_rows(min_row=5, values_only=True):
                if fila[0] and fila[1] is not None and not isinstance(fila[1], str):
                    valores[fila[0]] = fila[1]
            wa = wb["AWS y costo"]
            for fila in wa.iter_rows(min_row=5, values_only=True):
                if fila[0] in ("Total mensual 24×7", "Total por hora"):
                    valores["AWS: " + fila[0]] = fila[4]
            res["estados"] = {fila[0]: fila[4] for fila in ws.iter_rows(min_row=5, values_only=True) if fila[0] and fila[4]}
    res["valores"] = valores
    res["huella_fuente"] = huella_dc()
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", default=str(SALIDA))
    ap.add_argument("--verificar", action="store_true", help="recalcula una copia y registra errores de fórmula y valores (V-107)")
    a = ap.parse_args(argv)
    x = Infra.cargar()
    cd = CentroDatos.cargar(x)
    ruta = generar(x, cd, Path(a.salida))
    print(ruta.relative_to(RAIZ) if ruta.is_relative_to(RAIZ) else ruta)
    if a.verificar:
        res = verificar(ruta, cd)
        RECALCULO.parent.mkdir(parents=True, exist_ok=True)
        RECALCULO.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"recálculo: {res['motor'] or 'sin motor'} · {res['formulas']} fórmulas · {len(res['errores'])} errores · {res['sin_valor']} sin valor {res['nota']}")
        for e in res["errores"]:
            print("  ", e)
        return 1 if res["errores"] or not res["motor"] else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
