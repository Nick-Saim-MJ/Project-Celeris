"""Topología del Modo L v0.4 (CE03 D5.3): las IP de cada nodo son las del inventario y lab/celeris.clab.yml está al día."""
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
        assert f"nameserver {infra.zonas[zona]['gateway']}" in a and "nameserver 10.20.20.30" not in a, "el DNS es Unbound de FW01 (D-28)"


def test_los_pc_de_prueba_estan_dentro_del_rango_de_su_laboratorio(infra):
    """labcli02 en LAB-01 y labcli03 en LAB-03 (T52): sus IP son parámetros del laboratorio (CI-48) y caen en el /26 correcto."""
    import ipaddress
    rangos = {l["id"]: ipaddress.ip_network(l["cidr"]) for l in infra.inv["rangos_lab"]["laboratorios"]}
    assert ipaddress.ip_address(lab.P["labcli02"]) in rangos["LAB-01"] and ipaddress.ip_address(lab.P["labcli03"]) in rangos["LAB-03"]
    for nodo, (zona, par) in lab.CLIENTES_LAB.items():
        assert f"ip addr add {lab.P[par]}/22 dev eth1" in arranque(infra, nodo)


def test_fw01_sim_usa_las_interfaces_e_ip_de_fw01(infra):
    """v0.4: la WAN de FW01 es 10.20.0.2/29 en la red de tránsito y la ruta por defecto va al FortiGate (10.20.0.1)."""
    a = arranque(infra, "fw01-sim")
    for i in infra.componentes["FW01"]["ips"]:
        pref = int(infra.zonas[i["zona"]]["cidr"].split("/")[1])
        assert f"ip addr add {i['ip']}/{pref} dev {i['interfaz']}" in a, i
    assert "ip addr add 10.20.0.2/29 dev wan" in a and "ip route replace default via 10.20.0.1" in a
    assert "chronyd" in a and "unbound" in a, "DNS y NTP en FW01 (D-28)"


def test_fgt_sim_hace_nat_1_a_1_solo_de_ipsec_y_portal(infra):
    archivos = lab.archivos_nodo(infra, "fgt-sim", AVISO)
    nft = archivos["fgt.nft"]
    pub = lab.P["fgt_wan"]
    assert f"ip daddr {pub} udp dport {{ 500, 4500 }}" in nft and f"ip daddr {pub} tcp dport {{ 80, 443 }}" in nft
    assert nft.count("dnat to 10.20.0.2") == 2, "solo esos puertos se publican"
    a = archivos["arranque.sh"]
    assert "ip addr add 10.20.0.1/29 dev eth1" in a and "ip route replace 10.20.0.0/16 via 10.20.0.2" in a
    assert f"ip addr add {lab.P['wifi_gw']}/16 dev eth3" in a, "ruta al Wi-Fi 172.16.0.0/16"


def test_fw01_negocia_nat_t_con_la_ip_publica_como_identidad(infra):
    sw = lab.archivos_nodo(infra, "fw01-sim", AVISO)["swanctl.conf"]
    assert "local_addrs = 10.20.0.2" in sw and "encap = yes" in sw
    assert f"id = {lab.P['fgt_wan']}" in sw
    assert f"remote_addrs = {lab.P['fgt_wan']}" in lab.archivos_nodo(infra, "vgw-sim", AVISO)["swanctl.conf"]
    assert "local 10.20.0.2" in lab.archivos_nodo(infra, "fw01-sim", AVISO)["vti-up.sh"]


def test_siete_vlan_con_puente_y_sin_las_retiradas(infra):
    t = lab.topologia(infra)["topology"]
    puentes = {n for n in t["nodes"] if n.startswith("br-")}
    assert puentes == {f"br-vlan{infra.zonas[z]['vlan']}" for z in lab.ZONAS_PUENTE} | {"br-wan", "br-wifi"}
    assert not ({"br-vlan31", "br-vlan70", "br-vlan71"} & puentes), "VLAN 31, 70 y 71 retiradas (CI-39)"
    fw = [l["endpoints"][1].split(":")[0] for l in t["links"] if l["endpoints"][0].startswith("fw01-sim:") and l["endpoints"][1].startswith("br-")]
    assert sorted(fw) == sorted(f"br-vlan{infra.zonas[z]['vlan']}" for z in lab.ZONAS_FW01)
    assert ["fw01-sim:eth1", "fgt-sim:eth1"] in [l["endpoints"] for l in t["links"]], "la WAN de FW01 va al FortiGate por la red de tránsito"


def test_los_nodos_retirados_no_existen_y_los_nuevos_si(infra):
    nodos = lab.topologia(infra)["topology"]["nodes"]
    for retirado in ("svc01", "obs01", "ids01", "nas01", "probe01", "shield01", "ctrlr-sim", "waf01", "web01"):
        assert retirado not in nodos, retirado
    for nuevo in ("fgt-sim", "byod01", "enc01", "labcli02", "labcli03", "ctrl01", "origin-sim", "gw-sim", "portal01"):
        assert nuevo in nodos, nuevo


def test_wifi_sim_conecta_byod01_con_fgt_sim_y_gw_sim_cuelga_de_vgw_sim(infra):
    enlaces = [l["endpoints"] for l in lab.topologia(infra)["topology"]["links"]]
    assert any(e[0] == "byod01:eth1" and e[1].startswith("br-wifi:") for e in enlaces)
    assert any(e[0] == "fgt-sim:eth3" and e[1].startswith("br-wifi:") for e in enlaces)
    assert ["vgw-sim:eth2", "gw-sim:eth1"] in enlaces
    a = lab.archivos_nodo(infra, "gw-sim", AVISO)["arranque.sh"]
    assert "ip addr add 10.30.0.10/24 dev eth1" in a and "ip route replace default via 10.30.0.1" in a
    assert "proxy_pass https://10.20.20.10:443" in lab.archivos_nodo(infra, "gw-sim", AVISO)["nginx.conf"]
    assert "proxy_ssl_certificate /pki/gw-sim.pem" in lab.archivos_nodo(infra, "gw-sim", AVISO)["nginx.conf"]


def test_portal01_une_el_waf_y_el_sitio_estatico(infra):
    a = lab.archivos_nodo(infra, "portal01", AVISO)
    assert "root /lab/web" in a["nginx.conf"] and "modsecurity on" in a["nginx.conf"] and "proxy_pass" not in a["nginx.conf"]
    assert "web/index.html" in a and "<script" not in a["web/index.html"]
    assert "ip addr add 10.20.40.10/24 dev eth1" in a["arranque.sh"]


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


def test_la_deteccion_de_red_es_suricata_de_fw01_en_lab_y_servers(infra):
    """DET-02 (v0.4): ya no hay ids01 ni captura por espejo; Suricata corre en fw01-sim sobre las interfaces LAB y SERVERS."""
    archivos = lab.archivos_nodo(infra, "fw01-sim", AVISO)
    assert "- interface: vlan30" in archivos["suricata.yaml"] and "- interface: vlan20" in archivos["suricata.yaml"]
    assert "sid:9000001" in archivos["local.rules"]
    assert "suricata --af-packet" in archivos["arranque.sh"]
    assert "OPENSSL:10.20.50.10:6514" in archivos["eve-a-siem.sh"], "los eventos llegan a Wazuh por F14, no por un agente"


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


def test_edge_acepta_solo_los_rangos_habilitados_y_trata_el_wifi_como_byod(infra):
    """REQ-F-10 y REQ-F-32: allowed_clients = rangos /26 habilitados + infraestructura de LAB + Wi-Fi; REQ-F-36: byod_networks = el Wi-Fi."""
    import tomllib
    cfg = tomllib.loads(lab.archivos_nodo(infra, "edge01", AVISO)["config.toml"])
    esperados = [l["cidr"] for l in infra.inv["rangos_lab"]["laboratorios"] if l["habilitado"]] + ["10.20.35.0/24", "172.16.0.0/16"]
    assert cfg["allowed_clients"] == esperados and cfg["byod_networks"] == ["172.16.0.0/16"]
    assert cfg["listen"] == "10.20.60.10:3128" and cfg["admin_listen"] == "10.20.60.10:9128"
    assert "upstream_parent" not in cfg, "sin shield (D-19)"


def test_un_laboratorio_deshabilitado_sale_de_allowed_clients(infra):
    import copy
    import tomllib
    from celeris_infra import Infra
    inv = copy.deepcopy(infra.inv)
    next(l for l in inv["rangos_lab"]["laboratorios"] if l["id"] == "LAB-03")["habilitado"] = False
    cfg = tomllib.loads(lab.archivos_nodo(Infra(inv, infra.pru, infra.traz), "edge01", AVISO)["config.toml"])
    assert "10.20.32.128/26" not in cfg["allowed_clients"] and "10.20.32.0/26" in cfg["allowed_clients"]


def test_los_dos_nodos_sirven_el_pac_con_el_binario(infra):
    for nodo in ("edge01", "edge02"):
        archivos = lab.archivos_nodo(infra, nodo, AVISO)
        assert "celeris-cache pac /lab/config.toml > /pac/wpad.dat" in archivos["arranque.sh"] and "nginx -c /lab/nginx.conf" in archivos["arranque.sh"], nodo
    assert not any("svc01" in n for n in lab.todos_los_nodos())


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


def test_los_nodos_edge_conocen_la_honey_url(infra):
    import tomllib
    for nodo in ("edge01", "edge02"):
        cfg = tomllib.loads(lab.archivos_nodo(infra, nodo, AVISO)["config.toml"])
        assert cfg["honey_urls"] == [lab.P["honey_url"]]


def test_ctrl01_es_una_consola_de_prueba_con_sesiones_campus_y_remoto(infra):
    a = lab.archivos_nodo(infra, "ctrl01", AVISO)
    assert "ip addr add 10.20.20.10/24 dev eth1" in a["arranque.sh"] and "REQ-F-37" in a["consola.py"] and "403" in a["consola.py"]


def test_las_reglas_de_fw01_sim_son_las_del_generador(infra):
    from gen import nftables
    assert lab.archivos_nodo(infra, "fw01-sim", AVISO)["fw01sim.nft"] == nftables.generar(
        infra, modo="piloto", ventana=False, aws_peers=lab.P["aws_peers"])


def test_ningun_archivo_generado_contiene_llaves(infra):
    patron = re.compile(r"(secret|PRIVATE KEY|psk)\s*[=:]", re.I)
    for nodo in lab.todos_los_nodos():
        for nombre, texto in lab.archivos_nodo(infra, nodo, AVISO).items():
            assert not patron.search(texto), f"{nodo}/{nombre}"


def test_la_configuracion_firmada_llega_a_los_nodos_edge_desde_ctrl01(infra):
    """REQ-F-17: ctrl01 escribe /firmada (config.toml + .sig); los EDGE la leen con la llave pública fijada en su configuración de arranque."""
    import tomllib
    nodos = lab.topologia(infra)["topology"]["nodes"]
    assert ".run/firmada:/firmada" in nodos["ctrl01"]["binds"]
    for n in ("edge01", "edge02"):
        assert ".run/firmada:/firmada:ro" in nodos[n]["binds"]
        cfg = tomllib.loads(lab.archivos_nodo(infra, n, AVISO)["config.toml"])
        assert cfg["signed_config"] == "/firmada/config.toml" and cfg["config_public_key"] == "/pki/config-firma.pub"
    firmar = lab.archivos_nodo(infra, "ctrl01", AVISO)["firmar.sh"]
    assert "openssl pkeyutl -sign -inkey /pki/config-firma.key -rawin" in firmar and "PRIVATE" not in firmar


def test_la_pki_de_laboratorio_genera_el_par_de_firma_fuera_del_repositorio(tmp_path):
    lab.crear_pki(tmp_path)
    pub = (tmp_path / "config-firma.pub").read_text().strip()
    assert len(bytes.fromhex(pub)) == 32 and (tmp_path / "config-firma.key").exists()
