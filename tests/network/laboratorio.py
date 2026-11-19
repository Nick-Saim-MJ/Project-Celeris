"""Acceso al laboratorio emulado: docker exec, copias, contadores de nftables y registro de evidencias.

Todo se ejecuta en el anfitrión que tiene Docker (WSL en Windows). Cada orden se anota en la evidencia de la prueba en curso.
"""
from __future__ import annotations

import os as _os
import shutil as _shutil
import subprocess as _subprocess


def _docker_nativo() -> None:
    """Con Docker Desktop (integración de WSL) el socket por defecto no es el del dockerd que usa containerlab: se usa el nativo (lab/docker-nativo.sh)."""
    if _os.environ.get("DOCKER_HOST") or not _os.path.exists("/run/docker-nativo.sock") or not _shutil.which("docker"):
        return
    try:
        nombre = _subprocess.run(["docker", "info", "--format", "{{.Name}}"], capture_output=True, text=True, timeout=20).stdout.strip()
    except (OSError, _subprocess.SubprocessError):
        return
    if nombre == "docker-desktop":
        _os.environ["DOCKER_HOST"] = "unix:///run/docker-nativo.sock"


_docker_nativo()

import re
import subprocess
import time
from pathlib import Path

PREFIJO = "clab-celeris-"


class LaboratorioNoDisponible(RuntimeError):
    pass


class Evidencia:
    """Carpeta evidencias/<fecha>-L/<T-xx>/ de una prueba."""

    def __init__(self, directorio: Path):
        self.dir = directorio
        self.dir.mkdir(parents=True, exist_ok=True)
        self.dir.chmod(0o777)            # las herramientas en contenedor (testssl, ZAP) escriben aquí con otro usuario
        self.archivos: list[str] = []
        self._log = self.dir / "salida.txt"

    def anotar(self, texto: str) -> None:
        with self._log.open("a", encoding="utf-8") as f:
            f.write(texto if texto.endswith("\n") else texto + "\n")
        if "salida.txt" not in self.archivos:
            self.archivos.append("salida.txt")

    def guardar(self, nombre: str, contenido: str | bytes) -> Path:
        ruta = self.dir / nombre
        if isinstance(contenido, bytes):
            ruta.write_bytes(contenido)
        else:
            ruta.write_text(contenido, encoding="utf-8", newline="\n")
        if nombre not in self.archivos:
            self.archivos.append(nombre)
        return ruta

    def registrar_existente(self, nombre: str) -> None:
        if (self.dir / nombre).exists() and nombre not in self.archivos:
            self.archivos.append(nombre)


_actual: Evidencia | None = None


def usar(ev: Evidencia | None) -> None:
    global _actual
    _actual = ev


def _run(args: list[str], timeout: float, entrada: str | None = None) -> tuple[int, str]:
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout, input=entrada, errors="replace")
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        salida = ((e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")) + "\n[tiempo agotado]"
        return 124, salida


def docker(args: list[str], timeout: float = 60, entrada: str | None = None, nota: str | None = None) -> tuple[int, str]:
    rc, out = _run(["docker", *args], timeout, entrada)
    if _actual is not None:
        _actual.anotar(f"$ {nota or 'docker ' + ' '.join(args)}\n{out.rstrip()}\n[salida {rc}]")
    return rc, out


def ex(nodo: str, cmd: str, timeout: float = 30, entrada: str | None = None) -> tuple[int, str]:
    """docker exec en el nodo (sh -c). Código 124 = tiempo agotado."""
    args = ["exec", *(["-i"] if entrada is not None else []), PREFIJO + nodo, "sh", "-c", cmd]
    return docker(args, timeout, entrada, nota=f"[{nodo}] {cmd}")


def fondo(nodo: str, cmd: str) -> None:
    """Lanza una orden que sigue ejecutándose en el nodo (docker exec -d)."""
    docker(["exec", "-d", PREFIJO + nodo, "sh", "-c", cmd], 30, nota=f"[{nodo}] (en segundo plano) {cmd}")


def leer(nodo: str, ruta: str) -> str:
    return ex(nodo, f"cat {ruta} 2>/dev/null")[1]


def enviar(nodo: str, ruta: str, contenido: str, modo: str = "644") -> None:
    ex(nodo, f"cat > {ruta} && chmod {modo} {ruta}", entrada=contenido)


def traer(nodo: str, ruta: str, destino: Path) -> bool:
    rc, _ = docker(["cp", f"{PREFIJO}{nodo}:{ruta}", str(destino)], 60, nota=f"docker cp {nodo}:{ruta} {destino.name}")
    return rc == 0


def esperar(condicion, timeout: float, paso: float = 1.0) -> bool:
    fin = time.time() + timeout
    while time.time() < fin:
        if condicion():
            return True
        time.sleep(paso)
    return condicion()


def verificar_laboratorio(nodos: list[str]) -> None:
    rc, out = _run(["docker", "ps", "--format", "{{.Names}}"], 20)
    if rc != 0:
        raise LaboratorioNoDisponible("Docker no responde. En Windows ejecute dentro de WSL.")
    vivos = set(out.split())
    faltan = [n for n in nodos if PREFIJO + n not in vivos]
    if faltan:
        raise LaboratorioNoDisponible(f"el laboratorio no está levantado (faltan {', '.join(faltan)}): ejecute `make lab-up`")
    for n in nodos:
        if n in ("hny01-cowrie", "siem01-wazuh"):
            continue
        rc, _ = _run(["docker", "exec", PREFIJO + n, "test", "-f", "/run/lab-listo"], 20)
        if rc != 0:
            raise LaboratorioNoDisponible(f"{n} no terminó su arranque (docker exec {PREFIJO}{n} cat /var/log/arranque.log)")


# --- contadores de nftables en fw01-sim -----------------------------------------------------------------------------

def contador_nft(patron: str, cadena: str = "forward") -> int:
    """Suma los paquetes de las reglas de la cadena cuya línea contiene `patron` (subcadena)."""
    _, out = _run(["docker", "exec", PREFIJO + "fw01-sim", "nft", "list", "chain", "inet", "fw01sim", cadena], 20)
    total = 0
    for linea in out.splitlines():
        m = re.search(r"counter packets (\d+)", linea)
        if patron in linea and m:
            total += int(m.group(1))
    return total


def recargar_nft(texto: str) -> bool:
    rc, _ = docker(["exec", "-i", PREFIJO + "fw01-sim", "nft", "-f", "-"], 30, entrada=texto, nota="[fw01-sim] nft -f - (reglas regeneradas desde el inventario)")
    return rc == 0


# --- enlaces ----------------------------------------------------------------------------------------------------------

def enlace(nodo: str, arriba: bool, puerta: str | None = None) -> None:
    """Simula apagar (o encender) un equipo desconectando su interfaz; al encender restituye la ruta por defecto."""
    if arriba:
        ex(nodo, "ip link set eth1 up" + (f"; ip route replace default via {puerta}" if puerta else ""))
    else:
        ex(nodo, "ip link set eth1 down")
