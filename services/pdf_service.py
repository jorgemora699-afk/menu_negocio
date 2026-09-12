"""
services/pdf_service.py

Genera el PDF de detalle de horario y salario para un empleado, usando
reportlab. Devuelve un BytesIO listo para enviar con send_file.
"""

import io
from datetime import datetime
from zoneinfo import ZoneInfo

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

BRASS = colors.HexColor("#9c7a3c")
BRASS_SOFT = colors.HexColor("#f3ecda")
INK = colors.HexColor("#1b1812")
MUTED = colors.HexColor("#6b6558")
LINE = colors.HexColor("#e7e1d3")

ZONA_COLOMBIA = ZoneInfo("America/Bogota")


def _formatear_hora(dt_utc):
    if dt_utc is None:
        return "—"
    local = dt_utc.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZONA_COLOMBIA)
    return local.strftime("%I:%M %p").lstrip("0")


def _formatear_fecha_larga(fecha):
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    return f"{dias[fecha.weekday()]} {fecha.day:02d}/{fecha.month:02d}"


def _formatear_moneda(valor):
    if valor is None:
        return "—"
    return f"${valor:,.0f}".replace(",", ".")


def generar_pdf_salario(business_nombre, empleado_nombre, desde, hasta, filas, total_horas, total_salario):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=22 * mm,
        bottomMargin=18 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    style_titulo = ParagraphStyle(
        "Titulo", parent=styles["Title"], fontSize=18, textColor=INK, spaceAfter=2,
    )
    style_subtitulo = ParagraphStyle(
        "Subtitulo", parent=styles["Normal"], fontSize=11, textColor=MUTED, spaceAfter=14,
    )
    style_normal = ParagraphStyle(
        "NormalInk", parent=styles["Normal"], fontSize=10, textColor=INK,
    )

    story = []

    story.append(Paragraph(business_nombre, style_subtitulo))
    story.append(Paragraph(f"Reporte de horario y salario — {empleado_nombre}", style_titulo))
    story.append(Paragraph(
        f"Período: {desde.strftime('%d/%m/%Y')} al {hasta.strftime('%d/%m/%Y')}",
        style_subtitulo,
    ))
    story.append(Spacer(1, 6))

    # ---- tabla de días ----
    encabezado = ["Día", "Entrada", "Salida", "Horas", "Tarifa/h", "Subtotal"]
    datos_tabla = [encabezado]

    for f in filas:
        datos_tabla.append([
            _formatear_fecha_larga(f["fecha"]),
            _formatear_hora(f["hora_entrada"]),
            _formatear_hora(f["hora_salida"]),
            f"{f['horas']:.2f} h" if f["horas"] is not None else "en curso",
            _formatear_moneda(f["tarifa"]),
            _formatear_moneda(f["subtotal"]),
        ])

    if not filas:
        story.append(Paragraph("No hay turnos registrados en este período.", style_normal))
    else:
        tabla = Table(datos_tabla, colWidths=[32 * mm, 22 * mm, 22 * mm, 20 * mm, 22 * mm, 26 * mm])
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRASS),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRASS_SOFT]),
            ("GRID", (0, 0), (-1, -1), 0.5, LINE),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tabla)

    story.append(Spacer(1, 18))

    # ---- resumen total ----
    resumen_data = [
        ["Total horas trabajadas", f"{total_horas:.2f} h"],
        ["Total a pagar", _formatear_moneda(total_salario)],
    ]
    tabla_resumen = Table(resumen_data, colWidths=[60 * mm, 40 * mm])
    tabla_resumen.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(tabla_resumen)

    story.append(Spacer(1, 24))
    story.append(Paragraph(
        f"Generado el {datetime.now(ZONA_COLOMBIA).strftime('%d/%m/%Y %I:%M %p')}",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=MUTED),
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generar_pdf_reporte_general(business_nombre, desde, hasta, empleados, total_general):
    """
    empleados: lista de dicts [{empleado_nombre, total_horas, total_salario}, ...]
    (el mismo formato que devuelve calcular_salario_empleado)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=22 * mm,
        bottomMargin=18 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    style_titulo = ParagraphStyle(
        "Titulo", parent=styles["Title"], fontSize=18, textColor=INK, spaceAfter=2,
    )
    style_subtitulo = ParagraphStyle(
        "Subtitulo", parent=styles["Normal"], fontSize=11, textColor=MUTED, spaceAfter=14,
    )
    style_normal = ParagraphStyle(
        "NormalInk", parent=styles["Normal"], fontSize=10, textColor=INK,
    )

    story = []

    story.append(Paragraph(business_nombre, style_subtitulo))
    story.append(Paragraph("Reporte general de nómina", style_titulo))
    story.append(Paragraph(
        f"Período: {desde.strftime('%d/%m/%Y')} al {hasta.strftime('%d/%m/%Y')}",
        style_subtitulo,
    ))
    story.append(Spacer(1, 6))

    encabezado = ["Empleado", "Horas trabajadas", "Salario a pagar"]
    datos_tabla = [encabezado]

    for e in empleados:
        datos_tabla.append([
            e["empleado_nombre"],
            f"{e['total_horas']:.2f} h",
            _formatear_moneda(e["total_salario"]),
        ])

    if not empleados:
        story.append(Paragraph("No hay empleados activos registrados.", style_normal))
    else:
        tabla = Table(datos_tabla, colWidths=[70 * mm, 45 * mm, 45 * mm])
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRASS),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRASS_SOFT]),
            ("GRID", (0, 0), (-1, -1), 0.5, LINE),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(tabla)

    story.append(Spacer(1, 18))

    tabla_total = Table([["Total general a pagar", _formatear_moneda(total_general)]], colWidths=[70 * mm, 45 * mm])
    tabla_total.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("LINEABOVE", (0, 0), (-1, 0), 0.75, BRASS),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(tabla_total)

    story.append(Spacer(1, 24))
    story.append(Paragraph(
        f"Generado el {datetime.now(ZONA_COLOMBIA).strftime('%d/%m/%Y %I:%M %p')}",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=MUTED),
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer