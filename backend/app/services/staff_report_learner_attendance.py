from app.services.staff_report_common import (
    active_class_lateral,
    fetch_rows,
    make_report,
)


def learner_report(code: str, f: dict) -> dict:
    if code == "learner.enrolment":
        rows = fetch_rows(
            f"""
            SELECT
                r.student_number,
                CONCAT_WS(' ', a.first_name, a.middle_name, a.last_name) AS learner_name,
                r.course_code,
                c.course_name,
                COALESCE(cl.cycle_code, r.cycle) AS cycle_code,
                cl.class_code,
                cl.class_group,
                r.registration_date,
                r.registration_status,
                r.funding_type,
                r.program_start_date,
                r.expected_completion_date
            FROM public.registrations r
            JOIN public.applications a
                ON a.id = r.application_id
            JOIN public.courses c
                ON c.course_code = r.course_code
            {active_class_lateral()}
            WHERE
                (:cycle_code IS NULL OR COALESCE(cl.cycle_code, r.cycle) = :cycle_code)
                AND (:course_code IS NULL OR r.course_code = :course_code)
                AND (:class_code IS NULL OR cl.class_code = :class_code)
                AND (:date_from IS NULL OR r.registration_date >= :date_from)
                AND (:date_to IS NULL OR r.registration_date <= :date_to)
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
                ("cycle_code", "Cycle"),
                ("class_code", "Class"),
                ("class_group", "Group"),
                ("registration_date", "Registered"),
                ("registration_status", "Status"),
                ("funding_type", "Funding"),
                ("program_start_date", "Start"),
                ("expected_completion_date", "Expected Completion"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "learner.demographics":
        rows = fetch_rows(
            f"""
            SELECT
                r.student_number,
                CONCAT_WS(' ', a.first_name, a.middle_name, a.last_name) AS learner_name,
                a.gender_code,
                a.birth_date,
                DATE_PART('year', AGE(CURRENT_DATE, a.birth_date))::integer AS age,
                a.equity_code,
                a.nationality_code,
                a.home_language,
                a.disability_status,
                a.province_code,
                a.employment_status,
                c.course_name,
                COALESCE(cl.cycle_code, r.cycle) AS cycle_code,
                cl.class_code
            FROM public.registrations r
            JOIN public.applications a
                ON a.id = r.application_id
            JOIN public.courses c
                ON c.course_code = r.course_code
            {active_class_lateral()}
            WHERE
                (:cycle_code IS NULL OR COALESCE(cl.cycle_code, r.cycle) = :cycle_code)
                AND (:course_code IS NULL OR r.course_code = :course_code)
                AND (:class_code IS NULL OR cl.class_code = :class_code)
            ORDER BY c.course_name, learner_name
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("student_number", "Student No."),
                ("learner_name", "Learner"),
                ("gender_code", "Gender"),
                ("birth_date", "DOB"),
                ("age", "Age"),
                ("equity_code", "Equity"),
                ("nationality_code", "Nationality"),
                ("home_language", "Home Language"),
                ("disability_status", "Disability"),
                ("province_code", "Province"),
                ("employment_status", "Employment"),
                ("course_name", "Programme"),
                ("cycle_code", "Cycle"),
                ("class_code", "Class"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "learner.status":
        rows = fetch_rows(
            f"""
            SELECT
                r.student_number,
                CONCAT_WS(' ', a.first_name, a.middle_name, a.last_name) AS learner_name,
                c.course_name,
                COALESCE(cl.cycle_code, r.cycle) AS cycle_code,
                cl.class_code,
                a.app_status,
                r.registration_status,
                a.eisa_readiness,
                r.eisa_eligible,
                a.sor_status,
                a.graduation_date,
                r.expected_completion_date
            FROM public.registrations r
            JOIN public.applications a
                ON a.id = r.application_id
            JOIN public.courses c
                ON c.course_code = r.course_code
            {active_class_lateral()}
            WHERE
                (:cycle_code IS NULL OR COALESCE(cl.cycle_code, r.cycle) = :cycle_code)
                AND (:course_code IS NULL OR r.course_code = :course_code)
                AND (:class_code IS NULL OR cl.class_code = :class_code)
            ORDER BY r.registration_status, learner_name
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
                ("app_status", "Application"),
                ("registration_status", "Registration"),
                ("eisa_readiness", "EISA Readiness"),
                ("eisa_eligible", "EISA Eligible"),
                ("sor_status", "SoR Status"),
                ("graduation_date", "Graduation"),
                ("expected_completion_date", "Expected Completion"),
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
            COALESCE(cl.cycle_code, r.cycle) AS cycle_code,
            cl.class_code,
            r.registration_status,
            a.archive_type,
            a.archive_reason,
            a.archive_date,
            r.updated_at AS last_updated
        FROM public.registrations r
        JOIN public.applications a
            ON a.id = r.application_id
        JOIN public.courses c
            ON c.course_code = r.course_code
        {active_class_lateral()}
        WHERE
            (
                r.registration_status IN ('Withdrawn', 'Cancelled')
                OR a.archive_type IS NOT NULL
            )
            AND (:cycle_code IS NULL OR COALESCE(cl.cycle_code, r.cycle) = :cycle_code)
            AND (:course_code IS NULL OR r.course_code = :course_code)
            AND (:class_code IS NULL OR cl.class_code = :class_code)
            AND (:date_from IS NULL OR COALESCE(a.archive_date, r.updated_at::date) >= :date_from)
            AND (:date_to IS NULL OR COALESCE(a.archive_date, r.updated_at::date) <= :date_to)
        ORDER BY COALESCE(a.archive_date, r.updated_at::date) DESC
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
            ("registration_status", "Registration Status"),
            ("archive_type", "Archive Type"),
            ("archive_reason", "Reason"),
            ("archive_date", "Archive Date"),
            ("last_updated", "Last Updated"),
        ],
        rows=rows,
        filters=f,
    )


def attendance_report(code: str, f: dict) -> dict:
    if code == "attendance.weekly":
        rows = fetch_rows(
            """
            SELECT
                d.register_date,
                b.control_number,
                cl.class_code,
                cl.class_group,
                cl.course_code,
                cl.cycle_code,
                r.student_number,
                CONCAT_WS(' ', a.first_name, a.middle_name, a.last_name) AS learner_name,
                w.attendance_status,
                w.sign_in_time,
                w.sign_out_time,
                w.notes,
                w.captured_by
            FROM public.attendance_weekly_capture_records w
            JOIN public.attendance_register_days d
                ON d.id = w.register_day_id
            JOIN public.attendance_register_batches b
                ON b.id = w.batch_id
            JOIN public.classes cl
                ON cl.id = b.class_id
            JOIN public.registrations r
                ON r.id = w.registration_id
            JOIN public.applications a
                ON a.id = r.application_id
            WHERE
                (:cycle_code IS NULL OR cl.cycle_code = :cycle_code)
                AND (:course_code IS NULL OR cl.course_code = :course_code)
                AND (:class_code IS NULL OR cl.class_code = :class_code)
                AND (:date_from IS NULL OR d.register_date >= :date_from)
                AND (:date_to IS NULL OR d.register_date <= :date_to)
            ORDER BY d.register_date, cl.class_code, learner_name
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("register_date", "Date"),
                ("control_number", "Register"),
                ("class_code", "Class"),
                ("class_group", "Group"),
                ("course_code", "Course"),
                ("cycle_code", "Cycle"),
                ("student_number", "Student No."),
                ("learner_name", "Learner"),
                ("attendance_status", "Status"),
                ("sign_in_time", "Sign In"),
                ("sign_out_time", "Sign Out"),
                ("captured_by", "Captured By"),
            ],
            rows=rows,
            filters=f,
        )

    base = """
        FROM public.attendance_records ar
        JOIN public.attendance_sessions ats
            ON ats.id = ar.attendance_session_id
        JOIN public.timetable_sessions ts
            ON ts.id = ats.timetable_session_id
        JOIN public.classes cl
            ON cl.id = ts.class_id
        JOIN public.registrations r
            ON r.id = ar.registration_id
        JOIN public.applications a
            ON a.id = r.application_id
        LEFT JOIN public.modules m
            ON m.id = ts.module_id
        WHERE
            (:cycle_code IS NULL OR cl.cycle_code = :cycle_code)
            AND (:course_code IS NULL OR cl.course_code = :course_code)
            AND (:class_code IS NULL OR cl.class_code = :class_code)
            AND (:date_from IS NULL OR ts.session_date >= :date_from)
            AND (:date_to IS NULL OR ts.session_date <= :date_to)
    """

    if code == "attendance.daily":
        rows = fetch_rows(
            f"""
            SELECT
                ts.session_date,
                cl.class_code,
                cl.class_group,
                m.module_code,
                m.module_name,
                ts.session_title,
                r.student_number,
                CONCAT_WS(' ', a.first_name, a.middle_name, a.last_name) AS learner_name,
                ar.attendance_status,
                ar.minutes_late,
                ar.notes,
                ar.captured_by,
                ats.status AS session_status
            {base}
            ORDER BY ts.session_date, cl.class_code, learner_name
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("session_date", "Date"),
                ("class_code", "Class"),
                ("class_group", "Group"),
                ("module_code", "Module"),
                ("module_name", "Module Name"),
                ("session_title", "Session"),
                ("student_number", "Student No."),
                ("learner_name", "Learner"),
                ("attendance_status", "Status"),
                ("minutes_late", "Minutes Late"),
                ("session_status", "Register Status"),
                ("captured_by", "Captured By"),
            ],
            rows=rows,
            filters=f,
        )

    if code == "attendance.exceptions":
        rows = fetch_rows(
            f"""
            SELECT
                ts.session_date,
                cl.class_code,
                m.module_code,
                ts.session_title,
                r.student_number,
                CONCAT_WS(' ', a.first_name, a.middle_name, a.last_name) AS learner_name,
                ar.attendance_status,
                ar.minutes_late,
                ar.notes,
                ats.status AS register_status,
                ats.return_reason
            {base}
                AND (
                    ar.attendance_status IN ('Absent', 'Late')
                    OR COALESCE(ar.minutes_late, 0) > 0
                    OR ats.status = 'Returned'
                )
            ORDER BY ts.session_date DESC, cl.class_code, learner_name
            """,
            f,
        )
        return make_report(
            code,
            columns=[
                ("session_date", "Date"),
                ("class_code", "Class"),
                ("module_code", "Module"),
                ("session_title", "Session"),
                ("student_number", "Student No."),
                ("learner_name", "Learner"),
                ("attendance_status", "Attendance"),
                ("minutes_late", "Minutes Late"),
                ("register_status", "Register Status"),
                ("return_reason", "Return Reason"),
                ("notes", "Notes"),
            ],
            rows=rows,
            filters=f,
        )

    rows = fetch_rows(
        f"""
        SELECT
            cl.class_code,
            cl.course_code,
            cl.cycle_code,
            m.module_code,
            m.module_name,
            r.student_number,
            CONCAT_WS(' ', a.first_name, a.middle_name, a.last_name) AS learner_name,
            COUNT(*) AS sessions_recorded,
            COUNT(*) FILTER (WHERE ar.attendance_status = 'Present') AS present_count,
            COUNT(*) FILTER (WHERE ar.attendance_status = 'Late') AS late_count,
            COUNT(*) FILTER (WHERE ar.attendance_status = 'Absent') AS absent_count,
            COUNT(*) FILTER (WHERE ar.attendance_status = 'Excused') AS excused_count,
            ROUND(
                (
                    100.0
                    * COUNT(*) FILTER (
                        WHERE ar.attendance_status IN ('Present', 'Late')
                    )
                    / NULLIF(COUNT(*), 0)
                )::numeric,
                2
            ) AS attendance_rate
        {base}
        GROUP BY
            cl.class_code,
            cl.course_code,
            cl.cycle_code,
            m.module_code,
            m.module_name,
            r.student_number,
            a.first_name,
            a.middle_name,
            a.last_name
        ORDER BY cl.class_code, m.module_code, learner_name
        """,
        f,
    )
    return make_report(
        code,
        columns=[
            ("class_code", "Class"),
            ("course_code", "Course"),
            ("cycle_code", "Cycle"),
            ("module_code", "Module"),
            ("module_name", "Module Name"),
            ("student_number", "Student No."),
            ("learner_name", "Learner"),
            ("sessions_recorded", "Sessions"),
            ("present_count", "Present"),
            ("late_count", "Late"),
            ("absent_count", "Absent"),
            ("excused_count", "Excused"),
            ("attendance_rate", "Attendance %"),
        ],
        rows=rows,
        filters=f,
    )
