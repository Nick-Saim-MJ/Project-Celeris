"""Utilidades comunes de los XLSX del Entregable 1 (matriz de pruebas, matriz de componentes): estilo, impresión y guardado reproducible.

Identidad visual de CLAUDE.md: paleta Okabe-Ito (apta para daltonismo). El color nunca va solo: toda celda con color lleva también el
nombre de la zona o el estado en texto. Fuente Calibri de 11 pt, encabezados fijos, filtros, impresión A4 horizontal.
"""
from __future__ import annotations

import io
import re
import zipfile
from datetime import datetime
from pathlib import Path

from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins
from openpyxl.worksheet.properties import PageSetupProperties

# Okabe-Ito por zona (CLAUDE.md). AWS usa el naranja de los grupos de AWS; INTERNET y PERIMETRO, grises neutros.
COLOR_ZONA = {
    "MGMT": "0072B2", "SERVERS": "009E73", "LAB": "E69F00", "LAB-TEST": "F0E442", "DMZ-SVC": "D55E00", "DMZ-HONEY": "CC79A7",
    "SECURITY": "56B4E9", "EDGE": "4D4D4D", "STORAGE": "BBBBBB", "BACKUP": "888888", "AWS": "FF9900", "INTERNET": "FFFFFF",
    "PERIMETRO": "DDDDDD",
}
# Estados de una celda de resultado: color de apoyo; el texto del estado siempre está en la celda.
COLOR_ESTADO = {
    "PASA": "009E73", "FALLA": "D55E00", "PARCIAL": "F0E442", "NO_APLICA": "BBBBBB", "SIN ENSAYO": "FFFFFF",
    "Cubierto": "009E73", "SIN PRUEBA": "D55E00",
}
ENCABEZADO_FONDO = "4D4D4D"
FILA_ALTERNA = "F2F2F2"

LADO = Side(style="thin", color="999999")
BORDE = Border(left=LADO, right=LADO, top=LADO, bottom=LADO)
FUENTE = Font(name="Calibri", size=11)
NEGRITA = Font(name="Calibri", size=11, bold=True)
TITULO = Font(name="Calibri", size=11, bold=True)
AJUSTE = Alignment(wrap_text=True, vertical="top")
CENTRO = Alignment(wrap_text=True, vertical="top", horizontal="center")


def _luminosidad(hex6: str) -> float:
    r, g, b = (int(hex6[i:i + 2], 16) for i in (0, 2, 4))
    return 0.299 * r + 0.587 * g + 0.114 * b


def fuente_sobre(fondo: str, negrita: bool = False) -> Font:
    """Texto blanco o negro, el que más contraste da sobre `fondo`."""
    return Font(name="Calibri", size=11, bold=negrita, color="FFFFFF" if _luminosidad(fondo) < 140 else "000000")


def relleno(hex6: str) -> PatternFill:
    return PatternFill("solid", start_color=hex6, end_color=hex6)


def celda_zona(c, zona: str) -> None:
    """Pinta una celda con el color de la zona; el texto de la celda es el nombre de la zona."""
    fondo = COLOR_ZONA.get(zona, "FFFFFF")
    c.fill = relleno(fondo)
    c.font = fuente_sobre(fondo, negrita=True)


def celda_estado(c, estado: str) -> None:
    fondo = COLOR_ESTADO.get(estado)
    if fondo:
        c.fill = relleno(fondo)
        c.font = fuente_sobre(fondo, negrita=True)


def escribir_encabezado(ws, fila: int, columnas: list[str], anchos: list[float] | None = None) -> None:
    for i, texto in enumerate(columnas, start=1):
        c = ws.cell(row=fila, column=i, value=texto)
        c.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        c.fill = relleno(ENCABEZADO_FONDO)
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        c.border = BORDE
    if anchos:
        for i, a in enumerate(anchos, start=1):
            ws.column_dimensions[get_column_letter(i)].width = a


def escribir_fila(ws, fila: int, valores: list, centrar: set[int] | None = None, alterna: bool = False) -> None:
    for i, v in enumerate(valores, start=1):
        c = ws.cell(row=fila, column=i, value=v)
        c.font = FUENTE
        c.alignment = CENTRO if centrar and i in centrar else AJUSTE
        c.border = BORDE
        if alterna:
            c.fill = relleno(FILA_ALTERNA)


def configurar_hoja(ws, fila_encabezado: int, ultima_columna: int, ultima_fila: int, congelar: str | None = None, filtro: bool = True) -> None:
    """Encabezado fijo, filtros e impresión en A4 horizontal ajustada al ancho, con el encabezado repetido en cada página."""
    ws.freeze_panes = congelar or f"A{fila_encabezado + 1}"
    if filtro and ultima_fila > fila_encabezado:
        ws.auto_filter.ref = f"A{fila_encabezado}:{get_column_letter(ultima_columna)}{ultima_fila}"
    ws.row_dimensions[fila_encabezado].height = 48
    imprimir_a4(ws, fila_encabezado)


def imprimir_a4(ws, fila_encabezado: int | None = None) -> None:
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.page_margins = PageMargins(left=0.4, right=0.4, top=0.5, bottom=0.5)
    ws.print_options.horizontalCentered = False
    ws.oddFooter.center.text = "&A — página &P de &N"
    if fila_encabezado:
        ws.print_title_rows = f"{fila_encabezado}:{fila_encabezado}"


def propiedades(wb, titulo: str, fecha: str) -> None:
    """Propiedades fijas: el mismo inventario produce el mismo archivo (sin la hora de generación)."""
    f = datetime.fromisoformat(fecha)
    wb.properties.creator = "Celeris Edge — infra/gen"
    wb.properties.lastModifiedBy = "Celeris Edge — infra/gen"
    wb.properties.title = titulo
    wb.properties.created = f
    wb.properties.modified = f
    wb.calculation.fullCalcOnLoad = True        # Excel y LibreOffice recalculan las fórmulas al abrir


def guardar_reproducible(wb, ruta: Path) -> bytes:
    """Guarda el libro con marcas de tiempo fijas dentro del ZIP: dos ejecuciones dan los mismos bytes."""
    fijo = wb.properties.created.strftime("%Y-%m-%dT%H:%M:%SZ").encode()
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    salida = io.BytesIO()
    with zipfile.ZipFile(buf) as origen, zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as destino:
        for info in sorted(origen.infolist(), key=lambda i: i.filename):
            nuevo = zipfile.ZipInfo(info.filename, date_time=(2026, 1, 1, 0, 0, 0))
            nuevo.compress_type = zipfile.ZIP_DEFLATED
            nuevo.external_attr = 0o644 << 16
            datos = origen.read(info.filename)
            if info.filename == "docProps/core.xml":        # openpyxl pone la hora de guardado en `modified`: se fija a la de `created`
                datos = re.sub(rb"(<dcterms:modified[^>]*>)[^<]*", rb"\g<1>" + fijo, datos)
            destino.writestr(nuevo, datos)
    datos = salida.getvalue()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(datos)
    return datos
