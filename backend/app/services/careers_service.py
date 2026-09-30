from pathlib import Path
from datetime import date
from uuid import uuid4
import re
from fastapi import UploadFile
from sqlalchemy import text
from app.database import engine
from app.services.email_service import send_email

ALLOWED_EXTENSIONS={'.pdf','.doc','.docx','.jpg','.jpeg','.png'}
MAX_FILE_BYTES=10*1024*1024

def applicant_number(): return f"CAR-{date.today().year}-{uuid4().hex[:8].upper()}"
def application_number(): return f"JOB-{date.today().year}-{uuid4().hex[:10].upper()}"
def _safe(name): return re.sub(r'[^A-Za-z0-9._-]+','_',Path(name or 'document').name)[:180] or 'document'
def _docs(v):
    if not v: return []
    if isinstance(v,list): return [str(x).strip() for x in v if str(x).strip()]
    return []

def list_public_vacancies():
    with engine.connect() as c:
        rows=c.execute(text("""SELECT id,vacancy_code,job_title,department,location,employment_type,positions_available,description,responsibilities,minimum_requirements,preferred_requirements,required_documents,opening_date,closing_date,status,published_at FROM public.career_vacancies WHERE status='Published' AND opening_date<=CURRENT_DATE AND closing_date>=CURRENT_DATE ORDER BY closing_date,job_title""")).mappings().all()
    return [dict(x) for x in rows]

def get_public_vacancy(code):
    with engine.connect() as c:
        r=c.execute(text("""SELECT * FROM public.career_vacancies WHERE vacancy_code=:code AND status='Published' AND opening_date<=CURRENT_DATE AND closing_date>=CURRENT_DATE LIMIT 1"""),{'code':str(code or '').strip().upper()}).mappings().first()
    if not r: raise ValueError('Vacancy is not available for applications.')
    return dict(r)

def create_application_draft(*,applicant_id,vacancy_code,cover_letter=None):
    v=get_public_vacancy(vacancy_code)
    with engine.begin() as c:
        old=c.execute(text("SELECT * FROM public.career_applications WHERE applicant_id=CAST(:a AS uuid) AND vacancy_id=:v LIMIT 1"),{'a':applicant_id,'v':v['id']}).mappings().first()
        if old: return dict(old)
        r=c.execute(text("""INSERT INTO public.career_applications(application_number,applicant_id,vacancy_id,cover_letter,status) VALUES(:n,CAST(:a AS uuid),:v,:cover,'Draft') RETURNING *"""),{'n':application_number(),'a':applicant_id,'v':v['id'],'cover':str(cover_letter or '').strip() or None}).mappings().first()
    return dict(r)

def _owned(c,applicant_id,application_id):
    r=c.execute(text("""SELECT ca.*,cv.vacancy_code,cv.job_title,cv.department,cv.location,cv.employment_type,cv.required_documents,cv.closing_date,cv.status vacancy_status FROM public.career_applications ca JOIN public.career_vacancies cv ON cv.id=ca.vacancy_id WHERE ca.id=CAST(:id AS uuid) AND ca.applicant_id=CAST(:a AS uuid) LIMIT 1"""),{'id':application_id,'a':applicant_id}).mappings().first()
    if not r: raise ValueError('Job application was not found.')
    return dict(r)

def list_my_applications(applicant_id):
    with engine.connect() as c:
        rows=c.execute(text("""SELECT ca.id,ca.application_number,ca.status,ca.submitted_at,ca.status_reason,ca.created_at,ca.updated_at,cv.vacancy_code,cv.job_title,cv.department,cv.location,cv.employment_type,cv.closing_date,(SELECT i.scheduled_at FROM public.career_interviews i WHERE i.application_id=ca.id ORDER BY i.created_at DESC LIMIT 1) interview_date,(SELECT o.status FROM public.career_offers o WHERE o.application_id=ca.id ORDER BY o.created_at DESC LIMIT 1) offer_status FROM public.career_applications ca JOIN public.career_vacancies cv ON cv.id=ca.vacancy_id WHERE ca.applicant_id=CAST(:a AS uuid) ORDER BY ca.created_at DESC"""),{'a':applicant_id}).mappings().all()
    return [dict(x) for x in rows]

def get_my_application(applicant_id,application_id):
    with engine.connect() as c:
        a=_owned(c,applicant_id,application_id)
        d=c.execute(text("SELECT id,document_type,original_filename,mime_type,file_size_bytes,review_status,review_notes,uploaded_at FROM public.career_application_documents WHERE application_id=CAST(:id AS uuid) ORDER BY uploaded_at DESC"),{'id':application_id}).mappings().all()
        i=c.execute(text("SELECT id,scheduled_at,mode,venue,panel,outcome FROM public.career_interviews WHERE application_id=CAST(:id AS uuid) ORDER BY created_at DESC LIMIT 1"),{'id':application_id}).mappings().first()
        o=c.execute(text("SELECT id,start_date,employment_type,offer_summary,status,offered_at,responded_at FROM public.career_offers WHERE application_id=CAST(:id AS uuid) ORDER BY created_at DESC LIMIT 1"),{'id':application_id}).mappings().first()
    return {'application':a,'documents':[dict(x) for x in d],'interview':dict(i) if i else None,'offer':dict(o) if o else None}

async def upload_document(*,applicant_id,application_id,document_type,upload:UploadFile):
    document_type=str(document_type or '').strip()
    if not document_type: raise ValueError('Document type is required.')
    with engine.connect() as c: a=_owned(c,applicant_id,application_id)
    if a['status']!='Draft': raise ValueError('Documents can only be uploaded while the application is in Draft.')
    suffix=Path(upload.filename or '').suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS: raise ValueError('Allowed formats: PDF, DOC, DOCX, JPG, JPEG and PNG.')
    data=await upload.read()
    if not data: raise ValueError('Uploaded document is empty.')
    if len(data)>MAX_FILE_BYTES: raise ValueError('Document exceeds the 10 MB upload limit.')
    folder=Path(__file__).resolve().parents[1]/'uploads'/'careers'/str(applicant_id)/str(application_id); folder.mkdir(parents=True,exist_ok=True)
    stored=uuid4().hex+suffix; target=folder/stored; target.write_bytes(data)
    with engine.begin() as c:
        r=c.execute(text("""INSERT INTO public.career_application_documents(application_id,document_type,original_filename,stored_filename,storage_path,mime_type,file_size_bytes,review_status) VALUES(CAST(:id AS uuid),:t,:orig,:stored,:path,:mime,:size,'Pending') RETURNING id,application_id,document_type,original_filename,mime_type,file_size_bytes,review_status,uploaded_at"""),{'id':application_id,'t':document_type,'orig':_safe(upload.filename),'stored':stored,'path':str(target),'mime':upload.content_type,'size':len(data)}).mappings().first()
    return dict(r)

def owned_document_path(*,applicant_id,application_id,document_id):
    with engine.connect() as c:
        _owned(c,applicant_id,application_id)
        r=c.execute(text("SELECT storage_path,original_filename,mime_type FROM public.career_application_documents WHERE id=CAST(:d AS uuid) AND application_id=CAST(:a AS uuid) LIMIT 1"),{'d':document_id,'a':application_id}).mappings().first()
    if not r: raise ValueError('Application document was not found.')
    p=Path(r['storage_path'])
    if not p.exists(): raise ValueError('Stored application document file was not found.')
    return p,r['original_filename'],r['mime_type']

def submit_application(*,applicant_id,application_id):
    with engine.begin() as c:
        a=_owned(c,applicant_id,application_id)
        if a['status']!='Draft': raise ValueError('Only Draft applications can be submitted.')
        if a['vacancy_status']!='Published' or a['closing_date']<date.today(): raise ValueError('This vacancy is no longer accepting applications.')
        uploaded=set(c.execute(text("SELECT DISTINCT document_type FROM public.career_application_documents WHERE application_id=CAST(:id AS uuid)"),{'id':application_id}).scalars().all())
        missing=[x for x in _docs(a['required_documents']) if x not in uploaded]
        if missing: raise ValueError('Required documents still missing: '+', '.join(missing))
        r=c.execute(text("UPDATE public.career_applications SET status='Received',submitted_at=NOW(),updated_at=NOW() WHERE id=CAST(:id AS uuid) RETURNING *"),{'id':application_id}).mappings().first()
        c.execute(text("INSERT INTO public.career_application_history(application_id,old_status,new_status,note,changed_by_type,changed_by_reference) VALUES(CAST(:id AS uuid),'Draft','Received','Application submitted by applicant.','APPLICANT',:a)"),{'id':application_id,'a':applicant_id})
        person=c.execute(text("SELECT email,first_name,last_name FROM public.career_applicants WHERE id=CAST(:a AS uuid)"),{'a':applicant_id}).mappings().first()
    if person:
        try: send_email(to_email=person['email'],subject='Glen Moniques Careers - Application Received',body=f"Dear {person['first_name']} {person['last_name']},\n\nYour application {r['application_number']} for {a['job_title']} has been received.\n\nKind regards,\nGlen Moniques (Pty) Ltd")
        except Exception as e: print(f'WARNING: Careers acknowledgement email failed: {e}')
    return dict(r)

def withdraw_application(*,applicant_id,application_id):
    with engine.begin() as c:
        a=_owned(c,applicant_id,application_id)
        if a['status'] in {'Rejected','Hired','Withdrawn'}: raise ValueError('This application can no longer be withdrawn.')
        r=c.execute(text("UPDATE public.career_applications SET status='Withdrawn',withdrawn_at=NOW(),updated_at=NOW() WHERE id=CAST(:id AS uuid) RETURNING *"),{'id':application_id}).mappings().first()
        c.execute(text("INSERT INTO public.career_application_history(application_id,old_status,new_status,note,changed_by_type,changed_by_reference) VALUES(CAST(:id AS uuid),:old,'Withdrawn','Application withdrawn by applicant.','APPLICANT',:a)"),{'id':application_id,'old':a['status'],'a':applicant_id})
    return dict(r)
