from pathlib import Path
from datetime import date,datetime
from decimal import Decimal
from uuid import UUID,uuid4
import json
from sqlalchemy import text
from app.database import engine
from app.services.email_service import send_email
from app.services.staff_audit_service import create_staff_audit_log

APP_STATUSES={'Received','Under Review','Shortlisted','Rejected'}
DOC_STATUSES={'Pending','Accepted','Rejected'}
INTERVIEW_OUTCOMES={'Pending','Recommended','Not Recommended','Hold'}
OFFER_STATUSES={'Sent','Accepted','Declined','Withdrawn'}

def safe(v):
    if v is None:return None
    if isinstance(v,dict):return {str(k):safe(x) for k,x in v.items()}
    if isinstance(v,(list,tuple,set)):return [safe(x) for x in v]
    if isinstance(v,(date,datetime,UUID,Decimal)):return str(v)
    return v

def audit(actor,action,etype,eid,desc,before=None,after=None,meta=None):
    try:create_staff_audit_log(actor_staff_code=actor,action_code=action,module_code='HR_RECRUITMENT',entity_type=etype,entity_id=str(eid),description=desc,before_data=safe(before),after_data=safe(after),metadata=safe(meta or {}))
    except Exception as e:print(f'WARNING: HR audit failed: {e}')

def notify(application_id,subject,body):
    try:
        with engine.connect() as c:r=c.execute(text("SELECT a.email FROM public.career_applications x JOIN public.career_applicants a ON a.id=x.applicant_id WHERE x.id=CAST(:id AS uuid)"),{'id':application_id}).mappings().first()
        if r:send_email(recipient_email=r['email'],subject=subject,html_body=body)
    except Exception as e:print(f'WARNING: HR applicant email failed: {e}')

def dashboard():
    with engine.connect() as c:
        v=c.execute(text("SELECT COUNT(*) FILTER(WHERE status='Published' AND closing_date>=CURRENT_DATE) open_vacancies,COUNT(*) FILTER(WHERE status='Draft') draft_vacancies,COUNT(*) FILTER(WHERE status='Closed') closed_vacancies FROM public.career_vacancies")).mappings().first()
        a=c.execute(text("SELECT COUNT(*) FILTER(WHERE status='Received') received,COUNT(*) FILTER(WHERE status='Under Review') under_review,COUNT(*) FILTER(WHERE status='Shortlisted') shortlisted,COUNT(*) FILTER(WHERE status='Interview Scheduled') interviews_scheduled,COUNT(*) FILTER(WHERE status='Offer Made') offers_made,COUNT(*) FILTER(WHERE status='Hired') hired FROM public.career_applications WHERE status<>'Draft'")).mappings().first()
        r=c.execute(text("""SELECT x.id,x.application_number,x.status,x.submitted_at,p.first_name,p.last_name,v.vacancy_code,v.job_title FROM public.career_applications x JOIN public.career_applicants p ON p.id=x.applicant_id JOIN public.career_vacancies v ON v.id=x.vacancy_id WHERE x.status<>'Draft' ORDER BY x.submitted_at DESC NULLS LAST LIMIT 10""")).mappings().all()
    return {'vacancies':dict(v),'applications':dict(a),'recent_applications':[dict(x) for x in r]}

def vacancy_code():return f"VAC-{date.today().year}-{uuid4().hex[:8].upper()}"
def vacancies(status=None):
    q='SELECT v.*,(SELECT COUNT(*) FROM public.career_applications a WHERE a.vacancy_id=v.id AND a.status<>\'Draft\') submitted_applications FROM public.career_vacancies v';p={}
    if status:q+=' WHERE v.status=:s';p['s']=status
    q+=' ORDER BY v.created_at DESC'
    with engine.connect() as c:r=c.execute(text(q),p).mappings().all()
    return [dict(x) for x in r]
def vacancy(vacancy_id):
    with engine.connect() as c:r=c.execute(text("SELECT * FROM public.career_vacancies WHERE id=CAST(:id AS uuid)"),{'id':vacancy_id}).mappings().first()
    if not r:raise ValueError('Vacancy was not found.')
    return dict(r)

def create_vacancy(actor,p):
    op=p.get('opening_date') or date.today();cl=p['closing_date']
    if cl<op:raise ValueError('Closing date cannot be before opening date.')
    docs=list(dict.fromkeys(str(x).strip() for x in p.get('required_documents',[]) if str(x).strip()))
    with engine.begin() as c:r=c.execute(text("""INSERT INTO public.career_vacancies(vacancy_code,job_title,department,location,employment_type,positions_available,description,responsibilities,minimum_requirements,preferred_requirements,required_documents,opening_date,closing_date,status,created_by) VALUES(:code,:job_title,:department,:location,:employment_type,:positions_available,:description,:responsibilities,:minimum_requirements,:preferred_requirements,CAST(:docs AS jsonb),:opening_date,:closing_date,'Draft',:actor) RETURNING *"""),{**p,'code':vacancy_code(),'docs':json.dumps(docs),'opening_date':op,'actor':actor}).mappings().first()
    d=dict(r);audit(actor,'HR_VACANCY_CREATED','CAREER_VACANCY',d['id'],'HR created a job vacancy.',after=d);return d

def update_vacancy(actor,vacancy_id,u):
    b=vacancy(vacancy_id);allowed={'job_title','department','location','employment_type','positions_available','description','responsibilities','minimum_requirements','preferred_requirements','required_documents','opening_date','closing_date'};u={k:v for k,v in u.items() if k in allowed and v is not None}
    if not u:return b
    if 'required_documents' in u:u['required_documents']=json.dumps(list(dict.fromkeys(str(x).strip() for x in u['required_documents'] if str(x).strip())))
    if u.get('closing_date',b['closing_date'])<u.get('opening_date',b['opening_date']):raise ValueError('Closing date cannot be before opening date.')
    sets=[];p={'id':vacancy_id}
    for k,v in u.items():sets.append(('required_documents=CAST(:required_documents AS jsonb)' if k=='required_documents' else f'{k}=:{k}'));p[k]=v
    sets.append('updated_at=NOW()')
    with engine.begin() as c:r=c.execute(text(f"UPDATE public.career_vacancies SET {','.join(sets)} WHERE id=CAST(:id AS uuid) RETURNING *"),p).mappings().first()
    d=dict(r);audit(actor,'HR_VACANCY_UPDATED','CAREER_VACANCY',vacancy_id,'HR updated a job vacancy.',b,d);return d

def set_vacancy(actor,vacancy_id,status):
    if status not in {'Published','Closed'}:raise ValueError('Invalid vacancy status action.')
    b=vacancy(vacancy_id)
    if status=='Published' and b['closing_date']<date.today():raise ValueError('A vacancy with a past closing date cannot be published.')
    extra="published_at=COALESCE(published_at,NOW())," if status=='Published' else 'closed_at=NOW(),'
    with engine.begin() as c:r=c.execute(text(f"UPDATE public.career_vacancies SET status=:s,{extra}updated_at=NOW() WHERE id=CAST(:id AS uuid) RETURNING *"),{'s':status,'id':vacancy_id}).mappings().first()
    d=dict(r);audit(actor,'HR_VACANCY_'+status.upper(),'CAREER_VACANCY',vacancy_id,f'HR changed vacancy status to {status}.',b,d);return d

def applications(status=None,vacancy_id=None,search=None):
    fs=["x.status<>'Draft'"];p={}
    if status:fs.append('x.status=:s');p['s']=status
    if vacancy_id:fs.append('x.vacancy_id=CAST(:v AS uuid)');p['v']=vacancy_id
    if search:fs.append('(x.application_number ILIKE :q OR a.first_name ILIKE :q OR a.last_name ILIKE :q OR a.email ILIKE :q OR j.job_title ILIKE :q OR j.vacancy_code ILIKE :q)');p['q']='%'+search.strip()+'%'
    with engine.connect() as c:r=c.execute(text(f"""SELECT x.id,x.application_number,x.status,x.submitted_at,x.status_reason,a.applicant_number,a.first_name,a.last_name,a.email,a.cell_number,j.id vacancy_id,j.vacancy_code,j.job_title,j.department,j.location,j.employment_type FROM public.career_applications x JOIN public.career_applicants a ON a.id=x.applicant_id JOIN public.career_vacancies j ON j.id=x.vacancy_id WHERE {' AND '.join(fs)} ORDER BY x.submitted_at DESC NULLS LAST"""),p).mappings().all()
    return [dict(x) for x in r]

def application(application_id):
    with engine.connect() as c:
        a=c.execute(text("""SELECT x.*,p.applicant_number,p.first_name,p.last_name,p.email,p.cell_number,p.national_id,v.vacancy_code,v.job_title,v.department,v.location,v.employment_type,v.required_documents FROM public.career_applications x JOIN public.career_applicants p ON p.id=x.applicant_id JOIN public.career_vacancies v ON v.id=x.vacancy_id WHERE x.id=CAST(:id AS uuid) AND x.status<>'Draft'"""),{'id':application_id}).mappings().first()
        if not a:raise ValueError('Submitted job application was not found.')
        d=c.execute(text("SELECT * FROM public.career_application_documents WHERE application_id=CAST(:id AS uuid) ORDER BY uploaded_at DESC"),{'id':application_id}).mappings().all();i=c.execute(text("SELECT * FROM public.career_interviews WHERE application_id=CAST(:id AS uuid) ORDER BY created_at DESC"),{'id':application_id}).mappings().all();o=c.execute(text("SELECT * FROM public.career_offers WHERE application_id=CAST(:id AS uuid) ORDER BY created_at DESC"),{'id':application_id}).mappings().all();h=c.execute(text("SELECT * FROM public.career_application_history WHERE application_id=CAST(:id AS uuid) ORDER BY changed_at DESC"),{'id':application_id}).mappings().all()
    return {'application':dict(a),'documents':[dict(x) for x in d],'interviews':[dict(x) for x in i],'offers':[dict(x) for x in o],'history':[dict(x) for x in h]}

def set_application_status(actor,application_id,status,reason=None):
    if status not in APP_STATUSES:raise ValueError('HR status must be Received, Under Review, Shortlisted or Rejected.')
    b=application(application_id)['application']
    with engine.begin() as c:
        r=c.execute(text("UPDATE public.career_applications SET status=:s,status_reason=:reason,reviewed_by=:actor,reviewed_at=NOW(),updated_at=NOW() WHERE id=CAST(:id AS uuid) RETURNING *"),{'s':status,'reason':str(reason or '').strip() or None,'actor':actor,'id':application_id}).mappings().first();c.execute(text("INSERT INTO public.career_application_history(application_id,old_status,new_status,note,changed_by_type,changed_by_reference) VALUES(CAST(:id AS uuid),:old,:new,:note,'STAFF',:actor)"),{'id':application_id,'old':b['status'],'new':status,'note':reason,'actor':actor})
    d=dict(r);audit(actor,'HR_APPLICATION_STATUS_CHANGED','CAREER_APPLICATION',application_id,f'HR changed job application status to {status}.',b,d);notify(application_id,'Glen Moniques Careers - Application Update',f'Your Glen Moniques job application status is now: {status}.\n\n'+(f'Additional information: {reason}\n\n' if reason else '')+'Please sign in to your Careers account for details.');return d

def review_document(actor,document_id,status,notes=None):
    if status not in DOC_STATUSES:raise ValueError('Document review status must be Pending, Accepted or Rejected.')
    with engine.begin() as c:
        b=c.execute(text("SELECT * FROM public.career_application_documents WHERE id=CAST(:id AS uuid)"),{'id':document_id}).mappings().first()
        if not b:raise ValueError('Application document was not found.')
        r=c.execute(text("UPDATE public.career_application_documents SET review_status=:s,review_notes=:n,reviewed_by=:actor,reviewed_at=NOW() WHERE id=CAST(:id AS uuid) RETURNING *"),{'s':status,'n':str(notes or '').strip() or None,'actor':actor,'id':document_id}).mappings().first()
    d=dict(r);audit(actor,'HR_JOB_DOCUMENT_REVIEWED','CAREER_APPLICATION_DOCUMENT',document_id,f'HR reviewed document as {status}.',dict(b),d);return d

def document_path(document_id):
    with engine.connect() as c:r=c.execute(text("SELECT storage_path,original_filename,mime_type FROM public.career_application_documents WHERE id=CAST(:id AS uuid)"),{'id':document_id}).mappings().first()
    if not r:raise ValueError('Application document was not found.')
    p=Path(r['storage_path']);
    if not p.exists():raise ValueError('Stored application document file was not found.')
    return p,r['original_filename'],r['mime_type']

def create_interview(actor,application_id,p):
    a=application(application_id)['application']
    if a['status'] not in {'Shortlisted','Interview Scheduled'}:raise ValueError('Only shortlisted applications can be scheduled for interview.')
    with engine.begin() as c:
        r=c.execute(text("""INSERT INTO public.career_interviews(application_id,scheduled_at,mode,venue,panel,notes,outcome,created_by) VALUES(CAST(:id AS uuid),:scheduled_at,:mode,:venue,:panel,:notes,'Pending',:actor) RETURNING *"""),{'id':application_id,**p,'actor':actor}).mappings().first();c.execute(text("UPDATE public.career_applications SET status='Interview Scheduled',updated_at=NOW() WHERE id=CAST(:id AS uuid)"),{'id':application_id})
    d=dict(r);audit(actor,'HR_INTERVIEW_SCHEDULED','CAREER_INTERVIEW',d['id'],'HR scheduled a job interview.',after=d);notify(application_id,'Glen Moniques Careers - Interview Scheduled',f"An interview has been scheduled.\n\nDate/Time: {p['scheduled_at']}\nMode: {p['mode']}\nVenue: {p.get('venue') or 'To be confirmed'}");return d

def update_interview(actor,interview_id,u):
    with engine.connect() as c:b=c.execute(text("SELECT * FROM public.career_interviews WHERE id=CAST(:id AS uuid)"),{'id':interview_id}).mappings().first()
    if not b:raise ValueError('Interview was not found.')
    u={k:v for k,v in u.items() if v is not None};
    if u.get('outcome') and u['outcome'] not in INTERVIEW_OUTCOMES:raise ValueError('Invalid interview outcome.')
    if not u:return dict(b)
    sets=[];p={'id':interview_id}
    for k,v in u.items():sets.append(f'{k}=:{k}');p[k]=v
    sets.append('updated_at=NOW()')
    with engine.begin() as c:
        r=c.execute(text(f"UPDATE public.career_interviews SET {','.join(sets)} WHERE id=CAST(:id AS uuid) RETURNING *"),p).mappings().first()
        if u.get('outcome') and u['outcome']!='Pending':c.execute(text("UPDATE public.career_applications SET status='Interviewed',updated_at=NOW() WHERE id=:id"),{'id':r['application_id']})
    d=dict(r);audit(actor,'HR_INTERVIEW_UPDATED','CAREER_INTERVIEW',interview_id,'HR updated a job interview.',dict(b),d);return d

def create_offer(actor,application_id,start_date,employment_type,summary):
    a=application(application_id)['application']
    if a['status'] not in {'Interviewed','Offer Made'}:raise ValueError('An offer can only be created after the interview stage.')
    et=str(employment_type or '').strip() or a['employment_type']
    with engine.begin() as c:
        r=c.execute(text("INSERT INTO public.career_offers(application_id,start_date,employment_type,offer_summary,status,offered_at,created_by) VALUES(CAST(:id AS uuid),:start,:et,:sum,'Sent',NOW(),:actor) RETURNING *"),{'id':application_id,'start':start_date,'et':et,'sum':summary,'actor':actor}).mappings().first();c.execute(text("UPDATE public.career_applications SET status='Offer Made',updated_at=NOW() WHERE id=CAST(:id AS uuid)"),{'id':application_id})
    d=dict(r);audit(actor,'HR_JOB_OFFER_CREATED','CAREER_OFFER',d['id'],'HR created a job offer.',after=d);notify(application_id,'Glen Moniques Careers - Employment Offer',summary);return d

def update_offer(actor,offer_id,status,notes=None):
    if status not in OFFER_STATUSES:raise ValueError('Offer status must be Sent, Accepted, Declined or Withdrawn.')
    with engine.begin() as c:
        b=c.execute(text("SELECT * FROM public.career_offers WHERE id=CAST(:id AS uuid)"),{'id':offer_id}).mappings().first()
        if not b:raise ValueError('Job offer was not found.')
        r=c.execute(text("UPDATE public.career_offers SET status=:s,response_notes=:n,responded_at=CASE WHEN :s IN('Accepted','Declined') THEN NOW() ELSE responded_at END,updated_at=NOW() WHERE id=CAST(:id AS uuid) RETURNING *"),{'s':status,'n':str(notes or '').strip() or None,'id':offer_id}).mappings().first()
    d=dict(r);audit(actor,'HR_JOB_OFFER_UPDATED','CAREER_OFFER',offer_id,f'HR changed job offer status to {status}.',dict(b),d);return d

def employee_columns(c):return {r['column_name']:dict(r) for r in c.execute(text("SELECT column_name,is_nullable,column_default,data_type FROM information_schema.columns WHERE table_schema='public' AND table_name='employees' ORDER BY ordinal_position")).mappings().all()}
def employee_number(c):
    for _ in range(20):
        n=f"GM-EMP-{date.today().year}-{uuid4().hex[:6].upper()}"
        if not c.execute(text("SELECT 1 FROM public.employees WHERE employee_number=:n"),{'n':n}).first():return n
    raise RuntimeError('Could not generate a unique employee number.')

def hire(actor,application_id,start_date,employment_type=None):
    d=application(application_id);a=d['application'];offer=next((o for o in d['offers'] if o['status']=='Accepted'),None)
    if not offer:raise ValueError('The job offer must be marked Accepted before hiring.')
    with engine.begin() as c:
        cols=employee_columns(c);vals={'employee_number':None,'first_name':a['first_name'],'last_name':a['last_name'],'email':a['email'],'cell_number':a['cell_number'],'phone_number':a['cell_number'],'national_id':a['national_id'],'job_title':a['job_title'],'department':a['department'],'employment_type':str(employment_type or '').strip() or offer.get('employment_type') or a['employment_type'],'employment_status':'Active','start_date':start_date,'hire_date':start_date,'date_started':start_date,'recruitment_application_id':application_id}
        if 'employee_number' in cols:vals['employee_number']=employee_number(c)
        vals={k:v for k,v in vals.items() if k in cols and v is not None};missing=[k for k,x in cols.items() if k not in vals and k!='id' and x['is_nullable']=='NO' and x['column_default'] is None]
        if missing:raise ValueError('Employee conversion requires values for existing employee fields that Careers cannot safely infer: '+', '.join(missing))
        ks=list(vals);emp=c.execute(text(f"INSERT INTO public.employees({','.join(chr(34)+k+chr(34) for k in ks)}) VALUES({','.join(':'+k for k in ks)}) RETURNING *"),vals).mappings().first();c.execute(text("UPDATE public.career_applications SET status='Hired',hired_at=NOW(),employee_id=:e,updated_at=NOW() WHERE id=CAST(:id AS uuid)"),{'e':str(emp.get('id')) if emp.get('id') is not None else None,'id':application_id})
    out=dict(emp);audit(actor,'HR_APPLICANT_HIRED','EMPLOYEE',out.get('id') or out.get('employee_number'),'HR converted successful applicant to employee.',after=out,meta={'application_id':application_id});notify(application_id,'Glen Moniques Careers - Hiring Process Completed','Your employment application has been marked Hired. HR will communicate onboarding details separately.');return out

def employees():
    with engine.connect() as c:
        cols=employee_columns(c)
        if not cols:return []
        order='employee_number' if 'employee_number' in cols else next(iter(cols));r=c.execute(text(f'SELECT * FROM public.employees ORDER BY "{order}"')).mappings().all()
    return [dict(x) for x in r]
