from __future__ import annotations

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.user.serializers.base import BaseMixin
from apps.user.utils.sender import EmailSender, SMSSender


class SMSTokenMixin(BaseMixin):
    sms_token = BaseMixin.get_verify_token_field()

    def validate_sms_token(self, value: str) -> str:
        return BaseMixin.validate_verify_token(self, value)


class EmailTokenMixin(BaseMixin):
    email_token = BaseMixin.get_verify_token_field()

    def validate_email_token(self, value: str) -> str:
        return BaseMixin.validate_verify_token(self, value)

class SMSCodeMixin(BaseMixin):
    phone_number = BaseMixin.get_phone_number_field()
    sms_code = BaseMixin.get_verify_code_field()

    def validate_sms_code(self, value: str) -> str:
        BaseMixin.validate_verify_code(value)

class EmailCodeMixin(BaseMixin):
    email = BaseMixin.get_email_field()
    email_code = BaseMixin.get_verify_code_field()

    def validate_email_code(self, value: str) -> str:
        BaseMixin.validate_verify_code(value)

class SenderMixin:
    sms_sender_class = SMSSender
    email_sender_class = EmailSender

    def verify_sms_token(self, token: str) -> str:
        try:
            return self.sms_sender_class().verify_token(token)
        except ValidationError:
            raise
        except RuntimeError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - unexpected path
            raise serializers.ValidationError("회원가입 세션이 만료되었습니다.") from exc

    def verify_email_token(self, token: str) -> str:
        try:
            return self.email_sender_class().verify_token(token)
        except ValidationError:
            raise
        except Exception as exc:  # pragma: no cover - unexpected path
            raise serializers.ValidationError("회원가입 세션이 만료되었습니다.") from exc
    
    def verify_sms_code(self, phone_number: str, code: str) -> str:
        try:
            return self.sms_sender_class().verify_code(phone_number,code)
        except ValidationError:
            raise
        except Exception as exc:  # pragma: no cover - unexpected path
            raise serializers.ValidationError("코드 검증에 실패했습니다.") from exc
    
    def verify_email_code(self, email: str, code: str) -> str:
        try:
            return self.email_sender_class().verify_code(email,code)
        except ValidationError:
            raise
        except Exception as exc:  # pragma: no cover - unexpected path
            raise serializers.ValidationError("코드 검증에 실패했습니다.") from exc