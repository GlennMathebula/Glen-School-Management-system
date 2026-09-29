from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database import engine


# ============================================================
# CONSTANTS
# ============================================================

EDITABLE_ASSESSOR_STATUSES = {
    "Draft",
    "Returned",
}

MODERATION_READY_STATUS = "Submitted"

VALID_SUMMATIVE_TYPES = {
    "FISA",
    "EISA",
}


# ============================================================
# HELPERS
# ============================================================

def _clean_required(
    value: Any,
    field_name: str,
) -> str:

    cleaned = str(
        value or ""
    ).strip()

    if not cleaned:

        raise ValueError(
            f"{field_name} is required."
        )

    return cleaned


def _clean_optional(
    value: Any,
) -> str | None:

    if value is None:

        return None

    cleaned = str(
        value
    ).strip()

    return cleaned or None


def _normalise_assessment_type(
    value: str,
) -> str:

    assessment_type = (
        _clean_required(
            value,
            "Assessment type",
        )
        .upper()
    )

    if (
        assessment_type
        not in VALID_SUMMATIVE_TYPES
    ):

        raise ValueError(
            "Assessment type must be "
            "FISA or EISA."
        )

    return assessment_type


def _parse_datetime(
    value: str | None,
) -> datetime | None:

    if value is None:

        return None

    cleaned = str(
        value
    ).strip()

    if not cleaned:

        return None

    try:

        return datetime.fromisoformat(
            cleaned.replace(
                "Z",
                "+00:00",
            )
        )

    except ValueError as error:

        raise ValueError(
            "Assessment date must be "
            "a valid ISO date/time."
        ) from error


# ============================================================
# ASSESSOR OWNERSHIP
# ============================================================

def assessor_owns_registration(
    *,
    staff_code: str,
    registration_id: str,
) -> bool:

    with engine.connect() as connection:

        result = connection.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1

                    FROM public.class_enrolments ce

                    JOIN public.classes c
                        ON c.id = ce.class_id

                    WHERE
                        ce.registration_id = CAST(
                            :registration_id AS uuid
                        )

                        AND ce.status = 'Active'

                        AND c.status = 'Active'

                        AND c.assessor_code =
                            :staff_code
                )
                """
            ),
            {
                "staff_code": staff_code,
                "registration_id": (
                    registration_id
                ),
            },
        ).scalar_one()

    return bool(
        result
    )


def assessor_owns_module_registration(
    *,
    staff_code: str,
    module_registration_id: str,
) -> bool:

    with engine.connect() as connection:

        registration_id = (
            connection.execute(
                text(
                    """
                    SELECT registration_id

                    FROM public.module_registrations

                    WHERE
                        id = CAST(
                            :module_registration_id
                            AS uuid
                        )
                    """
                ),
                {
                    "module_registration_id": (
                        module_registration_id
                    ),
                },
            )
            .scalar_one_or_none()
        )

    if registration_id is None:

        return False

    return assessor_owns_registration(
        staff_code=staff_code,
        registration_id=str(
            registration_id
        ),
    )


# ============================================================
# MODULE MARK DETAIL
# ============================================================

def get_module_mark(
    mark_id: str,
) -> dict | None:

    with engine.connect() as connection:

        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        mk.id,
                        mk.module_registration_id,
                        mk.attempt_number,
                        mk.mark,
                        mk.grade,
                        mk.semester,
                        mk.academic_year,
                        mk.result,
                        mk.status,
                        mk.assessor_code,
                        mk.moderator_code,
                        mk.return_reason,
                        mk.moderated_date,
                        mk.rendered_date,
                        mk.created_at,
                        mk.updated_at,

                        mr.registration_id,

                        m.module_code,
                        m.module_name,
                        m.module_type,
                        m.credits,
                        m.nqf_level,
                        m.result_format,
                        m.pass_mark,

                        r.student_number,
                        r.course_code,
                        r.cycle,

                        a.first_name,
                        a.middle_name,
                        a.last_name

                    FROM public.marks mk

                    JOIN public.module_registrations mr
                        ON mr.id =
                            mk.module_registration_id

                    JOIN public.modules m
                        ON m.id =
                            mr.module_id

                    JOIN public.registrations r
                        ON r.id =
                            mr.registration_id

                    JOIN public.applications a
                        ON a.id =
                            r.application_id

                    WHERE
                        mk.id = CAST(
                            :mark_id AS uuid
                        )

                    LIMIT 1
                    """
                ),
                {
                    "mark_id": mark_id,
                },
            )
            .mappings()
            .first()
        )

    if not row:

        return None

    return dict(
        row
    )


# ============================================================
# ASSESSOR MODULE QUEUE
# ============================================================

def get_assessor_module_queue(
    *,
    staff_code: str,
) -> list[dict]:

    with engine.connect() as connection:

        rows = (
            connection.execute(
                text(
                    """
                    SELECT DISTINCT
                        mr.id
                            AS module_registration_id,

                        mr.registration_id,

                        mr.status
                            AS module_registration_status,

                        m.id
                            AS module_id,

                        m.module_code,
                        m.module_name,
                        m.module_type,
                        m.credits,
                        m.result_format,
                        m.pass_mark,

                        r.student_number,
                        r.course_code,
                        r.cycle,
                        r.registration_status,

                        a.first_name,
                        a.middle_name,
                        a.last_name,

                        c.class_code,
                        c.class_name,

                        latest_mark.id
                            AS mark_id,

                        latest_mark.attempt_number,

                        latest_mark.mark,

                        latest_mark.grade,

                        latest_mark.result,

                        latest_mark.status
                            AS assessment_status,

                        latest_mark.return_reason

                    FROM public.module_registrations mr

                    JOIN public.modules m
                        ON m.id = mr.module_id

                    JOIN public.registrations r
                        ON r.id =
                            mr.registration_id

                    JOIN public.applications a
                        ON a.id =
                            r.application_id

                    JOIN public.class_enrolments ce
                        ON ce.registration_id =
                            r.id

                        AND ce.status = 'Active'

                    JOIN public.classes c
                        ON c.id = ce.class_id

                        AND c.status = 'Active'

                        AND c.assessor_code =
                            :staff_code

                    LEFT JOIN LATERAL (
                        SELECT
                            x.id,
                            x.attempt_number,
                            x.mark,
                            x.grade,
                            x.result,
                            x.status,
                            x.return_reason

                        FROM public.marks x

                        WHERE
                            x.module_registration_id
                            = mr.id

                        ORDER BY
                            x.attempt_number DESC,
                            x.created_at DESC

                        LIMIT 1
                    ) latest_mark
                        ON TRUE

                    WHERE
                        mr.status NOT IN (
                            'Withdrawn',
                            'Cancelled'
                        )

                    ORDER BY
                        a.last_name,
                        a.first_name,
                        m.module_code
                    """
                ),
                {
                    "staff_code": (
                        staff_code
                    ),
                },
            )
            .mappings()
            .all()
        )

    return [
        dict(
            row
        )
        for row in rows
    ]


# ============================================================
# CAPTURE MODULE MARK
# ============================================================

def capture_module_mark(
    *,
    staff_code: str,
    module_registration_id: str,
    attempt_number: int,
    mark: Decimal | None,
    grade: str | None,
    semester: str | None,
    academic_year: int | None,
    result: str | None,
) -> dict:

    if not assessor_owns_module_registration(
        staff_code=staff_code,
        module_registration_id=(
            module_registration_id
        ),
    ):

        raise ValueError(
            "This module registration is "
            "not assigned to this assessor."
        )

    try:

        with engine.begin() as connection:

            mark_id = (
                connection.execute(
                    text(
                        """
                        INSERT INTO public.marks
                        (
                            module_registration_id,
                            attempt_number,
                            mark,
                            grade,
                            semester,
                            academic_year,
                            result,
                            status,
                            assessor_code
                        )

                        VALUES
                        (
                            CAST(
                                :module_registration_id
                                AS uuid
                            ),

                            :attempt_number,
                            :mark,
                            :grade,
                            :semester,
                            :academic_year,
                            :result,
                            'Draft',
                            :assessor_code
                        )

                        RETURNING id
                        """
                    ),
                    {
                        "module_registration_id": (
                            module_registration_id
                        ),
                        "attempt_number": (
                            attempt_number
                        ),
                        "mark": mark,
                        "grade": (
                            _clean_optional(
                                grade
                            )
                        ),
                        "semester": (
                            _clean_optional(
                                semester
                            )
                        ),
                        "academic_year": (
                            academic_year
                        ),
                        "result": (
                            _clean_optional(
                                result
                            )
                        ),
                        "assessor_code": (
                            staff_code
                        ),
                    },
                )
                .scalar_one()
            )

    except IntegrityError as error:

        raise ValueError(
            "An assessment attempt with "
            "that number already exists."
        ) from error

    return get_module_mark(
        str(
            mark_id
        )
    )


# ============================================================
# UPDATE MODULE MARK
# ============================================================

def update_module_mark(
    *,
    staff_code: str,
    mark_id: str,
    mark: Decimal | None,
    grade: str | None,
    semester: str | None,
    academic_year: int | None,
    result: str | None,
) -> dict:

    existing = get_module_mark(
        mark_id
    )

    if not existing:

        raise ValueError(
            "Module mark not found."
        )

    if (
        existing.get(
            "assessor_code"
        )
        != staff_code
    ):

        raise ValueError(
            "Only the assessor who captured "
            "this mark may edit it."
        )

    if (
        existing.get(
            "status"
        )
        not in EDITABLE_ASSESSOR_STATUSES
    ):

        raise ValueError(
            "Only Draft or Returned marks "
            "can be edited."
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE public.marks

                SET
                    mark = :mark,
                    grade = :grade,
                    semester = :semester,
                    academic_year =
                        :academic_year,
                    result = :result,
                    status = 'Draft',
                    moderator_code = NULL,
                    return_reason = NULL,
                    moderated_date = NULL,
                    rendered_date = NULL,
                    updated_at = now()

                WHERE
                    id = CAST(
                        :mark_id AS uuid
                    )
                """
            ),
            {
                "mark_id": mark_id,
                "mark": mark,
                "grade": (
                    _clean_optional(
                        grade
                    )
                ),
                "semester": (
                    _clean_optional(
                        semester
                    )
                ),
                "academic_year": (
                    academic_year
                ),
                "result": (
                    _clean_optional(
                        result
                    )
                ),
            },
        )

    return get_module_mark(
        mark_id
    )


# ============================================================
# SUBMIT MODULE MARK
# ============================================================

def submit_module_mark(
    *,
    staff_code: str,
    mark_id: str,
) -> dict:

    existing = get_module_mark(
        mark_id
    )

    if not existing:

        raise ValueError(
            "Module mark not found."
        )

    if (
        existing.get(
            "assessor_code"
        )
        != staff_code
    ):

        raise ValueError(
            "Only the assessor who captured "
            "this mark may submit it."
        )

    if (
        existing.get(
            "status"
        )
        not in EDITABLE_ASSESSOR_STATUSES
    ):

        raise ValueError(
            "Only Draft or Returned marks "
            "can be submitted."
        )

    if (
        existing.get(
            "mark"
        )
        is None
        and not existing.get(
            "result"
        )
    ):

        raise ValueError(
            "Enter a mark or result before "
            "submitting for moderation."
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE public.marks

                SET
                    status = 'Submitted',
                    moderator_code = NULL,
                    return_reason = NULL,
                    moderated_date = NULL,
                    updated_at = now()

                WHERE
                    id = CAST(
                        :mark_id AS uuid
                    )
                """
            ),
            {
                "mark_id": (
                    mark_id
                ),
            },
        )

    return get_module_mark(
        mark_id
    )


# ============================================================
# MODERATOR MODULE QUEUE
# ============================================================

def get_moderator_module_queue(
    *,
    staff_code: str,
) -> list[dict]:

    with engine.connect() as connection:

        rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        mk.id,
                        mk.attempt_number,
                        mk.mark,
                        mk.grade,
                        mk.result,
                        mk.status,
                        mk.assessor_code,
                        mk.moderator_code,
                        mk.return_reason,
                        mk.updated_at,

                        m.module_code,
                        m.module_name,
                        m.module_type,
                        m.credits,
                        m.result_format,
                        m.pass_mark,

                        r.student_number,
                        r.course_code,
                        r.cycle,

                        a.first_name,
                        a.middle_name,
                        a.last_name

                    FROM public.marks mk

                    JOIN public.module_registrations mr
                        ON mr.id =
                            mk.module_registration_id

                    JOIN public.modules m
                        ON m.id =
                            mr.module_id

                    JOIN public.registrations r
                        ON r.id =
                            mr.registration_id

                    JOIN public.applications a
                        ON a.id =
                            r.application_id

                    WHERE
                        mk.status = 'Submitted'

                        AND (
                            mk.assessor_code IS NULL

                            OR mk.assessor_code
                            <> :staff_code
                        )

                    ORDER BY
                        mk.updated_at ASC
                    """
                ),
                {
                    "staff_code": (
                        staff_code
                    ),
                },
            )
            .mappings()
            .all()
        )

    return [
        dict(
            row
        )
        for row in rows
    ]


# ============================================================
# MODERATE MODULE MARK
# ============================================================

def moderate_module_mark(
    *,
    moderator_staff_code: str,
    mark_id: str,
) -> dict:

    existing = get_module_mark(
        mark_id
    )

    if not existing:

        raise ValueError(
            "Module mark not found."
        )

    if (
        existing.get(
            "status"
        )
        != MODERATION_READY_STATUS
    ):

        raise ValueError(
            "Only Submitted marks can "
            "be moderated."
        )

    if (
        existing.get(
            "assessor_code"
        )
        == moderator_staff_code
    ):

        raise ValueError(
            "A moderator may not moderate "
            "an assessment they personally "
            "assessed."
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE public.marks

                SET
                    status = 'Moderated',
                    moderator_code =
                        :moderator_code,
                    return_reason = NULL,
                    moderated_date = now(),
                    updated_at = now()

                WHERE
                    id = CAST(
                        :mark_id AS uuid
                    )
                """
            ),
            {
                "mark_id": (
                    mark_id
                ),
                "moderator_code": (
                    moderator_staff_code
                ),
            },
        )

    return get_module_mark(
        mark_id
    )


# ============================================================
# RETURN MODULE MARK
# ============================================================

def return_module_mark(
    *,
    moderator_staff_code: str,
    mark_id: str,
    return_reason: str,
) -> dict:

    existing = get_module_mark(
        mark_id
    )

    if not existing:

        raise ValueError(
            "Module mark not found."
        )

    if (
        existing.get(
            "status"
        )
        != MODERATION_READY_STATUS
    ):

        raise ValueError(
            "Only Submitted marks can "
            "be returned."
        )

    if (
        existing.get(
            "assessor_code"
        )
        == moderator_staff_code
    ):

        raise ValueError(
            "A moderator may not moderate "
            "an assessment they personally "
            "assessed."
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE public.marks

                SET
                    status = 'Returned',
                    moderator_code =
                        :moderator_code,
                    return_reason =
                        :return_reason,
                    moderated_date = now(),
                    updated_at = now()

                WHERE
                    id = CAST(
                        :mark_id AS uuid
                    )
                """
            ),
            {
                "mark_id": (
                    mark_id
                ),
                "moderator_code": (
                    moderator_staff_code
                ),
                "return_reason": (
                    return_reason
                ),
            },
        )

    return get_module_mark(
        mark_id
    )


# ============================================================
# SUMMATIVE DETAIL
# ============================================================

def get_summative_assessment(
    assessment_id: str,
) -> dict | None:

    with engine.connect() as connection:

        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        sa.id,
                        sa.registration_id,
                        sa.assessment_type,
                        sa.attempt_number,
                        sa.mark,
                        sa.assessment_date,
                        sa.result,
                        sa.status,
                        sa.assessor_code,
                        sa.moderator_code,
                        sa.return_reason,
                        sa.created_at,
                        sa.updated_at,

                        r.student_number,
                        r.course_code,
                        r.cycle,
                        r.registration_status,
                        r.eisa_eligible,

                        a.first_name,
                        a.middle_name,
                        a.last_name

                    FROM
                        public.summative_assessments sa

                    JOIN public.registrations r
                        ON r.id =
                            sa.registration_id

                    JOIN public.applications a
                        ON a.id =
                            r.application_id

                    WHERE
                        sa.id = CAST(
                            :assessment_id
                            AS uuid
                        )

                    LIMIT 1
                    """
                ),
                {
                    "assessment_id": (
                        assessment_id
                    ),
                },
            )
            .mappings()
            .first()
        )

    if not row:

        return None

    return dict(
        row
    )


# ============================================================
# ASSESSOR SUMMATIVE QUEUE
# ============================================================

def get_assessor_summative_queue(
    *,
    staff_code: str,
) -> list[dict]:

    with engine.connect() as connection:

        rows = (
            connection.execute(
                text(
                    """
                    SELECT DISTINCT
                        r.id
                            AS registration_id,

                        r.student_number,
                        r.course_code,
                        r.cycle,
                        r.registration_status,
                        r.eisa_eligible,

                        a.first_name,
                        a.middle_name,
                        a.last_name,

                        c.class_code,
                        c.class_name

                    FROM public.registrations r

                    JOIN public.applications a
                        ON a.id =
                            r.application_id

                    JOIN public.class_enrolments ce
                        ON ce.registration_id =
                            r.id

                        AND ce.status = 'Active'

                    JOIN public.classes c
                        ON c.id = ce.class_id

                        AND c.status = 'Active'

                        AND c.assessor_code =
                            :staff_code

                    ORDER BY
                        a.last_name,
                        a.first_name
                    """
                ),
                {
                    "staff_code": (
                        staff_code
                    ),
                },
            )
            .mappings()
            .all()
        )

    return [
        dict(
            row
        )
        for row in rows
    ]


# ============================================================
# CAPTURE SUMMATIVE
# ============================================================

def capture_summative_assessment(
    *,
    staff_code: str,
    registration_id: str,
    assessment_type: str,
    attempt_number: int,
    mark: Decimal | None,
    assessment_date: str | None,
    result: str | None,
) -> dict:

    assessment_type = (
        _normalise_assessment_type(
            assessment_type
        )
    )

    if not assessor_owns_registration(
        staff_code=staff_code,
        registration_id=registration_id,
    ):

        raise ValueError(
            "This registration is not "
            "assigned to this assessor."
        )

    try:

        with engine.begin() as connection:

            assessment_id = (
                connection.execute(
                    text(
                        """
                        INSERT INTO
                            public.summative_assessments
                        (
                            registration_id,
                            assessment_type,
                            attempt_number,
                            mark,
                            assessment_date,
                            result,
                            status,
                            assessor_code
                        )

                        VALUES
                        (
                            CAST(
                                :registration_id
                                AS uuid
                            ),

                            :assessment_type,
                            :attempt_number,
                            :mark,
                            :assessment_date,
                            :result,
                            'Draft',
                            :assessor_code
                        )

                        RETURNING id
                        """
                    ),
                    {
                        "registration_id": (
                            registration_id
                        ),
                        "assessment_type": (
                            assessment_type
                        ),
                        "attempt_number": (
                            attempt_number
                        ),
                        "mark": mark,
                        "assessment_date": (
                            _parse_datetime(
                                assessment_date
                            )
                        ),
                        "result": (
                            _clean_optional(
                                result
                            )
                        ),
                        "assessor_code": (
                            staff_code
                        ),
                    },
                )
                .scalar_one()
            )

    except IntegrityError as error:

        raise ValueError(
            "That summative assessment "
            "attempt already exists."
        ) from error

    return get_summative_assessment(
        str(
            assessment_id
        )
    )


# ============================================================
# UPDATE SUMMATIVE
# ============================================================

def update_summative_assessment(
    *,
    staff_code: str,
    assessment_id: str,
    mark: Decimal | None,
    assessment_date: str | None,
    result: str | None,
) -> dict:

    existing = get_summative_assessment(
        assessment_id
    )

    if not existing:

        raise ValueError(
            "Summative assessment not found."
        )

    if (
        existing.get(
            "assessor_code"
        )
        != staff_code
    ):

        raise ValueError(
            "Only the assessor who captured "
            "this assessment may edit it."
        )

    if (
        existing.get(
            "status"
        )
        not in EDITABLE_ASSESSOR_STATUSES
    ):

        raise ValueError(
            "Only Draft or Returned "
            "assessments can be edited."
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    public.summative_assessments

                SET
                    mark = :mark,
                    assessment_date =
                        :assessment_date,
                    result = :result,
                    status = 'Draft',
                    moderator_code = NULL,
                    return_reason = NULL,
                    updated_at = now()

                WHERE
                    id = CAST(
                        :assessment_id AS uuid
                    )
                """
            ),
            {
                "assessment_id": (
                    assessment_id
                ),
                "mark": mark,
                "assessment_date": (
                    _parse_datetime(
                        assessment_date
                    )
                ),
                "result": (
                    _clean_optional(
                        result
                    )
                ),
            },
        )

    return get_summative_assessment(
        assessment_id
    )


# ============================================================
# SUBMIT SUMMATIVE
# ============================================================

def submit_summative_assessment(
    *,
    staff_code: str,
    assessment_id: str,
) -> dict:

    existing = get_summative_assessment(
        assessment_id
    )

    if not existing:

        raise ValueError(
            "Summative assessment not found."
        )

    if (
        existing.get(
            "assessor_code"
        )
        != staff_code
    ):

        raise ValueError(
            "Only the assessor who captured "
            "this assessment may submit it."
        )

    if (
        existing.get(
            "status"
        )
        not in EDITABLE_ASSESSOR_STATUSES
    ):

        raise ValueError(
            "Only Draft or Returned "
            "assessments can be submitted."
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    public.summative_assessments

                SET
                    status = 'Submitted',
                    moderator_code = NULL,
                    return_reason = NULL,
                    updated_at = now()

                WHERE
                    id = CAST(
                        :assessment_id AS uuid
                    )
                """
            ),
            {
                "assessment_id": (
                    assessment_id
                ),
            },
        )

    return get_summative_assessment(
        assessment_id
    )


# ============================================================
# MODERATOR SUMMATIVE QUEUE
# ============================================================

def get_moderator_summative_queue(
    *,
    staff_code: str,
) -> list[dict]:

    with engine.connect() as connection:

        rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        sa.id,
                        sa.registration_id,
                        sa.assessment_type,
                        sa.attempt_number,
                        sa.mark,
                        sa.assessment_date,
                        sa.result,
                        sa.status,
                        sa.assessor_code,
                        sa.moderator_code,
                        sa.return_reason,

                        r.student_number,
                        r.course_code,
                        r.cycle,

                        a.first_name,
                        a.middle_name,
                        a.last_name

                    FROM
                        public.summative_assessments sa

                    JOIN public.registrations r
                        ON r.id =
                            sa.registration_id

                    JOIN public.applications a
                        ON a.id =
                            r.application_id

                    WHERE
                        sa.status = 'Submitted'

                        AND (
                            sa.assessor_code IS NULL

                            OR sa.assessor_code
                            <> :staff_code
                        )

                    ORDER BY
                        sa.updated_at ASC
                    """
                ),
                {
                    "staff_code": (
                        staff_code
                    ),
                },
            )
            .mappings()
            .all()
        )

    return [
        dict(
            row
        )
        for row in rows
    ]


# ============================================================
# MODERATE SUMMATIVE
# ============================================================

def moderate_summative_assessment(
    *,
    moderator_staff_code: str,
    assessment_id: str,
) -> dict:

    existing = get_summative_assessment(
        assessment_id
    )

    if not existing:

        raise ValueError(
            "Summative assessment not found."
        )

    if (
        existing.get(
            "status"
        )
        != MODERATION_READY_STATUS
    ):

        raise ValueError(
            "Only Submitted assessments "
            "can be moderated."
        )

    if (
        existing.get(
            "assessor_code"
        )
        == moderator_staff_code
    ):

        raise ValueError(
            "A moderator may not moderate "
            "an assessment they personally "
            "assessed."
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    public.summative_assessments

                SET
                    status = 'Moderated',
                    moderator_code =
                        :moderator_code,
                    return_reason = NULL,
                    updated_at = now()

                WHERE
                    id = CAST(
                        :assessment_id AS uuid
                    )
                """
            ),
            {
                "assessment_id": (
                    assessment_id
                ),
                "moderator_code": (
                    moderator_staff_code
                ),
            },
        )

    return get_summative_assessment(
        assessment_id
    )


# ============================================================
# RETURN SUMMATIVE
# ============================================================

def return_summative_assessment(
    *,
    moderator_staff_code: str,
    assessment_id: str,
    return_reason: str,
) -> dict:

    existing = get_summative_assessment(
        assessment_id
    )

    if not existing:

        raise ValueError(
            "Summative assessment not found."
        )

    if (
        existing.get(
            "status"
        )
        != MODERATION_READY_STATUS
    ):

        raise ValueError(
            "Only Submitted assessments "
            "can be returned."
        )

    if (
        existing.get(
            "assessor_code"
        )
        == moderator_staff_code
    ):

        raise ValueError(
            "A moderator may not moderate "
            "an assessment they personally "
            "assessed."
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    public.summative_assessments

                SET
                    status = 'Returned',
                    moderator_code =
                        :moderator_code,
                    return_reason =
                        :return_reason,
                    updated_at = now()

                WHERE
                    id = CAST(
                        :assessment_id AS uuid
                    )
                """
            ),
            {
                "assessment_id": (
                    assessment_id
                ),
                "moderator_code": (
                    moderator_staff_code
                ),
                "return_reason": (
                    return_reason
                ),
            },
        )

    return get_summative_assessment(
        assessment_id
    )