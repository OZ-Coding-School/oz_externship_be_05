from typing import Any

from rest_framework import serializers

from apps.user.models import User
from apps.user.models.user import RoleChoices
from apps.user.serializers.admin.common import (
    CohortMiniSerializer,
    CourseMiniSerializer,
    StatusMixin,
)

ROLE_USER = {"U", "AD"}
ROLE_COHORT = {"TA", "ST"}
ROLE_COURSES = {"OM", "LC"}


# 계정 목록 조회 시리얼라이저
class AdminAccountListSerializer(StatusMixin, serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ("id", "email", "nickname", "name", "birthday", "status", "role", "created_at")


# 계정 상세 조회 시리얼라이저
class CohortStudentAssignedSerializer(serializers.Serializer[dict[str, Any]]):
    cohort = CohortMiniSerializer(read_only=True)
    course = CourseMiniSerializer(source="cohort.course", read_only=True)

class AdminAccountRetrieveSerializer(StatusMixin, serializers.ModelSerializer[User]):
    assigned_courses = CohortStudentAssignedSerializer(
        source="cohortstudent_set",
        many=True,
        read_only=True,
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "gender",
            "status",
            "role",
            "profile_image_url",
            "assigned_courses",
            "created_at",
        )


# 회원 정보 수정 요청 시리얼라이저
class AdminAccountUpdateSerializer(serializers.ModelSerializer[User]):
    status = serializers.ChoiceField(
        choices=["active", "inactive"],
        required=False,
        write_only=True,
    )

    class Meta:
        model = User
        fields = ("nickname", "name", "phone_number", "birthday", "gender", "status", "profile_image_url")

    def update(self, instance: User, validated_data: dict[str, Any]) -> User:
        status = validated_data.pop("status", None)
        if status is not None:
            instance.is_active = status == "active"

        return super().update(instance, validated_data)


# 회원 정보 수정 응답 시리얼라이저
class AdminAccountResponseSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "gender",
            "profile_image_url",
            "updated_at",
        )


# 회원 권한 변경 시리얼라이저
class AdminAccountRoleUpdateSerializer(serializers.Serializer[dict[str, Any]]):
    role = serializers.ChoiceField(choices=["U", "AD", "TA", "ST", "OM", "LC"])
    cohort_id = serializers.IntegerField(required=False, allow_null=True)
    assigned_courses = serializers.ListField(child=serializers.IntegerField(), required=False, allow_empty=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        role = attrs["role"]
        cohort_id_present = "cohort_id" in attrs and attrs.get("cohort_id") is not None
        courses_present = "assigned_courses" in attrs and attrs.get("assigned_courses") is not None

        if role in ROLE_USER:
            if cohort_id_present or courses_present:
                raise serializers.ValidationError(
                    {"detail": "USER/ADMIN은 role만 변경 가능합니다.", "allowed_fields": ["role"]}
                )
            return attrs

        if role in ROLE_COHORT:
            if not cohort_id_present:
                raise serializers.ValidationError({"cohort_id": ["학생/조교 권한으로 변경 시 필수 필드입니다."]})
            if courses_present:
                raise serializers.ValidationError(
                    {"assigned_courses": ["학생/조교 권한으로 변경할 수 없는 필드입니다."]}
                )
            return attrs

        if role in ROLE_COURSES:
            if not courses_present:
                raise serializers.ValidationError(
                    {"assigned_courses": ["러닝코치/운영매니저 권한으로 변경 시 필수 필드입니다."]}
                )
            if cohort_id_present:
                raise serializers.ValidationError(
                    {"cohort_id": ["러닝코치/운영매니저 권한으로 변경할 수 없는 필드입니다."]}
                )
            return attrs

        return attrs
