from typing import Any

from rest_framework import serializers

from apps.courses.models.cohorts_models import Cohort
from apps.courses.models.courses_models import Course
from apps.user.models import User, Withdrawal


# status field 생성 class
class StatusMixin(serializers.Serializer[dict[str, Any]]):
    status = serializers.SerializerMethodField()

    def get_status(self, obj: User) -> str:
        if Withdrawal.objects.filter(user=obj).exists():
            return "withdrew"
        return "active" if obj.is_active else "inactive"


# course 응답 검증 시리얼라이저
class CourseMiniSerializer(serializers.ModelSerializer[Course]):
    class Meta:
        model = Course
        fields = ("id", "name", "tag")


# chort 응답 검증 시리얼라이저
class CohortMiniSerializer(serializers.ModelSerializer[Cohort]):
    class Meta:
        model = Cohort
        fields = ("id", "number", "status", "start_date", "end_date")


class CohortSimpleSerializer(serializers.ModelSerializer[Cohort]):
    class Meta:
        model = Cohort
        fields = ("id", "number")


class UserMiniSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ("id", "email", "name", "birthday", "gender")


class UserWithdrawalMiniSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ("id", "email", "name", "role", "birthday")


class UserWithdrawalDetailMiniSerializer(StatusMixin, serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ("id", "email", "name", "gender", "role", "status", "profile_image_url", "created_at")
