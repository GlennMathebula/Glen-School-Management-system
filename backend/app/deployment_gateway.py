from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from urllib.parse import unquote

from starlette.responses import FileResponse, PlainTextResponse
from starlette.types import Receive, Scope, Send

from app.main import app as api_app


PROJECT_ROOT = Path(__file__).resolve().parents[2]

WEBSITE_DIST = PROJECT_ROOT / "frontends" / "website-web" / "dist"
APPLICATIONS_DIST = PROJECT_ROOT / "frontends" / "applications-web" / "dist"
CAREERS_DIST = PROJECT_ROOT / "frontends" / "careers-web" / "dist"
STUDENT_DIST = PROJECT_ROOT / "frontends" / "student-web" / "dist"

APPLICATIONS_PUBLIC_URL = os.getenv(
    "APPLICATIONS_PUBLIC_URL",
    "https://www.glenmoniques.co.za/applications",
).rstrip("/")

CAREERS_PUBLIC_URL = os.getenv(
    "CAREERS_PUBLIC_URL",
    "https://www.glenmoniques.co.za/careers",
).rstrip("/")

STUDENT_PUBLIC_URL = os.getenv(
    "STUDENT_PUBLIC_URL",
    "https://www.glenmoniques.co.za/lms",
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


def _scope_without_prefix(scope: Scope, prefix: str) -> Scope:
    request_path = _path(scope)
    stripped = request_path[len(prefix) :] if request_path.startswith(prefix) else request_path

    if not stripped:
        stripped = "/"

    if not stripped.startswith("/"):
        stripped = "/" + stripped

    routed_scope = dict(scope)
    routed_scope["path"] = stripped
    routed_scope["raw_path"] = stripped.encode("utf-8")
    return routed_scope


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

    Current-plan public routing through one custom domain:
      www.glenmoniques.co.za/              -> website-web
      www.glenmoniques.co.za/applications  -> applications-web
      www.glenmoniques.co.za/careers       -> careers-web
      www.glenmoniques.co.za/lms           -> student-web
      www.glenmoniques.co.za/api/*         -> FastAPI

    /api and /health are routed to FastAPI before frontend routing. This keeps
    all browser applications same-origin and avoids requiring permissive CORS.

    Dedicated subdomain host routing is retained for a future plan upgrade.
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

        # Current Railway plan exposes one custom domain on this service.
        # Serve each web application under a stable path prefix. The frontend
        # bundles use matching Vite base paths and BrowserRouter basenames.
        if path == "/applications" or path.startswith("/applications/"):
            routed_scope = _scope_without_prefix(scope, "/applications")
            await applications_app(routed_scope, receive, send)
            return

        if path == "/careers" or path.startswith("/careers/"):
            routed_scope = _scope_without_prefix(scope, "/careers")
            await careers_app(routed_scope, receive, send)
            return

        if path == "/lms" or path.startswith("/lms/"):
            routed_scope = _scope_without_prefix(scope, "/lms")
            await student_app(routed_scope, receive, send)
            return

        await website_app(scope, receive, send)


app = GlenMoniquesDeploymentGateway()