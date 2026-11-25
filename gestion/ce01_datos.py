"""Cargador de la fuente única de CE01: gestion/ce01.yaml + las referencias que declara.

    python gestion/ce01_datos.py            # resumen de control (CAPEX, OPEX, beneficios)

Ningún script de CE01 lee cifras de otro lado. Este módulo:
  - resuelve las referencias «archivo#ruta.en.el.yaml» (infra/centro_datos.yaml, infra/trazabilidad.yaml…);
  - lee los supuestos S-xx de infra/trazabilidad.yaml y comprueba que la «lectura numérica» declarada en
    gestion/ce01.yaml siga apareciendo, tal cual, en el `valor` del supuesto (CI-97). Si alguien cambia un supuesto y
    no actualiza la lectura, falla en lugar de usar una cifra vieja;
  - expone costos(), beneficios(), supuestos(), objetivos(), estilo() y datos() (cadenas ya formateadas para
    {{dato:clave}} en los informes).

Los cálculos de economia.opex y economia.beneficios de ce01.yaml se implementan aquí, uno por ID; validar() comprueba
que cada ID del YAML tenga su implementación y viceversa.
"""
from __future__ import annotations

import re
import sys
from functools import lru_cache
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
CE01_YAML = RAIZ / "gestion" / "ce01.yaml"
TRAZ = RAIZ / "infra" / "trazabilidad.yaml"
MARCO = RAIZ / "docs" / "celeris" / "Celeris-00-Marco-Comun.md"


class DatosCE01Error(Exception):
    """Dato faltante, referencia rota o lectura numérica que ya no coincide con la fuente."""


# ==================================================================================================
# Lectura y referencias
# ==================================================================================================
@lru_cache(maxsize=None)
def _yaml(ruta: str) -> dict:
    p = RAIZ / ruta
    if not p.exists():
        raise DatosCE01Error(f"No existe {ruta}")
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def cargar() -> dict:
    return _yaml("gestion/ce01.yaml")


def resolver(ref: str):
    """«infra/centro_datos.yaml#energia.consumo_w» → valor. Las claves se separan con «.»."""
    archivo, _, ruta = ref.partition("#")
    if archivo.endswith(".md"):
        return _frontmatter(archivo)[ruta]
    nodo = _yaml(archivo)
    for clave in filter(None, ruta.split(".")):
        if not isinstance(nodo, dict) or clave not in nodo:
            raise DatosCE01Error(f"Referencia rota: {ref} (no existe «{clave}»)")
        nodo = nodo[clave]
    return nodo


def _frontmatter(archivo: str) -> dict:
    txt = (RAIZ / archivo).read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---", txt, re.S)
    if not m:
        raise DatosCE01Error(f"{archivo} no tiene encabezado YAML")
    return yaml.safe_load(m.group(1))


def equipo() -> list[str]:
    return list(resolver(cargar()["meta"]["equipo"]))


def estilo() -> dict:
    return cargar()["estilo"]


def objetivos() -> list[dict]:
    return list(resolver(cargar()["referencias"]["objetivos"]))


# ==================================================================================================
# Supuestos
# ==================================================================================================
def _normalizar(t: str) -> str:
    return re.sub(r"\s+", " ", str(t)).strip()


@lru_cache(maxsize=None)
def supuestos() -> dict[str, dict]:
    """{S-xx: {clave: valor numérico}} de los supuestos que usa CE01, verificados contra infra/trazabilidad.yaml."""
    catalogo = _yaml("infra/trazabilidad.yaml")["supuestos"]
    out: dict[str, dict] = {}
    for sid, lecturas in cargar()["referencias"]["supuestos"].items():
        if sid not in catalogo:
            raise DatosCE01Error(f"{sid} no existe en infra/trazabilidad.yaml → supuestos")
        if catalogo[sid].get("estado") == "retirado":
            raise DatosCE01Error(f"{sid} está retirado: CE01 no puede usarlo")
        valor = _normalizar(catalogo[sid]["valor"])
        out[sid] = {}
        for clave, (num, texto) in (lecturas or {}).items():
            if _normalizar(texto) not in valor:
                raise DatosCE01Error(
                    f"{sid}.{clave}: el texto «{texto}» ya no aparece en el valor del supuesto («{valor}»). "
                    "Actualice la lectura en gestion/ce01.yaml → referencias.supuestos")
            out[sid][clave] = num
    return out


def s(ref: str) -> float:
    """«S-03.usd_mbps_mes» → 8."""
    sid, _, clave = ref.partition(".")
    try:
        return supuestos()[sid][clave]
    except KeyError as e:
        raise DatosCE01Error(f"Lectura {ref} no declarada en gestion/ce01.yaml → referencias.supuestos") from e


def texto_supuesto(sid: str) -> dict:
    """El supuesto completo tal como está en infra/trazabilidad.yaml (para anexos)."""
    return _yaml("infra/trazabilidad.yaml")["supuestos"][sid]


# ==================================================================================================
# Modelo económico base
# ==================================================================================================
def aws_mensual() -> float:
    """Suma exacta de C1–C7 (sin redondear: el anual se calcula sobre la suma exacta, no sobre US$ 69,58)."""
    return sum(l["cantidad"] * l["precio_unitario"] for l in resolver(cargar()["referencias"]["aws_lineas"]))


def _opex_impl(capex_total: float) -> dict[str, float]:
    eco = cargar()["economia"]
    consumo_w = resolver(cargar()["referencias"]["consumo_w"])
    return {
        "OX-1": aws_mensual() * 12,
        "OX-2": consumo_w * eco["horas_anio"] / 1000 * s("S-09.usd_kwh"),
        "OX-3": s("S-41.mant_fraccion") * capex_total,
    }


def mbps_diferidos() -> float:
    """S-40 = BHR [S-04] × enlace [S-02]."""
    return s("S-04.bhr") * s("S-02.enlace_mbps")


def _beneficios_impl() -> dict[str, float]:
    return {
        "BN-1": mbps_diferidos() * s("S-03.usd_mbps_mes") * 12,
        "BN-2": s("S-01.pcs") * s("S-06.ciclos_anio") * s("S-07.horas_pc_ciclo") * s("S-07.tarifa_usd_h"),
    }


def costos() -> dict:
    eco = cargar()["economia"]
    capex = [{**c, "usd": float(s(c["de"]))} for c in eco["capex"]]
    total = sum(c["usd"] for c in capex)
    impl = _opex_impl(total)
    opex = [{**o, "usd": round(impl[o["id"]], 2)} for o in eco["opex"]]
    oper = sum(o["usd"] for o in opex if o["tipo"] == "operacion")
    mant = sum(o["usd"] for o in opex if o["tipo"] == "mantenimiento")
    return {"capex": capex, "capex_total": total, "opex": opex, "opex_operacion": round(oper, 2),
            "opex_mantenimiento": round(mant, 2), "opex_total": round(oper + mant, 2),
            "aws_mensual": aws_mensual(), "consumo_w": resolver(cargar()["referencias"]["consumo_w"])}


def beneficios() -> dict:
    impl = _beneficios_impl()
    lista = [{**b, "usd": round(impl[b["id"]], 2)} for b in cargar()["economia"]["beneficios"]]
    return {"lista": lista, "total": round(sum(b["usd"] for b in lista), 2), "mbps_diferidos": mbps_diferidos()}


def flujo_neto_anual() -> float:
    return round(beneficios()["total"] - costos()["opex_total"], 2)


def van() -> float:
    """VAN del caso base: −I0 + flujo neto constante descontado al COK [S-10] en el horizonte (P2 lo amplía)."""
    n, k = cargar()["economia"]["horizonte_anios"], s("S-10.cok")
    return round(-costos()["capex_total"] + sum(flujo_neto_anual() / (1 + k) ** t for t in range(1, n + 1)), 2)


def payback_meses() -> float:
    """Meses para recuperar I0 con el flujo neto mensual constante del caso base."""
    return costos()["capex_total"] / (flujo_neto_anual() / 12)


# ==================================================================================================
# Formato (español del Perú: miles con espacio, decimales con coma)
# ==================================================================================================
def num(x: float, dec: int = 0) -> str:
    t = f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")
    return t


def usd(x: float, dec: int = 0) -> str:
    """«US$ 1 234»; los negativos con signo menos tipográfico delante: «−US$ 774»."""
    return ("−" if round(x, dec) < 0 else "") + f"US$ {num(abs(x), dec)}"


def pct(x: float, dec: int = 0) -> str:
    return f"{num(x * 100, dec)} %"


def datos() -> dict[str, str]:
    """Cadenas para {{dato:clave}}. Los informes nunca escriben estas cifras a mano."""
    c, b = costos(), beneficios()
    d = {
        "capex_total": usd(c["capex_total"]),
        "opex_total": usd(c["opex_total"]),
        "opex_operacion": usd(c["opex_operacion"]),
        "opex_mantenimiento": usd(c["opex_mantenimiento"]),
        "aws_mensual": usd(c["aws_mensual"], 2),
        "consumo_w": f"{num(c['consumo_w'])} W",
        "mbps_diferidos": f"{num(b['mbps_diferidos'])} Mbps",
        "beneficio_total": usd(b["total"]),
        "flujo_neto_anual": usd(flujo_neto_anual()),
        "horizonte_anios": f"{cargar()['economia']['horizonte_anios']} años",
        "cok": pct(s("S-10.cok")),
        "van": usd(van()),
        "payback_meses": f"{num(payback_meses(), 1)} meses",
    }
    for x in c["capex"] + c["opex"] + b["lista"]:
        d[x["id"].lower().replace("-", "_")] = usd(x["usd"])
    return d


# ==================================================================================================
# Validación (la usa gestion/validate_ce01.py)
# ==================================================================================================
def validar(avisos: list[str] | None = None) -> list[str]:
    """Lista de errores; vacía si la fuente única de CE01 es coherente. Lo que falta pero está declarado (p. ej. una
    fila RACI con `nota`) va a `avisos` si se pasa una lista."""
    errores: list[str] = []
    avisos = avisos if avisos is not None else []
    try:
        y = cargar()
        supuestos()
        for clave, ref in y["referencias"].items():
            if isinstance(ref, str):
                resolver(ref)
        equipo()
        eco = y["economia"]
        ids_opex = {o["id"] for o in eco["opex"]}
        ids_ben = {b["id"] for b in eco["beneficios"]}
        if ids_opex != set(_opex_impl(0)):
            errores.append(f"economia.opex {sorted(ids_opex)} ≠ implementados en ce01_datos.py {sorted(_opex_impl(0))}")
        if ids_ben != set(_beneficios_impl()):
            errores.append(f"economia.beneficios {sorted(ids_ben)} ≠ implementados {sorted(_beneficios_impl())}")
        for c in eco["capex"]:
            s(c["de"])
        pesos = sum(c["peso"] for c in y["criterios"]["lista"])
        if abs(pesos - 1) > 1e-9:
            errores.append(f"Los pesos de los criterios suman {pesos}, no 1")
        n = len(y["criterios"]["lista"])
        for a in y["alternativas"]["lista"]:
            if len(a["puntajes"]) != n or not all(1 <= p <= 5 for p in a["puntajes"]):
                errores.append(f"{a['id']}: se esperan {n} puntajes entre 1 y 5")
        for grupo in ("riesgos_estrategicos", "riesgos_proyecto"):
            for r in y[grupo]["lista"]:
                if not (1 <= r["p"] <= 5 and 1 <= r["i"] <= 5):
                    errores.append(f"{r['id']}: P e I deben estar entre 1 y 5")
        roles = y["raci"]["roles"]
        for f in y["raci"]["filas"]:
            if len(f["asignacion"]) != len(roles):
                errores.append(f"RACI «{f['paquete']}»: {len(f['asignacion'])} asignaciones para {len(roles)} roles")
            n_a = sum("A" in a for a in f["asignacion"])
            if n_a != 1:
                msg = f"RACI «{f['paquete']}»: {n_a} aprobadores (A); debe haber exactamente uno"
                (avisos if n_a == 0 and f.get("nota") else errores).append(msg + (f" — {f['nota']}" if f.get("nota") else ""))
        ids_edt = [p["id"] for p in y["edt"]["paquetes"]]
        for pid in ids_edt:
            padre = pid.rpartition(".")[0] or ("0" if pid != "0" else None)
            if padre and padre not in ids_edt:
                errores.append(f"EDT {pid}: falta su paquete padre {padre}")
        paleta = y["estilo"]["paleta"]
        for nombre in y["estilo"]["series"] + list(y["estilo"]["texto_sobre"]):
            if nombre not in paleta:
                errores.append(f"estilo: «{nombre}» no está en la paleta")
    except DatosCE01Error as e:
        errores.append(str(e))
    return errores


def main() -> int:
    avisos: list[str] = []
    errores = validar(avisos)
    for a in avisos:
        print("AVISO:", a)
    if errores:
        for e in errores:
            print("FALLA:", e)
        return 1
    c, b = costos(), beneficios()
    print("CAPEX (I0):")
    for x in c["capex"]:
        print(f"  {x['id']} {x['concepto']:<45} {usd(x['usd']):>12}  [{x['de'].split('.')[0]}]")
    print(f"  {'Total':<50} {usd(c['capex_total']):>12}")
    print("OPEX anual:")
    for x in c["opex"]:
        print(f"  {x['id']} {x['concepto']:<45} {usd(x['usd'], 2):>12}  ({x['tipo']})")
    print(f"  {'Total':<50} {usd(c['opex_total'], 2):>12}")
    print("Beneficios anuales:")
    for x in b["lista"]:
        print(f"  {x['id']} {x['concepto']:<45} {usd(x['usd']):>12}")
    print(f"  Mbps diferidos [S-40] = {num(b['mbps_diferidos'])}")
    print(f"Flujo neto anual: {usd(flujo_neto_anual(), 2)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
