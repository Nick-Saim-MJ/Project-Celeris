import copy
import os
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "infra"))

from celeris_infra import Infra  # noqa: E402

SNAP = RAIZ / "tests" / "snapshots"
AWS_PEERS = ["198.51.100.21", "198.51.100.22"]   # RFC 5737; el inventario no fija las IP públicas de AWS (CI-23)


@pytest.fixture(scope="session")
def infra() -> Infra:
    return Infra.cargar()


@pytest.fixture
def mutar(infra):
    """Devuelve una copia del inventario sobre la que un test cambia un dato (para pruebas de regresión)."""
    def _mutar(fn):
        inv = copy.deepcopy(infra.inv)
        fn(inv)
        return Infra(inv, infra.pru, infra.traz)
    return _mutar


def comparar_snapshot(nombre: str, texto: str):
    """Compara con tests/snapshots/<nombre>. UPDATE_SNAPSHOTS=1 los regenera (revise el diff antes de commitear)."""
    ruta = SNAP / nombre
    if os.environ.get("UPDATE_SNAPSHOTS") == "1":
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(texto, encoding="utf-8", newline="\n")
    assert ruta.exists(), f"falta el snapshot {nombre}: ejecute UPDATE_SNAPSHOTS=1 pytest tests/gen y revise el diff"
    esperado = ruta.read_text(encoding="utf-8")
    assert texto == esperado, (
        f"el resultado generado difiere de tests/snapshots/{nombre}: cambió el inventario o el generador. "
        "Si es intencional: UPDATE_SNAPSHOTS=1 pytest tests/gen y commitee el diff.")
