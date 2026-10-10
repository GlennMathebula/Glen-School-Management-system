import hashlib
import html
from datetime import (
    date,
    datetime,
    time,
    timezone,
)

from sqlalchemy import text

from app.database import engine
from app.services.email_service import (
    send_email,
)


# ============================================================
# GET FACILITATOR SESSION
# ============================================================

def get_facilitator_notification_session(
    *,
    staff_code: str,
    timetable_session_id: str,
) -> dict | None:

    query = text(
        """
        SELECT
            ts.id AS timetable_session_id,
            ts.class_id,
            ts.module_id,

            ts.session_title,
            ts.session_date,
            ts.start_time,
            ts.end_time,

            ts.delivery_mode,
            ts.venue,
            ts.meeting_link,
            ts.notes,
            ts.status,

            c.class_code,
            c.class_name,
            c.course_code,
            c.cycle_code,
            c.class_group,

            m.module_code,
            m.module_name

        FROM public.timetable_sessions ts

        JOIN public.classes c
            ON c.id = ts.class_id

        LEFT JOIN public.modules m
            ON m.id = ts.module_id

        WHERE
            ts.id = CAST(
                :timetable_session_id
                AS uuid
            )

            AND c.facilitator_code =
                :staff_code

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = connection.execute(
            query,
            {
                "staff_code": (
                    staff_code
                ),

                "timetable_session_id": (
                    timetable_session_id
                ),
            },
        ).mappings().first()

    return (
        dict(
            row
        )
        if row
        else None
    )


# ============================================================
# GET ACTIVE LEARNERS
# ============================================================

def get_session_learners(
    class_id: str,
) -> list[dict]:

    query = text(
        """
        SELECT
            r.id AS registration_id,
            r.student_number,

            a.first_name,
            a.middle_name,
            a.last_name,
            a.email

        FROM public.class_enrolments ce

        JOIN public.registrations r
            ON r.id = ce.registration_id

        JOIN public.applications a
            ON a.id = r.application_id

        WHERE
            ce.class_id = CAST(
                :class_id
                AS uuid
            )

            AND ce.status = 'Active'

        ORDER BY
            a.last_name,
            a.first_name,
            r.student_number
        """
    )

    with engine.connect() as connection:

        rows = connection.execute(
            query,
            {
                "class_id": (
                    class_id
                ),
            },
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


# ============================================================
# FORMAT HELPERS
# ============================================================

def format_session_date(
    value: date,
) -> str:

    return value.strftime(
        "%d %B %Y"
    )


def format_session_time(
    value: time,
) -> str:

    return value.strftime(
        "%H:%M"
    )


def learner_name(
    learner: dict,
) -> str:

    names = [
        learner.get(
            "first_name"
        ),

        learner.get(
            "middle_name"
        ),

        learner.get(
            "last_name"
        ),
    ]

    return " ".join(
        str(
            name
        ).strip()
        for name in names
        if name
    )


# ============================================================
# NOTIFICATION FINGERPRINT
# ============================================================

def build_notification_fingerprint(
    session: dict,
) -> str:

    raw_value = "|".join(
        [
            str(
                session.get(
                    "session_title"
                )
                or ""
            ),

            str(
                session.get(
                    "session_date"
                )
                or ""
            ),

            str(
                session.get(
                    "start_time"
                )
                or ""
            ),

            str(
                session.get(
                    "end_time"
                )
                or ""
            ),

            str(
                session.get(
                    "delivery_mode"
                )
                or ""
            ),

            str(
                session.get(
                    "venue"
                )
                or ""
            ),

            str(
                session.get(
                    "meeting_link"
                )
                or ""
            ),

            str(
                session.get(
                    "module_code"
                )
                or ""
            ),

            str(
                session.get(
                    "module_name"
                )
                or ""
            ),
        ]
    )

    return hashlib.sha256(
        raw_value.encode(
            "utf-8"
        )
    ).hexdigest()


# ============================================================
# CHECK IF ALREADY SENT
# ============================================================

def notification_already_sent(
    *,
    timetable_session_id: str,
    registration_id: str,
    fingerprint: str,
) -> bool:

    query = text(
        """
        SELECT
            id

        FROM
            public.timetable_session_email_notifications

        WHERE
            timetable_session_id = CAST(
                :timetable_session_id
                AS uuid
            )

            AND registration_id = CAST(
                :registration_id
                AS uuid
            )

            AND notification_fingerprint =
                :fingerprint

            AND status = 'Sent'

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = connection.execute(
            query,
            {
                "timetable_session_id": (
                    timetable_session_id
                ),

                "registration_id": (
                    registration_id
                ),

                "fingerprint": (
                    fingerprint
                ),
            },
        ).first()

    return row is not None


# ============================================================
# LOG NOTIFICATION
# ============================================================

def log_notification(
    *,
    timetable_session_id: str,
    registration_id: str,
    student_number: str,
    recipient_email: str | None,
    fingerprint: str,
    status: str,
    error_message: str | None = None,
):

    sent_at = (
        datetime.now(
            timezone.utc
        )
        if status == "Sent"
        else None
    )

    query = text(
        """
        INSERT INTO
            public.timetable_session_email_notifications
        (
            timetable_session_id,
            registration_id,
            student_number,
            recipient_email,
            notification_type,
            notification_fingerprint,
            status,
            sent_at,
            error_message
        )

        VALUES
        (
            CAST(
                :timetable_session_id
                AS uuid
            ),

            CAST(
                :registration_id
                AS uuid
            ),

            :student_number,
            :recipient_email,
            'CLASS_SESSION',
            :notification_fingerprint,
            :status,
            :sent_at,
            :error_message
        )
        """
    )

    with engine.begin() as connection:

        connection.execute(
            query,
            {
                "timetable_session_id": (
                    timetable_session_id
                ),

                "registration_id": (
                    registration_id
                ),

                "student_number": (
                    student_number
                ),

                "recipient_email": (
                    recipient_email
                ),

                "notification_fingerprint": (
                    fingerprint
                ),

                "status": (
                    status
                ),

                "sent_at": (
                    sent_at
                ),

                "error_message": (
                    error_message
                ),
            },
        )
# ============================================================
# BUILD EMAIL CONTENT
# ============================================================

def build_session_email(
    *,
    learner: dict,
    session: dict,
) -> tuple[
    str,
    str,
    str,
]:

    title = (
        session.get(
            "session_title"
        )
        or session.get(
            "module_name"
        )
        or session.get(
            "class_name"
        )
        or session[
            "class_code"
        ]
    )

    student_name = (
        learner_name(
            learner
        )
        or "Student"
    )

    session_date = (
        format_session_date(
            session[
                "session_date"
            ]
        )
    )

    start_time = (
        format_session_time(
            session[
                "start_time"
            ]
        )
    )

    end_time = (
        format_session_time(
            session[
                "end_time"
            ]
        )
    )

    delivery_mode = (
        session.get(
            "delivery_mode"
        )
        or "Not specified"
    )

    venue = (
        session.get(
            "venue"
        )
    )

    meeting_link = (
        session.get(
            "meeting_link"
        )
    )

    subject = (
        f"Class Session: {title} - "
        f"{session_date}"
    )

    escaped_name = html.escape(
        student_name
    )

    escaped_title = html.escape(
        str(
            title
        )
    )

    escaped_class = html.escape(
        str(
            session[
                "class_code"
            ]
        )
    )

    escaped_course = html.escape(
        str(
            session[
                "course_code"
            ]
        )
    )

    escaped_delivery = html.escape(
        str(
            delivery_mode
        )
    )

    module_line = ""

    if session.get(
        "module_code"
    ):

        module_text = (
            f"{session['module_code']} - "
            f"{session.get('module_name') or ''}"
        )

        module_line = (
            "<p><strong>Module:</strong> "
            f"{html.escape(module_text)}</p>"
        )

    venue_line = ""

    if venue:

        venue_line = (
            "<p><strong>Venue:</strong> "
            f"{html.escape(str(venue))}</p>"
        )

    meeting_section = ""

    if meeting_link:

        safe_link = html.escape(
            str(
                meeting_link
            ),
            quote=True,
        )

        meeting_section = f"""
        <p>
            <strong>Online Class Link:</strong>
        </p>

        <p>
            <a
                href="{safe_link}"
                style="
                    display:inline-block;
                    padding:12px 18px;
                    background:#1a73e8;
                    color:#ffffff;
                    text-decoration:none;
                    border-radius:6px;
                    font-weight:bold;
                "
            >
                Join Online Class
            </a>
        </p>

        <p>
            {safe_link}
        </p>
        """

    html_body = f"""
    <html>
        <body
            style="
                font-family:Arial,sans-serif;
                line-height:1.6;
                color:#222222;
            "
        >
            <p>
                Dear {escaped_name},
            </p>

            <p>
                You have a scheduled class session
                with Glen Moniques.
            </p>

            <p>
                <strong>Session:</strong>
                {escaped_title}
            </p>

            <p>
                <strong>Class:</strong>
                {escaped_class}
            </p>

            <p>
                <strong>Course:</strong>
                {escaped_course}
            </p>

            {module_line}

            <p>
                <strong>Date:</strong>
                {session_date}
            </p>

            <p>
                <strong>Time:</strong>
                {start_time} - {end_time}
            </p>

            <p>
                <strong>Delivery Mode:</strong>
                {escaped_delivery}
            </p>

            {venue_line}

            {meeting_section}

            <p>
                Please ensure that you are ready
                before the scheduled start time.
            </p>

            <p>
                Regards,<br>
                <strong>Glen Moniques</strong>
            </p>
        </body>
    </html>
    """

    text_lines = [
        f"Dear {student_name},",
        "",
        "You have a scheduled class session "
        "with Glen Moniques.",
        "",
        f"Session: {title}",
        f"Class: {session['class_code']}",
        f"Course: {session['course_code']}",
    ]

    if session.get(
        "module_code"
    ):

        text_lines.append(
            (
                f"Module: "
                f"{session['module_code']} - "
                f"{session.get('module_name') or ''}"
            )
        )

    text_lines.extend(
        [
            f"Date: {session_date}",
            (
                f"Time: "
                f"{start_time} - {end_time}"
            ),
            (
                f"Delivery Mode: "
                f"{delivery_mode}"
            ),
        ]
    )

    if venue:

        text_lines.append(
            f"Venue: {venue}"
        )

    if meeting_link:

        text_lines.extend(
            [
                "",
                (
                    "Join Online Class: "
                    f"{meeting_link}"
                ),
            ]
        )

    text_lines.extend(
        [
            "",
            (
                "Please ensure that you are "
                "ready before the scheduled "
                "start time."
            ),
            "",
            "Regards,",
            "Glen Moniques",
        ]
    )

    text_body = "\n".join(
        text_lines
    )

    return (
        subject,
        html_body,
        text_body,
    )


# ============================================================
# NOTIFY LEARNERS
# ============================================================

def notify_learners_about_session(
    *,
    staff_code: str,
    timetable_session_id: str,
    force_resend: bool = False,
) -> dict:

    session = (
        get_facilitator_notification_session(
            staff_code=(
                staff_code
            ),
            timetable_session_id=(
                timetable_session_id
            ),
        )
    )

    if not session:

        raise ValueError(
            "Timetable session not found "
            "or not assigned to this facilitator."
        )

    if (
        session[
            "status"
        ]
        != "Published"
    ):

        raise ValueError(
            "Learners can only be notified "
            "about Published timetable sessions."
        )

    delivery_mode = (
        session.get(
            "delivery_mode"
        )
        or ""
    ).strip().lower()

    if (
        delivery_mode
        in {
            "online",
            "hybrid",
            "blended",
        }
        and not session.get(
            "meeting_link"
        )
    ):

        raise ValueError(
            "Online or blended session does "
            "not have a meeting link yet."
        )

    learners = (
        get_session_learners(
            str(
                session[
                    "class_id"
                ]
            )
        )
    )

    fingerprint = (
        build_notification_fingerprint(
            session
        )
    )

    sent = 0
    skipped = 0
    failed = 0
    missing_email = 0

    results = []

    for learner in learners:

        registration_id = str(
            learner[
                "registration_id"
            ]
        )

        student_number = str(
            learner[
                "student_number"
            ]
        )

        recipient_email = (
            learner.get(
                "email"
            )
            or ""
        ).strip()

        if not recipient_email:

            missing_email += 1

            log_notification(
                timetable_session_id=(
                    timetable_session_id
                ),
                registration_id=(
                    registration_id
                ),
                student_number=(
                    student_number
                ),
                recipient_email=None,
                fingerprint=(
                    fingerprint
                ),
                status="Skipped",
                error_message=(
                    "Learner does not have "
                    "an email address."
                ),
            )

            results.append(
                {
                    "student_number": (
                        student_number
                    ),
                    "status": (
                        "Skipped"
                    ),
                    "reason": (
                        "Missing email address."
                    ),
                }
            )

            continue

        if (
            not force_resend
            and notification_already_sent(
                timetable_session_id=(
                    timetable_session_id
                ),
                registration_id=(
                    registration_id
                ),
                fingerprint=(
                    fingerprint
                ),
            )
        ):

            skipped += 1

            results.append(
                {
                    "student_number": (
                        student_number
                    ),
                    "email": (
                        recipient_email
                    ),
                    "status": (
                        "Skipped"
                    ),
                    "reason": (
                        "Already notified about "
                        "this version of the session."
                    ),
                }
            )

            continue

        (
            subject,
            html_body,
            text_body,
        ) = build_session_email(
            learner=(
                learner
            ),
            session=(
                session
            ),
        )

        try:

            send_email(
                recipient_email=(
                    recipient_email
                ),
                subject=(
                    subject
                ),
                html_body=(
                    html_body
                ),
                text_body=(
                    text_body
                ),
            )

            sent += 1

            log_notification(
                timetable_session_id=(
                    timetable_session_id
                ),
                registration_id=(
                    registration_id
                ),
                student_number=(
                    student_number
                ),
                recipient_email=(
                    recipient_email
                ),
                fingerprint=(
                    fingerprint
                ),
                status="Sent",
            )

            results.append(
                {
                    "student_number": (
                        student_number
                    ),
                    "email": (
                        recipient_email
                    ),
                    "status": (
                        "Sent"
                    ),
                }
            )

        except Exception as error:

            failed += 1

            log_notification(
                timetable_session_id=(
                    timetable_session_id
                ),
                registration_id=(
                    registration_id
                ),
                student_number=(
                    student_number
                ),
                recipient_email=(
                    recipient_email
                ),
                fingerprint=(
                    fingerprint
                ),
                status="Failed",
                error_message=str(
                    error
                )[:2000],
            )

            results.append(
                {
                    "student_number": (
                        student_number
                    ),
                    "email": (
                        recipient_email
                    ),
                    "status": (
                        "Failed"
                    ),
                    "reason": (
                        "Email could not be sent."
                    ),
                }
            )

    return {
        "timetable_session_id": (
            timetable_session_id
        ),

        "class_code": (
            session[
                "class_code"
            ]
        ),

        "session_title": (
            session.get(
                "session_title"
            )
        ),

        "total_learners": (
            len(
                learners
            )
        ),

        "sent": (
            sent
        ),

        "skipped": (
            skipped
        ),

        "missing_email": (
            missing_email
        ),

        "failed": (
            failed
        ),

        "force_resend": (
            force_resend
        ),

        "results": (
            results
        ),
    }