"""Casos de prueba del Modo L: cómo se ejecuta cada T-nn de infra/pruebas.yaml dentro del laboratorio emulado.

Cada caso devuelve una `Medicion`; los criterios de aprobación los evalúa `evaluar.py` con lo medido, no el caso.
Las IP, puertos y nombres salen del inventario (`Contexto.ip`, `Contexto.puerto`) o de `gen.lab.PARAMETROS_LAB`.
"""
from __future__ import annotations

import re
import time
from pathlib import Path

import laboratorio as L
from evaluar import Medicion

SIN_WAZUH = "Wazuh (siem01) no está desplegado en el laboratorio: la alerta del SIEM no se puede evaluar en el Modo L"

# T-nn con Modo L en infra/pruebas.yaml que el laboratorio no puede ejecutar, y por qué (CI-16, CI-24)
NO_APLICA_L = {
    "T12": "NAS01 y la VLAN 70 no se emulan (F4.1 no tiene br-vlan70, CI-16): que 10.20.70.20 no responda no demuestra que la VLAN no tenga ruta",
    "T23": "RA guard es un control del switch de acceso (SW-ACC, S-14); los puentes Linux del laboratorio no lo emulan",
    "T25": "ESX01, IPMI01, BRK01 y SW-CORE01 no se emulan: el puerto break-glass no existe en F4.1 (CI-16)",
    "T28": "siem01 (Wazuh) no está desplegado y fw01-sim no tiene syslog sobre TLS configurado: no hay flujo F14 que capturar",
}

SONDA_PY = r"""
import socket, sys, time
ip, port, dur, out = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
fin = time.time() + dur
with open(out, "w") as f:
    while time.time() < fin:
        t = time.time(); estado = "down"
        s = socket.socket(); s.settimeout(0.4)
        try:
            s.connect((ip, port)); estado = "up"
        except ConnectionRefusedError:
            estado = "up"          # el RST del destino llegó por el túnel: hay camino
        except Exception:
            estado = "down"
        finally:
            s.close()
        f.write("%.3f %s\n" % (t, estado)); f.flush()
        time.sleep(max(0, 0.1 - (time.time() - t)))
"""

UDP_RX_PY = r"""
import socket, sys, time
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("0.0.0.0", int(sys.argv[1]))); s.settimeout(1)
fin = time.time() + float(sys.argv[2]); n = 0
while time.time() < fin:
    try: s.recvfrom(2048); n += 1
    except Exception: pass
open(sys.argv[3], "w").write(str(n))
"""

UDP_TX_PY = r"""
import socket, sys
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
for i in range(5): s.sendto(b"\xc0" + b"quic-prueba" * 20, (sys.argv[1], int(sys.argv[2])))
"""

TCP_ESCUCHA_PY = r"""
import socket, sys, time
s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind((sys.argv[1], int(sys.argv[2]))); s.listen(8); s.settimeout(1)
fin = time.time() + float(sys.argv[3])
while time.time() < fin:
    try: c, _ = s.accept(); c.close()
    except Exception: pass
"""


class Contexto:
    def __init__(self, infra, parametros, ev, raiz: Path, nodo_ca_cache: dict):
        self.infra, self.P, self.ev, self.raiz = infra, parametros, ev, raiz
        self._ca = nodo_ca_cache

    def ip(self, comp: str, zona: str | None = None) -> str:
        return next(i["ip"] for i in self.infra.componentes[comp]["ips"] if i["ip"] and (zona is None or i["zona"] == zona))

    def puerto(self, flujo: str, n: int = 0) -> int:
        return [p for pr in self.infra.flujos[flujo]["protocolos"] for p in pr["puertos"]][n]

    def puerta(self, comp: str) -> str:
        zona = self.infra.componentes[comp]["zonas"][0]
        return self.infra.zonas[zona]["gateway"]

    @property
    def pki(self) -> Path:
        return self.raiz / "lab" / ".run" / "pki"

    def ca_del_nodo(self) -> str:
        """Ruta en labcli01 de la CA que emite edge01 (para validar el TLS interceptado)."""
        if "ruta" not in self._ca:
            pem = L.leer("edge01", "/data/ca/celeris-ca.crt")
            L.enviar("labcli01", "/tmp/celeris-ca.crt", pem)
            self._ca["ruta"] = "/tmp/celeris-ca.crt"
        return self._ca["ruta"]


def _sin_wazuh(m: Medicion) -> None:
    m.no_evaluable["alerta_wazuh"] = SIN_WAZUH


def _codigo_principal(rcs: list[int]) -> int:
    """0 si alguna conexión tuvo éxito; si todas fallaron, el primer código distinto de cero."""
    return 0 if 0 in rcs else next((r for r in rcs if r), 1)


def _bgp_y_sas(c: Contexto) -> tuple[bool, str]:
    _, sas = L.ex("fw01-sim", "swanctl --list-sas 2>/dev/null | grep -v '^plugin'")
    _, bgp = L.ex("fw01-sim", "vtysh -c 'show bgp summary' | grep -E '^16'")
    ok = sas.count("ESTABLISHED") >= 2 and len(re.findall(r"\d+:\d\d:\d\d|\d+d\d+h", bgp)) >= 2 and "Active" not in bgp and "Connect" not in bgp
    return ok, sas + "\n" + bgp


# ---------------------------------------------------------------------------------------------------------------------
def t05(c: Contexto) -> Medicion:
    """Falla de un túnel: baja el túnel activo con tráfico en curso y mide cuánto tarda en volver a pasar por el otro."""
    m = Medicion()
    objetivo, puerto = c.ip("EC2-SHIELD"), c.puerto("F9")
    ok, estado = _bgp_y_sas(c)
    c.ev.guardar("antes.txt", estado)
    if not ok:
        raise RuntimeError("precondición: los dos túneles y las dos sesiones BGP deben estar establecidos")
    L.enviar("edge01", "/tmp/sonda.py", SONDA_PY)
    L.fondo("edge01", f"python3 /tmp/sonda.py {objetivo} {puerto} 110 /tmp/sonda.log")
    time.sleep(4)
    t_baja = time.time()
    L.ex("fw01-sim", "swanctl --terminate --ike tunel1 2>&1 | grep -v '^plugin' | tail -2", timeout=30)

    def analizar():
        lineas = [l.split() for l in L.leer("edge01", "/tmp/sonda.log").splitlines() if len(l.split()) == 2]
        caida = next((float(t) for t, e in lineas if e == "down" and float(t) >= t_baja), None)
        if caida is None:
            return None, None
        vuelta = next((float(t) for t, e in lineas if e == "up" and float(t) > caida), None)
        return caida, vuelta
    L.esperar(lambda: analizar()[1] is not None, 100, 2)
    caida, vuelta = analizar()
    if caida is None:
        m.medidas["convergencia_s"] = 0.0
        m.hallazgos.append("la sonda no vio ninguna interrupción tras bajar el túnel 1 (¿ya iba por el túnel 2?)")
    elif vuelta is None:
        m.medidas["convergencia_s"] = 999.0
        m.hallazgos.append("el tráfico no se recuperó por el túnel 2 en 100 s")
    else:
        m.medidas["convergencia_s"] = round(vuelta - t_baja, 1)
        m.medidas["interrupcion_s"] = round(vuelta - caida, 1)
    L.ex("edge01", "pkill -f sonda.py")
    L.traer("edge01", "/tmp/sonda.log", c.ev.dir / "sonda.log")
    c.ev.registrar_existente("sonda.log")
    _, sas = L.ex("fw01-sim", "swanctl --list-sas 2>/dev/null | grep -v '^plugin'")
    _, ruta = L.ex("fw01-sim", "vtysh -c 'show ip route 10.30.0.0/16' | head -8")
    c.ev.guardar("despues.txt", sas + "\n" + ruta)
    m.salidas["swanctl --list-sas"] = sas
    m.salidas["stdout"] = sas
    m.hallazgos.append(f"tras la caída la ruta a 10.30.0.0/16 va por: {'vti2' if 'vti2' in ruta else 'vti1' if 'vti1' in ruta else 'ninguna'}")
    # restaura el túnel 1 y espera a que BGP vuelva a tener los dos vecinos
    L.ex("fw01-sim", "timeout 25 swanctl --initiate --child tunel1 2>&1 | grep -v '^plugin' | tail -1", timeout=40)
    L.esperar(lambda: _bgp_y_sas(c)[0], 90, 3)
    return m


def t06(c: Contexto) -> Medicion:
    """LAB → MGMT: con puertos abiertos a propósito en MGMT, nmap desde LABCLI01 no debe ver ninguno abierto."""
    m = Medicion()
    red = c.infra.zonas["MGMT"]["cidr"]
    jmp = c.ip("JMP01")
    L.enviar("jmp01", "/tmp/escucha.py", TCP_ESCUCHA_PY)
    L.fondo("jmp01", f"python3 /tmp/escucha.py {jmp} 22 40 & python3 /tmp/escucha.py {jmp} 443 40 & wait")
    time.sleep(1)
    rc_ctrl, _ = L.ex("jmp01", f"nc -zv -w2 {jmp} 22")
    antes = L.contador_nft("DENEGADO", "forward")
    rc, out = L.ex("labcli01", f"nmap -n -Pn -p22,443 --max-retries 1 --max-rtt-timeout 300ms {red}", timeout=120)
    despues = L.contador_nft("DENEGADO", "forward")
    c.ev.guardar("nmap.txt", out)
    m.salidas["stdout"] = out
    m.medidas["puertos_open"] = len(re.findall(r"(?m)^\d+/tcp\s+open", out))
    m.medidas["paquetes_denegados_por_fw01"] = despues - antes
    if rc_ctrl != 0:
        m.vacia = "el control positivo falló: el puerto 22 de JMP01 no abre ni desde su propia red"
    elif "filtered" not in out and "all 2" not in out and m.medidas["puertos_open"] == 0:
        m.vacia = "nmap no informó puertos filtrados: la denegación no quedó demostrada"
    return m


def t07(c: Contexto) -> Medicion:
    """LAB → EDGE 3128: proxy explícito hacia el dominio listado, con la CA del nodo."""
    m = Medicion()
    ca = c.ca_del_nodo()
    px = f"http://{c.ip('EDGE01')}:{c.puerto('F1')}"
    url = f"https://{c.P['dominio_origen']}/t07.js"
    cmd = f"curl -sS -D - -o /dev/null -x {px} --cacert {ca} {url}"
    rc1, h1 = L.ex("labcli01", cmd)
    rc2, h2 = L.ex("labcli01", cmd)
    m.codigos["principal"] = rc1 or rc2
    m.salidas["stdout"] = h1 + "\n--- segunda petición ---\n" + h2
    c.ev.guardar("cabeceras.txt", m.salidas["stdout"])
    est = re.findall(r"(?im)^x-celeris-cache:\s*(\S+)", m.salidas["stdout"])
    m.medidas["x_celeris_cache_primera"] = 0 if not est else (1 if est[0] == "MISS" else 2)
    # Cache-Status (RFC 9211): la primera petición es un MISS guardado y la segunda un HIT (D1.16, REQ-NF-11).
    primera, segunda = (re.findall(r"(?im)^cache-status:\s*(.+?)\s*$", h) for h in (h1, h2))
    m.medidas["cache_status_primera_miss"] = int(any(re.match(r"celeris; fwd=miss; stored$", v) for v in primera))
    m.medidas["cache_status_segunda_hit"] = int(any(re.match(r"celeris; hit; ttl=-?\d+$", v) for v in segunda))
    if not primera:
        m.hallazgos.append(f"el nodo responde X-Celeris-Cache ({', '.join(est)}) pero no la cabecera estándar Cache-Status (RFC 9211) que pide D1.16 (REQ-NF-11)")
    elif not (m.medidas["cache_status_primera_miss"] and m.medidas["cache_status_segunda_hit"]):
        m.hallazgos.append(f"Cache-Status presente pero distinto de lo esperado: primera = {primera}, segunda = {segunda}")
    return m


def t08(c: Contexto) -> Medicion:
    """QUIC (UDP 443): los datagramas no llegan al origen y la regla de F7 cuenta paquetes."""
    m = Medicion()
    ext = c.P["ext01"]
    L.enviar("ext01", "/tmp/udp_rx.py", UDP_RX_PY)
    L.fondo("ext01", "python3 /tmp/udp_rx.py 443 8 /tmp/udp_rx.n")
    L.enviar("labcli01", "/tmp/udp_tx.py", UDP_TX_PY)
    time.sleep(1)
    antes = L.contador_nft("udp . 443", "forward")
    L.ex("labcli01", f"python3 /tmp/udp_tx.py {ext} 443")
    time.sleep(8)
    despues = L.contador_nft("udp . 443", "forward")
    recibidos = int((L.leer("ext01", "/tmp/udp_rx.n") or "0").strip() or 0)
    rc_curl, _ = L.ex("labcli01", "curl --version | grep -i -c http3")
    # curl de Debian no trae HTTP/3: se sustituye `curl --http3` por 5 datagramas UDP al puerto 443 de ext01 (documentado en el ensayo)
    m.codigos["curl --http3 -m 5 https://example.com"] = 0 if recibidos > 0 else 1
    m.medidas["paquetes_bloqueados_regla_F7"] = despues - antes
    m.medidas["datagramas_recibidos_en_ext01"] = recibidos
    m.hallazgos.append("curl del laboratorio no soporta HTTP/3: `curl --http3` se sustituyó por una sonda UDP 443 (5 datagramas) hacia ext01")
    m.no_evaluable["manual"] = "requiere un navegador real con QUIC activado (Modo H)"
    return m


def _pac_fetch(c: Contexto, ruta: str) -> tuple[int, float, str]:
    """Cliente que imita al PAC: PROXY EDGE01, PROXY EDGE02, DIRECT, con 2 s de espera de conexión por proxy."""
    cmd = (f"for e in {c.ip('EDGE01')}:{c.puerto('F1')} {c.ip('EDGE02')}:{c.puerto('F1')} DIRECT; do "
           f"if [ \"$e\" = DIRECT ]; then k=$(curl -s -m4 --noproxy '*' -o /dev/null -w '%{{http_code}}' http://{c.P['dominio_generico']}{ruta}); "
           f"else k=$(curl -s --connect-timeout 2 -m4 -x http://$e -o /dev/null -w '%{{http_code}}' http://{c.P['dominio_generico']}{ruta}); fi; "
           f"echo \"$e -> $k\"; [ \"$k\" = 200 ] && {{ echo \"sirvió=$e\"; exit 0; }}; done; exit 1")
    t = time.time()
    rc, out = L.ex("labcli01", cmd, timeout=40)
    return rc, round(time.time() - t, 1), out


def t09(c: Contexto) -> Medicion:
    """Caída de EDGE01 (y luego de EDGE02): el cliente cambia de nodo y, sin nodos, a DIRECT. Imita al PAC; no es un navegador."""
    m = Medicion()
    p1, p2 = c.puerta("EDGE01"), c.puerta("EDGE02")
    try:
        rc0, t0, o0 = _pac_fetch(c, "/t09-base")
        L.enlace("edge01", False)
        rc1, t1, o1 = _pac_fetch(c, "/t09-a")
        L.enlace("edge02", False)
        rc2, t2, o2 = _pac_fetch(c, "/t09-b")
    finally:
        L.enlace("edge01", True, p1)
        L.enlace("edge02", True, p2)
    c.ev.guardar("conmutacion.txt", f"normal ({t0}s):\n{o0}\nEDGE01 caído ({t1}s):\n{o1}\nambos caídos ({t2}s):\n{o2}")
    m.medidas["tiempo_de_cambio_s"] = t1
    m.medidas["tiempo_hasta_direct_s"] = t2
    ok1 = rc1 == 0 and f"sirvió={c.ip('EDGE02')}" in o1
    ok2 = rc2 == 0 and "sirvió=DIRECT" in o2
    if not (ok1 and ok2):
        m.codigos["principal"] = 1
        m.salidas["conmutacion"] = o1 + o2
        m.hallazgos.append(f"conmutación incompleta: EDGE02={'sí' if ok1 else 'no'}, DIRECT={'sí' if ok2 else 'no'}")
        m.medidas["tiempo_de_cambio_s"] = -1
    m.no_evaluable["manual"] = "requiere navegar con un navegador real (Modo H); aquí se imita la lógica del PAC con curl"
    return m


def t10(c: Contexto) -> Medicion:
    """DMZ → LAN: con el puerto 445 abierto a propósito en LABCLI01, WEB01 y HNY01 no deben alcanzarlo."""
    m = Medicion()
    lab = c.ip("LABCLI01")
    L.enviar("labcli01", "/tmp/escucha.py", TCP_ESCUCHA_PY)
    L.fondo("labcli01", f"python3 /tmp/escucha.py {lab} 445 25")
    time.sleep(1)
    rc_ctrl, _ = L.ex("labcli01", f"nc -zv -w2 {lab} 445")
    rcs = [L.ex(n, f"nc -zv -w3 {lab} 445")[0] for n in ("web01", "hny01")]
    m.codigos["principal"] = _codigo_principal(rcs)
    if rc_ctrl != 0:
        m.vacia = "el control positivo falló: el puerto 445 de LABCLI01 no abre ni localmente"
    return m


def _reglas(c: Contexto, ventana: bool) -> str:
    from gen import nftables
    return nftables.generar(c.infra, modo="piloto", ventana=ventana, wan_ip=c.P["fw01_wan"], aws_peers=c.P["aws_peers"])


def t11(c: Contexto) -> Medicion:
    """Internet → DMZ-HONEY: con la ventana autorizada (F24), ext01 llega a Cowrie por el 22 y queda registro."""
    m = Medicion()
    wan = c.P["fw01_wan"]
    try:
        L.recargar_nft(_reglas(c, ventana=True))
        rc, out = L.ex("ext01", f"nc -zv -w3 {wan} 22")
        m.codigos["principal"] = rc
        L.ex("ext01", f"hydra -l root -p prueba123 -t 1 -f -s 22 ssh://{wan} 2>&1 | tail -4", timeout=60)
        time.sleep(2)
        _, cowrie = L.docker(["logs", "--tail", "80", L.PREFIJO + "hny01-cowrie"], 30)
        m.salidas["cowrie"] = cowrie
        c.ev.guardar("cowrie.log", cowrie)
        m.medidas["conexiones_en_cowrie"] = len(re.findall(r"New connection|login attempt|SSH client", cowrie))
        if m.medidas["conexiones_en_cowrie"] == 0:
            m.hallazgos.append("Cowrie no registró la conexión")
            m.codigos["principal"] = m.codigos["principal"] or 1
    finally:
        L.recargar_nft(_reglas(c, ventana=False))
    _sin_wazuh(m)
    m.hallazgos.append("el puerto 23 de F24 no se prueba: OpenCanary no está en el laboratorio")
    return m


def _nodo_edge_log(c: Contexto) -> str:
    time.sleep(1.5)
    return L.ex("edge01", "cat /data/logs/security-*.jsonl 2>/dev/null")[1]


def _connect(c: Contexto, destino: str, clave: str) -> Medicion:
    m = Medicion()
    px = f"http://{c.ip('EDGE01')}:{c.puerto('F1')}"
    rc, out = L.ex("labcli01", f"curl -s -m8 -p -x {px} -o /dev/null -w '%{{http_connect}}' https://{destino}/")
    m.codigos["principal"] = rc
    m.salidas["stdout"] = out.strip()
    log = _nodo_edge_log(c)
    m.salidas["registro_celeris"] = log
    c.ev.guardar("registro_seguridad.jsonl", log)
    return m


def t13(c: Contexto) -> Medicion:
    """Abuso del proxy: CONNECT a una IP interna (ESX01 vmk0) debe dar 403 y el evento destination_blocked."""
    return _connect(c, f"{c.ip('ESX01', 'MGMT')}:443", "destination_blocked")


def t14(c: Contexto) -> Medicion:
    """Puerto no permitido: CONNECT a example.com:25 debe dar 403 y el evento port_blocked."""
    return _connect(c, f"{c.P['dominio_generico']}:25", "port_blocked")


def t15(c: Contexto) -> Medicion:
    """Exposición del portal: desde Internet solo 80 y 443 (los señuelos solo con ventana autorizada)."""
    m = Medicion()
    wan = c.P["fw01_wan"]
    extra = ",".join(str(p) for p in sorted({c.puerto("F1"), c.puerto("F12"), c.puerto("F9"), c.puerto("F22"), 2222, 5601, 3000} - set(range(1, 1025))))
    rc, out = L.ex("ext01", f"nmap -sS -Pn -n -T4 --max-retries 1 -p 1-1024,{extra} {wan}", timeout=240)
    c.ev.guardar("nmap.txt", out)
    m.codigos["principal"] = rc
    m.salidas["stdout"] = out
    abiertos = re.findall(r"(?m)^(\d+)/tcp\s+open", out)
    m.medidas["puertos_abiertos"] = len(abiertos)
    time.sleep(2)
    eve = L.ex("fw01-sim", "grep -c '\"event_type\":\"alert\"' /var/log/suricata/eve.json 2>/dev/null")[1].strip()
    alertas = L.ex("fw01-sim", "grep '\"event_type\":\"alert\"' /var/log/suricata/eve.json 2>/dev/null | tail -3")[1]
    c.ev.guardar("suricata_alertas.json", alertas)
    m.medidas["alertas_suricata_fw01"] = int(eve) if eve.isdigit() else 0
    return m


def t16(c: Contexto) -> Medicion:
    """TLS del portal con testssl.sh (contenedor en la red de ext01, con la CA de laboratorio)."""
    m = Medicion()
    imagen = TESTSSL_IMAGEN
    rc, out = L.docker(["run", "--rm", "--network", f"container:{L.PREFIJO}ext01", "-v", f"{c.ev.dir}:/out", "-v", f"{c.pki}:/pki:ro", imagen,
                        "--add-ca", "/pki/ca.pem", "--ip", c.P["fw01_wan"], "--jsonfile", "/out/tls.json", "--warnings", "off", "--color", "0",
                        f"{c.P['dominio_portal']}:443"], 900)
    c.ev.guardar("testssl.txt", out)
    m.codigos["principal"] = rc
    ruta = c.ev.dir / "tls.json"
    if ruta.exists():
        m.salidas["tls.json"] = ruta.read_text(encoding="utf-8", errors="replace")
        c.ev.registrar_existente("tls.json")
        g = re.search(r'"id"\s*:\s*"overall_grade"[^}]*?"finding"\s*:\s*"([^"]+)"', m.salidas["tls.json"])
        m.hallazgos.append(f"calificación de testssl.sh: {g.group(1) if g else 'no informada'} (certificado de la CA de laboratorio; el ACME público se prueba en Modo H)")
    else:
        m.no_evaluable["tls.json"] = "testssl.sh no produjo tls.json"
    return m


def t17(c: Contexto) -> Medicion:
    """Escaneo web con ZAP baseline contra el portal."""
    m = Medicion()
    rc, out = L.docker(["run", "--rm", "--network", f"container:{L.PREFIJO}ext01", "-v", f"{c.ev.dir}:/zap/wrk:rw", ZAP_IMAGEN, "zap-baseline.py",
                        "-t", f"https://{c.P['fw01_wan']}/", "-J", "zap.json", "-m", "1", "-I"], 900)
    c.ev.guardar("zap.txt", out)
    ruta = c.ev.dir / "zap.json"
    m.codigos["principal"] = rc
    if ruta.exists():
        txt = ruta.read_text(encoding="utf-8", errors="replace")
        m.salidas["zap.json"] = txt
        c.ev.registrar_existente("zap.json")
        if '"@name"' not in txt and '"site"' not in txt:
            m.vacia = "ZAP no escaneó ningún sitio"
        m.medidas["alertas_altas"] = len(re.findall(r'"riskcode"\s*:\s*"3"', txt))
    else:
        m.no_evaluable["zap.json"] = "ZAP no produjo zap.json"
    return m


def t18(c: Contexto) -> Medicion:
    """WAF: una inyección SQL debe recibir 403 y quedar en el registro de auditoría de ModSecurity."""
    m = Medicion()
    q = "https://%s/?q=%%27%%20OR%%201%%3D1--" % c.P["dominio_portal"]
    rc, out = L.ex("ext01", f"curl -sk -m8 --resolve {c.P['dominio_portal']}:443:{c.P['fw01_wan']} -o /dev/null -w '%{{http_code}}' '{q}'")
    m.codigos["principal"] = rc
    m.salidas["stdout"] = out.strip()
    time.sleep(1)
    audit = L.ex("waf01", "tail -c 6000 /var/log/modsec_audit.log 2>/dev/null")[1]
    c.ev.guardar("modsec_audit.log", audit)
    n = L.ex("waf01", "grep -c '\"transaction\"' /var/log/modsec_audit.log 2>/dev/null")[1].strip()
    m.medidas["eventos_modsecurity"] = int(n) if n.isdigit() else 0
    _sin_wazuh(m)
    return m


def t19(c: Contexto) -> Medicion:
    """Salida del portal: WEB01 no sale a Internet (control positivo: WAF01 sí alcanza ACME/443)."""
    m = Medicion()
    objetivo = f"https://{c.P['dominio_generico']}/"
    rc_ctrl, _ = L.ex("waf01", f"curl -sk -m6 -o /dev/null -w '%{{http_code}}' --resolve {c.P['dominio_generico']}:443:{c.P['ext01']} {objetivo}")
    rc, out = L.ex("web01", f"curl -sS -m6 --resolve {c.P['dominio_generico']}:443:{c.P['ext01']} {objetivo}")
    m.codigos["principal"] = rc
    if rc_ctrl != 0:
        m.vacia = "el control positivo falló: WAF01 tampoco alcanzó al origen de prueba, así que la denegación de WEB01 no es concluyente"
    return m


def t20(c: Contexto) -> Medicion:
    """Aislamiento del señuelo: HNY01 no alcanza a WEB01:8080 (control positivo: WAF01 sí)."""
    m = Medicion()
    web, pt = c.ip("WEB01"), c.puerto("F22")
    rc_ctrl, _ = L.ex("waf01", f"nc -zv -w3 {web} {pt}")
    rc, _ = L.ex("hny01", f"nc -zv -w3 {web} {pt}")
    m.codigos["principal"] = rc
    if rc_ctrl != 0:
        m.vacia = "el control positivo falló: WAF01 no alcanza a WEB01"
    return m


def t22(c: Contexto) -> Medicion:
    """Caída de SVC01: el DNS lo atiende FW01 y el PAC lo sirve EDGE01."""
    m = Medicion()
    puerta_svc = c.puerta("SVC01")
    svc = c.ip("SVC01")
    resolv = L.leer("labcli01", "/etc/resolv.conf")
    try:
        L.ex("labcli01", f"printf '%s\\noptions timeout:2 attempts:1\\n' \"$(cat /etc/resolv.conf)\" > /tmp/r && cat /tmp/r > /etc/resolv.conf")
        L.enlace("svc01", False)
        rc_dns, dns = L.ex("labcli01", f"kdig +short +time=2 +retry=1 @{c.puerta('LABCLI01')} {c.P['dominio_generico']}")
        # El connect-timeout incluye la resolución: con SVC01 caído el cliente espera el timeout del resolvedor (2 s) antes de usar FW01.
        inicio = time.time()
        rc_pac, pac = L.ex("labcli01", "curl -s -m14 --connect-timeout 10 -o /dev/null -w '%{http_code}' http://pac.celeris.internal/wpad.dat", timeout=30)
        m.medidas["tiempo_hasta_el_pac_s"] = round(time.time() - inicio, 1)
        _, quien = L.ex("edge01", "tail -n 2 /var/log/nginx/pac.log 2>/dev/null")
    finally:
        L.enlace("svc01", True, puerta_svc)
        L.enviar("labcli01", "/etc/resolv.conf", resolv)
    c.ev.guardar("conmutacion.txt", f"DNS por FW01: {dns}\nPAC: {pac}\nnginx de EDGE01:\n{quien}")
    m.codigos["nslookup example.com 10.20.32.1"] = rc_dns if dns.strip() else 1
    m.salidas["curl ... http://pac.celeris.internal/wpad.dat"] = pac.strip()
    m.no_evaluable["manual"] = "requiere comprobar la navegación del usuario con un navegador real (Modo H)"
    m.hallazgos.append("`nslookup` no está en la imagen: se usó kdig contra la IP de FW01 en la VLAN de LAB")
    return m


def t24(c: Contexto) -> Medicion:
    """DNS cifrado: DoT (TCP 853) desde LABCLI01 queda bloqueado por F7 (control: ext01 escucha en 853)."""
    m = Medicion()
    ext = c.P["ext01"]
    L.enviar("ext01", "/tmp/escucha.py", TCP_ESCUCHA_PY)
    L.fondo("ext01", f"python3 /tmp/escucha.py {ext} 853 25")
    time.sleep(1)
    rc_ctrl, _ = L.ex("ext01", f"nc -zv -w2 {ext} 853")
    antes = L.contador_nft("tcp . 853", "forward")
    rc, out = L.ex("labcli01", f"kdig +tls +time=3 +retry=1 @{ext} {c.P['dominio_generico']}")
    despues = L.contador_nft("tcp . 853", "forward")
    m.codigos["principal"] = rc
    m.medidas["paquetes_bloqueados_regla_F7"] = despues - antes
    m.hallazgos.append("el resolvedor de prueba es ext01 (IP del laboratorio), no 203.0.113.53 (CI-19): la regla F7 bloquea por puerto, no por destino")
    if rc_ctrl != 0:
        m.vacia = "el control positivo falló: ext01 no escucha en 853"
    return m


def t26(c: Contexto) -> Medicion:
    """Privacidad del túnel: captura en vti1 durante un MISS con cabeceras de cliente falsas."""
    m = Medicion()
    ca = c.ca_del_nodo()
    px = f"http://{c.ip('EDGE01')}:{c.puerto('F1')}"
    L.fondo("fw01-sim", "timeout 12 tcpdump -ni any -w /tmp/t26.pcap 'ip proto 50 or udp port 4500 or (host 10.30.10.10)'")
    time.sleep(1.5)
    L.ex("labcli01", f"curl -s -m8 -x {px} --cacert {ca} -H 'X-Forwarded-For: {c.ip('LABCLI01')}' -H 'Via: 1.1 cliente-lab' -o /dev/null "
                     f"https://{c.P['dominio_origen']}/t26-{int(time.time())}.js")
    time.sleep(11)
    L.traer("fw01-sim", "/tmp/t26.pcap", c.ev.dir / "t26.pcap")
    c.ev.registrar_existente("t26.pcap")
    _, ascii_ = L.ex("fw01-sim", "tcpdump -nn -A -r /tmp/t26.pcap 2>/dev/null | head -400")
    _, n = L.ex("fw01-sim", "tcpdump -nn -r /tmp/t26.pcap 2>/dev/null | wc -l")
    paquetes = int(n.strip() or 0)
    m.salidas["captura"] = ascii_
    m.medidas["paquetes_en_la_vpn"] = paquetes
    c.ev.guardar("captura.txt", ascii_)
    m.vacia = ("" if paquetes > 0 and re.search(r"(?i)celeris|10\.30\.10\.10", ascii_) else
               "durante el MISS no cruzó nada por la VPN: el nodo no tiene ruta al shield (REQ-F-29 pendiente), así que la ausencia de cabeceras no demuestra nada")
    m.hallazgos.append("F9 (EDGE → EC2-SHIELD) no se ejercita en un MISS real hasta que exista REQ-F-29; REQ-F-28 se prueba en e2e (Etapa 5)")
    return m


def t27(c: Contexto) -> Medicion:
    """Métricas cifradas: scraping obs01 → edge01:9128; captura en edge01; nada en claro y sin el token."""
    m = Medicion()
    edge, puerto = c.ip("EDGE01"), c.puerto("F12")
    token = L.leer("edge01", "/data/admin.token").strip()
    # el certificado de laboratorio del nodo se fija como ancla de confianza en obs01 (equivale a `--cacert` de Prometheus)
    L.enviar("obs01", "/tmp/admin-tls.crt", L.leer("edge01", "/data/ca/admin-tls.crt"))
    L.fondo("edge01", f"timeout 12 tcpdump -ni eth1 -w /tmp/t27.pcap 'host {c.ip('OBS01')} and port {puerto}'")
    time.sleep(1.5)
    m.medidas["esquema_https"] = 0
    for esquema, opcion in (("https", "--cacert /tmp/admin-tls.crt"), ("http", "")):
        rc, out = L.ex("obs01", f"curl -s -m6 {opcion} -H \"Authorization: Bearer {token}\" -o /dev/null -w '%{{http_code}}' {esquema}://{edge}:{puerto}/metrics")
        if rc == 0 and out.strip() == "200":
            m.medidas["esquema_https"] = 1 if esquema == "https" else 0
            break
    time.sleep(10)
    # fuera de la ventana de captura (y sin token): una petición HTTP en claro al mismo puerto no debe recibir ninguna respuesta
    rc_claro, resp_claro = L.ex("obs01", f"curl -s -m5 http://{edge}:{puerto}/healthz")
    m.medidas["respuestas_http_en_claro_del_servidor"] = 0 if (rc_claro != 0 and not resp_claro.strip()) else 1
    L.traer("edge01", "/tmp/t27.pcap", c.ev.dir / "t27.pcap")
    c.ev.registrar_existente("t27.pcap")
    _, ascii_ = L.ex("edge01", "tcpdump -nn -A -r /tmp/t27.pcap 2>/dev/null | head -300")
    _, http = L.ex("edge01", "tshark -r /tmp/t27.pcap -Y http 2>/dev/null | wc -l")
    _, tls = L.ex("edge01", "tshark -r /tmp/t27.pcap -Y tls.handshake 2>/dev/null | wc -l")
    enclaro = L.ex("edge01", f"grep -a -c '{token}' /tmp/t27.pcap")[1].strip()
    m.salidas["scrape.pcap"] = ascii_.replace(token, "<TOKEN>")
    m.medidas["paquetes_http_en_claro"] = int(http.strip() or 0)
    m.medidas["handshakes_tls"] = int(tls.strip() or 0)
    m.medidas["apariciones_del_token_en_la_captura"] = int(enclaro) if enclaro.isdigit() else -1
    c.ev.guardar("captura.txt", m.salidas["scrape.pcap"])
    if m.medidas["paquetes_http_en_claro"] > 0 or m.medidas["respuestas_http_en_claro_del_servidor"] > 0:
        m.hallazgos.append("el puerto 9128 sigue sirviendo HTTP en claro con el token en la cabecera Authorization: incumple REQ-NF-14 (hallazgo F12 de D1.11)")
    else:
        m.hallazgos.append("el puerto 9128 solo acepta TLS (REQ-NF-14); el certificado es autofirmado de laboratorio: en producción F12 usa los de step-ca (F11)")
    if m.medidas.get("apariciones_del_token_en_la_captura", 0) > 0:
        m.hallazgos.append("el token de administración aparece en claro en la captura")
    return m


CASOS = {"T05": t05, "T06": t06, "T07": t07, "T08": t08, "T09": t09, "T10": t10, "T11": t11, "T13": t13, "T14": t14, "T15": t15,
         "T16": t16, "T17": t17, "T18": t18, "T19": t19, "T20": t20, "T22": t22, "T24": t24, "T26": t26, "T27": t27}

TESTSSL_IMAGEN = "drwetter/testssl.sh@sha256:64bab3c1fd8eee440f68d5e020dd633c1f2d375fe0ae593bdfec2725110a7e29"   # 3.2
ZAP_IMAGEN = "ghcr.io/zaproxy/zaproxy@sha256:9624669db72f54d86c4b46a7064518bd9bf79d8c61a4c31befa9923489f328af"   # stable
