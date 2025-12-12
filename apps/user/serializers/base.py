from typing import Any

from django.conf import settings
from django.contrib.auth.password_validation import (
    validate_password as dj_validate_password,
)
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.user.validaters.validate_token import is_valid_token_format

# 원래 진짜 단순했는데 mypy떄문에 곱창냈어요


def _merge_defaults(defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {**defaults, **overrides}
    return merged


class BaseMixin:
    # [이메일] [email]
    @staticmethod
    def get_email_field(**kwargs: Any) -> serializers.EmailField:
        """
        이메일 필드를 반환합니다.
        [🌸] validate가 없습니다.
        """
        return serializers.EmailField(**_merge_defaults({"required": True}, kwargs))

    # [인증코드] [verify_code] [code]
    @staticmethod
    def get_verify_code_field(**kwargs: Any) -> serializers.CharField:
        """
        인증 코드 필드를 반환합니다.
        [☠️] validate가 있습니다 !
        """
        code_length = getattr(settings, "VERIFICATION_CODE_LENGTH", 6)
        defaults: dict[str, Any] = {
            "min_length": code_length,
            "max_length": code_length,
            "allow_blank": False,
            "required": True,
        }
        return serializers.CharField(**_merge_defaults(defaults, kwargs))

    def validate_verify_code(self, value: str) -> str:
        if len(value) != getattr(settings, "VERIFICATION_CODE_LENGTH", 6):
            raise serializers.ValidationError("코드 길이가 올바르지 않습니다.")
        if any(ch not in settings.VERIFICATION_CODE_CHARS for ch in value):
            raise serializers.ValidationError("코드 형식이 올바르지 않습니다.")
        return value

    # [인증 서비스 토큰] [토큰] [verify_token] [token]
    @staticmethod
    def get_verify_token_field(**kwargs: Any) -> serializers.CharField:
        """
        인증 토큰 필드를 반환합니다.
        [☠️] validate가 있습니다 !
        """
        return serializers.CharField(**_merge_defaults({"required": True}, kwargs))

    def validate_verify_token(self, value: str) -> str:
        if not is_valid_token_format(value, token_bytes=settings.VERIFICATION_TOKEN_BYTES):
            raise serializers.ValidationError("토큰 형식이 올바르지 않습니다.")
        return value

    # [비밀번호] [password] [pw]
    @staticmethod
    def get_password_field(**kwargs: Any) -> serializers.CharField:
        """
        비밀번호 필드를 반환합니다.
        [☠️] validate가 있습니다 !
        """
        return serializers.CharField(**_merge_defaults({"required": True}, kwargs))

    def validate_password(self, value: str) -> str:
        try:
            dj_validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    # [전화번호] [phone] [phone_number]
    @staticmethod
    def get_phone_number_field(**kwargs: Any) -> serializers.CharField:
        """
        휴대폰 번호 필드를 반환합니다.
        [☠️] validate가 있습니다 !
        """
        defaults: dict[str, Any] = {
            "max_length": 15,
            "min_length": 9,
            "allow_blank": False,
            "trim_whitespace": True,
            "required": True,
        }
        return serializers.CharField(**_merge_defaults(defaults, kwargs))

    def validate_phone_number(self, value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError("전화번호는 숫자만 입력해주세요.")
        return value
