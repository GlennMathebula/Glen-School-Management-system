# Glen Moniques Staff Desktop

Portal 4 of the Glen Moniques SMS.

## Run the backend

```powershell
cd "C:\Projects\Glen Moniques SMS\backend"
python -m uvicorn app.main:app --reload
```

## Run Staff Desktop in development

```powershell
cd "C:\Projects\Glen Moniques SMS\frontends\staff-desktop"
npm run dev
```

This launches the Vite UI and an Electron desktop window.

## Run built desktop

```powershell
cd "C:\Projects\Glen Moniques SMS\frontends\staff-desktop"
npm run desktop
```

The built desktop connects to:

http://127.0.0.1:8000
