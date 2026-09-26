from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import (
    TA_CENTER,
    TA_LEFT,
    TA_RIGHT,
)
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

# ============================================================
# BRAND
# ============================================================

NAVY = colors.HexColor("#0B2E59")
NAVY_DARK = colors.HexColor("#082341")
GOLD = colors.HexColor("#F2B01E")
GOLD_LIGHT = colors.HexColor("#FFF3CD")
LIGHT_BLUE = colors.HexColor("#F4F8FC")
MID_GREY = colors.HexColor("#D9E0E7")
GREEN_LIGHT = colors.HexColor("#E4F5E9")
GREEN = colors.HexColor("#1E7B42")
TEXT = colors.HexColor("#1E2A35")
WHITE = colors.white


COMPANY_NAME = "GLEN MONIQUES (PTY) LTD"
TAGLINE = "Hi tirhela n'wina"

PHONE = "015 880 2413"
EMAIL = "admin@glenmoniques.co.za"
WEBSITE = "www.glenmoniques.co.za"


# ============================================================
# STYLES
# ============================================================

COMPANY_STYLE = ParagraphStyle(
    "ReceiptCompany",
    fontName="Helvetica-Bold",
    fontSize=17,
    leading=20,
    textColor=NAVY,
    alignment=TA_LEFT,
)

TAGLINE_STYLE = ParagraphStyle(
    "ReceiptTagline",
    fontName="Helvetica",
    fontSize=8.5,
    leading=10,
    textColor=NAVY,
    alignment=TA_LEFT,
)

TITLE_STYLE = ParagraphStyle(
    "ReceiptTitle",
    fontName="Helvetica-Bold",
    fontSize=20,
    leading=23,
    textColor=NAVY,
    alignment=TA_RIGHT,
)

SUBTITLE_STYLE = ParagraphStyle(
    "ReceiptSubtitle",
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=colors.HexColor("#6C7785"),
    alignment=TA_RIGHT,
)

LABEL_STYLE = ParagraphStyle(
    "ReceiptLabel",
    fontName="Helvetica-Bold",
    fontSize=7.5,
    leading=9,
    textColor=NAVY,
)

VALUE_STYLE = ParagraphStyle(
    "ReceiptValue",
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=TEXT,
)

AMOUNT_LABEL = ParagraphStyle(
    "ReceiptAmountLabel",
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=12,
    textColor=NAVY_DARK,
)

AMOUNT_VALUE = ParagraphStyle(
    "ReceiptAmountValue",
    fontName="Helvetica-Bold",
    fontSize=17,
    leading=20,
    textColor=GREEN,
    alignment=TA_RIGHT,
)

NOTE_STYLE = ParagraphStyle(
    "ReceiptNote",
    fontName="Helvetica",
    fontSize=7,
    leading=9,
    textColor=colors.HexColor("#55616F"),
)


# ============================================================
# HELPERS
# ============================================================

def clean_text(
    value: Any,
    default: str = "",
) -> str:

    if value is None:
        return default

    value = str(value).strip()

    return value if value else default


def money(
    value,
) -> str:

    return f"R {float(value or 0):,.2f}"


def find_logo() -> Path | None:

    assets_directory = (
        Path(__file__)
        .resolve()
        .parents[2]
        / "assets"
    )

    possible_names = [
        "logo.png",
        "logo.jpg",
        "logo.jpeg",
        "glen_moniques_logo.png",
        "glen-moniques-logo.png",
        "GM Logo.png",
        "gm_logo.png",
    ]

    for name in possible_names:

        candidate = (
            assets_directory
            / name
        )

        if candidate.exists():
            return candidate

    if assets_directory.exists():

        for candidate in assets_directory.glob("*"):

            if (
                candidate.suffix.lower()
                in {
                    ".png",
                    ".jpg",
                    ".jpeg",
                }
                and "logo"
                in candidate.name.lower()
            ):
                return candidate

    return None


# ============================================================
# HEADER
# ============================================================

def build_header() -> Table:

    logo_path = find_logo()

    if logo_path:

        logo = Image(
            str(logo_path),
            width=28 * mm,
            height=20 * mm,
        )

    else:

        logo = Paragraph(
            "<b>GM</b>",
            ParagraphStyle(
                "ReceiptLogoFallback",
                fontName="Helvetica-Bold",
                fontSize=22,
                textColor=NAVY,
                alignment=TA_CENTER,
            ),
        )

    company_block = [
        Paragraph(
            COMPANY_NAME,
            COMPANY_STYLE,
        ),
        Paragraph(
            TAGLINE,
            TAGLINE_STYLE,
        ),
    ]

    title_block = [
        Paragraph(
            "RECEIPT",
            TITLE_STYLE,
        ),
        Paragraph(
            "OFFICIAL PAYMENT RECEIPT",
            SUBTITLE_STYLE,
        ),
    ]

    table = Table(
        [
            [
                logo,
                company_block,
                title_block,
            ]
        ],
        colWidths=[
            32 * mm,
            91 * mm,
            57 * mm,
        ],
    )

    table.setStyle(
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
                    0,
                ),
                (
                    "LINEBEFORE",
                    (2, 0),
                    (2, 0),
                    1.2,
                    GOLD,
                ),
                (
                    "LEFTPADDING",
                    (2, 0),
                    (2, 0),
                    6,
                ),
            ]
        )
    )

    return table


# ============================================================
# RECEIPT INFORMATION
# ============================================================

def build_receipt_information(
    data: dict,
) -> Table:

    rows = [
        [
            Paragraph(
                "Receipt Number",
                LABEL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "receipt_number"
                    )
                ),
                VALUE_STYLE,
            ),
            Paragraph(
                "Payment Date",
                LABEL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "payment_date"
                    )
                ),
                VALUE_STYLE,
            ),
        ],
        [
            Paragraph(
                "Student Number",
                LABEL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "student_number"
                    )
                ),
                VALUE_STYLE,
            ),
            Paragraph(
                "Payment Method",
                LABEL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "payment_method"
                    )
                ),
                VALUE_STYLE,
            ),
        ],
        [
            Paragraph(
                "Student Name",
                LABEL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "student_name"
                    )
                ),
                VALUE_STYLE,
            ),
            Paragraph(
                "Payment Reference",
                LABEL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "payment_reference"
                    )
                ),
                VALUE_STYLE,
            ),
        ],
    ]

    table = Table(
        rows,
        colWidths=[
            30 * mm,
            60 * mm,
            31 * mm,
            59 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    MID_GREY,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    LIGHT_BLUE,
                ),
                (
                    "BACKGROUND",
                    (2, 0),
                    (2, -1),
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
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
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

    return table


# ============================================================
# AMOUNT PAID
# ============================================================

def build_amount_box(
    data: dict,
) -> Table:

    rows = [
        [
            Paragraph(
                "AMOUNT RECEIVED",
                AMOUNT_LABEL,
            ),
            Paragraph(
                money(
                    data.get(
                        "amount"
                    )
                ),
                AMOUNT_VALUE,
            ),
        ]
    ]

    table = Table(
        rows,
        colWidths=[
            90 * mm,
            90 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    GREEN_LIGHT,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    GREEN,
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
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
            ]
        )
    )

    return table


# ============================================================
# EXTERNAL REFERENCE
# ============================================================

def build_external_reference(
    data: dict,
) -> Table:

    table = Table(
        [
            [
                Paragraph(
                    "External / Bank Reference",
                    LABEL_STYLE,
                ),
                Paragraph(
                    clean_text(
                        data.get(
                            "external_reference"
                        ),
                        "N/A",
                    ),
                    VALUE_STYLE,
                ),
            ]
        ],
        colWidths=[
            45 * mm,
            135 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    MID_GREY,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
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
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
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

    return table


# ============================================================
# FOOTER
# ============================================================

def draw_footer(
    canvas,
    document,
):

    canvas.saveState()

    width, _ = A4

    canvas.setStrokeColor(
        GOLD
    )

    canvas.setLineWidth(
        1
    )

    canvas.line(
        16 * mm,
        13 * mm,
        width - 16 * mm,
        13 * mm,
    )

    canvas.setFillColor(
        NAVY
    )

    canvas.setFont(
        "Helvetica",
        6.5,
    )

    canvas.drawCentredString(
        width / 2,
        8 * mm,
        (
            f"{PHONE}   |   "
            f"{EMAIL}   |   "
            f"{WEBSITE}"
        ),
    )

    canvas.restoreState()


# ============================================================
# GENERATE
# ============================================================

def generate_receipt_pdf(
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
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=14 * mm,
        bottomMargin=18 * mm,
        title="Glen Moniques Payment Receipt",
        author=COMPANY_NAME,
    )

    story = [
        build_header(),

        Spacer(
            1,
            6 * mm,
        ),

        build_receipt_information(
            data
        ),

        Spacer(
            1,
            6 * mm,
        ),

        build_external_reference(
            data
        ),

        Spacer(
            1,
            8 * mm,
        ),

        build_amount_box(
            data
        ),

        Spacer(
            1,
            8 * mm,
        ),

        Paragraph(
            "<b>PAYMENT CONFIRMATION</b>",
            ParagraphStyle(
                "ReceiptConfirmationHeading",
                fontName="Helvetica-Bold",
                fontSize=8,
                textColor=NAVY,
            ),
        ),

        Spacer(
            1,
            2 * mm,
        ),

        Paragraph(
            (
                "This receipt confirms that the above payment "
                "has been recorded against the student's "
                "Glen Moniques finance account."
            ),
            NOTE_STYLE,
        ),

        Spacer(
            1,
            2 * mm,
        ),

        Paragraph(
            (
                "This is a system-generated receipt. "
                "Its validity is subject to the corresponding "
                "payment record in the Glen Moniques "
                "School Management System."
            ),
            NOTE_STYLE,
        ),
    ]

    document.build(
        story,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer,
    )

    return output_path