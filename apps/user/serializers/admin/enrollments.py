from typing import Any

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.user.models import User
from apps.user.models.enrollment import StudentEnrollmentRequest
from apps.user.serializers.admin.common import (
    CohortSimpleSerializer,
    CourseMiniSerializer,
    UserMiniSerializer,
)


# 수강생 목록 조회 시리얼라이저
class InProgressCourseSerializer(serializers.Serializer[dict[str, Any]]):
    cohort: CohortSimpleSerializer = CohortSimpleSerializer(source="cohort")
    course: CourseMiniSerializer = CourseMiniSerializer(source="cohort.course")


class AdminStudentSerializer(serializers.ModelSerializer[User]):
    in_progress_course = InProgressCourseSerializer(
        source="in_progress_cohortstudent",
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
            "status",
            "role",
            "in_progress_course",
            "created_at",
        )


# 수강생 등록 요청 목록 시리얼라이저
class AdminStudentEnrollSerializer(serializers.ModelSerializer[StudentEnrollmentRequest]):
    user: UserMiniSerializer = UserMiniSerializer(read_only=True)
    cohort: CohortSimpleSerializer = CohortSimpleSerializer(read_only=True)
    course: CourseMiniSerializer = CourseMiniSerializer(source="cohort.course", read_only=True)

    class Meta:
        model = StudentEnrollmentRequest
        fields = ("id", "user", "cohort", "course", "status", "created_at")


# 수강생 등록 요청 승인/거절 시리얼라이저
class AdminStudentEnrollRequestSerializer(serializers.Serializer[dict[str, list[int]]]):
    enrollments = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)

    # id 중복 제거
    def validate_enrollments(self, value: list[int]) -> list[int]:
        return list(dict.fromkeys(value))


# 수강생 등록 요청 승인 시리얼라이저
class AdminStudentEnrollAcceptSerializer(serializers.Serializer[dict[str, str | int]]):
    detail = serializers.CharField(max_length=255)


# 수강생 등록 거절/승인 응답 시리얼라이저
class AdminStudentEnrollRejectSerializer(serializers.Serializer[dict[str, str | int]]):
    detail = serializers.CharField(max_length=255)

