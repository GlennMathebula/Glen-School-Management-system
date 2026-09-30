from app.services.staff_report_common import (
    fetch_rows,
    make_report,
)


def curriculum_report(code: str, f: dict) -> dict:
    module_type = None
    if code == "curriculum.km_delivery":
        module_type = "KM"
    elif code == "curriculum.pm_delivery":
        module_type = "PM"
    elif code == "curriculum.wm_delivery":
        module_type = "WM"

    params = {**f, "module_type": module_type}

    rows = fetch_rows(
        """
        SELECT
            m.course_code,
            c.course_name,
            cl.cycle_code,
            cl.class_code,
            cl.class_group,
            m.module_type,
            m.module_code,
            m.module_name,
            m.credits,
            COUNT(DISTINCT ts.id) AS scheduled_sessions,
            COUNT(DISTINCT ts.id) FILTER (
                WHERE ts.status = 'Published'
            ) AS published_sessions,
            MIN(ts.session_date) AS first_session,
            MAX(ts.session_date) AS last_session,
            COUNT(DISTINCT lr.id) FILTER (
                WHERE lr.status = 'Published'
            ) AS published_resources,
            COUNT(DISTINCT mr.id) AS learner_module_registrations,
            COUNT(DISTINCT mr.id) FILTER (
                WHERE mr.status = 'Completed'
            ) AS completed_module_registrations,
            ROUND(
                (
                    100.0
                    * COUNT(DISTINCT mr.id) FILTER (
                        WHERE mr.status = 'Completed'
                    )
                    / NULLIF(COUNT(DISTINCT mr.id), 0)
                )::numeric,
                2
            ) AS completion_rate
        FROM public.modules m
        JOIN public.courses c
            ON c.course_code = m.course_code
        LEFT JOIN public.classes cl
            ON cl.course_code = m.course_code
            AND (:cycle_code IS NULL OR cl.cycle_code = :cycle_code)
            AND (:class_code IS NULL OR cl.class_code = :class_code)
        LEFT JOIN public.timetable_sessions ts
            ON ts.module_id = m.id
            AND ts.class_id = cl.id
            AND (:date_from IS NULL OR ts.session_date >= :date_from)
            AND (:date_to IS NULL OR ts.session_date <= :date_to)
        LEFT JOIN public.learning_resources lr
            ON lr.module_id = m.id
            AND (lr.class_id IS NULL OR lr.class_id = cl.id)
        LEFT JOIN public.module_registrations mr
            ON mr.module_id = m.id
        LEFT JOIN public.registrations r
            ON r.id = mr.registration_id
            AND (:cycle_code IS NULL OR r.cycle = :cycle_code)
        WHERE
            (:course_code IS NULL OR m.course_code = :course_code)
            AND (:module_type IS NULL OR m.module_type = :module_type)
        GROUP BY
            m.course_code,
            c.course_name,
            cl.cycle_code,
            cl.class_code,
            cl.class_group,
            m.module_type,
            m.module_code,
            m.module_name,
            m.credits
        ORDER BY
            c.course_name,
            cl.cycle_code,
            cl.class_code,
            CASE
                WHEN m.module_type = 'KM' THEN 1
                WHEN m.module_type = 'PM' THEN 2
                WHEN m.module_type = 'WM' THEN 3
                ELSE 4
            END,
            m.module_code
        """,
        params,
    )

    return make_report(
        code,
        columns=[
            ("course_code", "Course"),
            ("course_name", "Programme"),
            ("cycle_code", "Cycle"),
            ("class_code", "Class"),
            ("class_group", "Group"),
            ("module_type", "Type"),
            ("module_code", "Module"),
            ("module_name", "Module Name"),
            ("credits", "Credits"),
            ("scheduled_sessions", "Scheduled"),
            ("published_sessions", "Published"),
            ("published_resources", "Resources"),
            ("learner_module_registrations", "Registered"),
            ("completed_module_registrations", "Completed"),
            ("completion_rate", "Completion %"),
        ],
        rows=rows,
        filters=f,
    )


def _assessment_union(
    f: dict,
    *,
    extra_mark_where: str = "",
    extra_sum_where: str = "",
) -> list[dict]:
    return fetch_rows(
        f"""
        SELECT *
        FROM (
            SELECT
                'MODULE' AS record_type,
                r.student_number,
                CONCAT_WS(' ', a.first_name, a.middle_name, a.last_name) AS learner_name,
                r.course_code,
                c.course_name,
                r.cycle AS cycle_code,
                cl.class_code,
                m.module_code AS assessment_code,
                m.module_name AS assessment_name,
                m.module_type AS assessment_type,
                mk.attempt_number,
                mk.mark,
                mk.result,
                mk.status,
                mk.assessor_code,
                mk.moderator_code,
                mk.return_reason,
                mk.created_at AS assessment_date
            FROM public.marks mk
            JOIN public.module_registrations mr
                ON mr.id = mk.module_registration_id
            JOIN public.modules m
                ON m.id = mr.module_id
            JOIN public.registrations r
                ON r.id = mr.registration_id
            JOIN public.applications a
                ON a.id = r.application_id
            JOIN public.courses c
                ON c.course_code = r.course_code
            LEFT JOIN LATERAL (
                SELECT c2.class_code
                FROM public.class_enrolments ce2
                JOIN public.classes c2
                    ON c2.id = ce2.class_id
                WHERE
                    ce2.registration_id = r.id
                    AND ce2.status = 'Active'
                LIMIT 1
            ) cl ON TRUE
            WHERE
                (:cycle_code IS NULL OR r.cycle = :cycle_code)
                AND (:course_code IS NULL OR r.course_code = :course_code)
                AND (:class_code IS NULL OR cl.class_code = :class_code)
                AND (:date_from IS NULL OR mk.created_at::date >= :date_from)
                AND (:date_to IS NULL OR mk.created_at::date <= :date_to)
                {extra_mark_where}

            UNION ALL

            SELECT
                'SUMMATIVE' AS record_type,
                r.student_number,
                CONCAT_WS(' ', a.first_name, a.middle_name, a.last_name) AS learner_name,
                r.course_code,
                c.course_name,
                r.cycle AS cycle_code,
                cl.class_code,
                sa.assessment_type AS assessment_code,
                sa.assessment_type AS assessment_name,
                sa.assessment_type,
                sa.attempt_number,
                sa.mark,
                sa.result,
                sa.status,
                sa.assessor_code,
                sa.moderator_code,
                sa.return_reason,
                sa.assessment_date
            FROM public.summative_assessments sa
            JOIN public.registrations r
                ON r.id = sa.registration_id
            JOIN public.applications a
                ON a.id = r.application_id
            JOIN public.courses c
                ON c.course_code = r.course_code
            LEFT JOIN LATERAL (
                SELECT c2.class_code
                FROM public.class_enrolments ce2
                JOIN public.classes c2
                    ON c2.id = ce2.class_id
                WHERE
                    ce2.registration_id = r.id
                    AND ce2.status = 'Active'
                LIMIT 1
            ) cl ON TRUE
            WHERE
                (:cycle_code IS NULL OR r.cycle = :cycle_code)
                AND (:course_code IS NULL OR r.course_code = :course_code)
                AND (:class_code IS NULL OR cl.class_code = :class_code)
                AND (:date_from IS NULL OR sa.assessment_date::date >= :date_from)
                AND (:date_to IS NULL OR sa.assessment_date::date <= :date_to)
                {extra_sum_where}
        ) q
        ORDER BY assessment_date DESC, learner_name, assessment_code
        """,
        f,
    )


def assessment_report(code: str, f: dict) -> dict:
    if code == "assessment.schedule":
        rows = fetch_rows(
            """
            SELECT
                fs.sitting_reference,
                fs.course_code,
                c.course_name,
                fs.cycle_code,
                fs.assessment_date,
                fs.reporting_time,
                fs.start_time,
                fs.end_time,
                fs.venue,
                fs.assessment_centre,
                fs.status,
                COUNT(fsc.id) AS candidate_count
            FROM public.fisa_sittings fs
            JOIN public.courses c
                ON c.course_code = fs.course_code
            LEFT JOIN public.fisa_sitting_candidates fsc
                ON fsc.sitting_id = fs.id
            WHERE
                (:cycle_code IS NULL OR fs.cycle_code = :cycle_code)
                AND (:course_code IS NULL OR fs.course_code = :course_code)
                AND (:date_from IS NULL OR fs.assessment_date >= :date_from)
                AND (:date_to IS NULL OR fs.assessment_date <= :date_to)
            GROUP BY fs.id, c.course_name
            ORDER BY fs.assessment_date, fs.start_time
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("sitting_reference", "Reference"),
                ("course_code", "Course"),
                ("course_name", "Programme"),
                ("cycle_code", "Cycle"),
                ("assessment_date", "Date"),
                ("reporting_time", "Reporting"),
                ("start_time", "Start"),
                ("end_time", "End"),
                ("venue", "Venue"),
                ("assessment_centre", "Assessment Centre"),
                ("status", "Status"),
                ("candidate_count", "Candidates"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "assessment.assessor":
        rows = fetch_rows(
            """
            SELECT
                assessor_code,
                COUNT(*) AS records_captured,
                COUNT(*) FILTER (WHERE status = 'Draft') AS draft_count,
                COUNT(*) FILTER (WHERE status = 'Submitted') AS submitted_count,
                COUNT(*) FILTER (WHERE status IN ('Moderated', 'Published')) AS approved_count,
                COUNT(*) FILTER (WHERE status = 'Returned') AS returned_count,
                ROUND(AVG(mark)::numeric, 2) AS average_mark
            FROM (
                SELECT
                    mk.assessor_code,
                    mk.status,
                    mk.mark,
                    r.course_code,
                    r.cycle,
                    mk.created_at
                FROM public.marks mk
                JOIN public.module_registrations mr
                    ON mr.id = mk.module_registration_id
                JOIN public.registrations r
                    ON r.id = mr.registration_id

                UNION ALL

                SELECT
                    sa.assessor_code,
                    sa.status,
                    sa.mark,
                    r.course_code,
                    r.cycle,
                    sa.created_at
                FROM public.summative_assessments sa
                JOIN public.registrations r
                    ON r.id = sa.registration_id
            ) q
            WHERE
                assessor_code IS NOT NULL
                AND (:cycle_code IS NULL OR q.cycle = :cycle_code)
                AND (:course_code IS NULL OR q.course_code = :course_code)
                AND (:date_from IS NULL OR q.created_at::date >= :date_from)
                AND (:date_to IS NULL OR q.created_at::date <= :date_to)
            GROUP BY assessor_code
            ORDER BY assessor_code
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("assessor_code", "Assessor"),
                ("records_captured", "Captured"),
                ("draft_count", "Draft"),
                ("submitted_count", "Submitted"),
                ("approved_count", "Moderated/Published"),
                ("returned_count", "Returned"),
                ("average_mark", "Average Mark"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "assessment.moderation":
        rows = _assessment_union(
            f,
            extra_mark_where="AND mk.status IN ('Submitted', 'Moderated', 'Published', 'Returned')",
            extra_sum_where="AND sa.status IN ('Submitted', 'Moderated', 'Published', 'Returned')",
        )
    elif code == "assessment.nyc":
        rows = _assessment_union(
            f,
            extra_mark_where="""
                AND (
                    UPPER(COALESCE(mk.result, '')) IN (
                        'NYC',
                        'NOT YET COMPETENT',
                        'FAIL',
                        'FAILED'
                    )
                    OR (
                        mk.mark IS NOT NULL
                        AND m.pass_mark IS NOT NULL
                        AND mk.mark < m.pass_mark
                    )
                )
            """,
            extra_sum_where="""
                AND (
                    UPPER(COALESCE(sa.result, '')) IN (
                        'NYC',
                        'NOT YET COMPETENT',
                        'FAIL',
                        'FAILED'
                    )
                    OR (
                        sa.assessment_type = 'FISA'
                        AND sa.mark IS NOT NULL
                        AND c.fisa_pass_mark IS NOT NULL
                        AND sa.mark < c.fisa_pass_mark
                    )
                )
            """,
        )
    elif code == "assessment.reassessment":
        rows = _assessment_union(
            f,
            extra_mark_where="AND mk.attempt_number > 1",
            extra_sum_where="AND sa.attempt_number > 1",
        )
    else:
        rows = _assessment_union(f)

    return make_report(
        code,
        columns=[
            ("record_type", "Record Type"),
            ("student_number", "Student No."),
            ("learner_name", "Learner"),
            ("course_name", "Programme"),
            ("cycle_code", "Cycle"),
            ("class_code", "Class"),
            ("assessment_code", "Assessment"),
            ("assessment_type", "Type"),
            ("attempt_number", "Attempt"),
            ("mark", "Mark"),
            ("result", "Result"),
            ("status", "Workflow Status"),
            ("assessor_code", "Assessor"),
            ("moderator_code", "Moderator"),
            ("return_reason", "Return Reason"),
            ("assessment_date", "Assessment Date"),
        ],
        rows=rows,
        filters=f,
    )
