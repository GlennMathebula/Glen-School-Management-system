from app.services.staff_report_common import (
    fetch_rows,
    make_report,
)


def wm_completion_report(code: str, f: dict) -> dict:
    rows = fetch_rows(
        """
        SELECT
            r.student_number,
            CONCAT_WS(' ', a.first_name, a.middle_name, a.last_name) AS learner_name,
            c.course_name,
            r.cycle AS cycle_code,
            m.module_code,
            m.module_name,
            mr.status AS module_registration_status,
            mr.completed_at,
            latest_mark.mark,
            latest_mark.result,
            latest_mark.status AS assessment_status
        FROM public.module_registrations mr
        JOIN public.modules m
            ON m.id = mr.module_id
        JOIN public.registrations r
            ON r.id = mr.registration_id
        JOIN public.applications a
            ON a.id = r.application_id
        JOIN public.courses c
            ON c.course_code = r.course_code
        LEFT JOIN LATERAL (
            SELECT
                mk.mark,
                mk.result,
                mk.status
            FROM public.marks mk
            WHERE mk.module_registration_id = mr.id
            ORDER BY mk.attempt_number DESC, mk.created_at DESC
            LIMIT 1
        ) latest_mark ON TRUE
        WHERE
            m.module_type = 'WM'
            AND (:cycle_code IS NULL OR r.cycle = :cycle_code)
            AND (:course_code IS NULL OR r.course_code = :course_code)
        ORDER BY c.course_name, learner_name, m.module_code
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
            ("module_code", "WM"),
            ("module_name", "Work Experience Module"),
            ("module_registration_status", "Module Status"),
            ("completed_at", "Completed At"),
            ("mark", "Mark"),
            ("result", "Result"),
            ("assessment_status", "Assessment Status"),
        ],
        rows=rows,
        filters=f,
    )


def eisa_report(code: str, f: dict) -> dict:
    if code in {"eisa.readiness", "eisa.registration"}:
        rows = fetch_rows(
            """
            SELECT
                r.student_number,
                CONCAT_WS(' ', a.first_name, a.middle_name, a.last_name) AS learner_name,
                r.course_code,
                c.course_name,
                r.cycle AS cycle_code,
                r.registration_status,
                r.eisa_eligible,
                a.eisa_readiness,
                a.flc,
                a.flc_sor_number,
                a.assessment_centre,
                eisa.id IS NOT NULL AS eisa_record_exists,
                eisa.assessment_date AS eisa_assessment_date,
                eisa.status AS eisa_status
            FROM public.registrations r
            JOIN public.applications a
                ON a.id = r.application_id
            JOIN public.courses c
                ON c.course_code = r.course_code
            LEFT JOIN LATERAL (
                SELECT
                    sa.id,
                    sa.assessment_date,
                    sa.status
                FROM public.summative_assessments sa
                WHERE
                    sa.registration_id = r.id
                    AND sa.assessment_type = 'EISA'
                ORDER BY sa.attempt_number DESC, sa.created_at DESC
                LIMIT 1
            ) eisa ON TRUE
            WHERE
                LOWER(COALESCE(c.assessment_type, '')) = 'fisa + eisa'
                AND (:cycle_code IS NULL OR r.cycle = :cycle_code)
                AND (:course_code IS NULL OR r.course_code = :course_code)
            ORDER BY c.course_name, learner_name
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
                ("registration_status", "Registration"),
                ("eisa_eligible", "Eligible"),
                ("eisa_readiness", "Readiness"),
                ("flc", "FLC"),
                ("flc_sor_number", "FLC SoR"),
                ("assessment_centre", "Assessment Centre"),
                ("eisa_record_exists", "EISA Record"),
                ("eisa_assessment_date", "EISA Date"),
                ("eisa_status", "EISA Status"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "eisa.results":
        rows = fetch_rows(
            """
            SELECT
                r.student_number,
                CONCAT_WS(' ', a.first_name, a.middle_name, a.last_name) AS learner_name,
                c.course_name,
                r.cycle AS cycle_code,
                sa.attempt_number,
                sa.assessment_date,
                sa.mark,
                sa.result,
                sa.status,
                sa.assessor_code,
                sa.moderator_code
            FROM public.summative_assessments sa
            JOIN public.registrations r
                ON r.id = sa.registration_id
            JOIN public.applications a
                ON a.id = r.application_id
            JOIN public.courses c
                ON c.course_code = r.course_code
            WHERE
                sa.assessment_type = 'EISA'
                AND (:cycle_code IS NULL OR r.cycle = :cycle_code)
                AND (:course_code IS NULL OR r.course_code = :course_code)
                AND (:date_from IS NULL OR sa.assessment_date::date >= :date_from)
                AND (:date_to IS NULL OR sa.assessment_date::date <= :date_to)
            ORDER BY sa.assessment_date DESC, learner_name
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
                ("attempt_number", "Attempt"),
                ("assessment_date", "Assessment Date"),
                ("mark", "Mark"),
                ("result", "Result"),
                ("status", "Status"),
                ("assessor_code", "Assessor"),
                ("moderator_code", "Moderator"),
            ],
            rows=rows,
            filters=f,
        )

    rows = fetch_rows(
        """
        SELECT
            r.student_number,
            CONCAT_WS(' ', a.first_name, a.middle_name, a.last_name) AS learner_name,
            c.course_name,
            r.cycle AS cycle_code,
            r.registration_status,
            a.sor_status,
            a.sor_date,
            a.graduation_date,
            r.expected_completion_date,
            a.eisa_readiness,
            r.eisa_eligible
        FROM public.registrations r
        JOIN public.applications a
            ON a.id = r.application_id
        JOIN public.courses c
            ON c.course_code = r.course_code
        WHERE
            LOWER(COALESCE(c.assessment_type, '')) = 'fisa + eisa'
            AND (:cycle_code IS NULL OR r.cycle = :cycle_code)
            AND (:course_code IS NULL OR r.course_code = :course_code)
        ORDER BY c.course_name, learner_name
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
            ("registration_status", "Registration"),
            ("eisa_eligible", "EISA Eligible"),
            ("eisa_readiness", "EISA Readiness"),
            ("sor_status", "SoR Status"),
            ("sor_date", "SoR Date"),
            ("graduation_date", "Graduation Date"),
            ("expected_completion_date", "Expected Completion"),
        ],
        rows=rows,
        filters=f,
    )


def _skills_predicate() -> str:
    return """
        (
            LOWER(COALESCE(c.qualification_type, '')) LIKE '%skill%'
            OR LOWER(COALESCE(c.assessment_type, '')) = 'fisa only'
        )
    """


def skills_report(code: str, f: dict) -> dict:
    if code == "skills_programme.enrolment":
        rows = fetch_rows(
            f"""
            SELECT
                r.student_number,
                CONCAT_WS(' ', a.first_name, a.middle_name, a.last_name) AS learner_name,
                r.course_code,
                c.course_name,
                c.nqf_level,
                c.credits,
                r.cycle AS cycle_code,
                r.registration_date,
                r.registration_status,
                r.expected_completion_date
            FROM public.registrations r
            JOIN public.applications a
                ON a.id = r.application_id
            JOIN public.courses c
                ON c.course_code = r.course_code
            WHERE
                {_skills_predicate()}
                AND (:cycle_code IS NULL OR r.cycle = :cycle_code)
                AND (:course_code IS NULL OR r.course_code = :course_code)
            ORDER BY c.course_name, learner_name
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("student_number", "Student No."),
                ("learner_name", "Learner"),
                ("course_code", "Course"),
                ("course_name", "Programme"),
                ("nqf_level", "NQF"),
                ("credits", "Credits"),
                ("cycle_code", "Cycle"),
                ("registration_date", "Registered"),
                ("registration_status", "Status"),
                ("expected_completion_date", "Expected Completion"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "skills_programme.implementation":
        rows = fetch_rows(
            f"""
            SELECT
                c.course_code,
                c.course_name,
                cl.cycle_code,
                cl.class_code,
                m.module_type,
                m.module_code,
                m.module_name,
                COUNT(DISTINCT ts.id) AS scheduled_sessions,
                COUNT(DISTINCT ts.id) FILTER (
                    WHERE ts.status = 'Published'
                ) AS published_sessions,
                MIN(ts.session_date) AS first_session,
                MAX(ts.session_date) AS last_session
            FROM public.courses c
            LEFT JOIN public.modules m
                ON m.course_code = c.course_code
            LEFT JOIN public.classes cl
                ON cl.course_code = c.course_code
            LEFT JOIN public.timetable_sessions ts
                ON ts.class_id = cl.id
                AND ts.module_id = m.id
            WHERE
                {_skills_predicate()}
                AND (:cycle_code IS NULL OR cl.cycle_code = :cycle_code)
                AND (:course_code IS NULL OR c.course_code = :course_code)
                AND (:class_code IS NULL OR cl.class_code = :class_code)
                AND (:date_from IS NULL OR ts.session_date >= :date_from)
                AND (:date_to IS NULL OR ts.session_date <= :date_to)
            GROUP BY
                c.course_code,
                c.course_name,
                cl.cycle_code,
                cl.class_code,
                m.module_type,
                m.module_code,
                m.module_name
            ORDER BY c.course_name, cl.class_code, m.module_code
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("course_code", "Course"),
                ("course_name", "Programme"),
                ("cycle_code", "Cycle"),
                ("class_code", "Class"),
                ("module_type", "Type"),
                ("module_code", "Module"),
                ("module_name", "Module Name"),
                ("scheduled_sessions", "Scheduled"),
                ("published_sessions", "Published"),
                ("first_session", "First Session"),
                ("last_session", "Last Session"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "skills_programme.fisa":
        rows = fetch_rows(
            f"""
            SELECT
                fs.sitting_reference,
                fs.course_code,
                c.course_name,
                fs.cycle_code,
                fs.assessment_date,
                fs.venue,
                fs.status,
                r.student_number,
                CONCAT_WS(' ', a.first_name, a.middle_name, a.last_name) AS learner_name,
                fsc.seat_number,
                fsc.admission_status,
                fsc.attendance_status
            FROM public.fisa_sittings fs
            JOIN public.courses c
                ON c.course_code = fs.course_code
            LEFT JOIN public.fisa_sitting_candidates fsc
                ON fsc.sitting_id = fs.id
            LEFT JOIN public.registrations r
                ON r.id = fsc.registration_id
            LEFT JOIN public.applications a
                ON a.id = r.application_id
            WHERE
                {_skills_predicate()}
                AND (:cycle_code IS NULL OR fs.cycle_code = :cycle_code)
                AND (:course_code IS NULL OR fs.course_code = :course_code)
                AND (:date_from IS NULL OR fs.assessment_date >= :date_from)
                AND (:date_to IS NULL OR fs.assessment_date <= :date_to)
            ORDER BY fs.assessment_date, fs.sitting_reference, fsc.seat_number
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("sitting_reference", "Sitting"),
                ("course_name", "Programme"),
                ("cycle_code", "Cycle"),
                ("assessment_date", "Date"),
                ("venue", "Venue"),
                ("status", "Sitting Status"),
                ("student_number", "Student No."),
                ("learner_name", "Learner"),
                ("seat_number", "Seat"),
                ("admission_status", "Admission"),
                ("attendance_status", "Attendance"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "skills_programme.results":
        rows = fetch_rows(
            f"""
            SELECT
                r.student_number,
                CONCAT_WS(' ', a.first_name, a.middle_name, a.last_name) AS learner_name,
                c.course_name,
                r.cycle AS cycle_code,
                sa.attempt_number,
                sa.assessment_date,
                sa.mark,
                sa.result,
                sa.status
            FROM public.summative_assessments sa
            JOIN public.registrations r
                ON r.id = sa.registration_id
            JOIN public.applications a
                ON a.id = r.application_id
            JOIN public.courses c
                ON c.course_code = r.course_code
            WHERE
                sa.assessment_type = 'FISA'
                AND {_skills_predicate()}
                AND (:cycle_code IS NULL OR r.cycle = :cycle_code)
                AND (:course_code IS NULL OR r.course_code = :course_code)
            ORDER BY sa.assessment_date DESC, learner_name
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
                ("attempt_number", "Attempt"),
                ("assessment_date", "FISA Date"),
                ("mark", "Mark"),
                ("result", "Result"),
                ("status", "Status"),
            ],
            rows=rows,
            filters=f,
        )

    rows = fetch_rows(
        f"""
        SELECT
            r.student_number,
            CONCAT_WS(' ', a.first_name, a.middle_name, a.last_name) AS learner_name,
            c.course_name,
            r.cycle AS cycle_code,
            r.registration_status,
            r.expected_completion_date,
            latest_fisa.mark AS fisa_mark,
            latest_fisa.result AS fisa_result,
            latest_fisa.status AS fisa_status,
            a.sor_status,
            a.sor_date,
            a.graduation_date
        FROM public.registrations r
        JOIN public.applications a
            ON a.id = r.application_id
        JOIN public.courses c
            ON c.course_code = r.course_code
        LEFT JOIN LATERAL (
            SELECT
                sa.mark,
                sa.result,
                sa.status
            FROM public.summative_assessments sa
            WHERE
                sa.registration_id = r.id
                AND sa.assessment_type = 'FISA'
            ORDER BY sa.attempt_number DESC, sa.created_at DESC
            LIMIT 1
        ) latest_fisa ON TRUE
        WHERE
            {_skills_predicate()}
            AND (:cycle_code IS NULL OR r.cycle = :cycle_code)
            AND (:course_code IS NULL OR r.course_code = :course_code)
        ORDER BY c.course_name, learner_name
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
            ("registration_status", "Registration"),
            ("expected_completion_date", "Expected Completion"),
            ("fisa_mark", "FISA Mark"),
            ("fisa_result", "FISA Result"),
            ("fisa_status", "FISA Status"),
            ("sor_status", "SoR Status"),
            ("sor_date", "SoR Date"),
            ("graduation_date", "Completion/Graduation"),
        ],
        rows=rows,
        filters=f,
    )


def _compliance_rows(f: dict) -> list[dict]:
    return fetch_rows(
        """
        SELECT
            cy.cycle_code,
            cy.cycle_name,
            cy.status AS cycle_status,
            cl.class_code,
            cl.class_name,
            cl.class_group,
            c.course_code,
            c.course_name,
            cl.status AS class_status,
            cl.facilitator_code,
            cl.assessor_code,
            COUNT(DISTINCT m.id) AS module_count,
            COUNT(DISTINCT ce.id) FILTER (
                WHERE ce.status = 'Active'
            ) AS active_learners,
            COUNT(DISTINCT ts.id) FILTER (
                WHERE ts.status = 'Published'
            ) AS published_sessions,
            COUNT(DISTINCT lr.id) FILTER (
                WHERE lr.status = 'Published'
            ) AS published_resources,
            CASE
                WHEN cl.facilitator_code IS NULL THEN 'FAIL'
                WHEN cl.assessor_code IS NULL THEN 'FAIL'
                WHEN COUNT(DISTINCT m.id) = 0 THEN 'FAIL'
                WHEN COUNT(DISTINCT ce.id) FILTER (
                    WHERE ce.status = 'Active'
                ) = 0 THEN 'WARNING'
                WHEN COUNT(DISTINCT ts.id) FILTER (
                    WHERE ts.status = 'Published'
                ) = 0 THEN 'WARNING'
                ELSE 'PASS'
            END AS compliance_status
        FROM public.classes cl
        LEFT JOIN public.cycles cy
            ON cy.cycle_code = cl.cycle_code
        JOIN public.courses c
            ON c.course_code = cl.course_code
        LEFT JOIN public.modules m
            ON m.course_code = cl.course_code
            AND m.status = 'Active'
        LEFT JOIN public.class_enrolments ce
            ON ce.class_id = cl.id
        LEFT JOIN public.timetable_sessions ts
            ON ts.class_id = cl.id
            AND (:date_from IS NULL OR ts.session_date >= :date_from)
            AND (:date_to IS NULL OR ts.session_date <= :date_to)
        LEFT JOIN public.learning_resources lr
            ON lr.class_id = cl.id
        WHERE
            (:cycle_code IS NULL OR cl.cycle_code = :cycle_code)
            AND (:course_code IS NULL OR cl.course_code = :course_code)
            AND (:class_code IS NULL OR cl.class_code = :class_code)
        GROUP BY
            cy.cycle_code,
            cy.cycle_name,
            cy.status,
            cl.id,
            c.course_code,
            c.course_name
        ORDER BY cy.cycle_code, c.course_name, cl.class_code
        """,
        f,
    )


def quality_report(code: str, f: dict) -> dict:
    if code == "quality.compliance_checklist":
        rows = _compliance_rows(f)
        failed = sum(1 for row in rows if row["compliance_status"] == "FAIL")
        warnings = sum(1 for row in rows if row["compliance_status"] == "WARNING")
        return make_report(
            code,
            columns=[
                ("cycle_code", "Cycle"),
                ("cycle_status", "Cycle Status"),
                ("class_code", "Class"),
                ("class_group", "Group"),
                ("course_name", "Programme"),
                ("class_status", "Class Status"),
                ("facilitator_code", "Facilitator"),
                ("assessor_code", "Assessor"),
                ("module_count", "Modules"),
                ("active_learners", "Active Learners"),
                ("published_sessions", "Published Sessions"),
                ("published_resources", "Resources"),
                ("compliance_status", "Compliance"),
            ],
            rows=rows,
            filters=f,
            summary={
                "record_count": len(rows),
                "failed_checks": failed,
                "warning_checks": warnings,
            },
        )

    if code == "quality.internal_qa":
        rows = fetch_rows(
            """
            SELECT *
            FROM (
                SELECT
                    'Module Assessment' AS qa_area,
                    r.student_number AS reference,
                    r.course_code,
                    r.cycle AS cycle_code,
                    mk.status,
                    mk.assessor_code AS responsible_staff,
                    mk.moderator_code AS reviewer_staff,
                    mk.return_reason AS finding,
                    mk.updated_at AS event_date
                FROM public.marks mk
                JOIN public.module_registrations mr
                    ON mr.id = mk.module_registration_id
                JOIN public.registrations r
                    ON r.id = mr.registration_id
                WHERE mk.status IN ('Returned', 'Moderated', 'Published')

                UNION ALL

                SELECT
                    'Summative Assessment',
                    r.student_number,
                    r.course_code,
                    r.cycle,
                    sa.status,
                    sa.assessor_code,
                    sa.moderator_code,
                    sa.return_reason,
                    sa.updated_at
                FROM public.summative_assessments sa
                JOIN public.registrations r
                    ON r.id = sa.registration_id
                WHERE sa.status IN ('Returned', 'Moderated', 'Published')

                UNION ALL

                SELECT
                    'Attendance Register',
                    cl.class_code,
                    cl.course_code,
                    cl.cycle_code,
                    ats.status,
                    ats.captured_by,
                    ats.rendered_by,
                    ats.return_reason,
                    ats.updated_at
                FROM public.attendance_sessions ats
                JOIN public.timetable_sessions ts
                    ON ts.id = ats.timetable_session_id
                JOIN public.classes cl
                    ON cl.id = ts.class_id
                WHERE ats.status IN ('Returned', 'Rendered')
            ) q
            WHERE
                (:cycle_code IS NULL OR q.cycle_code = :cycle_code)
                AND (:course_code IS NULL OR q.course_code = :course_code)
                AND (:date_from IS NULL OR q.event_date::date >= :date_from)
                AND (:date_to IS NULL OR q.event_date::date <= :date_to)
            ORDER BY q.event_date DESC
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("qa_area", "QA Area"),
                ("reference", "Reference"),
                ("course_code", "Course"),
                ("cycle_code", "Cycle"),
                ("status", "Status"),
                ("responsible_staff", "Responsible"),
                ("reviewer_staff", "Reviewer"),
                ("finding", "Finding / Return Reason"),
                ("event_date", "Event Date"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "quality.findings_register":
        rows = []
        for row in _compliance_rows(f):
            if row["compliance_status"] == "PASS":
                continue
            findings = []
            if not row.get("facilitator_code"):
                findings.append("Facilitator not assigned")
            if not row.get("assessor_code"):
                findings.append("Assessor not assigned")
            if not row.get("module_count"):
                findings.append("No active modules configured")
            if not row.get("active_learners"):
                findings.append("No active learner enrolments")
            if not row.get("published_sessions"):
                findings.append("No published timetable sessions")
            rows.append(
                {
                    "cycle_code": row.get("cycle_code"),
                    "reference": row.get("class_code"),
                    "programme": row.get("course_name"),
                    "severity": "High" if row["compliance_status"] == "FAIL" else "Medium",
                    "finding": "; ".join(findings),
                    "status": "Open",
                }
            )

        returned = fetch_rows(
            """
            SELECT
                r.cycle AS cycle_code,
                r.student_number AS reference,
                r.course_code AS programme,
                'Medium' AS severity,
                COALESCE(mk.return_reason, 'Assessment returned by Moderator') AS finding,
                'Open' AS status
            FROM public.marks mk
            JOIN public.module_registrations mr
                ON mr.id = mk.module_registration_id
            JOIN public.registrations r
                ON r.id = mr.registration_id
            WHERE
                mk.status = 'Returned'
                AND (:cycle_code IS NULL OR r.cycle = :cycle_code)
                AND (:course_code IS NULL OR r.course_code = :course_code)
                AND (:date_from IS NULL OR mk.updated_at::date >= :date_from)
                AND (:date_to IS NULL OR mk.updated_at::date <= :date_to)
            """,
            f,
        )
        rows.extend(returned)

        return make_report(
            code,
            columns=[
                ("cycle_code", "Cycle"),
                ("reference", "Reference"),
                ("programme", "Programme/Course"),
                ("severity", "Severity"),
                ("finding", "Finding"),
                ("status", "Status"),
            ],
            rows=rows,
            filters=f,
        )

    rows = fetch_rows(
        """
        SELECT
            cy.cycle_code,
            cy.cycle_name,
            cy.status AS cycle_status,
            cy.program_start_date,
            cy.expected_completion_date,
            COUNT(DISTINCT r.id) AS registered_learners,
            COUNT(DISTINCT r.id) FILTER (
                WHERE r.registration_status = 'Completed'
            ) AS completed_learners,
            COUNT(DISTINCT cl.id) AS class_count,
            COUNT(DISTINCT cl.id) FILTER (
                WHERE cl.facilitator_code IS NULL OR cl.assessor_code IS NULL
            ) AS classes_missing_staff,
            COUNT(DISTINCT ats.id) FILTER (
                WHERE ats.status = 'Returned'
            ) AS returned_attendance_registers,
            COUNT(DISTINCT sa.id) FILTER (
                WHERE sa.status = 'Returned'
            ) AS returned_summative_assessments
        FROM public.cycles cy
        LEFT JOIN public.registrations r
            ON r.cycle = cy.cycle_code
        LEFT JOIN public.classes cl
            ON cl.cycle_code = cy.cycle_code
        LEFT JOIN public.timetable_sessions ts
            ON ts.class_id = cl.id
        LEFT JOIN public.attendance_sessions ats
            ON ats.timetable_session_id = ts.id
        LEFT JOIN public.summative_assessments sa
            ON sa.registration_id = r.id
        WHERE
            (:cycle_code IS NULL OR cy.cycle_code = :cycle_code)
            AND (
                :course_code IS NULL
                OR r.course_code = :course_code
                OR cl.course_code = :course_code
            )
        GROUP BY cy.id
        ORDER BY cy.program_start_date DESC
        """,
        f,
    )

    for row in rows:
        issues = (
            int(row.get("classes_missing_staff") or 0)
            + int(row.get("returned_attendance_registers") or 0)
            + int(row.get("returned_summative_assessments") or 0)
        )
        row["closeout_status"] = (
            "READY"
            if row.get("cycle_status") in {"Closed", "Archived"} and issues == 0
            else "OUTSTANDING"
        )

    return make_report(
        code,
        columns=[
            ("cycle_code", "Cycle"),
            ("cycle_name", "Cycle Name"),
            ("cycle_status", "Cycle Status"),
            ("program_start_date", "Start"),
            ("expected_completion_date", "Expected Completion"),
            ("registered_learners", "Registered"),
            ("completed_learners", "Completed"),
            ("class_count", "Classes"),
            ("classes_missing_staff", "Missing Staff"),
            ("returned_attendance_registers", "Returned Attendance"),
            ("returned_summative_assessments", "Returned Assessments"),
            ("closeout_status", "Close-out"),
        ],
        rows=rows,
        filters=f,
    )


def management_report(code: str, f: dict) -> dict:
    if code == "management.completion_statistics":
        rows = fetch_rows(
            """
            SELECT
                r.cycle AS cycle_code,
                r.course_code,
                c.course_name,
                COUNT(*) AS registered_learners,
                COUNT(*) FILTER (
                    WHERE r.registration_status = 'Completed'
                ) AS completed_learners,
                COUNT(*) FILTER (
                    WHERE r.registration_status = 'Withdrawn'
                ) AS withdrawn_learners,
                ROUND(
                    (
                        100.0
                        * COUNT(*) FILTER (
                            WHERE r.registration_status = 'Completed'
                        )
                        / NULLIF(COUNT(*), 0)
                    )::numeric,
                    2
                ) AS completion_rate
            FROM public.registrations r
            JOIN public.courses c
                ON c.course_code = r.course_code
            WHERE
                (:cycle_code IS NULL OR r.cycle = :cycle_code)
                AND (:course_code IS NULL OR r.course_code = :course_code)
            GROUP BY r.cycle, r.course_code, c.course_name
            ORDER BY r.cycle, c.course_name
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("cycle_code", "Cycle"),
                ("course_code", "Course"),
                ("course_name", "Programme"),
                ("registered_learners", "Registered"),
                ("completed_learners", "Completed"),
                ("withdrawn_learners", "Withdrawn"),
                ("completion_rate", "Completion %"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "management.assessment_statistics":
        rows = fetch_rows(
            """
            SELECT
                r.cycle AS cycle_code,
                r.course_code,
                c.course_name,
                sa.assessment_type,
                COUNT(*) AS assessment_records,
                COUNT(*) FILTER (
                    WHERE UPPER(COALESCE(sa.result, '')) IN (
                        'C', 'COMPETENT', 'PASS', 'PASSED'
                    )
                ) AS competent_count,
                COUNT(*) FILTER (
                    WHERE UPPER(COALESCE(sa.result, '')) IN (
                        'NYC', 'NOT YET COMPETENT', 'FAIL', 'FAILED'
                    )
                ) AS nyc_count,
                ROUND(AVG(sa.mark)::numeric, 2) AS average_mark
            FROM public.summative_assessments sa
            JOIN public.registrations r
                ON r.id = sa.registration_id
            JOIN public.courses c
                ON c.course_code = r.course_code
            WHERE
                (:cycle_code IS NULL OR r.cycle = :cycle_code)
                AND (:course_code IS NULL OR r.course_code = :course_code)
                AND (:date_from IS NULL OR sa.assessment_date::date >= :date_from)
                AND (:date_to IS NULL OR sa.assessment_date::date <= :date_to)
            GROUP BY r.cycle, r.course_code, c.course_name, sa.assessment_type
            ORDER BY r.cycle, c.course_name, sa.assessment_type
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("cycle_code", "Cycle"),
                ("course_code", "Course"),
                ("course_name", "Programme"),
                ("assessment_type", "Assessment"),
                ("assessment_records", "Records"),
                ("competent_count", "Competent"),
                ("nyc_count", "NYC"),
                ("average_mark", "Average Mark"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "management.attendance_statistics":
        rows = fetch_rows(
            """
            SELECT
                cl.cycle_code,
                cl.course_code,
                c.course_name,
                cl.class_code,
                cl.class_group,
                COUNT(ar.id) AS attendance_records,
                COUNT(ar.id) FILTER (
                    WHERE ar.attendance_status IN ('Present', 'Late')
                ) AS attended_records,
                COUNT(ar.id) FILTER (
                    WHERE ar.attendance_status = 'Absent'
                ) AS absent_records,
                ROUND(
                    (
                        100.0
                        * COUNT(ar.id) FILTER (
                            WHERE ar.attendance_status IN ('Present', 'Late')
                        )
                        / NULLIF(COUNT(ar.id), 0)
                    )::numeric,
                    2
                ) AS attendance_rate
            FROM public.classes cl
            JOIN public.courses c
                ON c.course_code = cl.course_code
            LEFT JOIN public.timetable_sessions ts
                ON ts.class_id = cl.id
            LEFT JOIN public.attendance_sessions ats
                ON ats.timetable_session_id = ts.id
            LEFT JOIN public.attendance_records ar
                ON ar.attendance_session_id = ats.id
            WHERE
                (:cycle_code IS NULL OR cl.cycle_code = :cycle_code)
                AND (:course_code IS NULL OR cl.course_code = :course_code)
                AND (:class_code IS NULL OR cl.class_code = :class_code)
                AND (:date_from IS NULL OR ts.session_date >= :date_from)
                AND (:date_to IS NULL OR ts.session_date <= :date_to)
            GROUP BY
                cl.cycle_code,
                cl.course_code,
                c.course_name,
                cl.class_code,
                cl.class_group
            ORDER BY cl.cycle_code, c.course_name, cl.class_code
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("cycle_code", "Cycle"),
                ("course_code", "Course"),
                ("course_name", "Programme"),
                ("class_code", "Class"),
                ("class_group", "Group"),
                ("attendance_records", "Records"),
                ("attended_records", "Present/Late"),
                ("absent_records", "Absent"),
                ("attendance_rate", "Attendance %"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "management.programme_closeout":
        rows = fetch_rows(
            """
            SELECT
                r.cycle AS cycle_code,
                r.course_code,
                c.course_name,
                COUNT(DISTINCT r.id) AS registered_learners,
                COUNT(DISTINCT r.id) FILTER (
                    WHERE r.registration_status = 'Completed'
                ) AS completed_learners,
                COUNT(DISTINCT sa.id) FILTER (
                    WHERE sa.status = 'Published'
                ) AS published_summative_results,
                COUNT(DISTINCT sa.id) FILTER (
                    WHERE sa.status = 'Returned'
                ) AS returned_summative_results,
                COUNT(DISTINCT ce.class_id) AS class_count
            FROM public.registrations r
            JOIN public.courses c
                ON c.course_code = r.course_code
            LEFT JOIN public.summative_assessments sa
                ON sa.registration_id = r.id
            LEFT JOIN public.class_enrolments ce
                ON ce.registration_id = r.id
            WHERE
                (:cycle_code IS NULL OR r.cycle = :cycle_code)
                AND (:course_code IS NULL OR r.course_code = :course_code)
            GROUP BY r.cycle, r.course_code, c.course_name
            ORDER BY r.cycle, c.course_name
            """,
            f,
        )
        for row in rows:
            registered = int(row.get("registered_learners") or 0)
            completed = int(row.get("completed_learners") or 0)
            returned = int(row.get("returned_summative_results") or 0)
            row["completion_rate"] = (
                round(100.0 * completed / registered, 2)
                if registered else 0
            )
            row["closeout_status"] = (
                "READY"
                if registered > 0 and completed == registered and returned == 0
                else "OUTSTANDING"
            )
        return make_report(
            code,
            columns=[
                ("cycle_code", "Cycle"),
                ("course_code", "Course"),
                ("course_name", "Programme"),
                ("registered_learners", "Registered"),
                ("completed_learners", "Completed"),
                ("completion_rate", "Completion %"),
                ("class_count", "Classes"),
                ("published_summative_results", "Published Results"),
                ("returned_summative_results", "Returned Results"),
                ("closeout_status", "Close-out"),
            ],
            rows=rows,
            filters=f,
        )

    rows = fetch_rows(
        """
        SELECT
            r.cycle AS cycle_code,
            r.course_code,
            c.course_name,
            cl.class_code,
            cl.class_group,
            COUNT(DISTINCT r.id) AS learner_count,
            COUNT(DISTINCT r.id) FILTER (
                WHERE r.registration_status = 'Completed'
            ) AS completed_learners,
            ROUND(AVG(sa.mark)::numeric, 2) AS average_summative_mark,
            COUNT(DISTINCT sa.id) FILTER (
                WHERE UPPER(COALESCE(sa.result, '')) IN (
                    'C', 'COMPETENT', 'PASS', 'PASSED'
                )
            ) AS competent_results,
            COUNT(DISTINCT sa.id) FILTER (
                WHERE UPPER(COALESCE(sa.result, '')) IN (
                    'NYC', 'NOT YET COMPETENT', 'FAIL', 'FAILED'
                )
            ) AS nyc_results
        FROM public.registrations r
        JOIN public.courses c
            ON c.course_code = r.course_code
        LEFT JOIN public.class_enrolments ce
            ON ce.registration_id = r.id
            AND ce.status = 'Active'
        LEFT JOIN public.classes cl
            ON cl.id = ce.class_id
        LEFT JOIN public.summative_assessments sa
            ON sa.registration_id = r.id
            AND sa.status = 'Published'
        WHERE
            (:cycle_code IS NULL OR r.cycle = :cycle_code)
            AND (:course_code IS NULL OR r.course_code = :course_code)
            AND (:class_code IS NULL OR cl.class_code = :class_code)
        GROUP BY
            r.cycle,
            r.course_code,
            c.course_name,
            cl.class_code,
            cl.class_group
        ORDER BY r.cycle, c.course_name, cl.class_code
        """,
        f,
    )
    return make_report(
        code,
        columns=[
            ("cycle_code", "Cycle"),
            ("course_code", "Course"),
            ("course_name", "Programme"),
            ("class_code", "Class"),
            ("class_group", "Group"),
            ("learner_count", "Learners"),
            ("completed_learners", "Completed"),
            ("average_summative_mark", "Avg Mark"),
            ("competent_results", "Competent"),
            ("nyc_results", "NYC"),
        ],
        rows=rows,
        filters=f,
    )
