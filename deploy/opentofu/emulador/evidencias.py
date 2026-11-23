#!/usr/bin/env python3
"""AWS EMULADO: PLANO DE CONTROL, SIN TRÁFICO.

Lee lo que `tofu apply` creó en el AWS Emulator con `aws ec2 describe-*` y `aws s3api get-*`, lo guarda en evidencias/<fecha>-E/ sin secretos
y lo compara con infra/inventory.yaml. No toca ninguna cuenta real: el endpoint es el del emulador local.

Uso (con el emulador en marcha y `tofu apply` hecho):
    AWS_ENDPOINT_URL=https://127.0.0.1:9297 AWS_CA_BUNDLE=~/.aws/emulator/9297/ca.pem python3 evidencias.py [--fecha AAAA-MM-DD]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "infra"))
from celeris_infra import Infra  # noqa: E402
from gen import tofu  # noqa: E402

AVISO = "AWS emulado: plano de control, sin tráfico"
SECRETOS = {"PreSharedKey", "CustomerGatewayConfiguration", "SecretAccessKey", "AccessKeyId", "SessionToken", "Password"}


def aws(*args: str):
    cli = os.environ.get("AWS_CLI", "aws").split()
    r = subprocess.run([*cli, *args, "--output", "json"], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return {"_error": r.stderr.strip().splitlines()[-1] if r.stderr.strip() else f"salida {r.returncode}"}
    return json.loads(r.stdout) if r.stdout.strip() else {}


def limpiar(x):
    """Quita llaves y credenciales: ninguna evidencia lleva secretos."""
    if isinstance(x, dict):
        return {k: ("[REDACTADO]" if k in SECRETOS else limpiar(v)) for k, v in x.items()}
    if isinstance(x, list):
        return [limpiar(v) for v in x]
    return x


CONSULTAS = {
    "vpcs": ("ec2", "describe-vpcs"), "subredes": ("ec2", "describe-subnets"), "tablas_de_rutas": ("ec2", "describe-route-tables"),
    "internet_gateways": ("ec2", "describe-internet-gateways"), "security_groups": ("ec2", "describe-security-groups"),
    "nacls": ("ec2", "describe-network-acls"), "vpn_gateways": ("ec2", "describe-vpn-gateways"),
    "customer_gateways": ("ec2", "describe-customer-gateways"), "vpn_connections": ("ec2", "describe-vpn-connections"),
    "vpc_endpoints": ("ec2", "describe-vpc-endpoints"), "direcciones_elasticas": ("ec2", "describe-addresses"),
    "instancias": ("ec2", "describe-instances"), "buckets": ("s3api", "list-buckets"),
}
BUCKET = {"versionado": "get-bucket-versioning", "object_lock": "get-object-lock-configuration", "politica": "get-bucket-policy",
          "acceso_publico": "get-public-access-block"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fecha", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    a = ap.parse_args()
    carpeta = RAIZ / "evidencias" / f"{a.fecha}-E"
    carpeta.mkdir(parents=True, exist_ok=True)
    x = Infra.cargar()
    d = tofu.variables(x)
    datos = {}
    for nombre, (servicio, op) in CONSULTAS.items():
        datos[nombre] = limpiar(aws(servicio, op))
    bucket = d["respaldo"]["bucket"]
    datos["bucket"] = {k: limpiar(aws("s3api", op, "--bucket", bucket)) for k, op in BUCKET.items()}
    datos["usuario_de_respaldo"] = limpiar(aws("iam", "get-user", "--user-name", d["respaldo"]["usuario"]))
    datos["politica_del_usuario"] = limpiar(aws("iam", "list-user-policies", "--user-name", d["respaldo"]["usuario"]))
    for nombre, valor in datos.items():
        (carpeta / f"{nombre}.json").write_text(json.dumps({"aviso": AVISO, "datos": valor}, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- comparación con el inventario
    v = []

    def comprobar(id_, que, ok, detalle):
        v.append({"id": id_, "comprobacion": que, "resultado": "PASA" if ok else "FALLA", "detalle": detalle})

    vpcs = [p for p in datos["vpcs"].get("Vpcs", []) if p["CidrBlock"] == d["vpc"]["cidr"]]
    comprobar("V1", f"VPC {d['vpc']['cidr']}", len(vpcs) == 1, [p["VpcId"] for p in vpcs])
    vpc_id = vpcs[0]["VpcId"] if vpcs else None
    esperadas = {s["cidr"]: s for s in d["subredes"]}
    reales = {s["CidrBlock"]: s for s in datos["subredes"].get("Subnets", []) if s["VpcId"] == vpc_id}
    comprobar("V2", "subredes pub-a y app-a con sus CIDR", set(reales) == set(esperadas), sorted(reales))
    tablas = [t for t in datos["tablas_de_rutas"].get("RouteTables", []) if t["VpcId"] == vpc_id]
    rutas = {(r.get("DestinationCidrBlock"), "igw" if r.get("GatewayId", "").startswith("igw-") else "vgw" if r.get("GatewayId", "").startswith("vgw-") else r.get("GatewayId", ""))
             for t in tablas for r in t["Routes"] if r.get("DestinationCidrBlock")}
    comprobar("V3", "ruta 0.0.0.0/0 hacia el IGW", ("0.0.0.0/0", "igw") in rutas, sorted(rutas, key=str))
    campus = x.inv["vpn"]["extremo_onpremise"]["redes_anunciadas"][0]
    comprobar("V4", f"ruta estática {campus} hacia el VGW (el emulador no propaga rutas: diferencia con AWS real)", (campus, "vgw") in rutas, campus)
    vgws = datos["vpn_gateways"].get("VpnGateways", [])
    comprobar("V5", f"VGW con ASN {d['vpn']['asn_aws']} adjunto a la VPC", any(g.get("AmazonSideAsn") == d["vpn"]["asn_aws"] and any(at.get("VpcId") == vpc_id and at.get("State") == "attached" for at in g.get("VpcAttachments", [])) for g in vgws), [g["VpnGatewayId"] for g in vgws])
    cgws = datos["customer_gateways"].get("CustomerGateways", [])
    comprobar("V6", f"customer gateway {d['vpn']['ip_publica_campus']} (FortiGate, S-29) con ASN {d['vpn']['asn_cliente']}", any(c["IpAddress"] == d["vpn"]["ip_publica_campus"] and str(c["BgpAsn"]) == str(d["vpn"]["asn_cliente"]) for c in cgws), [c["CustomerGatewayId"] for c in cgws])
    conex = datos["vpn_connections"].get("VpnConnections", [])
    comprobar("V7", "conexión VPN con BGP (sin rutas estáticas) y dos túneles", len(conex) == 1 and conex[0]["Options"]["StaticRoutesOnly"] is False and len(conex[0]["Options"]["TunnelOptions"]) == 2, [c["VpnConnectionId"] for c in conex])
    sg = next((g for g in datos["security_groups"].get("SecurityGroups", []) if g["VpcId"] == vpc_id and g["GroupName"].endswith("sg-gw")), None)
    entrada = {(p.get("IpProtocol"), p.get("FromPort"), r["CidrIp"]) for p in (sg or {}).get("IpPermissions", []) for r in p.get("IpRanges", [])}
    comprobar("V8", "sg-gw: entrada TCP 443 desde Internet (F29) y ninguna otra", entrada == {("tcp", 443, "0.0.0.0/0")}, sorted(entrada, key=str))
    salida = {(p.get("IpProtocol"), p.get("FromPort"), r["CidrIp"]) for p in (sg or {}).get("IpPermissionsEgress", []) for r in p.get("IpRanges", [])}
    esperada_salida = {(r["protocolo"], r["desde"], r["cidr"]) for g in d["security_groups"] for r in g["egress"] if g["id"] == "sg-gw"}
    comprobar("V9", "sg-gw: salida solo CTRL01:443 (F30), SIEM01:1514/1515 (F13) y TCP 443 a Internet", salida == esperada_salida, sorted(salida, key=str))
    nombre = lambda r: next((t["Value"] for t in r.get("Tags", []) if t["Key"] == "Name"), None)
    nacls = {nombre(n): n for n in datos["nacls"].get("NetworkAcls", []) if n["VpcId"] == vpc_id and nombre(n)}
    comprobar("V10", "NACL nacl-public y nacl-private", {"nacl-public", "nacl-private"} <= set(nacls), sorted(nacls))
    gw = [i for r in datos["instancias"].get("Reservations", []) for i in r["Instances"] if i.get("PrivateIpAddress") == d["instancias"]["EC2-GW"]["ip"]]
    comprobar("V11", f"EC2-GW en {d['instancias']['EC2-GW']['ip']} con IMDSv2 obligatorio", len(gw) == 1 and gw[0].get("MetadataOptions", {}).get("HttpTokens") == "required", [i["InstanceId"] for i in gw])
    comprobar("V12", f"bucket {bucket} existe", any(b["Name"] == bucket for b in datos["buckets"].get("Buckets", [])), bucket)
    comprobar("V13", "versionado activo", datos["bucket"]["versionado"].get("Status") == "Enabled", datos["bucket"]["versionado"])
    ol = datos["bucket"]["object_lock"].get("ObjectLockConfiguration", {})
    ret = ol.get("Rule", {}).get("DefaultRetention", {})
    comprobar("V14", f"Object Lock {d['respaldo']['object_lock']['dias']} días, modo {d['respaldo']['object_lock']['modo']}", ol.get("ObjectLockEnabled") == "Enabled" and ret.get("Days") == d["respaldo"]["object_lock"]["dias"] and ret.get("Mode", "").lower() == d["respaldo"]["object_lock"]["modo"], ret)
    pol = datos["bucket"]["politica"].get("Policy", "")
    comprobar("V15", f"política del bucket: el usuario de respaldo solo desde {d['respaldo']['ip_campus']}", d["respaldo"]["ip_campus"] in pol and "NotIpAddress" in pol, "politica.json")
    comprobar("V16", "usuario de respaldo con política solo-escritura", bool(datos["politica_del_usuario"].get("PolicyNames")), datos["politica_del_usuario"].get("PolicyNames"))
    creados = [t for t in tablas if nombre(t)] + list(nacls.values()) + gw + vgws + conex
    sin = [r for r in creados if not {"Proyecto", "Ttl"} <= {t["Key"] for t in r.get("Tags", [])}]
    comprobar("V17", "etiquetas Proyecto y Ttl en tablas de rutas, NACL, EC2-GW, VGW y conexión VPN", bool(creados) and not sin, f"{len(creados)} recursos revisados, {len(sin)} sin etiquetas")

    resultado = {"aviso": AVISO, "fecha": a.fecha, "endpoint": os.environ.get("AWS_ENDPOINT_URL", "(sin definir)"),
                 "resumen": {k: sum(c["resultado"] == k for c in v) for k in ("PASA", "FALLA")}, "comprobaciones": v}
    (carpeta / "verificaciones.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    for c in v:
        print(f"{c['id']:4} {c['resultado']:5} {c['comprobacion']}")
    print(f"\n{AVISO}: {resultado['resumen']} → {carpeta.relative_to(RAIZ)}")
    return 1 if resultado["resumen"]["FALLA"] else 0


if __name__ == "__main__":
    sys.exit(main())
