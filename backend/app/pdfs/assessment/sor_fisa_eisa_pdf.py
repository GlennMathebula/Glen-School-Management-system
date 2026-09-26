from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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
# BRANDING
# ============================================================

NAVY = colors.HexColor("#0B2E59")
DARK_NAVY = colors.HexColor("#082341")
GOLD = colors.HexColor("#F2B01E")
LIGHT_GOLD = colors.HexColor("#FFF3CD")
LIGHT_BLUE = colors.HexColor("#F4F8FC")
MID_GREY = colors.HexColor("#D9E0E7")
TEXT = colors.HexColor("#1E2A35")
WHITE = colors.white


COMPANY_NAME = "GLEN MONIQUES (PTY) LTD"
TAGLINE = "Hi tirhela n’wina"

PHONE = "015 880 2413"
EMAIL = "admin@glenmoniques.co.za"
WEBSITE = "www.glenmoniques.co.za"

DEFAULT_ADDRESS = (
    "cnr mchipisi & Greenfarm Roads,Malamulele, Limpopo, South Africa, 0982"
)


# ============================================================
# STYLES
# ============================================================

TITLE_STYLE = ParagraphStyle(
    "SoRTitle",
    fontName="Helvetica-Bold",
    fontSize=17,
    leading=20,
    textColor=NAVY,
    alignment=TA_CENTER,
)

QUALIFICATION_STYLE = ParagraphStyle(
    "QualificationStyle",
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=13,
    textColor=TEXT,
    alignment=TA_CENTER,
)

QUALIFICATION_META_STYLE = ParagraphStyle(
    "QualificationMetaStyle",
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=TEXT,
    alignment=TA_CENTER,
)

LABEL_STYLE = ParagraphStyle(
    "LabelStyle",
    fontName="Helvetica-Bold",
    fontSize=7.5,
    leading=9,
    textColor=NAVY,
)

VALUE_STYLE = ParagraphStyle(
    "ValueStyle",
    fontName="Helvetica",
    fontSize=7.5,
    leading=9,
    textColor=TEXT,
)

HEADER_CELL_STYLE = ParagraphStyle(
    "HeaderCellStyle",
    fontName="Helvetica-Bold",
    fontSize=7,
    leading=8.5,
    textColor=WHITE,
    alignment=TA_CENTER,
)

CELL_STYLE = ParagraphStyle(
    "CellStyle",
    fontName="Helvetica",
    fontSize=7,
    leading=8.5,
    textColor=TEXT,
)

CENTER_CELL_STYLE = ParagraphStyle(
    "CenterCellStyle",
    fontName="Helvetica",
    fontSize=7,
    leading=8.5,
    textColor=TEXT,
    alignment=TA_CENTER,
)

SECTION_STYLE = ParagraphStyle(
    "SectionStyle",
    fontName="Helvetica-Bold",
    fontSize=8.5,
    leading=10,
    textColor=NAVY,
    alignment=TA_CENTER,
)

NOTE_STYLE = ParagraphStyle(
    "NoteStyle",
    fontName="Helvetica",
    fontSize=7.2,
    leading=9.2,
    textColor=TEXT,
)

COMPANY_NAME_STYLE = ParagraphStyle(
    "CompanyNameStyle",
    fontName="Helvetica-Bold",
    fontSize=15,
    leading=17,
    textColor=NAVY,
    alignment=TA_LEFT,
)

TAGLINE_STYLE = ParagraphStyle(
    "TaglineStyle",
    fontName="Helvetica",
    fontSize=8.2,
    leading=10,
    textColor=NAVY,
    alignment=TA_LEFT,
)

CONTACT_STYLE = ParagraphStyle(
    "ContactStyle",
    fontName="Helvetica",
    fontSize=6.7,
    leading=8.2,
    textColor=DARK_NAVY,
    alignment=TA_LEFT,
)

ADDRESS_STYLE = ParagraphStyle(
    "AddressStyle",
    fontName="Helvetica",
    fontSize=6.7,
    leading=8.2,
    textColor=DARK_NAVY,
    alignment=TA_LEFT,
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

    value = str(
        value
    ).strip()

    return (
        value
        if value
        else default
    )


def find_logo() -> Path | None:

    assets_path = (
        Path(__file__)
        .resolve()
        .parents[2]
        / "assets"
    )

    preferred_names = [
        "logo.png",
        "logo.jpg",
        "logo.jpeg",
        "glen_moniques_logo.png",
        "glen-moniques-logo.png",
        "gm_logo.png",
    ]

    for name in preferred_names:

        candidate = (
            assets_path
            / name
        )

        if candidate.exists():
            return candidate

    if assets_path.exists():

        for candidate in (
            assets_path.iterdir()
        ):

            if (
                candidate.is_file()
                and candidate.suffix.lower()
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

def build_header(
    data: dict,
) -> Table:

    logo_path = (
        find_logo()
    )

    if logo_path:

        logo = Image(
            str(
                logo_path
            ),
            width=24 * mm,
            height=24 * mm,
        )

    else:

        logo = Paragraph(
            "<b>GM</b>",
            ParagraphStyle(
                "LogoFallback",
                fontName="Helvetica-Bold",
                fontSize=20,
                textColor=NAVY,
                alignment=TA_CENTER,
            ),
        )

    company_name = Paragraph(
        COMPANY_NAME,
        COMPANY_NAME_STYLE,
    )

    tagline = Paragraph(
        TAGLINE,
        TAGLINE_STYLE,
    )

    address = Paragraph(
        clean_text(
            data.get(
                "sdp_address"
            ),
            DEFAULT_ADDRESS,
        ),
        ADDRESS_STYLE,
    )

    contact = Paragraph(
        (
            f"{PHONE}"
            f" &nbsp;&nbsp; | &nbsp;&nbsp; "
            f"{EMAIL}"
            f" &nbsp;&nbsp; | &nbsp;&nbsp; "
            f"{WEBSITE}"
        ),
        CONTACT_STYLE,
    )

    text_block = Table(
        [
            [
                company_name
            ],
            [
                tagline
            ],
            [
                address
            ],
            [
                contact
            ],
        ],
        colWidths=[
            148 * mm
        ],
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
                    (0, 0),
                    1,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 1),
                    (0, 1),
                    1,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 2),
                    (0, 2),
                    1,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 3),
                    (0, 3),
                    0,
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
                text_block,
            ]
        ],
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
            ]
        )
    )

    return header


def build_header_separator() -> Table:

    table = Table(
        [
            [""]
        ],
        colWidths=[
            180 * mm
        ],
        rowHeights=[
            1.5 * mm
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    GOLD,
                ),
            ]
        )
    )

    return table


# ============================================================
# LEARNER DETAILS
# ============================================================

def build_learner_details(
    data: dict,
) -> Table:

    rows = [
        [
            Paragraph(
                "Learner Name",
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
        ],
        [
            Paragraph(
                "ID / Passport",
                LABEL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "identity_number"
                    )
                ),
                VALUE_STYLE,
            ),
            Paragraph(
                "Date Issued",
                LABEL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "date_issued"
                    )
                ),
                VALUE_STYLE,
            ),
        ],
    ]

    table = Table(
        rows,
        colWidths=[
            28 * mm,
            62 * mm,
            28 * mm,
            62 * mm,
        ],
    )

    table.setStyle(
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

    return table


# ============================================================
# MODULE TABLE
# ============================================================

def build_component_table(
    heading: str,
    modules: list[dict],
    show_percentage: bool,
) -> Table:

    if show_percentage:

        rows = [
            [
                Paragraph(
                    "Assessment Date",
                    HEADER_CELL_STYLE,
                ),
                Paragraph(
                    "Module",
                    HEADER_CELL_STYLE,
                ),
                Paragraph(
                    "Credits",
                    HEADER_CELL_STYLE,
                ),
                Paragraph(
                    "%",
                    HEADER_CELL_STYLE,
                ),
                Paragraph(
                    "C / NYC",
                    HEADER_CELL_STYLE,
                ),
            ]
        ]

        widths = [
            27 * mm,
            93 * mm,
            18 * mm,
            19 * mm,
            23 * mm,
        ]

    else:

        rows = [
            [
                Paragraph(
                    "Assessment / Sign-off Date",
                    HEADER_CELL_STYLE,
                ),
                Paragraph(
                    "Module",
                    HEADER_CELL_STYLE,
                ),
                Paragraph(
                    "Credits",
                    HEADER_CELL_STYLE,
                ),
                Paragraph(
                    "C / NYC",
                    HEADER_CELL_STYLE,
                ),
            ]
        ]

        widths = [
            37 * mm,
            100 * mm,
            18 * mm,
            25 * mm,
        ]

    for module in modules:

        if show_percentage:

            rows.append(
                [
                    Paragraph(
                        clean_text(
                            module.get(
                                "assessment_date"
                            )
                        ),
                        CENTER_CELL_STYLE,
                    ),
                    Paragraph(
                        clean_text(
                            module.get(
                                "module_name"
                            )
                        ),
                        CELL_STYLE,
                    ),
                    Paragraph(
                        clean_text(
                            module.get(
                                "credits"
                            )
                        ),
                        CENTER_CELL_STYLE,
                    ),
                    Paragraph(
                        clean_text(
                            module.get(
                                "percentage"
                            ),
                            "-",
                        ),
                        CENTER_CELL_STYLE,
                    ),
                    Paragraph(
                        clean_text(
                            module.get(
                                "achievement"
                            )
                        ),
                        CENTER_CELL_STYLE,
                    ),
                ]
            )

        else:

            rows.append(
                [
                    Paragraph(
                        clean_text(
                            module.get(
                                "assessment_date"
                            )
                        ),
                        CENTER_CELL_STYLE,
                    ),
                    Paragraph(
                        clean_text(
                            module.get(
                                "module_name"
                            )
                        ),
                        CELL_STYLE,
                    ),
                    Paragraph(
                        clean_text(
                            module.get(
                                "credits"
                            )
                        ),
                        CENTER_CELL_STYLE,
                    ),
                    Paragraph(
                        clean_text(
                            module.get(
                                "achievement"
                            )
                        ),
                        CENTER_CELL_STYLE,
                    ),
                ]
            )

    data_table = Table(
        rows,
        colWidths=widths,
        repeatRows=1,
    )

    data_table.setStyle(
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

    wrapper = Table(
        [
            [
                Paragraph(
                    heading,
                    SECTION_STYLE,
                )
            ],
            [
                data_table
            ],
        ],
        colWidths=[
            180 * mm
        ],
    )

    wrapper.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    LIGHT_GOLD,
                ),
                (
                    "BOX",
                    (0, 0),
                    (0, 0),
                    0.5,
                    GOLD,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (0, 0),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (0, 0),
                    5,
                ),
                (
                    "LEFTPADDING",
                    (0, 1),
                    (0, 1),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 1),
                    (0, 1),
                    0,
                ),
                (
                    "TOPPADDING",
                    (0, 1),
                    (0, 1),
                    0,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 1),
                    (0, 1),
                    0,
                ),
            ]
        )
    )

    return wrapper


# ============================================================
# EISA ADMISSION
# ============================================================

def build_eisa_section(
    data: dict,
) -> Table:

    rows = [
        [
            Paragraph(
                "EISA Admission",
                LABEL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "eisa_admission"
                    ),
                    "No",
                ),
                VALUE_STYLE,
            ),
            Paragraph(
                "Next EISA Date",
                LABEL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "next_eisa_date"
                    ),
                    "To be confirmed",
                ),
                VALUE_STYLE,
            ),
        ],
        [
            Paragraph(
                "AQP",
                LABEL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "aqp_name"
                    ),
                    "To be confirmed",
                ),
                VALUE_STYLE,
            ),
            Paragraph(
                "SDP Code",
                LABEL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "sdp_code"
                    ),
                    "-",
                ),
                VALUE_STYLE,
            ),
        ],
    ]

    table = Table(
        rows,
        colWidths=[
            28 * mm,
            62 * mm,
            28 * mm,
            62 * mm,
        ],
    )

    table.setStyle(
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

    return table


# ============================================================
# SUPPORTING DOCUMENT CHECKLIST
# ============================================================

def build_document_checklist(
    data: dict,
) -> Table:

    rows = [
        [
            Paragraph(
                "SUPPORTING DOCUMENT CHECKLIST",
                SECTION_STYLE,
            ),
            "",
        ],
        [
            Paragraph(
                "Learner ID / Passport",
                CELL_STYLE,
            ),
            Paragraph(
                "✓",
                CENTER_CELL_STYLE,
            ),
        ],
    ]

    entry_document = clean_text(
        data.get(
            "entry_requirement_document"
        )
    )

    if entry_document:

        rows.append(
            [
                Paragraph(
                    entry_document,
                    CELL_STYLE,
                ),
                Paragraph(
                    "✓",
                    CENTER_CELL_STYLE,
                ),
            ]
        )

    table = Table(
        rows,
        colWidths=[
            165 * mm,
            15 * mm,
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
                    LIGHT_GOLD,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    MID_GREY,
                ),
                (
                    "INNERGRID",
                    (0, 1),
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
                    (1, 1),
                    (1, -1),
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

    return table


# ============================================================
# SIGNATURE
# ============================================================

def build_signature_section(
    data: dict,
) -> Table:

    rows = [
        [
            Paragraph(
                clean_text(
                    data.get(
                        "authorised_name"
                    ),
                    "____________________________",
                ),
                VALUE_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "date_issued"
                    ),
                    "________________",
                ),
                VALUE_STYLE,
            ),
        ],
        [
            Paragraph(
                clean_text(
                    data.get(
                        "authorised_designation"
                    ),
                    "Principal / Academic Manager",
                ),
                LABEL_STYLE,
            ),
            Paragraph(
                "Date Issued",
                LABEL_STYLE,
            ),
        ],
    ]

    return Table(
        rows,
        colWidths=[
            110 * mm,
            70 * mm,
        ],
    )


# ============================================================
# GENERATOR
# ============================================================

def generate_sor_fisa_eisa_pdf(
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
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=11 * mm,
        bottomMargin=13 * mm,
        title="Statement of Results",
        author=COMPANY_NAME,
    )

    story = [
        build_header(
            data
        ),

        Spacer(
            1,
            2.5 * mm,
        ),

        build_header_separator(),

        Spacer(
            1,
            4 * mm,
        ),

        Paragraph(
            "STATEMENT OF RESULTS",
            TITLE_STYLE,
        ),

        Spacer(
            1,
            2.5 * mm,
        ),

        Paragraph(
            clean_text(
                data.get(
                    "qualification_name"
                )
            ),
            QUALIFICATION_STYLE,
        ),

        Paragraph(
            (
                f"SAQA ID: "
                f"{clean_text(data.get('saqa_id'), '-')}"
                f" &nbsp;&nbsp; | &nbsp;&nbsp; "
                f"Credits: "
                f"{clean_text(data.get('credits'), '-')}"
                f" &nbsp;&nbsp; | &nbsp;&nbsp; "
                f"NQF Level: "
                f"{clean_text(data.get('nqf_level'), '-')}"
            ),
            QUALIFICATION_META_STYLE,
        ),

        Spacer(
            1,
            4 * mm,
        ),

        build_learner_details(
            data
        ),

        Spacer(
            1,
            4 * mm,
        ),

        build_component_table(
            "KNOWLEDGE MODULES",
            data.get(
                "knowledge_modules",
                [],
            ),
            True,
        ),

        Spacer(
            1,
            3 * mm,
        ),

        build_component_table(
            "PRACTICAL SKILLS MODULES",
            data.get(
                "practical_modules",
                [],
            ),
            False,
        ),

        Spacer(
            1,
            3 * mm,
        ),

        build_component_table(
            "WORK EXPERIENCE MODULES",
            data.get(
                "workplace_modules",
                [],
            ),
            False,
        ),

        Spacer(
            1,
            4 * mm,
        ),

        Paragraph(
            (
                "<b>Result Key:</b> "
                "C = Competent"
                " &nbsp;&nbsp; | &nbsp;&nbsp; "
                "NYC = Not Yet Competent"
            ),
            NOTE_STYLE,
        ),

        Spacer(
            1,
            3 * mm,
        ),

        build_eisa_section(
            data
        ),

        Spacer(
            1,
            4 * mm,
        ),

        Paragraph(
            (
                "<b>Note:</b> A learner gains entrance "
                "to the External Integrated Summative "
                "Assessment (EISA) when all required "
                "Knowledge, Practical Skills and Work "
                "Experience Modules have been "
                "successfully completed."
            ),
            NOTE_STYLE,
        ),

        Spacer(
            1,
            2 * mm,
        ),

        Paragraph(
            (
                "The learner must bring this Statement "
                "of Results together with their "
                "identification document when writing "
                "the EISA."
            ),
            NOTE_STYLE,
        ),

        Spacer(
            1,
            4 * mm,
        ),

        build_document_checklist(
            data
        ),

        Spacer(
            1,
            5 * mm,
        ),

        build_signature_section(
            data
        ),

        # Small blank physical stamp area only
        Spacer(
            1,
            10 * mm,
        ),

        Paragraph(
            (
                "<b>This Statement of Results is not an "
                "Occupational Certificate.</b> "
                "The learner has complied with the "
                "requirement of the practical, workplace "
                "and knowledge components of the "
                "qualification. The Quality Council for "
                "Trades and Occupations may issue the "
                "Occupational Certificate after the "
                "candidate has successfully completed "
                "the External Summative Assessment "
                "requirements."
            ),
            NOTE_STYLE,
        ),
    ]

    document.build(
        story
    )

    return output_path