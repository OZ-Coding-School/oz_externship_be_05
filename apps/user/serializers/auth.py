from __future__ import annotations

from typing import Any, cast

from django.contrib.auth import authenticate
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.user.models import User
from apps.user.serializers.base import BaseMixin
from apps.user.serializers.mixins import EmailTokenMixin, SenderMixin, SMSTokenMixin


class SignupSerializer(SenderMixin, EmailTokenMixin, SMSTokenMixin, serializers.ModelSerializer[Any]):

    sms_token = BaseMixin.get_verify_token_field()
    email_token = BaseMixin.get_verify_token_field()
    password = BaseMixin.get_password_field(write_only=True)

    class Meta:
        model = User
        fields = [
            "password",
            "name",
            "birthday",
            "gender",
            "nickname",
            "sms_token",
            "email_token",
        ]
        extra_kwargs = {
            "nickname": {"required": False, "allow_blank": True, "allow_null": True},
        }

    def validate_password(self, value: str) -> str:
        return BaseMixin.validate_password(self, value)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        sms_token = attrs.get("sms_token")
        email_token = attrs.get("email_token")

        if sms_token is None or email_token is None:
            raise serializers.ValidationError("인증 토큰이 누락되었습니다.")

        phone_identifier = self.verify_sms_token(cast(str, sms_token))
        email_identifier = self.verify_email_token(cast(str, email_token))

        if User.objects.filter(email=email_identifier).exists():
            raise serializers.ValidationError("이미 가입된 이메일입니다.")
        if User.objects.filter(phone_number=phone_identifier).exists():
            raise serializers.ValidationError("이미 사용중인 휴대폰 번호입니다.")

        attrs["phone_number"] = phone_identifier
        attrs.pop("sms_token", None)
        attrs["email"] = email_identifier
        attrs.pop("email_token", None)
        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        password = validated_data.pop("password")
        try:
            return User.objects.create_user(password=password, **validated_data)
        except IntegrityError as exc:
            raise serializers.ValidationError("이미 가입된 사용자입니다.") from exc


class LoginSerializer(serializers.Serializer[Any], BaseMixin):
    email = BaseMixin.get_email_field()
    password = BaseMixin.get_password_field(write_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        request = self.context.get("request")
        user = authenticate(request=request, email=attrs["email"], password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("이메일 또는 비밀번호가 올바르지 않습니다.")
        if not user.is_active:
            raise serializers.ValidationError("비활성화된 계정입니다.")
        attrs["user"] = user
        return attrs


class TokenRefreshSerializer(serializers.Serializer[Any]):
    refresh_token = serializers.CharField()
    access_token = serializers.CharField(read_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        try:
            token = RefreshToken(attrs["refresh_token"])
        except TokenError as exc:
            raise serializers.ValidationError("로그인이 만료되었습니다.") from exc
        attrs["access_token"] = str(token.access_token)
        return attrs
