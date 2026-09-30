from fastapi import Header, HTTPException
from app.services.career_auth_service import decode_applicant_token, get_applicant_by_id

def get_current_career_applicant(authorization: str | None = Header(default=None)) -> dict:
    if not authorization: raise HTTPException(401, "Career applicant authentication is required.")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer": raise HTTPException(401, "Invalid Career applicant authorization header.")
    try:
        p = decode_applicant_token(parts[1].strip())
        return get_applicant_by_id(str(p["sub"]))
    except ValueError as e:
        raise HTTPException(401, str(e)) from e
