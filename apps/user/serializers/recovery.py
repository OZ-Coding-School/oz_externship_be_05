from typing import Any

from rest_framework import serializers
from rest_framework.serializers import Serializer

from apps.user.models import User
from apps.user.serializers.base import BaseMixin
from apps.user.serializers.mixins import EmailTokenMixin, SenderMixin, SMSTokenMixin
from apps.user.utils.sender import EmailSender


class RestoreAccountSerializer(SenderMixin, EmailTokenMixin, Serializer[Any]):
    email_token = BaseMixin.get_verify_token_field()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        email = self.verify_email_token(attrs["email_token"])
        user = User.objects.filter(email=email).first()
        if user is None:
            raise serializers.ValidationError("해당 이메일로 가입된 계정이 없습니다.")
        attrs["user"] = user
        attrs["email"] = email
        return attrs


class FindEmailSerializer(SenderMixin, SMSTokenMixin, Serializer[Any]):
    sms_token = BaseMixin.get_verify_token_field()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        phone_number = self.verify_sms_token(attrs["sms_token"])
        user = User.objects.filter(phone_number=phone_number).first()
        if user is None:
            raise serializers.ValidationError("해당 휴대전화 번호로 가입된 계정이 없습니다.")
        attrs["masked_email"] = EmailSender.mask_email(user.email)
        return attrs


class FindPasswordSerializer(SenderMixin, EmailTokenMixin, Serializer[Any], BaseMixin):
    email_token = BaseMixin.get_verify_token_field()
    new_password = BaseMixin.get_password_field(write_only=True)

    def validate_new_password(self, value: str) -> str:
        return BaseMixin.validate_password(self, value)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        email = self.verify_email_token(attrs["email_token"])
        user = User.objects.filter(email=email).first()
        if user is None:
            raise serializers.ValidationError("해당 이메일로 가입된 계정이 없습니다.")
        attrs["user"] = user
        return attrs
