from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database import engine
from app.services.staff_audit_service import create_staff_audit_log


APPEAL_STATUSES = {
    "Pending",
    "Under Review",
    "Upheld",
    "Dismissed",
    "Withdrawn",
    "Closed",
}
PLACEMENT_STATUSES = {
    "Planned",
    "Active",
    "Completed",
    "Terminated",
    "Cancelled",
}
ATTENDANCE_STATUSES = {
    "Present",
    "Absent",
    "Late",
    "Excused",
}
SUBMISSION_STATUSES = {
    "Submitted",
    "Reviewed",
    "Returned",
    "Approved",
}
SUPERVISOR_REPORT_STATUSES = {
    "Draft",
    "Submitted",
    "Reviewed",
}
EISA_SITTING_STATUSES = {
    "Draft",
    "Published",
    "Completed",
    "Cancelled",
}
EISA_ADMISSION_STATUSES = {
    "Admitted",
    "Not Admitted",
    "Withdrawn",
}
EISA_ATTENDANCE_STATUSES = {
    "Pending",
    "Present",
    "Absent",
    "Late",
    "Excused",
}
QA_ACTION_STATUSES = {
    "Open",
    "In Progress",
    "Completed",
    "Overdue",
    "Closed",
}
QA_SOURCE_TYPES = {
    "Compliance",
    "Assessment",
    "Attendance",
    "Internal QA",
    "Other",
}


def _uuid(value: str, label: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid {label}.") from error


def _clean(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def _fetch_one(sql: str, params: dict) -> dict | None:
    with engine.connect() as connection:
        row = connection.execute(
            text(sql),
            params,
        ).mappings().first()
    return dict(row) if row else None


def _fetch_all(sql: str, params: dict) -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(
            text(sql),
            params,
        ).mappings().all()
    return [dict(row) for row in rows]


def _reference(prefix: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    tail = uuid4().hex[:6].upper()
    return f"{prefix}-{stamp}-{tail}"


def _audit(
    *,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    description: str,
    after_data: dict | None = None,
) -> None:
    try:
        create_staff_audit_log(
            actor_staff_code=actor,
            action_code=action,
            module_code="QA_COMPLIANCE",
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            before_data=None,
            after_data=after_data,
            metadata=None,
        )
    except Exception as error:
        print(
            "WARNING: QA/Compliance action succeeded "
            f"but audit logging failed: {error}"
        )


def _registration(registration_id: str) -> dict:
    registration_id = _uuid(
        registration_id,
        "registration_id",
    )
    row = _fetch_one(
        """
        SELECT
            r.id,
            r.student_number,
            r.course_code,
            r.cycle,
            r.registration_status,
            r.eisa_eligible,
            c.course_name,
            c.assessment_type
        FROM public.registrations r
        JOIN public.courses c
            ON c.course_code = r.course_code
        WHERE r.id = CAST(:id AS uuid)
        LIMIT 1
        """,
        {"id": registration_id},
    )
    if not row:
        raise ValueError("Registration not found.")
    return row


def list_appeals(
    *,
    cycle_code: str | None = None,
    course_code: str | None = None,
    status: str | None = None,
) -> list[dict]:
    return _fetch_all(
        """
        SELECT
            aa.*,
            r.student_number,
            r.course_code,
            r.cycle AS cycle_code,
            c.course_name,
            CONCAT_WS(
                ' ',
                a.first_name,
                a.middle_name,
                a.last_name
            ) AS learner_name
        FROM public.assessment_appeals aa
        JOIN public.registrations r
            ON r.id = aa.registration_id
        JOIN public.applications a
            ON a.id = r.application_id
        JOIN public.courses c
            ON c.course_code = r.course_code
        WHERE
            (:cycle_code IS NULL OR r.cycle = :cycle_code)
            AND (:course_code IS NULL OR r.course_code = :course_code)
            AND (:status IS NULL OR aa.status = :status)
        ORDER BY aa.lodged_date DESC, aa.created_at DESC
        """,
        {
            "cycle_code": _clean(cycle_code),
            "course_code": _clean(course_code),
            "status": _clean(status),
        },
    )


def create_appeal(
    payload: dict,
    *,
    actor: str,
) -> dict:
    registration = _registration(
        payload["registration_id"]
    )

    scope = str(
        payload["assessment_scope"]
    ).strip()

    if scope not in {"Module", "FISA", "EISA"}:
        raise ValueError(
            "assessment_scope must be Module, FISA or EISA."
        )

    mark_id = _clean(payload.get("mark_id"))
    summative_id = _clean(
        payload.get("summative_assessment_id")
    )

    if scope == "Module":
        if not mark_id or summative_id:
            raise ValueError(
                "Module appeals require mark_id only."
            )

        mark = _fetch_one(
            """
            SELECT mk.id
            FROM public.marks mk
            JOIN public.module_registrations mr
                ON mr.id = mk.module_registration_id
            WHERE
                mk.id = CAST(:mark_id AS uuid)
                AND mr.registration_id =
                    CAST(:registration_id AS uuid)
            LIMIT 1
            """,
            {
                "mark_id": _uuid(mark_id, "mark_id"),
                "registration_id": registration["id"],
            },
        )
        if not mark:
            raise ValueError(
                "The selected mark does not belong to this registration."
            )

    else:
        if not summative_id or mark_id:
            raise ValueError(
                "FISA/EISA appeals require summative_assessment_id only."
            )

        assessment = _fetch_one(
            """
            SELECT id, assessment_type
            FROM public.summative_assessments
            WHERE
                id = CAST(:id AS uuid)
                AND registration_id =
                    CAST(:registration_id AS uuid)
            LIMIT 1
            """,
            {
                "id": _uuid(
                    summative_id,
                    "summative_assessment_id",
                ),
                "registration_id": registration["id"],
            },
        )

        if not assessment:
            raise ValueError(
                "The selected summative assessment does not "
                "belong to this registration."
            )

        if assessment["assessment_type"] != scope:
            raise ValueError(
                "assessment_scope does not match the selected assessment."
            )

    appeal_reference = _reference("APL")

    params = {
        "appeal_reference": appeal_reference,
        "registration_id": registration["id"],
        "assessment_scope": scope,
        "mark_id": (
            _uuid(mark_id, "mark_id")
            if mark_id
            else None
        ),
        "summative_id": (
            _uuid(
                summative_id,
                "summative_assessment_id",
            )
            if summative_id
            else None
        ),
        "lodged_date": payload.get("lodged_date"),
        "reason": str(payload["reason"]).strip(),
        "actor": actor,
    }

    if not params["reason"]:
        raise ValueError("Appeal reason is required.")

    try:
        with engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    INSERT INTO public.assessment_appeals (
                        appeal_reference,
                        registration_id,
                        assessment_scope,
                        mark_id,
                        summative_assessment_id,
                        lodged_date,
                        reason,
                        created_by
                    )
                    VALUES (
                        :appeal_reference,
                        CAST(:registration_id AS uuid),
                        :assessment_scope,
                        CAST(:mark_id AS uuid),
                        CAST(:summative_id AS uuid),
                        COALESCE(:lodged_date, CURRENT_DATE),
                        :reason,
                        :actor
                    )
                    RETURNING *
                    """
                ),
                params,
            ).mappings().one()
    except IntegrityError as error:
        raise ValueError(
            "The appeal could not be created."
        ) from error

    result = dict(row)

    _audit(
        actor=actor,
        action="ASSESSMENT_APPEAL_CREATED",
        entity_type="ASSESSMENT_APPEAL",
        entity_id=str(result["id"]),
        description="Assessment appeal created.",
        after_data=result,
    )

    return result


def update_appeal(
    appeal_id: str,
    payload: dict,
    *,
    actor: str,
) -> dict:
    appeal_id = _uuid(
        appeal_id,
        "appeal_id",
    )

    status = _clean(
        payload.get("status")
    )

    if status and status not in APPEAL_STATUSES:
        raise ValueError("Invalid appeal status.")

    outcome = _clean(
        payload.get("outcome")
    )

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                UPDATE public.assessment_appeals
                SET
                    status = COALESCE(:status, status),
                    outcome = COALESCE(:outcome, outcome),
                    reviewed_by = CASE
                        WHEN :status IN (
                            'Under Review',
                            'Upheld',
                            'Dismissed',
                            'Closed'
                        )
                        THEN :actor
                        ELSE reviewed_by
                    END,
                    reviewed_at = CASE
                        WHEN :status IN (
                            'Upheld',
                            'Dismissed',
                            'Closed'
                        )
                        THEN now()
                        ELSE reviewed_at
                    END,
                    updated_at = now()
                WHERE id = CAST(:id AS uuid)
                RETURNING *
                """
            ),
            {
                "id": appeal_id,
                "status": status,
                "outcome": outcome,
                "actor": actor,
            },
        ).mappings().first()

    if not row:
        raise ValueError("Appeal not found.")

    result = dict(row)

    _audit(
        actor=actor,
        action="ASSESSMENT_APPEAL_UPDATED",
        entity_type="ASSESSMENT_APPEAL",
        entity_id=appeal_id,
        description="Assessment appeal updated.",
        after_data=result,
    )

    return result


def list_placements(
    *,
    cycle_code: str | None = None,
    course_code: str | None = None,
    status: str | None = None,
) -> list[dict]:
    return _fetch_all(
        """
        SELECT
            wp.*,
            r.student_number,
            r.course_code,
            r.cycle AS cycle_code,
            c.course_name,
            CONCAT_WS(
                ' ',
                a.first_name,
                a.middle_name,
                a.last_name
            ) AS learner_name
        FROM public.workplace_placements wp
        JOIN public.registrations r
            ON r.id = wp.registration_id
        JOIN public.applications a
            ON a.id = r.application_id
        JOIN public.courses c
            ON c.course_code = r.course_code
        WHERE
            (:cycle_code IS NULL OR r.cycle = :cycle_code)
            AND (:course_code IS NULL OR r.course_code = :course_code)
            AND (:status IS NULL OR wp.status = :status)
        ORDER BY wp.placement_start_date DESC, learner_name
        """,
        {
            "cycle_code": _clean(cycle_code),
            "course_code": _clean(course_code),
            "status": _clean(status),
        },
    )


def create_placement(
    payload: dict,
    *,
    actor: str,
) -> dict:
    registration = _registration(
        payload["registration_id"]
    )

    status = payload.get(
        "status",
        "Planned",
    )
    if status not in PLACEMENT_STATUSES:
        raise ValueError("Invalid placement status.")

    start = payload["placement_start_date"]
    end = payload.get("placement_end_date")
    if end and end < start:
        raise ValueError(
            "placement_end_date cannot be before placement_start_date."
        )

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                INSERT INTO public.workplace_placements (
                    registration_id,
                    employer_name,
                    employer_reg_no,
                    workplace_address,
                    supervisor_name,
                    supervisor_contact,
                    supervisor_email,
                    placement_start_date,
                    placement_end_date,
                    hours_required,
                    status,
                    notes,
                    created_by
                )
                VALUES (
                    CAST(:registration_id AS uuid),
                    :employer_name,
                    :employer_reg_no,
                    :workplace_address,
                    :supervisor_name,
                    :supervisor_contact,
                    :supervisor_email,
                    :placement_start_date,
                    :placement_end_date,
                    :hours_required,
                    :status,
                    :notes,
                    :actor
                )
                RETURNING *
                """
            ),
            {
                **payload,
                "registration_id": registration["id"],
                "actor": actor,
            },
        ).mappings().one()

    result = dict(row)

    _audit(
        actor=actor,
        action="WORKPLACE_PLACEMENT_CREATED",
        entity_type="WORKPLACE_PLACEMENT",
        entity_id=str(result["id"]),
        description="Workplace placement created.",
        after_data=result,
    )

    return result


def update_placement(
    placement_id: str,
    payload: dict,
    *,
    actor: str,
) -> dict:
    placement_id = _uuid(
        placement_id,
        "placement_id",
    )

    current = _fetch_one(
        """
        SELECT *
        FROM public.workplace_placements
        WHERE id = CAST(:id AS uuid)
        """,
        {"id": placement_id},
    )
    if not current:
        raise ValueError("Placement not found.")

    merged = dict(current)
    for key, value in payload.items():
        if value is not None:
            merged[key] = value

    if merged["status"] not in PLACEMENT_STATUSES:
        raise ValueError("Invalid placement status.")

    if (
        merged.get("placement_end_date")
        and merged["placement_end_date"]
        < merged["placement_start_date"]
    ):
        raise ValueError(
            "placement_end_date cannot be before placement_start_date."
        )

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                UPDATE public.workplace_placements
                SET
                    employer_name = :employer_name,
                    employer_reg_no = :employer_reg_no,
                    workplace_address = :workplace_address,
                    supervisor_name = :supervisor_name,
                    supervisor_contact = :supervisor_contact,
                    supervisor_email = :supervisor_email,
                    placement_start_date = :placement_start_date,
                    placement_end_date = :placement_end_date,
                    hours_required = :hours_required,
                    status = CAST(:status AS varchar),
                    notes = :notes,
                    updated_at = now()
                WHERE id = CAST(:id AS uuid)
                RETURNING *
                """
            ),
            {
                "id": placement_id,
                **{
                    key: merged.get(key)
                    for key in (
                        "employer_name",
                        "employer_reg_no",
                        "workplace_address",
                        "supervisor_name",
                        "supervisor_contact",
                        "supervisor_email",
                        "placement_start_date",
                        "placement_end_date",
                        "hours_required",
                        "status",
                        "notes",
                    )
                },
            },
        ).mappings().one()

    result = dict(row)

    _audit(
        actor=actor,
        action="WORKPLACE_PLACEMENT_UPDATED",
        entity_type="WORKPLACE_PLACEMENT",
        entity_id=placement_id,
        description="Workplace placement updated.",
        after_data=result,
    )

    return result


def list_workplace_attendance(
    placement_id: str,
) -> list[dict]:
    placement_id = _uuid(
        placement_id,
        "placement_id",
    )
    return _fetch_all(
        """
        SELECT *
        FROM public.workplace_attendance
        WHERE placement_id = CAST(:placement_id AS uuid)
        ORDER BY attendance_date DESC
        """,
        {"placement_id": placement_id},
    )


def upsert_workplace_attendance(
    placement_id: str,
    payload: dict,
    *,
    actor: str,
) -> dict:
    placement_id = _uuid(
        placement_id,
        "placement_id",
    )

    placement = _fetch_one(
        """
        SELECT id
        FROM public.workplace_placements
        WHERE id = CAST(:id AS uuid)
        """,
        {"id": placement_id},
    )
    if not placement:
        raise ValueError("Placement not found.")

    status = payload["attendance_status"]
    if status not in ATTENDANCE_STATUSES:
        raise ValueError("Invalid attendance status.")

    sign_in = payload.get("sign_in_time")
    sign_out = payload.get("sign_out_time")
    if sign_in and sign_out and sign_out <= sign_in:
        raise ValueError(
            "sign_out_time must be later than sign_in_time."
        )

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                INSERT INTO public.workplace_attendance (
                    placement_id,
                    attendance_date,
                    attendance_status,
                    sign_in_time,
                    sign_out_time,
                    hours_worked,
                    supervisor_confirmed,
                    notes,
                    captured_by
                )
                VALUES (
                    CAST(:placement_id AS uuid),
                    :attendance_date,
                    :attendance_status,
                    :sign_in_time,
                    :sign_out_time,
                    :hours_worked,
                    :supervisor_confirmed,
                    :notes,
                    :actor
                )
                ON CONFLICT (
                    placement_id,
                    attendance_date
                )
                DO UPDATE SET
                    attendance_status = EXCLUDED.attendance_status,
                    sign_in_time = EXCLUDED.sign_in_time,
                    sign_out_time = EXCLUDED.sign_out_time,
                    hours_worked = EXCLUDED.hours_worked,
                    supervisor_confirmed = EXCLUDED.supervisor_confirmed,
                    notes = EXCLUDED.notes,
                    captured_by = EXCLUDED.captured_by,
                    updated_at = now()
                RETURNING *
                """
            ),
            {
                "placement_id": placement_id,
                **payload,
                "actor": actor,
            },
        ).mappings().one()

    result = dict(row)

    _audit(
        actor=actor,
        action="WORKPLACE_ATTENDANCE_CAPTURED",
        entity_type="WORKPLACE_ATTENDANCE",
        entity_id=str(result["id"]),
        description="Workplace attendance captured.",
        after_data=result,
    )

    return result


def list_weekly_submissions(
    placement_id: str,
) -> list[dict]:
    placement_id = _uuid(
        placement_id,
        "placement_id",
    )
    return _fetch_all(
        """
        SELECT *
        FROM public.workplace_weekly_submissions
        WHERE placement_id = CAST(:placement_id AS uuid)
        ORDER BY week_start DESC, created_at DESC
        """,
        {"placement_id": placement_id},
    )


def create_weekly_submission(
    placement_id: str,
    payload: dict,
    *,
    actor: str,
) -> dict:
    placement_id = _uuid(
        placement_id,
        "placement_id",
    )
    if payload["week_end"] < payload["week_start"]:
        raise ValueError(
            "week_end cannot be before week_start."
        )

    status = payload.get(
        "status",
        "Submitted",
    )
    if status not in SUBMISSION_STATUSES:
        raise ValueError("Invalid submission status.")

    try:
        with engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    INSERT INTO public.workplace_weekly_submissions (
                        placement_id,
                        week_start,
                        week_end,
                        submission_type,
                        title,
                        evidence_reference,
                        learner_comment,
                        status,
                        created_by
                    )
                    VALUES (
                        CAST(:placement_id AS uuid),
                        :week_start,
                        :week_end,
                        :submission_type,
                        :title,
                        :evidence_reference,
                        :learner_comment,
                        :status,
                        :actor
                    )
                    RETURNING *
                    """
                ),
                {
                    "placement_id": placement_id,
                    **payload,
                    "actor": actor,
                },
            ).mappings().one()
    except IntegrityError as error:
        raise ValueError(
            "A submission of this type already exists "
            "for the selected week."
        ) from error

    result = dict(row)

    _audit(
        actor=actor,
        action="WORKPLACE_WEEKLY_SUBMISSION_CREATED",
        entity_type="WORKPLACE_WEEKLY_SUBMISSION",
        entity_id=str(result["id"]),
        description="Workplace weekly submission created.",
        after_data=result,
    )

    return result


def update_weekly_submission(
    submission_id: str,
    payload: dict,
    *,
    actor: str,
) -> dict:
    submission_id = _uuid(
        submission_id,
        "submission_id",
    )

    status = _clean(
        payload.get("status")
    )
    if status and status not in SUBMISSION_STATUSES:
        raise ValueError("Invalid submission status.")

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                UPDATE public.workplace_weekly_submissions
                SET
                    status = COALESCE(:status, status),
                    review_comment = COALESCE(
                        :review_comment,
                        review_comment
                    ),
                    evidence_reference = COALESCE(
                        :evidence_reference,
                        evidence_reference
                    ),
                    reviewed_by = CASE
                        WHEN :status IN (
                            'Reviewed',
                            'Returned',
                            'Approved'
                        )
                        THEN :actor
                        ELSE reviewed_by
                    END,
                    reviewed_at = CASE
                        WHEN :status IN (
                            'Reviewed',
                            'Returned',
                            'Approved'
                        )
                        THEN now()
                        ELSE reviewed_at
                    END,
                    updated_at = now()
                WHERE id = CAST(:id AS uuid)
                RETURNING *
                """
            ),
            {
                "id": submission_id,
                "status": status,
                "review_comment": _clean(
                    payload.get("review_comment")
                ),
                "evidence_reference": _clean(
                    payload.get("evidence_reference")
                ),
                "actor": actor,
            },
        ).mappings().first()

    if not row:
        raise ValueError("Weekly submission not found.")

    result = dict(row)

    _audit(
        actor=actor,
        action="WORKPLACE_WEEKLY_SUBMISSION_UPDATED",
        entity_type="WORKPLACE_WEEKLY_SUBMISSION",
        entity_id=submission_id,
        description="Workplace weekly submission updated.",
        after_data=result,
    )

    return result


def list_supervisor_reports(
    placement_id: str,
) -> list[dict]:
    placement_id = _uuid(
        placement_id,
        "placement_id",
    )
    return _fetch_all(
        """
        SELECT *
        FROM public.workplace_supervisor_reports
        WHERE placement_id = CAST(:placement_id AS uuid)
        ORDER BY report_date DESC, created_at DESC
        """,
        {"placement_id": placement_id},
    )


def create_supervisor_report(
    placement_id: str,
    payload: dict,
    *,
    actor: str,
) -> dict:
    placement_id = _uuid(
        placement_id,
        "placement_id",
    )

    period_start = payload.get("period_start")
    period_end = payload.get("period_end")
    if (
        period_start
        and period_end
        and period_end < period_start
    ):
        raise ValueError(
            "period_end cannot be before period_start."
        )

    status = payload.get(
        "status",
        "Submitted",
    )
    if status not in SUPERVISOR_REPORT_STATUSES:
        raise ValueError("Invalid supervisor report status.")

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                INSERT INTO public.workplace_supervisor_reports (
                    placement_id,
                    report_date,
                    period_start,
                    period_end,
                    overall_rating,
                    attendance_comment,
                    performance_comment,
                    conduct_comment,
                    competencies_comment,
                    recommendation,
                    supervisor_name,
                    status,
                    submitted_at,
                    created_by
                )
                VALUES (
                    CAST(:placement_id AS uuid),
                    COALESCE(:report_date, CURRENT_DATE),
                    :period_start,
                    :period_end,
                    :overall_rating,
                    :attendance_comment,
                    :performance_comment,
                    :conduct_comment,
                    :competencies_comment,
                    :recommendation,
                    :supervisor_name,
                    :status,
                    CASE
                        WHEN :status IN ('Submitted','Reviewed')
                        THEN now()
                        ELSE NULL
                    END,
                    :actor
                )
                RETURNING *
                """
            ),
            {
                "placement_id": placement_id,
                **payload,
                "actor": actor,
            },
        ).mappings().one()

    result = dict(row)

    _audit(
        actor=actor,
        action="WORKPLACE_SUPERVISOR_REPORT_CREATED",
        entity_type="WORKPLACE_SUPERVISOR_REPORT",
        entity_id=str(result["id"]),
        description="Workplace supervisor report created.",
        after_data=result,
    )

    return result


def update_supervisor_report(
    report_id: str,
    payload: dict,
    *,
    actor: str,
) -> dict:
    report_id = _uuid(
        report_id,
        "report_id",
    )

    status = _clean(
        payload.get("status")
    )
    if (
        status
        and status not in SUPERVISOR_REPORT_STATUSES
    ):
        raise ValueError("Invalid supervisor report status.")

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                UPDATE public.workplace_supervisor_reports
                SET
                    status = COALESCE(:status, status),
                    review_comment = COALESCE(
                        :review_comment,
                        review_comment
                    ),
                    overall_rating = COALESCE(
                        :overall_rating,
                        overall_rating
                    ),
                    recommendation = COALESCE(
                        :recommendation,
                        recommendation
                    ),
                    reviewed_by = CASE
                        WHEN :status = 'Reviewed'
                        THEN :actor
                        ELSE reviewed_by
                    END,
                    reviewed_at = CASE
                        WHEN :status = 'Reviewed'
                        THEN now()
                        ELSE reviewed_at
                    END,
                    updated_at = now()
                WHERE id = CAST(:id AS uuid)
                RETURNING *
                """
            ),
            {
                "id": report_id,
                "status": status,
                "review_comment": _clean(
                    payload.get("review_comment")
                ),
                "overall_rating": payload.get(
                    "overall_rating"
                ),
                "recommendation": _clean(
                    payload.get("recommendation")
                ),
                "actor": actor,
            },
        ).mappings().first()

    if not row:
        raise ValueError("Supervisor report not found.")

    result = dict(row)

    _audit(
        actor=actor,
        action="WORKPLACE_SUPERVISOR_REPORT_UPDATED",
        entity_type="WORKPLACE_SUPERVISOR_REPORT",
        entity_id=report_id,
        description="Workplace supervisor report updated.",
        after_data=result,
    )

    return result


def list_eisa_sittings(
    *,
    cycle_code: str | None = None,
    course_code: str | None = None,
    status: str | None = None,
) -> list[dict]:
    return _fetch_all(
        """
        SELECT
            es.*,
            c.course_name,
            COUNT(esc.id) AS candidate_count
        FROM public.eisa_sittings es
        JOIN public.courses c
            ON c.course_code = es.course_code
        LEFT JOIN public.eisa_sitting_candidates esc
            ON esc.sitting_id = es.id
        WHERE
            (:cycle_code IS NULL OR es.cycle_code = :cycle_code)
            AND (:course_code IS NULL OR es.course_code = :course_code)
            AND (:status IS NULL OR es.status = :status)
        GROUP BY es.id, c.course_name
        ORDER BY es.assessment_date DESC, es.start_time
        """,
        {
            "cycle_code": _clean(cycle_code),
            "course_code": _clean(course_code),
            "status": _clean(status),
        },
    )


def create_eisa_sitting(
    payload: dict,
    *,
    actor: str,
) -> dict:
    course_code = str(
        payload["course_code"]
    ).strip().upper()

    course = _fetch_one(
        """
        SELECT course_code, assessment_type
        FROM public.courses
        WHERE course_code = :course_code
        LIMIT 1
        """,
        {"course_code": course_code},
    )
    if not course:
        raise ValueError("Course not found.")

    if (
        str(course.get("assessment_type") or "")
        .strip()
        .upper()
        not in {
            "FISA_PLUS_EISA",
            "FISA + EISA",
        }
    ):
        raise ValueError(
            "EISA sittings can only be created for "
            "FISA + EISA programmes."
        )

    if payload["end_time"] <= payload["start_time"]:
        raise ValueError(
            "end_time must be later than start_time."
        )

    status = payload.get(
        "status",
        "Draft",
    )
    if status not in EISA_SITTING_STATUSES:
        raise ValueError("Invalid EISA sitting status.")

    sitting_reference = _reference("EISA")

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                INSERT INTO public.eisa_sittings (
                    sitting_reference,
                    course_code,
                    cycle_code,
                    assessment_date,
                    reporting_time,
                    start_time,
                    end_time,
                    venue,
                    assessment_centre,
                    capacity,
                    instructions,
                    status,
                    created_by,
                    published_at
                )
                VALUES (
                    :sitting_reference,
                    :course_code,
                    :cycle_code,
                    :assessment_date,
                    :reporting_time,
                    :start_time,
                    :end_time,
                    :venue,
                    :assessment_centre,
                    :capacity,
                    :instructions,
                    :status,
                    :actor,
                    CASE
                        WHEN CAST(:status AS varchar) = 'Published'
                        THEN now()
                        ELSE NULL
                    END
                )
                RETURNING *
                """
            ),
            {
                "sitting_reference": sitting_reference,
                **payload,
                "course_code": course_code,
                "cycle_code": _clean(
                    payload.get("cycle_code")
                ),
                "actor": actor,
            },
        ).mappings().one()

    result = dict(row)

    _audit(
        actor=actor,
        action="EISA_SITTING_CREATED",
        entity_type="EISA_SITTING",
        entity_id=str(result["id"]),
        description="EISA sitting created.",
        after_data=result,
    )

    return result


def update_eisa_sitting(
    sitting_id: str,
    payload: dict,
    *,
    actor: str,
) -> dict:
    sitting_id = _uuid(
        sitting_id,
        "sitting_id",
    )

    current = _fetch_one(
        """
        SELECT *
        FROM public.eisa_sittings
        WHERE id = CAST(:id AS uuid)
        """,
        {"id": sitting_id},
    )
    if not current:
        raise ValueError("EISA sitting not found.")

    merged = dict(current)
    for key, value in payload.items():
        if value is not None:
            merged[key] = value

    if merged["end_time"] <= merged["start_time"]:
        raise ValueError(
            "end_time must be later than start_time."
        )

    if merged["status"] not in EISA_SITTING_STATUSES:
        raise ValueError("Invalid EISA sitting status.")

    if merged.get("capacity"):
        current_count = _fetch_one(
            """
            SELECT COUNT(*) AS count
            FROM public.eisa_sitting_candidates
            WHERE sitting_id = CAST(:id AS uuid)
            """,
            {"id": sitting_id},
        )
        if int(current_count["count"]) > int(
            merged["capacity"]
        ):
            raise ValueError(
                "Capacity cannot be lower than the "
                "current candidate count."
            )

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                UPDATE public.eisa_sittings
                SET
                    assessment_date = :assessment_date,
                    reporting_time = :reporting_time,
                    start_time = :start_time,
                    end_time = :end_time,
                    venue = :venue,
                    assessment_centre = :assessment_centre,
                    capacity = :capacity,
                    instructions = :instructions,
                    status = CAST(:status AS varchar),
                    published_at = CASE
                        WHEN CAST(:status AS varchar) = 'Published'
                             AND published_at IS NULL
                        THEN now()
                        ELSE published_at
                    END,
                    completed_at = CASE
                        WHEN CAST(:status AS varchar) = 'Completed'
                        THEN now()
                        ELSE completed_at
                    END,
                    updated_at = now()
                WHERE id = CAST(:id AS uuid)
                RETURNING *
                """
            ),
            {
                "id": sitting_id,
                **{
                    key: merged.get(key)
                    for key in (
                        "assessment_date",
                        "reporting_time",
                        "start_time",
                        "end_time",
                        "venue",
                        "assessment_centre",
                        "capacity",
                        "instructions",
                        "status",
                    )
                },
            },
        ).mappings().one()

    result = dict(row)

    _audit(
        actor=actor,
        action="EISA_SITTING_UPDATED",
        entity_type="EISA_SITTING",
        entity_id=sitting_id,
        description="EISA sitting updated.",
        after_data=result,
    )

    return result


def list_eisa_candidates(
    sitting_id: str,
) -> list[dict]:
    sitting_id = _uuid(
        sitting_id,
        "sitting_id",
    )
    return _fetch_all(
        """
        SELECT
            esc.*,
            r.student_number,
            r.course_code,
            r.cycle AS cycle_code,
            CONCAT_WS(
                ' ',
                a.first_name,
                a.middle_name,
                a.last_name
            ) AS learner_name
        FROM public.eisa_sitting_candidates esc
        JOIN public.registrations r
            ON r.id = esc.registration_id
        JOIN public.applications a
            ON a.id = r.application_id
        WHERE esc.sitting_id = CAST(:id AS uuid)
        ORDER BY esc.seat_number
        """,
        {"id": sitting_id},
    )


def add_eisa_candidate(
    sitting_id: str,
    payload: dict,
    *,
    actor: str,
) -> dict:
    sitting_id = _uuid(
        sitting_id,
        "sitting_id",
    )
    sitting = _fetch_one(
        """
        SELECT *
        FROM public.eisa_sittings
        WHERE id = CAST(:id AS uuid)
        """,
        {"id": sitting_id},
    )
    if not sitting:
        raise ValueError("EISA sitting not found.")

    if sitting["status"] in {
        "Completed",
        "Cancelled",
    }:
        raise ValueError(
            "Candidates cannot be changed for this sitting."
        )

    registration = _registration(
        payload["registration_id"]
    )

    if registration["course_code"] != sitting["course_code"]:
        raise ValueError(
            "Registration course does not match the sitting."
        )

    if (
        sitting.get("cycle_code")
        and registration.get("cycle")
        and registration["cycle"] != sitting["cycle_code"]
    ):
        raise ValueError(
            "Registration cycle does not match the sitting."
        )

    if not registration.get("eisa_eligible"):
        raise ValueError(
            "Learner is not marked EISA eligible."
        )

    admission = payload.get(
        "admission_status",
        "Admitted",
    )
    attendance = payload.get(
        "attendance_status",
        "Pending",
    )

    if admission not in EISA_ADMISSION_STATUSES:
        raise ValueError("Invalid admission status.")

    if attendance not in EISA_ATTENDANCE_STATUSES:
        raise ValueError("Invalid attendance status.")

    seat_number = payload.get("seat_number")

    if seat_number is None:
        next_seat = _fetch_one(
            """
            SELECT
                COALESCE(
                    MAX(seat_number),
                    0
                ) + 1 AS seat_number
            FROM public.eisa_sitting_candidates
            WHERE sitting_id = CAST(:id AS uuid)
            """,
            {"id": sitting_id},
        )
        seat_number = int(
            next_seat["seat_number"]
        )

    capacity = sitting.get("capacity")
    if capacity and int(seat_number) > int(capacity):
        raise ValueError(
            "Seat number exceeds the sitting capacity."
        )

    try:
        with engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    INSERT INTO public.eisa_sitting_candidates (
                        sitting_id,
                        registration_id,
                        seat_number,
                        admission_status,
                        attendance_status,
                        notes
                    )
                    VALUES (
                        CAST(:sitting_id AS uuid),
                        CAST(:registration_id AS uuid),
                        :seat_number,
                        :admission_status,
                        :attendance_status,
                        :notes
                    )
                    RETURNING *
                    """
                ),
                {
                    "sitting_id": sitting_id,
                    "registration_id": registration["id"],
                    "seat_number": seat_number,
                    "admission_status": admission,
                    "attendance_status": attendance,
                    "notes": _clean(
                        payload.get("notes")
                    ),
                },
            ).mappings().one()
    except IntegrityError as error:
        raise ValueError(
            "Learner or seat is already allocated "
            "to this EISA sitting."
        ) from error

    result = dict(row)

    _audit(
        actor=actor,
        action="EISA_CANDIDATE_ADDED",
        entity_type="EISA_SITTING_CANDIDATE",
        entity_id=str(result["id"]),
        description="Learner added to EISA sitting.",
        after_data=result,
    )

    return result


def update_eisa_candidate(
    candidate_id: str,
    payload: dict,
    *,
    actor: str,
) -> dict:
    candidate_id = _uuid(
        candidate_id,
        "candidate_id",
    )

    admission = _clean(
        payload.get("admission_status")
    )
    attendance = _clean(
        payload.get("attendance_status")
    )

    if admission and admission not in EISA_ADMISSION_STATUSES:
        raise ValueError("Invalid admission status.")

    if attendance and attendance not in EISA_ATTENDANCE_STATUSES:
        raise ValueError("Invalid attendance status.")

    try:
        with engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE public.eisa_sitting_candidates
                    SET
                        seat_number = COALESCE(
                            :seat_number,
                            seat_number
                        ),
                        admission_status = COALESCE(
                            :admission_status,
                            admission_status
                        ),
                        attendance_status = COALESCE(
                            :attendance_status,
                            attendance_status
                        ),
                        notes = COALESCE(
                            :notes,
                            notes
                        ),
                        updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    RETURNING *
                    """
                ),
                {
                    "id": candidate_id,
                    "seat_number": payload.get(
                        "seat_number"
                    ),
                    "admission_status": admission,
                    "attendance_status": attendance,
                    "notes": _clean(
                        payload.get("notes")
                    ),
                },
            ).mappings().first()
    except IntegrityError as error:
        raise ValueError(
            "The requested EISA seat is already allocated."
        ) from error

    if not row:
        raise ValueError("EISA candidate not found.")

    result = dict(row)

    _audit(
        actor=actor,
        action="EISA_CANDIDATE_UPDATED",
        entity_type="EISA_SITTING_CANDIDATE",
        entity_id=candidate_id,
        description="EISA candidate updated.",
        after_data=result,
    )

    return result


def list_corrective_actions(
    *,
    cycle_code: str | None = None,
    course_code: str | None = None,
    class_code: str | None = None,
    status: str | None = None,
) -> list[dict]:
    return _fetch_all(
        """
        SELECT
            qca.*,
            c.course_name,
            cl.class_name
        FROM public.quality_corrective_actions qca
        LEFT JOIN public.courses c
            ON c.course_code = qca.course_code
        LEFT JOIN public.classes cl
            ON cl.class_code = qca.class_code
        WHERE
            (:cycle_code IS NULL OR qca.cycle_code = :cycle_code)
            AND (:course_code IS NULL OR qca.course_code = :course_code)
            AND (:class_code IS NULL OR qca.class_code = :class_code)
            AND (:status IS NULL OR qca.status = :status)
        ORDER BY
            CASE
                WHEN qca.status IN ('Open','In Progress','Overdue')
                THEN 0
                ELSE 1
            END,
            qca.due_date NULLS LAST,
            qca.created_at DESC
        """,
        {
            "cycle_code": _clean(cycle_code),
            "course_code": _clean(course_code),
            "class_code": _clean(class_code),
            "status": _clean(status),
        },
    )


def create_corrective_action(
    payload: dict,
    *,
    actor: str,
) -> dict:
    source_type = payload["source_type"]
    if source_type not in QA_SOURCE_TYPES:
        raise ValueError("Invalid QA source_type.")

    status = payload.get(
        "status",
        "Open",
    )
    if status not in QA_ACTION_STATUSES:
        raise ValueError(
            "Invalid corrective action status."
        )

    action_reference = _reference("CAR")

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                INSERT INTO public.quality_corrective_actions (
                    action_reference,
                    source_type,
                    source_reference,
                    cycle_code,
                    course_code,
                    class_code,
                    finding,
                    root_cause,
                    corrective_action,
                    owner_staff_code,
                    due_date,
                    status,
                    evidence_reference,
                    created_by
                )
                VALUES (
                    :action_reference,
                    :source_type,
                    :source_reference,
                    :cycle_code,
                    :course_code,
                    :class_code,
                    :finding,
                    :root_cause,
                    :corrective_action,
                    :owner_staff_code,
                    :due_date,
                    :status,
                    :evidence_reference,
                    :actor
                )
                RETURNING *
                """
            ),
            {
                "action_reference": action_reference,
                **payload,
                "cycle_code": _clean(
                    payload.get("cycle_code")
                ),
                "course_code": _clean(
                    payload.get("course_code")
                ),
                "class_code": _clean(
                    payload.get("class_code")
                ),
                "owner_staff_code": _clean(
                    payload.get("owner_staff_code")
                ),
                "actor": actor,
            },
        ).mappings().one()

    result = dict(row)

    _audit(
        actor=actor,
        action="QA_CORRECTIVE_ACTION_CREATED",
        entity_type="QA_CORRECTIVE_ACTION",
        entity_id=str(result["id"]),
        description="QA corrective action created.",
        after_data=result,
    )

    return result


def update_corrective_action(
    action_id: str,
    payload: dict,
    *,
    actor: str,
) -> dict:
    action_id = _uuid(
        action_id,
        "action_id",
    )

    status = _clean(
        payload.get("status")
    )
    if status and status not in QA_ACTION_STATUSES:
        raise ValueError(
            "Invalid corrective action status."
        )

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                UPDATE public.quality_corrective_actions
                SET
                    root_cause = COALESCE(
                        :root_cause,
                        root_cause
                    ),
                    corrective_action = COALESCE(
                        :corrective_action,
                        corrective_action
                    ),
                    owner_staff_code = COALESCE(
                        :owner_staff_code,
                        owner_staff_code
                    ),
                    due_date = COALESCE(
                        :due_date,
                        due_date
                    ),
                    status = COALESCE(
                        CAST(:status AS varchar),
                        status
                    ),
                    completion_notes = COALESCE(
                        :completion_notes,
                        completion_notes
                    ),
                    evidence_reference = COALESCE(
                        :evidence_reference,
                        evidence_reference
                    ),
                    completed_at = CASE
                        WHEN CAST(:status AS varchar) = 'Completed'
                        THEN now()
                        ELSE completed_at
                    END,
                    closed_by = CASE
                        WHEN CAST(:status AS varchar) = 'Closed'
                        THEN :actor
                        ELSE closed_by
                    END,
                    closed_at = CASE
                        WHEN CAST(:status AS varchar) = 'Closed'
                        THEN now()
                        ELSE closed_at
                    END,
                    updated_at = now()
                WHERE id = CAST(:id AS uuid)
                RETURNING *
                """
            ),
            {
                "id": action_id,
                "root_cause": _clean(
                    payload.get("root_cause")
                ),
                "corrective_action": _clean(
                    payload.get("corrective_action")
                ),
                "owner_staff_code": _clean(
                    payload.get("owner_staff_code")
                ),
                "due_date": payload.get("due_date"),
                "status": status,
                "completion_notes": _clean(
                    payload.get("completion_notes")
                ),
                "evidence_reference": _clean(
                    payload.get("evidence_reference")
                ),
                "actor": actor,
            },
        ).mappings().first()

    if not row:
        raise ValueError(
            "Corrective action not found."
        )

    result = dict(row)

    _audit(
        actor=actor,
        action="QA_CORRECTIVE_ACTION_UPDATED",
        entity_type="QA_CORRECTIVE_ACTION",
        entity_id=action_id,
        description="QA corrective action updated.",
        after_data=result,
    )

    return result


# ============================================================
# V5.0 COMPLIANCE READ PARAMETER TYPE FIX
# ============================================================

from sqlalchemy import (
    Date as _V50Date,
    Integer as _V50Integer,
    Numeric as _V50Numeric,
    String as _V50String,
    bindparam as _v50_bindparam,
    text as _v50_text,
)


def _v50_statement(
    sql: str,
    params: dict,
):
    statement = _v50_text(
        sql
    )

    bind_types = {
        "cycle_code": _V50String(),
        "course_code": _V50String(),
        "class_code": _V50String(),
        "status": _V50String(),
        "assessment_scope": _V50String(),
        "source_type": _V50String(),
        "admission_status": _V50String(),
        "attendance_status": _V50String(),
        "date_from": _V50Date(),
        "date_to": _V50Date(),
        "seat_number": _V50Integer(),
        "hours_required": _V50Numeric(),
    }

    binds = []

    for name, type_ in bind_types.items():
        if (
            f":{name}" in sql
            and name in params
        ):
            binds.append(
                _v50_bindparam(
                    name,
                    type_=type_,
                )
            )

    if binds:
        statement = statement.bindparams(
            *binds
        )

    return statement


def _fetch_one(
    sql: str,
    params: dict,
) -> dict | None:
    statement = _v50_statement(
        sql,
        params,
    )

    with engine.connect() as connection:
        row = connection.execute(
            statement,
            params,
        ).mappings().first()

    return dict(row) if row else None


def _fetch_all(
    sql: str,
    params: dict,
) -> list[dict]:
    statement = _v50_statement(
        sql,
        params,
    )

    with engine.connect() as connection:
        rows = connection.execute(
            statement,
            params,
        ).mappings().all()

    return [
        dict(row)
        for row in rows
    ]
