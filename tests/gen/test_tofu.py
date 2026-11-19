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
    assert v["onprem_sim"]["vpc_cidr"] == "10.20.0.0/16"
    esperadas = {c["id"].removeprefix("AWS-").lower(): c["cidr"] for c in infra.componentes.values() if c["tipo"] == "aws_subred"}
    assert {s["id"]: s["cidr"] for s in v["subredes"]} == esperadas
    assert sorted(esperadas) == ["app-a", "app-b", "data-a", "data-b", "pub-a", "pub-b"]


def test_las_instancias_usan_la_ip_y_la_subred_del_inventario(infra):
    v = tofu.variables(infra)
    for cid in ("EC2-SHIELD", "EC2-CTRLR", "NAT01"):
        c = infra.componentes[cid]
        assert v["instancias"][cid]["ip"] == c["ips"][0]["ip"]
        assert v["instancias"][cid]["subred"] == c["subred"].removeprefix("AWS-").lower()


def test_sg_shield_replica_f9_y_f12(infra):
    sg = next(s for s in tofu.variables(infra)["security_groups"] if s["id"] == "sg-shield")
    edge = infra.zonas["EDGE"]["cidr"]
    obs = infra.componentes["OBS01"]["ips"][0]["ip"] + "/32"
    assert {(r["protocolo"], r["desde"], r["cidr"]) for r in sg["ingress"]} == {("tcp", 8443, edge), ("tcp", 9128, obs)}


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
