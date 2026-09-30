from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#16294A")
GOLD = colors.HexColor("#F9A826")
LIGHT_GREY = colors.HexColor("#F3F4F6")
MID_GREY = colors.HexColor("#D1D5DB")
TEXT = colors.HexColor("#1F2937")
MUTED = colors.HexColor("#6B7280")


def _safe(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if hasattr(value, "strftime"):
        try:
            return value.strftime("%Y-%m-%d")
        except (TypeError, ValueError):
            pass
    return str(value)


def _find_logo() -> Path | None:
    app_dir = Path(__file__).resolve().parents[2]
    candidates = [
        app_dir / "assets" / "logo.png",
        app_dir / "assets" / "glen_moniques_logo.png",
        app_dir / "assets" / "glen-moniques-logo.png",
        app_dir.parent / "assets" / "logo.png",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _output_dir() -> Path:
    path = (
        Path(__file__).resolve().parents[2]
        / "generated_pdfs"
        / "reports"
    )
    path.mkdir(parents=True, exist_ok=True)
    return path


def _footer(canvas, doc) -> None:
    canvas.saveState()
    width, _ = doc.pagesize
    canvas.setStrokeColor(MID_GREY)
    canvas.setLineWidth(0.4)
    canvas.line(
        15 * mm,
        13 * mm,
        width - 15 * mm,
        13 * mm,
    )
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(
        15 * mm,
        8 * mm,
        "GLEN MONIQUES (PTY) LTD - QA & Compliance Report",
    )
    canvas.drawRightString(
        width - 15 * mm,
        8 * mm,
        f"Page {doc.page}",
    )
    canvas.restoreState()


def _styles() -> dict[str, ParagraphStyle]:
    return {
        "title": ParagraphStyle(
            "ReportTitle",
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=19,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=4 * mm,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=4 * mm,
        ),
        "section": ParagraphStyle(
            "ReportSection",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceBefore=2 * mm,
            spaceAfter=2 * mm,
        ),
        "body": ParagraphStyle(
            "ReportBody",
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=TEXT,
            alignment=TA_LEFT,
        ),
        "cell": ParagraphStyle(
            "ReportCell",
            fontName="Helvetica",
            fontSize=6.6,
            leading=8,
            textColor=TEXT,
            alignment=TA_LEFT,
        ),
        "cell_header": ParagraphStyle(
            "ReportCellHeader",
            fontName="Helvetica-Bold",
            fontSize=6.5,
            leading=8,
            textColor=colors.white,
            alignment=TA_LEFT,
        ),
    }


def generate_qa_compliance_report_pdf(
    report: dict,
    *,
    generated_by: str,
) -> str:
    columns = report.get("columns", [])
    rows = report.get("rows", [])
    page_size = landscape(A4) if len(columns) > 5 else A4

    safe_code = (
        str(report.get("code", "report"))
        .replace(".", "_")
        .replace("/", "_")
    )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = _output_dir() / f"{safe_code}_{timestamp}.pdf"

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=page_size,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=19 * mm,
        title=str(report.get("title", "QA & Compliance Report")),
        author="GLEN MONIQUES (PTY) LTD",
    )

    styles = _styles()
    story = []

    logo = _find_logo()
    if logo:
        try:
            image = Image(
                str(logo),
                width=34 * mm,
                height=18 * mm,
            )
            image.hAlign = "CENTER"
            story.extend([image, Spacer(1, 2 * mm)])
        except Exception:
            pass

    story.append(
        Paragraph(
            escape(str(report.get("title", "QA & Compliance Report"))),
            styles["title"],
        )
    )

    generated_at = datetime.now().strftime("%d %B %Y %H:%M")
    story.append(
        Paragraph(
            (
                f"{escape(str(report.get('category', 'QA & Compliance')))} | "
                f"Generated: {escape(generated_at)} | "
                f"Generated by: {escape(generated_by)}"
            ),
            styles["subtitle"],
        )
    )

    active_filters = [
        (
            key.replace("_", " ").title(),
            _safe(value),
        )
        for key, value in report.get("filters", {}).items()
        if value not in (None, "")
    ]

    if active_filters:
        story.append(Paragraph("Report Filters", styles["section"]))
        data = [
            [
                Paragraph(f"<b>{escape(key)}</b>", styles["body"]),
                Paragraph(escape(value), styles["body"]),
            ]
            for key, value in active_filters
        ]
        table = Table(data, colWidths=[42 * mm, None], hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), LIGHT_GREY),
                    ("BOX", (0, 0), (-1, -1), 0.4, MID_GREY),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, MID_GREY),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.extend([table, Spacer(1, 3 * mm)])

    summary = report.get("summary", {})
    if summary:
        story.append(Paragraph("Summary", styles["section"]))
        data = [
            [
                Paragraph(
                    f"<b>{escape(str(key).replace('_', ' ').title())}</b>",
                    styles["body"],
                ),
                Paragraph(escape(_safe(value)), styles["body"]),
            ]
            for key, value in summary.items()
        ]
        table = Table(data, colWidths=[48 * mm, None], hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#FFF7E6")),
                    ("BOX", (0, 0), (-1, -1), 0.4, MID_GREY),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, MID_GREY),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.extend([table, Spacer(1, 4 * mm)])

    story.append(Paragraph("Report Detail", styles["section"]))

    if not columns:
        story.append(
            Paragraph(
                "No report columns were configured.",
                styles["body"],
            )
        )
    elif not rows:
        story.append(
            Paragraph(
                "No records matched the selected report filters.",
                styles["body"],
            )
        )
    else:
        table_data = [
            [
                Paragraph(
                    escape(str(column["label"])),
                    styles["cell_header"],
                )
                for column in columns
            ]
        ]

        for row in rows:
            table_data.append(
                [
                    Paragraph(
                        escape(_safe(row.get(column["key"]))),
                        styles["cell"],
                    )
                    for column in columns
                ]
            )

        available_width = (
            page_size[0]
            - doc.leftMargin
            - doc.rightMargin
        )
        width = available_width / max(len(columns), 1)

        table = LongTable(
            table_data,
            repeatRows=1,
            colWidths=[width for _ in columns],
            hAlign="LEFT",
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.25, MID_GREY),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, LIGHT_GREY],
                    ),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(table)

    story.extend(
        [
            Spacer(1, 5 * mm),
            Paragraph(
                (
                    "System-generated QA & Compliance report. "
                    "Data reflects records available in the "
                    "Glen Moniques Student Management System "
                    "at the time of generation."
                ),
                styles["body"],
            ),
        ]
    )

    doc.build(
        story,
        onFirstPage=_footer,
        onLaterPages=_footer,
    )

    return str(output_path)
