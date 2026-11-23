#!/usr/bin/env python3
"""Runner de pruebas de red del Modo L (emulación local, Parte F4).

Lee infra/pruebas.yaml, ejecuta dentro del laboratorio emulado (docker exec) las pruebas cuyo campo `modos` incluye L, evalúa
`criterio_aprobacion` con lo medido y guarda la evidencia en evidencias/<fecha>-L/<T-xx>/.

    python3 tests/network/run.py [--solo T06,T07] [--fecha AAAA-MM-DD] [--commit SHA] [--sin-ensayo]

Salidas:  evidencias/<fecha>-L/resultados.json, junit.xml y docs/infra/e1/ensayo-laboratorio.md.
Resultados: PASA, FALLA, PARCIAL (parte de los criterios no se pudo evaluar en L; NO es PASA) y NO_APLICA (con el motivo y el modo
en que sí se ejecutará). Si el laboratorio no está levantado, termina con código 2 sin simular nada.
"""
from __future__ import annotations

import argparse
import shutil
import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(RAIZ / "infra"))

import casos  # noqa: E402
import laboratorio as L  # noqa: E402
from celeris_infra import Infra  # noqa: E402
from evaluar import Medicion, evaluar  # noqa: E402
from gen import lab as genlab  # noqa: E402

NODOS_REQUERIDOS = ["fw01-sim", "fgt-sim", "vgw-sim", "gw-sim", "ext01", "origin-sim", "byod01", "jmp01", "ctrl01", "enc01", "labcli01", "labcli02", "labcli03",
                    "hny02", "kali01", "portal01", "hny01", "hny01-cowrie", "edge01", "edge02", "siem01", "siem01-wazuh"]


def commit_actual() -> str:
    """SHA de HEAD. En WSL, git no resuelve el worktree de Windows (.git apunta a una ruta D:/…): se lee a mano."""
    import os
    import subprocess
    if os.environ.get("CELERIS_COMMIT"):
        return os.environ["CELERIS_COMMIT"]
    p = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=RAIZ)
    if p.returncode == 0:
        return p.stdout.strip()
    try:
        gitdir = (RAIZ / ".git").read_text().split("gitdir:")[1].strip()
        if len(gitdir) > 2 and gitdir[1] == ":":
            gitdir = f"/mnt/{gitdir[0].lower()}{gitdir[2:]}"
        gd = Path(gitdir)
        ref = (gd / "HEAD").read_text().strip()
        if ref.startswith("ref:"):
            nombre = ref.split()[1]
            comun = Path((gd / "commondir").read_text().strip()) if (gd / "commondir").exists() else gd
            comun = comun if comun.is_absolute() else (gd / comun).resolve()
            for base in (gd, comun):
                if (base / nombre).exists():
                    return (base / nombre).read_text().strip()
            for linea in (comun / "packed-refs").read_text().splitlines():
                if linea.endswith(" " + nombre):
                    return linea.split()[0]
        return ref
    except Exception:
        return "desconocido"


def ejecutar(infra: Infra, t: dict, ctx_base: dict, raiz_ev: Path) -> dict:
    inicio = time.time()
    r = {"id": t["id"], "nombre": t["nombre"], "categoria": t["categoria"], "modos": t["modos"], "flujos": t["flujos"],
         "comando_de_referencia": t["comando"], "resultado": None, "motivo": "", "valor_medido": {}, "criterios": [], "hallazgos": [],
         "evidencia": [], "error_de_ejecucion": False}
    modos = t["modos"]
    if "L" not in modos:
        r.update(resultado="NO_APLICA", motivo=f"el Modo L no ejecuta {t['id']} (modos de la prueba: {', '.join(modos)}); se ejecuta en {' y '.join(modos)}")
        return r
    if t["id"] in casos.NO_APLICA_L:
        motivo = casos.NO_APLICA_L[t["id"]]
        motivo, donde = motivo if isinstance(motivo, tuple) else (motivo, ["H"])
        r.update(resultado="NO_APLICA", motivo=motivo + f"; se ejecuta en Modo {' y '.join(donde)}", modo_en_que_si_se_ejecuta=donde)
        return r
    ev = L.Evidencia(raiz_ev / t["id"])
    L.usar(ev)
    ctx = casos.Contexto(infra, genlab.PARAMETROS_LAB, ev, RAIZ, ctx_base)
    try:
        m: Medicion = casos.CASOS[t["id"]](ctx)
        res, crit, motivo = evaluar(t["criterio_aprobacion"], m)
        r.update(resultado=res, motivo=motivo, hallazgos=m.hallazgos,
                 valor_medido={**m.medidas, **({"codigos_de_salida": m.codigos} if m.codigos else {})},
                 criterios=[{"descripcion": x.descripcion, "estado": x.estado, "medido": x.medido, "detalle": x.detalle} for x in crit])
    except Exception as exc:                  # error del runner o del laboratorio: no es PASA y se dice
        ev.anotar("ERROR DE EJECUCIÓN:\n" + traceback.format_exc())
        r.update(resultado="FALLA", motivo=f"error de ejecución: {exc}", error_de_ejecucion=True)
    finally:
        L.usar(None)
    r["evidencia"] = [f"{t['id']}/{a}" for a in ev.archivos]
    r["duracion_s"] = round(time.time() - inicio, 1)
    return r


def junit(resultados: list[dict], fecha: str) -> str:
    n = len(resultados)
    fallas = sum(r["resultado"] == "FALLA" for r in resultados)
    omit = sum(r["resultado"] in ("NO_APLICA", "PARCIAL") for r in resultados)
    L_ = [f'<?xml version="1.0" encoding="UTF-8"?>', f'<testsuite name="celeris-modo-L" tests="{n}" failures="{fallas}" skipped="{omit}" timestamp="{fecha}">']
    for r in resultados:
        L_.append(f'  <testcase classname="CE0311.{r["categoria"]}" name="{r["id"]} {escape(r["nombre"])}" time="{r.get("duracion_s", 0)}">')
        if r["resultado"] == "FALLA":
            L_.append(f'    <failure message="{escape(r["motivo"][:300], {chr(34): "&quot;"})}"/>')
        elif r["resultado"] in ("NO_APLICA", "PARCIAL"):
            L_.append(f'    <skipped message="{r["resultado"]}: {escape(r["motivo"][:300], {chr(34): "&quot;"})}"/>')
        L_.append("  </testcase>")
    L_.append("</testsuite>")
    return "\n".join(L_) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--solo", help="IDs separados por coma (p. ej. T06,T07)")
    ap.add_argument("--fecha", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    ap.add_argument("--commit")
    ap.add_argument("--sin-ensayo", action="store_true", help="no reescribe docs/infra/e1/ensayo-laboratorio.md")
    a = ap.parse_args(argv)
    infra = Infra.cargar()
    pruebas = sorted(infra.pruebas.values(), key=lambda t: t["id"])
    if a.solo:
        pedidas = {x.strip().upper() for x in a.solo.split(",")}
        pruebas = [t for t in pruebas if t["id"] in pedidas]
    try:
        L.verificar_laboratorio(NODOS_REQUERIDOS)
    except L.LaboratorioNoDisponible as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    commit = a.commit or commit_actual()
    raiz_ev = RAIZ / "evidencias" / f"{a.fecha}-L"
    raiz_ev.mkdir(parents=True, exist_ok=True)
    ctx_base: dict = {}
    resultados = []
    for t in pruebas:
        print(f"{t['id']} {t['nombre']} ...", flush=True)
        if a.solo:
            shutil.rmtree(raiz_ev / t["id"], ignore_errors=True)       # sin restos de una corrida anterior de esta prueba
        r = ejecutar(infra, t, ctx_base, raiz_ev)
        r.update(commit=commit, fecha=a.fecha)
        resultados.append(r)
        print(f"   {r['resultado']}" + (f": {r['motivo'][:160]}" if r["motivo"] else ""), flush=True)
    _, imagenes = L.docker(["image", "ls", "--format", "{{.Repository}}:{{.Tag}} {{.ID}}", "--filter", "reference=celeris*"], 20)
    meta = {"modo": "L (emulación local con containerlab)", "fecha": a.fecha, "commit": commit, "imagenes": imagenes.split("\n")[:-1] if imagenes else [],
            "aviso": "Laboratorio EMULADO (Parte F4.2): no es OPNsense ni el VGW de AWS. PARCIAL y NO_APLICA no cuentan como PASA."}
    previo = raiz_ev / "resultados.json"
    if a.solo and previo.exists():
        # --solo sobre un ensayo del mismo día: se reemplazan solo esas pruebas y el resto del ensayo se conserva (queda dicho en meta)
        anterior = json.loads(previo.read_text(encoding="utf-8"))
        por_id = {r["id"]: r for r in anterior["resultados"]}
        por_id.update({r["id"]: r for r in resultados})
        meta = {**anterior["meta"], "reejecutadas": sorted(set(anterior["meta"].get("reejecutadas", [])) | {r["id"] for r in resultados}), "commit_reejecucion": commit}
        resultados = sorted(por_id.values(), key=lambda r: r["id"])
        fusion = True
    else:
        fusion = False
    cuenta = {k: sum(r["resultado"] == k for r in resultados) for k in ("PASA", "FALLA", "PARCIAL", "NO_APLICA")}
    meta["resumen"] = cuenta
    (raiz_ev / "resultados.json").write_text(json.dumps({"meta": meta, "resultados": resultados}, ensure_ascii=False, indent=2), encoding="utf-8")
    (raiz_ev / "junit.xml").write_text(junit(resultados, a.fecha), encoding="utf-8")
    print("\nResumen:", ", ".join(f"{v} {k}" for k, v in cuenta.items()), f"→ {raiz_ev.relative_to(RAIZ)}/resultados.json")
    if not a.sin_ensayo and (fusion or not a.solo):
        import ensayo
        print("Ensayo:", ensayo.escribir(infra, meta, resultados, RAIZ))
    return 1 if cuenta["FALLA"] else 0


if __name__ == "__main__":
    sys.exit(main())
