from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from urllib.parse import unquote

from starlette.responses import FileResponse, PlainTextResponse, RedirectResponse
from starlette.types import Receive, Scope, Send

from app.main import app as api_app


PROJECT_ROOT = Path(__file__).resolve().parents[2]

WEBSITE_DIST = PROJECT_ROOT / "frontends" / "website-web" / "dist"
APPLICATIONS_DIST = PROJECT_ROOT / "frontends" / "applications-web" / "dist"
CAREERS_DIST = PROJECT_ROOT / "frontends" / "careers-web" / "dist"
STUDENT_DIST = PROJECT_ROOT / "frontends" / "student-web" / "dist"

APPLICATIONS_PUBLIC_URL = os.getenv(
    "APPLICATIONS_PUBLIC_URL",
    "https://applications.glenmoniques.co.za",
).rstrip("/")

CAREERS_PUBLIC_URL = os.getenv(
    "CAREERS_PUBLIC_URL",
    "https://careers.glenmoniques.co.za",
).rstrip("/")

STUDENT_PUBLIC_URL = os.getenv(
    "STUDENT_PUBLIC_URL",
    "https://lms.glenmoniques.co.za",
).rstrip("/")


def _host(scope: Scope) -> str:
    for key, value in scope.get("headers", []):
        if key.lower() == b"host":
            return value.decode("latin-1").split(":", 1)[0].strip().lower()
    return ""


def _path(scope: Scope) -> str:
    return unquote(scope.get("path") or "/")


def _host_matches(host: str, names: tuple[str, ...]) -> bool:
    return host in names or any(host.startswith(prefix) for prefix in names)


def _safe_file(root: Path, request_path: str) -> Path | None:
    clean = request_path.split("?", 1)[0].split("#", 1)[0]
    clean = clean.lstrip("/")

    candidate = (root / clean).resolve()
    root_resolved = root.resolve()

    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        return None

    if candidate.is_file():
        return candidate

    return None


class SPAStaticApp:
    def __init__(self, root: Path, label: str):
        self.root = root
        self.label = label

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            response = PlainTextResponse("Unsupported protocol", status_code=400)
            await response(scope, receive, send)
            return

        if not self.root.exists():
            response = PlainTextResponse(
                f"{self.label} frontend build is not available.",
                status_code=503,
            )
            await response(scope, receive, send)
            return

        request_path = _path(scope)
        target = _safe_file(self.root, request_path)

        if target is None:
            target = self.root / "index.html"

        if not target.exists():
            response = PlainTextResponse(
                f"{self.label} frontend index is not available.",
                status_code=503,
            )
            await response(scope, receive, send)
            return

        media_type, _ = mimetypes.guess_type(str(target))

        response = FileResponse(
            target,
            media_type=media_type,
            headers={
                "Cache-Control": (
                    "no-cache"
                    if target.name == "index.html"
                    else "public, max-age=31536000, immutable"
                )
            },
        )
        await response(scope, receive, send)


website_app = SPAStaticApp(WEBSITE_DIST, "Website")
applications_app = SPAStaticApp(APPLICATIONS_DIST, "Applications")
careers_app = SPAStaticApp(CAREERS_DIST, "Careers")
student_app = SPAStaticApp(STUDENT_DIST, "Student LMS")


class GlenMoniquesDeploymentGateway:
    """
    One Railway application service for the full deployable Glen Moniques SMS.

    Public routing:
      www.glenmoniques.co.za          -> website-web
      applications.glenmoniques.co.za -> applications-web
      careers.glenmoniques.co.za      -> careers-web
      lms.glenmoniques.co.za          -> student-web
      api.glenmoniques.co.za          -> FastAPI

    /api and /health are also routed to FastAPI on every host. This keeps
    frontend API calls same-origin and avoids requiring permissive CORS.
    """

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] not in {"http", "websocket"}:
            await api_app(scope, receive, send)
            return

        host = _host(scope)
        path = _path(scope)

        # API endpoints remain reachable from every Glen Moniques host so
        # browser frontends can call /api using the same origin.
        if (
            path == "/health"
            or path.startswith("/health/")
            or path == "/api"
            or path.startswith("/api/")
            or host == "api.glenmoniques.co.za"
        ):
            await api_app(scope, receive, send)
            return

        if scope["type"] == "websocket":
            await api_app(scope, receive, send)
            return

        if host in {
            "applications.glenmoniques.co.za",
            "apply.glenmoniques.co.za",
        }:
            await applications_app(scope, receive, send)
            return

        if host == "careers.glenmoniques.co.za":
            await careers_app(scope, receive, send)
            return

        if host == "lms.glenmoniques.co.za":
            await student_app(scope, receive, send)
            return

        # Keep the existing public website links working without forcing
        # BrowserRouter basename changes in the dedicated React applications.
        if path == "/applications":
            response = RedirectResponse(
                APPLICATIONS_PUBLIC_URL + "/",
                status_code=307,
            )
            await response(scope, receive, send)
            return

        if path.startswith("/applications/"):
            suffix = path[len("/applications") :]
            response = RedirectResponse(
                APPLICATIONS_PUBLIC_URL + suffix,
                status_code=307,
            )
            await response(scope, receive, send)
            return

        if path == "/careers":
            response = RedirectResponse(
                CAREERS_PUBLIC_URL + "/",
                status_code=307,
            )
            await response(scope, receive, send)
            return

        if path.startswith("/careers/"):
            suffix = path[len("/careers") :]
            response = RedirectResponse(
                CAREERS_PUBLIC_URL + suffix,
                status_code=307,
            )
            await response(scope, receive, send)
            return

        if path == "/lms":
            response = RedirectResponse(
                STUDENT_PUBLIC_URL + "/",
                status_code=307,
            )
            await response(scope, receive, send)
            return

        if path.startswith("/lms/"):
            suffix = path[len("/lms") :]
            response = RedirectResponse(
                STUDENT_PUBLIC_URL + suffix,
                status_code=307,
            )
            await response(scope, receive, send)
            return

        await website_app(scope, receive, send)


app = GlenMoniquesDeploymentGateway()