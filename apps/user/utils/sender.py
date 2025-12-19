from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

from django.conf import settings
from django.core.mail import send_mail
from rest_framework.exceptions import APIException, ValidationError
from twilio.rest import Client  # type: ignore[import-untyped]

from apps.user.utils.verification import VerificationService

logger = logging.getLogger(__name__)


class TWILIO_STATUS(Enum):
    Pending = "pending"
    Approved = "approved"
    Canceled = "canceled"
    MaxAttemptsReached = "max_attempts_reached"
    Deleted = "deleted"
    Failed = "failed"
    Expired = "expired"


class Sender(ABC):
    def __init__(self, verification_service: Optional[VerificationService] = None) -> None:
        self.verification_service = verification_service or VerificationService()

    @abstractmethod
    def send(self, send_to: str, *args: Any, **kwargs: Any) -> None:
        """인증 코드를 전송함"""
        ...

    @abstractmethod
    def verify_code(self, identifier: str, code: str) -> str:
        """코드를 검증함. 성공하면 토큰 반환"""
        ...

    def verify_token(self, token: str) -> str:
        """토큰 검증함. 성공하면 idenfier(폰번호/이메일) 반환"""
        identifier = self.verification_service.verify_token(token, consume=True)
        if identifier:
            return identifier
        raise ValidationError("인증이 만료되었습니다.")


class EmailSender(Sender):
    @staticmethod
    def mask_email(email: str, keep_start: int = 1, keep_end: int = 1, mask_char: str = "*") -> str:
        if "@" not in email:
            raise ValueError("이메일 형식이 아닙니다.")
        local, domain = email.split("@", 1)
        if keep_start < 0 or keep_end < 0:
            raise ValueError("keep_start , keep_end 값은 0보다 커야함다")
        n = len(local)
        if n == 0:
            return email
        if keep_start + keep_end >= n:
            return f"{local}@{domain}"
        start = local[:keep_start] if keep_start > 0 else ""
        end = local[-keep_end:] if keep_end > 0 else ""
        masked_len = n - (keep_start + keep_end)
        return f"{start}{mask_char * masked_len}{end}@{domain}"

    def send(self, send_to: str) -> None:
        try:
            subject = f"[오즈코딩스쿨] 이메일 인증 코드"
            code = self.verification_service.generate_code(send_to)
            message = f"인증코드: {code}\n"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [send_to])
            logger.info("인증 코드를 전송합니다.", extra={"to": send_to})
            return
        except Exception as exc:
            logger.exception(f"이메일 인증코드 전송 실패 : {exc}")
            raise APIException("이메일 전송에 실패했습니다.")

    def verify_code(self, email: str, code: str) -> str:
        try:
            if self.verification_service.verify(email, code, consume=True, is_token=False):
                return self.verification_service.generate_token(email)
            else:
                raise ValidationError("유효하지 않은 번호 / 코드입니다.")
        except ValidationError:
            # ValidationError는 그대로 상위로 올려 클라이언트에 검증 실패를 알림
            raise
        except Exception as exc:
            logger.exception(f"이메일 인증코드 검증 실패 : {exc}")
            raise APIException("검증에 실패했습니다.")


class SMSSender(Sender):
    def __init__(
        self,
        verification_service: Optional[VerificationService] = None,
    ) -> None:
        super().__init__(verification_service=verification_service)
        self.account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
        self.auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", None)
        self.verify_service_sid = getattr(settings, "TWILIO_VERIFY_SERVICE_SID", None)

        if not self.account_sid or not self.auth_token or not self.verify_service_sid:
            raise RuntimeError("Twilio 설정값이 안보임 : (ACCOUNT_SID / AUTH_TOKEN / VERIFY_SERVICE_SID).")

        self.client = Client(self.account_sid, self.auth_token)

    @staticmethod
    def make_it_korean(phone_number: str) -> str:
        digits = "".join(ch for ch in phone_number if ch.isdigit())
        if digits.startswith("0"):
            digits = digits[1:]
        return f"+82{digits}"

    def send(self, send_to: str, locale: str = "ko") -> None:
        try:
            self.client.verify.v2.services(self.verify_service_sid).verifications.create(
                to=self.make_it_korean(send_to),
                channel="sms",
                locale=locale,
            )
        except Exception as exc:
            logger.exception(f"SMS 전송 실패 : {exc}")
            raise APIException("SMS 전송에 실패했습니다.")

    def verify_code(self, phone_number: str, code: str) -> str:
        try:
            result = self.client.verify.v2.services(self.verify_service_sid).verification_checks.create(
                to=self.make_it_korean(phone_number),
                code=code,
            )
            status = getattr(result, "status", "")
            match status:
                case TWILIO_STATUS.Approved.value:
                    return self.verification_service.generate_token(phone_number)
                case TWILIO_STATUS.MaxAttemptsReached.value:
                    raise ValidationError("인증 코드 발송 한도에 도달했습니다.")
                case _:
                    raise ValidationError("인증 코드 발송에 실패했습니다.")

        except ValidationError:
            # 검증 실패 사유는 그대로 전달
            raise
        except Exception as exc:
            logger.exception(f"SMS 검증 실패 : {exc}")
            raise ValidationError("유효하지 않은 번호 혹은 코드입니다.")
