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
MID_GREY = colors.HexColor("#D9E0E7")
TEXT = colors.HexColor("#1E2A35")
WHITE = colors.white


TITLE_STYLE = ParagraphStyle(
    "Title",
    fontName="Helvetica-Bold",
    fontSize=15,
    leading=18,
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
    fontSize=7,
    leading=8,
    textColor=WHITE,
    alignment=TA_CENTER,
)

CELL_STYLE = ParagraphStyle(
    "Cell",
    fontName="Helvetica",
    fontSize=7,
    leading=8.5,
    textColor=TEXT,
)

CENTER_STYLE = ParagraphStyle(
    "Center",
    fontName="Helvetica",
    fontSize=8,
    leading=9,
    textColor=TEXT,
    alignment=TA_CENTER,
)


def generate_fisa_attendance_register_pdf(
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
        leftMargin=8 * mm,
        rightMargin=8 * mm,
        topMargin=10 * mm,
        bottomMargin=12 * mm,
        title="FISA Attendance Register",
    )

    rows = [
        [
            Paragraph(
                "Seat",
                HEADER_STYLE,
            ),
            Paragraph(
                "Student No.",
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
            Paragraph(
                "✓",
                HEADER_STYLE,
            ),
            Paragraph(
                "Signature In",
                HEADER_STYLE,
            ),
            Paragraph(
                "✓",
                HEADER_STYLE,
            ),
            Paragraph(
                "Signature Out",
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
                Paragraph(
                    str(
                        candidate.get(
                            "seat_number",
                            "",
                        )
                    ),
                    CENTER_STYLE,
                ),
                Paragraph(
                    candidate.get(
                        "student_number",
                        "",
                    ),
                    CENTER_STYLE,
                ),
                Paragraph(
                    candidate.get(
                        "identity_number",
                        "",
                    ),
                    CENTER_STYLE,
                ),
                Paragraph(
                    candidate.get(
                        "student_name",
                        "",
                    ),
                    CELL_STYLE,
                ),
                "",
                "",
                "",
                "",
            ]
        )

    table = Table(
        rows,
        colWidths=[
            14 * mm,
            30 * mm,
            42 * mm,
            58 * mm,
            10 * mm,
            50 * mm,
            10 * mm,
            50 * mm,
        ],
        repeatRows=1,
        rowHeights=[
            10 * mm
        ] + [
            15 * mm
            for _ in data.get(
                "candidates",
                [],
            )
        ],
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
                    "ALIGN",
                    (4, 1),
                    (7, -1),
                    "CENTER",
                ),
            ]
        )
    )

    signoff_table = Table(
        [
            [
                Paragraph(
                    "Invigilator Signature:",
                    CELL_STYLE,
                ),
                "",
                Paragraph(
                    "Date:",
                    CELL_STYLE,
                ),
                "",
            ],
            [
                Paragraph(
                    "Principal Signature:",
                    CELL_STYLE,
                ),
                "",
                Paragraph(
                    "Date:",
                    CELL_STYLE,
                ),
                "",
            ],
        ],
        colWidths=[
            35 * mm,
            95 * mm,
            15 * mm,
            55 * mm,
        ],
        rowHeights=[
            12 * mm,
            12 * mm,
        ],
    )

    signoff_table.setStyle(
        TableStyle(
            [
                (
                    "LINEBELOW",
                    (1, 0),
                    (1, 0),
                    0.5,
                    TEXT,
                ),
                (
                    "LINEBELOW",
                    (3, 0),
                    (3, 0),
                    0.5,
                    TEXT,
                ),
                (
                    "LINEBELOW",
                    (1, 1),
                    (1, 1),
                    0.5,
                    TEXT,
                ),
                (
                    "LINEBELOW",
                    (3, 1),
                    (3, 1),
                    0.5,
                    TEXT,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "BOTTOM",
                ),
            ]
        )
    )

    story = [
        Paragraph(
            "GLEN MONIQUES (PTY) LTD",
            TITLE_STYLE,
        ),

        Paragraph(
            "FISA ATTENDANCE REGISTER",
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
                f"Time: {data.get('start_time', '')} - "
                f"{data.get('end_time', '')} | "
                f"Venue: {data.get('venue', '')}"
            ),
            INFO_STYLE,
        ),

        Spacer(
            1,
            5 * mm,
        ),

        table,

        Spacer(
            1,
            8 * mm,
        ),

        signoff_table,
    ]

    document.build(
        story
    )

    return output_path