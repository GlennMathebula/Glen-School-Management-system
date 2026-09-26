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


# ============================================================
# STYLES
# ============================================================

TITLE_STYLE = ParagraphStyle(
    "FisaOnlyTitle",
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

NOTE_STYLE = ParagraphStyle(
    "NoteStyle",
    fontName="Helvetica",
    fontSize=7.3,
    leading=9.3,
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
    fontSize=6.8,
    leading=8.5,
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

    value = str(value).strip()

    return value if value else default


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

        candidate = assets_path / name

        if candidate.exists():
            return candidate

    if assets_path.exists():

        for candidate in assets_path.iterdir():

            if (
                candidate.is_file()
                and candidate.suffix.lower()
                in {".png", ".jpg", ".jpeg"}
                and "logo" in candidate.name.lower()
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
            width=24 * mm,
            height=17 * mm,
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
            [company_name],
            [tagline],
            [contact],
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
                    (0, 0),
                    0,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (0, 0),
                    1,
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
                    2,
                ),
                (
                    "TOPPADDING",
                    (0, 2),
                    (0, 2),
                    0,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 2),
                    (0, 2),
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
        [[""]],
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
# MODULE RESULTS
# ============================================================

def build_modules_table(
    modules: list[dict],
) -> Table:

    rows = [
        [
            Paragraph(
                "Type",
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

    for module in modules:

        module_type = clean_text(
            module.get(
                "module_type"
            )
        )

        percentage = "-"

        if module_type == "KM":

            percentage = clean_text(
                module.get(
                    "percentage"
                ),
                "-",
            )

        rows.append(
            [
                Paragraph(
                    module_type,
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
                    percentage,
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

    table = Table(
        rows,
        colWidths=[
            15 * mm,
            104 * mm,
            18 * mm,
            18 * mm,
            25 * mm,
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
# FISA RESULT
# ============================================================

def build_fisa_result_table(
    data: dict,
) -> Table:

    fisa_format = clean_text(
        data.get(
            "fisa_result_format"
        ),
        "COMPETENCY",
    )

    if (
        fisa_format
        == "PERCENTAGE_COMPETENCY"
    ):

        rows = [
            [
                Paragraph(
                    "FISA Date",
                    LABEL_STYLE,
                ),
                Paragraph(
                    clean_text(
                        data.get(
                            "fisa_date"
                        )
                    ),
                    VALUE_STYLE,
                ),
                Paragraph(
                    "FISA Mark",
                    LABEL_STYLE,
                ),
                Paragraph(
                    clean_text(
                        data.get(
                            "fisa_mark"
                        ),
                        "-",
                    ),
                    VALUE_STYLE,
                ),
            ],
            [
                Paragraph(
                    "FISA Result",
                    LABEL_STYLE,
                ),
                Paragraph(
                    clean_text(
                        data.get(
                            "fisa_result"
                        )
                    ),
                    VALUE_STYLE,
                ),
                Paragraph(
                    "Overall Result",
                    LABEL_STYLE,
                ),
                Paragraph(
                    clean_text(
                        data.get(
                            "overall_result"
                        )
                    ),
                    VALUE_STYLE,
                ),
            ],
        ]

    else:

        rows = [
            [
                Paragraph(
                    "FISA Date",
                    LABEL_STYLE,
                ),
                Paragraph(
                    clean_text(
                        data.get(
                            "fisa_date"
                        )
                    ),
                    VALUE_STYLE,
                ),
                Paragraph(
                    "FISA Result",
                    LABEL_STYLE,
                ),
                Paragraph(
                    clean_text(
                        data.get(
                            "fisa_result"
                        )
                    ),
                    VALUE_STYLE,
                ),
            ],
            [
                Paragraph(
                    "Overall Result",
                    LABEL_STYLE,
                ),
                Paragraph(
                    clean_text(
                        data.get(
                            "overall_result"
                        )
                    ),
                    VALUE_STYLE,
                ),
                Paragraph(
                    "Assessment Pathway",
                    LABEL_STYLE,
                ),
                Paragraph(
                    "FISA ONLY",
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
                    LIGHT_GOLD,
                ),
                (
                    "BACKGROUND",
                    (2, 0),
                    (2, -1),
                    LIGHT_GOLD,
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
# GENERATOR
# ============================================================

def generate_sor_fisa_only_pdf(
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
        topMargin=12 * mm,
        bottomMargin=15 * mm,
        title="Statement of Results",
        author=COMPANY_NAME,
    )

    story = [
        build_header(),

        Spacer(
            1,
            3 * mm,
        ),

        build_header_separator(),

        Spacer(
            1,
            5 * mm,
        ),

        Paragraph(
            "STATEMENT OF RESULTS",
            TITLE_STYLE,
        ),

        Spacer(
            1,
            3 * mm,
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
                f"NQF Level: "
                f"{clean_text(data.get('nqf_level'), '-')}"
                f" &nbsp;&nbsp; | &nbsp;&nbsp; "
                f"Credits: "
                f"{clean_text(data.get('credits'), '-')}"
            ),
            QUALIFICATION_META_STYLE,
        ),

        Spacer(
            1,
            5 * mm,
        ),

        build_learner_details(
            data
        ),

        Spacer(
            1,
            6 * mm,
        ),

        Table(
            [
                [
                    Paragraph(
                        "MODULE RESULTS",
                        ParagraphStyle(
                            "ModuleHeading",
                            fontName="Helvetica-Bold",
                            fontSize=8.5,
                            leading=10,
                            textColor=NAVY,
                            alignment=TA_CENTER,
                        ),
                    )
                ],
                [
                    build_modules_table(
                        data.get(
                            "modules",
                            [],
                        )
                    )
                ],
            ],
            colWidths=[
                180 * mm
            ],
            style=TableStyle(
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
            ),
        ),

        Spacer(
            1,
            6 * mm,
        ),

        Paragraph(
            "FINAL INTEGRATED SUMMATIVE ASSESSMENT",
            ParagraphStyle(
                "FisaHeading",
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=11,
                textColor=NAVY,
                alignment=TA_CENTER,
            ),
        ),

        Spacer(
            1,
            3 * mm,
        ),

        build_fisa_result_table(
            data
        ),

        Spacer(
            1,
            5 * mm,
        ),

        Paragraph(
            (
                "<b>Result Key:</b> "
                "C = Competent &nbsp;&nbsp; | &nbsp;&nbsp; "
                "NYC = Not Yet Competent"
            ),
            NOTE_STYLE,
        ),

        Spacer(
            1,
            5 * mm,
        ),

        Table(
            [
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
            ],
            colWidths=[
                110 * mm,
                70 * mm,
            ],
        ),

        Spacer(
            1,
            6 * mm,
        ),

        Paragraph(
            (
                "<b>This Statement of Results is not an "
                "Occupational Certificate.</b> "
                "It records the learner's academic and "
                "Final Integrated Summative Assessment results "
                "for the programme indicated above."
            ),
            NOTE_STYLE,
        ),

        Spacer(
            1,
            5 * mm,
        ),

        Table(
            [
                [
                    Paragraph(
                        "<b>STAMP OF THE INSTITUTION</b>",
                        LABEL_STYLE,
                    )
                ],
                [
                    ""
                ],
            ],
            colWidths=[
                180 * mm
            ],
            rowHeights=[
                8 * mm,
                22 * mm,
            ],
            style=TableStyle(
                [
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        NAVY,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        LIGHT_BLUE,
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
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            ),
        ),
    ]

    document.build(
        story
    )

    return output_path