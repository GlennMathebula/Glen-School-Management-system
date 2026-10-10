# Glen Moniques Main Website

Frontend: `frontends/website-web`

## Public production routing

- `https://www.glenmoniques.co.za/` -> website-web
- `https://www.glenmoniques.co.za/applications` -> applications-web
- `https://www.glenmoniques.co.za/careers` -> careers-web
- `https://lms.glenmoniques.co.za` -> student-web
- `https://api.glenmoniques.co.za` -> FastAPI backend on Railway

The main website intentionally uses normal `<a>` links for `/applications` and `/careers`
so a production reverse proxy can hand those paths to their separate frontend services.

## Local development

```powershell
cd "C:\Projects\Glen Moniques SMS\frontends\website-web"
npm run dev
```

## Production build

```powershell
npm run build
```

## Important deployment note

The main site uses `BrowserRouter`, so the production web server/front-door proxy must:
1. send `/applications` and `/applications/*` to applications-web;
2. send `/careers` and `/careers/*` to careers-web;
3. send other main-site routes such as `/about`, `/programmes`, `/contact`,
   `/terms`, `/popia` and `/cookies` back to website-web/index.html.

## Legal notice

The Terms, POPIA and Cookie pages are website drafts and should be reviewed
against Glen Moniques' final internal policies and legal requirements before production launch.
