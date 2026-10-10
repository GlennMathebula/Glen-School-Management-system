import mimetypes
import base64
import json
from urllib import request, error
from email.utils import formataddr
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

from app.config import settings

# ============================================================
# SMTP VALIDATION
# ============================================================

def _send_resend(*, recipient_email, subject, html_body, text_body=None, attachment_path=None, attachment_name=None):
    if not settings.resend_api_key or not settings.resend_from_email:
        raise RuntimeError("Resend configuration missing")
    payload = {"from": formataddr(("Glen Moniques", settings.resend_from_email)),
               "to": [recipient_email], "subject": subject, "html": html_body}
    if text_body is not None:
        payload["text"] = text_body
    if attachment_path:
        f = Path(attachment_path)
        if not f.is_file():
            raise FileNotFoundError(f"Attachment missing: {f}")
        payload["attachments"] = [{"filename": attachment_name or f.name,
             "content": base64.b64encode(f.read_bytes()).decode("ascii")}]
    req = request.Request("https://api.resend.com/emails",
        data=json.dumps(payload).encode(), method="POST",
        headers={"User-Agent": "GlenMoniquesSMS/1.0",
                 "Authorization": "Bearer " + settings.resend_api_key,
                 "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with request.urlopen(req, timeout=20) as response:
            response.read()
    except error.HTTPError as exc:
        # Log only a redacted Resend error, never the request, PDF or API token.
        try:
            import logging
            import re

            response_type = str(exc.headers.get("Content-Type", "unknown"))[:80]
            response_server = str(exc.headers.get("Server", "unknown"))[:50]
            logging.getLogger(__name__).warning(
                "Resend gateway metadata: content_type=%s | server=%s | cf_ray_present=%s",
                response_type, response_server, bool(exc.headers.get("CF-Ray")),
            )

            body = exc.read(2048).decode("utf-8", errors="replace")
            try:
                details = json.loads(body)
            except (ValueError, TypeError):
                details = {}

            if not isinstance(details, dict):
                details = {}

            kind = str(details.get("name") or details.get("error") or "unknown")
            message = str(details.get("message") or "No message provided")

            def _redact(value):
                value = re.sub(r"(?i)\bre_[A-Za-z0-9_-]+", "[redacted-key]", value)
                value = re.sub(r"(?i)Bearer\s+\S+", "Bearer [redacted]", value)
                value = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[redacted-email]", value)
                value = re.sub(r"\b(?:\+?27|0)[0-9\s-]{8,15}\b", "[redacted-phone]", value)
                value = re.sub(r"[\r\n\t]+", " ", value)
                return value

            logging.getLogger(__name__).warning(
                "Resend HTTPS rejection: HTTP %s | type=%s | detail=%s",
                exc.code,
                _redact(kind)[:80],
                _redact(message)[:220],
            )
        except Exception:
            logging.getLogger(__name__).warning(
                "Resend HTTPS rejection: HTTP %s | details unavailable",
                exc.code,
            )
        raise RuntimeError(f"Resend rejected email (HTTP {exc.code})") from None
    except error.URLError:
        raise RuntimeError("Resend HTTPS network failure") from None


def validate_email_configuration() -> None:
    provider = settings.email_provider.strip().lower()
    if provider == "resend":
        if not settings.resend_api_key or not settings.resend_from_email:
            raise RuntimeError("Resend configuration missing")
        return
    if provider != "smtp":
        raise RuntimeError("Unsupported email provider")

    missing = []

    if not settings.smtp_host:
        missing.append("SMTP_HOST")

    if not settings.smtp_username:
        missing.append("SMTP_USERNAME")

    if not settings.smtp_password:
        missing.append("SMTP_PASSWORD")

    if not settings.smtp_from_email:
        missing.append("SMTP_FROM_EMAIL")

    if missing:

        raise RuntimeError(
            "Email is not configured. Missing: "
            + ", ".join(missing)
        )


# ============================================================
# SEND EMAIL
# ============================================================

def send_email(
    *,
    recipient_email: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
    attachment_path: str | Path | None = None,
    attachment_name: str | None = None,
) -> None:

    validate_email_configuration()
    if settings.email_provider.strip().lower() == "resend":
        return _send_resend(recipient_email=recipient_email, subject=subject,
            html_body=html_body, text_body=text_body,
            attachment_path=attachment_path, attachment_name=attachment_name)

    message = EmailMessage()

    message[
        "From"
    ] = (
        f"{settings.smtp_from_name} "
        f"<{settings.smtp_from_email}>"
    )

    message[
        "To"
    ] = recipient_email

    message[
        "Subject"
    ] = subject

    if text_body is None:

        text_body = (
            "Please view this email in an "
            "HTML-compatible email client."
        )

    message.set_content(
        text_body
    )

    message.add_alternative(
        html_body,
        subtype="html",
    )

    # --------------------------------------------------------
    # ATTACHMENT
    # --------------------------------------------------------

    if attachment_path:

        attachment_path = Path(
            attachment_path
        )

        if not attachment_path.exists():

            raise FileNotFoundError(
                f"Attachment not found: "
                f"{attachment_path}"
            )

        mime_type, _ = (
            mimetypes.guess_type(
                str(
                    attachment_path
                )
            )
        )

        if mime_type:

            maintype, subtype = (
                mime_type.split(
                    "/",
                    1,
                )
            )

        else:

            maintype = (
                "application"
            )

            subtype = (
                "octet-stream"
            )

        with attachment_path.open(
            "rb"
        ) as file:

            message.add_attachment(
                file.read(),
                maintype=maintype,
                subtype=subtype,
                filename=(
                    attachment_name
                    or attachment_path.name
                ),
            )

    # --------------------------------------------------------
    # SMTP CONNECTION
    # --------------------------------------------------------

    smtp_port = int(settings.smtp_port)
    ssl_context = ssl.create_default_context()

    if smtp_port == 465:

        with smtplib.SMTP_SSL(
            settings.smtp_host,
            smtp_port,
            timeout=30,
            context=ssl_context,
        ) as server:

            server.login(
                settings.smtp_username,
                settings.smtp_password,
            )

            server.send_message(
                message
            )

    else:

        with smtplib.SMTP(
            settings.smtp_host,
            smtp_port,
            timeout=30,
        ) as server:

            server.ehlo()

            if settings.smtp_use_tls:

                server.starttls(
                    context=ssl_context
                )

                server.ehlo()

            server.login(
                settings.smtp_username,
                settings.smtp_password,
            )

            server.send_message(
                message
            )
