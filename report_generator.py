import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from config import OUTPUT_DIR

STYLES = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "TitleStyle", parent=STYLES["Title"], fontSize=20, textColor=colors.HexColor("#0f172a")
)
SUB_STYLE = ParagraphStyle(
    "SubStyle", parent=STYLES["Normal"], fontSize=10, textColor=colors.HexColor("#475569")
)
SECTION_STYLE = ParagraphStyle(
    "SectionStyle", parent=STYLES["Heading2"], fontSize=14,
    textColor=colors.HexColor("#1e3a8a"), spaceBefore=14, spaceAfter=6
)

RISK_COLORS = {
    "CRITICAL": colors.HexColor("#dc2626"),
    "WARNING": colors.HexColor("#ea580c"),
    "WATCH": colors.HexColor("#ca8a04"),
    "SAFE": colors.HexColor("#16a34a"),
}


def generate_district_report(results, filename=None):
    """
    results: list of village risk dicts (from RiskEngine, includes breakdown/cloudburst/glof)
    Returns the filepath of the generated PDF.
    """
    filename = filename or f"floodshield_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm
    )
    elements = []

    # Header
    elements.append(Paragraph("🌊 FloodShield — District Risk Report", TITLE_STYLE))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')} | "
        f"Multi-Hazard Flash Flood Early Warning System", SUB_STYLE
    ))
    elements.append(Spacer(1, 12))

    # Summary
    total_people_at_risk = sum(r["people_at_risk"] for r in results)
    critical_count = sum(1 for r in results if r["risk_level"] == "CRITICAL")
    warning_count = sum(1 for r in results if r["risk_level"] == "WARNING")

    summary_data = [
        ["Total Villages Monitored", str(len(results))],
        ["Critical Risk Villages", str(critical_count)],
        ["Warning Level Villages", str(warning_count)],
        ["Total Population at Risk", f"{total_people_at_risk:,}"],
    ]
    summary_table = Table(summary_data, colWidths=[9 * cm, 6 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 16))

    # Village breakdown table
    elements.append(Paragraph("Village-Level Risk Assessment", SECTION_STYLE))

    table_data = [["Village", "Risk Score", "Level", "Cloudburst", "GLOF Risk", "People at Risk"]]
    for r in results:
        table_data.append([
            r["name"],
            f"{r['risk_score']}/100",
            r["risk_level"],
            r["cloudburst"]["level"].replace("_", " "),
            r["glof"]["risk_level"] if r["glof"]["applicable"] else "N/A",
            f"{r['people_at_risk']:,}"
        ])

    village_table = Table(table_data, colWidths=[3.2 * cm, 2.3 * cm, 2.3 * cm, 3.2 * cm, 2.5 * cm, 3 * cm])
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    for i, r in enumerate(results, start=1):
        style_commands.append(("TEXTCOLOR", (2, i), (2, i), RISK_COLORS.get(r["risk_level"], colors.black)))
        style_commands.append(("FONTNAME", (2, i), (2, i), "Helvetica-Bold"))
    village_table.setStyle(TableStyle(style_commands))
    elements.append(village_table)
    elements.append(Spacer(1, 16))

    # Priority action section
    critical_villages = [r for r in results if r["risk_level"] in ("CRITICAL", "WARNING")]
    if critical_villages:
        elements.append(Paragraph("Priority Action Required", SECTION_STYLE))
        for r in critical_villages:
            elements.append(Paragraph(
                f"<b>{r['name']}</b> — {r['risk_level']} ({r['risk_score']}/100). "
                f"Rainfall score: {r['breakdown']['rainfall']}, Soil Saturation: {r['breakdown']['soil']}, "
                f"Cloudburst: {r['cloudburst']['level'].replace('_', ' ')}. "
                f"Estimated {r['people_at_risk']:,} people require evacuation readiness.",
                STYLES["Normal"]
            ))
            elements.append(Spacer(1, 6))

    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        "This report was auto-generated by FloodShield using real-time data from Open-Meteo "
        "and USGS Earthquake API. Data reflects multi-factor risk analysis including rainfall, "
        "terrain slope, soil saturation, elevation, cloudburst detection, and glacial lake "
        "outburst flood (GLOF) risk.",
        SUB_STYLE
    ))

    doc.build(elements)
    return filepath