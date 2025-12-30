from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.user.models import User, WithdrawalReason
from apps.user.serializers.base import BaseMixin
from apps.user.serializers.mixins import SenderMixin, SMSTokenMixin


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
            "role",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["email", "phone_number", "role", "is_active", "created_at", "updated_at"]


class UserUpdateSerializer(serializers.ModelSerializer[Any], BaseMixin):
    class Meta:
        model = User
        fields = ["name", "nickname", "gender", "birthday"]
        extra_kwargs = {
            "nickname": {"required": False, "allow_blank": True, "allow_null": True},
            "name": {"required": False},
            "gender": {"required": False},
            "birthday": {"required": False},
        }


class NicknameCheckSerializer(serializers.Serializer[Any]):
    nickname = serializers.CharField(max_length=15)


class ChangePasswordSerializer(serializers.Serializer[Any], BaseMixin):
    current_password = BaseMixin.get_password_field(write_only=True)
    new_password = BaseMixin.get_password_field(write_only=True)

    def validate_new_password(self, value: str) -> str:  # noqa: D401
        return BaseMixin.validate_password(self, value)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        user: User = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError("현재 비밀번호가 올바르지 않습니다.")
        if attrs["current_password"] == attrs["new_password"]:
            raise serializers.ValidationError("새 비밀번호는 기존 비밀번호와 달라야 합니다.")
        return attrs


class ChangePhoneSerializer(SenderMixin, SMSTokenMixin, serializers.Serializer[Any]):
    sms_token = BaseMixin.get_verify_token_field()

    def update(self, instance: User, validated_data: dict[str, Any]) -> User:
        phone_number = self.verify_sms_token(validated_data["sms_token"])
        if User.objects.exclude(pk=instance.pk).filter(phone_number=phone_number).exists():
            raise serializers.ValidationError("이미 사용중인 휴대전화 번호입니다.")
        instance.phone_number = phone_number
        instance.save(update_fields=["phone_number", "updated_at"])
        return instance


class ProfileImageUploadSerializer(serializers.Serializer[Any]):
    image = serializers.ImageField()


class WithdrawalRequestSerializer(serializers.Serializer[Any]):
    reason = serializers.ChoiceField(
        choices=WithdrawalReason.choices,
        required=False,
        default=WithdrawalReason.OTHER,
    )
    reason_detail = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
