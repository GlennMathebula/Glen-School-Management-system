from sqlalchemy import text

from app.database import engine

EDITABLE_CONTACT_FIELDS = {
    "email",
    "phone_number",
    "cell_number",
    "home_addr_1",
    "home_addr_2",
    "home_addr_3",
    "home_postal_code",
    "postal_addr_1",
    "postal_addr_2",
    "postal_addr_3",
    "postal_code",
}


# ============================================================
# GET SETTINGS
# ============================================================

def get_student_settings(
    student_number: str,
) -> dict:

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                INSERT INTO
                    public.student_settings (
                        student_number
                    )

                VALUES (
                    :student_number
                )

                ON CONFLICT (
                    student_number
                )
                DO NOTHING
                """
            ),
            {
                "student_number": student_number,
            },
        )

        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        a.student_number,
                        a.first_name,
                        a.middle_name,
                        a.last_name,
                        a.national_id,
                        a.alternate_id,
                        a.alt_id_type,
                        a.birth_date,

                        a.email,
                        a.phone_number,
                        a.cell_number,

                        a.home_addr_1,
                        a.home_addr_2,
                        a.home_addr_3,
                        a.home_postal_code,

                        a.postal_addr_1,
                        a.postal_addr_2,
                        a.postal_addr_3,
                        a.postal_code,

                        a.popi_agree,
                        a.popi_date,

                        r.course_code,
                        r.cycle,
                        r.registration_status,
                        r.registration_date,
                        r.funding_type,

                        c.course_name,

                        sa.account_status,
                        sa.must_change_password,
                        sa.pin_created,
                        sa.password_changed_at,
                        sa.pin_changed_at,

                        ss.preferred_notification_channel,
                        ss.preferred_language

                    FROM
                        public.applications a

                    LEFT JOIN LATERAL (
                        SELECT
                            r2.*

                        FROM
                            public.registrations r2

                        WHERE
                            r2.student_number =
                                a.student_number

                        ORDER BY
                            r2.registration_date DESC,
                            r2.created_at DESC

                        LIMIT 1
                    ) r
                        ON true

                    LEFT JOIN
                        public.courses c
                        ON c.course_code =
                            r.course_code

                    LEFT JOIN
                        public.student_accounts sa
                        ON sa.student_number =
                            a.student_number

                    LEFT JOIN
                        public.student_settings ss
                        ON ss.student_number =
                            a.student_number

                    WHERE
                        a.student_number =
                            :student_number

                    LIMIT 1
                    """
                ),
                {
                    "student_number": student_number,
                },
            )
            .mappings()
            .first()
        )

    if not row:

        raise ValueError(
            "Student record was not found."
        )

    data = dict(row)

    return {
        "profile": {
            "student_number": data.get(
                "student_number"
            ),
            "first_name": data.get(
                "first_name"
            ),
            "middle_name": data.get(
                "middle_name"
            ),
            "last_name": data.get(
                "last_name"
            ),
            "national_id": data.get(
                "national_id"
            ),
            "alternate_id": data.get(
                "alternate_id"
            ),
            "alt_id_type": data.get(
                "alt_id_type"
            ),
            "birth_date": data.get(
                "birth_date"
            ),
        },

        "contact": {
            "email": data.get(
                "email"
            ),
            "phone_number": data.get(
                "phone_number"
            ),
            "cell_number": data.get(
                "cell_number"
            ),

            "home_addr_1": data.get(
                "home_addr_1"
            ),
            "home_addr_2": data.get(
                "home_addr_2"
            ),
            "home_addr_3": data.get(
                "home_addr_3"
            ),
            "home_postal_code": data.get(
                "home_postal_code"
            ),

            "postal_addr_1": data.get(
                "postal_addr_1"
            ),
            "postal_addr_2": data.get(
                "postal_addr_2"
            ),
            "postal_addr_3": data.get(
                "postal_addr_3"
            ),
            "postal_code": data.get(
                "postal_code"
            ),
        },

        "registration": {
            "course_code": data.get(
                "course_code"
            ),
            "course_name": data.get(
                "course_name"
            ),
            "cycle": data.get(
                "cycle"
            ),
            "registration_status": data.get(
                "registration_status"
            ),
            "registration_date": data.get(
                "registration_date"
            ),
            "funding_type": data.get(
                "funding_type"
            ),
        },

        "privacy": {
            "popi_agree": data.get(
                "popi_agree"
            ),
            "popi_date": data.get(
                "popi_date"
            ),
        },

        "security": {
            "account_status": data.get(
                "account_status"
            ),
            "must_change_password": data.get(
                "must_change_password"
            ),
            "pin_created": data.get(
                "pin_created"
            ),
            "password_changed_at": data.get(
                "password_changed_at"
            ),
            "pin_changed_at": data.get(
                "pin_changed_at"
            ),
        },

        "preferences": {
            "preferred_notification_channel": (
                data.get(
                    "preferred_notification_channel"
                )
            ),
            "preferred_language": data.get(
                "preferred_language"
            ),
        },
    }


# ============================================================
# UPDATE CONTACT DETAILS
# ============================================================

def update_student_contact_details(
    student_number: str,
    changes: dict,
) -> dict:

    clean_changes = {
        key: (
            str(value).strip()
            if value is not None
            else None
        )
        for key, value in changes.items()
        if key in EDITABLE_CONTACT_FIELDS
    }

    if not clean_changes:

        raise ValueError(
            "No contact changes were supplied."
        )

    with engine.begin() as connection:

        current = (
            connection.execute(
                text(
                    """
                    SELECT
                        email,
                        phone_number,
                        cell_number,

                        home_addr_1,
                        home_addr_2,
                        home_addr_3,
                        home_postal_code,

                        postal_addr_1,
                        postal_addr_2,
                        postal_addr_3,
                        postal_code

                    FROM
                        public.applications

                    WHERE
                        student_number =
                            :student_number

                    FOR UPDATE
                    """
                ),
                {
                    "student_number": student_number,
                },
            )
            .mappings()
            .first()
        )

        if not current:

            raise ValueError(
                "Student record was not found."
            )

        changed_fields = {}

        for field_name, new_value in (
            clean_changes.items()
        ):

            old_value = current.get(
                field_name
            )

            old_normalized = (
                str(old_value).strip()
                if old_value is not None
                else None
            )

            if old_normalized == new_value:

                continue

            changed_fields[
                field_name
            ] = {
                "old": old_normalized,
                "new": new_value,
            }

        if not changed_fields:

            return {
                "changed": False,
                "changed_fields": [],
            }

        set_parts = []

        parameters = {
            "student_number": student_number,
        }

        for field_name, values in (
            changed_fields.items()
        ):

            set_parts.append(
                f"{field_name} = :{field_name}"
            )

            parameters[
                field_name
            ] = values["new"]

        set_parts.append(
            "updated_at = now()"
        )

        connection.execute(
            text(
                f"""
                UPDATE
                    public.applications

                SET
                    {", ".join(set_parts)}

                WHERE
                    student_number =
                        :student_number
                """
            ),
            parameters,
        )

        for field_name, values in (
            changed_fields.items()
        ):

            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.student_profile_change_log (
                            student_number,
                            field_name,
                            old_value,
                            new_value,
                            changed_by,
                            changed_at
                        )

                    VALUES (
                        :student_number,
                        :field_name,
                        :old_value,
                        :new_value,
                        'Student',
                        now()
                    )
                    """
                ),
                {
                    "student_number": student_number,
                    "field_name": field_name,
                    "old_value": values["old"],
                    "new_value": values["new"],
                },
            )

    return {
        "changed": True,
        "changed_fields": list(
            changed_fields.keys()
        ),
    }


# ============================================================
# UPDATE PREFERENCES
# ============================================================

def update_student_preferences(
    student_number: str,
    preferred_notification_channel: str,
    preferred_language: str | None,
) -> dict:

    preferred_language = (
        str(
            preferred_language
        ).strip()
        if preferred_language
        else None
    )

    with engine.begin() as connection:

        row = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.student_settings (
                            student_number,
                            preferred_notification_channel,
                            preferred_language,
                            created_at,
                            updated_at
                        )

                    VALUES (
                        :student_number,
                        :preferred_notification_channel,
                        :preferred_language,
                        now(),
                        now()
                    )

                    ON CONFLICT (
                        student_number
                    )

                    DO UPDATE SET
                        preferred_notification_channel =
                            EXCLUDED.preferred_notification_channel,

                        preferred_language =
                            EXCLUDED.preferred_language,

                        updated_at =
                            now()

                    RETURNING
                        student_number,
                        preferred_notification_channel,
                        preferred_language,
                        updated_at
                    """
                ),
                {
                    "student_number": student_number,
                    "preferred_notification_channel": (
                        preferred_notification_channel
                    ),
                    "preferred_language": (
                        preferred_language
                    ),
                },
            )
            .mappings()
            .first()
        )

    return dict(row)