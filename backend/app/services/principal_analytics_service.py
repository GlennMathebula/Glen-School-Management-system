"""Principal-only, aggregated institutional facts, scoped by academic cycle.

No learner-level personal information is returned or exported. The authorisation
boundary is the FastAPI route; this service never trusts a frontend role flag.
"""
from datetime import datetime, timezone

from sqlalchemy import text
from app.database import engine


def _rows(connection, sql, params=None):
    return [dict(r) for r in connection.execute(text(sql), params or {}).mappings().all()]


def _count(connection, sql, params=None):
    return int(connection.execute(text(sql), params or {}).scalar_one() or 0)


def _breakdown(connection, sql, params=None):
    """Normalise grouped SQL to frontend-safe {label, value} records."""
    result = []
    for row in _rows(connection, sql, params):
        result.append({"label": str(row["label"] or "Not recorded"), "value": int(row["value"] or 0)})
    return result


def _scope(field, cycle_code):
    # field names are fixed, internal SQL identifiers, never user-controlled.
    return f" WHERE {field} = :cycle_code" if cycle_code else ""


def _and_scope(field, cycle_code):
    return f" AND {field} = :cycle_code" if cycle_code else ""


def _sum(rows):
    return sum(int(r.get("value") or 0) for r in rows)


def _total(rows, field="amount"):
    return round(sum(float(r.get(field) or 0) for r in rows), 2)


def get_principal_statistics(cycle_code=None):
    """Return an internally consistent live database snapshot.

    Application, registration and other measures use their own native cycle
    associations. This avoids the misleading assumption that an accepted
    application is already a registration.
    """
    cycle_code = str(cycle_code or "").strip() or None
    if cycle_code and len(cycle_code) > 100:
        raise ValueError("Invalid cycle code.")
    params = {"cycle_code": cycle_code} if cycle_code else {}
    with engine.connect() as db:
        # One connection/transaction for the report; no database mutation.
        registered_cycles = _rows(db, """
            SELECT cycle_code, cycle_name, status, application_start_date,
                   application_end_date, program_start_date, expected_completion_date
              FROM public.cycles ORDER BY cycle_code DESC
        """)
        extra_cycles = _rows(db, """
            SELECT DISTINCT cycle_code FROM (
                SELECT application_cycle AS cycle_code FROM public.applications
                UNION ALL SELECT cycle AS cycle_code FROM public.registrations
            ) x WHERE cycle_code IS NOT NULL AND trim(cycle_code) <> ''
        """)
        codes = {r["cycle_code"] for r in registered_cycles} | {r["cycle_code"] for r in extra_cycles}
        if cycle_code and cycle_code not in codes:
            raise ValueError("The requested academic cycle does not exist.")
        cycles = [{"cycle_code": c, "cycle_name": next((r["cycle_name"] for r in registered_cycles if r["cycle_code"] == c), c)} for c in sorted(codes, reverse=True)]
        selected_cycle = next((r for r in registered_cycles if r["cycle_code"] == cycle_code), None)

        app_where = _scope("a.application_cycle", cycle_code)
        reg_where = _scope("r.cycle", cycle_code)
        app_and = _and_scope("a.application_cycle", cycle_code)
        reg_and = _and_scope("r.cycle", cycle_code)

        application_status = _breakdown(db, f"""
            SELECT COALESCE(NULLIF(trim(a.app_status), ''), 'Not recorded') AS label,
                   COUNT(*) AS value FROM public.applications a{app_where}
            GROUP BY 1 ORDER BY value DESC, label
        """, params)
        gender = _breakdown(db, f"""
            SELECT CASE WHEN upper(trim(coalesce(a.gender_code,''))) IN ('F','FEMALE') THEN 'Female'
                        WHEN upper(trim(coalesce(a.gender_code,''))) IN ('M','MALE') THEN 'Male'
                        WHEN trim(coalesce(a.gender_code,'')) = '' THEN 'Not recorded'
                        ELSE 'Other / unspecified' END AS label,
                   COUNT(*) AS value FROM public.applications a{app_where}
            GROUP BY 1 ORDER BY value DESC, label
        """, params)
        provinces = _breakdown(db, f"""
            SELECT COALESCE(NULLIF(trim(a.province_code),''),'Not recorded') AS label,
                   COUNT(*) AS value FROM public.applications a{app_where}
            GROUP BY 1 ORDER BY value DESC, label
        """, params)
        applicant_employment = _breakdown(db, f"""
            SELECT COALESCE(NULLIF(trim(a.employment_status),''),'Not recorded') AS label,
                   COUNT(*) AS value FROM public.applications a{app_where}
            GROUP BY 1 ORDER BY value DESC, label
        """, params)
        registrations_status = _breakdown(db, f"""
            SELECT COALESCE(NULLIF(trim(r.registration_status),''),'Not recorded') AS label,
                   COUNT(*) AS value FROM public.registrations r{reg_where}
            GROUP BY 1 ORDER BY value DESC, label
        """, params)

        apps_by_course = _rows(db, f"""
            SELECT a.qualification_id AS code,
                   COALESCE(MAX(c.course_name),MAX(a.course_name),a.qualification_id,'Unknown') AS name,
                   COUNT(*) AS applications
              FROM public.applications a
              LEFT JOIN public.courses c ON c.course_code = a.qualification_id
              {app_where}
             GROUP BY a.qualification_id ORDER BY applications DESC, code
        """, params)
        regs_by_course = _rows(db, f"""
            SELECT r.course_code AS code, COALESCE(MAX(c.course_name),r.course_code,'Unknown') AS name,
                   COUNT(*) AS registrations
              FROM public.registrations r LEFT JOIN public.courses c ON c.course_code = r.course_code
              {reg_where}
             GROUP BY r.course_code ORDER BY registrations DESC, code
        """, params)
        course_index = {}
        for item in apps_by_course:
            key = item["code"] or "Unknown"
            course_index[key] = {"code": key, "label": item["name"], "applications": int(item["applications"]), "registrations": 0}
        for item in regs_by_course:
            key = item["code"] or "Unknown"
            course_index.setdefault(key, {"code": key, "label": item["name"], "applications": 0, "registrations": 0})["registrations"] = int(item["registrations"])
        course_comparison = sorted(course_index.values(), key=lambda x: (-x["applications"], -x["registrations"], x["code"]))

        app_months = _breakdown(db, f"""
            SELECT COALESCE(to_char(a.created_at,'YYYY-MM'),'Not dated') AS label, COUNT(*) AS value
              FROM public.applications a{app_where}
             GROUP BY 1 ORDER BY 1
        """, params)
        reg_months = _breakdown(db, f"""
            SELECT COALESCE(to_char(r.created_at,'YYYY-MM'),'Not dated') AS label, COUNT(*) AS value
              FROM public.registrations r{reg_where}
             GROUP BY 1 ORDER BY 1
        """, params)
        trend = {}
        for row in app_months:
            trend.setdefault(row["label"], {"label": row["label"], "applications": 0, "registrations": 0})["applications"] = row["value"]
        for row in reg_months:
            trend.setdefault(row["label"], {"label": row["label"], "applications": 0, "registrations": 0})["registrations"] = row["value"]
        monthly_trend = [trend[k] for k in sorted(trend)]

        # Cycle comparison does not conflate application and registration counts.
        cycle_counts = {}
        for row in _rows(db, """
            SELECT COALESCE(NULLIF(trim(application_cycle),''),'Unassigned') AS label,
                   COUNT(*) AS applications FROM public.applications
             GROUP BY 1 ORDER BY 1
        """):
            cycle_counts[row["label"]] = {"label": row["label"], "applications": int(row["applications"]), "registrations": 0}
        for row in _rows(db, """
            SELECT COALESCE(NULLIF(trim(cycle),''),'Unassigned') AS label,
                   COUNT(*) AS registrations FROM public.registrations
             GROUP BY 1 ORDER BY 1
        """):
            cycle_counts.setdefault(row["label"], {"label": row["label"], "applications": 0, "registrations": 0})["registrations"] = int(row["registrations"])
        cycle_comparison = [cycle_counts[k] for k in sorted(cycle_counts)] if not cycle_code else []

        class_status = _breakdown(db, f"""
            SELECT COALESCE(NULLIF(trim(cls.status),''),'Not recorded') AS label,
                   COUNT(*) AS value FROM public.classes cls
            { _scope('cls.cycle_code', cycle_code) }
             GROUP BY 1 ORDER BY value DESC, label
        """, params)
        workplace_status = _breakdown(db, f"""
            SELECT COALESCE(NULLIF(trim(w.status),''),'Not recorded') AS label, COUNT(*) AS value
              FROM public.workplace_placements w JOIN public.registrations r ON r.id=w.registration_id
             WHERE 1=1{reg_and} GROUP BY 1 ORDER BY value DESC, label
        """, params)
        attendance = _breakdown(db, f"""
            SELECT COALESCE(NULLIF(trim(ar.attendance_status),''),'Not recorded') AS label,
                   COUNT(*) AS value FROM public.attendance_records ar
              JOIN public.registrations r ON r.id=ar.registration_id
             WHERE 1=1{reg_and} GROUP BY 1 ORDER BY value DESC, label
        """, params)
        weekly_attendance = _breakdown(db, f"""
            SELECT COALESCE(NULLIF(trim(ar.attendance_status),''),'Not recorded') AS label,
                   COUNT(*) AS value FROM public.attendance_weekly_capture_records ar
              JOIN public.registrations r ON r.id=ar.registration_id
             WHERE 1=1{reg_and} GROUP BY 1 ORDER BY value DESC, label
        """, params)
        summative_status = _breakdown(db, f"""
            SELECT COALESCE(NULLIF(trim(sa.status),''),'Not recorded') AS label,
                   COUNT(*) AS value FROM public.summative_assessments sa
              JOIN public.registrations r ON r.id=sa.registration_id
             WHERE 1=1{reg_and} GROUP BY 1 ORDER BY value DESC, label
        """, params)
        summative_result = _breakdown(db, f"""
            SELECT COALESCE(NULLIF(trim(sa.result),''),'Not recorded') AS label,
                   COUNT(*) AS value FROM public.summative_assessments sa
              JOIN public.registrations r ON r.id=sa.registration_id
             WHERE 1=1{reg_and} GROUP BY 1 ORDER BY value DESC, label
        """, params)
        fisa_digital_scripts = _breakdown(db, f"""
            SELECT COALESCE(NULLIF(trim(fs.status),''),'Not recorded') AS label, COUNT(*) AS value
              FROM public.gm_fisa_scripts fs JOIN public.gm_fisa_sittings sit ON sit.id=fs.sitting_id
             WHERE 1=1{_and_scope('sit.cycle',cycle_code)}
             GROUP BY 1 ORDER BY value DESC, label
        """, params)
        fisa_published_results = _breakdown(db, f"""
            SELECT COALESCE(NULLIF(trim(fs.rendered_outcome),''),'Not recorded') AS label,
                   COUNT(*) AS value
              FROM public.gm_fisa_scripts fs JOIN public.gm_fisa_sittings sit ON sit.id=fs.sitting_id
             WHERE fs.published_at IS NOT NULL{_and_scope('sit.cycle',cycle_code)}
             GROUP BY 1 ORDER BY value DESC, label
        """, params)
        fisa_sittings = _breakdown(db, f"""
            SELECT COALESCE(NULLIF(trim(fs.status),''),'Not recorded') AS label,COUNT(*) AS value
              FROM public.fisa_sittings fs WHERE 1=1{_and_scope('fs.cycle_code',cycle_code)}
             GROUP BY 1 ORDER BY value DESC, label
        """, params)
        eisa_sittings = _breakdown(db, f"""
            SELECT COALESCE(NULLIF(trim(es.status),''),'Not recorded') AS label,COUNT(*) AS value
              FROM public.eisa_sittings es WHERE 1=1{_and_scope('es.cycle_code',cycle_code)}
             GROUP BY 1 ORDER BY value DESC, label
        """, params)
        support_status = _breakdown(db, f"""
            SELECT COALESCE(NULLIF(trim(st.status),''),'Not recorded') AS label,COUNT(*) AS value
              FROM public.support_tickets st JOIN public.registrations r ON r.id=st.registration_id
             WHERE 1=1{reg_and} GROUP BY 1 ORDER BY value DESC, label
        """, params)
        appeal_status = _breakdown(db, f"""
            SELECT COALESCE(NULLIF(trim(ap.status),''),'Not recorded') AS label,COUNT(*) AS value
              FROM public.assessment_appeals ap JOIN public.registrations r ON r.id=ap.registration_id
             WHERE 1=1{reg_and} GROUP BY 1 ORDER BY value DESC, label
        """, params)

        invoice_status = _rows(db, f"""
            SELECT COALESCE(NULLIF(trim(fi.status),''),'Not recorded') AS label,
                   COUNT(*) AS count, COALESCE(SUM(fi.total_amount),0) AS amount
              FROM public.finance_invoices fi JOIN public.finance_accounts fa ON fa.id=fi.finance_account_id
              JOIN public.registrations r ON r.id=fa.registration_id
             WHERE 1=1{reg_and} GROUP BY 1 ORDER BY count DESC, label
        """, params)
        payment_methods = _rows(db, f"""
            SELECT COALESCE(NULLIF(trim(fp.payment_method),''),'Not recorded') AS label,
                   COUNT(*) AS count, COALESCE(SUM(fp.amount),0) AS amount
              FROM public.finance_payments fp JOIN public.finance_accounts fa ON fa.id=fp.finance_account_id
              JOIN public.registrations r ON r.id=fa.registration_id
             WHERE (fp.is_reversed = false OR fp.is_reversed IS NULL)
               AND lower(coalesce(fp.status,'')) NOT IN ('reversed','failed','cancelled','canceled')
               {reg_and} GROUP BY 1 ORDER BY count DESC, label
        """, params)
        # Do not include invoices cancelled or voided when calculating face value.
        billable_invoices = [dict(row, amount=float(row["amount"])) for row in invoice_status if row["label"].lower() not in ("cancelled","canceled","void","voided")]
        payment_methods = [dict(row, amount=float(row["amount"])) for row in payment_methods]
        invoice_status = [dict(row, amount=float(row["amount"])) for row in invoice_status]

        roles = _rows(db, """
            SELECT COALESCE(NULLIF(trim(role_code),''),'Not recorded') AS label,
                   COUNT(*) AS total, COUNT(*) FILTER (WHERE is_active) AS active
              FROM public.staff_accounts GROUP BY 1 ORDER BY label
        """) if not cycle_code else []
        reg_count = _sum(registrations_status)
        app_count = _sum(application_status)
        accepted = sum(x["value"] for x in application_status if x["label"].lower()=="accepted")
        unique_applicants = _count(db, f"""
            SELECT COUNT(DISTINCT a.student_number) FROM public.applications a{app_where}
        """, params)

    sections = [
        {"key":"application_status", "title":"Application decisions", "unit":"Application records", "rows":application_status},
        {"key":"gender", "title":"Applicant gender (as recorded)", "unit":"Application records", "rows":gender},
        {"key":"provinces", "title":"Applicant province codes", "unit":"Application records", "rows":provinces},
        {"key":"applicant_employment", "title":"Applicant employment status", "unit":"Application records", "rows":applicant_employment},
        {"key":"registrations_status", "title":"Registration statuses", "unit":"Registration records", "rows":registrations_status},
        {"key":"class_status", "title":"Class statuses", "unit":"Class records", "rows":class_status},
        {"key":"attendance", "title":"Digital attendance records", "unit":"Captured attendance entries", "rows":attendance},
        {"key":"weekly_attendance", "title":"Weekly register attendance", "unit":"Captured paper-register entries", "rows":weekly_attendance},
        {"key":"summative_status", "title":"Summative assessment workflow", "unit":"Assessment attempts", "rows":summative_status},
        {"key":"summative_result", "title":"Summative recorded results", "unit":"Assessment attempts", "rows":summative_result},
        {"key":"fisa_digital_scripts", "title":"Digital FISA script workflow", "unit":"Script records", "rows":fisa_digital_scripts},
        {"key":"fisa_published_results", "title":"Published digital FISA outcomes", "unit":"Published script outcomes only", "rows":fisa_published_results},
        {"key":"fisa_sittings", "title":"FISA sitting statuses", "unit":"Sittings", "rows":fisa_sittings},
        {"key":"eisa_sittings", "title":"EISA sitting statuses", "unit":"Sittings", "rows":eisa_sittings},
        {"key":"workplace_status", "title":"Workplace placement statuses", "unit":"Placement records", "rows":workplace_status},
        {"key":"appeal_status", "title":"Assessment appeal statuses", "unit":"Appeal records", "rows":appeal_status},
        {"key":"support_status", "title":"Learner support ticket statuses", "unit":"Support tickets", "rows":support_status},
        {"key":"invoice_status", "title":"Finance invoice statuses", "unit":"Invoice records and total value", "rows":invoice_status},
        {"key":"payment_methods", "title":"Unreversed recorded payments by method", "unit":"Payment entries and amounts", "rows":payment_methods},
    ]
    if not cycle_code:
        sections.append({"key":"roles", "title":"Staff accounts by role (institution-wide)", "unit":"Staff accounts", "rows":roles})
        sections.append({"key":"cycle_comparison", "title":"Academic cycle comparison", "unit":"Application and registration records", "rows":cycle_comparison})

    data_notes = [
        "Figures are live database records at the generated timestamp, not audited annual returns.",
        "Applications and registrations are separate events. Acceptance does not imply registration.",
        "Overall totals count records; the same person can appear in more than one cycle or programme.",
        "Application demographics describe applications, not necessarily unique individuals.",
        "Attendance from digital sessions and weekly paper-register capture is reported separately to prevent double-counting.",
        "Summative results include all recorded attempts; digital FISA outcomes are shown separately and only once published.",
        "Finance shows non-cancelled invoice face values and unreversed recorded payments. These are not cashbook or audited outstanding-balance figures.",
        "Missing records are displayed as no captured data, not assumed proof that training or activity did not happen.",
        "This report contains aggregated data only; learner names, national IDs and individual financial accounts are excluded.",
    ]
    if cycle_code and selected_cycle is None:
        data_notes.append("This cycle appears in historic applications/registrations but has no matching cycle setup record.")
    if not _sum(attendance) and not _sum(weekly_attendance):
        data_notes.append("No attendance records were captured for this selected scope at the time of reporting.")
    if not _sum(fisa_published_results):
        data_notes.append("No published digital FISA outcomes were recorded for this scope; do not infer a pass rate.")

    return {
        "scope": {"type":"cycle" if cycle_code else "overall", "cycle_code":cycle_code,
                  "title":f"Academic Cycle {cycle_code}" if cycle_code else "Overall Institution",
                  "generated_at":datetime.now(timezone.utc).isoformat(),
                  "cycle_details": {k:(v.isoformat() if hasattr(v,"isoformat") else v) for k,v in selected_cycle.items()} if selected_cycle else None},
        "cycles":cycles,
        "summary":{
            "applications":app_count, "unique_applicants":unique_applicants,
            "accepted_applications":accepted, "registrations":reg_count,
            "classes":_sum(class_status), "programmes":len(course_comparison),
            "digital_attendance_entries":_sum(attendance),
            "weekly_attendance_entries":_sum(weekly_attendance),
            "summative_attempts":_sum(summative_status),
            "published_fisa_outcomes":_sum(fisa_published_results),
            "billable_invoice_value":_total(billable_invoices),
            "unreversed_payment_value":_total(payment_methods),
            "learner_support_tickets":_sum(support_status),
            "workplace_placements":_sum(workplace_status),
        },
        "charts":{
            "application_status":application_status,"gender":gender,
            "registration_status":registrations_status,"courses":course_comparison,
            "cycles":cycle_comparison,"monthly_trend":monthly_trend,
            "attendance":attendance,"weekly_attendance":weekly_attendance,
            "published_fisa":fisa_published_results,"invoice_status":invoice_status,
            "payment_methods":payment_methods,"staff_roles":roles,
        },
        "sections":sections,"notes":data_notes,
    }
