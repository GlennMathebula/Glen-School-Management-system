from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,Field
from app.services.staff_permission_service import require_permission
from app.services.returning_application_service import staff_list_returning,staff_review_returning

router=APIRouter(prefix='/api/staff/admissions/returning-applications',tags=['Returning Admissions Review'])

class ReviewReturning(BaseModel):
    status:str
    note:str=Field(default='',max_length=3000)

@router.get('')
def returning_review_queue(status:str|None=None,limit:int=Query(50,ge=1,le=200),
      staff:dict=Depends(require_permission('VIEW_APPLICATIONS'))):
    if status is not None and status not in ('Pending','UnderReview','Rejected'):
        raise HTTPException(400,'Invalid status filter.')
    return {'success':True,'applications':staff_list_returning(status,limit)}

@router.patch('/{request_id}')
def returning_review(request_id:UUID,payload:ReviewReturning,
      staff:dict=Depends(require_permission('MANAGE_APPLICATIONS'))):
    try:
        row=staff_review_returning(request_id,payload.status,payload.note,staff['staff_code'])
        return {'success':True,'data':row}
    except ValueError as error:
        raise HTTPException(status_code=400,detail=str(error)) from error
