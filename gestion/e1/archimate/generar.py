"""Vista de motivación ArchiMate 3.2 del E1 (CE0112): driver → assessment → goal → outcome → requirement → componente.

    python gestion/e1/archimate/generar.py

1. Escribe gestion/e1/archimate/celeris-motivacion.xml en el formato de intercambio de The Open Group (ArchiMate 3.1/3.2
   Model Exchange File Format), con la vista «Motivación de Celeris Edge» ya dispuesta y con la paleta UPeU (CI-100).
2. Si Archi está instalado (ARCHI o C:\\Program Files\\Archi\\Archi.exe), lo importa por la línea de comandos de Archi,
   guarda el modelo .archimate y genera el reporte HTML; de ahí copia la imagen de la vista a
   gestion/e1/figuras/motivacion-archi.png (la figura oficial). Sin Archi, deja el XML y avisa: el paso manual está en
   gestion/e1/README.md.

Fuentes: gestion/e1/datos/diagnostico.yaml → archimate (enlaces), infra/trazabilidad.yaml (OB-x y REQ-x, textos).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

import yaml

AQUI = Path(__file__).resolve().parent
E1 = AQUI.parent
sys.path.insert(0, str(E1.parent))
import ce01_datos as cd  # noqa: E402
import estilo_ce01 as est  # noqa: E402

XML = AQUI / "celeris-motivacion.xml"
MODELO = AQUI / "celeris-motivacion.archimate"
PNG = E1 / "figuras" / "motivacion-archi.png"
ARCHI = [os.environ.get("ARCHI", ""), r"C:\Program Files\Archi\Archi.exe", "/opt/Archi/Archi",
         "/Applications/Archi.app/Contents/MacOS/Archi"]

# (tipo ArchiMate, relleno, borde) por columna, de izquierda a derecha
COLUMNAS = [
    ("Driver", "azul_muy_claro", "azul_upeu"),
    ("Assessment", "azul_muy_claro", "azul_medio"),
    ("Goal", "ambar_claro", "ambar_upeu"),
    ("Outcome", "ambar_claro", "ambar_upeu"),
    ("Requirement", "azul_claro", "azul_upeu"),
    ("ApplicationComponent", "blanco", "azul_upeu"),
]
W, H, DX, DY, X0, Y0 = 200, 80, 240, 90, 20, 56


def _rgb(nombre: str) -> str:
    h = est.color(nombre).lstrip("#")
    return f'r="{int(h[0:2], 16)}" g="{int(h[2:4], 16)}" b="{int(h[4:6], 16)}"'


def modelo() -> tuple[list, list]:
    """(elementos [(id, tipo, nombre, columna)], relaciones [(id, tipo, origen, destino)])."""
    d = yaml.safe_load((E1 / "datos" / "diagnostico.yaml").read_text(encoding="utf-8"))
    a = d["archimate"]
    oe = {o["id"]: o for o in d["identidad"]["objetivos"]}
    obs = {o["id"]: o for o in cd.objetivos()}
    req = cd._yaml("infra/trazabilidad.yaml")["requisitos"]
    el, rel = [], []
    for x in a["drivers"]:
        el.append((x["id"], "Driver", x["nombre"], 0))
    for x in a["assessments"]:
        el.append((x["id"], "Assessment", x["nombre"], 1))
        rel.append((f"r-{x['id']}-{x['driver']}", "Association", x["id"], x["driver"]))
    for g in a["goals"]:
        texto = oe[g["id"]]["texto"].split(" (")[0]
        el.append((g["id"], "Goal", f"{g['id']} {texto}", 2))
        for s_ in g["assessments"]:
            rel.append((f"r-{s_}-{g['id']}", "Influence", s_, g["id"]))
    for ob, goals in a["outcomes"].items():
        el.append((ob, "Outcome", f"{ob} {obs[ob]['necesidad']}: {obs[ob]['meta'].split(' [')[0]}", 3))
        for g in goals:
            rel.append((f"r-{ob}-{g}", "Realization", ob, g))
    for r in a["requisitos"]:
        el.append((r["id"], "Requirement", f"{r['id']} {r.get('corto') or req[r['id']]}", 4))
        rel.append((f"r-{r['id']}-{r['ob']}", "Realization", r["id"], r["ob"]))
        for c in r["componentes"]:
            rel.append((f"r-{c}-{r['id']}", "Realization", c, r["id"]))
    for c in a["componentes"]:
        el.append((c["id"], "ApplicationComponent", c["nombre"], 5))
    return el, rel


def xml() -> str:
    el, rel = modelo()
    ident = lambda x: "id-" + x.replace(" ", "_")
    filas = {}
    pos = {}
    for eid, _, _, col in el:
        n = filas.get(col, 0)
        filas[col] = n + 1
        pos[eid] = (col, n)
    alto = max(filas.values())
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<model xmlns="http://www.opengroup.org/xsd/archimate/3.0/" '
           'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
           'xsi:schemaLocation="http://www.opengroup.org/xsd/archimate/3.0/ '
           'http://www.opengroup.org/xsd/archimate/3.1/archimate3_Diagram.xsd" identifier="id-celeris-e1">',
           '  <name xml:lang="es">Celeris Edge — Motivación (CE01 E1, CE0112)</name>',
           '  <documentation xml:lang="es">Generado por gestion/e1/archimate/generar.py desde '
           'gestion/e1/datos/diagnostico.yaml e infra/trazabilidad.yaml. No editar a mano.</documentation>',
           '  <elements>']
    for eid, tipo, nombre, _ in el:
        out.append(f'    <element identifier="{ident(eid)}" xsi:type="{tipo}"><name xml:lang="es">{escape(nombre)}</name></element>')
    out.append('  </elements>')
    out.append('  <relationships>')
    for rid, tipo, o, dst in rel:
        out.append(f'    <relationship identifier="{ident(rid)}" source="{ident(o)}" target="{ident(dst)}" xsi:type="{tipo}"/>')
    out.append('  </relationships>')
    out += ['  <views>', '    <diagrams>',
            '      <view identifier="id-vista-motivacion" xsi:type="Diagram">',
            '        <name xml:lang="es">Motivación de Celeris Edge</name>']
    for col, (tipo, _, _) in enumerate(COLUMNAS):
        out.append(f'        <node identifier="id-t{col}" xsi:type="Label" x="{X0 + col * DX}" y="10" w="{W}" h="30">'
                   f'<label xml:lang="es">{["Drivers", "Assessments", "Goals (OE)", "Outcomes (OB)", "Requirements (CE02)", "Componentes (CE03)"][col]}</label>'
                   f'<style><fillColor {_rgb("blanco")} a="0"/><lineColor {_rgb("blanco")} a="0"/>'
                   f'<font name="Calibri" size="13" style="bold"><color {_rgb("azul_upeu")}/></font></style></node>')
    out.append(f'        <node identifier="id-nota" xsi:type="Label" x="{X0}" y="{int(Y0 + alto * DY + 6)}" w="{6 * DX - 40}" h="28">'
               f'<label xml:lang="es">OE-a…OE-d: rótulos de trabajo de los objetivos estratégicos institucionales '
               f'[confirmar con el plan estratégico]. OB-x: infra/trazabilidad.yaml. REQ-x: SRS de CE02. Componentes: '
               f'infra/inventory.yaml.</label><style><fillColor {_rgb("blanco")} a="0"/><lineColor {_rgb("blanco")} a="0"/>'
               f'<font name="Calibri" size="10" style="italic"><color {_rgb("gris_medio")}/></font></style></node>')
    for eid, tipo, _, col in el:
        _, relleno, borde = COLUMNAS[col]
        n = pos[eid][1]
        desp = (alto - filas[col]) * DY / 2           # centra verticalmente las columnas cortas
        out.append(f'        <node identifier="n-{ident(eid)}" elementRef="{ident(eid)}" xsi:type="Element" '
                   f'x="{X0 + col * DX}" y="{int(Y0 + desp + n * DY)}" w="{W}" h="{H}">'
                   f'<style><fillColor {_rgb(relleno)}/><lineColor {_rgb(borde)}/>'
                   f'<font name="Calibri" size="11"><color {_rgb("gris_texto")}/></font></style></node>')
    for rid, _, o, dst in rel:
        out.append(f'        <connection identifier="c-{ident(rid)}" relationshipRef="{ident(rid)}" xsi:type="Relationship" '
                   f'source="n-{ident(o)}" target="n-{ident(dst)}">'
                   f'<style><lineColor {_rgb("gris_medio")}/></style></connection>')
    out += ['      </view>', '    </diagrams>', '  </views>', '</model>', '']
    return "\n".join(out)


def archi() -> str | None:
    return next((c for c in ARCHI if c and Path(c).is_file()), None)


def exportar_png(exe: str) -> bool:
    """Importa el XML en Archi (línea de comandos), guarda el .archimate y saca la imagen de la vista del reporte HTML."""
    with tempfile.TemporaryDirectory() as tmp:
        rep = Path(tmp) / "reporte"
        cmd = [exe, "-application", "com.archimatetool.commandline.app", "-consoleLog", "-nosplash",
               "--xmlexchange.import", str(XML), "--saveModel", str(MODELO), "--html.createReport", str(rep)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        imgs = sorted(rep.rglob("*.png"), key=lambda p: p.stat().st_size, reverse=True) if rep.exists() else []
        vistas = [p for p in imgs if "images" in p.parts or "elements" in p.parts]
        if r.returncode != 0 or not vistas:
            print(f"  Archi no generó la imagen (código {r.returncode}). {r.stdout[-400:]} {r.stderr[-400:]}")
            return False
        PNG.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(vistas[0], PNG)
        return True


def main() -> int:
    XML.write_text(xml(), encoding="utf-8")
    print(f"  {XML.relative_to(cd.RAIZ).as_posix()}")
    exe = archi()
    if not exe:
        print("  Archi no está instalado: importe el XML a mano (gestion/e1/README.md, paso 2)")
        return 0
    if exportar_png(exe):
        print(f"  {PNG.relative_to(cd.RAIZ).as_posix()} (exportada por Archi)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
