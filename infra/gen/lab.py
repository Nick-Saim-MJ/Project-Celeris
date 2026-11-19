"""Topología containerlab del Modo L (Parte F4.1) y configuración de cada nodo, generadas desde infra/inventory.yaml.

Todo el laboratorio es EMULADO (Parte F4.2): fw01-sim no es OPNsense, vgw-sim no es el VGW de AWS, el WAF es nginx con
ModSecurity y OWASP CRS (F4.2 dice Caddy + Coraza) y los honeypots son equivalentes funcionales.
Las IP de los nodos, los CIDR, las puertas de enlace, los puertos y los flujos salen del inventario. Lo que el inventario no
define (la WAN del laboratorio, los nombres DNS de prueba, la IP de vgw-sim en la subred app-a) está en PARAMETROS_LAB y se
registra en docs/infra/e1/CAMBIOS-INVENTARIO.md (CI-24).
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

# CI-24: valores del laboratorio que el inventario no fija.
PARAMETROS_LAB = {
    "wan_red": "198.51.100.0/24",           # F4.1: la WAN y las IP públicas se reemplazan por la red de documentación
    "fw01_wan": "198.51.100.10",            # mismo último octeto que 203.0.113.10
    "ext01": "198.51.100.100",              # atacante externo / origen web de prueba
    "aws_peers": ["198.51.100.21", "198.51.100.22"],
    "vgw_lan": "10.30.10.1",                # vgw-sim dentro de app-a (la VPC real no tiene este equipo)
    "dominio_portal": "portal.celeris.internal",
    "dominio_origen": "listado.example.com",    # dominio «listado» de T07: el nodo descifra su TLS
    "dominio_generico": "example.com",          # T14, T19, T22, T24
}
P = PARAMETROS_LAB

# nombre de nodo → (componente, zona, rol)
NODOS = {
    "jmp01": ("JMP01", "MGMT", "host"),
    "svc01": ("SVC01", "SERVERS", "svc"),
    "obs01": ("OBS01", "SERVERS", "host"),
    "labcli01": ("LABCLI01", "LAB", "host"),
    "hny02": ("HNY02", "LAB", "canary"),
    "kali01": ("KALI01", "LAB-TEST", "host"),
    "waf01": ("WAF01", "DMZ-SVC", "waf"),
    "web01": ("WEB01", "DMZ-SVC", "web"),
    "hny01": ("HNY01", "DMZ-HONEY", "host"),
    "ids01": ("IDS01", "SECURITY", "ids"),
    "edge01": ("EDGE01", "EDGE", "edge"),
    "edge02": ("EDGE02", "EDGE", "edge"),
}
# Zonas con puente en F4.1 (no hay br-vlan70 ni br-vlan71: STORAGE y BACKUP no se emulan, CI-16)
ZONAS_PUENTE = ["MGMT", "SERVERS", "LAB", "LAB-TEST", "DMZ-SVC", "DMZ-HONEY", "SECURITY", "EDGE"]
CAPTURAS_IDS01 = ["MGMT", "SERVERS", "LAB-TEST", "SECURITY"]      # D1.14: VLAN 10, 20, 31 y 50


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

    def linux(nombre, imagen, ifaces, extra=None):
        d = {"kind": "linux", "image": imagen, "binds": [f"generated/{nombre}:/lab:ro", ".run/pki:/pki:ro"],
             "env": {"ESPERA_IFACES": " ".join(ifaces)}, "cap-add": ["NET_ADMIN", "NET_RAW", "SYS_ADMIN"]}
        d.update(extra or {})
        nodes[nombre] = d

    # fw01-sim: wan + una interfaz por zona con puente
    zf = ZONAS_PUENTE
    ifs = [f"eth{n}" for n in range(1, len(zf) + 2)]
    linux("fw01-sim", IMAGEN_BASE, ifs, {"sysctls": {"net.ipv4.ip_forward": 1, "net.ipv4.conf.all.rp_filter": 0}})
    links.append({"endpoints": ["fw01-sim:eth1", f"br-wan:{_veth('fw01-sim', 'wan')}"]})
    for n, z in enumerate(zf, start=2):
        links.append({"endpoints": [f"fw01-sim:eth{n}", f"{puente(x, z)}:{_veth('fw01-sim', str(x.zonas[z]['vlan']))}"]})

    for nombre, (comp, zona, rol) in NODOS.items():
        extra, ifaces = {}, ["eth1"]
        if nombre in ("edge01", "edge02"):
            imagen = IMAGEN_NODO
        else:
            imagen = IMAGEN_BASE
        if rol == "ids":
            ifaces = ["eth1"] + [f"eth{n}" for n in range(2, 2 + len(CAPTURAS_IDS01))]
        linux(nombre, imagen, ifaces, extra)
        links.append({"endpoints": [f"{nombre}:eth1", f"{puente(x, zona)}:{_veth(nombre, str(x.zonas[zona]['vlan']))}"]})
        if rol == "ids":
            for n, zc in enumerate(CAPTURAS_IDS01, start=2):
                links.append({"endpoints": [f"{nombre}:eth{n}", f"{puente(x, zc)}:{_veth(nombre, 'c' + str(x.zonas[zc]['vlan']))}"]})

    # Cowrie (SSH 2222, F24) comparte la red de hny01: su imagen oficial no trae shell para configurar interfaces
    nodes["hny01-cowrie"] = {"kind": "linux", "image": IMAGEN_COWRIE, "network-mode": "container:hny01"}

    # WAN simulada y nube emulada
    linux("ext01", IMAGEN_BASE, ["eth1"])
    links.append({"endpoints": ["ext01:eth1", f"br-wan:{_veth('ext01', 'wan')}"]})
    linux("vgw-sim", IMAGEN_BASE, ["eth1", "eth2"], {"sysctls": {"net.ipv4.ip_forward": 1, "net.ipv4.conf.all.rp_filter": 0}})
    links.append({"endpoints": ["vgw-sim:eth1", f"br-wan:{_veth('vgw-sim', 'wan')}"]})
    linux("shield01", IMAGEN_NODO, ["eth1"])
    links.append({"endpoints": ["vgw-sim:eth2", "shield01:eth1"]})
    return {"name": "celeris", "topology": {"nodes": nodes, "links": links}}


def topologia_yaml(x: Infra) -> str:
    cab = ("# GENERADO por infra/gen/lab.py desde infra/inventory.yaml — no editar a mano (make lab-gen).\n"
           "# Laboratorio EMULADO (Modo L, Parte F4): no es el producto real. Las IP de cada nodo están en lab/generated/<nodo>/arranque.sh.\n")
    return cab + yaml.safe_dump(topologia(x), sort_keys=False, allow_unicode=True, width=200)


# ------------------------------------------------------------------------------------------------------------------
# Configuración de cada nodo
# ------------------------------------------------------------------------------------------------------------------

def _resolv(x: Infra, zona: str) -> str:
    svc = _ip_de(x, "SVC01")
    return f"printf 'nameserver {svc}\\nnameserver {_gw(x, zona)}\\n' > /etc/resolv.conf"


def _red_host(x: Infra, comp: str, zona: str, iface: str = "eth1") -> list[str]:
    return [f"ip link set {iface} up", f"ip addr add {_ip_de(x, comp, zona)}/{_pref(x, zona)} dev {iface}",
            f"ip route replace default via {_gw(x, zona)}", _resolv(x, zona)]


def _zona_dns(x: Infra) -> str:
    """Zona DNS interna del laboratorio: nombres del inventario y nombres de prueba (CI-24)."""
    pac_host = x.inv["servicios_base"]["pac"]["url"].split("/")[2]
    lineas = ["server:"]
    for r in x.inv["servicios_base"]["pac"]["registros_a"]:
        lineas.append(f'  local-data: "{pac_host}. A {r["ip"]}"')
    lineas.append(f'  local-data: "{P["dominio_portal"]}. A {_ip_de(x, "WAF01")}"')
    for d in (P["dominio_origen"], P["dominio_generico"]):
        lineas.append(f'  local-zone: "{d}." redirect')
        lineas.append(f'  local-data: "{d}. A {P["ext01"]}"')
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


def _nginx_waf(x: Infra) -> str:
    web = _ip_de(x, "WEB01")
    pt = next(p for f in x.inv["flujos"] if f["id"] == "F22" for pr in f["protocolos"] for p in pr["puertos"])
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
    {CAB_WAF}    limit_req zone=porip burst=40 nodelay;
    location / {{ proxy_pass http://{web}:{pt}; proxy_set_header Host $host; }}
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


def _nginx_web(x: Infra) -> str:
    pt = next(p for f in x.inv["flujos"] if f["id"] == "F22" for pr in f["protocolos"] for p in pr["puertos"])
    return f"""{cabecera('#')}user www-data;
worker_processes 1;
pid /run/nginx.pid;
events {{ worker_connections 64; }}
http {{
  access_log /var/log/nginx/access.log;
  server {{
    listen {_ip_de(x, 'WEB01')}:{pt};
    server_tokens off;
    root /lab/web;
    {CAB_APP}    location / {{ try_files $uri /index.html; }}
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
    return (f"{cabecera('#')}# Lab: sin sincronización hacia arriba (F25 NTS no se emula); sirve la hora local a los clientes (F2).\n"
            "local stratum 10\nrtcsync\nmakestep 1 3\n" + "".join(f"allow {s['cidr']}\n" for s in x.inv["supernets"] if s["id"] == "CAMPUS-RESUMEN")
            + "driftfile /run/chrony.drift\n")


def _config_edge(x: Infra, nodo: str) -> str:
    comp, zona, _ = NODOS[nodo]
    f1 = x.flujos["F1"]
    clientes = [x.zonas[z]["cidr"] for z in f1["origen"]]
    puerto = f1["protocolos"][0]["puertos"][0]
    f12 = x.flujos["F12"]
    admin = next(p for pr in f12["protocolos"] for p in pr["puertos"] if p == 9128)
    ip = _ip_de(x, comp)
    return (f'{cabecera("#")}listen = "{ip}:{puerto}"\n'
            f"allowed_clients = {clientes!r}\n".replace("'", '"') +
            f'operator_contact = "redes@example.invalid"\ndata_dir = "/data/store"\nca_cert = "/data/ca/celeris-ca.crt"\nca_key = "/data/ca/celeris-ca.key"\n'
            f'intercept_domains = ["{P["dominio_origen"]}"]\nupstream_extra_ca = ["/pki/ca.pem"]\n'
            f'admin_listen = "{ip}:{admin}"\nadmin_token_file = "/data/admin.token"\n'
            # REQ-NF-14: el puerto de administración solo por TLS (certificado autofirmado de laboratorio, generado por el nodo al arrancar)
            'admin_tls = true\nadmin_tls_cert = "/data/ca/admin-tls.crt"\nadmin_tls_key = "/data/ca/admin-tls.key"\n'
            'security_log_enabled = true\nsecurity_log_dir = "/data/logs"\n')


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
import http.server, ssl, sys, threading
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        cuerpo = ("origen " + self.headers.get("Host", "?") + " " + self.path + "\\n").encode() + b"x" * 2048
        self.send_response(200); self.send_header("Content-Type", "text/plain")
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


def _arranque_fw(x: Infra) -> str:
    fw = fw01_interfaces(x)
    L = ["#!/bin/sh", cabecera("#").rstrip(), "set -u", "mount -o remount,rw /proc/sys 2>/dev/null || true",
         "sysctl -qw net.ipv4.ip_forward=1 net.ipv4.conf.all.rp_filter=0 net.ipv4.conf.default.rp_filter=0 || true"]
    orden = ["PERIMETRO"] + ZONAS_PUENTE
    for n, zona in enumerate(orden, start=1):
        nombre = fw[zona]["interfaz"]
        L += [f"ip link set eth{n} down", f"ip link set eth{n} name {nombre}", f"ip link set {nombre} up"]
        pref = _pref(x, zona) if zona != "PERIMETRO" else ipaddress.ip_network(P["wan_red"]).prefixlen
        ip = fw[zona]["ip"] if zona != "PERIMETRO" else P["fw01_wan"]
        L.append(f"ip addr add {ip}/{pref} dev {nombre}")
    L += ["# VPN: interfaces VTI, charon (strongSwan) y FRR (BGP)", "sh /lab/vti-up.sh",
          "mkdir -p /etc/swanctl /run/frr", "cp /lab/swanctl.conf /etc/swanctl/swanctl.conf", "cp /lab/psk-fw01.conf /etc/swanctl/psk-fw01.conf 2>/dev/null || cp /pki/psk-fw01.conf /etc/swanctl/psk-fw01.conf",
          "cp /lab/strongswan.conf /etc/strongswan.conf", "/usr/lib/ipsec/charon > /var/log/charon.log 2>&1 &",
          "for i in 1 2 3 4 5 6 7 8 9 10; do [ -S /var/run/charon.vici ] && break; sleep 0.5; done", "swanctl --load-all --noprompt > /var/log/swanctl-load.log 2>&1",
          "cp /lab/frr.conf /etc/frr/frr.conf", "chown frr:frr /etc/frr/frr.conf /run/frr; chmod 640 /etc/frr/frr.conf",
          "sed -i 's/^bgpd=no/bgpd=yes/; s/^staticd=no/staticd=yes/' /etc/frr/daemons", "/usr/lib/frr/frrinit.sh start > /var/log/frr-start.log 2>&1",
          "# DNS secundario (Unbound de FW01), reglas y detección", "unbound -c /lab/unbound.conf &", "nft -f /lab/fw01sim.nft",
          f"nohup suricata --af-packet -c /lab/suricata.yaml > /var/log/suricata.out 2>&1 &", "touch /run/lab-listo", ""]
    return "\n".join(L)


def _arranque_vgw(x: Infra) -> str:
    L = ["#!/bin/sh", cabecera("#").rstrip(), "set -u", "mount -o remount,rw /proc/sys 2>/dev/null || true",
         "sysctl -qw net.ipv4.ip_forward=1 net.ipv4.conf.all.rp_filter=0 net.ipv4.conf.default.rp_filter=0 || true",
         "ip link set eth1 up"]
    L += [f"ip addr add {p}/{ipaddress.ip_network(P['wan_red']).prefixlen} dev eth1" for p in P["aws_peers"]]
    L += ["ip link set eth2 up", f"ip addr add {P['vgw_lan']}/{ipaddress.ip_network(x.componentes['AWS-APP-A']['cidr']).prefixlen} dev eth2",
          "sh /lab/vti-up.sh", "mkdir -p /etc/swanctl /run/frr", "cp /lab/swanctl.conf /etc/swanctl/swanctl.conf",
          "cp /pki/psk-vgw.conf /etc/swanctl/psk-vgw.conf", "cp /lab/strongswan.conf /etc/strongswan.conf",
          "/usr/lib/ipsec/charon > /var/log/charon.log 2>&1 &", "for i in 1 2 3 4 5 6 7 8 9 10; do [ -S /var/run/charon.vici ] && break; sleep 0.5; done",
          "swanctl --load-all --noprompt > /var/log/swanctl-load.log 2>&1", "cp /lab/frr.conf /etc/frr/frr.conf",
          "chown frr:frr /etc/frr/frr.conf /run/frr; chmod 640 /etc/frr/frr.conf", "sed -i 's/^bgpd=no/bgpd=yes/; s/^staticd=no/staticd=yes/' /etc/frr/daemons",
          "/usr/lib/frr/frrinit.sh start > /var/log/frr-start.log 2>&1", "touch /run/lab-listo", ""]
    return "\n".join(L)


def archivos_nodo(x: Infra, nodo: str, aviso_md: Path) -> dict[str, str]:
    """Contenido de lab/generated/<nodo>/: {nombre de archivo: texto}."""
    pac_txt = pac.generar(x)
    if nodo == "fw01-sim":
        fw = fw01_interfaces(x)
        ifaces_dns = [fw[z]["ip"] for z in ZONAS_PUENTE]
        aws = P["aws_peers"]
        return {
            "arranque.sh": _arranque_fw(x),
            "fw01sim.nft": nftables.generar(x, modo="piloto", ventana=False, wan_ip=P["fw01_wan"], aws_peers=aws),
            "swanctl.conf": vpn.swanctl(x, "fw01", aws, P["fw01_wan"]),
            "frr.conf": vpn.frr(x, "fw01"),
            "vti-up.sh": vpn.vti_up(x, "fw01", aws, P["fw01_wan"]),
            "strongswan.conf": vpn.strongswan_conf(),
            "unbound.conf": _unbound(x, ifaces_dns),
            "suricata.yaml": _suricata([fw["PERIMETRO"]["interfaz"]], "/lab/local.rules"),
            "local.rules": REGLAS_SURICATA,
        }
    if nodo == "vgw-sim":
        aws = P["aws_peers"]
        return {"arranque.sh": _arranque_vgw(x), "swanctl.conf": vpn.swanctl(x, "vgw", aws, P["fw01_wan"]), "frr.conf": vpn.frr(x, "vgw"),
                "vti-up.sh": vpn.vti_up(x, "vgw", aws, P["fw01_wan"]), "strongswan.conf": vpn.strongswan_conf()}
    if nodo == "ext01":
        return {"arranque.sh": "\n".join(["#!/bin/sh", cabecera("#").rstrip(), "ip link set eth1 up", f"ip addr add {P['ext01']}/{ipaddress.ip_network(P['wan_red']).prefixlen} dev eth1",
                                          f"ip route replace {x.inv['supernets'][0]['cidr']} via {P['fw01_wan']}", "python3 /lab/origen.py > /var/log/origen.log 2>&1 &", "touch /run/lab-listo", ""]),
                "origen.py": ORIGEN_PY}
    if nodo == "shield01":
        ip = _ip_de(x, "EC2-SHIELD")
        pref = ipaddress.ip_network(x.componentes["AWS-APP-A"]["cidr"]).prefixlen
        return {"arranque.sh": "\n".join(["#!/bin/sh", cabecera("#").rstrip(), "ip link set eth1 up", f"ip addr add {ip}/{pref} dev eth1",
                                          f"ip route replace default via {P['vgw_lan']}", "touch /run/lab-listo", ""])}
    comp, zona, rol = NODOS[nodo]
    base = ["#!/bin/sh", cabecera("#").rstrip(), "set -u"] + _red_host(x, comp, zona)
    if rol == "host":
        base += ["touch /run/lab-listo", ""]
        return {"arranque.sh": "\n".join(base)}
    if rol == "svc":
        ip = _ip_de(x, comp)
        base += [f"unbound -c /lab/unbound.conf &", "chronyd -f /lab/chrony.conf -x &", "nginx -c /lab/nginx.conf", "touch /run/lab-listo", ""]
        return {"arranque.sh": "\n".join(base), "unbound.conf": _unbound(x, [ip]), "chrony.conf": _chrony(x),
                "nginx.conf": _nginx_pac(ip).replace("root /lab/pac", "root /lab"), "wpad.dat": pac_txt}
    if rol == "edge":
        ip = _ip_de(x, comp)
        base += ["mkdir -p /data/store /data/ca /data/logs", "RUST_LOG=celeris_cache=info celeris-cache /lab/config.toml > /var/log/celeris.log 2>&1 &"]
        if nodo == "edge01":                                      # D1.12: EDGE01 sirve además una copia del PAC (F3)
            base += ["nginx -c /lab/nginx.conf"]
        base += ["touch /run/lab-listo", ""]
        out = {"arranque.sh": "\n".join(base), "config.toml": _config_edge(x, nodo)}
        if nodo == "edge01":
            out |= {"nginx.conf": _nginx_pac(ip).replace("root /lab/pac", "root /lab"), "wpad.dat": pac_txt}
        return out
    if rol == "waf":
        base += ["mkdir -p /var/log/nginx", "mkdir -p /etc/modsecurity; cp /lab/lab-main.conf /etc/modsecurity/lab-main.conf", "nginx -c /lab/nginx.conf", "touch /run/lab-listo", ""]
        return {"arranque.sh": "\n".join(base), "nginx.conf": _nginx_waf(x), "lab-main.conf": _modsec_main()}
    if rol == "web":
        ip = _ip_de(x, comp)
        waf = _ip_de(x, "WAF01")
        pt = next(p for f in x.inv["flujos"] if f["id"] == "F22" for pr in f["protocolos"] for p in pr["puertos"])
        # F22: nftables de host: solo WAF01 llega al origen; WEB01 no inicia nada (D1.9, «Salida»)
        nft = (f"{cabecera('#')}flush ruleset\ntable inet web01 {{\n  chain input {{ type filter hook input priority 0; policy drop;\n"
               f"    ct state established,related accept\n    iifname \"lo\" accept\n"
               f"    ip saddr {waf} ip daddr {ip} tcp dport {pt} counter accept comment \"F22 WAF01 > WEB01\"\n  }}\n"
               f"  chain output {{ type filter hook output priority 0; policy drop;\n    ct state established,related accept\n    oifname \"lo\" accept\n  }}\n}}\n")
        base += ["mkdir -p /var/log/nginx", "nft -f /lab/web01.nft", "nginx -c /lab/nginx.conf", "touch /run/lab-listo", ""]
        return {"arranque.sh": "\n".join(base), "nginx.conf": _nginx_web(x), "web01.nft": nft, "web/index.html": _html_aviso(aviso_md)}
    if rol == "canary":
        ip = _ip_de(x, comp)
        base += [f"python3 /lab/canario.py {ip} 22,80,445,3389 &", "touch /run/lab-listo", ""]
        return {"arranque.sh": "\n".join(base), "canario.py": CANARIO_PY}
    if rol == "ids":
        base += ["# eth2..eth5 son las interfaces de captura (D1.14); sin IP, en modo promiscuo"]
        for n in range(2, 2 + len(CAPTURAS_IDS01)):
            base.append(f"ip link set eth{n} up promisc on")
        caps = [f"eth{n}" for n in range(2, 2 + len(CAPTURAS_IDS01))]
        base += ["nohup suricata --af-packet -c /lab/suricata.yaml > /var/log/suricata.out 2>&1 &", "touch /run/lab-listo", ""]
        return {"arranque.sh": "\n".join(base), "suricata.yaml": _suricata(caps, "/lab/local.rules"), "local.rules": REGLAS_SURICATA}
    raise ValueError(nodo)


def todos_los_nodos() -> list[str]:
    return ["fw01-sim", "vgw-sim", "ext01", "shield01"] + list(NODOS)


def puentes_sh(x: Infra) -> str:
    """Script del anfitrión: crea los puentes Linux (uno por VLAN y la WAN) y desactiva br_netfilter (si no, Docker filtraría L2)."""
    nombres = [puente(x, z) for z in ZONAS_PUENTE] + ["br-wan"]
    return "\n".join(["#!/bin/sh", cabecera("#").rstrip(), "set -e", 'accion="${1:-up}"', "modprobe br_netfilter 2>/dev/null || true",
                      "for k in bridge-nf-call-iptables bridge-nf-call-ip6tables bridge-nf-call-arptables; do sysctl -qw net.bridge.$k=0 2>/dev/null || true; done",
                      f"for b in {' '.join(nombres)}; do", '  if [ "$accion" = up ]; then ip link show "$b" >/dev/null 2>&1 || ip link add "$b" type bridge; ip link set "$b" up',
                      '  else ip link del "$b" 2>/dev/null || true; fi', "done", ""])


def espejo_sh(x: Infra) -> str:
    """Espejo de puertos hacia las interfaces de captura de ids01 (D1.14: el tráfico entre VM de una VLAN no sale al switch físico)."""
    L = ["#!/bin/sh", cabecera("#").rstrip(), "set -u"]
    for zc in CAPTURAS_IDS01:
        v = x.zonas[zc]["vlan"]
        br = puente(x, zc)
        cap = _veth("ids01", f"c{v}")
        L += [f"# {br}: copia de cada puerto hacia {cap}", f"for p in $(ls /sys/class/net/{br}/brif); do",
              f'  [ "$p" = "{cap}" ] && continue', f'  case "$p" in ids01-{v}) continue;; esac',
              '  tc qdisc replace dev "$p" clsact 2>/dev/null',
              f'  tc filter replace dev "$p" ingress matchall action mirred egress mirror dev {cap} 2>/dev/null', "done"]
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------------------------------------------------------
# PKI de laboratorio (fuera del repositorio) y salida
# ------------------------------------------------------------------------------------------------------------------

def crear_pki(directorio: Path) -> None:
    """CA de laboratorio y certificados del portal y del origen. Se generan una vez; nunca se versionan (lab/.run/ está en .gitignore)."""
    directorio.mkdir(parents=True, exist_ok=True)
    if (directorio / "ca.pem").exists():
        return

    def sh(*a):
        subprocess.run(a, check=True, capture_output=True, cwd=directorio)
    sh("openssl", "req", "-x509", "-newkey", "rsa:3072", "-nodes", "-keyout", "ca.key", "-out", "ca.pem", "-days", "30", "-subj", "/CN=Celeris Lab CA",
       "-addext", "basicConstraints=critical,CA:TRUE", "-addext", "keyUsage=critical,keyCertSign,cRLSign")
    for nombre, dns in (("portal", [P["dominio_portal"]]), ("origen", [P["dominio_origen"], P["dominio_generico"]])):
        sh("openssl", "req", "-newkey", "rsa:2048", "-nodes", "-keyout", f"{nombre}.key", "-out", f"{nombre}.csr", "-subj", f"/CN={dns[0]}")
        (directorio / f"{nombre}.cnf").write_text("subjectAltName=" + ",".join(f"DNS:{d}" for d in dns) + "\nbasicConstraints=CA:FALSE\nextendedKeyUsage=serverAuth\n")
        sh("openssl", "x509", "-req", "-in", f"{nombre}.csr", "-CA", "ca.pem", "-CAkey", "ca.key", "-CAcreateserial", "-out", f"{nombre}.pem", "-days", "30",
           "-extfile", f"{nombre}.cnf")
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
    for nombre, texto in (("puentes.sh", puentes_sh(x)), ("espejo.sh", espejo_sh(x))):
        escribir(gen / nombre, texto, 0o755)
        escritos.append(gen / nombre)
    pki = lab_dir / ".run" / "pki"
    crear_pki(pki)
    vpn.escribir_psk(pki, x, P["aws_peers"], P["fw01_wan"])
    return escritos
