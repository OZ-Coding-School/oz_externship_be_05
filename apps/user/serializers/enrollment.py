from typing import Any, cast

from rest_framework import serializers

from apps.courses.models.cohorts_models import Cohort
from apps.courses.models.courses_models import Course
from apps.user.models import CohortStudent, StudentEnrollmentRequest
from apps.user.utils.enrollment import get_available_cohorts_queryset


class CohortSerializer(serializers.ModelSerializer[Cohort]):
    class Meta:
        model = Cohort
        fields = ("id", "number", "start_date", "end_date", "status")


class CourseAvailableSerializer(serializers.ModelSerializer[Course]):
    class Meta:
        model = Course
        fields = ("id", "name")


class CourseEnrolledSerializer(serializers.ModelSerializer[Course]):
    class Meta:
        model = Course
        fields = ("id", "name", "tag", "thumbnail_img_url")


class AvailableCourseSerializer(serializers.Serializer[Any]):
    cohort = CohortSerializer(source="*", read_only=True)
    course = CourseAvailableSerializer(read_only=True)


class EnrolledCourseItemSerializer(serializers.Serializer[Any]):
    cohort = CohortSerializer(source="cohort", read_only=True)
    course = CourseEnrolledSerializer(source="cohort.course", read_only=True)


class EnrollStudentSerializer(serializers.Serializer[Any]):
    cohort_id: serializers.PrimaryKeyRelatedField[Cohort] = serializers.PrimaryKeyRelatedField(
        source="cohort",
        queryset=Cohort.objects.none(),
        write_only=True,
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        cohort_field = cast(serializers.PrimaryKeyRelatedField[Cohort], self.fields["cohort_id"])
        cohort_field.queryset = get_available_cohorts_queryset()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        user = self.context["user"]
        cohort = attrs["cohort"]

        if CohortStudent.objects.filter(user=user, cohort=cohort).exists():
            raise serializers.ValidationError("이미 수강 중인 수업입니다.")

        if StudentEnrollmentRequest.objects.filter(user=user, cohort=cohort).exists():
            raise serializers.ValidationError("이미 수강 신청한 수업입니다.")

        return attrs

    def create(self, validated_data: dict[str, Any]) -> StudentEnrollmentRequest:
        user = self.context["user"]
        return StudentEnrollmentRequest.objects.create(user=user, cohort=validated_data["cohort"])
