"""Send BulkSMS through HTTPS; do not log OTPs or credentials."""
import base64
import json
import re
from urllib import request, error
from app.config import settings


def normalise_phone_number(value: str) -> str:
    number = re.sub(r"[\s().-]", "", str(value or ""))
    if number.startswith("00"):
        number = "+" + number[2:]
    if number.startswith("0") and len(number) == 10 and number.isdigit():
        number = "+27" + number[1:]
    if number.startswith("27") and len(number) == 11 and number.isdigit():
        number = "+" + number
    if not re.fullmatch(r"\+[1-9]\d{7,14}", number):
        raise ValueError("Staff mobile number missing or invalid")
    return number


def send_sms(*, recipient_phone: str, message: str) -> None:
    if not settings.bulksms_token_id or not settings.bulksms_token_secret:
        raise RuntimeError("BulkSMS configuration missing")
    number = normalise_phone_number(recipient_phone)
    if not message.strip():
        raise ValueError("SMS cannot be empty")
    key = f"{settings.bulksms_token_id}:{settings.bulksms_token_secret}".encode()
    req = request.Request("https://api.bulksms.com/v1/messages",
        data=json.dumps({"to": number, "body": message}).encode(), method="POST",
        headers={"Authorization": "Basic " + base64.b64encode(key).decode(),
                 "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with request.urlopen(req, timeout=20) as response:
            response.read()
    except error.HTTPError as exc:
        raise RuntimeError(f"BulkSMS rejected request (HTTP {exc.code})") from None
    except error.URLError:
        raise RuntimeError("BulkSMS HTTPS network failure") from None
