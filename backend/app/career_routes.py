from fastapi import APIRouter,Depends,File,Form,HTTPException,UploadFile
from fastapi.responses import FileResponse
from app.career_auth_dependency import get_current_career_applicant
from app.models.careers_hr import CareerApplicantLogin,CareerApplicantRegister,CareerApplicationDraftCreate,CareerPasswordChange
from app.services.career_auth_service import authenticate_applicant,change_applicant_password,create_applicant_account
from app.services.careers_service import applicant_number,create_application_draft,get_my_application,get_public_vacancy,list_my_applications,list_public_vacancies,owned_document_path,submit_application,upload_document,withdraw_application

router=APIRouter(prefix='/api/careers',tags=['Public Careers'])

def bad(e,code=400): raise HTTPException(code,str(e)) from e
@router.post('/auth/register')
def register(p:CareerApplicantRegister):
    try:return {'success':True,'account':create_applicant_account(applicant_number=applicant_number(),**p.model_dump())}
    except ValueError as e:bad(e)
@router.post('/auth/login')
def login(p:CareerApplicantLogin):
    try:return {'success':True,**authenticate_applicant(**p.model_dump())}
    except ValueError as e:bad(e,401)
@router.get('/auth/me')
def me(a:dict=Depends(get_current_career_applicant)):return {'success':True,'account':a}
@router.post('/auth/change-password')
def change(p:CareerPasswordChange,a:dict=Depends(get_current_career_applicant)):
    try:change_applicant_password(applicant_id=str(a['id']),**p.model_dump());return {'success':True,'message':'Password changed successfully.'}
    except ValueError as e:bad(e)
@router.get('/vacancies')
def vacancies():
    x=list_public_vacancies();return {'success':True,'count':len(x),'vacancies':x}
@router.get('/vacancies/{vacancy_code}')
def vacancy(vacancy_code:str):
    try:return {'success':True,'vacancy':get_public_vacancy(vacancy_code)}
    except ValueError as e:bad(e,404)
@router.post('/vacancies/{vacancy_code}/applications')
def draft(vacancy_code:str,p:CareerApplicationDraftCreate,a:dict=Depends(get_current_career_applicant)):
    try:return {'success':True,'application':create_application_draft(applicant_id=str(a['id']),vacancy_code=vacancy_code,cover_letter=p.cover_letter)}
    except ValueError as e:bad(e)
@router.get('/applications')
def apps(a:dict=Depends(get_current_career_applicant)):
    x=list_my_applications(str(a['id']));return {'success':True,'count':len(x),'applications':x}
@router.get('/applications/{application_id}')
def app(application_id:str,a:dict=Depends(get_current_career_applicant)):
    try:return {'success':True,'data':get_my_application(str(a['id']),application_id)}
    except ValueError as e:bad(e,404)
@router.post('/applications/{application_id}/documents')
async def upload(application_id:str,document_type:str=Form(...),upload:UploadFile=File(...),a:dict=Depends(get_current_career_applicant)):
    try:return {'success':True,'document':await upload_document(applicant_id=str(a['id']),application_id=application_id,document_type=document_type,upload=upload)}
    except ValueError as e:bad(e)
@router.get('/applications/{application_id}/documents/{document_id}/download')
def download(application_id:str,document_id:str,a:dict=Depends(get_current_career_applicant)):
    try:
        p,n,m=owned_document_path(applicant_id=str(a['id']),application_id=application_id,document_id=document_id);return FileResponse(str(p),filename=n,media_type=m or 'application/octet-stream')
    except ValueError as e:bad(e,404)
@router.post('/applications/{application_id}/submit')
def submit(application_id:str,a:dict=Depends(get_current_career_applicant)):
    try:return {'success':True,'application':submit_application(applicant_id=str(a['id']),application_id=application_id)}
    except ValueError as e:bad(e)
@router.post('/applications/{application_id}/withdraw')
def withdraw(application_id:str,a:dict=Depends(get_current_career_applicant)):
    try:return {'success':True,'application':withdraw_application(applicant_id=str(a['id']),application_id=application_id)}
    except ValueError as e:bad(e)
