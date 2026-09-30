REPORT_DEFINITIONS = {
    "learner.enrolment": ("1. Learner Reports", "Enrolment Report", True, None),
    "learner.demographics": ("1. Learner Reports", "Learner Demographics", True, None),
    "learner.status": ("1. Learner Reports", "Learner Status", True, None),
    "learner.withdrawal": ("1. Learner Reports", "Learner Withdrawal Report", True, None),

    "attendance.daily": ("2. Attendance", "Daily Attendance", True, None),
    "attendance.weekly": ("2. Attendance", "Weekly Attendance", True, None),
    "attendance.module": ("2. Attendance", "Module Attendance", True, None),
    "attendance.exceptions": ("2. Attendance", "Attendance Exceptions", True, None),

    "curriculum.km_delivery": ("3. Curriculum Implementation", "KM Delivery", True, None),
    "curriculum.pm_delivery": ("3. Curriculum Implementation", "PM Delivery", True, None),
    "curriculum.wm_delivery": ("3. Curriculum Implementation", "WM Delivery", True, None),
    "curriculum.progress": ("3. Curriculum Implementation", "Curriculum Progress", True, None),

    "assessment.schedule": ("4. Assessment", "Assessment Schedule", True, None),
    "assessment.results": ("4. Assessment", "Assessment Results", True, None),
    "assessment.assessor": ("4. Assessment", "Assessor Report", True, None),
    "assessment.moderation": ("4. Assessment", "Moderation Report", True, None),
    "assessment.nyc": ("4. Assessment", "NYC Report", True, None),
    "assessment.reassessment": ("4. Assessment", "Reassessment Report", True, None),
    "assessment.appeals_register": (
        "4. Assessment",
        "Appeals Register",
        True,
        None,
    ),

    "work_experience.placement": (
        "5. Work Experience",
        "Placement Report",
        True,
        None,
    ),
    "work_experience.workplace_attendance": (
        "5. Work Experience",
        "Workplace Attendance",
        True,
        None,
    ),
    "work_experience.weekly_submissions": (
        "5. Work Experience",
        "Weekly Submissions",
        True,
        None,
    ),
    "work_experience.supervisor_reports": (
        "5. Work Experience",
        "Supervisor Reports",
        True,
        None,
    ),
    "work_experience.wm_completion": (
        "5. Work Experience",
        "WM Completion",
        True,
        None,
    ),

    "eisa.readiness": ("6. EISA", "EISA Readiness", True, None),
    "eisa.registration": ("6. EISA", "EISA Registration", True, None),
    "eisa.sitting_orders": (
        "6. EISA",
        "Sitting Orders",
        True,
        None,
    ),
    "eisa.results": ("6. EISA", "EISA Results", True, None),
    "eisa.certification_tracking": (
        "6. EISA",
        "Certification Tracking",
        True,
        None,
    ),

    "skills_programme.enrolment": ("7. Skills Programme", "Enrolment", True, None),
    "skills_programme.implementation": ("7. Skills Programme", "Implementation", True, None),
    "skills_programme.fisa": ("7. Skills Programme", "FISA", True, None),
    "skills_programme.results": ("7. Skills Programme", "Results", True, None),
    "skills_programme.completion": ("7. Skills Programme", "Completion", True, None),

    "quality.internal_qa": ("8. Quality Assurance", "Internal QA Report", True, None),
    "quality.compliance_checklist": ("8. Quality Assurance", "Compliance Checklist", True, None),
    "quality.findings_register": ("8. Quality Assurance", "Findings Register", True, None),
    "quality.corrective_action_register": (
        "8. Quality Assurance",
        "Corrective Action Register",
        True,
        None,
    ),
    "quality.closeout": ("8. Quality Assurance", "QA Close-out Report", True, None),

    "management.cohort_performance": ("9. Management", "Cohort Performance", True, None),
    "management.completion_statistics": ("9. Management", "Completion Statistics", True, None),
    "management.assessment_statistics": ("9. Management", "Assessment Statistics", True, None),
    "management.attendance_statistics": ("9. Management", "Attendance Statistics", True, None),
    "management.programme_closeout": ("9. Management", "Programme Close-out Report", True, None),
}


DESCRIPTIONS = {
    "learner.enrolment": "Learner registrations, programmes, cycles and class placement.",
    "learner.demographics": "Demographic profile of registered learners.",
    "learner.status": "Current learner registration and application status.",
    "learner.withdrawal": "Withdrawn, cancelled and archived learner records.",
    "attendance.daily": "Attendance captured per timetable session and learner.",
    "attendance.weekly": "Weekly register capture records.",
    "attendance.module": "Attendance totals and rates by learner and module.",
    "attendance.exceptions": "Absence, late arrival and returned attendance records.",
    "curriculum.km_delivery": "Knowledge Module implementation evidence.",
    "curriculum.pm_delivery": "Practical Module implementation evidence.",
    "curriculum.wm_delivery": "Work Experience Module implementation evidence.",
    "curriculum.progress": "Programme and module completion progress.",
    "assessment.schedule": "Scheduled FISA sittings and assessment activity.",
    "assessment.results": "Module and summative assessment outcomes.",
    "assessment.assessor": "Assessment workload and workflow status by Assessor.",
    "assessment.moderation": "Moderation workflow and returned assessment records.",
    "assessment.nyc": "Not Yet Competent assessment outcomes.",
    "assessment.reassessment": "Second and subsequent assessment attempts.",
    "assessment.appeals_register": "Assessment appeals register.",
    "work_experience.placement": "Learner workplace placement records.",
    "work_experience.workplace_attendance": "Attendance at approved workplace placements.",
    "work_experience.weekly_submissions": "Weekly learner workplace evidence submissions.",
    "work_experience.supervisor_reports": "Workplace supervisor reports and sign-offs.",
    "work_experience.wm_completion": "Work Experience Module completion status.",
    "eisa.readiness": "Learner readiness and eligibility for EISA.",
    "eisa.registration": "Eligible learners and EISA assessment records.",
    "eisa.sitting_orders": "EISA venue and seating allocations.",
    "eisa.results": "Recorded EISA assessment outcomes.",
    "eisa.certification_tracking": "SoR, completion and certification-related status.",
    "skills_programme.enrolment": "Skills Programme learner enrolments.",
    "skills_programme.implementation": "Skills Programme timetable and module implementation.",
    "skills_programme.fisa": "FISA sittings and candidate status.",
    "skills_programme.results": "Skills Programme FISA results.",
    "skills_programme.completion": "Skills Programme completion status.",
    "quality.internal_qa": "System QA workflow signals from assessment and attendance.",
    "quality.compliance_checklist": "Automated academic implementation compliance checks.",
    "quality.findings_register": "System-generated open compliance and workflow findings.",
    "quality.corrective_action_register": "Corrective actions, owners, due dates and closure evidence.",
    "quality.closeout": "Cycle-level close-out readiness and outstanding issues.",
    "management.cohort_performance": "Cohort-level assessment and completion performance.",
    "management.completion_statistics": "Completion rates by cycle and programme.",
    "management.assessment_statistics": "Assessment outcome statistics.",
    "management.attendance_statistics": "Attendance performance by class and programme.",
    "management.programme_closeout": "Programme-level close-out status and key indicators.",
}


def get_catalog() -> list[dict]:
    result = []
    for code, (category, title, available, reason) in REPORT_DEFINITIONS.items():
        result.append(
            {
                "code": code,
                "category": category,
                "title": title,
                "description": DESCRIPTIONS.get(code, ""),
                "available": available,
                "reason": reason,
            }
        )
    return result


def get_definition(code: str) -> dict | None:
    item = REPORT_DEFINITIONS.get(code)
    if not item:
        return None
    category, title, available, reason = item
    return {
        "code": code,
        "category": category,
        "title": title,
        "description": DESCRIPTIONS.get(code, ""),
        "available": available,
        "reason": reason,
    }
