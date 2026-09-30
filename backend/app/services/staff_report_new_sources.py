from app.services.staff_report_common import (
    active_class_lateral,
    fetch_rows,
    make_report,
)


NEW_SOURCE_REPORT_CODES = {
    "assessment.appeals_register",
    "work_experience.placement",
    "work_experience.workplace_attendance",
    "work_experience.weekly_submissions",
    "work_experience.supervisor_reports",
    "eisa.sitting_orders",
    "quality.corrective_action_register",
}


def new_source_report(
    code: str,
    f: dict,
) -> dict:
    if code == "assessment.appeals_register":
        rows = fetch_rows(
            f"""
            SELECT
                aa.appeal_reference,
                aa.lodged_date,
                aa.assessment_scope,
                aa.reason,
                aa.status,
                aa.outcome,
                aa.reviewed_by,
                aa.reviewed_at,
                r.student_number,
                CONCAT_WS(
                    ' ',
                    a.first_name,
                    a.middle_name,
                    a.last_name
                ) AS learner_name,
                r.course_code,
                c.course_name,
                COALESCE(cl.cycle_code, r.cycle) AS cycle_code,
                cl.class_code
            FROM public.assessment_appeals aa
            JOIN public.registrations r
                ON r.id = aa.registration_id
            JOIN public.applications a
                ON a.id = r.application_id
            JOIN public.courses c
                ON c.course_code = r.course_code
            {active_class_lateral()}
            WHERE
                (:cycle_code IS NULL OR COALESCE(cl.cycle_code, r.cycle) = :cycle_code)
                AND (:course_code IS NULL OR r.course_code = :course_code)
                AND (:class_code IS NULL OR cl.class_code = :class_code)
                AND (:date_from IS NULL OR aa.lodged_date >= :date_from)
                AND (:date_to IS NULL OR aa.lodged_date <= :date_to)
            ORDER BY aa.lodged_date DESC, aa.created_at DESC
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("appeal_reference", "Appeal Ref"),
                ("lodged_date", "Lodged"),
                ("assessment_scope", "Assessment"),
                ("student_number", "Student No."),
                ("learner_name", "Learner"),
                ("course_name", "Programme"),
                ("cycle_code", "Cycle"),
                ("class_code", "Class"),
                ("reason", "Reason"),
                ("status", "Status"),
                ("outcome", "Outcome"),
                ("reviewed_by", "Reviewed By"),
                ("reviewed_at", "Reviewed At"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "work_experience.placement":
        rows = fetch_rows(
            f"""
            SELECT
                wp.id AS placement_id,
                r.student_number,
                CONCAT_WS(
                    ' ',
                    a.first_name,
                    a.middle_name,
                    a.last_name
                ) AS learner_name,
                r.course_code,
                c.course_name,
                COALESCE(cl.cycle_code, r.cycle) AS cycle_code,
                cl.class_code,
                wp.employer_name,
                wp.employer_reg_no,
                wp.workplace_address,
                wp.supervisor_name,
                wp.supervisor_contact,
                wp.supervisor_email,
                wp.placement_start_date,
                wp.placement_end_date,
                wp.hours_required,
                COALESCE(att.hours_completed, 0) AS hours_completed,
                wp.status,
                wp.notes
            FROM public.workplace_placements wp
            JOIN public.registrations r
                ON r.id = wp.registration_id
            JOIN public.applications a
                ON a.id = r.application_id
            JOIN public.courses c
                ON c.course_code = r.course_code
            {active_class_lateral()}
            LEFT JOIN LATERAL (
                SELECT
                    SUM(
                        COALESCE(
                            wa.hours_worked,
                            0
                        )
                    ) AS hours_completed
                FROM public.workplace_attendance wa
                WHERE
                    wa.placement_id = wp.id
                    AND wa.attendance_status IN ('Present','Late')
            ) att ON TRUE
            WHERE
                (:cycle_code IS NULL OR COALESCE(cl.cycle_code, r.cycle) = :cycle_code)
                AND (:course_code IS NULL OR r.course_code = :course_code)
                AND (:class_code IS NULL OR cl.class_code = :class_code)
                AND (
                    :date_from IS NULL
                    OR COALESCE(wp.placement_end_date, wp.placement_start_date) >= :date_from
                )
                AND (:date_to IS NULL OR wp.placement_start_date <= :date_to)
            ORDER BY wp.placement_start_date DESC, learner_name
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("student_number", "Student No."),
                ("learner_name", "Learner"),
                ("course_name", "Programme"),
                ("cycle_code", "Cycle"),
                ("class_code", "Class"),
                ("employer_name", "Employer"),
                ("supervisor_name", "Supervisor"),
                ("placement_start_date", "Start"),
                ("placement_end_date", "End"),
                ("hours_required", "Hours Required"),
                ("hours_completed", "Hours Completed"),
                ("status", "Status"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "work_experience.workplace_attendance":
        rows = fetch_rows(
            f"""
            SELECT
                wa.attendance_date,
                wa.attendance_status,
                wa.sign_in_time,
                wa.sign_out_time,
                wa.hours_worked,
                wa.supervisor_confirmed,
                wa.notes,
                r.student_number,
                CONCAT_WS(
                    ' ',
                    a.first_name,
                    a.middle_name,
                    a.last_name
                ) AS learner_name,
                r.course_code,
                c.course_name,
                COALESCE(cl.cycle_code, r.cycle) AS cycle_code,
                cl.class_code,
                wp.employer_name,
                wp.supervisor_name
            FROM public.workplace_attendance wa
            JOIN public.workplace_placements wp
                ON wp.id = wa.placement_id
            JOIN public.registrations r
                ON r.id = wp.registration_id
            JOIN public.applications a
                ON a.id = r.application_id
            JOIN public.courses c
                ON c.course_code = r.course_code
            {active_class_lateral()}
            WHERE
                (:cycle_code IS NULL OR COALESCE(cl.cycle_code, r.cycle) = :cycle_code)
                AND (:course_code IS NULL OR r.course_code = :course_code)
                AND (:class_code IS NULL OR cl.class_code = :class_code)
                AND (:date_from IS NULL OR wa.attendance_date >= :date_from)
                AND (:date_to IS NULL OR wa.attendance_date <= :date_to)
            ORDER BY wa.attendance_date DESC, learner_name
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("attendance_date", "Date"),
                ("student_number", "Student No."),
                ("learner_name", "Learner"),
                ("course_name", "Programme"),
                ("cycle_code", "Cycle"),
                ("class_code", "Class"),
                ("employer_name", "Employer"),
                ("attendance_status", "Status"),
                ("sign_in_time", "Sign In"),
                ("sign_out_time", "Sign Out"),
                ("hours_worked", "Hours"),
                ("supervisor_confirmed", "Supervisor Confirmed"),
                ("notes", "Notes"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "work_experience.weekly_submissions":
        rows = fetch_rows(
            f"""
            SELECT
                ws.week_start,
                ws.week_end,
                ws.submission_type,
                ws.title,
                ws.evidence_reference,
                ws.learner_comment,
                ws.status,
                ws.submitted_at,
                ws.reviewed_by,
                ws.reviewed_at,
                ws.review_comment,
                r.student_number,
                CONCAT_WS(
                    ' ',
                    a.first_name,
                    a.middle_name,
                    a.last_name
                ) AS learner_name,
                r.course_code,
                c.course_name,
                COALESCE(cl.cycle_code, r.cycle) AS cycle_code,
                cl.class_code,
                wp.employer_name
            FROM public.workplace_weekly_submissions ws
            JOIN public.workplace_placements wp
                ON wp.id = ws.placement_id
            JOIN public.registrations r
                ON r.id = wp.registration_id
            JOIN public.applications a
                ON a.id = r.application_id
            JOIN public.courses c
                ON c.course_code = r.course_code
            {active_class_lateral()}
            WHERE
                (:cycle_code IS NULL OR COALESCE(cl.cycle_code, r.cycle) = :cycle_code)
                AND (:course_code IS NULL OR r.course_code = :course_code)
                AND (:class_code IS NULL OR cl.class_code = :class_code)
                AND (:date_from IS NULL OR ws.week_end >= :date_from)
                AND (:date_to IS NULL OR ws.week_start <= :date_to)
            ORDER BY ws.week_start DESC, learner_name
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("week_start", "Week Start"),
                ("week_end", "Week End"),
                ("student_number", "Student No."),
                ("learner_name", "Learner"),
                ("course_name", "Programme"),
                ("cycle_code", "Cycle"),
                ("class_code", "Class"),
                ("employer_name", "Employer"),
                ("submission_type", "Type"),
                ("title", "Title"),
                ("evidence_reference", "Evidence"),
                ("status", "Status"),
                ("reviewed_by", "Reviewed By"),
                ("review_comment", "Review Comment"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "work_experience.supervisor_reports":
        rows = fetch_rows(
            f"""
            SELECT
                sr.report_date,
                sr.period_start,
                sr.period_end,
                sr.overall_rating,
                sr.attendance_comment,
                sr.performance_comment,
                sr.conduct_comment,
                sr.competencies_comment,
                sr.recommendation,
                sr.supervisor_name,
                sr.status,
                sr.reviewed_by,
                sr.reviewed_at,
                sr.review_comment,
                r.student_number,
                CONCAT_WS(
                    ' ',
                    a.first_name,
                    a.middle_name,
                    a.last_name
                ) AS learner_name,
                r.course_code,
                c.course_name,
                COALESCE(cl.cycle_code, r.cycle) AS cycle_code,
                cl.class_code,
                wp.employer_name
            FROM public.workplace_supervisor_reports sr
            JOIN public.workplace_placements wp
                ON wp.id = sr.placement_id
            JOIN public.registrations r
                ON r.id = wp.registration_id
            JOIN public.applications a
                ON a.id = r.application_id
            JOIN public.courses c
                ON c.course_code = r.course_code
            {active_class_lateral()}
            WHERE
                (:cycle_code IS NULL OR COALESCE(cl.cycle_code, r.cycle) = :cycle_code)
                AND (:course_code IS NULL OR r.course_code = :course_code)
                AND (:class_code IS NULL OR cl.class_code = :class_code)
                AND (:date_from IS NULL OR sr.report_date >= :date_from)
                AND (:date_to IS NULL OR sr.report_date <= :date_to)
            ORDER BY sr.report_date DESC, learner_name
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("report_date", "Report Date"),
                ("student_number", "Student No."),
                ("learner_name", "Learner"),
                ("course_name", "Programme"),
                ("cycle_code", "Cycle"),
                ("class_code", "Class"),
                ("employer_name", "Employer"),
                ("supervisor_name", "Supervisor"),
                ("overall_rating", "Rating"),
                ("performance_comment", "Performance"),
                ("conduct_comment", "Conduct"),
                ("competencies_comment", "Competencies"),
                ("recommendation", "Recommendation"),
                ("status", "Status"),
                ("reviewed_by", "Reviewed By"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "eisa.sitting_orders":
        rows = fetch_rows(
            """
            SELECT
                es.sitting_reference,
                es.assessment_date,
                es.reporting_time,
                es.start_time,
                es.end_time,
                es.venue,
                es.assessment_centre,
                es.capacity,
                es.status AS sitting_status,
                es.course_code,
                c.course_name,
                es.cycle_code,
                esc.seat_number,
                esc.admission_status,
                esc.attendance_status,
                r.student_number,
                CONCAT_WS(
                    ' ',
                    a.first_name,
                    a.middle_name,
                    a.last_name
                ) AS learner_name
            FROM public.eisa_sittings es
            JOIN public.courses c
                ON c.course_code = es.course_code
            LEFT JOIN public.eisa_sitting_candidates esc
                ON esc.sitting_id = es.id
            LEFT JOIN public.registrations r
                ON r.id = esc.registration_id
            LEFT JOIN public.applications a
                ON a.id = r.application_id
            WHERE
                (:cycle_code IS NULL OR es.cycle_code = :cycle_code)
                AND (:course_code IS NULL OR es.course_code = :course_code)
                AND (:date_from IS NULL OR es.assessment_date >= :date_from)
                AND (:date_to IS NULL OR es.assessment_date <= :date_to)
            ORDER BY
                es.assessment_date,
                es.start_time,
                es.sitting_reference,
                esc.seat_number
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("sitting_reference", "Sitting"),
                ("assessment_date", "Date"),
                ("course_name", "Programme"),
                ("cycle_code", "Cycle"),
                ("venue", "Venue"),
                ("assessment_centre", "Assessment Centre"),
                ("reporting_time", "Reporting"),
                ("start_time", "Start"),
                ("end_time", "End"),
                ("capacity", "Capacity"),
                ("seat_number", "Seat"),
                ("student_number", "Student No."),
                ("learner_name", "Learner"),
                ("admission_status", "Admission"),
                ("attendance_status", "Attendance"),
                ("sitting_status", "Sitting Status"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "quality.corrective_action_register":
        rows = fetch_rows(
            """
            SELECT
                qca.action_reference,
                qca.source_type,
                qca.source_reference,
                qca.cycle_code,
                qca.course_code,
                c.course_name,
                qca.class_code,
                qca.finding,
                qca.root_cause,
                qca.corrective_action,
                qca.owner_staff_code,
                qca.due_date,
                CASE
                    WHEN
                        qca.status IN ('Open','In Progress')
                        AND qca.due_date IS NOT NULL
                        AND qca.due_date < CURRENT_DATE
                    THEN 'Overdue'
                    ELSE qca.status
                END AS status,
                qca.completion_notes,
                qca.evidence_reference,
                qca.completed_at,
                qca.closed_by,
                qca.closed_at,
                qca.created_at
            FROM public.quality_corrective_actions qca
            LEFT JOIN public.courses c
                ON c.course_code = qca.course_code
            WHERE
                (:cycle_code IS NULL OR qca.cycle_code = :cycle_code)
                AND (:course_code IS NULL OR qca.course_code = :course_code)
                AND (:class_code IS NULL OR qca.class_code = :class_code)
                AND (:date_from IS NULL OR qca.created_at::date >= :date_from)
                AND (:date_to IS NULL OR qca.created_at::date <= :date_to)
            ORDER BY
                CASE
                    WHEN qca.status IN ('Open','In Progress','Overdue')
                    THEN 0
                    ELSE 1
                END,
                qca.due_date NULLS LAST,
                qca.created_at DESC
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("action_reference", "CAR Ref"),
                ("source_type", "Source"),
                ("source_reference", "Source Ref"),
                ("cycle_code", "Cycle"),
                ("course_name", "Programme"),
                ("class_code", "Class"),
                ("finding", "Finding"),
                ("root_cause", "Root Cause"),
                ("corrective_action", "Corrective Action"),
                ("owner_staff_code", "Owner"),
                ("due_date", "Due Date"),
                ("status", "Status"),
                ("completion_notes", "Completion Notes"),
                ("evidence_reference", "Evidence"),
                ("completed_at", "Completed"),
                ("closed_by", "Closed By"),
                ("closed_at", "Closed"),
            ],
            rows=rows,
            filters=f,
        )

    raise ValueError(
        "New report source handler is not configured."
    )
