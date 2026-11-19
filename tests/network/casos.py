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
    "T23": "RA guard es un control del switch de acceso (SW-ACC, S-14); los puentes Linux del laboratorio no lo emulan",
    "T25": "ESX01, IPMI01, BRK01 y SW-CORE01 no se emulan: el puerto break-glass no existe en F4.1 (CI-16)",
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
    t08_navegador(c, m)
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
    t09_navegador(c, m)
    m.hallazgos.append("el navegador es Chromium sin pantalla con --ignore-certificate-errors (la CA del nodo no está en su almacén); el cliente imitado con curl se conserva como control")
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
    inicio = time.time()
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
    _alerta_wazuh(c, m, "100302", inicio)
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
    inicio = time.time()
    q = "https://%s/?q=%%27%%20OR%%201%%3D1--" % c.P["dominio_portal"]
    rc, out = L.ex("ext01", f"curl -sk -m8 --resolve {c.P['dominio_portal']}:443:{c.P['fw01_wan']} -o /dev/null -w '%{{http_code}}' '{q}'")
    m.codigos["principal"] = rc
    m.salidas["stdout"] = out.strip()
    time.sleep(1)
    audit = L.ex("waf01", "tail -c 6000 /var/log/modsec_audit.log 2>/dev/null")[1]
    c.ev.guardar("modsec_audit.log", audit)
    n = L.ex("waf01", "grep -c '\"transaction\"' /var/log/modsec_audit.log 2>/dev/null")[1].strip()
    m.medidas["eventos_modsecurity"] = int(n) if n.isdigit() else 0
    _alerta_wazuh(c, m, "100303", inicio)
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
    t22_navegador(c, m)
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
    # Lo que llega al motor del shield ya descifrado (el TLS termina en el shield): ahí se vería cualquier cabecera que identifique al cliente
    L.fondo("shield01", "timeout 12 tcpdump -ni lo -A -s 0 'tcp port 3128' > /tmp/t26-shield.txt 2>&1")
    time.sleep(1.5)
    ruta = f"/t26-{int(time.time())}.js"
    L.ex("labcli01", f"curl -s -m8 -x {px} --cacert {ca} -H 'X-Forwarded-For: {c.ip('LABCLI01')}' -H 'Via: 1.1 cliente-lab' -o /dev/null "
                     f"https://{c.P['dominio_origen']}{ruta}")
    time.sleep(11)
    L.traer("fw01-sim", "/tmp/t26.pcap", c.ev.dir / "t26.pcap")
    c.ev.registrar_existente("t26.pcap")
    _, ascii_ = L.ex("fw01-sim", "tcpdump -nn -A -r /tmp/t26.pcap 2>/dev/null | head -400")
    _, n = L.ex("fw01-sim", "tcpdump -nn -r /tmp/t26.pcap 2>/dev/null | wc -l")
    paquetes = int(n.strip() or 0)
    en_shield = L.leer("shield01", "/tmp/t26-shield.txt")
    m.salidas["captura"] = ascii_ + "\n--- en el shield, ya descifrado ---\n" + en_shield
    m.medidas["paquetes_en_la_vpn"] = paquetes
    c.ev.guardar("captura.txt", m.salidas["captura"])
    llego_al_shield = ruta in en_shield
    m.vacia = ("" if paquetes > 0 and llego_al_shield else
               "el MISS no llegó al shield (la captura del shield no contiene la petición): la ausencia de cabeceras no demuestra nada")
    m.hallazgos.append("F9 (EDGE → EC2-SHIELD) se ejercita con REQ-F-29: los MISS salen del nodo hacia el shield por la VPN con mTLS; en la VPN solo se ve TLS, "
                       "y por eso se mira también lo que llega al motor del shield ya descifrado")
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



# ---------------------------------------------------------------------------------------------------------------
# Ampliación T29+ (CI-27): las que tienen nodos en el laboratorio. Las demás son del Modo H.
# ---------------------------------------------------------------------------------------------------------------
PUERTOS_SONDA = "22,443"
NO_EMULADAS = "STORAGE y BACKUP no se emulan (F4.1 no tiene br-vlan70 ni br-vlan71, CI-16): sus celdas no se pudieron probar en el Modo L"


def _escuchas(nodos: dict[str, str], segundos: int = 90) -> None:
    """Abre los puertos 22 y 443 en cada nodo (control: sin un puerto abierto, que nmap no lo vea no demuestra nada)."""
    for clave, ip in nodos.items():
        nodo = clave.split("#")[0]
        L.enviar(nodo, "/tmp/escucha.py", TCP_ESCUCHA_PY)
        L.fondo(nodo, f"python3 /tmp/escucha.py {ip} 22 {segundos} & python3 /tmp/escucha.py {ip} 443 {segundos} & wait")
    time.sleep(1)


def _escaneo_denegado(c: Contexto, origen: str, destinos: dict[str, str], previo: str = "") -> Medicion:
    """nmap desde `origen` hacia un nodo de cada zona: ninguno debe tener un puerto abierto y FW01 debe contar denegaciones."""
    m = Medicion()
    _escuchas(destinos)
    controles = [L.ex(clave.split("#")[0], f"nc -zv -w2 {ip} 22")[0] for clave, ip in destinos.items()]
    antes = L.contador_nft("DENEGADO", "forward")
    rc, out = L.ex(origen, f"nmap -n -Pn -sS -p{PUERTOS_SONDA} --max-retries 1 --max-rtt-timeout 300ms {' '.join(destinos.values())}", timeout=180)
    despues = L.contador_nft("DENEGADO", "forward")
    c.ev.guardar("nmap.txt", out)
    m.codigos["principal"] = rc
    m.salidas["stdout"] = out
    m.medidas["puertos_open"] = len(re.findall(r"(?m)^\d+/tcp\s+open", out))
    m.medidas["paquetes_denegados_por_fw01"] = despues - antes
    if any(controles):
        m.vacia = f"el control positivo falló: algún destino no abre el puerto 22 ni desde su propio nodo ({controles})"
    return m


def _destinos_de_zonas(c: Contexto, zonas: list[str]) -> dict[str, str]:
    nodos = {"MGMT": ("jmp01", "JMP01"), "SERVERS": ("obs01", "OBS01"), "LAB": ("labcli01", "LABCLI01"), "LAB-TEST": ("kali01", "KALI01"),
             "SECURITY": ("ids01", "IDS01"), "EDGE": ("edge01", "EDGE01"), "STORAGE": ("nas01", "NAS01"), "BACKUP": ("nas01", "NAS01")}
    out = {}
    for z in zonas:
        if z in nodos:
            nodo = nodos[z][0]
            out[nodo if nodo not in out else f"{nodo}#{len(out)}"] = c.ip(nodos[z][1], z)      # NAS01 aparece dos veces: una por zona
    return out


def t29(c: Contexto) -> Medicion:
    """Escaneo desde KALI01 hacia SERVERS: FW01 lo deniega e IDS01 lo detecta en su captura de la VLAN 31."""
    m = Medicion()
    inicio = time.time()
    destinos = [c.ip("OBS01")]
    previas = int(L.ex("ids01", "grep -c '\"event_type\":\"alert\"' /var/log/suricata/eve.json")[1].strip() or 0)
    antes = L.contador_nft("DENEGADO", "forward")
    rc, out = L.ex("kali01", f"nmap -n -Pn -sS -p 1-1024 --max-rate 100 --max-retries 1 --max-rtt-timeout 300ms --host-timeout 150s {' '.join(destinos)}", timeout=400)
    time.sleep(5)
    despues = L.contador_nft("DENEGADO", "forward")
    eve = L.ex("ids01", f"grep '\"event_type\":\"alert\"' /var/log/suricata/eve.json | tail -n +{previas + 1} | tail -5")[1]
    c.ev.guardar("nmap.txt", out)
    c.ev.guardar("eve_ids01.json", eve)
    m.codigos["principal"] = rc
    m.salidas["stdout"] = out
    m.salidas["eve_json_ids01"] = eve
    m.medidas["puertos_open"] = len(re.findall(r"(?m)^\d+/tcp\s+open", out))
    m.medidas["paquetes_denegados_por_fw01"] = despues - antes
    _alerta_wazuh(c, m, "100300", inicio, filtro=r'10\.20\.31\.60')
    m.hallazgos.append("las reglas del laboratorio son locales (sid 9000001, escaneo SYN por origen): ET Open no está disponible en el Modo L")
    m.hallazgos.append("el destino es OBS01, el nodo de SERVERS que existe en el laboratorio y que ningún flujo alcanza desde LAB-TEST (SVC01 no sirve: F3 le abre el puerto 80)")
    return m


def t30(c: Contexto) -> Medicion:
    """Barrido de LABCLI01 hacia HNY02, en la misma VLAN: el canario lo registra y FW01 no ve ese tráfico."""
    m = Medicion()
    inicio = time.time()
    canario = c.ip("HNY02")
    L.ex("hny02", "truncate -s 0 /var/log/canary.json")
    L.enviar("fw01-sim", "/tmp/rx30.sh", f"timeout 40 tcpdump -ni vlan30 -c 1 'tcp and host {canario} and not port 1514' > /tmp/rx30.txt 2>&1\n")
    L.fondo("fw01-sim", "sh /tmp/rx30.sh")
    time.sleep(1)
    _, syn = L.ex("labcli01", f"nmap -n -Pn -sS -p 22,80,445,3389 --max-retries 1 {canario}", timeout=120)
    time.sleep(1)
    con_syn = len([linea for linea in L.leer("hny02", "/var/log/canary.json").splitlines() if "conexion" in linea])
    rc, out = L.ex("labcli01", f"nmap -n -Pn -sT -p 22,80,445,3389 --max-retries 1 {canario}", timeout=120)
    time.sleep(2)
    registro = L.leer("hny02", "/var/log/canary.json")
    visto = L.leer("fw01-sim", "/tmp/rx30.txt")
    L.ex("fw01-sim", "pkill tcpdump; true")
    c.ev.guardar("nmap.txt", out)
    c.ev.guardar("canary.json", registro)
    c.ev.guardar("tcpdump_fw01_vlan30.txt", visto)
    m.codigos["principal"] = rc
    m.salidas["stdout"] = out
    m.medidas["conexiones_registradas_en_hny02"] = len([linea for linea in registro.splitlines() if '"evento": "conexion"' in linea or '"evento":"conexion"' in linea])
    m.medidas["paquetes_vistos_por_fw01"] = len(re.findall(r"(?m)^\d\d:\d\d:\d\d", visto))
    _alerta_wazuh(c, m, "100301", inicio)
    m.hallazgos.append(f"el canario registró {con_syn} eventos con un barrido SYN (-sS) y {m.medidas['conexiones_registradas_en_hny02']} con uno de conexión completa (-sT): un canario de aplicación no ve los SYN sin respuesta; IDS01 no captura la VLAN 30 (D1.14)")
    m.hallazgos.append("el canario es un equivalente funcional de OpenCanary (F4.2): registra la conexión en un archivo, sin enviarla a un agente de Wazuh")
    return m


def t44(c: Contexto) -> Medicion:
    """Alcance IP entre EDGE01 y EDGE02 (VLAN 60). El puerto del peering no está definido (CI-06): no se prueba ninguno."""
    m = Medicion()
    uno, dos = c.ip("EDGE01"), c.ip("EDGE02")
    rc1, o1 = L.ex("edge01", f"ping -c 3 -W 2 {dos}")
    rc2, o2 = L.ex("edge02", f"ping -c 3 -W 2 {uno}")
    c.ev.guardar("ping.txt", o1 + "\n---\n" + o2)
    m.codigos[f"ping -c 3 {dos}"] = rc1
    m.codigos[f"ping -c 3 {uno}"] = rc2
    m.vacia = "el protocolo y el puerto del peering no están definidos (CI-06): solo se probó el alcance IP"
    return m


def t45(c: Contexto) -> Medicion:
    """Internet → zonas internas: ext01 enruta 10.20.0.0/16 por la WAN de FW01 y escanea un nodo de cada zona emulada."""
    wan = c.P["fw01_wan"]
    destinos = _destinos_de_zonas(c, ["MGMT", "SERVERS", "LAB", "LAB-TEST", "SECURITY", "EDGE", "STORAGE", "BACKUP"])
    try:
        L.ex("ext01", f"ip route replace 10.20.0.0/16 via {wan}")
        m = _escaneo_denegado(c, "ext01", destinos)
        rc_f21, _ = L.ex("ext01", f"nc -zv -w3 {wan} 443")
        if rc_f21 != 0 and not m.vacia:
            m.vacia = "el control positivo falló: ext01 no llega al puerto 443 publicado (F21), así que la ruta de prueba no es válida"
    finally:
        L.ex("ext01", "ip route del 10.20.0.0/16 via " + wan + "; true")
    return m


def t46(c: Contexto) -> Medicion:
    """DMZ-SVC → zonas internas: WEB01 «comprometido» (sin su cortafuegos de host) escanea un nodo de cada zona interna emulada."""
    destinos = _destinos_de_zonas(c, ["MGMT", "SERVERS", "LAB-TEST", "EDGE", "STORAGE", "BACKUP"])
    try:
        L.ex("web01", "nft flush ruleset")      # el cortafuegos de host de WEB01 bloquearía la salida por sí solo: no sería FW01 quien deniega
        m = _escaneo_denegado(c, "web01", destinos)
    finally:
        L.ex("web01", "nft -f /lab/web01.nft")
    m.hallazgos.append("WEB01 se probó como equipo comprometido, sin su nftables de host: con él, WEB01 ya no puede iniciar conexiones (D1.9, «Salida») y no sería FW01 quien deniega")
    return m


def t47(c: Contexto) -> Medicion:
    """DMZ-HONEY → cualquier zona: HNY01 escanea un nodo de cada zona y no llega a Internet (ext01)."""
    destinos = _destinos_de_zonas(c, ["MGMT", "SERVERS", "LAB-TEST", "EDGE", "STORAGE", "BACKUP"])
    ext = c.P["ext01"]
    L.enviar("ext01", "/tmp/escucha.py", TCP_ESCUCHA_PY)
    L.fondo("ext01", f"python3 /tmp/escucha.py {ext} 443 60")
    m = _escaneo_denegado(c, "hny01", destinos)
    rc_ctrl, _ = L.ex("ext01", f"nc -zv -w2 {ext} 443")
    rc_ext, _ = L.ex("hny01", f"nc -zv -w3 {ext} 443")
    m.codigos["curl -sS -m5 https://example.com"] = rc_ext
    if rc_ctrl != 0 and not m.vacia:
        m.vacia = "el control positivo falló: ext01 no escucha en 443 ni desde su propio nodo"
    m.codigos["nc -zv -w3 10.20.50.10 1514"], _ = L.ex("hny01", f"nc -zv -w3 {c.ip('SIEM01')} 1514")      # control positivo: F13 (agente → SIEM01)
    m.hallazgos.append("«Internet» es ext01 (198.51.100.100): el laboratorio no tiene DNS ni salida a Internet real")
    return m


"""Casos del Modo L con Wazuh, NAS01, shield con mTLS y navegador (Chromium sin pantalla). Se agrega a tests/network/casos.py."""

# ---------------------------------------------------------------------------------------------------------------
# Wazuh (siem01): alertas reales del manager, no simuladas
# ---------------------------------------------------------------------------------------------------------------
def _epoch_wazuh(ts: str) -> float:
    from datetime import datetime
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%f%z").timestamp()


def _alerta_wazuh(c: Contexto, m: Medicion, regla: str, desde: float, filtro: str = "", espera: int = 75) -> None:
    """Espera la alerta de la regla `regla` que Wazuh genera después de `desde` y la deja en las fuentes que miden los criterios
    (`alerta_wazuh`, `latencia_alerta_wazuh_s`). Sin alerta en `espera` s la fuente queda vacía: el criterio FALLA, no se omite."""
    fin = time.time() + espera
    encontradas: list[tuple[float, str]] = []
    while True:
        _, out = L._run(["docker", "exec", L.PREFIJO + "siem01-wazuh", "tail", "-n", "4000", "/var/ossec/logs/alerts/alerts.json"], 30)
        encontradas = []
        for linea in out.splitlines():
            if f'"id":"{regla}"' not in linea or (filtro and not re.search(filtro, linea)):
                continue
            ts = re.search(r'"timestamp":"([^"]+)"', linea)
            if ts and _epoch_wazuh(ts.group(1)) >= desde - 1:
                encontradas.append((_epoch_wazuh(ts.group(1)), linea))
        if encontradas or time.time() > fin:
            break
        time.sleep(3)
    m.salidas["alerta_wazuh"] = "\n".join(linea for _, linea in encontradas)
    m.medidas["latencia_alerta_wazuh_s"] = round(min(e for e, _ in encontradas) - desde, 1) if encontradas else 999
    c.ev.guardar(f"alerta_wazuh_{regla}.json", m.salidas["alerta_wazuh"] or "(sin alerta en %d s)" % espera)
    m.no_evaluable.pop("alerta_wazuh", None)


# ---------------------------------------------------------------------------------------------------------------
# Navegador real automatizado (Chromium sin pantalla dentro de labcli01)
# ---------------------------------------------------------------------------------------------------------------
CHROMIUM = ("chromium --headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage --no-first-run --ignore-certificate-errors "
            "--user-data-dir=/tmp/cr-{n} {extra} --dump-dom '{url}'")


def _navegar(c: Contexto, url: str, extra: str = "", espera: int = 90, perfil: str | None = None) -> tuple[int, float, str]:
    """Carga `url` con Chromium; devuelve (código, segundos, DOM). `extra` agrega opciones (PAC, QUIC, registro de red).
    Con `perfil` se reutiliza el perfil (el navegador recuerda lo aprendido, como el Alt-Svc) y no se borra."""
    n = perfil or str(int(time.time() * 1000) % 10**9)
    t = time.time()
    rc, out = L.ex("labcli01", CHROMIUM.format(n=n, extra=extra, url=url) + " 2>/dev/null", timeout=espera)
    if perfil is None:
        L.ex("labcli01", f"rm -rf /tmp/cr-{n}")
    return rc, round(time.time() - t, 1), out


def _peticiones_del_nodo(c: Contexto, nodo: str) -> int:
    """Peticiones que ha atendido un nodo EDGE (estadísticas de celeris-cache, F1)."""
    ip = c.ip(nodo.upper())
    _, out = L.ex("labcli01", f"curl -s -m5 -x http://{ip}:{c.puerto('F1')} http://celeris.stats/ | jq -r .requests")
    return int(out.strip()) if out.strip().isdigit() else -1


PAC_URL = "http://pac.celeris.internal/wpad.dat"


def t08_navegador(c: Contexto, m: Medicion) -> None:
    """Chromium con QUIC forzado hacia el origen: UDP 443 está bloqueado (F7), así que debe terminar por TCP/HTTP2."""
    dominio = c.P["dominio_generico"]
    L.ex("labcli01", "rm -rf /tmp/net.json /tmp/cr-t08")
    # El origen anuncia h3 (Alt-Svc). La primera visita lo aprende; en la segunda el navegador intenta QUIC por UDP 443, que F7 bloquea, y debe terminar por TCP.
    _navegar(c, f"https://{dominio}/t08-aprende", "--enable-quic", perfil="t08")
    rc, seg, dom = _navegar(c, f"https://{dominio}/t08-navegador", "--enable-quic --log-net-log=/tmp/net.json --net-log-capture-mode=Default", perfil="t08")
    _, net = L.ex("labcli01", "cat /tmp/net.json", timeout=60)
    c.ev.guardar("navegador_dom.html", dom)
    m.salidas["navegador"] = dom
    try:
        import json
        d = json.loads(net)
        tipos = {v: k for k, v in d["constants"]["logEventTypes"].items()}
        nombres = [tipos.get(e["type"], "") for e in d["events"]]
        m.medidas["paquetes_quic_recibidos"] = sum(1 for n in nombres if n == "QUIC_SESSION_PACKET_RECEIVED")
        m.medidas["conexiones_tcp"] = sum(1 for n in nombres if n == "TCP_CONNECT")
        m.medidas["intentos_quic"] = sum(1 for n in nombres if n.startswith("QUIC_SESSION"))
    except (ValueError, KeyError):
        m.no_evaluable["paquetes_quic_recibidos"] = "Chromium no escribió el registro de red"
        m.no_evaluable["conexiones_tcp"] = "Chromium no escribió el registro de red"


def t09_navegador(c: Contexto, m: Medicion) -> None:
    """Chromium con el PAC del laboratorio: con EDGE01 caído usa EDGE02 y, con ambos caídos, DIRECT. El origen ve la IP de quien le llega."""
    dominio = c.P["dominio_generico"]
    p1, p2 = c.puerta("EDGE01"), c.puerta("EDGE02")
    pac = f"--proxy-pac-url={PAC_URL}"
    try:
        rc0, t0, d0 = _navegar(c, f"https://{c.P['dominio_origen']}/t09-nav-base", pac)
        antes2 = _peticiones_del_nodo(c, "edge02")
        L.enlace("edge01", False)
        rc1, t1, d1 = _navegar(c, f"https://{c.P['dominio_origen']}/t09-nav-a", pac)
        despues2 = _peticiones_del_nodo(c, "edge02")
        L.enlace("edge02", False)
        rc2, t2, d2 = _navegar(c, f"https://{c.P['dominio_origen']}/t09-nav-b", pac, espera=120)
    finally:
        L.enlace("edge01", True, p1)
        L.enlace("edge02", True, p2)
    log = L.ex("ext01", "grep -E 't09-nav' /var/log/origen.log | tail -5")[1]
    c.ev.guardar("navegador.txt", f"normal ({t0}s) rc={rc0}\nEDGE01 caído ({t1}s) rc={rc1}\nambos caídos ({t2}s) rc={rc2}\norigen:\n{log}")
    m.salidas["navegador_con_edge01_caido"] = d1
    m.salidas["navegador_sin_nodos"] = d2
    directas = [linea for linea in log.splitlines() if "t09-nav-b" in linea]
    # DIRECT: el origen ve la IP de la WAN de FW01 (NAT de salida); si pasara por un nodo EDGE o por el shield vería otra (la de vgw-sim)
    m.salidas["registro_origen_directo"] = "salida=DIRECT" if any(f"origen {c.P['fw01_wan']} " in linea for linea in directas) else "\n".join(directas)
    m.medidas["tiempo_de_cambio_s"] = t1
    m.medidas["tiempo_hasta_direct_s"] = t2
    m.medidas["peticiones_nuevas_en_edge02_con_edge01_caido"] = despues2 - antes2 if antes2 >= 0 and despues2 >= 0 else -1


def t22_navegador(c: Contexto, m: Medicion) -> None:
    """Chromium con SVC01 caído: el DNS lo resuelve FW01 y la navegación sigue sin intervención."""
    puerta_svc = c.puerta("SVC01")
    resolv = L.leer("labcli01", "/etc/resolv.conf")
    try:
        L.ex("labcli01", "printf '%s\\noptions timeout:2 attempts:1\\n' \"$(cat /etc/resolv.conf)\" > /tmp/r && cat /tmp/r > /etc/resolv.conf")
        L.enlace("svc01", False)
        rc, seg, dom = _navegar(c, f"https://{c.P['dominio_origen']}/t22-navegador", f"--proxy-server=http://{c.ip('EDGE01')}:{c.puerto('F1')}")
    finally:
        L.enlace("svc01", True, puerta_svc)
        L.enviar("labcli01", "/etc/resolv.conf", resolv)
    c.ev.guardar("navegador_dom.html", dom)
    m.salidas["navegador"] = dom
    m.medidas["tiempo_navegador_con_svc01_caido_s"] = seg


# ---------------------------------------------------------------------------------------------------------------
# T12, T28, T31, T35, T39, T49: ahora con NAS01, siem01, el nodo con honey-URL, restic y el ACME de laboratorio
# ---------------------------------------------------------------------------------------------------------------
def t12(c: Contexto) -> Medicion:
    """STORAGE no enrutada: sin gateway ni ruta, ni LABCLI01 ni OBS01 alcanzan a NAS01 en la VLAN 70 (control: NAS01 sí escucha en 2049)."""
    m = Medicion()
    alm = c.ip("NAS01", "STORAGE")
    rc_ctrl, _ = L.ex("nas01", f"nc -zv -w2 {alm} 2049")
    rcs, perdidas = [], []
    for nodo in ("labcli01", "obs01"):
        rc, out = L.ex(nodo, f"ping -c 4 -W 2 {alm}")
        rcs.append(rc)
        perdidas.append(out)
        rc_t, _ = L.ex(nodo, f"nc -zv -w3 {alm} 2049")
        rcs.append(rc_t)
    c.ev.guardar("ping.txt", "\n---\n".join(perdidas))
    m.codigos["principal"] = 0 if 0 in rcs else 1
    m.salidas["stdout"] = perdidas[0]
    if rc_ctrl != 0:
        m.vacia = "el control positivo falló: NAS01 no escucha en el puerto 2049 de la VLAN 70 ni desde su propio nodo"
    m.hallazgos.append("NAS01 es un equivalente funcional (F4.2): sshd, restic y un puerto 2049 que no es NFS; el origen CTRL01 no se emula (se usan LABCLI01 y OBS01)")
    return m


def t28(c: Contexto) -> Medicion:
    """Syslog cifrado: un evento de FW01 llega a SIEM01 solo por TLS en 6514, sin UDP 514 (receptor de siem01 hacia el syslog local de Wazuh)."""
    m = Medicion()
    siem = c.ip("SIEM01")
    inicio = time.time()
    L.fondo("siem01", f"timeout 10 tcpdump -ni eth1 -w /tmp/t28.pcap 'host {c.ip('FW01', 'SECURITY')} and (udp port 514 or tcp port 6514)'")
    time.sleep(1.5)
    evento = "<134>fw01sim DENEGADO forward: T28 prueba de syslog por TLS"
    L.ex("fw01-sim", f"printf '%s\\n' '{evento}' | socat - OPENSSL:{siem}:6514,cafile=/pki/ca.pem,verify=0")
    time.sleep(13)
    _, udp = L.ex("siem01", "tcpdump -nn -r /tmp/t28.pcap 'udp port 514' 2>/dev/null | wc -l")
    _, tls = L.ex("siem01", "tcpdump -nn -r /tmp/t28.pcap 'tcp port 6514 and tcp[((tcp[12] & 0xf0) >> 2)] = 0x16' 2>/dev/null | wc -l")
    c.ev.guardar("syslog_tcpdump.txt", L.ex("siem01", "tcpdump -nn -r /tmp/t28.pcap 2>/dev/null | head -30")[1])
    m.medidas["paquetes_udp_514"] = 0 if udp.strip() == "0" else int(udp.strip() or 0)
    m.medidas["handshakes_tls_6514"] = int(tls.strip() or 0)
    m.salidas["tshark -r syslog.pcap -Y 'udp.port == 514'"] = ""
    _alerta_wazuh(c, m, "100304", inicio, espera=45)
    m.hallazgos.append("fw01-sim no es OPNsense y no tiene syslog nativo: el evento lo envía `socat` desde fw01-sim; lo que se prueba es el receptor de SIEM01 (solo TLS)")
    _, abierto = L.ex("siem01", "ss -uln | grep -c ':514 '")
    m.hallazgos.append(f"escuchas UDP en el puerto 514 de SIEM01: {abierto.strip() or '0'}")
    if abierto.strip() not in ("0", ""):
        m.medidas["paquetes_udp_514"] = 1
    if m.medidas["handshakes_tls_6514"] == 0:
        m.vacia = "no se vio ningún apretón de manos TLS en la captura"
    return m


def t31(c: Contexto) -> Medicion:
    """Honey-URL (REQ-F-27): pedir la ruta señuelo al nodo genera el evento honey_url y la alerta de Wazuh."""
    m = Medicion()
    ca = c.ca_del_nodo()
    px = f"http://{c.ip('EDGE01')}:{c.puerto('F1')}"
    inicio = time.time()
    rc, out = L.ex("labcli01", f"curl -sS -o /dev/null -w '%{{http_code}}' -x {px} --cacert {ca} https://{c.P['dominio_origen']}{c.P['honey_url']}")
    m.codigos["principal"] = rc
    m.salidas["stdout"] = out.strip()
    time.sleep(1.5)
    log = _nodo_edge_log(c)
    m.salidas["registro_celeris"] = log
    c.ev.guardar("registro_seguridad.jsonl", log)
    _alerta_wazuh(c, m, "100135", inicio)
    m.hallazgos.append(f"la ruta señuelo del laboratorio es {c.P['honey_url']} [S-17]; en S2 se define con el equipo")
    return m


def t35(c: Contexto) -> Medicion:
    """MGMT → Internet solo por 443: JMP01 llega a un origen de prueba por HTTPS; el puerto 22 y el HTTP en claro no deben abrir."""
    m = Medicion()
    dom = c.P["dominio_generico"]
    rc_https, code = L.ex("jmp01", f"curl -sS -m8 --cacert /pki/ca.pem --resolve {dom}:443:{c.P['ext01']} -o /dev/null -w '%{{http_code}}' https://{dom}/")
    m.salidas["stdout"] = code.strip()
    m.salidas["curl -sS -o /dev/null -w \"%{http_code}\" https://example.com"] = code.strip()
    m.codigos["nc -zv -w5 example.com 22"], _ = L.ex("jmp01", f"nc -zv -w5 {dom} 22")
    m.codigos["curl -sS -m5 http://example.com"], _ = L.ex("jmp01", f"curl -sS -m5 --resolve {dom}:80:{c.P['ext01']} http://{dom}/")
    return m


def t39(c: Contexto) -> Medicion:
    """Respaldo por SFTP (F17): OBS01 respalda en NAS01 por la VLAN 71 con restic, comprueba y restaura; LABCLI01 no llega a esa VLAN."""
    import secrets
    m = Medicion()
    nas = c.ip("NAS01", "BACKUP")
    usr, repo = c.P["restic_usuario"], c.P["restic_repositorio"]
    clave = secrets.token_hex(16)      # solo para este ensayo: se genera al vuelo y no se guarda en el repositorio
    nombre = f"t39-{int(time.time())}"
    ssh = f"ssh -i /root/.ssh/id_respaldo -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR {usr}@{nas} -s sftp"
    r = f"restic -r sftp:{usr}@{nas}:{repo}/{nombre} -o sftp.command='{ssh}'"
    pre = f"export RESTIC_PASSWORD={clave}; mkdir -p /root/.ssh /tmp/datos; install -m600 /pki/respaldo.key /root/.ssh/id_respaldo; "
    L.ex("obs01", pre + "head -c 4194304 /dev/urandom > /tmp/datos/a.bin; sha256sum /tmp/datos/a.bin > /tmp/datos.sha")
    rc_init, o_init = L.ex("obs01", pre + f"{r} init", timeout=120)
    rc_b, o_b = L.ex("obs01", pre + f"{r} backup /tmp/datos", timeout=180)
    rc_c, o_c = L.ex("obs01", pre + f"{r} check", timeout=180)
    inicio = time.time()
    rc_r, o_r = L.ex("obs01", pre + f"{r} restore latest --target /tmp/restaurado", timeout=180)
    m.medidas["tiempo_restauracion_s"] = round(time.time() - inicio, 1)
    _, ok = L.ex("obs01", "cd /tmp/restaurado/tmp/datos && sha256sum -c /tmp/datos.sha 2>&1 | tail -1; cd /; sha256sum /tmp/restaurado/tmp/datos/a.bin | cut -d' ' -f1; cut -d' ' -f1 /tmp/datos.sha")
    iguales = len(set(ok.split()[-2:])) == 1
    c.ev.guardar("restic.txt", "\n".join(re.sub(clave, "<clave>", x) for x in (o_init, o_b, o_c, o_r)))
    m.codigos["restic backup"] = rc_b if rc_init == 0 else rc_init
    m.salidas["stdout"] = o_c
    m.salidas["restic check"] = o_c
    rc_lab, _ = L.ex("labcli01", f"nc -zv -w3 {nas} 22")
    m.codigos["nc -zv -w3 10.20.71.20 22"] = rc_lab
    if not iguales:
        m.vacia = "la restauración no coincide con el original (sha256)"
    m.hallazgos.append("NAS01 es un equivalente funcional (F4.2): sshd + restic; la clave del repositorio se genera al vuelo y no se guarda")
    return m


def t49(c: Contexto) -> Medicion:
    """ACME desde WAF01 (F23): el directorio ACME de laboratorio de ext01 responde 200 por 443; el HTTP en claro hacia Internet no sale."""
    m = Medicion()
    acme = c.P["dominio_acme"]
    rc, out = L.ex("waf01", f"curl -sS -m8 --cacert /pki/ca.pem --resolve {acme}:443:{c.P['ext01']} -o /dev/null -w '%{{http_code}}' https://{acme}/directory")
    m.salidas["stdout"] = out.strip()
    m.salidas["curl -sS -o /dev/null -w \"%{http_code}\" https://acme-v02.api.letsencrypt.org/directory"] = out.strip()
    m.codigos["curl -sS -m5 http://example.com"], _ = L.ex("waf01", f"curl -sS -m5 --resolve {c.P['dominio_generico']}:80:{c.P['ext01']} http://{c.P['dominio_generico']}/")
    m.hallazgos.append("el directorio ACME es un servidor de laboratorio en ext01 (no Let's Encrypt, no emite certificados)")
    return m


CASOS = {"T05": t05, "T06": t06, "T07": t07, "T08": t08, "T09": t09, "T10": t10, "T11": t11, "T13": t13, "T14": t14, "T15": t15,
         "T16": t16, "T17": t17, "T18": t18, "T19": t19, "T20": t20, "T22": t22, "T24": t24, "T26": t26, "T27": t27,
         "T29": t29, "T30": t30, "T44": t44, "T45": t45, "T46": t46, "T47": t47,
         "T12": t12, "T28": t28, "T31": t31, "T35": t35, "T39": t39, "T49": t49}

TESTSSL_IMAGEN = "drwetter/testssl.sh@sha256:64bab3c1fd8eee440f68d5e020dd633c1f2d375fe0ae593bdfec2725110a7e29"   # 3.2
ZAP_IMAGEN = "ghcr.io/zaproxy/zaproxy@sha256:9624669db72f54d86c4b46a7064518bd9bf79d8c61a4c31befa9923489f328af"   # stable
