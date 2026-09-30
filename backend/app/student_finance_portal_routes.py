from fastapi import APIRouter,Depends,HTTPException
from app.services.student_finance_portal_service import get_student_finance_summary
from app.student_auth_dependency import require_full_student_access
router=APIRouter(tags=["Student Portal"])
@router.get("/api/student/finance")
def student_finance_summary(current_student:dict=Depends(require_full_student_access)):
    try:return {"success":True,"data":get_student_finance_summary(current_student["student_number"])}
    except Exception as error:
        print("ERROR loading student finance summary:",error)
        raise HTTPException(status_code=500,detail="Student finance information could not be retrieved.")
