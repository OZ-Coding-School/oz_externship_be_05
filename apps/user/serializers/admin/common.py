from typing import Any

from rest_framework import serializers

from apps.courses.models.cohorts_models import Cohort
from apps.courses.models.courses_models import Course
from apps.user.models import User, Withdrawal


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


class UserWithdrawalDetailMiniSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ("id", "email", "name", "gender", "role", "status", "profile_image_url", "created_at")
