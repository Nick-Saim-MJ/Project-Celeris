"""Topología containerlab del Modo L (Parte F4.1) y configuración de cada nodo, generadas desde infra/inventory.yaml.

v0.4 (CE03 D5.3): fgt-sim emula al FortiGate (NAT 1:1 y NAT-T, sin FortiGuard), wifi-sim + byod01 al Wi-Fi de estudiantes, portal01 une
WAF01 y WEB01, ctrl01 es una consola de prueba y gw-sim emula a EC2-GW detrás de vgw-sim; ya no hay svc01, obs01, ids01, nas01, probe01 ni shield01.
Todo el laboratorio es EMULADO (Parte F4.2): fw01-sim no es OPNsense, vgw-sim no es el VGW de AWS, el WAF es nginx con
ModSecurity y OWASP CRS (D5.3 dice Caddy + Coraza; la imagen base no los trae) y los honeypots son equivalentes funcionales.
Las IP de los nodos, los CIDR, las puertas de enlace, los puertos y los flujos salen del inventario. Lo que el inventario no
define (la WAN del laboratorio, los nombres DNS de prueba, la IP de vgw-sim en la subred app-a) está en PARAMETROS_LAB y se
registra en docs/infra/e1/CAMBIOS-INVENTARIO.md (CI-24 y CI-48).
"""
from __future__ import annotations

import ipaddress
import re
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from celeris_infra import Infra  # noqa: E402
from gen import nftables, pac, vpn  # noqa: E402
from gen.comun import cabecera, escribir, fw01_interfaces  # noqa: E402

IMAGEN_BASE = "celeris-lab/base:dev"
IMAGEN_NODO = "celeris-lab/node:dev"        # base + el binario de celeris-node (misma compilación que la imagen OCI)
IMAGEN_COWRIE = "cowrie/cowrie@sha256:e7c4b4fe5fbb874e682c6c0c7a1daf1c3183c622d5cc2d281f453c1c4d9f97ac"  # oficial, sin shell: va como acompañante de hny01
IMAGEN_WAZUH = "wazuh/wazuh-manager@sha256:b906ebfc77d78446e9b676e1a0b3cd78e2bf3ac2341688f1726b09c29e0aa826"  # 4.9.2; sin shell ni herramientas de red: acompañante de siem01

# CI-24: valores del laboratorio que el inventario no fija.
PARAMETROS_LAB = {
    "wan_red": "198.51.100.0/24",           # F4.1: la WAN y las IP públicas se reemplazan por la red de documentación
    "fgt_wan": "198.51.100.10",             # IP pública del FortiGate (FGT-EXT): en el laboratorio 198.51.100.10 sustituye a 203.0.113.10
    "ext01": "198.51.100.100",              # atacante externo / origen web de prueba
    "origin_sim": "198.51.100.110",         # origin-sim: origen con archivos de 100 MB a 1 GB (D5.3; CI-48)
    "gw_publica": "198.51.100.30",          # IP pública de EC2-GW en el laboratorio (la real la asigna AWS; CI-48)
    "aws_peers": ["198.51.100.21", "198.51.100.22"],
    "vgw_lan": "10.30.0.1",                 # vgw-sim dentro de pub-a, junto a EC2-GW (la VPC real no tiene este equipo; CI-48)
    "wifi_gw": "172.16.0.1",                # fgt-sim en wifi-sim (CI-48)
    "byod01": "172.16.0.50",                # equipo personal de prueba en 172.16.0.0/16 [S-28] (CI-48)
    "labcli02": "10.20.32.2",               # PC de prueba dentro de LAB-01 (10.20.32.0/26): control positivo de T52 (CI-48)
    "labcli03": "10.20.32.130",             # PC de prueba dentro de LAB-03 (10.20.32.128/26), T52 (D5.3; CI-48)
    "dominio_portal": "portal.celeris.internal",
    "dominio_origen": "listado.example.com",    # dominio «listado» de T07: el nodo descifra su TLS
    "dominio_generico": "example.com",          # T14, T19, T24
    "dominio_grande": "descargas.example.com",  # T55: archivos grandes en origin-sim
    "dominio_panel": "panel.celeris.internal",  # EC2-GW (panel remoto): certificado de la CA de laboratorio
    "honey_url": "/admin-backup.zip",           # T31 (REQ-F-27): ruta señuelo de los nodos EDGE [S-17]
}
P = PARAMETROS_LAB

P = PARAMETROS_LAB

# nombre de nodo → (componente, zona, rol)
NODOS = {
    "jmp01": ("JMP01", "MGMT", "host"),
    "ctrl01": ("CTRL01", "SERVERS", "ctrl"),
    "labcli01": ("LABCLI01", "LAB", "host"),
    "enc01": ("ENC01", "LAB", "host"),
    "kali01": ("KALI01", "LAB", "host"),
    "hny02": ("HNY02", "LAB", "canary"),
    "portal01": ("PORTAL01", "DMZ-SVC", "portal"),
    "hny01": ("HNY01", "DMZ-HONEY", "host"),
    "edge01": ("EDGE01", "EDGE", "edge"),
    "edge02": ("EDGE02", "EDGE", "edge"),
    "siem01": ("SIEM01", "SECURITY", "siem"),
}
# PC de laboratorio de prueba que no están en el inventario (componente PCS-LAB es un grupo): nombre → (zona, parámetro con su IP)
CLIENTES_LAB = {"labcli02": ("LAB", "labcli02"), "labcli03": ("LAB", "labcli03")}

SIEM_IP_ZONA = "SECURITY"
# Zonas con puente. STORAGE (VLAN 70) no tiene interfaz en FW01: no hay gateway (D1.4) y solo la usan ESX01 y NAS01; BACKUP (VLAN 71) sí.
ZONAS_PUENTE = ["MGMT", "SERVERS", "LAB", "DMZ-SVC", "DMZ-HONEY", "SECURITY", "EDGE"]       # v0.4: 7 VLAN (CE03 D1.8)
ZONAS_FW01 = list(ZONAS_PUENTE)

def puente(x: Infra, zona: str) -> str:
    return f"br-vlan{x.zonas[zona]['vlan']}"


def _ip_de(x: Infra, comp: str, zona: str | None = None) -> str:
    ips = [i for i in x.componentes[comp]["ips"] if i["ip"] and (zona is None or i["zona"] == zona)]
    assert len(ips) == 1, f"{comp}: IP ambigua"
    return ips[0]["ip"]


def _pref(x: Infra, zona: str) -> int:
    return ipaddress.ip_network(x.zonas[zona]["cidr"]).prefixlen


def _gw(x: Infra, zona: str) -> str:
    return x.zonas[zona]["gateway"]


def _veth(nodo: str, sufijo: str) -> str:
    n = f"{nodo.replace('-sim', '')}-{sufijo}"
    assert len(n) <= 15, n
    return n


# ------------------------------------------------------------------------------------------------------------------
# Topología
# ------------------------------------------------------------------------------------------------------------------

def topologia(x: Infra) -> dict:
    nodes, links = {}, []
    for z in ZONAS_PUENTE:
        nodes[puente(x, z)] = {"kind": "bridge"}
    nodes["br-wan"] = {"kind": "bridge"}
    nodes["br-wifi"] = {"kind": "bridge"}

    def linux(nombre, imagen, ifaces, extra=None):
        d = {"kind": "linux", "image": imagen, "binds": [f"generated/{nombre}:/lab:ro", ".run/pki:/pki:ro"],
             "env": {"ESPERA_IFACES": " ".join(ifaces)}, "cap-add": ["NET_ADMIN", "NET_RAW", "SYS_ADMIN"]}
        d.update(extra or {})
        nodes[nombre] = d

    # fw01-sim: eth1 = WAN (red de tránsito hacia fgt-sim) + una interfaz por zona
    zf = ZONAS_FW01
    ifs = [f"eth{n}" for n in range(1, len(zf) + 2)]
    linux("fw01-sim", IMAGEN_BASE, ifs, {"sysctls": {"net.ipv4.ip_forward": 1, "net.ipv4.conf.all.rp_filter": 0}})
    for n, z in enumerate(zf, start=2):
        links.append({"endpoints": [f"fw01-sim:eth{n}", f"{puente(x, z)}:{_veth('fw01-sim', str(x.zonas[z]['vlan']))}"]})
    # fgt-sim (FortiGate emulado): eth1 tránsito (FW01), eth2 Internet (br-wan), eth3 Wi-Fi (br-wifi)
    linux("fgt-sim", IMAGEN_BASE, ["eth1", "eth2", "eth3"], {"sysctls": {"net.ipv4.ip_forward": 1, "net.ipv4.conf.all.rp_filter": 0}})
    links.append({"endpoints": ["fw01-sim:eth1", "fgt-sim:eth1"]})
    links.append({"endpoints": ["fgt-sim:eth2", f"br-wan:{_veth('fgt-sim', 'wan')}"]})
    links.append({"endpoints": ["fgt-sim:eth3", f"br-wifi:{_veth('fgt-sim', 'wifi')}"]})
    linux("byod01", IMAGEN_BASE, ["eth1"])
    links.append({"endpoints": ["byod01:eth1", f"br-wifi:{_veth('byod01', 'wifi')}"]})

    todos = {n: (zona, rol) for n, (comp, zona, rol) in NODOS.items()} | {n: (zona, "host") for n, (zona, _) in CLIENTES_LAB.items()}
    for nombre, (zona, rol) in todos.items():
        extra = {}
        imagen = IMAGEN_NODO if nombre in ("edge01", "edge02") else IMAGEN_BASE
        if nombre == "hny01":        # los registros de Cowrie (acompañante) los lee el agente de Wazuh de hny01
            extra = {"binds": [f"generated/{nombre}:/lab:ro", ".run/pki:/pki:ro", ".run/cowrie-log:/var/log/cowrie:ro"]}
        if nombre == "ctrl01":       # REQ-F-17: la consola de prueba publica aquí la configuración firmada (config.toml + config.toml.sig)
            extra = {"binds": [f"generated/{nombre}:/lab:ro", ".run/pki:/pki:ro", ".run/firmada:/firmada"]}
        if nombre in ("edge01", "edge02"):
            extra = {"binds": [f"generated/{nombre}:/lab:ro", ".run/pki:/pki:ro", ".run/firmada:/firmada:ro"]}
        linux(nombre, imagen, ["eth1"], extra)
        links.append({"endpoints": [f"{nombre}:eth1", f"{puente(x, zona)}:{_veth(nombre, str(x.zonas[zona]['vlan']))}"]})

    # Cowrie (SSH 2222, F24) comparte la red de hny01: su imagen oficial no trae shell para configurar interfaces
    nodes["hny01-cowrie"] = {"kind": "linux", "image": IMAGEN_COWRIE, "network-mode": "container:hny01",
                             "binds": [".run/cowrie-log:/cowrie/cowrie-git/var/log/cowrie"]}
    # Wazuh manager (SIEM01): comparte la red de siem01 porque su imagen no trae herramientas para configurarla. Config y reglas por montaje.
    nodes["siem01-wazuh"] = {"kind": "linux", "image": IMAGEN_WAZUH, "network-mode": "container:siem01",
                             "binds": [".run/wazuh/ossec.conf:/wazuh-config-mount/etc/ossec.conf:ro",
                                       "../siem/wazuh/local_rules.xml:/wazuh-config-mount/etc/rules/local_rules.xml:ro"]}

    # WAN simulada y nube emulada: ext01 y origin-sim en br-wan; vgw-sim en br-wan (IP de los túneles y de EC2-GW) y, por un enlace directo, gw-sim (EC2-GW)
    linux("ext01", IMAGEN_BASE, ["eth1"])
    links.append({"endpoints": ["ext01:eth1", f"br-wan:{_veth('ext01', 'wan')}"]})
    linux("origin-sim", IMAGEN_BASE, ["eth1"])
    links.append({"endpoints": ["origin-sim:eth1", f"br-wan:{_veth('origin-sim', 'wan')}"]})
    linux("vgw-sim", IMAGEN_BASE, ["eth1", "eth2"], {"sysctls": {"net.ipv4.ip_forward": 1, "net.ipv4.conf.all.rp_filter": 0}})
    links.append({"endpoints": ["vgw-sim:eth1", f"br-wan:{_veth('vgw-sim', 'wan')}"]})
    linux("gw-sim", IMAGEN_BASE, ["eth1"])
    links.append({"endpoints": ["vgw-sim:eth2", "gw-sim:eth1"]})
    # Red de gestión de containerlab: fuera de 172.16.0.0/12 bajo 172.17-172.24 (las usan otros proyectos de Docker) y de las redes del diseño (CI-24).
    return {"name": "celeris", "mgmt": {"network": "celeris-mgmt", "ipv4-subnet": "172.30.250.0/24"},
            "topology": {"nodes": nodes, "links": links}}


def topologia_yaml(x: Infra) -> str:
    cab = ("# GENERADO por infra/gen/lab.py desde infra/inventory.yaml — no editar a mano (make lab-gen).\n"
           "# Laboratorio EMULADO (Modo L, Parte F4): no es el producto real. Las IP de cada nodo están en lab/generated/<nodo>/arranque.sh.\n")
    return cab + yaml.safe_dump(topologia(x), sort_keys=False, allow_unicode=True, width=200)


# ------------------------------------------------------------------------------------------------------------------
# Configuración de cada nodo
# ------------------------------------------------------------------------------------------------------------------

def _resolv(x: Infra, zona: str) -> str:
    """v0.4 (D-28): el único resolvedor es Unbound en FW01, en la interfaz .1 de cada VLAN."""
    return f"printf 'nameserver {_gw(x, zona)}\\n' > /etc/resolv.conf"


def _red_host(x: Infra, comp: str | None, zona: str, iface: str = "eth1", ip: str | None = None) -> list[str]:
    return [f"ip link set {iface} up", f"ip addr add {ip or _ip_de(x, comp, zona)}/{_pref(x, zona)} dev {iface}",
            f"ip route replace default via {_gw(x, zona)}", _resolv(x, zona)]


def _zona_dns(x: Infra) -> str:
    """Zona DNS interna del laboratorio: nombres del inventario y nombres de prueba (CI-24)."""
    pac_host = x.inv["servicios_base"]["pac"]["url"].split("/")[2]
    lineas = ["server:"]
    for r in x.inv["servicios_base"]["pac"]["registros_a"]:
        lineas.append(f'  local-data: "{pac_host}. A {r["ip"]}"')
    lineas.append(f'  local-data: "{P["dominio_portal"]}. A {_ip_de(x, "PORTAL01")}"')
    for d in (P["dominio_origen"], P["dominio_generico"]):
        lineas.append(f'  local-zone: "{d}." redirect')
        lineas.append(f'  local-data: "{d}. A {P["ext01"]}"')
    lineas.append(f'  local-zone: "{P["dominio_grande"]}." redirect')
    lineas.append(f'  local-data: "{P["dominio_grande"]}. A {P["origin_sim"]}"')
    return "\n".join(lineas) + "\n"


def _unbound(x: Infra, interfaces: list[str]) -> str:
    redes = [str(n) for n in sorted({ipaddress.ip_network(s["cidr"]) for s in x.inv["supernets"] if s["id"] in ("CAMPUS-RESUMEN",)})]
    cab = "server:\n  verbosity: 1\n  do-ip6: no\n  do-udp: yes\n  do-tcp: yes\n  username: \"\"\n  chroot: \"\"\n  pidfile: \"/run/unbound.pid\"\n"
    cab += "".join(f"  interface: {i}\n" for i in interfaces)
    cab += "".join(f"  access-control: {r} allow\n" for r in redes)
    cab += "  access-control: 127.0.0.0/8 allow\n  val-permissive-mode: yes\n  logfile: \"\"\n  use-syslog: no\n"
    return cab + _zona_dns(x).replace("server:\n", "", 1)


def _html_aviso(md_path: Path) -> str:
    """AVISO.md → HTML mínimo (títulos, listas, párrafos, énfasis). Sin dependencias; el sitio es estático (REQ-F-30)."""
    import html
    texto = md_path.read_text(encoding="utf-8")
    out, en_lista = [], False
    def inline(t):
        t = html.escape(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
        return t
    for linea in texto.splitlines():
        m = re.match(r"^(#{1,4})\s+(.*)", linea)
        if m:
            if en_lista:
                out.append("</ul>"); en_lista = False
            n = len(m.group(1)); out.append(f"<h{n}>{inline(m.group(2))}</h{n}>")
        elif re.match(r"^\s*[-*]\s+", linea):
            if not en_lista:
                out.append("<ul>"); en_lista = True
            out.append(f"<li>{inline(re.sub(r'^\s*[-*]\s+', '', linea))}</li>")
        elif linea.strip():
            if en_lista:
                out.append("</ul>"); en_lista = False
            out.append(f"<p>{inline(linea)}</p>")
    if en_lista:
        out.append("</ul>")
    titulo = html.escape(next((l.lstrip("# ").strip() for l in texto.splitlines() if l.startswith("#")), "Aviso de transparencia"))
    return (f'<!doctype html>\n<html lang="es"><head><meta charset="utf-8"><title>{titulo}</title>'
            '<meta name="viewport" content="width=device-width,initial-scale=1"></head><body>\n' + "\n".join(out) + "\n</body></html>\n")


CAB_APP = ("add_header Content-Security-Policy \"default-src 'self'; frame-ancestors 'none'\" always;\n"
           "    add_header X-Content-Type-Options nosniff always;\n"
           "    add_header Referrer-Policy no-referrer always;\n")      # D1.9: cabeceras de la aplicación (WEB01)
CAB_WAF = ("add_header Strict-Transport-Security \"max-age=31536000; includeSubDomains\" always;\n"
           "    proxy_hide_header Strict-Transport-Security;\n")           # D1.9: HSTS en el borde TLS (WAF01), una sola vez


def _nginx_portal(x: Infra) -> str:
    """PORTAL01 (D-28): WAF y sitio estático firmado en una sola VM. nginx + ModSecurity + OWASP CRS (equivalente funcional de Caddy + Coraza)."""
    return f"""{cabecera('#')}user www-data;
worker_processes 1;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;
events {{ worker_connections 256; }}
http {{
  access_log /var/log/nginx/access.log;
  error_log /var/log/nginx/error.log warn;
  limit_req_zone $binary_remote_addr zone=porip:10m rate=20r/s;
  modsecurity on;
  modsecurity_rules_file /etc/modsecurity/lab-main.conf;
  server {{
    listen 80;
    location /.well-known/acme-challenge/ {{ return 404; }}
    location / {{ return 301 https://$host$request_uri; }}
  }}
  server {{
    listen 443 ssl;
    server_name {P['dominio_portal']};
    ssl_certificate /pki/portal.pem;
    ssl_certificate_key /pki/portal.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_session_tickets off;
    server_tokens off;
    {CAB_WAF}    {CAB_APP}    limit_req zone=porip burst=40 nodelay;
    root /lab/web;
    location / {{ try_files $uri /index.html; }}
  }}
}}
"""


def _modsec_main() -> str:
    return """# Reglas del WAF de laboratorio: ModSecurity en modo bloqueo + OWASP CRS (equivalente funcional de Caddy + Coraza, F4.2)
Include /etc/nginx/modsecurity.conf
SecRuleEngine On
SecAuditEngine RelevantOnly
SecAuditLog /var/log/modsec_audit.log
SecAuditLogFormat JSON
Include /etc/modsecurity/crs/crs-setup.conf
Include /usr/share/modsecurity-crs/rules/*.conf
"""


def _nginx_gw(x: Infra) -> str:
    """gw-sim (EC2-GW emulado): termina TLS con el certificado de la CA de laboratorio, aplica ModSecurity + CRS y reenvía solo a CTRL01:443
    con su certificado de cliente (F30, mTLS dentro de IPsec). Equivalente funcional de Caddy + Coraza (la imagen base no los trae)."""
    ctrl = _ip_de(x, "CTRL01")
    return f"""{cabecera('#')}user www-data;
worker_processes 1;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;
events {{ worker_connections 256; }}
http {{
  access_log /var/log/nginx/access.log;
  error_log /var/log/nginx/error.log warn;
  limit_req_zone $binary_remote_addr zone=porip:10m rate=10r/s;
  modsecurity on;
  modsecurity_rules_file /etc/modsecurity/lab-main.conf;
  server {{
    listen 443 ssl;
    server_name {P['dominio_panel']};
    ssl_certificate /pki/gw-sim-servidor.pem;
    ssl_certificate_key /pki/gw-sim-servidor.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    server_tokens off;
    {CAB_WAF}    limit_req zone=porip burst=20 nodelay;
    location / {{
      proxy_pass https://{ctrl}:443;
      proxy_ssl_certificate /pki/gw-sim.pem;
      proxy_ssl_certificate_key /pki/gw-sim.key;
      proxy_ssl_trusted_certificate /pki/ca.pem;
      proxy_ssl_verify on;
      proxy_ssl_name ctrl01;
      proxy_set_header Host $host;
      proxy_set_header X-Origen-Sesion remoto;
    }}
  }}
}}
"""


def _nginx_pac(ip: str) -> str:
    return f"""{cabecera('#')}user www-data;
worker_processes 1;
pid /run/nginx-pac.pid;
events {{ worker_connections 64; }}
http {{
  access_log /var/log/nginx/pac.log;
  types {{ application/x-ns-proxy-autoconfig dat; }}
  server {{ listen {ip}:80; root /lab/pac; location = /wpad.dat {{ default_type application/x-ns-proxy-autoconfig; }} }}
}}
"""


def _chrony(x: Infra) -> str:
    return (f"{cabecera('#')}# Lab: NTP de FW01 (D-28) sin sincronización hacia arriba (F25 NTS no se emula); sirve la hora local a las zonas (F2).\n"
            "local stratum 10\nrtcsync\nmakestep 1 3\n" + "".join(f"allow {s['cidr']}\n" for s in x.inv["supernets"] if s["id"] == "CAMPUS-RESUMEN")
            + "driftfile /run/chrony.drift\n")


def _clientes_permitidos(x: Infra) -> list[str]:
    """allowed_clients (REQ-F-10, REQ-F-32): los rangos /26 HABILITADOS de rangos_lab, el rango de infraestructura de LAB (ENC01, LABCLI01, KALI01)
    y, para F31, la red del Wi-Fi (el nodo la trata siempre en passthrough: byod_networks)."""
    rl = x.inv["rangos_lab"]
    redes = [l["cidr"] for l in rl["laboratorios"] if l["habilitado"]] + [rl["infraestructura"]["cidr"]]
    return redes + [x.zonas["WIFI-EST"]["cidr"]]


def _config_edge(x: Infra, nodo: str) -> str:
    comp, zona, _ = NODOS[nodo]
    f1 = x.flujos["F1"]
    puerto = f1["protocolos"][0]["puertos"][0]
    admin = next(p for pr in x.flujos["F20"]["protocolos"] for p in pr["puertos"] if p == 9128)
    ip = _ip_de(x, comp)
    nodos_pac = [f"{n[1]}:{n[2]}" for n in pac.nodos_proxy(x)]
    directas = [f"{n}" for n in pac.redes_internas(x)]
    pac_host = x.inv["servicios_base"]["pac"]["url"].split("/")[2]
    byod = [x.zonas["WIFI-EST"]["cidr"]]
    return (f'{cabecera("#")}listen = "{ip}:{puerto}"\n'
            f"allowed_clients = {_clientes_permitidos(x)!r}\n".replace("'", '"') +
            f'byod_networks = {byod!r}\n'.replace("'", '"') +        # REQ-F-36: el nodo nunca descifra esta red (etapa 3)
            f'operator_contact = "redes@example.invalid"\ndata_dir = "/data/store"\nca_cert = "/data/ca/celeris-ca.crt"\nca_key = "/data/ca/celeris-ca.key"\n'
            f'intercept_domains = ["{P["dominio_origen"]}", "{P["dominio_grande"]}"]\nupstream_extra_ca = ["/pki/ca.pem"]\n'
            f'admin_listen = "{ip}:{admin}"\nadmin_token_file = "/data/admin.token"\n'
            # REQ-NF-14: el puerto de administración solo por TLS (certificado autofirmado de laboratorio, generado por el nodo al arrancar)
            'admin_tls = true\nadmin_tls_cert = "/data/ca/admin-tls.crt"\nadmin_tls_key = "/data/ca/admin-tls.key"\n'
            'security_log_enabled = true\nsecurity_log_dir = "/data/logs"\n'
            # T55: objetos de hasta 200 MiB, espera de coalescencia de 30 s y 3 GiB de memoria para servir (por defecto 64 MiB, 10 s y 512 MiB: un instalador de 100 MB no se guardaría y 20 clientes agotarían la memoria)
            'max_object_bytes = 209715200\ncoalesce_wait_secs = 30\nmax_buffered_bytes = 3221225472\n'
            # REQ-F-27: ruta señuelo de laboratorio [S-17]
            f'honey_urls = ["{P["honey_url"]}"]\n'
            # REQ-F-17: el nodo recarga la configuración que la consola de prueba firma (ctrl01); la llave pública queda fijada aquí, en el arranque
            'signed_config = "/firmada/config.toml"\nconfig_public_key = "/pki/config-firma.pub"\nconfig_reload_secs = 5\n'
            # REQ-F-26: el PAC lo genera el binario desde estos valores (`celeris-cache pac`); nginx lo sirve por F3
            f'pac_nodes = {nodos_pac!r}\npac_direct_networks = {directas!r}\npac_host = "{pac_host}"\n'.replace("'", '"'))



def _suricata(ifaces: list[str], reglas: str) -> str:
    af = "".join(f"  - interface: {i}\n" for i in ifaces)
    return f"""%YAML 1.1
---
vars:
  address-groups: {{ HOME_NET: "[10.20.0.0/14,10.30.0.0/16]", EXTERNAL_NET: "!$HOME_NET" }}
  port-groups: {{ HTTP_PORTS: "80" }}
default-log-dir: /var/log/suricata
outputs:
  - eve-log: {{ enabled: yes, filetype: regular, filename: eve.json, types: [alert, anomaly] }}
af-packet:
{af}rule-files: [{reglas}]
classification-file: /etc/suricata/classification.config
reference-config-file: /etc/suricata/reference.config
"""


REGLAS_SURICATA = """# Reglas locales del laboratorio (no sustituyen a ET Open: no hay Internet en el Modo L).
alert tcp any any -> any any (msg:"LAB escaneo SYN de un origen"; flags:S,12; threshold: type threshold, track by_src, count 30, seconds 5; classtype:attempted-recon; sid:9000001; rev:1;)
alert tcp any any -> any [22,23] (msg:"LAB intento de acceso SSH/Telnet"; flags:S; threshold: type threshold, track by_src, count 5, seconds 30; classtype:attempted-admin; sid:9000002; rev:1;)
"""

SFTP_SIM_PY = """#!/usr/bin/env python3
# EMULADO (CE03 D5.3, CI-52): no es OpenSSH ni SFTP; solo abre TCP 22 con un banner SSH para comprobar que F33 abre.
import socket, sys
s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind((sys.argv[1], int(sys.argv[2]))); s.listen(8)
while True:
    c, _ = s.accept()
    try: c.sendall(b"SSH-2.0-celeris-lab-sftp-emulado\\r\\n")
    except Exception: pass
    c.close()
"""


CANARIO_PY = '''#!/usr/bin/env python3
"""Canario interno del laboratorio (equivalente funcional de OpenCanary, F4.2): cualquier conexión a sus puertos es una alerta."""
import json, socket, sys, threading, time
IP, PUERTOS = sys.argv[1], [int(p) for p in sys.argv[2].split(",")]
def escuchar(p):
    s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind((IP, p)); s.listen(16)
    while True:
        c, a = s.accept()
        with open("/var/log/canary.json", "a") as f:
            f.write(json.dumps({"t": time.time(), "evento": "conexion", "puerto": p, "origen": a[0]}) + "\\n")
        c.close()
for p in PUERTOS:
    threading.Thread(target=escuchar, args=(p,), daemon=True).start()
threading.Event().wait()
'''

ORIGEN_PY = '''#!/usr/bin/env python3
"""Origen web de prueba del laboratorio (ext01): HTTP 80 y HTTPS 443, contenido cacheable (Cache-Control public)."""
import http.server, json, ssl, sys, threading
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/echo"):        # T26 (REQ-F-28): devuelve las cabeceras tal como llegaron al origen
            cuerpo = json.dumps({k.lower(): v for k, v in self.headers.items()}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(cuerpo))); self.end_headers(); self.wfile.write(cuerpo); return
        cuerpo = ("origen " + self.headers.get("Host", "?") + " " + self.path + "\\n").encode() + b"x" * 2048
        self.send_response(200); self.send_header("Content-Type", "text/plain"); self.send_header("Alt-Svc", 'h3=":443"; ma=3600')
        self.send_header("Cache-Control", "public, max-age=3600"); self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers(); self.wfile.write(cuerpo)
    def log_message(self, *a): sys.stderr.write("origen %s %s\\n" % (self.client_address[0], self.requestline))
def srv(puerto, tls):
    s = http.server.ThreadingHTTPServer(("0.0.0.0", puerto), H)
    if tls:
        c = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); c.load_cert_chain("/pki/origen.pem", "/pki/origen.key")
        s.socket = c.wrap_socket(s.socket, server_side=True)
    s.serve_forever()
threading.Thread(target=srv, args=(80, False), daemon=True).start()
srv(443, True)
'''


ORIGIN_SIM_PY = '''#!/usr/bin/env python3
"""origin-sim (D5.3): origen de Internet de laboratorio con archivos de 100 MB a 1 GB, generados al vuelo (sin disco). Cada GET completo queda en el registro
(T55 cuenta cuántas descargas llegan al origen). Cacheable: Cache-Control public."""
import http.server, sys, threading, time
TAM = {"/archivo-100MB.bin": 100 << 20, "/archivo-500MB.bin": 500 << 20, "/archivo-1GB.bin": 1 << 30}
class H(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def do_GET(self):
        n = TAM.get(self.path.split("?")[0])
        if n is None:
            cuerpo = b"origin-sim\\n"
            self.send_response(200); self.send_header("Content-Length", str(len(cuerpo))); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(cuerpo); return
        sys.stderr.write("origin-sim DESCARGA %s %s %s\\n" % (time.time(), self.client_address[0], self.path)); sys.stderr.flush()
        self.send_response(200); self.send_header("Content-Type", "application/octet-stream"); self.send_header("Content-Length", str(n))
        self.send_header("Cache-Control", "public, max-age=3600"); self.send_header("ETag", '"sim-%d"' % n); self.end_headers()
        trozo = b"\\0" * (1 << 20); resto = n
        try:
            while resto > 0:
                self.wfile.write(trozo[:min(len(trozo), resto)]); resto -= len(trozo)
                time.sleep(0.002)          # ≈ 500 MB/s como máximo: el origen es lento a propósito, para que la coalescencia sea observable
        except (BrokenPipeError, ConnectionResetError):
            pass
    def log_message(self, *a): pass
http.server.ThreadingHTTPServer(("0.0.0.0", 80), H).serve_forever()
'''

CONSOLA_PY = '''#!/usr/bin/env python3
"""Consola de prueba (ctrl01, D5.3): HTTPS en 443 con certificado de servidor. Una sesión con certificado de cliente de gw-sim (F30) se marca `remoto`
(REQ-F-37); la que llega directo (ENC01, F28) se marca `campus`. Las acciones críticas (POST /aprobar) se rechazan con 403 si la sesión es remota.
No es la consola de CE02: sirve para probar el diseño de red y la firma de la configuración (etapa 3)."""
import http.server, json, ssl, sys
class H(http.server.BaseHTTPRequestHandler):
    def _origen(self):
        return "remoto" if self.headers.get("X-Origen-Sesion") == "remoto" or self.connection.getpeercert() else "campus"
    def _resp(self, cod, obj):
        cuerpo = json.dumps(obj).encode(); self.send_response(cod); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo))); self.end_headers(); self.wfile.write(cuerpo)
    def do_GET(self):
        self._resp(200, {"consola": "laboratorio (emulada)", "origen": self._origen()})
    def do_POST(self):
        if self.path.startswith("/aprobar") and self._origen() == "remoto":
            sys.stderr.write("ACCION_CRITICA_REMOTA rechazada %s\\n" % self.path); sys.stderr.flush()
            self._resp(403, {"error": "acción crítica solo desde el campus (REQ-F-37)"}); return
        self._resp(200, {"aceptada": self.path, "origen": self._origen()})
    def log_message(self, *a): sys.stderr.write("consola %s %s\\n" % (self.client_address[0], self.requestline))
c = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); c.load_cert_chain("/pki/ctrl01.pem", "/pki/ctrl01.key")
c.load_verify_locations("/pki/nodos-ca.pem"); c.verify_mode = ssl.CERT_OPTIONAL
srv = http.server.ThreadingHTTPServer(("0.0.0.0", 443), H); srv.socket = c.wrap_socket(srv.socket, server_side=True); srv.serve_forever()
'''


FIRMAR_SH = """#!/bin/sh
# Ayudante de laboratorio de ctrl01 (REQ-F-17): firma con ed25519 la configuración que llega por la entrada estándar y la publica en /firmada.
# Uso: firmar.sh < config.toml        La llave privada (/pki/config-firma.key) es de laboratorio y se genera en cada equipo; no está en el repositorio.
set -eu
tmp=/firmada/.config.toml.nuevo
cat > "$tmp"
openssl pkeyutl -sign -inkey /pki/config-firma.key -rawin -in "$tmp" | od -An -tx1 | tr -d ' \\n' > /firmada/config.toml.sig.nuevo
mv "$tmp" /firmada/config.toml
mv /firmada/config.toml.sig.nuevo /firmada/config.toml.sig
"""


def _arranque_fw(x: Infra) -> str:
    fw = fw01_interfaces(x)
    L = ["#!/bin/sh", cabecera("#").rstrip(), "set -u", "mount -o remount,rw /proc/sys 2>/dev/null || true",
         "sysctl -qw net.ipv4.ip_forward=1 net.ipv4.conf.all.rp_filter=0 net.ipv4.conf.default.rp_filter=0 || true"]
    orden = ["PERIMETRO"] + ZONAS_FW01       # «PERIMETRO» es la WAN de FW01, que en la v0.4 está en la red de tránsito (TRANSITO)
    for n, zona in enumerate(orden, start=1):
        nombre = fw[zona]["interfaz"]
        L += [f"ip link set eth{n} down", f"ip link set eth{n} name {nombre}", f"ip link set {nombre} up"]
        pref = _pref(x, zona) if zona != "PERIMETRO" else _pref(x, "TRANSITO")
        L.append(f"ip addr add {fw[zona]['ip']}/{pref} dev {nombre}")
    fgt = _ip_de(x, "FGT-EXT", "TRANSITO")
    L += [f"# Ruta por defecto hacia el FortiGate (D1.8): {fgt}", f"ip route replace default via {fgt}"]
    L += ["# VPN: interfaces VTI, charon (strongSwan) y FRR (BGP)", "sh /lab/vti-up.sh",
          "mkdir -p /etc/swanctl /run/frr", "cp /lab/swanctl.conf /etc/swanctl/swanctl.conf", "cp /lab/psk-fw01.conf /etc/swanctl/psk-fw01.conf 2>/dev/null || cp /pki/psk-fw01.conf /etc/swanctl/psk-fw01.conf",
          "cp /lab/strongswan.conf /etc/strongswan.conf", "/usr/lib/ipsec/charon > /var/log/charon.log 2>&1 &",
          "for i in 1 2 3 4 5 6 7 8 9 10; do [ -S /var/run/charon.vici ] && break; sleep 0.5; done", "swanctl --load-all --noprompt > /var/log/swanctl-load.log 2>&1",
          "cp /lab/frr.conf /etc/frr/frr.conf", "chown frr:frr /etc/frr/frr.conf /run/frr; chmod 640 /etc/frr/frr.conf",
          "sed -i 's/^bgpd=no/bgpd=yes/; s/^staticd=no/staticd=yes/' /etc/frr/daemons", "/usr/lib/frr/frrinit.sh start > /var/log/frr-start.log 2>&1",
          "# DNS (Unbound con DNSSEC en .1 de cada VLAN) y NTP de FW01 (D-28), reglas y detección (Suricata IDS en LAB y SERVERS, DET-02)",
          "unbound -c /lab/unbound.conf &", "chronyd -f /lab/chrony.conf -x &", "nft -f /lab/fw01sim.nft",
          "nohup suricata --af-packet -c /lab/suricata.yaml > /var/log/suricata.out 2>&1 &",
          "sh /lab/crowdsec.sh &", "sh /lab/eve-a-siem.sh &", "touch /run/lab-listo", ""]
    return "\n".join(L)


def _eve_a_siem(x: Infra) -> str:
    """F14: los eventos de Suricata de FW01 viajan al SIEM por syslog sobre TLS (6514), no por un agente (F13 no incluye a FW01)."""
    siem = _ip_de(x, "SIEM01")
    return "\n".join(["#!/bin/sh", cabecera("#").rstrip(), "# EVE de Suricata → SIEM01 por syslog TLS (F14, TCP 6514). Reintenta mientras el SIEM arranca.",
                      "mkdir -p /var/log/suricata; touch /var/log/suricata/eve.json",
                      f"while true; do tail -n0 -F /var/log/suricata/eve.json | socat - OPENSSL:{siem}:6514,verify=0 2>/dev/null; sleep 3; done", ""])


def _arranque_fgt(x: Infra) -> str:
    """fgt-sim (FortiGate emulado, D5.3): NAT 1:1 de la IP pública hacia la WAN de FW01 solo para UDP 500/4500 y TCP 80/443; ruta al Wi-Fi.
    Sin FortiGuard ni inspección SSL: la exclusión de EDGE01/02 de esa inspección [S-29] no se puede emular."""
    wan_fw = x.inv["vpn"]["extremo_onpremise"]["ip_interna"]
    t = ipaddress.ip_network(x.zonas["TRANSITO"]["cidr"])
    sede = x.inv["supernets"][0]["cidr"]
    pub = P["fgt_wan"]
    return "\n".join(["#!/bin/sh", cabecera("#").rstrip(), "set -u", "mount -o remount,rw /proc/sys 2>/dev/null || true",
        "sysctl -qw net.ipv4.ip_forward=1 net.ipv4.conf.all.rp_filter=0 net.ipv4.conf.default.rp_filter=0 || true",
        f"ip link set eth1 up", f"ip addr add {x.zonas['TRANSITO']['gateway']}/{t.prefixlen} dev eth1          # tránsito: FortiGate .1 [S-29]",
        f"ip link set eth2 up", f"ip addr add {pub}/{ipaddress.ip_network(P['wan_red']).prefixlen} dev eth2         # IP pública del laboratorio (sustituye a 203.0.113.10)",
        f"ip link set eth3 up", f"ip addr add {P['wifi_gw']}/{ipaddress.ip_network(x.zonas['WIFI-EST']['cidr']).prefixlen} dev eth3         # Wi-Fi de estudiantes [S-28]",
        f"# Ruta estática al campus vía FW01 (devuelve el tráfico del Wi-Fi hacia EDGE y PORTAL01) [S-29]", f"ip route replace {sede} via {wan_fw}",
        "nft -f /lab/fgt.nft", "touch /run/lab-listo", ""])


def _nft_fgt(x: Infra) -> str:
    wan_fw = x.inv["vpn"]["extremo_onpremise"]["ip_interna"]
    pub = P["fgt_wan"]
    sede = x.inv["supernets"][0]["cidr"]
    return f"""{cabecera('#')}flush ruleset
table ip fgt {{
  chain prerouting {{
    type nat hook prerouting priority dstnat; policy accept;
    # NAT 1:1 (D1.8, D-26): solo IPsec con NAT-T y el portal; el resto de la IP pública no se publica
    iifname "eth2" ip daddr {pub} udp dport {{ 500, 4500 }} counter dnat to {wan_fw} comment "NAT 1:1 IPsec NAT-T"
    iifname "eth2" ip daddr {pub} tcp dport {{ 80, 443 }} counter dnat to {wan_fw} comment "NAT 1:1 portal (F21)"
  }}
  # Ventana autorizada de F24 (señuelo): vacía; T11 agrega ahí TCP 22 y 23 mientras dura (CI-49)
  chain ventana {{
    type nat hook prerouting priority dstnat; policy accept;
  }}
  chain postrouting {{
    type nat hook postrouting priority srcnat; policy accept;
    oifname "eth2" ip saddr {sede} counter snat to {pub} comment "campus hacia Internet con la IP pública (F8, F18, VPN)"
    oifname "eth2" ip saddr {x.zonas['WIFI-EST']['cidr']} counter snat to {pub} comment "Wi-Fi de estudiantes hacia Internet, como hoy"
  }}
}}
table ip filter {{
  chain forward {{
    type filter hook forward priority 0; policy accept;
    counter comment "FortiGate emulado: sin FortiGuard (D5.3)"
  }}
}}
"""


def _crowdsec_sh() -> str:
    return "\n".join(["#!/bin/sh", cabecera("#").rstrip(), "# CrowdSec (DET-08) en modo local: API de bucle local y bouncer de nftables; sin conexión a la nube de CrowdSec. Clave del bouncer generada al arrancar.",
        "set -u", "mkdir -p /etc/crowdsec/bouncers /var/lib/crowdsec/data /var/log/crowdsec; touch /var/log/fw01-auth.log",
        "printf 'filenames:%s  - /var/log/fw01-auth.log%slabels:%s  type: syslog%s' '\n' '\n' '\n' '\n' > /etc/crowdsec/acquis.yaml",
        "rm -rf /etc/crowdsec/acquis.d", "mkdir -p /etc/crowdsec/hub; [ -s /etc/crowdsec/hub/.index.json ] || echo '{}' > /etc/crowdsec/hub/.index.json", "sed -i '/online_client:/,+1d' /etc/crowdsec/config.yaml",
        "[ -s /etc/crowdsec/local_api_credentials.yaml ] || cscli machines add --auto > /var/log/crowdsec-machine.log 2>&1",
        "crowdsec -no-cs > /var/log/crowdsec.out 2>&1 &",
        "for i in $(seq 1 90); do cscli lapi status >/dev/null 2>&1 && break; sleep 1; done",
        "cscli bouncers delete fw01-bouncer >/dev/null 2>&1; CLAVE=$(cscli bouncers add fw01-bouncer -o raw 2>/dev/null)",
        "printf 'mode: nftables\nupdate_frequency: 2s\nlog_mode: stdout\napi_url: http://127.0.0.1:8080/\napi_key: %s\ndisable_ipv6: true\ndeny_action: DROP\ndeny_log: false\nsupported_decisions_types:\n  - ban\nblacklists_ipv4: crowdsec-blacklists\nnftables:\n  ipv4:\n    enabled: true\n    set-only: false\n    table: crowdsec\n    chain: crowdsec-chain\n    priority: -10\nnftables_hooks:\n  - input\n  - forward\n' \"$CLAVE\" > /etc/crowdsec/bouncers/crowdsec-firewall-bouncer.yaml",
        "crowdsec-firewall-bouncer -c /etc/crowdsec/bouncers/crowdsec-firewall-bouncer.yaml > /var/log/crowdsec-bouncer.out 2>&1 &", ""])


def _arranque_vgw(x: Infra) -> str:
    L = ["#!/bin/sh", cabecera("#").rstrip(), "set -u", "mount -o remount,rw /proc/sys 2>/dev/null || true",
         "sysctl -qw net.ipv4.ip_forward=1 net.ipv4.conf.all.rp_filter=0 net.ipv4.conf.default.rp_filter=0 || true",
         "ip link set eth1 up"]
    L += [f"ip addr add {p}/{ipaddress.ip_network(P['wan_red']).prefixlen} dev eth1" for p in P["aws_peers"]]
    L += [f"ip addr add {P['gw_publica']}/{ipaddress.ip_network(P['wan_red']).prefixlen} dev eth1     # IP pública de EC2-GW (la asigna AWS)"]
    vpc = x.componentes["AWS-VPC"]["cidr"]
    gw = _ip_de(x, "EC2-GW")
    # Internet Gateway emulado: F29 entra por la IP pública de EC2-GW (443); lo que sale de la VPC hacia «Internet» lo hace con la IP de vgw-sim.
    L += ["nft add table ip nat", "nft 'add chain ip nat pre { type nat hook prerouting priority dstnat ; }'", "nft 'add chain ip nat post { type nat hook postrouting priority srcnat ; }'",
          f"nft add rule ip nat pre iifname eth1 ip daddr {P['gw_publica']} tcp dport 443 dnat to {gw}",
          f"nft add rule ip nat post ip saddr {vpc} oifname eth1 masquerade"]
    L += ["ip link set eth2 up", f"ip addr add {P['vgw_lan']}/{ipaddress.ip_network(x.componentes['AWS-PUB-A']['cidr']).prefixlen} dev eth2",
          "sh /lab/vti-up.sh", "mkdir -p /etc/swanctl /run/frr", "cp /lab/swanctl.conf /etc/swanctl/swanctl.conf",
          "cp /pki/psk-vgw.conf /etc/swanctl/psk-vgw.conf", "cp /lab/strongswan.conf /etc/strongswan.conf",
          "/usr/lib/ipsec/charon > /var/log/charon.log 2>&1 &", "for i in 1 2 3 4 5 6 7 8 9 10; do [ -S /var/run/charon.vici ] && break; sleep 0.5; done",
          "swanctl --load-all --noprompt > /var/log/swanctl-load.log 2>&1", "cp /lab/frr.conf /etc/frr/frr.conf",
          "chown frr:frr /etc/frr/frr.conf /run/frr; chmod 640 /etc/frr/frr.conf", "sed -i 's/^bgpd=no/bgpd=yes/; s/^staticd=no/staticd=yes/' /etc/frr/daemons",
          "/usr/lib/frr/frrinit.sh start > /var/log/frr-start.log 2>&1", "touch /run/lab-listo", ""]
    return "\n".join(L)


AGENTES = {   # nodo → archivos JSON que su agente de Wazuh lee (F13: CTRL01, EDGE01/02, PORTAL01, HNY01, HNY02, EC2-GW)
    "portal01": ["/var/log/modsec_audit.log"], "hny01": ["/var/log/cowrie/cowrie.json"], "hny02": ["/var/log/canary.json"],
    "edge01": ["/data/logs/security-*.jsonl"], "edge02": ["/data/logs/security-*.jsonl"], "ctrl01": ["/var/log/consola.log"],
    "gw-sim": ["/var/log/modsec_audit.log"],
}

def _agente_sh(x: Infra, nodo: str) -> str:
    """Enrola el agente de Wazuh del nodo en siem01 (F13: 1515 para el alta y 1514 para los eventos) y le indica sus archivos."""
    siem = _ip_de(x, "SIEM01")
    nombre = nodo.upper()
    localfiles = "".join(f"<localfile><log_format>json</log_format><location>{ruta}</location></localfile>" for ruta in AGENTES[nodo])
    return "\n".join([
        "#!/bin/sh", cabecera("#").rstrip(), "# Agente de Wazuh: espera al manager, se enrola y lee los archivos del nodo. Corre en segundo plano.",
        f"for i in $(seq 1 180); do nc -z -w1 {siem} 1515 && break; sleep 1; done",
        f"sed -i 's|<address>.*</address>|<address>{siem}</address>|' /var/ossec/etc/ossec.conf",
        f"sed -i ':a;N;$!ba;s|\\(.*\\)</ossec_config>|\\1{localfiles}</ossec_config>|' /var/ossec/etc/ossec.conf" if localfiles else ":",
        f"for i in 1 2 3 4 5; do /var/ossec/bin/agent-auth -m {siem} -A {nombre} && break; sleep 3; done > /var/log/agent-auth.log 2>&1",
        "/var/ossec/bin/wazuh-control start > /var/log/wazuh-agent.log 2>&1", ""])


def archivos_nodo(x: Infra, nodo: str, aviso_md: Path) -> dict[str, str]:
    """Contenido de lab/generated/<nodo>/: {nombre de archivo: texto}."""
    pac_txt = pac.generar(x)
    if nodo == "fw01-sim":
        fw = fw01_interfaces(x)
        ifaces_dns = [fw[z]["ip"] for z in ZONAS_FW01]
        aws = P["aws_peers"]
        # DET-02 (D1.14): Suricata de FW01 como IDS en las interfaces LAB y SERVERS, y en la WAN (tránsito); el IPS inline no se emula
        vigiladas = [fw[z]["interfaz"] for z in ("PERIMETRO", "LAB", "SERVERS")]
        return {
            "arranque.sh": _arranque_fw(x),
            "fw01sim.nft": nftables.generar(x, modo="piloto", ventana=False, aws_peers=aws),
            "swanctl.conf": vpn.swanctl(x, "fw01", aws, P["fgt_wan"]),
            "frr.conf": vpn.frr(x, "fw01"),
            "vti-up.sh": vpn.vti_up(x, "fw01", aws, P["fgt_wan"]),
            "strongswan.conf": vpn.strongswan_conf(),
            "unbound.conf": _unbound(x, ifaces_dns),
            "chrony.conf": _chrony(x),
            "suricata.yaml": _suricata(vigiladas, "/lab/local.rules"),
            "local.rules": REGLAS_SURICATA,
            "crowdsec.sh": _crowdsec_sh(),
            "eve-a-siem.sh": _eve_a_siem(x),
        }
    if nodo == "fgt-sim":
        return {"arranque.sh": _arranque_fgt(x), "fgt.nft": _nft_fgt(x)}
    if nodo == "vgw-sim":
        aws = P["aws_peers"]
        return {"arranque.sh": _arranque_vgw(x), "swanctl.conf": vpn.swanctl(x, "vgw", aws, P["fgt_wan"]), "frr.conf": vpn.frr(x, "vgw"),
                "vti-up.sh": vpn.vti_up(x, "vgw", aws, P["fgt_wan"]), "strongswan.conf": vpn.strongswan_conf()}
    if nodo == "ext01":
        return {"arranque.sh": "\n".join(["#!/bin/sh", cabecera("#").rstrip(), "ip link set eth1 up", f"ip addr add {P['ext01']}/{ipaddress.ip_network(P['wan_red']).prefixlen} dev eth1",
                                          f"ip route replace {x.inv['supernets'][0]['cidr']} via {P['fgt_wan']}", "python3 /lab/origen.py > /var/log/origen.log 2>&1 &", "touch /run/lab-listo", ""]),
                "origen.py": ORIGEN_PY}
    if nodo == "origin-sim":
        return {"arranque.sh": "\n".join(["#!/bin/sh", cabecera("#").rstrip(), "ip link set eth1 up", f"ip addr add {P['origin_sim']}/{ipaddress.ip_network(P['wan_red']).prefixlen} dev eth1",
                                          "python3 /lab/origin-sim.py > /var/log/origin-sim.log 2>&1 &", "touch /run/lab-listo", ""]),
                "origin-sim.py": ORIGIN_SIM_PY}
    if nodo == "gw-sim":
        ip = _ip_de(x, "EC2-GW")
        pref = ipaddress.ip_network(x.componentes["AWS-PUB-A"]["cidr"]).prefixlen
        base = ["#!/bin/sh", cabecera("#").rstrip(), "set -u", "ip link set eth1 up", f"ip addr add {ip}/{pref} dev eth1",
                f"ip route replace default via {P['vgw_lan']}", "mkdir -p /var/log/nginx", "touch /var/log/modsec_audit.log; chmod 666 /var/log/modsec_audit.log",
                "mkdir -p /etc/modsecurity; cp /lab/lab-main.conf /etc/modsecurity/lab-main.conf", "nginx -c /lab/nginx.conf", "sh /lab/agente.sh &", "touch /run/lab-listo", ""]
        return {"arranque.sh": "\n".join(base), "nginx.conf": _nginx_gw(x), "lab-main.conf": _modsec_main(), "agente.sh": _agente_sh(x, "gw-sim")}
    if nodo == "byod01":
        # Equipo personal en el Wi-Fi (D5.3): sin DNS de la DTI emulado; resuelve a mano los nombres de prueba
        return {"arranque.sh": "\n".join(["#!/bin/sh", cabecera("#").rstrip(), "ip link set eth1 up",
                f"ip addr add {P['byod01']}/{ipaddress.ip_network(x.zonas['WIFI-EST']['cidr']).prefixlen} dev eth1", f"ip route replace default via {P['wifi_gw']}",
                f"printf '%s\\n' '{P['ext01']} {P['dominio_origen']} {P['dominio_generico']}' '{P['origin_sim']} {P['dominio_grande']}' '{_ip_de(x, 'PORTAL01')} {P['dominio_portal']}' >> /etc/hosts",
                "touch /run/lab-listo", ""])}
    if nodo in CLIENTES_LAB:
        zona, par = CLIENTES_LAB[nodo]
        return {"arranque.sh": "\n".join(["#!/bin/sh", cabecera("#").rstrip(), "set -u"] + _red_host(x, None, zona, ip=P[par]) + ["touch /run/lab-listo", ""])}
    comp, zona, rol = NODOS[nodo]
    base = ["#!/bin/sh", cabecera("#").rstrip(), "set -u"] + _red_host(x, comp, zona)
    agente = nodo in AGENTES
    if agente:
        base += ["sh /lab/agente.sh &"]
    extra_agente = {"agente.sh": _agente_sh(x, nodo)} if agente else {}
    if rol == "host":
        base += ["touch /run/lab-listo", ""]
        return {"arranque.sh": "\n".join(base)} | extra_agente
    if rol == "siem":
        ip = _ip_de(x, comp)
        # F14: syslog por TLS en 6514, hacia el syslog TCP de bucle local del manager (sin UDP 514, REQ-NF-14 análogo). Servidor TLS sin certificado de cliente.
        base += [f"socat -d OPENSSL-LISTEN:6514,bind={ip},reuseaddr,fork,cert=/pki/siem01.pem,key=/pki/siem01.key,verify=0 TCP:127.0.0.1:514 > /var/log/syslog-tls.log 2>&1 &",
                 "touch /run/lab-listo", ""]
        return {"arranque.sh": "\n".join(base)}
    if rol == "ctrl":
        # CTRL01 (D5.3): consola de prueba en 443 (F28, F30) y, en la etapa 3, firma de la configuración de los nodos
        base += ["touch /var/log/consola.log; chmod 666 /var/log/consola.log", "mkdir -p /firmada",
                 "python3 /lab/consola.py >> /var/log/consola.log 2>&1 &", "touch /run/lab-listo", ""]
        return {"arranque.sh": "\n".join(base), "consola.py": CONSOLA_PY, "firmar.sh": FIRMAR_SH} | extra_agente
    if rol == "edge":
        ip = _ip_de(x, comp)
        base += ["mkdir -p /data/store /data/ca /data/logs", "RUST_LOG=celeris_cache=info celeris-cache /lab/config.toml > /var/log/celeris.log 2>&1 &"]
        # D1.8: EDGE01 y EDGE02 sirven el PAC (dos registros A). REQ-F-26: lo genera el binario (`celeris-cache pac`) desde la configuración del nodo
        base += ["mkdir -p /pac", "celeris-cache pac /lab/config.toml > /pac/wpad.dat", "nginx -c /lab/nginx.conf"]
        base += ["touch /run/lab-listo", ""]
        return {"arranque.sh": "\n".join(base), "config.toml": _config_edge(x, nodo), "nginx.conf": _nginx_pac(ip).replace("root /lab/pac", "root /pac")} | extra_agente
    if rol == "portal":
        # F33 (CI-52): el SFTP de entrega del certificado se EMULA con un escucha en TCP 22 (sin ACME, sin llave ni chroot reales). PORTAL01 no tiene ninguna regla de salida hacia la WAN.
        base += [f"python3 /lab/sftp-sim.py {_ip_de(x, comp)} 22 &","mkdir -p /var/log/nginx", "touch /var/log/modsec_audit.log; chmod 666 /var/log/modsec_audit.log",
                 "mkdir -p /etc/modsecurity; cp /lab/lab-main.conf /etc/modsecurity/lab-main.conf", "nginx -c /lab/nginx.conf", "touch /run/lab-listo", ""]
        return {"arranque.sh": "\n".join(base), "nginx.conf": _nginx_portal(x), "lab-main.conf": _modsec_main(), "web/index.html": _html_aviso(aviso_md), "sftp-sim.py": SFTP_SIM_PY} | extra_agente
    if rol == "canary":
        ip = _ip_de(x, comp)
        base += ["touch /var/log/canary.json; chmod 666 /var/log/canary.json", f"python3 /lab/canario.py {ip} 22,80,445,3389 &", "touch /run/lab-listo", ""]
        return {"arranque.sh": "\n".join(base), "canario.py": CANARIO_PY} | extra_agente
    raise ValueError(nodo)





def todos_los_nodos() -> list[str]:
    return ["fw01-sim", "fgt-sim", "vgw-sim", "gw-sim", "ext01", "origin-sim", "byod01"] + list(NODOS) + list(CLIENTES_LAB)


def puentes_sh(x: Infra) -> str:
    """Script del anfitrión: crea los puentes Linux (uno por VLAN y la WAN) y desactiva br_netfilter (si no, Docker filtraría L2)."""
    nombres = [puente(x, z) for z in ZONAS_PUENTE] + ["br-wan", "br-wifi"]
    return "\n".join(["#!/bin/sh", cabecera("#").rstrip(), "set -e", 'accion="${1:-up}"', "modprobe br_netfilter 2>/dev/null || true",
                      "for k in bridge-nf-call-iptables bridge-nf-call-ip6tables bridge-nf-call-arptables; do sysctl -qw net.bridge.$k=0 2>/dev/null || true; done",
                      f"for b in {' '.join(nombres)}; do", '  if [ "$accion" = up ]; then ip link show "$b" >/dev/null 2>&1 || ip link add "$b" type bridge; ip link set "$b" up',
                      '  else ip link del "$b" 2>/dev/null || true; fi', "done", ""])





# ------------------------------------------------------------------------------------------------------------------
# PKI de laboratorio (fuera del repositorio) y salida
# ------------------------------------------------------------------------------------------------------------------

def crear_pki(directorio: Path, x: Infra | None = None) -> None:
    """CA de laboratorio y certificados del portal, el origen, siem01, ctrl01, el panel de EC2-GW y los clientes mTLS (nodos EDGE y gw-sim).
    Se generan una vez; nunca se versionan (lab/.run/ está en .gitignore). Lo que falte se completa sin tocar la CA."""
    directorio.mkdir(parents=True, exist_ok=True)

    def sh(*a):
        subprocess.run(a, check=True, capture_output=True, cwd=directorio)

    def ca(nombre: str, asunto: str):
        if not (directorio / f"{nombre}.pem").exists():
            sh("openssl", "req", "-x509", "-newkey", "rsa:3072", "-nodes", "-keyout", f"{nombre}.key", "-out", f"{nombre}.pem", "-days", "30", "-subj", f"/CN={asunto}",
               "-addext", "basicConstraints=critical,CA:TRUE", "-addext", "keyUsage=critical,keyCertSign,cRLSign")

    def cert(nombre: str, emisor: str, asunto: str, san: list[str], uso: str):
        if (directorio / f"{nombre}.pem").exists():
            return
        sh("openssl", "req", "-newkey", "rsa:2048", "-nodes", "-keyout", f"{nombre}.key", "-out", f"{nombre}.csr", "-subj", f"/CN={asunto}")
        ext = ("subjectAltName=" + ",".join(san) + "\n" if san else "") + f"basicConstraints=CA:FALSE\nextendedKeyUsage={uso}\n"
        (directorio / f"{nombre}.cnf").write_text(ext)
        sh("openssl", "x509", "-req", "-in", f"{nombre}.csr", "-CA", f"{emisor}.pem", "-CAkey", f"{emisor}.key", "-CAcreateserial", "-out", f"{nombre}.pem", "-days", "30",
           "-extfile", f"{nombre}.cnf")

    ca("ca", "Celeris Lab CA")
    ca("nodos-ca", "Celeris Lab CA de nodos")
    cert("portal", "ca", P["dominio_portal"], [f"DNS:{P['dominio_portal']}"], "serverAuth")
    cert("origen", "ca", P["dominio_origen"], [f"DNS:{d}" for d in (P["dominio_origen"], P["dominio_generico"])], "serverAuth")
    if x is not None:
        cert("siem01", "ca", "siem01", [f"IP:{_ip_de(x, 'SIEM01')}"], "serverAuth")
        cert("ctrl01", "ca", "ctrl01", [f"IP:{_ip_de(x, 'CTRL01')}", "DNS:ctrl01"], "serverAuth")
        cert("gw-sim-servidor", "ca", P["dominio_panel"], [f"DNS:{P['dominio_panel']}", f"IP:{P['gw_publica']}"], "serverAuth")
    for nodo in ("edge01", "edge02", "gw-sim"):          # certificados de cliente (mTLS): nodos hacia la consola (F10) y EC2-GW hacia CTRL01 (F30)
        cert(nodo, "nodos-ca", nodo, [], "clientAuth")
    if not (directorio / "config-firma.key").exists():        # REQ-F-17: par ed25519 con que ctrl01 firma la configuración; la pública (32 bytes en hex) se fija en los nodos
        sh("openssl", "genpkey", "-algorithm", "ed25519", "-out", "config-firma.key")
        der = subprocess.run(["openssl", "pkey", "-in", "config-firma.key", "-pubout", "-outform", "DER"], check=True, capture_output=True, cwd=directorio).stdout
        (directorio / "config-firma.pub").write_text(der[-32:].hex() + "\n")
    for f in directorio.glob("*.key"):
        f.chmod(0o644)       # los contenedores leen la llave desde un montaje de solo lectura; es de laboratorio y vive en lab/.run/


def generar_todo(x: Infra, lab_dir: Path, aviso_md: Path) -> list[Path]:
    gen = lab_dir / "generated"
    escritos = []
    escribir(lab_dir / "celeris.clab.yml", topologia_yaml(x))
    escritos.append(lab_dir / "celeris.clab.yml")
    for nodo in todos_los_nodos():
        for nombre, texto in archivos_nodo(x, nodo, aviso_md).items():
            ruta = gen / nodo / nombre
            escribir(ruta, texto, 0o755 if nombre.endswith(".sh") else None)
            escritos.append(ruta)
    for nombre, texto in (("puentes.sh", puentes_sh(x)),):
        escribir(gen / nombre, texto, 0o755)
        escritos.append(gen / nombre)
    firmada = lab_dir / ".run" / "firmada"
    firmada.mkdir(parents=True, exist_ok=True)
    firmada.chmod(0o777)                # ctrl01 (root) escribe y los nodos EDGE leen
    pki = lab_dir / ".run" / "pki"
    crear_pki(pki, x)
    vpn.escribir_psk(pki, x, P["aws_peers"], P["fgt_wan"])
    return escritos
