from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.enums import (
    TA_CENTER,
    TA_LEFT,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ============================================================
# PATHS
# ============================================================

APP_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

ASSETS_DIR = (
    APP_DIR
    / "assets"
)

OUTPUT_DIR = (
    APP_DIR
    / "generated_pdfs"
    / "enrolment_forms"
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
# INSTITUTION
# ============================================================

COMPANY_NAME = (
    "GLEN MONIQUES (PTY) LTD"
)

DOCUMENT_TITLE = (
    "LEARNER ENROLMENT FORM"
)


# ============================================================
# HELPERS
# ============================================================

def get_current_sast() -> datetime:

    return datetime.now(
        ZoneInfo(
            "Africa/Johannesburg"
        )
    )


def safe_value(
    value,
    default: str = "N/A",
) -> str:

    if value is None:
        return default

    if isinstance(
        value,
        bool,
    ):

        return (
            "Yes"
            if value
            else "No"
        )

    if isinstance(
        value,
        str,
    ):

        cleaned = value.strip()

        if not cleaned:
            return default

        return cleaned

    return str(value)


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

        try:

            parsed = date.fromisoformat(
                value[:10]
            )

            return parsed.strftime(
                "%d %B %Y"
            )

        except Exception:

            return value

    return str(value)


def build_full_name(
    data: dict,
) -> str:

    values = [
        data.get(
            "first_name"
        ),
        data.get(
            "middle_name"
        ),
        data.get(
            "last_name"
        ),
    ]

    clean_values = [
        str(value).strip()
        for value in values
        if value
        and str(value).strip()
    ]

    return (
        " ".join(
            clean_values
        )
        or "N/A"
    )


def build_address(
    *values,
) -> str:

    clean_values = [
        str(value).strip()
        for value in values
        if value
        and str(value).strip()
    ]

    return (
        ", ".join(
            clean_values
        )
        or "N/A"
    )


def create_document_id(
    student_number: str,
    now: datetime,
) -> str:

    return (
        "ENR-"
        f"{student_number}-"
        f"{now.strftime('%Y%m%d-%H%M%S')}"
    )


# ============================================================
# STYLES
# ============================================================

def get_styles():

    base = getSampleStyleSheet()

    return {

        "title": ParagraphStyle(
            "EnrolmentTitle",
            parent=base[
                "Heading1"
            ],
            fontName=(
                "Helvetica-Bold"
            ),
            fontSize=15,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor(
                "#0B1F52"
            ),
        ),

        "section": ParagraphStyle(
            "EnrolmentSection",
            parent=base[
                "Heading2"
            ],
            fontName=(
                "Helvetica-Bold"
            ),
            fontSize=10,
            leading=13,
            textColor=colors.white,
            backColor=colors.HexColor(
                "#0B1F52"
            ),
            borderPadding=5,
            spaceBefore=4,
            spaceAfter=4,
        ),

        "normal": ParagraphStyle(
            "EnrolmentNormal",
            parent=base[
                "Normal"
            ],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            alignment=TA_LEFT,
        ),

        "small": ParagraphStyle(
            "EnrolmentSmall",
            parent=base[
                "Normal"
            ],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9,
        ),

        "center": ParagraphStyle(
            "EnrolmentCenter",
            parent=base[
                "Normal"
            ],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
        ),

        "center_bold": ParagraphStyle(
            "EnrolmentCenterBold",
            parent=base[
                "Normal"
            ],
            fontName=(
                "Helvetica-Bold"
            ),
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
        ),
    }


# ============================================================
# ASSETS
# ============================================================

def get_logo():

    styles = get_styles()

    if LOGO_PATH.exists():

        image = Image(
            str(LOGO_PATH)
        )

        image.drawHeight = (
            22 * mm
        )

        image.drawWidth = (
            22 * mm
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

        image.drawWidth = (
            42 * mm
        )

        image.drawHeight = (
            16 * mm
        )

        return image

    return Paragraph(
        "Signature image unavailable",
        styles["center"],
    )


# ============================================================
# HEADER
# ============================================================

def build_header(
    styles,
):

    institution = Table(
        [
            [
                Paragraph(
                    COMPANY_NAME,
                    styles[
                        "center_bold"
                    ],
                )
            ],
            [
                Paragraph(
                    DOCUMENT_TITLE,
                    styles[
                        "title"
                    ],
                )
            ],
            [
                Paragraph(
                    (
                        "Administrative "
                        "Learner Enrolment Record"
                    ),
                    styles[
                        "center"
                    ],
                )
            ],
        ],
        colWidths=[
            140 * mm
        ],
    )

    institution.setStyle(
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
                get_logo(),
                institution,
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

    return header


# ============================================================
# INFORMATION TABLE
# ============================================================

def build_information_table(
    styles,
    heading: str,
    rows: list[
        tuple[
            str,
            object,
        ]
    ],
):

    story = [
        Paragraph(
            heading,
            styles[
                "section"
            ],
        )
    ]

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
                    styles[
                        "normal"
                    ],
                ),
                Paragraph(
                    safe_value(
                        value
                    ),
                    styles[
                        "normal"
                    ],
                ),
            ]
        )

    table = Table(
        data,
        colWidths=[
            55 * mm,
            120 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
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
                    (0, -1),
                    colors.HexColor(
                        "#F3F6FA"
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

    story.append(
        table
    )

    return story


# ============================================================
# POPIA CONSENT
# ============================================================

def build_popia_consent(
    styles,
    data: dict,
):

    story = []

    story.append(
        Paragraph(
            (
                "POPIA Consent and "
                "Third-Party Data Sharing"
            ),
            styles[
                "section"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "I acknowledge that GLEN MONIQUES "
                "(PTY) LTD collects and processes my "
                "personal information for purposes "
                "related to my application, enrolment, "
                "training, funding, workplace placement, "
                "assessment, certification, learner "
                "administration and statutory reporting."
            ),
            styles[
                "normal"
            ],
        )
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    story.append(
        Paragraph(
            (
                "I further acknowledge and consent that, "
                "where necessary for the administration "
                "and delivery of my programme, my personal "
                "information may be shared with authorised "
                "third parties including:"
            ),
            styles[
                "normal"
            ],
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    third_parties = [
        (
            "Quality Council for Trades "
            "and Occupations (QCTO)"
        ),
        (
            "Sector Education and Training "
            "Authorities (SETAs)"
        ),
        (
            "Bursary administrators "
            "and bursars"
        ),
        (
            "Programme funders and "
            "funding organisations"
        ),
        (
            "Employers and approved "
            "workplace training providers"
        ),
    ]

    for party in third_parties:

        story.append(
            Paragraph(
                f"• {party}",
                styles[
                    "normal"
                ],
            )
        )

        story.append(
            Spacer(
                1,
                1.5 * mm,
            )
        )

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    story.append(
        Paragraph(
            (
                "I understand that such information "
                "will be used where reasonably required "
                "for learner registration, programme "
                "funding, training administration, "
                "workplace learning, assessment, "
                "certification, monitoring, reporting "
                "and related educational purposes."
            ),
            styles[
                "normal"
            ],
        )
    )

    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    consent_status = (
        "Yes"
        if data.get(
            "popi_agree"
        )
        else "No"
    )

    popia_date = (
        format_date(
            data.get(
                "popi_date"
            )
        )
    )

    consent_table = Table(
        [
            [
                Paragraph(
                    (
                        "<b>POPIA Consent "
                        "Recorded</b>"
                    ),
                    styles[
                        "normal"
                    ],
                ),
                Paragraph(
                    consent_status,
                    styles[
                        "normal"
                    ],
                ),
            ],
            [
                Paragraph(
                    (
                        "<b>POPIA Consent "
                        "Date</b>"
                    ),
                    styles[
                        "normal"
                    ],
                ),
                Paragraph(
                    popia_date,
                    styles[
                        "normal"
                    ],
                ),
            ],
        ],
        colWidths=[
            70 * mm,
            105 * mm,
        ],
    )

    consent_table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
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
                    (0, -1),
                    colors.HexColor(
                        "#F3F6FA"
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

    story.append(
        consent_table
    )

    story.append(
        Spacer(
            1,
            16 * mm,
        )
    )

    signature_table = Table(
        [
            [
                Paragraph(
                    (
                        "________________________"
                        "________________"
                    ),
                    styles[
                        "center"
                    ],
                ),
                Paragraph(
                    popia_date,
                    styles[
                        "center"
                    ],
                ),
            ],
            [
                Paragraph(
                    (
                        "<b>Learner POPIA "
                        "Signature</b>"
                    ),
                    styles[
                        "center"
                    ],
                ),
                Paragraph(
                    "<b>POPIA Date</b>",
                    styles[
                        "center"
                    ],
                ),
            ],
        ],
        colWidths=[
            100 * mm,
            75 * mm,
        ],
    )

    signature_table.setStyle(
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
                    "BOTTOM",
                ),
            ]
        )
    )

    story.append(
        signature_table
    )

    return story


# ============================================================
# LEARNER DECLARATION
# ============================================================

def build_learner_declaration(
    styles,
):

    story = []

    story.append(
        Paragraph(
            "Learner Declaration",
            styles[
                "section"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "I declare that the information "
                "recorded on this enrolment form "
                "is true and correct to the best "
                "of my knowledge. I understand "
                "that this information may be used "
                "for learner enrolment, training "
                "administration, assessment, "
                "certification and statutory "
                "reporting purposes."
            ),
            styles[
                "normal"
            ],
        )
    )

    story.append(
        Spacer(
            1,
            15 * mm,
        )
    )

    table = Table(
        [
            [
                Paragraph(
                    (
                        "________________"
                        "________________"
                    ),
                    styles[
                        "center"
                    ],
                ),
                Paragraph(
                    (
                        "________________"
                        "________________"
                    ),
                    styles[
                        "center"
                    ],
                ),
            ],
            [
                Paragraph(
                    "<b>Learner Signature</b>",
                    styles[
                        "center"
                    ],
                ),
                Paragraph(
                    "<b>Date</b>",
                    styles[
                        "center"
                    ],
                ),
            ],
        ],
        colWidths=[
            90 * mm,
            85 * mm,
        ],
    )

    table.setStyle(
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
                    "BOTTOM",
                ),
            ]
        )
    )

    story.append(
        table
    )

    return story


# ============================================================
# REGISTRAR CONFIRMATION
# ============================================================

def build_registrar_confirmation(
    styles,
):

    story = []

    story.append(
        Paragraph(
            "Institutional Confirmation",
            styles[
                "section"
            ],
        )
    )

    story.append(
        Paragraph(
            (
                "The institution confirms that "
                "the learner has been enrolled "
                "against the programme information "
                "recorded in this document."
            ),
            styles[
                "normal"
            ],
        )
    )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    table = Table(
        [
            [
                get_registrar_signature(),
                "",
            ],
            [
                Paragraph(
                    (
                        "________________"
                        "________________"
                    ),
                    styles[
                        "center"
                    ],
                ),
                Paragraph(
                    (
                        "________________"
                        "________________"
                    ),
                    styles[
                        "center"
                    ],
                ),
            ],
            [
                Paragraph(
                    "<b>Registrar</b>",
                    styles[
                        "center"
                    ],
                ),
                Paragraph(
                    "<b>Date</b>",
                    styles[
                        "center"
                    ],
                ),
            ],
        ],
        colWidths=[
            90 * mm,
            85 * mm,
        ],
    )

    table.setStyle(
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
                    "BOTTOM",
                ),
            ]
        )
    )

    story.append(
        table
    )

    return story


# ============================================================
# GENERATE ENROLMENT FORM
# ============================================================


# ============================================================
# GM_ENROLMENT_DISPLAY_HELPERS_V1
# Stored database/QCTO codes remain unchanged. These helpers
# translate only learner-facing document values.
# ============================================================

GM_ENROLMENT_DISPLAY_MAPS = {
    "gender_code": {"M": "Male", "F": "Female"},
    "equity_code": {
        "BA": "African",
        "BC": "Coloured",
        "BI": "Indian",
        "Oth": "Other",
        "U": "Unknown",
        "Wh": "White",
        "WH": "White",
    },
    "nationality_code": {
        "SA": "South Africa",
        "SDC": "SADC except South Africa",
        "ANG": "Angola",
        "BOT": "Botswana",
        "LES": "Lesotho",
        "MAL": "Malawi",
        "MAU": "Mauritius",
        "MOZ": "Mozambique",
        "NAM": "Namibia",
        "SEY": "Seychelles",
        "SWA": "Eswatini",
        "TAN": "Tanzania",
        "ZAI": "Zaire",
        "ZAM": "Zambia",
        "ZIM": "Zimbabwe",
        "AIS": "Asian countries",
        "AUS": "Australia and Oceania countries",
        "EUR": "European countries",
        "NOR": "North American countries",
        "SOU": "South and Central American countries",
        "ROA": "Rest of Africa",
        "OOC": "Other and rest of Oceania",
        "NOT": "Not applicable / Institution",
        "U": "Unspecified",
    },
    "home_language": {
        "Afr": "Afrikaans",
        "Eng": "English",
        "Nde": "isiNdebele",
        "Oth": "Other",
        "SASL": "South African Sign Language",
        "Sep": "Sepedi",
        "Ses": "Sesotho",
        "Set": "Setswana",
        "Swa": "Siswati",
        "Tsh": "Tshivenda",
        "U": "Unknown",
        "Xho": "isiXhosa",
        "Xit": "Xitsonga",
        "Zul": "isiZulu",
    },
    "citizen_status": {
        "SA": "South African",
        "O": "Other",
        "D": "Dual (South Africa plus other)",
        "PR": "Permanent Resident",
        "U": "Unknown",
    },
    "socioeconomic_code": {
        "01": "Employed",
        "02": "Unemployed, seeking work",
        "03": "Not working, not looking for work",
        "04": "Home-maker (not working)",
        "06": "Scholar / Student (not working)",
        "07": "Pensioner / Retired (not working)",
        "08": "Not working - disabled",
        "09": "Not working - no wish to work",
        "10": "Not working - none of the above",
        "97": "N/A - aged under 15",
        "98": "N/A - Institution",
        "U": "Unspecified",
    },
    "disability_status": {
        "N": "None",
        "01": "Sight difficulty (even with glasses)",
        "02": "Hearing difficulty (even with hearing aid)",
        "03": "Communication difficulty (talking / listening)",
        "04": "Physical difficulty (moving / standing / grasping)",
        "05": "Intellectual difficulty (learning)",
        "06": "Emotional / behavioural / psychological difficulty",
        "07": "Multiple disabilities",
        "09": "Disabled but unspecified",
        "U": "Unknown disability status",
    },
    "disability_rating": {
        "01": "No difficulty",
        "02": "Some difficulty",
        "03": "A lot of difficulty",
        "04": "Cannot do at all",
        "06": "Cannot yet be determined",
        "60": "May be part of multiple difficulties",
        "70": "May have difficulty",
        "80": "Former difficulty - none now",
    },
    "immigrant_status": {
        "01": "Immigrant",
        "02": "Refugee",
        "03": "SA Citizen",
    },
    "province_code": {
        "1": "Western Cape",
        "2": "Eastern Cape",
        "3": "Northern Cape",
        "4": "Free State",
        "5": "KwaZulu-Natal",
        "6": "North West",
        "7": "Gauteng",
        "8": "Mpumalanga",
        "9": "Limpopo",
        "N": "South Africa National",
        "X": "Outside South Africa",
    },
}

GM_ASSESSMENT_TYPE_LABELS = {
    "FISA_ONLY": "FISA",
    "FISA": "FISA",
    "FISA_PLUS_EISA": "FISA + EISA",
    "FISA+EISA": "FISA + EISA",
    "FISA + EISA": "FISA + EISA",
}


def _gm_display_code(field_name, value):
    if value is None:
        return value
    text_value = str(value).strip()
    if not text_value:
        return value
    mapping = GM_ENROLMENT_DISPLAY_MAPS.get(field_name, {})
    return mapping.get(text_value, mapping.get(text_value.upper(), value))


def _gm_display_assessment_type(value):
    if value is None:
        return value
    text_value = str(value).strip()
    if not text_value:
        return value
    return GM_ASSESSMENT_TYPE_LABELS.get(
        text_value,
        GM_ASSESSMENT_TYPE_LABELS.get(text_value.upper(), value),
    )


def _gm_format_academic_subjects(value):
    if value is None:
        return value

    import json

    parsed = value

    if isinstance(parsed, str):
        candidate = parsed.strip()
        if not candidate:
            return parsed

        for _ in range(2):
            try:
                parsed = json.loads(candidate)
            except Exception:
                break

            if isinstance(parsed, str):
                candidate = parsed.strip()
                continue
            break

    if isinstance(parsed, dict):
        parsed = [parsed]

    if not isinstance(parsed, list):
        return value

    readable = []

    for item in parsed:
        if not isinstance(item, dict):
            item_text = str(item).strip()
            if item_text:
                readable.append(item_text)
            continue

        category = (
            item.get("category")
            or item.get("subject_category")
            or item.get("type")
            or ""
        )
        subject = (
            item.get("subject")
            or item.get("subject_name")
            or item.get("name")
            or ""
        )
        achievement = (
            item.get("achievement_level")
            or item.get("achievement")
            or item.get("result")
            or item.get("level")
            or ""
        )

        category = str(category).strip()
        subject = str(subject).strip()
        achievement = str(achievement).strip()

        if subject and category:
            line = f"{category}: {subject}"
        else:
            line = subject or category

        if achievement:
            line = f"{line} - {achievement}" if line else achievement

        if line:
            readable.append(line)

    if not readable:
        return "N/A"

    return "  |  ".join(readable)


def _gm_prepare_enrolment_display_data(data):
    result = dict(data or {})

    for field_name in GM_ENROLMENT_DISPLAY_MAPS:
        if field_name in result:
            result[field_name] = _gm_display_code(
                field_name,
                result.get(field_name),
            )

    if "assessment_type" in result:
        result["assessment_type"] = _gm_display_assessment_type(
            result.get("assessment_type")
        )

    if "academic_subjects" in result:
        result["academic_subjects"] = _gm_format_academic_subjects(
            result.get("academic_subjects")
        )

    if isinstance(result.get("rpl_admission"), bool):
        result["rpl_admission"] = "Yes" if result["rpl_admission"] else "No"

    return result


def generate_enrolment_form(
    data: dict,
) -> str:
    data = _gm_prepare_enrolment_display_data(data)

    styles = get_styles()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    now = get_current_sast()

    student_number = safe_value(
        data.get(
            "student_number"
        ),
        "UNKNOWN",
    )

    document_id = (
        create_document_id(
            student_number,
            now,
        )
    )

    filename = (
        "enrolment_form_"
        f"{student_number}_"
        f"{now.strftime('%Y%m%d_%H%M%S')}"
        ".pdf"
    )

    file_path = (
        OUTPUT_DIR
        / filename
    )

    document = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=DOCUMENT_TITLE,
        author=COMPANY_NAME,
    )

    story = []

    # ========================================================
    # PAGE 1
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

    # ========================================================
    # DOCUMENT INFORMATION
    # ========================================================

    for item in build_information_table(
        styles,
        "Document Information",
        [
            (
                "Document ID",
                document_id,
            ),
            (
                "Generated Date",
                format_date(
                    now
                ),
            ),
            (
                "Student Number",
                student_number,
            ),
            (
                "Registration Status",
                data.get(
                    "registration_status"
                ),
            ),
        ],
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
    # PERSONAL INFORMATION
    # ========================================================

    for item in build_information_table(
        styles,
        "Learner Personal Information",
        [
            (
                "Title",
                data.get(
                    "title"
                ),
            ),
            (
                "Full Name",
                build_full_name(
                    data
                ),
            ),
            (
                "National ID",
                data.get(
                    "national_id"
                ),
            ),
            (
                "Alternate ID",
                data.get(
                    "alternate_id"
                ),
            ),
            (
                "Alternate ID Type",
                data.get(
                    "alt_id_type"
                ),
            ),
            (
                "Date of Birth",
                format_date(
                    data.get(
                        "birth_date"
                    )
                ),
            ),
            (
                "Gender",
                data.get(
                    "gender_code"
                ),
            ),
            (
                "Equity",
                data.get(
                    "equity_code"
                ),
            ),
            (
                "Nationality",
                data.get(
                    "nationality_code"
                ),
            ),
            (
                "Home Language",
                data.get(
                    "home_language"
                ),
            ),
            (
                "Citizen Status",
                data.get(
                    "citizen_status"
                ),
            ),
            (
                "Socioeconomic Status",
                data.get(
                    "socioeconomic_code"
                ),
            ),
        ],
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
    # CONTACT AND ADDRESS
    # ========================================================

    residential_address = (
        build_address(
            data.get(
                "home_addr_1"
            ),
            data.get(
                "home_addr_2"
            ),
            data.get(
                "home_addr_3"
            ),
        )
    )

    postal_address = (
        build_address(
            data.get(
                "postal_addr_1"
            ),
            data.get(
                "postal_addr_2"
            ),
            data.get(
                "postal_addr_3"
            ),
        )
    )

    for item in build_information_table(
        styles,
        "Contact and Address Information",
        [
            (
                "Residential Address",
                residential_address,
            ),
            (
                "Residential Postal Code",
                data.get(
                    "home_postal_code"
                ),
            ),
            (
                "Postal Address",
                postal_address,
            ),
            (
                "Postal Code",
                data.get(
                    "postal_code"
                ),
            ),
            (
                "Province",
                data.get(
                    "province_code"
                ),
            ),
            (
                "Stats SA Area Code",
                data.get(
                    "statssa_code"
                ),
            ),
            (
                "Telephone",
                data.get(
                    "phone_number"
                ),
            ),
            (
                "Cell Number",
                data.get(
                    "cell_number"
                ),
            ),
            (
                "Fax Number",
                data.get(
                    "fax_number"
                ),
            ),
            (
                "Email Address",
                data.get(
                    "email"
                ),
            ),
        ],
    ):

        story.append(
            item
        )

    # ========================================================
    # PAGE 2
    # ========================================================

    story.append(
        PageBreak()
    )

    # ========================================================
    # LEARNER STATUS INFORMATION
    # ========================================================

    for item in build_information_table(
        styles,
        "Learner Status Information",
        [
            (
                "Disability Status",
                data.get(
                    "disability_status"
                ),
            ),
            (
                "Disability Rating",
                data.get(
                    "disability_rating"
                ),
            ),
            (
                "Immigrant Status",
                data.get(
                    "immigrant_status"
                ),
            ),
        ],
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
    # EDUCATIONAL BACKGROUND
    # ========================================================

    for item in build_information_table(
        styles,
        "Educational Background",
        [
            (
                "Highest Grade Passed",
                data.get(
                    "highest_grade"
                ),
            ),
            (
                "School Name",
                data.get(
                    "school_name"
                ),
            ),
            (
                "Year Completed",
                data.get(
                    "year_completed"
                ),
            ),
            (
                "Academic Subjects",
                data.get(
                    "academic_subjects"
                ),
            ),
        ],
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
    # EMPLOYMENT AND RPL
    # ========================================================

    for item in build_information_table(
        styles,
        "Employment and Admission Information",
        [
            (
                "Employment Status",
                data.get(
                    "employment_status"
                ),
            ),
            (
                "RPL Admission",
                data.get(
                    "rpl_admission"
                ),
            ),
        ],
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
    # NEXT OF KIN
    # ========================================================

    for item in build_information_table(
        styles,
        "Next of Kin Information",
        [
            (
                "Surname",
                data.get(
                    "next_of_kin_surname"
                ),
            ),
            (
                "Full Name",
                data.get(
                    "next_of_kin_full_name"
                ),
            ),
            (
                "Relationship",
                data.get(
                    "next_of_kin_relationship"
                ),
            ),
            (
                "Cell Number",
                data.get(
                    "next_of_kin_cell"
                ),
            ),
            (
                "Email Address",
                data.get(
                    "next_of_kin_email"
                ),
            ),
        ],
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
    # PROGRAMME INFORMATION
    # ========================================================

    for item in build_information_table(
        styles,
        "Programme and Enrolment Information",
        [
            (
                "Qualification Code",
                data.get(
                    "course_code"
                ),
            ),
            (
                "Qualification Name",
                data.get(
                    "course_name"
                ),
            ),
            (
                "NQF Level",
                data.get(
                    "nqf_level"
                ),
            ),
            (
                "Credits",
                data.get(
                    "credits"
                ),
            ),
            (
                "SDP Code",
                data.get(
                    "sdp_code"
                ),
            ),
            (
                "Registration Date",
                format_date(
                    data.get(
                        "registration_date"
                    )
                ),
            ),
            (
                "Programme Start Date",
                format_date(
                    data.get(
                        "program_start_date"
                    )
                ),
            ),
            (
                "Expected Completion Date",
                format_date(
                    data.get(
                        "expected_completion_date"
                    )
                ),
            ),
            (
                "Academic Cycle",
                data.get(
                    "cycle"
                ),
            ),
            (
                "Funding Type",
                data.get(
                    "funding_type"
                ),
            ),
            (
                "Sponsor ID",
                data.get(
                    "sponsor_id"
                ),
            ),
            (
                "Sponsor",
                data.get(
                    "sponsor_name"
                ),
            ),
            (
                "Assessment Type",
                data.get(
                    "assessment_type"
                ),
            ),
        ],
    ):

        story.append(
            item
        )

    # ========================================================
    # PAGE 3
    # POPIA MUST ALWAYS START ON A FRESH PAGE
    # ========================================================

    story.append(
        PageBreak()
    )

    for item in build_popia_consent(
        styles,
        data,
    ):

        story.append(
            item
        )

    # ========================================================
    # PAGE 4
    # DECLARATION AND INSTITUTION
    # ========================================================

    story.append(
        PageBreak()
    )

    # ========================================================
    # LEARNER DECLARATION
    # ========================================================

    for item in build_learner_declaration(
        styles
    ):

        story.append(
            item
        )

    story.append(
        Spacer(
            1,
            12 * mm,
        )
    )

    # ========================================================
    # REGISTRAR CONFIRMATION
    # ========================================================

    for item in build_registrar_confirmation(
        styles
    ):

        story.append(
            item
        )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    # ========================================================
    # ADMINISTRATION NOTE
    # ========================================================

    story.append(
        Paragraph(
            (
                "<b>Administration Note:</b> "
                "This document must be printed "
                "and physically signed by the learner. "
                "The signed copy, including the learner's "
                "POPIA consent signature, must be retained "
                "as part of the learner's official "
                "enrolment record."
            ),
            styles[
                "small"
            ],
        )
    )

    document.build(
        story
    )

    return str(
        file_path
    )