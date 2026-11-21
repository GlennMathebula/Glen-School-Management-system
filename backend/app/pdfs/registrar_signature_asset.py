"""Private Registrar signature loader for registration PDFs.

The signature MUST NOT be committed into the public GitHub repository.
Set GM_REGISTRAR_SIGNATURE_BASE64 as a Railway service environment variable.
The optional local asset supports non-production development only.
"""
from __future__ import annotations

import base64
from io import BytesIO
import logging
import os
from pathlib import Path

from PIL import Image as PILImage
from reportlab.platypus import Image as PDFImage

ENV_NAME = "GM_REGISTRAR_SIGNATURE_BASE64"
MAX_IMAGE_BYTES = 2_000_000


def get_registrar_signature_image(path: Path, *, width: float, height: float):
    """Return a ReportLab Image or None; never log or write signature bytes."""
    encoded = os.getenv(ENV_NAME, "").strip()
    if encoded:
        try:
            payload = base64.b64decode(encoded, validate=True)
            if not (16 <= len(payload) <= MAX_IMAGE_BYTES):
                raise ValueError("Signature image size is invalid")
            stream = BytesIO(payload)
            with PILImage.open(stream) as candidate:
                if candidate.format not in {"PNG", "JPEG"}:
                    raise ValueError("Signature must be PNG or JPEG")
                candidate.verify()
            stream.seek(0)
            return PDFImage(stream, width=width, height=height, kind="proportional")
        except Exception as error:
            logging.warning("Configured Registrar signature unavailable (%s)", type(error).__name__)

    local = Path(path)
    if local.is_file():
        try:
            return PDFImage(str(local), width=width, height=height, kind="proportional")
        except Exception as error:
            logging.warning("Local Registrar signature unavailable (%s)", type(error).__name__)
    return None
