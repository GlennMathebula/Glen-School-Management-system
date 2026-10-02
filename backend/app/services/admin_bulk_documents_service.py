from __future__ import annotations

import csv
import re
import shutil
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy import text

from app.database import engine
from app.pdfs.registration_documents import generate_proof_of_registration
from app.services.admin_enrolment_form_service import generate_admin_enrolment_form
from app.services.registration_service import get_registration
from app.services.statement_of_results_service import generate_student_statement_of_results
from app.services.student_completion_documents_service import (
    generate_student_graduation_letter,
    generate_student_letter_of_completion,
)

DOCUMENT_TYPES = {
    "enrolment_form": {"label": "Enrolment Forms", "filename": "Enrolment_Forms"},
    "proof_of_registration": {"label": "Proof of Registration", "filename": "Proof_of_Registration"},
    "letter_of_completion": {"label": "Letters of Completion", "filename": "Letters_of_Completion"},
    "graduation_letter": {"label": "Graduation Letters", "filename": "Graduation_Letters"},
    "sor_fisa_only": {"label": "SoR - FISA Only", "filename": "SOR_FISA_ONLY"},
    "sor_fisa_plus_eisa": {"label": "SoR - FISA + EISA", "filename": "SOR_FISA_PLUS_EISA"},
}


def _clean(value) -> str:
    return str(value or "").strip()


def _safe_name(value) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", _clean(value))
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "bulk"


def _output_root() -> Path:
    root = Path(__file__).resolve().parents[2] / "generated" / "bulk_documents"
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_bulk_document_scope(*, scope_type: str, scope_value: str) -> list[dict]:
    scope_type = _clean(scope_type).lower()
    scope_value = _clean(scope_value)

    if scope_type not in {"cycle", "class", "student"}:
        raise ValueError("Scope must be Cycle, Class or Student.")
    if not scope_value:
        raise ValueError("Select a cycle, class or student.")

    params = {"scope_value": scope_value}

    if scope_type == "student":
        joins = ""
        where_sql = "r.student_number = :scope_value"
    elif scope_type == "cycle":
        joins = ""
        where_sql = """
            r.cycle = :scope_value
            AND r.registration_status NOT IN ('Cancelled', 'Withdrawn')
        """
    else:
        joins = """
            JOIN public.class_enrolments ce
                ON ce.registration_id = r.id
               AND ce.status = 'Active'
            JOIN public.classes cl
                ON cl.id = ce.class_id
        """
        where_sql = "cl.class_code = :scope_value"

    statement = text(
        f"""
        SELECT DISTINCT
            r.id AS registration_id,
            r.student_number,
            r.course_code,
            r.cycle,
            r.registration_status,
            a.first_name,
            a.middle_name,
            a.last_name,
            a.email,
            c.course_name,
            c.assessment_type
        FROM public.registrations r
        JOIN public.applications a
            ON a.student_number = r.student_number
        JOIN public.courses c
            ON c.course_code = r.course_code
        {joins}
        WHERE {where_sql}
        ORDER BY a.last_name, a.first_name, r.student_number
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(statement, params).mappings().all()

    return [dict(row) for row in rows]


def _require_pdf_path(path_value) -> Path:
    path = Path(str(path_value or "")).resolve()
    if not path.exists() or not path.is_file():
        raise ValueError("Generated PDF could not be located.")
    return path


def _generate_one(*, record: dict, document_type: str) -> Path:
    student_number = record["student_number"]

    if document_type == "enrolment_form":
        result = generate_admin_enrolment_form(student_number)
        return _require_pdf_path(result["pdf_path"])

    if document_type == "proof_of_registration":
        registration = get_registration(student_number)
        if not registration:
            raise ValueError("Registration not found.")
        return _require_pdf_path(generate_proof_of_registration(registration))

    if document_type == "letter_of_completion":
        return _require_pdf_path(generate_student_letter_of_completion(student_number))

    if document_type == "graduation_letter":
        return _require_pdf_path(generate_student_graduation_letter(student_number))

    if document_type == "sor_fisa_only":
        if record.get("assessment_type") != "FISA_ONLY":
            raise ValueError("Learner is not on a FISA-only assessment pathway.")
        result = generate_student_statement_of_results(student_number)
        if result.get("assessment_type") != "FISA_ONLY":
            raise ValueError("Generated SoR pathway did not match FISA Only.")
        return _require_pdf_path(result["pdf_path"])

    if document_type == "sor_fisa_plus_eisa":
        if record.get("assessment_type") != "FISA_PLUS_EISA":
            raise ValueError("Learner is not on a FISA + EISA assessment pathway.")
        result = generate_student_statement_of_results(student_number)
        if result.get("assessment_type") != "FISA_PLUS_EISA":
            raise ValueError("Generated SoR pathway did not match FISA + EISA.")
        return _require_pdf_path(result["pdf_path"])

    raise ValueError("Unsupported bulk document type.")


def generate_bulk_documents_zip(*, document_type: str, scope_type: str, scope_value: str) -> dict:
    document_type = _clean(document_type).lower()
    config = DOCUMENT_TYPES.get(document_type)
    if not config:
        raise ValueError("Unsupported bulk document type.")

    records = resolve_bulk_document_scope(scope_type=scope_type, scope_value=scope_value)
    if not records:
        raise ValueError("No registered learners were found for the selected scope.")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = _output_root()
    work_dir = root / f"work_{stamp}_{_safe_name(scope_type)}_{_safe_name(scope_value)}"
    work_dir.mkdir(parents=True, exist_ok=True)
    archive_path = root / (
        f"{config['filename']}_{_safe_name(scope_type)}_{_safe_name(scope_value)}_{stamp}.zip"
    )

    report_rows = []
    generated_count = 0

    try:
        with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
            for record in records:
                student_number = record["student_number"]
                full_name = " ".join(
                    filter(
                        None,
                        [
                            _clean(record.get("first_name")),
                            _clean(record.get("middle_name")),
                            _clean(record.get("last_name")),
                        ],
                    )
                )
                try:
                    pdf_path = _generate_one(record=record, document_type=document_type)
                    suffix = pdf_path.suffix or ".pdf"
                    arcname = (
                        "documents/"
                        + _safe_name(student_number)
                        + "_"
                        + _safe_name(config["filename"])
                        + suffix
                    )
                    archive.write(pdf_path, arcname=arcname)
                    generated_count += 1
                    report_rows.append(
                        {
                            "student_number": student_number,
                            "name": full_name,
                            "course_code": record.get("course_code") or "",
                            "assessment_type": record.get("assessment_type") or "",
                            "status": "Generated",
                            "file": arcname,
                            "reason": "",
                        }
                    )
                except Exception as error:
                    report_rows.append(
                        {
                            "student_number": student_number,
                            "name": full_name,
                            "course_code": record.get("course_code") or "",
                            "assessment_type": record.get("assessment_type") or "",
                            "status": "Skipped",
                            "file": "",
                            "reason": str(error),
                        }
                    )

            report_path = work_dir / "generation_report.csv"
            with report_path.open("w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "student_number",
                        "name",
                        "course_code",
                        "assessment_type",
                        "status",
                        "file",
                        "reason",
                    ],
                )
                writer.writeheader()
                writer.writerows(report_rows)
            archive.write(report_path, arcname="generation_report.csv")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    return {
        "archive_path": str(archive_path),
        "filename": archive_path.name,
        "learner_count": len(records),
        "generated_count": generated_count,
        "skipped_count": len(report_rows) - generated_count,
    }


def cleanup_bulk_archive(path_value: str) -> None:
    try:
        path = Path(path_value).resolve()
        root = _output_root().resolve()
        if path.parent == root and path.suffix.lower() == ".zip" and path.exists():
            path.unlink()
    except Exception as error:
        print(f"WARNING: Bulk document archive cleanup failed: {error}")
