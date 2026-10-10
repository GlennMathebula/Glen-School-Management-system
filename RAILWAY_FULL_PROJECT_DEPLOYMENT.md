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

## Production routing

The current Railway plan allows one custom domain on the combined application
service. The full deployable SMS therefore uses one production hostname with
path-based routing:

- `https://www.glenmoniques.co.za/` -> public website
- `https://www.glenmoniques.co.za/applications` -> learner applications / registration
- `https://www.glenmoniques.co.za/careers` -> careers portal
- `https://www.glenmoniques.co.za/lms` -> student web / LMS
- `https://www.glenmoniques.co.za/api/*` -> FastAPI
- `https://www.glenmoniques.co.za/health` -> application health

`/api/*` and `/health*` are routed to FastAPI before frontend routing, so the web
frontends use same-origin API calls without permissive CORS.

The deployment gateway still understands the dedicated subdomain hostnames for
a future Railway plan upgrade, but they are not required for the current
production deployment.

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