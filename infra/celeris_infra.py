"""Librería de la fuente única de datos de red de Celeris (CE0311, Entregable 1).

Carga infra/inventory.yaml, infra/pruebas.yaml e infra/trazabilidad.yaml, resuelve referencias,
deriva la matriz zona × zona a partir de los flujos y calcula coberturas. La usan infra/validate.py
y, más adelante, los generadores de diagramas, XLSX y DOCX (P2–P5): ninguno debe releer los YAML por su cuenta.

Uso mínimo:
    from celeris_infra import Infra
    infra = Infra.cargar()
    infra.derivar_matriz()
"""
from __future__ import annotations

import ipaddress
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

RAIZ = Path(__file__).resolve().parent.parent
INFRA_DIR = RAIZ / "infra"
CAMBIOS_MD = RAIZ / "docs" / "infra" / "e1" / "CAMBIOS-INVENTARIO.md"
RUBRICA_XLSX = RAIZ / "docs" / "fuentes" / "CE03" / "Rubrica_S1_E1_Diseno_de_Red.xlsx"

ARCHIVOS = {"inventory": "inventory", "pruebas": "pruebas", "trazabilidad": "trazabilidad"}

# Rangos de documentación (RFC 5737): las únicas IP públicas admitidas en el repositorio.
RFC5737 = [ipaddress.ip_network(n) for n in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")]

# Componentes de D1.12 v0.4 vigentes (el contrato). VTI1/VTI2 se desglosan como pide el inventario; ESX01 solo tiene vmk0.
COMPONENTES_D112 = [
    "FGT-EXT", "FW01", "SW-CORE01", "SW-ACC", "BRK01", "ESX01", "IPMI01", "UPS01", "JMP01", "CTRL01", "EDGE01", "EDGE02",
    "PORTAL01", "HNY01", "SIEM01", "ENC01", "LABCLI01", "KALI01", "HNY02", "PCS-LAB", "WIFI-EST", "VTI1", "VTI2", "VGW",
    "EC2-GW", "S3", "AWS-VPC", "AWS-PUB-A", "AWS-APP-A",
]
# Temporales (simulacro de recuperación): existen en el inventario pero no cuentan como faltantes en figuras permanentes.
COMPONENTES_TEMPORALES = ["EC2-DR", "NAT-DR"]
# Retirados en la v0.4 (CI-35, CI-36, CI-39): su ID no se reutiliza y no puede aparecer en nada vigente (V-44).
COMPONENTES_RETIRADOS = ["DB01", "OBS01", "SVC01", "WAF01", "WEB01", "IDS01", "PROBE01", "NAS01", "EC2-SHIELD", "EC2-CTRLR", "NAT01",
                         "AWS-PUB-B", "AWS-APP-B", "AWS-DATA-A", "AWS-DATA-B"]
FLUJOS_ESPERADOS = [f"F{n}" for n in range(1, 27)]            # D1.11 original; F27+ son ampliaciones registradas (CI-29, CI-35…CI-38, CI-40)
PRUEBAS_ESPERADAS = [f"T{n:02d}" for n in range(1, 29)]       # D1.16; T29+ son ampliaciones registradas (CI-27, CI-41)
# «Interna» en la regla de celdas críticas de la matriz de pruebas: toda zona del campus salvo las DMZ y Perímetro.
# Criterios de la rúbrica que se evalúan con el informe y no con pruebas (R1 contexto y alcance; R7 calidad documental).
RUBRICA_SIN_PRUEBAS = ("R1", "R7")
ZONAS_INTERNAS = ["MGMT", "SERVERS", "LAB", "SECURITY", "EDGE"]


def red(cidr: str):
    return ipaddress.ip_network(cidr, strict=True)


def es_publica(ip: str) -> bool:
    a = ipaddress.ip_address(ip)
    return not (a.is_private or a.is_link_local or a.is_loopback or a.is_multicast or a.is_reserved)


def en_rfc5737(ip: str) -> bool:
    a = ipaddress.ip_address(ip)
    return any(a in n for n in RFC5737)


@dataclass(frozen=True)
class Extremo:
    """Extremo de un flujo ya resuelto."""
    crudo: str
    tipo: str               # 'zona' | 'componente'
    zona: str | None        # zona efectiva (None = ambiguo o inexistente)
    componente: str | None
    interfaz: str | None
    es_firewall: bool = False
    error: str | None = None


class _CargadorUnico(yaml.SafeLoader):
    """SafeLoader que rechaza claves duplicadas (PyYAML se queda en silencio con la última)."""


def _sin_duplicados(cargador, nodo, profundo=False):
    vistas = set()
    for clave_nodo, _ in nodo.value:
        clave = cargador.construct_object(clave_nodo, deep=profundo)
        if clave in vistas:
            raise yaml.constructor.ConstructorError(
                None, None, f"clave duplicada «{clave}»", clave_nodo.start_mark)
        vistas.add(clave)
    return yaml.SafeLoader.construct_mapping(cargador, nodo, profundo)


_CargadorUnico.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _sin_duplicados)


def _cargar_yaml(ruta: Path):
    with ruta.open(encoding="utf-8") as f:
        return yaml.load(f, Loader=_CargadorUnico)  # noqa: S506 - SafeLoader subclass


def ids_en_cambios() -> set[str]:
    """IDs CI-nn registrados en docs/infra/e1/CAMBIOS-INVENTARIO.md (encabezados `### CI-nn`)."""
    if not CAMBIOS_MD.exists():
        return set()
    return set(re.findall(r"^#{2,4}\s+(CI-\d{2})\b", CAMBIOS_MD.read_text(encoding="utf-8"), flags=re.M))


def titulos_de_cambios() -> dict[str, str]:
    """{CI-nn: título} de los encabezados `### CI-nn — título` de CAMBIOS-INVENTARIO.md."""
    if not CAMBIOS_MD.exists():
        return {}
    return {m.group(1): m.group(2).strip() for m in re.finditer(r"^#{2,4}\s+(CI-\d{2})\s+—\s+(.+)$", CAMBIOS_MD.read_text(encoding="utf-8"), flags=re.M)}


def resultados_mas_recientes(raiz: Path = RAIZ) -> tuple[Path | None, dict | None]:
    """(carpeta, contenido) del evidencias/<fecha>-<modo>/resultados.json más reciente; (None, None) si no hay."""
    import json
    # Solo carpetas evidencias/AAAA-MM-DD-<modo>: las temporales de depuración no cuentan como último ensayo
    candidatos = sorted((p for p in raiz.glob("evidencias/*/resultados.json") if re.fullmatch(r"\d{4}-\d{2}-\d{2}-[A-Z]", p.parent.name)),
                        key=lambda p: p.parent.name)
    if not candidatos:
        return None, None
    return candidatos[-1].parent, json.loads(candidatos[-1].read_text(encoding="utf-8"))


class Infra:
    def __init__(self, inv: dict, pru: dict, traz: dict, raiz: Path = RAIZ):
        self.raiz = raiz
        self.inv, self.pru, self.traz = inv, pru, traz
        # Lo retirado (v0.4) conserva su ID en el YAML pero no es vigente: `zonas`, `componentes`, `flujos` y `pruebas` solo traen
        # lo vigente, de modo que cualquier referencia a un ID retirado falla V-03/V-44. Los retirados quedan en `*_retirados`.
        vig = lambda e: e.get("estado") != "retirado"  # noqa: E731
        self.zonas = {z["id"]: z for z in inv["zonas"] if vig(z)}
        self.zonas_retiradas = {z["id"]: z for z in inv["zonas"] if not vig(z)}
        self.componentes = {c["id"]: c for c in inv["componentes"] if vig(c)}
        self.componentes_retirados = {c["id"]: c for c in inv["componentes"] if not vig(c)}
        self.flujos = {f["id"]: f for f in inv["flujos"] if vig(f)}
        self.flujos_retirados = {f["id"]: f for f in inv["flujos"] if not vig(f)}
        self.pruebas = {t["id"]: t for t in pru["pruebas"] if vig(t)}
        self.pruebas_retiradas = {t["id"]: t for t in pru["pruebas"] if not vig(t)}
        self.objetivos = {o["id"]: o for o in traz["objetivos"]}
        self.amenazas = {a["id"]: a for a in traz["amenazas"]}
        self.detecciones = {d["id"]: d for d in traz["detecciones"]}
        self.figuras = {f["id"]: f for f in traz["figuras"]}
        self.rubrica = traz["rubrica"]
        self.secciones = {s["id"]: s for s in traz["docx_secciones"]}
        self.artefactos = {a["id"]: a for a in traz["artefactos"]}
        self.supuestos = traz["supuestos"]
        self.decisiones = traz["decisiones"]
        self.requisitos = traz["requisitos"]
        self._cache_extremos: dict[str, list[Extremo]] = {}

    # ------------------------------------------------------------------ carga
    @classmethod
    def cargar(cls, raiz: Path = RAIZ) -> "Infra":
        d = raiz / "infra"
        return cls(_cargar_yaml(d / "inventory.yaml"), _cargar_yaml(d / "pruebas.yaml"),
                   _cargar_yaml(d / "trazabilidad.yaml"), raiz)

    @staticmethod
    def errores_de_esquema(raiz: Path = RAIZ) -> list[tuple[str, str, str]]:
        """Devuelve (archivo, ruta JSON, mensaje) por cada incumplimiento del esquema."""
        salida = []
        for nombre in ARCHIVOS:
            esquema = json.loads((raiz / "infra" / "schema" / f"{nombre}.schema.json").read_text(encoding="utf-8"))
            datos = _cargar_yaml(raiz / "infra" / f"{nombre}.yaml")
            for e in sorted(Draft202012Validator(esquema).iter_errors(datos), key=lambda e: [str(p) for p in e.path]):
                ruta = "/".join(str(p) for p in e.path) or "(raíz)"
                salida.append((f"{nombre}.yaml", ruta, e.message[:300]))
        return salida

    # --------------------------------------------------------------- endpoints
    def resolver(self, crudo: str) -> list[Extremo]:
        """Resuelve un endpoint de flujo: ID de zona, ID de componente o `COMPONENTE:interfaz`."""
        if crudo in self._cache_extremos:
            return self._cache_extremos[crudo]
        if crudo in self.zonas:
            res = [Extremo(crudo, "zona", crudo, None, None)]
        else:
            cid, _, iface = crudo.partition(":")
            comp = self.componentes.get(cid)
            if comp is None:
                res = [Extremo(crudo, "componente", None, cid, iface or None, error=f"«{crudo}» no es zona ni componente")]
            elif cid == "FW01":
                res = [Extremo(crudo, "componente", "PERIMETRO", cid, iface or None, es_firewall=True)]
            elif iface:
                ip = next((i for i in comp["ips"] if i["interfaz"] == iface), None)
                if ip is None:
                    res = [Extremo(crudo, "componente", None, cid, iface, error=f"{cid} no tiene la interfaz «{iface}»")]
                else:
                    res = [Extremo(crudo, "componente", ip["zona"], cid, iface)]
            else:
                zonas_ip = {i["zona"] for i in comp["ips"]}
                if len(comp["zonas"]) == 1:
                    res = [Extremo(crudo, "componente", comp["zonas"][0], cid, None)]
                elif len(zonas_ip) == 1:
                    res = [Extremo(crudo, "componente", next(iter(zonas_ip)), cid, None)]
                else:
                    res = [Extremo(crudo, "componente", None, cid, None,
                                   error=f"{cid} está en varias zonas: use «{cid}:interfaz»")]
        self._cache_extremos[crudo] = res
        return res

    def extremos(self, flujo: dict, lado: str) -> list[Extremo]:
        return [e for crudo in flujo[lado] for e in self.resolver(crudo)]

    # ---------------------------------------------------------------- matriz
    @property
    def orden_matriz(self) -> list[str]:
        return self.inv["matriz_esperada"]["orden"]

    def derivar_matriz(self) -> dict[tuple[str, str], dict[str, set[str]]]:
        """Matriz zona × zona derivada de los flujos.

        Se omiten los pares intra-zona (se conmutan en capa 2, nota 2 de D1.8) y los pares con FW01
        en alguno de sus extremos (tráfico local al firewall; la matriz no tiene fila «Perímetro»).
        """
        celdas: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(lambda: {"permitidos": set(), "bloqueados": set()})
        for f in self.flujos.values():
            if f["estado"] != "activo":
                continue
            clave = "permitidos" if f["accion"] == "permitir" else "bloqueados"
            for o in self.extremos(f, "origen"):
                for d in self.extremos(f, "destino"):
                    if o.es_firewall or d.es_firewall or o.zona is None or d.zona is None or o.zona == d.zona:
                        continue
                    celdas[(o.zona, d.zona)][clave].add(f["id"])
        return celdas

    def matriz_esperada(self) -> dict[tuple[str, str], dict]:
        out = {}
        for zo, fila in self.inv["matriz_esperada"]["celdas"].items():
            for zd, celda in fila.items():
                out[(zo, zd)] = celda
        return out

    def diferencias_matriz(self) -> list[dict]:
        """Diferencias entre la matriz derivada y la esperada. Cada una trae si está declarada pendiente."""
        derivada = self.derivar_matriz()
        esperada = self.matriz_esperada()
        difs = []
        for par in sorted(esperada):
            exp = esperada[par]
            der = derivada.get(par, {"permitidos": set(), "bloqueados": set()})
            exp_p, exp_b = set(exp.get("flujos", [])), set(exp.get("bloqueados", []))
            sobran = der["permitidos"] - exp_p          # en flujos, no en la matriz
            faltan = exp_p - der["permitidos"]          # en la matriz, no en flujos
            b_sobran, b_faltan = der["bloqueados"] - exp_b, exp_b - der["bloqueados"]
            estado_der = "permitido" if der["permitidos"] else ("no_aplica" if par[0] == par[1] else "denegado")
            estado_mal = (exp["estado"] == "permitido") != bool(der["permitidos"]) and exp["estado"] != "no_aplica"
            if exp["estado"] == "no_aplica" and der["permitidos"]:
                estado_mal = True
            if not (sobran or faltan or b_sobran or b_faltan or estado_mal):
                continue
            implicados = sobran | faltan | b_sobran | b_faltan
            cambios = set()
            pendiente = bool(exp.get("pendiente"))
            cambios |= set(_como_lista(exp.get("cambio")))
            for fid in implicados:
                if self.flujos[fid].get("pendiente"):
                    pendiente = True
                    cambios |= set(_como_lista(self.flujos[fid].get("cambio")))
            difs.append({"par": par, "esperado": exp, "derivado": der, "estado_derivado": estado_der,
                         "sobran_en_flujos": sorted(sobran, key=_clave_id), "faltan_en_flujos": sorted(faltan, key=_clave_id),
                         "bloq_sobran": sorted(b_sobran), "bloq_faltan": sorted(b_faltan),
                         "pendiente": pendiente, "cambios": sorted(cambios)})
        return difs

    # --------------------------------------------------------------- flujos
    def flujos_de(self, cid: str, incluir_zona: bool = True) -> set[str]:
        """Flujos activos en los que interviene el componente. Con `incluir_zona`, cuenta los extremos
        expresados como zona completa (p. ej. «LAB» incluye a PROBE01)."""
        comp = self.componentes[cid]
        res = set()
        for f in self.flujos.values():
            if f["estado"] != "activo":
                continue
            for lado in ("origen", "destino"):
                for e in self.extremos(f, lado):
                    if e.componente == cid or (incluir_zona and e.tipo == "zona" and e.zona in comp["zonas"]):
                        res.add(f["id"])
        return res

    def figuras_requeridas(self, cid: str) -> set[str]:
        """FIG-5.1 siempre (D1.7: todo ID de D1.12 aparece) más la figura de cada flujo donde es extremo directo."""
        if self.componentes[cid].get("estado") == "temporal":
            return set()                 # recursos del simulacro: no cuentan como faltantes en figuras permanentes
        req = {"FIG-5.1"}
        for fid in self.flujos_de(cid, incluir_zona=False):
            if self.flujos[fid].get("figura"):
                req.add(self.flujos[fid]["figura"])
        return req

    def flujos_de_figura(self, fig: str) -> list[str]:
        return [f["id"] for f in self.flujos.values() if f.get("figura") == fig]

    # --------------------------------------------------------------- pruebas
    def pruebas_de_flujo(self, fid: str) -> list[str]:
        return [t["id"] for t in self.pruebas.values() if fid in t["flujos"]]

    def pruebas_de_celda(self, par: str) -> list[str]:
        return [t["id"] for t in self.pruebas.values() if par in t.get("celdas_matriz", [])]

    def pruebas_de_objetivo(self, od: str) -> list[str]:
        return [t["id"] for t in self.pruebas.values() if od in t["objetivos"]]

    # ------------------------------------------------- cobertura de la matriz de pruebas
    def celdas_denegadas_criticas(self) -> dict[str, str]:
        """Celdas «denegado» de la matriz cuya falla expone un límite del diseño, con el grupo al que pertenecen:
        Internet → interna (y AWS), LAB → MGMT, DMZ → interna, DMZ-HONEY → cualquiera y WIFI-EST → interna (v0.4: sin STORAGE)."""
        out = {}
        for (o, d), c in self.matriz_esperada().items():
            if c["estado"] != "denegado":
                continue
            celda = f"{o}>{d}"
            if d == "WIFI-EST":
                continue          # D1.8 v0.4 no tiene columna WIFI-EST (CI-45): se acepta denegado, sin prueba dedicada
            if o == "WIFI-EST" and d in ZONAS_INTERNAS:
                out[celda] = "WIFI-EST → interna"
            elif o == "DMZ-HONEY":
                out[celda] = "DMZ-HONEY → cualquiera"
            elif o == "INTERNET" and d in ZONAS_INTERNAS + ["AWS"]:
                out[celda] = "Internet → interna"
            elif (o, d) == ("LAB", "MGMT"):
                out[celda] = "LAB → MGMT"
            elif o == "DMZ-SVC" and d in ZONAS_INTERNAS + ["AWS"]:
                out[celda] = "DMZ → interna"
        return out

    def celdas_permitidas(self) -> dict[str, list[str]]:
        """Celdas «permitido» de la matriz con los flujos que las abren (puede ser vacío: celda sin F-nn)."""
        return {f"{o}>{d}": list(c.get("flujos", [])) for (o, d), c in self.matriz_esperada().items() if c["estado"] == "permitido"}

    def pruebas_por_polaridad(self, *polaridades: str) -> list[dict]:
        return [t for t in self.pruebas.values() if t.get("polaridad") in polaridades]

    def pruebas_positivas_de_celda(self, celda: str, flujos: list[str]) -> list[str]:
        """Pruebas positivas o mixtas que verifican una celda permitida: la citan o prueban alguno de sus flujos."""
        return [t["id"] for t in self.pruebas_por_polaridad("positiva", "mixta")
                if celda in t.get("celdas_matriz", []) or set(flujos) & set(t["flujos"])]

    def pruebas_negativas_de_celda(self, celda: str) -> list[str]:
        return [t["id"] for t in self.pruebas_por_polaridad("negativa", "mixta") if celda in t.get("celdas_matriz", [])]

    def cobertura_de_pruebas(self) -> dict[str, dict]:
        """Cobertura por dimensión: {nombre: {cubiertos, total, faltan: [...]}}. Es la que muestra la hoja «Cobertura»
        del XLSX y la que exige V-70+."""
        act = [f for f in self.flujos.values() if f["estado"] == "activo"]
        permitidos = [f["id"] for f in act if f["accion"] == "permitir"]
        bloqueados = [f["id"] for f in act if f["accion"] == "bloquear"]

        def dim(elementos, tiene):
            faltan = [e for e in elementos if not tiene(e)]
            return {"cubiertos": len(elementos) - len(faltan), "total": len(elementos), "faltan": faltan}

        positivas = {f: [t["id"] for t in self.pruebas_por_polaridad("positiva", "mixta") if f in t["flujos"]] for f in permitidos}
        negativas_flujo = {f: [t["id"] for t in self.pruebas_por_polaridad("negativa", "mixta") if f in t["flujos"]] for f in bloqueados}
        permit = self.celdas_permitidas()
        criticas = self.celdas_denegadas_criticas()
        denegadas = [f"{o}>{d}" for (o, d), c in self.matriz_esperada().items() if c["estado"] == "denegado"]
        elementos = {eid: e for rid in ("R3", "R4") for e in self.rubrica[rid].get("elementos_evaluados", []) for eid in [e["id"]]}
        return {
            "Flujos permitidos con prueba positiva": dim(permitidos, lambda f: positivas[f]),
            "Flujos bloqueados con prueba negativa": dim(bloqueados, lambda f: negativas_flujo[f]),
            "Celdas permitidas con prueba positiva": dim(list(permit), lambda c: self.pruebas_positivas_de_celda(c, permit[c])),
            "Celdas denegadas críticas con prueba negativa": dim(list(criticas), lambda c: self.pruebas_negativas_de_celda(c)),
            "Celdas denegadas (todas) con prueba negativa": dim(denegadas, lambda c: self.pruebas_negativas_de_celda(c)),
            "Objetivos OD con ≥ 1 prueba": dim(list(self.objetivos), lambda o: self.pruebas_de_objetivo(o)),
            "Amenazas AM con ≥ 1 prueba": dim(list(self.amenazas), lambda a: [t for t in self.pruebas.values() if a in t["amenazas"]]),
            "Detecciones DET con ≥ 1 prueba": dim(list(self.detecciones), lambda d: [t for t in self.pruebas.values() if d in t["detecciones"]]),
            "Criterios de rúbrica con ≥ 1 prueba": dim([r for r in self.rubrica if r not in RUBRICA_SIN_PRUEBAS], lambda r: [t for t in self.pruebas.values() if r in t["criterios_rubrica"]]),
            "Elementos evaluados de R3 y R4 con ≥ 1 prueba": dim(list(elementos), lambda e: [p for p in elementos[e]["pruebas"] if p in self.pruebas]),
        }

    # ------------------------------------------------------------ coberturas
    def coberturas(self) -> dict[str, tuple[int, int]]:
        """(cubiertos, total) de las relaciones de trazabilidad."""
        act = [f for f in self.flujos.values() if f["estado"] == "activo"]
        cel_den = [(a, b) for (a, b), c in self.matriz_esperada().items() if c["estado"] == "denegado"]
        return {
            "flujos con prueba": (sum(bool(self.pruebas_de_flujo(f["id"])) for f in act), len(act)),
            "flujos con prueba o justificación": (sum(bool(self.pruebas_de_flujo(f["id"]) or f.get("sin_prueba_justificacion")) for f in act), len(act)),
            "componentes con ≥ 1 flujo": (sum(bool(self.flujos_de(c)) for c in self.componentes), len(self.componentes)),
            "objetivos con ≥ 1 prueba": (sum(bool(self.pruebas_de_objetivo(o)) for o in self.objetivos), len(self.objetivos)),
            "amenazas con ≥ 1 prueba": (sum(bool(a["pruebas"]) for a in self.amenazas.values()), len(self.amenazas)),
            "detecciones con ≥ 1 prueba": (sum(bool(d["validacion"]["pruebas"]) for d in self.detecciones.values()), len(self.detecciones)),
            "celdas denegadas con ≥ 1 prueba": (sum(bool(self.pruebas_de_celda(f"{a}>{b}")) for a, b in cel_den), len(cel_den)),
            "criterios de rúbrica con evidencia": (sum(bool(r["evidencias"]) for r in self.rubrica.values()), len(self.rubrica)),
        }

    # ------------------------------------------------------------ utilidades
    def todas_las_ips(self) -> list[tuple[str, str, str, str]]:
        """(componente, interfaz, ip, zona) de cada IP asignada."""
        return [(c["id"], i["interfaz"], i["ip"], i["zona"]) for c in self.componentes.values() for i in c["ips"] if i["ip"]]

    def referencias_cambio(self) -> list[tuple[str, str]]:
        """(origen, CI-nn) de cada `cambio` declarado en los tres archivos."""
        refs = []

        def visitar(nodo, ruta):
            if isinstance(nodo, dict):
                if "cambio" in nodo and nodo.get("pendiente"):
                    for ci in _como_lista(nodo["cambio"]):
                        refs.append((ruta or "(raíz)", ci))
                for k, v in nodo.items():
                    visitar(v, f"{ruta}/{k}" if ruta else str(k))
            elif isinstance(nodo, list):
                for i, v in enumerate(nodo):
                    ident = v.get("id") if isinstance(v, dict) and "id" in v else i
                    visitar(v, f"{ruta}[{ident}]")

        for nombre, datos in (("inventory", self.inv), ("pruebas", self.pru), ("trazabilidad", self.traz)):
            visitar(datos, nombre)
        return refs


def _como_lista(v) -> list[str]:
    if v is None:
        return []
    return [v] if isinstance(v, str) else list(v)


def _clave_id(i: str):
    m = re.match(r"([A-Z]+)(\d+)", i)
    return (m.group(1), int(m.group(2))) if m else (i, 0)
