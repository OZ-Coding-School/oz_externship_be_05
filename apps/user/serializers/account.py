from __future__ import annotations

from typing import Any

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.user.models import User
from apps.user.serializers.base import BaseMixin
from apps.user.serializers.mixins import AllTokensMixin, SMSTokenMixin, SenderTokenMixin


class SignupSerializer(SenderTokenMixin, AllTokensMixin, serializers.ModelSerializer[Any]):
    password = BaseMixin.get_password_field(write_only=True)

    class Meta:
        model = User
        fields = [
            "password",
            "name",
            "birthday",
            "gender",
            "nickname",
            "profile_image_url",
            "sms_token",
            "email_token",
        ]
        extra_kwargs = {
            "nickname": {"required": False, "allow_blank": True, "allow_null": True},
            "profile_image_url": {"required": False, "allow_blank": True, "allow_null": True},
        }

    def validate_password(self, value: str) -> str:
        return BaseMixin.validate_password(self, value)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        phone_identifier = self.verify_sms_token(attrs["sms_token"])
        email_identifier = self.verify_email_token(attrs["email_token"])

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
        return User.objects.create_user(password=password, **validated_data)


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
            raise serializers.ValidationError("로그인이 유효하지 않습니다.") from exc
        attrs["access_token"] = str(token.access_token)
        return attrs


class UserProfileSerializer(serializers.ModelSerializer[Any]):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "nickname",
            "phone_number",
            "gender",
            "birthday",
            "profile_image_url",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["email", "role", "is_active", "created_at", "updated_at"]


class UserUpdateSerializer(serializers.ModelSerializer[Any], BaseMixin):
    class Meta:
        model = User
        fields = ["name", "nickname", "profile_image_url", "gender", "birthday"]
        extra_kwargs = {
            "nickname": {"required": False, "allow_blank": True, "allow_null": True},
            "profile_image_url": {"required": False, "allow_blank": True, "allow_null": True},
            "name": {"required": False},
            "gender": {"required": False},
            "birthday": {"required": False},
        }


class NicknameCheckSerializer(serializers.Serializer[Any]):
    nickname = serializers.CharField(max_length=15)


class ChangePasswordSerializer(serializers.Serializer[Any], BaseMixin):
    current_password = BaseMixin.get_password_field(write_only=True)
    new_password = BaseMixin.get_password_field(write_only=True)

    def validate_new_password(self, value: str) -> str:
        return BaseMixin.validate_password(self, value)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["current_password"] == attrs["new_password"]:
            raise serializers.ValidationError("새 비밀번호는 기존 비밀번호와 달라야 합니다.")
        user: User = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError("현재 비밀번호가 올바르지 않습니다.")
        return attrs


class ChangePhoneSerializer(SenderTokenMixin, SMSTokenMixin, serializers.Serializer[Any]):
    def update(self, instance: User, validated_data: dict[str, Any]) -> User:
        phone_number = self.verify_sms_token(validated_data["sms_token"])
        if User.objects.exclude(pk=instance.pk).filter(phone_number=phone_number).exists():
            raise serializers.ValidationError("이미 사용중인 휴대폰 번호입니다.")
        instance.phone_number = phone_number
        instance.save(update_fields=["phone_number", "updated_at"])
        return instance
