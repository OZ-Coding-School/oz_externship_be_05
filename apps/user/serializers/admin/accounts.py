from typing import Any, cast

from django.db import transaction
from rest_framework import serializers

from apps.courses.models.cohorts_models import Cohort
from apps.courses.models.courses_models import Course
from apps.user.models.user import RoleChoices, User
from apps.user.serializers.admin.common import (
    CohortMiniSerializer,
    CourseMiniSerializer,
)


# 계정 목록 조회 시리얼라이저
class AdminAccountListSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ("id", "email", "nickname", "name", "birthday", "status", "role", "created_at")


# 계정 상세 조회 시리얼라이저
class CohortStudentAssignedSerializer(serializers.Serializer[dict[str, Any]]):
    cohort = CohortMiniSerializer(read_only=True)
    course = CourseMiniSerializer(source="cohort.course", read_only=True)


class AdminAccountRetrieveSerializer(serializers.ModelSerializer[User]):
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
            "status",
            "gender",
            "profile_image_url",
            "updated_at",
        )


# 회원 권한 변경 시리얼라이저
class AdminAccountRoleUpdateSerializer(serializers.Serializer[User]):
    role = serializers.ChoiceField(choices=RoleChoices.choices)

    cohort_id = serializers.PrimaryKeyRelatedField(
        source="cohort",
        queryset=Cohort.objects.all(),
        required=False,
        allow_null=True,
    )

    assigned_courses = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        many=True,
        required=False,
        allow_empty=False,
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        role = attrs.get("role")
        cohort = attrs.get("cohort")
        courses = attrs.get("assigned_courses")

        if role in (RoleChoices.TA, RoleChoices.ST) and cohort is None:
            raise serializers.ValidationError({"cohort_id": ["해당 권한으로 변경 시 필수 값입니다."]})

        if role in (RoleChoices.OM, RoleChoices.LC) and not courses:
            raise serializers.ValidationError({"assigned_courses": ["해당 권한으로 변경 시 필수 값입니다."]})

        return attrs

    @transaction.atomic
    def update(self, instance: User, validated_data: dict[str, Any]) -> User:
        role = cast(str, validated_data.get("role"))
        # 기존 역할 정리
        self._clear_exists_role_relations(instance)
        match role:
            case RoleChoices.OM | RoleChoices.LC:
                courses = validated_data["assigned_courses"]
                if role == RoleChoices.OM:
                    instance.operationmanager_set.set(courses)
                elif role == RoleChoices.LC:
                    instance.learningcoach_set.set(courses)

            case RoleChoices.TA | RoleChoices.ST:
                cohort = validated_data["cohort"]
                if role == RoleChoices.TA:
                    instance.trainingassistant_set.set([cohort])
                elif role == RoleChoices.ST:
                    instance.cohortstudent_set.set([cohort])

        instance.role = role
        instance.save()
        return instance

    def _clear_exists_role_relations(self, user: User) -> None:
        match user.role:
            case RoleChoices.OM:
                user.operationmanager_set.all().delete()
            case RoleChoices.LC:
                user.learningcoach_set.all().delete()
            case RoleChoices.TA:
                user.trainingassistant_set.all().delete()
            case RoleChoices.ST:
                user.cohortstudent_set.all().delete()
