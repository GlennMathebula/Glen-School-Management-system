from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import (
    TA_CENTER,
    TA_LEFT,
)
from reportlab.lib.pagesizes import (
    A4,
    landscape,
)
from reportlab.lib.styles import (
    ParagraphStyle,
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
# PAGE SETTINGS
# ============================================================

PAGE_SIZE = landscape(
    A4
)

LEFT_MARGIN = 8 * mm
RIGHT_MARGIN = 8 * mm
TOP_MARGIN = 8 * mm
BOTTOM_MARGIN = 10 * mm


# ============================================================
# STYLES
# ============================================================

TITLE_STYLE = ParagraphStyle(
    "DailyAttendanceTitle",
    fontName="Helvetica-Bold",
    fontSize=13,
    leading=15,
    alignment=TA_CENTER,
)

SUBTITLE_STYLE = ParagraphStyle(
    "DailyAttendanceSubtitle",
    fontName="Helvetica-Bold",
    fontSize=9,
    leading=11,
    alignment=TA_CENTER,
)

CONTROL_STYLE = ParagraphStyle(
    "DailyAttendanceControl",
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=10,
    alignment=TA_CENTER,
)

NORMAL_STYLE = ParagraphStyle(
    "DailyAttendanceNormal",
    fontName="Helvetica",
    fontSize=7,
    leading=9,
    alignment=TA_LEFT,
)

SMALL_STYLE = ParagraphStyle(
    "DailyAttendanceSmall",
    fontName="Helvetica",
    fontSize=6,
    leading=7,
    alignment=TA_LEFT,
)

TABLE_HEADER_STYLE = ParagraphStyle(
    "DailyAttendanceHeader",
    fontName="Helvetica-Bold",
    fontSize=6,
    leading=7,
    alignment=TA_CENTER,
)

STUDENT_STYLE = ParagraphStyle(
    "DailyAttendanceStudent",
    fontName="Helvetica",
    fontSize=6.5,
    leading=8,
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

    if not value:
        return default

    return value


def format_date(
    value,
) -> str:

    if not value:
        return ""

    if hasattr(
        value,
        "strftime",
    ):

        return value.strftime(
            "%A, %d %B %Y"
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
    ]

    for name in possible_names:

        candidate = (
            assets_directory
            / name
        )

        if candidate.exists():

            return candidate

    return None


def get_full_name(
    student: dict,
) -> str:

    parts = [
        clean_text(
            student.get(
                "first_name"
            )
        ),
        clean_text(
            student.get(
                "middle_name"
            )
        ),
        clean_text(
            student.get(
                "last_name"
            )
        ),
    ]

    return " ".join(
        part
        for part in parts
        if part
    )


def get_identity_number(
    student: dict,
) -> str:

    national_id = clean_text(
        student.get(
            "national_id"
        )
    )

    if national_id:

        return national_id

    alternate_id = clean_text(
        student.get(
            "alternate_id"
        )
    )

    return alternate_id


# ============================================================
# HEADER
# ============================================================

def build_page_header(
    data: dict,
    day: dict,
) -> list:

    elements = []

    logo_path = find_logo()

    if logo_path:

        logo = Image(
            str(
                logo_path
            ),
            width=22 * mm,
            height=15 * mm,
        )

        logo.hAlign = "CENTER"

        elements.append(
            logo
        )

        elements.append(
            Spacer(
                1,
                1 * mm,
            )
        )

    elements.append(
        Paragraph(
            "GLEN MONIQUES (PTY) LTD",
            TITLE_STYLE,
        )
    )

    elements.append(
        Paragraph(
            "DAILY LEARNER ATTENDANCE REGISTER",
            SUBTITLE_STYLE,
        )
    )

    elements.append(
        Paragraph(
            (
                f"CONTROL NO: "
                f"{clean_text(data.get('control_number'))}"
            ),
            CONTROL_STYLE,
        )
    )

    elements.append(
        Spacer(
            1,
            2.5 * mm,
        )
    )

    programme = data[
        "programme"
    ]

    class_data = data[
        "class"
    ]

    information = [
        [
            Paragraph(
                "<b>Date:</b>",
                NORMAL_STYLE,
            ),
            Paragraph(
                format_date(
                    day[
                        "date"
                    ]
                ),
                NORMAL_STYLE,
            ),
            Paragraph(
                "<b>Cycle:</b>",
                NORMAL_STYLE,
            ),
            Paragraph(
                clean_text(
                    class_data.get(
                        "cycle_code"
                    )
                ),
                NORMAL_STYLE,
            ),
            Paragraph(
                "<b>Class:</b>",
                NORMAL_STYLE,
            ),
            Paragraph(
                clean_text(
                    class_data.get(
                        "class_code"
                    )
                ),
                NORMAL_STYLE,
            ),
        ],
        [
            Paragraph(
                "<b>Programme:</b>",
                NORMAL_STYLE,
            ),
            Paragraph(
                clean_text(
                    programme.get(
                        "course_name"
                    )
                ),
                NORMAL_STYLE,
            ),
            Paragraph(
                "<b>Programme Code:</b>",
                NORMAL_STYLE,
            ),
            Paragraph(
                clean_text(
                    programme.get(
                        "course_code"
                    )
                ),
                NORMAL_STYLE,
            ),
            Paragraph(
                "<b>NQF Level:</b>",
                NORMAL_STYLE,
            ),
            Paragraph(
                clean_text(
                    programme.get(
                        "nqf_level"
                    )
                ),
                NORMAL_STYLE,
            ),
        ],
        [
            Paragraph(
                "<b>Module(s):</b>",
                NORMAL_STYLE,
            ),
            Paragraph(
                clean_text(
                    day.get(
                        "modules_text"
                    ),
                    "As per timetable",
                ),
                NORMAL_STYLE,
            ),
            Paragraph(
                "<b>Venue:</b>",
                NORMAL_STYLE,
            ),
            Paragraph(
                clean_text(
                    day.get(
                        "venue"
                    ),
                    "As per timetable",
                ),
                NORMAL_STYLE,
            ),
            Paragraph(
                "<b>Facilitator:</b>",
                NORMAL_STYLE,
            ),
            Paragraph(
                clean_text(
                    class_data.get(
                        "facilitator_code"
                    ),
                    "Not assigned",
                ),
                NORMAL_STYLE,
            ),
        ],
        [
            Paragraph(
                "<b>SDP Name:</b>",
                NORMAL_STYLE,
            ),
            Paragraph(
                "Glen Moniques (Pty) Ltd",
                NORMAL_STYLE,
            ),
            Paragraph(
                "<b>SDP Code:</b>",
                NORMAL_STYLE,
            ),
            Paragraph(
                clean_text(
                    programme.get(
                        "sdp_code"
                    ),
                    "Not configured",
                ),
                NORMAL_STYLE,
            ),
            Paragraph(
                "<b>Total Learners:</b>",
                NORMAL_STYLE,
            ),
            Paragraph(
                str(
                    len(
                        data[
                            "students"
                        ]
                    )
                ),
                NORMAL_STYLE,
            ),
        ],
    ]

    table = Table(
        information,
        colWidths=[
            20 * mm,
            68 * mm,
            28 * mm,
            55 * mm,
            25 * mm,
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
                    0.35,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.whitesmoke,
                ),
                (
                    "BACKGROUND",
                    (2, 0),
                    (2, -1),
                    colors.whitesmoke,
                ),
                (
                    "BACKGROUND",
                    (4, 0),
                    (4, -1),
                    colors.whitesmoke,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
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

    elements.append(
        table
    )

    elements.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    return elements


# ============================================================
# REGISTER TABLE
# ============================================================

def build_attendance_table(
    students: list[dict],
):

    headers = [
        Paragraph(
            "No.",
            TABLE_HEADER_STYLE,
        ),
        Paragraph(
            "Student Number",
            TABLE_HEADER_STYLE,
        ),
        Paragraph(
            "ID / Passport Number",
            TABLE_HEADER_STYLE,
        ),
        Paragraph(
            "Full Name",
            TABLE_HEADER_STYLE,
        ),
        Paragraph(
            "Sign-in Time",
            TABLE_HEADER_STYLE,
        ),
        Paragraph(
            "Sign-in Signature",
            TABLE_HEADER_STYLE,
        ),
        Paragraph(
            "Sign-out Time",
            TABLE_HEADER_STYLE,
        ),
        Paragraph(
            "Sign-out Signature",
            TABLE_HEADER_STYLE,
        ),
    ]

    rows = [
        headers
    ]

    for number, student in enumerate(
        students,
        start=1,
    ):

        rows.append(
            [
                str(
                    number
                ),

                Paragraph(
                    clean_text(
                        student.get(
                            "student_number"
                        )
                    ),
                    STUDENT_STYLE,
                ),

                Paragraph(
                    get_identity_number(
                        student
                    ),
                    STUDENT_STYLE,
                ),

                Paragraph(
                    get_full_name(
                        student
                    ),
                    STUDENT_STYLE,
                ),

                "",
                "",
                "",
                "",
            ]
        )

    table = Table(
        rows,
        colWidths=[
            8 * mm,
            25 * mm,
            31 * mm,
            43 * mm,
            20 * mm,
            43 * mm,
            20 * mm,
            43 * mm,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.45,
                    colors.black,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#EDEDED"
                    ),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, 0),
                    "CENTER",
                ),
                (
                    "ALIGN",
                    (0, 1),
                    (0, -1),
                    "CENTER",
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
                    2,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "TOPPADDING",
                    (0, 1),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 1),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    return table


# ============================================================
# SIGN-OFF
# ============================================================

def build_signoff_section():

    rows = [
        [
            Paragraph(
                "<b>Facilitator Name:</b>",
                NORMAL_STYLE,
            ),
            "",
            Paragraph(
                "<b>Signature:</b>",
                NORMAL_STYLE,
            ),
            "",
            Paragraph(
                "<b>Date:</b>",
                NORMAL_STYLE,
            ),
            "",
        ],
        [
            Paragraph(
                "<b>Comments:</b>",
                NORMAL_STYLE,
            ),
            "",
            "",
            "",
            "",
            "",
        ],
    ]

    table = Table(
        rows,
        colWidths=[
            30 * mm,
            62 * mm,
            20 * mm,
            62 * mm,
            15 * mm,
            45 * mm,
        ],
        rowHeights=[
            12 * mm,
            18 * mm,
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
                    colors.black,
                ),
                (
                    "SPAN",
                    (1, 1),
                    (5, 1),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.whitesmoke,
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

    return table


# ============================================================
# FOOTER
# ============================================================

def draw_footer(
    canvas,
    document,
):

    canvas.saveState()

    page_width, _ = PAGE_SIZE

    canvas.setFont(
        "Helvetica",
        6,
    )

    canvas.drawString(
        LEFT_MARGIN,
        5 * mm,
        (
            "Glen Moniques (Pty) Ltd - "
            "Daily Learner Attendance Register"
        ),
    )

    canvas.drawRightString(
        page_width
        - RIGHT_MARGIN,
        5 * mm,
        f"Page {document.page}",
    )

    canvas.restoreState()


# ============================================================
# GENERATE WEEKLY DAILY PACK
# ============================================================

def generate_daily_attendance_pack_pdf(
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
        pagesize=PAGE_SIZE,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title=(
            "Daily Learner "
            "Attendance Register Pack"
        ),
        author=(
            "Glen Moniques (Pty) Ltd"
        ),
    )

    story = []

    printable_days = [
        day
        for day in data[
            "days"
        ]
        if day[
            "is_training_day"
        ]
    ]

    if not printable_days:

        raise ValueError(
            "There are no training days "
            "to print for this week."
        )

    for index, day in enumerate(
        printable_days
    ):

        story.extend(
            build_page_header(
                data,
                day,
            )
        )

        story.append(
            build_attendance_table(
                data[
                    "students"
                ]
            )
        )

        story.append(
            Spacer(
                1,
                5 * mm,
            )
        )

        story.append(
            build_signoff_section()
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
                    "Each learner must personally "
                    "record their sign-in and "
                    "sign-out time and signature. "
                    "This register forms part of "
                    "the official attendance evidence."
                ),
                SMALL_STYLE,
            )
        )

        if index < (
            len(
                printable_days
            )
            - 1
        ):

            story.append(
                PageBreak()
            )

    document.build(
        story,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer,
    )

    return output_path