import time
from datetime import datetime
from uuid import uuid4

from googleapiclient.discovery import build
from sqlalchemy import text

from app.database import engine
from app.services.google_calendar_service import (
    get_google_calendar_credentials,
)


# ============================================================
# SETTINGS
# ============================================================

GOOGLE_CALENDAR_TIMEZONE = (
    "Africa/Johannesburg"
)

ONLINE_DELIVERY_MODES = {
    "online",
    "hybrid",
    "blended",
}


# ============================================================
# GET FACILITATOR TIMETABLE SESSION
# ============================================================

def get_facilitator_calendar_session(
    *,
    staff_code: str,
    timetable_session_id: str,
) -> dict | None:

    query = text(
        """
        SELECT
            ts.id AS timetable_session_id,
            ts.session_title,
            ts.session_date,
            ts.start_time,
            ts.end_time,
            ts.delivery_mode,
            ts.venue,
            ts.meeting_link,
            ts.notes,
            ts.status,

            ts.google_calendar_event_id,
            ts.google_calendar_sync_status,
            ts.google_calendar_synced_at,

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

            AND (
                c.facilitator_code = :staff_code
                OR c.assessor_code = :staff_code
            )

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
# DELIVERY MODE CHECK
# ============================================================

def requires_google_meet(
    session: dict,
) -> bool:

    delivery_mode = (
        session.get(
            "delivery_mode"
        )
        or ""
    )

    return (
        delivery_mode
        .strip()
        .lower()
        in ONLINE_DELIVERY_MODES
    )


# ============================================================
# BUILD GOOGLE EVENT
# ============================================================

def build_google_event_body(
    session: dict,
) -> dict:

    start_datetime = datetime.combine(
        session[
            "session_date"
        ],
        session[
            "start_time"
        ],
    )

    end_datetime = datetime.combine(
        session[
            "session_date"
        ],
        session[
            "end_time"
        ],
    )

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

    description_lines = [
        "Glen Moniques School Management System",
        "",
        (
            f"Class: "
            f"{session['class_code']}"
        ),
        (
            f"Course: "
            f"{session['course_code']}"
        ),
    ]

    if session.get(
        "module_code"
    ):

        description_lines.append(
            (
                f"Module: "
                f"{session['module_code']} - "
                f"{session.get('module_name') or ''}"
            ).strip()
        )

    if session.get(
        "class_group"
    ):

        description_lines.append(
            (
                f"Class Group: "
                f"{session['class_group']}"
            )
        )

    if session.get(
        "delivery_mode"
    ):

        description_lines.append(
            (
                f"Delivery Mode: "
                f"{session['delivery_mode']}"
            )
        )

    if session.get(
        "meeting_link"
    ):

        description_lines.extend(
            [
                "",
                (
                    "Online Meeting: "
                    f"{session['meeting_link']}"
                ),
            ]
        )

    if session.get(
        "notes"
    ):

        description_lines.extend(
            [
                "",
                "Session Notes:",
                session[
                    "notes"
                ],
            ]
        )

    event_body = {
        "summary": (
            title
        ),

        "description": (
            "\n".join(
                description_lines
            )
        ),

        "start": {
            "dateTime": (
                start_datetime.isoformat()
            ),
            "timeZone": (
                GOOGLE_CALENDAR_TIMEZONE
            ),
        },

        "end": {
            "dateTime": (
                end_datetime.isoformat()
            ),
            "timeZone": (
                GOOGLE_CALENDAR_TIMEZONE
            ),
        },
    }

    if session.get(
        "venue"
    ):

        event_body[
            "location"
        ] = session[
            "venue"
        ]

    # ========================================================
    # REQUEST GOOGLE MEET
    # ========================================================

    if (
        requires_google_meet(
            session
        )
        and not session.get(
            "meeting_link"
        )
    ):

        event_body[
            "conferenceData"
        ] = {
            "createRequest": {
                "requestId": (
                    str(
                        uuid4()
                    )
                ),
                "conferenceSolutionKey": {
                    "type": (
                        "hangoutsMeet"
                    )
                },
            }
        }

    return event_body


# ============================================================
# EXTRACT GOOGLE MEET LINK
# ============================================================

def extract_google_meet_link(
    event: dict,
) -> str | None:

    hangout_link = event.get(
        "hangoutLink"
    )

    if hangout_link:

        return str(
            hangout_link
        )

    conference_data = (
        event.get(
            "conferenceData"
        )
        or {}
    )

    entry_points = (
        conference_data.get(
            "entryPoints"
        )
        or []
    )

    for entry in entry_points:

        if (
            entry.get(
                "entryPointType"
            )
            == "video"
        ):

            uri = entry.get(
                "uri"
            )

            if uri:

                return str(
                    uri
                )

    return None


# ============================================================
# WAIT BRIEFLY FOR GOOGLE MEET CREATION
# ============================================================

def wait_for_google_meet_link(
    *,
    calendar_service,
    event_id: str,
) -> tuple[dict, str | None]:

    latest_event = (
        calendar_service
        .events()
        .get(
            calendarId="primary",
            eventId=(
                event_id
            ),
        )
        .execute()
    )

    meet_link = (
        extract_google_meet_link(
            latest_event
        )
    )

    if meet_link:

        return (
            latest_event,
            meet_link,
        )

    for _ in range(
        5
    ):

        time.sleep(
            1
        )

        latest_event = (
            calendar_service
            .events()
            .get(
                calendarId="primary",
                eventId=(
                    event_id
                ),
            )
            .execute()
        )

        meet_link = (
            extract_google_meet_link(
                latest_event
            )
        )

        if meet_link:

            break

    return (
        latest_event,
        meet_link,
    )


# ============================================================
# SAVE GOOGLE CALENDAR SYNC RESULT
# ============================================================

def save_google_calendar_sync_result(
    *,
    timetable_session_id: str,
    event_id: str,
    staff_account_id: str,
    meeting_link: str | None,
):

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    public.timetable_sessions

                SET
                    google_calendar_event_id =
                        :event_id,

                    google_calendar_sync_status =
                        'Synced',

                    google_calendar_synced_at =
                        now(),

                    meeting_link =
                        COALESCE(
                            :meeting_link,
                            meeting_link
                        ),

                    updated_at =
                        now()

                WHERE
                    id = CAST(
                        :timetable_session_id
                        AS uuid
                    )
                """
            ),
            {
                "event_id": (
                    event_id
                ),

                "meeting_link": (
                    meeting_link
                ),

                "timetable_session_id": (
                    timetable_session_id
                ),
            },
        )

        connection.execute(
            text(
                """
                UPDATE
                    public.google_calendar_connections

                SET
                    last_synced_at =
                        now(),

                    updated_at =
                        now()

                WHERE
                    staff_account_id = CAST(
                        :staff_account_id
                        AS uuid
                    )
                """
            ),
            {
                "staff_account_id": (
                    staff_account_id
                ),
            },
        )


# ============================================================
# SYNC TIMETABLE SESSION TO GOOGLE CALENDAR
# ============================================================

def sync_facilitator_timetable_to_google(
    *,
    staff_account_id: str,
    staff_code: str,
    timetable_session_id: str,
) -> dict:

    session = (
        get_facilitator_calendar_session(
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
            "or not assigned to this academic staff member."
        )

    if (
        session[
            "status"
        ]
        != "Published"
    ):

        raise ValueError(
            "Only Published timetable sessions "
            "can be synced to Google Calendar."
        )

    credentials = (
        get_google_calendar_credentials(
            staff_account_id
        )
    )

    calendar_service = build(
        "calendar",
        "v3",
        credentials=(
            credentials
        ),
        cache_discovery=False,
    )

    event_body = (
        build_google_event_body(
            session
        )
    )

    existing_event_id = (
        session.get(
            "google_calendar_event_id"
        )
    )

    # ========================================================
    # UPDATE EXISTING GOOGLE EVENT
    # ========================================================

    if existing_event_id:

        event = (
            calendar_service
            .events()
            .patch(
                calendarId="primary",
                eventId=(
                    existing_event_id
                ),
                body=(
                    event_body
                ),
                conferenceDataVersion=1,
            )
            .execute()
        )

        action = (
            "updated"
        )

    # ========================================================
    # CREATE NEW GOOGLE EVENT
    # ========================================================

    else:

        event = (
            calendar_service
            .events()
            .insert(
                calendarId="primary",
                body=(
                    event_body
                ),
                conferenceDataVersion=1,
            )
            .execute()
        )

        action = (
            "created"
        )

    event_id = event.get(
        "id"
    )

    if not event_id:

        raise RuntimeError(
            "Google Calendar did not return "
            "an event ID."
        )

    meet_link = (
        extract_google_meet_link(
            event
        )
    )

    # Google Meet creation may finish asynchronously.
    if (
        requires_google_meet(
            session
        )
        and not meet_link
    ):

        event, meet_link = (
            wait_for_google_meet_link(
                calendar_service=(
                    calendar_service
                ),
                event_id=(
                    event_id
                ),
            )
        )

    save_google_calendar_sync_result(
        timetable_session_id=(
            timetable_session_id
        ),
        event_id=(
            event_id
        ),
        staff_account_id=(
            staff_account_id
        ),
        meeting_link=(
            meet_link
        ),
    )

    return {
        "action": (
            action
        ),

        "google_event_id": (
            event_id
        ),

        "html_link": (
            event.get(
                "htmlLink"
            )
        ),

        "google_meet_link": (
            meet_link
        ),

        "summary": (
            event.get(
                "summary"
            )
        ),

        "status": (
            event.get(
                "status"
            )
        ),

        "start": (
            event.get(
                "start"
            )
        ),

        "end": (
            event.get(
                "end"
            )
        ),

        "location": (
            event.get(
                "location"
            )
        ),

        "delivery_mode": (
            session.get(
                "delivery_mode"
            )
        ),
    }