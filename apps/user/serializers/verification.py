from typing import Any

from rest_framework.serializers import Serializer

from apps.user.serializers.base import BaseMixin


class EmailCodeSerializer(Serializer[Any], BaseMixin):
    email = BaseMixin.get_email()
    verify_code = BaseMixin.get_verify_code()


class ChangePasswordSerializer(EmailCodeSerializer):
    new_password = BaseMixin.get_password()

    def validate_new_password(self, value: str) -> str:
        return BaseMixin.validate_password(self, value)


class PhoneCodeSerializer(Serializer[Any], BaseMixin):
    phone_number = BaseMixin.get_phone_number()
    verify_code = BaseMixin.get_verify_code()


class TokensSerializer(Serializer[Any], BaseMixin):
    verify_token = BaseMixin.get_verify_token()


class AllTokensSerializer(Serializer[Any], BaseMixin):
    sms_token = BaseMixin.get_verify_token()
    email_token = BaseMixin.get_verify_token()

    def validate_sms_token(self, value: str) -> str:
        return BaseMixin.validate_verify_token(self, value)

    def validate_email_token(self, value: str) -> str:
        return BaseMixin.validate_verify_token(self, value)
