"""REQ-F-26: PAC con varios nodos y DIRECT de respaldo."""
import json
import shutil
import subprocess

import pytest

from conftest import comparar_snapshot
from gen import pac

NODE = shutil.which("node")

HARNESS = """
const ip = h => /^\\d+\\.\\d+\\.\\d+\\.\\d+$/.test(h) ? h.split('.').reduce((a, b) => a * 256 + (+b), 0) : null;
function isPlainHostName(h) { return h.indexOf('.') < 0; }
function isInNet(h, p, m) { const a = ip(h); if (a === null) return false; const n = ip(p), k = ip(m); return ((a & k) >>> 0) === ((n & k) >>> 0); }
console.log(JSON.stringify(FindProxyForURL(process.argv[2], process.argv[3])));
"""


def test_nodos_y_puerto_salen_de_f1(infra):
    assert pac.nodos_proxy(infra) == [("EDGE01", "10.20.60.10", 3128), ("EDGE02", "10.20.60.11", 3128)]


def test_orden_de_proxies_y_direct_al_final(infra):
    assert 'return "PROXY 10.20.60.10:3128; PROXY 10.20.60.11:3128; DIRECT";' in pac.generar(infra)


def test_exclusiones_de_redes_internas(infra):
    t = pac.generar(infra)
    assert 'isInNet(host, "10.20.0.0", "255.252.0.0")' in t          # 10.20.0.0/14: todo el campus
    assert 'isInNet(host, "10.30.0.0", "255.255.0.0")' in t          # VPC de AWS
    assert "pac.celeris.internal" in t and "isPlainHostName(host)" in t
    assert "REQ-F-26" in t


def test_un_nodo_mas_en_f1_aparece_en_el_pac(infra, mutar):
    def agregar(inv):
        next(f for f in inv["flujos"] if f["id"] == "F1")["destino"].append("EDGE02")
    assert pac.generar(mutar(agregar)).count("PROXY") == pac.generar(infra).count("PROXY") + 1


def test_snapshot_wpad(infra):
    comparar_snapshot("wpad.dat", pac.generar(infra))


@pytest.mark.skipif(NODE is None, reason="node no está instalado: no se evalúa el JavaScript del PAC")
@pytest.mark.parametrize("host,url,esperado", [
    ("example.com", "https://example.com/", "PROXY 10.20.60.10:3128; PROXY 10.20.60.11:3128; DIRECT"),
    ("8.8.8.8", "http://8.8.8.8/", "PROXY 10.20.60.10:3128; PROXY 10.20.60.11:3128; DIRECT"),
    ("10.20.10.10", "https://10.20.10.10/", "DIRECT"),
    ("10.30.10.10", "https://10.30.10.10/", "DIRECT"),
    ("pac.celeris.internal", "http://pac.celeris.internal/wpad.dat", "DIRECT"),
    ("intranet", "http://intranet/", "DIRECT"),
    ("127.0.0.1", "http://127.0.0.1/", "DIRECT"),
])
def test_el_pac_se_evalua_como_javascript(infra, tmp_path, host, url, esperado):
    js = tmp_path / "pac.js"
    js.write_text(pac.generar(infra) + HARNESS, encoding="utf-8")
    r = subprocess.run([NODE, str(js), url, host], capture_output=True, text=True, check=True)
    assert json.loads(r.stdout) == esperado
