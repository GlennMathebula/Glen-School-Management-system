from datetime import datetime, timedelta, timezone
import jwt
from sqlalchemy import text
from app.config import settings
from app.database import engine
from app.services.staff_auth_service import hash_secret, verify_secret

TOKEN_TYPE = "career_applicant"

def _email(v: str) -> str:
    v = str(v or "").strip().lower()
    if not v or "@" not in v or "." not in v.split("@")[-1]:
        raise ValueError("A valid email address is required.")
    return v

def _jwt_secret() -> str:
    for n in ("jwt_secret_key","jwt_secret","secret_key","app_secret_key","access_token_secret","supabase_jwt_secret"):
        v = getattr(settings, n, None)
        if v: return str(v)
    for n in dir(settings):
        if "jwt" in n.lower() and "secret" in n.lower() and "service_role" not in n.lower():
            v = getattr(settings, n, None)
            if v and not callable(v): return str(v)
    raise RuntimeError("No JWT secret could be resolved from app.config.settings.")

def _jwt_algorithm() -> str:
    return str(getattr(settings, "jwt_algorithm", None) or "HS256")

def create_applicant_token(a: dict) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub":str(a["id"]),"type":TOKEN_TYPE,"email":a["email"],"applicant_number":a["applicant_number"],"iat":int(now.timestamp()),"exp":int((now+timedelta(hours=8)).timestamp())}, _jwt_secret(), algorithm=_jwt_algorithm())

def decode_applicant_token(token: str) -> dict:
    try:
        p = jwt.decode(token, _jwt_secret(), algorithms=[_jwt_algorithm()])
    except jwt.ExpiredSignatureError as e:
        raise ValueError("Career applicant session has expired.") from e
    except jwt.InvalidTokenError as e:
        raise ValueError("Invalid career applicant session.") from e
    if p.get("type") != TOKEN_TYPE or not p.get("sub"):
        raise ValueError("Invalid career applicant session.")
    return p

def create_applicant_account(**d) -> dict:
    d["email"] = _email(d["email"])
    d["password_hash"] = hash_secret(d.pop("password"))
    with engine.begin() as c:
        if c.execute(text("SELECT 1 FROM public.career_applicants WHERE lower(email)=:email LIMIT 1"), {"email":d["email"]}).first():
            raise ValueError("A Careers account already exists for this email address.")
        r = c.execute(text("""INSERT INTO public.career_applicants (applicant_number,first_name,last_name,email,cell_number,national_id,password_hash,account_status)
        VALUES (:applicant_number,:first_name,:last_name,:email,:cell_number,:national_id,:password_hash,'Active')
        RETURNING id,applicant_number,first_name,last_name,email,cell_number,national_id,account_status,created_at"""), d).mappings().first()
    return dict(r)

def authenticate_applicant(*, email: str, password: str) -> dict:
    email = _email(email)
    with engine.begin() as c:
        r = c.execute(text("SELECT * FROM public.career_applicants WHERE lower(email)=:email LIMIT 1 FOR UPDATE"), {"email":email}).mappings().first()
        if not r: raise ValueError("Email or password is incorrect.")
        a = dict(r)
        if a["account_status"] != "Active": raise ValueError("Career applicant account is not active.")
        if a.get("locked_until") and a["locked_until"] > datetime.now(timezone.utc): raise ValueError("Career applicant account is temporarily locked.")
        if not verify_secret(password, a["password_hash"]):
            n = int(a.get("failed_login_attempts") or 0) + 1
            if n >= 5:
                c.execute(text("UPDATE public.career_applicants SET failed_login_attempts=:n,locked_until=NOW()+INTERVAL '30 minutes',updated_at=NOW() WHERE id=:id"), {"n":n,"id":a["id"]})
            else:
                c.execute(text("UPDATE public.career_applicants SET failed_login_attempts=:n,updated_at=NOW() WHERE id=:id"), {"n":n,"id":a["id"]})
            raise ValueError("Email or password is incorrect.")
        c.execute(text("UPDATE public.career_applicants SET failed_login_attempts=0,locked_until=NULL,last_login_at=NOW(),updated_at=NOW() WHERE id=:id"), {"id":a["id"]})
    public = {k:a.get(k) for k in ("id","applicant_number","first_name","last_name","email","cell_number","national_id","account_status","created_at")}
    return {"account":public,"access_token":create_applicant_token(a),"token_type":"bearer","expires_in_hours":8}

def get_applicant_by_id(applicant_id: str) -> dict:
    with engine.connect() as c:
        r = c.execute(text("SELECT id,applicant_number,first_name,last_name,email,cell_number,national_id,account_status,last_login_at,created_at,updated_at FROM public.career_applicants WHERE id=CAST(:id AS uuid) LIMIT 1"), {"id":applicant_id}).mappings().first()
    if not r or r["account_status"] != "Active": raise ValueError("Career applicant account was not found or is inactive.")
    return dict(r)

def change_applicant_password(*, applicant_id: str, current_password: str, new_password: str):
    with engine.begin() as c:
        r = c.execute(text("SELECT password_hash FROM public.career_applicants WHERE id=CAST(:id AS uuid) LIMIT 1 FOR UPDATE"), {"id":applicant_id}).mappings().first()
        if not r: raise ValueError("Career applicant account was not found.")
        if not verify_secret(current_password, r["password_hash"]): raise ValueError("Current password is incorrect.")
        if verify_secret(new_password, r["password_hash"]): raise ValueError("New password must be different from the current password.")
        c.execute(text("UPDATE public.career_applicants SET password_hash=:h,updated_at=NOW() WHERE id=CAST(:id AS uuid)"), {"h":hash_secret(new_password),"id":applicant_id})
