from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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

COMPANY_NAME = "GLEN MONIQUES (PTY) LTD"
COMPANY_REGISTRATION = "2020/089305/07"
COMPANY_EMAIL = "admin@glenmoniques.co.za"
COMPANY_PHONE = "015 880 2413"
COMPANY_WEBSITE = "www.glenmoniques.co.za"
COMPANY_TAGLINE = "Hi tirhela n'wina"


# ============================================================
# PATH HELPERS
# ============================================================

def get_completion_pdf_directory() -> Path:

    directory = (
        Path(__file__)
        .resolve()
        .parents[2]
        / "generated_pdfs"
        / "completion_documents"
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


def get_assets_directory() -> Path:

    return (
        Path(__file__)
        .resolve()
        .parents[2]
        / "assets"
    )


def find_glen_moniques_logo() -> Path | None:

    assets_directory = (
        get_assets_directory()
    )

    candidate_names = [
        "logo.png",
        "logo.jpg",
        "logo.jpeg",
        "glen_moniques_logo.png",
        "glen_moniques_logo.jpg",
        "glen_moniques_logo.jpeg",
        "glen-moniques-logo.png",
        "glen-moniques-logo.jpg",
        "glenmoniques_logo.png",
        "glenmoniques.png",
        "glen_moniques.png",
    ]

    for filename in candidate_names:

        path = (
            assets_directory
            / filename
        )

        if path.exists():

            return path

    for path in assets_directory.glob("*"):

        if (
            path.is_file()
            and path.suffix.lower()
            in {
                ".png",
                ".jpg",
                ".jpeg",
            }
            and "logo"
            in path.stem.lower()
        ):

            return path

    return None


def safe_filename_value(
    value: str,
) -> str:

    value = str(
        value or ""
    ).strip()

    allowed = []

    for character in value:

        if (
            character.isalnum()
            or character
            in (
                "-",
                "_",
            )
        ):

            allowed.append(
                character
            )

        else:

            allowed.append(
                "_"
            )

    return "".join(
        allowed
    )


# ============================================================
# STYLES
# ============================================================

def build_styles():

    styles = (
        getSampleStyleSheet()
    )

    return {
        "company": ParagraphStyle(
            "Company",
            parent=styles[
                "Normal"
            ],
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=colors.HexColor(
                "#172554"
            ),
            spaceAfter=3,
        ),

        "company_details": ParagraphStyle(
            "CompanyDetails",
            parent=styles[
                "Normal"
            ],
            alignment=TA_CENTER,
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor(
                "#475569"
            ),
            spaceAfter=2,
        ),

        "title": ParagraphStyle(
            "DocumentTitle",
            parent=styles[
                "Normal"
            ],
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor(
                "#172554"
            ),
            spaceBefore=10,
            spaceAfter=15,
        ),

        "body": ParagraphStyle(
            "Body",
            parent=styles[
                "Normal"
            ],
            alignment=TA_LEFT,
            fontName="Helvetica",
            fontSize=10.5,
            leading=16,
            textColor=colors.HexColor(
                "#1F2937"
            ),
            spaceAfter=11,
        ),

        "body_bold": ParagraphStyle(
            "BodyBold",
            parent=styles[
                "Normal"
            ],
            alignment=TA_LEFT,
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=16,
            textColor=colors.HexColor(
                "#1F2937"
            ),
            spaceAfter=11,
        ),

        "small": ParagraphStyle(
            "Small",
            parent=styles[
                "Normal"
            ],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor(
                "#64748B"
            ),
        ),
    }


# ============================================================
# HEADER
# ============================================================

def add_header(
    story: list,
    styles: dict,
    title: str,
):

    logo_path = (
        find_glen_moniques_logo()
    )

    if logo_path:

        logo = Image(
            str(
                logo_path
            )
        )

        max_width = 36 * mm
        max_height = 24 * mm

        width = float(
            logo.imageWidth
        )

        height = float(
            logo.imageHeight
        )

        scale = min(
            max_width / width,
            max_height / height,
        )

        logo.drawWidth = (
            width * scale
        )

        logo.drawHeight = (
            height * scale
        )

        logo.hAlign = "CENTER"

        story.append(
            logo
        )

        story.append(
            Spacer(
                1,
                3 * mm,
            )
        )

    story.append(
        Paragraph(
            COMPANY_NAME,
            styles[
                "company"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "Registration No: "
                f"{COMPANY_REGISTRATION}"
            ),
            styles[
                "company_details"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                f"{COMPANY_PHONE} | "
                f"{COMPANY_EMAIL} | "
                f"{COMPANY_WEBSITE}"
            ),
            styles[
                "company_details"
            ],
        )
    )

    story.append(
        Paragraph(
            COMPANY_TAGLINE,
            styles[
                "company_details"
            ],
        )
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    divider = Table(
        [
            [""]
        ],
        colWidths=[
            170 * mm
        ],
        rowHeights=[
            1.5 * mm
        ],
    )

    divider.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#D4A72C"
                    ),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0,
                    colors.white,
                ),
            ]
        )
    )

    story.append(
        divider
    )

    story.append(
        Paragraph(
            title,
            styles[
                "title"
            ],
        )
    )


# ============================================================
# STUDENT INFORMATION
# ============================================================

def add_student_information(
    story: list,
    styles: dict,
    data: dict,
):

    table_data = [
        [
            "Student Number",
            data.get(
                "student_number",
                "",
            ),
        ],
        [
            "Full Name",
            data.get(
                "full_name",
                "",
            ),
        ],
        [
            "Programme",
            data.get(
                "course_name",
                "",
            ),
        ],
        [
            "Programme Code",
            data.get(
                "course_code",
                "",
            ),
        ],
        [
            "NQF Level",
            str(
                data.get(
                    "nqf_level",
                    "",
                )
            ),
        ],
        [
            "Credits",
            str(
                data.get(
                    "credits",
                    "",
                )
            ),
        ],
    ]

    info_table = Table(
        table_data,
        colWidths=[
            45 * mm,
            120 * mm,
        ],
    )

    info_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor(
                        "#F1F5F9"
                    ),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (1, 0),
                    (1, -1),
                    "Helvetica",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#1F2937"
                    ),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#CBD5E1"
                    ),
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

    story.append(
        info_table
    )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )


def add_footer_note(
    story: list,
    styles: dict,
):

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    story.append(
        Paragraph(
            (
                "This document was generated by the "
                "Glen Moniques School Management System."
            ),
            styles[
                "small"
            ],
        )
    )


# ============================================================
# LETTER OF COMPLETION
# ============================================================

def generate_letter_of_completion_pdf(
    data: dict,
) -> str:

    output_directory = (
        get_completion_pdf_directory()
    )

    student_number = (
        safe_filename_value(
            data.get(
                "student_number",
                "student",
            )
        )
    )

    output_path = (
        output_directory
        / (
            "Letter_of_Completion_"
            f"{student_number}.pdf"
        )
    )

    document = SimpleDocTemplate(
        str(
            output_path
        ),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=18 * mm,
        title=(
            "Letter of Completion"
        ),
        author=COMPANY_NAME,
    )

    styles = (
        build_styles()
    )

    story = []

    add_header(
        story,
        styles,
        "LETTER OF COMPLETION",
    )

    story.append(
        Paragraph(
            (
                "Date: "
                f"{data.get('document_date', '')}"
            ),
            styles[
                "body"
            ],
        )
    )

    add_student_information(
        story,
        styles,
        data,
    )

    story.append(
        Paragraph(
            "To Whom It May Concern",
            styles[
                "body_bold"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "This letter serves to confirm that "
                f"<b>{data.get('full_name', '')}</b>, "
                "Student Number "
                f"<b>{data.get('student_number', '')}</b>, "
                "has completed the prescribed learning "
                "and assessment requirements for the "
                "programme "
                f"<b>{data.get('course_name', '')}</b>."
            ),
            styles[
                "body"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "The learner has successfully completed "
                "the required programme modules and the "
                "Final Integrated Supervised Assessment "
                "(FISA), as recorded by Glen Moniques."
            ),
            styles[
                "body"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "The learner's academic achievement is "
                "also reflected in the official Statement "
                "of Results available through the student "
                "portal."
            ),
            styles[
                "body"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "This Letter of Completion is issued as "
                "confirmation of programme completion. "
                "It is not an Occupational Certificate "
                "issued by the Quality Council for Trades "
                "and Occupations (QCTO)."
            ),
            styles[
                "body"
            ],
        )
    )

    story.append(
        Spacer(
            1,
            10 * mm,
        )
    )

    story.append(
        Paragraph(
            "Yours faithfully,",
            styles[
                "body"
            ],
        )
    )

    story.append(
        Paragraph(
            "<b>GLEN MONIQUES (PTY) LTD</b>",
            styles[
                "body"
            ],
        )
    )

    add_footer_note(
        story,
        styles,
    )

    document.build(
        story
    )

    return str(
        output_path
    )


# ============================================================
# GRADUATION LETTER
# ============================================================

def generate_graduation_letter_pdf(
    data: dict,
) -> str:

    output_directory = (
        get_completion_pdf_directory()
    )

    student_number = (
        safe_filename_value(
            data.get(
                "student_number",
                "student",
            )
        )
    )

    output_path = (
        output_directory
        / (
            "Graduation_Letter_"
            f"{student_number}.pdf"
        )
    )

    document = SimpleDocTemplate(
        str(
            output_path
        ),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=18 * mm,
        title=(
            "Graduation Letter"
        ),
        author=COMPANY_NAME,
    )

    styles = (
        build_styles()
    )

    story = []

    add_header(
        story,
        styles,
        "GRADUATION LETTER",
    )

    story.append(
        Paragraph(
            (
                "Date: "
                f"{data.get('document_date', '')}"
            ),
            styles[
                "body"
            ],
        )
    )

    add_student_information(
        story,
        styles,
        data,
    )

    story.append(
        Paragraph(
            (
                "Dear "
                f"{data.get('first_name', 'Student')},"
            ),
            styles[
                "body_bold"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "Congratulations on successfully completing "
                "the requirements of the programme "
                f"<b>{data.get('course_name', '')}</b>."
            ),
            styles[
                "body"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "Glen Moniques confirms that the required "
                "programme components have been completed "
                "and that the official External Integrated "
                "Summative Assessment (EISA) result received "
                "from the relevant external assessment "
                "process has been recorded as competent."
            ),
            styles[
                "body"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "You are therefore recognised by Glen "
                "Moniques as having successfully completed "
                "the programme requirements."
            ),
            styles[
                "body"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "Please note that this Graduation Letter "
                "is not the Occupational Certificate. "
                "Formal certification for the occupational "
                "qualification is issued by the Quality "
                "Council for Trades and Occupations (QCTO)."
            ),
            styles[
                "body"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "The official QCTO certificate will be "
                "handled separately once issued through the "
                "applicable certification process."
            ),
            styles[
                "body"
            ],
        )
    )

    story.append(
        Spacer(
            1,
            10 * mm,
        )
    )

    story.append(
        Paragraph(
            (
                "We congratulate you on this achievement "
                "and wish you success in your future "
                "endeavours."
            ),
            styles[
                "body"
            ],
        )
    )

    story.append(
        Paragraph(
            "Yours faithfully,",
            styles[
                "body"
            ],
        )
    )

    story.append(
        Paragraph(
            "<b>GLEN MONIQUES (PTY) LTD</b>",
            styles[
                "body"
            ],
        )
    )

    add_footer_note(
        story,
        styles,
    )

    document.build(
        story
    )

    return str(
        output_path
    )