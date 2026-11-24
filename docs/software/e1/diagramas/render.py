"""Genera y valida los diagramas UML de CE02 E1, sección 4 (Diseño detallado).

Uso (desde la raíz del repositorio):
    python docs/software/e1/diagramas/render.py              # valida y genera PNG + SVG
    python docs/software/e1/diagramas/render.py --solo-validar
    python docs/software/e1/diagramas/render.py --descargar  # baja PlantUML si falta (verifica SHA-256)

Requiere Java 11+ y Graphviz (`dot`). PlantUML se guarda en .tools/plantuml/ (ignorado por git).

Validación (regla del proyecto: no se inventan IP, nombres ni IDs):
  D-01  cada IPv4 citada existe en infra/inventory.yaml y corresponde al componente que la acompaña
  D-02  cada componente en MAYÚSCULAS (EDGE01, CTRL01…) existe en el inventario
  D-03  cada F-nn (flujo) existe en el inventario
  D-04  cada REQ-… existe en infra/trazabilidad.yaml (también la forma corta F-02, NF-14, RN-07 de los pies)
  D-05  cada D-nn existe en infra/trazabilidad.yaml; cada CU-nn en CE02 v0.4 (C1.6); cada P-nn en pantallas.md
  D-06  cada S-nn existe en infra/trazabilidad.yaml o en la tabla «Supuestos nuevos» de README.md
  D-07  cada CI-nn existe en docs/infra/e1/CAMBIOS-INVENTARIO.md
  D-08  cada diagrama tiene título con su propio ID (DS-nn) y pie de trazabilidad ($pie)
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
SRC = AQUI / "src"
JAR = RAIZ / ".tools" / "plantuml" / "plantuml.jar"
PLANTUML_VERSION = "1.2026.9"
PLANTUML_URL = f"https://github.com/plantuml/plantuml/releases/download/v{PLANTUML_VERSION}/plantuml-{PLANTUML_VERSION}.jar"
PLANTUML_SHA256 = "aa4a1d06f8911c4b842beff4828dd955be431692b631a312d04c0e9fab9581de"

sys.path.insert(0, str(RAIZ / "infra"))
from celeris_infra import Infra, ids_en_cambios  # noqa: E402

RE_IP = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")
RE_COMP = re.compile(r"\b([A-Z]{2,}\d{2}(?:-[A-Z0-9]+)?|EC2-[A-Z]+)\b")
# Siglas con dígitos que no son componentes: cursos (CE022), grupos TLS (X25519MLKEM768), algoritmos.
NO_COMPONENTE = re.compile(r"^(CE\d+|X25519.*|MLKEM.*|SHA\d+|AES\d+|DS\d+)$")
RE_FLUJO = re.compile(r"(?<![A-Z-])F(\d{1,2})\b(?!-)")
RE_REQ = re.compile(r"\bREQ-(F|NF|RN)-(\d{2})\b")
RE_REQ_CORTO = re.compile(r"(?<![A-Z-])(F|NF|RN)-(\d{2})\b")
RE_DEC = re.compile(r"(?<![A-Z-])D-(\d{2})\b")
RE_CU = re.compile(r"\bCU-(\d{2})\b")
RE_PANT = re.compile(r"(?<![A-Z-])P-(\d{2})\b")
RE_SUP = re.compile(r"\[?S-(\d{2})\]?")
RE_CI = re.compile(r"\bCI-(\d{2})\b")


def contexto() -> dict[str, set[str]]:
    infra = Infra.cargar(RAIZ)
    maestro = (RAIZ / "docs" / "celeris" / "Celeris-CE02-Ingenieria-Software.md").read_text(encoding="utf-8")
    pantallas = (RAIZ / "docs" / "software" / "e1" / "prototipo" / "pantallas.md").read_text(encoding="utf-8")
    readme = (AQUI / "README.md").read_text(encoding="utf-8") if (AQUI / "README.md").exists() else ""
    nuevos = set(re.findall(r"^\|\s*(S-\d{2})\s*\|", readme.split("## Supuestos nuevos", 1)[-1], flags=re.M)) \
        if "## Supuestos nuevos" in readme else set()
    ips: dict[str, str] = {ip: cid for cid, _if, ip, _z in infra.todas_las_ips()}
    return {
        "ips": ips,
        "componentes": set(infra.componentes),
        "flujos": set(infra.flujos),
        "req": set(infra.requisitos),
        "dec": set(infra.decisiones),
        "sup": set(infra.supuestos) | nuevos,
        "cu": set(re.findall(r"^\|\s*(CU-\d{2})\s*\|", maestro, flags=re.M)),
        "pant": set(re.findall(r"^\|\s*(P-\d{2})\s*\|", pantallas, flags=re.M)),
        "ci": ids_en_cambios(),
    }


def validar(archivo: Path, ctx: dict) -> list[str]:
    texto = archivo.read_text(encoding="utf-8")
    # Los comentarios de PlantUML (líneas que empiezan con ') no se validan.
    cuerpo = "\n".join(l for l in texto.splitlines() if not l.lstrip().startswith("'"))
    errores: list[str] = []
    did = archivo.stem.split("-")[0] + "-" + archivo.stem.split("-")[1]

    for linea in cuerpo.splitlines():
        for ip in RE_IP.findall(linea):
            if ip not in ctx["ips"]:
                errores.append(f"D-01 IP {ip} no está en infra/inventory.yaml")
                continue
            dueño = ctx["ips"][ip]
            if dueño not in linea and dueño.split(":")[0] not in linea:
                otros = [c for c in RE_COMP.findall(linea) if c in ctx["componentes"]]
                if otros:
                    errores.append(f"D-01 IP {ip} es de {dueño}, pero la línea nombra {', '.join(otros)}")
    for c in set(RE_COMP.findall(cuerpo)):
        if NO_COMPONENTE.match(c):
            continue
        if c not in ctx["componentes"]:
            errores.append(f"D-02 componente {c} no está en el inventario")
    for n in set(RE_FLUJO.findall(cuerpo)):
        if f"F{n}" not in ctx["flujos"]:
            errores.append(f"D-03 flujo F{n} no está en el inventario")
    reqs = {f"REQ-{t}-{n}" for t, n in RE_REQ.findall(cuerpo)}
    reqs |= {f"REQ-{t}-{n}" for t, n in RE_REQ_CORTO.findall(cuerpo)}
    for r in sorted(reqs - ctx["req"]):
        errores.append(f"D-04 {r} no está en infra/trazabilidad.yaml")
    for n in set(RE_DEC.findall(cuerpo)):
        if f"D-{n}" not in ctx["dec"]:
            errores.append(f"D-05 decisión D-{n} no existe")
    for n in set(RE_CU.findall(cuerpo)):
        if f"CU-{n}" not in ctx["cu"]:
            errores.append(f"D-05 caso de uso CU-{n} no existe en CE02 C1.6")
    for n in set(RE_PANT.findall(cuerpo)):
        if f"P-{n}" not in ctx["pant"]:
            errores.append(f"D-05 pantalla P-{n} no existe en pantallas.md")
    for n in set(RE_SUP.findall(cuerpo)):
        if f"S-{n}" not in ctx["sup"]:
            errores.append(f"D-06 supuesto S-{n} no está registrado")
    for n in set(RE_CI.findall(cuerpo)):
        if f"CI-{n}" not in ctx["ci"]:
            errores.append(f"D-07 CI-{n} no está en CAMBIOS-INVENTARIO.md")
    if not re.search(rf"^title {re.escape(did)} ", cuerpo, flags=re.M):
        errores.append(f"D-08 falta «title {did} …»")
    if not re.search(rf'^\$pie\("{re.escape(did)}"', cuerpo, flags=re.M):
        errores.append(f"D-08 falta el pie $pie(\"{did}\", …)")
    return errores


def descargar() -> None:
    JAR.parent.mkdir(parents=True, exist_ok=True)
    tmp = JAR.with_suffix(".part")
    print(f"Descargando PlantUML {PLANTUML_VERSION} desde GitHub…")
    urllib.request.urlretrieve(PLANTUML_URL, tmp)  # noqa: S310 - URL fija y hash verificado
    digest = hashlib.sha256(tmp.read_bytes()).hexdigest()
    if digest != PLANTUML_SHA256:
        tmp.unlink()
        sys.exit(f"SHA-256 inesperado: {digest}")
    tmp.replace(JAR)


def generar(archivos: list[Path]) -> None:
    if not JAR.exists():
        sys.exit(f"Falta {JAR.relative_to(RAIZ)}. Ejecute con --descargar.")
    if not shutil.which("java"):
        sys.exit("Falta Java en el PATH.")
    for formato in ("png", "svg"):
        cmd = ["java", "-Djava.awt.headless=true", "-jar", str(JAR), "-charset", "UTF-8", "-failfast2",
               f"-t{formato}", "-o", str(AQUI / formato), *map(str, archivos)]
        subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--solo-validar", action="store_true")
    ap.add_argument("--descargar", action="store_true")
    args = ap.parse_args()

    archivos = sorted(p for p in SRC.glob("DS-*.puml"))
    ctx = contexto()
    total = 0
    for a in archivos:
        errores = validar(a, ctx)
        total += len(errores)
        estado = "OK" if not errores else f"{len(errores)} error(es)"
        print(f"{a.name}: {estado}")
        for e in errores:
            print(f"   - {e}")
    if total:
        print(f"\n{total} error(es) de trazabilidad: corrija el .puml o registre el dato en CAMBIOS-INVENTARIO.md.")
        return 1
    if args.descargar and not JAR.exists():
        descargar()
    if not args.solo_validar:
        generar(archivos)
        print(f"\n{len(archivos)} diagramas generados en png/ y svg/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
