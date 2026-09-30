from __future__ import annotations

from datetime import date

from app.pdfs.reports.qa_compliance_report_pdf import (
    generate_qa_compliance_report_pdf,
)
from app.services.staff_audit_service import (
    create_staff_audit_log,
)
from app.services.staff_report_academic import (
    assessment_report,
    curriculum_report,
)
from app.services.staff_report_catalog import (
    get_catalog,
    get_definition,
)
from app.services.staff_report_common import (
    clean_filters,
)
from app.services.staff_report_compliance import (
    eisa_report,
    management_report,
    quality_report,
    skills_report,
    wm_completion_report,
)
from app.services.staff_report_learner_attendance import (
    attendance_report,
    learner_report,
)
from app.services.staff_report_new_sources import (
    NEW_SOURCE_REPORT_CODES,
    new_source_report,
)


def get_report_catalog() -> list[dict]:
    return get_catalog()


def build_report(
    report_code: str,
    *,
    cycle_code: str | None = None,
    course_code: str | None = None,
    class_code: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict:
    report_code = str(report_code or "").strip()
    definition = get_definition(report_code)

    if not definition:
        raise ValueError("Unknown report code.")

    if not definition["available"]:
        raise NotImplementedError(
            definition.get("reason")
            or "This report is not yet available."
        )

    filters = clean_filters(
        cycle_code=cycle_code,
        course_code=course_code,
        class_code=class_code,
        date_from=date_from,
        date_to=date_to,
    )

    if report_code in NEW_SOURCE_REPORT_CODES:
        return new_source_report(
            report_code,
            filters,
        )

    if report_code.startswith("learner."):
        return learner_report(report_code, filters)

    if report_code.startswith("attendance."):
        return attendance_report(report_code, filters)

    if report_code.startswith("curriculum."):
        return curriculum_report(report_code, filters)

    if report_code.startswith("assessment."):
        return assessment_report(report_code, filters)

    if report_code == "work_experience.wm_completion":
        return wm_completion_report(report_code, filters)

    if report_code.startswith("eisa."):
        return eisa_report(report_code, filters)

    if report_code.startswith("skills_programme."):
        return skills_report(report_code, filters)

    if report_code.startswith("quality."):
        return quality_report(report_code, filters)

    if report_code.startswith("management."):
        return management_report(report_code, filters)

    raise ValueError("Report handler is not configured.")


def generate_report_pdf(
    report_code: str,
    *,
    generated_by: str,
    cycle_code: str | None = None,
    course_code: str | None = None,
    class_code: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[str, dict]:
    report = build_report(
        report_code,
        cycle_code=cycle_code,
        course_code=course_code,
        class_code=class_code,
        date_from=date_from,
        date_to=date_to,
    )

    pdf_path = generate_qa_compliance_report_pdf(
        report,
        generated_by=generated_by,
    )

    try:
        create_staff_audit_log(
            actor_staff_code=generated_by,
            action_code="REPORT_PDF_GENERATED",
            module_code="REPORTS",
            entity_type="REPORT",
            entity_id=report_code,
            description="QA & Compliance report PDF generated.",
            before_data=None,
            after_data=None,
            metadata={
                "report_code": report_code,
                "filters": {
                    key: str(value) if value is not None else None
                    for key, value in report.get("filters", {}).items()
                },
                "row_count": len(report.get("rows", [])),
            },
        )
    except Exception as error:
        print(
            "WARNING: Report generated but audit logging failed: "
            f"{error}"
        )

    return pdf_path, report
