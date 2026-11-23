"""Genera docs/infra/e1/ensayo-laboratorio.md a partir de resultados.json (lo escribe `make test-lab`; no se edita a mano)."""
from __future__ import annotations

from pathlib import Path

EQUIVALENCIAS = [
    ("FW01 OPNsense", "`fw01-sim`: Debian + nftables (reglas generadas del inventario) + strongSwan + FRR + Suricata + Unbound + NTP + CrowdSec", "Funcional (D5.3): mismas zonas, flujos, política por defecto, VPN con NAT-T y BGP. No es OPNsense; el IPS inline se emula como IDS"),
    ("FortiGate (FGT-EXT)", "`fgt-sim`: nftables con NAT 1:1 de la IP pública del laboratorio (198.51.100.10) hacia 10.20.0.2 solo para UDP 500/4500 y TCP 80/443, y ruta al Wi-Fi", "Funcional (D5.3), sin FortiGuard ni inspección SSL: la exclusión de EDGE01/02 de esa inspección [S-29] no se puede probar en el Modo L"),
    ("Wi-Fi de estudiantes (WIFI-EST)", "Puente `br-wifi` (172.16.0.0/16) + `byod01`", "Funcional (D5.3), sin puntos de acceso ni el DNS y el DHCP de la DTI [S-28]"),
    ("Port groups de ESXi, SW-CORE01", "Puentes Linux por VLAN (`br-vlanNN`, 7 VLAN)", "Funcional. No hay trunk 802.1Q ni controles de capa 2 (RA guard, DHCP snooping, port-security)"),
    ("VGW de AWS", "`vgw-sim`: strongSwan + FRR con los mismos parámetros de fase 1/2 y BGP; también hace de Internet Gateway y NAT de la VPC", "Funcional, sin el servicio gestionado ni sus tablas de rutas, Security Groups o NACL"),
    ("EC2-GW", "`gw-sim`: nginx + ModSecurity + OWASP CRS detrás de `vgw-sim`, con certificado de cliente hacia `ctrl01:443`", "Funcional; D5.3 dice Caddy + Coraza («mismo producto»), que la imagen base no trae (CI-48). El Security Group `sg-gw` no se emula"),
    ("CTRL01 (consola)", "`ctrl01`: consola de prueba HTTPS en 443 (sesiones `campus` y `remoto`, 403 a las acciones críticas remotas) y firma ed25519 de la configuración de los nodos", "Funcional y mínima (D5.3). No es la consola de CE02: T50, T53 y T54 la necesitan y quedan NO_APLICA"),
    ("EDGE01/02", "`edge01`/`edge02`: el mismo binario que la imagen OCI de producción, sobre la imagen base de laboratorio (la imagen mínima no trae shell para configurar la red)", "Mismo código; el contenedor es el de laboratorio, no la imagen OCI"),
    ("PORTAL01", "`portal01`: nginx + ModSecurity + OWASP CRS con el aviso de `docs/AVISO.md` como sitio estático", "Funcional; D5.3 dice Caddy + Coraza. El sitio es generado, no firmado (REQ-F-30 pendiente)"),
    ("HNY01", "`hny01` + Cowrie oficial (SSH, puerto 2222)", "Cowrie sí; OpenCanary y el puerto 23 de F24 no"),
    ("HNY02", "`hny02`: canario propio en Python (puertos 22, 80, 445, 3389)", "Equivalente funcional; no es OpenCanary"),
    ("SIEM01 Wazuh", "`siem01` + `siem01-wazuh`: Wazuh manager 4.9.2 real y agentes en CTRL01, EDGE01/02, PORTAL01, HNY01, HNY02 y EC2-GW", "Mismo producto; las reglas locales 100300–100305 son de laboratorio. El IDS de FW01 llega por syslog TLS (F14), no por un agente"),
    ("ENC01, PCs de LAB-01…LAB-10", "`enc01`, `labcli01` (con Chromium), `labcli02` (LAB-01) y `labcli03` (LAB-03)", "Funcional (D5.3): no se emulan los 400 equipos"),
    ("Orígenes de Internet", "`ext01` (atacante externo y origen web) y `origin-sim` (archivos de 100 MB a 1 GB)", "Funcional; no hay Internet real ni DNS público"),
    ("Certificado público del portal y de EC2-GW", "Certificados de una CA de laboratorio (se generan en `lab/.run/pki`, fuera de git)", "El ACME real y la calificación con CA pública se prueban en Modo A o H"),
    ("ESX01, IPMI01, UPS01, BRK01, SW-CORE01, SW-ACC, S3, EC2-DR, NAT-DR", "No existen en el laboratorio", "Sus pruebas se ejecutan en Modo A o H (CI-16, D5.4)"),
]


def _celda(t: str, n: int = 170) -> str:
    t = " ".join(str(t).split()).replace("|", "\\|")
    return t if len(t) <= n else t[: n - 1] + "…"


def _valor(r: dict) -> str:
    v = {k: x for k, x in r["valor_medido"].items() if k != "codigos_de_salida"}
    return ", ".join(f"{k} = {x}" for k, x in v.items()) or "—"


def _previos(raiz: Path, fecha_actual: str) -> tuple[str, dict]:
    """Resultados de la v0.2: el ensayo anterior a este (carpeta evidencias/AAAA-MM-DD-L con resultados.json)."""
    import json
    carpetas = sorted(p for p in (raiz / "evidencias").glob("*-L") if (p / "resultados.json").exists() and p.name != f"{fecha_actual}-L")
    if not carpetas:
        return "", {}
    datos = json.loads((carpetas[-1] / "resultados.json").read_text(encoding="utf-8"))
    return carpetas[-1].name[:-2], {r["id"]: r["resultado"] for r in datos["resultados"]}


RETIRADAS_V04 = {"T12": "STORAGE y NFS", "T22": "SVC01", "T37": "OTLP", "T38": "base de datos en red", "T39": "NAS", "T41": "NFS", "T44": "peering", "T48": "STORAGE"}
CAMBIOS_DE_DESTINO = {
    "T01": "destino EC2-GW 10.30.0.10 (antes EC2-SHIELD)", "T02": "EC2-GW → CTRL01:443 (antes EC2-CTRLR → DB01:5432)", "T20": "HNY01 → PORTAL01:443 (antes WEB01:8080)",
    "T21": "destino 10.30.0.10", "T29": "Suricata de FW01 en la interfaz LAB (antes IDS01)", "T42": "origen FW01 (antes SVC01)", "T46": "DMZ-SVC → zonas internas, incluido CTRL01:5432",
}


def escribir(infra, meta: dict, resultados: list[dict], raiz: Path) -> Path:
    c = meta["resumen"]
    fecha_previa, previos = _previos(raiz, meta["fecha"])
    L = ["# Ensayo en el laboratorio emulado (Modo L)\n",
         "> Generado por `make test-lab` (`tests/network/run.py`). No editar a mano.\n",
         "> **El laboratorio es emulado** (Parte F4.2 del documento maestro). Lo que pasa aquí demuestra que el *diseño* se comporta como "
         "está descrito en una emulación funcional; no es la validación del producto real (OPNsense, VGW de AWS) ni del campus.\n",
         f"- Fecha: {meta['fecha']} · commit: `{meta['commit'][:12]}`",
         f"- Resultado: **{c['PASA']} PASA**, **{c['FALLA']} FALLA**, **{c['PARCIAL']} PARCIAL**, **{c['NO_APLICA']} NO_APLICA** (de {len(resultados)} pruebas vigentes, {len(resultados) - 28} de ellas ampliaciones T29+ que aún no tienen caso en el Modo L)",
         "- `PARCIAL` = parte de los criterios no se pudo evaluar en el Modo L (navegador real, Wazuh…) o la medición no ejercitó lo que la prueba valida. **No cuenta como PASA.**",
         "- `NO_APLICA` = la prueba no se puede ejecutar en L; se indica el modo en que sí se ejecutará. **Nunca cuenta como PASA.**\n",
         "## Resultados\n", f"La columna «v0.2 → v0.4» compara con el ensayo anterior ({fecha_previa or 'sin ensayo previo'}, v0.2). «nueva» = prueba de la v0.4; «cambió de destino» = D1.16 v0.4 la apunta a otra pieza.\n",
         "| Prueba | Resultado | v0.2 → v0.4 | Medido | Motivo o nota |", "| --- | --- | --- | --- | --- |"]
    for r in resultados:
        nota = r["motivo"] or ("; ".join(r["hallazgos"][:1]) if r["hallazgos"] else "")
        previo = previos.get(r["id"])
        cambio = (f"{previo} → {r['resultado']}" if previo else "nueva") + (f" (cambió de destino: {CAMBIOS_DE_DESTINO[r['id']]})" if r["id"] in CAMBIOS_DE_DESTINO else "")
        L.append(f"| {r['id']} — {_celda(r['nombre'], 60)} | **{r['resultado']}** | {_celda(cambio, 110)} | {_celda(_valor(r), 90)} | {_celda(nota)} |")
    L += ["", "### Pruebas retiradas en la v0.4 (no se ejecutan ni se reutilizan sus IDs)", "", "| Prueba | Motivo | Resultado en la v0.2 |", "| --- | --- | --- |"]
    L += [f"| {tid} | {motivo} | {previos.get(tid, '—')} |" for tid, motivo in RETIRADAS_V04.items()]
    por_id = {r["id"]: r for r in resultados}
    L += ["\n## Mediciones", ""]
    t05 = por_id.get("T05", {}).get("valor_medido", {})
    if "convergencia_s" in t05:
        L.append(f"- **Convergencia de la VPN (T05, OD-05):** {t05['convergencia_s']} s desde que cae el túnel 1 hasta que el tráfico vuelve a pasar por el túnel 2 "
                 f"(interrupción visible {t05.get('interrupcion_s', '—')} s). Meta de D1.10: ≤ 60 s. El hold de BGP (30 s) es solo un componente; el valor real es el medido.")
    t09 = por_id.get("T09", {}).get("valor_medido", {})
    if "tiempo_de_cambio_s" in t09:
        L.append(f"- **Cambio de nodo del PAC (T09/OD-03):** {t09['tiempo_de_cambio_s']} s con EDGE01 caído; {t09.get('tiempo_hasta_direct_s', '—')} s hasta DIRECT con ambos caídos "
                 "(cliente que imita al PAC con `curl`, no un navegador).")
    t55 = por_id.get("T55", {}).get("valor_medido", {})
    if "descargas_en_origen" in t55:
        L.append(f"- **Coalescencia (T55):** {t55['descargas_en_origen']} descarga(s) en origin-sim para 20 clientes simultáneos de 100 MB; {t55.get('respuestas_collapsed_o_hit', '—')} respuestas HIT de las 19 que esperaron.")
    t51 = por_id.get("T51", {}).get("valor_medido", {})
    if "latencia_cambio_s" in t51:
        L.append(f"- **Cambio firmado (T51, REQ-NF-16):** el nodo aplicó la configuración firmada en {t51['latencia_cambio_s']} s (meta ≤ 60 s; intervalo de recarga del laboratorio: 5 s).")
    for h in por_id.get("T16", {}).get("hallazgos", []):
        L.append(f"- **TLS del portal (T16, OD-08):** {h}")
    t15 = por_id.get("T15", {}).get("valor_medido", {})
    if t15:
        L.append(f"- **Exposición (T15):** {t15.get('puertos_abiertos', '—')} puertos abiertos desde Internet; alertas de Suricata en fw01-sim durante el escaneo: {t15.get('alertas_suricata_fw01', '—')}.")
    t27 = por_id.get("T27", {}).get("valor_medido", {})
    if t27:
        L.append(f"- **Métricas (T27, REQ-NF-14):** paquetes HTTP en claro = {t27.get('paquetes_http_en_claro', '—')}, handshakes TLS = {t27.get('handshakes_tls', '—')}, "
                 f"apariciones del token = {t27.get('apariciones_del_token_en_la_captura', '—')}.")
    L += ["", "## Hallazgos (contradicen o precisan el diseño)", ""]
    hubo = False
    for r in resultados:
        if r["resultado"] == "FALLA":
            hubo = True
            L.append(f"- **{r['id']} FALLA** — {r['motivo']}" + (f" ({'; '.join(r['hallazgos'])})" if r["hallazgos"] else ""))
    for r in resultados:
        if r["resultado"] != "FALLA" and r["hallazgos"]:
            hubo = True
            for h in r["hallazgos"]:
                L.append(f"- {r['id']} — {h}")
    if not hubo:
        L.append("Ninguno.")
    L += ["", "## Qué se emula y qué no (equivalencias de F4.2)", "", "| En el diseño | En el laboratorio | Equivalencia |", "| --- | --- | --- |"]
    L += [f"| {a} | {b} | {c_} |" for a, b, c_ in EQUIVALENCIAS]
    L += ["", "## Limitaciones", "",
          "- Las IP son las del inventario, salvo la WAN (198.51.100.0/24, F4.1), el nombre del portal, los dominios de prueba y los parámetros de CI-24 y CI-48.",
          "- T50, T53 y T54 requieren la consola (CE02, S2): son NO_APLICA aquí y se ejecutan en Modo H (T50) o A y H (T53, T54).",
          "- `curl` de la imagen no soporta HTTP/3: T08 usa datagramas UDP 443 en lugar de `curl --http3`.",
          "- T09 imita la lógica del PAC con `curl` además de usar Chromium; el cambio real de un navegador de producción se mide en Modo H.",
          "- Los comandos de `infra/pruebas.yaml` son la referencia; el runner ejecuta su equivalente en los nodos del laboratorio (ver `evidencias/<fecha>-L/<T-xx>/salida.txt`).",
          "- Las evidencias (pcap, registros, salidas) están en `evidencias/<fecha>-L/`, fuera de git: pueden contener el token de laboratorio. `resultados.json` y `junit.xml` sí se versionan.",
          "", "## Reproducir", "", "```bash", "make lab-up      # genera, construye y despliega (Docker + containerlab en Linux/WSL)",
          "make test-lab    # ejecuta las pruebas del Modo L (T05–T60) y reescribe este archivo", "make lab-down", "```", ""]
    ruta = raiz / "docs" / "infra" / "e1" / "ensayo-laboratorio.md"
    ruta.write_text("\n".join(L), encoding="utf-8", newline="\n")
    return ruta
