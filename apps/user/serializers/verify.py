from apps.user.serializers.base import BaseMixin
from rest_framework.serializers import Serializer

# 아름답다 👽

class EmailCodeSerializer(Serializer,BaseMixin):
    email = BaseMixin.get_email()
    code = BaseMixin.get_password()

class ChangePasswordSerializer(EmailCodeSerializer):
    new_password = BaseMixin.get_password()

    def validate_new_password(self, value: str) -> str:
        BaseMixin.validate_password(value)

class PhoneCodeSerializer(Serializer,BaseMixin):
    phone_number = BaseMixin.get_phone_number()
    code = BaseMixin.get_verify_code()

class TokensSerializer(Serializer,BaseMixin):
    verify_token = BaseMixin.get_verify_token()

class AllTokensSerializer(Serializer,BaseMixin):
    sms_token = BaseMixin.get_verify_token()
    email_token = BaseMixin.get_verify_token()

    def validate_sms_token():
        BaseMixin.validate_verify_token()
    
    def validate_email_token():
        BaseMixin.validate_verify_token