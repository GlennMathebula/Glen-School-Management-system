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
LIGHT_GREY = colors.HexColor("#F5F5F5")
MID_GREY = colors.HexColor("#D9E0E7")
TEXT = colors.HexColor("#1E2A35")
WHITE = colors.white


# ============================================================
# COMPANY DETAILS
# ============================================================

COMPANY_NAME = "GLEN MONIQUES (PTY) LTD"
TAGLINE = "Hi tirhela n'wina"

PHONE = "015 880 2413"
EMAIL = "admin@glenmoniques.co.za"
WEBSITE = "www.glenmoniques.co.za"


# ============================================================
# STYLES
# ============================================================

COMPANY_STYLE = ParagraphStyle(
    "InvoiceCompany",
    fontName="Helvetica-Bold",
    fontSize=17,
    leading=20,
    textColor=NAVY,
    alignment=TA_LEFT,
)

TAGLINE_STYLE = ParagraphStyle(
    "InvoiceTagline",
    fontName="Helvetica",
    fontSize=8.5,
    leading=10,
    textColor=NAVY,
    alignment=TA_LEFT,
)

DOCUMENT_TITLE = ParagraphStyle(
    "InvoiceDocumentTitle",
    fontName="Helvetica-Bold",
    fontSize=20,
    leading=23,
    textColor=NAVY,
    alignment=TA_RIGHT,
)

DOCUMENT_SUBTITLE = ParagraphStyle(
    "InvoiceDocumentSubtitle",
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=colors.HexColor("#6C7785"),
    alignment=TA_RIGHT,
    spaceAfter=0,
)

LABEL_STYLE = ParagraphStyle(
    "InvoiceLabel",
    fontName="Helvetica-Bold",
    fontSize=7.5,
    leading=9,
    textColor=NAVY,
)

VALUE_STYLE = ParagraphStyle(
    "InvoiceValue",
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=TEXT,
)

VALUE_RIGHT_STYLE = ParagraphStyle(
    "InvoiceValueRight",
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=TEXT,
    alignment=TA_RIGHT,
)

TABLE_HEADER = ParagraphStyle(
    "InvoiceTableHeader",
    fontName="Helvetica-Bold",
    fontSize=7.5,
    leading=9,
    textColor=WHITE,
    alignment=TA_CENTER,
)

TABLE_TEXT = ParagraphStyle(
    "InvoiceTableText",
    fontName="Helvetica",
    fontSize=7.5,
    leading=9,
    textColor=TEXT,
)

TABLE_TEXT_RIGHT = ParagraphStyle(
    "InvoiceTableTextRight",
    fontName="Helvetica",
    fontSize=7.5,
    leading=9,
    textColor=TEXT,
    alignment=TA_RIGHT,
)

SUMMARY_LABEL = ParagraphStyle(
    "InvoiceSummaryLabel",
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=10,
    textColor=NAVY,
)

SUMMARY_VALUE = ParagraphStyle(
    "InvoiceSummaryValue",
    fontName="Helvetica-Bold",
    fontSize=9,
    leading=11,
    textColor=NAVY,
    alignment=TA_RIGHT,
)

OUTSTANDING_LABEL = ParagraphStyle(
    "InvoiceOutstandingLabel",
    fontName="Helvetica-Bold",
    fontSize=9,
    leading=11,
    textColor=NAVY_DARK,
)

OUTSTANDING_VALUE = ParagraphStyle(
    "InvoiceOutstandingValue",
    fontName="Helvetica-Bold",
    fontSize=12,
    leading=14,
    textColor=NAVY_DARK,
    alignment=TA_RIGHT,
)

NOTE_STYLE = ParagraphStyle(
    "InvoiceNote",
    fontName="Helvetica",
    fontSize=7,
    leading=9,
    textColor=colors.HexColor("#55616F"),
)

FOOTER_STYLE = ParagraphStyle(
    "InvoiceFooter",
    fontName="Helvetica",
    fontSize=6.5,
    leading=8,
    textColor=NAVY,
    alignment=TA_CENTER,
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

        if candidate.suffix.lower() in {
            ".png",
            ".jpg",
            ".jpeg",
        }:

            if "logo" in candidate.name.lower():
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
                "LogoFallback",
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
            "INVOICE",
            DOCUMENT_TITLE,
        ),
        Paragraph(
            "STUDENT ACCOUNT",
            DOCUMENT_SUBTITLE,
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
# STUDENT / INVOICE INFORMATION
# ============================================================

def build_information_box(
    data: dict,
) -> list:

    elements = []

    top_rows = [
        [
            Paragraph(
                "Invoice Number",
                LABEL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "invoice_number"
                    )
                ),
                VALUE_STYLE,
            ),
            Paragraph(
                "Invoice Date",
                LABEL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "invoice_date"
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
                "Due Date",
                LABEL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "due_date"
                    ),
                    "Payable as arranged",
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
                "Status",
                LABEL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "status"
                    )
                ),
                VALUE_STYLE,
            ),
        ],
    ]

    top_table = Table(
        top_rows,
        colWidths=[
            30 * mm,
            60 * mm,
            25 * mm,
            65 * mm,
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

    elements.append(top_table)

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
# INVOICE ITEMS
# ============================================================

def build_items_table(
    data: dict,
) -> Table:

    rows = [
        [
            Paragraph(
                "#",
                TABLE_HEADER,
            ),
            Paragraph(
                "DESCRIPTION",
                TABLE_HEADER,
            ),
            Paragraph(
                "QTY",
                TABLE_HEADER,
            ),
            Paragraph(
                "UNIT PRICE",
                TABLE_HEADER,
            ),
            Paragraph(
                "AMOUNT",
                TABLE_HEADER,
            ),
        ]
    ]

    for index, item in enumerate(
        data.get(
            "items",
            [],
        ),
        start=1,
    ):

        rows.append(
            [
                Paragraph(
                    str(index),
                    TABLE_TEXT,
                ),
                Paragraph(
                    clean_text(
                        item.get(
                            "description"
                        )
                    ),
                    TABLE_TEXT,
                ),
                Paragraph(
                    clean_text(
                        item.get(
                            "quantity"
                        ),
                        "1",
                    ),
                    TABLE_TEXT_RIGHT,
                ),
                Paragraph(
                    money(
                        item.get(
                            "unit_price"
                        )
                    ),
                    TABLE_TEXT_RIGHT,
                ),
                Paragraph(
                    money(
                        item.get(
                            "line_total"
                        )
                    ),
                    TABLE_TEXT_RIGHT,
                ),
            ]
        )

    table = Table(
        rows,
        colWidths=[
            10 * mm,
            85 * mm,
            15 * mm,
            32 * mm,
            38 * mm,
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
                    "ALIGN",
                    (0, 1),
                    (0, -1),
                    "CENTER",
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
# PAYMENT SUMMARY
# ============================================================

def build_summary(
    data: dict,
) -> Table:

    rows = [
        [
            Paragraph(
                "PAYMENT SUMMARY",
                ParagraphStyle(
                    "SummaryHeading",
                    fontName="Helvetica-Bold",
                    fontSize=9,
                    textColor=WHITE,
                ),
            ),
        ],
        [
            Paragraph(
                "Total Charges",
                SUMMARY_LABEL,
            ),
            Paragraph(
                money(
                    data.get(
                        "total_amount"
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
                        "amount_paid"
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
            90 * mm,
            90 * mm,
        ],
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
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
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

    footer_text = (
        f"{PHONE}   |   "
        f"{EMAIL}   |   "
        f"{WEBSITE}"
    )

    canvas.drawCentredString(
        width / 2,
        8 * mm,
        footer_text,
    )

    canvas.restoreState()


# ============================================================
# GENERATE
# ============================================================

def generate_invoice_pdf(
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
        title="Glen Moniques Student Invoice",
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
        build_information_box(
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
        build_items_table(
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
            "<b>PAYMENT INFORMATION</b>",
            ParagraphStyle(
                "PaymentHeading",
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
                "Please use the invoice number as your payment "
                "reference when making payment. Payments made "
                "through the Student Portal will be updated "
                "automatically once confirmed."
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