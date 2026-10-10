# Glen Moniques Main Website

Frontend: `frontends/website-web`

## Public production routing

- `https://www.glenmoniques.co.za/` -> website-web
- `https://www.glenmoniques.co.za/applications` -> applications-web
- `https://www.glenmoniques.co.za/careers` -> careers-web
- `https://lms.glenmoniques.co.za` -> student-web
- `https://api.glenmoniques.co.za` -> FastAPI backend on Railway
- `https://www.glenmoniques.co.za/payfast/return` -> website-web PayFast return page
- `https://www.glenmoniques.co.za/payfast/cancel` -> website-web PayFast cancel page

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
3. send other main-site routes such as `/about`, `/programmes`, `/shop`,
   `/donate`, `/contact`, `/payfast/return`, `/payfast/cancel`, `/terms`,
   `/popia` and `/cookies` back to website-web/index.html.


## Production integration callback URLs

Use these production URLs when the API is deployed at `api.glenmoniques.co.za`
and the public website is deployed at `www.glenmoniques.co.za`.

### PayFast

- Return URL: `https://www.glenmoniques.co.za/payfast/return`
- Cancel URL: `https://www.glenmoniques.co.za/payfast/cancel`
- Notify / ITN URL: `https://api.glenmoniques.co.za/api/payments/payfast/notify`

Recommended backend environment values:

```text
PAYFAST_RETURN_URL=https://www.glenmoniques.co.za/payfast/return
PAYFAST_CANCEL_URL=https://www.glenmoniques.co.za/payfast/cancel
PAYFAST_NOTIFY_URL=https://api.glenmoniques.co.za/api/payments/payfast/notify
```

The PayFast notify URL is intentionally a FastAPI endpoint, not a React page.
PayFast posts the server-to-server ITN there so the backend can verify the
signature/source/server response and update finance records securely.

### Google Calendar OAuth

Google redirect / callback URI:

`https://api.glenmoniques.co.za/api/google/calendar/callback`

Recommended backend environment value:

```text
GOOGLE_CALENDAR_REDIRECT_URI=https://api.glenmoniques.co.za/api/google/calendar/callback
```

The Google callback is intentionally handled by FastAPI because the backend
must securely exchange the authorization code and validate the OAuth state.

## Legal notice

The Terms, POPIA and Cookie pages are website drafts and should be reviewed
against Glen Moniques' final internal policies and legal requirements before production launch.
