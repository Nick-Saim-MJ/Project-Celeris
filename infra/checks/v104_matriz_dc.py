"""Gancho V-104+ — Matriz de componentes y dimensionamiento del centro de datos (CE0331), al estilo de V-60.

Lee entregables/CE0331/Matriz_Componentes_DC_v<versión>.xlsx (lo genera infra/gen/xlsx_centro_datos.py):
    V-104  El archivo existe, abre y tiene las 6 hojas.
    V-105  «Componentes» = 100 % de lo dibujado en DC-0…DC-3 y viceversa; ninguna celda obligatoria vacía; criticidad válida y
           coherente con el inventario / centro_datos.yaml; sin «Por qué existe» repetido.
    V-106  «Máquinas virtuales» es 1 a 1 con centro_datos.yaml (vCPU, RAM, disco, caché) y trae las sumas como fórmulas.
    V-107  Las fórmulas recalculan sin errores (Excel o LibreOffice) y los valores recalculados coinciden con el cálculo en Python
           (núcleos, RAM, disco, holguras, costo mensual); el recálculo es del archivo actual.
"""
import hashlib
import json
import sys
from pathlib import Path

GRUPO = "E2"
PRIMER_ID = "V-104"
DESCRIPCION = "Matriz de componentes y dimensionamiento del centro de datos: hojas, 100 % de lo dibujado, VM y fórmulas recalculadas"

_INFRA = Path(__file__).resolve().parents[1]
for _p in (str(_INFRA), str(_INFRA / "gen")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

GENERAR = "python infra/gen/xlsx_centro_datos.py --verificar"


def run(infra):
    from openpyxl import load_workbook
    from validate import E, Resultado, W, estado_de

    import centro_datos as cdm
    import xlsx_centro_datos as gd

    cd = cdm.CentroDatos.cargar(infra)
    ruta = gd.SALIDA / gd.nombre_archivo(cd)
    rel = ruta.relative_to(infra.raiz).as_posix()
    res = []

    def resultado(cid, titulo, hs, detalle=""):
        res.append(Resultado(cid, titulo, estado_de(hs), hs, detalle))

    h = []
    try:
        wb = load_workbook(ruta)
    except Exception as exc:  # noqa: BLE001
        resultado("V-104", "Matriz DC: archivo y hojas", [E(f"{rel} no existe o no abre: {exc.__class__.__name__}", GENERAR)])
        return res + [Resultado(f"V-10{i}", "Omitido: V-104 falló", "FALLA", [E("Sin archivo no se evalúa")]) for i in (5, 6, 7)]
    for hoja in gd.HOJAS:
        if hoja not in wb.sheetnames:
            h.append(E(f"Falta la hoja «{hoja}»", GENERAR))
    resultado("V-104", "Matriz DC: archivo y las 6 hojas", h, rel)
    if h:
        return res + [Resultado(f"V-10{i}", "Omitido: faltan hojas", "FALLA", [E("Hojas incompletas")]) for i in (5, 6, 7)]

    # ---- V-105
    h = []
    ws = wb["Componentes"]
    filas = [r for r in ws.iter_rows(min_row=5, values_only=True) if r[0] and not str(r[0]).startswith("=") and r[1] and r[2] != "Resumen" and r[5] in ("Alta", "Media", "Baja")]
    ids = [r[0] for r in filas]
    cob_ruta = infra.raiz / "docs" / "infra" / "e2" / "cobertura-figuras.json"
    if not cob_ruta.exists():
        h.append(E("Falta docs/infra/e2/cobertura-figuras.json (lo escribe V-100)", "python infra/gen/drawio_dc_check.py"))
        dibujados = set()
    else:
        cob = json.loads(cob_ruta.read_text(encoding="utf-8"))
        dibujados = {i for d in cob.values() for i in d["ids"]}
    for i in sorted(dibujados - set(ids)):
        h.append(E(f"{i} está dibujado y no está en la matriz", GENERAR))
    for i in sorted(set(ids) - dibujados):
        h.append(E(f"{i} está en la matriz y no está dibujado", GENERAR))
    if len(ids) != len(set(ids)):
        h.append(E("IDs repetidos en la matriz", GENERAR))
    ex = cd.extras()
    porques = {}
    for r in filas:
        if any(v in (None, "") for v in r[:11]):
            h.append(E(f"{r[0]}: celda obligatoria vacía", GENERAR))
        fuente = infra.componentes[r[0]]["criticidad"] if r[0] in infra.componentes else ex.get(r[0], {}).get("criticidad")
        if r[5] != fuente:
            h.append(E(f"{r[0]}: criticidad {r[5]} ≠ fuente {fuente}", GENERAR))
        if r[2] not in ("On-premise", "AWS"):
            h.append(E(f"{r[0]}: entorno {r[2]} inválido", GENERAR))
        if r[0] in infra.componentes and ((r[2] == "AWS") != ("AWS" in infra.componentes[r[0]]["zonas"])):
            h.append(E(f"{r[0]}: entorno distinto del inventario", GENERAR))
        porques.setdefault(r[9], []).append(r[0])
    for texto, lst in porques.items():
        if len(lst) > 1 and not all(i.startswith(("PG-", "vmnic")) for i in lst):
            h.append(W(f"«Por qué existe» repetido en {', '.join(lst)}", "Cada elemento tiene su propia razón"))
    resultado("V-105", "Matriz DC: 100 % de lo dibujado en DC-0…DC-3 (y viceversa), criticidad y celdas obligatorias", h,
              f"{len(ids)} elementos en la matriz · {len(dibujados)} dibujados")

    # ---- V-106
    h = []
    ws = wb["Máquinas virtuales"]
    vms = {r[0]: r for r in ws.iter_rows(min_row=5, values_only=True) if r[0] in cd.vm_por_id}
    for cid, v in cd.vm_por_id.items():
        r = vms.get(cid)
        if not r:
            h.append(E(f"Falta la VM {cid}", GENERAR))
            continue
        if (r[2], r[3], r[4], r[5]) != (v["vcpu"], v["ram_gb"], v["disco_gb"], v["cache_gb"]) or r[1] != v["fase"]:
            h.append(E(f"{cid}: la fila no coincide con centro_datos.yaml", GENERAR))
    formulas = [c.value for fila in ws.iter_rows(min_row=5 + len(cd.vms)) for c in fila if isinstance(c.value, str) and c.value.startswith("=SUM")]
    if len(formulas) < 6:
        h.append(E("Los totales de las VM deben ser fórmulas (SUMIF/SUM)", GENERAR))
    resultado("V-106", "Matriz DC: máquinas virtuales 1 a 1 con centro_datos.yaml y totales por fórmula", h, f"{len(vms)} VM · {len(formulas)} fórmulas de total")

    # ---- V-107
    h = []
    rec = infra.raiz / "docs" / "infra" / "e2" / "recalculo-xlsx.json"
    if not rec.exists():
        h.append(E("Falta docs/infra/e2/recalculo-xlsx.json", GENERAR))
        resultado("V-107", "Matriz DC: fórmulas recalculadas sin errores y coherentes con el cálculo", h)
        return res
    j = json.loads(rec.read_text(encoding="utf-8"))
    if j.get("sha256") != hashlib.sha256(ruta.read_bytes()).hexdigest():
        h.append(W("El último recálculo es de otra versión del archivo", GENERAR))
    if not j.get("motor"):
        h.append(W(f"No hubo motor de recálculo: {j.get('nota')}", "Instale LibreOffice o Excel"))
    for e in j.get("errores", []):
        h.append(E(f"Fórmula con error: {e}", GENERAR))
    if j.get("sin_valor"):
        h.append(W(f"{j['sin_valor']} fórmulas sin valor tras recalcular", GENERAR))
    v = j.get("valores", {})
    d = cd.dimensionar()
    c = cd.costo()
    esperado = {"Núcleos necesarios": d["nucleos_necesarios"], "RAM requerida con crecimiento": d["ram_con_crecimiento"],
                "Disco total requerido": d["disco_con_copia"], "Holgura de CPU": d["holgura_cpu"],
                "Holgura de RAM tras la sobrecarga de ESXi": d["holgura_ram"], "Margen de RAM tras reservar el crecimiento": d["margen_ram_tras_crecimiento"],
                "Holgura de disco": d["holgura_disco"], "vCPU totales (F2)": d["vcpu"], "AWS: Total mensual 24×7": c["total"], "AWS: Total por hora": c["lab_hora"]}
    for k, val in esperado.items():
        if k not in v:
            h.append(E(f"El recálculo no trae «{k}»", GENERAR))
        elif abs(v[k] - val) > 1e-6 * max(1, abs(val)):
            h.append(E(f"«{k}»: Excel/LibreOffice {v[k]} ≠ Python {val}", GENERAR))
    resultado("V-107", "Matriz DC: fórmulas recalculadas sin errores y coherentes con el cálculo en Python", h,
              f"{j.get('motor')} · {j.get('formulas')} fórmulas · {len(j.get('errores', []))} errores")
    return res
