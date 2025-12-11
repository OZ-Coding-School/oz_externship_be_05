from __future__ import annotations

import os
from typing import Optional

from twilio.rest import Client

from django.conf import settings

ACCOUNT_SID = getattr(settings, "TWILIO_ACCOUNT_SID", None) or os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = getattr(settings, "TWILIO_AUTH_TOKEN", None) or os.getenv("TWILIO_AUTH_TOKEN")
VERIFY_SERVICE_SID = getattr(settings, "TWILIO_VERIFY_SERVICE_SID", None) or os.getenv("TWILIO_VERIFY_SERVICE_SID")


def _get_client() -> Client:
    if not ACCOUNT_SID or not AUTH_TOKEN:
        raise RuntimeError("ACCOUNT_SID || AUTH_TOKEN 값 없음.")
    return Client(ACCOUNT_SID, AUTH_TOKEN)


def make_it_korean(phone_number: str) -> str:
    digits = "".join(ch for ch in phone_number if ch.isdigit())
    if digits.startswith("0"):
        digits = digits[1:]
    return f"+82{digits}"


def send_verification_code(phone_number: str ,locale: str = "ko") -> Optional[str]:
    """
    twilio verify API로 인증코드를 전송합니다.
    """
    if not VERIFY_SERVICE_SID:
        raise RuntimeError("VERIFY_SERVICE_SID 값 없음.")

    client = _get_client()
    verification = client.verify.v2.services(VERIFY_SERVICE_SID).verifications.create(
        to=make_it_korean(phone_number),
        channel="sms",
        locale=locale,
    )
    return verification.sid


def check_verification_code(phone_number: str, code: str) -> bool:
    """
    twilio verify API로 인증코드를 검증합니다.
    """
    if not VERIFY_SERVICE_SID:
        raise RuntimeError("VERIFY_SERVICE_SID 값 없음.")

    client = _get_client()
    result = client.verify.v2.services(VERIFY_SERVICE_SID).verification_checks.create(
        to=make_it_korean(phone_number),
        code=code,
    )
    return result.status == "approved"
