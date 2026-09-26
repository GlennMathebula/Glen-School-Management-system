from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import (
    TA_CENTER,
    TA_LEFT,
)
from reportlab.lib.pagesizes import (
    A3,
    landscape,
)
from reportlab.lib.styles import (
    ParagraphStyle,
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
# PAGE SETTINGS
# ============================================================

PAGE_SIZE = landscape(A3)

LEFT_MARGIN = 7 * mm
RIGHT_MARGIN = 7 * mm
TOP_MARGIN = 7 * mm
BOTTOM_MARGIN = 10 * mm


# ============================================================
# STYLES
# ============================================================

TITLE_STYLE = ParagraphStyle(
    "AttendanceTitle",
    fontName="Helvetica-Bold",
    fontSize=13,
    leading=15,
    alignment=TA_CENTER,
)

SUBTITLE_STYLE = ParagraphStyle(
    "AttendanceSubtitle",
    fontName="Helvetica-Bold",
    fontSize=9,
    leading=11,
    alignment=TA_CENTER,
)

NORMAL_STYLE = ParagraphStyle(
    "AttendanceNormal",
    fontName="Helvetica",
    fontSize=7,
    leading=9,
    alignment=TA_LEFT,
)

SMALL_STYLE = ParagraphStyle(
    "AttendanceSmall",
    fontName="Helvetica",
    fontSize=6,
    leading=7,
    alignment=TA_LEFT,
)

SMALL_CENTER_STYLE = ParagraphStyle(
    "AttendanceSmallCenter",
    fontName="Helvetica",
    fontSize=6,
    leading=7,
    alignment=TA_CENTER,
)

TABLE_HEADER_STYLE = ParagraphStyle(
    "AttendanceTableHeader",
    fontName="Helvetica-Bold",
    fontSize=5.5,
    leading=6.5,
    alignment=TA_CENTER,
)

STUDENT_STYLE = ParagraphStyle(
    "AttendanceStudent",
    fontName="Helvetica",
    fontSize=6.3,
    leading=7.5,
    alignment=TA_LEFT,
)

TIME_STYLE = ParagraphStyle(
    "AttendanceTime",
    fontName="Helvetica",
    fontSize=5.5,
    leading=6,
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
    ]

    for name in possible_names:

        candidate = (
            assets_directory
            / name
        )

        if candidate.exists():
            return candidate

    return None


def full_name(
    student: dict,
) -> str:

    names = [
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
        name
        for name in names
        if name
    )


def identity_number(
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

    if alternate_id:
        return alternate_id

    return ""


# ============================================================
# SIGNATURE CELL
# ============================================================

def build_signature_cell(
    label: str,
):

    content = [
        [
            Paragraph(
                f"<b>{label}</b>",
                SMALL_CENTER_STYLE,
            )
        ],
        [
            ""
        ],
        [
            Paragraph(
                "Time: __________________",
                TIME_STYLE,
            )
        ],
    ]

    table = Table(
        content,
        colWidths=[
            26 * mm,
        ],
        rowHeights=[
            5 * mm,
            10 * mm,
            5 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.black,
                ),
                (
                    "LINEABOVE",
                    (0, 2),
                    (-1, 2),
                    0.25,
                    colors.grey,
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
                    (0, 0),
                    (-1, -1),
                    1,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    1,
                ),
            ]
        )
    )

    return table


# ============================================================
# HEADER
# ============================================================

def build_header(
    data: dict,
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
            "WEEKLY LEARNER ATTENDANCE REGISTER",
            SUBTITLE_STYLE,
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

    week = data[
        "week"
    ]

    information = [
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
                "<b>Class:</b>",
                NORMAL_STYLE,
            ),
            Paragraph(
                (
                    f"{clean_text(class_data.get('class_code'))}"
                    f" - "
                    f"{clean_text(class_data.get('class_name'))}"
                ),
                NORMAL_STYLE,
            ),
            Paragraph(
                "<b>Class Group:</b>",
                NORMAL_STYLE,
            ),
            Paragraph(
                clean_text(
                    class_data.get(
                        "class_group"
                    ),
                    "N/A",
                ),
                NORMAL_STYLE,
            ),
            Paragraph(
                "<b>Credits:</b>",
                NORMAL_STYLE,
            ),
            Paragraph(
                clean_text(
                    programme.get(
                        "credits"
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
                    data.get(
                        "modules_text"
                    ),
                    "Not specified",
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
            Paragraph(
                "<b>Assessor:</b>",
                NORMAL_STYLE,
            ),
            Paragraph(
                clean_text(
                    class_data.get(
                        "assessor_code"
                    ),
                    "Not assigned",
                ),
                NORMAL_STYLE,
            ),
        ],
        [
            Paragraph(
                "<b>Week:</b>",
                NORMAL_STYLE,
            ),
            Paragraph(
                (
                    f"{format_date(week['start_date'])}"
                    f" - "
                    f"{format_date(week['end_date'])}"
                ),
                NORMAL_STYLE,
            ),
            Paragraph(
                "<b>Venue:</b>",
                NORMAL_STYLE,
            ),
            Paragraph(
                clean_text(
                    data.get(
                        "venue"
                    ),
                    "As per timetable",
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
            24 * mm,
            82 * mm,
            27 * mm,
            72 * mm,
            23 * mm,
            45 * mm,
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
# WEEKLY REGISTER TABLE
# ============================================================

def build_register_table(
    data: dict,
):

    week_days = data[
        "week_days"
    ]

    students = data[
        "students"
    ]

    first_header = [
        "",
        "",
        "",
        "",
    ]

    for day in week_days:

        day_name = (
            day[
                "date"
            ]
            .strftime(
                "%A"
            )
            .upper()
        )

        date_text = (
            day[
                "date"
            ]
            .strftime(
                "%d/%m/%Y"
            )
        )

        if day[
            "is_training_day"
        ]:

            title = (
                f"{day_name}<br/>"
                f"{date_text}"
            )

        else:

            title = (
                f"{day_name}<br/>"
                f"{date_text}<br/>"
                f"{clean_text(day.get('description'), 'NO TRAINING')}"
            )

        first_header.extend(
            [
                Paragraph(
                    title,
                    TABLE_HEADER_STYLE,
                ),
                "",
            ]
        )

    second_header = [
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
    ]

    for day in week_days:

        if day[
            "is_training_day"
        ]:

            second_header.extend(
                [
                    Paragraph(
                        "Sign-in",
                        TABLE_HEADER_STYLE,
                    ),
                    Paragraph(
                        "Sign-out",
                        TABLE_HEADER_STYLE,
                    ),
                ]
            )

        else:

            second_header.extend(
                [
                    Paragraph(
                        "NO TRAINING",
                        TABLE_HEADER_STYLE,
                    ),
                    "",
                ]
            )

    table_data = [
        first_header,
        second_header,
    ]

    for index, student in enumerate(
        students,
        start=1,
    ):

        row = [
            Paragraph(
                str(index),
                SMALL_CENTER_STYLE,
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
                identity_number(
                    student
                ),
                STUDENT_STYLE,
            ),

            Paragraph(
                full_name(
                    student
                ),
                STUDENT_STYLE,
            ),
        ]

        for day in week_days:

            if day[
                "is_training_day"
            ]:

                row.extend(
                    [
                        build_signature_cell(
                            "Signature"
                        ),

                        build_signature_cell(
                            "Signature"
                        ),
                    ]
                )

            else:

                description = clean_text(
                    day.get(
                        "description"
                    ),
                    "NO TRAINING",
                )

                row.extend(
                    [
                        Paragraph(
                            description,
                            SMALL_CENTER_STYLE,
                        ),
                        "",
                    ]
                )

        table_data.append(
            row
        )

    # ========================================================
    # WIDTHS
    #
    # Total is kept below printable A3 landscape width.
    # ========================================================

    column_widths = [
        8 * mm,
        24 * mm,
        31 * mm,
        40 * mm,
    ]

    for _day in week_days:

        column_widths.extend(
            [
                28 * mm,
                28 * mm,
            ]
        )

    table = Table(
        table_data,
        colWidths=column_widths,
        repeatRows=2,
    )

    style_commands = [
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.4,
            colors.black,
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE",
        ),
        (
            "ALIGN",
            (0, 0),
            (-1, 1),
            "CENTER",
        ),
        (
            "BACKGROUND",
            (0, 0),
            (-1, 1),
            colors.HexColor(
                "#EDEDED"
            ),
        ),
        (
            "FONTNAME",
            (0, 0),
            (-1, 1),
            "Helvetica-Bold",
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            1.5,
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            1.5,
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            2,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            2,
        ),

        # Fixed learner columns span both header rows
        (
            "SPAN",
            (0, 0),
            (0, 1),
        ),
        (
            "SPAN",
            (1, 0),
            (1, 1),
        ),
        (
            "SPAN",
            (2, 0),
            (2, 1),
        ),
        (
            "SPAN",
            (3, 0),
            (3, 1),
        ),
    ]

    start_column = 4

    for day_index, day in enumerate(
        week_days
    ):

        first_column = (
            start_column
            + (
                day_index
                * 2
            )
        )

        last_column = (
            first_column
            + 1
        )

        style_commands.append(
            (
                "SPAN",
                (
                    first_column,
                    0,
                ),
                (
                    last_column,
                    0,
                ),
            )
        )

        if not day[
            "is_training_day"
        ]:

            style_commands.append(
                (
                    "SPAN",
                    (
                        first_column,
                        1,
                    ),
                    (
                        last_column,
                        1,
                    ),
                )
            )

            style_commands.append(
                (
                    "BACKGROUND",
                    (
                        first_column,
                        0,
                    ),
                    (
                        last_column,
                        -1,
                    ),
                    colors.HexColor(
                        "#F2F2F2"
                    ),
                )
            )

            for learner_row in range(
                2,
                len(
                    table_data
                ),
            ):

                style_commands.append(
                    (
                        "SPAN",
                        (
                            first_column,
                            learner_row,
                        ),
                        (
                            last_column,
                            learner_row,
                        ),
                    )
                )

    table.setStyle(
        TableStyle(
            style_commands
        )
    )

    return table


# ============================================================
# VERIFICATION SECTION
# ============================================================

def build_verification_section():

    rows = [
        [
            Paragraph(
                "<b>Facilitator Name:</b>",
                NORMAL_STYLE,
            ),
            "",
            Paragraph(
                "<b>Facilitator Signature:</b>",
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
                "<b>Admin Verification:</b>",
                NORMAL_STYLE,
            ),
            "",
            Paragraph(
                "<b>Admin Signature:</b>",
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
            31 * mm,
            72 * mm,
            35 * mm,
            72 * mm,
            16 * mm,
            42 * mm,
        ],
        rowHeights=[
            12 * mm,
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
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "SPAN",
                    (1, 2),
                    (5, 2),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
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
            ]
        )
    )

    return table


# ============================================================
# FOOTER
# ============================================================

def draw_page_footer(
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
            "Weekly Learner Attendance Register"
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
# GENERATE PDF
# ============================================================

def generate_attendance_register_pdf(
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
            "Weekly Learner "
            "Attendance Register"
        ),
        author=(
            "Glen Moniques (Pty) Ltd"
        ),
    )

    story = []

    story.extend(
        build_header(
            data
        )
    )

    story.append(
        build_register_table(
            data
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        build_verification_section()
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
                "Attendance must be completed "
                "in ink and signed by each learner. "
                "The learner must record the time "
                "of arrival below the sign-in signature "
                "and the time of departure below the "
                "sign-out signature. Corrections must "
                "remain auditable."
            ),
            SMALL_STYLE,
        )
    )

    document.build(
        story,
        onFirstPage=draw_page_footer,
        onLaterPages=draw_page_footer,
    )

    return output_path