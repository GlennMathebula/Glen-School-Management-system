# Glen Moniques Applications Web

Frontend 1 of the Glen Moniques SMS five-client architecture.

## Purpose

Public web frontend for:

- New student applications
- Application acknowledgement resend
- Application status (UI prepared; secure public status API still required)
- Accepted-applicant public registration

## Backend

This frontend shares the existing FastAPI backend with the other four clients.

Local backend:

```powershell
cd "C:\Projects\Glen Moniques SMS\backend"
python -m uvicorn app.main:app --reload
```

Local frontend:

```powershell
cd "C:\Projects\Glen Moniques SMS\frontends\applications-web"
npm run dev
```

Open:

http://localhost:5173

## Current public API contract

- POST `/api/applications`
- POST `/api/applications/{student_number}/acknowledgement/resend`
- POST `/api/public/registration`

The current backend does not expose:

- a secure public GET endpoint for application status
- a public active-programme catalogue endpoint

Those two API additions should be made before production launch.
