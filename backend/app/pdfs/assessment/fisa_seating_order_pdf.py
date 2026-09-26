from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#0B2E59")
GOLD = colors.HexColor("#F2B01E")
LIGHT_BLUE = colors.HexColor("#F4F8FC")
MID_GREY = colors.HexColor("#D9E0E7")
TEXT = colors.HexColor("#1E2A35")
WHITE = colors.white


TITLE_STYLE = ParagraphStyle(
    "Title",
    fontName="Helvetica-Bold",
    fontSize=16,
    leading=19,
    textColor=NAVY,
    alignment=TA_CENTER,
)

INFO_STYLE = ParagraphStyle(
    "Info",
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=TEXT,
    alignment=TA_CENTER,
)

HEADER_STYLE = ParagraphStyle(
    "Header",
    fontName="Helvetica-Bold",
    fontSize=7.5,
    leading=9,
    textColor=WHITE,
    alignment=TA_CENTER,
)

CELL_STYLE = ParagraphStyle(
    "Cell",
    fontName="Helvetica",
    fontSize=7.5,
    leading=9,
    textColor=TEXT,
)


def generate_fisa_seating_order_pdf(
    output_path: str | Path,
    data: dict,
) -> Path:
    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title="FISA Seating Order",
    )

    rows = [
        [
            Paragraph(
                "Seat",
                HEADER_STYLE,
            ),
            Paragraph(
                "Student Number",
                HEADER_STYLE,
            ),
            Paragraph(
                "ID / Passport",
                HEADER_STYLE,
            ),
            Paragraph(
                "Learner Name",
                HEADER_STYLE,
            ),
        ]
    ]

    for candidate in data.get(
        "candidates",
        [],
    ):
        rows.append(
            [
                str(
                    candidate.get(
                        "seat_number",
                        "",
                    )
                ),
                candidate.get(
                    "student_number",
                    "",
                ),
                candidate.get(
                    "identity_number",
                    "",
                ),
                Paragraph(
                    candidate.get(
                        "student_name",
                        "",
                    ),
                    CELL_STYLE,
                ),
            ]
        )

    table = Table(
        rows,
        colWidths=[
            25 * mm,
            45 * mm,
            60 * mm,
            135 * mm,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    NAVY,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    MID_GREY,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (0, 1),
                    (2, -1),
                    "CENTER",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story = [
        Paragraph(
            "GLEN MONIQUES (PTY) LTD",
            TITLE_STYLE,
        ),

        Spacer(
            1,
            2 * mm,
        ),

        Paragraph(
            "FISA SEATING ORDER",
            TITLE_STYLE,
        ),

        Spacer(
            1,
            3 * mm,
        ),

        Paragraph(
            (
                f"{data.get('course_name', '')}<br/>"
                f"Reference: {data.get('sitting_reference', '')} | "
                f"Date: {data.get('assessment_date', '')} | "
                f"Venue: {data.get('venue', '')}"
            ),
            INFO_STYLE,
        ),

        Spacer(
            1,
            5 * mm,
        ),

        table,
    ]

    document.build(
        story
    )

    return output_path