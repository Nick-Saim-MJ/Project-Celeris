"""Verificación del cronograma con Microsoft Project (COM) — CE01 E3.

Lo llama gestion/e3/plan.py. Abre entregables/CE01/E3/Cronograma_Celeris.xml con MS Project, deja que recalcule y
compara, actividad por actividad, inicio, fin, ruta crítica (Critical), holgura total y costo con los de Python. Si
coinciden, guarda Cronograma_Celeris.mpp (con la línea base del XML) e intenta exportar la vista Gantt como imagen
(gestion/e3/figuras/gantt-msproject.png). Si MS Project no está instalado, lo informa y no falla: el XML queda para
abrirlo a mano (paso manual del README).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import mspdi  # noqa: E402
import plan as P  # noqa: E402

PNG = AQUI / "figuras" / "gantt-msproject.png"

PS = r"""
$ErrorActionPreference = 'Stop'
$salida = '__SALIDA__'
$app = New-Object -ComObject MSProject.Application
$app.Visible = $false
$app.DisplayAlerts = $false
try {
  [void]$app.FileOpenEx('__XML__')
  $p = $app.ActiveProject
  $lineas = New-Object System.Collections.Generic.List[string]
  foreach ($t in $p.Tasks) {
    if ($t -ne $null) {
      $lineas.Add(('{0}|{1}|{2}|{3}|{4}|{5}|{6}|{7}' -f $t.UniqueID, $t.Start.ToString('yyyy-MM-dd HH:mm'),
        $t.Finish.ToString('yyyy-MM-dd HH:mm'), [int]$t.Critical, $t.TotalSlack, $t.Cost, [int]$t.Summary, $t.PercentComplete))
    }
  }
  $lineas.Add(('PROYECTO|{0}|{1}|{2}' -f $p.ProjectSummaryTask.Start.ToString('yyyy-MM-dd HH:mm'),
    $p.ProjectSummaryTask.Finish.ToString('yyyy-MM-dd HH:mm'), $p.ProjectSummaryTask.Cost))
  [System.IO.File]::WriteAllLines($salida, $lineas)
  [void]$app.FileSaveAs('__MPP__')
  if ('__PNG__' -ne '') {
    try {
      Add-Type -AssemblyName System.Windows.Forms
      Add-Type -AssemblyName System.Drawing
      [void]$app.SelectAll()
      [void]$app.EditCopyPicture($false, $false, $false, '__DESDE__', '__HASTA__')
      $img = [System.Windows.Forms.Clipboard]::GetImage()
      if ($img -ne $null) { $img.Save('__PNG__', [System.Drawing.Imaging.ImageFormat]::Png) }
    } catch { }
  }
  [void]$app.FileCloseEx(0)
} finally {
  $app.Quit()
}
"""


def disponible() -> bool:
    if os.name != "nt" or not shutil.which("powershell"):
        return False
    p = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command",
                        "try { $a = New-Object -ComObject MSProject.Application; $a.Quit(); 'si' } catch { 'no' }"],
                       capture_output=True, text=True, timeout=120)
    return p.stdout.strip().endswith("si")


def verificar(xml: Path, m: dict, imagen: bool = True) -> dict:
    if not disponible():
        return {"ok": None, "resumen": "no instalado: abrir el XML a mano (README, pasos manuales)", "diferencias": []}
    mpp = xml.with_suffix(".mpp")
    with tempfile.TemporaryDirectory() as d:
        salida = Path(d) / "tareas.txt"
        ps = (PS.replace("__SALIDA__", str(salida)).replace("__XML__", str(xml.resolve()))
              .replace("__MPP__", str(mpp.resolve())).replace("__PNG__", str(PNG.resolve()) if imagen else "")
              .replace("__DESDE__", "01/03/2027").replace("__HASTA__", "18/06/2027"))
        script = Path(d) / "verificar.ps1"
        script.write_text(ps, encoding="utf-8-sig")
        p = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-STA", "-ExecutionPolicy", "Bypass",
                            "-File", str(script)], capture_output=True, text=True, timeout=600)
        if p.returncode != 0 or not salida.exists():
            raise RuntimeError(f"MS Project no pudo abrir el XML: {p.stderr.strip()[-400:]}")
        lineas = salida.read_text(encoding="utf-8-sig").splitlines()
    uid = mspdi.uids(m)
    filas = {f["id"]: f for f in m["filas"]}
    cron = P.programar()
    dif, criticas_mp = [], []
    proyecto = None
    for ln in lineas:
        c = ln.split("|")
        if c[0] == "PROYECTO":
            proyecto = {"inicio": c[1], "fin": c[2], "costo": float(c[3].replace(",", "."))}
            continue
        u, ini, fin, crit, holg, costo, resumen, avance = c
        aid = uid.get(int(u))
        if aid is None or aid not in filas or resumen == "1":
            continue
        f = filas[aid]
        if crit == "1":
            criticas_mp.append(aid)
        if f["hecha"]:
            continue
        if ini[:10] != f["inicio"] or fin[:10] != f["fin"]:
            dif.append(f"{aid}: MS Project {ini[:10]}–{fin[:10]} ≠ Python {f['inicio']}–{f['fin']}")
        if int(crit) != int(f["critica"]):
            dif.append(f"{aid}: crítica en MS Project = {crit}, en Python = {int(f['critica'])}")
        holg_d = round(float(holg.replace(",", ".")) / 480, 2)
        if abs(holg_d - cron[aid]["holgura"]) > 0.01:
            dif.append(f"{aid}: holgura MS Project {holg_d} d ≠ Python {cron[aid]['holgura']} d")
        if abs(float(costo.replace(",", ".")) - f["costo"]) > 0.01:
            dif.append(f"{aid}: costo MS Project {costo} ≠ Python {f['costo']:.2f}")
    if proyecto and abs(proyecto["costo"] - m["presupuesto"]["bac"]) > 0.01:
        dif.append(f"Costo total MS Project {proyecto['costo']:.2f} ≠ presupuesto de actividades {m['presupuesto']['bac']:.2f}")
    rc_py = [i for i in m["ruta_critica"]]
    if sorted(criticas_mp) != sorted(rc_py):
        dif.append(f"Ruta crítica distinta: MS Project {sorted(criticas_mp)} ≠ Python {sorted(rc_py)}")
    if dif:
        raise RuntimeError("MS Project y Python no coinciden:\n  - " + "\n  - ".join(dif[:20]))
    return {"ok": True, "diferencias": [], "criticas": criticas_mp, "proyecto": proyecto,
            "mpp": mpp.name, "imagen": PNG.exists(),
            "resumen": f"abrió el XML: {len(criticas_mp)} tareas críticas iguales a las de Python; costo "
                       f"{proyecto['costo']:.2f}; guardado {mpp.name}" + (" e imagen Gantt" if PNG.exists() else "")}
