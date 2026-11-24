"""Validación V-100+ de los diagramas del Entregable 2 (DC-0…DC-3) contra centro_datos.yaml e inventory.yaml, al estilo de V-50.

    V-100  Las 4 figuras existen en .drawio, .png y .pdf; PNG y PDF llevan el XML embebido y es el del .drawio actual.
    V-101  Todo `celeris_id` es un ID del contrato (componente vigente, elemento de centro_datos, zona, F-nn o enlace entre IDs válidos);
           cada figura dibuja todo lo que debe (cobertura) y ningún ID retirado.
    V-102  Toda IP o CIDR rotulada existe en el inventario; en la caja de un componente es de ese componente.
    V-103  Cada figura tiene título, leyenda y panel que cubre lo dibujado; criticidad por grosor y texto; vCPU, RAM, VLAN y CIDR
           rotulados coinciden con los YAML.
Escribe docs/infra/e2/cobertura-figuras.json (lo lee la matriz XLSX).
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from celeris_infra import RAIZ, COMPONENTES_RETIRADOS  # noqa: E402
import drawio_check as dc  # noqa: E402
from centro_datos import CentroDatos  # noqa: E402
from drawio import CRITICIDAD  # noqa: E402
from drawio_dc import FIGURAS_DC, huella_dc  # noqa: E402

DIR = RAIZ / "entregables" / "CE0331" / "diagramas"
JSON_COB = RAIZ / "docs" / "infra" / "e2" / "cobertura-figuras.json"
RE_IP = dc.RE_IP


def esperados(cd: CentroDatos, fig: str) -> set[str]:
    return {
        "DC-0": {"FGT-EXT", "ESX01", "FW01", "EDGE01", "CTRL01", "SIEM01", "VGW", "EC2-GW", "S3"},
        "DC-1": {"ESX01", "SW-CORE01", "SW-ACC", "BRK01", "IPMI01", "UPS01", "JMP01", "FGT-EXT", "RACK01",
                 *[e["id"] for e in cd.raw["rack"]["elementos"]], *cd.nics, *cd.datastores},
        "DC-2": {*cd.vm_por_id, *cd.vswitches, *cd.port_groups, *cd.nics, *cd.datastores},
        "DC-3": {"AWS-VPC", "AWS-PUB-A", "AWS-APP-A", "EC2-GW", "EC2-DR", "NAT-DR", "VGW", "S3", *[e["id"] for e in cd.aws["elementos"]],
                 *cd.aws["reglas_aws"]["tablas"], *cd.aws["reglas_aws"]["security_groups"], *cd.aws["reglas_aws"]["nacl"]},
    }[fig]


def comprobar(infra, cd: CentroDatos | None = None, directorio: Path = DIR):
    cd = cd or CentroDatos.cargar(infra)
    c100 = dc.Chequeo("V-100", "Diagramas DC-0…DC-3: .drawio, .png y .pdf presentes, con XML embebido y al día")
    c101 = dc.Chequeo("V-101", "Todo celeris_id es un ID del contrato y cada figura dibuja todo lo que debe (cobertura)")
    c102 = dc.Chequeo("V-102", "IP y CIDR rotulados existen en el inventario (y son del componente que los rotula)")
    c103 = dc.Chequeo("V-103", "Título, leyenda, panel; criticidad (borde + texto); vCPU, RAM, VLAN y CIDR coinciden con los YAML")
    cobertura: dict[str, dict] = {}
    ips_inv = dc.ips_del_inventario(infra)
    ex = cd.extras()
    validos = set(infra.componentes) | set(ex) | set(infra.zonas) | set(infra.flujos)
    for fig in FIGURAS_DC:
        ruta = directorio / f"{fig}.drawio"
        if not ruta.exists():
            c100.e(f"Falta {fig}.drawio", "python infra/gen/drawio_dc.py")
            continue
        texto = ruta.read_text(encoding="utf-8")
        for ext, fn in ((".png", dc.png_embebido), (".pdf", dc.pdf_embebido)):
            f = ruta.with_suffix(ext)
            if not f.exists():
                c100.e(f"Falta {f.name}", "python infra/gen/exportar_dc.py")
            elif not fn(f):
                c100.e(f"{f.name} no lleva el XML embebido", "python infra/gen/exportar_dc.py")
        png = ruta.with_suffix(".png")
        if png.exists():
            from PIL import Image
            Image.MAX_IMAGE_PIXELS = None
            with Image.open(png) as im:
                meta = getattr(im, "text", {}).get("mxfile")
            if meta and urllib.parse.unquote(meta) != texto:
                c100.w(f"{png.name} se exportó de una versión anterior de {ruta.name}", "python infra/gen/exportar_dc.py")
        elems = dc.leer_drawio(ruta)
        dibujados: set[str] = set()
        roles = {e.attrs.get("celeris_rol") for e in elems}
        for e in elems:
            cid, tipo = e.attrs.get("celeris_id"), e.attrs.get("celeris_tipo")
            if not cid:
                continue
            if tipo == "enlace":
                for extremo in (e.attrs.get("enlace_a"), e.attrs.get("enlace_b")):
                    if extremo.split(":")[0] not in validos and extremo not in ("campus",):
                        c101.e(f"{fig}: enlace {cid} con extremo desconocido {extremo}", "Use IDs del inventario o de centro_datos.yaml")
                continue
            base = cid.split(":")[0]
            if base not in validos:
                c101.e(f"{fig}: celeris_id {cid} no es un ID del contrato", "Corrija el generador")
            if base in COMPONENTES_RETIRADOS:
                c101.e(f"{fig}: dibuja {cid}, retirado en v0.4", "Quítelo")
            if tipo in ("componente", "elemento"):
                dibujados.add(cid)
        esp = esperados(cd, fig)
        for i in sorted(esp - dibujados):
            c101.e(f"{fig}: falta dibujar {i}", "Agréguelo a la figura")
        for i in sorted({d for d in dibujados if d in infra.componentes or d in ex} - esp):
            c101.w(f"{fig}: dibuja {i}, que no está en su lista esperada", "Actualice drawio_dc_check.esperados si es deliberado")
        cobertura[fig] = {"ids": sorted(dibujados)}
        for e in elems:
            if e.es_arista or not e.texto:
                continue
            for ip in RE_IP.findall(e.texto):
                if ip not in ips_inv:
                    c102.e(f"{fig}: {ip} no existe en el inventario", "Use una IP del inventario")
            cid = e.attrs.get("celeris_id")
            if e.attrs.get("celeris_tipo") == "componente" and cid in infra.componentes:
                propias = dc.ips_de_componente(infra.componentes[cid])
                for ip in RE_IP.findall(e.texto.split("\n")[1] if "\n" in e.texto else ""):
                    if propias and ip not in propias and "/" not in ip:
                        c102.e(f"{fig}: {ip} rotulada en {cid} no es suya", "Corrija el rótulo")
        for r in ("titulo", "leyenda", "panel"):
            if r not in roles:
                c103.e(f"{fig}: falta el bloque «{r}»", "Corrija el generador")
        panel = " ".join(e.texto for e in elems if e.attrs.get("celeris_rol") == "panel")
        for i in sorted(dibujados):
            if not re.search(rf"(?<![\w-]){re.escape(i)}(?![\w-])", panel):
                c103.e(f"{fig}: el panel no cubre {i}", "El panel lista todo lo dibujado")
        for e in elems:
            cid = e.attrs.get("celeris_id")
            if e.attrs.get("celeris_tipo") not in ("componente", "elemento") or not cid:
                continue
            crit = e.attrs.get("criticidad")
            fuente = infra.componentes[cid]["criticidad"] if cid in infra.componentes else ex[cid]["criticidad"]
            if crit != fuente:
                c103.e(f"{fig}: criticidad de {cid} ({crit}) distinta de la fuente ({fuente})", "Corrija")
                continue
            m = re.search(r"strokeWidth=(\d+)", e.estilo)
            if not m or int(m.group(1)) != CRITICIDAD[crit][0]:
                c103.e(f"{fig}: borde de {cid} ≠ {CRITICIDAD[crit][0]} px de {crit}", "Corrija el grosor")
            if CRITICIDAD[crit][1] not in e.texto:
                c103.e(f"{fig}: {cid} no rotula {CRITICIDAD[crit][1]}", "El color y el grosor nunca van solos")
        if fig == "DC-2":
            for e in elems:
                cid = e.attrs.get("celeris_id")
                if cid in cd.vm_por_id and e.attrs.get("celeris_tipo") == "componente":
                    v = cd.vm_por_id[cid]
                    if f"{v['vcpu']} vCPU" not in e.texto or f"{v['ram_gb']} GB" not in e.texto:
                        c103.e(f"DC-2: {cid} no rotula {v['vcpu']} vCPU y {v['ram_gb']} GB", "Corrija el rótulo")
                if cid in cd.port_groups and e.attrs.get("celeris_tipo") == "elemento":
                    vl = cd.port_groups[cid]["vlan"]
                    if (f"VLAN {vl}" if vl is not None else "sin etiqueta") not in e.texto:
                        c103.e(f"DC-2: {cid} no rotula su VLAN {vl}", "Corrija el rótulo")
        if fig == "DC-3":
            for e in elems:
                cid = e.attrs.get("celeris_id")
                if cid in ("EC2-DR", "NAT-DR") and "dashed=1" not in e.estilo:
                    c103.e(f"DC-3: {cid} debe dibujarse punteado (temporal)", "Corrija el estilo")
                if cid in infra.componentes and infra.componentes[cid].get("cidr") and infra.componentes[cid]["cidr"] not in e.texto:
                    c103.e(f"DC-3: {cid} no rotula su CIDR {infra.componentes[cid]['cidr']}", "Corrija")
    c101.hallazgos.append(dc.Hallazgo("info", f"Huella de la fuente al generar: {huella_dc()}"))
    return [c100, c101, c102, c103], cobertura


def escribir(cobertura: dict) -> None:
    JSON_COB.parent.mkdir(parents=True, exist_ok=True)
    JSON_COB.write_text(json.dumps(cobertura, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    from celeris_infra import Infra
    x = Infra.cargar()
    chequeos, cob = comprobar(x)
    escribir(cob)
    mal = False
    for c in chequeos:
        print(f"{c.id} {c.estado}: {c.titulo}")
        for h in c.hallazgos:
            print(f"   [{h.nivel}] {h.mensaje} → {h.corregir}")
        mal |= c.estado == "FALLA"
    return 1 if mal else 0


if __name__ == "__main__":
    sys.exit(main())
