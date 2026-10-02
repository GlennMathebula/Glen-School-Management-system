from __future__ import annotations

from sqlalchemy import text

from app.database import engine


def _clean(value: str | None) -> str | None:
    value = str(value or "").strip()
    return value or None


def list_students(
    *,
    search: str | None = None,
    course_code: str | None = None,
    registration_status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    search = _clean(search)
    course_code = _clean(course_code)
    registration_status = _clean(registration_status)
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))

    filters: list[str] = []
    params: dict = {"limit": limit, "offset": offset}

    if search:
        filters.append(
            "("
            "a.student_number ILIKE :search "
            "OR a.first_name ILIKE :search "
            "OR a.last_name ILIKE :search "
            "OR a.email ILIKE :search "
            "OR a.national_id ILIKE :search"
            ")"
        )
        params["search"] = f"%{search}%"

    if course_code:
        filters.append("r.course_code = :course_code")
        params["course_code"] = course_code

    if registration_status:
        filters.append(
            "r.registration_status = :registration_status"
        )
        params["registration_status"] = registration_status

    where_sql = ""
    if filters:
        where_sql = "WHERE " + "\nAND ".join(filters)

    base_sql = f"""
        FROM public.applications a

        LEFT JOIN LATERAL (
            SELECT rr.*
            FROM public.registrations rr
            WHERE rr.student_number = a.student_number
            ORDER BY rr.created_at DESC NULLS LAST
            LIMIT 1
        ) r ON TRUE

        LEFT JOIN public.courses c
            ON c.course_code = r.course_code

        LEFT JOIN public.student_accounts sa
            ON sa.student_number = a.student_number

        {where_sql}
    """

    with engine.connect() as connection:
        total = connection.execute(
            text(f"SELECT COUNT(*) {base_sql}"),
            params,
        ).scalar_one()

        rows = connection.execute(
            text(
                f"""
                SELECT
                    a.id AS application_id,
                    a.student_number,
                    a.first_name,
                    a.middle_name,
                    a.last_name,
                    a.email,
                    a.cell_number,
                    a.national_id,
                    a.app_status,
                    a.created_at AS application_created_at,

                    r.id AS registration_id,
                    r.course_code,
                    c.course_name,
                    c.assessment_type,
                    r.registration_status,
                    r.cycle,
                    r.program_start_date,
                    r.expected_completion_date,
                    r.eisa_eligible,

                    sa.account_status

                {base_sql}

                ORDER BY
                    a.last_name,
                    a.first_name,
                    a.student_number

                LIMIT :limit
                OFFSET :offset
                """
            ),
            params,
        ).mappings().all()

    return {
        "count": len(rows),
        "total": int(total),
        "limit": limit,
        "offset": offset,
        "students": [dict(row) for row in rows],
    }


def get_student_record(student_number: str) -> dict | None:
    student_number = str(student_number or "").strip()

    if not student_number:
        raise ValueError("Student number is required.")

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT
                    a.*,

                    r.id AS registration_id,
                    r.course_code,
                    r.registration_date,
                    r.registration_status,
                    r.funding_type,
                    r.cycle,
                    r.program_start_date,
                    r.expected_completion_date,
                    r.eisa_eligible,

                    c.course_name,
                    c.qualification_type,
                    c.nqf_level,
                    c.credits,
                    c.assessment_type,
                    c.sdp_code,
                    c.aqp_name,

                    sa.account_status,
                    sa.created_at AS student_account_created_at

                FROM public.applications a

                LEFT JOIN LATERAL (
                    SELECT rr.*
                    FROM public.registrations rr
                    WHERE rr.student_number = a.student_number
                    ORDER BY rr.created_at DESC NULLS LAST
                    LIMIT 1
                ) r ON TRUE

                LEFT JOIN public.courses c
                    ON c.course_code = r.course_code

                LEFT JOIN public.student_accounts sa
                    ON sa.student_number = a.student_number

                WHERE a.student_number = :student_number
                LIMIT 1
                """
            ),
            {"student_number": student_number},
        ).mappings().first()

    return dict(row) if row else None


def get_student_document_inventory(
    student_number: str,
) -> dict:
    student_number = str(student_number or "").strip()

    if not student_number:
        raise ValueError("Student number is required.")

    preferred_columns = [
        "id",
        "student_number",
        "document_type",
        "document_name",
        "document_code",
        "file_name",
        "filename",
        "mime_type",
        "status",
        "verification_status",
        "file_path",
        "storage_path",
        "uploaded_at",
        "created_at",
        "updated_at",
    ]

    with engine.connect() as connection:
        tables = connection.execute(
            text(
                """
                SELECT DISTINCT c.table_name
                FROM information_schema.columns c
                WHERE c.table_schema = 'public'
                  AND c.column_name = 'student_number'
                  AND (
                        c.table_name ILIKE '%document%'
                        OR c.table_name ILIKE '%file%'
                  )
                ORDER BY c.table_name
                """
            )
        ).scalars().all()

        records: list[dict] = []

        for table_name in tables:
            column_rows = connection.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = :table_name
                    ORDER BY ordinal_position
                    """
                ),
                {"table_name": table_name},
            ).scalars().all()

            selected = [
                name
                for name in preferred_columns
                if name in set(column_rows)
            ]

            if "student_number" not in selected:
                selected.insert(0, "student_number")

            quoted_table = '"' + table_name.replace('"', '""') + '"'
            select_sql = ", ".join(
                '"' + name.replace('"', '""') + '"'
                for name in selected
            )

            rows = connection.execute(
                text(
                    f"""
                    SELECT {select_sql}
                    FROM public.{quoted_table}
                    WHERE student_number = :student_number
                    LIMIT 100
                    """
                ),
                {"student_number": student_number},
            ).mappings().all()

            records.append(
                {
                    "source_table": table_name,
                    "count": len(rows),
                    "documents": [dict(row) for row in rows],
                }
            )

    return {
        "student_number": student_number,
        "sources": records,
        "total_documents": sum(
            item["count"] for item in records
        ),
    }



# ============================================================
# ADMIN STUDENT RECORD UPDATE
# ============================================================

ADMIN_STUDENT_EDITABLE_FIELDS = {
    "first_name",
    "middle_name",
    "last_name",
    "national_id",
    "alternate_id",
    "birth_date",
    "email",
    "cell_number",
    "phone_number",
    "home_addr_1",
    "home_addr_2",
    "home_addr_3",
    "home_postal_code",
    "postal_addr_1",
    "postal_addr_2",
    "postal_addr_3",
    "postal_code",
    "province_code",
    "municipality",
    "ward",
    "next_of_kin_surname",
    "next_of_kin_full_name",
    "next_of_kin_cell",
    "next_of_kin_relationship",
    "next_of_kin_email",
}

ADMIN_REQUIRED_STUDENT_FIELDS = {
    "first_name",
    "last_name",
    "email",
}

ADMIN_REGISTRATION_STATUSES = {
    "Registered",
    "In Progress",
    "Suspended",
    "Withdrawn",
    "Cancelled",
    "Completed",
}


def update_student_record(
    student_number: str,
    changes: dict,
) -> dict:

    student_number = str(
        student_number or ""
    ).strip()

    if not student_number:
        raise ValueError(
            "Student number is required."
        )

    if not get_student_record(
        student_number
    ):
        raise ValueError(
            "Student record not found."
        )

    changes = dict(
        changes or {}
    )

    registration_status = changes.pop(
        "registration_status",
        None,
    )

    application_changes = {
        key: value
        for key, value in changes.items()
        if key in ADMIN_STUDENT_EDITABLE_FIELDS
    }

    for required in ADMIN_REQUIRED_STUDENT_FIELDS:
        if (
            required in application_changes
            and not str(
                application_changes[required]
                or ""
            ).strip()
        ):
            raise ValueError(
                f"{required.replace('_', ' ').title()} "
                "cannot be blank."
            )

    if (
        registration_status is not None
        and registration_status
        not in ADMIN_REGISTRATION_STATUSES
    ):
        raise ValueError(
            "Invalid registration status."
        )

    if (
        not application_changes
        and registration_status is None
    ):
        raise ValueError(
            "No student changes were supplied."
        )

    try:
        with engine.begin() as connection:

            if application_changes:
                assignments = []
                params = {
                    "student_number": student_number,
                }

                for index, (
                    field_name,
                    value,
                ) in enumerate(
                    application_changes.items()
                ):
                    parameter = f"value_{index}"

                    assignments.append(
                        f"{field_name} = :{parameter}"
                    )

                    params[parameter] = value

                assignments.append(
                    "updated_at = now()"
                )

                connection.execute(
                    text(
                        f"""
                        UPDATE public.applications
                        SET {", ".join(assignments)}
                        WHERE student_number = :student_number
                        """
                    ),
                    params,
                )

            if registration_status is not None:
                connection.execute(
                    text(
                        """
                        UPDATE public.registrations
                        SET
                            registration_status = :registration_status,
                            updated_at = now()
                        WHERE student_number = :student_number
                        """
                    ),
                    {
                        "student_number": student_number,
                        "registration_status": registration_status,
                    },
                )

    except Exception as error:
        raise ValueError(
            "Student record could not be updated. "
            "Check that identity and email values "
            "are not already in use."
        ) from error

    updated = get_student_record(
        student_number
    )

    if not updated:
        raise RuntimeError(
            "Student record was updated but "
            "could not be reloaded."
        )

    return updated


# V3.4 STUDENT RECORD UPDATE FIX
from sqlalchemy.exc import IntegrityError


V34_ADMIN_STUDENT_EDITABLE_FIELDS = {
    "first_name",
    "middle_name",
    "last_name",
    "national_id",
    "alternate_id",
    "birth_date",
    "email",
    "cell_number",
    "phone_number",
    "home_addr_1",
    "home_addr_2",
    "home_addr_3",
    "home_postal_code",
    "postal_addr_1",
    "postal_addr_2",
    "postal_addr_3",
    "postal_code",
    "province_code",
    "next_of_kin_surname",
    "next_of_kin_full_name",
    "next_of_kin_cell",
    "next_of_kin_relationship",
    "next_of_kin_email",
}

V34_REQUIRED_STUDENT_FIELDS = {
    "first_name",
    "last_name",
    "email",
}

V34_REGISTRATION_STATUSES = {
    "Registered",
    "In Progress",
    "Suspended",
    "Withdrawn",
    "Cancelled",
    "Completed",
}


def _v34_clean_student_value(
    field_name: str,
    value,
):
    if isinstance(value, str):
        value = value.strip()

        if (
            value == ""
            and field_name
            not in V34_REQUIRED_STUDENT_FIELDS
        ):
            return None

    return value


def _v34_check_student_duplicates(
    connection,
    *,
    student_number: str,
    application_changes: dict,
) -> None:
    email = application_changes.get(
        "email"
    )

    if email:
        duplicate = connection.execute(
            text(
                """
                SELECT student_number
                FROM public.applications
                WHERE lower(trim(email))
                    = lower(trim(:email))
                  AND student_number
                    <> :student_number
                LIMIT 1
                """
            ),
            {
                "email": email,
                "student_number": (
                    student_number
                ),
            },
        ).scalar()

        if duplicate:
            raise ValueError(
                "That email address is already "
                "used by another applicant/student."
            )

    national_id = application_changes.get(
        "national_id"
    )

    if national_id:
        duplicate = connection.execute(
            text(
                """
                SELECT student_number
                FROM public.applications
                WHERE trim(national_id)
                    = trim(:national_id)
                  AND student_number
                    <> :student_number
                LIMIT 1
                """
            ),
            {
                "national_id": (
                    national_id
                ),
                "student_number": (
                    student_number
                ),
            },
        ).scalar()

        if duplicate:
            raise ValueError(
                "That National ID is already "
                "used by another applicant/student."
            )


def update_student_record(
    student_number: str,
    changes: dict,
) -> dict:
    student_number = str(
        student_number or ""
    ).strip()

    if not student_number:
        raise ValueError(
            "Student number is required."
        )

    current = get_student_record(
        student_number
    )

    if not current:
        raise ValueError(
            "Student record not found."
        )

    changes = dict(
        changes or {}
    )

    # Legacy desktop fields. These columns do not exist
    # in the authoritative public.applications table.
    changes.pop(
        "municipality",
        None,
    )
    changes.pop(
        "ward",
        None,
    )

    registration_status = (
        changes.pop(
            "registration_status",
            None,
        )
    )

    if (
        registration_status
        in ("", None)
    ):
        registration_status = None

    if (
        registration_status
        is not None
        and registration_status
        not in V34_REGISTRATION_STATUSES
    ):
        raise ValueError(
            "Invalid registration status."
        )

    application_changes = {}

    for key, value in changes.items():
        if (
            key
            not in
            V34_ADMIN_STUDENT_EDITABLE_FIELDS
        ):
            continue

        cleaned = (
            _v34_clean_student_value(
                key,
                value,
            )
        )

        if (
            key
            in V34_REQUIRED_STUDENT_FIELDS
            and not cleaned
        ):
            raise ValueError(
                f"{key.replace('_', ' ').title()} "
                "cannot be blank."
            )

        application_changes[
            key
        ] = cleaned

    if (
        not application_changes
        and registration_status
        is None
    ):
        raise ValueError(
            "No student changes were supplied."
        )

    try:
        with engine.begin() as connection:
            _v34_check_student_duplicates(
                connection,
                student_number=(
                    student_number
                ),
                application_changes=(
                    application_changes
                ),
            )

            if application_changes:
                assignments = []
                params = {
                    "student_number": (
                        student_number
                    ),
                }

                for (
                    index,
                    (
                        field_name,
                        value,
                    ),
                ) in enumerate(
                    application_changes.items()
                ):
                    parameter = (
                        f"value_{index}"
                    )

                    assignments.append(
                        f"{field_name} = :{parameter}"
                    )

                    params[
                        parameter
                    ] = value

                assignments.append(
                    "updated_at = now()"
                )

                connection.execute(
                    text(
                        f"""
                        UPDATE public.applications
                        SET
                            {", ".join(assignments)}
                        WHERE
                            student_number
                            = :student_number
                        """
                    ),
                    params,
                )

            if (
                registration_status
                is not None
            ):
                registration = (
                    connection.execute(
                        text(
                            """
                            SELECT id
                            FROM public.registrations
                            WHERE student_number
                                = :student_number
                            LIMIT 1
                            """
                        ),
                        {
                            "student_number": (
                                student_number
                            ),
                        },
                    ).first()
                )

                if not registration:
                    raise ValueError(
                        "This applicant has not been "
                        "registered yet. Application "
                        "status must be managed under "
                        "Admissions."
                    )

                connection.execute(
                    text(
                        """
                        UPDATE public.registrations
                        SET
                            registration_status
                                = :registration_status,
                            updated_at = now()
                        WHERE
                            student_number
                                = :student_number
                        """
                    ),
                    {
                        "student_number": (
                            student_number
                        ),
                        "registration_status": (
                            registration_status
                        ),
                    },
                )

    except ValueError:
        raise

    except IntegrityError as error:
        message = str(
            getattr(
                error,
                "orig",
                error,
            )
        ).lower()

        if "email" in message:
            raise ValueError(
                "That email address is already "
                "used by another applicant/student."
            ) from error

        if (
            "national_id" in message
            or "national id" in message
        ):
            raise ValueError(
                "That National ID is already "
                "used by another applicant/student."
            ) from error

        raise ValueError(
            "Student record could not be updated "
            "because a database rule was not met."
        ) from error

    except Exception as error:
        raise ValueError(
            "Student record could not be updated: "
            f"{error}"
        ) from error

    updated = get_student_record(
        student_number
    )

    if not updated:
        raise RuntimeError(
            "Student record was updated but "
            "could not be reloaded."
        )

    return updated
