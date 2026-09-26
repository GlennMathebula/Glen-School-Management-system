from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#0B2E59")
DARK_NAVY = colors.HexColor("#082341")
GOLD = colors.HexColor("#F2B01E")
LIGHT_BLUE = colors.HexColor("#F4F8FC")
LIGHT_GOLD = colors.HexColor("#FFF3CD")
MID_GREY = colors.HexColor("#D9E0E7")
TEXT = colors.HexColor("#1E2A35")
WHITE = colors.white


COMPANY_NAME = "GLEN MONIQUES (PTY) LTD"
TAGLINE = "Hi tirhela n’wana"
PHONE = "015 880 2413"
EMAIL = "admin@glenmoniques.co.za"
WEBSITE = "www.glenmoniques.co.za"
ADDRESS = "Xitlhelani Village, Malamulele, Limpopo"


TITLE_STYLE = ParagraphStyle(
    "Title",
    fontName="Helvetica-Bold",
    fontSize=17,
    leading=20,
    textColor=NAVY,
    alignment=TA_CENTER,
)

BODY_STYLE = ParagraphStyle(
    "Body",
    fontName="Helvetica",
    fontSize=9,
    leading=13,
    textColor=TEXT,
)

LABEL_STYLE = ParagraphStyle(
    "Label",
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=10,
    textColor=NAVY,
)

VALUE_STYLE = ParagraphStyle(
    "Value",
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=TEXT,
)

COMPANY_STYLE = ParagraphStyle(
    "Company",
    fontName="Helvetica-Bold",
    fontSize=15,
    leading=17,
    textColor=NAVY,
)

TAGLINE_STYLE = ParagraphStyle(
    "Tagline",
    fontName="Helvetica",
    fontSize=8.2,
    leading=10,
    textColor=NAVY,
)

CONTACT_STYLE = ParagraphStyle(
    "Contact",
    fontName="Helvetica",
    fontSize=6.7,
    leading=8,
    textColor=DARK_NAVY,
)


def clean(value: Any, default: str = "") -> str:
    if value is None:
        return default

    value = str(value).strip()
    return value if value else default


def find_logo() -> Path | None:
    assets = (
        Path(__file__)
        .resolve()
        .parents[2]
        / "assets"
    )

    if not assets.exists():
        return None

    for candidate in assets.iterdir():
        if (
            candidate.is_file()
            and candidate.suffix.lower()
            in {".png", ".jpg", ".jpeg"}
            and "logo" in candidate.name.lower()
        ):
            return candidate

    return None


def build_header() -> Table:
    logo_path = find_logo()

    if logo_path:
        logo = Image(
            str(logo_path),
            width=24 * mm,
            height=17 * mm,
        )
    else:
        logo = Paragraph(
            "<b>GM</b>",
            COMPANY_STYLE,
        )

    text_block = Table(
        [
            [
                Paragraph(
                    COMPANY_NAME,
                    COMPANY_STYLE,
                )
            ],
            [
                Paragraph(
                    TAGLINE,
                    TAGLINE_STYLE,
                )
            ],
            [
                Paragraph(
                    ADDRESS,
                    CONTACT_STYLE,
                )
            ],
            [
                Paragraph(
                    (
                        f"{PHONE} | "
                        f"{EMAIL} | "
                        f"{WEBSITE}"
                    ),
                    CONTACT_STYLE,
                )
            ],
        ],
        colWidths=[148 * mm],
    )

    text_block.setStyle(
        TableStyle(
            [
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    1,
                ),
            ]
        )
    )

    header = Table(
        [[logo, text_block]],
        colWidths=[
            29 * mm,
            151 * mm,
        ],
    )

    header.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
            ]
        )
    )

    return header


def generate_fisa_admission_letter_pdf(
    output_path: str | Path,
    data: dict,
) -> Path:
    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=13 * mm,
        bottomMargin=15 * mm,
        title="FISA Admission Letter",
        author=COMPANY_NAME,
    )

    details = Table(
        [
            [
                Paragraph(
                    "Student Number",
                    LABEL_STYLE,
                ),
                Paragraph(
                    clean(
                        data.get(
                            "student_number"
                        )
                    ),
                    VALUE_STYLE,
                ),
            ],
            [
                Paragraph(
                    "Learner",
                    LABEL_STYLE,
                ),
                Paragraph(
                    clean(
                        data.get(
                            "student_name"
                        )
                    ),
                    VALUE_STYLE,
                ),
            ],
            [
                Paragraph(
                    "Programme",
                    LABEL_STYLE,
                ),
                Paragraph(
                    clean(
                        data.get(
                            "course_name"
                        )
                    ),
                    VALUE_STYLE,
                ),
            ],
            [
                Paragraph(
                    "FISA Reference",
                    LABEL_STYLE,
                ),
                Paragraph(
                    clean(
                        data.get(
                            "sitting_reference"
                        )
                    ),
                    VALUE_STYLE,
                ),
            ],
            [
                Paragraph(
                    "Assessment Date",
                    LABEL_STYLE,
                ),
                Paragraph(
                    clean(
                        data.get(
                            "assessment_date"
                        )
                    ),
                    VALUE_STYLE,
                ),
            ],
            [
                Paragraph(
                    "Reporting Time",
                    LABEL_STYLE,
                ),
                Paragraph(
                    clean(
                        data.get(
                            "reporting_time"
                        )
                    ),
                    VALUE_STYLE,
                ),
            ],
            [
                Paragraph(
                    "Assessment Time",
                    LABEL_STYLE,
                ),
                Paragraph(
                    (
                        f"{clean(data.get('start_time'))}"
                        f" - "
                        f"{clean(data.get('end_time'))}"
                    ),
                    VALUE_STYLE,
                ),
            ],
            [
                Paragraph(
                    "Venue",
                    LABEL_STYLE,
                ),
                Paragraph(
                    clean(
                        data.get(
                            "venue"
                        )
                    ),
                    VALUE_STYLE,
                ),
            ],
            [
                Paragraph(
                    "Assessment Centre",
                    LABEL_STYLE,
                ),
                Paragraph(
                    clean(
                        data.get(
                            "assessment_centre"
                        )
                    ),
                    VALUE_STYLE,
                ),
            ],
            [
                Paragraph(
                    "Seat Number",
                    LABEL_STYLE,
                ),
                Paragraph(
                    clean(
                        data.get(
                            "seat_number"
                        )
                    ),
                    VALUE_STYLE,
                ),
            ],
        ],
        colWidths=[
            42 * mm,
            132 * mm,
        ],
    )

    details.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    MID_GREY,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    LIGHT_BLUE,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
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

    instructions = clean(
        data.get("instructions"),
        (
            "Bring your original identification "
            "document and required stationery."
        ),
    )

    story = [
        build_header(),

        Spacer(
            1,
            3 * mm,
        ),

        Table(
            [[""]],
            colWidths=[174 * mm],
            rowHeights=[1.5 * mm],
            style=TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        GOLD,
                    )
                ]
            ),
        ),

        Spacer(
            1,
            7 * mm,
        ),

        Paragraph(
            "FISA ADMISSION LETTER",
            TITLE_STYLE,
        ),

        Spacer(
            1,
            7 * mm,
        ),

        Paragraph(
            (
                f"Dear "
                f"<b>{clean(data.get('student_name'))}</b>,"
            ),
            BODY_STYLE,
        ),

        Spacer(
            1,
            4 * mm,
        ),

        Paragraph(
            (
                "This letter confirms that you have been "
                "admitted to the Final Integrated Summative "
                "Assessment (FISA) for the programme indicated below."
            ),
            BODY_STYLE,
        ),

        Spacer(
            1,
            6 * mm,
        ),

        details,

        Spacer(
            1,
            6 * mm,
        ),

        Table(
            [
                [
                    Paragraph(
                        "<b>ASSESSMENT INSTRUCTIONS</b>",
                        LABEL_STYLE,
                    )
                ],
                [
                    Paragraph(
                        instructions,
                        BODY_STYLE,
                    )
                ],
            ],
            colWidths=[174 * mm],
            style=TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        LIGHT_GOLD,
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        GOLD,
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
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
            ),
        ),

        Spacer(
            1,
            8 * mm,
        ),

        Paragraph(
            (
                "<b>Please arrive at the reporting time shown above.</b> "
                "Late admission to the assessment venue may be subject "
                "to the assessment centre rules."
            ),
            BODY_STYLE,
        ),

        Spacer(
            1,
            12 * mm,
        ),

        Paragraph(
            "____________________________",
            BODY_STYLE,
        ),

        Paragraph(
            "Principal / Academic Manager",
            LABEL_STYLE,
        ),
    ]

    document.build(story)

    return output_path