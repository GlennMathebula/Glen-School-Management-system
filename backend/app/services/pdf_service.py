from datetime import datetime
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
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
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

ASSETS_DIR = BASE_DIR / "assets"
PDF_DIR = BASE_DIR / "generated_pdfs"

LOGO_PATH = ASSETS_DIR / "glen-moniques-logo.png"

PDF_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# SYSTEM SETTINGS
# ============================================================

SYSTEM_VERSION = "1.0.0"

NAVY = colors.HexColor("#0B1F4B")
ORANGE = colors.HexColor("#F5A623")
LIGHT_BLUE = colors.HexColor("#EEF5FC")
LIGHT_GREY = colors.HexColor("#F3F4F6")
TEXT_COLOUR = colors.HexColor("#24364B")


# ============================================================
# HELPERS
# ============================================================

def safe_value(value) -> str:
    if value is None:
        return "Not specified"

    value = str(value).strip()

    if not value:
        return "Not specified"

    return value


def get_current_time():
    return datetime.now(
        ZoneInfo("Africa/Johannesburg")
    )


def format_date(value) -> str:
    if not value:
        return "Not available"

    try:
        return value.strftime(
            "%d %B %Y"
        )
    except AttributeError:
        return str(value)[:10]


def get_qualification_display(
    application: dict,
) -> str:

    course_name = safe_value(
        application.get("course_name")
    )

    nqf_level = safe_value(
        application.get("nqf_level")
    )

    if course_name == "Not specified":
        return "Not specified"

    if nqf_level == "Not specified":
        return course_name

    return (
        f"{course_name} - "
        f"NQF Level {nqf_level}"
    )


def create_document_id(
    document_type: str,
    student_number: str,
) -> str:

    now = get_current_time()

    return (
        f"{document_type}-"
        f"{student_number}-"
        f"{now.strftime('%Y%m%d%H%M%S')}-"
        f"{uuid4().hex[:6].upper()}"
    )


# ============================================================
# STYLES
# ============================================================

def build_styles():
    styles = getSampleStyleSheet()

    return {
        "company": ParagraphStyle(
            "CompanyName",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=20,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),

        "slogan": ParagraphStyle(
            "Slogan",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=12,
            textColor=TEXT_COLOUR,
            alignment=TA_CENTER,
        ),

        "title": ParagraphStyle(
            "DocumentTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),

        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=TEXT_COLOUR,
            alignment=TA_CENTER,
        ),

        "heading": ParagraphStyle(
            "Heading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceBefore=6,
            spaceAfter=4,
        ),

        "normal": ParagraphStyle(
            "NormalGM",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=TEXT_COLOUR,
            alignment=TA_LEFT,
        ),

        "letter": ParagraphStyle(
            "LetterBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=15,
            textColor=TEXT_COLOUR,
            alignment=TA_LEFT,
            spaceAfter=7,
        ),

        "letter_date": ParagraphStyle(
            "LetterDate",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=TEXT_COLOUR,
            alignment=TA_RIGHT,
        ),

        "label": ParagraphStyle(
            "Label",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=13,
            textColor=NAVY,
        ),

        "small": ParagraphStyle(
            "Small",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=TEXT_COLOUR,
        ),

        "student_number": ParagraphStyle(
            "StudentNumber",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=21,
            leading=25,
            textColor=NAVY,
            alignment=TA_LEFT,
        ),

        "status": ParagraphStyle(
            "Status",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#B85C00"),
        ),

        "bullet": ParagraphStyle(
            "Bullet",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=15,
            leftIndent=12,
            firstLineIndent=-8,
            textColor=TEXT_COLOUR,
            spaceAfter=3,
        ),
    }


# ============================================================
# COMMON HEADER
# ============================================================

def add_header(
    story: list,
    styles: dict,
):

    if LOGO_PATH.exists():
        logo = Image(
            str(LOGO_PATH),
            width=30 * mm,
            height=30 * mm,
        )

        header_text = [
            Paragraph(
                "GLEN MONIQUES (PTY) LTD",
                styles["company"],
            ),
            Paragraph(
                "Hi tirhela n'wana",
                styles["slogan"],
            ),
            Spacer(1, 2),
            Paragraph(
                "TRAINING &nbsp;&nbsp; | &nbsp;&nbsp; "
                "SKILLS DEVELOPMENT &nbsp;&nbsp; | &nbsp;&nbsp; "
                "BUSINESS SOLUTIONS",
                ParagraphStyle(
                    "Services",
                    parent=styles["normal"],
                    alignment=TA_CENTER,
                    fontSize=8,
                    textColor=NAVY,
                ),
            ),
        ]

        header_table = Table(
            [[logo, header_text]],
            colWidths=[
                38 * mm,
                132 * mm,
            ],
        )

        header_table.setStyle(
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

        story.append(header_table)

    else:
        story.append(
            Paragraph(
                "GLEN MONIQUES (PTY) LTD",
                styles["company"],
            )
        )

    story.append(
        Spacer(
            1,
            5,
        )
    )

    orange_line = Table(
        [[""]],
        colWidths=[40 * mm],
        rowHeights=[1.4 * mm],
    )

    orange_line.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    ORANGE,
                ),
            ]
        )
    )

    story.append(
        orange_line
    )

    story.append(
        Spacer(
            1,
            8,
        )
    )


# ============================================================
# COMMON FOOTER
# ============================================================

def add_footer(
    story: list,
    styles: dict,
):

    story.append(
        Spacer(
            1,
            10,
        )
    )

    story.append(
        Paragraph(
            "Glen Moniques (Pty) Ltd"
            " &nbsp;&nbsp; | &nbsp;&nbsp; "
            "admin@glenmoniques.co.za"
            " &nbsp;&nbsp; | &nbsp;&nbsp; "
            "www.glenmoniques.co.za",
            ParagraphStyle(
                "Footer",
                parent=styles["small"],
                alignment=TA_CENTER,
                textColor=NAVY,
            ),
        )
    )


# ============================================================
# METADATA
# ============================================================

def create_metadata_table(
    document_id: str,
    styles: dict,
):

    generated_at = get_current_time().strftime(
        "%d %B %Y at %H:%M:%S"
    )

    table = Table(
        [
            [
                Paragraph(
                    "<b>Generated At</b>",
                    styles["small"],
                ),
                Paragraph(
                    generated_at,
                    styles["small"],
                ),
            ],
            [
                Paragraph(
                    "<b>Document ID</b>",
                    styles["small"],
                ),
                Paragraph(
                    document_id,
                    styles["small"],
                ),
            ],
            [
                Paragraph(
                    "<b>System Version</b>",
                    styles["small"],
                ),
                Paragraph(
                    SYSTEM_VERSION,
                    styles["small"],
                ),
            ],
        ],
        colWidths=[
            35 * mm,
            135 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#F8FAFC"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#D9E0E8"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.HexColor("#E5E7EB"),
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
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    return table


# ============================================================
# APPLICATION ACKNOWLEDGEMENT
# ============================================================

def generate_application_acknowledgement(
    application: dict,
) -> str:

    styles = build_styles()

    student_number = safe_value(
        application.get("student_number")
    )

    first_name = safe_value(
        application.get("first_name")
    )

    last_name = safe_value(
        application.get("last_name")
    )

    email = safe_value(
        application.get("email")
    )

    status = safe_value(
        application.get("app_status")
    )

    national_id = safe_value(
        application.get("national_id")
    )

    cell_number = safe_value(
        application.get("cell_number")
    )

    qualification_id = safe_value(
        application.get("qualification_id")
    )

    funding_type = safe_value(
        application.get("funding_type")
    )

    application_date = format_date(
        application.get("created_at")
    )

    qualification_display = (
        get_qualification_display(
            application
        )
    )

    document_id = create_document_id(
        "ACK",
        student_number,
    )

    pdf_path = (
        PDF_DIR
        / f"Application_Acknowledgement_{student_number}.pdf"
    )

    document = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )

    story = []

    add_header(
        story,
        styles,
    )

    story.append(
        Paragraph(
            "APPLICATION ACKNOWLEDGEMENT",
            styles["title"],
        )
    )

    story.append(
        Paragraph(
            "Your application has been successfully received "
            "and recorded in the Glen Moniques Student "
            "Management System.",
            styles["subtitle"],
        )
    )

    story.append(
        Spacer(
            1,
            9,
        )
    )

    summary_table = Table(
        [
            [
                [
                    Paragraph(
                        "STUDENT NUMBER",
                        styles["label"],
                    ),
                    Paragraph(
                        student_number,
                        styles["student_number"],
                    ),
                ],
                [
                    Paragraph(
                        "APPLICATION DATE",
                        styles["label"],
                    ),
                    Paragraph(
                        application_date,
                        styles["normal"],
                    ),
                ],
            ]
        ],
        colWidths=[
            105 * mm,
            65 * mm,
        ],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT_BLUE,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.HexColor("#D4E2F1"),
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
                    12,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    12,
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
                (
                    "LINEBEFORE",
                    (1, 0),
                    (1, 0),
                    0.6,
                    NAVY,
                ),
            ]
        )
    )

    story.append(
        summary_table
    )

    story.append(
        Spacer(
            1,
            8,
        )
    )

    application_data = [
        [
            Paragraph(
                "Full Name",
                styles["label"],
            ),
            Paragraph(
                f"{first_name} {last_name}",
                styles["normal"],
            ),
        ],
        [
            Paragraph(
                "ID Number",
                styles["label"],
            ),
            Paragraph(
                national_id,
                styles["normal"],
            ),
        ],
        [
            Paragraph(
                "Cellphone Number",
                styles["label"],
            ),
            Paragraph(
                cell_number,
                styles["normal"],
            ),
        ],
        [
            Paragraph(
                "Email Address",
                styles["label"],
            ),
            Paragraph(
                email,
                styles["normal"],
            ),
        ],
        [
            Paragraph(
                "SP / SAQA ID",
                styles["label"],
            ),
            Paragraph(
                qualification_id,
                styles["normal"],
            ),
        ],
        [
            Paragraph(
                "SP / Qualification Name and NQF Level",
                styles["label"],
            ),
            Paragraph(
                qualification_display,
                styles["normal"],
            ),
        ],
        [
            Paragraph(
                "Funding Type",
                styles["label"],
            ),
            Paragraph(
                funding_type,
                styles["normal"],
            ),
        ],
        [
            Paragraph(
                "Application Status",
                styles["label"],
            ),
            Paragraph(
                status,
                styles["status"],
            ),
        ],
    ]

    application_table = Table(
        application_data,
        colWidths=[
            60 * mm,
            110 * mm,
        ],
    )

    application_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#D9E0E8"),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    LIGHT_GREY,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
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

    story.append(
        application_table
    )

    story.append(
        Spacer(
            1,
            8,
        )
    )

    story.append(
        Paragraph(
            "WHAT HAPPENS NEXT?",
            styles["heading"],
        )
    )

    story.append(
        Paragraph(
            "Your application is currently pending review. "
            "Our admissions team will assess your application "
            "and may contact you if additional information or "
            "supporting documentation is required.",
            styles["normal"],
        )
    )

    story.append(
        Spacer(
            1,
            8,
        )
    )

    story.append(
        create_metadata_table(
            document_id,
            styles,
        )
    )

    add_footer(
        story,
        styles,
    )

    document.build(
        story
    )

    return str(
        pdf_path
    )


# ============================================================
# ACCEPTANCE LETTER
# ============================================================

def generate_acceptance_letter(
    application: dict,
) -> str:

    styles = build_styles()

    student_number = safe_value(
        application.get("student_number")
    )

    first_name = safe_value(
        application.get("first_name")
    )

    last_name = safe_value(
        application.get("last_name")
    )

    qualification_id = safe_value(
        application.get("qualification_id")
    )

    qualification_display = (
        get_qualification_display(
            application
        )
    )

    funding_type = safe_value(
        application.get("funding_type")
    )

    document_date = get_current_time().strftime(
        "%d %B %Y"
    )

    document_id = create_document_id(
        "ACC",
        student_number,
    )

    pdf_path = (
        PDF_DIR
        / f"Acceptance_Letter_{student_number}.pdf"
    )

    document = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=14 * mm,
        bottomMargin=15 * mm,
    )

    story = []

    add_header(
        story,
        styles,
    )

    story.append(
        Paragraph(
            document_date,
            styles["letter_date"],
        )
    )

    story.append(
        Spacer(
            1,
            12,
        )
    )

    story.append(
        Paragraph(
            f"<b>{first_name} {last_name}</b>",
            styles["letter"],
        )
    )

    story.append(
        Paragraph(
            f"Student Number: {student_number}",
            styles["letter"],
        )
    )

    story.append(
        Spacer(
            1,
            8,
        )
    )

    story.append(
        Paragraph(
            "<b>LETTER OF ACCEPTANCE</b>",
            styles["heading"],
        )
    )

    story.append(
        Spacer(
            1,
            4,
        )
    )

    story.append(
        Paragraph(
            f"Dear {first_name} {last_name},",
            styles["letter"],
        )
    )

    story.append(
        Paragraph(
            "We are pleased to inform you that your application "
            "to Glen Moniques (Pty) Ltd has been successfully "
            "reviewed and accepted.",
            styles["letter"],
        )
    )

    story.append(
        Paragraph(
            f"You have been accepted for "
            f"<b>{qualification_display}</b>.",
            styles["letter"],
        )
    )

    if qualification_id != "Not specified":
        story.append(
            Paragraph(
                f"SP / SAQA ID: <b>{qualification_id}</b>",
                styles["letter"],
            )
        )

    if funding_type != "Not specified":
        story.append(
            Paragraph(
                f"Funding Type: <b>{funding_type}</b>",
                styles["letter"],
            )
        )

    story.append(
        Paragraph(
            "Please note that this acceptance confirms the outcome "
            "of your application. It does not, on its own, constitute "
            "final registration. Registration will be confirmed once "
            "all required registration processes and documentation "
            "have been completed.",
            styles["letter"],
        )
    )

    story.append(
        Paragraph(
            "Our admissions team will communicate with you regarding "
            "registration, programme commencement, orientation and "
            "any further administrative requirements.",
            styles["letter"],
        )
    )

    story.append(
        Paragraph(
            "Congratulations on your successful application. "
            "We look forward to supporting you throughout your "
            "learning journey with Glen Moniques.",
            styles["letter"],
        )
    )

    story.append(
        Spacer(
            1,
            10,
        )
    )

    story.append(
        Paragraph(
            "Yours faithfully,",
            styles["letter"],
        )
    )

    story.append(
        Spacer(
            1,
            14,
        )
    )

    story.append(
        Paragraph(
            "<b>Admissions Office</b>",
            styles["letter"],
        )
    )

    story.append(
        Paragraph(
            "Glen Moniques (Pty) Ltd",
            styles["letter"],
        )
    )

    story.append(
        Spacer(
            1,
            10,
        )
    )

    story.append(
        create_metadata_table(
            document_id,
            styles,
        )
    )

    add_footer(
        story,
        styles,
    )

    document.build(
        story
    )

    return str(
        pdf_path
    )


# ============================================================
# REJECTION LETTER
# ============================================================

def generate_rejection_letter(
    application: dict,
) -> str:

    styles = build_styles()

    student_number = safe_value(
        application.get("student_number")
    )

    first_name = safe_value(
        application.get("first_name")
    )

    last_name = safe_value(
        application.get("last_name")
    )

    qualification_id = safe_value(
        application.get("qualification_id")
    )

    qualification_display = (
        get_qualification_display(
            application
        )
    )

    document_date = get_current_time().strftime(
        "%d %B %Y"
    )

    document_id = create_document_id(
        "REJ",
        student_number,
    )

    pdf_path = (
        PDF_DIR
        / f"Rejection_Letter_{student_number}.pdf"
    )

    document = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=14 * mm,
        bottomMargin=15 * mm,
    )

    story = []

    add_header(
        story,
        styles,
    )

    story.append(
        Paragraph(
            document_date,
            styles["letter_date"],
        )
    )

    story.append(
        Spacer(
            1,
            12,
        )
    )

    story.append(
        Paragraph(
            f"<b>{first_name} {last_name}</b>",
            styles["letter"],
        )
    )

    story.append(
        Paragraph(
            f"Student Number: {student_number}",
            styles["letter"],
        )
    )

    story.append(
        Spacer(
            1,
            8,
        )
    )

    story.append(
        Paragraph(
            "<b>APPLICATION OUTCOME</b>",
            styles["heading"],
        )
    )

    story.append(
        Spacer(
            1,
            4,
        )
    )

    story.append(
        Paragraph(
            f"Dear {first_name} {last_name},",
            styles["letter"],
        )
    )

    story.append(
        Paragraph(
            "Thank you for your interest in studying with "
            "Glen Moniques (Pty) Ltd and for taking the time "
            "to submit your application.",
            styles["letter"],
        )
    )

    story.append(
        Paragraph(
            "After reviewing your application, we regret to inform "
            "you that your application has not been successful "
            "at this time.",
            styles["letter"],
        )
    )

    if qualification_display != "Not specified":
        story.append(
            Paragraph(
                f"Programme applied for: "
                f"<b>{qualification_display}</b>",
                styles["letter"],
            )
        )

    if qualification_id != "Not specified":
        story.append(
            Paragraph(
                f"SP / SAQA ID: "
                f"<b>{qualification_id}</b>",
                styles["letter"],
            )
        )

    story.append(
        Paragraph(
            "This outcome relates to the current application and "
            "does not prevent you from applying again for a future "
            "intake or another programme for which you meet the "
            "applicable admission requirements.",
            styles["letter"],
        )
    )

    story.append(
        Paragraph(
            "We appreciate your interest in Glen Moniques and wish "
            "you well with your future learning and career plans.",
            styles["letter"],
        )
    )

    story.append(
        Spacer(
            1,
            10,
        )
    )

    story.append(
        Paragraph(
            "Yours faithfully,",
            styles["letter"],
        )
    )

    story.append(
        Spacer(
            1,
            14,
        )
    )

    story.append(
        Paragraph(
            "<b>Admissions Office</b>",
            styles["letter"],
        )
    )

    story.append(
        Paragraph(
            "Glen Moniques (Pty) Ltd",
            styles["letter"],
        )
    )

    story.append(
        Spacer(
            1,
            10,
        )
    )

    story.append(
        create_metadata_table(
            document_id,
            styles,
        )
    )

    add_footer(
        story,
        styles,
    )

    document.build(
        story
    )

    return str(
        pdf_path
    )


# ============================================================
# OUTSTANDING DOCUMENTS LETTER
# ============================================================

def generate_outstanding_documents_letter(
    application: dict,
    outstanding_documents: list[str],
) -> str:

    if not outstanding_documents:
        raise ValueError(
            "At least one outstanding document is required."
        )

    styles = build_styles()

    student_number = safe_value(
        application.get("student_number")
    )

    first_name = safe_value(
        application.get("first_name")
    )

    last_name = safe_value(
        application.get("last_name")
    )

    qualification_display = (
        get_qualification_display(
            application
        )
    )

    document_date = get_current_time().strftime(
        "%d %B %Y"
    )

    document_id = create_document_id(
        "OUT",
        student_number,
    )

    pdf_path = (
        PDF_DIR
        / f"Outstanding_Documents_{student_number}.pdf"
    )

    document = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=14 * mm,
        bottomMargin=15 * mm,
    )

    story = []

    add_header(
        story,
        styles,
    )

    story.append(
        Paragraph(
            document_date,
            styles["letter_date"],
        )
    )

    story.append(
        Spacer(
            1,
            12,
        )
    )

    story.append(
        Paragraph(
            f"<b>{first_name} {last_name}</b>",
            styles["letter"],
        )
    )

    story.append(
        Paragraph(
            f"Student Number: {student_number}",
            styles["letter"],
        )
    )

    story.append(
        Spacer(
            1,
            8,
        )
    )

    story.append(
        Paragraph(
            "<b>OUTSTANDING APPLICATION DOCUMENTS</b>",
            styles["heading"],
        )
    )

    story.append(
        Spacer(
            1,
            4,
        )
    )

    story.append(
        Paragraph(
            f"Dear {first_name} {last_name},",
            styles["letter"],
        )
    )

    story.append(
        Paragraph(
            "Thank you for your application to "
            "Glen Moniques (Pty) Ltd.",
            styles["letter"],
        )
    )

    if qualification_display != "Not specified":
        story.append(
            Paragraph(
                f"Your application for "
                f"<b>{qualification_display}</b> "
                "is currently being assessed.",
                styles["letter"],
            )
        )

    story.append(
        Paragraph(
            "We are unable to complete the assessment of your "
            "application because the following documentation "
            "is still outstanding:",
            styles["letter"],
        )
    )

    story.append(
        Spacer(
            1,
            3,
        )
    )

    for item in outstanding_documents:
        story.append(
            Paragraph(
                f"• {item}",
                styles["bullet"],
            )
        )

    story.append(
        Spacer(
            1,
            7,
        )
    )

    story.append(
        Paragraph(
            "Please submit the outstanding documents as soon as "
            "possible so that your application can proceed to the "
            "next stage of the admissions process.",
            styles["letter"],
        )
    )

    story.append(
        Paragraph(
            "Your application will remain under "
            "<b>Outstanding Documents</b> status until the required "
            "documents have been received and verified.",
            styles["letter"],
        )
    )

    story.append(
        Paragraph(
            "When submitting documents, please quote your student "
            f"number <b>{student_number}</b> to ensure that they "
            "are linked to the correct application.",
            styles["letter"],
        )
    )

    story.append(
        Spacer(
            1,
            10,
        )
    )

    story.append(
        Paragraph(
            "Yours faithfully,",
            styles["letter"],
        )
    )

    story.append(
        Spacer(
            1,
            14,
        )
    )

    story.append(
        Paragraph(
            "<b>Admissions Office</b>",
            styles["letter"],
        )
    )

    story.append(
        Paragraph(
            "Glen Moniques (Pty) Ltd",
            styles["letter"],
        )
    )

    story.append(
        Spacer(
            1,
            10,
        )
    )

    story.append(
        create_metadata_table(
            document_id,
            styles,
        )
    )

    add_footer(
        story,
        styles,
    )

    document.build(
        story
    )

    return str(
        pdf_path
    )