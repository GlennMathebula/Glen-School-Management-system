from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from app.student_auth_dependency import require_full_student_access
from app.services.returning_application_service import get_student_returning,submit_student_returning

router=APIRouter(prefix='/api/student/returning-applications',tags=['Returning Student Applications'])

class NewReturningApplication(BaseModel):
    course_code:str=Field(min_length=1,max_length=100)
    cycle_code:str=Field(min_length=1,max_length=100)

@router.get('')
def returning_summary(current_student:dict=Depends(require_full_student_access)):
    return {'success':True,'data':get_student_returning(current_student['student_number'])}

@router.post('',status_code=201)
def returning_submit(payload:NewReturningApplication,current_student:dict=Depends(require_full_student_access)):
    try:
        row=submit_student_returning(current_student['student_number'],payload.course_code,payload.cycle_code)
        return {'success':True,'message':'Returning application submitted for review. This is not an admission or enrolment confirmation.','data':row}
    except ValueError as error:
        raise HTTPException(status_code=400,detail=str(error)) from error
