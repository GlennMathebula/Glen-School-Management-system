from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.services.student_card_asset_service import (
    generate_identity_barcode,
    generate_student_card_qr,
    get_avatar_file_path,
)

# ============================================================
# PORTRAIT CR80 / ID-1 CARD
# ============================================================

CARD_WIDTH = 53.98 * mm
CARD_HEIGHT = 85.60 * mm


# ============================================================
# GLEN MONIQUES BRAND
# ============================================================

NAVY = colors.HexColor(
    "#0D1B2A"
)

DARK_NAVY = colors.HexColor(
    "#07121F"
)

GOLD = colors.HexColor(
    "#D4AF37"
)

LIGHT_GOLD = colors.HexColor(
    "#F3E5A3"
)

WHITE = colors.white

LIGHT_GREY = colors.HexColor(
    "#F3F5F7"
)

MID_GREY = colors.HexColor(
    "#939DA8"
)

TEXT_GREY = colors.HexColor(
    "#59636E"
)

GREEN = colors.HexColor(
    "#1F7A4D"
)

RED = colors.HexColor(
    "#A63D40"
)


# ============================================================
# HELPERS
# ============================================================

def clean_text(
    value,
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


def format_expiry_date(
    value,
) -> str:

    if not value:
        return ""

    if hasattr(
        value,
        "strftime",
    ):
        return value.strftime(
            "%d %b %Y"
        ).upper()

    return str(
        value
    )


def fit_text(
    pdf: canvas.Canvas,
    text: str,
    font_name: str,
    max_font_size: float,
    min_font_size: float,
    max_width: float,
) -> float:

    font_size = max_font_size

    while (
        font_size > min_font_size
        and pdf.stringWidth(
            text,
            font_name,
            font_size,
        ) > max_width
    ):

        font_size -= 0.2

    return font_size


def draw_wrapped_text(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    font_name: str = "Helvetica-Bold",
    font_size: float = 4.5,
    line_height: float = 5.4,
    max_lines: int = 3,
) -> float:

    words = clean_text(
        text
    ).split()

    lines = []

    current_line = ""

    for word in words:

        candidate = (
            f"{current_line} {word}".strip()
        )

        width = pdf.stringWidth(
            candidate,
            font_name,
            font_size,
        )

        if width <= max_width:

            current_line = candidate

        else:

            if current_line:

                lines.append(
                    current_line
                )

            current_line = word

        if len(
            lines
        ) >= max_lines:

            break

    if (
        current_line
        and len(
            lines
        ) < max_lines
    ):

        lines.append(
            current_line
        )

    pdf.setFont(
        font_name,
        font_size,
    )

    for index, line in enumerate(
        lines
    ):

        pdf.drawString(
            x,
            y
            - (
                index
                * line_height
            ),
            line,
        )

    return (
        y
        - (
            len(
                lines
            )
            * line_height
        )
    )


# ============================================================
# FIND GLEN MONIQUES LOGO
# ============================================================

def find_glen_moniques_logo() -> Path | None:

    assets_directory = (
        Path(__file__)
        .resolve()
        .parents[1]
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
        "Glen Moniques.png",
        "Glen Moniques.jpg",
        "Glen Moniques.jpeg",
    ]

    for filename in possible_names:

        candidate = (
            assets_directory
            / filename
        )

        if candidate.exists():

            return candidate

    return None


# ============================================================
# LOGO WATERMARK
# ============================================================

def draw_logo_watermark(
    pdf: canvas.Canvas,
) -> None:

    logo_path = (
        find_glen_moniques_logo()
    )

    if not logo_path:

        print(
            "WARNING: Glen Moniques logo "
            "not found for student card watermark."
        )

        return

    watermark_width = (
        31 * mm
    )

    watermark_height = (
        31 * mm
    )

    watermark_x = (
        17 * mm
    )

    watermark_y = (
        29 * mm
    )

    pdf.saveState()

    try:

        pdf.setFillAlpha(
            0.075
        )

        pdf.setStrokeAlpha(
            0.075
        )

    except Exception:

        pass

    pdf.drawImage(
        str(
            logo_path
        ),
        watermark_x,
        watermark_y,
        width=watermark_width,
        height=watermark_height,
        preserveAspectRatio=True,
        anchor="c",
        mask="auto",
    )

    pdf.restoreState()


# ============================================================
# AVATAR PLACEHOLDER
# ============================================================

def draw_avatar_placeholder(
    pdf: canvas.Canvas,
    center_x: float,
    center_y: float,
    radius: float,
) -> None:

    pdf.setFillColor(
        LIGHT_GREY
    )

    pdf.circle(
        center_x,
        center_y,
        radius,
        fill=1,
        stroke=0,
    )

    pdf.setFillColor(
        MID_GREY
    )

    pdf.circle(
        center_x,
        center_y + radius * 0.22,
        radius * 0.26,
        fill=1,
        stroke=0,
    )

    pdf.roundRect(
        center_x - radius * 0.42,
        center_y - radius * 0.43,
        radius * 0.84,
        radius * 0.48,
        radius * 0.18,
        fill=1,
        stroke=0,
    )


# ============================================================
# AVATAR IMAGE
# ============================================================

def draw_avatar(
    pdf: canvas.Canvas,
    data: dict,
) -> None:

    center_x = (
        31.5 * mm
    )

    center_y = (
        58.5 * mm
    )

    outer_radius = (
        14.2 * mm
    )

    inner_radius = (
        12.4 * mm
    )

    pdf.setFillColor(
        GOLD
    )

    pdf.circle(
        center_x,
        center_y,
        outer_radius,
        fill=1,
        stroke=0,
    )

    avatar_path = (
        get_avatar_file_path(
            data[
                "avatar"
            ].get(
                "path"
            )
        )
    )

    if not avatar_path:

        draw_avatar_placeholder(
            pdf,
            center_x,
            center_y,
            inner_radius,
        )

        return

    avatar_size = (
        inner_radius
        * 2
    )

    pdf.saveState()

    path = pdf.beginPath()

    path.circle(
        center_x,
        center_y,
        inner_radius,
    )

    pdf.clipPath(
        path,
        stroke=0,
        fill=0,
    )

    pdf.drawImage(
        str(
            avatar_path
        ),
        center_x - inner_radius,
        center_y - inner_radius,
        width=avatar_size,
        height=avatar_size,
        preserveAspectRatio=False,
        mask="auto",
    )

    pdf.restoreState()


# ============================================================
# LEFT VERTICAL BRAND STRIP
# ============================================================

def draw_brand_strip(
    pdf: canvas.Canvas,
) -> None:

    strip_width = (
        10.5 * mm
    )

    pdf.setFillColor(
        NAVY
    )

    pdf.rect(
        0,
        0,
        strip_width,
        CARD_HEIGHT,
        fill=1,
        stroke=0,
    )

    pdf.setFillColor(
        GOLD
    )

    pdf.rect(
        0,
        CARD_HEIGHT - 4 * mm,
        strip_width,
        4 * mm,
        fill=1,
        stroke=0,
    )

    pdf.saveState()

    pdf.translate(
        6.8 * mm,
        8 * mm,
    )

    pdf.rotate(
        90
    )

    pdf.setFillColor(
        WHITE
    )

    pdf.setFont(
        "Helvetica-Bold",
        10,
    )

    pdf.drawString(
        0,
        0,
        "STUDENT",
    )

    pdf.restoreState()


# ============================================================
# HEADER
# ============================================================

def draw_header(
    pdf: canvas.Canvas,
) -> None:

    pdf.setFillColor(
        NAVY
    )

    pdf.setFont(
        "Helvetica-Bold",
        6.6,
    )

    pdf.drawCentredString(
        32 * mm,
        CARD_HEIGHT - 6.6 * mm,
        "GLEN MONIQUES",
    )

    pdf.setFillColor(
        TEXT_GREY
    )

    pdf.setFont(
        "Helvetica",
        3.7,
    )

    pdf.drawCentredString(
        32 * mm,
        CARD_HEIGHT - 9.2 * mm,
        "HI TIRHELA N'WINA",
    )

    pdf.setStrokeColor(
        GOLD
    )

    pdf.setLineWidth(
        0.8
    )

    pdf.line(
        14 * mm,
        CARD_HEIGHT - 11.5 * mm,
        CARD_WIDTH - 3 * mm,
        CARD_HEIGHT - 11.5 * mm,
    )


# ============================================================
# DETAILS
# ============================================================

def draw_student_details(
    pdf: canvas.Canvas,
    data: dict,
) -> None:

    content_left = (
        13.3 * mm
    )

    content_right = (
        CARD_WIDTH
        - 3 * mm
    )

    content_width = (
        content_right
        - content_left
    )

    # --------------------------------------------------------
    # NAME
    # --------------------------------------------------------

    name = clean_text(
        data[
            "full_name"
        ]
    ).upper()

    name_y = (
        40.5 * mm
    )

    name_size = fit_text(
        pdf,
        name,
        "Helvetica-Bold",
        7.2,
        4.8,
        content_width,
    )

    pdf.setFillColor(
        NAVY
    )

    pdf.setFont(
        "Helvetica-Bold",
        name_size,
    )

    pdf.drawCentredString(
        (
            content_left
            + content_right
        )
        / 2,
        name_y,
        name,
    )

    # --------------------------------------------------------
    # STUDENT NUMBER
    # --------------------------------------------------------

    pdf.setFillColor(
        TEXT_GREY
    )

    pdf.setFont(
        "Helvetica-Bold",
        3.3,
    )

    pdf.drawCentredString(
        (
            content_left
            + content_right
        )
        / 2,
        36.8 * mm,
        "STUDENT NUMBER",
    )

    pdf.setFillColor(
        NAVY
    )

    pdf.setFont(
        "Helvetica-Bold",
        6.4,
    )

    pdf.drawCentredString(
        (
            content_left
            + content_right
        )
        / 2,
        33.8 * mm,
        clean_text(
            data[
                "student_number"
            ]
        ),
    )

    # --------------------------------------------------------
    # COURSE
    # --------------------------------------------------------

    pdf.setFillColor(
        TEXT_GREY
    )

    pdf.setFont(
        "Helvetica-Bold",
        3.3,
    )

    pdf.drawString(
        content_left,
        29.7 * mm,
        "COURSE",
    )

    pdf.setFillColor(
        NAVY
    )

    course_name = clean_text(
        data[
            "course"
        ][
            "course_name"
        ]
    )

    draw_wrapped_text(
        pdf=pdf,
        text=course_name,
        x=content_left,
        y=27.2 * mm,
        max_width=content_width,
        font_name="Helvetica-Bold",
        font_size=4.2,
        line_height=4.8,
        max_lines=3,
    )

    # --------------------------------------------------------
    # EXPIRY
    # --------------------------------------------------------

    pdf.setFillColor(
        TEXT_GREY
    )

    pdf.setFont(
        "Helvetica-Bold",
        3.3,
    )

    pdf.drawString(
        content_left,
        18.5 * mm,
        "EXPIRY DATE",
    )

    pdf.setFillColor(
        NAVY
    )

    pdf.setFont(
        "Helvetica-Bold",
        5,
    )

    pdf.drawString(
        content_left,
        15.7 * mm,
        format_expiry_date(
            data[
                "card"
            ][
                "expiry_date"
            ]
        ),
    )


# ============================================================
# BOTTOM SECURITY AREA
# ============================================================

def draw_security_area(
    pdf: canvas.Canvas,
    data: dict,
) -> None:

    # --------------------------------------------------------
    # BARCODE
    # --------------------------------------------------------

    barcode_buffer = (
        generate_identity_barcode(
            data[
                "identity_barcode_value"
            ]
        )
    )

    barcode_x = (
        13.2 * mm
    )

    barcode_y = (
        5.3 * mm
    )

    barcode_width = (
        24.5 * mm
    )

    barcode_height = (
        6.4 * mm
    )

    pdf.drawImage(
        ImageReader(
            barcode_buffer
        ),
        barcode_x,
        barcode_y,
        width=barcode_width,
        height=barcode_height,
        preserveAspectRatio=False,
        mask="auto",
    )

    pdf.setFillColor(
        TEXT_GREY
    )

    pdf.setFont(
        "Helvetica-Bold",
        2.8,
    )

    pdf.drawCentredString(
        barcode_x
        + barcode_width / 2,
        3.8 * mm,
        (
            f"{clean_text(data['identity_type']).upper()} BARCODE"
        ),
    )

    # --------------------------------------------------------
    # QR CODE
    # --------------------------------------------------------

    qr_buffer = (
        generate_student_card_qr(
            data[
                "verification"
            ][
                "url"
            ]
        )
    )

    qr_size = (
        10.8 * mm
    )

    qr_x = (
        CARD_WIDTH
        - qr_size
        - 2.7 * mm
    )

    qr_y = (
        4.2 * mm
    )

    pdf.drawImage(
        ImageReader(
            qr_buffer
        ),
        qr_x,
        qr_y,
        width=qr_size,
        height=qr_size,
        mask="auto",
    )

    pdf.setFillColor(
        TEXT_GREY
    )

    pdf.setFont(
        "Helvetica-Bold",
        2.5,
    )

    pdf.drawCentredString(
        qr_x
        + qr_size / 2,
        2.9 * mm,
        "SCAN TO VERIFY",
    )


# ============================================================
# STATUS
# ============================================================

def draw_status(
    pdf: canvas.Canvas,
    data: dict,
) -> None:

    status = (
        clean_text(
            data[
                "card"
            ][
                "card_status"
            ],
            "UNKNOWN",
        )
        .upper()
    )

    status_colour = (
        GREEN
        if status == "ACTIVE"
        else RED
    )

    width = (
        11 * mm
    )

    height = (
        3.8 * mm
    )

    x = (
        CARD_WIDTH
        - width
        - 2.5 * mm
    )

    y = (
        CARD_HEIGHT
        - 16.6 * mm
    )

    pdf.setFillColor(
        status_colour
    )

    pdf.roundRect(
        x,
        y,
        width,
        height,
        1.5 * mm,
        fill=1,
        stroke=0,
    )

    pdf.setFillColor(
        WHITE
    )

    pdf.setFont(
        "Helvetica-Bold",
        3.2,
    )

    pdf.drawCentredString(
        x
        + width / 2,
        y
        + 1.25 * mm,
        status,
    )


# ============================================================
# DRAW CARD
# ============================================================

def draw_student_card(
    pdf: canvas.Canvas,
    data: dict,
) -> None:

    # --------------------------------------------------------
    # WHITE BACKGROUND
    # --------------------------------------------------------

    pdf.setFillColor(
        WHITE
    )

    pdf.rect(
        0,
        0,
        CARD_WIDTH,
        CARD_HEIGHT,
        fill=1,
        stroke=0,
    )

    # --------------------------------------------------------
    # SUBTLE DECORATIVE BACKGROUND
    # --------------------------------------------------------

    pdf.setFillColor(
        colors.HexColor(
            "#FAFAFA"
        )
    )

    path = pdf.beginPath()

    path.moveTo(
        10.5 * mm,
        48 * mm,
    )

    path.lineTo(
        CARD_WIDTH,
        70 * mm,
    )

    path.lineTo(
        CARD_WIDTH,
        45 * mm,
    )

    path.lineTo(
        10.5 * mm,
        30 * mm,
    )

    path.close()

    pdf.drawPath(
        path,
        fill=1,
        stroke=0,
    )

    # --------------------------------------------------------
    # GLEN MONIQUES WATERMARK
    # --------------------------------------------------------

    draw_logo_watermark(
        pdf
    )

    # --------------------------------------------------------
    # BRAND STRIP
    # --------------------------------------------------------

    draw_brand_strip(
        pdf
    )

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    draw_header(
        pdf
    )

    # --------------------------------------------------------
    # AVATAR
    # --------------------------------------------------------

    draw_avatar(
        pdf,
        data,
    )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    draw_status(
        pdf,
        data,
    )

    # --------------------------------------------------------
    # DETAILS
    # --------------------------------------------------------

    draw_student_details(
        pdf,
        data,
    )

    # --------------------------------------------------------
    # SECURITY AREA
    # --------------------------------------------------------

    draw_security_area(
        pdf,
        data,
    )


# ============================================================
# GENERATE PDF
# ============================================================

def generate_student_card_pdf(
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

    pdf = canvas.Canvas(
        str(
            output_path
        ),
        pagesize=(
            CARD_WIDTH,
            CARD_HEIGHT,
        ),
    )

    pdf.setTitle(
        
            "Glen Moniques Student Card - "
            f"{data['student_number']}"
        
    )

    pdf.setAuthor(
        "Glen Moniques (Pty) Ltd"
    )

    draw_student_card(
        pdf,
        data,
    )

    pdf.showPage()

    pdf.save()

    return output_path