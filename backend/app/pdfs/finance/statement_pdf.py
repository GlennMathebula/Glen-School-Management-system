from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import (
    TA_CENTER,
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
    "StatementCompany",
    fontName="Helvetica-Bold",
    fontSize=17,
    leading=20,
    textColor=NAVY,
)

TAGLINE_STYLE = ParagraphStyle(
    "StatementTagline",
    fontName="Helvetica",
    fontSize=8.5,
    leading=10,
    textColor=NAVY,
)

TITLE_STYLE = ParagraphStyle(
    "StatementTitle",
    fontName="Helvetica-Bold",
    fontSize=17,
    leading=20,
    alignment=TA_RIGHT,
    textColor=NAVY,
)

SUBTITLE_STYLE = ParagraphStyle(
    "StatementSubtitle",
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    alignment=TA_RIGHT,
    textColor=colors.HexColor("#6C7785"),
)

LABEL_STYLE = ParagraphStyle(
    "StatementLabel",
    fontName="Helvetica-Bold",
    fontSize=7.5,
    leading=9,
    textColor=NAVY,
)

VALUE_STYLE = ParagraphStyle(
    "StatementValue",
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=TEXT,
)

HEADER_STYLE = ParagraphStyle(
    "StatementTableHeader",
    fontName="Helvetica-Bold",
    fontSize=7,
    leading=8,
    alignment=TA_CENTER,
    textColor=WHITE,
)

CELL_STYLE = ParagraphStyle(
    "StatementCell",
    fontName="Helvetica",
    fontSize=7,
    leading=8.5,
    textColor=TEXT,
)

MONEY_STYLE = ParagraphStyle(
    "StatementMoney",
    fontName="Helvetica",
    fontSize=7,
    leading=8.5,
    textColor=TEXT,
    alignment=TA_RIGHT,
)

SUMMARY_LABEL = ParagraphStyle(
    "StatementSummaryLabel",
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=10,
    textColor=NAVY,
)

SUMMARY_VALUE = ParagraphStyle(
    "StatementSummaryValue",
    fontName="Helvetica-Bold",
    fontSize=8.5,
    leading=10,
    textColor=NAVY,
    alignment=TA_RIGHT,
)

OUTSTANDING_LABEL = ParagraphStyle(
    "StatementOutstandingLabel",
    fontName="Helvetica-Bold",
    fontSize=9,
    leading=11,
    textColor=NAVY_DARK,
)

OUTSTANDING_VALUE = ParagraphStyle(
    "StatementOutstandingValue",
    fontName="Helvetica-Bold",
    fontSize=12,
    leading=14,
    textColor=NAVY_DARK,
    alignment=TA_RIGHT,
)

NOTE_STYLE = ParagraphStyle(
    "StatementNote",
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

    if not value:
        return default

    return value


def money(
    value,
) -> str:

    return (
        f"R "
        f"{float(value or 0):,.2f}"
    )


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
                "StatementLogoFallback",
                fontName="Helvetica-Bold",
                fontSize=22,
                textColor=NAVY,
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
            "STATEMENT OF ACCOUNT",
            TITLE_STYLE,
        ),
        Paragraph(
            "STUDENT FINANCE STATEMENT",
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
            88 * mm,
            60 * mm,
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
# STUDENT INFORMATION
# ============================================================

def build_student_information(
    data: dict,
) -> list:

    elements = []

    rows = [
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
        ],
        [
            Paragraph(
                "Funding Type",
                LABEL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "funding_type"
                    )
                ),
                VALUE_STYLE,
            ),
            Paragraph(
                "Account Status",
                LABEL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "account_status"
                    )
                ),
                VALUE_STYLE,
            ),
        ],
    ]

    top_table = Table(
        rows,
        colWidths=[
            30 * mm,
            60 * mm,
            28 * mm,
            62 * mm,
        ],
    )

    top_table.setStyle(
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
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    elements.append(
        top_table
    )

    programme_table = Table(
        [
            [
                Paragraph(
                    "Programme",
                    LABEL_STYLE,
                ),
                Paragraph(
                    clean_text(
                        data.get(
                            "course_name"
                        )
                    ),
                    VALUE_STYLE,
                ),
            ]
        ],
        colWidths=[
            30 * mm,
            150 * mm,
        ],
    )

    programme_table.setStyle(
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
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    elements.append(
        programme_table
    )

    return elements


# ============================================================
# TRANSACTION TABLE
# ============================================================

def build_transaction_table(
    data: dict,
) -> Table:

    rows = [
        [
            Paragraph(
                "DATE",
                HEADER_STYLE,
            ),
            Paragraph(
                "REFERENCE",
                HEADER_STYLE,
            ),
            Paragraph(
                "DESCRIPTION",
                HEADER_STYLE,
            ),
            Paragraph(
                "DEBIT",
                HEADER_STYLE,
            ),
            Paragraph(
                "CREDIT",
                HEADER_STYLE,
            ),
            Paragraph(
                "BALANCE",
                HEADER_STYLE,
            ),
        ]
    ]

    for transaction in data.get(
        "transactions",
        [],
    ):

        debit = transaction.get(
            "debit"
        )

        credit = transaction.get(
            "credit"
        )

        rows.append(
            [
                Paragraph(
                    clean_text(
                        transaction.get(
                            "date"
                        )
                    ),
                    CELL_STYLE,
                ),
                Paragraph(
                    clean_text(
                        transaction.get(
                            "reference"
                        )
                    ),
                    CELL_STYLE,
                ),
                Paragraph(
                    clean_text(
                        transaction.get(
                            "description"
                        )
                    ),
                    CELL_STYLE,
                ),
                Paragraph(
                    money(debit)
                    if debit
                    else "-",
                    MONEY_STYLE,
                ),
                Paragraph(
                    money(credit)
                    if credit
                    else "-",
                    MONEY_STYLE,
                ),
                Paragraph(
                    money(
                        transaction.get(
                            "balance"
                        )
                    ),
                    MONEY_STYLE,
                ),
            ]
        )

    table = Table(
        rows,
        colWidths=[
            24 * mm,
            34 * mm,
            58 * mm,
            21 * mm,
            21 * mm,
            22 * mm,
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
                    0.35,
                    MID_GREY,
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
                    4,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
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
# ACCOUNT SUMMARY
# ============================================================

def build_summary(
    data: dict,
) -> Table:

    rows = [
        [
            Paragraph(
                "ACCOUNT SUMMARY",
                ParagraphStyle(
                    "StatementSummaryHeading",
                    fontName="Helvetica-Bold",
                    fontSize=9,
                    textColor=WHITE,
                ),
            ),
            "",
        ],
        [
            Paragraph(
                "Total Charges",
                SUMMARY_LABEL,
            ),
            Paragraph(
                money(
                    data.get(
                        "total_charges"
                    )
                ),
                SUMMARY_VALUE,
            ),
        ],
        [
            Paragraph(
                "Total Payments",
                SUMMARY_LABEL,
            ),
            Paragraph(
                money(
                    data.get(
                        "total_payments"
                    )
                ),
                SUMMARY_VALUE,
            ),
        ],
        [
            Paragraph(
                "Outstanding Balance",
                OUTSTANDING_LABEL,
            ),
            Paragraph(
                money(
                    data.get(
                        "outstanding"
                    )
                ),
                OUTSTANDING_VALUE,
            ),
        ],
    ]

    table = Table(
        rows,
        colWidths=[
            85 * mm,
            55 * mm,
        ],
        hAlign="RIGHT",
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "SPAN",
                    (0, 0),
                    (1, 0),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    NAVY,
                ),
                (
                    "BACKGROUND",
                    (0, -1),
                    (-1, -1),
                    GOLD_LIGHT,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    MID_GREY,
                ),
                (
                    "LINEABOVE",
                    (0, -1),
                    (-1, -1),
                    1,
                    GOLD,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
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

def generate_statement_pdf(
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
        title=(
            "Glen Moniques "
            "Student Account Statement"
        ),
        author=COMPANY_NAME,
    )

    story = []

    story.append(
        build_header()
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.extend(
        build_student_information(
            data
        )
    )

    story.append(
        Spacer(
            1,
            7 * mm,
        )
    )

    story.append(
        build_transaction_table(
            data
        )
    )

    story.append(
        Spacer(
            1,
            7 * mm,
        )
    )

    story.append(
        build_summary(
            data
        )
    )

    story.append(
        Spacer(
            1,
            7 * mm,
        )
    )

    story.append(
        Paragraph(
            "<b>IMPORTANT INFORMATION</b>",
            ParagraphStyle(
                "StatementInfoHeading",
                fontName="Helvetica-Bold",
                fontSize=8,
                textColor=NAVY,
            ),
        )
    )

    story.append(
        Spacer(
            1,
            1.5 * mm,
        )
    )

    story.append(
        Paragraph(
            (
                "This statement reflects transactions recorded "
                "on your Glen Moniques student account. Please "
                "use the relevant invoice or payment reference "
                "when making finance enquiries."
            ),
            NOTE_STYLE,
        )
    )

    document.build(
        story,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer,
    )

    return output_path