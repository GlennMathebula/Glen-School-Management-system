# Glen Moniques Careers Web

Public recruitment portal for Glen Moniques.

## Development

Backend:

```powershell
cd "C:\Projects\Glen Moniques SMS\backend"
python -m uvicorn app.main:app --reload
```

Careers frontend:

```powershell
cd "C:\Projects\Glen Moniques SMS\frontends\careers-web"
npm run dev
```

Open:

http://localhost:5174

The Vite development server proxies `/api` and `/health` to FastAPI on
`http://127.0.0.1:8000`.
