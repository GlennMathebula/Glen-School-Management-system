from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
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

APP_DIR = Path(__file__).resolve().parents[1]

ASSETS_DIR = APP_DIR / "assets"

OUTPUT_DIR = (
    APP_DIR
    / "generated_pdfs"
    / "proof_of_registration"
)

LOGO_PATH = (
    ASSETS_DIR
    / "glen-moniques-logo.png"
)

REGISTRAR_SIGNATURE_PATH = (
    ASSETS_DIR
    / "registrar_signature.png"
)


# ============================================================
# INSTITUTION DETAILS
# ============================================================

COMPANY_NAME = "GLEN MONIQUES (PTY) LTD"

SLOGAN = "Hi tirhela n'wina"

REG_NUMBER = "2020/089305/07"

SYSTEM_VERSION = "1.0.0"

OFFICIAL_ADDRESS = (
    "Malamulele, Limpopo, South Africa"
)

OFFICIAL_EMAIL = (
    "admin@glenmoniques.co.za"
)

OFFICIAL_PHONE = (
    "015 880 2413"
)

OFFICIAL_WEBSITE = (
    "www.glenmoniques.co.za"
)


# ============================================================
# DATE / TIME HELPERS
# ============================================================

def get_current_sast() -> datetime:
    return datetime.now(
        ZoneInfo("Africa/Johannesburg")
    )


def format_date(
    value,
) -> str:

    if not value:
        return "N/A"

    if isinstance(
        value,
        datetime,
    ):
        return value.strftime(
            "%d %B %Y"
        )

    if isinstance(
        value,
        date,
    ):
        return value.strftime(
            "%d %B %Y"
        )

    if isinstance(
        value,
        str,
    ):

        value = value.strip()

        if not value:
            return "N/A"

        try:

            if "T" in value:

                clean_value = value.replace(
                    "Z",
                    "+00:00",
                )

                parsed = (
                    datetime.fromisoformat(
                        clean_value
                    )
                )

                return parsed.strftime(
                    "%d %B %Y"
                )

            parsed = date.fromisoformat(
                value
            )

            return parsed.strftime(
                "%d %B %Y"
            )

        except Exception:
            return value

    return str(value)


def format_timestamp(
    value: datetime | None = None,
) -> str:

    if value is None:
        value = get_current_sast()

    return value.strftime(
        "%Y-%m-%d %H:%M:%S SAST"
    )


# ============================================================
# GENERAL HELPERS
# ============================================================

def safe_value(
    value,
    default: str = "N/A",
) -> str:

    if value is None:
        return default

    if isinstance(
        value,
        str,
    ):

        cleaned = value.strip()

        if not cleaned:
            return default

        return cleaned

    return str(value)


def create_por_document_id(
    student_number: str,
) -> str:

    now = get_current_sast()

    timestamp = now.strftime(
        "%Y%m%d-%H%M%S"
    )

    return (
        f"POR-"
        f"{student_number}-"
        f"{timestamp}"
    )


# ============================================================
# STYLES
# ============================================================

def get_styles():

    base = getSampleStyleSheet()

    styles = {}

    styles["title"] = ParagraphStyle(
        "PORTitle",
        parent=base["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor(
            "#0B1F52"
        ),
        spaceAfter=6,
    )

    styles["subtitle"] = ParagraphStyle(
        "PORSubtitle",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor(
            "#F39C12"
        ),
    )

    styles["normal"] = ParagraphStyle(
        "PORNormal",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=TA_LEFT,
        textColor=colors.black,
    )

    styles["small"] = ParagraphStyle(
        "PORSmall",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=TA_LEFT,
        textColor=colors.black,
    )

    styles["small_center"] = ParagraphStyle(
        "PORSmallCenter",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.black,
    )

    styles["section_heading"] = (
        ParagraphStyle(
            "PORSectionHeading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            alignment=TA_LEFT,
            textColor=colors.white,
            backColor=colors.HexColor(
                "#0B1F52"
            ),
            borderPadding=5,
            spaceBefore=4,
            spaceAfter=5,
        )
    )

    styles["table_header"] = (
        ParagraphStyle(
            "PORTableHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.white,
        )
    )

    styles["stamp_title"] = (
        ParagraphStyle(
            "PORStampTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor(
                "#0B1F52"
            ),
        )
    )

    styles["stamp_text"] = (
        ParagraphStyle(
            "PORStampText",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            alignment=TA_CENTER,
            textColor=colors.black,
        )
    )

    return styles


# ============================================================
# DATA NORMALISATION
# ============================================================

def normalize_registration_data(
    registration_data: dict,
    modules: list[dict] | None = None,
) -> tuple[dict, list[dict]]:

    if (
        isinstance(
            registration_data,
            dict,
        )
        and "registration"
        in registration_data
        and isinstance(
            registration_data[
                "registration"
            ],
            dict,
        )
    ):

        registration = dict(
            registration_data[
                "registration"
            ]
        )

    else:

        registration = dict(
            registration_data
        )

    if modules is None:

        modules = (
            registration_data.get(
                "modules",
                [],
            )
        )

    return (
        registration,
        modules or [],
    )


# ============================================================
# ASSET LOADERS
# ============================================================

def get_logo():

    styles = get_styles()

    if LOGO_PATH.exists():

        image = Image(
            str(LOGO_PATH)
        )

        image.drawHeight = (
            24 * mm
        )

        image.drawWidth = (
            24 * mm
        )

        return image

    return Paragraph(
        "",
        styles["normal"],
    )


def get_registrar_signature():

    styles = get_styles()

    if (
        REGISTRAR_SIGNATURE_PATH.exists()
    ):

        image = Image(
            str(
                REGISTRAR_SIGNATURE_PATH
            )
        )

        image.drawHeight = (
            18 * mm
        )

        image.drawWidth = (
            45 * mm
        )

        return image

    return Paragraph(
        "<i>Signature not uploaded</i>",
        styles["small_center"],
    )


# ============================================================
# HEADER
# ============================================================

def build_header(
    styles,
):

    logo = get_logo()

    organisation_block = Table(
        [
            [
                Paragraph(
                    COMPANY_NAME,
                    ParagraphStyle(
                        "HeaderCompanyName",
                        parent=(
                            styles["normal"]
                        ),
                        fontName=(
                            "Helvetica-Bold"
                        ),
                        fontSize=13,
                        leading=16,
                        alignment=TA_CENTER,
                        textColor=(
                            colors.HexColor(
                                "#0B1F52"
                            )
                        ),
                    ),
                )
            ],
            [
                Paragraph(
                    SLOGAN,
                    styles["subtitle"],
                )
            ],
            [
                Paragraph(
                    (
                        f"{OFFICIAL_ADDRESS}"
                        "<br/>"
                        f"Tel: "
                        f"{OFFICIAL_PHONE}"
                        " | "
                        f"Email: "
                        f"{OFFICIAL_EMAIL}"
                        "<br/>"
                        f"Website: "
                        f"{OFFICIAL_WEBSITE}"
                    ),
                    styles[
                        "small_center"
                    ],
                )
            ],
        ],
        colWidths=[
            135 * mm
        ],
    )

    organisation_block.setStyle(
        TableStyle(
            [
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )

    header = Table(
        [
            [
                logo,
                organisation_block,
            ]
        ],
        colWidths=[
            30 * mm,
            145 * mm,
        ],
    )

    header.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.HexColor(
                        "#0B1F52"
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
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    return header


# ============================================================
# GENERATED SCHOOL STAMP
# ============================================================

def build_institution_stamp(
    styles,
    sdp_code: str,
    issue_date: str,
):

    rows = [
        [
            Paragraph(
                (
                    "OFFICIAL "
                    "INSTITUTIONAL STAMP"
                ),
                styles[
                    "stamp_title"
                ],
            )
        ],
        [
            Paragraph(
                (
                    f"<b>"
                    f"{COMPANY_NAME}"
                    f"</b>"
                ),
                styles[
                    "stamp_text"
                ],
            )
        ],
        [
            Paragraph(
                SLOGAN,
                styles[
                    "stamp_text"
                ],
            )
        ],
        [
            Paragraph(
                (
                    "Registration No: "
                    f"{REG_NUMBER}"
                ),
                styles[
                    "stamp_text"
                ],
            )
        ],
        [
            Paragraph(
                (
                    "Accreditation / "
                    "SDP Code: "
                    f"{safe_value(sdp_code)}"
                ),
                styles[
                    "stamp_text"
                ],
            )
        ],
        [
            Paragraph(
                OFFICIAL_ADDRESS,
                styles[
                    "stamp_text"
                ],
            )
        ],
        [
            Paragraph(
                (
                    "Date: "
                    f"{issue_date}"
                ),
                styles[
                    "stamp_text"
                ],
            )
        ],
    ]

    stamp = Table(
        rows,
        colWidths=[
            72 * mm
        ],
    )

    stamp.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    1.2,
                    colors.HexColor(
                        "#0B1F52"
                    ),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.lightgrey,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#EEF3FF"
                    ),
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
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
                    3,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
            ]
        )
    )

    stamp.hAlign = "RIGHT"

    return stamp


# ============================================================
# INFORMATION TABLE
# ============================================================

def build_info_table(
    styles,
    title: str,
    rows: list[
        tuple[
            str,
            str,
        ]
    ],
):

    title_paragraph = Paragraph(
        title,
        styles[
            "section_heading"
        ],
    )

    data = []

    for label, value in rows:

        data.append(
            [
                Paragraph(
                    (
                        f"<b>"
                        f"{label}"
                        f"</b>"
                    ),
                    styles["normal"],
                ),
                Paragraph(
                    safe_value(value),
                    styles["normal"],
                ),
            ]
        )

    table = Table(
        data,
        colWidths=[
            50 * mm,
            125 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    colors.HexColor(
                        "#0B1F52"
                    ),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.lightgrey,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor(
                        "#F7F9FC"
                    ),
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

    return [
        title_paragraph,
        table,
    ]


# ============================================================
# MODULE GROUPING
# ============================================================

def group_modules(
    modules: list[dict],
) -> dict[
    str,
    list[dict],
]:

    grouped = {
        "KM": [],
        "PM": [],
        "WM": [],
    }

    for module in modules:

        module_type = safe_value(
            module.get(
                "module_type"
            ),
            default="",
        ).upper()

        if module_type in grouped:

            grouped[
                module_type
            ].append(
                module
            )

    return grouped


# ============================================================
# MODULE SECTION
# ============================================================

def build_module_section(
    styles,
    title: str,
    modules: list[dict],
):

    if not modules:
        return []

    story = [
        Paragraph(
            title,
            styles[
                "section_heading"
            ],
        )
    ]

    data = [
        [
            Paragraph(
                "Module Code",
                styles[
                    "table_header"
                ],
            ),
            Paragraph(
                "Module Name",
                styles[
                    "table_header"
                ],
            ),
            Paragraph(
                "Level",
                styles[
                    "table_header"
                ],
            ),
            Paragraph(
                "Credits",
                styles[
                    "table_header"
                ],
            ),
        ]
    ]

    section_credits = 0

    for module in modules:

        credits = (
            module.get(
                "credits"
            )
            or 0
        )

        section_credits += credits

        data.append(
            [
                Paragraph(
                    safe_value(
                        module.get(
                            "module_code"
                        )
                    ),
                    styles[
                        "small"
                    ],
                ),
                Paragraph(
                    safe_value(
                        module.get(
                            "module_name"
                        )
                    ),
                    styles[
                        "small"
                    ],
                ),
                Paragraph(
                    safe_value(
                        module.get(
                            "nqf_level"
                        )
                    ),
                    styles[
                        "small_center"
                    ],
                ),
                Paragraph(
                    safe_value(
                        credits
                    ),
                    styles[
                        "small_center"
                    ],
                ),
            ]
        )

    data.append(
        [
            "",
            Paragraph(
                "<b>"
                "Section Credits"
                "</b>",
                styles[
                    "small"
                ],
            ),
            "",
            Paragraph(
                (
                    f"<b>"
                    f"{section_credits}"
                    f"</b>"
                ),
                styles[
                    "small_center"
                ],
            ),
        ]
    )

    table = Table(
        data,
        colWidths=[
            35 * mm,
            102 * mm,
            18 * mm,
            20 * mm,
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
                    colors.HexColor(
                        "#0B1F52"
                    ),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    colors.HexColor(
                        "#0B1F52"
                    ),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.lightgrey,
                ),
                (
                    "BACKGROUND",
                    (0, -1),
                    (-1, -1),
                    colors.HexColor(
                        "#F7F9FC"
                    ),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "ALIGN",
                    (2, 1),
                    (3, -1),
                    "CENTER",
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

    story.append(
        table
    )

    return story


# ============================================================
# REGISTRAR APPROVAL
# ============================================================

def build_registrar_section(
    styles,
    generated_at: str,
    issue_date: str,
    document_id: str,
):

    signature = (
        get_registrar_signature()
    )

    signature_block = Table(
        [
            [
                signature
            ],
            [
                Paragraph(
                    (
                        "________________"
                        "_______________"
                    ),
                    styles[
                        "small_center"
                    ],
                )
            ],
            [
                Paragraph(
                    "<b>Registrar</b>",
                    styles[
                        "small_center"
                    ],
                )
            ],
        ],
        colWidths=[
            70 * mm
        ],
    )

    signature_block.setStyle(
        TableStyle(
            [
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )

    document_details = Table(
        [
            [
                Paragraph(
                    (
                        "<b>"
                        "Date Issued:"
                        "</b> "
                        f"{issue_date}"
                    ),
                    styles["small"],
                )
            ],
            [
                Paragraph(
                    (
                        "<b>"
                        "Generated At:"
                        "</b> "
                        f"{generated_at}"
                    ),
                    styles["small"],
                )
            ],
            [
                Paragraph(
                    (
                        "<b>"
                        "Document ID:"
                        "</b> "
                        f"{document_id}"
                    ),
                    styles["small"],
                )
            ],
            [
                Paragraph(
                    (
                        "<b>"
                        "System Version:"
                        "</b> "
                        f"{SYSTEM_VERSION}"
                    ),
                    styles["small"],
                )
            ],
        ],
        colWidths=[
            95 * mm
        ],
    )

    document_details.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    colors.HexColor(
                        "#0B1F52"
                    ),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.lightgrey,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#F7F9FC"
                    ),
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

    section = Table(
        [
            [
                signature_block,
                document_details,
            ]
        ],
        colWidths=[
            75 * mm,
            100 * mm,
        ],
    )

    section.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
            ]
        )
    )

    return section


# ============================================================
# MAIN PDF GENERATOR
# ============================================================

def generate_proof_of_registration(
    registration_data: dict,
    modules: list[dict] | None = None,
) -> str:

    styles = get_styles()

    registration, modules = (
        normalize_registration_data(
            registration_data,
            modules,
        )
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # STUDENT
    # --------------------------------------------------------

    student_number = safe_value(
        registration.get(
            "student_number"
        ),
        default="UNKNOWN",
    )

    first_name = safe_value(
        registration.get(
            "first_name"
        ),
        default="",
    )

    middle_name = safe_value(
        registration.get(
            "middle_name"
        ),
        default="",
    )

    last_name = safe_value(
        registration.get(
            "last_name"
        ),
        default="",
    )

    full_name = " ".join(
        value
        for value in [
            first_name,
            middle_name,
            last_name,
        ]
        if value
    )

    if not full_name:
        full_name = "N/A"

    national_id = safe_value(
        registration.get(
            "national_id"
        )
    )

    if national_id == "N/A":

        national_id = safe_value(
            registration.get(
                "alternate_id"
            )
        )

    email = safe_value(
        registration.get(
            "email"
        )
    )

    cell_number = safe_value(
        registration.get(
            "cell_number"
        )
    )

    # --------------------------------------------------------
    # QUALIFICATION
    # --------------------------------------------------------

    course_code = safe_value(
        registration.get(
            "course_code"
        )
    )

    course_name = safe_value(
        registration.get(
            "course_name"
        )
    )

    nqf_level = safe_value(
        registration.get(
            "nqf_level"
        )
    )

    qualification_credits = (
        safe_value(
            registration.get(
                "credits"
            )
        )
    )

    assessment_type = safe_value(
        registration.get(
            "assessment_type"
        )
    )

    sdp_code = safe_value(
        registration.get(
            "sdp_code"
        )
    )

    # --------------------------------------------------------
    # REGISTRATION
    # --------------------------------------------------------

    registration_status = (
        safe_value(
            registration.get(
                "registration_status"
            )
        )
    )

    funding_type = safe_value(
        registration.get(
            "funding_type"
        )
    )

    cycle = safe_value(
        registration.get(
            "cycle"
        )
    )

    registration_date = (
        format_date(
            registration.get(
                "registration_date"
            )
        )
    )

    expected_completion_date = (
        format_date(
            registration.get(
                "expected_completion_date"
            )
        )
    )

    # --------------------------------------------------------
    # GENERATED DETAILS
    # --------------------------------------------------------

    issue_now = (
        get_current_sast()
    )

    issue_date = (
        format_date(
            issue_now
        )
    )

    generated_at = (
        format_timestamp(
            issue_now
        )
    )

    document_id = (
        create_por_document_id(
            student_number
        )
    )

    filename = (
        "proof_of_registration_"
        f"{student_number}_"
        f"{issue_now.strftime('%Y%m%d_%H%M%S')}"
        ".pdf"
    )

    file_path = (
        OUTPUT_DIR
        / filename
    )

    # --------------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------------

    document = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=(
            "Proof of Registration"
        ),
        author=COMPANY_NAME,
    )

    story = []

    # ========================================================
    # HEADER
    # ========================================================

    story.append(
        build_header(
            styles
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        Paragraph(
            "PROOF OF REGISTRATION",
            styles["title"],
        )
    )

    story.append(
        Paragraph(
            (
                "This document confirms that "
                "the learner named below is "
                "officially registered with "
                "Glen Moniques."
            ),
            styles[
                "small_center"
            ],
        )
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    # ========================================================
    # STAMP
    # ========================================================

    story.append(
        build_institution_stamp(
            styles=styles,
            sdp_code=sdp_code,
            issue_date=issue_date,
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    # ========================================================
    # LEARNER INFORMATION
    # ========================================================

    learner_rows = [
        (
            "Student Number",
            student_number,
        ),
        (
            "Full Name",
            full_name,
        ),
        (
            "ID / Passport Number",
            national_id,
        ),
        (
            "Email Address",
            email,
        ),
        (
            "Cell Number",
            cell_number,
        ),
    ]

    for item in build_info_table(
        styles,
        "Learner Information",
        learner_rows,
    ):
        story.append(
            item
        )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    # ========================================================
    # REGISTRATION DETAILS
    # ========================================================

    registration_rows = [
        (
            "Registration Date",
            registration_date,
        ),
        (
            "Academic Cycle",
            cycle,
        ),
        (
            "Funding Type",
            funding_type,
        ),
        (
            "Registration Status",
            registration_status,
        ),
        (
            "Expected Completion Date",
            expected_completion_date,
        ),
    ]

    for item in build_info_table(
        styles,
        "Registration Details",
        registration_rows,
    ):
        story.append(
            item
        )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    # ========================================================
    # QUALIFICATION DETAILS
    # ========================================================

    qualification_rows = [
        (
            "Qualification Code",
            course_code,
        ),
        (
            "Qualification Name",
            course_name,
        ),
        (
            "NQF Level",
            nqf_level,
        ),
        (
            "Qualification Credits",
            qualification_credits,
        ),
        (
            "Assessment Type",
            assessment_type,
        ),
        (
            "SDP Code",
            sdp_code,
        ),
    ]

    for item in build_info_table(
        styles,
        "Qualification Details",
        qualification_rows,
    ):
        story.append(
            item
        )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    # ========================================================
    # MODULE GROUPS
    # ========================================================

    grouped = group_modules(
        modules
    )

    knowledge_modules = (
        grouped["KM"]
    )

    practical_modules = (
        grouped["PM"]
    )

    workplace_modules = (
        grouped["WM"]
    )

    # --------------------------------------------------------
    # KNOWLEDGE
    # --------------------------------------------------------

    for item in build_module_section(
        styles,
        "Knowledge Modules",
        knowledge_modules,
    ):
        story.append(
            item
        )

    if knowledge_modules:

        story.append(
            Spacer(
                1,
                4 * mm,
            )
        )

    # --------------------------------------------------------
    # PRACTICAL
    # --------------------------------------------------------

    for item in build_module_section(
        styles,
        "Practical Modules",
        practical_modules,
    ):
        story.append(
            item
        )

    if practical_modules:

        story.append(
            Spacer(
                1,
                4 * mm,
            )
        )

    # --------------------------------------------------------
    # WORKPLACE
    # Only displayed if WM modules exist.
    # --------------------------------------------------------

    if workplace_modules:

        for item in build_module_section(
            styles,
            "Workplace Modules",
            workplace_modules,
        ):
            story.append(
                item
            )

        story.append(
            Spacer(
                1,
                4 * mm,
            )
        )

    # ========================================================
    # TOTAL REGISTERED CREDITS
    # ========================================================

    total_registered_credits = 0

    for module in modules:

        credits = (
            module.get(
                "credits"
            )
            or 0
        )

        total_registered_credits += (
            credits
        )

    total_table = Table(
        [
            [
                Paragraph(
                    (
                        "<b>"
                        "Total Registered Credits"
                        "</b>"
                    ),
                    styles["normal"],
                ),
                Paragraph(
                    (
                        f"<b>"
                        f"{total_registered_credits}"
                        f"</b>"
                    ),
                    styles[
                        "small_center"
                    ],
                ),
            ]
        ],
        colWidths=[
            140 * mm,
            35 * mm,
        ],
    )

    total_table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    colors.HexColor(
                        "#0B1F52"
                    ),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#EEF3FF"
                    ),
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, 0),
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
        total_table
    )

    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    # ========================================================
    # DECLARATION
    # ========================================================

    story.append(
        Paragraph(
            (
                "This Proof of Registration "
                "is issued by "
                f"{COMPANY_NAME} "
                "as official confirmation "
                "that the learner has been "
                "registered for the qualification "
                "and modules reflected in "
                "this document."
            ),
            styles["normal"],
        )
    )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    # ========================================================
    # REGISTRAR
    # ========================================================

    story.append(
        build_registrar_section(
            styles=styles,
            generated_at=generated_at,
            issue_date=issue_date,
            document_id=document_id,
        )
    )

    # ========================================================
    # BUILD
    # ========================================================

    document.build(
        story
    )

    return str(
        file_path
    )