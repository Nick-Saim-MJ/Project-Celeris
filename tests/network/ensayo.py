"""Genera docs/infra/e1/ensayo-laboratorio.md a partir de resultados.json (lo escribe `make test-lab`; no se edita a mano)."""
from __future__ import annotations

from pathlib import Path

EQUIVALENCIAS = [
    ("FW01 OPNsense", "`fw01-sim`: Debian + nftables (reglas generadas del inventario) + strongSwan + FRR + Suricata + Unbound", "Funcional: mismas zonas, flujos, política por defecto, VPN y BGP. No es OPNsense (FreeBSD); no se prueban sus GUI, MFA ni CrowdSec"),
    ("Port groups de ESXi, SW-CORE01", "Puentes Linux por VLAN (`br-vlanNN`), sin br-vlan70 ni br-vlan71", "Funcional. No hay trunk 802.1Q ni controles de capa 2 (RA guard, DHCP snooping, port-security)"),
    ("VGW de AWS", "`vgw-sim`: strongSwan + FRR con los mismos parámetros de fase 1/2 y BGP", "Funcional, sin el servicio gestionado ni sus tablas de rutas, Security Groups o NACL"),
    ("EC2-SHIELD", "`shield01`: binario de `celeris-node` sobre la imagen base de laboratorio", "Solo recibe tráfico de prueba directo (REQ-F-29 pendiente)"),
    ("EDGE01/02", "`edge01`/`edge02`: el mismo binario que la imagen OCI de producción, sobre la imagen base de laboratorio (la imagen mínima no trae shell para configurar la red)", "Mismo código; el contenedor final no es el de producción"),
    ("WAF01", "`waf01`: nginx + ModSecurity v3 + OWASP CRS", "Equivalente funcional; F4.2 dice Caddy + Coraza"),
    ("WEB01", "`web01`: nginx con el aviso de `docs/AVISO.md` como sitio estático", "Mismo producto de la familia; sitio generado, no firmado (REQ-F-30 pendiente)"),
    ("HNY01", "`hny01` + Cowrie oficial (SSH, puerto 2222)", "Cowrie sí; OpenCanary y el puerto 23 de F24 no"),
    ("HNY02", "`hny02`: canario propio en Python (puertos 22, 80, 445, 3389)", "Equivalente funcional; no es OpenCanary"),
    ("IDS01", "`ids01`: Suricata 7 con 4 interfaces de captura (VLAN 10, 20, 31, 50) y espejo de puertos con `tc mirred`", "Funcional, con reglas locales mínimas (sin ET Open: el laboratorio no tiene Internet)"),
    ("SIEM01 Wazuh", "No desplegado", "Sin SIEM: las comprobaciones de alertas de Wazuh no se evalúan"),
    ("Certificado público del portal", "Certificado de una CA de laboratorio (se genera en `lab/.run/pki`, fuera de git)", "El ACME real y la calificación con CA pública se prueban en Modo A o H"),
    ("ESX01, IPMI01, UPS01, BRK01, NAS01, CTRL01, DB01, PROBE01, EC2-CTRLR, NAT01", "No existen en el laboratorio (F4.1)", "Sus pruebas se ejecutan en Modo H (CI-16, CI-24)"),
]


def _celda(t: str, n: int = 170) -> str:
    t = " ".join(str(t).split()).replace("|", "\\|")
    return t if len(t) <= n else t[: n - 1] + "…"


def _valor(r: dict) -> str:
    v = {k: x for k, x in r["valor_medido"].items() if k != "codigos_de_salida"}
    return ", ".join(f"{k} = {x}" for k, x in v.items()) or "—"


def escribir(infra, meta: dict, resultados: list[dict], raiz: Path) -> Path:
    c = meta["resumen"]
    L = ["# Ensayo en el laboratorio emulado (Modo L)\n",
         "> Generado por `make test-lab` (`tests/network/run.py`). No editar a mano.\n",
         "> **El laboratorio es emulado** (Parte F4.2 del documento maestro). Lo que pasa aquí demuestra que el *diseño* se comporta como "
         "está descrito en una emulación funcional; no es la validación del producto real (OPNsense, VGW de AWS) ni del campus.\n",
         f"- Fecha: {meta['fecha']} · commit: `{meta['commit'][:12]}`",
         f"- Resultado: **{c['PASA']} PASA**, **{c['FALLA']} FALLA**, **{c['PARCIAL']} PARCIAL**, **{c['NO_APLICA']} NO_APLICA** (de {len(resultados)} pruebas, {len(resultados) - 28} de ellas ampliaciones T29+ que aún no tienen caso en el Modo L)",
         "- `PARCIAL` = parte de los criterios no se pudo evaluar en el Modo L (navegador real, Wazuh…) o la medición no ejercitó lo que la prueba valida. **No cuenta como PASA.**",
         "- `NO_APLICA` = la prueba no se puede ejecutar en L; se indica el modo en que sí se ejecutará. **Nunca cuenta como PASA.**\n",
         "## Resultados\n", "| Prueba | Resultado | Medido | Motivo o nota |", "| --- | --- | --- | --- |"]
    for r in resultados:
        nota = r["motivo"] or ("; ".join(r["hallazgos"][:1]) if r["hallazgos"] else "")
        L.append(f"| {r['id']} — {_celda(r['nombre'], 60)} | **{r['resultado']}** | {_celda(_valor(r), 90)} | {_celda(nota)} |")
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
          "- Las IP son las del inventario, salvo la WAN (198.51.100.0/24, F4.1), el nombre del portal y los dominios de prueba (CI-24).",
          "- `curl` de la imagen no soporta HTTP/3: T08 usa datagramas UDP 443 en lugar de `curl --http3`.",
          "- T09 y T22 imitan la lógica del PAC con `curl`; el cambio real de un navegador se mide en Modo H.",
          "- Los comandos de `infra/pruebas.yaml` son la referencia; el runner ejecuta su equivalente en los nodos del laboratorio (ver `evidencias/<fecha>-L/<T-xx>/salida.txt`).",
          "- Las evidencias (pcap, registros, salidas) están en `evidencias/<fecha>-L/`, fuera de git: pueden contener el token de laboratorio. `resultados.json` y `junit.xml` sí se versionan.",
          "", "## Reproducir", "", "```bash", "make lab-up      # genera, construye y despliega (Docker + containerlab en Linux/WSL)",
          "make test-lab    # ejecuta T05–T28 en Modo L y reescribe este archivo", "make lab-down", "```", ""]
    ruta = raiz / "docs" / "infra" / "e1" / "ensayo-laboratorio.md"
    ruta.write_text("\n".join(L), encoding="utf-8", newline="\n")
    return ruta
