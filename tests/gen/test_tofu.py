"""IaC del Modo A: las variables de OpenTofu salen del inventario y los módulos no llevan valores de diseño propios."""
import json
import re

from conftest import RAIZ
from gen import tofu

TOFU = RAIZ / "deploy" / "opentofu"
TFVARS = TOFU / "envs" / "demo" / "diseno.auto.tfvars.json"


def test_el_tfvars_versionado_esta_al_dia(infra):
    assert TFVARS.read_text(encoding="utf-8") == tofu.texto(infra), \
        "diseno.auto.tfvars.json no coincide con el inventario: ejecute `make tofu-gen` y commitee el resultado"


def test_las_redes_son_las_del_inventario(infra):
    v = tofu.variables(infra)
    assert v["vpc"]["cidr"] == infra.componentes["AWS-VPC"]["cidr"] == "10.30.0.0/16"
    esperadas = {c["id"].removeprefix("AWS-").lower(): c["cidr"] for c in infra.componentes.values() if c["tipo"] == "aws_subred"}
    assert {s["id"]: s["cidr"] for s in v["subredes"]} == esperadas
    assert sorted(esperadas) == ["app-a", "pub-a"]


def test_la_v04_no_lleva_componentes_retirados_ni_temporales(infra):
    """D2.5 v0.4: sin EC2-SHIELD, EC2-CTRLR ni NAT01 (retirados) y sin EC2-DR, NAT-DR ni sg-dr (temporales: solo en el simulacro)."""
    v = tofu.variables(infra)
    assert set(v["instancias"]) == {"EC2-GW"}
    assert [g["id"] for g in v["security_groups"]] == ["sg-gw"]
    for r in v["tablas_de_rutas"]:
        assert all(x["salto"] != "nat" for x in r["rutas"]), "la ruta por NAT-DR es solo del simulacro"
    assert "shield" not in v and "frr_conf" not in v and "onprem_sim" not in v


def test_las_instancias_usan_la_ip_y_la_subred_del_inventario(infra):
    v = tofu.variables(infra)
    c = infra.componentes["EC2-GW"]
    assert v["instancias"]["EC2-GW"]["ip"] == c["ips"][0]["ip"] == "10.30.0.10"
    assert v["instancias"]["EC2-GW"]["subred"] == c["subred"].removeprefix("AWS-").lower() == "pub-a"


def test_sg_gw_replica_f29_f30_y_f13(infra):
    sg = next(s for s in tofu.variables(infra)["security_groups"] if s["id"] == "sg-gw")
    ctrl, siem = infra.componentes["CTRL01"]["ips"][0]["ip"] + "/32", infra.componentes["SIEM01"]["ips"][0]["ip"] + "/32"
    assert {(r["protocolo"], r["desde"], r["cidr"]) for r in sg["ingress"]} == {("tcp", 443, "0.0.0.0/0")}                       # F29
    assert {(r["protocolo"], r["desde"], r["cidr"]) for r in sg["egress"]} == {("tcp", 443, ctrl), ("tcp", 1514, siem), ("tcp", 1515, siem), ("tcp", 443, "0.0.0.0/0")}


def test_la_ruta_al_campus_es_la_de_la_sede_con_salto_vgw(infra):
    """En AWS real la trae la propagación de BGP; con var.emulador el módulo aws-vpn la crea estática con este mismo destino."""
    v = tofu.variables(infra)
    destinos = {r["destino"] for t in v["tablas_de_rutas"] for r in t["rutas"] if r["salto"] == "vgw"}
    assert destinos == {"10.20.0.0/16"} == {infra.inv["vpn"]["extremo_onpremise"]["redes_anunciadas"][0]}


def test_el_respaldo_sigue_d2_5(infra):
    r = tofu.variables(infra)["respaldo"]
    assert r["bucket"] == "celeris-backups" and r["versionado"] is True
    assert r["object_lock"] == {"dias": 30, "modo": "compliance"}
    assert r["ip_campus"] == infra.inv["vpn"]["extremo_onpremise"]["ip_publica"] == tofu.variables(infra)["vpn"]["ip_publica_campus"]


def test_las_descripciones_de_reglas_son_validas_para_aws(infra):
    permitido = re.compile(r"^[0-9A-Za-z_ .:/()#,@\[\]+=&;{}!$*-]*$")
    for s in tofu.variables(infra)["security_groups"]:
        for r in s["ingress"] + s["egress"]:
            assert permitido.match(r["descripcion"]), (s["id"], r["descripcion"])


def test_las_opciones_de_la_vpn_de_aws_siguen_d1_10(infra):
    o = tofu.variables(infra)["vpn"]["opciones_aws"]
    assert o["ike_versions"] == ["ikev2"]
    assert o["phase1_dh_group_numbers"] == o["phase2_dh_group_numbers"] == [20]
    assert o["phase1_lifetime_seconds"] == 28800 and o["phase2_lifetime_seconds"] == 3600
    assert o["dpd_timeout_seconds"] >= tofu.DPD_MINIMO_AWS_S      # AWS no admite menos de 30 s (CI-25)


def test_el_entorno_apunta_al_emulador_por_defecto_y_no_a_una_cuenta_real():
    """AWS emulado: plano de control, sin tráfico. Sin `-var emulador=false` nadie toca una cuenta real."""
    variables = (TOFU / "envs" / "demo" / "variables.tf").read_text(encoding="utf-8")
    assert re.search(r'variable "emulador" \{.*?default\s*=\s*true', variables, re.S)
    versiones = (TOFU / "envs" / "demo" / "versions.tf").read_text(encoding="utf-8")
    for clave in ("skip_credentials_validation", "skip_requesting_account_id", "skip_metadata_api_check", "custom_ca_bundle", "endpoints"):
        assert clave in versiones, clave
    assert re.search(r'access_key\s*=\s*var\.emulador \? "ficticia"', versiones)
    assert 'default     = "https://127.0.0.1:' in variables, "el endpoint por defecto es local"


def test_con_el_emulador_la_propagacion_de_rutas_se_reemplaza_por_una_ruta_estatica():
    vpn = (TOFU / "modules" / "aws-vpn" / "main.tf").read_text(encoding="utf-8")
    assert "for_each       = var.emulador ? {} : var.tablas_de_rutas" in vpn, "con el emulador no se propaga (NotImplemented)"
    assert "aws_route\" \"campus_estatica" in vpn and "gateway_id             = aws_vpn_gateway.vgw.id" in vpn
    assert "DIFERENCIA CON AWS REAL" in vpn


def test_los_modulos_de_la_demo_son_los_de_la_v04():
    modulos = {p.name for p in (TOFU / "modules").iterdir() if p.is_dir()}
    assert {"aws-vpc", "aws-vpn", "aws-gw", "aws-backup"} <= modulos
    assert "aws-shield" not in modulos and "aws-dr" not in modulos


def test_la_region_por_defecto_es_la_del_laboratorio(infra):
    por_defecto = re.search(r'variable "region" \{.*?default\s*=\s*"([^"]+)"', (TOFU / "envs" / "demo" / "variables.tf").read_text(encoding="utf-8"), re.S)
    assert por_defecto.group(1) == infra.inv["aws"]["region"]["laboratorio"] == "us-east-1"


def test_los_modulos_no_llevan_valores_de_diseno():
    """Ni IP privadas, ni ASN, ni puertos de aplicación escritos en los .tf: todo llega del inventario por variables."""
    prohibido = re.compile(r"\b(10\.\d+\.\d+\.\d+|169\.254\.\d+\.\d+|198\.51\.100\.\d+|203\.0\.113\.\d+|650\d\d|64512|8443|9128)\b")   # ASN de D1.10 (65532, el UID no-root de la imagen, no es de diseño)
    for ruta in list(TOFU.glob("modules/**/*.tf")) + list(TOFU.glob("modules/**/*.tftpl")) + list(TOFU.glob("envs/demo/*.tf")):
        for n, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
            sin_comentario = linea.split("#", 1)[0]
            assert not prohibido.search(sin_comentario), f"{ruta.relative_to(RAIZ)}:{n}: valor de diseño escrito a mano: {linea.strip()}"


def test_no_hay_secretos_ni_estado_en_el_repo():
    for ruta in TOFU.rglob("*"):
        if ruta.is_file() and ".terraform" not in ruta.parts and ruta.name != ".terraform.lock.hcl":
            assert not ruta.name.endswith((".tfstate", ".tfstate.backup", ".tfplan")), ruta
    contenido = TFVARS.read_text(encoding="utf-8")
    assert not re.search(r"(?i)\b(psk|secret|password|token)\b\s*\"?\s*:\s*\"[^\"]+", contenido)
    json.loads(contenido)
