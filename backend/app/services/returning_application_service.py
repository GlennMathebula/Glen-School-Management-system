"""Returning applicant request queue, deliberately separate from registration/admission.

No new student numbers, student accounts, registrations, or finance records are made.
Approval/enrolment conversion will require a later, coordinated schema update.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database import engine
from app.services.admin_completion_service import _is_competent


_REGISTRATIONS = text("""
    SELECT r.id AS registration_id, r.course_code, c.course_name,
           c.assessment_type, c.fisa_pass_mark, r.registration_status,
           fisa.mark AS fisa_mark, fisa.result AS fisa_result,
           fisa.status AS fisa_status
    FROM public.registrations r
    JOIN public.courses c ON c.course_code = r.course_code
    LEFT JOIN LATERAL (
        SELECT sa.mark,sa.result,sa.status
        FROM public.summative_assessments sa
        WHERE sa.registration_id = r.id AND sa.assessment_type = 'FISA'
        ORDER BY sa.attempt_number DESC NULLS LAST,
                 sa.updated_at DESC NULLS LAST
        LIMIT 1
    ) fisa ON TRUE
    WHERE r.student_number=:student_number
    ORDER BY r.registration_date DESC, r.created_at DESC, r.id DESC
""")

_OPTIONS = text("""
    SELECT c.course_code,c.course_name,c.nqf_level,c.credits,
           cy.cycle_code,cy.cycle_name,cy.application_end_date
    FROM public.cycles cy
    JOIN public.cycle_courses cc ON cc.cycle_id=cy.id AND cc.is_active=TRUE
    JOIN public.courses c ON c.id=cc.course_id
    WHERE cy.status='Active' AND c.status='Active'
      AND (cy.application_start_date IS NULL OR cy.application_start_date<=CURRENT_DATE)
      AND (cy.application_end_date IS NULL OR cy.application_end_date>=CURRENT_DATE)
    ORDER BY cy.program_start_date,c.course_name
""")


def _eligibility(connection, student_number):
    rows = [dict(r) for r in connection.execute(_REGISTRATIONS, {"student_number": student_number}).mappings()]
    if not rows:
        return False, "No programme registration is recorded for this student.", rows
    # Check EVERY existing registration; an earlier passed FISA cannot unlock
    # applications while a newer/current course is unfinished.
    for item in rows:
        kind = str(item["assessment_type"] or "").upper()
        if kind != "FISA_ONLY":
            return False, ("Your programme requires a final completion verification which "
                           "is not yet supported by returning applications. Contact Academic Administration."), rows
        if not _is_competent(item['fisa_result'],item['fisa_mark'],
                             item['fisa_pass_mark'],item['fisa_status']):
            return False, "Your current programme has not yet been confirmed completed with a published competent final result.", rows
    return True, "Your recorded programme(s) have completed final results.", rows


def get_student_returning(student_number):
    with engine.connect() as con:
        eligible, reason, regs = _eligibility(con,student_number)
        open_requests = [dict(x) for x in con.execute(text("""
            SELECT ra.id,ra.target_course_code,c.course_name,ra.target_cycle_code,
                   ra.status,ra.submitted_at,ra.review_note
            FROM public.returning_applications ra
            JOIN public.courses c ON c.course_code=ra.target_course_code
            WHERE ra.student_number=:student_number ORDER BY ra.submitted_at DESC
            LIMIT 30
        """),{"student_number":student_number}).mappings()]
        options = [dict(x) for x in con.execute(_OPTIONS).mappings()] if eligible else []
        previous = {r['course_code'] for r in regs}
        options = [o for o in options if o['course_code'] not in previous]
        pending = any(r['status'] in ('Pending','UnderReview') for r in open_requests)
        return {"eligible":eligible and not pending,
                "completion_verified":eligible,
                "reason": "You already have an application under review." if pending else reason,
                "student_number":student_number,
                "previous_courses":[{"course_code":r['course_code'],"course_name":r['course_name']} for r in regs],
                "options":options,
                "applications":open_requests}


def submit_student_returning(student_number, course_code, cycle_code):
    course_code = (course_code or '').strip()
    cycle_code = (cycle_code or '').strip()
    if not course_code or not cycle_code:
        raise ValueError('Choose a programme and intake cycle.')
    try:
        with engine.begin() as con:
            # Serialize concurrent submissions for the same account.
            con.execute(text('SELECT pg_advisory_xact_lock(hashtext(:student_number))'),
                        {'student_number':student_number})
            eligible,reason,regs = _eligibility(con,student_number)
            if not eligible:
                raise ValueError(reason)
            open_row=con.execute(text("""
                SELECT 1 FROM public.returning_applications
                WHERE student_number=:sn AND status IN ('Pending','UnderReview') LIMIT 1
            """),{'sn':student_number}).first()
            if open_row:
                raise ValueError('A returning application is already under review.')
            if course_code in {r['course_code'] for r in regs}:
                raise ValueError('Choose a different programme from your previous registration.')
            available = con.execute(_OPTIONS).mappings().all()
            if not any(o['course_code']==course_code and o['cycle_code']==cycle_code for o in available):
                raise ValueError('This programme is not currently accepting applications in the selected cycle.')
            result=con.execute(text("""
                INSERT INTO public.returning_applications
                (student_number,previous_registration_id,target_course_code,target_cycle_code)
                VALUES (:sn,:rid,:course,:cycle)
                RETURNING id,status,submitted_at
            """),{'sn':student_number,'rid':regs[0]['registration_id'],
                  'course':course_code,'cycle':cycle_code}).mappings().one()
            return dict(result)
    except IntegrityError as err:
        raise ValueError('A request already exists or the selected programme is unavailable.') from err


def staff_list_returning(status,limit):
    limit=max(1,min(int(limit),200))
    with engine.connect() as con:
        rows=con.execute(text("""
            SELECT ra.id,ra.student_number,ra.target_course_code,c.course_name,
                   ra.target_cycle_code,ra.status,ra.submitted_at,ra.reviewed_at,
                   ra.reviewed_by,ra.review_note, a.first_name,a.last_name,a.email
            FROM public.returning_applications ra
            JOIN public.applications a ON a.student_number=ra.student_number
            JOIN public.courses c ON c.course_code=ra.target_course_code
            WHERE (CAST(:status AS varchar) IS NULL OR ra.status=CAST(:status AS varchar))
            ORDER BY ra.submitted_at DESC LIMIT :limit
        """),{'status':status,'limit':limit}).mappings().all()
    return [dict(x) for x in rows]


def staff_review_returning(request_id,status,note,actor):
    if status not in ('UnderReview','Rejected'):
        raise ValueError('Allowed review statuses: UnderReview or Rejected. Admission approval is not yet implemented.')
    if status=='Rejected' and not (note or '').strip():
        raise ValueError('A reason is required when rejecting an application.')
    with engine.begin() as con:
        row=con.execute(text("""
            UPDATE public.returning_applications SET status=:status,review_note=:note,
                reviewed_by=:actor,reviewed_at=now(),updated_at=now()
            WHERE id=:id AND status IN ('Pending','UnderReview')
            RETURNING id,student_number,status,reviewed_at
        """),{'id':str(request_id),'status':status,'note':(note or '').strip() or None,
              'actor':actor}).mappings().first()
        if not row:
            raise ValueError('The request is not available for this review change.')
        return dict(row)
