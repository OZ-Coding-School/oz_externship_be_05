from typing import Any

from rest_framework import serializers
from rest_framework.serializers import Serializer

from apps.user.models import User
from apps.user.serializers.base import BaseMixin


class EmailRequestSerializer(Serializer[Any], BaseMixin):
    email = BaseMixin.get_email_field()


class SignupEmailRequestSerializer(EmailRequestSerializer):
    def validate_email(self, value: str) -> str:  # noqa: D401
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 가입된 이메일입니다.")
        return value


class SMSRequestSerializer(Serializer[Any], BaseMixin):
    phone_number = BaseMixin.get_phone_number_field()


class EmailCodeSerializer(Serializer[Any], BaseMixin):

    email = BaseMixin.get_email_field()
    email_code = BaseMixin.get_verify_code_field()

    def validate_email_code(self, value: str) -> str:
        return self.validate_verify_code(value)


class PhoneCodeSerializer(Serializer[Any], BaseMixin):
    phone_number = BaseMixin.get_phone_number_field()
    sms_code = BaseMixin.get_verify_code_field()

    def validate_sms_code(self, value: str) -> str:
        return self.validate_verify_code(value)
