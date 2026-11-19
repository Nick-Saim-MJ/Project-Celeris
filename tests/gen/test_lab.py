"""Topología del Modo L: las IP de cada nodo son las del inventario y lab/celeris.clab.yml está al día."""
import re

import yaml

from conftest import RAIZ
from gen import lab

AVISO = RAIZ / "docs" / "AVISO.md"


def arranque(infra, nodo):
    return lab.archivos_nodo(infra, nodo, AVISO)["arranque.sh"]


def test_la_topologia_versionada_esta_al_dia(infra):
    assert (RAIZ / "lab" / "celeris.clab.yml").read_text(encoding="utf-8") == lab.topologia_yaml(infra), \
        "lab/celeris.clab.yml no coincide con el inventario: ejecute `make lab-gen` y commitee el resultado"


def test_cada_host_usa_la_ip_del_inventario(infra):
    for nodo, (comp, zona, rol) in lab.NODOS.items():
        ip = next(i["ip"] for i in infra.componentes[comp]["ips"] if i["zona"] == zona and i["ip"])
        pref = int(infra.zonas[zona]["cidr"].split("/")[1])
        a = arranque(infra, nodo)
        assert f"ip addr add {ip}/{pref} dev eth1" in a, nodo
        assert f"ip route replace default via {infra.zonas[zona]['gateway']}" in a, nodo


def test_fw01_sim_usa_las_interfaces_e_ip_de_fw01(infra):
    a = arranque(infra, "fw01-sim")
    for i in infra.componentes["FW01"]["ips"]:
        if i["interfaz"] == "wan" or i["zona"] in ("BACKUP",):
            continue                    # la WAN del laboratorio es 198.51.100.0/24 (F4.1) y no hay VLAN 71 (CI-16)
        pref = int(infra.zonas[i["zona"]]["cidr"].split("/")[1])
        assert f"ip addr add {i['ip']}/{pref} dev {i['interfaz']}" in a, i
    assert f"ip addr add {lab.P['fw01_wan']}/24 dev wan" in a


def test_no_hay_puentes_para_storage_ni_backup(infra):
    t = lab.topologia(infra)["topology"]["nodes"]
    assert {n for n in t if n.startswith("br-")} == {f"br-vlan{infra.zonas[z]['vlan']}" for z in lab.ZONAS_PUENTE} | {"br-wan"}


def test_ids01_captura_vlan_10_20_31_y_50(infra):
    enlaces = [e for l in lab.topologia(infra)["topology"]["links"] for e in l["endpoints"] if e.startswith("ids01:")]
    assert len(enlaces) == 5            # eth1 (gestión) + 4 capturas
    puentes = [l["endpoints"][1].split(":")[0] for l in lab.topologia(infra)["topology"]["links"] if l["endpoints"][0].startswith("ids01:")]
    assert puentes == ["br-vlan50", "br-vlan10", "br-vlan20", "br-vlan31", "br-vlan50"]


def test_todos_los_enlaces_apuntan_a_nodos_existentes(infra):
    t = lab.topologia(infra)["topology"]
    for l in t["links"]:
        for e in l["endpoints"]:
            assert e.split(":")[0] in t["nodes"], e


def test_las_interfaces_esperadas_coinciden_con_los_enlaces(infra):
    t = lab.topologia(infra)["topology"]
    for nombre, n in t["nodes"].items():
        if n["kind"] != "linux" or "env" not in n:
            continue
        usadas = {e.split(":")[1] for l in t["links"] for e in l["endpoints"] if e.startswith(nombre + ":")}
        assert usadas == set(n["env"]["ESPERA_IFACES"].split()), nombre


def test_el_aviso_se_convierte_en_html_estatico(infra):
    h = lab._html_aviso(AVISO)
    assert h.startswith("<!doctype html>") and "<script" not in h


def test_edge_acepta_solo_los_clientes_de_f1(infra):
    c = lab.archivos_nodo(infra, "edge01", AVISO)["config.toml"]
    assert 'allowed_clients = ["10.20.32.0/22", "10.20.31.0/24"]' in c
    assert 'listen = "10.20.60.10:3128"' in c and 'admin_listen = "10.20.60.10:9128"' in c


def test_el_pac_de_svc01_y_edge01_es_el_generado(infra):
    from gen import pac
    for nodo in ("svc01", "edge01"):
        assert lab.archivos_nodo(infra, nodo, AVISO)["wpad.dat"] == pac.generar(infra)


def test_las_reglas_de_fw01_sim_son_las_del_generador(infra):
    from gen import nftables
    assert lab.archivos_nodo(infra, "fw01-sim", AVISO)["fw01sim.nft"] == nftables.generar(
        infra, modo="piloto", ventana=False, wan_ip=lab.P["fw01_wan"], aws_peers=lab.P["aws_peers"])


def test_ningun_archivo_generado_contiene_llaves(infra):
    patron = re.compile(r"(secret|PRIVATE KEY|psk)\s*[=:]", re.I)
    for nodo in lab.todos_los_nodos():
        for nombre, texto in lab.archivos_nodo(infra, nodo, AVISO).items():
            assert not patron.search(texto), f"{nodo}/{nombre}"
