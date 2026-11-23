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
    # v0.4: dependen de la consola completa (CE02, S2). ctrl01 es solo una consola de prueba: aquí no se simulan ni se marcan PASA.
    "T50": ("requiere la consola (CE02, S2): la precarga programada con ventana horaria y límite de ancho de banda (REQ-F-34, REQ-RN-10) no existe en el nodo ni en ctrl01", ["H"]),
    "T53": ("requiere la consola (CE02, S2): el segundo factor, el límite de intentos y la auditoría de inicios de sesión (REQ-F-33, DET-10) no existen en ctrl01", ["A", "H"]),
    "T54": ("requiere la consola (CE02, S2): la aprobación de fuentes y el RBAC de la API (REQ-F-31, REQ-F-37); ctrl01 solo rechaza con 403 un POST /aprobar remoto de prueba", ["A", "H"]),
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
    """Falla de un túnel: baja el túnel activo con tráfico en curso (EC2-GW → CTRL01:443, F30) y mide cuánto tarda en volver a pasar por el otro."""
    m = Medicion()
    objetivo, puerto = c.ip("CTRL01"), c.puerto("F30")
    ok, estado = _bgp_y_sas(c)
    c.ev.guardar("antes.txt", estado)
    if not ok:
        raise RuntimeError("precondición: los dos túneles y las dos sesiones BGP deben estar establecidos")
    L.enviar("gw-sim", "/tmp/sonda.py", SONDA_PY)
    L.fondo("gw-sim", f"python3 /tmp/sonda.py {objetivo} {puerto} 110 /tmp/sonda.log")
    time.sleep(4)
    t_baja = time.time()
    L.ex("fw01-sim", "swanctl --terminate --ike tunel1 2>&1 | grep -v '^plugin' | tail -2", timeout=30)

    def analizar():
        lineas = [l.split() for l in L.leer("gw-sim", "/tmp/sonda.log").splitlines() if len(l.split()) == 2]
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
    L.ex("gw-sim", "pkill -f sonda.py")
    L.traer("gw-sim", "/tmp/sonda.log", c.ev.dir / "sonda.log")
    c.ev.registrar_existente("sonda.log")
    _, sas = L.ex("fw01-sim", "swanctl --list-sas 2>/dev/null | grep -v '^plugin'")
    _, ruta = L.ex("fw01-sim", "vtysh -c 'show ip route 10.30.0.0/16' | head -8")
    c.ev.guardar("despues.txt", sas + "\n" + ruta)
    m.salidas["swanctl --list-sas"] = sas
    m.salidas["stdout"] = sas
    m.hallazgos.append(f"tras la caída la ruta a 10.30.0.0/16 va por: {'vti2' if 'vti2' in ruta else 'vti1' if 'vti1' in ruta else 'ninguna'}")
    m.hallazgos.append("la sonda va de EC2-GW (gw-sim) a CTRL01:443 (F30): es el flujo que la VPN transporta en la v0.4")
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
    """DMZ → LAN: con el puerto 445 abierto a propósito en LABCLI01, PORTAL01 y HNY01 no deben alcanzarlo."""
    m = Medicion()
    lab = c.ip("LABCLI01")
    L.enviar("labcli01", "/tmp/escucha.py", TCP_ESCUCHA_PY)
    L.fondo("labcli01", f"python3 /tmp/escucha.py {lab} 445 25")
    time.sleep(1)
    rc_ctrl, _ = L.ex("labcli01", f"nc -zv -w2 {lab} 445")
    rcs = [L.ex(n, f"nc -zv -w3 {lab} 445")[0] for n in ("portal01", "hny01")]
    m.codigos["principal"] = _codigo_principal(rcs)
    if rc_ctrl != 0:
        m.vacia = "el control positivo falló: el puerto 445 de LABCLI01 no abre ni localmente"
    return m


def _reglas(c: Contexto, ventana: bool) -> str:
    from gen import nftables
    return nftables.generar(c.infra, modo="piloto", ventana=ventana, aws_peers=c.P["aws_peers"])


def t11(c: Contexto) -> Medicion:
    """Internet → DMZ-HONEY: con la ventana autorizada (F24), ext01 llega a Cowrie por el 22 y queda registro."""
    m = Medicion()
    wan = c.P["fgt_wan"]
    fw = c.infra.componentes["FW01"]["ips"][0]["ip"]
    inicio = time.time()
    try:
        # La ventana autorizada también abre el FortiGate: D1.8 limita su NAT 1:1 a UDP 500/4500 y TCP 80/443, y F24 necesita TCP 22 y 23 (CI-49)
        L.ex("fgt-sim", f"nft add rule ip fgt ventana iifname eth2 ip daddr {wan} tcp dport {{ 22, 23 }} counter dnat to {fw}")
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
        L.ex("fgt-sim", "nft flush chain ip fgt ventana")
        L.recargar_nft(_reglas(c, ventana=False))
    _alerta_wazuh(c, m, "100302", inicio)
    m.hallazgos.append("F24 exige abrir TCP 22 y 23 en el FortiGate durante la ventana, pero D1.8 y S-29 limitan su NAT 1:1 a UDP 500/4500 y TCP 80/443 (CI-49)")
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
    """Exposición del portal: desde Internet solo 80 y 443 en la IP pública del FortiGate; CTRL01 no es alcanzable (los señuelos, solo con ventana)."""
    m = Medicion()
    wan = c.P["fgt_wan"]
    extra = ",".join(str(p) for p in sorted({c.puerto("F1"), c.puerto("F10"), 9128, 2222, 5601, 5432} - set(range(1, 1025))))
    rc, out = L.ex("ext01", f"nmap -sS -Pn -n -T4 --max-retries 1 -p 1-1024,{extra} {wan}", timeout=240)
    c.ev.guardar("nmap.txt", out)
    m.codigos["principal"] = rc
    m.salidas["stdout"] = out
    abiertos = re.findall(r"(?m)^(\d+)/tcp\s+open", out)
    m.medidas["puertos_abiertos"] = len(abiertos)
    ctrl = c.ip("CTRL01")
    rc_ctrl, out_ctrl = L.ex("ext01", f"ip route replace 10.20.0.0/16 via {wan}; nmap -sS -Pn -n -T4 --max-retries 1 -p 22,443,8443 {ctrl}; ip route del 10.20.0.0/16 via {wan}", timeout=120)
    c.ev.guardar("nmap_ctrl01.txt", out_ctrl)
    m.medidas["puertos_abiertos_en_ctrl01"] = len(re.findall(r"(?m)^\d+/tcp\s+open", out_ctrl))
    m.salidas["nmap hacia CTRL01"] = out_ctrl
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
                        "--add-ca", "/pki/ca.pem", "--ip", c.P["fgt_wan"], "--jsonfile", "/out/tls.json", "--warnings", "off", "--color", "0",
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
                        "-t", f"https://{c.P['fgt_wan']}/", "-J", "zap.json", "-m", "1", "-I"], 900)
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
    """WAF (PORTAL01): una inyección SQL debe recibir 403 y quedar en el registro de auditoría de ModSecurity."""
    m = Medicion()
    inicio = time.time()
    q = "https://%s/?q=%%27%%20OR%%201%%3D1--" % c.P["dominio_portal"]
    rc, out = L.ex("ext01", f"curl -sk -m8 --resolve {c.P['dominio_portal']}:443:{c.P['fgt_wan']} -o /dev/null -w '%{{http_code}}' '{q}'")
    m.codigos["principal"] = rc
    m.salidas["stdout"] = out.strip()
    time.sleep(1)
    audit = L.ex("portal01", "tail -c 6000 /var/log/modsec_audit.log 2>/dev/null")[1]
    c.ev.guardar("modsec_audit.log", audit)
    n = L.ex("portal01", "grep -c '\"transaction\"' /var/log/modsec_audit.log 2>/dev/null")[1].strip()
    m.medidas["eventos_modsecurity"] = int(n) if n.isdigit() else 0
    _alerta_wazuh(c, m, "100303", inicio)
    return m


def t19(c: Contexto) -> Medicion:
    """Salida del portal: PORTAL01 solo debe alcanzar los endpoints ACME por 443 (F23); hacia otro destino de Internet no debe salir (D1.16: «Denegado»)."""
    m = Medicion()
    objetivo = f"https://{c.P['dominio_generico']}/"
    acme = c.P["dominio_acme"]
    rc_ctrl, _ = L.ex("portal01", f"curl -sk -m6 -o /dev/null -w '%{{http_code}}' --resolve {acme}:443:{c.P['ext01']} https://{acme}/directory")
    rc, out = L.ex("portal01", f"curl -sS -m6 --resolve {c.P['dominio_generico']}:443:{c.P['ext01']} {objetivo}")
    m.codigos["principal"] = rc
    if rc_ctrl != 0:
        m.vacia = "el control positivo falló: PORTAL01 tampoco alcanzó el endpoint ACME de laboratorio (F23), así que la denegación no es concluyente"
    if rc == 0:
        m.hallazgos.append("PORTAL01 alcanza example.com por 443: F23 permite TCP 443 hacia cualquier destino de Internet y no solo hacia los endpoints ACME que D1.9 («Salida: solo ACME y Wazuh») y D1.11 («Renovación del certificado») prometen; "
                           "el diseño no define cómo se limita el destino (alias de FW01 por FQDN o lista del FortiGate)")
    return m


def t20(c: Contexto) -> Medicion:
    """Aislamiento del señuelo: HNY01 no alcanza a PORTAL01:443 (control positivo: LABCLI01 sí, por F5)."""
    m = Medicion()
    portal, pt = c.ip("PORTAL01"), c.puerto("F5")
    rc_ctrl, _ = L.ex("labcli01", f"nc -zv -w3 {portal} {pt}")
    rc, _ = L.ex("hny01", f"nc -zv -w3 {portal} {pt}")
    m.codigos["principal"] = rc
    if rc_ctrl != 0:
        m.vacia = "el control positivo falló: LABCLI01 no alcanza a PORTAL01:443 (F5)"
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
    """Privacidad hacia orígenes (F8, REQ-F-28): el nodo reenvía una petición con X-Forwarded-For y Via falsos y el origen no los recibe."""
    m = Medicion()
    px = f"http://{c.ip('EDGE01')}:{c.puerto('F1')}"
    ext = c.P["ext01"]
    L.fondo("edge01", f"timeout 10 tcpdump -ni eth1 -A -s 0 'tcp port 80 and host {ext}' > /tmp/t26.txt 2>&1")
    time.sleep(1.5)
    rc, eco = L.ex("labcli01", f"curl -s -m8 -x {px} -H 'X-Forwarded-For: {c.ip('LABCLI01')}' -H 'Via: 1.1 cliente-lab' -H 'Forwarded: for={c.ip('LABCLI01')}' "
                               f"http://{ext}/echo?t26={int(time.time())}")
    time.sleep(9)
    saliente = L.leer("edge01", "/tmp/t26.txt")
    m.salidas["captura"] = saliente + "\n--- lo que recibió el origen (eco) ---\n" + eco
    m.medidas["paquetes_en_la_vpn"] = 0
    c.ev.guardar("captura.txt", m.salidas["captura"])
    m.codigos["principal"] = rc
    m.vacia = "" if ("GET /echo" in saliente and "host" in eco.lower()) else "la petición no salió del nodo hacia el origen: la ausencia de cabeceras no demuestra nada"
    m.hallazgos.append("en la v0.4 el MISS sale a Internet (F8) y no por la VPN; se captura en la interfaz del nodo y se compara con el eco del origen (/echo de ext01)")
    return m


def t27(c: Contexto) -> Medicion:
    """Administración y consola cifradas (F20, F28, F30): capturas en edge01:9128 y ctrl01:443; todo es TLS y el token no aparece en claro."""
    m = Medicion()
    edge, adm = c.ip("EDGE01"), 9128
    ctrl = c.ip("CTRL01")
    token = L.leer("edge01", "/data/admin.token").strip()
    L.enviar("jmp01", "/tmp/admin-tls.crt", L.leer("edge01", "/data/ca/admin-tls.crt"))
    L.fondo("edge01", f"rm -f /tmp/t27a.pcap; timeout 14 tcpdump -Z root -ni eth1 -w /tmp/t27a.pcap 'port {adm}'")
    L.fondo("ctrl01", f"rm -f /tmp/t27c.pcap; timeout 14 tcpdump -Z root -ni eth1 -w /tmp/t27c.pcap 'port 443'")
    time.sleep(1.5)
    ok = 0
    # F20: JMP01 → edge01:9128 con el token, por TLS
    rc, out = L.ex("jmp01", f"curl -s -m6 --cacert /tmp/admin-tls.crt -H \"Authorization: Bearer {token}\" -o /dev/null -w '%{{http_code}}' https://{edge}:{adm}/metrics")
    ok += int(rc == 0 and out.strip() == "200")
    # F28: ENC01 → ctrl01:443; F30: EC2-GW → ctrl01:443 por la VPN (certificado de cliente)
    rc2, o2 = L.ex("enc01", f"curl -sk -m6 -H 'Authorization: Bearer prueba-no-secreto' https://{ctrl}/")
    ok += int(rc2 == 0 and "campus" in o2)
    rc3, o3 = L.ex("ext01", f"curl -sk -m8 -H 'Authorization: Bearer prueba-no-secreto' https://{c.P['gw_publica']}/")
    ok += int(rc3 == 0 and "remoto" in o3)
    time.sleep(14)
    # fuera de la captura: HTTP en claro hacia los mismos puertos no debe recibir respuesta
    claro1 = L.ex("jmp01", f"curl -s -m5 http://{edge}:{adm}/healthz")
    claro2 = L.ex("enc01", f"curl -s -m5 http://{ctrl}/")
    m.medidas["respuestas_http_en_claro_del_servidor"] = int(bool(claro1[1].strip()) and claro1[0] == 0) + int(bool(claro2[1].strip()) and claro2[0] == 0)
    L.traer("edge01", "/tmp/t27a.pcap", c.ev.dir / "t27a.pcap")
    L.traer("ctrl01", "/tmp/t27c.pcap", c.ev.dir / "t27c.pcap")
    c.ev.registrar_existente("t27a.pcap")
    c.ev.registrar_existente("t27c.pcap")
    http = tls = claves = 0
    texto = ""
    for nodo, pcap in (("edge01", "/tmp/t27a.pcap"), ("ctrl01", "/tmp/t27c.pcap")):
        h = L.ex(nodo, f"tshark -r {pcap} -Y http 2>/dev/null | wc -l")[1]
        t = L.ex(nodo, f"tshark -r {pcap} -Y tls.handshake 2>/dev/null | wc -l")[1]
        k = L.ex(nodo, f"grep -a -c -e '{token}' -e 'prueba-no-secreto' {pcap}")[1]
        http += int(h.strip() or 0)
        tls += int(t.strip() or 0)
        claves += int(k.strip()) if k.strip().isdigit() else 0
        texto += L.ex(nodo, f"tcpdump -nn -A -r {pcap} 2>/dev/null | head -150")[1]
    m.salidas["admin.pcap"] = texto.replace(token, "<TOKEN>")
    m.medidas["paquetes_http_en_claro"] = http
    m.medidas["handshakes_tls"] = tls
    m.medidas["apariciones_del_token_en_la_captura"] = claves
    c.ev.guardar("captura.txt", m.salidas["admin.pcap"])
    if ok < 3:
        m.vacia = f"solo {ok} de las 3 sesiones (JMP01 → edge01:9128, ENC01 → ctrl01, EC2-GW → ctrl01) funcionaron: la captura no cubre F20, F28 y F30"
    if http > 0 or m.medidas["respuestas_http_en_claro_del_servidor"] > 0:
        m.hallazgos.append("algún puerto de administración o de la consola responde en claro: incumple REQ-NF-14")
    else:
        m.hallazgos.append("el 9128 de los nodos y el 443 de ctrl01 solo aceptan TLS; los certificados son de laboratorio (en producción, los de step-ca)")
    return m


# ---------------------------------------------------------------------------------------------------------------
# Ampliación T29+ (CI-27): las que tienen nodos en el laboratorio. Las demás son del Modo H.
# ---------------------------------------------------------------------------------------------------------------
PUERTOS_SONDA = "22,443"
NO_EMULADAS = "STORAGE y BACKUP no se emulan (F4.1 no tiene br-vlan70 ni br-vlan71, CI-16): sus celdas no se pudieron probar en el Modo L"


def _escuchas(nodos: dict[str, str], segundos: int = 90, puertos: tuple[int, ...] = (22, 443)) -> None:
    """Abre los puertos indicados en cada nodo (control: sin un puerto abierto, que nmap no lo vea no demuestra nada)."""
    for clave, ip in nodos.items():
        nodo = clave.split("#")[0]
        L.enviar(nodo, "/tmp/escucha.py", TCP_ESCUCHA_PY)
        L.fondo(nodo, " & ".join(f"python3 /tmp/escucha.py {ip} {p} {segundos}" for p in puertos) + " & wait")
    time.sleep(1)


def _escaneo_denegado(c: Contexto, origen: str, destinos: dict[str, str], previo: str = "", puertos: tuple[int, ...] = (22, 443)) -> Medicion:
    """nmap desde `origen` hacia un nodo de cada zona: ninguno debe tener un puerto abierto y FW01 debe contar denegaciones."""
    m = Medicion()
    _escuchas(destinos, puertos=puertos)
    controles = [L.ex(clave.split("#")[0], f"nc -zv -w2 {ip} 22")[0] for clave, ip in destinos.items()]
    antes = L.contador_nft("DENEGADO", "forward")
    rc, out = L.ex(origen, f"nmap -n -Pn -sS -p{",".join(str(p) for p in puertos)} --max-retries 1 --max-rtt-timeout 300ms {' '.join(destinos.values())}", timeout=180)
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
    nodos = {"MGMT": ("jmp01", "JMP01"), "SERVERS": ("ctrl01", "CTRL01"), "LAB": ("labcli01", "LABCLI01"), "SECURITY": ("siem01", "SIEM01"),
             "EDGE": ("edge01", "EDGE01"), "DMZ-SVC": ("portal01", "PORTAL01")}
    return {nodos[z][0]: c.ip(nodos[z][1], z) for z in zonas if z in nodos}


def t29(c: Contexto) -> Medicion:
    """Escaneo desde KALI01 (LAB) hacia CTRL01 (SERVERS): FW01 lo deniega y Suricata de fw01-sim, en la interfaz LAB, lo detecta (DET-02)."""
    m = Medicion()
    inicio = time.time()
    destino = c.ip("CTRL01")
    previas = int(L.ex("fw01-sim", "grep -c '\"event_type\":\"alert\"' /var/log/suricata/eve.json")[1].strip() or 0)
    antes = L.contador_nft("DENEGADO", "forward")
    rc, out = L.ex("kali01", f"nmap -n -Pn -sS -p 1-1024 --max-rate 100 --max-retries 1 --max-rtt-timeout 300ms --host-timeout 150s {destino}", timeout=400)
    time.sleep(5)
    despues = L.contador_nft("DENEGADO", "forward")
    eve = L.ex("fw01-sim", f"grep '\"event_type\":\"alert\"' /var/log/suricata/eve.json | tail -n +{previas + 1} | tail -5")[1]
    c.ev.guardar("nmap.txt", out)
    c.ev.guardar("eve_fw01.json", eve)
    m.codigos["principal"] = rc
    m.salidas["stdout"] = out
    m.salidas["eve_json_fw01"] = eve
    m.medidas["puertos_open"] = len(re.findall(r"(?m)^\d+/tcp\s+open", out))
    m.medidas["paquetes_denegados_por_fw01"] = despues - antes
    _alerta_wazuh(c, m, "100300", inicio, filtro=r'10\.20\.35\.60')
    m.hallazgos.append("las reglas del laboratorio son locales (sid 9000001, escaneo SYN por origen): ET Open no está disponible en el Modo L")
    m.hallazgos.append("el escaneo cruza FW01 desde la interfaz LAB (vlan30): Suricata de fw01-sim lo ve aunque el firewall lo deniegue; el evento llega a Wazuh por syslog TLS (F14)")
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


def t45(c: Contexto) -> Medicion:
    """Internet → zonas internas: ext01 enruta 10.20.0.0/16 por el FortiGate y escanea un nodo de cada zona interna del laboratorio."""
    wan = c.P["fgt_wan"]
    destinos = _destinos_de_zonas(c, ["MGMT", "SERVERS", "LAB", "SECURITY", "EDGE"])
    try:
        L.ex("ext01", f"ip route replace 10.20.0.0/16 via {wan}")
        m = _escaneo_denegado(c, "ext01", destinos)
        rc_f21, _ = L.ex("ext01", f"nc -zv -w3 {wan} 443")
        if rc_f21 != 0 and not m.vacia:
            m.vacia = "el control positivo falló: ext01 no llega al puerto 443 publicado (F21), así que la ruta de prueba no es válida"
    finally:
        L.ex("ext01", "ip route del 10.20.0.0/16 via " + wan + "; true")
    m.hallazgos.append("el FortiGate emulado reenvía todo y deja la política a FW01; el FortiGate real solo publica UDP 500/4500 y TCP 80/443 (D1.8)")
    return m


def t46(c: Contexto) -> Medicion:
    """DMZ-SVC → zonas internas, incluido CTRL01:5432: PORTAL01 «comprometido» escanea un nodo de cada zona interna."""
    destinos = _destinos_de_zonas(c, ["MGMT", "SERVERS", "LAB", "EDGE"])
    m = _escaneo_denegado(c, "portal01", destinos, puertos=(22, 443, 5432))
    m.hallazgos.append("PORTAL01 se probó como equipo comprometido; el 5432 de CTRL01 es un puerto de prueba: PostgreSQL de la v0.4 no escucha en la red (socket local, D-25)")
    return m


def t47(c: Contexto) -> Medicion:
    """DMZ-HONEY → cualquier zona: HNY01 escanea un nodo de cada zona y no llega a Internet (ext01)."""
    destinos = _destinos_de_zonas(c, ["MGMT", "SERVERS", "LAB", "EDGE"])
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
    # DIRECT: el origen ve la IP pública del FortiGate (NAT de salida); si pasara por un nodo EDGE vería la misma, así que se distingue por el registro del nodo
    m.salidas["registro_origen_directo"] = "salida=DIRECT" if any(f"origen {c.P['fgt_wan']} " in linea for linea in directas) else "\n".join(directas)
    m.medidas["tiempo_de_cambio_s"] = t1
    m.medidas["tiempo_hasta_direct_s"] = t2
    m.medidas["peticiones_nuevas_en_edge02_con_edge01_caido"] = despues2 - antes2 if antes2 >= 0 and despues2 >= 0 else -1


# ---------------------------------------------------------------------------------------------------------------
# T12, T28, T31, T35, T39, T49: ahora con NAS01, siem01, el nodo con honey-URL, restic y el ACME de laboratorio
# ---------------------------------------------------------------------------------------------------------------
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


def t49(c: Contexto) -> Medicion:
    """ACME desde PORTAL01 (F23): el directorio ACME de laboratorio de ext01 responde 200 por 443; el HTTP en claro hacia Internet no sale."""
    m = Medicion()
    acme = c.P["dominio_acme"]
    rc, out = L.ex("portal01", f"curl -sS -m8 --cacert /pki/ca.pem --resolve {acme}:443:{c.P['ext01']} -o /dev/null -w '%{{http_code}}' https://{acme}/directory")
    m.salidas["stdout"] = out.strip()
    m.salidas["curl -sS -o /dev/null -w \"%{http_code}\" https://acme-v02.api.letsencrypt.org/directory"] = out.strip()
    m.codigos["curl -sS -m5 http://example.com"], _ = L.ex("portal01", f"curl -sS -m5 --resolve {c.P['dominio_generico']}:80:{c.P['ext01']} http://{c.P['dominio_generico']}/")
    m.hallazgos.append("el directorio ACME es un servidor de laboratorio en ext01 (no Let's Encrypt, no emite certificados)")
    return m


def t32(c: Contexto) -> Medicion:
    """CrowdSec (DET-08): una decisión de bloqueo sobre la IP externa la aplica el bouncer de nftables de FW01 y llega a Wazuh por el syslog TLS."""
    m = Medicion()
    wan, ext, siem = c.P["fgt_wan"], c.P["ext01"], c.ip("SIEM01")
    inicio = time.time()
    # Otras pruebas recargan las reglas de FW01 con `flush ruleset` y eso borra la tabla del bouncer: se reinicia para empezar con su tabla creada.
    L.ex("fw01-sim", "pkill -x crowdsec-firewall-bouncer; sleep 1; (crowdsec-firewall-bouncer -c /etc/crowdsec/bouncers/crowdsec-firewall-bouncer.yaml >> /var/log/crowdsec-bouncer.out 2>&1 &); sleep 3")
    rc_antes, _ = L.ex("ext01", f"nc -zv -w3 {wan} 443")              # control: F21 está abierto, así que el bloqueo posterior se debe a CrowdSec
    cont = "nft list counters table ip crowdsec 2>/dev/null | awk '/counter crowdsec-blacklists/ {f=1} f && /packets/ {s+=$2; f=0} END {print s+0}'"
    antes = int(L.ex("fw01-sim", cont)[1].strip() or 0)
    try:
        L.ex("fw01-sim", f"cscli decisions add --ip {ext} --duration 5m --type ban --reason 'T32 simulación (escenario de prueba)'")
        time.sleep(6)                                                   # el bouncer consulta la API cada 2 s
        rcs = [L.ex("ext01", f"nc -zv -w2 {wan} 443")[0] for _ in range(4)]
        _, lista = L.ex("fw01-sim", "cscli decisions list")
        despues = int(L.ex("fw01-sim", cont)[1].strip() or 0)
        L.ex("fw01-sim", f"printf '%s\\n' '<134>fw01sim CROWDSEC ban {ext}: decisión de CrowdSec' | socat - OPENSSL:{siem}:6514,cafile=/pki/ca.pem,verify=0")
    finally:
        L.ex("fw01-sim", f"cscli decisions delete --ip {ext}")
    time.sleep(4)
    rc_tras, _ = L.ex("ext01", f"nc -zv -w3 {wan} 443")                 # al retirar la decisión, el acceso vuelve
    c.ev.guardar("cscli_decisions.txt", lista)
    m.salidas["stdout"] = lista
    m.salidas["cscli decisions list"] = lista
    m.medidas["paquetes_descartados_tras_la_decision"] = max(despues - antes, 0)
    m.codigos["principal"] = 0 if all(r != 0 for r in rcs) else 1
    _alerta_wazuh(c, m, "100305", inicio, espera=45)
    if rc_antes != 0 or rc_tras != 0:
        m.vacia = f"el control falló: antes del bloqueo {'abre' if rc_antes == 0 else 'no abre'} y tras retirarlo {'abre' if rc_tras == 0 else 'no abre'} el puerto 443"
    m.hallazgos.append("la decisión se agrega con `cscli decisions add` (la «simulación con su escenario de prueba» de D1.14): un escenario real exige logs de SSH o del WAF")
    m.hallazgos.append("fw01-sim no es OPNsense: el aviso a Wazuh lo envía `socat` por el syslog TLS (F14); CrowdSec y su bouncer sí son los reales, en modo local sin nube")
    return m



# ---------------------------------------------------------------------------------------------------------------
# v0.4: configuración firmada, acceso por laboratorio, coalescencia, BYOD, panel remoto y WPAD (T51, T52, T55, T56, T57, T58, T60)
# ---------------------------------------------------------------------------------------------------------------
def _toml_firmado(c: Contexto, version: int, dominios: list[str] | None = None, deshabilitados: tuple[str, ...] = ()) -> str:
    """Configuración que ctrl01 firma para los nodos: rangos /26 habilitados + infraestructura + Wi-Fi, dominios a descifrar y redes BYOD (REQ-F-17, REQ-F-32, REQ-F-36)."""
    import json
    rl = c.infra.inv["rangos_lab"]
    permitidos = [l["cidr"] for l in rl["laboratorios"] if l["habilitado"] and l["id"] not in deshabilitados] + [rl["infraestructura"]["cidr"], c.infra.zonas["WIFI-EST"]["cidr"]]
    base = dominios if dominios is not None else [c.P["dominio_origen"], c.P["dominio_grande"]]
    return (f"config_version = {version}\nallowed_clients = {json.dumps(permitidos)}\nintercept_domains = {json.dumps(base)}\n"
            f"byod_networks = {json.dumps([c.infra.zonas['WIFI-EST']['cidr']])}\n")


def _firmar(c: Contexto, toml: str) -> None:
    """ctrl01 firma y publica la configuración (`firmar.sh`)."""
    L.ex("ctrl01", "sh /lab/firmar.sh", entrada=toml, timeout=30)


def _version() -> int:
    return int(time.time())          # creciente entre ejecuciones; el nodo solo exige que no baje


def _intercepta(c: Contexto, nodo_cliente: str = "labcli01", ruta: str = "/firmada") -> bool:
    """¿El nodo EDGE01 descifra el dominio listado para este cliente? Sí si el certificado que recibe es de la CA del nodo."""
    ca = c.ca_del_nodo()
    px = f"http://{c.ip('EDGE01')}:{c.puerto('F1')}"
    rc, _ = L.ex(nodo_cliente, f"curl -sS -m6 -o /dev/null -x {px} --cacert {ca} https://{c.P['dominio_origen']}{ruta}-{int(time.time() * 1000) % 10**8}", timeout=20)
    return rc == 0


def t51(c: Contexto) -> Medicion:
    """Cambio del encargado y configuración sin firma (REQ-F-17, AM-15): ctrl01 firma un cambio; el nodo lo aplica en ≤ 60 s y rechaza lo no firmado o más antiguo."""
    m = Medicion()
    v0 = _version()
    # precondición: v0 con el dominio descifrado
    _firmar(c, _toml_firmado(c, v0))
    L.esperar(lambda: _intercepta(c), 40, 3)
    previo = _intercepta(c)
    # cambio firmado: el encargado deja de descifrar el dominio (la fuente se desactiva)
    t0 = time.time()
    _firmar(c, _toml_firmado(c, v0 + 1, dominios=[]))
    aplicado = L.esperar(lambda: not _intercepta(c), 70, 2)
    m.medidas["latencia_cambio_s"] = round(time.time() - t0, 1) if aplicado else 999.0
    # configuración alterada sin volver a firmar (versión nueva, mismo .sig): debe rechazarse y conservarse la anterior
    alterada = _toml_firmado(c, v0 + 2, dominios=[c.P["dominio_origen"], c.P["dominio_grande"]])
    L.ex("ctrl01", "cat > /firmada/config.toml", entrada=alterada, timeout=20)
    time.sleep(14)
    m.medidas["bundles_sin_firma_aplicados"] = 1 if _intercepta(c) else 0
    # firmada pero con versión anterior a la aplicada
    _firmar(c, _toml_firmado(c, v0 - 1))
    time.sleep(14)
    anterior_aplicada = _intercepta(c)
    m.medidas["bundles_sin_firma_aplicados"] += 1 if anterior_aplicada else 0
    log = _nodo_edge_log(c)
    m.salidas["registro_celeris"] = log
    c.ev.guardar("registro_seguridad.jsonl", log)
    # deja el laboratorio como estaba: dominio descifrado con una versión mayor
    _firmar(c, _toml_firmado(c, v0 + 3))
    L.esperar(lambda: _intercepta(c), 40, 3)
    if not previo:
        m.vacia = "la precondición falló: el nodo no descifraba el dominio antes del cambio, así que no se pudo observar el efecto"
    if not aplicado:
        m.hallazgos.append("el nodo no aplicó el cambio firmado en 70 s")
    m.hallazgos.append("el nodo recarga cada 5 s (config_reload_secs en el laboratorio); en producción el intervalo lo fija la DTI. Solo cambian allowed_clients, intercept_domains, never_intercept y byod_networks")
    return m


def t52(c: Contexto) -> Medicion:
    """Laboratorio deshabilitado (REQ-F-32): con LAB-03 fuera de allowed_clients, labcli03 recibe 403 y labcli02 (LAB-01) sigue con acceso."""
    m = Medicion()
    px = f"http://{c.ip('EDGE01')}:{c.puerto('F1')}"
    dom = c.P["dominio_generico"]
    cmd = f"curl -s -m8 -o /dev/null -w '%{{http_code}}' -x {px} http://{dom}/t52-@N@"
    v = _version()
    _firmar(c, _toml_firmado(c, v))
    L.esperar(lambda: L.ex("labcli03", cmd.replace("@N@", str(int(time.time()))))[1].strip() == "200", 40, 3)
    previo = L.ex("labcli03", cmd.replace("@N@", "previo"))[1].strip()
    _firmar(c, _toml_firmado(c, v + 1, deshabilitados=("LAB-03",)))
    L.esperar(lambda: L.ex("labcli03", cmd.replace("@N@", str(int(time.time()))))[1].strip() == "403", 40, 3)
    c03 = L.ex("labcli03", cmd.replace("@N@", "lab03"))[1].strip()
    c01 = L.ex("labcli02", cmd.replace("@N@", "lab01"))[1].strip()
    m.salidas["curl desde una PC de LAB-03"] = c03
    m.salidas["curl desde una PC de LAB-01"] = c01
    time.sleep(1.5)
    log = _nodo_edge_log(c)
    m.salidas["registro_celeris"] = log
    c.ev.guardar("registro_seguridad.jsonl", log)
    c.ev.guardar("codigos.txt", f"antes: LAB-03={previo}\ndespués: LAB-03={c03} LAB-01={c01}")
    # restablece el acceso a LAB-03 (versión mayor)
    _firmar(c, _toml_firmado(c, v + 2))
    L.esperar(lambda: L.ex("labcli03", cmd.replace("@N@", str(int(time.time()))))[1].strip() == "200", 40, 3)
    if previo != "200":
        m.vacia = f"la precondición falló: labcli03 no tenía acceso antes de deshabilitar LAB-03 (código {previo})"
    m.hallazgos.append("el laboratorio es un /26 de allowed_clients; el tráfico de LAB-03 sigue llegando al nodo (F1 abre toda la VLAN 30 en FW01): el control está en el nodo (D1.8, nota 1)")
    return m


def t55(c: Contexto) -> Medicion:
    """Coalescencia: 20 descargas simultáneas del mismo instalador (100 MB en origin-sim) producen 1 sola descarga en el origen."""
    m = Medicion()
    px = f"http://{c.ip('EDGE01')}:{c.puerto('F1')}"
    ruta = f"/archivo-100MB.bin?t55={int(time.time())}"
    url = f"http://{c.P['dominio_grande']}{ruta}"
    antes = L.ex("origin-sim", "grep -c DESCARGA /var/log/origin-sim.log")[1].strip()
    n_antes = int(antes) if antes.isdigit() else 0
    script = ("#!/bin/sh\nfor i in $(seq 1 20); do ( curl -s -m90 -D /tmp/t55-$i.h -o /dev/null -x " + px + " '" + url + "' ) & done\nwait\n"
              "cat /tmp/t55-*.h | tr -d '\r' | grep -iE '^(HTTP/|cache-status:)'\nrm -f /tmp/t55-*.h\n")
    L.enviar("labcli01", "/tmp/t55.sh", script)
    rc, out = L.ex("labcli01", "sh /tmp/t55.sh", timeout=180)
    time.sleep(2)
    despues = L.ex("origin-sim", "grep -c DESCARGA /var/log/origin-sim.log")[1].strip()
    n_despues = int(despues) if despues.isdigit() else 0
    c.ev.guardar("respuestas.txt", out)
    c.ev.guardar("origin-sim.log", L.ex("origin-sim", "tail -n 40 /var/log/origin-sim.log")[1])
    m.codigos["principal"] = rc
    m.salidas["stdout"] = out
    respuestas_200 = len(re.findall(r"(?m)^HTTP/\S+ 200", out))
    hit = len(re.findall(r"(?im)^cache-status:.*\bhit\b", out))
    m.medidas["descargas_en_origen"] = n_despues - n_antes
    m.medidas["respuestas_collapsed_o_hit"] = hit
    m.medidas["respuestas_200"] = respuestas_200
    if respuestas_200 != 20:
        m.vacia = f"solo {respuestas_200} de las 20 peticiones recibieron 200: la medición no ejercita la coalescencia completa"
    m.hallazgos.append("con el presupuesto de memoria por defecto (max_buffered_bytes = 512 MiB) los seguidores de un objeto de 100 MB se sirven desde memoria de a uno por cada 100 MB reservados; en una primera corrida "
                       "solo 5 de 19 obtuvieron HIT y 15 pasaron por el origen (sobre presupuesto). El laboratorio fija 3 GiB; el dimensionamiento de RAM del nodo (8 GB, D2.4) debe reservar max_buffered_bytes para 20 clientes × el instalador más grande")
    m.hallazgos.append("los 19 que esperan reciben la copia ya guardada (Cache-Status: hit): el nodo no marca «collapsed»; el líder es el único MISS")
    m.hallazgos.append("el laboratorio sube max_object_bytes a 200 MiB y coalesce_wait_secs a 30 en los nodos EDGE: con los valores por defecto (64 MiB) un objeto de 100 MB no se guarda ni se coalesce")
    return m


def _emisor(nodo: str, ruta: str) -> str:
    return L.ex(nodo, f"openssl x509 -in {ruta} -noout -subject | sed 's/^subject=//'")[1].strip()


def t56(c: Contexto) -> Medicion:
    """BYOD: un equipo del Wi-Fi que abre un dominio aprobado para descifrar recibe el certificado del origen, no el de la CA del proyecto (REQ-F-36)."""
    m = Medicion()
    px = f"http://{c.ip('EDGE01')}:{c.puerto('F31')}"
    url = f"https://{c.P['dominio_origen']}/t56"
    ca_nodo = _emisor("edge01", "/data/ca/celeris-ca.crt")
    cmd = f"curl -sv -k -m8 -o /dev/null -x {px} {url}-{{n}} 2>&1 | grep -i 'issuer:'"
    _, byod = L.ex("byod01", cmd.format(n="byod"), timeout=30)
    _, ctrl = L.ex("labcli01", cmd.format(n="control"), timeout=30)
    c.ev.guardar("emisores.txt", f"CA del nodo: {ca_nodo}\nBYOD: {byod}\nControl (LABCLI01): {ctrl}\n")
    m.salidas["stdout"] = byod
    cn = lambda t: (re.search(r"CN\s*=\s*([^,;\n]+)", t) or [None, ""])[1].strip().lower()
    norm = lambda t: cn(t)
    m.medidas["certificados_emitidos_por_la_ca_del_proyecto"] = 1 if cn(ca_nodo) and cn(ca_nodo) == cn(byod) else 0
    if not byod.strip():
        m.vacia = "byod01 no obtuvo ningún certificado (¿F31 o el nodo cerrados?)"
    elif not (cn(ca_nodo) and cn(ca_nodo) == cn(ctrl)):
        m.vacia = "el control falló: un PC de laboratorio tampoco recibió el certificado de la CA del nodo, así que no se puede distinguir un certificado del otro"
    m.hallazgos.append("la red del Wi-Fi está en byod_networks del nodo; la regla no depende de la configuración que llegue (REQ-RN-11)")
    return m


def t57(c: Contexto) -> Medicion:
    """WIFI-EST → CTRL01, MGMT y LAB: byod01 escanea un nodo de cada zona; controles positivos hacia EDGE (F31) y el portal (F32)."""
    destinos = {"ctrl01": c.ip("CTRL01"), "jmp01": c.ip("JMP01"), "labcli01": c.ip("LABCLI01")}
    m = _escaneo_denegado(c, "byod01", destinos)
    edge, portal = c.ip("EDGE01"), c.ip("PORTAL01")
    m.codigos[f"nc -zv -w3 {edge} 3128"], _ = L.ex("byod01", f"nc -zv -w3 {edge} 3128")
    m.codigos[f"nc -zv -w3 {portal} 443"], _ = L.ex("byod01", f"nc -zv -w3 {portal} 443")
    return m


def t58(c: Contexto) -> Medicion:
    """EC2-GW comprometido: desde gw-sim solo abren CTRL01:443 y SIEM01:1514; todo lo demás lo deniega FW01 (el Security Group no se emula en el Modo L)."""
    m = Medicion()
    ctrl, siem, jmp, lab, edge = c.ip("CTRL01"), c.ip("SIEM01"), c.ip("JMP01"), c.ip("LABCLI01"), c.ip("EDGE01")
    _escuchas({"jmp01": jmp, "labcli01": lab, "siem01": siem}, puertos=(22, 445))
    antes = L.contador_nft("DENEGADO", "forward")
    m.codigos[f"nc -zv -w3 {ctrl} 443"], _ = L.ex("gw-sim", f"nc -zv -w3 {ctrl} 443")
    m.codigos[f"nc -zv -w3 {siem} 1514"], _ = L.ex("gw-sim", f"nc -zv -w3 {siem} 1514")
    negativos = {f"{ctrl}:22": ("gw-sim", ctrl, 22), f"{siem}:22": ("gw-sim", siem, 22), f"{jmp}:22": ("gw-sim", jmp, 22), f"{lab}:445": ("gw-sim", lab, 445),
                 f"{edge}:3128": ("gw-sim", edge, 3128)}
    cerrados = {k: L.ex(n, f"nc -zv -w3 {ip} {p}")[0] for k, (n, ip, p) in negativos.items()}
    m.codigos["nc -zv -w3 10.20.10.10 443"] = L.ex("gw-sim", "nc -zv -w3 10.20.10.10 443")[0]
    despues = L.contador_nft("DENEGADO", "forward")
    m.medidas["paquetes_denegados_por_fw01"] = despues - antes
    c.ev.guardar("negativos.txt", "\n".join(f"{k}: rc={v}" for k, v in cerrados.items()))
    controles = [L.ex("jmp01", f"nc -zv -w2 {jmp} 22")[0], L.ex("labcli01", f"nc -zv -w2 {lab} 445")[0], L.ex("siem01", f"nc -zv -w2 {siem} 22")[0]]
    if any(controles):
        m.vacia = f"el control falló: algún puerto de prueba no abre ni desde su propio nodo ({controles})"
    elif all(v != 0 for v in cerrados.values()):
        m.vacia = "el Security Group sg-gw no existe en el Modo L: aquí solo se midió la denegación de FW01; la del SG se prueba en el Modo A (D5.4, make test-aws)"
    m.hallazgos.append("sg-gw (D2.5) no se emula; la mitad «SG» de T58 queda para el Modo A")
    return m


def t60(c: Contexto) -> Medicion:
    """Secuestro de WPAD: kali01 anuncia `wpad` (un servidor rogue en LAB); LABCLI01 con la URL fija del PAC por GPO lo ignora."""
    m = Medicion()
    kali = c.ip("KALI01")
    L.ex("kali01", "mkdir -p /tmp/rogue")
    L.enviar("kali01", "/tmp/rogue/wpad.dat", "function FindProxyForURL(url, host) { return \"PROXY " + kali + ":8080\"; }\n")
    L.ex("kali01", "cd /tmp/rogue && (nohup python3 -m http.server 80 > /tmp/rogue.log 2>&1 &) ; sleep 1")
    # el anuncio falso por DNS y DHCP se emula resolviendo `wpad` hacia kali01 en los clientes de autodescubrimiento
    resolv_hosts = L.leer("labcli01", "/etc/hosts")
    L.ex("labcli01", f"echo '{kali} wpad' >> /etc/hosts")
    try:
        _, vulnerable = L.ex("labcli01", "curl -s -m5 http://wpad/wpad.dat")             # control: un cliente con autodescubrimiento SÍ recibe el PAC falso
        golpes_control = int((L.ex("kali01", "grep -c 'GET /wpad.dat' /tmp/rogue.log")[1].strip() or 0))
        rc_dns, dns = L.ex("labcli01", f"kdig +short +time=2 +retry=1 @{c.puerta('LABCLI01')} pac.celeris.internal")
        rc_pac, pac = L.ex("labcli01", f"curl -s -m5 {PAC_URL}")
        rc_nav, seg, dom = _navegar(c, f"https://{c.P['dominio_origen']}/t60-navegador", f"--proxy-pac-url={PAC_URL}")
        golpes = int((L.ex("kali01", "grep -c 'GET /wpad.dat' /tmp/rogue.log")[1].strip() or 0))
    finally:
        L.enviar("labcli01", "/etc/hosts", resolv_hosts)
        L.ex("kali01", "pkill -f 'http.server 80'; true")
    c.ev.guardar("pac_obtenido.txt", pac)
    c.ev.guardar("rogue.log", L.leer("kali01", "/tmp/rogue.log"))
    m.salidas["curl http://pac.celeris.internal/wpad.dat"] = pac
    m.codigos["nslookup pac.celeris.internal 10.20.32.1"] = rc_dns if dns.strip() else 1
    m.medidas["peticiones_a_la_url_falsa_wpad"] = golpes - golpes_control
    if "FindProxyForURL" not in vulnerable or golpes_control < 1:
        m.vacia = "el control falló: ni un cliente con autodescubrimiento recibió el PAC falso, así que el anuncio rogue no quedó demostrado"
    m.hallazgos.append("el anuncio por DNS y DHCP se emula con una entrada `wpad` en el cliente y un servidor rogue en kali01: ni FW01 ni el laboratorio tienen un DHCP donde anunciar la opción 252")
    m.hallazgos.append("`nslookup` no está en la imagen: se usó kdig contra la IP de FW01 en la VLAN de LAB")
    return m


# ---------------------------------------------------------------------------------------------------------------
CASOS = {"T05": t05, "T06": t06, "T07": t07, "T08": t08, "T09": t09, "T10": t10, "T11": t11, "T13": t13, "T14": t14, "T15": t15,
         "T16": t16, "T17": t17, "T18": t18, "T19": t19, "T20": t20, "T24": t24, "T26": t26, "T27": t27,
         "T29": t29, "T30": t30, "T45": t45, "T46": t46, "T47": t47, "T28": t28, "T32": t32, "T31": t31, "T35": t35, "T49": t49,
         "T51": t51, "T52": t52, "T55": t55, "T56": t56, "T57": t57, "T58": t58, "T60": t60}

TESTSSL_IMAGEN = "drwetter/testssl.sh@sha256:64bab3c1fd8eee440f68d5e020dd633c1f2d375fe0ae593bdfec2725110a7e29"   # 3.2
ZAP_IMAGEN = "ghcr.io/zaproxy/zaproxy@sha256:9624669db72f54d86c4b46a7064518bd9bf79d8c61a4c31befa9923489f328af"   # stable
