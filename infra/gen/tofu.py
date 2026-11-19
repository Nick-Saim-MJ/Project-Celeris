"""Variables de OpenTofu (Modo A, Parte F5) generadas desde infra/inventory.yaml.

Los módulos de deploy/opentofu no llevan ninguna IP, CIDR, puerto ni parámetro criptográfico escrito a mano: todo entra por
`diseno.auto.tfvars.json`, que se genera aquí. Así la VPC, las rutas, los Security Groups, las NACL y la VPN que se crean en AWS
son las del diseño de D1.10 y D2.5, y un cambio en el inventario cambia el plan (y una prueba lo detecta, ver tests/gen/test_tofu.py).

Lo que D2.5 no define y la IaC necesita está marcado con `ci` en el inventario y registrado en CAMBIOS-INVENTARIO.md (CI-25).
"""
from __future__ import annotations

import ipaddress
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from celeris_infra import Infra  # noqa: E402
from gen import vpn  # noqa: E402
from gen.comun import escribir  # noqa: E402

# Nombres de AWS para los algoritmos de D1.10. Un valor sin equivalente se rechaza: no se adivina.
AES_AWS = {"AES-256-GCM-16": "AES256-GCM-16"}
INTEGRIDAD_AWS = {"SHA2-384": "SHA2-384"}
DPD_MINIMO_AWS_S = 30      # AWS no admite un DPD menor de 30 s (D1.10 pide 10 s: CI-25)
CABECERA = {"_generado": "infra/gen/tofu.py desde infra/inventory.yaml; no editar a mano (make tofu-gen)"}


def _red(x: Infra, ref: str) -> str:
    """Resuelve «zona:EDGE», «componente:OBS01», «supernet:CAMPUS-RESUMEN» o «cidr:10.30.10.0/23» a un CIDR."""
    if ref in ("0.0.0.0/0",) or ref[0].isdigit():
        return ref
    tipo, _, nombre = ref.partition(":")
    if tipo == "cidr":
        return nombre
    if tipo == "zona":
        return x.zonas[nombre]["cidr"]
    if tipo == "supernet":
        return next(s["cidr"] for s in x.inv["supernets"] if s["id"] == nombre)
    if tipo == "componente":
        c = x.componentes[nombre]
        if c.get("cidr"):
            return c["cidr"]
        return next(i["ip"] for i in c["ips"] if i["ip"]) + "/32"
    raise ValueError(f"referencia de red desconocida: {ref}")


def _id_subred(componente: str) -> str:
    return componente.removeprefix("AWS-").lower()      # AWS-PUB-A → pub-a (los nombres de D2.5)


def _puertos(r: dict) -> list[tuple[int, int]]:
    if "rango" in r:
        return [tuple(r["rango"])]
    if "puerto" in r:
        return [(r["puerto"], r["puerto"])]
    return [(p, p) for p in r.get("puertos", [])]


def _ascii(texto: str) -> str:
    """La descripción de una regla de Security Group solo admite un conjunto ASCII (lo valida el proveedor de AWS)."""
    base = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^0-9A-Za-z_ .:/()#,@\[\]+=&;{}!$*-]", " ", base)[:255].strip()


def _reglas_sg(x: Infra, reglas, lado: str) -> list[dict]:
    if reglas == "todo":
        return [{"protocolo": "-1", "desde": 0, "hasta": 0, "cidr": "0.0.0.0/0", "descripcion": "sin restriccion (D2.5 no define reglas de salida)"}]
    out = []
    for r in reglas:
        ref = r["origen"] if lado == "ingress" else r["destino"]
        proto = "-1" if r["proto"] == "todo" else r["proto"]
        for d, h in (_puertos(r) if proto != "-1" else [(0, 0)]):
            out.append({"protocolo": proto, "desde": d, "hasta": h, "cidr": _red(x, ref),
                        "descripcion": _ascii(r.get("flujo") or r.get("nota") or "regla de D2.5")})
    return out


def _nacl(x: Infra, n: dict) -> dict:
    reglas = {"ingress": [], "egress": []}
    for lado in ("ingress", "egress"):
        cont = 100
        if n[lado] == "todo":
            reglas[lado].append({"numero": 100, "accion": "allow", "protocolo": "-1", "desde": 0, "hasta": 0, "cidr": "0.0.0.0/0"})
            continue
        for r in n[lado]:
            proto = "-1" if r["proto"] == "todo" else r["proto"]
            for d, h in (_puertos(r) if proto != "-1" else [(0, 0)]):
                reglas[lado].append({"numero": cont, "accion": r["accion"], "protocolo": proto, "desde": d, "hasta": h, "cidr": _red(x, r["origen"])})
                cont += 10
    return {"id": n["id"], "subredes": [_id_subred(s) for s in n["subredes"]], **reglas}


def _grupo(texto: str) -> int:
    """«grupo 20 (ECP-384)» → 20."""
    return int(texto.split()[1])


def _opciones_vpn_aws(x: Infra) -> dict:
    v = x.inv["vpn"]
    f1, f2 = v["fase1"], v["fase2"]
    if f1["cifrado"] not in AES_AWS or f2["cifrado"] not in AES_AWS or f1["prf"] not in INTEGRIDAD_AWS:
        raise ValueError("algoritmo de D1.10 sin equivalente en las opciones de túnel de AWS; agréguelo en gen/tofu.py")
    vpn._dh(f1["dh"]), vpn._dh(f2["pfs"])                       # rechaza un grupo sin equivalente en strongSwan
    dh1, dh2 = _grupo(f1["dh"]), _grupo(f2["pfs"])
    return {"ike_versions": ["ikev2"], "phase1_encryption_algorithms": [AES_AWS[f1["cifrado"]]],
            "phase1_integrity_algorithms": [INTEGRIDAD_AWS[f1["prf"]]], "phase1_dh_group_numbers": [dh1],
            "phase1_lifetime_seconds": f1["vida_s"],
            "phase2_encryption_algorithms": [AES_AWS[f2["cifrado"]]], "phase2_dh_group_numbers": [dh2],
            "phase2_lifetime_seconds": f2["vida_s"],
            "dpd_timeout_seconds": max(DPD_MINIMO_AWS_S, v["dpd"]["intervalo_s"]), "dpd_timeout_action": v["dpd"]["accion"],
            "startup_action": "add"}


def variables(x: Infra) -> dict:
    inv, aws = x.inv, x.inv["aws"]
    vpc = x.componentes["AWS-VPC"]
    subredes = [{"id": _id_subred(c["id"]), "cidr": c["cidr"], "az": c["az"], "publica": c["subred_tipo"] == "publica"}
                for c in x.componentes.values() if c["tipo"] == "aws_subred"]
    reserva = next(r["cidr"] for r in inv["reservas"] if r["dentro_de"] == "AWS-CELERIS")
    def destino(d: str) -> str:
        return d if d == "prefijo_s3" else _red(x, d)

    def salto(s: str) -> str:
        return "nat" if s.startswith("nat:") else s

    rutas = [{"id": t["id"], "subredes": [_id_subred(s) for s in t["subredes"]],
              "rutas": [{"destino": destino(r["destino"]), "salto": salto(r["salto"])} for r in t["rutas"]]} for t in aws["tablas_de_rutas"]]
    sgs = [{"id": s["id"], "componente": s["componente"], "ingress": _reglas_sg(x, s["ingress"], "ingress"),
            "egress": _reglas_sg(x, s["egress"], "egress")} for s in aws["security_groups"]]
    instancias = {}
    for cid in ("EC2-SHIELD", "EC2-CTRLR", "NAT01"):
        c = x.componentes[cid]
        instancias[cid] = {"ip": c["ips"][0]["ip"], "subred": _id_subred(c["subred"]), "tipo_produccion": c["instancia"]["tipo_produccion"],
                           "tipo_laboratorio": c["instancia"]["tipo_laboratorio"], "disco_gb": c["instancia"]["disco_gb_gp3"],
                           "grupo_de_seguridad": next(s["id"] for s in aws["security_groups"] if s["componente"] == cid)}
    v = inv["vpn"]
    ts = vpn.tuneles(x)
    ike, esp = vpn.propuestas(x)
    shield_puerto = x.flujos["F9"]["protocolos"][0]["puertos"][0]
    admin = next(p for pr in x.flujos["F12"]["protocolos"] for p in pr["puertos"] if p == 9128)
    cgw = aws["onprem_sim"]["cgw_sim"]
    lab = aws["onprem_sim"]["labcli_sim"]
    zona_lab = x.zonas[lab["zona"]]
    return {
        **CABECERA,
        "region_por_defecto": aws["region"]["laboratorio"],
        "etiquetas_base": {"Proyecto": aws["etiquetas"]["Proyecto"]},
        "ttl_por_defecto": aws["etiquetas"]["Ttl_por_defecto"],
        "vpc": {"nombre": "celeris", "cidr": vpc["cidr"], "reservado": reserva},
        "subredes": sorted(subredes, key=lambda s: s["id"]),
        "tablas_de_rutas": rutas,
        "security_groups": sgs,
        "nacls": [_nacl(x, n) for n in aws["nacl"]],
        "instancias": instancias,
        "presupuesto_alarma_porcentaje": aws["presupuesto"]["alarma_porcentaje"],
        "shield": {"puerto_f9": shield_puerto, "puerto_admin": admin,
                   "clientes_permitidos": [x.zonas[z]["cidr"] for z in ("EDGE",)]},
        "vpn": {
            "asn_aws": v["extremo_aws"]["asn"], "asn_cliente": v["extremo_onpremise"]["asn"],
            "redes": {"campus": v["extremo_onpremise"]["redes_anunciadas"][0], "aws": v["extremo_aws"]["redes_anunciadas"][0]},
            "tuneles": [{"nombre": t["nombre"], "inside_cidr": t["red"], "ip_aws": t["ip_aws"], "ip_cliente": t["ip_campus"],
                         "rol": t["rol"], "prepend": t["prepend"], "clave_vti": t["n"]} for t in ts],
            "opciones_aws": _opciones_vpn_aws(x),
            "strongswan": {"ike": ike, "esp": esp, "dpd_s": v["dpd"]["intervalo_s"], "dpd_accion": v["dpd"]["accion"],
                           "reautenticacion_ike_s": v["fase1"]["vida_s"], "vida_child_s": v["fase2"]["vida_s"]},
            "bgp": {"keepalive_s": v["bgp"]["keepalive_s"], "hold_s": v["bgp"]["hold_s"]},
            "mtu": v["mtu"], "mss": v["mss_clamping"],
        },
        "frr_conf": vpn.frr(x, "fw01"),
        "onprem_sim": {
            "vpc_cidr": _red(x, aws["onprem_sim"]["vpc"]["cidr"]),
            "subred_wan_cidr": cgw["subred_cidr"], "cgw_tipo": cgw["tipo"],
            "subred_lab_cidr": zona_lab["cidr"], "labcli_ip": next(i["ip"] for i in x.componentes[lab["componente"]]["ips"] if i["zona"] == lab["zona"]),
            "labcli_tipo": lab["tipo"], "campus_resumen": _red(x, "supernet:CAMPUS-RESUMEN"),
        },
    }


def texto(x: Infra) -> str:
    return json.dumps(variables(x), ensure_ascii=False, indent=2) + "\n"


def main(x: Infra, raiz: Path) -> Path:
    ruta = raiz / "deploy" / "opentofu" / "envs" / "demo" / "diseno.auto.tfvars.json"
    escribir(ruta, texto(x))
    return ruta
