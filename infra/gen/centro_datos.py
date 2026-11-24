"""Fuente única del centro de datos híbrido (CE0331, Entregable 2): carga infra/centro_datos.yaml, lo cruza con el inventario
(infra/inventory.yaml, vía celeris_infra.Infra) y calcula dimensionamiento, costo, continuidad y la lista de elementos de la matriz.

Lo usan los generadores de diagramas (drawio_dc.py), de la matriz (xlsx_centro_datos.py), del informe (docs/infra/e2/build_informe.py)
y los chequeos V-90+ (infra/checks/v90_*.py). Ninguno debe releer el YAML por su cuenta ni repetir un cálculo.

    from centro_datos import CentroDatos
    cd = CentroDatos.cargar()
"""
from __future__ import annotations

import json
import re
from decimal import ROUND_HALF_UP, Decimal
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from celeris_infra import RAIZ, Infra  # noqa: E402

RUTA = RAIZ / "infra" / "centro_datos.yaml"
ESQUEMA = RAIZ / "infra" / "schema" / "centro_datos.schema.json"
ORDEN_CRIT = {"Alta": 3, "Media": 2, "Baja": 1}


def coma(v: float, d: int = 1) -> str:
    """Número con coma decimal y espacio fino como separador de miles (formato del informe)."""
    q = Decimal(1).scaleb(-d)
    s = f"{Decimal(repr(round(v, 9))).quantize(q, rounding=ROUND_HALF_UP):,.{d}f}".replace(",", " ").replace(".", ",")
    return s


def max_crit(crits) -> str:
    cs = [c for c in crits if c]
    return max(cs, key=lambda c: ORDEN_CRIT[c]) if cs else "Baja"


def plano(valor: str) -> str:
    """Nombre de port group sin «PG-» y sin espacios: el inventario escribe «TRANSITO + FW-TRUNK» y el diseño «PG-TRANSITO»."""
    return re.sub(r"^PG-", "", valor.strip())


class CentroDatos:
    def __init__(self, raw: dict, x: Infra):
        self.raw, self.x = raw, x
        self.meta = raw["meta"]
        self.host = raw["host"]
        self.vms = raw["maquinas_virtuales"]
        self.vm_por_id = {v["componente"]: v for v in self.vms}
        self.datastores = {d["id"]: d for d in raw["almacenamiento"]["datastores"]}
        self.vswitches = {s["id"]: s for s in raw["hipervisor_red"]["vswitches"]}
        self.port_groups = {pg["id"]: {**pg, "vswitch": s["id"]} for s in raw["hipervisor_red"]["vswitches"] for pg in s["port_groups"]}
        self.nics = {n["id"]: n for n in raw["host"]["nic"]}
        self.aws = raw["aws"]
        self.continuidad = raw["continuidad"]
        self.servicios = {s["id"]: s for s in raw["continuidad"]["servicios"]}

    # ------------------------------------------------------------------ carga
    @classmethod
    def cargar(cls, x: Infra | None = None) -> "CentroDatos":
        x = x or Infra.cargar()
        raw = yaml.safe_load(RUTA.read_text(encoding="utf-8"))
        return cls(raw, x)

    @staticmethod
    def errores_esquema() -> list[str]:
        raw = yaml.safe_load(RUTA.read_text(encoding="utf-8"))
        esquema = json.loads(ESQUEMA.read_text(encoding="utf-8"))
        return [f"{'/'.join(str(p) for p in e.absolute_path) or '(raíz)'}: {e.message}" for e in
                sorted(Draft202012Validator(esquema).iter_errors(raw), key=lambda e: list(e.absolute_path))]

    # ------------------------------------------------------------------ máquinas virtuales
    def vms_hasta(self, fase: str) -> list[dict]:
        fases = ["F1", "F2"]
        return [v for v in self.vms if fases.index(v["fase"]) <= fases.index(fase)]

    def totales(self, fase: str) -> dict:
        vs = self.vms_hasta(fase)
        return {"vcpu": sum(v["vcpu"] for v in vs), "ram_gb": sum(v["ram_gb"] for v in vs),
                "disco_gb": sum(v["disco_gb"] + v["cache_gb"] for v in vs), "disco_sin_cache_gb": sum(v["disco_gb"] for v in vs),
                "cache_gb": sum(v["cache_gb"] for v in vs), "vms": len(vs)}

    def vm_texto_disco(self, v: dict) -> str:
        return f"{v['disco_gb']} + {v['cache_gb']} caché" if v["cache_gb"] else str(v["disco_gb"])

    def inv_vm(self, cid: str) -> dict | None:
        return (self.x.componentes.get(cid) or {}).get("vm")

    # ------------------------------------------------------------------ dimensionamiento (D2.8)
    def dimensionar(self) -> dict:
        d = self.raw["dimensionamiento"]
        fase, h = d["fase"], self.host
        vs = self.vms_hasta(fase)
        t = self.totales(fase)
        sens = sum(v["vcpu"] for v in vs if v["sensible"])
        resto = t["vcpu"] - sens
        n_sens = sens / d["razones_overcommit"]["sensible"]
        n_resto = resto / d["razones_overcommit"]["resto"]
        nucleos = n_sens + n_resto
        ram_sobrecarga = t["ram_gb"] * d["sobrecarga_esxi"]
        ram_crec = ram_sobrecarga * d["crecimiento"]
        disco_req = t["disco_sin_cache_gb"] * d["factor_disco"]
        disco_tot = disco_req + d["copia_local_restic_gb"]
        cap_vm = self.datastores["DS-VM"]["capacidad_gb"]
        cache = {k: {"usado": sum(v["cache_gb"] for v in vs if v.get("datastore_cache") == k), "cap": ds["capacidad_gb"]}
                 for k, ds in self.datastores.items() if ds.get("vm")}
        return {
            "fase": fase, **t, "vcpu_sensibles": sens, "vcpu_resto": resto, "nucleos_sensibles": n_sens, "nucleos_resto": n_resto,
            "nucleos_necesarios": nucleos, "nucleos_host": h["cpu"]["nucleos"], "holgura_cpu": (h["cpu"]["nucleos"] - nucleos) / h["cpu"]["nucleos"],
            "ram_con_sobrecarga": ram_sobrecarga, "ram_con_crecimiento": ram_crec, "ram_host": h["ram_gb"],
            "holgura_ram": (h["ram_gb"] - ram_sobrecarga) / h["ram_gb"],
            "margen_ram_tras_crecimiento": (h["ram_gb"] - ram_crec) / h["ram_gb"],
            "ram_libre_tras_crecimiento": h["ram_gb"] - ram_crec,
            "disco_requerido": disco_req, "disco_con_copia": disco_tot, "disco_capacidad": cap_vm,
            "uso_disco": disco_tot / cap_vm, "holgura_disco": (cap_vm - disco_tot) / cap_vm,
            "cache": {k: {**v, "holgura": (v["cap"] - v["usado"]) / v["cap"]} for k, v in cache.items()},
            "vcpu_max_vm": max(v["vcpu"] for v in self.vms),
            "relacion_vcpu_nucleos": t["vcpu"] / h["cpu"]["nucleos"],
        }

    # ------------------------------------------------------------------ EC2-GW frente a su carga
    def ec2_gw(self) -> dict:
        i = next(i for i in self.aws["instancias"] if i["componente"] == "EC2-GW")
        c = i["carga_diseno"]
        base = i["vcpu"] * i["linea_base_por_vcpu"]
        return {**i, "linea_base_vcpu": base, "margen_cpu": (base - c["cpu_medio_vcpu"]) / base,
                "margen_ram": (i["ram_gib"] * 1024 - c["ram_mib"]) / (i["ram_gib"] * 1024),
                "creditos_consumidos_por_hora": c["cpu_medio_vcpu"] * 60, "creditos_ganados_por_hora": i["creditos_por_hora"]}

    # ------------------------------------------------------------------ costo (D2.5)
    def costo(self) -> dict:
        c = self.aws["costo_mensual"]
        lineas = [{**l, "total": round(l["cantidad"] * l["precio_unitario"], 4)} for l in c["lineas"]]
        total = sum(l["total"] for l in lineas)
        le = c["laboratorio_efimero"]
        hora = sum(l["cantidad"] * l["precio_hora"] for l in le["lineas"])
        sim = c["simulacro"]
        sim_h = sum(l["cantidad"] * l["precio_hora"] for l in sim["lineas"])
        alts = []
        for a in self.aws["nat"]["alternativas"]:
            alts.append({**a, "mensual": a["precio_hora"] * a["horas_mes"]})
        return {"lineas": lineas, "total": total, "meta": c["meta_usd"], "referencial": c["referencial_documento_usd"],
                "lab_hora": hora, "lab_meta": le["meta_usd_hora"], "simulacro_hora": sim_h, "simulacro_horas": sim["horas"],
                "simulacro_total": sim_h * sim["horas"], "nat_alternativas": alts}

    # ------------------------------------------------------------------ continuidad (D2.9)
    def criticidad_servicio(self, s: dict) -> str:
        if s.get("criticidad_propia"):
            return s["criticidad_propia"]
        return max_crit(self.x.componentes[c]["criticidad"] for c in s["componentes"])

    # ------------------------------------------------------------------ elementos (matriz y diagramas)
    def criticidad_de(self, cid: str) -> str:
        if cid in self.x.componentes:
            return self.x.componentes[cid]["criticidad"]
        e = self._extras().get(cid)
        return e["criticidad"] if e else "Baja"

    def _vms_en_pg(self, pg: str) -> list[str]:
        return [v["componente"] for v in self.vms if pg in v["port_groups"]]

    def _extras(self) -> dict[str, dict]:
        """Elementos que el inventario no registra como componente, con criticidad heredada de lo que sirven."""
        if hasattr(self, "_cache_extras"):
            return self._cache_extras
        ex: dict[str, dict] = {}
        crit = self.criticidad_de
        raw = self.raw
        for e in raw["rack"]["elementos"]:
            ex[e["id"]] = {"entorno": "On-premise", "criticidad": max_crit(crit(s) for s in e["sirve_a"]), **e}
        for d in self.datastores.values():
            ex[d["id"]] = {"id": d["id"], "nombre": f"{d['id']} — {d['nombre']}", "entorno": "On-premise", "tipo": "Almacenamiento",
                           "funcion": d["contiene"], "recursos": f"{d['medio']} · {coma(d['capacidad_gb'] / 1000, 2)} TB", "criticidad": d["criticidad"],
                           "por_que": d["por_que"], "si_falla": d["si_falla"], "estado": "diseño" if d["fase"] == "F1" else "diseño (F2)"}
        # vSwitch y port groups: criticidad = la mayor de las VM que cuelgan de ellos
        for s in self.vswitches.values():
            vms = sorted({v for pg in s["port_groups"] for v in self._vms_en_pg(pg["id"])})
            nics = ", ".join(s["uplinks"])
            t = s["teaming"]
            ex[s["id"]] = {"id": s["id"], "nombre": f"{s['id']} — vSwitch estándar", "entorno": "On-premise", "tipo": "Red virtual (vSwitch)",
                           "funcion": s["uso"], "recursos": f"Uplinks {nics}" + (f" · teaming: {t['politica']}" if t else " · sin teaming (una NIC)"),
                           "criticidad": max_crit(crit(v) for v in vms), "estado": "diseño",
                           "por_que": ("Dos NIC de 10 GbE con teaming por puerto virtual de origen: reparte las VM entre los enlaces y sigue funcionando si uno cae; "
                                       "el vSwitch estándar no soporta LACP." if t else
                                       "Aísla la red de tránsito hacia el FortiGate en una NIC física dedicada: solo FW01 se conecta."),
                           "si_falla": ("Si cae un enlace, las VM se reubican en el otro (teaming); si cae SW-CORE01 se pierden ambos y con ellos todas las zonas."
                                        if t else "Si cae vmnic2 o el enlace al FortiGate, FW01 pierde la salida a Internet y la VPN (VTI1 y VTI2); el campus sigue sin Internet.")}
            for pg in s["port_groups"]:
                vm_pg = self._vms_en_pg(pg["id"])
                vlan = "sin etiqueta" if pg["vlan"] is None else f"VLAN {pg['vlan']}"
                zona = pg.get("zona")
                ex[pg["id"]] = {"id": pg["id"], "nombre": f"{pg['id']} — Port group", "entorno": "On-premise", "tipo": "Red virtual (port group)",
                                "funcion": f"{vlan}" + (f" · zona {zona}" if zona else "") + (f" · {pg['nota']}" if pg.get("nota") else ""),
                                "recursos": f"{s['id']} · {vlan} · VM: {', '.join(vm_pg)}",
                                "criticidad": max_crit(crit(v) for v in vm_pg), "estado": "diseño",
                                "por_que": (f"Una VLAN por port group mantiene la zona {zona} aislada de las demás dentro del mismo vSwitch." if zona else
                                            "Entrega a FW01 todas las VLAN para que enrute entre zonas (D-17)."),
                                "si_falla": f"Las VM conectadas ({', '.join(vm_pg)}) pierden red; el resto de port groups no se afecta."}
        for n in self.nics.values():
            sw = n["vswitch"]
            ex[n["id"]] = {"id": n["id"], "nombre": f"{n['id']} — NIC física de ESX01", "entorno": "On-premise", "tipo": "Red (NIC física)",
                           "funcion": n["uso"],
                           "recursos": (f"{n['velocidad_gbps']} GbE" if n["velocidad_gbps"] else "Libre, velocidad sin definir (CI-80)") + (f" · {sw}" if sw else ""),
                           "criticidad": ex[sw]["criticidad"] if sw else "Baja", "estado": "diseño",
                           "por_que": ("Enlace de 10 GbE: un laboratorio de 40 PCs necesita ≈ 1 Gbps desde la caché (REQ-NF-02)." if (n["velocidad_gbps"] or 0) >= 10 else
                                       "NIC dedicada a la red de tránsito, separada del trunk de las zonas." if n["vswitch"] else "Reserva para un enlace adicional sin rediseñar el host."),
                           "si_falla": ("El teaming mueve las VM a la otra NIC de vSwitch0 sin cortar el servicio." if sw == "vSwitch0" else
                                        "FW01 pierde la salida a Internet y la VPN." if sw == "vSwitch1" else "Sin efecto: no transporta tráfico.")}
        # AWS: elementos propios y los del inventario con ID (tablas, SG, NACL)
        aws = self.x.inv["aws"]
        for e in self.aws["elementos"]:
            ex[e["id"]] = {"entorno": "AWS", "criticidad": max_crit(crit(s) for s in e["sirve_a"]), "estado": "diseño", **e}
        for t in aws["tablas_de_rutas"]:
            rutas = "; ".join(f"{self._destino(r['destino'])} → {self._salto(r)}" for r in t["rutas"])
            ex[t["id"]] = {"id": t["id"], "nombre": f"{t['id']} — Tabla de rutas", "entorno": "AWS", "tipo": "Red (tabla de rutas)",
                           "funcion": rutas, "recursos": f"Subred: {', '.join(t['subredes'])}", "criticidad": max_crit(crit(s) for s in t["subredes"]),
                           "estado": "diseño", "por_que": "Decide a dónde va el tráfico de la subred: Internet por el IGW, el campus por el VGW (BGP) y S3 por el endpoint."
                           if t["id"] == "rt-public" else "La subred privada no tiene ruta a Internet: solo al campus (VGW) y a S3 (endpoint); la ruta por NAT-DR existe solo en el simulacro.",
                           "si_falla": "Sin la ruta correcta la subred pierde su destino; se recrea con OpenTofu (RTO 15 min)."}
        for sg in aws["security_groups"]:
            reglas = len(sg["ingress"]) + len(sg["egress"])
            ex[sg["id"]] = {"id": sg["id"], "nombre": f"{sg['id']} — Security Group", "entorno": "AWS", "tipo": "Seguridad (Security Group)",
                            "funcion": f"Firewall con estado de {sg['componente']}", "recursos": f"{len(sg['ingress'])} regla(s) de entrada · {len(sg['egress'])} de salida",
                            "criticidad": crit(sg["componente"]), "estado": "temporal" if sg.get("temporal") else "diseño",
                            "por_que": "Limita a TCP 443 la entrada pública y la salida a CTRL01:443, SIEM01:1514/1515 y 443 a Internet."
                            if sg["id"] == "sg-gw" else "Sin entrada desde Internet; solo sale a S3 por el endpoint y a NAT-DR durante el simulacro.",
                            "si_falla": "Si se abre de más, EC2-GW queda más expuesta; la NACL de la subred y la ausencia de datos en la instancia limitan el daño."
                            if sg["id"] == "sg-gw" else "Sin efecto en operación normal (existe solo en el simulacro)."}
        for n in aws["nacl"]:
            ex[n["id"]] = {"id": n["id"], "nombre": f"{n['id']} — NACL", "entorno": "AWS", "tipo": "Seguridad (NACL)",
                           "funcion": f"Filtro sin estado de la subred {', '.join(n['subredes'])}", "recursos": f"{len(n['ingress'])} regla(s) de entrada",
                           "criticidad": max_crit(crit(s) for s in n["subredes"]), "estado": "diseño",
                           "por_que": "Niega TCP 22 y 3389 desde Internet y permite 443 y el retorno efímero." if n["id"] == "nacl-public" else
                           "Permite solo TCP 443 desde pub-a y el retorno efímero; sin SSH.",
                           "si_falla": "Queda solo el Security Group como filtro; se restaura desde OpenTofu."}
        self._cache_extras = ex
        return ex

    def _destino(self, d: str) -> str:
        if d.startswith("supernet:"):
            return self.x.inv["supernets"][[s["id"] for s in self.x.inv["supernets"]].index(d.split(":", 1)[1])]["cidr"]
        return {"prefijo_s3": "prefijo S3"}.get(d, d)

    def _salto(self, r: dict) -> str:
        s = r["salto"]
        nombre = {"internet_gateway": "IGW01", "vgw": "VGW", "gateway_endpoint_s3": "VPCE-S3"}.get(s, s.replace("nat:", ""))
        return nombre + (" (solo en el simulacro)" if r.get("solo_en_simulacro") else "")

    def extras(self) -> dict[str, dict]:
        return self._extras()

    def recursos_de(self, cid: str) -> str:
        """Texto de «Recursos asignados» de un componente del inventario."""
        c = self.x.componentes[cid]
        h = self.host
        if cid in self.vm_por_id:
            v = self.vm_por_id[cid]
            return f"{v['vcpu']} vCPU · {v['ram_gb']} GB RAM · {self.vm_texto_disco(v)} GB disco · {v['so']}"
        if cid == "ESX01":
            return f"{h['cpu']['nucleos']} núcleos · {h['ram_gb']} GB RAM · {len(self.nics)} NIC · formato {h['chasis']['formato_u']}U"
        if cid == "SW-CORE01":
            return "24× 1 GbE + 2–4× SFP+ 10 GbE · U11"
        if cid == "UPS01":
            e = self.raw["energia"]
            return f"{coma(e['capacidad_kva'])} kVA {e['topologia']} · carga ≈ {e['consumo_w']} W · autonomía {e['autonomia_min'][0]}–{e['autonomia_min'][1]} min"
        if cid == "IPMI01":
            return "iDRAC/iLO · puerto dedicado en MGMT"
        if cid == "BRK01":
            return "1 puerto de SW-CORE01 en VLAN 10, apagado por defecto"
        if cid == "SW-ACC":
            return "Existente (DTI), con 802.1Q [S-14]"
        if cid == "FGT-EXT":
            return "Existente (DTI) · WAN y tránsito 10.20.0.0/29"
        if cid in ("AWS-VPC", "AWS-PUB-A", "AWS-APP-A"):
            return c["cidr"] + (f" · AZ {c['az']}" if c.get("az") else "")
        if cid == "VGW":
            return "2 túneles IPsec (activo/pasivo) · ASN 64512"
        if cid == "S3":
            s3 = self.x.inv["aws"]["s3"]
            return f"≈ 300 GB · versionado · Object Lock {s3['object_lock']['dias']} d ({s3['object_lock']['modo']})"
        inst = next((i for i in self.aws["instancias"] if i["componente"] == cid), None)
        if inst:
            r = f"{inst['tipo']} · {inst['vcpu']} vCPU · {inst['ram_gib']} GiB"
            if inst.get("ebs_gb"):
                r += f" · {inst['ebs_gb']} GB {inst['ebs_tipo']}"
            return r
        return "—"

    def entorno_de(self, cid: str) -> str:
        return "AWS" if "AWS" in self.x.componentes[cid]["zonas"] else "On-premise"

    def tipo_de(self, cid: str) -> str:
        t = self.x.componentes[cid]["tipo"]
        if cid in self.vm_por_id:
            return "Cómputo (VM)"
        return {"hipervisor": "Hipervisor", "switch": "Red (switch)", "switch_existente": "Red (switch existente)", "puerto_emergencia": "Red (acceso de emergencia)",
                "gestion_fuera_banda": "Gestión fuera de banda", "ups": "Energía", "firewall_existente": "Seguridad (firewall existente)",
                "aws_vpc": "Red virtual (VPC)", "aws_subred": "Red virtual (subred)", "vpn_gateway": "Red (extremo VPN)", "aws_instancia": "Cómputo (EC2)",
                "aws_s3": "Almacenamiento (S3)"}.get(t, t)
