"""Glen Moniques FISA Digital Workflow, intentionally separate from EISA.

Deployment prerequisite: sql/001_fisa_digital.sql must be reviewed and applied.
Uploaded QA report unlocks eligible results *without* authenticity checks (requested policy).
"""
from __future__ import annotations

import hashlib
from datetime import date
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text

from app.services.fisa_scoring import (validate_marking, render_result, valid_rendered)
from app.config import settings
from app.database import engine
from app.student_auth_dependency import require_full_student_access
from app.staff_auth_dependency import get_current_staff
from app.services.staff_permission_service import get_staff_roles, get_staff_permissions
from supabase import create_client

router = APIRouter(prefix="/api/fisa-digital", tags=["FISA Digital"])
BUCKET = "student-documents"  # existing private Supabase bucket
MAX_BYTES = 10 * 1024 * 1024
MIME = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png"}


def uid(value):
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError):
        raise HTTPException(400, "Invalid record identifier")


def storage():
    return create_client(settings.supabase_url, settings.supabase_service_role_key).storage.from_(BUCKET)


async def upload(file: UploadFile, prefix: str):
    suffix = MIME.get((file.content_type or "").lower())
    if not suffix:
        raise HTTPException(400, "Upload PDF, JPG or PNG only")
    content = await file.read(MAX_BYTES + 1)
    if not content or len(content) > MAX_BYTES:
        raise HTTPException(400, "File must be 1 byte to 10 MB")
    if (suffix == ".pdf" and not content.startswith(b"%PDF-")) or (suffix == ".png" and not content.startswith(b"\x89PNG\r\n\x1a\n")) or (suffix == ".jpg" and not content.startswith(b"\xff\xd8")):
        raise HTTPException(400, "File contents do not match type")
    path = f"fisa-digital/{prefix}/{uuid4()}{suffix}"
    try:
        storage().upload(path, content, {"content-type": file.content_type, "upsert": "false"})
    except Exception as exc:
        raise HTTPException(502, "Private document storage upload failed") from exc
    return path, hashlib.sha256(content).hexdigest(), file.filename or "answer-script"


def remove(path):
    try:
        storage().remove([path])
    except Exception:
        pass


def read_file(path):
    try:
        return storage().download(path)
    except Exception as exc:
        raise HTTPException(502, "Document unavailable") from exc


def staff_access(actor, required):
    code = actor["staff_code"]
    roles = set(get_staff_roles(staff_code=code))
    perms = set(get_staff_permissions(staff_code=code))
    if required == "review" and not (roles & {"ASSESSOR", "MODERATOR", "ADMIN", "PRINCIPAL"}):
        raise HTTPException(403, "Assessment staff role required")
    if required == "admin" and not (roles & {"ADMIN", "PRINCIPAL"}):
        raise HTTPException(403, "Admin or Principal required")
    if required == "assessor" and "ASSESS_RESULT" not in perms:
        raise HTTPException(403, "Assessor permission required")
    if required == "moderator" and "MODERATE_RESULT" not in perms:
        raise HTTPException(403, "Moderator permission required")
    return code


def log(conn, sid, actor, action, script=None, details=None):
    conn.execute(text("""INSERT INTO public.gm_fisa_events
      (sitting_id,script_id,actor_code,action,details)
      VALUES (CAST(:s AS uuid),CAST(:x AS uuid),:a,:n,CAST(:d AS jsonb))"""),
      {"s": sid,"x": script,"a": actor,"n":action,"d": __import__("json").dumps(details or {})})


def sitting(conn, sid, lock=False):
    row = conn.execute(text("SELECT * FROM public.gm_fisa_sittings WHERE id=CAST(:id AS uuid)" + (" FOR UPDATE" if lock else "")),{"id":uid(sid)}).mappings().first()
    if not row: raise HTTPException(404, "FISA sitting not found")
    return row


def script(conn, script_id, lock=False):
    row = conn.execute(text("SELECT * FROM public.gm_fisa_scripts WHERE id=CAST(:id AS uuid)" + (" FOR UPDATE" if lock else "")),{"id":uid(script_id)}).mappings().first()
    if not row: raise HTTPException(404, "Script not found")
    return row


def check_assigned(s, actor, role):
    if s[f"{role}_code"] != actor:
        raise HTTPException(403, f"Only assigned {role} may perform this action")


class SittingCreate(BaseModel):
    course_code: str = Field(min_length=1, max_length=80)
    cycle: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=3, max_length=250)
    assessment_date: date
    submission_deadline: str | None = None
    assessor_code: str
    moderator_code: str
    criteria: list[str] = Field(min_length=1, max_length=100)
    marking_method: Literal["competency", "percentage"] = "competency"
    criterion_max_marks: list[float] | None = None
    pass_percentage: float | None = None
    @model_validator(mode="after")
    def validate(self):
        if self.assessor_code == self.moderator_code: raise ValueError("Assessor and moderator must differ")
        if any(not c.strip() for c in self.criteria): raise ValueError("Rubric criteria cannot be empty")
        if self.marking_method == "percentage":
            if self.criterion_max_marks is None or len(self.criterion_max_marks) != len(self.criteria):
                raise ValueError("Each percentage criterion requires a maximum mark")
            if any(not 0 < x <= 100000 for x in self.criterion_max_marks):
                raise ValueError("Maximum marks must be positive")
            if self.pass_percentage is None or not 0 <= self.pass_percentage <= 100:
                raise ValueError("A pass percentage between 0 and 100 is required")
        elif self.criterion_max_marks or self.pass_percentage is not None:
            raise ValueError("Maximum marks and pass percentage apply to percentage marking only")
        return self


@router.post("/sittings")
def create_sitting(payload:SittingCreate, actor:dict=Depends(get_current_staff)):
    code=staff_access(actor,"admin")
    with engine.begin() as conn:
        row=conn.execute(text("""INSERT INTO public.gm_fisa_sittings
         (course_code,cycle,title,assessment_date,submission_deadline,assessor_code,moderator_code,criteria,marking_method,criterion_max_marks,pass_percentage,created_by)
         VALUES(:course,:cycle,:title,:day,CAST(:deadline AS timestamptz),:a,:m,CAST(:criteria AS jsonb),:method,CAST(:maxima AS jsonb),:pass,:by)
         RETURNING id"""),{"course":payload.course_code,"cycle":payload.cycle,"title":payload.title,"day":payload.assessment_date,"deadline":payload.submission_deadline,"a":payload.assessor_code,"m":payload.moderator_code,"criteria":__import__("json").dumps(payload.criteria),"method":payload.marking_method,"maxima":__import__("json").dumps(payload.criterion_max_marks or []),"pass":payload.pass_percentage,"by":code}).scalar_one()
        log(conn,str(row),code,"SITTING_CREATED",details={"criteria_count":len(payload.criteria)})
    return {"id":str(row)}


@router.get("/staff/sittings")
def staff_sittings(actor:dict=Depends(get_current_staff)):
    code=staff_access(actor,"review")
    roles=set(get_staff_roles(staff_code=code))
    where="" if roles & {"ADMIN","PRINCIPAL"} else "WHERE s.assessor_code=:code OR s.moderator_code=:code"
    with engine.connect() as conn:
        rows=conn.execute(text(f"""SELECT s.*, (SELECT count(*) FROM public.gm_fisa_scripts x WHERE x.sitting_id=s.id) AS submissions
            FROM public.gm_fisa_sittings s {where} ORDER BY s.assessment_date DESC"""),{"code":code}).mappings().all()
    return {"sittings":[dict(x) for x in rows]}


@router.get("/student/sittings")
def student_sittings(actor:dict=Depends(require_full_student_access)):
    number=actor["student_number"]
    with engine.connect() as conn:
        rows=conn.execute(text("""SELECT s.id,s.title,s.course_code,s.cycle,s.assessment_date,s.submission_deadline,s.marking_method,
          x.id AS script_id,x.status,CASE WHEN x.status='Published' THEN x.rendered_outcome ELSE NULL END AS outcome,
          CASE WHEN x.status='Published' THEN x.rendered_percentage ELSE NULL END AS percentage
          FROM public.gm_fisa_sittings s
          JOIN public.registrations r ON r.course_code=s.course_code AND r.cycle=s.cycle
          LEFT JOIN public.gm_fisa_scripts x ON x.sitting_id=s.id AND x.student_number=r.student_number
          WHERE r.student_number=:n AND (s.status='Open' OR x.id IS NOT NULL) ORDER BY s.assessment_date DESC"""),{"n":number}).mappings().all()
    return {"sittings":[dict(x) for x in rows]}


@router.post("/student/sittings/{sid}/upload")
async def student_submit(sid:str, file:UploadFile=File(...), actor:dict=Depends(require_full_student_access)):
    number=actor["student_number"]
    with engine.connect() as conn:
        s=sitting(conn,sid)
        exists=conn.execute(text("""SELECT 1 FROM public.registrations WHERE student_number=:n AND course_code=:c AND cycle=:cycle LIMIT 1"""),{"n":number,"c":s["course_code"],"cycle":s["cycle"]}).first()
        if not exists: raise HTTPException(403,"Not enrolled in this sitting")
        if s["status"]!="Open": raise HTTPException(409,"Sitting closed")
        if s["submission_deadline"] and __import__("datetime").datetime.now(__import__("datetime").timezone.utc)>s["submission_deadline"]:
            raise HTTPException(409,"Submission deadline has passed")
        if conn.execute(text("SELECT 1 FROM public.gm_fisa_scripts WHERE sitting_id=CAST(:s AS uuid) AND student_number=:n"),{"s":uid(sid),"n":number}).first():
            raise HTTPException(409,"Script already submitted")
    path,sha,name=await upload(file,f"{uid(sid)}/{number}")
    try:
        with engine.begin() as conn:
            s=sitting(conn,sid,True)
            if s["status"]!="Open": raise HTTPException(409,"Sitting closed")
            if s["submission_deadline"] and __import__("datetime").datetime.now(__import__("datetime").timezone.utc)>s["submission_deadline"]:raise HTTPException(409,"Submission deadline passed")
            row=conn.execute(text("""INSERT INTO public.gm_fisa_scripts(sitting_id,student_number,script_path,script_sha256,script_name,mime_type)
              VALUES(CAST(:s AS uuid),:n,:p,:h,:name,:mime) RETURNING id"""),{"s":uid(sid),"n":number,"p":path,"h":sha,"name":name,"mime":file.content_type}).scalar_one()
            log(conn,uid(sid),number,"SCRIPT_SUBMITTED",str(row),{"sha256":sha})
    except Exception:
        remove(path)
        raise
    return {"success":True,"script_id":str(row),"status":"Submitted"}


@router.get("/staff/sittings/{sid}/scripts")
def staff_scripts(sid:str,actor:dict=Depends(get_current_staff)):
    code=staff_access(actor,"review")
    with engine.connect() as conn:
        s=sitting(conn,sid)
        if code not in {s["assessor_code"],s["moderator_code"]}:
            staff_access(actor,"admin")
        rows=conn.execute(text("SELECT * FROM public.gm_fisa_scripts WHERE sitting_id=CAST(:s AS uuid) ORDER BY student_number"),{"s":uid(sid)}).mappings().all()
    return {"sitting":dict(s),"scripts":[dict(x) for x in rows]}


@router.get("/staff/scripts/{script_id}/document")
def staff_script_file(script_id:str,actor:dict=Depends(get_current_staff)):
    code=staff_access(actor,"review")
    with engine.connect() as conn:
        x=script(conn,script_id)
        s=sitting(conn,str(x["sitting_id"]))
        if code not in {s["assessor_code"],s["moderator_code"]}:staff_access(actor,"admin")
    return Response(read_file(x["script_path"]),media_type=x["mime_type"],headers={"Cache-Control":"no-store","Content-Disposition":"inline"})


class Decision(BaseModel):
    criterion:int=Field(ge=0)
    result:Literal["C","NYC"] | None = None
    awarded_marks: float | None = Field(default=None, ge=0)
    comment:str=Field(min_length=1,max_length=2500)
class Marking(BaseModel):
    decisions:list[Decision]=Field(min_length=1,max_length=100)
    annotations:list[dict]=Field(default_factory=list,max_length=500)
    comment:str=Field(min_length=1,max_length=4000)


def validated_decisions(s, decisions):
    return validate_marking(
        s["marking_method"], s["criteria"], s["criterion_max_marks"],
        [d.model_dump() for d in decisions],
    )


@router.post("/staff/scripts/{script_id}/assess")
def assessor_mark(script_id:str,payload:Marking,actor:dict=Depends(get_current_staff)):
    code=staff_access(actor,"assessor")
    with engine.begin() as conn:
        x=script(conn,script_id,True);s=sitting(conn,str(x["sitting_id"]))
        check_assigned(s,code,"assessor")
        if not s["rubric_path"]:raise HTTPException(409,"Approved rubric must be uploaded before marking")
        if x["status"] not in {"Submitted","Returned"}:raise HTTPException(409,"Script not awaiting assessor marking")
        decisions=validated_decisions(s,payload.decisions)
        conn.execute(text("""UPDATE public.gm_fisa_scripts SET assessor_decisions=CAST(:d AS jsonb),assessor_annotations=CAST(:a AS jsonb),
          assessor_comment=:c,assessed_at=now(),moderator_decisions=NULL,moderator_annotations=NULL,moderator_comment=NULL,moderated_at=NULL,
          rendered_outcome=NULL,rendered_percentage=NULL,rendered_total=NULL,rendered_maximum=NULL,rendered_at=NULL,approved_at=NULL,approved_by=NULL,status='Assessed',updated_at=now()
          WHERE id=CAST(:id AS uuid)"""),{"d":__import__("json").dumps(decisions),"a":__import__("json").dumps(payload.annotations),"c":payload.comment,"id":uid(script_id)})
        log(conn,str(x["sitting_id"]),code,"ASSESSED",uid(script_id))
    return {"status":"Assessed"}


class Moderation(BaseModel):
    decision:Literal["Accept","Return"]
    comment:str=Field(min_length=1,max_length=4000)
    decisions:list[Decision]=Field(default_factory=list)
    annotations:list[dict]=Field(default_factory=list,max_length=500)


@router.post("/staff/scripts/{script_id}/moderate")
def moderator_mark(script_id:str,payload:Moderation,actor:dict=Depends(get_current_staff)):
    code=staff_access(actor,"moderator")
    with engine.begin() as conn:
        x=script(conn,script_id,True);s=sitting(conn,str(x["sitting_id"]))
        check_assigned(s,code,"moderator")
        if code==s["assessor_code"]:raise HTTPException(403,"Cannot moderate own assessment")
        if x["status"]!="Assessed":raise HTTPException(409,"Script not assessed")
        decisions=validated_decisions(s,payload.decisions) if payload.decision=="Accept" else []
        new_status="Moderated" if payload.decision=="Accept" else "Returned"
        conn.execute(text("""UPDATE public.gm_fisa_scripts SET moderator_decisions=CAST(:d AS jsonb),moderator_annotations=CAST(:a AS jsonb),
          moderator_comment=:c,moderated_at=now(),status=:status,updated_at=now() WHERE id=CAST(:id AS uuid)"""),
          {"d":__import__("json").dumps(decisions),"a":__import__("json").dumps(payload.annotations),"c":payload.comment,"status":new_status,"id":uid(script_id)})
        log(conn,str(x["sitting_id"]),code,"MODERATED" if new_status=="Moderated" else "RETURNED",uid(script_id))
    return {"status":new_status}


class BatchMarkItem(BaseModel):
    script_id: UUID
    decisions: list[Decision] = Field(default_factory=list, max_length=100)
    annotations: list[dict] = Field(default_factory=list, max_length=500)
    comment: str = Field(min_length=1, max_length=4000)
    decision: Literal["Accept", "Return"] = "Accept"

class BatchMarks(BaseModel):
    entries: list[BatchMarkItem] = Field(min_length=1, max_length=200)
    @model_validator(mode="after")
    def unique(self):
        ids=[x.script_id for x in self.entries]
        if len(ids)!=len(set(ids)): raise ValueError("Duplicate scripts in marking batch")
        return self


def mark_batch(sid, payload, actor, role):
    code=staff_access(actor,role)
    with engine.begin() as conn:
        s=sitting(conn,sid,True)
        check_assigned(s,code,role)
        if role=="assessor" and not s["rubric_path"]:raise HTTPException(409,"Upload approved rubric before marking")
        if role=="moderator" and code==s["assessor_code"]:raise HTTPException(403,"Cannot moderate own marking")
        ids=[str(e.script_id) for e in payload.entries]
        rows=conn.execute(text("SELECT * FROM public.gm_fisa_scripts WHERE sitting_id=CAST(:s AS uuid) AND id=ANY(CAST(:ids AS uuid[])) FOR UPDATE"),{"s":uid(sid),"ids":ids}).mappings().all()
        records={str(x["id"]):x for x in rows}
        if len(records)!=len(ids):raise HTTPException(400,"Script not found in this sitting")
        # Validate EVERY script before ANY database write. Entire batch commits or rolls back.
        prepared=[]
        for item in payload.entries:
            x=records[str(item.script_id)]
            expected={"Submitted","Returned"} if role=="assessor" else {"Assessed"}
            if x["status"] not in expected:raise HTTPException(409,f"Script {item.script_id} not in expected status")
            decisions=validated_decisions(s,item.decisions) if (role=="assessor" or item.decision=="Accept") else []
            prepared.append((item,x,decisions))
        for item,x,decisions in prepared:
            params={"id":str(item.script_id),"d":__import__("json").dumps(decisions),"a":__import__("json").dumps(item.annotations),"c":item.comment}
            if role=="assessor":
                conn.execute(text("""UPDATE public.gm_fisa_scripts SET assessor_decisions=CAST(:d AS jsonb),assessor_annotations=CAST(:a AS jsonb),
                 assessor_comment=:c,assessed_at=now(),moderator_decisions=NULL,moderator_annotations=NULL,moderator_comment=NULL,moderated_at=NULL,
                 rendered_outcome=NULL,rendered_percentage=NULL,rendered_total=NULL,rendered_maximum=NULL,rendered_at=NULL,approved_at=NULL,approved_by=NULL,status='Assessed',updated_at=now()
                 WHERE id=CAST(:id AS uuid)"""),params)
                action="ASSESSED"
            else:
                params["status"]="Moderated" if item.decision=="Accept" else "Returned"
                conn.execute(text("""UPDATE public.gm_fisa_scripts SET moderator_decisions=CAST(:d AS jsonb),moderator_annotations=CAST(:a AS jsonb),
                 moderator_comment=:c,moderated_at=now(),status=:status,updated_at=now() WHERE id=CAST(:id AS uuid)"""),params)
                action="MODERATED" if item.decision=="Accept" else "RETURNED"
            log(conn,uid(sid),code,action,str(item.script_id))
    return {"success":True,"count":len(prepared),"role":role}


@router.post("/staff/sittings/{sid}/assess-batch")
def assess_batch(sid:str,payload:BatchMarks,actor:dict=Depends(get_current_staff)):
    return mark_batch(sid,payload,actor,"assessor")


@router.post("/staff/sittings/{sid}/moderate-batch")
def moderate_batch(sid:str,payload:BatchMarks,actor:dict=Depends(get_current_staff)):
    return mark_batch(sid,payload,actor,"moderator")


class Batch(BaseModel):
    script_ids:list[UUID]=Field(min_length=1,max_length=200)
    @model_validator(mode="after")
    def no_duplicates(self):
        if len(self.script_ids)!=len(set(self.script_ids)):raise ValueError("Duplicate script IDs")
        return self


def transition(sid:str,payload:Batch,actor:dict,step:str):
    code=staff_access(actor,"admin" if step in {"approve","publish"} else "review")
    ids=[str(x) for x in payload.script_ids]
    with engine.begin() as conn:
        s=sitting(conn,sid,True)
        rows=conn.execute(text("SELECT * FROM public.gm_fisa_scripts WHERE sitting_id=CAST(:s AS uuid) AND id=ANY(CAST(:ids AS uuid[])) FOR UPDATE"),{"s":uid(sid),"ids":ids}).mappings().all()
        if len(rows)!=len(ids):raise HTTPException(400,"One or more scripts are not in this sitting")
        if step=="render":
            if code not in {s["assessor_code"],s["moderator_code"]}:
                staff_access(actor,"admin")
            if any(x["status"]!="Moderated" for x in rows):raise HTTPException(409,"Only moderated scripts can be rendered")
            for x in rows:
                outcome, percent, total, maximum = render_result(s, x["moderator_decisions"])
                conn.execute(text("""UPDATE public.gm_fisa_scripts
                  SET rendered_outcome=:outcome, rendered_percentage=:percent,
                      rendered_total=:total, rendered_maximum=:maximum,
                      rendered_at=now(), status='Rendered', updated_at=now()
                  WHERE id=CAST(:id AS uuid)"""),
                  {"outcome":outcome,"percent":percent,"total":total,"maximum":maximum,"id":str(x["id"])})
        elif step=="approve":
            if any(x["status"]!="Rendered" for x in rows):raise HTTPException(409,"Only rendered scripts can be approved")
            for x in rows:
                conn.execute(text("UPDATE public.gm_fisa_scripts SET status='Internally Approved',approved_by=:by,approved_at=now(),updated_at=now() WHERE id=CAST(:id AS uuid)"),{"by":code,"id":str(x["id"])})
        elif step=="publish":
            if not s["qa_report_path"]:raise HTTPException(409,"QA report not uploaded; results locked")
            if any(x["status"]!="Internally Approved" for x in rows):raise HTTPException(409,"Results must be internally approved first")
            if any(not x["approved_at"] or not valid_rendered(s, x) for x in rows):
                raise HTTPException(409, "Publication blocked: internal approval or valid rendered outcome missing")
            for x in rows:
                conn.execute(text("UPDATE public.gm_fisa_scripts SET status='Published',published_by=:by,published_at=now(),updated_at=now() WHERE id=CAST(:id AS uuid)"),{"by":code,"id":str(x["id"])})
        else:raise HTTPException(400,"Invalid stage")
        for x in rows:log(conn,uid(sid),code,step.upper(),str(x["id"]))
    return {"success":True,"count":len(rows),"stage":step}


@router.post("/staff/sittings/{sid}/render")
def render(sid:str,payload:Batch,actor:dict=Depends(get_current_staff)):
    return transition(sid,payload,actor,"render")
@router.post("/staff/sittings/{sid}/approve")
def approve(sid:str,payload:Batch,actor:dict=Depends(get_current_staff)):
    return transition(sid,payload,actor,"approve")

@router.get("/staff/sittings/{sid}/publication-check")
def publication_check(sid: str, actor: dict = Depends(get_current_staff)):
    """Read-only preview of publishable results and blocking reasons."""
    code = staff_access(actor, "admin")
    with engine.connect() as conn:
        s = sitting(conn, sid)
        records = conn.execute(text("""
            SELECT id, student_number, status, rendered_outcome, rendered_percentage,
                   approved_at, published_at
            FROM public.gm_fisa_scripts
            WHERE sitting_id = CAST(:sid AS uuid)
            ORDER BY student_number
        """), {"sid": uid(sid)}).mappings().all()
    has_qa = bool(s["qa_report_path"])
    items = []
    for x in records:
        status = x["status"]
        blockers = []
        if status == "Published":
            state = "Published"
        else:
            if status != "Internally Approved" or not x["approved_at"]:
                blockers.append("Internal approval incomplete")
            if not valid_rendered(s, x):
                blockers.append("Valid rendered outcome missing")
            if not has_qa:
                blockers.append("QA report not uploaded")
            state = "Eligible for publication" if not blockers else "Locked"
        items.append({
            "script_id": str(x["id"]),
            "student_number": x["student_number"],
            "status": status,
            "marking_method": s["marking_method"],
            "rendered_outcome": x["rendered_outcome"] if status == "Published" else None,
            "rendered_percentage": float(x["rendered_percentage"]) if status == "Published" and x["rendered_percentage"] is not None else None,
            "publication_state": state,
            "eligible": state == "Eligible for publication",
            "blockers": blockers,
        })
    return {
        "sitting_id": uid(sid),
        "qa_report_uploaded": has_qa,
        "qa_report_reference": s["qa_report_reference"],
        "total": len(items),
        "eligible": sum(x["eligible"] for x in items),
        "published": sum(x["publication_state"] == "Published" for x in items),
        "locked": sum(x["publication_state"] == "Locked" for x in items),
        "items": items,
    }

@router.post("/staff/sittings/{sid}/publish")
def publish(sid:str,payload:Batch,actor:dict=Depends(get_current_staff)):
    return transition(sid,payload,actor,"publish")


@router.post("/staff/sittings/{sid}/rubric")
async def rubric_upload(sid:str,file:UploadFile=File(...),actor:dict=Depends(get_current_staff)):
    code=staff_access(actor,"admin")
    with engine.connect() as conn:
        s=sitting(conn,sid)
        if s["rubric_path"]:raise HTTPException(409,"Rubric already uploaded; original version is locked")
        if conn.execute(text("SELECT 1 FROM public.gm_fisa_scripts WHERE sitting_id=CAST(:id AS uuid) LIMIT 1"),{"id":uid(sid)}).first():
            raise HTTPException(409,"Rubric cannot be uploaded after learners submit")
    path,sha,_=await upload(file,f"{uid(sid)}/rubric")
    try:
        with engine.begin() as conn:
            s=sitting(conn,sid,True)
            if s["rubric_path"]:raise HTTPException(409,"Rubric already uploaded")
            conn.execute(text("UPDATE public.gm_fisa_sittings SET rubric_path=:path,rubric_sha256=:sha,updated_at=now() WHERE id=CAST(:id AS uuid)"),{"path":path,"sha":sha,"id":uid(sid)})
            log(conn,uid(sid),code,"RUBRIC_UPLOADED",details={"sha256":sha})
    except Exception:
        remove(path)
        raise
    return {"success":True,"message":"Rubric uploaded and locked"}


@router.get("/staff/sittings/{sid}/rubric")
def rubric_download(sid:str,actor:dict=Depends(get_current_staff)):
    code=staff_access(actor,"review")
    with engine.connect() as conn:
        s=sitting(conn,sid)
        if code not in {s["assessor_code"],s["moderator_code"]}:staff_access(actor,"admin")
    if not s["rubric_path"]:raise HTTPException(404,"Rubric not uploaded")
    content=read_file(s["rubric_path"])
    return Response(content,media_type="application/pdf" if content.startswith(b"%PDF-") else "application/octet-stream",headers={"Cache-Control":"no-store"})


@router.post("/staff/sittings/{sid}/qa-report")
async def qa_upload(sid:str,file:UploadFile=File(...),reference:str=Form(...),actor:dict=Depends(get_current_staff)):
    code=staff_access(actor,"admin")
    if not reference.strip():raise HTTPException(400,"QA reference required")
    with engine.connect() as conn:
        s=sitting(conn,sid)
        if s["qa_report_path"]:raise HTTPException(409,"QA report already uploaded; contact system administrator for correction procedure")
        if not conn.execute(text("SELECT 1 FROM public.gm_fisa_scripts WHERE sitting_id=CAST(:sid AS uuid) AND status='Internally Approved' LIMIT 1"),{"sid":uid(sid)}).first():
            raise HTTPException(409,"Complete internal approval before uploading QA report")
    path,sha,_=await upload(file,f"{uid(sid)}/qa")
    try:
        with engine.begin() as conn:
            s=sitting(conn,sid,True)
            if s["qa_report_path"]:raise HTTPException(409,"QA report already exists")
            conn.execute(text("""UPDATE public.gm_fisa_sittings SET qa_report_path=:path,qa_report_sha256=:sha,
             qa_report_reference=:ref,qa_uploaded_by=:by,qa_uploaded_at=now(),updated_at=now() WHERE id=CAST(:id AS uuid)"""),
             {"path":path,"sha":sha,"ref":reference.strip(),"by":code,"id":uid(sid)})
            log(conn,uid(sid),code,"QA_REPORT_UPLOADED",details={"sha256":sha,"reference":reference.strip()})
    except Exception:
        remove(path)
        raise
    return {"success":True,"unlocked":True,"message":"QA report stored; internally approved results eligible for publication"}


@router.get("/staff/sittings/{sid}/qa-report")
def qa_download(sid:str,actor:dict=Depends(get_current_staff)):
    code=staff_access(actor,"review")
    with engine.connect() as conn:
        s=sitting(conn,sid)
        if code not in {s["assessor_code"],s["moderator_code"]}:staff_access(actor,"admin")
    if not s["qa_report_path"]:raise HTTPException(404,"No QA report")
    content=read_file(s["qa_report_path"])
    return Response(content,media_type="application/pdf" if content.startswith(b"%PDF-") else "application/octet-stream",headers={"Cache-Control":"no-store"})
