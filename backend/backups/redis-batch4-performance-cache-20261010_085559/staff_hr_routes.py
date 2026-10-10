from fastapi import APIRouter,Depends,HTTPException
from fastapi.responses import FileResponse
from app.models.careers_hr import HRApplicationStatusUpdate,HRDocumentReview,HRHireRequest,HRInterviewCreate,HRInterviewUpdate,HROfferCreate,HROfferUpdate,HRVacancyCreate,HRVacancyUpdate
from app.services.staff_hr_service import application,applications,create_interview,create_offer,create_vacancy,dashboard,document_path,employees,hire,review_document,set_application_status,set_vacancy,update_interview,update_offer,update_vacancy,vacancies,vacancy
from app.services.staff_permission_service import require_permission
router=APIRouter(prefix='/api/staff/hr',tags=['HR Recruitment & Employment'])
view=require_permission('VIEW_RECRUITMENT');manage_v=require_permission('MANAGE_VACANCIES');review=require_permission('REVIEW_JOB_APPLICATIONS');interviews=require_permission('MANAGE_INTERVIEWS');offers=require_permission('MANAGE_JOB_OFFERS');view_emp=require_permission('VIEW_EMPLOYEES');manage_emp=require_permission('MANAGE_EMPLOYMENT')
def bad(e,code=400):raise HTTPException(code,str(e)) from e
@router.get('/dashboard')
def dash(s:dict=Depends(view)):return {'success':True,'data':dashboard()}
@router.get('/vacancies')
def vs(status:str|None=None,s:dict=Depends(view)):
    x=vacancies(status);return {'success':True,'count':len(x),'vacancies':x}
@router.post('/vacancies')
def vc(p:HRVacancyCreate,s:dict=Depends(manage_v)):
    try:return {'success':True,'vacancy':create_vacancy(s['staff_code'],p.model_dump())}
    except ValueError as e:bad(e)
@router.get('/vacancies/{vacancy_id}')
def vd(vacancy_id:str,s:dict=Depends(view)):
    try:return {'success':True,'vacancy':vacancy(vacancy_id)}
    except ValueError as e:bad(e,404)
@router.patch('/vacancies/{vacancy_id}')
def vu(vacancy_id:str,p:HRVacancyUpdate,s:dict=Depends(manage_v)):
    try:return {'success':True,'vacancy':update_vacancy(s['staff_code'],vacancy_id,p.model_dump(exclude_unset=True))}
    except ValueError as e:bad(e)
@router.post('/vacancies/{vacancy_id}/publish')
def vp(vacancy_id:str,s:dict=Depends(manage_v)):
    try:return {'success':True,'vacancy':set_vacancy(s['staff_code'],vacancy_id,'Published')}
    except ValueError as e:bad(e)
@router.post('/vacancies/{vacancy_id}/close')
def vx(vacancy_id:str,s:dict=Depends(manage_v)):
    try:return {'success':True,'vacancy':set_vacancy(s['staff_code'],vacancy_id,'Closed')}
    except ValueError as e:bad(e)
@router.get('/applications')
def aps(status:str|None=None,vacancy_id:str|None=None,search:str|None=None,s:dict=Depends(view)):
    x=applications(status,vacancy_id,search);return {'success':True,'count':len(x),'applications':x}
@router.get('/applications/{application_id}')
def ap(application_id:str,s:dict=Depends(view)):
    try:return {'success':True,'data':application(application_id)}
    except ValueError as e:bad(e,404)
@router.patch('/applications/{application_id}/status')
def st(application_id:str,p:HRApplicationStatusUpdate,s:dict=Depends(review)):
    try:return {'success':True,'application':set_application_status(s['staff_code'],application_id,p.status,p.reason)}
    except ValueError as e:bad(e)
@router.patch('/documents/{document_id}/review')
def dr(document_id:str,p:HRDocumentReview,s:dict=Depends(review)):
    try:return {'success':True,'document':review_document(s['staff_code'],document_id,p.review_status,p.review_notes)}
    except ValueError as e:bad(e)
@router.get('/documents/{document_id}/download')
def dd(document_id:str,s:dict=Depends(view)):
    try:
        p,n,m=document_path(document_id);return FileResponse(str(p),filename=n,media_type=m or 'application/octet-stream')
    except ValueError as e:bad(e,404)
@router.post('/applications/{application_id}/interviews')
def ic(application_id:str,p:HRInterviewCreate,s:dict=Depends(interviews)):
    try:return {'success':True,'interview':create_interview(s['staff_code'],application_id,p.model_dump())}
    except ValueError as e:bad(e)
@router.patch('/interviews/{interview_id}')
def iu(interview_id:str,p:HRInterviewUpdate,s:dict=Depends(interviews)):
    try:return {'success':True,'interview':update_interview(s['staff_code'],interview_id,p.model_dump(exclude_unset=True))}
    except ValueError as e:bad(e)
@router.post('/applications/{application_id}/offers')
def oc(application_id:str,p:HROfferCreate,s:dict=Depends(offers)):
    try:return {'success':True,'offer':create_offer(s['staff_code'],application_id,p.start_date,p.employment_type,p.offer_summary)}
    except ValueError as e:bad(e)
@router.patch('/offers/{offer_id}')
def ou(offer_id:str,p:HROfferUpdate,s:dict=Depends(offers)):
    try:return {'success':True,'offer':update_offer(s['staff_code'],offer_id,p.status,p.response_notes)}
    except ValueError as e:bad(e)
@router.post('/applications/{application_id}/hire')
def hi(application_id:str,p:HRHireRequest,s:dict=Depends(manage_emp)):
    try:return {'success':True,'message':'Applicant converted to employee. Staff login remains a separate Admin/Principal step.','employee':hire(s['staff_code'],application_id,p.start_date,p.employment_type)}
    except ValueError as e:bad(e)
@router.get('/employees')
def es(s:dict=Depends(view_emp)):
    x=employees();return {'success':True,'count':len(x),'employees':x}
