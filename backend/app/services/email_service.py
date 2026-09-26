import mimetypes
import smtplib
from email.message import EmailMessage
from pathlib import Path

from app.config import settings

# ============================================================
# SMTP VALIDATION
# ============================================================

def validate_email_configuration() -> None:

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

    with smtplib.SMTP(
        settings.smtp_host,
        settings.smtp_port,
        timeout=30,
    ) as server:

        server.ehlo()

        if settings.smtp_use_tls:

            server.starttls()

            server.ehlo()

        server.login(
            settings.smtp_username,
            settings.smtp_password,
        )

        server.send_message(
            message
        )