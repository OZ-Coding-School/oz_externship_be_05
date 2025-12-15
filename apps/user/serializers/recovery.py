from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.user.models import User
from apps.user.serializers.base import BaseMixin
from apps.user.serializers.mixins import EmailTokenMixin, SMSTokenMixin, SenderTokenMixin
from apps.user.serializers.verification import EmailRequestSerializer


class FindEmailSerializer(SenderTokenMixin, SMSTokenMixin, serializers.Serializer):

    name = serializers.CharField(max_length=30)
    emails = serializers.ListField(child=serializers.CharField(), read_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        phone_number = self.verify_sms_token(attrs["sms_token"])
        emails = list(
            User.objects.filter(phone_number=phone_number, name=attrs["name"]).values_list("email", flat=True)
        )
        attrs["emails"] = emails
        return attrs


class PasswordResetRequestSerializer(EmailRequestSerializer):
    def validate_email(self, value: str) -> str:  # noqa: D401
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("해당 이메일로 가입된 계정이 없습니다.")
        return value


class PasswordResetSerializer(SenderTokenMixin, EmailTokenMixin, serializers.Serializer):
    new_password = BaseMixin.get_password_field(write_only=True)

    def validate_new_password(self, value: str) -> str:  # noqa: D401
        return BaseMixin.validate_password(self, value)

    def save(self, **kwargs: Any) -> User:
        email = self.verify_email_token(self.validated_data["email_token"])
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("계정을 찾을 수 없습니다.") from exc
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        return user


class RestoreSerializer(SenderTokenMixin, EmailTokenMixin, serializers.Serializer):
    def save(self, **kwargs: Any) -> User:
        email = self.verify_email_token(self.validated_data["email_token"])
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("계정을 찾을 수 없습니다.") from exc
        user.is_active = True
        user.save(update_fields=["is_active", "updated_at"])
        return user
