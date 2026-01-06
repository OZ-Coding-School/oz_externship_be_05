from typing import Any

from django.db.models import TextChoices
from rest_framework import serializers
from rest_framework.serializers import Serializer

from apps.user.models import User
from apps.user.models.user import UserStatus
from apps.user.serializers.base import BaseMixin


class RequestPurpose(TextChoices):
    SIGNUP = "signup"
    FIND = "find"
    RESTORE = "restore"


class EmailRequestSerializer(Serializer[Any], BaseMixin):
    purpose = serializers.ChoiceField(choices=RequestPurpose.choices, default=RequestPurpose.SIGNUP)
    email = BaseMixin.get_email_field()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        email = attrs["email"]
        purpose = attrs["purpose"]

        if purpose == RequestPurpose.SIGNUP:
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError({"email": "이미 가입된 이메일입니다."})

        if purpose == RequestPurpose.FIND:
            if not User.objects.filter(email=email).exists():
                raise serializers.ValidationError({"email": "가입되지 않는 이메일입니다."})

        if purpose == RequestPurpose.RESTORE:
            try:
                user = User.objects.prefetch_related("withdrawal_set").get(email=email)
                if not user.status == UserStatus.WITHDREW:
                    raise serializers.ValidationError("탈퇴진행 중인 유저가 아닙니다.")
            except User.DoesNotExist:
                raise serializers.ValidationError("존재하지 않는 회원입니다.")
            except serializers.ValidationError as exc:
                raise exc

        return attrs


class SMSRequestSerializer(Serializer[Any], BaseMixin):
    phone_number = BaseMixin.get_phone_number_field()
    purpose = serializers.ChoiceField(choices=RequestPurpose.choices, default=RequestPurpose.SIGNUP)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        phone_number = attrs["phone_number"]
        purpose = attrs["purpose"]

        if purpose == RequestPurpose.SIGNUP:
            if User.objects.filter(phone_number=phone_number).exists():
                raise serializers.ValidationError({"phone_number": "이미 가입된 전화번호입니다."})

        if purpose == RequestPurpose.FIND:
            if not User.objects.filter(phone_number=phone_number).exists():
                raise serializers.ValidationError({"phone_number": "가입되지 않는 전화번호입니다."})

        if purpose == RequestPurpose.RESTORE:
            raise serializers.ValidationError("잘못된 요청입니다.")

        return attrs


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
