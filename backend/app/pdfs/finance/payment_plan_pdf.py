from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ============================================================
# COMPANY DETAILS
# ============================================================

COMPANY_NAME = (
    "GLEN MONIQUES (PTY) LTD"
)

COMPANY_REG = (
    "2020/089305/07"
)

PHONE = (
    "015 880 2413"
)

EMAIL = (
    "admin@glenmoniques.co.za"
)

WEBSITE = (
    "www.glenmoniques.co.za"
)

TAGLINE = (
    "HI TIRHELA N'WINA"
)


# ============================================================
# BRAND COLOURS
# ============================================================

NAVY = colors.HexColor(
    "#0D1B2A"
)

GOLD = colors.HexColor(
    "#D4AF37"
)

LIGHT_GOLD = colors.HexColor(
    "#F5E9B8"
)

LIGHT_GREY = colors.HexColor(
    "#F5F6F7"
)

MID_GREY = colors.HexColor(
    "#D8DDE2"
)

TEXT_GREY = colors.HexColor(
    "#5D6670"
)

GREEN = colors.HexColor(
    "#1F7A4D"
)

RED = colors.HexColor(
    "#A63D40"
)

ORANGE = colors.HexColor(
    "#B26A00"
)

WHITE = colors.white


# ============================================================
# STYLES
# ============================================================

STYLES = (
    getSampleStyleSheet()
)


TITLE_STYLE = ParagraphStyle(
    "PaymentPlanTitle",
    parent=STYLES[
        "Heading1"
    ],
    fontName="Helvetica-Bold",
    fontSize=16,
    leading=19,
    textColor=NAVY,
    alignment=TA_CENTER,
    spaceAfter=3 * mm,
)


SUBTITLE_STYLE = ParagraphStyle(
    "PaymentPlanSubtitle",
    parent=STYLES[
        "Normal"
    ],
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=TEXT_GREY,
    alignment=TA_CENTER,
)


SECTION_STYLE = ParagraphStyle(
    "PaymentPlanSection",
    parent=STYLES[
        "Heading2"
    ],
    fontName="Helvetica-Bold",
    fontSize=9,
    leading=11,
    textColor=NAVY,
    spaceAfter=2 * mm,
)


BODY_STYLE = ParagraphStyle(
    "PaymentPlanBody",
    parent=STYLES[
        "Normal"
    ],
    fontName="Helvetica",
    fontSize=8,
    leading=11,
    textColor=NAVY,
)


SMALL_STYLE = ParagraphStyle(
    "PaymentPlanSmall",
    parent=STYLES[
        "Normal"
    ],
    fontName="Helvetica",
    fontSize=7,
    leading=9,
    textColor=TEXT_GREY,
)


# ============================================================
# HELPERS
# ============================================================

def clean_text(
    value,
    default: str = "-",
) -> str:

    if value is None:

        return default

    value = str(
        value
    ).strip()

    if not value:

        return default

    return value


def money(
    value,
) -> str:

    try:

        amount = float(
            value or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        amount = 0

    return (
        f"R {amount:,.2f}"
    )


def format_date(
    value,
) -> str:

    if value is None:

        return "-"

    if hasattr(
        value,
        "strftime",
    ):

        return value.strftime(
            "%d %B %Y"
        )

    return str(
        value
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
        "glen_moniques.png",
        "glenmoniques.png",
    ]

    for filename in possible_names:

        candidate = (
            assets_directory
            / filename
        )

        if candidate.exists():

            return candidate

    return None


def status_colour(
    status: str,
):

    status = clean_text(
        status,
        "",
    ).lower()

    if status in {
        "active",
        "paid",
        "completed",
    }:

        return GREEN

    if status in {
        "overdue",
        "defaulted",
        "cancelled",
    }:

        return RED

    if status in {
        "pending",
        "partially paid",
        "partial",
    }:

        return ORANGE

    return NAVY


# ============================================================
# HEADER
# ============================================================

def build_header():
    logo_path = (
        find_logo()
    )

    left_content = []

    if logo_path:

        from reportlab.platypus import Image

        logo = Image(
            str(
                logo_path
            ),
            width=25 * mm,
            height=25 * mm,
        )

        logo.hAlign = "LEFT"

        left_content.append(
            logo
        )

    else:

        left_content.append(
            Paragraph(
                "<b>GLEN MONIQUES</b>",
                ParagraphStyle(
                    "HeaderLogoFallback",
                    fontName="Helvetica-Bold",
                    fontSize=14,
                    textColor=NAVY,
                ),
            )
        )

    company_details = Paragraph(
        (
            f"<b>{COMPANY_NAME}</b><br/>"
            f"Reg: {COMPANY_REG}<br/>"
            f"{PHONE}<br/>"
            f"{EMAIL}<br/>"
            f"{WEBSITE}"
        ),
        ParagraphStyle(
            "HeaderCompanyDetails",
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            textColor=NAVY,
            alignment=2,
        ),
    )

    table = Table(
        [
            [
                left_content[
                    0
                ],
                company_details,
            ]
        ],
        colWidths=[
            65 * mm,
            110 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    "TOP",
                ),

                (
                    "BOTTOMPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    4 * mm,
                ),

                (
                    "LINEBELOW",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    1.5,
                    GOLD,
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
):

    rows = [
        [
            Paragraph(
                "<b>Student Number</b>",
                BODY_STYLE,
            ),

            Paragraph(
                clean_text(
                    data.get(
                        "student_number"
                    )
                ),
                BODY_STYLE,
            ),
        ],

        [
            Paragraph(
                "<b>Student Name</b>",
                BODY_STYLE,
            ),

            Paragraph(
                clean_text(
                    data.get(
                        "student_name"
                    )
                ),
                BODY_STYLE,
            ),
        ],

        [
            Paragraph(
                "<b>Programme</b>",
                BODY_STYLE,
            ),

            Paragraph(
                clean_text(
                    data.get(
                        "course_name"
                    )
                ),
                BODY_STYLE,
            ),
        ],
    ]

    table = Table(
        rows,
        colWidths=[
            42 * mm,
            133 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (
                        0,
                        0,
                    ),
                    (
                        0,
                        -1,
                    ),
                    LIGHT_GREY,
                ),

                (
                    "GRID",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    0.4,
                    MID_GREY,
                ),

                (
                    "VALIGN",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    "TOP",
                ),

                (
                    "LEFTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    3 * mm,
                ),

                (
                    "RIGHTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    3 * mm,
                ),

                (
                    "TOPPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    2.2 * mm,
                ),

                (
                    "BOTTOMPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    2.2 * mm,
                ),
            ]
        )
    )

    return table


# ============================================================
# PLAN INFORMATION
# ============================================================

def build_plan_information(
    data: dict,
):

    plan_status = clean_text(
        data.get(
            "status"
        )
    )

    rows = [
        [
            Paragraph(
                "<b>Payment Plan</b>",
                BODY_STYLE,
            ),

            Paragraph(
                clean_text(
                    data.get(
                        "plan_name"
                    )
                ),
                BODY_STYLE,
            ),
        ],

        [
            Paragraph(
                "<b>Start Date</b>",
                BODY_STYLE,
            ),

            Paragraph(
                format_date(
                    data.get(
                        "start_date"
                    )
                ),
                BODY_STYLE,
            ),
        ],

        [
            Paragraph(
                "<b>End Date</b>",
                BODY_STYLE,
            ),

            Paragraph(
                format_date(
                    data.get(
                        "end_date"
                    )
                ),
                BODY_STYLE,
            ),
        ],

        [
            Paragraph(
                "<b>Total Plan Amount</b>",
                BODY_STYLE,
            ),

            Paragraph(
                money(
                    data.get(
                        "total_plan_amount"
                    )
                ),
                BODY_STYLE,
            ),
        ],

        [
            Paragraph(
                "<b>Plan Status</b>",
                BODY_STYLE,
            ),

            Paragraph(
                (
                    f"<font color='"
                    f"{status_colour(plan_status).hexval()}"
                    f"'><b>"
                    f"{plan_status.upper()}"
                    f"</b></font>"
                ),
                BODY_STYLE,
            ),
        ],
    ]

    table = Table(
        rows,
        colWidths=[
            48 * mm,
            127 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (
                        0,
                        0,
                    ),
                    (
                        0,
                        -1,
                    ),
                    LIGHT_GOLD,
                ),

                (
                    "GRID",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    0.4,
                    MID_GREY,
                ),

                (
                    "VALIGN",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    "TOP",
                ),

                (
                    "LEFTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    3 * mm,
                ),

                (
                    "RIGHTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    3 * mm,
                ),

                (
                    "TOPPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    2.2 * mm,
                ),

                (
                    "BOTTOMPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    2.2 * mm,
                ),
            ]
        )
    )

    return table


# ============================================================
# INSTALLMENT TABLE
# ============================================================

def build_installment_table(
    data: dict,
):

    installments = (
        data.get(
            "installments"
        )
        or []
    )

    table_data = [
        [
            Paragraph(
                "<b>#</b>",
                BODY_STYLE,
            ),

            Paragraph(
                "<b>Due Date</b>",
                BODY_STYLE,
            ),

            Paragraph(
                "<b>Amount Due</b>",
                BODY_STYLE,
            ),

            Paragraph(
                "<b>Status</b>",
                BODY_STYLE,
            ),
        ]
    ]

    total_installments = 0

    for installment in installments:

        amount_due = (
            installment.get(
                "amount_due"
            )
            or 0
        )

        try:

            total_installments += float(
                amount_due
            )

        except (
            TypeError,
            ValueError,
        ):

            pass

        installment_status = clean_text(
            installment.get(
                "status"
            )
        )

        table_data.append(
            [
                Paragraph(
                    clean_text(
                        installment.get(
                            "installment_number"
                        )
                    ),
                    BODY_STYLE,
                ),

                Paragraph(
                    format_date(
                        installment.get(
                            "due_date"
                        )
                    ),
                    BODY_STYLE,
                ),

                Paragraph(
                    money(
                        amount_due
                    ),
                    BODY_STYLE,
                ),

                Paragraph(
                    (
                        f"<font color='"
                        f"{status_colour(installment_status).hexval()}"
                        f"'><b>"
                        f"{installment_status.upper()}"
                        f"</b></font>"
                    ),
                    BODY_STYLE,
                ),
            ]
        )

    if not installments:

        table_data.append(
            [
                "",
                Paragraph(
                    "No installments have been configured.",
                    BODY_STYLE,
                ),
                "",
                "",
            ]
        )

    table = Table(
        table_data,
        colWidths=[
            15 * mm,
            50 * mm,
            55 * mm,
            55 * mm,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        0,
                    ),
                    NAVY,
                ),

                (
                    "TEXTCOLOR",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        0,
                    ),
                    WHITE,
                ),

                (
                    "GRID",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    0.4,
                    MID_GREY,
                ),

                (
                    "VALIGN",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    "MIDDLE",
                ),

                (
                    "ALIGN",
                    (
                        0,
                        0,
                    ),
                    (
                        0,
                        -1,
                    ),
                    "CENTER",
                ),

                (
                    "ALIGN",
                    (
                        2,
                        1,
                    ),
                    (
                        2,
                        -1,
                    ),
                    "RIGHT",
                ),

                (
                    "LEFTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    2.5 * mm,
                ),

                (
                    "RIGHTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    2.5 * mm,
                ),

                (
                    "TOPPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    2.4 * mm,
                ),

                (
                    "BOTTOMPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    2.4 * mm,
                ),
            ]
        )
    )

    return (
        table,
        total_installments,
    )


# ============================================================
# SUMMARY
# ============================================================

def build_summary(
    data: dict,
    installment_total: float,
):

    plan_total = float(
        data.get(
            "total_plan_amount"
        )
        or 0
    )

    difference = (
        plan_total
        - installment_total
    )

    rows = [
        [
            Paragraph(
                "<b>Plan Amount</b>",
                BODY_STYLE,
            ),

            Paragraph(
                f"<b>{money(plan_total)}</b>",
                BODY_STYLE,
            ),
        ],

        [
            Paragraph(
                "<b>Total Scheduled Installments</b>",
                BODY_STYLE,
            ),

            Paragraph(
                f"<b>{money(installment_total)}</b>",
                BODY_STYLE,
            ),
        ],
    ]

    if abs(
        difference
    ) > 0.01:

        rows.append(
            [
                Paragraph(
                    "<b>Difference</b>",
                    BODY_STYLE,
                ),

                Paragraph(
                    f"<b>{money(difference)}</b>",
                    BODY_STYLE,
                ),
            ]
        )

    table = Table(
        rows,
        colWidths=[
            95 * mm,
            80 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    LIGHT_GREY,
                ),

                (
                    "GRID",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    0.4,
                    MID_GREY,
                ),

                (
                    "ALIGN",
                    (
                        1,
                        0,
                    ),
                    (
                        1,
                        -1,
                    ),
                    "RIGHT",
                ),

                (
                    "LEFTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    3 * mm,
                ),

                (
                    "RIGHTPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    3 * mm,
                ),

                (
                    "TOPPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    2.5 * mm,
                ),

                (
                    "BOTTOMPADDING",
                    (
                        0,
                        0,
                    ),
                    (
                        -1,
                        -1,
                    ),
                    2.5 * mm,
                ),
            ]
        )
    )

    return table


# ============================================================
# FOOTER
# ============================================================

def draw_footer(
    pdf_canvas,
    document,
):

    width, _ = A4

    pdf_canvas.saveState()

    pdf_canvas.setStrokeColor(
        GOLD
    )

    pdf_canvas.setLineWidth(
        1
    )

    pdf_canvas.line(
        16 * mm,
        13 * mm,
        width - 16 * mm,
        13 * mm,
    )

    pdf_canvas.setFillColor(
        NAVY
    )

    pdf_canvas.setFont(
        "Helvetica",
        6.5,
    )

    pdf_canvas.drawCentredString(
        width / 2,
        8 * mm,
        (
            f"{PHONE}   |   "
            f"{EMAIL}   |   "
            f"{WEBSITE}"
        ),
    )

    pdf_canvas.restoreState()


# ============================================================
# GENERATE PAYMENT PLAN PDF
# ============================================================

def generate_payment_plan_pdf(
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
        str(
            output_path
        ),
        pagesize=A4,
        leftMargin=17 * mm,
        rightMargin=17 * mm,
        topMargin=15 * mm,
        bottomMargin=20 * mm,
        title=(
            "Glen Moniques Payment Plan"
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
            6 * mm,
        )
    )

    story.append(
        Paragraph(
            "STUDENT PAYMENT PLAN",
            TITLE_STYLE,
        )
    )

    story.append(
        Paragraph(
            (
                "Official installment schedule for "
                "the registered student account."
            ),
            SUBTITLE_STYLE,
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
            "STUDENT INFORMATION",
            SECTION_STYLE,
        )
    )

    story.append(
        build_student_information(
            data
        )
    )

    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    story.append(
        Paragraph(
            "PAYMENT PLAN DETAILS",
            SECTION_STYLE,
        )
    )

    story.append(
        build_plan_information(
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
            "INSTALLMENT SCHEDULE",
            SECTION_STYLE,
        )
    )

    (
        installment_table,
        installment_total,
    ) = build_installment_table(
        data
    )

    story.append(
        installment_table
    )

    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    story.append(
        Paragraph(
            "PAYMENT PLAN SUMMARY",
            SECTION_STYLE,
        )
    )

    story.append(
        build_summary(
            data,
            installment_total,
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
            SECTION_STYLE,
        )
    )

    story.append(
        Paragraph(
            (
                "Installments should be paid on or before "
                "their respective due dates. Payments must "
                "be made using the correct student or invoice "
                "reference so that they can be allocated to "
                "the correct account."
            ),
            SMALL_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            2 * mm,
        )
    )

    story.append(
        Paragraph(
            (
                "This payment plan forms part of the student's "
                "financial account record. It does not itself "
                "serve as proof of payment. Official receipts "
                "are issued separately once qualifying payments "
                "have been recorded."
            ),
            SMALL_STYLE,
        )
    )

    document.build(
        story,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer,
    )

    return output_path