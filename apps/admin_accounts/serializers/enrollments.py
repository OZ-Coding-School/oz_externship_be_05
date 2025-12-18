from typing import Any

from rest_framework import serializers

from apps.admin_accounts.serializers.common import (
    CohortSimpleSerializer,
    CourseMiniSerializer,
    StatusMixin,
    UserMiniSerializer,
)
from apps.user.models import User
from apps.user.models.enrollment import StudentEnrollmentRequest


# 수강생 목록 조회 시리얼라이저
class AdminAccountStudentSerializer(StatusMixin, serializers.ModelSerializer[User]):
    in_progress_course = serializers.SerializerMethodField()

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
            "role",
            "in_progress_course",
            "created_at",
        )

    def get_in_progress_course(self, obj: User) -> dict[str, Any]:
        for cs in obj.cohortstudent_set.all():
            cohort = cs.cohort
            if not cohort:
                continue
            return {
                "cohort": CohortSimpleSerializer(cohort).data,
                "course": CourseMiniSerializer(cohort.course).data,
            }
        return {}


# 수강생 등록 요청 목록 시리얼라이저
class AdminAccountStudentEnrollSerializer(serializers.ModelSerializer[StudentEnrollmentRequest]):
    user = UserMiniSerializer(read_only=True)
    cohort = CohortSimpleSerializer(read_only=True)
    course = serializers.SerializerMethodField()

    class Meta:
        model = StudentEnrollmentRequest
        fields = ("id", "user", "cohort", "course", "status", "created_at")

    def get_course(self, obj: StudentEnrollmentRequest) -> dict[str, Any] | None:
        cohort = getattr(obj, "cohort", None)
        course = getattr(cohort, "course", None) if cohort else None
        return CourseMiniSerializer(course).data if course else None


# 수강생 등록 요청 승인 시리얼라이저
class AdminAccountStudentEnrollAcceptSerializer(serializers.Serializer[dict[str, str | int]]):
    detail = serializers.CharField(max_length=255)
    success = serializers.IntegerField()
    failed = serializers.IntegerField()


# 수강생 등록 요청 거절 시리얼라이저
class AdminAccountStudentEnrollRejectRequestSerializer(serializers.Serializer[dict[str, list[int]]]):
    enrollments = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)


# 수강생 등록 거절/승인 응답 시리얼라이저
class AdminAccountStudentEnrollRejectResponseSerializer(serializers.Serializer[dict[str, str | int]]):
    detail = serializers.CharField(max_length=255)
    success = serializers.IntegerField()
    failed = serializers.IntegerField()
