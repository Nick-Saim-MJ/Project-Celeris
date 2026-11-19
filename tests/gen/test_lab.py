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
        if i["interfaz"] == "wan":
            continue                    # la WAN del laboratorio es 198.51.100.0/24 (F4.1)
        pref = int(infra.zonas[i["zona"]]["cidr"].split("/")[1])
        assert f"ip addr add {i['ip']}/{pref} dev {i['interfaz']}" in a, i
    assert f"ip addr add {lab.P['fw01_wan']}/24 dev wan" in a


def test_storage_y_backup_tienen_puente_y_solo_backup_llega_a_fw01(infra):
    t = lab.topologia(infra)["topology"]
    puentes = {n for n in t["nodes"] if n.startswith("br-")}
    assert puentes == {f"br-vlan{infra.zonas[z]['vlan']}" for z in lab.ZONAS_PUENTE} | {"br-wan"}
    assert {"br-vlan70", "br-vlan71"} <= puentes
    fw = [l["endpoints"][1].split(":")[0] for l in t["links"] if l["endpoints"][0].startswith("fw01-sim:")]
    assert "br-vlan71" in fw and "br-vlan70" not in fw, "STORAGE no tiene interfaz en FW01 (D1.4: sin gateway)"


def test_nas01_tiene_las_tres_ips_del_inventario_y_no_reenvia(infra):
    a = lab.archivos_nodo(infra, "nas01", AVISO)["arranque.sh"]
    for iface, zona in (("eth1", "STORAGE"), ("eth2", "BACKUP"), ("eth3", "MGMT")):
        ip = next(i["ip"] for i in infra.componentes["NAS01"]["ips"] if i["zona"] == zona)
        assert f"ip addr add {ip}/{infra.zonas[zona]['cidr'].split('/')[1]} dev {iface}" in a, zona
    assert "net.ipv4.ip_forward=0" in a
    assert "ip route replace default via 10.20.71.1" in a and "10.20.70.1" not in a, "STORAGE no tiene gateway"
    enlaces = [l["endpoints"] for l in lab.topologia(infra)["topology"]["links"] if l["endpoints"][0].startswith("nas01:")]
    assert [e[1].split(":")[0] for e in enlaces] == ["br-vlan70", "br-vlan71", "br-vlan10"]


def test_siem01_recibe_el_syslog_solo_por_tls_en_6514(infra):
    a = lab.archivos_nodo(infra, "siem01", AVISO)["arranque.sh"]
    assert "OPENSSL-LISTEN:6514" in a and "bind=10.20.50.10" in a and "514/udp" not in a and "UDP-LISTEN" not in a
    nodos = lab.topologia(infra)["topology"]["nodes"]
    assert nodos["siem01-wazuh"]["network-mode"] == "container:siem01" and "@sha256:" in nodos["siem01-wazuh"]["image"]


def test_todo_agente_de_wazuh_se_enrola_en_siem01_por_f13(infra):
    puertos = {p for pr in infra.flujos["F13"]["protocolos"] for p in pr["puertos"]}
    assert puertos == {1514, 1515}
    for nodo in lab.AGENTES:
        s = lab.archivos_nodo(infra, nodo, AVISO)["agente.sh"]
        assert "nc -z -w1 10.20.50.10 1515" in s and "agent-auth -m 10.20.50.10" in s, nodo
        assert "sh /lab/agente.sh &" in lab.archivos_nodo(infra, nodo, AVISO)["arranque.sh"], nodo


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


def test_el_pac_de_svc01_es_el_generado(infra):
    from gen import pac
    assert lab.archivos_nodo(infra, "svc01", AVISO)["wpad.dat"] == pac.generar(infra)


def test_edge01_genera_su_pac_con_el_binario_desde_el_inventario(infra):
    """REQ-F-26: edge01 no trae un wpad.dat hecho; lo genera `celeris-cache pac` con los valores del inventario. Se replica aquí el algoritmo del
    binario sobre la configuración que recibe y se compara con el generador de Python: los dos deben producir el mismo PAC."""
    import ipaddress
    import tomllib
    from gen import pac
    archivos = lab.archivos_nodo(infra, "edge01", AVISO)
    assert "wpad.dat" not in archivos and "celeris-cache pac /lab/config.toml > /pac/wpad.dat" in archivos["arranque.sh"]
    cfg = tomllib.loads(archivos["config.toml"])
    nodos = [f"{ip}:{pt}" for _, ip, pt in pac.nodos_proxy(infra)]
    assert cfg["pac_nodes"] == nodos
    cadena = "; ".join(f"PROXY {n}" for n in cfg["pac_nodes"]) + "; DIRECT"
    esperado = [f'  if (isInNet(host, "{ipaddress.ip_network(r).network_address}", "{ipaddress.ip_network(r).netmask}")) return "DIRECT";' for r in cfg["pac_direct_networks"]]
    generado = pac.generar(infra)
    assert f'return "{cadena}";' in generado
    assert all(linea in generado for linea in esperado) and f'host === "{cfg["pac_host"]}"' in generado


def test_los_nodos_edge_envian_los_miss_al_shield_con_mtls_y_conocen_la_honey_url(infra):
    import tomllib
    for nodo in ("edge01", "edge02"):
        cfg = tomllib.loads(lab.archivos_nodo(infra, nodo, AVISO)["config.toml"])
        puerto_f9 = infra.flujos["F9"]["protocolos"][0]["puertos"][0]
        assert cfg["upstream_parent"] == f"10.30.10.10:{puerto_f9}"
        assert cfg["upstream_parent_cert"] == f"/pki/{nodo}.pem" and cfg["upstream_parent_key"] == f"/pki/{nodo}.key"
        assert cfg["honey_urls"] == [lab.P["honey_url"]]
    sh = tomllib.loads(lab.archivos_nodo(infra, "shield01", AVISO)["config.toml"])
    assert sh["shield_listen"] == "10.30.10.10:8443" and sh["listen"].startswith("127.0.0.1:")
    assert sh["shield_client_ca"] == "/pki/nodos-ca.pem" and sh["admin_tls"] is True


def test_las_reglas_de_fw01_sim_son_las_del_generador(infra):
    from gen import nftables
    assert lab.archivos_nodo(infra, "fw01-sim", AVISO)["fw01sim.nft"] == nftables.generar(
        infra, modo="piloto", ventana=False, wan_ip=lab.P["fw01_wan"], aws_peers=lab.P["aws_peers"])


def test_ningun_archivo_generado_contiene_llaves(infra):
    patron = re.compile(r"(secret|PRIVATE KEY|psk)\s*[=:]", re.I)
    for nodo in lab.todos_los_nodos():
        for nombre, texto in lab.archivos_nodo(infra, nodo, AVISO).items():
            assert not patron.search(texto), f"{nodo}/{nombre}"
