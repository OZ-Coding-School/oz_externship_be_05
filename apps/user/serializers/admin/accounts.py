from typing import Any

from rest_framework import serializers

from apps.user.models import User
from apps.user.models.user import RoleChoices
from apps.user.serializers.admin.common import (
    CohortMiniSerializer,
    CourseMiniSerializer,
    StatusMixin,
)

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
    class Meta:
        model = User
        fields = ("nickname", "name", "phone_number", "birthday", "gender", "profile_image_url")


# 회원 정보 수정 응답 시리얼라이저
class AdminAccountResponseSerializer(StatusMixin, serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "status",
            "gender",
            "profile_image_url",
            "updated_at",
        )


# 회원 권한 변경 시리얼라이저
class AdminAccountRoleUpdateSerializer(serializers.Serializer[dict[str, Any]]):
    role = serializers.ChoiceField(choices=RoleChoices.choices)
    cohort_id = serializers.IntegerField(required=False, allow_null=True)
    assigned_courses = serializers.ListField(child=serializers.IntegerField(), required=False, allow_empty=False)