from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.courses.models.cohorts_models import Cohort
from apps.user.models import CohortStudent, StudentEnrollmentRequest, User


class EnrollmentRequestSerializer(serializers.Serializer[Any]):
    cohort_id = serializers.IntegerField(min_value=1)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        user: User = self.context["request"].user
        try:
            cohort = Cohort.objects.get(pk=attrs["cohort_id"])
        except Cohort.DoesNotExist as exc:
            raise serializers.ValidationError("해당 기수를 찾을 수 없습니다.") from exc

        if CohortStudent.objects.filter(cohort=cohort, user=user).exists():
            raise serializers.ValidationError("이미 수강 중 입니다.")
        if StudentEnrollmentRequest.objects.filter(cohort=cohort, user=user).exists():
            raise serializers.ValidationError("이미 수강 신청이 존재합니다.")

        attrs["cohort"] = cohort
        attrs["user"] = user
        return attrs

    def create(self, validated_data: dict[str, Any]) -> StudentEnrollmentRequest:
        return StudentEnrollmentRequest.objects.create(
            cohort=validated_data["cohort"],
            user=validated_data["user"],
            accepted_at=None,
        )


class CohortInfoSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    number = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    status = serializers.CharField()


class CourseInfoSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    name = serializers.CharField()
    tag = serializers.CharField()
    thumbnail_img_url = serializers.CharField(allow_null=True, allow_blank=True)


class EnrolledCourseSerializer(serializers.Serializer[Any]):
    cohort = CohortInfoSerializer()
    course = CourseInfoSerializer()
