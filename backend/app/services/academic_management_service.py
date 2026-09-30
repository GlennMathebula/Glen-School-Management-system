from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database import engine
from app.services.staff_audit_service import (
    create_staff_audit_log,
)


CYCLE_STATUSES = {
    "Draft",
    "Active",
    "Closed",
    "Archived",
}

CLASS_STATUSES = {
    "Draft",
    "Active",
    "Closed",
    "Archived",
}

ELIGIBLE_REGISTRATION_STATUSES = {
    "Registered",
    "In Progress",
}


def _clean_code(
    value: str,
    field_name: str,
) -> str:
    value = str(
        value
        or ""
    ).strip().upper()

    if not value:
        raise ValueError(
            f"{field_name} is required."
        )

    return value


def _clean_optional_code(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    value = str(
        value
    ).strip().upper()

    return value or None


def _clean_uuid(
    value: str,
    field_name: str,
) -> str:
    value = str(
        value
        or ""
    ).strip()

    try:
        UUID(
            value
        )
    except (
        ValueError,
        TypeError,
        AttributeError,
    ) as error:
        raise ValueError(
            f"Invalid {field_name}."
        ) from error

    return value


def _json_safe(
    value,
):
    if value is None:
        return None

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): _json_safe(
                item
            )
            for key, item
            in value.items()
        }

    if isinstance(
        value,
        (list, tuple, set),
    ):
        return [
            _json_safe(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        (
            datetime,
            date,
            UUID,
            Decimal,
        ),
    ):
        return str(
            value
        )

    return value


def _write_audit(
    *,
    actor_staff_code: str,
    action_code: str,
    entity_type: str,
    entity_id: str,
    description: str,
    before_data: dict | None = None,
    after_data: dict | None = None,
    metadata: dict | None = None,
) -> None:
    try:
        create_staff_audit_log(
            actor_staff_code=(
                actor_staff_code
            ),
            action_code=action_code,
            module_code=(
                "ACADEMIC_MANAGEMENT"
            ),
            entity_type=entity_type,
            entity_id=str(
                entity_id
            ),
            description=description,
            before_data=(
                _json_safe(
                    before_data
                )
            ),
            after_data=(
                _json_safe(
                    after_data
                )
            ),
            metadata=(
                _json_safe(
                    metadata
                    or {}
                )
            ),
        )

    except Exception as error:
        print(
            "WARNING: Academic management "
            "action succeeded but audit "
            "logging failed: "
            f"{error}"
        )


def _validate_date_range(
    *,
    start_date,
    end_date,
    label: str,
) -> None:
    if (
        start_date
        and end_date
        and end_date < start_date
    ):
        raise ValueError(
            f"{label} end date cannot "
            "be before the start date."
        )


def _get_cycle(
    cycle_code: str,
) -> dict | None:
    cycle_code = _clean_code(
        cycle_code,
        "Cycle code",
    )

    with engine.connect() as connection:
        row = connection.execute(
            text("""
                SELECT *
                FROM public.cycles
                WHERE cycle_code =
                      :cycle_code
                LIMIT 1
            """),
            {
                "cycle_code": cycle_code
            },
        ).mappings().first()

    return (
        dict(
            row
        )
        if row
        else None
    )


def _get_class(
    class_code: str,
) -> dict | None:
    class_code = _clean_code(
        class_code,
        "Class code",
    )

    with engine.connect() as connection:
        row = connection.execute(
            text("""
                SELECT *
                FROM public.classes
                WHERE class_code =
                      :class_code
                LIMIT 1
            """),
            {
                "class_code": class_code
            },
        ).mappings().first()

    return (
        dict(
            row
        )
        if row
        else None
    )


def _ensure_cycle_course(
    *,
    cycle_code: str,
    course_code: str,
) -> dict:
    cycle_code = _clean_code(
        cycle_code,
        "Cycle code",
    )
    course_code = _clean_code(
        course_code,
        "Course code",
    )

    with engine.connect() as connection:
        row = connection.execute(
            text("""
                SELECT
                    cc.id,
                    cc.is_active,
                    cy.id AS cycle_id,
                    cy.cycle_code,
                    cy.status AS cycle_status,
                    c.course_code,
                    c.course_name,
                    c.status AS course_status
                FROM public.cycle_courses cc
                JOIN public.cycles cy
                    ON cy.id = cc.cycle_id
                JOIN public.courses c
                    ON c.course_code =
                       cc.course_code
                WHERE
                    cy.cycle_code =
                        :cycle_code
                    AND cc.course_code =
                        :course_code
                    AND cc.is_active = TRUE
                LIMIT 1
            """),
            {
                "cycle_code": cycle_code,
                "course_code": course_code,
            },
        ).mappings().first()

    if not row:
        raise ValueError(
            "This course is not active "
            "for the selected cycle."
        )

    return dict(
        row
    )


def _staff_has_role(
    *,
    staff_code: str,
    required_role: str,
) -> bool:
    staff_code = _clean_code(
        staff_code,
        "Staff code",
    )
    required_role = _clean_code(
        required_role,
        "Role code",
    )

    with engine.connect() as connection:
        row = connection.execute(
            text("""
                SELECT 1
                FROM public.staff_accounts sa
                WHERE
                    sa.staff_code =
                        :staff_code
                    AND sa.is_active = TRUE
                    AND (
                        sa.role_code =
                            :required_role
                        OR EXISTS (
                            SELECT 1
                            FROM public.staff_account_roles sar
                            WHERE
                                sar.staff_code =
                                    sa.staff_code
                                AND sar.role_code =
                                    :required_role
                                AND sar.is_active =
                                    TRUE
                        )
                    )
                LIMIT 1
            """),
            {
                "staff_code": staff_code,
                "required_role": (
                    required_role
                ),
            },
        ).first()

    return row is not None


# ============================================================
# CYCLES
# ============================================================

def get_cycles() -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT
                    cy.*,

                    COUNT(
                        DISTINCT cc.id
                    ) FILTER (
                        WHERE cc.is_active =
                              TRUE
                    ) AS active_course_count,

                    COUNT(
                        DISTINCT cl.id
                    ) AS class_count

                FROM public.cycles cy

                LEFT JOIN public.cycle_courses cc
                    ON cc.cycle_id = cy.id

                LEFT JOIN public.classes cl
                    ON cl.cycle_code =
                       cy.cycle_code

                GROUP BY cy.id

                ORDER BY
                    cy.program_start_date DESC,
                    cy.cycle_code DESC
            """)
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def create_cycle(
    *,
    actor_staff_code: str,
    cycle_code: str,
    cycle_name: str | None,
    application_start_date,
    application_end_date,
    registration_start_date,
    registration_end_date,
    program_start_date,
    expected_completion_date,
    cipc_required: bool,
    status: str,
) -> dict:
    cycle_code = _clean_code(
        cycle_code,
        "Cycle code",
    )

    status = str(
        status
        or "Draft"
    ).strip().title()

    if status not in CYCLE_STATUSES:
        raise ValueError(
            "Invalid cycle status."
        )

    _validate_date_range(
        start_date=(
            application_start_date
        ),
        end_date=(
            application_end_date
        ),
        label="Application",
    )

    _validate_date_range(
        start_date=(
            registration_start_date
        ),
        end_date=(
            registration_end_date
        ),
        label="Registration",
    )

    if (
        expected_completion_date
        and expected_completion_date <
            program_start_date
    ):
        raise ValueError(
            "Expected completion date "
            "cannot be before the "
            "programme start date."
        )

    try:
        with engine.begin() as connection:
            row = connection.execute(
                text("""
                    INSERT INTO public.cycles (
                        cycle_code,
                        cycle_name,
                        application_start_date,
                        application_end_date,
                        registration_start_date,
                        registration_end_date,
                        program_start_date,
                        expected_completion_date,
                        cipc_required,
                        status
                    )
                    VALUES (
                        :cycle_code,
                        :cycle_name,
                        :application_start_date,
                        :application_end_date,
                        :registration_start_date,
                        :registration_end_date,
                        :program_start_date,
                        :expected_completion_date,
                        :cipc_required,
                        :status
                    )
                    RETURNING *
                """),
                {
                    "cycle_code": cycle_code,
                    "cycle_name": cycle_name,
                    "application_start_date": (
                        application_start_date
                    ),
                    "application_end_date": (
                        application_end_date
                    ),
                    "registration_start_date": (
                        registration_start_date
                    ),
                    "registration_end_date": (
                        registration_end_date
                    ),
                    "program_start_date": (
                        program_start_date
                    ),
                    "expected_completion_date": (
                        expected_completion_date
                    ),
                    "cipc_required": (
                        bool(
                            cipc_required
                        )
                    ),
                    "status": status,
                },
            ).mappings().first()

    except IntegrityError as error:
        raise ValueError(
            "A cycle with this code "
            "already exists."
        ) from error

    record = dict(
        row
    )

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code="CYCLE_CREATED",
        entity_type="CYCLE",
        entity_id=record["id"],
        description=(
            "Academic cycle created."
        ),
        after_data=record,
    )

    return record


def update_cycle(
    *,
    actor_staff_code: str,
    cycle_code: str,
    cycle_name: str | None,
    application_start_date,
    application_end_date,
    registration_start_date,
    registration_end_date,
    program_start_date,
    expected_completion_date,
    cipc_required: bool | None,
) -> dict:
    cycle_code = _clean_code(
        cycle_code,
        "Cycle code",
    )

    before = _get_cycle(
        cycle_code
    )

    if not before:
        raise ValueError(
            "Cycle not found."
        )

    application_start_date = (
        application_start_date
        if application_start_date is not None
        else before[
            "application_start_date"
        ]
    )

    application_end_date = (
        application_end_date
        if application_end_date is not None
        else before[
            "application_end_date"
        ]
    )

    registration_start_date = (
        registration_start_date
        if registration_start_date is not None
        else before[
            "registration_start_date"
        ]
    )

    registration_end_date = (
        registration_end_date
        if registration_end_date is not None
        else before[
            "registration_end_date"
        ]
    )

    program_start_date = (
        program_start_date
        if program_start_date is not None
        else before[
            "program_start_date"
        ]
    )

    expected_completion_date = (
        expected_completion_date
        if expected_completion_date is not None
        else before[
            "expected_completion_date"
        ]
    )

    _validate_date_range(
        start_date=(
            application_start_date
        ),
        end_date=(
            application_end_date
        ),
        label="Application",
    )

    _validate_date_range(
        start_date=(
            registration_start_date
        ),
        end_date=(
            registration_end_date
        ),
        label="Registration",
    )

    if (
        expected_completion_date
        and expected_completion_date <
            program_start_date
    ):
        raise ValueError(
            "Expected completion date "
            "cannot be before the "
            "programme start date."
        )

    with engine.begin() as connection:
        row = connection.execute(
            text("""
                UPDATE public.cycles
                SET
                    cycle_name =
                        COALESCE(
                            :cycle_name,
                            cycle_name
                        ),
                    application_start_date =
                        :application_start_date,
                    application_end_date =
                        :application_end_date,
                    registration_start_date =
                        :registration_start_date,
                    registration_end_date =
                        :registration_end_date,
                    program_start_date =
                        :program_start_date,
                    expected_completion_date =
                        :expected_completion_date,
                    cipc_required =
                        COALESCE(
                            :cipc_required,
                            cipc_required
                        ),
                    updated_at = NOW()
                WHERE cycle_code =
                      :cycle_code
                RETURNING *
            """),
            {
                "cycle_code": cycle_code,
                "cycle_name": cycle_name,
                "application_start_date": (
                    application_start_date
                ),
                "application_end_date": (
                    application_end_date
                ),
                "registration_start_date": (
                    registration_start_date
                ),
                "registration_end_date": (
                    registration_end_date
                ),
                "program_start_date": (
                    program_start_date
                ),
                "expected_completion_date": (
                    expected_completion_date
                ),
                "cipc_required": (
                    cipc_required
                ),
            },
        ).mappings().first()

    record = dict(
        row
    )

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code="CYCLE_UPDATED",
        entity_type="CYCLE",
        entity_id=record["id"],
        description=(
            "Academic cycle updated."
        ),
        before_data=before,
        after_data=record,
    )

    return record


def set_cycle_status(
    *,
    actor_staff_code: str,
    cycle_code: str,
    status: str,
) -> dict:
    cycle_code = _clean_code(
        cycle_code,
        "Cycle code",
    )

    status = str(
        status
        or ""
    ).strip().title()

    if status not in CYCLE_STATUSES:
        raise ValueError(
            "Invalid cycle status."
        )

    before = _get_cycle(
        cycle_code
    )

    if not before:
        raise ValueError(
            "Cycle not found."
        )

    with engine.begin() as connection:
        row = connection.execute(
            text("""
                UPDATE public.cycles
                SET
                    status = :status,
                    updated_at = NOW()
                WHERE cycle_code =
                      :cycle_code
                RETURNING *
            """),
            {
                "cycle_code": cycle_code,
                "status": status,
            },
        ).mappings().first()

    record = dict(
        row
    )

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code=(
            "CYCLE_STATUS_CHANGED"
        ),
        entity_type="CYCLE",
        entity_id=record["id"],
        description=(
            "Academic cycle status changed."
        ),
        before_data=before,
        after_data=record,
    )

    return record


# ============================================================
# COURSE OFFERINGS
# ============================================================

def get_courses() -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT
                    id,
                    course_code,
                    course_name,
                    qualification_type,
                    nqf_level,
                    credits,
                    status,
                    completion_months,
                    assessment_type,
                    last_enrolment_date,
                    last_achievement_date
                FROM public.courses
                ORDER BY
                    status,
                    course_name,
                    course_code
            """)
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def get_cycle_courses(
    *,
    cycle_code: str,
) -> list[dict]:
    cycle_code = _clean_code(
        cycle_code,
        "Cycle code",
    )

    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT
                    cc.id,
                    cy.cycle_code,
                    cy.cycle_name,
                    cc.course_code,
                    c.course_name,
                    c.nqf_level,
                    c.credits,
                    c.assessment_type,
                    cc.is_active,
                    cc.created_at
                FROM public.cycles cy
                JOIN public.cycle_courses cc
                    ON cc.cycle_id =
                       cy.id
                JOIN public.courses c
                    ON c.course_code =
                       cc.course_code
                WHERE
                    cy.cycle_code =
                        :cycle_code
                ORDER BY
                    cc.is_active DESC,
                    c.course_name
            """),
            {
                "cycle_code": cycle_code
            },
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def set_cycle_course_status(
    *,
    actor_staff_code: str,
    cycle_code: str,
    course_code: str,
    is_active: bool,
) -> dict:
    cycle_code = _clean_code(
        cycle_code,
        "Cycle code",
    )
    course_code = _clean_code(
        course_code,
        "Course code",
    )

    with engine.begin() as connection:
        cycle = connection.execute(
            text("""
                SELECT id
                FROM public.cycles
                WHERE cycle_code =
                      :cycle_code
                LIMIT 1
            """),
            {
                "cycle_code": cycle_code
            },
        ).mappings().first()

        if not cycle:
            raise ValueError(
                "Cycle not found."
            )

        course = connection.execute(
            text("""
                SELECT
                    course_code,
                    status
                FROM public.courses
                WHERE course_code =
                      :course_code
                LIMIT 1
            """),
            {
                "course_code": course_code
            },
        ).mappings().first()

        if not course:
            raise ValueError(
                "Course not found."
            )

        if (
            not is_active
        ):
            active_classes = (
                connection.execute(
                    text("""
                        SELECT COUNT(*)
                        FROM public.classes
                        WHERE
                            cycle_code =
                                :cycle_code
                            AND course_code =
                                :course_code
                            AND status IN (
                                'Draft',
                                'Active'
                            )
                    """),
                    {
                        "cycle_code": (
                            cycle_code
                        ),
                        "course_code": (
                            course_code
                        ),
                    },
                ).scalar_one()
            )

            if active_classes:
                raise ValueError(
                    "This course cannot be "
                    "deactivated for the cycle "
                    "while Draft or Active "
                    "classes still use it."
                )

        row = connection.execute(
            text("""
                INSERT INTO public.cycle_courses (
                    cycle_id,
                    course_code,
                    is_active
                )
                VALUES (
                    :cycle_id,
                    :course_code,
                    :is_active
                )
                ON CONFLICT (
                    cycle_id,
                    course_code
                )
                DO UPDATE SET
                    is_active =
                        EXCLUDED.is_active
                RETURNING *
            """),
            {
                "cycle_id": cycle["id"],
                "course_code": course_code,
                "is_active": bool(
                    is_active
                ),
            },
        ).mappings().first()

    record = dict(
        row
    )

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code=(
            "CYCLE_COURSE_STATUS_CHANGED"
        ),
        entity_type="CYCLE_COURSE",
        entity_id=record["id"],
        description=(
            "Cycle course offering "
            "status changed."
        ),
        after_data=record,
        metadata={
            "cycle_code": cycle_code,
            "course_code": course_code,
        },
    )

    return record


# ============================================================
# CLASSES
# ============================================================

def get_classes(
    *,
    cycle_code: str | None = None,
    course_code: str | None = None,
) -> list[dict]:
    cycle_code = (
        _clean_optional_code(
            cycle_code
        )
    )
    course_code = (
        _clean_optional_code(
            course_code
        )
    )

    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT
                    cl.id,
                    cl.class_code,
                    cl.class_name,
                    cl.course_code,
                    c.course_name,
                    cl.cycle_code,
                    cy.cycle_name,
                    cl.class_group,
                    cl.facilitator_code,
                    CONCAT_WS(
                        ' ',
                        ef.first_name,
                        ef.last_name
                    ) AS facilitator_name,
                    cl.assessor_code,
                    CONCAT_WS(
                        ' ',
                        ea.first_name,
                        ea.last_name
                    ) AS assessor_name,
                    cl.status,
                    cl.created_at,
                    cl.updated_at,

                    COUNT(
                        DISTINCT ce.id
                    ) FILTER (
                        WHERE ce.status =
                              'Active'
                    ) AS active_learner_count

                FROM public.classes cl

                JOIN public.courses c
                    ON c.course_code =
                       cl.course_code

                LEFT JOIN public.cycles cy
                    ON cy.cycle_code =
                       cl.cycle_code

                LEFT JOIN public.staff_accounts saf
                    ON saf.staff_code =
                       cl.facilitator_code

                LEFT JOIN public.employees ef
                    ON ef.id =
                       saf.employee_id

                LEFT JOIN public.staff_accounts saa
                    ON saa.staff_code =
                       cl.assessor_code

                LEFT JOIN public.employees ea
                    ON ea.id =
                       saa.employee_id

                LEFT JOIN public.class_enrolments ce
                    ON ce.class_id =
                       cl.id

                WHERE
                    (
                        :cycle_code IS NULL
                        OR cl.cycle_code =
                           :cycle_code
                    )
                    AND (
                        :course_code IS NULL
                        OR cl.course_code =
                           :course_code
                    )

                GROUP BY
                    cl.id,
                    c.course_name,
                    cy.cycle_name,
                    ef.first_name,
                    ef.last_name,
                    ea.first_name,
                    ea.last_name

                ORDER BY
                    cl.cycle_code DESC,
                    c.course_name,
                    cl.class_code
            """),
            {
                "cycle_code": cycle_code,
                "course_code": course_code,
            },
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def create_class(
    *,
    actor_staff_code: str,
    class_code: str,
    class_name: str | None,
    course_code: str,
    cycle_code: str,
    class_group: str | None,
    facilitator_code: str | None,
    assessor_code: str | None,
    status: str,
) -> dict:
    class_code = _clean_code(
        class_code,
        "Class code",
    )
    course_code = _clean_code(
        course_code,
        "Course code",
    )
    cycle_code = _clean_code(
        cycle_code,
        "Cycle code",
    )

    status = str(
        status
        or "Draft"
    ).strip().title()

    if status not in CLASS_STATUSES:
        raise ValueError(
            "Invalid class status."
        )

    _ensure_cycle_course(
        cycle_code=cycle_code,
        course_code=course_code,
    )

    facilitator_code = (
        _clean_optional_code(
            facilitator_code
        )
    )

    assessor_code = (
        _clean_optional_code(
            assessor_code
        )
    )

    if facilitator_code:
        if not _staff_has_role(
            staff_code=(
                facilitator_code
            ),
            required_role=(
                "FACILITATOR"
            ),
        ):
            raise ValueError(
                "Selected facilitator does "
                "not have an active "
                "Facilitator role."
            )

    if assessor_code:
        if not _staff_has_role(
            staff_code=assessor_code,
            required_role="ASSESSOR",
        ):
            raise ValueError(
                "Selected assessor does "
                "not have an active "
                "Assessor role."
            )

    try:
        with engine.begin() as connection:
            row = connection.execute(
                text("""
                    INSERT INTO public.classes (
                        class_code,
                        class_name,
                        course_code,
                        cycle_code,
                        class_group,
                        facilitator_code,
                        assessor_code,
                        status
                    )
                    VALUES (
                        :class_code,
                        :class_name,
                        :course_code,
                        :cycle_code,
                        :class_group,
                        :facilitator_code,
                        :assessor_code,
                        :status
                    )
                    RETURNING *
                """),
                {
                    "class_code": class_code,
                    "class_name": class_name,
                    "course_code": course_code,
                    "cycle_code": cycle_code,
                    "class_group": class_group,
                    "facilitator_code": (
                        facilitator_code
                    ),
                    "assessor_code": (
                        assessor_code
                    ),
                    "status": status,
                },
            ).mappings().first()

    except IntegrityError as error:
        raise ValueError(
            "A class with this class code "
            "already exists."
        ) from error

    record = dict(
        row
    )

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code="CLASS_CREATED",
        entity_type="CLASS",
        entity_id=record["id"],
        description=(
            "Academic class created."
        ),
        after_data=record,
    )

    return record


def update_class(
    *,
    actor_staff_code: str,
    class_code: str,
    class_name: str | None,
    course_code: str | None,
    cycle_code: str | None,
    class_group: str | None,
    status: str | None,
) -> dict:
    class_code = _clean_code(
        class_code,
        "Class code",
    )

    before = _get_class(
        class_code
    )

    if not before:
        raise ValueError(
            "Class not found."
        )

    target_course_code = (
        _clean_optional_code(
            course_code
        )
        or before["course_code"]
    )

    target_cycle_code = (
        _clean_optional_code(
            cycle_code
        )
        or before["cycle_code"]
    )

    if (
        target_course_code
        != before["course_code"]
        or target_cycle_code
        != before["cycle_code"]
    ):
        with engine.connect() as connection:
            active_enrolments = (
                connection.execute(
                    text("""
                        SELECT COUNT(*)
                        FROM public.class_enrolments
                        WHERE class_id =
                              CAST(
                                  :class_id
                                  AS uuid
                              )
                          AND status =
                              'Active'
                    """),
                    {
                        "class_id": (
                            str(
                                before["id"]
                            )
                        )
                    },
                ).scalar_one()
            )

        if active_enrolments:
            raise ValueError(
                "Course or cycle cannot be "
                "changed while the class has "
                "active learner enrolments."
            )

        _ensure_cycle_course(
            cycle_code=(
                target_cycle_code
            ),
            course_code=(
                target_course_code
            ),
        )

    target_status = (
        str(
            status
        ).strip().title()
        if status is not None
        else before["status"]
    )

    if (
        target_status
        not in CLASS_STATUSES
    ):
        raise ValueError(
            "Invalid class status."
        )

    with engine.begin() as connection:
        row = connection.execute(
            text("""
                UPDATE public.classes
                SET
                    class_name =
                        COALESCE(
                            :class_name,
                            class_name
                        ),
                    course_code =
                        :course_code,
                    cycle_code =
                        :cycle_code,
                    class_group =
                        COALESCE(
                            :class_group,
                            class_group
                        ),
                    status =
                        :status,
                    updated_at = NOW()
                WHERE class_code =
                      :class_code
                RETURNING *
            """),
            {
                "class_code": class_code,
                "class_name": class_name,
                "course_code": (
                    target_course_code
                ),
                "cycle_code": (
                    target_cycle_code
                ),
                "class_group": class_group,
                "status": target_status,
            },
        ).mappings().first()

    record = dict(
        row
    )

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code="CLASS_UPDATED",
        entity_type="CLASS",
        entity_id=record["id"],
        description=(
            "Academic class updated."
        ),
        before_data=before,
        after_data=record,
    )

    return record


# ============================================================
# STAFF ASSIGNMENT
# ============================================================

def get_academic_staff_options() -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT
                    sa.staff_code,
                    sa.role_code AS primary_role,
                    e.employee_number,
                    e.first_name,
                    e.middle_name,
                    e.last_name,
                    e.job_title,
                    e.department,

                    (
                        sa.role_code =
                            'FACILITATOR'
                        OR EXISTS (
                            SELECT 1
                            FROM public.staff_account_roles sar
                            WHERE
                                sar.staff_code =
                                    sa.staff_code
                                AND sar.role_code =
                                    'FACILITATOR'
                                AND sar.is_active =
                                    TRUE
                        )
                    ) AS can_facilitate,

                    (
                        sa.role_code =
                            'ASSESSOR'
                        OR EXISTS (
                            SELECT 1
                            FROM public.staff_account_roles sar
                            WHERE
                                sar.staff_code =
                                    sa.staff_code
                                AND sar.role_code =
                                    'ASSESSOR'
                                AND sar.is_active =
                                    TRUE
                        )
                    ) AS can_assess

                FROM public.staff_accounts sa
                JOIN public.employees e
                    ON e.id =
                       sa.employee_id
                WHERE
                    sa.is_active = TRUE
                    AND e.employment_status =
                        'Active'
                    AND (
                        sa.role_code IN (
                            'FACILITATOR',
                            'ASSESSOR'
                        )
                        OR EXISTS (
                            SELECT 1
                            FROM public.staff_account_roles sar
                            WHERE
                                sar.staff_code =
                                    sa.staff_code
                                AND sar.is_active =
                                    TRUE
                                AND sar.role_code IN (
                                    'FACILITATOR',
                                    'ASSESSOR'
                                )
                        )
                    )
                ORDER BY
                    e.last_name,
                    e.first_name,
                    sa.staff_code
            """)
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def assign_class_staff(
    *,
    actor_staff_code: str,
    class_code: str,
    facilitator_code: str | None,
    assessor_code: str | None,
) -> dict:
    class_code = _clean_code(
        class_code,
        "Class code",
    )

    before = _get_class(
        class_code
    )

    if not before:
        raise ValueError(
            "Class not found."
        )

    facilitator_code = (
        _clean_optional_code(
            facilitator_code
        )
    )

    assessor_code = (
        _clean_optional_code(
            assessor_code
        )
    )

    if facilitator_code:
        if not _staff_has_role(
            staff_code=(
                facilitator_code
            ),
            required_role=(
                "FACILITATOR"
            ),
        ):
            raise ValueError(
                "Selected facilitator does "
                "not have an active "
                "Facilitator role."
            )

    if assessor_code:
        if not _staff_has_role(
            staff_code=assessor_code,
            required_role="ASSESSOR",
        ):
            raise ValueError(
                "Selected assessor does "
                "not have an active "
                "Assessor role."
            )

    with engine.begin() as connection:
        row = connection.execute(
            text("""
                UPDATE public.classes
                SET
                    facilitator_code =
                        :facilitator_code,
                    assessor_code =
                        :assessor_code,
                    updated_at = NOW()
                WHERE class_code =
                      :class_code
                RETURNING *
            """),
            {
                "class_code": class_code,
                "facilitator_code": (
                    facilitator_code
                ),
                "assessor_code": (
                    assessor_code
                ),
            },
        ).mappings().first()

    record = dict(
        row
    )

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code=(
            "CLASS_STAFF_ASSIGNED"
        ),
        entity_type="CLASS",
        entity_id=record["id"],
        description=(
            "Facilitator and/or Assessor "
            "assignment updated."
        ),
        before_data=before,
        after_data=record,
    )

    return record


# ============================================================
# CLASS ENROLMENTS
# ============================================================

def get_class_learners(
    *,
    class_code: str,
) -> list[dict]:
    class_record = _get_class(
        class_code
    )

    if not class_record:
        raise ValueError(
            "Class not found."
        )

    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT
                    ce.id AS class_enrolment_id,
                    ce.status AS
                        class_enrolment_status,
                    ce.enrolled_at,

                    r.id AS registration_id,
                    r.student_number,
                    r.registration_status,
                    r.course_code,
                    r.cycle,

                    a.first_name,
                    a.middle_name,
                    a.last_name,
                    a.email,
                    a.cell_number

                FROM public.class_enrolments ce

                JOIN public.registrations r
                    ON r.id =
                       ce.registration_id

                JOIN public.applications a
                    ON a.student_number =
                       r.student_number

                WHERE ce.class_id =
                      :class_id

                ORDER BY
                    CASE
                        WHEN ce.status =
                             'Active'
                        THEN 0
                        ELSE 1
                    END,
                    a.last_name,
                    a.first_name
            """),
            {
                "class_id": (
                    class_record["id"]
                )
            },
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def get_eligible_class_learners(
    *,
    class_code: str,
) -> list[dict]:
    class_record = _get_class(
        class_code
    )

    if not class_record:
        raise ValueError(
            "Class not found."
        )

    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT
                    r.id AS registration_id,
                    r.student_number,
                    r.registration_status,
                    r.course_code,
                    r.cycle,
                    r.registration_date,

                    a.first_name,
                    a.middle_name,
                    a.last_name,
                    a.email,
                    a.cell_number

                FROM public.registrations r

                JOIN public.applications a
                    ON a.student_number =
                       r.student_number

                WHERE
                    r.course_code =
                        :course_code

                    AND r.registration_status
                        IN (
                            'Registered',
                            'In Progress'
                        )

                    AND (
                        :cycle_code IS NULL
                        OR r.cycle IS NULL
                        OR r.cycle =
                           :cycle_code
                    )

                    AND NOT EXISTS (
                        SELECT 1
                        FROM public.class_enrolments ce
                        WHERE
                            ce.registration_id =
                                r.id
                            AND ce.status =
                                'Active'
                    )

                ORDER BY
                    a.last_name,
                    a.first_name,
                    r.student_number
            """),
            {
                "course_code": (
                    class_record[
                        "course_code"
                    ]
                ),
                "cycle_code": (
                    class_record[
                        "cycle_code"
                    ]
                ),
            },
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def enrol_registration_in_class(
    *,
    actor_staff_code: str,
    class_code: str,
    registration_id: str,
) -> dict:
    class_code = _clean_code(
        class_code,
        "Class code",
    )

    registration_id = _clean_uuid(
        registration_id,
        "registration ID",
    )

    class_record = _get_class(
        class_code
    )

    if not class_record:
        raise ValueError(
            "Class not found."
        )

    if (
        class_record["status"]
        in {
            "Closed",
            "Archived",
        }
    ):
        raise ValueError(
            "Learners cannot be enrolled "
            "into a Closed or Archived class."
        )

    with engine.begin() as connection:
        registration = connection.execute(
            text("""
                SELECT *
                FROM public.registrations
                WHERE id = CAST(
                    :registration_id
                    AS uuid
                )
                LIMIT 1
            """),
            {
                "registration_id": (
                    registration_id
                )
            },
        ).mappings().first()

        if not registration:
            raise ValueError(
                "Registration not found."
            )

        if (
            registration[
                "registration_status"
            ]
            not in
            ELIGIBLE_REGISTRATION_STATUSES
        ):
            raise ValueError(
                "This learner's registration "
                "status is not eligible for "
                "class enrolment."
            )

        if (
            registration["course_code"]
            != class_record["course_code"]
        ):
            raise ValueError(
                "The learner is registered "
                "for a different course."
            )

        if (
            class_record["cycle_code"]
            and registration["cycle"]
            and class_record["cycle_code"]
                != registration["cycle"]
        ):
            raise ValueError(
                "The learner is registered "
                "for a different cycle."
            )

        existing_active = (
            connection.execute(
                text("""
                    SELECT
                        ce.id,
                        c.class_code
                    FROM public.class_enrolments ce
                    JOIN public.classes c
                        ON c.id =
                           ce.class_id
                    WHERE
                        ce.registration_id =
                            CAST(
                                :registration_id
                                AS uuid
                            )
                        AND ce.status =
                            'Active'
                    LIMIT 1
                """),
                {
                    "registration_id": (
                        registration_id
                    )
                },
            ).mappings().first()
        )

        if existing_active:
            if (
                existing_active[
                    "class_code"
                ]
                == class_code
            ):
                row = connection.execute(
                    text("""
                        SELECT *
                        FROM public.class_enrolments
                        WHERE id =
                              :enrolment_id
                    """),
                    {
                        "enrolment_id": (
                            existing_active[
                                "id"
                            ]
                        )
                    },
                ).mappings().first()

                return dict(
                    row
                )

            raise ValueError(
                "This learner is already "
                "actively enrolled in class "
                f"{existing_active['class_code']}."
            )

        row = connection.execute(
            text("""
                INSERT INTO public.class_enrolments (
                    class_id,
                    registration_id,
                    status
                )
                VALUES (
                    :class_id,
                    CAST(
                        :registration_id
                        AS uuid
                    ),
                    'Active'
                )
                ON CONFLICT (
                    class_id,
                    registration_id
                )
                DO UPDATE SET
                    status = 'Active',
                    enrolled_at = NOW(),
                    updated_at = NOW()
                RETURNING *
            """),
            {
                "class_id": (
                    class_record["id"]
                ),
                "registration_id": (
                    registration_id
                ),
            },
        ).mappings().first()

    record = dict(
        row
    )

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code=(
            "LEARNER_ENROLLED_IN_CLASS"
        ),
        entity_type="CLASS_ENROLMENT",
        entity_id=record["id"],
        description=(
            "Learner enrolled in class."
        ),
        after_data=record,
        metadata={
            "class_code": class_code,
            "registration_id": (
                registration_id
            ),
        },
    )

    return record


def remove_registration_from_class(
    *,
    actor_staff_code: str,
    class_code: str,
    registration_id: str,
) -> dict:
    class_code = _clean_code(
        class_code,
        "Class code",
    )

    registration_id = _clean_uuid(
        registration_id,
        "registration ID",
    )

    class_record = _get_class(
        class_code
    )

    if not class_record:
        raise ValueError(
            "Class not found."
        )

    with engine.begin() as connection:
        before = connection.execute(
            text("""
                SELECT *
                FROM public.class_enrolments
                WHERE
                    class_id =
                        :class_id
                    AND registration_id =
                        CAST(
                            :registration_id
                            AS uuid
                        )
                LIMIT 1
            """),
            {
                "class_id": (
                    class_record["id"]
                ),
                "registration_id": (
                    registration_id
                ),
            },
        ).mappings().first()

        if not before:
            raise ValueError(
                "Class enrolment not found."
            )

        row = connection.execute(
            text("""
                UPDATE public.class_enrolments
                SET
                    status = 'Removed',
                    updated_at = NOW()
                WHERE
                    class_id =
                        :class_id
                    AND registration_id =
                        CAST(
                            :registration_id
                            AS uuid
                        )
                RETURNING *
            """),
            {
                "class_id": (
                    class_record["id"]
                ),
                "registration_id": (
                    registration_id
                ),
            },
        ).mappings().first()

    before = dict(
        before
    )
    record = dict(
        row
    )

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code=(
            "LEARNER_REMOVED_FROM_CLASS"
        ),
        entity_type="CLASS_ENROLMENT",
        entity_id=record["id"],
        description=(
            "Learner removed from class."
        ),
        before_data=before,
        after_data=record,
        metadata={
            "class_code": class_code,
            "registration_id": (
                registration_id
            ),
        },
    )

    return record

