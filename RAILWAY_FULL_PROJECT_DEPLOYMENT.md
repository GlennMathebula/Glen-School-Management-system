# Glen Moniques SMS - Railway Full Project Deployment

Railway Free currently allows this project to run as:

1. `Redis`
2. one full Glen Moniques application service

The application service builds and hosts:

- FastAPI backend
- `frontends/website-web`
- `frontends/applications-web`
- `frontends/careers-web`
- `frontends/student-web`

The Electron staff desktop and Expo student mobile application are not Railway
web services. They remain separately packaged/distributed clients that connect
to the same production API.

## Production hosts

All of these domains can point to the same Railway application service:

- `www.glenmoniques.co.za` -> public website
- `applications.glenmoniques.co.za` -> learner applications
- `careers.glenmoniques.co.za` -> careers
- `lms.glenmoniques.co.za` -> student web/LMS
- `api.glenmoniques.co.za` -> FastAPI

`/api/*` and `/health*` are routed to FastAPI on every host so that the web
frontends can use same-origin API calls without permissive CORS.

The public website keeps `/applications` and `/careers` as convenient links;
the deployment gateway redirects them to the dedicated hostnames.

## Railway service

Use repository root `/` and Dockerfile:

`/Dockerfile.railway`

Health check:

`/health`

The Railway-generated service domain can be used to verify the website and
`/health` before custom domains are moved.

## Required backend variables

The production application service needs the existing backend configuration,
including at least the mandatory values currently declared in `app/config.py`:

- `DATABASE_URL`
- `MAIL_HOST`
- `MAIL_PORT`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_FROM`
- `JWT_SECRET_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `REDIS_URL`

Optional integrations can then be added using their existing backend variables:

- Google Calendar OAuth variables
- PayFast variables
- SMTP variables
- Gemini variables

Do not commit `.env` files to GitHub.

For Railway Redis, use a project reference/private URL instead of the public
Redis proxy whenever the application and Redis are in the same Railway project.